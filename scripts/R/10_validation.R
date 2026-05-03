# ===========================================================================
# 10_validation.R — SOS validation against Chainalysis and Google Trends
#
# Inputs:  data/cleaned/sos_country.parquet
#          data/raw/chainalysis_rankings.csv
#          data/cleaned/gravity_unilateral.parquet (for GDP per capita)
# Outputs: paper/tables/10_validation/
#          paper/figures/10_validation/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("10_validation.R — SOS Validation")

TABLE_DIR <- ensure_output_dir("10_validation", "tables")
FIG_DIR   <- ensure_output_dir("10_validation", "figures")

# ---------------------------------------------------------------------------
# 1. Load SOS and control variables
# ---------------------------------------------------------------------------
log_time("Loading SOS rankings...")
sos <- read_clean("sos_country.parquet")

# Load GDP per capita for income conditioning
unilateral <- read_clean("gravity_unilateral.parquet")
if ("gdpcap" %in% names(unilateral)) {
  gdp_latest <- unilateral[year == max(year), .(iso3, ln_gdpcap = log(gdpcap))][, .SD[1], by = iso3]
} else if ("ln_gdpcap" %in% names(unilateral)) {
  gdp_latest <- unilateral[year == max(year), .(iso3, ln_gdpcap)][, .SD[1], by = iso3]
} else {
  gdp_latest <- data.table(iso3 = character(), ln_gdpcap = numeric())
}
sos <- merge(sos, gdp_latest, by = "iso3", all.x = TRUE)

# ---------------------------------------------------------------------------
# 2. Chainalysis validation
# ---------------------------------------------------------------------------
log_time("Loading Chainalysis rankings...")

chainalysis_path <- file.path(DIR_RAW, "chainalysis_rankings.csv")
if (file.exists(chainalysis_path)) {
  chainalysis <- fread(chainalysis_path)
  # Standardize column names
  setnames(chainalysis, tolower(names(chainalysis)))

  # Try to find ISO3 and rank columns
  iso_col <- grep("iso", names(chainalysis), value = TRUE)
  rank_col <- grep("rank|index|score", names(chainalysis), value = TRUE)

  if (length(iso_col) > 0 && length(rank_col) > 0) {
    chainalysis <- chainalysis[, .(iso3 = get(iso_col[1]),
                                    chainalysis_rank = as.numeric(get(rank_col[1])))]
    sos <- merge(sos, chainalysis, by = "iso3", all.x = TRUE)

    n_matched <- sum(!is.na(sos$chainalysis_rank))
    log_time(sprintf("  Matched: %d countries", n_matched))

    # Unconditional Spearman rank correlation
    rho_unconditional <- cor(sos$rank_total, sos$chainalysis_rank,
                              use = "complete.obs", method = "spearman")
    log_time(sprintf("  Spearman (unconditional): %.3f", rho_unconditional))

    # Income-conditional: residualize both on log GDP per capita
    sos_resid <- sos[!is.na(chainalysis_rank) & !is.na(ln_gdpcap)]
    sos_resid[, sos_resid := residuals(lm(rank_total ~ ln_gdpcap))]
    sos_resid[, chain_resid := residuals(lm(chainalysis_rank ~ ln_gdpcap))]
    rho_conditional <- cor(sos_resid$sos_resid, sos_resid$chain_resid,
                            method = "spearman")
    log_time(sprintf("  Spearman (conditional on GDP/cap): %.3f", rho_conditional))

    # Within income group
    sos_resid[, income_group := cut(ln_gdpcap,
      breaks = quantile(ln_gdpcap, probs = c(0, 0.25, 0.5, 0.75, 1), na.rm = TRUE),
      labels = c("LIC", "LMIC", "UMIC", "HIC"), include.lowest = TRUE)]

    within_group <- sos_resid[, .(
      rho = cor(rank_total, chainalysis_rank, method = "spearman", use = "complete.obs"),
      n = .N
    ), by = income_group]
    fwrite(within_group, file.path(TABLE_DIR, "within_income_group_correlation.csv"))

    # Validation summary table
    val_table <- data.table(
      Test = c("Spearman (unconditional)", "Spearman (conditional on GDP/cap)",
               "N countries matched"),
      Value = c(round(rho_unconditional, 3), round(rho_conditional, 3), n_matched)
    )
    fwrite(val_table, file.path(TABLE_DIR, "validation_summary.csv"))

    # Scatter plot: SOS rank vs Chainalysis rank
    p <- ggplot(sos[!is.na(chainalysis_rank)],
                aes(x = rank_total, y = chainalysis_rank)) +
      geom_point(alpha = 0.6) +
      geom_smooth(method = "lm", se = TRUE, color = "steelblue") +
      geom_text(data = sos[!is.na(chainalysis_rank) & rank_total <= 10],
                aes(label = iso3), nudge_y = 3, size = 3) +
      labs(x = "SOS Rank (1 = highest opportunity)",
           y = "Chainalysis Crypto Adoption Rank") +
      theme_minimal(base_family = "serif", base_size = 12)

    ggsave(file.path(FIG_DIR, "sos_vs_chainalysis.pdf"), p, width = 8, height = 6)

    # Conditional scatter
    p2 <- ggplot(sos_resid, aes(x = sos_resid, y = chain_resid)) +
      geom_point(alpha = 0.6) +
      geom_smooth(method = "lm", se = TRUE, color = "darkred") +
      labs(x = "SOS Rank (residualized on GDP/cap)",
           y = "Chainalysis Rank (residualized on GDP/cap)") +
      theme_minimal(base_family = "serif", base_size = 12)

    ggsave(file.path(FIG_DIR, "sos_vs_chainalysis_conditional.pdf"), p2, width = 8, height = 6)

  } else {
    log_time("  WARNING: Could not identify ISO3/rank columns in Chainalysis data")
  }
} else {
  log_time("  Chainalysis data not found — skipping validation")
  log_time("  Save as: data/raw/chainalysis_rankings.csv")
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Validation")
log_time("Done. Next: R/14_feasibility_quadrant.R")
