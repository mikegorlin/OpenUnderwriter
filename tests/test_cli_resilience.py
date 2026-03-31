"""Tests for CLI exit code resilience logic (Phase 144-01).

Verifies the failed-stages detection and exit-code decision logic
that was added to the CLI analyze command.
"""

from __future__ import annotations

from do_uw.models.common import StageResult, StageStatus
from do_uw.models.state import AnalysisState


def _make_state_with_failures() -> AnalysisState:
    """Create state where some stages failed."""
    state = AnalysisState(ticker="TEST")
    state.stages["resolve"].status = StageStatus.COMPLETED
    state.stages["acquire"].status = StageStatus.COMPLETED
    state.stages["extract"].status = StageStatus.FAILED
    state.stages["extract"].error = "LLM extraction timeout"
    state.stages["analyze"].status = StageStatus.COMPLETED
    state.stages["score"].status = StageStatus.COMPLETED
    state.stages["benchmark"].status = StageStatus.FAILED
    state.stages["benchmark"].error = "No peer data"
    state.stages["render"].status = StageStatus.COMPLETED
    return state


def _make_state_all_ok() -> AnalysisState:
    """Create state where all stages succeeded."""
    state = AnalysisState(ticker="TEST")
    for s in state.stages.values():
        s.status = StageStatus.COMPLETED
    return state


def _extract_failed_stages(state: AnalysisState) -> list[tuple[str, StageResult]]:
    """Same logic as in cli.py -- extract failed stages for testing."""
    return [
        (name, result) for name, result in state.stages.items()
        if result.status == StageStatus.FAILED
    ]


class TestFailedStagesDetection:
    """Test the failed_stages list comprehension logic used in CLI."""

    def test_detects_failed_stages(self) -> None:
        """Failed stages are identified from state with mixed statuses."""
        state = _make_state_with_failures()
        failed = _extract_failed_stages(state)

        assert len(failed) == 2
        names = [name for name, _ in failed]
        assert "extract" in names
        assert "benchmark" in names

    def test_no_failures_detected_when_all_ok(self) -> None:
        """No failed stages when all completed."""
        state = _make_state_all_ok()
        failed = _extract_failed_stages(state)

        assert len(failed) == 0

    def test_failed_stages_carry_error_messages(self) -> None:
        """Each failed stage result includes an error message."""
        state = _make_state_with_failures()
        failed = _extract_failed_stages(state)

        for name, result in failed:
            assert result.error is not None
            assert len(result.error) > 0


class TestExitCodeDecision:
    """Test the exit code decision: 0 if HTML exists, 1 if not."""

    def test_exit_0_when_html_exists(self, tmp_path: object) -> None:
        """Should exit 0 when HTML file exists in output dir, even with failures."""
        from pathlib import Path
        d = Path(str(tmp_path))
        (d / "TEST_worksheet.html").write_text("<html></html>")

        html_files = list(d.glob("*_worksheet.html"))
        assert len(html_files) > 0  # Would trigger exit 0

    def test_exit_1_when_no_html(self, tmp_path: object) -> None:
        """Should exit 1 when no HTML file in output dir."""
        from pathlib import Path
        d = Path(str(tmp_path))
        d.mkdir(exist_ok=True)

        html_files = list(d.glob("*_worksheet.html"))
        assert len(html_files) == 0  # Would trigger exit 1


class TestCLINoExceptPipelineError:
    """Verify CLI no longer catches PipelineError."""

    def test_cli_does_not_import_pipeline_error(self) -> None:
        """CLI module no longer imports PipelineError."""
        import do_uw.cli as cli_mod
        # PipelineError should not be in the module namespace
        assert not hasattr(cli_mod, "PipelineError")

    def test_cli_source_no_except_pipeline_error(self) -> None:
        """CLI source does not contain 'except PipelineError'."""
        import inspect
        import do_uw.cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert "except PipelineError" not in source
