"""
tables.py -- st.dataframe column_config builders.

Two factories matching the products-at-risk and diversification-opps schemas
in data/cleaned/webapp/. Used by app.py and pages/1_Country_Detail.py.
"""
from __future__ import annotations

import streamlit as st


def products_at_risk_columns() -> dict:
    """Column config for the products-at-risk dataframe."""
    return {
        "rank_within_country": st.column_config.NumberColumn(
            "Rank", format="%d", width="small",
            help="Within-country rank by SOS composite (1 = most exposed)",
        ),
        "hs4": st.column_config.TextColumn("HS4", width="small"),
        "product_name": st.column_config.TextColumn("Product", width="medium"),
        "sos_score": st.column_config.NumberColumn(
            "SOS score",
            format="%.4f",
            help="Country-product composite Stablecoin Opportunity Score",
        ),
        "pci_std": st.column_config.NumberColumn(
            "PCI (std)", format="%.2f",
            help="Standardized Product Complexity Index",
        ),
        "rca": st.column_config.NumberColumn(
            "RCA", format="%.2f",
            help="Revealed Comparative Advantage (>= 1 is competitive)",
        ),
        "trade_value": st.column_config.NumberColumn(
            "Trade (USD M)", format="%,.1f",
        ),
    }


def diversification_columns() -> dict:
    """Column config for the diversification-opportunities dataframe."""
    return {
        "rank_within_country": st.column_config.NumberColumn(
            "Rank", format="%d", width="small",
            help="Within-country rank by diversification score (density x complexity)",
        ),
        "hs4": st.column_config.TextColumn("HS4", width="small"),
        "product_name": st.column_config.TextColumn("Product", width="medium"),
        "density": st.column_config.NumberColumn(
            "Density", format="%.3f",
            help="Distance to country's existing export basket (higher = closer)",
        ),
        "pci_std": st.column_config.NumberColumn(
            "PCI (std)", format="%.2f",
            help="Standardized Product Complexity Index",
        ),
        "rca": st.column_config.NumberColumn(
            "RCA", format="%.2f",
            help="Revealed Comparative Advantage (< 1 here -- still nascent)",
        ),
        "diversification_score": st.column_config.NumberColumn(
            "Diversification score", format="%.3f",
            help="density x PCI -- combines feasibility and value",
        ),
    }


def top20_columns() -> dict:
    """Column config for the landing-page top-20 ranking table."""
    return {
        "rank_composite": st.column_config.NumberColumn(
            "Rank", format="%d", width="small",
        ),
        "name": st.column_config.TextColumn("Country", width="medium"),
        "iso3": st.column_config.TextColumn("ISO3", width="small"),
        "sos_composite": st.column_config.ProgressColumn(
            "Composite SOS", format="%.2f", min_value=0.0, max_value=12.0,
            help="Aggregate Stablecoin Opportunity Score across the three channels",
        ),
        "sos_fatf": st.column_config.NumberColumn("FATF SOS", format="%.2f"),
        "sos_fdi": st.column_config.NumberColumn("FDI SOS", format="%.2f"),
        "sos_amld": st.column_config.NumberColumn("AMLD adj.", format="%.2f"),
        "trade_derisked": st.column_config.NumberColumn(
            "Trade at risk (USD M)", format="%,.1f",
        ),
    }
