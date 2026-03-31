# Complete Check Inventory -- checks.json (388 checks)

**Schema**: BRAIN_CHECKS_V7 v9.0.0
**Last Updated**: 2026-02-12
**Total Checks**: 388

This document lists every check in the system. Use it to decide what to keep, remove, merge, or add.

## Global Summary

### By Content Type

| Content Type | Count | Description |
|---|---|---|
| EVALUATIVE_CHECK | 305 | Has red/yellow/clear thresholds, produces a risk signal |
| MANAGEMENT_DISPLAY | 64 | Context/display data, no risk evaluation |
| INFERENCE_PATTERN | 19 | Multi-signal pattern detection, combines multiple inputs |

### By Depth

| Depth | Count | Description |
|---|---|---|
| 1 | 20 | Core identification/classification |
| 2 | 270 | Standard analysis |
| 3 | 54 | Deep dive |
| 4 | 44 | Comprehensive/advanced |

### By Prefix Category

| Prefix | Count | MGMT_DISPLAY | EVAL_CHECK | INFER_PATTERN | With Factors | No Factors | Has field_key |
|---|---|---|---|---|---|---|---|
| **BIZ** | 40 | 29 | 11 | 0 | 11 | 29 | 40 |
| **EXEC** | 20 | 4 | 13 | 3 | 16 | 4 | 0 |
| **FIN** | 58 | 0 | 58 | 0 | 58 | 0 | 35 |
| **FWRD** | 83 | 19 | 64 | 0 | 64 | 19 | 0 |
| **GOV** | 81 | 0 | 71 | 10 | 81 | 0 | 81 |
| **LIT** | 56 | 0 | 56 | 0 | 56 | 0 | 56 |
| **NLP** | 15 | 5 | 10 | 0 | 10 | 5 | 0 |
| **STOCK** | 35 | 7 | 22 | 6 | 28 | 7 | 35 |
| **TOTAL** | **388** | **64** | **305** | **19** | **324** | **64** | **247** |

### Factor Coverage (F1-F10)

| Factor | Name | Checks Mapped |
|---|---|---|
| F1 | Securities Class Action History | 45 |
| F2 | Financial Condition | 25 |
| F3 | Corporate Governance | 56 |
| F4 | Industry Risk | 13 |
| F5 | Stock Volatility | 27 |
| F6 | Growth/Earnings | 17 |
| F7 | Insider Activity | 27 |
| F8 | M&A/Restructuring | 9 |
| F9 | Regulatory/Compliance | 39 |
| F10 | Emerging/Forward Risk | 109 |
| -- | *(no factor mapping)* | 64 |

### Threshold Types

| Threshold Type | Count | Description |
|---|---|---|
| boolean | 19 | Yes/no with risk meaning |
| classification | 5 | Categorical classification |
| count | 3 | Count-based thresholds |
| display | 8 | Display value only |
| info | 17 | Informational display only |
| multi_period | 1 | Multi-horizon comparison |
| pattern | 6 | Pattern detection with triggers |
| percentage | 11 | Percentage-based thresholds |
| search | 1 | Requires external search execution |
| temporal | 10 | Time-series trend analysis |
| tiered | 303 | Red/yellow/clear risk levels |
| value | 4 | Dollar/numeric value thresholds |

### Checks with Tiered Type but No Criteria Defined (190)

These checks have `threshold.type: tiered` but no `red`, `yellow`, or `clear` values defined.
They are effectively placeholder checks that cannot evaluate.

- `STOCK.ANALYST.momentum`
- `STOCK.INSIDER.notable_activity`
- `STOCK.INSIDER.cluster_timing`
- `STOCK.OWN.concentration`
- `STOCK.OWN.activist`
- `STOCK.SHORT.trend`
- `STOCK.SHORT.report`
- `STOCK.TRADE.liquidity`
- `STOCK.TRADE.volume_patterns`
- `STOCK.TRADE.options`
- `STOCK.VALUATION.pe_ratio`
- `STOCK.VALUATION.ev_ebitda`
- `STOCK.VALUATION.premium_discount`
- `STOCK.VALUATION.peg_ratio`
- `FIN.PROFIT.trend`
- `FIN.ACCT.auditor`
- `FIN.ACCT.internal_controls`
- `FIN.ACCT.sec_correspondence`
- `FIN.ACCT.quality_indicators`
- `FIN.ACCT.earnings_manipulation`
- `FIN.GUIDE.current`
- `FIN.GUIDE.philosophy`
- `FIN.GUIDE.earnings_reaction`
- `FIN.GUIDE.analyst_consensus`
- `FIN.SECTOR.energy`
- `FIN.SECTOR.retail`
- `LIT.REG.state_ag`
- `LIT.REG.subpoena`
- `LIT.REG.comment_letters`
- `LIT.REG.deferred_pros`
- `LIT.REG.wells_notice`
- `LIT.REG.consent_order`
- `LIT.REG.cease_desist`
- `LIT.REG.civil_penalty`
- `LIT.REG.dol_audit`
- `LIT.REG.epa_action`
- `LIT.REG.osha_citation`
- `LIT.REG.cfpb_action`
- `LIT.REG.fdic_order`
- `LIT.REG.fda_warning`
- `LIT.REG.foreign_gov`
- `LIT.REG.state_action`
- `LIT.OTHER.product`
- `LIT.OTHER.employment`
- `LIT.OTHER.ip`
- `LIT.OTHER.environmental`
- `LIT.OTHER.contract`
- `LIT.OTHER.aggregate`
- `LIT.OTHER.class_action`
- `LIT.OTHER.antitrust`
- `LIT.OTHER.trade_secret`
- `LIT.OTHER.whistleblower`
- `LIT.OTHER.cyber_breach`
- `LIT.OTHER.bankruptcy`
- `LIT.OTHER.foreign_suit`
- `LIT.OTHER.gov_contract`
- `GOV.BOARD.tenure`
- `GOV.BOARD.overboarding`
- `GOV.BOARD.departures`
- `GOV.BOARD.attendance`
- `GOV.BOARD.expertise`
- `GOV.BOARD.refresh_activity`
- `GOV.BOARD.meetings`
- `GOV.BOARD.committees`
- `GOV.BOARD.succession`
- `GOV.PAY.ceo_total`
- `GOV.PAY.ceo_structure`
- `GOV.PAY.peer_comparison`
- `GOV.PAY.clawback`
- `GOV.PAY.related_party`
- `GOV.PAY.golden_para`
- `GOV.PAY.incentive_metrics`
- `GOV.PAY.equity_burn`
- `GOV.PAY.hedging`
- `GOV.PAY.perks`
- `GOV.PAY.401k_match`
- `GOV.PAY.deferred_comp`
- `GOV.PAY.pension`
- `GOV.PAY.exec_loans`
- `GOV.RIGHTS.dual_class`
- `GOV.RIGHTS.voting_rights`
- `GOV.RIGHTS.bylaws`
- `GOV.RIGHTS.takeover`
- `GOV.RIGHTS.proxy_access`
- `GOV.RIGHTS.forum_select`
- `GOV.RIGHTS.supermajority`
- `GOV.RIGHTS.action_consent`
- `GOV.RIGHTS.special_mtg`
- `GOV.RIGHTS.classified`
- `GOV.ACTIVIST.13d_filings`
- `GOV.ACTIVIST.campaigns`
- `GOV.ACTIVIST.proxy_contests`
- `GOV.ACTIVIST.settle_agree`
- `GOV.ACTIVIST.short_activism`
- `GOV.ACTIVIST.demands`
- `GOV.ACTIVIST.schedule_13g`
- `GOV.ACTIVIST.wolf_pack`
- `GOV.ACTIVIST.board_seat`
- `GOV.ACTIVIST.dissident`
- `GOV.ACTIVIST.withhold`
- `GOV.ACTIVIST.proposal`
- `GOV.ACTIVIST.consent`
- `GOV.ACTIVIST.standstill`
- `GOV.EFFECT.audit_committee`
- `GOV.EFFECT.audit_opinion`
- `GOV.EFFECT.auditor_change`
- `GOV.EFFECT.material_weakness`
- `GOV.EFFECT.iss_score`
- `GOV.EFFECT.proxy_advisory`
- `GOV.EFFECT.sox_404`
- `GOV.EFFECT.sig_deficiency`
- `GOV.EFFECT.late_filing`
- `GOV.EFFECT.nt_filing`
- `GOV.INSIDER.form4_filings`
- `GOV.INSIDER.10b5_plans`
- `GOV.INSIDER.plan_adoption`
- `GOV.INSIDER.cluster_sales`
- `GOV.INSIDER.unusual_timing`
- `GOV.INSIDER.executive_sales`
- `GOV.INSIDER.ownership_pct`
- `FWRD.EVENT.customer_retention`
- `FWRD.EVENT.employee_retention`
- `FWRD.EVENT.integration`
- `FWRD.EVENT.proxy_deadline`
- `FWRD.EVENT.19-BIOT`
- `FWRD.EVENT.20-BIOT`
- `FWRD.EVENT.21-BIOT`
- `FWRD.EVENT.22-HLTH`
- `FWRD.WARN.glassdoor_sentiment`
- `FWRD.WARN.indeed_reviews`
- `FWRD.WARN.blind_posts`
- `FWRD.WARN.linkedin_headcount`
- `FWRD.WARN.linkedin_departures`
- `FWRD.WARN.g2_reviews`
- `FWRD.WARN.trustpilot_trend`
- `FWRD.WARN.app_ratings`
- `FWRD.WARN.cfpb_complaints`
- `FWRD.WARN.fda_medwatch`
- `FWRD.WARN.nhtsa_complaints`
- `FWRD.WARN.social_sentiment`
- `FWRD.WARN.journalism_activity`
- `FWRD.WARN.whistleblower_exposure`
- `FWRD.WARN.vendor_payment_delays`
- `FWRD.WARN.job_posting_patterns`
- `FWRD.WARN.compliance_hiring`
- `FWRD.WARN.legal_hiring`
- `FWRD.WARN.zone_of_insolvency`
- `FWRD.WARN.goodwill_risk`
- `FWRD.WARN.impairment_risk`
- `FWRD.WARN.ai_revenue_concentration`
- `FWRD.WARN.hyperscaler_dependency`
- `FWRD.WARN.gpu_allocation`
- `FWRD.WARN.data_center_risk`
- `FWRD.WARN.contract_disputes`
- `FWRD.WARN.customer_churn_signals`
- `FWRD.WARN.partner_stability`
- `FWRD.WARN.revenue_quality`
- `FWRD.WARN.margin_pressure`
- `FWRD.WARN.capex_discipline`
- `FWRD.WARN.working_capital_trends`
- `FWRD.MACRO.sector_performance`
- `FWRD.MACRO.peer_issues`
- `FWRD.MACRO.industry_consolidation`
- `FWRD.MACRO.disruptive_tech`
- `FWRD.MACRO.interest_rate_sensitivity`
- `FWRD.MACRO.inflation_impact`
- `FWRD.MACRO.fx_exposure`
- `FWRD.MACRO.commodity_impact`
- `FWRD.MACRO.labor_market`
- `FWRD.MACRO.regulatory_changes`
- `FWRD.MACRO.legislative_risk`
- `FWRD.MACRO.trade_policy`
- `FWRD.MACRO.geopolitical_exposure`
- `FWRD.MACRO.supply_chain_disruption`
- `FWRD.MACRO.climate_transition_risk`
- `FWRD.DISC.risk_factor_evolution`
- `FWRD.DISC.mda_depth`
- `FWRD.DISC.non_gaap_reconciliation`
- `FWRD.DISC.segment_consistency`
- `FWRD.DISC.related_party_completeness`
- `FWRD.DISC.metric_consistency`
- `FWRD.DISC.guidance_methodology`
- `FWRD.DISC.sec_comment_letters`
- `FWRD.DISC.disclosure_quality_composite`
- `FWRD.NARRATIVE.10k_vs_earnings`
- `FWRD.NARRATIVE.investor_vs_sec`
- `FWRD.NARRATIVE.analyst_skepticism`
- `FWRD.NARRATIVE.short_thesis`
- `FWRD.NARRATIVE.auditor_cams`
- `FWRD.NARRATIVE.narrative_coherence_composite`

