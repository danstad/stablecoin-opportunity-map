"""
14_feasibility_quadrant.py — Feasibility Quadrant policy overlay on SOS

Classifies countries on a 2x2 grid:
    x-axis: Capital account openness (Chinn-Ito KAOPEN, latest year >= 2018)
    y-axis: On/off-ramp infrastructure availability

Quadrants (split at sample medians):
    Q1 (high openness, high infrastructure): "Actionable now"
    Q2 (high openness, low infrastructure):  "Infrastructure gap"
    Q3 (low openness, high infrastructure):  "Legal complexity — sandbox"
    Q4 (low openness, low infrastructure):   "Structurally blocked"

Infrastructure proxy
--------------------
Chainalysis grassroots adoption rankings and stablecoin-exchange country
listings are NOT available on this machine. Per the strategy memo, we adopt
a developmental proxy: log GDP per capita (latest available year) from
gravity_unilateral.parquet. Higher GDP per capita correlates with deeper
fintech penetration, smartphone adoption, retail-broker availability, and
local on/off-ramp partners. This is a placeholder; a future pipeline run
should swap in Chainalysis ranks once licensed.

    TODO: replace `infrastructure_score` with Chainalysis grassroots adoption
          rank (inverted) when the dataset becomes available.

Inputs
------
    data/cleaned/sos_country_composite.parquet
    data/cleaned/pf_kaopen.parquet
    data/cleaned/gravity_unilateral.parquet  (GDP per capita proxy)

Outputs
-------
    data/cleaned/feasibility_quadrant.parquet
    paper/tables/14_feasibility_quadrant/quadrant_summary.tex
    paper/tables/14_feasibility_quadrant/actionable_top10.tex
    paper/figures/14_feasibility_quadrant/quadrant_scatter.pdf

Usage
-----
    python scripts/python/14_feasibility_quadrant.py
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Shared style (serif, larger fonts) from _figure_style.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _figure_style import apply_style  # noqa: E402

# ---------------------------------------------------------------------------
# 0. Setup
# ---------------------------------------------------------------------------
SEED = 20260502
np.random.seed(SEED)

PROJECT   = Path(__file__).resolve().parents[2]
DIR_CLEAN = PROJECT / "data" / "cleaned"
TABLE_DIR = PROJECT / "paper" / "tables" / "14_feasibility_quadrant"
FIG_DIR   = PROJECT / "paper" / "figures" / "14_feasibility_quadrant"
JOURNAL   = PROJECT / "quality_reports" / "research_journal.md"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

KAOPEN_MIN_YEAR = 2018


def log(msg: str) -> None:
    safe = msg.encode("ascii", errors="replace").decode("ascii")
    print(f"[{time.strftime('%H:%M:%S')}] {safe}", flush=True)


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
log("=" * 70)
log("14_feasibility_quadrant.py — Feasibility Quadrant policy overlay")
log("=" * 70)

log("[1/5] Loading SOS, KAOPEN, and gravity unilateral data ...")
sos = pd.read_parquet(DIR_CLEAN / "sos_country_composite.parquet")
kaopen = pd.read_parquet(DIR_CLEAN / "pf_kaopen.parquet")
uni = pd.read_parquet(DIR_CLEAN / "gravity_unilateral.parquet")

log(f"  SOS:    {len(sos):,} countries")
log(f"  KAOPEN: {len(kaopen):,} country-year rows")
log(f"  Uni:    {len(uni):,} country-year rows")


# ---------------------------------------------------------------------------
# 2. Build country-level cross-section
# ---------------------------------------------------------------------------
log("[2/5] Building country-level cross-section ...")

# Latest KAOPEN per country (year >= 2018)
ka = kaopen.loc[kaopen["year"] >= KAOPEN_MIN_YEAR].copy()
ka = ka.sort_values(["iso3", "year"]).groupby("iso3", as_index=False).tail(1)
ka = ka[["iso3", "year", "kaopen", "kaopen_norm"]].rename(
    columns={"year": "kaopen_year", "kaopen_norm": "kaopen_score"}
)
log(f"  KAOPEN cross-section: {len(ka):,} countries (year range "
    f"{ka['kaopen_year'].min()}-{ka['kaopen_year'].max()})")

# Latest GDP per capita per country.
# Note: gravity_unilateral's ln_gdpcap is year-normalized and NA for the
# most recent years. Re-derive ln_gdpcap from raw gdpcap so we keep the
# latest available observation per country.
uni_gdp = uni.copy()
uni_gdp["ln_gdpcap_raw"] = np.log(uni_gdp["gdpcap"].where(uni_gdp["gdpcap"] > 0))
gdp = (
    uni_gdp.dropna(subset=["ln_gdpcap_raw"])
    .sort_values(["iso3", "year"])
    .groupby("iso3", as_index=False)
    .tail(1)[["iso3", "year", "gdpcap", "ln_gdpcap_raw", "internet_pct"]]
    .rename(columns={"year": "gdp_year", "ln_gdpcap_raw": "ln_gdpcap"})
)
log(f"  GDP cross-section:   {len(gdp):,} countries (year range "
    f"{gdp['gdp_year'].min()}-{gdp['gdp_year'].max()})")

# Merge
quad = sos[["iso3", "sos_composite", "rank_composite"]].merge(
    ka, on="iso3", how="left"
).merge(gdp, on="iso3", how="left")

# Infrastructure score = ln(GDPpc) (developmental proxy; see TODO above)
quad["infrastructure_score"] = quad["ln_gdpcap"]

n_full = quad[["kaopen_score", "infrastructure_score"]].dropna().shape[0]
log(f"  Countries with both axes: {n_full:,} / {len(quad):,}")


# ---------------------------------------------------------------------------
# 3. Quadrant assignment via median splits
# ---------------------------------------------------------------------------
log("[3/5] Assigning quadrants via median splits ...")

ka_med  = quad["kaopen_score"].median(skipna=True)
inf_med = quad["infrastructure_score"].median(skipna=True)

log(f"  Sample median KAOPEN_norm:        {ka_med:.4f}")
log(f"  Sample median infrastructure (ln GDPpc): {inf_med:.4f}")


def assign_quadrant(row: pd.Series) -> str:
    k = row["kaopen_score"]
    s = row["infrastructure_score"]
    if pd.isna(k) or pd.isna(s):
        return "NA"
    high_k = k >= ka_med
    high_s = s >= inf_med
    if high_k and high_s:
        return "Q1"
    if high_k and not high_s:
        return "Q2"
    if not high_k and high_s:
        return "Q3"
    return "Q4"


QUAD_LABELS = {
    "Q1": "Q1: Actionable now",
    "Q2": "Q2: Infrastructure gap",
    "Q3": "Q3: Legal complexity (sandbox)",
    "Q4": "Q4: Structurally blocked",
    "NA": "Unclassified",
}

quad["quadrant"]       = quad.apply(assign_quadrant, axis=1)
quad["quadrant_label"] = quad["quadrant"].map(QUAD_LABELS)

# Actionable priority = SOS x indicator(Q1)
quad["actionable_priority"] = np.where(
    quad["quadrant"].eq("Q1"), quad["sos_composite"], 0.0
)

# Save cleaned dataset
out_pq = DIR_CLEAN / "feasibility_quadrant.parquet"
quad.to_parquet(out_pq, index=False)
log(f"  Saved: {out_pq.relative_to(PROJECT)}")

# Console: quadrant counts and Q1 top-10
counts = quad["quadrant"].value_counts().reindex(["Q1", "Q2", "Q3", "Q4", "NA"], fill_value=0)
log("Quadrant counts:")
for q, n in counts.items():
    log(f"  {QUAD_LABELS[q]:35s}  {n:4d}")

q1_top10 = (
    quad.loc[quad["quadrant"].eq("Q1")]
    .sort_values("sos_composite", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
log("Q1 (Actionable now) — top 10 by SOS composite:")
for _, r in q1_top10.iterrows():
    log(f"  {r['iso3']}  SOS={r['sos_composite']:8.3f}  "
        f"KAOPEN={r['kaopen_score']:.3f}  ln(GDPpc)={r['infrastructure_score']:.3f}")


# ---------------------------------------------------------------------------
# 4. LaTeX tables (booktabs)
# ---------------------------------------------------------------------------
log("[4/5] Writing LaTeX tables (booktabs) ...")

def fmt_num(x: float, digits: int = 2) -> str:
    if pd.isna(x):
        return "--"
    return f"{x:,.{digits}f}"


# --- Quadrant summary: count, mean SOS, top-3 countries ---
summary_rows = []
for q in ["Q1", "Q2", "Q3", "Q4"]:
    sub = quad.loc[quad["quadrant"].eq(q)]
    n = len(sub)
    mean_sos = sub["sos_composite"].mean() if n else float("nan")
    top3 = (
        sub.sort_values("sos_composite", ascending=False)["iso3"].head(3).tolist()
    )
    top3_str = ", ".join(top3) if top3 else "--"
    summary_rows.append({
        "Quadrant": QUAD_LABELS[q],
        "N": n,
        "Mean SOS": fmt_num(mean_sos, 3),
        "Top-3 (by SOS)": top3_str,
    })

summary_df = pd.DataFrame(summary_rows)

summary_tex = []
summary_tex.append(r"\begin{tabular}{lccl}")
summary_tex.append(r"\toprule")
summary_tex.append(r"Quadrant & N & Mean SOS & Top-3 (by SOS) \\")
summary_tex.append(r"\midrule")
for _, r in summary_df.iterrows():
    summary_tex.append(
        f"{r['Quadrant']} & {r['N']} & {r['Mean SOS']} & {r['Top-3 (by SOS)']} \\\\"
    )
summary_tex.append(r"\bottomrule")
summary_tex.append(r"\end{tabular}")

(quad_summary_path := TABLE_DIR / "quadrant_summary.tex").write_text(
    "\n".join(summary_tex) + "\n", encoding="utf-8"
)
log(f"  Saved: {quad_summary_path.relative_to(PROJECT)}")


# --- Top 10 actionable (Q1 only) ---
actionable_rows = []
for _, r in q1_top10.iterrows():
    actionable_rows.append({
        "ISO3":           r["iso3"],
        "SOS composite":  fmt_num(r["sos_composite"], 3),
        "Rank (overall)": int(r["rank_composite"]) if not pd.isna(r["rank_composite"]) else "--",
        "KAOPEN":         fmt_num(r["kaopen_score"], 3),
        "ln(GDPpc)":      fmt_num(r["infrastructure_score"], 3),
    })

act_tex = []
act_tex.append(r"\begin{tabular}{lcccc}")
act_tex.append(r"\toprule")
act_tex.append(
    r"ISO3 & SOS composite & Rank (overall) & KAOPEN & ln(GDPpc) \\"
)
act_tex.append(r"\midrule")
for r in actionable_rows:
    act_tex.append(
        f"{r['ISO3']} & {r['SOS composite']} & {r['Rank (overall)']} & "
        f"{r['KAOPEN']} & {r['ln(GDPpc)']} \\\\"
    )
act_tex.append(r"\bottomrule")
act_tex.append(r"\end{tabular}")

(act_path := TABLE_DIR / "actionable_top10.tex").write_text(
    "\n".join(act_tex) + "\n", encoding="utf-8"
)
log(f"  Saved: {act_path.relative_to(PROJECT)}")


# ---------------------------------------------------------------------------
# 5. Scatter plot
# ---------------------------------------------------------------------------
log("[5/5] Producing quadrant scatter plot ...")

plot_df = quad.dropna(subset=["kaopen_score", "infrastructure_score", "sos_composite"]).copy()

# SOS quintile coloring
plot_df["sos_quintile"] = pd.qcut(
    plot_df["sos_composite"], q=5, labels=["Q1 (low)", "Q2", "Q3", "Q4", "Q5 (high)"]
)

# Top 20 by SOS for ISO3 labels
top20 = plot_df.sort_values("sos_composite", ascending=False).head(20)

palette = {
    "Q1 (low)":  "#4575b4",
    "Q2":        "#91bfdb",
    "Q3":        "#ffffbf",
    "Q4":        "#fc8d59",
    "Q5 (high)": "#d73027",
}

apply_style()

fig, ax = plt.subplots(figsize=(10, 7.5))

for q_label, color in palette.items():
    sub = plot_df.loc[plot_df["sos_quintile"].eq(q_label)]
    ax.scatter(
        sub["kaopen_score"], sub["infrastructure_score"],
        s=55, c=color, edgecolor="black", linewidth=0.4,
        alpha=0.85, label=f"SOS {q_label}",
    )

# Median splits (use sample medians computed above)
ax.axvline(ka_med,  color="grey", linestyle="--", linewidth=0.8)
ax.axhline(inf_med, color="grey", linestyle="--", linewidth=0.8)

# Quadrant labels in corners
xlim = ax.get_xlim()
ylim = ax.get_ylim()
ax.text(xlim[1], ylim[1], "Q1: Actionable",
        ha="right", va="top", fontsize=12, style="italic", color="#2ca02c")
ax.text(xlim[1], ylim[0], "Q2: Infra gap",
        ha="right", va="bottom", fontsize=12, style="italic", color="#ff7f0e")
ax.text(xlim[0], ylim[1], "Q3: Sandbox",
        ha="left", va="top", fontsize=12, style="italic", color="#d62728")
ax.text(xlim[0], ylim[0], "Q4: Blocked",
        ha="left", va="bottom", fontsize=12, style="italic", color="#7f7f7f")

# ISO3 labels for top 20 by SOS at the larger font size. Suppress labels that
# fall too close to an already-placed label (simple greedy thinning). Distance
# threshold is in axis-coord units rescaled by axis range.
xrng = xlim[1] - xlim[0]
yrng = ylim[1] - ylim[0]
min_sep_x = 0.04 * xrng
min_sep_y = 0.04 * yrng

placed = []  # list of (x, y)
for _, r in top20.iterrows():
    x, y = r["kaopen_score"], r["infrastructure_score"]
    too_close = any(
        abs(x - px) < min_sep_x and abs(y - py) < min_sep_y
        for px, py in placed
    )
    if too_close:
        continue
    ax.annotate(
        r["iso3"],
        xy=(x, y),
        xytext=(4, 4), textcoords="offset points",
        fontsize=11, family="serif", fontweight="bold",
    )
    placed.append((x, y))

ax.set_xlabel("Capital account openness (KAOPEN, normalized)")
ax.set_ylabel("On/off-ramp infrastructure proxy (ln GDP per capita)")
ax.legend(loc="lower right", frameon=True, framealpha=0.9)
ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.6)

fig.tight_layout()
out_pdf = FIG_DIR / "quadrant_scatter.pdf"
fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
plt.close(fig)
log(f"  Saved: {out_pdf.relative_to(PROJECT)}")


# ---------------------------------------------------------------------------
# 6. Append research journal entry
# ---------------------------------------------------------------------------
ts = datetime.now().strftime("%Y-%m-%d %H:%M")
journal_entry = (
    f"\n### {ts} — coder\n"
    f"**Phase:** Execution\n"
    f"**Target:** scripts/python/14_feasibility_quadrant.py\n"
    f"**Score:** N/A (pending coder-critic)\n"
    f"**Verdict:** Quadrant overlay computed; Q1 top-10 actionable countries identified.\n"
    f"**Report:** paper/tables/14_feasibility_quadrant/quadrant_summary.tex\n"
)
JOURNAL.parent.mkdir(parents=True, exist_ok=True)
with open(JOURNAL, "a", encoding="utf-8") as f:
    f.write(journal_entry)
log(f"  Appended journal entry to {JOURNAL.relative_to(PROJECT)}")

log("=" * 70)
log("Done.")
log("=" * 70)
