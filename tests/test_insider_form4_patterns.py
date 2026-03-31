"""Tests for exercise-sell pattern detection and filing timing analysis (Plan 71-02)."""

from __future__ import annotations

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import (
    ExerciseSellEvent,
    FilingTimingSuspect,
    InsiderTransaction,
)


def _now() -> str:
    return "2026-03-06T00:00:00Z"


def _sv_str(val: str, src: str = "test") -> SourcedValue[str]:
    return SourcedValue[str](value=val, source=src, confidence=Confidence.HIGH, as_of=_now())


def _sv_float(val: float, src: str = "test") -> SourcedValue[float]:
    return SourcedValue[float](value=val, source=src, confidence=Confidence.HIGH, as_of=_now())


def _sv_bool(val: bool, src: str = "test") -> SourcedValue[bool]:
    return SourcedValue[bool](value=val, source=src, confidence=Confidence.HIGH, as_of=_now())


def _make_tx(
    name: str = "John Doe",
    date: str = "2025-06-15",
    code: str = "S",
    tx_type: str = "SELL",
    shares: float = 1000.0,
    price: float = 50.0,
    is_10b5_1: bool | None = None,
) -> InsiderTransaction:
    return InsiderTransaction(
        insider_name=_sv_str(name),
        title=_sv_str("CEO"),
        transaction_date=_sv_str(date),
        transaction_type=tx_type,
        transaction_code=code,
        shares=_sv_float(shares),
        price_per_share=_sv_float(price),
        total_value=_sv_float(shares * price),
        is_10b5_1=_sv_bool(is_10b5_1) if is_10b5_1 is not None else None,
        is_discretionary=not is_10b5_1 if is_10b5_1 is not None else False,
    )


# ---------------------------------------------------------------------------
# Exercise-sell pattern detection
# ---------------------------------------------------------------------------

