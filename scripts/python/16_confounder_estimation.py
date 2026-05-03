"""
16_confounder_estimation.py — Three-pronged identification: AMLD, FATF, Horse Race

MEMORY-EFFICIENT: Builds derisking lookup, frees memory, processes each year from disk.

Inputs:  data/cleaned/panel_main_confounders.parquet
Outputs: data/cleaned/estimates_confounders.pkl
         paper/tables/15_confounders/
         paper/figures/15_confounders/
"""

import os, sys, time, pickle, warnings, gc
import numpy as np
import pandas as pd
import polars as pl
import pyfixest as pf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_CLEAN = os.path.join(PROJECT, "data", "cleaned")
TABLE_DIR = os.path.join(PROJECT, "paper", "tables", "15_confounders")
FIG_DIR   = os.path.join(PROJECT, "paper", "figures", "15_confounders")
os.makedirs(TABLE_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

PANEL_PATH = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")
BASE_PERIOD = [2015, 2016, 2017]
POST_YEARS  = [2018, 2019, 2020, 2021, 2022, 2023]
MAX_TREATED_PAIRS = 2000
MAX_CONTROL_PAIRS = 1000

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def run_spec(formula, data, vcov, spec_name, yr=None):
    """Run a single PPML specification and return result dicts."""
    try:
        t0 = time.time()
        m = pf.fepois(formula, data=data, vcov=vcov)
        coefs, ses, pvals = m.coef(), m.se(), m.pvalue()
        elapsed = time.time() - t0
        interactions = [n for n in coefs.index if ":" in n and "pci" in n.lower()]
        results = []
        for iname in interactions:
            stars = "***" if pvals[iname] < 0.01 else "**" if pvals[iname] < 0.05 else "*" if pvals[iname] < 0.10 else ""
            log(f"    {iname}: {coefs[iname]:.4f} (SE {ses[iname]:.4f}, p={pvals[iname]:.4f}){stars} [{elapsed:.0f}s]")
            results.append({
                "spec": spec_name, "year": yr, "interaction": iname,
                "coef": coefs[iname], "se": ses[iname], "pvalue": pvals[iname],
                "n_obs": m._N, "converged": True, "time_s": elapsed,
            })
        if not interactions:
            log(f"    WARNING: No PCI interaction found")
            results.append({"spec": spec_name, "year": yr, "interaction": "NONE", "converged": True, "n_obs": m._N})
        return results
    except Exception as e:
        log(f"    FAILED: {e}")
        return [{"spec": spec_name, "year": yr, "interaction": "FAILED", "converged": False, "error": str(e)}]

# =========================================================================
# STEP 1: Build derisking lookup (pair × year level, ~200K rows)
# =========================================================================
log("Building derisking lookup from FDI data...")
t0 = time.time()

# Read only the columns needed for derisking construction
fdi_cols = ["pair", "year", "fdi_bilateral"]
fdi_data = (
    pl.scan_parquet(PANEL_PATH)
    .select(fdi_cols)
    .filter(pl.col("fdi_bilateral").is_not_null())
    .unique(subset=["pair", "year"])
    .collect()
)
log(f"  FDI pair-years: {fdi_data.height:,}")

# Base period average FDI
base_fdi = (
    fdi_data.filter(pl.col("year").is_in(BASE_PERIOD))
    .group_by("pair")
    .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
)

# Construct derisking at pair-year level
derisking = fdi_data.join(base_fdi, on="pair", how="left")
derisking = derisking.with_columns([
    (pl.col("fdi_bilateral") / pl.when(pl.col("fdi_base") > 0)
     .then(pl.col("fdi_base")).otherwise(None)).alias("fdi_ratio"),
])
derisking = derisking.with_columns([
    (pl.col("fdi_ratio").is_not_null() & (pl.col("fdi_ratio") < 0.50))
    .cast(pl.Int8).fill_null(0).alias("derisked"),
])
derisking = derisking.select(["pair", "year", "derisked"])
log(f"  Derisking lookup: {derisking.height:,} rows")
log(f"  Derisked pair-years: {derisking.filter(pl.col('derisked')==1).height:,}")

del fdi_data, base_fdi
gc.collect()
log(f"  Done in {time.time()-t0:.1f}s")

# =========================================================================
# STEP 2: Year-by-year cross-sections
# =========================================================================
log("\n" + "=" * 60)
log("PART 1: YEAR-BY-YEAR CROSS-SECTIONS")
log("=" * 60)

CONTROLS = "ln_dist + contig + comlang_off + colony"
FE_XS = "iso3_o + iso3_d + hs4"

SPECS_XS = {
    "B0: Baseline":
        f"trade_value ~ derisked + derisked:pci_std + {CONTROLS} | {FE_XS}",
    "E1: AMLD (primary)":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + {CONTROLS} | {FE_XS}",
    "E2: AMLD + FDI":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + derisked + derisked:pci_std + {CONTROLS} | {FE_XS}",
    "F1: FATF":
        f"trade_value ~ fatf_grey + fatf_grey:pci_std + {CONTROLS} | {FE_XS}",
    "F2: FATF + FDI":
        f"trade_value ~ fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + {CONTROLS} | {FE_XS}",
    "H1: Triple":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + {CONTROLS} | {FE_XS}",
    "H2: Kitchen sink":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + diplo_disagreement + diplo_disagreement:pci_std + {CONTROLS} | {FE_XS}",
    "H3: AMLD + confounders":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + diplo_disagreement + diplo_disagreement:pci_std + {CONTROLS} | {FE_XS}",
}

all_results = []

for yr in POST_YEARS:
    log(f"\n{'='*40} Year {yr} {'='*40}")
    t1 = time.time()

    # Read this year's data directly from parquet (scan + filter = memory efficient)
    read_cols = [
        "trade_value", "pci_std", "ln_dist", "contig", "comlang_off", "colony",
        "iso3_o", "iso3_d", "hs4", "pair", "year",
        "eu_post2017", "fatf_grey", "diplo_disagreement",
    ]
    chunk = (
        pl.scan_parquet(PANEL_PATH)
        .filter(
            (pl.col("year") == yr) &
            pl.col("pci_std").is_not_null() &
            pl.col("ln_dist").is_not_null()
        )
        .select([c for c in read_cols if c in pl.read_parquet_schema(PANEL_PATH)])
        .collect()
    )

    # Merge derisking
    derisking_yr = derisking.filter(pl.col("year") == yr).select(["pair", "derisked"])
    chunk = chunk.join(derisking_yr, on="pair", how="left")
    chunk = chunk.with_columns(pl.col("derisked").fill_null(0))

    log(f"  Loaded: {chunk.height:,} rows in {time.time()-t1:.1f}s")

    # Convert to pandas
    df_yr = chunk.to_pandas()
    del chunk; gc.collect()

    for c in ["iso3_o", "iso3_d", "hs4", "pair"]:
        df_yr[c] = df_yr[c].astype(str)
    for col in ["eu_post2017", "fatf_grey", "derisked"]:
        if col in df_yr.columns:
            df_yr[col] = df_yr[col].fillna(0).astype(int)

    n_yr = len(df_yr)
    log(f"  N={n_yr:,}, derisked={(df_yr['derisked']==1).sum():,}, eu_post2017={(df_yr['eu_post2017']==1).sum():,}, fatf_grey={(df_yr['fatf_grey']==1).sum():,}")

    for spec_name, formula in SPECS_XS.items():
        log(f"\n  {spec_name}:")
        if "diplo_disagreement" in formula:
            n_diplo = df_yr["diplo_disagreement"].notna().sum()
            if n_diplo < n_yr * 0.3:
                log(f"    SKIPPED: diplo_disagreement only {n_diplo:,}/{n_yr:,} non-null")
                all_results.append({"spec": spec_name, "year": yr, "interaction": "SKIPPED", "converged": False})
                continue
        results = run_spec(formula, df_yr, "hetero", spec_name, yr)
        all_results.extend(results)

    del df_yr; gc.collect()

# =========================================================================
# STEP 3: Panel with pair FE (smaller subsample)
# =========================================================================
log("\n" + "=" * 60)
log("PART 2: POOLED PANEL WITH PAIR FE")
log("=" * 60)

# Identify treated and control pairs from derisking lookup
treated_pairs_all = derisking.filter(
    pl.col("derisked") == 1
).select("pair").unique()
n_treated_all = treated_pairs_all.height
log(f"  Total treated pairs: {n_treated_all:,}")

np.random.seed(42)
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
log(f"  Treated pairs: {treated_pairs.height:,}, Control pairs: {control_pairs.height:,}")

keep_pairs = pl.concat([treated_pairs, control_pairs])["pair"].to_list()

del treated_pairs, treated_pairs_all, control_pairs, control_candidates, all_pairs, derisking
gc.collect()

# Read panel subsample from disk
log("  Reading panel subsample...")
t2 = time.time()

panel_cols = [
    "trade_value", "pci_std", "pair", "hs4", "year",
    "exporter_year", "importer_year",
    "eu_post2017", "fatf_grey", "diplo_disagreement",
    "fdi_bilateral", "iso3_o", "iso3_d",
]
panel_sub = (
    pl.scan_parquet(PANEL_PATH)
    .filter(
        pl.col("pair").is_in(keep_pairs) &
        pl.col("pci_std").is_not_null()
    )
    .select([c for c in panel_cols if c in pl.read_parquet_schema(PANEL_PATH)])
    .collect()
)
log(f"  Panel subsample: {panel_sub.height:,} rows in {time.time()-t2:.1f}s")

# Construct derisking for panel subsample
base_fdi_panel = (
    panel_sub.filter(pl.col("year").is_in(BASE_PERIOD))
    .group_by("pair")
    .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
)
panel_sub = panel_sub.join(base_fdi_panel, on="pair", how="left")
panel_sub = panel_sub.with_columns([
    (pl.col("fdi_bilateral") / pl.when(pl.col("fdi_base") > 0)
     .then(pl.col("fdi_base")).otherwise(None)).alias("fdi_ratio"),
])
panel_sub = panel_sub.with_columns([
    (pl.col("fdi_ratio").is_not_null() & (pl.col("fdi_ratio") < 0.50))
    .cast(pl.Int8).fill_null(0).alias("derisked"),
])

del base_fdi_panel
gc.collect()

# Convert to pandas
df_panel = panel_sub.select([
    "trade_value", "pci_std", "pair", "hs4",
    "exporter_year", "importer_year",
    "eu_post2017", "fatf_grey", "diplo_disagreement", "derisked",
]).to_pandas()
del panel_sub; gc.collect()

for c in ["exporter_year", "importer_year", "pair", "hs4"]:
    df_panel[c] = df_panel[c].astype(str)
for col in ["eu_post2017", "fatf_grey", "derisked"]:
    df_panel[col] = df_panel[col].fillna(0).astype(int)

log(f"  Panel N={len(df_panel):,}, derisked={(df_panel['derisked']==1).sum():,}")
log(f"  eu_post2017={(df_panel['eu_post2017']==1).sum():,}, fatf_grey={(df_panel['fatf_grey']==1).sum():,}")

FE_PANEL = "exporter_year + importer_year + pair + hs4"
SPECS_PANEL = {
    "PB: Panel Baseline":
        f"trade_value ~ derisked + derisked:pci_std | {FE_PANEL}",
    "PE: Panel AMLD":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std | {FE_PANEL}",
    "PF: Panel FATF":
        f"trade_value ~ fatf_grey + fatf_grey:pci_std | {FE_PANEL}",
    "PH: Panel Triple":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std | {FE_PANEL}",
    "PK: Panel Kitchen Sink":
        f"trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + diplo_disagreement + diplo_disagreement:pci_std | {FE_PANEL}",
}

for spec_name, formula in SPECS_PANEL.items():
    log(f"\n  {spec_name}:")
    if "diplo_disagreement" in formula:
        n_diplo = df_panel["diplo_disagreement"].notna().sum()
        if n_diplo < len(df_panel) * 0.3:
            log(f"    SKIPPED: diplo_disagreement only {n_diplo:,}/{len(df_panel):,}")
            all_results.append({"spec": spec_name, "year": "panel", "interaction": "SKIPPED", "converged": False})
            continue
    results = run_spec(formula, df_panel, {"CRV1": "pair"}, spec_name, yr="panel")
    all_results.extend(results)

del df_panel; gc.collect()

# =========================================================================
# STEP 4: Save results + generate outputs
# =========================================================================
log("\n" + "=" * 60)
log("SAVING RESULTS")
log("=" * 60)

results_df = pd.DataFrame(all_results)
results_df.to_pickle(os.path.join(DIR_CLEAN, "estimates_confounders.pkl"))
log(f"  Saved {len(results_df)} rows to estimates_confounders.pkl")

converged = results_df[results_df["converged"] == True].copy()

# CSV tables
if len(converged) > 0:
    yearly = converged[converged["year"] != "panel"]
    if len(yearly) > 0:
        yearly.to_csv(os.path.join(TABLE_DIR, "confounder_yearly.csv"), index=False)
        log(f"  Saved confounder_yearly.csv ({len(yearly)} rows)")

    panel_res = converged[converged["year"] == "panel"]
    if len(panel_res) > 0:
        panel_res.to_csv(os.path.join(TABLE_DIR, "confounder_panel.csv"), index=False)
        log(f"  Saved confounder_panel.csv ({len(panel_res)} rows)")

# Forest plot
try:
    plot_data = converged[
        converged["interaction"].str.contains("pci", case=False, na=False)
    ].copy()
    if len(plot_data) > 0:
        # Use 2020 (middle year) for cross-section + panel
        plot_xs = plot_data[plot_data["year"] == 2020]
        plot_panel = plot_data[plot_data["year"] == "panel"]
        plot_combined = pd.concat([plot_xs, plot_panel]).copy()

        if len(plot_combined) > 0:
            plot_combined["label"] = plot_combined.apply(
                lambda r: f"{r['spec']} | {r['interaction']}" + (" [panel]" if r["year"] == "panel" else ""), axis=1)
            plot_combined = plot_combined.sort_values("coef")

            fig, ax = plt.subplots(figsize=(10, max(6, len(plot_combined) * 0.35)))
            y_pos = range(len(plot_combined))
            ax.errorbar(plot_combined["coef"], y_pos, xerr=1.96 * plot_combined["se"],
                       fmt="o", color="steelblue", ecolor="gray", elinewidth=1.5, capsize=3, markersize=6)
            ax.axvline(x=0, color="red", linestyle="--", linewidth=0.8, alpha=0.6)
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(plot_combined["label"], fontsize=8, family="serif")
            ax.set_xlabel("Coefficient (95% CI)", fontsize=11, family="serif")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            plt.tight_layout()
            fig.savefig(os.path.join(FIG_DIR, "coefficient_comparison.pdf"), bbox_inches="tight", dpi=150)
            plt.close(fig)
            log("  Saved coefficient_comparison.pdf")
except Exception as e:
    log(f"  Forest plot FAILED: {e}")

# LaTeX: AMLD reduced form across years
try:
    amld_rows = converged[
        (converged["spec"] == "E1: AMLD (primary)") &
        (converged["year"] != "panel") &
        (converged["interaction"].str.contains("eu_post2017.*pci", case=False, na=False))
    ].sort_values("year")
    if len(amld_rows) > 0:
        lines = [r"\begin{tabular}{l" + "c" * len(amld_rows) + "}",
                 r"\toprule"]
        years_str = " & ".join([str(int(y)) for y in amld_rows["year"]])
        lines.append(f" & {years_str} \\\\")
        lines.append(r"\midrule")
        coef_str = " & ".join([
            f"{r['coef']:.4f}{'***' if r['pvalue']<0.01 else '**' if r['pvalue']<0.05 else '*' if r['pvalue']<0.10 else ''}"
            for _, r in amld_rows.iterrows()])
        lines.append(f"EU AMLD $\\times$ PCI & {coef_str} \\\\")
        se_str = " & ".join([f"({r['se']:.4f})" for _, r in amld_rows.iterrows()])
        lines.append(f" & {se_str} \\\\")
        lines.append(r"\midrule")
        n_str = " & ".join([f"{int(r['n_obs']):,}" for _, r in amld_rows.iterrows()])
        lines.append(f"Observations & {n_str} \\\\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        with open(os.path.join(TABLE_DIR, "amld_reduced_form.tex"), "w") as f:
            f.write("\n".join(lines))
        log("  Saved amld_reduced_form.tex")
except Exception as e:
    log(f"  LaTeX FAILED: {e}")

# Summary
log("\n" + "=" * 60)
log("SUMMARY")
log("=" * 60)
total = len(results_df)
conv = (results_df["converged"] == True).sum()
log(f"Total: {total}, Converged: {conv}, Failed: {total - conv}")

if len(converged) > 0:
    log("\nKey results:")
    for spec in ["B0: Baseline", "E1: AMLD (primary)", "F1: FATF", "H1: Triple"]:
        rows = converged[converged["spec"] == spec]
        for _, row in rows.iterrows():
            if "pci" in str(row.get("interaction", "")).lower():
                stars = "***" if row["pvalue"]<0.01 else "**" if row["pvalue"]<0.05 else "*" if row["pvalue"]<0.10 else ""
                log(f"  {spec} | yr={row['year']} | {row['interaction']}: {row['coef']:.4f}{stars}")

log("\nDone.")
