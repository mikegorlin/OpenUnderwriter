"""Tests for post-pipeline learning integration.

Verifies that run_post_pipeline_learning:
- Returns expected dict structure
- Never raises (catches exceptions gracefully)
- Logs fire-rate alerts at WARNING level
- Generates proposals without auto-applying them
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from do_uw.brain.brain_schema import create_schema


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def brain_db(tmp_path):
    """Create a temp DuckDB with brain schema, return its path."""
    db_path = tmp_path / "brain.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_pipeline_generates_proposals(brain_db):
    """run_post_pipeline_learning returns dict with expected keys."""
    with patch(
        "do_uw.brain.brain_schema.get_brain_db_path", return_value=brain_db
    ):
        from do_uw.brain.post_pipeline import run_post_pipeline_learning

        result = run_post_pipeline_learning("TEST")

    assert isinstance(result, dict)
    assert "drift_proposals" in result
    assert "fire_rate_alerts" in result
    assert "lifecycle_proposals" in result
    assert "total_proposals" in result
    # total_proposals = drift + lifecycle (fire_rate_alerts are logged, not proposals)
    assert result["total_proposals"] == (
        result["drift_proposals"] + result["lifecycle_proposals"]
    )


def test_post_pipeline_never_raises():
    """Learning loop must never raise -- returns empty dict on failure."""
    with patch(
        "do_uw.brain.brain_calibration.compute_calibration_report",
        side_effect=RuntimeError("DB exploded"),
    ):
        from do_uw.brain.post_pipeline import run_post_pipeline_learning

        result = run_post_pipeline_learning("CRASH")

    assert result == {}


def test_post_pipeline_logs_fire_rate_alerts(brain_db, caplog):
    """Fire-rate alerts should be logged at WARNING level."""
    from do_uw.brain.brain_calibration import CalibrationReport, FireRateAlert
    from do_uw.brain.brain_lifecycle_v2 import LifecycleReport

    mock_cal_report = CalibrationReport(
        fire_rate_alerts=[
            FireRateAlert(
                signal_id="FIN.RATIO.high_leverage",
                fire_rate=0.95,
                alert_type="HIGH_FIRE_RATE",
                recommendation="Consider raising threshold",
            ),
            FireRateAlert(
                signal_id="GOV.BOARD.tiny_board",
                fire_rate=0.01,
                alert_type="LOW_FIRE_RATE",
                recommendation="Consider lowering threshold",
            ),
        ],
        total_proposals_generated=0,
    )
    mock_lifecycle_report = LifecycleReport(proposals=[], total_signals_analyzed=0)

    with (
        patch(
            "do_uw.brain.brain_schema.get_brain_db_path", return_value=brain_db
        ),
        patch(
            "do_uw.brain.brain_calibration.compute_calibration_report",
            return_value=mock_cal_report,
        ),
        patch(
            "do_uw.brain.brain_lifecycle_v2.compute_lifecycle_proposals",
            return_value=mock_lifecycle_report,
        ),
    ):
        with caplog.at_level(logging.WARNING, logger="do_uw.brain.post_pipeline"):
            from do_uw.brain.post_pipeline import run_post_pipeline_learning

            result = run_post_pipeline_learning("TEST")

    assert result["fire_rate_alerts"] == 2
    # Check WARNING log messages contain the signal IDs
    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    signal_ids_found = sum(
        1 for msg in warning_messages
        if "FIN.RATIO.high_leverage" in msg or "GOV.BOARD.tiny_board" in msg
    )
    assert signal_ids_found == 2


def test_proposals_not_auto_applied(brain_db):
    """Proposals should be stored in brain_proposals but never auto-applied.

    After running post-pipeline learning, verify proposals exist in the
    brain_proposals table with status=PENDING.
    """
    # Seed some signal run data so calibration has something to analyze
    conn = duckdb.connect(str(brain_db))
    # Insert runs that would trigger lifecycle analysis
    for i in range(10):
        conn.execute(
            """INSERT INTO brain_signal_runs
               (run_id, signal_id, signal_version, status, value, ticker, run_date, is_backtest)
               VALUES (?, 'TEST.SIGNAL.one', 1, 'TRIGGERED', '5.0', 'TEST', CURRENT_TIMESTAMP, FALSE)""",
            [f"run_{i}"],
        )
    conn.close()

    with patch(
        "do_uw.brain.brain_schema.get_brain_db_path", return_value=brain_db
    ):
        from do_uw.brain.post_pipeline import run_post_pipeline_learning

        run_post_pipeline_learning("TEST")

    # Check proposals table: all should be PENDING (not APPLIED)
    conn = duckdb.connect(str(brain_db))
    rows = conn.execute(
        "SELECT status FROM brain_proposals WHERE status != 'PENDING'"
    ).fetchall()
    conn.close()

    assert len(rows) == 0, "No proposals should be auto-applied"


__all__ = [
    "test_post_pipeline_generates_proposals",
    "test_post_pipeline_logs_fire_rate_alerts",
]
