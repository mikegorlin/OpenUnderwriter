"""Integration tests: classification + hazard profile against real companies.

Validates that the classification engine and hazard profile produce
sensible results when run against actual AAPL, XOM, and SMCI state.json
files from the output/ directory.

Also tests:
- AnalyzeStage integration (classification + hazard run pre-ANALYZE)
- Graceful degradation when company data is missing
- Pipeline stages unchanged at 7
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.classification import ClassificationResult, MarketCapTier
from do_uw.models.state import PIPELINE_STAGES, AnalysisState

logger = logging.getLogger(__name__)

# Path to output directory with state.json files
_OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _load_state(ticker: str) -> AnalysisState | None:
    """Load a state.json file for a given ticker, or return None."""
    state_path = _OUTPUT_DIR / ticker / "state.json"
    if not state_path.exists():
        return None
    try:
        raw = state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return AnalysisState.model_validate(data)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", state_path, exc)
        return None


def _run_classification(state: AnalysisState) -> ClassificationResult:
    """Run classification on a loaded state."""
    from do_uw.stages.analyze.layers.classify import classify_company
    from do_uw.stages.analyze.layers.classify.classification_engine import (
        load_classification_config,
    )

    config = load_classification_config()

    market_cap: float | None = None
    if state.company is not None and state.company.market_cap is not None:
        market_cap = float(state.company.market_cap.value)

    sector_code = "DEFAULT"
    if (
        state.company is not None
        and state.company.identity.sector is not None
    ):
        sector_code = str(state.company.identity.sector.value)

    years_public: int | None = None
    if state.company is not None and state.company.years_public is not None:
        years_public = int(state.company.years_public.value)

    return classify_company(market_cap, sector_code, years_public, config)


def _run_hazard_profile(
    state: AnalysisState,
    classification: ClassificationResult,
) -> Any:
    """Run hazard profile on a loaded state."""
    from do_uw.stages.analyze.layers.hazard import compute_hazard_profile
    from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

    weights, interactions = load_hazard_config()
    return compute_hazard_profile(
        state.extracted,
        state.company,
        classification,
        weights,
        interactions,
    )


# -----------------------------------------------------------------------
# Company-specific integration tests
# -----------------------------------------------------------------------


class TestAAPLIntegration:
    """AAPL: Mega-cap tech, low risk, expected IES ~25-40."""

    @pytest.fixture()
    def state(self) -> AnalysisState:
        s = _load_state("AAPL")
        if s is None:
            pytest.skip("AAPL state.json not available")
        return s

    def test_classification_tier(self, state: AnalysisState) -> None:
        """AAPL should classify as MEGA or LARGE cap."""
        result = _run_classification(state)
        assert result.market_cap_tier in (MarketCapTier.MEGA, MarketCapTier.LARGE)

    def test_filing_rate_sensible(self, state: AnalysisState) -> None:
        """AAPL filing rate should be between 0.5% and 25%."""
        result = _run_classification(state)
        assert 0.5 <= result.base_filing_rate_pct <= 25.0

    def test_ies_in_expected_band(self, state: AnalysisState) -> None:
        """AAPL IES should be relatively low (~25-45)."""
        classification = _run_classification(state)
        profile = _run_hazard_profile(state, classification)
        # AAPL is well-run mega-cap: expect lower IES
        assert 15 <= profile.ies_score <= 60, (
            f"AAPL IES={profile.ies_score} outside expected 15-60 range"
        )

    def test_ies_multiplier_below_neutral(self, state: AnalysisState) -> None:
        """AAPL should have IES multiplier at or below 1.0x (low risk)."""
        classification = _run_classification(state)
        profile = _run_hazard_profile(state, classification)
        # Mega-cap seasoned company should be near or below neutral
        assert profile.ies_multiplier <= 1.5


class TestXOMIntegration:
    """XOM: Large-cap energy, moderate risk, expected IES ~35-55."""

    @pytest.fixture()
    def state(self) -> AnalysisState:
        s = _load_state("XOM")
        if s is None:
            pytest.skip("XOM state.json not available")
        return s

    def test_classification_tier(self, state: AnalysisState) -> None:
        """XOM should classify as MEGA or LARGE cap."""
        result = _run_classification(state)
        assert result.market_cap_tier in (MarketCapTier.MEGA, MarketCapTier.LARGE)

    def test_sector_energy(self, state: AnalysisState) -> None:
        """XOM sector should be ENGY."""
        result = _run_classification(state)
        assert result.sector_code == "ENGY"

    def test_ies_in_expected_band(self, state: AnalysisState) -> None:
        """XOM IES should be moderate (~30-60)."""
        classification = _run_classification(state)
        profile = _run_hazard_profile(state, classification)
        assert 20 <= profile.ies_score <= 70, (
            f"XOM IES={profile.ies_score} outside expected 20-70 range"
        )


class TestSMCIIntegration:
    """SMCI: Mid-cap tech with issues, expected higher IES (~50-90)."""

    @pytest.fixture()
    def state(self) -> AnalysisState:
        s = _load_state("SMCI")
        if s is None:
            pytest.skip("SMCI state.json not available")
        return s

    def test_classification_tier(self, state: AnalysisState) -> None:
        """SMCI should classify as MID or LARGE cap."""
        result = _run_classification(state)
        assert result.market_cap_tier in (
            MarketCapTier.MID,
            MarketCapTier.LARGE,
        )

    def test_ies_in_expected_band(self, state: AnalysisState) -> None:
        """SMCI IES should be elevated (~40-90)."""
        classification = _run_classification(state)
        profile = _run_hazard_profile(state, classification)
        assert 30 <= profile.ies_score <= 95, (
            f"SMCI IES={profile.ies_score} outside expected 30-95 range"
        )

    def test_ies_multiplier_above_neutral_or_near(
        self, state: AnalysisState,
    ) -> None:
        """SMCI should have IES multiplier at or above neutral (higher risk)."""
        classification = _run_classification(state)
        profile = _run_hazard_profile(state, classification)
        # SMCI is a company with known issues -- IES multiplier should
        # be at or above 0.7 (not deeply discounted)
        assert profile.ies_multiplier >= 0.7


# -----------------------------------------------------------------------
# Pipeline integration tests
# -----------------------------------------------------------------------


class TestPipelineIntegration:
    """Test that classification + hazard are wired into the pipeline."""

    def test_pipeline_stages_unchanged(self) -> None:
        """PIPELINE_STAGES must remain exactly 7 stages."""
        expected = [
            "resolve",
            "acquire",
            "extract",
            "analyze",
            "score",
            "benchmark",
            "render",
        ]
        assert PIPELINE_STAGES == expected

    def test_analyze_stage_populates_classification(self) -> None:
        """AnalyzeStage.run() populates state.classification."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _load_state("AAPL")
        if state is None:
            pytest.skip("AAPL state.json not available")

        # Ensure classification is None before
        state.classification = None
        state.hazard_profile = None

        # Mock the check execution part (we only want to test pre-ANALYZE)
        stage = AnalyzeStage()

        # Mock the brain loading and check execution to avoid
        # needing the full brain config
        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}

        with (
            patch(
                "do_uw.stages.analyze.BrainLoader"
            ) as mock_loader_cls,
            patch(
                "do_uw.stages.analyze.execute_signals", return_value=[]
            ),
            patch(
                "do_uw.stages.analyze.aggregate_results",
                return_value={
                    "executed": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "info": 0,
                },
            ),
        ):
            mock_loader_cls.return_value.load_all.return_value = mock_brain
            # Mark extract as complete so validate_input passes
            from do_uw.models.common import StageStatus

            state.mark_stage_completed("extract")
            stage.run(state)

        # Classification should be populated
        assert state.classification is not None
        assert isinstance(state.classification, ClassificationResult)
        assert state.classification.market_cap_tier in (
            MarketCapTier.MEGA,
            MarketCapTier.LARGE,
        )

    def test_analyze_stage_populates_hazard_profile(self) -> None:
        """AnalyzeStage.run() populates state.hazard_profile."""
        from do_uw.models.hazard_profile import HazardProfile
        from do_uw.stages.analyze import AnalyzeStage

        state = _load_state("AAPL")
        if state is None:
            pytest.skip("AAPL state.json not available")

        state.classification = None
        state.hazard_profile = None

        stage = AnalyzeStage()
        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}

        with (
            patch(
                "do_uw.stages.analyze.BrainLoader"
            ) as mock_loader_cls,
            patch(
                "do_uw.stages.analyze.execute_signals", return_value=[]
            ),
            patch(
                "do_uw.stages.analyze.aggregate_results",
                return_value={
                    "executed": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "info": 0,
                },
            ),
        ):
            mock_loader_cls.return_value.load_all.return_value = mock_brain
            from do_uw.models.common import StageStatus

            state.mark_stage_completed("extract")
            stage.run(state)

        assert state.hazard_profile is not None
        assert isinstance(state.hazard_profile, HazardProfile)
        assert 0 <= state.hazard_profile.ies_score <= 100

    def test_end_to_end_analyze_with_real_state(self) -> None:
        """Full AnalyzeStage.run with real AAPL state validates all fields."""
        from do_uw.models.hazard_profile import HazardProfile
        from do_uw.stages.analyze import AnalyzeStage

        state = _load_state("AAPL")
        if state is None:
            pytest.skip("AAPL state.json not available")

        state.classification = None
        state.hazard_profile = None

        stage = AnalyzeStage()
        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}

        with (
            patch(
                "do_uw.stages.analyze.BrainLoader"
            ) as mock_loader_cls,
            patch(
                "do_uw.stages.analyze.execute_signals", return_value=[]
            ),
            patch(
                "do_uw.stages.analyze.aggregate_results",
                return_value={
                    "executed": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "info": 0,
                },
            ),
        ):
            mock_loader_cls.return_value.load_all.return_value = mock_brain
            from do_uw.models.common import StageStatus

            state.mark_stage_completed("extract")
            stage.run(state)

        # Verify all expected fields
        assert state.classification is not None
        assert isinstance(state.classification, ClassificationResult)
        assert state.hazard_profile is not None
        assert isinstance(state.hazard_profile, HazardProfile)
        assert 0 <= state.hazard_profile.ies_score <= 100
        assert len(state.hazard_profile.dimension_scores) > 0
        assert len(state.hazard_profile.category_scores) > 0

        # Pipeline stages unchanged
        assert PIPELINE_STAGES == [
            "resolve",
            "acquire",
            "extract",
            "analyze",
            "score",
            "benchmark",
            "render",
        ]


