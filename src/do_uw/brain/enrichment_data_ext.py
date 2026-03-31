"""Extended enrichment mapping tables: risk framework layers and characteristics.

Split from enrichment_data.py for file length compliance (<500 lines).
Contains CHECK_TO_RISK_FRAMEWORK_LAYER and CHECK_TO_CHARACTERISTIC mappings.

See enrichment_data.py module docstring for full v6 section/taxonomy context.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 5. CHECK_TO_RISK_FRAMEWORK_LAYER
# Override mappings for checks that are NOT 'risk_modifier' (the default).
# Phase 42 renames: hazard -> peril_indicator, risk_characteristic -> risk_modifier
# Inherent risk: structural company attributes that determine base risk level.
# Peril indicator: specific loss scenarios or direct indicators of claims.
# ---------------------------------------------------------------------------

CHECK_TO_RISK_FRAMEWORK_LAYER: dict[str, str] = {
    # --- Inherent Risk: Company structure/identity ---
    "BIZ.CLASS.primary": "inherent_risk",
    "BIZ.CLASS.secondary": "inherent_risk",
    "BIZ.CLASS.litigation_history": "inherent_risk",
    "BIZ.SIZE.market_cap": "inherent_risk",
    "BIZ.SIZE.revenue_ttm": "inherent_risk",
    "BIZ.SIZE.employees": "inherent_risk",
    "BIZ.SIZE.growth_trajectory": "inherent_risk",
    "BIZ.SIZE.public_tenure": "inherent_risk",
    "BIZ.MODEL.description": "inherent_risk",
    "BIZ.MODEL.revenue_type": "inherent_risk",
    "BIZ.MODEL.revenue_segment": "inherent_risk",
    "BIZ.MODEL.revenue_geo": "inherent_risk",
    "BIZ.MODEL.cost_structure": "inherent_risk",
    "BIZ.MODEL.leverage_ops": "inherent_risk",
    "BIZ.MODEL.regulatory_dep": "inherent_risk",
    "BIZ.MODEL.capital_intensity": "inherent_risk",
    "BIZ.COMP.market_position": "inherent_risk",
    "BIZ.COMP.market_share": "inherent_risk",
    "BIZ.COMP.competitive_advantage": "inherent_risk",
    "BIZ.COMP.barriers_entry": "inherent_risk",
    "BIZ.COMP.barriers": "inherent_risk",
    "BIZ.COMP.moat": "inherent_risk",
    "BIZ.COMP.threat_assessment": "inherent_risk",
    "BIZ.COMP.industry_growth": "inherent_risk",
    "BIZ.COMP.headwinds": "inherent_risk",
    "BIZ.COMP.consolidation": "inherent_risk",
    "BIZ.COMP.peer_litigation": "inherent_risk",
    "BIZ.DEPEND.customer_conc": "inherent_risk",
    "BIZ.DEPEND.supplier_conc": "inherent_risk",
    "BIZ.DEPEND.tech_dep": "inherent_risk",
    "BIZ.DEPEND.key_person": "inherent_risk",
    "BIZ.DEPEND.regulatory_dep": "inherent_risk",
    "BIZ.DEPEND.capital_dep": "inherent_risk",
    "BIZ.DEPEND.macro_sensitivity": "inherent_risk",
    "BIZ.DEPEND.distribution": "inherent_risk",
    "BIZ.DEPEND.contract_terms": "inherent_risk",
    "BIZ.DEPEND.labor": "inherent_risk",
    # BIZ.STRUCT: corporate structure is inherent risk
    "BIZ.STRUCT.subsidiary_count": "inherent_risk",
    "BIZ.STRUCT.vie_spe": "inherent_risk",
    "BIZ.STRUCT.related_party": "inherent_risk",

    # --- Hazard: Litigation checks (direct loss scenarios) ---
    "LIT.SCA.active": "peril_indicator",
    "LIT.SCA.allegations": "peril_indicator",
    "LIT.SCA.case_status": "peril_indicator",
    "LIT.SCA.class_period": "peril_indicator",
    "LIT.SCA.demand": "peril_indicator",
    "LIT.SCA.derivative": "peril_indicator",
    "LIT.SCA.dismiss_basis": "peril_indicator",
    "LIT.SCA.erisa": "peril_indicator",
    "LIT.SCA.exposure": "peril_indicator",
    "LIT.SCA.filing_date": "peril_indicator",
    "LIT.SCA.historical": "peril_indicator",
    "LIT.SCA.lead_plaintiff": "peril_indicator",
    "LIT.SCA.merger_obj": "peril_indicator",
    "LIT.SCA.policy_status": "peril_indicator",
    "LIT.SCA.prefiling": "peril_indicator",
    "LIT.SCA.prior_dismiss": "peril_indicator",
    "LIT.SCA.prior_settle": "peril_indicator",
    "LIT.SCA.search": "peril_indicator",
    "LIT.SCA.settle_amount": "peril_indicator",
    "LIT.SCA.settle_date": "peril_indicator",
    "LIT.REG.sec_investigation": "peril_indicator",
    "LIT.REG.sec_active": "peril_indicator",
    "LIT.REG.sec_severity": "peril_indicator",
    "LIT.REG.wells_notice": "peril_indicator",
    "LIT.REG.comment_letters": "peril_indicator",
    "LIT.REG.cease_desist": "peril_indicator",
    "LIT.REG.civil_penalty": "peril_indicator",
    "LIT.REG.consent_order": "peril_indicator",
    "LIT.REG.subpoena": "peril_indicator",
    "LIT.REG.doj_investigation": "peril_indicator",
    "LIT.REG.deferred_pros": "peril_indicator",
    "LIT.REG.foreign_gov": "peril_indicator",
    "LIT.REG.industry_reg": "peril_indicator",
    "LIT.REG.ftc_investigation": "peril_indicator",
    "LIT.REG.cfpb_action": "peril_indicator",
    "LIT.REG.fdic_order": "peril_indicator",
    "LIT.REG.fda_warning": "peril_indicator",
    "LIT.REG.epa_action": "peril_indicator",
    "LIT.REG.osha_citation": "peril_indicator",
    "LIT.REG.dol_audit": "peril_indicator",
    "LIT.REG.state_ag": "peril_indicator",
    "LIT.REG.state_action": "peril_indicator",
    "LIT.OTHER.product": "peril_indicator",
    "LIT.OTHER.employment": "peril_indicator",
    "LIT.OTHER.ip": "peril_indicator",
    "LIT.OTHER.environmental": "peril_indicator",
    "LIT.OTHER.contract": "peril_indicator",
    "LIT.OTHER.class_action": "peril_indicator",
    "LIT.OTHER.antitrust": "peril_indicator",
    "LIT.OTHER.trade_secret": "peril_indicator",
    "LIT.OTHER.whistleblower": "peril_indicator",
    "LIT.OTHER.cyber_breach": "peril_indicator",
    "LIT.OTHER.bankruptcy": "peril_indicator",
    "LIT.OTHER.foreign_suit": "peril_indicator",
    "LIT.OTHER.gov_contract": "peril_indicator",
    "LIT.OTHER.aggregate": "peril_indicator",
    "STOCK.LIT.existing_action": "peril_indicator",
    # LIT.DEFENSE: defense posture checks are hazard-related
    "LIT.DEFENSE.forum_selection": "peril_indicator",
    "LIT.DEFENSE.contingent_liabilities": "peril_indicator",
    "LIT.DEFENSE.pslra_safe_harbor": "peril_indicator",
    # LIT.PATTERN: litigation pattern checks are hazard indicators
    "LIT.PATTERN.sol_windows": "peril_indicator",
    "LIT.PATTERN.industry_theories": "peril_indicator",
    "LIT.PATTERN.peer_contagion": "peril_indicator",
    "LIT.PATTERN.temporal_correlation": "peril_indicator",
    # LIT.SECTOR: sector-specific litigation is hazard-related
    "LIT.SECTOR.industry_patterns": "peril_indicator",
    "LIT.SECTOR.regulatory_databases": "peril_indicator",

    # --- Hazard: Forward events that could trigger claims ---
    "FWRD.EVENT.earnings_calendar": "peril_indicator",
    "FWRD.EVENT.guidance_risk": "peril_indicator",
    "FWRD.EVENT.catalyst_dates": "peril_indicator",
    "FWRD.EVENT.debt_maturity": "peril_indicator",
    "FWRD.EVENT.covenant_test": "peril_indicator",
    "FWRD.EVENT.lockup_expiry": "peril_indicator",
    "FWRD.EVENT.warrant_expiry": "peril_indicator",
    "FWRD.EVENT.contract_renewal": "peril_indicator",
    "FWRD.EVENT.regulatory_decision": "peril_indicator",
    "FWRD.EVENT.litigation_milestone": "peril_indicator",
    "FWRD.EVENT.shareholder_mtg": "peril_indicator",
    "FWRD.EVENT.ma_closing": "peril_indicator",
    "FWRD.EVENT.synergy": "peril_indicator",
    "FWRD.EVENT.customer_retention": "peril_indicator",
    "FWRD.EVENT.employee_retention": "peril_indicator",
    "FWRD.EVENT.integration": "peril_indicator",
    "FWRD.EVENT.proxy_deadline": "peril_indicator",
    "FWRD.EVENT.19-BIOT": "peril_indicator",
    "FWRD.EVENT.20-BIOT": "peril_indicator",
    "FWRD.EVENT.21-BIOT": "peril_indicator",
    "FWRD.EVENT.22-HLTH": "peril_indicator",
}
# Everything else defaults to "risk_modifier"


# ---------------------------------------------------------------------------
# 6. CHECK_TO_CHARACTERISTIC
# Maps signal_id to (direction, strength) for key risk characteristics.
# From BRAIN-DESIGN.md Section 1 "Risk Characteristics by Strength" table.
# direction: "amplifier" | "mitigator" | "context"
# strength: "very_strong" | "strong" | "moderate" | "weak"
# Only checks that are risk_characteristics and have known signal properties.
# ---------------------------------------------------------------------------

CHECK_TO_CHARACTERISTIC: dict[str, tuple[str, str]] = {
    # --- Very Strong Amplifiers ---
    # Financial distress signals
    "FIN.LIQ.position": ("amplifier", "very_strong"),
    "FIN.LIQ.cash_burn": ("amplifier", "very_strong"),
    "FIN.LIQ.working_capital": ("amplifier", "very_strong"),
    "FIN.DEBT.structure": ("amplifier", "very_strong"),
    "FIN.DEBT.coverage": ("amplifier", "very_strong"),
    "FIN.TEMPORAL.cash_flow_deterioration": ("amplifier", "very_strong"),
    "FWRD.WARN.zone_of_insolvency": ("amplifier", "very_strong"),
    "STOCK.PATTERN.death_spiral": ("amplifier", "very_strong"),

    # Insider trading at suspicious times
    "GOV.INSIDER.cluster_sales": ("amplifier", "very_strong"),
    "GOV.INSIDER.unusual_timing": ("amplifier", "very_strong"),
    "EXEC.INSIDER.cluster_selling": ("amplifier", "very_strong"),
    "EXEC.INSIDER.non_10b51": ("amplifier", "very_strong"),
    "STOCK.INSIDER.cluster_timing": ("amplifier", "very_strong"),

    # Financial restatement
    "FIN.ACCT.restatement": ("amplifier", "very_strong"),
    "FIN.ACCT.restatement_magnitude": ("amplifier", "very_strong"),
    "FIN.ACCT.restatement_pattern": ("amplifier", "very_strong"),

    # Material weakness in internal controls
    "FIN.ACCT.material_weakness": ("amplifier", "very_strong"),
    "FIN.ACCT.internal_controls": ("amplifier", "very_strong"),
    "GOV.EFFECT.material_weakness": ("amplifier", "very_strong"),

    # Recent significant stock drop
    "STOCK.PRICE.recent_drop_alert": ("amplifier", "very_strong"),
    "STOCK.PRICE.single_day_events": ("amplifier", "very_strong"),
    "STOCK.PATTERN.event_collapse": ("amplifier", "very_strong"),

    # --- Strong Amplifiers ---
    # M&A activity
    "FWRD.EVENT.ma_closing": ("amplifier", "strong"),
    "FWRD.EVENT.synergy": ("amplifier", "strong"),

    # High stock volatility
    "STOCK.PRICE.position": ("amplifier", "strong"),
    "STOCK.PATTERN.cascade": ("amplifier", "strong"),
    "STOCK.PATTERN.peer_divergence": ("amplifier", "strong"),

    # Short seller signals
    "STOCK.SHORT.position": ("amplifier", "strong"),
    "STOCK.SHORT.report": ("amplifier", "strong"),
    "STOCK.PATTERN.short_attack": ("amplifier", "strong"),

    # Aggressive guidance
    "FIN.GUIDE.track_record": ("amplifier", "strong"),
    "FIN.GUIDE.earnings_reaction": ("amplifier", "strong"),

    # Auditor change
    "GOV.EFFECT.auditor_change": ("amplifier", "strong"),
    "FIN.ACCT.restatement_auditor_link": ("amplifier", "strong"),

    # Forensic accounting signals
    "FIN.FORENSIC.fis_composite": ("amplifier", "strong"),
    "FIN.FORENSIC.dechow_f_score": ("amplifier", "strong"),
    "FIN.FORENSIC.montier_c_score": ("amplifier", "strong"),
    "FIN.FORENSIC.enhanced_sloan": ("amplifier", "strong"),
    "FIN.FORENSIC.accrual_intensity": ("amplifier", "strong"),
    "FIN.FORENSIC.beneish_dechow_convergence": ("amplifier", "strong"),

    # NLP disclosure signals
    "NLP.MDA.tone_shift": ("amplifier", "strong"),
    "NLP.RISK.new_risk_factors": ("amplifier", "strong"),
    "NLP.RISK.litigation_risk_factor_new": ("amplifier", "strong"),
    "NLP.WHISTLE.language_detected": ("amplifier", "strong"),
    "NLP.WHISTLE.internal_investigation": ("amplifier", "strong"),

    # --- Moderate Amplifiers ---
    # Governance weakness
    "GOV.BOARD.independence": ("amplifier", "moderate"),
    "GOV.BOARD.ceo_chair": ("amplifier", "moderate"),
    "GOV.BOARD.diversity": ("amplifier", "moderate"),
    "GOV.BOARD.overboarding": ("amplifier", "moderate"),
    "GOV.BOARD.tenure": ("amplifier", "moderate"),

    # Temporal financial deterioration
    "FIN.TEMPORAL.revenue_deceleration": ("amplifier", "moderate"),
    "FIN.TEMPORAL.margin_compression": ("amplifier", "moderate"),
    "FIN.TEMPORAL.operating_margin_compression": ("amplifier", "moderate"),
    "FIN.TEMPORAL.dso_expansion": ("amplifier", "moderate"),
    "FIN.TEMPORAL.cfo_ni_divergence": ("amplifier", "moderate"),
    "FIN.TEMPORAL.working_capital_deterioration": ("amplifier", "moderate"),
    "FIN.TEMPORAL.debt_ratio_increase": ("amplifier", "moderate"),
    "FIN.TEMPORAL.profitability_trend": ("amplifier", "moderate"),
    "FIN.TEMPORAL.earnings_quality_divergence": ("amplifier", "moderate"),

    # Earnings quality
    "FIN.QUALITY.revenue_quality_score": ("amplifier", "moderate"),
    "FIN.QUALITY.cash_flow_quality": ("amplifier", "moderate"),
    "FIN.QUALITY.dso_ar_divergence": ("amplifier", "moderate"),
    "FIN.QUALITY.q4_revenue_concentration": ("amplifier", "moderate"),
    "FIN.QUALITY.deferred_revenue_trend": ("amplifier", "moderate"),
    "FIN.QUALITY.quality_of_earnings": ("amplifier", "moderate"),
    "FIN.QUALITY.non_gaap_divergence": ("amplifier", "moderate"),

    # Executive turnover
    "GOV.EXEC.turnover_analysis": ("amplifier", "moderate"),
    "GOV.EXEC.turnover_pattern": ("amplifier", "moderate"),
    "GOV.EXEC.departure_context": ("amplifier", "moderate"),
    "EXEC.TENURE.ceo_new": ("amplifier", "moderate"),
    "EXEC.TENURE.cfo_new": ("amplifier", "moderate"),
    "EXEC.TENURE.c_suite_turnover": ("amplifier", "moderate"),
    "EXEC.DEPARTURE.cfo_departure_timing": ("amplifier", "moderate"),
    "EXEC.DEPARTURE.cao_departure": ("amplifier", "moderate"),

    # Filing timing
    "NLP.FILING.late_filing": ("amplifier", "moderate"),
    "NLP.FILING.filing_timing_change": ("amplifier", "moderate"),
    "GOV.EFFECT.late_filing": ("amplifier", "moderate"),
    "GOV.EFFECT.nt_filing": ("amplifier", "moderate"),

    # --- Moderate Mitigators ---
    # Strong governance
    "GOV.PAY.say_on_pay": ("mitigator", "moderate"),
    "GOV.PAY.clawback": ("mitigator", "moderate"),
    "GOV.EFFECT.audit_committee": ("mitigator", "moderate"),
    "GOV.EFFECT.sox_404": ("mitigator", "moderate"),

    # Big 4 auditor with long tenure
    "FIN.ACCT.auditor": ("mitigator", "moderate"),

    # --- Context (informational, direction depends on value) ---
    "STOCK.ANALYST.coverage": ("context", "moderate"),
    "STOCK.ANALYST.momentum": ("context", "moderate"),
    "STOCK.OWN.structure": ("context", "moderate"),
    "STOCK.OWN.concentration": ("context", "moderate"),
    "FIN.PROFIT.revenue": ("context", "moderate"),
    "FIN.PROFIT.margins": ("context", "moderate"),
    "FIN.PROFIT.earnings": ("context", "moderate"),
    "FIN.PROFIT.segment": ("context", "weak"),
    "FIN.LIQ.efficiency": ("context", "moderate"),
    "FIN.LIQ.trend": ("context", "moderate"),
    "FIN.DEBT.credit_rating": ("context", "moderate"),
    "FIN.DEBT.maturity": ("context", "moderate"),

    # --- BIZ.STRUCT: structural complexity context ---
    "BIZ.STRUCT.subsidiary_count": ("amplifier", "moderate"),
    "BIZ.STRUCT.vie_spe": ("amplifier", "strong"),
    "BIZ.STRUCT.related_party": ("amplifier", "strong"),

    # --- LIT.DEFENSE: defense posture mitigators ---
    "LIT.DEFENSE.forum_selection": ("mitigator", "moderate"),
    "LIT.DEFENSE.contingent_liabilities": ("amplifier", "strong"),
    "LIT.DEFENSE.pslra_safe_harbor": ("context", "moderate"),

    # --- LIT.PATTERN: litigation risk amplifiers ---
    "LIT.PATTERN.sol_windows": ("amplifier", "strong"),
    "LIT.PATTERN.industry_theories": ("amplifier", "moderate"),
    "LIT.PATTERN.peer_contagion": ("amplifier", "strong"),
    "LIT.PATTERN.temporal_correlation": ("amplifier", "very_strong"),

    # --- LIT.SECTOR: sector-specific context ---
    "LIT.SECTOR.industry_patterns": ("context", "moderate"),
    "LIT.SECTOR.regulatory_databases": ("amplifier", "moderate"),
}
