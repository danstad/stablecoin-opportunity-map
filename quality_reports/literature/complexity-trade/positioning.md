# Positioning Statement: Economic Complexity x Stablecoin Payments
## Suggested Contribution and Differentiation

**Date:** 2026-04-03

---

## 1. Suggested Contribution Statement (Draft)

> This paper makes three contributions. First, we integrate the economic complexity framework (Hidalgo & Hausmann, 2009; Hausmann et al., 2014) with a structural gravity model of bilateral trade to show that payment frictions---measured by remittance costs, correspondent banking density, and exchange rate volatility---disproportionately reduce trade in complex products. Second, we develop a Stablecoin Opportunity Score (SOS) that identifies country-product pairs where stablecoin adoption would most increase trade by jointly considering product complexity, capability proximity, and payment friction severity. Third, we provide the first systematic mapping of which bilateral trade corridors and product categories stand to gain most from stablecoin-enabled payment infrastructure, offering actionable guidance for development policy and fintech strategy.

---

## 2. Differentiation from Closest Papers

### vs. Manova (2013) --- Credit Constraints, Heterogeneous Firms, and International Trade
- **Their angle:** Financial frictions affect trade through firm selection and export volumes
- **Our angle:** We focus on payment frictions (not credit access), use complexity metrics (not sector-level financial vulnerability), and study a specific technology (stablecoins) rather than aggregate financial development
- **Key distinction:** Manova asks "does financial development matter for trade?" We ask "which specific products and corridors benefit most from a specific financial innovation?"

### vs. Amiri et al. (2024) --- Has FinTech Reshaped Global Trade?
- **Their angle:** Aggregate fintech index in a structural gravity model
- **Our angle:** Product-level gravity with complexity interactions; stablecoin-specific measures rather than broad fintech
- **Key distinction:** They show fintech increases trade on average. We show which products and corridors gain most, and why (complexity + payment friction interaction).

### vs. Zhu & Li (2019) --- ICT and Trade by Product Complexity
- **Their angle:** ICT (internet penetration) affects trade differently by country complexity segment
- **Our angle:** Payment infrastructure (stablecoins) affects trade differently by product complexity, not country complexity
- **Key distinction:** They segment by country ECI. We interact at the product level (PCI), which is finer and more policy-relevant. Our treatment (stablecoins) is narrower and more identifiable than "ICT."

### vs. Verginer & Riccaboni (2020) --- Bilateral Relatedness
- **Their angle:** Bilateral relatedness predicts trade growth
- **Our angle:** We add a payment friction channel to the relatedness framework
- **Key distinction:** They show relatedness drives trade. We show that payment frictions modulate the strength of this relationship---high relatedness + high payment frictions = large gains from stablecoin adoption.

### vs. Ndoya et al. (2024) --- Financial Development and Complexity
- **Their angle:** Financial development increases ECI, moderated by country stability
- **Our angle:** We study specific bilateral trade flows, not aggregate complexity scores
- **Key distinction:** They ask "does finance make countries more complex?" We ask "does payment infrastructure unlock trade in complex products along specific corridors?"

---

## 3. Where to Publish

Based on the literature landscape:

| Journal | Fit | Reason |
|---------|-----|--------|
| Journal of International Economics | High | Gravity + trade costs + product-level variation; follows Manova (2013), Bahar et al. (2014) |
| Journal of Development Economics | High | Development implications; complexity + fintech + developing countries |
| Review of Economics and Statistics | Medium-High | Empirical contribution with novel data; follows Cadot et al. (2011) |
| Research Policy | Medium | Complexity methods + innovation/technology; follows Balland et al. (2022), Mealy & Teytelboym (2022) |
| Journal of International Money and Finance | Medium | Stablecoin/crypto + trade finance angle |

---

## 4. Anticipated Referee Concerns (from Literature)

1. **"Why not just use standard gravity without complexity?"** Must demonstrate that the complexity interaction significantly improves explanatory power (cf. Ounoughi et al. 2024 show it does for prediction).

2. **"Endogeneity of payment frictions"** --- Payment infrastructure responds to trade demand. Need exogenous variation or strong controls (cf. Manova 2013 uses legal origins; we could use de-risking shocks or regulatory changes).

3. **"Stablecoin data quality"** --- Geographic attribution of on-chain data is unreliable (Cerutti et al. 2024). May need to use predicted adoption based on observable fundamentals rather than actual flows.

4. **"Is this really about stablecoins or just about financial development?"** Must show that the stablecoin-specific channel (settlement speed, 24/7 availability, non-bank access) matters beyond aggregate financial development.

5. **"Product Space stability"** --- If the proximity matrix changes over time, results may be period-specific. Robustness check using different base periods for proximity computation.

---

## 5. Key Equations to Reference

From the literature, our empirical specification should build on:

**Structural gravity (Head & Mayer 2014):**
$$X_{ijpt} = \exp(\alpha_1 \text{PayFriction}_{ijt} + \alpha_2 \text{PCI}_p + \alpha_3 \text{PayFriction}_{ijt} \times \text{PCI}_p + \gamma_{it} + \delta_{jt} + \mu_{ij}) \times \epsilon_{ijpt}$$

The key coefficient is $\alpha_3$: does the trade-reducing effect of payment frictions increase with product complexity?

**Stablecoin Opportunity Score:**
$$\text{SOS}_{cp} = f(\text{PCI}_p, \text{Density}_{cp}, \text{PayFriction}_c, \hat{\beta}_{\text{gravity}})$$

where Density is relatedness density from the product space, and $\hat{\beta}_{\text{gravity}}$ captures the estimated trade response to friction reduction.
