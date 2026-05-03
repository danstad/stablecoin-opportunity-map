---
status: APPROVED 2026-05-01
date: 2026-05-01
scope: points 1–3 (reframe sections 01–08, interpret AMLD, recompute SOS)
decisions:
  - Part A: regulatory clarity/harmonization frame for AMLD (recommended)
  - Part C: Option C — composite SOS with AMLD-positive corridors down-weighted
---

# Paper Reframe Plan — Three-Pronged Identification

## Context

The 2026-04-06 confounder estimation produced three coefficients, all robust across years and pair-FE panel:

| Instrument | Yearly range | Panel (pair FE) | Interpretation |
|---|---|---|---|
| FATF greylist × PCI | −0.08 to −0.35 *** | −0.108 * | **Cleanest** payment-friction shock (binary, exogenous AML reviews) |
| EU AMLD × PCI | +0.10 to +0.21 *** | +0.141 ** | **Regulatory harmonization** — friction reduction → complex trade gain |
| FDI-derisked × PCI | −0.21 to −0.37 *** | −0.135 ** | Broad reduced form, survives triple horse race |

The current paper (`paper/main.tex` and `sections/01–08`) leads with FDI-derisked alone. The reframe re-spines the paper around all three, treating AMLD as a **symmetric counterpoint** rather than a confounder.

## Part A — AMLD interpretation (decide before rewriting)

**Recommended primary frame: regulatory-clarity / harmonization.**
AMLD4 (effective 2017) imposed common KYC/AML standards across EU. Complex trade — which passes through more compliance gates — gains disproportionately when those gates are standardized. This is the **mirror image** of the FATF mechanism: friction up hurts complex trade, friction down helps it.

Alternative interpretations to acknowledge:
- **(ii) Diversion:** Complex trade rerouted into EU corridors as non-EU corridors got greylisted. Testable by checking whether the AMLD effect grows after major FATF designations (Pakistan 2018, UAE 2022). Defer to robustness, not main text.
- **(iii) Composition:** EU recovery from sovereign-debt crisis. Pair FEs absorb time-invariant corridor traits, and the panel coefficient (+0.141, p=0.04) survives those FEs. Address briefly in §6.

**Why this is a stronger paper than the original frame:** symmetric evidence — friction up hurts, friction down helps — is the cleanest causal-mechanism design. FATF is the natural-experiment plaintiff; AMLD is the natural-experiment defendant.

## Part B — Section-by-section changes

| Sec | Current frame | New frame | Effort |
|---|---|---|---|
| 01 Intro | γ = −0.284 (single) headline | Three-pronged: FATF, AMLD, FDI. Symmetric mechanism. New contribution #1: two distinct natural experiments. | Rewrite paragraphs 4–6 + contribution list |
| 02 Lit | 3 streams | Add brief AML/regulatory-harmonization stream (4–6 cites). Reposition FATF as cleanest payment-friction shock. | Add 1 subsection (~150 words) |
| 03 Data | Single de-risking definition | New §3.X: Regulatory shocks — define AMLD post-2017, FATF greylist (already built), confounder controls. Rename `pf_cbr` → `fdi_proxy` in text (per memory: it's transformed FDI, not real CBR). | New 1-page subsection |
| 04 Strategy | One reduced form | Three reduced forms (FATF primary, AMLD symmetric, FDI broad). Exogeneity argument for each. Triple horse race + kitchen sink as identification stress test. | Substantial rewrite |
| 05 Results | One main table | Restructure 5.1 FATF, 5.2 AMLD, 5.3 Triple horse race. New lead table: yearly + panel side-by-side from `confounder_yearly.csv` / `confounder_panel.csv`. | Heaviest rewrite |
| 06 Robustness | Existing checks | Add triple horse race (H1), kitchen sink (H2), panel-PK attenuation discussion (sample halves to 1.37M when adding diplo/RTA). | Add ~2 subsections |
| 07 SOS | FDI-derisked γ → SOS | See Part C. AMLD-positive corridors flagged as "regulatory substitute" — down-weighted in headline SOS. | Recompute + re-rank |
| 08 Conclusion | One mechanism | Three findings. Policy: stablecoins as substitute for missing regulatory harmonization. | Rewrite |

## Part C — SOS recomputation

**Recommendation: composite SOS (Option C) as headline.**

| Option | Description | Use |
|---|---|---|
| A | Keep FDI-derisked γ (current) | Continuity, but γ is the noisiest of the three |
| B | Use FATF γ | Cleanest, but FATF is binary at country level → coarser corridor variation |
| **C** | Composite: SOS_intensive = \|γ_FATF\| × PCI × FATF_exposure + \|γ_FDI\| × PCI × FDI_derisked_exposure | **Recommended** — combines clean ID with continuous corridor variation |

Plus an AMLD adjustment: countries in EU corridors get a **negative** SOS contribution (regulatory infrastructure already substitutes for stablecoins).

**Deliverables:**
- `scripts/python/17_sos_recompute.py` — composite SOS using all three γ estimates
- `paper/tables/09_sos_construction/sos_top20_composite.tex` — new ranking
- `paper/tables/09_sos_construction/sos_ranking_correlations.tex` — Spearman across A, B, C
- Updated `paper/tables/14_feasibility_quadrant/`
- New figure: top-20 under each γ source, side-by-side bars

Open empirical question: how stable is the top-20 across γ choices? If Spearman > 0.85, defend headline as "robust to γ choice"; if not, the paper needs to defend the composite explicitly.

## Execution order

1. **User approves AMLD interpretation (Part A) and SOS recipe (Part C-C)** ← BLOCKING
2. Run `17_sos_recompute.py` → produce composite rankings + correlation table
3. Rewrite §05 Results around `confounder_yearly.csv` / `confounder_panel.csv` (heaviest)
4. Rewrite §01 Intro and §08 Conclusion (anchored to §05)
5. Rewrite §04 Strategy (anchored to §05 structure)
6. Update §02 Lit, §03 Data, §06 Robustness, §07 SOS in parallel
7. Compile (3-pass XeLaTeX), check for overfull hboxes, undefined refs
8. Dispatch writer-critic for polish review (target ≥ 80)

## Out of scope (deferred)

- Running scripts 07 (extensive margin), 10 (validation), 13 (figures), 14 (feasibility quadrant) on full data — they are points 4–7 in the wider list.
- Replacing `pf_cbr` with real BIS CBR data — flagged separately.
- LaTeX recompile is point 4; included here as step 7 since the reframe makes it necessary.

## Verification

- All three γ values cited in text match `paper/tables/15_confounders/confounder_panel.csv` (panel) and `confounder_yearly.csv` (yearly ranges)
- SOS rankings match `scripts/python/17_sos_recompute.py` output
- `xelatex` 3-pass produces 0 errors, 0 undefined refs
- writer-critic score ≥ 80
