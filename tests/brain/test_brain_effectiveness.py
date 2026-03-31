"""Tests for brain effectiveness tracking (brain_signal_runs analysis)."""

from __future__ import annotations

import uuid

import duckdb
import pytest

from do_uw.brain.brain_effectiveness import (
    EffectivenessReport,
    compute_effectiveness,
    record_check_run,
    record_signal_runs_batch,
    update_effectiveness_table,
)
from do_uw.brain.brain_schema import create_schema


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with brain schema."""
    c = duckdb.connect(":memory:")
    create_schema(c)
    return c


@pytest.fixture()
def seeded_conn(conn: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Seed brain_signal_runs with synthetic data.

    5 runs x 10 checks with controlled statuses:
      - CHECK_ALWAYS: TRIGGERED in all 5 runs (always-fire)
      - CHECK_NEVER: CLEAR in all 5 runs (never-fire)
      - CHECK_HIGH_SKIP: SKIPPED in 4/5 runs, CLEAR in 1 (high-skip)
      - CHECK_CONSISTENT: TRIGGERED in 2, CLEAR in 3 (consistent, fire_rate=0.4)
      - CHECK_INFO_ONLY: INFO in all 5 runs
      - CHECK_MIXED_1 through CHECK_MIXED_5: varying statuses
    """
    run_ids = [f"run_{i}" for i in range(1, 6)]

    # Define check -> status pattern for each run
    patterns: dict[str, list[str]] = {
        "CHECK_ALWAYS": ["TRIGGERED", "TRIGGERED", "TRIGGERED", "TRIGGERED", "TRIGGERED"],
        "CHECK_NEVER": ["CLEAR", "CLEAR", "CLEAR", "CLEAR", "CLEAR"],
        "CHECK_HIGH_SKIP": ["SKIPPED", "SKIPPED", "SKIPPED", "SKIPPED", "CLEAR"],
        "CHECK_CONSISTENT": ["TRIGGERED", "CLEAR", "TRIGGERED", "CLEAR", "CLEAR"],
        "CHECK_INFO_ONLY": ["INFO", "INFO", "INFO", "INFO", "INFO"],
        "CHECK_MIXED_1": ["TRIGGERED", "CLEAR", "SKIPPED", "INFO", "TRIGGERED"],
        "CHECK_MIXED_2": ["CLEAR", "CLEAR", "TRIGGERED", "CLEAR", "CLEAR"],
        "CHECK_MIXED_3": ["TRIGGERED", "TRIGGERED", "TRIGGERED", "CLEAR", "TRIGGERED"],
        "CHECK_MIXED_4": ["SKIPPED", "SKIPPED", "CLEAR", "SKIPPED", "SKIPPED"],
        "CHECK_MIXED_5": ["TRIGGERED", "TRIGGERED", "CLEAR", "TRIGGERED", "TRIGGERED"],
    }

    for signal_id, statuses in patterns.items():
        for run_id, status in zip(run_ids, statuses):
            conn.execute(
                """INSERT INTO brain_signal_runs
                   (run_id, signal_id, signal_version, status, value, evidence,
                    ticker, run_date, is_backtest)
                   VALUES (?, ?, 1, ?, NULL, NULL, 'TEST', CURRENT_TIMESTAMP, FALSE)""",
                [run_id, signal_id, status],
            )

    return conn


# ---------------------------------------------------------------------------
# Tests: compute_effectiveness
# ---------------------------------------------------------------------------


