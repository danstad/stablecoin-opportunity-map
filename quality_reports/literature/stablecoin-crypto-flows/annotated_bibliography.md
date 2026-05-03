# Annotated Bibliography: Stablecoins, Cryptocurrency, and Cross-Border Trade/Capital Flows

**Stream:** Stablecoins, Crypto, and Cross-Border Flows
**Date compiled:** 2026-04-03
**Compiled by:** Librarian agent (Stream 2 of literature search)
**Status:** DRAFT (pending librarian-critic review)

---

## Category 1: Stablecoins and Cross-Border Payments / Capital Flows

### Auer, Lewrick & Paulick (2025) --- DeFiying Gravity?
- **Journal:** BIS Working Papers No. 1265 (May 2025)
- **Proximity:** 2 (closely related, different angle)
- **Summary:** Investigates trends and drivers of cross-border flows of Bitcoin, Ether, Tether, and USD Coin between 184 countries from 2017 to 2024 using a gravity framework. Cross-border crypto flows peaked at ~USD 2.6 trillion in 2021, with stablecoins accounting for close to half. Finds speculative motives and global funding conditions drive native crypto flows, while transactional motives (remittances, payments) drive stablecoin flows. Geographic distance and linguistic barriers have a much smaller effect on crypto than on traditional flows. Capital flow management measures appear ineffective against crypto flows.
- **Identification strategy:** Augmented gravity model (PPML) with crypto-specific bilateral flow data from Chainalysis; push-pull factor decomposition
- **Key data:** Chainalysis bilateral crypto flow data, 184 countries, 2017--2024
- **Key finding:** Higher traditional remittance costs are strongly associated with larger stablecoin and low-value BTC cross-border flows; gravity frictions (distance, language) attenuated relative to traditional finance
- **Relevance:** Directly validates our premise that stablecoins substitute for high-friction traditional payment channels. Their gravity framework is methodological precedent for our gravity + payment friction approach. Key competitor paper -- we must differentiate by adding economic complexity dimension.

### Reuter (2025) --- How to Estimate International Stablecoin Flows
- **Journal:** IMF Working Paper 25/141 (July 2025)
- **Proximity:** 3 (related method)
- **Summary:** Develops a novel methodology leveraging AI and machine learning to estimate the geographic distribution of international stablecoin flows, overcoming the anonymity problem of on-chain data. Analyzes 2024 transactions totaling $2 trillion. Finds flows highest in North America ($633bn) and Asia-Pacific ($519bn); relative to GDP, most significant in Latin America and Caribbean (7.7%) and Africa/Middle East (6.7%). North America exhibits net outflows, meeting global dollar demand.
- **Identification strategy:** ML-based geographic attribution of blockchain transactions; comparison with Chainalysis commercial data
- **Key data:** On-chain stablecoin transactions (USDT, USDC), 2024
- **Key finding:** Stablecoin flows between EMDEs are largest by value; flows increase during dollar appreciation periods
- **Relevance:** Critical methodological reference for geographic attribution of stablecoin flows. The regional flow patterns directly inform which corridors our model should prioritize. Their ML approach for geolocating wallets is relevant if we use on-chain data.

### Aldasoro, Beltran & Grinberg (2026) --- Stablecoin Flows and Spillovers to FX Markets
- **Journal:** BIS Working Papers No. 1340 / IMF WP 26/056 (March 2026)
- **Proximity:** 3 (related method, different question)
- **Summary:** Documents spillovers from stablecoin-based FX markets to traditional FX markets using data on four USD-pegged stablecoins traded against 27 fiat currencies across 64 exchanges from 2021 to 2025. A 1% exogenous increase in net stablecoin inflows raises parity deviations by 40 basis points, depreciates the local currency, and widens covered interest parity deviations. Mechanism: intermediaries connecting stablecoin and traditional markets face limited balance sheet capacity.
- **Identification strategy:** IV approach exploiting exogenous variation in stablecoin inflows; high-frequency exchange data
- **Key data:** Four stablecoins x 27 fiat currencies x 64 exchanges, 2021--2025
- **Key finding:** 1% increase in net stablecoin inflows --> 40bp parity deviation, local currency depreciation
- **Relevance:** Establishes that stablecoin flows have real effects on exchange rates, validating the economic significance of stablecoin corridors. Relevant for understanding how stablecoin adoption could affect trade competitiveness through exchange rate channels.

