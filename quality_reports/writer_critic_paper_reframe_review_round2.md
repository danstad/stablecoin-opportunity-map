# Writer-Critic Review — Paper Reframe (Sections 01–08), Round 2

**Target:** `paper/main.tex` (with sections 01–08 + abstract + appendix)
**Round 1 report:** `quality_reports/writer_critic_paper_reframe_review.md` (50/100)
**Phase:** Execution (severity: HIGH)
**Reviewer:** writer-critic
**Round:** 2

---

## Score: 97/100 — APPROVE (PR gate clear)

**Verdict:** Seven of eight round-1 deductions are fully closed. All numerical claims in §05–§07 reconcile to source CSVs within rounding. Compile log confirms 0 errors, 0 undefined refs, 0 overfull hboxes, 42 pages. Two minor concerns remain: em-dash density (~20 instances; §08 lines 4/6 alone use 6 em-dashes in two sentences) and the §07 SOS top-20 table using `\scriptsize` (a borderline readability concession; could be addressed by moving CI columns to an appendix).

---

## Round-2 Verification of Round-1 Deductions

| # | Round 1 Issue | Deduction | Status |
|---|---------------|-----------|--------|
| 1 | "6/6 years" H2 kitchen-sink extrapolation | −15 | **CLOSED** |
| 2 | "five of six" yearly-significance count | −5 | **CLOSED** |
| 3 | Overfull \hbox 26.25pt §03 | −10 | **CLOSED** |
| 4 | Overfull \hbox 11.79pt §01 | −10 | **CLOSED** |
| 5 | §07 SOS table format | −5 | **CLOSED** |
| 6 | Title-page placeholders | −2 | **CLOSED** |
| 7 | Em-dash density | −2 | **PARTIALLY CLOSED (−2 retained)** |
| 8 | Overfull \hbox 6.20pt §04 | −1 | **CLOSED** |

Round-2 deductions: −2 (em-dash density) + −1 (SOS table sizing concern) = −3 → **97/100**

---

## Round-2 New Issues

### Issue 9: Em-dash density not materially reduced (−2)
~20 `---` instances remain across §01, §02, §04, §08. §08 lines 4 and 6 contain 6 em-dashes in two sentences. The writer's "5 of 15 replaced" was offset by other em-dashes not flagged in round 1.

### Issue 10: SOS top-20 table uses `\scriptsize` (−1, advisory)
Round 1 advised dropping `rank_range` and using `\small`. Writer dropped `rank_range` (good) but kept two CI rank columns (`Rank low`, `Rank high`), requiring `\scriptsize` to fit. Recommendation: move CI columns to an appendix table; revert main table to `\small` with 8 columns.

---

## Numerical Re-Verification

All claims reconcile to source CSVs within rounding:
- Panel coefficients (PB/PE/PF), Triple horse race (PH), Kitchen sink (PK)
- Yearly cross-sections F1/E1/B0/H2 for 2018–2023
- Composite SOS top 5: HTI 10.83, FJI 9.26, SYR 8.10, LBN 7.36, NIC 7.31
- Spearman correlations: 0.249 / 0.487 / 0.429
- Magnitude implied effects (−10.2%, +15.1%, −12.6%) ← match exp(γ)−1 of source coefficients

---

## What Passes

- Compile: 0 errors, 0 undefined refs, 0 overfull hboxes, 42 pages
- Anti-hedging clean
- Notation consistent ($\hat{\gamma}_{\text{FATF}}$, $\hat{\gamma}_{\text{AMLD}}$, $\hat{\gamma}_{\text{FDI}}$)
- Effect sizes cited with implied % trade-flow effect throughout
- §07 framing avoids "robust to γ choice" trap
- Working-paper format compliant
- Booktabs everywhere, threeparttable + tablenotes consistent

---

## Recommended Path Forward

The paper clears the PR gate (≥90). Two minor edits would clear the submission gate (≥95):
1. Em-dash spot-edit in §08 conclusion (6 → 2)
2. SOS table: move CI columns to appendix; revert main table to `\small` with 8 columns

Neither blocks PR or submission at the working-paper stage.
