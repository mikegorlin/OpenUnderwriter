"""Tests for brain feedback/proposals schema and Pydantic models.

Validates:
- brain_feedback and brain_proposals tables created in DuckDB schema
- INCUBATING checks excluded from brain_signals_active view
- INCUBATING checks can be promoted to ACTIVE via BrainWriter
- DocumentIngestionResult and ProposedCheck models validate/serialize
- FeedbackEntry, ProposalRecord, and FeedbackSummary models validate/serialize
"""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
import pytest

from do_uw.brain.brain_schema import connect_brain_db, create_schema
from do_uw.brain.brain_writer import BrainWriter
from do_uw.knowledge.feedback_models import (
    FeedbackEntry,
    FeedbackSummary,
    ProposalRecord,
)
from do_uw.knowledge.ingestion_models import (
    DocumentIngestionResult,
    IngestionImpactReport,
    ProposedCheck,
)


@pytest.fixture
def brain_conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with brain schema for testing."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    return conn


@pytest.fixture
def brain_writer(brain_conn: duckdb.DuckDBPyConnection) -> BrainWriter:
    """BrainWriter wired to the in-memory test connection."""
    writer = BrainWriter(db_path=":memory:")
    writer._conn = brain_conn  # noqa: SLF001
    return writer


# ------------------------------------------------------------------
# Schema table creation tests
# ------------------------------------------------------------------


