"""Severity estimation Pydantic models (Phase 108).

Captures the complete severity computation result including damages
estimation, settlement regression, severity amplifiers, layer erosion,
and P x S zone classification. Used by the SeverityLens protocol.

SeverityResult is the top-level model stored on state.scoring.severity_result.
It holds both the primary (v7.0) and legacy severity lens results for
side-by-side comparison.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AmplifierResult",
    "LayerErosionResult",
    "ScenarioSeverity",
    "SeverityLensResult",
    "SeverityResult",
    "SeverityZone",
]


class SeverityZone(StrEnum):
    """P x S matrix zone classification.

    Zone boundaries from severity_model_design.yaml:
      GREEN:  P < 0.10 AND S < $10M
      YELLOW: P >= 0.10 OR S >= $10M (but not both high)
      ORANGE: (P >= 0.25 AND S >= $5M) OR P >= 0.35 OR S >= $50M
      RED:    P >= 0.35 AND S >= $50M
    """

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"

    @classmethod
    def zone_for(cls, probability: float, severity: float) -> SeverityZone:
        """Classify zone from probability and severity.

        Args:
            probability: Claim probability P in [0, 1].
            severity: Estimated settlement S in USD.

        Returns:
            SeverityZone classification.
        """
        # RED: P >= 0.35 AND S >= $50M
        if probability >= 0.35 and severity >= 50_000_000:
            return cls.RED

        # ORANGE: (P >= 0.25 AND S >= $5M) OR P >= 0.35 OR S >= $50M
        if (probability >= 0.25 and severity >= 5_000_000) or probability >= 0.35 or severity >= 50_000_000:
            return cls.ORANGE

        # YELLOW: P >= 0.10 OR S >= $10M
        if probability >= 0.10 or severity >= 10_000_000:
            return cls.YELLOW

        # GREEN: P < 0.10 AND S < $10M
        return cls.GREEN


class ScenarioSeverity(BaseModel):
    """Single severity scenario for an allegation type and drop level.

    Each scenario represents: "If allegation type X occurs with drop
    level Y, what is the estimated settlement?"
    """

    model_config = ConfigDict(frozen=False)

    allegation_type: str = Field(
        description="Allegation type (e.g. financial_restatement, guidance_miss)"
    )
    drop_level: str = Field(
        description="Drop level label (worst_actual, sector_median, catastrophic)"
    )
    base_damages: float = Field(
        default=0.0,
        description="Base damages estimate before modifiers (USD)",
    )
    settlement_estimate: float = Field(
        default=0.0,
        description="Settlement estimate after allegation modifier (USD)",
    )
    amplified_settlement: float = Field(
        default=0.0,
        description="Settlement after amplifier application (USD)",
    )
    defense_cost_estimate: float = Field(
        default=0.0,
        description="Estimated defense costs (USD)",
    )
    total_exposure: float = Field(
        default=0.0,
        description="Total exposure: amplified settlement + defense costs (USD)",
    )


class AmplifierResult(BaseModel):
    """Result of evaluating a single severity amplifier.

    Tracks whether the amplifier fired, its multiplier, which signals
    triggered it, and a human-readable explanation.
    """

    model_config = ConfigDict(frozen=False)

    amplifier_id: str = Field(description="Amplifier identifier")
    name: str = Field(description="Human-readable amplifier name")
    fired: bool = Field(
        default=False,
        description="Whether this amplifier was triggered",
    )
    multiplier: float = Field(
        default=1.0,
        description="Severity multiplier (1.0 if not fired)",
    )
    trigger_signals_matched: list[str] = Field(
        default_factory=list,
        description="Signal IDs that triggered this amplifier",
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation of firing or non-firing",
    )


class LayerErosionResult(BaseModel):
    """Per-layer severity estimate with penetration probability.

    For excess underwriters, the key question is: what is the probability
    that a claim reaches my layer, and how much of my layer would be
    consumed?
    """

    model_config = ConfigDict(frozen=False)

    attachment: float = Field(description="Layer attachment point (USD)")
    limit: float = Field(description="Layer limit (USD)")
    product: str = Field(
        description="Product type: ABC or SIDE_A"
    )
    penetration_probability: float = Field(
        description="P(settlement > attachment), 0-1"
    )
    liberty_severity: float = Field(
        description="max(0, settlement - attachment) capped by limit (USD)"
    )
    effective_expected_loss: float = Field(
        description="P_claim * P_erosion * liberty_severity (USD)"
    )


class SeverityLensResult(BaseModel):
    """Output from a severity lens evaluation.

    Contains the estimated settlement, damages breakdown, amplifier
    results, scenario table, defense costs, layer erosion details,
    zone classification, and metadata.
    """

    model_config = ConfigDict(frozen=False)

    lens_name: str = Field(description="Identifier for this severity lens")
    estimated_settlement: float = Field(
        description="Primary scenario point estimate (USD)"
    )
    damages_estimate: float = Field(
        description="Base damages estimate before modifiers (USD)"
    )
    amplifier_results: list[AmplifierResult] = Field(
        default_factory=list,
        description="Results from evaluating each severity amplifier",
    )
    scenarios: list[ScenarioSeverity] = Field(
        default_factory=list,
        description="Scenario table: allegation_type x drop_level",
    )
    defense_costs: float = Field(
        default=0.0,
        description="Estimated defense costs for primary scenario (USD)",
    )
    layer_erosion: list[LayerErosionResult] | None = Field(
        default=None,
        description="Per-layer erosion results (if attachment provided)",
    )
    zone: SeverityZone = Field(
        description="P x S zone classification"
    )
    confidence: str = Field(
        default="MEDIUM",
        description="Confidence level: HIGH, MEDIUM, LOW",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (allegation type, turnover rate, etc.)",
    )


class SeverityResult(BaseModel):
    """Top-level severity result stored on state.scoring.severity_result.

    Holds both the primary (v7.0) severity lens result and the legacy
    DDL model result for side-by-side comparison.
    """

    model_config = ConfigDict(frozen=False)

    primary: SeverityLensResult | None = Field(
        default=None,
        description="v7.0 severity lens result (primary, drives worksheet)",
    )
    legacy: SeverityLensResult | None = Field(
        default=None,
        description="Legacy DDL model wrapped as severity lens (comparison only)",
    )
    probability: float = Field(
        default=0.0,
        description="Claim probability P from H/A/E scoring",
    )
    severity: float = Field(
        default=0.0,
        description="Estimated settlement S (primary lens, USD)",
    )
    expected_loss: float = Field(
        default=0.0,
        description="Expected loss = P x S (USD)",
    )
    zone: SeverityZone = Field(
        default=SeverityZone.GREEN,
        description="P x S zone classification",
    )
    scenario_table: list[ScenarioSeverity] = Field(
        default_factory=list,
        description="Full scenario table from primary lens",
    )
