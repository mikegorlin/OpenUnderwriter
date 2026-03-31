"""Adversarial critique models -- Devil's Advocate caveats.

Phase 110-02: Captures false positive, false negative, contradiction,
and data completeness caveats that challenge the scoring recommendation.
Caveats are informational only -- they NEVER modify scores or tiers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Caveat(BaseModel):
    """A single adversarial caveat challenging a scoring finding.

    Each caveat identifies a potential weakness in the analysis:
    - false_positive: A triggered signal that may be over-counted
    - false_negative: A risk the system may be missing
    - contradiction: Conflicting signals suggesting incomplete picture
    - data_completeness: Missing data that weakens conclusions
    """

    model_config = ConfigDict(frozen=False)

    caveat_type: Literal[
        "false_positive", "false_negative", "contradiction", "data_completeness"
    ]
    target_signal_id: str = Field(
        default="",
        description="Signal this caveat concerns (empty for general caveats)",
    )
    headline: str = Field(
        description="One-sentence summary of the caveat",
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation (LLM-generated or template fallback)",
    )
    confidence: float = Field(
        default=0.0,
        description="0.0-1.0 how confident the caveat is valid",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence strings",
    )
    severity: Literal["info", "caution", "warning"] = Field(
        default="info",
        description="Caveat severity level",
    )
    narrative_source: Literal["llm", "template"] = Field(
        default="template",
        description="Whether LLM or template generated the explanation",
    )


class AdversarialResult(BaseModel):
    """Aggregated adversarial critique result from all 4 check types.

    Informational overlay -- does NOT modify any scoring fields.
    """

    model_config = ConfigDict(frozen=False)

    caveats: list[Caveat] = Field(
        default_factory=list,
        description="All detected caveats across 4 check types",
    )
    false_positive_count: int = Field(
        default=0,
        description="Number of false positive caveats",
    )
    false_negative_count: int = Field(
        default=0,
        description="Number of false negative (blind spot) caveats",
    )
    contradiction_count: int = Field(
        default=0,
        description="Number of contradiction caveats",
    )
    completeness_issues: int = Field(
        default=0,
        description="Number of data completeness caveats",
    )
    summary: str = Field(
        default="",
        description="Overall confidence assessment narrative (LLM-generated)",
    )
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When adversarial critique was computed",
    )


__all__ = ["AdversarialResult", "Caveat"]
