# ===========================================================================
# 07_estimation_extensive.R — Extensive margin estimation (diversification)
#
# REFRAMED: Uses country-level de-risking exposure as friction proxy,
# since KAOPEN is not available and bilateral CBR not public.
#
# De-risking exposure = fraction of a country's trade partners where
# bilateral FDI dropped > 50% from base period.
#
# Spec 4: Does de-risking impede product diversification?
# Pr(RCA >= 1) = f(relatedness density, derisking_exposure, interactions)
#
# Inputs:  data/cleaned/panel_extensive.parquet
#          data/cleaned/imf_fdi_bilateral.parquet
# Outputs: data/cleaned/estimates_extensive.rds
#          paper/tables/07_estimation_extensive/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("07_estimation_extensive.R — Extensive Margin (Reframed)")

TABLE_DIR <- ensure_output_dir("07_estimation_extensive", "tables")

# ---------------------------------------------------------------------------
# 1. Load extensive margin panel
# ---------------------------------------------------------------------------
log_time("Loading extensive margin panel...")
ext <- read_clean("panel_extensive.parquet")
log_time(sprintf("  %s rows, %d countries, %d products",
                 format(nrow(ext), big.mark = ","),
                 uniqueN(ext$iso3), uniqueN(ext$hs4)))

# ---------------------------------------------------------------------------
# 2. Build country-level de-risking exposure from FDI
# ---------------------------------------------------------------------------
log_time("Building country-level de-risking exposure...")

fdi_path <- file.path(DIR_CLEAN, "imf_fdi_bilateral.parquet")
if (file.exists(fdi_path)) {
  fdi <- as.data.table(arrow::read_parquet(fdi_path))

  # Base period FDI per pair
  base_fdi <- fdi[year %in% BASE_PERIOD,
                  .(fdi_base = mean(fdi_bilateral, na.rm = TRUE)),
                  by = .(iso3_o, iso3_d)]

  # For each year, compute de-risking status
  dr_by_year <- fdi[year %in% SAMPLE_YEARS, .(iso3_o, iso3_d, year, fdi_bilateral)]
  dr_by_year <- merge(dr_by_year, base_fdi, by = c("iso3_o", "iso3_d"), all.x = TRUE)
  dr_by_year[, fdi_ratio := fdi_bilateral / fifelse(fdi_base > 0, fdi_base, NA_real_)]
  dr_by_year[, derisked := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.5)]

  # Country × year level: fraction of partners that are de-risked
  dr_country <- dr_by_year[, .(
    frac_derisked = mean(derisked, na.rm = TRUE),
    n_derisked = sum(derisked, na.rm = TRUE),
    n_partners = .N
  ), by = .(iso3 = iso3_o, year)]

  log_time(sprintf("  De-risking exposure: %d country-year obs", nrow(dr_country)))
  log_time(sprintf("  Mean frac_derisked: %.3f", mean(dr_country$frac_derisked, na.rm = TRUE)))

  # Drop old pf_country (was all NA from KAOPEN) and interaction columns
  ext[, c("pf_country", "density_x_pf", "pf_x_pci") := NULL]

  # Merge de-risking exposure as new pf_country
  ext <- merge(ext, dr_country[, .(iso3, year, pf_country = frac_derisked)],
               by = c("iso3", "year"), all.x = TRUE)
  ext[is.na(pf_country), pf_country := 0]

  # Rebuild interaction terms
  ext[, density_x_pf := density * pf_country]
  ext[, pf_x_pci := pf_country * pci_std]

  pf_match <- mean(ext$pf_country > 0)
  log_time(sprintf("  PF non-zero: %.1f%% of obs", 100 * pf_match))

} else {
  log_time("  WARNING: No FDI data — cannot compute de-risking exposure")
  log_time("  Skipping extensive margin estimation")
  ext[, pf_country := NA_real_]
}

# Drop missing
ext_est <- ext[!is.na(density) & !is.na(pci_std) & !is.na(pf_country)]
log_time(sprintf("  Estimation sample: %s rows", format(nrow(ext_est), big.mark = ",")))

# ---------------------------------------------------------------------------
# 3. Specification 4a: LPM — baseline (density only)
# ---------------------------------------------------------------------------
log_time("Estimating Spec 4a: LPM baseline (density + country FE + year FE)...")
t0 <- Sys.time()

spec4a_base <- feols(
  has_rca ~ density + density_x_pci |
    iso3 + year,
  data = ext_est,
  cluster = ~iso3
)

log_time(sprintf("  Spec 4a done in %.1f seconds", difftime(Sys.time(), t0, units = "secs")))
log_time(sprintf("  Density: %.4f (p=%.4f)", coef(spec4a_base)["density"],
                 pvalue(spec4a_base)["density"]))

