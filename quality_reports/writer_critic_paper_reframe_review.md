# Writer-Critic Review — Paper Reframe (Sections 01–08)

**Target:** `paper/main.tex` (with sections 01–08 + abstract)
**Plan executed:** `quality_reports/plans/2026-05-01_paper-reframe-points-1-2-3.md`
**Phase:** Execution (severity: HIGH)
**Reviewer:** writer-critic
**Round:** 1

---

## Score: 50/100 — REVISE

**Verdict:** The reframe around three-pronged identification is conceptually sound and the headline numbers in the abstract/§05 panel coefficients reconcile exactly with `confounder_panel.csv`. The §07 framing correctly avoids the "robust to γ choice" trap and explicitly addresses ρ(FDI, FATF) = 0.249. However, two unsupported "6/6 years" claims extrapolate beyond data that exists in `confounder_yearly.csv` (H2 rows present only for 2018–2020), one yearly-significance count is internally inconsistent (§05 says "five of six" but all six pass p<0.01), the §07 SOS top20 table breaks the `threeparttable`/`tablenote{}` convention, and two overfull hboxes exceed the 10pt threshold.

---

## Deduction Rubric

| # | Issue | Severity | Deduction |
|---|-------|----------|-----------|
| 1 | "6/6 years" extrapolation for H2 kitchen-sink yearly diplo_disagreement and AMLD claims (data only exists 2018–2020) | Major (Claims-Evidence) | −15 |
| 2 | §05 line 14 says "five of six estimates significant at the 1% level" — all six F1 FATF p-values are <0.01 | Major (Claims-Evidence internal inconsistency) | −5 |
| 3 | Overfull \hbox (26.25pt) at §03 lines 55–56 | Critical (LaTeX) | −10 |
| 4 | Overfull \hbox (11.79pt) at §01 lines 10–11 | Critical (LaTeX) | −10 |
| 5 | §07 SOS top20 table uses `\resizebox` outside `threeparttable` | Major (Table standards) | −5 |
| 6 | Author/affiliation/email/seminar placeholders unfilled in `main.tex` lines 4–6 | Minor (Polish) | −2 |
| 7 | Em-dash density (15 `---` across 8 sections) — moderate AI-tell flag | Minor (Writing) | −2 |
| 8 | Overfull \hbox (6.20pt) at §04 lines 30–31 | Minor (LaTeX) | −1 |
| | **Total** | | **−50 → Score 50/100** |

---

## Detailed Findings

### Issue 1 — H2 kitchen-sink "6/6 years" extrapolation
- **Files:** `05_results.tex` line 47; `06_robustness.tex` line 20
- **Evidence:** `confounder_yearly.csv` H2 rows only cover 2018–2020. Numeric ranges are correct for 2018–2020.
- **Fix:** Replace "6/6 years" / "every year from 2018 to 2023" with "every estimated year (2018–2020)".

### Issue 2 — FATF yearly-significance count
- **File:** `05_results.tex` line 14
- **Evidence:** F1 yearly p-values: {1.0e-10, 0, 0, 1.19e-5, 1.82e-7, 1.96e-4} — all <0.01.
- **Fix:** "all six significant at the 1% level. The two weakest-magnitude years, 2021 and 2023…"

### Issue 3 — Overfull hbox 26.25pt
- **File:** `03_data.tex` lines 55–56
- **Fix:** Rephrase to break the unbreakable phrase, e.g., "(population-weighted, logged)".

### Issue 4 — Overfull hbox 11.79pt
- **File:** `01_introduction.tex` lines 10–11
- **Fix:** "Pseudo-Maximum Likelihood (PPML)" → discretionary hyphen `Pseudo-Max\-imum`.

### Issue 5 — §07 table format
- **File:** `07_stablecoin_opportunity.tex` lines 49–59
- **Fix:** Convert to `threeparttable`, drop the `Range` column (redundant), use `\small` instead of `\resizebox`. Move notes into `\begin{tablenotes}`.

### Issue 6 — Title-page placeholders
- **File:** `main.tex` lines 4–6
- **Fix:** Either fill with the project's standing values or remove the `\thanks{}` for now.

### Issue 7 — Em-dash density
- **Fix:** Spot-replace ~5 instances with commas/semicolons.

### Issue 8 — Overfull hbox 6.20pt
- **File:** `04_empirical_strategy.tex` lines 30–31
- **Fix:** Discretionary hyphen on `customer-due-dili\-gence` or remove the first hyphen.

---

## What Passes

- Notation consistency across sections
- Headline panel coefficients reconcile to `confounder_panel.csv`
- Triple horse race numbers match row PH
- Kitchen-sink panel coefficients match row PK
- Composite top 5 matches CSV
- Spearman correlations match CSV
- §07 framing avoids "robust to γ choice"
- Anti-hedging clean (no "interestingly", "arguably", "robust to")
- AI-tells minimal (no "delve", "leverage", "unprecedented")
- Working-paper format compliant (12pt, 1in, doublespacing, titling, JEL/keywords)
- Contribution statement on page 1
- Effect sizes cited with interpretive scale
- 0 errors, 0 undefined refs at compile

---

## Recommended Fix Order

1. Issue 1 (two locations) — soften to "(2018–2020)"
2. Issue 2 — correct yearly-significance phrasing
3. Issues 3, 4, 8 — overfull hbox fixes
4. Issue 5 — convert §07 table to threeparttable
5. Issue 6 — fill or remove placeholders
6. Issue 7 — em-dash spot-edit

After these fixes, expected score is approximately **92/100** (PR gate clear).
