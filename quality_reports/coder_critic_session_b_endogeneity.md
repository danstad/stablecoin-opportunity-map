# Coder-Critic Review — `scripts/python/08_endogeneity.py`

**Date:** 2026-05-03
**Reviewer:** coder-critic
**Score:** **94/100** — above PR gate (≥90)

---

## Strategy alignment: MATCH
- Layer 1 (EN1, EN2): Lag-1, Lag-2 PPMLs match R sister script and falsification baseline
- Layer 2 (EN3): Lead-1 placebo correctly implemented
- Layer 3 (EN4): Auto-skip via `check_layer3_availability()` — `n_correspondents` not in panel; skipped with clear stdout note. Code path dormant but tested-in-shape so when CBR data lands, runs without re-engineering
- Sample comparability with F0: identical filter to `12_falsification.py` (pci_std AND ln_dist non-null), same MAX_TREATED_PAIRS=2000, MAX_CONTROL_PAIRS=1000, seed=42 → EN1/EN2/EN3 baselines directly comparable to F0=−0.198
- Lag/lead built BEFORE subsampling via period-shifted self-join (not pl.shift, so panel gaps don't silently produce wrong-period lags) — same 3000 pairs feed all three regressions ✓

## Sanity checks: PASS (with documented concern)
- EN1/EN2 negative interactions (−0.277, −0.274) — same direction as F0
- ~1.4× F0 magnitude, plausible for trade contracts negotiated in advance
- Strong significance (p=0.006, p=0.005)
- EN3 lead-test: −0.355, p=0.0005 (LARGER than contemporaneous). Script correctly flags this in stdout: `WARNING: possible anticipation / pre-trends in de-risked corridors`. As substantively documented, most likely persistent treatment status — real finding, not code bug. Script does NOT silently bury it.

## Code quality
All 12 categories pass with minor-only deductions:
- Decorative stdout dividers (−1)
- Bare `except Exception` swallows traceback class name (−1)
- Hand-rolled LaTeX writer rather than modelsummary/etable (−2)
- Placebo-failure flag is print-only, no machine-readable warning artifact (−2)

## Output standards
Booktabs-compliant. Bare tabular. No in-table notes. Stars per content-standards.md.

---

## Score: 94/100

| Component | Deduction |
|---|---|
| Decorative stdout dividers | −1 |
| Bare exception swallows class name | −1 |
| Hand-rolled LaTeX vs preferred packages | −2 |
| Placebo failure not machine-readable | −2 |

## Escalation: None — above PR gate (≥90)

## Recommended advisory fixes
1. Use `repr(e)` in error logging
2. Emit `paper/tables/08_endogeneity/PLACEBO_WARNING.txt` when |EN3 coef| > 0.5 × |F0|
3. Consider modelsummary/etable for table generation
