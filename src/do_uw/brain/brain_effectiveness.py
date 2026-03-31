"""Brain check effectiveness tracking: compute fire rates from brain_signal_runs.

Reads brain_signal_runs table (populated by pipeline after ANALYZE) and
computes per-check effectiveness metrics: fire_rate, skip_rate, and
classification (always-fire, never-fire, high-skip).

Two systems coexist for check result tracking:
  1. KnowledgeStore CheckRun (SQLite, knowledge.db) -- records used by
     knowledge CLI commands (check-stats, dead-checks).
  2. brain_signal_runs (DuckDB, brain.duckdb) -- records used by brain
     effectiveness analysis and backtesting.

These will converge in a future plan. For now, brain_effectiveness.py
reads ONLY from brain_signal_runs in DuckDB, and the pipeline's
post-ANALYZE step should record to both stores.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import duckdb
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SignalEffectivenessEntry(BaseModel):
    """Per-check effectiveness metrics from brain_signal_runs."""

    signal_id: str
    fire_rate: float = 0.0
    """TRIGGERED / total evaluations (excludes SKIPPED)."""
    clear_rate: float = 0.0
    skip_rate: float = 0.0
    info_rate: float = 0.0
    total_evaluations: int = 0
    """Total non-skip evaluations (TRIGGERED + CLEAR + INFO)."""
    total_runs: int = 0
    """Total rows including SKIPPED."""
    triggered_count: int = 0
    clear_count: int = 0
    skipped_count: int = 0
    info_count: int = 0


class EffectivenessReport(BaseModel):
    """Aggregated effectiveness report across all checks."""

    total_signals_analyzed: int = 0
    total_runs: int = 0
    """Total distinct run_ids in brain_signal_runs."""

    always_fire: list[dict[str, Any]] = Field(default_factory=list)
    """Checks firing in every non-skip evaluation (fire_rate == 1.0).
    Each entry: {signal_id, name, fire_rate, run_count}. Too sensitive?"""

    never_fire: list[dict[str, Any]] = Field(default_factory=list)
    """Checks never firing (fire_rate == 0.0 AND skip_rate < 1.0).
    Each entry: {signal_id, name, run_count}. Miscalibrated?"""

    high_skip: list[dict[str, Any]] = Field(default_factory=list)
    """Checks skipped >50% of the time.
    Each entry: {signal_id, name, skip_rate, run_count}. Data gap?"""

    consistent: list[dict[str, Any]] = Field(default_factory=list)
    """Checks with stable fire rates (0.2-0.8, low stddev).
    Each entry: {signal_id, name, fire_rate, stddev}."""

    confidence_note: str = ""
    """Confidence assessment based on run count."""

    by_content_type: dict[str, dict[str, Any]] = Field(default_factory=dict)
    """Stats grouped by content_type."""


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def compute_effectiveness(
    conn: duckdb.DuckDBPyConnection,
    min_runs: int = 1,
) -> EffectivenessReport:
    """Compute effectiveness metrics from brain_signal_runs.

    Reads all non-backtest check runs, computes fire/skip/clear rates
    per check, classifies into always-fire/never-fire/high-skip/consistent,
    and determines confidence based on total distinct run_ids.

    Args:
        conn: DuckDB connection with brain schema.
        min_runs: Minimum total runs for a check to be included.

    Returns:
        EffectivenessReport with all classifications.
    """
    # Count distinct runs for confidence
    total_runs_result = conn.execute(
        "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
        "WHERE is_backtest = FALSE"
    ).fetchone()
    total_distinct_runs = total_runs_result[0] if total_runs_result else 0

    # Get per-check status counts
    rows = conn.execute(
        "SELECT signal_id, status, COUNT(*) as cnt "
        "FROM brain_signal_runs "
        "WHERE is_backtest = FALSE "
        "GROUP BY signal_id, status "
        "ORDER BY signal_id, status"
    ).fetchall()

    if not rows:
        return EffectivenessReport(
            confidence_note=_confidence_note(0),
        )

    # Aggregate per check
    check_stats: dict[str, SignalEffectivenessEntry] = {}
    for signal_id, status, cnt in rows:
        if signal_id not in check_stats:
            check_stats[signal_id] = SignalEffectivenessEntry(signal_id=signal_id)
        entry = check_stats[signal_id]
        entry.total_runs += cnt
        status_upper = status.upper()
        if status_upper == "TRIGGERED":
            entry.triggered_count += cnt
        elif status_upper == "CLEAR":
            entry.clear_count += cnt
        elif status_upper == "SKIPPED":
            entry.skipped_count += cnt
        elif status_upper == "INFO":
            entry.info_count += cnt

    # Compute rates and classify
    report = EffectivenessReport(
        total_runs=total_distinct_runs,
        confidence_note=_confidence_note(total_distinct_runs),
    )

    for signal_id, entry in check_stats.items():
        if entry.total_runs < min_runs:
            continue

        report.total_signals_analyzed += 1
        entry.total_evaluations = (
            entry.triggered_count + entry.clear_count + entry.info_count
        )

        # Compute rates (against total_runs including skips)
        if entry.total_runs > 0:
            entry.fire_rate = round(entry.triggered_count / entry.total_runs, 4)
            entry.clear_rate = round(entry.clear_count / entry.total_runs, 4)
            entry.skip_rate = round(entry.skipped_count / entry.total_runs, 4)
            entry.info_rate = round(entry.info_count / entry.total_runs, 4)

        # Classify (priority order: always-fire, high-skip, never-fire)
        # High-skip checked before never-fire because a check that is
        # mostly skipped is primarily a data gap, not a calibration issue.
        check_summary = {"signal_id": signal_id, "run_count": entry.total_runs}

        if entry.fire_rate == 1.0 and entry.total_evaluations > 0:
            check_summary["fire_rate"] = entry.fire_rate
            check_summary["name"] = signal_id  # Name not in brain_signal_runs
            report.always_fire.append(check_summary)
        elif entry.skip_rate > 0.5:
            check_summary["skip_rate"] = entry.skip_rate
            check_summary["name"] = signal_id
            report.high_skip.append(check_summary)
        elif (
            entry.fire_rate == 0.0
            and entry.skip_rate < 1.0
            and entry.total_evaluations > 0
        ):
            check_summary["name"] = signal_id
            report.never_fire.append(check_summary)

        # Consistent: fire rate between 0.2 and 0.8 (requires per-run
        # analysis for stddev, but we can approximate for now)
        if 0.2 <= entry.fire_rate <= 0.8:
            report.consistent.append(
                {
                    "signal_id": signal_id,
                    "name": signal_id,
                    "fire_rate": entry.fire_rate,
                    "stddev": 0.0,  # Placeholder until per-run stddev computation
                }
            )

    return report


def _confidence_note(n_runs: int) -> str:
    """Determine confidence level from distinct run count."""
    if n_runs < 5:
        return f"LOW (N={n_runs} runs, need 5+ for meaningful statistics)"
    if n_runs < 20:
        return f"MEDIUM (N={n_runs} runs, need 20+ for high confidence)"
    return f"HIGH (N={n_runs} runs)"


# ---------------------------------------------------------------------------
# brain_effectiveness table management
# ---------------------------------------------------------------------------


def update_effectiveness_table(
    conn: duckdb.DuckDBPyConnection,
    period: str = "all_time",
) -> int:
    """Compute effectiveness metrics and upsert into brain_effectiveness.

    Reads brain_signal_runs, computes per-check metrics, and writes
    one row per check into brain_effectiveness with the given period.

    Args:
        conn: DuckDB connection with brain schema.
        period: Measurement period label (e.g., "all_time", "2026-Q1").

    Returns:
        Number of rows written.
    """
    # Get per-check status counts
    rows = conn.execute(
        "SELECT signal_id, status, COUNT(*) as cnt "
        "FROM brain_signal_runs "
        "WHERE is_backtest = FALSE "
        "GROUP BY signal_id, status"
    ).fetchall()

    if not rows:
        return 0

    # Aggregate per check
    stats: dict[str, dict[str, int]] = {}
    for signal_id, status, cnt in rows:
        if signal_id not in stats:
            stats[signal_id] = {
                "triggered": 0,
                "clear": 0,
                "skipped": 0,
                "info": 0,
                "total": 0,
            }
        s = stats[signal_id]
        s["total"] += cnt
        status_upper = status.upper()
        if status_upper == "TRIGGERED":
            s["triggered"] += cnt
        elif status_upper == "CLEAR":
            s["clear"] += cnt
        elif status_upper == "SKIPPED":
            s["skipped"] += cnt
        elif status_upper == "INFO":
            s["info"] += cnt

    # Count distinct runs per check for run_count
    run_counts = conn.execute(
        "SELECT signal_id, COUNT(DISTINCT run_id) "
        "FROM brain_signal_runs WHERE is_backtest = FALSE "
        "GROUP BY signal_id"
    ).fetchall()
    run_count_map = {r[0]: r[1] for r in run_counts}

    # Delete existing rows for this period and insert fresh
    conn.execute(
        "DELETE FROM brain_effectiveness WHERE measurement_period = ?",
        [period],
    )

    now = datetime.now(UTC).isoformat()
    rows_written = 0

    for signal_id, s in stats.items():
        total = s["total"]
        non_skip = s["triggered"] + s["clear"] + s["info"]
        discrimination = 0.0
        if non_skip > 0:
            # Discrimination: 1 - max_rate (more even = higher discrimination)
            rates = [
                s["triggered"] / non_skip,
                s["clear"] / non_skip,
                s["info"] / non_skip,
            ]
            discrimination = round(1.0 - max(rates), 4)

        fire_rate = s["triggered"] / total if total > 0 else 0.0
        skip_rate = s["skipped"] / total if total > 0 else 0.0

        conn.execute(
            """INSERT OR REPLACE INTO brain_effectiveness (
                signal_id, measurement_period, total_evaluations,
                red_count, yellow_count, clear_count, info_count,
                skipped_count, not_available_count, discrimination_power,
                flagged_always_fires, flagged_never_fires,
                flagged_high_skip, flagged_low_discrimination,
                computed_at, run_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                signal_id,
                period,
                non_skip,
                s["triggered"],  # red_count = triggered
                0,  # yellow_count (not tracked separately yet)
                s["clear"],
                s["info"],
                s["skipped"],
                0,  # not_available_count
                discrimination,
                fire_rate == 1.0 and non_skip > 0,  # always fires
                fire_rate == 0.0 and skip_rate < 1.0 and non_skip > 0,  # never fires
                skip_rate > 0.5,  # high skip
                discrimination < 0.1 and non_skip > 0,  # low discrimination
                now,
                run_count_map.get(signal_id, 0),
            ],
        )
        rows_written += 1

    return rows_written


