"""
04_extract_cpmi.py — Extract usable series from CPMI Red Book datasets

Extracts country-level payment infrastructure indicators from 8 CPMI files
and combines into a single clean panel.

Inputs:  data/raw/WS_CPMI_*.csv (8 files)
Outputs: data/cleaned/cpmi_panel.parquet          (country x year, all indicators)
         data/cleaned/cpmi_panel_diagnostics.json  (coverage stats)
"""

import json
import logging
from pathlib import Path

import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TIME_COLS = [str(y) for y in range(2012, 2024)]


def read_cpmi(filename: str) -> pd.DataFrame:
    """Read a CPMI CSV and return as DataFrame."""
    path = RAW_DIR / filename
    df = pd.read_csv(path, low_memory=False)
    log.info(f"  Loaded {filename}: {df.shape[0]} rows")
    return df


def melt_time(df: pd.DataFrame, id_cols: list, value_name: str) -> pd.DataFrame:
    """Melt wide time columns (2012-2023) into long format."""
    available_time = [c for c in TIME_COLS if c in df.columns]
    melted = df[id_cols + available_time].melt(
        id_vars=id_cols, var_name="year", value_name=value_name
    )
    melted["year"] = melted["year"].astype(int)
    melted[value_name] = pd.to_numeric(melted[value_name], errors="coerce")
    return melted.dropna(subset=[value_name])


# ===================================================================
# 1. SWIFT Messages (from WS_CPMI_SYSTEMS)
# ===================================================================
def extract_swift_messages() -> pd.DataFrame:
    """Extract SWIFT message volumes by country and category."""
    log.info("Extracting SWIFT messages...")
    df = read_cpmi("WS_CPMI_SYSTEMS_csv_col.csv")

    swift = df[df["SYSTEM_TYPE"] == "S"].copy()

    # Key instrument types:
    # MN = Messages sent, all
    # MQ = Messages received, all
    # MO = Messages sent, category I (customer payments — trade relevant)
    # MR = Messages received, category I
    # MP = Messages sent, category II (financial institution)
    # MS = Messages received, category II
    # MM = Domestic messages

    results = []

    for code, col_name in [
        ("MN", "swift_msg_sent_all"),
        ("MQ", "swift_msg_recv_all"),
        ("MO", "swift_msg_sent_cat1"),
        ("MR", "swift_msg_recv_cat1"),
        ("MP", "swift_msg_sent_cat2"),
        ("MS", "swift_msg_recv_cat2"),
        ("MM", "swift_msg_domestic"),
    ]:
        subset = swift[swift["INSTRUMENT_TYPE"] == code]
        if len(subset) > 0:
            melted = melt_time(subset, ["REP_CTY"], col_name)
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            results.append(melted)
            log.info(f"    {col_name}: {len(melted)} obs, {melted['iso2'].nunique()} countries")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")

        # Derived: total messages = sent + received
        if "swift_msg_sent_all" in merged.columns and "swift_msg_recv_all" in merged.columns:
            merged["swift_msg_total"] = (
                merged["swift_msg_sent_all"].fillna(0) +
                merged["swift_msg_recv_all"].fillna(0)
            )

        # Derived: cat1 share (customer payments / total) — higher = more trade-oriented
        if "swift_msg_sent_cat1" in merged.columns and "swift_msg_sent_all" in merged.columns:
            merged["swift_cat1_share"] = (
                merged["swift_msg_sent_cat1"] / merged["swift_msg_sent_all"]
            )

        return merged

    return pd.DataFrame()


# ===================================================================
# 2. SWIFT Participants (from WS_CPMI_PARTICIP)
# ===================================================================
def extract_swift_participants() -> pd.DataFrame:
    """Extract number of SWIFT participants (members) per country."""
    log.info("Extracting SWIFT participants...")
    df = read_cpmi("WS_CPMI_PARTICIP_csv_col.csv")

    swift_part = df[df["SYSTEM_TYPE"] == "S"].copy()

    results = []

    for code, col_name in [
        ("A", "swift_participants_all"),
        ("0", "swift_members"),
        ("1", "swift_submembers"),
    ]:
        subset = swift_part[swift_part["PART_TYPE"] == code]
        if len(subset) > 0:
            melted = melt_time(subset, ["REP_CTY"], col_name)
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            results.append(melted)
            log.info(f"    {col_name}: {len(melted)} obs")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")
        return merged

    return pd.DataFrame()


