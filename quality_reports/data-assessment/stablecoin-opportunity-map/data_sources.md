# Data Sources Assessment: Macro Controls, Institutional Variables, and Stablecoin Validation

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Explorer Agent:** Macro Controls and Validation Data Stream
**Date:** 2026-04-03
**Phase:** Discovery

---

## Summary

This assessment covers data sources for (1) standard macro controls in the gravity model, (2) institutional/governance variables, and (3) stablecoin adoption data for validation. The core finding: macro controls are straightforward (Grades A-B), but constructing a credible country-level stablecoin adoption measure from public data remains the hardest data challenge in this project.

---

## Source 1: World Development Indicators (WDI)

**Provider:** World Bank
**Feasibility Grade: A**

### Access
- **Status:** Fully public, no registration required for bulk download or API
- **URL (Bulk):** https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators
- **URL (DataBank):** https://databank.worldbank.org/source/world-development-indicators
- **URL (API):** https://data.worldbank.org/ (RESTful API, JSON/XML/CSV)
- **R Package:** `WDI` on CRAN (updated July 2025)
- **Cost:** Free
- **Last Updated:** February 2026

### Coverage
- **Countries:** 200+ economies
- **Time Period:** 1960--present (varies by indicator)
- **Format:** Repeated cross-section (country x year panels)

### Key Variables for This Project

| Variable | WDI Code | Notes |
|----------|----------|-------|
| GDP (current USD) | NY.GDP.MKTP.CD | Gravity model standard |
| GDP per capita (current USD) | NY.GDP.PCAP.CD | Income control |
| GDP per capita (PPP, constant 2021 intl $) | NY.GDP.PCAP.PP.KD | PPP-adjusted alternative |
| Population | SP.POP.TOTL | Gravity standard |
| Inflation (CPI, annual %) | FP.CPI.TOTL.ZG | Macro instability proxy |
| Official exchange rate (LCU per USD) | PA.NUS.FCRF | Exchange rate control |
| Real effective exchange rate index | PX.REX.REER | Competitiveness measure |
| Domestic credit to private sector (% GDP) | FD.AST.PRVT.GD.ZS | Financial development proxy |
| Broad money (% GDP) | FM.LBL.BMNY.GD.ZS | Financial depth |
| Bank branches per 100k adults | FB.CBK.BRCH.P5 | Financial access |
| ATMs per 100k adults | FB.ATM.TOTL.P5 | Financial access |
| Trade openness (% GDP) | NE.TRD.GNFS.ZS | Trade integration |
| Internet users (% population) | IT.NET.USER.ZS | Digital infrastructure |
| Mobile subscriptions per 100 | IT.CEL.SETS.P2 | Digital infrastructure |

### Known Issues
- GDP data lags 1--2 years for some developing countries
- Financial development indicators (credit/GDP) have gaps for small states
- Internet/mobile data have near-complete coverage post-2005
- Some series revised in quarterly updates; use vintage-consistent downloads for replicability

### Fit for Project
- **Excellent fit.** WDI provides all standard gravity controls (GDP, population) plus financial development and digital infrastructure proxies essential for modeling stablecoin opportunity.
- Treatment identification: No (WDI provides controls, not treatment)
- Outcome measurement: GDP and trade data serve as context, not outcome
- Population: Covers all countries in our trade data

---

## Source 2: Penn World Table (PWT) 11.0

**Provider:** Groningen Growth and Development Centre, University of Groningen
**Feasibility Grade: A**

### Access
- **Status:** Fully public, direct download
- **URL:** https://www.rug.nl/ggdc/productivity/pwt/
- **DOI:** 10.34894/FABVLR (DataverseNL)
- **Formats:** Stata (.dta), Excel (.xlsx)
- **R Package:** `pwt10` on CRAN (awaiting `pwt11` package)
- **FRED mirror:** https://fred.stlouisfed.org/release?rid=285
- **Cost:** Free
- **Version:** 11.0 (published October 7, 2025)

### Coverage
- **Countries:** 185 economies
- **Time Period:** 1950--2023
- **Format:** Panel (country x year)

### Key Variables for This Project

