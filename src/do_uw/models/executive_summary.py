"""Executive Summary models -- SECT1 output for the final worksheet.

Captures the top-level summary that underwriters read first:
- SECT1-01: CompanySnapshot (identity + key metrics)
- SECT1-02: InherentRiskBaseline (actuarial filing probability)
- SECT1-03/04: KeyFindings (negatives + positives)
- SECT1-07: DealContext (layer, premium, carrier)
- UnderwritingThesis (narrative synthesis)

SECT1-05 (ClaimProbability) and SECT1-06 (TowerRecommendation) already
exist on ScoringResult and are referenced directly from state.scoring.

Populated during BENCHMARK stage (Phase 7) and RENDER stage (Phase 8).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue

# -----------------------------------------------------------------------
# SECT1-01: Company Snapshot
# -----------------------------------------------------------------------


class CompanySnapshot(BaseModel):
    """Top-line company identification and key metrics.

    Populated from CompanyProfile and ExtractedFinancials during
    BENCHMARK stage. Provides the "at a glance" view for underwriters.
    """

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Legal entity name")
    market_cap: SourcedValue[float] | None = Field(
        default=None, description="Market capitalization in USD"
    )
    revenue: SourcedValue[float] | None = Field(
        default=None, description="Most recent annual revenue in USD"
    )
    employee_count: SourcedValue[int] | None = Field(
        default=None, description="Total employees"
    )
    industry: str = Field(
        default="", description="Industry classification"
    )
    sic_code: str = Field(
        default="", description="SIC code"
    )
    exchange: str = Field(
        default="", description="Primary exchange (NYSE, NASDAQ, etc.)"
    )


# -----------------------------------------------------------------------
# SECT1-02: Inherent Risk Baseline
# -----------------------------------------------------------------------


class InherentRiskBaseline(BaseModel):
    """Actuarial inherent risk baseline for the company.

    Computed via multiplicative adjustment:
    company_adjusted_rate = sector_base_rate * cap_multiplier * score_multiplier

    Severity ranges from scoring.json by_market_cap tiers.
    All values marked NEEDS CALIBRATION per SECT7-11.
    """

    model_config = ConfigDict(frozen=False)

    sector_base_rate_pct: float = Field(
        description="Annual SCA filing probability (%) from sectors.json"
    )
    market_cap_multiplier: float = Field(
        description="Filing rate multiplier by market cap tier"
    )
    market_cap_adjusted_rate_pct: float = Field(
        description="base_rate * cap_multiplier"
    )
    score_multiplier: float = Field(
        description="Quality score adjustment multiplier"
    )
    company_adjusted_rate_pct: float = Field(
        description="Final adjusted filing probability (%)"
    )
    severity_range_25th: float = Field(
        default=0.0,
        description="25th percentile settlement estimate (USD millions)",
    )
    severity_range_50th: float = Field(
        default=0.0,
        description="50th percentile settlement estimate (USD millions)",
    )
    severity_range_75th: float = Field(
        default=0.0,
        description="75th percentile settlement estimate (USD millions)",
    )
    severity_range_95th: float = Field(
        default=0.0,
        description="95th percentile settlement estimate (USD millions)",
    )
    sector_name: str = Field(
        default="", description="Human-readable sector name"
    )
    market_cap_tier: str = Field(
        default="", description="Market cap tier: MEGA, LARGE, MID, SMALL, MICRO"
    )
    methodology_note: str = Field(
        default="NEEDS CALIBRATION",
        description="Calibration status per SECT7-11",
    )


# -----------------------------------------------------------------------
# SECT1-03/04: Key Findings
# -----------------------------------------------------------------------


class KeyFinding(BaseModel):
    """Individual key finding for underwriter review.

    Can be negative (risk signal) or positive (mitigating factor).
    Ranked by scoring_impact for prioritization.
    """

    model_config = ConfigDict(frozen=False)

    evidence_narrative: str = Field(
        description="Human-readable description of the finding"
    )
    section_origin: str = Field(
        description="Which section (SECT2-SECT7) this originated from"
    )
    scoring_impact: str = Field(
        description="Points and factor impact (e.g. 'F1: +20 points')"
    )
    theory_mapping: str = Field(
        description="Allegation or defense theory (e.g. 'Theory A: Disclosure')"
    )
    ranking_score: float = Field(
        default=0.0,
        description="Numeric score for sorting (internal, not displayed)",
    )


def _default_findings_list() -> list[KeyFinding]:
    """Default factory for key findings lists."""
    return []


class KeyFindings(BaseModel):
    """Aggregated key findings: top negatives and top positives.

    Negatives are the biggest risk drivers. Positives are mitigating
    factors. Both sorted by ranking_score descending.
    """

    model_config = ConfigDict(frozen=False)

    negatives: list[KeyFinding] = Field(
        default_factory=_default_findings_list,
        description="Top negative risk findings (descending impact)",
    )
    positives: list[KeyFinding] = Field(
        default_factory=_default_findings_list,
        description="Top positive mitigating findings (descending impact)",
    )


# -----------------------------------------------------------------------
# Market Intelligence
# -----------------------------------------------------------------------


class MarketIntelligence(BaseModel):
    """Market pricing intelligence from accumulated quote data.

    Populated during BENCHMARK stage when pricing data exists in the
    knowledge store. Non-breaking when no data is available (has_data=False).
    """

    model_config = ConfigDict(frozen=False)

    has_data: bool = Field(
        default=False, description="Whether pricing data exists"
    )
    peer_count: int = Field(
        default=0, description="Number of comparable quotes"
    )
    confidence_level: str = Field(
        default="INSUFFICIENT", description="Data confidence"
    )
    median_rate_on_line: float | None = Field(
        default=None, description="Median ROL for peer segment"
    )
    ci_low: float | None = Field(
        default=None, description="95% CI lower bound"
    )
    ci_high: float | None = Field(
        default=None, description="95% CI upper bound"
    )
    trend_direction: str = Field(
        default="INSUFFICIENT_DATA",
        description="HARDENING/SOFTENING/STABLE/INSUFFICIENT_DATA",
    )
    trend_magnitude_pct: float | None = Field(
        default=None, description="Trend magnitude percentage"
    )
    mispricing_alert: str | None = Field(
        default=None, description="Alert if >15% deviation from median"
    )
    model_vs_market_alert: str | None = Field(
        default=None,
        description="Alert if model-indicated pricing diverges >20% from market",
    )
    data_window: str = Field(
        default="", description="Date range of pricing data"
    )
    segment_label: str = Field(
        default="", description="e.g., 'LARGE / TECH'"
    )


# -----------------------------------------------------------------------
# SECT1-07: Deal Context
# -----------------------------------------------------------------------


class DealContext(BaseModel):
    """Deal-specific context for the underwriting worksheet.

    Placeholder fields for layer, premium, carrier information.
    Populated from user input or broker submission in RENDER stage.
    """

    model_config = ConfigDict(frozen=False)

    layer_quoted: str = Field(
        default="", description="Layer being quoted (e.g. '$10M xs $10M')"
    )
    premium: str = Field(
        default="", description="Premium indication or range"
    )
    carrier_lineup: str = Field(
        default="", description="Known carriers in the tower"
    )
    tower_structure: str = Field(
        default="", description="Full tower structure description"
    )
    additional_notes: str = Field(
        default="", description="Broker or submission notes"
    )
    is_placeholder: bool = Field(
        default=True,
        description="True if deal context is not yet populated",
    )
    market_intelligence: MarketIntelligence | None = Field(
        default=None,
        description="Market pricing intelligence from accumulated quote data",
    )


# -----------------------------------------------------------------------
# Underwriting Thesis
# -----------------------------------------------------------------------


class UnderwritingThesis(BaseModel):
    """Synthesized underwriting thesis narrative.

    A 2-3 sentence summary of the risk profile, combining the risk
    type classification, top scoring factors, and recommended action.
    """

    model_config = ConfigDict(frozen=False)

    narrative: str = Field(
        default="",
        description="2-3 sentence underwriting thesis",
    )
    risk_type_label: str = Field(
        default="",
        description="Human-readable risk type label",
    )
    top_factor_summary: str = Field(
        default="",
        description="Summary of top scoring factors",
    )


# -----------------------------------------------------------------------
# Root Executive Summary Container
# -----------------------------------------------------------------------


class ExecutiveSummary(BaseModel):
    """Root container for the Executive Summary section (SECT1).

    Populated progressively:
    - BENCHMARK stage: snapshot (SECT1-01) + inherent_risk (SECT1-02)
    - Plan 07-02: key_findings (SECT1-03/04) + thesis
    - RENDER stage: deal_context (SECT1-07) from user input

    SECT1-05 (ClaimProbability) and SECT1-06 (TowerRecommendation) are
    on ScoringResult -- not duplicated here.
    """

    model_config = ConfigDict(frozen=False)

    snapshot: CompanySnapshot | None = Field(
        default=None,
        description="SECT1-01: Company identification and key metrics",
    )
    inherent_risk: InherentRiskBaseline | None = Field(
        default=None,
        description="SECT1-02: Actuarial inherent risk baseline",
    )
    key_findings: KeyFindings | None = Field(
        default=None,
        description="SECT1-03/04: Top negative and positive findings",
    )
    thesis: UnderwritingThesis | None = Field(
        default=None,
        description="Underwriting thesis narrative synthesis",
    )
    deal_context: DealContext = Field(
        default_factory=DealContext,
        description="SECT1-07: Deal-specific context (placeholder until populated)",
    )


__all__: list[str] = [
    "CompanySnapshot",
    "DealContext",
    "ExecutiveSummary",
    "InherentRiskBaseline",
    "KeyFinding",
    "KeyFindings",
    "MarketIntelligence",
    "UnderwritingThesis",
]
