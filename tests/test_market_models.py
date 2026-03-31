"""Tests for market data models (market.py and market_events.py).

Validates model instantiation, SourcedValue field creation,
JSON round-trip serialization, and list field isolation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market import (
    InsiderTradingProfile,
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
    AdverseEventScore,
    AnalystSentimentProfile,
    CapitalMarketsActivity,
    CapitalMarketsOffering,
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    InsiderTransaction,
    StockDropAnalysis,
    StockDropEvent,
)

NOW = datetime(2025, 6, 15, tzinfo=UTC)


def _sv_str(value: str, source: str = "test") -> SourcedValue[str]:
    """Create a SourcedValue[str] with minimal boilerplate."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.MEDIUM, as_of=NOW
    )


def _sv_float(value: float, source: str = "test") -> SourcedValue[float]:
    """Create a SourcedValue[float] with minimal boilerplate."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.MEDIUM, as_of=NOW
    )


def _sv_int(value: int, source: str = "test") -> SourcedValue[int]:
    """Create a SourcedValue[int] with minimal boilerplate."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.MEDIUM, as_of=NOW
    )


def _sv_bool(value: bool, source: str = "test") -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with minimal boilerplate."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.MEDIUM, as_of=NOW
    )


# ---------------------------------------------------------------------------
# StockDropEvent / StockDropAnalysis
# ---------------------------------------------------------------------------


class TestStockDropEvent:
    def test_default_instantiation(self) -> None:
        event = StockDropEvent()
        assert event.date is None
        assert event.drop_pct is None
        assert event.drop_type == ""
        assert event.period_days == 1
        assert event.is_company_specific is False
        assert event.close_price is None

    def test_populated_event(self) -> None:
        event = StockDropEvent(
            date=_sv_str("2025-01-15", "yfinance"),
            drop_pct=_sv_float(-12.5, "yfinance"),
            drop_type="SINGLE_DAY",
            period_days=1,
            is_company_specific=True,
            trigger_event=_sv_str("Earnings miss", "news"),
            close_price=42.50,
        )
        assert event.date is not None
        assert event.date.value == "2025-01-15"
        assert event.drop_pct is not None
        assert event.drop_pct.value == -12.5
        assert event.drop_type == "SINGLE_DAY"
        assert event.is_company_specific is True
        assert event.close_price == 42.50


class TestStockDropAnalysis:
    def test_default_empty(self) -> None:
        analysis = StockDropAnalysis()
        assert analysis.single_day_drops == []
        assert analysis.multi_day_drops == []
        assert analysis.analysis_period_months == 18
        assert analysis.worst_single_day is None

    def test_list_isolation(self) -> None:
        """Ensure default_factory creates independent lists."""
        a = StockDropAnalysis()
        b = StockDropAnalysis()
        a.single_day_drops.append(StockDropEvent())
        assert len(b.single_day_drops) == 0

    def test_with_events(self) -> None:
        event = StockDropEvent(
            drop_pct=_sv_float(-8.2),
            drop_type="SINGLE_DAY",
        )
        analysis = StockDropAnalysis(
            single_day_drops=[event],
            worst_single_day=event,
        )
        assert len(analysis.single_day_drops) == 1
        assert analysis.worst_single_day is not None
        assert analysis.worst_single_day.drop_pct is not None
        assert analysis.worst_single_day.drop_pct.value == -8.2


# ---------------------------------------------------------------------------
# InsiderTransaction / InsiderClusterEvent / InsiderTradingAnalysis
# ---------------------------------------------------------------------------


class TestInsiderTransaction:
    def test_default_instantiation(self) -> None:
        txn = InsiderTransaction()
        assert txn.insider_name is None
        assert txn.transaction_type == ""
        assert txn.transaction_code == ""
        assert txn.is_discretionary is False

    def test_populated_transaction(self) -> None:
        txn = InsiderTransaction(
            insider_name=_sv_str("John Smith", "SEC Form 4"),
            title=_sv_str("CEO", "SEC Form 4"),
            transaction_date=_sv_str("2025-03-10", "SEC Form 4"),
            transaction_type="SELL",
            transaction_code="S",
            shares=_sv_float(50000.0, "SEC Form 4"),
            price_per_share=_sv_float(75.50, "SEC Form 4"),
            total_value=_sv_float(3775000.0, "SEC Form 4"),
            is_10b5_1=_sv_bool(False, "SEC Form 4"),
            is_discretionary=True,
        )
        assert txn.insider_name is not None
        assert txn.insider_name.value == "John Smith"
        assert txn.total_value is not None
        assert txn.total_value.value == 3775000.0
        assert txn.is_discretionary is True