# ---------------------------------------------------------------------------
# Recording functions
# ---------------------------------------------------------------------------


def record_check_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    signal_id: str,
    signal_version: int,
    status: str,
    value: str | None,
    evidence: str | None,
    ticker: str,
    is_backtest: bool = False,
) -> None:
    """Insert a single row into brain_signal_runs.

    Used by the pipeline to record each check result after ANALYZE.

    Args:
        conn: DuckDB connection with brain schema.
        run_id: Unique pipeline run identifier.
        signal_id: Check ID (e.g., "BIZ.SIZE.market_cap").
        signal_version: Check definition version.
        status: Check result status (TRIGGERED, CLEAR, SKIPPED, INFO).
        value: Check result value (if any).
        evidence: Evidence text (if any).
        ticker: Company ticker symbol.
        is_backtest: True if this is a backtest replay, not live.
    """
    now = datetime.now(UTC).isoformat()
    conn.execute(
        """INSERT INTO brain_signal_runs (
            run_id, signal_id, signal_version, status, value,
            evidence, ticker, run_date, is_backtest
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [run_id, signal_id, signal_version, status, value, evidence, ticker, now, is_backtest],
    )


def record_signal_runs_batch(
    conn: duckdb.DuckDBPyConnection,
    rows: list[dict[str, Any]],
) -> int:
    """Batch insert multiple brain_signal_runs rows.

    More efficient than record_check_run() for post-ANALYZE recording
    of all 381+ check results in a single transaction.

    Each row dict must contain: run_id, signal_id, signal_version,
    status, ticker. Optional: value, evidence, is_backtest.

    Args:
        conn: DuckDB connection with brain schema.
        rows: List of row dicts to insert.

    Returns:
        Number of rows inserted.
    """
    if not rows:
        return 0

    now = datetime.now(UTC).isoformat()
    values_list = []
    for row in rows:
        values_list.append((
            row["run_id"],
            row["signal_id"],
            row.get("signal_version", 1),
            row["status"],
            row.get("value"),
            row.get("evidence"),
            row["ticker"],
            now,
            row.get("is_backtest", False),
        ))

    conn.executemany(
        """INSERT INTO brain_signal_runs (
            run_id, signal_id, signal_version, status, value,
            evidence, ticker, run_date, is_backtest
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        values_list,
    )

    return len(values_list)


__all__ = [
    "SignalEffectivenessEntry",
    "EffectivenessReport",
    "compute_effectiveness",
    "record_check_run",
    "record_signal_runs_batch",
    "update_effectiveness_table",
]