---

## BIZ -- 40 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 29 |
| EVALUATIVE_CHECK | 11 |
| INFERENCE_PATTERN | 0 |
| With factor mappings | 11 |
| Without factor mappings | 29 |

### BIZ.CLASS (3 checks)

**1. `BIZ.CLASS.primary`** -- Primary D&O Risk Classification
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `risk_classification`
- Threshold: classify: BINARY_EVENT, GROWTH_DARLING, GUIDANCE_DEPENDENT, REGULATORY_SENSITIVE, TRANSFORMATION, STABLE_MATURE, DISTRESSED

**2. `BIZ.CLASS.secondary`** -- Secondary Risk Classification
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `risk_classification`
- Threshold: classify: 

**3. `BIZ.CLASS.litigation_history`** -- Litigation History Profile
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `total_sca_count`
- Threshold: RED: Prior SCA within 3 years / YEL: Prior SCA within 5 years / CLR: No SCA history in 5+ years

### BIZ.COMP (11 checks)

**1. `BIZ.COMP.market_position`** -- Sector Classification
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `sector`
- Threshold: info/display

**2. `BIZ.COMP.market_share`** -- Sector ETF Benchmark
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `sector`
- Threshold: info/display

**3. `BIZ.COMP.competitive_advantage`** -- Peer Group
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `sector`
- Threshold: info/display

**4. `BIZ.COMP.threat_assessment`** -- Market Position
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `sector`
- Threshold: classify: Leader, Challenger, Niche

**5. `BIZ.COMP.barriers_entry`** -- Market Share
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `barriers_to_entry`
- Threshold: RED: Leadership claimed without support / YEL: Share declining

**6. `BIZ.COMP.moat`** -- Competitive Moat
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `competitive_moat`
- Threshold: RED: NONE + premium valuation / YEL: WEAK

**7. `BIZ.COMP.barriers`** -- Barriers to Entry
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `barriers_to_entry`
- Threshold: YEL: LOW + premium valuation

**8. `BIZ.COMP.industry_growth`** -- Industry Growth Rate
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `sector`
- Threshold: RED: Growth claims >2x industry / YEL: Company < industry

**9. `BIZ.COMP.headwinds`** -- Industry Headwinds/Tailwinds
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `industry_headwinds`
- Threshold: RED: SEVERE headwinds / YEL: MODERATE

**10. `BIZ.COMP.consolidation`** -- Consolidation Trend
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `sector`
- Threshold: YEL: Target characteristics

**11. `BIZ.COMP.peer_litigation`** -- Peer Litigation Frequency
- Content Type: MANAGEMENT_DISPLAY
- Depth: 4
- Factors: none
- field_key: `active_sca_count`
- Threshold: RED: >20% sued / YEL: >10%

### BIZ.DEPEND (10 checks)

**1. `BIZ.DEPEND.customer_conc`** -- Customer Concentration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `customer_concentration`
- Threshold: RED: >25% from top customer / YEL: >15% from top customer / CLR: <15% from top customer

**2. `BIZ.DEPEND.supplier_conc`** -- Top 5 Customers Concentration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `supplier_concentration`
- Threshold: RED: >50% / YEL: >35%

**3. `BIZ.DEPEND.tech_dep`** -- Government Contract Percentage
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `technology_dependency`
- Threshold: YEL: >30%

**4. `BIZ.DEPEND.key_person`** -- Customer Concentration Risk Composite
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `employee_count`
- Threshold: RED: HIGH / YEL: MODERATE

**5. `BIZ.DEPEND.regulatory_dep`** -- Single-Source Suppliers
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `regulatory_dependency`
- Threshold: RED: Yes (critical) / YEL: Disclosed risk

**6. `BIZ.DEPEND.capital_dep`** -- Key Supplier Dependencies
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `capital_dependency`
- Threshold: YEL: Disclosed as risk

**7. `BIZ.DEPEND.macro_sensitivity`** -- Supply Chain Complexity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `macro_sensitivity`
- Threshold: YEL: HIGH complexity

**8. `BIZ.DEPEND.distribution`** -- Product Concentration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `distribution_channels`
- Threshold: RED: >70% / YEL: >50%

**9. `BIZ.DEPEND.contract_terms`** -- Key Partnerships
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `contract_terms`
- Threshold: RED: Partner >25% revenue / YEL: >15%

**10. `BIZ.DEPEND.labor`** -- Concentration Risk Composite
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `employee_count`
- Threshold: RED: 3+ flags / YEL: 2 flags

### BIZ.MODEL (8 checks)

**1. `BIZ.MODEL.description`** -- Business Description
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `business_description`
- Threshold: info/display

**2. `BIZ.MODEL.revenue_type`** -- Revenue Model Type
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `revenue_type_analysis`
- Threshold: RED: >80% project-based / YEL: >80% transactional / CLR: Mixed or recurring

**3. `BIZ.MODEL.revenue_segment`** -- Revenue Mix by Segment
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `revenue_segment_breakdown`
- Threshold: YEL: Single segment >80%

**4. `BIZ.MODEL.revenue_geo`** -- Revenue Mix by Geography
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `revenue_geographic_mix`
- Threshold: YEL: Single country >70% (ex-US)

**5. `BIZ.MODEL.cost_structure`** -- Cost Structure
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `cost_structure_analysis`
- Threshold: RED: Fixed >70% + declining revenue / YEL: Fixed >70%

**6. `BIZ.MODEL.leverage_ops`** -- Operating Leverage Assessment
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `operating_leverage`
- Threshold: RED: HIGH (earnings swing >2x revenue swing) / YEL: ELEVATED (1.5-2x)

**7. `BIZ.MODEL.regulatory_dep`** -- Regulatory Dependency
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `model_regulatory_dependency`
- Threshold: RED: Entire model depends on regulatory approval / YEL: Material exposure

**8. `BIZ.MODEL.capital_intensity`** -- Capital Intensity
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `capital_intensity_ratio`
- Threshold: RED: CapEx >20% + utilization <60% / YEL: Either alone

### BIZ.SIZE (5 checks)

**1. `BIZ.SIZE.market_cap`** -- Market Capitalization
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `market_cap`
- Threshold: classify: Mega >$200B, Large $10-200B, Mid $2-10B, Small $300M-2B, Micro <$300M

