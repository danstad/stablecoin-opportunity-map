"""
05_extract_imf_dip.py — Extract bilateral FDI positions from IMF DIP/CDIS

Reads the 2.2GB IMF file in chunks, filters to the key slice
(All instruments, All entities, Net positions), and produces a clean
bilateral panel for use as a payment friction proxy.

Inputs:  data/raw/DEFAULT_INTEGRATION_IMF.STA_DIP_12.0.1.csv (2.2 GB)
Outputs: data/cleaned/imf_fdi_bilateral.parquet
         data/cleaned/imf_fdi_diagnostics.json
"""

import json
import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

INFILE = RAW_DIR / "DEFAULT_INTEGRATION_IMF.STA_DIP_12.0.1.csv"
TIME_COLS = [str(y) for y in range(2009, 2025)]
SAMPLE_YEARS = [str(y) for y in range(2015, 2024)]

# Columns we actually need (skip the 30+ metadata columns)
USE_COLS = [
    "COUNTRY", "COUNTERPART_COUNTRY", "DI_DIRECTION",
    "INSTR_ASSET", "DI_ENTITY", "DV_TYPE",
    "ACCOUNTING_ENTRY",
] + TIME_COLS


# Country name to ISO3 mapping for IMF names
# We'll use countrycode in R for the full mapping, but handle the
# most common edge cases here
MANUAL_ISO3 = {
    "Korea, Republic of": "KOR",
    "Korea, Democratic People's Republic of": "PRK",
    "Hong Kong Special Administrative Region, People's Republic of China": "HKG",
    "Macao Special Administrative Region, People's Republic of China": "MAC",
    "Taiwan Province of China": "TWN",
    "Iran, Islamic Republic of": "IRN",
    "Lao People's Democratic Republic": "LAO",
    "Venezuela, Republica Bolivariana de": "VEN",
    "Bolivia, Plurinational State of": "BOL",
    "Moldova, Republic of": "MDA",
    "North Macedonia, Republic of": "MKD",
    "Congo, Democratic Republic of the": "COD",
    "Congo, Republic of": "COG",
    "Tanzania, United Republic of": "TZA",
    "Micronesia, Federated States of": "FSM",
    "Estonia, Republic of": "EST",
    "Lithuania, Republic of": "LTU",
    "Latvia, Republic of": "LVA",
    "Slovak Republic": "SVK",
    "Czech Republic": "CZE",
    "Türkiye": "TUR",
    "T\u00fcrkiye": "TUR",
    "Côte d'Ivoire": "CIV",
    "C\u00f4te d'Ivoire": "CIV",
    "São Tomé and Príncipe, Democratic Republic of": "STP",
    "Timor-Leste, Democratic Republic of": "TLS",
    "West Bank and Gaza Strip": "PSE",
    "Kosovo, Republic of": "XKX",
    "Curaçao, Kingdom of the Netherlands": "CUW",
    "Sint Maarten, Kingdom of the Netherlands": "SXM",
    "Aruba, Kingdom of the Netherlands": "ABW",
    "World": "WLD",
    "South Africa": "ZAF",
    "Eswatini": "SWZ",
    "Eswatini, Kingdom of": "SWZ",
    "Cabo Verde": "CPV",
    "Brunei Darussalam": "BRN",
    "Syrian Arab Republic": "SYR",
    "Viet Nam": "VNM",
    "Palestine, State of": "PSE",
}


