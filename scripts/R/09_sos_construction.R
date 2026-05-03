# ===========================================================================
# 09_sos_construction.R — Stablecoin Opportunity Score (Reframed)
#
# APPROACH: SOS is built from the de-risking × PCI coefficient (gamma),
# not the continuous PF × PCI interaction (alpha_2). The logic:
#
#   gamma = coef on (derisked × pci_std) from Spec B2/B3
#
# Interpretation: for a de-risked corridor, a one-SD increase in product
# complexity amplifies the trade loss by |gamma| × 100%. Reversing the
# sign: stablecoins that restore payment infrastructure would generate
# a trade gain of |gamma| × PCI_std for each de-risked corridor.
#
# INTENSIVE MARGIN SOS (for country c, product p):
#   SOS_int[c,p] = |gamma| × PCI_std_p × sum_j(derisked[c,j] × X[c,j,p,T])
#   = trade-weighted de-risking exposure × product complexity
#
# EXTENSIVE MARGIN SOS (for country c, product p where RCA < 1):
#   SOS_ext[c,p] = |beta_3| × density[c,p,T] × PCI_std_p × pf_country[c]
#
# Combined: SOS[c,p] = omega × SOS_int + (1-omega) × SOS_ext
#
# Inputs:  data/cleaned/estimates_main.rds (or estimates_reframed.rds)
#          data/cleaned/estimates_extensive.rds
#          data/cleaned/panel_main.parquet (or estimation subsets)
#          data/cleaned/complexity_pci.parquet
#          data/cleaned/complexity_density.parquet
#          data/cleaned/complexity_rca.parquet
# Outputs: data/cleaned/sos_country_product.parquet
#          data/cleaned/sos_country.parquet
#          paper/tables/09_sos_construction/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("09_sos_construction.R — Stablecoin Opportunity Score")

TABLE_DIR <- ensure_output_dir("09_sos_construction", "tables")

# ---------------------------------------------------------------------------
# 1. Load estimates and extract key coefficients
# ---------------------------------------------------------------------------
log_time("Loading estimates...")

# Try reframed estimates first, fall back to main
est_path <- file.path(DIR_CLEAN, "estimates_reframed.rds")
if (!file.exists(est_path)) {
  est_path <- file.path(DIR_CLEAN, "estimates_main.rds")
}
est_main <- readRDS(est_path)
log_time(sprintf("  Loaded: %s", est_path))

# Extract gamma (de-risking × PCI coefficient)
# Prefer B3 (pair FE) if available, otherwise B2 (cross-sectional)
gamma_spec <- NULL
gamma_name <- NULL

if (!is.null(est_main$b3_derisked_pci_pairfe)) {
  gamma_spec <- est_main$b3_derisked_pci_pairfe
  gamma_name <- "B3 (pair FE)"
} else if (!is.null(est_main$b2_derisked_pci)) {
  gamma_spec <- est_main$b2_derisked_pci
  gamma_name <- "B2 (cross-sectional)"
}

if (!is.null(gamma_spec)) {
  gamma <- coef(gamma_spec)["derisked:pci_std"]
  gamma_se <- se(gamma_spec)["derisked:pci_std"]
  log_time(sprintf("  gamma (derisked × PCI) from %s: %.4f (SE: %.4f)",
                   gamma_name, gamma, gamma_se))
} else {
  # Fallback placeholder based on validation results
  log_time("  WARNING: No de-risking estimates found. Using validation placeholder.")
  gamma <- -0.284
  gamma_se <- 0.134
}

# Extract PF level effect (for country-level scoring)
if (!is.null(est_main$a2_pf_level)) {
  # Coefficient name is "fdi_proxy" after the pf_cbr -> fdi_proxy rename
  # in 06_estimation_main.R. Fall back to "pf_cbr" if reading legacy estimates.
  cf <- coef(est_main$a2_pf_level)
  pf_level <- if ("fdi_proxy" %in% names(cf)) cf["fdi_proxy"] else cf["pf_cbr"]
  log_time(sprintf("  PF level effect: %.4f", pf_level))
} else {
  pf_level <- -0.22
}

# Extract beta_3 (extensive margin) if available
ext_path <- file.path(DIR_CLEAN, "estimates_extensive.rds")
if (file.exists(ext_path)) {
  est_ext <- readRDS(ext_path)
  if (!is.null(est_ext$spec4_lpm)) {
    beta_3 <- coef(est_ext$spec4_lpm)["density_x_pf"]
    beta_3_se <- se(est_ext$spec4_lpm)["density_x_pf"]
    log_time(sprintf("  beta_3 (density × PF): %.4f (SE: %.4f)", beta_3, beta_3_se))
  } else {
    beta_3 <- -0.05
    beta_3_se <- 0.025
    log_time("  WARNING: Extensive margin estimates not available. Using placeholder.")
  }
} else {
  beta_3 <- -0.05
  beta_3_se <- 0.025
  log_time("  WARNING: estimates_extensive.rds not found. Using placeholder beta_3.")
}

