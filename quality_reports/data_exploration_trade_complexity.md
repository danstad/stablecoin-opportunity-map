# Data Exploration: Trade Data and Economic Complexity Sources

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Agent:** Explorer
**Date:** 2026-04-03
**Phase:** Discovery
**Focus:** Bilateral trade data (HS 6-digit) and economic complexity metrics (ECI, PCI, Product Space proximity)

---

## Summary Table

| # | Source | Type | Feasibility | Fit |
|---|--------|------|-------------|-----|
| 1 | CEPII BACI | Bilateral trade (HS6) | **A** | Primary trade data |
| 2 | UN Comtrade | Bilateral trade (HS6) | **B** | Backup / validation |
| 3 | CEPII Gravity | Gravity controls | **A** | Standard controls |
| 4 | Harvard Growth Lab Atlas / Dataverse | ECI, PCI, Product Space | **A** | Pre-computed complexity |
| 5 | OEC (Observatory of Economic Complexity) | ECI, PCI, visualizations | **B** | Supplementary / validation |
| 6 | R package `economiccomplexity` | Compute RCA, ECI, PCI, proximity | **A** | Computation engine |

---

## Source 1: CEPII BACI (Bilateral Trade at the Product Level)

### Provider
Centre d'Etudes Prospectives et d'Informations Internationales (CEPII), Paris.

### Current Access Status
**Verified working.** Last updated January 30, 2026 (version 202601). Free download under Etalab 2.0 open license. No registration required.

### Download URL
http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37

Detailed documentation: https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/DescriptionBACI.html

### Variables Available

| Variable | Description | Notes |
|----------|-------------|-------|
| `t` | Year | Annual |
| `i` | Exporter country code | ISO 3-digit numeric |
| `j` | Importer country code | ISO 3-digit numeric |
| `k` | Product code (HS 6-digit) | Keep as string to preserve leading zeros |
| `v` | Trade value | Thousands of USD |
| `q` | Trade quantity | Metric tons |

Supporting files include country code dictionaries and product code concordances.

### Coverage

- **Countries:** ~200 countries and territories
- **Products:** ~5,000 products at HS 6-digit level
- **Time period by HS revision:**
  - HS92: 1995-2024
  - HS96: 1996-2024
  - HS02: 2002-2024
  - HS07: 2007-2024
  - HS12: 2012-2024
  - HS17: 2017-2024
  - HS22: 2022-2024
- **Panel structure:** Repeated cross-section (annual bilateral trade flows). Only strictly positive trade flows recorded.

### Format
CSV files, comma-delimited, dots as decimal separators. Separate files per HS revision and year.

### Feasibility Grade: A
Public, free, no registration, well-documented, standard CSV format, covers 2015-2024 in multiple HS revisions.

### Known Quality Issues
- BACI reconciles mirror trade statistics (exporter reports vs. importer reports) using a reliability weighting scheme. This is a major advantage over raw Comtrade data.
- Quantity data (`q`) has more missing values than trade values (`v`). For this project, we primarily need values.
- Only positive flows are recorded -- zeros must be inferred from the universe of possible bilateral-product combinations.
- HS revision concordance across time is handled by BACI internally within each HS track, but merging across HS revisions requires external concordance tables.
- Small country trade may be noisy due to re-exports and transshipment.

### Fit for This Project
**Excellent.** BACI is the standard source for PPML gravity at the HS 6-digit level. It covers our 2015-2024 panel (2025 will not be available until early 2027). The HS92 track gives the longest consistent series. The reconciled values reduce measurement error relative to raw Comtrade. Zeros must be constructed (standard practice -- create the full i x j x k x t matrix and fill non-observed flows with zero). This is computationally intensive at HS6 (~200 x 200 x 5000 x 10 = 2 billion potential observations) but can be managed with product-level or region-level subsets.

---

## Source 2: UN Comtrade (Bilateral Trade)

### Provider
United Nations Statistics Division.

### Current Access Status
**Verified working, with limitations.** The new Comtrade Plus portal (comtradeplus.un.org) replaced the legacy system. Free API access requires registration. Bulk download requires paid subscription.