def name_to_iso3(name: str) -> str | None:
    """Convert IMF country name to ISO3. Returns None for aggregates."""
    if pd.isna(name):
        return None

    # Check manual mapping first
    if name in MANUAL_ISO3:
        return MANUAL_ISO3[name]

    # Skip regional aggregates
    aggregates = [
        "World", "Africa", "Asia", "Europe", "Americas",
        "East Asia", "South Asia", "Southeast Asia", "West Asia",
        "Central Asia", "Eastern Europe", "Western Europe",
        "Northern America", "Central America", "South America",
        "Caribbean", "Oceania and Polar Regions", "Middle East",
        "Sub-Saharan Africa", "North Africa",
        "Not specified (including confidential)",
        "International organisations",
        "Special Categories",
    ]
    for agg in aggregates:
        if agg.lower() in name.lower():
            return None

    # Try pycountry-style lookup
    try:
        import pycountry
        result = pycountry.countries.search_fuzzy(name)
        if result:
            return result[0].alpha_3
    except (ImportError, LookupError):
        pass

    # Simple heuristic: try common patterns
    # "Country, Republic of" -> try "Country"
    simple = name.split(",")[0].strip()
    try:
        import pycountry
        result = pycountry.countries.search_fuzzy(simple)
        if result:
            return result[0].alpha_3
    except (ImportError, LookupError):
        pass

    return None


