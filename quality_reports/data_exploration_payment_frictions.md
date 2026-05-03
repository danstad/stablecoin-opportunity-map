# Data Exploration: Payment Friction and Financial Infrastructure

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Agent:** Explorer
**Date:** 2026-04-03
**Research Question:** Which country x industry links stand to benefit most from stablecoin adoption? Construct a Payment Friction Index at the country-pair level.

---

## Summary Table

| # | Data Source | Feasibility | Coverage | Bilateral? | Key Strength |
|---|-----------|-------------|----------|------------|--------------|
| 1 | World Bank RPW | **A** | 367 corridors, 2011-Q1 2025 | Yes | Direct corridor-level remittance costs |
| 2 | World Bank Bilateral Remittance Matrix | **B+** | ~215 countries, 2010-2021 | Yes | Flow volumes for all country pairs |
| 3 | BIS/CPMI Correspondent Banking Data | **A-** | 200+ jurisdictions, 2011-2023 | Yes | Active correspondents and corridors |
| 4 | IMF Financial Access Survey | **A** | 163 economies, 2004-2024 | No (country) | Banking infrastructure depth |
| 5 | Chinn-Ito KAOPEN | **A** | 182 countries, 1970-2023 | No (country) | Capital account openness |
| 6 | SWIFT Messaging Data | **D** | 200+ countries | Yes | Ideal but not publicly available |
| 7 | Doing Business / B-READY | **B-** | 190 countries (historical) / 101 (B-READY) | No (country) | Trading across borders costs |

**Overall assessment:** A credible Payment Friction Index can be constructed from sources 1-5 plus 7, without needing SWIFT (source 6). The combination of corridor-level remittance costs (RPW), correspondent banking connectivity (BIS/CPMI), country-level financial infrastructure (FAS), and capital openness (KAOPEN) provides multiple complementary dimensions of payment friction.

---

## Source 1: World Bank Remittance Prices Worldwide (RPW)

### Current Access Status
**Verified working.** Data publicly available for download without registration.

### Download URL
- Excel download: https://remittanceprices.worldbank.org/data-download
  - File: `rpw_dataset_2011_2025_q1.xlsx`
- DataBank interface: https://databank.worldbank.org/source/remittance-prices-worldwide-(corridors)
- Data Catalog: https://datacatalog.worldbank.org/dataset/remittance-prices-worldwide

### Variables Available
- **Total remittance cost** (% of amount sent) -- for USD 200 and USD 500 transfers
- **Transaction fee** (explicit fee charged by provider)
- **Exchange rate margin** (difference between provider and interbank rate)
- **Speed of transfer** (time to delivery)
- **Payment instrument** (cash, bank transfer, debit/credit card, mobile money)
- **Payout method** (cash pickup, bank account credit)
- **Provider type** (bank, money transfer operator, mobile money, post office)
- **Provider name**
- **Sending country, receiving country** (corridor identifiers)

### Coverage
- **Corridors:** 367 country corridors (48 sending countries to 105 receiving countries)
- **Time period:** Q1 2011 to Q1 2025 (quarterly)
- **Frequency:** Quarterly updates
- **Sample:** Multiple providers surveyed per corridor per quarter

### Format
- MS Excel (.xlsx)
- Also accessible via DataBank API (JSON/CSV export)
- Repeated cross-section (same corridors surveyed each quarter)

### Feasibility Grade: A
Public, immediately downloadable, rich corridor-level detail, long time series.

### Known Quality Issues
- Corridors are not exhaustive -- covers major migration corridors but not all possible country pairs
- 367 corridors out of ~40,000 possible pairs means ~1% coverage
- Biased toward high-remittance-flow corridors (migration-driven)
- Costs are for retail remittances (USD 200/500), not commercial B2B payments
- Provider-level variation is large; need to decide whether to use average, cheapest, or median
- Survey methodology changes over time (new corridors added, some dropped)

### Fit for Our Project
**What it gives us:**
- Direct, quantitative measure of payment friction at the corridor level
- Can construct: average cost, cheapest option, speed premium, exchange rate margin
- Variation across corridors and over time enables panel estimation
- Distinguishes cash-based from digital payment channels

