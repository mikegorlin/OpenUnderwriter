"""Evaluative scoring context builders -- AI risk, meeting questions, and
scoring helper functions for allegation mapping and tower recommendations.

These functions extract from post-signal computed artifacts (ScoringResult,
AllegationMapping, TowerRecommendation, SeverityScenarios, AIRiskAssessment)
rather than from brain signal results directly. This is correct because:
- Allegation mapping, tower recommendations, and severity scenarios are
  outputs of the scoring pipeline that already consumed signal results
- AI risk assessment is computed from 10-K disclosure analysis, not from
  individual brain signals (no AI-risk signal IDs exist in brain/signals/)
- Meeting questions are generated from analysis findings, not signal evaluations

The signal_results parameter on extract_ai_risk() and extract_meeting_questions()
is retained for interface consistency but these functions correctly read from
state.extracted and state.analysis (post-signal artifacts).

Extracted from scoring.py (Phase 113-04) to meet the <300 line BUILD-07 limit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.formatters import format_currency


def _load_crf_conditions() -> dict[str, str]:
    """Load CRF condition text from red_flags.json for threshold_context display."""
    rf_path = Path(__file__).parent.parent.parent.parent / "brain" / "config" / "red_flags.json"
    try:
        data = json.loads(rf_path.read_text())
        return {t["id"]: t.get("condition", "") for t in data.get("escalation_triggers", []) if "id" in t}
    except Exception:
        return {}


# Allegation theory -> human-readable name and D&O claim type mapping
_THEORY_NAMES: dict[str, str] = {
    "A_DISCLOSURE": "Disclosure & Reporting",
    "B_GUIDANCE": "Guidance & Forward Statements",
    "C_PRODUCT_OPS": "Product & Operations",
    "D_GOVERNANCE": "Governance & Fiduciary",
    "E_MA": "M&A & Corporate Transactions",
}
_THEORY_CLAIM_TYPES: dict[str, list[str]] = {
    "A_DISCLOSURE": ["10b-5 Securities Fraud", "Section 11 Registration", "SOX Violations"],
    "B_GUIDANCE": ["10b-5 Forward Statement", "Guidance Failure", "Selective Disclosure"],
    "C_PRODUCT_OPS": ["Caremark (Oversight Failure)", "Product Liability Director Exposure", "Environmental/Safety"],
    "D_GOVERNANCE": ["Entire Fairness", "Waste Claims", "Proxy Violations", "Say-on-Pay"],
    "E_MA": ["Revlon Duties", "Appraisal Rights", "Deal Protection Scrutiny"],
}


def format_pattern_description(p: Any) -> str:
    """Build a description for a composite pattern match."""
    parts: list[str] = []
    if p.severity and p.severity != "BASELINE":
        parts.append(f"Severity: {p.severity}")
    if p.triggers_matched:
        parts.append(f"Triggers: {', '.join(p.triggers_matched[:3])}")
    if p.score_impact:
        parts.append(f"Impact: {', '.join(f'{k}: +{v:.0f}' for k, v in p.score_impact.items())}")
    return ". ".join(parts) if parts else "Detected"


def build_allegation_map(sc: Any) -> dict[str, Any]:
    """Extract allegation mapping data from scoring result."""
    result: dict[str, Any] = {}
    if not sc.allegation_mapping or not sc.allegation_mapping.theories:
        return result
    allegations: list[dict[str, Any]] = []
    for te in sc.allegation_mapping.theories:
        allegations.append({
            "theory": te.theory.value,
            "theory_name": _THEORY_NAMES.get(te.theory.value, te.theory.value),
            "exposure_level": te.exposure_level,
            "evidence": "; ".join(te.findings[:2]) if te.findings else "",
            "all_findings": te.findings,
            "factor_sources": te.factor_sources,
            "claim_types": _THEORY_CLAIM_TYPES.get(te.theory.value, []),
        })
    result["allegation_map"] = allegations
    am = sc.allegation_mapping
    if hasattr(am, "concentration_analysis") and am.concentration_analysis:
        result["allegation_concentration"] = str(am.concentration_analysis)
    if hasattr(am, "primary_exposure") and am.primary_exposure:
        result["primary_exposure"] = str(am.primary_exposure.value)
    return result


def build_tower_recommendation(sc: Any) -> dict[str, Any]:
    """Extract tower recommendation data from scoring result."""
    if not sc.tower_recommendation:
        return {}
    tr = sc.tower_recommendation
    tower: dict[str, Any] = {
        "position": tr.recommended_position.value.replace("_", " ").title(),
        "min_attachment": tr.minimum_attachment or "N/A",
        "side_a": tr.side_a_assessment or "N/A",
    }
    if tr.layers:
        tower["layers"] = [
            {"position": la.position.value.replace("_", " ").title(),
             "risk": la.risk_assessment,
             "premium": la.premium_guidance, "attachment": la.attachment_range}
            for la in tr.layers
        ]
    return {"tower_recommendation": tower}


def build_severity_scenarios(sc: Any) -> dict[str, Any]:
    """Extract severity scenario data from scoring result."""
    if not sc.severity_scenarios or not sc.severity_scenarios.scenarios:
        return {}
    scenarios: list[dict[str, str]] = []
    for scenario in sc.severity_scenarios.scenarios:
        label = scenario.label or f"{scenario.percentile}th percentile"
        scenarios.append({
            "scenario": label,
            "probability": f"{scenario.percentile}th percentile",
            "expected_loss": format_currency(scenario.settlement_estimate, compact=True),
            "defense_costs": format_currency(scenario.defense_cost_estimate, compact=True),
            "total": format_currency(scenario.total_exposure, compact=True),
        })
    return {"severity_scenarios": scenarios}


def extract_scoring_do_context(
    signal_results: dict[str, Any] | None,
    scoring: Any | None = None,
) -> dict[str, Any]:
    """Extract D&O context for scoring-related tables.

    Returns do_context strings for factor scoring, pattern detection,
    and allegation mapping templates. When scoring is provided, also
    returns per-factor detail data with evidence and do_context.
    """
    result: dict[str, Any] = {}

    # Collect do_context from all signal prefixes that feed into scoring
    do_context_by_signal: dict[str, str] = {}
    for prefix in ("FIN.", "GOV.", "LIT.", "STOCK.", "BIZ.", "DISC.",
                    "EXEC.", "FWRD.", "NLP.", "ENV."):
        for view in safe_get_signals_by_prefix(signal_results, prefix):
            if view.do_context:
                do_context_by_signal[view.signal_id] = view.do_context

    # Strip generic boilerplate from do_context values before passing to templates
    _BOILERPLATE = (
        "Monitor for deterioration \u2014 trend direction and "
        "peer comparison inform the D&O risk assessment."
    )
    for sig_id in list(do_context_by_signal):
        dc = do_context_by_signal[sig_id]
        if _BOILERPLATE in dc:
            dc = dc.replace(_BOILERPLATE, "").strip()
            do_context_by_signal[sig_id] = dc

    result["scoring_do_context_map"] = do_context_by_signal

    # Per-factor detail with evidence and D&O context (Phase 116-05)
    if scoring is not None and hasattr(scoring, "factor_scores"):
        from do_uw.stages.render.sections.sect7_scoring_factors import (
            build_factor_detail_context,
        )
        result["factor_details"] = build_factor_detail_context(
            scoring, signal_results,
        )

    return result


# -- Tier Explanation (re-exported from split module for 300-line compliance) --
from do_uw.stages.render.context_builders.tier_explanation import (  # noqa: E402
    generate_tier_explanation as generate_tier_explanation,
)


# -- AI Risk --


def _ai_threat_level(score: float | None) -> str:
    """Map overall AI risk score to threat level."""
    if score is None:
        return "LOW"
    if score >= 70:
        return "HIGH"
    return "MEDIUM" if score >= 50 else "LOW"


def extract_ai_risk(
    state: AnalysisState, *, signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract AI risk data for template."""
    if state.extracted is None or state.extracted.ai_risk is None:
        return None
    ai = state.extracted.ai_risk
    dimensions: list[dict[str, Any]] = []
    for dim in ai.sub_dimensions:
        threat = str(dim.threat_level or "INFO").upper()
        status = {"HIGH": "TRIGGERED", "MEDIUM": "ELEVATED", "LOW": "CLEAR"}.get(threat, "INFO")
        dimensions.append({
            "name": dim.dimension, "weight": dim.weight,
            "score": round(dim.score, 1) if isinstance(dim.score, float) else dim.score,
            "threat": status, "threat_level": str(dim.threat_level or ""),
        })
    cp = ai.competitive_position
    return {
        "overall_score": round(ai.overall_score, 1) if isinstance(ai.overall_score, float) else ai.overall_score,
        "threat_level": _ai_threat_level(ai.overall_score),
        "model": ai.industry_model_id,
        "industry_model_id": ai.industry_model_id,
        "disclosure_trend": ai.disclosure_trend,
        "dimensions": dimensions,
        "sub_dimensions": dimensions,
        "competitive_position": {
            "company_ai_mentions": cp.company_ai_mentions,
            "peer_avg_mentions": cp.peer_avg_mentions,
            "adoption_stance": str(cp.adoption_stance or "UNKNOWN"),
        },
        "peer_comparison_available": ai.peer_comparison_available,
        "narrative": ai.narrative,
        "strategic_assessment": ai.narrative,
        "forward_indicators": ai.forward_indicators,
    }


