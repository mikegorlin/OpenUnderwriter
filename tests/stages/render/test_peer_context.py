"""Unit tests for peer context formatting utilities."""

from __future__ import annotations

import pytest

from do_uw.models.scoring import BenchmarkResult, MetricBenchmark
from do_uw.models.state import AnalysisState
from do_uw.stages.render.peer_context import (
    _ordinal,
    format_metric_with_context,
    get_benchmark_for_metric,
    get_peer_context_line,
)


# ---------------------------------------------------------------------------
# _ordinal tests
# ---------------------------------------------------------------------------


class TestOrdinal:
    """Tests for _ordinal edge cases."""

    def test_1st(self) -> None:
        assert _ordinal(1) == "1st"

    def test_2nd(self) -> None:
        assert _ordinal(2) == "2nd"

    def test_3rd(self) -> None:
        assert _ordinal(3) == "3rd"

    def test_4th(self) -> None:
        assert _ordinal(4) == "4th"

    def test_11th(self) -> None:
        assert _ordinal(11) == "11th"

    def test_12th(self) -> None:
        assert _ordinal(12) == "12th"

    def test_13th(self) -> None:
        assert _ordinal(13) == "13th"

    def test_21st(self) -> None:
        assert _ordinal(21) == "21st"

    def test_22nd(self) -> None:
        assert _ordinal(22) == "22nd"

    def test_23rd(self) -> None:
        assert _ordinal(23) == "23rd"

    def test_111th(self) -> None:
        assert _ordinal(111) == "111th"

    def test_112th(self) -> None:
        assert _ordinal(112) == "112th"

    def test_0th(self) -> None:
        assert _ordinal(0) == "0th"

    def test_100th(self) -> None:
        assert _ordinal(100) == "100th"

    def test_101st(self) -> None:
        assert _ordinal(101) == "101st"


# ---------------------------------------------------------------------------
# format_metric_with_context tests
# ---------------------------------------------------------------------------


class TestFormatMetricWithContext:
    """Tests for format_metric_with_context."""

    def test_none_benchmark_returns_plain(self) -> None:
        result = format_metric_with_context("Revenue", "$1.2B", None)
        assert result == "Revenue: $1.2B"

    def test_none_percentile_returns_plain(self) -> None:
        mb = MetricBenchmark(
            metric_name="revenue",
            company_value=1_200_000_000,
            percentile_rank=None,
            peer_count=10,
        )
        result = format_metric_with_context("Revenue", "$1.2B", mb)
        assert result == "Revenue: $1.2B"

    def test_full_benchmark_with_baseline(self) -> None:
        mb = MetricBenchmark(
            metric_name="market_cap",
            company_value=12_000_000_000,
            percentile_rank=72.0,
            peer_count=15,
            baseline_value=8_100_000_000,
        )
        result = format_metric_with_context("Market Cap", "$12.0B", mb)
        assert "72nd percentile" in result
        assert "15 peers" in result
        assert "median $8.1B" in result

    def test_full_benchmark_without_baseline(self) -> None:
        mb = MetricBenchmark(
            metric_name="quality_score",
            company_value=85.0,
            percentile_rank=90.0,
            peer_count=20,
            baseline_value=None,
        )
        result = format_metric_with_context("Quality Score", "85.0", mb)
        assert "90th percentile" in result
        assert "20 peers" in result
        assert "median" not in result

    def test_with_named_peers(self) -> None:
        mb = MetricBenchmark(
            metric_name="market_cap",
            company_value=5_000_000_000,
            percentile_rank=55.0,
            peer_count=10,
            baseline_value=4_000_000_000,
        )
        result = format_metric_with_context(
            "Market Cap", "$5.0B", mb, named_peers=["AAPL", "MSFT", "GOOG"]
        )
        assert "[AAPL, MSFT, GOOG]" in result

    def test_named_peers_truncated_to_3(self) -> None:
        mb = MetricBenchmark(
            metric_name="market_cap",
            company_value=5_000_000_000,
            percentile_rank=55.0,
            peer_count=10,
        )
        result = format_metric_with_context(
            "Market Cap",
            "$5.0B",
            mb,
            named_peers=["A", "B", "C", "D", "E"],
        )
        assert "[A, B, C]" in result
        assert "D" not in result

    def test_percentage_baseline_for_volatility(self) -> None:
        mb = MetricBenchmark(
            metric_name="volatility_90d",
            company_value=35.0,
            percentile_rank=80.0,
            peer_count=12,
            baseline_value=25.5,
        )
        result = format_metric_with_context("90d Volatility", "35.0%", mb)
        assert "median 25.5%" in result


# ---------------------------------------------------------------------------
# get_peer_context_line tests
# ---------------------------------------------------------------------------


class TestGetPeerContextLine:
    """Tests for get_peer_context_line."""

    def test_none_benchmark_returns_none(self) -> None:
        result = get_peer_context_line("market_cap", None)
        assert result is None

    def test_missing_metric_returns_none(self) -> None:
        bm = BenchmarkResult()
        result = get_peer_context_line("nonexistent", bm)
        assert result is None

    def test_structured_metric_details(self) -> None:
        bm = BenchmarkResult(
            metric_details={
                "market_cap": MetricBenchmark(
                    metric_name="market_cap",
                    company_value=10_000_000_000,
                    percentile_rank=65.0,
                    peer_count=12,
                    baseline_value=7_000_000_000,
                )
            }
        )
        result = get_peer_context_line("market_cap", bm)
        assert result is not None
        assert "65th percentile" in result
        assert "12 peers" in result
        assert "peer median" in result

    def test_fallback_to_peer_rankings(self) -> None:
        bm = BenchmarkResult(
            peer_rankings={"quality_score": 88.0},
        )
        result = get_peer_context_line("quality_score", bm)
        assert result is not None
        assert "88th percentile" in result

    def test_none_percentile_in_metric_details(self) -> None:
        bm = BenchmarkResult(
            metric_details={
                "revenue": MetricBenchmark(
                    metric_name="revenue",
                    percentile_rank=None,
                    peer_count=5,
                )
            }
        )
        result = get_peer_context_line("revenue", bm)
        assert result is None


# ---------------------------------------------------------------------------
# get_benchmark_for_metric tests
# ---------------------------------------------------------------------------


class TestGetBenchmarkForMetric:
    """Tests for get_benchmark_for_metric."""

    def test_none_benchmark_returns_none(self) -> None:
        state = AnalysisState(ticker="TEST")
        assert state.benchmark is None
        result = get_benchmark_for_metric("market_cap", state)
        assert result is None

    def test_missing_metric_returns_none(self) -> None:
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(metric_details={}),
        )
        result = get_benchmark_for_metric("nonexistent", state)
        assert result is None

    def test_found_metric(self) -> None:
        mb = MetricBenchmark(
            metric_name="quality_score",
            company_value=85.0,
            percentile_rank=90.0,
            peer_count=20,
        )
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(metric_details={"quality_score": mb}),
        )
        result = get_benchmark_for_metric("quality_score", state)
        assert result is not None
        assert result.percentile_rank == 90.0
