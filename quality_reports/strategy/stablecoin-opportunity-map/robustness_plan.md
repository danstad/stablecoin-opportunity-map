# Robustness Plan: Stablecoin Opportunity Map

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## Robustness Checks (Ordered by Priority)

### Tier 1: Must-Have (present in main paper or appendix)

| # | Check | Specification Change | Rationale | Table |
|---|-------|---------------------|-----------|-------|
| R1 | Lagged payment frictions (t-1) | Replace $PF_{ij,t}$ with $PF_{ij,t-1}$ in Spec 3 | Address contemporaneous reverse causality | Endogeneity table |
| R2 | Lagged payment frictions (t-2) | Replace $PF_{ij,t}$ with $PF_{ij,t-2}$ in Spec 3 | Deeper lag for stronger exogeneity argument | Endogeneity table |
| R3 | Reduced form: de-risking x PCI | Replace $PF$ with binary de-risking indicator | Cleaner causal test without exclusion restriction | Endogeneity table |
| R4 | Rajan-Zingales horse race | Add $PF_{ij,t} \times EFD_p$ alongside $PF_{ij,t} \times PCI_p$ | Distinguish complexity from financial vulnerability | Main table extension |
| R5 | Correspondent banking only (drop RPW) | Use only BIS/CPMI CBR density as friction | Address "remittance != trade costs" critique | Appendix table |
| R6 | RPW only (drop CBR) | Use only RPW remittance cost as friction | Show results are not artifact of one measure | Appendix table |

### Tier 2: Should-Have (present in appendix)

| # | Check | Specification Change | Rationale | Table |
|---|-------|---------------------|-----------|-------|
| R7 | HS12 2-digit aggregation | Aggregate trade to ~97 chapters; recompute PCI at 2-digit | Robustness to product aggregation (coarser) | Appendix |
| R8 | HS12 6-digit subsample | Estimate at 6-digit for top 500 corridors | Robustness to product aggregation (finer) | Appendix |
| R9 | Exclude entrepot economies | Drop SGP, HKG, ARE, NLD, BEL from sample | Re-export trade distorts complexity and trade patterns | Appendix |
| R10 | Subsample: Low-income countries | Restrict to LIC + LMIC exporters | Check if effects driven by developing countries | Appendix |
| R11 | Subsample: High-income countries | Restrict to HIC exporters | Check if effects present in developed economies | Appendix |
| R12 | Panel window: 2015-2019 (pre-COVID) | Restrict to pre-COVID period | COVID disrupted trade patterns and payment systems | Appendix |
| R13 | RCA threshold = 0.5 | Use RCA >= 0.5 instead of >= 1 for extensive margin | Sensitivity of extensive margin to threshold | Appendix |
| R14 | RCA threshold = 2.0 | Use RCA >= 2.0 instead of >= 1 for extensive margin | Sensitivity of extensive margin to threshold | Appendix |

### Tier 3: Nice-to-Have (available upon request)

| # | Check | Specification Change | Rationale |
|---|-------|---------------------|-----------|
| R15 | Method of Reflections for PCI | Replace eigenvalue PCI with MR PCI | Alternative complexity computation |
| R16 | OLS on log(1+trade) | Replace PPML with OLS | Standard robustness (PPML is preferred) |
| R17 | Multi-way clustering (exporter x importer) | Replace pair clustering with two-way | Alternative inference |
| R18 | Add product x pair tariff controls | Include applied tariff from TRAINS/WITS | Rule out tariff-driven confounding |
| R19 | Exclude primary commodities (HS 1-27) | Drop resource-based products | These are low-PCI and traded through established channels |
| R20 | Panel window: 2017-2023 | Drop 2015-2016 | Sensitivity to starting year |
| R21 | KAOPEN-based friction measure | Use capital account openness as friction | Alternative regulatory friction dimension |
| R22 | Combined friction index (PCA) | PCA of CBR, RPW, FAS, KAOPEN | Composite friction measure |
| R23 | Weighted vs. unweighted PPML | Compare default PPML (quasi-ML) with explicit weights | Weighting sensitivity |
| R24 | Country-pair x product clustering | Cluster at finest level | Most conservative inference |
| R25 | Drop China | China dominates trade flows and has unique payment/crypto regime | Check if results driven by single country |

---

## Robustness Reporting Strategy

**Main paper body:**
- Table with Spec 1, 2a, 2b, 3, 3+RZ (5 columns)
- Table with endogeneity: lag-1, lag-2, reduced form, IV (4 columns)

**Online appendix:**
- All Tier 2 checks in individual appendix tables
- Summary table showing key coefficient (alpha_2) across all specifications
- "Coefficient stability" plot: point estimates and CIs for alpha_2 across all robustness checks

**Available upon request:**
- Tier 3 checks with code to reproduce
