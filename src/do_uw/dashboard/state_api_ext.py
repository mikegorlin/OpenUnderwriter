"""Extended dashboard state API: sections 5-8, meeting prep, peers, helpers.

Split from state_api.py for 500-line compliance. Contains specialized
extractors for governance, litigation, scoring, AI risk, meeting prep,
peer metrics, risk signals, and company/financial data.
"""

from __future__ import annotations

from typing import Any, cast

from do_uw.models.state import AnalysisState
from do_uw.stages.render.md_renderer import build_template_context


def _finding(label: str, value: str, sid: str, idx: int, **kw: Any) -> dict[str, Any]:
    """Build a finding dict with standard keys."""
    base: dict[str, Any] = {
        "label": label, "value": value, "confidence": "HIGH",
        "section_id": sid, "idx": idx,
    }
    base.update(kw)
    return base


# -- Section 5: Governance --------------------------------------------------

def extract_governance_detail(state: AnalysisState) -> dict[str, Any]:
    """Extract governance data for section drill-down."""
    findings: list[dict[str, Any]] = []
    section_data: dict[str, Any] = {}
    ctx = build_template_context(state)
    gov_ctx = ctx.get("governance")
    if isinstance(gov_ctx, dict):
        section_data = cast(dict[str, Any], gov_ctx)
    ext = state.extracted
    if ext is not None and ext.governance is not None:
        gov = ext.governance
        board = gov.board
        if board.size and board.size.value:
            findings.append(_finding("Board Size", f"{board.size.value} directors", "governance", len(findings)))
        if board.independence_ratio and board.independence_ratio.value:
            pct = board.independence_ratio.value * 100
            findings.append(_finding("Board Independence", f"{pct:.0f}% independent", "governance", len(findings)))
        if board.ceo_chair_duality is not None:
            dual = "Yes" if board.ceo_chair_duality.value else "No"
            findings.append(_finding("CEO/Chair Duality", dual, "governance", len(findings)))
        comp = gov.comp_analysis
        if comp.ceo_total_comp is not None and comp.ceo_total_comp.value:
            from do_uw.stages.render.formatters import format_currency
            findings.append(_finding(
                "CEO Total Compensation",
                format_currency(float(comp.ceo_total_comp.value), compact=True),
                "governance", len(findings),
            ))
        if comp.say_on_pay_pct is not None and comp.say_on_pay_pct.value:
            findings.append(_finding("Say-on-Pay Approval", f"{comp.say_on_pay_pct.value:.0f}%", "governance", len(findings)))
        gs = gov.governance_score
        if gs.total_score is not None and gs.total_score.value:
            findings.append(_finding("Governance Score", f"{gs.total_score.value:.0f}/100", "governance", len(findings)))
    return {"title": "Governance", "section_id": "governance", "findings": findings, "charts": [], "data": section_data}


# -- Section 6: Litigation --------------------------------------------------

def extract_litigation_detail(state: AnalysisState) -> dict[str, Any]:
    """Extract litigation data for section drill-down."""
    findings: list[dict[str, Any]] = []
    section_data: dict[str, Any] = {}
    ctx = build_template_context(state)
    lit_ctx = ctx.get("litigation")
    if isinstance(lit_ctx, dict):
        section_data = cast(dict[str, Any], lit_ctx)
    ext = state.extracted
    if ext is not None and ext.litigation is not None:
        lit = ext.litigation
        active = lit.active_matter_count.value if lit.active_matter_count else 0
        findings.append(_finding(
            "Active Matters",
            f"{active} active matter(s)" if active else "No active litigation",
            "litigation", len(findings),
        ))
        hist = lit.historical_matter_count.value if lit.historical_matter_count else 0
        findings.append(_finding(
            "Historical Matters",
            f"{hist} historical matter(s)" if hist else "No historical cases",
            "litigation", len(findings),
        ))
        cases_list: list[Any] = section_data.get("cases", [])
        for case in cases_list:
            case_d = cast(dict[str, str], case) if isinstance(case, dict) else None
            if case_d is not None:
                findings.append(_finding(
                    case_d.get("name", "Unknown Case"),
                    f"Status: {case_d.get('status', 'N/A')} | Coverage: {case_d.get('coverage', 'N/A')}",
                    "litigation", len(findings),
                ))
        sol_windows: list[Any] = section_data.get("sol_windows", [])
        open_count: int = section_data.get("open_sol_count", 0)
        if sol_windows:
            findings.append(_finding(
                "SOL Windows",
                f"{len(sol_windows)} claim types tracked, {open_count} OPEN",
                "litigation", len(findings),
            ))
    return {"title": "Litigation", "section_id": "litigation", "findings": findings, "charts": [], "data": section_data}


