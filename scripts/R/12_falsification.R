# ===========================================================================
# 12_falsification.R — 7 falsification tests
#
# Tests what SHOULD NOT show effects to validate the mechanism.
#
# Inputs:  data/cleaned/panel_main.parquet
# Outputs: data/cleaned/estimates_falsification.rds
#          paper/tables/12_falsification/
#          paper/figures/12_falsification/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("12_falsification.R — Falsification Tests")

TABLE_DIR <- ensure_output_dir("12_falsification", "tables")
FIG_DIR   <- ensure_output_dir("12_falsification", "figures")

# ---------------------------------------------------------------------------
# 1. Load panel
# ---------------------------------------------------------------------------
log_time("Loading panel...")
panel <- read_clean("panel_main.parquet")
# Rename legacy pf_cbr* columns to fdi_proxy* (FDI-derived; see 03_data.tex).
panel <- rename_pf_to_fdi(panel)
panel[, exporter_year := as.factor(exporter_year)]
panel[, importer_year := as.factor(importer_year)]
panel[, pair := as.factor(pair)]
panel[, hs4 := as.factor(hs4)]

base_data <- panel[!is.na(pci_std) & !is.na(fdi_proxy)]

results <- list()

# ---------------------------------------------------------------------------
# 2. Test 1: PF x Product Weight (should be NULL)
# ---------------------------------------------------------------------------
# Product weight proxy: average kg per dollar of trade (lower = lighter/higher value)
log_time("Test 1: PF x Product Weight...")
baci <- read_clean("baci_hs4.parquet")
product_weight <- baci[trade_value > 0 & !is.na(trade_quantity) & trade_quantity > 0,
                        .(weight_per_dollar = median(trade_quantity / trade_value, na.rm = TRUE)),
                        by = hs4]
product_weight[, weight_std := standardize(log(weight_per_dollar + 0.001))]

base_data <- merge(base_data, product_weight[, .(hs4, weight_std)],
                    by = "hs4", all.x = TRUE)

if (sum(!is.na(base_data$weight_std)) > 1000) {
  test1 <- fepois(
    trade_value ~ fdi_proxy + fdi_proxy:weight_std |
      exporter_year + importer_year + pair + hs4,
    data = base_data[!is.na(weight_std)],
    cluster = ~pair,
    nthreads = parallel::detectCores() - 1
  )
  interaction_name <- grep("weight", names(coef(test1)), value = TRUE)
  interaction_name <- grep(":", interaction_name, value = TRUE)[1]
  results[["T1: PF x Weight"]] <- data.table(
    test = "T1: PF x Weight",
    expected = "Null",
    coef = coef(test1)[interaction_name],
    se = se(test1)[interaction_name],
    pvalue = pvalue(test1)[interaction_name],
    verdict = ifelse(pvalue(test1)[interaction_name] > 0.1, "PASS", "CONCERN")
  )
  log_time(sprintf("  Coef: %.4f, p=%.3f -> %s",
                   coef(test1)[interaction_name],
                   pvalue(test1)[interaction_name],
                   results[["T1: PF x Weight"]]$verdict))
}

# ---------------------------------------------------------------------------
# 3. Test 2: PF x Perishability (should be NULL)
# ---------------------------------------------------------------------------
log_time("Test 2: PF x Perishability...")
base_data[, perishable := as.integer(as.integer(substr(as.character(hs4), 1, 2)) <= 8)]

test2 <- fepois(
  trade_value ~ fdi_proxy + fdi_proxy:perishable |
    exporter_year + importer_year + pair + hs4,
  data = base_data,
  cluster = ~pair,
  nthreads = parallel::detectCores() - 1
)
interaction_name <- grep("perishable", names(coef(test2)), value = TRUE)
interaction_name <- grep(":", interaction_name, value = TRUE)[1]
results[["T2: PF x Perishable"]] <- data.table(
  test = "T2: PF x Perishable",
  expected = "Null",
  coef = coef(test2)[interaction_name],
  se = se(test2)[interaction_name],
  pvalue = pvalue(test2)[interaction_name],
  verdict = ifelse(pvalue(test2)[interaction_name] > 0.1, "PASS", "CONCERN")
)
log_time(sprintf("  Coef: %.4f, p=%.3f -> %s",
                 coef(test2)[interaction_name],
                 pvalue(test2)[interaction_name],
                 results[["T2: PF x Perishable"]]$verdict))