# ---------------------------------------------------------------------------
# 2. Load data for SOS computation
# ---------------------------------------------------------------------------
log_time("Loading data for SOS computation...")

pci <- read_clean("complexity_pci.parquet")
rca <- read_clean("complexity_rca.parquet")
density <- read_clean("complexity_density.parquet")

# Load trade data for latest year
baci <- read_clean(BACI_FILE)
T_year <- max(baci$year)
baci_T <- baci[year == T_year]
log_time(sprintf("  Trade data: year %d, %s flows", T_year,
                 format(nrow(baci_T), big.mark = ",")))

# Load FDI bilateral for de-risking identification
fdi_path <- file.path(DIR_CLEAN, "imf_fdi_bilateral.parquet")
if (file.exists(fdi_path)) {
  fdi <- as.data.table(arrow::read_parquet(fdi_path))
  log_time(sprintf("  FDI bilateral: %s obs", format(nrow(fdi), big.mark = ",")))
} else {
  fdi <- data.table(iso3_o = character(), iso3_d = character(),
                    year = integer(), fdi_bilateral = numeric())
  log_time("  WARNING: No FDI bilateral data")
}

# ---------------------------------------------------------------------------
# 3. Identify de-risked corridors
# ---------------------------------------------------------------------------
log_time("Identifying de-risked corridors...")

# Base period FDI
base_fdi <- fdi[year %in% BASE_PERIOD,
                .(fdi_base = mean(fdi_bilateral, na.rm = TRUE)),
                by = .(iso3_o, iso3_d)]

# Latest year FDI
fdi_T <- fdi[year == max(fdi$year, na.rm = TRUE)]

# Merge and compute de-risking status
derisking <- merge(base_fdi, fdi_T[, .(iso3_o, iso3_d, fdi_current = fdi_bilateral)],
                   by = c("iso3_o", "iso3_d"), all.x = TRUE)
derisking[, fdi_ratio := fdi_current / fifelse(fdi_base > 0, fdi_base, NA_real_)]
derisking[, derisked := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.5)]

n_derisked <- sum(derisking$derisked, na.rm = TRUE)
log_time(sprintf("  De-risked corridors: %d (of %d with base FDI data)",
                 n_derisked, nrow(derisking)))

# ---------------------------------------------------------------------------
# 4. Intensive Margin SOS
# ---------------------------------------------------------------------------
log_time("Computing intensive margin SOS...")

# For each exporter c, product p:
# SOS_int[c,p] = |gamma| × PCI_std_p × sum_j(derisked[c,j] × X[c,j,p,T])
#
# Interpretation: potential trade gain from restoring payment infrastructure
# in de-risked corridors, weighted by how much the product is affected
# (higher PCI → more affected by de-risking → more to gain from stablecoins)

# Merge PCI onto trade
baci_T <- merge(baci_T, pci[, .(hs4, pci_std)], by = "hs4", all.x = TRUE)

# Merge de-risking status onto trade
baci_T <- merge(baci_T, derisking[, .(iso3_o, iso3_d, derisked)],
                by = c("iso3_o", "iso3_d"), all.x = TRUE)
baci_T[is.na(derisked), derisked := 0L]

# Compute intensive SOS at corridor-product level
# |gamma| because gamma < 0 and we want SOS > 0 for opportunities
abs_gamma <- abs(gamma)
baci_T[, sos_int_raw := abs_gamma * pci_std * derisked * trade_value]

# Also compute a continuous version using PF level × PCI
fdi_latest <- fdi_T[, .(iso3_o, iso3_d, pf_fdi)]
baci_T <- merge(baci_T, fdi_latest, by = c("iso3_o", "iso3_d"), all.x = TRUE)
baci_T[, sos_int_continuous := abs(pf_level) * pci_std * abs(fifelse(is.na(pf_fdi), 0, pf_fdi)) * trade_value]

# Aggregate over partners: country × product
sos_intensive <- baci_T[!is.na(sos_int_raw),
                         .(sos_intensive = sum(sos_int_raw, na.rm = TRUE),
                           sos_int_continuous = sum(sos_int_continuous, na.rm = TRUE),
                           trade_derisked = sum(trade_value * derisked, na.rm = TRUE),
                           n_derisked_partners = sum(derisked, na.rm = TRUE)),
                         by = .(iso3 = iso3_o, hs4)]

