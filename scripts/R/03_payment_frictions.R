# ===========================================================================
# 03_payment_frictions.R — Clean all payment friction sources
#
# Primary:   BIS/CPMI correspondent banking density (bilateral)
# Secondary: World Bank RPW remittance costs (bilateral, 367 corridors)
# Country:   IMF FAS financial access, Chinn-Ito KAOPEN
#
# Inputs:  data/raw/bis_cpmi_corr_banking.csv
#          data/raw/rpw_dataset.xlsx
#          data/raw/imf_fas.csv
#          data/raw/chinn_ito_kaopen.xlsx
# Outputs: data/cleaned/pf_cbr.parquet     (LEGACY NAME — see note below)
#          data/cleaned/pf_rpw.parquet     (bilateral, secondary friction)
#          data/cleaned/pf_fas.parquet     (country-level)
#          data/cleaned/pf_kaopen.parquet  (country-level)
#
# IMPORTANT — LEGACY NAMING (pf_cbr → fdi_proxy):
#   The output file `pf_cbr.parquet` was originally intended for BIS CBR data.
#   In practice the BIS file was never obtained, and the column actually
#   contains a transformation of CDIS bilateral FDI (built in 04_merge_panel.R).
#   The on-disk column name `pf_cbr` is preserved for backward compatibility,
#   but downstream R/Python code reads the column and renames it to
#   `fdi_proxy` immediately on load (see rename_pf_to_fdi() in 00_config.R).
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("03_payment_frictions.R — Payment Friction Sources")

# ===================================================================
# 1. BIS/CPMI Correspondent Banking Density (PRIMARY)
# ===================================================================
log_time("Processing BIS/CPMI Correspondent Banking...")

bis_path <- list.files(DIR_RAW, pattern = "bis.*cpmi|cpmi.*corr",
                        full.names = TRUE, ignore.case = TRUE)

if (length(bis_path) > 0) {
  log_time(paste("  Loading:", basename(bis_path[1])))
  bis_raw <- fread(bis_path[1], na.strings = c("", "NA", "."))
  log_time(sprintf("  Raw BIS: %s rows, %d columns",
                   format(nrow(bis_raw), big.mark = ","), ncol(bis_raw)))

  # BIS data format varies — attempt to identify key columns
  # Expected: sending_country, receiving_country, year/period, n_correspondents
  cols_lower <- tolower(names(bis_raw))
  names(bis_raw) <- cols_lower

  # Attempt to extract bilateral correspondent banking counts
  # This will need adaptation based on actual BIS file format
  # The BIS CPMI data typically has country pairs and counts of active
  # correspondent relationships

  # Generic approach: look for country columns and value columns
  country_cols <- grep("country|economy|jurisdiction|iso", cols_lower, value = TRUE)
  value_cols <- grep("value|count|number|correspondents|active", cols_lower, value = TRUE)
  time_cols <- grep("year|period|date|time", cols_lower, value = TRUE)

  log_time(paste("  Detected columns — country:", paste(country_cols, collapse = ", ")))
  log_time(paste("  Detected columns — value:", paste(value_cols, collapse = ", ")))
  log_time(paste("  Detected columns — time:", paste(time_cols, collapse = ", ")))

  # Placeholder: construct the friction variable
  # This section MUST be adapted once the actual BIS data format is inspected
  if (length(country_cols) >= 2 && length(value_cols) >= 1) {
    cbr <- bis_raw[, c(country_cols[1:2], time_cols[1], value_cols[1]), with = FALSE]
    setnames(cbr, c("iso3_o", "iso3_d", "year", "n_correspondents"))
    cbr[, year := as.integer(year)]
    cbr[, n_correspondents := as.numeric(n_correspondents)]
    cbr <- cbr[year %in% SAMPLE_YEARS]

    # Apply friction transformation: higher = more friction
    cbr[, pf_cbr := pf_cbr_transform(n_correspondents)]

    log_time(sprintf("  CBR processed: %s corridor-years",
                     format(nrow(cbr), big.mark = ",")))
  } else {
    log_time("  WARNING: Could not auto-detect BIS column structure.")
    log_time("  Creating empty placeholder — manual inspection required.")
    cbr <- data.table(iso3_o = character(), iso3_d = character(),
                       year = integer(), n_correspondents = numeric(),
                       pf_cbr = numeric())
  }
} else {
  log_time("  BIS/CPMI file not found — creating empty placeholder")
  log_time("  Download from: https://www.bis.org/cpmi/paysysinfo.htm")
  cbr <- data.table(iso3_o = character(), iso3_d = character(),
                     year = integer(), n_correspondents = numeric(),
                     pf_cbr = numeric())
}

