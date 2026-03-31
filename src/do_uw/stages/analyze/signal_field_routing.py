"""Check-to-field routing for the ANALYZE stage.

Maps each signal_id to the specific field key in the mapper return dict
that the check should evaluate. Without this, _first_data_value() grabs
the first non-None value, causing every check in a section to evaluate
the same (wrong) field.

Resolution order in narrow_result():
1. data_strategy.field_key from check definition (Phase 31 declarative)
2. Exact signal_id match in FIELD_FOR_CHECK (legacy)
3. Fallback: return full data dict (existing behavior)
"""

from __future__ import annotations

from typing import Any


def narrow_result(
    signal_id: str,
    data: dict[str, Any],
    signal_def: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Narrow a mapper result dict to the field relevant to this check.

    Resolution order:
    1. data_strategy.field_key from check definition (Phase 31 declarative)
    2. Exact signal_id match in FIELD_FOR_CHECK (legacy)
    3. Fallback: return full data dict (existing behavior)
    """
    # Phase 31: declarative field_key from check definition
    if signal_def is not None:
        ds = signal_def.get("data_strategy")
        if isinstance(ds, dict):
            fk = ds.get("field_key")
            if fk is not None:
                if fk in data:
                    return {fk: data[fk]}
                return {}  # Intended field missing -> DATA_UNAVAILABLE

    # Legacy: exact match in FIELD_FOR_CHECK
    field = FIELD_FOR_CHECK.get(signal_id)
    if field is not None:
        if field in data:
            return {field: data[field]}
        return {}  # Intended field missing -> DATA_UNAVAILABLE
    return data


# ---------------------------------------------------------------------------
# Check ID → field key mapping
#
# Organized by section/prefix. Only checks whose intended field differs
# from the first non-None value in the mapper output need entries here.
# Phase 26 checks (EXEC.*, NLP.*, FIN.TEMPORAL/FORENSIC/QUALITY) are
# handled by signal_mappers_analytical.py and don't need entries.
# ---------------------------------------------------------------------------

FIELD_FOR_CHECK: dict[str, str] = {
    # ── Section 1: Business Profile (BIZ.*) → company mapper ──
    # BIZ.CLASS
    "BIZ.CLASS.primary": "risk_classification",
    "BIZ.CLASS.secondary": "risk_classification",
    "BIZ.CLASS.litigation_history": "total_sca_count",
    # BIZ.COMP
    "BIZ.COMP.market_position": "sector",
    "BIZ.COMP.market_share": "sector",
    "BIZ.COMP.competitive_advantage": "sector",
    "BIZ.COMP.threat_assessment": "sector",
    "BIZ.COMP.barriers_entry": "barriers_to_entry",
    "BIZ.COMP.moat": "competitive_moat",
    "BIZ.COMP.barriers": "barriers_to_entry",
    "BIZ.COMP.industry_growth": "sector",
    "BIZ.COMP.headwinds": "industry_headwinds",
    "BIZ.COMP.consolidation": "sector",
    "BIZ.COMP.peer_litigation": "active_sca_count",
    # BIZ.DEPEND
    "BIZ.DEPEND.customer_conc": "customer_concentration",
    "BIZ.DEPEND.supplier_conc": "supplier_concentration",
    "BIZ.DEPEND.tech_dep": "technology_dependency_count",
    # Phase 33-02: key_person is "Customer Concentration Risk" -- route to
    # customer_concentration, NOT employee_count (was false trigger)
    "BIZ.DEPEND.key_person": "customer_concentration",
    "BIZ.DEPEND.regulatory_dep": "regulatory_dependency_count",
    "BIZ.DEPEND.capital_dep": "capital_dependency_count",
    "BIZ.DEPEND.macro_sensitivity": "macro_sensitivity_count",
    "BIZ.DEPEND.distribution": "distribution_channels_count",
    "BIZ.DEPEND.contract_terms": "contract_terms_count",
    # Phase 33-02: labor check threshold expects labor risk flag count,
    # NOT employee_count (was false trigger: 150,000 employees > 2 flags)
    "BIZ.DEPEND.labor": "labor_risk_flag_count",
    # BIZ.MODEL
    "BIZ.MODEL.description": "business_description",
    "BIZ.MODEL.revenue_type": "revenue_type_analysis",
    "BIZ.MODEL.revenue_segment": "xbrl_revenue_segments",
    "BIZ.MODEL.revenue_geo": "xbrl_revenue_geo",
    "BIZ.MODEL.cost_structure": "cost_structure_analysis",
    "BIZ.MODEL.leverage_ops": "operating_leverage",
    "BIZ.MODEL.regulatory_dep": "model_regulatory_dependency",
    "BIZ.MODEL.capital_intensity": "capital_intensity_ratio",
    # BIZ.SIZE — Phase 70: XBRL-sourced field_keys
    "BIZ.SIZE.market_cap": "xbrl_market_cap",
    "BIZ.SIZE.revenue_ttm": "section_summary",
    "BIZ.SIZE.employees": "employee_count",
    "BIZ.SIZE.growth_trajectory": "years_public",
    "BIZ.SIZE.public_tenure": "years_public",
    # BIZ.UNI
    "BIZ.UNI.ai_claims": "ai_risk_exposure",
    "BIZ.UNI.cyber_posture": "cybersecurity_posture",
    "BIZ.UNI.cyber_business": "cyber_business_risk",
    # BIZ.EVENT (Phase 95: corporate event extraction)
    "BIZ.EVENT.ma_history": "event_ma_risk_score",
    "BIZ.EVENT.ipo_exposure": "event_ipo_exposure_score",
    "BIZ.EVENT.restatements": "event_restatement_severity",
    "BIZ.EVENT.capital_changes": "event_capital_change_count",
    "BIZ.EVENT.business_changes": "event_business_change_count",
    # BIZ.STRUCT (Phase 33-03: corporate structure complexity)
    "BIZ.STRUCT.subsidiary_count": "subsidiary_count",
    "BIZ.STRUCT.vie_spe": "vie_spe_present",
    "BIZ.STRUCT.related_party": "related_party_txns",
    # BIZ.OPS (Phase 99: operational complexity signals)
    "BIZ.OPS.subsidiary_structure": "jurisdiction_count",
    "BIZ.OPS.workforce": "international_pct",
    "BIZ.OPS.resilience": "geographic_concentration_score",
    "BIZ.OPS.complexity_score": "ops_complexity_score",
    # BIZ.STRUC (Phase 96: structural complexity signals)
    "BIZ.STRUC.disclosure_complexity": "disclosure_complexity_score",
    "BIZ.STRUC.nongaap": "nongaap_measure_count",
    "BIZ.STRUC.related_parties": "related_party_density",
    "BIZ.STRUC.obs_exposure": "obs_exposure_score",
    "BIZ.STRUC.holding_structure": "holding_structure_depth",
    # ── Section 2: Stock/Market (STOCK.*) → market mapper ──
    # STOCK.PRICE
    "STOCK.PRICE.recent_drop_alert": "decline_from_high",
    "STOCK.PRICE.chart_comparison": "decline_from_high",
    "STOCK.PRICE.position": "decline_from_high",
    "STOCK.PRICE.returns_multi_horizon": "returns_1y",
    "STOCK.PRICE.attribution": "decline_from_high",
    "STOCK.PRICE.peer_relative": "returns_1y",
    "STOCK.PRICE.single_day_events": "single_day_drops_count",
    "STOCK.PRICE.recovery": "returns_1y",
    "STOCK.PRICE.technical": "volatility_90d",
    "STOCK.PRICE.delisting_risk": "current_price",
    # STOCK.ANALYST
    "STOCK.ANALYST.coverage": "analyst_count",
    "STOCK.ANALYST.momentum": "recommendation_mean",
    # STOCK.INSIDER
    "STOCK.INSIDER.summary": "insider_net_activity",
    "STOCK.INSIDER.notable_activity": "ceo_cfo_selling_pct",
    "STOCK.INSIDER.cluster_timing": "cluster_selling",
    # STOCK.OWN (routed to governance mapper)
    "STOCK.OWN.structure": "institutional_pct",
    "STOCK.OWN.concentration": "institutional_pct",
    "STOCK.OWN.activist": "activist_present",
    # STOCK.PATTERN
    "STOCK.PATTERN.event_collapse": "single_day_drops_count",
    "STOCK.PATTERN.informed_trading": "insider_net_activity",
    "STOCK.PATTERN.cascade": "decline_from_high",
    "STOCK.PATTERN.peer_divergence": "returns_1y",
    "STOCK.PATTERN.death_spiral": "decline_from_high",
    "STOCK.PATTERN.short_attack": "short_interest_pct",
    # STOCK.SHORT
    "STOCK.SHORT.position": "short_interest_pct",
    "STOCK.SHORT.trend": "short_interest_ratio",
    "STOCK.SHORT.report": "short_interest_pct",
    # STOCK.LIT (routed to litigation mapper)
    "STOCK.LIT.existing_action": "active_sca_count",
    # STOCK.TRADE
    "STOCK.TRADE.liquidity": "avg_daily_volume",
    "STOCK.TRADE.volume_patterns": "volume_spike_count",
    "STOCK.TRADE.options": "adverse_event_count",
    # STOCK.VALUATION
    "STOCK.VALUATION.pe_ratio": "pe_ratio",
    "STOCK.VALUATION.ev_ebitda": "ev_ebitda",
    "STOCK.VALUATION.premium_discount": "returns_1y",
    "STOCK.VALUATION.peg_ratio": "peg_ratio",
    # ── Section 3: Financial (FIN.*) → financial mapper ──
    # FIN.LIQ — Phase 70: XBRL-sourced field_keys
    "FIN.LIQ.position": "xbrl_current_ratio",
    "FIN.LIQ.working_capital": "xbrl_working_capital",
    "FIN.LIQ.efficiency": "xbrl_cash_ratio",
    "FIN.LIQ.trend": "xbrl_current_ratio",
    "FIN.LIQ.cash_burn": "xbrl_cash_burn_months",
    # FIN.DEBT — Phase 70: XBRL-sourced field_keys
    "FIN.DEBT.structure": "xbrl_debt_to_ebitda",
    "FIN.DEBT.coverage": "xbrl_interest_coverage",
    "FIN.DEBT.maturity": "xbrl_debt_maturity",
    "FIN.DEBT.credit_rating": "xbrl_credit_rating",
    "FIN.DEBT.covenants": "xbrl_covenant_headroom",
    # FIN.PROFIT — Phase 70: XBRL-sourced field_keys
    "FIN.PROFIT.revenue": "xbrl_revenue_growth",
    "FIN.PROFIT.margins": "xbrl_operating_margin",
    "FIN.PROFIT.earnings": "xbrl_earnings_quality",
    "FIN.PROFIT.segment": "financial_health_narrative",
    "FIN.PROFIT.trend": "xbrl_margin_trend",
    # FIN.ACCT — Phase 70: dual XBRL+narrative field_keys
    "FIN.ACCT.auditor": "xbrl_auditor_opinion",
    "FIN.ACCT.internal_controls": "xbrl_material_weakness_count",
    "FIN.ACCT.restatement": "xbrl_restatement_count",
    "FIN.ACCT.restatement_magnitude": "xbrl_restatement_magnitude",
    "FIN.ACCT.restatement_pattern": "xbrl_restatement_pattern",
    "FIN.ACCT.restatement_auditor_link": "xbrl_restatement_auditor_link",
    "FIN.ACCT.material_weakness": "xbrl_material_weakness_flag",
    "FIN.ACCT.auditor_disagreement": "xbrl_auditor_disagreement",
    "FIN.ACCT.auditor_attestation_fail": "xbrl_auditor_attestation_fail",
    "FIN.ACCT.restatement_stock_window": "xbrl_restatement_stock_window",
    "FIN.ACCT.sec_correspondence": "xbrl_sec_correspondence_count",
    "FIN.ACCT.quality_indicators": "xbrl_altman_z_score",
    "FIN.ACCT.ohlson_o_score": "xbrl_ohlson_o_score",
    "FIN.ACCT.earnings_manipulation": "xbrl_beneish_m_score",
    "FIN.ACCT.restatement_history": "amendment_filing_10k_count",
    "FIN.ACCT.auditor_change": "eight_k_auditor_change",
    # FIN.TEMPORAL — Phase 70: XBRL-sourced field_keys
    "FIN.TEMPORAL.revenue_deceleration": "xbrl_revenue_deceleration",
    "FIN.TEMPORAL.margin_compression": "xbrl_margin_compression",
    "FIN.TEMPORAL.operating_margin_compression": "xbrl_op_margin_compression",
    "FIN.TEMPORAL.dso_expansion": "xbrl_dso_expansion",
    "FIN.TEMPORAL.cfo_ni_divergence": "xbrl_cfo_ni_divergence",
    "FIN.TEMPORAL.working_capital_deterioration": "xbrl_working_capital_deterioration",
    "FIN.TEMPORAL.debt_ratio_increase": "xbrl_debt_ratio_increase",
    "FIN.TEMPORAL.cash_flow_deterioration": "xbrl_cfo_deterioration",
    "FIN.TEMPORAL.profitability_trend": "xbrl_profitability_trend",
    "FIN.TEMPORAL.earnings_quality_divergence": "xbrl_earnings_quality_divergence",
    # FIN.QUALITY — Phase 70: XBRL-sourced field_keys
    "FIN.QUALITY.revenue_quality_score": "xbrl_revenue_quality",
    "FIN.QUALITY.cash_flow_quality": "xbrl_cash_flow_quality",
    "FIN.QUALITY.dso_ar_divergence": "xbrl_dso_ar_divergence",
    "FIN.QUALITY.q4_revenue_concentration": "xbrl_q4_concentration",
    "FIN.QUALITY.quality_of_earnings": "xbrl_earnings_quality",
    "FIN.QUALITY.deferred_revenue_trend": "xbrl_deferred_revenue_trend",
    # FIN.GUIDE
    "FIN.GUIDE.current": "guidance_provided",
    "FIN.GUIDE.track_record": "beat_rate",
    "FIN.GUIDE.philosophy": "guidance_philosophy",
    "FIN.GUIDE.earnings_reaction": "post_earnings_drift",
    "FIN.GUIDE.analyst_consensus": "consensus_divergence",
    # FIN.SECTOR
    "FIN.SECTOR.energy": "financial_health_narrative",
    "FIN.SECTOR.retail": "financial_health_narrative",
    # ── Section 4: Litigation (LIT.*) → litigation mapper ──
    # LIT.SCA
    "LIT.SCA.search": "total_sca_count",
    "LIT.SCA.active": "active_sca_count",
    "LIT.SCA.filing_date": "sca_filing_date",
    "LIT.SCA.class_period": "active_sca_count",
    "LIT.SCA.allegations": "active_sca_count",
    "LIT.SCA.lead_plaintiff": "sca_lead_counsel_tier",
    "LIT.SCA.case_status": "active_sca_count",
    "LIT.SCA.exposure": "contingent_liabilities_total",
    "LIT.SCA.policy_status": "active_sca_count",
    "LIT.SCA.prior_settle": "settled_sca_count",
    "LIT.SCA.settle_amount": "contingent_liabilities_total",
    "LIT.SCA.settle_date": "settled_sca_count",
    "LIT.SCA.prior_dismiss": "total_sca_count",
    "LIT.SCA.dismiss_basis": "total_sca_count",
    "LIT.SCA.historical": "total_sca_count",
    "LIT.SCA.derivative": "derivative_suit_count",
    "LIT.SCA.demand": "derivative_suit_count",
    "LIT.SCA.merger_obj": "deal_litigation_count",
    "LIT.SCA.erisa": "regulatory_count",
    "LIT.SCA.prefiling": "active_sca_count",
    # LIT.REG
    "LIT.REG.sec_investigation": "sec_enforcement_stage",
    "LIT.REG.sec_active": "sec_enforcement_stage",
    "LIT.REG.sec_severity": "sec_enforcement_stage",
    "LIT.REG.doj_investigation": "regulatory_count",
    "LIT.REG.industry_reg": "regulatory_count",
    "LIT.REG.ftc_investigation": "regulatory_count",
    "LIT.REG.state_ag": "state_ag_count",
    "LIT.REG.subpoena": "subpoena_count",
    "LIT.REG.comment_letters": "comment_letter_count",
    "LIT.REG.deferred_pros": "deferred_prosecution_count",
    "LIT.REG.wells_notice": "wells_notice",
    "LIT.REG.consent_order": "consent_order_count",
    "LIT.REG.cease_desist": "cease_desist_count",
    "LIT.REG.civil_penalty": "civil_penalty_count",
    "LIT.REG.dol_audit": "dol_audit_count",
    "LIT.REG.epa_action": "epa_action_count",
    "LIT.REG.osha_citation": "osha_citation_count",
    "LIT.REG.cfpb_action": "cfpb_action_count",
    "LIT.REG.fdic_order": "fdic_order_count",
    "LIT.REG.fda_warning": "fda_warning_count",
    "LIT.REG.foreign_gov": "foreign_gov_count",
    "LIT.REG.state_action": "state_action_count",
    # LIT.OTHER
    "LIT.OTHER.product": "product_liability_count",
    "LIT.OTHER.employment": "employment_lit_count",
    "LIT.OTHER.ip": "ip_litigation_count",
    "LIT.OTHER.environmental": "environmental_lit_count",
    "LIT.OTHER.contract": "contract_dispute_count",
    "LIT.OTHER.aggregate": "active_matter_count",
    "LIT.OTHER.class_action": "non_sca_class_action_count",
    "LIT.OTHER.antitrust": "antitrust_count",
    "LIT.OTHER.trade_secret": "trade_secret_count",
    "LIT.OTHER.whistleblower": "whistleblower_count",
    "LIT.OTHER.cyber_breach": "cyber_breach_count",
    "LIT.OTHER.bankruptcy": "bankruptcy_count",
    "LIT.OTHER.foreign_suit": "foreign_suit_count",
    "LIT.OTHER.gov_contract": "gov_contract_count",
    # LIT.DEFENSE (Phase 33-03: defense posture & reserves)
    "LIT.DEFENSE.forum_selection": "forum_selection_clause",
    "LIT.DEFENSE.contingent_liabilities": "contingent_liabilities_total",
    "LIT.DEFENSE.pslra_safe_harbor": "pslra_safe_harbor",
    # LIT.PATTERN (Phase 33-03: litigation risk patterns)
    "LIT.PATTERN.sol_windows": "sol_open_count",
    "LIT.PATTERN.industry_theories": "industry_pattern_count",
    "LIT.PATTERN.peer_contagion": "peer_contagion_risk",
    "LIT.PATTERN.temporal_correlation": "single_day_drops_count",
    # LIT.SECTOR (Phase 33-03: sector-specific litigation)
    "LIT.SECTOR.industry_patterns": "industry_pattern_count",
    "LIT.SECTOR.regulatory_databases": "sector_regulatory_count",
    # ── Section 5: Governance (GOV.*) → governance mapper ──
    # GOV.EXEC
    "GOV.EXEC.ceo_profile": "xbrl_ceo_tenure_years",
    "GOV.EXEC.cfo_profile": "xbrl_cfo_tenure_years",
    "GOV.EXEC.other_officers": "leadership_stability_score",
    "GOV.EXEC.officer_litigation": "leadership_stability_score",
    "GOV.EXEC.stability": "leadership_stability_score",
    "GOV.EXEC.turnover_analysis": "departures_18mo",
    "GOV.EXEC.departure_context": "departures_18mo",
    "GOV.EXEC.succession_status": "interim_ceo",
    "GOV.EXEC.founder": "ceo_tenure_years",
    "GOV.EXEC.key_person": "ceo_tenure_years",
    "GOV.EXEC.turnover_pattern": "departures_18mo",
    # GOV.BOARD
    "GOV.BOARD.size": "board_size",
    "GOV.BOARD.independence": "xbrl_board_independence",
    "GOV.BOARD.ceo_chair": "ceo_chair_duality",
    "GOV.BOARD.diversity": "board_diversity",
    "GOV.BOARD.tenure": "avg_board_tenure",
    "GOV.BOARD.overboarding": "overboarded_directors",
    "GOV.BOARD.departures": "departures_18mo",
    "GOV.BOARD.attendance": "board_attendance",
    "GOV.BOARD.expertise": "board_expertise",
    "GOV.BOARD.refresh_activity": "board_refresh",
    "GOV.BOARD.meetings": "board_meeting_count",
    "GOV.BOARD.committees": "board_committees",
    "GOV.BOARD.succession": "ceo_succession_plan",
    # GOV.PAY
    "GOV.PAY.ceo_total": "ceo_pay_ratio",
    "GOV.PAY.ceo_structure": "ceo_pay_ratio",
    "GOV.PAY.peer_comparison": "ceo_pay_ratio",
    "GOV.PAY.say_on_pay": "say_on_pay_pct",
    "GOV.PAY.clawback": "clawback_policy",
    "GOV.PAY.related_party": "related_party_txns",
    "GOV.PAY.golden_para": "golden_parachute_value",
    "GOV.PAY.incentive_metrics": "incentive_metrics_detail",
    "GOV.PAY.equity_burn": "equity_burn_rate",
    "GOV.PAY.hedging": "hedging_policy",
    "GOV.PAY.perks": "executive_perks",
    "GOV.PAY.401k_match": "retirement_benefits",
    "GOV.PAY.deferred_comp": "deferred_comp_detail",
    "GOV.PAY.pension": "pension_detail",
    "GOV.PAY.exec_loans": "executive_loans",
    # GOV.RIGHTS
    "GOV.RIGHTS.dual_class": "dual_class",
    "GOV.RIGHTS.voting_rights": "dual_class",
    "GOV.RIGHTS.bylaws": "bylaw_provisions",
    "GOV.RIGHTS.takeover": "takeover_defenses",
    "GOV.RIGHTS.proxy_access": "proxy_access_threshold",
    "GOV.RIGHTS.forum_select": "forum_selection_clause",
    "GOV.RIGHTS.supermajority": "supermajority_required",
    "GOV.RIGHTS.action_consent": "action_by_consent",
    "GOV.RIGHTS.special_mtg": "special_meeting_threshold",
    "GOV.RIGHTS.classified": "classified_board",
    # GOV.ACTIVIST — use specific counts where model supports it
    "GOV.ACTIVIST.13d_filings": "filing_13d_count",
    "GOV.ACTIVIST.campaigns": "activist_count",
    "GOV.ACTIVIST.proxy_contests": "proxy_contest_count",
    "GOV.ACTIVIST.settle_agree": "activist_count",
    "GOV.ACTIVIST.short_activism": "activist_count",
    "GOV.ACTIVIST.demands": "activist_count",
    "GOV.ACTIVIST.schedule_13g": "institutional_pct",
    "GOV.ACTIVIST.wolf_pack": "activist_count",
    "GOV.ACTIVIST.board_seat": "activist_count",
    "GOV.ACTIVIST.dissident": "activist_count",
    "GOV.ACTIVIST.withhold": "activist_count",
    "GOV.ACTIVIST.proposal": "activist_count",
    "GOV.ACTIVIST.consent": "activist_count",
    "GOV.ACTIVIST.standstill": "activist_count",
    # GOV.BOARD/EXEC character and qualifications
    "GOV.BOARD.prior_litigation": "board_prior_litigation_count",
    "GOV.BOARD.character_conduct": "board_character_issues",
    "GOV.BOARD.qualifications": "board_qualifications_pct",
    "GOV.EXEC.character_conduct": "exec_character_issues",
    # GOV.EFFECT
    "GOV.EFFECT.audit_committee": "xbrl_audit_committee_quality",
    "GOV.EFFECT.audit_opinion": "audit_opinion_type",
    "GOV.EFFECT.auditor_change": "auditor_change_flag",
    "GOV.EFFECT.material_weakness": "material_weakness_flag",
    "GOV.EFFECT.iss_score": "iss_governance_score",
    "GOV.EFFECT.proxy_advisory": "proxy_advisory_concern",
    "GOV.EFFECT.sox_404": "xbrl_sox_404_assessment",
    "GOV.EFFECT.sig_deficiency": "significant_deficiency_flag",
    "GOV.EFFECT.late_filing": "late_filing_flag",
    "GOV.EFFECT.nt_filing": "nt_filing_flag",
    # GOV.INSIDER
    "GOV.INSIDER.form4_filings": "insider_pct",
    "GOV.INSIDER.net_selling": "insider_pct",
    "GOV.INSIDER.10b5_plans": "trading_plans_10b51",
    "GOV.INSIDER.plan_adoption": "plan_adoption_timing",
    "GOV.INSIDER.cluster_sales": "insider_cluster_count",
    "GOV.INSIDER.unusual_timing": "timing_suspect_count",
    "GOV.INSIDER.executive_sales": "insider_pct",
    "GOV.INSIDER.ownership_pct": "insider_pct",
    "GOV.INSIDER.ownership_concentration": "ownership_concentration_severity",
    "GOV.INSIDER.exercise_sell": "exercise_sell_count",
    "GOV.INSIDER.timing_suspect": "timing_suspect_severity",
    # ── Phase 70: XBRL Forensic field_keys (from xbrl_forensics) ──
    # Balance sheet forensics
    "FIN.FORENSIC.goodwill_impairment_risk": "forensic_goodwill_to_assets",
    "FIN.FORENSIC.intangible_concentration": "forensic_intangible_concentration",
    "FIN.FORENSIC.off_balance_sheet": "forensic_off_balance_sheet",
    "FIN.FORENSIC.cash_conversion_cycle": "forensic_cash_conversion_cycle",
    "FIN.FORENSIC.working_capital_volatility": "forensic_working_capital_volatility",
    # Revenue forensics
    "FIN.FORENSIC.deferred_revenue_divergence": "forensic_deferred_revenue_divergence",
    "FIN.FORENSIC.channel_stuffing": "forensic_channel_stuffing",
    "FIN.FORENSIC.margin_compression": "forensic_margin_compression",
    "FIN.FORENSIC.ocf_revenue_ratio": "forensic_ocf_revenue_ratio",
    # Capital allocation forensics
    "FIN.FORENSIC.roic_decline": "forensic_roic_trend",
    "FIN.FORENSIC.acquisition_effectiveness": "forensic_acquisition_effectiveness",
    "FIN.FORENSIC.buyback_timing": "forensic_buyback_timing",
    "FIN.FORENSIC.dividend_sustainability": "forensic_dividend_sustainability",
    # Debt/tax forensics
    "FIN.FORENSIC.interest_coverage_decline": "forensic_interest_coverage_trend",
    "FIN.FORENSIC.debt_maturity_concentration": "forensic_debt_maturity_concentration",
    "FIN.FORENSIC.etr_anomaly": "forensic_etr_anomaly",
    "FIN.FORENSIC.deferred_tax_growth": "forensic_deferred_tax_growth",
    "FIN.FORENSIC.pension_underfunding": "forensic_pension_underfunding",
    # Beneish component forensics
    "FIN.FORENSIC.dsri_elevated": "forensic_beneish_dsri",
    "FIN.FORENSIC.aqi_elevated": "forensic_beneish_aqi",
    "FIN.FORENSIC.tata_elevated": "forensic_beneish_tata",
    "FIN.FORENSIC.m_score_composite": "forensic_beneish_composite",
    # Earnings quality forensics
    "FIN.FORENSIC.sloan_accruals": "forensic_sloan_accruals",
    "FIN.FORENSIC.cash_flow_manipulation": "forensic_cash_flow_manipulation",
    "FIN.FORENSIC.sbc_dilution": "forensic_sbc_dilution",
    "FIN.FORENSIC.non_gaap_gap": "forensic_non_gaap_gap",
    # M&A forensics
    "FIN.FORENSIC.serial_acquirer": "forensic_serial_acquirer",
    "FIN.FORENSIC.goodwill_growth_rate": "forensic_goodwill_growth_rate",
    "FIN.FORENSIC.acquisition_to_revenue": "forensic_acquisition_to_revenue",
}


__all__ = ["FIELD_FOR_CHECK", "narrow_result"]
