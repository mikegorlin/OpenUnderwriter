"""Tests for chart placeholder PNG wiring (Phase 144-03).

Verifies that when a chart builder returns None, a placeholder PNG
is written to the chart_dir instead of leaving a missing file.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from do_uw.models.state import AnalysisState


def _make_state() -> AnalysisState:
    """Create minimal state for chart generation."""
    return AnalysisState(ticker="TEST")


class TestChartPlaceholderWiring:
    """Placeholder PNGs are written when chart builders return None."""

    @patch("do_uw.stages.render.charts.stock_charts.create_stock_performance_chart", return_value=None)
    def test_stock_chart_placeholder_written(self, mock_chart: object) -> None:
        """When stock chart returns None, placeholder PNG is written."""
        from do_uw.stages.render import _generate_chart_images
        from do_uw.stages.render.design_system import DesignSystem

        state = _make_state()
        ds = DesignSystem()

        with tempfile.TemporaryDirectory() as tmp:
            chart_dir = Path(tmp)
            _generate_chart_images(state, chart_dir, ds)

            # Both stock chart files should exist as placeholders
            stock_1y = chart_dir / "stock_1y.png"
            assert stock_1y.exists(), "stock_1y.png not written as placeholder"
            data = stock_1y.read_bytes()
            assert len(data) > 0, "Placeholder PNG is empty"
            assert data[:4] == b"\x89PNG", "File is not a valid PNG"

    @patch("do_uw.stages.render.charts.stock_charts.create_stock_performance_chart", return_value=None)
    def test_placeholder_preserves_expected_filename(self, mock_chart: object) -> None:
        """Placeholder files use the same filenames as real charts."""
        from do_uw.stages.render import _generate_chart_images
        from do_uw.stages.render.design_system import DesignSystem

        state = _make_state()
        ds = DesignSystem()

        with tempfile.TemporaryDirectory() as tmp:
            chart_dir = Path(tmp)
            _generate_chart_images(state, chart_dir, ds)

            # Both 1Y and 5Y should exist
            assert (chart_dir / "stock_1y.png").exists()
            assert (chart_dir / "stock_5y.png").exists()

    @patch("do_uw.stages.render.charts.stock_charts.create_stock_performance_chart", return_value=None)
    def test_placeholder_is_valid_png(self, mock_chart: object) -> None:
        """Placeholder PNG has valid PNG magic bytes and non-zero size."""
        from do_uw.stages.render import _generate_chart_images
        from do_uw.stages.render.design_system import DesignSystem

        state = _make_state()
        ds = DesignSystem()

        with tempfile.TemporaryDirectory() as tmp:
            chart_dir = Path(tmp)
            _generate_chart_images(state, chart_dir, ds)

            for fn in ["stock_1y.png", "stock_5y.png"]:
                path = chart_dir / fn
                if path.exists():
                    data = path.read_bytes()
                    assert len(data) > 100, f"{fn} placeholder too small ({len(data)} bytes)"
                    assert data[:4] == b"\x89PNG", f"{fn} not a valid PNG"
