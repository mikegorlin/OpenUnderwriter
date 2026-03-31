"""SECT7-04 through SECT7-10 scoring output models.

Split from scoring.py to stay under 500-line limit.
These models capture the detailed output of the SCORE stage
beyond factor scores and red flags.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------
# SECT7-04: Risk Type Classification
# -----------------------------------------------------------------------


class RiskType(StrEnum):
    """Primary D&O risk type for the company."""

    BINARY_EVENT = "BINARY_EVENT"
    GROWTH_DARLING = "GROWTH_DARLING"
    GUIDANCE_DEPENDENT = "GUIDANCE_DEPENDENT"
    REGULATORY_SENSITIVE = "REGULATORY_SENSITIVE"
    TRANSFORMATION = "TRANSFORMATION"
    STABLE_MATURE = "STABLE_MATURE"
    DISTRESSED = "DISTRESSED"


class RiskTypeClassification(BaseModel):
    """SECT7-04: Risk type classification output."""

    model_config = ConfigDict(frozen=False)

    primary: RiskType = Field(description="Primary risk type")
    secondary: RiskType | None = Field(
        default=None, description="Secondary risk type if applicable"
    )
    evidence: list[str] = Field(
        default_factory=lambda: [],
        description="Evidence supporting classification",
    )
    needs_calibration: bool = Field(
        default=True,
        description="Flagged per SECT7-11 for calibration review",
    )


# -----------------------------------------------------------------------
# SECT7-05: Allegation Theory Mapping
# -----------------------------------------------------------------------


class AllegationTheory(StrEnum):
    """D&O allegation theory categories."""

    A_DISCLOSURE = "A_DISCLOSURE"
    B_GUIDANCE = "B_GUIDANCE"
    C_PRODUCT_OPS = "C_PRODUCT_OPS"
    D_GOVERNANCE = "D_GOVERNANCE"
    E_MA = "E_MA"


class TheoryExposure(BaseModel):
    """Exposure level for a single allegation theory."""

    model_config = ConfigDict(frozen=False)

    theory: AllegationTheory = Field(description="Allegation theory")
    exposure_level: str = Field(
        description="Exposure level: HIGH, MODERATE, or LOW"
    )
    findings: list[str] = Field(
        default_factory=lambda: [],
        description="Evidence findings for this theory",
    )
    factor_sources: list[str] = Field(
        default_factory=lambda: [],
        description="Factor IDs contributing (e.g. F1, F3)",
    )


class AllegationMapping(BaseModel):
    """SECT7-05: Allegation theory mapping output."""

    model_config = ConfigDict(frozen=False)

    theories: list[TheoryExposure] = Field(
        default_factory=lambda: [],
        description="Exposure by allegation theory",
    )
    primary_exposure: AllegationTheory = Field(
        description="Highest-exposure allegation theory"
    )
    concentration_analysis: str = Field(
        default="",
        description="Narrative on exposure concentration",
    )
    needs_calibration: bool = Field(
        default=True,
        description="Flagged per SECT7-11 for calibration review",
    )


# -----------------------------------------------------------------------
# SECT7-07: Claim Probability
# -----------------------------------------------------------------------


class ProbabilityBand(StrEnum):
    """Claim probability classification band."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ClaimProbability(BaseModel):
    """SECT7-07: Claim probability estimation output."""

    model_config = ConfigDict(frozen=False)

    band: ProbabilityBand = Field(
        description="Probability classification band"
    )
    range_low_pct: float = Field(
        description="Low end of probability range (%)"
    )
    range_high_pct: float = Field(
        description="High end of probability range (%)"
    )
    industry_base_rate_pct: float = Field(
        default=0.0,
        description="Industry baseline claim rate (%)",
    )
    adjustment_narrative: str = Field(
        default="",
        description="Narrative explaining adjustments from base rate",
    )
    needs_calibration: bool = Field(
        default=True,
        description="Flagged per SECT7-11 for calibration review",
    )


# -----------------------------------------------------------------------
# SECT7-08: Severity Scenarios
# -----------------------------------------------------------------------


class SeverityScenario(BaseModel):
    """Single severity scenario at a given percentile."""

    model_config = ConfigDict(frozen=False)

    percentile: int = Field(
        description="Scenario percentile: 25, 50, 75, or 95"
    )
    label: str = Field(
        description="Scenario label: favorable, median, adverse, catastrophic"
    )
    ddl_amount: float = Field(
        default=0.0,
        description="Damages, disgorgement, and losses (USD)",
    )
    settlement_estimate: float = Field(
        default=0.0, description="Expected settlement amount (USD)"
    )
    defense_cost_estimate: float = Field(
        default=0.0, description="Expected defense costs (USD)"
    )
    total_exposure: float = Field(
        default=0.0, description="Total exposure (USD)"
    )