### Cerutti, Firat, Hengge & Sagawa (2026) --- Stablecoin Shocks
- **Journal:** IMF Working Paper 26/044 (March 2026)
- **Proximity:** 3 (related, different question)
- **Summary:** Develops novel measures of stablecoin shocks using a daily narrative dataset of stablecoin-specific news combined with changes in USDC+USDT market capitalization. Uses heteroskedasticity-based identification within event-study and SVAR-IV framework. Finds stablecoin demand shocks trigger persistent declines in short-term Treasury yields, dollar depreciation, and spillovers into crypto/equity markets. Payment providers benefit; banks show no disintermediation risk.
- **Identification strategy:** Narrative identification + heteroskedasticity-based SVAR-IV
- **Key data:** Daily stablecoin news dataset, USDC/USDT market cap, US financial market data
- **Key finding:** Stablecoin demand shocks reduce short-term Treasury yields persistently; payment providers gain, banks unaffected
- **Relevance:** Establishes causal effects of stablecoin growth on financial markets. The payment provider angle is relevant for understanding disruption to incumbent cross-border payment infrastructure.

### Copestake, Englander, Martinez Peria & Villegas-Bauer (2026) --- Stablecoins and the Future of Payments
- **Journal:** IMF Working Paper 26/052 (March 2026)
- **Proximity:** 3 (related context)
- **Summary:** Examines whether financial markets expect stablecoins to play an important role in payments. Uses high-frequency stock price variation around US stablecoin legislation (GENIUS Act). Finds the legislation reduced market value of listed incumbent payment firms by 18% (~$300 billion). Effect is proportionally larger for incumbents focused on cross-border payments, smaller for those with network effects or crypto services.
- **Identification strategy:** Event study using stock market reactions to legislative events
- **Key data:** Stock prices of payment firms around GENIUS Act passage, 2025
- **Key finding:** 18% market value decline for incumbent payment firms; larger for cross-border-focused firms
- **Relevance:** Provides market-based evidence that stablecoins are expected to disrupt cross-border payments. The cross-border differential validates our focus on international payment frictions.

### Cerutti, Chen & Hengge (2024) --- A Primer on Bitcoin Cross-Border Flows
- **Journal:** IMF Working Paper 24/085 (April 2024)
- **Proximity:** 3 (related method and context)
- **Summary:** Provides detailed description of available methodologies and datasets for measuring Bitcoin cross-border flows, discusses crucial assumptions behind quantification. Uses both on-chain (Crystal, Chainalysis) and off-chain (LocalBitcoins) data. Finds Bitcoin cross-border flows respond differently from traditional capital flows; off-chain flows correlate with incentives to avoid capital flow restrictions.
- **Identification strategy:** Descriptive + push-pull factor analysis
- **Key data:** Crystal, Chainalysis on-chain data; LocalBitcoins off-chain data
- **Key finding:** Off-chain Bitcoin flows correlated with capital control circumvention; on-chain and off-chain flows respond to different drivers
- **Relevance:** Essential methodological reference for crypto flow measurement. Validates data sources we may use and highlights measurement challenges.

### Cerutti, Firat & Perez-Saiz (2025) --- Estimating the Impact of Digital Money on Cross-Border Flows
- **Journal:** IMF Fintech Notes 2025/002 (February 2025)
- **Proximity:** 2 (closely related)
- **Summary:** Performs empirical scenario analysis of the potential impact of digital money (including stablecoins) on the volume and transaction costs of cross-border payments. Assumes 60% reduction in transaction costs from digital money adoption. Uses elasticities estimated from remittances data to project changes in cross-border flow volumes on the intensive margin.
- **Identification strategy:** Scenario analysis with estimated cost elasticities from remittance data
- **Key data:** World Bank Remittance Prices Worldwide, cross-border payment volumes
- **Key finding:** 60% cost reduction --> significant increase in cross-border payment volumes, especially for corridors with highest current costs
- **Relevance:** Directly relevant to our payment friction analysis. Their cost-reduction estimates and elasticities can calibrate our gravity model's payment friction channel.

