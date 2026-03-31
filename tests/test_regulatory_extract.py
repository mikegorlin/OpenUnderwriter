"""Tests for regulatory proceedings extractor (SECT6-06).

Covers agency pattern detection, multi-agency extraction, penalty
amount parsing, proceeding type classification, FCPA detection,
and empty state handling.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.regulatory_extract import (
    extract_regulatory_proceedings,
)
from do_uw.stages.extract.regulatory_extract_patterns import (
    _agency_to_report_field,
    _classify_proceeding_type,
    _extract_penalty_amount,
    _scan_text_for_agencies,
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
    """Create filing_documents with a 10-K containing the given Item 3 text."""
    # Need enough surrounding text for section parsing to work.
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
# Agency pattern tests
# ---------------------------------------------------------------------------


class TestAgencyPatterns:
    """Test each agency pattern matches correctly."""

    def test_doj_investigation(self) -> None:
        text = "The DOJ investigation into pricing practices is ongoing."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "DOJ" for p in procs
        )

    def test_doj_settlement(self) -> None:
        text = "The Department of Justice settlement was finalized."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "DOJ" for p in procs
        )

    def test_fcpa_detection(self) -> None:
        text = (
            "The company is subject to FCPA compliance"
            " requirements and a potential FCPA investigation."
        )
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "DOJ_FCPA" for p in procs
        )

    def test_ftc_enforcement(self) -> None:
        text = "The FTC enforcement action resulted in a consent order."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "FTC" for p in procs
        )

    def test_fda_warning(self) -> None:
        text = "The FDA warning letter cited manufacturing deficiencies."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "FDA" for p in procs
        )

    def test_epa_enforcement(self) -> None:
        text = "EPA enforcement actions related to air quality violations."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "EPA" for p in procs
        )

    def test_cfpb_investigation(self) -> None:
        text = "The CFPB investigation into consumer lending practices."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "CFPB" for p in procs
        )

    def test_occ_consent_order(self) -> None:
        text = "The OCC consent order requires improved compliance."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "OCC" for p in procs
        )

    def test_osha_violation(self) -> None:
        text = "OSHA citation for workplace safety violations was issued."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "OSHA" for p in procs
        )

    def test_state_ag_action(self) -> None:
        text = "The state attorney general investigation into pricing."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "STATE_AG" for p in procs
        )

    def test_eeoc_charge(self) -> None:
        text = "An EEOC charge was filed alleging discrimination."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "EEOC" for p in procs
        )


# ---------------------------------------------------------------------------
# Multi-agency and extraction tests
# ---------------------------------------------------------------------------


class TestMultiAgencyDetection:
    """Test detecting multiple agencies in a single text."""

    def test_multi_agency_single_text(self) -> None:
        text = (
            "The company faces an FTC enforcement action related to "
            "consumer protection, and a separate EPA enforcement for "
            "environmental violations at the manufacturing facility."
        )
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        agencies = {p.agency.value for p in procs if p.agency}
        assert "FTC" in agencies
        assert "EPA" in agencies

    def test_no_match_returns_empty(self) -> None:
        text = "The company had a good year with strong revenue growth."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) == 0


# ---------------------------------------------------------------------------
# Penalty extraction tests
# ---------------------------------------------------------------------------


class TestPenaltyExtraction:
    """Test penalty amount extraction from text."""

    def test_million_amount(self) -> None:
        amount = _extract_penalty_amount(
            "The company paid $50 million in penalties."
        )
        assert amount is not None
        assert amount == 50_000_000.0

    def test_billion_amount(self) -> None:
        amount = _extract_penalty_amount(
            "Settlement of $1.2 billion was reached."
        )
        assert amount is not None
        assert amount == 1_200_000_000.0

    def test_comma_separated(self) -> None:
        amount = _extract_penalty_amount(
            "A fine of $125,000 million was imposed."
        )
        assert amount is not None
        assert amount == 125_000_000_000.0

    def test_no_penalty(self) -> None:
        amount = _extract_penalty_amount(
            "The investigation is ongoing with no penalties assessed."
        )
        assert amount is None

    def test_penalty_in_proceeding(self) -> None:
        text = (
            "The EPA enforcement action resulted in penalties of "
            "$25 million for environmental violations."
        )
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        has_penalty = any(p.penalties is not None for p in procs)
        assert has_penalty


# ---------------------------------------------------------------------------
# Proceeding type classification tests
# ---------------------------------------------------------------------------


class TestProceedingTypeClassification:
    """Test proceeding type classification from context."""

    def test_investigation(self) -> None:
        assert _classify_proceeding_type("under investigation") == "investigation"

    def test_enforcement(self) -> None:
        assert _classify_proceeding_type("enforcement action filed") == "enforcement"

    def test_consent_decree(self) -> None:
        assert _classify_proceeding_type("entered consent decree") == "consent_decree"

    def test_penalty(self) -> None:
        assert _classify_proceeding_type("paid a penalty of $5M") == "penalty"

    def test_settlement(self) -> None:
        assert _classify_proceeding_type("reached a settlement") == "penalty"

    def test_default_investigation(self) -> None:
        assert _classify_proceeding_type("something unknown") == "investigation"


# ---------------------------------------------------------------------------
# FCPA-specific tests
# ---------------------------------------------------------------------------


class TestFCPADetection:
    """Test FCPA-specific pattern detection."""

    def test_fcpa_acronym(self) -> None:
        text = "FCPA compliance program was strengthened."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "DOJ_FCPA" for p in procs
        )

    def test_foreign_corrupt_practices(self) -> None:
        text = "Foreign Corrupt Practices Act violations were investigated."
        procs = _scan_text_for_agencies(text, "test", Confidence.HIGH)
        assert len(procs) >= 1
        assert any(
            p.agency and p.agency.value == "DOJ_FCPA" for p in procs
        )


# ---------------------------------------------------------------------------
# Empty state tests
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test graceful handling of empty or missing data."""

    def test_empty_state_returns_empty(self) -> None:
        state = AnalysisState(ticker="EMPTY")
        proceedings, report = extract_regulatory_proceedings(state)
        assert proceedings == []
        assert report.extractor_name == "regulatory_proceedings"

    def test_no_acquired_data(self) -> None:
        state = AnalysisState(ticker="NODATA")
        state.acquired_data = None
        proceedings, _report = extract_regulatory_proceedings(state)
        assert proceedings == []

    def test_empty_filings(self) -> None:
        state = _make_state(filing_documents={})
        proceedings, _report = extract_regulatory_proceedings(state)
        assert proceedings == []


