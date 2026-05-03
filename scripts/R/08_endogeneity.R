# ===========================================================================
# 08_endogeneity.R — Causal robustness: lags, de-risking reduced form, leads
#
# Three layers of endogeneity strategy:
# 1. Lagged payment frictions (L1, L2)
# 2. De-risking reduced form (derisked x PCI in PPML)
# 3. Leads test (F1 should be null — pre-trends check)
#
# Inputs:  data/cleaned/panel_main.parquet
# Outputs: data/cleaned/estimates_endogeneity.rds
#          paper/tables/08_endogeneity/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("08_endogeneity.R — Causal Robustness")

TABLE_DIR <- ensure_output_dir("08_endogeneity", "tables")

# ---------------------------------------------------------------------------
# 1. Load panel
# ---------------------------------------------------------------------------
log_time("Loading panel...")
panel <- read_clean("panel_main.parquet")
# Rename legacy pf_cbr* columns to fdi_proxy* (FDI-derived; see 03_data.tex).
panel <- rename_pf_to_fdi(panel)

# Ensure factors
panel[, exporter_year := as.factor(exporter_year)]
panel[, importer_year := as.factor(importer_year)]
panel[, pair := as.factor(pair)]
panel[, hs4 := as.factor(hs4)]

has_fdi <- sum(!is.na(panel$fdi_proxy)) > 0.1 * nrow(panel)
if (!has_fdi) {
  log_time("fdi_proxy not available — cannot run endogeneity checks.")
  log_time("Re-run 04_merge_panel.R to rebuild the panel.")
  saveRDS(list(), file.path(DIR_CLEAN, "estimates_endogeneity.rds"))
  quit(save = "no")
}

panel_est <- panel[!is.na(pci_std) & !is.na(fdi_proxy)]

estimates <- list()

# ---------------------------------------------------------------------------
# 2. Lag-1 specification
# ---------------------------------------------------------------------------
log_time("Estimating Lag-1 specification...")
t0 <- Sys.time()

estimates$lag1 <- fepois(
  trade_value ~ fdi_proxy_L1 + fdi_proxy_L1:pci_std |
    exporter_year + importer_year + pair + hs4,
  data = panel_est[!is.na(fdi_proxy_L1)],
  cluster = ~pair,
  nthreads = parallel::detectCores() - 1
)
log_time(sprintf("  Done in %.1f min. Interaction coef: %.4f",
                 difftime(Sys.time(), t0, units = "mins"),
                 coef(estimates$lag1)["fdi_proxy_L1:pci_std"]))

# ---------------------------------------------------------------------------
# 3. Lag-2 specification
# ---------------------------------------------------------------------------
log_time("Estimating Lag-2 specification...")
t0 <- Sys.time()

estimates$lag2 <- fepois(
  trade_value ~ fdi_proxy_L2 + fdi_proxy_L2:pci_std |
    exporter_year + importer_year + pair + hs4,
  data = panel_est[!is.na(fdi_proxy_L2)],
  cluster = ~pair,
  nthreads = parallel::detectCores() - 1
)
log_time(sprintf("  Done in %.1f min. Interaction coef: %.4f",
                 difftime(Sys.time(), t0, units = "mins"),
                 coef(estimates$lag2)["fdi_proxy_L2:pci_std"]))

# ---------------------------------------------------------------------------
# 4. De-risking reduced form
# ---------------------------------------------------------------------------
log_time("Constructing de-risking indicator...")

# Identify corridors with large drops in correspondent banking
# De-risking = corridor experienced >50% decline in CBR count over any 2-year window
cbr_panel <- panel_est[, .(fdi_proxy = mean(fdi_proxy, na.rm = TRUE),
                            n_corr = mean(n_correspondents, na.rm = TRUE)),
                        by = .(iso3_o, iso3_d, year)]
setkey(cbr_panel, iso3_o, iso3_d, year)

cbr_panel[, n_corr_L2 := shift(n_corr, n = 2, type = "lag"),
          by = .(iso3_o, iso3_d)]
cbr_panel[, pct_change := (n_corr - n_corr_L2) / (n_corr_L2 + 1)]
cbr_panel[, derisked := as.integer(pct_change < -0.5 & !is.na(pct_change))]

n_derisked <- sum(cbr_panel$derisked == 1, na.rm = TRUE)
log_time(sprintf("  De-risked corridor-years: %d", n_derisked))

if (n_derisked > 50) {
  # Merge de-risking indicator onto estimation panel
  panel_est <- merge(panel_est,
                      cbr_panel[, .(iso3_o, iso3_d, year, derisked)],
                      by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
  panel_est[is.na(derisked), derisked := 0L]

  log_time("Estimating de-risking reduced form...")
  t0 <- Sys.time()

  estimates$derisking <- fepois(
    trade_value ~ derisked + derisked:pci_std |
      exporter_year + importer_year + pair + hs4,
    data = panel_est,
    cluster = ~pair,
    nthreads = parallel::detectCores() - 1
  )
  log_time(sprintf("  Done in %.1f min. DeRisk x PCI coef: %.4f",
                   difftime(Sys.time(), t0, units = "mins"),
                   coef(estimates$derisking)["derisked:pci_std"]))
} else {
  log_time("  Too few de-risking events — skipping reduced form")
  estimates$derisking <- NULL
}

# ---------------------------------------------------------------------------
# 5. Leads test (pre-trends)
# ---------------------------------------------------------------------------
log_time("Estimating leads test (F1 — should be NULL)...")
t0 <- Sys.time()

estimates$leads <- fepois(
  trade_value ~ fdi_proxy_F1 + fdi_proxy_F1:pci_std |
    exporter_year + importer_year + pair + hs4,
  data = panel_est[!is.na(fdi_proxy_F1)],
  cluster = ~pair,
  nthreads = parallel::detectCores() - 1
)

lead_coef <- coef(estimates$leads)["fdi_proxy_F1:pci_std"]
lead_pval <- pvalue(estimates$leads)["fdi_proxy_F1:pci_std"]
log_time(sprintf("  Lead interaction coef: %.4f (p=%.4f)", lead_coef, lead_pval))
if (lead_pval < 0.05) {
  log_time("  WARNING: Lead is significant — potential reverse causality concern!")
} else {
  log_time("  PASS: Lead is not significant — no pre-trend detected")
}

# ---------------------------------------------------------------------------
# 6. Save and produce table
# ---------------------------------------------------------------------------
log_time("Saving estimates...")
saveRDS(estimates, file.path(DIR_CLEAN, "estimates_endogeneity.rds"))

model_list <- Filter(Negate(is.null), estimates)
msummary(
  model_list,
  output = file.path(TABLE_DIR, "endogeneity_checks.tex"),
  stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  gof_omit = "AIC|BIC|Log|RMSE",
  title = "Endogeneity Checks: Lags, De-Risking Reduced Form, and Leads Test",
  notes = "Standard errors clustered at the country-pair level."
)

msummary(model_list,
         output = file.path(TABLE_DIR, "endogeneity_checks.csv"),
         stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01))

log_section("SUMMARY — Endogeneity Checks")
log_time("Done. Next: R/10_validation.R")
