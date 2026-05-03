"""
20_build_webapp_data.py — Build slim webapp aggregates for Streamlit (Stage 1)
                          and the future Quarto + ojs static site (Stage 2).

Reads the existing slim country-/product-/pair-level parquets in
``data/cleaned/`` and produces four small derived files in
``data/cleaned/webapp/``. The Streamlit MVP MUST NEVER load
``panel_main_confounders.parquet`` (~579 MB); only these aggregates ship.

Outputs (all in ``data/cleaned/webapp/``)
-----------------------------------------
1. ``country_lookup.parquet``       (~226 rows; ~10 KB)
   - iso3 (str), name (str, pycountry), region (str), has_sos (bool)

2. ``products_at_risk.parquet``     (~226 x 15 ~= 3,400 rows; ~80 KB)
   - For each iso3, top-15 HS4 products with rca >= 1 AND sos contribution
     ABOVE the country's median sos contribution.
   - Schema: iso3, hs4, product_name, sos_score, pci_std, rca,
             trade_value, rank_within_country.
   - DESIGN CHOICE: ``sos_country_product_composite.parquet`` exposes several
     candidate SOS columns. We pick ``sos_composite`` as the headline score
     (it combines FDI / FATF / AMLD legs the same way as the country-level
     composite). Falls back to ``sos_composite_int`` if absent.

3. ``diversification_opps.parquet`` (~226 x 15 ~= 3,400 rows; ~80 KB)
   - For each iso3, top-15 HS4 products with rca < 1, density >= country's
     60th percentile, AND pci_std >= country's 50th percentile.
   - Schema: iso3, hs4, product_name, density, pci_std, rca,
             diversification_score, rank_within_country.
   - DESIGN CHOICE: diversification_score = density * pci_std (both already
     standardised; product penalises low-relatedness or low-complexity rows).

4. ``corridor_top5.parquet``        (~226 x 5 ~= 1,100 rows; ~30 KB)
   - For each reporter iso3, top-5 partner countries by friction-weighted
     trade contribution.
   - Schema: iso3, partner_iso3, partner_name, contribution, trade_value,
             derisked, rank_within_country.
   - DESIGN CHOICE: ``gravity_bilateral.parquet`` lacks both trade values
     and a derisked flag. We therefore aggregate the pair x year x hs4
     panel from ``panel_main_confounders.parquet`` LAZILY (polars
     scan_parquet -> group_by -> sink/collect-on-aggregate) for year 2023
     to (iso3_o, iso3_d) -> (sum trade_value, mean pf_cbr).
     ``pf_cbr`` is the FDI-derived derisking proxy (more negative => more
     derisked; see scripts/python/12_falsification.py docstring). We define
     ``derisked_intensity = max(-pf_cbr, 0)`` and
     ``contribution = trade_value * derisked_intensity``.
     ``derisked`` (bool) = derisked_intensity > 0.

5. ``webapp_meta.json`` (small)
   - build_date, source_commit (or "unknown"), files, row_counts.

Total payload budget: < 50 MB (Streamlit Cloud has a 300 MB hard limit;
we are well under).

Conventions
-----------
- Mirror ``16_confounder_estimation.py`` / ``12_falsification.py``:
  ``log()`` helper with timestamps + ``flush=True``, UTF-8 stdout,
  polars lazy reads, pandas at the analysis layer when convenient.
- ``main()`` wrapped in ``if __name__ == "__main__":`` invocation.
- argparse ``--format {parquet,json,both}`` (default parquet). JSON branch
  is a Stage-2 stub for now.
- Idempotent: running twice yields identical outputs (sorted final frames,
  no timestamps inside parquet bodies).
- Each output has at least 200 distinct iso3 values (left-joined onto the
  country_lookup spine where appropriate).

Inputs
------
- data/cleaned/sos_country_composite.parquet
- data/cleaned/sos_country_product_composite.parquet
- data/cleaned/complexity_rca.parquet
- data/cleaned/complexity_pci.parquet
- data/cleaned/complexity_density.parquet
- data/cleaned/panel_main_confounders.parquet  (LAZY scan only)

Outputs
-------
- data/cleaned/webapp/country_lookup.parquet
- data/cleaned/webapp/products_at_risk.parquet
- data/cleaned/webapp/diversification_opps.parquet
- data/cleaned/webapp/corridor_top5.parquet
- data/cleaned/webapp/webapp_meta.json
"""

