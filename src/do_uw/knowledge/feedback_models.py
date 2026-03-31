"""Pydantic models for feedback entries and change proposals.

Defines structured representations for:
- FeedbackEntry: human or automated feedback on a check result
- ProposalRecord: a proposed change to the brain knowledge base
- FeedbackSummary: dashboard-ready summary of pending feedback/proposals
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ReactionType(str, Enum):
    """Structured underwriter reaction to a triggered signal (Phase 51)."""

    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    ADJUST_SEVERITY = "ADJUST_SEVERITY"


class FeedbackEntry(BaseModel):
    """A feedback entry on a specific check result or coverage gap.

    Feedback types:
    - ACCURACY: check result was wrong (false positive/negative)
    - THRESHOLD: threshold is too sensitive or too loose
    - MISSING_COVERAGE: an important risk area has no check
    """

    feedback_id: int | None = None
    ticker: str | None = None
    signal_id: str | None = None
    run_id: str | None = None
    feedback_type: Literal["ACCURACY", "THRESHOLD", "MISSING_COVERAGE"]
    direction: Literal[
        "FALSE_POSITIVE", "FALSE_NEGATIVE", "TOO_SENSITIVE", "TOO_LOOSE"
    ] | None = None
    note: str
    reviewer: str = "anonymous"
    status: str = "PENDING"
    created_at: datetime | None = None


class FeedbackReaction(BaseModel):
    """A structured underwriter reaction to a triggered signal.

    Phase 51 reaction types:
    - AGREE: Signal correctly triggered -- no change needed
    - DISAGREE: Signal should not have triggered (false positive, irrelevant)
    - ADJUST_SEVERITY: Signal is relevant but severity level is wrong
    """

    feedback_id: int | None = None
    ticker: str
    signal_id: str
    run_id: str | None = None
    reaction_type: ReactionType
    severity_target: str | None = None
    """Target severity for ADJUST_SEVERITY (e.g., 'MEDIUM'). None for AGREE/DISAGREE."""
    rationale: str
    """Required: underwriter's reasoning for this reaction."""
    reviewer: str = "anonymous"
    status: str = "PENDING"
    created_at: datetime | None = None


class ProposalRecord(BaseModel):
    """A proposed change to the brain knowledge base.

    Proposal types:
    - NEW_CHECK: propose adding a new check
    - THRESHOLD_CHANGE: propose adjusting an existing check's threshold
    - DEACTIVATION: propose deactivating a check that is no longer useful
    - THRESHOLD_CALIBRATION: Phase 57 statistical drift calibration
    - CORRELATION_ANNOTATION: Phase 57 co-occurrence annotation
    - LIFECYCLE_TRANSITION: Phase 57 lifecycle state transition
    """

    proposal_id: int | None = None
    source_type: str
    """Origin of the proposal: INGESTION, FEEDBACK, PATTERN, CALIBRATION, CORRELATION_MINING."""
    source_ref: str | None = None
    signal_id: str | None = None
    proposal_type: Literal[
        "NEW_CHECK", "THRESHOLD_CHANGE", "DEACTIVATION",
        "THRESHOLD_CALIBRATION", "CORRELATION_ANNOTATION", "LIFECYCLE_TRANSITION",
    ]
    proposed_check: dict[str, Any] | None = None
    proposed_changes: dict[str, Any] | None = None
    backtest_results: dict[str, Any] | None = None
    rationale: str
    status: str = "PENDING"
    reviewed_by: str | None = None
    created_at: datetime | None = None


def _empty_feedback_list() -> list[FeedbackEntry]:
    return []


def _empty_proposal_list() -> list[ProposalRecord]:
    return []


class FeedbackSummary(BaseModel):
    """Dashboard-ready summary of pending feedback and proposals."""

    pending_accuracy: int
    pending_threshold: int
    pending_coverage_gaps: int
    pending_proposals: int
    recent_feedback: list[FeedbackEntry] = Field(
        default_factory=_empty_feedback_list,
    )
    recent_proposals: list[ProposalRecord] = Field(
        default_factory=_empty_proposal_list,
    )
