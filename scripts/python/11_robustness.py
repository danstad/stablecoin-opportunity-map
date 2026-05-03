"""
11_robustness.py — Specification curve / robustness battery

Re-estimates the headline FDI-derisking x PCI specification under multiple
variations to produce a coefficient-stability / specification curve plot.
Each variant tests whether the headline result depends on a particular
sample, FE structure, lag, friction measure, or estimator.

Mirrors scripts/python/12_falsification.py and 16_confounder_estimation.py:
  - Polars lazy reads, pandas conversion for pyfixest
  - 2000 treated + 1000 control pair subsample
  - pyfixest fepois (PPML) for most specs; feols for OLS-on-log spec
  - Pair-clustered SEs (exporter-clustered for the no-pair-FE spec)
  - Bare-tabular booktabs LaTeX output (no in-table notes)

Headline reference: gamma_FDI = -0.135 (PB Panel Baseline in
confounder_panel.csv); gamma_FDI = -0.198 in 4-FE subsample baseline (F0).

Specifications (10 specs):
  R0:  Baseline (full subsample, 4-FE, PPML)                  derisked  + derisked:pci_std
  R1:  Lag-1 derisked                                         derisked_L1 + derisked_L1:pci_std
  R2:  Lag-2 derisked                                         derisked_L2 + derisked_L2:pci_std
  R3:  RPW friction only                                      pf_rpw   + pf_rpw:pci_std
  R5:  Excl. entrepots (SGP, HKG, ARE, NLD, LUX, BEL, CHE)
  R6:  Excl. China
  R7:  Excl. commodities (HS01-27)
  R8:  Pre-COVID (year <= 2019)
  R9:  No pair FEs (cross-sectional)
  R10: OLS on log(1 + trade_value)

Inputs:  data/cleaned/panel_main_confounders.parquet
Outputs: data/cleaned/estimates_robustness.pkl
         paper/tables/11_robustness/robustness_specification_curve.csv
         paper/tables/11_robustness/robustness_specification_curve.tex
         paper/figures/11_robustness/specification_curve.pdf
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Shared figure style (serif, larger fonts) from _figure_style.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _figure_style import apply_style  # noqa: E402

apply_style()

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
PROJECT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_CLEAN = os.path.join(PROJECT, "data", "cleaned")
TABLE_DIR = os.path.join(PROJECT, "paper", "tables", "11_robustness")
FIG_DIR   = os.path.join(PROJECT, "paper", "figures", "11_robustness")
os.makedirs(TABLE_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

PANEL_PATH  = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")
BASE_PERIOD = [2015, 2016, 2017]
POST_YEARS  = [2018, 2019, 2020, 2021, 2022, 2023]

# Subsample sizes (mirror 12_falsification.py / 16_confounder_estimation.py).
MAX_TREATED_PAIRS = 2000
MAX_CONTROL_PAIRS = 1000

ENTREPOTS = ["SGP", "HKG", "ARE", "NLD", "LUX", "BEL", "CHE"]

np.random.seed(20260502)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_interaction(coef_index, treat_var: str, mod_var: str = "pci_std"):
    """Return the first interaction term name involving treat_var x mod_var."""
    for name in coef_index:
        if ":" not in name:
            continue
        if treat_var in name and mod_var in name:
            return name
    return None


def run_spec(label: str, formula: str, data: pd.DataFrame, treat_var: str,
             vcov, estimator: str = "fepois") -> dict:
    """Estimate a single spec; extract treat_var x pci_std interaction."""
    t0 = time.time()
    out = {
        "label": label,
        "formula": formula,
        "treat_var": treat_var,
        "estimator": estimator,
        "converged": False,
        "n_obs": np.nan,
        "coef": np.nan,
        "se": np.nan,
        "pvalue": np.nan,
        "ci_lo": np.nan,
        "ci_hi": np.nan,
        "interaction_name": "",
        "time_s": np.nan,
        "error": "",
    }
    try:
        if estimator == "fepois":
            m = pf.fepois(formula, data=data, vcov=vcov)
        elif estimator == "feols":
            m = pf.feols(formula, data=data, vcov=vcov)
        else:
            raise ValueError(f"Unknown estimator: {estimator}")

        coefs, ses, pvals = m.coef(), m.se(), m.pvalue()
        elapsed = time.time() - t0

        iname = find_interaction(coefs.index, treat_var, "pci_std")
        out["converged"] = True
        out["n_obs"] = int(m._N)
        out["time_s"] = elapsed

        if iname is not None:
            coef = float(coefs[iname])
            se   = float(ses[iname])
            out["interaction_name"] = iname
            out["coef"]    = coef
            out["se"]      = se
            out["pvalue"]  = float(pvals[iname])
            out["ci_lo"]   = coef - 1.96 * se
            out["ci_hi"]   = coef + 1.96 * se
            stars = ""
            p = out["pvalue"]
            if not np.isnan(p):
                if p < 0.01:
                    stars = "***"
                elif p < 0.05:
                    stars = "**"
                elif p < 0.10:
                    stars = "*"
            log(f"  {label}: {iname}={coef:.4f} (SE {se:.4f}, p={p:.4f}){stars} "
                f"| N={out['n_obs']:,} [{elapsed:.0f}s]")
        else:
            log(f"  {label}: WARNING no {treat_var}:pci_std interaction in coefs "
                f"| N={out['n_obs']:,} [{elapsed:.0f}s]")
    except Exception as e:
        out["error"] = str(e)
        log(f"  {label}: FAILED -- {e}")
    return out


# ---------------------------------------------------------------------------
# Build derisking lookup, including 1- and 2-year lags
# ---------------------------------------------------------------------------
def build_derisking_lookup() -> pl.DataFrame:
    """Construct (pair, year) derisked indicator and its 1/2-year lags.

    derisked_t = 1 iff fdi_bilateral_t / mean(fdi_bilateral, 2015-2017) < 0.5.
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

    # Construct lag-1 and lag-2 indicators by self-join on (pair, year-k)
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
    deri = deri.join(lag1, on=["pair", "year"], how="left")
    deri = deri.join(lag2, on=["pair", "year"], how="left")

    log(f"  Derisking lookup: {deri.height:,} rows "
        f"({deri.filter(pl.col('derisked') == 1).height:,} derisked, "
        f"{deri.filter(pl.col('derisked_L1') == 1).height:,} L1, "
        f"{deri.filter(pl.col('derisked_L2') == 1).height:,} L2)")

    log(f"  Done in {time.time()-t0:.1f}s")
    return deri


