# Pseudo-Code: Stablecoin Opportunity Map Estimation

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## Phase 1: Data Construction

```
# 1.1 Import and Clean Trade Data
BACI <- read_parquet("BACI_HS12_Y{2015:2023}.parquet")
BACI <- standardize_iso3(BACI)
BACI <- aggregate_to_hs4(BACI)  # ~1,200 products x ~200 exporters x ~200 importers x 9 years

# 1.2 Compute Economic Complexity
FOR each year t in 2015:2023:
    RCA[c,p,t] <- (X[c,p,t] / sum_p(X[c,p,t])) / (sum_c(X[c,p,t]) / sum_cp(X[c,p,t]))
    MCP[c,p,t] <- 1(RCA[c,p,t] >= 1)

    # Eigenvalue method (primary)
    {ECI[c,t], PCI[p,t]} <- eigenvalue_method(MCP[c,p,t])

    # Method of Reflections (robustness)
    {ECI_MR[c,t], PCI_MR[p,t]} <- method_of_reflections(MCP[c,p,t], iterations=20)

    # Proximity matrix
    proximity[p,p',t] <- min(P(RCA_p>=1 | RCA_p'>=1), P(RCA_p'>=1 | RCA_p>=1))

    # Relatedness density
    FOR each country c, product p:
        density[c,p,t] <- sum_{p'!=p}(proximity[p,p',t] * MCP[c,p',t]) / sum_{p'!=p}(proximity[p,p',t])

# 1.3 Merge Gravity Variables
gravity <- read("CEPII_Gravity_V202301.dta")
gravity_ext <- extend_to_2023(gravity, wdi_gdp, wdi_pop)  # Extend time-varying vars with WDI
panel <- merge(BACI, gravity_ext, by=c("iso3_o","iso3_d","year"))

# 1.4 Merge Payment Friction Variables
# Primary: Correspondent Banking
cbr <- read_bis_cpmi("corr_bank_data.csv")  # bilateral, 2011-2023
cbr$pf_cbr <- -log(1 + cbr$n_correspondents)  # higher = more friction
panel <- merge(panel, cbr, by=c("iso3_o","iso3_d","year"), all.x=TRUE)

# Secondary: Remittance Costs (367 corridors only)
rpw <- read("RPW_data.xlsx")
rpw$pf_rpw <- rpw$total_cost_pct  # already in friction direction
panel <- merge(panel, rpw, by=c("iso3_o","iso3_d","year"), all.x=TRUE)

# Country-level frictions (construct bilateral)
fas <- read_imf_fas()  # country x year
kaopen <- read_chinn_ito()  # country x year
panel$fas_bilateral <- pmin(fas[iso3_o], fas[iso3_d])  # minimum of pair
panel$kaopen_bilateral <- (kaopen[iso3_o] + kaopen[iso3_d]) / 2  # mean of pair

# 1.5 Merge Complexity into Panel
panel <- merge(panel, PCI, by=c("hs4","year"))
panel <- merge(panel, ECI, by=c("iso3_o","year"))

# 1.6 Construct Interaction Terms
panel$pf_x_pci <- panel$pf_cbr * panel$pci_std  # standardized PCI
panel$pf_x_efd <- panel$pf_cbr * panel$rz_efd   # Rajan-Zingales horse race

# 1.7 Fill Zeros for Active Pairs
# Identify active pairs: any positive trade in sample period
active_pairs <- unique(panel[trade > 0, .(iso3_o, iso3_d)])
panel <- expand_grid(active_pairs, hs4=unique_products, year=2015:2023)
panel <- merge(panel, trade_data, all.x=TRUE)
panel[is.na(trade), trade := 0]  # zeros for PPML

# 1.8 Construct FE Variables
panel$exporter_year <- paste(panel$iso3_o, panel$year, sep="_")
panel$importer_year <- paste(panel$iso3_d, panel$year, sep="_")
panel$pair <- paste(panel$iso3_o, panel$iso3_d, sep="_")
```

## Phase 2: Estimation -- Intensive Margin

```
library(fixest)

# Specification 1: Baseline Gravity (sanity check)
spec1 <- fepois(
    trade ~ log(dist) + contig + comlang + colony + fta |
        exporter_year + importer_year + hs4,
    data = panel,
    cluster = ~pair
)

# Specification 2a: Payment Friction (cross-sectional identification)
spec2a <- fepois(
    trade ~ pf_cbr + log(dist) + contig + comlang + colony + fta |
        exporter_year + importer_year + hs4,
    data = panel,
    cluster = ~pair
)

# Specification 2b: Payment Friction (within-pair identification)
spec2b <- fepois(
    trade ~ pf_cbr |
        exporter_year + importer_year + pair + hs4,
    data = panel,
    cluster = ~pair
)

# Specification 3: KEY -- Payment Friction x Product Complexity
spec3 <- fepois(
    trade ~ pf_cbr + pf_cbr:pci_std |
        exporter_year + importer_year + pair + hs4,
    data = panel,
    cluster = ~pair
)
# Note: PCI main effect absorbed by product FE
# Note: PF main effect identified from within-pair temporal variation

# Specification 3 enriched: Horse race with Rajan-Zingales
spec3_rz <- fepois(
    trade ~ pf_cbr + pf_cbr:pci_std + pf_cbr:rz_efd |
        exporter_year + importer_year + pair + hs4,
    data = panel,
    cluster = ~pair
)

# Extract key coefficients
alpha2_hat <- coef(spec3)["pf_cbr:pci_std"]
alpha2_se <- se(spec3)["pf_cbr:pci_std"]
```