import argparse
import json
import os
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone

# Force UTF-8 output on Windows consoles whose default codepage is cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import polars as pl

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
PROJECT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_CLEAN = os.path.join(PROJECT, "data", "cleaned")
DIR_OUT   = os.path.join(DIR_CLEAN, "webapp")
DIR_SITE  = os.path.join(PROJECT, "site", "_data")

P_SOS_COUNTRY  = os.path.join(DIR_CLEAN, "sos_country_composite.parquet")
P_SOS_PRODUCT  = os.path.join(DIR_CLEAN, "sos_country_product_composite.parquet")
P_RCA          = os.path.join(DIR_CLEAN, "complexity_rca.parquet")
P_PCI          = os.path.join(DIR_CLEAN, "complexity_pci.parquet")
P_DENSITY      = os.path.join(DIR_CLEAN, "complexity_density.parquet")
P_PANEL        = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")

YEAR_LATEST    = 2023            # PCI / RCA / panel coverage extends to 2024
                                 # but 2023 is the cleanest joined year per
                                 # session_2026_04_03_progress notes.
TOP_K_PRODUCT  = 15
TOP_K_CORRIDOR = 5


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_source_commit() -> str:
    """Return current git HEAD if the project is a git repo, else 'unknown'."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Output 1: country_lookup
# ---------------------------------------------------------------------------
def build_country_lookup(sos_iso3: set[str], all_iso3: set[str]) -> pl.DataFrame:
    """ISO3 -> (name, region, has_sos). Spine for every other output."""
    log("Building country_lookup ...")
    import pycountry

    # ISO3 -> continent map. pycountry exposes country.alpha_3 but not region;
    # we derive region from a small lookup over alpha_2 -> continent. To avoid
    # a hard dep on pycountry_convert, we construct a manual UN-region map at
    # the M49 level using pycountry's iso3166-1 metadata when available.
    # Pragmatic fallback: alpha_2 prefix -> coarse region via a hand-curated
    # mapping covering the canonical continent groupings. If unknown, "—".
    A2_TO_REGION = {}
    try:
        # Optional dependency; if present use it for cleaner regions.
        import pycountry_convert as pcc  # type: ignore
        def a2_to_region(a2: str) -> str:
            try:
                cont = pcc.country_alpha2_to_continent_code(a2)
                return {
                    "AF": "Africa", "AS": "Asia", "EU": "Europe",
                    "NA": "North America", "SA": "South America",
                    "OC": "Oceania", "AN": "Antarctica",
                }.get(cont, "—")
            except Exception:
                return "—"
    except Exception:
        # Inline coarse fallback: leave region blank; Streamlit can group by
        # has_sos instead. The selector still works.
        def a2_to_region(a2: str) -> str:
            return "—"

    spine = sorted(all_iso3 | sos_iso3)
    rows = []
    for iso3 in spine:
        c = pycountry.countries.get(alpha_3=iso3)
        if c is None:
            name = iso3
            region = "—"
        else:
            name = c.name
            region = a2_to_region(c.alpha_2)
        rows.append({
            "iso3": iso3,
            "name": name,
            "region": region,
            "has_sos": iso3 in sos_iso3,
        })
    df = pl.DataFrame(rows).sort("iso3")
    return df


# ---------------------------------------------------------------------------
# Output 2: products_at_risk
# ---------------------------------------------------------------------------
def build_products_at_risk(spine_iso3: list[str]) -> pl.DataFrame:
    """Top-15 HS4 by SOS exposure conditional on rca >= 1, per country."""
    log("Building products_at_risk ...")

    sos = pl.read_parquet(P_SOS_PRODUCT)
    cols = sos.columns
    if "sos_composite" in cols:
        sos_col = "sos_composite"
    elif "sos_composite_int" in cols:
        sos_col = "sos_composite_int"
    else:
        # Should not happen given current schema, but be defensive.
        candidates = [c for c in cols if c.startswith("sos_")]
        if not candidates:
            raise RuntimeError("No SOS column found in sos_country_product_composite")
        sos_col = candidates[0]
    log(f"  using SOS score column: {sos_col}")

    sos = sos.select([
        "iso3", "hs4",
        pl.col(sos_col).alias("sos_score"),
        pl.col("pci_std"),
        pl.col("trade_total").alias("trade_value"),
    ])

    rca = pl.read_parquet(P_RCA).filter(pl.col("year") == YEAR_LATEST).select(["iso3", "hs4", "rca"])

    df = (
        sos.join(rca, on=["iso3", "hs4"], how="inner")
           .filter(pl.col("rca") >= 1.0)
           .filter(pl.col("sos_score").is_not_null())
    )

    # Country-level median of sos_score among rca>=1 set.
    df = df.with_columns(
        pl.col("sos_score").median().over("iso3").alias("_median_sos")
    ).filter(pl.col("sos_score") > pl.col("_median_sos")).drop("_median_sos")

    # Rank within country by sos_score desc, take top-15.
    df = df.with_columns(
        pl.col("sos_score").rank(method="ordinal", descending=True).over("iso3").cast(pl.Int32).alias("rank_within_country")
    ).filter(pl.col("rank_within_country") <= TOP_K_PRODUCT)

    df = df.with_columns(
        ("HS4 " + pl.col("hs4").cast(pl.Utf8)).alias("product_name")
    ).select([
        "iso3", "hs4", "product_name",
        "sos_score", "pci_std", "rca", "trade_value",
        "rank_within_country",
    ]).sort(["iso3", "rank_within_country"])

    return df


# ---------------------------------------------------------------------------
# Output 3: diversification_opps
# ---------------------------------------------------------------------------
def build_diversification_opps(spine_iso3: list[str]) -> pl.DataFrame:
    """Top-15 HS4 reachable + complex products with rca < 1, per country."""
    log("Building diversification_opps ...")

    rca = pl.read_parquet(P_RCA).filter(pl.col("year") == YEAR_LATEST).select(["iso3", "hs4", "rca"])
    den = pl.read_parquet(P_DENSITY).filter(pl.col("year") == YEAR_LATEST).select(["iso3", "hs4", "density"])
    pci = pl.read_parquet(P_PCI).select(["hs4", "pci_std"])

    df = den.join(rca, on=["iso3", "hs4"], how="inner") \
            .join(pci, on="hs4", how="inner")

    df = df.filter(pl.col("rca") < 1.0) \
           .filter(pl.col("density").is_not_null()) \
           .filter(pl.col("pci_std").is_not_null())

    df = df.with_columns([
        pl.col("density").quantile(0.6).over("iso3").alias("_d60"),
        pl.col("pci_std").quantile(0.5).over("iso3").alias("_p50"),
    ]).filter(
        (pl.col("density") >= pl.col("_d60")) & (pl.col("pci_std") >= pl.col("_p50"))
    ).drop(["_d60", "_p50"])

    df = df.with_columns(
        (pl.col("density") * pl.col("pci_std")).alias("diversification_score")
    )

    df = df.with_columns(
        pl.col("diversification_score").rank(method="ordinal", descending=True).over("iso3").cast(pl.Int32).alias("rank_within_country")
    ).filter(pl.col("rank_within_country") <= TOP_K_PRODUCT)

    df = df.with_columns(
        ("HS4 " + pl.col("hs4").cast(pl.Utf8)).alias("product_name")
    ).select([
        "iso3", "hs4", "product_name",
        "density", "pci_std", "rca",
        "diversification_score", "rank_within_country",
    ]).sort(["iso3", "rank_within_country"])

    return df


# ---------------------------------------------------------------------------
# Output 4: corridor_top5
# ---------------------------------------------------------------------------
def build_corridor_top5(country_lookup: pl.DataFrame) -> pl.DataFrame:
    """Top-5 partner corridors per reporter, weighted by friction intensity.

    Aggregates panel_main_confounders.parquet LAZILY: scan -> filter year ->
    group by (iso3_o, iso3_d) -> sum trade_value + mean pf_cbr. Polars
    streams the parquet so we never materialise the 579 MB body.
    """
    log("Building corridor_top5 (lazy scan over panel_main_confounders) ...")

    # Lazy projection + filter pushdown: only the required columns/year are
    # materialised before group-by. We use the in-memory engine (not
    # streaming) so the floating-point reduction order is stable across
    # runs, ensuring byte-identical outputs.
    agg = (
        pl.scan_parquet(P_PANEL)
          .filter(pl.col("year") == YEAR_LATEST)
          .select(["iso3_o", "iso3_d", "trade_value", "pf_cbr"])
          .sort(["iso3_o", "iso3_d", "trade_value", "pf_cbr"])
          .group_by(["iso3_o", "iso3_d"], maintain_order=True)
          .agg([
              pl.col("trade_value").sum().alias("trade_value"),
              pl.col("pf_cbr").mean().alias("pf_cbr_mean"),
          ])
          .collect()
    )

    log(f"  pair-level rows after aggregation: {agg.height:,}")

    # Derisking intensity: pf_cbr is non-positive (more negative => more
    # derisked). Map to a non-negative intensity and clip.
    agg = agg.with_columns([
        pl.when(pl.col("pf_cbr_mean").is_null())
          .then(0.0)
          .otherwise((-pl.col("pf_cbr_mean")).clip(lower_bound=0.0))
          .alias("derisked_intensity"),
    ]).with_columns([
        (pl.col("trade_value").fill_null(0.0) * pl.col("derisked_intensity")).alias("contribution"),
        (pl.col("derisked_intensity") > 0.0).alias("derisked"),
    ])

    # Sort first so that any tie-breaking in the ordinal rank is
    # deterministic and independent of upstream group-by ordering (the
    # streaming engine does not guarantee a stable group order).
    agg = agg.sort(["iso3_o", "iso3_d"])

    # Top-5 partners per reporter by contribution; if all contributions are
    # zero (no derisking), fall back to plain trade_value so corridor_top5
    # still surfaces meaningful rows.
    agg = agg.with_columns(
        (pl.col("contribution") + 1e-12 * pl.col("trade_value").fill_null(0.0)).alias("_rank_score")
    ).with_columns(
        pl.col("_rank_score").rank(method="ordinal", descending=True).over("iso3_o").cast(pl.Int32).alias("rank_within_country")
    ).filter(pl.col("rank_within_country") <= TOP_K_CORRIDOR).drop("_rank_score")

    # Attach partner_name from the lookup.
    name_lookup = country_lookup.select([
        pl.col("iso3").alias("iso3_d"),
        pl.col("name").alias("partner_name"),
    ])
    agg = agg.join(name_lookup, on="iso3_d", how="left").with_columns(
        pl.col("partner_name").fill_null(pl.col("iso3_d"))
    )

    out = agg.select([
        pl.col("iso3_o").alias("iso3"),
        pl.col("iso3_d").alias("partner_iso3"),
        pl.col("partner_name"),
        pl.col("contribution").cast(pl.Float64),
        pl.col("trade_value").cast(pl.Float64),
        pl.col("derisked").cast(pl.Boolean),
        pl.col("rank_within_country"),
    ]).sort(["iso3", "rank_within_country"])

    return out


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------
def write_and_log(df: pl.DataFrame, path: str) -> tuple[int, float]:
    df.write_parquet(path, compression="zstd")
    n = df.height
    sz = os.path.getsize(path) / 1e6
    log(f"  wrote {os.path.basename(path)}  rows={n:,}  size={sz:.2f} MB  iso3_distinct={df['iso3'].n_unique() if 'iso3' in df.columns else 'NA'}")
    return n, sz


def _df_to_records(df: pl.DataFrame) -> list[dict]:
    """Convert a polars DataFrame to a list of plain JSON-serialisable dicts.

    NaN/None floats are coerced to JSON null. Numpy / polars scalars are
    cast to native Python via ``to_dicts``. Boolean columns are preserved.
    """
    import math

    records = df.to_dicts()
    cleaned = []
    for r in records:
        out = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                out[k] = None
            else:
                out[k] = v
        cleaned.append(out)
    return cleaned


def _write_json(obj, path: str, indent: int | None = None) -> float:
    """Write JSON object to disk and return file size in MB."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=indent, allow_nan=False, default=str)
    return os.path.getsize(path) / 1e6


