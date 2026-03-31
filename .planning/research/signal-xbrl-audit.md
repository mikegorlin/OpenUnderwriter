# Signal XBRL Audit — v3.1 Planning

## Summary
- 230/400 signals audited (fin, biz, fwrd, exec, gov/insider, gov/board, gov/effect)
- Remaining: lit/, stock/, nlp/, gov/pay, gov/rights (~170 signals, est. 25 more candidates)

## Bucket A: XBRL-Replaceable (45 signals)
Direct swap from LLM extraction to structured XBRL concepts.

Key signals: FIN.LIQ.position, FIN.LIQ.working_capital, FIN.DEBT.structure, FIN.DEBT.coverage, FIN.DEBT.maturity, FIN.PROFIT.revenue, FIN.PROFIT.margins, FIN.TEMPORAL.revenue_deceleration, FIN.TEMPORAL.margin_compression, FIN.TEMPORAL.operating_margin_compression, FIN.TEMPORAL.cfo_ni_divergence, FIN.TEMPORAL.profitability_trend, FIN.TEMPORAL.cash_flow_deterioration, FIN.FORENSIC.fis_composite, FIN.FORENSIC.enhanced_sloan, FIN.FORENSIC.accrual_intensity, FIN.QUALITY.dso_ar_divergence, FIN.QUALITY.q4_revenue_concentration, FIN.QUALITY.quality_of_earnings, BIZ.SIZE.market_cap, BIZ.DEPEND.customer_conc, BIZ.MODEL.revenue_segment, BIZ.MODEL.revenue_geo

## Bucket B: XBRL-Enhanceable (28 signals)
XBRL for numbers, LLM for narrative context.

Key signals: FIN.ACCT.restatement, FIN.ACCT.auditor_opinion, FIN.ACCT.material_weakness, FIN.DEBT.credit_rating, FIN.DEBT.covenants, GOV.BOARD.independence, GOV.EXEC.ceo_profile, GOV.EXEC.cfo_profile

## Bucket C: Web-Search-Candidate (35 signals)
External/qualitative data via Brave Search + Exa.

Key signals: GOV.BOARD.prior_litigation, GOV.BOARD.character_conduct, GOV.EXEC.character_conduct, FWRD.WARN.whistleblower_exposure, FWRD.WARN.social_sentiment, FWRD.WARN.journalism_activity, FWRD.WARN.glassdoor_sentiment

## Bucket D: LLM-Only (68 signals)
Narrative interpretation — correct choice, no change needed.

## Bucket E: Broken/Skipped (24 signals)
Could reactivate with XBRL or web search data.

Key signals: GOV.EFFECT.late_filing, GOV.EFFECT.nt_filing, GOV.INSIDER.plan_adoption, GOV.INSIDER.unusual_timing, FIN.QUALITY.q4_revenue_concentration, FIN.QUALITY.deferred_revenue_trend, FWRD.WARN.cfpb_complaints, FWRD.WARN.fda_medwatch

## Bucket F: New Signal Opportunities (12+)
1. FIN.QUALITY.revenue_recognition_risk (ASC 606)
2. FIN.FORENSIC.level3_fair_value_concentration (ASC 820)
3. FIN.DEBT.pension_underfunded_risk (ASC 715)
4. FIN.DEBT.operating_lease_burden (ASC 842)
5. FIN.FORENSIC.goodwill_deterioration_pattern
6. FIN.QUALITY.stock_comp_dilution_rate (ASC 718)
7. FIN.FORENSIC.related_party_revenue_concentration (ASC 850)
8. GOV.INSIDER.trading_pattern_deviation (Form 4)
9. GOV.INSIDER.option_exercise_sell_pattern (Form 4)
10. STOCK.PATTERN.peer_valuation_gap (Frames API)
11. FIN.GUIDE.estimate_revision_pattern
12. FWRD.EVENT.ma_integration_risk_score

## Impact Estimate
- 73 signals materially improved (45 replaced + 28 enhanced)
- 24 broken signals potentially reactivated
- 12+ new signals for currently-blind risk areas
- Net: ~110 signal improvements out of 400 total
