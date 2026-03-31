"""Tests for deal litigation extractor (SECT6-07).

Covers M&A deal pattern detection, settlement extraction,
court detection, empty state handling, and deduplication.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.deal_litigation import (
    _detect_court,
    _extract_deal_name,
    _extract_settlement_amount,
    _scan_text_for_deal_litigation,
    extract_deal_litigation,
)
from do_uw.stages.extract.sourced import now

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_state(
    ticker: str = "TEST",
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    web_search_results: dict[str, Any] | None = None,
    blind_spot_results: dict[str, Any] | None = None,
    company_name: str = "Test Corp",
) -> AnalysisState:
    """Build an AnalysisState with the specified acquired data."""
    state = AnalysisState(ticker=ticker)
    state.acquired_data = AcquiredData(
        filing_documents=filing_documents or {},
        web_search_results=web_search_results or {},
        blind_spot_results=blind_spot_results or {},
    )
    identity = CompanyIdentity(ticker=ticker)
    identity.legal_name = SourcedValue[str](
        value=company_name,
        source="test",
        confidence=Confidence.HIGH,
        as_of=now(),
    )
    state.company = CompanyProfile(identity=identity)
    return state


def _make_10k_with_item3(item3_text: str) -> dict[str, list[dict[str, str]]]:
    """Create filing_documents with a 10-K containing the given Item 3."""
    full_text = (
        "Item 1. Business\n"
        "The company operates in multiple segments.\n" * 20
        + "\nItem 1A. Risk Factors\n"
        + "Various risks may affect the company.\n" * 20
        + "\nItem 3. Legal Proceedings\n"
        + item3_text
        + "\n\nItem 4. Mine Safety Disclosures\n"
        + "No mine safety disclosures applicable.\n"
    )
    return {"10-K": [{"full_text": full_text, "form_type": "10-K"}]}


# ---------------------------------------------------------------------------
# Deal pattern tests
# ---------------------------------------------------------------------------


class TestDealPatterns:
    """Test each deal litigation pattern matches correctly."""

    def test_merger_objection(self) -> None:
        text = "Shareholders filed a merger objection lawsuit."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "merger_objection"
            for c in cases
        )

    def test_merger_challenge(self) -> None:
        text = "The merger challenge was filed in Delaware Chancery."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "merger_objection"
            for c in cases
        )

    def test_appraisal_action(self) -> None:
        text = "Shareholders filed an appraisal action seeking fair value."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "appraisal"
            for c in cases
        )

    def test_section_262_appraisal(self) -> None:
        text = "A Section 262 proceeding was commenced for the deal."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "appraisal"
            for c in cases
        )

    def test_disclosure_only_settlement(self) -> None:
        text = "The case was resolved through a disclosure-only settlement."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "disclosure_only"
            for c in cases
        )

    def test_revlon_claim(self) -> None:
        text = "Plaintiffs alleged a Revlon duty breach in the sale."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "revlon"
            for c in cases
        )

    def test_fiduciary_duty_merger(self) -> None:
        text = (
            "A fiduciary duty breach claim was filed in connection "
            "with the pending merger transaction."
        )
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) >= 1
        assert any(
            c.litigation_type and c.litigation_type.value == "fiduciary"
            for c in cases
        )


# ---------------------------------------------------------------------------
# Settlement extraction tests
# ---------------------------------------------------------------------------


class TestSettlementExtraction:
    """Test settlement amount extraction from text."""

    def test_million_settlement(self) -> None:
        amount = _extract_settlement_amount(
            "The merger objection was settled for $35 million."
        )
        assert amount is not None
        assert amount == 35_000_000.0

    def test_billion_settlement(self) -> None:
        amount = _extract_settlement_amount(
            "Settlement reached at $2.5 billion."
        )
        assert amount is not None
        assert amount == 2_500_000_000.0

    def test_no_settlement(self) -> None:
        amount = _extract_settlement_amount(
            "The case is still pending with no resolution."
        )
        assert amount is None


# ---------------------------------------------------------------------------
# Court detection tests
# ---------------------------------------------------------------------------


class TestCourtDetection:
    """Test court name detection from text."""

    def test_delaware_chancery(self) -> None:
        court = _detect_court(
            "Filed in the Delaware Court of Chancery."
        )
        assert court == "Delaware Chancery"

    def test_sdny(self) -> None:
        court = _detect_court("Case pending in S.D.N.Y.")
        assert court == "S.D.N.Y."

    def test_no_court(self) -> None:
        court = _detect_court("The matter is under review.")
        assert court is None


# ---------------------------------------------------------------------------
# Deal name extraction tests
# ---------------------------------------------------------------------------


class TestDealNameExtraction:
    """Test deal name extraction from context."""

    def test_merger_with(self) -> None:
        name = _extract_deal_name(
            "The merger with Acme Industries, for $10 billion."
        )
        assert name is not None
        assert "Acme" in name

    def test_acquisition_of(self) -> None:
        name = _extract_deal_name(
            "The acquisition of Global Corp in 2024."
        )
        assert name is not None
        assert "Global" in name

    def test_no_deal_name(self) -> None:
        name = _extract_deal_name("The case is still pending.")
        assert name is None


# ---------------------------------------------------------------------------
# Empty state tests
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test graceful handling of empty or missing data."""

    def test_empty_state_returns_empty(self) -> None:
        state = AnalysisState(ticker="EMPTY")
        cases, report = extract_deal_litigation(state)
        assert cases == []
        assert report.extractor_name == "deal_litigation"

    def test_no_acquired_data(self) -> None:
        state = AnalysisState(ticker="NODATA")
        state.acquired_data = None
        cases, _report = extract_deal_litigation(state)
        assert cases == []

    def test_empty_filings(self) -> None:
        state = _make_state(filing_documents={})
        cases, _report = extract_deal_litigation(state)
        assert cases == []


