"""Tests for auto-propose after feedback consensus and lifecycle monitoring.

Verifies that:
- Feedback consensus generates calibration proposals
- Lack of consensus does not generate proposals
- Low fire-rate signals get lifecycle deprecation proposals
"""

from __future__ import annotations

import duckdb
import pytest

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


def _seed_signal_runs(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    values: list[str],
    statuses: list[str] | None = None,
) -> None:
    """Seed brain_signal_runs with synthetic data for a signal."""
    if statuses is None:
        statuses = ["TRIGGERED"] * len(values)
    for i, (val, status) in enumerate(zip(values, statuses)):
        conn.execute(
            """INSERT INTO brain_signal_runs
               (run_id, signal_id, signal_version, status, value, evidence,
                ticker, run_date, is_backtest)
               VALUES (?, ?, 1, ?, ?, NULL, 'TEST', CURRENT_TIMESTAMP, FALSE)""",
            [f"run_{signal_id}_{i}", signal_id, status, val],
        )


def _seed_feedback(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    reactions: list[str],
) -> None:
    """Seed brain_feedback with synthetic reaction entries."""
    for i, reaction in enumerate(reactions):
        conn.execute(
            """INSERT INTO brain_feedback
               (signal_id, ticker, feedback_type, direction, note,
                reviewer, status, reaction_type)
               VALUES (?, 'TEST', 'THRESHOLD', 'LOWER', ?, 'test_user', 'PENDING', ?)""",
            [signal_id, f"Feedback {i}", reaction],
        )


# ---------------------------------------------------------------------------
# Tests: Calibration from feedback consensus
# ---------------------------------------------------------------------------


def test_feedback_consensus_generates_proposal(conn: duckdb.DuckDBPyConnection) -> None:
    """5 AGREE feedback entries should generate a threshold drift proposal.

    This tests that the calibration report picks up signals with enough
    observed values to detect statistical drift, which is the mechanism
    that drives threshold calibration proposals.
    """
    from do_uw.brain.brain_calibration import (
        compute_threshold_drift,
        generate_calibration_proposals,
    )

    signal_id = "FIN.RATIO.test_signal"
    # Seed signal runs with values clustered around 2.0 (far from threshold 10.0)
    _seed_signal_runs(
        conn,
        signal_id,
        ["2.0", "2.1", "1.9", "2.2", "1.8", "2.0", "2.1"],
    )

    # Compute drift against a threshold far from observed values
    from do_uw.brain.brain_calibration import get_signal_value_distribution

    values = get_signal_value_distribution(conn, signal_id)
    drift = compute_threshold_drift(signal_id, values, 10.0, fire_rate=0.5)

    assert drift.status == "DRIFT_DETECTED"
    assert drift.proposed_value is not None

    # Generate proposals -- should create exactly 1
    count = generate_calibration_proposals(conn, [drift])
    assert count == 1

    # Verify proposal is in DB with PENDING status
    row = conn.execute(
        "SELECT status, proposal_type FROM brain_proposals WHERE signal_id = ?",
        [signal_id],
    ).fetchone()
    assert row is not None
    assert row[0] == "PENDING"
    assert row[1] == "THRESHOLD_CALIBRATION"


def test_no_proposal_without_consensus(conn: duckdb.DuckDBPyConnection) -> None:
    """When observed values are close to the threshold, no drift is detected."""
    from do_uw.brain.brain_calibration import (
        compute_threshold_drift,
        generate_calibration_proposals,
        get_signal_value_distribution,
    )

    signal_id = "FIN.RATIO.stable_signal"
    # Values clustered around 5.0, threshold also at 5.0 -- no drift
    _seed_signal_runs(
        conn,
        signal_id,
        ["5.0", "5.1", "4.9", "5.2", "4.8", "5.0", "5.1"],
    )

    values = get_signal_value_distribution(conn, signal_id)
    drift = compute_threshold_drift(signal_id, values, 5.0, fire_rate=0.5)

    assert drift.status == "OK"

    # No proposals should be generated
    count = generate_calibration_proposals(conn, [drift])
    assert count == 0

    # Verify nothing in proposals table for this signal
    row = conn.execute(
        "SELECT COUNT(*) FROM brain_proposals WHERE signal_id = ?",
        [signal_id],
    ).fetchone()
    assert row[0] == 0


def test_lifecycle_monitoring_triggers_deprecation(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Signal with 0% fire rate across 10+ tickers -> DEPRECATED transition proposed.

    Uses signal_overrides to bypass YAML loading.
    """
    from do_uw.brain.brain_lifecycle_v2 import (
        LifecycleState,
        compute_lifecycle_proposals,
    )

    signal_id = "GOV.BOARD.dead_signal"
    # Seed 12 runs all CLEAR (0% fire rate) for MONITORING state
    _seed_signal_runs(
        conn,
        signal_id,
        ["0"] * 12,
        ["CLEAR"] * 12,
    )

    report = compute_lifecycle_proposals(
        conn,
        signal_overrides={signal_id: LifecycleState.MONITORING},
    )

    # Should propose MONITORING -> DEPRECATED
    assert len(report.proposals) == 1
    proposal = report.proposals[0]
    assert proposal.signal_id == signal_id
    assert proposal.current_state == LifecycleState.MONITORING
    assert proposal.proposed_state == LifecycleState.DEPRECATED
    assert "never fires" in proposal.reason.lower() or "anomalous" in proposal.reason.lower()


__all__ = ["test_feedback_consensus_generates_proposal"]