class TestSchemaCreation:
    """Verify new tables created by brain schema DDL."""

    def test_schema_creates_feedback_table(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        tables = [
            r[0]
            for r in brain_conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='main'"
            ).fetchall()
        ]
        assert "brain_feedback" in tables

    def test_schema_creates_proposals_table(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        tables = [
            r[0]
            for r in brain_conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='main'"
            ).fetchall()
        ]
        assert "brain_proposals" in tables

    def test_feedback_table_accepts_inserts(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        brain_conn.execute(
            "INSERT INTO brain_feedback "
            "(ticker, signal_id, feedback_type, note, reviewer) "
            "VALUES ('AAPL', 'FIN.LIQ.01', 'ACCURACY', 'False positive', 'tester')"
        )
        row = brain_conn.execute(
            "SELECT ticker, feedback_type, status FROM brain_feedback"
        ).fetchone()
        assert row is not None
        assert row[0] == "AAPL"
        assert row[1] == "ACCURACY"
        assert row[2] == "PENDING"

    def test_proposals_table_accepts_inserts(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        brain_conn.execute(
            "INSERT INTO brain_proposals "
            "(source_type, proposal_type, rationale) "
            "VALUES ('INGESTION', 'NEW_CHECK', 'Test rationale')"
        )
        row = brain_conn.execute(
            "SELECT source_type, status FROM brain_proposals"
        ).fetchone()
        assert row is not None
        assert row[0] == "INGESTION"
        assert row[1] == "PENDING"


# ------------------------------------------------------------------
# INCUBATING lifecycle tests
# ------------------------------------------------------------------


class TestIncubatingLifecycle:
    """Verify INCUBATING checks excluded from active view and promotable."""

    def test_incubating_excluded_from_active(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        brain_conn.execute(
            "INSERT INTO brain_signals "
            "(signal_id, version, name, content_type, lifecycle_state, "
            "report_section, risk_questions, risk_framework_layer, "
            "threshold_type, question) "
            "VALUES ('TEST.INC.1', 1, 'Test Incubating', 'EVALUATIVE_CHECK', "
            "'INCUBATING', '1', ['Q1'], 'inherent_risk', 'boolean', 'Test?')"
        )
        active = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active"
        ).fetchall()
        active_ids = {r[0] for r in active}
        assert "TEST.INC.1" not in active_ids

    def test_incubating_promoted_to_active(
        self,
        brain_conn: duckdb.DuckDBPyConnection,
        brain_writer: BrainWriter,
    ) -> None:
        # Insert check as INCUBATING
        brain_writer.insert_check(
            "TEST.PROM.1",
            {
                "name": "Promotable Check",
                "content_type": "EVALUATIVE_CHECK",
                "lifecycle_state": "INCUBATING",
                "report_section": "company",
                "risk_questions": ["Q1"],
                "risk_framework_layer": "inherent_risk",
                "threshold_type": "boolean",
                "question": "Is this promotable?",
            },
            reason="Testing promotion",
            created_by="test",
        )
        # Verify excluded from active
        active_before = {
            r[0]
            for r in brain_conn.execute(
                "SELECT signal_id FROM brain_signals_active"
            ).fetchall()
        }
        assert "TEST.PROM.1" not in active_before

        # Promote to ACTIVE (which is equivalent to SCORING for visibility)
        brain_writer.promote_check(
            "TEST.PROM.1",
            "SCORING",
            "Approved after review",
            promoted_by="test",
        )
        # Verify now in active view
        active_after = {
            r[0]
            for r in brain_conn.execute(
                "SELECT signal_id FROM brain_signals_active"
            ).fetchall()
        }
        assert "TEST.PROM.1" in active_after

    def test_inactive_excluded_from_active(
        self, brain_conn: duckdb.DuckDBPyConnection
    ) -> None:
        brain_conn.execute(
            "INSERT INTO brain_signals "
            "(signal_id, version, name, content_type, lifecycle_state, "
            "report_section, risk_questions, risk_framework_layer, "
            "threshold_type, question) "
            "VALUES ('TEST.INACT.1', 1, 'Test Inactive', 'EVALUATIVE_CHECK', "
            "'INACTIVE', '1', ['Q1'], 'inherent_risk', 'boolean', 'Test?')"
        )
        active = brain_conn.execute(
            "SELECT signal_id FROM brain_signals_active"
        ).fetchall()
        active_ids = {r[0] for r in active}
        assert "TEST.INACT.1" not in active_ids


# ------------------------------------------------------------------
# Pydantic model validation tests
# ------------------------------------------------------------------


class TestIngestionModels:
    """Verify ingestion Pydantic models validate and serialize."""

    def test_ingestion_models_validate(self) -> None:
        proposed = ProposedCheck(
            signal_id="LIT.NEW.cyber_breach",
            name="Cyber breach disclosure timing",
            threshold_type="tiered",
            threshold_red="> 30 days",
            threshold_yellow="> 14 days",
            threshold_clear="<= 14 days",
            report_section="litigation",
            question="Was the cyber breach disclosed within 14 days?",
            rationale="SEC 8-K requires material cyber incident disclosure within 4 business days",
            field_key="cyber_breach_disclosure_days",
            required_data=["8-K filings", "news coverage"],
            data_source="sec_filings",
        )
        result = DocumentIngestionResult(
            company_ticker="AAPL",
            industry_scope="TECH_SAAS",
            event_type="REGULATORY",
            event_summary="SEC proposes new cyber disclosure rules",
            do_implications=[
                "Directors may face liability for delayed disclosure",
                "Board cyber oversight becomes a D&O exposure factor",
            ],
            affected_checks=["GOV.DISC.cyber", "LIT.REG.sec_investigation"],
            proposed_new_checks=[proposed],
            gap_analysis="No existing check for cyber breach disclosure timing",
            confidence="HIGH",
        )
        # Verify serialization round-trip
        json_str = result.model_dump_json()
        restored = DocumentIngestionResult.model_validate_json(json_str)
        assert restored.event_type == "REGULATORY"
        assert len(restored.proposed_new_checks) == 1
        assert restored.proposed_new_checks[0].signal_id == "LIT.NEW.cyber_breach"
        assert restored.confidence == "HIGH"

    def test_impact_report_validates(self) -> None:
        ingestion_result = DocumentIngestionResult(
            event_type="LITIGATION",
            event_summary="Major SCA filed",
            do_implications=["Increased D&O exposure"],
        )
        report = IngestionImpactReport(
            document_name="sec_complaint_2024.pdf",
            document_type="legal_filing",
            ingestion_result=ingestion_result,
            checks_affected=3,
            gaps_found=1,
            proposals_generated=2,
            summary="3 checks affected, 1 gap found, 2 proposals generated",
        )
        json_str = report.model_dump_json()
        restored = IngestionImpactReport.model_validate_json(json_str)
        assert restored.checks_affected == 3
        assert restored.ingestion_result.event_type == "LITIGATION"

    def test_proposed_signal_defaults(self) -> None:
        check = ProposedCheck(
            signal_id="TEST.01",
            name="Test",
            threshold_type="boolean",
            report_section="company",
            question="Test?",
            rationale="Test rationale",
        )
        assert check.content_type == "EVALUATIVE_CHECK"
        assert check.required_data == []
        assert check.data_source is None
        assert check.threshold_red is None


class TestFeedbackModels:
    """Verify feedback Pydantic models validate and serialize."""

    def test_feedback_models_validate(self) -> None:
        entry = FeedbackEntry(
            feedback_id=1,
            ticker="AAPL",
            signal_id="FIN.LIQ.01",
            run_id="run_20260101",
            feedback_type="ACCURACY",
            direction="FALSE_POSITIVE",
            note="Current ratio check triggered but company has strong cash position",
            reviewer="analyst_1",
            status="PENDING",
            created_at=datetime(2026, 1, 15, tzinfo=UTC),
        )
        proposal = ProposalRecord(
            proposal_id=1,
            source_type="FEEDBACK",
            source_ref="feedback:1",
            signal_id="FIN.LIQ.01",
            proposal_type="THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": "< 0.8", "threshold_yellow": "< 1.2"},
            rationale="Current thresholds too aggressive for large-cap tech",
            status="PENDING",
            created_at=datetime(2026, 1, 15, tzinfo=UTC),
        )
        summary = FeedbackSummary(
            pending_accuracy=5,
            pending_threshold=3,
            pending_coverage_gaps=2,
            pending_proposals=4,
            recent_feedback=[entry],
            recent_proposals=[proposal],
        )
        # Verify serialization round-trip
        json_str = summary.model_dump_json()
        restored = FeedbackSummary.model_validate_json(json_str)
        assert restored.pending_accuracy == 5
        assert len(restored.recent_feedback) == 1
        assert restored.recent_feedback[0].direction == "FALSE_POSITIVE"
        assert len(restored.recent_proposals) == 1
        assert restored.recent_proposals[0].proposal_type == "THRESHOLD_CHANGE"

    def test_feedback_entry_defaults(self) -> None:
        entry = FeedbackEntry(
            feedback_type="MISSING_COVERAGE",
            note="No check for supply chain risk",
        )
        assert entry.reviewer == "anonymous"
        assert entry.status == "PENDING"
        assert entry.ticker is None
        assert entry.direction is None

    def test_proposal_record_defaults(self) -> None:
        proposal = ProposalRecord(
            source_type="PATTERN",
            proposal_type="NEW_CHECK",
            rationale="Pattern detected across multiple runs",
        )
        assert proposal.status == "PENDING"
        assert proposal.proposed_check is None
        assert proposal.backtest_results is None
