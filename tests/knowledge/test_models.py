"""Tests for knowledge store SQLAlchemy models and schema creation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from do_uw.knowledge.models import (
    Base,
    Check,
    CheckHistory,
    IndustryPlaybook,
    Note,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
)


@pytest.fixture()
def engine() -> object:
    """Create an in-memory SQLite engine with all tables."""
    eng = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine: object) -> Session:
    """Create a session from the engine."""
    with Session(engine) as sess:  # type: ignore[arg-type]
        yield sess


def _now() -> datetime:
    return datetime.now(UTC)


class TestSchemaCreation:
    """Tests for Base.metadata.create_all() schema creation."""

    def test_creates_all_expected_tables(self, engine: object) -> None:
        inspector = inspect(engine)  # type: ignore[arg-type]
        table_names = set(inspector.get_table_names())
        expected = {
            "signals",
            "signal_history",
            "patterns",
            "scoring_rules",
            "red_flags",
            "sectors",
            "notes",
            "industry_playbooks",
        }
        assert expected.issubset(table_names)

    def test_creates_all_model_tables(
        self, engine: object
    ) -> None:
        inspector = inspect(engine)  # type: ignore[arg-type]
        table_names = inspector.get_table_names()
        # At minimum 9 core tables (signals, signal_history, signal_runs, patterns, etc.)
        assert len(table_names) >= 9


class TestCheckModel:
    """Tests for the Check model CRUD operations."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        check = Check(
            id="FIN.DEBT.high_leverage",
            name="High Leverage Ratio",
            section=3,
            pillar="P1_WHAT_WRONG",
            severity="HIGH",
            execution_mode="AUTO",
            status="ACTIVE",
            threshold_type="value",
            threshold_value='{"value": 3.0, "operator": "gt"}',
            required_data=["SEC_10K"],
            data_locations={"SEC_10K": ["item_8_financials"]},
            scoring_factor="F3_financial_health",
            scoring_rule="F3-006",
            output_section="SECT3",
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
            version=1,
        )
        session.add(check)
        session.flush()

        result = session.get(Check, "FIN.DEBT.high_leverage")
        assert result is not None
        assert result.name == "High Leverage Ratio"
        assert result.section == 3
        assert result.severity == "HIGH"
        assert result.required_data == ["SEC_10K"]

    def test_default_status(self, session: Session) -> None:
        now = _now()
        check = Check(
            id="TEST.DEFAULT",
            name="Default Status",
            section=1,
            pillar="P1_WHAT_WRONG",
            required_data=[],
            data_locations={},
            origin="USER_ADDED",
            created_at=now,
            modified_at=now,
        )
        session.add(check)
        session.flush()

        result = session.get(Check, "TEST.DEFAULT")
        assert result is not None
        assert result.status == "ACTIVE"

    def test_repr(self) -> None:
        check = Check(
            id="TEST.REPR",
            name="Repr Test",
            section=1,
            pillar="P1",
            status="ACTIVE",
            required_data=[],
            data_locations={},
            origin="USER_ADDED",
            created_at=_now(),
            modified_at=_now(),
        )
        assert "TEST.REPR" in repr(check)
        assert "Repr Test" in repr(check)


class TestCheckHistoryModel:
    """Tests for the CheckHistory model and FK constraint."""

    def test_insert_with_valid_check_fk(self, session: Session) -> None:
        now = _now()
        check = Check(
            id="HIST.TEST",
            name="History Test",
            section=1,
            pillar="P1_WHAT_WRONG",
            status="ACTIVE",
            required_data=[],
            data_locations={},
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
        )
        session.add(check)
        session.flush()

        history = CheckHistory(
            signal_id="HIST.TEST",
            version=2,
            field_name="status",
            old_value="INCUBATING",
            new_value="ACTIVE",
            changed_at=now,
            changed_by="test_user",
            reason="Passed validation",
        )
        session.add(history)
        session.flush()

        results = (
            session.query(CheckHistory)
            .filter_by(signal_id="HIST.TEST")
            .all()
        )
        assert len(results) == 1
        assert results[0].field_name == "status"

    def test_relationship_navigation(self, session: Session) -> None:
        now = _now()
        check = Check(
            id="REL.TEST",
            name="Relationship Test",
            section=1,
            pillar="P1_WHAT_WRONG",
            status="ACTIVE",
            required_data=[],
            data_locations={},
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
        )
        session.add(check)
        session.flush()

        history = CheckHistory(
            signal_id="REL.TEST",
            version=2,
            field_name="severity",
            old_value="LOW",
            new_value="HIGH",
            changed_at=now,
            changed_by="analyst",
        )
        session.add(history)
        session.flush()

        # Navigate from check to history
        loaded_check = session.get(Check, "REL.TEST")
        assert loaded_check is not None
        assert len(loaded_check.history) == 1
        assert loaded_check.history[0].field_name == "severity"

        # Navigate from history to check
        loaded_history = session.query(CheckHistory).first()
        assert loaded_history is not None
        assert loaded_history.signal.id == "REL.TEST"


