"""Performance budget tests for D&O worksheet rendering.

Enforces timing constraints on render operations to catch performance
regressions. Uses cached state data to measure render times without
needing live API access.

Usage:
    PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py -v
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

# Performance budgets (seconds)
HTML_RENDER_BUDGET = 10.0
PDF_RENDER_BUDGET = 30.0
PIPELINE_TOTAL_BUDGET = 1500.0  # 25 minutes


def _find_cached_state() -> Path | None:
    """Find most recent state.json from output directory."""
    output_root = Path(__file__).parent.parent / "output"
    if not output_root.exists():
        return None
    dirs = sorted(output_root.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
    for d in dirs:
        state_path = d / "state.json"
        if state_path.exists():
            return state_path
    return None


def _load_state(state_path: Path):  # noqa: ANN202
    """Load AnalysisState from cached state.json."""
    from do_uw.models.state import AnalysisState

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    return AnalysisState.model_validate(raw)


@pytest.mark.skipif(
    not os.environ.get("PERFORMANCE_TESTS"),
    reason="Set PERFORMANCE_TESTS=1 to run performance budget tests",
)
class TestPerformanceBudget:
    """Performance budget enforcement for render operations."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        """Locate cached state for testing."""
        state_path = _find_cached_state()
        if state_path is None:
            pytest.skip("No cached state.json found in output/")
        self._state_path = state_path
        self._output_dir = state_path.parent

    def test_html_render_under_budget(self) -> None:
        """HTML rendering completes within 10 seconds."""
        from do_uw.stages.render.html_renderer import render_html_pdf

        state = _load_state(self._state_path)
        output_path = self._output_dir / "perf_test_worksheet.html"

        start = time.perf_counter()
        try:
            render_html_pdf(state, output_path)
        finally:
            duration = time.perf_counter() - start
            # Clean up test output
            output_path.unlink(missing_ok=True)
            output_path.with_suffix(".html").unlink(missing_ok=True)

        assert duration < HTML_RENDER_BUDGET, (
            f"HTML render took {duration:.1f}s, budget is {HTML_RENDER_BUDGET:.0f}s"
        )

    def test_pdf_render_under_budget(self) -> None:
        """PDF rendering completes within 30 seconds."""
        from do_uw.stages.render.pdf_renderer import render_pdf

        state = _load_state(self._state_path)
        output_path = self._output_dir / "perf_test_worksheet.pdf"

        start = time.perf_counter()
        try:
            render_pdf(state, output_path.parent)
        finally:
            duration = time.perf_counter() - start
            # Clean up test output
            output_path.unlink(missing_ok=True)

        assert duration < PDF_RENDER_BUDGET, (
            f"PDF render took {duration:.1f}s, budget is {PDF_RENDER_BUDGET:.0f}s"
        )


@pytest.mark.skipif(
    not os.environ.get("PERFORMANCE_TESTS"),
    reason="Set PERFORMANCE_TESTS=1 to run performance budget tests",
)
class TestPerformanceBudgetConstants:
    """Smoke tests for budget configuration."""

    def test_html_budget_reasonable(self) -> None:
        """HTML budget is between 5-30 seconds."""
        assert 5.0 <= HTML_RENDER_BUDGET <= 30.0

    def test_pdf_budget_reasonable(self) -> None:
        """PDF budget is between 15-60 seconds."""
        assert 15.0 <= PDF_RENDER_BUDGET <= 60.0

    def test_pipeline_budget_reasonable(self) -> None:
        """Pipeline budget is between 10-30 minutes."""
        assert 600.0 <= PIPELINE_TOTAL_BUDGET <= 1800.0