# ===================================================================
# 3. Banking Institutions (from WS_CPMI_INSTITUT)
# ===================================================================
def extract_institutions() -> pd.DataFrame:
    """Extract banking institution counts: total banks, foreign banks, e-money."""
    log.info("Extracting banking institutions...")
    df = read_cpmi("WS_CPMI_INSTITUT_csv_col.csv")

    # Filter to Number (not Value) and key institution/indicator combos
    df_num = df[df["MEASURE"] == "N"].copy()

    results = []

    # Total banks - Institutions count
    banks_inst = df_num[
        (df_num["INSTITUTION_TYPE"] == "BA") & (df_num["INDICATOR"] == "A")
    ]
    if len(banks_inst) > 0:
        melted = melt_time(banks_inst, ["REP_CTY"], "n_banks_total")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_banks_total: {len(melted)} obs")

    # Foreign banks
    foreign = df_num[
        (df_num["INSTITUTION_TYPE"] == "FB") & (df_num["INDICATOR"] == "A")
    ]
    if len(foreign) > 0:
        melted = melt_time(foreign, ["REP_CTY"], "n_foreign_banks")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_foreign_banks: {len(melted)} obs")

    # Bank branches
    branches = df_num[
        (df_num["INSTITUTION_TYPE"] == "BA") & (df_num["INDICATOR"] == "C")
    ]
    if len(branches) > 0:
        melted = melt_time(branches, ["REP_CTY"], "n_bank_branches")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_bank_branches: {len(melted)} obs")

    # E-money issuers (all)
    emoney = df_num[
        (df_num["INSTITUTION_TYPE"] == "EA") & (df_num["INDICATOR"] == "A")
    ]
    if len(emoney) > 0:
        melted = melt_time(emoney, ["REP_CTY"], "n_emoney_issuers")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_emoney_issuers: {len(melted)} obs")

    # Non-bank e-money issuers
    emoney_nb = df_num[
        (df_num["INSTITUTION_TYPE"] == "EN") & (df_num["INDICATOR"] == "A")
    ]
    if len(emoney_nb) > 0:
        melted = melt_time(emoney_nb, ["REP_CTY"], "n_emoney_nonbanks")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_emoney_nonbanks: {len(melted)} obs")

    # All institutions
    all_inst = df_num[
        (df_num["INSTITUTION_TYPE"] == "IA") & (df_num["INDICATOR"] == "A")
    ]
    if len(all_inst) > 0:
        melted = melt_time(all_inst, ["REP_CTY"], "n_institutions_all")
        melted = melted.rename(columns={"REP_CTY": "iso2"})
        results.append(melted)
        log.info(f"    n_institutions_all: {len(melted)} obs")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")

        # Derived: foreign bank share
        if "n_foreign_banks" in merged.columns and "n_banks_total" in merged.columns:
            merged["foreign_bank_share"] = (
                merged["n_foreign_banks"] / merged["n_banks_total"]
            )

        return merged

    return pd.DataFrame()


