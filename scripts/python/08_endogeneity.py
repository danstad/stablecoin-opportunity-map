"""
08_endogeneity.py -- Causal-robustness checks via timing on the headline
                     FDI-derisking x PCI specification.

Three estimation layers test whether the headline contemporaneous correlation
reflects a causal payment-friction channel by exploiting the timing of
de-risking events:

  Layer 1 -- Lagged de-risking (causal-channel evidence)
    EN1: trade_value ~ derisked_L1 + derisked_L1:pci_std
    EN2: trade_value ~ derisked_L2 + derisked_L2:pci_std
    Trade contracts are negotiated in advance; if a payment-friction shock
    drove the headline, lagged de-risking should still negatively predict
    complex-product trade. Reverse causality (trade declines causing FDI
    pullout) would imply weaker / null lags.

  Layer 2 -- Lead test (placebo / pre-trends)
    EN3: trade_value ~ derisked_F1 + derisked_F1:pci_std
    Future de-risking should NOT predict current trade. A significant lead
    coefficient would indicate anticipation effects or pre-trends in
    de-risked corridors and would undermine the causal interpretation.

  Layer 3 -- CBR-derived de-risking reduced form
    EN4: trade_value ~ derisked_cbr + derisked_cbr:pci_std
    SKIPPED in this run: BIS CBR data (n_correspondents) is not in the
    panel; the FDI-derived `derisked` indicator already serves the
    de-risking-shock role in the headline. See stdout summary.

Sample lineage (so EN1-EN3 baselines are directly comparable to F0):
  This script applies the SAME row filter used in 12_falsification.py:
  pci_std non-null AND ln_dist non-null. F0 (Falsification baseline,
  contemporaneous derisked x pci_std) = -0.198. EN1/EN2/EN3 use the same
  panel slice and the same 4-FE structure so coefficients can be compared
  on a like-for-like basis.

Sub-sampling lineage (so EN1/EN2/EN3 use the SAME pairs):
  We construct ALL lag/lead derisked indicators on the FULL FDI lookup
  BEFORE subsampling, then subsample 2000 treated + 1000 control pairs
  ONCE. Each spec drops only its own per-row null-lag / null-lead
  observations. This guarantees that EN1, EN2, and EN3 see the same
  underlying corridors -- only the temporal alignment of the treatment
  indicator changes.

The on-disk panel keeps the legacy column name `pf_cbr` for backward
compatibility; substantively this is an FDI-derived proxy. We rename
pf_cbr* -> fdi_proxy* immediately on load (see rename_pf_to_fdi() in
scripts/R/00_config.R and the section 03 footnote in
paper/sections/03_data.tex). This script does not actually use pf_cbr
for estimation -- the derisked indicators are rebuilt from fdi_bilateral
exactly as in 11_robustness.py and 12_falsification.py -- but the rename
is performed for consistency with sister scripts.

Estimator: pyfixest fepois (PPML) with pair-clustered SEs (CRV1: pair).
Fixed effects: exporter_year + importer_year + pair + hs4.

Inputs:  data/cleaned/panel_main_confounders.parquet
Outputs: data/cleaned/estimates_endogeneity.pkl
         paper/tables/08_endogeneity/endogeneity_panel.csv
         paper/tables/08_endogeneity/endogeneity_panel.tex
"""

import os
import sys
import time
import pickle
import warnings
import gc

# Force UTF-8 output on Windows consoles whose default codepage is cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
import polars as pl
import pyfixest as pf

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
PROJECT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_CLEAN = os.path.join(PROJECT, "data", "cleaned")
TABLE_DIR = os.path.join(PROJECT, "paper", "tables", "08_endogeneity")
os.makedirs(TABLE_DIR, exist_ok=True)

PANEL_PATH  = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")
BASE_PERIOD = [2015, 2016, 2017]
POST_YEARS  = [2018, 2019, 2020, 2021, 2022, 2023]

# Subsample sizes (mirror 11_robustness.py / 12_falsification.py /
# 16_confounder_estimation.py). Full ~6M-row panel makes 4 sequential PPMLs
# intractable on 16 GB RAM.
MAX_TREATED_PAIRS = 2000
MAX_CONTROL_PAIRS = 1000

# Reference baseline from 12_falsification.py F0 (same FE, same filter,
# contemporaneous derisked).
F0_BASELINE_COEF = -0.198

