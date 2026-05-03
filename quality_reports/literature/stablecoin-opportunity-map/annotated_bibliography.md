# Annotated Bibliography: Payment Infrastructure, Trade Costs, and Financial Frictions in Trade

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Stream:** Payment Infrastructure, Trade Costs, and Financial Frictions
**Date:** 2026-04-03
**Librarian Agent**

---

## Category 1: Directly Related -- Payment Systems and Trade Flows

### Ferrari Minesso, Lebastard & Triay Bagur (2026) -- Interlinking Payment Systems and Trade Flows
- **Journal:** ECB Working Paper No. 3202
- **Proximity:** 5
- **Main contribution:** First causal estimate of the trade impact of interlinking fast payment systems across countries, using a gravity framework with a novel dataset covering 84 countries and 531 payment links (2021--2024).
- **Identification strategy:** Structural gravity with PPML; endogeneity addressed using the method of Carlson and Joshi (2024).
- **Key finding:** Interconnected payment systems increase bilateral trade by approximately 4%, roughly half the effect of a formal trade agreement and a quarter of a common currency.
- **Relevance:** Directly demonstrates that payment infrastructure reduces trade costs in a gravity framework -- the exact channel our stablecoin paper proposes to study. Key methodological precedent.

### Auer, Lewrick & Paulick (2025) -- DeFiying Gravity? An Empirical Analysis of Cross-Border Crypto Flows
- **Journal:** BIS Working Paper No. 1265
- **Proximity:** 5
- **Main contribution:** Applies a gravity framework to cross-border flows of Bitcoin, Ether, Tether, and USDC across 184 countries (2017--2024). Distinguishes speculative vs. transactional motives.
- **Identification strategy:** Gravity model with bilateral crypto flow data; separates stablecoin flows from native crypto; exploits variation in traditional remittance costs.
- **Key finding:** High costs of traditional remittance payments are associated with significantly larger cross-border stablecoin flows from advanced to emerging economies. Stablecoin flows peaked at ~USD 1.3 trillion in 2021.
- **Relevance:** This is the closest existing paper to ours. It shows stablecoins substitute for costly payment rails using gravity. Our paper extends this by bringing in economic complexity (which products benefit) rather than just which corridors see flows.

### Du, Huang & Scharfstein (2026) -- Competing Rails for Cross-Border Payments: Banks, Fintechs, and Stablecoins
- **Journal:** Harvard Business School Working Paper
- **Proximity:** 5
- **Main contribution:** Compares the cost structure of three payment rails -- correspondent banking/SWIFT, non-bank money transmitters (Wise, Remitly), and stablecoin-based transfers -- for cross-border payments.
- **Identification strategy:** Cost decomposition analysis across payment rails; comparison of fee components (FX spreads, network fees, on/off-ramp costs).
- **Key finding:** Stablecoin rails reduce settlement and balance sheet frictions but do not eliminate intermediation. For major currencies, stablecoin FX execution approaches benchmark rates and blockchain fees are negligible, but on/off-ramp costs introduce new frictions.
- **Relevance:** Provides the micro-level cost decomposition that motivates our macro-level gravity analysis. Identifies exactly where stablecoins reduce vs. redistribute payment frictions.

### Borchert, De Haas, Kirschenmann & Schultz (2024) -- Broken Relationships: De-Risking by Correspondent Banks and International Trade
- **Journal:** CEPR Discussion Paper No. 19373 (also EBRD Working Paper No. 285)
- **Proximity:** 5
- **Main contribution:** Uses firm-level export data from emerging Europe to show that terminated correspondent banking relationships cause significant export declines, especially for SMEs.
- **Identification strategy:** Exploits variation in bank-level exposure to correspondent relationship terminations; firm-level panel with bank-firm linkages.
- **Key finding:** Export probability falls by 5.2 pp immediately after correspondent bank loss, growing to 20.6 pp after four years. Small firms' export probability declines by 40.1 pp by year four.
- **Relevance:** Establishes the causal mechanism our paper seeks to quantify at scale: when payment infrastructure breaks down, trade collapses. Stablecoins could serve as an alternative rail in de-risked corridors.

---

## Category 2: Same Context, Different Method -- Correspondent Banking, Remittances, and De-Risking

