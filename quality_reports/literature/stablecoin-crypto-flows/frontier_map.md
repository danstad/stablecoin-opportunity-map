# Frontier Map: Stablecoins, Crypto, and Cross-Border Flows

**Date:** 2026-04-03
**Stream:** Stablecoins, Cryptocurrency, and Cross-Border Trade/Capital Flows

---

## What Has Been Done

### 1. Measuring Cross-Border Crypto/Stablecoin Flows
- **Auer, Lewrick & Paulick (2025, BIS):** Full gravity model of crypto flows (BTC, ETH, USDT, USDC) across 184 countries. The current gold standard for bilateral crypto flow estimation.
- **Reuter (2025, IMF):** AI/ML-based geographic attribution of stablecoin flows. Regional flow estimates: NA $633bn, APAC $519bn, LAC/MENA highest relative to GDP.
- **Cerutti, Chen & Hengge (2024, IMF):** Methodology primer for Bitcoin cross-border flow measurement. Distinguishes on-chain vs. off-chain data.
- **Cerutti, Obstfeld & Zhou (2024, IMF) [in bib]:** Push/pull SVAR for cross-border crypto flows.
- **Graf von Luckner, Reinhart & Rogoff (2023, JME) [in bib]:** Foundational paper on crypto as new-age capital flows.

### 2. Stablecoins and Real-Economy Effects
- **Aldasoro, Beltran & Grinberg (2026, BIS/IMF):** Stablecoin inflows spill over to FX markets (40bp parity deviation per 1% inflow).
- **Cerutti et al. (2026, IMF):** Stablecoin demand shocks move Treasury yields, dollar, and equity markets.
- **Copestake et al. (2026, IMF):** GENIUS Act reduced incumbent payment firm valuations by 18% (~$300bn); effect larger for cross-border-focused firms.
- **Barthelemy, Gardin & Nguyen (2024, BdF):** Stablecoin reserve demand drives commercial paper issuance.

### 3. Stablecoins, Dollarization, and Financial Inclusion
- **Murakami & Viswanath-Natraj (2025, JIMF):** Sovereign risk drives stablecoin adoption in EMs. Theoretical framework for digital dollarization benefits/costs.
- **Copestake et al. (2025, Economics Letters):** DSGE model showing foreign stablecoins amplify currency substitution and capital outflows in developing economies.
- **Rey (2025, F&D):** High-level argument that stablecoins could fragment the international monetary system.

### 4. Payment Frictions and Trade
- **Borchert et al. (2024, CEPR):** Correspondent banking de-risking reduces export probability by 9.7pp. Quantifies the payment friction --> trade disruption channel.
- **Liu & Chen (2025):** Fintech reduces trade costs in gravity framework.
- **Cerutti, Firat & Perez-Saiz (2025, IMF):** Scenario analysis: 60% cross-border cost reduction from digital money --> significant volume increase.

### 5. Regulatory Landscape
- **Aldasoro et al. (2025, BIS Bulletin 108):** Documents stablecoin market growth, policy challenges, monetary sovereignty concerns.
- **GENIUS Act (2025):** US regulatory framework for payment stablecoins.
- **MiCA (2023-2024):** EU crypto-asset framework with stablecoin-specific provisions.

---

## What Has NOT Been Done (The Gaps)

### Gap 1: No paper connects stablecoin adoption to product-level trade flows
- Auer et al. (2025) use a gravity model for aggregate bilateral crypto flows but do not disaggregate by industry or product.
- No existing paper asks: "Which specific industries or products benefit most from stablecoin-enabled payment cost reductions?"
- **This is our primary contribution.**

### Gap 2: No paper integrates economic complexity with digital payment infrastructure
- The economic complexity literature (Hidalgo et al. 2007, 2009; Hausmann et al. 2014) studies which products countries can competitively export.
- The stablecoin literature studies aggregate flows and financial stability.
- No paper combines these: which countries can newly access complex-product export markets when payment frictions are reduced by stablecoins?
- **This is our second contribution.**

