"""
03_download_bilateral_frictions.py — Download bilateral payment friction data

Downloads publicly available bilateral financial data to construct
the payment friction composite index:

1. World Bank Bilateral Remittance Matrix (KNOMAD)
2. BIS Locational Banking Statistics (bulk CSV)
3. IMF CDIS Bilateral FDI (API)
4. FATF Grey/Black List (historical, from Wikipedia)
5. CLS Currency Membership (manual list)
6. World Bank RPW Remittance Prices (corridor-level costs)

Outputs to: data/raw/
"""

import json
import logging
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ===================================================================
# 1. World Bank Bilateral Remittance Matrix
# ===================================================================
def download_bilateral_remittances():
    """Download KNOMAD bilateral remittance estimates."""
    outpath = RAW_DIR / "bilateral_remittances.xlsx"
    if outpath.exists():
        log.info(f"Bilateral remittances already downloaded: {outpath}")
        return

    log.info("Downloading World Bank Bilateral Remittance Matrix...")

    # KNOMAD publishes bilateral remittance estimates as Excel files
    # Try multiple known URLs
    urls = [
        # Prosperity Data360 endpoint
        "https://prosperitydata360.worldbank.org/en/indicator/WB+KNOMAD+BRE",
        # Direct KNOMAD download links (these change periodically)
        "https://www.knomad.org/sites/default/files/2023-06/Bilateral_Remittance_Matrix_2021.xlsx",
        "https://www.knomad.org/sites/default/files/2022-11/Bilateral_Remittance_Matrix_2020.xlsx",
        # World Bank migration data page
        "https://thedocs.worldbank.org/en/doc/id/bilateral-remittance-estimates",
    ]

    for url in urls:
        try:
            log.info(f"  Trying: {url}")
            resp = requests.get(url, timeout=60, allow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 10000:
                # Check if it's actually an Excel file
                if (resp.content[:4] == b'PK\x03\x04' or  # xlsx
                    resp.content[:8] == b'\xd0\xcf\x11\xe0'):  # xls
                    outpath.write_bytes(resp.content)
                    log.info(f"  Saved: {outpath} ({len(resp.content) // 1024} KB)")
                    return
                else:
                    log.info(f"  Response is not Excel ({len(resp.content)} bytes)")
            else:
                log.info(f"  HTTP {resp.status_code} or small response")
        except Exception as e:
            log.info(f"  Failed: {e}")

    log.warning(
        "Could not auto-download bilateral remittances.\n"
        "  Manual download:\n"
        "  1. Go to: https://www.worldbank.org/en/topic/migrationremittancesdiasporaissues/brief/migration-remittances-data\n"
        "  2. Download 'Bilateral Remittance Matrix' (Excel)\n"
        "  3. Save as: data/raw/bilateral_remittances.xlsx"
    )


# ===================================================================
# 2. BIS Locational Banking Statistics (Bulk Download)
# ===================================================================
def download_bis_lbs():
    """Download BIS Locational Banking Statistics bulk CSV."""
    outpath = RAW_DIR / "bis_lbs_bilateral.csv"
    if outpath.exists():
        log.info(f"BIS LBS already downloaded: {outpath}")
        return

    log.info("Downloading BIS Locational Banking Statistics (bulk)...")
    log.info("  This is a large file (~100-300 MB) and may take several minutes.")

    # BIS bulk download endpoint
    # The LBS data is available as a single CSV via the bulk download page
    bulk_url = "https://data.bis.org/api/v2/data/dataflow/BIS/WS_LBS_D_PUB/1.0?format=csv"
    alt_urls = [
        "https://stats.bis.org/api/v1/data/BIS,WS_LBS_D_PUB,1.0/all?format=csv",
        "https://data.bis.org/bulkdownload",
    ]

    for url in [bulk_url] + alt_urls:
        try:
            log.info(f"  Trying: {url}")
            resp = requests.get(url, timeout=300, stream=True,
                                headers={"Accept": "text/csv"})
            if resp.status_code == 200:
                # Check content type
                ct = resp.headers.get("Content-Type", "")
                content_length = int(resp.headers.get("Content-Length", 0))
                log.info(f"  Response: {resp.status_code}, type={ct}, size={content_length // 1024}KB")

                if content_length > 100000 or "csv" in ct.lower() or "text" in ct.lower():
                    with open(outpath, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    file_size = outpath.stat().st_size
                    log.info(f"  Saved: {outpath} ({file_size // (1024*1024)} MB)")
                    return
                else:
                    log.info(f"  Response doesn't look like CSV data")
            else:
                log.info(f"  HTTP {resp.status_code}")
        except Exception as e:
            log.info(f"  Failed: {e}")

    log.warning(
        "Could not auto-download BIS LBS.\n"
        "  Manual download:\n"
        "  1. Go to: https://data.bis.org/bulkdownload\n"
        "  2. Download 'Locational banking statistics' (CSV)\n"
        "  3. Extract and save as: data/raw/bis_lbs_bilateral.csv"
    )


# ===================================================================
# 3. IMF CDIS Bilateral FDI
# ===================================================================
def download_imf_cdis():
    """Download IMF CDIS bilateral FDI positions via API."""
    outpath = RAW_DIR / "imf_cdis_bilateral.parquet"
    if outpath.exists():
        log.info(f"IMF CDIS already downloaded: {outpath}")
        return

    log.info("Downloading IMF CDIS bilateral FDI data...")

    # IMF JSON REST API for CDIS
    # Structure: indicator.reporter.counterpart.frequency.time
    # We want: Inward FDI positions (I_FA_D_T_BP6_USD) by counterpart economy
    base_url = "https://data.imf.org/api/v2/data"

    all_rows = []

    # Download year by year to avoid API limits
    for year in range(2015, 2024):
        url = (
            f"https://data.imf.org/api/v1/data/IMF.STA:DIP"
            f"?$filter=TIME_PERIOD eq '{year}'"
            f"&$top=10000"
            f"&format=json"
        )
        # Alternative IMF SDMX endpoint
        alt_url = (
            f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/"
            f"CDIS/A..I_FA_D_T_BP6_USD?startPeriod={year}&endPeriod={year}"
        )

        for attempt_url in [alt_url, url]:
            try:
                log.info(f"  {year}: trying {attempt_url[:80]}...")
                resp = requests.get(attempt_url, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()

                    # Parse SDMX JSON format
                    if "CompactData" in data:
                        ds = data["CompactData"].get("DataSet", {})
                        series = ds.get("Series", [])
                        if isinstance(series, dict):
                            series = [series]
                        for s in series:
                            ref_area = s.get("@REF_AREA", "")
                            counterpart = s.get("@COUNTERPART_AREA", "")
                            obs = s.get("Obs", [])
                            if isinstance(obs, dict):
                                obs = [obs]
                            for o in obs:
                                val = o.get("@OBS_VALUE")
                                period = o.get("@TIME_PERIOD", str(year))
                                if val and ref_area and counterpart:
                                    all_rows.append({
                                        "reporter": ref_area,
                                        "counterpart": counterpart,
                                        "year": int(period),
                                        "fdi_inward_usd_mn": float(val),
                                    })
                        if series:
                            log.info(f"  {year}: {len(series)} series parsed")
                            break
                    else:
                        log.info(f"  {year}: unexpected JSON structure")
                else:
                    log.info(f"  {year}: HTTP {resp.status_code}")
            except Exception as e:
                log.info(f"  {year}: failed: {e}")

        time.sleep(2)  # rate limit

    if all_rows:
        df = pd.DataFrame(all_rows)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, outpath)
        log.info(f"IMF CDIS saved: {outpath} ({len(df)} rows)")
    else:
        log.warning(
            "Could not download IMF CDIS via API.\n"
            "  Manual download:\n"
            "  1. Go to: https://data.imf.org/CDIS\n"
            "  2. Select bilateral FDI positions by counterpart economy\n"
            "  3. Download all years 2015-2023\n"
            "  4. Save as: data/raw/imf_cdis_bilateral.csv"
        )


# ===================================================================
# 4. FATF Grey/Black List Historical Data
# ===================================================================
def download_fatf_lists():
    """Scrape historical FATF grey/black list from Wikipedia."""
    outpath = RAW_DIR / "fatf_greylist_historical.parquet"
    if outpath.exists():
        log.info(f"FATF list already downloaded: {outpath}")
        return

    log.info("Scraping FATF grey/black list history from Wikipedia...")

    url = "https://en.wikipedia.org/wiki/Financial_Action_Task_Force_blacklist"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find tables with country listings
        tables = soup.find_all("table", class_="wikitable")
        log.info(f"  Found {len(tables)} wikitables")

        all_entries = []

        # Parse tables for country-date information
        for table in tables:
            rows = table.find_all("tr")
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])] if rows else []

            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) >= 2:
                    # Try to extract country name and dates
                    country = cells[0]
                    # Look for date-like information in other cells
                    for cell in cells[1:]:
                        if any(str(y) in cell for y in range(2000, 2026)):
                            all_entries.append({
                                "country": country,
                                "info": cell,
                                "headers": "|".join(headers[:len(cells)]),
                            })

        if all_entries:
            df = pd.DataFrame(all_entries)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, outpath)
            log.info(f"  FATF history saved: {outpath} ({len(df)} entries)")
        else:
            log.info("  Could not parse tables — saving raw HTML for manual parsing")
            (RAW_DIR / "fatf_wikipedia_raw.html").write_text(resp.text, encoding="utf-8")

    except Exception as e:
        log.warning(f"  FATF scraping failed: {e}")

    # Also create a manually curated FATF timeline from known sources
    _create_fatf_manual_timeline()