# Minimum non-null observations on n_correspondents for Layer 3 to run
LAYER3_MIN_OBS = 1000

np.random.seed(20260502)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Per-spec runner: returns a result dict
# ---------------------------------------------------------------------------
def run_spec(label: str, formula: str, data: pd.DataFrame, treat_var: str,
             vcov) -> dict:
    """Estimate a single PPML spec; extract treat_var x pci_std interaction
    AND the treat_var level coefficient."""
    t0 = time.time()
    out = {
        "label": label,
        "formula": formula,
        "treat_var": treat_var,
        "converged": False,
        "n_obs": np.nan,
        # interaction (treat:pci_std)
        "interaction_name": "",
        "coef": np.nan,
        "se": np.nan,
        "pvalue": np.nan,
        "ci_lo": np.nan,
        "ci_hi": np.nan,
        # level (treat alone)
        "level_name": "",
        "level_coef": np.nan,
        "level_se": np.nan,
        "level_pvalue": np.nan,
        "time_s": np.nan,
        "error": "",
    }
    try:
        m = pf.fepois(formula, data=data, vcov=vcov)
        coefs, ses, pvals = m.coef(), m.se(), m.pvalue()
        elapsed = time.time() - t0
        out["converged"] = True
        out["n_obs"] = int(m._N)
        out["time_s"] = elapsed

        # Interaction: any term containing both treat_var and "pci_std" with ":"
        for name in coefs.index:
            if ":" not in name:
                continue
            if treat_var in name and "pci_std" in name:
                out["interaction_name"] = name
                coef = float(coefs[name])
                se   = float(ses[name])
                out["coef"]   = coef
                out["se"]     = se
                out["pvalue"] = float(pvals[name])
                out["ci_lo"]  = coef - 1.96 * se
                out["ci_hi"]  = coef + 1.96 * se
                break

        # Level term: treat_var on its own (no ":")
        for name in coefs.index:
            if ":" in name:
                continue
            if name == treat_var:
                out["level_name"]    = name
                out["level_coef"]    = float(coefs[name])
                out["level_se"]      = float(ses[name])
                out["level_pvalue"]  = float(pvals[name])
                break

        head_str = (
            f"int={out['coef']:.4f} (SE {out['se']:.4f}, p={out['pvalue']:.4f})"
            if not np.isnan(out["coef"])
            else "int=NA"
        )
        lvl_str = (
            f"lvl={out['level_coef']:.4f} (p={out['level_pvalue']:.4f})"
            if not np.isnan(out["level_coef"])
            else "lvl=NA"
        )
        log(f"  {label}: {head_str} | {lvl_str} | N={out['n_obs']:,} [{elapsed:.0f}s]")
    except Exception as e:
        out["error"] = str(e)
        log(f"  {label}: FAILED -- {e}")
    return out


