# Strategy Review — strategist-critic

**Date:** 2026-04-03
**Score:** 82/100 (PASSES 80 threshold)
**Strike:** 0 of 3

---

## Verdict

Strategy is fundamentally sound. Four major issues to address, all fixable. Zero critical issues. The within-pair cross-product identification for the interaction term is well-conceived and the causal-descriptive decomposition is exemplary.

---

## Major Issues (4)

### 1. Fix PCI to Base Period (-5)
Time-varying PCI computed from BACI creates a reflection problem: trade → RCA → PCI → regression predicting trade. Fix PCI to a base-period average (2015-2017) and hold constant. This is the single most important methodological fix.

### 2. Add Nunn (2007) Contract Intensity Horse Race (-5)
Complex products are relationship-intensive (Nunn 2007). Payment friction may proxy for weak contract enforcement. Add PF × ContractIntensity alongside PF × PCI and PF × EFD (Rajan-Zingales). Most likely referee objection not currently addressed.

### 3. SOS Uncertainty Quantification Missing (-5)
No confidence intervals on SOS rankings. Country ranked #5 vs. #15 may not be statistically distinguishable. At minimum: sensitivity of top-20 ranking to α₂ ± 1 SE. Ideally: bootstrap.

### 4. IV in PPML Inconsistency (-3)
Standard 2SLS is inconsistent in PPML. Promote reduced form (de-risking × PCI) as primary causal robustness. If IV reported, use control function approach (Wooldridge 2015), not 2SLS on log(1+trade).

---

## Minor Issues (8, no deductions at Strategy phase)
- Within-pair PF variation statistics needed
- SOS weighting by endogenous trade flows — discuss limitation
- Exclusion restriction for de-risking IV weaker than presented
- Multi-way clustering should be Tier 2
- Joint presentation of falsification tests
- Main effect interpretation with standardized PCI
- No Oster bounds / coefficient stability
- No leave-one-out country test

---

## Strengths Noted
1. Within-pair cross-product identification is the right approach
2. Causal-descriptive decomposition (Section 2.3) is exemplary
3. Falsification tests are well-designed and comprehensive
4. Tiered endogeneity strategy shows good econometric judgment
5. Honest assessment that reduced form may be cleaner than IV
