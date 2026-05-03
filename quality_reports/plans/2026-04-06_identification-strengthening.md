# Implementation Plan: Identification Strengthening

**Status:** DRAFT
**Date:** 2026-04-06

## Context

The paper's de-risking indicator (bilateral FDI drop >50% from 2015-2017 base) is endogenous — it captures sanctions, political instability, trade wars, and other shocks beyond payment friction. The `pf_cbr` variable is NOT real correspondent banking data — it's a transformation of the same FDI bilateral used for `derisked`.

### Strategy: Three-Pronged Identification

1. **EU AMLD Regulatory Shock (PRIMARY)** — The 4th AMLD (transposition deadline June 2017) created a compliance shock to correspondent banking in EU corridors. This is the main instrument: exogenous regulatory timing, specific to payment infrastructure, affecting all EU corridors uniformly. Constructible from existing CEPII data (`eu_o`, `eu_d`).

2. **FATF Greylist × PCI (ADDITIONAL)** — Regulatory event specific to AML/CFT compliance. Greylisting triggers correspondent banking withdrawal. Data: downloaded and verified (55 country-episodes, 2015-2023). Secondary analysis supporting the AMLD finding.

3. **Composite Horse Race (VALIDATION)** — Pit AMLD × PCI, FATF × PCI, and FDI-derisked × PCI against each other. Also control for `diplo_disagreement × PCI` (geopolitics) and `kaopen × PCI` (capital openness). This decomposes the financial disruption channel.

### Why EU AMLD is the Best Available Instrument

- **Exogenous to trade:** Regulatory directive adopted at EU level, transposition deadline predetermined (June 2017 for AMLD4, January 2020 for AMLD5)
- **Specific to payment infrastructure:** AMLD compliance costs fell on banks' correspondent banking operations, directly driving CBR withdrawal
- **Clean treatment:** ALL EU corridors affected simultaneously — no selection into treatment
- **Sharp timing:** Pre-period (2015-2017) vs post-period (2018-2023) for AMLD4; additional shock at 2020 for AMLD5
- **Broad coverage:** EU has 27 member states, creating thousands of affected bilateral corridors
- **No reverse causality:** EU legislative calendar is not driven by bilateral trade patterns between (say) Tanzania and Germany

---

## Phase 1: Data Preparation

**Script:** `scripts/python/15_confounder_merge.py`
**Inputs:**
- `data/cleaned/panel_main.parquet` (33.3M rows)
- `data/raw/fatf_greylist_panel_2015_2023.csv` (495 rows, binary indicator)
- `data/raw/Gravity_csv_V202211/Gravity_V202211.csv` (diplo_disagreement, eu_o, eu_d, rta_coverage)

### 1.1 FATF Greylist Variable
```
fatf_grey_ij,t = 1 if fatf_greylist(i,t) == 1 OR fatf_greylist(j,t) == 1
```
- Merge country-year FATF panel onto both origin and destination
- Construct bilateral indicator: corridor is affected if EITHER partner is greylisted
- Construct interaction: `fatf_grey_x_pci = fatf_grey × pci_std`

### 1.2 EU AMLD Instrument
```
eu_corridor_ij = 1 if eu_o == 1 OR eu_d == 1 (at least one EU partner)
eu_post2017_ij,t = eu_corridor × (year >= 2018)  [AMLD4]
eu_post2020_ij,t = eu_corridor × (year >= 2020)  [AMLD5]
```
- Extract `eu_o`, `eu_d` from raw CEPII Gravity
- Construct time-varying instrument

### 1.3 Confounder Controls
- `diplo_disagreement` from raw Gravity (fill 2022-2023 with 2021)
- `rta_coverage` from raw Gravity (fill missing with 0)
- `kaopen_bilateral` already in panel_main

### 1.4 All Interaction Terms
- `fatf_grey_x_pci` = fatf_grey × pci_std
- `eu_post2017_x_pci` = eu_post2017 × pci_std
- `diplo_disagreement_x_pci` = diplo_disagreement × pci_std
- `kaopen_bilateral_x_pci` = kaopen_bilateral × pci_std

### 1.5 Output
- `data/cleaned/panel_main_confounders.parquet` — same 33.3M rows + ~12 new columns

---

## Phase 2: Estimation

**Script:** `scripts/python/16_confounder_estimation.py`
**Structure:** Same hybrid approach as 08_endogeneity.py (year-by-year cross-sections + panel subsample)

### 2.1 Cross-Section Specifications (6 years × 8 specs = 48 models)

```
# B0: Original Baseline (replicate)
trade_value ~ derisked + derisked:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# E1: EU AMLD Instrument (reduced form — PRIMARY SPECIFICATION)
trade_value ~ eu_post2017 + eu_post2017:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# E2: AMLD + FDI-derisked Horse Race
trade_value ~ eu_post2017 + eu_post2017:pci_std + derisked + derisked:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# F1: FATF Greylist (additional analysis)
trade_value ~ fatf_grey + fatf_grey:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# F2: FATF + FDI-derisked Horse Race
trade_value ~ fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# H1: AMLD + FATF + FDI Triple Horse Race
trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# H2: Kitchen Sink (all confounders)
trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + diplo_disagreement + diplo_disagreement:pci_std + kaopen_bilateral + kaopen_bilateral:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4

# H3: AMLD + Confounders (no FDI-derisked)
trade_value ~ eu_post2017 + eu_post2017:pci_std + diplo_disagreement + diplo_disagreement:pci_std + kaopen_bilateral + kaopen_bilateral:pci_std + ln_dist + contig + comlang_off + colony | iso3_o + iso3_d + hs4
```