### Download URL / API
- Portal: https://comtradeplus.un.org/
- API developer portal: https://comtradedeveloper.un.org/
- R package: `comtradr` (rOpenSci) -- https://docs.ropensci.org/comtradr/
- Python library: `comtradeapicall` -- https://github.com/uncomtrade/comtradeapicall

### API Rate Limits

| Tier | Calls/Day | Records/Call | Bulk Download | Cost |
|------|-----------|-------------|---------------|------|
| No token | Unlimited | 500 | No | Free |
| Free registered | 500 | 100,000 | No | Free (registration) |
| Premium Individual | Higher | Higher | Yes | Paid (contact subscriptions@un.org) |
| Premium Pro | Highest | Highest | Yes | Paid |

### Variables Available
- Reporter, partner, commodity code (HS 2/4/6 digit), trade flow direction (import/export), trade value (USD), quantity, quantity unit, year, HS revision.
- Multiple classification systems: HS, SITC, BEC.

### Coverage
- **Countries:** 200+ reporters
- **Products:** HS 6-digit (and coarser)
- **Time period:** 1962-present (SITC), 1988-present (HS)
- **Format:** API returns JSON/CSV

### Feasibility Grade: B
Free API access is workable but rate-limited. Downloading the full HS6 bilateral panel for 200 countries x 10 years would require thousands of API calls. Bulk download is paid. For our project, BACI is strictly superior since it already cleans and reconciles Comtrade data.

### Known Quality Issues
- Raw Comtrade data has well-known mirror trade discrepancies (exporter A reports differently from importer B).
- Missing reporters for some country-years.
- HS revision changes create concordance challenges across time.
- Re-export and re-import confusion for entrepot economies (Singapore, Hong Kong, Netherlands).

### Fit for This Project
**Backup / validation only.** Since BACI is built from Comtrade with reconciliation, there is no reason to use raw Comtrade as the primary source. Useful for: (a) checking specific bilateral flows, (b) accessing the most recent year (2025) before BACI updates, (c) cross-validation of suspicious values.

---

## Source 3: CEPII Gravity Dataset

### Provider
CEPII (Conte, Cotterlaz, and Mayer, 2022).

### Current Access Status
**Verified working.** Version 202211 (November 2022). Free download under Etalab 2.0 open license.

### Download URL
http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8

Documentation: https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf

### Variables Available

**Bilateral variables (country-pair-year):**

| Variable | Description |
|----------|-------------|
| `iso3_o`, `iso3_d` | Origin and destination ISO3 codes |
| `year` | Year |
| `distw` | Weighted bilateral distance (km, population-weighted) |
| `dist` | Simple distance between capitals |
| `contig` | Contiguity dummy (shared land border) |
| `comlang_off` | Common official language dummy |
| `comlang_ethno` | Common language (ethnolinguistic) dummy |
| `comcol` | Common colonizer dummy |
| `col45` | Colonial relationship post-1945 |
| `colony` | Ever in colonial relationship |
| `comcur` | Common currency dummy |
| `curcol` | Currently in colonial relationship |
| `fta_wto` | Free trade agreement (from WTO RTA database) |
| `rta_type` | RTA type (1=PSA, 2=FTA, 3=CU, 4=EIA) |
| `tradeflow_baci` | Bilateral trade flow from BACI |

**Unilateral variables (country-year):**

| Variable | Description |
|----------|-------------|
| `gdp_o`, `gdp_d` | GDP (current USD) |
| `pop_o`, `pop_d` | Population |
| `gdpcap_o`, `gdpcap_d` | GDP per capita |
| `wto_o`, `wto_d` | WTO membership dummy |

### Coverage
- **Country pairs:** All existing countries
- **Time period:** 1948-2020
- **Format:** CSV, RDS (R), DTA (Stata)
- **Unit of observation:** Country-pair-year (bilateral) + country-year (unilateral)

### Feasibility Grade: A
Public, free, well-documented, available in multiple formats. Standard in the gravity literature. The documentation explicitly warns against opening in Excel due to file size -- use R or Python.

