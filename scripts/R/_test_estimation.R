library(data.table)
library(fixest)

cat("Loading data...\n")
ps <- fread("data/cleaned/panel_main_tiny.csv")
cat(sprintf("Loaded: %s rows\n", format(nrow(ps), big.mark=",")))

# Ensure numeric types
ps[, trade_value := as.numeric(trade_value)]
ps[, ln_dist := as.numeric(ln_dist)]
ps[, contig := as.numeric(contig)]
ps[, comlang_off := as.numeric(comlang_off)]
# colony column may be named col45 in CEPII V202211
if ("col45" %in% names(ps) & !"colony" %in% names(ps)) ps[, colony := col45]
if (!"colony" %in% names(ps)) ps[, colony := 0]
ps[, colony := as.numeric(colony)]
ps[, pci_std := as.numeric(pci_std)]
ps[, pf_cbr := as.numeric(pf_cbr)]

ps_est <- ps[!is.na(pci_std) & !is.na(ln_dist)]
cat(sprintf("Estimation sample: %s rows\n", format(nrow(ps_est), big.mark=",")))

# ---- Spec 1: Baseline Gravity ----
cat("\n=== Spec 1: Baseline Gravity ===\n")
m1 <- fepois(trade_value ~ ln_dist + contig + comlang_off + colony |
               exporter_year + importer_year + hs4,
             data = ps_est, cluster = ~pair)
cat(sprintf("  ln_dist:     %.4f (SE %.4f)\n", coef(m1)["ln_dist"], se(m1)["ln_dist"]))
cat(sprintf("  contig:      %.4f (SE %.4f)\n", coef(m1)["contig"], se(m1)["contig"]))
cat(sprintf("  comlang_off: %.4f (SE %.4f)\n", coef(m1)["comlang_off"], se(m1)["comlang_off"]))
cat(sprintf("  colony:      %.4f (SE %.4f)\n", coef(m1)["colony"], se(m1)["colony"]))
cat(sprintf("  N: %s\n", format(nobs(m1), big.mark=",")))

# ---- Spec 2a: PF cross-sectional ----
ps_pf <- ps_est[!is.na(pf_cbr)]
cat(sprintf("\nObs with PF: %s (%d pairs)\n",
            format(nrow(ps_pf), big.mark=","), uniqueN(ps_pf$pair)))

if (nrow(ps_pf) > 1000) {
  cat("\n=== Spec 2a: PF cross-sectional ===\n")
  m2a <- fepois(trade_value ~ pf_cbr + ln_dist + contig + comlang_off + colony |
                  exporter_year + importer_year + hs4,
                data = ps_pf, cluster = ~pair)
  cat(sprintf("  pf_cbr:  %.4f (SE %.4f, p=%.4f)\n",
              coef(m2a)["pf_cbr"], se(m2a)["pf_cbr"], pvalue(m2a)["pf_cbr"]))

  # ---- Spec 2b: PF within-pair ----
  cat("\n=== Spec 2b: PF within-pair ===\n")
  m2b <- fepois(trade_value ~ pf_cbr |
                  exporter_year + importer_year + pair + hs4,
                data = ps_pf, cluster = ~pair)
  cat(sprintf("  pf_cbr:  %.4f (SE %.4f, p=%.4f)\n",
              coef(m2b)["pf_cbr"], se(m2b)["pf_cbr"], pvalue(m2b)["pf_cbr"]))

  # ---- Spec 3: KEY — PF x PCI interaction ----
  cat("\n=== Spec 3: PF x PCI (KEY SPECIFICATION) ===\n")
  m3 <- fepois(trade_value ~ pf_cbr + pf_cbr:pci_std |
                 exporter_year + importer_year + pair + hs4,
               data = ps_pf, cluster = ~pair)
  cat(sprintf("  pf_cbr:         %.4f (SE %.4f, p=%.4f)\n",
              coef(m3)["pf_cbr"], se(m3)["pf_cbr"], pvalue(m3)["pf_cbr"]))
  cat(sprintf("  pf_cbr:pci_std: %.4f (SE %.4f, p=%.4f)\n",
              coef(m3)["pf_cbr:pci_std"], se(m3)["pf_cbr:pci_std"], pvalue(m3)["pf_cbr:pci_std"]))
  cat(sprintf("  N: %s\n", format(nobs(m3), big.mark=",")))

  cat("\n=== VERDICT ===\n")
  alpha2 <- coef(m3)["pf_cbr:pci_std"]
  pval <- pvalue(m3)["pf_cbr:pci_std"]
  cat(sprintf("  alpha_2 = %.6f (p = %.4f)\n", alpha2, pval))
  if (alpha2 < 0 & pval < 0.05) {
    cat("  RESULT: Negative and significant at 5%% -- THEORY CONFIRMED\n")
  } else if (alpha2 < 0) {
    cat("  RESULT: Negative but not significant -- directionally consistent\n")
  } else {
    cat("  RESULT: Not negative -- investigate\n")
  }
}

cat("\nEstimation complete.\n")
