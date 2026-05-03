"""
app.py -- Landing page for the Stablecoin Opportunity Map explorer.

Sections (top to bottom):
  1. Header + disclaimer
  2. Sidebar: country selector + top-5 mini-list
  3. World choropleth of composite SOS
  4. Top-20 ranking table
  5. Feasibility quadrant scatter

All data come from slim parquets in data/cleaned/webapp/ and the country-
level SOS file. No estimation runs in this app.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the app's directory is on sys.path so `components.*` imports work
# whether the script is launched via `streamlit run` (which prepends the
# script dir automatically) or via Streamlit's AppTest harness (which does not).
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

from components.charts import quadrant_scatter, world_choropleth
from components.loaders import (
    load_country_lookup,
    load_meta,
    load_sos_country,
)
from components.tables import top20_columns
from components.theme import configure_page


configure_page()


# --- Header ------------------------------------------------------------------

st.title("The Stablecoin Opportunity Map")
st.markdown(
    "**Where would alternative payment infrastructure unlock the most "
    "economically valuable trade?**"
)
st.caption(
    "Preliminary analysis using publicly available data. "
    "See the Methodology page for details and limitations."
)
st.divider()


# --- Sidebar -----------------------------------------------------------------

with st.sidebar:
    st.header("Explore by country")
    lookup = load_country_lookup()
    sos_country = load_sos_country()

    options = ["—"] + lookup["name"].tolist()
    default_idx = 0
    if "selected_iso3" in st.session_state and st.session_state["selected_iso3"]:
        cur_iso = st.session_state["selected_iso3"]
        cur_name = lookup.loc[lookup["iso3"] == cur_iso, "name"]
        if not cur_name.empty and cur_name.iloc[0] in options:
            default_idx = options.index(cur_name.iloc[0])

    pick = st.selectbox(
        "Pick a country to explore",
        options=options,
        index=default_idx,
        key="landing_country_select",
    )

    if pick and pick != "—":
        iso3 = lookup.loc[lookup["name"] == pick, "iso3"].iloc[0]
        st.session_state["selected_iso3"] = iso3
        st.switch_page("pages/1_Country_Detail.py")

    st.divider()
    st.subheader("Top 5 by composite SOS")
    top5 = (
        sos_country.dropna(subset=["sos_composite"])
        .sort_values("sos_composite", ascending=False)
        .head(5)
    )
    for _, row in top5.iterrows():
        if st.button(
            f"{row['name']} ({row['iso3']}) -- {row['sos_composite']:.2f}",
            key=f"top5_{row['iso3']}",
            width="stretch",
        ):
            st.session_state["selected_iso3"] = row["iso3"]
            st.switch_page("pages/1_Country_Detail.py")

    st.divider()
    meta = load_meta()
    if meta:
        st.caption(
            f"Build: {meta.get('build_date', 'n/a')} · "
            f"Latest year: {meta.get('year_latest', 'n/a')}"
        )


# --- Main body ---------------------------------------------------------------

st.subheader("Composite SOS across the world")
st.caption(
    "Higher values flag countries where complex-goods trade is most exposed "
    "to correspondent-banking frictions. Hover for country, score, and rank."
)
fig = world_choropleth(sos_country, value_col="sos_composite", height=520)
st.plotly_chart(fig, width="stretch", theme=None)


# Top-20 table
st.subheader("Top 20 by composite SOS")
top20 = (
    sos_country.dropna(subset=["sos_composite"])
    .sort_values("rank_composite")
    .head(20)
    [["rank_composite", "name", "iso3", "sos_composite",
      "sos_fatf", "sos_fdi", "sos_amld", "trade_derisked"]]
    .reset_index(drop=True)
)
st.dataframe(
    top20,
    column_config=top20_columns(),
    hide_index=True,
    width="stretch",
    height=560,
)


# Quadrant scatter
st.subheader("Feasibility quadrant")
st.caption(
    "Capital openness (Chinn-Ito) on x; infrastructure / GDP-per-capita "
    "score on y; bubble size = composite SOS. Q1 (top-right) flags "
    "actionable-now jurisdictions; Q4 (bottom-left) is structurally blocked."
)
quad_fig = quadrant_scatter(sos_country, height=520)
st.plotly_chart(quad_fig, width="stretch", theme=None)

st.divider()
st.markdown(
    "Pick a country in the sidebar to see its three-pronged decomposition, "
    "products at risk, and diversification opportunities. "
    "See **Methodology** for how the scores are built."
)
