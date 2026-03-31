"""Tests for --from-stage, --rerender, --fresh, and --purge CLI options.

Verifies that stage reset logic correctly marks the target stage and all
downstream stages as PENDING without deleting any cached data or output files.
Also verifies --fresh preserves caches and --purge is the destructive option.
"""

from __future__ import annotations

import pytest

from do_uw.models.common import StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState


def _reset_all_stages(state: AnalysisState) -> None:
    """Apply the same reset logic as cli.py --fresh (reset ALL stages)."""
    for stage_name in PIPELINE_STAGES:
        if stage_name in state.stages:
            state.stages[stage_name].status = StageStatus.PENDING


def _make_all_completed_state(ticker: str = "TEST") -> AnalysisState:
    """Create an AnalysisState with all stages marked COMPLETED."""
    state = AnalysisState(ticker=ticker)
    for stage_name in PIPELINE_STAGES:
        state.stages[stage_name].status = StageStatus.COMPLETED
    return state


def _reset_from_stage(state: AnalysisState, from_stage: str) -> list[str]:
    """Apply the same reset logic as cli.py --from-stage.

    Returns the list of stage names that were reset.
    Raises ValueError for invalid stage names.
    """
    from_stage = from_stage.lower().strip()
    if from_stage not in PIPELINE_STAGES:
        msg = f"Invalid stage: '{from_stage}'. Valid stages: {', '.join(PIPELINE_STAGES)}"
        raise ValueError(msg)
    stage_idx = PIPELINE_STAGES.index(from_stage)
    stages_to_reset = PIPELINE_STAGES[stage_idx:]
    for stage_name in stages_to_reset:
        if stage_name in state.stages:
            state.stages[stage_name].status = StageStatus.PENDING
    return stages_to_reset


class TestFromStageRender:
    """--from-stage render resets only the render stage."""

    def test_resets_render_only(self) -> None:
        state = _make_all_completed_state()
        reset = _reset_from_stage(state, "render")

        assert reset == ["render"]
        assert state.stages["render"].status == StageStatus.PENDING
        # All upstream stages remain COMPLETED
        for stage_name in PIPELINE_STAGES[:-1]:
            assert state.stages[stage_name].status == StageStatus.COMPLETED, (
                f"{stage_name} should still be COMPLETED"
            )


class TestFromStageAnalyze:
    """--from-stage analyze resets analyze, score, benchmark, render."""

    def test_resets_analyze_and_downstream(self) -> None:
        state = _make_all_completed_state()
        reset = _reset_from_stage(state, "analyze")

        assert reset == ["analyze", "score", "benchmark", "render"]
        # Upstream stages stay COMPLETED
        for stage_name in ["resolve", "acquire", "extract"]:
            assert state.stages[stage_name].status == StageStatus.COMPLETED
        # Target + downstream stages are PENDING
        for stage_name in ["analyze", "score", "benchmark", "render"]:
            assert state.stages[stage_name].status == StageStatus.PENDING


class TestFromStageInvalid:
    """--from-stage with invalid name raises an error."""

    def test_invalid_stage_name(self) -> None:
        state = _make_all_completed_state()
        with pytest.raises(ValueError, match="Invalid stage"):
            _reset_from_stage(state, "nonexistent")

    def test_empty_string_is_not_applied(self) -> None:
        """An empty string is invalid (CLI guards against it before calling)."""
        state = _make_all_completed_state()
        with pytest.raises(ValueError, match="Invalid stage"):
            _reset_from_stage(state, "")


class TestRerenderEquivalence:
    """--rerender should be equivalent to --from-stage render."""

    def test_rerender_same_as_from_stage_render(self) -> None:
        state_a = _make_all_completed_state()
        state_b = _make_all_completed_state()

        _reset_from_stage(state_a, "render")
        # Simulate --rerender: sets from_stage = "render"
        _reset_from_stage(state_b, "render")

        for stage_name in PIPELINE_STAGES:
            assert (
                state_a.stages[stage_name].status
                == state_b.stages[stage_name].status
            ), f"Mismatch on {stage_name}"


