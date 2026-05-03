"""
charts.py -- Plotly factories for the Stablecoin Opportunity Map app.

Per content-standards.md: no in-figure titles (st.subheader provides labels),
viridis palette for ordinal/sequential data, Set2 anchors for the three
treatments (FATF, AMLD, FDI), white background.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import (
    COLOR_AMLD,
    COLOR_FATF,
    COLOR_FDI,
    QUADRANT_COLORS,
    VIRIDIS,
)


def _base_layout(fig: go.Figure, height: int = 500) -> go.Figure:
    """Shared layout: white bg, serif-leaning font, no title."""
    fig.update_layout(
        height=height,
        title=None,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Georgia, 'Times New Roman', serif", size=13),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def world_choropleth(
    df: pd.DataFrame,
    value_col: str = "sos_composite",
    height: int = 500,
) -> go.Figure:
    """
    World choropleth of country-level SOS composite.

    df must contain iso3, name, value_col, rank_composite (for hover).
    """
    work = df.copy()
    if "rank_composite" not in work.columns:
        work["rank_composite"] = work[value_col].rank(ascending=False).astype(int)

    fig = px.choropleth(
        work,
        locations="iso3",
        locationmode="ISO-3",
        color=value_col,
        color_continuous_scale=VIRIDIS,
        hover_name="name",
        hover_data={
            "iso3": True,
            value_col: ":.2f",
            "rank_composite": True,
        },
        labels={
            value_col: "Composite SOS",
            "rank_composite": "Rank",
            "iso3": "ISO3",
        },
    )
    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True,
        coastlinecolor="#888888",
        showland=True,
        landcolor="#f5f5f5",
        showocean=True,
        oceancolor="white",
        showframe=False,
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Composite SOS", thickness=12, len=0.7),
    )
    return _base_layout(fig, height=height)


def quadrant_scatter(df: pd.DataFrame, height: int = 500) -> go.Figure:
    """
    Feasibility-quadrant scatter: capital openness vs infrastructure score,
    colored by quadrant, sized by composite SOS.
    """
    work = df.dropna(subset=["kaopen_score", "infrastructure_score"]).copy()
    work["sos_size"] = work["sos_composite"].clip(lower=0).fillna(0) + 1.0
    # Strip "Q1: " prefix from labels for cleaner legend; fall back if missing.
    if "quadrant_label" in work.columns:
        work["quadrant_short"] = work["quadrant_label"].fillna(work["quadrant"])
    else:
        work["quadrant_short"] = work["quadrant"]

    fig = px.scatter(
        work,
        x="kaopen_score",
        y="infrastructure_score",
        color="quadrant",
        size="sos_size",
        hover_name="name",
        hover_data={
            "iso3": True,
            "sos_composite": ":.2f",
            "kaopen_score": ":.2f",
            "infrastructure_score": ":.2f",
            "quadrant_short": True,
            "sos_size": False,
            "quadrant": False,
        },
        color_discrete_map=QUADRANT_COLORS,
        labels={
            "kaopen_score": "Capital openness (0-1)",
            "infrastructure_score": "Infrastructure / GDP per capita score",
            "quadrant": "Quadrant",
        },
        size_max=28,
    )
    # Median split lines.
    x_med = work["kaopen_score"].median()
    y_med = work["infrastructure_score"].median()
    fig.add_hline(y=y_med, line_dash="dash", line_color="#999999", opacity=0.7)
    fig.add_vline(x=x_med, line_dash="dash", line_color="#999999", opacity=0.7)
    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")))
    return _base_layout(fig, height=height)


def three_pronged_bars(
    country_row: pd.Series,
    sample_median_row: pd.Series,
) -> go.Figure:
    """
    Horizontal bar chart of FATF / FDI / AMLD components for the country
    alongside the sample median. Three groups (one per channel), two bars.
    """
    components = [
        ("FATF (greylist)", "sos_fatf", COLOR_FATF),
        ("FDI (derisked)", "sos_fdi", COLOR_FDI),
        ("AMLD (EU harmon.)", "sos_amld", COLOR_AMLD),
    ]
    rows = []
    for label, col, _color in components:
        rows.append({"channel": label, "series": "This country",
                     "value": float(country_row.get(col, 0.0) or 0.0)})
        rows.append({"channel": label, "series": "Sample median",
                     "value": float(sample_median_row.get(col, 0.0) or 0.0)})
    plot_df = pd.DataFrame(rows)

    fig = px.bar(
        plot_df,
        x="value",
        y="channel",
        color="series",
        barmode="group",
        orientation="h",
        color_discrete_map={
            "This country": "#440154",      # viridis dark purple
            "Sample median": "#bdbdbd",     # neutral grey
        },
        labels={"value": "Component score", "channel": "", "series": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1.0),
        yaxis=dict(autorange="reversed"),  # FATF on top
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eeeeee", zeroline=True,
                     zerolinecolor="#888888")
    return _base_layout(fig, height=320)


def product_treemap(df_country: pd.DataFrame, top_n: int = 50) -> go.Figure:
    """
    Treemap of country-product composite SOS exposure.

    df_country: rows from sos_country_product_composite filtered to one iso3.
    Path: HS section (hs4 first two digits, mapped to a section label) -> hs4.
    Color: sos_composite. Size: trade_total (fallback to abs(sos_composite)).
    """
    if df_country is None or df_country.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No product data available for this country.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#666666"),
        )
        return _base_layout(fig, height=400)

    work = df_country.copy()
    # Size column: prefer trade_total; fall back to absolute SOS for ranking.
    if "trade_total" in work.columns:
        work["size"] = work["trade_total"].clip(lower=0.0).fillna(0.0)
    else:
        work["size"] = work["sos_composite"].abs().fillna(0.0)

    # Top N by size, group rest into "Other".
    work = work.sort_values("size", ascending=False)
    if len(work) > top_n:
        top = work.head(top_n).copy()
        rest = work.iloc[top_n:].copy()
        other = pd.DataFrame([{
            "hs4": "Other",
            "size": rest["size"].sum(),
            "sos_composite": rest["sos_composite"].mean() if not rest.empty else 0.0,
        }])
        work = pd.concat([top, other], ignore_index=True, sort=False)

    work["hs4"] = work["hs4"].astype(str)
    work["section"] = work["hs4"].apply(_hs_section)
    work["product_label"] = work["hs4"].apply(lambda h: f"HS{h}" if h != "Other" else "Other")

    # Make sure size is strictly positive for treemap (zero -> tiny epsilon).
    work["size_plot"] = work["size"].clip(lower=1e-9)

    fig = px.treemap(
        work,
        path=["section", "product_label"],
        values="size_plot",
        color="sos_composite",
        color_continuous_scale=VIRIDIS,
        hover_data={
            "hs4": True,
            "sos_composite": ":.4f",
            "size": ":.1f",
            "size_plot": False,
            "section": False,
            "product_label": False,
        },
        labels={
            "sos_composite": "Composite SOS",
            "size": "Trade total",
        },
    )
    fig.update_traces(
        textinfo="label+value",
        textfont=dict(family="Georgia, 'Times New Roman', serif", size=12),
        marker=dict(cornerradius=2),
    )
    return _base_layout(fig, height=520)


def corridor_bars(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top-5 derisked corridors for one country."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No corridor data available for this country.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#666666"),
        )
        return _base_layout(fig, height=300)

    work = df.sort_values("contribution", ascending=True).copy()
    work["partner_display"] = work["partner_name"].fillna(work["partner_iso3"])

    fig = px.bar(
        work,
        x="contribution",
        y="partner_display",
        orientation="h",
        color="derisked",
        color_discrete_map={True: COLOR_FDI, False: "#cccccc"},
        hover_data={
            "partner_iso3": True,
            "trade_value": ":,.1f",
            "contribution": ":,.1f",
            "derisked": True,
            "partner_display": False,
        },
        labels={
            "contribution": "Corridor contribution to country SOS",
            "partner_display": "",
            "derisked": "FDI-derisked",
            "trade_value": "Trade value (USD M)",
        },
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1.0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eeeeee")
    return _base_layout(fig, height=300)


# --- helpers -----------------------------------------------------------------


# HS-section labels follow the WCO Harmonized System chapter ranges.
_HS_SECTIONS = [
    (1, 5,  "I. Live animals & products"),
    (6, 14, "II. Vegetable products"),
    (15, 15, "III. Fats & oils"),
    (16, 24, "IV. Food, beverages & tobacco"),
    (25, 27, "V. Mineral products"),
    (28, 38, "VI. Chemicals"),
    (39, 40, "VII. Plastics & rubber"),
    (41, 43, "VIII. Hides, skins & leather"),
    (44, 46, "IX. Wood & cork"),
    (47, 49, "X. Pulp, paper & printing"),
    (50, 63, "XI. Textiles & apparel"),
    (64, 67, "XII. Footwear & headgear"),
    (68, 70, "XIII. Stone, ceramics & glass"),
    (71, 71, "XIV. Precious metals & stones"),
    (72, 83, "XV. Base metals"),
    (84, 85, "XVI. Machinery & electronics"),
    (86, 89, "XVII. Transport equipment"),
    (90, 92, "XVIII. Optical & precision"),
    (93, 93, "XIX. Arms & ammunition"),
    (94, 96, "XX. Misc. manufactured"),
    (97, 99, "XXI. Art & antiques"),
]


def _hs_section(hs4: str) -> str:
    """Map an HS4 code (first two digits) to its section label."""
    if hs4 == "Other":
        return "Other"
    try:
        chap = int(str(hs4)[:2])
    except (TypeError, ValueError):
        return "Unclassified"
    for lo, hi, label in _HS_SECTIONS:
        if lo <= chap <= hi:
            return label
    return "Unclassified"
