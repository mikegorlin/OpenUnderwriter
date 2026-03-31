"""Tests for HTML Jinja2 component macros.

Uses Jinja2 Environment to render macros directly -- no browser needed.
Validates badge, table, callout, chart, and narrative components produce
correct HTML structure with expected CSS classes.
"""

from __future__ import annotations

import re

import jinja2
import pytest

from do_uw.stages.render.formatters import humanize_enum
from do_uw.stages.render.formatters_humanize import humanize_source


def _strip_markdown(text: str) -> str:
    """Test-local strip_md filter matching html_renderer._strip_markdown."""
    if not text:
        return ""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def _narratize(text: str) -> list[dict[str, str]]:
    """Test-local narratize filter matching html_renderer._narratize."""
    from do_uw.stages.render.html_renderer import _narratize
    return _narratize(text)


@pytest.fixture()
def env() -> jinja2.Environment:
    """Jinja2 environment loaded from the html templates directory."""
    from do_uw.stages.render.formatters_humanize import clean_narrative_text

    e = jinja2.Environment(
        loader=jinja2.FileSystemLoader("src/do_uw/templates/html"),
        autoescape=True,
    )
    # Register custom filters used by templates
    e.filters["strip_md"] = _strip_markdown
    e.filters["humanize"] = humanize_enum
    e.filters["format_na"] = lambda v: str(v) if v is not None else "N/A"
    e.filters["narratize"] = _narratize
    e.filters["clean_narrative"] = clean_narrative_text
    e.filters["humanize_source"] = humanize_source
    return e


# ── Badge Tests ──────────────────────────────────────────────────────


class TestTrafficLight:
    """Tests for traffic_light badge macro."""

    def test_traffic_light_triggered(self, env: jinja2.Environment) -> None:
        """TRIGGERED status renders red badge span."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('TRIGGERED') }}"
        )
        result = template.render()
        assert "bg-red-700" in result
        assert "TRIGGERED" in result

    def test_traffic_light_clear(self, env: jinja2.Environment) -> None:
        """CLEAR status renders emerald/green badge span."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('CLEAR') }}"
        )
        result = template.render()
        assert "bg-emerald-600" in result
        assert "CLEAR" in result

    def test_traffic_light_info(self, env: jinja2.Environment) -> None:
        """INFO status renders blue badge span."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('INFO') }}"
        )
        result = template.render()
        assert "bg-blue-600" in result
        assert "INFO" in result

    def test_traffic_light_custom_label(self, env: jinja2.Environment) -> None:
        """Custom label overrides default status text."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('TRIGGERED', label='High Risk') }}"
        )
        result = template.render()
        assert "High Risk" in result
        assert "bg-red-700" in result


class TestDensityIndicator:
    """Tests for density_indicator macro."""

    def test_density_indicator_critical(self, env: jinja2.Environment) -> None:
        """CRITICAL density renders red density-indicator div."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import density_indicator %}'
            "{{ density_indicator('CRITICAL') }}"
        )
        result = template.render()
        assert "density-indicator--critical" in result
        assert "Critical Risk" in result

    def test_density_indicator_elevated(self, env: jinja2.Environment) -> None:
        """ELEVATED density renders amber density-indicator div."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import density_indicator %}'
            "{{ density_indicator('ELEVATED') }}"
        )
        result = template.render()
        assert "density-indicator--elevated" in result
        assert "Elevated Concern" in result

    def test_density_indicator_clean(self, env: jinja2.Environment) -> None:
        """CLEAN density renders nothing."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import density_indicator %}'
            "{{ density_indicator('CLEAN') }}"
        )
        result = template.render().strip()
        assert result == ""


class TestConfidenceMarker:
    """Tests for confidence_marker macro."""

    def test_confidence_low(self, env: jinja2.Environment) -> None:
        """LOW confidence renders visible marker."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import confidence_marker %}'
            "{{ confidence_marker('LOW') }}"
        )
        result = template.render()
        assert "low conf." in result
        assert "italic" in result

    def test_confidence_medium(self, env: jinja2.Environment) -> None:
        """MEDIUM confidence renders nothing."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import confidence_marker %}'
            "{{ confidence_marker('MEDIUM') }}"
        )
        result = template.render().strip()
        assert result == ""

    def test_confidence_high(self, env: jinja2.Environment) -> None:
        """HIGH confidence renders nothing."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import confidence_marker %}'
            "{{ confidence_marker('HIGH') }}"
        )
        result = template.render().strip()
        assert result == ""


