"""Tests for SECT4-06/07/08/09 extractors.

Covers earnings guidance, analyst sentiment, capital markets,
and adverse event scoring extractors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market import MarketSignals
from do_uw.models.market_events import (
    AnalystSentimentProfile,
    CapitalMarketsActivity,
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    EarningsResult,
    GuidancePhilosophy,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    StockDropAnalysis,
    StockDropEvent,
)
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.analyze.adverse_events import (
    compute_adverse_event_score,
    load_severity_weights,
)
from do_uw.stages.extract.capital_markets import (
    compute_section_11_end,
    extract_capital_markets,
    is_window_active,
)
from do_uw.stages.extract.earnings_guidance import (
    extract_earnings_guidance,
)
from do_uw.stages.extract.earnings_guidance_classify import (
    classify_result,
    compute_consecutive_misses,
    compute_philosophy,
)
from do_uw.stages.extract.sourced import sourced_float

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    market_data: dict[str, Any] | None = None,
    filings: dict[str, Any] | None = None,
    extracted_market: MarketSignals | None = None,
) -> AnalysisState:
    """Create a minimal AnalysisState for testing."""
    state = AnalysisState(ticker="TEST")
    state.acquired_data = AcquiredData(
        market_data=market_data or {},
        filings=filings or {},
    )
    if extracted_market is not None:
        state.extracted = ExtractedData(market=extracted_market)
    return state


def _sv_float(value: float) -> SourcedValue[float]:
    """Quick sourced float for tests."""
    return sourced_float(value, "test", Confidence.MEDIUM)


# ===========================================================================
# Earnings Guidance Tests (SECT4-06)
# ===========================================================================


class TestBeatMissClassification:
    """Test classify_result for BEAT/MISS/MEET."""

    def test_beat(self) -> None:
        result, mag = classify_result(1.00, 1.10)
        assert result == EarningsResult.BEAT
        assert mag is None

    def test_miss(self) -> None:
        result, mag = classify_result(1.00, 0.80)
        assert result == EarningsResult.MISS
        assert mag is not None
        assert mag == 20.0

    def test_meet(self) -> None:
        result, mag = classify_result(1.00, 1.005)
        assert result == EarningsResult.MEET
        assert mag is None

    def test_miss_magnitude(self) -> None:
        """Miss magnitude is abs((actual-estimate)/estimate) * 100."""
        result, mag = classify_result(2.00, 1.50)
        assert result == EarningsResult.MISS
        assert mag == 25.0

    def test_none_estimate(self) -> None:
        result, mag = classify_result(None, 1.00)
        assert result == ""
        assert mag is None

    def test_none_actual(self) -> None:
        result, mag = classify_result(1.00, None)
        assert result == ""
        assert mag is None


class TestConsecutiveMisses:
    """Test consecutive miss counting."""

    def test_three_consecutive_misses(self) -> None:
        records = [
            EarningsQuarterRecord(quarter="Q4 2025", result="MISS"),
            EarningsQuarterRecord(quarter="Q3 2025", result="MISS"),
            EarningsQuarterRecord(quarter="Q2 2025", result="MISS"),
            EarningsQuarterRecord(quarter="Q1 2025", result="BEAT"),
        ]
        assert compute_consecutive_misses(records) == 3

    def test_no_consecutive_misses(self) -> None:
        records = [
            EarningsQuarterRecord(quarter="Q4 2025", result="BEAT"),
            EarningsQuarterRecord(quarter="Q3 2025", result="MISS"),
        ]
        assert compute_consecutive_misses(records) == 0

    def test_empty_records(self) -> None:
        assert compute_consecutive_misses([]) == 0


class TestGuidancePhilosophy:
    """Test philosophy classification from beat rate."""

    def test_conservative(self) -> None:
        assert compute_philosophy(0.80) == GuidancePhilosophy.CONSERVATIVE

    def test_aggressive(self) -> None:
        assert compute_philosophy(0.30) == GuidancePhilosophy.AGGRESSIVE

    def test_mixed(self) -> None:
        assert compute_philosophy(0.60) == GuidancePhilosophy.MIXED

    def test_no_guidance(self) -> None:
        assert compute_philosophy(None) == GuidancePhilosophy.NO_GUIDANCE


class TestExtractEarningsGuidance:
    """Integration test for extract_earnings_guidance."""

    def test_with_earnings_data(self) -> None:
        market_data = {
            "earnings_dates": {
                "EPS Estimate": {
                    "2025-10-15": 1.00,
                    "2025-07-15": 0.90,
                    "2025-04-15": 0.80,
                    "2025-01-15": 0.70,
                },
                "Reported EPS": {
                    "2025-10-15": 1.10,
                    "2025-07-15": 0.95,
                    "2025-04-15": 0.85,
                    "2025-01-15": 0.75,
                },
                "Surprise(%)": {
                    "2025-10-15": 2.5,
                    "2025-07-15": 1.8,
                    "2025-04-15": 1.2,
                    "2025-01-15": 0.5,
                },
            },
        }
        state = _make_state(market_data=market_data)
        analysis, report = extract_earnings_guidance(state)

        assert len(analysis.quarters) == 4
        assert analysis.beat_rate is not None
        assert analysis.beat_rate.value == 1.0  # All beats
        assert analysis.philosophy == GuidancePhilosophy.CONSERVATIVE
        assert analysis.consecutive_miss_count == 0
        assert report.coverage_pct == 100.0

    def test_with_earnings_data_list_format(self) -> None:
        """Dict-of-lists format from yfinance serialization."""
        market_data = {
            "earnings_dates": {
                "Earnings Date": [
                    "2025-10-15",
                    "2025-07-15",
                    "2025-04-15",
                    "2025-01-15",
                ],
                "EPS Estimate": [1.00, 0.90, 0.80, 0.70],
                "Reported EPS": [1.10, 0.95, 0.85, 0.75],
                "Surprise(%)": [2.5, 1.8, 1.2, 0.5],
            },
        }
        state = _make_state(market_data=market_data)
        analysis, report = extract_earnings_guidance(state)

        assert len(analysis.quarters) == 4
        assert analysis.beat_rate is not None
        assert analysis.beat_rate.value == 1.0  # All beats
        assert analysis.philosophy == GuidancePhilosophy.CONSERVATIVE
        assert analysis.consecutive_miss_count == 0
        assert report.coverage_pct == 100.0

    def test_list_format_with_future_dates(self) -> None:
        """List format with some future dates (no reported EPS)."""
        market_data = {
            "earnings_dates": {
                "Earnings Date": [
                    "2026-04-15",
                    "2026-01-15",
                    "2025-10-15",
                    "2025-07-15",
                ],
                "EPS Estimate": [0.50, 0.45, 0.40, 0.35],
                "Reported EPS": [None, 0.50, 0.35, 0.30],
                "Surprise(%)": [None, 10.96, -12.5, -14.29],
            },
        }
        state = _make_state(market_data=market_data)
        analysis, _report = extract_earnings_guidance(state)

        # Should skip the future date (None reported EPS).
        assert len(analysis.quarters) == 3
        assert analysis.beat_rate is not None
        # 1 beat, 2 misses = 1/3 beat rate
        assert abs(analysis.beat_rate.value - 1.0 / 3.0) < 0.01

    def test_no_earnings_data(self) -> None:
        state = _make_state(market_data={})
        analysis, report = extract_earnings_guidance(state)

        assert len(analysis.quarters) == 0
        assert analysis.philosophy == GuidancePhilosophy.NO_GUIDANCE
        assert report.coverage_pct < 100.0


# ===========================================================================
# Capital Markets Tests (SECT4-08)
# ===========================================================================


class TestSection11Window:
    """Test Section 11 window computation."""

    def testcompute_section_11_end(self) -> None:
        end = compute_section_11_end("2024-06-15")
        assert end == "2027-06-15"

    def test_leap_year_feb29(self) -> None:
        end = compute_section_11_end("2024-02-29")
        # 2027 is not a leap year, so falls to March 1.
        assert end == "2027-03-01"

    def test_invalid_date(self) -> None:
        end = compute_section_11_end("not-a-date")
        assert end == ""

    def test_active_window(self) -> None:
        # Far future date should be active.
        assert is_window_active("2099-01-01") is True

    def test_expired_window(self) -> None:
        assert is_window_active("2020-01-01") is False


class TestExtractCapitalMarkets:
    """Integration test for extract_capital_markets."""

    def test_with_offering_filings(self) -> None:
        filings = {
            "recent": {
                "form": ["S-3", "424B5", "10-K"],
                "filingDate": ["2024-01-15", "2024-03-20", "2024-02-28"],
                "accessionNumber": ["acc-1", "acc-2", "acc-3"],
            },
        }
        state = _make_state(filings=filings)
        activity, report = extract_capital_markets(state)

        # Should find S-3 and 424B5, not 10-K.
        assert len(activity.offerings_3yr) == 2
        assert activity.active_section_11_windows >= 0
        assert activity.has_atm_program is not None
        assert report.coverage_pct == 100.0

    def test_active_window_count(self) -> None:
        """Offerings with future Section 11 dates should be counted."""
        filings = {
            "recent": {
                "form": ["S-3", "S-3"],
                "filingDate": ["2025-01-01", "2020-01-01"],
                "accessionNumber": ["acc-1", "acc-2"],
            },
        }
        state = _make_state(filings=filings)
        activity, _report = extract_capital_markets(state)

        # 2025 + 3 = 2028 (active), 2020 + 3 = 2023 (expired).
        assert activity.active_section_11_windows == 1

    def test_no_offerings(self) -> None:
        filings = {
            "recent": {
                "form": ["10-K", "10-Q"],
                "filingDate": ["2024-02-28", "2024-05-15"],
                "accessionNumber": ["acc-1", "acc-2"],
            },
        }
        state = _make_state(filings=filings)
        activity, _report = extract_capital_markets(state)

        assert len(activity.offerings_3yr) == 0
        assert activity.active_section_11_windows == 0


# ===========================================================================
# Adverse Event Scoring Tests (SECT4-09)
# ===========================================================================


def _make_market_with_events() -> MarketSignals:
    """Create MarketSignals with various adverse events."""
    market = MarketSignals()

    # Add stock drops.
    market.stock_drops = StockDropAnalysis(
        single_day_drops=[
            StockDropEvent(
                drop_pct=_sv_float(-12.0),
                drop_type="SINGLE_DAY",
            ),
            StockDropEvent(
                drop_pct=_sv_float(-6.0),
                drop_type="SINGLE_DAY",
            ),
        ],
        multi_day_drops=[
            StockDropEvent(
                drop_pct=_sv_float(-15.0),
                drop_type="MULTI_DAY",
                period_days=5,
            ),
        ],
    )

    # Add earnings misses.
    market.earnings_guidance = EarningsGuidanceAnalysis(
        quarters=[
            EarningsQuarterRecord(
                quarter="Q4 2025", result=EarningsResult.MISS
            ),
            EarningsQuarterRecord(
                quarter="Q3 2025", result=EarningsResult.MISS
            ),
            EarningsQuarterRecord(
                quarter="Q2 2025", result=EarningsResult.BEAT
            ),
        ],
        consecutive_miss_count=2,
    )

    # Add analyst downgrades.
    market.analyst = AnalystSentimentProfile(recent_downgrades=3)

    # Add insider cluster selling.
    market.insider_analysis = InsiderTradingAnalysis(
        cluster_events=[
            InsiderClusterEvent(insider_count=4, total_value=5_000_000),
        ],
    )

    # Active Section 11 windows.
    market.capital_markets = CapitalMarketsActivity(
        active_section_11_windows=2,
    )

    return market


class TestAdverseEventScoring:
    """Test adverse event composite scoring."""

    def test_severity_scoring(self) -> None:
        market = _make_market_with_events()
        state = _make_state(extracted_market=market)
        score, report = compute_adverse_event_score(state)

        assert score.total_score is not None
        assert score.total_score.value > 0
        assert score.event_count > 0
        assert report.coverage_pct == 100.0

    def test_consecutive_miss_bonus(self) -> None:
        """3+ consecutive misses adds a bonus penalty."""
        market = MarketSignals()
        market.earnings_guidance = EarningsGuidanceAnalysis(
            quarters=[
                EarningsQuarterRecord(
                    quarter="Q4", result=EarningsResult.MISS
                ),
                EarningsQuarterRecord(
                    quarter="Q3", result=EarningsResult.MISS
                ),
                EarningsQuarterRecord(
                    quarter="Q2", result=EarningsResult.MISS
                ),
            ],
            consecutive_miss_count=3,
        )
        state = _make_state(extracted_market=market)
        score, _report = compute_adverse_event_score(state)

        assert score.total_score is not None
        # Should have: 3 * earnings_miss(1.0) + consecutive_bonus(3.0) = 6.0
        assert score.total_score.value == 6.0

    def test_severity_breakdown(self) -> None:
        market = _make_market_with_events()
        state = _make_state(extracted_market=market)
        score, _report = compute_adverse_event_score(state)

        # Should have entries in breakdown.
        assert len(score.severity_breakdown) > 0

    def test_empty_events(self) -> None:
        """Empty market signals should produce zero score."""
        market = MarketSignals()
        state = _make_state(extracted_market=market)
        score, report = compute_adverse_event_score(state)

        assert score.total_score is not None
        assert score.total_score.value == 0.0
        assert score.event_count == 0
        assert report.coverage_pct == 100.0

    def test_config_loading(self) -> None:
        """Config file should load and contain expected keys."""
        weights = load_severity_weights()
        assert isinstance(weights, dict)
        assert "single_day_drop_5pct" in weights
        assert "earnings_miss" in weights
        assert weights["single_day_drop_20pct"] == 4.0

    def test_missing_config_returns_empty(self, tmp_path: Path) -> None:
        """Missing config file returns empty dict."""
        weights = load_severity_weights(
            tmp_path / "nonexistent.json"
        )
        assert weights == {}
