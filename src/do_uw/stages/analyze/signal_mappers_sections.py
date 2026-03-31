"""Section 5-6 check data mappers (Governance + Litigation).

Split from signal_mappers.py to stay under 500-line limit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.signal_field_routing import narrow_result
from do_uw.stages.analyze.signal_mappers import (
    _is_regulatory_coverage,
    _safe_sourced,
)

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_filing_flag(extracted: ExtractedData, flag_type: str) -> bool:
    """Check for late filing or NT filing evidence in text signals and filings.

    Returns False (CLEAR) rather than None to avoid SKIPPED status.
    """
    # Check text_signals for explicit mentions
    sig = extracted.text_signals.get(flag_type)
    if isinstance(sig, dict) and sig.get("present"):
        return True
    # Check filing_analysis for late filing indicators
    sig2 = extracted.text_signals.get("compliance_hiring")
    if isinstance(sig2, dict) and sig2.get("present"):
        ctx = sig2.get("context", "")
        if flag_type == "late_filing" and "late fil" in ctx.lower():
            return True
        if flag_type == "nt_filing" and ("nt 10-k" in ctx.lower() or "nt 10-q" in ctx.lower()):
            return True
    return False


# ---------------------------------------------------------------------------
# Section 5: Governance data
# ---------------------------------------------------------------------------


def map_governance_fields(
    signal_id: str,
    extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map governance data for GOV.* and STOCK.OWN.* checks."""
    result: dict[str, Any] = {}
    gov = extracted.governance
    if gov is None:
        return result

    # Board composition
    raw_independence = _safe_sourced(gov.board.independence_ratio)
    if isinstance(raw_independence, (int, float)) and raw_independence <= 1.0:
        result["board_independence"] = raw_independence * 100
    else:
        result["board_independence"] = raw_independence
    # Phase 70: XBRL dual-source alias
    result["xbrl_board_independence"] = result["board_independence"]
    result["ceo_chair_duality"] = _safe_sourced(gov.board.ceo_chair_duality)
    result["board_size"] = _safe_sourced(gov.board.size)
    result["overboarded_directors"] = _safe_sourced(gov.board.overboarded_count)
    result["dual_class"] = _safe_sourced(gov.board.dual_class_structure)
    if result["dual_class"] is None and gov.ownership.has_dual_class is not None:
        result["dual_class"] = gov.ownership.has_dual_class.value
    result["classified_board"] = _safe_sourced(gov.board.classified_board)

    # Board tenure (from BoardProfile model)
    result["avg_board_tenure"] = _safe_sourced(gov.board.avg_tenure_years)

    # Executive stability
    _map_executive_fields(result, gov)

    # Compensation — prefer comp_analysis (populated by proxy extraction),
    # fall back to compensation model (populated by LLM extraction)
    ca = gov.comp_analysis
    result["say_on_pay_pct"] = (
        _safe_sourced(ca.say_on_pay_pct)
        if ca.say_on_pay_pct is not None
        else _safe_sourced(gov.compensation.say_on_pay_support_pct)
    )
    result["ceo_pay_ratio"] = (
        _safe_sourced(ca.ceo_pay_ratio)
        if ca.ceo_pay_ratio is not None
        else _safe_sourced(gov.compensation.ceo_pay_ratio)
    )
    result["ceo_total_comp"] = _safe_sourced(ca.ceo_total_comp)

    # Compensation detail fields (GOV.PAY.* checks)
    result["clawback_policy"] = _safe_sourced(ca.has_clawback)
    result["golden_parachute_value"] = _safe_sourced(
        gov.compensation.golden_parachute_value
    )
    result["incentive_metrics_detail"] = (
        len(ca.performance_metrics) if ca.performance_metrics else 0
    )
    # Phase 70-03: Wire to forensic SBC dilution if available
    # equity_grant_dilution is not on CompensationAnalysis — fall back to
    # forensic SBC ratio from xbrl_forensics when available.
    result["equity_burn_rate"] = None  # Populated by forensic re-eval if available
    # hedging_prohibition is on BoardProfile, not CompensationAnalysis
    _board = gov.board
    result["hedging_policy"] = (
        _safe_sourced(_board.hedging_prohibition)
        if _board is not None and hasattr(_board, "hedging_prohibition")
        else None
    )
    result["executive_perks"] = (
        len(ca.notable_perquisites) if ca.notable_perquisites else 0
    )
    # Phase 70-03: Wire to comp_analysis fields when available
    result["retirement_benefits"] = _safe_sourced(ca.retirement_plan_description) if hasattr(ca, "retirement_plan_description") else None
    result["deferred_comp_detail"] = _safe_sourced(ca.deferred_comp_plans) if hasattr(ca, "deferred_comp_plans") else None
    result["pension_detail"] = _safe_sourced(ca.pension_plan_description) if hasattr(ca, "pension_plan_description") else None
    result["executive_loans"] = _safe_sourced(ca.executive_loans_present) if hasattr(ca, "executive_loans_present") else None
    result["related_party_txns"] = (
        len(ca.related_party_transactions)
        if ca.related_party_transactions
        else 0
    )

    # Board detail fields (GOV.BOARD.* checks — mostly from DEF 14A)
    # Board attendance — populated from DEF 14A extraction
    result["board_attendance"] = (
        _safe_sourced(gov.board.board_attendance_pct) if gov.board else None
    )
    # Phase 70-03: Wire board expertise to forensic qualifications count
    bf = gov.board_forensics or []
    result["board_expertise"] = sum(1 for d in bf if getattr(d, "qualifications", None)) if bf else None
    result["board_refresh"] = getattr(
        gov.governance_score, "refreshment_score", None
    )
    # Board meeting count — populated from DEF 14A extraction
    result["board_meeting_count"] = (
        _safe_sourced(gov.board.board_meetings_held) if gov.board else None
    )
    result["board_committees"] = getattr(
        gov.governance_score, "committee_score", None
    )
    # Phase 70-03: Wire succession to governance score component or board data
    _board = gov.board
    result["ceo_succession_plan"] = _safe_sourced(_board.ceo_succession_plan) if _board is not None and hasattr(_board, "ceo_succession_plan") else None

    # Board diversity — populated from DEF 14A extraction
    result["board_diversity"] = (
        _safe_sourced(gov.board.board_gender_diversity_pct) if gov.board else None
    )
    result["board_racial_diversity"] = (
        _safe_sourced(gov.board.board_racial_diversity_pct) if gov.board else None
    )
    result["directors_below_75_pct_attendance"] = (
        _safe_sourced(gov.board.directors_below_75_pct_attendance)
        if gov.board
        else None
    )

    # Shareholder rights fields (GOV.RIGHTS.* checks)
    # Anti-takeover provisions from DEF14A (via BoardProfile)
    bp = gov.board
    result["takeover_defenses"] = None
    if bp is not None:
        # Count anti-takeover provisions: poison pill, blank check preferred
        takeover_count = 0
        if _safe_sourced(bp.poison_pill) is True:
            takeover_count += 1
        if _safe_sourced(bp.blank_check_preferred) is True:
            takeover_count += 1
        if takeover_count > 0:
            result["takeover_defenses"] = takeover_count
    result["supermajority_required"] = (
        _safe_sourced(bp.supermajority_voting) if bp is not None else None
    )
    # Phase 70-03: Wire to DEF14A BoardProfile fields when available
    result["bylaw_provisions"] = (
        _safe_sourced(bp.bylaw_amendment_provisions) if bp is not None and hasattr(bp, "bylaw_amendment_provisions") else None
    )
    result["proxy_access_threshold"] = (
        _safe_sourced(bp.proxy_access_threshold) if bp is not None and hasattr(bp, "proxy_access_threshold") else None
    )
    result["action_by_consent"] = (
        _safe_sourced(bp.written_consent_allowed) if bp is not None and hasattr(bp, "written_consent_allowed") else None
    )
    result["special_meeting_threshold"] = (
        _safe_sourced(bp.special_meeting_threshold) if bp is not None and hasattr(bp, "special_meeting_threshold") else None
    )
    result["forum_selection_clause"] = (
        _safe_sourced(bp.exclusive_forum_provision) if bp is not None else None
    )
    result["shareholder_proposal_count"] = (
        _safe_sourced(bp.shareholder_proposal_count)
        if bp is not None
        else None
    )
    # Forum selection — prefer DEF14A extraction, fall back to litigation
    result["forum_selection_clause"] = (
        _safe_sourced(bp.forum_selection_clause) if bp is not None else None
    )
    if result["forum_selection_clause"] is None:
        lit = extracted.litigation
        if lit is not None and hasattr(lit.defense, "forum_selection_clause"):
            result["forum_selection_clause"] = _safe_sourced(
                lit.defense.forum_selection_clause
            )

    # Ownership/activist risk — granular counts instead of single boolean
    result["activist_present"] = len(gov.ownership.known_activists) > 0
    result["activist_count"] = len(gov.ownership.known_activists)
    result["filing_13d_count"] = len(gov.ownership.filings_13d_24mo)
    result["proxy_contest_count"] = len(gov.ownership.proxy_contests_3yr)
    result["conversion_13g_to_13d_count"] = len(
        gov.ownership.conversions_13g_to_13d
    )
    result["institutional_pct"] = _safe_sourced(gov.ownership.institutional_pct)
    result["insider_pct"] = _safe_sourced(gov.ownership.insider_pct)

    # Board/exec character, qualifications, prior litigation (GOV.BOARD.*/GOV.EXEC.*)
    _map_character_fields(result, gov)

    # Governance quality score
    result["governance_score"] = _safe_sourced(gov.governance_score.total_score)

    # GOV.EFFECT fields — governance effectiveness indicators
    acq = getattr(gov.governance_score, "committee_score", None)
    result["audit_committee_quality"] = acq
    result["xbrl_audit_committee_quality"] = acq  # Phase 70: dual-source alias
    fin = extracted.financials
    if fin is not None:
        result["audit_opinion_type"] = _safe_sourced(fin.audit.opinion_type)
        result["material_weakness_flag"] = (
            len(fin.audit.material_weaknesses) > 0
            if fin.audit.material_weaknesses
            else False
        )
        # Phase 70-03: sig_deficiency -> infer from material weakness count
        result["significant_deficiency_flag"] = (
            len(fin.audit.material_weaknesses) > 0
            if fin.audit.material_weaknesses
            else False
        )
        sox = _safe_sourced(fin.audit.opinion_type)
        result["sox_404_assessment"] = sox
        result["xbrl_sox_404_assessment"] = sox  # Phase 70: dual-source alias
        # Phase 70-03: auditor_change -> infer from audit tenure
        auditor_tenure = _safe_sourced(fin.audit.tenure_years)
        result["auditor_change_flag"] = (
            auditor_tenure is not None and auditor_tenure <= 1
        )
    else:
        result["audit_opinion_type"] = None
        result["material_weakness_flag"] = None
        result["significant_deficiency_flag"] = None
        result["sox_404_assessment"] = None
        result["xbrl_sox_404_assessment"] = None  # Phase 70: dual-source alias
        result["auditor_change_flag"] = None
    # ISS governance risk scores (populated from yfinance)
    result["iss_governance_score"] = _safe_sourced(gov.board.iss_overall_risk)
    result["iss_audit_risk"] = _safe_sourced(gov.board.iss_audit_risk)
    result["iss_board_risk"] = _safe_sourced(gov.board.iss_board_risk)
    result["iss_compensation_risk"] = _safe_sourced(gov.board.iss_compensation_risk)
    result["iss_shareholder_rights_risk"] = _safe_sourced(gov.board.iss_shareholder_rights_risk)
    result["proxy_advisory_concern"] = None  # External service
    # Phase 70-03: Wire late/NT filing to text_signals and filing analysis
    result["late_filing_flag"] = _extract_filing_flag(extracted, "late_filing")
    result["nt_filing_flag"] = _extract_filing_flag(extracted, "nt_filing")

    # GOV.INSIDER fields — insider trading patterns
    mkt = extracted.market
    if mkt is not None:
        insider = mkt.insider_analysis
        result["insider_cluster_count"] = len(insider.cluster_events)
        result["trading_plans_10b51"] = _safe_sourced(insider.pct_10b5_1)
        # Phase 70-03: Reactivate plan_adoption + unusual_timing
        # plan_adoption_timing: if 10b5-1 % is low, adoption patterns may be suspicious
        pct_planned = _safe_sourced(insider.pct_10b5_1)
        result["plan_adoption_timing"] = (
            round(100 - pct_planned, 1) if pct_planned is not None else None
        )
        # unusual_timing: count of filing timing suspects
        result["timing_suspect_count"] = len(insider.timing_suspects)
        # Phase 71-02: Exercise-sell and timing suspect fields
        result["exercise_sell_count"] = len(insider.exercise_sell_events)
        # Max severity: RED_FLAG > AMBER > None
        if insider.timing_suspects:
            severities = [s.severity for s in insider.timing_suspects]
            result["timing_suspect_severity"] = (
                "RED_FLAG" if "RED_FLAG" in severities else "AMBER"
            )
        else:
            result["timing_suspect_severity"] = None
        # Ownership concentration severity (from Plan 01)
        if insider.ownership_alerts:
            alert_severities = [a.severity for a in insider.ownership_alerts]
            _SEV_ORDER = {"RED_FLAG": 3, "WARNING": 2, "INFORMATIONAL": 1, "POSITIVE": 0}
            result["ownership_concentration_severity"] = max(
                alert_severities, key=lambda s: _SEV_ORDER.get(s, 0)
            )
        else:
            result["ownership_concentration_severity"] = None
    else:
        result["insider_cluster_count"] = None
        result["trading_plans_10b51"] = None
        result["plan_adoption_timing"] = None
        result["timing_suspect_count"] = 0
        result["exercise_sell_count"] = 0
        result["timing_suspect_severity"] = None
        result["ownership_concentration_severity"] = None

    # Leadership stability
    result["leadership_stability_score"] = _safe_sourced(
        gov.leadership.stability_score
    )
    result["departures_18mo"] = len(gov.leadership.departures_18mo)

    # Sentiment
    result["management_tone"] = _safe_sourced(
        gov.sentiment.management_tone_trajectory
    )
    result["narrative_coherence"] = _safe_sourced(
        gov.narrative_coherence.overall_assessment
    )

    return narrow_result(signal_id, result, check_config)