class TestTierBadge:
    """Tests for tier_badge macro."""

    def test_tier_win(self, env: jinja2.Environment) -> None:
        """WIN tier renders emerald badge."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import tier_badge %}'
            "{{ tier_badge('WIN') }}"
        )
        result = template.render()
        assert "bg-emerald-600" in result
        assert "WIN" in result

    def test_tier_walk(self, env: jinja2.Environment) -> None:
        """WALK tier renders red badge."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import tier_badge %}'
            "{{ tier_badge('WALK') }}"
        )
        result = template.render()
        assert "bg-red-600" in result
        assert "WALK" in result

    def test_tier_no_touch(self, env: jinja2.Environment) -> None:
        """NO_TOUCH tier renders dark red badge."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import tier_badge %}'
            "{{ tier_badge('NO_TOUCH') }}"
        )
        result = template.render()
        assert "bg-red-900" in result
        assert "NO TOUCH" in result


# ── Table Tests ──────────────────────────────────────────────────────


class TestKvTable:
    """Tests for kv_table macro."""

    def test_kv_table_renders_pairs(self, env: jinja2.Environment) -> None:
        """KV table renders key-value pairs as table rows."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import kv_table %}'
            "{{ kv_table([('Market Cap', '$2.8T'), ('Employees', '164,000')]) }}"
        )
        result = template.render()
        assert "<table" in result
        assert "Market Cap" in result
        assert "$2.8T" in result
        assert "Employees" in result
        assert "164,000" in result
        assert "kv-table" in result

    def test_kv_table_with_title(self, env: jinja2.Environment) -> None:
        """KV table with title renders header row."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import kv_table %}'
            "{{ kv_table([('Ticker', 'AAPL')], title='Company Info') }}"
        )
        result = template.render()
        assert "Company Info" in result
        assert "<thead" in result

    def test_kv_table_with_dicts(self, env: jinja2.Environment) -> None:
        """KV table accepts list of dicts with key/value."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import kv_table %}'
            "{{ kv_table([{'key': 'SIC', 'value': '3571'}]) }}"
        )
        result = template.render()
        assert "SIC" in result
        assert "3571" in result


class TestDataTable:
    """Tests for data_table macro."""

    def test_data_table_renders(self, env: jinja2.Environment) -> None:
        """Data table renders headers and rows."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import data_table %}'
            "{{ data_table(['Metric', 'Value'], [['Revenue', '$394B'], ['Net Income', '$97B']]) }}"
        )
        result = template.render()
        assert "bg-navy" in result
        assert "Metric" in result
        assert "Revenue" in result
        assert "$394B" in result

    def test_data_table_empty(self, env: jinja2.Environment) -> None:
        """Empty data table shows 'No data available'."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import data_table %}'
            "{{ data_table(['Col1'], []) }}"
        )
        result = template.render()
        assert "No data available" in result


# ── Chart Tests ──────────────────────────────────────────────────────