# ===================================================================
# 4. Fast Payments Adoption (from WS_CPMI_CT1)
# ===================================================================
def extract_fast_payments() -> pd.DataFrame:
    """Extract fast payment transaction volumes as a modernity indicator."""
    log.info("Extracting fast payments & cashless indicators...")
    df = read_cpmi("WS_CPMI_CT1_csv_col.csv")

    results = []

    # Fast payments — Number of transactions
    fast = df[
        (df["INDICATOR_CT"] == "N") &  # Fast payments indicator
        (df["MEASURE"] == "N")  # Number (not value)
    ]
    if len(fast) > 0:
        # Get the "all instruments" rows
        fast_all = fast[fast["INSTRUMENT_TYPE_CT"].isin(["A", "T"])]  # All or Total
        if len(fast_all) > 0:
            melted = melt_time(fast_all, ["REP_CTY"], "fast_payment_txns")
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            # Take max per country-year (avoid duplicates from different instrument types)
            melted = melted.groupby(["iso2", "year"], as_index=False)["fast_payment_txns"].max()
            results.append(melted)
            log.info(f"    fast_payment_txns: {len(melted)} obs")

    # Total cashless payments — Number
    cashless = df[
        (df["INDICATOR_CT"] == "M") &  # Cashless payments
        (df["MEASURE"] == "N")
    ]
    if len(cashless) > 0:
        cashless_all = cashless[cashless["INSTRUMENT_TYPE_CT"].isin(["A", "T"])]
        if len(cashless_all) > 0:
            melted = melt_time(cashless_all, ["REP_CTY"], "cashless_payment_txns")
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            melted = melted.groupby(["iso2", "year"], as_index=False)["cashless_payment_txns"].max()
            results.append(melted)
            log.info(f"    cashless_payment_txns: {len(melted)} obs")

    # Total cashless payments — Value
    cashless_v = df[
        (df["INDICATOR_CT"] == "M") &
        (df["MEASURE"] == "V")
    ]
    if len(cashless_v) > 0:
        cashless_v_all = cashless_v[cashless_v["INSTRUMENT_TYPE_CT"].isin(["A", "T"])]
        if len(cashless_v_all) > 0:
            melted = melt_time(cashless_v_all, ["REP_CTY"], "cashless_payment_value")
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            melted = melted.groupby(["iso2", "year"], as_index=False)["cashless_payment_value"].max()
            results.append(melted)
            log.info(f"    cashless_payment_value: {len(melted)} obs")

    # Cards — Number
    cards = df[
        (df["INDICATOR_CT"] == "T") &  # Cards
        (df["MEASURE"] == "N")
    ]
    if len(cards) > 0:
        cards_all = cards[cards["INSTRUMENT_TYPE_CT"].isin(["A", "T"])]
        if len(cards_all) > 0:
            melted = melt_time(cards_all, ["REP_CTY"], "n_cards")
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            melted = melted.groupby(["iso2", "year"], as_index=False)["n_cards"].max()
            results.append(melted)
            log.info(f"    n_cards: {len(melted)} obs")

    # GDP and population from CT1 (for normalization)
    for ind_code, col_name in [("A", "gdp_ct1"), ("B", "population_ct1")]:
        gdp = df[df["INDICATOR_CT"] == ind_code]
        if len(gdp) > 0:
            melted = melt_time(gdp, ["REP_CTY"], col_name)
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            melted = melted.groupby(["iso2", "year"], as_index=False)[col_name].first()
            results.append(melted)
            log.info(f"    {col_name}: {len(melted)} obs")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")
        return merged

    return pd.DataFrame()


# ===================================================================
# 5. Payment System Participants (from WS_CPMI_PARTICIP)
# ===================================================================
def extract_system_participants() -> pd.DataFrame:
    """Extract participant counts for large-value and retail payment systems."""
    log.info("Extracting payment system participants...")
    df = read_cpmi("WS_CPMI_PARTICIP_csv_col.csv")

    results = []

    # Large-value payment systems — direct participants
    for sys_type, sys_label in [
        ("A", "lvps"),        # Large-value
        ("B", "retail_ps"),   # Retail
        ("C", "fast_ps"),     # Fast payments
    ]:
        subset = df[
            (df["SYSTEM_TYPE"] == sys_type) &
            (df["PART_TYPE"] == "D")  # Direct participants, all
        ]
        if len(subset) > 0:
            col_name = f"n_participants_{sys_label}"
            melted = melt_time(subset, ["REP_CTY"], col_name)
            melted = melted.rename(columns={"REP_CTY": "iso2"})
            # Sum across systems within same type for a country
            melted = melted.groupby(["iso2", "year"], as_index=False)[col_name].sum()
            results.append(melted)
            log.info(f"    {col_name}: {len(melted)} obs")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")
        return merged

    return pd.DataFrame()


# ===================================================================
# 6. Payment System Transaction Volumes (from WS_CPMI_SYSTEMS)
# ===================================================================
def extract_system_volumes() -> pd.DataFrame:
    """Extract transaction volumes/values for large-value payment systems."""
    log.info("Extracting payment system transaction volumes...")
    df = read_cpmi("WS_CPMI_SYSTEMS_csv_col.csv")

    results = []

    # Large-value payment systems — total transactions
    for sys_type, sys_label in [
        ("A", "lvps"),
        ("B", "retail_ps"),
        ("C", "fast_ps"),
    ]:
        for measure, m_label in [("N", "txn_count"), ("V", "txn_value")]:
            subset = df[
                (df["SYSTEM_TYPE"] == sys_type) &
                (df["MEASURE"] == measure) &
                (df["INSTRUMENT_TYPE"] == "PA")  # Transactions, all
            ]
            if len(subset) > 0:
                col_name = f"{sys_label}_{m_label}"
                melted = melt_time(subset, ["REP_CTY"], col_name)
                melted = melted.rename(columns={"REP_CTY": "iso2"})
                melted = melted.groupby(["iso2", "year"], as_index=False)[col_name].sum()
                results.append(melted)
                log.info(f"    {col_name}: {len(melted)} obs")

    if results:
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r, on=["iso2", "year"], how="outer")
        return merged

    return pd.DataFrame()


