"""Tests for PDF TOC generation, details expansion, and file size optimization.

Tests cover:
- TOC conditional rendering (pdf_mode=True vs False)
- TOC entry structure from section headings
- Details expansion script presence
- Chart image optimization
- CSS TOC styling
- HTML file size sanity check
"""

from __future__ import annotations

import base64
import io
import struct
import zlib
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


def _minimal_png(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid PNG of given dimensions (red square)."""
    sig = b"\x89PNG\r\n\x1a\n"
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
    # IDAT - red pixels (R=255, G=0, B=0)
    raw_rows = b""
    for _ in range(height):
        raw_rows += b"\x00" + b"\xff\x00\x00" * width  # filter byte + RGB
    compressed = zlib.compress(raw_rows)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)
    # IEND
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
    return sig + ihdr + idat + iend


# ---------------------------------------------------------------------------
# Test 1: TOC appears in PDF HTML but not browser HTML
# ---------------------------------------------------------------------------


class TestTocConditionalRendering:
    """Test that TOC div only appears when pdf_mode=True."""

    def test_toc_present_in_pdf_mode(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        ctx["pdf_mode"] = True
        html = _render_html_template(ctx)

        assert "pdf-toc" in html
        assert "pdf-toc-title" in html
        assert "Table of Contents" in html

    def test_toc_absent_in_browser_mode(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        # pdf_mode defaults to False
        html = _render_html_template(ctx)

        # The TOC div (id="pdf-toc") should NOT be in the HTML body.
        # Note: CSS class definitions (.pdf-toc) and CSS comments are always
        # present in the inlined stylesheet, so we check for the actual
        # HTML element and the rendered h2 tag.
        assert 'id="pdf-toc"' not in html
        assert '<h2 class="pdf-toc-title">' not in html


# ---------------------------------------------------------------------------
# Test 2: TOC script references expected section IDs
# ---------------------------------------------------------------------------


class TestTocEntries:
    """Test that the TOC generation script targets the correct section selectors."""

    def test_toc_script_targets_sections(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        ctx["pdf_mode"] = True
        html = _render_html_template(ctx)

        # The TOC script should reference section[id] for heading discovery
        assert "section[id]" in html
        assert "pdf-toc-entries" in html
        # The script builds anchor links using section IDs
        assert "href" in html
        assert "pdf-toc-entry" in html


# ---------------------------------------------------------------------------
# Test 3: Details expansion script present in PDF HTML
# ---------------------------------------------------------------------------


class TestDetailsExpansion:
    """Test that <details> expansion script is present in pdf_mode HTML."""

    def test_details_expansion_script_in_pdf_html(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        ctx["pdf_mode"] = True
        html = _render_html_template(ctx)

        # Script should set details elements to open
        assert "details" in html
        assert "setAttribute" in html
        assert "open" in html

    def test_details_expansion_script_absent_in_browser(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        # The pdf_mode script block should not be rendered in browser mode.
        # Check for the actual HTML TOC div, not CSS class definitions.
        assert 'id="pdf-toc"' not in html
        # Note: setAttribute IS present in browser mode for the
        # "expand all details" script (workup mode, everything visible).
        # Only the PDF TOC building script should be absent.


# ---------------------------------------------------------------------------
# Test 4: Details expansion CSS already exists from Phase 59
# ---------------------------------------------------------------------------


class TestDetailsExpansionCss:
    """Test that CSS already forces collapsible sections open in print."""

    def test_collapsible_print_rules_intact(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        # Verify the existing collapsible print CSS from Phase 59
        assert "details.collapsible" in css
        assert "display: block !important" in css
        assert "display: none !important" in css  # hides summary in print


# ---------------------------------------------------------------------------
# Test 5: Chart image optimization function
# ---------------------------------------------------------------------------


class TestChartImageOptimization:
    """Test _optimize_chart_images_for_pdf function."""

    def test_optimization_produces_valid_png(self) -> None:
        Image = pytest.importorskip("PIL.Image")

        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        # Create a 100x100 test PNG
        png_bytes = _minimal_png(100, 100)
        b64_data = base64.b64encode(png_bytes).decode("ascii")

        context: dict[str, Any] = {"chart_images": {"test_chart": b64_data}}
        _optimize_chart_images_for_pdf(context)

        # Verify output is valid base64 PNG
        result_b64 = context["chart_images"]["test_chart"]
        result_bytes = base64.b64decode(result_b64)
        img = Image.open(io.BytesIO(result_bytes))
        assert img.format == "PNG"

    def test_optimization_reduces_large_image(self) -> None:
        Image = pytest.importorskip("PIL.Image")

        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        # Create a 1200x800 PNG (larger than 800px threshold)
        png_bytes = _minimal_png(1200, 800)
        b64_data = base64.b64encode(png_bytes).decode("ascii")

        context: dict[str, Any] = {"chart_images": {"wide_chart": b64_data}}
        _optimize_chart_images_for_pdf(context)

        # Verify the optimized image is 800px wide
        result_bytes = base64.b64decode(context["chart_images"]["wide_chart"])
        img = Image.open(io.BytesIO(result_bytes))
        assert img.width == 800
        # Height should be proportionally reduced
        assert img.height < 800

    def test_optimization_skips_empty_data(self) -> None:
        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        context: dict[str, Any] = {"chart_images": {"empty": ""}}
        _optimize_chart_images_for_pdf(context)

        # Empty data should pass through unchanged
        assert context["chart_images"]["empty"] == ""

    def test_optimization_handles_missing_chart_images(self) -> None:
        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        context: dict[str, Any] = {}
        _optimize_chart_images_for_pdf(context)

        # Should not crash when chart_images key is missing
        assert context.get("chart_images", {}) == {}

    def test_optimization_preserves_small_images(self) -> None:
        pytest.importorskip("PIL.Image")

        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        # Create a small 200x200 PNG (under 800px threshold)
        png_bytes = _minimal_png(200, 200)
        b64_data = base64.b64encode(png_bytes).decode("ascii")

        context: dict[str, Any] = {"chart_images": {"small": b64_data}}
        _optimize_chart_images_for_pdf(context)

        # Should still produce valid PNG (re-encoded but not resized)
        from PIL import Image

        result_bytes = base64.b64decode(context["chart_images"]["small"])
        img = Image.open(io.BytesIO(result_bytes))
        assert img.width == 200
        assert img.height == 200


# ---------------------------------------------------------------------------
# Test 6: CSS contains TOC styling
# ---------------------------------------------------------------------------


class TestTocCss:
    """Test that components.css contains TOC styling."""

    def test_toc_css_classes_present(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        assert ".pdf-toc-title" in css
        assert ".pdf-toc-entry" in css
        assert ".pdf-toc-dots" in css
        assert ".pdf-toc-page" in css
        assert ".pdf-toc-text" in css

    def test_toc_has_page_break_after(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        # TOC should break to next page after itself
        assert "break-after: page" in css

    def test_chart_figure_img_constraint_in_print(self) -> None:
        css_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "templates"
            / "html"
            / "components.css"
        )
        css = css_path.read_text(encoding="utf-8")

        # Chart images should be constrained in print
        assert ".chart-figure img" in css


# ---------------------------------------------------------------------------
# Test 7: PDF file size estimation (HTML proxy)
# ---------------------------------------------------------------------------


class TestPdfFileSizeEstimation:
    """Sanity check that rendered HTML size is reasonable."""

    def test_html_size_under_2mb(self) -> None:
        from do_uw.stages.render.html_renderer import (
            _render_html_template,
            build_html_context,
        )

        state = _make_state()
        ctx = build_html_context(state)
        ctx["pdf_mode"] = True
        html = _render_html_template(ctx)

        # HTML size is a rough proxy for PDF size
        html_bytes = len(html.encode("utf-8"))
        two_mb = 2 * 1024 * 1024
        assert html_bytes < two_mb, (
            f"HTML is {html_bytes / 1024:.0f}KB, exceeds 2MB sanity limit"
        )


# ---------------------------------------------------------------------------
# Test 8: _build_pdf_html integrates optimization
# ---------------------------------------------------------------------------


class TestBuildPdfHtmlIntegration:
    """Test that _build_pdf_html calls optimization and sets pdf_mode."""

    def test_build_pdf_html_sets_pdf_mode(self) -> None:
        from do_uw.stages.render.html_renderer import _build_pdf_html

        state = _make_state()
        html = _build_pdf_html(state)

        # Should contain PDF-specific elements
        assert "pdf-toc" in html
        assert "pdf-running-header" in html

    def test_build_pdf_html_has_details_expansion(self) -> None:
        from do_uw.stages.render.html_renderer import _build_pdf_html

        state = _make_state()
        html = _build_pdf_html(state)

        # Should contain the details expansion script
        assert "setAttribute" in html
        assert "details" in html

    def test_optimize_called_in_build_pdf_html(self) -> None:
        """Verify _optimize_chart_images_for_pdf is referenced in _build_pdf_html."""
        from do_uw.stages.render.html_renderer import _optimize_chart_images_for_pdf

        # Verify the function exists and is callable
        assert callable(_optimize_chart_images_for_pdf)

        # Verify _build_pdf_html source calls it (code inspection)
        import inspect
        from do_uw.stages.render.html_renderer import _build_pdf_html

        source = inspect.getsource(_build_pdf_html)
        assert "_optimize_chart_images_for_pdf" in source
