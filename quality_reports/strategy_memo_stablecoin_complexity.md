# Strategy Memo: Stablecoin Opportunity Map

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Agent:** Strategist
**Date:** 2026-04-03
**Phase:** Strategy
**Status:** DRAFT (awaiting strategist-critic)

---

## 0. Executive Summary

This paper estimates how payment frictions interact with product complexity to shape bilateral trade flows, and uses those estimates to construct a "Stablecoin Opportunity Score" (SOS) identifying which country x product cells would benefit most from stablecoin adoption. The primary empirical design is a **structural gravity model estimated by PPML** with product-level heterogeneity via payment friction x complexity interactions. The key estimand is the **differential trade elasticity of payment frictions across the product complexity distribution** -- i.e., do payment frictions suppress trade in complex products more than in simple products? If yes, then stablecoins (which reduce payment frictions) would disproportionately unlock complex-product trade.

The paper has two distinct empirical components:

1. **Causal estimation** (Sections 5-7): Gravity model estimating the effect of payment frictions on trade, with complexity interactions. This requires careful identification.
2. **Descriptive prediction** (Section 8): The SOS, which combines gravity estimates with complexity metrics to rank country x product opportunities. This is a calibration/prediction exercise, not a causal claim.

---

## 1. Design Choice

### 1.1 The Ideal Experiment

If we could run the ideal experiment, we would:

1. Randomly assign stablecoin payment rails to a subset of bilateral trade corridors
2. Observe the change in trade flows, separately for simple vs. complex products
3. Compare treated corridors to control corridors

This is impossible. Stablecoin adoption is endogenous, driven by the same factors (weak banking systems, capital controls, high inflation) that also affect trade.

### 1.2 Our Design: Structural Gravity with Payment Friction Interactions

We use a **structural gravity model** -- the workhorse of the international trade literature since Anderson and van Wincoop (2003). This is not a quasi-experimental design (DiD, RDD, IV) but rather a structural approach with three key features:

1. **Theory-consistent fixed effects** absorb all unilateral (exporter- and importer-specific) determinants of trade, including multilateral resistance terms. This eliminates a large class of omitted variables.
2. **Within-corridor, cross-product variation** identifies the interaction coefficient. The key question is not "do payment frictions reduce trade?" (absorbed by pair FEs) but "do payment frictions reduce trade *more* for complex products?" This within-pair, across-product variation is much harder to confound.
3. **PPML estimation** (Santos Silva and Tenreyro 2006) handles zeros, heteroskedasticity, and is consistent under the structural gravity model.

### 1.3 Why Not Alternatives?

| Alternative | Why Not |
|------------|---------|
| DiD | No clean "stablecoin treatment" event with a well-defined treatment date and control group. Stablecoin adoption is gradual and endogenous. |
| RDD | No running variable with a discontinuity in stablecoin/payment infrastructure. |
| IV (as primary) | Candidate instruments (de-risking shocks) have limited coverage and may violate exclusion. Better as robustness than primary. |
| Synthetic Control | Unit of analysis is country-pair x product -- too many treated units, too few donors per unit. |
| Selection on Observables | Structural gravity FEs are more credible than selection-on-observables because they absorb *all* unilateral determinants, not just observed ones. |

### 1.4 Precedent

This design follows the template established by:
- **Manova (2013)**: financial development x industry financial vulnerability in gravity
- **Ferrari Minesso et al. (2026)**: payment system interlinking in gravity
- **Borchert et al. (2024)**: correspondent banking loss and trade
- **Freund and Weinhold (2004)**: internet adoption and trade in gravity

---

## 2. Estimand

### 2.1 Primary Estimand: Differential Trade Elasticity

The primary quantity of interest is:

**How much larger is the trade-reducing effect of payment frictions for complex products compared to simple products?**

Formally, this is the coefficient on `PayFriction_{ij,t} x PCI_p` in the gravity equation. It estimates:

- **Estimand type:** Average partial effect (semi-elasticity) -- for a one-unit increase in payment friction, how much additional trade reduction do you get per unit of product complexity?
- **Who it applies to:** All country-pair x product cells in the sample (ATE-like, though in a structural model rather than a treatment effects framework)

### 2.2 Secondary Estimands

| Estimand | What It Captures |
|----------|-----------------|
| Coefficient on `PayFriction_{ij,t}` (when not absorbed by pair FEs) | Average effect of payment friction on trade |
| Coefficient on `PayFriction_{ij,t} x PCI_p` | Differential effect across complexity distribution (PRIMARY) |
| Extensive margin: `PayFriction x Density` interaction | Whether payment frictions block diversification into nearby products |
| SOS rankings | Descriptive prediction, not a causal estimand |

### 2.3 Causal vs. Descriptive Decomposition

| Component | Nature | Identification Standard |
|-----------|--------|------------------------|
| Gravity coefficients (beta-hat on payment frictions, interactions) | Causal (under structural gravity assumptions) | High -- structural FEs, robustness to IV |
| ECI, PCI, proximity matrix | Descriptive (computed from data) | N/A -- these are data transformations |
| SOS = f(beta-hat, PCI, Density, PayFriction) | Predictive/descriptive | Medium -- combines causal estimates with descriptive inputs |
| SOS validation against Chainalysis | Descriptive correlation | Low -- no causal claim |

---

## 3. Estimating Equations

### Notation

| Symbol | Definition |
|--------|-----------|
| $X_{ijp,t}$ | Exports from country $i$ to country $j$ of product $p$ (HS12 6-digit) in year $t$ |
| $PF_{ij,t}$ | Payment friction measure for corridor $i$-$j$ in year $t$ (correspondent banking density, or RPW cost) |
| $PCI_p$ | Product Complexity Index for product $p$ (time-invariant or slowly-moving) |
| $\phi_{cp,t}$ | Relatedness density of country $c$ to product $p$ in year $t$ |
| $Z_{ij,t}$ | Standard gravity bilateral controls (distance, language, colony, contiguity, FTA) |
| $\pi_{i,t}$ | Exporter x year fixed effect |
| $\chi_{j,t}$ | Importer x year fixed effect |
| $\mu_{ij}$ | Country-pair fixed effect |
| $\gamma_p$ | Product fixed effect |

### Specification 1: Baseline Structural Gravity (No Payment Frictions)

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \gamma_p + \beta_1 \ln \text{dist}_{ij} + \beta_2 \text{contig}_{ij} + \beta_3 \text{comlang}_{ij} + \beta_4 \text{colony}_{ij} + \beta_5 \text{FTA}_{ij,t}\right] \times \varepsilon_{ijp,t}$$

