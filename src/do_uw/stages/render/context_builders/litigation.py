"""Litigation context builder for D&O worksheet rendering.

Extracts litigation data from AnalysisState into template-ready dicts
for Section 6: Litigation Landscape.

Display data (case lists, settlements, provisions, timelines) is
extracted directly from state via _litigation_helpers. Evaluative
content (defense strength, SEC enforcement, SoL urgency, reserve
adequacy) comes from signal results via litigation_evaluative.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._litigation_helpers import (
    COVERAGE_DISPLAY,
    _extract_contingent_liabilities,
    _extract_derivative_suits,
    _extract_sca_cases,
    _extract_sol_windows,
    _extract_whistleblower_indicators,
    _extract_workforce_product_env,
    _sv_str,
    extract_data_quality_flags,
    extract_source_references,
    format_legal_theories,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders.litigation_evaluative import (
    extract_litigation_evaluative,
)
from do_uw.stages.render.formatters import format_currency, safe_float


def extract_litigation(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract litigation data for template.

    Display data (cases, settlements, provisions) from state.
    Evaluative content (defense flags, SEC flags) from signal results.
    """
    ext = state.extracted
    if ext is None or ext.litigation is None:
        return {}
    lit = ext.litigation
    active_count = lit.active_matter_count.value if lit.active_matter_count else 0
    hist_count = lit.historical_matter_count.value if lit.historical_matter_count else 0

    cases = _extract_sca_cases(lit)

    # Enrich SCA case dicts with classifier output (Plan 01 fields)
    recovery_list = (
        lit.cases_needing_recovery
        if hasattr(lit, "cases_needing_recovery") else []
    )
    sca_list = (
        lit.securities_class_actions
        if isinstance(lit.securities_class_actions, list) else []
    )
    for i, case_dict in enumerate(cases):
        if i < len(sca_list):
            sca_obj = sca_list[i]
            case_dict["legal_theories_display"] = format_legal_theories(sca_obj)
            cov_sv = getattr(sca_obj, "coverage_type", None)
            if cov_sv is not None:
                raw_cov = _sv_str(cov_sv)
                fallback = raw_cov.replace("_", " ").title()
                case_dict["coverage_display"] = COVERAGE_DISPLAY.get(
                    raw_cov, fallback,
                )
            else:
                case_dict["coverage_display"] = ""
            case_dict["source_references"] = extract_source_references(
                sca_obj,
            )
            case_dict["data_quality_flags"] = extract_data_quality_flags(
                sca_obj, recovery_list,
            )

    sol_windows = _extract_sol_windows(lit)
    # Only count actual (non-proxy) windows for dashboard stats — proxy windows
    # are theoretical (based on annual report date) and confuse underwriters
    actual_windows = [
        w for w in sol_windows
        if w.get("confidence", "LOW") != "LOW"
        and "proxy" not in w.get("trigger_desc", "").lower()
    ]
    open_windows = sum(1 for w in actual_windows if w["status"] == "OPEN")

    active_cases = [c for c in cases if c["status"].upper() in ("ACTIVE", "PENDING", "N/A")]
    historical_cases = [c for c in cases if c["status"].upper() in (
        "SETTLED", "DISMISSED", "CLOSED", "RESOLVED")]

    result: dict[str, Any] = {
        "active_summary": f"{active_count} active matter(s)" if active_count > 0 else "No active litigation.",
        "historical_summary": f"{hist_count} historical matter(s), all resolved." if hist_count > 0 else "",
        "cases": active_cases,
        "historical_cases": historical_cases,
        "sol_windows": sol_windows,
        "open_sol_count": open_windows,
    }

    # SEC enforcement pipeline
    sec = lit.sec_enforcement
    highest = _sv_str(sec.highest_confirmed_stage) if sec.highest_confirmed_stage else "NONE"
    result["sec_enforcement_stage"] = highest
    cl_count = sec.comment_letter_count
    result["comment_letters"] = str(cl_count.value) if cl_count else "0"

    # Derivative suits
    derivative_suits = _extract_derivative_suits(lit)
    # Enrich derivative suit dicts with classifier output
    deriv_list = lit.derivative_suits if isinstance(lit.derivative_suits, list) else []
    for i, suit_dict in enumerate(derivative_suits):
        if i < len(deriv_list):
            deriv_obj = deriv_list[i]
            suit_dict["legal_theories_display"] = format_legal_theories(deriv_obj)
            cov_sv = getattr(deriv_obj, "coverage_type", None)
            if cov_sv is not None:
                raw_cov = _sv_str(cov_sv)
                fallback = raw_cov.replace("_", " ").title()
                suit_dict["coverage_display"] = COVERAGE_DISPLAY.get(
                    raw_cov, fallback,
                )
            else:
                suit_dict["coverage_display"] = ""
            suit_dict["source_references"] = extract_source_references(deriv_obj)
            suit_dict["data_quality_flags"] = extract_data_quality_flags(deriv_obj, recovery_list)
    result["derivative_suits"] = derivative_suits
    result["derivative_count"] = str(len(derivative_suits))

    # Unclassified reserves (D-07 boilerplate bucket from Plan 01 classifier)
    unclassified: list[dict[str, str]] = []
    if hasattr(lit, "unclassified_reserves") and lit.unclassified_reserves:
        for uc in lit.unclassified_reserves:
            uc_name = _sv_str(getattr(uc, "case_name", None), "Unknown")
            uc_date = _sv_str(getattr(uc, "filing_date", None))
            uc_status = _sv_str(getattr(uc, "status", None))
            unclassified.append({
                "case_name": uc_name,
                "filing_date": uc_date,
                "status": uc_status,
            })
    result["unclassified_reserves"] = unclassified

    # Regulatory proceedings
    regulatory: list[dict[str, str]] = []
    company_name = ""
    if state.company and state.company.identity:
        cn_sv = state.company.identity.legal_name
        company_name = (cn_sv.value if hasattr(cn_sv, "value") else str(cn_sv)) if cn_sv else ""
    if lit.regulatory_proceedings:
        for rp in lit.regulatory_proceedings:
            val = rp.value if hasattr(rp, "value") else rp
            if isinstance(val, dict):
                raw_agency = val.get("agency", "N/A")
                desc = val.get("description", "N/A")
                confidence = val.get("confidence", getattr(rp, "confidence", ""))
                source = val.get("source", getattr(rp, "source", ""))
                conf_str = str(confidence).upper() if confidence else ""
                source_str = str(source).lower() if source else ""
                # Filter false-positive regulatory proceedings:
                # LOW confidence web-search results that are generic articles (contain [PDF])
                # or don't mention the company name are noise, not real proceedings
                if conf_str == "LOW" and "web" in source_str:
                    if "[PDF]" in desc:
                        continue
                    if company_name and company_name.lower() not in desc.lower():
                        continue
                # Humanize SCREAMING_SNAKE_CASE agency names (e.g. DOJ_FCPA -> DOJ/FCPA)
                agency = raw_agency.replace("_", "/") if "_" in raw_agency else raw_agency
                raw_type = val.get("type", "N/A")
                proc_type = raw_type.replace("_", " ").title() if "_" in raw_type else raw_type
                regulatory.append({
                    "agency": agency,
                    "type": proc_type,
                    "description": desc,
                    "status": val.get("status", "N/A"),
                })
    result["regulatory_proceedings"] = regulatory

    # Contingent liabilities, workforce/product/env, whistleblower
    result["contingent_liabilities"] = _extract_contingent_liabilities(lit)
    result["workforce_product_env"] = _extract_workforce_product_env(lit)
    result["whistleblower_indicators"] = _extract_whistleblower_indicators(lit)

    # Industry claim patterns
    industry_patterns: list[str] = []
    if lit.industry_patterns:
        for p in lit.industry_patterns[:5]:
            if p.legal_theory:
                raw = str(p.legal_theory.value)
                industry_patterns.append(raw.replace("_", " ").title() if "_" in raw else raw)
            elif p.description:
                industry_patterns.append(str(p.description.value))
    result["industry_patterns"] = industry_patterns

    # Defense strength -- full assessment
    defense: dict[str, str] = {}
    if lit.defense:
        d = lit.defense
        if d.overall_defense_strength:
            defense["overall"] = str(d.overall_defense_strength.value)
        fp = d.forum_provisions
        if fp.has_federal_forum is not None:
            defense["federal_forum"] = "Yes" if fp.has_federal_forum.value else "No"
            if fp.federal_forum_details:
                defense["federal_forum_detail"] = _sv_str(fp.federal_forum_details)
        if fp.has_exclusive_forum is not None:
            defense["exclusive_forum"] = "Yes" if fp.has_exclusive_forum.value else "No"
            if fp.exclusive_forum_details:
                defense["exclusive_forum_detail"] = _sv_str(fp.exclusive_forum_details)
        if d.pslra_safe_harbor_usage:
            defense["pslra_safe_harbor"] = _sv_str(d.pslra_safe_harbor_usage)
        if d.truth_on_market_viability:
            defense["truth_on_market"] = _sv_str(d.truth_on_market_viability)
        if d.judge_track_record:
            defense["judge_track_record"] = _sv_str(d.judge_track_record)
        if d.prior_dismissal_success:
            defense["prior_dismissal"] = _sv_str(d.prior_dismissal_success)
        if d.defense_narrative:
            defense["narrative"] = _sv_str(d.defense_narrative)
    result["defense"] = defense
    result["defense_strength"] = defense.get("overall", "N/A")

    # Litigation reserve — value may be stored in millions (< 10,000 = millions)
    if lit.total_litigation_reserve and lit.total_litigation_reserve.value:
        reserve_val = safe_float(lit.total_litigation_reserve.value)
        if 0 < reserve_val < 10_000:
            reserve_val = reserve_val * 1_000_000
        result["litigation_reserve"] = format_currency(reserve_val, compact=True)
    else:
        result["litigation_reserve"] = "N/A"

    # --- HTML template compatibility aliases ---
    result["active_matters"] = active_cases

    pipeline_pos = _sv_str(sec.pipeline_position) if sec.pipeline_position else "NONE"
    wells = "Yes" if "WELLS" in highest.upper() or "WELLS" in pipeline_pos.upper() else "No"
    investigation = "Yes" if "INVESTIGATION" in highest.upper() or "INVESTIGATION" in pipeline_pos.upper() else "No"
    result["sec_enforcement"] = {
        "highest_stage": highest, "wells_notice": wells,
        "comment_letters": result["comment_letters"], "investigation": investigation,
    }

    settlements: list[dict[str, str]] = [{
        "case_name": hc.get("case_name", "N/A"), "amount": hc.get("settlement_amount", "N/A"),
        "year": hc.get("filing_date", "N/A"), "type": hc.get("coverage_type", "N/A"),
    } for hc in historical_cases]
    result["settlements"] = settlements

    if sol_windows:
        open_list = [w for w in sol_windows if w["status"] == "OPEN"]
        result["sol_analysis"] = {
            "window_status": f"{open_windows} open" if open_windows > 0 else "All closed",
            "earliest_open": open_list[0].get("earliest_date", "N/A") if open_list else "N/A",
            "repose_deadline": open_list[0].get("repose_date", "N/A") if open_list else "N/A",
        }

    # Litigation dashboard summary
    total_matters = len(active_cases) + len(historical_cases) + len(derivative_suits) + len(regulatory)
    result["dashboard"] = {
        "total_matters": total_matters,
        "active_count": len(active_cases),
        "historical_count": len(historical_cases),
        "derivative_count": len(derivative_suits),
        "regulatory_count": len(regulatory),
        "contingent_count": len(result["contingent_liabilities"]),
        "open_sol_windows": open_windows,
        "total_sol_windows": len(actual_windows),
        "litigation_reserve": result.get("litigation_reserve", "N/A"),
        "sec_stage": highest,
        "defense_strength": defense.get("overall", "N/A"),
    }

    # Deal litigation (SECT6-03) — from state.extracted.litigation.deal_litigation
    deal_litigation_items: list[dict[str, str]] = []
    if lit.deal_litigation:
        for dl in lit.deal_litigation:
            deal_name = _sv_str(dl.deal_name) if dl.deal_name else "—"
            lit_type = _sv_str(dl.litigation_type) if dl.litigation_type else "—"
            dl_status = _sv_str(dl.status) if dl.status else "—"
            court_str = _sv_str(dl.court) if dl.court else "—"
            filing_date_str = str(dl.filing_date.value) if dl.filing_date else "—"
            settlement_str = (
                format_currency(dl.settlement_amount.value, compact=True)
                if dl.settlement_amount is not None
                else "—"
            )
            desc_str = _sv_str(dl.description) if dl.description else ""
            deal_litigation_items.append({
                "deal_name": deal_name,
                "litigation_type": lit_type.replace("_", " ").title(),
                "status": dl_status,
                "court": court_str,
                "filing_date": filing_date_str,
                "settlement": settlement_str,
                "description": desc_str if desc_str != "N/A" else "",
            })
    result["deal_litigation"] = deal_litigation_items

    # M&A activity context — surface recent deals when no deal litigation found
    # so template can show a contextual note instead of a bare negative
    ma_activity_items: list[str] = []
    if state.company is not None:
        # business_changes often contain M&A descriptions (acquisitions, divestitures)
        for sv_change in state.company.business_changes:
            val = str(sv_change.value if hasattr(sv_change, "value") else sv_change).strip()
            if not val:
                continue
            val_lower = val.lower()
            if any(kw in val_lower for kw in (
                "acqui", "divesti", "merger", "spin-off", "spinoff",
                "joint venture", "sale of", "sold", "purchase",
            )):
                ma_activity_items.append(val)
        # Also check explicit acquisitions list
        for sv_acq in state.company.acquisitions:
            val = str(sv_acq.value if hasattr(sv_acq, "value") else sv_acq).strip()
            if val and val not in ma_activity_items:
                ma_activity_items.append(val)
    result["ma_activity_notes"] = ma_activity_items[:5]  # Cap at 5 for display

    # Litigation timeline events (SECT6-10)
    timeline_events: list[dict[str, str]] = []
    for evt in lit.litigation_timeline_events:
        evt_type_raw = ""
        if evt.event_type:
            evt_type_raw = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
        desc_raw = ""
        if evt.description:
            desc_raw = evt.description.value if hasattr(evt.description, "value") else str(evt.description)
        sev_raw = ""
        if evt.severity:
            sev_raw = evt.severity.value if hasattr(evt.severity, "value") else str(evt.severity)
        timeline_events.append({
            "date": str(evt.event_date) if evt.event_date else "N/A",
            "type": str(evt_type_raw),
            "description": str(desc_raw),
            "severity": str(sev_raw),
        })
    result["timeline_events"] = timeline_events

    # SEC comment letter topics
    comment_topics: list[str] = []
    if sec.comment_letter_topics:
        for topic in sec.comment_letter_topics[:5]:
            val = topic.value if hasattr(topic, "value") else str(topic)
            if val:
                comment_topics.append(str(val))
    result["comment_letter_topics"] = comment_topics

    # Risk card from Supabase get_risk_card() — scenario benchmarks,
    # screening questions, repeat filer detail, company risk profile
    _hydrate_risk_card(state, result)

    # Signal-backed evaluative content
    evaluative = extract_litigation_evaluative(signal_results)
    result.update(evaluative)

    return result


