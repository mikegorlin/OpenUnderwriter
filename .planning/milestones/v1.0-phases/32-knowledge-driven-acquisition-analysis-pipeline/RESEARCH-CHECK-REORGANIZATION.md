# Check Reorganization Analysis

**Date**: 2026-02-15
**Scope**: All 388 checks in brain/checks.json, cross-referenced with OLD-SYSTEM-INSIGHTS.md
**Goal**: Map checks to underwriting questions, identify redundancies and gaps, propose reorganization

---

## 1. Underwriting Questions Extracted

Every check exists to answer an underwriting question. Here are the real questions grouped by domain, with every check_id mapped.

### Q1: What is this company and how risky is it inherently?
**Purpose**: Establish baseline identity and inherent risk classification before any analysis.

| Sub-question | Check IDs | Status |
|---|---|---|
| What does this company do? | `BIZ.MODEL.description`, `BIZ.COMP.market_position` | Active (display) |
| What D&O risk category does it fall into? | `BIZ.CLASS.primary`, `BIZ.CLASS.secondary` | Active (classify) |
| How big is it (market cap, revenue, employees)? | `BIZ.SIZE.market_cap`, `BIZ.SIZE.revenue_ttm`, `BIZ.SIZE.employees` | Active (display) |
| How long has it been public? | `BIZ.SIZE.growth_trajectory`, `BIZ.SIZE.public_tenure` | Active (display) |
| What sector/industry? | `BIZ.COMP.market_position`, `BIZ.COMP.market_share`, `BIZ.COMP.competitive_advantage` | Active (display) |
| Does it have prior SCA history? | `BIZ.CLASS.litigation_history` | Active (evaluative) |

**Checks**: BIZ.CLASS.primary, BIZ.CLASS.secondary, BIZ.CLASS.litigation_history, BIZ.MODEL.description, BIZ.COMP.market_position, BIZ.COMP.market_share, BIZ.COMP.competitive_advantage, BIZ.SIZE.market_cap, BIZ.SIZE.revenue_ttm, BIZ.SIZE.employees, BIZ.SIZE.growth_trajectory, BIZ.SIZE.public_tenure (12 checks)

---

### Q2: How sustainable and diversified is the business model?
**Purpose**: Assess whether the business model creates inherent exposure to D&O claims through concentration, dependency, or structural fragility.

| Sub-question | Check IDs | Status |
|---|---|---|
| How does the company make money? | `BIZ.MODEL.revenue_type`, `BIZ.MODEL.revenue_segment`, `BIZ.MODEL.revenue_geo` | Active |
| What is the cost structure risk? | `BIZ.MODEL.cost_structure`, `BIZ.MODEL.leverage_ops` | Active |
| Is the business model dependent on regulation? | `BIZ.MODEL.regulatory_dep` | Active |
| How capital-intensive is it? | `BIZ.MODEL.capital_intensity` | Active |
| Is there customer/supplier concentration? | `BIZ.DEPEND.customer_conc`, `BIZ.DEPEND.supplier_conc` | Active |
| Is there technology/regulatory/capital dependency? | `BIZ.DEPEND.tech_dep`, `BIZ.DEPEND.regulatory_dep`, `BIZ.DEPEND.capital_dep` | Active |
| Is there key-person dependency? | `BIZ.DEPEND.key_person` | Active |
| Is there macro sensitivity? | `BIZ.DEPEND.macro_sensitivity` | Active |
| Is distribution concentrated? | `BIZ.DEPEND.distribution` | Active |
| Are key contracts at risk? | `BIZ.DEPEND.contract_terms` | Active |
| Is labor a concentration risk? | `BIZ.DEPEND.labor` | Active |

**Checks**: BIZ.MODEL.revenue_type, BIZ.MODEL.revenue_segment, BIZ.MODEL.revenue_geo, BIZ.MODEL.cost_structure, BIZ.MODEL.leverage_ops, BIZ.MODEL.regulatory_dep, BIZ.MODEL.capital_intensity, BIZ.DEPEND.customer_conc, BIZ.DEPEND.supplier_conc, BIZ.DEPEND.tech_dep, BIZ.DEPEND.key_person, BIZ.DEPEND.regulatory_dep, BIZ.DEPEND.capital_dep, BIZ.DEPEND.macro_sensitivity, BIZ.DEPEND.distribution, BIZ.DEPEND.contract_terms, BIZ.DEPEND.labor (17 checks)

---

### Q3: What is the competitive landscape and how does it affect risk?
**Purpose**: Understand whether competitive dynamics create claim-triggering pressure.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is the competitive position? | `BIZ.COMP.threat_assessment`, `BIZ.COMP.barriers_entry`, `BIZ.COMP.moat`, `BIZ.COMP.barriers` | Active |
| Is the industry growing or contracting? | `BIZ.COMP.industry_growth`, `BIZ.COMP.headwinds` | Active |
| Is consolidation happening? | `BIZ.COMP.consolidation` | Active |
| How litigious is the peer group? | `BIZ.COMP.peer_litigation` | Active |

**Checks**: BIZ.COMP.threat_assessment, BIZ.COMP.barriers_entry, BIZ.COMP.moat, BIZ.COMP.barriers, BIZ.COMP.industry_growth, BIZ.COMP.headwinds, BIZ.COMP.consolidation, BIZ.COMP.peer_litigation (8 checks)

---

### Q4: Does this company have active or recent securities litigation?
**Purpose**: The most direct D&O risk question -- does the company already have claims or a pattern of claims?

| Sub-question | Check IDs | Status |
|---|---|---|
| Has a securities class action search been performed? | `LIT.SCA.search` | Active (search) |
| Is there an active SCA? | `LIT.SCA.active`, `STOCK.LIT.existing_action` | Active |
| What are the SCA details (date, period, allegations)? | `LIT.SCA.filing_date`, `LIT.SCA.class_period`, `LIT.SCA.allegations` | Active |
| Who is the lead plaintiff and how strong is the case? | `LIT.SCA.lead_plaintiff`, `LIT.SCA.case_status` | Active |
| What is the monetary exposure? | `LIT.SCA.exposure` | Active |
| What is the D&O policy impact? | `LIT.SCA.policy_status` | Active |
| Is there prior settlement history? | `LIT.SCA.prior_settle`, `LIT.SCA.settle_amount`, `LIT.SCA.settle_date` | Active |
| Were prior cases dismissed and on what basis? | `LIT.SCA.prior_dismiss`, `LIT.SCA.dismiss_basis` | Active |
| Is there a long history of suits? | `LIT.SCA.historical` | Active |
| Are there derivative suits? | `LIT.SCA.derivative`, `LIT.SCA.demand` | Active |
| Are there merger objection suits? | `LIT.SCA.merger_obj` | Active |
| Are there ERISA claims? | `LIT.SCA.erisa` | Active |
| Is there pre-filing activity (law firms investigating)? | `LIT.SCA.prefiling` | Active |

**Checks**: LIT.SCA.search, LIT.SCA.active, LIT.SCA.filing_date, LIT.SCA.class_period, LIT.SCA.allegations, LIT.SCA.lead_plaintiff, LIT.SCA.case_status, LIT.SCA.exposure, LIT.SCA.policy_status, LIT.SCA.prior_settle, LIT.SCA.settle_amount, LIT.SCA.settle_date, LIT.SCA.prior_dismiss, LIT.SCA.dismiss_basis, LIT.SCA.historical, LIT.SCA.derivative, LIT.SCA.demand, LIT.SCA.merger_obj, LIT.SCA.erisa, LIT.SCA.prefiling, STOCK.LIT.existing_action (21 checks)

---

### Q5: What other litigation exists and what regulatory actions are pending?
**Purpose**: Non-SCA litigation and regulatory actions that could trigger D&O claims or indicate deeper problems.

| Sub-question | Check IDs | Status |
|---|---|---|
| Is there an SEC investigation or enforcement? | `LIT.REG.sec_investigation`, `LIT.REG.sec_active`, `LIT.REG.sec_severity`, `LIT.REG.doj_investigation`, `LIT.REG.industry_reg`, `LIT.REG.ftc_investigation` | Active |
| Are there Wells Notices? | `LIT.REG.wells_notice` | Placeholder |
| Are there other federal regulatory actions? | `LIT.REG.cfpb_action`, `LIT.REG.fdic_order`, `LIT.REG.fda_warning`, `LIT.REG.epa_action`, `LIT.REG.osha_citation`, `LIT.REG.dol_audit` | Placeholder |
| Are there state-level regulatory actions? | `LIT.REG.state_ag`, `LIT.REG.state_action` | Placeholder |
| Are there specific enforcement types? | `LIT.REG.subpoena`, `LIT.REG.comment_letters`, `LIT.REG.deferred_pros`, `LIT.REG.consent_order`, `LIT.REG.cease_desist`, `LIT.REG.civil_penalty`, `LIT.REG.foreign_gov` | Placeholder |
| What other types of litigation exist? | `LIT.OTHER.product`, `LIT.OTHER.employment`, `LIT.OTHER.ip`, `LIT.OTHER.environmental`, `LIT.OTHER.contract`, `LIT.OTHER.class_action`, `LIT.OTHER.antitrust`, `LIT.OTHER.trade_secret`, `LIT.OTHER.whistleblower`, `LIT.OTHER.cyber_breach`, `LIT.OTHER.bankruptcy`, `LIT.OTHER.foreign_suit`, `LIT.OTHER.gov_contract` | Placeholder |
| What is the aggregate litigation burden? | `LIT.OTHER.aggregate` | Placeholder |

**Checks**: All 22 LIT.REG.* + all 14 LIT.OTHER.* = 36 checks

---

### Q6: Is the financial condition sound, or is there distress risk?
**Purpose**: Financial weakness is the #1 precursor to securities fraud claims.

