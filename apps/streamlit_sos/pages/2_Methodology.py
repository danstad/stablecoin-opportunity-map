"""
2_Methodology.py -- Plain-language explainer for non-technical readers.

Mirrors paper/sections/00_executive_summary.tex but reformatted for web
viewing. Provides a download button for paper/main.pdf when present.
"""
from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

from components.loaders import get_paper_pdf_path, load_meta
from components.theme import configure_page


configure_page(title="Methodology · Stablecoin Opportunity Map")

st.title("Methodology")
st.caption(
    "How the Stablecoin Opportunity Score is built, and what it can and "
    "cannot say. A plain-language summary of the working paper."
)


# --- Why this matters --------------------------------------------------------

st.header("Why this matters")
st.markdown(
    """
Cross-border payments depend on banks talking to other banks through a network
called **correspondent banking**. Over the last decade, banks have been
quietly walking away from each other -- closing accounts, dropping
relationships, refusing to clear payments through certain country pairs.
Regulators call this **de-risking**.

Not all trade is hit equally. Simple commodities can be paid for with cash,
prepayment, or a single bank transfer. Complex products -- semiconductors,
pharmaceuticals, machinery -- are different. They typically need a chain of
trust: letters of credit, several banks acting in sequence, foreign-exchange
settlement, extended payment terms. When the chain breaks, the kinds of trade
that depend most on the chain are the kinds that get cut first.

**Stablecoins** -- dollar-denominated digital tokens that move on blockchain
networks -- bypass the bank-to-bank chain entirely. The question is simple:
*where would they help most?*
"""
)


# --- The intuition -----------------------------------------------------------

st.header("The intuition")
st.markdown(
    """
If payment-network problems hit complex trade harder than simple trade, the
data should show a clean signature: where countries face *more* payment
friction, complex-goods exports should fall faster than simple-goods exports;
where they face *less* friction, the reverse. The paper uses three real-world
events that pushed payment frictions in **opposite directions**:
"""
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
**FATF greylisting** -- *friction up*

The global anti-money-laundering body publishes a watch list. Once listed,
banks abroad become more cautious about clearing the country's payments.

Expected sign: **γ < 0**
"""
    )
with c2:
    st.markdown(
        """
**EU AMLD harmonization** -- *friction down*

EU members adopted common AML rules in 2017. Within EU corridors, banks
became more confident, not less.

Expected sign: **γ > 0**
"""
    )
with c3:
    st.markdown(
        """
**FDI-derisked corridors** -- *friction up*

When bilateral FDI positions collapse, the underlying financial relationship
has typically broken. A corridor is flagged de-risked if bilateral FDI fell
more than 50% from its 2015-2017 average.

Expected sign: **γ < 0**
"""
    )

st.markdown(
    """
A spurious channel -- a generic "advanced economies do better" story --
cannot produce *opposite* signs on *opposite-direction* shocks. The fact that
AMLD pulls one way while FATF and FDI pull the other way is the cleanest
causal-mechanism evidence available in this setting.
"""
)


# --- What we found -----------------------------------------------------------

st.header("What we found")
st.markdown(
    """
On a panel of **226 countries × 94 product categories × 2018-2023**
(2.82 million observations), the three signs go the right way. Per standard
deviation of product complexity:

- **FATF greylisting** reduces trade flow by **11-30%**.
- **EU AMLD** raises it by **10-15%** in EU corridors after 2017.
- **FDI de-risking** reduces it by **21-37%**.

The pattern survives ten different ways of slicing the data, three
fixed-effect structures, and a battery of placebo tests using gravity
variables (distance, language, regional-trade-agreement coverage) in place
of the friction shocks. The placebos do not load; the friction shocks do.
"""
)


# --- What it is good for -----------------------------------------------------

st.header("What this is good for")
st.markdown(
    """
The estimated effects aggregate into a country-level **Stablecoin
Opportunity Score** -- a ranking of where alternative payment infrastructure
would unlock the most economically valuable trade.

- **Composite top five:** Haiti, Fiji, Syria, Lebanon, Nicaragua. Small
  economies with high friction exposure and limited regulatory alternatives.
- **Feasibility filter** (capital-account openness × infrastructure readiness):
  within the 60 "actionable now" jurisdictions, the top ten by SOS are
  Panama, Trinidad and Tobago, the United Arab Emirates, Bahrain, Georgia,
  San Marino, Uruguay, Oman, Armenia, and Kuwait.
"""
)


# --- What this is and isn't --------------------------------------------------

st.header("What this is -- and isn't")
st.markdown(
    """
This is a **preliminary analysis using publicly available data**. Trade
flows from BACI; complexity from the Harvard Growth Lab; de-risking from
IMF bilateral FDI and the FATF greylist; AMLD timing from public EU sources.

Three limitations follow:

1. **Direct correspondent-banking data, ideally from BIS or SWIFT, would
   sharpen the test.** The FDI-based de-risking measure is a coarse stand-in
   for actual bank-to-bank account closures.
2. **Higher computing power would let us run the full panel** rather than
   subsamples on the heaviest specifications. The full bilateral panel has
   roughly 33 million observations and does not fit in 16 GB of memory under
   the four-fixed-effect Poisson estimator used for robustness; a stratified
   3,000-pair subsample is used for those specifications.
3. **The Chainalysis Global Crypto Adoption Index would replace the
   GDP-per-capita placeholder** used as the second axis of the feasibility
   filter -- a behavioral measure of where stablecoin infrastructure already
   exists, rather than a developmental proxy.

What this analysis *can* show with public data is the **direction and order
of magnitude** of where stablecoins would help most and where they would
help least. It *cannot* say exactly which corridors will respond first, or
how fast adoption would translate into trade.
"""
)


# --- Read the paper ----------------------------------------------------------

st.header("Read the paper")
pdf_path = get_paper_pdf_path()
if pdf_path.exists():
    with pdf_path.open("rb") as fh:
        st.download_button(
            "Download the working paper (PDF)",
            data=fh.read(),
            file_name="stablecoin_opportunity_map.pdf",
            mime="application/pdf",
        )
else:
    st.info(
        "The PDF will appear here once the paper is compiled. "
        "Run `cd paper && xelatex main.tex` to build it."
    )

meta = load_meta()
if meta:
    st.divider()
    st.caption(
        f"Build date: {meta.get('build_date', 'n/a')} · "
        f"Latest data year: {meta.get('year_latest', 'n/a')} · "
        f"Source commit: {meta.get('source_commit', 'unknown')}"
    )