**What it does NOT give us:**
- Only 367 corridors -- insufficient alone for full gravity model with all country pairs
- Retail remittance costs may not reflect commercial/trade payment costs
- No information on B2B payments, letters of credit, or documentary collections
- Missing many South-South corridors

**Bottom line:** Excellent as one dimension of the Payment Friction Index. Must be supplemented with broader coverage data for the full country-pair matrix.

---

## Source 2: World Bank Bilateral Remittance Matrix

### Current Access Status
**Verified working**, but data is somewhat dated. KNOMAD (the producing unit) wound down in 2024. Latest bilateral matrix covers up to 2021.

### Download URL
- Main page: https://www.worldbank.org/en/topic/migration/brief/remittances-knomad
- Migration Policy Institute visualization: https://www.migrationpolicy.org/programs/data-hub/charts/bilateral-remittance-flows
- Direct download available as Excel from the KNOMAD/World Bank migration page

### Variables Available
- **Bilateral remittance flows** (estimated, USD millions) for all country pairs
- Based on migrant stock data, host/source country incomes
- Derived variable, not directly observed

### Coverage
- **Countries:** ~215 countries/territories (full matrix)
- **Time period:** Available for select years (2010, 2015, 2017, 2019, 2021 are typical)
- **Frequency:** Irregular (updated every 2-3 years)
- **Estimation methodology:** Allocates total inward remittances across source countries proportional to migrant stocks and income differentials

### Format
- Excel matrix (country x country)
- Cross-sectional (one matrix per year)

### Feasibility Grade: B+
Public download, full bilateral coverage, but estimated (not observed) and somewhat dated.

### Known Quality Issues
- **Estimated, not observed.** These are modeled bilateral flows, not transaction data
- Methodology depends on bilateral migrant stock data (which itself has measurement issues)
- Assumes remittances proportional to migrant stock -- ignores corridor-specific factors
- Limited time variation (only a few snapshots)
- KNOMAD discontinued in 2024 -- future updates uncertain
- Likely understates some South-South flows