class TestEmbedChart:
    """Tests for embed_chart macro.

    The embed_chart macro reads chart_images from template context
    (not as a positional argument). Pass chart_images via render().
    """

    def test_embed_chart_with_data(self, env: jinja2.Environment) -> None:
        """Chart with base64 data renders img with data URI src and figure caption."""
        template = env.from_string(
            '{% from "components/charts.html.j2" import embed_chart with context %}'
            "{{ embed_chart('stock_chart', 'Stock Price', figure_num=1) }}"
        )
        result = template.render(chart_images={"stock_chart": "iVBOR"})
        assert "<img" in result
        assert "data:image/png;base64,iVBOR" in result
        assert "Stock Price" in result
        assert "Figure 1:" in result
        assert "figcaption" in result

    def test_embed_chart_missing(self, env: jinja2.Environment) -> None:
        """Missing chart renders nothing (suppressed placeholder)."""
        template = env.from_string(
            '{% from "components/charts.html.j2" import embed_chart with context %}'
            "{{ embed_chart('missing_chart', 'Missing Chart') }}"
        )
        result = template.render(chart_images={})
        assert "<img" not in result
        # Placeholder suppressed -- no gray box, no "not available" text
        assert result.strip() == ""

    def test_embed_chart_none_dict(self, env: jinja2.Environment) -> None:
        """None chart_images renders nothing (suppressed placeholder)."""
        template = env.from_string(
            '{% from "components/charts.html.j2" import embed_chart with context %}'
            "{{ embed_chart('radar', 'Radar') }}"
        )
        result = template.render(chart_images=None)
        assert "<img" not in result
        # Placeholder suppressed -- no gray box, no "not available" text
        assert result.strip() == ""


# ── Callout Tests ────────────────────────────────────────────────────


class TestGapNotice:
    """Tests for gap_notice macro."""

    def test_gap_notice(self, env: jinja2.Environment) -> None:
        """Gap notice renders grey 'Data not available' div."""
        template = env.from_string(
            '{% from "components/callouts.html.j2" import gap_notice %}'
            "{{ gap_notice('Board Composition') }}"
        )
        result = template.render()
        assert "Board Composition" in result
        assert "Data not available" in result
        assert "gap-notice" in result

    def test_gap_notice_with_reason(self, env: jinja2.Environment) -> None:
        """Gap notice with reason renders custom explanation."""
        template = env.from_string(
            '{% from "components/callouts.html.j2" import gap_notice %}'
            "{{ gap_notice('Revenue Segments', reason='Not reported in 10-K') }}"
        )
        result = template.render()
        assert "Revenue Segments" in result
        assert "Not reported in 10-K" in result


class TestWarningBox:
    """Tests for warning_box macro."""

    def test_warning_box(self, env: jinja2.Environment) -> None:
        """Warning box renders amber callout."""
        template = env.from_string(
            '{% from "components/callouts.html.j2" import warning_box %}'
            "{{ warning_box('Short interest above 5%') }}"
        )
        result = template.render()
        assert "warning-box" in result
        assert "border-amber-500" in result
        assert "Short interest above 5%" in result

    def test_warning_box_with_do_context(self, env: jinja2.Environment) -> None:
        """Warning box with D&O context shows italic explanation."""
        template = env.from_string(
            '{% from "components/callouts.html.j2" import warning_box %}'
            "{{ warning_box('Elevated short interest', do_context_text='Increases SCA filing probability') }}"
        )
        result = template.render()
        assert "Increases SCA filing probability" in result
        assert "italic" in result


# ── Narrative Tests ──────────────────────────────────────────────────


