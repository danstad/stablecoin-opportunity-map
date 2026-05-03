"""
07_estimation_extensive.py — Extensive margin (diversification) estimation

Spec 4 of the stablecoin opportunity map: does FDI-derisking impede a country's
ability to diversify into NEW complex products?

Outcome
-------
    has_rca_ipt = 1{RCA_ipt >= 1}
        Country i starts (or continues) competitively exporting product p in year t.

Mechanism
---------
    Relatedness density (Hidalgo-Hausmann) tells us where a country *could* expand.
    Product complexity (PCI) tells us how sophisticated each product is.
    Payment-friction (here: country-level FDI-derisking exposure, fraction of
    bilateral partners whose FDI dropped >50% from a 2015-2017 base period)
    tells us how reliably the country can plug into the cross-border financial
    plumbing complex products require.

    H1: density predicts has_rca > 0  (Hausmann/Hidalgo prior)
    H2: density * pci  predicts has_rca   ("denser path into complex product")
    H3: density * pf_country  weakens the density gradient (financial friction
        impedes diversification overall)
    H4 (KEY):  density * pci * pf_country  is NEGATIVE — high-PF countries
        lose their density-based access disproportionately for COMPLEX products.

Specifications
--------------
    E0 LPM baseline:        density + pci + density:pci    | iso3 + hs4 + year
    E1 LPM + PF main:       + pf_country
    E2 LPM + density:PF:    + density:pf_country
    E3 LPM TRIPLE INT:      + density:pci:pf_country     <-- key result
    E4 Logit (E3 form):     same RHS, family=binomial

    All standard errors clustered at iso3 (country) level.
    Sample restricted to 2018-2023 for panel consistency.

Note on `pf_country`
--------------------
The `pf_country` column in `panel_extensive.parquet` was constructed in the R
pipeline using country-level FDI-derisking exposure (Chinn-Ito KAOPEN was
unavailable). This script REBUILDS that column from `imf_fdi_bilateral.parquet`
to make the Python pipeline self-contained, and overwrites the existing column.
The variable is `frac_derisked`: the share of a country's bilateral-FDI partners
whose FDI fell to <50% of the 2015-2017 mean.

Inputs
------
    data/cleaned/panel_extensive.parquet
    data/cleaned/imf_fdi_bilateral.parquet

Outputs
-------
    data/cleaned/estimates_extensive.pkl
    paper/tables/07_estimation_extensive/extensive_panel.csv
    paper/tables/07_estimation_extensive/extensive_panel.tex
"""

from __future__ import annotations

import gc
import io
import os
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pyfixest as pf

# Windows cp1252 console fix
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 20260502
np.random.seed(SEED)

PROJECT   = Path(__file__).resolve().parents[2]
DIR_CLEAN = PROJECT / "data" / "cleaned"
TABLE_DIR = PROJECT / "paper" / "tables" / "07_estimation_extensive"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DIR_CLEAN / "panel_extensive.parquet"
FDI_PATH   = DIR_CLEAN / "imf_fdi_bilateral.parquet"