### 2.2 Panel Specifications (subsample with pair FE, 5 specs)

```
# PB: Panel Baseline (replicate)
trade_value ~ derisked + derisked:pci_std | exporter_year + importer_year + pair + hs4

# PE: Panel AMLD (reduced form — PRIMARY)
trade_value ~ eu_post2017 + eu_post2017:pci_std | exporter_year + importer_year + pair + hs4

# PF: Panel FATF (additional)
trade_value ~ fatf_grey + fatf_grey:pci_std | exporter_year + importer_year + pair + hs4

# PH: Panel Horse Race (AMLD + FATF + FDI-derisked)
trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std | exporter_year + importer_year + pair + hs4

# PK: Panel Kitchen Sink
trade_value ~ eu_post2017 + eu_post2017:pci_std + fatf_grey + fatf_grey:pci_std + derisked + derisked:pci_std + diplo_disagreement + diplo_disagreement:pci_std | exporter_year + importer_year + pair + hs4
```

### 2.3 Output
- `data/cleaned/estimates_confounders.pkl` — all results
- `paper/tables/15_confounders/fatf_reduced_form.tex` — FATF × PCI results (the paper's key new table)
- `paper/tables/15_confounders/horse_race.tex` — composite horse race
- `paper/figures/15_confounders/coefficient_comparison.pdf` — forest plot

### 2.4 Interpretation Matrix

| eu_post2017 × PCI | derisked × PCI (after AMLD control) | Interpretation |
|-------------------|--------------------------------------|----------------|
| Negative, significant | Survives | Both banking regulation (AMLD) and broader disruption (FDI) channels active |
| Negative, significant | Attenuates/disappears | Payment friction IS the channel; FDI was capturing it noisily — strongest result |
| Null | Survives | FDI disruption matters but not through EU banking regulation specifically |
| Null | Null | Neither specification identifies a real effect |

---

## Phase 3: Paper Reframing

Depends on Phase 2 results. Two scenarios:

### If eu_post2017 × PCI is significant (Scenarios 1 or 2):
**Strong paper.** Reframe around AMLD as cleaner identification:
- Title stays — stablecoin opportunity is justified by the payment friction channel
- Introduction: lead with EU AMLD as the identification, FDI-derisked as complementary evidence
- Empirical strategy: present AMLD as primary instrument, FATF as additional, FDI as robustness
- Results: AMLD table as main, horse race as validation
- SOS: construct from AMLD coefficients (gamma_AMLD), not FDI gamma

### If eu_post2017 × PCI is null (Scenario 3):
**Different paper.** The effect is broader financial disruption, not payment friction:
- Reframe as "bilateral financial disruption × complexity"
- Temper stablecoin-specific claims
- SOS measures total disruption opportunity, stablecoins address a subset

### Specific section edits (both scenarios):
- `01_introduction.tex` — Add FATF identification, acknowledge FDI endogeneity
- `03_data.tex` — Add FATF greylist variable description, EU AMLD dates
- `04_empirical_strategy.tex` — Present three-pronged identification
- `05_results.tex` — Add FATF reduced-form subsection, horse-race subsection
- `07_stablecoin_opportunity.tex` — Update SOS construction if gamma source changes
- `08_conclusion.tex` — Update contribution claims

---

## Phase 4: SOS Recalculation (if needed)

If FATF × PCI provides a cleaner gamma, re-run SOS construction:
- Replace gamma from `estimates_reframed.rds` with gamma_FATF
- Re-run scripts 09 (SOS), 10 (validation), 14 (feasibility)
- Update rankings table, maps, quadrant analysis

---

## Phase 5: Compilation & Verification

1. Run `15_confounder_merge.py` — creates augmented panel
2. Run `16_confounder_estimation.py` — produces all results
3. Update paper sections based on results
4. Re-run SOS if needed
5. 3-pass XeLaTeX compilation
6. Verify all tables/figures render

---

## Critical Files

| File | Action |
|------|--------|
| `scripts/python/15_confounder_merge.py` | CREATE |
| `scripts/python/16_confounder_estimation.py` | CREATE |
| `data/raw/fatf_greylist_panel_2015_2023.csv` | EXISTS (verified) |
| `data/cleaned/panel_main_confounders.parquet` | CREATE (output) |
| `paper/sections/01-08` | EDIT (after results) |

## Estimated Runtime

- Phase 1 (data merge): ~10 min (polars, 33M rows)
- Phase 2 (estimation): ~60-90 min (48 cross-section + 4 panel specs)
- Phase 3 (paper edits): ~30 min
- Phase 4 (SOS, if needed): ~15 min
- Phase 5 (compilation): ~10 min