## Phase 3: Estimation -- Extensive Margin

```
# Construct country x product x year panel
ext_panel <- panel[, .(
    has_rca = as.integer(RCA >= 1),
    density = density,
    pf_country = pf_fas,  # country-level friction
    pci = pci_std,
    gdppc = gdppc,
    kaopen = kaopen
), by = .(iso3, hs4, year)]

# Specification 4: LPM for diversification
spec4 <- feols(
    has_rca ~ density + pf_country + density:pf_country +
              density:pci + pf_country:pci |
        iso3 + year,
    data = ext_panel,
    cluster = ~iso3
)

beta3_hat <- coef(spec4)["density:pf_country"]
```

## Phase 4: SOS Construction

```
# 4.1 Intensive Margin SOS
FOR each country c, product p:
    sos_intensive[c,p] <- 0
    FOR each partner j:
        # Predicted trade increase from eliminating friction
        delta_trade <- alpha2_hat * pci[p] * pf_cbr[c,j] * X[c,j,p,T]
        sos_intensive[c,p] <- sos_intensive[c,p] + delta_trade

# 4.2 Extensive Margin SOS (products c does NOT export)
FOR each country c, product p WHERE RCA[c,p,T] < 1:
    sos_extensive[c,p] <- beta3_hat * density[c,p,T] * pf_country[c,T] * pci[p]

# 4.3 Combined SOS
FOR omega in c(0.5):  # report multiple weights
    sos_combined[c,p] <- omega * sos_intensive[c,p] + (1-omega) * sos_extensive[c,p]

# 4.4 Aggregate to Country Level
sos_country[c] <- sum_p(sos_combined[c,p])

# 4.5 Rank
rankings <- rank(-sos_country)  # highest SOS = rank 1
```

## Phase 5: Validation

```
# 5.1 Load Chainalysis Index
chainalysis <- read_chainalysis_rankings()  # 151 countries, ordinal

# 5.2 Unconditional Rank Correlation
rho_unconditional <- cor(sos_country, chainalysis$rank, method="spearman")

# 5.3 Conditional on Income
resid_sos <- residuals(lm(sos_country ~ log(gdppc)))
resid_chain <- residuals(lm(chainalysis$rank ~ log(gdppc)))
rho_conditional <- cor(resid_sos, resid_chain, method="spearman")

# 5.4 Within-Income-Group Validation
FOR each group in c("LIC","LMIC","UMIC","HIC"):
    subset <- filter(data, income_group == group)
    rho_group <- cor(subset$sos_country, subset$chainalysis_rank, method="spearman")
```

## Phase 6: Endogeneity Checks

```
# 6.1 Lagged Frictions
spec_lag1 <- fepois(
    trade ~ L1_pf_cbr + L1_pf_cbr:pci_std |
        exporter_year + importer_year + pair + hs4,
    data = panel[year >= 2016],
    cluster = ~pair
)

spec_lag2 <- fepois(
    trade ~ L2_pf_cbr + L2_pf_cbr:pci_std |
        exporter_year + importer_year + pair + hs4,
    data = panel[year >= 2017],
    cluster = ~pair
)

# 6.2 Reduced Form: De-Risking x PCI
# Construct de-risking indicator
panel$derisked <- as.integer(delta_cbr[pair,t] < threshold_loss)

spec_rf <- fepois(
    trade ~ derisked + derisked:pci_std |
        exporter_year + importer_year + pair + hs4,
    data = panel,
    cluster = ~pair
)

# 6.3 IV (if first stage is strong)
# First stage: derisked -> pf_cbr
first_stage <- feols(
    pf_cbr ~ derisked | exporter_year + importer_year + pair,
    data = panel,
    cluster = ~pair
)
# Check F-stat > 10

# Second stage (manual 2SLS with interaction -- complex in PPML)
# Use control function approach for PPML-IV
# Or: use feols on log(1+trade) as approximation for IV
spec_iv <- feols(
    log(1 + trade) ~ 1 | exporter_year + importer_year + pair + hs4 |
        pf_cbr + pf_cbr:pci_std ~ derisked + derisked:pci_std,
    data = panel,
    cluster = ~pair
)

# 6.4 Pre-trends / Leads Test
spec_leads <- fepois(
    trade ~ F1_pf_cbr:pci_std + pf_cbr:pci_std + L1_pf_cbr:pci_std |
        exporter_year + importer_year + pair + hs4,
    data = panel[year >= 2016 & year <= 2022],
    cluster = ~pair
)
# Check: F1 coefficient should be null
```

## Phase 7: Output

```
# 7.1 Regression Tables
etable(spec1, spec2a, spec2b, spec3, spec3_rz,
       file = "paper/tables/main_gravity_results.tex")

etable(spec4, file = "paper/tables/extensive_margin.tex")

etable(spec_lag1, spec_lag2, spec_rf, spec_iv,
       file = "paper/tables/endogeneity.tex")

# 7.2 SOS Maps and Rankings
# Top 20 countries table
# Top 50 country x product cells table
# World heat map of SOS_country
# Product space visualization colored by SOS

# 7.3 Validation Scatter
ggplot: SOS_country vs. Chainalysis rank, with GDP-per-capita residualized version
```