class SeverityScenarios(BaseModel):
    """SECT7-08: Severity scenario analysis output."""

    model_config = ConfigDict(frozen=False)

    market_cap: float = Field(
        default=0.0, description="Market cap used for calculations"
    )
    decline_scenarios: dict[str, float] = Field(
        default_factory=dict,
        description="Decline scenarios: '10%', '20%', '30%' -> DDL amount",
    )
    scenarios: list[SeverityScenario] = Field(
        default_factory=lambda: [],
        description="Percentile-based severity scenarios",
    )
    needs_calibration: bool = Field(
        default=True,
        description="Flagged per SECT7-11 for calibration review",
    )


# -----------------------------------------------------------------------
# SECT7-09: Tower Recommendation
# -----------------------------------------------------------------------


class TowerPosition(StrEnum):
    """Insurance tower position recommendation."""

    PRIMARY = "PRIMARY"
    LOW_EXCESS = "LOW_EXCESS"
    MID_EXCESS = "MID_EXCESS"
    HIGH_EXCESS = "HIGH_EXCESS"
    DECLINE = "DECLINE"


class LayerAssessment(BaseModel):
    """Assessment for a single tower layer."""

    model_config = ConfigDict(frozen=False)

    position: TowerPosition = Field(description="Tower layer position")
    risk_assessment: str = Field(
        default="", description="Risk assessment narrative"
    )
    premium_guidance: str = Field(
        default="", description="Premium guidance for this layer"
    )
    attachment_range: str = Field(
        default="", description="Attachment point range"
    )


class TowerRecommendation(BaseModel):
    """SECT7-09: Tower position recommendation output."""

    model_config = ConfigDict(frozen=False)

    recommended_position: TowerPosition = Field(
        description="Recommended tower position"
    )
    minimum_attachment: str = Field(
        default="", description="Minimum attachment point"
    )
    layers: list[LayerAssessment] = Field(
        default_factory=lambda: [],
        description="Per-layer assessments",
    )
    side_a_assessment: str = Field(
        default="", description="Side A/DIC assessment narrative"
    )
    needs_calibration: bool = Field(
        default=True,
        description="Flagged per SECT7-11 for calibration review",
    )


# -----------------------------------------------------------------------
# SECT7-10: Red Flag Summary
# -----------------------------------------------------------------------