def _map_executive_fields(result: dict[str, Any], gov: Any) -> None:
    """Extract CEO/CFO tenure and interim status from governance data."""
    ceo_tenure: float | str | None = None
    cfo_tenure: float | str | None = None
    interim_ceo = False
    interim_cfo = False

    for exec_profile in gov.leadership.executives:
        title = _safe_sourced(exec_profile.title)
        if title is None:
            continue
        title_upper = title.upper()
        if "CEO" in title_upper or "CHIEF EXECUTIVE" in title_upper:
            ceo_tenure = exec_profile.tenure_years
            # If exec identified but tenure unknown, provide name as evidence
            if ceo_tenure is None:
                name = _safe_sourced(exec_profile.name) or "identified"
                ceo_tenure = f"Identified: {name} (tenure unavailable)"
            interim_ceo = bool(_safe_sourced(exec_profile.is_interim))
        if "CFO" in title_upper or "CHIEF FINANCIAL" in title_upper:
            cfo_tenure = exec_profile.tenure_years
            if cfo_tenure is None:
                name = _safe_sourced(exec_profile.name) or "identified"
                cfo_tenure = f"Identified: {name} (tenure unavailable)"
            interim_cfo = bool(_safe_sourced(exec_profile.is_interim))

    result["ceo_tenure_years"] = ceo_tenure
    result["cfo_tenure_years"] = cfo_tenure
    # Phase 70: XBRL dual-source aliases
    result["xbrl_ceo_tenure_years"] = ceo_tenure
    result["xbrl_cfo_tenure_years"] = cfo_tenure
    result["interim_ceo"] = interim_ceo
    result["interim_cfo"] = interim_cfo