| Variable | PWT Code | Notes |
|----------|----------|-------|
| Real GDP (output-side, PPP) | rgdpo | Preferred for cross-country comparisons |
| Real GDP (expenditure-side, PPP) | rgdpe | Alternative GDP measure |
| GDP per capita | rgdpo/pop | Computed |
| Population | pop | In millions |
| Capital stock (PPP) | ck | Capital deepening proxy |
| Total Factor Productivity | ctfp | TFP level (USA=1) |
| TFP at constant national prices | rtfpna | TFP growth |
| Price level of GDP | pl_gdpo | PPP / exchange rate ratio |
| Real exchange rate | xr / pl_gdpo | Can be constructed |
| Human capital index | hc | Based on schooling + returns |
| Labor share of income | labsh | For calibration |
| Exchange rate (national currency/USD) | xr | Nominal exchange rate |

### Known Issues
- PWT 11.0 is a major update from 10.01; check for methodological breaks
- TFP estimates rely on capital stock construction assumptions; less reliable for low-income countries
- Coverage drops off for very small states
- Some variables (capital stock, TFP) only available for subset of countries

### Fit for Project
- **Strong fit for PPP-adjusted measures.** PWT provides the gold-standard PPP GDP data, capital stock, and TFP -- all useful as gravity controls and for constructing real exchange rate measures.
- Complementary to WDI: use PWT for PPP GDP and TFP; use WDI for financial development and digital infrastructure.
- Human capital index is a useful development control not available in WDI.

---

## Source 3: Worldwide Governance Indicators (WGI)

**Provider:** World Bank (Daniel Kaufmann and Aart Kraay)
**Feasibility Grade: A**

### Access
- **Status:** Fully public, direct download
- **URL (Official):** https://www.worldbank.org/en/publication/worldwide-governance-indicators
- **URL (DataBank):** https://databank.worldbank.org/source/worldwide-governance-indicators
- **URL (Download):** www.govindicators.org
- **Formats:** Excel, CSV, via DataBank query tool
- **Cost:** Free
- **Latest Data:** Through 2024 (updated annually in September)
- **Methodology Update:** 2025 methodology revision published

### Coverage
- **Countries:** 200+ economies
- **Time Period:** 1996--2024 (annual from 2002; biennial 1996/1998/2000)
- **Format:** Panel (country x year)

### Key Variables for This Project

| Dimension | Code | Use in Project |
|-----------|------|---------------|
| Rule of Law | RL | Contract enforcement quality -- core for trade costs |
| Control of Corruption | CC | Institutional quality for gravity model |
| Regulatory Quality | RQ | Regulatory environment for fintech adoption |
| Government Effectiveness | GE | State capacity proxy |
| Political Stability | PV | Risk measure for trade/investment |
| Voice and Accountability | VA | Democratic governance proxy |

All indicators are standardized: mean ~0, standard deviation ~1, ranging approximately -2.5 to +2.5.

### Known Issues
- Composite indicators based on multiple underlying sources; methodology changes over time
- 2025 methodology revision may create breaks with earlier vintages
- Point estimates have substantial margins of error (confidence intervals provided)
- Not suitable for short-run within-country variation -- governance changes slowly
- Perception-based measures, not objective institutional metrics

### Fit for Project
- **Excellent fit.** Rule of Law and Regulatory Quality are standard gravity controls and directly relevant to stablecoin adoption potential.
- Rule of Law proxies contract enforcement quality, which affects both trade costs and crypto regulation enforcement.
- Regulatory Quality captures the regulatory environment that shapes stablecoin legality and adoption.
- Best used as cross-sectional controls or slow-moving panel controls; not suitable for event studies.

---

## Source 4: Chainalysis Global Crypto Adoption Index

**Provider:** Chainalysis Inc.
**Feasibility Grade: C**

### Access
- **Status:** Report available for free download (registration required); granular data NOT publicly available as CSV/dataset
- **URL (Report):** https://go.chainalysis.com/2025-geography-of-cryptocurrency-report.html
- **URL (Blog/Rankings):** https://www.chainalysis.com/blog/2025-global-crypto-adoption-index/
- **Cost:** Report is free; underlying transaction-level data requires Chainalysis subscription (enterprise pricing, likely $50K+/year)
- **Format:** PDF report with tables and charts; no public API or bulk data export

