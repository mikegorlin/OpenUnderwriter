"""Tests for workforce/product/environmental extractor (SECT6-08).

Covers 8 claim categories, multi-category detection, whistleblower
indicator extraction, cybersecurity detection, and empty state handling.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sourced import now
from do_uw.stages.extract.workforce_product import (
    _create_whistleblower_indicator,
    _scan_text_for_categories,
    extract_workforce_product_environmental,
)

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
# Category pattern tests
# ---------------------------------------------------------------------------


class TestCategoryPatterns:
    """Test each category's patterns match correctly."""

    def test_employment_litigation(self) -> None:
        text = "The employment litigation against the company is pending."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "employment_matters" in results

    def test_wage_hour(self) -> None:
        text = "A wage and hour class action was certified."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "employment_matters" in results

    def test_flsa(self) -> None:
        text = "FLSA claims were filed regarding overtime."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "employment_matters" in results

    def test_discrimination(self) -> None:
        text = "A discrimination complaint was filed."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "employment_matters" in results

    def test_eeoc_charge(self) -> None:
        text = "An EEOC charge was filed alleging workplace bias."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "eeoc_charges" in results

    def test_whistleblower_complaint(self) -> None:
        text = "A whistleblower complaint was filed with the SEC."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "whistleblower_complaints" in results

    def test_qui_tam(self) -> None:
        text = "A qui tam action under the False Claims Act was filed."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "whistleblower_complaints" in results

    def test_sec_whistleblower(self) -> None:
        text = "The SEC whistleblower award program was referenced."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "whistleblower_complaints" in results

    def test_dodd_frank_whistleblower(self) -> None:
        text = "Dodd-Frank whistleblower protections apply."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "whistleblower_complaints" in results

    def test_warn_act(self) -> None:
        text = "A WARN Act notice was filed for the facility closure."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "warn_notices" in results

    def test_mass_layoff(self) -> None:
        text = "The mass layoff affected 500 workers."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "warn_notices" in results

    def test_product_recall(self) -> None:
        text = "A product recall was issued for defective units."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "product_recalls" in results

    def test_cpsc(self) -> None:
        text = "CPSC investigated the consumer product defect."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "product_recalls" in results

    def test_mass_tort(self) -> None:
        text = "The company faces mass tort litigation in multiple states."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "mass_tort_exposure" in results

    def test_mdl(self) -> None:
        text = "The multidistrict litigation was consolidated."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "mass_tort_exposure" in results

    def test_personal_injury(self) -> None:
        text = "Personal injury claims were filed."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "mass_tort_exposure" in results

    def test_environmental_enforcement(self) -> None:
        text = "EPA enforcement action for water quality violations."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "environmental_actions" in results

    def test_superfund(self) -> None:
        text = "The Superfund site remediation is ongoing."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "environmental_actions" in results

    def test_cercla(self) -> None:
        text = "CERCLA liability was assessed for the contaminated site."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "environmental_actions" in results

    def test_climate_litigation(self) -> None:
        text = "Climate-related litigation was filed by state AGs."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "environmental_actions" in results

    def test_data_breach(self) -> None:
        text = "A data breach exposed customer information."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "cybersecurity_incidents" in results

    def test_gdpr_violation(self) -> None:
        text = "A GDPR violation resulted in a regulatory fine."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "cybersecurity_incidents" in results

    def test_ransomware(self) -> None:
        text = "A ransomware attack disrupted operations."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "cybersecurity_incidents" in results

    def test_ccpa_privacy(self) -> None:
        text = "The CCPA penalty was assessed for privacy violations."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "cybersecurity_incidents" in results


# ---------------------------------------------------------------------------
# Multi-category detection tests
# ---------------------------------------------------------------------------


class TestMultiCategoryDetection:
    """Test detecting multiple categories in a single text."""

    def test_multi_category_single_text(self) -> None:
        text = (
            "The company faces employment litigation for wage and hour "
            "violations. Additionally, a data breach exposed customer "
            "records, and a product recall was issued for defective units."
        )
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert "employment_matters" in results
        assert "cybersecurity_incidents" in results
        assert "product_recalls" in results

    def test_no_match_returns_empty(self) -> None:
        text = "The company reported strong quarterly earnings."
        results = _scan_text_for_categories(text, "test", Confidence.HIGH)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Whistleblower indicator tests
# ---------------------------------------------------------------------------


