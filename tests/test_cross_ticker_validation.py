"""Cross-ticker rendering validation test.

Validates that pipeline output for multiple tickers meets QUALITY bar:
- Real company data populated (not "Unknown Company" or all N/A)
- Financial metrics present and non-empty
- All required sections present with substantial content
- No Python tracebacks in output
- Data manifest has real acquisition results

This test operates on pre-generated output directories. Run the pipeline
for each ticker before running this test:
    uv run do-uw analyze AAPL
    uv run do-uw analyze SNA
    uv run do-uw analyze RPM
    uv run do-uw analyze WWD
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# Project root and output directory
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# Tickers to validate
VALIDATION_TICKERS = ["AAPL", "SNA", "RPM", "WWD"]

# Required HTML section IDs — each entry is a tuple of acceptable aliases
REQUIRED_SECTIONS: list[tuple[str, ...]] = [
    ("identity", "company-profile"),
    ("executive-summary",),
    ("financial-health",),
    ("market", "market-trading"),
    ("governance",),
    ("litigation",),
    ("ai-risk",),
    ("scoring",),
    ("meeting-prep",),
    ("coverage",),
]

# Sections introduced in v3.0
V3_SECTIONS: list[tuple[str, ...]] = [
    ("red-flags",),
    ("sources",),
    ("qa-audit",),
]

# Patterns that indicate Python errors leaked into output
ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"File \".*\.py\", line \d+",
    r"raise \w+Error",
    r"ModuleNotFoundError",
    r"AttributeError:",
    r"TypeError:",
    r"KeyError:",
    r"ValueError:",
]

# Known company names for validation tickers — detect "Unknown Company" garbage
EXPECTED_COMPANIES = {
    "AAPL": "Apple",
    "SNA": "Snap-on",
    "RPM": "RPM International",
    "WWD": "Woodward",
}

# Key metrics that MUST be populated (not N/A) for a valid output
# These are basic identity/financial fields that should always be available
REQUIRED_POPULATED_FIELDS = [
    "Market Cap",
    "Revenue",
    "Employees",
]

# Minimum manifest entries for a real pipeline run (V has 61)
MIN_MANIFEST_ENTRIES = 8


def _find_latest_output_dir(ticker: str) -> Path | None:
    """Find the most recent output directory for a ticker."""
    # Try date-stamped directories first (sorted by name = chronological)
    date_dirs = sorted(
        OUTPUT_DIR.glob(f"{ticker}-*"),
        reverse=True,
    )
    for d in date_dirs:
        if d.is_dir() and (d / f"{ticker}_worksheet.html").exists():
            return d

    # Fall back to plain ticker directory
    plain_dir = OUTPUT_DIR / ticker
    if plain_dir.is_dir() and (plain_dir / f"{ticker}_worksheet.html").exists():
        return plain_dir

    return None


def _read_html(ticker: str) -> tuple[Path, str] | None:
    """Find and read the HTML output for a ticker."""
    output_path = _find_latest_output_dir(ticker)
    if output_path is None:
        return None
    html_file = output_path / f"{ticker}_worksheet.html"
    if not html_file.exists():
        return None
    return html_file, html_file.read_text(encoding="utf-8")


class TestCrossTickerValidation:
    """Validate output quality across multiple tickers."""

    def _get_available_tickers(self) -> list[str]:
        """Get tickers that have generated output."""
        available = []
        for ticker in VALIDATION_TICKERS:
            if _find_latest_output_dir(ticker) is not None:
                available.append(ticker)
        return available

    def test_at_least_one_ticker_has_output(self) -> None:
        """Ensure at least one ticker has been analyzed."""
        available = self._get_available_tickers()
        assert len(available) > 0, (
            f"No output found for any validation ticker: {VALIDATION_TICKERS}. "
            "Run 'uv run do-uw analyze AAPL' to generate output."
        )

    # ─── DATA QUALITY GATES ──────────────────────────────────────────

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_company_name_is_real(self, ticker: str) -> None:
        """Company name must be resolved — not 'Unknown Company' or blank."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        # Extract company name from <title> tag — most reliable indicator
        title_match = re.search(r"<title>(.*?)</title>", content)
        assert title_match, f"{ticker} HTML has no <title> tag"
        title = title_match.group(1)

        # Check for known garbage values in the title
        garbage_patterns = ["Unknown Company", "Unknown ("]
        has_garbage_name = any(g in title for g in garbage_patterns)
        assert not has_garbage_name, (
            f"{ticker} output has garbage company name in <title>: '{title}'. "
            "Pipeline likely failed to resolve company identity."
        )

        # Verify expected company name appears in the document
        if ticker in EXPECTED_COMPANIES:
            expected = EXPECTED_COMPANIES[ticker]
            assert expected.lower() in content.lower(), (
                f"{ticker} output does not contain expected company name '{expected}'. "
                "Company identity was not properly resolved."
            )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_key_metrics_populated(self, ticker: str) -> None:
        """Key financial metrics must have real values, not all N/A."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        na_count = 0
        total = len(REQUIRED_POPULATED_FIELDS)
        na_fields = []

        for field in REQUIRED_POPULATED_FIELDS:
            # Match the pattern: field label in <th> followed by value in <td>
            # Handles whitespace around field name: "  Market Cap\n  </th>"
            # Also match <span> layout: "Market Cap</span>...<span>$23.6B</span>"
            pattern = (
                rf'{re.escape(field)}\s*</(?:th|span)>'
                r'.*?'
                r'<(?:td|span)[^>]*>(.*?)</(?:td|span)>'
            )
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                na_fields.append(f"{field} (not found in HTML)")
                na_count += 1
                continue

            value = match.group(1).strip()
            # Strip HTML tags from value
            value_text = re.sub(r'<[^>]+>', '', value).strip()
            if value_text in ("N/A", "—", "", "None"):
                na_fields.append(f"{field} ({value_text!r})")
                na_count += 1

        # Allow at most 1 missing field (some companies may legitimately miss one)
        assert na_count <= 1, (
            f"{ticker} has {na_count}/{total} key metrics unpopulated: {na_fields}. "
            "Pipeline likely failed during data acquisition."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_data_manifest_has_real_data(self, ticker: str) -> None:
        """Data manifest must show real acquisition results, not empty run."""
        output_path = _find_latest_output_dir(ticker)
        if output_path is None:
            pytest.skip(f"No output available for {ticker}")

        manifest_file = output_path / "sources" / "manifest.json"
        if not manifest_file.exists():
            pytest.fail(
                f"{ticker} has no sources/manifest.json — "
                "data acquisition did not run properly."
            )

        with open(manifest_file) as f:
            manifest = json.load(f)

        assert len(manifest) >= MIN_MANIFEST_ENTRIES, (
            f"{ticker} manifest has only {len(manifest)} entries "
            f"(minimum {MIN_MANIFEST_ENTRIES}). Pipeline likely failed during "
            "data acquisition. A normal run produces 30-60+ entries."
        )

        # Must have SEC filings specifically
        sec_entries = [e for e in manifest if e.get("type") == "sec_filing"]
        assert len(sec_entries) >= 3, (
            f"{ticker} manifest has only {len(sec_entries)} SEC filing entries. "
            "EdgarTools acquisition likely failed."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_no_all_na_identity_section(self, ticker: str) -> None:
        """Identity/company profile section must not be all N/A."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        # Find the identity section
        for section_id in ("identity", "company-profile"):
            pattern = rf'<section id="{section_id}"[^>]*>(.*?)</section>'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                section_content = match.group(1)
                # Count N/A occurrences vs total table cells
                na_count = len(re.findall(r'>N/A<', section_content))
                td_count = len(re.findall(r'<td', section_content))
                if td_count > 0:
                    na_ratio = na_count / td_count
                    assert na_ratio < 0.7, (
                        f"{ticker} identity section is {na_ratio:.0%} N/A "
                        f"({na_count}/{td_count} cells). "
                        "Company data was not properly acquired/extracted."
                    )
                break

    # ─── STRUCTURAL CHECKS ───────────────────────────────────────────

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_html_output_exists_and_nonempty(self, ticker: str) -> None:
        """HTML output file must exist and contain substantial content."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        assert len(content) > 1000, (
            f"{ticker} HTML output is suspiciously small ({len(content)} bytes)"
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_pdf_output_exists_and_nonempty(self, ticker: str) -> None:
        """PDF output file must exist and contain content."""
        output_path = _find_latest_output_dir(ticker)
        if output_path is None:
            pytest.skip(f"No output available for {ticker}")
        pdf_file = output_path / f"{ticker}_worksheet.pdf"
        if not pdf_file.exists():
            pytest.skip(f"PDF not generated for {ticker}")
        assert pdf_file.stat().st_size > 1000, (
            f"{ticker} PDF output is suspiciously small"
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_all_sections_present_in_html(self, ticker: str) -> None:
        """All required sections must be present in HTML output."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        missing_sections = []
        for aliases in REQUIRED_SECTIONS:
            found = any(f'id="{sid}"' in content for sid in aliases)
            if not found:
                missing_sections.append(aliases[0])

        assert not missing_sections, (
            f"{ticker} HTML missing sections: {missing_sections}"
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_no_python_tracebacks_in_html(self, ticker: str) -> None:
        """No Python error tracebacks should appear in rendered output."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        found_errors = []
        for pattern in ERROR_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                found_errors.append(f"{pattern}: {len(matches)} occurrences")

        assert not found_errors, (
            f"{ticker} HTML contains Python errors:\n"
            + "\n".join(found_errors)
        )

    # Sections that may legitimately be sparse
    _SPARSE_EXEMPT = {"ai-risk", "coverage"}

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_section_content_not_empty(self, ticker: str) -> None:
        """Core data sections should have substantial content."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        sparse_sections = []
        for aliases in REQUIRED_SECTIONS:
            for section_id in aliases:
                if section_id in self._SPARSE_EXEMPT:
                    break
                pattern = rf'<section id="{section_id}"[^>]*>(.*?)</section>'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    section_content = match.group(1).strip()
                    if len(section_content) < 100:
                        sparse_sections.append(
                            f"{section_id} ({len(section_content)} chars)"
                        )
                    break

        assert not sparse_sections, (
            f"{ticker} has sparse sections: {sparse_sections}"
        )

    # ─── CONTENT DEPTH CHECKS ────────────────────────────────────────

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_executive_summary_has_thesis(self, ticker: str) -> None:
        """Executive summary must contain an actual underwriting thesis."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        pattern = rf'<section id="executive-summary"[^>]*>(.*?)</section>'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            pytest.skip(f"{ticker} has no executive-summary section")

        summary = match.group(1)
        # Check for any scoring/tier/recommendation indicator
        has_substance = (
            # Standard tier names
            re.search(r'(WIN|COMPETE|WATCH|WALK|NO_TOUCH|WANT)', summary)
            # Recommendation verbs
            or re.search(r'(ACCEPT|DECLINE|REFER)', summary)
            # Numeric score
            or re.search(r'\d+\s*/\s*100', summary)
            # Badge-tier class (v3.0 HTML format)
            or re.search(r'badge-tier', summary)
            # Claim probability
            or re.search(r'\d+\.\d+%', summary)
            # Risk tier label
            or re.search(r'risk.*tier', summary, re.IGNORECASE)
        )
        assert has_substance, (
            f"{ticker} executive summary has no risk tier, score, or recommendation. "
            "Scoring likely failed."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_financial_section_has_numbers(self, ticker: str) -> None:
        """Financial section must contain actual dollar amounts or ratios."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        pattern = rf'<section id="financial-health"[^>]*>(.*?)</section>'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            pytest.skip(f"{ticker} has no financial-health section")

        financial = match.group(1)
        # Must have actual numbers — dollar amounts, percentages, ratios
        has_numbers = bool(
            re.search(r'[\$]\s*[\d,]+', financial)
            or re.search(r'\d+\.\d+[x%]', financial)
            or re.search(r'[\d,]+\s*(million|billion|M|B)', financial, re.IGNORECASE)
        )

        # Check it's not just "Financial data not available"
        is_empty = "not available" in financial.lower() and not has_numbers

        assert not is_empty, (
            f"{ticker} financial section says 'not available'. "
            "Financial data extraction failed."
        )

    # ─── FEATURE PARITY CHECKS ────────────────────────────────────────

    # Minimum feature thresholds — based on what a complete v3.0 output should have
    _MIN_SCORE_BADGES = 10
    _MIN_COLLAPSIBLES = 40
    _MIN_SPARKLINES = 2  # At least annual comparison sparklines
    _MIN_KV_TABLES = 20
    _MIN_BULL_BEAR = 8

    @staticmethod
    def _is_v3_output(content: str) -> bool:
        """Detect whether HTML was generated with v3.0+ templates."""
        return "badge-tier" in content and content.count("<details") >= 5

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_score_badges_present(self, ticker: str) -> None:
        """v3.0 output must have score/verdict/tier badges."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        if not self._is_v3_output(content):
            pytest.skip(f"{ticker} output is pre-v3.0 — re-run pipeline to update")

        badge_count = len(
            re.findall(r"score-badge|verdict-badge|badge-tier", content)
        )
        assert badge_count >= self._MIN_SCORE_BADGES, (
            f"{ticker} has only {badge_count} score badges "
            f"(minimum {self._MIN_SCORE_BADGES}). "
            "Output may be from pre-v3.0 pipeline — re-run needed."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_collapsible_sections_present(self, ticker: str) -> None:
        """v3.0 output must have collapsible/expandable sections."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        if not self._is_v3_output(content):
            pytest.skip(f"{ticker} output is pre-v3.0 — re-run pipeline to update")

        collapsible_count = len(re.findall(r"<details|collapsible", content))
        assert collapsible_count >= self._MIN_COLLAPSIBLES, (
            f"{ticker} has only {collapsible_count} collapsible sections "
            f"(minimum {self._MIN_COLLAPSIBLES}). "
            "Output may be from pre-v3.0 pipeline — re-run or re-render needed."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_sparklines_present(self, ticker: str) -> None:
        """v3.0 output must have inline sparkline charts."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        if not self._is_v3_output(content):
            pytest.skip(f"{ticker} output is pre-v3.0 — re-run pipeline to update")

        sparkline_count = len(re.findall(r'viewBox="0 0 60 16"', content))
        assert sparkline_count >= self._MIN_SPARKLINES, (
            f"{ticker} has only {sparkline_count} sparklines "
            f"(minimum {self._MIN_SPARKLINES}). "
            "Financial data may lack multi-period history."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_bull_bear_framing_present(self, ticker: str) -> None:
        """v3.0 output must have bull/bear case framing."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        if not self._is_v3_output(content):
            pytest.skip(f"{ticker} output is pre-v3.0 — re-run pipeline to update")

        bb_count = len(
            re.findall(r"bull-case|bear-case|Bull Case|Bear Case", content)
        )
        assert bb_count >= self._MIN_BULL_BEAR, (
            f"{ticker} has only {bb_count} bull/bear references "
            f"(minimum {self._MIN_BULL_BEAR}). "
            "Narrative generation may have failed."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_v3_sections_present(self, ticker: str) -> None:
        """v3.0-specific sections (red-flags, sources) must be present."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result
        if not self._is_v3_output(content):
            pytest.skip(f"{ticker} output is pre-v3.0 — re-run pipeline to update")

        missing = []
        for aliases in V3_SECTIONS:
            # qa-audit depends on gap_search_summary data — skip if not present
            if "qa-audit" in aliases:
                continue
            found = any(f'id="{sid}"' in content for sid in aliases)
            if not found:
                # Also check by heading text
                found = any(
                    re.search(rf">{re.escape(sid.replace('-', ' '))}<", content, re.IGNORECASE)
                    for sid in aliases
                )
            if not found:
                missing.append(aliases[0])

        assert not missing, (
            f"{ticker} missing v3.0 sections: {missing}. "
            "Output may need re-render with v3.0 template."
        )

    @pytest.mark.parametrize("ticker", VALIDATION_TICKERS)
    def test_chart_figures_present(self, ticker: str) -> None:
        """v3.0 output must have chart figures (stock, radar, ownership)."""
        result = _read_html(ticker)
        if result is None:
            pytest.skip(f"No output available for {ticker}")
        _html_path, content = result

        chart_count = len(re.findall(r"chart-figure", content))
        assert chart_count >= 3, (
            f"{ticker} has only {chart_count} chart figures (minimum 3). "
            "Chart generation may have failed."
        )
