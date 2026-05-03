# ===========================================================================
# _run_sos_test.R — SOS construction using saved estimates + CSV subsets
#
# Runs the SOS logic on data that fits in memory.
# Uses the validated gamma from estimates_reframed.rds.
# ===========================================================================

library(data.table)
library(arrow)
library(fixest)

cat("=", rep("=", 59), "\n", sep="")
cat("Stablecoin Opportunity Score — Test Construction\n")
cat("=", rep("=", 59), "\n", sep="")

# ---- 1. Load coefficient ----
cat("\nLoading estimates...\n")
est <- readRDS("data/cleaned/estimates_reframed.rds")

# Prefer B3 (pair FE), fall back to B2
if (!is.null(est$b3_derisked_pci_pairfe)) {
  gamma <- coef(est$b3_derisked_pci_pairfe)["derisked:pci_std"]
  gamma_se <- se(est$b3_derisked_pci_pairfe)["derisked:pci_std"]
  cat(sprintf("  gamma (B3, pair FE): %.4f (SE: %.4f)\n", gamma, gamma_se))
} else if (!is.null(est$b2_derisked_pci)) {
  gamma <- coef(est$b2_derisked_pci)["derisked:pci_std"]
  gamma_se <- se(est$b2_derisked_pci)["derisked:pci_std"]
  cat(sprintf("  gamma (B2, cross-sect): %.4f (SE: %.4f)\n", gamma, gamma_se))
} else {
  gamma <- -0.284; gamma_se <- 0.134
  cat(sprintf("  gamma (placeholder): %.4f (SE: %.4f)\n", gamma, gamma_se))
}

pf_level <- if (!is.null(est$a2_pf)) coef(est$a2_pf)["pf_cbr"] else -0.22
cat(sprintf("  PF level effect: %.4f\n", pf_level))

# ---- 2. Load PCI and trade ----
cat("\nLoading PCI and trade data...\n")
pci <- as.data.table(read_parquet("data/cleaned/complexity_pci.parquet"))
baci <- as.data.table(read_parquet("data/cleaned/baci_hs4_hs2_agg.parquet"))

# Use HS2 aggregated BACI data
T_year <- max(baci$year)
baci_T <- baci[year == T_year]
cat(sprintf("  Trade flows: %s (year %d)\n",
            format(nrow(baci_T), big.mark=","), T_year))

# ---- 3. Load FDI and compute de-risking ----
cat("\nComputing de-risking corridors...\n")
fdi <- as.data.table(read_parquet("data/cleaned/imf_fdi_bilateral.parquet"))

# Base period average
base_fdi <- fdi[year %in% 2015:2017,
                .(fdi_base = mean(fdi_bilateral, na.rm=TRUE)),
                by = .(iso3_o, iso3_d)]

# Latest year
fdi_latest <- fdi[year == max(fdi$year)]

derisking <- merge(base_fdi,
                   fdi_latest[, .(iso3_o, iso3_d, fdi_current = fdi_bilateral)],
                   by = c("iso3_o", "iso3_d"), all.x = TRUE)
derisking[, fdi_ratio := fdi_current / fifelse(fdi_base > 0, fdi_base, NA_real_)]
derisking[, derisked := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.5)]

cat(sprintf("  Total corridors: %d\n", nrow(derisking)))
cat(sprintf("  De-risked: %d (%.1f%%)\n",
            sum(derisking$derisked, na.rm=TRUE),
            100 * mean(derisking$derisked, na.rm=TRUE)))

# ---- 4. Intensive SOS ----
cat("\nComputing intensive margin SOS...\n")

# Merge PCI
setnames(baci_T, "hs2", "hs4", skip_absent = TRUE)  # handle hs2 naming
baci_T <- merge(baci_T, pci[, .(hs4, pci_std)], by = "hs4", all.x = TRUE)

