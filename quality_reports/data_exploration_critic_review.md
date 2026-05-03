# Data Assessment Review — explorer-critic

**Date:** 2026-04-03
**Score:** 72/100
**Strike:** 1 of 3
**Verdict:** Below 80 threshold. Five issues to address.

---

## Issues Found

### ISSUE 1: Remittance Cost ≠ Trade Payment Cost (CRITICAL, -15)
RPW measures retail remittance fees (USD 200/500 P2P transfers). Trade payments involve letters of credit, documentary collections, B2B bank transfers of much larger amounts. The cost structure is entirely different. Using remittance costs as a proxy for trade payment friction is a conceptual stretch.

**Mitigation:** (a) Acknowledge this as a proxy limitation explicitly in the paper; (b) use BIS/CPMI correspondent banking density as a more direct measure of trade payment infrastructure; (c) show that results hold when using correspondent banking density alone; (d) frame RPW as capturing the "access" dimension (countries with high remittance costs also lack efficient trade payment infrastructure) rather than the "cost" dimension directly.

### ISSUE 2: Endogeneity of Payment Frictions Not Discussed (MAJOR, -10)
Payment frictions are endogenous to trade flows — countries that trade more develop better infrastructure. De-risking is proposed as "exogenous" but is itself partly driven by trade volumes.

**Mitigation:** (a) Use de-risking events (bank exits from specific corridors) as plausibly exogenous shocks, noting that regulatory-driven de-risking is less correlated with trade volumes than voluntary exits; (b) include lagged payment friction measures; (c) discuss IV strategies in the `/strategize` phase; (d) note that Ferrari Minesso et al. (2026) face the same challenge and use payment system establishment as the event.

### ISSUE 3: Validation Confounded by Income (MAJOR, -10)
Chainalysis adoption index is PPP-weighted. If SOS also correlates with income (likely), the validation is confounded. High rank correlation could reflect income, not genuine stablecoin adoption prediction.

**Mitigation:** (a) Partial correlation: validate SOS against Chainalysis conditional on GDP per capita; (b) within-income-group validation: does SOS predict adoption differences among similarly wealthy countries?; (c) use Google Trends as an alternative that is not PPP-weighted.

### ISSUE 4: Effective Panel Window Shorter Than Claimed (MAJOR, -5)
Full variable coverage is 2015-2019 (5 years), not 2015-2025. BIS/CPMI ends 2023, KAOPEN ends 2023, Doing Business ends 2019, WB Bilateral Remittances ends 2021.

**Mitigation:** (a) Primary panel: 2015-2023 with BACI + CEPII Gravity (extended) + FAS + KAOPEN + BIS/CPMI; (b) RPW available quarterly to 2025 for the subset of 367 corridors; (c) Doing Business as historical control (2015-2019 subpanel); (d) be transparent about temporal coverage in the paper.

### ISSUE 5: HS92 May Attenuate Complexity Signal (MAJOR, -10)
Products that didn't exist in 1992 (smartphones, lithium batteries, solar panels) are in residual categories under HS92. The complexity metrics should capture the actual product space of 2015-2025.

**Mitigation:** (a) Use HS12 (2012 revision) as the primary classification — it covers 2012-2024 in BACI and captures modern products; (b) use HS92 as robustness check for longer series; (c) recompute ECI/PCI/proximity under HS12 using `economiccomplexity` package.

---

## Additional Issues (MINOR)
- Panel balance: no coverage intersection analysis produced (-5)
- External validity: not discussed (-5)
- BIS/CPMI bilateral data availability uncertain — grade may be overstated (-5)
- Missing Enterprise Surveys and GSMA assessment (-8)

---

## Strengths Noted
- All sources verified accessible with URLs
- Strategic decisions sound (BACI preference, separate friction dimensions, stablecoin validation-only framing)
- Documentation quality high
- Feasibility grades mostly accurate

---

## Required Actions
1. Acknowledge remittance-trade cost gap; position correspondent banking as primary friction measure
2. Discuss endogeneity and IV strategy (defer to `/strategize`)
3. Plan conditional validation (partial on income)
4. Clarify effective panel window (2015-2023 realistic)
5. Switch primary HS revision from HS92 to HS12
6. Produce coverage intersection analysis (how many country-pairs have all variables?)