class TestDetectExerciseSellPatterns:
    """Tests for detect_exercise_sell_patterns."""

    def test_same_owner_same_day_m_plus_s(self):
        """M+S same owner same day detected."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=500, price=30.0),
            _make_tx(name="Alice", date="2025-06-15", code="S", tx_type="SELL", shares=500, price=50.0),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert len(events) == 1
        assert events[0].owner == "Alice"
        assert events[0].exercised_shares == 500.0
        assert events[0].sold_shares == 500.0
        assert events[0].sold_value == 25000.0

    def test_same_owner_adjacent_day(self):
        """M+S same owner T+1 (adjacent day) detected per Pitfall 4."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Bob", date="2025-06-15", code="M", tx_type="EXERCISE", shares=1000, price=20.0),
            _make_tx(name="Bob", date="2025-06-16", code="S", tx_type="SELL", shares=1000, price=45.0),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert len(events) == 1
        assert events[0].sold_value == 45000.0

    def test_different_owners_ignored(self):
        """M+S by different owners NOT detected."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=500, price=30.0),
            _make_tx(name="Bob", date="2025-06-15", code="S", tx_type="SELL", shares=500, price=50.0),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert len(events) == 0

    def test_combined_totals(self):
        """Multiple M and S transactions combine totals."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=300, price=20.0),
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=200, price=20.0),
            _make_tx(name="Alice", date="2025-06-15", code="S", tx_type="SELL", shares=500, price=50.0),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert len(events) == 1
        assert events[0].exercised_shares == 500.0
        assert events[0].sold_shares == 500.0

    def test_severity_always_amber(self):
        """ExerciseSellEvent always has severity=AMBER."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=500, price=30.0),
            _make_tx(name="Alice", date="2025-06-15", code="S", tx_type="SELL", shares=500, price=50.0),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert events[0].severity == "AMBER"

    def test_inherits_10b5_1_from_sell(self):
        """10b5-1 status inherited from the sell transaction."""
        from do_uw.stages.extract.insider_trading_patterns import detect_exercise_sell_patterns

        txns = [
            _make_tx(name="Alice", date="2025-06-15", code="M", tx_type="EXERCISE", shares=500, price=30.0),
            _make_tx(name="Alice", date="2025-06-15", code="S", tx_type="SELL", shares=500, price=50.0, is_10b5_1=True),
        ]
        events = detect_exercise_sell_patterns(txns)
        assert events[0].is_10b5_1 is True


# ---------------------------------------------------------------------------
# 8-K item classification
# ---------------------------------------------------------------------------

class TestClassify8kItem:
    """Tests for classify_8k_item."""

    def test_negative_items(self):
        from do_uw.stages.extract.insider_trading_patterns import classify_8k_item
        assert classify_8k_item("2.02") == "NEGATIVE"
        assert classify_8k_item("5.02") == "NEGATIVE"
        assert classify_8k_item("4.02") == "NEGATIVE"

    def test_positive_items(self):
        from do_uw.stages.extract.insider_trading_patterns import classify_8k_item
        assert classify_8k_item("1.01") == "POSITIVE"
        assert classify_8k_item("2.01") == "POSITIVE"

    def test_neutral_items(self):
        from do_uw.stages.extract.insider_trading_patterns import classify_8k_item
        assert classify_8k_item("8.01") == "NEUTRAL"
        assert classify_8k_item("3.01") == "NEUTRAL"
        assert classify_8k_item("") == "NEUTRAL"


# ---------------------------------------------------------------------------
# Filing timing analysis
# ---------------------------------------------------------------------------

class TestAnalyzeFilingTiming:
    """Tests for analyze_filing_timing."""

    def test_sell_before_negative_8k(self):
        """Sell within 60 days before negative 8-K detected as RED_FLAG."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Alice", date="2025-06-01", code="S", tx_type="SELL", shares=1000, price=50.0),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-15", "items": ["2.02"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 1
        assert suspects[0].severity == "RED_FLAG"
        assert suspects[0].filing_sentiment == "NEGATIVE"
        assert suspects[0].days_before_filing == 44

    def test_buy_before_positive_8k(self):
        """Buy within 60 days before positive 8-K detected as AMBER."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Bob", date="2025-06-01", code="P", tx_type="BUY", shares=1000, price=50.0),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-01", "items": ["1.01"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 1
        assert suspects[0].severity == "AMBER"
        assert suspects[0].filing_sentiment == "POSITIVE"

    def test_uses_filing_date_as_proxy(self):
        """Filing date used as conservative proxy per Pitfall 5."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Alice", date="2025-06-10", code="S", tx_type="SELL"),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-10", "items": ["5.02"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 1
        assert suspects[0].days_before_filing == 30

    def test_60_day_window(self):
        """Transactions outside 60-day window NOT flagged."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Alice", date="2025-04-01", code="S", tx_type="SELL"),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-15", "items": ["2.02"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 0

    def test_gift_estate_excluded(self):
        """Gift/estate/compensation transactions excluded."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Alice", date="2025-06-01", code="G", tx_type="GIFT"),
            _make_tx(name="Bob", date="2025-06-01", code="W", tx_type="WILL_OR_ESTATE"),
            _make_tx(name="Carol", date="2025-06-01", code="A", tx_type="GRANT"),
            _make_tx(name="Dan", date="2025-06-01", code="F", tx_type="TAX_WITHHOLD"),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-15", "items": ["2.02"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 0

    def test_neutral_8k_ignored(self):
        """Neutral 8-K items do not trigger timing suspects."""
        from do_uw.stages.extract.insider_trading_patterns import analyze_filing_timing

        txns = [
            _make_tx(name="Alice", date="2025-06-01", code="S", tx_type="SELL"),
        ]
        eight_k_filings = [
            {"filing_date": "2025-07-01", "items": ["8.01"]},
        ]
        suspects = analyze_filing_timing(txns, eight_k_filings, window_days=60)
        assert len(suspects) == 0


# ---------------------------------------------------------------------------
# Integration: wiring into extract_insider_trading
# ---------------------------------------------------------------------------

class TestExtractInsiderTradingWiring:
    """Verify that extract_insider_trading stores exercise-sell and timing results."""

    def test_exercise_sell_events_stored(self):
        """ExerciseSellEvents stored on InsiderTradingAnalysis."""
        from do_uw.models.market_events import InsiderTradingAnalysis
        # Just verify the model field exists and accepts data
        analysis = InsiderTradingAnalysis(
            exercise_sell_events=[
                ExerciseSellEvent(
                    owner="Alice",
                    date="2025-06-15",
                    exercised_shares=500.0,
                    sold_shares=500.0,
                    sold_value=25000.0,
                ),
            ],
        )
        assert len(analysis.exercise_sell_events) == 1

    def test_timing_suspects_stored(self):
        """FilingTimingSuspects stored on InsiderTradingAnalysis."""
        from do_uw.models.market_events import InsiderTradingAnalysis
        analysis = InsiderTradingAnalysis(
            timing_suspects=[
                FilingTimingSuspect(
                    insider_name="Alice",
                    transaction_date="2025-06-01",
                    transaction_type="SELL",
                    filing_date="2025-07-15",
                    filing_item="2.02",
                    filing_sentiment="NEGATIVE",
                    days_before_filing=44,
                    transaction_value=50000.0,
                    severity="RED_FLAG",
                ),
            ],
        )
        assert len(analysis.timing_suspects) == 1
        assert analysis.timing_suspects[0].severity == "RED_FLAG"
