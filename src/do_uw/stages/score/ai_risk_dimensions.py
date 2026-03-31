"""Per-dimension AI risk scorers and narrative generation.

Split from ai_risk_scoring.py for 500-line compliance. Contains the
5 sub-dimension scoring functions and the narrative generator.

Each scorer takes extraction data + impact model area, returns (score, evidence).
The threat_level baseline acts as a Bayesian prior: HIGH=7, MEDIUM=5, LOW=3.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)

# Threat level baseline scores (0-10 scale)
THREAT_BASELINES: dict[str, float] = {
    "HIGH": 7.0,
    "MEDIUM": 5.0,
    "LOW": 3.0,
    "UNKNOWN": 5.0,
}


# ---------------------------------------------------------------------------
# Per-dimension scoring functions (public for testability)
# ---------------------------------------------------------------------------


def score_revenue_displacement(
    disclosure: AIDisclosureData,
    impact_model: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score revenue displacement risk (0-10).

    Based on AI threat mentions ratio, competitor AI announcements,
    and industry threat_level baseline.
    """
    area = impact_model.get("exposure_areas", {}).get("revenue_displacement", {})
    threat_level: str = area.get("threat_level", "UNKNOWN")
    base = THREAT_BASELINES.get(threat_level, 5.0)
    evidence: list[str] = []

    if disclosure.mention_count == 0:
        evidence.append("Insufficient data: no AI disclosure mentions found")
        return base, evidence

    # Adjust based on threat/opportunity ratio
    total_sentiment = disclosure.threat_mentions + disclosure.opportunity_mentions
    if total_sentiment > 0:
        threat_ratio = disclosure.threat_mentions / total_sentiment
        adjustment = (threat_ratio - 0.5) * 4.0  # -2 to +2
        base += adjustment
        evidence.append(
            f"Threat/opportunity ratio: {threat_ratio:.1%} "
            f"({disclosure.threat_mentions} threats, "
            f"{disclosure.opportunity_mentions} opportunities)"
        )

    # Adjust for YoY trend
    if disclosure.yoy_trend == "INCREASING":
        base += 1.0
        evidence.append("AI disclosure mentions increasing YoY")
    elif disclosure.yoy_trend == "DECREASING":
        base -= 0.5
        evidence.append("AI disclosure mentions decreasing YoY")

    return max(0.0, min(10.0, base)), evidence


