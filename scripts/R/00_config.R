# ===========================================================================
# 00_config.R — Master configuration for Stablecoin Opportunity Map
#
# Sourced by all other R scripts. Sets paths, loads packages, defines
# constants and helper functions. Does not write any files.
# ===========================================================================

# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------
suppressPackageStartupMessages({
  library(data.table)
  library(arrow)
  library(fixest)
  library(economiccomplexity)
  library(ggplot2)
  library(modelsummary)
  library(countrycode)
  library(here)
})

# ---------------------------------------------------------------------------
# Paths (relative to project root via here::here())
# ---------------------------------------------------------------------------
DIR_RAW     <- here("data", "raw")
DIR_CLEAN   <- here("data", "cleaned")
DIR_TABLES  <- here("paper", "tables")
DIR_FIGURES <- here("paper", "figures")
DIR_REPORTS <- here("quality_reports")

# Ensure output directories exist
for (d in c(DIR_CLEAN, DIR_TABLES, DIR_FIGURES)) {
  if (!dir.exists(d)) dir.create(d, recursive = TRUE)
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAMPLE_YEARS   <- 2015:2024     # extended to 2024 (BACI V202601)
BASE_PERIOD    <- 2015:2017     # PCI fixed to this period (strategist-critic)
RCA_THRESHOLD  <- 1.0
PCI_METHOD     <- "eigenvalues"  # primary; "reflections" for robustness
N_REFLECTIONS  <- 20            # iterations for Method of Reflections
HS_DIGITS_MAIN <- 4             # primary aggregation level
CLUSTER_VAR    <- "pair"        # primary clustering

# Validation mode: use HS2 data (set to TRUE for code validation on this machine)
# Set to FALSE for production runs at HS4 on a larger machine
HS2_VALIDATION_MODE <- TRUE
BACI_FILE <- if (HS2_VALIDATION_MODE) "baci_hs2.parquet" else "baci_hs4.parquet"

# Friction transformation: higher value = more friction.
# Legacy name: this transformation was originally written for BIS CBR data
# (correspondent-banking relationships) but was applied to a CDIS-derived
# FDI proxy because BIS CBR was not obtained. The function name is kept for
# backward compatibility with any caller in 03_payment_frictions.R; analytical
# scripts now read the resulting variable as `fdi_proxy`. See paper/sections/03_data.tex.
fdi_proxy_transform <- function(n_correspondents) {
  -log(1 + n_correspondents)
}
# Backward-compatible alias (legacy)
pf_cbr_transform <- fdi_proxy_transform

#' Rename legacy pf_cbr columns to fdi_proxy after reading panel parquets.
#' The on-disk parquet retains the legacy column names; this helper performs
#' the rename in memory so all downstream code uses fdi_proxy consistently.
#' @param dt a data.table just read from data/cleaned/panel_main*.parquet
#' @return dt with pf_cbr* columns renamed to fdi_proxy*
rename_pf_to_fdi <- function(dt) {
  legacy <- c("pf_cbr", "pf_cbr_x_pci", "pf_cbr_x_pci_mr",
              "pf_cbr_L1", "pf_cbr_L2", "pf_cbr_F1",
              "pf_cbr_L1_x_pci", "pf_cbr_L2_x_pci", "pf_cbr_F1_x_pci")
  new   <- c("fdi_proxy", "fdi_proxy_x_pci", "fdi_proxy_x_pci_mr",
             "fdi_proxy_L1", "fdi_proxy_L2", "fdi_proxy_F1",
             "fdi_proxy_L1_x_pci", "fdi_proxy_L2_x_pci", "fdi_proxy_F1_x_pci")
  present <- legacy %in% names(dt)
  if (any(present)) {
    setnames(dt, legacy[present], new[present])
  }
  dt
}

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
set.seed(20260403)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

#' Create a subdirectory for a script's outputs
#' @param script_name e.g., "06_estimation_main"
#' @param type "tables" or "figures"
#' @return path to the subdirectory
ensure_output_dir <- function(script_name, type = c("tables", "figures")) {
  type <- match.arg(type)
  base <- if (type == "tables") DIR_TABLES else DIR_FIGURES
  d <- file.path(base, script_name)
  if (!dir.exists(d)) dir.create(d, recursive = TRUE)
  d
}

#' Read a parquet file from data/cleaned/ as data.table
read_clean <- function(filename) {
  path <- file.path(DIR_CLEAN, filename)
  if (!file.exists(path)) {
    stop("File not found: ", path, "\nRun the prerequisite script first.")
  }
  as.data.table(read_parquet(path))
}

#' Write a data.table to parquet in data/cleaned/
write_clean <- function(dt, filename) {
  path <- file.path(DIR_CLEAN, filename)
  write_parquet(as.data.frame(dt), path)
  message("Saved: ", path, " (", format(nrow(dt), big.mark = ","), " rows)")
}

#' Standardize a numeric vector to mean 0, sd 1
standardize <- function(x) {
  (x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE)
}

#' Print a section header for logging
log_section <- function(title) {
  width <- 60
  message("\n", strrep("=", width))
  message(title)
  message(strrep("=", width))
}

#' Timestamp for logging
log_time <- function(msg) {
  message(sprintf("[%s] %s", format(Sys.time(), "%H:%M:%S"), msg))
}

# ---------------------------------------------------------------------------
# Startup message
# ---------------------------------------------------------------------------
log_section("Stablecoin Opportunity Map -- R Pipeline")
log_time(paste("R version:", R.version.string))
log_time(paste("fixest version:", packageVersion("fixest")))
log_time(paste("data.table version:", packageVersion("data.table")))
log_time(paste("Project root:", here()))