### Coverage
- **Countries:** 151 economies
- **Time Period:** Published annually since 2020; sub-indices reported by quarter
- **Editions Available:** 2020, 2021, 2022, 2023, 2024, 2025

### Key Variables

| Sub-Index | What It Measures |
|-----------|-----------------|
| Retail Centralized Service Value | Crypto received by centralized services, weighted by PPP per capita |
| Overall Centralized Service Value | Total (retail + institutional) centralized service value |
| DeFi Value Received | DeFi protocol usage by country |
| Institutional Centralized Service Value | Transfers >$1M (new in 2025 edition) |
| **Overall Index** | Geometric mean of four sub-indices, normalized 0--1 |

### Methodology
- Transaction volumes estimated by mapping web traffic patterns of crypto services to countries
- Rankings weighted by PPP per capita and population
- Geometric mean ensures countries must rank well across all sub-indices
- 2025 methodology changed: added institutional sub-index, removed standalone retail DeFi sub-index

### Known Issues
- **Critical: Granular data not publicly downloadable.** Only rankings and report text are free
- Web traffic attribution is imprecise (VPN usage, shared hosting)
- Methodology changes across editions make time-series comparisons problematic
- Crypto adoption != stablecoin adoption (index covers all crypto, not stablecoins specifically)
- No stablecoin-specific sub-index
- Country rankings may be extractable from the report PDF but this is manual and error-prone

### Fit for Project
- **Partial fit, significant limitations.** Best available country-level crypto adoption ranking, but:
  - Not stablecoin-specific
  - Rankings (ordinal), not continuous measures
  - Data extraction from PDF is fragile
  - Methodology changes limit panel construction
- **Recommended use:** Validation exercise only. Show that countries our model predicts as high-opportunity also rank high on Chainalysis index. Use rankings from a single edition (2024 or 2025) as cross-sectional validation.

---

## Source 5: CoinGecko / CoinMarketCap APIs

**Provider:** CoinGecko / CoinMarketCap
**Feasibility Grade: D**

### Access
- **URL (CoinGecko):** https://www.coingecko.com/en/api
- **URL (CoinGecko Pricing):** https://www.coingecko.com/en/api/pricing
- **Free Tier:** Demo plan -- 30 calls/min, 10,000 calls/month cap
- **Paid Tiers:** Analyst ($14.99/mo), Lite ($129/mo), Pro ($499/mo)
- **CoinMarketCap:** Similar tiered API access

### Coverage
- **Coins:** All major stablecoins (USDT, USDC, DAI, BUSD, etc.)
- **Data:** Market cap, 24h volume, price history, exchange-level tickers
- **Time Period:** Varies by coin; most stablecoins from 2018+
- **Format:** JSON API responses

### Key Variables Available
- Global stablecoin market cap (aggregate and per-coin)
- Trading volume by exchange
- Historical price and volume data
- Exchange-level trading pair volumes

### What Is NOT Available
- **No country-level volume data.** Exchange location != user location
- **No geographic attribution.** Cannot determine where stablecoin demand originates
- Volume data is exchange-level, not user-level

### Known Issues
- Exchange-reported volumes are widely known to be inflated (wash trading)
- Free tier is heavily rate-limited
- Exchange domicile does not equal user geography (Binance serves global users from multiple jurisdictions)
- No on-chain data; only exchange-reported data

### Fit for Project
- **Poor fit for country-level analysis.** CoinGecko/CMC data is coin-level and exchange-level, not country-level. Cannot construct country-level stablecoin adoption from this source.
- **Possible use:** Global stablecoin market cap trends as aggregate time-series context only.

---

## Source 6: Artemis Terminal / Allium Labs / Visa Onchain Analytics

**Provider:** Artemis Analytics (primary), Allium Labs (data provider), Visa (dashboard partner)
**Feasibility Grade: C**

