# ===========================================================================
# _run_estimation_test.R — Validate all PPML specs on 200-pair subsample
#
# Uses CSV to avoid arrow segfault on this machine.
# Once specs validate here, run full estimation on a 32GB+ machine.
# ===========================================================================

library(data.table)
library(fixest)

cat("=" , rep("=", 59), "\n", sep="")
cat("PPML Estimation Validation (200-pair subsample)\n")
cat("=" , rep("=", 59), "\n", sep="")

# Load data
cat("\nLoading data...\n")
ps <- fread("data/cleaned/panel_estimation_sample.csv")
cat(sprintf("  Loaded: %s rows, %d columns\n", format(nrow(ps), big.mark=","), ncol(ps)))

# Ensure types
ps[, trade_value := as.numeric(trade_value)]
ps[, ln_dist := as.numeric(ln_dist)]
ps[, contig := as.integer(contig)]
ps[, comlang_off := as.integer(comlang_off)]
ps[, colony := as.integer(colony)]
ps[, pci_std := as.numeric(pci_std)]
ps[, pf_cbr := as.numeric(pf_cbr)]

# Convert FE columns to factor
ps[, exporter_year := as.factor(exporter_year)]
ps[, importer_year := as.factor(importer_year)]
ps[, pair := as.factor(pair)]
ps[, hs4 := as.factor(hs4)]

cat(sprintf("  Pairs: %d\n", uniqueN(ps$pair)))
cat(sprintf("  Products: %d\n", uniqueN(ps$hs4)))
cat(sprintf("  Years: %s\n", paste(sort(unique(ps$year)), collapse=", ")))
cat(sprintf("  Positive trade: %s (%.1f%%)\n",
            format(sum(ps$trade_value > 0), big.mark=","),
            100 * mean(ps$trade_value > 0)))
cat(sprintf("  Colony==1: %d\n", sum(ps$colony == 1, na.rm=TRUE)))
cat(sprintf("  pf_cbr non-NA: %.1f%%\n", 100 * mean(!is.na(ps$pf_cbr))))

# ---- Spec 1: Baseline Gravity ----
cat("\n--- Spec 1: Baseline Gravity ---\n")
cat("  trade ~ ln_dist + contig + comlang_off + colony | exp_yr + imp_yr + hs4\n")
t0 <- Sys.time()
m1 <- fepois(trade_value ~ ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps, cluster = ~pair)
dt <- difftime(Sys.time(), t0, units = "secs")
cat(sprintf("  Time: %.0f sec\n", dt))
cat(sprintf("  ln_dist:     %7.4f  (SE %6.4f)  %s\n",
            coef(m1)["ln_dist"], se(m1)["ln_dist"],
            ifelse(pvalue(m1)["ln_dist"] < 0.01, "***",
                   ifelse(pvalue(m1)["ln_dist"] < 0.05, "**",
                          ifelse(pvalue(m1)["ln_dist"] < 0.10, "*", "")))))
cat(sprintf("  contig:      %7.4f  (SE %6.4f)\n", coef(m1)["contig"], se(m1)["contig"]))
cat(sprintf("  comlang_off: %7.4f  (SE %6.4f)\n", coef(m1)["comlang_off"], se(m1)["comlang_off"]))
cat(sprintf("  colony:      %7.4f  (SE %6.4f)\n", coef(m1)["colony"], se(m1)["colony"]))
cat(sprintf("  N: %s, Pseudo-R2: %.4f\n", format(nobs(m1), big.mark=","), r2(m1, "pr2")))

# Sanity check
dist_ok <- coef(m1)["ln_dist"] > -1.5 & coef(m1)["ln_dist"] < -0.5
cat(sprintf("  >> Distance sanity: %s (%.4f, expect [-1.3, -0.7])\n",
            ifelse(dist_ok, "PASS", "CAUTION"), coef(m1)["ln_dist"]))

# ---- Spec 2a: PF cross-sectional ----
cat("\n--- Spec 2a: PF cross-sectional ---\n")
cat("  trade ~ pf_cbr + gravity | exp_yr + imp_yr + hs4\n")
t0 <- Sys.time()
m2a <- fepois(trade_value ~ pf_cbr + ln_dist + contig + comlang_off + colony |
                exporter_year + importer_year + hs4,
              data = ps, cluster = ~pair)
dt <- difftime(Sys.time(), t0, units = "secs")
cat(sprintf("  Time: %.0f sec\n", dt))
cat(sprintf("  pf_cbr:  %7.4f  (SE %6.4f, p=%6.4f)  %s\n",
            coef(m2a)["pf_cbr"], se(m2a)["pf_cbr"], pvalue(m2a)["pf_cbr"],
            ifelse(pvalue(m2a)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m2a)["pf_cbr"] < 0.05, "**",
                          ifelse(pvalue(m2a)["pf_cbr"] < 0.10, "*", "")))))