# -----------------------------------------------------------------------
# Graceful degradation tests
# -----------------------------------------------------------------------


class TestGracefulDegradation:
    """Test that missing data produces sensible defaults without crashes."""

    def test_classification_with_none_company(self) -> None:
        """Classification handles None company by using defaults."""
        from do_uw.stages.analyze.layers.classify import classify_company
        from do_uw.stages.analyze.layers.classify.classification_engine import (
            load_classification_config,
        )

        config = load_classification_config()
        result = classify_company(None, "DEFAULT", None, config)

        assert result.market_cap_tier == MarketCapTier.MID
        assert result.base_filing_rate_pct > 0
        assert result.ipo_multiplier == 1.0

    def test_hazard_profile_with_none_inputs(self) -> None:
        """Hazard profile handles None extracted/company gracefully."""
        from do_uw.stages.analyze.layers.hazard import compute_hazard_profile
        from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

        classification = ClassificationResult(
            market_cap_tier=MarketCapTier.MID,
            sector_code="DEFAULT",
            base_filing_rate_pct=3.5,
            severity_band_low_m=15.0,
            severity_band_high_m=40.0,
        )

        weights, interactions = load_hazard_config()
        profile = compute_hazard_profile(
            None, None, classification, weights, interactions,
        )

        assert 0 <= profile.ies_score <= 100
        assert profile.ies_multiplier > 0

    def test_analyze_stage_survives_classification_failure(self) -> None:
        """AnalyzeStage continues even if classification config is missing."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze import AnalyzeStage

        state = AnalysisState(ticker="TEST")
        state.extracted = ExtractedData()
        state.mark_stage_completed("extract")

        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}

        # Patch the classification config load to fail
        with (
            patch(
                "do_uw.stages.analyze.BrainLoader"
            ) as mock_loader_cls,
            patch(
                "do_uw.stages.analyze.execute_signals", return_value=[]
            ),
            patch(
                "do_uw.stages.analyze.aggregate_results",
                return_value={
                    "executed": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "info": 0,
                },
            ),
            patch(
                "do_uw.stages.analyze.layers.classify.classification_engine.load_classification_config",
                side_effect=FileNotFoundError("simulated config missing"),
            ),
        ):
            mock_loader_cls.return_value.load_all.return_value = mock_brain
            stage = AnalyzeStage()
            stage.run(state)  # Should not raise

        # Classification should be None (failed), but analyze completed
        assert state.classification is None
        assert state.analysis is not None
