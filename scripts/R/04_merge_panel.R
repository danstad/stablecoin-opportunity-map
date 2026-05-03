# ===========================================================================
# 04_merge_panel.R — Merge all data sources, build analysis-ready panel
#
# Reads the panel skeleton (with zeros, from Python) and merges:
# gravity, complexity (base-period PCI), payment frictions, interactions.
# Builds lags/leads and FE identifiers.
#
# Inputs:  data/cleaned/panel_skeleton.parquet (or baci_hs4.parquet if skeleton too large)
#          data/cleaned/complexity_pci.parquet
#          data/cleaned/complexity_eci.parquet
#          data/cleaned/complexity_density.parquet
#          data/cleaned/complexity_rca.parquet
#          data/cleaned/gravity_bilateral.parquet
#          data/cleaned/gravity_unilateral.parquet
#          data/cleaned/pf_cbr.parquet
#          data/cleaned/pf_rpw.parquet
#          data/cleaned/pf_kaopen.parquet
# Outputs: data/cleaned/panel_main.parquet       (intensive margin panel)
#          data/cleaned/panel_extensive.parquet   (extensive margin: country x product x year)
#          data/cleaned/panel_merge_diagnostics.rds
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("04_merge_panel.R — Panel Assembly")

# ---------------------------------------------------------------------------
# 1. Load panel skeleton
# ---------------------------------------------------------------------------
log_time("Loading panel skeleton...")

skeleton_path <- file.path(DIR_CLEAN, "panel_skeleton.parquet")
if (file.exists(skeleton_path)) {
  # Check file size first
  size_gb <- file.info(skeleton_path)$size / 1e9
  log_time(sprintf("  Panel skeleton: %.1f GB on disk", size_gb))

  if (size_gb > 8) {
    log_time("  WARNING: Panel skeleton is very large. Using arrow for out-of-core processing.")
    panel <- as.data.table(read_parquet(skeleton_path,
                                         col_select = c("year", "iso3_o", "iso3_d",
                                                        "hs4", "trade_value", "pair")))
  } else {
    panel <- read_clean("panel_skeleton.parquet")
  }
} else {
  log_time("  Panel skeleton not found — building from baci_hs4 (positive flows only)")
  log_time("  NOTE: No zeros filled. Run py/01_preprocess_baci.py for full panel.")
  panel <- read_clean("baci_hs4.parquet")
  panel[, pair := paste(iso3_o, iso3_d, sep = "_")]
}

log_time(sprintf("  Panel: %s rows", format(nrow(panel), big.mark = ",")))

# Ensure FE identifiers exist
if (!"exporter_year" %in% names(panel)) {
  panel[, exporter_year := paste(iso3_o, year, sep = "_")]
}
if (!"importer_year" %in% names(panel)) {
  panel[, importer_year := paste(iso3_d, year, sep = "_")]
}

# ---------------------------------------------------------------------------
# 2. Merge PCI (base period, time-invariant)
# ---------------------------------------------------------------------------
log_time("Merging PCI (base period, time-invariant)...")
pci <- read_clean("complexity_pci.parquet")
panel <- merge(panel, pci[, .(hs4, pci_raw, pci_std, pci_mr_std)],
               by = "hs4", all.x = TRUE)
pci_match <- mean(!is.na(panel$pci_std))
log_time(sprintf("  PCI match rate: %.1f%%", 100 * pci_match))

# ---------------------------------------------------------------------------
# 3. Merge ECI (time-varying, country x year)
# ---------------------------------------------------------------------------
log_time("Merging ECI (exporter complexity)...")
eci <- read_clean("complexity_eci.parquet")
panel <- merge(panel, eci[, .(iso3, year, eci_o = eci)],
               by.x = c("iso3_o", "year"), by.y = c("iso3", "year"),
               all.x = TRUE)
eci_match <- mean(!is.na(panel$eci_o))
log_time(sprintf("  ECI match rate: %.1f%%", 100 * eci_match))

