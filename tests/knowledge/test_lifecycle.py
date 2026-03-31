"""Tests for check lifecycle state machine and history recording."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from do_uw.knowledge.lifecycle import (
    SignalStatus,
    record_field_change,
    transition_signal,
    validate_transition,
)
from do_uw.knowledge.models import Base, Check, CheckHistory


@pytest.fixture()
def session() -> Session:
    """Create an in-memory SQLite session with all tables."""
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess


def _make_check(
    signal_id: str = "TEST.CHECK.001",
    status: str = "INCUBATING",
) -> Check:
    """Create a test check with minimal required fields."""
    now = datetime.now(UTC)
    return Check(
        id=signal_id,
        name="Test Check",
        section=1,
        pillar="P1_WHAT_WRONG",
        status=status,
        required_data=["SEC_10K"],
        data_locations={"SEC_10K": ["item_1_business"]},
        origin="BRAIN_MIGRATION",
        created_at=now,
        modified_at=now,
        version=1,
    )


class TestSignalStatus:
    """Tests for the SignalStatus enum."""

    def test_has_four_states(self) -> None:
        assert len(SignalStatus) == 4

    def test_values(self) -> None:
        assert SignalStatus.INCUBATING == "INCUBATING"
        assert SignalStatus.DEVELOPING == "DEVELOPING"
        assert SignalStatus.ACTIVE == "ACTIVE"
        assert SignalStatus.DEPRECATED == "DEPRECATED"

    def test_is_str_enum(self) -> None:
        assert isinstance(SignalStatus.ACTIVE, str)


class TestValidateTransition:
    """Tests for the validate_transition function."""

    def test_incubating_to_developing(self) -> None:
        assert validate_transition(
            SignalStatus.INCUBATING, SignalStatus.DEVELOPING
        )

    def test_incubating_to_deprecated(self) -> None:
        assert validate_transition(
            SignalStatus.INCUBATING, SignalStatus.DEPRECATED
        )

    def test_developing_to_active(self) -> None:
        assert validate_transition(
            SignalStatus.DEVELOPING, SignalStatus.ACTIVE
        )

    def test_developing_to_incubating(self) -> None:
        assert validate_transition(
            SignalStatus.DEVELOPING, SignalStatus.INCUBATING
        )

    def test_developing_to_deprecated(self) -> None:
        assert validate_transition(
            SignalStatus.DEVELOPING, SignalStatus.DEPRECATED
        )

    def test_active_to_deprecated(self) -> None:
        assert validate_transition(
            SignalStatus.ACTIVE, SignalStatus.DEPRECATED
        )

    def test_deprecated_to_developing(self) -> None:
        """Reactivation path: DEPRECATED -> DEVELOPING."""
        assert validate_transition(
            SignalStatus.DEPRECATED, SignalStatus.DEVELOPING
        )

    def test_incubating_to_active_invalid(self) -> None:
        """Cannot skip DEVELOPING phase."""
        assert not validate_transition(
            SignalStatus.INCUBATING, SignalStatus.ACTIVE
        )

    def test_active_to_incubating_invalid(self) -> None:
        assert not validate_transition(
            SignalStatus.ACTIVE, SignalStatus.INCUBATING
        )

    def test_active_to_developing_invalid(self) -> None:
        assert not validate_transition(
            SignalStatus.ACTIVE, SignalStatus.DEVELOPING
        )

    def test_deprecated_to_active_invalid(self) -> None:
        """Must go through DEVELOPING to reactivate."""
        assert not validate_transition(
            SignalStatus.DEPRECATED, SignalStatus.ACTIVE
        )

    def test_deprecated_to_incubating_invalid(self) -> None:
        assert not validate_transition(
            SignalStatus.DEPRECATED, SignalStatus.INCUBATING
        )

    def test_same_status_invalid(self) -> None:
        for status in SignalStatus:
            assert not validate_transition(status, status)


class TestTransitionCheck:
    """Tests for the transition_signal function."""

    def test_valid_transition_updates_status(self, session: Session) -> None:
        check = _make_check(status="INCUBATING")
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="test_user",
            reason="Ready for development",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.status == "DEVELOPING"

    def test_transition_increments_version(self, session: Session) -> None:
        check = _make_check(status="INCUBATING")
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="test_user",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.version == 2

    def test_transition_creates_history_record(
        self, session: Session
    ) -> None:
        check = _make_check(status="INCUBATING")
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="test_user",
            reason="Starting development",
        )

        history = (
            session.query(CheckHistory)
            .filter_by(signal_id="TEST.CHECK.001")
            .all()
        )
        assert len(history) == 1
        record = history[0]
        assert record.field_name == "status"
        assert record.old_value == "INCUBATING"
        assert record.new_value == "DEVELOPING"
        assert record.changed_by == "test_user"
        assert record.reason == "Starting development"
        assert record.version == 2

    def test_invalid_transition_raises_value_error(
        self, session: Session
    ) -> None:
        check = _make_check(status="INCUBATING")
        session.add(check)
        session.flush()

        with pytest.raises(ValueError, match="Invalid transition"):
            transition_signal(
                session,
                "TEST.CHECK.001",
                SignalStatus.ACTIVE,
                changed_by="test_user",
            )

    def test_check_not_found_raises_value_error(
        self, session: Session
    ) -> None:
        with pytest.raises(ValueError, match="Check not found"):
            transition_signal(
                session,
                "NONEXISTENT.CHECK",
                SignalStatus.DEVELOPING,
                changed_by="test_user",
            )

    def test_full_lifecycle_incubating_to_active(
        self, session: Session
    ) -> None:
        """Test the full happy path: INCUBATING -> DEVELOPING -> ACTIVE."""
        check = _make_check(status="INCUBATING")
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="user1",
            reason="Starting build",
        )
        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.ACTIVE,
            changed_by="user2",
            reason="Passed validation",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.status == "ACTIVE"
        assert updated.version == 3

        history = (
            session.query(CheckHistory)
            .filter_by(signal_id="TEST.CHECK.001")
            .order_by(CheckHistory.id)
            .all()
        )
        assert len(history) == 2

    def test_deprecated_to_developing_reactivation(
        self, session: Session
    ) -> None:
        """Test reactivation path: DEPRECATED -> DEVELOPING."""
        check = _make_check(status="DEPRECATED")
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="test_user",
            reason="Reactivating for new data source",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.status == "DEVELOPING"

    def test_transition_updates_modified_at(self, session: Session) -> None:
        check = _make_check(status="INCUBATING")
        original_modified = check.modified_at
        session.add(check)
        session.flush()

        transition_signal(
            session,
            "TEST.CHECK.001",
            SignalStatus.DEVELOPING,
            changed_by="test_user",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.modified_at >= original_modified


class TestRecordFieldChange:
    """Tests for the record_field_change function."""

    def test_creates_history_entry(self, session: Session) -> None:
        check = _make_check(status="ACTIVE")
        session.add(check)
        session.flush()

        record_field_change(
            session,
            "TEST.CHECK.001",
            field_name="severity",
            old_value="MEDIUM",
            new_value="HIGH",
            changed_by="analyst",
            reason="Upgraded after claim study",
        )

        history = (
            session.query(CheckHistory)
            .filter_by(signal_id="TEST.CHECK.001")
            .all()
        )
        assert len(history) == 1
        record = history[0]
        assert record.field_name == "severity"
        assert record.old_value == "MEDIUM"
        assert record.new_value == "HIGH"
        assert record.changed_by == "analyst"
        assert record.reason == "Upgraded after claim study"

    def test_increments_version(self, session: Session) -> None:
        check = _make_check(status="ACTIVE")
        session.add(check)
        session.flush()

        record_field_change(
            session,
            "TEST.CHECK.001",
            field_name="name",
            old_value="Test Check",
            new_value="Updated Check",
            changed_by="analyst",
        )

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.version == 2

    def test_check_not_found_raises_value_error(
        self, session: Session
    ) -> None:
        with pytest.raises(ValueError, match="Check not found"):
            record_field_change(
                session,
                "NONEXISTENT.CHECK",
                field_name="name",
                old_value="old",
                new_value="new",
                changed_by="analyst",
            )

    def test_multiple_field_changes(self, session: Session) -> None:
        check = _make_check(status="ACTIVE")
        session.add(check)
        session.flush()

        record_field_change(
            session,
            "TEST.CHECK.001",
            field_name="severity",
            old_value="LOW",
            new_value="MEDIUM",
            changed_by="analyst1",
        )
        record_field_change(
            session,
            "TEST.CHECK.001",
            field_name="threshold_value",
            old_value="5.0",
            new_value="3.0",
            changed_by="analyst2",
        )

        history = (
            session.query(CheckHistory)
            .filter_by(signal_id="TEST.CHECK.001")
            .order_by(CheckHistory.id)
            .all()
        )
        assert len(history) == 2
        assert history[0].field_name == "severity"
        assert history[1].field_name == "threshold_value"

        updated = session.get(Check, "TEST.CHECK.001")
        assert updated is not None
        assert updated.version == 3

    def test_nullable_reason(self, session: Session) -> None:
        check = _make_check(status="ACTIVE")
        session.add(check)
        session.flush()

        record_field_change(
            session,
            "TEST.CHECK.001",
            field_name="pillar",
            old_value="P1_WHAT_WRONG",
            new_value="P2_HOW_BAD",
            changed_by="analyst",
            reason=None,
        )

        history = (
            session.query(CheckHistory)
            .filter_by(signal_id="TEST.CHECK.001")
            .all()
        )
        assert len(history) == 1
        assert history[0].reason is None
