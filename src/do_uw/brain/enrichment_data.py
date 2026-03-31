"""Static enrichment mapping tables for brain check metadata.

Data-only module -- no logic. All mappings derived from QUESTIONS-FINAL.md
v6 taxonomy (5 sections, 36 subsections) and BRAIN-DESIGN.md risk characteristics.

v6 Section Boundaries (36 subsections after reorganization):
    1. COMPANY (1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 1.9, 1.11):
       Identity, business model, operations, structure, M&A, macro,
       early warning signals, risk calendar.
       Absorbed: 1.5 (Geographic -> 1.2+1.3), 1.7 (Competitive -> 1.2+1.8),
       1.10 (Company-specific -> 1.9). Merged: 1.9+1.10 -> 1.9.
    2. MARKET (2.1-2.8): Stock price, volatility, short interest, ownership,
       analysts, valuation, insider trading
    3. FINANCIAL (3.1-3.8): Liquidity, leverage, profitability, earnings quality,
       accounting, distress, guidance, sector KPIs
    4. GOVERNANCE & DISCLOSURE (4.1-4.4): People Risk, Structural Governance,
       Transparency & Disclosure, Activist Pressure.
       Reorganized: old 4.1+4.2 -> 4.1, old 4.3+4.4+RPT -> 4.2,
       old 4.6+4.7+4.8 -> 4.3, old 4.5 -> 4.4.
    5. LITIGATION & REGULATORY (5.1-5.7): SCAs, SCA history, derivative, SEC,
       other regulatory, non-securities, litigation risk analysis.
       Merged: 5.7+5.8+5.9 -> 5.7.

Data structures:
    PREFIX_TO_REPORT_SECTION: check prefix -> report section (5 v6 sections)
    CHECK_TO_RISK_QUESTIONS: signal_id -> risk question IDs (v6 X.Y subsections)
    CHECK_TO_HAZARDS: signal_id -> hazard codes (HAZ-*)
    CHECK_TO_RISK_FRAMEWORK_LAYER: signal_id -> framework layer override
    CHECK_TO_CHARACTERISTIC: signal_id -> (direction, strength)
    SUBDOMAIN_TO_RISK_QUESTIONS: prefix.subdomain -> default risk questions (v6 X.Y)
"""

from __future__ import annotations

from do_uw.brain.enrichment_data_ext import (
    CHECK_TO_CHARACTERISTIC,
    CHECK_TO_RISK_FRAMEWORK_LAYER,
)

__all__ = [
    "CHECK_TO_CHARACTERISTIC",
    "CHECK_TO_HAZARDS",
    "CHECK_TO_RISK_FRAMEWORK_LAYER",
    "CHECK_TO_RISK_QUESTIONS",
    "PREFIX_TO_REPORT_SECTION",
    "SUBDOMAIN_TO_RISK_QUESTIONS",
]

# ---------------------------------------------------------------------------
# 1. PREFIX_TO_REPORT_SECTION
# Maps check ID first segment to one of 5 v6 report sections.
# v6 sections: company, market, financial, governance, litigation
# ---------------------------------------------------------------------------

PREFIX_TO_REPORT_SECTION: dict[str, str] = {
    "BIZ": "company",
    "FIN": "financial",
    "GOV": "governance",
    "EXEC": "governance",
    "LIT": "litigation",
    "STOCK": "market",
    "NLP": "governance",      # disclosure merged into governance (Section 4) in v6
    "FWRD": "company",        # forward-looking maps to company risk calendar (1.11) in v6
}


# ---------------------------------------------------------------------------
# 2. SUBDOMAIN_TO_RISK_QUESTIONS
# Maps prefix.subdomain patterns to default v6 subsection IDs (X.Y format).
# Used as fallback when a signal_id is not explicitly in CHECK_TO_RISK_QUESTIONS.
# Granularity: SUBSECTION-LEVEL (45 entities), NOT individual question X.Y.Z.
# ---------------------------------------------------------------------------