**2. `BIZ.SIZE.revenue_ttm`** -- Revenue TTM
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `section_summary`
- Threshold: info/display

**3. `BIZ.SIZE.employees`** -- Employee Count
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `employee_count`
- Threshold: RED: <100 with public costs / YEL: Significant decline

**4. `BIZ.SIZE.growth_trajectory`** -- Public Company Tenure
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `years_public`
- Threshold: RED: <2 years since IPO / YEL: 2-5 years

**5. `BIZ.SIZE.public_tenure`** -- Revenue Growth YoY
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `years_public`
- Threshold: RED: Negative + decelerating / YEL: Decelerating from high base

### BIZ.UNI (3 checks)

**1. `BIZ.UNI.ai_claims`** -- AI Claims
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `ai_risk_exposure`
- Threshold: RED: Specific AI revenue/benefit claims / YEL: General AI capabilities claims / CLR: No AI claims

**2. `BIZ.UNI.cyber_posture`** -- Cyber Security Posture
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `cybersecurity_posture`
- Threshold: RED: Prior breach or inadequate disclosure / YEL: Standard cyber risk factors / CLR: Robust cyber program described

**3. `BIZ.UNI.cyber_business`** -- Cyber Business Impact
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `cyber_business_risk`
- Threshold: info/display

---

## EXEC -- 20 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 4 |
| EVALUATIVE_CHECK | 13 |
| INFERENCE_PATTERN | 3 |
| With factor mappings | 16 |
| Without factor mappings | 4 |

### EXEC.AGGREGATE (2 checks)

**1. `EXEC.AGGREGATE.board_risk`** -- Board Aggregate Risk Score
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F9
- field_key: `none`
- Threshold: RED: Score >= 50 (elevated) / YEL: Score >= 35 (moderate) / CLR: Score < 35

**2. `EXEC.AGGREGATE.highest_risk_individual`** -- Highest Individual Risk Score Exceeds Threshold
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F9
- field_key: `none`
- Threshold: RED: Individual score >= 40 / YEL: Individual score >= 25 / CLR: Below 25

### EXEC.CEO (1 checks)

**1. `EXEC.CEO.risk_score`** -- CEO Individual Risk Score
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F9, F10
- field_key: `none`
- Threshold: RED: Score >= 30 / YEL: Score >= 15 / CLR: Below 15

### EXEC.CFO (1 checks)

**1. `EXEC.CFO.risk_score`** -- CFO Individual Risk Score
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F9, F10
- field_key: `none`
- Threshold: RED: Score >= 30 / YEL: Score >= 15 / CLR: Below 15

### EXEC.DEPARTURE (2 checks)

**1. `EXEC.DEPARTURE.cfo_departure_timing`** -- CFO Departure Coinciding With Stress Signals
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10, F3
- field_key: `none`
- Threshold: boolean

**2. `EXEC.DEPARTURE.cao_departure`** -- Chief Accounting Officer Departure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10, F3
- field_key: `none`
- Threshold: boolean

### EXEC.INSIDER (4 checks)

**1. `EXEC.INSIDER.ceo_net_selling`** -- CEO Net Seller of Stock
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6, F9
- field_key: `none`
- Threshold: RED: Selling pct > 80% / YEL: Selling pct > 50% / CLR: Selling pct <= 50%

**2. `EXEC.INSIDER.cfo_net_selling`** -- CFO Net Seller of Stock
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6, F9
- field_key: `none`
- Threshold: RED: Selling pct > 80% / YEL: Selling pct > 50% / CLR: Net buyer or neutral

**3. `EXEC.INSIDER.cluster_selling`** -- Multiple Officers Selling Within 30 Days
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F6, F9
- field_key: `none`
- Threshold: boolean

**4. `EXEC.INSIDER.non_10b51`** -- Discretionary Selling (Not 10b5-1 Plan)
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F6, F9
- field_key: `none`
- Threshold: RED: >50% sales discretionary / YEL: Any discretionary sales / CLR: All under 10b5-1

### EXEC.PRIOR_LIT (2 checks)

**1. `EXEC.PRIOR_LIT.any_officer`** -- Any Officer With Prior Litigation at Previous Company
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F9
- field_key: `none`
- Threshold: boolean

**2. `EXEC.PRIOR_LIT.ceo_cfo`** -- CEO or CFO With Prior Litigation
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F9
- field_key: `none`
- Threshold: boolean

### EXEC.PROFILE (5 checks)

**1. `EXEC.PROFILE.board_size`** -- Board Size (Number of Members)
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Number of board members

**2. `EXEC.PROFILE.avg_tenure`** -- Average Executive Tenure
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Average tenure in years

**3. `EXEC.PROFILE.ceo_chair_duality`** -- CEO Also Chairs Board
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: boolean

**4. `EXEC.PROFILE.independent_ratio`** -- Board Independence Percentage
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Percentage of independent directors

**5. `EXEC.PROFILE.overboarded_directors`** -- Directors Serving on 4+ Boards
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: RED: 2+ directors overboarded / YEL: 1 director overboarded / CLR: No overboarding

### EXEC.TENURE (3 checks)

**1. `EXEC.TENURE.ceo_new`** -- CEO Tenure Less Than 2 Years
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: RED: Tenure < 1 year / YEL: Tenure < 2 years / CLR: Tenure >= 2 years

**2. `EXEC.TENURE.cfo_new`** -- CFO Tenure Less Than 2 Years
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: RED: Tenure < 1 year / YEL: Tenure < 2 years / CLR: Tenure >= 2 years

**3. `EXEC.TENURE.c_suite_turnover`** -- Multiple C-Suite Departures in 12 Months
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `none`
- Threshold: RED: 3+ C-suite departures in 12mo / YEL: 2 C-suite departures in 12mo / CLR: 0-1 departures

---

## FIN -- 58 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 0 |
| EVALUATIVE_CHECK | 58 |
| INFERENCE_PATTERN | 0 |
| With factor mappings | 58 |
| Without factor mappings | 0 |

### FIN.ACCT (13 checks)

**1. `FIN.ACCT.auditor`** -- Auditor
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `auditor_opinion`
- Threshold: tiered (no criteria defined)

**2. `FIN.ACCT.internal_controls`** -- Internal Controls
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `material_weaknesses`
- Threshold: tiered (no criteria defined)

**3. `FIN.ACCT.restatement`** -- Restatement History
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `restatements`
- Threshold: RED: Restatement in past 3 years / YEL: Restatement in past 5 years / CLR: No restatements

**4. `FIN.ACCT.restatement_magnitude`** -- Restatement Revenue Impact
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `restatements`
- Threshold: RED: >5% / YEL: >2% / CLR: <=2%

**5. `FIN.ACCT.restatement_pattern`** -- Repeat Restatement Pattern
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `restatements`
- Threshold: RED: >1 / YEL: 1

**6. `FIN.ACCT.restatement_auditor_link`** -- Restatement-Auditor Change Correlation
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `restatement_auditor_link`
- Threshold: RED: Restatement coinciding with auditor change / CLR: No restatement-auditor change correlation

**7. `FIN.ACCT.material_weakness`** -- Material Weakness in Internal Controls
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `material_weaknesses`
- Threshold: RED: Material weakness disclosed in Item 9A / CLR: No material weakness disclosed

**8. `FIN.ACCT.auditor_disagreement`** -- Auditor Disagreement Letter
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `auditor_disagreement`
- Threshold: RED: Auditor change with disagreement letter filed / CLR: No auditor disagreement letters

**9. `FIN.ACCT.auditor_attestation_fail`** -- Failed Auditor Attestation on Internal Controls
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `auditor_attestation_fail`
- Threshold: RED: Auditor unable to attest to internal control effectiveness under SOX 404 / CLR: Auditor attested to effective internal controls

**10. `FIN.ACCT.restatement_stock_window`** -- Restatement Within Stock Drop Window
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `restatement_stock_window`
- Threshold: RED: Restatement within 90 days of significant stock decline creating class period exposure / CLR: No restatement-stock drop temporal overlap

**11. `FIN.ACCT.sec_correspondence`** -- Sec Correspondence
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

**12. `FIN.ACCT.quality_indicators`** -- Quality Indicators
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `altman_z_score`
- Threshold: tiered (no criteria defined)

**13. `FIN.ACCT.earnings_manipulation`** -- Earnings Manipulation
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `beneish_m_score`
- Threshold: tiered (no criteria defined)

### FIN.DEBT (5 checks)

**1. `FIN.DEBT.structure`** -- Debt Structure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `debt_to_ebitda`
- Threshold: RED: Debt/EBITDA >6x OR Debt/Equity >3x / YEL: Debt/EBITDA >4x OR Debt/Equity >2x / CLR: Otherwise

**2. `FIN.DEBT.coverage`** -- Debt Service Coverage
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `interest_coverage`
- Threshold: RED: Interest coverage <1.5x OR fixed charge coverage <1.0x / YEL: Interest coverage <2.5x OR below sector 25th percentile / CLR: Otherwise

**3. `FIN.DEBT.maturity`** -- Debt Maturity Profile
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `refinancing_risk`
- Threshold: RED: >30% due within 24 months OR any material maturity <12 months / YEL: >20% due within 24 months OR maturity <24 months / CLR: Otherwise

