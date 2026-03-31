"""Provenance tracking and audit trail utilities for checks.

Provides functions to query the modification history of checks,
generate provenance summaries, compute migration statistics, and
retrieve deprecation logs. Every check modification is auditable
with who, when, what changed, and why.

Relies on the CheckHistory table populated by lifecycle.py's
transition_signal() and record_field_change() functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from do_uw.knowledge.models import Check, CheckHistory
from do_uw.knowledge.store import KnowledgeStore


def _empty_entry_list() -> list[ProvenanceEntry]:
    """Return empty list of ProvenanceEntry (pyright strict)."""
    return []


@dataclass
class ProvenanceEntry:
    """A single modification record for a check.

    Attributes:
        version: Version number after this change.
        field_name: Name of the field that changed.
        old_value: Previous value (as string), or None for creation.
        new_value: New value (as string), or None for deletion.
        changed_at: When the change occurred.
        changed_by: Identity of who made the change.
        reason: Optional reason for the change.
    """

    version: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime
    changed_by: str
    reason: str | None


@dataclass
class ProvenanceSummary:
    """At-a-glance provenance summary for a check.

    Attributes:
        signal_id: The check being summarized.
        signal_name: Human-readable check name.
        origin: How the check was created (BRAIN_MIGRATION, USER_ADDED,
            AI_GENERATED).
        created_at: When the check was first created.
        current_version: Current version number.
        total_modifications: Total number of history entries.
        status_transitions: History entries for status changes only.
        recent_changes: Last 10 changes (any field).
    """

    signal_id: str
    signal_name: str
    origin: str
    created_at: datetime
    current_version: int
    total_modifications: int
    status_transitions: list[ProvenanceEntry] = field(
        default_factory=_empty_entry_list
    )
    recent_changes: list[ProvenanceEntry] = field(
        default_factory=_empty_entry_list
    )


def _history_to_entry(h: CheckHistory) -> ProvenanceEntry:
    """Convert a CheckHistory ORM object to a ProvenanceEntry."""
    return ProvenanceEntry(
        version=h.version,
        field_name=h.field_name,
        old_value=h.old_value,
        new_value=h.new_value,
        changed_at=h.changed_at,
        changed_by=h.changed_by,
        reason=h.reason,
    )


def get_signal_history(
    store: KnowledgeStore,
    signal_id: str,
) -> list[ProvenanceEntry]:
    """Get the full modification history for a check.

    Returns all history entries sorted by version ascending
    (oldest first).

    Args:
        store: KnowledgeStore instance.
        signal_id: ID of the check to query.

    Returns:
        List of ProvenanceEntry in chronological order.
        Empty list if the check has no history.
    """
    with store.get_session() as session:
        stmt = (
            select(CheckHistory)
            .where(CheckHistory.signal_id == signal_id)
            .order_by(CheckHistory.version)
        )
        rows = list(session.execute(stmt).scalars().all())
        return [_history_to_entry(h) for h in rows]


def get_provenance_summary(
    store: KnowledgeStore,
    signal_id: str,
) -> ProvenanceSummary:
    """Get a provenance summary for a check.

    Combines check metadata with modification history to produce
    an at-a-glance view of the check's lifecycle.

    Args:
        store: KnowledgeStore instance.
        signal_id: ID of the check to summarize.

    Returns:
        ProvenanceSummary with lifecycle information.

    Raises:
        ValueError: If the check is not found.
    """
    with store.get_session() as session:
        check = session.get(Check, signal_id)
        if check is None:
            msg = f"Check not found: {signal_id}"
            raise ValueError(msg)

        # Get full history
        stmt = (
            select(CheckHistory)
            .where(CheckHistory.signal_id == signal_id)
            .order_by(CheckHistory.version)
        )
        history_rows = list(session.execute(stmt).scalars().all())
        all_entries = [_history_to_entry(h) for h in history_rows]

        # Filter for status transitions
        status_transitions = [
            e for e in all_entries if e.field_name == "status"
        ]

        # Recent changes: last 10
        recent_changes = all_entries[-10:] if all_entries else []

        return ProvenanceSummary(
            signal_id=check.id,
            signal_name=check.name,
            origin=check.origin,
            created_at=check.created_at,
            current_version=check.version,
            total_modifications=len(all_entries),
            status_transitions=status_transitions,
            recent_changes=recent_changes,
        )


def get_migration_stats(
    store: KnowledgeStore,
) -> dict[str, Any]:
    """Get statistics about the knowledge store population.

    Counts checks by origin and status, and totals history entries.
    Useful for understanding the composition and activity of the
    knowledge store.

    Args:
        store: KnowledgeStore instance.

    Returns:
        Dict with keys: by_origin, by_status, total_signals,
        total_history_entries.
    """
    with store.get_session() as session:
        # Count checks by origin
        origin_stmt = (
            select(
                Check.origin,
                func.count(Check.id),
            )
            .group_by(Check.origin)
        )
        origin_rows = list(session.execute(origin_stmt).all())
        by_origin: dict[str, int] = {
            str(row[0]): int(row[1]) for row in origin_rows
        }

        # Count checks by status
        status_stmt = (
            select(
                Check.status,
                func.count(Check.id),
            )
            .group_by(Check.status)
        )
        status_rows = list(session.execute(status_stmt).all())
        by_status: dict[str, int] = {
            str(row[0]): int(row[1]) for row in status_rows
        }

        # Total checks
        total_signals_result = session.execute(
            select(func.count(Check.id))
        ).scalar()
        total_signals = int(total_signals_result) if total_signals_result else 0

        # Total history entries
        total_history_result = session.execute(
            select(func.count(CheckHistory.id))
        ).scalar()
        total_history = (
            int(total_history_result) if total_history_result else 0
        )

    return {
        "by_origin": by_origin,
        "by_status": by_status,
        "total_signals": total_signals,
        "total_history_entries": total_history,
    }


def get_deprecation_log(
    store: KnowledgeStore,
) -> list[dict[str, Any]]:
    """Get a log of all deprecated checks with reasons.

    Finds all DEPRECATED checks and includes the history entry
    for when the status changed to DEPRECATED (including the reason).

    Args:
        store: KnowledgeStore instance.

    Returns:
        List of dicts sorted by deprecation date, each containing:
        signal_id, signal_name, deprecated_at, deprecated_by, reason.
    """
    with store.get_session() as session:
        # Find all deprecated checks
        dep_stmt = select(Check).where(Check.status == "DEPRECATED")
        deprecated_checks = list(
            session.execute(dep_stmt).scalars().all()
        )

        result: list[dict[str, Any]] = []
        for check in deprecated_checks:
            # Find the history entry for the DEPRECATED transition
            hist_stmt = (
                select(CheckHistory)
                .where(CheckHistory.signal_id == check.id)
                .where(CheckHistory.field_name == "status")
                .where(CheckHistory.new_value == "DEPRECATED")
                .order_by(CheckHistory.version.desc())
                .limit(1)
            )
            hist_row = session.execute(hist_stmt).scalars().first()

            entry: dict[str, Any] = {
                "signal_id": check.id,
                "signal_name": check.name,
            }
            if hist_row is not None:
                entry["deprecated_at"] = hist_row.changed_at
                entry["deprecated_by"] = hist_row.changed_by
                entry["reason"] = hist_row.reason
            else:
                entry["deprecated_at"] = check.modified_at
                entry["deprecated_by"] = "unknown"
                entry["reason"] = None

            result.append(entry)

        # Sort by deprecation date
        result.sort(
            key=lambda r: r.get(
                "deprecated_at", datetime(2000, 1, 1, tzinfo=UTC)
            )
        )
        return result
