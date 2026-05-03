# ===========================================================================
# 05_descriptive.R — Summary statistics and panel diagnostics
#
# Produces descriptive tables and diagnostic figures before estimation.
# Key output: within-pair variation statistics for PF (strategist-critic).
#
# Inputs:  data/cleaned/panel_main.parquet
#          data/cleaned/panel_extensive.parquet
# Outputs: paper/tables/05_descriptive/
#          paper/figures/05_descriptive/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("05_descriptive.R — Summary Statistics & Diagnostics")

TABLE_DIR <- ensure_output_dir("05_descriptive", "tables")
FIG_DIR   <- ensure_output_dir("05_descriptive", "figures")

# ---------------------------------------------------------------------------
# 1. Load panel
# ---------------------------------------------------------------------------
log_time("Loading main panel...")
panel <- read_clean("panel_main.parquet")
# Rename legacy pf_cbr* columns to fdi_proxy* (the variable is FDI-derived,
# not BIS CBR — see paper/sections/03_data.tex footnote and 00_config.R).
panel <- rename_pf_to_fdi(panel)
log_time(sprintf("  %s rows loaded", format(nrow(panel), big.mark = ",")))

# ---------------------------------------------------------------------------
# 2. Summary statistics table
# ---------------------------------------------------------------------------
log_time("Computing summary statistics...")

# Variables for summary
sum_vars <- c("trade_value", "fdi_proxy", "pf_rpw", "pci_std", "eci_o",
              "ln_dist", "kaopen_bilateral")
available_vars <- intersect(sum_vars, names(panel))
# Drop columns that are entirely NA
available_vars <- available_vars[
  sapply(available_vars, function(v) sum(!is.na(panel[[v]])) > 0)
]
log_time(paste("  Variables for summary:", paste(available_vars, collapse = ", ")))

# For positive-trade observations
panel_pos <- panel[trade_value > 0]

sum_table <- rbindlist(lapply(available_vars, function(v) {
  x <- panel_pos[[v]]
  x <- x[!is.na(x)]
  if (length(x) == 0) return(NULL)
  data.table(
    Variable = v,
    N = format(length(x), big.mark = ","),
    Mean = round(mean(x), 3),
    SD = round(sd(x), 3),
    Min = round(min(x), 3),
    P25 = round(quantile(x, 0.25), 3),
    Median = round(median(x), 3),
    P75 = round(quantile(x, 0.75), 3),
    Max = round(max(x), 3)
  )
}))

fwrite(sum_table, file.path(TABLE_DIR, "summary_statistics.csv"))
log_time("  Saved: summary_statistics.csv")

# ---------------------------------------------------------------------------
# 3. Within-pair variation in payment friction (strategist-critic issue)
# ---------------------------------------------------------------------------
log_time("Computing within-pair PF variation...")

if ("fdi_proxy" %in% names(panel) && sum(!is.na(panel$fdi_proxy)) > 0) {
  within_pair_var <- panel[!is.na(fdi_proxy),
                            .(sd_pf = sd(fdi_proxy, na.rm = TRUE),
                              range_pf = max(fdi_proxy, na.rm = TRUE) - min(fdi_proxy, na.rm = TRUE),
                              n_years = uniqueN(year)),
                            by = pair]

  # Summary of within-pair variation
  wp_summary <- data.table(
    Statistic = c("Pairs with any PF variation (sd > 0)",
                  "Mean within-pair SD",
                  "Median within-pair SD",
                  "Pairs with >0.1 SD",
                  "Share with meaningful variation"),
    Value = c(
      sum(within_pair_var$sd_pf > 0, na.rm = TRUE),
      round(mean(within_pair_var$sd_pf, na.rm = TRUE), 4),
      round(median(within_pair_var$sd_pf, na.rm = TRUE), 4),
      sum(within_pair_var$sd_pf > 0.1, na.rm = TRUE),
      round(mean(within_pair_var$sd_pf > 0, na.rm = TRUE), 3)
    )
  )
  fwrite(wp_summary, file.path(TABLE_DIR, "within_pair_pf_variation.csv"))
  log_time("  Saved: within_pair_pf_variation.csv")
  log_time(sprintf("  Pairs with variation: %d / %d (%.1f%%)",
                   sum(within_pair_var$sd_pf > 0, na.rm = TRUE),
                   nrow(within_pair_var),
                   100 * mean(within_pair_var$sd_pf > 0, na.rm = TRUE)))
} else {
  log_time("  fdi_proxy not available — skipping within-pair variation")
}

# ---------------------------------------------------------------------------
# 4. Zero share by PCI quintile
# ---------------------------------------------------------------------------
log_time("Computing zero share by PCI quintile...")

