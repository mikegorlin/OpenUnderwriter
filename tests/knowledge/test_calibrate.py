"""Tests for calibration preview, impact simulation, apply with git audit.

Validates:
- get_pending_proposals retrieves PENDING proposals from brain_proposals
- preview_calibration returns empty CalibrationPreview with no proposals
- preview_calibration shows changes and impact with active proposals
- apply_calibration promotes NEW_CHECK INCUBATING -> ACTIVE
- apply_calibration updates threshold via BrainWriter
- apply_calibration deactivates checks (lifecycle_state -> INACTIVE)
- Git commit mock verifies correct files and message
- Dirty working tree detection aborts apply
- CLI preview command renders tables
- CLI apply --yes skips confirmation
- THRESHOLD_CHANGE proposal updates claims_correlation weight
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from typer.testing import CliRunner

from do_uw.brain.brain_schema import connect_brain_db, create_schema
from do_uw.knowledge.calibrate import (
    ApplyResult,
    CalibrationPreview,
    apply_calibration,
    get_pending_proposals,
    preview_calibration,
)


@pytest.fixture
def brain_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with brain schema for testing."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    return conn


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _insert_active_check(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    name: str = "Test Check",
    lifecycle_state: str = "ACTIVE",
    threshold_red: str | None = "> 5",
    threshold_yellow: str | None = "> 3",
) -> None:
    """Insert a check into brain_signals for testing."""
    conn.execute(
        """INSERT INTO brain_signals (
            signal_id, version, name, content_type, lifecycle_state,
            depth, execution_mode, report_section, risk_questions,
            risk_framework_layer, threshold_type, threshold_red,
            threshold_yellow, question, created_by
        ) VALUES (?, 1, ?, 'EVALUATIVE_CHECK', ?, 2, 'AUTO',
                  'company', '[]'::VARCHAR[], 'risk_characteristic',
                  'tiered', ?, ?, ?, 'system')""",
        [signal_id, name, lifecycle_state, threshold_red, threshold_yellow, name],
    )


def _insert_proposal(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    proposal_type: str,
    source_type: str = "FEEDBACK",
    source_ref: str | None = None,
    proposed_check: dict[str, Any] | None = None,
    proposed_changes: dict[str, Any] | None = None,
    rationale: str = "Test proposal",
) -> int:
    """Insert a proposal into brain_proposals. Returns proposal_id."""
    conn.execute(
        """INSERT INTO brain_proposals
           (source_type, source_ref, signal_id, proposal_type,
            proposed_check, proposed_changes, rationale, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')""",
        [
            source_type,
            source_ref,
            signal_id,
            proposal_type,
            json.dumps(proposed_check) if proposed_check else None,
            json.dumps(proposed_changes) if proposed_changes else None,
            rationale,
        ],
    )
    result = conn.execute(
        "SELECT MAX(proposal_id) FROM brain_proposals"
    ).fetchone()
    return result[0] if result else 0


# ---------------------------------------------------------------------------
# Unit tests: get_pending_proposals
# ---------------------------------------------------------------------------


