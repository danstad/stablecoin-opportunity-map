# Writer-Critic Review (Round 3, post-Session A) — paper/main.tex

**Score: 37/100** (Round 1 = 50; Round 2 = 97; Round 3 = 37 — regression from stale text propagation)

**Verdict:** Session A added strong new §06 falsification + §07 quadrant content with clean numerical traceability, but failed to propagate the new Q1 count (60, not 22) and Q1 top-10 list back into abstract, intro, and conclusion — producing high-visibility numerical inconsistencies that block PR (≥90) and submission (≥95) gates.

---

## Critical Issues

### Issue 1 (−25): Abstract, intro, conclusion say "22 actionable" countries; new §07 table reports 60

Files:
- `paper/main.tex` line 17 (abstract): "Twenty-two countries fall in the actionable feasibility quadrant"
- `paper/sections/01_introduction.tex` line 16
- `paper/sections/08_conclusion.tex` line 4

Evidence: `paper/tables/14_feasibility_quadrant/quadrant_summary.tex` Q1 row = **60 countries**. §07 line 140 also states 60.

### Issue 2 (−10): Conclusion top-5 list bears no relation to new top-10

File: `paper/sections/08_conclusion.tex` line 6

Current: "Kenya, Philippines, Bulgaria, Canada, and Australia top the deployment list"
Evidence: `actionable_top10.tex` lists PAN, TTO, ARE, BHR, GEO, SMR, URY, OMN, ARM, KWT.

### Issue 3 (−15): AMLD "10–21%" yearly range stale; actual max is 14.9%

Files: `paper/sections/01_introduction.tex` line 14; `paper/sections/08_conclusion.tex` line 4

Evidence: yearly AMLD coefficients +0.096 to +0.139 → +10.1% to +14.9%, not 10–21%.

## Major / Minor Issues

### Issue 4 (−5): FATF "10–25%" understates upper bound

File: `paper/sections/01_introduction.tex` line 14
Evidence: yearly FATF range −0.115 to −0.354 → magnitude 10.9% to 29.8%; should be "10–30%".

### Issue 5 (−5): "Diplo positive sign" claim does not specify spec

Files: abstract, `01_introduction.tex` line 12, `04_empirical_strategy.tex` line 57
Evidence: Yearly H2 cross-sections show diplo × PCI = +0.062 to +0.086. Panel kitchen-sink shows diplo × PCI = −0.016 (null). The text omits this distinction.

### Issue 6 (−3): Q1 lowest-mean-SOS not disclosed

File: `paper/sections/07_stablecoin_opportunity.tex` lines 140–142
Evidence: `quadrant_summary.tex` shows Q1 mean SOS = −2.181 (the lowest of four quadrants). Reader of the table sees a counterintuitive number with no narrative explanation.

---

## Positive Findings

1. **§06 falsification numerical traceability is exact** — all 6 placebo coefficients and p-values match `falsification_panel.csv` to 3 decimals.
2. **§06 partial-falsification framing is honest** — explicit "partial falsification, not a clean win"; contig/colony loadings framed as institutional-tie loadings, not refutation.
3. **§07 quadrant counts and top-10 list match tables exactly** (60/23/15/63; PAN/TTO/ARE/BHR/GEO/SMR/URY/OMN/ARM/KWT).
4. **All 6 new figure files exist**; `fig:sos_decomp_main` label avoids appendix collision.
5. **Notation consistency** maintained.
6. **Em-dash density decreased** (Round 2 ~20, now ~10).
7. **No hedging language**.
8. **Compilation clean**: 0 errors, 0 undefined refs, 0 overfull hboxes.

---

## Routing

These are stale-text propagation failures, not writer-quality issues. **Route to writer for one targeted update pass; do not escalate.**

### Required edits

1. Replace "22" → "60" in abstract, intro line 16, conclusion line 4
2. Replace Kenya/Philippines/Bulgaria/Canada/Australia list in conclusion line 6 with PAN, TTO, ARE, BHR, GEO
3. Replace AMLD "10–21%" → "10–15%" in intro line 14, conclusion line 4
4. Replace FATF "10–25%" → "11–30%" in intro line 14
5. Specify "in the yearly kitchen-sink cross-sections" when claiming diplo positive sign in intro line 12 and §04 line 57
6. Add one sentence to §07 quadrant subsection explaining why Q1 mean SOS is low (high-SOS countries select into Q2/Q4 by construction)

After fixes, expected score returns to 95+ band.
