"""Tests for Pydantic pricing models (enums + input/output models)."""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.pricing import (
    BrokerInput,
    BrokerOutput,
    CarrierInput,
    CarrierOutput,
    DataCompleteness,
    DataSource,
    EnhancedLayerInput,
    LayerType,
    PolicyYearInput,
    PolicyYearOutput,
    ProgramInput,
    ProgramOutput,
    QuoteInput,
    QuoteStatus,
    TowerLayerOutput,
)


def _now() -> datetime:
    return datetime.now(UTC)


class TestLayerTypeEnum:
    """Tests for the LayerType enum."""

    def test_values(self) -> None:
        assert LayerType.PRIMARY == "PRIMARY"
        assert LayerType.EXCESS == "EXCESS"
        assert LayerType.SIDE_A == "SIDE_A"

    def test_from_string(self) -> None:
        assert LayerType("PRIMARY") is LayerType.PRIMARY


class TestDataCompletenessEnum:
    """Tests for the DataCompleteness enum."""

    def test_values(self) -> None:
        assert DataCompleteness.FRAGMENT == "FRAGMENT"
        assert DataCompleteness.PARTIAL == "PARTIAL"
        assert DataCompleteness.COMPLETE == "COMPLETE"


class TestDataSourceEnum:
    """Tests for the DataSource enum."""

    def test_values(self) -> None:
        assert DataSource.VERIFIED == "VERIFIED"
        assert DataSource.INFERRED == "INFERRED"
        assert DataSource.ESTIMATED == "ESTIMATED"
        assert DataSource.AI_EXTRACTED == "AI_EXTRACTED"


class TestBrokerModels:
    """Tests for BrokerInput and BrokerOutput."""

    def test_broker_input_minimal(self) -> None:
        b = BrokerInput(brokerage_name="Marsh")
        assert b.brokerage_name == "Marsh"
        assert b.producer_name is None
        assert b.email is None

    def test_broker_input_full(self) -> None:
        b = BrokerInput(
            brokerage_name="Aon",
            producer_name="Jane Doe",
            email="jane@aon.com",
            phone="555-0100",
            notes_text="Key contact",
        )
        assert b.producer_name == "Jane Doe"

    def test_broker_output(self) -> None:
        b = BrokerOutput(
            id=1,
            brokerage_name="WTW",
            created_at=_now(),
        )
        assert b.id == 1
        assert b.brokerage_name == "WTW"


class TestCarrierModels:
    """Tests for CarrierInput and CarrierOutput."""

    def test_carrier_input_minimal(self) -> None:
        c = CarrierInput(carrier_name="Hartford")
        assert c.carrier_name == "Hartford"
        assert c.am_best_rating is None

    def test_carrier_input_full(self) -> None:
        c = CarrierInput(
            carrier_name="Chubb",
            am_best_rating="A++",
            appetite_notes="Growing in tech",
            notes_text="Top carrier",
        )
        assert c.am_best_rating == "A++"

    def test_carrier_output(self) -> None:
        c = CarrierOutput(
            id=1,
            carrier_name="AIG",
            created_at=_now(),
        )
        assert c.id == 1


class TestEnhancedLayerInput:
    """Tests for EnhancedLayerInput with partial data support."""

    def test_minimal_layer(self) -> None:
        layer = EnhancedLayerInput(
            layer_type=LayerType.PRIMARY,
            layer_number=1,
        )
        assert layer.layer_type == LayerType.PRIMARY
        assert layer.layer_number == 1
        assert layer.limit_amount is None
        assert layer.premium is None
        assert layer.carrier_name is None
        assert layer.data_source == DataSource.VERIFIED

    def test_full_layer(self) -> None:
        layer = EnhancedLayerInput(
            layer_type=LayerType.EXCESS,
            layer_label="1st Excess",
            layer_number=2,
            attachment_point=10_000_000.0,
            limit_amount=10_000_000.0,
            premium=400_000.0,
            carrier_name="Hartford",
            carrier_id=5,
            carrier_rating="A",
            is_lead=True,
            share_pct=100.0,
            commission_pct=10.0,
            data_source=DataSource.AI_EXTRACTED,
            notes_text="Extracted from PDF",
        )
        assert layer.layer_label == "1st Excess"
        assert layer.commission_pct == 10.0
        assert layer.data_source == DataSource.AI_EXTRACTED

    def test_side_a_layer(self) -> None:
        layer = EnhancedLayerInput(
            layer_type=LayerType.SIDE_A,
            layer_label="Lead Side A",
            layer_number=1,
            attachment_point=100_000_000.0,
            limit_amount=10_000_000.0,
        )
        assert layer.layer_type == LayerType.SIDE_A