# ---------------------------------------------------------------------------
# Subsample pairs (mirror 16_confounder_estimation.py PART 2)
# ---------------------------------------------------------------------------
def subsample_pairs(deri: pl.DataFrame) -> list:
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
    log("\nLoading subsampled panel slice...")
    t0 = time.time()

    schema = pl.read_parquet_schema(PANEL_PATH)
    candidate_cols = [
        "trade_value", "pci_std",
        "ln_dist", "contig", "comlang_off", "colony",
        "exporter_year", "importer_year", "pair", "hs4", "year",
        "iso3_o", "iso3_d",
        "pf_cbr",   # legacy on-disk name; renamed to fdi_proxy below
        "pf_rpw",
    ]
    read_cols = [c for c in candidate_cols if c in schema]

    panel = (
        pl.scan_parquet(PANEL_PATH)
        .select(read_cols)
        .filter(
            pl.col("year").is_in(POST_YEARS) &
            pl.col("pci_std").is_not_null() &
            pl.col("pair").is_in(keep_pairs)
        )
        .collect()
    )

    # Legacy -> fdi_proxy rename (mirrors rename_pf_to_fdi in 00_config.R).
    rename_map = {old: old.replace("pf_cbr", "fdi_proxy")
                  for old in panel.columns if old.startswith("pf_cbr")}
    if rename_map:
        panel = panel.rename(rename_map)
        log(f"  Renamed columns: {rename_map}")

    # Merge derisking (current + L1 + L2)
    panel = panel.join(deri, on=["pair", "year"], how="left")
    for col in ["derisked", "derisked_L1", "derisked_L2"]:
        if col in panel.columns:
            panel = panel.with_columns(pl.col(col).fill_null(0))

    log(f"  Loaded: {panel.height:,} rows in {time.time()-t0:.1f}s")
    log(f"  derisked obs: {panel.filter(pl.col('derisked') == 1).height:,}")

    df = panel.to_pandas()
    del panel
    gc.collect()

    for c in ["exporter_year", "importer_year", "pair", "hs4"]:
        df[c] = df[c].astype(str)
    for c in ["derisked", "derisked_L1", "derisked_L2"]:
        if c in df.columns:
            df[c] = df[c].fillna(0).astype(int)

    log(f"  Pandas frame: N={len(df):,}, "
        f"derisked={(df['derisked']==1).sum():,}, "
        f"L1={(df['derisked_L1']==1).sum():,}, "
        f"L2={(df['derisked_L2']==1).sum():,}, "
        f"pf_rpw non-null={df['pf_rpw'].notna().sum():,}"
        if "pf_rpw" in df.columns
        else f"  Pandas frame: N={len(df):,}, "
             f"derisked={(df['derisked']==1).sum():,}")

    return df