write_clean(cbr, "pf_cbr.parquet")

# ===================================================================
# 2. World Bank Remittance Prices Worldwide (SECONDARY)
# ===================================================================
log_time("Processing World Bank RPW...")

rpw_path <- list.files(DIR_RAW, pattern = "rpw.*\\.xlsx$|remittance.*price",
                        full.names = TRUE, ignore.case = TRUE)

if (length(rpw_path) > 0) {
  log_time(paste("  Loading:", basename(rpw_path[1])))

  # RPW is distributed as Excel with multiple sheets
  # Main sheet has: sending_country, receiving_country, firm, period,
  #                 total_cost_pct_200, total_cost_pct_500, etc.
  rpw_raw <- as.data.table(readxl::read_excel(rpw_path[1]))
  log_time(sprintf("  Raw RPW: %s rows", format(nrow(rpw_raw), big.mark = ",")))

  # Standardize column names
  setnames(rpw_raw, tolower(gsub("[^a-zA-Z0-9]", "_", names(rpw_raw))))

  # Look for key columns
  send_col <- grep("send|source|origin", names(rpw_raw), value = TRUE)[1]
  recv_col <- grep("receiv|dest|target", names(rpw_raw), value = TRUE)[1]
  cost_col <- grep("total.*cost.*200|cc1", names(rpw_raw), value = TRUE)[1]
  period_col <- grep("period|quarter|date|year", names(rpw_raw), value = TRUE)[1]

  if (!is.na(send_col) && !is.na(recv_col) && !is.na(cost_col)) {
    rpw <- rpw_raw[, c(send_col, recv_col, period_col, cost_col), with = FALSE]
    setnames(rpw, c("sending_country", "receiving_country", "period", "total_cost_pct"))

    # Convert country names to ISO3
    rpw[, iso3_o := countrycode(sending_country, "country.name", "iso3c",
                                 warn = FALSE)]
    rpw[, iso3_d := countrycode(receiving_country, "country.name", "iso3c",
                                 warn = FALSE)]

    # Extract year from period
    rpw[, year := as.integer(substr(as.character(period), 1, 4))]
    rpw[, total_cost_pct := as.numeric(total_cost_pct)]

    # Aggregate to corridor-year mean (averaging across providers and quarters)
    rpw_agg <- rpw[year %in% SAMPLE_YEARS & !is.na(iso3_o) & !is.na(iso3_d),
                    .(pf_rpw = mean(total_cost_pct, na.rm = TRUE),
                      n_providers = .N),
                    by = .(iso3_o, iso3_d, year)]

    log_time(sprintf("  RPW processed: %s corridor-years (%d unique corridors)",
                     format(nrow(rpw_agg), big.mark = ","),
                     uniqueN(paste(rpw_agg$iso3_o, rpw_agg$iso3_d))))
  } else {
    log_time("  WARNING: Could not auto-detect RPW column structure.")
    rpw_agg <- data.table(iso3_o = character(), iso3_d = character(),
                           year = integer(), pf_rpw = numeric(),
                           n_providers = integer())
  }
} else {
  log_time("  RPW file not found — creating empty placeholder")
  rpw_agg <- data.table(iso3_o = character(), iso3_d = character(),
                         year = integer(), pf_rpw = numeric(),
                         n_providers = integer())
}

write_clean(rpw_agg, "pf_rpw.parquet")

# ===================================================================
# 3. IMF Financial Access Survey (Country-Level)
# ===================================================================
log_time("Processing IMF Financial Access Survey...")

fas_path <- list.files(DIR_RAW, pattern = "fas|financial.*access",
                        full.names = TRUE, ignore.case = TRUE)