**4. `FIN.DEBT.credit_rating`** -- Credit Ratings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `debt_structure`
- Threshold: RED: CCC/Caa or below OR downgraded in last 12 months / YEL: B rating OR negative outlook OR high yield / CLR: BBB/Baa or above with stable/positive outlook

**5. `FIN.DEBT.covenants`** -- Covenant Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `debt_structure`
- Threshold: RED: Breach/default OR <10% headroom OR multiple waivers / YEL: <20% headroom OR any waiver/amendment in 12 months / CLR: Otherwise

### FIN.FORENSIC (6 checks)

**1. `FIN.FORENSIC.fis_composite`** -- Financial Integrity Score Composite
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: > -1.78 / YEL: > -2.22 / CLR: <= -2.22

**2. `FIN.FORENSIC.dechow_f_score`** -- Dechow F-Score Manipulation Indicator
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: > 1.85 / YEL: > 1.40 / CLR: <= 1.40

**3. `FIN.FORENSIC.montier_c_score`** -- Montier C-Score Manipulation Indicator
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: >= 5 / YEL: >= 3 / CLR: < 3

**4. `FIN.FORENSIC.enhanced_sloan`** -- Enhanced Sloan Accrual Ratio
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: > 0.10 / YEL: > 0.05 / CLR: <= 0.05

**5. `FIN.FORENSIC.accrual_intensity`** -- Accrual Intensity Ratio
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: > 0.50 / YEL: > 0.25 / CLR: <= 0.25

**6. `FIN.FORENSIC.beneish_dechow_convergence`** -- Beneish-Dechow Convergence Amplifier
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: boolean

### FIN.GUIDE (5 checks)

**1. `FIN.GUIDE.current`** -- Current
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

**2. `FIN.GUIDE.track_record`** -- Guidance Track Record
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: RED: Multiple misses in past 4 quarters / YEL: One significant miss / CLR: Consistently meets guidance

**3. `FIN.GUIDE.philosophy`** -- Philosophy
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

**4. `FIN.GUIDE.earnings_reaction`** -- Earnings Reaction
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

**5. `FIN.GUIDE.analyst_consensus`** -- Analyst Consensus
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

### FIN.LIQ (5 checks)

**1. `FIN.LIQ.position`** -- Liquidity Position
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `current_ratio`
- Threshold: RED: <6 months runway OR revolver >80% utilized / YEL: <12 months runway OR revolver >50% utilized / CLR: >18 months runway AND revolver <50% utilized

**2. `FIN.LIQ.working_capital`** -- Working Capital Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `current_ratio`
- Threshold: RED: Current ratio <1.0 OR WC declining >30% YoY / YEL: Current ratio <1.5 OR below sector median / CLR: Otherwise

**3. `FIN.LIQ.efficiency`** -- Liquidity Efficiency
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `cash_ratio`
- Threshold: RED: Cash Ratio <0.2 OR OCF Ratio <0.4 OR Defensive Interval <30 days / YEL: Cash Ratio <0.5 OR OCF Ratio <0.8 OR CCC >sector 75th percentile / CLR: Otherwise

**4. `FIN.LIQ.trend`** -- Liquidity Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `current_ratio`
- Threshold: RED: DETERIORATING: 3+ consecutive quarters declining in majority of metrics / YEL: WEAKENING: 2 consecutive quarters declining / CLR: STABLE/IMPROVING: No sustained decline pattern

**5. `FIN.LIQ.cash_burn`** -- Cash Burn Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `cash_burn_months`
- Threshold: RED: Runway <12 months with no clear funding path / YEL: Runway 12-18 months / CLR: Runway >18 months or company is cash flow positive

### FIN.PROFIT (5 checks)

**1. `FIN.PROFIT.revenue`** -- Revenue Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: RED: Revenue decline >20% OR 3 consecutive years declining / YEL: Revenue decline >10% OR growth decelerating / CLR: Otherwise

**2. `FIN.PROFIT.margins`** -- Margin Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `accruals_ratio`
- Threshold: RED: Margin compression >500bps OR below sector 25th percentile / YEL: Margin compression >200bps OR below sector median / CLR: Otherwise

**3. `FIN.PROFIT.earnings`** -- Earnings Quality
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `ocf_to_ni`
- Threshold: RED: GAAP negative while Adjusted positive, OR Adjusted exceeds 2x GAAP / YEL: GAAP/Adjusted gap exceeds 50%, OR swing to loss / CLR: Otherwise

**4. `FIN.PROFIT.segment`** -- Segment Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: info/display

**5. `FIN.PROFIT.trend`** -- Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

### FIN.QUALITY (7 checks)

**1. `FIN.QUALITY.revenue_quality_score`** -- Revenue Quality Score Composite
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: RED: > 2 / YEL: > 1 / CLR: <= 1

**2. `FIN.QUALITY.cash_flow_quality`** -- Cash Flow Quality Score Composite
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F8
- field_key: `none`
- Threshold: RED: < 0.5 / YEL: < 0.8 / CLR: >= 0.8

**3. `FIN.QUALITY.dso_ar_divergence`** -- DSO and AR Divergence from Revenue
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: AR growing >20% faster than revenue / YEL: AR growing >10% faster than revenue / CLR: AR growth aligned with revenue growth

**4. `FIN.QUALITY.q4_revenue_concentration`** -- Q4 Revenue Concentration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3, F5
- field_key: `none`
- Threshold: RED: > 40% of annual revenue in Q4 / YEL: > 30% of annual revenue in Q4 / CLR: <= 30% of annual revenue in Q4

**5. `FIN.QUALITY.deferred_revenue_trend`** -- Deferred Revenue Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: Deferred revenue declining >20% while recognized revenue grows / YEL: Deferred revenue declining while recognized revenue grows / CLR: Deferred revenue stable or growing

**6. `FIN.QUALITY.quality_of_earnings`** -- Quality of Earnings (CFO/NI Ratio)
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F8
- field_key: `none`
- Threshold: RED: CFO/NI < 0.5 or > 2.0 / YEL: CFO/NI < 0.7 or > 1.5 / CLR: CFO/NI between 0.7 and 1.5

**7. `FIN.QUALITY.non_gaap_divergence`** -- Non-GAAP vs GAAP Earnings Divergence
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F5
- field_key: `none`
- Threshold: RED: Non-GAAP earnings > 2x GAAP earnings / YEL: Non-GAAP earnings > 1.5x GAAP earnings / CLR: Non-GAAP within 1.5x of GAAP

### FIN.SECTOR (2 checks)

**1. `FIN.SECTOR.energy`** -- Energy
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

**2. `FIN.SECTOR.retail`** -- Retail
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `financial_health_narrative`
- Threshold: tiered (no criteria defined)

### FIN.TEMPORAL (10 checks)

**1. `FIN.TEMPORAL.revenue_deceleration`** -- Revenue Growth Deceleration
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F2, F5
- field_key: `none`
- Threshold: temporal: revenue_growth (lower_is_worse)

**2. `FIN.TEMPORAL.margin_compression`** -- Gross/Operating Margin Compression
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F8
- field_key: `none`
- Threshold: temporal: gross_margin (lower_is_worse)

**3. `FIN.TEMPORAL.operating_margin_compression`** -- Operating Margin Compression
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F8
- field_key: `none`
- Threshold: temporal: operating_margin (lower_is_worse)

**4. `FIN.TEMPORAL.dso_expansion`** -- Days Sales Outstanding Expansion
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: temporal: dso_days (higher_is_worse)

**5. `FIN.TEMPORAL.cfo_ni_divergence`** -- Cash Flow / Net Income Divergence
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3
- field_key: `none`
- Threshold: temporal: net_income_cfo_divergence (higher_is_worse)

**6. `FIN.TEMPORAL.working_capital_deterioration`** -- Working Capital Deterioration
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F8
- field_key: `none`
- Threshold: temporal: working_capital (lower_is_worse)

**7. `FIN.TEMPORAL.debt_ratio_increase`** -- Leverage Ratio Increase
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F8
- field_key: `none`
- Threshold: temporal: debt_ratio (higher_is_worse)

**8. `FIN.TEMPORAL.cash_flow_deterioration`** -- Operating Cash Flow Deterioration
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F8
- field_key: `none`
- Threshold: temporal: operating_cash_flow (lower_is_worse)

**9. `FIN.TEMPORAL.profitability_trend`** -- Net Income / Profitability Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F2, F3
- field_key: `none`
- Threshold: temporal: net_income (lower_is_worse)

**10. `FIN.TEMPORAL.earnings_quality_divergence`** -- Earnings Quality Divergence Pattern
- Content Type: EVALUATIVE_CHECK
- Depth: 3
- Factors: F3, F6
- field_key: `none`
- Threshold: temporal: net_income_cfo_divergence (higher_is_worse)

---

## FWRD -- 83 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 19 |
| EVALUATIVE_CHECK | 64 |
| INFERENCE_PATTERN | 0 |
| With factor mappings | 64 |
| Without factor mappings | 19 |

### FWRD.DISC (9 checks)