def emit_json(country_lookup: pl.DataFrame,
              par: pl.DataFrame,
              div: pl.DataFrame,
              cor: pl.DataFrame,
              meta: dict) -> None:
    """Stage 2: write slim JSON aggregates to ``site/_data/`` for the
    static Quarto + Observable JS site.

    Files written
    -------------
    - sos_country.json            — country-level composite + components + quadrant
    - products_at_risk.json       — products_at_risk (full)
    - diversification_opps.json   — diversification_opps (full)
    - corridors_top5.json         — corridor_top5 (full)
    - treemap_<iso3>.json         — per-country product slices (top-50 + Other)
    - webapp_meta.json            — copy of meta with site build info
    """
    log("Building JSON outputs for site/_data/ ...")
    os.makedirs(DIR_SITE, exist_ok=True)

    # -------- 1. sos_country.json -------------------------------------------
    sos = pl.read_parquet(P_SOS_COUNTRY)
    quad = pl.read_parquet(os.path.join(DIR_CLEAN, "feasibility_quadrant.parquet"))
    overlap = [c for c in quad.columns if c in sos.columns and c != "iso3"]
    quad = quad.drop(overlap)
    merged = sos.join(quad, on="iso3", how="left").join(
        country_lookup.select(["iso3", "name", "region"]),
        on="iso3", how="left",
    )

    keep = [
        "iso3", "name", "region",
        "sos_composite", "sos_fatf", "sos_fdi", "sos_amld",
        "rank_composite",
        "quadrant", "quadrant_label",
        "kaopen_score", "infrastructure_score",
        "trade_derisked", "trade_fatf", "trade_amld",
        "n_derisked_partners",
    ]
    keep = [c for c in keep if c in merged.columns]
    sos_country_df = merged.select(keep).sort("iso3")
    p = os.path.join(DIR_SITE, "sos_country.json")
    sz = _write_json(_df_to_records(sos_country_df), p)
    log(f"  wrote sos_country.json  rows={sos_country_df.height}  size={sz:.3f} MB")

    # -------- 2. products_at_risk.json --------------------------------------
    p = os.path.join(DIR_SITE, "products_at_risk.json")
    sz = _write_json(_df_to_records(par), p)
    log(f"  wrote products_at_risk.json  rows={par.height}  size={sz:.3f} MB")

    # -------- 3. diversification_opps.json ----------------------------------
    p = os.path.join(DIR_SITE, "diversification_opps.json")
    sz = _write_json(_df_to_records(div), p)
    log(f"  wrote diversification_opps.json  rows={div.height}  size={sz:.3f} MB")

    # -------- 4. corridors_top5.json ----------------------------------------
    p = os.path.join(DIR_SITE, "corridors_top5.json")
    sz = _write_json(_df_to_records(cor), p)
    log(f"  wrote corridors_top5.json  rows={cor.height}  size={sz:.3f} MB")

    # -------- 5. treemap_<iso3>.json ----------------------------------------
    log("  building per-country treemap slices ...")
    cprod = pl.read_parquet(P_SOS_PRODUCT)
    # Pick canonical SOS column (matches build_products_at_risk).
    sos_col = "sos_composite" if "sos_composite" in cprod.columns else "sos_composite_int"
    # Build slim slice with required cols.
    slim = cprod.select([
        "iso3",
        pl.col("hs4"),
        pl.col(sos_col).alias("sos"),
        pl.col("trade_total").alias("exposure"),
        pl.col("pci_std"),
    ]).filter(pl.col("exposure").is_not_null())

    # HS4 -> HS-section coarse mapping. The hs4 column is already a 2-digit
    # HS chapter string ('01'..'97') in this build, so we group by HS section
    # using the standard chapter -> section ranges.
    def hs2_to_section(hs2: str) -> str:
        try:
            n = int(hs2)
        except (TypeError, ValueError):
            return "Other"
        if 1 <= n <= 5: return "Animal products"
        if 6 <= n <= 14: return "Vegetable products"
        if 15 <= n <= 15: return "Animal/vegetable fats"
        if 16 <= n <= 24: return "Foodstuffs"
        if 25 <= n <= 27: return "Mineral products"
        if 28 <= n <= 38: return "Chemicals"
        if 39 <= n <= 40: return "Plastics & rubber"
        if 41 <= n <= 43: return "Hides & leather"
        if 44 <= n <= 49: return "Wood & paper"
        if 50 <= n <= 63: return "Textiles"
        if 64 <= n <= 67: return "Footwear & headwear"
        if 68 <= n <= 71: return "Stone, ceramics & jewellery"
        if 72 <= n <= 83: return "Metals"
        if 84 <= n <= 85: return "Machinery & electronics"
        if 86 <= n <= 89: return "Transportation"
        if 90 <= n <= 92: return "Instruments"
        if 93 <= n <= 93: return "Arms"
        if 94 <= n <= 96: return "Misc. manufactures"
        if 97 <= n <= 99: return "Art & antiques"
        return "Other"

    treemap_dir = os.path.join(DIR_SITE, "treemap")
    os.makedirs(treemap_dir, exist_ok=True)
    iso3_list = country_lookup["iso3"].to_list()
    sizes = []
    for iso3 in iso3_list:
        sub = slim.filter(pl.col("iso3") == iso3)
        if sub.height == 0:
            continue
        # Sort by exposure desc, take top 50, aggregate the rest into "Other".
        sub_sorted = sub.sort("exposure", descending=True)
        top = sub_sorted.head(50)
        rest = sub_sorted.tail(max(sub_sorted.height - 50, 0))

        rows = []
        for r in top.to_dicts():
            hs2 = str(r["hs4"]).zfill(2) if r["hs4"] is not None else "00"
            sec = hs2_to_section(hs2)
            sos_v = r.get("sos")
            exp_v = r.get("exposure")
            pci_v = r.get("pci_std")
            rows.append({
                "hs4": hs2,
                "hs_section": sec,
                "sos": float(sos_v) if sos_v is not None and not (isinstance(sos_v, float) and sos_v != sos_v) else None,
                "exposure": float(exp_v) if exp_v is not None and not (isinstance(exp_v, float) and exp_v != exp_v) else 0.0,
                "pci_std": float(pci_v) if pci_v is not None and not (isinstance(pci_v, float) and pci_v != pci_v) else None,
            })
        if rest.height > 0:
            other_exposure = float(rest["exposure"].sum() or 0.0)
            sos_mean = rest.select(pl.col("sos").mean()).item()
            pci_mean = rest.select(pl.col("pci_std").mean()).item()
            rows.append({
                "hs4": "Other",
                "hs_section": "Other",
                "sos": float(sos_mean) if sos_mean is not None and not (isinstance(sos_mean, float) and sos_mean != sos_mean) else None,
                "exposure": other_exposure,
                "pci_std": float(pci_mean) if pci_mean is not None and not (isinstance(pci_mean, float) and pci_mean != pci_mean) else None,
            })
        path = os.path.join(treemap_dir, f"treemap_{iso3}.json")
        sz = _write_json(rows, path)
        sizes.append(sz)
    if sizes:
        log(f"  wrote {len(sizes)} treemap_<iso3>.json files  total={sum(sizes):.2f} MB  median={sorted(sizes)[len(sizes)//2]:.3f} MB")

    # -------- 6. world.geojson (Natural Earth low-res, with ISO_A3) ----------
    # Used by the choropleth on index.qmd. Natural Earth bundles ISO_A3 keys
    # in feature.properties, so the join is exact (no name-mismatch fallback
    # needed). The same file feeds the matplotlib choropleths in 19_*.py.
    ne_src = os.path.join(PROJECT, "data", "raw", "natural_earth",
                          "ne_110m_admin_0_countries.geojson")
    if os.path.exists(ne_src):
        ne_dst = os.path.join(DIR_SITE, "world.geojson")
        with open(ne_src, "rb") as fsrc, open(ne_dst, "wb") as fdst:
            fdst.write(fsrc.read())
        sz = os.path.getsize(ne_dst) / 1e6
        log(f"  copied world.geojson  size={sz:.3f} MB")
    else:
        log(f"  WARN: Natural Earth geojson missing at {ne_src}; "
            f"choropleth will fall back to CDN if site/_ojs/ uses one.")

    # -------- 7. webapp_meta.json -------------------------------------------
    p = os.path.join(DIR_SITE, "webapp_meta.json")
    sz = _write_json(meta, p, indent=2)
    log(f"  wrote webapp_meta.json  size={sz:.3f} MB")

    # Total payload check.
    total_mb = 0.0
    for root, _, files in os.walk(DIR_SITE):
        for f in files:
            total_mb += os.path.getsize(os.path.join(root, f)) / 1e6
    log(f"Total site/_data/ payload: {total_mb:.2f} MB")
    if total_mb >= 5.0:
        log("  WARN: payload exceeds 5 MB target.")
    else:
        log("  OK: payload within 5 MB target.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Build slim webapp aggregates.")
    parser.add_argument(
        "--format",
        choices=["parquet", "json", "both"],
        default="parquet",
        help="Output format. 'json' (Stage 2) is a stub; 'both' writes parquet and prints stub message.",
    )
    args = parser.parse_args()

    t_start = time.time()
    os.makedirs(DIR_OUT, exist_ok=True)

    log(f"Project root: {PROJECT}")
    log(f"Output dir:   {DIR_OUT}")
    log(f"Format:       {args.format}")
    log(f"Latest year:  {YEAR_LATEST}")
    log("")

    # ---- Discover the iso3 spine -----------------------------------------
    sos_iso3 = set(pl.read_parquet(P_SOS_COUNTRY, columns=["iso3"])["iso3"].to_list())
    rca_iso3 = set(pl.read_parquet(P_RCA, columns=["iso3"])["iso3"].to_list())
    den_iso3 = set(pl.read_parquet(P_DENSITY, columns=["iso3"])["iso3"].to_list())
    all_iso3 = sos_iso3 | rca_iso3 | den_iso3
    log(f"ISO3 spine: |sos|={len(sos_iso3)}  |rca|={len(rca_iso3)}  |den|={len(den_iso3)}  |union|={len(all_iso3)}")

    # ---- Output 1: country_lookup ----------------------------------------
    country_lookup = build_country_lookup(sos_iso3=sos_iso3, all_iso3=all_iso3)
    p_country = os.path.join(DIR_OUT, "country_lookup.parquet")
    n_country, _ = write_and_log(country_lookup, p_country)

    spine_iso3 = country_lookup["iso3"].to_list()

    # ---- Output 2: products_at_risk --------------------------------------
    par = build_products_at_risk(spine_iso3=spine_iso3)
    p_par = os.path.join(DIR_OUT, "products_at_risk.parquet")
    n_par, _ = write_and_log(par, p_par)

    # ---- Output 3: diversification_opps ----------------------------------
    div = build_diversification_opps(spine_iso3=spine_iso3)
    p_div = os.path.join(DIR_OUT, "diversification_opps.parquet")
    n_div, _ = write_and_log(div, p_div)

    # ---- Output 4: corridor_top5 -----------------------------------------
    cor = build_corridor_top5(country_lookup=country_lookup)
    p_cor = os.path.join(DIR_OUT, "corridor_top5.parquet")
    n_cor, _ = write_and_log(cor, p_cor)

    # ---- Coverage check --------------------------------------------------
    log("")
    log("Coverage diagnostics (distinct iso3 per output, must be >= 200):")
    for label, df in [("country_lookup", country_lookup), ("products_at_risk", par),
                      ("diversification_opps", div), ("corridor_top5", cor)]:
        n_iso3 = df["iso3"].n_unique()
        flag = "OK " if n_iso3 >= 200 else "WARN"
        log(f"  [{flag}] {label}: {n_iso3} distinct iso3")

    # ---- Spot checks -----------------------------------------------------
    log("")
    log("Spot checks (HTI, USA, FJI):")
    for iso3 in ["HTI", "USA", "FJI"]:
        n_par_i = par.filter(pl.col("iso3") == iso3).height
        n_div_i = div.filter(pl.col("iso3") == iso3).height
        n_cor_i = cor.filter(pl.col("iso3") == iso3).height
        in_lookup = country_lookup.filter(pl.col("iso3") == iso3).height
        log(f"  {iso3}: lookup={in_lookup}  par={n_par_i}  div={n_div_i}  cor={n_cor_i}")

    # ---- Output 5: webapp_meta.json --------------------------------------
    meta = {
        "build_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_commit": get_source_commit(),
        "year_latest": YEAR_LATEST,
        "files": [
            "country_lookup.parquet",
            "products_at_risk.parquet",
            "diversification_opps.parquet",
            "corridor_top5.parquet",
        ],
        "row_counts": {
            "country_lookup":       n_country,
            "products_at_risk":     n_par,
            "diversification_opps": n_div,
            "corridor_top5":        n_cor,
        },
        "design_notes": {
            "products_at_risk_sos_col": "sos_composite (top choice; matches country-level composite)",
            "diversification_score":    "density * pci_std",
            "corridor_metric":          "trade_value * max(-pf_cbr, 0); pf_cbr is FDI-derisked proxy",
            "year_filter":              YEAR_LATEST,
        },
    }
    p_meta = os.path.join(DIR_OUT, "webapp_meta.json")
    with open(p_meta, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    sz = os.path.getsize(p_meta) / 1e6
    log(f"  wrote webapp_meta.json  size={sz:.3f} MB")

    # ---- Total payload ---------------------------------------------------
    total_mb = sum(
        os.path.getsize(os.path.join(DIR_OUT, f)) for f in os.listdir(DIR_OUT)
    ) / 1e6
    log("")
    log(f"Total payload (data/cleaned/webapp/): {total_mb:.2f} MB")
    if total_mb >= 50:
        log("  WARNING: payload exceeds 50 MB budget.")
    else:
        log("  OK: payload within 50 MB budget.")

    # ---- JSON branch (Stage 2: site/_data) -------------------------------
    if args.format in ("json", "both"):
        emit_json(country_lookup=country_lookup,
                  par=par, div=div, cor=cor, meta=meta)

    log("")
    log(f"Done in {time.time() - t_start:.1f}s.")


if __name__ == "__main__":
    main()
