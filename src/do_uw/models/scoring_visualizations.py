"""Pydantic models for scoring visualization charts.

Data contracts for waterfall (score factor buildup), tornado (scenario
sensitivity), radar enhancement (threshold rings), and risk clustering.
These models are consumed by chart renderers in stages/render/charts/.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProbabilityComponent(BaseModel):
    """Single component in a filing probability decomposition.

    Each component contributes to the overall claim probability,
    either as a base rate or an adjustment (increase/decrease).
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(description="Component name (e.g., 'Base Rate', 'Restatement Boost')")
    value_pct: float = Field(
        description="Percentage contribution. Use safe_float() when populating from state/LLM."
    )
    direction: Literal["base", "increase", "decrease"] = Field(
        description="Whether this is base rate, upward adjustment, or downward adjustment"
    )
    is_calibrated: bool = Field(
        default=False,
        description="True if backed by actuarial/NERA data, False if estimated",
    )
    source: str = Field(
        default="",
        description="Data source for this component (e.g., 'NERA 2024', 'model estimate')",
    )
    running_total_pct: float = Field(
        default=0.0,
        description="Cumulative probability after this component. Use safe_float() when populating.",
    )


class ScenarioFactorDelta(BaseModel):
    """Change to a single scoring factor under a hypothetical scenario.

    Captures what-if: if this factor's score changed, how would the
    overall quality score and tier be affected?
    """

    model_config = ConfigDict(frozen=False)

    factor_id: str = Field(description="Factor identifier (F1-F10)")
    factor_name: str = Field(description="Human-readable factor name")
    current_points: float = Field(
        description="Current points deducted. Use safe_float() when populating."
    )
    scenario_points: float = Field(
        description="Points deducted under scenario. Use safe_float() when populating."
    )
    max_points: float = Field(
        description="Maximum possible deduction for this factor."
    )


class ScoreScenario(BaseModel):
    """A what-if scenario showing score sensitivity to factor changes.

    Each scenario represents a hypothetical situation (e.g., 'restatement
    announced', 'SCA filed') and its impact on the quality score and tier.
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(description="Scenario identifier (e.g., 'WORST', 'BEST')")
    name: str = Field(description="Human-readable scenario name")
    description: str = Field(
        default="", description="Brief description of the scenario"
    )
    factor_deltas: list[ScenarioFactorDelta] = Field(
        default_factory=list,
        description="Per-factor changes under this scenario",
    )
    current_score: float = Field(
        description="Current quality score before scenario. Use safe_float()."
    )
    scenario_score: float = Field(
        description="Quality score under scenario. Use safe_float()."
    )
    current_tier: str = Field(default="", description="Current tier label")
    scenario_tier: str = Field(default="", description="Tier under scenario")
    score_delta: float = Field(
        default=0.0,
        description="Score change (scenario_score - current_score). Use safe_float().",
    )
    probability_impact: float = Field(
        default=0.0,
        description="Change in filing probability (percentage points). Use safe_float().",
    )


class RiskCluster(BaseModel):
    """Group of related scoring factors that concentrate risk.

    Identifies when multiple factors in the same risk domain are firing
    together, indicating concentrated rather than diversified risk.
    """

    model_config = ConfigDict(frozen=False)

    name: str = Field(description="Cluster name (e.g., 'Financial Integrity')")
    factor_ids: list[str] = Field(
        description="Factor IDs in this cluster (e.g., ['F1', 'F3', 'F5'])"
    )
    total_points: float = Field(
        default=0.0,
        description="Sum of points deducted by factors in this cluster. Use safe_float().",
    )
    pct_of_total: float = Field(
        default=0.0,
        description="Fraction of total risk points from this cluster (0.0-1.0).",
    )
    is_dominant: bool = Field(
        default=False,
        description="True if this cluster accounts for >50% of total risk points.",
    )


__all__ = [
    "ProbabilityComponent",
    "RiskCluster",
    "ScenarioFactorDelta",
    "ScoreScenario",
]