# ---------------------------------------------------------------------------
# Build derisking lookup, including 1- and 2-year lags AND 1-year lead
# ---------------------------------------------------------------------------
def build_derisking_lookup() -> pl.DataFrame:
    """Construct (pair, year) derisked indicator and lag/lead variants.

    derisked_t = 1 iff fdi_bilateral_t / mean(fdi_bilateral, 2015-2017) < 0.5.
    derisked_L1 = derisked at year-1; derisked_L2 = at year-2;
    derisked_F1 = derisked at year+1.

    Built on the FULL FDI lookup so every (pair, year) row in the
    estimation panel can join to a value. Per-spec sample drops happen in
    main() after merging.
    """
    log("Building derisking lookup from FDI data...")
    t0 = time.time()

    fdi = (
        pl.scan_parquet(PANEL_PATH)
        .select(["pair", "year", "fdi_bilateral"])
        .filter(pl.col("fdi_bilateral").is_not_null())
        .unique(subset=["pair", "year"])
        .collect()
    )
    log(f"  FDI pair-years: {fdi.height:,}")

    base_fdi = (
        fdi.filter(pl.col("year").is_in(BASE_PERIOD))
        .group_by("pair")
        .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
    )

    deri = fdi.join(base_fdi, on="pair", how="left")
    deri = deri.with_columns([
        (pl.col("fdi_bilateral") /
         pl.when(pl.col("fdi_base") > 0).then(pl.col("fdi_base")).otherwise(None)
         ).alias("fdi_ratio"),
    ])
    deri = deri.with_columns([
        (pl.col("fdi_ratio").is_not_null() & (pl.col("fdi_ratio") < 0.50))
        .cast(pl.Int8).fill_null(0).alias("derisked"),
    ])
    deri = deri.select(["pair", "year", "derisked"]).sort(["pair", "year"])

    # Construct lag-1, lag-2 and lead-1 indicators by self-join on
    # (pair, year +/- k). Using join (not pl.shift) so that gaps in the
    # year sequence don't silently produce wrong-period lags.
    lag1 = deri.select([
        pl.col("pair"),
        (pl.col("year") + 1).alias("year"),
        pl.col("derisked").alias("derisked_L1"),
    ])
    lag2 = deri.select([
        pl.col("pair"),
        (pl.col("year") + 2).alias("year"),
        pl.col("derisked").alias("derisked_L2"),
    ])
    lead1 = deri.select([
        pl.col("pair"),
        (pl.col("year") - 1).alias("year"),
        pl.col("derisked").alias("derisked_F1"),
    ])
    deri = deri.join(lag1, on=["pair", "year"], how="left")
    deri = deri.join(lag2, on=["pair", "year"], how="left")
    deri = deri.join(lead1, on=["pair", "year"], how="left")

    log(f"  Derisking lookup: {deri.height:,} rows | "
        f"derisked={deri.filter(pl.col('derisked') == 1).height:,}, "
        f"L1={deri.filter(pl.col('derisked_L1') == 1).height:,}, "
        f"L2={deri.filter(pl.col('derisked_L2') == 1).height:,}, "
        f"F1={deri.filter(pl.col('derisked_F1') == 1).height:,}")

    log(f"  Done in {time.time()-t0:.1f}s")
    return deri


# ---------------------------------------------------------------------------
# Subsample pairs (mirror 11_robustness.py / 12_falsification.py)
# ---------------------------------------------------------------------------
def subsample_pairs(deri: pl.DataFrame) -> list:
    """Stratified subsample: up to MAX_TREATED_PAIRS pairs that experience
    contemporaneous derisking, plus MAX_CONTROL_PAIRS untreated pairs.

    Sampling is on `derisked` (contemporaneous), not on the lag/lead
    variants -- so the same set of pairs feeds EN1/EN2/EN3.
    """
    log("\nSubsampling pairs to fit memory budget...")
    t0 = time.time()

    treated_all = deri.filter(pl.col("derisked") == 1).select("pair").unique()
    log(f"  Total treated pairs available: {treated_all.height:,}")

    if treated_all.height > MAX_TREATED_PAIRS:
        treated = treated_all.sample(n=MAX_TREATED_PAIRS, seed=42)
    else:
        treated = treated_all

    all_pairs = deri.select("pair").unique()
    control_cands = all_pairs.filter(
        ~pl.col("pair").is_in(treated["pair"].to_list())
    )
    n_control = min(MAX_CONTROL_PAIRS, control_cands.height)
    control = control_cands.sample(n=n_control, seed=42)

    log(f"  Treated kept: {treated.height:,}, control kept: {control.height:,}")
    keep = pl.concat([treated, control])["pair"].to_list()
    log(f"  Total pairs in subsample: {len(keep):,}")
    log(f"  Subsample built in {time.time()-t0:.1f}s")
    return keep