### Gap 3: No paper models the heterogeneous treatment of stablecoins across product types
- Borchert et al. (2024) show that payment disruption harms exports heterogeneously by firm size.
- No paper examines whether relationship-intensive, complex products are more or less affected by payment friction changes than simple commodities.
- **This is our third contribution** (interaction of payment frictions x product complexity in gravity).

### Gap 4: Predictive "opportunity maps" do not exist
- The Atlas of Economic Complexity provides product-space-based predictions of future comparative advantage.
- No analogous exercise predicts which country x industry links are most likely to activate if stablecoin-based payment frictions fall.
- **This is our applied/policy contribution.**

### Gap 5: Limited gravity analysis of stablecoin-specific (not aggregate crypto) trade cost effects
- Auer et al. (2025) use gravity for crypto flows themselves, but do not estimate how stablecoin availability affects goods/services trade flows in a gravity framework.
- The fintech-trade gravity literature (Liu & Chen 2025) uses broad fintech indices, not stablecoin-specific measures.
- **We fill this by using stablecoin-specific payment friction proxies in a goods-trade gravity model.**

---

## Where Our Paper Fits

```
                          Aggregate         Product-Level
                          Flows             Trade Flows
                    +------------------+------------------+
                    |                  |                  |
    Crypto/         | Auer et al.      |                  |
    Stablecoin      | (2025)           |   [OUR PAPER]    |
    Flows           | Reuter (2025)    |                  |
                    | Cerutti (2024)   |                  |
                    +------------------+------------------+
                    |                  |                  |
    Traditional     | Standard gravity |  Borchert et al. |
    Payment         | (Anderson &      |  (2024) -- firm  |
    Frictions       |  van Wincoop)    |  level effects   |
                    |                  |                  |
                    +------------------+------------------+

                    Missing dimension: PRODUCT COMPLEXITY
                    (Hidalgo & Hausmann 2009)
```

Our paper sits at the intersection of:
1. **Stablecoin/crypto flow measurement** (Auer et al. 2025, Reuter 2025)
2. **Payment frictions and trade** (Borchert et al. 2024, Cerutti et al. 2025)
3. **Economic complexity** (Hidalgo et al. 2007, 2009)
4. **Structural gravity estimation** (Santos Silva & Tenreyro 2006, Head & Mayer 2014)

---

## Scooping Risk Assessment

| Paper | Risk Level | Reason |
|-------|-----------|--------|
| Auer, Lewrick & Paulick (2025) | MEDIUM | Uses gravity for crypto flows but does NOT connect to goods trade or complexity. We extend their framework. |
| Cerutti, Firat & Perez-Saiz (2025) | LOW-MEDIUM | Scenario analysis of digital money --> cross-border flows, but no gravity estimation and no product-level analysis. |
| Copestake et al. (2026) | LOW | Event study on payment firms; does not study trade flows. |
| Liu & Chen (2025) | LOW | Fintech-trade gravity, but uses broad fintech index, not stablecoin-specific. |
| Borchert et al. (2024) | LOW | Studies the disruption problem but not the stablecoin solution. |

**Overall scooping risk: LOW.** No paper combines stablecoins + gravity + economic complexity. The gap is clear and defensible.

---

## Key Data Sources Used Across These Papers

| Data Source | Used By | Relevance for Us |
|-------------|---------|-----------------|
| Chainalysis bilateral crypto flow data | Auer et al. (2025), Reuter (2025) | Primary stablecoin flow data |
| World Bank Remittance Prices Worldwide | Cerutti et al. (2025), Auer et al. (2025) | Payment friction proxy |
| Crystal Analytics (on-chain) | Cerutti et al. (2024) | Alternative flow measurement |
| BIS correspondent banking data | Borchert et al. (2024) | De-risking measurement |
| Chainalysis Adoption Index | Murakami & Viswanath-Natraj (2025) | Country-level adoption proxy |
| Stablecoin market cap data | Cerutti et al. (2026), Ahmed et al. (2025) | Market size measurement |