# Merge de-risking
baci_T <- merge(baci_T, derisking[, .(iso3_o, iso3_d, derisked)],
                by = c("iso3_o", "iso3_d"), all.x = TRUE)
baci_T[is.na(derisked), derisked := 0L]

# SOS_int = |gamma| × PCI × derisked × trade
abs_gamma <- abs(gamma)
baci_T[, sos_int := abs_gamma * pci_std * derisked * trade_value]

# Aggregate over partners
sos_int <- baci_T[!is.na(sos_int),
                   .(sos_intensive = sum(sos_int, na.rm=TRUE),
                     trade_derisked = sum(trade_value * derisked, na.rm=TRUE),
                     n_derisked_partners = sum(derisked > 0, na.rm=TRUE)),
                   by = .(iso3 = iso3_o, hs4)]

cat(sprintf("  Intensive SOS: %s country-product pairs\n",
            format(nrow(sos_int), big.mark=",")))
cat(sprintf("  Non-zero SOS: %d\n", sum(sos_int$sos_intensive > 0)))

# ---- 5. Extensive SOS ----
cat("\nComputing extensive margin SOS...\n")

rca <- as.data.table(read_parquet("data/cleaned/complexity_rca.parquet"))
dens <- as.data.table(read_parquet("data/cleaned/complexity_density.parquet"))

rca_T <- rca[year == T_year & has_rca == 0]
dens_T <- dens[year == T_year]

ext <- merge(rca_T[, .(iso3, hs4)], dens_T[, .(iso3, hs4, density)],
             by = c("iso3", "hs4"), all.x = TRUE)
ext <- merge(ext, pci[, .(hs4, pci_std)], by = "hs4", all.x = TRUE)

# Country-level de-risking exposure
dr_country <- derisking[, .(frac_derisked = mean(derisked, na.rm=TRUE),
                             n_derisked = sum(derisked, na.rm=TRUE)),
                          by = .(iso3 = iso3_o)]
ext <- merge(ext, dr_country, by = "iso3", all.x = TRUE)
ext[is.na(frac_derisked), frac_derisked := 0]

beta_3 <- -0.05  # placeholder until extensive margin is estimated
ext[, sos_extensive := abs(beta_3) * density * frac_derisked * pci_std]

sos_ext <- ext[!is.na(sos_extensive), .(iso3, hs4, sos_extensive, density)]
cat(sprintf("  Extensive SOS: %s country-product pairs\n",
            format(nrow(sos_ext), big.mark=",")))

# ---- 6. Combine ----
cat("\nCombining intensive + extensive...\n")
omega <- 0.5

sos_cp <- merge(sos_int[, .(iso3, hs4, sos_intensive, trade_derisked, n_derisked_partners)],
                sos_ext[, .(iso3, hs4, sos_extensive, density)],
                by = c("iso3", "hs4"), all = TRUE)
sos_cp[is.na(sos_intensive), sos_intensive := 0]
sos_cp[is.na(sos_extensive), sos_extensive := 0]

# Normalize to [0,1]
max_int <- max(sos_cp$sos_intensive, na.rm=TRUE)
max_ext <- max(sos_cp$sos_extensive, na.rm=TRUE)
if (max_int > 0) sos_cp[, sos_int_norm := sos_intensive / max_int] else sos_cp[, sos_int_norm := 0]
if (max_ext > 0) sos_cp[, sos_ext_norm := sos_extensive / max_ext] else sos_cp[, sos_ext_norm := 0]
sos_cp[, sos_combined := omega * sos_int_norm + (1 - omega) * sos_ext_norm]

# Add PCI
sos_cp <- merge(sos_cp, pci[, .(hs4, pci_std, pci_raw)], by = "hs4", all.x = TRUE)

# Save
write_parquet(as.data.frame(sos_cp), "data/cleaned/sos_country_product.parquet")
cat(sprintf("  Saved sos_country_product.parquet: %s rows\n",
            format(nrow(sos_cp), big.mark=",")))

