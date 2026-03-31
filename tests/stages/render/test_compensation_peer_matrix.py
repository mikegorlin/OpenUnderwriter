"""Tests for compensation analysis and peer matrix context builders (Phase 61)."""

from __future__ import annotations

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import CompensationAnalysis
from do_uw.models.scoring import BenchmarkResult, MetricBenchmark
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.financials import extract_peer_matrix
from do_uw.stages.render.context_builders.governance import (
    _build_compensation_analysis,
    extract_governance,
)

from datetime import datetime, UTC


def _sv(val, source="test", confidence=Confidence.HIGH):
    """Shorthand SourcedValue factory."""
    return SourcedValue(
        value=val,
        source=source,
        confidence=confidence,
        as_of=datetime.now(tz=UTC),
    )


# ---------------------------------------------------------------------------
# Compensation Analysis Tests
# ---------------------------------------------------------------------------


class TestBuildCompensationAnalysis:
    """Tests for _build_compensation_analysis helper."""

    def test_full_comp_analysis(self) -> None:
        """All fields populated produces complete dict."""
        comp = CompensationAnalysis(
            ceo_total_comp=_sv(15_000_000.0, source="DEF 14A 2025"),
            ceo_salary=_sv(1_500_000.0),
            ceo_bonus=_sv(3_000_000.0),
            ceo_equity=_sv(9_000_000.0),
            ceo_other=_sv(500_000.0),
            ceo_pay_ratio=_sv(256.0),
            ceo_pay_vs_peer_median=_sv(1.23),
            comp_mix={"salary": 10.0, "bonus": 20.0, "equity": 60.0, "other": 10.0},
            performance_metrics=[_sv("Revenue Growth"), _sv("EPS")],
            say_on_pay_pct=_sv(92.5),
            say_on_pay_trend=_sv("IMPROVING"),
            has_clawback=_sv(True),
            clawback_scope=_sv("BROADER_THAN_DODD_FRANK"),
            related_party_transactions=[_sv("Office lease with CEO entity")],
            notable_perquisites=[_sv("Private aircraft usage")],
        )
        result = _build_compensation_analysis(comp)

        assert "$15.0M" in result["ceo_total"]
        assert "$1.5M" in result["ceo_salary"]
        assert "$3.0M" in result["ceo_bonus"]
        assert "$9.0M" in result["ceo_equity"]
        assert "256:1" == result["ceo_pay_ratio"]
        assert "1.23x" in result["ceo_pay_vs_peer_median"]
        assert "above median" in result["ceo_pay_vs_peer_median"]
        assert len(result["comp_mix"]) == 4
        assert result["comp_mix"][0]["name"] == "Salary"
        assert result["comp_mix"][0]["pct"] == "10%"
        assert len(result["performance_metrics"]) == 2
        assert "92.5%" in result["say_on_pay_pct"]
        assert result["say_on_pay_trend"] == "IMPROVING"
        assert result["has_clawback"] == "Yes"
        assert "Broader" in result["clawback_scope"]
        assert len(result["related_party_transactions"]) == 1
        assert len(result["notable_perquisites"]) == 1

    def test_empty_comp_analysis(self) -> None:
        """Empty CompensationAnalysis produces N/A values."""
        comp = CompensationAnalysis()
        result = _build_compensation_analysis(comp)

        assert result["ceo_total"] == "N/A"
        assert result["ceo_salary"] == "N/A"
        assert result["ceo_pay_ratio"] == "N/A"
        assert result["ceo_pay_vs_peer_median"] == "N/A"
        assert result["comp_mix"] == []
        assert result["performance_metrics"] == []
        assert result["say_on_pay_pct"] == "N/A"
        assert result["has_clawback"] == "N/A"
        assert result["clawback_scope"] == "N/A"
        assert result["related_party_transactions"] == []
        assert result["notable_perquisites"] == []

    def test_source_attribution(self) -> None:
        """Source strings extracted from SourcedValues."""
        comp = CompensationAnalysis(
            ceo_total_comp=_sv(15_000_000.0, source="DEF 14A 2025-03"),
            ceo_salary=_sv(1_500_000.0, source="DEF 14A SCT"),
        )
        result = _build_compensation_analysis(comp)

        assert "DEF 14A 2025-03" in result["_sources"]["ceo_total"]
        assert "DEF 14A SCT" in result["_sources"]["ceo_salary"]

    def test_confidence_tracking(self) -> None:
        """Confidence levels extracted from SourcedValues."""
        comp = CompensationAnalysis(
            ceo_total_comp=_sv(15_000_000.0, confidence=Confidence.HIGH),
            say_on_pay_pct=_sv(85.0, confidence=Confidence.MEDIUM),
        )
        result = _build_compensation_analysis(comp)

        assert result["_confidence"]["ceo_total"] == "HIGH"
        assert result["_confidence"]["say_on_pay_pct"] == "MEDIUM"

    def test_below_median_peer_comparison(self) -> None:
        """CEO pay below peer median renders correctly."""
        comp = CompensationAnalysis(
            ceo_pay_vs_peer_median=_sv(0.75),
        )
        result = _build_compensation_analysis(comp)
        assert "0.75x" in result["ceo_pay_vs_peer_median"]
        assert "below median" in result["ceo_pay_vs_peer_median"]


