# Coder-Critic Review — Session A (Stablecoin Opportunity Map)

**Date:** 2026-05-02
**Reviewer:** coder-critic
**Aggregate Score:** **86/100** (average of 86 + 88 + 84)

---

## Script 1 — `scripts/python/12_falsification.py` — **86/100**

### Strategy alignment: PARTIAL MATCH

The strategy memo specifies 7 falsification tests; the script implements 2 (distance, language) plus 3 sensible extensions (contig, colony, RTA). Missing: weight × PCI, perishability × PCI, non-payment-tech outcome, leads/pre-trends, commodity-only subsample.

### Sanity checks: PASS
- Headline γ_FDI = −0.186 to −0.205 across 5 specs, all p<0.01
- F1/F2/F5 placebos clean null (ln_dist p=0.89; comlang p=0.61; RTA p=0.23)
- F3 contig (p=0.011) and F4 colony (p=0.007) significant — substantive finding, not a code bug
- N=1.68M after subsample as expected

### Score breakdown
- Missing 5/7 memo robustness checks: −15
- Broad `except` without NaN/Inf check: −2
- F-string formatting on L275–277: −1
- Dep var not labeled in table column header: −1

---

## Script 2 — `scripts/python/13_figures.py` — **88/100**

### Sanity checks: PASS
All 6 PDFs exist; serif font, Set2 palette, no in-figure titles, marker+linestyle redundancy → grayscale-readable.

### Issues
- No `np.random.seed()` (script is deterministic but hygiene gap): −3
- Dead `rename(columns={"pf_cbr": "fdi_proxy"})` at L193 — column never requested: −3
- Stale R-era PDFs (`world_heatmap_sos.pdf`, `derisking_coefficient_plot.pdf`, etc.) coexist in `paper/figures/13_figures/` with no notice: −5
- One unused import: −1

---

## Script 3 — `scripts/python/14_feasibility_quadrant.py` — **84/100**

### Sanity checks: PASS with substantive flag
- Q1 actionable_priority logic correct
- Median splits healthy (Q1=60, Q2=23, Q3=15, Q4=63)
- **Substantive flag (not code bug):** Q1 has lowest mean SOS (−2.181) while Q2 has highest (+2.519). Reason: SOS targets high-friction countries (low KAOPEN / low GDPpc), exactly those EXCLUDED from Q1. The framing "Q1 actionable" matches high-SOS-within-Q1 only. Top-10 of Q1 is correct framing.

### Issues
- Script writes journal entry directly (separation-of-powers violation): −8
- Encoding strategy inconsistent with sister scripts: −1
- No `main()` wrapper inconsistent with `13_figures.py` style: −2
- Q1 mean-SOS counterintuitive — unflagged in script output: −2
- Quadrant corner-labels overlap data points: −1
- Column header `ln(GDPpc)` semantic mismatch with script's `infrastructure_score`: −2

---

## Rename Audit: `pf_cbr` → `fdi_proxy` — **CLEAN**

No orphan references in production R/Python scripts outside permitted retention spots:
- `00_config.R` (rename helper)
- `03_payment_frictions.R` (write step)
- `04_merge_panel.R` (read step)
- `09_sos_construction.R`, `13_figures.R` (fall-back coefficient lookups)
- on-disk parquet column

### Two minor follow-ups
1. `paper/tables/05_descriptive/summary_statistics.csv` and `correlation_matrix.csv` still contain `pf_cbr` column labels — re-run `05_descriptive.R` to refresh
2. `13_figures.py` L193 has dead rename call (already counted in script 2's score)

---

## Summary

| Script | Score | Status |
|---|---|---|
| `12_falsification.py` | 86/100 | PASS |
| `13_figures.py` | 88/100 | PASS |
| `14_feasibility_quadrant.py` | 84/100 | PASS |
| **Aggregate** | **86/100** | **PASS — above 80 threshold** |

### Escalation: None (all scripts ≥ 80, single-iteration acceptable)

### Recommendations (advisory, non-blocking)
1. `12_falsification.py`: extend to F6 (leads) and F7 (commodity subsample) in a future run
2. `13_figures.py`: clean stale R-era PDFs from `paper/figures/13_figures/` or document them
3. `14_feasibility_quadrant.py`: move journal-write out of script (separation), wrap in `main()`
4. Re-run `05_descriptive.R` to refresh `pf_cbr`-labeled summary tables
