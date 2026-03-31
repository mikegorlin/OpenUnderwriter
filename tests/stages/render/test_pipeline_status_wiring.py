"""Tests for pipeline status wiring into HTML context (Phase 144-03).

Verifies that build_html_context populates the 'pipeline_status' key
and that the audit trail template includes the pipeline status table.
"""

from __future__ import annotations

from unittest.mock import patch

from do_uw.models.common import StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState


def _make_state_with_failures() -> AnalysisState:
    """Create state with mixed stage statuses for testing."""
    state = AnalysisState(ticker="TEST")
    state.stages["resolve"].status = StageStatus.COMPLETED
    state.stages["resolve"].duration_seconds = 1.5
    state.stages["acquire"].status = StageStatus.COMPLETED
    state.stages["acquire"].duration_seconds = 12.3
    state.stages["extract"].status = StageStatus.FAILED
    state.stages["extract"].error = "LLM timeout"
    state.stages["extract"].duration_seconds = 30.0
    state.stages["analyze"].status = StageStatus.COMPLETED
    state.stages["analyze"].duration_seconds = 2.1
    state.stages["score"].status = StageStatus.COMPLETED
    state.stages["score"].duration_seconds = 0.5
    state.stages["benchmark"].status = StageStatus.SKIPPED
    # render stays PENDING
    return state


class TestPipelineStatusWiring:
    """Pipeline status context is wired into build_html_context."""

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_pipeline_status_key_in_context(self, mock_beta: object) -> None:
        """build_html_context returns context with 'pipeline_status' key."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        state = _make_state_with_failures()
        context = build_html_context(state)

        assert "pipeline_status" in context
        assert isinstance(context["pipeline_status"], list)

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_pipeline_status_has_seven_stages(self, mock_beta: object) -> None:
        """Pipeline status list has 7 entries (one per PIPELINE_STAGES)."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        state = _make_state_with_failures()
        context = build_html_context(state)

        ps = context["pipeline_status"]
        assert len(ps) == len(PIPELINE_STAGES)

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_failed_stage_has_status_fail_class(self, mock_beta: object) -> None:
        """A FAILED stage has status_class 'status-fail'."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        state = _make_state_with_failures()
        context = build_html_context(state)

        by_stage = {r["stage"]: r for r in context["pipeline_status"]}
        assert by_stage["extract"]["status_class"] == "status-fail"
        assert by_stage["extract"]["error"] == "LLM timeout"

    @patch("do_uw.stages.render.context_builders.assembly_uw_analysis.build_uw_analysis_context")
    def test_each_stage_dict_has_required_keys(self, mock_beta: object) -> None:
        """Each stage dict has keys: stage, status, duration, error, status_class."""
        from do_uw.stages.render.context_builders.assembly_registry import (
            build_html_context,
        )

        state = _make_state_with_failures()
        context = build_html_context(state)

        for row in context["pipeline_status"]:
            assert "stage" in row
            assert "status" in row
            assert "duration" in row
            assert "error" in row
            assert "status_class" in row