class TestPatternModel:
    """Tests for the Pattern model."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        pattern = Pattern(
            id="PATTERN.STOCK.EVENT_COLLAPSE",
            name="Event-Driven Stock Collapse",
            category="stock",
            description="Sudden collapse following adverse event",
            allegation_types=["A", "B"],
            trigger_conditions={"min_drop": 15.0},
            score_impact={"base_points": 10},
            severity_modifier="HIGH",
            status="ACTIVE",
            created_at=now,
            modified_at=now,
        )
        session.add(pattern)
        session.flush()

        result = session.get(Pattern, "PATTERN.STOCK.EVENT_COLLAPSE")
        assert result is not None
        assert result.category == "stock"
        assert result.allegation_types == ["A", "B"]


class TestScoringRuleModel:
    """Tests for the ScoringRule model."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        rule = ScoringRule(
            id="F1-001",
            factor_id="F1_prior_litigation",
            condition="Active securities class action",
            points=20.0,
            triggers_crf="CRF-001",
            created_at=now,
        )
        session.add(rule)
        session.flush()

        result = session.get(ScoringRule, "F1-001")
        assert result is not None
        assert result.points == 20.0
        assert result.triggers_crf == "CRF-001"


class TestRedFlagModel:
    """Tests for the RedFlag model."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        flag = RedFlag(
            id="CRF-1",
            name="Active SCA",
            condition="Active securities class action lawsuit",
            detection_logic="Check litigation status",
            max_tier="WALK",
            max_quality_score=35.0,
            status="ACTIVE",
            created_at=now,
        )
        session.add(flag)
        session.flush()

        result = session.get(RedFlag, "CRF-1")
        assert result is not None
        assert result.max_quality_score == 35.0


class TestSectorModel:
    """Tests for the Sector model."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        sector = Sector(
            sector_code="TECH",
            metric_name="short_interest",
            baseline_value=4.5,
            created_at=now,
        )
        session.add(sector)
        session.flush()

        result = session.query(Sector).filter_by(sector_code="TECH").first()
        assert result is not None
        assert result.metric_name == "short_interest"
        assert result.baseline_value == 4.5


class TestNoteModel:
    """Tests for the Note model."""

    def test_insert_without_check(self, session: Session) -> None:
        now = _now()
        note = Note(
            title="Revenue Recognition Risk",
            content="Watch for aggressive revenue recognition practices.",
            tags="revenue,accounting",
            source="Claims study 2025",
            created_at=now,
            modified_at=now,
        )
        session.add(note)
        session.flush()

        result = session.query(Note).first()
        assert result is not None
        assert result.title == "Revenue Recognition Risk"
        assert result.signal_id is None

    def test_insert_with_check_fk(self, session: Session) -> None:
        now = _now()
        check = Check(
            id="NOTE.FK.TEST",
            name="FK Test Check",
            section=3,
            pillar="P1_WHAT_WRONG",
            status="ACTIVE",
            required_data=[],
            data_locations={},
            origin="USER_ADDED",
            created_at=now,
            modified_at=now,
        )
        session.add(check)
        session.flush()

        note = Note(
            title="Related Note",
            content="Additional context for this check.",
            signal_id="NOTE.FK.TEST",
            created_at=now,
            modified_at=now,
        )
        session.add(note)
        session.flush()

        # Navigate from check to notes
        loaded_check = session.get(Check, "NOTE.FK.TEST")
        assert loaded_check is not None
        assert len(loaded_check.notes) == 1
        assert loaded_check.notes[0].title == "Related Note"


class TestIndustryPlaybookModel:
    """Tests for the IndustryPlaybook model."""

    def test_insert_and_query(self, session: Session) -> None:
        now = _now()
        playbook = IndustryPlaybook(
            id="TECH_SAAS",
            name="Technology / SaaS",
            description="Playbook for SaaS companies",
            sic_ranges=[[7371, 7379]],
            naics_prefixes=["5112", "5182"],
            check_overrides={"FIN.DEBT.high_leverage": {"threshold": 5.0}},
            scoring_adjustments={"F3_financial_health": {"weight": 0.8}},
            risk_patterns=["recurring_revenue_cliff"],
            claim_theories=["subscription_churn_disclosure"],
            meeting_questions=["SaaS ARR trends?"],
            status="ACTIVE",
            created_at=now,
            modified_at=now,
        )
        session.add(playbook)
        session.flush()

        result = session.get(IndustryPlaybook, "TECH_SAAS")
        assert result is not None
        assert result.name == "Technology / SaaS"
        assert result.sic_ranges == [[7371, 7379]]
        assert result.naics_prefixes == ["5112", "5182"]


class TestFTS5VirtualTable:
    """Tests for FTS5 full-text search availability."""

    def test_fts5_available_on_platform(self) -> None:
        """Check if FTS5 is available in the SQLite build."""
        engine = create_engine("sqlite://", echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA compile_options"))
            options = [row[0] for row in result]
            # FTS5 should be available on macOS Python builds
            if "ENABLE_FTS5" in options:
                # Create FTS5 table to verify it works
                conn.execute(
                    text(
                        "CREATE VIRTUAL TABLE test_fts USING fts5("
                        "content)"
                    )
                )
                conn.execute(
                    text(
                        "INSERT INTO test_fts(content) "
                        "VALUES ('test document')"
                    )
                )
                rows = conn.execute(
                    text(
                        "SELECT * FROM test_fts WHERE test_fts "
                        "MATCH 'test'"
                    )
                ).fetchall()
                assert len(rows) == 1
            else:
                pytest.skip("FTS5 not available in this SQLite build")
