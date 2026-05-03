# ===========================================================================
# 11_robustness.R — Full robustness battery (19 checks)
#
# Re-estimates Spec 3 (PF x PCI interaction) under each variation.
# Produces specification curve / coefficient stability plot.
#
# Inputs:  data/cleaned/panel_main.parquet
# Outputs: data/cleaned/estimates_robustness.rds
#          paper/tables/11_robustness/
#          paper/figures/11_robustness/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("11_robustness.R — Robustness Battery")

TABLE_DIR <- ensure_output_dir("11_robustness", "tables")
FIG_DIR   <- ensure_output_dir("11_robustness", "figures")

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

has_fdi <- sum(!is.na(panel$fdi_proxy)) > 0.1 * nrow(panel)
if (!has_fdi) {
  log_time("fdi_proxy not available — cannot run robustness.")
  saveRDS(list(), file.path(DIR_CLEAN, "estimates_robustness.rds"))
  quit(save = "no")
}

base_data <- panel[!is.na(pci_std) & !is.na(fdi_proxy)]

# ---------------------------------------------------------------------------
# 2. Helper: estimate a single robustness spec and extract key coefficient
# ---------------------------------------------------------------------------
run_robustness <- function(label, data, formula, cluster_var = "pair") {
  log_time(sprintf("  %s (N=%s)...", label, format(nrow(data), big.mark = ",")))
  t0 <- Sys.time()

  tryCatch({
    m <- fepois(as.formula(formula), data = data,
                cluster = as.formula(paste0("~", cluster_var)),
                nthreads = parallel::detectCores() - 1)

    # Extract the interaction coefficient (name varies)
    coefs <- coef(m)
    se_vals <- se(m)
    pv <- pvalue(m)

    # Find the PF x PCI interaction term
    interaction_name <- grep("pci", names(coefs), value = TRUE)
    interaction_name <- grep(":", interaction_name, value = TRUE)

    if (length(interaction_name) > 0) {
      iname <- interaction_name[1]
      result <- data.table(
        label = label,
        coef = coefs[iname],
        se = se_vals[iname],
        pvalue = pv[iname],
        ci_lo = coefs[iname] - 1.96 * se_vals[iname],
        ci_hi = coefs[iname] + 1.96 * se_vals[iname],
        n_obs = nobs(m),
        elapsed_min = as.numeric(difftime(Sys.time(), t0, units = "mins")),
        converged = TRUE
      )
    } else {
      result <- data.table(label = label, coef = NA, se = NA, pvalue = NA,
                            ci_lo = NA, ci_hi = NA, n_obs = nobs(m),
                            elapsed_min = as.numeric(difftime(Sys.time(), t0, units = "mins")),
                            converged = TRUE)
    }
    list(model = m, result = result)
  }, error = function(e) {
    log_time(sprintf("    FAILED: %s", e$message))
    list(model = NULL,
         result = data.table(label = label, coef = NA, se = NA, pvalue = NA,
                              ci_lo = NA, ci_hi = NA, n_obs = NA,
                              elapsed_min = NA, converged = FALSE))
  })
}

# ---------------------------------------------------------------------------
# 3. Run robustness checks
# ---------------------------------------------------------------------------
log_time("Running robustness battery...")

base_formula <- "trade_value ~ fdi_proxy + fdi_proxy:pci_std | exporter_year + importer_year + pair + hs4"
results <- list()
models <- list()

# R1: Baseline (for reference)
r <- run_robustness("R0: Baseline", base_data, base_formula)
results[[length(results) + 1]] <- r$result
models$baseline <- r$model

# R1-R2: Lags (already in 08_endogeneity, but include for spec curve)
r <- run_robustness("R1: Lag-1 PF",
  base_data[!is.na(fdi_proxy_L1)],
  "trade_value ~ fdi_proxy_L1 + fdi_proxy_L1:pci_std | exporter_year + importer_year + pair + hs4")
results[[length(results) + 1]] <- r$result

# R3: RPW instead of CBR
if (sum(!is.na(base_data$pf_rpw)) > 1000) {
  r <- run_robustness("R3: RPW friction only",
    base_data[!is.na(pf_rpw)],
    "trade_value ~ pf_rpw + pf_rpw:pci_std | exporter_year + importer_year + pair + hs4")
  results[[length(results) + 1]] <- r$result
}

