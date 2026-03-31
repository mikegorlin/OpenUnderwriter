"""Tests for pipeline status context builder (Phase 144-01).

Verifies that build_pipeline_status_context produces structured data
for the audit section pipeline execution status table.
"""

from __future__ import annotations

from do_uw.models.common import StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState
from do_uw.stages.render.context_builders.pipeline_status import (
    build_pipeline_status_context,
)


def _make_state() -> AnalysisState:
    """Create state with mixed stage statuses."""
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


class TestPipelineStatusContext:
    """build_pipeline_status_context returns structured stage data."""

    def test_returns_list_of_dicts_with_expected_keys(self) -> None:
        """Returns list of dicts with stage/status/duration/error/status_class keys."""
        state = _make_state()
        result = build_pipeline_status_context(state)

        assert isinstance(result, list)
        assert len(result) == 7
        for item in result:
            assert "stage" in item
            assert "status" in item
            assert "duration" in item
            assert "error" in item
            assert "status_class" in item

    def test_status_class_mapping(self) -> None:
        """FAILED stages get status-fail, COMPLETED get status-ok."""
        state = _make_state()
        result = build_pipeline_status_context(state)

        by_stage = {r["stage"]: r for r in result}
        assert by_stage["resolve"]["status_class"] == "status-ok"
        assert by_stage["extract"]["status_class"] == "status-fail"
        assert by_stage["benchmark"]["status_class"] == "status-skip"
        assert by_stage["render"]["status_class"] == "status-pending"

    def test_includes_all_seven_stages(self) -> None:
        """Context includes all 7 stages even when some are PENDING."""
        state = _make_state()
        result = build_pipeline_status_context(state)

        stage_names = [r["stage"] for r in result]
        assert stage_names == PIPELINE_STAGES
