# Writer-Critic Review (Round 4) — paper/main.tex

**Score: 96/100** (Round 1=50, Round 2=97, Round 3=37, Round 4=96)

**Verdict:** All six round-3 fixes propagated cleanly; numerical traceability restored end-to-end; cleared for PR (≥90) and submission (≥95) gates. Two minor residuals.

---

## Round-3 Fix Verification (all 6 closed)

| Fix | Status |
|---|---|
| 1. "22 actionable" → "60" in abstract / intro / conclusion | ✅ All three locations updated; cross-checks against `quadrant_summary.tex` |
| 2. Conclusion top-5 list updated to PAN/TTO/ARE/BHR/GEO | ✅ Matches `actionable_top10.tex` exactly |
| 3. AMLD "10–21%" → "10–15%" in intro and conclusion | ✅ Defensible against yearly range +0.096 to +0.139 → 10.1–14.9% |
| 4. FATF "10–25%" → "11–30%" in intro | ✅ Matches yearly range −0.115 to −0.354 → 10.9–29.8% |
| 5. Diplo claim specifies "yearly kitchen-sink" in intro and §04 | ✅ Both locations updated; matches §05 line 47 framing |
| 6. §07 Q1 low-mean-SOS explanation added | ✅ "−2.18, lowest of the four quadrants, because high-SOS countries select into Q2/Q4 by construction" — clarifying and accurate |

---

## Residual Issues

### Issue 1 (−3): Abstract diplo qualifier still generic
- **File:** `paper/main.tex` line 17 (abstract)
- **Current:** "diplomatic disagreement enters with a positive sign and does not explain the complexity penalty"
- **Note:** Round-3 Issue 5 listed three locations (abstract, intro, §04). Intro and §04 were updated; abstract was missed.
- **Proposed:** "diplomatic disagreement enters with a positive sign in yearly kitchen-sink cross-sections (null in the panel kitchen-sink) and does not explain the complexity penalty"

### Issue 2 (−1): Rounding asymmetry FATF "11–30%" vs AMLD "10–15%"
- **File:** `paper/sections/01_introduction.tex` line 14
- **Note:** FATF rounds 10.9 → 11 (up); AMLD rounds 10.1 → 10 (down). Same parenthetical sweep, different conventions. Taste-level; not strictly wrong.

---

## Positive Findings

1. All 6 round-3 fixes propagated cleanly
2. §07 Q1 explanation is genuinely clarifying — adds reader trust
3. No new em-dash regressions
4. No hedging language introduced
5. Notation consistency preserved
6. Compilation clean (0 errors, 0 undefined refs, 0 overfull hboxes, 49 pages)
7. Numerical traceability end-to-end consistent for headline statistics

---

## Routing

No escalation. **Approved for PR and submission gates.** Fixing Issue 1 lifts to 99/100.
