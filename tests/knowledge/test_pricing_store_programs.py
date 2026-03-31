"""Tests for the ProgramStore CRUD API."""

from __future__ import annotations

import pytest

from do_uw.knowledge.pricing_store_programs import ProgramStore
from do_uw.models.pricing import (
    BrokerInput,
    CarrierInput,
    DataSource,
    EnhancedLayerInput,
    LayerType,
    PolicyYearInput,
    ProgramInput,
    QuoteStatus,
)


class TestAddProgram:
    """Test program creation with various input levels."""

    def test_add_program_minimum_viable(self) -> None:
        """Create a program with just a ticker (D2 decision)."""
        store = ProgramStore(db_path=None)
        program_id = store.add_program(
            ProgramInput(ticker="AAPL")
        )
        assert program_id >= 1

        result = store.get_program(program_id)
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.company_name is None
        assert result.broker_id is None
        assert result.policy_years == []

    def test_add_program_with_broker(self) -> None:
        """Create a program with inline BrokerInput."""
        store = ProgramStore(db_path=None)
        program_id = store.add_program(
            ProgramInput(
                ticker="MSFT",
                company_name="Microsoft Corp.",
                anniversary_month=6,
                anniversary_day=15,
                broker=BrokerInput(
                    brokerage_name="Marsh McLennan",
                    producer_name="Jane Smith",
                    email="jane@marsh.com",
                ),
            )
        )

        result = store.get_program(program_id)
        assert result is not None
        assert result.ticker == "MSFT"
        assert result.company_name == "Microsoft Corp."
        assert result.anniversary_month == 6
        assert result.anniversary_day == 15
        assert result.broker_id is not None
        assert result.broker is not None
        assert result.broker.brokerage_name == "Marsh McLennan"
        assert result.broker.producer_name == "Jane Smith"

    def test_add_program_with_broker_id(self) -> None:
        """Create a program referencing an existing broker."""
        store = ProgramStore(db_path=None)
        broker_id = store.add_broker(
            BrokerInput(brokerage_name="Aon")
        )

        program_id = store.add_program(
            ProgramInput(ticker="GOOG", broker_id=broker_id)
        )

        result = store.get_program(program_id)
        assert result is not None
        assert result.broker_id == broker_id

    def test_add_program_ticker_uppercased(self) -> None:
        """Tickers are uppercased on creation."""
        store = ProgramStore(db_path=None)
        pid = store.add_program(ProgramInput(ticker="aapl"))
        result = store.get_program(pid)
        assert result is not None
        assert result.ticker == "AAPL"


class TestGetProgram:
    """Test program retrieval methods."""

    def test_get_program_by_ticker(self) -> None:
        """Find program by ticker."""
        store = ProgramStore(db_path=None)
        store.add_program(
            ProgramInput(
                ticker="AAPL", company_name="Apple Inc."
            )
        )

        result = store.get_program_by_ticker("AAPL")
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.company_name == "Apple Inc."

    def test_get_program_by_ticker_case_insensitive(
        self,
    ) -> None:
        """Ticker lookup is case-insensitive."""
        store = ProgramStore(db_path=None)
        store.add_program(ProgramInput(ticker="AAPL"))

        result = store.get_program_by_ticker("aapl")
        assert result is not None
        assert result.ticker == "AAPL"

    def test_get_nonexistent_program(self) -> None:
        """Getting a nonexistent program returns None."""
        store = ProgramStore(db_path=None)
        assert store.get_program(999) is None
        assert store.get_program_by_ticker("NOPE") is None

    def test_list_programs(self) -> None:
        """List multiple programs, filtered by ticker."""
        store = ProgramStore(db_path=None)
        store.add_program(
            ProgramInput(
                ticker="AAPL", company_name="Apple Inc."
            )
        )
        store.add_program(
            ProgramInput(
                ticker="MSFT", company_name="Microsoft Corp."
            )
        )
        store.add_program(
            ProgramInput(
                ticker="AAPL", company_name="Apple Inc. (v2)"
            )
        )

        all_programs = store.list_programs()
        assert len(all_programs) == 3

        aapl_programs = store.list_programs(ticker="AAPL")
        assert len(aapl_programs) == 2
        assert all(p.ticker == "AAPL" for p in aapl_programs)


