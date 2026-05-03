"""
theme.py -- Page configuration and color constants.

Mirrors paper visual standards: serif fonts, viridis palette, no in-figure
titles. Colors anchored to the same Set2 palette used in the paper figures.
"""
from __future__ import annotations

import streamlit as st

# Set2 anchors per scripts/python/_figure_style.py (kept in sync with paper).
COLOR_AMLD = "#66c2a5"   # Set2 green   -- AMLD harmonization (friction down)
COLOR_FATF = "#fc8d62"   # Set2 orange  -- FATF greylist (friction up)
COLOR_FDI  = "#8da0cb"   # Set2 blue    -- FDI corridor drop (friction up)

# Composite uses viridis dark purple to match Streamlit primary color.
COLOR_COMPOSITE = "#440154"

# Quadrant palette (Q1 actionable green, Q4 blocked grey, etc.).
QUADRANT_COLORS = {
    "Q1": "#1b9e77",  # actionable now
    "Q2": "#d95f02",  # infrastructure gap
    "Q3": "#7570b3",  # capital-controls bound
    "Q4": "#7f7f7f",  # structurally blocked
}

VIRIDIS = "viridis"


def configure_page(
    title: str = "The Stablecoin Opportunity Map",
    icon: str = "🌍",
) -> None:
    """Apply standard page configuration. Call once at the top of every page."""
    st.set_page_config(
        layout="wide",
        page_title=title,
        page_icon=icon,
        initial_sidebar_state="expanded",
        menu_items={
            "About": (
                "Stablecoin Opportunity Map -- interactive companion to the "
                "working paper. Preliminary analysis using public data."
            ),
        },
    )
