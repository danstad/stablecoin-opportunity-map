# Data Dictionary: Top Candidate Sources for Macro Controls and Validation

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## 1. World Development Indicators (WDI) -- Key Variables

### Gravity Model Controls

| WDI Code | Variable Name | Unit | Coverage | Notes |
|----------|--------------|------|----------|-------|
| NY.GDP.MKTP.CD | GDP (current US$) | USD | 200+ countries, 1960--present | Standard gravity mass variable |
| NY.GDP.MKTP.KD | GDP (constant 2015 US$) | USD | 200+ countries, 1960--present | Real GDP for growth |
| NY.GDP.PCAP.CD | GDP per capita (current US$) | USD | 200+ countries, 1960--present | Income level control |
| NY.GDP.PCAP.PP.KD | GDP per capita, PPP (constant 2021 intl $) | Intl $ | 200+ countries, 1990--present | PPP-adjusted income |
| SP.POP.TOTL | Population, total | Persons | 200+ countries, 1960--present | Gravity mass variable |

### Financial Development

| WDI Code | Variable Name | Unit | Coverage | Notes |
|----------|--------------|------|----------|-------|
| FD.AST.PRVT.GD.ZS | Domestic credit to private sector (% of GDP) | % | ~180 countries, 1960--present | Primary financial development proxy |
| FM.LBL.BMNY.GD.ZS | Broad money (% of GDP) | % | ~170 countries, 1960--present | Financial depth |
| FB.CBK.BRCH.P5 | Commercial bank branches (per 100,000 adults) | Count | ~160 countries, 2004--present | Financial access |
| FB.ATM.TOTL.P5 | ATMs (per 100,000 adults) | Count | ~160 countries, 2004--present | Financial access |

### Digital Infrastructure

| WDI Code | Variable Name | Unit | Coverage | Notes |
|----------|--------------|------|----------|-------|
| IT.NET.USER.ZS | Individuals using the Internet (% of population) | % | ~200 countries, 1990--present | Digital readiness |
| IT.CEL.SETS.P2 | Mobile cellular subscriptions (per 100 people) | Count | ~200 countries, 1975--present | Mobile penetration |
| IT.NET.BBND.P2 | Fixed broadband subscriptions (per 100 people) | Count | ~200 countries, 2000--present | Broadband access |

### Macroeconomic Stability

| WDI Code | Variable Name | Unit | Coverage | Notes |
|----------|--------------|------|----------|-------|
| FP.CPI.TOTL.ZG | Inflation, consumer prices (annual %) | % | ~190 countries, 1960--present | Macro instability; high inflation drives stablecoin demand |
| PA.NUS.FCRF | Official exchange rate (LCU per US$, period average) | Ratio | ~190 countries, 1960--present | Exchange rate control |
| NE.TRD.GNFS.ZS | Trade (% of GDP) | % | ~190 countries, 1960--present | Trade openness |
| BN.CAB.XOKA.GD.ZS | Current account balance (% of GDP) | % | ~180 countries, 1970--present | External balance |

---

## 2. Penn World Table 11.0 -- Key Variables

| PWT Code | Variable Name | Unit | Coverage | Notes |
|----------|--------------|------|----------|-------|
| rgdpo | Output-side real GDP at chained PPPs | Million 2017 USD | 185 countries, 1950--2023 | Preferred for cross-country levels |
| rgdpe | Expenditure-side real GDP at chained PPPs | Million 2017 USD | 185 countries, 1950--2023 | Alternative GDP |
| pop | Population | Millions | 185 countries, 1950--2023 | For per-capita computation |
| emp | Number of persons engaged | Millions | 185 countries, 1950--2023 | Labor force |
| hc | Human capital index | Index | ~150 countries, 1950--2023 | Based on years of schooling and returns |
| ck | Capital stock at current PPPs | Million 2017 USD | ~150 countries, 1950--2023 | Physical capital |
| ctfp | TFP level at current PPPs | USA=1 | ~100 countries, 1950--2023 | Cross-country TFP levels |
| rtfpna | TFP at constant national prices | 2017=1 | ~100 countries, 1950--2023 | TFP growth over time |
| xr | Exchange rate, national currency/USD | Ratio | 185 countries, 1950--2023 | Nominal exchange rate |
| pl_gdpo | Price level of output-side GDP | USA=1 | 185 countries, 1950--2023 | For real exchange rate |
| labsh | Share of labour compensation in GDP | Ratio | ~150 countries, 1950--2023 | Factor shares |
| csh_x | Share of merchandise exports at current PPPs | Ratio | 185 countries, 1950--2023 | Export intensity |
| csh_m | Share of merchandise imports at current PPPs | Ratio | 185 countries, 1950--2023 | Import intensity |