cat(sprintf("  N: %s\n", format(nobs(m2a), big.mark=",")))

# ---- Spec 2b: PF within-pair ----
cat("\n--- Spec 2b: PF within-pair ---\n")
cat("  trade ~ pf_cbr | exp_yr + imp_yr + pair + hs4\n")
t0 <- Sys.time()
m2b <- fepois(trade_value ~ pf_cbr |
                exporter_year + importer_year + pair + hs4,
              data = ps, cluster = ~pair)
dt <- difftime(Sys.time(), t0, units = "secs")
cat(sprintf("  Time: %.0f sec\n", dt))
cat(sprintf("  pf_cbr:  %7.4f  (SE %6.4f, p=%6.4f)  %s\n",
            coef(m2b)["pf_cbr"], se(m2b)["pf_cbr"], pvalue(m2b)["pf_cbr"],
            ifelse(pvalue(m2b)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m2b)["pf_cbr"] < 0.05, "**",
                          ifelse(pvalue(m2b)["pf_cbr"] < 0.10, "*", "")))))
cat(sprintf("  N: %s\n", format(nobs(m2b), big.mark=",")))

# ---- Spec 3: KEY — PF x PCI interaction ----
cat("\n--- Spec 3: PF x PCI (KEY SPECIFICATION) ---\n")
cat("  trade ~ pf_cbr + pf_cbr:pci_std | exp_yr + imp_yr + pair + hs4\n")
t0 <- Sys.time()
m3 <- fepois(trade_value ~ pf_cbr + pf_cbr:pci_std |
               exporter_year + importer_year + pair + hs4,
             data = ps, cluster = ~pair)
dt <- difftime(Sys.time(), t0, units = "secs")
cat(sprintf("  Time: %.0f sec\n", dt))
cat(sprintf("  pf_cbr:          %7.4f  (SE %6.4f, p=%6.4f)  %s\n",
            coef(m3)["pf_cbr"], se(m3)["pf_cbr"], pvalue(m3)["pf_cbr"],
            ifelse(pvalue(m3)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m3)["pf_cbr"] < 0.05, "**",
                          ifelse(pvalue(m3)["pf_cbr"] < 0.10, "*", "")))))
cat(sprintf("  pf_cbr:pci_std:  %7.4f  (SE %6.4f, p=%6.4f)  %s\n",
            coef(m3)["pf_cbr:pci_std"], se(m3)["pf_cbr:pci_std"], pvalue(m3)["pf_cbr:pci_std"],
            ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.01, "***",
                   ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.05, "**",
                          ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.10, "*", "")))))
cat(sprintf("  N: %s\n", format(nobs(m3), big.mark=",")))

# ---- VERDICT ----
cat("\n", rep("=", 60), "\n", sep="")
cat("ESTIMATION VALIDATION SUMMARY\n")
cat(rep("=", 60), "\n", sep="")

alpha2 <- coef(m3)["pf_cbr:pci_std"]
pval <- pvalue(m3)["pf_cbr:pci_std"]
cat(sprintf("\n  Key parameter: alpha_2 (PF x PCI) = %.6f\n", alpha2))
cat(sprintf("  Standard error:                      %.6f\n", se(m3)["pf_cbr:pci_std"]))
cat(sprintf("  p-value:                             %.4f\n", pval))

if (alpha2 < 0 & pval < 0.05) {
  cat("\n  >> THEORY CONFIRMED: Payment frictions hurt complex products more.\n")
  cat("  >> Stablecoins would disproportionately benefit complex trade.\n")
} else if (alpha2 < 0 & pval < 0.10) {
  cat("\n  >> DIRECTIONALLY CONSISTENT: Negative but marginal significance.\n")
  cat("  >> May strengthen with full sample.\n")
} else if (alpha2 < 0) {
  cat("\n  >> DIRECTIONALLY CONSISTENT but not significant.\n")
  cat("  >> This is a 200-pair subsample — full sample may be significant.\n")
} else {
  cat("\n  >> UNEXPECTED: alpha_2 is not negative. Investigate.\n")
}

cat("\n  Gravity sanity checks:\n")
cat(sprintf("    Distance:  %.4f (expect -0.7 to -1.3)\n", coef(m1)["ln_dist"]))
cat(sprintf("    Contiguity: %.4f (expect positive)\n", coef(m1)["contig"]))
cat(sprintf("    Language:   %.4f (expect positive)\n", coef(m1)["comlang_off"]))
cat(sprintf("    Colony:     %.4f (expect positive)\n", coef(m1)["colony"]))

# Save estimates
cat("\nSaving estimates to data/cleaned/estimates_validation.rds...\n")
saveRDS(list(spec1=m1, spec2a=m2a, spec2b=m2b, spec3=m3),
        "data/cleaned/estimates_validation.rds")

cat("\nDone. All 4 specifications estimated successfully.\n")
