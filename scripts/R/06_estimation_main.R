# ===========================================================================
# 06_estimation_main.R — Central PPML gravity estimation (reframed)
#
# IDENTIFICATION STRATEGY (reframed after validation):
#   Part A: Cross-sectional gravity with bilateral financial linkage (FDI).
#           Identifies the level effect of payment infrastructure on trade.
#   Part B: De-risking reduced form. Corridors that lost > 50% of bilateral
#           FDI are "de-risked." Tests whether de-risking hits complex
#           products disproportionately. This is the KEY causal result.
#
# Why this reframing: FDI bilateral positions are too sticky for within-pair
# continuous variation to identify the PCI interaction. But large discrete
# drops (de-risking events) create meaningful within-pair shocks. The
# de-risking × PCI interaction is identified from within-pair cross-product
# variation in response to corridor-level financial disruptions.
#
# All estimated via fixest::fepois() with pair-level clustering.
#
# Inputs:  data/cleaned/panel_main.parquet
# Outputs: data/cleaned/estimates_main.rds
#          paper/tables/06_estimation_main/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("06_estimation_main.R — PPML Gravity Estimation (Reframed)")

TABLE_DIR <- ensure_output_dir("06_estimation_main", "tables")
NTHREADS <- max(1, parallel::detectCores() - 1)

# ---------------------------------------------------------------------------
# 1. Load panel
# ---------------------------------------------------------------------------
log_time("Loading panel...")
panel <- read_clean("panel_main.parquet")
# Rename legacy pf_cbr* columns to fdi_proxy* (FDI-derived; see 03_data.tex).
panel <- rename_pf_to_fdi(panel)
log_time(sprintf("  %s rows", format(nrow(panel), big.mark = ",")))

# Fix CEPII V202211 column name: col45 -> colony
if ("col45" %in% names(panel) & !"colony" %in% names(panel)) {
  panel[, colony := col45]
  log_time("  Renamed col45 -> colony (CEPII V202211 naming)")
}
if (!"colony" %in% names(panel)) {
  panel[, colony := 0L]
  log_time("  WARNING: no colony column found, set to 0")
}

# Ensure factor types for FEs
panel[, exporter_year := as.factor(exporter_year)]
panel[, importer_year := as.factor(importer_year)]
panel[, pair := as.factor(pair)]
panel[, hs4 := as.factor(hs4)]

# Estimation sample: keep zeros (essential for PPML), drop missing controls
n_before <- nrow(panel)
panel_est <- panel[!is.na(pci_std) & !is.na(ln_dist)]
log_time(sprintf("  Estimation sample: %s rows (dropped %s with missing PCI/dist)",
                 format(nrow(panel_est), big.mark = ","),
                 format(n_before - nrow(panel_est), big.mark = ",")))

# Check PF availability
has_pf <- sum(!is.na(panel_est$fdi_proxy)) > 0.1 * nrow(panel_est)
log_time(sprintf("  fdi_proxy available: %s (%.1f%% non-missing)",
                 has_pf, 100 * mean(!is.na(panel_est$fdi_proxy))))

# =========================================================================
# PART A: CROSS-SECTIONAL SPECIFICATIONS
# FEs: exporter×year + importer×year + product
# Identification: between-pair variation in bilateral financial linkage
# =========================================================================
log_section("Part A: Cross-Sectional Identification")

# ---------------------------------------------------------------------------
# A1. Baseline Gravity (sanity check)
# ---------------------------------------------------------------------------
log_time("Estimating A1: Baseline gravity...")
t0 <- Sys.time()

spec_a1 <- fepois(
  trade_value ~ ln_dist + contig + comlang_off + colony |
    exporter_year + importer_year + hs4,
  data = panel_est,
  cluster = ~pair,
  nthreads = NTHREADS
)

