"""
12_falsification.py — Payment-channel specificity falsification tests

Strategy: confirm that the FDI-derisking × PCI penalty operates through a
*payment-specific* channel by adding placebo-friction × PCI interactions to
the headline specification. The headline coefficient (derisked × pci_std)
should survive; the falsification interactions should be null or wrong-signed.

The on-disk panel keeps the legacy column name `pf_cbr` for backward
compatibility; substantively this is an FDI-derived proxy. We rename it to
`fdi_proxy` immediately on load (see rename_pf_to_fdi()/00_config.R for the
R counterpart and the §03 footnote in paper/sections/03_data.tex).

Specifications (PPML, full panel 2018-2023, pair-level clustering):
  F0: derisked × pci_std                                  (baseline; replicates B0)
  F1: derisked × pci_std + ln_dist × pci_std              (placebo: distance)
  F2: derisked × pci_std + comlang_off × pci_std          (placebo: language)
  F3: derisked × pci_std + contig × pci_std               (placebo: contiguity)
  F4: derisked × pci_std + colony × pci_std               (placebo: colony)
  F5: derisked × pci_std + rta_coverage × pci_std         (placebo: RTA)

Fixed effects: exporter_year + importer_year + pair + hs4
  (Exporter × year and importer × year absorb multilateral resistance;
  pair absorbs corridor-invariant frictions; hs4 absorbs product effects.)

Mirrors the structure of scripts/python/16_confounder_estimation.py.

Inputs:  data/cleaned/panel_main_confounders.parquet
Outputs: data/cleaned/estimates_falsification.pkl
         paper/tables/12_falsification/falsification_panel.csv
         paper/tables/12_falsification/falsification_panel.tex
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
TABLE_DIR = os.path.join(PROJECT, "paper", "tables", "12_falsification")
os.makedirs(TABLE_DIR, exist_ok=True)

PANEL_PATH  = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")
BASE_PERIOD = [2015, 2016, 2017]
POST_YEARS  = [2018, 2019, 2020, 2021, 2022, 2023]

# Subsample sizes (mirror scripts/python/16_confounder_estimation.py PART 2).
# Full ~6M-row panel makes 6 PPMLs intractable on 16 GB RAM; the headline
# γ_FDI = -0.135 cited in the paper is itself a subsample estimate.
MAX_TREATED_PAIRS = 2000
MAX_CONTROL_PAIRS = 1000

np.random.seed(20260502)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_spec(formula: str, data: pd.DataFrame, vcov, spec_name: str) -> dict:
    """Run a single PPML spec; return scalar coefficients we need.

    We extract:
      - the headline interaction `derisked:pci_std`
      - the placebo interaction (any other `:pci_std` term)
    """
    t0 = time.time()
    out = {
        "spec": spec_name,
        "formula": formula,
        "converged": False,
        "n_obs": np.nan,
        "headline_coef": np.nan,
        "headline_se": np.nan,
        "headline_pvalue": np.nan,
        "placebo_term": "",
        "placebo_coef": np.nan,
        "placebo_se": np.nan,
        "placebo_pvalue": np.nan,
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

        # Headline: derisked:pci_std (or pci_std:derisked — pyfixest may flip order)
        for name in coefs.index:
            if ":" in name and "derisked" in name and "pci_std" in name:
                out["headline_coef"]   = float(coefs[name])
                out["headline_se"]     = float(ses[name])
                out["headline_pvalue"] = float(pvals[name])
                break

        # Placebo: any other `:pci_std` interaction term that isn't the headline
        for name in coefs.index:
            if ":" not in name:
                continue
            if "pci_std" not in name:
                continue
            if "derisked" in name:
                continue
            out["placebo_term"]    = name
            out["placebo_coef"]    = float(coefs[name])
            out["placebo_se"]      = float(ses[name])
            out["placebo_pvalue"]  = float(pvals[name])
            break

        head_str = (
            f"head={out['headline_coef']:.4f} (p={out['headline_pvalue']:.4f})"
            if not np.isnan(out["headline_coef"])
            else "head=NA"
        )
        plac_str = (
            f"plac[{out['placebo_term']}]={out['placebo_coef']:.4f} (p={out['placebo_pvalue']:.4f})"
            if out["placebo_term"]
            else "plac=NONE"
        )
        log(f"  {spec_name}: {head_str} | {plac_str} | N={out['n_obs']:,} [{elapsed:.0f}s]")
    except Exception as e:
        out["error"] = str(e)
        log(f"  {spec_name}: FAILED — {e}")
    return out


# =========================================================================
# STEP 1: Build derisking lookup from FDI base-period ratios
# =========================================================================
log("Building derisking lookup from FDI data...")
t0 = time.time()

fdi_data = (
    pl.scan_parquet(PANEL_PATH)
    .select(["pair", "year", "fdi_bilateral"])
    .filter(pl.col("fdi_bilateral").is_not_null())
    .unique(subset=["pair", "year"])
    .collect()
)
log(f"  FDI pair-years: {fdi_data.height:,}")

base_fdi = (
    fdi_data.filter(pl.col("year").is_in(BASE_PERIOD))
    .group_by("pair")
    .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
)

derisking = fdi_data.join(base_fdi, on="pair", how="left")
derisking = derisking.with_columns([
    (pl.col("fdi_bilateral") /
     pl.when(pl.col("fdi_base") > 0).then(pl.col("fdi_base")).otherwise(None)
     ).alias("fdi_ratio"),
])
derisking = derisking.with_columns([
    (pl.col("fdi_ratio").is_not_null() & (pl.col("fdi_ratio") < 0.50))
    .cast(pl.Int8).fill_null(0).alias("derisked"),
])
derisking = derisking.select(["pair", "year", "derisked"])
log(f"  Derisking lookup: {derisking.height:,} rows "
    f"({derisking.filter(pl.col('derisked') == 1).height:,} derisked)")

del fdi_data, base_fdi
gc.collect()
log(f"  Done in {time.time()-t0:.1f}s")


# =========================================================================
# STEP 1b: Subsample treated + control pairs (mirrors 16_confounder_estimation.py)
# =========================================================================
log("\nSubsampling pairs to fit memory budget...")
t_sub = time.time()

treated_pairs_all = (
    derisking.filter(pl.col("derisked") == 1)
    .select("pair").unique()
)
n_treated_all = treated_pairs_all.height
log(f"  Total treated pairs available: {n_treated_all:,}")

if n_treated_all > MAX_TREATED_PAIRS:
    treated_pairs = treated_pairs_all.sample(n=MAX_TREATED_PAIRS, seed=42)
else:
    treated_pairs = treated_pairs_all

all_pairs = derisking.select("pair").unique()
control_candidates = all_pairs.filter(
    ~pl.col("pair").is_in(treated_pairs["pair"].to_list())
)
n_control = min(MAX_CONTROL_PAIRS, control_candidates.height)
control_pairs = control_candidates.sample(n=n_control, seed=42)
log(f"  Treated kept: {treated_pairs.height:,}, control kept: {control_pairs.height:,}")

keep_pairs = pl.concat([treated_pairs, control_pairs])["pair"].to_list()
log(f"  Total pairs in subsample: {len(keep_pairs):,}")

del treated_pairs_all, treated_pairs, control_pairs, control_candidates, all_pairs
gc.collect()
log(f"  Subsample built in {time.time()-t_sub:.1f}s")


# =========================================================================
# STEP 2: Load subsampled panel for 2018-2023 with placebo-friction columns
# =========================================================================
log("\nLoading 2018-2023 panel slice (subsampled)...")
t0 = time.time()

# All columns potentially needed; we filter to those present at runtime.
schema = pl.read_parquet_schema(PANEL_PATH)
candidate_cols = [
    "trade_value", "pci_std",
    "ln_dist", "contig", "comlang_off", "colony", "rta_coverage",
    "exporter_year", "importer_year", "pair", "hs4", "year",
    "pf_cbr",  # legacy on-disk name; renamed below to fdi_proxy
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

# Legacy → fdi_proxy rename (mirrors rename_pf_to_fdi() in scripts/R/00_config.R).
rename_map = {old: old.replace("pf_cbr", "fdi_proxy")
              for old in panel.columns if old.startswith("pf_cbr")}
if rename_map:
    panel = panel.rename(rename_map)
    log(f"  Renamed columns (legacy -> new): {rename_map}")

# Merge derisking
panel = panel.join(derisking, on=["pair", "year"], how="left")
panel = panel.with_columns(pl.col("derisked").fill_null(0))
log(f"  Loaded: {panel.height:,} rows in {time.time()-t0:.1f}s "
    f"(derisked obs: {panel.filter(pl.col('derisked') == 1).height:,})")

# Convert to pandas for pyfixest
df = panel.to_pandas()
del panel
gc.collect()

for c in ["exporter_year", "importer_year", "pair", "hs4"]:
    df[c] = df[c].astype(str)
df["derisked"] = df["derisked"].fillna(0).astype(int)

# rta_coverage may have NAs; drop those when running F5
log(f"  Pandas frame: N={len(df):,}, derisked={(df['derisked']==1).sum():,}, "
    f"rta non-null={df['rta_coverage'].notna().sum():,}" if "rta_coverage" in df.columns
    else f"  Pandas frame: N={len(df):,}, derisked={(df['derisked']==1).sum():,}")


# =========================================================================
# STEP 3: Define and run specifications F0–F5
# =========================================================================
FE = "exporter_year + importer_year + pair + hs4"
HEADLINE = "derisked + derisked:pci_std"

SPECS = {
    "F0: Baseline":
        f"trade_value ~ {HEADLINE} | {FE}",
    "F1: + ln_dist x PCI":
        f"trade_value ~ {HEADLINE} + ln_dist:pci_std | {FE}",
    "F2: + comlang_off x PCI":
        f"trade_value ~ {HEADLINE} + comlang_off:pci_std | {FE}",
    "F3: + contig x PCI":
        f"trade_value ~ {HEADLINE} + contig:pci_std | {FE}",
    "F4: + colony x PCI":
        f"trade_value ~ {HEADLINE} + colony:pci_std | {FE}",
    "F5: + rta_coverage x PCI":
        f"trade_value ~ {HEADLINE} + rta_coverage:pci_std | {FE}",
}

log("\n" + "=" * 60)
log("FALSIFICATION SPECIFICATIONS")
log("=" * 60)

results = []
for spec_name, formula in SPECS.items():
    log(f"\n>>> {spec_name}")
    needed = []
    if "rta_coverage" in formula:
        needed.append("rta_coverage")
    if "comlang_off" in formula:
        needed.append("comlang_off")
    if "contig" in formula:
        needed.append("contig")
    if "colony" in formula:
        needed.append("colony")
    if "ln_dist" in formula:
        needed.append("ln_dist")

    sub = df
    for col in needed:
        if col in sub.columns:
            n_before = len(sub)
            sub = sub[sub[col].notna()]
            if len(sub) < n_before:
                log(f"  drop {n_before - len(sub):,} rows missing {col} → N={len(sub):,}")

    res = run_spec(formula, sub, {"CRV1": "pair"}, spec_name)
    results.append(res)


# =========================================================================
# STEP 4: Save results
# =========================================================================
log("\n" + "=" * 60)
log("SAVING RESULTS")
log("=" * 60)

results_df = pd.DataFrame(results)

# Pickle
with open(os.path.join(DIR_CLEAN, "estimates_falsification.pkl"), "wb") as fh:
    pickle.dump(results, fh)
log(f"  Saved: {os.path.join(DIR_CLEAN, 'estimates_falsification.pkl')}")

# CSV
csv_path = os.path.join(TABLE_DIR, "falsification_panel.csv")
results_df.to_csv(csv_path, index=False)
log(f"  Saved: {csv_path}")


# =========================================================================
# STEP 5: Booktabs LaTeX table (bare tabular, no in-table title or notes)
# =========================================================================
def fmt_coef(coef: float, pval: float) -> str:
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


def fmt_se(se: float) -> str:
    return "--" if pd.isna(se) else f"({se:.4f})"


def short_term(name: str) -> str:
    """Map raw pyfixest interaction names to clean LaTeX labels."""
    if not name:
        return ""
    pretty = (name
              .replace("ln_dist:pci_std",     r"$\ln(\text{dist}) \times \text{PCI}$")
              .replace("pci_std:ln_dist",     r"$\ln(\text{dist}) \times \text{PCI}$")
              .replace("comlang_off:pci_std", r"Common language $\times$ PCI")
              .replace("pci_std:comlang_off", r"Common language $\times$ PCI")
              .replace("contig:pci_std",      r"Contiguity $\times$ PCI")
              .replace("pci_std:contig",      r"Contiguity $\times$ PCI")
              .replace("colony:pci_std",      r"Colony $\times$ PCI")
              .replace("pci_std:colony",      r"Colony $\times$ PCI")
              .replace("rta_coverage:pci_std", r"RTA $\times$ PCI")
              .replace("pci_std:rta_coverage", r"RTA $\times$ PCI"))
    return pretty


col_labels = ["(1)", "(2)", "(3)", "(4)", "(5)", "(6)"]
spec_short = ["Baseline", "+ Distance", "+ Language", "+ Contiguity",
              "+ Colony", "+ RTA"]

n_specs = len(results)
col_spec = "l" + "c" * n_specs

tex = []
tex.append(r"\begin{tabular}{" + col_spec + "}")
tex.append(r"\toprule")
tex.append(" & " + " & ".join(col_labels[:n_specs]) + r" \\")
tex.append(" & " + " & ".join(spec_short[:n_specs]) + r" \\")
tex.append(r"\midrule")

# Headline row
tex.append(
    r"Derisked $\times$ PCI & "
    + " & ".join(fmt_coef(r["headline_coef"], r["headline_pvalue"]) for r in results)
    + r" \\"
)
tex.append(
    " & "
    + " & ".join(fmt_se(r["headline_se"]) for r in results)
    + r" \\"
)
tex.append(r"\midrule")

# Placebo rows: list all unique placebo terms encountered, one row each.
placebo_terms_in_order = []
for r in results:
    if r["placebo_term"] and r["placebo_term"] not in placebo_terms_in_order:
        placebo_terms_in_order.append(r["placebo_term"])

for term in placebo_terms_in_order:
    label = short_term(term)
    coef_cells = []
    se_cells   = []
    for r in results:
        if r["placebo_term"] == term:
            coef_cells.append(fmt_coef(r["placebo_coef"], r["placebo_pvalue"]))
            se_cells.append(fmt_se(r["placebo_se"]))
        else:
            coef_cells.append("--")
            se_cells.append("--")
    tex.append(label + " & " + " & ".join(coef_cells) + r" \\")
    tex.append(" & " + " & ".join(se_cells) + r" \\")

tex.append(r"\midrule")

# Footer rows
tex.append(
    "Observations & "
    + " & ".join(f"{int(r['n_obs']):,}" if not pd.isna(r["n_obs"]) else "--"
                 for r in results)
    + r" \\"
)
tex.append(
    "Pair $\\times$ year FE & " + " & ".join(["Yes"] * n_specs) + r" \\"
)
tex.append(
    "Exporter-year, Importer-year FE & " + " & ".join(["Yes"] * n_specs) + r" \\"
)
tex.append(
    "Product (HS4) FE & " + " & ".join(["Yes"] * n_specs) + r" \\"
)

tex.append(r"\bottomrule")
tex.append(r"\end{tabular}")

tex_path = os.path.join(TABLE_DIR, "falsification_panel.tex")
with open(tex_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(tex))
log(f"  Saved: {tex_path}")


# =========================================================================
# STEP 6: Summary line
# =========================================================================
log("\n" + "=" * 60)
log("SUMMARY")
log("=" * 60)

baseline = next((r for r in results if r["spec"].startswith("F0")), None)
baseline_coef = baseline["headline_coef"] if baseline else float("nan")

log(f"Headline (F0) gamma_FDI = {baseline_coef:.4f}"
    f" (vs ~-0.135 baseline reference in 16_confounder_estimation.py)")

for r in results[1:]:
    head = r["headline_coef"]
    plac = r["placebo_coef"]
    plac_p = r["placebo_pvalue"]
    if pd.isna(head):
        log(f"  {r['spec']}: headline did not converge")
        continue
    survives = (
        "survives"
        if (not pd.isna(baseline_coef)
            and np.sign(head) == np.sign(baseline_coef)
            and abs(head) > 0.5 * abs(baseline_coef))
        else "ATTENUATED"
    )
    plac_str = (f"placebo {r['placebo_term']}={plac:.4f} (p={plac_p:.4f})"
                if not pd.isna(plac) else "no placebo")
    log(f"  {r['spec']}: head={head:.4f} [{survives}]; {plac_str}")

placebos_null = [
    r for r in results[1:]
    if not pd.isna(r["placebo_pvalue"]) and r["placebo_pvalue"] > 0.10
]
log(f"\nPlacebos with p>0.10: {len(placebos_null)}/{len(results)-1}")

log("\nDone.")
