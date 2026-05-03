"""
01b_build_hs2_skeleton.py — Build HS2 panel skeleton for code validation.

Reads baci_hs4_hs2_agg.parquet (already produced by 01_preprocess_baci.py),
identifies active pairs, and builds the zero-filled panel skeleton at HS2
(~33M cells — fits comfortably in memory).

Inputs:  data/cleaned/baci_hs4_hs2_agg.parquet
Outputs: data/cleaned/baci_hs2.parquet            (positive flows, renamed for pipeline)
         data/cleaned/panel_skeleton_hs2.parquet   (with zeros)
         data/cleaned/active_pairs.parquet         (overwrites — same pairs)
         data/cleaned/baci_diagnostics_hs2.json
"""

import json
import logging
import time
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"

SAMPLE_YEARS = list(range(2015, 2025))
MIN_YEARS_ACTIVE = 3
EXCLUDED_HS_CHAPTERS = ["93", "97", "98", "99"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    log.info("=" * 60)
    log.info("HS2 Panel Skeleton Builder (Validation Mode)")
    log.info("=" * 60)

    # Load HS2 aggregation
    log.info("Loading HS2 aggregated trade data...")
    baci_hs2 = pl.read_parquet(CLEAN_DIR / "baci_hs4_hs2_agg.parquet")
    log.info(f"  {len(baci_hs2):,} rows loaded")

    # Filter excluded chapters
    baci_hs2 = baci_hs2.filter(~pl.col("hs2").is_in(EXCLUDED_HS_CHAPTERS))
    log.info(f"  After excluding {EXCLUDED_HS_CHAPTERS}: {len(baci_hs2):,} rows")

    # Save as the "primary" trade file for the R pipeline
    # Rename hs2 -> hs4 so the R scripts work without modification
    baci_for_pipeline = baci_hs2.rename({"hs2": "hs4"})
    baci_for_pipeline.write_parquet(CLEAN_DIR / "baci_hs2.parquet")
    log.info(f"  Saved: baci_hs2.parquet ({len(baci_for_pipeline):,} rows)")

    # Identify active pairs
    log.info("Identifying active country pairs...")
    pair_years = (
        baci_hs2
        .filter(pl.col("trade_value") > 0)
        .group_by(["iso3_o", "iso3_d"])
        .agg(pl.col("year").n_unique().alias("n_years"))
        .filter(pl.col("n_years") >= MIN_YEARS_ACTIVE)
    )
    active_pairs = pair_years.select(["iso3_o", "iso3_d"])
    n_pairs = len(active_pairs)
    log.info(f"  Active pairs (>= {MIN_YEARS_ACTIVE} years): {n_pairs:,}")

    active_pairs.write_parquet(CLEAN_DIR / "active_pairs.parquet")

    # Get unique products and years
    products = baci_hs2.select("hs2").unique().sort("hs2")
    n_products = len(products)
    n_years = len(SAMPLE_YEARS)
    total_cells = n_pairs * n_products * n_years

    log.info(f"  Panel: {n_pairs:,} pairs x {n_products} products x {n_years} years = {total_cells:,} cells")

    # Build skeleton
    log.info("Building full panel skeleton...")
    t0 = time.time()

    years_df = pl.DataFrame({"year": SAMPLE_YEARS})
    skeleton = (
        active_pairs
        .join(products, how="cross")
        .join(years_df, how="cross")
    )
    elapsed = time.time() - t0
    log.info(f"  Skeleton: {len(skeleton):,} rows in {elapsed:.1f}s")

    # Merge actual trade values
    log.info("Merging trade values onto skeleton...")
    panel = skeleton.join(
        baci_hs2.select(["year", "iso3_o", "iso3_d", "hs2", "trade_value"]),
        on=["year", "iso3_o", "iso3_d", "hs2"],
        how="left",
    )
    panel = panel.with_columns(pl.col("trade_value").fill_null(0.0))

    n_positive = panel.filter(pl.col("trade_value") > 0).height
    zero_share = 1 - (n_positive / len(panel))
    log.info(f"  Zero share: {zero_share:.1%} ({n_positive:,} positive flows)")

    # Rename hs2 -> hs4 for pipeline compatibility
    panel = panel.rename({"hs2": "hs4"})

    # Add FE identifiers
    panel = panel.with_columns(
        (pl.col("iso3_o") + "_" + pl.col("iso3_d")).alias("pair"),
        (pl.col("iso3_o") + "_" + pl.col("year").cast(pl.Utf8)).alias("exporter_year"),
        (pl.col("iso3_d") + "_" + pl.col("year").cast(pl.Utf8)).alias("importer_year"),
    )

    # Save
    out_panel = CLEAN_DIR / "panel_skeleton.parquet"
    log.info(f"Saving panel skeleton: {out_panel}")
    panel.write_parquet(out_panel)

    # Diagnostics
    world_trade = (
        baci_hs2
        .group_by("year")
        .agg(pl.col("trade_value").sum().alias("total_1000usd"))
        .sort("year")
    )

    diag = {
        "mode": "HS2 validation",
        "baci_hs2_rows": len(baci_hs2),
        "panel_skeleton_rows": len(panel),
        "n_pairs": n_pairs,
        "n_products_hs2": n_products,
        "n_years": n_years,
        "n_exporters": baci_hs2.select("iso3_o").n_unique(),
        "n_importers": baci_hs2.select("iso3_d").n_unique(),
        "zero_share": round(zero_share, 4),
        "world_trade_by_year": {
            str(r["year"]): round(r["total_1000usd"] / 1e6, 2)
            for r in world_trade.iter_rows(named=True)
        },
    }

    diag_path = CLEAN_DIR / "baci_diagnostics_hs2.json"
    with open(diag_path, "w") as f:
        json.dump(diag, f, indent=2)

    log.info("\n" + "=" * 60)
    log.info("SUMMARY (HS2 Validation Mode)")
    log.info(f"  Products (HS2 chapters):  {n_products}")
    log.info(f"  Active pairs:             {n_pairs:,}")
    log.info(f"  Panel skeleton:           {len(panel):,} rows")
    log.info(f"  Zero share:               {zero_share:.1%}")
    log.info(f"  Parquet size:             {out_panel.stat().st_size / 1e6:.0f} MB")
    log.info("=" * 60)
    log.info("Done. Next: run R/01_complexity.R")


if __name__ == "__main__":
    main()
