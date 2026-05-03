# Falsification Tests: Stablecoin Opportunity Map

**Project:** Stablecoin Opportunity Map
**Date:** 2026-04-03

---

## Purpose

Falsification tests check that the payment-friction x complexity interaction is driven by the hypothesized mechanism and not by mechanical confounds. Each test specifies what SHOULD NOT happen if our story is correct.

---

## Test 1: Payment Friction x Product Weight (Placebo Interaction)

**Hypothesis to reject:** Payment frictions disproportionately reduce trade in heavy products.

**Specification:**
$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \mu_{ij} + \gamma_p + \alpha_1 PF_{ij,t} + \alpha_2 (PF_{ij,t} \times \text{Weight}_p)\right] \times \varepsilon_{ijp,t}$$

where $\text{Weight}_p$ = average kg per dollar of trade for product $p$.

**Expected result:** $\alpha_2 \approx 0$. Product weight is a logistics friction, not a payment friction. If payment friction interacts with weight, it suggests PF proxies for general trade costs, not payment-specific costs.

**Data source:** BACI includes quantity (kg) alongside value; compute value-to-weight ratio.

**Interpretation if test fails:** PF is not payment-specific; it captures general infrastructure quality. Would require reframing the paper.

---

## Test 2: Payment Friction x Perishability (Placebo Interaction)

**Hypothesis to reject:** Payment frictions disproportionately reduce trade in perishable goods.

**Specification:** Same as Test 1 but replace Weight with a perishability indicator (HS chapters 1-10, 16-23 for food products; or Hummels and Schaur 2013 time-sensitivity classification).

**Expected result:** $\alpha_2 \approx 0$. Perishability is a logistics/time friction, not a payment friction.

**Interpretation if test fails:** PF proxies for general trade facilitation, not payment infrastructure.

---

## Test 3: Geographic Distance x PCI (Placebo Friction)

**Hypothesis to reject:** The PCI interaction is driven by distance, not payment friction.

**Specification:**
$$X_{ijp,t} = \exp\left[\pi_{i,t} + \chi_{j,t} + \gamma_p + \alpha_2 (\ln \text{dist}_{ij} \times PCI_p) + \alpha_3 (PF_{ij,t} \times PCI_p)\right] \times \varepsilon_{ijp,t}$$

**Expected result:** $\alpha_2$ (distance x PCI) is much smaller than $\alpha_3$ (PF x PCI), ideally null. Distance should not differentially penalize complex products because complex products are typically high-value-to-weight (low transport cost per dollar).

**Interpretation if test fails:** Complex products are generally harder to trade at distance (e.g., due to relationship-specificity). Would need to argue PF captures something beyond general trade costs.

---

## Test 4: Common Language x PCI (Placebo Friction)

**Hypothesis to reject:** The PCI interaction works with any bilateral friction, not just payment-related ones.

**Specification:** Replace $PF$ with a common language dummy (inverted: "no common language" = 1).

**Expected result:** $\alpha_2 \approx 0$. Language barriers may affect trade but should not differentially affect complex products through a payment mechanism.

**Interpretation if test fails:** Complex products may require more communication/coordination (plausible), but this is a different mechanism from payment friction. Would need to control for language barriers in the main specification.

---

## Test 5: SOS vs. Non-Payment Technology Adoption (Placebo Outcome)

**Hypothesis to reject:** SOS predicts adoption of technologies unrelated to payments.

**Specification:** Correlate country-level SOS with:
- Renewable energy capacity per capita
- EV adoption rates
- Broadband penetration
All conditional on GDP per capita.

**Expected result:** $\text{corr}(SOS_c, \text{Non-payment tech}_c | \text{GDPpc}_c) \approx 0$. If SOS captures payment-specific opportunity, it should not predict non-payment technology adoption after controlling for income.

**Interpretation if test fails:** SOS is just a proxy for "developing country modernization potential." Would need to show SOS predicts crypto/stablecoin adoption *above and beyond* general technology adoption.

---

## Test 6: Pre-Trends / Leads Test (Temporal Placebo)

**Hypothesis to reject:** Future changes in payment friction "predict" current trade patterns.

**Specification:**
$$X_{ijp,t} = \exp\left[\text{FEs} + \alpha_{+2}(PF_{ij,t+2} \times PCI_p) + \alpha_{+1}(PF_{ij,t+1} \times PCI_p) + \alpha_0(PF_{ij,t} \times PCI_p) + \alpha_{-1}(PF_{ij,t-1} \times PCI_p)\right] \times \varepsilon_{ijp,t}$$

**Expected result:** $\alpha_{+1} \approx 0$ and $\alpha_{+2} \approx 0$. Future friction changes should not predict current trade (conditional on current friction). $\alpha_0$ and $\alpha_{-1}$ should be significant.

**Interpretation if test fails:** Reverse causality -- trade patterns drive subsequent payment infrastructure investment. Would strengthen the case for IV/de-risking approach.

---

## Test 7: Commodity-Only Subsample (Subsample Falsification)

**Hypothesis to reject:** The PF x PCI interaction is driven by within-commodity variation.

**Specification:** Estimate Specification 3 restricted to HS chapters 1-27 (primary commodities, agriculture, minerals, fuels).

**Expected result:** $\alpha_2 \approx 0$ in this subsample. Commodities are:
- Low PCI (minimal within-subsample variation in complexity)
- Traded through established commodity channels (less sensitive to payment infrastructure)
- Often denominated in USD and traded on exchanges (bypass bilateral payment systems)

**Interpretation if test fails:** Payment frictions affect even commodity trade composition, which would actually strengthen the paper but require additional explanation.

---

## Summary Table

| Test | Placebo Element | Expected Result | Threat if Fails |
|------|----------------|-----------------|-----------------|
| 1 | Product weight as interaction | Null | PF proxies for general trade costs |
| 2 | Perishability as interaction | Null | PF proxies for trade facilitation |
| 3 | Distance as friction | Null or small | PCI interaction not payment-specific |
| 4 | Language as friction | Null | Complex products generally harder to trade |
| 5 | Non-payment tech as outcome | Null correlation | SOS = general development proxy |
| 6 | Future friction as predictor | Null on leads | Reverse causality |
| 7 | Commodity subsample | Null interaction | Mechanism broader than hypothesized |

---

## Reporting

Present falsification results in a single appendix table (or figure panel) showing:
- One row per test
- Coefficient, SE, p-value for the placebo interaction
- Comparison to the main result coefficient

Visual: "Specification curve" style plot with the main result highlighted and all placebos shown as a distribution of null results.
