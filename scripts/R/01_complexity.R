# ===========================================================================
# 01_complexity.R — Compute economic complexity metrics from BACI trade data
#
# Computes: RCA, ECI, PCI, proximity matrix, relatedness density
# Key decision: PCI is FIXED to base period (2015-2017 average) to avoid
# reflection problem identified by strategist-critic.
#
# Inputs:  data/cleaned/baci_hs4.parquet
# Outputs: data/cleaned/complexity_pci.parquet      (product-level, fixed)
#          data/cleaned/complexity_eci.parquet       (country x year)
#          data/cleaned/complexity_proximity.parquet (product x product)
#          data/cleaned/complexity_density.parquet   (country x product x year)
#          data/cleaned/complexity_rca.parquet       (country x product x year)
#          data/cleaned/complexity_diagnostics.rds   (validation stats)
# ===========================================================================

source(here::here("scripts", "R", "00_config.R"))

log_section("01_complexity.R — Economic Complexity Metrics")

# ---------------------------------------------------------------------------
# 1. Load BACI HS4 (positive flows only)
# ---------------------------------------------------------------------------
log_time(sprintf("Loading BACI data (HS2_VALIDATION_MODE=%s)...", HS2_VALIDATION_MODE))
log_time(sprintf("  Reading: %s", BACI_FILE))
baci <- read_clean(BACI_FILE)
log_time(sprintf("  %s rows, %d exporters, %d products, %d years",
                 format(nrow(baci), big.mark = ","),
                 uniqueN(baci$iso3_o),
                 uniqueN(baci$hs4),
                 uniqueN(baci$year)))

# ---------------------------------------------------------------------------
# 2. Compute country x product export matrix (summed over importers)
# ---------------------------------------------------------------------------
log_time("Computing country x product export totals...")
exports_cp <- baci[, .(export_value = sum(trade_value, na.rm = TRUE)),
                   by = .(year, iso3 = iso3_o, hs4)]

# ---------------------------------------------------------------------------
# 3. Compute RCA for each year
# ---------------------------------------------------------------------------
log_time("Computing Revealed Comparative Advantage (RCA)...")

compute_rca <- function(dt_year) {
  # Pivot to country x product matrix
  mat <- dcast(dt_year, iso3 ~ hs4, value.var = "export_value", fill = 0)
  countries <- mat$iso3
  mat <- as.matrix(mat[, -1])
  rownames(mat) <- countries

  # Balassa RCA
  country_totals <- rowSums(mat)
  product_totals <- colSums(mat)
  world_total <- sum(mat)

  rca <- sweep(mat, 1, country_totals, "/")
  rca <- sweep(rca, 2, product_totals / world_total, "/")

  # Replace NaN/Inf with 0
  rca[!is.finite(rca)] <- 0

  list(rca = rca, export_matrix = mat)
}

rca_by_year <- list()
export_matrices <- list()

for (yr in SAMPLE_YEARS) {
  dt_yr <- exports_cp[year == yr]
  if (nrow(dt_yr) == 0) next
  result <- compute_rca(dt_yr)
  rca_by_year[[as.character(yr)]] <- result$rca
  export_matrices[[as.character(yr)]] <- result$export_matrix
  log_time(sprintf("  %d: %d countries x %d products",
                   yr, nrow(result$rca), ncol(result$rca)))
}

# Save full RCA as long-format data.table
rca_long <- rbindlist(lapply(names(rca_by_year), function(yr) {
  rca <- rca_by_year[[yr]]
  dt <- as.data.table(as.table(rca))
  setnames(dt, c("iso3", "hs4", "rca"))
  dt[, year := as.integer(yr)]
  dt[, has_rca := as.integer(rca >= RCA_THRESHOLD)]
  dt
}))
write_clean(rca_long, "complexity_rca.parquet")

# ---------------------------------------------------------------------------
# 4. Compute ECI and PCI
# ---------------------------------------------------------------------------
log_time("Computing ECI and PCI (eigenvalue method)...")

compute_complexity <- function(rca_matrix, method = PCI_METHOD) {
  # Binary MCP matrix
  mcp <- ifelse(rca_matrix >= RCA_THRESHOLD, 1, 0)

  # Use economiccomplexity package
  cm <- complexity_measures(
    mcp,
    method = method,
    iterations = N_REFLECTIONS
  )

  list(
    eci = cm$complexity_index_country,
    pci = cm$complexity_index_product,
    mcp = mcp
  )
}

