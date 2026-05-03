"""
19_regenerate_world_maps.py — Restore world choropleth maps.

Replaces the bar-chart fallback in:
  paper/figures/13_figures/world_heatmap_sos.pdf
  paper/figures/13_figures/world_derisking_exposure.pdf

with proper choropleths using geopandas + Natural Earth low-res country shapes.

Inputs:
  data/cleaned/sos_country_composite.parquet
  Natural Earth low-res (fetched from public URL on first run, cached locally)

Outputs:
  paper/figures/13_figures/world_heatmap_sos.pdf
  paper/figures/13_figures/world_derisking_exposure.pdf
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# Project paths
PROJECT  = Path(__file__).resolve().parents[2]
DATA_CLEAN = PROJECT / "data" / "cleaned"
FIGS = PROJECT / "paper" / "figures" / "13_figures"
FIGS.mkdir(parents=True, exist_ok=True)

# Local cache for the Natural Earth file
NE_DIR  = PROJECT / "data" / "raw" / "natural_earth"
NE_DIR.mkdir(parents=True, exist_ok=True)
NE_FILE = NE_DIR / "ne_110m_admin_0_countries.geojson"
NE_URL  = ("https://raw.githubusercontent.com/nvkelso/"
           "natural-earth-vector/master/geojson/"
           "ne_110m_admin_0_countries.geojson")


def get_world() -> gpd.GeoDataFrame:
    """Load Natural Earth low-res country polygons (download once, cache)."""
    if not NE_FILE.exists():
        print(f"  downloading {NE_URL.split('/')[-1]} ...", flush=True)
        urllib.request.urlretrieve(NE_URL, NE_FILE)
    world = gpd.read_file(NE_FILE)
    # Standardize ISO3 column name (Natural Earth uses ADM0_A3 or ISO_A3_EH)
    for cand in ("ISO_A3_EH", "ADM0_A3", "ISO_A3", "iso_a3"):
        if cand in world.columns:
            world = world.rename(columns={cand: "iso3"})
            break
    if "iso3" not in world.columns:
        raise RuntimeError(
            f"No ISO3 column in Natural Earth shapes; columns: {world.columns.tolist()}"
        )
    # Drop Antarctica for cleaner layout
    world = world[world["iso3"] != "ATA"].copy()
    return world[["iso3", "geometry"]]


def style() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 14,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "pdf.fonttype": 42,
    })


def make_choropleth(
    world: gpd.GeoDataFrame,
    values: pd.DataFrame,
    value_col: str,
    cmap: str,
    legend_label: str,
    out_path: Path,
) -> None:
    merged = world.merge(values, on="iso3", how="left")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    merged.plot(
        column=value_col,
        ax=ax,
        cmap=cmap,
        legend=True,
        legend_kwds={
            "label": legend_label,
            "orientation": "horizontal",
            "shrink": 0.55,
            "pad": 0.02,
            "aspect": 30,
        },
        missing_kwds={"color": "lightgray", "edgecolor": "white", "label": "no data"},
        edgecolor="white",
        linewidth=0.3,
    )
    ax.set_axis_off()
    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  saved {out_path.relative_to(PROJECT)}", flush=True)


def main() -> None:
    style()
    print("19_regenerate_world_maps.py", flush=True)
    print("  loading Natural Earth shapes ...", flush=True)
    world = get_world()
    print(f"  {len(world)} country polygons", flush=True)

    sos = pd.read_parquet(DATA_CLEAN / "sos_country_composite.parquet")

    # Composite SOS map
    make_choropleth(
        world,
        sos[["iso3", "sos_composite"]],
        value_col="sos_composite",
        cmap="viridis",
        legend_label="Composite Stablecoin Opportunity Score",
        out_path=FIGS / "world_heatmap_sos.pdf",
    )

    # De-risking exposure map (use n_derisked_partners; fall back if absent)
    if "n_derisked_partners" in sos.columns:
        derisk_col = "n_derisked_partners"
    elif "share_derisked" in sos.columns:
        derisk_col = "share_derisked"
    else:
        # Fall back to FDI-channel SOS, which is itself driven by derisking exposure
        derisk_col = "sos_fdi"

    make_choropleth(
        world,
        sos[["iso3", derisk_col]],
        value_col=derisk_col,
        cmap="magma_r",
        legend_label="De-risked bilateral corridors (count)" if derisk_col == "n_derisked_partners"
                    else ("Share of de-risked partners" if derisk_col == "share_derisked"
                          else "FDI-channel SOS"),
        out_path=FIGS / "world_derisking_exposure.pdf",
    )

    print("done.", flush=True)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
