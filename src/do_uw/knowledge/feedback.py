"""Feedback recording, querying, and auto-proposal generation.

Records underwriter feedback on check accuracy, threshold sensitivity,
and missing coverage gaps. MISSING_COVERAGE feedback auto-generates
INCUBATING check proposals via BrainWriter.

Functions:
    record_feedback: Insert feedback entry into brain_feedback table
    get_feedback_summary: Dashboard-ready summary of pending items
    get_feedback_for_check: All feedback for a specific signal_id
    mark_feedback_applied: Mark feedback as applied after calibration
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, cast

import duckdb

from do_uw.knowledge.feedback_models import (
    FeedbackEntry,
    FeedbackSummary,
    ProposalRecord,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_feedback(
    conn: duckdb.DuckDBPyConnection,
    entry: FeedbackEntry,
) -> int:
    """Record a feedback entry in brain_feedback table.

    If feedback_type is MISSING_COVERAGE, also auto-proposes an
    INCUBATING check definition via _auto_propose_check().

    Args:
        conn: DuckDB connection with brain schema.
        entry: Feedback entry to record.

    Returns:
        feedback_id of the inserted row.
    """
    conn.execute(
        """INSERT INTO brain_feedback
           (ticker, signal_id, run_id, feedback_type, direction,
            note, reviewer, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            entry.ticker,
            entry.signal_id,
            entry.run_id,
            entry.feedback_type,
            entry.direction,
            entry.note,
            entry.reviewer,
            entry.status,
        ],
    )

    # Retrieve the auto-generated feedback_id
    result = conn.execute(
        "SELECT MAX(feedback_id) FROM brain_feedback"
    ).fetchone()
    feedback_id: int = result[0] if result else 0

    logger.info(
        "Recorded %s feedback (ID: %d) for %s/%s by %s",
        entry.feedback_type,
        feedback_id,
        entry.ticker or "N/A",
        entry.signal_id or "N/A",
        entry.reviewer,
    )

    # Auto-propose check for missing coverage
    if entry.feedback_type == "MISSING_COVERAGE":
        entry_with_id = entry.model_copy(update={"feedback_id": feedback_id})
        proposal_id = _auto_propose_check(conn, entry_with_id)
        if proposal_id is not None:
            logger.info(
                "Auto-proposed INCUBATING check (proposal_id: %d) from feedback %d",
                proposal_id,
                feedback_id,
            )

    return feedback_id


def record_reaction(
    conn: duckdb.DuckDBPyConnection,
    reaction: "FeedbackReaction",
) -> int:
    """Record a structured underwriter reaction in brain_feedback.

    Uses the new reaction columns (reaction_type, severity_target,
    reaction_rationale) alongside the legacy columns. The legacy
    feedback_type is set to 'REACTION' to distinguish from old entries.
    The note column gets the rationale for backward compat with summary queries.

    Args:
        conn: DuckDB connection with brain schema.
        reaction: Structured reaction to record.

    Returns:
        feedback_id of the inserted row.
    """
    from do_uw.knowledge.feedback_models import FeedbackReaction  # noqa: F811

    conn.execute(
        """INSERT INTO brain_feedback
           (ticker, signal_id, run_id, feedback_type, note, reviewer, status,
            reaction_type, severity_target, reaction_rationale)
           VALUES (?, ?, ?, 'REACTION', ?, ?, 'PENDING', ?, ?, ?)""",
        [
            reaction.ticker,
            reaction.signal_id,
            reaction.run_id,
            reaction.rationale,  # note = rationale for backward compat
            reaction.reviewer,
            reaction.reaction_type.value,
            reaction.severity_target,
            reaction.rationale,
        ],
    )

    result = conn.execute(
        "SELECT MAX(feedback_id) FROM brain_feedback"
    ).fetchone()
    feedback_id: int = result[0] if result else 0

    logger.info(
        "Recorded %s reaction (ID: %d) for %s/%s by %s",
        reaction.reaction_type.value,
        feedback_id,
        reaction.ticker,
        reaction.signal_id,
        reaction.reviewer,
    )

    return feedback_id


