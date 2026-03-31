"""Tests for brain_delta: cross-run signal status comparison."""

from __future__ import annotations

import duckdb
import pytest

from do_uw.brain.brain_delta import (
    DeltaReport,
    RunInfo,
    SignalChange,
    compute_delta,
    list_runs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with brain_signal_runs table."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE brain_signal_runs (
            run_id VARCHAR NOT NULL,
            signal_id VARCHAR NOT NULL,
            signal_version INTEGER NOT NULL,
            status VARCHAR NOT NULL,
            value VARCHAR,
            evidence TEXT,
            ticker VARCHAR NOT NULL,
            run_date TIMESTAMP NOT NULL,
            is_backtest BOOLEAN DEFAULT FALSE,
            industry_code VARCHAR,
            threshold_was_adjusted BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (run_id, signal_id)
        )
    """)
    return conn


def _insert_signal(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    signal_id: str,
    status: str,
    ticker: str = "TEST",
    run_date: str = "2026-01-01 00:00:00",
    value: str | None = None,
    is_backtest: bool = False,
) -> None:
    """Insert a single signal run row."""
    conn.execute(
        """
        INSERT INTO brain_signal_runs
        (run_id, signal_id, signal_version, status, value, ticker, run_date, is_backtest)
        VALUES (?, ?, 1, ?, ?, ?, ?, ?)
        """,
        [run_id, signal_id, status, value, ticker, run_date, is_backtest],
    )


# ---------------------------------------------------------------------------
# Test: insufficient runs
# ---------------------------------------------------------------------------


def test_delta_insufficient_runs_zero(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """No runs at all for ticker -> error."""
    report = compute_delta(mem_conn, "TEST")
    assert report.error is not None
    assert "0 run(s)" in report.error


def test_delta_insufficient_runs_one(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """Only one run for ticker -> error."""
    _insert_signal(mem_conn, "run-1", "SIG.A", "CLEAR")
    report = compute_delta(mem_conn, "TEST")
    assert report.error is not None
    assert "1 run(s)" in report.error
    assert "Need at least 2" in report.error


# ---------------------------------------------------------------------------
# Test: two runs with changes
# ---------------------------------------------------------------------------


def test_delta_two_runs_with_changes(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """Two runs with differing statuses -> correct classification."""
    # Old run (run-1): SIG.A=CLEAR, SIG.B=TRIGGERED, SIG.C=CLEAR, SIG.D=INFO
    for sig, status in [("SIG.A", "CLEAR"), ("SIG.B", "TRIGGERED"), ("SIG.C", "CLEAR"), ("SIG.D", "INFO")]:
        _insert_signal(mem_conn, "run-1", sig, status, run_date="2026-01-01 00:00:00")

    # New run (run-2): SIG.A=TRIGGERED, SIG.B=CLEAR, SIG.C=SKIPPED, SIG.D=TRIGGERED
    for sig, status in [("SIG.A", "TRIGGERED"), ("SIG.B", "CLEAR"), ("SIG.C", "SKIPPED"), ("SIG.D", "TRIGGERED")]:
        _insert_signal(mem_conn, "run-2", sig, status, run_date="2026-01-02 00:00:00")

    report = compute_delta(mem_conn, "TEST")

    assert report.error is None
    assert len(report.changes) == 4

    # SIG.A: CLEAR -> TRIGGERED = newly_triggered
    assert len(report.newly_triggered) == 2  # SIG.A and SIG.D
    triggered_ids = {c.signal_id for c in report.newly_triggered}
    assert "SIG.A" in triggered_ids
    assert "SIG.D" in triggered_ids

    # SIG.B: TRIGGERED -> CLEAR = newly_cleared
    assert len(report.newly_cleared) == 1
    assert report.newly_cleared[0].signal_id == "SIG.B"

    # SIG.C: CLEAR -> SKIPPED = newly_skipped
    assert len(report.newly_skipped) == 1
    assert report.newly_skipped[0].signal_id == "SIG.C"

    assert report.unchanged_count == 0


# ---------------------------------------------------------------------------
# Test: explicit run IDs
# ---------------------------------------------------------------------------


def test_delta_explicit_run_ids(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """Explicit --run1/--run2 compares specific runs, not most recent."""
    # Three runs: run-1, run-2, run-3
    _insert_signal(mem_conn, "run-1", "SIG.A", "CLEAR", run_date="2026-01-01 00:00:00")
    _insert_signal(mem_conn, "run-2", "SIG.A", "TRIGGERED", run_date="2026-01-02 00:00:00")
    _insert_signal(mem_conn, "run-3", "SIG.A", "CLEAR", run_date="2026-01-03 00:00:00")

    # Default (no explicit IDs): compares run-2 (old) and run-3 (new)
    default_report = compute_delta(mem_conn, "TEST")
    assert default_report.error is None
    assert default_report.old_run.run_id == "run-2"
    assert default_report.new_run.run_id == "run-3"

    # Explicit: compare run-1 (old) and run-2 (new)
    explicit_report = compute_delta(mem_conn, "TEST", run1_id="run-1", run2_id="run-2")
    assert explicit_report.error is None
    assert explicit_report.old_run.run_id == "run-1"
    assert explicit_report.new_run.run_id == "run-2"
    assert len(explicit_report.newly_triggered) == 1
    assert explicit_report.newly_triggered[0].signal_id == "SIG.A"


def test_delta_invalid_run_id(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """Invalid explicit run ID -> error."""
    _insert_signal(mem_conn, "run-1", "SIG.A", "CLEAR")
    report = compute_delta(mem_conn, "TEST", run1_id="run-1", run2_id="NONEXISTENT")
    assert report.error is not None
    assert "NONEXISTENT" in report.error


# ---------------------------------------------------------------------------
# Test: no changes
# ---------------------------------------------------------------------------


def test_delta_no_changes(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """Two runs with identical statuses -> 0 changes."""
    for sig in ["SIG.A", "SIG.B", "SIG.C"]:
        _insert_signal(mem_conn, "run-1", sig, "CLEAR", run_date="2026-01-01 00:00:00")
        _insert_signal(mem_conn, "run-2", sig, "CLEAR", run_date="2026-01-02 00:00:00")

    report = compute_delta(mem_conn, "TEST")
    assert report.error is None
    assert len(report.changes) == 0
    assert report.unchanged_count == 3


# ---------------------------------------------------------------------------
# Test: list_runs
# ---------------------------------------------------------------------------


def test_list_runs(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """list_runs returns runs in descending date order."""
    _insert_signal(mem_conn, "run-1", "SIG.A", "CLEAR", run_date="2026-01-01 00:00:00")
    _insert_signal(mem_conn, "run-2", "SIG.A", "CLEAR", run_date="2026-01-02 00:00:00")
    _insert_signal(mem_conn, "run-3", "SIG.A", "CLEAR", run_date="2026-01-03 00:00:00")

    runs = list_runs(mem_conn, "TEST")
    assert len(runs) == 3
    assert runs[0].run_id == "run-3"  # most recent first
    assert runs[1].run_id == "run-2"
    assert runs[2].run_id == "run-1"


def test_list_runs_excludes_backtests(mem_conn: duckdb.DuckDBPyConnection) -> None:
    """list_runs excludes backtest runs."""
    _insert_signal(mem_conn, "run-1", "SIG.A", "CLEAR", run_date="2026-01-01 00:00:00")
    _insert_signal(mem_conn, "run-bt", "SIG.A", "CLEAR", run_date="2026-01-02 00:00:00", is_backtest=True)

    runs = list_runs(mem_conn, "TEST")
    assert len(runs) == 1
    assert runs[0].run_id == "run-1"


# ---------------------------------------------------------------------------
# Test: model creation
# ---------------------------------------------------------------------------


def test_model_creation() -> None:
    """DeltaReport, SignalChange, RunInfo can be created."""
    change = SignalChange(
        signal_id="SIG.A",
        old_status="CLEAR",
        new_status="TRIGGERED",
        change_direction="newly_triggered",
    )
    run = RunInfo(run_id="r1", run_date="2026-01-01", signal_count=100)
    report = DeltaReport(
        ticker="TEST",
        old_run=run,
        new_run=RunInfo(run_id="r2", run_date="2026-01-02", signal_count=100),
        changes=[change],
        newly_triggered=[change],
        unchanged_count=99,
    )
    assert report.ticker == "TEST"
    assert len(report.changes) == 1
    assert report.unchanged_count == 99
