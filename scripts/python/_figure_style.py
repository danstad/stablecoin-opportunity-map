"""
_figure_style.py -- Shared matplotlib rcParams for all paper figures.

Per content-standards.md (serif, no in-figure titles, colorblind-aware).
The font sizes are deliberately larger than matplotlib defaults so that
labels remain legible after the figure is shrunk to width=0.8\\textwidth
in the LaTeX paper.

Usage
-----
    from _figure_style import apply_style, COLORS
    apply_style()
"""
from __future__ import annotations

import matplotlib.pyplot as plt

# Colorblind-friendly Set2 palette anchors for the three treatments.
COLOR_AMLD = "#66c2a5"   # Set2 green
COLOR_FATF = "#fc8d62"   # Set2 orange
COLOR_FDI  = "#8da0cb"   # Set2 blue/purple

COLORS = {
    "amld": COLOR_AMLD,
    "fatf": COLOR_FATF,
    "fdi":  COLOR_FDI,
}

MARKERS = {"amld": "o", "fatf": "s", "fdi": "^"}
LINESTYLES = {"amld": "-", "fatf": "--", "fdi": "-."}


def apply_style() -> None:
    """Set publication rcParams: serif, larger fonts, vector-friendly PDF."""
    plt.rcParams.update({
        "font.family":     "serif",
        "font.size":       14,
        "axes.titlesize":  14,
        "axes.labelsize":  14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "figure.titlesize": 14,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype":  42,
    })