class TestPolicyYearInput:
    """Tests for PolicyYearInput with partial data support."""

    def test_minimal_policy_year(self) -> None:
        py = PolicyYearInput(policy_year=2025)
        assert py.policy_year == 2025
        assert py.total_limit is None
        assert py.total_premium is None
        assert py.retention is None
        assert py.status == QuoteStatus.QUOTED
        assert py.data_completeness == DataCompleteness.FRAGMENT
        assert py.source == "manual"
        assert py.layers == []

    def test_full_policy_year(self) -> None:
        now = _now()
        py = PolicyYearInput(
            policy_year=2024,
            effective_date=now,
            total_limit=50_000_000.0,
            total_premium=500_000.0,
            retention=2_500_000.0,
            status=QuoteStatus.BOUND,
            data_completeness=DataCompleteness.COMPLETE,
            source="csv_import",
            source_document="tower_2024.xlsx",
            notes_text="Full tower from broker",
            layers=[
                EnhancedLayerInput(
                    layer_type=LayerType.PRIMARY,
                    layer_number=1,
                    limit_amount=10_000_000.0,
                    premium=1_000_000.0,
                ),
                EnhancedLayerInput(
                    layer_type=LayerType.EXCESS,
                    layer_label="1st Excess",
                    layer_number=2,
                    limit_amount=10_000_000.0,
                    premium=400_000.0,
                ),
            ],
        )
        assert len(py.layers) == 2
        assert py.data_completeness == DataCompleteness.COMPLETE


class TestPolicyYearOutput:
    """Tests for PolicyYearOutput."""

    def test_policy_year_output(self) -> None:
        py = PolicyYearOutput(
            id=1,
            program_id=10,
            policy_year=2025,
            status="QUOTED",
            data_completeness="FRAGMENT",
            source="manual",
            program_rate_on_line=None,
            created_at=_now(),
        )
        assert py.id == 1
        assert py.program_rate_on_line is None


class TestProgramInput:
    """Tests for ProgramInput with D2 minimum viable record."""

    def test_minimum_viable_ticker_only(self) -> None:
        """Just ticker = valid program (D2 decision)."""
        p = ProgramInput(ticker="AAPL")
        assert p.ticker == "AAPL"
        assert p.company_name is None
        assert p.anniversary_month is None
        assert p.broker is None
        assert p.broker_id is None

    def test_full_program(self) -> None:
        p = ProgramInput(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            anniversary_month=6,
            anniversary_day=15,
            broker=BrokerInput(brokerage_name="Marsh"),
            notes_text="Major tech program",
        )
        assert p.company_name == "Microsoft Corporation"
        assert p.broker is not None
        assert p.broker.brokerage_name == "Marsh"

    def test_program_with_broker_id(self) -> None:
        p = ProgramInput(ticker="GOOG", broker_id=42)
        assert p.broker_id == 42
        assert p.broker is None


class TestProgramOutput:
    """Tests for ProgramOutput."""

    def test_program_output_minimal(self) -> None:
        now = _now()
        p = ProgramOutput(
            id=1,
            ticker="TSLA",
            created_at=now,
            updated_at=now,
        )
        assert p.id == 1
        assert p.ticker == "TSLA"
        assert p.policy_years == []
        assert p.broker is None

    def test_program_output_with_policy_years(self) -> None:
        now = _now()
        p = ProgramOutput(
            id=1,
            ticker="META",
            created_at=now,
            updated_at=now,
            policy_years=[
                PolicyYearOutput(
                    id=10,
                    program_id=1,
                    policy_year=2025,
                    status="QUOTED",
                    data_completeness="FRAGMENT",
                    source="manual",
                    created_at=now,
                ),
            ],
        )
        assert len(p.policy_years) == 1
        assert p.policy_years[0].policy_year == 2025


class TestExistingModelsUnchanged:
    """Verify existing QuoteInput still works unchanged."""

    def test_quote_input_still_works(self) -> None:
        from do_uw.models.pricing import MarketCapTier

        q = QuoteInput(
            ticker="AAPL",
            company_name="Apple Inc.",
            effective_date=_now(),
            quote_date=_now(),
            total_limit=50_000_000.0,
            total_premium=500_000.0,
            market_cap_tier=MarketCapTier.MEGA,
        )
        assert q.ticker == "AAPL"
        assert q.status == QuoteStatus.QUOTED

    def test_tower_layer_output_still_works(self) -> None:
        layer = TowerLayerOutput(
            id=1,
            layer_position="PRIMARY",
            layer_number=1,
            attachment_point=0.0,
            limit_amount=10_000_000.0,
            premium=1_000_000.0,
            carrier_name="Hartford",
            rate_on_line=0.10,
            premium_per_million=100_000.0,
        )
        assert layer.rate_on_line == 0.10