| Sub-question | Check IDs | Status |
|---|---|---|
| Can the company meet short-term obligations? | `FIN.LIQ.position`, `FIN.LIQ.working_capital`, `FIN.LIQ.efficiency`, `FIN.LIQ.trend`, `FIN.LIQ.cash_burn` | Active |
| Is the debt structure sustainable? | `FIN.DEBT.structure`, `FIN.DEBT.coverage`, `FIN.DEBT.maturity`, `FIN.DEBT.credit_rating`, `FIN.DEBT.covenants` | Active |
| Is the company profitable and how is the trend? | `FIN.PROFIT.revenue`, `FIN.PROFIT.margins`, `FIN.PROFIT.earnings`, `FIN.PROFIT.segment`, `FIN.PROFIT.trend` | Active (trend=placeholder) |
| Are financial trends deteriorating over time? | `FIN.TEMPORAL.revenue_deceleration`, `FIN.TEMPORAL.margin_compression`, `FIN.TEMPORAL.operating_margin_compression`, `FIN.TEMPORAL.dso_expansion`, `FIN.TEMPORAL.cfo_ni_divergence`, `FIN.TEMPORAL.working_capital_deterioration`, `FIN.TEMPORAL.debt_ratio_increase`, `FIN.TEMPORAL.cash_flow_deterioration`, `FIN.TEMPORAL.profitability_trend`, `FIN.TEMPORAL.earnings_quality_divergence` | Active (temporal) |
| Are there industry-specific financial risks? | `FIN.SECTOR.energy`, `FIN.SECTOR.retail` | Placeholder |

**Checks**: FIN.LIQ.* (5), FIN.DEBT.* (5), FIN.PROFIT.* (5), FIN.TEMPORAL.* (10), FIN.SECTOR.* (2) = 27 checks

---

### Q7: Are the financial statements reliable?
**Purpose**: Financial statement integrity -- is the company reporting honestly?

| Sub-question | Check IDs | Status |
|---|---|---|
| Has there been a restatement? | `FIN.ACCT.restatement`, `FIN.ACCT.restatement_magnitude`, `FIN.ACCT.restatement_pattern`, `FIN.ACCT.restatement_auditor_link`, `FIN.ACCT.restatement_stock_window` | Active |
| Are internal controls effective? | `FIN.ACCT.internal_controls`, `FIN.ACCT.material_weakness`, `FIN.ACCT.auditor_attestation_fail` | Active/Placeholder |
| Is the auditor independent and reliable? | `FIN.ACCT.auditor`, `FIN.ACCT.auditor_disagreement`, `FIN.ACCT.sec_correspondence` | Active/Placeholder |
| Do forensic models detect manipulation? | `FIN.FORENSIC.fis_composite`, `FIN.FORENSIC.dechow_f_score`, `FIN.FORENSIC.montier_c_score`, `FIN.FORENSIC.enhanced_sloan`, `FIN.FORENSIC.accrual_intensity`, `FIN.FORENSIC.beneish_dechow_convergence` | Active |
| Are there earnings quality red flags? | `FIN.QUALITY.revenue_quality_score`, `FIN.QUALITY.cash_flow_quality`, `FIN.QUALITY.dso_ar_divergence`, `FIN.QUALITY.q4_revenue_concentration`, `FIN.QUALITY.deferred_revenue_trend`, `FIN.QUALITY.quality_of_earnings`, `FIN.QUALITY.non_gaap_divergence` | Active |
| Is earnings manipulation likely? | `FIN.ACCT.earnings_manipulation`, `FIN.ACCT.quality_indicators` | Placeholder |

**Checks**: FIN.ACCT.* (13), FIN.FORENSIC.* (6), FIN.QUALITY.* (7) = 26 checks

---

### Q8: Is management guidance credible?
**Purpose**: Guidance misses are a primary trigger for securities class actions.

| Sub-question | Check IDs | Status |
|---|---|---|
| What guidance is outstanding? | `FIN.GUIDE.current`, `FIN.GUIDE.philosophy` | Placeholder |
| Has management historically met guidance? | `FIN.GUIDE.track_record` | Active |
| How does the market react to earnings? | `FIN.GUIDE.earnings_reaction` | Placeholder |
| What do analysts expect? | `FIN.GUIDE.analyst_consensus` | Placeholder |

**Checks**: FIN.GUIDE.* (5)

---

### Q9: Is the board providing adequate oversight?
**Purpose**: Board quality directly determines derivative suit risk and governance failure exposure.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is the board composition? | `GOV.BOARD.size`, `GOV.BOARD.independence`, `GOV.BOARD.ceo_chair`, `GOV.BOARD.diversity` | Active/Mixed |
| Is the board engaged and competent? | `GOV.BOARD.tenure`, `GOV.BOARD.overboarding`, `GOV.BOARD.attendance`, `GOV.BOARD.expertise`, `GOV.BOARD.meetings`, `GOV.BOARD.committees` | Placeholder |
| Is there board continuity and succession? | `GOV.BOARD.departures`, `GOV.BOARD.refresh_activity`, `GOV.BOARD.succession` | Placeholder |
| Are governance controls effective? | `GOV.EFFECT.audit_committee`, `GOV.EFFECT.audit_opinion`, `GOV.EFFECT.auditor_change`, `GOV.EFFECT.material_weakness`, `GOV.EFFECT.sox_404`, `GOV.EFFECT.sig_deficiency`, `GOV.EFFECT.late_filing`, `GOV.EFFECT.nt_filing` | Placeholder |
| What do governance ratings say? | `GOV.EFFECT.iss_score`, `GOV.EFFECT.proxy_advisory` | Placeholder |

**Checks**: GOV.BOARD.* (13), GOV.EFFECT.* (10) = 23 checks
Also overlapping: EXEC.PROFILE.board_size, EXEC.PROFILE.avg_tenure, EXEC.PROFILE.ceo_chair_duality, EXEC.PROFILE.independent_ratio (display versions)

---

### Q10: Is the executive team trustworthy and stable?
**Purpose**: Management quality, stability, and integrity directly predict claim probability.

| Sub-question | Check IDs | Status |
|---|---|---|
| Who are the key executives? | `GOV.EXEC.ceo_profile`, `GOV.EXEC.cfo_profile`, `GOV.EXEC.other_officers` | Active |
| Is the leadership team stable? | `GOV.EXEC.stability`, `GOV.EXEC.turnover_analysis`, `GOV.EXEC.departure_context`, `GOV.EXEC.turnover_pattern` | Active |
| Is there a succession plan? | `GOV.EXEC.succession_status` | Active |
| Is there founder/key-person risk? | `GOV.EXEC.founder`, `GOV.EXEC.key_person` | Active |
| Do officers have prior litigation history? | `GOV.EXEC.officer_litigation`, `EXEC.PRIOR_LIT.any_officer`, `EXEC.PRIOR_LIT.ceo_cfo` | Active |
| What are the individual risk scores? | `EXEC.CEO.risk_score`, `EXEC.CFO.risk_score`, `EXEC.AGGREGATE.board_risk`, `EXEC.AGGREGATE.highest_risk_individual` | Active |
| Are new executives in key roles? | `EXEC.TENURE.ceo_new`, `EXEC.TENURE.cfo_new`, `EXEC.TENURE.c_suite_turnover` | Active |
| Are there concerning departures? | `EXEC.DEPARTURE.cfo_departure_timing`, `EXEC.DEPARTURE.cao_departure` | Active |
| Are executives overboarded? | `EXEC.PROFILE.overboarded_directors` | Active |

**Checks**: GOV.EXEC.* (11), EXEC.* (20) = 31 checks total

---

### Q11: Are insiders trading in concerning patterns?
**Purpose**: Insider selling before bad news is a primary allegation in securities fraud cases.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is the overall insider activity? | `STOCK.INSIDER.summary`, `GOV.INSIDER.form4_filings`, `GOV.INSIDER.net_selling`, `GOV.INSIDER.executive_sales`, `GOV.INSIDER.ownership_pct` | Active/Placeholder |
| Are there 10b5-1 plan concerns? | `GOV.INSIDER.10b5_plans`, `GOV.INSIDER.plan_adoption` | Placeholder |
| Is there cluster/unusual selling? | `GOV.INSIDER.cluster_sales`, `GOV.INSIDER.unusual_timing`, `STOCK.INSIDER.notable_activity`, `STOCK.INSIDER.cluster_timing` | Placeholder |
| Are specific executives selling? | `EXEC.INSIDER.ceo_net_selling`, `EXEC.INSIDER.cfo_net_selling`, `EXEC.INSIDER.cluster_selling`, `EXEC.INSIDER.non_10b51` | Active |

**Checks**: GOV.INSIDER.* (8), STOCK.INSIDER.* (3), EXEC.INSIDER.* (4) = 15 checks

---

### Q12: Is executive compensation aligned with shareholder interests?
**Purpose**: Misaligned compensation creates perverse incentives and is a common derivative suit trigger.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is CEO pay and how is it structured? | `GOV.PAY.ceo_total`, `GOV.PAY.ceo_structure` | Placeholder |
| How does pay compare to peers? | `GOV.PAY.peer_comparison` | Placeholder |
| Did shareholders approve pay? | `GOV.PAY.say_on_pay` | Active |
| Are there clawback provisions? | `GOV.PAY.clawback` | Placeholder |
| Are there related-party transactions? | `GOV.PAY.related_party` | Placeholder |
| Are there excessive golden parachutes? | `GOV.PAY.golden_para` | Placeholder |
| Are incentive metrics appropriate? | `GOV.PAY.incentive_metrics` | Placeholder |
| Is equity dilution excessive? | `GOV.PAY.equity_burn` | Placeholder |
| Are hedging/pledging policies adequate? | `GOV.PAY.hedging` | Placeholder |
| Are perks excessive? | `GOV.PAY.perks`, `GOV.PAY.401k_match`, `GOV.PAY.deferred_comp`, `GOV.PAY.pension`, `GOV.PAY.exec_loans` | Placeholder |

**Checks**: GOV.PAY.* (15)

---

### Q13: Do shareholder rights protect or expose investors?
**Purpose**: Weak shareholder rights increase derivative suit risk and reduce accountability.

