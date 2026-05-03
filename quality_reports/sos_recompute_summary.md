# SOS Recompute Summary — 2026-05-02

Recomputed Stablecoin Opportunity Score using the three gamma estimates from
the 2026-04-06 panel pair-FE confounder estimation:
gamma_AMLD = +0.1414 (SE 0.0689); gamma_FATF = -0.1076 (SE 0.0649);
gamma_FDI = -0.1346 (SE 0.0664). The composite SOS is
SOS_composite = SOS_FATF + SOS_FDI - SOS_AMLD, where the AMLD term enters with
a minus sign so countries already covered by EU regulatory harmonization are
down-weighted (regulatory clarity is a partial substitute for stablecoins).

**Top-5 stability across rankings.** Composite top-5: ['HTI', 'FJI', 'SYR', 'LBN', 'NIC'].
Of these, 4/5 also appear in the FDI-only top-5 (['FJI', 'HTI', 'NIC', 'MDG', 'LBN']) and
0/5 also appear in the FATF-only top-5 (['HRV', 'TUR', 'BGR', 'JOR', 'BRB']).
Spearman rank correlations: rho(FDI, composite) = 0.487,
rho(FATF, composite) = 0.429,
rho(FDI, FATF) = 0.249. Quintile shifts vs composite:
FDI -> composite reassigns 152 of 226 countries to a
different quintile; FATF -> composite reassigns 155. The two
single-instrument rankings are themselves only weakly correlated
(rho(FDI, FATF) = 0.249), reflecting that FATF
greylisting and FDI-derisking identify substantively different sets of
exposed countries. The composite therefore *necessarily* re-orders the
rankings — by design — and the paper should defend it as a
weighted-evidence aggregator rather than claim "robust to gamma choice."
