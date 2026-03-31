"""Integration tests: OutputSanitizer wired into html_renderer.render_html_pdf."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Dirty HTML that the sanitizer MUST clean
_DIRTY_BROWSER_HTML = "<html><body><p>**bold leak** and F.7 = 5/8 jargon</p></body></html>"
_DIRTY_PDF_HTML = "<html><body><p>Revenue is **$3.2B** with coverage=100%</p></body></html>"
_CLEAN_HTML = "<html><body><p>Revenue is 3.2B for the year</p></body></html>"


def _make_mock_state() -> MagicMock:
    """Create a minimal mock AnalysisState for render_html_pdf."""
    state = MagicMock()
    state.company.ticker = "TEST"
    state.company.name = "Test Corp"
    return state


class TestSanitizerWiredIntoBrowserHTML:
    """Verify OutputSanitizer runs on browser HTML before writing to disk."""

    @patch("do_uw.stages.render.html_renderer._build_pdf_html", return_value=_CLEAN_HTML)
    @patch("do_uw.stages.render.html_renderer._render_html_template", return_value=_DIRTY_BROWSER_HTML)
    @patch("do_uw.stages.render.html_renderer.build_html_context", return_value={})
    def test_browser_html_is_sanitized(
        self, mock_ctx, mock_render, mock_pdf, tmp_path: Path
    ):
        """Browser HTML written to disk must NOT contain markdown artifacts."""
        from do_uw.stages.render.html_renderer import render_html_pdf
        from do_uw.stages.render.design_system import DesignSystem

        output_path = tmp_path / "TEST_worksheet.pdf"
        ds = MagicMock(spec=DesignSystem)

        # Playwright import will fail -> falls back to weasyprint -> also fails -> returns None
        with patch("do_uw.stages.render.html_renderer._fallback_weasyprint", return_value=None):
            render_html_pdf(_make_mock_state(), output_path, ds, chart_dir=None)

        html_path = output_path.with_suffix(".html")
        assert html_path.exists(), "Browser HTML file must be written"
        content = html_path.read_text(encoding="utf-8")
        assert "**bold" not in content, "Markdown bold must be stripped"
        assert "F.7 = 5/8" not in content, "Factor codes must be stripped"


class TestSanitizerWiredIntoPDFHTML:
    """Verify OutputSanitizer runs on PDF HTML before sending to Playwright."""

    @patch("do_uw.stages.render.html_renderer._build_pdf_html", return_value=_DIRTY_PDF_HTML)
    @patch("do_uw.stages.render.html_renderer._render_html_template", return_value=_CLEAN_HTML)
    @patch("do_uw.stages.render.html_renderer.build_html_context", return_value={})
    def test_pdf_html_is_sanitized(
        self, mock_ctx, mock_render, mock_pdf, tmp_path: Path
    ):
        """PDF HTML passed to Playwright must NOT contain markdown/jargon."""
        from do_uw.stages.render.html_renderer import render_html_pdf
        from do_uw.stages.render.design_system import DesignSystem

        output_path = tmp_path / "TEST_worksheet.pdf"
        ds = MagicMock(spec=DesignSystem)

        # Capture what _build_pdf_html returns AFTER sanitizer processes it
        # We mock Playwright import to fail so it falls through to weasyprint fallback
        with patch("do_uw.stages.render.html_renderer._fallback_weasyprint", return_value=None):
            render_html_pdf(_make_mock_state(), output_path, ds, chart_dir=None)

        # The PDF HTML is sanitized in-memory, we verify by checking the sanitizer was called
        # via the OutputSanitizer.sanitize method (it modifies _DIRTY_PDF_HTML)
        # Since we can't easily capture the in-memory PDF html, we verify via patch
        with (
            patch("do_uw.stages.render.html_renderer._build_pdf_html", return_value=_DIRTY_PDF_HTML),
            patch("do_uw.stages.render.html_renderer._render_html_template", return_value=_CLEAN_HTML),
            patch("do_uw.stages.render.html_renderer.build_html_context", return_value={}),
            patch("do_uw.stages.render.html_renderer._fallback_weasyprint", return_value=None),
            patch("do_uw.stages.render.html_renderer.OutputSanitizer") as mock_san_cls,
        ):
            mock_san = MagicMock()
            mock_san.sanitize.return_value = (_CLEAN_HTML, MagicMock(total_substitutions=0))
            mock_san_cls.from_defaults.return_value = mock_san

            render_html_pdf(_make_mock_state(), output_path, ds, chart_dir=None)

            # sanitize() must be called twice: once for browser, once for PDF
            assert mock_san.sanitize.call_count == 2, (
                f"Expected 2 sanitize() calls (browser + PDF), got {mock_san.sanitize.call_count}"
            )


class TestSanitizationLogFile:
    """Verify sanitization log is written when substitutions are made."""

    @patch("do_uw.stages.render.html_renderer._build_pdf_html", return_value=_CLEAN_HTML)
    @patch("do_uw.stages.render.html_renderer._render_html_template", return_value=_DIRTY_BROWSER_HTML)
    @patch("do_uw.stages.render.html_renderer.build_html_context", return_value={})
    def test_log_file_created_when_dirty(
        self, mock_ctx, mock_render, mock_pdf, tmp_path: Path
    ):
        """Sanitization log must be written when browser HTML has substitutions."""
        from do_uw.stages.render.html_renderer import render_html_pdf
        from do_uw.stages.render.design_system import DesignSystem

        output_path = tmp_path / "TEST_worksheet.pdf"
        ds = MagicMock(spec=DesignSystem)

        with patch("do_uw.stages.render.html_renderer._fallback_weasyprint", return_value=None):
            render_html_pdf(_make_mock_state(), output_path, ds, chart_dir=None)

        log_path = tmp_path / "TEST_worksheet_sanitization_log.txt"
        assert log_path.exists(), "Sanitization log must be created when substitutions found"
        content = log_path.read_text(encoding="utf-8")
        assert "substitution" in content.lower(), "Log must contain substitution info"

    @patch("do_uw.stages.render.html_renderer._build_pdf_html", return_value=_CLEAN_HTML)
    @patch("do_uw.stages.render.html_renderer._render_html_template", return_value=_CLEAN_HTML)
    @patch("do_uw.stages.render.html_renderer.build_html_context", return_value={})
    def test_no_log_file_when_clean(
        self, mock_ctx, mock_render, mock_pdf, tmp_path: Path
    ):
        """No sanitization log when HTML is already clean."""
        from do_uw.stages.render.html_renderer import render_html_pdf
        from do_uw.stages.render.design_system import DesignSystem

        output_path = tmp_path / "TEST_worksheet.pdf"
        ds = MagicMock(spec=DesignSystem)

        with patch("do_uw.stages.render.html_renderer._fallback_weasyprint", return_value=None):
            render_html_pdf(_make_mock_state(), output_path, ds, chart_dir=None)

        log_path = tmp_path / "TEST_worksheet_sanitization_log.txt"
        assert not log_path.exists(), "No log file should be created when HTML is clean"
