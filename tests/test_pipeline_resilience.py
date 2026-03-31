"""Tests for pipeline catch-and-continue resilience (Phase 144-01).

Verifies that Pipeline.run() continues through stage failures instead of
raising PipelineError. All stages get status entries regardless of outcome.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.common import StageResult, StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState
from do_uw.pipeline import NullCallbacks, Pipeline
from do_uw.stages.render import RenderStage


class FakeStage:
    """Configurable fake stage for testing pipeline flow."""

    def __init__(self, name: str, *, should_raise: bool = False, error_cls: type = Exception) -> None:
        self._name = name
        self._should_raise = should_raise
        self._error_cls = error_cls

    @property
    def name(self) -> str:
        return self._name

    def validate_input(self, state: AnalysisState) -> None:
        """No-op validation by default."""

    def run(self, state: AnalysisState) -> None:
        state.mark_stage_running(self.name)
        if self._should_raise:
            msg = f"Simulated {self.name} failure"
            raise self._error_cls(msg)
        state.mark_stage_completed(self.name)


class FailValidationStage(FakeStage):
    """Stage whose validate_input raises ValueError."""

    def validate_input(self, state: AnalysisState) -> None:
        msg = f"Validation failed for {self.name}"
        raise ValueError(msg)


def _make_pipeline(stages: list[Any]) -> Pipeline:
    """Build a Pipeline with custom stages (bypass _build_default_stages)."""
    p = Pipeline.__new__(Pipeline)
    p._stages = stages
    p._output_dir = None
    p._callbacks = NullCallbacks()
    return p


def _fresh_state() -> AnalysisState:
    """Create a minimal AnalysisState with all 7 stage slots."""
    return AnalysisState(ticker="TEST")


class TestCatchAndContinue:
    """Pipeline.run() catches stage failures and continues."""

    def test_continue_on_failure(self) -> None:
        """Pipeline with a stage that raises Exception continues to subsequent stages."""
        stages = [
            FakeStage("resolve"),
            FakeStage("acquire", should_raise=True),
            FakeStage("extract"),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        pipeline = _make_pipeline(stages)
        state = _fresh_state()

        # Should NOT raise
        result = pipeline.run(state)

        # acquire should be FAILED, others COMPLETED
        assert result.stages["acquire"].status == StageStatus.FAILED
        assert result.stages["resolve"].status == StageStatus.COMPLETED
        assert result.stages["extract"].status == StageStatus.COMPLETED

    def test_extract_failure_still_runs_later_stages(self) -> None:
        """Pipeline with EXTRACT failing still runs ANALYZE, SCORE, BENCHMARK, RENDER."""
        stages = [
            FakeStage("resolve"),
            FakeStage("acquire"),
            FakeStage("extract", should_raise=True),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        pipeline = _make_pipeline(stages)
        state = _fresh_state()

        result = pipeline.run(state)

        assert result.stages["extract"].status == StageStatus.FAILED
        # Later stages should have been attempted (COMPLETED since they succeed)
        assert result.stages["analyze"].status == StageStatus.COMPLETED
        assert result.stages["score"].status == StageStatus.COMPLETED
        assert result.stages["benchmark"].status == StageStatus.COMPLETED
        assert result.stages["render"].status == StageStatus.COMPLETED

    def test_validation_failure_continues(self) -> None:
        """Pipeline with validation failure (ValueError) on a stage continues to next."""
        stages = [
            FakeStage("resolve"),
            FailValidationStage("acquire"),
            FakeStage("extract"),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        pipeline = _make_pipeline(stages)
        state = _fresh_state()

        result = pipeline.run(state)

        assert result.stages["acquire"].status == StageStatus.FAILED
        assert result.stages["extract"].status == StageStatus.COMPLETED

    def test_state_records_all_stages(self) -> None:
        """state.stages contains entries for ALL 7 stages after run, each with status and duration."""
        stages = [
            FakeStage("resolve"),
            FakeStage("acquire"),
            FakeStage("extract"),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        pipeline = _make_pipeline(stages)
        state = _fresh_state()

        result = pipeline.run(state)

        for stage_name in PIPELINE_STAGES:
            assert stage_name in result.stages
            sr = result.stages[stage_name]
            assert sr.status in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.PENDING)

    def test_failed_stages_retried_on_rerun(self) -> None:
        """FAILED stages are retried (not skipped) on re-run -- only COMPLETED stages are skipped."""
        # First run: acquire fails
        stages_run1 = [
            FakeStage("resolve"),
            FakeStage("acquire", should_raise=True),
            FakeStage("extract"),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        pipeline1 = _make_pipeline(stages_run1)
        state = _fresh_state()
        state = pipeline1.run(state)
        assert state.stages["acquire"].status == StageStatus.FAILED
        assert state.stages["resolve"].status == StageStatus.COMPLETED

        # Second run: acquire succeeds. resolve should be SKIPPED (already COMPLETED).
        stages_run2 = [
            FakeStage("resolve"),  # Should be skipped
            FakeStage("acquire"),  # Should be retried and succeed
            FakeStage("extract"),
            FakeStage("analyze"),
            FakeStage("score"),
            FakeStage("benchmark"),
            FakeStage("render"),
        ]
        mock_cb = MagicMock(spec=NullCallbacks)
        pipeline2 = _make_pipeline(stages_run2)
        pipeline2._callbacks = mock_cb
        state = pipeline2.run(state)

        # resolve was COMPLETED from run1 -> should have been skipped
        mock_cb.on_stage_skip.assert_any_call("resolve", 0, 7)
        # acquire should now be COMPLETED
        assert state.stages["acquire"].status == StageStatus.COMPLETED


class TestRenderValidation:
    """RenderStage.validate_input accepts degraded state."""

    def test_validate_input_accepts_failed_benchmark(self) -> None:
        """RenderStage.validate_input accepts state where benchmark is FAILED."""
        state = _fresh_state()
        state.stages["benchmark"].status = StageStatus.FAILED

        render = RenderStage()
        # Should NOT raise ValueError
        render.validate_input(state)
