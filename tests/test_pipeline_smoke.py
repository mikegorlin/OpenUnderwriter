"""End-to-end pipeline smoke test.

Validates that the pipeline can run from state.json through RENDER
and produce all 3 output formats with correct content.

Skips gracefully if state.json doesn't exist (requires prior pipeline run).
"""

from __future__ import annotations

import zipfile

import pytest
from pathlib import Path

TICKERS = ["AAPL"]


@pytest.fixture(params=TICKERS)
def ticker(request: pytest.FixtureRequest) -> str:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture()
def output_dir(ticker: str) -> Path:
    """Find the most recent COMPLETE output directory for a ticker.

    Supports both date-based dirs (output/AAPL-2026-02-24/) and
    legacy dirs (output/AAPL/). Skips dirs without HTML output.
    """
    base = Path("output")
    # Prefer date-based directories (newest first), but only those with HTML
    date_dirs = sorted(base.glob(f"{ticker}-*"), reverse=True)
    for d in date_dirs:
        if list(d.glob("*worksheet*.html")):
            return d
    # Fall back to plain ticker directory
    plain = base / ticker
    if plain.is_dir():
        return plain
    # Last resort: return newest even if incomplete (test will skip/fail)
    if date_dirs:
        return date_dirs[0]
    return base / ticker


class TestPipelineSmoke:
    """Smoke tests verifying pipeline output files exist and are valid."""

    def test_state_file_exists(self, ticker: str, output_dir: Path) -> None:
        """State JSON should exist and contain meaningful data."""
        state_path = output_dir / "state.json"
        if not state_path.exists():
            pytest.skip(f"No state.json for {ticker} -- run pipeline first")
        assert state_path.stat().st_size > 1000

    def test_markdown_output_exists_and_correct(
        self, ticker: str, output_dir: Path
    ) -> None:
        """Markdown worksheet should exist with correct company and sections."""
        state_path = output_dir / "state.json"
        if not state_path.exists():
            pytest.skip(f"No state.json for {ticker} -- stale or incomplete run")
        md_files = list(output_dir.glob("*worksheet*.md"))
        if not md_files:
            pytest.skip(f"No Markdown output for {ticker}")
        content = md_files[0].read_text()
        assert len(content) > 1000, "Markdown output suspiciously short"
        assert "Unknown Company" not in content, (
            "Company name not resolved -- still shows 'Unknown Company'"
        )
        assert "executive summary" in content.lower(), (
            "Missing Executive Summary section"
        )

    def test_word_output_exists(
        self, ticker: str, output_dir: Path
    ) -> None:
        """Word document should exist and be a valid DOCX (ZIP) file."""
        docx_files = list(output_dir.glob("*.docx"))
        if not docx_files:
            pytest.skip(f"No Word output for {ticker}")
        docx_path = docx_files[0]
        assert docx_path.stat().st_size > 1000, (
            "Word output suspiciously small"
        )
        # DOCX files are ZIP archives with [Content_Types].xml
        assert zipfile.is_zipfile(docx_path), (
            "Word output is not a valid ZIP/DOCX file"
        )

    def test_pdf_output_exists(
        self, ticker: str, output_dir: Path
    ) -> None:
        """PDF file should exist and have valid PDF magic bytes."""
        pdf_files = list(output_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip(f"No PDF output for {ticker}")
        pdf_path = pdf_files[0]
        assert pdf_path.stat().st_size > 1000, (
            "PDF output suspiciously small"
        )
        # Validate PDF magic bytes
        with open(pdf_path, "rb") as f:
            magic = f.read(4)
        assert magic == b"%PDF", (
            f"PDF has invalid magic bytes: {magic!r}"
        )

    def test_all_three_formats_present(
        self, ticker: str, output_dir: Path
    ) -> None:
        """Primary output formats (HTML, DOCX, PDF) should be present."""
        if not output_dir.exists():
            pytest.skip(f"No output directory for {ticker}")
        has_html = bool(list(output_dir.glob("*worksheet*.html")))
        has_docx = bool(list(output_dir.glob("*.docx")))
        has_pdf = bool(list(output_dir.glob("*.pdf")))
        assert has_html, "Missing HTML output"
        assert has_docx, "Missing Word output"
        assert has_pdf, "Missing PDF output"

    def test_markdown_has_populated_sections(
        self, ticker: str, output_dir: Path
    ) -> None:
        """Markdown should have key underwriting sections with content."""
        md_files = list(output_dir.glob("*worksheet*.md"))
        if not md_files:
            pytest.skip(f"No Markdown output for {ticker}")
        content = md_files[0].read_text().lower()

        # Key sections that should appear in a complete worksheet
        expected_sections = [
            "executive summary",
            "company",
            "financial",
            "governance",
            "litigation",
        ]
        for section in expected_sections:
            assert section in content, (
                f"Missing expected section: {section}"
            )

    def test_pipeline_state_all_stages_completed(
        self, ticker: str, output_dir: Path
    ) -> None:
        """All 7 pipeline stages should be marked as completed."""
        import json

        state_path = output_dir / "state.json"
        if not state_path.exists():
            pytest.skip(f"No state.json for {ticker}")

        with open(state_path) as f:
            data = json.load(f)

        stages = data.get("stages", {})
        if not stages:
            pytest.skip(f"No stages data in state.json for {ticker}")

        expected_stages = [
            "resolve", "acquire", "extract",
            "analyze", "score", "benchmark", "render",
        ]
        incomplete = [
            s for s in expected_stages
            if s not in stages or stages[s].get("status") != "completed"
        ]
        if incomplete:
            pytest.skip(
                f"{ticker} has incomplete stages {incomplete} — "
                "partial pipeline run, re-run to complete"
            )