def get_reactions_for_signal(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> list["FeedbackReaction"]:
    """Get all Phase 51 reactions for a specific signal_id.

    Only returns entries where reaction_type IS NOT NULL (excludes legacy feedback).
    """
    from do_uw.knowledge.feedback_models import FeedbackReaction, ReactionType

    rows = conn.execute(
        """SELECT feedback_id, ticker, signal_id, run_id,
                  reaction_type, severity_target, reaction_rationale,
                  reviewer, status, created_at
           FROM brain_feedback
           WHERE signal_id = ? AND reaction_type IS NOT NULL
           ORDER BY created_at DESC""",
        [signal_id],
    ).fetchall()

    results: list[FeedbackReaction] = []
    for row in rows:
        results.append(FeedbackReaction(
            feedback_id=row[0],
            ticker=row[1],
            signal_id=row[2],
            run_id=row[3],
            reaction_type=ReactionType(row[4]),
            severity_target=row[5],
            rationale=row[6] or "",
            reviewer=row[7],
            status=row[8],
            created_at=row[9],
        ))

    return results


def get_pending_reactions(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, list["FeedbackReaction"]]:
    """Get all PENDING reactions grouped by signal_id.

    Returns dict mapping signal_id -> list of reactions, for proposal generation.
    """
    from do_uw.knowledge.feedback_models import FeedbackReaction, ReactionType

    rows = conn.execute(
        """SELECT feedback_id, ticker, signal_id, run_id,
                  reaction_type, severity_target, reaction_rationale,
                  reviewer, status, created_at
           FROM brain_feedback
           WHERE reaction_type IS NOT NULL AND status = 'PENDING'
           ORDER BY signal_id, created_at""",
    ).fetchall()

    grouped: dict[str, list[FeedbackReaction]] = {}
    for row in rows:
        reaction = FeedbackReaction(
            feedback_id=row[0],
            ticker=row[1],
            signal_id=row[2],
            run_id=row[3],
            reaction_type=ReactionType(row[4]),
            severity_target=row[5],
            rationale=row[6] or "",
            reviewer=row[7],
            status=row[8],
            created_at=row[9],
        )
        grouped.setdefault(reaction.signal_id, []).append(reaction)

    return grouped


def get_feedback_summary(
    conn: duckdb.DuckDBPyConnection,
) -> FeedbackSummary:
    """Build dashboard-ready summary of pending feedback and proposals.

    Queries brain_feedback for counts by type/status, brain_proposals
    for pending proposal count, and returns the 10 most recent entries
    of each.

    Args:
        conn: DuckDB connection with brain schema.

    Returns:
        FeedbackSummary with counts and recent items.
    """
    # Counts by type where PENDING
    pending_accuracy = _count_feedback(conn, "ACCURACY")
    pending_threshold = _count_feedback(conn, "THRESHOLD")
    pending_coverage_gaps = _count_feedback(conn, "MISSING_COVERAGE")

    # Pending proposals
    result = conn.execute(
        "SELECT COUNT(*) FROM brain_proposals WHERE status = 'PENDING'"
    ).fetchone()
    pending_proposals: int = result[0] if result else 0

    # Recent feedback (last 10)
    recent_feedback = _recent_feedback(conn, limit=10)

    # Recent proposals (last 10)
    recent_proposals = _recent_proposals(conn, limit=10)

    return FeedbackSummary(
        pending_accuracy=pending_accuracy,
        pending_threshold=pending_threshold,
        pending_coverage_gaps=pending_coverage_gaps,
        pending_proposals=pending_proposals,
        recent_feedback=recent_feedback,
        recent_proposals=recent_proposals,
    )


def get_feedback_for_check(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> list[FeedbackEntry]:
    """Retrieve all feedback for a specific signal_id.

    Args:
        conn: DuckDB connection with brain schema.
        signal_id: The check to query feedback for.

    Returns:
        List of FeedbackEntry, newest first.
    """
    rows = conn.execute(
        """SELECT feedback_id, ticker, signal_id, run_id,
                  feedback_type, direction, note, reviewer,
                  status, created_at
           FROM brain_feedback
           WHERE signal_id = ?
           ORDER BY created_at DESC""",
        [signal_id],
    ).fetchall()

    return [row_to_feedback_entry(row) for row in rows]


def mark_feedback_applied(
    conn: duckdb.DuckDBPyConnection,
    feedback_id: int,
    change_id: int,
) -> None:
    """Mark a feedback entry as applied after a calibration change.

    Updates status to APPLIED and records the change_id that
    addressed this feedback.

    Args:
        conn: DuckDB connection with brain schema.
        feedback_id: The feedback to mark applied.
        change_id: The changelog/change ID that addressed it.
    """
    conn.execute(
        """UPDATE brain_feedback
           SET status = 'APPLIED',
               applied_at = current_timestamp,
               applied_change_id = ?
           WHERE feedback_id = ?""",
        [change_id, feedback_id],
    )

    logger.info(
        "Marked feedback %d as APPLIED (change_id: %d)",
        feedback_id,
        change_id,
    )


# ---------------------------------------------------------------------------
# Auto-proposal for MISSING_COVERAGE
# ---------------------------------------------------------------------------


def _auto_propose_check(
    conn: duckdb.DuckDBPyConnection,
    entry: FeedbackEntry,
) -> int | None:
    """Auto-generate an INCUBATING check proposal from missing coverage feedback.

    Creates both a proposal record in brain_proposals and an INCUBATING
    check in brain_signals (invisible to pipeline until promoted).

    Args:
        conn: DuckDB connection with brain schema.
        entry: The MISSING_COVERAGE feedback entry (must have feedback_id set).

    Returns:
        proposal_id if successful, None if auto-proposal fails.
    """
    try:
        # Generate a signal_id from the note keywords
        signal_id = _derive_signal_id(entry.note)
        signal_name = entry.note[:80]
        rationale = f"Proposed from underwriter feedback by {entry.reviewer}"

        # Build skeleton check dict
        proposed_check: dict[str, Any] = {
            "signal_id": signal_id,
            "name": signal_name,
            "content_type": "EVALUATIVE_CHECK",
            "lifecycle_state": "INCUBATING",
            "threshold_type": "boolean",
            "question": entry.note,
            "rationale": rationale,
            "report_section": "company",
            "risk_questions": [],
            "risk_framework_layer": "risk_modifier",
        }

        # Insert proposal into brain_proposals
        conn.execute(
            """INSERT INTO brain_proposals
               (source_type, source_ref, signal_id, proposal_type,
                proposed_check, rationale, status)
               VALUES (?, ?, ?, ?, ?, ?, 'PENDING')""",
            [
                "FEEDBACK",
                f"feedback_{entry.feedback_id}",
                signal_id,
                "NEW_CHECK",
                json.dumps(proposed_check),
                rationale,
            ],
        )

        result = conn.execute(
            "SELECT MAX(proposal_id) FROM brain_proposals"
        ).fetchone()
        proposal_id: int = result[0] if result else 0

        # Insert INCUBATING check via BrainWriter (lazy import)
        from do_uw.brain.brain_writer import BrainWriter

        writer = BrainWriter(db_path=":memory:")
        writer._conn = conn  # pyright: ignore[reportPrivateUsage]  # reuse existing connection
        try:
            writer.insert_check(
                signal_id,
                proposed_check,
                reason=rationale,
                created_by=f"feedback_{entry.feedback_id}",
            )
        except ValueError:
            # Check already exists -- not an error for auto-proposal
            logger.warning(
                "Auto-proposal check %s already exists, skipping insert",
                signal_id,
            )

        return proposal_id

    except Exception:
        logger.exception("Auto-proposal failed for feedback %s", entry.feedback_id)
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _derive_signal_id(note: str) -> str:
    """Derive a signal_id from feedback note keywords.

    Takes the first 2-3 significant words from the note and constructs
    an ING.FEED.{keyword} format check ID.

    Args:
        note: The feedback note text.

    Returns:
        A check ID like "ING.FEED.supply_chain_risk".
    """
    # Remove non-alphanumeric, lowercase, split on whitespace
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", note.lower())
    words = cleaned.split()

    # Filter out common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "no", "not",
        "for", "of", "in", "on", "at", "to", "and", "or", "but",
        "this", "that", "check", "missing", "need", "should", "would",
        "could", "have", "has", "had", "with", "from", "about",
    }
    significant = [w for w in words if w not in stop_words and len(w) > 1]

    # Take first 3 significant words
    keyword = "_".join(significant[:3]) if significant else "unknown"
    return f"ING.FEED.{keyword}"


def _count_feedback(
    conn: duckdb.DuckDBPyConnection,
    feedback_type: str,
) -> int:
    """Count PENDING feedback of a given type."""
    result = conn.execute(
        "SELECT COUNT(*) FROM brain_feedback "
        "WHERE feedback_type = ? AND status = 'PENDING'",
        [feedback_type],
    ).fetchone()
    return result[0] if result else 0


def _recent_feedback(
    conn: duckdb.DuckDBPyConnection,
    limit: int = 10,
) -> list[FeedbackEntry]:
    """Return the most recent feedback entries."""
    rows = conn.execute(
        """SELECT feedback_id, ticker, signal_id, run_id,
                  feedback_type, direction, note, reviewer,
                  status, created_at
           FROM brain_feedback
           ORDER BY created_at DESC
           LIMIT ?""",
        [limit],
    ).fetchall()

    return [row_to_feedback_entry(row) for row in rows]


def _recent_proposals(
    conn: duckdb.DuckDBPyConnection,
    limit: int = 10,
) -> list[ProposalRecord]:
    """Return the most recent proposal records."""
    rows = conn.execute(
        """SELECT proposal_id, source_type, source_ref, signal_id,
                  proposal_type, proposed_check, proposed_changes,
                  backtest_results, rationale, status, reviewed_by,
                  created_at
           FROM brain_proposals
           ORDER BY created_at DESC
           LIMIT ?""",
        [limit],
    ).fetchall()

    results: list[ProposalRecord] = []
    for row in rows:
        proposed_check = _parse_json_field(row[5])
        proposed_changes = _parse_json_field(row[6])
        backtest_results = _parse_json_field(row[7])

        results.append(
            ProposalRecord(
                proposal_id=row[0],
                source_type=row[1],
                source_ref=row[2],
                signal_id=row[3],
                proposal_type=row[4],
                proposed_check=proposed_check,
                proposed_changes=proposed_changes,
                backtest_results=backtest_results,
                rationale=row[8],
                status=row[9],
                reviewed_by=row[10],
                created_at=row[11],
            )
        )

    return results


def row_to_feedback_entry(
    row: tuple[Any, ...],
) -> FeedbackEntry:
    """Convert a DuckDB row tuple to a FeedbackEntry."""
    return FeedbackEntry(
        feedback_id=row[0],
        ticker=row[1],
        signal_id=row[2],
        run_id=row[3],
        feedback_type=row[4],
        direction=row[5],
        note=row[6],
        reviewer=row[7],
        status=row[8],
        created_at=row[9],
    )


def _parse_json_field(value: Any) -> dict[str, Any] | None:
    """Parse a JSON field that may be a string, dict, or None."""
    if value is None:
        return None
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return cast(dict[str, Any], parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return None
