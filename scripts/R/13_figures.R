# ===========================================================================
# 13_figures.R — Static publication figures (PDF/PNG)
#
# Inputs:  All cleaned data + estimates
# Outputs: paper/figures/13_figures/
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))
suppressPackageStartupMessages({
  library(sf)
  library(rnaturalearth)
  library(rnaturalearthdata)
})

log_section("13_figures.R — Publication Figures")

FIG_DIR <- ensure_output_dir("13_figures", "figures")

# ---------------------------------------------------------------------------
# 1. World Heatmap of SOS
# ---------------------------------------------------------------------------
log_time("Figure 1: World heatmap of country-level SOS...")

sos <- read_clean("sos_country.parquet")
world <- ne_countries(scale = "medium", returnclass = "sf")
world <- merge(world, sos[, .(iso3 = iso3, sos_total, rank_total)],
               by.x = "iso_a3", by.y = "iso3", all.x = TRUE)

p1 <- ggplot(world) +
  geom_sf(aes(fill = sos_total), color = "grey80", size = 0.1) +
  scale_fill_viridis_c(option = "plasma", na.value = "grey90",
                        name = "SOS", direction = -1) +
  theme_void(base_family = "serif", base_size = 12) +
  theme(legend.position = "bottom",
        legend.key.width = unit(2, "cm"),
        plot.title = element_blank())

ggsave(file.path(FIG_DIR, "world_heatmap_sos.pdf"), p1,
       width = 12, height = 7)
ggsave(file.path(FIG_DIR, "world_heatmap_sos.png"), p1,
       width = 12, height = 7, dpi = 300)
log_time("  Saved: world_heatmap_sos.pdf/png")

# ---------------------------------------------------------------------------
# 2. SOS vs GDP per capita scatter
# ---------------------------------------------------------------------------
log_time("Figure 2: SOS vs GDP per capita...")

unilateral <- read_clean("gravity_unilateral.parquet")
gdp_cols <- intersect(c("iso3", "year", "gdpcap", "ln_gdpcap"), names(unilateral))

if ("gdpcap" %in% names(unilateral)) {
  gdp <- unilateral[year == max(year), .(iso3, ln_gdpcap = log(gdpcap))][, .SD[1], by = iso3]
} else if ("ln_gdpcap" %in% names(unilateral)) {
  gdp <- unilateral[year == max(year), .(iso3, ln_gdpcap)][, .SD[1], by = iso3]
} else {
  gdp <- data.table(iso3 = character(), ln_gdpcap = numeric())
}

sos_gdp <- merge(sos, gdp, by = "iso3", all.x = TRUE)

if (sum(!is.na(sos_gdp$ln_gdpcap)) > 10) {
  p2 <- ggplot(sos_gdp[!is.na(ln_gdpcap)],
               aes(x = exp(ln_gdpcap), y = sos_total)) +
    geom_point(alpha = 0.5, color = "steelblue") +
    geom_text(data = sos_gdp[rank_total <= 10 & !is.na(ln_gdpcap)],
              aes(label = iso3),
              nudge_y = max(sos_gdp$sos_total, na.rm = TRUE) * 0.03,
              size = 3) +
    scale_x_log10(labels = scales::comma) +
    labs(x = "GDP per Capita (USD, log scale)",
         y = "Stablecoin Opportunity Score") +
    theme_minimal(base_family = "serif", base_size = 12)

  ggsave(file.path(FIG_DIR, "sos_vs_gdppc.pdf"), p2, width = 8, height = 6)
  log_time("  Saved: sos_vs_gdppc.pdf")
} else {
  log_time("  Skipped: insufficient GDP data")
}

# ---------------------------------------------------------------------------
# 3. Coefficient plot: De-risking specifications
# ---------------------------------------------------------------------------
log_time("Figure 3: Coefficient plot (de-risking × PCI)...")

est_path <- file.path(DIR_CLEAN, "estimates_reframed.rds")
if (!file.exists(est_path)) est_path <- file.path(DIR_CLEAN, "estimates_main.rds")