### Rice, von Peter & Boar (2020) -- On the Global Retreat of Correspondent Banks
- **Journal:** BIS Quarterly Review (March 2020)
- **Proximity:** 4 (already in bibliography)
- **Main contribution:** Documents the global decline in correspondent banking relationships (CBRs) from 2011 to 2019, identifying concentration patterns and geographic variation.
- **Identification strategy:** Descriptive analysis of SWIFT data on active CBR connections by country pair.
- **Key finding:** Active correspondent banks per country-pair declined substantially, with increasing concentration (Gini coefficient rose). Small and developing countries most affected.
- **Relevance:** Provides the descriptive backdrop for our payment friction measure. The de-risking map aligns with corridors where stablecoin adoption is highest.

### Beck & Martinez Peria (2011) -- What Explains the Cost of Remittances?
- **Journal:** World Bank Economic Review, 25(1), 105--131
- **Proximity:** 4 (already in bibliography)
- **Main contribution:** Examines remittance cost determinants across 119 corridors, focusing on market structure, regulation, and infrastructure.
- **Identification strategy:** Cross-corridor OLS regressions with corridor-level controls.
- **Key finding:** Lack of competition (fewer remittance service providers) and regulatory barriers are the primary drivers of high remittance costs. Corridors with exclusive partnerships pay 2--4 pp more.
- **Relevance:** Identifies the structural factors behind high payment costs that stablecoins could bypass. Remittance cost data is a key variable in our gravity specification.

### IMF SDN (2016) -- The Withdrawal of Correspondent Banking Relationships
- **Journal:** IMF Staff Discussion Note SDN/16/06
- **Proximity:** 4
- **Main contribution:** Provides the first comprehensive policy analysis of the global withdrawal of correspondent banking relationships, driven by AML/CFT compliance costs and risk aversion.
- **Identification strategy:** Descriptive; survey-based evidence from affected jurisdictions.
- **Key finding:** Smaller jurisdictions in Africa, Caribbean, Central Asia, and the Pacific are most affected. Some countries left with only one or two CBR connections, creating systemic vulnerability.
- **Relevance:** Identifies the exact geographic pattern where stablecoin payment alternatives would have the highest marginal value -- our "opportunity map" targets these corridors.

---

## Category 3: Financial Frictions and Trade

### Manova (2013) -- Credit Constraints, Heterogeneous Firms, and International Trade
- **Journal:** Review of Economic Studies, 80(2), 711--744
- **Proximity:** 3
- **Main contribution:** Incorporates financial frictions into a heterogeneous-firm trade model. Shows that credit constraints affect trade through three channels: domestic production selection, export selection, and export levels.
- **Identification strategy:** Cross-country, cross-sector variation in financial development x financial vulnerability (Rajan-Zingales approach).
- **Key finding:** 20--25% of credit constraint effects on trade come from reduced output; of the trade-specific effect, one-third is limited entry, two-thirds are lower per-firm exports. Financially developed economies export more in financially vulnerable sectors.
- **Relevance:** Provides the theoretical framework for why payment/financial frictions have heterogeneous effects across industries -- exactly the mechanism our complexity interaction exploits.

### Leibovici (2021) -- Financial Development and International Trade
- **Journal:** Journal of Political Economy, 129(12), 3405--3446
- **Proximity:** 3
- **Main contribution:** General equilibrium model with input-output linkages showing that financial development reallocates trade from labor- to capital-intensive industries, with minor aggregate effects.
- **Identification strategy:** Calibrated multi-industry GE model with heterogeneous firms and financial frictions; validated against cross-country industry-level data.
- **Key finding:** Financial development substantially reallocates trade shares across industries but has minor aggregate effects. Industry-level financial vulnerability determines the reallocation pattern.
- **Relevance:** Supports our hypothesis that payment frictions have heterogeneous effects across product categories. Complexity (our measure) correlates with capital intensity and financial dependence.

### Antras & Foley (2015) -- Poultry in Motion: A Study of International Trade Finance Practices
- **Journal:** Journal of Political Economy, 123(4), 809--852
- **Proximity:** 3
- **Main contribution:** Uses transaction-level data from a U.S. food exporter to study how trade finance terms (cash in advance, open account, letters of credit) vary with destination-country characteristics.
- **Identification strategy:** Within-firm variation across destinations and over time; exploits relationship building to identify trust effects.
- **Key finding:** Cash in advance (42.4%) and open account (41.3%) dominate over letters of credit (10.7%). Weak contract enforcement increases reliance on cash-in-advance or LC terms. Relationships shift terms toward open account over time.
- **Relevance:** Shows how payment terms respond to institutional risk -- the micro-mechanism through which payment infrastructure affects trade patterns. Stablecoins could reduce the need for costly LCs.

