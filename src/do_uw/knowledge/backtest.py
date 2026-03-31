"""Backtesting infrastructure: replay checks against historical state files.

Loads a serialized AnalysisState from disk, runs the current check corpus
against the historical ExtractedData and CompanyProfile, and records results
in brain_signal_runs with is_backtest=TRUE.

Used by the ``do-uw brain backtest`` CLI command and programmatically for
check effectiveness measurement over time.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BacktestResult(BaseModel):
    """Result of replaying checks against a historical state file."""

    ticker: str
    state_path: str
    state_date: str = ""
    """Extracted from state file metadata or created_at."""
    checks_executed: int = 0
    triggered: int = 0
    clear: int = 0
    skipped: int = 0
    info: int = 0
    results_by_id: dict[str, str] = Field(default_factory=dict)
    """signal_id -> status string (TRIGGERED, CLEAR, SKIPPED, INFO)."""


class BacktestComparison(BaseModel):
    """Comparison of two backtest results for the same state."""

    ticker: str
    run_a: BacktestResult
    run_b: BacktestResult
    changed: list[dict[str, str]] = Field(default_factory=list)
    """Checks that changed status: [{signal_id, old_status, new_status}]."""
    new_checks: list[str] = Field(default_factory=list)
    """Checks in B but not A (newly added)."""
    removed_checks: list[str] = Field(default_factory=list)
    """Checks in A but not B (retired)."""


# ---------------------------------------------------------------------------
# Backtest execution
# ---------------------------------------------------------------------------


def run_backtest(
    state_path: Path,
    record: bool = True,
) -> BacktestResult:
    """Load a historical state file and replay all checks.

    Args:
        state_path: Path to a state.json file (e.g., output/AAPL/state.json).
        record: If True, insert results into brain_signal_runs with
                is_backtest=TRUE.

    Returns:
        BacktestResult with counts and per-check status.

    Raises:
        FileNotFoundError: If state_path does not exist.
        ValueError: If state file cannot be deserialized.
    """
    if not state_path.exists():
        msg = f"State file not found: {state_path}"
        raise FileNotFoundError(msg)

    # Load state file
    from do_uw.models.state import AnalysisState

    with open(state_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        state = AnalysisState.model_validate(data)
    except Exception as exc:
        msg = f"Failed to deserialize state file: {exc}"
        raise ValueError(msg) from exc

    # Extract state date from metadata
    state_date = ""
    if hasattr(state, "created_at") and state.created_at:
        state_date = str(state.created_at)
    elif "created_at" in data:
        state_date = str(data["created_at"])

    # Load current check definitions
    from do_uw.brain.brain_unified_loader import load_signals

    checks_data = load_signals()

    checks = checks_data.get("signals", [])

    # Execute checks against historical state
    from do_uw.stages.analyze.signal_engine import execute_signals

    extracted = state.extracted
    company = state.company

    if extracted is None:
        msg = "State file has no extracted data -- nothing to backtest against"
        raise ValueError(msg)

    results = execute_signals(checks, extracted, company)

    # Build result
    bt = BacktestResult(
        ticker=state.ticker,
        state_path=str(state_path),
        state_date=state_date,
        checks_executed=len(results),
    )
    for r in results:
        status_val = r.status.value
        bt.results_by_id[r.signal_id] = status_val
        if status_val == "TRIGGERED":
            bt.triggered += 1
        elif status_val == "CLEAR":
            bt.clear += 1
        elif status_val == "SKIPPED":
            bt.skipped += 1
        elif status_val == "INFO":
            bt.info += 1

    logger.info(
        "Backtest %s: %d signals (%d triggered, %d clear, %d skipped, %d info)",
        bt.ticker,
        bt.checks_executed,
        bt.triggered,
        bt.clear,
        bt.skipped,
        bt.info,
    )

    # Record to brain_signal_runs if requested
    if record:
        _record_backtest_results(bt, results)

    return bt


def _record_backtest_results(
    bt: BacktestResult,
    results: list[Any],
) -> None:
    """Insert backtest results into brain_signal_runs table."""
    from do_uw.brain.brain_effectiveness import record_signal_runs_batch
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        logger.warning("brain.duckdb not found at %s, skipping recording", db_path)
        return

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_id = f"backtest_{bt.ticker}_{timestamp}"

    rows: list[dict[str, Any]] = []
    for r in results:
        rows.append({
            "run_id": run_id,
            "signal_id": r.signal_id,
            "signal_version": 1,
            "status": r.status.value,
            "value": str(r.value) if r.value is not None else None,
            "evidence": r.evidence,
            "ticker": bt.ticker,
            "is_backtest": True,
        })

    conn = connect_brain_db(db_path)
    try:
        inserted = record_signal_runs_batch(conn, rows)
        logger.info("Recorded %d backtest results as run_id=%s", inserted, run_id)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare_backtests(
    result_a: BacktestResult,
    result_b: BacktestResult,
) -> BacktestComparison:
    """Compare two backtest results to identify changes.

    Useful for comparing results after check definition changes:
    run backtest with old checks, update checks, run backtest again,
    then compare.

    Args:
        result_a: Earlier/baseline backtest result.
        result_b: Later/updated backtest result.

    Returns:
        BacktestComparison with changed, new, and removed checks.
    """
    ids_a = set(result_a.results_by_id.keys())
    ids_b = set(result_b.results_by_id.keys())

    changed: list[dict[str, str]] = []
    for signal_id in ids_a & ids_b:
        old_status = result_a.results_by_id[signal_id]
        new_status = result_b.results_by_id[signal_id]
        if old_status != new_status:
            changed.append({
                "signal_id": signal_id,
                "old_status": old_status,
                "new_status": new_status,
            })

    return BacktestComparison(
        ticker=result_a.ticker or result_b.ticker,
        run_a=result_a,
        run_b=result_b,
        changed=changed,
        new_checks=sorted(ids_b - ids_a),
        removed_checks=sorted(ids_a - ids_b),
    )


__all__ = [
    "BacktestComparison",
    "BacktestResult",
    "compare_backtests",
    "run_backtest",
]
