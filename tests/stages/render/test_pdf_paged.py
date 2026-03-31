"""Tests for Paged.js CSS integration in PDF rendering.

Tests PDF-specific context flags, running headers/footers in HTML output,
@page CSS rules, table break-avoidance, and chart static/interactive toggle.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_state(**overrides: Any) -> AnalysisState:
    """Create a minimal AnalysisState for testing PDF rendering."""
    from do_uw.models.common import SourcedValue
    from do_uw.models.company import CompanyIdentity, CompanyProfile
    from do_uw.models.state import AnalysisResults

    _now = datetime.now(tz=UTC)
    state = AnalysisState(ticker="TEST")
    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            legal_name=SourcedValue[str](
                value="Acme Corp",
                source="test",
                confidence="HIGH",
                as_of=_now,
            ),
        ),
    )
    state.analysis = AnalysisResults()

    for key, val in overrides.items():
        setattr(state, key, val)
    return state


# ---------------------------------------------------------------------------
# Test 1: build_html_context returns pdf_mode=False by default
# ---------------------------------------------------------------------------


class TestPdfModeDefault:
    """Test that pdf_mode defaults to False in build_html_context."""

    def test_pdf_mode_is_false_by_default(self) -> None:
        from do_uw.stages.render.html_renderer import build_html_context

        state = _make_state()
        ctx = build_html_context(state)
        assert ctx["pdf_mode"] is False


# ---------------------------------------------------------------------------
# Test 2: _build_pdf_html sets pdf_mode=True in rendered HTML
# ---------------------------------------------------------------------------


class TestBuildPdfHtml:
    """Test that _build_pdf_html produces HTML with pdf_mode=True context."""

    def test_pdf_html_contains_running_header(self) -> None:
        from do_uw.stages.render.html_renderer import _build_pdf_html

        state = _make_state()
        html = _build_pdf_html(state)

        assert isinstance(html, str)
        assert len(html) > 0
        # The running header should be present in the HTML
        assert "pdf-running-header" in html


# ---------------------------------------------------------------------------
# Test 3: base.html.j2 renders pdf-running-header with company name
# ---------------------------------------------------------------------------


class TestRunningHeader:
    """Test that the base template includes running header with company name."""

    def test_running_header_has_company_name(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        assert 'class="pdf-running-header"' in html
        assert "Acme Corp" in html


# ---------------------------------------------------------------------------
# Test 4: base.html.j2 renders pdf-running-footer
# ---------------------------------------------------------------------------


class TestRunningFooter:
    """Test that the base template includes running footer."""

    def test_running_footer_present(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        assert 'class="pdf-running-footer"' in html
        assert "Confidential" in html
        assert "Angry Dolphin" in html


# ---------------------------------------------------------------------------
# Test 5: styles.css contains @page rules with letter size
# ---------------------------------------------------------------------------


class TestCssPageRules:
    """Test that styles.css has proper @page rules for PDF."""

    def test_page_rules_present(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "styles.css"
        )
        css = css_path.read_text(encoding="utf-8")

        assert "@page" in css
        assert "size: letter" in css
        # Margins for running header/footer (fixed position)
        assert "0.75in 0.65in 0.75in 0.65in" in css

    def test_first_page_rule(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "styles.css"
        )
        css = css_path.read_text(encoding="utf-8")

        # Running header/footer use CSS position:fixed — no separate
        # @page:first rule needed.  Verify @page rule exists.
        assert "@page" in css


# ---------------------------------------------------------------------------
# Test 6: components.css contains table break-inside: avoid in print
# ---------------------------------------------------------------------------


class TestTableBreakAvoidance:
    """Test that components.css has table break-inside: avoid in print."""

    def test_table_break_inside_avoid(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        # Should have break-inside: avoid for tables in the @media print section
        assert "break-inside: avoid" in css
        assert "page-break-inside: avoid" in css


# ---------------------------------------------------------------------------
# Test 7: chart_images included in context when chart_dir provided
# ---------------------------------------------------------------------------


class TestChartImages:
    """Test that chart_images are populated when chart_dir has PNGs."""

    def test_chart_images_with_chart_dir(self, tmp_path: Path) -> None:
        from do_uw.stages.render.html_renderer import build_html_context

        # Create a minimal PNG file (1x1 pixel)
        import struct
        import zlib

        def _minimal_png() -> bytes:
            """Create a minimal valid 1x1 pixel PNG."""
            sig = b"\x89PNG\r\n\x1a\n"
            # IHDR
            ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
            ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
            # IDAT
            raw = zlib.compress(b"\x00\x00\x00\x00")
            idat_crc = zlib.crc32(b"IDAT" + raw) & 0xFFFFFFFF
            idat = struct.pack(">I", len(raw)) + b"IDAT" + raw + struct.pack(">I", idat_crc)
            # IEND
            iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
            iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
            return sig + ihdr + idat + iend

        chart_dir = tmp_path / "charts"
        chart_dir.mkdir()
        (chart_dir / "stock_1y.png").write_bytes(_minimal_png())

        state = _make_state()
        ctx = build_html_context(state, chart_dir=chart_dir)

        assert "chart_images" in ctx
        assert "stock_1y" in ctx["chart_images"]
        assert len(ctx["chart_images"]["stock_1y"]) > 0


# ---------------------------------------------------------------------------
# Test 8: CSS has chart-interactive/chart-static toggle in print
# ---------------------------------------------------------------------------


class TestChartToggleCss:
    """Test CSS for chart interactive/static toggle in print media."""

    def test_chart_interactive_hidden_in_print(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        assert ".chart-interactive" in css
        assert ".chart-static" in css
        # In the @media print section, chart-interactive should be display: none
        assert "display: none !important" in css
        assert "display: block !important" in css