### Access
- **Artemis Dashboard:** https://app.artemisanalytics.com/stablecoins
- **Artemis Stablecoin Dashboard:** https://stablecoins.artemisanalytics.com/
- **Artemis Pricing:** https://www.artemisanalytics.com/pricing
- **Visa Dashboard:** https://visaonchainanalytics.com/
- **Artemis Free Tier:** Artemis Lite (free, limited access)
- **Paid Tiers:** Professional and Enterprise (pricing not publicly listed; likely $1,000--5,000+/month for API access)
- **Allium Labs:** Enterprise pricing for geographic stablecoin data

### Coverage
- **Blockchains:** 8+ chains (Ethereum, Solana, Tron, BSC, Polygon, Arbitrum, Optimism, Base)
- **Stablecoins:** 50+ tracked
- **Data Types:** Supply, volume, active addresses, transfer counts, geographic flows
- **Time Period:** Chain-dependent; most from 2020+

### Key Variables

| Variable | Availability | Notes |
|----------|-------------|-------|
| Stablecoin supply by chain | Free dashboard | Aggregate data visible |
| Transfer volumes by chain | Free dashboard | Aggregate data visible |
| Active addresses | Free dashboard | Aggregate data visible |
| Geographic flows by country | Paid / Enterprise | IP + timezone-based attribution |
| Cross-border corridors | Paid / Enterprise | Top corridor pairs |
| Domestic vs cross-border split | Paid / Enterprise | Geographic classification |

### Geographic Attribution Methodology
- IP addresses and timezones of on-chain entities as transactions reach blockchain nodes
- Combined with firm-provided geographic data
- Top sending countries identified: USA, Singapore, Hong Kong, Japan, UK
- Singapore-China identified as most active corridor

### Known Issues
- **Geographic attribution is inherently noisy.** VPN usage, node location != user location, privacy protocols
- Free tier provides aggregate chain-level data only; country-level requires paid access
- Enterprise pricing makes this expensive for academic use
- Attribution methodology not fully transparent
- Selection bias: only captures on-chain activity, not off-chain OTC stablecoin use
- Domain-profile note: "on-chain data has geographic attribution problems" -- this is a known referee concern

### Fit for Project
- **Best available source for geographic stablecoin flows, but access is expensive and data quality is uncertain.**
- If accessible, this would be the most direct validation data: actual stablecoin transfer volumes by country
- Geographic attribution issues mean this is validation data with noise, not ground truth
- **Recommendation:** Contact Artemis/Allium about academic partnerships or data grants. Many crypto data firms offer academic access programs.

---

## Source 7: Rajan-Zingales External Finance Dependence

**Provider:** Originally Rajan and Zingales (1998, AER); extended by Manova (2013, REStud) and others
**Feasibility Grade: B**

### Access
- **Original Data:** Available in the appendix of Rajan and Zingales (1998) -- Table 3
- **Manova (2013) Version:** Replication files available at REStud data archive
- **NBER Working Paper:** https://www.nber.org/papers/w5758
- **Compustat Construction:** Can be rebuilt from Compustat (requires WRDS access)
- **Cost:** Free (for published measures); WRDS subscription needed to update
- **Format:** Industry-level cross-section

### Coverage
- **Industries:** 36 ISIC 3-digit industries (original Rajan-Zingales)
- **Classification:** Originally SIC/ISIC; Manova extends to 3-digit ISIC mapped to SITC
- **Time Period:** Cross-sectional (based on 1980s US Compustat data; treated as time-invariant industry characteristic)
- **Countries:** Industry characteristic, not country-specific (by design)

### Key Variables

| Variable | Definition | Source |
|----------|-----------|-------|
| External Finance Dependence (EFD) | (Capital expenditure - cash flow) / capital expenditure, median US firm | Compustat |
| Asset Tangibility | Net PPE / total assets, median US firm | Compustat |
| Inventory-to-Sales Ratio | Inventories / sales, median US firm | Compustat |

### Concordance to HS Codes
- Rajan-Zingales uses ISIC Rev. 2 at 3-digit level
- Manova (2013) uses ISIC Rev. 2 mapped to SITC Rev. 2 via Haveman concordance tables
- For HS-based trade data, need: HS -> SITC -> ISIC concordance (available from UN and WITS)
- Concordance is many-to-one: multiple HS codes map to each ISIC industry