**Purpose:** Establish baseline gravity estimates. Confirm standard coefficients are sensible (distance negative, contiguity positive, etc.). This is the "does our data behave like trade data?" sanity check.

**Variation used:** Cross-sectional bilateral variation (no pair FEs yet).

### Specification 2: Payment Friction in Gravity (Average Effect)

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \gamma_p + \alpha_1 PF_{ij,t} + \beta Z_{ij} \right] \times \varepsilon_{ijp,t}$$

**Purpose:** Estimate the average trade effect of payment frictions across all products.

**Key coefficient:** $\alpha_1$ -- the semi-elasticity of trade with respect to payment frictions. Expected sign: negative (higher friction, less trade).

**Variation used:** Across-pair variation in payment friction levels, conditional on exporter x year and importer x year FEs (which absorb all unilateral determinants including GDP, financial development, institutions).

**Alternative with pair FEs:**

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \gamma_p + \mu_{ij} + \alpha_1 PF_{ij,t}\right] \times \varepsilon_{ijp,t}$$

With pair FEs, $\alpha_1$ is identified from within-pair time variation in payment frictions. This is the more demanding specification -- it asks "when a corridor's payment friction changes (e.g., due to de-risking), does trade respond?"

### Specification 3: The Key Interaction (Payment Friction x Product Complexity)

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \mu_{ij} + \gamma_p + \alpha_1 PF_{ij,t} + \alpha_2 (PF_{ij,t} \times PCI_p) \right] \times \varepsilon_{ijp,t}$$

**Purpose:** This is the paper's central specification. It tests whether payment frictions have heterogeneous effects across the product complexity distribution.

**Key coefficient:** $\alpha_2$ -- the differential effect. Expected sign: negative. Interpretation: a one-standard-deviation increase in payment friction reduces trade in a product at the 75th percentile of PCI by $|\alpha_2| \times (PCI_{75} - PCI_{25})$ more than a product at the 25th percentile.

**Identification:** Within country-pair, across-product variation. For a given corridor $i$-$j$ facing payment friction $PF_{ij,t}$, does the trade pattern tilt away from complex products? The pair FE absorbs the average level effect; the product FE absorbs the average complexity effect. The interaction is identified from the cross-product variation in friction sensitivity *within* corridors.

**Why this works:** Consider two country pairs, one with high payment friction (Nigeria-Brazil) and one with low (Germany-France). Both export both simple products (raw materials) and complex products (machinery). If payment frictions disproportionately suppress complex-product trade, then Nigeria-Brazil's export basket will be more concentrated in simple products than Germany-France's, *conditional on* the pair FEs and product FEs absorbing level differences.

**Enriched version with Rajan-Zingales horse race:**

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \mu_{ij} + \gamma_p + \alpha_1 PF_{ij,t} + \alpha_2 (PF_{ij,t} \times PCI_p) + \alpha_3 (PF_{ij,t} \times EFD_p)\right] \times \varepsilon_{ijp,t}$$

where $EFD_p$ is Rajan-Zingales external finance dependence mapped to HS products via ISIC concordance. This tests whether the complexity channel operates independently of the financial vulnerability channel.

### Specification 4: Extensive Margin (Diversification)

$$\Pr(RCA_{cp,t} \geq 1) = \Lambda\left[\delta_c + \delta_t + \beta_1 \phi_{cp,t} + \beta_2 PF_{c,t} + \beta_3 (\phi_{cp,t} \times PF_{c,t}) + \beta_4 X_{c,t}\right]$$

where:
- $RCA_{cp,t} \geq 1$ indicates country $c$ has revealed comparative advantage in product $p$ at time $t$
- $\phi_{cp,t}$ is relatedness density (how many "nearby" products in the product space does $c$ already export?)
- $PF_{c,t}$ is a country-level payment friction measure (since this is exporter-level, not bilateral)
- $\Lambda(\cdot)$ is the logistic function (logit) or identity (LPM)

**Purpose:** Test whether payment frictions impede product diversification, especially into products that are "close" in the product space (high relatedness density).

**Key coefficient:** $\beta_3$ -- the interaction. Expected sign: negative. Countries with high payment frictions are less able to diversify into nearby complex products.

**Note:** This specification uses country-level (not bilateral) payment friction because the unit of analysis is country x product, not exporter x importer x product.

---

## 4. Fixed Effects Structure

### 4.1 What Each FE Absorbs

| Fixed Effect | Absorbs | Needed For |
|-------------|---------|-----------|
| $\pi_{i,t}$ (exporter x year) | Outward multilateral resistance, GDP, financial development, institutions, all time-varying exporter characteristics | Structural gravity consistency (Anderson & van Wincoop 2003) |
| $\chi_{j,t}$ (importer x year) | Inward multilateral resistance, GDP, demand shocks, all time-varying importer characteristics | Structural gravity consistency |
| $\gamma_p$ (product) | Average trade level by product, product-specific factors (weight, perishability, etc.) | Absorbs PCI level effect; interaction still identified |
| $\mu_{ij}$ (country-pair) | Time-invariant bilateral factors: distance, language, colony, contiguity, historical ties | Absorbs all cross-sectional bilateral confounders; only within-pair time variation identifies $\alpha_1$ |

### 4.2 What Variation Identifies What

| Coefficient | Variation Used | FE Structure Required |
|-------------|---------------|----------------------|
| $\alpha_1$ (PF level effect, no pair FE) | Cross-sectional: high-friction vs. low-friction corridors | Exporter x year, importer x year, product |
| $\alpha_1$ (PF level effect, with pair FE) | Within-pair temporal: corridor friction changes over time | Exporter x year, importer x year, product, pair |
| $\alpha_2$ (PF x PCI interaction) | Within-pair, cross-product: does the product mix shift toward simplicity when friction is high? | Exporter x year, importer x year, product, pair |
| $\beta_3$ (extensive margin interaction) | Within-country, cross-product: which products does a high-friction country NOT export? | Country, year |

### 4.3 The Identification Sweet Spot

The interaction coefficient $\alpha_2$ survives the most demanding FE structure (exporter x year + importer x year + pair + product). This is because it exploits variation in *two dimensions simultaneously*: across products (complexity) and across pairs (friction). Neither the pair FE (which is product-invariant) nor the product FE (which is pair-invariant) absorbs this interaction.

### 4.4 Computational Considerations

With ~5,200 HS12 6-digit products, ~200 exporters, ~200 importers, and 9 years:
- Exporter x year: ~1,800 FEs
- Importer x year: ~1,800 FEs
- Products: ~5,200 FEs
- Pairs: ~20,000+ FEs (active trade pairs)
- Observations: potentially 5,200 x 20,000 x 9 = 936 million