SUBDOMAIN_TO_RISK_QUESTIONS: dict[str, list[str]] = {
    # Company / Business (BIZ.*)
    "BIZ.CLASS": ["1.1"],       # Identity
    "BIZ.SIZE": ["1.1"],        # Identity (key company metrics)
    "BIZ.MODEL": ["1.2"],       # Business Model & Revenue
    "BIZ.DEPEND": ["1.3"],      # Operations & Dependencies
    "BIZ.COMP": ["1.2", "1.8"], # Competitive Position -> absorbed into Business Model + Macro
    "BIZ.STRUCT": ["1.4"],      # Corporate Structure & Complexity
    "BIZ.UNI": ["1.3"],         # Operations & Dependencies (cyber, AI, hazard exposure, ESG)
    # Financial (FIN.*)
    "FIN.LIQ": ["3.1"],         # Liquidity & Solvency
    "FIN.DEBT": ["3.2"],        # Leverage & Debt Structure
    "FIN.PROFIT": ["3.3"],      # Profitability & Growth
    "FIN.TEMPORAL": ["3.3"],    # Profitability & Growth (trend analysis)
    "FIN.SECTOR": ["3.8"],      # Sector-Specific Financial Metrics
    "FIN.ACCT": ["3.5"],        # Accounting Integrity & Audit Risk
    "FIN.FORENSIC": ["3.4"],    # Earnings Quality & Forensic Analysis
    "FIN.QUALITY": ["3.4"],     # Earnings Quality & Forensic Analysis
    "FIN.GUIDE": ["3.7"],       # Guidance & Market Expectations
    # Governance (GOV.*) — Section 4 reorganized: 4.1=People, 4.2=Structural, 4.3=Transparency, 4.4=Activist
    "GOV.BOARD": ["4.1"],       # People Risk (board composition)
    "GOV.EFFECT": ["4.1"],      # People Risk (governance effectiveness)
    "GOV.EXEC": ["4.1"],        # People Risk (executive team — old 4.2 -> new 4.1)
    "GOV.INSIDER": ["2.8"],     # Insider Trading Activity (moved to Market in v6)
    "GOV.PAY": ["4.2"],         # Structural Governance (compensation — old 4.3 -> new 4.2)
    "GOV.RIGHTS": ["4.2"],      # Structural Governance (shareholder rights — old 4.4 -> new 4.2)
    "GOV.ACTIVIST": ["4.4"],    # Activist Pressure (old 4.5 -> new 4.4)
    # Executive (EXEC.*) — all map to 4.1 People Risk (old 4.2 -> new 4.1)
    "EXEC.PROFILE": ["4.1"],    # People Risk
    "EXEC.CEO": ["4.1"],        # People Risk
    "EXEC.CFO": ["4.1"],        # People Risk
    "EXEC.AGGREGATE": ["4.1"],  # People Risk
    "EXEC.TENURE": ["4.1"],     # People Risk
    "EXEC.DEPARTURE": ["4.1"],  # People Risk
    "EXEC.PRIOR_LIT": ["4.1"],  # People Risk
    "EXEC.INSIDER": ["2.8"],    # Insider Trading Activity (moved to Market in v6)
    # Litigation (LIT.*) — 5.7+5.8+5.9 merged into 5.7
    "LIT.SCA": ["5.1"],         # Securities Class Actions (Active)
    "LIT.REG": ["5.4"],         # SEC Enforcement (+ 5.5 Other Regulatory)
    "LIT.OTHER": ["5.6"],       # Non-Securities Litigation
    "LIT.DEFENSE": ["5.7"],     # Litigation Risk Analysis (merged 5.7+5.8+5.9)
    "LIT.PATTERN": ["5.7"],     # Litigation Risk Analysis (old 5.8 -> 5.7)
    "LIT.SECTOR": ["5.7"],      # Litigation Risk Analysis (old 5.9 -> 5.7)
    # Stock / Market (STOCK.*)
    "STOCK.PRICE": ["2.1"],     # Stock Price Performance
    "STOCK.PATTERN": ["2.2"],   # Stock Drop Events
    "STOCK.SHORT": ["2.4"],     # Short Interest & Bearish Signals
    "STOCK.OWN": ["2.5"],       # Ownership Structure
    "STOCK.ANALYST": ["2.6"],   # Analyst Coverage & Sentiment
    "STOCK.VALUATION": ["2.7"], # Valuation Metrics
    "STOCK.TRADE": ["2.3"],     # Volatility & Trading Patterns
    "STOCK.INSIDER": ["2.8"],   # Insider Trading Activity
    "STOCK.LIT": ["5.1"],       # Securities Class Actions (Active)
    # NLP / Disclosure -> Transparency & Disclosure (new 4.3)
    "NLP.RISK": ["4.3"],        # Transparency & Disclosure (old 4.6 -> new 4.3)
    "NLP.MDA": ["4.3"],         # Transparency & Disclosure (old 4.7 -> new 4.3)
    "NLP.DISCLOSURE": ["4.3"],  # Transparency & Disclosure (old 4.6 -> new 4.3)
    "NLP.FILING": ["4.3"],      # Transparency & Disclosure (old 4.6 -> new 4.3)
    "NLP.WHISTLE": ["4.3"],     # Transparency & Disclosure (old 4.8 -> new 4.3)
    "NLP.CAM": ["3.5"],         # Accounting Integrity (CAMs are audit-related)
    # Forward-Looking -> Company Section in v6 (1.11 Risk Calendar & others)
    "FWRD.EVENT": ["1.11"],     # Risk Calendar & Upcoming Catalysts
    "FWRD.WARN": ["3.6"],       # Financial Distress Indicators (early warnings)
    "FWRD.MACRO": ["1.8"],      # Macro & Industry Environment
    "FWRD.DISC": ["4.3"],       # Transparency & Disclosure (old 4.6 -> new 4.3)
    "FWRD.NARRATIVE": ["4.3"],  # Transparency & Disclosure (old 4.7 -> new 4.3)
}


