"""Scoring and benchmark models -- SCORE/BENCHMARK stage output.

Captures the 10-factor scoring result, red flag detections, tier
classification, composite pattern matches, and peer benchmarking.
Populated during SCORE stage (Phase 6) and BENCHMARK stage (Phase 7).

SECT7-04 through SECT7-10 output models are in scoring_output.py
(split to stay under 500-line limit) and re-exported here.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.executive_summary import InherentRiskBaseline

if TYPE_CHECKING:
    from do_uw.models.adversarial import AdversarialResult
    from do_uw.models.deepdive import DeepDiveResult
    from do_uw.models.patterns import PatternEngineResult
    from do_uw.models.severity import SeverityResult
    from do_uw.stages.score.scoring_lens import ScoringLensResult

# Re-export SECT7-04 through SECT7-10 output models
from do_uw.models.scoring_output import (
    ActuarialPricing,
    AllegationMapping,
    AllegationTheory,
    CalibratedPricing,
    ClaimProbability,
    ExpectedLoss,
    FlaggedItem,
    FlagSeverity,
    LayerAssessment,
    LayerPricing,
    LayerSpec,
    ProbabilityBand,
    RedFlagSummary,
    RiskType,
    RiskTypeClassification,
    ScenarioLoss,
    SeverityScenario,
    SeverityScenarios,
    TheoryExposure,
    TowerPosition,
    TowerRecommendation,
)


class Tier(StrEnum):
    """Underwriting tier classification (W-series).

    Higher quality score = better tier.
    WIN (86-100) through NO_TOUCH (0-10).
    """

    WIN = "WIN"
    WANT = "WANT"
    WRITE = "WRITE"
    WATCH = "WATCH"
    WALK = "WALK"
    NO_TOUCH = "NO_TOUCH"


class FactorScore(BaseModel):
    """Individual scoring factor result (F1-F10).

    Each factor deducts points from a 100-point quality score.
    Factor definitions are in brain/scoring.json.
    """

    model_config = ConfigDict(frozen=False)

    factor_name: str = Field(description="Human-readable factor name")
    factor_id: str = Field(
        description="Factor identifier: F1 through F10"
    )
    max_points: int = Field(
        description="Maximum points this factor can deduct"
    )
    points_deducted: float = Field(
        default=0.0, description="Actual points deducted"
    )
    evidence: list[str] = Field(
        default_factory=lambda: [],
        description="Evidence supporting the deduction",
    )
    rules_triggered: list[str] = Field(
        default_factory=lambda: [],
        description="Rule IDs that triggered (e.g. F1-001, F2-003)",
    )
    sub_components: dict[str, float] = Field(
        default_factory=dict,
        description="Sub-component breakdown (e.g. base, multiplier, bonus)",
    )
    signal_contributions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Signals that contributed to this factor with weights and severity",
    )
    signal_coverage: float = Field(
        default=0.0,
        description="Fraction of factor signals evaluated (0.0-1.0)",
    )
    scoring_method: str = Field(
        default="rule_based",
        description="Scoring method used: 'signal_driven' or 'rule_based'",
    )


class TierClassification(BaseModel):
    """Tier assignment with score boundaries.

    Tier boundaries are defined in brain/scoring.json under 'tiers'.
    """

    model_config = ConfigDict(frozen=False)

    tier: Tier = Field(description="Assigned underwriting tier")
    score_range_low: int = Field(
        description="Low end of tier score range"
    )
    score_range_high: int = Field(
        description="High end of tier score range"
    )
    probability_range: str = Field(
        default="", description="Claim probability range for this tier"
    )
    pricing_multiplier: str = Field(
        default="", description="Pricing guidance for this tier"
    )
    action: str = Field(
        default="", description="Underwriting action guidance"
    )


class RedFlagResult(BaseModel):
    """Critical red flag evaluation result.

    Red flags impose quality score CEILINGS regardless of factor scores.
    Definitions are in brain/red_flags.json.
    """

    model_config = ConfigDict(frozen=False)

    flag_id: str = Field(description="Red flag ID (e.g. CRF-01)")
    flag_name: str = Field(
        default="", description="Human-readable flag name"
    )
    triggered: bool = Field(
        default=False, description="Whether this red flag fired"
    )
    ceiling_applied: int | None = Field(
        default=None,
        description="Quality score ceiling imposed (e.g. 30, 50)",
    )
    max_tier: str | None = Field(
        default=None,
        description="Maximum tier allowed when triggered",
    )
    evidence: list[str] = Field(
        default_factory=lambda: [],
        description="Evidence supporting the trigger",
    )


class PatternMatch(BaseModel):
    """Composite pattern detection result.

    Pattern definitions are in brain/patterns.json.
    """

    model_config = ConfigDict(frozen=False)

    pattern_id: str = Field(
        description="Pattern ID (e.g. PATTERN.STOCK.EVENT_COLLAPSE)"
    )
    pattern_name: str = Field(
        default="", description="Human-readable pattern name"
    )
    detected: bool = Field(
        default=False, description="Whether pattern was detected"
    )
    severity: str = Field(
        default="BASELINE",
        description="Severity level: BASELINE, ELEVATED, HIGH, SEVERE",
    )
    triggers_matched: list[str] = Field(
        default_factory=lambda: [],
        description="Which trigger conditions were matched",
    )
    score_impact: dict[str, float] = Field(
        default_factory=dict,
        description="Points added per factor (e.g. {'F2': 3, 'F9': 2})",
    )


# -----------------------------------------------------------------------
# Aggregated Scoring Result (updated with SECT7-04 through SECT7-10)
# -----------------------------------------------------------------------


class ScoringResult(BaseModel):
    """Complete scoring output from SCORE stage.

    The composite_score is the final quality score after all factors,
    patterns, and red flag ceilings are applied.
    """

    model_config = ConfigDict(frozen=False)

    composite_score: float = Field(
        default=100.0,
        description="Final quality score: 100 - total_risk_points",
    )
    quality_score: float = Field(
        default=100.0,
        description=(
            "Quality score after red flag ceilings: "
            "MIN(composite_score, lowest_ceiling)"
        ),
    )
    total_risk_points: float = Field(
        default=0.0, description="Sum of all factor point deductions"
    )
    factor_scores: list[FactorScore] = Field(
        default_factory=lambda: [],
        description="Individual factor scores (F1-F10)",
    )
    red_flags: list[RedFlagResult] = Field(
        default_factory=lambda: [],
        description="Critical red flag evaluation results",
    )
    tier: TierClassification | None = Field(
        default=None, description="Assigned tier with boundaries"
    )
    patterns_detected: list[PatternMatch] = Field(
        default_factory=lambda: [],
        description="Composite patterns that fired",
    )

    # SECT7-04 through SECT7-10 output fields (populated in 06-03/06-04)
    risk_type: RiskTypeClassification | None = Field(
        default=None, description="SECT7-04: Risk type classification"
    )
    allegation_mapping: AllegationMapping | None = Field(
        default=None,
        description="SECT7-05: Allegation theory mapping",
    )
    claim_probability: ClaimProbability | None = Field(
        default=None, description="SECT7-07: Claim probability estimation"
    )
    severity_scenarios: SeverityScenarios | None = Field(
        default=None, description="SECT7-08: Severity scenario analysis"
    )
    tower_recommendation: TowerRecommendation | None = Field(
        default=None,
        description="SECT7-09: Tower position recommendation",
    )
    red_flag_summary: RedFlagSummary | None = Field(
        default=None, description="SECT7-10: Red flag summary"
    )
    calibration_notes: list[str] = Field(
        default_factory=lambda: [],
        description="NEEDS CALIBRATION items per SECT7-11",
    )
    binding_ceiling_id: str | None = Field(
        default=None, description="CRF ID of the binding ceiling"
    )
    ceiling_details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-CRF ceiling resolution details (size-conditioned, weighted)",
    )
    actuarial_pricing: ActuarialPricing | None = Field(
        default=None, description="Actuarial loss model output"
    )
    hae_result: ScoringLensResult | None = Field(
        default=None,
        description="H/A/E multiplicative scoring lens result",
    )
    severity_result: SeverityResult | None = Field(
        default=None,
        description="v7.0 severity model result (damages, settlement, amplifiers)",
    )
    pattern_engine_result: PatternEngineResult | None = Field(
        default=None,
        description="v7.0 pattern engine results (conjunction, outlier, drift, precedent)",
    )
    deepdive_result: DeepDiveResult | None = Field(
        default=None,
        description="v7.0 deep-dive trigger results (Phase 110)",
    )
    adversarial_result: AdversarialResult | None = Field(
        default=None,
        description="v7.0 adversarial critique result (caveats, devil's advocate)",
    )


class FramesPercentileResult(BaseModel):
    """Per-metric percentile from SEC Frames API.

    Provides true cross-filer percentile ranking computed from
    ~5,000-10,000 SEC EDGAR filers per metric.
    """

    model_config = ConfigDict(frozen=False)

    overall: float | None = Field(
        default=None, description="Percentile vs ALL filers",
    )
    sector: float | None = Field(
        default=None, description="Percentile vs same-SIC filers",
    )
    peer_count_overall: int = Field(
        default=0, description="Number of filers in overall ranking",
    )
    peer_count_sector: int = Field(
        default=0, description="Number of filers in sector ranking",
    )
    company_value: float | None = Field(
        default=None, description="Company's value for this metric",
    )
    higher_is_better: bool = Field(
        default=True, description="Whether higher values are favorable",
    )


class MetricBenchmark(BaseModel):
    """Structured benchmark result for a single metric.

    Holds the company value, percentile rank, peer count, and
    sector baseline for display in the BENCHMARK section.
    """

    model_config = ConfigDict(frozen=False)

    metric_name: str = Field(description="Human-readable metric name")
    company_value: float | None = Field(
        default=None, description="Company's value for this metric"
    )
    percentile_rank: float | None = Field(
        default=None,
        description="Percentile rank 0-100 within peer/sector group",
    )
    peer_count: int = Field(
        default=0, description="Number of peers with data for this metric"
    )
    baseline_value: float | None = Field(
        default=None,
        description="Sector baseline value from sectors.json",
    )
    higher_is_better: bool = Field(
        default=True,
        description="Whether higher values are favorable",
    )
    section: str = Field(
        default="",
        description="Which worksheet section this metric belongs to",
    )


class BenchmarkResult(BaseModel):
    """Peer benchmarking output from BENCHMARK stage.

    Compares the subject company against a peer group across key metrics.
    """

    model_config = ConfigDict(frozen=False)

    peer_group_tickers: list[str] = Field(
        default_factory=lambda: [],
        description="Tickers in the peer comparison group",
    )
    peer_rankings: dict[str, float] = Field(
        default_factory=dict,
        description="Metric -> percentile rank within peer group",
    )
    peer_quality_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Peer ticker -> quality score for comparison",
    )
    sector_average_score: float | None = Field(
        default=None,
        description="Average quality score for the sector",
    )
    relative_position: str | None = Field(
        default=None,
        description=(
            "Position vs peers: BEST_IN_CLASS, ABOVE_AVERAGE, "
            "AVERAGE, BELOW_AVERAGE, WORST_IN_CLASS"
        ),
    )
    metric_details: dict[str, MetricBenchmark] = Field(
        default_factory=dict,
        description="Structured per-metric benchmark info",
    )
    frames_percentiles: dict[str, FramesPercentileResult] = Field(
        default_factory=dict,
        description="Per-metric Frames API percentile results",
    )
    inherent_risk: InherentRiskBaseline | None = Field(
        default=None,
        description="Computed inherent risk baseline (also on ExecutiveSummary)",
    )

    # Phase 29: Pre-computed narratives (computed in BENCHMARK stage)
    # RENDER reads these strings directly, never generates them.
    thesis_narrative: str | None = Field(
        default=None,
        description="Pre-computed underwriting thesis (4-6 sentences)",
    )
    risk_narrative: str | None = Field(
        default=None,
        description="Pre-computed risk assessment narrative",
    )
    risk_level: str | None = Field(
        default=None,
        description="Pre-computed risk level label from score",
    )
    claim_narrative: str | None = Field(
        default=None,
        description="Pre-computed claim probability context narrative",
    )


def _rebuild_scoring_models() -> None:
    """Rebuild ScoringResult to resolve forward refs.

    Resolves ScoringLensResult, SeverityResult, PatternEngineResult,
    DeepDiveResult, and AdversarialResult forward references. Must be
    called after the relevant modules are importable. Safe to call
    multiple times (Pydantic no-ops if already resolved).
    """
    from do_uw.models.adversarial import AdversarialResult as _AR
    from do_uw.models.deepdive import DeepDiveResult as _DDR
    from do_uw.models.patterns import PatternEngineResult as _PER
    from do_uw.models.severity import SeverityResult as _SR
    from do_uw.stages.score.scoring_lens import ScoringLensResult as _SLR

    ScoringResult.model_rebuild(
        _types_namespace={
            "ScoringLensResult": _SLR,
            "SeverityResult": _SR,
            "PatternEngineResult": _PER,
            "DeepDiveResult": _DDR,
            "AdversarialResult": _AR,
        },
    )


# Re-export everything for convenient access
__all__: list[str] = [
    "ActuarialPricing",
    "AdversarialResult",
    "DeepDiveResult",
    "AllegationMapping",
    "AllegationTheory",
    "BenchmarkResult",
    "CalibratedPricing",
    "ClaimProbability",
    "ExpectedLoss",
    "FactorScore",
    "FlagSeverity",
    "FramesPercentileResult",
    "FlaggedItem",
    "InherentRiskBaseline",
    "LayerAssessment",
    "LayerPricing",
    "LayerSpec",
    "MetricBenchmark",
    "PatternEngineResult",
    "PatternMatch",
    "ProbabilityBand",
    "RedFlagResult",
    "RedFlagSummary",
    "RiskType",
    "RiskTypeClassification",
    "ScenarioLoss",
    "ScoringLensResult",
    "ScoringResult",
    "SeverityResult",
    "SeverityScenario",
    "SeverityScenarios",
    "TheoryExposure",
    "Tier",
    "TierClassification",
    "TowerPosition",
    "TowerRecommendation",
]