def _map_character_fields(result: dict[str, Any], gov: Any) -> None:
    """Map board/exec character, prior litigation, and qualifications.

    Aggregates across all directors and executives to produce counts
    for GOV.BOARD.prior_litigation, GOV.BOARD.character_conduct,
    GOV.BOARD.qualifications, and GOV.EXEC.character_conduct.
    """
    board_lit_count = 0
    board_shade_count = 0
    board_qual_count = 0
    total_directors = 0

    # Board forensic profiles (gov.board_forensics, NOT gov.board.directors)
    directors = gov.board_forensics or []
    for d in directors:
        total_directors += 1
        if getattr(d, "prior_litigation", None):
            board_lit_count += len(d.prior_litigation)
        if getattr(d, "qualifications", None):
            board_qual_count += 1

    # Executive forensic profiles (from LeadershipStability.executives)
    exec_lit_count = 0
    exec_shade_count = 0
    for ep in gov.leadership.executives:
        if getattr(ep, "prior_litigation", None):
            exec_lit_count += len(ep.prior_litigation)
        if getattr(ep, "shade_factors", None):
            exec_shade_count += len(ep.shade_factors)
            board_shade_count += len(ep.shade_factors)

    result["board_prior_litigation_count"] = board_lit_count
    result["board_character_issues"] = board_shade_count
    result["board_qualifications_pct"] = (
        round(100 * board_qual_count / total_directors, 1)
        if total_directors > 0
        else None
    )
    result["exec_character_issues"] = exec_shade_count
    result["exec_prior_litigation_count"] = exec_lit_count