class TestInsiderClusterEvent:
    def test_default_instantiation(self) -> None:
        cluster = InsiderClusterEvent()
        assert cluster.insider_count == 0
        assert cluster.insiders == []
        assert cluster.total_value == 0.0

    def test_populated_cluster(self) -> None:
        cluster = InsiderClusterEvent(
            start_date="2025-03-01",
            end_date="2025-03-15",
            insider_count=3,
            insiders=["CEO", "CFO", "CTO"],
            total_value=5_000_000.0,
        )
        assert cluster.insider_count == 3
        assert len(cluster.insiders) == 3

    def test_list_isolation(self) -> None:
        a = InsiderClusterEvent()
        b = InsiderClusterEvent()
        a.insiders.append("CEO")
        assert len(b.insiders) == 0


class TestInsiderTradingAnalysis:
    def test_default_empty(self) -> None:
        analysis = InsiderTradingAnalysis()
        assert analysis.transactions == []
        assert analysis.cluster_events == []
        assert analysis.net_buying_selling is None

    def test_list_isolation(self) -> None:
        a = InsiderTradingAnalysis()
        b = InsiderTradingAnalysis()
        a.transactions.append(InsiderTransaction())
        assert len(b.transactions) == 0


# ---------------------------------------------------------------------------
# EarningsQuarterRecord / EarningsGuidanceAnalysis
# ---------------------------------------------------------------------------


class TestEarningsQuarterRecord:
    def test_default_instantiation(self) -> None:
        record = EarningsQuarterRecord()
        assert record.quarter == ""
        assert record.consensus_eps_low is None
        assert record.actual_eps is None
        assert record.result == ""

    def test_populated_record(self) -> None:
        record = EarningsQuarterRecord(
            quarter="Q3 2025",
            consensus_eps_low=_sv_float(1.20),
            consensus_eps_high=_sv_float(1.30),
            actual_eps=_sv_float(1.10),
            result="MISS",
            miss_magnitude_pct=_sv_float(-8.0),
            stock_reaction_pct=_sv_float(-5.2),
        )
        assert record.quarter == "Q3 2025"
        assert record.result == "MISS"
        assert record.actual_eps is not None
        assert record.actual_eps.value == 1.10


class TestEarningsGuidanceAnalysis:
    def test_default_empty(self) -> None:
        analysis = EarningsGuidanceAnalysis()
        assert analysis.quarters == []
        assert analysis.beat_rate is None
        assert analysis.consecutive_miss_count == 0
        assert analysis.guidance_withdrawals == 0
        assert analysis.philosophy == ""

    def test_list_isolation(self) -> None:
        a = EarningsGuidanceAnalysis()
        b = EarningsGuidanceAnalysis()
        a.quarters.append(EarningsQuarterRecord(quarter="Q1 2025"))
        assert len(b.quarters) == 0


# ---------------------------------------------------------------------------
# AnalystSentimentProfile
# ---------------------------------------------------------------------------


class TestAnalystSentimentProfile:
    def test_default_instantiation(self) -> None:
        profile = AnalystSentimentProfile()
        assert profile.coverage_count is None
        assert profile.consensus is None
        assert profile.recent_upgrades == 0
        assert profile.recent_downgrades == 0

    def test_populated_profile(self) -> None:
        profile = AnalystSentimentProfile(
            coverage_count=_sv_int(12, "Yahoo Finance"),
            consensus=_sv_str("BUY", "Yahoo Finance"),
            recommendation_mean=_sv_float(2.1, "Yahoo Finance"),
            target_price_mean=_sv_float(85.0, "Yahoo Finance"),
            target_price_high=_sv_float(110.0),
            target_price_low=_sv_float(60.0),
            recent_upgrades=3,
            recent_downgrades=1,
        )
        assert profile.coverage_count is not None
        assert profile.coverage_count.value == 12
        assert profile.recent_upgrades == 3


# ---------------------------------------------------------------------------
# CapitalMarketsOffering / CapitalMarketsActivity
# ---------------------------------------------------------------------------


class TestCapitalMarketsOffering:
    def test_default_instantiation(self) -> None:
        offering = CapitalMarketsOffering()
        assert offering.offering_type == ""
        assert offering.filing_type == ""
        assert offering.date is None
        assert offering.amount is None

    def test_populated_offering(self) -> None:
        offering = CapitalMarketsOffering(
            offering_type="SECONDARY",
            filing_type="S-3",
            date=_sv_str("2025-01-20", "SEC EDGAR"),
            amount=_sv_float(500_000_000.0, "SEC EDGAR"),
            section_11_window_end="2028-01-20",
        )
        assert offering.offering_type == "SECONDARY"
        assert offering.amount is not None
        assert offering.amount.value == 500_000_000.0


class TestCapitalMarketsActivity:
    def test_default_empty(self) -> None:
        activity = CapitalMarketsActivity()
        assert activity.shelf_registrations == []
        assert activity.offerings_3yr == []
        assert activity.has_atm_program is None
        assert activity.active_section_11_windows == 0

    def test_list_isolation(self) -> None:
        a = CapitalMarketsActivity()
        b = CapitalMarketsActivity()
        a.offerings_3yr.append(CapitalMarketsOffering())
        assert len(b.offerings_3yr) == 0


# ---------------------------------------------------------------------------
# AdverseEventScore
# ---------------------------------------------------------------------------


