"""Tests for Program, PolicyYear, Broker, Carrier ORM models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from do_uw.knowledge.models import Base
from do_uw.knowledge.pricing_models import TowerLayer
from do_uw.knowledge.pricing_models_program import (
    Broker,
    Carrier,
    PolicyYear,
    Program,
)


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture()
def engine() -> object:
    """Create an in-memory SQLite engine with all tables."""
    eng = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine: object) -> Session:
    """Create a session bound to the in-memory engine."""
    with Session(engine) as sess:  # type: ignore[arg-type]
        yield sess  # type: ignore[misc]


class TestBrokerModel:
    """Tests for the Broker ORM model."""

    def test_create_broker_minimal(self, session: Session) -> None:
        broker = Broker(
            brokerage_name="Marsh",
            created_at=_now(),
        )
        session.add(broker)
        session.flush()
        assert broker.id is not None
        assert broker.brokerage_name == "Marsh"
        assert broker.producer_name is None

    def test_create_broker_full(self, session: Session) -> None:
        broker = Broker(
            brokerage_name="Aon",
            producer_name="Jane Smith",
            email="jane@aon.com",
            phone="555-1234",
            notes_text="Key D&O contact",
            created_at=_now(),
        )
        session.add(broker)
        session.flush()
        assert broker.producer_name == "Jane Smith"
        assert broker.email == "jane@aon.com"

    def test_broker_repr(self, session: Session) -> None:
        broker = Broker(
            brokerage_name="WTW",
            producer_name="Bob",
            created_at=_now(),
        )
        session.add(broker)
        session.flush()
        r = repr(broker)
        assert "WTW" in r
        assert "Bob" in r


class TestCarrierModel:
    """Tests for the Carrier ORM model."""

    def test_create_carrier_minimal(self, session: Session) -> None:
        carrier = Carrier(
            carrier_name="Hartford",
            created_at=_now(),
        )
        session.add(carrier)
        session.flush()
        assert carrier.id is not None
        assert carrier.carrier_name == "Hartford"
        assert carrier.am_best_rating is None

    def test_create_carrier_full(self, session: Session) -> None:
        carrier = Carrier(
            carrier_name="Chubb",
            am_best_rating="A++",
            appetite_notes="Growing in tech sector",
            notes_text="Top-tier carrier",
            created_at=_now(),
        )
        session.add(carrier)
        session.flush()
        assert carrier.am_best_rating == "A++"

    def test_carrier_repr(self, session: Session) -> None:
        carrier = Carrier(
            carrier_name="AIG",
            created_at=_now(),
        )
        session.add(carrier)
        session.flush()
        assert "AIG" in repr(carrier)


class TestProgramModel:
    """Tests for the Program ORM model."""

    def test_create_program_minimum_viable(self, session: Session) -> None:
        """Program with just ticker (D2 minimum viable record)."""
        now = _now()
        program = Program(
            ticker="AAPL",
            created_at=now,
            updated_at=now,
        )
        session.add(program)
        session.flush()
        assert program.id is not None
        assert program.ticker == "AAPL"
        assert program.company_name is None
        assert program.anniversary_month is None
        assert program.broker_id is None

    def test_create_program_full(self, session: Session) -> None:
        """Program with all fields including broker relationship."""
        now = _now()
        broker = Broker(brokerage_name="Marsh", created_at=now)
        session.add(broker)
        session.flush()

        program = Program(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            anniversary_month=6,
            anniversary_day=15,
            broker_id=broker.id,
            notes_text="Large tech program",
            created_at=now,
            updated_at=now,
        )
        session.add(program)
        session.flush()
        assert program.company_name == "Microsoft Corporation"
        assert program.anniversary_month == 6
        assert program.broker_id == broker.id

    def test_program_broker_relationship(self, session: Session) -> None:
        now = _now()
        broker = Broker(brokerage_name="Aon", created_at=now)
        session.add(broker)
        session.flush()

        program = Program(
            ticker="GOOG",
            broker_id=broker.id,
            created_at=now,
            updated_at=now,
        )
        session.add(program)
        session.flush()
        session.refresh(program)
        assert program.broker is not None
        assert program.broker.brokerage_name == "Aon"

    def test_program_repr(self, session: Session) -> None:
        now = _now()
        program = Program(
            ticker="TSLA",
            anniversary_month=3,
            anniversary_day=1,
            created_at=now,
            updated_at=now,
        )
        session.add(program)
        session.flush()
        r = repr(program)
        assert "TSLA" in r
        assert "3" in r


class TestPolicyYearModel:
    """Tests for the PolicyYear ORM model."""

    def test_create_policy_year_minimal(self, session: Session) -> None:
        now = _now()
        program = Program(ticker="AAPL", created_at=now, updated_at=now)
        session.add(program)
        session.flush()

        py = PolicyYear(
            program_id=program.id,
            policy_year=2025,
            created_at=now,
        )
        session.add(py)
        session.flush()
        assert py.id is not None
        assert py.policy_year == 2025
        assert py.status == "QUOTED"
        assert py.data_completeness == "FRAGMENT"
        assert py.total_limit is None
        assert py.total_premium is None
        assert py.program_rate_on_line is None

    def test_create_policy_year_full(self, session: Session) -> None:
        now = _now()
        program = Program(ticker="MSFT", created_at=now, updated_at=now)
        session.add(program)
        session.flush()

        py = PolicyYear(
            program_id=program.id,
            policy_year=2024,
            effective_date=now,
            total_limit=50_000_000.0,
            total_premium=500_000.0,
            retention=2_500_000.0,
            status="BOUND",
            data_completeness="COMPLETE",
            source="csv_import",
            source_document="tower_2024.xlsx",
            program_rate_on_line=0.01,
            notes_text="Full tower from broker",
            created_at=now,
        )
        session.add(py)
        session.flush()
        assert py.total_limit == 50_000_000.0
        assert py.status == "BOUND"
        assert py.data_completeness == "COMPLETE"

    def test_policy_year_program_relationship(
        self, session: Session
    ) -> None:
        now = _now()
        program = Program(ticker="GOOG", created_at=now, updated_at=now)
        session.add(program)
        session.flush()

        py = PolicyYear(
            program_id=program.id, policy_year=2025, created_at=now
        )
        session.add(py)
        session.flush()
        session.refresh(py)
        assert py.program.ticker == "GOOG"

    def test_program_policy_years_cascade(self, session: Session) -> None:
        """Deleting a program cascades to policy years."""
        now = _now()
        program = Program(ticker="NFLX", created_at=now, updated_at=now)
        session.add(program)
        session.flush()

        py = PolicyYear(
            program_id=program.id, policy_year=2025, created_at=now
        )
        session.add(py)
        session.flush()

        session.refresh(program)
        assert len(program.policy_years) == 1
        session.delete(program)
        session.flush()
        remaining = session.query(PolicyYear).all()
        assert len(remaining) == 0

    def test_policy_year_repr(self, session: Session) -> None:
        now = _now()
        program = Program(ticker="META", created_at=now, updated_at=now)
        session.add(program)
        session.flush()

        py = PolicyYear(
            program_id=program.id, policy_year=2025, created_at=now
        )
        session.add(py)
        session.flush()
        r = repr(py)
        assert "2025" in r


class TestTowerLayerEnhancements:
    """Tests for the new TowerLayer columns added in Phase 10.1."""

    def test_tower_layer_has_new_columns(self) -> None:
        """TowerLayer should have all new optional columns."""
        assert hasattr(TowerLayer, "layer_type")
        assert hasattr(TowerLayer, "layer_label")
        assert hasattr(TowerLayer, "commission_pct")
        assert hasattr(TowerLayer, "data_source")
        assert hasattr(TowerLayer, "carrier_id")
        assert hasattr(TowerLayer, "policy_year_id")
