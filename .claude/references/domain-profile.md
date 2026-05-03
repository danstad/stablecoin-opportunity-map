# Domain Profile

## Field

**Primary:** International/Trade Economics, Economic Complexity
**Adjacent subfields:** Development Economics, Fintech/Digital Finance, Monetary Economics

---

## Target Journals (ranked by tier)

| Tier | Journals |
|------|----------|
| Top-5 | AER, Econometrica, JPE, QJE, REStud |
| Top field | Journal of International Economics, Journal of Development Economics, Review of Economics and Statistics |
| Strong field | Journal of International Money and Finance, IMF Economic Review, World Bank Economic Review |
| Specialty | Research Policy, Journal of Financial Economics (fintech), Journal of Monetary Economics |

---

## Common Data Sources

| Dataset | Type | Access | Notes |
|---------|------|--------|-------|
| UN Comtrade | Bilateral trade, HS 6-digit | Public API | Primary trade data; use CEPII BACI for cleaned version |
| CEPII BACI | Harmonized bilateral trade | Public download | Reconciled mirror flows, HS 6-digit |
| CEPII Gravity | Gravity variables | Public download | Distance, language, colony, contiguity, FTA |
| OEC / Growth Lab | ECI, PCI, Product Space, proximity | Public download | Pre-computed complexity metrics |
| World Bank RPW | Corridor-level remittance fees | Public CSV | Remittance Prices Worldwide |
| World Bank Bilateral Remittances | Remittance volumes by corridor | Public Excel | Annual bilateral matrix |
| IMF Financial Access Survey | Banking infrastructure by country | Public CSV | ATMs, branches, accounts per capita |
| FSB/BIS | Correspondent banking relationships | Reports + CSV | De-risking data |
| Chinn-Ito Index | Capital account openness | Public CSV | Updated periodically |
| WDI / PWT | GDP, population, inflation, institutions | Public API | Standard macro controls |
| Chainalysis Adoption Index | Crypto/stablecoin adoption by country | Public report | For validation, not estimation |

---

## Common Identification Strategies

| Strategy | Typical Application | Key Assumption to Defend |
|----------|-------------------|------------------------|
| PPML Gravity | Bilateral trade estimation with zeros and heteroskedasticity | Conditional mean correctly specified (Santos Silva & Tenreyro, 2006) |
| Augmented gravity with friction interactions | Payment friction effects conditional on product complexity | Payment friction proxies are exogenous to bilateral trade (needs IV or controls) |
| Event study / DiD | Regulatory shocks (crypto bans, CBDC launches, de-risking events) | Parallel trends in trade flows pre-event |
| Out-of-sample validation | Estimate on 2015-2020, predict 2021-2025 | Structural stability of gravity parameters |

---

## Field Conventions

- Gravity models estimated with PPML (Santos Silva & Tenreyro, 2006), not OLS on log trade
- Include exporter×year and importer×year fixed effects for structural gravity
- Report both intensive margin (trade volume) and extensive margin (new trade links)
- Cluster standard errors at country-pair level
- Economic complexity computed from RCA matrix using Method of Reflections
- Product Space proximity based on conditional probability of co-exporting
- Always discuss both statistical and economic significance of trade cost elasticities

---

## Notation Conventions

| Symbol | Meaning | Anti-pattern |
|--------|---------|-------------|
| $X_{ijpt}$ | Bilateral trade flow from i to j in product p at time t | Don't use $T$ for trade (conflicts with time) |
| $\text{RCA}_{cp}$ | Revealed Comparative Advantage of country c in product p | Subscript order matters |
| $\text{ECI}_c$ | Economic Complexity Index of country c | |
| $\text{PCI}_p$ | Product Complexity Index of product p | |
| $\phi_{ij}$ | Proximity between products i and j in Product Space | |
| $\tau_{ijt}$ | Trade costs / payment friction between countries i and j at time t | |
| $\text{SOS}_{cp}$ | Stablecoin Opportunity Score for country c, product p | Novel metric |

---

## Seminal References

| Paper | Why It Matters |
|-------|---------------|
| Hidalgo et al. (2007, Science) | Product Space — foundational network structure |
| Hidalgo & Hausmann (2009, PNAS) | ECI/PCI — complexity measurement |
| Hausmann et al. (2014) | Atlas of Economic Complexity — comprehensive methodology |
| Anderson & van Wincoop (2004) | Trade costs — structural gravity framework |
| Santos Silva & Tenreyro (2006) | PPML — proper gravity estimation |
| Head & Mayer (2014) | Gravity equations — handbook chapter |
| Cerutti et al. (2024, IMF WP) | Cross-border crypto flow measurement |
| Graf von Luckner, Reinhart & Rogoff (2023, JME) | New-age international capital flows |

---

## Field-Specific Referee Concerns

- "Why not just use standard gravity without complexity?" — must show complexity adds explanatory power
- "RCA threshold sensitivity" — results should be robust to RCA cutoff (0.5, 1.0, 2.0)
- "Endogeneity of payment frictions" — frictions may respond to trade, not just cause it
- "Product Space stability" — proximity matrix should be stable across time periods
- "Stablecoin data quality" — on-chain data has geographic attribution problems
- "External validity" — do results from high-adoption countries generalize?

---

## Quality Tolerance Thresholds

| Quantity | Tolerance | Rationale |
|----------|-----------|-----------|
| Point estimates | 1e-6 | Numerical precision in PPML |
| Standard errors | 1e-4 | Clustering variability |
| ECI/PCI scores | 1e-3 | Method of Reflections convergence |
| RCA threshold | Binary at 1.0 (robustness at 0.5, 2.0) | Standard practice |