---

## Category 2: Stablecoins and Financial Inclusion / Dollarization

### Murakami & Viswanath-Natraj (2025) --- Cryptocurrencies in Emerging Markets: A Stablecoin Solution?
- **Journal:** Journal of International Money and Finance, Vol. 156 (2025)
- **Proximity:** 3 (related context)
- **Summary:** Examines costs and benefits of digital dollarization via stablecoins in emerging markets. Provides theoretical rationale for why EMs benefit from stablecoins. Empirically shows cryptocurrency adoption responds to sovereign default risk: higher CDS spreads lead to increased app downloads and usage. Dollar-backed stablecoins facilitate remittances at near-zero cost.
- **Identification strategy:** Theoretical model + empirical analysis of adoption response to sovereign risk (CDS spreads as IV)
- **Key data:** Crypto app download data, CDS spreads, country-level macro variables
- **Key finding:** Higher sovereign default risk drives stablecoin adoption in EMs; stablecoins reduce remittance costs to near-zero
- **Relevance:** Validates demand-side story: countries with macro instability and high payment frictions adopt stablecoins. This aligns with our hypothesis that stablecoin opportunity is highest where payment frictions and complexity gaps intersect.

### Copestake, Le, Tan, Papageorgiou, Peiris & Rawat (2025) --- Macro-Financial Impacts of Foreign Digital Money
- **Journal:** Economics Letters (2025); originally IMF WP 23/249
- **Proximity:** 4 (background)
- **Summary:** Develops a two-country New Keynesian model with endogenous currency substitution and financial frictions to examine the impact of a foreign stablecoin on a small developing economy. Finds that stablecoin introduction amplifies currency substitution, reduces bank intermediation, weakens monetary policy transmission, exacerbates recessionary shocks, and increases banking sector stress.
- **Identification strategy:** Two-country DSGE model calibration
- **Key data:** Model-based (no empirical estimation)
- **Key finding:** Foreign stablecoins amplify currency substitution and capital outflows during negative shocks in developing economies
- **Relevance:** Provides theoretical framework for understanding risks of stablecoin adoption. Relevant for our discussion of which countries face the most transformative effects from stablecoin-enabled trade.

### Rey (2025) --- Stablecoins, Tokens, and Global Dominance
- **Journal:** IMF Finance & Development, September 2025
- **Proximity:** 4 (background)
- **Summary:** Argues that stablecoins and tokenization could redraw the financial map, amplifying opportunity and risk. Notes Tether and USDC collectively hold more US Treasuries than Saudi Arabia. Discusses risks: dollarization, capital flow volatility, banking system weakening, and potential return to 19th-century world of competing private money issuers.
- **Identification strategy:** N/A (policy essay)
- **Key data:** IMF External Sector Report data on stablecoin Treasury holdings
- **Key finding:** Stablecoins may accelerate dollarization and increase exchange rate volatility in developing countries
- **Relevance:** High-profile framing of stablecoin geopolitical implications by a leading international macroeconomist. Useful for motivation section of our paper.

---

## Category 3: Crypto Regulation and Flows

### Aldasoro, Aquilina, Lewrick & Lim (2025) --- Stablecoin Growth: Policy Challenges and Approaches
- **Journal:** BIS Bulletin No. 108 (July 2025)
- **Proximity:** 4 (background)
- **Summary:** Documents rapid growth: stablecoins in active use soared from ~60 in mid-2024 to over 170, market cap from $125bn to $255bn. Discusses policy challenges: financial integrity, financial stability, monetary sovereignty. Notes foreign-currency stablecoins could erode FX regulation effectiveness. Argues "same risks, same regulation" principle has limitations; bespoke and potentially more restrictive frameworks needed.
- **Identification strategy:** N/A (policy analysis)
- **Key data:** BIS stablecoin market data
- **Key finding:** Rapid growth creates monetary sovereignty concerns; existing regulation insufficient
- **Relevance:** Documents the regulatory heterogeneity that creates differential stablecoin adoption patterns across countries -- a key source of variation in our model.