**1. `FWRD.DISC.risk_factor_evolution`** -- Risk Factor Evolution
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**2. `FWRD.DISC.mda_depth`** -- Mda Depth
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**3. `FWRD.DISC.non_gaap_reconciliation`** -- Non Gaap Reconciliation
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**4. `FWRD.DISC.segment_consistency`** -- Segment Consistency
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**5. `FWRD.DISC.related_party_completeness`** -- Related Party Completeness
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**6. `FWRD.DISC.metric_consistency`** -- Metric Consistency
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**7. `FWRD.DISC.guidance_methodology`** -- Guidance Methodology
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**8. `FWRD.DISC.sec_comment_letters`** -- Sec Comment Letters
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**9. `FWRD.DISC.disclosure_quality_composite`** -- Disclosure Quality Composite
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

### FWRD.EVENT (21 checks)

**1. `FWRD.EVENT.earnings_calendar`** -- Upcoming Earnings Date
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `none`
- Threshold: RED: >= 3 / YEL: >= 1 / CLR: < 1

**2. `FWRD.EVENT.guidance_risk`** -- Guidance Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F6
- field_key: `none`
- Threshold: RED: Likely miss (run-rate significantly below guidance) / YEL: Uncertain (marginal, guidance recently lowered) / CLR: On track (run-rate supports guidance)

**3. `FWRD.EVENT.catalyst_dates`** -- Catalyst Dates
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: YEL: Material catalyst in policy period / CLR: No material catalysts in policy period

**4. `FWRD.EVENT.debt_maturity`** -- Debt Maturity 12mo
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: >$100M maturing + no refinancing in place / YEL: >$50M maturing / CLR: Minimal maturities or refinancing complete

**5. `FWRD.EVENT.covenant_test`** -- Covenant Test Dates
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: Test <90 days + marginal compliance (<10% headroom) / YEL: Test in policy period / CLR: Comfortable compliance (>20% headroom)

**6. `FWRD.EVENT.lockup_expiry`** -- Lock-up Expiration
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: RED: Lock-up expiration <60 days / YEL: Lock-up expiration <90 days / CLR: >90 days or not applicable

**7. `FWRD.EVENT.warrant_expiry`** -- Warrant Expiration
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: YEL: Warrant expiration in policy period with material dilution / CLR: No warrants or not in policy period

**8. `FWRD.EVENT.contract_renewal`** -- Contract Renewal Dates
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: YEL: >10% revenue at risk from contract expiration / CLR: <10% revenue at risk

**9. `FWRD.EVENT.regulatory_decision`** -- Regulatory Decision Dates
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F5
- field_key: `none`
- Threshold: YEL: Material regulatory decision in policy period / CLR: No pending regulatory decisions

**10. `FWRD.EVENT.litigation_milestone`** -- Litigation Milestones
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `none`
- Threshold: YEL: Material litigation milestone in policy period / CLR: No milestones or no active litigation

**11. `FWRD.EVENT.shareholder_mtg`** -- Shareholder Meeting Date
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: info/display

**12. `FWRD.EVENT.ma_closing`** -- M&A Closing Date
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F8
- field_key: `none`
- Threshold: YEL: M&A closing in policy period / CLR: No pending M&A or closed

**13. `FWRD.EVENT.synergy`** -- Synergy Realization
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F8
- field_key: `none`
- Threshold: RED: Synergy targets missed / YEL: Synergy targets at risk / CLR: On track or no synergy claims

**14. `FWRD.EVENT.customer_retention`** -- Customer Retention
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**15. `FWRD.EVENT.employee_retention`** -- Employee Retention
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**16. `FWRD.EVENT.integration`** -- Integration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**17. `FWRD.EVENT.proxy_deadline`** -- Proxy Deadline
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**18. `FWRD.EVENT.19-BIOT`** -- 19-Biot
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**19. `FWRD.EVENT.20-BIOT`** -- 20-Biot
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**20. `FWRD.EVENT.21-BIOT`** -- 21-Biot
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**21. `FWRD.EVENT.22-HLTH`** -- 22-Hlth
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

### FWRD.MACRO (15 checks)

**1. `FWRD.MACRO.sector_performance`** -- Sector Performance
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**2. `FWRD.MACRO.peer_issues`** -- Peer Issues
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**3. `FWRD.MACRO.industry_consolidation`** -- Industry Consolidation
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**4. `FWRD.MACRO.disruptive_tech`** -- Disruptive Tech
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**5. `FWRD.MACRO.interest_rate_sensitivity`** -- Interest Rate Sensitivity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**6. `FWRD.MACRO.inflation_impact`** -- Inflation Impact
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**7. `FWRD.MACRO.fx_exposure`** -- Fx Exposure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**8. `FWRD.MACRO.commodity_impact`** -- Commodity Impact
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**9. `FWRD.MACRO.labor_market`** -- Labor Market
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**10. `FWRD.MACRO.regulatory_changes`** -- Regulatory Changes
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**11. `FWRD.MACRO.legislative_risk`** -- Legislative Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**12. `FWRD.MACRO.trade_policy`** -- Trade Policy
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**13. `FWRD.MACRO.geopolitical_exposure`** -- Geopolitical Exposure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**14. `FWRD.MACRO.supply_chain_disruption`** -- Supply Chain Disruption
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

**15. `FWRD.MACRO.climate_transition_risk`** -- Climate Transition Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F9
- field_key: `none`
- Threshold: tiered (no criteria defined)

### FWRD.NARRATIVE (6 checks)

**1. `FWRD.NARRATIVE.10k_vs_earnings`** -- 10K Vs Earnings
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**2. `FWRD.NARRATIVE.investor_vs_sec`** -- Investor Vs Sec
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**3. `FWRD.NARRATIVE.analyst_skepticism`** -- Analyst Skepticism
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**4. `FWRD.NARRATIVE.short_thesis`** -- Short Thesis
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**5. `FWRD.NARRATIVE.auditor_cams`** -- Auditor Cams
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

**6. `FWRD.NARRATIVE.narrative_coherence_composite`** -- Narrative Coherence Composite
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `none`
- Threshold: tiered (no criteria defined)

### FWRD.WARN (32 checks)

**1. `FWRD.WARN.glassdoor_sentiment`** -- Glassdoor Sentiment
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**2. `FWRD.WARN.indeed_reviews`** -- Indeed Reviews
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**3. `FWRD.WARN.blind_posts`** -- Blind Posts
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**4. `FWRD.WARN.linkedin_headcount`** -- Linkedin Headcount
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**5. `FWRD.WARN.linkedin_departures`** -- Linkedin Departures
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**6. `FWRD.WARN.g2_reviews`** -- G2 Reviews
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**7. `FWRD.WARN.trustpilot_trend`** -- Trustpilot Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**8. `FWRD.WARN.app_ratings`** -- App Ratings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**9. `FWRD.WARN.cfpb_complaints`** -- Cfpb Complaints
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**10. `FWRD.WARN.fda_medwatch`** -- Fda Medwatch
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**11. `FWRD.WARN.nhtsa_complaints`** -- Nhtsa Complaints
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**12. `FWRD.WARN.social_sentiment`** -- Social Sentiment
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**13. `FWRD.WARN.journalism_activity`** -- Journalism Activity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**14. `FWRD.WARN.whistleblower_exposure`** -- Whistleblower Exposure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**15. `FWRD.WARN.vendor_payment_delays`** -- Vendor Payment Delays
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**16. `FWRD.WARN.job_posting_patterns`** -- Job Posting Patterns
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**17. `FWRD.WARN.compliance_hiring`** -- Compliance Hiring
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**18. `FWRD.WARN.legal_hiring`** -- Legal Hiring
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**19. `FWRD.WARN.zone_of_insolvency`** -- Zone Of Insolvency
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**20. `FWRD.WARN.goodwill_risk`** -- Goodwill Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**21. `FWRD.WARN.impairment_risk`** -- Impairment Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**22. `FWRD.WARN.ai_revenue_concentration`** -- Ai Revenue Concentration
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**23. `FWRD.WARN.hyperscaler_dependency`** -- Hyperscaler Dependency
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**24. `FWRD.WARN.gpu_allocation`** -- Gpu Allocation
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**25. `FWRD.WARN.data_center_risk`** -- Data Center Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**26. `FWRD.WARN.contract_disputes`** -- Contract Disputes
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**27. `FWRD.WARN.customer_churn_signals`** -- Customer Churn Signals
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**28. `FWRD.WARN.partner_stability`** -- Partner Stability
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**29. `FWRD.WARN.revenue_quality`** -- Revenue Quality
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**30. `FWRD.WARN.margin_pressure`** -- Margin Pressure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**31. `FWRD.WARN.capex_discipline`** -- Capex Discipline
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

**32. `FWRD.WARN.working_capital_trends`** -- Working Capital Trends
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `none`
- Threshold: tiered (no criteria defined)

---

## GOV -- 81 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 0 |
| EVALUATIVE_CHECK | 71 |
| INFERENCE_PATTERN | 10 |
| With factor mappings | 81 |
| Without factor mappings | 0 |

### GOV.ACTIVIST (14 checks)

**1. `GOV.ACTIVIST.13d_filings`** -- 13D Filings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**2. `GOV.ACTIVIST.campaigns`** -- Campaigns
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**3. `GOV.ACTIVIST.proxy_contests`** -- Proxy Contests
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**4. `GOV.ACTIVIST.settle_agree`** -- Settle Agree
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**5. `GOV.ACTIVIST.short_activism`** -- Short Activism
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**6. `GOV.ACTIVIST.demands`** -- Demands
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**7. `GOV.ACTIVIST.schedule_13g`** -- Schedule 13G
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `institutional_pct`
- Threshold: tiered (no criteria defined)

