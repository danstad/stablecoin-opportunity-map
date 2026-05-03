# ===========================================================================
# _run_estimation_reframed.R — Cross-sectional identification + de-risking
#
# Path 3: Cross-sectional PF × PCI as primary result.
# De-risking reduced form for causal credibility.
#
# Uses 1000-pair medium sample for validation.
# ===========================================================================

library(data.table)
library(fixest)

cat("=" , rep("=", 59), "\n", sep="")
cat("REFRAMED ESTIMATION: Cross-sectional + De-risking\n")
cat("=" , rep("=", 59), "\n", sep="")

# ---- Load ----
cat("\nLoading data...\n")
ps <- fread("data/cleaned/panel_estimation_medium.csv")
cat(sprintf("  %s rows, %d pairs, %d products\n",
            format(nrow(ps), big.mark=","), uniqueN(ps$pair), uniqueN(ps$hs4)))

# Types
for (v in c("trade_value","ln_dist","pci_std","pf_cbr","fdi_bilateral"))
  if (v %in% names(ps)) ps[, (v) := as.numeric(get(v))]
for (v in c("contig","comlang_off","colony"))
  if (v %in% names(ps)) ps[, (v) := as.integer(get(v))]
ps[, exporter_year := as.factor(exporter_year)]
ps[, importer_year := as.factor(importer_year)]
ps[, pair := as.factor(pair)]
ps[, hs4 := as.factor(hs4)]

# Estimation sample
ps_est <- ps[!is.na(ln_dist) & !is.na(pf_cbr) & !is.na(pci_std)]
cat(sprintf("  Estimation sample: %s rows\n", format(nrow(ps_est), big.mark=",")))

# =========================================================================
# PART A: CROSS-SECTIONAL SPECIFICATIONS (PRIMARY)
# =========================================================================
cat("\n", rep("=", 60), "\n", sep="")
cat("PART A: CROSS-SECTIONAL IDENTIFICATION\n")
cat("  FEs: exporter×year + importer×year + product\n")
cat("  Identification: between-pair variation in financial linkage\n")
cat(rep("=", 60), "\n", sep="")

# ---- A1: Baseline gravity (no PF) ----
cat("\n--- A1: Gravity baseline ---\n")
t0 <- Sys.time()
a1 <- fepois(trade_value ~ ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est, cluster = ~pair, nthreads = 4)
cat(sprintf("  Time: %.0f sec, N: %s\n",
            difftime(Sys.time(), t0, units="secs"), format(nobs(a1), big.mark=",")))
cat(sprintf("  ln_dist: %.4f (%.4f) ***\n", coef(a1)["ln_dist"], se(a1)["ln_dist"]))
cat(sprintf("  contig:  %.4f (%.4f)\n", coef(a1)["contig"], se(a1)["contig"]))