def _create_fatf_manual_timeline():
    """Create manually curated FATF grey-list timeline from public sources."""
    outpath = RAW_DIR / "fatf_greylist_curated.csv"
    if outpath.exists():
        return

    log.info("  Creating curated FATF grey-list timeline...")

    # Curated from FATF public statements and news reports
    # Format: country, iso3, added_date, removed_date, list_type
    entries = [
        # Major grey-list episodes relevant to our 2015-2023 sample
        ("Pakistan", "PAK", "2018-06", "2022-10", "grey"),
        ("Iran", "IRN", "2008-02", None, "black"),
        ("North Korea", "PRK", "2011-02", None, "black"),
        ("Myanmar", "MMR", "2020-02", None, "black"),
        ("Ethiopia", "ETH", "2017-10", "2019-10", "grey"),
        ("Sri Lanka", "LKA", "2017-11", "2019-10", "grey"),
        ("Tunisia", "TUN", "2017-11", "2019-10", "grey"),
        ("Trinidad and Tobago", "TTO", "2017-11", "2020-02", "grey"),
        ("Serbia", "SRB", "2018-02", "2019-06", "grey"),
        ("The Bahamas", "BHS", "2018-10", "2020-02", "grey"),
        ("Botswana", "BWA", "2018-10", "2021-10", "grey"),
        ("Cambodia", "KHM", "2019-02", "2023-02", "grey"),
        ("Ghana", "GHA", "2018-10", "2021-06", "grey"),
        ("Iceland", "ISL", "2019-10", "2020-10", "grey"),
        ("Mongolia", "MNG", "2019-10", "2020-10", "grey"),
        ("Panama", "PAN", "2019-06", "2023-10", "grey"),
        ("Zimbabwe", "ZWE", "2019-10", "2022-03", "grey"),
        ("Albania", "ALB", "2020-02", "2023-10", "grey"),
        ("Barbados", "BRB", "2020-02", "2021-06", "grey"),
        ("Jamaica", "JAM", "2020-02", "2022-03", "grey"),
        ("Mauritius", "MUS", "2020-02", "2021-10", "grey"),
        ("Nicaragua", "NIC", "2020-02", "2022-10", "grey"),
        ("Uganda", "UGA", "2020-02", "2020-10", "grey"),
        ("Cayman Islands", "CYM", "2021-02", "2023-10", "grey"),
        ("Haiti", "HTI", "2021-06", None, "grey"),
        ("Malta", "MLT", "2021-06", "2022-06", "grey"),
        ("Philippines", "PHL", "2021-06", "2022-06", "grey"),
        ("South Sudan", "SSD", "2021-06", None, "grey"),
        ("Jordan", "JOR", "2021-10", "2023-10", "grey"),
        ("Mali", "MLI", "2021-10", None, "grey"),
        ("Turkey", "TUR", "2021-10", "2024-06", "grey"),
        ("United Arab Emirates", "ARE", "2022-03", "2024-02", "grey"),
        ("DR Congo", "COD", "2022-10", None, "grey"),
        ("Mozambique", "MOZ", "2022-10", None, "grey"),
        ("Tanzania", "TZA", "2022-10", "2024-02", "grey"),
        ("South Africa", "ZAF", "2023-02", "2025-02", "grey"),
        ("Cameroon", "CMR", "2023-06", None, "grey"),
        ("Croatia", "HRV", "2023-06", "2025-02", "grey"),
        ("Vietnam", "VNM", "2023-06", "2024-06", "grey"),
        ("Bulgaria", "BGR", "2023-10", None, "grey"),
        ("Nigeria", "NGA", "2023-02", "2024-10", "grey"),
        ("Morocco", "MAR", "2019-02", "2023-02", "grey"),
        ("Senegal", "SEN", "2021-02", "2022-02", "grey"),
        ("Syria", "SYR", "2010-02", None, "grey"),
        ("Yemen", "YEM", "2010-02", None, "grey"),
    ]

    df = pd.DataFrame(entries, columns=["country", "iso3", "added_date",
                                          "removed_date", "list_type"])
    df.to_csv(outpath, index=False)
    log.info(f"  Curated FATF timeline saved: {outpath} ({len(df)} entries)")


