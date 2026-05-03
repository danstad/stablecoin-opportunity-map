# Frontier Map: Payment Infrastructure, Trade Costs, and Financial Frictions in Trade

**Project:** Stablecoin Opportunity Map -- Economic Complexity Meets Payment Innovation
**Stream:** Payment Infrastructure, Trade Costs, and Financial Frictions
**Date:** 2026-04-03

---

## 1. What Has Been Done

### 1A. Payment Systems and Trade (Emerging Frontier)

The literature on payment infrastructure and trade is new and growing rapidly.

- **Ferrari Minesso et al. (2026)** provide the first causal estimate that interlinking fast payment systems increases bilateral trade by ~4%. This is the closest methodological precedent: gravity + payment infrastructure variable. Their dataset covers 84 countries and 531 payment links.

- **Auer, Lewrick & Paulick (2025)** apply gravity to cross-border *crypto* flows (not goods trade), showing that stablecoin flows substitute for costly traditional remittances. This is the paper most likely to be seen as a competitor, but it studies financial flows, not goods trade.

- **Du, Huang & Scharfstein (2026)** decompose the cost structure of stablecoin payments vs. SWIFT vs. fintech, showing stablecoins reduce settlement frictions but introduce on/off-ramp costs. Descriptive, not causal.

**Frontier status:** The payment-systems-as-trade-costs idea is established but the stablecoin-specific version is wide open.

### 1B. Correspondent Banking and De-Risking

- **Rice et al. (2020)** document the global CBR decline. **Borchert et al. (2024)** provide the first causal evidence that CBR termination reduces firm exports (5--41 pp over four years). **IMF (2016)** maps the affected geographies.

- The de-risking literature establishes that losing correspondent banking access is a severe trade barrier. No paper connects this to stablecoin adoption as a substitute rail.

**Frontier status:** Causal effects of de-risking on trade are established. The stablecoin-as-alternative-rail hypothesis is untested.

### 1C. Financial Frictions and Trade

- **Manova (2013)** is the foundational paper: credit constraints reduce trade through selection and intensity channels, with effects varying by industry financial vulnerability (Rajan-Zingales).

- **Leibovici (2021)** shows financial development reallocates trade across industries (labor- to capital-intensive) with minor aggregate effects.

- **Antras & Foley (2015)** document micro-level trade finance practices. **Niepmann & Schmidt-Eisenlohr (2017)** show LC supply shocks reduce exports. **Crozet, Demir & Javorcik (2022)** show product-level heterogeneity in trade finance dependence.

**Frontier status:** The financial-frictions-and-trade literature is mature but has not considered stablecoins or digital payment alternatives as a friction reducer.

### 1D. Currency Invoicing

- **Gopinath et al. (2020)** establish the dominant currency paradigm: USD invoicing governs trade dynamics even for non-US trade pairs. **Boz et al. (2020)** provide comprehensive invoicing data.

**Frontier status:** Well established. USD stablecoins naturally align with the DCP but no paper has explored this connection.

### 1E. Technology and Trade Costs

- **Freund & Weinhold (2004)** is the template paper: internet adoption reduces trade costs in gravity. **Jack & Suri (2014)** show M-Pesa reduces transaction costs with real welfare effects. **Aker & Mbiti (2010)** document mobile phones improving market efficiency.

**Frontier status:** The "technology reduces trade costs" template is well established. Applying it to stablecoins is novel.

### 1F. Trade Cost Measurement

- **Anderson & van Wincoop (2004)** survey total trade costs (~170% ad valorem). **Novy (2013)** provides an inferred trade cost measure. **Chen & Novy (2022)** show trade cost elasticities are heterogeneous across country pairs.

**Frontier status:** Payment costs are identified as a component of trade costs but never measured directly or isolated empirically.

---

## 2. What Is the Gap

### Gap 1: No paper studies how stablecoin adoption affects goods trade flows.
- Auer et al. (2025) study crypto *financial* flows using gravity but do not connect to goods trade.
- Ferrari Minesso et al. (2026) study fast payment system links and trade but not crypto/stablecoins.
- No paper combines stablecoins + gravity + bilateral goods trade.

### Gap 2: No paper introduces product-level heterogeneity (economic complexity) into the payment-costs-and-trade relationship.
- Manova (2013) uses Rajan-Zingales financial vulnerability for credit constraints.
- Crozet et al. (2022) use product-level LC intensity.
- Nobody uses economic complexity (ECI/PCI) as the heterogeneity dimension for payment friction effects.

### Gap 3: No paper maps the "opportunity surface" -- which country x product cells would benefit most from reduced payment frictions.
- The de-risking literature identifies affected countries but not affected products.
- The complexity literature identifies products with growth potential but not the payment barrier.
- The intersection (country with high payment friction x product with high complexity potential) is unexplored.

### Gap 4: The DCP-stablecoin connection is unexplored.
- Gopinath et al. (2020) show dollar invoicing shapes trade dynamics.
- Stablecoins are overwhelmingly USD-denominated.
- Whether stablecoin adoption reinforces or disrupts the DCP in trade is an open question.

---

## 3. Where Our Paper Fits

```
                    Payment Infrastructure
                    (Ferrari Minesso 2026,
                     Rice et al. 2020,
                     Borchert et al. 2024)
                           |
                           |  GAP: stablecoins as
                           |  payment infrastructure
                           |
    Economic Complexity ---[OUR PAPER]--- Gravity + Trade Costs
    (Hidalgo 2007/2009,    |              (Anderson & vW 2004,
     Hausmann 2014)        |               Head & Mayer 2014,
                           |               Santos Silva 2006)
                           |
                    Financial Frictions
                    (Manova 2013,
                     Antras & Foley 2015,
                     Niepmann & SE 2017)
```

**Our paper occupies the intersection of four literatures:**

1. We use **gravity model** methodology (PPML, structural FEs) from the trade costs literature.
2. We introduce **payment friction** as a trade cost component, measured through correspondent banking density, remittance costs, and stablecoin adoption (from the payment/de-risking literature).
3. We interact payment frictions with **product complexity** (from the economic complexity literature) to identify which products are most affected.
4. We draw on **financial frictions and trade** theory (Manova 2013) to motivate why complex products are more sensitive to payment frictions (they require more trade finance, longer payment cycles, and higher counterparty trust).

**The result is a "Stablecoin Opportunity Map":** a predicted surface over country-pairs x product categories showing where stablecoin-mediated payment cost reduction would generate the largest trade gains.

---

## 4. Key Methodological Lessons from the Literature

| Lesson | Source | Implication for Our Paper |
|--------|--------|--------------------------|
| Use PPML, not OLS on log trade | Santos Silva & Tenreyro (2006) | All specifications use PPML with zeros |
| Include exporter x year and importer x year FEs | Head & Mayer (2014) | Structural gravity specification |
| Cluster SEs at country-pair level | Head & Mayer (2014) | Standard error computation |
| Trade cost elasticities are heterogeneous | Chen & Novy (2022) | Thin corridors are more sensitive -- our main result likely driven by these |
| Use product-level variation for identification | Manova (2013), Crozet et al. (2022) | Interact payment friction with product complexity for within-corridor variation |
| Address endogeneity of payment infrastructure | Ferrari Minesso et al. (2026) | Payment infrastructure may respond to trade -- need IV or control strategy |
| Technology effects are larger for differentiated goods | Freund & Weinhold (2004) | Complex products are differentiated -- expect larger effects |
