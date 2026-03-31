"""Tests for the BacktestRunner: historical state replay and comparison.

Uses synthetic state data and in-memory DuckDB to test backtesting
without requiring real pipeline output files.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from do_uw.knowledge.backtest import (
    BacktestComparison,
    BacktestResult,
    compare_backtests,
    run_backtest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_state_file(tmp_path: Path) -> Path:
    """Create a minimal state.json file for backtesting.

    Constructs a valid AnalysisState with defaults, serializes it,
    and writes to disk. This ensures the fixture stays in sync with
    the AnalysisState model schema.
    """
    from do_uw.models.state import AnalysisState, ExtractedData

    state = AnalysisState(ticker="TEST")
    # Ensure extracted is not None so backtest can run checks
    state.extracted = ExtractedData()

    state_path = tmp_path / "state.json"
    state_path.write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return state_path


@pytest.fixture()
def brain_db_path(tmp_path: Path) -> Path:
    """Create a file-backed brain.duckdb with schema and minimal checks."""
    from do_uw.brain.brain_schema import create_schema

    db_path = tmp_path / "brain.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)

    # Insert a few test checks that will exercise the engine
    for i, prefix in enumerate(["BIZ.SIZE", "FIN.LIQ", "LIT.ACTIVE"], 1):
        signal_id = f"{prefix}.test_check_{i}"
        conn.execute(
            """INSERT INTO brain_signals (
                signal_id, version, name, content_type, lifecycle_state,
                depth, execution_mode, report_section, risk_questions,
                risk_framework_layer, threshold_type, question, field_key,
                required_data, factors,
                created_by, change_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                signal_id,
                1,
                f"Test Check {i}",
                "EVALUATIVE_CHECK",
                "SCORING",
                2,
                "AUTO",
                "company" if i == 1 else "financial" if i == 2 else "litigation",
                [],
                "risk_modifier",
                "tiered",
                f"Test question {i}?",
                None,
                ["SEC_10K"],
                [],
                "test",
                "test insert",
            ],
        )

    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Tests: run_backtest
# ---------------------------------------------------------------------------


class TestRunBacktest:
    """Test the run_backtest function."""

    def test_backtest_nonexistent_file(self) -> None:
        """Backtest with missing state file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="State file not found"):
            run_backtest(Path("/nonexistent/state.json"), record=False)

    def test_backtest_invalid_json(self, tmp_path: Path) -> None:
        """Backtest with invalid JSON raises an error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")

        with pytest.raises((ValueError, json.JSONDecodeError)):
            run_backtest(bad_file, record=False)

    def test_backtest_produces_result(
        self, minimal_state_file: Path, brain_db_path: Path
    ) -> None:
        """Backtest with valid state produces BacktestResult."""
        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            result = run_backtest(minimal_state_file, record=False)

        assert isinstance(result, BacktestResult)
        assert result.ticker == "TEST"
        assert result.state_path == str(minimal_state_file)
        assert result.checks_executed >= 0
        # Sum should equal total
        assert (
            result.triggered + result.clear + result.skipped + result.info
            == result.checks_executed
        )

    def test_backtest_results_by_id_populated(
        self, minimal_state_file: Path, brain_db_path: Path
    ) -> None:
        """Backtest populates results_by_id dict."""
        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            result = run_backtest(minimal_state_file, record=False)

        # Every executed check should have an entry
        assert len(result.results_by_id) == result.checks_executed
        # All values should be valid status strings
        valid_statuses = {"TRIGGERED", "CLEAR", "SKIPPED", "INFO"}
        for status in result.results_by_id.values():
            assert status in valid_statuses, f"Invalid status: {status}"

    def test_backtest_record_true_writes_to_db(
        self, minimal_state_file: Path, brain_db_path: Path
    ) -> None:
        """Backtest with record=True inserts rows into brain_signal_runs."""
        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            result = run_backtest(minimal_state_file, record=True)

        # Verify rows were inserted
        conn = duckdb.connect(str(brain_db_path))
        rows = conn.execute(
            "SELECT COUNT(*) FROM brain_signal_runs WHERE is_backtest = TRUE"
        ).fetchone()[0]
        conn.close()

        assert rows == result.checks_executed

    def test_backtest_record_false_no_db_writes(
        self, minimal_state_file: Path, brain_db_path: Path
    ) -> None:
        """Backtest with record=False does NOT insert rows."""
        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            run_backtest(minimal_state_file, record=False)

        conn = duckdb.connect(str(brain_db_path))
        rows = conn.execute(
            "SELECT COUNT(*) FROM brain_signal_runs WHERE is_backtest = TRUE"
        ).fetchone()[0]
        conn.close()

        assert rows == 0

    def test_backtest_deterministic(
        self, minimal_state_file: Path, brain_db_path: Path
    ) -> None:
        """Running the same backtest twice produces identical results."""
        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            result_a = run_backtest(minimal_state_file, record=False)
            result_b = run_backtest(minimal_state_file, record=False)

        assert result_a.checks_executed == result_b.checks_executed
        assert result_a.triggered == result_b.triggered
        assert result_a.clear == result_b.clear
        assert result_a.skipped == result_b.skipped
        assert result_a.info == result_b.info
        assert result_a.results_by_id == result_b.results_by_id

    def test_backtest_no_extracted_data(self, tmp_path: Path, brain_db_path: Path) -> None:
        """Backtest with state missing extracted data raises ValueError."""
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="EMPTY")
        # extracted is None by default
        state_path = tmp_path / "empty_state.json"
        state_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=brain_db_path,
        ):
            with pytest.raises(ValueError, match="no extracted data"):
                run_backtest(state_path, record=False)