# ---------------------------------------------------------------------------
# 3. CHECK_TO_RISK_QUESTIONS
# Explicit per-check question mappings using v6 subsection IDs (X.Y format).
# Checks listed here override the subdomain default.
# Multi-question checks are listed with all applicable subsections.
# ---------------------------------------------------------------------------

CHECK_TO_RISK_QUESTIONS: dict[str, list[str]] = {
    # --- BIZ.CLASS: 1.1 (Identity) ---
    "BIZ.CLASS.primary": ["1.1"],
    "BIZ.CLASS.secondary": ["1.1"],
    "BIZ.CLASS.litigation_history": ["1.1", "5.2"],  # also informs SCA history

    # --- BIZ.COMP: 1.2+1.8 (absorbed Competitive Position) ---
    "BIZ.COMP.peer_litigation": ["1.2", "5.7"],  # peer litigation ties to litigation risk analysis

    # --- BIZ.MODEL: 1.2 (Business Model) + 1.3 (Operations) for geo ---
    "BIZ.MODEL.revenue_geo": ["1.2", "1.3"],  # geography absorbed into Business Model + Operations

    # --- BIZ.SIZE: 1.1 (Identity) + 1.9 (Early Warning Signals) ---
    "BIZ.SIZE.employees": ["1.1", "1.9"],  # employee count -> Early Warning Signals

    # --- BIZ.DEPEND: 1.3 (Operations) + 1.9 (Early Warning Signals) ---
    "BIZ.DEPEND.customer_conc": ["1.3", "1.9"],  # customer risk -> Early Warning Signals
    "BIZ.DEPEND.labor": ["1.3", "1.9"],            # labor risk -> Early Warning Signals

    # --- BIZ.UNI: 1.3 (Operations & Dependencies) + 1.9 (Early Warning Signals) ---
    "BIZ.UNI.ai_claims": ["1.3", "1.9"],          # unique company risk (1.10 merged into 1.9)
    "BIZ.UNI.cyber_posture": ["1.3", "1.9"],      # unique company risk
    "BIZ.UNI.cyber_business": ["1.3", "1.9"],     # unique company risk

    # --- BIZ.STRUCT: 1.4 (Corporate Structure & Complexity) ---
    "BIZ.STRUCT.subsidiary_count": ["1.4"],
    "BIZ.STRUCT.vie_spe": ["1.4"],
    "BIZ.STRUCT.related_party": ["1.4", "4.2"],  # also Structural Governance (RPT)

    # --- FIN distress checks ---
    "FIN.TEMPORAL.revenue_deceleration": ["3.3"],       # Profitability & Growth
    "FIN.TEMPORAL.margin_compression": ["3.3"],          # Profitability & Growth
    "FIN.TEMPORAL.cash_flow_deterioration": ["3.3"],     # Profitability & Growth
    "FIN.TEMPORAL.profitability_trend": ["3.3"],         # Profitability & Growth
    "FIN.TEMPORAL.earnings_quality_divergence": ["3.3", "3.4"],  # also Earnings Quality

    # --- FIN.QUALITY checks that span profitability and earnings quality ---
    "FIN.QUALITY.cash_flow_quality": ["3.3", "3.4"],
    "FIN.QUALITY.quality_of_earnings": ["3.3", "3.4"],
    "FIN.QUALITY.non_gaap_divergence": ["3.4", "3.7"],  # Earnings Quality + Guidance credibility

    # --- FIN.ACCT restatement checks ---
    "FIN.ACCT.restatement": ["3.5"],
    "FIN.ACCT.restatement_magnitude": ["3.5"],
    "FIN.ACCT.restatement_pattern": ["3.5"],
    "FIN.ACCT.restatement_auditor_link": ["3.5"],
    "FIN.ACCT.restatement_stock_window": ["3.5", "2.2"],  # stock drop impact
    "FIN.ACCT.material_weakness": ["3.5"],
    "FIN.ACCT.internal_controls": ["3.5"],
    "FIN.ACCT.sec_correspondence": ["3.5", "5.4"],    # SEC enforcement

    # --- EXEC.PROFILE board/governance checks -> 4.1 People Risk ---
    "EXEC.PROFILE.board_size": ["4.1"],
    "EXEC.PROFILE.avg_tenure": ["4.1"],
    "EXEC.PROFILE.ceo_chair_duality": ["4.1"],
    "EXEC.PROFILE.independent_ratio": ["4.1"],
    "EXEC.PROFILE.overboarded_directors": ["4.1"],

    # --- GOV.EFFECT checks that span governance and financial ---
    "GOV.EFFECT.auditor_change": ["4.1", "3.5"],       # governance + accounting integrity
    "GOV.EFFECT.material_weakness": ["4.1", "3.5"],
    "GOV.EFFECT.late_filing": ["4.1", "4.3"],           # governance + transparency
    "GOV.EFFECT.nt_filing": ["4.1", "4.3"],

    # --- GOV.EXEC / EXEC checks -> 4.1 People Risk ---
    "GOV.EXEC.officer_litigation": ["4.1", "5.1"],      # officer lit ties to SCA
    "EXEC.PRIOR_LIT.any_officer": ["4.1", "5.2"],       # SCA history
    "EXEC.PRIOR_LIT.ceo_cfo": ["4.1", "5.2"],
    "EXEC.DEPARTURE.cfo_departure_timing": ["4.1", "3.6"],  # financial distress indicator
    "EXEC.DEPARTURE.cao_departure": ["4.1", "3.6"],

    # --- Insider trading: GOV.INSIDER, EXEC.INSIDER, STOCK.INSIDER -> 2.8 ---
    "GOV.INSIDER.form4_filings": ["2.8"],
    "GOV.INSIDER.net_selling": ["2.8"],
    "GOV.INSIDER.executive_sales": ["2.8"],
    "GOV.INSIDER.ownership_pct": ["2.8"],
    "GOV.INSIDER.ownership_concentration": ["2.8"],
    "GOV.INSIDER.exercise_sell": ["2.8"],
    "GOV.INSIDER.timing_suspect": ["2.8"],
    "GOV.INSIDER.10b5_plans": ["2.8"],
    "GOV.INSIDER.plan_adoption": ["2.8"],
    "GOV.INSIDER.cluster_sales": ["2.8"],
    "GOV.INSIDER.unusual_timing": ["2.8"],
    "EXEC.INSIDER.ceo_net_selling": ["2.8"],
    "EXEC.INSIDER.cfo_net_selling": ["2.8"],
    "EXEC.INSIDER.cluster_selling": ["2.8"],
    "EXEC.INSIDER.non_10b51": ["2.8"],
    "STOCK.INSIDER.summary": ["2.8"],
    "STOCK.INSIDER.notable_activity": ["2.8"],
    "STOCK.INSIDER.cluster_timing": ["2.8"],

    # --- GOV.ACTIVIST checks -> 4.4 Activist Pressure, some also 2.5 ---
    "GOV.ACTIVIST.13d_filings": ["4.4", "2.5"],
    "GOV.ACTIVIST.schedule_13g": ["4.4", "2.5"],

    # --- STOCK.OWN -> 2.5, activist also 4.4 ---
    "STOCK.OWN.activist": ["4.4", "2.5"],

    # --- STOCK.SHORT -> 2.4 (Short Interest), also financial signal ---
    "STOCK.SHORT.position": ["2.4", "3.6"],    # financial distress indicator
    "STOCK.SHORT.trend": ["2.4"],
    "STOCK.SHORT.report": ["2.4"],

    # --- STOCK.PRICE checks -> 2.1 / 2.2 ---
    "STOCK.PRICE.recent_drop_alert": ["2.2"],           # Stock Drop Events
    "STOCK.PRICE.delisting_risk": ["2.1", "3.6"],       # financial distress indicator
    "STOCK.PATTERN.death_spiral": ["2.2", "3.6"],       # financial distress pattern
    "STOCK.PATTERN.short_attack": ["2.2", "2.4"],       # short selling crossover

    # --- STOCK.LIT -> 5.1 + 2.2 ---
    "STOCK.LIT.existing_action": ["5.1", "2.2"],

    # --- NLP checks -> 4.3 Transparency & Disclosure ---
    "NLP.WHISTLE.language_detected": ["4.3"],            # Whistleblower in Transparency
    "NLP.WHISTLE.internal_investigation": ["4.3"],
    "NLP.FILING.late_filing": ["4.3", "4.1"],           # Transparency + governance issue

    # --- FWRD.EVENT checks -> 1.11 (Risk Calendar) ---
    "FWRD.EVENT.earnings_calendar": ["1.11"],
    "FWRD.EVENT.guidance_risk": ["1.11", "3.7"],         # guidance credibility crossover
    "FWRD.EVENT.debt_maturity": ["1.11", "3.2"],         # leverage crossover
    "FWRD.EVENT.covenant_test": ["1.11", "3.2"],
    "FWRD.EVENT.litigation_milestone": ["1.11", "5.1"],  # litigation crossover
    "FWRD.EVENT.ma_closing": ["1.11", "1.6"],            # M&A crossover
    "FWRD.EVENT.regulatory_decision": ["1.11", "5.5"],   # regulatory crossover
    "FWRD.EVENT.customer_retention": ["1.11", "1.9"],    # Early Warning Signals
    "FWRD.EVENT.employee_retention": ["1.11", "1.9"],    # Early Warning Signals

    # --- FWRD.WARN financial early warnings -> 3.6 (Distress) + others ---
    "FWRD.WARN.zone_of_insolvency": ["3.6", "3.1"],     # Distress + Liquidity
    "FWRD.WARN.goodwill_risk": ["3.6", "1.6"],           # Distress + M&A (goodwill)
    "FWRD.WARN.impairment_risk": ["3.6", "3.3"],         # Distress + Profitability
    "FWRD.WARN.revenue_quality": ["3.6", "3.4"],         # Distress + Earnings Quality
    "FWRD.WARN.margin_pressure": ["3.6", "3.3"],         # Distress + Profitability
    "FWRD.WARN.capex_discipline": ["3.6", "3.3"],        # Distress + Profitability
    "FWRD.WARN.working_capital_trends": ["3.6", "3.1"],  # Distress + Liquidity

    # --- FWRD.WARN customer/employee warnings -> 3.6 (Distress) + 1.9 (Early Warning) ---
    "FWRD.WARN.customer_churn_signals": ["3.6", "1.9"],  # Early Warning Signals

    # --- FWRD.WARN AI/tech warnings -> 3.6 (Distress) + 1.3 (Dependencies/hazards) ---
    "FWRD.WARN.ai_revenue_concentration": ["3.6", "1.3"],
    "FWRD.WARN.hyperscaler_dependency": ["3.6", "1.3"],
    "FWRD.WARN.gpu_allocation": ["3.6", "1.3"],
    "FWRD.WARN.data_center_risk": ["3.6", "1.3"],

    # --- FWRD.MACRO -> 1.8 (Macro) + 1.3 (Operations, geographic exposure) ---
    "FWRD.MACRO.geopolitical_exposure": ["1.8", "1.3"],  # Geographic absorbed into Operations

    # --- LIT.SCA derivative checks -> 5.1 (Active SCA) + 5.3 (Derivative Litigation) ---
    "LIT.SCA.derivative": ["5.1", "5.3"],    # Derivative Litigation
    "LIT.SCA.demand": ["5.1", "5.3"],         # Derivative Demand
    "LIT.SCA.merger_obj": ["5.1", "5.3"],     # Merger Objection -> derivative

    # --- LIT.REG foreign -> 5.4 (SEC) + 1.3 (Operations, geographic) ---
    "LIT.REG.foreign_gov": ["5.4", "1.3"],   # Foreign government -> Operations (geo absorbed)

    # --- LIT.OTHER foreign -> 5.6 (Non-Securities) + 1.3 (Operations, geographic) ---
    "LIT.OTHER.foreign_suit": ["5.6", "1.3"],  # Foreign suit -> Operations (geo absorbed)

    # --- FWRD.WARN media/narrative -> 3.6 (Distress) + 1.9 (Early Warning Signals) ---
    "FWRD.WARN.social_sentiment": ["3.6", "1.9"],    # Distress + Early Warning (media absorbed)
    "FWRD.WARN.journalism_activity": ["3.6", "1.9"], # Distress + Early Warning (media absorbed)

    # --- LIT.DEFENSE: 5.7 (Litigation Risk Analysis — merged) ---
    "LIT.DEFENSE.forum_selection": ["5.7"],
    "LIT.DEFENSE.contingent_liabilities": ["5.7"],
    "LIT.DEFENSE.pslra_safe_harbor": ["5.7"],

    # --- LIT.PATTERN: 5.7 (Litigation Risk Analysis — merged from old 5.8) ---
    "LIT.PATTERN.sol_windows": ["5.7"],
    "LIT.PATTERN.industry_theories": ["5.7"],
    "LIT.PATTERN.peer_contagion": ["5.7", "1.2"],           # also Business Model (competitive)
    "LIT.PATTERN.temporal_correlation": ["5.7", "2.2"],     # also Stock Drop Events

    # --- LIT.SECTOR: 5.7 (Litigation Risk Analysis — merged from old 5.9) ---
    "LIT.SECTOR.industry_patterns": ["5.7"],
    "LIT.SECTOR.regulatory_databases": ["5.7"],
}


