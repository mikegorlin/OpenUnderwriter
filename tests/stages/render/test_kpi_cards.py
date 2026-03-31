"""Tests for KPI summary card builder (INFO-06).

Covers build_kpi_card and build_kpi_strip context generation,
plus CSS class presence and template integration.
"""

from __future__ import annotations

from pathlib import Path

from do_uw.stages.render.charts.kpi_cards import build_kpi_card, build_kpi_strip


class TestKpiCardBuilder:
    """build_kpi_card produces correct context dicts."""

    def test_basic_card(self) -> None:
        card = build_kpi_card("Revenue", "$42.3B")
        assert card["label"] == "Revenue"
        assert card["value"] == "$42.3B"

    def test_card_with_sub_label(self) -> None:
        card = build_kpi_card("Revenue", "$42.3B", sub_label="FY 2025")
        assert card["sub_label"] == "FY 2025"

    def test_card_with_trend(self) -> None:
        card = build_kpi_card("Revenue", "$42.3B", current=42.3, previous=38.1)
        assert card["direction"] == "up"
        assert card["trend_svg"] != ""
        assert "<svg" in card["trend_svg"]

    def test_card_with_decrease_trend(self) -> None:
        card = build_kpi_card("Net Income", "$5B", current=5.0, previous=8.0)
        assert card["direction"] == "down"

    def test_card_flat_trend(self) -> None:
        card = build_kpi_card("Revenue", "$42.3B", current=100.0, previous=100.5)
        assert card["direction"] == "flat"

    def test_card_no_trend_without_values(self) -> None:
        card = build_kpi_card("Revenue", "$42.3B")
        assert card["trend_svg"] == ""
        assert card["direction"] == "flat"

    def test_card_with_severity(self) -> None:
        card = build_kpi_card("Debt Ratio", "3.2x", severity="critical")
        assert card["severity"] == "critical"

    def test_card_inverted_trend(self) -> None:
        card = build_kpi_card("Expenses", "$10B", current=10.0, previous=8.0, inverted=True)
        assert card["direction"] == "up"
        # Inverted: up is bad, so arrow should be red (#DC2626)
        assert "#DC2626" in card["trend_svg"]


class TestKpiStrip:
    """build_kpi_strip produces correct strip context."""

    def test_strip_with_cards(self) -> None:
        cards = [
            build_kpi_card("Revenue", "$42.3B"),
            build_kpi_card("Net Income", "$5B"),
            build_kpi_card("Market Cap", "$3.6T"),
        ]
        strip = build_kpi_strip(cards)
        assert strip["count"] == 3
        assert len(strip["cards"]) == 3

    def test_empty_strip(self) -> None:
        strip = build_kpi_strip([])
        assert strip["count"] == 0
        assert strip["cards"] == []


class TestKpiCssExists:
    """KPI CSS classes are defined in infographic.css."""

    def test_css_file_exists(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "infographic.css"
        )
        assert css_path.exists()

    def test_kpi_strip_class(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "infographic.css"
        )
        css = css_path.read_text()
        assert ".kpi-strip" in css
        assert ".kpi-card" in css
        assert ".kpi-card-value" in css
        assert ".kpi-card-label" in css

    def test_kpi_severity_variants(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "infographic.css"
        )
        css = css_path.read_text()
        assert ".kpi-card--critical" in css
        assert ".kpi-card--elevated" in css
        assert ".kpi-card--positive" in css

    def test_grid_column_variants(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "infographic.css"
        )
        css = css_path.read_text()
        for n in [2, 3, 4, 5]:
            assert f".kpi-strip--{n}" in css


class TestKpiTemplateIntegration:
    """KPI card component template exists and is used in sections."""

    def test_component_template_exists(self) -> None:
        tmpl = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components"
            / "kpi_cards.html.j2"
        )
        assert tmpl.exists()
        content = tmpl.read_text()
        assert "kpi_strip" in content
        assert "kpi-card" in content

    def test_financial_uses_kpi_cards(self) -> None:
        tmpl = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "sections"
            / "financial.html.j2"
        )
        content = tmpl.read_text()
        assert "kpi_cards.html.j2" in content
        assert "kpi_strip" in content

    def test_company_uses_kpi_cards(self) -> None:
        tmpl = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "sections"
            / "company.html.j2"
        )
        content = tmpl.read_text()
        assert "kpi_cards.html.j2" in content
        assert "kpi_strip" in content
