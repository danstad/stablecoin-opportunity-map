"""
loaders.py -- Cached parquet readers for the Streamlit app.

All loaders use ``@st.cache_data`` because the slim webapp parquets are
immutable build artifacts. Paths are resolved relative to the project root
(three parents up from this file), so the app runs from any CWD.

Inputs read (read-only):
    data/cleaned/webapp/country_lookup.parquet
    data/cleaned/webapp/products_at_risk.parquet
    data/cleaned/webapp/diversification_opps.parquet
    data/cleaned/webapp/corridor_top5.parquet
    data/cleaned/webapp/webapp_meta.json
    data/cleaned/sos_country_composite.parquet
    data/cleaned/feasibility_quadrant.parquet
    data/cleaned/sos_country_product_composite.parquet (filtered subsets only)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


# Project root: apps/streamlit_sos/components/loaders.py -> three up.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
WEBAPP_DIR = PROJECT_ROOT / "data" / "cleaned" / "webapp"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"


@st.cache_data(show_spinner=False)
def load_country_lookup() -> pd.DataFrame:
    """iso3 -> name + region + has_sos flag (226 rows)."""
    df = pd.read_parquet(WEBAPP_DIR / "country_lookup.parquet")
    return df.sort_values("name").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_sos_country() -> pd.DataFrame:
    """
    Country-level SOS joined with feasibility-quadrant and country lookup.

    Returns one row per iso3 with composite SOS, three components, rank,
    quadrant classification, GDP and infrastructure scores.
    """
    sos = pd.read_parquet(CLEANED_DIR / "sos_country_composite.parquet")
    quad = pd.read_parquet(CLEANED_DIR / "feasibility_quadrant.parquet")
    lookup = load_country_lookup()

    # Drop overlapping cols from quad before merge to avoid _x/_y suffixes.
    overlap = [c for c in quad.columns if c in sos.columns and c != "iso3"]
    quad = quad.drop(columns=overlap)

    out = sos.merge(quad, on="iso3", how="left")
    out = out.merge(lookup[["iso3", "name", "region"]], on="iso3", how="left")
    return out


@st.cache_data(show_spinner=False)
def load_products_at_risk() -> pd.DataFrame:
    """Top-N products at risk per country (1,813 rows / 221 countries)."""
    return pd.read_parquet(WEBAPP_DIR / "products_at_risk.parquet")


@st.cache_data(show_spinner=False)
def load_diversification_opps() -> pd.DataFrame:
    """Top-N diversification opportunities per country (1,663 rows)."""
    return pd.read_parquet(WEBAPP_DIR / "diversification_opps.parquet")


@st.cache_data(show_spinner=False)
def load_corridors() -> pd.DataFrame:
    """Top-5 derisked corridors per country (1,130 rows)."""
    return pd.read_parquet(WEBAPP_DIR / "corridor_top5.parquet")


@st.cache_data(show_spinner=False)
def load_sos_country_product(iso3: str | None = None) -> pd.DataFrame:
    """
    Country-product SOS panel. Pass an iso3 to filter to a single country
    (recommended -- the full file is ~21k rows but slim, fits comfortably).

    Used by the country-detail treemap.
    """
    df = pd.read_parquet(CLEANED_DIR / "sos_country_product_composite.parquet")
    if iso3 is not None:
        df = df[df["iso3"] == iso3].copy()
    return df


@st.cache_data(show_spinner=False)
def load_meta() -> dict:
    """Build provenance from webapp_meta.json."""
    path = WEBAPP_DIR / "webapp_meta.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_resource(show_spinner=False)
def get_iso3_to_name() -> dict[str, str]:
    """Fast iso3 -> human-readable country name lookup."""
    lookup = load_country_lookup()
    return dict(zip(lookup["iso3"], lookup["name"]))


def get_country_row(iso3: str) -> pd.Series | None:
    """Return the SOS row for an iso3, or None if not found."""
    df = load_sos_country()
    sub = df[df["iso3"] == iso3]
    if sub.empty:
        return None
    return sub.iloc[0]


def get_paper_pdf_path() -> Path:
    """Return the path to the working-paper PDF (may not exist)."""
    return PROJECT_ROOT / "paper" / "main.pdf"