This is computationally infeasible at the full product-pair-year level. **Aggregation strategy:**

1. **Primary:** Aggregate to HS12 4-digit (~1,200 products) or 2-digit (~97 chapters)
2. **Alternative:** Estimate at 6-digit but restrict to a subsample of high-trade corridors
3. **Alternative:** Use the `fixest` package in R, which handles high-dimensional FEs efficiently via demeaning

**Recommendation:** Lead with HS12 4-digit (manageable, retains product-level complexity variation). Robustness at 2-digit and 6-digit (subsample).

---

## 5. Identification Assumptions

### 5.1 For Specification 2 (Average Payment Friction Effect, no pair FEs)

**Assumption:** Conditional on exporter x year and importer x year FEs, payment frictions $PF_{ij,t}$ are uncorrelated with unobserved bilateral trade costs.

**Threat:** Bilateral trade infrastructure (including payment systems) is jointly determined with trade volumes. High-trade corridors invest in payment infrastructure; low-trade corridors do not. This is *classic* simultaneity.

**Mitigation:** Exporter x year and importer x year FEs absorb all unilateral determinants. The remaining confounders must be bilateral and time-varying. Bilateral controls (FTA, colonial ties) address some, but the concern remains that bilateral payment friction is endogenous to bilateral trade.

**Assessment:** This assumption is strong. We present Specification 2 as descriptive, not our primary causal result.

### 5.2 For Specification 3 (Interaction, with pair FEs)

**Assumption:** Conditional on the full FE structure (exporter x year, importer x year, pair, product), the interaction $PF_{ij,t} \times PCI_p$ is uncorrelated with unobserved determinants of product-level bilateral trade.

**What could violate this?** A confounder would need to:
1. Vary at the corridor x product level
2. Correlate with both payment friction and product complexity
3. Not be absorbed by the FEs

**Candidate confounders:**
- **Product-specific trade costs correlated with PCI:** e.g., complex products require more customs documentation, and corridors with high payment friction also have worse customs. The Doing Business "Trading Across Borders" score is a control for this.
- **Product-specific credit constraints:** Complex products require more trade finance (Manova 2013). Payment friction may proxy for financial underdevelopment more broadly. The Rajan-Zingales horse race (Specification 3, enriched version) addresses this directly.
- **Tariff structure:** If high-friction corridors also have higher tariffs on complex products, the interaction is confounded. Including product x pair tariff data (from WITS/TRAINS) would address this, though data burden is high.

**Assessment:** The interaction is identified from within-pair cross-product variation, which is much more credible than the level effect. The key remaining threat is that something other than payment friction varies at the corridor-product level and correlates with PCI. The Rajan-Zingales horse race and the falsification tests (Section 9) are designed to address this.

### 5.3 For the Extensive Margin (Specification 4)

**Assumption:** Conditional on country and year FEs, payment frictions do not affect the probability of exporting product $p$ through channels other than the payment friction mechanism.

**Threat:** Country-level payment friction proxies for general institutional quality. A country with poor payment infrastructure also has poor contract enforcement, logistics, etc.

**Mitigation:** Include WGI Rule of Law, logistics performance, and other institutional controls. But this is inherently weaker than the intensive margin identification because we lose the bilateral dimension.

**Assessment:** The extensive margin results are supportive, not the primary identification.

---

## 6. Endogeneity Strategy

### 6.1 Primary: Structural Gravity Fixed Effects

The first line of defense is the structural gravity FE structure itself. Exporter x year and importer x year FEs absorb *all* unilateral determinants of trade, including:
- GDP, population, financial development
- Institutional quality, governance
- Aggregate stablecoin/crypto adoption
- Domestic payment infrastructure quality
- All other time-varying country characteristics

This means the only remaining endogeneity concern is at the *bilateral* level: does bilateral payment friction respond to bilateral trade?

With pair FEs added, only *within-pair temporal variation* in payment friction identifies the level effect. This is more demanding but also more credible: it asks "when this specific corridor experiences a change in payment friction, does trade respond?"

**Strengths:** Theory-consistent, standard in the literature, absorbs a large class of confounders.
**Limitations:** Cannot address bilateral reverse causality within corridor over time.

### 6.2 Secondary: Lagged Payment Frictions

Use $PF_{ij,t-1}$ or $PF_{ij,t-2}$ instead of $PF_{ij,t}$.

**Rationale:** If trade in year $t$ causes payment infrastructure improvement in year $t$, using lagged friction avoids this simultaneity.

**Strengths:** Simple, easy to implement, standard robustness check.
**Limitations:** (a) Only addresses contemporaneous reverse causality, not feedback loops where past trade affects payment infrastructure which affects future trade. (b) Reduces sample by 1-2 years.

### 6.3 Tertiary: Instrumental Variable -- De-Risking Shocks

Following Borchert et al. (2024), use **regulatory-driven de-risking events** as instruments for payment friction.

**Instrument construction:**
- Identify corridors where global banks withdrew correspondent banking relationships due to AML/CFT compliance concerns (not due to declining trade volumes)
- Use the BIS/CPMI data to identify corridors with large drops in correspondent banking density
- Focus on "push-factor" de-risking: driven by global bank compliance decisions, not by trade conditions in the corridor

**First stage:** De-risking event -> increase in payment friction (loss of correspondent banking)
**Second stage:** Instrumented payment friction -> trade

**Exclusion restriction:** De-risking by global banks is driven by regulatory compliance costs and perceived AML/CFT risk in the destination country, not by bilateral trade conditions. This is plausible for regulatory-driven withdrawals (e.g., HSBC exiting correspondent banking in the Pacific Islands due to global compliance strategy), less plausible for voluntary commercial exits.

**Strengths:** Addresses bilateral endogeneity directly. Borchert et al. (2024) have established the first-stage relationship.
**Limitations:** (a) De-risking is concentrated in specific regions (Pacific Islands, Caribbean, parts of Africa) -- results may not generalize. (b) De-risking may affect trade through channels other than payment friction (e.g., signaling country risk). (c) First stage may be weak for corridors with multiple correspondent banks. (d) Data requirements are substantial -- constructing a corridor-level de-risking indicator from BIS/CPMI data is non-trivial.

**Recommendation:** Present IV as a robustness check, not the primary specification. The reduced form (de-risking -> trade) is more credible than the IV (de-risking -> friction -> trade) because it doesn't require the exclusion restriction.

### 6.4 Supportive: Reduced Form (De-Risking -> Trade, by Product Complexity)

$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \mu_{ij} + \gamma_p + \alpha_1 \text{DeRisk}_{ij,t} + \alpha_2 (\text{DeRisk}_{ij,t} \times PCI_p)\right] \times \varepsilon_{ijp,t}$$

