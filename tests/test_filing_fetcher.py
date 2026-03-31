"""Tests for filing_fetcher.py -- full document fetching and caching."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from do_uw.stages.acquire.clients.filing_fetcher import (
    fetch_all_filing_documents,
    fetch_exhibit_21,
    fetch_filing_document,
    strip_html,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>
<h1>Annual Report</h1>
<p>This is the full filing content for Test Corporation.</p>
<script>var x = 1;</script>
<style>.class { color: red; }</style>
<p>More content &amp; entities &lt;here&gt;.</p>
</body></html>
"""

SAMPLE_INDEX_JSON: dict[str, Any] = {
    "directory": {
        "item": [
            {"name": "primary-doc.htm", "type": "10-K"},
            {"name": "ex21-1.htm", "type": "EX-21"},
        ]
    }
}


def _make_filings_metadata() -> dict[str, Any]:
    """Build synthetic filings metadata for testing."""
    return {
        "10-K": [
            {
                "accession_number": "0001234567-24-000123",
                "filing_date": "2025-02-15",
                "form_type": "10-K",
                "primary_doc_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    "1234567/000123456724000123/annual.htm"
                ),
            },
            {
                "accession_number": "0001234567-23-000456",
                "filing_date": "2024-02-15",
                "form_type": "10-K",
                "primary_doc_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    "1234567/000123456723000456/annual.htm"
                ),
            },
        ],
        "DEF 14A": [
            {
                "accession_number": "0001234567-24-000789",
                "filing_date": "2025-04-01",
                "form_type": "DEF 14A",
                "primary_doc_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    "1234567/000123456724000789/proxy.htm"
                ),
            },
        ],
        "company_facts": {"facts": {}},  # Should be skipped
    }


# ---------------------------------------------------------------------------
# Tests: strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_removes_tags(self) -> None:
        result = strip_html("<p>Hello <b>world</b></p>")
        assert "Hello" in result
        assert "world" in result
        assert "<p>" not in result

    def test_decodes_entities(self) -> None:
        result = strip_html("A &amp; B &lt; C")
        assert "A & B < C" in result

    def test_removes_script_and_style(self) -> None:
        result = strip_html(SAMPLE_HTML)
        assert "var x" not in result
        assert "color: red" not in result
        assert "full filing content" in result

    def test_normalizes_whitespace(self) -> None:
        result = strip_html("<p>  lots   of   spaces  </p>")
        assert "  " not in result


# ---------------------------------------------------------------------------
# Tests: fetch_filing_document
# ---------------------------------------------------------------------------


class TestFetchFilingDocument:
    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_fetches_and_strips_html(
        self, mock_get_text: MagicMock
    ) -> None:
        mock_get_text.return_value = SAMPLE_HTML
        doc = fetch_filing_document(
            primary_doc_url="https://sec.gov/doc.htm",
            accession="0001234567-24-000123",
            form_type="10-K",
            filing_date="2025-02-15",
        )
        assert doc is not None
        assert doc["accession"] == "0001234567-24-000123"
        assert doc["form_type"] == "10-K"
        assert doc["filing_date"] == "2025-02-15"
        assert "full filing content" in doc["full_text"]
        assert "<html>" not in doc["full_text"]

    def test_empty_url_returns_none(self) -> None:
        doc = fetch_filing_document(
            primary_doc_url="",
            accession="acc",
            form_type="10-K",
            filing_date="2025-01-01",
        )
        assert doc is None

    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_fetch_failure_returns_none(
        self, mock_get_text: MagicMock
    ) -> None:
        mock_get_text.side_effect = Exception("Network error")
        doc = fetch_filing_document(
            primary_doc_url="https://sec.gov/doc.htm",
            accession="acc",
            form_type="10-K",
            filing_date="2025-01-01",
        )
        assert doc is None

    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_caches_result(self, mock_get_text: MagicMock) -> None:
        mock_get_text.return_value = SAMPLE_HTML
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        doc = fetch_filing_document(
            primary_doc_url="https://sec.gov/doc.htm",
            accession="0001234567-24-000123",
            form_type="10-K",
            filing_date="2025-02-15",
            cache=mock_cache,
        )
        assert doc is not None
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert "sec:filing_doc:0001234567-24-000123" in call_args.args

    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_cache_hit_skips_fetch(
        self, mock_get_text: MagicMock
    ) -> None:
        mock_cache = MagicMock()
        mock_cache.get.return_value = {
            "accession": "acc-123",
            "filing_date": "2025-01-01",
            "form_type": "10-K",
            "full_text": "cached text",
        }
        doc = fetch_filing_document(
            primary_doc_url="https://sec.gov/doc.htm",
            accession="acc-123",
            form_type="10-K",
            filing_date="2025-01-01",
            cache=mock_cache,
        )
        assert doc is not None
        assert doc["full_text"] == "cached text"
        mock_get_text.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: fetch_all_filing_documents
# ---------------------------------------------------------------------------


class TestFetchAllFilingDocuments:
    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_fetches_all_types(
        self, mock_get_text: MagicMock
    ) -> None:
        mock_get_text.return_value = SAMPLE_HTML
        metadata = _make_filings_metadata()

        result = fetch_all_filing_documents(metadata, "1234567")

        assert "10-K" in result
        assert len(result["10-K"]) == 2
        assert "DEF 14A" in result
        assert len(result["DEF 14A"]) == 1
        # company_facts should not appear
        assert "company_facts" not in result

    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    def test_skips_filings_without_url(
        self, mock_get_text: MagicMock
    ) -> None:
        mock_get_text.return_value = SAMPLE_HTML
        metadata: dict[str, Any] = {
            "10-K": [{"accession_number": "acc", "filing_date": "2025-01-01"}],
        }
        result = fetch_all_filing_documents(metadata, "1234567")
        # Filing without primary_doc_url should be skipped
        assert result.get("10-K", []) == []

    def test_empty_metadata_returns_empty(self) -> None:
        result = fetch_all_filing_documents({}, "1234567")
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: fetch_exhibit_21
# ---------------------------------------------------------------------------


class TestFetchExhibit21:
    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get"
    )
    def test_fetches_exhibit_21(
        self, mock_get: MagicMock, mock_get_text: MagicMock
    ) -> None:
        mock_get.return_value = SAMPLE_INDEX_JSON
        mock_get_text.return_value = (
            "<html><body>Test Corp UK Ltd - England</body></html>"
        )
        metadata = _make_filings_metadata()

        result = fetch_exhibit_21(metadata, "1234567")
        assert "Test Corp UK Ltd" in result
        assert "England" in result

    def test_no_filings_returns_empty(self) -> None:
        result = fetch_exhibit_21({}, "1234567")
        assert result == ""

    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get_text"
    )
    @patch(
        "do_uw.stages.acquire.clients.filing_fetcher.sec_get"
    )
    def test_caches_result(
        self, mock_get: MagicMock, mock_get_text: MagicMock
    ) -> None:
        mock_get.return_value = SAMPLE_INDEX_JSON
        mock_get_text.return_value = "<html><body>subs</body></html>"
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        metadata = _make_filings_metadata()

        result = fetch_exhibit_21(metadata, "1234567", cache=mock_cache)
        assert result != ""
        mock_cache.set.assert_called_once()
