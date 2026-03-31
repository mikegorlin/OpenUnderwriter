"""Tests for stage failure banner propagation to uw_analysis (Phase 144-03).

Verifies that when a pipeline stage fails, the amber banner text is
propagated from top-level context keys into uw_analysis sub-dicts
so that report section templates can render it.
"""

from __future__ import annotations

from unittest.mock import patch

from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisState


def _make_state_extract_failed() -> AnalysisState:
    """Create state with EXTRACT stage FAILED."""
    state = AnalysisState(ticker="TEST")
    state.stages["resolve"].status = StageStatus.COMPLETED
    state.stages["acquire"].status = StageStatus.COMPLETED
    state.stages["extract"].status = StageStatus.FAILED
    state.stages["extract"].error = "LLM timeout"
    state.stages["analyze"].status = StageStatus.COMPLETED
    state.stages["score"].status = StageStatus.COMPLETED
    state.stages["benchmark"].status = StageStatus.COMPLETED
    state.stages["render"].status = StageStatus.COMPLETED
    return state


def _make_state_score_failed() -> AnalysisState:
    """Create state with SCORE stage FAILED."""
    state = AnalysisState(ticker="TEST")
    state.stages["resolve"].status = StageStatus.COMPLETED
    state.stages["acquire"].status = StageStatus.COMPLETED
    state.stages["extract"].status = StageStatus.COMPLETED
    state.stages["analyze"].status = StageStatus.COMPLETED
    state.stages["score"].status = StageStatus.FAILED
    state.stages["score"].error = "Missing factor weights"
    state.stages["benchmark"].status = StageStatus.COMPLETED
    state.stages["render"].status = StageStatus.COMPLETED
    return state


class TestStageBannerPropagation:
    """Stage failure banners propagate into uw_analysis sub-dicts."""

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_extract_failure_banner_in_beta_fin(self, mock_beta: object) -> None:
        """EXTRACT failure injects _stage_banner into uw_analysis.fin."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        # Mock returns a dict with sub-dicts so propagation can inject banners
        mock_beta.return_value = {  # type: ignore[attr-defined]
            "fin": {"revenue": "N/A"},
            "gov": {"board_size": "N/A"},
            "lit_detail": {},
            "market_ext": {},
            "score_detail": {},
        }

        state = _make_state_extract_failed()
        context = build_html_context(state)

        br = context.get("uw_analysis", {})
        fin = br.get("fin", {})
        assert isinstance(fin, dict)
        assert "_stage_banner" in fin
        assert "Incomplete" in fin["_stage_banner"]
        assert "EXTRACT" in fin["_stage_banner"]

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_extract_failure_banner_in_beta_gov(self, mock_beta: object) -> None:
        """EXTRACT failure injects _stage_banner into uw_analysis.gov."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        mock_beta.return_value = {  # type: ignore[attr-defined]
            "fin": {},
            "gov": {"board_size": "N/A"},
            "lit_detail": {},
            "market_ext": {},
            "score_detail": {},
        }

        state = _make_state_extract_failed()
        context = build_html_context(state)

        br = context.get("uw_analysis", {})
        gov = br.get("gov", {})
        assert isinstance(gov, dict)
        assert "_stage_banner" in gov
        assert "Incomplete" in gov["_stage_banner"]

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_score_failure_banner_in_beta_scoring(self, mock_beta: object) -> None:
        """SCORE failure injects _stage_banner into uw_analysis.score_detail."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        mock_beta.return_value = {  # type: ignore[attr-defined]
            "fin": {},
            "gov": {},
            "lit_detail": {},
            "market_ext": {},
            "score_detail": {"quality_score": "N/A"},
        }

        state = _make_state_score_failed()
        context = build_html_context(state)

        br = context.get("uw_analysis", {})
        scoring = br.get("score_detail", {})
        assert isinstance(scoring, dict)
        assert "_stage_banner" in scoring
        assert "Incomplete" in scoring["_stage_banner"]
        assert "SCORE" in scoring["_stage_banner"]