where $\text{DeRisk}_{ij,t}$ is a binary indicator for corridors that experienced major correspondent banking loss.

**Interpretation:** Does de-risking disproportionately reduce trade in complex products? If $\alpha_2 < 0$, this is consistent with the payment-friction-complexity channel *without* requiring the exclusion restriction.

**This may be the paper's cleanest causal result** and deserves prominence.

---

## 7. Stablecoin Opportunity Score (SOS) Construction

### 7.1 Conceptual Framework

The SOS combines three inputs:

1. **Gravity estimates:** How much does payment friction suppress trade, especially in complex products? (From beta-hat in Specification 3)
2. **Product complexity:** Which products have high PCI? (From the complexity computation)
3. **Relatedness density:** Which country x product cells are close to existing capabilities? (From the product space)

### 7.2 Intensive Margin SOS

For each country $c$, product $p$, and partner $j$:

$$SOS^{intensive}_{cjp} = \hat{\alpha}_2 \times PCI_p \times \overline{PF}_{cj}$$

This gives the predicted trade increase from eliminating payment friction in corridor $c$-$j$ for product $p$. Aggregate over partners:

$$SOS^{intensive}_{cp} = \sum_j \hat{\alpha}_2 \times PCI_p \times \overline{PF}_{cj} \times X_{cjp,T}$$

where $X_{cjp,T}$ is current trade (weights the corridor by importance).

### 7.3 Extensive Margin SOS

For each country $c$ and product $p$ that $c$ does NOT currently export (RCA < 1):

$$SOS^{extensive}_{cp} = \hat{\beta}_3 \times \phi_{cp,T} \times PF_{c,T} \times PCI_p$$

This predicts how much more likely country $c$ would be to develop RCA in product $p$ if payment frictions were removed, weighted by both the product's complexity and the country's relatedness to it.

### 7.4 Combined SOS

$$SOS_{cp} = \omega \cdot SOS^{intensive}_{cp} + (1 - \omega) \cdot SOS^{extensive}_{cp}$$

where $\omega$ is a weighting parameter (report results for $\omega = 0.5$ and for each margin separately).

### 7.5 Aggregation

- **Country-level SOS:** $SOS_c = \sum_p SOS_{cp}$ -- which countries have the most stablecoin opportunity?
- **Product-level SOS:** $SOS_p = \sum_c SOS_{cp}$ -- which products would benefit most from stablecoin adoption?
- **Country x product heat map:** The full matrix for visualization.

### 7.6 Validation

Correlate $SOS_c$ with:
1. Chainalysis Global Crypto Adoption Index rankings (primary)
2. Google Trends for "USDT" by country (secondary)
3. Partial correlation: $\text{corr}(SOS_c, \text{Chainalysis}_c | \text{GDPpc}_c)$ -- controlling for income

Expected: positive correlation. Countries where our model predicts high stablecoin opportunity should also show high observed crypto adoption, even after conditioning on income.

---

## 7B. Feasibility Quadrant: From Economic Potential to Policy Actionability

### 7B.1 Motivation

The SOS answers "where would stablecoins matter most for trade?" -- a question about economic potential. But potential is not the same as implementability. A country may rank high on SOS yet lack the infrastructure or legal environment to actually adopt stablecoin-based payments. The Feasibility Quadrant separates opportunity from actionability by classifying countries along two dimensions:

1. **On/off ramp availability:** Do established channels exist for converting local currency to stablecoins and back?
2. **Capital account openness:** Does the regulatory environment permit stablecoin-based cross-border payments?

### 7B.2 The Four Quadrants

|  | **Open Capital Account** | **Restricted Capital Account** |
|--|--------------------------|-------------------------------|
| **On/Off Ramps Exist** | **Q1: Actionable Now.** SOS translates directly into policy. Stablecoin firms can enter, firms can adopt, gains are realizable. These are the low-hanging fruit for stablecoin-based trade payment pilots. | **Q3: Legal Complexity.** Infrastructure exists but usage may conflict with capital controls. Stablecoins risk being used to circumvent restrictions, which is exactly what regulators fear. Case-by-case legal analysis required. Policy recommendation: regulatory sandboxes for trade-related stablecoin payments, ring-fenced from capital account transactions. |
| **No On/Off Ramps** | **Q2: Infrastructure Gap.** The economics work, the law permits it, but local exchange infrastructure is absent. This is an anomaly -- the market should have provided on-ramps here. Possible explanations: coordination failure (exchanges need liquidity to attract users, users need exchanges), regulatory ambiguity (not prohibited but not explicitly permitted), banking sector resistance (local banks refuse to serve crypto exchanges), or small market size. Policy recommendation: development finance institutions and stablecoin firms should prioritize exchange infrastructure investment in Q2 countries. | **Q4: Structurally Blocked.** Neither infrastructure nor legal environment supports stablecoin adoption. SOS remains theoretical. These countries need broader institutional and regulatory reform before stablecoins become relevant. Policy recommendation: focus on traditional payment infrastructure improvement (correspondent banking, regional payment systems). |

### 7B.3 Measurement

#### Capital Account Openness (Column Dimension)

**Primary measure:** Chinn-Ito KAOPEN index (182 countries, 1970-2023).

KAOPEN measures de jure capital account openness based on IMF AREAER binary indicators. Higher values indicate more open capital accounts.

**Classification:** Countries above the global median KAOPEN are classified as "open"; below as "restricted." Robustness: use terciles (open / intermediate / restricted) and continuous KAOPEN.

**Refinement:** KAOPEN captures aggregate capital account openness, but stablecoin-relevant restrictions may be narrower. Where available, use the IMF AREAER's specific indicators for restrictions on payments for current transactions (as opposed to capital account transactions). Trade-related payments are current account items under IMF Article VIII -- many countries that restrict capital flows freely permit current account payments. This distinction matters: a country with closed capital account but open current account is more hospitable to trade-related stablecoin payments than raw KAOPEN suggests.

#### On/Off Ramp Availability (Row Dimension)

No single authoritative dataset exists. We construct a proxy and validate with alternatives.

**Primary measure: Google Trends for "buy USDT" / "buy USDC" (by country, annual average).**

Rationale:
- Behavioral demand signal, stablecoin-specific (not general crypto)
- Available for nearly every country, at monthly frequency
- Not mechanically correlated with payment friction measures (no circularity)
- Transparent and fully replicable
- Conservative: noisy signal means results are biased toward null