def main():
    log.info("=" * 60)
    log.info("IMF DIP/CDIS Bilateral FDI Extraction")
    log.info(f"Input: {INFILE} ({INFILE.stat().st_size / 1e9:.1f} GB)")
    log.info("=" * 60)

    # ---------------------------------------------------------------
    # 1. Read in chunks, filter to key slice
    # ---------------------------------------------------------------
    log.info("Reading CSV in chunks (filtering to key slice)...")

    # Key slice:
    # - INSTR_ASSET = "All financial instruments" (broadest)
    # - DI_ENTITY = "All entities"
    # - ACCOUNTING_ENTRY = "Net (assets less liabilities)" for outward,
    #                      "Net (liabilities less assets)" for inward
    # We keep both Reported and Derived data for maximum coverage

    chunks = []
    chunk_size = 200_000
    total_read = 0
    total_kept = 0

    for chunk in pd.read_csv(
        INFILE,
        chunksize=chunk_size,
        encoding="utf-8-sig",
        low_memory=False,
        usecols=USE_COLS,
    ):
        total_read += len(chunk)

        # Filter to key slice
        filtered = chunk[
            (chunk["INSTR_ASSET"] == "All financial instruments") &
            (chunk["DI_ENTITY"] == "All entities")
        ]
        if len(filtered) > 0:
            chunks.append(filtered)
            total_kept += len(filtered)

        if total_read % 1_000_000 == 0:
            log.info(f"  Read {total_read:,} rows, kept {total_kept:,}")

    log.info(f"  Total read: {total_read:,}, kept: {total_kept:,}")

    df = pd.concat(chunks, ignore_index=True)
    log.info(f"  Combined: {len(df):,} rows")

    # ---------------------------------------------------------------
    # 2. Melt to long format (year as rows)
    # ---------------------------------------------------------------
    log.info("Melting to long format...")

    available_time = [c for c in TIME_COLS if c in df.columns]
    id_cols = ["COUNTRY", "COUNTERPART_COUNTRY", "DI_DIRECTION",
               "DV_TYPE", "ACCOUNTING_ENTRY"]

    long = df.melt(
        id_vars=id_cols,
        value_vars=available_time,
        var_name="year",
        value_name="fdi_usd_mn",
    )
    long["year"] = long["year"].astype(int)
    long["fdi_usd_mn"] = pd.to_numeric(long["fdi_usd_mn"], errors="coerce")

    # Drop nulls
    long = long.dropna(subset=["fdi_usd_mn"])
    log.info(f"  Long format: {len(long):,} obs (non-null FDI values)")

    # ---------------------------------------------------------------
    # 3. Map country names to ISO3
    # ---------------------------------------------------------------
    log.info("Mapping country names to ISO3...")

    all_names = set(long["COUNTRY"].unique()) | set(long["COUNTERPART_COUNTRY"].unique())
    name_map = {}
    unmapped = []
    for name in all_names:
        iso3 = name_to_iso3(name)
        if iso3:
            name_map[name] = iso3
        else:
            unmapped.append(name)

    log.info(f"  Mapped: {len(name_map)} country names to ISO3")
    if unmapped:
        log.info(f"  Unmapped (aggregates/unknown): {len(unmapped)}")
        for u in sorted(unmapped)[:20]:
            log.info(f"    {u}")

    long["iso3_reporter"] = long["COUNTRY"].map(name_map)
    long["iso3_counterpart"] = long["COUNTERPART_COUNTRY"].map(name_map)

    # Drop rows where either country couldn't be mapped
    long = long.dropna(subset=["iso3_reporter", "iso3_counterpart"])
    log.info(f"  After ISO3 mapping: {len(long):,} obs")

    # ---------------------------------------------------------------
    # 4. Create bilateral FDI panel
    # ---------------------------------------------------------------
    log.info("Creating bilateral FDI panel...")

    # Strategy: for each (reporter, counterpart, year), we want ONE
    # number capturing the financial linkage.
    #
    # Take the NET position (outward net = assets - liabilities).
    # Use absolute value since we care about linkage depth, not direction.
    # Prefer reported data; fill gaps with derived data.

    # Separate reported vs derived
    reported = long[long["DV_TYPE"] == "Reported official data"].copy()
    derived = long[long["DV_TYPE"] == "Derived using counterparty information"].copy()

    # For reported: take outward net position (most commonly reported)
    reported_out = reported[reported["DI_DIRECTION"] == "Outward"]
    reported_in = reported[reported["DI_DIRECTION"] == "Inward"]

    # Aggregate: for each (reporter, counterpart, year), take outward net if available
    panel_reported = (
        reported_out
        .groupby(["iso3_reporter", "iso3_counterpart", "year"], as_index=False)
        ["fdi_usd_mn"].first()
        .rename(columns={"fdi_usd_mn": "fdi_outward_net"})
    )
    panel_reported["data_source"] = "reported"

    # For derived: same structure
    derived_out = derived[derived["DI_DIRECTION"] == "Outward"]
    panel_derived = (
        derived_out
        .groupby(["iso3_reporter", "iso3_counterpart", "year"], as_index=False)
        ["fdi_usd_mn"].first()
        .rename(columns={"fdi_usd_mn": "fdi_outward_net"})
    )
    panel_derived["data_source"] = "derived"

    # Combine: reported preferred, derived fills gaps
    panel = pd.concat([panel_reported, panel_derived], ignore_index=True)
    panel = panel.sort_values(
        ["iso3_reporter", "iso3_counterpart", "year", "data_source"]
    )
    # Keep first (reported takes priority over derived)
    panel = panel.drop_duplicates(
        subset=["iso3_reporter", "iso3_counterpart", "year"],
        keep="first",
    )

    log.info(f"  Panel: {len(panel):,} obs")
    log.info(f"  Reporters: {panel['iso3_reporter'].nunique()}")
    log.info(f"  Counterparts: {panel['iso3_counterpart'].nunique()}")
    log.info(f"  Unique pairs: {panel.groupby(['iso3_reporter', 'iso3_counterpart']).ngroups:,}")

    # ---------------------------------------------------------------
    # 5. Construct bilateral symmetric FDI linkage
    # ---------------------------------------------------------------
    log.info("Constructing symmetric bilateral FDI linkage...")

    # For friction purposes, we want a symmetric measure:
    # fdi_bilateral(A,B) = |FDI_A->B| + |FDI_B->A|
    # This captures total financial linkage regardless of direction

    panel["fdi_abs"] = panel["fdi_outward_net"].abs()

    # Create mirror: swap reporter/counterpart
    mirror = panel[["iso3_counterpart", "iso3_reporter", "year", "fdi_abs"]].copy()
    mirror.columns = ["iso3_reporter", "iso3_counterpart", "year", "fdi_abs_mirror"]

    # Merge original with mirror
    bilateral = panel[["iso3_reporter", "iso3_counterpart", "year", "fdi_abs", "data_source"]].merge(
        mirror,
        on=["iso3_reporter", "iso3_counterpart", "year"],
        how="outer",
    )

    # Symmetric linkage = sum of both directions (use max of available)
    bilateral["fdi_bilateral"] = bilateral[["fdi_abs", "fdi_abs_mirror"]].sum(axis=1)

    # Also keep the max (less sensitive to one-sided reporting)
    bilateral["fdi_max_direction"] = bilateral[["fdi_abs", "fdi_abs_mirror"]].max(axis=1)

    # Construct friction variable: higher = more friction (less FDI)
    import numpy as np
    bilateral["pf_fdi"] = -np.log(1 + bilateral["fdi_bilateral"])
    bilateral["pf_fdi_max"] = -np.log(1 + bilateral["fdi_max_direction"])

    # Rename for consistency with our pipeline
    bilateral = bilateral.rename(columns={
        "iso3_reporter": "iso3_o",
        "iso3_counterpart": "iso3_d",
    })

    # Filter to sample years
    bilateral_sample = bilateral[
        bilateral["year"].isin(range(2015, 2024))
    ].copy()

    # Drop self-pairs and WLD
    bilateral_sample = bilateral_sample[
        (bilateral_sample["iso3_o"] != bilateral_sample["iso3_d"]) &
        (bilateral_sample["iso3_o"] != "WLD") &
        (bilateral_sample["iso3_d"] != "WLD")
    ]

    # Sort
    bilateral_sample = bilateral_sample.sort_values(
        ["iso3_o", "iso3_d", "year"]
    ).reset_index(drop=True)

    # Select final columns
    output_cols = [
        "iso3_o", "iso3_d", "year",
        "fdi_bilateral", "fdi_max_direction",
        "pf_fdi", "pf_fdi_max", "data_source",
    ]
    bilateral_final = bilateral_sample[output_cols]

    log.info(f"  Final bilateral panel: {len(bilateral_final):,} obs")
    log.info(f"  Country pairs: {bilateral_final.groupby(['iso3_o', 'iso3_d']).ngroups:,}")
    log.info(f"  Reporters: {bilateral_final['iso3_o'].nunique()}")
    log.info(f"  Counterparts: {bilateral_final['iso3_d'].nunique()}")

    # ---------------------------------------------------------------
    # 6. Save
    # ---------------------------------------------------------------
    outpath = CLEAN_DIR / "imf_fdi_bilateral.parquet"
    table = pa.Table.from_pandas(bilateral_final)
    pq.write_table(table, outpath)
    log.info(f"\nSaved: {outpath}")

    # ---------------------------------------------------------------
    # 7. Diagnostics
    # ---------------------------------------------------------------
    years_coverage = bilateral_final.groupby("year").agg(
        n_pairs=("iso3_o", "count"),
        n_reporters=("iso3_o", "nunique"),
        mean_fdi=("fdi_bilateral", "mean"),
        median_fdi=("fdi_bilateral", "median"),
    ).reset_index()

    diag = {
        "total_obs": len(bilateral_final),
        "n_reporters": int(bilateral_final["iso3_o"].nunique()),
        "n_counterparts": int(bilateral_final["iso3_d"].nunique()),
        "n_pairs": int(bilateral_final.groupby(["iso3_o", "iso3_d"]).ngroups),
        "years": sorted(bilateral_final["year"].unique().tolist()),
        "data_source_split": bilateral_final["data_source"].value_counts().to_dict(),
        "coverage_by_year": {
            str(row["year"]): {
                "n_pairs": int(row["n_pairs"]),
                "n_reporters": int(row["n_reporters"]),
            }
            for _, row in years_coverage.iterrows()
        },
    }

    diag_path = CLEAN_DIR / "imf_fdi_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diag, f, indent=2)
    log.info(f"Diagnostics: {diag_path}")

    # Print summary
    log.info("\n" + "=" * 60)
    log.info("COVERAGE BY YEAR")
    log.info(f"{'Year':>6} {'Pairs':>8} {'Reporters':>10}")
    log.info("-" * 28)
    for _, row in years_coverage.iterrows():
        log.info(f"  {int(row['year']):>4}   {int(row['n_pairs']):>6,}    {int(row['n_reporters']):>6}")

    log.info(f"\nData source: {diag['data_source_split']}")
    log.info("=" * 60)
    log.info("Done.")


if __name__ == "__main__":
    main()
