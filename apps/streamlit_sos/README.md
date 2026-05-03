# Stablecoin Opportunity Map -- Interactive Explorer

A Streamlit companion to the working paper *The Stablecoin Opportunity Map:
Economic Complexity Meets Payment Innovation*. The app lets a non-technical
reader pick a country and see the analysis applied to it: composite SOS,
three-pronged decomposition (FATF / FDI / AMLD), products at risk,
diversification opportunities, and top derisked corridors.

This is **Stage 1 (MVP)** of the two-stage build documented in
`quality_reports/plans/snappy-churning-dahl.md`. Stage 2 ports the same
data to a static Quarto + Observable site.

## Run locally

From the project root:

```bash
streamlit run apps/streamlit_sos/app.py
```

The app loads only slim parquets in `data/cleaned/webapp/` and the
country-level SOS files. The 553 MB main panel is never touched.

## Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. Connect the repo at <https://share.streamlit.io>.
3. Point the app entry to `apps/streamlit_sos/app.py`, Python 3.11.
4. The cloud runner installs `apps/streamlit_sos/requirements.txt`.
5. Total payload is well under the 300 MB limit.

## Data dictionary

Inputs (read-only; produced by `scripts/python/20_build_webapp_data.py`):

| File | Grain | Rows |
|---|---|---|
| `data/cleaned/webapp/country_lookup.parquet` | one per iso3 | 226 |
| `data/cleaned/webapp/products_at_risk.parquet` | iso3 × hs4 (top-N per country) | 1,813 |
| `data/cleaned/webapp/diversification_opps.parquet` | iso3 × hs4 (top-N per country) | 1,663 |
| `data/cleaned/webapp/corridor_top5.parquet` | iso3 × partner_iso3 (top-5 per country) | 1,130 |
| `data/cleaned/sos_country_composite.parquet` | one per iso3 | 226 |
| `data/cleaned/feasibility_quadrant.parquet` | one per iso3 | 226 |
| `data/cleaned/sos_country_product_composite.parquet` | iso3 × hs4 (filtered subsets) | 21,244 |

## Smoke test

A standalone regression test lives at `_smoke_test.py`. Run it whenever you
modify the components:

```bash
python apps/streamlit_sos/_smoke_test.py
```

It imports every component module and runs every loader, asserting
non-empty outputs for the five reference countries (HTI, FJI, USA, KOR,
ARE).

## File layout

```
apps/streamlit_sos/
  app.py                          # Landing: choropleth + top-20 + selector
  pages/
    1_Country_Detail.py           # KPI row + bars + treemap + 2 tables
    2_Methodology.py              # Plain-language explainer + paper PDF
  components/
    __init__.py
    loaders.py                    # @st.cache_data parquet readers
    charts.py                     # Plotly factories
    tables.py                     # st.dataframe column_config builders
    theme.py                      # Page config + Set2 / viridis colors
  requirements.txt                # Pinned versions
  .streamlit/config.toml          # Theme + server settings
  _smoke_test.py                  # Regression test (no pytest dep)
  README.md                       # This file
```

## Read the paper

The PDF lives at `paper/main.pdf` after compilation. The Methodology page
exposes a download button when the file is present.

---

Built using Claude Code.
