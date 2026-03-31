"""AI Transformation Risk scoring engine.

Computes a 0-100 composite AI risk score from 5 sub-dimensions,
weighted by industry-specific config from ai_risk_weights.json.

The industry impact model's threat_level acts as a Bayesian prior:
HIGH -> base 7/10, MEDIUM -> 5/10, LOW -> 3/10. Extraction evidence
then adjusts up or down from that baseline.

Scoring logic lives here in stages/score/ per CLAUDE.md.
Per-dimension scorers are in ai_risk_dimensions.py (500-line split).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.knowledge.ai_impact_models import get_ai_impact_model
from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.score.ai_risk_dimensions import (
    generate_ai_risk_narrative,
    score_competitive_moat,
    score_cost_structure,
    score_regulatory_ip,
    score_revenue_displacement,
    score_workforce_automation,
)

logger = logging.getLogger(__name__)



# Re-export dimension scorers + narrative for public API
__all__ = [
    "generate_ai_risk_narrative",
    "score_ai_risk",
    "score_competitive_moat",
    "score_cost_structure",
    "score_regulatory_ip",
    "score_revenue_displacement",
    "score_workforce_automation",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_ai_risk(state: AnalysisState) -> AIRiskAssessment:
    """Score AI transformation risk for a company.

    Reads extraction data from state.extracted.ai_risk and applies
    industry-specific weights to produce a 0-100 composite score.

    Args:
        state: The full analysis state.

    Returns:
        Populated AIRiskAssessment with sub-dimension scores and narrative.
    """
    # Load config weights
    weights = _load_weights()

    # Determine industry model
    sic_code = _get_sic_code(state)
    impact_model = get_ai_impact_model(sic_code, state.active_playbook_id)
    model_id: str = impact_model.get("id", "GENERIC")
    industry_name: str = impact_model.get("industry", "General")

    # Get industry-specific weights (fall back to default)
    industry_weights: dict[str, float] = weights.get(
        model_id, weights.get("default", {})
    )

    # Get extraction data (may be empty/default)
    disclosure = AIDisclosureData()
    patents = AIPatentActivity()
    competitive = AICompetitivePosition()

    if state.extracted is not None and state.extracted.ai_risk is not None:
        disclosure = state.extracted.ai_risk.disclosure_data
        patents = state.extracted.ai_risk.patent_activity
        competitive = state.extracted.ai_risk.competitive_position

    # Score each sub-dimension
    exposure_areas: dict[str, Any] = impact_model.get("exposure_areas", {})

    dimensions: list[AISubDimension] = []
    dimension_names = [
        "revenue_displacement",
        "cost_structure",
        "competitive_moat",
        "workforce_automation",
        "regulatory_ip",
    ]

    for dim_name in dimension_names:
        area = exposure_areas.get(dim_name, {})
        weight = industry_weights.get(dim_name, 0.20)

        score_val, evidence = _score_dimension(
            dim_name, disclosure, patents, competitive, area
        )

        threat_level: str = area.get("threat_level", "UNKNOWN")
        dimensions.append(
            AISubDimension(
                dimension=dim_name,
                score=score_val,
                weight=weight,
                evidence=evidence,
                threat_level=threat_level,
            )
        )

    # Compute overall score: sum(sub_score * weight * 10) for 0-100 range
    overall = sum(d.score * d.weight * 10.0 for d in dimensions)
    overall = max(0.0, min(100.0, overall))

    # Build assessment
    assessment = AIRiskAssessment(
        overall_score=round(overall, 1),
        sub_dimensions=dimensions,
        disclosure_data=disclosure,
        patent_activity=patents,
        competitive_position=competitive,
        industry_model_id=model_id,
        disclosure_trend=disclosure.yoy_trend,
        peer_comparison_available=competitive.percentile_rank is not None,
        data_sources=_determine_data_sources(
            disclosure, patents, competitive
        ),
    )

    # Generate narrative
    assessment.narrative = generate_ai_risk_narrative(
        assessment, industry_name
    )
    assessment.narrative_source = f"AI impact model {model_id}"
    assessment.narrative_confidence = (
        "MEDIUM" if assessment.data_sources else "LOW"
    )

    return assessment


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _score_dimension(
    dim_name: str,
    disclosure: AIDisclosureData,
    patents: AIPatentActivity,
    competitive: AICompetitivePosition,
    area: dict[str, Any],
) -> tuple[float, list[str]]:
    """Route to the appropriate dimension scorer."""
    # Build a minimal impact_model dict for the scorer
    impact_stub: dict[str, Any] = {"exposure_areas": {dim_name: area}}

    if dim_name == "revenue_displacement":
        return score_revenue_displacement(disclosure, impact_stub)
    if dim_name == "cost_structure":
        return score_cost_structure(disclosure, impact_stub)
    if dim_name == "competitive_moat":
        return score_competitive_moat(patents, competitive, impact_stub)
    if dim_name == "workforce_automation":
        return score_workforce_automation(disclosure, impact_stub)
    if dim_name == "regulatory_ip":
        return score_regulatory_ip(disclosure, patents, impact_stub)

    # Fallback for unknown dimension
    logger.warning("Unknown AI risk dimension: %s", dim_name)
    return 5.0, [f"Unknown dimension: {dim_name}"]


def _load_weights() -> dict[str, Any]:
    """Load AI risk weights from config JSON."""
    data = load_config("ai_risk_weights")
    if not data:
        logger.warning("Failed to load AI risk weights, using defaults")
        return {
            "default": {
                "revenue_displacement": 0.25,
                "cost_structure": 0.20,
                "competitive_moat": 0.25,
                "workforce_automation": 0.20,
                "regulatory_ip": 0.10,
            }
        }
    return data


def _get_sic_code(state: AnalysisState) -> int | None:
    """Extract SIC code from state as int."""
    if state.company is None:
        return None
    sic_sv = state.company.identity.sic_code
    if sic_sv is None:
        return None
    try:
        return int(sic_sv.value)
    except (ValueError, TypeError):
        return None


def _determine_data_sources(
    disclosure: AIDisclosureData,
    patents: AIPatentActivity,
    competitive: AICompetitivePosition,
) -> list[str]:
    """Determine which data sources contributed to the assessment."""
    sources: list[str] = []
    if disclosure.mention_count > 0:
        sources.append("SEC filings (AI disclosure analysis)")
    if patents.ai_patent_count > 0:
        sources.append("Patent database")
    if competitive.adoption_stance != "UNKNOWN":
        sources.append("Peer comparison analysis")
    return sources
