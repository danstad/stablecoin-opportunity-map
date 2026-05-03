# ===========================================================================
# _run_estimation_yearly.R — Year-by-year cross-sectional PPML
#
# Estimates gravity + PF x PCI interaction for each year separately.
# Shows how the effect evolves over time.
# Uses medium sample (1000 pairs) for better precision per year.
# ===========================================================================

library(data.table)
library(fixest)

cat("=" , rep("=", 59), "\n", sep="")
cat("Year-by-Year PPML Estimation (1000-pair sample)\n")
cat("=" , rep("=", 59), "\n", sep="")

# Load medium sample
cat("\nLoading data...\n")
ps <- fread("data/cleaned/panel_estimation_medium.csv")
cat(sprintf("  Loaded: %s rows, %d pairs\n", format(nrow(ps), big.mark=","), uniqueN(ps$pair)))

# Ensure types
ps[, trade_value := as.numeric(trade_value)]
ps[, ln_dist := as.numeric(ln_dist)]
ps[, contig := as.integer(contig)]
ps[, comlang_off := as.integer(comlang_off)]
ps[, colony := as.integer(colony)]
ps[, pci_std := as.numeric(pci_std)]
ps[, pf_cbr := as.numeric(pf_cbr)]

# Results storage
years <- sort(unique(ps$year))
results <- data.table(
  year = integer(),
  spec = character(),
  coef_name = character(),
  estimate = numeric(),
  se = numeric(),
  pvalue = numeric(),
  nobs = integer()
)

for (yr in years) {
  cat(sprintf("\n--- Year %d ---\n", yr))
  d <- ps[year == yr]
  cat(sprintf("  Obs: %s, Positive trade: %s (%.1f%%)\n",
              format(nrow(d), big.mark=","),
              format(sum(d$trade_value > 0), big.mark=","),
              100 * mean(d$trade_value > 0)))

  # Spec 1: Gravity baseline (cross-section, no pair FE)
  tryCatch({
    m1 <- fepois(trade_value ~ ln_dist + contig + comlang_off + colony + pf_cbr |
                   iso3_o + iso3_d + hs4,
                 data = d[!is.na(ln_dist) & !is.na(pf_cbr)],
                 cluster = ~pair)

    results <- rbind(results, data.table(
      year = yr, spec = "gravity+pf",
      coef_name = "pf_cbr",
      estimate = coef(m1)["pf_cbr"],
      se = se(m1)["pf_cbr"],
      pvalue = pvalue(m1)["pf_cbr"],
      nobs = nobs(m1)
    ))
    results <- rbind(results, data.table(
      year = yr, spec = "gravity+pf",
      coef_name = "ln_dist",
      estimate = coef(m1)["ln_dist"],
      se = se(m1)["ln_dist"],
      pvalue = pvalue(m1)["ln_dist"],
      nobs = nobs(m1)
    ))
    cat(sprintf("  Gravity+PF: dist=%.3f, pf_cbr=%.3f (p=%.3f)\n",
                coef(m1)["ln_dist"], coef(m1)["pf_cbr"], pvalue(m1)["pf_cbr"]))
  }, error = function(e) cat(sprintf("  Gravity+PF failed: %s\n", e$message)))

  # Spec 3 cross-section: PF x PCI (KEY)
  tryCatch({
    m3 <- fepois(trade_value ~ pf_cbr + pf_cbr:pci_std + ln_dist + contig + comlang_off + colony |
                   iso3_o + iso3_d + hs4,
                 data = d[!is.na(ln_dist) & !is.na(pf_cbr)],
                 cluster = ~pair)

    results <- rbind(results, data.table(
      year = yr, spec = "pf_x_pci",
      coef_name = "pf_cbr",
      estimate = coef(m3)["pf_cbr"],
      se = se(m3)["pf_cbr"],
      pvalue = pvalue(m3)["pf_cbr"],
      nobs = nobs(m3)
    ))
    results <- rbind(results, data.table(
      year = yr, spec = "pf_x_pci",
      coef_name = "pf_cbr:pci_std",
      estimate = coef(m3)["pf_cbr:pci_std"],
      se = se(m3)["pf_cbr:pci_std"],
      pvalue = pvalue(m3)["pf_cbr:pci_std"],
      nobs = nobs(m3)
    ))
    cat(sprintf("  PF x PCI:   alpha_2=%.4f (SE %.4f, p=%.3f) %s\n",
                coef(m3)["pf_cbr:pci_std"],
                se(m3)["pf_cbr:pci_std"],
                pvalue(m3)["pf_cbr:pci_std"],
                ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.05, "**",
                       ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.10, "*", ""))))
  }, error = function(e) cat(sprintf("  PF x PCI failed: %s\n", e$message)))
}

# ---- Summary table ----
cat("\n", rep("=", 70), "\n", sep="")
cat("YEAR-BY-YEAR alpha_2 (PF x PCI interaction)\n")
cat(rep("=", 70), "\n", sep="")
cat(sprintf("%-6s  %10s  %10s  %10s  %6s  %s\n",
            "Year", "alpha_2", "SE", "p-value", "N", "Sig"))
cat(rep("-", 70), "\n", sep="")

alpha2_by_year <- results[spec == "pf_x_pci" & coef_name == "pf_cbr:pci_std"]
for (i in seq_len(nrow(alpha2_by_year))) {
  r <- alpha2_by_year[i]
  sig <- ifelse(r$pvalue < 0.01, "***",
                ifelse(r$pvalue < 0.05, "**",
                       ifelse(r$pvalue < 0.10, "*", "")))
  cat(sprintf("%-6d  %10.4f  %10.4f  %10.4f  %6s  %s\n",
              r$year, r$estimate, r$se, r$pvalue,
              format(r$nobs, big.mark=","), sig))
}

# Save
cat("\nSaving results...\n")
fwrite(results, "data/cleaned/estimation_yearly_results.csv")
saveRDS(results, "data/cleaned/estimation_yearly_results.rds")
cat("Done.\n")