log_time(sprintf("  A1 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
log_time(sprintf("  Distance: %.4f (expected: [-1.3, -0.7])", coef(spec_a1)["ln_dist"]))
log_time(sprintf("  Contiguity: %.4f (expected: positive)", coef(spec_a1)["contig"]))

# ---------------------------------------------------------------------------
# A2. Financial linkage (PF level, cross-sectional)
# ---------------------------------------------------------------------------
if (has_pf) {
  log_time("Estimating A2: Financial linkage (cross-sectional)...")
  t0 <- Sys.time()

  panel_pf <- panel_est[!is.na(fdi_proxy)]

  spec_a2 <- fepois(
    trade_value ~ fdi_proxy + ln_dist + contig + comlang_off + colony |
      exporter_year + importer_year + hs4,
    data = panel_pf,
    cluster = ~pair,
    nthreads = NTHREADS
  )

  log_time(sprintf("  A2 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
  log_time(sprintf("  PF_CBR: %.4f (p=%.4f, expected: negative)",
                   coef(spec_a2)["fdi_proxy"], pvalue(spec_a2)["fdi_proxy"]))

  # -------------------------------------------------------------------------
  # A3. PF × PCI interaction (cross-sectional)
  # -------------------------------------------------------------------------
  log_time("Estimating A3: PF × PCI (cross-sectional)...")
  t0 <- Sys.time()

  spec_a3 <- fepois(
    trade_value ~ fdi_proxy + fdi_proxy:pci_std +
      ln_dist + contig + comlang_off + colony |
      exporter_year + importer_year + hs4,
    data = panel_pf,
    cluster = ~pair,
    nthreads = NTHREADS
  )

  log_time(sprintf("  A3 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
  log_time(sprintf("  PF:PCI: %.4f (p=%.4f)",
                   coef(spec_a3)["fdi_proxy:pci_std"],
                   pvalue(spec_a3)["fdi_proxy:pci_std"]))
} else {
  spec_a2 <- spec_a3 <- NULL
}

# =========================================================================
# PART B: DE-RISKING REDUCED FORM (CAUSAL CREDIBILITY)
# A corridor is "de-risked" if bilateral FDI drops > 50% from base period.
# The de-risking event creates a discrete within-pair shock.
# =========================================================================
log_section("Part B: De-Risking Reduced Form")

if (has_pf) {
  # Construct de-risking indicator
  log_time("Constructing de-risking indicator...")

  # Compute base period FDI for each pair
  base_fdi <- panel_est[year %in% BASE_PERIOD & !is.na(fdi_bilateral),
                        .(fdi_base = mean(fdi_bilateral, na.rm = TRUE)),
                        by = pair]
  panel_pf <- merge(panel_pf, base_fdi, by = "pair", all.x = TRUE)

  # De-risking: FDI dropped > 50% from base period average
  panel_pf[, fdi_ratio := fdi_bilateral / fifelse(fdi_base > 0, fdi_base, NA_real_)]
  panel_pf[, derisked := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.5)]

  n_derisked_pairs <- uniqueN(panel_pf[derisked == 1]$pair)
  n_derisked_obs <- sum(panel_pf$derisked, na.rm = TRUE)
  log_time(sprintf("  De-risked pairs: %d (of %d total)",
                   n_derisked_pairs, uniqueN(panel_pf$pair)))
  log_time(sprintf("  De-risked obs: %s (%.1f%%)",
                   format(n_derisked_obs, big.mark = ","),
                   100 * mean(panel_pf$derisked, na.rm = TRUE)))

  if (n_derisked_pairs >= 10) {
    # -----------------------------------------------------------------------
    # B1. De-risking main effect (cross-sectional)
    # -----------------------------------------------------------------------
    log_time("Estimating B1: De-risking main effect...")
    t0 <- Sys.time()

    spec_b1 <- fepois(
      trade_value ~ derisked + ln_dist + contig + comlang_off + colony |
        exporter_year + importer_year + hs4,
      data = panel_pf,
      cluster = ~pair,
      nthreads = NTHREADS
    )

    log_time(sprintf("  B1 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
    log_time(sprintf("  Derisked: %.4f (p=%.4f)",
                     coef(spec_b1)["derisked"], pvalue(spec_b1)["derisked"]))

    # -----------------------------------------------------------------------
    # B2. De-risking × PCI (cross-sectional, KEY RESULT)
    # -----------------------------------------------------------------------
    log_time("Estimating B2: Derisked × PCI (KEY SPECIFICATION)...")
    t0 <- Sys.time()

    spec_b2 <- fepois(
      trade_value ~ derisked + derisked:pci_std +
        ln_dist + contig + comlang_off + colony |
        exporter_year + importer_year + hs4,
      data = panel_pf,
      cluster = ~pair,
      nthreads = NTHREADS
    )

    log_time(sprintf("  B2 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
    log_time(sprintf("  Derisked:PCI: %.4f (SE %.4f, p=%.4f) << KEY",
                     coef(spec_b2)["derisked:pci_std"],
                     se(spec_b2)["derisked:pci_std"],
                     pvalue(spec_b2)["derisked:pci_std"]))

    # -----------------------------------------------------------------------
    # B3. De-risking × PCI with pair FEs (within-pair identification)
    # -----------------------------------------------------------------------
    log_time("Estimating B3: Derisked × PCI + pair FEs...")
    t0 <- Sys.time()

    spec_b3 <- fepois(
      trade_value ~ derisked + derisked:pci_std |
        exporter_year + importer_year + pair + hs4,
      data = panel_pf,
      cluster = ~pair,
      nthreads = NTHREADS
    )

    log_time(sprintf("  B3 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
    log_time(sprintf("  Derisked:PCI (pair FE): %.4f (SE %.4f, p=%.4f)",
                     coef(spec_b3)["derisked:pci_std"],
                     se(spec_b3)["derisked:pci_std"],
                     pvalue(spec_b3)["derisked:pci_std"]))

    # -----------------------------------------------------------------------
    # B4. De-risking × PCI with continuous PF control
    # Shows de-risking interaction is not just PF level × PCI
    # -----------------------------------------------------------------------
    log_time("Estimating B4: Derisked × PCI controlling for PF level...")
    t0 <- Sys.time()

    spec_b4 <- fepois(
      trade_value ~ fdi_proxy + derisked + derisked:pci_std +
        ln_dist + contig + comlang_off + colony |
        exporter_year + importer_year + hs4,
      data = panel_pf,
      cluster = ~pair,
      nthreads = NTHREADS
    )

    log_time(sprintf("  B4 done in %.1f minutes", difftime(Sys.time(), t0, units = "mins")))
    log_time(sprintf("  PF level: %.4f (p=%.4f)",
                     coef(spec_b4)["fdi_proxy"], pvalue(spec_b4)["fdi_proxy"]))
    log_time(sprintf("  Derisked:PCI: %.4f (p=%.4f)",
                     coef(spec_b4)["derisked:pci_std"],
                     pvalue(spec_b4)["derisked:pci_std"]))

    # -----------------------------------------------------------------------
    # B5. Robustness: alternative de-risking thresholds
    # -----------------------------------------------------------------------
    log_time("Estimating B5: Alternative thresholds (25%, 75%)...")

    # 25% drop threshold (stricter)
    panel_pf[, derisked_25 := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.25)]
    # 75% drop threshold (looser)
    panel_pf[, derisked_75 := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.75)]

    spec_b5_strict <- tryCatch(
      fepois(
        trade_value ~ derisked_25 + derisked_25:pci_std +
          ln_dist + contig + comlang_off + colony |
          exporter_year + importer_year + hs4,
        data = panel_pf,
        cluster = ~pair,
        nthreads = NTHREADS
      ), error = function(e) { log_time(paste("  B5 strict failed:", e$message)); NULL }
    )

    spec_b5_loose <- tryCatch(
      fepois(
        trade_value ~ derisked_75 + derisked_75:pci_std +
          ln_dist + contig + comlang_off + colony |
          exporter_year + importer_year + hs4,
        data = panel_pf,
        cluster = ~pair,
        nthreads = NTHREADS
      ), error = function(e) { log_time(paste("  B5 loose failed:", e$message)); NULL }
    )

    if (!is.null(spec_b5_strict)) {
      log_time(sprintf("  25%% threshold: %.4f (p=%.4f)",
                       coef(spec_b5_strict)["derisked_25:pci_std"],
                       pvalue(spec_b5_strict)["derisked_25:pci_std"]))
    }
    if (!is.null(spec_b5_loose)) {
      log_time(sprintf("  75%% threshold: %.4f (p=%.4f)",
                       coef(spec_b5_loose)["derisked_75:pci_std"],
                       pvalue(spec_b5_loose)["derisked_75:pci_std"]))
    }
  } else {
    log_time("  Too few de-risked pairs — skipping Part B")
    spec_b1 <- spec_b2 <- spec_b3 <- spec_b4 <- NULL
    spec_b5_strict <- spec_b5_loose <- NULL
  }
} else {
  spec_a2 <- spec_a3 <- NULL
  spec_b1 <- spec_b2 <- spec_b3 <- spec_b4 <- NULL
  spec_b5_strict <- spec_b5_loose <- NULL
}

# =========================================================================
# SAVE ALL ESTIMATES
# =========================================================================
log_section("Saving Estimates")

estimates <- list(
  # Part A: cross-sectional
  a1_gravity = spec_a1,
  a2_pf_level = spec_a2,
  a3_pf_pci_xs = spec_a3,
  # Part B: de-risking
  b1_derisked = if (exists("spec_b1")) spec_b1 else NULL,
  b2_derisked_pci = if (exists("spec_b2")) spec_b2 else NULL,
  b3_derisked_pci_pairfe = if (exists("spec_b3")) spec_b3 else NULL,
  b4_derisked_pci_pfctrl = if (exists("spec_b4")) spec_b4 else NULL,
  b5_derisked_strict = if (exists("spec_b5_strict")) spec_b5_strict else NULL,
  b5_derisked_loose = if (exists("spec_b5_loose")) spec_b5_loose else NULL
)

saveRDS(estimates, file.path(DIR_CLEAN, "estimates_main.rds"))
log_time(paste("  Saved:", file.path(DIR_CLEAN, "estimates_main.rds")))

# =========================================================================
# REGRESSION TABLES
# =========================================================================
log_time("Producing regression tables...")

# Table 1: Cross-sectional results (A1-A3)
models_xs <- Filter(Negate(is.null), list(
  "(1)" = spec_a1,
  "(2)" = spec_a2,
  "(3)" = spec_a3
))
if (length(models_xs) > 0) {
  msummary(
    models_xs,
    output = file.path(TABLE_DIR, "table1_cross_sectional.tex"),
    stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
    gof_omit = "AIC|BIC|Log|Adj|RMSE",
    title = "Financial Linkage and Trade: Cross-Sectional Evidence",
    notes = "Standard errors clustered at the country-pair level."
  )
  msummary(models_xs,
           output = file.path(TABLE_DIR, "table1_cross_sectional.csv"),
           stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01))
}

# Table 2: De-risking results (B1-B4)
models_dr <- Filter(Negate(is.null), list(
  "(1)" = if (exists("spec_b1")) spec_b1 else NULL,
  "(2)" = if (exists("spec_b2")) spec_b2 else NULL,
  "(3)" = if (exists("spec_b3")) spec_b3 else NULL,
  "(4)" = if (exists("spec_b4")) spec_b4 else NULL
))
if (length(models_dr) > 0) {
  msummary(
    models_dr,
    output = file.path(TABLE_DIR, "table2_derisking.tex"),
    stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
    gof_omit = "AIC|BIC|Log|Adj|RMSE",
    title = "De-Risking and Complex-Product Trade",
    notes = "Standard errors clustered at the country-pair level. De-risked = bilateral FDI dropped > 50\\% from 2015-2017 base."
  )
  msummary(models_dr,
           output = file.path(TABLE_DIR, "table2_derisking.csv"),
           stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01))
}

# =========================================================================
# SUMMARY
# =========================================================================
log_section("SUMMARY — Main Estimation (Reframed)")

log_time("Part A (Cross-sectional):")
if (!is.null(spec_a1))
  log_time(sprintf("  A1 Gravity:  dist=%.4f", coef(spec_a1)["ln_dist"]))
if (!is.null(spec_a2))
  log_time(sprintf("  A2 PF level: %.4f (p=%.4f)",
                   coef(spec_a2)["fdi_proxy"], pvalue(spec_a2)["fdi_proxy"]))
if (!is.null(spec_a3))
  log_time(sprintf("  A3 PF×PCI:   %.4f (p=%.4f)",
                   coef(spec_a3)["fdi_proxy:pci_std"],
                   pvalue(spec_a3)["fdi_proxy:pci_std"]))

if (exists("spec_b2") && !is.null(spec_b2)) {
  log_time("\nPart B (De-risking — KEY RESULTS):")
  log_time(sprintf("  B2 Derisked×PCI (cross-sect): %.4f (p=%.4f)",
                   coef(spec_b2)["derisked:pci_std"],
                   pvalue(spec_b2)["derisked:pci_std"]))
  if (!is.null(spec_b3))
    log_time(sprintf("  B3 Derisked×PCI (pair FE):    %.4f (p=%.4f)",
                     coef(spec_b3)["derisked:pci_std"],
                     pvalue(spec_b3)["derisked:pci_std"]))
}

log_time("\nDone. Next: R/07_estimation_extensive.R")
