# Access Instructions: Payment Friction Data Sources

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## Timeline Summary

All primary data sources except SWIFT are publicly available and can be obtained within a single day. No applications, registrations, or fees are required.

| Source | Access Time | Registration | Cost |
|--------|------------|-------------|------|
| World Bank RPW | Immediate | None | Free |
| World Bank Bilateral Remittances | Immediate | None | Free |
| BIS/CPMI Correspondent Banking | Immediate | None | Free |
| IMF Financial Access Survey | Immediate | None (API key optional) | Free |
| Chinn-Ito KAOPEN | Immediate | None | Free |
| Doing Business Archive | Immediate | None | Free |
| B-READY | Immediate | None | Free |
| SWIFT Messaging Data | Not feasible | Institutional partnership | Enterprise pricing |

---

## Source 1: World Bank Remittance Prices Worldwide (RPW)

### Steps to Download
1. Navigate to https://remittanceprices.worldbank.org/data-download
2. Download `rpw_dataset_2011_2025_q1.xlsx` (single Excel file)
3. No registration or account needed
4. Attribution required: cite "The World Bank, Remittance Prices Worldwide"

### Alternative Access
- DataBank interface for custom queries: https://databank.worldbank.org/source/remittance-prices-worldwide-(corridors)
- Select corridors, variables, and time periods interactively
- Export as CSV or Excel from DataBank

### Timeline: Immediate (< 5 minutes)

---

## Source 2: World Bank Bilateral Remittance Matrix

### Steps to Download
1. Navigate to https://www.worldbank.org/en/topic/migration/brief/remittances-knomad
2. Scroll to "Bilateral Remittance Matrix" section
3. Download the Excel file for the latest available year (2021)
4. Historical matrices may be available for earlier years (2010, 2015, 2017, 2019)

### Notes
- KNOMAD was discontinued in 2024; no guarantee of future updates
- The matrix is a single Excel sheet with sending countries as rows and receiving countries as columns
- Values are in USD millions (estimated, not observed)

### Timeline: Immediate (< 5 minutes)

---

## Source 3: BIS/CPMI Correspondent Banking Data

### Steps to Download
1. Navigate to https://www.bis.org/cpmi/paysysinfo/corr_bank_data.htm
2. Download the latest chartpack PDF and underlying data files
3. For bulk CSV download: https://data.bis.org/bulkdownload
   - Select the correspondent banking dataset
   - Download as zipped CSV or SDMX

### Important Notes
- The chartpack (PDF) contains charts and summary tables
- The "underlying data" files contain the actual numbers behind the charts
- For full bilateral corridor-level data, the bulk download from the BIS Data Portal is recommended
- Data sourced from SWIFT but published by BIS/CPMI with permission

### Timeline: Immediate to 30 minutes (depending on which format you need)

---

## Source 4: IMF Financial Access Survey (FAS)

### Steps to Download
1. Navigate to https://data.imf.org/en/datasets/IMF.STA:FAS
2. Use the dataset browser to select variables and countries
3. Export as CSV or Excel
4. Alternative: Use the IMF Data API (RESTful, JSON format)

### API Access
- Base URL: https://data.imf.org/api/
- No API key required for basic access
- Rate limits apply for heavy usage
- R package `imfr` or Python `requests` can be used

### Key Variables to Request
- Geographic Access: ATMs per 100,000 adults, branches per 100,000 adults
- Usage: Deposit accounts per 1,000 adults, loan accounts per 1,000 adults
- Mobile Money: Mobile money accounts per 1,000 adults, transaction value
- Financial Depth: Outstanding deposits (% GDP)

### Timeline: Immediate (< 15 minutes)

---

## Source 5: Chinn-Ito KAOPEN Index

### Steps to Download
1. Navigate to http://web.pdx.edu/~ito/Chinn-Ito_website.htm
2. Download `kaopen_2023.xls` (Excel) or `kaopen_2023.dta` (Stata 17)
3. Read the readme: https://web.pdx.edu/~ito/Readme_kaopen2023.pdf
4. No registration needed

### Notes
- The Excel file contains: country name, ISO code, year, kaopen (normalized), ka_open (raw)
- Data covers 1970-2023, 182 countries
- Next update expected summer/fall 2026 (after IMF AREAER 2025 publication)

### Timeline: Immediate (< 5 minutes)

---

## Source 6: World Bank Doing Business Archive (Trading Across Borders)

### Steps to Download
1. Navigate to https://archive.doingbusiness.org/en/data
2. Download "Historical Data" Excel file (covers DB04-DB20, all editions)
3. Or navigate to https://archive.doingbusiness.org/en/data/exploretopics/trading-across-borders for topic-specific data
4. Data is available in Excel and Stata formats

### Notes
- This is archived data (last update May 2019, project discontinued 2021)
- Data integrity concerns led to the project's discontinuation
- Trading Across Borders was one of the less controversial indicators
- Use for the 2005-2019 period only

### Timeline: Immediate (< 5 minutes)

---

## Source 7: World Bank B-READY

### Steps to Download
1. Navigate to https://www.worldbank.org/en/businessready
2. Or use Data360: https://data360.worldbank.org/en/dataset/WB_BREADY
3. Download the 2024 or 2025 edition data
4. Currently covers 101 economies (expanding)

### Notes
- B-READY is the successor to Doing Business but uses a fundamentally different methodology
- Cannot splice B-READY with historical Doing Business data
- Coverage is still incomplete (101/190+ economies)
- International trade indicators are in Pillars II and III

### Timeline: Immediate (< 10 minutes)

---

## Source 8: SWIFT Messaging Data (NOT FEASIBLE)

### Why It Is Not Accessible
- SWIFT data is proprietary and not available for public download
- Access requires an institutional partnership with SWIFT
- Some central banks receive SWIFT data for their jurisdictions but do not redistribute it
- The BIS/CPMI publishes aggregated SWIFT-derived data (see Source 3 above)

### If You Want to Try
- Contact SWIFT's research division at https://www.swift.com/
- Prepare an institutional letter of support from your university
- Be prepared for a multi-month negotiation process
- Most academic researchers use BIS/CPMI data instead

### Recommended Alternative
Use BIS/CPMI Correspondent Banking Data (Source 3), which is derived from SWIFT data and publicly available.

---

## Data Integration Notes

### Matching Country Identifiers
All sources use different country identifiers. You will need concordance tables:
- RPW: Country names (need manual matching to ISO codes)
- BIS/CPMI: BIS country codes (concordance to ISO available on BIS website)
- IMF FAS: IMF country codes (concordance to ISO available)
- Chinn-Ito: ISO 3166 codes included in the dataset
- WB Doing Business: ISO 3166 codes included

### Recommended Workflow
1. Download all datasets (Day 1)
2. Build country concordance table mapping all identifier systems to ISO 3166-1 alpha-3 (Day 1-2)
3. Merge datasets at country-year or country-pair-year level (Day 2-3)
4. Construct bilateral measures from country-level variables (Day 3)
5. Merge with trade data (BACI/Comtrade) at country-pair-product-year level (Day 4-5)