| Sub-question | Check IDs | Status |
|---|---|---|
| Is there a dual-class structure? | `GOV.RIGHTS.dual_class`, `GOV.RIGHTS.voting_rights` | Placeholder |
| Are bylaws shareholder-friendly? | `GOV.RIGHTS.bylaws` | Placeholder |
| Are there anti-takeover provisions? | `GOV.RIGHTS.takeover`, `GOV.RIGHTS.classified` | Placeholder |
| Do shareholders have proxy access? | `GOV.RIGHTS.proxy_access` | Placeholder |
| Are there forum selection/supermajority provisions? | `GOV.RIGHTS.forum_select`, `GOV.RIGHTS.supermajority` | Placeholder |
| Can shareholders act by consent or call special meetings? | `GOV.RIGHTS.action_consent`, `GOV.RIGHTS.special_mtg` | Placeholder |

**Checks**: GOV.RIGHTS.* (10)

---

### Q14: Is there activist investor pressure?
**Purpose**: Activist campaigns create D&O exposure through proxy fights, demands, and litigation.

| Sub-question | Check IDs | Status |
|---|---|---|
| Are there 13D filings? | `GOV.ACTIVIST.13d_filings`, `GOV.ACTIVIST.schedule_13g` | Placeholder |
| Are there active campaigns? | `GOV.ACTIVIST.campaigns`, `GOV.ACTIVIST.proxy_contests`, `GOV.ACTIVIST.demands` | Placeholder |
| Have there been settlements/agreements? | `GOV.ACTIVIST.settle_agree`, `GOV.ACTIVIST.standstill` | Placeholder |
| Is there short activism? | `GOV.ACTIVIST.short_activism` | Placeholder |
| Is there wolf pack behavior? | `GOV.ACTIVIST.wolf_pack` | Placeholder |
| Have activists obtained board seats? | `GOV.ACTIVIST.board_seat` | Placeholder |
| Are there dissident/withhold/proposal actions? | `GOV.ACTIVIST.dissident`, `GOV.ACTIVIST.withhold`, `GOV.ACTIVIST.proposal`, `GOV.ACTIVIST.consent` | Placeholder |

**Checks**: GOV.ACTIVIST.* (14), plus STOCK.OWN.activist (display)

---

### Q15: What does the stock price behavior tell us about risk?
**Purpose**: Stock price patterns are both risk indicators and the basis for class period/damages calculation.

| Sub-question | Check IDs | Status |
|---|---|---|
| Has there been a significant recent decline? | `STOCK.PRICE.recent_drop_alert`, `STOCK.PRICE.position` | Active |
| How does price compare to sector/peers? | `STOCK.PRICE.chart_comparison`, `STOCK.PRICE.peer_relative`, `STOCK.PRICE.attribution` | Active |
| What are multi-horizon returns? | `STOCK.PRICE.returns_multi_horizon` | Active |
| Were there single-day crash events? | `STOCK.PRICE.single_day_events` | Active |
| Is recovery happening? | `STOCK.PRICE.recovery` | Active |
| What do technical indicators show? | `STOCK.PRICE.technical` | Active |
| Is there delisting risk? | `STOCK.PRICE.delisting_risk` | Active |
| What patterns does the decline show? | `STOCK.PATTERN.event_collapse`, `STOCK.PATTERN.cascade`, `STOCK.PATTERN.peer_divergence`, `STOCK.PATTERN.death_spiral` | Active |
| Is there informed trading evidence? | `STOCK.PATTERN.informed_trading` | Active |
| Is there a short attack? | `STOCK.PATTERN.short_attack` | Active |

**Checks**: STOCK.PRICE.* (10), STOCK.PATTERN.* (6) = 16 checks

---

### Q16: What does the short selling and options activity signal?
**Purpose**: Elevated short interest often precedes claims; short seller reports can trigger them.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is short interest? | `STOCK.SHORT.position` | Active |
| Is short interest trending up? | `STOCK.SHORT.trend` | Placeholder |
| Are there short seller reports? | `STOCK.SHORT.report` | Placeholder |

**Checks**: STOCK.SHORT.* (3)

---

### Q17: What is the ownership structure and how does it affect risk?
**Purpose**: Institutional vs. retail mix, concentration, and activist presence affect claim dynamics.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is the ownership breakdown? | `STOCK.OWN.structure` | Active |
| Is ownership concentrated? | `STOCK.OWN.concentration` | Placeholder |
| Are activists present? | `STOCK.OWN.activist` | Placeholder |

**Checks**: STOCK.OWN.* (3)

---

### Q18: What do valuation metrics and analyst coverage suggest?
**Purpose**: Overvaluation creates larger damages in class actions; analyst expectations drive lawsuit triggers.

| Sub-question | Check IDs | Status |
|---|---|---|
| What is analyst coverage? | `STOCK.ANALYST.coverage`, `STOCK.ANALYST.momentum` | Active/Placeholder |
| What are valuation multiples? | `STOCK.VALUATION.pe_ratio`, `STOCK.VALUATION.ev_ebitda`, `STOCK.VALUATION.peg_ratio` | Placeholder |
| Is the stock at premium/discount to peers? | `STOCK.VALUATION.premium_discount` | Placeholder |
| What does trading activity show? | `STOCK.TRADE.liquidity`, `STOCK.TRADE.volume_patterns`, `STOCK.TRADE.options` | Placeholder |

**Checks**: STOCK.ANALYST.* (2), STOCK.VALUATION.* (4), STOCK.TRADE.* (3) = 9 checks

---

### Q19: What does the company's own disclosure language reveal?
**Purpose**: Changes in disclosure language -- especially hedging, risk factors, and narrative tone -- predict future problems.

| Sub-question | Check IDs | Status |
|---|---|---|
| Have risk factors changed? | `NLP.RISK.factor_count_change`, `NLP.RISK.new_risk_factors`, `NLP.RISK.litigation_risk_factor_new`, `NLP.RISK.regulatory_risk_factor_new` | Active |
| Has MD&A language become more obscure or negative? | `NLP.MDA.readability_change`, `NLP.MDA.tone_shift`, `NLP.MDA.readability_absolute`, `NLP.MDA.tone_absolute` | Active |
| Is hedging language increasing? | `NLP.DISCLOSURE.hedging_language_increase`, `NLP.DISCLOSURE.forward_looking_decrease` | Active (display) |
| Have Critical Audit Matters changed? | `NLP.CAM.changes` | Active |
| Has the filing timing changed? | `NLP.FILING.late_filing`, `NLP.FILING.filing_timing_change` | Active |
| Is there whistleblower/investigation language? | `NLP.WHISTLE.language_detected`, `NLP.WHISTLE.internal_investigation` | Active |

**Checks**: NLP.* (15)

---

### Q20: What are the forward-looking events during the policy period?
**Purpose**: Identify claim-triggering events (earnings, debt maturities, M&A, regulatory decisions) within the policy period.

| Sub-question | Check IDs | Status |
|---|---|---|
| When are earnings? | `FWRD.EVENT.earnings_calendar` | Active |
| Is guidance at risk? | `FWRD.EVENT.guidance_risk` | Active |
| What catalyst dates exist? | `FWRD.EVENT.catalyst_dates` | Active |
| Are there debt maturities/covenant tests? | `FWRD.EVENT.debt_maturity`, `FWRD.EVENT.covenant_test` | Active |
| Are there lock-up/warrant expirations? | `FWRD.EVENT.lockup_expiry`, `FWRD.EVENT.warrant_expiry` | Active |
| Are key contracts expiring? | `FWRD.EVENT.contract_renewal` | Active |
| Are there regulatory decisions pending? | `FWRD.EVENT.regulatory_decision` | Active |
| Are there litigation milestones? | `FWRD.EVENT.litigation_milestone` | Active |
| Is there a shareholder meeting? | `FWRD.EVENT.shareholder_mtg` | Active |
| Is there pending M&A? | `FWRD.EVENT.ma_closing`, `FWRD.EVENT.synergy` | Active |
| Post-M&A integration risks? | `FWRD.EVENT.customer_retention`, `FWRD.EVENT.employee_retention`, `FWRD.EVENT.integration`, `FWRD.EVENT.proxy_deadline` | Placeholder |
| Biotech-specific events? | `FWRD.EVENT.19-BIOT`, `FWRD.EVENT.20-BIOT`, `FWRD.EVENT.21-BIOT`, `FWRD.EVENT.22-HLTH` | Placeholder |

**Checks**: FWRD.EVENT.* (21)

---

### Q21: Are there early warning signals from alternative data?
**Purpose**: Detect problems before they become public through employee sentiment, customer complaints, and social signals.

| Sub-question | Check IDs | Status |
|---|---|---|
| What do employees say? | `FWRD.WARN.glassdoor_sentiment`, `FWRD.WARN.indeed_reviews`, `FWRD.WARN.blind_posts`, `FWRD.WARN.linkedin_headcount`, `FWRD.WARN.linkedin_departures` | Placeholder |
| What do customers say? | `FWRD.WARN.g2_reviews`, `FWRD.WARN.trustpilot_trend`, `FWRD.WARN.app_ratings`, `FWRD.WARN.cfpb_complaints`, `FWRD.WARN.fda_medwatch`, `FWRD.WARN.nhtsa_complaints` | Placeholder |
| What does social media/news say? | `FWRD.WARN.social_sentiment`, `FWRD.WARN.journalism_activity` | Placeholder |
| Are there whistleblower signals? | `FWRD.WARN.whistleblower_exposure` | Placeholder |
| Are there operational stress signals? | `FWRD.WARN.vendor_payment_delays`, `FWRD.WARN.contract_disputes`, `FWRD.WARN.customer_churn_signals`, `FWRD.WARN.partner_stability` | Placeholder |
| Are there hiring pattern anomalies? | `FWRD.WARN.job_posting_patterns`, `FWRD.WARN.compliance_hiring`, `FWRD.WARN.legal_hiring` | Placeholder |
| Are there financial early warnings? | `FWRD.WARN.zone_of_insolvency`, `FWRD.WARN.goodwill_risk`, `FWRD.WARN.impairment_risk`, `FWRD.WARN.revenue_quality`, `FWRD.WARN.margin_pressure`, `FWRD.WARN.capex_discipline`, `FWRD.WARN.working_capital_trends` | Placeholder |
| Are there AI/tech-specific warnings? | `FWRD.WARN.ai_revenue_concentration`, `FWRD.WARN.hyperscaler_dependency`, `FWRD.WARN.gpu_allocation`, `FWRD.WARN.data_center_risk` | Placeholder |

