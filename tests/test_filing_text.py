"""Tests for filing text fetcher -- section parsing and Exhibit 21.

Phase 4 refactor: Section parsing moved to extract/filing_sections.py,
HTML stripping and Exhibit 21 moved to filing_fetcher.py. Imports updated.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from do_uw.stages.acquire.clients.filing_fetcher import (
    fetch_exhibit_21,
)
from do_uw.stages.acquire.clients.filing_fetcher import (
    strip_html as _strip_html,
)
from do_uw.stages.acquire.clients.filing_text import (
    _get_latest_filing,
    fetch_filing_content,
    fetch_filing_texts,
)
from do_uw.stages.extract.filing_sections import extract_section as _extract_section

# ---------------------------------------------------------------------------
# Fixtures: synthetic filing data
# ---------------------------------------------------------------------------

SAMPLE_10K_HTML = """
<html><body>
<h1>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</h1>
<p>Form 10-K</p>

<b>Table of Contents</b>
<p>Item 1. Business</p>
<p>Item 1A. Risk Factors</p>
<p>Item 7. Management's Discussion and Analysis</p>

<h2>Item 1. Business</h2>
<p>Test Corporation is a leading provider of software solutions
for enterprise customers. The company was founded in 2005 and
operates in the technology sector. Our primary products include
cloud computing platforms, data analytics tools, and cybersecurity
solutions. We serve customers across North America, Europe, and
Asia-Pacific regions. Revenue is generated through subscription
licensing and professional services.</p>
<p>We have approximately 5,000 employees worldwide.</p>
<p>Additional business description text that extends beyond the
minimum threshold for section extraction to ensure we have enough
content to pass the 200 character minimum.</p>

<h2>Item 1A. Risk Factors</h2>
<p>The following risk factors may affect our business...</p>

<h2>Item 7. Management's Discussion and Analysis</h2>
<p>Overview: For fiscal year 2024, revenue increased 25% year-over-year
driven by strong subscription growth. Operating margins expanded
to 22% from 18% in the prior year. Cash flow from operations was
$500 million, up from $380 million. We continue to invest in R&D
at approximately 20% of revenue to drive long-term innovation.</p>
<p>We expect continued growth in fiscal 2025 driven by new product
launches and geographic expansion into emerging markets. Our
backlog of contracted revenue provides visibility into future
performance and reduces risk of revenue shortfall.</p>

<h2>Item 7A. Quantitative and Qualitative Disclosures</h2>
<p>Market risk disclosures...</p>

<h2>Item 9A. Controls and Procedures</h2>
<p>Management's Report on Internal Control Over Financial Reporting:
Management is responsible for establishing and maintaining adequate
internal control over financial reporting. Our independent auditor
PricewaterhouseCoopers LLP has issued an unqualified opinion on
the effectiveness of our internal controls. There were no material
weaknesses identified during the assessment period.</p>

