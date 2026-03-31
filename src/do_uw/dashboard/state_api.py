"""AnalysisState to dashboard context extraction.

Builds the template context dictionary for the dashboard by reusing
build_template_context from md_renderer and adding dashboard-specific
keys for section cards, CSS classes, and navigation.

Also provides drill-down extraction for section detail views and
finding detail. Sections 5-8, meeting prep, peer metrics, risk signal
counting, and company/financial helpers live in state_api_ext.py.
"""

from __future__ import annotations

from typing import Any, cast

from do_uw.dashboard.design import tier_to_css_class

# Import extended extraction functions (sections 5-8, helpers)
from do_uw.dashboard.state_api_ext import (
    count_risk_signals,
    extract_ai_risk_detail,
    extract_governance_detail,
    extract_litigation_detail,
    extract_meeting_prep_data,
    extract_peer_metrics,
    extract_scoring_detail,
    extract_top_findings,
)
from do_uw.dashboard.state_api_ext import (
    get_company_data as get_company_data,
)
from do_uw.dashboard.state_api_ext import (
    get_financial_data as get_financial_data,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.md_renderer import build_template_context

# Section titles used across summary and detail views
SECTION_TITLES: dict[str, str] = {
    "company": "Company Profile",
    "financials": "Financial Health",
    "market": "Market & Trading",
    "governance": "Governance",
    "litigation": "Litigation",
    "scoring": "Risk Scoring",
    "ai_risk": "AI Transformation Risk",
}

# Chart URLs applicable per section
_SECTION_CHARTS: dict[str, list[dict[str, str]]] = {
    "financials": [
        {"id": "detail-distress-z", "url": "/api/chart/distress/z_score", "title": "Altman Z-Score"},
        {"id": "detail-distress-o", "url": "/api/chart/distress/o_score", "title": "Ohlson O-Score"},
        {"id": "detail-distress-m", "url": "/api/chart/distress/m_score", "title": "Beneish M-Score"},
        {"id": "detail-distress-f", "url": "/api/chart/distress/f_score", "title": "Piotroski F-Score"},
    ],
    "scoring": [
        {"id": "detail-risk-radar", "url": "/api/chart/risk-radar", "title": "Risk Radar"},
        {"id": "detail-factor-bars", "url": "/api/chart/factor-bars", "title": "Factor Deductions"},
        {"id": "detail-red-flags", "url": "/api/chart/red-flags", "title": "Red Flags"},
    ],
    "market": [
        {"id": "detail-risk-heatmap", "url": "/api/chart/risk-heatmap", "title": "Risk Heatmap"},
    ],
    "ai_risk": [],
}


def _section_status(data: Any) -> str:
    """Return a status label based on whether section data exists."""
    if data is None:
        return "No data"
    if isinstance(data, dict) and not data:
        return "No data"
    return "Available"


def _section_status_class(data: Any) -> str:
    """Return a DaisyUI badge class based on data availability."""
    if data is None or (isinstance(data, dict) and not data):
        return "badge-ghost"
    return "badge-success"


def _build_section_summary(section_id: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """Build a summary dict for a single analytical section."""
    data = ctx.get(section_id)
    return {
        "id": section_id,
        "title": SECTION_TITLES.get(section_id, section_id.title()),
        "status": _section_status(data),
        "status_class": _section_status_class(data),
        "data": data if isinstance(data, dict) else {},
    }


def build_dashboard_context(state: AnalysisState) -> dict[str, Any]:
    """Build the complete dashboard template context from AnalysisState.

    Reuses build_template_context() from md_renderer for the base data,
    then adds dashboard-specific keys for section navigation, CSS classes,
    risk signals, and interactive features.
    """
    ctx = build_template_context(state)

    # Extract ticker and company name
    ticker = state.ticker
    company_name = "Unknown Company"
    if state.company and state.company.identity:
        sv_name = state.company.identity.legal_name
        if sv_name is not None:
            company_name = str(sv_name.value)

    # Determine scoring tier and CSS class
    tier_label: str | None = None
    quality_score: str | None = None
    if state.scoring is not None:
        quality_score = f"{state.scoring.quality_score:.1f}"
        if state.scoring.tier is not None:
            tier_label = state.scoring.tier.tier

    risk_level_class = tier_to_css_class(tier_label)

    # Build section summaries for the card grid
    section_ids = list(SECTION_TITLES.keys())
    sections = [_build_section_summary(sid, ctx) for sid in section_ids]

    # Risk signal counts for summary display
    risk_signals = count_risk_signals(state)

    # Top findings for prominent display
    negatives, positives = extract_top_findings(state)

    # Factor score mini-bars for landing page
    factor_bars: list[dict[str, Any]] = []
    if state.scoring is not None:
        for fs in state.scoring.factor_scores:
            pct = (fs.points_deducted / fs.max_points * 100) if fs.max_points > 0 else 0
            factor_bars.append({
                "name": fs.factor_name,
                "deducted": fs.points_deducted,
                "max": fs.max_points,
                "pct": round(pct, 1),
            })

    # Active red flags for summary
    active_red_flags: list[dict[str, str]] = []
    if state.scoring is not None:
        for rf in state.scoring.red_flags:
            if rf.triggered:
                active_red_flags.append({
                    "name": rf.flag_name or rf.flag_id,
                    "description": "; ".join(rf.evidence) if rf.evidence else "",
                    "ceiling": str(rf.ceiling_applied) if rf.ceiling_applied else "",
                })

    ctx.update({
        "ticker": ticker,
        "company_name": company_name,
        "tier_label": tier_label,
        "quality_score": quality_score,
        "risk_level_class": risk_level_class,
        "sections": sections,
        "risk_signals": risk_signals,
        "key_negatives": negatives,
        "key_positives": positives,
        "factor_bars": factor_bars,
        "active_red_flags": active_red_flags,
    })

    return ctx


# ---------------------------------------------------------------------------
# Section detail extraction (drill-down)
# ---------------------------------------------------------------------------


def _extract_findings_for_section(
    section_data: dict[str, Any],
    section_id: str,
) -> list[dict[str, Any]]:
    """Convert section data dict into a list of findings for display."""
    findings: list[dict[str, Any]] = []
    for key, val in section_data.items():
        if key.startswith("has_") or val is None:
            continue
        if isinstance(val, (list, dict)):
            continue
        findings.append({
            "label": key.replace("_", " ").title(),
            "value": str(val),
            "confidence": "MEDIUM",
            "section_id": section_id,
            "idx": len(findings),
        })
    return findings


def extract_section_detail(
    state: AnalysisState,
    section_id: str,
) -> dict[str, Any]:
    """Extract detailed data for a specific analytical section.

    Dispatches to specialized extractors for governance, litigation,
    scoring, and AI risk sections. Falls back to generic extraction
    for company, financials, and market.
    """
    if section_id == "governance":
        return extract_governance_detail(state)
    if section_id == "litigation":
        return extract_litigation_detail(state)
    if section_id == "scoring":
        return extract_scoring_detail(state)
    if section_id == "ai_risk":
        return extract_ai_risk_detail(state)

    # Generic extraction for company, financials, market
    ctx = build_template_context(state)
    raw_data = ctx.get(section_id)
    section_data: dict[str, Any] = (
        cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
    )
    items = _extract_findings_for_section(section_data, section_id)

    return {
        "title": SECTION_TITLES.get(section_id, section_id.title()),
        "section_id": section_id,
        "findings": items,
        "charts": _SECTION_CHARTS.get(section_id, []),
        "data": section_data,
    }


def extract_finding_detail(
    state: AnalysisState,
    section_id: str,
    finding_idx: int,
) -> dict[str, Any]:
    """Extract detail for a specific finding within a section.

    Returns evidence narrative, source citation, confidence level,
    D&O underwriting context, and scoring impact.
    """
    detail = extract_section_detail(state, section_id)
    items = detail.get("findings", [])

    if finding_idx < 0 or finding_idx >= len(items):
        return {
            "label": "Not Found",
            "value": "Finding index out of range.",
            "confidence": "LOW",
            "source": "N/A",
            "do_context": "Unable to locate the requested finding.",
            "scoring_impact": "None",
        }

    item = items[finding_idx]
    evidence = item.get("evidence", [])
    rules = item.get("rules", [])

    return {
        "label": item.get("label", "Unknown"),
        "value": item.get("value", "N/A"),
        "confidence": item.get("confidence", "MEDIUM"),
        "source": f"Section: {section_id}, Analysis pipeline",
        "do_context": (
            f"This finding relates to the {section_id} analysis area. "
            f"Review for D&O underwriting implications."
        ),
        "scoring_impact": (
            f"Rules triggered: {', '.join(rules)}" if rules
            else "No direct scoring rules identified."
        ),
        "evidence": evidence,
    }


def extract_meeting_questions(
    state: AnalysisState,
    category: str | None = None,
) -> list[dict[str, str]]:
    """Extract meeting prep questions with optional category filtering.

    Delegates to extract_meeting_prep_data in state_api_ext.py.
    """
    return extract_meeting_prep_data(state, category)


__all__ = [
    "build_dashboard_context",
    "extract_finding_detail",
    "extract_meeting_questions",
    "extract_peer_metrics",
    "extract_section_detail",
    "get_company_data",
    "get_financial_data",
]
