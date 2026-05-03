# ===========================================================================
# 14_feasibility_quadrant.R — Q1-Q4 classification + predictive validity
#
# Classifies countries by on/off ramp availability x capital account openness.
# Tests whether early-period SOS predicts future on/off ramp development.
#
# Inputs:  data/cleaned/sos_country.parquet
#          data/cleaned/pf_kaopen.parquet
#          data/raw/google_trends_stablecoins.parquet
#          data/cleaned/gravity_unilateral.parquet
# Outputs: data/cleaned/feasibility_quadrant.parquet
#          paper/tables/14_feasibility_quadrant/
#          paper/figures/14_feasibility_quadrant/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("14_feasibility_quadrant.R — Feasibility Quadrant")

TABLE_DIR <- ensure_output_dir("14_feasibility_quadrant", "tables")
FIG_DIR   <- ensure_output_dir("14_feasibility_quadrant", "figures")

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
log_time("Loading SOS and classification data...")
sos <- read_clean("sos_country.parquet")
kaopen <- read_clean("pf_kaopen.parquet")

# Latest KAOPEN per country
if (nrow(kaopen) > 0) {
  kaopen_latest <- kaopen[year == max(year), .(iso3, kaopen_norm)][, .SD[1], by = iso3]
} else {
  log_time("  WARNING: KAOPEN data is empty. Using de-risking exposure as proxy.")
  # Use inverse de-risking exposure as capital openness proxy
  # Countries with fewer de-risked partners are more open
  dr_country <- sos[, .(iso3, kaopen_norm = 1 - fifelse(is.na(frac_derisked), 0, frac_derisked))]
  kaopen_latest <- dr_country
}

# GDP per capita for controls
unilateral <- read_clean("gravity_unilateral.parquet")
# Dynamically select available columns
uni_cols <- intersect(c("iso3", "year", "gdpcap", "ln_gdpcap", "internet_pct"), names(unilateral))
if (nrow(unilateral) > 0 && "year" %in% names(unilateral)) {
  gdp <- unilateral[year == max(year), ..uni_cols][, .SD[1], by = iso3]
  if (!"gdpcap" %in% names(gdp) && "ln_gdpcap" %in% names(gdp)) {
    gdp[, gdpcap := exp(ln_gdpcap)]
  }
  if (!"ln_gdpcap" %in% names(gdp) && "gdpcap" %in% names(gdp)) {
    gdp[, ln_gdpcap := log(gdpcap)]
  }
  if (!"internet_pct" %in% names(gdp)) gdp[, internet_pct := NA_real_]
} else {
  gdp <- data.table(iso3 = character(), gdpcap = numeric(),
                     ln_gdpcap = numeric(), internet_pct = numeric())
}

# ---------------------------------------------------------------------------
# 2. On/off ramp measure: Google Trends (primary)
# ---------------------------------------------------------------------------
log_time("Loading Google Trends on/off ramp proxy...")

gtrends_path <- file.path(DIR_RAW, "google_trends_stablecoins.parquet")
if (file.exists(gtrends_path)) {
  gtrends <- as.data.table(arrow::read_parquet(gtrends_path))

  # Aggregate: mean interest across "buy USDT" and "buy USDC" queries
  gtrends_agg <- gtrends[, .(onramp_interest = mean(interest, na.rm = TRUE)),
                          by = .(geo_code)]

  # Map geo codes to ISO3 (Google uses ISO2)
  gtrends_agg[, iso3 := countrycode(geo_code, "iso2c", "iso3c", warn = FALSE)]
  gtrends_agg <- gtrends_agg[!is.na(iso3)]

  # Normalize by internet penetration (from WDI)
  gtrends_agg <- merge(gtrends_agg, gdp[, .(iso3, internet_pct)],
                         by = "iso3", all.x = TRUE)
  gtrends_agg[, onramp_norm := onramp_interest / (internet_pct / 100 + 0.01)]

  log_time(sprintf("  Google Trends: %d countries", nrow(gtrends_agg)))
} else {
  log_time("  Google Trends data not found — using Chainalysis fallback")
  # Try Chainalysis as fallback
  chain_path <- file.path(DIR_RAW, "chainalysis_rankings.csv")
  if (file.exists(chain_path)) {
    chain <- fread(chain_path)
    setnames(chain, tolower(names(chain)))
    iso_col <- grep("iso", names(chain), value = TRUE)[1]
    rank_col <- grep("rank|index|score", names(chain), value = TRUE)[1]
    if (!is.na(iso_col) && !is.na(rank_col)) {
      gtrends_agg <- chain[, .(iso3 = get(iso_col),
                                 onramp_norm = -as.numeric(get(rank_col)))]
      # Invert rank so higher = more on-ramp
    }
  } else {
    gtrends_agg <- data.table(iso3 = character(), onramp_norm = numeric())
  }
}