### Known Quality Issues
- **Time coverage ends at 2020.** Our panel extends to 2024/2025. We will need to extend the gravity variables for 2021-2024 using other sources (WTO RTA database for FTAs, WDI for GDP/population). The time-invariant variables (distance, language, colony) do not need updating.
- Common currency variable (`comcur`) is particularly relevant for our project but may not capture informal dollarization or stablecoin usage.
- FTA coverage may lag behind actual implementation dates.

### Fit for This Project
**Essential for gravity controls.** The CEPII Gravity dataset provides the standard right-hand-side variables for PPML gravity estimation. The gap from 2021-2024 is manageable for time-invariant bilateral variables (distance, language, colony, contiguity) and can be extended for time-varying variables (GDP, population, FTA status) from primary sources. The `comcur` variable will be interesting as a baseline against which to measure stablecoin-induced "virtual common currency" effects.

---

## Source 4: Harvard Growth Lab -- Atlas of Economic Complexity / Dataverse

### Provider
Harvard Kennedy School, Growth Lab. Previously at CID (Center for International Development). The Atlas has moved to atlas.hks.harvard.edu (redirected from atlas.cid.harvard.edu).

### Current Access Status
**Verified working.** Data downloads available through two channels:
1. **Atlas website:** https://atlas.hks.harvard.edu/data-downloads (JavaScript-heavy, may require browser)
2. **Harvard Dataverse:** https://dataverse.harvard.edu/dataverse/atlas (direct file downloads)

Both are free and public. No registration required for Dataverse downloads.

### Download URLs

| Dataset | URL | Last Updated |
|---------|-----|-------------|
| Atlas Dataverse (all datasets) | https://dataverse.harvard.edu/dataverse/atlas | Various |
| Product Space Networks | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/FCDZBN | Sep 2024 |
| Growth Projections & Complexity Rankings | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XTAQMC | Various |
| Classifications Data | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/3BAL1O | Various |

### Variables Available

**Country-level (annual):**
- ECI (Economic Complexity Index) -- country-year
- ECI rankings

**Product-level:**
- PCI (Product Complexity Index) -- product-year
- Product Space coordinates (UMAP embeddings of proximity matrix)
- Product cluster assignments

**Product Space Networks:**
- Node data: product codes, (X, Y) coordinates, cluster names
- Proximity matrix: conditional probability of co-exporting (the key input for Product Space analysis)
- Coordinates represent UMAP embeddings where distances are meaningful

**Complexity Rankings:**
- ECI rankings through 2022 (latest available as of Atlas 10.0)

### Coverage
- **Countries:** All countries with sufficient trade data for complexity computation
- **Products:** HS 6-digit (HS92 and later revisions)
- **Time period:** ECI/PCI available from 1995 onward (based on BACI data)
- **Format:** CSV

### Feasibility Grade: A
Public, free, no registration for Dataverse downloads. Pre-computed metrics save substantial computation time. The Product Space proximity matrix is the key deliverable.

### Known Quality Issues
- ECI/PCI computation depends on the RCA threshold (standard = 1.0). The Growth Lab uses Method of Reflections with 20 iterations.
- The proximity matrix is based on conditional co-export probabilities and may change slightly across time periods depending on which base year is used.
- Product Space layout (UMAP coordinates) is for visualization; the underlying proximity matrix is what matters for analysis.
- Atlas 10.0 data appears to extend through 2022 trade data. More recent years may lag.
- HS concordance: the Growth Lab computes complexity using HS92 for the longest series. Concordance with later HS revisions (used in BACI) requires mapping.

### Fit for This Project
**Core data source for complexity metrics.** The pre-computed ECI, PCI, and proximity matrices are exactly what we need. Two approaches:
1. **Use pre-computed values** from the Dataverse (faster, reproducible, matches published Atlas rankings).
2. **Recompute from BACI** using the `economiccomplexity` R package (allows custom parameters, extends to 2024, ensures consistency with our trade data vintage).

Recommendation: Use pre-computed Growth Lab data as the baseline, then verify by recomputing from BACI. Report robustness to both approaches.

---

## Source 5: Observatory of Economic Complexity (OEC)

