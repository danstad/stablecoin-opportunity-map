"""
15_confounder_merge.py — Merge confounder and instrument variables into panel

MEMORY-EFFICIENT: Builds a slim lookup table first, then joins once.

Adds to panel_main.parquet:
  1. EU AMLD instrument: eu_corridor, eu_post2017, eu_post2020
  2. FATF greylist: fatf_grey (bilateral indicator)
  3. Confounders: diplo_disagreement, rta_coverage
  4. All × pci_std interaction terms

Inputs:  data/cleaned/panel_main.parquet
         data/raw/fatf_greylist_panel_2015_2023.csv
         data/raw/Gravity_csv_V202211/Gravity_V202211.csv
Outputs: data/cleaned/panel_main_confounders.parquet
"""

import os
import time
import gc
import polars as pl

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_CLEAN = os.path.join(PROJECT, "data", "cleaned")
DIR_RAW = os.path.join(PROJECT, "data", "raw")
PANEL_PATH = os.path.join(DIR_CLEAN, "panel_main.parquet")
FATF_PATH = os.path.join(DIR_RAW, "fatf_greylist_panel_2015_2023.csv")
GRAVITY_PATH = os.path.join(DIR_RAW, "Gravity_csv_V202211", "Gravity_V202211.csv")
OUTPUT_PATH = os.path.join(DIR_CLEAN, "panel_main_confounders.parquet")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# =========================================================================
# STEP 1: Build a slim bilateral-year lookup with all new variables
#         This is small (~500K rows max) and fits easily in memory
# =========================================================================

# --- 1a. CEPII Gravity ---
log("Loading CEPII Gravity (selected columns)...")
t0 = time.time()

gravity = pl.read_csv(
    GRAVITY_PATH,
    columns=["iso3_o", "iso3_d", "year", "eu_o", "eu_d",
             "diplo_disagreement", "rta_coverage"],
    schema_overrides={
        "eu_o": pl.Float64,
        "eu_d": pl.Float64,
        "diplo_disagreement": pl.Float64,
        "rta_coverage": pl.Float64,
    },
    null_values=["", "NA", "."],
)
log(f"  Gravity loaded: {gravity.height:,} rows in {time.time()-t0:.1f}s")

# Filter to sample years
gravity = gravity.filter(pl.col("year").is_in(list(range(2015, 2025))))
log(f"  After year filter: {gravity.height:,} rows")

# Forward-fill 2022-2023 from latest available year
max_gravity_year = gravity["year"].max()
log(f"  Max gravity year: {max_gravity_year}")

if max_gravity_year < 2023:
    log("  Forward-filling to 2023...")
    latest = gravity.filter(pl.col("year") == max_gravity_year)
    for fill_year in range(max_gravity_year + 1, 2025):
        filled = latest.with_columns(pl.lit(fill_year).cast(gravity["year"].dtype).alias("year"))
        gravity = pl.concat([gravity, filled])
    log(f"  After forward-fill: {gravity.height:,} rows")

gravity = gravity.unique(subset=["iso3_o", "iso3_d", "year"], keep="first")

# Construct EU corridor
gravity = gravity.with_columns([
    ((pl.col("eu_o").fill_null(0) > 0) | (pl.col("eu_d").fill_null(0) > 0))
    .cast(pl.Int8).alias("eu_corridor"),
    pl.col("rta_coverage").fill_null(0.0),
])

# Construct AMLD instruments
gravity = gravity.with_columns([
    ((pl.col("eu_corridor") == 1) & (pl.col("year") >= 2018))
    .cast(pl.Int8).alias("eu_post2017"),
    ((pl.col("eu_corridor") == 1) & (pl.col("year") >= 2020))
    .cast(pl.Int8).alias("eu_post2020"),
])

lookup = gravity.select([
    "iso3_o", "iso3_d", "year",
    "eu_corridor", "eu_post2017", "eu_post2020",
    "diplo_disagreement", "rta_coverage",
])

del gravity
gc.collect()
log(f"  Gravity lookup: {lookup.height:,} rows")

# --- 1b. FATF Greylist ---
log("Processing FATF greylist...")
fatf = pl.read_csv(FATF_PATH)
log(f"  FATF panel: {fatf.height} rows")

# Forward-fill 2024 from 2023 (panel data only goes to 2023)
fatf_max_yr = fatf["year"].max()
if fatf_max_yr < 2024:
    fatf_2024 = fatf.filter(pl.col("year") == fatf_max_yr).with_columns(
        pl.lit(2024).cast(fatf["year"].dtype).alias("year")
    )
    fatf = pl.concat([fatf, fatf_2024])
    log(f"  Extended FATF to 2024: {fatf.height} rows")

# Build country-year sets for origin and destination
fatf_set = fatf.filter(pl.col("fatf_greylist") == 1).select(["iso3", "year"])

# Merge FATF onto lookup (origin side)
lookup = lookup.join(
    fatf_set.select([pl.col("iso3").alias("iso3_o"), "year"]).with_columns(
        pl.lit(1).cast(pl.Int8).alias("fatf_o")
    ),
    on=["iso3_o", "year"], how="left"
)
# Merge FATF onto lookup (destination side)
lookup = lookup.join(
    fatf_set.select([pl.col("iso3").alias("iso3_d"), "year"]).with_columns(
        pl.lit(1).cast(pl.Int8).alias("fatf_d")
    ),
    on=["iso3_d", "year"], how="left"
)