Construction:
- Query Google Trends for "buy USDT" and "buy USDC" by country
- Use annual average of monthly search intensity index (0-100)
- Normalize by internet penetration (World Bank WDI) to avoid confounding internet access with stablecoin demand
- Multi-language queries where Google market share is low (construct queries in major local languages for top-20 non-English-speaking countries)

Classification: Countries above median normalized search intensity are classified as "ramps exist" (demand is present and likely served); below as "no ramps." Robustness with terciles and continuous measure.

**Robustness measures (ordered):**

| # | Measure | What It Captures | Source | Coverage |
|---|---------|-----------------|--------|----------|
| R1 | Chainalysis Global Crypto Adoption Index | Composite: on-chain volume (PPP-weighted), DeFi, P2P, centralized exchange activity | Chainalysis annual report | 151 countries |
| R2 | Number of licensed crypto exchanges per jurisdiction | Institutional supply of on/off ramps | CoinGecko/CoinMarketCap exchange listings, cross-referenced with regulatory filings | ~100 countries (manual construction) |
| R3 | P2P trading volume (Binance P2P, historical Paxful/LocalBitcoins) | Informal/grassroots on-ramp activity; signals demand where formal infrastructure is absent | Platform data (scraped or from academic datasets) | ~80 countries (data availability fragile) |

Each robustness measure has known limitations:
- Chainalysis is PPP-weighted (confounded with income) and captures all crypto, not stablecoins specifically
- Exchange counts conflate jurisdiction of registration with jurisdiction of operation; a Seychelles-registered exchange serving global users does not indicate Seychellois on-ramp availability
- P2P volume is endogenous to the same conditions that create high payment friction, and covers retail transactions poorly suited for B2B trade payments

### 7B.4 Integration with SOS

The Feasibility Quadrant operates as a **policy overlay**, not as an input to the gravity estimation. The causal estimates ($\hat{\alpha}_2$, $\hat{\beta}_3$) and the raw SOS rankings are computed on the full sample regardless of quadrant position. The quadrant then filters the SOS for policy interpretation:

**Feasibility-Adjusted SOS:**

$$SOS^{adj}_c = SOS_c \times \mathbb{1}[\text{Quadrant}(c)]$$

where the indicator function flags the quadrant for policy routing, not for rescaling. We do NOT multiply the SOS by a feasibility weight -- that would mix causal estimates with implementation judgment. Instead, we present:

1. **Raw SOS rankings** (Table X): economic potential, all countries
2. **SOS by quadrant** (Table X+1): same rankings, partitioned into four groups with distinct policy recommendations
3. **Top-20 actionable opportunities** (Table X+2): highest-SOS countries in Q1 only -- these are the immediately implementable recommendations

### 7B.5 Predictive Validity Test: Does SOS Predict Future On/Off Ramp Development?

The quadrant classification is not static. If the SOS captures genuine economic opportunity, countries with high SOS should attract on/off ramp infrastructure over time -- the market should respond to profit opportunities.

**Test:** Do countries with high $SOS_c$ computed from early-panel data (2015-2017) develop better on/off ramp availability by 2023?

$$\text{OnOffRamp}_{c,2023} = \gamma_0 + \gamma_1 SOS_{c,2015\text{-}17} + \gamma_2 \text{GDPpc}_{c,2015} + \gamma_3 X_{c,2015} + \varepsilon_c$$

where $\text{OnOffRamp}_{c,2023}$ is one of our four measures of on/off ramp availability, and controls include baseline GDP per capita, institutional quality, internet penetration, and baseline crypto adoption (if available).

**Expected:** $\gamma_1 > 0$. Countries where our model predicts high stablecoin opportunity in the base period should exhibit higher on/off ramp development by end-of-sample. This result would:
- Validate the SOS as capturing genuine economic forces (markets respond to the opportunities the model identifies)
- Distinguish SOS from a pure income proxy (controlling for GDP per capita)
- Provide a theory consistency check: if payment frictions suppress complex-product trade and stablecoins reduce those frictions, then countries with the most to gain should be the ones where stablecoin infrastructure emerges

**Interpretation if $\gamma_1 = 0$:** Either the SOS does not capture genuine opportunity (concerning), or market failures prevent on-ramp development even where opportunity exists (the Q2 anomaly, which is itself an interesting finding for policy).

### 7B.6 Quadrant-Specific Policy Recommendations

| Quadrant | Policy Target | Recommendation |
|----------|--------------|----------------|
| Q1 (Ramps + Open) | Stablecoin firms, trade ministries, central banks | Pilot trade payment corridors using stablecoins. Integrate with existing trade finance platforms. Regulatory clarity on stablecoin payment status. |
| Q2 (No Ramps + Open) | Development finance institutions, fintech investors | Invest in local exchange infrastructure. Investigate barriers to market entry (banking sector resistance, regulatory ambiguity). Public-private partnership for on-ramp provision. |
| Q3 (Ramps + Controls) | Financial regulators, central banks | Design regulatory sandboxes for trade-related stablecoin payments, ring-fenced from capital account transactions. Distinguish current account payments (IMF Article VIII) from capital flows. |
| Q4 (No Ramps + Controls) | International organizations, reform advocates | Broader institutional reform is the binding constraint. Traditional payment infrastructure (regional payment systems, correspondent banking restoration) may be more effective than stablecoin adoption. |

---

## 8. Robustness Plan