if (file.exists(est_path)) {
  est <- readRDS(est_path)

  # Collect de-risking interaction coefficients across specs
  spec_names <- c("b2_derisked_pci", "b3_derisked_pci_pairfe",
                   "b4_derisked_pci_pfctrl",
                   "b5_derisked_strict", "b5_derisked_loose")
  spec_labels <- c("B2: Cross-sectional",
                    "B3: + Pair FE",
                    "B4: + PF level control",
                    "B5: Strict (25% drop)",
                    "B5: Loose (75% drop)")

  coef_data <- rbindlist(lapply(seq_along(spec_names), function(i) {
    m <- est[[spec_names[i]]]
    if (is.null(m)) return(NULL)
    # Find the derisked:pci interaction term
    cnames <- names(coef(m))
    pci_term <- grep("pci_std", cnames, value = TRUE)
    if (length(pci_term) == 0) return(NULL)
    pci_term <- pci_term[1]
    data.table(
      spec = spec_labels[i],
      estimate = coef(m)[pci_term],
      se = se(m)[pci_term],
      ci_lo = coef(m)[pci_term] - 1.96 * se(m)[pci_term],
      ci_hi = coef(m)[pci_term] + 1.96 * se(m)[pci_term]
    )
  }))

  if (nrow(coef_data) > 0) {
    coef_data[, spec := factor(spec, levels = rev(spec_labels))]

    p3 <- ggplot(coef_data, aes(x = estimate, y = spec)) +
      geom_vline(xintercept = 0, linetype = "dashed", color = "grey60") +
      geom_point(size = 3, color = "darkred") +
      geom_errorbarh(aes(xmin = ci_lo, xmax = ci_hi),
                     height = 0.2, color = "darkred") +
      labs(x = "Coefficient on De-risked × PCI (95% CI)",
           y = NULL) +
      theme_minimal(base_family = "serif", base_size = 12) +
      theme(axis.text.y = element_text(hjust = 0))

    ggsave(file.path(FIG_DIR, "derisking_coefficient_plot.pdf"), p3,
           width = 8, height = 4)
    log_time("  Saved: derisking_coefficient_plot.pdf")
  }

  # Also plot PF level effect across specs.
  # Coefficient name was renamed pf_cbr -> fdi_proxy in 06_estimation_main.R;
  # we look up the new name and fall back to legacy in case of older estimates.
  pf_specs <- c("a2_pf_level" = "A2: PF Level (cross-sect)",
                "a2_pf" = "A2: PF Level (cross-sect)")
  pf_data <- rbindlist(lapply(names(pf_specs), function(nm) {
    m <- est[[nm]]
    if (is.null(m)) return(NULL)
    cf <- coef(m); s <- se(m)
    coef_name <- if ("fdi_proxy" %in% names(cf)) "fdi_proxy" else if ("pf_cbr" %in% names(cf)) "pf_cbr" else NULL
    if (is.null(coef_name)) return(NULL)
    data.table(
      spec = pf_specs[nm],
      estimate = cf[coef_name],
      se = s[coef_name],
      ci_lo = cf[coef_name] - 1.96 * s[coef_name],
      ci_hi = cf[coef_name] + 1.96 * s[coef_name]
    )
  }))
  # Handled inline, no separate plot needed for this
}

# ---------------------------------------------------------------------------
# 4. PCI distribution
# ---------------------------------------------------------------------------
log_time("Figure 4: PCI distribution with product examples...")

pci <- read_clean("complexity_pci.parquet")

p4 <- ggplot(pci, aes(x = pci_std)) +
  geom_histogram(bins = 50, fill = "steelblue", alpha = 0.8, color = "white") +
  geom_vline(xintercept = 0, linetype = "dashed") +
  annotate("text", x = min(pci$pci_std, na.rm = TRUE) + 0.3, y = Inf,
           label = "Simple\n(commodities)", vjust = 2, size = 3,
           color = "darkred", family = "serif") +
  annotate("text", x = max(pci$pci_std, na.rm = TRUE) - 0.3, y = Inf,
           label = "Complex\n(machinery)", vjust = 2, size = 3,
           color = "darkblue", family = "serif") +
  labs(x = "Product Complexity Index (standardized)",
       y = "Number of Products") +
  theme_minimal(base_family = "serif", base_size = 12)

ggsave(file.path(FIG_DIR, "pci_distribution.pdf"), p4,
       width = 8, height = 5)
log_time("  Saved: pci_distribution.pdf")

# ---------------------------------------------------------------------------
# 5. De-risking exposure map
# ---------------------------------------------------------------------------
log_time("Figure 5: De-risking exposure by country...")

if ("n_derisked" %in% names(sos)) {
  world_dr <- merge(world, sos[, .(iso3 = iso3, n_derisked)],
                    by.x = "iso_a3", by.y = "iso3", all.x = TRUE)

  p5 <- ggplot(world_dr) +
    geom_sf(aes(fill = n_derisked), color = "grey80", size = 0.1) +
    scale_fill_viridis_c(option = "inferno", na.value = "grey90",
                          name = "De-risked\nPartners", direction = -1) +
    theme_void(base_family = "serif", base_size = 12) +
    theme(legend.position = "bottom",
          legend.key.width = unit(2, "cm"))

  ggsave(file.path(FIG_DIR, "world_derisking_exposure.pdf"), p5,
         width = 12, height = 7)
  log_time("  Saved: world_derisking_exposure.pdf")
}

# ---------------------------------------------------------------------------
# 6. SOS decomposition: intensive vs extensive
# ---------------------------------------------------------------------------
log_time("Figure 6: SOS decomposition (top 20 countries)...")

top20 <- sos[rank_total <= 20]
if (nrow(top20) > 0 && "sos_intensive_total" %in% names(top20)) {
  top20_long <- melt(top20,
    id.vars = "iso3",
    measure.vars = c("sos_intensive_total", "sos_extensive_total"),
    variable.name = "margin",
    value.name = "sos"
  )
  top20_long[, margin := fifelse(margin == "sos_intensive_total",
                                  "Intensive", "Extensive")]
  # Order by total SOS
  top20_long[, iso3 := factor(iso3, levels = top20[order(sos_total)]$iso3)]

  p6 <- ggplot(top20_long, aes(x = iso3, y = sos, fill = margin)) +
    geom_col(position = "stack") +
    coord_flip() +
    scale_fill_manual(values = c("Intensive" = "steelblue",
                                  "Extensive" = "coral")) +
    labs(x = NULL, y = "Stablecoin Opportunity Score",
         fill = "Margin") +
    theme_minimal(base_family = "serif", base_size = 12) +
    theme(legend.position = "bottom")

  ggsave(file.path(FIG_DIR, "sos_decomposition_top20.pdf"), p6,
         width = 8, height = 7)
  log_time("  Saved: sos_decomposition_top20.pdf")
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Figures")
log_time("Files produced:")
for (f in list.files(FIG_DIR)) {
  log_time(paste("  ", f))
}
log_time("Done.")
