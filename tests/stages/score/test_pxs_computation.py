"""Tests for P x S computation, zone classification, SeverityScoringLens,
scenario table generation, layer erosion integration, and calibration report.

Phase 108 Plan 02 Task 1: TDD RED then GREEN.
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.severity import (
    SeverityResult,
    SeverityZone,
)


# ---------------------------------------------------------------------------
# P x S expected loss computation
# ---------------------------------------------------------------------------


class TestPxSExpectedLoss:
    """P x S = probability x severity."""

    def test_p_x_s_expected_loss(self) -> None:
        """P=0.15, S=$50M -> EL=$7.5M."""
        from do_uw.stages.score.severity_scoring import compute_p_x_s

        result = compute_p_x_s(0.15, 50_000_000)
        assert result == pytest.approx(7_500_000, rel=1e-6)

    def test_p_x_s_zero_probability(self) -> None:
        """Zero probability -> zero EL."""
        from do_uw.stages.score.severity_scoring import compute_p_x_s

        assert compute_p_x_s(0.0, 100_000_000) == 0.0

    def test_p_x_s_zero_severity(self) -> None:
        """Zero severity -> zero EL."""
        from do_uw.stages.score.severity_scoring import compute_p_x_s

        assert compute_p_x_s(0.50, 0.0) == 0.0


# ---------------------------------------------------------------------------
# Zone classification
# ---------------------------------------------------------------------------


class TestZoneClassification:
    """Zone classification matches severity_model_design.yaml criteria."""

    def test_zone_green(self) -> None:
        """P=0.05, S=$5M -> GREEN."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.05, 5_000_000) == SeverityZone.GREEN

    def test_zone_yellow_high_p(self) -> None:
        """P=0.15, S=$5M -> YELLOW (P elevated)."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.15, 5_000_000) == SeverityZone.YELLOW

    def test_zone_yellow_high_s(self) -> None:
        """P=0.05, S=$15M -> YELLOW (S elevated)."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.05, 15_000_000) == SeverityZone.YELLOW

    def test_zone_orange(self) -> None:
        """P=0.30, S=$30M -> ORANGE."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.30, 30_000_000) == SeverityZone.ORANGE

    def test_zone_orange_high_s_only(self) -> None:
        """P=0.05, S=$55M -> ORANGE (S >= $50M alone)."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.05, 55_000_000) == SeverityZone.ORANGE

    def test_zone_red(self) -> None:
        """P=0.40, S=$80M -> RED."""
        from do_uw.stages.score.severity_scoring import classify_zone

        assert classify_zone(0.40, 80_000_000) == SeverityZone.RED


# ---------------------------------------------------------------------------
# SeverityScoringLens full evaluation
# ---------------------------------------------------------------------------