### Known Issues
- Based on 1980s US data; assumes industry financial characteristics are stable and transferable across countries
- Choi (2020, Economica) shows EFD is endogenous to financial development -- countries with more developed financial systems have industries that rely more on external finance
- 36 industries is coarse relative to HS 6-digit product-level data
- Concordance from HS to ISIC introduces noise
- Some researchers (e.g., Braun 2003) provide alternative measures using asset tangibility

### Fit for Project
- **Good fit for robustness check.** The Rajan-Zingales EFD measure tests whether stablecoin opportunity is driven by product complexity (our main channel) or by financial vulnerability (alternative channel).
- This is a robustness/horse-race variable, not the main treatment
- Concordance challenge: our trade data is HS 6-digit; EFD is ISIC 3-digit. This is manageable but adds noise.
- Referee expectation: a trade + finance paper should control for or discuss Rajan-Zingales.

---

## Source 8: Regulatory Event Timeline (CBDC + Crypto Regulation)

### Source 8a: Atlantic Council CBDC Tracker

**Provider:** Atlantic Council GeoEconomics Center
**Feasibility Grade: B**

#### Access
- **URL:** https://www.atlanticcouncil.org/cbdctracker/
- **Format:** Interactive web dashboard; some data visible in structured tables
- **Cost:** Free
- **Downloadable Data:** Limited; appears to be web-only interactive tool. No dedicated CSV/API.
- **Workaround:** Manual extraction from web interface or web scraping

#### Coverage
- **Countries:** 137 countries/currency unions (98% of global GDP)
- **Status Categories:** Research, Development, Pilot, Launched, Cancelled, Inactive
- **Launched CBDCs:** Bahamas (Sand Dollar), Jamaica (JAM-DEX), Nigeria (eNaira)
- **Active Pilots:** 49 countries (2025 data)

#### Key Variables
- CBDC development status (categorical: research/development/pilot/launch)
- Type of CBDC (retail vs wholesale)
- Technology platform
- Timeline milestones

#### Known Issues
- No bulk download; data must be scraped or manually extracted
- Status categories are coarse (no dates of transition between stages)
- Updated irregularly
- Crypto regulation data covers only 75 largest economies

#### Fit for Project
- **Good fit for CBDC control variable.** CBDC status is relevant because CBDC launches may substitute for or complement stablecoin adoption. Binary or categorical variable (has_CBDC_pilot / has_CBDC_launched) is easy to construct.
- For event study: need precise dates, which the tracker provides imprecisely.

### Source 8b: Library of Congress Crypto Regulation Survey

**Provider:** Law Library of Congress, Global Legal Research Directorate
**Feasibility Grade: B**

#### Access
- **URL:** https://www.loc.gov/item/2021687419/
- **Full Report PDF:** https://tile.loc.gov/storage-services/service/ll/llglrd/2021687419/2021687419.pdf
- **Cost:** Free
- **Format:** PDF report with structured tables

#### Coverage
- **Countries:** ~130 jurisdictions
- **Categories:** Absolute ban (9 countries), Implicit ban (42 countries), Tax treatment, AML/CFT application
- **Time Period:** Last comprehensive update November 2021; original report 2018

#### Key Variables
- Crypto ban status (absolute/implicit/legal)
- Tax treatment of crypto
- AML/CFT application to crypto
- Regulatory framework existence

#### Known Issues
- **Last comprehensive update is November 2021** -- significantly outdated
- Regulatory landscape has changed dramatically since 2021 (EU MiCA, US ETF approvals, etc.)
- PDF format requires manual extraction
- Binary categories miss regulatory nuance

#### Fit for Project
- **Partial fit, needs supplementation.** The ban/legal classification is useful for 2021 and earlier but needs updating for 2022--2025. Can be combined with Atlantic Council data and manual research for key countries.

### Constructing a Regulatory Timeline (Combined Approach)

For a usable regulatory event dataset, combine:
1. LoC 2018/2021 survey for historical ban/legal status
2. Atlantic Council CBDC tracker for CBDC milestones
3. Manual research for key regulatory events (EU MiCA effective dates, US executive orders, India crypto tax, China ban enforcement, El Salvador Bitcoin legal tender)
4. Academic sources: Auer et al. (2025, BIS) and Cerutti et al. (2024, IMF) provide regulatory classification data