# ---------------------------------------------------------------------------
# LaTeX export
# ---------------------------------------------------------------------------
def write_latex_table(results: list, path: str) -> None:
    """Bare-tabular booktabs LaTeX, no in-table notes."""
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

    lines = []
    lines.append(r"\begin{tabular}{llccccc}")
    lines.append(r"\toprule")
    lines.append(r"ID & Specification & Coefficient & Std. Error & "
                 r"95\% CI Low & 95\% CI High & N \\")
    lines.append(r"\midrule")
    for r in results:
        # Split label at first ":" if present, e.g. "R0: Baseline"
        if ":" in r["label"]:
            ident, descr = r["label"].split(":", 1)
            ident, descr = ident.strip(), descr.strip()
        else:
            ident, descr = r["label"], ""
        # Escape any underscores or special chars; convert <= / >= to math.
        descr = (descr
                 .replace("&", r"\&")
                 .replace("_", r"\_")
                 .replace("<=", r"$\leq$")
                 .replace(">=", r"$\geq$"))
        coef_cell = fmt_coef(r["coef"], r["pvalue"])
        se_cell   = fmt_se(r["se"])
        clo       = "--" if pd.isna(r["ci_lo"]) else f"{r['ci_lo']:.4f}"
        chi       = "--" if pd.isna(r["ci_hi"]) else f"{r['ci_hi']:.4f}"
        n_cell    = fmt_n(r["n_obs"])
        lines.append(f"{ident} & {descr} & {coef_cell} & {se_cell} & "
                     f"{clo} & {chi} & {n_cell} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Specification curve plot
# ---------------------------------------------------------------------------
def plot_specification_curve(results: list, baseline_coef: float, path: str) -> None:
    """Coefficient + 95% CI per spec, sorted by point estimate.

    Per content-standards.md: serif font, no in-figure title.
    """
    plot_data = [r for r in results
                 if r["converged"] and not pd.isna(r["coef"])]
    if not plot_data:
        log("  Specification curve: no converged specs to plot")
        return

    plot_data = sorted(plot_data, key=lambda r: r["coef"])
    labels = [r["label"] for r in plot_data]
    coefs  = np.array([r["coef"]  for r in plot_data])
    ci_lo  = np.array([r["ci_lo"] for r in plot_data])
    ci_hi  = np.array([r["ci_hi"] for r in plot_data])

    err_lo = coefs - ci_lo
    err_hi = ci_hi - coefs

    fig, ax = plt.subplots(figsize=(10, max(6, 0.55 * len(plot_data) + 1.5)))
    y_pos = np.arange(len(plot_data))
    ax.errorbar(coefs, y_pos,
                xerr=[err_lo, err_hi],
                fmt="o", color="steelblue", ecolor="gray",
                elinewidth=1.5, capsize=4, markersize=9)

    # Reference lines
    ax.axvline(x=0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    if not pd.isna(baseline_coef):
        ax.axvline(x=baseline_coef, color="firebrick",
                   linestyle="--", linewidth=1.0, alpha=0.7,
                   label=f"R0 baseline ({baseline_coef:.3f})")
        ax.legend(loc="best", frameon=False)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Treatment x PCI coefficient (95% CI)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    log(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log("=" * 60)
    log("11_robustness.py -- specification curve / robustness battery")
    log("=" * 60)

    # --replot: skip estimation; reuse cached pickle to redraw the figure
    # at the new larger-font style. Useful when only style has changed.
    if "--replot" in sys.argv:
        pkl_path = os.path.join(DIR_CLEAN, "estimates_robustness.pkl")
        log(f"REPLOT MODE -- loading {pkl_path}")
        with open(pkl_path, "rb") as fh:
            results = pickle.load(fh)
        baseline = next((r for r in results if r["label"].startswith("R0")), None)
        baseline_coef = baseline["coef"] if baseline and not pd.isna(baseline["coef"]) else float("nan")
        pdf_path = os.path.join(FIG_DIR, "specification_curve.pdf")
        plot_specification_curve(results, baseline_coef, pdf_path)
        log("Replot done.")
        return

    deri = build_derisking_lookup()
    keep_pairs = subsample_pairs(deri)
    df = load_panel(keep_pairs, deri)

    FE_FULL = "exporter_year + importer_year + pair + hs4"
    FE_NOPA = "exporter_year + importer_year + hs4"

    pair_vcov     = {"CRV1": "pair"}
    exporter_vcov = {"CRV1": "exporter_year"}

    results = []

    # ------------------------------ R0 ------------------------------
    log("\n>>> R0: Baseline")
    sub = df[df["pci_std"].notna()]
    f0 = f"trade_value ~ derisked + derisked:pci_std | {FE_FULL}"
    results.append(run_spec("R0: Baseline", f0, sub, "derisked",
                            pair_vcov, "fepois"))

    # ------------------------------ R1 ------------------------------
    log("\n>>> R1: Lag-1 derisked")
    sub = df[df["pci_std"].notna()]
    f1 = f"trade_value ~ derisked_L1 + derisked_L1:pci_std | {FE_FULL}"
    results.append(run_spec("R1: Lag-1 derisked", f1, sub, "derisked_L1",
                            pair_vcov, "fepois"))

    # ------------------------------ R2 ------------------------------
    log("\n>>> R2: Lag-2 derisked")
    sub = df[df["pci_std"].notna()]
    f2 = f"trade_value ~ derisked_L2 + derisked_L2:pci_std | {FE_FULL}"
    results.append(run_spec("R2: Lag-2 derisked", f2, sub, "derisked_L2",
                            pair_vcov, "fepois"))

    # ------------------------------ R3 ------------------------------
    log("\n>>> R3: RPW friction only")
    if "pf_rpw" in df.columns and df["pf_rpw"].notna().sum() > 1000:
        sub = df[df["pci_std"].notna() & df["pf_rpw"].notna()]
        f3 = f"trade_value ~ pf_rpw + pf_rpw:pci_std | {FE_FULL}"
        results.append(run_spec("R3: RPW friction only", f3, sub, "pf_rpw",
                                pair_vcov, "fepois"))
    else:
        log("  R3: SKIPPED (pf_rpw missing or too sparse)")
        results.append({
            "label": "R3: RPW friction only",
            "formula": "skipped", "treat_var": "pf_rpw",
            "estimator": "fepois", "converged": False,
            "n_obs": np.nan, "coef": np.nan, "se": np.nan,
            "pvalue": np.nan, "ci_lo": np.nan, "ci_hi": np.nan,
            "interaction_name": "", "time_s": np.nan,
            "error": "pf_rpw missing or too sparse",
        })

    # ------------------------------ R5 ------------------------------
    log("\n>>> R5: Excl. entrepots")
    sub = df[
        df["pci_std"].notna() &
        ~df["iso3_o"].isin(ENTREPOTS) &
        ~df["iso3_d"].isin(ENTREPOTS)
    ]
    log(f"  After dropping entrepots: N={len(sub):,}")
    results.append(run_spec("R5: Excl. entrepots", f0, sub, "derisked",
                            pair_vcov, "fepois"))

    # ------------------------------ R6 ------------------------------
    log("\n>>> R6: Excl. China")
    sub = df[
        df["pci_std"].notna() &
        (df["iso3_o"] != "CHN") & (df["iso3_d"] != "CHN")
    ]
    log(f"  After dropping CHN: N={len(sub):,}")
    results.append(run_spec("R6: Excl. China", f0, sub, "derisked",
                            pair_vcov, "fepois"))

    # ------------------------------ R7 ------------------------------
    log("\n>>> R7: Excl. commodities (HS01-27)")
    # hs4 is a 4-digit string; first two chars are the HS chapter
    hs_chapter = pd.to_numeric(df["hs4"].str[:2], errors="coerce")
    sub = df[df["pci_std"].notna() & (hs_chapter > 27)]
    log(f"  After dropping HS01-27: N={len(sub):,}")
    results.append(run_spec("R7: Excl. commodities (HS01-27)", f0, sub,
                            "derisked", pair_vcov, "fepois"))

    # ------------------------------ R8 ------------------------------
    log("\n>>> R8: Pre-COVID (year <= 2019)")
    sub = df[df["pci_std"].notna() & (df["year"] <= 2019)]
    log(f"  Pre-COVID rows: N={len(sub):,}")
    results.append(run_spec("R8: Pre-COVID (year <= 2019)", f0, sub,
                            "derisked", pair_vcov, "fepois"))

    # ------------------------------ R9 ------------------------------
    log("\n>>> R9: No pair FEs")
    sub = df[df["pci_std"].notna()]
    f9 = f"trade_value ~ derisked + derisked:pci_std | {FE_NOPA}"
    results.append(run_spec("R9: No pair FEs", f9, sub, "derisked",
                            exporter_vcov, "fepois"))

    # ------------------------------ R10 -----------------------------
    log("\n>>> R10: OLS on log(1+trade)")
    sub = df[df["pci_std"].notna()].copy()
    sub["ln_trade"] = np.log1p(sub["trade_value"].astype(float))
    f10 = f"ln_trade ~ derisked + derisked:pci_std | {FE_FULL}"
    results.append(run_spec("R10: OLS log(1+trade)", f10, sub, "derisked",
                            pair_vcov, "feols"))

    # =====================================================================
    # Save results
    # =====================================================================
    log("\n" + "=" * 60)
    log("SAVING RESULTS")
    log("=" * 60)

    pkl_path = os.path.join(DIR_CLEAN, "estimates_robustness.pkl")
    with open(pkl_path, "wb") as fh:
        pickle.dump(results, fh)
    log(f"  Saved: {pkl_path}")

    csv_cols = ["label", "coef", "se", "pvalue", "ci_lo", "ci_hi",
                "n_obs", "converged", "interaction_name",
                "estimator", "treat_var", "time_s", "error", "formula"]
    csv_df = pd.DataFrame(results)
    for c in csv_cols:
        if c not in csv_df.columns:
            csv_df[c] = np.nan
    csv_df = csv_df[csv_cols]
    csv_path = os.path.join(TABLE_DIR, "robustness_specification_curve.csv")
    csv_df.to_csv(csv_path, index=False)
    log(f"  Saved: {csv_path}")

    tex_path = os.path.join(TABLE_DIR, "robustness_specification_curve.tex")
    write_latex_table(results, tex_path)
    log(f"  Saved: {tex_path}")

    # Specification curve figure
    baseline = next((r for r in results if r["label"].startswith("R0")), None)
    baseline_coef = baseline["coef"] if baseline and not pd.isna(baseline["coef"]) else float("nan")
    pdf_path = os.path.join(FIG_DIR, "specification_curve.pdf")
    plot_specification_curve(results, baseline_coef, pdf_path)

    # =====================================================================
    # Summary
    # =====================================================================
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)

    n_total = len(results)
    converged = [r for r in results if r["converged"] and not pd.isna(r["coef"])]
    n_conv = len(converged)
    log(f"Specs run: {n_total}")
    log(f"Specs converged with non-missing coef: {n_conv}")

    if n_conv > 0:
        coefs = np.array([r["coef"] for r in converged])
        log(f"Coefficient range: [{coefs.min():.4f}, {coefs.max():.4f}]")
        log(f"Mean: {coefs.mean():.4f}, Median: {np.median(coefs):.4f}")

        # Sign survival relative to baseline
        if not pd.isna(baseline_coef):
            same_sign = sum(1 for r in converged
                            if np.sign(r["coef"]) == np.sign(baseline_coef))
            log(f"Sign of R0 baseline ({baseline_coef:.4f}) survived in "
                f"{same_sign}/{n_conv} = {100*same_sign/n_conv:.1f}% of specs")

        # Survival at p<0.10
        sig = sum(1 for r in converged
                  if not pd.isna(r["pvalue"]) and r["pvalue"] < 0.10)
        log(f"Significance at p<0.10: {sig}/{n_conv} = "
            f"{100*sig/n_conv:.1f}%")

        # Specs deviating from baseline by > 0.05 in absolute terms
        if not pd.isna(baseline_coef):
            big_dev = [r for r in converged
                       if abs(r["coef"] - baseline_coef) > 0.05]
            if big_dev:
                log(f"\nSpecs deviating from baseline by > 0.05 (n={len(big_dev)}):")
                for r in big_dev:
                    log(f"  {r['label']}: coef={r['coef']:.4f}, "
                        f"delta={r['coef']-baseline_coef:+.4f}")
            else:
                log("No spec deviates from baseline by > 0.05.")

    log("\nDone.")


if __name__ == "__main__":
    main()