### Provider
OEC (oec.world), originally spun off from MIT Media Lab / Harvard Growth Lab. Now an independent commercial platform.

### Current Access Status
**Verified working, tiered access.** Free tier allows limited downloads from profile pages. Pro and Premium tiers provide bulk data, API access, and company-level data.

### Download URL
https://oec.world/en/resources/data

### Access Tiers

| Tier | Download | API | Bulk Data | Cost |
|------|----------|-----|-----------|------|
| Free | Limited (profile pages) | No | No | Free |
| Pro | From data explorer tools | Limited | No | Paid |
| Premium | Full | Full | Yes, company-level | Paid |

### Variables Available
- ECI and PCI rankings (trade, technology, research, software variants)
- Trade data (SITC2: 1962-2018; HS revisions: 1995-2024)
- World Development Indicators (from World Bank)
- Tariff data (from WITS)

### Coverage
- **Countries:** Global
- **Products:** HS 6-digit, SITC
- **Time period:** HS data 1995-2024, SITC 1962-2018
- **ECI rankings:** Through 2024

### Format
CSV, Excel, JSON (depending on tier).

### Feasibility Grade: B
Free tier is limited. Bulk download and API require paid subscription. The underlying trade data comes from the same sources (BACI/Comtrade) we already have access to. The complexity metrics can be recomputed. OEC's main value-add is visualization and the commercial data products.

### Known Quality Issues
- OEC computes ECI/PCI using its own methodology, which may differ slightly from the Growth Lab's published method.
- Multiple ECI variants (trade, technology, research, software) can cause confusion about which is being used.
- Data provenance is less transparent than the Growth Lab's Dataverse.

### Fit for This Project
**Supplementary / validation.** The free tier is sufficient for spot-checking ECI/PCI values and for visualization during presentation. Not suitable as a primary data source due to download restrictions and less transparent methodology. Use Harvard Growth Lab data instead.

---

## Source 6: R Package `economiccomplexity`

### Provider
Mauricio Vargas Sepulveda (maintainer). Published in JOSS (doi: 10.21105/joss.01866).

### Current Access Status
**Verified working.** Version 2.1.0 on CRAN, last updated February 18, 2026. All 13 CRAN checks pass. Actively maintained.

### Installation
```r
install.packages("economiccomplexity")
```

### GitHub
https://github.com/pachadotdev/economiccomplexity

### Documentation
https://pacha.dev/economiccomplexity/

### Key Functions

| Function | What It Computes |
|----------|-----------------|
| `balassa_index()` | Revealed Comparative Advantage (RCA) matrix |
| `complexity_measures()` | ECI and PCI via Method of Reflections or eigenvalue method |
| `proximity()` | Product-product proximity matrix (conditional co-export probability) |
| `complexity_outlook()` | Complexity Outlook Index and Complexity Outlook Gain |
| `projections()` | Network projections for country-space and product-space |

### Dependencies
- R >= 3.5
- `igraph` >= 2.0.0
- `Rdpack`
- Compiled code requires `cpp4r`, `armadillo4r`

### Included Data
- World trade data sample (from Open Trade Statistics)
- World GDP per capita (from World Bank)

### Feasibility Grade: A
Free, open source, on CRAN, well-documented, published in a peer-reviewed software journal. Computes all the complexity metrics we need directly from BACI trade data.