if (length(fas_path) > 0) {
  log_time(paste("  Loading:", basename(fas_path[1])))
  fas_raw <- fread(fas_path[1], na.strings = c("", "NA", "."))

  # FAS indicators of interest:
  # ATMs per 100,000 adults, bank branches per 100,000 adults,
  # deposit accounts, mobile money accounts
  # Format varies — adapt to actual file structure

  # Attempt generic processing
  setnames(fas_raw, tolower(gsub("[^a-zA-Z0-9]", "_", names(fas_raw))))

  # Look for country and indicator columns
  country_col <- grep("country|economy|iso", names(fas_raw), value = TRUE)[1]

  if (!is.na(country_col)) {
    fas_raw[, iso3 := countrycode(get(country_col), "country.name", "iso3c",
                                    warn = FALSE)]

    # Select key indicators if in wide format, or reshape if long
    # This is highly dependent on the actual FAS file format
    log_time("  FAS loaded — structure requires manual verification")
    fas <- fas_raw[!is.na(iso3)]
  } else {
    fas <- data.table(iso3 = character(), year = integer())
  }
} else {
  log_time("  FAS file not found — using WDI proxies from gravity")
  fas <- data.table(iso3 = character(), year = integer())
}

write_clean(fas, "pf_fas.parquet")

# ===================================================================
# 4. Chinn-Ito KAOPEN (Capital Account Openness)
# ===================================================================
log_time("Processing Chinn-Ito KAOPEN...")

kaopen_path <- list.files(DIR_RAW, pattern = "kaopen|chinn.?ito",
                           full.names = TRUE, ignore.case = TRUE)

if (length(kaopen_path) > 0) {
  log_time(paste("  Loading:", basename(kaopen_path[1])))

  kaopen_raw <- as.data.table(readxl::read_excel(kaopen_path[1]))
  setnames(kaopen_raw, tolower(gsub("[^a-zA-Z0-9]", "_", names(kaopen_raw))))

  # KAOPEN file typically has: country_name, iso2/iso3, year, kaopen, ka_open
  iso_col <- grep("iso.*3|iso3", names(kaopen_raw), value = TRUE)
  if (length(iso_col) == 0) {
    # Try country name conversion
    country_col <- grep("country|cname", names(kaopen_raw), value = TRUE)[1]
    if (!is.na(country_col)) {
      kaopen_raw[, iso3 := countrycode(get(country_col), "country.name", "iso3c",
                                         warn = FALSE)]
    }
  } else {
    setnames(kaopen_raw, iso_col[1], "iso3")
  }

  year_col <- grep("^year$", names(kaopen_raw), value = TRUE)
  ka_col <- grep("kaopen|ka_open", names(kaopen_raw), value = TRUE)

  if (length(year_col) > 0 && length(ka_col) > 0 && "iso3" %in% names(kaopen_raw)) {
    kaopen <- kaopen_raw[, .(iso3, year = as.integer(get(year_col[1])),
                              kaopen = as.numeric(get(ka_col[1])))]
    kaopen <- kaopen[year %in% SAMPLE_YEARS & !is.na(iso3)]

    # Normalize KAOPEN to [0, 1] for comparability
    kaopen[, kaopen_norm := (kaopen - min(kaopen, na.rm = TRUE)) /
             (max(kaopen, na.rm = TRUE) - min(kaopen, na.rm = TRUE))]

    log_time(sprintf("  KAOPEN processed: %d country-years (%d countries)",
                     nrow(kaopen), uniqueN(kaopen$iso3)))
  } else {
    log_time("  WARNING: Could not auto-detect KAOPEN column structure.")
    kaopen <- data.table(iso3 = character(), year = integer(),
                          kaopen = numeric(), kaopen_norm = numeric())
  }
} else {
  log_time("  KAOPEN file not found — creating empty placeholder")
  kaopen <- data.table(iso3 = character(), year = integer(),
                        kaopen = numeric(), kaopen_norm = numeric())
}

write_clean(kaopen, "pf_kaopen.parquet")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Payment Frictions")
log_time(sprintf("CBR (primary): %s corridor-years, %d unique corridors",
                 format(nrow(cbr), big.mark = ","),
                 uniqueN(paste(cbr$iso3_o, cbr$iso3_d))))
log_time(sprintf("RPW (secondary): %s corridor-years, %d unique corridors",
                 format(nrow(rpw_agg), big.mark = ","),
                 uniqueN(paste(rpw_agg$iso3_o, rpw_agg$iso3_d))))
log_time(sprintf("FAS: %s rows", format(nrow(fas), big.mark = ",")))
log_time(sprintf("KAOPEN: %s country-years",
                 format(nrow(kaopen), big.mark = ",")))
log_time("Done. Next: R/04_merge_panel.R")
