"""Tests for brain_lifecycle_v2: 5-state lifecycle machine with transition proposals.

Uses in-memory DuckDB with synthetic brain_signal_runs, brain_feedback,
brain_changelog, brain_proposals data for each scenario.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import duckdb
import pytest

from do_uw.brain.brain_lifecycle_v2 import (
    LifecycleReport,
    LifecycleState,
    TransitionProposal,
    VALID_TRANSITIONS,
    compute_lifecycle_proposals,
    evaluate_transition,
    is_valid_transition,
    normalize_lifecycle_state,
)


# ---------------------------------------------------------------------------
# Fixture: in-memory DuckDB with brain schema subset
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with the tables lifecycle code needs."""
    c = duckdb.connect(":memory:")

    c.execute("CREATE SEQUENCE IF NOT EXISTS proposal_seq START 1")
    c.execute("CREATE SEQUENCE IF NOT EXISTS changelog_seq START 1")
    c.execute("CREATE SEQUENCE IF NOT EXISTS feedback_seq START 1")

    c.execute("""
        CREATE TABLE brain_signal_runs (
            run_id VARCHAR NOT NULL,
            signal_id VARCHAR NOT NULL,
            signal_version INTEGER NOT NULL DEFAULT 1,
            status VARCHAR NOT NULL,
            value VARCHAR,
            evidence TEXT,
            ticker VARCHAR NOT NULL,
            run_date TIMESTAMP NOT NULL,
            is_backtest BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (run_id, signal_id)
        )
    """)

    c.execute("""
        CREATE TABLE brain_feedback (
            feedback_id INTEGER PRIMARY KEY DEFAULT nextval('feedback_seq'),
            ticker VARCHAR,
            signal_id VARCHAR,
            run_id VARCHAR,
            feedback_type VARCHAR NOT NULL,
            direction VARCHAR,
            reaction_type VARCHAR,
            note TEXT NOT NULL,
            reviewer VARCHAR NOT NULL DEFAULT 'test',
            status VARCHAR NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    c.execute("""
        CREATE TABLE brain_changelog (
            changelog_id INTEGER DEFAULT nextval('changelog_seq'),
            signal_id VARCHAR NOT NULL,
            old_version INTEGER,
            new_version INTEGER NOT NULL DEFAULT 1,
            change_type VARCHAR NOT NULL,
            change_description TEXT NOT NULL,
            fields_changed VARCHAR[],
            changed_by VARCHAR NOT NULL DEFAULT 'system',
            changed_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            change_reason TEXT,
            triggered_by VARCHAR,
            PRIMARY KEY (changelog_id)
        )
    """)

    c.execute("""
        CREATE TABLE brain_proposals (
            proposal_id INTEGER PRIMARY KEY DEFAULT nextval('proposal_seq'),
            source_type VARCHAR NOT NULL,
            source_ref VARCHAR,
            signal_id VARCHAR,
            proposal_type VARCHAR NOT NULL,
            proposed_check JSON,
            proposed_changes JSON,
            backtest_results JSON,
            rationale TEXT NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'PENDING',
            reviewed_by VARCHAR,
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    return c


# ---------------------------------------------------------------------------
# Helpers: seed data
# ---------------------------------------------------------------------------


def _seed_runs(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    total: int,
    triggered: int,
    start_date: datetime | None = None,
) -> None:
    """Seed brain_signal_runs with given total/triggered counts."""
    if start_date is None:
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for i in range(total):
        status = "TRIGGERED" if i < triggered else "CLEAR"
        run_date = start_date + timedelta(days=i)
        conn.execute(
            "INSERT INTO brain_signal_runs (run_id, signal_id, status, ticker, run_date) "
            "VALUES (?, ?, ?, 'TEST', ?)",
            [f"run_{signal_id}_{i}", signal_id, status, run_date],
        )


def _seed_disagree_feedback(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    count: int,
) -> None:
    """Seed DISAGREE feedback entries."""
    for i in range(count):
        conn.execute(
            "INSERT INTO brain_feedback (signal_id, feedback_type, reaction_type, note, status) "
            "VALUES (?, 'SIGNAL_REACTION', 'DISAGREE', 'Test disagree', 'PENDING')",
            [signal_id],
        )


def _seed_lifecycle_change(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    change_type: str,
    days_ago: int,
) -> None:
    """Seed a changelog entry for lifecycle transition from days_ago."""
    changed_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    conn.execute(
        "INSERT INTO brain_changelog (signal_id, change_type, change_description, changed_at) "
        "VALUES (?, ?, 'test lifecycle change', ?)",
        [signal_id, change_type, changed_at],
    )


# ---------------------------------------------------------------------------
# Test: Valid transitions
# ---------------------------------------------------------------------------


class TestValidTransitions:
    """Test is_valid_transition for all allowed and disallowed paths."""

    def test_valid_transitions(self) -> None:
        """All allowed transitions should be accepted."""
        valid_pairs = [
            (LifecycleState.INCUBATING, LifecycleState.ACTIVE),
            (LifecycleState.INCUBATING, LifecycleState.ARCHIVED),
            (LifecycleState.ACTIVE, LifecycleState.MONITORING),
            (LifecycleState.ACTIVE, LifecycleState.DEPRECATED),
            (LifecycleState.MONITORING, LifecycleState.ACTIVE),
            (LifecycleState.MONITORING, LifecycleState.DEPRECATED),
            (LifecycleState.DEPRECATED, LifecycleState.ARCHIVED),
            (LifecycleState.DEPRECATED, LifecycleState.ACTIVE),
        ]
        for from_state, to_state in valid_pairs:
            assert is_valid_transition(from_state, to_state), (
                f"{from_state} -> {to_state} should be valid"
            )

    def test_invalid_transitions(self) -> None:
        """Disallowed transitions should be rejected."""
        invalid_pairs = [
            (LifecycleState.ARCHIVED, LifecycleState.ACTIVE),
            (LifecycleState.ARCHIVED, LifecycleState.MONITORING),
            (LifecycleState.ACTIVE, LifecycleState.INCUBATING),
            (LifecycleState.MONITORING, LifecycleState.INCUBATING),
            (LifecycleState.MONITORING, LifecycleState.ARCHIVED),  # must go through DEPRECATED
        ]
        for from_state, to_state in invalid_pairs:
            assert not is_valid_transition(from_state, to_state), (
                f"{from_state} -> {to_state} should be invalid"
            )

    def test_archived_terminal(self) -> None:
        """No transitions allowed from ARCHIVED state."""
        assert VALID_TRANSITIONS[LifecycleState.ARCHIVED] == set()
        for state in LifecycleState:
            if state != LifecycleState.ARCHIVED:
                assert not is_valid_transition(LifecycleState.ARCHIVED, state)


# ---------------------------------------------------------------------------
# Test: State normalization
# ---------------------------------------------------------------------------


class TestNormalizeState:
    """Test normalize_lifecycle_state for legacy and new values."""

    def test_inactive_mapping(self) -> None:
        """INACTIVE signals should map to DEPRECATED."""
        assert normalize_lifecycle_state("INACTIVE") == LifecycleState.DEPRECATED

    def test_retired_mapping(self) -> None:
        """RETIRED signals should map to ARCHIVED."""
        assert normalize_lifecycle_state("RETIRED") == LifecycleState.ARCHIVED

    def test_implicit_active(self) -> None:
        """Signals without lifecycle_state (None) should be treated as ACTIVE."""
        assert normalize_lifecycle_state(None) == LifecycleState.ACTIVE

    def test_unknown_defaults_active(self) -> None:
        """Unknown values default to ACTIVE (safe default)."""
        assert normalize_lifecycle_state("SOME_UNKNOWN") == LifecycleState.ACTIVE

    def test_valid_states_pass_through(self) -> None:
        """Known v2 states should pass through unchanged."""
        for state in LifecycleState:
            assert normalize_lifecycle_state(state.value) == state


# ---------------------------------------------------------------------------
# Test: Transition evaluation criteria
# ---------------------------------------------------------------------------


class TestEvaluateTransition:
    """Test transition evaluation with synthetic run stats."""

    def test_incubating_to_active(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with 5+ runs, fire rate 30%, 0 DISAGREE -> propose ACTIVE."""
        _seed_runs(conn, "SIG.TEST.incubating", total=10, triggered=3)
        result = evaluate_transition(
            conn,
            "SIG.TEST.incubating",
            LifecycleState.INCUBATING,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.ACTIVE

    def test_incubating_insufficient_runs(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with only 3 runs should NOT propose transition."""
        _seed_runs(conn, "SIG.TEST.few", total=3, triggered=1)
        result = evaluate_transition(
            conn,
            "SIG.TEST.few",
            LifecycleState.INCUBATING,
        )
        assert result is None

    def test_incubating_too_high_fire_rate(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with fire rate > 80% should NOT graduate from INCUBATING."""
        _seed_runs(conn, "SIG.TEST.hot", total=10, triggered=9)
        result = evaluate_transition(
            conn,
            "SIG.TEST.hot",
            LifecycleState.INCUBATING,
        )
        assert result is None

    def test_active_to_monitoring_high_fire(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with fire_rate > 0.80 for 3+ consecutive runs -> MONITORING."""
        # All 5 runs are TRIGGERED (fire rate = 1.0 for last 3)
        _seed_runs(conn, "SIG.TEST.highfire", total=5, triggered=5)
        result = evaluate_transition(
            conn,
            "SIG.TEST.highfire",
            LifecycleState.ACTIVE,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.MONITORING

    def test_active_to_monitoring_low_fire(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with fire_rate < 0.02 for 3+ consecutive runs -> MONITORING."""
        # 100 runs, 0 triggered = 0% fire rate
        _seed_runs(conn, "SIG.TEST.lowfire", total=100, triggered=0)
        result = evaluate_transition(
            conn,
            "SIG.TEST.lowfire",
            LifecycleState.ACTIVE,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.MONITORING

    def test_active_to_monitoring_disagree(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal with 3+ DISAGREE reactions -> MONITORING."""
        _seed_runs(conn, "SIG.TEST.disagree", total=10, triggered=5)
        _seed_disagree_feedback(conn, "SIG.TEST.disagree", 3)
        result = evaluate_transition(
            conn,
            "SIG.TEST.disagree",
            LifecycleState.ACTIVE,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.MONITORING

    def test_monitoring_to_deprecated(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal in MONITORING for 10+ runs, still anomalous -> DEPRECATED."""
        # All 15 runs triggered (fire rate = 1.0, still anomalous)
        _seed_runs(conn, "SIG.TEST.stillanomaly", total=15, triggered=15)
        _seed_lifecycle_change(conn, "SIG.TEST.stillanomaly", "LIFECYCLE_TRANSITION", days_ago=60)
        result = evaluate_transition(
            conn,
            "SIG.TEST.stillanomaly",
            LifecycleState.MONITORING,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.DEPRECATED

    def test_monitoring_to_active_recalibrated(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal in MONITORING with fire rate back in 5-80% -> ACTIVE."""
        _seed_runs(conn, "SIG.TEST.recalibrated", total=20, triggered=6)  # 30% fire rate
        _seed_lifecycle_change(conn, "SIG.TEST.recalibrated", "LIFECYCLE_TRANSITION", days_ago=30)
        result = evaluate_transition(
            conn,
            "SIG.TEST.recalibrated",
            LifecycleState.MONITORING,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.ACTIVE

    def test_deprecated_to_archived(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal in DEPRECATED for 90+ days with no new feedback -> ARCHIVED."""
        _seed_runs(conn, "SIG.TEST.deprecated", total=5, triggered=5)
        _seed_lifecycle_change(conn, "SIG.TEST.deprecated", "LIFECYCLE_TRANSITION", days_ago=100)
        result = evaluate_transition(
            conn,
            "SIG.TEST.deprecated",
            LifecycleState.DEPRECATED,
        )
        assert result is not None
        assert result.proposed_state == LifecycleState.ARCHIVED

    def test_deprecated_to_archived_blocked_by_feedback(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Signal in DEPRECATED with recent feedback should NOT archive."""
        _seed_runs(conn, "SIG.TEST.dep_feedback", total=5, triggered=5)
        _seed_lifecycle_change(conn, "SIG.TEST.dep_feedback", "LIFECYCLE_TRANSITION", days_ago=100)
        # Add recent feedback (objection)
        _seed_disagree_feedback(conn, "SIG.TEST.dep_feedback", 1)
        result = evaluate_transition(
            conn,
            "SIG.TEST.dep_feedback",
            LifecycleState.DEPRECATED,
        )
        assert result is None

    def test_archived_no_transition(self, conn: duckdb.DuckDBPyConnection) -> None:
        """ARCHIVED signals should never get transition proposals."""
        _seed_runs(conn, "SIG.TEST.archived", total=10, triggered=5)
        result = evaluate_transition(
            conn,
            "SIG.TEST.archived",
            LifecycleState.ARCHIVED,
        )
        assert result is None


# ---------------------------------------------------------------------------
# Test: Proposal generation and report
# ---------------------------------------------------------------------------


class TestProposalGeneration:
    """Test lifecycle proposal writing to brain_proposals."""

    def test_proposal_generation(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Proposals should be written with correct type and changes."""
        from do_uw.brain.brain_lifecycle_v2 import generate_lifecycle_proposals

        proposals = [
            TransitionProposal(
                signal_id="SIG.TEST.one",
                current_state=LifecycleState.INCUBATING,
                proposed_state=LifecycleState.ACTIVE,
                reason="Graduated: 5+ runs, healthy fire rate",
                evidence={"fire_rate": 0.30, "total_runs": 10},
                confidence="HIGH",
            )
        ]
        count = generate_lifecycle_proposals(conn, proposals)
        assert count == 1

        rows = conn.execute(
            "SELECT proposal_type, signal_id, proposed_changes, status "
            "FROM brain_proposals WHERE proposal_type = 'LIFECYCLE_TRANSITION'"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "LIFECYCLE_TRANSITION"
        assert rows[0][1] == "SIG.TEST.one"
        assert rows[0][3] == "PENDING"

        import json
        changes = json.loads(rows[0][2])
        assert changes["from_state"] == "INCUBATING"
        assert changes["to_state"] == "ACTIVE"
        assert changes["lifecycle_state"] == "ACTIVE"

    def test_lifecycle_report_structure(self, conn: duckdb.DuckDBPyConnection) -> None:
        """compute_lifecycle_proposals returns proper LifecycleReport."""
        # Seed an INCUBATING signal with enough runs to propose ACTIVE
        _seed_runs(conn, "SIG.TEST.report", total=10, triggered=3)

        report = compute_lifecycle_proposals(
            conn,
            signal_overrides={"SIG.TEST.report": LifecycleState.INCUBATING},
        )

        assert isinstance(report, LifecycleReport)
        assert report.total_signals_analyzed >= 1
        assert isinstance(report.by_state, dict)
        assert isinstance(report.proposals, list)
        assert isinstance(report.summary, str)