**8. `GOV.ACTIVIST.wolf_pack`** -- Wolf Pack
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**9. `GOV.ACTIVIST.board_seat`** -- Board Seat
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**10. `GOV.ACTIVIST.dissident`** -- Dissident
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**11. `GOV.ACTIVIST.withhold`** -- Withhold
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**12. `GOV.ACTIVIST.proposal`** -- Proposal
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**13. `GOV.ACTIVIST.consent`** -- Consent
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

**14. `GOV.ACTIVIST.standstill`** -- Standstill
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

### GOV.BOARD (13 checks)

**1. `GOV.BOARD.size`** -- Board Size
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `board_size`
- Threshold: info/display

**2. `GOV.BOARD.independence`** -- Board Independence
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `board_independence`
- Threshold: RED: <50% independent / YEL: <67% independent / CLR: >67% independent

**3. `GOV.BOARD.ceo_chair`** -- CEO Chair Separation
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `ceo_chair_duality`
- Threshold: YEL: Combined + no lead independent

**4. `GOV.BOARD.diversity`** -- Board Diversity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `board_size`
- Threshold: info/display

**5. `GOV.BOARD.tenure`** -- Tenure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**6. `GOV.BOARD.overboarding`** -- Overboarding
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `overboarded_directors`
- Threshold: tiered (no criteria defined)

**7. `GOV.BOARD.departures`** -- Departures
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `departures_18mo`
- Threshold: tiered (no criteria defined)

**8. `GOV.BOARD.attendance`** -- Attendance
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**9. `GOV.BOARD.expertise`** -- Expertise
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**10. `GOV.BOARD.refresh_activity`** -- Refresh Activity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**11. `GOV.BOARD.meetings`** -- Meetings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**12. `GOV.BOARD.committees`** -- Committees
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**13. `GOV.BOARD.succession`** -- Succession
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

### GOV.EFFECT (10 checks)

**1. `GOV.EFFECT.audit_committee`** -- Audit Committee
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**2. `GOV.EFFECT.audit_opinion`** -- Audit Opinion
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**3. `GOV.EFFECT.auditor_change`** -- Auditor Change
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**4. `GOV.EFFECT.material_weakness`** -- Material Weakness
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**5. `GOV.EFFECT.iss_score`** -- Iss Score
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**6. `GOV.EFFECT.proxy_advisory`** -- Proxy Advisory
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**7. `GOV.EFFECT.sox_404`** -- Sox 404
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**8. `GOV.EFFECT.sig_deficiency`** -- Sig Deficiency
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**9. `GOV.EFFECT.late_filing`** -- Late Filing
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**10. `GOV.EFFECT.nt_filing`** -- Nt Filing
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

### GOV.EXEC (11 checks)

**1. `GOV.EXEC.ceo_profile`** -- CEO Profile
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `ceo_tenure_years`
- Threshold: RED: <6 months tenure / YEL: <1 year tenure

**2. `GOV.EXEC.cfo_profile`** -- CFO Profile
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `cfo_tenure_years`
- Threshold: YEL: <1 year OR no CPA

**3. `GOV.EXEC.other_officers`** -- Other Officers Profile
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `leadership_stability_score`
- Threshold: YEL: CAO or GC <1 year tenure

**4. `GOV.EXEC.officer_litigation`** -- Officer Litigation History
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F7
- field_key: `leadership_stability_score`
- Threshold: RED: Any officer prior securities defendant / YEL: Any D&O involvement history / CLR: No litigation history found

**5. `GOV.EXEC.stability`** -- Executive Stability
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `leadership_stability_score`
- Threshold: RED: Both CEO and CFO <1 year / YEL: One <1 year / CLR: Stable executive team

**6. `GOV.EXEC.turnover_analysis`** -- Turnover Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `departures_18mo`
- Threshold: RED: 3+ departures in 24 months OR 2+ in 12 months / YEL: 2 departures in 24 months / CLR: 0-1 departures

**7. `GOV.EXEC.departure_context`** -- Departure Context
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `departures_18mo`
- Threshold: RED: Terminated OR departure during stress event / YEL: Unclear/'mutual agreement' language / CLR: Clear retirement or planned succession

**8. `GOV.EXEC.succession_status`** -- Succession Status
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `interim_ceo`
- Threshold: RED: Interim >6 months OR no succession plan disclosure / YEL: Interim appointment OR search underway / CLR: Named successor announced with departure

**9. `GOV.EXEC.founder`** -- Founder Status
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `ceo_tenure_years`
- Threshold: YEL: Founder + >50% voting control

**10. `GOV.EXEC.key_person`** -- Key Person Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `ceo_tenure_years`
- Threshold: YEL: Specific executive(s) named as key dependency

**11. `GOV.EXEC.turnover_pattern`** -- Turnover Pattern
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F7
- field_key: `departures_18mo`
- Threshold: RED: 4+ turnover stress signals / YEL: 2-3 signals

### GOV.INSIDER (8 checks)

**1. `GOV.INSIDER.form4_filings`** -- Form4 Filings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `insider_pct`
- Threshold: tiered (no criteria defined)

**2. `GOV.INSIDER.net_selling`** -- Net Insider Selling
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `insider_pct`
- Threshold: RED: Net selling >$5M in 12 months / YEL: Net selling $1-5M / CLR: Net buying or <$1M selling

**3. `GOV.INSIDER.10b5_plans`** -- 10B5 Plans
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**4. `GOV.INSIDER.plan_adoption`** -- Plan Adoption
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**5. `GOV.INSIDER.cluster_sales`** -- Cluster Sales
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**6. `GOV.INSIDER.unusual_timing`** -- Unusual Timing
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**7. `GOV.INSIDER.executive_sales`** -- Executive Sales
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `insider_pct`
- Threshold: tiered (no criteria defined)

**8. `GOV.INSIDER.ownership_pct`** -- Ownership Pct
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `insider_pct`
- Threshold: tiered (no criteria defined)

### GOV.PAY (15 checks)

**1. `GOV.PAY.ceo_total`** -- Ceo Total
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `ceo_pay_ratio`
- Threshold: tiered (no criteria defined)

**2. `GOV.PAY.ceo_structure`** -- Ceo Structure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `ceo_pay_ratio`
- Threshold: tiered (no criteria defined)

**3. `GOV.PAY.peer_comparison`** -- Peer Comparison
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `ceo_pay_ratio`
- Threshold: tiered (no criteria defined)

**4. `GOV.PAY.say_on_pay`** -- Say-on-Pay Results
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `say_on_pay_pct`
- Threshold: RED: <70% approval / YEL: 70-80% approval / CLR: >80% approval

**5. `GOV.PAY.clawback`** -- Clawback
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**6. `GOV.PAY.related_party`** -- Related Party
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**7. `GOV.PAY.golden_para`** -- Golden Para
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**8. `GOV.PAY.incentive_metrics`** -- Incentive Metrics
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**9. `GOV.PAY.equity_burn`** -- Equity Burn
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**10. `GOV.PAY.hedging`** -- Hedging
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**11. `GOV.PAY.perks`** -- Perks
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**12. `GOV.PAY.401k_match`** -- 401K Match
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**13. `GOV.PAY.deferred_comp`** -- Deferred Comp
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**14. `GOV.PAY.pension`** -- Pension
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**15. `GOV.PAY.exec_loans`** -- Exec Loans
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

### GOV.RIGHTS (10 checks)

**1. `GOV.RIGHTS.dual_class`** -- Dual Class
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `dual_class`
- Threshold: tiered (no criteria defined)

**2. `GOV.RIGHTS.voting_rights`** -- Voting Rights
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `dual_class`
- Threshold: tiered (no criteria defined)

**3. `GOV.RIGHTS.bylaws`** -- Bylaws
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**4. `GOV.RIGHTS.takeover`** -- Takeover
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**5. `GOV.RIGHTS.proxy_access`** -- Proxy Access
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**6. `GOV.RIGHTS.forum_select`** -- Forum Select
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**7. `GOV.RIGHTS.supermajority`** -- Supermajority
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**8. `GOV.RIGHTS.action_consent`** -- Action Consent
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**9. `GOV.RIGHTS.special_mtg`** -- Special Mtg
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `governance_score`
- Threshold: tiered (no criteria defined)

**10. `GOV.RIGHTS.classified`** -- Classified
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F10
- field_key: `classified_board`
- Threshold: tiered (no criteria defined)

---

## LIT -- 56 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 0 |
| EVALUATIVE_CHECK | 56 |
| INFERENCE_PATTERN | 0 |
| With factor mappings | 56 |
| Without factor mappings | 0 |

### LIT.OTHER (14 checks)

**1. `LIT.OTHER.product`** -- Product
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**2. `LIT.OTHER.employment`** -- Employment
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**3. `LIT.OTHER.ip`** -- Ip
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**4. `LIT.OTHER.environmental`** -- Environmental
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**5. `LIT.OTHER.contract`** -- Contract
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**6. `LIT.OTHER.aggregate`** -- Aggregate
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `active_matter_count`
- Threshold: tiered (no criteria defined)

**7. `LIT.OTHER.class_action`** -- Class Action
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**8. `LIT.OTHER.antitrust`** -- Antitrust
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**9. `LIT.OTHER.trade_secret`** -- Trade Secret
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**10. `LIT.OTHER.whistleblower`** -- Whistleblower
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `whistleblower_count`
- Threshold: tiered (no criteria defined)

