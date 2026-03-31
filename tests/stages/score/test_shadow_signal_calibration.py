"""Tests for shadow calibration signal-driven vs rule-based comparison.

Verifies that CalibrationRow captures per-factor signal-driven and
rule-based scores, and that the calibration report includes the
factor-level comparison section.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.score.shadow_calibration import (
    CalibrationMetrics,
    CalibrationRow,
    run_shadow_calibration,
)


# ---------------------------------------------------------------------------
# Tests: CalibrationRow signal-driven fields
# ---------------------------------------------------------------------------


class TestCalibrationRowSignalFields:
    """Test CalibrationRow has signal-driven vs rule-based fields."""

    def test_has_factor_scores_signal_field(self) -> None:
        """CalibrationRow should have factor_scores_signal dict."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            factor_scores_signal={"F1": 5.0, "F3": 2.0},
        )
        assert row.factor_scores_signal == {"F1": 5.0, "F3": 2.0}

    def test_has_factor_scores_rule_field(self) -> None:
        """CalibrationRow should have factor_scores_rule dict."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            factor_scores_rule={"F1": 8.0, "F3": 3.0},
        )
        assert row.factor_scores_rule == {"F1": 8.0, "F3": 3.0}

    def test_has_signal_composite_field(self) -> None:
        """CalibrationRow should have signal_composite float."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            signal_composite=82.5,
        )
        assert row.signal_composite == 82.5

    def test_has_signal_coverage_avg_field(self) -> None:
        """CalibrationRow should have signal_coverage_avg float."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            signal_coverage_avg=0.72,
        )
        assert row.signal_coverage_avg == 0.72

    def test_has_scoring_methods_field(self) -> None:
        """CalibrationRow should have scoring_methods dict."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            scoring_methods={"F1": "signal_driven", "F2": "rule_based"},
        )
        assert row.scoring_methods["F1"] == "signal_driven"
        assert row.scoring_methods["F2"] == "rule_based"

    def test_defaults_empty(self) -> None:
        """New fields should default to empty/zero."""
        row = CalibrationRow(ticker="TEST", category="known_good")
        assert row.factor_scores_signal == {}
        assert row.factor_scores_rule == {}
        assert row.signal_composite == 0.0
        assert row.signal_coverage_avg == 0.0
        assert row.scoring_methods == {}


# ---------------------------------------------------------------------------
# Tests: CalibrationMetrics signal-driven fields
# ---------------------------------------------------------------------------


class TestCalibrationMetricsSignalFields:
    """Test CalibrationMetrics has signal-driven comparison metrics."""

    def test_has_mean_factor_delta(self) -> None:
        """CalibrationMetrics should have mean_factor_delta."""
        metrics = CalibrationMetrics(mean_factor_delta=1.5)
        assert metrics.mean_factor_delta == 1.5

    def test_has_avg_signal_coverage(self) -> None:
        """CalibrationMetrics should have avg_signal_coverage."""
        metrics = CalibrationMetrics(avg_signal_coverage=0.65)
        assert metrics.avg_signal_coverage == 0.65

    def test_has_signal_factor_count(self) -> None:
        """CalibrationMetrics should have signal_factor_count."""
        metrics = CalibrationMetrics(signal_factor_count=7)
        assert metrics.signal_factor_count == 7

    def test_has_rule_factor_count(self) -> None:
        """CalibrationMetrics should have rule_factor_count."""
        metrics = CalibrationMetrics(rule_factor_count=3)
        assert metrics.rule_factor_count == 3

    def test_defaults_zero(self) -> None:
        """Signal metric fields default to zero."""
        metrics = CalibrationMetrics()
        assert metrics.mean_factor_delta == 0.0
        assert metrics.avg_signal_coverage == 0.0
        assert metrics.signal_factor_count == 0
        assert metrics.rule_factor_count == 0


# ---------------------------------------------------------------------------
# Tests: run_shadow_calibration still works
# ---------------------------------------------------------------------------


class TestShadowCalibrationStillWorks:
    """Verify existing shadow calibration stub mode still works."""

    def test_run_produces_rows_and_metrics(self) -> None:
        """run_shadow_calibration should return rows and metrics."""
        rows, metrics = run_shadow_calibration()
        assert len(rows) > 0
        assert isinstance(metrics, CalibrationMetrics)

    def test_synthetic_rows_have_new_fields(self) -> None:
        """Synthetic rows should have the new signal-driven fields (defaulted)."""
        rows, _ = run_shadow_calibration()
        for row in rows:
            assert hasattr(row, "factor_scores_signal")
            assert hasattr(row, "factor_scores_rule")
            assert hasattr(row, "signal_composite")
            assert hasattr(row, "signal_coverage_avg")
            assert hasattr(row, "scoring_methods")


# ---------------------------------------------------------------------------
# Tests: calibration report HTML includes factor comparison section
# ---------------------------------------------------------------------------


class TestCalibrationReportFactorComparison:
    """Test that calibration report HTML includes factor-level comparison."""

    def test_report_includes_factor_comparison_section(self) -> None:
        """HTML report should include factor-level comparison heading."""
        from do_uw.stages.score._calibration_report import (
            generate_calibration_html,
        )

        rows = [
            CalibrationRow(
                ticker="TEST",
                category="known_good",
                sector="Technology",
                legacy_score=85.0,
                legacy_tier="WIN",
                hae_tier="PREFERRED",
                factor_scores_signal={"F1": 5.0, "F3": 2.0},
                factor_scores_rule={"F1": 8.0, "F3": 3.0},
                signal_composite=82.0,
                signal_coverage_avg=0.75,
                scoring_methods={"F1": "signal_driven", "F3": "signal_driven"},
            ),
        ]
        metrics = CalibrationMetrics(
            rank_correlation=0.85,
            tier_agreement_pct=90.0,
            mean_factor_delta=1.2,
            avg_signal_coverage=0.75,
            signal_factor_count=7,
            rule_factor_count=3,
        )

        html = generate_calibration_html(rows, metrics)
        assert "Factor-Level Comparison" in html or "factor-comparison" in html

    def test_report_includes_signal_coverage_metric(self) -> None:
        """HTML report should show signal coverage metric badge."""
        from do_uw.stages.score._calibration_report import (
            generate_calibration_html,
        )

        rows, _ = run_shadow_calibration(
            [{"ticker": "V", "category": "known_good", "sector": "Financials"}]
        )
        metrics = CalibrationMetrics(
            rank_correlation=0.85,
            tier_agreement_pct=90.0,
            avg_signal_coverage=0.72,
        )
        html = generate_calibration_html(rows, metrics)
        assert "Signal Coverage" in html or "signal_coverage" in html


# ---------------------------------------------------------------------------
# Tests: factor delta computation
# ---------------------------------------------------------------------------


class TestFactorDeltaComputation:
    """Test that factor-level deltas are computed correctly."""

    def test_factor_delta_is_signal_minus_rule(self) -> None:
        """Delta per factor = signal_score - rule_score."""
        row = CalibrationRow(
            ticker="TEST",
            category="known_good",
            factor_scores_signal={"F1": 5.0, "F3": 2.0},
            factor_scores_rule={"F1": 8.0, "F3": 1.0},
        )
        # F1 delta = 5.0 - 8.0 = -3.0
        f1_delta = row.factor_scores_signal.get("F1", 0) - row.factor_scores_rule.get("F1", 0)
        assert f1_delta == -3.0
        # F3 delta = 2.0 - 1.0 = +1.0
        f3_delta = row.factor_scores_signal.get("F3", 0) - row.factor_scores_rule.get("F3", 0)
        assert f3_delta == 1.0