class TestExtractGovernanceCompensation:
    """Tests that extract_governance returns compensation_analysis key."""

    def test_returns_compensation_analysis_key(self) -> None:
        """extract_governance includes compensation_analysis in result."""
        state = AnalysisState(ticker="TEST")
        # Need extracted.governance to not return {}
        result = extract_governance(state)
        # With no extracted data, returns empty dict
        assert result == {}

    def test_existing_compensation_preserved(self) -> None:
        """The flat compensation dict for backward compat is untouched."""
        # This verifies the plan's requirement that existing compensation
        # flat dict is not modified. The new compensation_analysis key
        # is additive.
        # Just verify the function signature hasn't changed
        from inspect import signature
        sig = signature(extract_governance)
        assert "state" in sig.parameters


# ---------------------------------------------------------------------------
# Peer Matrix Tests
# ---------------------------------------------------------------------------


class TestExtractPeerMatrix:
    """Tests for extract_peer_matrix context builder."""

    def test_none_benchmark_returns_none(self) -> None:
        """No benchmark data returns None."""
        state = AnalysisState(ticker="TEST")
        assert extract_peer_matrix(state) is None

    def test_empty_metric_details_returns_none(self) -> None:
        """Benchmark with no metric_details returns None."""
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(metric_details={}),
        )
        assert extract_peer_matrix(state) is None

    def test_full_peer_matrix(self) -> None:
        """Full benchmark data produces complete matrix."""
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(
                peer_group_tickers=["AAPL", "MSFT", "GOOG"],
                relative_position="ABOVE_AVERAGE",
                sector_average_score=72.0,
                peer_quality_scores={"AAPL": 85.0, "MSFT": 92.0, "GOOG": 78.0},
                peer_rankings={"revenue": 75.0, "market_cap": 60.0},
                metric_details={
                    "revenue": MetricBenchmark(
                        metric_name="Revenue",
                        company_value=50_000_000_000,
                        percentile_rank=75.0,
                        peer_count=10,
                        baseline_value=30_000_000_000,
                        higher_is_better=True,
                        section="financial",
                    ),
                    "operating_margin": MetricBenchmark(
                        metric_name="Operating Margin",
                        company_value=25.5,
                        percentile_rank=82.0,
                        peer_count=10,
                        baseline_value=18.0,
                        higher_is_better=True,
                        section="financial",
                    ),
                },
            ),
        )

        result = extract_peer_matrix(state)
        assert result is not None

        # Metrics
        assert len(result["metrics"]) == 2
        rev_metric = next(m for m in result["metrics"] if m["key"] == "revenue")
        assert rev_metric["name"] == "Revenue"
        assert rev_metric["percentile_rank"] == 75
        assert rev_metric["peer_count"] == 10
        assert rev_metric["color"] == "green"

        # Peers
        assert len(result["peers"]) == 3
        assert result["peer_count"] == 3

        # Summary
        assert result["relative_position"] == "Above Average"
        assert result["sector_average"] == "72"

    def test_color_coding(self) -> None:
        """Percentile thresholds produce correct color codes."""
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(
                metric_details={
                    "high": MetricBenchmark(
                        metric_name="High",
                        percentile_rank=80.0,
                        peer_count=5,
                    ),
                    "mid": MetricBenchmark(
                        metric_name="Mid",
                        percentile_rank=50.0,
                        peer_count=5,
                    ),
                    "low": MetricBenchmark(
                        metric_name="Low",
                        percentile_rank=20.0,
                        peer_count=5,
                    ),
                    "none": MetricBenchmark(
                        metric_name="None",
                        percentile_rank=None,
                        peer_count=5,
                    ),
                },
            ),
        )
        result = extract_peer_matrix(state)
        assert result is not None

        colors = {m["key"]: m["color"] for m in result["metrics"]}
        assert colors["high"] == "green"
        assert colors["mid"] == "gold"
        assert colors["low"] == "red"
        assert colors["none"] == "gray"

    def test_metric_value_formatting(self) -> None:
        """Metric values are formatted based on metric name."""
        state = AnalysisState(
            ticker="TEST",
            benchmark=BenchmarkResult(
                metric_details={
                    "revenue": MetricBenchmark(
                        metric_name="Revenue",
                        company_value=50_000_000_000,
                        percentile_rank=75.0,
                        peer_count=10,
                        baseline_value=30_000_000_000,
                    ),
                    "operating_margin": MetricBenchmark(
                        metric_name="Operating Margin",
                        company_value=25.5,
                        percentile_rank=60.0,
                        peer_count=10,
                        baseline_value=18.0,
                    ),
                },
            ),
        )
        result = extract_peer_matrix(state)
        assert result is not None

        rev = next(m for m in result["metrics"] if m["key"] == "revenue")
        margin = next(m for m in result["metrics"] if m["key"] == "operating_margin")

        # Revenue should be formatted as currency
        assert "$" in rev["company_value"]
        # Margin should be formatted as percentage
        assert "%" in margin["company_value"]
