"""Forward-looking risk framework data models.

Provides Pydantic v2 models for:
- Forward statement extraction and miss risk assessment
- Management credibility scoring from guidance vs actuals
- Monitoring triggers for post-bind surveillance
- Underwriting posture recommendation from scoring tier
- Quick screen trigger matrix with nuclear trigger verification
- Catalyst events and growth estimates

These models are populated across EXTRACT, ANALYZE, and BENCHMARK stages
and consumed by RENDER for the forward-looking risk section of the worksheet.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ForwardStatement(BaseModel):
    """Single forward-looking claim extracted from SEC filings.

    Captures management guidance, targets, or projections from 10-K/8-K
    with miss risk assessment and SCA relevance mapping.
    """

    model_config = ConfigDict(frozen=False)

    metric_name: str = Field(default="", description="Metric being guided (revenue, EPS, margin, etc.)")
    current_value: str = Field(default="", description="Latest actual value as string for display")
    current_value_numeric: float | None = Field(default=None, description="For miss risk computation")
    guidance_claim: str = Field(default="", description="The forward-looking claim or target")
    guidance_midpoint: float | None = Field(default=None, description="Numeric midpoint for miss risk calc")
    guidance_type: str = Field(default="QUANTITATIVE", description="QUANTITATIVE or QUALITATIVE")
    miss_risk: str = Field(default="UNKNOWN", description="HIGH, MEDIUM, LOW, UNKNOWN")
    miss_risk_rationale: str = Field(default="", description="Why this miss risk level was assigned")
    sca_relevance: str = Field(default="", description="SCA theory if missed -- deterministic mapping")
    source_filing: str = Field(default="", description="10-K or 8-K accession number")
    source_date: str = Field(default="", description="Filing date YYYY-MM-DD")
    confidence: str = Field(default="MEDIUM", description="HIGH/MEDIUM/LOW per data integrity rules")


class CredibilityQuarter(BaseModel):
    """Single quarter guidance vs actual for credibility assessment."""

    model_config = ConfigDict(frozen=False)

    quarter: str = Field(default="", description="e.g. Q3 2025")
    metric: str = Field(default="", description="EPS, Revenue, etc.")
    guided_value: str = Field(default="", description="What management guided")
    actual_value: str = Field(default="", description="What was reported")
    beat_or_miss: str = Field(default="", description="BEAT, MISS, INLINE, UNKNOWN")
    magnitude_pct: float | None = Field(default=None, description="% above/below guidance")
    source: str = Field(default="", description="yfinance or 8-K accession")


class CredibilityScore(BaseModel):
    """Aggregate management credibility from historical guidance vs actuals.

    HIGH (>80% beat), MEDIUM (50-80%), LOW (<50%).
    """

    model_config = ConfigDict(frozen=False)

    beat_rate_pct: float = Field(default=0.0, description="Percentage of quarters beating guidance")
    quarters_assessed: int = Field(default=0, description="Number of quarters with guidance+actual data")
    credibility_level: str = Field(default="MEDIUM", description="HIGH >80%, MEDIUM 50-80%, LOW <50%")
    quarter_records: list[CredibilityQuarter] = Field(default_factory=list)
    source: str = Field(default="yfinance + 8-K LLM", description="Data source attribution")


class CatalystEvent(BaseModel):
    """Forward catalyst event that may affect D&O risk."""

    model_config = ConfigDict(frozen=False)

    event: str = Field(default="", description="The catalyst event")
    timing: str = Field(default="", description="When expected")
    impact_if_negative: str = Field(default="", description="Impact if outcome is negative")
    litigation_risk: str = Field(default="", description="HIGH/MEDIUM/LOW litigation exposure")
    source: str = Field(default="", description="Data source attribution")


class GrowthEstimate(BaseModel):
    """EPS/revenue estimate from analyst consensus or company guidance."""

    model_config = ConfigDict(frozen=False)

    period: str = Field(default="", description="Current Q, Current Y, Next Y")
    metric: str = Field(default="", description="EPS, Revenue")
    estimate: str = Field(default="", description="Display value")
    estimate_numeric: float | None = Field(default=None, description="Numeric value for computation")
    trend: str = Field(default="", description="UP, DOWN, FLAT")
    source: str = Field(default="yfinance", description="Data source attribution")


class MonitoringTrigger(BaseModel):
    """Post-bind surveillance trigger with company-specific threshold."""

    model_config = ConfigDict(frozen=False)

    trigger_name: str = Field(default="", description="Human-readable trigger name")
    action: str = Field(default="", description="Action to take when triggered")
    threshold: str = Field(default="", description="Company-specific threshold")
    current_value: str = Field(default="", description="Current value for reference")
    source: str = Field(default="", description="Data source for threshold computation")


class PostureElement(BaseModel):
    """Single element of the underwriting posture recommendation."""

    model_config = ConfigDict(frozen=False)

    element: str = Field(
        default="",
        description="decision, retention, limit, pricing, exclusions, monitoring, re_evaluation",
    )
    recommendation: str = Field(default="", description="Specific recommendation")
    rationale: str = Field(default="", description="Company-specific reasoning")


class PostureRecommendation(BaseModel):
    """Full underwriting posture derived from scoring tier + factor overrides."""

    model_config = ConfigDict(frozen=False)

    tier: str = Field(default="", description="Scoring tier driving base posture")
    elements: list[PostureElement] = Field(default_factory=list)
    overrides_applied: list[str] = Field(
        default_factory=list,
        description="Factor overrides applied, e.g. 'F.1>0: litigation exclusion added'",
    )


class NuclearTriggerCheck(BaseModel):
    """One of 5 nuclear triggers -- binary check demanding escalation if fired."""

    model_config = ConfigDict(frozen=False)

    trigger_id: str = Field(default="", description="NUC-01 through NUC-05")
    name: str = Field(default="", description="Human-readable trigger name")
    fired: bool = Field(default=False, description="Whether this nuclear trigger fired")
    evidence: str = Field(default="", description="Positive evidence for status")
    source: str = Field(default="", description="Data source for verification")


class WatchItem(BaseModel):
    """Item requiring ongoing underwriter attention."""

    model_config = ConfigDict(frozen=False)

    item: str = Field(default="", description="What to watch")
    current_state: str = Field(default="", description="Current status")
    threshold: str = Field(default="", description="When to act")
    re_evaluation: str = Field(default="", description="Review cadence")
    source: str = Field(default="", description="Data source attribution")


class TriggerMatrixRow(BaseModel):
    """Single row in the quick screen trigger matrix."""

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(default="", description="Brain signal ID")
    signal_name: str = Field(default="", description="Human-readable signal name")
    flag_level: str = Field(default="", description="RED or YELLOW")
    section: str = Field(default="", description="Worksheet section this maps to")
    section_anchor: str = Field(default="", description="HTML anchor for deep-dive link")
    do_context: str = Field(default="", description="D&O relevance explanation")


class ProspectiveCheck(BaseModel):
    """Forward-looking check with traffic light status."""

    model_config = ConfigDict(frozen=False)

    check_name: str = Field(default="", description="Check name")
    finding: str = Field(default="", description="What was found")
    status: str = Field(default="UNKNOWN", description="GREEN, YELLOW, RED, UNKNOWN")
    source: str = Field(default="", description="Data source attribution")


class QuickScreenResult(BaseModel):
    """Full quick screen: trigger matrix + nuclear triggers + prospective checks."""

    model_config = ConfigDict(frozen=False)

    trigger_matrix: list[TriggerMatrixRow] = Field(default_factory=list)
    nuclear_triggers: list[NuclearTriggerCheck] = Field(default_factory=list)
    nuclear_fired_count: int = Field(default=0, description="Number of nuclear triggers fired")
    prospective_checks: list[ProspectiveCheck] = Field(default_factory=list)
    red_count: int = Field(default=0, description="Total RED flags in trigger matrix")
    yellow_count: int = Field(default=0, description="Total YELLOW flags in trigger matrix")


class ForwardLookingData(BaseModel):
    """Container for all forward-looking risk analysis.

    Top-level on AnalysisState (not nested in ExtractedData) because
    forward-looking data spans extraction through benchmark stages.
    """

    model_config = ConfigDict(frozen=False)

    forward_statements: list[ForwardStatement] = Field(default_factory=list)
    credibility: CredibilityScore | None = Field(default=None)
    catalysts: list[CatalystEvent] = Field(default_factory=list)
    growth_estimates: list[GrowthEstimate] = Field(default_factory=list)
    monitoring_triggers: list[MonitoringTrigger] = Field(default_factory=list)
    posture: PostureRecommendation | None = Field(default=None)
    quick_screen: QuickScreenResult | None = Field(default=None)
    watch_items: list[WatchItem] = Field(default_factory=list)
    zero_verifications: list[dict[str, str]] = Field(
        default_factory=list,
        description="Factor zero-score verifications: [{factor_id, evidence, source}]",
    )
