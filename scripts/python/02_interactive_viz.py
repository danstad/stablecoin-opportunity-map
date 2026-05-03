"""
02_interactive_viz.py — Interactive Product Space + world heatmap

Creates interactive HTML visualizations using plotly and networkx.
Reads from Parquet outputs of the R pipeline.

Inputs:  data/cleaned/sos_country_product.parquet
         data/cleaned/sos_country.parquet
         data/cleaned/complexity_proximity.parquet
         data/cleaned/complexity_pci.parquet
         data/cleaned/feasibility_quadrant.parquet
Outputs: paper/figures/interactive/product_space.html
         paper/figures/interactive/world_heatmap.html
"""

import logging
from pathlib import Path

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"
FIG_DIR = PROJECT_ROOT / "paper" / "figures" / "interactive"
FIG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def build_product_space_network():
    """Build interactive Product Space colored by aggregate SOS."""
    log.info("Building interactive Product Space...")

    # Load proximity matrix
    prox_path = CLEAN_DIR / "complexity_proximity.parquet"
    if not prox_path.exists():
        log.warning("Proximity data not found — skipping Product Space")
        return

    prox = pl.read_parquet(prox_path)
    pci = pl.read_parquet(CLEAN_DIR / "complexity_pci.parquet")

    # Aggregate SOS by product
    sos_cp_path = CLEAN_DIR / "sos_country_product.parquet"
    if sos_cp_path.exists():
        sos_cp = pl.read_parquet(sos_cp_path)
        sos_product = (
            sos_cp
            .group_by("hs4")
            .agg(pl.col("sos_combined").sum().alias("sos_product"))
        )
    else:
        log.warning("SOS data not found — using PCI for coloring")
        sos_product = pci.select(["hs4", pl.col("pci_std").alias("sos_product")])

    # Build networkx graph
    G = nx.Graph()

    # Add nodes (products)
    pci_dict = dict(zip(pci["hs4"].to_list(), pci["pci_std"].to_list()))
    sos_dict = dict(zip(sos_product["hs4"].to_list(), sos_product["sos_product"].to_list()))

    for hs4 in pci["hs4"].to_list():
        G.add_node(hs4, pci=pci_dict.get(hs4, 0), sos=sos_dict.get(hs4, 0))

    # Add edges (proximity > threshold)
    prox_threshold = 0.3  # only show strong connections
    strong_prox = prox.filter(pl.col("proximity") > prox_threshold)
    for row in strong_prox.iter_rows(named=True):
        if row["hs4_a"] in G.nodes and row["hs4_b"] in G.nodes:
            G.add_edge(row["hs4_a"], row["hs4_b"], weight=row["proximity"])

    log.info(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Layout
    log.info("  Computing layout (spring)...")
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # Extract coordinates
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_sos = [G.nodes[n].get("sos", 0) for n in G.nodes()]
    node_pci = [G.nodes[n].get("pci", 0) for n in G.nodes()]
    node_text = [f"HS4: {n}<br>PCI: {G.nodes[n].get('pci', 0):.2f}<br>"
                 f"SOS: {G.nodes[n].get('sos', 0):.2f}"
                 for n in G.nodes()]

    # Edges
    edge_x, edge_y = [], []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Create plotly figure
    fig = go.Figure()

    # Edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.3, color="rgba(150,150,150,0.3)"),
        hoverinfo="none"
    ))

    # Nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers",
        marker=dict(
            size=6,
            color=node_sos,
            colorscale="Plasma",
            colorbar=dict(title="SOS"),
            line=dict(width=0.5, color="white")
        ),
        text=node_text,
        hoverinfo="text"
    ))

    fig.update_layout(
        title="Product Space — Colored by Stablecoin Opportunity Score",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=1200, height=800,
        template="plotly_white"
    )

    outpath = FIG_DIR / "product_space.html"
    fig.write_html(str(outpath))
    log.info(f"  Saved: {outpath}")


def build_world_heatmap():
    """Build interactive world choropleth of country-level SOS."""
    log.info("Building interactive world heatmap...")

    sos_path = CLEAN_DIR / "sos_country.parquet"
    if not sos_path.exists():
        log.warning("SOS country data not found — skipping heatmap")
        return

    sos = pl.read_parquet(sos_path).to_pandas()

    # Load feasibility quadrant if available
    quad_path = CLEAN_DIR / "feasibility_quadrant.parquet"
    if quad_path.exists():
        quad = pl.read_parquet(quad_path).to_pandas()
        sos = sos.merge(quad[["iso3", "quadrant"]], on="iso3", how="left")
        hover_data = ["sos_total", "rank_total", "quadrant"]
    else:
        hover_data = ["sos_total", "rank_total"]

    fig = px.choropleth(
        sos,
        locations="iso3",
        color="sos_total",
        hover_name="iso3",
        hover_data=hover_data,
        color_continuous_scale="Plasma_r",
        title="Stablecoin Opportunity Score by Country",
        labels={"sos_total": "SOS"},
    )
    fig.update_layout(
        width=1200, height=600,
        geo=dict(showframe=False, showcoastlines=True,
                 projection_type="natural earth"),
        template="plotly_white"
    )

    outpath = FIG_DIR / "world_heatmap.html"
    fig.write_html(str(outpath))
    log.info(f"  Saved: {outpath}")


def main():
    log.info("=" * 60)
    log.info("Interactive Visualizations")
    log.info("=" * 60)

    build_product_space_network()
    build_world_heatmap()

    log.info("Done. HTML files in: %s", FIG_DIR)


if __name__ == "__main__":
    main()