---

## 3. Worldwide Governance Indicators (WGI) -- All Six Dimensions

| WGI Code | Dimension | Unit | Coverage | Notes |
|----------|-----------|------|----------|-------|
| RL.EST | Rule of Law (Estimate) | Standardized (~N(0,1)) | 200+ countries, 1996--2024 | Contract enforcement; core institutional control |
| CC.EST | Control of Corruption (Estimate) | Standardized | 200+ countries, 1996--2024 | Corruption perception |
| RQ.EST | Regulatory Quality (Estimate) | Standardized | 200+ countries, 1996--2024 | Fintech/crypto regulatory environment |
| GE.EST | Government Effectiveness (Estimate) | Standardized | 200+ countries, 1996--2024 | State capacity |
| PV.EST | Political Stability (Estimate) | Standardized | 200+ countries, 1996--2024 | Absence of violence/terrorism |
| VA.EST | Voice and Accountability (Estimate) | Standardized | 200+ countries, 1996--2024 | Democratic governance |

**Standard errors available:** Each estimate has a corresponding standard error (e.g., RL.SE) for constructing confidence intervals.

**Percentile ranks available:** Each dimension also has a percentile rank version (e.g., RL.PER) ranging 0--100.

---

## 4. Chainalysis Global Crypto Adoption Index -- Sub-Indices

| Component | What It Captures | Scale | Notes |
|-----------|-----------------|-------|-------|
| Overall Index | Geometric mean of four sub-indices | 0--1 (normalized) | Primary validation variable |
| Retail Centralized Service Value | Small-value transfers through exchanges | Rank (1--151) | Weighted by PPP per capita |
| Overall Centralized Service Value | All transfers through exchanges | Rank (1--151) | Includes institutional |
| DeFi Value Received | DeFi protocol usage | Rank (1--151) | Less relevant for stablecoin payments |
| Institutional Centralized Service Value | Transfers >$1M | Rank (1--151) | New in 2025; captures institutional adoption |

**Important:** Sub-index values are RANKS, not continuous measures. Only the final index is normalized 0--1.

---

## 5. Rajan-Zingales External Finance Dependence -- Industry Measures

| Variable | Definition | Level | Source |
|----------|-----------|-------|--------|
| External Finance Dependence (EFD) | (Capex - Cash Flow) / Capex, median US firm | ISIC Rev.2 3-digit (36 industries) | Rajan & Zingales (1998), Table 3 |
| Asset Tangibility | Net PPE / Total Assets, median US firm | ISIC Rev.2 3-digit | Braun (2003) |
| Inventory/Sales | Inventories / Sales, median US firm | ISIC Rev.2 3-digit | Rajan & Zingales (1998) |

### ISIC-to-HS Concordance Path

```
HS 6-digit -> SITC Rev.3 (UN concordance)
SITC Rev.3 -> ISIC Rev.3 (UN concordance)
ISIC Rev.3 -> ISIC Rev.2 (UN concordance)
```

**Concordance tables available from:**
- UN Statistics Division: https://unstats.un.org/unsd/classifications/Econ
- WITS (World Bank): https://wits.worldbank.org/product_concordance.html
- Haveman's concordance tables (used by Manova 2013)

---

## 6. Regulatory Variables -- Constructed

| Variable | Type | Source | Construction |
|----------|------|--------|-------------|
| crypto_ban | Binary | LoC survey + manual | 1 if absolute or implicit ban on crypto |
| crypto_legal | Binary | LoC survey + manual | 1 if crypto explicitly legal |
| cbdc_status | Categorical | Atlantic Council | Research/Development/Pilot/Launched/None |
| cbdc_pilot | Binary | Atlantic Council | 1 if country has active CBDC pilot or launch |
| mica_jurisdiction | Binary | Manual | 1 if subject to EU MiCA (2025+) |
| stablecoin_regulation | Categorical | Manual compilation | None/Partial/Comprehensive |
