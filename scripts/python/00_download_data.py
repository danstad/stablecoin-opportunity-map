"""
00_download_data.py — Programmatic data downloads + manual download checklist.

Downloads what can be automated (WDI, KAOPEN, Google Trends, HS-ISIC concordance,
Harvard ECI/PCI validation). Prints checklist for manual downloads requiring registration.

Outputs to: data/raw/
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

import requests
import wbgapi as wb
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SAMPLE_YEARS = range(2015, 2024)  # 2015-2023


# ===================================================================
# 1. World Development Indicators (WDI) via wbgapi
# ===================================================================
def download_wdi():
    """Download key WDI indicators for 2010-2023."""
    outpath = RAW_DIR / "wdi_indicators.parquet"
    if outpath.exists():
        log.info(f"WDI already downloaded: {outpath}")
        return

    log.info("Downloading WDI indicators via wbgapi...")
    indicators = {
        "NY.GDP.MKTP.CD": "gdp_current_usd",
        "NY.GDP.MKTP.PP.CD": "gdp_ppp_usd",
        "NY.GDP.PCAP.CD": "gdp_pc_usd",
        "NY.GDP.PCAP.PP.CD": "gdp_pc_ppp_usd",
        "SP.POP.TOTL": "population",
        "FP.CPI.TOTL.ZG": "inflation_cpi",
        "IT.NET.USER.ZS": "internet_pct",
        "IT.CEL.SETS.P2": "mobile_subscriptions_per100",
        "FB.ATM.TOTL.P5": "atms_per_100k",
        "FB.CBK.BRCH.P5": "bank_branches_per_100k",
        "SM.POP.REFG.OR": "refugee_origin",  # proxy for instability
        "BX.TRF.PWKR.CD.DT": "remittances_received_usd",
    }

    frames = []
    for code, name in indicators.items():
        try:
            df = wb.data.DataFrame(
                code, time=range(2010, 2024), labels=False, columns="time"
            )
            df = df.reset_index()
            df = df.melt(id_vars=["economy"], var_name="year", value_name=name)
            df["year"] = df["year"].str.replace("YR", "").astype(int)
            df.rename(columns={"economy": "iso3"}, inplace=True)
            frames.append(df)
            log.info(f"  {name}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  Failed to download {code} ({name}): {e}")

    if frames:
        merged = frames[0]
        for f in frames[1:]:
            merged = merged.merge(f, on=["iso3", "year"], how="outer")
        table = pa.Table.from_pandas(merged)
        pq.write_table(table, outpath)
        log.info(f"WDI saved: {outpath} ({len(merged)} rows)")
    else:
        log.warning("wbgapi failed — trying direct World Bank API v2...")
        _download_wdi_fallback(outpath, indicators)


def _download_wdi_fallback(outpath, indicators):
    """Fallback WDI download using direct World Bank API v2 (REST/JSON)."""
    all_rows = []
    for code, name in indicators.items():
        url = (
            f"https://api.worldbank.org/v2/country/all/indicator/{code}"
            f"?date=2010:2023&format=json&per_page=5000"
        )
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 2 and data[1]:
                    for entry in data[1]:
                        iso3 = entry.get("countryiso3code", "")
                        year_val = entry.get("date", "")
                        value = entry.get("value")
                        if iso3 and year_val and value is not None:
                            all_rows.append({
                                "iso3": iso3,
                                "year": int(year_val),
                                name: float(value),
                            })
                    log.info(f"  {name}: OK via fallback API")
                else:
                    log.warning(f"  {name}: empty response from fallback API")
            else:
                log.warning(f"  {name}: HTTP {resp.status_code} from fallback API")
        except Exception as e:
            log.warning(f"  {name}: fallback failed: {e}")
        time.sleep(1)  # rate limit

    if all_rows:
        df = pd.DataFrame(all_rows)
        # Group by iso3+year, taking first non-null per indicator
        df = df.groupby(["iso3", "year"]).first().reset_index()
        table = pa.Table.from_pandas(df)
        pq.write_table(table, outpath)
        log.info(f"WDI (fallback) saved: {outpath} ({len(df)} rows)")
    else:
        log.error("WDI fallback also failed! World Bank API may be down.")
        log.info("Manual download: https://databank.worldbank.org/source/world-development-indicators")


# ===================================================================
# 2. Chinn-Ito KAOPEN Index
# ===================================================================
def download_kaopen():
    """Download Chinn-Ito KAOPEN from Portland State."""
    outpath = RAW_DIR / "chinn_ito_kaopen.xlsx"
    if outpath.exists():
        log.info(f"KAOPEN already downloaded: {outpath}")
        return

    log.info("Downloading Chinn-Ito KAOPEN index...")
    # The Chinn-Ito dataset is distributed as Excel from their website
    url = "https://web.pdx.edu/~ito/kaopen_2023.xlsx"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        outpath.write_bytes(resp.content)
        log.info(f"KAOPEN saved: {outpath} ({len(resp.content) // 1024} KB)")
    except requests.RequestException as e:
        log.warning(f"KAOPEN download failed: {e}")
        log.info("Manual download: https://web.pdx.edu/~ito/kaopen_2023.xlsx")


# ===================================================================
# 3. Google Trends — "buy USDT" / "buy USDC" by country
# ===================================================================
def download_google_trends():
    """
    Download Google Trends interest by country for stablecoin purchase queries.
    Primary on/off ramp proxy for the feasibility quadrant.
    """
    outpath = RAW_DIR / "google_trends_stablecoins.parquet"
    if outpath.exists():
        log.info(f"Google Trends already downloaded: {outpath}")
        return

    log.info("Downloading Google Trends data via pytrends...")
    log.info("  (This may take several minutes due to rate limiting)")

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360)

        all_results = []
        queries = ["buy USDT", "buy USDC", "buy stablecoin"]

        for query in queries:
            log.info(f"  Querying: '{query}'...")
            try:
                pytrends.build_payload(
                    [query], cat=0, timeframe="2020-01-01 2023-12-31", geo=""
                )
                df = pytrends.interest_by_region(
                    resolution="COUNTRY", inc_low_vol=True, inc_geo_code=True
                )
                df = df.reset_index()
                df.rename(
                    columns={
                        "geoName": "country_name",
                        "geoCode": "geo_code",
                        query: "interest",
                    },
                    inplace=True,
                )
                df["query"] = query
                all_results.append(df)
                time.sleep(5)  # rate limit
            except Exception as e:
                log.warning(f"  Failed for '{query}': {e}")
                time.sleep(10)

        if all_results:
            combined = pd.concat(all_results, ignore_index=True)
            table = pa.Table.from_pandas(combined)
            pq.write_table(table, outpath)
            log.info(f"Google Trends saved: {outpath} ({len(combined)} rows)")
        else:
            log.error("No Google Trends data retrieved!")

    except ImportError:
        log.error("pytrends not installed. Run: pip install pytrends")
    except Exception as e:
        log.error(f"Google Trends download failed: {e}")
        log.info("If rate-limited, wait and retry, or use VPN.")


# ===================================================================
# 4. HS-ISIC Concordance (UN Statistics Division)
# ===================================================================
def download_hs_isic_concordance():
    """Download HS 2012 to ISIC Rev.4 concordance from UN Stats."""
    outpath = RAW_DIR / "hs2012_isic4_concordance.csv"
    if outpath.exists():
        log.info(f"HS-ISIC concordance already downloaded: {outpath}")
        return

    log.info("Downloading HS2012-ISIC4 concordance from UN Stats...")
    # UN Stats provides concordance tables
    url = "https://unstats.un.org/unsd/classifications/Econ/tables/HS/HS2012_ISIC4/HS2012-ISIC4.txt"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        outpath.write_text(resp.text, encoding="utf-8")
        log.info(f"HS-ISIC concordance saved: {outpath}")
    except requests.RequestException as e:
        log.warning(f"HS-ISIC concordance download failed: {e}")
        log.info(
            "Manual download: https://unstats.un.org/unsd/classifications/Econ"
        )


# ===================================================================
# 5. Harvard Growth Lab ECI/PCI (validation only)
# ===================================================================
def download_harvard_complexity():
    """Download Harvard Growth Lab ECI/PCI rankings for validation."""
    outpath_eci = RAW_DIR / "harvard_eci_rankings.csv"
    outpath_pci = RAW_DIR / "harvard_pci_rankings.csv"

    if outpath_eci.exists() and outpath_pci.exists():
        log.info("Harvard complexity data already downloaded.")
        return

    log.info("Downloading Harvard Growth Lab complexity rankings...")
    # Atlas of Economic Complexity data is available via their data download page
    # The direct API endpoint for country rankings:
    base_url = "https://atlas.cid.harvard.edu/api/data"

    # Country complexity rankings
    try:
        url = f"{base_url}/country/ranking/?year=2021"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data)
            df.to_csv(outpath_eci, index=False)
            log.info(f"Harvard ECI saved: {outpath_eci}")
        else:
            log.warning(
                f"Harvard ECI API returned {resp.status_code}. "
                "Manual download: https://atlas.cid.harvard.edu/rankings"
            )
    except Exception as e:
        log.warning(f"Harvard ECI download failed: {e}")
        log.info(
            "Manual download: https://atlas.cid.harvard.edu/rankings"
        )

    # Product complexity rankings
    try:
        url = f"{base_url}/product/ranking/?year=2021"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data)
            df.to_csv(outpath_pci, index=False)
            log.info(f"Harvard PCI saved: {outpath_pci}")
        else:
            log.warning(
                f"Harvard PCI API returned {resp.status_code}. "
                "Manual download from Atlas."
            )
    except Exception as e:
        log.warning(f"Harvard PCI download failed: {e}")


# ===================================================================
# 6. BIS CPMI Correspondent Banking Statistics
# ===================================================================
def download_bis_cpmi():
    """
    Attempt to download BIS correspondent banking statistics.
    BIS distributes bulk data via CSV downloads.
    """
    outpath = RAW_DIR / "bis_cpmi_corr_banking.csv"
    if outpath.exists():
        log.info(f"BIS CPMI already downloaded: {outpath}")
        return

    log.info("Attempting BIS CPMI correspondent banking download...")
    # BIS bulk download endpoint for CPMI statistics
    url = "https://data.bis.org/api/v2/data/dataflow/BIS/WS_CPMI_CT3/1.0?format=csv"
    try:
        resp = requests.get(url, timeout=120, headers={"Accept": "text/csv"})
        if resp.status_code == 200 and len(resp.content) > 1000:
            outpath.write_bytes(resp.content)
            log.info(f"BIS CPMI saved: {outpath} ({len(resp.content) // 1024} KB)")
        else:
            log.warning(
                f"BIS download returned status {resp.status_code} or small file. "
                "This dataset may require manual download."
            )
            _print_bis_manual_instructions()
    except Exception as e:
        log.warning(f"BIS download failed: {e}")
        _print_bis_manual_instructions()


def _print_bis_manual_instructions():
    log.info(
        "MANUAL DOWNLOAD REQUIRED for BIS CPMI:\n"
        "  1. Go to: https://www.bis.org/cpmi/paysysinfo.htm\n"
        "  2. Navigate to 'Correspondent banking' statistics\n"
        "  3. Download the full dataset (CSV)\n"
        "  4. Save as: data/raw/bis_cpmi_corr_banking.csv"
    )


# ===================================================================
# Print Manual Download Checklist
# ===================================================================
def print_manual_checklist():
    """Print a checklist of data sources requiring manual download."""
    checklist = (
        "\n"
        "================================================================\n"
        "              MANUAL DOWNLOAD CHECKLIST                         \n"
        "================================================================\n"
        "\n"
        "  The following data sources require manual download            \n"
        "  (registration or no public API):                              \n"
        "\n"
        "  [ ] BACI HS12 Trade Data (CEPII)                             \n"
        "      URL: http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele.asp\n"
        "      Files: BACI_HS12_Y2015.csv through BACI_HS12_Y2023.csv  \n"
        "      Also: country_codes_baci_hs12.csv                        \n"
        "      Save to: data/raw/                                       \n"
        "      Note: Requires free CEPII account                        \n"
        "\n"
        "  [ ] CEPII Gravity Dataset                                    \n"
        "      URL: http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele.asp\n"
        "      File: Gravity_V202301.csv (or latest)                    \n"
        "      Save to: data/raw/                                       \n"
        "      Note: Requires free CEPII account                        \n"
        "\n"
        "  [ ] World Development Indicators (if WDI API was down)       \n"
        "      URL: https://databank.worldbank.org/source/world-development-indicators\n"
        "      Or retry: python scripts/python/00_download_data.py      \n"
        "\n"
        "  [ ] World Bank Remittance Prices Worldwide (RPW)             \n"
        "      URL: https://remittanceprices.worldbank.org/             \n"
        "      Download the full dataset (Excel)                        \n"
        "      Save as: data/raw/rpw_dataset.xlsx                       \n"
        "\n"
        "  [ ] IMF Financial Access Survey (FAS)                        \n"
        "      URL: https://data.imf.org/?sk=E5DCAB7E-A5CA-4892-A6EA   \n"
        "      Export all indicators as CSV                              \n"
        "      Save as: data/raw/imf_fas.csv                            \n"
        "\n"
        "  [ ] Chainalysis Global Crypto Adoption Index                 \n"
        "      URL: https://www.chainalysis.com/blog/                   \n"
        "           2023-global-crypto-adoption-index/                  \n"
        "      Extract country rankings from the report                 \n"
        "      Save as: data/raw/chainalysis_rankings.csv               \n"
        "      Columns: rank, country, iso3, index_score                \n"
        "\n"
        "  [ ] Rajan-Zingales External Finance Dependence               \n"
        "      Source: Rajan & Zingales (1998, AER), Table 1            \n"
        "      Save as: data/raw/rajan_zingales_efd.csv                 \n"
        "      Columns: isic3, industry_name, efd                       \n"
        "\n"
        "  [ ] Chinn-Ito KAOPEN                                         \n"
        "      URL: https://web.pdx.edu/~ito/chinn-ito_website.htm      \n"
        "      Download the Excel file                                   \n"
        "      Save as: data/raw/chinn_ito_kaopen.xlsx                  \n"
        "\n"
        "  [ ] BIS CPMI Correspondent Banking                           \n"
        "      URL: https://www.bis.org/cpmi/paysysinfo.htm             \n"
        "      Download correspondent banking statistics                \n"
        "      Save as: data/raw/bis_cpmi_corr_banking.csv              \n"
        "\n"
        "  [ ] HS-ISIC Concordance                                      \n"
        "      URL: https://unstats.un.org/unsd/classifications/Econ    \n"
        "      Download HS2012 to ISIC Rev.4 correspondence             \n"
        "      Save as: data/raw/hs2012_isic4_concordance.csv           \n"
        "\n"
        "================================================================\n"
    )
    print(checklist)


# ===================================================================
# Main
# ===================================================================
def main():
    log.info("=" * 60)
    log.info("Stablecoin Opportunity Map — Data Download Script")
    log.info(f"Project root: {PROJECT_ROOT}")
    log.info(f"Output directory: {RAW_DIR}")
    log.info("=" * 60)

    # Programmatic downloads
    download_wdi()
    download_kaopen()
    download_google_trends()
    download_hs_isic_concordance()
    download_harvard_complexity()
    download_bis_cpmi()

    # Report what we have
    log.info("\n" + "=" * 60)
    log.info("Download Summary:")
    for f in sorted(RAW_DIR.iterdir()):
        if f.is_file():
            size_kb = f.stat().st_size // 1024
            log.info(f"  {f.name}: {size_kb} KB")

    # Print manual checklist
    print_manual_checklist()

    log.info("Done. Complete the manual downloads above, then run 01_preprocess_baci.py.")


if __name__ == "__main__":
    main()
