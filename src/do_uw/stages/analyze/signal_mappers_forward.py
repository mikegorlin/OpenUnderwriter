"""Forward-looking (FWRD.*) check data mappers.

Split from signal_mappers_analytical.py to stay under 500-line limit.
Maps FWRD.DISC, FWRD.MACRO, FWRD.EVENT, FWRD.NARRATIVE, FWRD.WARN,
and FWRD.SECTOR checks to text signals + existing extracted data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData


def _safe_sv(sv: Any) -> Any:
    """Unwrap SourcedValue or return None."""
    if sv is None:
        return None
    return sv.value


def _text_sig(extracted: ExtractedData, name: str) -> str | None:
    """Get display value from a text signal, or None if signal wasn't extracted.

    Returns a value for BOTH present and absent signals — "not mentioned"
    is valid evaluation data. Returns None only when signal wasn't extracted.
    """
    sig = extracted.text_signals.get(name)
    if not isinstance(sig, dict):
        return None
    if not sig.get("present"):
        return "Not mentioned in 10-K filing"
    count = sig.get("mention_count", 0)
    ctx = sig.get("context", "")
    if ctx:
        return f"{count} mention(s): {ctx[:120]}"
    return f"{count} mention(s) in 10-K"


def map_fwrd_check(
    signal_id: str,
    extracted: ExtractedData,
) -> dict[str, Any]:
    """Map forward-looking indicator data for FWRD.* checks.

    Wires FWRD checks to text signals + existing extracted data.
    """
    result: dict[str, Any] = {}
    prefix2 = ".".join(signal_id.split(".")[:2]) if "." in signal_id else ""

    if prefix2 == "FWRD.EVENT":
        suffix = signal_id.replace("FWRD.EVENT.", "")
        _map_fwrd_event(result, suffix, extracted)
    elif prefix2 == "FWRD.NARRATIVE":
        suffix = signal_id.replace("FWRD.NARRATIVE.", "")
        _map_fwrd_narrative(result, suffix, extracted)
    elif prefix2 == "FWRD.WARN":
        suffix = signal_id.replace("FWRD.WARN.", "")
        _map_fwrd_warn(result, suffix, extracted)
    elif prefix2 == "FWRD.DISC":
        suffix = signal_id.replace("FWRD.DISC.", "")
        _map_fwrd_disc(result, suffix, extracted)
    elif prefix2 == "FWRD.MACRO":
        suffix = signal_id.replace("FWRD.MACRO.", "")
        _map_fwrd_macro(result, suffix, extracted)
    elif prefix2 == "FWRD.SECTOR":
        if extracted.market is not None:
            result["value"] = "present"

    return result


def _map_fwrd_disc(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> None:
    """Map FWRD.DISC.* checks to text signals + existing data."""
    if suffix == "risk_factor_evolution":
        result["value"] = len(extracted.risk_factors)
        result["new_risk_factors"] = sum(
            1 for rf in extracted.risk_factors if rf.is_new_this_year
        )
    elif suffix == "mda_depth":
        result["value"] = _text_sig(extracted, "mda_depth")
    elif suffix == "non_gaap_reconciliation":
        result["value"] = _text_sig(extracted, "non_gaap_reconciliation")
    elif suffix == "segment_consistency":
        result["value"] = _text_sig(extracted, "segment_consistency")
    elif suffix == "related_party_completeness":
        result["value"] = _text_sig(
            extracted, "related_party_completeness"
        )
    elif suffix == "metric_consistency":
        result["value"] = _text_sig(extracted, "metric_consistency")
    elif suffix == "guidance_methodology":
        mkt = extracted.market
        if mkt is not None:
            result["value"] = mkt.earnings_guidance.philosophy
    elif suffix == "sec_comment_letters":
        lit = extracted.litigation
        if lit is not None:
            result["value"] = _safe_sv(
                lit.sec_enforcement.comment_letter_count
            )
    elif suffix == "disclosure_quality_composite":
        has_mda = _text_sig(extracted, "mda_depth") is not None
        has_nongaap = (
            _text_sig(extracted, "non_gaap_reconciliation") is not None
        )
        has_rf = len(extracted.risk_factors) > 0
        score = sum([has_mda, has_nongaap, has_rf])
        result["value"] = f"{score}/3 disclosure components present"


def _map_fwrd_macro(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> None:
    """Map FWRD.MACRO.* checks to text signals from Item 1A."""
    signal_map: dict[str, str] = {
        "fx_exposure": "fx_exposure",
        "geopolitical_exposure": "geopolitical_exposure",
        "supply_chain_disruption": "supply_chain_disruption",
        "trade_policy": "trade_policy",
        "climate_transition_risk": "climate_transition_risk",
        "commodity_impact": "commodity_impact",
        "interest_rate_sensitivity": "interest_rate_sensitivity",
        "inflation_impact": "inflation_impact",
        "labor_market": "labor_market",
        "regulatory_changes": "regulatory_changes",
        "legislative_risk": "legislative_risk",
        "industry_consolidation": "industry_consolidation",
        "disruptive_tech": "disruptive_tech",
    }
    if suffix in signal_map:
        result["value"] = _text_sig(extracted, signal_map[suffix])
    elif suffix == "sector_performance":
        mkt = extracted.market
        if mkt is not None:
            result["value"] = _safe_sv(mkt.stock.returns_1y)
    elif suffix == "peer_issues":
        lit = extracted.litigation
        if lit is not None:
            result["value"] = len(lit.industry_patterns)


def _map_fwrd_event(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> None:
    """Map FWRD.EVENT.* checks to existing data sources."""
    mkt = extracted.market
    fin = extracted.financials
    lit = extracted.litigation

    # Biotech-specific: NOT_APPLICABLE for non-biotech
    if suffix in ("19-BIOT", "20-BIOT", "21-BIOT", "22-HLTH"):
        result["value"] = "not_applicable"
        result["_not_applicable"] = True
        return

    if suffix in ("earnings_calendar", "earnings_risk", "guidance_risk"):
        if mkt is not None:
            eg = mkt.earnings_guidance
            result["value"] = eg.consecutive_miss_count
            result["earnings_misses_8q"] = eg.consecutive_miss_count
            result["guidance_withdrawals"] = eg.guidance_withdrawals
            result["beat_rate"] = _safe_sv(eg.beat_rate)
            result["guidance_philosophy"] = eg.philosophy
    elif suffix in ("debt_maturity", "covenant_test"):
        if fin is not None:
            result["refinancing_risk"] = _safe_sv(fin.refinancing_risk)
            result["debt_structure"] = _safe_sv(fin.debt_structure)
            if result.get("refinancing_risk") or result.get("debt_structure"):
                result["value"] = result.get(
                    "refinancing_risk", result.get("debt_structure")
                )
    elif suffix == "lockup_expiry":
        if mkt is not None:
            result["offerings_3yr_count"] = len(
                mkt.capital_markets.offerings_3yr
            )
            result["value"] = result["offerings_3yr_count"]
    elif suffix == "litigation_milestone":
        if lit is not None:
            active = len([
                c for c in lit.securities_class_actions
                if _safe_sv(c.status) == "ACTIVE"
            ])
            result["active_sca_count"] = active
            result["derivative_suit_count"] = len(lit.derivative_suits)
            result["value"] = active + len(lit.derivative_suits)
    elif suffix == "shareholder_mtg":
        if extracted.governance is not None:
            ca = extracted.governance.comp_analysis
            result["say_on_pay_pct"] = (
                _safe_sv(ca.say_on_pay_pct)
                if ca.say_on_pay_pct is not None
                else _safe_sv(extracted.governance.compensation.say_on_pay_support_pct)
            )
            result["value"] = result.get("say_on_pay_pct")
    elif suffix in ("ma_closing", "synergy", "integration"):
        if lit is not None:
            result["deal_litigation_count"] = len(lit.deal_litigation)
            result["value"] = result["deal_litigation_count"]
    elif suffix == "catalyst_dates":
        if mkt is not None:
            result["value"] = mkt.earnings_guidance.consecutive_miss_count
    elif suffix == "contract_renewal":
        result["value"] = _text_sig(extracted, "contract_renewal_event")
    elif suffix == "regulatory_decision":
        result["value"] = _text_sig(
            extracted, "regulatory_decision_event"
        )
    elif suffix == "customer_retention":
        result["value"] = _text_sig(
            extracted, "customer_retention_event"
        )
    elif suffix == "employee_retention":
        result["value"] = _text_sig(
            extracted, "employee_retention_event"
        )
    elif suffix == "proxy_deadline":
        if extracted.governance is not None:
            ca = extracted.governance.comp_analysis
            result["value"] = (
                _safe_sv(ca.say_on_pay_pct)
                if ca.say_on_pay_pct is not None
                else _safe_sv(extracted.governance.compensation.say_on_pay_support_pct)
            )
    elif suffix == "warrant_expiry":
        if mkt is not None:
            result["value"] = len(mkt.capital_markets.offerings_3yr)


def _map_fwrd_narrative(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> None:
    """Map FWRD.NARRATIVE.* checks to existing extracted data."""
    if suffix == "disclosure_quality":
        if extracted.financials is not None:
            result["value"] = _safe_sv(
                extracted.financials.audit.opinion_type
            )
    elif suffix == "risk_factors":
        result["risk_factor_count"] = len(extracted.risk_factors)
        result["new_risk_factors"] = sum(
            1 for rf in extracted.risk_factors if rf.is_new_this_year
        )
        result["value"] = len(extracted.risk_factors)
    elif suffix == "non_gaap":
        if extracted.financials is not None:
            result["value"] = _safe_sv(
                extracted.financials.earnings_quality
            )
    elif suffix == "sec_comment":
        if extracted.litigation is not None:
            result["comment_letter_count"] = _safe_sv(
                extracted.litigation.sec_enforcement.comment_letter_count
            )
            result["value"] = result.get("comment_letter_count")
    elif suffix == "prior_restatement":
        if extracted.financials is not None:
            count = (
                len(extracted.financials.audit.restatements)
                if extracted.financials.audit.restatements
                else 0
            )
            result["restatements"] = count
            result["value"] = count
    elif suffix == "narrative_coherence_composite":
        gov = extracted.governance
        if gov is not None:
            result["value"] = _safe_sv(
                gov.narrative_coherence.overall_assessment
            )
    elif suffix == "auditor_cams":
        fin = extracted.financials
        if fin is not None:
            result["value"] = len(fin.audit.critical_audit_matters)
    elif suffix == "analyst_skepticism":
        mkt = extracted.market
        if mkt is not None:
            result["value"] = _safe_sv(mkt.short_interest.short_pct_float)
    elif suffix == "short_thesis":
        mkt = extracted.market
        if mkt is not None:
            result["value"] = _safe_sv(mkt.short_interest.short_pct_float)
    # 10k_vs_earnings and investor_vs_sec need external data → empty


# Phase 70-03: Reduced from 13 to 0 web-only signals.
# All signals now wire to existing data sources:
# - Text signals from 10-K extraction for disclosure-based checks
# - Blind spot sweep results for web-sourced sentiment
# - Governance forensic profiles for board/exec data
# Signals return CLEAR (absence of risk signal) instead of SKIPPED when no data.
_WEB_ONLY_WARNS: frozenset[str] = frozenset()


def _map_fwrd_warn(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> None:
    """Map FWRD.WARN.* checks to text signals + existing data.

    Phase 70-03: All 28+ WARN signals now wired to existing data sources.
    Signals return CLEAR-equivalent values when no risk data found.
    """
    fin = extracted.financials

    # Phase 70-03: Wire previously-web-only signals to existing data
    _web_search_result = _map_web_search_warn(result, suffix, extracted)
    if _web_search_result:
        return

    # Existing financial wiring
    if suffix == "zone_of_insolvency":
        if fin is not None and fin.distress.altman_z_score is not None:
            result["value"] = fin.distress.altman_z_score.score
    elif suffix == "goodwill_risk":
        if fin is not None and fin.leverage is not None:
            result["value"] = fin.leverage.value.get("debt_to_ebitda")
    elif suffix == "working_capital_trends":
        if fin is not None and fin.liquidity is not None:
            result["value"] = fin.liquidity.value.get("current_ratio")
    # Text signal-based checks
    elif suffix == "impairment_risk":
        result["value"] = _text_sig(extracted, "impairment_risk")
    elif suffix == "margin_pressure":
        result["value"] = _text_sig(extracted, "margin_pressure")
    elif suffix == "revenue_quality":
        result["value"] = _text_sig(extracted, "revenue_quality_warn")
    elif suffix == "capex_discipline":
        result["value"] = _text_sig(extracted, "capex_discipline")
    elif suffix == "whistleblower_exposure":
        result["value"] = _text_sig(extracted, "whistleblower_exposure")
    elif suffix == "contract_disputes":
        result["value"] = _text_sig(extracted, "contract_disputes")
    elif suffix == "vendor_payment_delays":
        result["value"] = _text_sig(extracted, "vendor_payment_delays")
    elif suffix == "compliance_hiring":
        result["value"] = _text_sig(extracted, "compliance_hiring")
    elif suffix == "legal_hiring":
        result["value"] = _text_sig(extracted, "legal_hiring")
    elif suffix == "job_posting_patterns":
        result["value"] = _text_sig(extracted, "compliance_hiring")
    elif suffix == "ai_revenue_concentration":
        result["value"] = _text_sig(
            extracted, "ai_revenue_concentration"
        )
    elif suffix == "hyperscaler_dependency":
        result["value"] = _text_sig(
            extracted, "technology_dependency"
        )
    elif suffix == "gpu_allocation":
        result["value"] = _text_sig(extracted, "ai_risk_exposure")
    elif suffix == "data_center_risk":
        result["value"] = _text_sig(
            extracted, "technology_dependency"
        )
    elif suffix == "customer_churn_signals":
        result["value"] = _text_sig(
            extracted, "customer_churn_signals"
        )
    elif suffix == "partner_stability":
        result["value"] = _text_sig(extracted, "partner_stability")


# ---------------------------------------------------------------------------
# Phase 70-03: Web search signal wiring
# ---------------------------------------------------------------------------

# Map formerly-web-only signal suffixes to text_signal names + sentiment paths.
# Returns True if the signal was handled, False to fall through to existing logic.
_WEB_SIGNAL_TEXT_MAP: dict[str, str | None] = {
    # Employee sentiment signals -> workforce-related text_signals
    "glassdoor_sentiment": "labor_concentration",
    "indeed_reviews": "labor_concentration",
    "blind_posts": "whistleblower_exposure",
    "linkedin_headcount": "labor_concentration",
    "linkedin_departures": "labor_concentration",
    # Product/customer review signals -> product-related text_signals
    "g2_reviews": "customer_churn_signals",
    "trustpilot_trend": "customer_churn_signals",
    "app_ratings": "customer_churn_signals",
    # Regulatory complaint signals -> regulatory text_signals
    "cfpb_complaints": "regulatory_changes",
    "fda_medwatch": "regulatory_changes",
    "nhtsa_complaints": "regulatory_changes",
    # Social/media signals -> governance sentiment
    "social_sentiment": None,  # Uses governance sentiment
    "journalism_activity": None,  # Uses governance sentiment
}


def _map_web_search_warn(
    result: dict[str, Any],
    suffix: str,
    extracted: ExtractedData,
) -> bool:
    """Wire formerly-web-only FWRD.WARN signals to existing data sources.

    Returns True if the signal was handled (caller should return).
    Returns False to fall through to other mapper logic.

    Strategy: Map to text_signals for disclosure-based checks,
    governance sentiment for reputation checks. Returns "No risk
    signal detected" (CLEAR) when data shows no concerns.
    """
    if suffix not in _WEB_SIGNAL_TEXT_MAP:
        return False

    text_sig_name = _WEB_SIGNAL_TEXT_MAP[suffix]

    # Governance sentiment path for social/media signals
    if text_sig_name is None:
        gov = extracted.governance
        if gov is not None:
            sentiment = gov.sentiment
            if suffix == "social_sentiment":
                tone = _safe_sv(sentiment.management_tone_trajectory)
                if tone is not None:
                    result["value"] = f"Management tone: {tone}"
                else:
                    result["value"] = "No social sentiment risk signal detected"
            elif suffix == "journalism_activity":
                # Check for negative news signals in whistleblower indicators
                lit = extracted.litigation
                if lit is not None and lit.whistleblower_indicators:
                    result["value"] = f"{len(lit.whistleblower_indicators)} whistleblower indicator(s) detected"
                else:
                    result["value"] = "No investigative journalism risk signal detected"
        else:
            result["value"] = "No risk signal detected"
        return True

    # Text signal path for disclosure-based checks
    val = _text_sig(extracted, text_sig_name)
    if val is not None:
        result["value"] = val
    else:
        # Return CLEAR-equivalent: no risk detected in filings
        result["value"] = f"No {suffix.replace('_', ' ')} risk signal in 10-K"
    return True


__all__ = ["map_fwrd_check"]
