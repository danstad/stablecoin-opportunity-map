"""
01_preprocess_baci.py — Import BACI HS12, aggregate to HS4, build panel skeleton.

This is the computational bottleneck of the pipeline. Uses polars for speed.

Inputs:  data/raw/BACI_HS12_V202601/BACI_HS12_Y{2015..2024}_V202601.csv
         data/raw/BACI_HS12_V202601/country_codes_V202601.csv
Outputs: data/cleaned/baci_hs4.parquet          (positive flows only, ~30-50M rows)
         data/cleaned/baci_hs4_hs2_agg.parquet   (HS2 aggregation for fallback)
         data/cleaned/panel_skeleton.parquet      (with zeros for active pairs, ~216M rows)
         data/cleaned/active_pairs.parquet        (list of active exporter-importer pairs)
         data/cleaned/baci_diagnostics.json       (row counts, coverage stats)
"""

import json
import logging
import sys
import time
from pathlib import Path

import polars as pl

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BACI_DIR = RAW_DIR / "BACI_HS12_V202601"
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_YEARS = list(range(2015, 2025))  # 2015-2024 (extended from 2023)
MIN_YEARS_ACTIVE = 3  # pairs must have >= 3 years of positive trade
EXCLUDED_HS_CHAPTERS = ["93", "97", "98", "99"]  # arms, special transactions
BACI_VERSION = "V202601"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ===================================================================
# 1. Load BACI country code concordance
# ===================================================================
def load_country_codes() -> pl.DataFrame:
    """Load BACI numeric-to-ISO3 country code mapping.

    V202601 file has columns: country_code, country_name, country_iso2, country_iso3
    """
    path = BACI_DIR / f"country_codes_{BACI_VERSION}.csv"
    if not path.exists():
        log.error(f"Country code file not found: {path}")
        sys.exit(1)

    log.info(f"Loading country codes from: {path.name}")
    df = pl.read_csv(path, infer_schema_length=1000)
    log.info(f"  Columns: {df.columns}")

    # V202601 format: country_code, country_name, country_iso2, country_iso3
    df = df.select([
        pl.col("country_code").cast(pl.Int64),
        pl.col("country_iso3").cast(pl.Utf8).alias("iso3"),
    ]).filter(pl.col("iso3").is_not_null() & (pl.col("iso3") != ""))

    log.info(f"  {len(df)} country codes loaded")
    return df