# ---------------------------------------------------------------------------
# Load subsampled panel
# ---------------------------------------------------------------------------
def load_panel(keep_pairs: list, deri: pl.DataFrame) -> pd.DataFrame:
    log("\nLoading subsampled panel slice (2018-2023)...")
    t0 = time.time()

    schema = pl.read_parquet_schema(PANEL_PATH)
    candidate_cols = [
        "trade_value", "pci_std",
        "ln_dist",
        "exporter_year", "importer_year", "pair", "hs4", "year",
        "iso3_o", "iso3_d",
        "pf_cbr",   # legacy on-disk name; renamed to fdi_proxy below
    ]
    read_cols = [c for c in candidate_cols if c in schema]

    panel = (
        pl.scan_parquet(PANEL_PATH)
        .select(read_cols)
        .filter(
            pl.col("year").is_in(POST_YEARS) &
            pl.col("pci_std").is_not_null() &
            pl.col("ln_dist").is_not_null() &
            pl.col("pair").is_in(keep_pairs)
        )
        .collect()
    )

    # Legacy -> fdi_proxy rename (mirrors rename_pf_to_fdi() in 00_config.R
    # and 12_falsification.py / 11_robustness.py).
    rename_map = {old: old.replace("pf_cbr", "fdi_proxy")
                  for old in panel.columns if old.startswith("pf_cbr")}
    if rename_map:
        panel = panel.rename(rename_map)
        log(f"  Renamed columns (legacy -> new): {rename_map}")

    # Merge derisking (current + L1 + L2 + F1)
    panel = panel.join(deri, on=["pair", "year"], how="left")
    # Contemporaneous derisked: a pair-year not in the FDI lookup is
    # assumed not de-risked. Lags/leads stay nullable -- a per-spec drop
    # excludes rows where the lag/lead is undefined (sample boundaries).
    panel = panel.with_columns(pl.col("derisked").fill_null(0))

    log(f"  Loaded: {panel.height:,} rows in {time.time()-t0:.1f}s")
    log(f"  derisked obs: {panel.filter(pl.col('derisked') == 1).height:,}")
    log(f"  derisked_L1 non-null: {panel.filter(pl.col('derisked_L1').is_not_null()).height:,}")
    log(f"  derisked_L2 non-null: {panel.filter(pl.col('derisked_L2').is_not_null()).height:,}")
    log(f"  derisked_F1 non-null: {panel.filter(pl.col('derisked_F1').is_not_null()).height:,}")

    df = panel.to_pandas()
    del panel
    gc.collect()

    for c in ["exporter_year", "importer_year", "pair", "hs4"]:
        df[c] = df[c].astype(str)
    df["derisked"] = df["derisked"].fillna(0).astype(int)
    # Lag/lead columns intentionally NOT filled -- preserve null so we can
    # drop the boundary rows per spec (otherwise we'd treat "no information"
    # as "not de-risked", which is wrong at the panel edges).

    log(f"  Pandas frame: N={len(df):,}, "
        f"derisked={(df['derisked']==1).sum():,}")

    return df


# ---------------------------------------------------------------------------
# Layer 3 availability check (CBR / n_correspondents)
# ---------------------------------------------------------------------------
def check_layer3_availability() -> bool:
    """Return True iff n_correspondents is in the on-disk schema with
    enough non-null observations to estimate Layer 3 (EN4)."""
    schema = pl.read_parquet_schema(PANEL_PATH)
    if "n_correspondents" not in schema:
        log("\nLayer 3 check: n_correspondents NOT in panel schema.")
        return False

    n_nn = (
        pl.scan_parquet(PANEL_PATH)
        .filter(pl.col("n_correspondents").is_not_null())
        .select(pl.len())
        .collect()
        .item()
    )
    log(f"\nLayer 3 check: n_correspondents non-null obs = {n_nn:,} "
        f"(threshold = {LAYER3_MIN_OBS:,})")
    return n_nn >= LAYER3_MIN_OBS


# ---------------------------------------------------------------------------
# Build CBR-derived derisked indicator (Layer 3 only)
# ---------------------------------------------------------------------------
def build_cbr_lookup() -> pl.DataFrame:
    """Per (iso3_o, iso3_d, year) compute pct_change in n_correspondents
    over a 2-year window; flag pairs with > 50% drop as derisked_cbr.

    Mirrors the R script's logic in scripts/R/08_endogeneity.R lines 87-95.
    """
    log("Building CBR derisking lookup...")
    cbr = (
        pl.scan_parquet(PANEL_PATH)
        .select(["iso3_o", "iso3_d", "year", "n_correspondents"])
        .filter(pl.col("n_correspondents").is_not_null())
        .unique(subset=["iso3_o", "iso3_d", "year"])
        .collect()
        .sort(["iso3_o", "iso3_d", "year"])
    )
    log(f"  CBR (iso_o, iso_d, year) rows: {cbr.height:,}")

    # 2-year lag join: align (iso_o, iso_d, year) with its (year-2) row.
    cbr_l2 = cbr.select([
        pl.col("iso3_o"),
        pl.col("iso3_d"),
        (pl.col("year") + 2).alias("year"),
        pl.col("n_correspondents").alias("n_corr_L2"),
    ])
    cbr = cbr.join(cbr_l2, on=["iso3_o", "iso3_d", "year"], how="left")
    cbr = cbr.with_columns([
        ((pl.col("n_correspondents") - pl.col("n_corr_L2")) /
         (pl.col("n_corr_L2") + 1)).alias("pct_change"),
    ])
    cbr = cbr.with_columns([
        (pl.col("pct_change").is_not_null() & (pl.col("pct_change") < -0.5))
        .cast(pl.Int8).fill_null(0).alias("derisked_cbr"),
    ])
    n_dr = cbr.filter(pl.col("derisked_cbr") == 1).height
    log(f"  CBR-derisked corridor-years: {n_dr:,}")

    return cbr.select(["iso3_o", "iso3_d", "year", "derisked_cbr"])