# Bilateral FATF: either partner greylisted
lookup = lookup.with_columns([
    (pl.col("fatf_o").fill_null(0) | pl.col("fatf_d").fill_null(0))
    .cast(pl.Int8).alias("fatf_grey")
]).drop(["fatf_o", "fatf_d"])

n_fatf_corridors = lookup.filter(pl.col("fatf_grey") == 1).height
log(f"  FATF-affected corridor-years in lookup: {n_fatf_corridors:,}")

del fatf, fatf_set
gc.collect()

# =========================================================================
# STEP 2: Process panel_main year-by-year, join lookup, write yearly chunks
#         Uses scan_parquet for predicate pushdown to stay within 16GB RAM
# =========================================================================
log("\nProcessing panel year-by-year to conserve memory...")

years = list(range(2015, 2025))
total_written = 0
tmp_dir = os.path.join(DIR_CLEAN, "_tmp_confounders")
os.makedirs(tmp_dir, exist_ok=True)

for yr in years:
    log(f"\n--- Year {yr} ---")
    t1 = time.time()

    # Use scan_parquet with filter pushdown — only materializes rows for this year
    chunk = (
        pl.scan_parquet(PANEL_PATH)
        .filter(pl.col("year") == yr)
        .collect()
    )
    n_chunk = chunk.height
    log(f"  Loaded: {n_chunk:,} rows in {time.time()-t1:.1f}s")

    # Get lookup for this year
    lookup_yr = lookup.filter(pl.col("year") == yr)
    log(f"  Lookup rows for {yr}: {lookup_yr.height:,}")

    # Join
    chunk = chunk.join(lookup_yr, on=["iso3_o", "iso3_d", "year"], how="left")

    # Fill nulls for binary variables
    for col in ["eu_corridor", "eu_post2017", "eu_post2020", "fatf_grey"]:
        chunk = chunk.with_columns(pl.col(col).fill_null(0))

    # Construct interaction terms
    chunk = chunk.with_columns([
        (pl.col("fatf_grey").cast(pl.Float64) * pl.col("pci_std")).alias("fatf_grey_x_pci"),
        (pl.col("eu_post2017").cast(pl.Float64) * pl.col("pci_std")).alias("eu_post2017_x_pci"),
        (pl.col("eu_post2020").cast(pl.Float64) * pl.col("pci_std")).alias("eu_post2020_x_pci"),
        (pl.col("diplo_disagreement") * pl.col("pci_std")).alias("diplo_disagreement_x_pci"),
        (pl.col("rta_coverage") * pl.col("pci_std")).alias("rta_coverage_x_pci"),
        (pl.col("kaopen_bilateral") * pl.col("pci_std")).alias("kaopen_bilateral_x_pci"),
    ])

    # Stats for this year
    n_eu = (chunk["eu_post2017"] == 1).sum()
    n_fatf = (chunk["fatf_grey"] == 1).sum()
    log(f"  eu_post2017=1: {n_eu:,} ({100*n_eu/n_chunk:.1f}%)")
    log(f"  fatf_grey=1: {n_fatf:,} ({100*n_fatf/n_chunk:.1f}%)")

    # Write yearly chunk
    tmp_path = os.path.join(tmp_dir, f"year_{yr}.parquet")
    chunk.write_parquet(tmp_path)

    total_written += n_chunk
    del chunk, lookup_yr
    gc.collect()
    log(f"  Done in {time.time()-t1:.1f}s")

del lookup
gc.collect()

# =========================================================================
# STEP 3: Combine yearly files using lazy scan (no full materialization)
# =========================================================================
log("\nCombining yearly files...")
t2 = time.time()

# Use scan on glob pattern — polars handles this efficiently
tmp_files = [os.path.join(tmp_dir, f"year_{yr}.parquet") for yr in years]
combined = pl.concat([pl.scan_parquet(f) for f in tmp_files])

# Collect and write — this streams through without holding all in memory at once
combined.sink_parquet(OUTPUT_PATH)
log(f"  Written to {OUTPUT_PATH} in {time.time()-t2:.1f}s")

# Verify row count
final = pl.scan_parquet(OUTPUT_PATH)
final_count = final.select(pl.len()).collect().item()
log(f"  Final row count: {final_count:,} (expected ~33.3M)")

# Cleanup temp files
import shutil
shutil.rmtree(tmp_dir)
log("  Temp files cleaned up")

# =========================================================================
# STEP 4: Summary (using scan to avoid loading everything)
# =========================================================================
log("\n=== SUMMARY ===")
log(f"Total rows: {final_count:,}")

schema = pl.read_parquet_schema(OUTPUT_PATH)
log(f"Total columns: {len(schema)}")

new_cols = ["fatf_grey", "eu_corridor", "eu_post2017", "eu_post2020",
            "diplo_disagreement", "rta_coverage",
            "fatf_grey_x_pci", "eu_post2017_x_pci", "eu_post2020_x_pci",
            "diplo_disagreement_x_pci", "rta_coverage_x_pci", "kaopen_bilateral_x_pci"]

# Check non-null counts using scan
for col in new_cols:
    n_nonnull = (
        pl.scan_parquet(OUTPUT_PATH)
        .select(pl.col(col).is_not_null().sum())
        .collect()
        .item()
    )
    log(f"  {col}: {n_nonnull:,} non-null ({100*n_nonnull/final_count:.1f}%)")

log("Done.")
