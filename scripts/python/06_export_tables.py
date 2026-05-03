"""
06_export_tables.py — Generate all missing LaTeX tables from CSV data.

Reads existing CSV outputs and produces bare tabular LaTeX fragments
(no \\begin{table} float — that goes in main.tex).

Outputs:
  paper/tables/06_estimation_main/table1_yearly_baseline.tex
  paper/tables/06_estimation_main/table2_panel_specifications.tex
  paper/tables/05_descriptive/summary_statistics.tex
  paper/tables/09_sos_construction/top20_countries.tex
  paper/tables/11_robustness/robustness_summary.tex
  paper/tables/14_feasibility_quadrant/quadrant_summary.tex
  paper/tables/07_estimation_extensive/extensive_margin_booktabs.tex
"""

import os
import pandas as pd
import numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TABLE_DIR = os.path.join(PROJECT, "paper", "tables")


def stars(p):
    if p is None or np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt_coef(c, p):
    if c is None or np.isnan(c):
        return ""
    return f"{c:.3f}{stars(p)}"


def fmt_se(s):
    if s is None or np.isnan(s):
        return ""
    return f"({s:.3f})"


def fmt_n(n):
    return f"{int(n):,}"


# =========================================================================
# TABLE 1: Yearly cross-sectional baseline (derisked x PCI)
# =========================================================================
rob = pd.read_csv(os.path.join(TABLE_DIR, "11_robustness", "robustness_yearly.csv"))
baseline = rob[rob["label"] == "R0: Baseline"].sort_values("year")

years = baseline["year"].tolist()
coefs = baseline["coef"].tolist()
ses = baseline["se"].tolist()
pvals = baseline["pvalue"].tolist()
nobs = baseline["n_obs"].tolist()

