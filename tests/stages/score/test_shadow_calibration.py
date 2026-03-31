"""Tests for legacy lens adapter and shadow calibration.

Covers: LegacyScoringLens tier mapping, score normalization,
lens_name, and ScoringLensResult construction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.models.scoring import _rebuild_scoring_models

# Resolve ScoringResult forward ref to ScoringLensResult
_rebuild_scoring_models()


# ---------------------------------------------------------------
# Task 1: Legacy lens adapter tests
# ---------------------------------------------------------------


class TestLegacyLensWinMapsToPreferred:
    """WIN legacy tier maps to PREFERRED HAETier."""

    def test_win_maps_to_preferred(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["WIN"] == "PREFERRED"


class TestLegacyLensNoTouchMapsToProhibited:
    """NO_TOUCH legacy tier maps to PROHIBITED HAETier."""

    def test_no_touch_maps_to_prohibited(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["NO_TOUCH"] == "PROHIBITED"


class TestLegacyLensNormalizesScore:
    """Legacy lens normalizes quality_score to [0, 1] product_score."""

    def test_normalizes_score_85(self) -> None:
        from do_uw.models.scoring import ScoringResult, TierClassification, Tier
        from do_uw.stages.score.legacy_lens import LegacyScoringLens

        scoring = ScoringResult(
            quality_score=85.0,
            tier=TierClassification(
                tier=Tier.WIN,
                score_range_low=86,
                score_range_high=100,
            ),
        )
        lens = LegacyScoringLens(scoring)
        result = lens.evaluate({})
        assert result.product_score == pytest.approx(0.85, abs=0.01)

    def test_normalizes_score_42(self) -> None:
        from do_uw.models.scoring import ScoringResult, TierClassification, Tier
        from do_uw.stages.score.legacy_lens import LegacyScoringLens

        scoring = ScoringResult(
            quality_score=42.0,
            tier=TierClassification(
                tier=Tier.WALK,
                score_range_low=11,
                score_range_high=30,
            ),
        )
        lens = LegacyScoringLens(scoring)
        result = lens.evaluate({})
        assert result.product_score == pytest.approx(0.42, abs=0.01)


class TestLegacyLensResultHasLensName:
    """Legacy lens result has lens_name='legacy_10_factor'."""

    def test_lens_name(self) -> None:
        from do_uw.models.scoring import ScoringResult, TierClassification, Tier
        from do_uw.stages.score.legacy_lens import LegacyScoringLens

        scoring = ScoringResult(
            quality_score=75.0,
            tier=TierClassification(
                tier=Tier.WRITE,
                score_range_low=51,
                score_range_high=70,
            ),
        )
        lens = LegacyScoringLens(scoring)
        result = lens.evaluate({})
        assert result.lens_name == "legacy_10_factor"


class TestLegacyTierMapCompleteness:
    """All legacy tiers are mapped."""

    def test_all_tiers_mapped(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        expected = {"WIN", "WANT", "WRITE", "WATCH", "WALK", "NO_TOUCH"}
        assert set(LEGACY_TIER_MAP.keys()) == expected

    def test_want_maps_to_standard(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["WANT"] == "STANDARD"

    def test_write_maps_to_standard(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["WRITE"] == "STANDARD"

    def test_watch_maps_to_elevated(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["WATCH"] == "ELEVATED"

    def test_walk_maps_to_high_risk(self) -> None:
        from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP

        assert LEGACY_TIER_MAP["WALK"] == "HIGH_RISK"


class TestLegacyLensComposites:
    """Legacy lens composites are placeholder zeros."""

    def test_composites_all_zero(self) -> None:
        from do_uw.models.scoring import ScoringResult, TierClassification, Tier
        from do_uw.stages.score.legacy_lens import LegacyScoringLens

        scoring = ScoringResult(
            quality_score=90.0,
            tier=TierClassification(
                tier=Tier.WIN,
                score_range_low=86,
                score_range_high=100,
            ),
        )
        lens = LegacyScoringLens(scoring)
        result = lens.evaluate({})
        assert result.composites == {"host": 0, "agent": 0, "environment": 0}


class TestLegacyLensNoTier:
    """Legacy lens handles missing tier gracefully."""

    def test_no_tier_defaults_to_standard(self) -> None:
        from do_uw.models.scoring import ScoringResult
        from do_uw.stages.score.legacy_lens import LegacyScoringLens

        scoring = ScoringResult(quality_score=50.0, tier=None)
        lens = LegacyScoringLens(scoring)
        result = lens.evaluate({})
        assert result.tier.value == "STANDARD"


# ---------------------------------------------------------------
# Task 2: Shadow calibration tests
# ---------------------------------------------------------------


class TestCalibrationTickersDiversity:
    """Calibration ticker universe has required diversity."""

    def test_at_least_30_tickers(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        assert len(CALIBRATION_TICKERS) >= 30

    def test_at_least_4_sectors(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        sectors = {t.get("sector", "") for t in CALIBRATION_TICKERS}
        sectors.discard("")
        assert len(sectors) >= 4

    def test_all_4_categories_present(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        categories = {t["category"] for t in CALIBRATION_TICKERS}
        assert {"known_good", "known_bad", "edge_case", "recent_actual"} <= categories

    def test_known_good_count(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        count = sum(1 for t in CALIBRATION_TICKERS if t["category"] == "known_good")
        assert count >= 8

    def test_known_bad_count(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        count = sum(1 for t in CALIBRATION_TICKERS if t["category"] == "known_bad")
        assert count >= 5

    def test_each_ticker_has_expected_tier_range(self) -> None:
        from do_uw.stages.score.shadow_calibration import CALIBRATION_TICKERS

        for t in CALIBRATION_TICKERS:
            assert "expected_tier_range" in t, f"{t['ticker']} missing expected_tier_range"
            assert len(t["expected_tier_range"]) == 2


class TestCalibrationRowConstruction:
    """CalibrationRow has all required fields populated."""

    def test_all_fields_populated(self) -> None:
        from do_uw.stages.score.shadow_calibration import CalibrationRow

        row = CalibrationRow(
            ticker="TEST",
            category="edge_case",
            sector="Technology",
            market_cap_tier="large",
            legacy_score=65.0,
            legacy_tier="WRITE",
            host_composite=0.25,
            agent_composite=0.35,
            environment_composite=0.20,
            hae_product=0.0175,
            hae_tier="STANDARD",
            tier_delta=-1,
            interpretation="H/A/E 1 tier less restrictive",
        )
        assert row.ticker == "TEST"
        assert row.category == "edge_case"
        assert row.legacy_score == 65.0
        assert row.hae_product == 0.0175
        assert row.tier_delta == -1

    def test_uw_fields_default_empty(self) -> None:
        from do_uw.stages.score.shadow_calibration import CalibrationRow

        row = CalibrationRow(ticker="X", category="known_good")
        assert row.uw_assessment == ""
        assert row.uw_rationale == ""


class TestCalibrationMetricsComputation:
    """CalibrationMetrics computed correctly from rows."""

    def test_rank_correlation_computed(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        # Spearman correlation should be positive for well-calibrated models
        assert isinstance(metrics.rank_correlation, float)
        assert -1.0 <= metrics.rank_correlation <= 1.0

    def test_tier_agreement_percentage(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        assert 0.0 <= metrics.tier_agreement_pct <= 100.0

    def test_systematic_bias_computed(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        assert isinstance(metrics.systematic_bias, float)

    def test_all_criteria_met_is_bool(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        assert isinstance(metrics.all_criteria_met, bool)


class TestGenerateHtmlContainsStructure:
    """Generated HTML contains required structural elements."""

    def test_contains_table(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert "<table" in html
        assert "calibration-table" in html

    def test_contains_metrics(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert "Rank Correlation" in html
        assert "Tier Agreement" in html
        assert "Systematic Bias" in html

    def test_contains_uw_inputs(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert 'class="uw-select"' in html
        assert 'class="uw-input"' in html

    def test_contains_export_button(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert "exportAssessments" in html
        assert "Export" in html

    def test_contains_category_tabs(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert "Known Good" in html
        assert "Known Bad" in html
        assert "Edge Cases" in html

    def test_html_is_self_contained(self) -> None:
        from do_uw.stages.score.shadow_calibration import (
            generate_calibration_html,
            run_shadow_calibration,
        )

        rows, metrics = run_shadow_calibration()
        html = generate_calibration_html(rows, metrics)
        assert "<style>" in html
        assert "<script>" in html
        assert "<!DOCTYPE html>" in html


class TestCalibrateFromPipelineNoScoring:
    """calibrate_from_pipeline returns None when scoring data missing."""

    def test_returns_none_no_scoring(self) -> None:
        from unittest.mock import MagicMock

        from do_uw.stages.score.shadow_calibration import calibrate_from_pipeline

        state = MagicMock()
        state.scoring = None
        result = calibrate_from_pipeline(state)
        assert result is None

    def test_returns_none_no_hae_result(self) -> None:
        from unittest.mock import MagicMock

        from do_uw.stages.score.shadow_calibration import calibrate_from_pipeline

        state = MagicMock()
        state.scoring.hae_result = None
        state.scoring.quality_score = 75.0
        state.scoring.tier.tier.value = "WRITE"
        result = calibrate_from_pipeline(state)
        assert result is None


class TestSaveCalibrationReport:
    """save_calibration_report creates file on disk."""

    def test_creates_report_file(self, tmp_path: Path) -> None:
        from pathlib import Path

        from do_uw.stages.score.shadow_calibration import (
            run_shadow_calibration,
            save_calibration_report,
        )

        rows, metrics = run_shadow_calibration()
        result_path = save_calibration_report(rows, metrics, str(tmp_path))
        assert Path(result_path).exists()
        content = Path(result_path).read_text()
        assert "<!DOCTYPE html>" in content