def score_cost_structure(
    disclosure: AIDisclosureData,
    impact_model: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score cost structure disruption risk (0-10).

    Based on workforce automation indicators and industry cost_structure
    threat_level baseline.
    """
    area = impact_model.get("exposure_areas", {}).get("cost_structure", {})
    threat_level: str = area.get("threat_level", "UNKNOWN")
    base = THREAT_BASELINES.get(threat_level, 5.0)
    evidence: list[str] = []

    if disclosure.mention_count == 0:
        evidence.append("Insufficient data: no AI disclosure mentions found")
        return base, evidence

    # More mentions in a high-threat industry = higher risk
    if disclosure.mention_count > 20:
        base += 1.0
        evidence.append(f"High AI mention count ({disclosure.mention_count})")
    elif disclosure.mention_count > 10:
        base += 0.5
        evidence.append(
            f"Moderate AI mention count ({disclosure.mention_count})"
        )

    # Sentiment signals
    if disclosure.sentiment == "THREAT":
        base += 0.5
        evidence.append("Company frames AI primarily as threat")
    elif disclosure.sentiment == "OPPORTUNITY":
        base -= 0.5
        evidence.append("Company frames AI primarily as opportunity")

    return max(0.0, min(10.0, base)), evidence


def score_competitive_moat(
    patents: AIPatentActivity,
    competitive: AICompetitivePosition,
    impact_model: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score competitive moat erosion risk (0-10).

    Based on patent activity, competitive position (LEADING/LAGGING),
    and industry moat threat_level baseline.

    Higher score = weaker moat (more risk).
    """
    area = impact_model.get("exposure_areas", {}).get("competitive_moat", {})
    threat_level: str = area.get("threat_level", "UNKNOWN")
    base = THREAT_BASELINES.get(threat_level, 5.0)
    evidence: list[str] = []

    has_data = (
        patents.ai_patent_count > 0
        or competitive.adoption_stance != "UNKNOWN"
    )

    if not has_data:
        evidence.append("Insufficient data: no patent or competitive data")
        return base, evidence

    # Patent activity reduces moat risk (company is investing)
    if patents.ai_patent_count > 50:
        base -= 2.0
        evidence.append(
            f"Strong AI patent portfolio ({patents.ai_patent_count})"
        )
    elif patents.ai_patent_count > 10:
        base -= 1.0
        evidence.append(
            f"Moderate AI patent portfolio ({patents.ai_patent_count})"
        )
    elif patents.ai_patent_count > 0:
        base -= 0.5
        evidence.append(f"Some AI patents ({patents.ai_patent_count})")

    # Competitive position
    if competitive.adoption_stance == "LEADING":
        base -= 1.5
        evidence.append("Leading AI adoption stance vs peers")
    elif competitive.adoption_stance == "LAGGING":
        base += 1.5
        evidence.append("Lagging AI adoption stance vs peers")
    elif competitive.adoption_stance == "INLINE":
        evidence.append("Inline AI adoption stance vs peers")

    # Percentile rank
    if competitive.percentile_rank is not None:
        if competitive.percentile_rank >= 75:
            base -= 0.5
            evidence.append(
                f"Top quartile AI engagement "
                f"({competitive.percentile_rank:.0f}th pctile)"
            )
        elif competitive.percentile_rank <= 25:
            base += 0.5
            evidence.append(
                f"Bottom quartile AI engagement "
                f"({competitive.percentile_rank:.0f}th pctile)"
            )

    return max(0.0, min(10.0, base)), evidence


def score_workforce_automation(
    disclosure: AIDisclosureData,
    impact_model: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score workforce automation risk (0-10).

    Based on disclosure mentions of automation and industry workforce
    threat_level baseline.
    """
    area = impact_model.get("exposure_areas", {}).get(
        "workforce_automation", {}
    )
    threat_level: str = area.get("threat_level", "UNKNOWN")
    base = THREAT_BASELINES.get(threat_level, 5.0)
    evidence: list[str] = []

    if disclosure.mention_count == 0:
        evidence.append("Insufficient data: no AI disclosure mentions found")
        return base, evidence

    # Disclosure volume signals awareness
    if disclosure.mention_count > 30:
        base += 1.0
        evidence.append(
            f"Extensive AI disclosure ({disclosure.mention_count} mentions) "
            "suggests significant workforce impact awareness"
        )
    elif disclosure.mention_count > 15:
        base += 0.5
        evidence.append(
            f"Notable AI disclosure ({disclosure.mention_count} mentions)"
        )

    # Risk factor count
    if len(disclosure.risk_factors) >= 3:
        base += 0.5
        evidence.append(
            f"Multiple AI risk factors disclosed "
            f"({len(disclosure.risk_factors)})"
        )

    return max(0.0, min(10.0, base)), evidence


def score_regulatory_ip(
    disclosure: AIDisclosureData,
    patents: AIPatentActivity,
    impact_model: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score regulatory and IP risk from AI (0-10).

    Based on AI regulatory mentions, patent count, and industry
    regulatory_ip threat_level baseline.
    """
    area = impact_model.get("exposure_areas", {}).get("regulatory_ip", {})
    threat_level: str = area.get("threat_level", "UNKNOWN")
    base = THREAT_BASELINES.get(threat_level, 5.0)
    evidence: list[str] = []

    has_data = disclosure.mention_count > 0 or patents.ai_patent_count > 0

    if not has_data:
        evidence.append("Insufficient data: no disclosure or patent data")
        return base, evidence

    # Patent activity increases regulatory exposure
    if patents.ai_patent_count > 20:
        base += 1.0
        evidence.append(
            f"Significant AI patent activity ({patents.ai_patent_count}) "
            "increases IP management complexity"
        )
    elif patents.ai_patent_count > 5:
        base += 0.5
        evidence.append(
            f"AI patents ({patents.ai_patent_count}) add IP complexity"
        )

    # Patent trend
    if patents.filing_trend == "INCREASING":
        base += 0.5
        evidence.append("Increasing AI patent filing trend")

    # Regulatory mentions in disclosure
    if len(disclosure.risk_factors) >= 2:
        base += 0.5
        evidence.append("Multiple AI-related risk factors in SEC filings")

    return max(0.0, min(10.0, base)), evidence


def generate_ai_risk_narrative(
    assessment: AIRiskAssessment,
    industry_name: str,
) -> str:
    """Generate an industry-specific AI risk narrative.

    Creates a human-readable summary of the AI risk assessment
    suitable for inclusion in the underwriting worksheet.

    Args:
        assessment: The scored AI risk assessment.
        industry_name: Display name of the industry.

    Returns:
        Narrative text string.
    """
    score = assessment.overall_score

    # Determine risk band
    if score >= 70:
        risk_band = "high"
        risk_desc = "faces significant AI transformation risk"
    elif score >= 40:
        risk_band = "moderate"
        risk_desc = "faces moderate AI transformation risk"
    else:
        risk_band = "low"
        risk_desc = "faces limited AI transformation risk"

    # Find highest-scoring dimension
    highest_dim: AISubDimension | None = None
    for dim in assessment.sub_dimensions:
        if highest_dim is None or dim.score > highest_dim.score:
            highest_dim = dim

    highest_name = (
        highest_dim.dimension.replace("_", " ") if highest_dim else "unknown"
    )
    highest_score = highest_dim.score if highest_dim else 0.0

    # Build narrative
    parts: list[str] = [
        f"This {industry_name} company {risk_desc} "
        f"(composite score: {score:.0f}/100, {risk_band} risk band).",
    ]

    if highest_dim is not None and highest_score >= 6.0:
        parts.append(
            f" The primary exposure is in {highest_name} "
            f"(scored {highest_score:.1f}/10)."
        )

    # Data availability note
    if not assessment.data_sources:
        parts.append(
            " Note: Limited data available; scores reflect industry "
            "baseline priors rather than company-specific evidence."
        )
    elif assessment.peer_comparison_available:
        parts.append(" Peer comparison data is available for context.")

    return "".join(parts)
