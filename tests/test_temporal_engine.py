"""Unit tests for temporal change detection engine.

Tests the TemporalAnalyzer classification logic including:
- All 4 classification states (IMPROVING/STABLE/DETERIORATING/CRITICAL)
- Direction-awareness (higher_is_worse vs lower_is_worse)
- Edge cases: insufficient data, zero division, mixed trends
- Evidence narrative generation
- TemporalSignal model correctness
"""

from __future__ import annotations

import pytest

from do_uw.models.temporal import (
    TemporalClassification,
    TemporalSignal,
)
from do_uw.stages.analyze.temporal_engine import TemporalAnalyzer


@pytest.fixture()
def analyzer() -> TemporalAnalyzer:
    """Create a TemporalAnalyzer with default config."""
    return TemporalAnalyzer({
        "consecutive_adverse_threshold": 3,
        "critical_consecutive_threshold": 4,
    })


class TestClassifyTemporalTrend:
    """Tests for classify_temporal_trend method."""

    def test_classify_stable(self, analyzer: TemporalAnalyzer) -> None:
        """Flat values should classify as STABLE."""
        result = analyzer.classify_temporal_trend(
            [100.0, 100.0, 100.0, 100.0], "lower_is_worse"
        )
        assert result == TemporalClassification.STABLE

    def test_classify_deteriorating(self, analyzer: TemporalAnalyzer) -> None:
        """3+ consecutive adverse moves should classify as DETERIORATING."""
        # 3 consecutive declines with lower_is_worse
        result = analyzer.classify_temporal_trend(
            [100.0, 90.0, 80.0, 70.0], "lower_is_worse"
        )
        assert result == TemporalClassification.DETERIORATING

    def test_classify_critical(self, analyzer: TemporalAnalyzer) -> None:
        """4+ consecutive adverse moves should classify as CRITICAL."""
        # 4 consecutive declines (critical_threshold + 1 = 4)
        result = analyzer.classify_temporal_trend(
            [100.0, 90.0, 80.0, 70.0, 60.0], "lower_is_worse"
        )
        assert result == TemporalClassification.CRITICAL

    def test_classify_improving(self, analyzer: TemporalAnalyzer) -> None:
        """3+ consecutive favorable moves should classify as IMPROVING."""
        result = analyzer.classify_temporal_trend(
            [70.0, 80.0, 90.0, 100.0], "lower_is_worse"
        )
        assert result == TemporalClassification.IMPROVING

    def test_direction_higher_is_worse(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """DSO increasing should be detected as adverse when higher_is_worse."""
        # DSO going up = bad
        result = analyzer.classify_temporal_trend(
            [30.0, 35.0, 40.0, 45.0], "higher_is_worse"
        )
        assert result == TemporalClassification.DETERIORATING

    def test_direction_lower_is_worse(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Revenue declining should be detected as adverse when lower_is_worse."""
        result = analyzer.classify_temporal_trend(
            [100.0, 90.0, 80.0, 70.0], "lower_is_worse"
        )
        assert result == TemporalClassification.DETERIORATING

    def test_insufficient_data(self, analyzer: TemporalAnalyzer) -> None:
        """Less than 2 values should return STABLE (graceful degradation)."""
        assert (
            analyzer.classify_temporal_trend([100.0], "lower_is_worse")
            == TemporalClassification.STABLE
        )
        assert (
            analyzer.classify_temporal_trend([], "lower_is_worse")
            == TemporalClassification.STABLE
        )

    def test_mixed_trend(self, analyzer: TemporalAnalyzer) -> None:
        """Up-down-up-down pattern should classify as STABLE (no consecutive run)."""
        result = analyzer.classify_temporal_trend(
            [100.0, 110.0, 90.0, 120.0, 80.0], "lower_is_worse"
        )
        assert result == TemporalClassification.STABLE

    def test_two_values_only(self, analyzer: TemporalAnalyzer) -> None:
        """Two values with one adverse move should be STABLE (below threshold)."""
        result = analyzer.classify_temporal_trend(
            [100.0, 90.0], "lower_is_worse"
        )
        assert result == TemporalClassification.STABLE

    def test_higher_is_worse_improving(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """DSO decreasing should classify as IMPROVING when higher_is_worse."""
        result = analyzer.classify_temporal_trend(
            [45.0, 40.0, 35.0, 30.0], "higher_is_worse"
        )
        assert result == TemporalClassification.IMPROVING


class TestAnalyzeMetric:
    """Tests for analyze_metric method."""

    def test_total_change_pct(self, analyzer: TemporalAnalyzer) -> None:
        """Correct percentage calculation from first to last value."""
        signal = analyzer.analyze_metric(
            "revenue_growth",
            [100.0, 90.0, 80.0, 70.0],
            ["FY2021", "FY2022", "FY2023", "FY2024"],
            "lower_is_worse",
        )
        assert signal.total_change_pct == pytest.approx(-30.0, abs=0.1)

    def test_zero_division_handling(self, analyzer: TemporalAnalyzer) -> None:
        """First value is 0 should not crash, returns 0.0 change."""
        signal = analyzer.analyze_metric(
            "test_metric",
            [0.0, 10.0, 20.0],
            ["Q1", "Q2", "Q3"],
            "lower_is_worse",
        )
        assert signal.total_change_pct == 0.0

    def test_evidence_narrative(self, analyzer: TemporalAnalyzer) -> None:
        """Evidence string should contain metric name and values."""
        signal = analyzer.analyze_metric(
            "revenue_growth",
            [100.0, 90.0, 80.0, 70.0],
            ["FY2021", "FY2022", "FY2023", "FY2024"],
            "lower_is_worse",
        )
        assert "Revenue Growth" in signal.evidence
        assert "FY2021" in signal.evidence
        assert "FY2024" in signal.evidence

    def test_analyze_metric_returns_temporal_signal(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Correct model type returned with proper fields."""
        signal = analyzer.analyze_metric(
            "dso_days",
            [30.0, 35.0, 40.0, 45.0],
            ["FY2021", "FY2022", "FY2023", "FY2024"],
            "higher_is_worse",
        )
        assert isinstance(signal, TemporalSignal)
        assert signal.metric_name == "dso_days"
        assert signal.classification == TemporalClassification.DETERIORATING
        assert signal.consecutive_adverse == 3
        assert len(signal.periods) == 4
        assert len(signal.source_periods) == 4

    def test_insufficient_data_returns_stable_signal(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Less than 2 data points should return STABLE with evidence."""
        signal = analyzer.analyze_metric(
            "revenue_growth", [100.0], ["FY2024"], "lower_is_worse"
        )
        assert signal.classification == TemporalClassification.STABLE
        assert "Insufficient" in signal.evidence

    def test_stable_evidence_narrative(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Stable classification should have appropriate evidence."""
        signal = analyzer.analyze_metric(
            "operating_margin",
            [25.0, 25.0, 25.0],
            ["FY2022", "FY2023", "FY2024"],
            "lower_is_worse",
        )
        assert signal.classification == TemporalClassification.STABLE
        assert "stable" in signal.evidence.lower()

    def test_improving_evidence_narrative(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Improving classification should mention improvement."""
        signal = analyzer.analyze_metric(
            "operating_cash_flow",
            [50.0, 60.0, 70.0, 80.0],
            ["FY2021", "FY2022", "FY2023", "FY2024"],
            "lower_is_worse",
        )
        assert signal.classification == TemporalClassification.IMPROVING
        assert "improved" in signal.evidence.lower()

    def test_critical_evidence_has_critically(
        self, analyzer: TemporalAnalyzer
    ) -> None:
        """Critical classification evidence should contain 'critically'."""
        signal = analyzer.analyze_metric(
            "debt_ratio",
            [0.3, 0.4, 0.5, 0.6, 0.7],
            ["FY2020", "FY2021", "FY2022", "FY2023", "FY2024"],
            "higher_is_worse",
        )
        assert signal.classification == TemporalClassification.CRITICAL
        assert "critically" in signal.evidence.lower()


class TestAnalyzerConfig:
    """Tests for TemporalAnalyzer configuration."""

    def test_default_config_loads(self) -> None:
        """TemporalAnalyzer should load default config without error."""
        analyzer = TemporalAnalyzer()
        # Should have defaults from temporal_thresholds.json
        assert analyzer._consecutive_threshold >= 1

    def test_custom_threshold(self) -> None:
        """Custom consecutive threshold should override default."""
        analyzer = TemporalAnalyzer({
            "consecutive_adverse_threshold": 2,
            "critical_consecutive_threshold": 3,
        })
        # With threshold of 2, two consecutive drops should be DETERIORATING
        result = analyzer.classify_temporal_trend(
            [100.0, 90.0, 80.0], "lower_is_worse"
        )
        assert result == TemporalClassification.DETERIORATING

    def test_empty_config_uses_defaults(self) -> None:
        """Empty config dict should fall back to coded defaults."""
        analyzer = TemporalAnalyzer({})
        assert analyzer._consecutive_threshold == 3
        assert analyzer._critical_threshold == 4