BASE_PERIOD  = [2015, 2016, 2017]
SAMPLE_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
DERISK_RATIO = 0.50  # ratio < 0.5 of base = "derisked"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Step 1: country-year frac_derisked
# ---------------------------------------------------------------------------
def build_frac_derisked() -> pl.DataFrame:
    """Construct country-year fraction-of-derisked-partners from bilateral FDI."""
    log("Building country-year frac_derisked from bilateral FDI ...")

    fdi = (
        pl.scan_parquet(FDI_PATH)
        .select(["iso3_o", "iso3_d", "year", "fdi_bilateral"])
        .filter(pl.col("fdi_bilateral").is_not_null())
        .collect()
    )
    log(f"  FDI rows loaded: {fdi.height:,}")

    # Base-period mean per (origin, destination) pair
    base = (
        fdi.filter(pl.col("year").is_in(BASE_PERIOD))
        .group_by(["iso3_o", "iso3_d"])
        .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
    )
    log(f"  Base-period pairs: {base.height:,}")

    # Year-by-year derisking flag
    yr = (
        fdi.filter(pl.col("year").is_in(SAMPLE_YEARS))
        .join(base, on=["iso3_o", "iso3_d"], how="left")
        .with_columns(
            (
                pl.when(pl.col("fdi_base") > 0)
                .then(pl.col("fdi_bilateral") / pl.col("fdi_base"))
                .otherwise(None)
            ).alias("fdi_ratio")
        )
        .with_columns(
            (
                pl.col("fdi_ratio").is_not_null()
                & (pl.col("fdi_ratio") < DERISK_RATIO)
            )
            .cast(pl.Int8)
            .alias("derisked")
        )
    )

    # Aggregate: country-year share of partners derisked
    cy = (
        yr.group_by([pl.col("iso3_o").alias("iso3"), "year"])
        .agg(
            pl.col("derisked").mean().alias("frac_derisked"),
            pl.col("derisked").sum().alias("n_derisked"),
            pl.len().alias("n_partners"),
        )
        .sort(["iso3", "year"])
    )

    mean_pf = cy["frac_derisked"].mean()
    log(f"  Country-year obs: {cy.height:,}")
    log(f"  Mean frac_derisked: {mean_pf:.3f}")
    log(f"  Country-years with any derisking: "
        f"{cy.filter(pl.col('frac_derisked') > 0).height:,}")
    return cy


# ---------------------------------------------------------------------------
# Step 2: assemble estimation sample
# ---------------------------------------------------------------------------
def build_sample(frac_derisked: pl.DataFrame) -> pd.DataFrame:
    """Load extensive panel, merge frac_derisked, build interactions."""
    log("Loading panel_extensive.parquet ...")
    ext = (
        pl.scan_parquet(PANEL_PATH)
        .select(["iso3", "hs4", "year", "has_rca", "density", "pci_std"])
        .filter(pl.col("year").is_in(SAMPLE_YEARS))
        .collect()
    )
    log(f"  Rows: {ext.height:,}, "
        f"countries: {ext['iso3'].n_unique():,}, "
        f"products: {ext['hs4'].n_unique():,}")

    # Cast year so the join key types match (panel: i32, frac_derisked: i64)
    ext = ext.with_columns(pl.col("year").cast(pl.Int64))
    fd  = frac_derisked.with_columns(pl.col("year").cast(pl.Int64))

    # Merge frac_derisked as pf_country
    merged = ext.join(
        fd.select(["iso3", "year", pl.col("frac_derisked").alias("pf_country")]),
        on=["iso3", "year"],
        how="left",
    ).with_columns(pl.col("pf_country").fill_null(0.0))

    n_pf_match = merged.filter(pl.col("pf_country") > 0).height
    log(f"  PF non-zero rows: {n_pf_match:,} "
        f"({100 * n_pf_match / merged.height:.1f}%)")

    # Drop rows missing critical RHS variables
    est = merged.drop_nulls(["density", "pci_std", "has_rca"])
    log(f"  Estimation sample after drop_nulls: {est.height:,}")

    # Convert to pandas for pyfixest
    df = est.to_pandas()

    # Build interactions
    df["density_x_pci"]    = df["density"] * df["pci_std"]
    df["density_x_pf"]     = df["density"] * df["pf_country"]
    df["pf_x_pci"]         = df["pf_country"] * df["pci_std"]
    df["density_x_pci_x_pf"] = df["density"] * df["pci_std"] * df["pf_country"]

    # FE keys must be strings/categoricals for pyfixest
    for c in ("iso3", "hs4"):
        df[c] = df[c].astype(str)
    df["year"] = df["year"].astype(int)
    df["has_rca"] = df["has_rca"].astype(int)

    return df


