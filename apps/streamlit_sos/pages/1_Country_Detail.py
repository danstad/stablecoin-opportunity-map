"""
1_Country_Detail.py -- Per-country deep dive.

Reads iso3 from st.session_state["selected_iso3"] (set by app.py sidebar)
or from the page's own selector (so the page works standalone).

Sections:
  1. Header (country name, composite SOS, rank, quadrant chip)
  2. KPI tile row (5 metrics)
  3. Three-pronged decomposition (FATF / FDI / AMLD vs sample median)
  4. Product treemap (HS section -> HS4)
  5. Products-at-risk table (15 rows)
  6. Diversification-opportunities table (15 rows)
  7. Top-5 derisked corridors (bar chart)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `components.*` importable when this page is loaded standalone via
# AppTest (which does not auto-prepend the project app dir).
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import pandas as pd
import streamlit as st

from components.charts import (
    corridor_bars,
    product_treemap,
    three_pronged_bars,
)
from components.loaders import (
    get_country_row,
    load_corridors,
    load_country_lookup,
    load_diversification_opps,
    load_products_at_risk,
    load_sos_country,
    load_sos_country_product,
)
from components.tables import (
    diversification_columns,
    products_at_risk_columns,
)
from components.theme import QUADRANT_COLORS, configure_page


configure_page(title="Country detail · Stablecoin Opportunity Map")

st.title("Country detail")


# --- Country selection -------------------------------------------------------

lookup = load_country_lookup()
sos_country = load_sos_country()

# Sidebar selector (works standalone if session-state is empty).
with st.sidebar:
    st.header("Country")
    options = ["—"] + lookup["name"].tolist()

    cur_iso = st.session_state.get("selected_iso3")
    default_idx = 0
    if cur_iso:
        cur_name = lookup.loc[lookup["iso3"] == cur_iso, "name"]
        if not cur_name.empty and cur_name.iloc[0] in options:
            default_idx = options.index(cur_name.iloc[0])

    pick = st.selectbox(
        "Pick a country",
        options=options,
        index=default_idx,
        key="detail_country_select",
    )
    if pick and pick != "—":
        new_iso = lookup.loc[lookup["name"] == pick, "iso3"].iloc[0]
        if new_iso != cur_iso:
            st.session_state["selected_iso3"] = new_iso
            st.rerun()

    st.divider()
    # page_link is only meaningful inside the multi-page runtime; guard so
    # AppTest harness (which lacks page metadata) doesn't crash.
    try:
        st.page_link("app.py", label="← Back to landing", icon="🌍")
        st.page_link("pages/2_Methodology.py", label="Methodology", icon="📘")
    except (KeyError, Exception):
        pass


iso3 = st.session_state.get("selected_iso3")
if not iso3 or iso3 == "—":
    st.info(
        "Pick a country from the sidebar to view its Stablecoin Opportunity "
        "decomposition."
    )
    st.stop()

row = get_country_row(iso3)
if row is None:
    st.error(f"No data found for ISO3 code '{iso3}'.")
    st.stop()

country_name = row.get("name", iso3)


# --- Header ------------------------------------------------------------------

quadrant = row.get("quadrant", "—")
quadrant_label = row.get("quadrant_label", quadrant if quadrant else "—")
quadrant_color = QUADRANT_COLORS.get(quadrant, "#888888") if isinstance(quadrant, str) else "#888888"
n_countries = sos_country["rank_composite"].notna().sum()

header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.header(f"{country_name}  ({iso3})")
    rank = row.get("rank_composite")
    rank_str = f"{int(rank)}" if pd.notna(rank) else "—"
    composite = row.get("sos_composite")
    composite_str = f"{composite:.2f}" if pd.notna(composite) else "—"
    st.markdown(
        f"**Composite SOS:** {composite_str} "
        f"&nbsp;·&nbsp; **Rank:** {rank_str} of {n_countries}"
    )
with header_col2:
    if isinstance(quadrant_label, str) and quadrant_label and quadrant_label != "—":
        st.markdown(
            f"<div style='display:inline-block;padding:6px 14px;"
            f"border-radius:14px;background:{quadrant_color};color:white;"
            f"font-weight:600;font-size:14px;margin-top:24px;'>"
            f"{quadrant_label}</div>",
            unsafe_allow_html=True,
        )


st.divider()


# --- KPI row -----------------------------------------------------------------

# Sample median for delta context.
median_row = sos_country.median(numeric_only=True)


def _safe_float(val):
    if val is None or pd.isna(val):
        return None
    return float(val)


kpi_cols = st.columns(5)
with kpi_cols[0]:
    val = _safe_float(row.get("sos_composite"))
    med = _safe_float(median_row.get("sos_composite"))
    delta = (val - med) if val is not None and med is not None else None
    st.metric(
        "Composite SOS",
        f"{val:.2f}" if val is not None else "—",
        delta=f"{delta:+.2f} vs median" if delta is not None else None,
    )
with kpi_cols[1]:
    val = _safe_float(row.get("sos_fatf"))
    st.metric("FATF SOS", f"{val:.2f}" if val is not None else "—")
with kpi_cols[2]:
    val = _safe_float(row.get("sos_fdi"))
    st.metric("FDI SOS", f"{val:.2f}" if val is not None else "—")
with kpi_cols[3]:
    val = _safe_float(row.get("sos_amld"))
    st.metric("AMLD adjustment", f"{val:.2f}" if val is not None else "—")
with kpi_cols[4]:
    val = _safe_float(row.get("trade_derisked"))
    st.metric(
        "Trade at risk (USD M)",
        f"{val:,.1f}" if val is not None else "—",
    )


# --- Three-pronged bars ------------------------------------------------------

st.subheader("Three-pronged decomposition")
st.caption(
    "Each component aggregates the country's exposure to one of the three "
    "natural experiments: FATF greylisting, FDI-derisked corridors, and "
    "EU AMLD harmonization. Sample median in grey for context."
)
bars_fig = three_pronged_bars(row, median_row)
st.plotly_chart(bars_fig, width="stretch", theme=None)


# --- Product treemap ---------------------------------------------------------

st.subheader("Product exposure treemap")
st.caption(
    "HS-section blocks group HS4 product categories. Color encodes the "
    "country-product composite SOS score; size encodes total trade in that "
    "HS4 category. Top 50 categories shown; the rest aggregated as 'Other'."
)
country_products = load_sos_country_product(iso3=iso3)
treemap_fig = product_treemap(country_products, top_n=50)
st.plotly_chart(treemap_fig, width="stretch", theme=None)


# --- Products at risk table --------------------------------------------------

st.subheader("Products at risk")
st.caption(
    "Top product categories where this country has revealed comparative "
    "advantage (RCA ≥ 1) and the SOS composite is in the upper range. "
    "These are the exports most exposed to payment-friction shocks."
)
par = load_products_at_risk()
par_country = par[par["iso3"] == iso3].sort_values("rank_within_country").head(15)
if par_country.empty:
    st.info("No products-at-risk data available for this country.")
else:
    par_country = par_country[
        ["rank_within_country", "hs4", "product_name",
         "sos_score", "pci_std", "rca", "trade_value"]
    ].reset_index(drop=True)
    st.dataframe(
        par_country,
        column_config=products_at_risk_columns(),
        hide_index=True,
        width="stretch",
        height=560,
    )


# --- Diversification opportunities ------------------------------------------

st.subheader("Diversification opportunities")
st.caption(
    "Products with high proximity (density) to the country's existing "
    "export basket and meaningful complexity, where RCA is currently below "
    "1. Higher diversification score = better-feasibility upgrades."
)
do = load_diversification_opps()
do_country = do[do["iso3"] == iso3].sort_values("rank_within_country").head(15)
if do_country.empty:
    st.info("No diversification-opportunity data available for this country.")
else:
    do_country = do_country[
        ["rank_within_country", "hs4", "product_name",
         "density", "pci_std", "rca", "diversification_score"]
    ].reset_index(drop=True)
    st.dataframe(
        do_country,
        column_config=diversification_columns(),
        hide_index=True,
        width="stretch",
        height=560,
    )


# --- Top-5 corridors ---------------------------------------------------------

st.subheader("Top-5 derisked corridors")
st.caption(
    "Bilateral partners contributing most to the country's SOS via the "
    "FDI-derisked channel. 'Derisked' flags corridors where bilateral FDI "
    "fell more than 50% from its 2015-2017 baseline."
)
corr = load_corridors()
corr_country = corr[corr["iso3"] == iso3].sort_values("rank_within_country").head(5)
corr_fig = corridor_bars(corr_country)
st.plotly_chart(corr_fig, width="stretch", theme=None)