# ---------------------------------------------------------------------------
# 4. CHECK_TO_HAZARDS
# Maps signal_id to hazard codes from BRAIN-DESIGN.md hazard taxonomy.
# Checks not listed here have no specific hazard mapping (they are
# risk characteristics, not direct hazard indicators).
# ---------------------------------------------------------------------------

CHECK_TO_HAZARDS: dict[str, list[str]] = {
    # --- Securities Class Actions (HAZ-SCA) ---
    "LIT.SCA.active": ["HAZ-SCA"],
    "LIT.SCA.allegations": ["HAZ-SCA"],
    "LIT.SCA.case_status": ["HAZ-SCA"],
    "LIT.SCA.class_period": ["HAZ-SCA"],
    "LIT.SCA.demand": ["HAZ-SCA", "HAZ-DER"],
    "LIT.SCA.derivative": ["HAZ-SCA", "HAZ-DER"],
    "LIT.SCA.dismiss_basis": ["HAZ-SCA"],
    "LIT.SCA.erisa": ["HAZ-SCA", "HAZ-EMPL"],
    "LIT.SCA.exposure": ["HAZ-SCA"],
    "LIT.SCA.filing_date": ["HAZ-SCA"],
    "LIT.SCA.historical": ["HAZ-SCA"],
    "LIT.SCA.lead_plaintiff": ["HAZ-SCA"],
    "LIT.SCA.merger_obj": ["HAZ-SCA", "HAZ-DER"],
    "LIT.SCA.policy_status": ["HAZ-SCA"],
    "LIT.SCA.prefiling": ["HAZ-SCA"],
    "LIT.SCA.prior_dismiss": ["HAZ-SCA"],
    "LIT.SCA.prior_settle": ["HAZ-SCA"],
    "LIT.SCA.search": ["HAZ-SCA"],
    "LIT.SCA.settle_amount": ["HAZ-SCA"],
    "LIT.SCA.settle_date": ["HAZ-SCA"],
    "STOCK.LIT.existing_action": ["HAZ-SCA"],

    # --- SEC Enforcement (HAZ-SEC) ---
    "LIT.REG.sec_investigation": ["HAZ-SEC"],
    "LIT.REG.sec_active": ["HAZ-SEC"],
    "LIT.REG.sec_severity": ["HAZ-SEC"],
    "LIT.REG.wells_notice": ["HAZ-SEC"],
    "LIT.REG.comment_letters": ["HAZ-SEC"],
    "LIT.REG.cease_desist": ["HAZ-SEC"],
    "LIT.REG.civil_penalty": ["HAZ-SEC"],
    "LIT.REG.consent_order": ["HAZ-SEC"],
    "LIT.REG.subpoena": ["HAZ-SEC"],

    # --- DOJ Criminal (HAZ-DOJ) ---
    "LIT.REG.doj_investigation": ["HAZ-DOJ"],
    "LIT.REG.deferred_pros": ["HAZ-DOJ"],
    "LIT.REG.foreign_gov": ["HAZ-DOJ"],

    # --- Industry-Specific Regulatory (HAZ-REG) ---
    "LIT.REG.industry_reg": ["HAZ-REG"],
    "LIT.REG.ftc_investigation": ["HAZ-REG"],
    "LIT.REG.cfpb_action": ["HAZ-REG"],
    "LIT.REG.fdic_order": ["HAZ-REG"],
    "LIT.REG.fda_warning": ["HAZ-REG"],
    "LIT.REG.epa_action": ["HAZ-REG"],
    "LIT.REG.osha_citation": ["HAZ-REG"],
    "LIT.REG.dol_audit": ["HAZ-REG"],
    "LIT.REG.state_ag": ["HAZ-REG"],
    "LIT.REG.state_action": ["HAZ-REG"],

    # --- Bankruptcy/Insolvency (HAZ-BANK) ---
    "FIN.LIQ.cash_burn": ["HAZ-BANK"],
    "FIN.DEBT.covenants": ["HAZ-BANK"],
    "FIN.DEBT.maturity": ["HAZ-BANK"],
    "FIN.TEMPORAL.cash_flow_deterioration": ["HAZ-BANK"],
    "FWRD.WARN.zone_of_insolvency": ["HAZ-BANK"],
    "STOCK.PRICE.delisting_risk": ["HAZ-BANK"],
    "STOCK.PATTERN.death_spiral": ["HAZ-BANK"],
    "LIT.OTHER.bankruptcy": ["HAZ-BANK"],

    # --- Employment (HAZ-EMPL) ---
    "LIT.OTHER.employment": ["HAZ-EMPL"],
    "LIT.OTHER.whistleblower": ["HAZ-EMPL"],

    # --- Cyber (HAZ-CYBER) ---
    "BIZ.UNI.cyber_posture": ["HAZ-CYBER"],
    "BIZ.UNI.cyber_business": ["HAZ-CYBER"],
    "LIT.OTHER.cyber_breach": ["HAZ-CYBER"],

    # --- AI (HAZ-AI) ---
    "BIZ.UNI.ai_claims": ["HAZ-AI"],
    "FWRD.WARN.ai_revenue_concentration": ["HAZ-AI"],
    "FWRD.WARN.hyperscaler_dependency": ["HAZ-AI"],
    "FWRD.WARN.gpu_allocation": ["HAZ-AI"],
    "FWRD.WARN.data_center_risk": ["HAZ-AI"],

    # --- ESG (HAZ-ESG) ---
    "LIT.OTHER.environmental": ["HAZ-ESG"],

    # --- Antitrust (HAZ-ANTITRUST) ---
    "LIT.OTHER.antitrust": ["HAZ-ANTITRUST"],

    # --- IP (HAZ-IP) ---
    "LIT.OTHER.ip": ["HAZ-IP"],

    # --- Product Liability (HAZ-PRODUCT) ---
    "LIT.OTHER.product": ["HAZ-PRODUCT"],

    # --- Derivative (HAZ-DER) ---
    "LIT.SCA.derivative": ["HAZ-SCA", "HAZ-DER"],
    "LIT.SCA.demand": ["HAZ-SCA", "HAZ-DER"],

    # --- Insider trading checks -> HAZ-SCA + HAZ-SEC ---
    "GOV.INSIDER.cluster_sales": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.unusual_timing": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.net_selling": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.executive_sales": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.ownership_concentration": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.exercise_sell": ["HAZ-SCA", "HAZ-SEC"],
    "GOV.INSIDER.timing_suspect": ["HAZ-SCA", "HAZ-SEC"],
    "EXEC.INSIDER.ceo_net_selling": ["HAZ-SCA", "HAZ-SEC"],
    "EXEC.INSIDER.cfo_net_selling": ["HAZ-SCA", "HAZ-SEC"],
    "EXEC.INSIDER.cluster_selling": ["HAZ-SCA", "HAZ-SEC"],
    "EXEC.INSIDER.non_10b51": ["HAZ-SCA", "HAZ-SEC"],
    "STOCK.INSIDER.cluster_timing": ["HAZ-SCA", "HAZ-SEC"],

    # --- Restatement checks -> HAZ-SCA + HAZ-SEC ---
    "FIN.ACCT.restatement": ["HAZ-SCA", "HAZ-SEC"],
    "FIN.ACCT.restatement_magnitude": ["HAZ-SCA", "HAZ-SEC"],
    "FIN.ACCT.restatement_pattern": ["HAZ-SCA", "HAZ-SEC"],
    "FIN.ACCT.material_weakness": ["HAZ-SCA", "HAZ-SEC"],

    # --- M&A-related -> HAZ-DER + HAZ-ANTITRUST ---
    "FWRD.EVENT.ma_closing": ["HAZ-DER", "HAZ-ANTITRUST"],
    "FWRD.EVENT.synergy": ["HAZ-DER"],
    "LIT.SCA.merger_obj": ["HAZ-SCA", "HAZ-DER"],

    # --- Short selling -> HAZ-SCA ---
    "STOCK.SHORT.position": ["HAZ-SCA"],
    "STOCK.SHORT.report": ["HAZ-SCA"],
    "STOCK.PATTERN.short_attack": ["HAZ-SCA"],

    # --- Defense/Pattern/Sector checks ---
    "LIT.DEFENSE.contingent_liabilities": ["HAZ-SCA"],
    "LIT.PATTERN.sol_windows": ["HAZ-SCA"],
    "LIT.PATTERN.peer_contagion": ["HAZ-SCA"],
    "LIT.PATTERN.temporal_correlation": ["HAZ-SCA"],
    "LIT.SECTOR.regulatory_databases": ["HAZ-REG"],
}