# ===================================================================
# 5. CLS Currency Membership
# ===================================================================
def create_cls_membership():
    """Create CLS settlement currency membership list."""
    outpath = RAW_DIR / "cls_currencies.csv"
    if outpath.exists():
        log.info(f"CLS currencies already created: {outpath}")
        return

    log.info("Creating CLS currency membership list...")

    # CLS (Continuous Linked Settlement) settles 18 currencies
    # Source: https://www.cls-group.com/products/settlement/clssettlement/
    cls_currencies = [
        ("AUD", "AUS", "Australian Dollar"),
        ("CAD", "CAN", "Canadian Dollar"),
        ("CHF", "CHE", "Swiss Franc"),
        ("DKK", "DNK", "Danish Krone"),
        ("EUR", "EMU", "Euro"),  # multiple countries
        ("GBP", "GBR", "British Pound"),
        ("HKD", "HKG", "Hong Kong Dollar"),
        ("HUF", "HUN", "Hungarian Forint"),
        ("ILS", "ISR", "Israeli Shekel"),
        ("JPY", "JPN", "Japanese Yen"),
        ("KRW", "KOR", "Korean Won"),
        ("MXN", "MEX", "Mexican Peso"),
        ("NOK", "NOR", "Norwegian Krone"),
        ("NZD", "NZL", "New Zealand Dollar"),
        ("PLN", "POL", "Polish Zloty"),
        ("SEK", "SWE", "Swedish Krona"),
        ("SGD", "SGP", "Singapore Dollar"),
        ("USD", "USA", "US Dollar"),
        ("ZAR", "ZAF", "South African Rand"),
    ]

    # Eurozone countries
    eurozone = [
        "AUT", "BEL", "CYP", "EST", "FIN", "FRA", "DEU", "GRC", "IRL",
        "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "PRT", "SVK", "SVN", "ESP",
        "HRV",  # joined 2023
    ]

    df = pd.DataFrame(cls_currencies, columns=["currency", "primary_iso3", "currency_name"])
    df.to_csv(outpath, index=False)

    # Also save eurozone list
    euro_df = pd.DataFrame({"iso3": eurozone, "currency": "EUR", "in_cls": True})
    euro_path = RAW_DIR / "eurozone_members.csv"
    euro_df.to_csv(euro_path, index=False)

    log.info(f"  CLS currencies saved: {outpath} ({len(df)} currencies)")
    log.info(f"  Eurozone members saved: {euro_path} ({len(euro_df)} countries)")