def _hydrate_risk_card(state: AnalysisState, result: dict[str, Any]) -> None:
    """Inject risk card data into litigation context if available."""
    lit_data = getattr(state.acquired_data, "litigation_data", None) or {}
    risk_card: dict[str, Any] = lit_data.get("risk_card", {}) if isinstance(lit_data, dict) else {}
    if not risk_card:
        return

    profile = risk_card.get("company_profile", {})
    if profile:
        result["risk_card_score"] = profile.get("composite_risk_score")
        result["risk_card_score_components"] = profile.get("risk_score_components", {})

    repeat = risk_card.get("repeat_filer_detail", {})
    if repeat:
        result["risk_card_repeat_filer"] = repeat

    benchmarks = risk_card.get("scenario_benchmarks", [])
    if benchmarks:
        result["risk_card_scenario_benchmarks"] = benchmarks

    questions = risk_card.get("screening_questions", [])
    if questions:
        # Filter to scenario-matched questions only — match against this
        # company's actual scenario history from the risk card
        scenario_history = set(profile.get("scenario_history", []))
        matched = [
            q for q in questions
            if q.get("scenario") in scenario_history or q.get("scenario") == "_universal"
        ]
        result["risk_card_screening_questions"] = matched or questions

    filing_history = risk_card.get("filing_history", [])
    if filing_history:
        result["risk_card_filing_history"] = filing_history

    result["risk_card_data_note"] = risk_card.get("data_coverage_note", "")


__all__ = ["extract_litigation"]