class TestSectionNarrative:
    """Tests for section_narrative macro."""

    def test_section_narrative_no_ai_label(self, env: jinja2.Environment) -> None:
        """Narrative renders without AI Assessment label (D-04)."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import section_narrative %}'
            "{{ section_narrative('Apple maintains strong financial health.') }}"
        )
        result = template.render()
        assert "AI Assessment" not in result
        assert "Apple maintains strong financial health." in result
        assert "ai-assessment-box" in result

    def test_section_narrative_formal_voice(self, env: jinja2.Environment) -> None:
        """Narrative renders content in formal research report style."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import section_narrative %}'
            "{{ section_narrative('Manual assessment.') }}"
        )
        result = template.render()
        assert "AI Assessment" not in result
        assert "Manual assessment." in result

    def test_section_narrative_empty(self, env: jinja2.Environment) -> None:
        """Empty text renders nothing."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import section_narrative %}'
            "{{ section_narrative('') }}"
        )
        result = template.render().strip()
        assert result == ""


class TestEvidenceChain:
    """Tests for evidence_chain macro."""

    def test_evidence_chain_strings(self, env: jinja2.Environment) -> None:
        """Evidence chain renders bulleted list from strings."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import evidence_chain %}'
            "{{ evidence_chain(['Revenue declined 5%', 'Margin compression noted']) }}"
        )
        result = template.render()
        assert "<li" in result
        assert "Revenue declined 5%" in result
        assert "Margin compression noted" in result

    def test_evidence_chain_dicts(self, env: jinja2.Environment) -> None:
        """Evidence chain renders items with sources."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import evidence_chain %}'
            "{{ evidence_chain([{'text': 'CFO departed', 'source': '8-K 2024-03-15'}]) }}"
        )
        result = template.render()
        assert "CFO departed" in result
        assert "8-K 2024-03-15" in result

    def test_evidence_chain_empty(self, env: jinja2.Environment) -> None:
        """Empty evidence list renders nothing."""
        template = env.from_string(
            '{% from "components/narratives.html.j2" import evidence_chain %}'
            "{{ evidence_chain([]) }}"
        )
        result = template.render().strip()
        assert result == ""


# ── Design System Tests ──────────────────────────────────────────────


class TestDesignSystemHtmlColors:
    """Tests for HTML color constants on DesignSystem."""

    def test_html_colors_exist(self) -> None:
        """DesignSystem has all html_* color constants."""
        from do_uw.stages.render.design_system import DesignSystem

        ds = DesignSystem()
        assert ds.html_navy == "#0B1D3A"
        assert ds.html_gold == "#D4A843"
        assert ds.html_risk_red == "#DC2626"  # Phase 124: updated risk colors
        assert ds.html_caution_amber == "#EA580C"
        assert ds.html_positive_blue == "#2563EB"
        assert ds.html_risk_critical == "#DC2626"
        assert ds.html_risk_elevated == "#EA580C"
        assert ds.html_risk_watch == "#EAB308"
        assert ds.html_risk_positive == "#2563EB"
        assert ds.html_neutral_gray == "#6B7280"
        assert ds.html_bg_alt == "#F8FAFC"

    def test_html_colors_match_css(self) -> None:
        """HTML color constants match values in styles.css."""
        from pathlib import Path

        from do_uw.stages.render.design_system import DesignSystem

        ds = DesignSystem()
        css_path = Path("src/do_uw/templates/html/styles.css")
        css_content = css_path.read_text()

        # All DesignSystem HTML colors should appear in CSS
        assert ds.html_navy in css_content
        assert ds.html_gold in css_content
        assert ds.html_risk_red in css_content
        assert ds.html_caution_amber in css_content
        assert ds.html_positive_blue in css_content
        assert ds.html_neutral_gray in css_content
        assert ds.html_bg_alt in css_content


# ── Paired KV Table Tests (Phase 59-01) ─────────────────────────────


class TestPairedKvTable:
    """Tests for paired_kv_table macro — 4-column CIQ density layout."""

    def test_paired_kv_table_renders_4_columns(self, env: jinja2.Environment) -> None:
        """Paired KV table renders 4 columns per row (label|value|label|value)."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import paired_kv_table %}'
            "{{ paired_kv_table([('Market Cap', '$2.8T'), ('Employees', '164,000')]) }}"
        )
        result = template.render()
        assert "kv-paired" in result, "Expected 'kv-paired' class on paired KV table"
        assert "Market Cap" in result
        assert "$2.8T" in result
        assert "Employees" in result
        assert "164,000" in result
        # Each row should have 2 th and 2 td elements (4 columns)
        assert result.count("<th") == 2, "Expected 2 <th> elements for 2 pairs in 1 row"
        assert result.count("<td") == 2, "Expected 2 <td> elements for 2 pairs in 1 row"

    def test_paired_kv_table_odd_pairs(self, env: jinja2.Environment) -> None:
        """Odd number of pairs renders last row with empty cells for alignment."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import paired_kv_table %}'
            "{{ paired_kv_table([('A', '1'), ('B', '2'), ('C', '3')]) }}"
        )
        result = template.render()
        # 3 pairs = 2 rows, first has 2 th + 2 td, second has 2 th + 2 td (one pair empty)
        assert result.count("<tr") == 2, "Expected 2 rows for 3 pairs"
        # 4 th per row x 2 rows = 4 th total (including the empty placeholder)
        assert result.count("<th") == 4, "Expected 4 <th> elements (3 labels + 1 empty)"
        assert result.count("<td") == 4, "Expected 4 <td> elements (3 values + 1 empty)"

    def test_paired_kv_table_with_title(self, env: jinja2.Environment) -> None:
        """Paired KV table with title renders colspan=4 header."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import paired_kv_table %}'
            "{{ paired_kv_table([('SIC', '3571')], title='Company Profile') }}"
        )
        result = template.render()
        assert "Company Profile" in result
        assert 'colspan="4"' in result
        assert "<thead" in result