### IMF (2025) --- Understanding Stablecoins
- **Journal:** IMF Departmental Paper (December 2025) [already in bibliography]
- **Proximity:** 4 (background)
- **Note:** Already in Bibliography_base.bib. Comprehensive overview of stablecoin market developments, use cases, risks, and regulatory landscape. Key reference for institutional context.

---

## Category 4: Correspondent Banking De-Risking and Trade Finance

### Borchert, De Haas, Kirschenmann & Schultz (2024) --- Broken Relationships: De-Risking by Correspondent Banks and International Trade
- **Journal:** CEPR Discussion Paper 19373 / EBRD Working Paper 285 (2024)
- **Proximity:** 2 (closely related, different angle)
- **Summary:** Exploits proprietary information on severed correspondent banking relationships to assess how payment disruptions impede cross-border trade. When local banks lose correspondent access, their clients' export probability falls by 9.7pp on average, intensifying from 5.2pp immediately to 20.6pp after four years. Small firms hit hardest (12.7pp). Effects aggregate to lower product-level exports from exposed countries.
- **Identification strategy:** Staggered DiD exploiting timing of correspondent bank relationship terminations; firm-level treatment
- **Key data:** Proprietary correspondent banking termination data, firm-level export data, 2008--2020
- **Key finding:** Losing correspondent banking access reduces export probability by 9.7pp; 20.6pp after 4 years
- **Relevance:** Directly motivates our paper: correspondent banking de-risking creates the payment friction gaps that stablecoins can fill. The product-level export effect is exactly the mechanism we model. This paper provides the "problem" our paper offers a "solution" to.

---

## Category 5: Digital Payments and Trade (Gravity Framework)

### Liu & Chen (2025) --- Has FinTech Reshaped Global Trade? % UNVERIFIED (authors approximate)
- **Journal:** North American Journal of Economics and Finance, Vol. 17(1), March 2025
- **Proximity:** 3 (same method, different context)
- **Summary:** Investigates the role of fintech in promoting international trade using a theory-consistent structural gravity model with bilateral trade flows from 106 countries over 2014--2019. Finds fintech innovations disproportionately stimulate international trade compared to domestic trade, operating through trade cost reduction channels.
- **Identification strategy:** Structural gravity (PPML) with fintech index as trade cost shifter
- **Key data:** Bilateral trade flows, 106 countries, 2014--2019; fintech development indices
- **Key finding:** Fintech reduces trade costs and disproportionately promotes international over domestic trade
- **Relevance:** Direct methodological precedent for our approach: fintech (of which stablecoins are a subset) enters the gravity model as a trade cost reducer. We extend this by focusing specifically on stablecoin-relevant payment frictions and interacting with product complexity.

---

## Category 6: Stablecoin Financial Stability and Market Structure

### Ahmed, Clouse, Natalucci, Rebucci & Sun (2025) --- Stablecoins: A Revolutionary Payment Technology with Financial Risks
- **Journal:** NBER Working Paper 34475 (October 2025)
- **Proximity:** 4 (background)
- **Summary:** Discusses use cases and potential benefits of stablecoins for payment system efficiency and costs, analyzes substitutability with money market mutual funds and bank deposits. Studies financial stability risks of both GENIUS-compliant and unregulated stablecoins using empirical analysis and historical case studies. Includes novel LLM-based analysis of expert opinions from US podcast episodes.
- **Identification strategy:** Empirical analysis + historical case studies + LLM-based text analysis
- **Key data:** Stablecoin market data, historical stress episodes, US podcast transcripts (Jan--Jul 2025)
- **Key finding:** Stablecoins offer significant payment efficiency gains but pose financial stability risks depending on regulatory framework
- **Relevance:** Comprehensive overview of stablecoin payment benefits. Useful for framing the payment efficiency gains in our model and discussing why stablecoins reduce trade costs.