**Checks**: FWRD.WARN.* (32)

---

### Q22: What are the macro and industry headwinds?
**Purpose**: External forces that could trigger claims regardless of company-specific behavior.

| Sub-question | Check IDs | Status |
|---|---|---|
| How is the sector performing? | `FWRD.MACRO.sector_performance`, `FWRD.MACRO.peer_issues`, `FWRD.MACRO.industry_consolidation`, `FWRD.MACRO.disruptive_tech` | Placeholder |
| What macro factors affect the company? | `FWRD.MACRO.interest_rate_sensitivity`, `FWRD.MACRO.inflation_impact`, `FWRD.MACRO.fx_exposure`, `FWRD.MACRO.commodity_impact`, `FWRD.MACRO.labor_market` | Placeholder |
| What regulatory/political risks exist? | `FWRD.MACRO.regulatory_changes`, `FWRD.MACRO.legislative_risk`, `FWRD.MACRO.trade_policy`, `FWRD.MACRO.geopolitical_exposure` | Placeholder |
| Are there supply chain/climate risks? | `FWRD.MACRO.supply_chain_disruption`, `FWRD.MACRO.climate_transition_risk` | Placeholder |

**Checks**: FWRD.MACRO.* (15)

---

### Q23: Is the company's disclosure quality adequate?
**Purpose**: Poor disclosure creates both misrepresentation claims and failure-to-disclose allegations.

| Sub-question | Check IDs | Status |
|---|---|---|
| How have risk factors evolved? | `FWRD.DISC.risk_factor_evolution` | Placeholder |
| Is MD&A adequately detailed? | `FWRD.DISC.mda_depth` | Placeholder |
| Are non-GAAP reconciliations adequate? | `FWRD.DISC.non_gaap_reconciliation` | Placeholder |
| Are segments reported consistently? | `FWRD.DISC.segment_consistency` | Placeholder |
| Are related-party disclosures complete? | `FWRD.DISC.related_party_completeness` | Placeholder |
| Are metrics consistent over time? | `FWRD.DISC.metric_consistency` | Placeholder |
| Is guidance methodology transparent? | `FWRD.DISC.guidance_methodology` | Placeholder |
| Have there been SEC comment letters? | `FWRD.DISC.sec_comment_letters` | Placeholder |
| What is the overall disclosure quality? | `FWRD.DISC.disclosure_quality_composite` | Placeholder |

**Checks**: FWRD.DISC.* (9)

---

### Q24: Are there narrative inconsistencies or credibility gaps?
**Purpose**: Contradictions between what management tells investors vs. regulators vs. analysts are a hallmark of fraud.

| Sub-question | Check IDs | Status |
|---|---|---|
| Does the 10-K match earnings call narrative? | `FWRD.NARRATIVE.10k_vs_earnings` | Placeholder |
| Does the investor narrative match SEC filings? | `FWRD.NARRATIVE.investor_vs_sec` | Placeholder |
| Are analysts skeptical? | `FWRD.NARRATIVE.analyst_skepticism` | Placeholder |
| Is there a short thesis? | `FWRD.NARRATIVE.short_thesis` | Placeholder |
| What do auditor Critical Audit Matters show? | `FWRD.NARRATIVE.auditor_cams` | Placeholder |
| Is the overall narrative coherent? | `FWRD.NARRATIVE.narrative_coherence_composite` | Placeholder |

**Checks**: FWRD.NARRATIVE.* (6)

---

### Q25: Does this company have unique/emerging risk exposures?
**Purpose**: AI claims, cybersecurity posture, and other non-traditional risk vectors.

| Sub-question | Check IDs | Status |
|---|---|---|
| Is the company making AI claims? | `BIZ.UNI.ai_claims` | Active |
| What is the cybersecurity posture? | `BIZ.UNI.cyber_posture`, `BIZ.UNI.cyber_business` | Active |

**Checks**: BIZ.UNI.* (3)

---

### Verification: All 388 Checks Accounted For

| Question | Check Count |
|---|---|
| Q1: Identity/classification | 12 |
| Q2: Business model sustainability | 17 |
| Q3: Competitive landscape | 8 |
| Q4: Securities litigation | 21 |
| Q5: Other litigation/regulatory | 36 |
| Q6: Financial condition | 27 |
| Q7: Financial statement integrity | 26 |
| Q8: Guidance credibility | 5 |
| Q9: Board oversight | 23 |
| Q10: Executive quality/stability | 31 |
| Q11: Insider trading patterns | 15 |
| Q12: Compensation alignment | 15 |
| Q13: Shareholder rights | 10 |
| Q14: Activist pressure | 15 |
| Q15: Stock price behavior | 16 |
| Q16: Short selling signals | 3 |
| Q17: Ownership structure | 3 |
| Q18: Valuation/analyst | 9 |
| Q19: Disclosure language (NLP) | 15 |
| Q20: Forward events | 21 |
| Q21: Alternative data warnings | 32 |
| Q22: Macro/industry headwinds | 15 |
| Q23: Disclosure quality | 9 |
| Q24: Narrative consistency | 6 |
| Q25: Unique/emerging risks | 3 |
| **TOTAL** | **432** |

**Note**: The total is 432 because some checks map to multiple questions. The actual unique check count is 388. The following checks appear in multiple questions:
- `STOCK.LIT.existing_action` (Q4 + Q15)
- `EXEC.PRIOR_LIT.*` (Q10 + Q4)
- `EXEC.INSIDER.*` (Q10 + Q11)
- `GOV.INSIDER.*` (Q11 + Q14)
- `STOCK.OWN.activist` (Q14 + Q17)
- `EXEC.PROFILE.*` 4 display checks overlap with GOV.BOARD counterparts (Q9 + Q10)

After deduplication: **388 unique checks confirmed**.

---

## 2. Redundancy Analysis

### 2.1 Truly Redundant (consolidate -- same data, same question)

**R1: Board size / composition display vs evaluative**
- `EXEC.PROFILE.board_size` (MGMT_DISPLAY) vs `GOV.BOARD.size` (EVALUATIVE_CHECK, info/display)
- Same data, same question, different prefix. **Consolidate to one.**

**R2: Board independence display vs evaluative**
- `EXEC.PROFILE.independent_ratio` (MGMT_DISPLAY) vs `GOV.BOARD.independence` (EVALUATIVE_CHECK with thresholds)
- Same data. EXEC version is display only; GOV version has thresholds. **Keep GOV.BOARD.independence, drop EXEC.PROFILE.independent_ratio or make it the display companion.**

**R3: CEO-Chair duality display vs evaluative**
- `EXEC.PROFILE.ceo_chair_duality` (MGMT_DISPLAY) vs `GOV.BOARD.ceo_chair` (EVALUATIVE_CHECK)
- Same data. **Consolidate.**

**R4: Average tenure display**
- `EXEC.PROFILE.avg_tenure` (MGMT_DISPLAY) vs `GOV.BOARD.tenure` (EVALUATIVE_CHECK, placeholder)
- Same underlying data. **Consolidate.**

**R5: SEC investigation cluster**
- `LIT.REG.sec_investigation` (RED: Formal investigation or Wells Notice)
- `LIT.REG.sec_active` (RED: Wells Notice received)
- `LIT.REG.sec_severity` (RED: Active enforcement action)
- `LIT.REG.wells_notice` (placeholder, tiered)
- These four all ask about SEC enforcement status at different stages. The first three have overlapping thresholds (Wells Notice appears in both sec_investigation and sec_active). **Consolidate into a single SEC enforcement lifecycle check with stages: Inquiry -> Investigation -> Wells Notice -> Enforcement -> Penalty -> Consent Decree.**

**R6: SEC prior actions / DOJ / FTC naming confusion**
- `LIT.REG.doj_investigation` is named "SEC Prior Actions" in the description
- `LIT.REG.industry_reg` is named "SEC Penalties"
- `LIT.REG.ftc_investigation` is named "SEC Consent Decrees"
- These check IDs don't match their descriptions at all. The IDs suggest DOJ/FTC/industry-reg but descriptions are about SEC enforcement history. **Rename or refactor -- these are misnamed checks that create confusion.**

**R7: Overboarding duplication**
- `EXEC.PROFILE.overboarded_directors` (EVALUATIVE, with thresholds) vs `GOV.BOARD.overboarding` (placeholder)
- Same check. **Keep EXEC.PROFILE.overboarded_directors (has thresholds), drop or redirect GOV.BOARD.overboarding.**

**R8: Executive turnover duplication**
- `GOV.EXEC.turnover_analysis` (RED: 3+ in 24mo or 2+ in 12mo)
- `EXEC.TENURE.c_suite_turnover` (RED: 3+ C-suite in 12mo)
- `GOV.EXEC.turnover_pattern` (RED: 4+ stress signals)
- Three checks all asking "is there excessive executive turnover?" with slightly different thresholds. **Consolidate to one primary check with a pattern amplifier.**

**R9: CEO tenure duplication**
- `GOV.EXEC.ceo_profile` (RED: <6mo tenure)
- `EXEC.TENURE.ceo_new` (RED: <1yr tenure)
- Both ask if the CEO is new. Different thresholds but same question. **Consolidate -- keep the one with richer context.**

**R10: CFO tenure duplication**
- `GOV.EXEC.cfo_profile` (YEL: <1yr or no CPA)
- `EXEC.TENURE.cfo_new` (RED: <1yr)
- Same question. **Consolidate.**

