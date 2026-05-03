# ===========================================================================
# _run_estimation_medium.R — PPML on 1000-pair sample (panel specs)
#
# This is the real validation: pair FEs, within-pair cross-product variation.
# 1000 pairs × 94 products × 9 years ≈ 739K rows
# ===========================================================================

library(data.table)
library(fixest)

cat("=" , rep("=", 59), "\n", sep="")
cat("PPML Estimation — 1000-pair Panel Sample\n")
cat("=" , rep("=", 59), "\n", sep="")

cat("\nLoading data...\n")
ps <- fread("data/cleaned/panel_estimation_medium.csv")
cat(sprintf("  Loaded: %s rows\n", format(nrow(ps), big.mark=",")))

# Types
ps[, trade_value := as.numeric(trade_value)]
ps[, ln_dist := as.numeric(ln_dist)]
ps[, contig := as.integer(contig)]
ps[, comlang_off := as.integer(comlang_off)]
ps[, colony := as.integer(colony)]
ps[, pci_std := as.numeric(pci_std)]
ps[, pf_cbr := as.numeric(pf_cbr)]
ps[, exporter_year := as.factor(exporter_year)]
ps[, importer_year := as.factor(importer_year)]
ps[, pair := as.factor(pair)]
ps[, hs4 := as.factor(hs4)]

cat(sprintf("  Pairs: %d, Products: %d, Years: %d\n",
            uniqueN(ps$pair), uniqueN(ps$hs4), uniqueN(ps$year)))
cat(sprintf("  Positive trade: %s (%.1f%%)\n",
            format(sum(ps$trade_value > 0), big.mark=","),
            100 * mean(ps$trade_value > 0)))

# ---- Spec 1: Baseline Gravity ----
cat("\n--- Spec 1: Baseline Gravity ---\n")
t0 <- Sys.time()
m1 <- fepois(trade_value ~ ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps[!is.na(ln_dist)], cluster = ~pair,
             nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units = "secs")))
cat(sprintf("  ln_dist: %.4f (SE %.4f) %s\n",
            coef(m1)["ln_dist"], se(m1)["ln_dist"],
            ifelse(pvalue(m1)["ln_dist"] < 0.01, "***", "")))
cat(sprintf("  contig:  %.4f (SE %.4f) %s\n",
            coef(m1)["contig"], se(m1)["contig"],
            ifelse(pvalue(m1)["contig"] < 0.01, "***", "")))
cat(sprintf("  N: %s\n", format(nobs(m1), big.mark=",")))

# ---- Spec 2a: PF cross-sectional ----
cat("\n--- Spec 2a: PF cross-sectional ---\n")
t0 <- Sys.time()
m2a <- fepois(trade_value ~ pf_cbr + ln_dist + contig + comlang_off + colony |
                exporter_year + importer_year + hs4,
              data = ps[!is.na(ln_dist)], cluster = ~pair,
              nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units = "secs")))
cat(sprintf("  pf_cbr: %.4f (SE %.4f, p=%.4f) %s\n",
            coef(m2a)["pf_cbr"], se(m2a)["pf_cbr"], pvalue(m2a)["pf_cbr"],
            ifelse(pvalue(m2a)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m2a)["pf_cbr"] < 0.05, "**", ""))))

# ---- Spec 2b: PF within-pair ----
cat("\n--- Spec 2b: PF within-pair ---\n")
t0 <- Sys.time()
m2b <- fepois(trade_value ~ pf_cbr |
                exporter_year + importer_year + pair + hs4,
              data = ps, cluster = ~pair,
              nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units = "secs")))
cat(sprintf("  pf_cbr: %.4f (SE %.4f, p=%.4f) %s\n",
            coef(m2b)["pf_cbr"], se(m2b)["pf_cbr"], pvalue(m2b)["pf_cbr"],
            ifelse(pvalue(m2b)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m2b)["pf_cbr"] < 0.05, "**", ""))))

# ---- Spec 3: KEY — PF x PCI ----
cat("\n--- Spec 3: PF x PCI (KEY) ---\n")
t0 <- Sys.time()
m3 <- fepois(trade_value ~ pf_cbr + pf_cbr:pci_std |
               exporter_year + importer_year + pair + hs4,
             data = ps, cluster = ~pair,
             nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units = "secs")))
cat(sprintf("  pf_cbr:          %.4f (SE %.4f, p=%.4f) %s\n",
            coef(m3)["pf_cbr"], se(m3)["pf_cbr"], pvalue(m3)["pf_cbr"],
            ifelse(pvalue(m3)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(m3)["pf_cbr"] < 0.05, "**", ""))))
cat(sprintf("  pf_cbr:pci_std:  %.4f (SE %.4f, p=%.4f) %s\n",
            coef(m3)["pf_cbr:pci_std"], se(m3)["pf_cbr:pci_std"],
            pvalue(m3)["pf_cbr:pci_std"],
            ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.01, "***",
                   ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.05, "**",
                          ifelse(pvalue(m3)["pf_cbr:pci_std"] < 0.10, "*", "")))))

# ---- VERDICT ----
cat("\n", rep("=", 60), "\n", sep="")
cat("RESULTS (1000-pair panel)\n")
cat(rep("=", 60), "\n", sep="")

alpha2 <- coef(m3)["pf_cbr:pci_std"]
pval <- pvalue(m3)["pf_cbr:pci_std"]
cat(sprintf("\n  alpha_2 = %.6f (SE %.6f, p = %.4f)\n",
            alpha2, se(m3)["pf_cbr:pci_std"], pval))

if (alpha2 < 0 & pval < 0.05) {
  cat("  >> SIGNIFICANT AND NEGATIVE — Theory confirmed\n")
} else if (alpha2 < 0 & pval < 0.10) {
  cat("  >> Negative, marginally significant\n")
} else if (alpha2 < 0) {
  cat("  >> Negative, not yet significant (expect improvement with full sample)\n")
} else {
  cat("  >> Not negative — investigate\n")
}

cat(sprintf("\n  Gravity: dist=%.3f, contig=%.3f, lang=%.3f, colony=%.3f\n",
            coef(m1)["ln_dist"], coef(m1)["contig"],
            coef(m1)["comlang_off"], coef(m1)["colony"]))

# Save
saveRDS(list(spec1=m1, spec2a=m2a, spec2b=m2b, spec3=m3),
        "data/cleaned/estimates_medium.rds")
cat("\nEstimates saved. Done.\n")