**Combined Feasibility Grade: B** -- requires manual compilation but components are accessible.

---

## Stablecoin Adoption Proxy: Assessment and Recommendation

### The Core Challenge

No public dataset provides clean, country-level, stablecoin-specific adoption data with sufficient time-series depth for panel estimation. This is the hardest data challenge in the project.

### Available Proxy Options (Ranked)

| Rank | Proxy | Source | Pros | Cons | Grade |
|------|-------|--------|------|------|-------|
| 1 | Chainalysis Adoption Index rankings | Chainalysis report | 151 countries, established methodology | Not stablecoin-specific; ordinal not cardinal; methodology changes across years | C+ |
| 2 | On-chain stablecoin geographic volumes | Artemis/Allium | Most direct measure; continuous variable | Expensive; geographic attribution noisy; access uncertain | C |
| 3 | P2P exchange volumes (LocalBitcoins/Paxful) | Coin Dance, Useful Tulips (historical) | Genuinely country-level (buyer/seller locations) | Services have shut down or declined; Bitcoin not stablecoin | C- |
| 4 | Stablecoin supply on country-dominant chains | On-chain data | Free; verifiable | Chain != country (Tron is not "one country") | D |
| 5 | Google Trends for stablecoin terms by country | Google Trends | Free; country-level; time-series | Measures awareness not adoption; noisy | D+ |
| 6 | Exchange volumes by exchange domicile | CoinGecko/CMC | Free API | Exchange domicile != user location | D |

### Recommended Strategy

**Primary validation (cross-sectional):** Extract Chainalysis 2024 or 2025 rankings for all 151 countries from the report. Use the overall index and, if available, sub-indices. Correlate with our predicted Stablecoin Opportunity Score (SOS). This is ordinal validation -- show rank correlation, not point prediction.

**Secondary validation (if budget allows):** Request Artemis/Allium academic access for geographic stablecoin transfer volumes. This provides a continuous, more direct measure.

**Tertiary validation (free, noisy):** Google Trends index for "USDT" or "stablecoin" by country as a robustness check.

**For the gravity model itself:** The project does NOT need stablecoin adoption data as a dependent variable. The Stablecoin Opportunity Score (SOS) is the output, not an input. Stablecoin adoption data is for validation only -- showing that our predicted opportunities correlate with observed adoption. This means even noisy proxies are acceptable as long as we are transparent about their limitations.

---

## Overall Data Architecture for Macro Controls

| Role in Model | Primary Source | Backup Source |
|---------------|---------------|---------------|
| GDP, Population (gravity) | WDI | PWT 11.0 |
| GDP per capita (PPP) | PWT 11.0 | WDI |
| Financial development | WDI (credit/GDP) | IMF Financial Access Survey |
| Digital infrastructure | WDI (internet, mobile) | ITU |
| Governance/institutions | WGI | ICRG (restricted) |
| Exchange rate / PPP | PWT 11.0 | WDI |
| TFP / capital stock | PWT 11.0 | -- |
| Human capital | PWT 11.0 | WDI (school enrollment) |
| Inflation | WDI | IMF WEO |
| Capital account openness | Chinn-Ito Index | -- |
| External finance dependence | Rajan-Zingales / Manova | Compustat rebuild |
| CBDC status | Atlantic Council | -- |
| Crypto regulation | LoC + manual research | -- |
| Stablecoin adoption (validation) | Chainalysis index | Artemis (if accessible) |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Stablecoin adoption data unavailable at country level | High | Use Chainalysis rankings (free but ordinal); frame as validation, not estimation |
| Geographic attribution noise in on-chain data | High | Acknowledge in limitations; use as noisy proxy with measurement error discussion |
| Rajan-Zingales concordance to HS codes | Medium | Use established ISIC-SITC-HS concordances; aggregate trade data to ISIC 3-digit for robustness |
| WGI methodology revision (2025) | Low | Use pre-revision vintage or document the revision |
| PWT 11.0 methodological breaks from 10.01 | Low | Test sensitivity to PWT version |
| Chainalysis methodology changes across editions | Medium | Use single edition for cross-sectional validation; do not construct panel from multiple editions |