# ---------------------------------------------------------------------------
# Section 6: Litigation data
# ---------------------------------------------------------------------------


def map_litigation_fields(
    signal_id: str,
    extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map litigation data for LIT.* and STOCK.LIT.* checks."""
    result: dict[str, Any] = {}
    lit = extracted.litigation
    if lit is None:
        return result

    genuine_scas = [
        c for c in lit.securities_class_actions
        if not _is_regulatory_coverage(c)
    ]
    active_scas = [c for c in genuine_scas if _safe_sourced(c.status) == "ACTIVE"]
    settled_scas = [c for c in genuine_scas if _safe_sourced(c.status) == "SETTLED"]
    result["active_sca_count"] = len(active_scas)
    result["settled_sca_count"] = len(settled_scas)
    result["total_sca_count"] = len(genuine_scas)
    result["active_matter_count"] = _safe_sourced(lit.active_matter_count)

    if active_scas:
        latest = active_scas[0]
        result["sca_lead_counsel"] = _safe_sourced(latest.lead_counsel)
        result["sca_lead_counsel_tier"] = _safe_sourced(latest.lead_counsel_tier)
        result["sca_filing_date"] = _safe_sourced(latest.filing_date)
    else:
        # No active SCAs is valid evaluation data, not DATA_UNAVAILABLE
        result["sca_filing_date"] = "No active SCAs"
        result["sca_lead_counsel"] = "No active SCAs"
        result["sca_lead_counsel_tier"] = 0

    result["sec_enforcement_stage"] = _safe_sourced(
        lit.sec_enforcement.highest_confirmed_stage
    )
    result["wells_notice"] = (
        _safe_sourced(lit.sec_enforcement.highest_confirmed_stage) == "WELLS_NOTICE"
    )
    result["aaer_count"] = _safe_sourced(lit.sec_enforcement.aaer_count)
    result["comment_letter_count"] = _safe_sourced(
        lit.sec_enforcement.comment_letter_count
    )
    result["derivative_suit_count"] = len(lit.derivative_suits)
    result["regulatory_count"] = len(lit.regulatory_proceedings)

    total_contingent = 0.0
    for cl in lit.contingent_liabilities:
        accrued = _safe_sourced(cl.accrued_amount)
        if accrued is not None:
            total_contingent += accrued
    result["contingent_liabilities_total"] = (
        round(total_contingent / 1_000_000, 1) if total_contingent > 0 else 0
    )

    result["defense_strength"] = _safe_sourced(lit.defense.overall_defense_strength)
    result["defense_assessment"] = _safe_sourced(lit.defense_assessment)
    result["deal_litigation_count"] = len(lit.deal_litigation)
    result["whistleblower_count"] = len(lit.whistleblower_indicators)
    result["industry_pattern_count"] = len(lit.industry_patterns)

    # Phase 33-03: LIT.DEFENSE fields
    result["forum_selection_clause"] = _safe_sourced(
        lit.defense.forum_selection_clause
    ) if hasattr(lit.defense, "forum_selection_clause") else None
    result["pslra_safe_harbor"] = _safe_sourced(
        lit.defense.defense_narrative
    ) if hasattr(lit.defense, "defense_narrative") else None

    # Phase 33-03: LIT.PATTERN fields
    sol_open = [w for w in lit.sol_map if getattr(w, "sol_open", False)]
    result["sol_open_count"] = len(sol_open)
    # peer_contagion_risk and sector_regulatory_count not yet extracted
    result["peer_contagion_risk"] = None
    result["sector_regulatory_count"] = None

    # single_day_drops_count for LIT.PATTERN.temporal_correlation
    if extracted.market is not None:
        result["single_day_drops_count"] = len(
            extracted.market.stock_drops.single_day_drops
        )
    else:
        result["single_day_drops_count"] = None

    # LIT.OTHER fields — per-type litigation counts from wpe model
    wpe = lit.workforce_product_environmental
    result["employment_lit_count"] = len(wpe.employment_matters)
    result["product_liability_count"] = len(wpe.product_recalls)
    result["environmental_lit_count"] = len(wpe.environmental_actions)
    result["cyber_breach_count"] = len(wpe.cybersecurity_incidents)
    # Counts derived from SCA legal theories
    result["non_sca_class_action_count"] = 0  # Tracked via wpe lists above
    result["antitrust_count"] = _count_by_theory(genuine_scas, "ANTITRUST")
    result["ip_litigation_count"] = _count_by_theory(genuine_scas, "IP")
    result["trade_secret_count"] = _count_by_theory(
        genuine_scas, "TRADE_SECRET"
    )
    result["contract_dispute_count"] = 0  # Not structured in model
    result["bankruptcy_count"] = 0  # Not structured in model
    result["foreign_suit_count"] = 0  # Not structured in model
    result["gov_contract_count"] = 0  # Not structured in model

    # LIT.REG fields — per-agency regulatory counts
    _map_regulatory_agency_counts(result, lit.regulatory_proceedings)

    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# Litigation helper functions
# ---------------------------------------------------------------------------


# Agency keyword → check field_key mapping for per-agency counts.
_AGENCY_KEYWORDS: dict[str, list[str]] = {
    "state_ag_count": ["STATE AG", "ATTORNEY GENERAL"],
    "epa_action_count": ["EPA", "ENVIRONMENTAL PROTECTION"],
    "osha_citation_count": ["OSHA", "OCCUPATIONAL SAFETY"],
    "cfpb_action_count": ["CFPB", "CONSUMER FINANCIAL"],
    "fdic_order_count": ["FDIC", "FEDERAL DEPOSIT"],
    "fda_warning_count": ["FDA", "FOOD AND DRUG"],
    "dol_audit_count": ["DOL", "DEPARTMENT OF LABOR"],
    "foreign_gov_count": ["FOREIGN", "EU ", "EUROPEAN"],
    "state_action_count": ["STATE"],
    "subpoena_count": ["SUBPOENA"],
    "deferred_prosecution_count": ["DEFERRED PROSECUTION", "DPA"],
    "consent_order_count": ["CONSENT ORDER", "CONSENT DECREE"],
    "cease_desist_count": ["CEASE AND DESIST", "CEASE-AND-DESIST"],
    "civil_penalty_count": ["CIVIL PENALTY", "FINE", "MONETARY PENALTY"],
}


def _map_regulatory_agency_counts(
    result: dict[str, Any],
    proceedings: list[Any],
) -> None:
    """Parse regulatory proceedings by agency/type to produce per-field counts."""
    # Initialize all to 0
    for field_key in _AGENCY_KEYWORDS:
        result[field_key] = 0

    for proc in proceedings:
        agency = _safe_sourced(getattr(proc, "agency", None)) or ""
        ptype = _safe_sourced(getattr(proc, "proceeding_type", None)) or ""
        combined = f"{agency} {ptype}".upper()
        for field_key, keywords in _AGENCY_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                result[field_key] += 1


def _count_by_theory(scas: list[Any], theory_keyword: str) -> int:
    """Count SCAs that match a legal theory keyword."""
    count = 0
    for sca in scas:
        theories = getattr(sca, "legal_theories", []) or []
        for t in theories:
            val = _safe_sourced(t) if hasattr(t, "value") else str(t)
            if val and theory_keyword.upper() in str(val).upper():
                count += 1
                break
    return count


__all__ = ["map_governance_fields", "map_litigation_fields"]