if ("pci_std" %in% names(panel) && sum(!is.na(panel$pci_std)) > 0) {
  panel[!is.na(pci_std), pci_quintile := cut(pci_std,
    breaks = quantile(pci_std, probs = seq(0, 1, 0.2), na.rm = TRUE),
    labels = paste0("Q", 1:5), include.lowest = TRUE)]

  zero_by_pci <- panel[!is.na(pci_quintile),
                        .(zero_share = mean(trade_value == 0, na.rm = TRUE),
                          n_obs = .N,
                          mean_trade = mean(trade_value[trade_value > 0], na.rm = TRUE)),
                        by = pci_quintile][order(pci_quintile)]

  fwrite(zero_by_pci, file.path(TABLE_DIR, "zero_share_by_pci_quintile.csv"))
  log_time("  Saved: zero_share_by_pci_quintile.csv")

  # Plot
  p <- ggplot(zero_by_pci, aes(x = pci_quintile, y = zero_share)) +
    geom_col(fill = "steelblue") +
    labs(x = "PCI Quintile (1=simplest, 5=most complex)",
         y = "Share of Zero Trade Flows",
         title = "Zero Trade Share by Product Complexity") +
    theme_minimal(base_size = 12) +
    scale_y_continuous(labels = scales::percent_format())

  ggsave(file.path(FIG_DIR, "zero_share_by_pci.pdf"), p, width = 7, height = 5)
  log_time("  Saved: zero_share_by_pci.pdf")
}

# ---------------------------------------------------------------------------
# 5. PCI distribution
# ---------------------------------------------------------------------------
log_time("Plotting PCI distribution...")

pci <- read_clean("complexity_pci.parquet")

p_pci <- ggplot(pci, aes(x = pci_std)) +
  geom_histogram(bins = 50, fill = "steelblue", color = "white", alpha = 0.8) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "red") +
  labs(x = "Product Complexity Index (standardized)",
       y = "Count",
       title = "Distribution of PCI (Base Period 2015-2017)") +
  theme_minimal(base_size = 12)

ggsave(file.path(FIG_DIR, "pci_distribution.pdf"), p_pci, width = 7, height = 5)
log_time("  Saved: pci_distribution.pdf")

# ---------------------------------------------------------------------------
# 6. Sample composition
# ---------------------------------------------------------------------------
log_time("Computing sample composition...")

composition <- data.table(
  Dimension = c("Total observations", "Positive trade flows", "Zero trade flows",
                "Exporters", "Importers", "Country pairs",
                "Products (HS4)", "Years",
                "Obs with PCI", "Obs with fdi_proxy", "Obs with gravity"),
  Count = c(
    format(nrow(panel), big.mark = ","),
    format(sum(panel$trade_value > 0, na.rm = TRUE), big.mark = ","),
    format(sum(panel$trade_value == 0, na.rm = TRUE), big.mark = ","),
    uniqueN(panel$iso3_o),
    uniqueN(panel$iso3_d),
    uniqueN(panel$pair),
    uniqueN(panel$hs4),
    uniqueN(panel$year),
    format(sum(!is.na(panel$pci_std)), big.mark = ","),
    format(sum(!is.na(panel$fdi_proxy)), big.mark = ","),
    format(sum(!is.na(panel$ln_dist)), big.mark = ",")
  )
)

fwrite(composition, file.path(TABLE_DIR, "sample_composition.csv"))
log_time("  Saved: sample_composition.csv")

# ---------------------------------------------------------------------------
# 7. Correlation matrix of key variables
# ---------------------------------------------------------------------------
log_time("Computing correlations...")

cor_vars <- intersect(c("trade_value", "fdi_proxy", "pf_rpw", "pci_std",
                         "eci_o", "ln_dist", "kaopen_bilateral"),
                       names(panel))

if (length(cor_vars) >= 3) {
  cor_mat <- cor(panel[, ..cor_vars], use = "pairwise.complete.obs")
  cor_dt <- as.data.table(round(cor_mat, 3), keep.rownames = "Variable")
  fwrite(cor_dt, file.path(TABLE_DIR, "correlation_matrix.csv"))
  log_time("  Saved: correlation_matrix.csv")
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Descriptive Statistics")
log_time(sprintf("Output tables: %s", TABLE_DIR))
log_time(sprintf("Output figures: %s", FIG_DIR))
log_time("Files produced:")
for (f in list.files(c(TABLE_DIR, FIG_DIR))) {
  log_time(paste("  ", f))
}
log_time("Done. Panel is ready for estimation. Next: R/06_estimation_main.R")