### Niepmann & Schmidt-Eisenlohr (2017) -- No Guarantees, No Trade: How Banks Affect Export Patterns
- **Journal:** Journal of International Economics, 108(C), 338--350
- **Proximity:** 3
- **Main contribution:** Uses U.S. banks' trade finance claims by country to estimate how shocks to letter of credit supply affect U.S. exports.
- **Identification strategy:** Exploits variation in bank market shares across destination countries; instruments LC supply with bank-level characteristics.
- **Key finding:** A one-standard-deviation negative shock to LC supply reduces U.S. exports to that country by 1.5 pp. Effect doubles during crises and is stronger for smaller/poorer destinations.
- **Relevance:** Establishes that bank-mediated trade finance is a binding constraint on trade. Stablecoins + smart contracts could automate parts of the LC function.

### Crozet, Demir & Javorcik (2022) -- International Trade and Letters of Credit: A Double-Edged Sword in Times of Crises
- **Journal:** IMF Economic Review, 70, 185--211
- **Proximity:** 3
- **Main contribution:** Shows that LC-intensive products are more resilient during uncertainty crises (e.g., COVID) but more vulnerable during financial crises when banks limit LC supply.
- **Identification strategy:** Product-level variation in LC intensity (new measure for 1,196 HS4 products) interacted with crisis indicators; gravity framework.
- **Key finding:** LC-backed trade flows show no decline relative to historical average during COVID uncertainty, but sharp declines during financial crises. Product LC intensity correlates with shipment size, time to ship, and relationship stickiness.
- **Relevance:** Product-level heterogeneity in trade finance dependence maps onto our product complexity dimension. Complex products requiring more trade finance may benefit most from stablecoin-based alternatives.

### Chaney (2016) -- Liquidity Constrained Exporters
- **Journal:** Journal of Economic Dynamics and Control, 72, 141--154
- **Proximity:** 2
- **Main contribution:** Extends Melitz-Chaney heterogeneous firm model with financial frictions binding on potential exporters who must cover fixed export costs with internal funds.
- **Identification strategy:** Theoretical model with calibration.
- **Key finding:** More productive and wealthier firms are more likely to export. Currency depreciation has ambiguous extensive margin effects: raises sales (encouraging entry) but reduces value of self-finance (discouraging entry).
- **Relevance:** Provides theoretical microfoundation for why reducing fixed costs of exporting (through cheaper payments) can expand the extensive margin of trade.

---

## Category 4: Technology Adoption and Trade Costs

### Freund & Weinhold (2004) -- The Effect of the Internet on International Trade
- **Journal:** Journal of International Economics, 62(1), 171--189
- **Proximity:** 3 (already in bibliography)
- **Main contribution:** Estimates the effect of internet penetration on bilateral trade using a gravity model, finding that the internet reduces trade costs particularly for differentiated goods.
- **Identification strategy:** Gravity model with internet penetration as trade cost shifter; country fixed effects and time effects.
- **Key finding:** A 10% increase in web hosts in a country increases exports by 0.2%. Effect is larger for differentiated goods and for developing country pairs.
- **Relevance:** Methodological template for our paper: technology adoption variable interacted with gravity model. We replace "internet penetration" with "stablecoin adoption / payment friction."

### Jack & Suri (2014) -- Risk Sharing and Transactions Costs: Evidence from Kenya's Mobile Money Revolution
- **Journal:** American Economic Review, 104(1), 183--223
- **Proximity:** 3
- **Main contribution:** Estimates the welfare effects of M-Pesa mobile money in Kenya, showing that reduced transaction costs improve risk sharing.
- **Identification strategy:** Panel data (2008--2010); uses the four-fold expansion of the M-Pesa agent network as exogenous variation in access.
- **Key finding:** Negative economic shocks reduce consumption by 7% for non-users, but M-Pesa users are unaffected. Mechanisms: more remittances received and more diverse sender networks.
- **Relevance:** Demonstrates that mobile payment infrastructure has real economic effects through reduced transaction costs -- analogous to the stablecoin channel but at the domestic level. Identification strategy (network expansion) could inspire IV approaches for stablecoin infrastructure.

### Aker & Mbiti (2010) -- Mobile Phones and Economic Development in Africa
- **Journal:** Journal of Economic Perspectives, 24(3), 207--232
- **Proximity:** 2
- **Main contribution:** Reviews the evidence on how mobile phones reduce communication and information costs in African markets, improving market efficiency and welfare.
- **Identification strategy:** Literature review; cites experimental and quasi-experimental evidence.
- **Key finding:** Mobile phones reduce grain price dispersion across markets by 10% in Niger. Effects are stronger for markets with higher transport costs.
- **Relevance:** Establishes precedent that communication/transaction cost reduction technologies improve market integration -- the mechanism we invoke for stablecoins.