# ---------------------------------------------------------------------------
# 4. Specification 4b: LPM with de-risking friction
# ---------------------------------------------------------------------------
log_time("Estimating Spec 4b: LPM + de-risking exposure...")
t0 <- Sys.time()

spec4b_pf <- feols(
  has_rca ~ density + pf_country + density_x_pf + density_x_pci + pf_x_pci |
    iso3 + year,
  data = ext_est,
  cluster = ~iso3
)

log_time(sprintf("  Spec 4b done in %.1f seconds", difftime(Sys.time(), t0, units = "secs")))
log_time(sprintf("  Density: %.4f", coef(spec4b_pf)["density"]))
log_time(sprintf("  Density × PF (beta_3): %.4f (SE: %.4f, p=%.4f)",
                 coef(spec4b_pf)["density_x_pf"],
                 se(spec4b_pf)["density_x_pf"],
                 pvalue(spec4b_pf)["density_x_pf"]))

# ---------------------------------------------------------------------------
# 5. Specification 4c: LPM with product FEs
# ---------------------------------------------------------------------------
log_time("Estimating Spec 4c: LPM + product FEs...")

spec4c_pfe <- feols(
  has_rca ~ density + pf_country + density_x_pf |
    iso3 + year + hs4,
  data = ext_est,
  cluster = ~iso3
)

log_time(sprintf("  Spec 4c done"))
log_time(sprintf("  Density × PF: %.4f (SE: %.4f, p=%.4f)",
                 coef(spec4c_pfe)["density_x_pf"],
                 se(spec4c_pfe)["density_x_pf"],
                 pvalue(spec4c_pfe)["density_x_pf"]))

# ---------------------------------------------------------------------------
# 6. Specification 4d: Logit
# ---------------------------------------------------------------------------
log_time("Estimating Spec 4d: Logit...")
t0 <- Sys.time()

spec4d_logit <- tryCatch(
  feglm(
    has_rca ~ density + pf_country + density_x_pf + density_x_pci + pf_x_pci |
      iso3 + year,
    data = ext_est,
    family = binomial(link = "logit"),
    cluster = ~iso3
  ),
  error = function(e) {
    log_time(paste("  Logit failed:", e$message))
    NULL
  }
)

if (!is.null(spec4d_logit)) {
  log_time(sprintf("  Spec 4d done in %.1f seconds", difftime(Sys.time(), t0, units = "secs")))
  log_time(sprintf("  Density × PF (logit): %.4f", coef(spec4d_logit)["density_x_pf"]))
}

# ---------------------------------------------------------------------------
# 7. Save estimates
# ---------------------------------------------------------------------------
log_time("Saving extensive margin estimates...")

estimates_ext <- list(
  spec4a_base = spec4a_base,
  spec4b_pf = spec4b_pf,
  spec4c_pfe = spec4c_pfe,
  spec4d_logit = spec4d_logit,
  # Backward compatibility: point 09_sos_construction to the right spec
  spec4_lpm = spec4b_pf
)

saveRDS(estimates_ext, file.path(DIR_CLEAN, "estimates_extensive.rds"))

# ---------------------------------------------------------------------------
# 8. Regression table
# ---------------------------------------------------------------------------
log_time("Producing regression table...")

model_list <- Filter(Negate(is.null), list(
  "(1) Density" = spec4a_base,
  "(2) + De-risking" = spec4b_pf,
  "(3) + Product FE" = spec4c_pfe,
  "(4) Logit" = spec4d_logit
))

msummary(
  model_list,
  output = file.path(TABLE_DIR, "extensive_margin.tex"),
  stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  gof_omit = "AIC|BIC|Log|RMSE",
  notes = "Standard errors clustered at the country level. Dependent variable: 1(RCA >= 1). PF = fraction of trade partners de-risked."
)

msummary(
  model_list,
  output = file.path(TABLE_DIR, "extensive_margin.csv"),
  stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01)
)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Extensive Margin")
log_time("Key coefficient (beta_3 on density × de-risking):")
log_time(sprintf("  LPM:      %.4f (SE: %.4f, p=%.4f)",
                 coef(spec4b_pf)["density_x_pf"],
                 se(spec4b_pf)["density_x_pf"],
                 pvalue(spec4b_pf)["density_x_pf"]))
if (!is.null(spec4d_logit)) {
  log_time(sprintf("  Logit:    %.4f (SE: %.4f)",
                   coef(spec4d_logit)["density_x_pf"],
                   se(spec4d_logit)["density_x_pf"]))
}
log_time(sprintf("  + Prod FE: %.4f (SE: %.4f, p=%.4f)",
                 coef(spec4c_pfe)["density_x_pf"],
                 se(spec4c_pfe)["density_x_pf"],
                 pvalue(spec4c_pfe)["density_x_pf"]))
log_time("Done. Next: R/09_sos_construction.R")