# ===================================================================
# 6. RPW Corridor-Level Remittance Costs (direct download attempt)
# ===================================================================
def download_rpw_costs():
    """Attempt to download RPW corridor-level cost data."""
    outpath = RAW_DIR / "rpw_corridor_costs.csv"
    if outpath.exists():
        log.info(f"RPW costs already downloaded: {outpath}")
        return

    log.info("Attempting RPW corridor cost data download...")

    # RPW provides a data download page
    url = "https://remittanceprices.worldbank.org/data-download"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Look for download links
            links = soup.find_all("a", href=True)
            download_links = [
                l for l in links
                if any(ext in l["href"].lower() for ext in [".xlsx", ".csv", ".xls"])
            ]
            for link in download_links:
                href = link["href"]
                if not href.startswith("http"):
                    href = "https://remittanceprices.worldbank.org" + href
                log.info(f"  Found download link: {href}")
                try:
                    dl = requests.get(href, timeout=120)
                    if dl.status_code == 200 and len(dl.content) > 10000:
                        ext = ".xlsx" if ".xlsx" in href else ".csv"
                        dl_path = RAW_DIR / f"rpw_dataset{ext}"
                        dl_path.write_bytes(dl.content)
                        log.info(f"  Saved: {dl_path} ({len(dl.content) // 1024} KB)")
                        return
                except Exception as e:
                    log.info(f"  Download failed: {e}")

    except Exception as e:
        log.info(f"  RPW page fetch failed: {e}")

    log.warning(
        "Could not auto-download RPW costs.\n"
        "  Manual download:\n"
        "  1. Go to: https://remittanceprices.worldbank.org/data-download\n"
        "  2. Download the full dataset\n"
        "  3. Save as: data/raw/rpw_dataset.xlsx"
    )


# ===================================================================
# Main
# ===================================================================
def main():
    log.info("=" * 60)
    log.info("Bilateral Payment Friction Data Download")
    log.info("=" * 60)

    download_bilateral_remittances()
    download_bis_lbs()
    download_imf_cdis()
    download_fatf_lists()
    create_cls_membership()
    download_rpw_costs()

    # Summary
    log.info("\n" + "=" * 60)
    log.info("Download Summary:")
    for f in sorted(RAW_DIR.iterdir()):
        if f.is_file() and f.name != ".gitkeep":
            size_kb = f.stat().st_size // 1024
            log.info(f"  {f.name}: {size_kb} KB")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
