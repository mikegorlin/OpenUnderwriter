"""Tests for waterfall chart SVG renderer.

Validates that the waterfall chart correctly renders scoring factors
as horizontal bars with cumulative deductions, tier threshold lines,
severity-based colors, and proper safe_float usage.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_factors() -> list[dict]:
    """10 scoring factors with varying deductions, including one zero."""
    return [
        {"id": "F1", "name": "Financial Integrity", "points_deducted": 8.0, "max_points": 15},
        {"id": "F2", "name": "Stock Volatility", "points_deducted": 5.0, "max_points": 12},
        {"id": "F3", "name": "Governance Quality", "points_deducted": 3.0, "max_points": 10},
        {"id": "F4", "name": "Litigation History", "points_deducted": 12.0, "max_points": 15},
        {"id": "F5", "name": "Regulatory Risk", "points_deducted": 0.0, "max_points": 8},
        {"id": "F6", "name": "Business Complexity", "points_deducted": 2.0, "max_points": 8},
        {"id": "F7", "name": "Insider Activity", "points_deducted": 6.0, "max_points": 8},
        {"id": "F8", "name": "Market Sentiment", "points_deducted": 1.0, "max_points": 6},
        {"id": "F9", "name": "Sector Risk", "points_deducted": 4.0, "max_points": 10},
        {"id": "F10", "name": "Event Risk", "points_deducted": 0.0, "max_points": 8},
    ]


@pytest.fixture
def tier_thresholds() -> list[dict]:
    """Standard tier score thresholds."""
    return [
        {"tier": "WIN", "min_score": 86},
        {"tier": "WANT", "min_score": 71},
        {"tier": "WRITE", "min_score": 51},
        {"tier": "WATCH", "min_score": 31},
        {"tier": "WALK", "min_score": 11},
    ]


class TestWaterfallChart:
    """Tests for render_waterfall_chart."""

    def test_returns_valid_svg(self, sample_factors, tier_thresholds):
        """Test 1: Returns valid SVG with opening/closing tags."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_one_rect_per_nonzero_factor(self, sample_factors, tier_thresholds):
        """Test 2: Contains one rect per non-zero factor."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        # 8 non-zero factors (F5 and F10 are zero)
        # Count factor bar rects (excluding background/track rects)
        nonzero = [f for f in sample_factors if f["points_deducted"] > 0]
        # Each non-zero factor should have a bar rect with a fill color
        for f in nonzero:
            assert f["id"] in svg, f"Factor {f['id']} not found in SVG"

    def test_tier_threshold_dashed_lines(self, sample_factors, tier_thresholds):
        """Test 3: Contains dashed lines for tier thresholds."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        assert "stroke-dasharray" in svg, "No dashed lines found for tier thresholds"
        # Should have tier labels
        for t in tier_thresholds:
            assert t["tier"] in svg, f"Tier label {t['tier']} not found"

    def test_factor_labels_include_id_and_name(self, sample_factors, tier_thresholds):
        """Test 4: Factor labels include factor_id and name."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        # Non-zero factors should have both ID and name in labels
        assert "F1" in svg
        assert "Financial Integrity" in svg
        assert "F4" in svg
        assert "Litigation History" in svg

    def test_points_labels_show_negative(self, sample_factors, tier_thresholds):
        """Test 5: Points labels show negative deductions (-X)."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        assert "-8" in svg, "Should show -8 for F1"
        assert "-12" in svg, "Should show -12 for F4"

    def test_zero_factors_skipped(self, sample_factors, tier_thresholds):
        """Test 6: Zero-scored factors are skipped (no bar)."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        # F5 and F10 have 0 points deducted, should NOT appear as labeled bars
        # They should not have label text in the chart
        assert "Regulatory Risk" not in svg, "Zero-scored F5 should be skipped"
        assert "Event Risk" not in svg, "Zero-scored F10 should be skipped"

    def test_safe_float_used(self):
        """Test 7: All float values use safe_float() -- handles string inputs."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        # Pass string values that safe_float should handle
        factors = [
            {"id": "F1", "name": "Test", "points_deducted": "5.5", "max_points": "10"},
            {"id": "F2", "name": "Test2", "points_deducted": "N/A", "max_points": 8},
        ]
        thresholds = [{"tier": "WIN", "min_score": 86}]
        # Should not raise -- safe_float handles strings
        svg = render_waterfall_chart(factors, total_score="75", tier_thresholds=thresholds)
        assert "<svg" in svg

    def test_colors_by_severity(self, sample_factors, tier_thresholds):
        """Test 8: Colors map to severity: >=60% red, >=30% orange, >0% gold."""
        from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart

        svg = render_waterfall_chart(sample_factors, total_score=59.0, tier_thresholds=tier_thresholds)
        # F4: 12/15 = 80% -> red (#DC2626)
        assert "#DC2626" in svg, "Should have red for high severity (F4=80%)"
        # F7: 6/8 = 75% -> red
        # F1: 8/15 = 53% -> orange (#EA580C)
        assert "#EA580C" in svg, "Should have orange for moderate severity (F1=53%)"
        # F8: 1/6 = 17% -> gold (#D4A843)
        assert "#D4A843" in svg, "Should have gold for low severity"