log_time(sprintf("  Intensive SOS: %s country-product pairs",
                 format(nrow(sos_intensive), big.mark = ",")))

# ---------------------------------------------------------------------------
# 5. Extensive Margin SOS
# ---------------------------------------------------------------------------
log_time("Computing extensive margin SOS...")

# For country c, product p where RCA < 1:
# SOS_ext[c,p] = |beta_3| × density[c,p,T] × PF_country[c,T] × PCI_p

rca_T <- rca[year == T_year]
density_T <- density[year == T_year]

extensive_data <- merge(rca_T[has_rca == 0, .(iso3, hs4)],
                        density_T[, .(iso3, hs4, density)],
                        by = c("iso3", "hs4"), all.x = TRUE)
extensive_data <- merge(extensive_data, pci[, .(hs4, pci_std)],
                        by = "hs4", all.x = TRUE)

# Country-level de-risking exposure
derisking_country <- derisking[, .(
  n_derisked = sum(derisked, na.rm = TRUE),
  frac_derisked = mean(derisked, na.rm = TRUE),
  mean_fdi_loss = mean(fifelse(derisked == 1, 1 - fdi_ratio, 0), na.rm = TRUE)
), by = .(iso3 = iso3_o)]

extensive_data <- merge(extensive_data, derisking_country,
                        by = "iso3", all.x = TRUE)
extensive_data[is.na(frac_derisked), frac_derisked := 0]

# Extensive SOS: higher for countries with more de-risked corridors,
# products with high PCI, and country-product pairs with high relatedness density
abs_beta3 <- abs(beta_3)
extensive_data[, sos_extensive := abs_beta3 * density * frac_derisked * pci_std]

sos_extensive <- extensive_data[!is.na(sos_extensive),
                                .(iso3, hs4, sos_extensive, density, frac_derisked)]

log_time(sprintf("  Extensive SOS: %s country-product pairs",
                 format(nrow(sos_extensive), big.mark = ",")))

# ---------------------------------------------------------------------------
# 6. Combined SOS
# ---------------------------------------------------------------------------
log_time("Combining intensive + extensive SOS...")

omega <- 0.5  # equal weight (robustness: vary omega)

sos_cp <- merge(sos_intensive[, .(iso3, hs4, sos_intensive, trade_derisked,
                                   n_derisked_partners)],
                sos_extensive[, .(iso3, hs4, sos_extensive, density, frac_derisked)],
                by = c("iso3", "hs4"), all = TRUE)
sos_cp[is.na(sos_intensive), sos_intensive := 0]
sos_cp[is.na(sos_extensive), sos_extensive := 0]

# Normalize each margin to [0,1] before combining
max_int <- max(sos_cp$sos_intensive, na.rm = TRUE)
max_ext <- max(sos_cp$sos_extensive, na.rm = TRUE)
if (max_int > 0) sos_cp[, sos_int_norm := sos_intensive / max_int] else sos_cp[, sos_int_norm := 0]
if (max_ext > 0) sos_cp[, sos_ext_norm := sos_extensive / max_ext] else sos_cp[, sos_ext_norm := 0]
sos_cp[, sos_combined := omega * sos_int_norm + (1 - omega) * sos_ext_norm]

# Merge product info
sos_cp <- merge(sos_cp, pci[, .(hs4, pci_raw, pci_std)],
                by = "hs4", all.x = TRUE)

write_clean(sos_cp, "sos_country_product.parquet")

# ---------------------------------------------------------------------------
# 7. Aggregate to country level
# ---------------------------------------------------------------------------
log_time("Aggregating SOS to country level...")

sos_country <- sos_cp[, .(
  sos_total = sum(sos_combined, na.rm = TRUE),
  sos_intensive_total = sum(sos_int_norm, na.rm = TRUE),
  sos_extensive_total = sum(sos_ext_norm, na.rm = TRUE),
  n_products_intensive = sum(sos_intensive > 0),
  n_products_extensive = sum(sos_extensive > 0),
  n_derisked_partners = max(n_derisked_partners, na.rm = TRUE),
  mean_pci_exposed = weighted.mean(pci_std[sos_intensive > 0],
                                    sos_intensive[sos_intensive > 0],
                                    na.rm = TRUE),
  trade_at_risk = sum(trade_derisked, na.rm = TRUE)
), by = iso3]

# Replace -Inf from max() when all NA
sos_country[is.infinite(n_derisked_partners), n_derisked_partners := 0L]
sos_country[is.nan(mean_pci_exposed), mean_pci_exposed := NA_real_]