class TestWhistleblowerIndicators:
    """Test whistleblower indicator extraction."""

    def test_whistleblower_indicator_creation(self) -> None:
        indicator = _create_whistleblower_indicator(
            "whistleblower",
            "Whistleblower complaint filed",
            "test",
            Confidence.HIGH,
        )
        assert indicator.indicator_type is not None
        assert indicator.indicator_type.value == "internal"
        assert indicator.description is not None

    def test_qui_tam_indicator(self) -> None:
        indicator = _create_whistleblower_indicator(
            "qui_tam",
            "False Claims Act case filed",
            "test",
            Confidence.HIGH,
        )
        assert indicator.indicator_type is not None
        assert indicator.indicator_type.value == "qui_tam"

    def test_sec_whistleblower_indicator(self) -> None:
        indicator = _create_whistleblower_indicator(
            "sec_whistleblower",
            "SEC whistleblower award",
            "test",
            Confidence.HIGH,
        )
        assert indicator.indicator_type is not None
        assert indicator.indicator_type.value == "sec_whistleblower"

    def test_full_extractor_returns_whistleblowers(self) -> None:
        filing_docs = _make_10k_with_item3(
            "A whistleblower complaint was filed against the company "
            "alleging financial irregularities. A separate qui tam "
            "action under the False Claims Act is pending."
        )
        state = _make_state(filing_documents=filing_docs)
        wpe, whistleblowers, report = (
            extract_workforce_product_environmental(state)
        )
        assert len(whistleblowers) >= 1
        assert len(wpe.whistleblower_complaints) >= 1
        assert "whistleblower_complaints" in report.found_fields


# ---------------------------------------------------------------------------
# Cybersecurity detection tests
# ---------------------------------------------------------------------------


class TestCybersecurityDetection:
    """Test cybersecurity incident detection."""

    def test_data_breach_full_extractor(self) -> None:
        filing_docs = _make_10k_with_item3(
            "The company experienced a cybersecurity incident in Q3 "
            "resulting in unauthorized access to customer data."
        )
        state = _make_state(filing_documents=filing_docs)
        wpe, _whistleblowers, report = (
            extract_workforce_product_environmental(state)
        )
        assert len(wpe.cybersecurity_incidents) >= 1
        assert "cybersecurity_incidents" in report.found_fields

    def test_cyber_attack_from_web(self) -> None:
        web_results: dict[str, Any] = {
            "cyber": [
                {
                    "title": "Test Corp hit by ransomware attack",
                    "description": "ransomware disrupted operations",
                    "snippet": "",
                    "url": "https://example.com",
                }
            ]
        }
        state = _make_state(web_search_results=web_results)
        wpe, _whistleblowers, _report = (
            extract_workforce_product_environmental(state)
        )
        assert len(wpe.cybersecurity_incidents) >= 1


# ---------------------------------------------------------------------------
# Empty state tests
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test graceful handling of empty or missing data."""

    def test_empty_state_returns_defaults(self) -> None:
        state = AnalysisState(ticker="EMPTY")
        wpe, whistleblowers, report = (
            extract_workforce_product_environmental(state)
        )
        assert wpe.employment_matters == []
        assert wpe.cybersecurity_incidents == []
        assert whistleblowers == []
        assert report.extractor_name == "workforce_product_environmental"

    def test_no_acquired_data(self) -> None:
        state = AnalysisState(ticker="NODATA")
        state.acquired_data = None
        _wpe, whistleblowers, _report = (
            extract_workforce_product_environmental(state)
        )
        assert whistleblowers == []

    def test_empty_filings(self) -> None:
        state = _make_state(filing_documents={})
        wpe, _whistleblowers, _report = (
            extract_workforce_product_environmental(state)
        )
        assert wpe.employment_matters == []


# ---------------------------------------------------------------------------
# Full extractor integration tests
# ---------------------------------------------------------------------------


class TestFullExtractor:
    """Test the full extract_workforce_product_environmental function."""

    def test_item3_multi_category(self) -> None:
        filing_docs = _make_10k_with_item3(
            "The company faces employment litigation for discrimination "
            "claims. An EEOC charge was filed. Additionally, the EPA "
            "enforcement action for environmental violations continues."
        )
        state = _make_state(filing_documents=filing_docs)
        wpe, _wb, report = extract_workforce_product_environmental(state)
        assert len(wpe.employment_matters) >= 1
        assert len(wpe.eeoc_charges) >= 1
        assert len(wpe.environmental_actions) >= 1
        assert "employment_matters" in report.found_fields
        assert "eeoc_charges" in report.found_fields
        assert "environmental_actions" in report.found_fields

    def test_web_and_filing_combined(self) -> None:
        filing_docs = _make_10k_with_item3(
            "A WARN Act notice was filed for the planned facility closure."
        )
        web_results: dict[str, Any] = {
            "product": [
                {
                    "title": "Product recall issued for Test Corp",
                    "description": "product recall affecting 10K units",
                    "snippet": "",
                    "url": "https://example.com",
                }
            ]
        }
        state = _make_state(
            filing_documents=filing_docs,
            web_search_results=web_results,
        )
        wpe, _wb, _report = extract_workforce_product_environmental(state)
        assert len(wpe.warn_notices) >= 1
        assert len(wpe.product_recalls) >= 1

    def test_3_tuple_return(self) -> None:
        """Verify the function returns exactly 3 values."""
        state = _make_state()
        result = extract_workforce_product_environmental(state)
        assert len(result) == 3
        wpe, whistleblowers, report = result
        assert hasattr(wpe, "employment_matters")
        assert isinstance(whistleblowers, list)
        assert hasattr(report, "extractor_name")