# ---- A2: Gravity + PF level ----
cat("\n--- A2: Gravity + PF ---\n")
t0 <- Sys.time()
a2 <- fepois(trade_value ~ pf_cbr + ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est, cluster = ~pair, nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
cat(sprintf("  pf_cbr:  %.4f (%.4f, p=%.4f) %s\n",
            coef(a2)["pf_cbr"], se(a2)["pf_cbr"], pvalue(a2)["pf_cbr"],
            ifelse(pvalue(a2)["pf_cbr"] < 0.01, "***", "")))

# ---- A3: KEY — PF × PCI interaction (cross-sectional) ----
cat("\n--- A3: PF × PCI interaction (KEY SPECIFICATION) ---\n")
cat("  trade ~ pf_cbr + pf_cbr:pci_std + gravity | exp_yr + imp_yr + hs4\n")
t0 <- Sys.time()
a3 <- fepois(trade_value ~ pf_cbr + pf_cbr:pci_std +
               ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est, cluster = ~pair, nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
cat(sprintf("  pf_cbr:          %.4f (%.4f, p=%.4f) %s\n",
            coef(a3)["pf_cbr"], se(a3)["pf_cbr"], pvalue(a3)["pf_cbr"],
            ifelse(pvalue(a3)["pf_cbr"] < 0.01, "***",
                   ifelse(pvalue(a3)["pf_cbr"] < 0.05, "**", ""))))
cat(sprintf("  pf_cbr:pci_std:  %.4f (%.4f, p=%.4f) %s\n",
            coef(a3)["pf_cbr:pci_std"], se(a3)["pf_cbr:pci_std"],
            pvalue(a3)["pf_cbr:pci_std"],
            ifelse(pvalue(a3)["pf_cbr:pci_std"] < 0.01, "***",
                   ifelse(pvalue(a3)["pf_cbr:pci_std"] < 0.05, "**",
                          ifelse(pvalue(a3)["pf_cbr:pci_std"] < 0.10, "*", "")))))

# ---- A4: PF × PCI + PCI level (to show interaction isn't just PCI main effect) ----
cat("\n--- A4: PF × PCI + PCI level ---\n")
t0 <- Sys.time()
a4 <- fepois(trade_value ~ pf_cbr + pci_std + pf_cbr:pci_std +
               ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est, cluster = ~pair, nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
cat(sprintf("  pf_cbr:          %.4f (%.4f, p=%.4f)\n",
            coef(a4)["pf_cbr"], se(a4)["pf_cbr"], pvalue(a4)["pf_cbr"]))
cat(sprintf("  pci_std:         %.4f (%.4f, p=%.4f)\n",
            coef(a4)["pci_std"], se(a4)["pci_std"], pvalue(a4)["pci_std"]))
cat(sprintf("  pf_cbr:pci_std:  %.4f (%.4f, p=%.4f) %s\n",
            coef(a4)["pf_cbr:pci_std"], se(a4)["pf_cbr:pci_std"],
            pvalue(a4)["pf_cbr:pci_std"],
            ifelse(pvalue(a4)["pf_cbr:pci_std"] < 0.01, "***",
                   ifelse(pvalue(a4)["pf_cbr:pci_std"] < 0.05, "**",
                          ifelse(pvalue(a4)["pf_cbr:pci_std"] < 0.10, "*", "")))))

# =========================================================================
# PART B: DE-RISKING REDUCED FORM (CAUSAL CREDIBILITY)
# =========================================================================
cat("\n", rep("=", 60), "\n", sep="")
cat("PART B: DE-RISKING REDUCED FORM\n")
cat("  Exploits large discrete changes in bilateral FDI as proxy\n")
cat("  for correspondent banking relationship disruptions\n")
cat(rep("=", 60), "\n", sep="")

# Construct de-risking indicator:
# A pair is "de-risked" if bilateral FDI drops by > 50% relative to
# its 2015-2017 base period average (or if FDI goes from positive to zero)
cat("\nConstructing de-risking indicator...\n")

# Compute base period FDI for each pair
base_fdi <- ps[year %in% 2015:2017 & !is.na(fdi_bilateral),
               .(fdi_base = mean(fdi_bilateral, na.rm=TRUE)),
               by = pair]
ps_est <- merge(ps_est, base_fdi, by = "pair", all.x = TRUE)

# De-risking: FDI dropped by > 50% from base
ps_est[, fdi_ratio := fdi_bilateral / fifelse(fdi_base > 0, fdi_base, NA_real_)]
ps_est[, derisked := as.integer(!is.na(fdi_ratio) & fdi_ratio < 0.5)]

n_derisked_pairs <- uniqueN(ps_est[derisked == 1]$pair)
n_derisked_obs <- sum(ps_est$derisked, na.rm=TRUE)
cat(sprintf("  De-risked pairs: %d (of %d)\n",
            n_derisked_pairs, uniqueN(ps_est$pair)))
cat(sprintf("  De-risked obs:   %s (%.1f%%)\n",
            format(n_derisked_obs, big.mark=","),
            100 * mean(ps_est$derisked, na.rm=TRUE)))

if (n_derisked_pairs >= 10) {
  # ---- B1: De-risking main effect ----
  cat("\n--- B1: De-risking main effect ---\n")
  t0 <- Sys.time()
  b1 <- fepois(trade_value ~ derisked + ln_dist + contig + comlang_off + colony |
                 exporter_year + importer_year + hs4,
               data = ps_est, cluster = ~pair, nthreads = 4)
  cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
  cat(sprintf("  derisked: %.4f (%.4f, p=%.4f) %s\n",
              coef(b1)["derisked"], se(b1)["derisked"], pvalue(b1)["derisked"],
              ifelse(pvalue(b1)["derisked"] < 0.01, "***",
                     ifelse(pvalue(b1)["derisked"] < 0.05, "**", ""))))

  # ---- B2: De-risking × PCI (KEY causal test) ----
  cat("\n--- B2: De-risking × PCI (CAUSAL TEST) ---\n")
  cat("  trade ~ derisked + derisked:pci_std + gravity | exp_yr + imp_yr + hs4\n")
  t0 <- Sys.time()
  b2 <- fepois(trade_value ~ derisked + derisked:pci_std +
                 ln_dist + contig + comlang_off + colony |
                 exporter_year + importer_year + hs4,
               data = ps_est, cluster = ~pair, nthreads = 4)
  cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
  cat(sprintf("  derisked:          %.4f (%.4f, p=%.4f) %s\n",
              coef(b2)["derisked"], se(b2)["derisked"], pvalue(b2)["derisked"],
              ifelse(pvalue(b2)["derisked"] < 0.01, "***",
                     ifelse(pvalue(b2)["derisked"] < 0.05, "**", ""))))
  cat(sprintf("  derisked:pci_std:  %.4f (%.4f, p=%.4f) %s\n",
              coef(b2)["derisked:pci_std"], se(b2)["derisked:pci_std"],
              pvalue(b2)["derisked:pci_std"],
              ifelse(pvalue(b2)["derisked:pci_std"] < 0.01, "***",
                     ifelse(pvalue(b2)["derisked:pci_std"] < 0.05, "**",
                            ifelse(pvalue(b2)["derisked:pci_std"] < 0.10, "*", "")))))

  # ---- B3: De-risking with pair FE (within-pair, exploiting shock timing) ----
  cat("\n--- B3: De-risking with pair FEs ---\n")
  cat("  trade ~ derisked + derisked:pci_std | exp_yr + imp_yr + pair + hs4\n")
  t0 <- Sys.time()
  b3 <- fepois(trade_value ~ derisked + derisked:pci_std |
                 exporter_year + importer_year + pair + hs4,
               data = ps_est, cluster = ~pair, nthreads = 4)
  cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
  cat(sprintf("  derisked:          %.4f (%.4f, p=%.4f) %s\n",
              coef(b3)["derisked"], se(b3)["derisked"], pvalue(b3)["derisked"],
              ifelse(pvalue(b3)["derisked"] < 0.01, "***",
                     ifelse(pvalue(b3)["derisked"] < 0.05, "**", ""))))
  cat(sprintf("  derisked:pci_std:  %.4f (%.4f, p=%.4f) %s\n",
              coef(b3)["derisked:pci_std"], se(b3)["derisked:pci_std"],
              pvalue(b3)["derisked:pci_std"],
              ifelse(pvalue(b3)["derisked:pci_std"] < 0.01, "***",
                     ifelse(pvalue(b3)["derisked:pci_std"] < 0.05, "**",
                            ifelse(pvalue(b3)["derisked:pci_std"] < 0.10, "*", "")))))
} else {
  cat("  Too few de-risked pairs for estimation. Skipping Part B.\n")
  b1 <- b2 <- b3 <- NULL
}

# =========================================================================
# PART C: ALTERNATIVE PF MEASURES
# =========================================================================
cat("\n", rep("=", 60), "\n", sep="")
cat("PART C: ALTERNATIVE FRICTION MEASURES\n")
cat(rep("=", 60), "\n", sep="")

# C1: Use FDI level directly (not log-transformed)
cat("\n--- C1: Raw FDI bilateral (higher = more linkage = less friction) ---\n")
ps_est[, fdi_std := scale(fdi_bilateral)[,1]]
t0 <- Sys.time()
c1 <- fepois(trade_value ~ fdi_std + fdi_std:pci_std +
               ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est[!is.na(fdi_std)], cluster = ~pair, nthreads = 4)
cat(sprintf("  Time: %.0f sec\n", difftime(Sys.time(), t0, units="secs")))
cat(sprintf("  fdi_std:          %.4f (%.4f, p=%.4f) %s\n",
            coef(c1)["fdi_std"], se(c1)["fdi_std"], pvalue(c1)["fdi_std"],
            ifelse(pvalue(c1)["fdi_std"] < 0.01, "***", "")))
cat(sprintf("  fdi_std:pci_std:  %.4f (%.4f, p=%.4f) %s\n",
            coef(c1)["fdi_std:pci_std"], se(c1)["fdi_std:pci_std"],
            pvalue(c1)["fdi_std:pci_std"],
            ifelse(pvalue(c1)["fdi_std:pci_std"] < 0.01, "***",
                   ifelse(pvalue(c1)["fdi_std:pci_std"] < 0.05, "**",
                          ifelse(pvalue(c1)["fdi_std:pci_std"] < 0.10, "*", "")))))
cat("  NOTE: fdi_std is linkage (positive = good). Expect fdi_std > 0, interaction > 0\n")
cat("        (more financial linkage helps complex products MORE)\n")

# =========================================================================
# SUMMARY
# =========================================================================
cat("\n", rep("=", 60), "\n", sep="")
cat("FULL RESULTS SUMMARY\n")
cat(rep("=", 60), "\n", sep="")

cat("\nPart A (Cross-sectional, primary):\n")
cat(sprintf("  A2: pf_cbr          = %.4f (p=%.4f) %s\n",
            coef(a2)["pf_cbr"], pvalue(a2)["pf_cbr"],
            ifelse(pvalue(a2)["pf_cbr"] < 0.01, "***", "")))
cat(sprintf("  A3: pf_cbr          = %.4f (p=%.4f)\n",
            coef(a3)["pf_cbr"], pvalue(a3)["pf_cbr"]))
cat(sprintf("  A3: pf_cbr:pci_std  = %.4f (p=%.4f) %s  << KEY\n",
            coef(a3)["pf_cbr:pci_std"], pvalue(a3)["pf_cbr:pci_std"],
            ifelse(pvalue(a3)["pf_cbr:pci_std"] < 0.05, "**",
                   ifelse(pvalue(a3)["pf_cbr:pci_std"] < 0.10, "*", ""))))

if (!is.null(b2)) {
  cat("\nPart B (De-risking, causal credibility):\n")
  cat(sprintf("  B2: derisked:pci_std = %.4f (p=%.4f) %s\n",
              coef(b2)["derisked:pci_std"], pvalue(b2)["derisked:pci_std"],
              ifelse(pvalue(b2)["derisked:pci_std"] < 0.05, "**",
                     ifelse(pvalue(b2)["derisked:pci_std"] < 0.10, "*", ""))))
  if (!is.null(b3)) {
    cat(sprintf("  B3: derisked:pci_std = %.4f (p=%.4f) %s  (with pair FE)\n",
                coef(b3)["derisked:pci_std"], pvalue(b3)["derisked:pci_std"],
                ifelse(pvalue(b3)["derisked:pci_std"] < 0.05, "**",
                       ifelse(pvalue(b3)["derisked:pci_std"] < 0.10, "*", ""))))
  }
}

cat("\nPart C (Alternative measures):\n")
cat(sprintf("  C1: fdi_std:pci_std = %.4f (p=%.4f) %s\n",
            coef(c1)["fdi_std:pci_std"], pvalue(c1)["fdi_std:pci_std"],
            ifelse(pvalue(c1)["fdi_std:pci_std"] < 0.05, "**",
                   ifelse(pvalue(c1)["fdi_std:pci_std"] < 0.10, "*", ""))))

# Save all estimates
estimates_reframed <- list(
  a1_gravity = a1, a2_pf = a2, a3_pf_pci = a3, a4_pf_pci_level = a4,
  b1_derisked = if (exists("b1")) b1 else NULL,
  b2_derisked_pci = if (exists("b2")) b2 else NULL,
  b3_derisked_pci_pairfe = if (exists("b3")) b3 else NULL,
  c1_fdi_std = c1
)
saveRDS(estimates_reframed, "data/cleaned/estimates_reframed.rds")
cat("\nEstimates saved to estimates_reframed.rds\n")
cat("Done.\n")