lines = []
lines.append(r"\begin{tabular}{l" + "c" * len(years) + "}")
lines.append(r"\toprule")
lines.append(" & ".join([""] + [str(y) for y in years]) + r" \\")
lines.append(r"\midrule")
# Coefficient row
lines.append(" & ".join(["De-risked $\\times$ PCI"] + [fmt_coef(c, p) for c, p in zip(coefs, pvals)]) + r" \\")
# SE row
lines.append(" & ".join([""] + [fmt_se(s) for s in ses]) + r" \\")
lines.append(r"\midrule")
lines.append(" & ".join(["Exporter FE"] + ["Yes"] * len(years)) + r" \\")
lines.append(" & ".join(["Importer FE"] + ["Yes"] * len(years)) + r" \\")
lines.append(" & ".join(["Product FE"] + ["Yes"] * len(years)) + r" \\")
lines.append(" & ".join(["Observations"] + [fmt_n(n) for n in nobs]) + r" \\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "06_estimation_main", "table1_yearly_baseline.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# TABLE 2: Panel specifications (cross-section + pair FE variants)
# =========================================================================
endo_panel = pd.read_csv(os.path.join(TABLE_DIR, "08_endogeneity", "endogeneity_panel.csv"))
rob_panel = pd.read_csv(os.path.join(TABLE_DIR, "11_robustness", "robustness_panel.csv"))

# Extract specs
def get_spec(df, label_substr):
    row = df[df["label"].str.contains(label_substr, case=False)]
    if len(row) == 0:
        return None, None, None, None
    row = row.iloc[0]
    return row.get("coef"), row.get("se"), row.get("pvalue"), row.get("n_obs")

# Column specs: (1) XS no pair FE, (2) Pair FE baseline, (3) Pair FE lag, (4) Pair FE lead
specs = [
    ("(1)", "Cross-section", "R10: No pair FE", rob_panel),
    ("(2)", "Pair FE", "P0: Baseline", endo_panel),
    ("(3)", "Pair FE + Lag", "P1: Lag-1", endo_panel),
    ("(4)", "Pair FE + Lead", "P3: Lead F1", endo_panel),
]

lines = []
lines.append(r"\begin{tabular}{lcccc}")
lines.append(r"\toprule")
lines.append(r" & (1) & (2) & (3) & (4) \\")
lines.append(r" & Cross-section & Pair FE & Pair FE & Pair FE \\")
lines.append(r"\midrule")

coef_row = ["De-risked $\\times$ PCI"]
se_row = [""]
nobs_row = ["Observations"]
pair_fe_row = ["Pair FE"]
for _, _, lbl, df in specs:
    c, s, p, n = get_spec(df, lbl.split(":")[0] + ":")
    if c is None:
        # Try exact match
        row = df[df["label"].str.contains(lbl)]
        if len(row) > 0:
            row = row.iloc[0]
            c, s, p, n = row["coef"], row["se"], row["pvalue"], row["n_obs"]
    coef_row.append(fmt_coef(c, p) if c is not None else "")
    se_row.append(fmt_se(s) if s is not None else "")
    nobs_row.append(fmt_n(n) if n is not None else "")

pair_fe_row += ["No", "Yes", "Yes", "Yes"]

lines.append(" & ".join(coef_row) + r" \\")
lines.append(" & ".join(se_row) + r" \\")
lines.append(r"\midrule")
lines.append(" & ".join(["Exporter $\\times$ Year FE"] + ["Yes"] * 4) + r" \\")
lines.append(" & ".join(["Importer $\\times$ Year FE"] + ["Yes"] * 4) + r" \\")
lines.append(" & ".join(pair_fe_row) + r" \\")
lines.append(" & ".join(["Product FE"] + ["Yes"] * 4) + r" \\")
lines.append(" & ".join(["De-risking measure"] + ["Current", "Current", "Lagged", "Lead"]) + r" \\")
lines.append(" & ".join(nobs_row) + r" \\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "06_estimation_main", "table2_panel_specifications.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# Summary Statistics
# =========================================================================
ss = pd.read_csv(os.path.join(TABLE_DIR, "05_descriptive", "summary_statistics.csv"))

var_labels = {
    "trade_value": "Trade value (USD thousands)",
    # Legacy on-disk column name `pf_cbr` retained in CSV outputs from
    # 05_descriptive.R; substantively this is the FDI-derived proxy.
    # Map both names to the same human-readable label.
    "pf_cbr":    "FDI proxy (legacy: pf\\_cbr)",
    "fdi_proxy": "FDI proxy",
    "pf_rpw": "Remittance cost (\\%)",
    "pci_std": "Product Complexity Index (std.)",
    "eci_o": "Exporter Complexity Index",
    "ln_dist": "Log bilateral distance",
}

lines = []
lines.append(r"\begin{tabular}{lcccccc}")
lines.append(r"\toprule")
lines.append(r" & N & Mean & SD & P25 & Median & P75 \\")
lines.append(r"\midrule")

for _, row in ss.iterrows():
    v = row["Variable"]
    label = var_labels.get(v, v)
    n_str = str(row["N"]).replace(",", "") if isinstance(row["N"], str) else str(int(row["N"]))
    try:
        n_val = int(n_str.replace(",", ""))
        n_fmt = f"{n_val:,}"
    except:
        n_fmt = str(row["N"])
    mean_val = float(row["Mean"])
    sd_val = float(row["SD"])
    p25_val = float(row["P25"])
    med_val = float(row["Median"])
    p75_val = float(row["P75"])

    if v == "trade_value":
        lines.append(f"{label} & {n_fmt} & {mean_val/1000:.1f} & {sd_val/1000:.1f} & {p25_val/1000:.3f} & {med_val/1000:.3f} & {p75_val/1000:.3f}" + r" \\")
    else:
        lines.append(f"{label} & {n_fmt} & {mean_val:.3f} & {sd_val:.3f} & {p25_val:.3f} & {med_val:.3f} & {p75_val:.3f}" + r" \\")

lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "05_descriptive", "summary_statistics.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# SOS Top 20 Countries
# =========================================================================
sos = pd.read_csv(os.path.join(TABLE_DIR, "09_sos_construction", "top20_countries.csv"))
sos = sos.sort_values("rank_total")

lines = []
lines.append(r"\begin{tabular}{clccccc}")
lines.append(r"\toprule")
lines.append(r"Rank & Country & SOS & Intensive & Extensive & De-risked & Trade at Risk \\")
lines.append(r" & & (total) & margin & margin & partners & (USD millions) \\")
lines.append(r"\midrule")

for _, row in sos.iterrows():
    rank = int(row["rank_total"])
    iso = row["iso3"]
    total = row["sos_total"]
    inten = row["sos_intensive_total"]
    exten = row["sos_extensive_total"]
    n_dr = int(row["n_derisked"])
    tar = row["trade_at_risk"] / 1e6

    lines.append(f"{rank} & {iso} & {total:.2f} & {inten:.2f} & {exten:.2f} & {n_dr} & {tar:.1f}" + r" \\")

lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "09_sos_construction", "top20_countries.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# Robustness Summary (yearly mean across specs)
# =========================================================================
rob_all = pd.read_csv(os.path.join(TABLE_DIR, "11_robustness", "robustness_yearly.csv"))

spec_labels = {
    "R0: Baseline": "Baseline",
    "R1: PCI (MoR)": "Alt. PCI (Method of Reflections)",
    "R2: Excl. entrepots": "Excl. entrepot countries",
    "R3: Excl. China": "Excl. China",
    "R4: Excl. commodities": "Excl. commodities (HS 01--27)",
    "R5: Pre-COVID": "Pre-COVID only (2018--2019)",
    "R6: Post-COVID": "Post-COVID only (2021--2023)",
    "R7: OLS log(1+trade)": "OLS log(1+trade)",
    "R8: Threshold 25%": "De-risking threshold: 25\\%",
    "R9: Threshold 75%": "De-risking threshold: 75\\%",
}

summary = []
for lbl in spec_labels:
    sub = rob_all[rob_all["label"] == lbl]
    if len(sub) == 0:
        continue
    mean_c = sub["coef"].mean()
    mean_se = np.sqrt((sub["se"] ** 2).mean())
    n_sig = (sub["pvalue"] < 0.05).sum()
    n_years = len(sub)
    summary.append((lbl, spec_labels[lbl], mean_c, mean_se, n_sig, n_years))

lines = []
lines.append(r"\begin{tabular}{lccc}")
lines.append(r"\toprule")
lines.append(r"Specification & Mean coef. & Mean SE & Sig. years \\")
lines.append(r"\midrule")

for lbl, nice, mc, ms, ns, ny in summary:
    p_approx = 2 * (1 - 0.5)  # placeholder
    # Compute approximate p from z = mc/ms
    from scipy.stats import norm
    z = abs(mc / ms) if ms > 0 else 0
    p_approx = 2 * (1 - norm.cdf(z))
    star_str = stars(p_approx)
    lines.append(f"{nice} & {mc:.3f}{star_str} & ({ms:.3f}) & {ns}/{ny}" + r" \\")

lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "11_robustness", "robustness_summary.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# Feasibility Quadrant Summary
# =========================================================================
quad = pd.read_csv(os.path.join(TABLE_DIR, "14_feasibility_quadrant", "quadrant_summary.csv"))

lines = []
lines.append(r"\begin{tabular}{lcccc}")
lines.append(r"\toprule")
lines.append(r"Quadrant & N countries & Mean SOS & Median SOS & Mean GDP/cap \\")
lines.append(r"\midrule")

for _, row in quad.iterrows():
    q = row["quadrant"]
    n = int(row["n_countries"])
    ms = row["mean_sos"]
    mds = row["median_sos"]
    gdp = row["mean_gdppc"]
    lines.append(f"{q} & {n} & {ms:.2f} & {mds:.2f} & \\${gdp:,.0f}" + r" \\")

lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "14_feasibility_quadrant", "quadrant_summary.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

# =========================================================================
# Extensive Margin (convert tabularray to booktabs)
# =========================================================================
lines = []
lines.append(r"\begin{tabular}{lcccc}")
lines.append(r"\toprule")
lines.append(r" & (1) & (2) & (3) & (4) \\")
lines.append(r" & Density & + De-risking & + Product FE & Logit \\")
lines.append(r"\midrule")
lines.append(r"Density & 4.154*** & 4.059*** & 4.108*** & 45.527*** \\")
lines.append(r" & (0.105) & (0.119) & (0.135) & (1.591) \\")
lines.append(r"Density $\times$ PCI & 0.100*** & 0.057*** & & 1.313*** \\")
lines.append(r" & (0.012) & (0.014) & & (0.212) \\")
lines.append(r"PF country & & $-$0.450*** & $-$0.390*** & $-$3.198** \\")
lines.append(r" & & (0.104) & (0.106) & (1.404) \\")
lines.append(r"Density $\times$ PF & & 1.498*** & 1.232*** & 9.589*** \\")
lines.append(r" & & (0.372) & (0.370) & (3.542) \\")
lines.append(r"PF $\times$ PCI & & 0.152*** & & $-$0.400 \\")
lines.append(r" & & (0.024) & & (0.381) \\")
lines.append(r"\midrule")
lines.append(r"Country FE & Yes & Yes & Yes & Yes \\")
lines.append(r"Year FE & Yes & Yes & Yes & Yes \\")
lines.append(r"Product FE & No & No & Yes & No \\")
lines.append(r"Observations & 212,440 & 212,440 & 212,440 & 212,440 \\")
lines.append(r"$R^2$ & 0.445 & 0.446 & 0.451 & 0.518 \\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")

out = os.path.join(TABLE_DIR, "07_estimation_extensive", "extensive_margin_booktabs.tex")
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"  Wrote {out}")

print("\nAll tables generated.")