### Azzimonti & Quadrini (2025) --- Digital Economy, Stablecoins, and the Global Financial System
- **Journal:** NBER Working Paper 34066 (July 2025)
- **Proximity:** 4 (background, theoretical)
- **Summary:** Develops a multicountry model (US, rest of world, digital economy) to quantify impact of stablecoin expansion. Stablecoins may increase demand for safe dollar instruments (reserve backing) but also substitute for traditional reserve assets. In long run, reserve demand effect dominates, leading to lower US interest rates and greater US foreign borrowing. Digital economy expansion increases US consumption volatility while reducing it elsewhere.
- **Identification strategy:** Multicountry general equilibrium model calibration
- **Key data:** Model-based (no empirical estimation)
- **Key finding:** Reserve demand effect of stablecoins dominates substitution effect; lower US rates and more US borrowing in equilibrium
- **Relevance:** Provides general equilibrium context for how stablecoin expansion reshapes global financial architecture. Background for our macro motivation.

### Barthelemy, Gardin & Nguyen (2024) --- Stablecoins and the Financing of the Real Economy
- **Journal:** Banque de France Working Paper No. 908 (2024)
- **Proximity:** 4 (background)
- **Summary:** Documents that the largest stablecoins manage their dollar peg by holding short-term safe assets. Identifies changes in stablecoin demand for US commercial paper by exploiting cross-sectional and time-varying heterogeneity in reserve asset policies. Shows CP issuers responded to stablecoin demand by issuing more, with no impact on rates.
- **Identification strategy:** Cross-sectional and time-series variation in stablecoin reserve policies; difference-in-differences on CP issuance
- **Key data:** Commercial paper issuance data, stablecoin reserve disclosures
- **Key finding:** Stablecoin demand caused economically significant increase in CP issuance; no effect on CP rates
- **Relevance:** Demonstrates real-economy financing effects of stablecoins. Tangentially relevant for understanding how stablecoin growth affects dollar-denominated markets.

---

## Category 7: Foundational Crypto Market Research

### Makarov & Schoar (2020) --- Trading and Arbitrage in Cryptocurrency Markets
- **Journal:** Journal of Financial Economics, Vol. 135(2), pp. 293--319 (2020)
- **Proximity:** 5 (tangential/foundational)
- **Summary:** Documents large, persistent arbitrage opportunities across cryptocurrency exchanges, with price deviations varying by jurisdiction. These deviations are informative about capital flow frictions and the effectiveness of capital controls. The "Kimchi premium" (Korea) and similar country-specific premia reveal how fiat on/off-ramp frictions shape crypto markets.
- **Identification strategy:** Cross-exchange price comparison; geographic arbitrage measurement
- **Key data:** Exchange-level Bitcoin price data across major global exchanges
- **Key finding:** Persistent cross-exchange price deviations correlated with capital control intensity; 90% of Bitcoin volume is spurious
- **Relevance:** Foundational paper on geographic crypto price frictions. The country-level price premia they document are early evidence that crypto markets reflect underlying payment and capital flow frictions -- the same frictions we model.

### Makarov & Schoar (2021) --- Blockchain Analysis of the Bitcoin Market
- **Journal:** NBER Working Paper 29396 (2021)
- **Proximity:** 5 (tangential/foundational)
- **Summary:** Builds a novel database linking Bitcoin addresses to real entities using public and proprietary sources. Analyzes transaction volume, network structure, and concentration of main blockchain participants. Finds 90% of transactions are spurious (designed to impede tracing); of "real" volume, 75% is exchange-based trading/speculation.
- **Identification strategy:** Entity resolution via heuristic clustering and behavior-based classification
- **Key data:** Full Bitcoin blockchain + proprietary entity identification
- **Key finding:** Real Bitcoin transaction volume much smaller than reported; highly concentrated among few entities
- **Relevance:** Methodological reference for blockchain data quality. Their finding that most on-chain volume is spurious is a cautionary note for our data sourcing.

