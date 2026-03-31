"""Tests for feedback recording, querying, summary, and CLI commands.

Validates:
- record_feedback inserts into brain_feedback table
- ACCURACY and THRESHOLD feedback with direction
- MISSING_COVERAGE auto-proposes INCUBATING check and proposal
- get_feedback_summary returns correct counts by type
- get_feedback_for_check filters by signal_id
- mark_feedback_applied updates status
- CLI feedback add and summary commands
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from typer.testing import CliRunner

from do_uw.brain.brain_schema import connect_brain_db, create_schema
from do_uw.knowledge.feedback import (
    get_feedback_for_check,
    get_feedback_summary,
    mark_feedback_applied,
    record_feedback,
)
from do_uw.knowledge.feedback_models import FeedbackEntry


@pytest.fixture
def brain_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with brain schema for testing."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    return conn


runner = CliRunner()


# ------------------------------------------------------------------
# Unit tests: record_feedback
# ------------------------------------------------------------------


class TestRecordFeedback:
    """Test feedback recording into brain_feedback table."""

    def test_record_accuracy_feedback(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        entry = FeedbackEntry(
            ticker="AAPL",
            signal_id="FIN.LIQ.current_ratio",
            feedback_type="ACCURACY",
            direction="FALSE_POSITIVE",
            note="Current ratio check triggered but company has strong cash",
            reviewer="john.smith",
        )

        feedback_id = record_feedback(brain_conn, entry)
        assert feedback_id > 0

        # Verify in database
        row = brain_conn.execute(
            "SELECT ticker, signal_id, feedback_type, direction, note, "
            "reviewer, status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "AAPL"
        assert row[1] == "FIN.LIQ.current_ratio"
        assert row[2] == "ACCURACY"
        assert row[3] == "FALSE_POSITIVE"
        assert "strong cash" in row[4]
        assert row[5] == "john.smith"
        assert row[6] == "PENDING"

    def test_record_threshold_feedback(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        entry = FeedbackEntry(
            ticker="TSLA",
            signal_id="FIN.LIQ.debt_equity",
            feedback_type="THRESHOLD",
            direction="TOO_SENSITIVE",
            note="Debt-to-equity threshold too low for growth companies",
            reviewer="analyst_2",
        )

        feedback_id = record_feedback(brain_conn, entry)
        assert feedback_id > 0

        row = brain_conn.execute(
            "SELECT feedback_type, direction FROM brain_feedback "
            "WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "THRESHOLD"
        assert row[1] == "TOO_SENSITIVE"

    def test_record_missing_coverage_auto_proposes(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        entry = FeedbackEntry(
            ticker="AAPL",
            feedback_type="MISSING_COVERAGE",
            note="No check for supply chain concentration risk",
            reviewer="senior.uw",
        )

        feedback_id = record_feedback(brain_conn, entry)
        assert feedback_id > 0

        # Verify feedback row exists
        fb_row = brain_conn.execute(
            "SELECT feedback_type FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert fb_row is not None
        assert fb_row[0] == "MISSING_COVERAGE"

        # Verify proposal was created
        prop_row = brain_conn.execute(
            "SELECT source_type, source_ref, signal_id, proposal_type, status "
            "FROM brain_proposals WHERE source_ref = ?",
            [f"feedback_{feedback_id}"],
        ).fetchone()
        assert prop_row is not None
        assert prop_row[0] == "FEEDBACK"
        assert prop_row[1] == f"feedback_{feedback_id}"
        assert prop_row[2] is not None  # signal_id derived from note
        assert prop_row[3] == "NEW_CHECK"
        assert prop_row[4] == "PENDING"

        # Verify INCUBATING check was inserted
        signal_row = brain_conn.execute(
            "SELECT lifecycle_state FROM brain_signals WHERE signal_id = ?",
            [prop_row[2]],
        ).fetchone()
        assert signal_row is not None
        assert signal_row[0] == "INCUBATING"

        # Verify INCUBATING check is NOT in active view
        active_row = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active WHERE signal_id = ?",
            [prop_row[2]],
        ).fetchone()
        assert active_row is None

    def test_record_feedback_with_run_id(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        entry = FeedbackEntry(
            ticker="MSFT",
            signal_id="GOV.BOARD.independence",
            run_id="run_20260215_001",
            feedback_type="ACCURACY",
            direction="FALSE_NEGATIVE",
            note="Board independence issue was missed",
            reviewer="reviewer_3",
        )

        feedback_id = record_feedback(brain_conn, entry)

        row = brain_conn.execute(
            "SELECT run_id FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "run_20260215_001"


# ------------------------------------------------------------------
# Unit tests: get_feedback_summary
# ------------------------------------------------------------------


class TestGetFeedbackSummary:
    """Test feedback summary aggregation."""

    def test_get_feedback_summary(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        # Insert multiple feedback entries of different types
        for i in range(3):
            record_feedback(
                brain_conn,
                FeedbackEntry(
                    ticker="AAPL",
                    signal_id=f"CHECK.{i}",
                    feedback_type="ACCURACY",
                    note=f"Accuracy feedback {i}",
                ),
            )

        record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="TSLA",
                signal_id="FIN.01",
                feedback_type="THRESHOLD",
                direction="TOO_SENSITIVE",
                note="Threshold too sensitive",
            ),
        )

        for i in range(2):
            record_feedback(
                brain_conn,
                FeedbackEntry(
                    ticker="MSFT",
                    feedback_type="MISSING_COVERAGE",
                    note=f"Missing coverage gap {i}",
                ),
            )

        summary = get_feedback_summary(brain_conn)

        assert summary.pending_accuracy == 3
        assert summary.pending_threshold == 1
        assert summary.pending_coverage_gaps == 2
        # MISSING_COVERAGE auto-generates proposals
        assert summary.pending_proposals >= 2
        assert len(summary.recent_feedback) <= 10
        assert len(summary.recent_feedback) == 6  # 3 + 1 + 2

    def test_empty_feedback_summary(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        summary = get_feedback_summary(brain_conn)
        assert summary.pending_accuracy == 0
        assert summary.pending_threshold == 0
        assert summary.pending_coverage_gaps == 0
        assert summary.pending_proposals == 0
        assert summary.recent_feedback == []
        assert summary.recent_proposals == []


# ------------------------------------------------------------------
# Unit tests: get_feedback_for_check
# ------------------------------------------------------------------


class TestGetFeedbackForCheck:
    """Test feedback retrieval by signal_id."""

    def test_get_feedback_for_check(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        target_check = "LIT.REG.sec_investigation"

        # Insert feedback for target check
        record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="AAPL",
                signal_id=target_check,
                feedback_type="ACCURACY",
                note="False positive on SEC investigation",
                reviewer="analyst_1",
            ),
        )
        record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="TSLA",
                signal_id=target_check,
                feedback_type="THRESHOLD",
                direction="TOO_SENSITIVE",
                note="Threshold too low for this check",
                reviewer="analyst_2",
            ),
        )

        # Insert feedback for a different check
        record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="AAPL",
                signal_id="FIN.LIQ.01",
                feedback_type="ACCURACY",
                note="Different check feedback",
            ),
        )

        entries = get_feedback_for_check(brain_conn, target_check)
        assert len(entries) == 2
        assert all(e.signal_id == target_check for e in entries)


# ------------------------------------------------------------------
# Unit tests: mark_feedback_applied
# ------------------------------------------------------------------


class TestMarkFeedbackApplied:
    """Test marking feedback as applied."""

    def test_mark_feedback_applied(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        feedback_id = record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="AAPL",
                signal_id="FIN.01",
                feedback_type="THRESHOLD",
                direction="TOO_SENSITIVE",
                note="Needs adjustment",
            ),
        )

        # Verify PENDING
        row = brain_conn.execute(
            "SELECT status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "PENDING"

        # Mark applied
        mark_feedback_applied(brain_conn, feedback_id, change_id=42)

        # Verify APPLIED
        row = brain_conn.execute(
            "SELECT status, applied_change_id FROM brain_feedback "
            "WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "APPLIED"
        assert row[1] == 42


# ------------------------------------------------------------------
# CLI tests
# ------------------------------------------------------------------


class TestCLIFeedback:
    """Test CLI feedback commands via CliRunner."""

    def test_cli_feedback_add(self) -> None:
        """Test recording feedback via CLI with mocked DB connection.

        Uses a wrapper that intercepts close() to keep connection alive
        for post-invocation verification.
        """
        real_conn = connect_brain_db(":memory:")
        create_schema(real_conn)

        # Wrapper prevents CLI's conn.close() from killing our test conn
        class _NoCloseConn:
            def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
                self._conn = conn

            def __getattr__(self, name: str) -> Any:
                if name == "close":
                    return lambda: None
                return getattr(self._conn, name)

        wrapper = _NoCloseConn(real_conn)

        with (
            patch(
                "do_uw.brain.brain_schema.get_brain_db_path",
            ) as mock_path,
            patch(
                "do_uw.brain.brain_schema.connect_brain_db",
                return_value=wrapper,
            ),
        ):
            mock_path.return_value = MagicMock()

            from do_uw.cli_feedback import feedback_app

            result = runner.invoke(
                feedback_app,
                [
                    "add", "AAPL",
                    "--check", "LIT.REG.sec_investigation",
                    "--note", "false positive",
                    "--reviewer", "john.smith",
                ],
            )

            assert result.exit_code == 0, result.output
            assert "Feedback recorded (ID:" in result.output

            # Verify feedback was actually recorded in test DB
            row = real_conn.execute(
                "SELECT ticker, signal_id, reviewer FROM brain_feedback LIMIT 1"
            ).fetchone()
            assert row is not None
            assert row[0] == "AAPL"
            assert row[1] == "LIT.REG.sec_investigation"
            assert row[2] == "john.smith"

        real_conn.close()

    def test_cli_feedback_summary(self) -> None:
        """Test summary subcommand via CLI."""
        # Create in-memory conn with some feedback data
        test_conn = connect_brain_db(":memory:")
        create_schema(test_conn)

        # Insert test data
        for i in range(3):
            record_feedback(
                test_conn,
                FeedbackEntry(
                    ticker="AAPL",
                    signal_id=f"CHECK.{i}",
                    feedback_type="ACCURACY",
                    note=f"Test accuracy {i}",
                ),
            )
        record_feedback(
            test_conn,
            FeedbackEntry(
                ticker="TSLA",
                feedback_type="THRESHOLD",
                direction="TOO_SENSITIVE",
                note="Threshold feedback",
            ),
        )

        with (
            patch(
                "do_uw.brain.brain_schema.get_brain_db_path",
            ) as mock_path,
            patch(
                "do_uw.brain.brain_schema.connect_brain_db",
                return_value=test_conn,
            ),
        ):
            mock_path.return_value = MagicMock()

            from do_uw.cli_feedback import feedback_app

            result = runner.invoke(feedback_app, ["summary"])

            assert result.exit_code == 0, result.output
            assert "Accuracy flags:    3" in result.output
            assert "Threshold tuning:  1" in result.output

    def test_cli_feedback_add_invalid_type(self) -> None:
        """Test that invalid feedback type shows error."""
        # Create an in-memory conn for the add command
        test_conn = connect_brain_db(":memory:")
        create_schema(test_conn)

        with (
            patch(
                "do_uw.brain.brain_schema.get_brain_db_path",
            ) as mock_path,
            patch(
                "do_uw.brain.brain_schema.connect_brain_db",
                return_value=test_conn,
            ),
        ):
            mock_path.return_value = MagicMock()

            from do_uw.cli_feedback import feedback_app

            result = runner.invoke(
                feedback_app,
                ["add", "AAPL", "--note", "test", "--type", "INVALID"],
            )

            assert result.exit_code == 1
            assert "Invalid feedback type" in result.output