# ---------------------------------------------------------------------------
# 4. Merge gravity bilateral variables
# ---------------------------------------------------------------------------
log_time("Merging gravity bilateral variables...")
grav <- read_clean("gravity_bilateral.parquet")
# Select only needed columns to reduce memory
grav_cols <- intersect(
  c("iso3_o", "iso3_d", "year", "ln_dist", "dist", "contig",
    "comlang_off", "colony", "col45", "rta", "fta_wto"),
  names(grav)
)
grav_merge <- grav[, ..grav_cols]
# CEPII V202211 uses col45 instead of colony — rename
if ("col45" %in% names(grav_merge) & !"colony" %in% names(grav_merge)) {
  setnames(grav_merge, "col45", "colony")
  log_time("  Renamed col45 -> colony (CEPII V202211 naming)")
}
# Deduplicate gravity to one row per (iso3_o, iso3_d, year)
grav_merge <- unique(grav_merge, by = c("iso3_o", "iso3_d", "year"))
log_time(sprintf("  Gravity rows after dedup: %s", format(nrow(grav_merge), big.mark = ",")))
panel <- merge(panel, grav_merge,
               by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
grav_match <- mean(!is.na(panel$ln_dist))
log_time(sprintf("  Gravity match rate: %.1f%%", 100 * grav_match))

# ---------------------------------------------------------------------------
# 5. Merge payment frictions — bilateral
# ---------------------------------------------------------------------------
# Primary: try CBR first, fall back to IMF FDI bilateral.
#
# LEGACY NAMING: The on-disk column is named `pf_cbr` for backward compatibility
# with earlier drafts that intended to use BIS CBR data. In practice the BIS file
# was never obtained, and `pf_cbr` here is a transformed CDIS bilateral FDI
# variable. Downstream R/Python code reads this parquet and renames `pf_cbr*`
# columns to `fdi_proxy*` immediately on load. See rename_pf_to_fdi() in
# 00_config.R and the footnote in paper/sections/03_data.tex.
log_time("Merging bilateral payment friction (column written as pf_cbr; renamed to fdi_proxy on read downstream)...")
cbr <- read_clean("pf_cbr.parquet")
if (nrow(cbr) > 0) {
  log_time("  Using BIS/CPMI correspondent banking density (primary)")
  panel <- merge(panel, cbr[, .(iso3_o, iso3_d, year, pf_cbr, n_correspondents)],
                 by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
  cbr_match <- mean(!is.na(panel$pf_cbr))
  log_time(sprintf("  CBR match rate: %.1f%%", 100 * cbr_match))
} else {
  # Fall back to IMF FDI bilateral as proxy
  fdi_path <- file.path(DIR_CLEAN, "imf_fdi_bilateral.parquet")
  if (file.exists(fdi_path)) {
    log_time("  CBR not available — using IMF FDI bilateral as proxy")
    fdi <- as.data.table(arrow::read_parquet(fdi_path))
    panel <- merge(panel, fdi[, .(iso3_o, iso3_d, year, pf_cbr = pf_fdi,
                                   fdi_bilateral)],
                   by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
    cbr_match <- mean(!is.na(panel$pf_cbr))
    log_time(sprintf("  FDI proxy match rate: %.1f%%", 100 * cbr_match))
  } else {
    log_time("  No bilateral friction data available — creating NA columns")
    panel[, c("pf_cbr", "fdi_bilateral") := .(NA_real_, NA_real_)]
  }
}

# ---------------------------------------------------------------------------
# 6. Merge payment frictions — RPW (secondary, bilateral)
# ---------------------------------------------------------------------------
log_time("Merging RPW remittance costs (secondary friction)...")
rpw <- read_clean("pf_rpw.parquet")
if (nrow(rpw) > 0) {
  # RPW may have pf_rpw or pf_rpw_200 depending on preprocessing
  rpw_cost_col <- intersect(c("pf_rpw", "pf_rpw_200"), names(rpw))
  if (length(rpw_cost_col) > 0) {
    rpw_merge <- rpw[, .(iso3_o, iso3_d, year, pf_rpw = get(rpw_cost_col[1]))]
    panel <- merge(panel, rpw_merge,
                   by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
    rpw_match <- mean(!is.na(panel$pf_rpw))
    log_time(sprintf("  RPW match rate: %.1f%% (expected low — ~378 corridors only)",
                     100 * rpw_match))
  } else {
    log_time("  RPW columns not recognized — skipping")
    panel[, pf_rpw := NA_real_]
  }
} else {
  panel[, pf_rpw := NA_real_]
}

# ---------------------------------------------------------------------------
# 7. Merge KAOPEN (country-level, construct bilateral)
# ---------------------------------------------------------------------------
log_time("Merging KAOPEN (bilateral = mean of exporter + importer)...")
kaopen <- read_clean("pf_kaopen.parquet")
if (nrow(kaopen) > 0) {
  panel <- merge(panel, kaopen[, .(iso3, year, kaopen_o = kaopen_norm)],
                 by.x = c("iso3_o", "year"), by.y = c("iso3", "year"),
                 all.x = TRUE)
  panel <- merge(panel, kaopen[, .(iso3, year, kaopen_d = kaopen_norm)],
                 by.x = c("iso3_d", "year"), by.y = c("iso3", "year"),
                 all.x = TRUE)
  panel[, kaopen_bilateral := (kaopen_o + kaopen_d) / 2]
} else {
  panel[, c("kaopen_o", "kaopen_d", "kaopen_bilateral") := .(NA_real_, NA_real_, NA_real_)]
}

# ---------------------------------------------------------------------------
# 8. Construct interaction terms
# ---------------------------------------------------------------------------
log_time("Constructing interaction terms...")
panel[, pf_cbr_x_pci := pf_cbr * pci_std]

# Rajan-Zingales interaction will be added when RZ data is merged
# For now, create placeholder
panel[, pf_cbr_x_pci_mr := pf_cbr * pci_mr_std]

# ---------------------------------------------------------------------------
# 9. Construct lags and leads for endogeneity tests
# ---------------------------------------------------------------------------
log_time("Constructing lags and leads of payment friction...")
setkey(panel, iso3_o, iso3_d, hs4, year)

# Lag-1 and Lag-2 of pf_cbr
panel[, pf_cbr_L1 := shift(pf_cbr, n = 1, type = "lag"), by = .(iso3_o, iso3_d, hs4)]
panel[, pf_cbr_L2 := shift(pf_cbr, n = 2, type = "lag"), by = .(iso3_o, iso3_d, hs4)]

# Lead-1 for pre-trends test
panel[, pf_cbr_F1 := shift(pf_cbr, n = 1, type = "lead"), by = .(iso3_o, iso3_d, hs4)]

# Lagged interactions
panel[, pf_cbr_L1_x_pci := pf_cbr_L1 * pci_std]
panel[, pf_cbr_L2_x_pci := pf_cbr_L2 * pci_std]
panel[, pf_cbr_F1_x_pci := pf_cbr_F1 * pci_std]

# ---------------------------------------------------------------------------
# 10. Build extensive margin panel (country x product x year)
# ---------------------------------------------------------------------------
log_time("Building extensive margin panel...")
rca <- read_clean("complexity_rca.parquet")
density <- read_clean("complexity_density.parquet")

extensive <- merge(rca[, .(iso3, hs4, year, rca, has_rca)],
                   density[, .(iso3, hs4, year, density)],
                   by = c("iso3", "hs4", "year"), all.x = TRUE)

# Add PCI
extensive <- merge(extensive, pci[, .(hs4, pci_std)],
                   by = "hs4", all.x = TRUE)

# Add country-level payment friction (use KAOPEN as country-level proxy)
if (nrow(kaopen) > 0) {
  extensive <- merge(extensive, kaopen[, .(iso3, year, pf_country = kaopen_norm)],
                     by = c("iso3", "year"), all.x = TRUE)
  # Invert so higher = more friction (KAOPEN is openness)
  extensive[, pf_country := 1 - pf_country]
} else {
  extensive[, pf_country := NA_real_]
}

# Interactions for extensive margin
extensive[, density_x_pf := density * pf_country]
extensive[, density_x_pci := density * pci_std]
extensive[, pf_x_pci := pf_country * pci_std]

write_clean(extensive, "panel_extensive.parquet")
log_time(sprintf("  Extensive panel: %s rows", format(nrow(extensive), big.mark = ",")))

# ---------------------------------------------------------------------------
# 11. Save main panel
# ---------------------------------------------------------------------------
log_time("Saving main panel...")
write_clean(panel, "panel_main.parquet")

# ---------------------------------------------------------------------------
# 12. Diagnostics
# ---------------------------------------------------------------------------
log_time("Computing merge diagnostics...")

diagnostics <- list(
  panel_rows = nrow(panel),
  n_exporters = uniqueN(panel$iso3_o),
  n_importers = uniqueN(panel$iso3_d),
  n_pairs = uniqueN(panel$pair),
  n_products = uniqueN(panel$hs4),
  n_years = uniqueN(panel$year),
  zero_share = mean(panel$trade_value == 0, na.rm = TRUE),
  match_rates = list(
    pci = pci_match,
    eci = eci_match,
    gravity = grav_match,
    cbr = if (exists("cbr_match")) cbr_match else NA,
    rpw = if (exists("rpw_match")) rpw_match else NA
  ),
  extensive_rows = nrow(extensive),
  extensive_countries = uniqueN(extensive$iso3),
  extensive_products = uniqueN(extensive$hs4)
)

saveRDS(diagnostics, file.path(DIR_CLEAN, "panel_merge_diagnostics.rds"))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Panel Assembly")
log_time(sprintf("Main panel:     %s rows", format(diagnostics$panel_rows, big.mark = ",")))
log_time(sprintf("  Pairs:        %s", format(diagnostics$n_pairs, big.mark = ",")))
log_time(sprintf("  Products:     %d", diagnostics$n_products))
log_time(sprintf("  Years:        %d", diagnostics$n_years))
log_time(sprintf("  Zero share:   %.1f%%", 100 * diagnostics$zero_share))
log_time(sprintf("Extensive panel: %s rows", format(diagnostics$extensive_rows, big.mark = ",")))
log_time("Match rates:")
for (nm in names(diagnostics$match_rates)) {
  val <- diagnostics$match_rates[[nm]]
  if (!is.na(val)) {
    log_time(sprintf("  %s: %.1f%%", nm, 100 * val))
  }
}
log_time("Done. Next: R/05_descriptive.R")