<h2>Item 9B. Other Information</h2>
<p>None.</p>
</body></html>
"""

SAMPLE_EXHIBIT_21_HTML = """
<html><body>
<h1>EXHIBIT 21 - SUBSIDIARIES OF THE REGISTRANT</h1>
<table>
<tr><th>Name of Subsidiary</th><th>Jurisdiction</th></tr>
<tr><td>Test Corp UK Ltd</td><td>England</td></tr>
<tr><td>Test Corp GmbH</td><td>Germany</td></tr>
<tr><td>Test Corp Japan KK</td><td>Japan</td></tr>
<tr><td>Test Cayman Holdings</td><td>Cayman Islands</td></tr>
</table>
</body></html>
"""

SAMPLE_INDEX_JSON: dict[str, Any] = {
    "directory": {
        "item": [
            {"name": "primary-doc.htm", "type": "10-K"},
            {"name": "ex21-1.htm", "type": "EX-21"},
            {"name": "ex23-1.htm", "type": "EX-23"},
        ]
    }
}


def _make_filings_metadata() -> dict[str, Any]:
    """Build synthetic filings metadata matching SEC client output."""
    return {
        "10-K": [
            {
                "accession_number": "0001234567-24-000123",
                "filing_date": "2025-02-15",
                "form_type": "10-K",
                "primary_doc_url": "https://www.sec.gov/Archives/edgar/data/1234567/0001234567-24-000123/primary.htm",
            }
        ],
        "10-Q": [
            {
                "accession_number": "0001234567-24-000456",
                "filing_date": "2024-11-15",
                "form_type": "10-Q",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Tests: HTML stripping
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_removes_tags(self) -> None:
        result = _strip_html("<p>Hello <b>world</b></p>")
        assert "Hello" in result
        assert "world" in result
        assert "<p>" not in result
        assert "<b>" not in result

    def test_decodes_entities(self) -> None:
        result = _strip_html("A &amp; B &lt; C")
        assert "A & B < C" in result

    def test_removes_script_blocks(self) -> None:
        html = "<p>text</p><script>alert('x')</script><p>more</p>"
        result = _strip_html(html)
        assert "alert" not in result
        assert "text" in result
        assert "more" in result


# ---------------------------------------------------------------------------
# Tests: Section extraction
# ---------------------------------------------------------------------------


class TestSectionExtraction:
    def test_extract_item1_from_10k(self) -> None:
        text = _strip_html(SAMPLE_10K_HTML)
        result = _extract_section(
            text,
            [r"(?i)\bitem\s+1[\.\s:]+business\b"],
            [r"(?i)\bitem\s+1a\b"],
        )
        assert "software solutions" in result
        assert "enterprise customers" in result

    def test_extract_item7_from_10k(self) -> None:
        text = _strip_html(SAMPLE_10K_HTML)
        result = _extract_section(
            text,
            [r"(?i)\bitem\s+7[\.\s:]+management"],
            [r"(?i)\bitem\s+7a\b"],
        )
        assert "revenue increased 25%" in result
        assert "Operating margins" in result

    def test_extract_item9a_from_10k(self) -> None:
        text = _strip_html(SAMPLE_10K_HTML)
        result = _extract_section(
            text,
            [r"(?i)\bitem\s+9a[\.\s:]+controls"],
            [r"(?i)\bitem\s+9b\b"],
        )
        assert "PricewaterhouseCoopers" in result
        assert "no material weaknesses" in result

    def test_missing_section_returns_empty(self) -> None:
        result = _extract_section(
            "Some random text without item markers",
            [r"(?i)\bitem\s+99\b"],
            [r"(?i)\bitem\s+100\b"],
        )
        assert result == ""


# ---------------------------------------------------------------------------
# Tests: fetch_filing_texts
# ---------------------------------------------------------------------------


class TestFetchFilingTexts:
    @patch("do_uw.stages.acquire.clients.filing_text.sec_get_text")
    def test_fetches_and_parses_sections(
        self, mock_get_text: Any
    ) -> None:
        mock_get_text.return_value = SAMPLE_10K_HTML
        metadata = _make_filings_metadata()

        result = fetch_filing_texts(metadata, "1234567")

        assert "item1" in result
        assert "software solutions" in result["item1"]
        assert "item7" in result
        assert "revenue increased" in result["item7"]
        mock_get_text.assert_called_once()

    def test_no_annual_filing_returns_empty(self) -> None:
        result = fetch_filing_texts({"10-Q": []}, "1234567")
        assert result == {}

    @patch("do_uw.stages.acquire.clients.filing_text.sec_get_text")
    def test_fetch_failure_returns_empty(
        self, mock_get_text: Any
    ) -> None:
        mock_get_text.side_effect = Exception("Network error")
        metadata = _make_filings_metadata()

        result = fetch_filing_texts(metadata, "1234567")
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: fetch_exhibit_21
# ---------------------------------------------------------------------------


class TestFetchExhibit21:
    @patch("do_uw.stages.acquire.clients.filing_fetcher.sec_get_text")
    @patch("do_uw.stages.acquire.clients.filing_fetcher.sec_get")
    def test_fetches_exhibit_21(
        self, mock_get: Any, mock_get_text: Any
    ) -> None:
        mock_get.return_value = SAMPLE_INDEX_JSON
        mock_get_text.return_value = SAMPLE_EXHIBIT_21_HTML
        metadata = _make_filings_metadata()

        result = fetch_exhibit_21(metadata, "1234567")

        assert "Test Corp UK Ltd" in result
        assert "Cayman Islands" in result

    @patch("do_uw.stages.acquire.clients.filing_fetcher.sec_get")
    def test_no_exhibit_21_in_index(self, mock_get: Any) -> None:
        mock_get.return_value = {
            "directory": {
                "item": [{"name": "primary.htm", "type": "10-K"}]
            }
        }
        metadata = _make_filings_metadata()

        result = fetch_exhibit_21(metadata, "1234567")
        assert result == ""

    def test_no_filings_returns_empty(self) -> None:
        result = fetch_exhibit_21({}, "1234567")
        assert result == ""


# ---------------------------------------------------------------------------
# Tests: _get_latest_filing helper
# ---------------------------------------------------------------------------


class TestGetLatestFiling:
    def test_returns_first_filing(self) -> None:
        metadata = _make_filings_metadata()
        result = _get_latest_filing(metadata, "10-K")
        assert result is not None
        assert result["accession_number"] == "0001234567-24-000123"

    def test_missing_form_type_returns_none(self) -> None:
        result = _get_latest_filing({"10-Q": []}, "10-K")
        assert result is None

    def test_empty_list_returns_none(self) -> None:
        result = _get_latest_filing({"10-K": []}, "10-K")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: fetch_filing_content (cached orchestrator)
# ---------------------------------------------------------------------------


class TestFetchFilingContent:
    @patch("do_uw.stages.acquire.clients.filing_text.fetch_exhibit_21")
    @patch("do_uw.stages.acquire.clients.filing_text.fetch_filing_texts")
    def test_orchestrates_both_fetches(
        self,
        mock_texts: Any,
        mock_ex21: Any,
    ) -> None:
        mock_texts.return_value = {"item1": "business desc"}
        mock_ex21.return_value = "subsidiary list"
        metadata = _make_filings_metadata()

        texts, ex21 = fetch_filing_content(metadata, "1234567")

        assert texts == {"item1": "business desc"}
        assert ex21 == "subsidiary list"
        mock_texts.assert_called_once()
        mock_ex21.assert_called_once()

    def test_no_metadata_returns_empty(self) -> None:
        texts, ex21 = fetch_filing_content({}, "1234567")
        assert texts == {}
        assert ex21 == ""