**11. `LIT.OTHER.cyber_breach`** -- Cyber Breach
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**12. `LIT.OTHER.bankruptcy`** -- Bankruptcy
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**13. `LIT.OTHER.foreign_suit`** -- Foreign Suit
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**14. `LIT.OTHER.gov_contract`** -- Gov Contract
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

### LIT.REG (22 checks)

**1. `LIT.REG.sec_investigation`** -- SEC Investigation
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F5
- field_key: `sec_enforcement_stage`
- Threshold: RED: Formal SEC investigation or Wells Notice / YEL: Informal inquiry disclosed / CLR: No SEC investigation

**2. `LIT.REG.sec_active`** -- SEC Wells Notice
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1, F5
- field_key: `sec_enforcement_stage`
- Threshold: RED: Wells Notice received / YEL: SEC investigation ongoing / CLR: No Wells Notice

**3. `LIT.REG.sec_severity`** -- SEC Current Action
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F5
- field_key: `sec_enforcement_stage`
- Threshold: RED: Active SEC enforcement action / YEL: SEC investigation (pre-enforcement) / CLR: No SEC enforcement

**4. `LIT.REG.doj_investigation`** -- SEC Prior Actions
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F5
- field_key: `regulatory_count`
- Threshold: RED: Prior SEC enforcement action in 5 years / YEL: SEC investigation history (no enforcement) / CLR: No SEC enforcement history

**5. `LIT.REG.industry_reg`** -- SEC Penalties
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F5
- field_key: `regulatory_count`
- Threshold: RED: >$10M / YEL: Any penalties / CLR: No SEC penalties

**6. `LIT.REG.ftc_investigation`** -- SEC Consent Decrees
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F5
- field_key: `regulatory_count`
- Threshold: RED: Active SEC consent decree / YEL: Prior consent decree / CLR: No consent decrees

**7. `LIT.REG.state_ag`** -- State Ag
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**8. `LIT.REG.subpoena`** -- Subpoena
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**9. `LIT.REG.comment_letters`** -- Comment Letters
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `comment_letter_count`
- Threshold: tiered (no criteria defined)

**10. `LIT.REG.deferred_pros`** -- Deferred Pros
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**11. `LIT.REG.wells_notice`** -- Wells Notice
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `wells_notice`
- Threshold: tiered (no criteria defined)

**12. `LIT.REG.consent_order`** -- Consent Order
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**13. `LIT.REG.cease_desist`** -- Cease Desist
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**14. `LIT.REG.civil_penalty`** -- Civil Penalty
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**15. `LIT.REG.dol_audit`** -- Dol Audit
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**16. `LIT.REG.epa_action`** -- Epa Action
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**17. `LIT.REG.osha_citation`** -- Osha Citation
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**18. `LIT.REG.cfpb_action`** -- Cfpb Action
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**19. `LIT.REG.fdic_order`** -- Fdic Order
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**20. `LIT.REG.fda_warning`** -- Fda Warning
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**21. `LIT.REG.foreign_gov`** -- Foreign Gov
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

**22. `LIT.REG.state_action`** -- State Action
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F5, F7
- field_key: `regulatory_count`
- Threshold: tiered (no criteria defined)

### LIT.SCA (20 checks)

**1. `LIT.SCA.search`** -- SCA Database Search
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `total_sca_count`
- Threshold: search: Must execute Stanford SCAC search

**2. `LIT.SCA.active`** -- Active SCA Status
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `active_sca_count`
- Threshold: RED: Active case / CLR: No active case

**3. `LIT.SCA.filing_date`** -- Filing Date
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `sca_filing_date`
- Threshold: RED: <12 months ago / YEL: 12-24 months ago / CLR: >24 months ago or no case

**4. `LIT.SCA.class_period`** -- Class Period
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `active_sca_count`
- Threshold: info/display

**5. `LIT.SCA.allegations`** -- Allegation Summary
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `active_sca_count`
- Threshold: classify: TYPE_A_DISCLOSURE, TYPE_B_GUIDANCE, TYPE_C_PRODUCT, TYPE_D_GOVERNANCE, TYPE_E_MA

**6. `LIT.SCA.lead_plaintiff`** -- Lead Plaintiff
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `sca_lead_counsel_tier`
- Threshold: RED: Institutional lead plaintiff / YEL: Individual lead plaintiff with major law firm / CLR: Case dismissed or no case

**7. `LIT.SCA.case_status`** -- Case Status
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `active_sca_count`
- Threshold: RED: Past motion to dismiss (MTD denied or in discovery) / YEL: MTD pending / CLR: MTD granted/dismissed or no case

**8. `LIT.SCA.exposure`** -- Exposure Estimate
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `contingent_liabilities_total`
- Threshold: RED: >$50M / YEL: $10M-$50M / CLR: <$10M or no case

**9. `LIT.SCA.policy_status`** -- Policy Status
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `active_sca_count`
- Threshold: info/display

**10. `LIT.SCA.prior_settle`** -- Prior Settlements
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `settled_sca_count`
- Threshold: RED: 2+ settlements in 5 years / YEL: 1 settlement in 5 years / CLR: No settlements

**11. `LIT.SCA.settle_amount`** -- Settlement Amount
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `contingent_liabilities_total`
- Threshold: RED: >$25M / YEL: $10M-$25M / CLR: <$10M or none

**12. `LIT.SCA.settle_date`** -- Settlement Date
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `settled_sca_count`
- Threshold: info/display

**13. `LIT.SCA.prior_dismiss`** -- Prior Dismissals
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `total_sca_count`
- Threshold: info/display

**14. `LIT.SCA.dismiss_basis`** -- Dismissal Basis
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `total_sca_count`
- Threshold: info/display

**15. `LIT.SCA.historical`** -- Historical Suits
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `total_sca_count`
- Threshold: RED: 3+ historical cases / YEL: 1-2 historical cases / CLR: No historical cases

**16. `LIT.SCA.derivative`** -- Derivative Litigation
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `derivative_suit_count`
- Threshold: RED: Active derivative action / YEL: Books and records demand pending / CLR: No derivative action

**17. `LIT.SCA.demand`** -- Derivative Demand
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `derivative_suit_count`
- Threshold: RED: Demand received and rejected / YEL: Demand pending / CLR: No demand received

**18. `LIT.SCA.merger_obj`** -- Merger Objection
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `deal_litigation_count`
- Threshold: RED: M&A litigation with material claims / YEL: Standard merger objection / CLR: No M&A litigation or no pending M&A

**19. `LIT.SCA.erisa`** -- ERISA Stock Drop
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1
- field_key: `regulatory_count`
- Threshold: RED: Active ERISA stock drop claim / YEL: 401k with company stock + recent stock decline / CLR: No ERISA claim and minimal exposure

**20. `LIT.SCA.prefiling`** -- Pre-Filing Activity
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1
- field_key: `active_sca_count`
- Threshold: RED: 3+ plaintiff firms investigating / YEL: 1-2 firms investigating / CLR: No investigation notices

---

## NLP -- 15 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 5 |
| EVALUATIVE_CHECK | 10 |
| INFERENCE_PATTERN | 0 |
| With factor mappings | 10 |
| Without factor mappings | 5 |

### NLP.CAM (1 checks)

**1. `NLP.CAM.changes`** -- Critical Audit Matters Changed From Prior Year
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: New CAM related to revenue recognition or litigation / YEL: Any new CAM added / CLR: No change in CAMs

### NLP.DISCLOSURE (2 checks)

**1. `NLP.DISCLOSURE.hedging_language_increase`** -- Increase in Hedging/Qualifying Language
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: YoY change in qualifying language frequency

**2. `NLP.DISCLOSURE.forward_looking_decrease`** -- Decrease in Forward-Looking Statements
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: YoY change in forward-looking statement frequency

### NLP.FILING (2 checks)

**1. `NLP.FILING.late_filing`** -- Filing Deadline Missed (NT Filing)
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: boolean

**2. `NLP.FILING.filing_timing_change`** -- Filing Date Shifted Significantly vs Prior Year
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Days difference vs prior year filing date

### NLP.MDA (4 checks)

**1. `NLP.MDA.readability_change`** -- MD&A Readability Change (Fog Index YoY)
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: Fog Index increase > 4 points / YEL: Fog Index increase > 2 points / CLR: Stable or improving

**2. `NLP.MDA.tone_shift`** -- MD&A Negative Tone Shift
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3, F5
- field_key: `none`
- Threshold: RED: Negative ratio shift > +10% / YEL: Negative ratio shift > +5% / CLR: Stable or improving

**3. `NLP.MDA.readability_absolute`** -- Current MD&A Fog Index Level
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Gunning Fog Index value

**4. `NLP.MDA.tone_absolute`** -- Current MD&A Negative Tone Ratio
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `none`
- Threshold: display: Negative keyword ratio

### NLP.RISK (4 checks)

**1. `NLP.RISK.factor_count_change`** -- Risk Factor Count Change YoY
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: 10+ new risk factors / YEL: 5+ new risk factors / CLR: Fewer than 5 new

