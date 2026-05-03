# Data Sources: Payment Friction and Financial Infrastructure

**Project:** Stablecoin Opportunity Map
**Component:** Payment Friction Index Construction
**Explorer Agent:** Payment Friction Data Stream
**Date:** 2026-04-03

---

## Ranked Data Sources by Feasibility and Fit

### Tier 1: Core Index Components (Grade A)

**1. World Bank Remittance Prices Worldwide (RPW)**
- **Grade: A**
- **Role:** Direct corridor-level remittance cost measurement
- **Coverage:** 367 corridors (48 sending, 105 receiving), Q1 2011 - Q1 2025
- **Format:** Excel, quarterly panel
- **URL:** https://remittanceprices.worldbank.org/data-download
- **Fit:** Only public source with direct bilateral payment cost data. Core variable for the friction index. Limited to 367 corridors (of ~40,000 possible), so must be supplemented.

**2. IMF Financial Access Survey (FAS)**
- **Grade: A**
- **Role:** Country-level financial infrastructure depth
- **Coverage:** 163 economies, 2004-2024, 121 variables
- **Format:** CSV/Excel/API via IMF Data Portal
- **URL:** https://data.imf.org/en/datasets/IMF.STA:FAS
- **Fit:** Measures domestic banking and mobile money infrastructure. Country-level, not bilateral -- needs bilateral construction (geometric mean or minimum). Essential for capturing the "access" dimension of payment friction.

**3. Chinn-Ito KAOPEN Index**
- **Grade: A**
- **Role:** De jure capital account openness (regulatory friction)
- **Coverage:** 182 countries, 1970-2023
- **Format:** Excel, Stata
- **URL:** http://web.pdx.edu/~ito/Chinn-Ito_website.htm
- **Fit:** Regulatory barriers to cross-border payments. Standard in gravity literature. De jure only (not de facto).

### Tier 2: Important Supplements (Grade A- to B+)

**4. BIS/CPMI Correspondent Banking Data**
- **Grade: A-**
- **Role:** Bilateral financial connectivity / de-risking exposure
- **Coverage:** 200+ jurisdictions, 2011-2023
- **Format:** PDF chartpack + CSV/SDMX via BIS bulk download
- **URL:** https://www.bis.org/cpmi/paysysinfo/corr_bank_data.htm
- **Fit:** Best available proxy for wholesale payment infrastructure at corridor level. De-risking trend provides exogenous variation. May require effort to extract full bilateral matrix from published format.

**5. World Bank Bilateral Remittance Matrix**
- **Grade: B+**
- **Role:** Bilateral remittance flow volumes (revealed connectivity)
- **Coverage:** ~215 countries, select years (2010-2021)
- **Format:** Excel matrix
- **URL:** https://www.worldbank.org/en/topic/migration/brief/remittances-knomad
- **Fit:** Full bilateral matrix but estimated (not observed). Good for identifying high-opportunity corridors. KNOMAD discontinued 2024 -- no future updates.

### Tier 3: Control Variables (Grade B-)

**6. World Bank Doing Business Archive (Trading Across Borders)**
- **Grade: B-**
- **Role:** Trade facilitation friction (non-payment)
- **Coverage:** ~190 economies, 2005-2019
- **Format:** Excel, Stata
- **URL:** https://archive.doingbusiness.org/en/data
- **Fit:** Useful control for separating payment frictions from logistics/customs frictions. Discontinued 2019, data integrity concerns. B-READY successor has only 101 economies and 2 years of data.

### Tier 4: Not Feasible (Grade D)

**7. SWIFT Messaging Data**
- **Grade: D**
- **Role:** Would be ideal bilateral payment flow data
- **Coverage:** 200+ countries, real-time
- **Format:** Proprietary
- **URL:** No public access
- **Fit:** Gold standard but inaccessible. Use BIS/CPMI (Source 4) as the public derivative instead.

---

## Coverage Matrix: What Each Source Contributes to PFI

| Friction Dimension | Source | Bilateral? | Time Series |
|-------------------|--------|-----------|-------------|
| Transfer cost (%) | RPW | Yes (367 corridors) | 2011-2025 |
| Banking connectivity | BIS/CPMI | Yes (200+ jurisdictions) | 2011-2023 |
| Financial access depth | IMF FAS | No (construct bilateral) | 2004-2024 |
| Regulatory openness | Chinn-Ito | No (construct bilateral) | 1970-2023 |
| Trade facilitation | Doing Business | No (country-level) | 2005-2019 |
| Flow volumes | WB Bilateral Matrix | Yes (full) | Snapshots |