# ===================================================================
# 2. Import and aggregate BACI
# ===================================================================
def process_one_year(year: int, country_codes: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Process a single BACI year: read, map ISO3, aggregate to HS4 and HS2."""
    path = BACI_DIR / f"BACI_HS12_Y{year}_{BACI_VERSION}.csv"
    if not path.exists():
        log.warning(f"  BACI file not found for {year}: {path.name}, skipping")
        return None, None

    t0 = time.time()

    # Build ISO3 lookup dicts for fast mapping (avoid polars join on large frames)
    iso_map = dict(zip(
        country_codes["country_code"].to_list(),
        country_codes["iso3"].to_list(),
    ))

    df = pl.read_csv(
        path,
        schema_overrides={
            "t": pl.Int32, "i": pl.Int64, "j": pl.Int64,
            "k": pl.Utf8, "v": pl.Float64, "q": pl.Float64,
        },
        ignore_errors=True,
    )

    # Map country codes using replace (much faster than join for this)
    df = df.with_columns(
        pl.col("i").replace_strict(iso_map, default=None).alias("iso3_o"),
        pl.col("j").replace_strict(iso_map, default=None).alias("iso3_d"),
        pl.col("k").str.slice(0, 4).alias("hs4"),
        pl.col("k").str.slice(0, 2).alias("hs2"),
    )

    # Drop unmapped and excluded chapters
    df = df.filter(
        pl.col("iso3_o").is_not_null()
        & pl.col("iso3_d").is_not_null()
        & ~pl.col("hs2").is_in(EXCLUDED_HS_CHAPTERS)
    )

    # Aggregate to HS4
    hs4 = (
        df.group_by(["t", "iso3_o", "iso3_d", "hs4"])
        .agg([
            pl.col("v").sum().alias("trade_value"),
            pl.col("q").sum().alias("trade_quantity"),
        ])
        .rename({"t": "year"})
    )

    # Aggregate to HS2
    hs2 = (
        df.group_by(["t", "iso3_o", "iso3_d", "hs2"])
        .agg([
            pl.col("v").sum().alias("trade_value"),
            pl.col("q").sum().alias("trade_quantity"),
        ])
        .rename({"t": "year"})
    )

    elapsed = time.time() - t0
    log.info(f"  {year}: {len(df):,} rows -> {len(hs4):,} HS4 / {len(hs2):,} HS2  ({elapsed:.1f}s)")

    return hs4, hs2


def import_baci(country_codes: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Read all yearly BACI CSVs one at a time, write each year to parquet,
    then read back as a lazy scan. Avoids holding all years in memory.
    """
    import pyarrow.parquet as pq

    temp_hs4_dir = CLEAN_DIR / "_temp_hs4"
    temp_hs2_dir = CLEAN_DIR / "_temp_hs2"
    temp_hs4_dir.mkdir(exist_ok=True)
    temp_hs2_dir.mkdir(exist_ok=True)

    years_processed = []

    for year in SAMPLE_YEARS:
        hs4, hs2 = process_one_year(year, country_codes)
        if hs4 is not None:
            hs4.write_parquet(temp_hs4_dir / f"{year}.parquet")
            hs2.write_parquet(temp_hs2_dir / f"{year}.parquet")
            years_processed.append(year)
            # Free memory
            del hs4, hs2

    if not years_processed:
        log.error(f"No BACI files found in {BACI_DIR}!")
        sys.exit(1)

    # Read back and concatenate from parquet (much more memory-efficient)
    log.info("Reading back aggregated years from parquet...")
    baci_hs4 = pl.scan_parquet(temp_hs4_dir / "*.parquet").sort(
        ["year", "iso3_o", "iso3_d", "hs4"]
    ).collect()
    log.info(f"  HS4 total: {len(baci_hs4):,} rows")

    baci_hs2 = pl.scan_parquet(temp_hs2_dir / "*.parquet").sort(
        ["year", "iso3_o", "iso3_d", "hs2"]
    ).collect()
    log.info(f"  HS2 total: {len(baci_hs2):,} rows")

    # Clean up temp files
    import shutil
    shutil.rmtree(temp_hs4_dir)
    shutil.rmtree(temp_hs2_dir)
    log.info("  Temp files cleaned up")

    return baci_hs4, baci_hs2


# ===================================================================
# 3. Identify active pairs and build panel skeleton
# ===================================================================
def build_panel_skeleton(baci_hs4: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Identify active country pairs and expand to full (pair x product x year) grid.
    Fill missing cells with zero trade.
    """
    # Identify active pairs: any positive trade in sample period, >= MIN_YEARS_ACTIVE years
    log.info("Identifying active country pairs...")
    pair_years = (
        baci_hs4
        .filter(pl.col("trade_value") > 0)
        .group_by(["iso3_o", "iso3_d"])
        .agg(pl.col("year").n_unique().alias("n_years"))
        .filter(pl.col("n_years") >= MIN_YEARS_ACTIVE)
    )
    n_pairs = len(pair_years)
    log.info(f"  Active pairs (>= {MIN_YEARS_ACTIVE} years): {n_pairs:,}")

    active_pairs = pair_years.select(["iso3_o", "iso3_d"])

    # Get unique products and years
    products = baci_hs4.select("hs4").unique().sort("hs4")
    years = pl.DataFrame({"year": SAMPLE_YEARS})
    n_products = len(products)
    n_years = len(years)

    total_cells = n_pairs * n_products * n_years
    log.info(
        f"  Panel dimensions: {n_pairs:,} pairs x {n_products:,} products x "
        f"{n_years} years = {total_cells:,} cells"
    )

    if total_cells > 200_000_000:
        log.warning(
            f"  Panel has {total_cells:,} cells -- this may exceed memory. "
            "Consider using HS2 fallback."
        )
        log.info("  Skipping full skeleton build. Saving active_pairs only.")
        log.info("  Use R/04_merge_panel.R with arrow for out-of-core merge,")
        log.info("  or re-run with HS2 aggregation.")
        return None, active_pairs

    # Build the full grid via cross joins
    log.info("Building full panel skeleton (this may take a while)...")
    t0 = time.time()
    skeleton = (
        active_pairs
        .join(products, how="cross")
        .join(years, how="cross")
    )
    elapsed = time.time() - t0
    log.info(f"  Skeleton built: {len(skeleton):,} rows in {elapsed:.1f}s")

    # Left-join actual trade values
    log.info("Merging actual trade values onto skeleton...")
    panel = skeleton.join(
        baci_hs4.select(["year", "iso3_o", "iso3_d", "hs4", "trade_value"]),
        on=["year", "iso3_o", "iso3_d", "hs4"],
        how="left",
    )

    # Fill missing trade with 0
    panel = panel.with_columns(
        pl.col("trade_value").fill_null(0.0)
    )

    n_positive = panel.filter(pl.col("trade_value") > 0).height
    zero_share = 1 - (n_positive / len(panel))
    log.info(f"  Zero share: {zero_share:.1%} ({n_positive:,} positive flows)")

    # Add pair identifier for FEs
    panel = panel.with_columns(
        (pl.col("iso3_o") + "_" + pl.col("iso3_d")).alias("pair"),
        (pl.col("iso3_o") + "_" + pl.col("year").cast(pl.Utf8)).alias("exporter_year"),
        (pl.col("iso3_d") + "_" + pl.col("year").cast(pl.Utf8)).alias("importer_year"),
    )

    return panel, active_pairs


# ===================================================================
# 4. Diagnostics
# ===================================================================
def compute_diagnostics(
    baci_hs4: pl.DataFrame,
    panel: pl.DataFrame | None,
    active_pairs: pl.DataFrame,
) -> dict:
    """Compute and save diagnostic statistics."""
    n_exporters = baci_hs4.select("iso3_o").n_unique()
    n_importers = baci_hs4.select("iso3_d").n_unique()
    n_products = baci_hs4.select("hs4").n_unique()
    n_years = baci_hs4.select("year").n_unique()

    # World trade totals by year
    world_trade = (
        baci_hs4
        .group_by("year")
        .agg(pl.col("trade_value").sum().alias("total_trade_1000usd"))
        .sort("year")
    )

    diagnostics = {
        "timestamp": str(time.strftime("%Y-%m-%d %H:%M:%S")),
        "baci_version": BACI_VERSION,
        "hs_revision": "HS12",
        "sample_years": SAMPLE_YEARS,
        "baci_hs4_rows": len(baci_hs4),
        "panel_skeleton_rows": len(panel) if panel is not None else "SKIPPED (too large)",
        "n_exporters": n_exporters,
        "n_importers": n_importers,
        "n_products_hs4": n_products,
        "n_years": n_years,
        "n_active_pairs": len(active_pairs),
        "zero_share": (
            round(1 - panel.filter(pl.col("trade_value") > 0).height / len(panel), 4)
            if panel is not None else None
        ),
        "world_trade_by_year": {
            str(row["year"]): round(row["total_trade_1000usd"] / 1e6, 2)  # billions USD
            for row in world_trade.iter_rows(named=True)
        },
        "excluded_hs_chapters": EXCLUDED_HS_CHAPTERS,
        "min_years_active": MIN_YEARS_ACTIVE,
    }
    return diagnostics


# ===================================================================
# Main
# ===================================================================
def main():
    log.info("=" * 60)
    log.info("BACI Preprocessing -- HS12 V202601")
    log.info(f"Source: {BACI_DIR}")
    log.info(f"Sample years: {SAMPLE_YEARS[0]}-{SAMPLE_YEARS[-1]}")
    log.info("=" * 60)

    # Step 1: Load country codes
    country_codes = load_country_codes()

    # Step 2: Import and aggregate BACI
    baci_hs4, baci_hs2 = import_baci(country_codes)

    # Step 3: Save positive-flows-only datasets
    out_hs4 = CLEAN_DIR / "baci_hs4.parquet"
    out_hs2 = CLEAN_DIR / "baci_hs4_hs2_agg.parquet"
    log.info(f"Saving HS4 positive flows: {out_hs4}")
    baci_hs4.write_parquet(out_hs4)
    log.info(f"Saving HS2 aggregation: {out_hs2}")
    baci_hs2.write_parquet(out_hs2)

    # Step 4: Build panel skeleton with zeros
    panel, active_pairs = build_panel_skeleton(baci_hs4)

    # Step 5: Save outputs
    out_pairs = CLEAN_DIR / "active_pairs.parquet"
    log.info(f"Saving active pairs: {out_pairs}")
    active_pairs.write_parquet(out_pairs)

    if panel is not None:
        out_panel = CLEAN_DIR / "panel_skeleton.parquet"
        log.info(f"Saving panel skeleton: {out_panel}")
        panel.write_parquet(out_panel)

    # Step 6: Diagnostics
    diag = compute_diagnostics(baci_hs4, panel, active_pairs)
    diag_path = CLEAN_DIR / "baci_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diag, f, indent=2)
    log.info(f"Diagnostics saved: {diag_path}")

    # Print summary
    log.info("\n" + "=" * 60)
    log.info("SUMMARY")
    log.info(f"  BACI version:        {BACI_VERSION}")
    log.info(f"  HS revision:         HS12")
    log.info(f"  Years:               {SAMPLE_YEARS[0]}-{SAMPLE_YEARS[-1]}")
    log.info(f"  HS4 positive flows:  {diag['baci_hs4_rows']:>15,} rows")
    log.info(f"  Panel skeleton:      {diag['panel_skeleton_rows']!s:>15}")
    log.info(f"  Active pairs:        {diag['n_active_pairs']:>15,}")
    log.info(f"  Exporters:           {diag['n_exporters']:>15,}")
    log.info(f"  Importers:           {diag['n_importers']:>15,}")
    log.info(f"  Products (HS4):      {diag['n_products_hs4']:>15,}")
    if diag["zero_share"] is not None:
        log.info(f"  Zero share:          {diag['zero_share']:>14.1%}")
    log.info(f"  World trade by year (billion USD):")
    for yr, val in diag["world_trade_by_year"].items():
        log.info(f"    {yr}: ${val:,.1f}B")
    log.info("=" * 60)
    log.info("Done. Next: run R/01_complexity.R")


if __name__ == "__main__":
    main()