# ---------------------------------------------------------------------------
# LaTeX table writer (booktabs, no in-table title or notes)
# ---------------------------------------------------------------------------
def write_latex_table(results: list, path: str) -> None:
    """Bare-tabular booktabs LaTeX:
       columns = EN1, EN2, EN3, (EN4 if available)
       rows    = headline interaction (with SE row), level (with SE row),
                 N, FE block.
    """
    def fmt_coef(coef, pval):
        if pd.isna(coef):
            return "--"
        stars = ""
        if not pd.isna(pval):
            if pval < 0.01:
                stars = r"$^{***}$"
            elif pval < 0.05:
                stars = r"$^{**}$"
            elif pval < 0.10:
                stars = r"$^{*}$"
        return f"{coef:.4f}{stars}"

    def fmt_se(se):
        return "--" if pd.isna(se) else f"({se:.4f})"

    def fmt_n(n):
        return "--" if pd.isna(n) else f"{int(n):,}"

    n_specs = len(results)
    col_spec = "l" + "c" * n_specs

    # Column header: ENk
    col_ids = [f"({i+1})" for i in range(n_specs)]
    col_lbls = [r["short"] for r in results]

    lines = []
    lines.append(r"\begin{tabular}{" + col_spec + "}")
    lines.append(r"\toprule")
    lines.append(" & " + " & ".join(col_ids) + r" \\")
    lines.append(" & " + " & ".join(col_lbls) + r" \\")
    lines.append(r"\midrule")

    # Interaction row (headline)
    lines.append(
        r"Treatment $\times$ PCI & "
        + " & ".join(fmt_coef(r["coef"], r["pvalue"]) for r in results)
        + r" \\"
    )
    lines.append(
        r" & "
        + " & ".join(fmt_se(r["se"]) for r in results)
        + r" \\"
    )

    # Level row
    lines.append(
        r"Treatment & "
        + " & ".join(fmt_coef(r["level_coef"], r["level_pvalue"]) for r in results)
        + r" \\"
    )
    lines.append(
        r" & "
        + " & ".join(fmt_se(r["level_se"]) for r in results)
        + r" \\"
    )

    lines.append(r"\midrule")

    # FE / N block
    lines.append(
        r"Observations & "
        + " & ".join(fmt_n(r["n_obs"]) for r in results)
        + r" \\"
    )
    lines.append(
        r"Exporter-year FE & "
        + " & ".join(["Yes"] * n_specs)
        + r" \\"
    )
    lines.append(
        r"Importer-year FE & "
        + " & ".join(["Yes"] * n_specs)
        + r" \\"
    )
    lines.append(
        r"Pair FE & "
        + " & ".join(["Yes"] * n_specs)
        + r" \\"
    )
    lines.append(
        r"Product (HS4) FE & "
        + " & ".join(["Yes"] * n_specs)
        + r" \\"
    )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Verdict relative to F0 baseline