# ── Sticky Header Tests (Phase 59-01) ───────────────────────────────


class TestStickyHeader:
    """Tests for sticky-header class on data_table macro."""

    def test_sticky_header_class_on_data_table(self, env: jinja2.Environment) -> None:
        """data_table macro output must contain 'sticky-header' class."""
        template = env.from_string(
            '{% from "components/tables.html.j2" import data_table %}'
            "{{ data_table(['Col1'], [['val1']]) }}"
        )
        result = template.render()
        assert "sticky-header" in result, (
            "Expected 'sticky-header' class on data_table output"
        )


# ── Badge CSS Class Tests (Phase 59-02) ──────────────────────────────


class TestBadgePillClass:
    """Tests for badge-pill CSS class on traffic_light macro."""

    def test_badge_pill_class_triggered(self, env: jinja2.Environment) -> None:
        """TRIGGERED traffic_light must use badge-pill CSS class."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('TRIGGERED') }}"
        )
        result = template.render()
        assert "badge-pill" in result, (
            "Expected 'badge-pill' class on traffic_light TRIGGERED output"
        )

    def test_badge_pill_class_clear(self, env: jinja2.Environment) -> None:
        """CLEAR traffic_light must use badge-pill CSS class."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('CLEAR') }}"
        )
        result = template.render()
        assert "badge-pill" in result, (
            "Expected 'badge-pill' class on traffic_light CLEAR output"
        )

    def test_badge_pill_class_elevated(self, env: jinja2.Environment) -> None:
        """ELEVATED traffic_light must use badge-pill CSS class."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import traffic_light %}'
            "{{ traffic_light('ELEVATED') }}"
        )
        result = template.render()
        assert "badge-pill" in result, (
            "Expected 'badge-pill' class on traffic_light ELEVATED output"
        )


class TestBadgeTierClass:
    """Tests for badge-tier CSS class on tier_badge macro."""

    def test_badge_tier_class_win(self, env: jinja2.Environment) -> None:
        """WIN tier_badge must use badge-tier CSS class."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import tier_badge %}'
            "{{ tier_badge('WIN') }}"
        )
        result = template.render()
        assert "badge-tier" in result, (
            "Expected 'badge-tier' class on tier_badge WIN output"
        )

    def test_badge_tier_class_walk(self, env: jinja2.Environment) -> None:
        """WALK tier_badge must use badge-tier CSS class."""
        template = env.from_string(
            '{% from "components/badges.html.j2" import tier_badge %}'
            "{{ tier_badge('WALK') }}"
        )
        result = template.render()
        assert "badge-tier" in result, (
            "Expected 'badge-tier' class on tier_badge WALK output"
        )
