"""Governance context builder for D&O worksheet rendering.

Extracts governance data from AnalysisState into template-ready dicts
for Section 5: Governance & Leadership Quality.

Display data (directors, holders, departures, compensation tables) is
extracted directly from state. Evaluative content (board quality flags,
compensation red flags, structural governance) comes from signal results
via governance_evaluative.py.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._governance_helpers import (
    _build_anti_takeover,
    _build_board_meeting_data,
    _build_board_member_detail,
    _build_executive_detail,
    _build_filing_entries,
    _build_leaders,
    _safe_ceo_comp,
    _sv_str,
    _sv_bool,
    build_compensation_analysis,
    build_skills_matrix,
    build_committee_detail,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders.governance_evaluative import (
    extract_governance_evaluative,
)
from do_uw.stages.render.context_builders._governance_intelligence import (
    build_officer_backgrounds,
    build_per_insider_activity,
    build_shareholder_rights,
)

# Backward-compat alias for test imports
_build_compensation_analysis = build_compensation_analysis
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
    safe_float,
)


# Common female first names for gender diversity inference from board member names
_FEMALE_NAMES: set[str] = {
    "andrea", "monica", "sue", "susan", "mary", "patricia", "jennifer", "linda",
    "elizabeth", "barbara", "margaret", "lisa", "nancy", "karen", "betty", "helen",
    "sandra", "donna", "carol", "ruth", "sharon", "michelle", "laura", "sarah",
    "kimberly", "deborah", "jessica", "shirley", "cynthia", "angela", "melissa",
    "brenda", "amy", "anna", "rebecca", "virginia", "kathleen", "pamela", "martha",
    "debra", "amanda", "stephanie", "carolyn", "christine", "marie", "janet",
    "catherine", "frances", "ann", "joyce", "diane", "alice", "julie", "heather",
    "teresa", "doris", "gloria", "evelyn", "jean", "cheryl", "mildred", "katherine",
    "joan", "ashley", "judith", "rose", "janice", "kelly", "nicole", "judy",
    "christina", "diana", "wendy", "victoria", "ruth", "deirdre", "kate", "meg",
    "luca", "tracey", "bonnie", "irene", "denise", "tammy", "maria", "rosa",
    "wanda", "roberta", "paula", "jane", "lynn", "rachel", "robin",
}


def _derive_gender_diversity_pct(board_forensics: list[Any]) -> float | None:
    """Derive board gender diversity percentage from member first names.

    Uses a lookup of common female first names. Returns percentage of
    female members, or None if board is empty.
    """
    if not board_forensics:
        return None
    total = len(board_forensics)
    female_count = 0
    for bf in board_forensics:
        name_val = bf.name.value if hasattr(bf.name, "value") else str(bf.name) if bf.name else ""
        first_name = str(name_val).split()[0].lower().rstrip(".,") if name_val else ""
        if first_name in _FEMALE_NAMES:
            female_count += 1
    if total == 0:
        return None
    return (female_count / total) * 100


def _build_ecd_context(gov: Any) -> dict[str, Any]:
    """Build ECD (Executive Compensation Disclosure) context from DEF 14A XBRL."""
    ecd = getattr(gov, "ecd", None)
    if not ecd or not isinstance(ecd, dict):
        return {}

    def _sv_val(d: Any) -> Any:
        if isinstance(d, dict):
            return d.get("value")
        if hasattr(d, "value"):
            return d.value
        return d

    result: dict[str, Any] = {}

    ceo_name = _sv_val(ecd.get("ceo_name"))
    if ceo_name:
        result["ceo_name"] = str(ceo_name)

    ceo_total = safe_float(_sv_val(ecd.get("ceo_total_comp")), None)
    if ceo_total is not None:
        result["ceo_total_comp"] = format_currency(ceo_total, compact=True)
        result["ceo_total_comp_raw"] = ceo_total

    ceo_paid = safe_float(_sv_val(ecd.get("ceo_comp_actually_paid")), None)
    if ceo_paid is not None:
        result["ceo_comp_actually_paid"] = format_currency(ceo_paid, compact=True)
        result["ceo_comp_actually_paid_raw"] = ceo_paid

    # Pay-for-performance delta
    if ceo_total is not None and ceo_paid is not None:
        delta = ceo_paid - ceo_total
        result["pfp_delta"] = format_currency(abs(delta), compact=True)
        result["pfp_direction"] = "above" if delta >= 0 else "below"

    neo_total = safe_float(_sv_val(ecd.get("neo_avg_total_comp")), None)
    if neo_total is not None:
        result["neo_avg_total_comp"] = format_currency(neo_total, compact=True)

    neo_paid = safe_float(_sv_val(ecd.get("neo_avg_comp_actually_paid")), None)
    if neo_paid is not None:
        result["neo_avg_comp_actually_paid"] = format_currency(neo_paid, compact=True)

    co_tsr = safe_float(_sv_val(ecd.get("company_tsr")), None)
    if co_tsr is not None:
        result["company_tsr"] = f"{co_tsr:.2f}"

    peer_tsr = safe_float(_sv_val(ecd.get("peer_group_tsr")), None)
    if peer_tsr is not None:
        result["peer_group_tsr"] = f"{peer_tsr:.2f}"

    # TSR comparison
    if co_tsr is not None and peer_tsr is not None:
        result["tsr_vs_peers"] = "outperforming" if co_tsr >= peer_tsr else "underperforming"

    measure_name = _sv_val(ecd.get("company_selected_measure_name"))
    measure_amt = safe_float(_sv_val(ecd.get("company_selected_measure_amt")), None)
    if measure_name:
        result["selected_measure_name"] = str(measure_name)
    if measure_amt is not None:
        result["selected_measure_amt"] = format_currency(measure_amt * 1e6 if measure_amt < 1e6 else measure_amt, compact=True)

    # ECD award timing and insider trading policy flags (items 5.4.5-7)
    ecd_badges: list[dict[str, str]] = []
    mnpi_val = ecd.get("award_timing_mnpi_considered")
    if mnpi_val is not None:
        is_true = mnpi_val is True or (isinstance(mnpi_val, dict) and mnpi_val.get("value") is True)
        ecd_badges.append({
            "label": "MNPI Considered",
            "value": "Yes" if is_true else "No",
            "color": "green" if is_true else "red",
        })
    predetermined_val = ecd.get("award_timing_predetermined")
    if predetermined_val is not None:
        is_true = predetermined_val is True or (isinstance(predetermined_val, dict) and predetermined_val.get("value") is True)
        ecd_badges.append({
            "label": "Awards Predetermined",
            "value": "Yes" if is_true else "No",
            "color": "green" if is_true else "amber",
        })
    policy_val = ecd.get("insider_trading_policy")
    if policy_val is not None:
        is_true = policy_val is True or (isinstance(policy_val, dict) and policy_val.get("value") is True)
        ecd_badges.append({
            "label": "Trading Policy",
            "value": "Yes" if is_true else "No",
            "color": "green" if is_true else "red",
        })
    if ecd_badges:
        result["ecd_badges"] = ecd_badges

    return result


def extract_governance(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract governance data for template.

    Display data (directors, holders, departures) from state.
    Evaluative content (board flags, comp flags) from signal results.
    """
    ext = state.extracted
    if ext is None or ext.governance is None:
        return {}
    gov = ext.governance
    board = gov.board
    comp = gov.comp_analysis
    gov_score = f"{gov.governance_score.total_score.value:.0f}/100" if gov.governance_score.total_score else None

    # Derive board size from forensics if not set explicitly
    _board_size = str(board.size.value) if board.size else (
        str(len(gov.board_forensics)) if gov.board_forensics else None
    )
    result: dict[str, Any] = {
        "board_size": na_if_none(_board_size),
        "independence_ratio": format_percentage(board.independence_ratio.value * 100 if board.independence_ratio else None),
        "ceo_duality": ("Yes" if board.ceo_chair_duality and board.ceo_chair_duality.value
                        else ("No" if board.ceo_chair_duality is not None else "N/A")),
        "ceo_comp": _safe_ceo_comp(comp),
        "say_on_pay": format_percentage(comp.say_on_pay_pct.value if comp.say_on_pay_pct else None),
        "governance_score": gov_score,
    }

    # ISS governance risk scores
    iss_scores: dict[str, str] = {}
    for key, attr in [("overall", "iss_overall_risk"), ("audit", "iss_audit_risk"),
                      ("board", "iss_board_risk"), ("compensation", "iss_compensation_risk"),
                      ("shareholder_rights", "iss_shareholder_rights_risk")]:
        sv = getattr(board, attr, None)
        if sv:
            iss_scores[key] = str(sv.value)
    if iss_scores:
        result["iss_scores"] = iss_scores

    # Board quality metrics
    result["avg_tenure"] = f"{board.avg_tenure_years.value:.1f} years" if board.avg_tenure_years else "N/A"
    result["classified_board"] = _sv_bool(board.classified_board)
    result["dual_class"] = _sv_bool(board.dual_class_structure)
    result["overboarded_count"] = na_if_none(
        str(int(board.overboarded_count.value)) if board.overboarded_count is not None else None)

    # Board meeting attendance + shareholder proposals (Caremark duty assessment)
    result.update(_build_board_meeting_data(board))

    # Ownership structure
    ownership = gov.ownership
    result["institutional_pct"] = format_percentage(ownership.institutional_pct.value if ownership.institutional_pct else None)
    result["insider_pct"] = format_percentage(ownership.insider_pct.value if ownership.insider_pct else None)

    # Top holders -- main body (top 10) + overflow (rest for audit)
    holders: list[dict[str, str]] = []
    overflow_holders: list[dict[str, str]] = []
    if ownership.top_holders:
        for idx, holder in enumerate(ownership.top_holders):
            info: Any = holder.value
            name = str(info.get("name", "Unknown")) if hasattr(info, "get") else "Unknown"
            pct: Any = info.get("pct_out") or info.get("percentage") or info.get("pct") if hasattr(info, "get") else None
            pct_str = ""
            if pct is not None:
                pct_cleaned = re.sub(r"[^\d.]", "", str(pct)) if not isinstance(pct, (int, float)) else pct
                pct_f = float(pct_cleaned) if pct_cleaned else 0.0
                if pct_f < 1.0:
                    pct_f *= 100.0
                pct_str = format_percentage(pct_f)
            entry = {"name": name, "pct": pct_str}
            holders.append(entry)  # ALL holders — density, not removal
    result["top_holders"] = holders
    result["top_holders_overflow"] = []
    result["known_activists"] = [str(a.value) for a in ownership.known_activists] if ownership.known_activists else []

    # Activist signals — 13D filings, 13G-to-13D conversions, proxy contests
    result["filings_13d_24mo"] = _build_filing_entries(ownership.filings_13d_24mo)
    result["conversions_13g_to_13d"] = _build_filing_entries(
        ownership.conversions_13g_to_13d, date_keys=("date", "conversion_date"),
    )
    result["proxy_contests_3yr"] = [_sv_str(pc) for pc in ownership.proxy_contests_3yr] if ownership.proxy_contests_3yr else []

    # Leadership stability
    executives = [_build_executive_detail(ep) for ep in gov.leadership.executives]
    result["executives"] = executives
    result["departures_18mo"] = [
        {"name": _sv_str(d.name), "title": _sv_str(d.title), "type": d.departure_type or "N/A"}
        for d in gov.leadership.departures_18mo
    ]

    # Leadership stability red flags (mass departures, interim officers)
    result["leadership_red_flags"] = [_sv_str(rf) for rf in gov.leadership.red_flags] if gov.leadership.red_flags else []

    # Sentiment
    sentiment = gov.sentiment
    has_sentiment = any([sentiment.management_tone_trajectory, sentiment.hedging_language_trend,
                         sentiment.ceo_cfo_divergence, sentiment.qa_evasion_score])
    result["has_sentiment_data"] = has_sentiment
    result["management_tone"] = _sv_str(sentiment.management_tone_trajectory, fallback="")
    result["hedging_language"] = _sv_str(sentiment.hedging_language_trend, fallback="")
    result["qa_evasion"] = format_percentage(sentiment.qa_evasion_score.value * 100) if sentiment.qa_evasion_score else ""

    # Anti-takeover provisions (classified board, dual-class, poison pill, supermajority, blank check)
    anti_takeover = _build_anti_takeover(board)
    result["anti_takeover"] = anti_takeover

    # Governance Bylaws Detail (5.6.5-9)
    bylaws_provisions: list[dict[str, str]] = []
    _bylaws_fields = [
        ("exclusive_forum_provision", "Exclusive Forum Clause",
         "Channels shareholder lawsuits to the state of incorporation court (typically Delaware Chancery)"),
        ("forum_selection_clause", "Forum Selection Clause",
         "Designates specific court for shareholder complaints"),
        ("classified_board", "Classified/Staggered Board",
         "Board divided into classes serving staggered multi-year terms — limits activist ability to replace majority"),
        ("supermajority_voting", "Supermajority Voting Requirement",
         "Requires >50% shareholder approval for certain actions (e.g., bylaw amendments, mergers)"),
        ("poison_pill", "Shareholder Rights Plan (Poison Pill)",
         "Anti-takeover mechanism that dilutes hostile acquirer's stake"),
        ("blank_check_preferred", "Blank Check Preferred Stock",
         "Board authority to issue preferred shares without shareholder approval — potential takeover defense"),
    ]
    for attr, display_name, description in _bylaws_fields:
        sv_field = getattr(board, attr, None)
        if sv_field is not None and hasattr(sv_field, "value"):
            val = sv_field.value
            status = "Yes" if val else "No"
            bylaws_provisions.append({
                "provision": display_name,
                "status": status,
                "description": description,
            })
    result["bylaws_provisions"] = bylaws_provisions

    # CEO pay ratio and clawback
    if comp.ceo_pay_ratio is not None:
        result["ceo_pay_ratio"] = f"{int(comp.ceo_pay_ratio.value)}:1"
    if comp.has_clawback is not None:
        result["has_clawback"] = "Yes" if comp.has_clawback.value else "No"
    if comp.clawback_scope is not None:
        scope = str(comp.clawback_scope.value)
        result["clawback_scope"] = ("Broader than Dodd-Frank" if "BROADER" in scope.upper()
                                    else "Dodd-Frank Minimum" if "DODD" in scope.upper() else scope)

    # Related-party and perquisites
    result["related_party_transactions"] = [_sv_str(r) for r in comp.related_party_transactions] if comp.related_party_transactions else []
    result["notable_perquisites"] = [_sv_str(p) for p in comp.notable_perquisites] if comp.notable_perquisites else []

    # Narrative coherence
    coherence = gov.narrative_coherence
    coh_data: dict[str, str] = {}
    for key, attr in [("strategy_alignment", "strategy_vs_results"), ("tone_alignment", "tone_vs_financials"),
                      ("insider_alignment", "insider_vs_confidence"), ("overall", "overall_assessment")]:
        val = getattr(coherence, attr, None)
        if val is not None:
            coh_data[key] = _sv_str(val).replace("_", " ").title()
    coh_flags = [_sv_str(f) for f in coherence.coherence_flags] if coherence.coherence_flags else []
    if coh_data:
        result["narrative_coherence"] = coh_data
    if coh_flags:
        result["coherence_flags"] = coh_flags

    # Board member profiles from forensics
    # Build executive name set for independence inference
    _exec_names: set[str] = set()
    for ep in gov.leadership.executives:
        en = ep.name.value if hasattr(ep.name, "value") else str(ep.name) if ep.name else ""
        if en:
            _exec_names.add(en)
    _ceo_chair_sep = board.ceo_chair_duality is not None and not board.ceo_chair_duality.value
    result["board_members"] = [
        _build_board_member_detail(bf, executive_names=_exec_names, ceo_chair_separated=_ceo_chair_sep)
        for bf in gov.board_forensics
    ] if gov.board_forensics else []

    # Compute column-visibility flags for board forensics table:
    # Hide columns where ALL rows are empty/dashes to avoid all-dash columns.
    _bm_list = result["board_members"]
    def _has_any(key: str, empties: set[str] = {"", "None", "N/A", "—", "0"}) -> bool:
        return any(str(bm.get(key, "")).strip() not in empties for bm in _bm_list)

    result["board_has_any_age"] = any(bm.get("age") not in ("", None) for bm in _bm_list)
    result["board_has_any_other_boards"] = _has_any("other_boards")
    result["board_has_any_flags"] = any(
        (bm.get("is_overboarded") == "Yes")
        or (bm.get("prior_litigation") not in ("0", "", None) and int(bm.get("prior_litigation", "0") or "0") > 0)
        or bm.get("has_forensic_flags")
        for bm in _bm_list
    )
    result["board_has_any_detail"] = any(
        bm.get("independence_concerns_detail")
        or bm.get("relationship_flags_detail")
        or bm.get("interlocks_detail")
        or bm.get("qualification_tags")
        or bm.get("prior_litigation_details")
        for bm in _bm_list
    )

    # Gender diversity: use state value or derive from board member names
    _gender_div_pct = board.board_gender_diversity_pct.value if board.board_gender_diversity_pct else None
    if _gender_div_pct is None and gov.board_forensics:
        _gender_div_pct = _derive_gender_diversity_pct(gov.board_forensics)

    # HTML template compat: nested dicts
    result["board"] = {
        "size": result.get("board_size", "N/A"), "independence": result.get("independence_ratio", "N/A"),
        "avg_tenure": result.get("avg_tenure", "N/A"),
        "gender_diversity": format_percentage(_gender_div_pct),
        "ceo_chair_separated": "No" if result.get("ceo_duality") == "Yes" else "Yes",
        "meetings_held": result.get("board_meetings_held"),
        "attendance_pct": result.get("board_attendance_pct"),
        "directors_below_75_pct": result.get("directors_below_75_pct"),
    }
    comp_dict: dict[str, str] = {}
    if result.get("ceo_comp") and result["ceo_comp"] != "N/A":
        comp_dict["ceo_total"] = result["ceo_comp"]
    if result.get("ceo_pay_ratio"):
        comp_dict["pay_ratio"] = result["ceo_pay_ratio"]
    if result.get("say_on_pay") and result["say_on_pay"] != "N/A":
        comp_dict["say_on_pay"] = result["say_on_pay"]
    if result.get("has_clawback"):
        comp_dict["clawback"] = result["has_clawback"]
    if result.get("clawback_scope"):
        comp_dict["clawback_scope"] = result["clawback_scope"]
    if comp_dict:
        result["compensation"] = comp_dict
    if anti_takeover:
        result["anti_takeover_provisions"] = [f"{at['provision']}: {at['status']} \u2014 {at['implication']}" for at in anti_takeover]

    # Leaders for People Risk table
    leaders = _build_leaders(executives)
    if leaders:
        result["leaders"] = leaders

    # Leadership stability score
    if gov.leadership.stability_score is not None:
        result["stability_score"] = f"{gov.leadership.stability_score.value:.0f}/100"

    # Full compensation analysis
    result["compensation_analysis"] = build_compensation_analysis(comp)

    # Golden parachute value (from CompensationFlags, separate from CompensationAnalysis)
    gp_sv = gov.compensation.golden_parachute_value
    if gp_sv is not None and gp_sv.value is not None:
        gp_val = safe_float(gp_sv.value)
        result["golden_parachute"] = format_currency(gp_val, compact=True) if gp_val > 0 else "N/A"
    else:
        result["golden_parachute"] = None
    # Also inject into compensation_analysis dict for template access
    if result.get("golden_parachute") and result["golden_parachute"] != "N/A":
        result["compensation_analysis"]["golden_parachute"] = result["golden_parachute"]

    # ECD (Executive Compensation Disclosure) data from DEF 14A XBRL
    result["compensation_analysis"]["ecd"] = _build_ecd_context(gov)

    # Governance score breakdown for visual display
    gs = gov.governance_score
    score_breakdown: list[dict[str, Any]] = []
    score_fields = [
        ("Independence", "independence_score", 10),
        ("CEO/Chair", "ceo_chair_score", 10),
        ("Refreshment", "refreshment_score", 10),
        ("Overboarding", "overboarding_score", 10),
        ("Committee", "committee_score", 10),
        ("Say-on-Pay", "say_on_pay_score", 10),
        ("Tenure", "tenure_score", 10),
    ]
    for label, attr, max_val in score_fields:
        raw_val = getattr(gs, attr, None)
        if raw_val is not None:
            val = safe_float(raw_val)
            pct = min(100, int(val / max_val * 100))
            score_breakdown.append({"label": label, "score": f"{val:.1f}", "max": str(max_val), "pct": pct})
    if score_breakdown:
        result["score_breakdown"] = score_breakdown

    # Board tenure distribution for visual display
    tenure_distribution: list[dict[str, Any]] = []
    if gov.board_forensics:
        for bf in gov.board_forensics:
            name_val = bf.name.value if hasattr(bf.name, "value") else str(bf.name)
            tenure_val = bf.tenure_years.value if bf.tenure_years and hasattr(bf.tenure_years, "value") else None
            if tenure_val is not None:
                # Use last "real" name part (skip suffixes like Jr., III, etc.)
                name_parts = str(name_val).split() if name_val else []
                suffixes = {"Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV"}
                short_name = "?"
                for part in reversed(name_parts):
                    clean = part.rstrip(",.")
                    if clean not in suffixes and clean:
                        short_name = clean
                        break
                # Use same independence inference as board member profiles
                raw_indep = bf.is_independent.value if bf.is_independent and hasattr(bf.is_independent, "value") else None
                if raw_indep is True:
                    is_indep = True
                elif raw_indep is False and _ceo_chair_sep:
                    full_name = str(name_val) if name_val else ""
                    is_indep = not any(full_name.lower() in en.lower() or en.lower() in full_name.lower()
                                       for en in _exec_names)
                else:
                    is_indep = raw_indep or False
                tenure_distribution.append({
                    "name": short_name,
                    "years": safe_float(tenure_val),
                    "independent": is_indep,
                })
    if tenure_distribution:
        tenure_distribution.sort(key=lambda x: x["years"], reverse=True)
        result["tenure_distribution"] = tenure_distribution

    # Board Skills Matrix — aggregate qualification_tags across all directors
    skills_matrix = build_skills_matrix(gov.board_forensics)
    if skills_matrix:
        result["skills_matrix"] = skills_matrix

    # Committee Membership Detail — structured view of committee assignments
    committee_detail = build_committee_detail(gov.board_forensics)
    if committee_detail:
        result["committee_detail"] = committee_detail

    # Signal-backed evaluative content
    evaluative = extract_governance_evaluative(signal_results)
    result.update(evaluative)

    # Governance intelligence: officer backgrounds, shareholder rights, per-insider activity
    result.update(build_officer_backgrounds(state))
    result.update(build_shareholder_rights(state))
    result.update(build_per_insider_activity(state))

    return result


__all__ = ["extract_governance"]