# ---------------------------------------------------------------------------
# Step 3: estimation
# ---------------------------------------------------------------------------
SPECS = [
    ("E0",
     "has_rca ~ density + pci_std + density:pci_std | iso3 + hs4 + year",
     "feols",
     {"density:pci_std", "density:pf_country", "density:pci_std:pf_country"}),
    ("E1",
     "has_rca ~ density + pci_std + density:pci_std + pf_country | iso3 + hs4 + year",
     "feols",
     {"density:pci_std", "density:pf_country", "density:pci_std:pf_country"}),
    ("E2",
     "has_rca ~ density + pci_std + density:pci_std + pf_country + density:pf_country | iso3 + hs4 + year",
     "feols",
     {"density:pci_std", "density:pf_country", "density:pci_std:pf_country"}),
    ("E3",
     "has_rca ~ density + pci_std + density:pci_std + pf_country + density:pf_country + density:pci_std:pf_country | iso3 + hs4 + year",
     "feols",
     {"density:pci_std", "density:pf_country", "density:pci_std:pf_country"}),
    ("E4",
     "has_rca ~ density + pci_std + density:pci_std + pf_country + density:pf_country + density:pci_std:pf_country | iso3 + hs4 + year",
     "feglm",
     {"density:pci_std", "density:pf_country", "density:pci_std:pf_country"}),
]

# Display names for table rows (LHS = pyfixest term, RHS = printable label)
TERM_LABELS = {
    "density":                    "Relatedness density",
    "pci_std":                    "PCI (standardized)",
    "density:pci_std":            "Density x PCI",
    "pf_country":                 "Frac. derisked (PF)",
    "density:pf_country":         "Density x PF",
    "pf_country:pci_std":         "PF x PCI",
    "density:pci_std:pf_country": "Density x PCI x PF (triple)",
}

# Order of rows in the printed table
TERM_ORDER = [
    "density",
    "pci_std",
    "density:pci_std",
    "pf_country",
    "density:pf_country",
    "density:pci_std:pf_country",
]


def fit_one(label: str, formula: str, kind: str, df: pd.DataFrame) -> dict:
    """Fit a single specification, return dict with model and tidy output."""
    log(f"  [{label}] {kind}: {formula}")
    t0 = time.time()
    if kind == "feols":
        m = pf.feols(formula, data=df, vcov={"CRV1": "iso3"})
    elif kind == "feglm":
        # Logit; cluster at iso3
        m = pf.feglm(
            formula,
            data=df,
            family="logit",
            vcov={"CRV1": "iso3"},
        )
    else:
        raise ValueError(f"Unknown kind: {kind}")

    elapsed = time.time() - t0
    coefs = m.coef()
    ses   = m.se()
    pvals = m.pvalue()

    rows = []
    for term in coefs.index:
        rows.append({
            "spec":   label,
            "kind":   kind,
            "term":   term,
            "coef":   float(coefs[term]),
            "se":     float(ses[term]),
            "pvalue": float(pvals[term]),
            "n_obs":  int(getattr(m, "_N", len(df))),
        })

    log(f"    done in {elapsed:.1f}s, terms: {list(coefs.index)}")
    return {"label": label, "kind": kind, "model": m, "rows": rows,
            "n_obs": int(getattr(m, "_N", len(df))), "elapsed": elapsed}


# ---------------------------------------------------------------------------
# Step 4: tables
# ---------------------------------------------------------------------------
def fmt_coef(c: float, p: float) -> str:
    stars = ("***" if p < 0.01 else
             "**"  if p < 0.05 else
             "*"   if p < 0.10 else
             "")
    return f"{c:.4f}{stars}"


def build_csv_long(results: list[dict], path: Path) -> None:
    """Long-format CSV: spec, term, coef, se, p-value."""
    rows = []
    for r in results:
        for row in r["rows"]:
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    log(f"  wrote {path.name} ({len(df)} rows)")