class FlagSeverity(StrEnum):
    """Red flag severity classification."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class FlaggedItem(BaseModel):
    """Individual flagged risk item for underwriter summary."""

    model_config = ConfigDict(frozen=False)

    description: str = Field(description="Human-readable flag description")
    source: str = Field(description="Data source for this flag")
    severity: FlagSeverity = Field(description="Severity classification")
    scoring_impact: str = Field(
        default="", description="Impact on scoring (e.g. 'F1: +20 points')"
    )
    allegation_theory: str = Field(
        default="",
        description="Related allegation theory (A-E)",
    )
    trajectory: str = Field(
        default="STABLE",
        description="Trajectory: NEW, WORSENING, STABLE, or IMPROVING",
    )


class RedFlagSummary(BaseModel):
    """SECT7-10: Red flag summary for underwriter review."""

    model_config = ConfigDict(frozen=False)

    items: list[FlaggedItem] = Field(
        default_factory=lambda: [],
        description="All flagged items",
    )
    critical_count: int = Field(
        default=0, description="Count of CRITICAL severity items"
    )
    high_count: int = Field(
        default=0, description="Count of HIGH severity items"
    )
    moderate_count: int = Field(
        default=0, description="Count of MODERATE severity items"
    )
    low_count: int = Field(
        default=0, description="Count of LOW severity items"
    )


# -----------------------------------------------------------------------
# Actuarial Pricing Models (Phase 12)
# -----------------------------------------------------------------------


class ScenarioLoss(BaseModel):
    """Expected loss at a single percentile scenario."""

    model_config = ConfigDict(frozen=False)

    percentile: int = Field(description="Scenario percentile (25, 50, 75, 95)")
    label: str = Field(description="Scenario label (favorable, median, adverse, catastrophic)")
    expected_indemnity: float = Field(
        default=0.0, description="Expected indemnity loss at this percentile (USD)"
    )
    expected_defense: float = Field(
        default=0.0, description="Expected defense costs at this percentile (USD)"
    )
    total_expected: float = Field(
        default=0.0, description="Total expected loss (indemnity + defense) (USD)"
    )


class ExpectedLoss(BaseModel):
    """Full expected loss breakdown from frequency-severity model."""

    model_config = ConfigDict(frozen=False)

    has_data: bool = Field(
        default=False, description="Whether sufficient data was available"
    )
    filing_probability_pct: float = Field(
        default=0.0, description="Filing probability used (percentage)"
    )
    median_severity: float = Field(
        default=0.0, description="Median (50th pct) severity used (USD)"
    )
    defense_cost_pct: float = Field(
        default=0.0, description="Defense cost percentage applied"
    )
    expected_indemnity: float = Field(
        default=0.0, description="Expected indemnity = prob * median_severity (USD)"
    )
    expected_defense: float = Field(
        default=0.0, description="Expected defense = expected_indemnity * defense_pct (USD)"
    )
    total_expected_loss: float = Field(
        default=0.0, description="Total expected loss = indemnity + defense (USD)"
    )
    scenario_losses: list[ScenarioLoss] = Field(
        default_factory=lambda: [],
        description="Expected losses at each percentile scenario",
    )
    methodology_note: str = Field(
        default="", description="Model methodology and calibration note"
    )


class LayerSpec(BaseModel):
    """Tower layer definition for pricing."""

    model_config = ConfigDict(frozen=False)

    layer_type: str = Field(description="Layer type (primary, low_excess, etc.)")
    layer_number: int = Field(description="Layer position in tower (1-based)")
    attachment: float = Field(description="Attachment point (USD)")
    limit: float = Field(description="Layer limit (USD)")


class LayerPricing(BaseModel):
    """Pricing result for a single tower layer."""

    model_config = ConfigDict(frozen=False)

    layer_type: str = Field(description="Layer type (primary, low_excess, etc.)")
    layer_number: int = Field(description="Layer position in tower (1-based)")
    attachment: float = Field(description="Attachment point (USD)")
    limit: float = Field(description="Layer limit (USD)")
    ilf_factor: float = Field(
        default=0.0, description="Increased limit factor for this layer"
    )
    expected_loss: float = Field(
        default=0.0, description="Expected loss for this layer (USD)"
    )
    target_loss_ratio: float = Field(
        default=0.0, description="Target loss ratio for premium derivation"
    )
    indicated_premium: float = Field(
        default=0.0, description="Model-indicated premium (USD)"
    )
    indicated_rol: float = Field(
        default=0.0, description="Model-indicated rate on line"
    )
    confidence_note: str = Field(
        default="", description="Confidence/calibration note for this layer"
    )


class CalibratedPricing(BaseModel):
    """Market-calibrated pricing result blending model and market."""

    model_config = ConfigDict(frozen=False)

    model_indicated_premium: float = Field(
        default=0.0, description="Model-indicated premium before calibration (USD)"
    )
    model_indicated_rol: float = Field(
        default=0.0, description="Model-indicated rate on line"
    )
    market_median_rol: float | None = Field(
        default=None, description="Market median rate on line (if available)"
    )
    credibility: float = Field(
        default=0.0, description="Credibility weight given to model vs market"
    )
    calibrated_rol: float = Field(
        default=0.0, description="Credibility-weighted rate on line"
    )
    calibrated_premium: float = Field(
        default=0.0, description="Credibility-weighted premium (USD)"
    )
    calibration_source: str = Field(
        default="", description="Source of market calibration data"
    )


class ActuarialPricing(BaseModel):
    """Root container for all actuarial pricing output."""

    model_config = ConfigDict(frozen=False)

    has_data: bool = Field(
        default=False, description="Whether actuarial model produced results"
    )
    expected_loss: ExpectedLoss | None = Field(
        default=None, description="Expected loss computation"
    )
    layer_pricing: list[LayerPricing] = Field(
        default_factory=lambda: [],
        description="Per-layer pricing results",
    )
    calibrated_primary: CalibratedPricing | None = Field(
        default=None, description="Market-calibrated primary layer pricing"
    )
    total_indicated_premium: float = Field(
        default=0.0, description="Sum of indicated premiums across tower (USD)"
    )
    tower_structure_used: str = Field(
        default="", description="Description of tower structure used"
    )
    methodology_note: str = Field(
        default="MODEL-INDICATED: Not prescriptive. Underwriter sets final price.",
        description="Methodology and disclaimer note",
    )
    assumptions: list[str] = Field(
        default_factory=lambda: [],
        description="Key assumptions used in pricing model",
    )