**2. `NLP.RISK.new_risk_factors`** -- New Risk Factors Added This Year
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: RED: New risk factor mentions litigation/SEC / YEL: Any new material risk factor / CLR: No significant new factors

**3. `NLP.RISK.litigation_risk_factor_new`** -- New Litigation-Specific Risk Factor
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1, F3
- field_key: `none`
- Threshold: boolean

**4. `NLP.RISK.regulatory_risk_factor_new`** -- New Regulatory Risk Factor
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: boolean

### NLP.WHISTLE (2 checks)

**1. `NLP.WHISTLE.language_detected`** -- Whistleblower/Qui Tam Language in Filings
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F1, F3
- field_key: `none`
- Threshold: boolean

**2. `NLP.WHISTLE.internal_investigation`** -- Internal Investigation Language Detected
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F3
- field_key: `none`
- Threshold: boolean

---

## STOCK -- 35 Checks

| Metric | Count |
|---|---|
| MANAGEMENT_DISPLAY | 7 |
| EVALUATIVE_CHECK | 22 |
| INFERENCE_PATTERN | 6 |
| With factor mappings | 28 |
| Without factor mappings | 7 |

### STOCK.ANALYST (2 checks)

**1. `STOCK.ANALYST.coverage`** -- Analyst Coverage
- Content Type: MANAGEMENT_DISPLAY
- Depth: 1
- Factors: none
- field_key: `beat_rate`
- Threshold: info/display

**2. `STOCK.ANALYST.momentum`** -- Momentum
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `beat_rate`
- Threshold: tiered (no criteria defined)

### STOCK.INSIDER (3 checks)

**1. `STOCK.INSIDER.summary`** -- Insider Activity Summary
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `insider_net_activity`
- Threshold: RED: Net selling >$1M in 90 days by multiple insiders / YEL: Significant selling by CEO/CFO / CLR: Balanced or net buying

**2. `STOCK.INSIDER.notable_activity`** -- Notable Activity
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `ceo_cfo_selling_pct`
- Threshold: tiered (no criteria defined)

**3. `STOCK.INSIDER.cluster_timing`** -- Cluster Timing
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `cluster_selling`
- Threshold: tiered (no criteria defined)

### STOCK.LIT (1 checks)

**1. `STOCK.LIT.existing_action`** -- Existing Securities Action
- Content Type: EVALUATIVE_CHECK
- Depth: 4
- Factors: F1, F2
- field_key: `active_sca_count`
- Threshold: RED: Active SCA pending / YEL: SCA recently settled or dismissed / CLR: No SCA history

### STOCK.OWN (3 checks)

**1. `STOCK.OWN.structure`** -- Ownership Structure
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F4
- field_key: `institutional_pct`
- Threshold: info/display

**2. `STOCK.OWN.concentration`** -- Concentration
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `institutional_pct`
- Threshold: tiered (no criteria defined)

**3. `STOCK.OWN.activist`** -- Activist
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `activist_present`
- Threshold: tiered (no criteria defined)

### STOCK.PATTERN (6 checks)

**1. `STOCK.PATTERN.event_collapse`** -- Event Collapse Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F2
- field_key: `single_day_drops_count`
- Threshold: detect: >15% single-day drop + company-specific trigger + peers dropped <5% / RED: Pattern detected with fraud/accounting trigger / YEL: Pattern detected with earnings/guidance trigger / CLR: No pattern detected

**2. `STOCK.PATTERN.informed_trading`** -- Informed Trading Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F4
- field_key: `insider_net_activity`
- Threshold: detect: 2+ signals within 90 days before drop / RED: 3+ signals detected / YEL: 2 signals detected / CLR: <2 signals

**3. `STOCK.PATTERN.cascade`** -- Cascade Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F2
- field_key: `decline_from_high`
- Threshold: detect: >20 days declining, no 5% recovery bounce, short interest rising / RED: Pattern detected with >40 decline days / YEL: Pattern detected / CLR: No pattern detected

**4. `STOCK.PATTERN.peer_divergence`** -- Peer Divergence Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F2
- field_key: `returns_1y`
- Threshold: detect: Company down vs peers: >15% at 30 days OR >20% at 90 days / RED: Gap >30% or accelerating / YEL: Gap >15% at 30d or >20% at 90d / CLR: No divergence detected

**5. `STOCK.PATTERN.death_spiral`** -- Death Spiral Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F2
- field_key: `decline_from_high`
- Threshold: detect: 3+ of: <$5 price, convertibles >20% mkt cap, shorts >2x sector, delisting warning, <12mo runway / RED: 4+ factors present / YEL: 3 factors present / CLR: <3 factors

**6. `STOCK.PATTERN.short_attack`** -- Short Attack Pattern
- Content Type: INFERENCE_PATTERN
- Depth: 3
- Factors: F2
- field_key: `short_interest_pct`
- Threshold: detect: 2+ triggers: short seller report, short spike >50% MoM, drop >15% on report day, rebuttal, SEC/DOJ inquiry / RED: Active attack with fraud allegations / YEL: Post-attack or valuation-only / CLR: No attack detected

### STOCK.PRICE (10 checks)

**1. `STOCK.PRICE.recent_drop_alert`** -- Recent Drop Alert
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `decline_from_high`
- Threshold: RED: >10% (7d) OR >15% (30d) OR >25% (90d) company-specific decline / YEL: >5% (7d) OR >10% (30d) OR >15% (90d) company-specific decline / CLR: Below thresholds

**2. `STOCK.PRICE.chart_comparison`** -- Chart Comparison
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `decline_from_high`
- Threshold: RED: Clear sustained divergence >20% from sector / YEL: Moderate divergence 10-20% from sector / CLR: Moves with sector (<10% divergence)

**3. `STOCK.PRICE.position`** -- Stock Price Position
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `decline_from_high`
- Threshold: RED: >50% from high OR price <$5 / YEL: >30% from high OR price <$10 / CLR: Otherwise

**4. `STOCK.PRICE.returns_multi_horizon`** -- Returns Multi Horizon
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `returns_1y`
- Threshold: RED: 90-day <-50% OR all horizons negative + worse than sector / YEL: 90-day <-25% OR 3+ horizons negative / periods: 7d, 30d, 90d, 180d, 365d, YTD

**5. `STOCK.PRICE.attribution`** -- Price Attribution
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `decline_from_high`
- Threshold: RED: Company-specific underperformance >15% / YEL: 5-15% underperformance / CLR: <5% underperformance

**6. `STOCK.PRICE.peer_relative`** -- Peer Relative Performance
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `returns_1y`
- Threshold: RED: Gap >20% at any horizon OR gap widening / YEL: Gap >10% at any horizon / CLR: Otherwise

**7. `STOCK.PRICE.single_day_events`** -- Single Day Events
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `single_day_drops_count`
- Threshold: RED: Any drop >20% OR drop >10% with litigation filed / YEL: Any drop >10% / CLR: No drops >10%

**8. `STOCK.PRICE.recovery`** -- Recovery Analysis
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `returns_1y`
- Threshold: RED: NOT RECOVERING: <5% from low after 60+ days / YEL: ATTEMPTING: 5-10% recovery or not sustained / CLR: RECOVERING: >10% sustained recovery

**9. `STOCK.PRICE.technical`** -- Technical Indicators
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `volatility_90d`
- Threshold: RED: Volatility >50% / YEL: Volatility >35% / CLR: Otherwise

**10. `STOCK.PRICE.delisting_risk`** -- Delisting Risk
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `current_price`
- Threshold: RED: Delisting notice OR price <$1 for 30+ consecutive days / YEL: Price <$2 or market cap below minimum / CLR: Otherwise

### STOCK.SHORT (3 checks)

**1. `STOCK.SHORT.position`** -- Short Interest Position
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `short_interest_pct`
- Threshold: RED: >20% of float / YEL: 10-20% of float / CLR: <10% of float

**2. `STOCK.SHORT.trend`** -- Trend
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `short_interest_ratio`
- Threshold: tiered (no criteria defined)

**3. `STOCK.SHORT.report`** -- Report
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `short_interest_pct`
- Threshold: tiered (no criteria defined)

### STOCK.TRADE (3 checks)

**1. `STOCK.TRADE.liquidity`** -- Liquidity
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `current_price`
- Threshold: tiered (no criteria defined)

**2. `STOCK.TRADE.volume_patterns`** -- Volume Patterns
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `adverse_event_count`
- Threshold: tiered (no criteria defined)

**3. `STOCK.TRADE.options`** -- Options
- Content Type: MANAGEMENT_DISPLAY
- Depth: 2
- Factors: none
- field_key: `adverse_event_count`
- Threshold: tiered (no criteria defined)

### STOCK.VALUATION (4 checks)

**1. `STOCK.VALUATION.pe_ratio`** -- Pe Ratio
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `current_price`
- Threshold: tiered (no criteria defined)

**2. `STOCK.VALUATION.ev_ebitda`** -- Ev Ebitda
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `current_price`
- Threshold: tiered (no criteria defined)

**3. `STOCK.VALUATION.premium_discount`** -- Premium Discount
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `returns_1y`
- Threshold: tiered (no criteria defined)

**4. `STOCK.VALUATION.peg_ratio`** -- Peg Ratio
- Content Type: EVALUATIVE_CHECK
- Depth: 2
- Factors: F2
- field_key: `current_price`
- Threshold: tiered (no criteria defined)

---