# ---------------------------------------------------------------------------
# Full extractor integration tests
# ---------------------------------------------------------------------------


class TestFullExtractor:
    """Test the full extract_deal_litigation function."""

    def test_item3_extraction(self) -> None:
        filing_docs = _make_10k_with_item3(
            "The company faces a merger objection lawsuit "
            "in Delaware Chancery Court related to the proposed "
            "acquisition of Widget Corp, for $50 million. "
            "The plaintiffs allege that the board of directors "
            "failed to adequately consider alternative proposals "
            "and did not negotiate at arm's length. " * 2
        )
        state = _make_state(filing_documents=filing_docs)
        cases, report = extract_deal_litigation(state)
        assert len(cases) >= 1
        assert "merger_objection" in report.found_fields

    def test_web_search_extraction(self) -> None:
        web_results: dict[str, Any] = {
            "deal": [
                {
                    "title": "Appraisal action filed against Test Corp",
                    "description": "Section 262 proceeding filed",
                    "snippet": "appraisal proceeding in Delaware",
                    "url": "https://example.com",
                }
            ]
        }
        state = _make_state(web_search_results=web_results)
        cases, _report = extract_deal_litigation(state)
        assert len(cases) >= 1

    def test_8k_extraction(self) -> None:
        filing_docs: dict[str, list[dict[str, str]]] = {
            "8-K": [
                {
                    "full_text": (
                        "A disclosure-only settlement was reached "
                        "in connection with the proposed transaction."
                    ),
                    "form_type": "8-K",
                }
            ]
        }
        state = _make_state(filing_documents=filing_docs)
        cases, _report = extract_deal_litigation(state)
        assert len(cases) >= 1

    def test_settlement_in_full_extraction(self) -> None:
        filing_docs = _make_10k_with_item3(
            "The merger objection lawsuit was settled for $25 million. "
            "No further payments are expected. The settlement resolved "
            "all claims by plaintiffs in connection with the proposed "
            "transaction. The board determined the settlement to be "
            "in the best interest of all shareholders. " * 2
        )
        state = _make_state(filing_documents=filing_docs)
        cases, report = extract_deal_litigation(state)
        assert len(cases) >= 1
        has_settlement = any(
            c.settlement_amount is not None for c in cases
        )
        assert has_settlement
        assert "settlement_amount" in report.found_fields

    def test_no_match_returns_empty(self) -> None:
        text = "The company had strong revenue growth this quarter."
        cases = _scan_text_for_deal_litigation(text, "test", Confidence.HIGH)
        assert len(cases) == 0
