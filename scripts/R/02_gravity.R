# ===========================================================================
# 02_gravity.R — Clean CEPII Gravity dataset, extend to 2023 with WDI
#
# Inputs:  data/raw/Gravity_V202301.csv (or similar)
#          data/raw/wdi_indicators.parquet (from py/00_download_data.py)
# Outputs: data/cleaned/gravity_bilateral.parquet  (pair x year)
#          data/cleaned/gravity_unilateral.parquet  (country x year)
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("02_gravity.R — CEPII Gravity + WDI Extension")

# ---------------------------------------------------------------------------
# 1. Load CEPII Gravity
# ---------------------------------------------------------------------------
log_time("Loading CEPII Gravity dataset...")

# Look for Gravity CSV in subdirectory or directly in raw
gravity_dirs <- list.dirs(DIR_RAW, recursive = FALSE)
gravity_dir <- grep("Gravity", gravity_dirs, value = TRUE)
if (length(gravity_dir) > 0) {
  gravity_files <- list.files(gravity_dir[1], pattern = "^Gravity.*\\.csv$",
                               full.names = TRUE)
} else {
  gravity_files <- list.files(DIR_RAW, pattern = "^Gravity.*\\.(csv|rds)$",
                               full.names = TRUE)
}
if (length(gravity_files) == 0) {
  stop("No Gravity file found in data/raw/. ",
       "Download from http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele.asp")
}

grav_path <- gravity_files[1]
log_time(paste("  Using:", basename(grav_path)))

if (grepl("\\.rds$", grav_path)) {
  grav <- as.data.table(readRDS(grav_path))
} else {
  grav <- fread(grav_path, na.strings = c("", "NA", "."))
}
log_time(sprintf("  Raw gravity: %s rows, %d columns",
                 format(nrow(grav), big.mark = ","), ncol(grav)))

# ---------------------------------------------------------------------------
# 2. Select and rename key variables
# ---------------------------------------------------------------------------
log_time("Selecting gravity variables...")

# CEPII Gravity column names (V202301 format)
# Bilateral: iso3_o, iso3_d, year, dist, contig, comlang_off, comlang_ethno,
#            colony, comcol, col45, smctry, rta, fta_wto
# Unilateral: gdp_o, gdp_d, pop_o, pop_d, gdpcap_o, gdpcap_d

# Standardize column names to lowercase
setnames(grav, tolower(names(grav)))

# Select bilateral variables
bilateral_vars <- c("iso3_o", "iso3_d", "year",
                     "dist", "distcap", "contig",
                     "comlang_off", "comlang_ethno",
                     "colony", "comcol", "col45", "smctry",
                     "rta", "fta_wto")

# Keep only variables that exist
available_bilateral <- intersect(bilateral_vars, names(grav))
log_time(paste("  Available bilateral vars:", paste(available_bilateral, collapse = ", ")))

# Select unilateral variables
unilateral_vars <- c("iso3_o", "iso3_d", "year",
                      "gdp_o", "gdp_d", "pop_o", "pop_d",
                      "gdpcap_o", "gdpcap_d")
available_unilateral <- intersect(unilateral_vars, names(grav))

# ---------------------------------------------------------------------------
# 3. Extract time-invariant bilateral characteristics
# ---------------------------------------------------------------------------
log_time("Extracting time-invariant bilateral variables...")

# These don't change over time: dist, contig, comlang, colony, etc.
time_invariant <- c("dist", "distcap", "contig", "comlang_off", "comlang_ethno",
                     "colony", "comcol", "col45", "smctry")
ti_available <- intersect(time_invariant, names(grav))

bilateral_ti <- unique(grav[, c("iso3_o", "iso3_d", ..ti_available)])
# Deduplicate (take first non-NA observation per pair)
bilateral_ti <- bilateral_ti[, lapply(.SD, function(x) x[!is.na(x)][1]),
                              by = .(iso3_o, iso3_d)]
log_time(sprintf("  Time-invariant bilateral: %s pairs",
                 format(nrow(bilateral_ti), big.mark = ",")))

# ---------------------------------------------------------------------------
# 4. Extract time-varying bilateral variables (FTA/RTA)
# ---------------------------------------------------------------------------
log_time("Extracting time-varying bilateral variables (FTA/RTA)...")

tv_vars <- intersect(c("rta", "fta_wto"), names(grav))
if (length(tv_vars) > 0) {
  bilateral_tv <- grav[year %in% SAMPLE_YEARS,
                        c("iso3_o", "iso3_d", "year", ..tv_vars)]

  # Carry forward FTA status for years beyond CEPII coverage
  max_cepii_year <- max(bilateral_tv$year, na.rm = TRUE)
  if (max_cepii_year < max(SAMPLE_YEARS)) {
    log_time(sprintf("  CEPII coverage ends %d, carrying forward FTA to %d",
                     max_cepii_year, max(SAMPLE_YEARS)))
    latest <- bilateral_tv[year == max_cepii_year]
    for (yr in (max_cepii_year + 1):max(SAMPLE_YEARS)) {
      forward <- copy(latest)
      forward[, year := yr]
      bilateral_tv <- rbind(bilateral_tv, forward)
    }
  }
} else {
  log_time("  No FTA/RTA variables found — creating empty placeholder")
  bilateral_tv <- data.table(iso3_o = character(), iso3_d = character(),
                              year = integer())
}