# ---------------------------------------------------------------------------
# Tests: compare_backtests
# ---------------------------------------------------------------------------


class TestCompareBacktests:
    """Test the compare_backtests function."""

    def test_compare_identical(self) -> None:
        """Comparing identical results shows no changes."""
        result = BacktestResult(
            ticker="TEST",
            state_path="/test/state.json",
            checks_executed=3,
            triggered=1,
            clear=1,
            skipped=1,
            results_by_id={
                "CHECK.a": "TRIGGERED",
                "CHECK.b": "CLEAR",
                "CHECK.c": "SKIPPED",
            },
        )

        comparison = compare_backtests(result, result)
        assert isinstance(comparison, BacktestComparison)
        assert len(comparison.changed) == 0
        assert len(comparison.new_checks) == 0
        assert len(comparison.removed_checks) == 0

    def test_compare_status_changes(self) -> None:
        """Comparing different results identifies changed checks."""
        result_a = BacktestResult(
            ticker="TEST",
            state_path="/test",
            checks_executed=3,
            results_by_id={
                "CHECK.a": "TRIGGERED",
                "CHECK.b": "CLEAR",
                "CHECK.c": "SKIPPED",
            },
        )
        result_b = BacktestResult(
            ticker="TEST",
            state_path="/test",
            checks_executed=3,
            results_by_id={
                "CHECK.a": "CLEAR",       # changed
                "CHECK.b": "CLEAR",       # same
                "CHECK.c": "TRIGGERED",   # changed
            },
        )

        comparison = compare_backtests(result_a, result_b)
        assert len(comparison.changed) == 2

        changed_ids = {c["signal_id"] for c in comparison.changed}
        assert "CHECK.a" in changed_ids
        assert "CHECK.c" in changed_ids

        # Verify details
        for change in comparison.changed:
            if change["signal_id"] == "CHECK.a":
                assert change["old_status"] == "TRIGGERED"
                assert change["new_status"] == "CLEAR"

    def test_compare_new_and_removed(self) -> None:
        """Comparing identifies new and removed checks."""
        result_a = BacktestResult(
            ticker="TEST",
            state_path="/test",
            results_by_id={
                "CHECK.a": "TRIGGERED",
                "CHECK.old": "CLEAR",
            },
        )
        result_b = BacktestResult(
            ticker="TEST",
            state_path="/test",
            results_by_id={
                "CHECK.a": "TRIGGERED",
                "CHECK.new": "CLEAR",
            },
        )

        comparison = compare_backtests(result_a, result_b)
        assert "CHECK.new" in comparison.new_checks
        assert "CHECK.old" in comparison.removed_checks
        # CHECK.a is in both, same status => no change
        assert len(comparison.changed) == 0