### Fit for Our Project
**What it gives us:**
- Full bilateral matrix for all country pairs -- essential for gravity model
- Measures the *volume* of remittance flows (complementing RPW's *cost* data)
- Can identify corridors where remittance volumes are large (high stablecoin opportunity)

**What it does NOT give us:**
- Not a friction measure per se -- it is a flow volume
- Estimated rather than observed -- introduces measurement error
- Annual snapshots only -- limited time-series variation
- Does not distinguish payment channels

**Bottom line:** Useful as a control variable and for identifying high-opportunity corridors, but not a direct friction measure. The flow volume can be combined with RPW cost data: high-volume corridors with high costs = high stablecoin opportunity.

---

## Source 3: BIS/CPMI Correspondent Banking Data

### Current Access Status
**Verified working.** Published annually by the BIS Committee on Payments and Market Infrastructures. Underlying data available alongside chartpack and commentary.

### Download URL
- Main page: https://www.bis.org/cpmi/paysysinfo/corr_bank_data.htm
- Chartpack (PDF): https://www.bis.org/cpmi/paysysinfo/corr_bank_data/chartpack_2305.pdf
- BIS bulk data downloads: https://data.bis.org/bulkdownload (CSV/SDMX)
- Interactive map: https://www.bis.org/cpmi/paysysinfo/corr_bank_data/int_map/

### Variables Available
- **Number of active correspondent banks** per country/corridor
- **Number of active corridors** (single-direction jurisdiction pairs with at least one payment)
- **Payment message volumes** (sent and received) per corridor
- **Payment message values** (nominal, sent and received) per corridor
- **Regional and global trends** in correspondent banking relationships

### Coverage
- **Jurisdictions:** 200+ countries and territories
- **Time period:** 2011-2023 (monthly data aggregated annually in publications)
- **Source:** SWIFT payment messaging data (MT103, MT202)
- **Frequency:** Monthly underlying data, annual publications

### Format
- PDF chartpack with underlying data tables
- CSV/SDMX via BIS Data Portal bulk downloads
- Panel data (country-pair x year)

### Feasibility Grade: A-
Public, downloadable, bilateral coverage, sourced from SWIFT. Grade reduced slightly because extracting bilateral corridor-level data from the published format may require effort (much is published at aggregate/regional level in the chartpack).

### Known Quality Issues
- Based on SWIFT data but is a subset -- only correspondent banking messages, not all cross-border payments
- "Active correspondent" definition (at least 1 message/year) is a low bar
- Data captures message counts, not necessarily payment values at corridor level in all published tables
- Some underlying corridor-level data may be in supplementary files rather than the main chartpack
- The decline in correspondent banking relationships ("de-risking") is a key trend: 22% fewer active correspondents globally since 2011

### Fit for Our Project
**What it gives us:**
- Direct measure of **financial connectivity** between country pairs
- Number of active correspondents per corridor = proxy for payment infrastructure depth
- The de-risking trend (loss of correspondent relationships) is a natural experiment for our identification
- Bilateral structure matches our gravity framework
- Can construct: connectivity index, de-risking exposure, correspondent density

**What it does NOT give us:**
- Not a cost measure -- measures existence/density of banking relationships
- Does not capture fintech or mobile money corridors
- Published aggregates may not give full bilateral matrix without additional data processing

**Bottom line:** Critical data source. Correspondent banking density is arguably the best available proxy for wholesale payment infrastructure at the corridor level. The de-risking trend provides exogenous variation. Priority for inclusion in the Payment Friction Index.

---

## Source 4: IMF Financial Access Survey (FAS)

### Current Access Status
**Verified working.** Public, free access. 2025 release (covering data through 2024) issued October 2025.

### Download URL
- IMF Data Portal: https://data.imf.org/en/datasets/IMF.STA:FAS
- Alternative: https://data.imf.org/?sk=E5DCAB7E-A5CA-4892-A6EA-598B5463A34C
- API access available
- Also available via World Bank Data360: https://data360.worldbank.org/en/dataset/IMF_FAS

### Variables Available
**Access indicators (supply side):**
- ATMs per 100,000 adults
- ATMs per 1,000 km2
- Commercial bank branches per 100,000 adults
- Commercial bank branches per 1,000 km2

**Usage indicators:**
- Deposit accounts with commercial banks per 1,000 adults
- Loan accounts with commercial banks per 1,000 adults
- Outstanding deposits (% GDP)
- Outstanding loans (% GDP)

**Mobile money and fintech (newer series):**
- Mobile money accounts per 1,000 adults
- Mobile money transactions (value, number)
- E-money accounts
- Fintech lending volumes (pilot 2024-2025)

**Insurance and other:**
- Insurance policy holders
- Life/non-life premium volumes
- Credit unions, microfinance data

### Coverage
- **Economies:** 163 reporting in 2025 (up from 158 in 2024)
- **Time period:** 2004-2024 (annual)
- **Variables:** 121 data series
- **Frequency:** Annual

### Format
- Downloadable via IMF Data Portal (CSV, Excel, API)
- Panel data (country x year)

### Feasibility Grade: A
Public, well-documented, long time series, excellent country coverage. API available.

### Known Quality Issues
- Supply-side data (counts of ATMs, branches) -- does not capture demand/usage gaps fully
- Mobile money data available only from ~2012, with increasing coverage over time
- Some countries report inconsistently across years
- Does not distinguish urban vs. rural access well
- Country-level only -- no subnational or bilateral data
- Self-reported by central banks; quality varies by country

### Fit for Our Project
**What it gives us:**
- Measures the domestic financial infrastructure that underlies cross-border payment capability
- A country with few ATMs and bank branches likely has higher payment frictions
- Mobile money penetration captures alternative payment infrastructure (key for stablecoin opportunity)
- Can construct: financial depth index, banking access score, digital readiness indicator

**What it does NOT give us:**
- Not bilateral -- captures country-level infrastructure, not corridor-specific frictions
- Needs to be interacted with partner country data to create bilateral measures (e.g., min(FAS_i, FAS_j) or geometric mean)
- Does not directly measure cross-border payment costs

**Bottom line:** Essential complement for the country-level component of the Payment Friction Index. Financial infrastructure depth is a necessary condition for low-friction payments. Combine with bilateral data (RPW, BIS/CPMI) for the full picture.

---

## Source 5: Chinn-Ito Capital Account Openness Index (KAOPEN)

### Current Access Status
**Verified working.** Publicly downloadable. Latest update: 2023 data (released January 4, 2026).

### Download URL
- Main page: http://web.pdx.edu/~ito/Chinn-Ito_website.htm
- Files: `kaopen_2023.xls` (Excel) and `kaopen_2023.dta` (Stata 17)
- Readme: https://web.pdx.edu/~ito/Readme_kaopen2023.pdf

### Variables Available
- **KAOPEN:** Normalized index of capital account openness (continuous, higher = more open)
- **ka_open:** Raw index (first standardized principal component)
- Based on IMF AREAER binary indicators:
  - Multiple exchange rates
  - Restrictions on current account transactions
  - Restrictions on capital account transactions
  - Surrender of export proceeds requirement
- Country ISO codes (included)
- Year

### Coverage
- **Countries:** 182 countries
- **Time period:** 1970-2023 (annual)
- **Frequency:** Annual, typically updated once per year with ~1 year lag
- **Next update:** Expected summer/fall 2026 (after IMF AREAER 2025)

### Format
- Excel (.xls) and Stata (.dta)
- Panel data (country x year)

### Feasibility Grade: A
Publicly downloadable, long time series, near-universal country coverage, well-established in the literature, includes ISO codes.

### Known Quality Issues
- De jure measure (legal restrictions on paper), not de facto openness
- Binary indicators create coarse variation -- many countries cluster at extremes
- Does not capture financial account restrictions specifically (broad capital account)
- Same KAOPEN score for countries with very different actual capital mobility
- Updated with lag (2023 data as of Jan 2026)

### Fit for Our Project
**What it gives us:**
- Direct measure of regulatory barriers to cross-border payments
- Closed capital accounts = higher payment friction by construction
- Long time series allows panel estimation
- Extremely well-known in the trade/international finance literature

**What it does NOT give us:**
- Not bilateral -- country-level only (need to construct bilateral measure, e.g., min(KAOPEN_i, KAOPEN_j))
- De jure only -- may not capture informal barriers or enforcement variation
- Does not distinguish payment types (remittances vs. trade payments vs. portfolio flows)

**Bottom line:** Standard control in any gravity model. Essential for the Payment Friction Index as the regulatory/legal dimension. Combine with de facto measures (FAS, RPW) for a richer picture.

---

## Source 6: SWIFT Messaging Data

### Current Access Status
**Not publicly available.** SWIFT data is proprietary. Access only through:
1. SWIFT's own research partnerships
2. BIS/CPMI (which publishes aggregated versions -- see Source 3)
3. Central banks (which receive data for their jurisdictions)
4. Special academic research agreements (rare, case-by-case)

### Download URL
- No public download. SWIFT offers analytics services: https://www.swift.com/your-needs/industry-themes/financial-crime-compliance/payment-data-and-analytics
- Academic access: No standard application process documented publicly

### Variables Available (if accessed)
- MT103 messages: Single customer credit transfers (retail cross-border payments)
- MT202 messages: Interbank transfers (wholesale)
- Message volumes and values by corridor
- Processing times (SWIFT gpi)
- Currency breakdown
- Bank-to-bank connectivity

### Coverage
- **Countries:** 200+ (essentially all countries in the global financial system)
- **Time period:** Continuous (real-time messaging since 1973)
- **Frequency:** Daily messages, aggregatable to any frequency

### Format
- Proprietary database
- Published research uses aggregated/anonymized subsets

### Feasibility Grade: D
Ideal data but effectively inaccessible for independent academic research. The BIS/CPMI data (Source 3) provides the best publicly available version of SWIFT-derived corridor data.

### Known Quality Issues (from published research using SWIFT data)
- SWIFT covers ~50% of high-value cross-border payments (not all -- some use other networks)
- Message counts do not equal transaction counts (one payment may generate multiple messages)
- Does not capture cash corridors, hawala, or informal transfers
- Geographic attribution can be imprecise (messages routed through intermediary banks)

### Fit for Our Project
**What it would give us (if accessible):**
- The gold standard for bilateral payment connectivity and flow measurement
- Direct volume and value of cross-border payments by corridor
- Processing time data for payment speed friction

**What we actually get:**
- The BIS/CPMI data (Source 3) is the publicly available derivative
- Some published research papers include SWIFT-based statistics we can reference

**Bottom line:** Acknowledge as the ideal data source, use BIS/CPMI as the feasible proxy. Do not plan the project around obtaining SWIFT access.

---

## Source 7: World Bank Doing Business / B-READY (Trading Across Borders)

### Current Access Status
**Historical Doing Business data: verified working** (archived). **B-READY: verified working** but limited coverage so far.

### Download URLs
- Doing Business archive (DB04-DB20): https://archive.doingbusiness.org/en/data
- Trading Across Borders topic: https://archive.doingbusiness.org/en/data/exploretopics/trading-across-borders
- B-READY 2025: https://www.worldbank.org/en/businessready
- B-READY data: https://data360.worldbank.org/en/dataset/WB_BREADY

### Variables Available

**Doing Business (historical, 2005-2019):**
- Time to export: Documentary compliance (hours)
- Cost to export: Documentary compliance (USD)
- Time to export: Border compliance (hours)
- Cost to export: Border compliance (USD)
- Time to import: Documentary compliance (hours)
- Cost to import: Documentary compliance (USD)
- Time to import: Border compliance (hours)
- Cost to import: Border compliance (USD)

**B-READY (2024-2025):**
- International trade infrastructure quality
- Border management efficiency
- Time and cost for export/import compliance
- Cross-border digital trade indicators (new)
- Perceived obstacles to international trade

### Coverage
- **Doing Business:** ~190 economies, 2005-2019 (last data collection May 2019)
- **B-READY 2025:** 101 economies (expanding to full coverage by 2026-2027)
- **Frequency:** Annual

### Format
- Excel and Stata files (Doing Business archive)
- Excel/API (B-READY via Data360)
- Panel data (country x year)

### Feasibility Grade: B-
Historical Doing Business data is public and well-known, but the series stopped in 2019 and the project was discontinued amid data integrity concerns. B-READY is the successor but has limited coverage (101 economies) and a short time series (2024-2025 only). The two are not directly comparable.

### Known Quality Issues
- **Doing Business discontinued** due to data integrity scandal (2021) -- some country scores were manipulated
- Data reflects regulatory text and a "typical" transaction, not actual firm experience
- Country-level, not bilateral -- measures domestic procedures, not corridor-specific frictions
- B-READY has a fundamentally different methodology from Doing Business -- cannot splice the series
- B-READY coverage is still incomplete (101/190+ economies)

### Fit for Our Project
**What it gives us:**
- Direct measure of trade-related bureaucratic frictions (time and cost at the border)
- Captures non-payment frictions that stablecoins might not address (customs, documentation)
- Useful control variable to separate payment frictions from logistics frictions

**What it does NOT give us:**
- Not bilateral (country-level border procedures)
- Stopped in 2019 (Doing Business) -- pre-dates stablecoin growth period
- B-READY too new and incomplete for panel analysis
- Does not measure payment-specific costs

**Bottom line:** Use historical Doing Business (2005-2019) as a control variable for trade facilitation. It measures complementary frictions (border compliance, documentation) rather than payment frictions per se. Useful for showing that stablecoin opportunity is specifically about payment frictions, not general trade costs.

---

## Constructing the Payment Friction Index

### Proposed Multi-Dimensional Structure

The Payment Friction Index (PFI) for country pair (i,j) at time t should combine multiple dimensions:

```
PFI_{ijt} = f(Remittance_Cost_{ijt}, Correspondent_Banking_{ijt},
              Financial_Access_{it}, Financial_Access_{jt},
              Capital_Openness_{it}, Capital_Openness_{jt},
              Trade_Facilitation_{it}, Trade_Facilitation_{jt})
```

### Dimension Mapping

| Dimension | Source | Level | Availability |
|-----------|--------|-------|-------------|
| **Remittance cost** (direct transfer pricing) | RPW | Bilateral (367 corridors) | 2011-2025 quarterly |
| **Correspondent banking density** (financial connectivity) | BIS/CPMI | Bilateral (200+ jurisdictions) | 2011-2023 annual |
| **Financial infrastructure depth** (domestic capacity) | IMF FAS | Country-level | 2004-2024 annual |
| **Capital account openness** (regulatory barriers) | Chinn-Ito | Country-level | 1970-2023 annual |
| **Trade facilitation** (border procedures) | Doing Business | Country-level | 2005-2019 annual |
| **Remittance flow volumes** (revealed connectivity) | WB Bilateral Matrix | Bilateral | 2010, 2015, 2017, 2019, 2021 |

### Construction Strategy

**Step 1: Bilateral core** (where corridor-level data exists)
- Use RPW remittance costs directly for the 367 covered corridors
- Use BIS/CPMI correspondent banking data for broader bilateral coverage
- These two form the core bilateral friction measures

**Step 2: Country-level augmentation** (for full matrix)
- For country pairs not in RPW, predict remittance costs using gravity-type covariates
- Construct bilateral financial access: `FAS_bilateral_{ij} = sqrt(FAS_i * FAS_j)` or `min(FAS_i, FAS_j)`
- Construct bilateral openness: `KAOPEN_bilateral_{ij} = min(KAOPEN_i, KAOPEN_j)` (binding constraint)

**Step 3: Index aggregation**
- Normalize each dimension to [0,1]
- Either: PCA to extract common factor
- Or: Weighted average with weights calibrated from a preliminary gravity regression
- Or: Use dimensions separately in the gravity model (preferred for transparency)

### Gaps and Limitations

1. **Coverage asymmetry:** RPW covers 367 corridors; BIS/CPMI covers 200+ jurisdictions more comprehensively. Most gravity models need ~40,000 pairs.
2. **Temporal alignment:** RPW is quarterly, CPMI is annual, Chinn-Ito lags 1 year. Analysis should use annual frequency.
3. **Retail vs. wholesale:** RPW measures retail remittance costs; BIS/CPMI measures wholesale banking connectivity. Trade payments may be a mix.
4. **Missing B2B payment costs:** No public data on the cost of commercial cross-border payments (letters of credit, documentary collections, SWIFT transfer fees for firms). This is a genuine gap.
5. **Informal channels:** None of these sources capture hawala, cash couriers, or crypto-native flows.

### Recommended Approach

Use the **multidimensional approach**: include RPW cost, BIS/CPMI correspondent density, FAS infrastructure, and KAOPEN openness as separate regressors in the gravity model (interacted with product complexity). This avoids arbitrary index aggregation weights and lets the data reveal which friction dimension matters most for which types of trade.

Then, for the "opportunity map" visualization, construct a composite PFI using estimated coefficients as weights.

---

## Additional Data Sources to Consider

| Source | What It Adds | Status |
|--------|-------------|--------|
| **Chainalysis Crypto Adoption Index** | Crypto/stablecoin adoption by country (validation) | Public report, country-level ranking |
| **FATF Grey/Black Lists** | AML/CFT compliance status (regulatory friction) | Public, updated 3x/year |
| **Transparency International CPI** | Corruption perception (institutional friction proxy) | Public, annual, ~180 countries |
| **ITU ICT Development Index** | Internet/mobile penetration (digital readiness) | Public, annual |
| **GSMA Mobile Money Data** | Mobile money deployment and volumes | Semi-public (registration) |

---

## Data Access Timeline

| Source | Access Time | Action Required |
|--------|------------|-----------------|
| World Bank RPW | Immediate | Download Excel from website |
| World Bank Bilateral Remittances | Immediate | Download Excel from KNOMAD page |
| BIS/CPMI Correspondent Banking | Immediate | Download from BIS bulk data portal |
| IMF FAS | Immediate | Download via IMF Data Portal or API |
| Chinn-Ito KAOPEN | Immediate | Download Excel/Stata from PDX website |
| Doing Business Archive | Immediate | Download from archive.doingbusiness.org |
| B-READY | Immediate | Download from Data360 |
| SWIFT | Not feasible | Would require institutional partnership |

All primary data sources (except SWIFT) are publicly available and can be obtained within a single day. No applications, registrations, or fees required.