# ---------------------------------------------------------------------------
# 5. Build unilateral panel (GDP, population) with WDI extension
# ---------------------------------------------------------------------------
log_time("Building unilateral panel...")

# Extract from CEPII
unilateral_cepii <- unique(rbind(
  grav[year %in% SAMPLE_YEARS,
       .(iso3 = iso3_o, year, gdp = gdp_o, pop = pop_o, gdpcap = gdpcap_o)],
  grav[year %in% SAMPLE_YEARS,
       .(iso3 = iso3_d, year, gdp = gdp_d, pop = pop_d, gdpcap = gdpcap_d)]
))
unilateral_cepii <- unilateral_cepii[, lapply(.SD, function(x) x[!is.na(x)][1]),
                                       by = .(iso3, year)]

# Load WDI data (from Python download)
wdi_path <- file.path(DIR_RAW, "wdi_indicators.parquet")
if (file.exists(wdi_path)) {
  log_time("  Loading WDI data for extension...")
  wdi <- as.data.table(read_parquet(wdi_path))

  # Fill gaps in CEPII with WDI
  # Select only WDI columns that actually exist (API may have been partially down)
  wdi_available <- intersect(
    c("gdp_current_usd", "population", "gdp_pc_usd",
      "internet_pct", "mobile_subscriptions_per100",
      "atms_per_100k", "bank_branches_per_100k",
      "remittances_received_usd"),
    names(wdi)
  )
  log_time(paste("  WDI columns available:", paste(wdi_available, collapse = ", ")))

  wdi_fill <- wdi[year %in% SAMPLE_YEARS, c("iso3", "year", ..wdi_available)]

  # Rename WDI columns to avoid conflicts with CEPII
  rename_map <- c(
    "gdp_current_usd" = "gdp_wdi",
    "population" = "pop_wdi",
    "gdp_pc_usd" = "gdpcap_wdi"
  )
  for (old_name in names(rename_map)) {
    if (old_name %in% names(wdi_fill)) {
      setnames(wdi_fill, old_name, rename_map[old_name])
    }
  }

  unilateral <- merge(unilateral_cepii, wdi_fill,
                       by = c("iso3", "year"), all = TRUE)

  # Use CEPII where available, WDI as fallback
  if ("gdp_wdi" %in% names(unilateral)) {
    unilateral[is.na(gdp), gdp := gdp_wdi]
    unilateral[, gdp_wdi := NULL]
  }
  if ("pop_wdi" %in% names(unilateral)) {
    unilateral[is.na(pop), pop := pop_wdi]
    unilateral[, pop_wdi := NULL]
  }
  if ("gdpcap_wdi" %in% names(unilateral)) {
    unilateral[is.na(gdpcap), gdpcap := gdpcap_wdi]
    unilateral[, gdpcap_wdi := NULL]
  }

} else {
  log_time("  WDI data not found — using CEPII only (may have gaps 2021+)")
  unilateral <- unilateral_cepii
}

# Log GDP
unilateral[, ln_gdp := log(gdp)]
unilateral[, ln_pop := log(pop)]
unilateral[, ln_gdpcap := log(gdpcap)]

log_time(sprintf("  Unilateral panel: %s rows (%d countries x %d years)",
                 format(nrow(unilateral), big.mark = ","),
                 uniqueN(unilateral$iso3),
                 uniqueN(unilateral$year)))

# ---------------------------------------------------------------------------
# 6. Merge bilateral time-invariant + time-varying
# ---------------------------------------------------------------------------
log_time("Merging bilateral components...")

# Expand time-invariant to all years
bilateral_full <- CJ(
  iso3_o = unique(c(bilateral_ti$iso3_o)),
  iso3_d = unique(c(bilateral_ti$iso3_d)),
  year = SAMPLE_YEARS
)
bilateral_full <- bilateral_full[iso3_o != iso3_d]  # no self-trade

# Merge time-invariant
bilateral_full <- merge(bilateral_full, bilateral_ti,
                         by = c("iso3_o", "iso3_d"), all.x = TRUE)

# Merge time-varying (FTA)
if (nrow(bilateral_tv) > 0) {
  bilateral_full <- merge(bilateral_full, bilateral_tv,
                           by = c("iso3_o", "iso3_d", "year"), all.x = TRUE)
}

# Log distance
bilateral_full[, ln_dist := log(dist)]

# Create pair identifier
bilateral_full[, pair := paste(iso3_o, iso3_d, sep = "_")]

log_time(sprintf("  Bilateral panel: %s rows",
                 format(nrow(bilateral_full), big.mark = ",")))

# ---------------------------------------------------------------------------
# 7. Save
# ---------------------------------------------------------------------------
log_time("Saving gravity datasets...")
write_clean(bilateral_full, "gravity_bilateral.parquet")
write_clean(unilateral, "gravity_unilateral.parquet")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Gravity")
log_time(sprintf("Bilateral pairs: %s", format(uniqueN(bilateral_full$pair), big.mark = ",")))
log_time(sprintf("Years: %d-%d", min(bilateral_full$year), max(bilateral_full$year)))
log_time(sprintf("Distance coverage: %.1f%%",
                 100 * mean(!is.na(bilateral_full$dist))))
log_time(sprintf("Unilateral: %d countries", uniqueN(unilateral$iso3)))
log_time("Done. Next: R/03_payment_frictions.R")
