"""
_smoke_test.py -- Programmatic regression test for the Streamlit app.

Imports each component module and runs each loader, asserting non-empty
outputs for the five reference countries (HTI, FJI, USA, KOR, ARE).

Run from the project root:
    python apps/streamlit_sos/_smoke_test.py

This file is intentionally lightweight (no pytest dependency) so it doubles
as a CI canary.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make sibling imports work when this script is run directly.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from components import charts, loaders, tables, theme  # noqa: E402

REFERENCE_ISO3 = ["HTI", "FJI", "USA", "KOR", "ARE"]


def _check(name: str, cond: bool, detail: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}{(' -- ' + detail) if detail else ''}")
    if not cond:
        raise AssertionError(f"{name} failed: {detail}")


def main() -> None:
    print("== Component imports ==")
    _check("import theme", theme is not None)
    _check("import loaders", loaders is not None)
    _check("import charts", charts is not None)
    _check("import tables", tables is not None)

    print()
    print("== Loaders (general) ==")
    lookup = loaders.load_country_lookup()
    _check("load_country_lookup non-empty", not lookup.empty,
           f"{len(lookup)} rows")

    sos_country = loaders.load_sos_country()
    _check("load_sos_country non-empty", not sos_country.empty,
           f"{len(sos_country)} rows / {sos_country.shape[1]} cols")
    _check("sos_country has name col", "name" in sos_country.columns)
    _check("sos_country has quadrant col", "quadrant" in sos_country.columns)

    par = loaders.load_products_at_risk()
    _check("load_products_at_risk non-empty", not par.empty,
           f"{len(par)} rows")

    do = loaders.load_diversification_opps()
    _check("load_diversification_opps non-empty", not do.empty,
           f"{len(do)} rows")

    corr = loaders.load_corridors()
    _check("load_corridors non-empty", not corr.empty,
           f"{len(corr)} rows")

    meta = loaders.load_meta()
    _check("load_meta non-empty", bool(meta),
           f"keys: {list(meta.keys())[:5]}")

    iso_to_name = loaders.get_iso3_to_name()
    _check("get_iso3_to_name non-empty", len(iso_to_name) > 0,
           f"{len(iso_to_name)} entries")

    print()
    print("== Per-country checks ==")
    for iso in REFERENCE_ISO3:
        row = loaders.get_country_row(iso)
        _check(f"{iso}: get_country_row", row is not None,
               f"name={row['name'] if row is not None else 'N/A'}")

        cp = loaders.load_sos_country_product(iso3=iso)
        _check(f"{iso}: load_sos_country_product non-empty", not cp.empty,
               f"{len(cp)} rows")

        # products_at_risk and diversification may be empty for some
        # countries (e.g. small islands); just confirm the slice works.
        par_country = par[par["iso3"] == iso]
        do_country = do[do["iso3"] == iso]
        corr_country = corr[corr["iso3"] == iso]
        print(f"   {iso}: par={len(par_country)} rows, "
              f"div={len(do_country)} rows, corr={len(corr_country)} rows")

    print()
    print("== Chart factories (smoke) ==")
    fig = charts.world_choropleth(sos_country)
    _check("world_choropleth returns figure", fig is not None
           and len(fig.data) > 0)

    fig = charts.quadrant_scatter(sos_country)
    _check("quadrant_scatter returns figure", fig is not None
           and len(fig.data) > 0)

    median_row = sos_country.median(numeric_only=True)
    hti_row = loaders.get_country_row("HTI")
    fig = charts.three_pronged_bars(hti_row, median_row)
    _check("three_pronged_bars returns figure", fig is not None
           and len(fig.data) > 0)

    cp = loaders.load_sos_country_product(iso3="HTI")
    fig = charts.product_treemap(cp, top_n=50)
    _check("product_treemap returns figure", fig is not None)

    corr_hti = corr[corr["iso3"] == "HTI"]
    fig = charts.corridor_bars(corr_hti)
    _check("corridor_bars returns figure", fig is not None)

    print()
    print("== Table factories ==")
    _check("products_at_risk_columns is dict", isinstance(
        tables.products_at_risk_columns(), dict))
    _check("diversification_columns is dict", isinstance(
        tables.diversification_columns(), dict))
    _check("top20_columns is dict", isinstance(
        tables.top20_columns(), dict))

    print()
    print("== Page renders (Streamlit AppTest) ==")
    from streamlit.testing.v1 import AppTest

    project_root = HERE.parent.parent  # apps/streamlit_sos -> project root
    landing = AppTest.from_file(str(HERE / "app.py")).run(timeout=30)
    _check("landing page renders", not landing.exception)

    for iso in REFERENCE_ISO3:
        at = AppTest.from_file(str(HERE / "pages" / "1_Country_Detail.py"))
        at.session_state["selected_iso3"] = iso
        at.run(timeout=30)
        _check(f"country detail renders ({iso})", not at.exception)

    at = AppTest.from_file(str(HERE / "pages" / "1_Country_Detail.py")).run(timeout=30)
    _check("country detail renders (no selection)", not at.exception)
    info_msgs = [i.value for i in at.info]
    _check(
        "no-selection prompt is shown",
        any("Pick a country" in m for m in info_msgs),
        f"info: {info_msgs}",
    )

    method = AppTest.from_file(str(HERE / "pages" / "2_Methodology.py")).run(timeout=30)
    _check("methodology page renders", not method.exception)

    # Suppress unused-variable lint for project_root.
    _ = project_root

    print()
    print("All smoke-test checks passed.")


if __name__ == "__main__":
    main()
