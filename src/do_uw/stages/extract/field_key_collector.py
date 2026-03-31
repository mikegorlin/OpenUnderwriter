"""Collect extracted field keys from pipeline state.

Maps check data_strategy field_key names to actual presence in the
state model. Used by ExtractionManifest for gap reporting.
"""

from __future__ import annotations

from do_uw.models.state import AnalysisState


def collect_extracted_field_keys(state: AnalysisState) -> set[str]:
    """Inspect state to determine which data fields have been extracted.

    Returns the set of field_key values that have non-None data,
    enabling extraction manifest gap reporting.
    """
    keys: set[str] = set()
    extracted = state.extracted

    # ---- Financial field keys ----
    if extracted and extracted.financials:
        fin = extracted.financials
        if fin.statements and fin.statements.income_statement:
            keys.update([
                "financial_health_narrative", "revenue_growth",
                "accruals_ratio", "ocf_to_ni",
            ])
        if fin.liquidity:
            keys.update(["current_ratio", "cash_ratio", "cash_burn_months"])
        if fin.leverage:
            keys.update([
                "debt_to_ebitda", "interest_coverage", "debt_structure",
            ])
        if fin.distress:
            keys.add("altman_z")
            if fin.distress.altman_z_score is not None:
                keys.add("altman_z_score")
            if fin.distress.beneish_m_score is not None:
                keys.add("beneish_m_score")
            if fin.distress.piotroski_f_score is not None:
                keys.add("piotroski_f_score")
        if fin.earnings_quality:
            keys.update([
                "accruals_ratio", "quality_of_earnings",
                "revenue_quality_score",
            ])
        if fin.quarterly_xbrl and len(fin.quarterly_xbrl.quarters) >= 4:
            keys.add("xbrl_q4_concentration")
        if fin.audit:
            keys.update([
                "auditor_opinion", "material_weaknesses", "restatements",
                "audit_opinion_type", "material_weakness_flag",
                "sox_404_assessment",
            ])
            if fin.audit.amendment_filing_10k_count > 0:
                keys.add("amendment_filing_10k_count")
            if fin.audit.amendment_filing_10q_count > 0:
                keys.add("amendment_filing_10q_count")
        if fin.debt_structure:
            keys.add("refinancing_risk")
        if fin.peer_group:
            keys.add("peer_group")

    # ---- Market field keys ----
    if extracted and extracted.market:
        mkt = extracted.market
        stk = mkt.stock
        if stk.decline_from_high_pct:
            keys.add("decline_from_high")
        if stk.returns_1y:
            keys.add("returns_1y")
        if stk.single_day_events:
            keys.update([
                "single_day_drops_count", "daily_returns", "close_prices",
            ])
        if stk.volatility_90d:
            keys.update([
                "historical_volatility", "daily_returns",
            ])
        si = mkt.short_interest
        if si.short_pct_float:
            keys.update([
                "short_interest", "shares_short", "short_ratio",
                "short_interest_history", "short_ratio_trend",
            ])
        it = mkt.insider_trading
        if it.net_buying_selling:
            keys.update([
                "insider_transactions", "form4_filings",
            ])
        # Insider analysis detail fields
        insider = mkt.insider_analysis
        if insider.cluster_events:
            keys.add("insider_cluster_count")
        if insider.pct_10b5_1 is not None:
            keys.add("trading_plans_10b51")
        if mkt.eight_k_items.has_auditor_change:
            keys.add("eight_k_auditor_change")

    # ---- Governance field keys ----
    if extracted and extracted.governance:
        gov = extracted.governance
        if gov.board.size:
            keys.update([
                "board_size", "board_composition", "number_of_directors",
            ])
        if gov.board.independence_ratio:
            keys.update([
                "independent_directors", "independence_ratio",
                "board_independence",
            ])
        if gov.board.ceo_chair_duality is not None:
            keys.add("ceo_chair_duality")
        if gov.board.classified_board is not None:
            keys.add("classified_board")
        if gov.board.avg_tenure_years:
            keys.add("avg_board_tenure")
        if gov.board.overboarded_count:
            keys.add("overboarded_directors")
        if gov.board.dual_class_structure is not None:
            keys.add("dual_class")
        if gov.compensation.ceo_pay_ratio:
            keys.update([
                "ceo_pay_ratio", "ceo_total_compensation",
            ])
        # CompensationAnalysis (comp_analysis) detail fields
        ca = gov.comp_analysis
        if ca.has_clawback is not None:
            keys.add("clawback_policy")
        if ca.say_on_pay_pct is not None:
            keys.add("say_on_pay_pct")
        if ca.performance_metrics:
            keys.add("incentive_metrics_detail")
        if ca.notable_perquisites:
            keys.add("executive_perks")
        if ca.related_party_transactions:
            keys.add("related_party_txns")
        if gov.compensation.golden_parachute_value is not None:
            keys.add("golden_parachute_value")
        # Governance quality score
        if gov.governance_score.total_score is not None:
            keys.update([
                "governance_score", "audit_committee_quality",
                "board_committees",
            ])
        # Leadership stability
        if gov.leadership.stability_score is not None:
            keys.add("leadership_stability_score")
        if gov.leadership.departures_18mo:
            keys.add("departures_18mo")
        # Ownership
        if gov.ownership.institutional_pct is not None:
            keys.add("institutional_pct")
        if gov.ownership.insider_pct is not None:
            keys.add("insider_pct")
        if gov.ownership.known_activists:
            keys.update(["activist_present", "activist_count"])
        if gov.ownership.filings_13d_24mo:
            keys.add("filing_13d_count")
        if gov.ownership.proxy_contests_3yr:
            keys.add("proxy_contest_count")
        if gov.ownership.conversions_13g_to_13d:
            keys.add("conversion_13g_to_13d_count")
        # Board/exec character and qualifications
        directors = gov.board_forensics or []
        if any(getattr(d, "prior_litigation", None) for d in directors):
            keys.add("board_prior_litigation_count")
        if any(getattr(d, "qualifications", None) for d in directors):
            keys.add("board_qualifications_pct")
        execs = gov.leadership.executives or []
        if any(getattr(ep, "shade_factors", None) for ep in execs):
            keys.update(["board_character_issues", "exec_character_issues"])
        if any(getattr(ep, "prior_litigation", None) for ep in execs):
            keys.add("exec_prior_litigation_count")

    # ---- Litigation field keys ----
    if extracted and extracted.litigation:
        lit = extracted.litigation
        if lit.securities_class_actions:
            keys.update([
                "total_sca_count", "active_sca_count",
                "securities_class_actions", "scac_matches",
                "scac_search_results", "sca_filing_date",
                "sca_lead_counsel_tier",
            ])
        sec = lit.sec_enforcement
        if sec.pipeline_position or sec.actions:
            keys.update([
                "sec_enforcement_actions", "aaer_matches",
                "litigation_releases", "sec_enforcement_stage",
            ])
        if sec.comment_letter_count is not None:
            keys.add("comment_letter_count")
        if lit.contingent_liabilities:
            keys.update([
                "contingent_liabilities", "contingent_liabilities_total",
                "litigation_reserves",
            ])
        if lit.derivative_suits:
            keys.update([
                "derivative_lawsuits", "shareholder_derivative",
                "derivative_suit_count",
            ])
        if lit.regulatory_proceedings:
            keys.update([
                "regulatory_count",
                # Per-agency counts are always available when proceedings exist
                "state_ag_count", "epa_action_count", "osha_citation_count",
                "cfpb_action_count", "fdic_order_count", "fda_warning_count",
                "dol_audit_count", "foreign_gov_count", "state_action_count",
                "subpoena_count", "deferred_prosecution_count",
                "consent_order_count", "cease_desist_count",
                "civil_penalty_count",
            ])
        if lit.deal_litigation:
            keys.add("deal_litigation_count")
        if lit.whistleblower_indicators:
            keys.add("whistleblower_count")
        if lit.industry_patterns:
            keys.add("industry_pattern_count")
        if lit.sol_map:
            keys.add("sol_open_count")
        # WPE per-type counts (always available even if empty)
        wpe = lit.workforce_product_environmental
        keys.update([
            "employment_lit_count", "product_liability_count",
            "environmental_lit_count", "cyber_breach_count",
            "antitrust_count",
        ])
        if wpe.employment_matters:
            keys.add("employment_lit_count")
        if wpe.product_recalls:
            keys.add("product_liability_count")
        if wpe.environmental_actions:
            keys.add("environmental_lit_count")
        if wpe.cybersecurity_incidents:
            keys.add("cyber_breach_count")

    # ---- Company / identity field keys ----
    if state.company:
        co = state.company
        if co.identity.sector:
            keys.update(["sector", "sic_code", "industry_classification"])
        if co.employee_count:
            keys.update([
                "employee_count", "full_time_employees",
            ])
        if co.market_cap:
            keys.update([
                "market_capitalization", "shares_outstanding", "close_price",
            ])
        if co.revenue_segments:
            keys.update(["revenue_segments", "segment_data"])
        if co.geographic_footprint:
            keys.update([
                "geographic_revenue", "revenue_by_region",
                "international_revenue",
            ])

    # ---- Text signal field keys ----
    if extracted and extracted.text_signals:
        for topic, signal in extracted.text_signals.items():
            if isinstance(signal, dict) and signal.get("present"):
                keys.add(topic)

    return keys