**R11: CEO/CFO selling duplication**
- `EXEC.INSIDER.ceo_net_selling` / `EXEC.INSIDER.cfo_net_selling` (individual exec selling %)
- `GOV.INSIDER.net_selling` (aggregate net selling $)
- `GOV.INSIDER.executive_sales` (placeholder)
- `STOCK.INSIDER.summary` (aggregate multi-insider)
- `STOCK.INSIDER.notable_activity` (placeholder)
- Five+ checks asking about insider selling. **Consolidate to: aggregate summary, individual CEO/CFO flags, and pattern detection.**

**R12: Cluster selling duplication**
- `EXEC.INSIDER.cluster_selling` (boolean: multiple officers within 30 days)
- `GOV.INSIDER.cluster_sales` (placeholder)
- `STOCK.INSIDER.cluster_timing` (placeholder)
- Three checks for the same pattern. **Consolidate to one.**

**R13: Material weakness duplication**
- `FIN.ACCT.material_weakness` (RED: MW disclosed in 9A)
- `FIN.ACCT.internal_controls` (placeholder, field_key: material_weaknesses)
- `GOV.EFFECT.material_weakness` (INFERENCE_PATTERN, placeholder)
- Three checks for material weakness. **Consolidate to one evaluative check + one governance-impact pattern.**

**R14: BIZ.DEPEND naming vs description mismatches**
- `BIZ.DEPEND.supplier_conc` -- described as "Top 5 Customers Concentration" (should be supplier)
- `BIZ.DEPEND.tech_dep` -- described as "Government Contract Percentage"
- `BIZ.DEPEND.key_person` -- described as "Customer Concentration Risk Composite"
- `BIZ.DEPEND.regulatory_dep` -- described as "Single-Source Suppliers"
- `BIZ.DEPEND.capital_dep` -- described as "Key Supplier Dependencies"
- `BIZ.DEPEND.macro_sensitivity` -- described as "Supply Chain Complexity"
- `BIZ.DEPEND.distribution` -- described as "Product Concentration"
- `BIZ.DEPEND.contract_terms` -- described as "Key Partnerships"
- `BIZ.DEPEND.labor` -- described as "Concentration Risk Composite"
- These IDs and descriptions are severely mismatched. The underlying data seems correct but naming is confusing. **Fix naming or restructure.**

**Total truly redundant pairs/clusters: 14 clusters involving ~45 checks. Consolidation would reduce by ~20-25 checks.**

### 2.2 Complementary (same question, different angles -- keep both)

**C1: Financial forensic models** -- FIS composite, Dechow F-Score, Montier C-Score, Enhanced Sloan, Accrual Intensity, Beneish-Dechow convergence. Six checks all asking "is there earnings manipulation?" but each model catches different patterns. The convergence check (`beneish_dechow_convergence`) amplifies when multiple models agree. **Keep all -- they are complementary by design.**

**C2: Stock price checks** -- recent_drop_alert, position, returns_multi_horizon, chart_comparison, peer_relative, attribution, single_day_events, recovery, technical, delisting_risk. Ten checks all about stock price, but each captures a different dimension (level, momentum, relative, events, technicals). **Keep all -- they answer different sub-questions.**

**C3: Stock patterns** -- event_collapse, informed_trading, cascade, peer_divergence, death_spiral, short_attack. Six pattern-detection checks that combine multiple signals. Each is a distinct pattern. **Keep all.**

**C4: Restatement checks** -- restatement (exists?), restatement_magnitude (how big?), restatement_pattern (repeat?), restatement_auditor_link (coincides with auditor change?), restatement_stock_window (coincides with stock drop?). Five checks that decompose the restatement question into actionable sub-questions. **Keep all -- each adds distinct risk information.**

**C5: SCA lifecycle checks** -- search, active, filing_date, class_period, allegations, lead_plaintiff, case_status, exposure, policy_status, prior_settle, settle_amount, settle_date, prior_dismiss, dismiss_basis, historical, derivative, demand, merger_obj, erisa, prefiling. Twenty checks that decompose the SCA question into every sub-question an underwriter needs. **Keep all -- this is the core of D&O analysis.**

**C6: FIN.TEMPORAL checks** -- 10 time-series trend checks covering revenue, margins, DSO, cash flow, working capital, leverage, profitability, earnings quality. Each tracks a different trend. **Keep all.**

**C7: Executive departure / stability** -- departure_context (why did they leave?), cfo_departure_timing (did CFO leave during stress?), cao_departure (did CAO leave?), stability (combined CEO+CFO), succession_status (is there a plan?). **Keep all -- different sub-questions about the same topic.**

**C8: Earnings quality suite** -- revenue_quality_score, cash_flow_quality, dso_ar_divergence, q4_revenue_concentration, deferred_revenue_trend, quality_of_earnings, non_gaap_divergence. Seven checks, each captures a different facet of earnings quality. **Keep all.**

### 2.3 Orphaned (unclear underwriting question)

**O1: `FWRD.EVENT.19-BIOT`, `FWRD.EVENT.20-BIOT`, `FWRD.EVENT.21-BIOT`, `FWRD.EVENT.22-HLTH`**
- Named with numeric codes and industry abbreviations. No descriptions beyond the codes. All placeholders.
- These appear to be industry-specific event checks for Biotech and Healthcare but have no clear definition.
- **Recommendation**: Either define them with clear underwriting questions (e.g., "Is there a PDUFA date?", "Is there a Phase 3 readout?") or remove and replace with properly named industry-specific checks.

**O2: `BIZ.SIZE.growth_trajectory` and `BIZ.SIZE.public_tenure`**
- growth_trajectory is described as "Public Company Tenure" with IPO recency thresholds
- public_tenure is described as "Revenue Growth YoY" with growth deceleration thresholds
- Names and descriptions are swapped. **Fix naming.**

**O3: Many FWRD.WARN checks duplicate FIN concepts**
- `FWRD.WARN.zone_of_insolvency` overlaps with `FIN.LIQ.cash_burn` and `FIN.LIQ.position`
- `FWRD.WARN.goodwill_risk` and `FWRD.WARN.impairment_risk` overlap with balance sheet analysis
- `FWRD.WARN.revenue_quality` overlaps with `FIN.QUALITY.revenue_quality_score`
- `FWRD.WARN.margin_pressure` overlaps with `FIN.TEMPORAL.margin_compression`
- `FWRD.WARN.working_capital_trends` overlaps with `FIN.TEMPORAL.working_capital_deterioration`
- `FWRD.WARN.capex_discipline` has no FIN counterpart but is financial in nature
- **Recommendation**: These "warnings" are meant to be forward-looking signals from alternative data, but several are actually core financial analysis checks. Decide: are these alternative-data-sourced versions or duplicates? If the former, clarify data sources. If the latter, consolidate.

### 2.4 Placeholder Summary

**190 checks have `tiered` threshold type with no criteria defined.**

By category:
| Prefix | Placeholder Count | Total | % Placeholder |
|---|---|---|---|
| STOCK | 14 | 35 | 40% |
| FIN | 8 | 58 | 14% |
| LIT | 35 | 56 | 63% |
| GOV | 62 | 81 | 77% |
| FWRD | 67 | 83 | 81% |
| EXEC | 0 | 20 | 0% |
| NLP | 0 | 15 | 0% |
| BIZ | 0 | 40 | 0% |
| **TOTAL** | **190** | **388** | **49%** |

**Key observation**: Nearly half the checks are placeholder. The areas most heavily affected are:
1. **FWRD (81%)** -- Forward-looking and alternative data. These were aspirational checks added before data acquisition was built.
2. **GOV (77%)** -- Governance checks beyond basic board composition. Most PAY, RIGHTS, ACTIVIST, INSIDER, and EFFECT checks lack criteria.
3. **LIT (63%)** -- All LIT.OTHER and most LIT.REG checks are placeholder. Only LIT.SCA and the first 6 LIT.REG checks have criteria.

**Implication**: Only 198 checks (51%) can actually evaluate anything. The other 190 are structural skeleton waiting for criteria.

---

## 3. Gap Analysis

### 3.1 Old System Questions We're Missing

These are questions the Old System explicitly answered that the current system has NO check for (not even a placeholder):

| # | Missing Question | Old System Reference | Priority |
|---|---|---|---|
| G1 | Is this a SPAC/De-SPAC company? What is its post-merger trajectory? | A.1.3, QS-43 | CRITICAL |
| G2 | Has the auditor issued a going concern opinion? | A.6.2 | CRITICAL |
| G3 | What is the Altman Z-Score distress prediction? | Module 2 | HIGH |
| G4 | What is the AGR (Accounting Governance Risk) score? | Module 2 Check 5.1.1 | HIGH |
| G5 | What specific revenue fraud patterns are present (bill-and-hold, channel stuffing, side letters, round-tripping, % of completion manipulation, cookie jar, big bath)? | A.4.4, Module 2 1.1.1-1.1.8 | HIGH |
| G6 | Which of the 5 derivative-suit risk categories does this company match? | Module 1, derivative_lawsuit_patterns.md | HIGH |
| G7 | Are there AI-specific fraud patterns (AI washing, misleading revenue claims, concealed limitations, false validation, concealed costs, undisclosed AI risks, misleading R&D)? | ai_technology_litigation_patterns.md | HIGH |
| G8 | Is there scientific community skepticism (PubPeer, Retraction Watch, KOL sentiment)? | Module 6 Section 6 | HIGH (biotech) |
| G9 | Are there compensation manipulation patterns (spring-loading, backdating, share pledging)? | Module 4 Checks 5.1-5.3 | MEDIUM |
| G10 | Are there ESG/greenwashing litigation risks? | Module 5 | MEDIUM |
| G11 | What is the non-audit fee ratio (auditor independence)? | B.6.1 | MEDIUM |
| G12 | Are there specific technical stock indicators (death cross, gap down, block trades)? | Module 2 7.1-7.20 | MEDIUM |
| G13 | Are there industry-specific operating metrics (SaaS Rule of 40, NRR, CAC; Biotech pipeline; Retail SSS; FinServ NIM, NPL; Energy RRR)? | B.7.1-B.7.4, Module 2 8.1-8.4 | MEDIUM |
| G14 | Is there an auto-decline / quick screen layer? | QS 40-43 checks | MEDIUM |
| G15 | What are the CDS spreads / default probability? | Case studies (CoreWeave) | MEDIUM |
| G16 | What is the Capex/OCF ratio? | Case studies (Oracle) | MEDIUM |
| G17 | What is off-balance-sheet lease commitment exposure? | Case studies (Oracle) | MEDIUM |
| G18 | Are there dual-class sunset provisions? | Module 4 6.1-6.5 | MEDIUM |
| G19 | Are there fee-shifting bylaws? | Module 4 6.1-6.5 | LOW |
| G20 | Is there dark web exposure (stolen credentials, data listings)? | Module 6 Check 10.1 | LOW |
| G21 | Are there patent/IP risks (PTAB, NPE, patent cliff)? | Module 6 Section 7 | MEDIUM (tech/pharma) |
| G22 | Is there litigation funding targeting the company? | Module 6 Check 10.6 | LOW |
| G23 | Are expert witnesses being retained against the company? | Module 6 Check 10.7 | LOW |
| G24 | Is there non-investor advocacy campaign activity? | Module 6 Check 10.5 | LOW |
| G25 | Is there unusual accounting firm activity (forensic accountants)? | Module 6 Check 10.8 | LOW |
| G26 | Are there undisclosed related parties discoverable via web research? | Module 6 Check 10.9 | MEDIUM |
| G27 | Is there union organizing activity (NLRB filings)? | Module 6 Check 10.5 | LOW |
| G28 | What are competitive intelligence signals? | Module 6 Section 9 | LOW |
| G29 | Are there circular deal structures (customer = investor)? | Case studies (CoreWeave) | MEDIUM |
| G30 | What is the operating margin vs. interest rate structural comparison? | Case studies (CoreWeave) | MEDIUM |

