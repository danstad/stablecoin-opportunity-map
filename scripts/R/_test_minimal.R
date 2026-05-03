library(data.table)
library(fixest)

ps <- fread("data/cleaned/panel_main_tiny.csv", nrows=50000)
cat("Loaded", nrow(ps), "rows\n")

# Simple feols first
cat("\nTrying feols...\n")
m <- feols(log(trade_value + 1) ~ ln_dist, data=ps[trade_value > 0 & !is.na(ln_dist)])
cat("feols coef:", coef(m)["ln_dist"], "\n")

# fepois minimal — no FE
cat("\nTrying fepois (no FE)...\n")
ps2 <- ps[!is.na(ln_dist)][1:5000]
m2 <- fepois(trade_value ~ ln_dist, data=ps2)
cat("fepois coef:", coef(m2)["ln_dist"], "\n")

# fepois with FE
cat("\nTrying fepois (with FE)...\n")
m3 <- fepois(trade_value ~ ln_dist | hs4, data=ps2)
cat("fepois+FE coef:", coef(m3)["ln_dist"], "\n")

cat("\nAll tests passed.\n")