# ---------------------------------------------------------------------------
# 4. Test 3: Distance x PCI (should be WEAK)
# ---------------------------------------------------------------------------
log_time("Test 3: Distance x PCI (placebo friction)...")
base_data[, ln_dist_x_pci := ln_dist * pci_std]

test3 <- fepois(
  trade_value ~ fdi_proxy + fdi_proxy:pci_std + ln_dist:pci_std |
    exporter_year + importer_year + hs4,
  data = base_data[!is.na(ln_dist)],
  cluster = ~pair,
  nthreads = parallel::detectCores() - 1
)
results[["T3: Dist x PCI"]] <- data.table(
  test = "T3: Distance x PCI",
  expected = "Weaker than PF x PCI",
  coef = coef(test3)["ln_dist:pci_std"],
  se = se(test3)["ln_dist:pci_std"],
  pvalue = pvalue(test3)["ln_dist:pci_std"],
  verdict = "CHECK"
)

# ---------------------------------------------------------------------------
# 5. Test 4: Common Language x PCI (should be NULL)
# ---------------------------------------------------------------------------
log_time("Test 4: Common Language x PCI...")
if ("comlang_off" %in% names(base_data)) {
  test4 <- fepois(
    trade_value ~ fdi_proxy + fdi_proxy:pci_std + comlang_off:pci_std |
      exporter_year + importer_year + hs4,
    data = base_data[!is.na(comlang_off)],
    cluster = ~pair,
    nthreads = parallel::detectCores() - 1
  )
  results[["T4: Lang x PCI"]] <- data.table(
    test = "T4: Language x PCI",
    expected = "Null",
    coef = coef(test4)["comlang_off:pci_std"],
    se = se(test4)["comlang_off:pci_std"],
    pvalue = pvalue(test4)["comlang_off:pci_std"],
    verdict = ifelse(pvalue(test4)["comlang_off:pci_std"] > 0.1, "PASS", "CONCERN")
  )
}

# ---------------------------------------------------------------------------
# 6. Test 7: Commodity-only subsample (should be WEAK/NULL)
# ---------------------------------------------------------------------------
log_time("Test 7: Commodity-only subsample (HS 01-27)...")
commodity_data <- base_data[as.integer(substr(as.character(hs4), 1, 2)) <= 27]

if (nrow(commodity_data) > 10000) {
  test7 <- fepois(
    trade_value ~ fdi_proxy + fdi_proxy:pci_std |
      exporter_year + importer_year + pair + hs4,
    data = commodity_data,
    cluster = ~pair,
    nthreads = parallel::detectCores() - 1
  )
  interaction_name <- grep("pci", names(coef(test7)), value = TRUE)
  interaction_name <- grep(":", interaction_name, value = TRUE)[1]
  results[["T7: Commodities"]] <- data.table(
    test = "T7: Commodities Only",
    expected = "Null or weak",
    coef = coef(test7)[interaction_name],
    se = se(test7)[interaction_name],
    pvalue = pvalue(test7)[interaction_name],
    verdict = ifelse(abs(coef(test7)[interaction_name]) <
                      abs(coef(results[["T1: PF x Weight"]]$coef %||% 0.1)),
                    "PASS", "CHECK")
  )
}

# ---------------------------------------------------------------------------
# 7. Compile and save
# ---------------------------------------------------------------------------
log_time("Compiling falsification results...")
falsification_table <- rbindlist(results, fill = TRUE)
fwrite(falsification_table, file.path(TABLE_DIR, "falsification_results.csv"))

saveRDS(list(test1 = if (exists("test1")) test1 else NULL,
             test2 = test2,
             test3 = test3,
             test4 = if (exists("test4")) test4 else NULL,
             test7 = if (exists("test7")) test7 else NULL),
        file.path(DIR_CLEAN, "estimates_falsification.rds"))

# Summary plot
if (nrow(falsification_table) >= 3) {
  p <- ggplot(falsification_table, aes(x = test, y = coef)) +
    geom_point(size = 3) +
    geom_errorbar(aes(ymin = coef - 1.96 * se, ymax = coef + 1.96 * se), width = 0.3) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
    coord_flip() +
    labs(x = NULL, y = "Coefficient on Placebo Interaction",
         title = "Falsification Tests (all should be near zero)") +
    theme_minimal(base_size = 11)

  ggsave(file.path(FIG_DIR, "falsification_panel.pdf"), p, width = 9, height = 6)
}

log_section("SUMMARY — Falsification")
log_time(sprintf("Tests run: %d", nrow(falsification_table)))
log_time(sprintf("Passed: %d", sum(falsification_table$verdict == "PASS")))
log_time("Done.")