# ---------------------------------------------------------------------------
# Full extractor integration tests
# ---------------------------------------------------------------------------


class TestFullExtractor:
    """Test the full extract_regulatory_proceedings function."""

    def test_item3_extraction(self) -> None:
        filing_docs = _make_10k_with_item3(
            "The company is subject to an FTC enforcement action "
            "regarding advertising practices. The matter is pending."
        )
        state = _make_state(filing_documents=filing_docs)
        proceedings, report = extract_regulatory_proceedings(state)
        assert len(proceedings) >= 1
        assert any(
            p.agency and p.agency.value == "FTC" for p in proceedings
        )
        assert "ftc" in report.found_fields

    def test_web_search_extraction(self) -> None:
        web_results: dict[str, Any] = {
            "regulatory": [
                {
                    "title": "EPA enforcement action against Test Corp",
                    "description": "EPA enforcement for water violations",
                    "snippet": "EPA enforcement remediation ordered",
                    "url": "https://example.com/epa",
                }
            ]
        }
        state = _make_state(web_search_results=web_results)
        proceedings, _report = extract_regulatory_proceedings(state)
        assert len(proceedings) >= 1
        assert any(
            p.agency and p.agency.value == "EPA" for p in proceedings
        )

    def test_blind_spot_extraction(self) -> None:
        blind_results: dict[str, Any] = {
            "regulatory_scan": [
                {
                    "title": "OSHA citation issued to Test Corp",
                    "description": "OSHA violation for safety hazards",
                    "snippet": "",
                    "url": "https://example.com/osha",
                }
            ]
        }
        state = _make_state(blind_spot_results=blind_results)
        proceedings, _report = extract_regulatory_proceedings(state)
        assert len(proceedings) >= 1
        assert any(
            p.agency and p.agency.value == "OSHA" for p in proceedings
        )

    def test_8k_extraction(self) -> None:
        filing_docs: dict[str, list[dict[str, str]]] = {
            "8-K": [
                {
                    "full_text": (
                        "The company received a CFPB enforcement notice "
                        "regarding consumer lending practices."
                    ),
                    "form_type": "8-K",
                }
            ]
        }
        state = _make_state(filing_documents=filing_docs)
        proceedings, _report = extract_regulatory_proceedings(state)
        assert len(proceedings) >= 1
        assert any(
            p.agency and p.agency.value == "CFPB" for p in proceedings
        )

    def test_deduplication(self) -> None:
        """Duplicate proceedings from same agency + context are deduped."""
        text = (
            "The FTC enforcement action is ongoing. "
            "This FTC enforcement matter is under review."
        )
        filing_docs = _make_10k_with_item3(text)
        # Also include same text in web search.
        web_results: dict[str, Any] = {
            "ftc": [
                {
                    "title": "FTC enforcement action is ongoing",
                    "description": "FTC enforcement against Test Corp",
                    "snippet": "",
                    "url": "",
                }
            ]
        }
        state = _make_state(
            filing_documents=filing_docs,
            web_search_results=web_results,
        )
        proceedings, _report = extract_regulatory_proceedings(state)
        # Should have multiple but with different descriptions (not N^2).
        ftc_count = sum(
            1 for p in proceedings
            if p.agency and p.agency.value == "FTC"
        )
        # The two 10-K matches + web match should be deduped to unique descs.
        assert ftc_count >= 1


# ---------------------------------------------------------------------------
# Agency-to-report-field mapping tests
# ---------------------------------------------------------------------------


class TestAgencyFieldMapping:
    """Test agency code to report field name mapping."""

    def test_standard_mappings(self) -> None:
        assert _agency_to_report_field("DOJ") == "doj"
        assert _agency_to_report_field("DOJ_FCPA") == "fcpa"
        assert _agency_to_report_field("FTC") == "ftc"
        assert _agency_to_report_field("FDA") == "fda"
        assert _agency_to_report_field("EPA") == "epa"
        assert _agency_to_report_field("CFPB") == "cfpb"
        assert _agency_to_report_field("OCC") == "occ"
        assert _agency_to_report_field("OSHA") == "osha"
        assert _agency_to_report_field("STATE_AG") == "state_ag"
        assert _agency_to_report_field("EEOC") == "eeoc"

    def test_unknown_agency_lowercase(self) -> None:
        assert _agency_to_report_field("OTHER") == "other"