| # | Check | Rationale | Expected Finding |
|---|-------|-----------|-----------------|
| 1 | Lagged payment frictions ($t-1$, $t-2$) | Address contemporaneous reverse causality | Coefficients stable or larger (attenuation bias from measurement error in contemporaneous friction) |
| 2 | IV using de-risking shocks | Address bilateral endogeneity | Larger coefficients (OLS biased toward zero if high-trade corridors have better infrastructure) |
| 3 | Reduced form: de-risking x PCI interaction | Cleaner causal test without exclusion restriction | Negative coefficient -- de-risking hurts complex products more |
| 4 | RCA threshold sensitivity (0.5, 1.0, 2.0) | Extensive margin sensitivity to threshold choice | Qualitatively similar results |
| 5 | Alternative complexity: Method of Reflections vs. eigenvalue method | Robustness to PCI computation method | Correlation between methods is high (>0.9); results should be similar |
| 6 | Alternative friction: correspondent banking only vs. RPW only vs. combined | Robustness to friction measure choice | All measures should show negative interaction with PCI |
| 7 | HS12 4-digit vs. HS12 2-digit vs. HS12 6-digit (subsample) | Robustness to product aggregation level | Coefficients should be qualitatively similar; precision may vary |
| 8 | Subsample by income group (LIC, LMIC, UMIC, HIC) | Check whether results are driven by specific income groups | Expect stronger effects for LIC/LMIC where payment frictions are more binding |
| 9 | Excluding entrepot economies (Singapore, Hong Kong, UAE, Netherlands) | Re-export trade may distort complexity measures | Results should survive; possibly sharper |
| 10 | Rajan-Zingales horse race: PF x PCI vs. PF x EFD | Distinguish complexity from financial vulnerability | Both may matter; PCI should remain significant after controlling for EFD |
| 11 | Panel window: 2015-2019 vs. 2015-2023 vs. 2017-2023 | Robustness to time period; pre/post-COVID | Expect weaker effects in COVID-disrupted 2020-2021 |
| 12 | Weighted vs. unweighted PPML | PPML implicitly weights by trade volume | Unweighted may give different point estimates; qualitative results should hold |
| 13 | OLS on log(1+X) instead of PPML | Standard robustness (though PPML is preferred) | Similar signs; magnitudes may differ due to Jensen's inequality |
| 14 | Adding tariff controls (product x pair level from TRAINS) | Rule out tariff-driven confounding of the interaction | Interaction coefficient should be robust to tariff controls |
| 15 | Excluding primary commodities (HS chapters 1-27) | Commodity trade driven by resource endowment, not payment infrastructure | Interaction should strengthen (commodities are low-PCI and less friction-sensitive) |
| 16 | Estimate $\alpha_2$ separately by feasibility quadrant (Q1-Q4) | Check whether the PF x PCI interaction varies by on/off ramp availability and capital account openness | $\alpha_2$ should be similar across quadrants (the economic mechanism does not depend on stablecoin availability); if stronger in Q1, stablecoin adoption may already be partially reducing frictions |
| 17 | Alternative on/off ramp measures: Chainalysis, licensed exchanges, P2P volume | Robustness of quadrant classification to measurement choice | Quadrant assignments should be broadly stable; countries switching quadrants under alternative measures should be discussed |
| 18 | KAOPEN refinement: use AREAER current-account-specific restrictions instead of aggregate KAOPEN | Distinguish countries that restrict capital flows but permit trade-related payments | Some countries may shift from Q3/Q4 to Q1/Q2, changing the feasibility assessment |
| 19 | SOS predictive validity: does early-period SOS (2015-2017) predict on/off ramp development by 2023? | Theory consistency test -- markets should respond to stablecoin opportunity | $\gamma_1 > 0$ conditional on GDP per capita and baseline crypto adoption |

---

## 9. Falsification Tests

### 9.1 Placebo Interactions

**Test 1: Payment Friction x Product Weight**

Interact payment friction with average product weight (kg per dollar of trade). Payment frictions should NOT disproportionately reduce trade in heavy products -- weight is a logistics friction, not a payment friction. If $PF \times \text{Weight}$ is significant, it suggests our PCI interaction is picking up general trade costs, not payment-specific costs.

**Expected:** Null coefficient on PF x Weight.

**Test 2: Payment Friction x Product Perishability**

Similarly, interact payment friction with a perishability indicator (HS chapters for food/agriculture). Payment frictions should not differentially affect perishable goods.

**Expected:** Null or weak coefficient.

### 9.2 Placebo Friction Measures

**Test 3: Geographic Distance x PCI**

Replace payment friction with geographic distance in the interaction. Distance affects all products roughly equally (modulo weight). If Distance x PCI is also strongly negative, our finding is not payment-specific.

**Expected:** Distance x PCI should be much weaker than PayFriction x PCI. Distance affects trade levels but should not differentially penalize complex products (which are often high-value-to-weight).

**Test 4: Language Barrier x PCI**

Common language should facilitate trade but not differentially for complex products through a payment channel.

**Expected:** Null or weak coefficient on Language x PCI.

### 9.3 Placebo Outcomes

**Test 5: SOS Should NOT Predict Non-Payment Technology Adoption**

If our SOS truly captures payment-specific opportunity, it should not predict adoption of unrelated technologies (e.g., renewable energy installations, mobile phone penetration). Correlate SOS with non-payment outcomes conditional on GDP per capita.

**Expected:** Null correlation.

### 9.4 Temporal Placebo

**Test 6: Pre-Trends in Panel Specification**

In the pair-FE specification with time-varying payment friction: check whether future friction changes "predict" current trade. Estimate leads of payment friction ($PF_{ij,t+1}$, $PF_{ij,t+2}$). If significant, there is reverse causality concern.

**Expected:** Null coefficients on leads.

### 9.5 Subsample Falsification

**Test 7: Commodity-Only Subsample**

Restrict to HS chapters 1-27 (primary commodities). These have low PCI and trade through established commodity channels with less sensitivity to payment friction. The PF x PCI interaction should be weak or absent in this subsample.

**Expected:** Null or small interaction coefficient in commodity subsample.

---

## 10. Referee Objection Anticipation

### Objection 1: "Payment friction is endogenous to trade volumes."

**Attack:** Countries that trade more invest in payment infrastructure. Your coefficient is biased.

**Response:**
- (a) The *level* effect is indeed vulnerable to this concern. We present it as descriptive.
- (b) The *interaction* (PF x PCI) is identified from within-pair cross-product variation. For this to be confounded, an unobserved variable would need to vary at the corridor-product level and correlate with both friction and complexity. We discuss candidates and rule them out with the Rajan-Zingales horse race and falsification tests.
- (c) We present three robustness strategies: lagged frictions, IV (de-risking), and reduced form. All yield consistent results.
- (d) If anything, endogeneity biases the level effect *toward zero* (high-trade corridors have better infrastructure), so our estimates are conservative.

### Objection 2: "Product complexity is just a proxy for capital intensity or financial vulnerability."

**Attack:** Manova (2013) already showed that financially vulnerable industries trade less under financial frictions. You are rediscovering this with a different variable label.

**Response:**
- (a) We run a direct horse race: PF x PCI vs. PF x EFD (Rajan-Zingales) in the same specification. Both may matter, but we show PCI captures something beyond EFD.
- (b) PCI captures the knowledge/capability dimension of products, not just their financing needs. Complex products require not only trade finance but also verified quality, reputational capital, and repeat transactions -- all of which are facilitated by reliable payment infrastructure.
- (c) The correlation between PCI and EFD is imperfect (~0.4), so they capture different dimensions.

### Objection 3: "Remittance costs are not trade payment costs."

**Attack:** RPW measures P2P retail transfer fees. B2B trade payments use completely different instruments (LCs, documentary collections, open account).

