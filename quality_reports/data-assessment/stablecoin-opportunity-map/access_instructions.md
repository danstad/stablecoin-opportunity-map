# Access Instructions: Macro Controls and Validation Data

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## Source 1: World Development Indicators (WDI)

### Method A: R Package (Recommended)
```r
install.packages("WDI")
library(WDI)

# Example: GDP, population, inflation, credit/GDP for all countries, 2000-2024
wdi_data <- WDI(
  country = "all",
  indicator = c(
    "NY.GDP.MKTP.CD",      # GDP current USD
    "SP.POP.TOTL",          # Population
    "FP.CPI.TOTL.ZG",      # Inflation
    "FD.AST.PRVT.GD.ZS",   # Domestic credit / GDP
    "IT.NET.USER.ZS",       # Internet users %
    "PA.NUS.FCRF"           # Exchange rate
  ),
  start = 2000, end = 2024
)
```

### Method B: Bulk Download
1. Go to https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators
2. Under "Data & Resources," download the CSV or Excel bulk file
3. File contains all indicators for all countries; filter in R/Stata/Python

### Method C: DataBank Query
1. Go to https://databank.worldbank.org/source/world-development-indicators
2. Select countries, series (indicators), and time period
3. Download as CSV or Excel

### Method D: API (for programmatic access)
```
GET https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD?date=2000:2024&format=json&per_page=20000
```

**Timeline:** Immediate. No registration, no application.

---

## Source 2: Penn World Table 11.0

### Download Steps
1. Go to https://www.rug.nl/ggdc/productivity/pwt/
2. Click on "PWT 11.0"
3. Download via DataverseNL (DOI: 10.34894/FABVLR)
4. Available in Stata (.dta) and Excel (.xlsx) formats

### R Access
```r
# PWT 11.0 R package may not yet be available; use direct download
# For PWT 10.01:
install.packages("pwt10")
library(pwt10)
data("pwt10.01")

# For PWT 11.0: download .dta file and read with haven
library(haven)
pwt11 <- read_dta("path/to/pwt110.dta")
```

### FRED Access (individual series)
- https://fred.stlouisfed.org/release?rid=285
- Browse and download individual country series

**Timeline:** Immediate. No registration required.

---

## Source 3: Worldwide Governance Indicators (WGI)

### Download Steps
1. Go to https://www.worldbank.org/en/publication/worldwide-governance-indicators
2. Or directly: www.govindicators.org
3. Download the full dataset (Excel format with all six dimensions, estimates, standard errors, and percentile ranks)

### DataBank Access
1. Go to https://databank.worldbank.org/source/worldwide-governance-indicators
2. Select countries, governance dimensions, and years
3. Download as CSV

### R Access
```r
# Via WDI package (governance indicators are in WDI)
library(WDI)
wgi_data <- WDI(
  country = "all",
  indicator = c("RL.EST", "CC.EST", "RQ.EST", "GE.EST", "PV.EST", "VA.EST"),
  start = 1996, end = 2024
)
```

**Timeline:** Immediate. No registration required.

---

## Source 4: Chainalysis Global Crypto Adoption Index

### Access Steps
1. Go to https://go.chainalysis.com/2025-geography-of-cryptocurrency-report.html
2. Register with email to download the full report (PDF)
3. **Rankings must be manually extracted from the report.** No CSV/dataset is publicly available.

### Data Extraction Strategy
- The report contains a ranked table of 151 countries with index scores
- Extract the table manually or use PDF parsing tools (e.g., `tabulizer` in R, `tabula-py` in Python)
- Cross-check with the blog post for top-20 rankings: https://www.chainalysis.com/blog/2025-global-crypto-adoption-index/
- Historical editions (2020--2024) available via similar URLs; each year requires separate extraction

### For Granular Data (Enterprise)
- Contact Chainalysis sales for academic pricing
- Enterprise products: Chainalysis Reactor, KYT, Market Intel
- Academic partnerships may be available; contact research@chainalysis.com

**Timeline:**
- Report download: Same day (email registration only)
- Data extraction from PDF: 1--2 days of manual work
- Enterprise data access: Weeks to months; uncertain pricing

---

## Source 5: CoinGecko API

### Setup
1. Register at https://www.coingecko.com/en/api
2. Get Demo API key (free)
3. Rate limits: 30 calls/min, 10,000 calls/month

### Example API Call
```python
import requests

# Get stablecoin market data
url = "https://api.coingecko.com/api/v3/coins/tether"
params = {"localization": "false", "tickers": "true", "market_data": "true"}
headers = {"x-cg-demo-api-key": "YOUR_API_KEY"}
response = requests.get(url, headers=headers, params=params)
```

### Stablecoin-Specific Endpoints
- `/coins/tether` -- USDT data
- `/coins/usd-coin` -- USDC data
- `/exchanges/{id}/tickers` -- Exchange-level trading pairs
- `/coins/{id}/market_chart` -- Historical price/volume

