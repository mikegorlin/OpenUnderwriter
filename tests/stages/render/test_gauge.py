"""Tests for SVG semi-circular risk score gauge (INFO-01).

Covers render_score_gauge: pure SVG generation for scorecard display.
"""

from __future__ import annotations

import pytest

from do_uw.stages.render.charts.gauge import render_score_gauge


class TestGaugeBasicOutput:
    """render_score_gauge produces valid SVG."""

    def test_returns_svg_string(self) -> None:
        result = render_score_gauge(75.0, "WRITE")
        assert result.strip().startswith("<svg")
        assert result.strip().endswith("</svg>")

    def test_contains_viewbox(self) -> None:
        result = render_score_gauge(50.0)
        assert "viewBox" in result

    def test_contains_score_text(self) -> None:
        result = render_score_gauge(82.5, "WIN")
        assert "82.5" in result

    def test_integer_score_no_decimal(self) -> None:
        result = render_score_gauge(80.0, "WIN")
        assert "80" in result
        # Should not show "80.0"
        assert ">80<" in result

    def test_contains_tier_label(self) -> None:
        result = render_score_gauge(30.0, "WALK")
        assert "WALK" in result

    def test_no_tier_label_when_empty(self) -> None:
        result = render_score_gauge(50.0, "")
        # Should not have a dangling empty text element
        assert 'font-size="9"' not in result


class TestGaugeScoreClamping:
    """Scores are clamped to 0-100 range."""

    def test_negative_score_clamped_to_zero(self) -> None:
        result = render_score_gauge(-10.0, "WALK")
        assert ">0<" in result

    def test_over_100_clamped(self) -> None:
        result = render_score_gauge(150.0, "WIN")
        assert ">100<" in result


class TestGaugeTierColors:
    """Different tiers produce different needle colors."""

    def test_win_tier_uses_green(self) -> None:
        result = render_score_gauge(95.0, "WIN")
        assert "#047857" in result

    def test_walk_tier_uses_red(self) -> None:
        result = render_score_gauge(25.0, "WALK")
        assert "#B91C1C" in result

    def test_unknown_tier_uses_gray(self) -> None:
        result = render_score_gauge(50.0, "UNKNOWN")
        assert "#6B7280" in result


class TestGaugeSvgStructure:
    """SVG contains expected structural elements."""

    def test_contains_gradient(self) -> None:
        result = render_score_gauge(50.0)
        assert "linearGradient" in result

    def test_contains_needle_line(self) -> None:
        result = render_score_gauge(50.0)
        assert "stroke-linecap" in result

    def test_contains_arc_path(self) -> None:
        result = render_score_gauge(50.0)
        # Arc path uses 'A' command
        assert " A " in result

    def test_contains_tick_marks(self) -> None:
        result = render_score_gauge(50.0)
        # Should have tick mark lines (5 ticks)
        assert result.count("stroke=\"#9CA3AF\"") == 5


class TestGaugeCustomDimensions:
    """Custom width/height are respected."""

    def test_custom_size(self) -> None:
        result = render_score_gauge(50.0, width=300, height=180)
        assert "viewBox=\"0 0 300 180\"" in result
        assert "width:300px" in result
