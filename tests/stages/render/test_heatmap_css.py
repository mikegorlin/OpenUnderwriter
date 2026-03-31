"""Tests for CSS heatmap coloring classes (INFO-05).

Verifies heatmap CSS classes exist in styles.css and use --intensity
custom property for dynamic coloring.
"""

from __future__ import annotations

from pathlib import Path

_STYLES_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "do_uw"
    / "templates"
    / "html"
    / "styles.css"
)


class TestHeatmapCssExists:
    """Required heatmap CSS classes are defined."""

    def test_styles_file_exists(self) -> None:
        assert _STYLES_PATH.exists()

    def test_heat_risk_class(self) -> None:
        css = _STYLES_PATH.read_text()
        assert ".heat-risk" in css

    def test_heat_caution_class(self) -> None:
        css = _STYLES_PATH.read_text()
        assert ".heat-caution" in css

    def test_heat_positive_class(self) -> None:
        css = _STYLES_PATH.read_text()
        assert ".heat-positive" in css

    def test_heat_severity_class(self) -> None:
        css = _STYLES_PATH.read_text()
        assert ".heat-severity" in css

    def test_heat_factor_class(self) -> None:
        css = _STYLES_PATH.read_text()
        assert ".heat-factor" in css


class TestHeatmapCustomProperty:
    """Heatmap classes use --intensity custom property."""

    def test_intensity_custom_property_used(self) -> None:
        css = _STYLES_PATH.read_text()
        assert "--intensity" in css

    def test_color_mix_used(self) -> None:
        css = _STYLES_PATH.read_text()
        assert "color-mix" in css


class TestHeatmapDiscreteLevels:
    """Discrete fallback heat levels exist."""

    def test_heat_0_through_5(self) -> None:
        css = _STYLES_PATH.read_text()
        for i in range(6):
            assert f".heat-{i}" in css, f"Missing .heat-{i} class"


class TestHeatmapInTemplates:
    """Heatmap classes are applied in scoring templates."""

    def test_scorecard_uses_heat_factor(self) -> None:
        scorecard = (
            _STYLES_PATH.parent / "sections" / "scorecard.html.j2"
        ).read_text()
        assert "heat-factor" in scorecard
        assert "--intensity" in scorecard

    def test_ten_factor_uses_heat_factor(self) -> None:
        ten_factor = (
            _STYLES_PATH.parent
            / "sections"
            / "scoring"
            / "ten_factor_scoring.html.j2"
        ).read_text()
        assert "heat-factor" in ten_factor
        assert "--intensity" in ten_factor
