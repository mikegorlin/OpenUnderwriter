"""Tests for Phase 4 ACQUIRE stage extensions.

Tests filing_sections.py (section parsing moved to EXTRACT),
sourced.py new helpers (get_filing_documents, get_filing_document_text),
AcquiredData.filing_documents field, and backward compatibility.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.filing_sections import (
    SECTION_DEFS,
    extract_10k_sections,
    extract_section,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_documents,
    get_filing_texts,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------


SAMPLE_10K_TEXT = (
    "Table of Contents "
    "Item 1. Business "
    "Item 1A. Risk Factors "
    "Item 7. Management's Discussion and Analysis "
    ""
    "Item 1. Business "
    "Test Corporation is a leading provider of enterprise software solutions "
    "for global customers. The company was founded in 2005 and operates in "
    "the technology sector. Our primary products include cloud platforms, "
    "analytics tools, and security solutions. We serve customers across "
    "multiple regions worldwide and have 5000 employees. "
    ""
    "Item 1A. Risk Factors "
    "Cybersecurity threats, competition, and regulatory changes pose risks. "
    ""
    "Item 7. Management's Discussion and Analysis "
    "For fiscal 2024, revenue increased 25% year-over-year to $500M. "
    "Operating margins expanded to 22% from 18% in the prior year. "
    "Cash flow from operations was $120M, up from $90M. We continue "
    "investing in research at approximately 20% of revenue. "
    ""
    "Item 7A. Quantitative and Qualitative Disclosures "
    "Market risk disclosures follow. "
    ""
    "Item 9A. Controls and Procedures "
    "Management assessed internal controls and found them effective. "
    "PwC issued an unqualified opinion on internal control effectiveness. "
    "No material weaknesses were identified during the assessment period. "
    ""
    "Item 9B. Other Information "
    "None."
)


def _sourced_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state_with_filing_documents() -> AnalysisState:
    """Build a state with filing_documents populated."""
    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
    )
    profile = CompanyProfile(identity=identity)

    filings: dict[str, Any] = {
        "filing_texts": {"item1": "business description"},
        "filing_documents": {
            "10-K": [
                {
                    "accession": "0001234567-24-000123",
                    "filing_date": "2025-02-15",
                    "form_type": "10-K",
                    "full_text": "Full 10-K annual report text here.",
                },
            ],
            "DEF 14A": [
                {
                    "accession": "0001234567-24-000789",
                    "filing_date": "2025-04-01",
                    "form_type": "DEF 14A",
                    "full_text": "Proxy statement with board info.",
                },
            ],
        },
    }

    acquired = AcquiredData(
        filings=filings,
        filing_documents={
            "10-K": [
                {
                    "accession": "0001234567-24-000123",
                    "filing_date": "2025-02-15",
                    "form_type": "10-K",
                    "full_text": "Full 10-K annual report text here.",
                },
            ],
            "DEF 14A": [
                {
                    "accession": "0001234567-24-000789",
                    "filing_date": "2025-04-01",
                    "form_type": "DEF 14A",
                    "full_text": "Proxy statement with board info.",
                },
            ],
        },
    )

    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=acquired,
    )


# ---------------------------------------------------------------------------
# Tests: filing_sections.py
# ---------------------------------------------------------------------------


class TestExtractSection:
    def test_extracts_item1(self) -> None:
        result = extract_section(
            SAMPLE_10K_TEXT,
            [r"(?i)\bitem\s+1[\.\s:]+business\b"],
            [r"(?i)\bitem\s+1a\b"],
        )
        assert "enterprise software" in result
        assert len(result) > 200

    def test_extracts_item7(self) -> None:
        result = extract_section(
            SAMPLE_10K_TEXT,
            [
                r"(?i)\bitem\s+7[\.\s:]+"
                r"management.s\s+discussion\s+and\s+analysis\b"
            ],
            [r"(?i)\bitem\s+7a\b"],
        )
        assert "revenue increased 25%" in result

    def test_extracts_item9a(self) -> None:
        result = extract_section(
            SAMPLE_10K_TEXT,
            [r"(?i)\bitem\s+9a[\.\s:]+controls"],
            [r"(?i)\bitem\s+9b\b"],
        )
        assert "PwC" in result
        assert "no material weaknesses" in result.lower()

    def test_missing_section_returns_empty(self) -> None:
        result = extract_section(
            "Random text without markers",
            [r"(?i)\bitem\s+99\b"],
            [r"(?i)\bitem\s+100\b"],
        )
        assert result == ""


class TestExtract10kSections:
    def test_returns_all_sections_with_aliases(self) -> None:
        result = extract_10k_sections(SAMPLE_10K_TEXT)

        # Should have both prefixed and short alias keys
        assert "10-K_item1" in result
        assert "item1" in result
        assert "10-K_item7" in result
        assert "item7" in result
        assert "10-K_item9a" in result
        assert "item9a" in result

    def test_prefixed_and_alias_same_content(self) -> None:
        result = extract_10k_sections(SAMPLE_10K_TEXT)
        assert result["10-K_item1"] == result["item1"]
        assert result["10-K_item7"] == result["item7"]

    def test_empty_text_returns_empty(self) -> None:
        result = extract_10k_sections("")
        assert result == {}


class TestSectionDefs:
    def test_section_defs_has_six_sections(self) -> None:
        assert len(SECTION_DEFS) == 6

    def test_section_names(self) -> None:
        names = [d[0] for d in SECTION_DEFS]
        assert "item1" in names
        assert "item1a" in names
        assert "item3" in names
        assert "item7" in names
        assert "item8" in names
        assert "item9a" in names


# ---------------------------------------------------------------------------
# Tests: AcquiredData.filing_documents field
# ---------------------------------------------------------------------------


class TestAcquiredDataFilingDocuments:
    def test_default_empty(self) -> None:
        ad = AcquiredData()
        assert ad.filing_documents == {}
        assert isinstance(ad.filing_documents, dict)

    def test_stores_filing_documents(self) -> None:
        docs: dict[str, list[dict[str, str]]] = {
            "10-K": [
                {
                    "accession": "acc-1",
                    "filing_date": "2025-01-01",
                    "form_type": "10-K",
                    "full_text": "content",
                }
            ]
        }
        ad = AcquiredData(filing_documents=docs)
        assert "10-K" in ad.filing_documents
        assert len(ad.filing_documents["10-K"]) == 1


# ---------------------------------------------------------------------------
# Tests: sourced.py helpers
# ---------------------------------------------------------------------------


class TestGetFilingDocuments:
    def test_returns_docs_from_state(self) -> None:
        state = _make_state_with_filing_documents()
        docs = get_filing_documents(state)
        assert "10-K" in docs
        assert "DEF 14A" in docs

    def test_empty_state_returns_empty(self) -> None:
        state = AnalysisState(ticker="TEST")
        docs = get_filing_documents(state)
        assert docs == {}


class TestGetFilingDocumentText:
    def test_returns_full_text(self) -> None:
        state = _make_state_with_filing_documents()
        text = get_filing_document_text(state, "10-K", 0)
        assert "Full 10-K annual report" in text

    def test_returns_proxy_text(self) -> None:
        state = _make_state_with_filing_documents()
        text = get_filing_document_text(state, "DEF 14A", 0)
        assert "Proxy statement" in text

    def test_missing_type_returns_empty(self) -> None:
        state = _make_state_with_filing_documents()
        text = get_filing_document_text(state, "S-1", 0)
        assert text == ""

    def test_out_of_range_index_returns_empty(self) -> None:
        state = _make_state_with_filing_documents()
        text = get_filing_document_text(state, "10-K", 99)
        assert text == ""


# ---------------------------------------------------------------------------
# Tests: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Ensure existing Phase 3 imports still work."""

    def test_get_filing_texts_still_works(self) -> None:
        filings: dict[str, Any] = {
            "filing_texts": {
                "10-K_item1": "business text",
                "item1": "business text",
            }
        }
        result = get_filing_texts(filings)
        assert result["item1"] == "business text"

    def test_filing_text_public_api_works(self) -> None:
        """filing_text.py public API (fetch_filing_texts, etc.) works."""
        from do_uw.stages.acquire.clients.filing_text import (
            _get_latest_filing,
            fetch_filing_content,
            fetch_filing_texts,
        )
        assert callable(fetch_filing_texts)
        assert callable(fetch_filing_content)
        assert callable(_get_latest_filing)

    def test_filing_fetcher_strip_html_works(self) -> None:
        """strip_html from filing_fetcher.py works."""
        from do_uw.stages.acquire.clients.filing_fetcher import strip_html

        result = strip_html("<p>Hello &amp; world</p>")
        assert "Hello & world" in result

    def test_filing_sections_extract_works(self) -> None:
        """extract_section from filing_sections.py works."""
        from do_uw.stages.extract.filing_sections import extract_section

        assert callable(extract_section)