---

## Category 5: Currency Invoicing and Trade

### Gopinath, Boz, Casas, Diez, Gourinchas & Plagborg-Moller (2020) -- Dominant Currency Paradigm
- **Journal:** American Economic Review, 110(3), 677--719
- **Proximity:** 4
- **Main contribution:** Proposes and tests the dominant currency paradigm (DCP): the dollar's role as invoicing currency creates asymmetric trade responses to exchange rate movements across countries.
- **Identification strategy:** New dataset of bilateral price and volume indices for 2,500+ country pairs (91% of world trade); gravity-style regressions of trade volumes on dollar exchange rates.
- **Key finding:** A 1% USD appreciation against all currencies predicts a 0.6% decline in trade volume between non-US countries within one year. Dollar exchange rate dominates bilateral exchange rate in pass-through regressions.
- **Relevance:** Critical context: stablecoins are predominantly USD-denominated (USDT, USDC). The DCP means stablecoin adoption reinforces dollar dominance in trade invoicing. Our paper should address whether stablecoins entrench or disrupt the DCP.

### Gopinath (2016) -- The International Price System
- **Journal:** Jackson Hole Symposium Proceedings (NBER WP 21646)
- **Proximity:** 3
- **Main contribution:** Documents that the overwhelming share of world trade is invoiced in very few currencies (primarily USD), and international prices in invoicing currency are sticky for up to two years.
- **Identification strategy:** Descriptive analysis of invoicing currency shares; exchange rate pass-through regressions.
- **Key finding:** U.S. inflation is insulated from exchange rate shocks; other countries are highly sensitive. A country's inflation sensitivity to exchange rates is well proxied by the fraction of imports invoiced in foreign currency.
- **Relevance:** Establishes that dollar invoicing is the default, which means USD stablecoins naturally fit existing trade invoicing patterns rather than requiring a currency shift.

### Boz, Casas, Georgiadis, Gopinath, Le Mezo, Mehl & Nguyen (2020) -- Patterns in Invoicing Currency in Global Trade
- **Journal:** IMF Working Paper WP/20/126
- **Proximity:** 3
- **Main contribution:** Constructs the most comprehensive panel dataset of invoicing currency shares for 100+ countries since 1990.
- **Identification strategy:** Descriptive panel analysis with cross-country regressions of invoicing currency determinants.
- **Key finding:** USD and EUR invoicing shares have grown even as US/Euro area trade shares declined. Countries invoicing more in USD experience greater USD exchange rate pass-through and trade volume sensitivity to USD fluctuations.
- **Relevance:** The invoicing currency dataset could serve as a control or moderator in our gravity model -- corridors with high USD invoicing may see different stablecoin effects.

---

## Category 6: Trade Costs Measurement (Methods Papers)

### Anderson & van Wincoop (2004) -- Trade Costs
- **Journal:** Journal of Economic Literature, 42(3), 691--751
- **Proximity:** 3 (already in bibliography; foundational)
- **Main contribution:** Comprehensive survey of trade costs, documenting that total trade costs are large (170% ad valorem for developed countries) and composed of transport, border, and distribution costs.
- **Identification strategy:** Survey/meta-analysis of trade cost estimates.
- **Key finding:** Trade costs equivalent to 170% tariff for industrialized countries. Policy barriers (tariffs, NTBs) are a small share; information costs, contract enforcement, and currency costs are substantial.
- **Relevance:** Foundational reference. Payment/transaction costs are identified as a component of trade costs but rarely measured directly -- our paper fills this gap using stablecoin adoption as a revealed preference measure.

### Novy (2013) -- Gravity Redux: Measuring International Trade Costs with Panel Data
- **Journal:** Economic Inquiry, 51(1), 101--121
- **Proximity:** 2
- **Main contribution:** Derives a micro-founded measure of bilateral trade costs inferred from observable trade data, consistent with Ricardian and heterogeneous-firm models.
- **Identification strategy:** Structural gravity inversion: trade costs inferred from bilateral trade relative to domestic trade.
- **Key finding:** U.S. trade costs with major partners declined ~40% between 1970 and 2000. Largest reductions with Mexico and Canada.
- **Relevance:** Provides the trade cost measurement approach we could use to validate whether stablecoin corridors show declining inferred trade costs.