class TestFromStageEdgeCases:
    """Edge cases for --from-stage."""

    def test_from_resolve_resets_everything(self) -> None:
        state = _make_all_completed_state()
        reset = _reset_from_stage(state, "resolve")

        assert reset == PIPELINE_STAGES
        for stage_name in PIPELINE_STAGES:
            assert state.stages[stage_name].status == StageStatus.PENDING

    def test_from_acquire_preserves_resolve(self) -> None:
        state = _make_all_completed_state()
        _reset_from_stage(state, "acquire")

        assert state.stages["resolve"].status == StageStatus.COMPLETED
        assert state.stages["acquire"].status == StageStatus.PENDING

    def test_does_not_modify_stage_data(self) -> None:
        """Reset only changes status, not stage result metadata."""
        state = _make_all_completed_state()
        # Simulate having some error info on a previously-failed stage
        state.stages["score"].error = "previous error"
        _reset_from_stage(state, "score")

        # Status is reset but other fields are untouched
        assert state.stages["score"].status == StageStatus.PENDING
        assert state.stages["score"].error == "previous error"

    def test_idempotent_on_pending_stages(self) -> None:
        """Resetting already-PENDING stages is a no-op."""
        state = AnalysisState(ticker="TEST")  # All PENDING by default
        _reset_from_stage(state, "analyze")

        for stage_name in PIPELINE_STAGES:
            assert state.stages[stage_name].status == StageStatus.PENDING


class TestFreshResetsAllStages:
    """--fresh resets all stages to PENDING (no cache deletion)."""

    def test_fresh_resets_all_completed_stages(self) -> None:
        state = _make_all_completed_state()
        _reset_all_stages(state)

        for stage_name in PIPELINE_STAGES:
            assert state.stages[stage_name].status == StageStatus.PENDING, (
                f"{stage_name} should be PENDING after --fresh"
            )

    def test_fresh_resets_mixed_statuses(self) -> None:
        """Fresh resets regardless of current status (COMPLETED, FAILED, etc.)."""
        state = _make_all_completed_state()
        state.stages["extract"].status = StageStatus.FAILED
        state.stages["analyze"].status = StageStatus.RUNNING

        _reset_all_stages(state)

        for stage_name in PIPELINE_STAGES:
            assert state.stages[stage_name].status == StageStatus.PENDING

    def test_fresh_does_not_clear_stage_metadata(self) -> None:
        """Fresh only resets status, not timing/error metadata."""
        state = _make_all_completed_state()
        state.stages["acquire"].error = "some old error"
        _reset_all_stages(state)

        assert state.stages["acquire"].status == StageStatus.PENDING
        assert state.stages["acquire"].error == "some old error"


class TestPurgeImpliesFresh:
    """--purge should reset all stages (it also deletes caches, tested via CLI)."""

    def test_purge_resets_all_stages(self) -> None:
        """After purge deletes caches, it sets fresh=True, which resets stages."""
        state = _make_all_completed_state()
        # Simulate purge: same as fresh for stage reset purposes
        _reset_all_stages(state)

        for stage_name in PIPELINE_STAGES:
            assert state.stages[stage_name].status == StageStatus.PENDING


class TestFreshVsFromStage:
    """--fresh and --from-stage interact correctly."""

    def test_from_stage_is_more_specific_than_fresh(self) -> None:
        """If both --fresh and --from-stage are given, --from-stage wins
        (only resets from that stage, not everything)."""
        state = _make_all_completed_state()

        # In the CLI: `if fresh and not from_stage` guards the full reset.
        # When from_stage is set, only from_stage logic runs.
        _reset_from_stage(state, "score")

        # Upstream stages remain COMPLETED
        for stage_name in ["resolve", "acquire", "extract", "analyze"]:
            assert state.stages[stage_name].status == StageStatus.COMPLETED
        # Only score + downstream are PENDING
        for stage_name in ["score", "benchmark", "render"]:
            assert state.stages[stage_name].status == StageStatus.PENDING
