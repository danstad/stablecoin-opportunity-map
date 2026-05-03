# Data Exploration: Macro Controls, Institutional Variables, and Stablecoin Validation

**Explorer Agent -- Macro/Validation Stream**
**Date:** 2026-04-03
**Phase:** Discovery

---

## Executive Summary

Eight data source categories were assessed for macro controls (gravity model), institutional variables, and stablecoin adoption validation. The macro controls are straightforward: WDI (Grade A), PWT 11.0 (Grade A), and WGI (Grade A) are all freely accessible, well-documented, and cover the countries and time periods needed. The binding constraint is stablecoin validation data. No public dataset provides clean, continuous, country-level stablecoin adoption measures. The best available option is the Chainalysis Global Crypto Adoption Index (Grade C) -- free as a report but requires manual extraction and is not stablecoin-specific. On-chain geographic data from Artemis/Allium (Grade C) is more direct but expensive and access-uncertain. The recommended strategy treats stablecoin data as validation-only (not estimation input), making even noisy proxies acceptable.

---

## Feasibility Grades Summary

| Source | Grade | Rationale |
|--------|-------|-----------|
| World Development Indicators (WDI) | **A** | Public API + bulk download, 200+ countries, all key controls |
| Penn World Table 11.0 | **A** | Public download, 185 countries, PPP GDP + TFP + capital stock |
| Worldwide Governance Indicators (WGI) | **A** | Public download, 200+ countries, 6 governance dimensions |
| Chainalysis Adoption Index | **C** | Free report but no CSV; not stablecoin-specific; manual extraction |
| CoinGecko / CoinMarketCap | **D** | No country-level data; exchange-level only |
| Artemis / Allium / Visa Onchain | **C** | Best geographic stablecoin data but enterprise pricing |
| Rajan-Zingales EFD | **B** | Published tables available; concordance to HS needed |
| Regulatory Timeline (combined) | **B** | Requires manual compilation from multiple free sources |

---

## Key Recommendations

1. **Assemble macro controls first** (WDI + PWT + WGI). This is 1--2 days of work and unblocks gravity model estimation.

2. **Begin Chainalysis extraction immediately.** Download the 2025 report, extract the 151-country ranking table. This is the primary validation variable.

3. **Contact Artemis for academic access.** If successful, geographic stablecoin volume data would be the strongest validation measure. Timeline: 2--4 weeks for a response.

4. **Build regulatory timeline in parallel.** Combine LoC, Atlantic Council, and manual research. Budget 1--2 weeks.

5. **Prepare Rajan-Zingales concordance.** Extract EFD from published tables; build HS-to-ISIC concordance. This is needed for the robustness check showing that product complexity (our channel) adds explanatory power beyond financial vulnerability.

---

## Detailed Assessments

See the following files for full details:
- `quality_reports/data-assessment/stablecoin-opportunity-map/data_sources.md` -- Ranked sources with feasibility grades
- `quality_reports/data-assessment/stablecoin-opportunity-map/data_dictionary.md` -- Variable definitions for top candidates
- `quality_reports/data-assessment/stablecoin-opportunity-map/access_instructions.md` -- Download URLs, API endpoints, timelines

---

## Can We Construct a Credible Stablecoin Adoption Measure?

**Short answer: Not easily, but we have a workable path.**

The best strategy is to frame stablecoin adoption data as validation evidence, not as a dependent variable in the main estimation. Our model produces a Stablecoin Opportunity Score (SOS) for each country x industry pair. Validation asks: do countries with high predicted SOS also show high observed stablecoin activity?

**Primary validation:** Chainalysis 2025 index (151 countries, ordinal ranking, geometric mean of 4 sub-indices). Show rank correlation between predicted SOS and observed adoption.

**Secondary validation (if accessible):** Artemis geographic stablecoin volumes. Show that countries with high predicted SOS receive larger stablecoin inflows.

**Robustness validation:** Google Trends for stablecoin-related search terms by country. Free, noisy, but independently constructed.

This three-pronged approach provides credible validation even without a perfect stablecoin adoption dataset.