# -- Meeting Questions --


def extract_meeting_questions(
    state: AnalysisState, *, signal_results: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Extract meeting prep questions for template."""
    pre_computed: list[str] = []
    if (state.analysis and state.analysis.pre_computed_narratives
            and state.analysis.pre_computed_narratives.meeting_prep_questions):
        pre_computed = state.analysis.pre_computed_narratives.meeting_prep_questions
    if pre_computed:
        return [
            {"category": "AI-Generated", "question": q,
             "context": "Based on automated analysis findings",
             "good_answer": "Management provides specific data and timeline",
             "bad_answer": "Vague or evasive response",
             "follow_up": "Request supporting documentation"}
            for q in pre_computed
        ]
    from do_uw.stages.render.sections.meeting_questions import (
        MeetingQuestion, generate_clarification_questions, generate_forward_indicator_questions,
    )
    from do_uw.stages.render.sections.meeting_questions_gap import (
        generate_credibility_test_questions, generate_gap_filler_questions,
    )
    all_q: list[MeetingQuestion] = []
    all_q.extend(generate_clarification_questions(state))
    all_q.extend(generate_forward_indicator_questions(state))
    all_q.extend(generate_gap_filler_questions(state))
    all_q.extend(generate_credibility_test_questions(state))
    all_q.sort(key=lambda q: q.priority, reverse=True)
    return [
        {"category": q.category, "question": q.question, "context": q.context,
         "good_answer": q.good_answer, "bad_answer": q.bad_answer, "follow_up": q.follow_up}
        for q in all_q
    ]