class TestComputeEffectiveness:
    """Test effectiveness computation from brain_signal_runs."""

    def test_empty_table(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Empty brain_signal_runs produces empty report."""
        report = compute_effectiveness(conn)
        assert report.total_signals_analyzed == 0
        assert report.total_runs == 0
        assert len(report.always_fire) == 0
        assert len(report.never_fire) == 0
        assert len(report.high_skip) == 0

    def test_total_signals_analyzed(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Should analyze all 10 seeded checks."""
        report = compute_effectiveness(seeded_conn)
        assert report.total_signals_analyzed == 10

    def test_total_distinct_runs(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Should detect 5 distinct run_ids."""
        report = compute_effectiveness(seeded_conn)
        assert report.total_runs == 5

    def test_always_fire_detection(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_ALWAYS should be classified as always-fire."""
        report = compute_effectiveness(seeded_conn)
        always_ids = {e["signal_id"] for e in report.always_fire}
        assert "CHECK_ALWAYS" in always_ids

    def test_never_fire_detection(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_NEVER should be classified as never-fire."""
        report = compute_effectiveness(seeded_conn)
        never_ids = {e["signal_id"] for e in report.never_fire}
        assert "CHECK_NEVER" in never_ids

    def test_high_skip_detection(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_HIGH_SKIP (4/5 skipped) should be classified as high-skip."""
        report = compute_effectiveness(seeded_conn)
        skip_ids = {e["signal_id"] for e in report.high_skip}
        assert "CHECK_HIGH_SKIP" in skip_ids

    def test_consistent_detection(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_CONSISTENT (fire_rate=0.4) should be in consistent list."""
        report = compute_effectiveness(seeded_conn)
        consistent_ids = {e["signal_id"] for e in report.consistent}
        assert "CHECK_CONSISTENT" in consistent_ids

    def test_info_only_never_fire(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_INFO_ONLY (all INFO, fire_rate=0.0, skip_rate=0.0) should be never-fire."""
        report = compute_effectiveness(seeded_conn)
        never_ids = {e["signal_id"] for e in report.never_fire}
        assert "CHECK_INFO_ONLY" in never_ids

    def test_mixed_4_high_skip(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """CHECK_MIXED_4 (4/5 skipped) should be high-skip."""
        report = compute_effectiveness(seeded_conn)
        skip_ids = {e["signal_id"] for e in report.high_skip}
        assert "CHECK_MIXED_4" in skip_ids

    def test_confidence_medium_at_5(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """5 runs should produce MEDIUM confidence (LOW is N<5)."""
        report = compute_effectiveness(seeded_conn)
        assert "MEDIUM" in report.confidence_note
        assert "N=5" in report.confidence_note

    def test_confidence_low(self, conn: duckdb.DuckDBPyConnection) -> None:
        """3 runs should produce LOW confidence."""
        for i in range(3):
            conn.execute(
                """INSERT INTO brain_signal_runs
                   (run_id, signal_id, signal_version, status, ticker,
                    run_date, is_backtest)
                   VALUES (?, 'X', 1, 'CLEAR', 'TST',
                    CURRENT_TIMESTAMP, FALSE)""",
                [f"run_{i}"],
            )
        report = compute_effectiveness(conn)
        assert "LOW" in report.confidence_note
        assert "N=3" in report.confidence_note

    def test_confidence_medium(self, conn: duckdb.DuckDBPyConnection) -> None:
        """10 runs should produce MEDIUM confidence."""
        for i in range(10):
            conn.execute(
                """INSERT INTO brain_signal_runs
                   (run_id, signal_id, signal_version, status, ticker,
                    run_date, is_backtest)
                   VALUES (?, 'X', 1, 'CLEAR', 'TST',
                    CURRENT_TIMESTAMP, FALSE)""",
                [f"run_{i}"],
            )
        report = compute_effectiveness(conn)
        assert "MEDIUM" in report.confidence_note

    def test_confidence_high(self, conn: duckdb.DuckDBPyConnection) -> None:
        """25 runs should produce HIGH confidence."""
        for i in range(25):
            conn.execute(
                """INSERT INTO brain_signal_runs
                   (run_id, signal_id, signal_version, status, ticker,
                    run_date, is_backtest)
                   VALUES (?, 'X', 1, 'CLEAR', 'TST',
                    CURRENT_TIMESTAMP, FALSE)""",
                [f"run_{i}"],
            )
        report = compute_effectiveness(conn)
        assert "HIGH" in report.confidence_note

    def test_min_runs_filter(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """min_runs=6 should exclude all checks (only 5 runs each)."""
        report = compute_effectiveness(seeded_conn, min_runs=6)
        assert report.total_signals_analyzed == 0

    def test_backtest_excluded(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Backtest runs should be excluded from effectiveness computation."""
        conn.execute(
            """INSERT INTO brain_signal_runs
               (run_id, signal_id, signal_version, status, ticker,
                run_date, is_backtest)
               VALUES ('bt_1', 'BACK', 1, 'TRIGGERED', 'TST',
                CURRENT_TIMESTAMP, TRUE)"""
        )
        report = compute_effectiveness(conn)
        assert report.total_signals_analyzed == 0


# ---------------------------------------------------------------------------
# Tests: update_effectiveness_table
# ---------------------------------------------------------------------------


class TestUpdateEffectivenessTable:
    """Test writing effectiveness metrics to brain_effectiveness."""

    def test_writes_rows(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Should write one row per check to brain_effectiveness."""
        count = update_effectiveness_table(seeded_conn)
        assert count == 10

        # Verify rows exist in brain_effectiveness
        result = seeded_conn.execute(
            "SELECT COUNT(*) FROM brain_effectiveness "
            "WHERE measurement_period = 'all_time'"
        ).fetchone()
        assert result is not None
        assert result[0] == 10

    def test_flags_correct(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Always-fire, never-fire, high-skip flags should be set correctly."""
        update_effectiveness_table(seeded_conn)

        # Always fires
        row = seeded_conn.execute(
            "SELECT flagged_always_fires FROM brain_effectiveness "
            "WHERE signal_id = 'CHECK_ALWAYS' AND measurement_period = 'all_time'"
        ).fetchone()
        assert row is not None
        assert row[0] is True

        # Never fires
        row = seeded_conn.execute(
            "SELECT flagged_never_fires FROM brain_effectiveness "
            "WHERE signal_id = 'CHECK_NEVER' AND measurement_period = 'all_time'"
        ).fetchone()
        assert row is not None
        assert row[0] is True

        # High skip
        row = seeded_conn.execute(
            "SELECT flagged_high_skip FROM brain_effectiveness "
            "WHERE signal_id = 'CHECK_HIGH_SKIP' AND measurement_period = 'all_time'"
        ).fetchone()
        assert row is not None
        assert row[0] is True

    def test_discrimination_power(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Discrimination power should be computed and stored."""
        update_effectiveness_table(seeded_conn)

        row = seeded_conn.execute(
            "SELECT discrimination_power FROM brain_effectiveness "
            "WHERE signal_id = 'CHECK_CONSISTENT' AND measurement_period = 'all_time'"
        ).fetchone()
        assert row is not None
        assert row[0] is not None
        assert row[0] > 0  # Consistent check should have non-zero discrimination

    def test_run_count_stored(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """run_count should reflect distinct run_ids per check."""
        update_effectiveness_table(seeded_conn)

        row = seeded_conn.execute(
            "SELECT run_count FROM brain_effectiveness "
            "WHERE signal_id = 'CHECK_ALWAYS' AND measurement_period = 'all_time'"
        ).fetchone()
        assert row is not None
        assert row[0] == 5

    def test_empty_table(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Empty brain_signal_runs produces 0 rows."""
        count = update_effectiveness_table(conn)
        assert count == 0

    def test_idempotent(
        self, seeded_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Running twice should replace, not duplicate rows."""
        update_effectiveness_table(seeded_conn)
        update_effectiveness_table(seeded_conn)

        result = seeded_conn.execute(
            "SELECT COUNT(*) FROM brain_effectiveness "
            "WHERE measurement_period = 'all_time'"
        ).fetchone()
        assert result is not None
        assert result[0] == 10  # Not 20


# ---------------------------------------------------------------------------
# Tests: record_check_run
# ---------------------------------------------------------------------------


class TestRecordCheckRun:
    """Test recording individual check runs."""

    def test_inserts_correctly(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Single record_check_run should insert one row."""
        record_check_run(
            conn,
            run_id="run_01",
            signal_id="BIZ.SIZE.market_cap",
            signal_version=1,
            status="TRIGGERED",
            value="$500B",
            evidence="Market cap exceeds threshold",
            ticker="AAPL",
        )

        row = conn.execute(
            "SELECT signal_id, status, value, evidence, ticker, is_backtest "
            "FROM brain_signal_runs WHERE run_id = 'run_01'"
        ).fetchone()
        assert row is not None
        assert row[0] == "BIZ.SIZE.market_cap"
        assert row[1] == "TRIGGERED"
        assert row[2] == "$500B"
        assert row[3] == "Market cap exceeds threshold"
        assert row[4] == "AAPL"
        assert row[5] is False

    def test_backtest_flag(self, conn: duckdb.DuckDBPyConnection) -> None:
        """is_backtest=True should be stored correctly."""
        record_check_run(
            conn,
            run_id="bt_01",
            signal_id="BIZ.SIZE.market_cap",
            signal_version=1,
            status="CLEAR",
            value=None,
            evidence=None,
            ticker="TSLA",
            is_backtest=True,
        )

        row = conn.execute(
            "SELECT is_backtest FROM brain_signal_runs "
            "WHERE run_id = 'bt_01'"
        ).fetchone()
        assert row is not None
        assert row[0] is True


# ---------------------------------------------------------------------------
# Tests: record_signal_runs_batch
# ---------------------------------------------------------------------------


class TestRecordCheckRunsBatch:
    """Test batch recording of check runs."""

    def test_empty_batch(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Empty batch returns 0."""
        count = record_signal_runs_batch(conn, [])
        assert count == 0

    def test_batch_100(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Batch insert of 100 rows should succeed."""
        run_id = str(uuid.uuid4())
        rows = [
            {
                "run_id": run_id,
                "signal_id": f"TEST.BATCH.{i:03d}",
                "signal_version": 1,
                "status": "TRIGGERED" if i % 3 == 0 else "CLEAR",
                "ticker": "BATCH",
                "value": str(i),
                "evidence": f"Test row {i}",
            }
            for i in range(100)
        ]

        count = record_signal_runs_batch(conn, rows)
        assert count == 100

        # Verify rows exist
        result = conn.execute(
            "SELECT COUNT(*) FROM brain_signal_runs WHERE run_id = ?",
            [run_id],
        ).fetchone()
        assert result is not None
        assert result[0] == 100

    def test_batch_with_backtest(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Batch with is_backtest should store correctly."""
        rows = [
            {
                "run_id": "bt_batch",
                "signal_id": "TEST.BT.01",
                "signal_version": 1,
                "status": "TRIGGERED",
                "ticker": "TST",
                "is_backtest": True,
            },
            {
                "run_id": "bt_batch",
                "signal_id": "TEST.BT.02",
                "signal_version": 1,
                "status": "CLEAR",
                "ticker": "TST",
                "is_backtest": False,
            },
        ]
        count = record_signal_runs_batch(conn, rows)
        assert count == 2

        bt_row = conn.execute(
            "SELECT is_backtest FROM brain_signal_runs "
            "WHERE signal_id = 'TEST.BT.01'"
        ).fetchone()
        assert bt_row is not None
        assert bt_row[0] is True

        normal_row = conn.execute(
            "SELECT is_backtest FROM brain_signal_runs "
            "WHERE signal_id = 'TEST.BT.02'"
        ).fetchone()
        assert normal_row is not None
        assert normal_row[0] is False

    def test_batch_defaults(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Batch with minimal fields should use defaults."""
        rows = [
            {
                "run_id": "min_batch",
                "signal_id": "TEST.MIN.01",
                "status": "CLEAR",
                "ticker": "TST",
            }
        ]
        count = record_signal_runs_batch(conn, rows)
        assert count == 1

        row = conn.execute(
            "SELECT signal_version, is_backtest FROM brain_signal_runs "
            "WHERE signal_id = 'TEST.MIN.01'"
        ).fetchone()
        assert row is not None
        assert row[0] == 1  # default signal_version
        assert row[1] is False  # default is_backtest
