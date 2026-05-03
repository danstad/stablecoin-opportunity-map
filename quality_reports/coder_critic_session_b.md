# Coder-Critic Review — Session B

**Date:** 2026-05-02
**Reviewer:** coder-critic
**Aggregate Score:** **87/100** (07 = 86, 11 = 88)
**Targets:**
- `scripts/python/07_estimation_extensive.py`
- `scripts/python/11_robustness.py`

---

## Script 1 — `07_estimation_extensive.py` — **86/100**

### Strategy alignment: MATCH
Spec 4 / extensive-margin hypothesis faithfully implemented (density + PCI + interaction + PF main + density:PF + triple). LPM + Logit pair. Country/product/year FE, country-clustered SEs.

### Sanity checks: PASS (with substantive flag)
- Density main effect +4.20 to +4.40 (LPM), +51.3 (Logit) — consistent with Hidalgo-Hausmann
- PF main effect −0.16 to −0.50, significant in E2/E3 — financial friction reduces RCA probability
- Triple interaction +0.274 (LPM, p=0.12), +1.09 (Logit, p=0.65) — **opposite hypothesized sign, not significant**
- Sample identical N=127,464 across all 5 specs

### Issues
| # | Issue | Deduction |
|---|---|---|
| 1 | PCI row empty in TeX output (universally absorbed by HS4+year FE) — not handled | −2 |
| 2 | ASCII "x" in TERM_LABELS instead of `$\times$` for TeX | −2 |
| 3 | Generic `Exception` swallow without traceback or NaN/Inf check | −3 |
| 4 | Triple interaction stdout flag does not state "opposite hypothesized sign" | −2 |
| 5 | PCI absorption not documented in stdout | −2 |
| 6 | Inline `print` via `log()` wrapper (style preference) | −1 |
| 7 | Status comment for null-result interpretation absent | −2 |

---

## Script 2 — `11_robustness.py` — **88/100**

### Strategy alignment: MATCH (with documented deviations)
Memo Tier 1 (R1, R2, R3 as baseline R0, R5 CBR-only, R6 RPW as script R3): all PASS.
Memo Tier 2 (R9 entrepots → R5, R12 pre-COVID → R8): PASS.
Memo Tier 3 (R16 OLS → R10, R19 commodities → R7, R25 China → R6): PASS.

### Sanity checks: PASS
- 10/10 specs converged
- 9/10 preserve negative sign at p<0.10
- R0 baseline = −0.308 (more negative than F0 from `12_falsification.py` because robustness omits ln_dist filter — sample composition, not bug)
- R6 (excl. China) = −0.160 — **half the headline magnitude**
- R10 OLS = −0.007 — expected PPML-vs-OLS gap
- R8 pre-COVID = −0.181 — sensible

### Issues
| # | Issue | Deduction |
|---|---|---|
| 1 | R4 (Method-of-Reflections PCI) skip not documented in script comment | −2 |
| 2 | R3 conceptual difference (RPW vs FDI-derisking) not flagged in stdout | −2 |
| 3 | R6 China dependence not specifically flagged | −2 |
| 4 | Sample-composition discrepancy with `12_falsification.py` (R0=−0.308 vs F0=−0.198) not documented | −3 |
| 5 | Generic `Exception` swallow without NaN/Inf check | −2 |
| 6 | `os.path.join` inconsistent with script 07's `pathlib` | −1 |

---

## Aggregate

| Script | Score | Status |
|---|---|---|
| `07_estimation_extensive.py` | 86 | PASS commit gate |
| `11_robustness.py` | 88 | PASS commit gate |
| **Average** | **87** | **PASS commit (≥80); below PR gate (≥90)** |

### Escalation: None

Both scripts produce correct, traceable outputs matching the strategy memo. The extensive-margin null and China-sensitivity are substantive findings, not bugs.

### Specific PR-gate fixes (advisory)

**07_estimation_extensive.py:**
1. Drop `pci_std` row from TERM_ORDER (universally absorbed by FE) OR add stdout note
2. Replace ASCII "x" with `$\times$` in TERM_LABELS
3. Add stdout banner: "TRIPLE INTERACTION: +0.274 — opposite hypothesized sign"
4. Use `traceback.format_exc()` and `np.isfinite()` check in per-spec try/except

**11_robustness.py:**
1. Document R4 skip in comment block
2. Add R3 stdout note: "RPW measures retail remittance prices, conceptually distinct"
3. Specifically flag R6 China dependence in stdout
4. Add docstring reconciling R0=−0.308 vs F0=−0.198 (no ln_dist filter)
5. Replace `os.path.join` with `pathlib` for cross-script consistency
6. Add `np.isfinite()` check on extracted coefs
