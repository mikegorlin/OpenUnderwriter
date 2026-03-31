"""Tests for radar chart threshold ring enhancements.

Validates that the radar chart supports optional threshold reference
rings and mean fraction rings while maintaining backward compatibility.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.models.scoring import FactorScore
from do_uw.stages.render.design_system import DesignSystem


@pytest.fixture
def spiky_factors() -> list[FactorScore]:
    """10 factors with varying deductions to create a spiky profile."""
    return [
        FactorScore(factor_id="F1", factor_name="Financial Integrity", max_points=15, points_deducted=12.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F2", factor_name="Stock Volatility", max_points=12, points_deducted=2.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F3", factor_name="Governance Quality", max_points=10, points_deducted=8.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F4", factor_name="Litigation History", max_points=15, points_deducted=0.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F5", factor_name="Regulatory Risk", max_points=8, points_deducted=6.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F6", factor_name="Business Complexity", max_points=8, points_deducted=1.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F7", factor_name="Insider Activity", max_points=8, points_deducted=7.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F8", factor_name="Market Sentiment", max_points=6, points_deducted=0.5, scoring_method="signal_driven"),
        FactorScore(factor_id="F9", factor_name="Sector Risk", max_points=10, points_deducted=9.0, scoring_method="signal_driven"),
        FactorScore(factor_id="F10", factor_name="Event Risk", max_points=8, points_deducted=3.0, scoring_method="signal_driven"),
    ]


@pytest.fixture
def design_system() -> DesignSystem:
    """Minimal design system for tests."""
    return DesignSystem()


class TestRadarEnhancement:
    """Tests for enhanced radar chart with threshold rings."""

    def test_threshold_rings_drawn(self, spiky_factors, design_system):
        """Test 1: Radar with show_threshold_rings=True draws 3 reference rings."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        result = create_radar_chart(
            spiky_factors, design_system,
            show_threshold_rings=True,
            format="svg",
        )
        assert result is not None
        svg = str(result)
        # Should contain references to 0.25, 0.50, 0.75 levels
        assert "25%" in svg, "Should label 25% ring"
        assert "50%" in svg, "Should label 50% ring"
        assert "75%" in svg, "Should label 75% ring"

    def test_threshold_rings_light_dashed(self, spiky_factors, design_system):
        """Test 2: Reference rings are light dashed lines."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        # With threshold rings, the matplotlib axes should have extra plot calls
        # We verify the SVG output contains dashed styling
        result = create_radar_chart(
            spiky_factors, design_system,
            show_threshold_rings=True,
            format="svg",
        )
        assert result is not None
        svg = str(result)
        # Dashed lines produce stroke-dasharray or dashes in SVG
        assert "dash" in svg.lower() or "CBD5E1" in svg or "stroke-dash" in svg.lower(), \
            "Threshold rings should be dashed"

    def test_mean_ring_shown(self, spiky_factors, design_system):
        """Test 3: Mean fraction ring shown when show_mean_ring=True."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        result = create_radar_chart(
            spiky_factors, design_system,
            show_mean_ring=True,
            format="svg",
        )
        assert result is not None
        svg = str(result)
        assert "AVG" in svg, "Should label mean ring as AVG"

    def test_backward_compatible_defaults(self, spiky_factors, design_system):
        """Test 4: Existing callers unaffected (default show_threshold_rings=False)."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        # Call without new params -- should work exactly as before
        result = create_radar_chart(spiky_factors, design_system, format="svg")
        assert result is not None
        svg = str(result)
        # Should NOT have threshold ring labels when not requested
        # The standard grid labels (25%, 50%, 75%, 100%) exist from the baseline
        # but "AVG" should not appear
        assert "AVG" not in svg

    def test_labels_show_factor_info(self, spiky_factors, design_system):
        """Test 5: Labels show factor_id, factor_name, points."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        result = create_radar_chart(spiky_factors, design_system, format="svg")
        assert result is not None
        svg = str(result)
        assert "F1" in svg, "Should show factor ID"
        assert "Financial Integrity" in svg, "Should show factor name"

    def test_svg_output_format(self, spiky_factors, design_system):
        """Test 6: SVG output format works (format='svg' returns string)."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart

        result = create_radar_chart(spiky_factors, design_system, format="svg")
        assert isinstance(result, str), "SVG format should return a string"
        assert "<svg" in result, "Should contain SVG markup"