**Response:**
- (a) We agree. This is why our primary friction measure is BIS/CPMI correspondent banking density, which directly measures the infrastructure underlying B2B trade payments.
- (b) RPW is a secondary proxy, used because it captures the "access" dimension: countries with high remittance costs also tend to have poor trade payment infrastructure.
- (c) We show that results hold using correspondent banking density alone, without RPW.
- (d) The correlation between RPW costs and correspondent banking density is documented and the mechanism discussed.

### Objection 4: "The SOS is just a complicated way of saying poor countries with complex export potential would benefit from better infrastructure."

**Attack:** Your rankings are driven by income, not payment-specific opportunity.

**Response:**
- (a) We validate SOS conditional on GDP per capita. If SOS predicted adoption only through income, the partial correlation would be zero.
- (b) We show within-income-group variation: among LMIC countries, which ones have high SOS? This is informative because it highlights payment-specific barriers, not general development.
- (c) The SOS incorporates the *interaction* estimate, not just friction levels. A country with high friction but no complex-product export potential has low SOS. The ranking is driven by the intersection of high friction AND high complexity potential.

### Objection 5: "Your paper is descriptive, not causal. The SOS is a prediction, not a treatment effect."

**Attack:** You estimate a gravity model, compute some scores, and call it an "opportunity map." Where is the causal identification?

**Response:**
- (a) We are transparent about the two-part structure. The gravity estimates *are* causal (under structural gravity assumptions with robustness to IV). The SOS is a policy-relevant prediction exercise that uses causal estimates as inputs.
- (b) The causal contribution is the interaction coefficient: payment frictions disproportionately suppress complex-product trade. This is a testable, falsifiable, causal claim.
- (c) The SOS adds value by translating the causal estimate into actionable rankings. This is analogous to how structural trade models estimate elasticities and then simulate counterfactual trade policies.
- (d) The reduced-form de-risking result (Specification 6.4) provides clean causal evidence without any structural assumptions.

---

## 11. Estimation Approach

### 11.1 Software

| Task | Package | Language |
|------|---------|----------|
| PPML gravity estimation | `fixest` | R |
| High-dimensional FEs | `fixest` (Berge 2018) | R |
| Economic complexity computation | `economiccomplexity` | R |
| Data manipulation | `data.table` + `arrow` (for Parquet) | R |
| Extensive margin (logit/LPM) | `fixest::feglm` or `fixest::feols` | R |
| Visualization (product space) | `ggraph` + `igraph` | R |
| Robustness tables | `modelsummary` + `kableExtra` | R |

### 11.2 Recommended Estimator

**Primary:** `fixest::fepois()` for PPML with high-dimensional fixed effects.

```r
# Specification 3 (key specification)
model_key <- fepois(
  trade_value ~ pay_friction:pci |
    exporter^year + importer^year + pair + product,
  data = panel,
  cluster = ~ pair
)
```

### 11.3 Clustering

**Primary:** Cluster at the country-pair level (Head and Mayer 2014 recommendation).

**Robustness:** Multi-way clustering at exporter x importer level (Cameron, Gelbach, Miller 2011). Also report pair x product clustering if computationally feasible.

### 11.4 Sample Restrictions

| Restriction | Rationale |
|------------|-----------|
| Drop product-pair-years where $X_{ijp,t} = 0$ for all $t$ | Never-traded pairs have no variation for pair FEs |
| Drop pairs with fewer than 3 years of positive trade | Insufficient within-pair variation |
| Drop HS chapters 93 (arms), 97-99 (special transactions) | Non-standard trade |
| Keep zeros within active pairs | PPML handles zeros; essential for extensive margin |

### 11.5 Variable Construction

**Correspondent Banking Density (Primary Friction):**
- $CBR_{ij,t}$ = number of active correspondent banking relationships between country $i$ and country $j$ in year $t$
- Normalize: $PF^{CBR}_{ij,t} = -\ln(1 + CBR_{ij,t})$ so higher values = higher friction (fewer correspondents)

**RPW Remittance Cost (Secondary Friction):**
- $RPW_{ij,t}$ = average total cost of sending USD 200 from $i$ to $j$ in year $t$ (% of principal)
- Already in friction-increasing direction

**Product Complexity Index:**
- Compute from BACI using `economiccomplexity` package
- Eigenvalue method (Hausmann et al. 2014 Atlas) as primary
- Method of Reflections (Hidalgo and Hausmann 2009) as robustness
- Standardize to mean 0, SD 1 for interpretation of interaction coefficients

