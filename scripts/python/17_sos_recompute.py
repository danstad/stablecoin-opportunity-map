"""
17_sos_recompute.py — Composite Stablecoin Opportunity Score (SOS)

Builds a composite SOS using the three γ estimates from the 2026-04-06 confounder
estimation (panel pair-FE, 2018–2023). The composite is the headline ranking;
the FDI-only and FATF-only rankings are kept as comparators.

Headline coefficients (PE/PF/PB Panel from confounder_panel.csv):
    γ_AMLD = +0.14138 (SE 0.0689, p=0.040)   — eu_post2017:pci_std
    γ_FATF = -0.10759 (SE 0.0649, p=0.098)   — fatf_grey:pci_std
    γ_FDI  = -0.13464 (SE 0.0664, p=0.043)   — derisked:pci_std

SOS variants (country i, summed over partners j and HS2 chapters p):

    SOS_FDI[i]  = |γ_FDI|  × Σ_{j,p} ( |PCI_p| × derisked_{ij,T}     × X_{ij,p,T} )
    SOS_FATF[i] = |γ_FATF| × Σ_{j,p} ( |PCI_p| × fatf_grey_{ij,T}    × X_{ij,p,T} )
    SOS_AMLD[i] = |γ_AMLD| × Σ_{j,p} ( |PCI_p| × eu_post2017_{ij,T}  × X_{ij,p,T} )

    SOS_composite[i] = SOS_FATF[i] + SOS_FDI[i]  −  SOS_AMLD[i]

We use |PCI_p| so that "exposure to a complex-trade-affected corridor" is
non-negative regardless of whether the product is above- or below-mean
complexity. Each variant is then a non-negative country-level "exposure to
the friction (or clarity) shock weighted by complexity intensity."

The minus sign on SOS_AMLD is intentional: countries already covered by EU
regulatory harmonization need stablecoins less, so they are *down-weighted*
in the composite (regulatory clarity is a partial substitute for stablecoins).

Extensive margin uses the same construction with relatedness density × PCI ×
country-level treatment exposure share, following 09_sos_construction.R.

Uncertainty bands: γ ± 1.96·SE → sos_lo / sos_hi (analytic delta-method scaling).

Inputs:
    data/cleaned/panel_main_confounders.parquet
    data/cleaned/imf_fdi_bilateral.parquet
    data/cleaned/complexity_pci.parquet
    data/cleaned/complexity_density.parquet
    data/cleaned/complexity_rca.parquet
    paper/tables/15_confounders/confounder_panel.csv

Outputs:
    data/cleaned/sos_country_composite.parquet
    data/cleaned/sos_country_product_composite.parquet
    paper/tables/09_sos_construction/sos_top20_composite.tex
    paper/tables/09_sos_construction/sos_top20_composite.csv
    paper/tables/09_sos_construction/sos_ranking_correlations.tex
    paper/tables/09_sos_construction/sos_ranking_correlations.csv
    quality_reports/sos_recompute_summary.md

Usage:
    python scripts/python/17_sos_recompute.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

# ---------------------------------------------------------------------------
# 0. Setup
# ---------------------------------------------------------------------------
PROJECT = Path(__file__).resolve().parents[2]
DIR_CLEAN = PROJECT / "data" / "cleaned"
TABLE_DIR = PROJECT / "paper" / "tables" / "09_sos_construction"
QR_DIR    = PROJECT / "quality_reports"
TABLE_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)

PANEL_PATH        = DIR_CLEAN / "panel_main_confounders.parquet"
FDI_PATH          = DIR_CLEAN / "imf_fdi_bilateral.parquet"
PCI_PATH          = DIR_CLEAN / "complexity_pci.parquet"
DENSITY_PATH      = DIR_CLEAN / "complexity_density.parquet"
RCA_PATH          = DIR_CLEAN / "complexity_rca.parquet"
CONFOUNDER_PANEL  = PROJECT / "paper" / "tables" / "15_confounders" / "confounder_panel.csv"

BASE_PERIOD = [2015, 2016, 2017]
SAMPLE_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
T_YEAR = 2023  # latest year for cross-section computation

OMEGA = 0.5  # equal weight intensive vs extensive (matches 09_sos_construction.R)
Z_95 = 1.959964


def log(msg: str) -> None:
    # Force-encode for Windows cp1252 consoles by stripping non-ASCII
    safe = msg.encode("ascii", errors="replace").decode("ascii")
    print(f"[{time.strftime('%H:%M:%S')}] {safe}", flush=True)


# ---------------------------------------------------------------------------
# 1. Load γ estimates from confounder_panel.csv
# ---------------------------------------------------------------------------
log("=" * 70)
log("17_sos_recompute.py — Composite SOS from three-pronged identification")
log("=" * 70)

log("\n[1/8] Loading γ estimates from confounder_panel.csv ...")
panel_est = pd.read_csv(CONFOUNDER_PANEL)


def _pick(spec: str, interaction: str) -> tuple[float, float]:
    row = panel_est.query("spec == @spec and interaction == @interaction")
    if row.empty:
        raise RuntimeError(f"Missing estimate: spec={spec}, interaction={interaction}")
    return float(row["coef"].iloc[0]), float(row["se"].iloc[0])


gamma_amld, se_amld = _pick("PE: Panel AMLD", "eu_post2017:pci_std")
gamma_fatf, se_fatf = _pick("PF: Panel FATF", "fatf_grey:pci_std")
gamma_fdi,  se_fdi  = _pick("PB: Panel Baseline", "derisked:pci_std")

log(f"    γ_AMLD = {gamma_amld:+.5f} (SE {se_amld:.4f})")
log(f"    γ_FATF = {gamma_fatf:+.5f} (SE {se_fatf:.4f})")
log(f"    γ_FDI  = {gamma_fdi:+.5f}  (SE {se_fdi:.4f})")

# ---------------------------------------------------------------------------
# 2. Build derisked pair-year flag (same recipe as 16_confounder_estimation.py)
# ---------------------------------------------------------------------------
log("\n[2/8] Building derisked pair-year flag from FDI ...")

fdi = (
    pl.scan_parquet(FDI_PATH)
    .select(["iso3_o", "iso3_d", "year", "fdi_bilateral"])
    .filter(pl.col("fdi_bilateral").is_not_null())
    .unique(subset=["iso3_o", "iso3_d", "year"])
    .collect()
)
fdi = fdi.with_columns((pl.col("iso3_o") + "_" + pl.col("iso3_d")).alias("pair"))

base_fdi = (
    fdi.filter(pl.col("year").is_in(BASE_PERIOD))
    .group_by("pair")
    .agg(pl.col("fdi_bilateral").mean().alias("fdi_base"))
)

derisking = fdi.join(base_fdi, on="pair", how="left").with_columns(
    (
        pl.col("fdi_bilateral")
        / pl.when(pl.col("fdi_base") > 0).then(pl.col("fdi_base")).otherwise(None)
    ).alias("fdi_ratio"),
)
derisking = derisking.with_columns(
    (
        pl.col("fdi_ratio").is_not_null() & (pl.col("fdi_ratio") < 0.50)
    ).cast(pl.Int8).fill_null(0).alias("derisked")
).select(["iso3_o", "iso3_d", "year", "derisked"])

n_derisked_pairyears = int(derisking.filter(pl.col("derisked") == 1).height)
log(f"    Derisked pair-years: {n_derisked_pairyears:,} (of {derisking.height:,})")

# ---------------------------------------------------------------------------
# 3. Load corridor-level treatment indicators in the latest year (T)
# ---------------------------------------------------------------------------
log(f"\n[3/8] Loading panel for year {T_YEAR} (HS2 × pair) ...")

panel_T = (
    pl.scan_parquet(PANEL_PATH)
    .filter(pl.col("year") == T_YEAR)
    .select([
        "iso3_o", "iso3_d", "year", "hs4",
        "trade_value", "pci_std",
        "eu_post2017", "fatf_grey",
    ])
    .collect()
)
log(f"    Rows: {panel_T.height:,}")

# Merge derisked (pair, year)
derisking_T = derisking.filter(pl.col("year") == T_YEAR).select(
    ["iso3_o", "iso3_d", "derisked"]
)
panel_T = panel_T.join(derisking_T, on=["iso3_o", "iso3_d"], how="left").with_columns(
    pl.col("derisked").fill_null(0).cast(pl.Int8)
)

# Drop rows with missing pci or trade
panel_T = panel_T.filter(
    pl.col("pci_std").is_not_null() & pl.col("trade_value").is_not_null()
)
log(f"    Rows after dropping missing pci/trade: {panel_T.height:,}")
log(
    f"    Treatment rates (pair-product-year): "
    f"derisked={(panel_T['derisked']==1).sum()/panel_T.height:.3%}, "
    f"eu_post2017={(panel_T['eu_post2017']==1).sum()/panel_T.height:.3%}, "
    f"fatf_grey={(panel_T['fatf_grey']==1).sum()/panel_T.height:.3%}"
)

# Convert to pandas for easier groupby arithmetic
df = panel_T.to_pandas()
del panel_T

# ---------------------------------------------------------------------------
# 4. Intensive-margin SOS at country-product (i, p) level
# ---------------------------------------------------------------------------
log("\n[4/8] Computing intensive-margin SOS at country-product level ...")

# Per-row contributions: |PCI| × treatment × trade_value
# We use |PCI| so the country-level exposure measure is non-negative
# regardless of whether the country exports above- or below-mean complexity
# products. The sign of γ enters at the |γ| scaling step below.
abs_pci = df["pci_std"].abs()
df["x_fdi"]  = abs_pci * df["derisked"]    * df["trade_value"]
df["x_fatf"] = abs_pci * df["fatf_grey"]   * df["trade_value"]
df["x_amld"] = abs_pci * df["eu_post2017"] * df["trade_value"]

# Aggregate over partners → country-product (exporter × HS2)
agg_cp = (
    df.groupby(["iso3_o", "hs4"], as_index=False)
    .agg(
        sum_x_fdi=("x_fdi",  "sum"),
        sum_x_fatf=("x_fatf", "sum"),
        sum_x_amld=("x_amld", "sum"),
        trade_total=("trade_value", "sum"),
        trade_derisked=(
            "trade_value",
            lambda s: s[df.loc[s.index, "derisked"] == 1].sum(),
        ),
        trade_fatf=(
            "trade_value",
            lambda s: s[df.loc[s.index, "fatf_grey"] == 1].sum(),
        ),
        trade_amld=(
            "trade_value",
            lambda s: s[df.loc[s.index, "eu_post2017"] == 1].sum(),
        ),
        n_derisked_partners=(
            "derisked",
            lambda s: s.gt(0).any(),
        ),  # we'll recompute properly below
    )
)

# Proper count of distinct derisked partners per (iso3_o, hs4) — boolean trick
n_partners = (
    df[df["derisked"] == 1]
    .drop_duplicates(["iso3_o", "iso3_d", "hs4"])
    .groupby(["iso3_o", "hs4"], as_index=False)
    .size()
    .rename(columns={"size": "n_derisked_partners"})
)
agg_cp = agg_cp.drop(columns=["n_derisked_partners"]).merge(
    n_partners, on=["iso3_o", "hs4"], how="left"
)
agg_cp["n_derisked_partners"] = agg_cp["n_derisked_partners"].fillna(0).astype(int)

# Apply |γ| scalings to obtain intensive SOS variants (all non-negative)
agg_cp["sos_fdi_int"]  = abs(gamma_fdi)  * agg_cp["sum_x_fdi"]
agg_cp["sos_fatf_int"] = abs(gamma_fatf) * agg_cp["sum_x_fatf"]
agg_cp["sos_amld_int"] = abs(gamma_amld) * agg_cp["sum_x_amld"]

# Composite: SOS_FATF + SOS_FDI − SOS_AMLD (down-weight EU corridors)
agg_cp["sos_composite_int"] = (
    agg_cp["sos_fatf_int"] + agg_cp["sos_fdi_int"] - agg_cp["sos_amld_int"]
)

log(f"    Country-product rows: {len(agg_cp):,}")
log(
    f"    Intensive totals (sum across all i,p): "
    f"FDI={agg_cp['sos_fdi_int'].sum():.3e}, "
    f"FATF={agg_cp['sos_fatf_int'].sum():.3e}, "
    f"AMLD={agg_cp['sos_amld_int'].sum():.3e}"
)

# ---------------------------------------------------------------------------
# 5. Extensive-margin SOS — relatedness density × country-level treatment share
#    (mirrors 09_sos_construction.R but with three γ instead of one β)
# ---------------------------------------------------------------------------
log("\n[5/8] Computing extensive-margin SOS ...")

pci      = pd.read_parquet(PCI_PATH).rename(columns={"hs4": "hs4"})
density  = pd.read_parquet(DENSITY_PATH)
rca      = pd.read_parquet(RCA_PATH)

density_T = density[density["year"] == T_YEAR][["iso3", "hs4", "density"]]
rca_T     = rca[rca["year"] == T_YEAR][["iso3", "hs4", "has_rca"]]

# Country-level treatment exposure shares (weighted by trade in T)
country_exposure = (
    df.groupby("iso3_o")
    .apply(
        lambda g: pd.Series({
            "share_derisked": (g["trade_value"] * g["derisked"]).sum()
            / g["trade_value"].sum() if g["trade_value"].sum() > 0 else 0.0,
            "share_fatf":     (g["trade_value"] * g["fatf_grey"]).sum()
            / g["trade_value"].sum() if g["trade_value"].sum() > 0 else 0.0,
            "share_amld":     (g["trade_value"] * g["eu_post2017"]).sum()
            / g["trade_value"].sum() if g["trade_value"].sum() > 0 else 0.0,
        }),
        include_groups=False,
    )
    .reset_index()
    .rename(columns={"iso3_o": "iso3"})
)
log(f"    Country exposure shares for {len(country_exposure)} countries")

# Build extensive frame: only (iso3, hs4) where RCA < 1 (potential entries)
ext = rca_T[rca_T["has_rca"] == 0][["iso3", "hs4"]].merge(
    density_T, on=["iso3", "hs4"], how="left"
).merge(
    pci[["hs4", "pci_std"]], on="hs4", how="left"
).merge(
    country_exposure, on="iso3", how="left"
)
ext = ext.dropna(subset=["density", "pci_std"])
ext = ext.fillna({"share_derisked": 0.0, "share_fatf": 0.0, "share_amld": 0.0})

# Extensive SOS variants: |γ| × density × |PCI| × country-share (all non-negative)
abs_pci_ext = ext["pci_std"].abs()
ext["sos_fdi_ext"]  = abs(gamma_fdi)  * ext["density"] * abs_pci_ext * ext["share_derisked"]
ext["sos_fatf_ext"] = abs(gamma_fatf) * ext["density"] * abs_pci_ext * ext["share_fatf"]
ext["sos_amld_ext"] = abs(gamma_amld) * ext["density"] * abs_pci_ext * ext["share_amld"]

ext["sos_composite_ext"] = ext["sos_fatf_ext"] + ext["sos_fdi_ext"] - ext["sos_amld_ext"]
log(f"    Extensive country-product rows (RCA<1): {len(ext):,}")

# ---------------------------------------------------------------------------
# 6. Combine intensive + extensive at country-product level
# ---------------------------------------------------------------------------
log("\n[6/8] Combining intensive + extensive into country-product SOS ...")

# Align column names between intensive and extensive frames
agg_cp = agg_cp.rename(columns={"iso3_o": "iso3"})

cp = agg_cp.merge(
    ext[["iso3", "hs4", "density",
         "sos_fdi_ext", "sos_fatf_ext", "sos_amld_ext", "sos_composite_ext",
         "share_derisked", "share_fatf", "share_amld"]],
    on=["iso3", "hs4"],
    how="outer",
)

# Fill missing margins with 0 so the union covers RCA<1 entries even if no trade
for c in [
    "sos_fdi_int", "sos_fatf_int", "sos_amld_int", "sos_composite_int",
    "sos_fdi_ext", "sos_fatf_ext", "sos_amld_ext", "sos_composite_ext",
]:
    cp[c] = cp.get(c, 0.0)
    cp[c] = cp[c].fillna(0.0)


def _norm(x: pd.Series) -> pd.Series:
    """Normalize a column to its max absolute value (preserve sign for AMLD)."""
    m = x.abs().max()
    return x / m if m > 0 else x * 0.0


# Normalize each variant's margins to the same scale as 09_sos_construction.R
cp["fdi_int_n"]  = _norm(cp["sos_fdi_int"])
cp["fdi_ext_n"]  = _norm(cp["sos_fdi_ext"])
cp["fatf_int_n"] = _norm(cp["sos_fatf_int"])
cp["fatf_ext_n"] = _norm(cp["sos_fatf_ext"])
cp["amld_int_n"] = _norm(cp["sos_amld_int"])
cp["amld_ext_n"] = _norm(cp["sos_amld_ext"])

cp["sos_fdi"]       = OMEGA * cp["fdi_int_n"]  + (1 - OMEGA) * cp["fdi_ext_n"]
cp["sos_fatf"]      = OMEGA * cp["fatf_int_n"] + (1 - OMEGA) * cp["fatf_ext_n"]
cp["sos_amld"]      = OMEGA * cp["amld_int_n"] + (1 - OMEGA) * cp["amld_ext_n"]
cp["sos_composite"] = cp["sos_fatf"] + cp["sos_fdi"] - cp["sos_amld"]

# Attach pci for downstream tables
cp = cp.merge(pci[["hs4", "pci_std", "pci_raw"]], on="hs4", how="left",
              suffixes=("", "_dup"))
cp = cp.drop(columns=[c for c in cp.columns if c.endswith("_dup")])

cp.to_parquet(DIR_CLEAN / "sos_country_product_composite.parquet", index=False)
log(f"    Wrote sos_country_product_composite.parquet ({len(cp):,} rows)")

# ---------------------------------------------------------------------------
# 7. Aggregate to country level + uncertainty bands
# ---------------------------------------------------------------------------
log("\n[7/8] Aggregating to country level and computing uncertainty bands ...")

country = (
    cp.groupby("iso3", as_index=False)
    .agg(
        sos_fdi=("sos_fdi", "sum"),
        sos_fatf=("sos_fatf", "sum"),
        sos_amld=("sos_amld", "sum"),
        sos_composite=("sos_composite", "sum"),
        sos_fdi_int=("sos_fdi_int", "sum"),
        sos_fatf_int=("sos_fatf_int", "sum"),
        sos_amld_int=("sos_amld_int", "sum"),
        sos_fdi_ext=("sos_fdi_ext", "sum"),
        sos_fatf_ext=("sos_fatf_ext", "sum"),
        sos_amld_ext=("sos_amld_ext", "sum"),
        trade_derisked=("trade_derisked", "sum"),
        trade_fatf=("trade_fatf", "sum"),
        trade_amld=("trade_amld", "sum"),
        n_derisked_partners=("n_derisked_partners", "max"),
    )
)

# Rankings: largest SOS = rank 1
for col, rank_col in [
    ("sos_fdi", "rank_fdi"),
    ("sos_fatf", "rank_fatf"),
    ("sos_amld", "rank_amld"),
    ("sos_composite", "rank_composite"),
]:
    country[rank_col] = country[col].rank(ascending=False, method="min").astype(int)

# Uncertainty bands for the composite — analytic delta-method scaling
# Composite = |γ_FATF|·U_FATF + |γ_FDI|·U_FDI − γ_AMLD·U_AMLD,
# where U_X = Σ_{j,p} (PCI × treatment × trade) (after intensive normalization
# this is captured by the pre-scaled sums; for bands we scale at the country level).
g_fatf_lo, g_fatf_hi = gamma_fatf - Z_95 * se_fatf, gamma_fatf + Z_95 * se_fatf
g_fdi_lo,  g_fdi_hi  = gamma_fdi  - Z_95 * se_fdi,  gamma_fdi  + Z_95 * se_fdi
g_amld_lo, g_amld_hi = gamma_amld - Z_95 * se_amld, gamma_amld + Z_95 * se_amld


def _scale(x: pd.Series, gamma_old: float, gamma_new: float, signed: bool = False) -> pd.Series:
    """Re-scale an SOS column from |γ_old| (or γ_old) to |γ_new| (or γ_new)."""
    if signed:
        return x * (gamma_new / gamma_old) if gamma_old != 0 else x * 0.0
    return x * (abs(gamma_new) / abs(gamma_old)) if gamma_old != 0 else x * 0.0


# Lower bound: most pessimistic for the composite ⇒
# smaller |γ_FATF|, smaller |γ_FDI|, larger γ_AMLD (more "regulatory substitute")
# but for uncertainty bands we report the symmetric ±1.96·SE re-scaling on each γ.
country["sos_fatf_lo"] = _scale(country["sos_fatf"], gamma_fatf, g_fatf_lo if abs(g_fatf_lo) < abs(g_fatf_hi) else g_fatf_hi)
country["sos_fatf_hi"] = _scale(country["sos_fatf"], gamma_fatf, g_fatf_lo if abs(g_fatf_lo) > abs(g_fatf_hi) else g_fatf_hi)
country["sos_fdi_lo"]  = _scale(country["sos_fdi"],  gamma_fdi,  g_fdi_lo  if abs(g_fdi_lo)  < abs(g_fdi_hi)  else g_fdi_hi)
country["sos_fdi_hi"]  = _scale(country["sos_fdi"],  gamma_fdi,  g_fdi_lo  if abs(g_fdi_lo)  > abs(g_fdi_hi)  else g_fdi_hi)
country["sos_amld_lo"] = _scale(country["sos_amld"], gamma_amld, g_amld_lo if abs(g_amld_lo) < abs(g_amld_hi) else g_amld_hi)
country["sos_amld_hi"] = _scale(country["sos_amld"], gamma_amld, g_amld_lo if abs(g_amld_lo) > abs(g_amld_hi) else g_amld_hi)

country["sos_composite_lo"] = country["sos_fatf_lo"] + country["sos_fdi_lo"] - country["sos_amld_hi"]
country["sos_composite_hi"] = country["sos_fatf_hi"] + country["sos_fdi_hi"] - country["sos_amld_lo"]

country["rank_composite_lo"] = country["sos_composite_lo"].rank(ascending=False, method="min").astype(int)
country["rank_composite_hi"] = country["sos_composite_hi"].rank(ascending=False, method="min").astype(int)
country["rank_range"] = (country["rank_composite_hi"] - country["rank_composite_lo"]).abs()

country = country.sort_values("rank_composite").reset_index(drop=True)
country.to_parquet(DIR_CLEAN / "sos_country_composite.parquet", index=False)
log(f"    Wrote sos_country_composite.parquet ({len(country)} countries)")

# ---------------------------------------------------------------------------
# 8. Output tables: top-20, ranking correlations, summary
# ---------------------------------------------------------------------------
log("\n[8/8] Writing output tables ...")

# --- Top-20 under composite -------------------------------------------------
top20 = country.head(20).copy()
top20_cols = [
    "rank_composite", "iso3",
    "sos_composite", "sos_fatf", "sos_fdi", "sos_amld",
    "n_derisked_partners", "trade_derisked",
    "rank_composite_lo", "rank_composite_hi", "rank_range",
]
top20_csv = top20[top20_cols].rename(columns={
    "rank_composite": "rank",
    "n_derisked_partners": "n_derisked",
    "trade_derisked": "trade_at_risk_usd",
})
top20_csv.to_csv(TABLE_DIR / "sos_top20_composite.csv", index=False)
log(f"    Wrote sos_top20_composite.csv")

# Booktabs LaTeX (no \hline, no in-table title or notes per content-standards.md)
def _fmt(x, prec=2, scale=1.0):
    if pd.isna(x):
        return "--"
    return f"{x*scale:.{prec}f}"


tex_lines = [
    r"\begin{tabular}{clcccccccc}",
    r"\toprule",
    r"Rank & Country & Composite & FATF & FDI & AMLD & De-risked & Trade at risk & Rank low & Rank high \\",
    r" & & SOS & SOS & SOS & adj. & partners & (USD M) & ($\gamma$ low) & ($\gamma$ high) \\",
    r"\midrule",
]
for _, r in top20.iterrows():
    tex_lines.append(
        f"{int(r['rank_composite'])} & {r['iso3']} & "
        f"{_fmt(r['sos_composite'], 2)} & "
        f"{_fmt(r['sos_fatf'], 2)} & "
        f"{_fmt(r['sos_fdi'], 2)} & "
        f"{_fmt(r['sos_amld'], 2)} & "
        f"{int(r['n_derisked_partners'])} & "
        f"{_fmt(r['trade_derisked']/1e6, 1)} & "
        f"{int(r['rank_composite_lo'])} & "
        f"{int(r['rank_composite_hi'])} \\\\"
    )
tex_lines += [r"\bottomrule", r"\end{tabular}"]
(TABLE_DIR / "sos_top20_composite.tex").write_text("\n".join(tex_lines), encoding="utf-8")
log(f"    Wrote sos_top20_composite.tex")

# --- Spearman correlations across rankings ---------------------------------
ranks = country[["rank_fdi", "rank_fatf", "rank_composite"]]
corr = ranks.corr(method="spearman")
corr.index   = ["SOS_FDI", "SOS_FATF", "SOS_composite"]
corr.columns = ["SOS_FDI", "SOS_FATF", "SOS_composite"]
corr.to_csv(TABLE_DIR / "sos_ranking_correlations.csv")

corr_tex = [
    r"\begin{tabular}{lccc}",
    r"\toprule",
    r" & SOS$_{\text{FDI}}$ & SOS$_{\text{FATF}}$ & SOS$_{\text{composite}}$ \\",
    r"\midrule",
]
for label, row in corr.iterrows():
    corr_tex.append(
        f"{label.replace('_', ' ')} & "
        f"{row['SOS_FDI']:.3f} & {row['SOS_FATF']:.3f} & {row['SOS_composite']:.3f} \\\\"
    )
corr_tex += [r"\bottomrule", r"\end{tabular}"]
(TABLE_DIR / "sos_ranking_correlations.tex").write_text("\n".join(corr_tex), encoding="utf-8")
log(f"    Wrote sos_ranking_correlations.tex")

# --- Console summary -------------------------------------------------------
log("\n" + "=" * 70)
log("RESULTS SUMMARY")
log("=" * 70)

for label, col, rank_col in [
    ("SOS_FDI",       "sos_fdi",       "rank_fdi"),
    ("SOS_FATF",      "sos_fatf",      "rank_fatf"),
    ("SOS_composite", "sos_composite", "rank_composite"),
]:
    log(f"\nTop 5 by {label}:")
    top5 = country.sort_values(rank_col).head(5)[["iso3", col, rank_col]]
    for _, r in top5.iterrows():
        log(f"  {int(r[rank_col]):2d}. {r['iso3']}  {col}={r[col]:+.4f}")

log("\nSpearman rank correlations:")
log(corr.round(3).to_string())

# Quintile-shift count (composite vs FDI baseline)
def _quintile(series: pd.Series) -> pd.Series:
    return pd.qcut(series.rank(ascending=False, method="first"), 5, labels=False) + 1

qf  = _quintile(country["sos_fdi"])
qc  = _quintile(country["sos_composite"])
qff = _quintile(country["sos_fatf"])
n_q_change_fdi  = int((qf  != qc).sum())
n_q_change_fatf = int((qff != qc).sum())
log(
    f"\nQuintile shifts vs composite: "
    f"FDI→composite = {n_q_change_fdi}/{len(country)}; "
    f"FATF→composite = {n_q_change_fatf}/{len(country)}"
)

# Validation: Spearman(FDI, composite) should exceed 0.5 as a sanity floor
sp_fdi_comp = corr.loc["SOS_FDI", "SOS_composite"]
status = "PASS" if sp_fdi_comp > 0.5 else "BORDERLINE" if sp_fdi_comp > 0.4 else "FAIL"
log(f"\nValidation: Spearman(SOS_FDI, SOS_composite) = {sp_fdi_comp:.3f} "
    f"[{status} - sanity floor 0.5; "
    f"composite intentionally re-orders rankings via FATF + AMLD]")

# --- Markdown summary for writer agent -------------------------------------
top5_comp = country.head(5)["iso3"].tolist()
top5_fdi  = country.sort_values("rank_fdi").head(5)["iso3"].tolist()
top5_fatf = country.sort_values("rank_fatf").head(5)["iso3"].tolist()
overlap_fdi  = set(top5_comp) & set(top5_fdi)
overlap_fatf = set(top5_comp) & set(top5_fatf)

md = f"""# SOS Recompute Summary — {time.strftime('%Y-%m-%d')}

