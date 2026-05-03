"""
13_figures.py -- Publication figures for the Stablecoin Opportunity Map paper.

This is the Python port of scripts/R/13_figures.R, which was never executed
because R/fixest crashes on the 16 GB development machine. Pure visualization
from already-computed estimates and cleaned panels; no estimation here.

Inputs
------
- paper/tables/15_confounders/confounder_panel.csv       (three-pronged panel gamma)
- paper/tables/15_confounders/confounder_yearly.csv      (yearly gamma, 2018-2023)
- paper/tables/09_sos_construction/sos_top20_composite.csv
- data/cleaned/sos_country_composite.parquet            (full 226-country rankings)
- data/cleaned/complexity_pci.parquet                   (HS4 PCI)
- data/cleaned/panel_main_confounders.parquet           (used sparingly; pf_cbr -> fdi_proxy)

Outputs (all PDF, paper/figures/13_figures/)
--------------------------------------------
- fig_yearly_three_pronged.pdf
- fig_sos_top20_composite.pdf
- fig_sos_decomposition.pdf
- fig_complexity_distribution.pdf
- fig_pci_treatment_correlation.pdf
- fig_ranking_correlations.pdf

Style: serif fonts, no in-figure titles, colorblind-aware palettes, vector PDF.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_CLEAN = ROOT / "data" / "cleaned"
TABLES = ROOT / "paper" / "tables"
FIG_DIR = ROOT / "paper" / "figures" / "13_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _figure_style import apply_style, COLOR_AMLD, COLOR_FATF, COLOR_FDI  # noqa: E402

apply_style()

MARKER_AMLD = "o"
MARKER_FATF = "s"
MARKER_FDI = "^"

LINESTYLE_AMLD = "-"
LINESTYLE_FATF = "--"
LINESTYLE_FDI = "-."


def save(fig, name: str) -> None:
    out = FIG_DIR / name
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Figure 1: Yearly three-pronged gamma
# ---------------------------------------------------------------------------
def fig_yearly_three_pronged() -> None:
    df = pd.read_csv(TABLES / "15_confounders" / "confounder_yearly.csv")

    # Use the H1 Triple specification — that one has all three interactions per year.
    triple = df[df["spec"] == "H1: Triple"].copy()
    triple["ci_lo"] = triple["coef"] - 1.96 * triple["se"]
    triple["ci_hi"] = triple["coef"] + 1.96 * triple["se"]

    series_map = {
        "eu_post2017:pci_std": ("AMLD x PCI", COLOR_AMLD, MARKER_AMLD, LINESTYLE_AMLD),
        "fatf_grey:pci_std":   ("FATF grey x PCI", COLOR_FATF, MARKER_FATF, LINESTYLE_FATF),
        "derisked:pci_std":    ("FDI / de-risking x PCI", COLOR_FDI, MARKER_FDI, LINESTYLE_FDI),
    }

    fig, axes = plt.subplots(1, 3, figsize=(10, 5), sharey=True)

    for ax, (interaction, (label, color, marker, ls)) in zip(axes, series_map.items()):
        sub = triple[triple["interaction"] == interaction].sort_values("year")
        years = sub["year"].to_numpy()
        ax.fill_between(years, sub["ci_lo"], sub["ci_hi"], color=color, alpha=0.20)
        ax.plot(years, sub["coef"], color=color, linestyle=ls, marker=marker,
                markersize=7, linewidth=2.0)
        ax.axhline(0, linestyle=":", color="grey", linewidth=0.8)
        ax.set_xticks(sorted(triple["year"].unique()))
        # Rotate year labels 90 degrees so they remain readable at the larger
        # rcParams font size (12pt tick labels).
        for tick in ax.get_xticklabels():
            tick.set_rotation(90)
        ax.set_xlabel("Year")
        # Sub-graph title (panel label) — clearly larger than tick labels.
        ax.text(0.05, 0.97, label, transform=ax.transAxes,
                ha="left", va="top", fontsize=15, fontweight="bold")

    axes[0].set_ylabel(r"$\hat{\gamma}$ (interaction with standardized PCI)")
    fig.tight_layout()
    save(fig, "fig_yearly_three_pronged.pdf")


# ---------------------------------------------------------------------------
# Figure 2: SOS top 20 composite (horizontal bars)
# ---------------------------------------------------------------------------
def fig_sos_top20_composite() -> None:
    df = pd.read_csv(TABLES / "09_sos_construction" / "sos_top20_composite.csv")
    df = df.sort_values("sos_composite", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    y = np.arange(len(df))
    ax.barh(y, df["sos_composite"], color=COLOR_FDI, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(df["iso3"])
    ax.set_xlabel("Composite Stablecoin Opportunity Score")
    ax.set_ylabel("")
    ax.margins(y=0.01)
    fig.tight_layout()
    save(fig, "fig_sos_top20_composite.pdf")


# ---------------------------------------------------------------------------
# Figure 3: SOS decomposition (FATF + FDI - AMLD adjustment)
# ---------------------------------------------------------------------------
def fig_sos_decomposition() -> None:
    df = pd.read_csv(TABLES / "09_sos_construction" / "sos_top20_composite.csv")
    df = df.sort_values("sos_composite", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    y = np.arange(len(df))
    fatf = df["sos_fatf"].to_numpy()
    fdi = df["sos_fdi"].to_numpy()
    amld = -df["sos_amld"].to_numpy()  # AMLD enters as a positive-side adjustment;
                                        # plotted negative to show what it deducts.

    ax.barh(y, fatf, color=COLOR_FATF, edgecolor="black", linewidth=0.3,
            label="FATF component", hatch="")
    ax.barh(y, fdi, left=fatf, color=COLOR_FDI, edgecolor="black", linewidth=0.3,
            label="FDI component", hatch="//")
    ax.barh(y, amld, color=COLOR_AMLD, edgecolor="black", linewidth=0.3,
            label="AMLD adjustment (negative)", hatch="..")

    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(df["iso3"])
    ax.set_xlabel("Component contribution to composite SOS")
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    save(fig, "fig_sos_decomposition.pdf")


# ---------------------------------------------------------------------------
# Figure 4: PCI distribution (standardized, HS4)
# ---------------------------------------------------------------------------
def fig_complexity_distribution() -> None:
    pci = pd.read_parquet(DATA_CLEAN / "complexity_pci.parquet")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(pci["pci_std"].dropna(), bins=30, color=COLOR_FDI,
            edgecolor="white", linewidth=0.5)
    ax.axvline(0, linestyle="--", color="grey", linewidth=0.8)
    ax.set_xlabel("Standardized Product Complexity Index (HS4)")
    ax.set_ylabel("Number of products")
    fig.tight_layout()
    save(fig, "fig_complexity_distribution.pdf")


# ---------------------------------------------------------------------------
# Figure 5: PCI vs greylisted-export-share (rules out a confounder)
# ---------------------------------------------------------------------------
def fig_pci_treatment_correlation() -> None:
    panel = pd.read_parquet(
        DATA_CLEAN / "panel_main_confounders.parquet",
        columns=["iso3_o", "iso3_d", "year", "trade_value", "pci_std", "fatf_grey"],
    ).rename(columns={"pf_cbr": "fdi_proxy"})  # convention: pf_cbr -> fdi_proxy

    # Restrict to a single representative year for the cross-section.
    yr = int(panel["year"].max())
    panel = panel[panel["year"] == yr]

    # Trade-weighted exporter PCI and FATF-greylist-partner export share.
    panel["w_pci"] = panel["trade_value"] * panel["pci_std"]
    grouped = panel.groupby("iso3_o", as_index=False).agg(
        total_trade=("trade_value", "sum"),
        total_w_pci=("w_pci", "sum"),
        total_grey=("trade_value", lambda s: s[panel.loc[s.index, "fatf_grey"] == 1].sum()),
    )
    grouped = grouped[grouped["total_trade"] > 0]
    grouped["mean_pci"] = grouped["total_w_pci"] / grouped["total_trade"]
    grouped["share_grey"] = grouped["total_grey"] / grouped["total_trade"]

    rho, _ = spearmanr(grouped["mean_pci"], grouped["share_grey"])

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(grouped["mean_pci"], grouped["share_grey"],
               s=22, alpha=0.6, color=COLOR_FATF, edgecolor="black", linewidth=0.3)
    ax.set_xlabel("Trade-weighted exporter PCI (standardized)")
    ax.set_ylabel("Share to FATF-greylisted partners")
    ax.text(0.05, 0.95, rf"Spearman $\rho$ = {rho:+.3f}",
            transform=ax.transAxes, ha="left", va="top")
    fig.tight_layout()
    save(fig, "fig_pci_treatment_correlation.pdf")


# ---------------------------------------------------------------------------
# Figure 6: Pairwise rank correlations (FDI / FATF / Composite)
# ---------------------------------------------------------------------------
def fig_ranking_correlations() -> None:
    sos = pd.read_parquet(DATA_CLEAN / "sos_country_composite.parquet")
    sos = sos[["rank_fdi", "rank_fatf", "rank_composite"]].dropna()

    pairs = [
        ("rank_fdi", "rank_fatf", "FDI rank", "FATF rank"),
        ("rank_fdi", "rank_composite", "FDI rank", "Composite rank"),
        ("rank_fatf", "rank_composite", "FATF rank", "Composite rank"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2))
    for ax, (xc, yc, xl, yl) in zip(axes, pairs):
        rho, _ = spearmanr(sos[xc], sos[yc])
        ax.scatter(sos[xc], sos[yc], s=14, alpha=0.5,
                   color=COLOR_FDI, edgecolor="black", linewidth=0.2)
        # 45 degree reference
        lo = min(sos[xc].min(), sos[yc].min())
        hi = max(sos[xc].max(), sos[yc].max())
        ax.plot([lo, hi], [lo, hi], linestyle=":", color="grey", linewidth=0.8)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.text(0.05, 0.95, rf"Spearman $\rho$ = {rho:+.3f}",
                transform=ax.transAxes, ha="left", va="top")

    fig.tight_layout()
    save(fig, "fig_ranking_correlations.pdf")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("13_figures.py -- generating publication figures")
    fig_yearly_three_pronged()
    fig_sos_top20_composite()
    fig_sos_decomposition()
    fig_complexity_distribution()
    fig_pci_treatment_correlation()
    fig_ranking_correlations()
    print("done.")


if __name__ == "__main__":
    main()