# -- Section 7: Scoring -----------------------------------------------------

_SCORING_CHARTS = [
    {"id": "detail-risk-radar", "url": "/api/chart/risk-radar", "title": "Risk Radar"},
    {"id": "detail-factor-bars", "url": "/api/chart/factor-bars", "title": "Factor Deductions"},
    {"id": "detail-red-flags", "url": "/api/chart/red-flags", "title": "Red Flags"},
]


def extract_scoring_detail(state: AnalysisState) -> dict[str, Any]:
    """Extract scoring data for section drill-down."""
    findings: list[dict[str, Any]] = []
    section_data: dict[str, Any] = {}
    ctx = build_template_context(state)
    sc_ctx = ctx.get("scoring")
    if isinstance(sc_ctx, dict):
        section_data = cast(dict[str, Any], sc_ctx)
    if state.scoring is not None:
        sc = state.scoring
        for fs in sc.factor_scores:
            frac = fs.points_deducted / fs.max_points if fs.max_points > 0 else 0.0
            findings.append(_finding(
                fs.factor_name,
                f"{fs.points_deducted:.1f}/{fs.max_points} pts ({frac:.0%} risk)",
                "scoring", len(findings),
                evidence=fs.evidence, rules=fs.rules_triggered,
            ))
        for rf in sc.red_flags:
            if rf.triggered:
                ceiling = f" (ceiling: {rf.ceiling_applied})" if rf.ceiling_applied else ""
                findings.append(_finding(
                    f"RED FLAG: {rf.flag_name or rf.flag_id}",
                    ("; ".join(rf.evidence) if rf.evidence else "Triggered") + ceiling,
                    "scoring", len(findings),
                    evidence=rf.evidence or [], rules=[],
                ))
        for pat in sc.patterns_detected:
            if pat.detected:
                findings.append(_finding(
                    f"PATTERN: {pat.pattern_name or pat.pattern_id}",
                    f"Severity: {pat.severity or 'BASELINE'}",
                    "scoring", len(findings),
                ))
    return {"title": "Risk Scoring", "section_id": "scoring", "findings": findings, "charts": _SCORING_CHARTS, "data": section_data}


# -- Section 8: AI Risk -----------------------------------------------------

def extract_ai_risk_detail(state: AnalysisState) -> dict[str, Any]:
    """Extract AI risk assessment detail for drill-down."""
    findings: list[dict[str, Any]] = []
    ai_data: dict[str, Any] = {}
    if state.extracted is not None and state.extracted.ai_risk is not None:
        ai = state.extracted.ai_risk
        findings.append(_finding("AI Risk Score", f"{ai.overall_score:.0f}/100", "ai_risk", len(findings)))
        sub_dims: list[dict[str, Any]] = []
        for dim in ai.sub_dimensions:
            sub_dims.append({
                "dimension": dim.dimension, "score": dim.score,
                "weight": dim.weight, "threat_level": dim.threat_level,
                "evidence": dim.evidence,
            })
            findings.append(_finding(
                dim.dimension.replace("_", " ").title(),
                f"Score: {dim.score:.1f}/10 | Threat: {dim.threat_level}",
                "ai_risk", len(findings),
            ))
        ai_data = {
            "overall_score": ai.overall_score,
            "industry_model_id": ai.industry_model_id,
            "disclosure_trend": ai.disclosure_trend,
            "sub_dimensions": sub_dims,
            "disclosure_data": {
                "mention_count": ai.disclosure_data.mention_count,
                "sentiment": ai.disclosure_data.sentiment,
                "yoy_trend": ai.disclosure_data.yoy_trend,
            },
            "patent_activity": {
                "ai_patent_count": ai.patent_activity.ai_patent_count,
                "filing_trend": ai.patent_activity.filing_trend,
            },
            "competitive_position": {
                "company_ai_mentions": ai.competitive_position.company_ai_mentions,
                "peer_avg_mentions": ai.competitive_position.peer_avg_mentions,
                "adoption_stance": ai.competitive_position.adoption_stance,
            },
            "narrative": ai.narrative,
            "forward_indicators": ai.forward_indicators,
            "peer_comparison_available": ai.peer_comparison_available,
        }
    return {"title": "AI Transformation Risk", "section_id": "ai_risk", "findings": findings, "charts": [], "data": ai_data}


# -- Meeting Prep -----------------------------------------------------------

def extract_meeting_prep_data(
    state: AnalysisState, category: str | None = None,
) -> list[dict[str, str]]:
    """Extract meeting prep questions with optional category filtering."""
    ctx = build_template_context(state)
    questions: list[dict[str, str]] = ctx.get("meeting_questions", [])
    if category is not None:
        cat_upper = category.upper()
        questions = [q for q in questions if q.get("category") == cat_upper]
    return questions


