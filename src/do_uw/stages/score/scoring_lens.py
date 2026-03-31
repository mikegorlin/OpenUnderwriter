"""Scoring lens protocol and models for pluggable scoring engines.

Defines the ScoringLens Protocol (pluggable interface), HAETier enum
(5-tier decision tiers), ScoringLensResult (output model), and
CRFVetoResult (CRF ELECTRE discordance result).

First lens implementation: HAEScoringLens (hae_scoring.py).
Legacy 10-factor additive is wrapped as a second lens in future work.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

__all__ = [
    "CRFVetoResult",
    "HAETier",
    "ScoringLens",
    "ScoringLensResult",
]

# Tier ordering map for comparison operators
_TIER_ORDER: dict[str, int] = {
    "PREFERRED": 0,
    "STANDARD": 1,
    "ELEVATED": 2,
    "HIGH_RISK": 3,
    "PROHIBITED": 4,
}


class HAETier(StrEnum):
    """Five-tier decision tiers from decision_framework.yaml.

    Ordered: PREFERRED < STANDARD < ELEVATED < HIGH_RISK < PROHIBITED.
    Supports comparison operators for max() operations on tiers.
    """

    PREFERRED = "PREFERRED"
    STANDARD = "STANDARD"
    ELEVATED = "ELEVATED"
    HIGH_RISK = "HIGH_RISK"
    PROHIBITED = "PROHIBITED"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, HAETier):
            return NotImplemented
        return _TIER_ORDER[self.value] < _TIER_ORDER[other.value]

    def __le__(self, other: object) -> bool:
        if not isinstance(other, HAETier):
            return NotImplemented
        return _TIER_ORDER[self.value] <= _TIER_ORDER[other.value]

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, HAETier):
            return NotImplemented
        return _TIER_ORDER[self.value] > _TIER_ORDER[other.value]

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, HAETier):
            return NotImplemented
        return _TIER_ORDER[self.value] >= _TIER_ORDER[other.value]

    # Override __hash__ since we override __eq__ via StrEnum
    def __hash__(self) -> int:
        return hash(self.value)


class CRFVetoResult(BaseModel):
    """CRF ELECTRE discordance evaluation result.

    Each CRF veto is time-aware (recent/aging/expired) and
    claim-status-aware (NO_CLAIM/CLAIM_FILED/CLAIM_RESOLVED).
    """

    crf_id: str = Field(description="CRF identifier (e.g. CRF-FRAUD)")
    condition: str = Field(description="Human-readable CRF condition")
    veto_target: HAETier = Field(
        description="Minimum tier this CRF imposes when active"
    )
    signals_matched: list[str] = Field(
        default_factory=list,
        description="Signal IDs that triggered this CRF",
    )
    is_active: bool = Field(
        default=False,
        description="Whether this CRF veto is currently active",
    )
    time_context: str = Field(
        default="recent",
        description="Temporal context: recent, aging, or expired",
    )
    claim_status: str = Field(
        default="NO_CLAIM",
        description="Claim status: NO_CLAIM, CLAIM_FILED, or CLAIM_RESOLVED",
    )


class ScoringLensResult(BaseModel):
    """Output from a scoring lens evaluation.

    Contains tier assignment, composite scores, product score,
    recommendations, and CRF veto details.
    """

    lens_name: str = Field(description="Identifier for this scoring lens")
    tier: HAETier = Field(description="Final assigned tier")
    composites: dict[str, float] = Field(
        description="Composite scores by dimension (host, agent, environment)"
    )
    product_score: float = Field(
        description="Multiplicative product P = H x A x E"
    )
    confidence: str = Field(
        description="Confidence level: HIGH, MEDIUM, LOW"
    )
    recommendations: dict[str, str] = Field(
        default_factory=dict,
        description="Recommendation outputs by dimension (6 keys from decision_framework.yaml)",
    )
    crf_vetoes: list[CRFVetoResult] = Field(
        default_factory=list,
        description="CRF ELECTRE discordance results",
    )
    tier_source: str = Field(
        default="composite",
        description="How tier was determined: composite, individual, or crf_override",
    )
    individual_tier: HAETier | None = Field(
        default=None,
        description="Tier from individual dimension criteria",
    )
    composite_tier: HAETier | None = Field(
        default=None,
        description="Tier from composite P score range",
    )


@runtime_checkable
class ScoringLens(Protocol):
    """Protocol for pluggable scoring lenses.

    All scoring engines implement this interface to produce a
    ScoringLensResult from signal evaluation results.
    """

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
    ) -> ScoringLensResult: ...
