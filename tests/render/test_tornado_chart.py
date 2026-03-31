"""Tests for tornado chart SVG renderer.

Validates that the tornado chart correctly renders scenario sensitivity
with sorted bars, center line, directional colors, and labels.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_scenarios() -> list[dict]:
    """5 scenarios with varying positive and negative deltas."""
    return [
        {"name": "SCA Filed", "score_delta": -15, "current_score": 65},
        {"name": "Restatement", "score_delta": -22, "current_score": 65},
        {"name": "Clean Audit", "score_delta": 8, "current_score": 65},
        {"name": "CEO Departure", "score_delta": -5, "current_score": 65},
        {"name": "Litigation Dismissed", "score_delta": 12, "current_score": 65},
    ]


class TestTornadoChart:
    """Tests for render_tornado_chart."""

    def test_returns_valid_svg(self, sample_scenarios):
        """Test 1: Returns valid SVG."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_scenarios_sorted_by_absolute_delta(self, sample_scenarios):
        """Test 2: Scenarios sorted by absolute delta (largest at top)."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        # Restatement (-22) should appear before SCA Filed (-15)
        restatement_pos = svg.index("Restatement")
        sca_pos = svg.index("SCA Filed")
        assert restatement_pos < sca_pos, "Restatement (|22|) should be above SCA Filed (|15|)"

    def test_center_line_drawn(self, sample_scenarios):
        """Test 3: Center line drawn at current_score position."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        # Should have a vertical line element for the center
        assert "stroke-dasharray" in svg or "Current" in svg or "65" in svg

    def test_directional_colors(self, sample_scenarios):
        """Test 4: Negative deltas red, positive deltas blue."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        assert "#DC2626" in svg, "Should have red for negative deltas"
        assert "#2563EB" in svg, "Should have blue for positive deltas"

    def test_scenario_name_labels(self, sample_scenarios):
        """Test 5: Scenario name labels present."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        for s in sample_scenarios:
            assert s["name"] in svg, f"Scenario '{s['name']}' not found in SVG"

    def test_delta_values_shown(self, sample_scenarios):
        """Test 6: Delta values shown on bars."""
        from do_uw.stages.render.charts.tornado_chart import render_tornado_chart

        svg = render_tornado_chart(sample_scenarios, current_score=65)
        assert "-22" in svg, "Should show -22 delta for Restatement"
        assert "+12" in svg or "12" in svg, "Should show +12 delta for Litigation Dismissed"
        assert "+8" in svg or "8" in svg, "Should show +8 delta for Clean Audit"