---

## Category 8: Institutional and Policy Context

### Kim, Ruprecht & Styczynski (2026) --- Payment Stablecoins and Cross-Border Payments
- **Journal:** FEDS Notes, Board of Governors of the Federal Reserve (March 30, 2026)
- **Proximity:** 4 (background)
- **Summary:** Examines benefits of payment stablecoins for cross-border payments and implications for monetary policy implementation following the GENIUS Act. Discusses how stablecoins could affect the market for domestic and foreign liquid assets, with implications for the central bank balance sheet. Some banks may replace reserve balances with stablecoin-related holdings.
- **Identification strategy:** N/A (institutional analysis)
- **Key data:** Federal Reserve balance sheet data, GENIUS Act regulatory text
- **Key finding:** Payment stablecoins could decrease demand for reserves while increasing demand for T-bills
- **Relevance:** Documents the post-GENIUS Act regulatory environment in the US, which is a key institutional feature affecting stablecoin-trade corridors involving the US.

### BIS (2023) --- Considerations for the Use of Stablecoin Arrangements in Cross-Border Payments
- **Journal:** BIS Committee on Payments and Market Infrastructures (October 2023)
- **Proximity:** 4 (background)
- **Summary:** Assesses opportunities and challenges of using stablecoins for cross-border payments. Identifies potential efficiency gains from faster settlement, lower costs, and 24/7 availability, but also risks related to financial stability, monetary sovereignty, and consumer protection.
- **Identification strategy:** N/A (policy report)
- **Key data:** Survey of central banks and payment system operators
- **Key finding:** Stablecoins offer cross-border payment opportunities but face governance, interoperability, and regulatory challenges
- **Relevance:** Institutional context for the payment infrastructure our model assumes stablecoins could improve.

### Azar, Baughman, Carapella et al. (2024) --- The Financial Stability Implications of Digital Assets
- **Journal:** Federal Reserve Bank of New York Economic Policy Review, Vol. 30(2), November 2024
- **Proximity:** 5 (tangential)
- **Summary:** Adapts the Federal Reserve's financial stability monitoring framework to digital assets. Documents fragility from valuation pressures, funding risk, widespread leverage use, and high interconnectedness within the crypto ecosystem.
- **Identification strategy:** Framework adaptation + descriptive analysis
- **Key data:** Crypto market data, DeFi protocol data
- **Key finding:** Digital asset ecosystem exhibits significant fragility across all four dimensions of the Fed's stability framework
- **Relevance:** Background on financial stability risks that constrain stablecoin adoption and shape regulatory responses.

---

## Summary Statistics

| Category | Papers | Avg Proximity |
|----------|--------|---------------|
| Cross-border stablecoin/crypto flows | 7 | 2.7 |
| Financial inclusion / dollarization | 3 | 3.7 |
| Crypto regulation | 2 | 4.0 |
| Correspondent banking / trade finance | 1 | 2.0 |
| Digital payments + gravity | 1 | 3.0 |
| Stablecoin financial stability | 3 | 4.0 |
| Foundational crypto research | 2 | 5.0 |
| Institutional/policy context | 3 | 4.3 |
| **Total** | **22** | **3.5** |

---

## Papers Already in Bibliography (not duplicated above)

- Cerutti, Obstfeld & Zhou (2024) --- Cross-Border Crypto Flows (IMF WP 24/261)
- Graf von Luckner, Reinhart & Rogoff (2023) --- New-Age Capital Flows (JME)
- Graf von Luckner, Koepke & Sgherri (2024) --- Capital Flight (IMF WP 24/133)
- IMF (2025) --- Understanding Stablecoins (Departmental Paper)

## Notes

- % UNVERIFIED: Liu & Chen (2025) --- exact author names need verification from the published version
- The BIS WP 1340 and IMF WP 26/056 (Aldasoro, Beltran & Grinberg) appear to be the same paper published at both institutions
- Several 2026 papers are very recent; citation counts not yet available