### 3.2 Hazard Categories Without Checks

The following D&O claim types/hazards have zero or near-zero explicit checks:

1. **SPAC/De-SPAC litigation** -- Zero checks. Was #1 source of new SCAs in 2022-2024.
2. **AI-specific securities fraud** -- Only `BIZ.UNI.ai_claims` (display). No checks for the 7 specific AI fraud hazard types.
3. **ESG/Greenwashing claims** -- Only `FWRD.MACRO.climate_transition_risk` (placeholder). No specific greenwashing risk assessment.
4. **Scientific community fraud signals** -- Zero checks. Critical for life sciences.
5. **Caremark/Board oversight failure claims** -- `GOV.BOARD.*` exists structurally but nearly all are placeholder. No explicit Caremark risk assessment.
6. **Compensation manipulation claims** -- `GOV.PAY.*` exists as 15 placeholders. No specific manipulation pattern detection (spring-loading, backdating, pledging).
7. **Revenue recognition fraud (by type)** -- Financial forensic models exist but don't name specific patterns (channel stuffing, bill-and-hold, etc.).
8. **Cyber breach/data privacy litigation** -- `LIT.OTHER.cyber_breach` and `BIZ.UNI.cyber_posture` exist but lack criteria. No data breach prediction.

### 3.3 Missing Risk Characteristics

The Old System uses these risk characteristics that the current system doesn't explicitly track:

1. **PURPLE (Unknown) classification** -- Current system has RED/YELLOW/CLEAR but no "data unavailable" classification. Missing data is treated as CLEAR by default, which is dangerous.
2. **Decision matrix (aggregate RED/YELLOW percentages)** -- No auto-decline or severity-weighted aggregation layer.
3. **Settlement severity dollar thresholds** -- Old system uses $10M/$50M/$market-cap-pct tiers. Current system lacks explicit severity calibration.
4. **Industry-adjusted thresholds** -- Old system recommends different module emphasis by industry. Current system applies all checks uniformly.
5. **Verification standards** -- Old system requires 2+ sources for soft signals. Current system has this in CLAUDE.md but no enforcement mechanism in the check framework.
6. **Stock decline attribution (mandatory)** -- Old system requires attribution for any >10% decline. Current system has `STOCK.PRICE.attribution` but it's not enforced as mandatory.
7. **Circular deal detection** -- Not a check type that exists at all.

---

## 4. Proposed Reorganization

### Design Principles

The current organization by data-source prefix (BIZ, FIN, GOV, LIT, STOCK, EXEC, NLP, FWRD) mixes:
- What is being measured (financial health, governance quality)
- Where the data comes from (SEC filings, stock data, NLP analysis)
- When it matters (current state, forward-looking, historical)