# ---------------------------------------------------------------------------
# 3. Classify countries into quadrants
# ---------------------------------------------------------------------------
log_time("Classifying countries into feasibility quadrants...")

quad <- merge(sos[, .(iso3, sos_total, rank_total)], kaopen_latest, by = "iso3", all.x = TRUE)
quad <- merge(quad, gtrends_agg[, .(iso3, onramp_norm)], by = "iso3", all.x = TRUE)
quad <- merge(quad, gdp[, .(iso3, gdpcap, ln_gdpcap)], by = "iso3", all.x = TRUE)

# Median splits — only for countries with non-NA values
kaopen_med <- median(quad[!is.na(kaopen_norm)]$kaopen_norm, na.rm = TRUE)
onramp_med <- median(quad[!is.na(onramp_norm) & onramp_norm > 0]$onramp_norm, na.rm = TRUE)
# If too many zeros in onramp, use >0 as threshold instead of median
if (is.na(onramp_med) || onramp_med == 0) onramp_med <- 0

log_time(sprintf("  KAOPEN median: %.3f, On-ramp median: %.3f", kaopen_med, onramp_med))
log_time(sprintf("  Countries with KAOPEN: %d, with on-ramp data: %d",
                 sum(!is.na(quad$kaopen_norm)), sum(!is.na(quad$onramp_norm))))

quad[, capital_open := fifelse(!is.na(kaopen_norm) & kaopen_norm >= kaopen_med,
                                "Open", "Restricted")]
quad[, ramps_exist := fifelse(!is.na(onramp_norm) & onramp_norm > onramp_med,
                               "Yes", "No")]

# Assign quadrant
quad[, quadrant := fcase(
  ramps_exist == "Yes" & capital_open == "Open",       "Q1: Actionable",
  ramps_exist == "No"  & capital_open == "Open",       "Q2: Infrastructure Gap",
  ramps_exist == "Yes" & capital_open == "Restricted",  "Q3: Legal Complexity",
  ramps_exist == "No"  & capital_open == "Restricted",  "Q4: Blocked"
)]

write_clean(quad, "feasibility_quadrant.parquet")

# Summary by quadrant
quad_summary <- quad[!is.na(quadrant), .(
  n_countries = .N,
  mean_sos = round(mean(sos_total, na.rm = TRUE), 2),
  median_sos = round(median(sos_total, na.rm = TRUE), 2),
  mean_gdppc = round(mean(gdpcap, na.rm = TRUE), 0)
), by = quadrant][order(quadrant)]

fwrite(quad_summary, file.path(TABLE_DIR, "quadrant_summary.csv"))
log_time("Quadrant distribution:")
for (i in seq_len(nrow(quad_summary))) {
  log_time(sprintf("  %s: %d countries, mean SOS = %.2f",
                   quad_summary$quadrant[i],
                   quad_summary$n_countries[i],
                   quad_summary$mean_sos[i]))
}

