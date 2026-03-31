"""Integration tests: brain YAML/JSON -> BrainLoader -> stages.

Validates the full data path from brain/ YAML signals and JSON configs
through BrainLoader to stage execution.
Tagged with @pytest.mark.integration for selective execution.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.brain.brain_unified_loader import BrainConfig, BrainLoader
from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisState, ExtractedData


@pytest.fixture()
def loader() -> BrainLoader:
    """Create BrainLoader instance."""
    return BrainLoader()


@pytest.mark.integration()
class TestBrainLoaderIntegration:
    """Test full data path from brain YAML/JSON through stages."""

    def test_brain_loader_returns_valid_config(
        self, loader: BrainLoader,
    ) -> None:
        """BrainLoader returns valid BrainConfig."""
        brain = loader.load_all()

        assert isinstance(brain, BrainConfig)
        assert isinstance(brain.checks, dict)
        assert isinstance(brain.scoring, dict)
        assert isinstance(brain.patterns, dict)
        assert isinstance(brain.sectors, dict)
        assert isinstance(brain.red_flags, dict)

    def test_signals_loaded(
        self, loader: BrainLoader,
    ) -> None:
        """Signals from YAML match expected structure."""
        brain = loader.load_all()
        checks = brain.checks.get("signals", [])
        assert isinstance(checks, list)
        assert len(checks) >= 370

        # Verify check structure
        first_check: dict[str, Any] = checks[0]
        assert "id" in first_check
        assert "name" in first_check

    def test_scoring_loaded(
        self, loader: BrainLoader,
    ) -> None:
        """Scoring config has factors and tiers."""
        brain = loader.load_all()
        assert "factors" in brain.scoring
        assert "tiers" in brain.scoring

    def test_patterns_loaded(
        self, loader: BrainLoader,
    ) -> None:
        """Patterns match expected count."""
        brain = loader.load_all()
        patterns = brain.patterns.get("patterns", [])
        assert isinstance(patterns, list)
        assert len(patterns) >= 19

    def test_red_flags_loaded(
        self, loader: BrainLoader,
    ) -> None:
        """Red flags have escalation_triggers."""
        brain = loader.load_all()
        triggers = brain.red_flags.get("escalation_triggers", [])
        assert isinstance(triggers, list)
        assert len(triggers) >= 11

    def test_analyze_stage_runs_with_brain_loader(self) -> None:
        """AnalyzeStage runs successfully using BrainLoader.

        Patches BrainLoader into AnalyzeStage and runs with mocked state
        to verify the full path from YAML signals through check execution.
        """
        from do_uw.stages.analyze import AnalyzeStage

        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("extract")
        state.mark_stage_completed("extract")
        state.extracted = ExtractedData()

        stage = AnalyzeStage()
        stage.run(state)

        # Verify checks were loaded and executed
        assert state.analysis is not None
        assert state.analysis.checks_executed > 0
        assert state.stages["analyze"].status == StageStatus.COMPLETED