class TestAddPolicyYear:
    """Test policy year creation with various data levels."""

    def test_add_policy_year_minimal(self) -> None:
        """Create a policy year with just the year (minimum viable)."""
        store = ProgramStore(db_path=None)
        pid = store.add_program(ProgramInput(ticker="AAPL"))

        py_id = store.add_policy_year(
            pid, PolicyYearInput(policy_year=2025)
        )
        assert py_id >= 1

        result = store.get_policy_year(py_id)
        assert result is not None
        assert result.policy_year == 2025
        assert result.program_id == pid
        assert result.total_limit is None
        assert result.total_premium is None
        assert result.program_rate_on_line is None
        assert result.status == "QUOTED"
        assert result.data_completeness == "FRAGMENT"
        assert result.layers == []

    def test_add_policy_year_with_layers(self) -> None:
        """Create policy year with full tower structure."""
        store = ProgramStore(db_path=None)
        pid = store.add_program(ProgramInput(ticker="MSFT"))

        layers = [
            EnhancedLayerInput(
                layer_type=LayerType.PRIMARY,
                layer_label="Primary ABC",
                layer_number=1,
                attachment_point=0.0,
                limit_amount=5_000_000.0,
                premium=250_000.0,
                carrier_name="CarrierA",
                carrier_rating="A+",
                is_lead=True,
                data_source=DataSource.VERIFIED,
            ),
            EnhancedLayerInput(
                layer_type=LayerType.EXCESS,
                layer_label="1st Excess",
                layer_number=2,
                attachment_point=5_000_000.0,
                limit_amount=5_000_000.0,
                premium=100_000.0,
                carrier_name="CarrierB",
                data_source=DataSource.VERIFIED,
            ),
        ]

        py_id = store.add_policy_year(
            pid,
            PolicyYearInput(
                policy_year=2025,
                total_limit=10_000_000.0,
                total_premium=350_000.0,
                retention=1_000_000.0,
                status=QuoteStatus.BOUND,
                layers=layers,
            ),
        )

        result = store.get_policy_year(py_id)
        assert result is not None
        assert result.policy_year == 2025
        assert result.total_limit == 10_000_000.0
        assert result.total_premium == 350_000.0
        assert result.retention == 1_000_000.0
        assert result.status == "BOUND"
        assert result.program_rate_on_line == pytest.approx(
            0.035
        )
        assert len(result.layers) == 2

        primary = next(
            lyr for lyr in result.layers if lyr.layer_number == 1
        )
        assert primary.rate_on_line == pytest.approx(0.05)
        assert primary.carrier_name == "CarrierA"
        assert primary.is_lead is True

    def test_add_policy_year_partial_layers(self) -> None:
        """Create policy year with layers missing premium/limit."""
        store = ProgramStore(db_path=None)
        pid = store.add_program(ProgramInput(ticker="GOOG"))

        layers = [
            EnhancedLayerInput(
                layer_type=LayerType.PRIMARY,
                layer_number=1,
                carrier_name="CarrierA",
                limit_amount=5_000_000.0,
                # No premium -- partial data
            ),
            EnhancedLayerInput(
                layer_type=LayerType.EXCESS,
                layer_number=2,
                # No limit, no premium, no carrier
            ),
        ]

        py_id = store.add_policy_year(
            pid,
            PolicyYearInput(
                policy_year=2024,
                layers=layers,
            ),
        )

        result = store.get_policy_year(py_id)
        assert result is not None
        assert len(result.layers) == 2

        # Layer 1: has limit but no premium -> ROL=0
        layer1 = next(
            lyr for lyr in result.layers if lyr.layer_number == 1
        )
        assert layer1.limit_amount == 5_000_000.0
        assert layer1.premium == 0.0
        assert layer1.rate_on_line == 0.0

        # Layer 2: no limit, no premium -> all zeros
        layer2 = next(
            lyr for lyr in result.layers if lyr.layer_number == 2
        )
        assert layer2.limit_amount == 0.0
        assert layer2.premium == 0.0
        assert layer2.carrier_name == "TBD"

    def test_add_policy_year_invalid_program(self) -> None:
        """Adding policy year to nonexistent program raises ValueError."""
        store = ProgramStore(db_path=None)
        with pytest.raises(ValueError, match="not found"):
            store.add_policy_year(
                999, PolicyYearInput(policy_year=2025)
            )