def build_latex(results: list[dict], path: Path) -> None:
    """Bare booktabs tabular: rows = TERM_ORDER, columns = E0..E4."""
    # Build a map: (spec_label, term) -> (coef, se, p)
    cell = {}
    for r in results:
        for row in r["rows"]:
            cell[(row["spec"], row["term"])] = (row["coef"], row["se"], row["pvalue"])

    spec_labels = [r["label"] for r in results]
    n_cols = len(spec_labels)

    lines = []
    col_spec = "l" + "c" * n_cols
    lines.append(rf"\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\toprule")
    header = " & " + " & ".join(f"({i+1})" for i in range(n_cols)) + r" \\"
    lines.append(header)
    sub = " & " + " & ".join(spec_labels) + r" \\"
    lines.append(sub)
    lines.append(r"\midrule")

    # Coefficient block
    for term in TERM_ORDER:
        label = TERM_LABELS.get(term, term)
        coef_cells = []
        se_cells   = []
        for spec in spec_labels:
            if (spec, term) in cell:
                c, se, p = cell[(spec, term)]
                coef_cells.append(fmt_coef(c, p))
                se_cells.append(f"({se:.4f})")
            else:
                coef_cells.append("")
                se_cells.append("")
        lines.append(f"{label} & " + " & ".join(coef_cells) + r" \\")
        lines.append(" & " + " & ".join(se_cells) + r" \\")

    lines.append(r"\midrule")
    # Diagnostics block
    n_row = "Observations & " + " & ".join(
        f"{r['n_obs']:,}" for r in results) + r" \\"
    lines.append(n_row)

    yes_all = " & ".join(["Yes"] * n_cols)
    lines.append(f"Country FE & {yes_all} \\\\")
    lines.append(f"Product (HS4) FE & {yes_all} \\\\")
    lines.append(f"Year FE & {yes_all} \\\\")

    estimator_row = "Estimator & " + " & ".join(
        ("Logit" if r["kind"] == "feglm" else "LPM") for r in results) + r" \\"
    lines.append(estimator_row)

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    path.write_text("\n".join(lines), encoding="utf-8")
    log(f"  wrote {path.name}")


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------
def main() -> None:
    log("=" * 70)
    log("07_estimation_extensive.py — Extensive margin (Spec 4)")
    log("=" * 70)

    # 1. derisking exposure
    fd = build_frac_derisked()

    # 2. estimation sample
    df = build_sample(fd)
    del fd
    gc.collect()

    log(f"Final sample: {len(df):,} rows, "
        f"{df['iso3'].nunique():,} countries, "
        f"{df['hs4'].nunique():,} HS4 products, "
        f"years {df['year'].min()}-{df['year'].max()}")

    # 3. fit all specs
    log("-" * 70)
    log("Estimating specifications ...")
    log("-" * 70)
    results = []
    for label, formula, kind, _interest in SPECS:
        try:
            r = fit_one(label, formula, kind, df)
            results.append(r)
        except Exception as e:
            log(f"  [{label}] FAILED: {e}")
            results.append({
                "label": label, "kind": kind, "model": None,
                "rows": [], "n_obs": 0, "elapsed": 0.0, "error": str(e),
            })

    converged = [r for r in results if r["model"] is not None]
    log(f"Converged specs: {len(converged)}/{len(results)}")

    # 4. save pickle
    pkl_path = DIR_CLEAN / "estimates_extensive.pkl"
    # Models themselves can be heavy/non-portable; save tidy rows + metadata.
    payload = []
    for r in results:
        payload.append({
            "label":   r["label"],
            "kind":    r["kind"],
            "rows":    r["rows"],
            "n_obs":   r["n_obs"],
            "elapsed": r["elapsed"],
            "error":   r.get("error"),
        })
    with open(pkl_path, "wb") as f:
        pickle.dump(payload, f)
    log(f"Saved {pkl_path.name}")

    # 5. tables
    log("-" * 70)
    log("Writing tables ...")
    log("-" * 70)
    build_csv_long(results, TABLE_DIR / "extensive_panel.csv")
    build_latex(results,    TABLE_DIR / "extensive_panel.tex")

    # 6. console summary — highlight the triple interaction
    log("=" * 70)
    log("KEY RESULT — Triple interaction (Density x PCI x PF)")
    log("=" * 70)
    triple_term = "density:pci_std:pf_country"
    for r in results:
        match = next((row for row in r["rows"] if row["term"] == triple_term),
                     None)
        if match is None:
            log(f"  [{r['label']:>3}] {r['kind']:>5}  (no triple interaction)")
            continue
        stars = ("***" if match["pvalue"] < 0.01 else
                 "**"  if match["pvalue"] < 0.05 else
                 "*"   if match["pvalue"] < 0.10 else "")
        log(f"  [{r['label']:>3}] {r['kind']:>5}  "
            f"coef={match['coef']:+.4f}{stars:<3}  "
            f"SE={match['se']:.4f}  p={match['pvalue']:.4f}  "
            f"N={match['n_obs']:,}")

    log("Done.")


if __name__ == "__main__":
    main()