# ---- 7. Aggregate to country level ----
cat("\nAggregating to country level...\n")

sos_country <- sos_cp[, .(
  sos_total = sum(sos_combined, na.rm=TRUE),
  sos_intensive_total = sum(sos_int_norm, na.rm=TRUE),
  sos_extensive_total = sum(sos_ext_norm, na.rm=TRUE),
  n_products_intensive = sum(sos_intensive > 0),
  n_products_extensive = sum(sos_extensive > 0),
  trade_at_risk = sum(trade_derisked, na.rm=TRUE)
), by = iso3]

# Add country-level de-risking info
sos_country <- merge(sos_country, dr_country, by = "iso3", all.x = TRUE)
sos_country[is.na(n_derisked), n_derisked := 0]

# Rank
sos_country[, rank_total := frank(-sos_total)]
setorder(sos_country, rank_total)

write_parquet(as.data.frame(sos_country), "data/cleaned/sos_country.parquet")

# ---- 8. Uncertainty ----
cat("\nUncertainty (gamma +/- 1 SE)...\n")
gamma_lo <- gamma - gamma_se
gamma_hi <- gamma + gamma_se

baci_T[, sos_lo := abs(gamma_lo) * pci_std * derisked * trade_value]
baci_T[, sos_hi := abs(gamma_hi) * pci_std * derisked * trade_value]

sos_lo_c <- baci_T[!is.na(sos_lo),
                    .(sos_lo = sum(sos_lo, na.rm=TRUE)),
                    by = .(iso3 = iso3_o)]
sos_hi_c <- baci_T[!is.na(sos_hi),
                    .(sos_hi = sum(sos_hi, na.rm=TRUE)),
                    by = .(iso3 = iso3_o)]

sos_country <- merge(sos_country, sos_lo_c, by = "iso3", all.x = TRUE)
sos_country <- merge(sos_country, sos_hi_c, by = "iso3", all.x = TRUE)
sos_country[!is.na(sos_lo), rank_lo := frank(-sos_lo)]
sos_country[!is.na(sos_hi), rank_hi := frank(-sos_hi)]
sos_country[, rank_range := abs(fifelse(is.na(rank_hi), 0L, as.integer(rank_hi)) -
                                 fifelse(is.na(rank_lo), 0L, as.integer(rank_lo)))]

write_parquet(as.data.frame(sos_country), "data/cleaned/sos_country.parquet")

# ---- 9. Print results ----
cat("\n", rep("=", 60), "\n", sep="")
cat("TOP 20 COUNTRIES BY STABLECOIN OPPORTUNITY SCORE\n")
cat(rep("=", 60), "\n", sep="")
cat(sprintf("%-4s %-5s %8s %6s %6s %8s %6s\n",
            "Rank", "ISO3", "SOS", "Int", "Ext", "Trade$M", "DeRisk"))
cat(rep("-", 60), "\n", sep="")

top20 <- sos_country[rank_total <= 20]
for (i in seq_len(nrow(top20))) {
  r <- top20[i]
  cat(sprintf("%-4d %-5s %8.3f %6.2f %6.2f %8.0f %6d\n",
              r$rank_total, r$iso3, r$sos_total,
              r$sos_intensive_total, r$sos_extensive_total,
              r$trade_at_risk / 1e6, r$n_derisked))
}

# Save tables
dir.create("paper/tables/09_sos_construction", recursive = TRUE, showWarnings = FALSE)
fwrite(top20, "paper/tables/09_sos_construction/top20_countries.csv")

top50_cp <- head(sos_cp[order(-sos_combined),
                         .(iso3, hs4, sos_combined, sos_int_norm, sos_ext_norm,
                           pci_std, trade_derisked)], 50)
fwrite(top50_cp, "paper/tables/09_sos_construction/top50_country_product.csv")

cat("\nSaved tables to paper/tables/09_sos_construction/\n")
cat("Done.\n")
