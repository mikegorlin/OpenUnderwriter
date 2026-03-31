"""Tests for print/PDF CSS divergence -- screen vs print UX (Phase 114-04).

Validates that @media print rules correctly:
- Hide signal drill-down panels (epistemological trace serves this purpose in print)
- Add page breaks for scorecard, executive brief, decision record
- Preserve heatmap colors with print-color-adjust
- Hide sidebar in print
- Render CRF banner as static (not sticky)
- Compact epistemological trace table headers
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


# CSS file paths
_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html"
_STYLES_CSS = _TEMPLATE_DIR / "styles.css"
_SIDEBAR_CSS = _TEMPLATE_DIR / "sidebar.css"
_SCORECARD_CSS = _TEMPLATE_DIR / "scorecard.css"
_BASE_TEMPLATE = _TEMPLATE_DIR / "base.html.j2"


def _extract_print_blocks(css_text: str) -> str:
    """Extract all content within @media print { ... } blocks."""
    blocks: list[str] = []
    pattern = re.compile(r"@media\s+print\s*\{", re.IGNORECASE)
    for match in pattern.finditer(css_text):
        start = match.end()
        depth = 1
        pos = start
        while pos < len(css_text) and depth > 0:
            if css_text[pos] == "{":
                depth += 1
            elif css_text[pos] == "}":
                depth -= 1
            pos += 1
        blocks.append(css_text[start : pos - 1])
    return "\n".join(blocks)


@pytest.fixture()
def styles_print() -> str:
    return _extract_print_blocks(_STYLES_CSS.read_text())


@pytest.fixture()
def sidebar_print() -> str:
    return _extract_print_blocks(_SIDEBAR_CSS.read_text())


@pytest.fixture()
def scorecard_print() -> str:
    return _extract_print_blocks(_SCORECARD_CSS.read_text())


class TestScorecardPrintBreaks:
    """Scorecard page should break-after in print."""

    def test_scorecard_page_break(self, scorecard_print: str) -> None:
        assert "scorecard-page" in scorecard_print
        assert "break-after" in scorecard_print or "page-break-after" in scorecard_print

    def test_scorecard_grid_max_height(self, scorecard_print: str) -> None:
        assert "scorecard-grid" in scorecard_print
        assert "max-height" in scorecard_print

    def test_scorecard_radar_scale(self, scorecard_print: str) -> None:
        assert "scorecard-radar" in scorecard_print
        assert "transform" in scorecard_print
        assert "scale" in scorecard_print


class TestExecutiveBriefPrintBreak:
    """Executive brief should break-after in print."""

    def test_executive_brief_break(self, scorecard_print: str) -> None:
        assert "executive-brief" in scorecard_print
        assert "break-after" in scorecard_print or "page-break-after" in scorecard_print


class TestDecisionRecordPrintBreak:
    """Decision record should break-before in print."""

    def test_decision_record_break(self, styles_print: str) -> None:
        assert "decision-record" in styles_print
        assert "break-before" in styles_print or "page-break-before" in styles_print

    def test_decision_record_borders(self, styles_print: str) -> None:
        assert "rationale-box" in styles_print
        assert "posture-option" in styles_print


class TestSignalDrilldownHiddenInPrint:
    """Signal drill-down panels must be hidden in print (trace appendix replaces them)."""

    def test_drilldown_display_none(self, scorecard_print: str) -> None:
        assert "signal-drilldown" in scorecard_print
        assert "display: none" in scorecard_print or "display:none" in scorecard_print


class TestHeatmapPrintColors:
    """Heatmap cells must preserve colors in print via print-color-adjust."""

    def test_global_print_color_adjust(self, styles_print: str) -> None:
        # Global rule ensures all elements print colors
        assert "print-color-adjust" in styles_print

    def test_heatmap_cell_print_color(self, scorecard_print: str) -> None:
        assert "heatmap-cell" in scorecard_print
        assert "print-color-adjust" in scorecard_print


class TestSidebarHiddenInPrint:
    """Sidebar TOC must be hidden in print."""

    def test_sidebar_hidden(self, sidebar_print: str) -> None:
        assert "sidebar-toc" in sidebar_print
        assert "display: none" in sidebar_print or "display:none" in sidebar_print


class TestCRFBannerNotStickyInPrint:
    """CRF banner should render as static box in print, not sticky."""

    def test_crf_banner_static(self, scorecard_print: str) -> None:
        assert "crf-banner" in scorecard_print
        assert "position: static" in scorecard_print or "position:static" in scorecard_print


class TestTraceTablePrint:
    """Epistemological trace table should have repeating headers in print."""

    def test_trace_table_compact_font(self, styles_print: str) -> None:
        assert "trace-table" in styles_print
        assert "7pt" in styles_print

    def test_thead_header_group(self, styles_print: str) -> None:
        assert "table-header-group" in styles_print


class TestPdfModeDetailsExpansion:
    """base.html.j2 pdf_mode script should exclude signal-drilldown from expansion."""

    def test_details_excludes_signal_drilldown(self) -> None:
        template = _BASE_TEMPLATE.read_text()
        assert "details:not(.signal-drilldown)" in template