# Top 20 actionable (Q1 only)
top20_q1 <- quad[quadrant == "Q1: Actionable"][order(-sos_total)][1:min(20, .N)]
fwrite(top20_q1[, .(iso3, sos_total, rank_total, kaopen_norm, onramp_norm)],
       file.path(TABLE_DIR, "top20_actionable_q1.csv"))

# SOS by quadrant table
sos_by_quad <- quad[!is.na(quadrant),
                     .(iso3, sos_total, rank_total, quadrant)][order(-sos_total)]
fwrite(sos_by_quad, file.path(TABLE_DIR, "sos_by_quadrant.csv"))

# ---------------------------------------------------------------------------
# 4. Feasibility quadrant scatter plot
# ---------------------------------------------------------------------------
log_time("Producing feasibility quadrant scatter...")

if (sum(!is.na(quad$kaopen_norm) & !is.na(quad$onramp_norm)) > 10) {
  p <- ggplot(quad[!is.na(kaopen_norm) & !is.na(onramp_norm)],
              aes(x = kaopen_norm, y = onramp_norm,
                  size = sos_total, color = quadrant)) +
    geom_point(alpha = 0.6) +
    geom_vline(xintercept = median(quad$kaopen_norm, na.rm = TRUE),
               linetype = "dashed", color = "grey50") +
    geom_hline(yintercept = median(quad$onramp_norm, na.rm = TRUE),
               linetype = "dashed", color = "grey50") +
    geom_text(data = quad[rank_total <= 10],
              aes(label = iso3), size = 3, nudge_y = 2) +
    scale_color_manual(values = c("Q1: Actionable" = "#2ca02c",
                                   "Q2: Infrastructure Gap" = "#ff7f0e",
                                   "Q3: Legal Complexity" = "#d62728",
                                   "Q4: Blocked" = "#7f7f7f")) +
    labs(x = "Capital Account Openness (KAOPEN, normalized)",
         y = "On/Off Ramp Availability (Google Trends, normalized)",
         size = "SOS", color = "Quadrant",
         title = "Feasibility Quadrant: Stablecoin Implementation Readiness") +
    theme_minimal(base_size = 12) +
    theme(legend.position = "right")

  ggsave(file.path(FIG_DIR, "feasibility_quadrant.pdf"), p, width = 10, height = 7)
  ggsave(file.path(FIG_DIR, "feasibility_quadrant.png"), p, width = 10, height = 7, dpi = 300)
  log_time("  Saved: feasibility_quadrant.pdf/png")
}

# ---------------------------------------------------------------------------
# 5. Predictive validity: does early SOS predict future ramp development?
# ---------------------------------------------------------------------------
log_time("Testing predictive validity (early SOS -> future ramps)...")

# This requires computing SOS from base period data only
# For now, use overall SOS as proxy (proper test requires re-estimation)
if (nrow(gtrends_agg) > 20 && sum(!is.na(quad$ln_gdpcap)) > 20) {
  pred_data <- quad[!is.na(onramp_norm) & !is.na(ln_gdpcap) & !is.na(sos_total)]

  pred_model <- lm(onramp_norm ~ sos_total + ln_gdpcap, data = pred_data)

  pred_summary <- data.table(
    Term = names(coef(pred_model)),
    Estimate = round(coef(pred_model), 4),
    SE = round(summary(pred_model)$coefficients[, 2], 4),
    p_value = round(summary(pred_model)$coefficients[, 4], 4)
  )
  fwrite(pred_summary, file.path(TABLE_DIR, "predictive_validity.csv"))
  log_time(sprintf("  SOS -> ramp coefficient: %.4f (p=%.4f)",
                   coef(pred_model)["sos_total"],
                   summary(pred_model)$coefficients["sos_total", 4]))
  log_time(sprintf("  R-squared: %.3f", summary(pred_model)$r.squared))
} else {
  log_time("  Insufficient data for predictive validity test")
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Feasibility Quadrant")
log_time(sprintf("Countries classified: %d", sum(!is.na(quad$quadrant))))
log_time("Done. Pipeline complete.")