### Known Quality Issues
- Computational intensity: computing the full proximity matrix from HS6 bilateral trade for 200 countries and 5,000 products is memory-intensive. May require chunking by year or subsetting.
- Method of Reflections convergence depends on number of iterations (default may differ from Growth Lab's 20 iterations).
- Results should be validated against the Growth Lab's published ECI/PCI values to ensure consistency.

### Fit for This Project
**Computation engine.** This package allows us to:
1. Compute RCA, ECI, PCI, and proximity from our BACI data directly.
2. Ensure consistency between the trade data vintage we use and the complexity metrics.
3. Run robustness checks with different RCA thresholds (0.5, 1.0, 2.0) and different methods (reflections vs. eigenvalue).
4. Compute the Complexity Outlook Index (COI) and Complexity Outlook Gain (COG), which are directly relevant to our "stablecoin opportunity" scoring.

---

## Overall Assessment and Recommendations

### Primary Data Stack

| Purpose | Source | Priority |
|---------|--------|----------|
| Bilateral trade flows (HS6) | **CEPII BACI** (HS92 track, 1995-2024) | Primary |
| Gravity controls | **CEPII Gravity** (1948-2020) + extensions | Primary |
| ECI, PCI (pre-computed) | **Harvard Growth Lab Dataverse** | Primary (validation) |
| Proximity matrix | **Compute from BACI** via `economiccomplexity` | Primary |
| ECI, PCI (recomputed) | **`economiccomplexity` R package** from BACI | Primary |
| Spot checks / visualization | **OEC** (free tier) | Supplementary |
| Raw trade validation | **UN Comtrade** (API) | Backup |

### Key Decisions

1. **BACI over Comtrade.** BACI is the cleaned, reconciled version of Comtrade. There is no advantage to using raw Comtrade unless we need 2025 data before BACI updates.

2. **HS92 revision track.** Use HS92 for the longest consistent product classification (1995-2024). This matches the Growth Lab's complexity computation base and avoids concordance issues across HS revisions.

3. **Recompute complexity from BACI.** While pre-computed ECI/PCI from the Growth Lab is convenient, recomputing from our exact BACI vintage ensures internal consistency. Use Growth Lab values for validation.

4. **Extend gravity variables 2021-2024.** The CEPII Gravity dataset ends at 2020. Time-invariant bilateral variables (distance, language, colony, contiguity) carry forward. Time-varying variables (GDP, population, FTA status) must be updated from WDI and the WTO RTA database.

5. **Proximity matrix computation.** Compute the full product-product proximity matrix from BACI using `economiccomplexity::proximity()`. Validate against the Growth Lab's published Product Space network data.

### Coverage Gaps

| Gap | Severity | Mitigation |
|-----|----------|------------|
| BACI ends at 2024 (no 2025 data) | Low | Panel 2015-2024 is 10 years; 2025 data will arrive in BACI ~early 2027 |
| Gravity dataset ends at 2020 | Medium | Extend time-varying variables from WDI + WTO RTA database |
| Growth Lab ECI/PCI may lag (through 2022) | Low | Recompute from BACI through 2024 |
| Zero trade flows not in BACI | Expected | Standard practice: construct full i x j x k x t matrix, fill with zeros |
| HS concordance across revisions | Low | Stick with HS92 track throughout |

### Computation Considerations

The HS6 bilateral panel is large:
- ~200 exporters x 200 importers x ~5,000 products x 10 years = potential 2 billion observations
- BACI records only positive flows; typical count is ~50-100 million observations over 10 years
- PPML estimation at full HS6 with exporter-year and importer-year FE may require product-level or sector-level subsetting
- RCA and proximity computation is feasible but memory-intensive; plan for ~16-32 GB RAM

---

## Data Source Details for Access Instructions

### CEPII BACI
1. Go to http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37
2. Select HS revision (recommend HS92 for longest series)
3. Download CSV files (one per year or bundled)
4. No registration required
5. Timeline: Immediate

### CEPII Gravity
1. Go to http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8
2. Download CSV, RDS, or DTA format
3. No registration required
4. Timeline: Immediate

### Harvard Growth Lab Dataverse
1. Go to https://dataverse.harvard.edu/dataverse/atlas
2. Select specific dataset (Product Space Networks, Complexity Rankings, etc.)
3. Download CSV files directly
4. No registration required
5. Timeline: Immediate

### UN Comtrade API
1. Go to https://comtradedeveloper.un.org/
2. Register for free account
3. Obtain API subscription key
4. Use `comtradr` (R) or `comtradeapicall` (Python)
5. Free tier: 500 calls/day, 100,000 records/call
6. Timeline: ~1 day for registration + API key

### R Package `economiccomplexity`
1. `install.packages("economiccomplexity")`
2. Timeline: Immediate

---

*Explorer assessment complete. Ready for explorer-critic review.*