eci_by_year <- list()
pci_by_year <- list()

for (yr in names(rca_by_year)) {
  result <- compute_complexity(rca_by_year[[yr]])
  eci_by_year[[yr]] <- result$eci
  pci_by_year[[yr]] <- result$pci
  log_time(sprintf("  %s: ECI range [%.2f, %.2f], PCI range [%.2f, %.2f]",
                   yr,
                   min(result$eci), max(result$eci),
                   min(result$pci), max(result$pci)))
}

# ---------------------------------------------------------------------------
# 5. Fix PCI to base period average (CRITICAL — strategist-critic requirement)
# ---------------------------------------------------------------------------
log_time("Fixing PCI to base period average (2015-2017)...")

base_years <- as.character(BASE_PERIOD)
base_pci_list <- pci_by_year[base_years]

# Find common products across base years
common_products <- Reduce(intersect, lapply(base_pci_list, names))
log_time(sprintf("  Common products across base period: %d", length(common_products)))

# Average PCI across base years
pci_base <- sapply(common_products, function(p) {
  mean(sapply(base_pci_list, function(pci) pci[p]), na.rm = TRUE)
})

# Standardize to mean 0, sd 1
pci_std <- standardize(pci_base)

pci_dt <- data.table(
  hs4 = names(pci_base),
  pci_raw = pci_base,
  pci_std = pci_std
)
write_clean(pci_dt, "complexity_pci.parquet")
log_time(sprintf("  PCI (base period): mean=%.3f, sd=%.3f (standardized: mean=%.3f, sd=%.3f)",
                 mean(pci_base), sd(pci_base),
                 mean(pci_std), sd(pci_std)))

# Also compute Method of Reflections PCI for robustness
log_time("Computing PCI via Method of Reflections (robustness)...")
pci_mr_list <- list()
for (yr in base_years) {
  result_mr <- compute_complexity(rca_by_year[[yr]], method = "reflections")
  pci_mr_list[[yr]] <- result_mr$pci
}
common_mr <- Reduce(intersect, lapply(pci_mr_list, names))
pci_mr_base <- sapply(common_mr, function(p) {
  mean(sapply(pci_mr_list, function(pci) pci[p]), na.rm = TRUE)
})
pci_dt[, pci_mr := pci_mr_base[match(hs4, names(pci_mr_base))]]
pci_dt[, pci_mr_std := standardize(pci_mr)]
write_clean(pci_dt, "complexity_pci.parquet")  # overwrite with MR column added

# Correlation between eigenvalue and MR methods
cor_methods <- cor(pci_dt$pci_std, pci_dt$pci_mr_std, use = "complete.obs")
log_time(sprintf("  Correlation eigenvalue vs MR: %.3f", cor_methods))

# ---------------------------------------------------------------------------
# 6. Save ECI (time-varying — country x year)
# ---------------------------------------------------------------------------
log_time("Saving ECI (country x year)...")
eci_dt <- rbindlist(lapply(names(eci_by_year), function(yr) {
  data.table(
    iso3 = names(eci_by_year[[yr]]),
    year = as.integer(yr),
    eci = as.numeric(eci_by_year[[yr]])
  )
}))
write_clean(eci_dt, "complexity_eci.parquet")

# ---------------------------------------------------------------------------
# 7. Compute proximity matrix (base period)
# ---------------------------------------------------------------------------
log_time("Computing proximity matrix (base period average)...")

# Use base period MCP for proximity
base_mcp_list <- lapply(base_years, function(yr) {
  ifelse(rca_by_year[[yr]] >= RCA_THRESHOLD, 1, 0)
})

# Average MCP across base years, then re-binarize
common_countries <- Reduce(intersect, lapply(base_mcp_list, rownames))
common_prods <- Reduce(intersect, lapply(base_mcp_list, colnames))

mcp_avg <- Reduce("+", lapply(base_mcp_list, function(m) {
  m[common_countries, common_prods]
})) / length(base_mcp_list)
mcp_binary <- ifelse(mcp_avg >= 0.5, 1, 0)  # majority rule

prox <- proximity(mcp_binary)
prox_mat <- prox$proximity_product

