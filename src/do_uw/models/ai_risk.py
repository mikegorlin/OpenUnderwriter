"""AI Transformation Risk Factor models for SECT8 analysis.

Provides typed Pydantic models for:
- AI sub-dimension scoring (revenue displacement, cost structure, etc.)
- AI disclosure analysis from SEC filings
- AI patent activity tracking
- Peer-relative AI competitive positioning
- Complete AI risk assessment composite

All models support JSON round-trip serialization per CLAUDE.md patterns.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Sub-models: AI disclosure, patent, competitive position
# ---------------------------------------------------------------------------


class AIDisclosureData(BaseModel):
    """AI disclosure analysis from SEC filings.

    Parsed from Item 1A risk factors and other filing sections to quantify
    how the company frames AI as opportunity vs threat.
    """

    model_config = ConfigDict(frozen=False)

    mention_count: int = Field(
        default=0, description="Total AI keyword mentions in Item 1A"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Specific AI risk factors disclosed",
    )
    opportunity_mentions: int = Field(
        default=0, description="AI framed as opportunity"
    )
    threat_mentions: int = Field(
        default=0, description="AI framed as threat"
    )
    sentiment: str = Field(
        default="UNKNOWN",
        description="OPPORTUNITY, THREAT, BALANCED, or UNKNOWN",
    )
    yoy_trend: str = Field(
        default="UNKNOWN",
        description="INCREASING, STABLE, DECREASING, or UNKNOWN",
    )


class AIPatentActivity(BaseModel):
    """Patent filing analysis for AI-related activity.

    Tracks AI patent filings and trends as a proxy for competitive
    positioning and investment in AI capabilities.
    """

    model_config = ConfigDict(frozen=False)

    ai_patent_count: int = Field(
        default=0, description="Total AI-related patent count"
    )
    recent_filings: list[dict[str, str]] = Field(
        default_factory=lambda: [],
        description="List of {patent_number, filing_date, title}",
    )
    filing_trend: str = Field(
        default="UNKNOWN",
        description="INCREASING, STABLE, DECREASING, or UNKNOWN",
    )


class AICompetitivePosition(BaseModel):
    """Peer-relative AI positioning assessment.

    Compares the company's AI engagement level against peers
    using disclosure mentions and adoption signals.
    """

    model_config = ConfigDict(frozen=False)

    company_ai_mentions: int = Field(
        default=0, description="Company AI keyword mention count"
    )
    peer_avg_mentions: float = Field(
        default=0.0, description="Average peer AI mention count"
    )
    peer_mention_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Peer ticker to mention count mapping",
    )
    percentile_rank: float | None = Field(
        default=None,
        description="0-100 where 100 = most AI-forward",
    )
    adoption_stance: str = Field(
        default="UNKNOWN",
        description="LEADING, INLINE, LAGGING, or UNKNOWN",
    )


# ---------------------------------------------------------------------------
# Sub-dimension scoring
# ---------------------------------------------------------------------------


class AISubDimension(BaseModel):
    """A single AI risk sub-dimension score.

    Each of the 5 dimensions (revenue_displacement, cost_structure,
    competitive_moat, workforce_automation, regulatory_ip) is scored
    on a 0-10 scale with industry-specific weights.
    """

    model_config = ConfigDict(frozen=False)

    dimension: str = Field(
        description=(
            "One of: revenue_displacement, cost_structure, "
            "competitive_moat, workforce_automation, regulatory_ip"
        )
    )
    score: float = Field(description="Score on 0-10 scale")
    weight: float = Field(
        description="Industry-specific weight (0.0-1.0, sums to 1.0)"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence items",
    )
    threat_level: str = Field(
        default="UNKNOWN",
        description="HIGH, MEDIUM, LOW, or UNKNOWN",
    )


# ---------------------------------------------------------------------------
# Complete AI Risk Assessment
# ---------------------------------------------------------------------------


class AIRiskAssessment(BaseModel):
    """Complete SECT8 AI transformation risk output.

    The top-level model aggregating all AI risk sub-dimensions,
    disclosure analysis, patent activity, and competitive positioning
    into a single composite score (0-100).
    """

    model_config = ConfigDict(frozen=False)

    overall_score: float = Field(
        default=0.0, description="0-100 weighted composite score"
    )
    sub_dimensions: list[AISubDimension] = Field(
        default_factory=lambda: [],
        description="Scored sub-dimensions with weights and evidence",
    )
    disclosure_data: AIDisclosureData = Field(
        default_factory=AIDisclosureData
    )
    patent_activity: AIPatentActivity = Field(
        default_factory=AIPatentActivity
    )
    competitive_position: AICompetitivePosition = Field(
        default_factory=AICompetitivePosition
    )
    industry_model_id: str = Field(
        default="GENERIC",
        description="References AI impact model used for scoring",
    )
    disclosure_trend: str = Field(
        default="UNKNOWN",
        description="INCREASING, STABLE, DECREASING, or UNKNOWN",
    )
    narrative: str = Field(
        default="", description="Industry-specific risk narrative text"
    )
    narrative_source: str = Field(
        default="", description="Source attribution for narrative"
    )
    narrative_confidence: str = Field(
        default="LOW", description="Confidence level for narrative"
    )
    peer_comparison_available: bool = Field(
        default=False,
        description="Whether peer comparison data is available",
    )
    forward_indicators: list[str] = Field(
        default_factory=list,
        description="Forward-looking AI risk indicators",
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="What data sources contributed to this assessment",
    )