# -- Peer Comparison --------------------------------------------------------

def extract_peer_metrics(state: AnalysisState) -> dict[str, Any]:
    """Extract available peer comparison metrics."""
    metrics: list[dict[str, str]] = [{"key": "quality_score", "label": "Quality Score"}]
    if state.benchmark is not None:
        for key, detail in state.benchmark.metric_details.items():
            metrics.append({"key": key, "label": detail.metric_name})
    return {"ticker": state.ticker, "available_metrics": metrics, "default_metric": "quality_score"}


# -- Risk Signals & Top Findings --------------------------------------------

def count_risk_signals(state: AnalysisState) -> dict[str, int]:
    """Count risk signals by severity from scoring data."""
    counts = {"critical": 0, "elevated": 0, "moderate": 0}
    if state.scoring is None:
        return counts
    for rf in state.scoring.red_flags:
        if rf.triggered:
            counts["critical"] += 1
    for fs in state.scoring.factor_scores:
        if fs.max_points > 0:
            ratio = fs.points_deducted / fs.max_points
            if ratio >= 0.7:
                counts["elevated"] += 1
            elif ratio >= 0.3:
                counts["moderate"] += 1
    for pat in state.scoring.patterns_detected:
        if pat.detected:
            counts["elevated"] += 1
    return counts


def extract_top_findings(
    state: AnalysisState, max_items: int = 5,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Extract top negative and positive findings with severity."""
    negatives: list[dict[str, str]] = []
    positives: list[dict[str, str]] = []
    es = state.executive_summary
    if es is not None and es.key_findings is not None:
        for kf in es.key_findings.negatives[:max_items]:
            negatives.append({
                "text": kf.evidence_narrative,
                "severity": "ELEVATED",
                "source": kf.section_origin,
            })
        for kf in es.key_findings.positives[:max_items]:
            positives.append({
                "text": kf.evidence_narrative, "severity": "NEUTRAL",
                "source": kf.section_origin,
            })
    return negatives, positives


# -- Company & Financial Data -----------------------------------------------

def get_company_data(state: AnalysisState) -> dict[str, Any]:
    """Extract rich company profile data for dashboard header/sidebar."""
    result: dict[str, Any] = {
        "ticker": state.ticker, "company_name": "Unknown Company",
        "sic_code": None, "state_of_inc": None,
        "market_cap": None, "employee_count": None,
        "business_description": None,
    }
    prof = state.company
    if prof is None:
        return result
    identity = prof.identity
    if identity:
        if identity.legal_name:
            result["company_name"] = str(identity.legal_name.value)
        if identity.sic_code:
            result["sic_code"] = str(identity.sic_code.value)
        if identity.state_of_incorporation:
            result["state_of_inc"] = str(identity.state_of_incorporation.value)
    if prof.market_cap:
        result["market_cap"] = prof.market_cap.value
    if prof.employee_count:
        result["employee_count"] = prof.employee_count.value
    if prof.business_description:
        raw = prof.business_description
        val = raw.value if hasattr(raw, "value") else raw
        if val:
            result["business_description"] = str(val)
    return result


def get_financial_data(state: AnalysisState) -> dict[str, Any]:
    """Extract complete financial data for charts and drill-down."""
    result: dict[str, Any] = {
        "has_data": False, "distress": {},
        "leverage": None, "liquidity": None, "earnings_quality": None,
    }
    ext = state.extracted
    if ext is None or ext.financials is None:
        return result
    fin = ext.financials
    result["has_data"] = True
    distress = fin.distress
    models: dict[str, dict[str, Any]] = {}
    for model_name, field_name in [
        ("z_score", "altman_z_score"), ("o_score", "ohlson_o_score"),
        ("m_score", "beneish_m_score"), ("f_score", "piotroski_f_score"),
    ]:
        val = getattr(distress, field_name, None)
        if val is not None:
            models[model_name] = {"score": val.score, "zone": str(val.zone) if val.zone else None}
    result["distress"] = models
    if fin.leverage is not None:
        result["leverage"] = fin.leverage.value
    if fin.liquidity is not None:
        result["liquidity"] = fin.liquidity.value
    if fin.earnings_quality is not None:
        result["earnings_quality"] = fin.earnings_quality.value
    return result


__all__ = [
    "count_risk_signals",
    "extract_ai_risk_detail",
    "extract_governance_detail",
    "extract_litigation_detail",
    "extract_meeting_prep_data",
    "extract_peer_metrics",
    "extract_scoring_detail",
    "extract_top_findings",
    "get_company_data",
    "get_financial_data",
]
