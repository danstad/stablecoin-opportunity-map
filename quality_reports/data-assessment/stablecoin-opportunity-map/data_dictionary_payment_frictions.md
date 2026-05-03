# Data Dictionary: Payment Friction Sources

**Project:** Stablecoin Opportunity Map
**Component:** Payment Friction Index -- Key Variables
**Date:** 2026-04-03

---

## Source 1: World Bank Remittance Prices Worldwide (RPW)

### Key Variables for PFI Construction

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| sending_country | ISO code of sending country | Categorical | ISO 3166 | 48 sending countries |
| receiving_country | ISO code of receiving country | Categorical | ISO 3166 | 105 receiving countries |
| quarter | Quarter of observation | Date | YYYY-QN | Q1 2011 - Q1 2025 |
| total_cost_pct_200 | Total cost as % of USD 200 sent | Continuous | Percent | Includes fee + FX margin |
| total_cost_pct_500 | Total cost as % of USD 500 sent | Continuous | Percent | Typically lower than $200 |
| transaction_fee | Explicit fee charged | Continuous | USD | Per transaction |
| fx_margin | Exchange rate margin vs interbank | Continuous | Percent | Provider markup |
| speed | Time to delivery | Categorical/Continuous | Hours/days | Varies by provider |
| payment_instrument | How sender initiates | Categorical | -- | Cash, bank transfer, card, mobile money |
| payout_method | How receiver collects | Categorical | -- | Cash pickup, account credit |
| provider_type | Type of RSP | Categorical | -- | Bank, MTO, mobile, post office |
| provider_name | Name of remittance service | Text | -- | Multiple per corridor per quarter |

### Recommended Aggregation
- **Primary variable:** `total_cost_pct_200` averaged across providers per corridor-quarter
- **Alternative:** Cheapest provider per corridor-quarter (captures frontier cost)
- **Robustness:** Use `total_cost_pct_500` as alternative

---

## Source 2: BIS/CPMI Correspondent Banking Data

### Key Variables for PFI Construction

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| jurisdiction_sending | Sending jurisdiction | Categorical | Country code | 200+ jurisdictions |
| jurisdiction_receiving | Receiving jurisdiction | Categorical | Country code | 200+ jurisdictions |
| year_month | Time period | Date | YYYY-MM | Monthly, published annually |
| active_correspondents | Number of banks with at least 1 message | Count | Banks | Bank-to-bank level |
| active_corridors | Whether corridor had any activity | Binary | 0/1 | At country-pair level |
| message_volume | Number of SWIFT messages in corridor | Count | Messages | Sent + received |
| message_value | Nominal value of messages | Continuous | USD | Where available |

### Recommended Construction
- **Primary variable:** `active_correspondents` per corridor (log-transformed)
- **Alternative:** Binary indicator for corridor activity (extensive margin)
- **De-risking measure:** Change in `active_correspondents` over time (percentage decline since 2011)

---

## Source 3: IMF Financial Access Survey (FAS)

### Key Variables for PFI Construction

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| country_code | ISO country code | Categorical | ISO 3166 | 163 economies |
| year | Year of observation | Date | YYYY | 2004-2024 |
| atms_per_100k | ATMs per 100,000 adults | Continuous | Count | Physical access |
| branches_per_100k | Commercial bank branches per 100,000 adults | Continuous | Count | Physical access |
| deposit_accounts_per_1k | Deposit accounts per 1,000 adults | Continuous | Count | Usage/penetration |
| loan_accounts_per_1k | Loan accounts per 1,000 adults | Continuous | Count | Credit access |
| mobile_money_accounts_per_1k | Mobile money accounts per 1,000 adults | Continuous | Count | From ~2012 |
| mobile_money_txn_value | Mobile money transaction value | Continuous | % GDP or USD | Digital payments |
| deposits_gdp | Outstanding deposits as % of GDP | Continuous | Percent | Financial depth |

### Recommended Construction
- **Financial access index:** PCA of ATMs, branches, deposit accounts, mobile money
- **Bilateral construction:** geometric_mean(FAS_i, FAS_j) or min(FAS_i, FAS_j)
- **Digital readiness:** mobile_money_accounts_per_1k separately

---

## Source 4: Chinn-Ito KAOPEN Index

### Key Variables for PFI Construction

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| country_code | ISO country code | Categorical | ISO 3166 | 182 countries |
| year | Year of observation | Date | YYYY | 1970-2023 |
| kaopen | Normalized capital openness index | Continuous | [-1.92, 2.39] | Higher = more open |
| ka_open | Raw index (principal component) | Continuous | Unstandardized | First principal component |

### Recommended Construction
- **Primary variable:** `kaopen` (normalized)
- **Bilateral construction:** min(kaopen_i, kaopen_j) -- the binding constraint determines friction
- **Alternative:** product or average of pair

---

## Source 5: World Bank Bilateral Remittance Matrix

### Key Variables

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| source_country | Sending country | Categorical | Country name/code | ~215 countries |
| destination_country | Receiving country | Categorical | Country name/code | ~215 countries |
| remittance_flow | Estimated bilateral remittance flow | Continuous | USD millions | Modeled, not observed |

### Recommended Use
- Control variable in gravity model, not a friction measure
- Identifies high-volume corridors for opportunity scoring

---

## Source 6: Doing Business -- Trading Across Borders (Historical)

### Key Variables

| Variable | Description | Type | Unit | Notes |
|----------|-------------|------|------|-------|
| country_code | ISO country code | Categorical | ISO 3166 | ~190 economies |
| year | Year of observation | Date | YYYY | 2005-2019 |
| time_export_doc | Time to export: documentary compliance | Continuous | Hours | Paperwork time |
| cost_export_doc | Cost to export: documentary compliance | Continuous | USD | Paperwork cost |
| time_export_border | Time to export: border compliance | Continuous | Hours | Customs time |
| cost_export_border | Cost to export: border compliance | Continuous | USD | Customs/inspection cost |
| time_import_doc | Time to import: documentary compliance | Continuous | Hours | Paperwork time |
| cost_import_doc | Cost to import: documentary compliance | Continuous | USD | Paperwork cost |
| time_import_border | Time to import: border compliance | Continuous | Hours | Customs time |
| cost_import_border | Cost to import: border compliance | Continuous | USD | Customs/inspection cost |

### Recommended Construction
- **Trade facilitation index:** PCA of time + cost variables, or simple average of normalized components
- **Bilateral construction:** sum or max of exporter and importer values
- **Use as control:** Separates payment frictions from logistics/regulatory frictions

---

## Variable Naming Convention for Merged Dataset

When constructing the final analysis dataset, use the following naming convention:

```
pfi_remcost_{ij}   = RPW remittance cost (corridor-level)
pfi_corrbank_{ij}  = BIS/CPMI correspondent banking density (corridor-level)
pfi_finaccess_{ij} = FAS financial access bilateral measure (constructed)
pfi_kaopen_{ij}    = Chinn-Ito bilateral openness (constructed)
pfi_tradefac_{ij}  = Doing Business trade facilitation bilateral (constructed)
rem_volume_{ij}    = Bilateral remittance volume (control)
```