class TestAdverseEventScore:
    def test_default_instantiation(self) -> None:
        score = AdverseEventScore()
        assert score.total_score is None
        assert score.event_count == 0
        assert score.severity_breakdown == {}
        assert score.peer_rank is None

    def test_populated_score(self) -> None:
        score = AdverseEventScore(
            total_score=_sv_float(72.5, "computed"),
            event_count=8,
            severity_breakdown={"LOW": 3, "MEDIUM": 3, "HIGH": 2},
            peer_rank=_sv_int(2, "peer analysis"),
            peer_percentile=_sv_float(15.0, "peer analysis"),
        )
        assert score.total_score is not None
        assert score.total_score.value == 72.5
        assert score.event_count == 8
        assert score.severity_breakdown["HIGH"] == 2


# ---------------------------------------------------------------------------
# StockPerformance (extended fields)
# ---------------------------------------------------------------------------


class TestStockPerformance:
    def test_default_instantiation(self) -> None:
        perf = StockPerformance()
        assert perf.current_price is None
        assert perf.returns_5y is None
        assert perf.returns_ytd is None
        assert perf.max_drawdown_1y is None

    def test_new_fields(self) -> None:
        perf = StockPerformance(
            returns_5y=_sv_float(45.0, "yfinance"),
            returns_ytd=_sv_float(-3.2, "yfinance"),
            max_drawdown_1y=_sv_float(-22.5, "yfinance"),
        )
        assert perf.returns_5y is not None
        assert perf.returns_5y.value == 45.0
        assert perf.max_drawdown_1y is not None
        assert perf.max_drawdown_1y.value == -22.5


# ---------------------------------------------------------------------------
# MarketSignals (SECT4 sub-model fields)
# ---------------------------------------------------------------------------


class TestMarketSignals:
    def test_default_instantiation(self) -> None:
        signals = MarketSignals()
        assert isinstance(signals.stock, StockPerformance)
        assert isinstance(signals.insider_trading, InsiderTradingProfile)
        assert isinstance(signals.short_interest, ShortInterestProfile)
        # SECT4 fields
        assert isinstance(signals.stock_drops, StockDropAnalysis)
        assert isinstance(signals.insider_analysis, InsiderTradingAnalysis)
        assert isinstance(signals.earnings_guidance, EarningsGuidanceAnalysis)
        assert isinstance(signals.analyst, AnalystSentimentProfile)
        assert isinstance(signals.capital_markets, CapitalMarketsActivity)
        assert isinstance(signals.adverse_events, AdverseEventScore)

    def test_sub_model_isolation(self) -> None:
        """Ensure default_factory creates independent sub-model instances."""
        a = MarketSignals()
        b = MarketSignals()
        a.stock_drops.single_day_drops.append(StockDropEvent())
        assert len(b.stock_drops.single_day_drops) == 0

    def test_json_round_trip(self) -> None:
        """Verify serialization and deserialization preserves structure."""
        signals = MarketSignals()
        signals.stock.current_price = _sv_float(150.0, "yfinance")
        signals.stock_drops.analysis_period_months = 24
        signals.insider_analysis.net_buying_selling = _sv_str(
            "NET_SELLING", "SEC Form 4"
        )
        signals.earnings_guidance.consecutive_miss_count = 2
        signals.analyst.recent_downgrades = 5
        signals.capital_markets.active_section_11_windows = 1
        signals.adverse_events.event_count = 4

        json_str = signals.model_dump_json()
        restored = MarketSignals.model_validate_json(json_str)

        assert restored.stock.current_price is not None
        assert restored.stock.current_price.value == 150.0
        assert restored.stock_drops.analysis_period_months == 24
        assert restored.insider_analysis.net_buying_selling is not None
        assert (
            restored.insider_analysis.net_buying_selling.value
            == "NET_SELLING"
        )
        assert restored.earnings_guidance.consecutive_miss_count == 2
        assert restored.analyst.recent_downgrades == 5
        assert restored.capital_markets.active_section_11_windows == 1
        assert restored.adverse_events.event_count == 4

    def test_nested_list_round_trip(self) -> None:
        """Verify nested list models survive JSON round-trip."""
        signals = MarketSignals()
        signals.stock_drops.single_day_drops.append(
            StockDropEvent(
                drop_pct=_sv_float(-10.0, "yfinance"),
                drop_type="SINGLE_DAY",
            )
        )
        signals.insider_analysis.transactions.append(
            InsiderTransaction(
                insider_name=_sv_str("Jane Doe", "SEC Form 4"),
                transaction_type="SELL",
            )
        )

        json_str = signals.model_dump_json()
        restored = MarketSignals.model_validate_json(json_str)

        assert len(restored.stock_drops.single_day_drops) == 1
        drop = restored.stock_drops.single_day_drops[0]
        assert drop.drop_pct is not None
        assert drop.drop_pct.value == -10.0

        assert len(restored.insider_analysis.transactions) == 1
        txn = restored.insider_analysis.transactions[0]
        assert txn.insider_name is not None
        assert txn.insider_name.value == "Jane Doe"