class TestSeverityScoringLens:
    """SeverityScoringLens.evaluate() orchestrates full severity pipeline."""

    def _make_mock_company(
        self, market_cap: float = 20_000_000_000
    ) -> MagicMock:
        """Build a mock company with market_cap."""
        company = MagicMock()
        company.market_cap = MagicMock()
        company.market_cap.value = market_cap
        company.identity.sector = MagicMock()
        company.identity.sector.value = "technology"
        return company

    def _make_mock_state(
        self, market_cap: float = 20_000_000_000
    ) -> MagicMock:
        """Build a mock AnalysisState."""
        state = MagicMock()
        state.company = self._make_mock_company(market_cap)

        # Stock drops
        drop = MagicMock()
        drop.drop_pct = MagicMock()
        drop.drop_pct.value = -35.0
        state.extracted.market.stock_drops.single_day_drops = [drop]
        state.extracted.market.stock_drops.multi_day_drops = []

        # Stock volume/shares
        state.extracted.market.stock.average_volume = MagicMock()
        state.extracted.market.stock.average_volume.value = 10_000_000
        state.extracted.market.stock.shares_outstanding = MagicMock()
        state.extracted.market.stock.shares_outstanding.value = 1_000_000_000

        # Analysis
        state.analysis.signal_results = {}

        return state

    def test_full_lens_evaluation(self) -> None:
        """Mock company ($20B mcap, 35% drop) -> settlement in range."""
        from do_uw.stages.score.severity_scoring import SeverityScoringLens

        lens = SeverityScoringLens()
        signal_results: dict[str, Any] = {}
        company = self._make_mock_company(20_000_000_000)

        # Mock hae_result
        hae_result = MagicMock()
        hae_result.product_score = 0.15
        hae_result.tier = MagicMock()
        hae_result.tier.value = "ELEVATED"
        hae_result.composites = {"host": 0.10, "agent": 0.20, "environment": 0.08}

        result = lens.evaluate(
            signal_results,
            company=company,
            hae_result=hae_result,
        )

        assert result.estimated_settlement > 0
        assert result.lens_name == "v7_severity_scoring"
        assert result.zone in list(SeverityZone)
        assert len(result.scenarios) > 0

    def test_scenario_table_completeness(self) -> None:
        """Scenario table has 3 drop levels for primary allegation."""
        from do_uw.stages.score.severity_scoring import SeverityScoringLens

        lens = SeverityScoringLens()
        signal_results: dict[str, Any] = {}
        company = self._make_mock_company()

        hae_result = MagicMock()
        hae_result.product_score = 0.15
        hae_result.tier = MagicMock()
        hae_result.tier.value = "STANDARD"
        hae_result.composites = {"host": 0.05, "agent": 0.08, "environment": 0.03}

        result = lens.evaluate(
            signal_results,
            company=company,
            hae_result=hae_result,
        )

        # At minimum 3 scenarios (worst_actual, sector_median, catastrophic)
        assert len(result.scenarios) >= 3
        drop_levels = {s.drop_level for s in result.scenarios}
        assert "worst_actual" in drop_levels or "sector_median" in drop_levels

    def test_layer_erosion_with_attachment(self) -> None:
        """$25M attachment produces layer erosion result."""
        from do_uw.stages.score.severity_scoring import SeverityScoringLens

        lens = SeverityScoringLens()
        signal_results: dict[str, Any] = {}
        company = self._make_mock_company(20_000_000_000)

        hae_result = MagicMock()
        hae_result.product_score = 0.20
        hae_result.tier = MagicMock()
        hae_result.tier.value = "ELEVATED"
        hae_result.composites = {"host": 0.10, "agent": 0.20, "environment": 0.08}

        result = lens.evaluate(
            signal_results,
            company=company,
            liberty_attachment=25_000_000,
            liberty_product="ABC",
            hae_result=hae_result,
        )

        assert result.layer_erosion is not None
        assert len(result.layer_erosion) > 0
        erosion = result.layer_erosion[0]
        assert erosion.attachment == 25_000_000
        assert 0.0 <= erosion.penetration_probability <= 1.0

    def test_lens_conforms_to_protocol(self) -> None:
        """SeverityScoringLens satisfies SeverityLens protocol."""
        from do_uw.stages.score.severity_lens import SeverityLens
        from do_uw.stages.score.severity_scoring import SeverityScoringLens

        lens = SeverityScoringLens()
        assert isinstance(lens, SeverityLens)


# ---------------------------------------------------------------------------
# build_severity_result
# ---------------------------------------------------------------------------


class TestBuildSeverityResult:
    """build_severity_result combines P and S into SeverityResult."""

    def test_build_severity_result(self) -> None:
        """Combines primary, legacy, and HAE into SeverityResult."""
        from do_uw.models.severity import SeverityLensResult, SeverityZone
        from do_uw.stages.score.severity_scoring import build_severity_result

        primary = SeverityLensResult(
            lens_name="primary",
            estimated_settlement=50_000_000,
            damages_estimate=80_000_000,
            zone=SeverityZone.YELLOW,
        )
        legacy = SeverityLensResult(
            lens_name="legacy",
            estimated_settlement=40_000_000,
            damages_estimate=60_000_000,
            zone=SeverityZone.YELLOW,
        )
        hae = MagicMock()
        hae.product_score = 0.15

        result = build_severity_result(primary, legacy, hae)

        assert isinstance(result, SeverityResult)
        assert result.probability == pytest.approx(0.15)
        assert result.severity == pytest.approx(50_000_000)
        assert result.expected_loss == pytest.approx(7_500_000, rel=1e-6)
        assert result.zone in list(SeverityZone)
        assert result.primary is not None
        assert result.legacy is not None


# ---------------------------------------------------------------------------
# Calibration report
# ---------------------------------------------------------------------------


class TestCalibrationReport:
    """generate_severity_calibration_report produces comparison HTML."""

    def test_calibration_report_generates(self) -> None:
        """Calibration report produces HTML with comparison table."""
        from do_uw.stages.score.severity_scoring import (
            generate_severity_calibration_report,
        )

        html = generate_severity_calibration_report()
        assert isinstance(html, str)
        assert len(html) > 500
        assert "<html" in html.lower() or "<table" in html.lower()
        # Should reference known cases
        assert "Enron" in html or "enron" in html.lower()

    def test_calibration_report_has_metrics(self) -> None:
        """Report includes error metrics (MAE, bias, etc.)."""
        from do_uw.stages.score.severity_scoring import (
            generate_severity_calibration_report,
        )

        html = generate_severity_calibration_report()
        # Should contain error metric labels
        assert "MAE" in html or "Error" in html or "error" in html.lower()