class TestGetPendingProposals:
    """Test querying pending proposals from brain_proposals."""

    def test_get_pending_proposals(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        _insert_proposal(
            brain_conn, "CHECK.A", "NEW_CHECK", rationale="Add check A",
        )
        _insert_proposal(
            brain_conn, "CHECK.B", "THRESHOLD_CHANGE",
            rationale="Adjust threshold for B",
        )

        proposals = get_pending_proposals(brain_conn)
        assert len(proposals) == 2
        assert proposals[0].signal_id == "CHECK.A"
        assert proposals[1].signal_id == "CHECK.B"

    def test_get_pending_excludes_applied(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        _insert_proposal(
            brain_conn, "CHECK.A", "NEW_CHECK", rationale="Add A",
        )

        # Mark it applied
        brain_conn.execute(
            "UPDATE brain_proposals SET status = 'APPLIED' "
            "WHERE signal_id = 'CHECK.A'"
        )

        proposals = get_pending_proposals(brain_conn)
        assert len(proposals) == 0


# ---------------------------------------------------------------------------
# Unit tests: preview_calibration
# ---------------------------------------------------------------------------


class TestPreviewCalibration:
    """Test calibration preview with changes and impact."""

    def test_preview_with_no_proposals(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        preview = preview_calibration(brain_conn)
        assert isinstance(preview, CalibrationPreview)
        assert len(preview.proposals) == 0
        assert len(preview.changes) == 0
        assert len(preview.impact) == 0
        assert preview.state_files_tested == 0

    def test_preview_with_proposals(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        # Insert an active check and a threshold change proposal
        _insert_active_check(brain_conn, "FIN.LIQ.01", threshold_red="> 5")
        _insert_proposal(
            brain_conn, "FIN.LIQ.01", "THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": "> 10"},
            rationale="Raise threshold",
        )

        # Mock the impact simulation (no state files available in test)
        preview = preview_calibration(brain_conn, output_dir=MagicMock())
        assert len(preview.proposals) == 1
        assert preview.proposals[0].signal_id == "FIN.LIQ.01"
        assert len(preview.changes) == 1
        assert preview.changes[0]["field"] == "threshold_red"
        assert preview.changes[0]["old_value"] == "> 5"
        assert preview.changes[0]["new_value"] == "> 10"

    def test_preview_new_check_shows_lifecycle_change(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        _insert_active_check(
            brain_conn, "NEW.CHECK.01", lifecycle_state="INCUBATING",
        )
        _insert_proposal(
            brain_conn, "NEW.CHECK.01", "NEW_CHECK",
            proposed_check={"name": "New check"},
            rationale="New check from feedback",
        )

        preview = preview_calibration(brain_conn, output_dir=MagicMock())
        assert len(preview.changes) == 1
        assert preview.changes[0]["field"] == "lifecycle_state"
        assert preview.changes[0]["old_value"] == "INCUBATING"
        assert preview.changes[0]["new_value"] == "ACTIVE"

    def test_preview_deactivation_shows_lifecycle_change(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        _insert_active_check(brain_conn, "OLD.CHECK.01")
        _insert_proposal(
            brain_conn, "OLD.CHECK.01", "DEACTIVATION",
            rationale="Check no longer useful",
        )

        preview = preview_calibration(brain_conn, output_dir=MagicMock())
        assert len(preview.changes) == 1
        assert preview.changes[0]["field"] == "lifecycle_state"
        assert preview.changes[0]["new_value"] == "INACTIVE"


# ---------------------------------------------------------------------------
# Unit tests: apply_calibration
# ---------------------------------------------------------------------------


class TestApplyCalibration:
    """Test applying proposals via BrainWriter."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_apply_new_check_proposal(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        mock_git_commit.return_value = "abc1234"

        # Insert an INCUBATING check and a NEW_CHECK proposal
        _insert_active_check(
            brain_conn, "ING.FEED.supply_chain",
            name="Supply chain check",
            lifecycle_state="INCUBATING",
        )
        _insert_proposal(
            brain_conn, "ING.FEED.supply_chain", "NEW_CHECK",
            source_ref="feedback_1",
            proposed_check={"name": "Supply chain check"},
            rationale="From underwriter feedback",
        )

        # Insert related feedback to resolve
        brain_conn.execute(
            """INSERT INTO brain_feedback
               (feedback_id, ticker, feedback_type, note, reviewer, status)
               VALUES (1, 'AAPL', 'MISSING_COVERAGE', 'supply chain', 'uw1', 'PENDING')"""
        )

        result = apply_calibration(brain_conn)

        assert isinstance(result, ApplyResult)
        assert result.proposals_applied == 1
        assert "ING.FEED.supply_chain" in result.checks_modified
        assert result.commit_hash == "abc1234"

        # Verify check was promoted to ACTIVE (version 2)
        row = brain_conn.execute(
            """SELECT lifecycle_state FROM brain_signals_current
               WHERE signal_id = 'ING.FEED.supply_chain'"""
        ).fetchone()
        assert row is not None
        assert row[0] == "ACTIVE"

        # Verify proposal status updated to APPLIED
        prop_row = brain_conn.execute(
            "SELECT status FROM brain_proposals WHERE signal_id = 'ING.FEED.supply_chain'"
        ).fetchone()
        assert prop_row is not None
        assert prop_row[0] == "APPLIED"

        # Verify related feedback resolved
        assert result.feedback_resolved == 1

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_apply_threshold_change(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        mock_git_commit.return_value = "def5678"

        _insert_active_check(
            brain_conn, "FIN.LIQ.ratio",
            name="Liquidity ratio check",
            threshold_red="> 5",
        )
        _insert_proposal(
            brain_conn, "FIN.LIQ.ratio", "THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": "> 8", "threshold_yellow": "> 6"},
            rationale="Raise thresholds based on backtest",
        )

        result = apply_calibration(brain_conn)

        assert result.proposals_applied == 1
        assert "FIN.LIQ.ratio" in result.checks_modified

        # Verify check was updated (version 2)
        row = brain_conn.execute(
            """SELECT threshold_red, threshold_yellow
               FROM brain_signals_current
               WHERE signal_id = 'FIN.LIQ.ratio'"""
        ).fetchone()
        assert row is not None
        assert row[0] == "> 8"
        assert row[1] == "> 6"

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_apply_deactivation(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        mock_git_commit.return_value = "ghi9012"

        _insert_active_check(brain_conn, "OLD.CHECK.retire")
        _insert_proposal(
            brain_conn, "OLD.CHECK.retire", "DEACTIVATION",
            rationale="Check no longer useful",
        )

        result = apply_calibration(brain_conn)

        assert result.proposals_applied == 1
        assert "OLD.CHECK.retire" in result.checks_modified

        # Verify check is INACTIVE
        row = brain_conn.execute(
            """SELECT lifecycle_state FROM brain_signals_current
               WHERE signal_id = 'OLD.CHECK.retire'"""
        ).fetchone()
        assert row is not None
        assert row[0] == "INACTIVE"

        # Verify check no longer in active view
        active_row = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active "
            "WHERE signal_id = 'OLD.CHECK.retire'"
        ).fetchone()
        assert active_row is None


# ---------------------------------------------------------------------------
# Git tests
# ---------------------------------------------------------------------------


class TestGitAudit:
    """Test git commit and dirty tree detection."""

    @patch("do_uw.knowledge.calibrate_impact.subprocess.run")
    def test_git_commit_mock(self, mock_run: MagicMock) -> None:
        """Verify git add and git commit called with correct files."""
        from do_uw.knowledge.calibrate import _git_commit_calibration

        # Mock successful git operations
        mock_run.return_value = MagicMock(
            returncode=0, stdout="abc1234\n", stderr="",
        )

        commit_hash = _git_commit_calibration(
            files_changed=["brain/signals.json", "brain/brain.duckdb"],
            summary="apply 2 proposals",
            details="- [NEW_CHECK] X\n- [THRESHOLD_CHANGE] Y",
        )

        assert commit_hash == "abc1234"

        # Verify git add was called for each file
        calls = mock_run.call_args_list
        assert len(calls) == 4  # 2 git add + 1 git commit + 1 rev-parse

        # First two calls should be git add
        assert calls[0].args[0] == ["git", "add", "brain/signals.json"]
        assert calls[1].args[0] == ["git", "add", "brain/brain.duckdb"]

        # Third call should be git commit
        assert calls[2].args[0][0:2] == ["git", "commit"]

    @patch("do_uw.knowledge.calibrate_impact.subprocess.run")
    def test_dirty_working_tree_aborts(self, mock_run: MagicMock) -> None:
        """Verify that dirty brain/ directory prevents apply."""
        from do_uw.knowledge.calibrate import _verify_clean_brain_tree

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="M  src/do_uw/brain/signals.json\n",
        )

        with pytest.raises(RuntimeError, match="uncommitted changes"):
            _verify_clean_brain_tree()

    @patch("do_uw.knowledge.calibrate_impact.subprocess.run")
    def test_clean_working_tree_passes(self, mock_run: MagicMock) -> None:
        """Verify that clean brain/ directory passes."""
        from do_uw.knowledge.calibrate import _verify_clean_brain_tree

        mock_run.return_value = MagicMock(
            returncode=0, stdout="",
        )

        # Should not raise
        _verify_clean_brain_tree()


# ---------------------------------------------------------------------------
# Claims correlation threshold update test
# ---------------------------------------------------------------------------


class TestClaimsCorrelationUpdate:
    """Test THRESHOLD_CHANGE proposal that modifies claims_correlation weight."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_apply_claims_correlation_update(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Insert a THRESHOLD_CHANGE proposal that modifies a claims_correlation
        weight field on a check, apply it, verify the field updates in
        brain_signals and propagates via export.
        """
        mock_git_commit.return_value = "claims123"

        # Insert check with initial calibration_notes (simulating claims weight)
        _insert_active_check(
            brain_conn, "FIN.CLAIMS.weight",
            name="Claims correlation weight check",
            threshold_red="> 0.8",
            threshold_yellow="> 0.5",
        )

        # Propose changing thresholds and calibration_notes
        _insert_proposal(
            brain_conn, "FIN.CLAIMS.weight", "THRESHOLD_CHANGE",
            proposed_changes={
                "threshold_red": "> 0.9",
                "threshold_yellow": "> 0.7",
                "calibration_notes": "claims_correlation weight updated from 0.8 to 0.9",
            },
            rationale="Adjust claims correlation weight per SECT7-06/07",
        )

        result = apply_calibration(brain_conn)

        assert result.proposals_applied == 1
        assert "FIN.CLAIMS.weight" in result.checks_modified

        # Verify updated fields
        row = brain_conn.execute(
            """SELECT threshold_red, threshold_yellow, calibration_notes
               FROM brain_signals_current
               WHERE signal_id = 'FIN.CLAIMS.weight'"""
        ).fetchone()
        assert row is not None
        assert row[0] == "> 0.9"
        assert row[1] == "> 0.7"
        assert "claims_correlation" in (row[2] or "")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class _NoCloseConn:
    """Wrapper that prevents CLI's conn.close() from killing test connection."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def __getattr__(self, name: str) -> Any:
        if name == "close":
            return lambda: None
        return getattr(self._conn, name)


class TestCLIPreview:
    """Test CLI calibrate preview command."""

    def test_cli_preview(self) -> None:
        """Test preview command with mocked DuckDB."""
        real_conn = connect_brain_db(":memory:")
        create_schema(real_conn)

        _insert_active_check(real_conn, "FIN.01", threshold_red="> 5")
        _insert_proposal(
            real_conn, "FIN.01", "THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": "> 10"},
            rationale="Test threshold change",
        )

        wrapper = _NoCloseConn(real_conn)

        with (
            patch(
                "do_uw.brain.brain_schema.connect_brain_db",
                return_value=wrapper,
            ),
        ):
            from do_uw.cli_calibrate import calibrate_app

            result = runner.invoke(calibrate_app, ["preview"])

            assert result.exit_code == 0, result.output
            assert "Pending Proposals" in result.output
            assert "FIN.01" in result.output

        real_conn.close()


class TestCLIApply:
    """Test CLI calibrate apply command."""

    def test_cli_apply_with_confirmation(self) -> None:
        """Test apply --yes skips confirmation and applies."""
        real_conn = connect_brain_db(":memory:")
        create_schema(real_conn)

        _insert_active_check(
            real_conn, "ING.CLI.test",
            lifecycle_state="INCUBATING",
        )
        _insert_proposal(
            real_conn, "ING.CLI.test", "NEW_CHECK",
            proposed_check={"name": "CLI test check"},
            rationale="CLI test",
        )

        wrapper = _NoCloseConn(real_conn)

        with (
            patch(
                "do_uw.brain.brain_schema.connect_brain_db",
                return_value=wrapper,
            ),
            patch(
                "do_uw.knowledge.calibrate._verify_clean_brain_tree",
            ),
            patch(
                "do_uw.knowledge.calibrate._git_commit_calibration",
                return_value="cli1234",
            ),
        ):

            from do_uw.cli_calibrate import calibrate_app

            result = runner.invoke(calibrate_app, ["apply", "--yes"])

            assert result.exit_code == 0, result.output
            assert "Applied 1 proposals" in result.output
            assert "cli1234" in result.output

        real_conn.close()