Recomputed Stablecoin Opportunity Score using the three gamma estimates from
the 2026-04-06 panel pair-FE confounder estimation:
gamma_AMLD = {gamma_amld:+.4f} (SE {se_amld:.4f}); gamma_FATF = {gamma_fatf:+.4f} (SE {se_fatf:.4f});
gamma_FDI = {gamma_fdi:+.4f} (SE {se_fdi:.4f}). The composite SOS is
SOS_composite = SOS_FATF + SOS_FDI - SOS_AMLD, where the AMLD term enters with
a minus sign so countries already covered by EU regulatory harmonization are
down-weighted (regulatory clarity is a partial substitute for stablecoins).

**Top-5 stability across rankings.** Composite top-5: {top5_comp}.
Of these, {len(overlap_fdi)}/5 also appear in the FDI-only top-5 ({top5_fdi}) and
{len(overlap_fatf)}/5 also appear in the FATF-only top-5 ({top5_fatf}).
Spearman rank correlations: rho(FDI, composite) = {sp_fdi_comp:.3f},
rho(FATF, composite) = {corr.loc['SOS_FATF','SOS_composite']:.3f},
rho(FDI, FATF) = {corr.loc['SOS_FDI','SOS_FATF']:.3f}. Quintile shifts vs composite:
FDI -> composite reassigns {n_q_change_fdi} of {len(country)} countries to a
different quintile; FATF -> composite reassigns {n_q_change_fatf}. The two
single-instrument rankings are themselves only weakly correlated
(rho(FDI, FATF) = {corr.loc['SOS_FDI','SOS_FATF']:.3f}), reflecting that FATF
greylisting and FDI-derisking identify substantively different sets of
exposed countries. The composite therefore *necessarily* re-orders the
rankings — by design — and the paper should defend it as a
weighted-evidence aggregator rather than claim "robust to gamma choice."
"""
(QR_DIR / "sos_recompute_summary.md").write_text(md, encoding="utf-8")
log(f"\nWrote {QR_DIR / 'sos_recompute_summary.md'}")

# --- Append to research journal --------------------------------------------
journal = QR_DIR / "research_journal.md"
journal_entry = (
    f"\n### {time.strftime('%Y-%m-%d %H:%M')} — coder\n"
    f"**Phase:** Execution\n"
    f"**Target:** scripts/python/17_sos_recompute.py — composite SOS\n"
    f"**Score:** N/A (pending coder-critic)\n"
    f"**Verdict:** Recomputed SOS using three γ; "
    f"Spearman(FDI, composite)={sp_fdi_comp:.3f}; top-5 composite = {top5_comp}.\n"
    f"**Report:** quality_reports/sos_recompute_summary.md\n"
)
with journal.open("a", encoding="utf-8") as f:
    f.write(journal_entry)
log(f"Appended to {journal}")

log("\nDone.")