# ---------------------------------------------------------------------------
def verdict_vs_baseline(coef: float, pvalue: float,
                        baseline: float = F0_BASELINE_COEF) -> str:
    """Compare a coefficient to F0_BASELINE_COEF (= -0.198).
       'survives' : same sign, |coef| >= 0.5 * |baseline|, p < 0.10
       'weaker'   : same sign but smaller magnitude OR p >= 0.10
       'null'     : opposite sign or |coef| < 0.2 * |baseline|
    """
    if pd.isna(coef):
        return "did not converge"
    if np.sign(coef) != np.sign(baseline):
        return "WRONG SIGN (likely null)"
    ratio = abs(coef) / abs(baseline) if baseline != 0 else np.inf
    sig   = (not pd.isna(pvalue)) and (pvalue < 0.10)
    if ratio >= 0.5 and sig:
        return "survives"
    if ratio < 0.2:
        return "null (much smaller than baseline)"
    return "weaker than baseline"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log("=" * 60)
    log("08_endogeneity.py -- causal-robustness layers (lags + lead + CBR)")
    log("=" * 60)
    log(f"  F0 baseline reference (12_falsification.py): {F0_BASELINE_COEF:.4f}")

    # ---- Build derisking lookups, subsample, load panel ----
    deri = build_derisking_lookup()
    keep_pairs = subsample_pairs(deri)
    df = load_panel(keep_pairs, deri)

    FE = "exporter_year + importer_year + pair + hs4"
    pair_vcov = {"CRV1": "pair"}

    results = []

    # =====================================================================
    # Layer 1 -- EN1: Lag-1 PPML
    # =====================================================================
    log("\n" + "-" * 60)
    log("Layer 1 -- Lagged de-risking (causal-channel evidence)")
    log("-" * 60)

    log("\n>>> EN1: Lag-1 derisked")
    sub = df[df["derisked_L1"].notna()].copy()
    sub["derisked_L1"] = sub["derisked_L1"].astype(int)
    log(f"  After dropping null L1 rows: N={len(sub):,} "
        f"(L1=1 obs: {(sub['derisked_L1']==1).sum():,})")
    f_en1 = f"trade_value ~ derisked_L1 + derisked_L1:pci_std | {FE}"
    r = run_spec("EN1: Lag-1", f_en1, sub, "derisked_L1", pair_vcov)
    r["short"]  = "Lag-1"
    r["layer"]  = 1
    results.append(r)

    # =====================================================================
    # EN2: Lag-2 PPML
    # =====================================================================
    log("\n>>> EN2: Lag-2 derisked")
    sub = df[df["derisked_L2"].notna()].copy()
    sub["derisked_L2"] = sub["derisked_L2"].astype(int)
    log(f"  After dropping null L2 rows: N={len(sub):,} "
        f"(L2=1 obs: {(sub['derisked_L2']==1).sum():,})")
    f_en2 = f"trade_value ~ derisked_L2 + derisked_L2:pci_std | {FE}"
    r = run_spec("EN2: Lag-2", f_en2, sub, "derisked_L2", pair_vcov)
    r["short"]  = "Lag-2"
    r["layer"]  = 1
    results.append(r)

    # =====================================================================
    # Layer 2 -- EN3: Lead-1 PPML (placebo / pre-trends)
    # =====================================================================
    log("\n" + "-" * 60)
    log("Layer 2 -- Lead test (placebo / pre-trends)")
    log("-" * 60)

    log("\n>>> EN3: Lead-1 derisked (should be NULL)")
    sub = df[df["derisked_F1"].notna()].copy()
    sub["derisked_F1"] = sub["derisked_F1"].astype(int)
    log(f"  After dropping null F1 rows: N={len(sub):,} "
        f"(F1=1 obs: {(sub['derisked_F1']==1).sum():,})")
    f_en3 = f"trade_value ~ derisked_F1 + derisked_F1:pci_std | {FE}"
    r = run_spec("EN3: Lead-1", f_en3, sub, "derisked_F1", pair_vcov)
    r["short"]  = "Lead-1"
    r["layer"]  = 2
    results.append(r)

    # =====================================================================
    # Layer 3 -- EN4: CBR-derisked x PCI (skip if data missing)
    # =====================================================================
    log("\n" + "-" * 60)
    log("Layer 3 -- CBR-derived de-risking reduced form")
    log("-" * 60)

    if check_layer3_availability():
        log("\n>>> EN4: CBR-derisked")
        cbr_lookup = build_cbr_lookup()
        # Need to load iso3_o / iso3_d into the panel to merge CBR
        if "iso3_o" in df.columns and "iso3_d" in df.columns:
            cbr_pd = cbr_lookup.to_pandas()
            sub = df.merge(cbr_pd, on=["iso3_o", "iso3_d", "year"], how="left")
            sub["derisked_cbr"] = sub["derisked_cbr"].fillna(0).astype(int)
            log(f"  Merged CBR onto panel: N={len(sub):,}, "
                f"CBR-derisked obs: {(sub['derisked_cbr']==1).sum():,}")
            f_en4 = f"trade_value ~ derisked_cbr + derisked_cbr:pci_std | {FE}"
            r = run_spec("EN4: CBR-derisked", f_en4, sub, "derisked_cbr",
                         pair_vcov)
            r["short"]  = "CBR-derisked"
            r["layer"]  = 3
            results.append(r)
        else:
            log("  iso3_o / iso3_d missing from panel; cannot merge CBR. "
                "Skipping EN4.")
    else:
        log("\nLayer 3 SKIPPED: n_correspondents not populated; "
            "FDI-derived `derisked` indicator already serves the "
            "de-risking-shock role in the headline.")

    # =====================================================================
    # Save results
    # =====================================================================
    log("\n" + "=" * 60)
    log("SAVING RESULTS")
    log("=" * 60)

    pkl_path = os.path.join(DIR_CLEAN, "estimates_endogeneity.pkl")
    with open(pkl_path, "wb") as fh:
        pickle.dump(results, fh)
    log(f"  Saved: {pkl_path}")

    csv_cols = [
        "label", "short", "layer", "treat_var",
        "interaction_name", "coef", "se", "pvalue", "ci_lo", "ci_hi",
        "level_name", "level_coef", "level_se", "level_pvalue",
        "n_obs", "converged", "time_s", "error", "formula",
    ]
    csv_df = pd.DataFrame(results)
    for c in csv_cols:
        if c not in csv_df.columns:
            csv_df[c] = np.nan
    csv_df = csv_df[csv_cols]
    csv_path = os.path.join(TABLE_DIR, "endogeneity_panel.csv")
    csv_df.to_csv(csv_path, index=False)
    log(f"  Saved: {csv_path}")

    tex_path = os.path.join(TABLE_DIR, "endogeneity_panel.tex")
    write_latex_table(results, tex_path)
    log(f"  Saved: {tex_path}")

    # =====================================================================
    # Summary
    # =====================================================================
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"F0 baseline reference (contemporaneous derisked x PCI): "
        f"{F0_BASELINE_COEF:.4f}")
    log("")
    for r in results:
        if not r["converged"] or pd.isna(r["coef"]):
            log(f"  {r['label']}: did not converge or no interaction term")
            continue
        v = verdict_vs_baseline(r["coef"], r["pvalue"])
        log(f"  {r['label']:18s}: coef={r['coef']:+.4f} "
            f"(SE {r['se']:.4f}, p={r['pvalue']:.4f}) -> {v}")

    # Layer-specific narrative
    log("")
    en1 = next((r for r in results if r["label"].startswith("EN1")), None)
    en2 = next((r for r in results if r["label"].startswith("EN2")), None)
    en3 = next((r for r in results if r["label"].startswith("EN3")), None)

    if en1 and en1["converged"] and not pd.isna(en1["coef"]):
        sign1 = "negative" if en1["coef"] < 0 else "positive"
        sig1  = "significant" if (not pd.isna(en1["pvalue"]) and en1["pvalue"] < 0.10) else "not significant"
        log(f"Lag-1 (EN1): {sign1}, {sig1} -- "
            f"{'consistent with causal channel' if (en1['coef'] < 0 and sig1 == 'significant') else 'weak / no causal-channel evidence'}")

    if en2 and en2["converged"] and not pd.isna(en2["coef"]):
        sign2 = "negative" if en2["coef"] < 0 else "positive"
        sig2  = "significant" if (not pd.isna(en2["pvalue"]) and en2["pvalue"] < 0.10) else "not significant"
        log(f"Lag-2 (EN2): {sign2}, {sig2}")

    if en3 and en3["converged"] and not pd.isna(en3["coef"]):
        sig3 = (not pd.isna(en3["pvalue"]) and en3["pvalue"] < 0.10)
        if sig3:
            # If the lead is itself negative AND large, that's a pre-trend warning
            if abs(en3["coef"]) > 0.5 * abs(F0_BASELINE_COEF):
                log(f"Lead-1 (EN3): SIGNIFICANT and large (|coef|={abs(en3['coef']):.4f}) -- "
                    f"WARNING: possible anticipation / pre-trends in de-risked corridors")
            else:
                log(f"Lead-1 (EN3): significant but small relative to baseline -- minor pre-trends concern")
        else:
            log(f"Lead-1 (EN3): not significant (p={en3['pvalue']:.4f}) -- "
                f"PASS, no detectable anticipation effect")

    log("\nDone.")


if __name__ == "__main__":
    main()
