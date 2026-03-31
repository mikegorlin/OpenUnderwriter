"""End-to-end knowledge feedback loop validation tests.

Validates the full round-trip for three feedback scenarios:
1. Score Override (ACCURACY feedback -> threshold change proposal -> calibration)
2. False Trigger Report (ACCURACY/FALSE_POSITIVE -> deactivation proposal -> calibration)
3. Data Correction (THRESHOLD feedback -> persistence -> retrieval)

Each scenario demonstrates: submit feedback -> verify DuckDB persistence ->
create calibration proposal -> apply calibration -> verify result changes ->
verify learning persists across sessions.

Also validates document ingestion producing knowledge entries from a real
SEC-style document.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from do_uw.brain.brain_schema import connect_brain_db, create_schema
from do_uw.knowledge.calibrate import (
    ApplyResult,
    apply_calibration,
    get_pending_proposals,
    preview_calibration,
)
from do_uw.knowledge.feedback import (
    get_feedback_for_check,
    get_feedback_summary,
    mark_feedback_applied,
    record_feedback,
)
from do_uw.knowledge.feedback_models import FeedbackEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def brain_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with brain schema for testing."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    return conn


@pytest.fixture
def tmp_brain_db_path(tmp_path: Path) -> Path:
    """Temporary DuckDB file path for session persistence tests."""
    return tmp_path / "test_brain.duckdb"


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
    threshold_clear: str | None = None,
) -> None:
    """Insert a check into brain_signals for testing."""
    conn.execute(
        """INSERT INTO brain_signals (
            signal_id, version, name, content_type, lifecycle_state,
            depth, execution_mode, report_section, risk_questions,
            risk_framework_layer, threshold_type, threshold_red,
            threshold_yellow, threshold_clear, question, created_by
        ) VALUES (?, 1, ?, 'EVALUATIVE_CHECK', ?, 2, 'AUTO',
                  'company', '[]'::VARCHAR[], 'risk_characteristic',
                  'tiered', ?, ?, ?, ?, 'system')""",
        [
            signal_id, name, lifecycle_state,
            threshold_red, threshold_yellow, threshold_clear, name,
        ],
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


# ===========================================================================
# Scenario 1: Score Override Round-Trip
# ===========================================================================


class TestScoreOverrideRoundTrip:
    """Submit 'this company should be HIGH risk not MEDIUM' and verify
    the full feedback -> proposal -> calibration -> result-change loop."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_score_override_round_trip(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Full round-trip: feedback -> persist -> proposal -> calibrate -> verify."""
        mock_git_commit.return_value = "score123"

        # -- Step 1: Submit ACCURACY feedback (score override scenario) --
        # The underwriter says "SEC investigation check should trigger, but it
        # didn't" (FALSE_NEGATIVE = score should be higher/worse)
        entry = FeedbackEntry(
            ticker="AAPL",
            signal_id="LIT.REG.sec_investigation",
            feedback_type="ACCURACY",
            direction="FALSE_NEGATIVE",
            note="Active SEC investigation not captured in scoring - "
                 "company should be HIGH risk not MEDIUM",
            reviewer="senior.underwriter",
        )
        feedback_id = record_feedback(brain_conn, entry)

        # -- Step 2: Verify persistence in brain_feedback table --
        assert feedback_id is not None
        assert feedback_id > 0

        row = brain_conn.execute(
            "SELECT ticker, signal_id, feedback_type, direction, note, "
            "reviewer, status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "AAPL"
        assert row[1] == "LIT.REG.sec_investigation"
        assert row[2] == "ACCURACY"
        assert row[3] == "FALSE_NEGATIVE"
        assert "HIGH risk" in row[4]
        assert row[5] == "senior.underwriter"
        assert row[6] == "PENDING"

        # -- Step 3: Create a calibration proposal (THRESHOLD_CHANGE) --
        # In production, an underwriter would create this via CLI after
        # reviewing the feedback. We simulate the manual proposal creation.
        _insert_active_check(
            brain_conn, "LIT.REG.sec_investigation",
            name="SEC investigation check",
            threshold_red="> 0",  # Only triggers when investigation count > 0
            threshold_yellow=None,
        )
        proposal_id = _insert_proposal(
            brain_conn,
            "LIT.REG.sec_investigation",
            "THRESHOLD_CHANGE",
            source_ref=f"feedback_{feedback_id}",
            proposed_changes={
                "threshold_red": ">= 0",  # Make more sensitive: trigger even for 0
                "calibration_notes": f"Adjusted per feedback {feedback_id}: "
                                     "SEC investigations not being caught",
            },
            rationale="Widen threshold to catch pending investigations "
                      "per underwriter feedback",
        )

        # -- Step 4: Preview calibration shows the change --
        preview = preview_calibration(brain_conn, output_dir=MagicMock())
        assert len(preview.proposals) == 1
        assert preview.proposals[0].signal_id == "LIT.REG.sec_investigation"
        assert len(preview.changes) >= 1
        threshold_change = [
            c for c in preview.changes if c["field"] == "threshold_red"
        ]
        assert len(threshold_change) == 1
        assert threshold_change[0]["old_value"] == "> 0"
        assert threshold_change[0]["new_value"] == ">= 0"

        # -- Step 5: Apply calibration --
        result = apply_calibration(brain_conn, proposal_ids=[proposal_id])
        assert isinstance(result, ApplyResult)
        assert result.proposals_applied == 1
        assert "LIT.REG.sec_investigation" in result.checks_modified

        # -- Step 6: Verify the calibration changed the check --
        updated = brain_conn.execute(
            """SELECT threshold_red, calibration_notes
               FROM brain_signals_current
               WHERE signal_id = 'LIT.REG.sec_investigation'""",
        ).fetchone()
        assert updated is not None
        assert updated[0] == ">= 0"
        assert "feedback" in (updated[1] or "").lower()

        # -- Step 7: Verify feedback was marked APPLIED --
        fb_row = brain_conn.execute(
            "SELECT status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert fb_row is not None
        assert fb_row[0] == "APPLIED"

        # -- Step 8: Verify proposal status updated --
        prop_row = brain_conn.execute(
            "SELECT status FROM brain_proposals WHERE proposal_id = ?",
            [proposal_id],
        ).fetchone()
        assert prop_row is not None
        assert prop_row[0] == "APPLIED"


# ===========================================================================
# Scenario 2: False Trigger Report Round-Trip
# ===========================================================================


class TestFalseTriggerRoundTrip:
    """Report 'BIZ.DEPEND.labor fired incorrectly' and verify check
    gets deactivated through the calibration pipeline."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_false_trigger_round_trip(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Full round-trip: false positive feedback -> deactivation -> verify."""
        mock_git_commit.return_value = "false456"

        # -- Step 1: Submit ACCURACY feedback for false trigger --
        entry = FeedbackEntry(
            ticker="AAPL",
            signal_id="BIZ.DEPEND.labor",
            feedback_type="ACCURACY",
            direction="FALSE_POSITIVE",
            note="Triggered on employee count, not labor dependency metric. "
                 "This check consistently fires incorrectly.",
            reviewer="analyst.jones",
        )
        feedback_id = record_feedback(brain_conn, entry)

        # -- Step 2: Verify persistence --
        assert feedback_id > 0
        row = brain_conn.execute(
            "SELECT feedback_type, direction, signal_id "
            "FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "ACCURACY"
        assert row[1] == "FALSE_POSITIVE"
        assert row[2] == "BIZ.DEPEND.labor"

        # -- Step 3: Multiple false positive reports accumulate --
        feedback_id_2 = record_feedback(
            brain_conn,
            FeedbackEntry(
                ticker="TSLA",
                signal_id="BIZ.DEPEND.labor",
                feedback_type="ACCURACY",
                direction="FALSE_POSITIVE",
                note="Same issue: triggers on headcount, not dependency",
                reviewer="analyst.smith",
            ),
        )
        assert feedback_id_2 > 0

        # Verify both exist for this check
        all_feedback = get_feedback_for_check(brain_conn, "BIZ.DEPEND.labor")
        assert len(all_feedback) == 2
        assert all(f.direction == "FALSE_POSITIVE" for f in all_feedback)

        # -- Step 4: Create deactivation proposal (underwriter decision) --
        _insert_active_check(
            brain_conn, "BIZ.DEPEND.labor",
            name="Labor dependency check",
            lifecycle_state="ACTIVE",
        )
        proposal_id = _insert_proposal(
            brain_conn,
            "BIZ.DEPEND.labor",
            "DEACTIVATION",
            source_ref=f"feedback_{feedback_id}",
            rationale="Multiple false positives reported: fires on employee "
                      "count instead of labor dependency metric",
        )

        # -- Step 5: Apply deactivation --
        result = apply_calibration(brain_conn, proposal_ids=[proposal_id])
        assert result.proposals_applied == 1
        assert "BIZ.DEPEND.labor" in result.checks_modified

        # -- Step 6: Verify check is now INACTIVE --
        signal_row = brain_conn.execute(
            """SELECT lifecycle_state FROM brain_signals_current
               WHERE signal_id = 'BIZ.DEPEND.labor'""",
        ).fetchone()
        assert signal_row is not None
        assert signal_row[0] == "INACTIVE"

        # -- Step 7: Verify check no longer in active view --
        active_row = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active "
            "WHERE signal_id = 'BIZ.DEPEND.labor'",
        ).fetchone()
        assert active_row is None

        # -- Step 8: Verify first feedback marked APPLIED --
        fb_row = brain_conn.execute(
            "SELECT status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert fb_row is not None
        assert fb_row[0] == "APPLIED"


# ===========================================================================
# Scenario 3: Data Correction Round-Trip
# ===========================================================================


class TestDataCorrectionRoundTrip:
    """Submit 'revenue was wrong, here's the real number' and verify
    the correction persists and is retrievable."""

    def test_data_correction_round_trip(
        self,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Full round-trip: data correction feedback -> persist -> retrieve."""

        # -- Step 1: Submit THRESHOLD feedback (data correction scenario) --
        # The underwriter says "the revenue threshold was computed against
        # wrong data -- the real revenue is $394B not $380B"
        entry = FeedbackEntry(
            ticker="AAPL",
            signal_id="FIN.REV.growth",
            feedback_type="THRESHOLD",
            direction="TOO_SENSITIVE",
            note="Revenue was wrong: used $380B but real fiscal year revenue "
                 "is $394.328B. Check fired incorrectly due to stale data. "
                 "Corrected value: 394328000000",
            reviewer="senior.analyst",
        )
        feedback_id = record_feedback(brain_conn, entry)

        # -- Step 2: Verify persistence --
        assert feedback_id > 0
        row = brain_conn.execute(
            "SELECT ticker, signal_id, feedback_type, direction, note, "
            "reviewer, status FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "AAPL"
        assert row[1] == "FIN.REV.growth"
        assert row[2] == "THRESHOLD"
        assert row[3] == "TOO_SENSITIVE"
        assert "394328000000" in row[4]  # Corrected value in note
        assert row[5] == "senior.analyst"
        assert row[6] == "PENDING"

        # -- Step 3: Verify correction is retrievable by signal_id --
        check_feedback = get_feedback_for_check(brain_conn, "FIN.REV.growth")
        assert len(check_feedback) == 1
        assert "394328000000" in check_feedback[0].note

        # -- Step 4: Verify feedback shows up in summary --
        summary = get_feedback_summary(brain_conn)
        assert summary.pending_threshold == 1
        assert len(summary.recent_feedback) == 1

        # -- Step 5: Mark feedback as applied (manual correction applied) --
        mark_feedback_applied(brain_conn, feedback_id, change_id=999)

        # Verify status changed to APPLIED
        applied_row = brain_conn.execute(
            "SELECT status, applied_change_id FROM brain_feedback "
            "WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert applied_row is not None
        assert applied_row[0] == "APPLIED"
        assert applied_row[1] == 999

        # -- Step 6: After applying, pending count drops --
        summary_after = get_feedback_summary(brain_conn)
        assert summary_after.pending_threshold == 0


# ===========================================================================
# Session Persistence Test
# ===========================================================================


class TestLearningPersistsAcrossSessions:
    """Verify DuckDB data survives session boundaries (not just in-memory)."""

    def test_feedback_persists_across_db_reconnect(
        self,
        tmp_brain_db_path: Path,
    ) -> None:
        """Submit feedback, close connection, reopen, verify data still there."""

        # -- Session 1: Submit feedback --
        conn1 = connect_brain_db(tmp_brain_db_path)
        create_schema(conn1)

        entry = FeedbackEntry(
            ticker="AAPL",
            signal_id="FIN.LIQ.current_ratio",
            feedback_type="ACCURACY",
            direction="FALSE_POSITIVE",
            note="Current ratio triggered but company has strong cash reserves",
            reviewer="session_test_user",
        )
        feedback_id = record_feedback(conn1, entry)
        assert feedback_id > 0
        conn1.close()

        # -- Session 2: Reopen and verify --
        conn2 = connect_brain_db(tmp_brain_db_path)
        row = conn2.execute(
            "SELECT ticker, signal_id, feedback_type, note, reviewer, status "
            "FROM brain_feedback WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert row is not None, "Feedback not found after DB reconnect"
        assert row[0] == "AAPL"
        assert row[1] == "FIN.LIQ.current_ratio"
        assert row[2] == "ACCURACY"
        assert "strong cash" in row[3]
        assert row[4] == "session_test_user"
        assert row[5] == "PENDING"
        conn2.close()

    def test_proposal_persists_across_db_reconnect(
        self,
        tmp_brain_db_path: Path,
    ) -> None:
        """Submit MISSING_COVERAGE feedback (auto-proposes), close, reopen,
        verify both feedback and proposal persist."""

        # -- Session 1: Submit feedback that auto-creates proposal --
        conn1 = connect_brain_db(tmp_brain_db_path)
        create_schema(conn1)

        entry = FeedbackEntry(
            ticker="TSLA",
            feedback_type="MISSING_COVERAGE",
            note="No check for executive insider trading patterns",
            reviewer="persistence_test",
        )
        feedback_id = record_feedback(conn1, entry)
        assert feedback_id > 0

        # Verify proposal was created in session 1
        proposals = get_pending_proposals(conn1)
        assert len(proposals) >= 1
        session1_proposal_id = proposals[0].proposal_id
        conn1.close()

        # -- Session 2: Reopen and verify both persist --
        conn2 = connect_brain_db(tmp_brain_db_path)

        # Feedback persists
        fb_row = conn2.execute(
            "SELECT feedback_type, note FROM brain_feedback "
            "WHERE feedback_id = ?",
            [feedback_id],
        ).fetchone()
        assert fb_row is not None, "Feedback not found after reconnect"
        assert fb_row[0] == "MISSING_COVERAGE"
        assert "insider trading" in fb_row[1]

        # Proposal persists
        proposals_2 = get_pending_proposals(conn2)
        assert len(proposals_2) >= 1
        assert proposals_2[0].proposal_id == session1_proposal_id
        conn2.close()

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_calibration_persists_across_sessions(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        tmp_brain_db_path: Path,
    ) -> None:
        """Apply calibration in session 1, verify changes visible in session 2."""
        mock_git_commit.return_value = "persist789"

        # -- Session 1: Insert check, proposal, apply calibration --
        conn1 = connect_brain_db(tmp_brain_db_path)
        create_schema(conn1)

        _insert_active_check(
            conn1, "TEST.PERSIST.check",
            name="Persistence test check",
            threshold_red="> 5",
        )
        proposal_id = _insert_proposal(
            conn1, "TEST.PERSIST.check", "THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": "> 10"},
            rationale="Test persistence of calibration",
        )

        result = apply_calibration(conn1, proposal_ids=[proposal_id])
        assert result.proposals_applied == 1
        conn1.close()

        # -- Session 2: Verify calibration changes persisted --
        conn2 = connect_brain_db(tmp_brain_db_path)
        row = conn2.execute(
            """SELECT threshold_red FROM brain_signals_current
               WHERE signal_id = 'TEST.PERSIST.check'""",
        ).fetchone()
        assert row is not None, "Check not found after reconnect"
        assert row[0] == "> 10", (
            f"Calibration did not persist: expected '> 10', got '{row[0]}'"
        )

        # Proposal should be marked APPLIED
        prop_row = conn2.execute(
            "SELECT status FROM brain_proposals WHERE proposal_id = ?",
            [proposal_id],
        ).fetchone()
        assert prop_row is not None
        assert prop_row[0] == "APPLIED"
        conn2.close()


# ===========================================================================
# Backtest Integration (skip if no state file)
# ===========================================================================


class TestCalibrationAffectsBacktest:
    """After calibration, verify backtest results change."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_deactivation_removes_check_from_active_view(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Deactivating a check removes it from brain_signals_active,
        which is what backtest loads. This verifies the chain:
        calibration -> brain_signals_active view -> backtest visibility."""
        mock_git_commit.return_value = "backtest1"

        # Insert two checks
        _insert_active_check(
            brain_conn, "BT.CHECK.keep",
            name="Check to keep",
        )
        _insert_active_check(
            brain_conn, "BT.CHECK.deactivate",
            name="Check to deactivate",
        )

        # Verify both in active view
        active_before = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active ORDER BY signal_id",
        ).fetchall()
        active_ids_before = {r[0] for r in active_before}
        assert "BT.CHECK.keep" in active_ids_before
        assert "BT.CHECK.deactivate" in active_ids_before

        # Deactivate one via calibration
        proposal_id = _insert_proposal(
            brain_conn, "BT.CHECK.deactivate", "DEACTIVATION",
            rationale="Remove from backtest",
        )
        apply_calibration(brain_conn, proposal_ids=[proposal_id])

        # Verify only one remains in active view
        active_after = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active ORDER BY signal_id",
        ).fetchall()
        active_ids_after = {r[0] for r in active_after}
        assert "BT.CHECK.keep" in active_ids_after
        assert "BT.CHECK.deactivate" not in active_ids_after

    def test_threshold_change_visible_in_signal_data(
        self,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """After a THRESHOLD_CHANGE calibration, the updated thresholds
        are visible when querying brain_signals_active -- the same view
        that backtest's BrainDBLoader reads from."""

        # Insert a check with known thresholds
        _insert_active_check(
            brain_conn, "BT.THRESH.test",
            name="Threshold backtest check",
            threshold_red="> 100",
            threshold_yellow="> 50",
        )

        # Read current threshold from active view
        before = brain_conn.execute(
            "SELECT threshold_red, threshold_yellow FROM brain_signals_active "
            "WHERE signal_id = 'BT.THRESH.test'",
        ).fetchone()
        assert before is not None
        assert before[0] == "> 100"
        assert before[1] == "> 50"

        # Manually apply a threshold update via BrainWriter (same path
        # as apply_calibration uses internally)
        from do_uw.brain.brain_writer import BrainWriter
        writer = BrainWriter(db_path=":memory:")
        writer._conn = brain_conn  # pyright: ignore[reportPrivateUsage]
        writer.update_check(
            "BT.THRESH.test",
            changes={"threshold_red": "> 200", "threshold_yellow": "> 100"},
            reason="Backtest threshold change test",
        )

        # Verify updated thresholds visible in active view
        after = brain_conn.execute(
            "SELECT threshold_red, threshold_yellow FROM brain_signals_active "
            "WHERE signal_id = 'BT.THRESH.test'",
        ).fetchone()
        assert after is not None
        assert after[0] == "> 200"
        assert after[1] == "> 100"


# ===========================================================================
# Document Ingestion Test
# ===========================================================================


class TestDocumentIngestion:
    """Validate document ingestion produces knowledge entries."""

    def test_document_ingestion_produces_knowledge_entries(
        self,
        tmp_path: Path,
    ) -> None:
        """Ingest a structured document and verify knowledge entries
        are created in the knowledge store (SQLite)."""
        from do_uw.knowledge.ingestion import (
            DocumentType,
            ingest_document,
        )
        from do_uw.knowledge.store import KnowledgeStore

        # Create a document with check and note markers that the
        # rule-based extractor will find (in case LLM is unavailable)
        doc_content = """\
# SEC Enforcement Analysis: Widget Corp (WGT)

## KEY FINDINGS

- Widget Corp received a Wells Notice from the SEC Division of Enforcement
- Three independent board members resigned within 6 months
- Revenue restatement of $2.1B across 4 quarters
- CFO sold shares 2 weeks before earnings miss announcement

RISK: Material weakness in internal controls over financial reporting
RISK: Potential Section 11 liability from IPO registration statement
CHECK: Revenue recognition policy changes near quarter-end deadlines

NOTE: Widget Corp's auditor issued a going concern qualification
NOTE: Class action filed in SDNY alleging securities fraud under Rule 10b-5
OBSERVATION: Short interest increased 300% in the month before the restatement

1) Board failed to maintain adequate oversight of financial reporting
2) Insider trading patterns suggest material non-public information leakage
3) Related party transactions with CEO's family members not properly disclosed
"""

        doc_path = tmp_path / "sec_analysis.md"
        doc_path.write_text(doc_content)

        # Use in-memory SQLite knowledge store
        store = KnowledgeStore(db_path=None)

        result = ingest_document(store, doc_path, DocumentType.REGULATORY_GUIDANCE)

        # Verify items were created
        assert result.checks_created > 0, (
            f"Expected checks created > 0, got {result.checks_created}"
        )
        assert result.notes_added > 0, (
            f"Expected notes added > 0, got {result.notes_added}"
        )
        total = result.checks_created + result.notes_added
        assert total >= 5, (
            f"Expected at least 5 knowledge entries, got {total}"
        )

        # Verify checks are queryable from the store
        # Note: some checks may get merged if auto-generated IDs collide
        # (timestamp + id-based), so we check >= 1 rather than exact match
        checks = store.query_checks(status="INCUBATING")
        assert len(checks) >= 1, "No INCUBATING checks found in store"

        # Verify notes are in the store with correct tags
        notes = store.query_notes_by_tag("regulatory")
        assert len(notes) >= result.notes_added

        # Verify entries have required fields
        for note in notes:
            assert note.get("title") is not None
            assert note.get("content") is not None
            assert note.get("source") is not None

    def test_document_ingestion_with_text_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify ingestion also works with .txt files."""
        from do_uw.knowledge.ingestion import (
            DocumentType,
            ingest_document,
        )
        from do_uw.knowledge.store import KnowledgeStore

        doc_content = """\
RISK: High executive turnover indicates governance instability
NOTE: Three CFO changes in 24 months is a major red flag
CHECK: Board independence ratio below 50% threshold
"""

        doc_path = tmp_path / "analysis.txt"
        doc_path.write_text(doc_content)

        store = KnowledgeStore(db_path=None)
        result = ingest_document(store, doc_path, DocumentType.UNDERWRITER_NOTES)

        assert result.checks_created >= 2  # RISK: and CHECK: lines
        assert result.notes_added >= 1  # NOTE: line

    def test_ingestion_rejects_unsupported_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify that unsupported file types raise ValueError."""
        from do_uw.knowledge.ingestion import (
            DocumentType,
            ingest_document,
        )
        from do_uw.knowledge.store import KnowledgeStore

        doc_path = tmp_path / "report.pdf"
        doc_path.write_text("fake pdf content")

        store = KnowledgeStore(db_path=None)
        with pytest.raises(ValueError, match="Unsupported file extension"):
            ingest_document(store, doc_path, DocumentType.GENERAL)


# ===========================================================================
# Missing Coverage Auto-Proposal Round-Trip
# ===========================================================================


class TestMissingCoverageRoundTrip:
    """MISSING_COVERAGE feedback auto-generates a proposal, which can be
    approved and promoted to ACTIVE through calibration."""

    @patch("do_uw.knowledge.calibrate._verify_clean_brain_tree")
    @patch("do_uw.knowledge.calibrate._git_commit_calibration")
    def test_missing_coverage_to_active_check(
        self,
        mock_git_commit: MagicMock,
        mock_verify: MagicMock,
        brain_conn: duckdb.DuckDBPyConnection,
    ) -> None:
        """Full round-trip: MISSING_COVERAGE -> auto-proposal ->
        promote INCUBATING -> ACTIVE."""
        mock_git_commit.return_value = "missing789"

        # -- Step 1: Submit MISSING_COVERAGE feedback --
        entry = FeedbackEntry(
            ticker="AAPL",
            feedback_type="MISSING_COVERAGE",
            note="No check for executive insider trading patterns near earnings",
            reviewer="coverage.analyst",
        )
        feedback_id = record_feedback(brain_conn, entry)
        assert feedback_id > 0

        # -- Step 2: Verify auto-proposal was created --
        proposals = get_pending_proposals(brain_conn)
        assert len(proposals) >= 1

        # Find the proposal linked to our feedback
        our_proposal = None
        for p in proposals:
            if p.source_ref == f"feedback_{feedback_id}":
                our_proposal = p
                break

        assert our_proposal is not None, (
            "No proposal found with source_ref matching feedback"
        )
        assert our_proposal.proposal_type == "NEW_CHECK"
        assert our_proposal.signal_id is not None

        # -- Step 3: Verify INCUBATING check exists (not in active view) --
        signal_id = our_proposal.signal_id
        incubating = brain_conn.execute(
            "SELECT lifecycle_state FROM brain_signals_current "
            "WHERE signal_id = ?",
            [signal_id],
        ).fetchone()
        assert incubating is not None
        assert incubating[0] == "INCUBATING"

        active = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active WHERE signal_id = ?",
            [signal_id],
        ).fetchone()
        assert active is None  # Not yet in active view

        # -- Step 4: Apply proposal (promote to ACTIVE) --
        result = apply_calibration(
            brain_conn,
            proposal_ids=[our_proposal.proposal_id],
        )
        assert result.proposals_applied == 1
        assert signal_id in result.checks_modified

        # -- Step 5: Verify check is now ACTIVE --
        promoted = brain_conn.execute(
            "SELECT lifecycle_state FROM brain_signals_current "
            "WHERE signal_id = ?",
            [signal_id],
        ).fetchone()
        assert promoted is not None
        assert promoted[0] == "ACTIVE"

        # Now visible in active view
        active_after = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active WHERE signal_id = ?",
            [signal_id],
        ).fetchone()
        assert active_after is not None

        # -- Step 6: Verify feedback resolved --
        assert result.feedback_resolved >= 1
