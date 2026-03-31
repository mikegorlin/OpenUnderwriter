"""Program and policy year CRUD operations for D&O pricing.

Provides the ProgramStore class for managing insurance programs,
policy years, brokers, and carriers. Supports partial data entry
(minimum viable record = just a ticker) with progressive enrichment.

Follows the PricingStore pattern: contextmanager _session, engine
creation, Base.metadata.create_all for table setup.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, sessionmaker

from do_uw.knowledge.models import Base
from do_uw.knowledge.pricing_models_program import (
    Broker,
    Carrier,
    PolicyYear,
    Program,
)
from do_uw.knowledge.pricing_store_converters import (
    broker_to_output,
    build_tower_layer,
    policy_year_to_output,
    program_to_output,
    safe_divide,
)
from do_uw.models.pricing import (
    BrokerInput,
    BrokerOutput,
    CarrierInput,
    EnhancedLayerInput,
    PolicyYearInput,
    PolicyYearOutput,
    ProgramInput,
    ProgramOutput,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).parent / "knowledge.db"


class ProgramStore:
    """CRUD API for D&O insurance programs, policy years, and contacts.

    Manages the program hierarchy: Program -> PolicyYear -> TowerLayer,
    with Broker and Carrier as separate linked entities.

    Args:
        db_path: Path to SQLite database. Use None for in-memory.
            Defaults to knowledge.db in the knowledge package directory.
    """

    def __init__(
        self, db_path: str | Path | None = _DEFAULT_DB_PATH
    ) -> None:
        if db_path is None:
            url = "sqlite://"
        else:
            url = f"sqlite:///{db_path}"
        self._engine: Engine = create_engine(url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """Yield a session with commit/rollback handling."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # -- Program CRUD --

    def add_program(self, program_input: ProgramInput) -> int:
        """Create a D&O insurance program.

        If input.broker is provided (BrokerInput), create or find
        broker first. If input.broker_id is provided, use that.

        Returns:
            The database ID of the created program.
        """
        now = datetime.now(UTC)
        broker_id = program_input.broker_id

        with self._session() as session:
            if program_input.broker is not None and broker_id is None:
                broker_id = self._resolve_broker(
                    session, program_input.broker
                )

            program = Program(
                ticker=program_input.ticker.upper(),
                company_name=program_input.company_name,
                anniversary_month=program_input.anniversary_month,
                anniversary_day=program_input.anniversary_day,
                broker_id=broker_id,
                notes_text=program_input.notes_text,
                created_at=now,
                updated_at=now,
            )
            session.add(program)
            session.flush()
            program_id: int = program.id

        return program_id

    def get_program(
        self, program_id: int
    ) -> ProgramOutput | None:
        """Get program by ID with eager-loaded relationships."""
        with self._session() as session:
            stmt = (
                select(Program)
                .options(
                    joinedload(Program.policy_years),
                    joinedload(Program.broker),
                )
                .where(Program.id == program_id)
            )
            program = (
                session.execute(stmt).unique().scalar_one_or_none()
            )
            if program is None:
                return None
            return program_to_output(program)

    def get_program_by_ticker(
        self, ticker: str
    ) -> ProgramOutput | None:
        """Find program by ticker (most recent if multiple)."""
        with self._session() as session:
            stmt = (
                select(Program)
                .options(
                    joinedload(Program.policy_years),
                    joinedload(Program.broker),
                )
                .where(Program.ticker == ticker.upper())
                .order_by(Program.updated_at.desc())
                .limit(1)
            )
            program = (
                session.execute(stmt).unique().scalar_one_or_none()
            )
            if program is None:
                return None
            return program_to_output(program)

    def list_programs(
        self,
        ticker: str | None = None,
        limit: int = 50,
    ) -> list[ProgramOutput]:
        """List programs, optionally filtered by ticker."""
        with self._session() as session:
            stmt = (
                select(Program)
                .options(
                    joinedload(Program.policy_years),
                    joinedload(Program.broker),
                )
                .order_by(Program.updated_at.desc())
            )
            if ticker is not None:
                stmt = stmt.where(
                    Program.ticker == ticker.upper()
                )
            stmt = stmt.limit(limit)
            programs = list(
                session.execute(stmt).unique().scalars().all()
            )
            return [program_to_output(p) for p in programs]

    # -- Policy Year CRUD --

    def add_policy_year(
        self, program_id: int, py_input: PolicyYearInput
    ) -> int:
        """Add a policy year to a program.

        Creates TowerLayer records from input.layers with
        computed rate_on_line and premium_per_million.

        Returns:
            The database ID of the created policy year.

        Raises:
            ValueError: If program_id does not exist.
        """
        now = datetime.now(UTC)

        # Compute program rate on line if both provided
        rol: float | None = None
        if (
            py_input.total_premium is not None
            and py_input.total_limit is not None
            and py_input.total_limit > 0
        ):
            rol = safe_divide(
                py_input.total_premium, py_input.total_limit
            )

        with self._session() as session:
            program = session.get(Program, program_id)
            if program is None:
                msg = f"Program {program_id} not found"
                raise ValueError(msg)

            policy_year = PolicyYear(
                program_id=program_id,
                policy_year=py_input.policy_year,
                effective_date=py_input.effective_date,
                expiration_date=py_input.expiration_date,
                total_limit=py_input.total_limit,
                total_premium=py_input.total_premium,
                retention=py_input.retention,
                status=py_input.status.value,
                data_completeness=py_input.data_completeness.value,
                source=py_input.source,
                source_document=py_input.source_document,
                program_rate_on_line=rol,
                notes_text=py_input.notes_text,
                created_at=now,
            )
            session.add(policy_year)
            session.flush()
            py_id: int = policy_year.id

            # Create tower layers from enhanced layer inputs
            self._create_layers(
                session, py_input.layers, py_id
            )

        return py_id

    def get_policy_year(
        self, policy_year_id: int
    ) -> PolicyYearOutput | None:
        """Get policy year by ID with eager-loaded layers."""
        with self._session() as session:
            stmt = (
                select(PolicyYear)
                .options(joinedload(PolicyYear.layers))
                .where(PolicyYear.id == policy_year_id)
            )
            py = (
                session.execute(stmt).unique().scalar_one_or_none()
            )
            if py is None:
                return None
            return policy_year_to_output(py)

    def get_program_history(
        self, ticker: str
    ) -> list[PolicyYearOutput]:
        """Get all policy years for a ticker, ordered by year desc.

        Enables year-over-year tracking (D8 requirement).
        """
        with self._session() as session:
            stmt = (
                select(PolicyYear)
                .options(joinedload(PolicyYear.layers))
                .join(
                    Program,
                    PolicyYear.program_id == Program.id,
                )
                .where(Program.ticker == ticker.upper())
                .order_by(PolicyYear.policy_year.desc())
            )
            years = list(
                session.execute(stmt).unique().scalars().all()
            )
            return [policy_year_to_output(py) for py in years]

    # -- Broker CRUD --

    def add_broker(self, broker_input: BrokerInput) -> int:
        """Add a broker record.

        Returns:
            The database ID of the created broker.
        """
        now = datetime.now(UTC)
        with self._session() as session:
            broker = Broker(
                brokerage_name=broker_input.brokerage_name,
                producer_name=broker_input.producer_name,
                email=broker_input.email,
                phone=broker_input.phone,
                notes_text=broker_input.notes_text,
                created_at=now,
            )
            session.add(broker)
            session.flush()
            broker_id: int = broker.id
        return broker_id

    def get_or_create_broker(
        self,
        brokerage_name: str,
        producer_name: str | None = None,
    ) -> int:
        """Find broker by name (case-insensitive), create if not exists.

        Returns:
            The database ID of the found or created broker.
        """
        with self._session() as session:
            stmt = select(Broker).where(
                func.lower(Broker.brokerage_name)
                == brokerage_name.lower()
            )
            broker = session.execute(stmt).scalar_one_or_none()
            if broker is not None:
                return broker.id

            now = datetime.now(UTC)
            new_broker = Broker(
                brokerage_name=brokerage_name,
                producer_name=producer_name,
                created_at=now,
            )
            session.add(new_broker)
            session.flush()
            return new_broker.id

    def list_brokers(
        self, brokerage_name: str | None = None
    ) -> list[BrokerOutput]:
        """List brokers, optionally filtered by brokerage name."""
        with self._session() as session:
            stmt = select(Broker).order_by(
                Broker.brokerage_name
            )
            if brokerage_name is not None:
                stmt = stmt.where(
                    func.lower(Broker.brokerage_name)
                    == brokerage_name.lower()
                )
            brokers = list(session.execute(stmt).scalars().all())
            return [broker_to_output(b) for b in brokers]

    # -- Carrier CRUD --

    def add_carrier(self, carrier_input: CarrierInput) -> int:
        """Add a carrier record.

        Returns:
            The database ID of the created carrier.
        """
        now = datetime.now(UTC)
        with self._session() as session:
            carrier = Carrier(
                carrier_name=carrier_input.carrier_name,
                am_best_rating=carrier_input.am_best_rating,
                appetite_notes=carrier_input.appetite_notes,
                notes_text=carrier_input.notes_text,
                created_at=now,
            )
            session.add(carrier)
            session.flush()
            carrier_id: int = carrier.id
        return carrier_id

    def get_or_create_carrier(self, carrier_name: str) -> int:
        """Find carrier by name (case-insensitive), create if not exists.

        Returns:
            The database ID of the found or created carrier.
        """
        with self._session() as session:
            stmt = select(Carrier).where(
                func.lower(Carrier.carrier_name)
                == carrier_name.lower()
            )
            carrier = session.execute(stmt).scalar_one_or_none()
            if carrier is not None:
                return carrier.id

            now = datetime.now(UTC)
            new_carrier = Carrier(
                carrier_name=carrier_name,
                created_at=now,
            )
            session.add(new_carrier)
            session.flush()
            return new_carrier.id

    # -- Internal helpers --

    def _resolve_broker(
        self, session: Session, broker_input: BrokerInput
    ) -> int:
        """Find or create a broker within an existing session."""
        stmt = select(Broker).where(
            func.lower(Broker.brokerage_name)
            == broker_input.brokerage_name.lower()
        )
        broker = session.execute(stmt).scalar_one_or_none()
        if broker is not None:
            return broker.id

        now = datetime.now(UTC)
        new_broker = Broker(
            brokerage_name=broker_input.brokerage_name,
            producer_name=broker_input.producer_name,
            email=broker_input.email,
            phone=broker_input.phone,
            notes_text=broker_input.notes_text,
            created_at=now,
        )
        session.add(new_broker)
        session.flush()
        return new_broker.id

    def _create_layers(
        self,
        session: Session,
        layers: list[EnhancedLayerInput],
        policy_year_id: int,
    ) -> None:
        """Create TowerLayer records for a policy year.

        Requires a dummy quote_id since tower_layers has a NOT NULL
        FK to quotes. Uses quote_id=0 as a sentinel value for
        program-sourced layers (they have policy_year_id set).
        """
        for layer_input in layers:
            tower = build_tower_layer(layer_input, quote_id=0)
            tower.policy_year_id = policy_year_id
            session.add(tower)
        session.flush()