**Note:** No country-level data available. Exchange-level only.

**Timeline:** Immediate setup; API key in minutes.

---

## Source 6: Artemis Terminal / Allium Labs

### Free Access (Limited)
1. Go to https://app.artemisanalytics.com/stablecoins
2. Browse aggregate stablecoin metrics (supply, volume, active addresses by chain)
3. Dashboard at https://stablecoins.artemisanalytics.com/ for summary views

### Paid Access (Geographic Data)
1. Contact Artemis for pricing: https://www.artemisanalytics.com/pricing
2. Professional plan provides API access to stablecoin analytics
3. Enterprise plan includes Snowflake data share and custom API

### Allium Labs (Geographic Attribution Data)
1. Go to https://www.allium.so/team/stablecoin
2. Contact for enterprise pricing
3. Geographic flows data (by country, corridors) is enterprise-only

### Academic Access Strategy
- Email Artemis team about academic partnerships
- Reference their published research (they have co-authored academic papers)
- Visa Onchain Analytics dashboard (https://visaonchainanalytics.com/) shows some aggregate data freely
- Check if Artemis research reports at https://www.stablecoin.fyi/ contain extractable country-level data

**Timeline:**
- Free dashboard browsing: Immediate
- Academic partnership inquiry: 2--4 weeks for response
- Enterprise setup: 1--3 months

---

## Source 7: Rajan-Zingales External Finance Dependence

### Option A: Published Tables
1. Access Rajan and Zingales (1998), Table 3 in the AER article
2. Available via JSTOR: https://www.jstor.org/stable/116849
3. Manually enter the 36 industry-level EFD values

### Option B: Manova (2013) Replication Files
1. Go to REStud data archive for Manova (2013)
2. Download replication package
3. Extract the EFD and asset tangibility measures at ISIC 3-digit level
4. Use the concordance tables included in the replication package

### Option C: Rebuild from Compustat (for updated measures)
1. Access WRDS (requires institutional subscription)
2. Download Compustat North America annual data
3. Compute: EFD = (capx - oancf) / capx for each SIC industry, take median firm
4. Map SIC to ISIC using concordance tables

### Concordance Tables
1. UN concordance tables: https://unstats.un.org/unsd/classifications/Econ
2. WITS concordance: https://wits.worldbank.org/product_concordance.html
3. Haveman's International Trade Data: http://www.macalester.edu/research/economics/PAGE/HAVEMAN/Trade.Resources/tradeconcordances.html

**Timeline:**
- Published tables: Same day
- Manova replication files: 1--2 days
- Compustat rebuild: 1--2 weeks (requires WRDS access)

---

## Source 8: Regulatory Event Timeline

### Atlantic Council CBDC Tracker
1. Go to https://www.atlanticcouncil.org/cbdctracker/
2. Browse interactive map and data tables
3. Manually record CBDC status for each country of interest
4. No bulk download available; plan for 2--4 hours of manual extraction for ~140 countries

### Library of Congress Crypto Regulation
1. Download the November 2021 report: https://tile.loc.gov/storage-services/service/ll/llglrd/2021687419/2021687419.pdf
2. Extract ban/legal status tables from PDF
3. Supplement with manual research for 2022--2025 regulatory changes

### Supplementary Sources for Regulatory Timeline
- **EU MiCA:** Official Journal of the EU for implementation dates
- **US regulatory actions:** SEC, CFTC enforcement databases
- **BIS/FSB surveys:** https://www.bis.org/topic/fintech.htm
- **IMF AREAER:** Annual Report on Exchange Arrangements and Exchange Restrictions (restricted access, but regulatory classifications are published)

### Recommended Construction Workflow
1. Start with LoC 2021 report for baseline ban/legal status
2. Layer Atlantic Council CBDC data
3. Add major 2022--2025 events from academic sources (Auer et al. 2025, Cerutti et al. 2024)
4. Manual verification for top 30 countries in our sample
5. Create a simple panel: country x year with regulatory status variables

**Timeline:** 1--2 weeks for a comprehensive regulatory panel covering ~140 countries.

---

## Summary of Timelines

| Source | Time to Access | Time to Analysis-Ready | Effort |
|--------|---------------|----------------------|--------|
| WDI | Immediate | 1 day (R script) | Low |
| PWT 11.0 | Immediate | 1 day | Low |
| WGI | Immediate | 1 day | Low |
| Chainalysis Index | Same day (report) | 2--3 days (extraction) | Medium |
| CoinGecko | Immediate | 1 day | Low (but poor fit) |
| Artemis/Allium | Weeks (if academic access) | Unknown | High |
| Rajan-Zingales | Same day | 2--3 days (with concordance) | Medium |
| Regulatory Timeline | 1--2 weeks | 1--2 weeks | High |

**Critical path:** The binding constraint is stablecoin validation data. Begin Chainalysis report extraction and Artemis academic inquiry immediately. Macro controls (WDI, PWT, WGI) can be assembled in 1--2 days.