**Relatedness Density:**
- $\phi_{cp,t} = \frac{\sum_{p' \neq p} \text{proximity}(p, p') \times \mathbb{1}(RCA_{cp',t} \geq 1)}{\sum_{p' \neq p} \text{proximity}(p, p')}$

---

## 12. Summary of Empirical Architecture

```
                        INTENSIVE MARGIN (Bilateral)
                        ============================
Data:       BACI (HS12 4-digit) x CEPII Gravity x BIS/CPMI x RPW
Unit:       exporter i x importer j x product p x year t
FEs:        exporter x year, importer x year, pair, product
Key coeff:  alpha_2 on PayFriction x PCI
Estimator:  PPML (fixest::fepois)
Clustering: country-pair
Panel:      2015-2023 (9 years)

                        EXTENSIVE MARGIN (Country x Product)
                        ====================================
Data:       BACI (RCA computation) x complexity x FAS/KAOPEN
Unit:       country c x product p x year t
Dep var:    1(RCA >= 1)
Key coeff:  beta_3 on Density x PayFriction
Estimator:  LPM or Logit (fixest::feols or feglm)
Clustering: country
Panel:      2015-2023

                        SOS CONSTRUCTION
                        ================
Input:      alpha_2-hat, beta_3-hat, PCI, Density, PayFriction
Output:     SOS_{cp} for all country x product cells
Validation: Rank correlation with Chainalysis | GDP per capita
```

---

## 13. Paper Section Structure

### Narrative Arc

The paper has three movements:

1. **"Payment frictions suppress complex-product trade."** (Sections 1-6) — the causal contribution
2. **"Here's where the suppressed trade is largest."** (Section 7) — the predictive/descriptive contribution
3. **"Here's where stablecoins can actually fix it."** (Section 8) — the policy contribution

### Section Outline

| Section | Title | Content | Est. Pages |
|---------|-------|---------|------------|
| 1 | Introduction | Gap, three contributions, preview of results | 3-4 |
| 2 | Conceptual Framework | Payment friction stack (7 layers, which stablecoins address vs. don't). Product complexity: why complex products need reliable payments. Feasibility quadrant as logical framework (introduced here, operationalized in Section 8). | 3-4 |
| 3 | Data | BACI, CEPII Gravity, BIS/CPMI, RPW, complexity computation (ECI/PCI/proximity from BACI), on/off ramp measures (Google Trends primary), KAOPEN. Coverage intersection analysis. | 3-4 |
| 4 | Empirical Strategy | Structural gravity with interactions (Specs 1-4). FE structure. Identification assumptions. Endogeneity strategy (FEs → lags → reduced form → IV). | 3-4 |
| 5 | Results: Payment Frictions and Complex-Product Trade | Specs 1-3 (baseline → friction → interaction). De-risking reduced form. Rajan-Zingales and Nunn horse races. | 5-6 |
| 6 | Results: Extensive Margin and Diversification | Spec 4. Payment frictions block diversification into nearby complex products. | 2-3 |
| 7 | The Stablecoin Opportunity Score | SOS construction (intensive + extensive). Country × product rankings. Validation against Chainalysis conditional on income. Uncertainty quantification. | 3-4 |
| 8 | From Opportunity to Feasibility | Feasibility quadrant operationalized. Country classification (Q1-Q4). SOS by quadrant. Top-20 actionable opportunities. Predictive validity test (early SOS → future ramp development). Quadrant-specific policy recommendations. | 3-4 |
| 9 | Robustness and Falsification | Robustness battery (19 checks). Falsification tests (7 tests). Specification curve or coefficient stability plot. | 3-4 |
| 10 | Conclusion | Summary, limitations, policy implications by quadrant, future research. | 2 |

**Total:** ~30-35 pages + tables/figures.

### Section 2 Detailed Outline: Conceptual Framework

**2.1 The Payment Friction Stack**

Decompose cross-border B2B payments into seven friction layers:
- Layer 1: Messaging (SWIFT, coordination)
- Layer 2: Clearing (netting, batching)
- Layer 3: Settlement (correspondent banking chain, speed, cost)
- Layer 4: FX conversion (vehicle currency, spreads)
- Layer 5: Compliance (KYC/AML, sanctions screening, de-risking)
- Layer 6: Trade finance (letters of credit, insurance, counterparty trust)
- Layer 7: Capital controls (sovereign policy, regulatory restrictions)

**2.2 What Stablecoins Can and Cannot Fix**

Map each layer to stablecoin capability:
- CAN reduce: Settlement (Layer 3), FX conversion partially (Layer 4), Access restoration in de-risked corridors (Layer 5 consequence)
- CANNOT reduce: Compliance obligations (Layer 5), Trade finance (Layer 6), Capital controls (Layer 7), On/off ramp frictions (meta-friction)
- Key implication: our friction measures (correspondent banking density, RPW) capture Layers 3-4 — precisely the frictions stablecoins address. This alignment is a feature, not an accident.

**2.3 Why Complex Products Are More Payment-Sensitive**

Draw on Hausmann-Hidalgo:
- Complex products (high PCI) require more capabilities → more supplier relationships → more transaction cycles → more payments per unit of trade
- Complex products are relationship-specific (Nunn 2007) → require repeated, trusted payment flows
- Complex products involve staged production and quality verification → payment must be reliable and timely
- Commodities trade through established exchanges with deep financial infrastructure → payment friction is less binding
- Testable prediction: α₂ < 0 (payment frictions suppress complex-product trade more than simple-product trade)

**2.4 The Extensive Margin: Payment Frictions as a Diversification Barrier**

Draw on Product Space:
- Countries diversify into nearby products (high relatedness density)
- But the jump requires building new supplier relationships, establishing quality credentials, integrating into value chains — all requiring reliable payments
- Payment frictions can block diversification even when capability prerequisites (relatedness density) are met
- Testable prediction: β₃ < 0 (payment frictions reduce diversification probability, especially for nearby products)

**2.5 The Feasibility Quadrant**

Introduce the 2×2 framework (on/off ramp × capital controls) as a logical device:
- Distinguish economic opportunity (SOS) from implementation feasibility
- Preview the four quadrants and their policy implications
- Note that the quadrant is endogenous to SOS itself (Q2 anomaly is theoretically interesting)
- Defer operationalization to Section 8

### Contribution Statement (Updated)

> This paper makes three contributions. First, we integrate the economic complexity framework (Hidalgo & Hausmann, 2009) with a structural gravity model to show that payment frictions disproportionately reduce trade in complex products — the products that matter most for economic development. Second, we develop a Stablecoin Opportunity Score that identifies country × product pairs where stablecoin-based payments would most increase trade, validated against observed crypto adoption patterns. Third, we introduce a feasibility framework that classifies countries by on/off ramp availability and capital account openness, distinguishing where stablecoin-based trade payments are immediately actionable from where they require infrastructure investment or regulatory reform — and show that our opportunity score predicts future on/off ramp development.

---

## Appendix A: Data Pipeline Overview

1. **Import BACI** (HS12, 2015-2023) -> clean, standardize country codes to ISO3
2. **Compute complexity** from BACI: RCA -> MCP matrix -> ECI, PCI, proximity (via `economiccomplexity`)
3. **Merge CEPII Gravity** (extend to 2023 using WDI for GDP/pop)
4. **Merge BIS/CPMI** correspondent banking density (bilateral)
5. **Merge RPW** remittance costs (367 corridors; missing corridors -> NA, not imputed)
6. **Merge IMF FAS** and Chinn-Ito (country-level, construct bilateral min/mean)
7. **Construct panel:** exporter x importer x product x year, including zeros for active pairs
8. **Estimate Specifications 1-4** in `fixest`
9. **Compute SOS** from estimated coefficients + complexity data
10. **Validate SOS** against Chainalysis, conditional on income
11. **Robustness and falsification** battery (15 robustness + 7 falsification tests)

---

## Appendix B: Comparison to Closest Papers' Methods

| Feature | Ferrari Minesso et al. (2026) | Borchert et al. (2024) | Manova (2013) | Our Paper |
|---------|-------------------------------|------------------------|---------------|-----------|
| Dep var | Bilateral trade (aggregate) | Firm-level exports | Industry-level exports | Bilateral trade (product-level) |
| Treatment | Payment system link (binary) | CBR loss (binary) | Financial development (country) | Payment friction (continuous, bilateral) |
| Interaction | None | None | Fin dev x Rajan-Zingales | Pay friction x PCI |
| Identification | Event study (link establishment) | Firm-level DiD | Cross-country variation | Structural gravity + within-pair cross-product |
| Product heterogeneity | No | No | Industry-level (ISIC) | Product-level (HS 4-digit, ~1,200 products) |
| Estimator | PPML | Probit/OLS | OLS/IV | PPML |
| FEs | Exporter x year, importer x year | Firm, country-year | Country x year, industry | Exporter x year, importer x year, pair, product |