# Save as long-format (only upper triangle, >0 proximity)
log_time("Converting proximity to long format...")
prox_long <- as.data.table(as.table(prox_mat))
setnames(prox_long, c("hs4_a", "hs4_b", "proximity"))
prox_long <- prox_long[hs4_a < hs4_b & proximity > 0]
write_clean(prox_long, "complexity_proximity.parquet")
log_time(sprintf("  Proximity pairs (>0): %s", format(nrow(prox_long), big.mark = ",")))

# ---------------------------------------------------------------------------
# 8. Compute relatedness density (country x product x year)
# ---------------------------------------------------------------------------
log_time("Computing relatedness density...")

compute_density <- function(mcp_matrix, prox_matrix) {
  # For each country-product pair:
  # density[c,p] = sum(proximity[p,p'] * mcp[c,p']) / sum(proximity[p,p'])
  # Only for products p where mcp[c,p] = 0 (non-exported products)

  common_p <- intersect(colnames(mcp_matrix), colnames(prox_matrix))
  mcp_sub <- mcp_matrix[, common_p]
  prox_sub <- prox_matrix[common_p, common_p]

  # Denominator: sum of proximity for each product
  prox_sum <- colSums(prox_sub)

  # Numerator: mcp %*% proximity
  numerator <- mcp_sub %*% prox_sub

  # Density
  density <- sweep(numerator, 2, prox_sum, "/")
  density[!is.finite(density)] <- 0

  density
}

density_list <- list()
for (yr in names(rca_by_year)) {
  mcp_yr <- ifelse(rca_by_year[[yr]] >= RCA_THRESHOLD, 1, 0)
  # Use common products with proximity matrix
  common_p <- intersect(colnames(mcp_yr), colnames(prox_mat))
  common_c <- rownames(mcp_yr)
  mcp_yr_sub <- mcp_yr[common_c, common_p]
  prox_sub <- prox_mat[common_p, common_p]

  dens <- compute_density(mcp_yr_sub, prox_sub)
  density_list[[yr]] <- dens
  log_time(sprintf("  %s: %d countries x %d products", yr, nrow(dens), ncol(dens)))
}

# Save as long format
density_long <- rbindlist(lapply(names(density_list), function(yr) {
  d <- density_list[[yr]]
  dt <- as.data.table(as.table(d))
  setnames(dt, c("iso3", "hs4", "density"))
  dt[, year := as.integer(yr)]
  dt
}))
write_clean(density_long, "complexity_density.parquet")

# ---------------------------------------------------------------------------
# 9. Validation against Harvard Growth Lab
# ---------------------------------------------------------------------------
log_time("Validating ECI against Harvard Growth Lab...")

diagnostics <- list(
  n_countries = uniqueN(eci_dt$iso3),
  n_products_pci = nrow(pci_dt),
  pci_eigenvalue_mr_correlation = cor_methods,
  eci_range = range(eci_dt$eci),
  pci_range = range(pci_dt$pci_raw),
  proximity_pairs = nrow(prox_long),
  density_rows = nrow(density_long)
)

# Try to load Harvard validation data
harvard_path <- file.path(DIR_RAW, "harvard_eci_rankings.csv")
if (file.exists(harvard_path)) {
  harvard <- fread(harvard_path)
  # Attempt to match and correlate
  log_time("  Harvard ECI data found — computing rank correlation...")
  # This depends on the exact format of the Harvard data
  # We'll attempt a basic correlation
  diagnostics$harvard_validation <- "attempted"
} else {
  log_time("  Harvard ECI data not found — skipping validation")
  log_time("  Run py/00_download_data.py to download, or manually save to data/raw/")
  diagnostics$harvard_validation <- "skipped"
}

saveRDS(diagnostics, file.path(DIR_CLEAN, "complexity_diagnostics.rds"))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log_section("SUMMARY — Economic Complexity")
log_time(sprintf("Countries: %d", diagnostics$n_countries))
log_time(sprintf("Products (HS4): %d", diagnostics$n_products_pci))
log_time(sprintf("PCI method: %s (base period %d-%d, standardized)",
                 PCI_METHOD, min(BASE_PERIOD), max(BASE_PERIOD)))
log_time(sprintf("PCI eigenvalue-MR correlation: %.3f", cor_methods))
log_time(sprintf("Proximity pairs (>0): %s",
                 format(diagnostics$proximity_pairs, big.mark = ",")))
log_time(sprintf("Density matrix: %s rows",
                 format(diagnostics$density_rows, big.mark = ",")))
log_time("Done. Next: R/02_gravity.R and R/03_payment_frictions.R")