# ===================================================================
# Combine all extractions
# ===================================================================
def main():
    log.info("=" * 60)
    log.info("CPMI Data Extraction")
    log.info("=" * 60)

    # ISO2 to ISO3 mapping for CPMI countries
    iso2_to_iso3 = {
        "AR": "ARG", "AU": "AUS", "BE": "BEL", "BR": "BRA", "CA": "CAN",
        "CH": "CHE", "CN": "CHN", "DE": "DEU", "ES": "ESP", "FR": "FRA",
        "GB": "GBR", "HK": "HKG", "ID": "IDN", "IN": "IND", "IT": "ITA",
        "JP": "JPN", "KR": "KOR", "MX": "MEX", "NL": "NLD", "RU": "RUS",
        "SA": "SAU", "SE": "SWE", "SG": "SGP", "TR": "TUR", "US": "USA",
        "ZA": "ZAF", "XW": "WLD", "XM": "EMU",
    }

    # Extract each component
    swift_msg = extract_swift_messages()
    swift_part = extract_swift_participants()
    institutions = extract_institutions()
    fast_pay = extract_fast_payments()
    sys_part = extract_system_participants()
    sys_vol = extract_system_volumes()

    # Merge all components
    log.info("\nMerging all CPMI components...")
    components = [swift_msg, swift_part, institutions, fast_pay, sys_part, sys_vol]
    components = [c for c in components if len(c) > 0]

    if not components:
        log.error("No data extracted!")
        return

    panel = components[0]
    for c in components[1:]:
        panel = panel.merge(c, on=["iso2", "year"], how="outer")

    # Map ISO2 to ISO3
    panel["iso3"] = panel["iso2"].map(iso2_to_iso3)

    # Remove world/euro area aggregates from country panel
    panel_countries = panel[~panel["iso2"].isin(["XW", "XM"])].copy()
    panel_world = panel[panel["iso2"].isin(["XW", "XM"])].copy()

    # Sort
    panel_countries = panel_countries.sort_values(["iso3", "year"]).reset_index(drop=True)

    # Compute per-capita / normalized indicators where GDP/pop available
    if "gdp_ct1" in panel_countries.columns and "population_ct1" in panel_countries.columns:
        pop = panel_countries["population_ct1"]
        if "cashless_payment_txns" in panel_countries.columns:
            panel_countries["cashless_per_capita"] = (
                panel_countries["cashless_payment_txns"] / pop
            )
        if "swift_msg_total" in panel_countries.columns:
            panel_countries["swift_msg_per_capita"] = (
                panel_countries["swift_msg_total"] / pop
            )
        if "n_cards" in panel_countries.columns:
            panel_countries["cards_per_capita"] = (
                panel_countries["n_cards"] / pop
            )

    # Save
    outpath = CLEAN_DIR / "cpmi_panel.parquet"
    table = pa.Table.from_pandas(panel_countries)
    pq.write_table(table, outpath)
    log.info(f"\nSaved: {outpath}")
    log.info(f"  Shape: {panel_countries.shape}")
    log.info(f"  Countries: {panel_countries['iso3'].nunique()}")
    log.info(f"  Years: {sorted(panel_countries['year'].unique())}")
    log.info(f"  Columns: {list(panel_countries.columns)}")

    # Diagnostics
    diag = {
        "n_countries": int(panel_countries["iso3"].nunique()),
        "countries": sorted(panel_countries["iso3"].dropna().unique().tolist()),
        "years": sorted(panel_countries["year"].unique().tolist()),
        "n_rows": len(panel_countries),
        "columns": list(panel_countries.columns),
        "coverage": {},
    }

    # Coverage: for each variable, how many country-years have data?
    data_cols = [c for c in panel_countries.columns if c not in ["iso2", "iso3", "year"]]
    for col in data_cols:
        n_valid = int(panel_countries[col].notna().sum())
        diag["coverage"][col] = {
            "n_valid": n_valid,
            "pct": round(100 * n_valid / len(panel_countries), 1),
        }

    diag_path = CLEAN_DIR / "cpmi_panel_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diag, f, indent=2)
    log.info(f"Diagnostics saved: {diag_path}")

    # Print coverage summary
    log.info("\n" + "=" * 60)
    log.info("COVERAGE SUMMARY")
    log.info(f"{'Variable':<35} {'N valid':>8} {'Coverage':>8}")
    log.info("-" * 55)
    for col in sorted(data_cols):
        cv = diag["coverage"][col]
        log.info(f"  {col:<33} {cv['n_valid']:>6}   {cv['pct']:>5.1f}%")

    log.info("\n" + "=" * 60)
    log.info("Done. Output: data/cleaned/cpmi_panel.parquet")


if __name__ == "__main__":
    main()
