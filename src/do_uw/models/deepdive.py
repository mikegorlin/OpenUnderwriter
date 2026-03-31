"""Deep-dive trigger result models.

Phase 110-01: Conditional deep-dive triggers that fire when compound
conditions are met, flagging areas for underwriter investigation.

Each trigger produces a DeepDiveTriggerResult with:
- Investigation prompt text for the underwriter
- Matched conditions that caused the trigger to fire
- Additional signals that should be flagged for review
- RAP dimension classification (host/agent/environment)
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class DeepDiveTriggerResult(BaseModel):
    """Result of evaluating a single deep-dive trigger."""

    model_config = ConfigDict(frozen=False)

    trigger_id: str = Field(
        ..., description="Trigger identifier (e.g. 'deepdive.financial_controls')"
    )
    trigger_name: str = Field(
        ..., description="Human-readable trigger name"
    )
    description: str = Field(
        default="", description="What this trigger detects"
    )
    fired: bool = Field(
        default=False, description="Whether all conditions were met"
    )
    matched_conditions: list[str] = Field(
        default_factory=list,
        description="Signal conditions that were satisfied",
    )
    additional_signals: list[str] = Field(
        default_factory=list,
        description="Additional signal IDs to flag for review",
    )
    uw_investigation_prompt: str = Field(
        default="",
        description="Investigation guidance text for the underwriter",
    )
    rap_dimensions: list[str] = Field(
        default_factory=list,
        description="H/A/E dimensions this trigger covers",
    )


class DeepDiveResult(BaseModel):
    """Aggregated result from all deep-dive trigger evaluations."""

    model_config = ConfigDict(frozen=False)

    triggers_evaluated: int = Field(
        default=0, description="Total triggers checked"
    )
    triggers_fired: int = Field(
        default=0, description="Triggers that fired (all conditions met)"
    )
    results: list[DeepDiveTriggerResult] = Field(
        default_factory=list,
        description="Individual trigger results",
    )
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When deep-dive evaluation was computed",
    )


__all__ = ["DeepDiveResult", "DeepDiveTriggerResult"]
