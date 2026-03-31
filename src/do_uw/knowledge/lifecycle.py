"""Signal lifecycle state machine with history recording.

Manages the lifecycle of D&O underwriting signals through four states:
INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED

Each transition is validated against allowed state transitions and
recorded in the signal_history table with timestamp, actor, and reason.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from do_uw.knowledge.models import Check, CheckHistory


class SignalStatus(StrEnum):
    """Lifecycle status for underwriting checks.

    States:
        INCUBATING: Raw idea captured, not yet developed.
        DEVELOPING: Building data/eval/output chain.
        ACTIVE: Production-ready, executes in pipeline.
        DEPRECATED: Preserved but inactive.
    """

    INCUBATING = "INCUBATING"
    DEVELOPING = "DEVELOPING"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


VALID_TRANSITIONS: dict[SignalStatus, list[SignalStatus]] = {
    SignalStatus.INCUBATING: [SignalStatus.DEVELOPING, SignalStatus.DEPRECATED],
    SignalStatus.DEVELOPING: [
        SignalStatus.ACTIVE,
        SignalStatus.INCUBATING,
        SignalStatus.DEPRECATED,
    ],
    SignalStatus.ACTIVE: [SignalStatus.DEPRECATED],
    SignalStatus.DEPRECATED: [SignalStatus.DEVELOPING],
}


def validate_transition(
    from_status: SignalStatus, to_status: SignalStatus
) -> bool:
    """Check whether a lifecycle transition is allowed.

    Args:
        from_status: Current check status.
        to_status: Desired new status.

    Returns:
        True if the transition is valid, False otherwise.
    """
    allowed = VALID_TRANSITIONS.get(from_status, [])
    return to_status in allowed


def transition_signal(
    session: Session,
    signal_id: str,
    to_status: SignalStatus,
    changed_by: str,
    reason: str | None = None,
) -> None:
    """Transition a signal to a new lifecycle status.

    Validates the transition, updates the signal, and records
    the change in signal_history.

    Args:
        session: SQLAlchemy session.
        signal_id: ID of the check to transition.
        to_status: Desired new status.
        changed_by: Identity of who made the change.
        reason: Optional reason for the transition.

    Raises:
        ValueError: If the check is not found or the transition
            is invalid.
    """
    check = session.get(Check, signal_id)
    if check is None:
        msg = f"Check not found: {signal_id}"
        raise ValueError(msg)

    from_status = SignalStatus(check.status)
    if not validate_transition(from_status, to_status):
        msg = (
            f"Invalid transition for check {signal_id}: "
            f"{from_status.value} -> {to_status.value}"
        )
        raise ValueError(msg)

    now = datetime.now(UTC)
    old_status = check.status
    check.status = to_status.value
    check.modified_at = now
    check.version += 1

    history = CheckHistory(
        signal_id=signal_id,
        version=check.version,
        field_name="status",
        old_value=old_status,
        new_value=to_status.value,
        changed_at=now,
        changed_by=changed_by,
        reason=reason,
    )
    session.add(history)
    session.flush()


def record_field_change(
    session: Session,
    signal_id: str,
    field_name: str,
    old_value: str | None,
    new_value: str | None,
    changed_by: str,
    reason: str | None = None,
) -> None:
    """Record a generic field change on a check.

    Updates the check's modified_at and version, and inserts
    a history record for the change.

    Args:
        session: SQLAlchemy session.
        signal_id: ID of the check being modified.
        field_name: Name of the field that changed.
        old_value: Previous value (as string).
        new_value: New value (as string).
        changed_by: Identity of who made the change.
        reason: Optional reason for the change.

    Raises:
        ValueError: If the check is not found.
    """
    check = session.get(Check, signal_id)
    if check is None:
        msg = f"Check not found: {signal_id}"
        raise ValueError(msg)

    now = datetime.now(UTC)
    check.modified_at = now
    check.version += 1

    history = CheckHistory(
        signal_id=signal_id,
        version=check.version,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_at=now,
        changed_by=changed_by,
        reason=reason,
    )
    session.add(history)
    session.flush()