# Rank (highest SOS = rank 1 = most opportunity)
sos_country[, rank_total := frank(-sos_total)]
sos_country[, rank_intensive := frank(-sos_intensive_total)]
sos_country[, rank_extensive := frank(-sos_extensive_total)]

setorder(sos_country, rank_total)

write_clean(sos_country, "sos_country.parquet")

# ---------------------------------------------------------------------------
# 8. Uncertainty quantification (gamma +/- 1 SE)
# ---------------------------------------------------------------------------
log_time("Computing SOS sensitivity to gamma +/- 1 SE...")

gamma_lo <- gamma - gamma_se  # more negative = larger effect
gamma_hi <- gamma + gamma_se  # less negative = smaller effect

# Recompute intensive SOS at bounds
baci_T[, sos_int_lo := abs(gamma_lo) * pci_std * derisked * trade_value]
baci_T[, sos_int_hi := abs(gamma_hi) * pci_std * derisked * trade_value]

sos_lo <- baci_T[!is.na(sos_int_lo),
                  .(sos_lo = sum(sos_int_lo, na.rm = TRUE)),
                  by = .(iso3 = iso3_o)]
sos_hi <- baci_T[!is.na(sos_int_hi),
                  .(sos_hi = sum(sos_int_hi, na.rm = TRUE)),
                  by = .(iso3 = iso3_o)]

sos_country <- merge(sos_country, sos_lo, by = "iso3", all.x = TRUE)
sos_country <- merge(sos_country, sos_hi, by = "iso3", all.x = TRUE)

# Rank at bounds
sos_country[!is.na(sos_lo), rank_lo := frank(-sos_lo)]
sos_country[!is.na(sos_hi), rank_hi := frank(-sos_hi)]
sos_country[, rank_range := abs(fifelse(is.na(rank_hi), 0L,
                                         as.integer(rank_hi)) -
                                 fifelse(is.na(rank_lo), 0L,
                                         as.integer(rank_lo)))]

# Save updated
write_clean(sos_country, "sos_country.parquet")

# ---------------------------------------------------------------------------
# 9. Output tables
# ---------------------------------------------------------------------------
log_time("Producing output tables...")

# Top 20 countries
top20 <- sos_country[rank_total <= 20,
                     .(iso3, rank_total, sos_total,
                       sos_intensive_total, sos_extensive_total,
                       n_derisked_partners, trade_at_risk,
                       rank_lo, rank_hi, rank_range)]
fwrite(top20, file.path(TABLE_DIR, "top20_countries.csv"))
log_time("  Top-20 countries saved")

# Top 50 country × product pairs
sos_cp_ranked <- sos_cp[order(-sos_combined)]
top50_cp <- head(sos_cp_ranked[, .(iso3, hs4, sos_combined,
                                    sos_int_norm, sos_ext_norm,
                                    pci_std, trade_derisked)], 50)
fwrite(top50_cp, file.path(TABLE_DIR, "top50_country_product.csv"))

# Rank sensitivity table
rank_sensitivity <- sos_country[rank_total <= 20,
                                .(iso3, rank_total, rank_lo, rank_hi, rank_range)]
fwrite(rank_sensitivity, file.path(TABLE_DIR, "rank_sensitivity_top20.csv"))
log_time("  Rank sensitivity table saved")
if (nrow(rank_sensitivity) > 0) {
  log_time(sprintf("  Top-20 mean rank range (gamma +/- 1 SE): %.1f positions",
                   mean(rank_sensitivity$rank_range, na.rm = TRUE)))
}

# De-risking exposure by country
derisking_summary <- derisking_country[order(-n_derisked)]
fwrite(head(derisking_summary, 30),
       file.path(TABLE_DIR, "derisking_exposure_top30.csv"))
log_time("  De-risking exposure table saved")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Stablecoin Opportunity Score")
log_time(sprintf("Key coefficient: gamma = %.4f (from %s)",
                 gamma, if (!is.null(gamma_name)) gamma_name else "placeholder"))
log_time(sprintf("Country-product SOS pairs: %s",
                 format(nrow(sos_cp), big.mark = ",")))
log_time(sprintf("Countries ranked: %d", nrow(sos_country)))
log_time(sprintf("De-risked corridors: %d", n_derisked))

if (nrow(top20) > 0) {
  log_time("\nTop 10 countries by SOS:")
  for (i in 1:min(10, nrow(top20))) {
    log_time(sprintf("  %2d. %s (SOS: %.3f, derisked partners: %d, trade at risk: $%.0fM)",
                     top20$rank_total[i], top20$iso3[i],
                     top20$sos_total[i], top20$n_derisked_partners[i],
                     top20$trade_at_risk[i] / 1e6))
  }
}

log_time("\nDone. Next: R/10_validation.R")
