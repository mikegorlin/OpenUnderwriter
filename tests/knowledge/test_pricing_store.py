"""Tests for the PricingStore CRUD API."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.knowledge.pricing_store import PricingStore
from do_uw.models.pricing import (
    MarketCapTier,
    QuoteInput,
    QuoteStatus,
    TowerLayerInput,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _make_quote_input(
    ticker: str = "AAPL",
    premium: float = 500_000.0,
    limit: float = 10_000_000.0,
    status: QuoteStatus = QuoteStatus.QUOTED,
    market_cap_tier: MarketCapTier = MarketCapTier.MEGA,
    sector: str | None = None,
    layers: list[TowerLayerInput] | None = None,
) -> QuoteInput:
    """Create a QuoteInput for testing."""
    return QuoteInput(
        ticker=ticker.upper(),
        company_name=f"{ticker} Inc.",
        effective_date=_now(),
        quote_date=_now(),
        status=status,
        total_limit=limit,
        total_premium=premium,
        market_cap_tier=market_cap_tier,
        sector=sector,
        source="test",
        layers=layers or [],
    )


def _make_layer(
    layer_number: int = 1,
    position: str = "PRIMARY",
    attachment: float = 0.0,
    limit_amount: float = 5_000_000.0,
    premium: float = 250_000.0,
    carrier: str = "TestCarrier",
) -> TowerLayerInput:
    """Create a TowerLayerInput for testing."""
    return TowerLayerInput(
        layer_position=position,
        layer_number=layer_number,
        attachment_point=attachment,
        limit_amount=limit_amount,
        premium=premium,
        carrier_name=carrier,
    )


class TestAddAndGetQuote:
    """Test adding and retrieving quotes."""

    def test_add_and_get_quote(self) -> None:
        """Add a quote and retrieve it by ID."""
        store = PricingStore(db_path=None)
        qi = _make_quote_input(ticker="AAPL", premium=500_000, limit=10_000_000)
        quote_id = store.add_quote(qi)

        assert quote_id >= 1

        result = store.get_quote(quote_id)
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.total_premium == 500_000.0
        assert result.total_limit == 10_000_000.0
        assert result.status == "QUOTED"
        assert result.market_cap_tier == "MEGA"
        assert result.program_rate_on_line == pytest.approx(0.05)

    def test_get_nonexistent_quote(self) -> None:
        """Getting a nonexistent quote returns None."""
        store = PricingStore(db_path=None)
        assert store.get_quote(999) is None

    def test_add_quote_with_layers(self) -> None:
        """Add a quote with tower layers and verify computed metrics."""
        store = PricingStore(db_path=None)
        layers = [
            _make_layer(
                layer_number=1,
                position="PRIMARY",
                attachment=0,
                limit_amount=5_000_000,
                premium=250_000,
                carrier="CarrierA",
            ),
            _make_layer(
                layer_number=2,
                position="LOW_EXCESS",
                attachment=5_000_000,
                limit_amount=5_000_000,
                premium=100_000,
                carrier="CarrierB",
            ),
        ]
        qi = _make_quote_input(
            ticker="MSFT", premium=350_000, limit=10_000_000, layers=layers
        )
        quote_id = store.add_quote(qi)
        result = store.get_quote(quote_id)

        assert result is not None
        assert len(result.layers) == 2

        primary = next(lyr for lyr in result.layers if lyr.layer_number == 1)
        assert primary.rate_on_line == pytest.approx(0.05)
        assert primary.premium_per_million == pytest.approx(50_000.0)
        assert primary.carrier_name == "CarrierA"

        excess = next(lyr for lyr in result.layers if lyr.layer_number == 2)
        assert excess.rate_on_line == pytest.approx(0.02)
        assert excess.premium_per_million == pytest.approx(20_000.0)


class TestListQuotes:
    """Test listing and filtering quotes."""

    def test_list_quotes_by_ticker(self) -> None:
        """Filter quotes by ticker."""
        store = PricingStore(db_path=None)
        store.add_quote(_make_quote_input(ticker="AAPL"))
        store.add_quote(_make_quote_input(ticker="MSFT"))
        store.add_quote(_make_quote_input(ticker="AAPL"))

        aapl = store.list_quotes(ticker="AAPL")
        assert len(aapl) == 2
        assert all(q.ticker == "AAPL" for q in aapl)

        msft = store.list_quotes(ticker="MSFT")
        assert len(msft) == 1

    def test_list_quotes_by_status(self) -> None:
        """Filter quotes by status."""
        store = PricingStore(db_path=None)
        store.add_quote(
            _make_quote_input(ticker="AAPL", status=QuoteStatus.QUOTED)
        )
        store.add_quote(
            _make_quote_input(ticker="AAPL", status=QuoteStatus.BOUND)
        )

        quoted = store.list_quotes(status="QUOTED")
        assert len(quoted) == 1
        assert quoted[0].status == "QUOTED"

        bound = store.list_quotes(status="BOUND")
        assert len(bound) == 1
        assert bound[0].status == "BOUND"

    def test_list_all_quotes(self) -> None:
        """List all quotes without filter."""
        store = PricingStore(db_path=None)
        store.add_quote(_make_quote_input(ticker="AAPL"))
        store.add_quote(_make_quote_input(ticker="MSFT"))

        all_quotes = store.list_quotes()
        assert len(all_quotes) == 2


class TestUpdateQuoteStatus:
    """Test status lifecycle updates."""

    def test_update_quote_status(self) -> None:
        """Update quote status from QUOTED to BOUND."""
        store = PricingStore(db_path=None)
        quote_id = store.add_quote(_make_quote_input())

        result = store.update_quote_status(quote_id, "BOUND")
        assert result is True

        quote = store.get_quote(quote_id)
        assert quote is not None
        assert quote.status == "BOUND"

    def test_update_nonexistent_quote(self) -> None:
        """Updating a nonexistent quote returns False."""
        store = PricingStore(db_path=None)
        assert store.update_quote_status(999, "BOUND") is False


class TestTowerComparison:
    """Test tower structure comparison."""

    def test_get_tower_comparison(self) -> None:
        """Compare tower structures for a company."""
        store = PricingStore(db_path=None)
        layers1 = [
            _make_layer(1, "PRIMARY", 0, 5_000_000, 250_000, "CarrierA"),
        ]
        layers2 = [
            _make_layer(1, "PRIMARY", 0, 5_000_000, 275_000, "CarrierC"),
            _make_layer(2, "LOW_EXCESS", 5_000_000, 5_000_000, 100_000, "CarrierD"),
        ]
        store.add_quote(
            _make_quote_input(ticker="AAPL", premium=250_000, layers=layers1)
        )
        store.add_quote(
            _make_quote_input(ticker="AAPL", premium=375_000, layers=layers2)
        )

        comparison = store.get_tower_comparison("AAPL")
        assert len(comparison) == 2

        # Each entry has quote-level and layer-level data
        for entry in comparison:
            assert "quote_id" in entry
            assert "layers" in entry
            assert "program_rate_on_line" in entry


class TestAddTowerLayer:
    """Test adding layers to existing quotes."""

    def test_add_tower_layer(self) -> None:
        """Add a layer to an existing quote."""
        store = PricingStore(db_path=None)
        quote_id = store.add_quote(_make_quote_input())

        layer = _make_layer(
            layer_number=1,
            position="PRIMARY",
            limit_amount=5_000_000,
            premium=250_000,
        )
        layer_id = store.add_tower_layer(quote_id, layer)
        assert layer_id >= 1

        # Verify layer is attached
        quote = store.get_quote(quote_id)
        assert quote is not None
        assert len(quote.layers) == 1

    def test_add_layer_to_nonexistent_quote(self) -> None:
        """Adding a layer to nonexistent quote raises ValueError."""
        store = PricingStore(db_path=None)
        layer = _make_layer()
        with pytest.raises(ValueError, match="not found"):
            store.add_tower_layer(999, layer)


class TestGetRatesForSegment:
    """Test segment-based rate queries."""

    def test_get_rates_for_segment(self) -> None:
        """Get rates filtered by market cap tier and sector."""
        store = PricingStore(db_path=None)
        store.add_quote(
            _make_quote_input(
                ticker="AAPL",
                premium=500_000,
                limit=10_000_000,
                market_cap_tier=MarketCapTier.MEGA,
                sector="Technology",
            )
        )
        store.add_quote(
            _make_quote_input(
                ticker="JPM",
                premium=800_000,
                limit=10_000_000,
                market_cap_tier=MarketCapTier.LARGE,
                sector="Financials",
            )
        )

        mega_rates = store.get_rates_for_segment(market_cap_tier="MEGA")
        assert len(mega_rates) == 1
        assert mega_rates[0] == pytest.approx(0.05)

        tech_rates = store.get_rates_for_segment(sector="Technology")
        assert len(tech_rates) == 1

        all_rates = store.get_rates_for_segment()
        assert len(all_rates) == 2

    def test_get_rates_status_filter(self) -> None:
        """Rates filter by status (default QUOTED+BOUND)."""
        store = PricingStore(db_path=None)
        store.add_quote(
            _make_quote_input(status=QuoteStatus.QUOTED)
        )
        store.add_quote(
            _make_quote_input(status=QuoteStatus.DECLINED)
        )

        rates = store.get_rates_for_segment()
        assert len(rates) == 1  # Only QUOTED included

    def test_get_rates_with_layer_position(self) -> None:
        """Get layer-level rates by position."""
        store = PricingStore(db_path=None)
        layers = [
            _make_layer(1, "PRIMARY", 0, 5_000_000, 250_000, "CarrierA"),
            _make_layer(2, "LOW_EXCESS", 5_000_000, 5_000_000, 100_000, "CarrierB"),
        ]
        store.add_quote(
            _make_quote_input(premium=350_000, limit=10_000_000, layers=layers)
        )

        primary_rates = store.get_rates_for_segment(layer_position="PRIMARY")
        assert len(primary_rates) == 1
        assert primary_rates[0] == pytest.approx(0.05)

        excess_rates = store.get_rates_for_segment(layer_position="LOW_EXCESS")
        assert len(excess_rates) == 1
        assert excess_rates[0] == pytest.approx(0.02)


class TestZeroDivisionGuard:
    """Test zero-division protection."""

    def test_zero_limit_guard(self) -> None:
        """Zero limit produces 0.0 rate_on_line instead of error."""
        store = PricingStore(db_path=None)
        qi = _make_quote_input(premium=0, limit=0)
        quote_id = store.add_quote(qi)

        result = store.get_quote(quote_id)
        assert result is not None
        assert result.program_rate_on_line == 0.0

    def test_zero_layer_limit_guard(self) -> None:
        """Zero layer limit produces 0.0 rate_on_line."""
        store = PricingStore(db_path=None)
        layers = [
            _make_layer(limit_amount=0, premium=0),
        ]
        qi = _make_quote_input(layers=layers)
        quote_id = store.add_quote(qi)

        result = store.get_quote(quote_id)
        assert result is not None
        assert len(result.layers) == 1
        assert result.layers[0].rate_on_line == 0.0
        assert result.layers[0].premium_per_million == 0.0
