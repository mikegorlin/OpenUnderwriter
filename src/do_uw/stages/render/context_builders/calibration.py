"""Calibration context builder for D&O worksheet rendering.

Renders a 'Calibration Notes' section showing system intelligence
status, recent calibration changes, discovery findings, and pending
feedback for the analyzed company. Uses lazy imports for brain DuckDB
and gracefully degrades when brain.duckdb is unavailable.

Moved from md_renderer_helpers_calibration.py as part of the shared
context layer (Phase 58). Zero logic changes.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def render_calibration_notes(state: AnalysisState) -> str:
    """Render a Calibration Notes markdown section from brain DuckDB data.

    Queries brain DuckDB for:
    - Active and incubating check counts
    - Pending feedback count and recent entries for this ticker
    - Recent calibration changes (last 30 days)
    - Discovery findings from blind_spot_results

    Returns empty string if no calibration data exists (section is
    omitted from worksheet rather than rendering an empty block).

    Args:
        state: AnalysisState with ticker and acquired_data.

    Returns:
        Markdown string for calibration notes section, or empty string.
    """
    ticker = state.ticker

    # Query brain DuckDB for calibration data (lazy import, graceful fail)
    active_count = 0
    incubating_count = 0
    pending_feedback = 0
    recent_changes: list[dict[str, str]] = []
    ticker_feedback: list[dict[str, str]] = []

    try:
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        db_path = get_brain_db_path()
        if not db_path.exists():
            logger.debug("brain.duckdb not found, skipping calibration notes")
        else:
            conn = connect_brain_db(db_path)
            active_count, incubating_count = _query_signal_counts(conn)
            pending_feedback = _query_pending_feedback_count(conn)
            recent_changes = _query_recent_changes(conn)
            ticker_feedback = _query_ticker_feedback(conn, ticker)
            conn.close()
    except Exception as exc:
        logger.debug("Brain DuckDB unavailable for calibration notes: %s", exc)

    # Discovery findings from blind spot search
    discovery_summary = ""
    if state.acquired_data and state.acquired_data.blind_spot_results:
        discovery_summary = str(
            state.acquired_data.blind_spot_results.get("discovery_findings", "")
        )

    # Don't render empty section
    has_data = any([
        active_count > 0,
        incubating_count > 0,
        pending_feedback > 0,
        recent_changes,
        ticker_feedback,
        discovery_summary,
    ])
    if not has_data:
        return ""

    # Build markdown
    lines: list[str] = []
    lines.append("## Calibration Notes")
    lines.append("")

    # System Intelligence Status
    lines.append("### System Intelligence Status")
    lines.append(f"- **Checks active**: {active_count}")
    lines.append(
        f"- **Checks incubating**: {incubating_count} "
        "(pending human approval)"
    )
    lines.append(f"- **Pending feedback**: {pending_feedback} entries")
    lines.append("")

    # Recent Calibration Changes
    lines.append("### Recent Calibration Changes")
    if recent_changes:
        lines.append("")
        lines.append("| Date | Check | Change | Changed By |")
        lines.append("|------|-------|--------|------------|")
        for change in recent_changes[:10]:
            lines.append(
                f"| {change.get('date', 'N/A')} "
                f"| {change.get('signal_id', 'N/A')} "
                f"| {change.get('description', 'N/A')} "
                f"| {change.get('changed_by', 'system')} |"
            )
    else:
        lines.append("No recent calibration changes.")
    lines.append("")

    # Discovery Findings
    lines.append("### Discovery Findings")
    if discovery_summary:
        lines.append(discovery_summary)
    else:
        lines.append("No new discoveries from this run.")
    lines.append("")

    # Feedback for this ticker
    lines.append(f"### Feedback for {ticker}")
    if ticker_feedback:
        for fb in ticker_feedback[:5]:
            lines.append(
                f"- **{fb.get('type', 'N/A')}** "
                f"({fb.get('signal_id', 'general')}): "
                f"{fb.get('note', '')}"
            )
    else:
        lines.append(f"No pending feedback for {ticker}.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Brain DuckDB query helpers
# ---------------------------------------------------------------------------


def _query_signal_counts(conn: Any) -> tuple[int, int]:
    """Get active and incubating signal counts from YAML (source of truth)."""
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        signals_data = load_signals()
        signals = signals_data.get("signals", [])
        active_count = len(signals)
        # Incubating signals are not in YAML (YAML only has active)
        incubating_count = 0
        return active_count, incubating_count
    except Exception:
        return 0, 0


def _query_pending_feedback_count(conn: Any) -> int:
    """Query count of pending feedback entries."""
    try:
        result = conn.execute(
            "SELECT COUNT(*) FROM brain_feedback WHERE status = 'PENDING'"
        ).fetchone()
        return result[0] if result else 0
    except Exception:
        return 0


def _query_recent_changes(conn: Any) -> list[dict[str, str]]:
    """Query recent changelog entries (last 30 days)."""
    try:
        rows = conn.execute(
            """SELECT changed_at, signal_id, change_description, changed_by
               FROM brain_changelog
               WHERE changed_at >= current_timestamp - INTERVAL 30 DAY
               ORDER BY changed_at DESC
               LIMIT 10"""
        ).fetchall()

        return [
            {
                "date": str(row[0])[:10] if row[0] else "N/A",
                "signal_id": str(row[1]),
                "description": str(row[2])[:60],
                "changed_by": str(row[3]),
            }
            for row in rows
        ]
    except Exception:
        return []


def _query_ticker_feedback(
    conn: Any, ticker: str,
) -> list[dict[str, str]]:
    """Query pending feedback for a specific ticker."""
    try:
        rows = conn.execute(
            """SELECT feedback_type, signal_id, note
               FROM brain_feedback
               WHERE ticker = ? AND status = 'PENDING'
               ORDER BY created_at DESC
               LIMIT 5""",
            [ticker],
        ).fetchall()

        return [
            {
                "type": str(row[0]),
                "signal_id": str(row[1]) if row[1] else "general",
                "note": str(row[2])[:80],
            }
            for row in rows
        ]
    except Exception:
        return []


__all__ = ["render_calibration_notes"]