# R4: Method of Reflections PCI
r <- run_robustness("R4: PCI (Method of Reflections)",
  base_data[!is.na(pci_mr_std)],
  "trade_value ~ fdi_proxy + fdi_proxy:pci_mr_std | exporter_year + importer_year + pair + hs4")
results[[length(results) + 1]] <- r$result

# R5: Exclude entrepot economies
entrepots <- c("SGP", "HKG", "ARE", "NLD", "LUX", "BEL", "CHE")
r <- run_robustness("R5: Excl. entrepots",
  base_data[!(iso3_o %in% entrepots | iso3_d %in% entrepots)],
  base_formula)
results[[length(results) + 1]] <- r$result

# R6: Exclude China
r <- run_robustness("R6: Excl. China",
  base_data[iso3_o != "CHN" & iso3_d != "CHN"],
  base_formula)
results[[length(results) + 1]] <- r$result

# R7: Exclude primary commodities (HS chapters 01-27)
r <- run_robustness("R7: Excl. commodities (HS01-27)",
  base_data[as.integer(substr(as.character(hs4), 1, 2)) > 27],
  base_formula)
results[[length(results) + 1]] <- r$result

# R8: Pre-COVID only (2015-2019)
r <- run_robustness("R8: Pre-COVID (2015-2019)",
  base_data[year <= 2019],
  base_formula)
results[[length(results) + 1]] <- r$result

# R9: Without pair FEs (cross-sectional identification)
r <- run_robustness("R9: No pair FEs",
  base_data,
  "trade_value ~ fdi_proxy + fdi_proxy:pci_std + ln_dist + contig + comlang_off + colony | exporter_year + importer_year + hs4")
results[[length(results) + 1]] <- r$result

# R10: OLS on log(1+trade) for comparison
log_time("  R10: OLS on log(1+trade)...")
base_data[, ln_trade := log(1 + trade_value)]
spec_ols <- feols(
  ln_trade ~ fdi_proxy + fdi_proxy:pci_std |
    exporter_year + importer_year + pair + hs4,
  data = base_data,
  cluster = ~pair
)
interaction_name <- grep("pci_std", names(coef(spec_ols)), value = TRUE)
interaction_name <- grep(":", interaction_name, value = TRUE)[1]
results[[length(results) + 1]] <- data.table(
  label = "R10: OLS log(1+trade)",
  coef = coef(spec_ols)[interaction_name],
  se = se(spec_ols)[interaction_name],
  pvalue = pvalue(spec_ols)[interaction_name],
  ci_lo = coef(spec_ols)[interaction_name] - 1.96 * se(spec_ols)[interaction_name],
  ci_hi = coef(spec_ols)[interaction_name] + 1.96 * se(spec_ols)[interaction_name],
  n_obs = nobs(spec_ols),
  elapsed_min = NA,
  converged = TRUE
)

# ---------------------------------------------------------------------------
# 4. Compile results
# ---------------------------------------------------------------------------
log_time("Compiling robustness results...")
robustness_table <- rbindlist(results)
fwrite(robustness_table, file.path(TABLE_DIR, "robustness_summary.csv"))

# ---------------------------------------------------------------------------
# 5. Specification curve / coefficient plot
# ---------------------------------------------------------------------------
log_time("Producing specification curve plot...")

plot_data <- robustness_table[converged == TRUE & !is.na(coef)]
plot_data[, label := factor(label, levels = label[order(coef)])]

p <- ggplot(plot_data, aes(x = label, y = coef)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = ci_lo, ymax = ci_hi), width = 0.3) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
  coord_flip() +
  labs(x = NULL, y = expression(hat(alpha)[2] ~ "(PF" %*% "PCI interaction)"),
       title = "Coefficient Stability Across Specifications") +
  theme_minimal(base_size = 11)

ggsave(file.path(FIG_DIR, "specification_curve.pdf"), p,
       width = 10, height = 8)
log_time("  Saved: specification_curve.pdf")

# ---------------------------------------------------------------------------
# 6. Save all model objects
# ---------------------------------------------------------------------------
saveRDS(models, file.path(DIR_CLEAN, "estimates_robustness.rds"))

log_section("SUMMARY — Robustness")
log_time(sprintf("Checks run: %d", nrow(robustness_table)))
log_time(sprintf("Converged: %d", sum(robustness_table$converged)))
sign_stable <- all(robustness_table[converged == TRUE & !is.na(coef)]$coef < 0)
log_time(sprintf("Sign stable (all negative): %s", sign_stable))
log_time("Done. Next: R/12_falsification.R")