### Chen & Novy (2022) -- Gravity and Heterogeneous Trade Cost Elasticities
- **Journal:** Economic Journal, 132(644), 1349--1377
- **Proximity:** 3
- **Main contribution:** Estimates a translog gravity model that allows trade cost elasticities to vary across country pairs. "Thin" bilateral relationships (small import shares) are more sensitive to trade cost changes than "thick" ones.
- **Identification strategy:** Translog gravity estimation with 1.1M+ observations; heterogeneous elasticities for currency unions, FTAs, WTO membership.
- **Key finding:** Trade cost effects are strong for thin bilateral relationships and weak or zero for thick relationships. Average effects mask substantial heterogeneity.
- **Relevance:** Directly relevant methodology. Stablecoin adoption likely has the largest trade effects on thin bilateral relationships (developing-country corridors) -- exactly where payment frictions are highest.

### Head & Mayer (2014) -- Gravity Equations: Workhorse, Toolkit, and Cookbook
- **Journal:** Handbook of International Economics, Vol. 4, 131--195
- **Proximity:** 2 (already in bibliography; methodological reference)
- **Main contribution:** Comprehensive handbook chapter on gravity model theory and estimation, covering structural foundations, estimation methods, and best practices.
- **Identification strategy:** Methodological guide; meta-analysis of gravity estimates.
- **Key finding:** Distance elasticity meta-estimate of -1.1. Recommends PPML estimation, exporter x year and importer x year FEs, and country-pair clustering.
- **Relevance:** Methodological bible for our gravity estimation. All specifications should conform to Head-Mayer best practices.

### Santos Silva & Tenreyro (2006) -- The Log of Gravity
- **Journal:** Review of Economics and Statistics, 88(4), 641--658
- **Proximity:** 2 (already in bibliography; methodological reference)
- **Main contribution:** Shows that log-linearized OLS gravity is inconsistent under heteroskedasticity and proposes PPML as the solution. PPML naturally handles zeros in trade data.
- **Identification strategy:** Monte Carlo simulations + empirical application demonstrating OLS bias.
- **Key finding:** OLS gravity overestimates distance effects and underestimates common-language effects. PPML yields qualitatively different results for several standard gravity variables.
- **Relevance:** Our estimation method. All results will use PPML.

---

## Category 7: Theoretical Foundations

### Accominotti & Ugolini (2025) -- International Trade Finance from the Origins to the Present
- **Journal:** Oxford Handbook of Institutions of International Economic Governance (Oxford University Press)
- **Proximity:** 2
- **Main contribution:** Historical overview of how international trade finance evolved from merchant bills to the modern correspondent banking system, documenting the role of "acceptance houses" as gatekeepers and the centralization/standardization cycle.
- **Identification strategy:** Historical narrative and institutional analysis.
- **Key finding:** Trade finance has historically been centralized around dominant financial centers (Antwerp, Amsterdam, London, New York). The correspondent banking network is the latest instantiation of a recurring pattern.
- **Relevance:** Contextualizes stablecoins as a potential disruption to the latest centralization cycle in trade finance, much as the bill of exchange disrupted medieval merchant networks.

---

## Scooping Risk Assessment

| Paper | Risk Level | Rationale |
|-------|-----------|-----------|
| Auer, Lewrick & Paulick (2025) | HIGH | Uses gravity model for crypto/stablecoin flows -- but focuses on capital flows, not goods trade |
| Ferrari Minesso et al. (2026) | HIGH | Payment systems + gravity + trade -- but studies fast payment system links, not stablecoins |
| Du, Huang & Scharfstein (2026) | MEDIUM | Cost comparison of payment rails -- but no gravity/trade volume analysis |
| Borchert et al. (2024) | MEDIUM | De-risking + trade -- but no stablecoin/crypto dimension |

**Our differentiation:** None of these papers combine (1) stablecoin adoption with (2) economic complexity / product-level heterogeneity in (3) a structural gravity framework. Auer et al. come closest but study financial flows, not goods trade. Ferrari Minesso et al. study payment links but not crypto/stablecoins. Our contribution sits at the intersection.

---

## Papers Already in Bibliography (Not Duplicated Above)

- Anderson & van Wincoop (2004) -- Trade Costs [JEL]
- Santos Silva & Tenreyro (2006) -- PPML [REStat]
- Head & Mayer (2014) -- Gravity Handbook [HBK Int Econ]
- Freund & Weinhold (2004) -- Internet and Trade [JIE]
- Fink, Mattoo & Neagu (2005) -- Communication Costs [JIE]
- Rice, von Peter & Boar (2020) -- Correspondent Banking [BIS QR]
- Beck & Martinez Peria (2011) -- Remittance Costs [WBER]