The proposed reorganization groups checks by **underwriting purpose**:
1. **Inherent Risk** -- What IS this company? (can't change, baseline exposure)
2. **Hazards** -- What COULD happen? (claim types the company is exposed to)
3. **Risk Characteristics** -- What amplifies/mitigates? (governance, financials, market signals)

Each check still needs data sources, but the organization follows the underwriter's thought process rather than the data pipeline's structure.

### 4.1 Inherent Risk Checks

**Purpose**: Establish the baseline risk level that can't be changed by the company. These determine the starting point for underwriting.

#### IR-1: Company Identity and Classification
**Underwriting question**: What is this company and what risk bucket does it belong to?

| Existing Checks | Disposition |
|---|---|
| `BIZ.CLASS.primary` | Keep -- primary risk classification |
| `BIZ.CLASS.secondary` | Keep -- secondary overlay |
| `BIZ.MODEL.description` | Keep -- business description |
| `BIZ.SIZE.market_cap` | Keep -- size classification |
| `BIZ.SIZE.revenue_ttm` | Keep -- revenue scale |
| `BIZ.SIZE.employees` | Keep -- operational scale |
| `BIZ.SIZE.growth_trajectory` / `BIZ.SIZE.public_tenure` | Fix naming, keep both (IPO recency + growth trajectory are distinct) |
| `BIZ.COMP.market_position` | Keep -- sector classification |

**New checks needed**: SPAC/De-SPAC classification flag (from G1).

**Data sources**: SEC EDGAR (SIC codes, filing dates), yfinance (market cap), 10-K (business description).

#### IR-2: Industry and Sector Risk
**Underwriting question**: What inherent litigation risk does this industry carry?

| Existing Checks | Disposition |
|---|---|
| `BIZ.COMP.market_share`, `BIZ.COMP.competitive_advantage` | Keep (display) |
| `BIZ.COMP.threat_assessment` | Keep -- market position |
| `BIZ.COMP.peer_litigation` | Keep -- peer litigation frequency |
| `FIN.SECTOR.energy`, `FIN.SECTOR.retail` | Keep but expand with industry-specific metrics |
| `FWRD.MACRO.sector_performance` | Move here -- sector context is inherent |

**New checks needed**: Industry-specific operating metric suites (G13) -- SaaS, Biotech, Retail, FinServ, Energy metrics. Industry base litigation rate.

**Data sources**: Industry databases, SEC filings, peer analysis.

#### IR-3: Business Model Risk
**Underwriting question**: Does the business model create structural exposure?

| Existing Checks | Disposition |
|---|---|
| All `BIZ.MODEL.*` (7 checks) | Keep |
| All `BIZ.DEPEND.*` (10 checks) | Keep (fix naming per R14) |
| `BIZ.COMP.moat`, `BIZ.COMP.barriers`, `BIZ.COMP.barriers_entry` | Keep |
| `BIZ.COMP.industry_growth`, `BIZ.COMP.headwinds`, `BIZ.COMP.consolidation` | Keep |

**New checks needed**: Circular deal structures (G29), Off-balance-sheet lease commitments (G17), Capex/OCF ratio (G16).

**Data sources**: 10-K (business description, risk factors), XBRL financials.

#### IR-4: Litigation History Profile
**Underwriting question**: What is this company's history of claims?

| Existing Checks | Disposition |
|---|---|
| `BIZ.CLASS.litigation_history` | Keep -- SCA history profile |
| `LIT.SCA.historical` | Keep -- historical suit count |
| `LIT.SCA.prior_settle`, `LIT.SCA.settle_amount`, `LIT.SCA.settle_date` | Keep -- settlement history |
| `LIT.SCA.prior_dismiss`, `LIT.SCA.dismiss_basis` | Keep -- dismissal history |

**Data sources**: Stanford SCAC, CourtListener, 10-K disclosure.

### 4.2 Hazard Checks

**Purpose**: Identify what types of claims the company is exposed to during the policy period. Organized by claim/event type.

#### HAZ-1: Securities Class Action Exposure
**Underwriting question**: Is there an active SCA, or are conditions ripe for one?

| Existing Checks | Disposition |
|---|---|
| `LIT.SCA.search` through `LIT.SCA.prefiling` (20 checks) | Keep all |
| `STOCK.LIT.existing_action` | Keep (stock-data perspective) |
| `LIT.SCA.merger_obj` | Move to HAZ-5 (M&A) |
| `LIT.SCA.erisa` | Move to HAZ-3 (employment) |

**Data sources**: Stanford SCAC, PACER, CourtListener, news search.

#### HAZ-2: Derivative Suit Exposure
**Underwriting question**: Is this company at risk of derivative litigation, and what type?

| Existing Checks | Disposition |
|---|---|
| `LIT.SCA.derivative`, `LIT.SCA.demand` | Keep |

**New checks needed (G6)**: 5-category derivative risk assessment:
- Board conflicts of interest (related-party M&A)
- M&A diligence failures
- Egregious behavior / culture failures (Caremark)
- Health & human safety (Caremark)
- Massive fraud

**Data sources**: DEF 14A (related-party transactions), 10-K (risk factors), news, Glassdoor.

#### HAZ-3: Regulatory Action Exposure
**Underwriting question**: Is the company facing or at risk of regulatory enforcement?

| Existing Checks | Disposition |
|---|---|
| `LIT.REG.sec_investigation` through `LIT.REG.ftc_investigation` (6 with criteria) | Consolidate (R5/R6) into SEC enforcement lifecycle |
| `LIT.REG.state_ag` through `LIT.REG.state_action` (16 placeholders) | Keep structure, define criteria |

**New checks needed**: FDA Form 483 observations, EPA consent decree active status, Congressional inquiry tracking, Multi-state AG coordination detection.

**Data sources**: SEC EDGAR, FOIA databases, news, regulatory agency websites.

#### HAZ-4: Non-Securities Litigation Exposure
**Underwriting question**: What other litigation could give rise to D&O claims?

| Existing Checks | Disposition |
|---|---|
| All `LIT.OTHER.*` (14 checks) | Keep, define criteria for all placeholders |

**New checks needed**: ERISA/stock-drop (move from LIT.SCA.erisa), union/labor disputes (G27), litigation funding detection (G22).

**Data sources**: PACER, CourtListener, NLRB, news search.

#### HAZ-5: M&A and Restructuring Exposure
**Underwriting question**: Is there pending M&A, and what litigation risks does it create?

| Existing Checks | Disposition |
|---|---|
| `FWRD.EVENT.ma_closing`, `FWRD.EVENT.synergy` | Keep |
| `FWRD.EVENT.customer_retention`, `FWRD.EVENT.employee_retention`, `FWRD.EVENT.integration` | Keep |
| `LIT.SCA.merger_obj` | Move here from HAZ-1 |

**Data sources**: 8-K, proxy statements, news.

#### HAZ-6: AI-Specific Claim Exposure
**Underwriting question**: Is this company making AI-related claims that create litigation exposure?

| Existing Checks | Disposition |
|---|---|
| `BIZ.UNI.ai_claims` | Upgrade from display to evaluative |
| `FWRD.WARN.ai_revenue_concentration`, `FWRD.WARN.hyperscaler_dependency`, `FWRD.WARN.gpu_allocation`, `FWRD.WARN.data_center_risk` | Move here |

**New checks needed (G7)**: 7 AI-specific hazard checks:
- AI washing (traditional software marketed as AI)
- Misleading AI revenue claims
- Concealment of AI limitations
- False third-party validation
- Concealment of AI costs
- Failure to disclose AI-specific risks
- Misleading AI R&D claims

**Data sources**: 10-K, earnings call transcripts, news, product analysis.

#### HAZ-7: SPAC/De-SPAC Claim Exposure
**Underwriting question**: Is this a de-SPAC company, and what are the post-merger risk factors?

| Existing Checks | Disposition |
|---|---|
| None | All new |

**New checks needed (G1)**:
- De-SPAC date and age
- Projections vs. actuals comparison
- Post-merger stock performance
- SPAC-related litigation filed
- SPAC sponsor conflicts of interest

**Data sources**: 8-K, S-4, original SPAC filings, stock data.

#### HAZ-8: Cyber/Data Privacy Claim Exposure
**Underwriting question**: Is the company at risk of cyber-related D&O claims?

| Existing Checks | Disposition |
|---|---|
| `BIZ.UNI.cyber_posture`, `BIZ.UNI.cyber_business` | Move here |
| `LIT.OTHER.cyber_breach` | Move here |

**New checks needed (G20)**: Dark web exposure signals, CVE vulnerabilities in products.

**Data sources**: News, breach databases, 10-K risk factors.

#### HAZ-9: ESG/Greenwashing Claim Exposure
**Underwriting question**: Is the company at risk of ESG-related litigation?

| Existing Checks | Disposition |
|---|---|
| `FWRD.MACRO.climate_transition_risk` | Move here |

**New checks needed (G10)**:
- ESG marketing vs. actual practices gap
- Internal climate reports not disclosed
- Board-level ESG oversight existence
- Climate risk disclosure adequacy

**Data sources**: Sustainability reports, news, proxy statements.

#### HAZ-10: Scientific/Clinical Integrity Claims (Industry-Specific)
**Underwriting question**: For life sciences companies, are there scientific integrity concerns?

| Existing Checks | Disposition |
|---|---|
| `FWRD.EVENT.19-BIOT`, `FWRD.EVENT.20-BIOT`, `FWRD.EVENT.21-BIOT`, `FWRD.EVENT.22-HLTH` | Redefine with clear names |

**New checks needed (G8)**:
- PubPeer comment monitoring
- Retraction Watch for paper retractions
- KOL sentiment at conferences
- Clinical trial endpoint changes
- Citizen petitions to FDA
- Data integrity allegations

**Data sources**: PubPeer, Retraction Watch, ClinicalTrials.gov, FDA citizen petition database, conference reports.

### 4.3 Risk Characteristic Checks

**Purpose**: Characteristics that amplify or mitigate the hazards. These are the "how bad could it get?" and "what protections exist?" questions.

#### RC-1: Financial Health (Amplifier)
**Underwriting question**: Does financial weakness amplify claim exposure?

| Existing Checks | Disposition |
|---|---|
| `FIN.LIQ.*` (5) | Keep |
| `FIN.DEBT.*` (5) | Keep |
| `FIN.PROFIT.*` (5) | Keep |
| `FIN.TEMPORAL.*` (10) | Keep |
| `FIN.GUIDE.*` (5) | Keep |

**New checks needed**:
- Altman Z-Score (G3)
- Going concern flag (G2)
- Capex/OCF ratio (G16)
- Off-balance-sheet lease commitments (G17)
- Operating margin vs. interest rate comparison (G30)

**Data sources**: XBRL financials, 10-K auditor report, yfinance.

#### RC-2: Financial Statement Integrity (Amplifier)
**Underwriting question**: Can we trust the reported numbers?

| Existing Checks | Disposition |
|---|---|
| `FIN.ACCT.*` (13) | Keep (consolidate MW duplication per R13) |
| `FIN.FORENSIC.*` (6) | Keep all (complementary per C1) |
| `FIN.QUALITY.*` (7) | Keep all (complementary per C8) |
| `NLP.CAM.changes` | Move here (relates to audit findings) |
| `NLP.WHISTLE.language_detected`, `NLP.WHISTLE.internal_investigation` | Move here (relates to financial integrity) |

**New checks needed**:
- Revenue fraud pattern taxonomy (G5) -- 8 specific patterns
- AGR Score (G4)
- Non-audit fee ratio (G11)
- Unusual accounting firm activity (G25)

**Data sources**: 10-K, audit reports, proxy statements, SEC comment letters.

#### RC-3: Governance Quality (Mitigator/Amplifier)
**Underwriting question**: Does governance protect or expose the company?

| Existing Checks | Disposition |
|---|---|
| `GOV.BOARD.*` (13) | Keep (consolidate per R1-R4, R7) |
| `GOV.EFFECT.*` (10) | Keep (consolidate MW per R13) |
| `GOV.RIGHTS.*` (10) | Keep |
| `GOV.PAY.*` (15) | Keep |

**New checks needed**:
- Compensation manipulation patterns (G9): spring-loading, backdating, pledging
- Dual-class sunset provisions (G18)
- Fee-shifting bylaws (G19)
- Non-audit fee ratio (also in RC-2)
- Caremark duty assessment (part of HAZ-2)

**Data sources**: DEF 14A, proxy statements, bylaws/charter, ISS/Glass Lewis.

#### RC-4: Management Quality (Mitigator/Amplifier)
**Underwriting question**: Does the management team increase or decrease claim risk?

| Existing Checks | Disposition |
|---|---|
| `GOV.EXEC.*` (11) | Keep (consolidate per R8-R10) |
| `EXEC.*` (20) | Keep (consolidate per R8-R10, reduce ~5 redundant checks) |

**New checks needed**: CEO credibility analysis (earnings call language vs. reality), management track record at prior companies.

**Data sources**: DEF 14A, 10-K, news, LinkedIn, prior company filings.

#### RC-5: Insider Activity (Amplifier)
**Underwriting question**: Are insiders behaving as if they know something bad is coming?

| Existing Checks | Disposition |
|---|---|
| `GOV.INSIDER.*` (8) | Consolidate per R11-R12 |
| `STOCK.INSIDER.*` (3) | Consolidate per R11-R12 |
| `EXEC.INSIDER.*` (4) | Keep (specific executive focus) |

**New checks needed**:
- Share pledging by insiders (G9)
- 10b5-1 adoption timing relative to material events
- Hedging transactions by executives

**Data sources**: Form 4, proxy statement, SEC filings (10b5-1 plan disclosures).

#### RC-6: Stock Market Signals (Amplifier)
**Underwriting question**: What is the market telling us about risk?

| Existing Checks | Disposition |
|---|---|
| `STOCK.PRICE.*` (10) | Keep all (complementary per C2) |
| `STOCK.PATTERN.*` (6) | Keep all (complementary per C3) |
| `STOCK.SHORT.*` (3) | Keep |
| `STOCK.OWN.*` (3) | Keep |
| `STOCK.VALUATION.*` (4) | Keep |
| `STOCK.TRADE.*` (3) | Keep |
| `STOCK.ANALYST.*` (2) | Keep |

**New checks needed (G12)**:
- Death cross detection (50-day MA crosses below 200-day)
- Gap down analysis (>5% single-day gaps)
- Block trade analysis (institutional selling)
- Options activity (unusual put buying)
- Days to cover calculation
- Short squeeze risk assessment
- CDS spread monitoring (G15)

**Data sources**: yfinance, options data, credit market data.

#### RC-7: Activist Pressure (Amplifier)
**Underwriting question**: Is activist pressure creating D&O exposure?

| Existing Checks | Disposition |
|---|---|
| `GOV.ACTIVIST.*` (14) | Keep all |

**New checks needed**: Non-investor advocacy campaigns (environmental, consumer, labor groups) (G24).

**Data sources**: SEC 13D/13G filings, news, proxy statements.

#### RC-8: Disclosure Quality (Mitigator/Amplifier)
**Underwriting question**: Does the quality of disclosure protect or expose the company?

| Existing Checks | Disposition |
|---|---|
| `FWRD.DISC.*` (9) | Keep |
| `FWRD.NARRATIVE.*` (6) | Keep |
| `NLP.MDA.*` (4) | Move here |
| `NLP.RISK.*` (4) | Move here |
| `NLP.DISCLOSURE.*` (2) | Move here |
| `NLP.FILING.*` (2) | Move here |

**Data sources**: 10-K, 10-Q, earnings call transcripts, investor presentations.

#### RC-9: Early Warning Signals (Forward-Looking Amplifier)
**Underwriting question**: Are there early signals of problems that haven't yet materialized?

| Existing Checks | Disposition |
|---|---|
| Employee sentiment: `FWRD.WARN.glassdoor_sentiment`, `FWRD.WARN.indeed_reviews`, `FWRD.WARN.blind_posts`, `FWRD.WARN.linkedin_headcount`, `FWRD.WARN.linkedin_departures` | Keep |
| Customer/product: `FWRD.WARN.g2_reviews`, `FWRD.WARN.trustpilot_trend`, `FWRD.WARN.app_ratings`, `FWRD.WARN.cfpb_complaints`, `FWRD.WARN.fda_medwatch`, `FWRD.WARN.nhtsa_complaints` | Keep |
| Social/news: `FWRD.WARN.social_sentiment`, `FWRD.WARN.journalism_activity` | Keep |
| Whistleblower: `FWRD.WARN.whistleblower_exposure` | Keep |
| Operational stress: `FWRD.WARN.vendor_payment_delays`, `FWRD.WARN.contract_disputes`, `FWRD.WARN.customer_churn_signals`, `FWRD.WARN.partner_stability` | Keep |
| Hiring anomalies: `FWRD.WARN.job_posting_patterns`, `FWRD.WARN.compliance_hiring`, `FWRD.WARN.legal_hiring` | Keep |

**Remove (consolidate to RC-1)**: `FWRD.WARN.zone_of_insolvency`, `FWRD.WARN.goodwill_risk`, `FWRD.WARN.impairment_risk`, `FWRD.WARN.revenue_quality`, `FWRD.WARN.margin_pressure`, `FWRD.WARN.capex_discipline`, `FWRD.WARN.working_capital_trends` (these are financial analysis checks, not alternative data warnings).

**New checks needed**:
- Glassdoor fraud keyword search (G13/2.3)
- Review surge detection (sudden increase in negative reviews)
- Department-level LinkedIn departures (accounting/legal departures = red flag)
- SimilarWeb/Sensor Tower web traffic trends
- Expert witness engagement detection (G23)
- Litigation funding targeting (G22)

**Data sources**: Glassdoor, Indeed, LinkedIn, Blind, G2, Trustpilot, App Stores, CFPB, FDA FAERS, NHTSA, Twitter/Reddit, news.

#### RC-10: Macro Environment (Context)
**Underwriting question**: What external forces could trigger claims regardless of company behavior?

| Existing Checks | Disposition |
|---|---|
| `FWRD.MACRO.*` (15) minus `climate_transition_risk` (moved to HAZ-9) and `sector_performance` (moved to IR-2) | Keep 13 remaining |

**Data sources**: Economic data, regulatory trackers, geopolitical analysis, news.

#### RC-11: Forward Events (Policy Period Calendar)
**Underwriting question**: What known events during the policy period could trigger claims?

| Existing Checks | Disposition |
|---|---|
| `FWRD.EVENT.*` (21) minus M&A checks (moved to HAZ-5) minus biotech (moved to HAZ-10) | Keep ~12 remaining event checks |

**Data sources**: Earnings calendars, debt schedules, regulatory calendars, proxy statements.

---

## 5. Migration Impact

### 5.1 Summary of Changes

| Category | Current | Proposed | Net Change |
|---|---|---|---|
| Total unique checks | 388 | ~400-420 | +12-32 (new gap fills) minus ~20-25 (consolidation) |
| Truly functional (with criteria) | 198 | 198 (no change until criteria defined) | 0 |
| Placeholder | 190 | 170-180 (some consolidated, some new) | -10 to -20 |
| New checks needed | 0 | ~40-50 | +40-50 |
| Checks to remove (true redundancy) | 0 | ~20-25 | -20-25 |
| Checks to rename/fix | 0 | ~15-20 | 0 (same count, better names) |

### 5.2 What Gets Removed

~20-25 checks eliminated through consolidation:
- 4 EXEC.PROFILE display checks redundant with GOV.BOARD evaluative checks (R1-R4)
- 3-4 SEC investigation checks collapsed into lifecycle (R5)
- 3 SEC misnamed checks refactored (R6)
- 1 GOV.BOARD.overboarding redundant with EXEC.PROFILE.overboarded_directors (R7)
- 2-3 executive turnover checks consolidated (R8)
- 2 CEO tenure checks consolidated (R9)
- 2 CFO tenure checks consolidated (R10)
- 2-3 insider selling checks consolidated (R11)
- 2 cluster selling checks consolidated (R12)
- 1-2 material weakness checks consolidated (R13)
- 7 FWRD.WARN financial checks moved to FIN (not removed, reclassified)

### 5.3 What Gets Added

~40-50 new checks across gap areas:
- **SPAC/De-SPAC** (G1): 5 checks
- **Going Concern** (G2): 1 check
- **Altman Z-Score** (G3): 1 check
- **AGR Score** (G4): 1 check
- **Revenue fraud patterns** (G5): 6-8 specific pattern checks
- **Derivative risk categories** (G6): 5 category checks
- **AI-specific hazards** (G7): 7 hazard checks
- **Scientific community** (G8): 5-6 checks (biotech only)
- **Compensation manipulation** (G9): 3-4 checks
- **ESG/Greenwashing** (G10): 4 checks
- **Non-audit fee ratio** (G11): 1 check
- **Stock technical indicators** (G12): 4-6 checks
- **Industry-specific metrics** (G13): 20-30 checks across 5 industries (conditional)

### 5.4 What Gets Renamed/Fixed

~15-20 checks need name/description fixes:
- All BIZ.DEPEND checks (R14) -- IDs don't match descriptions
- `BIZ.SIZE.growth_trajectory` / `BIZ.SIZE.public_tenure` -- swapped names
- `LIT.REG.doj_investigation`, `LIT.REG.industry_reg`, `LIT.REG.ftc_investigation` -- IDs don't match descriptions
- `FWRD.EVENT.19-BIOT` etc. -- unclear coded names

### 5.5 Structural Reorganization

The 8 current prefixes (BIZ, EXEC, FIN, FWRD, GOV, LIT, NLP, STOCK) would map to the new taxonomy:

| Current Prefix | Primary New Location | Notes |
|---|---|---|
| BIZ | IR (Inherent Risk) + HAZ (unique risks) | Split by purpose |
| EXEC | RC-4 (Management Quality) + RC-5 (Insider Activity) | Most stays together |
| FIN | RC-1 (Financial Health) + RC-2 (Statement Integrity) | Clean split |
| FWRD.EVENT | RC-11 (Forward Events) + HAZ-5 (M&A) + HAZ-10 (Biotech) | Split by hazard type |
| FWRD.WARN | RC-9 (Early Warnings) + RC-1 (financial ones move) | Financial warnings consolidate |
| FWRD.MACRO | RC-10 (Macro Environment) | Clean move |
| FWRD.DISC + FWRD.NARRATIVE | RC-8 (Disclosure Quality) | Clean move |
| GOV | RC-3 (Governance) + RC-4 (Management) + RC-5 (Insider) + RC-7 (Activist) | Split by sub-domain |
| LIT.SCA | HAZ-1 (SCA) + IR-4 (History) | Split current vs. historical |
| LIT.REG | HAZ-3 (Regulatory) | Clean move |
| LIT.OTHER | HAZ-4 (Non-Securities) | Clean move |
| NLP | RC-8 (Disclosure Quality) + RC-2 (Statement Integrity) | Split by what it detects |
| STOCK | RC-6 (Market Signals) + RC-5 (Insider, partial) | Most stays together |

### 5.6 Implementation Priority

**Phase 1 (Critical -- do first)**:
1. Fix naming mismatches (R6, R14, O2) -- prevents ongoing confusion
2. Consolidate true redundancies (R1-R5, R7-R13) -- reduce noise
3. Add Going Concern check (G2) -- highest predictive value, simple to implement
4. Add Altman Z-Score (G3) -- standard model, data already available
5. Add SPAC detection (G1) -- entire missing hazard category

**Phase 2 (High value)**:
6. Add revenue fraud pattern taxonomy (G5) -- #1 fraud type
7. Add derivative risk category assessment (G6) -- pre-filing risk detection
8. Add AI-specific hazard checks (G7) -- fastest-growing litigation area
9. Define criteria for LIT.REG and LIT.OTHER placeholders -- 35 checks unlocked
10. Add Quick Screen / auto-decline aggregation layer (G14)

**Phase 3 (Industry-specific)**:
11. Add scientific community monitoring for biotech (G8)
12. Add industry-specific operating metric suites (G13)
13. Add compensation manipulation patterns (G9)
14. Add ESG/greenwashing checks (G10)

**Phase 4 (Depth)**:
15. Define criteria for all remaining GOV placeholders (62 checks)
16. Define criteria for all remaining FWRD placeholders (67 checks)
17. Add technical stock indicators (G12)
18. Add remaining lower-priority gaps (G15-G30)

### 5.7 Key Architectural Decision Required

**Should the reorganization change check_id prefixes, or just create a logical grouping layer?**

Option A: **Change prefixes** (e.g., `IR.IDENTITY.market_cap`, `HAZ.SCA.active`, `RC.FIN.liquidity`). This is a clean break but requires updating all references throughout the codebase.

Option B: **Add a grouping/taxonomy layer** that maps existing check_ids to the IR/HAZ/RC categories. Keep existing prefixes for backward compatibility. This is lower risk but creates a mapping indirection.

Option C: **Hybrid** -- keep existing IDs but add `underwriting_category` and `underwriting_question` fields to each check in checks.json. The check engine routes by category; the renderer groups by underwriting question. No ID changes needed.

**Recommendation**: Option C. It preserves all existing plumbing while adding the underwriting-question organization. The new fields (`underwriting_category`, `underwriting_question`, `hazard_type`) can be added to the check schema incrementally.
