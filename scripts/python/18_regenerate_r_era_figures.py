"""
18_regenerate_r_era_figures.py -- Regenerate R-era figures in matplotlib.

Several figures in paper/figures/ were originally produced by R scripts that
no longer execute on the current 16 GB development machine. This script
re-creates each of them in pure Python (matplotlib + polars/pandas) using
the same source data, with the new larger-font style from _figure_style.py.

The output paths are preserved exactly so the LaTeX `\\includegraphics`
references in main.tex continue to resolve without edits.

Inputs
------
    paper/tables/11_robustness/robustness_specification_curve.csv
    paper/tables/12_falsification/falsification_panel.csv
    paper/tables/08_endogeneity/endogeneity_panel.csv
    paper/tables/09_sos_construction/sos_top20_composite.csv
    data/cleaned/sos_country_composite.parquet
    data/cleaned/gravity_unilateral.parquet

Outputs (overwriting existing R-era PDFs)
-----------------------------------------
    paper/figures/11_robustness/specification_curve_yearly.pdf
    paper/figures/11_robustness/specification_curve_panel.pdf
    paper/figures/12_falsification/falsification_panel.pdf
    paper/figures/08_endogeneity/endogeneity_panel_checks.pdf
    paper/figures/08_endogeneity/baseline_vs_lead.pdf
    paper/figures/13_figures/sos_vs_gdppc.pdf
    paper/figures/13_figures/world_heatmap_sos.pdf            (geopandas
                                                              fallback: top-30
                                                              horizontal bar)
    paper/figures/13_figures/world_derisking_exposure.pdf     (same fallback)
    paper/figures/13_figures/sos_decomposition_top20.pdf

Skipped (data not available on this machine)
--------------------------------------------
    paper/figures/10_validation/sos_vs_chainalysis.pdf
        Chainalysis grassroots-adoption data is not licensed for this run.
        Existing PDF left in place.

Style: serif, no in-figure titles, colorblind-aware (Set2 / viridis), vector PDF.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Shared style.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _figure_style import apply_style, COLOR_AMLD, COLOR_FATF, COLOR_FDI  # noqa: E402

apply_style()

PROJECT = Path(__file__).resolve().parents[2]
DATA_CLEAN = PROJECT / "data" / "cleaned"
TABLES = PROJECT / "paper" / "tables"
FIGS = PROJECT / "paper" / "figures"

# Try to import geopandas for the world map; fall back to bars if absent.
try:
    import geopandas as gpd  # noqa: F401
    HAS_GEOPANDAS = True
except Exception:
    HAS_GEOPANDAS = False


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path.relative_to(PROJECT)}")


# ---------------------------------------------------------------------------
# 1. specification_curve_panel.pdf and specification_curve_yearly.pdf
#
# The panel data comes from robustness_specification_curve.csv. There is no
# distinct "yearly" version in the data; per the task spec, when no yearly
# data exists we replicate the panel curve and rely on filename + LaTeX
# caption to disambiguate.
# ---------------------------------------------------------------------------
def _spec_curve_forest(csv_path: Path, out_path: Path, caption_hint: str) -> None:
    df = pd.read_csv(csv_path)
    df = df[df["converged"].fillna(False) & df["coef"].notna()].copy()
    if df.empty:
        print(f"  WARNING: no converged specs in {csv_path}; skipping")
        return
    df = df.sort_values("coef").reset_index(drop=True)

    coefs = df["coef"].to_numpy()
    err_lo = coefs - df["ci_lo"].to_numpy()
    err_hi = df["ci_hi"].to_numpy() - coefs
    labels = df["label"].tolist()

    fig, ax = plt.subplots(figsize=(10, max(6, 0.55 * len(df) + 1.5)))
    y = np.arange(len(df))
    ax.errorbar(coefs, y, xerr=[err_lo, err_hi],
                fmt="o", color="steelblue", ecolor="gray",
                elinewidth=1.5, capsize=4, markersize=9)
    ax.axvline(0, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    baseline_row = df[df["label"].str.startswith("R0")]
    if not baseline_row.empty:
        b = float(baseline_row["coef"].iloc[0])
        ax.axvline(b, color="firebrick", linestyle="--", linewidth=1.0,
                   alpha=0.7, label=f"R0 baseline ({b:.3f})")
        ax.legend(loc="best", frameon=False)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(f"Treatment x PCI coefficient (95% CI) -- {caption_hint}")
    fig.tight_layout()
    _save(fig, out_path)


def fig_specification_curves() -> None:
    csv = TABLES / "11_robustness" / "robustness_specification_curve.csv"
    _spec_curve_forest(csv, FIGS / "11_robustness" / "specification_curve_panel.pdf",
                       caption_hint="Panel pair-FE")
    _spec_curve_forest(csv, FIGS / "11_robustness" / "specification_curve_yearly.pdf",
                       caption_hint="Panel (yearly variant unavailable)")


# ---------------------------------------------------------------------------
# 2. falsification_panel.pdf -- forest plot of headline + placebo coefficients
# ---------------------------------------------------------------------------
def fig_falsification_panel() -> None:
    df = pd.read_csv(TABLES / "12_falsification" / "falsification_panel.csv")
    df = df[df["converged"].fillna(False)].copy()
    df = df.sort_values("spec").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(5.5, 0.7 * len(df) + 1.5)))
    y = np.arange(len(df))

    # Headline: derisked:pci_std coefficient
    h_coef = df["headline_coef"].to_numpy()
    h_se = df["headline_se"].to_numpy()
    h_lo, h_hi = h_coef - 1.96 * h_se, h_coef + 1.96 * h_se
    ax.errorbar(h_coef, y - 0.15, xerr=[h_coef - h_lo, h_hi - h_coef],
                fmt="o", color=COLOR_FDI, ecolor="gray",
                elinewidth=1.5, capsize=4, markersize=9,
                label="Headline (derisked x PCI)")

    # Placebo: optional row
    has_placebo = df["placebo_coef"].notna()
    if has_placebo.any():
        sub = df[has_placebo]
        ys = np.array([y[i] + 0.15 for i in sub.index])
        p_coef = sub["placebo_coef"].to_numpy()
        p_se = sub["placebo_se"].to_numpy()
        p_lo, p_hi = p_coef - 1.96 * p_se, p_coef + 1.96 * p_se
        ax.errorbar(p_coef, ys, xerr=[p_coef - p_lo, p_hi - p_coef],
                    fmt="s", color=COLOR_FATF, ecolor="gray",
                    elinewidth=1.5, capsize=4, markersize=9,
                    label="Placebo interaction")

    ax.axvline(0, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(df["spec"].tolist())
    ax.set_xlabel("Coefficient (95% CI)")
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    _save(fig, FIGS / "12_falsification" / "falsification_panel.pdf")


# ---------------------------------------------------------------------------
# 3. endogeneity_panel_checks.pdf -- forest of EN1, EN2, EN3 vs F0 baseline
# ---------------------------------------------------------------------------
F0_BASELINE_COEF = -0.198  # Headline F0 baseline from falsification_panel.csv


def fig_endogeneity_panel_checks() -> None:
    df = pd.read_csv(TABLES / "08_endogeneity" / "endogeneity_panel.csv")
    df = df[df["converged"].fillna(False)].copy().reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(4.5, 0.8 * len(df) + 1.5)))
    y = np.arange(len(df))
    coef = df["coef"].to_numpy()
    err_lo = coef - df["ci_lo"].to_numpy()
    err_hi = df["ci_hi"].to_numpy() - coef
    ax.errorbar(coef, y, xerr=[err_lo, err_hi],
                fmt="o", color=COLOR_FDI, ecolor="gray",
                elinewidth=1.6, capsize=5, markersize=10)
    ax.axvline(0, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.axvline(F0_BASELINE_COEF, color="firebrick", linestyle="--", linewidth=1.2,
               alpha=0.8, label=f"F0 baseline ({F0_BASELINE_COEF:+.3f})")
    ax.set_yticks(y)
    ax.set_yticklabels(df["short"].tolist())
    ax.set_xlabel("Treatment x PCI coefficient (95% CI)")
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    _save(fig, FIGS / "08_endogeneity" / "endogeneity_panel_checks.pdf")


# ---------------------------------------------------------------------------
# 4. baseline_vs_lead.pdf -- bar comparison of F0, Lag-1, Lag-2, Lead-1
# ---------------------------------------------------------------------------
def fig_baseline_vs_lead() -> None:
    df = pd.read_csv(TABLES / "08_endogeneity" / "endogeneity_panel.csv")
    df = df[df["converged"].fillna(False)].copy()

    rows = [{
        "label": "F0 baseline",
        "coef": F0_BASELINE_COEF,
        "se": 0.0606,  # from falsification_panel.csv F0 row
    }]
    for _, r in df.iterrows():
        rows.append({"label": r["short"], "coef": r["coef"], "se": r["se"]})
    plot_df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(plot_df))
    coef = plot_df["coef"].to_numpy()
    err = 1.96 * plot_df["se"].to_numpy()
    bars = ax.bar(x, coef, yerr=err, capsize=6,
                  color=[COLOR_FDI, COLOR_FATF, COLOR_FATF, COLOR_AMLD],
                  edgecolor="black", linewidth=0.5,
                  error_kw={"elinewidth": 1.4, "ecolor": "gray"})
    ax.axhline(0, color="black", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["label"].tolist())
    ax.set_ylabel("Treatment x PCI coefficient (95% CI)")
    fig.tight_layout()
    _save(fig, FIGS / "08_endogeneity" / "baseline_vs_lead.pdf")


# ---------------------------------------------------------------------------
# 5. sos_decomposition_top20.pdf -- stacked horizontal bar
# ---------------------------------------------------------------------------
def fig_sos_decomposition_top20() -> None:
    df = pd.read_csv(TABLES / "09_sos_construction" / "sos_top20_composite.csv")
    df = df.sort_values("sos_composite", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    y = np.arange(len(df))
    fatf = df["sos_fatf"].to_numpy()
    fdi = df["sos_fdi"].to_numpy()
    amld = -df["sos_amld"].to_numpy()  # AMLD subtracts; show on negative side

    ax.barh(y, fatf, color=COLOR_FATF, edgecolor="black", linewidth=0.4,
            label="FATF (intensive)")
    ax.barh(y, fdi, left=fatf, color=COLOR_FDI, edgecolor="black", linewidth=0.4,
            label="FDI (intensive)")
    ax.barh(y, amld, color=COLOR_AMLD, edgecolor="black", linewidth=0.4,
            label="AMLD adjustment (negative)")
    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(df["iso3"].tolist())
    ax.set_xlabel("Component contribution to composite SOS")
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    _save(fig, FIGS / "13_figures" / "sos_decomposition_top20.pdf")


# ---------------------------------------------------------------------------
# 6. sos_vs_gdppc.pdf -- scatter, ln(GDPpc) vs SOS, top-20 ISO labels
# ---------------------------------------------------------------------------
def fig_sos_vs_gdppc() -> None:
    sos = pd.read_parquet(DATA_CLEAN / "sos_country_composite.parquet")
    uni = pd.read_parquet(DATA_CLEAN / "gravity_unilateral.parquet")

    uni = uni.copy()
    uni["ln_gdpcap_raw"] = np.log(uni["gdpcap"].where(uni["gdpcap"] > 0))
    gdp = (
        uni.dropna(subset=["ln_gdpcap_raw"])
        .sort_values(["iso3", "year"])
        .groupby("iso3", as_index=False)
        .tail(1)[["iso3", "ln_gdpcap_raw"]]
        .rename(columns={"ln_gdpcap_raw": "ln_gdpcap"})
    )

    df = sos[["iso3", "sos_composite"]].merge(gdp, on="iso3", how="inner")
    df = df.dropna(subset=["sos_composite", "ln_gdpcap"]).reset_index(drop=True)

    top20 = df.sort_values("sos_composite", ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(df["ln_gdpcap"], df["sos_composite"],
               s=28, alpha=0.55, color=COLOR_FDI,
               edgecolor="black", linewidth=0.3)
    # Highlight top-20
    ax.scatter(top20["ln_gdpcap"], top20["sos_composite"],
               s=70, color=COLOR_FATF, edgecolor="black", linewidth=0.5,
               zorder=3, label="Top-20 SOS")

    # Labels for top-20 with simple thinning
    placed = []
    xrng = df["ln_gdpcap"].max() - df["ln_gdpcap"].min()
    yrng = df["sos_composite"].max() - df["sos_composite"].min()
    sx, sy = 0.04 * xrng, 0.04 * yrng
    for _, r in top20.iterrows():
        x, y = r["ln_gdpcap"], r["sos_composite"]
        if any(abs(x - px) < sx and abs(y - py) < sy for px, py in placed):
            continue
        ax.annotate(r["iso3"], xy=(x, y), xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=11, fontweight="bold")
        placed.append((x, y))

    ax.set_xlabel("ln(GDP per capita)")
    ax.set_ylabel("Composite Stablecoin Opportunity Score")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    _save(fig, FIGS / "13_figures" / "sos_vs_gdppc.pdf")


# ---------------------------------------------------------------------------
# 7. world_heatmap_sos.pdf -- choropleth (if geopandas) or top-30 bar fallback
# ---------------------------------------------------------------------------
def _world_choropleth(value_col: str, label: str, out: Path) -> None:
    """Render a quintile choropleth with a viridis palette."""
    import geopandas as gpd
    sos = pd.read_parquet(DATA_CLEAN / "sos_country_composite.parquet")
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    merged = world.merge(sos, left_on="iso_a3", right_on="iso3", how="left")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    merged.plot(column=value_col, cmap="viridis", ax=ax,
                legend=True, missing_kwds={"color": "lightgrey"},
                edgecolor="white", linewidth=0.2)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    _save(fig, out)


def _world_bar_fallback(value_col: str, xlabel: str, out: Path,
                        top_n: int = 30) -> None:
    """Top-N horizontal bar fallback when geopandas is unavailable."""
    sos = pd.read_parquet(DATA_CLEAN / "sos_country_composite.parquet")
    df = sos.dropna(subset=[value_col]).copy()
    df = df.sort_values(value_col, ascending=False).head(top_n)
    df = df.sort_values(value_col, ascending=True).reset_index(drop=True)

    # Color points by quintile (within full sample, not top-N)
    full = sos.dropna(subset=[value_col])
    quint = pd.qcut(full[value_col], q=5, labels=False, duplicates="drop")
    quint_lookup = dict(zip(full["iso3"].tolist(), quint.tolist()))
    cmap = plt.get_cmap("viridis")
    colors = [cmap(quint_lookup.get(iso3, 4) / 4.0) for iso3 in df["iso3"]]

    fig, ax = plt.subplots(figsize=(10, 11))
    y = np.arange(len(df))
    ax.barh(y, df[value_col], color=colors, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(df["iso3"].tolist())
    ax.set_xlabel(xlabel)
    fig.tight_layout()
    _save(fig, out)


def fig_world_heatmap_sos() -> None:
    out = FIGS / "13_figures" / "world_heatmap_sos.pdf"
    if HAS_GEOPANDAS:
        try:
            _world_choropleth("sos_composite", "Composite SOS", out)
            return
        except Exception as e:
            print(f"  geopandas choropleth failed ({e}); falling back to bars")
    print("  geopandas not available; rendering top-30 bar fallback")
    _world_bar_fallback("sos_composite",
                        "Composite Stablecoin Opportunity Score (top-30)",
                        out, top_n=30)


def fig_world_derisking_exposure() -> None:
    out = FIGS / "13_figures" / "world_derisking_exposure.pdf"
    # Use n_derisked_partners as the exposure indicator (share_derisked
    # column not present in sos_country_composite.parquet).
    if HAS_GEOPANDAS:
        try:
            _world_choropleth("n_derisked_partners",
                              "Number of de-risked FDI partners", out)
            return
        except Exception as e:
            print(f"  geopandas choropleth failed ({e}); falling back to bars")
    print("  geopandas not available; rendering top-30 bar fallback")
    _world_bar_fallback("n_derisked_partners",
                        "Number of de-risked FDI partners (top-30)",
                        out, top_n=30)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("18_regenerate_r_era_figures.py -- regenerating figures with larger fonts")
    print(f"  geopandas available: {HAS_GEOPANDAS}")
    fig_specification_curves()
    fig_falsification_panel()
    fig_endogeneity_panel_checks()
    fig_baseline_vs_lead()
    fig_sos_decomposition_top20()
    fig_sos_vs_gdppc()
    fig_world_heatmap_sos()
    fig_world_derisking_exposure()
    print("Note: paper/figures/10_validation/sos_vs_chainalysis.pdf NOT regenerated "
          "-- Chainalysis data not available on this machine; existing PDF kept in place.")
    print("Done.")


if __name__ == "__main__":
    main()
