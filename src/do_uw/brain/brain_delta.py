"""Brain delta: cross-run signal status comparison.

Computes which signals changed status between two pipeline runs for the
same ticker. Used by ``do-uw brain delta <TICKER>`` CLI command.
"""

from __future__ import annotations

import duckdb
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SignalChange(BaseModel):
    """A single signal whose status changed between two runs."""

    signal_id: str
    old_status: str | None = None
    new_status: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    change_direction: str  # "newly_triggered", "newly_cleared", "newly_skipped", "other"


class RunInfo(BaseModel):
    """Metadata for a single pipeline run."""

    run_id: str
    run_date: str
    signal_count: int


class DeltaReport(BaseModel):
    """Result of comparing two pipeline runs for a ticker."""

    ticker: str
    old_run: RunInfo
    new_run: RunInfo
    changes: list[SignalChange] = []
    newly_triggered: list[SignalChange] = []  # CLEAR/SKIPPED -> TRIGGERED
    newly_cleared: list[SignalChange] = []  # TRIGGERED/SKIPPED -> CLEAR
    newly_skipped: list[SignalChange] = []  # any -> SKIPPED
    other_changes: list[SignalChange] = []  # INFO changes, etc.
    unchanged_count: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Direction classification
# ---------------------------------------------------------------------------

_TRIGGERED_FROM = {"CLEAR", "SKIPPED", "INFO", None}
_CLEARED_FROM = {"TRIGGERED", "SKIPPED", None}


def _classify_direction(
    old_status: str | None,
    new_status: str | None,
) -> str:
    """Classify a status change into a direction bucket."""
    if new_status == "TRIGGERED" and old_status in _TRIGGERED_FROM:
        return "newly_triggered"
    if new_status == "CLEAR" and old_status in _CLEARED_FROM:
        return "newly_cleared"
    if new_status == "SKIPPED":
        return "newly_skipped"
    return "other"


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def list_runs(
    conn: duckdb.DuckDBPyConnection,
    ticker: str,
) -> list[RunInfo]:
    """List all non-backtest runs for a ticker, most recent first.

    Returns at most 20 runs.
    """
    rows = conn.execute(
        """
        SELECT run_id, MIN(run_date) as run_date, COUNT(*) as signal_count
        FROM brain_signal_runs
        WHERE ticker = ? AND is_backtest = FALSE
        GROUP BY run_id
        ORDER BY MIN(run_date) DESC
        LIMIT 20
        """,
        [ticker],
    ).fetchall()

    return [
        RunInfo(
            run_id=row[0],
            run_date=str(row[1]),
            signal_count=row[2],
        )
        for row in rows
    ]


def compute_delta(
    conn: duckdb.DuckDBPyConnection,
    ticker: str,
    run1_id: str | None = None,
    run2_id: str | None = None,
) -> DeltaReport:
    """Compare two pipeline runs and return signal status changes.

    Parameters
    ----------
    conn:
        DuckDB connection to brain.duckdb.
    ticker:
        Ticker symbol to compare runs for.
    run1_id:
        Explicit OLD run ID. If None, uses second-most-recent.
    run2_id:
        Explicit NEW run ID. If None, uses most-recent.

    Returns
    -------
    DeltaReport with classified changes, or error if fewer than 2 runs.
    """
    _placeholder_run = RunInfo(run_id="", run_date="", signal_count=0)

    # Step 1: Identify the two runs to compare
    if run1_id and run2_id:
        # Validate the explicit run IDs exist for this ticker
        for rid in [run1_id, run2_id]:
            count = conn.execute(
                "SELECT COUNT(*) FROM brain_signal_runs WHERE run_id = ? AND ticker = ?",
                [rid, ticker],
            ).fetchone()[0]  # type: ignore[index]
            if count == 0:
                return DeltaReport(
                    ticker=ticker,
                    old_run=_placeholder_run,
                    new_run=_placeholder_run,
                    error=f"Run ID '{rid}' not found for ticker {ticker}.",
                )
        old_run_id = run1_id
        new_run_id = run2_id
    else:
        # Use two most recent non-backtest runs
        recent = conn.execute(
            """
            SELECT run_id, MIN(run_date) as run_date, COUNT(*) as signal_count
            FROM brain_signal_runs
            WHERE ticker = ? AND is_backtest = FALSE
            GROUP BY run_id
            ORDER BY MIN(run_date) DESC
            LIMIT 2
            """,
            [ticker],
        ).fetchall()

        if len(recent) < 2:
            return DeltaReport(
                ticker=ticker,
                old_run=_placeholder_run,
                new_run=_placeholder_run,
                error=(
                    f"Need at least 2 runs for delta. "
                    f"Found {len(recent)} run(s) for {ticker}."
                ),
            )

        new_run_id = recent[0][0]
        old_run_id = recent[1][0]

    # Step 2: Get run metadata
    def _run_info(rid: str) -> RunInfo:
        row = conn.execute(
            """
            SELECT MIN(run_date) as run_date, COUNT(*) as signal_count
            FROM brain_signal_runs
            WHERE run_id = ? AND ticker = ?
            """,
            [rid, ticker],
        ).fetchone()
        return RunInfo(
            run_id=rid,
            run_date=str(row[0]) if row else "",  # type: ignore[index]
            signal_count=row[1] if row else 0,  # type: ignore[index]
        )

    old_run = _run_info(old_run_id)
    new_run = _run_info(new_run_id)

    # Step 3: Join the two run snapshots and find changes
    change_rows = conn.execute(
        """
        SELECT
            COALESCE(o.signal_id, n.signal_id) as signal_id,
            o.status AS old_status,
            n.status AS new_status,
            o.value AS old_value,
            n.value AS new_value
        FROM (SELECT * FROM brain_signal_runs WHERE run_id = ?) o
        FULL OUTER JOIN (SELECT * FROM brain_signal_runs WHERE run_id = ?) n
            ON o.signal_id = n.signal_id
        WHERE o.status IS DISTINCT FROM n.status
        ORDER BY COALESCE(o.signal_id, n.signal_id)
        """,
        [old_run_id, new_run_id],
    ).fetchall()

    # Step 4: Classify changes by direction
    changes: list[SignalChange] = []
    newly_triggered: list[SignalChange] = []
    newly_cleared: list[SignalChange] = []
    newly_skipped: list[SignalChange] = []
    other_changes: list[SignalChange] = []

    for row in change_rows:
        direction = _classify_direction(row[1], row[2])
        change = SignalChange(
            signal_id=row[0],
            old_status=row[1],
            new_status=row[2],
            old_value=row[3],
            new_value=row[4],
            change_direction=direction,
        )
        changes.append(change)
        if direction == "newly_triggered":
            newly_triggered.append(change)
        elif direction == "newly_cleared":
            newly_cleared.append(change)
        elif direction == "newly_skipped":
            newly_skipped.append(change)
        else:
            other_changes.append(change)

    # Step 5: Count unchanged
    unchanged_count = new_run.signal_count - len(changes)

    return DeltaReport(
        ticker=ticker,
        old_run=old_run,
        new_run=new_run,
        changes=changes,
        newly_triggered=newly_triggered,
        newly_cleared=newly_cleared,
        newly_skipped=newly_skipped,
        other_changes=other_changes,
        unchanged_count=unchanged_count,
    )