class TestGetProgramHistory:
    """Test year-over-year program history queries."""

    def test_get_program_history(self) -> None:
        """Get all policy years for a ticker, ordered desc."""
        store = ProgramStore(db_path=None)
        pid = store.add_program(ProgramInput(ticker="AAPL"))

        store.add_policy_year(
            pid, PolicyYearInput(policy_year=2023)
        )
        store.add_policy_year(
            pid, PolicyYearInput(policy_year=2025)
        )
        store.add_policy_year(
            pid, PolicyYearInput(policy_year=2024)
        )

        history = store.get_program_history("AAPL")
        assert len(history) == 3
        assert history[0].policy_year == 2025
        assert history[1].policy_year == 2024
        assert history[2].policy_year == 2023

    def test_get_program_history_empty(self) -> None:
        """Empty history for a nonexistent ticker."""
        store = ProgramStore(db_path=None)
        assert store.get_program_history("NOPE") == []


class TestBrokerCrud:
    """Test broker CRUD operations."""

    def test_add_broker_and_carrier(self) -> None:
        """Add broker and carrier as standalone records."""
        store = ProgramStore(db_path=None)
        broker_id = store.add_broker(
            BrokerInput(
                brokerage_name="Marsh McLennan",
                producer_name="Jane Smith",
            )
        )
        assert broker_id >= 1

        carrier_id = store.add_carrier(
            CarrierInput(
                carrier_name="AIG",
                am_best_rating="A",
            )
        )
        assert carrier_id >= 1

    def test_get_or_create_broker(self) -> None:
        """Idempotent broker creation."""
        store = ProgramStore(db_path=None)
        id1 = store.get_or_create_broker("Marsh McLennan")
        id2 = store.get_or_create_broker("marsh mclennan")
        id3 = store.get_or_create_broker("MARSH MCLENNAN")

        assert id1 == id2 == id3

    def test_get_or_create_broker_different_names(self) -> None:
        """Different brokerage names create different brokers."""
        store = ProgramStore(db_path=None)
        id1 = store.get_or_create_broker("Marsh McLennan")
        id2 = store.get_or_create_broker("Aon")

        assert id1 != id2

    def test_get_or_create_carrier(self) -> None:
        """Idempotent carrier creation."""
        store = ProgramStore(db_path=None)
        id1 = store.get_or_create_carrier("AIG")
        id2 = store.get_or_create_carrier("aig")
        id3 = store.get_or_create_carrier("AIG")

        assert id1 == id2 == id3

    def test_list_brokers(self) -> None:
        """List brokers with optional name filter."""
        store = ProgramStore(db_path=None)
        store.add_broker(
            BrokerInput(brokerage_name="Marsh McLennan")
        )
        store.add_broker(BrokerInput(brokerage_name="Aon"))
        store.add_broker(BrokerInput(brokerage_name="Willis"))

        all_brokers = store.list_brokers()
        assert len(all_brokers) == 3

        marsh = store.list_brokers(
            brokerage_name="Marsh McLennan"
        )
        assert len(marsh) == 1
        assert marsh[0].brokerage_name == "Marsh McLennan"

    def test_list_brokers_case_insensitive(self) -> None:
        """Broker name filter is case-insensitive."""
        store = ProgramStore(db_path=None)
        store.add_broker(
            BrokerInput(brokerage_name="Marsh McLennan")
        )

        result = store.list_brokers(
            brokerage_name="marsh mclennan"
        )
        assert len(result) == 1
