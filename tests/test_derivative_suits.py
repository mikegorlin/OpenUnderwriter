"""Tests for derivative suit and fiduciary claim extractor.

Covers:
- Derivative pattern matching from Item 3
- Section 220 books-and-records demand detection
- Caremark oversight claim detection
- Coverage type assignment (DERIVATIVE_SIDE_A/B)
- Empty text returns empty list
- Deduplication across sources
- Time horizon filtering (5 years)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from do_uw.models.litigation import CoverageType, LegalTheory
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.derivative_suits import (
    _determine_coverage_type,
    _is_derivative_reference,
    _is_within_horizon,
    extract_derivative_suits,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    web_results: list[str] | None = None,
    blind_spot_results: dict[str, Any] | None = None,
) -> AnalysisState:
    """Build minimal AnalysisState for derivative suit testing."""
    lit_data: dict[str, Any] = {}
    if web_results is not None:
        lit_data["web_results"] = web_results

    acquired = AcquiredData(
        litigation_data=lit_data,
        blind_spot_results=blind_spot_results or {},
        filing_documents=filing_documents or {},
    )

    return AnalysisState(
        ticker="TEST",
        acquired_data=acquired,
    )


def _make_10k_text(item3_content: str) -> str:
    """Build 10-K text with Item 3 content."""
    # Pad to exceed 200-char section minimum.
    padded = item3_content
    if len(padded) < 250:
        padded += " " * (250 - len(padded))

    return (
        "ITEM 1. BUSINESS\n\nCompany overview.\n\n"
        "Item 1A. Risk Factors\n\nRisk factors here.\n\n"
        f"Item 3. Legal Proceedings\n\n{padded}\n\n"
        "Item 4. Mine Safety\n\n"
    )


# ---------------------------------------------------------------------------
# Test derivative pattern matching
# ---------------------------------------------------------------------------


class TestDerivativePatterns:
    """Test derivative suit pattern detection."""

    def test_derivative_action_detected(self) -> None:
        """'derivative action' keyword detected."""
        assert _is_derivative_reference(
            "A shareholder filed a derivative action against directors."
        )

    def test_derivative_suit_detected(self) -> None:
        """'derivative suit' keyword detected."""
        assert _is_derivative_reference(
            "The derivative suit alleges breach of fiduciary duty."
        )

    def test_non_derivative_not_detected(self) -> None:
        """Non-derivative text not detected."""
        assert not _is_derivative_reference(
            "The Company sells widgets to customers."
        )

    def test_demand_futility_detected(self) -> None:
        """'demand futility' keyword detected."""
        assert _is_derivative_reference(
            "Plaintiff alleged demand futility based on board control."
        )

    def test_court_of_chancery_detected(self) -> None:
        """'Court of Chancery' keyword detected."""
        assert _is_derivative_reference(
            "Filed in the Court of Chancery of the State of Delaware."
        )

    def test_item3_derivative_case_extracted(self) -> None:
        """Derivative case extracted from Item 3."""
        state = _make_state(
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": _make_10k_text(
                        "A shareholder derivative action was filed in the "
                        "Court of Chancery alleging breach of fiduciary "
                        "duty by the Company's directors. The case is "
                        "currently pending. The plaintiff alleges demand "
                        "futility based on the directors' involvement "
                        "in the challenged transactions."
                    ),
                }],
            },
        )
        cases, _report = extract_derivative_suits(state)
        assert len(cases) >= 1


# ---------------------------------------------------------------------------
# Test Section 220 detection
# ---------------------------------------------------------------------------


class TestSection220:
    """Test Section 220 books-and-records demand detection."""

    def test_section_220_demand_detected(self) -> None:
        """Section 220 demand flagged in key_rulings."""
        state = _make_state(
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": _make_10k_text(
                        "A stockholder served a Section 220 books and "
                        "records demand seeking inspection of documents "
                        "related to the Company's acquisition of XYZ Corp. "
                        "The Company is responding to the demand. This is "
                        "a precursor to potential derivative litigation."
                    ),
                }],
            },
        )
        cases, report = extract_derivative_suits(state)
        assert len(cases) >= 1
        # Check Section 220 flagged.
        section_220_found = any(
            "Section 220" in kr.value
            for c in cases
            for kr in c.key_rulings
        )
        assert section_220_found
        assert "section_220_demands" in report.found_fields


# ---------------------------------------------------------------------------
# Test Caremark claim detection
# ---------------------------------------------------------------------------


class TestCaremark:
    """Test Caremark oversight claim detection."""

    def test_caremark_claim_detected(self) -> None:
        """Caremark claim added to allegations."""
        state = _make_state(
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": _make_10k_text(
                        "A derivative action was filed alleging Caremark "
                        "oversight claims against the board of directors. "
                        "The plaintiff argues the board failed to implement "
                        "adequate compliance and reporting systems, leading "
                        "to regulatory violations."
                    ),
                }],
            },
        )
        cases, _report = extract_derivative_suits(state)
        assert len(cases) >= 1
        caremark_found = any(
            "Caremark" in a.value
            for c in cases
            for a in c.allegations
        )
        assert caremark_found


# ---------------------------------------------------------------------------
# Test coverage type assignment
# ---------------------------------------------------------------------------


class TestCoverageType:
    """Test derivative coverage type determination."""

    def test_default_coverage_side_b(self) -> None:
        """Default derivative coverage is DERIVATIVE_SIDE_B."""
        coverage = _determine_coverage_type(
            "A derivative suit was filed against the company."
        )
        assert coverage == CoverageType.DERIVATIVE_SIDE_B

    def test_individual_capacity_side_a(self) -> None:
        """Individual capacity triggers DERIVATIVE_SIDE_A."""
        coverage = _determine_coverage_type(
            "Directors named in their individual capacity."
        )
        assert coverage == CoverageType.DERIVATIVE_SIDE_A

    def test_legal_theories_include_derivative_duty(self) -> None:
        """Legal theories always include DERIVATIVE_DUTY."""
        state = _make_state(
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": _make_10k_text(
                        "A shareholder derivative action was filed against "
                        "the board of directors alleging breach of fiduciary "
                        "duty and oversight duty failures. The matter is "
                        "being litigated in the Delaware Court of Chancery."
                    ),
                }],
            },
        )
        cases, _report = extract_derivative_suits(state)
        assert len(cases) >= 1
        theory_values = {t.value for c in cases for t in c.legal_theories}
        assert LegalTheory.DERIVATIVE_DUTY.value in theory_values


# ---------------------------------------------------------------------------
# Test empty text
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test empty inputs return empty list."""

    def test_no_acquired_data(self) -> None:
        """No acquired data returns empty list."""
        state = AnalysisState(ticker="TEST")
        cases, report = extract_derivative_suits(state)
        assert len(cases) == 0
        assert "No derivative suits found" in report.warnings

    def test_empty_filing_documents(self) -> None:
        """Empty filing documents returns empty list."""
        state = _make_state(filing_documents={})
        cases, _report = extract_derivative_suits(state)
        assert len(cases) == 0


# ---------------------------------------------------------------------------
# Test time horizon filtering
# ---------------------------------------------------------------------------


class TestTimeHorizon:
    """Test 5-year time horizon filtering."""

    def test_recent_within_horizon(self) -> None:
        """Recent date within 5 years."""
        assert _is_within_horizon(date.today() - timedelta(days=365))

    def test_old_outside_horizon(self) -> None:
        """Old date outside 5 years."""
        assert not _is_within_horizon(
            date.today() - timedelta(days=1826),
        )

    def test_none_date_included(self) -> None:
        """None date always included."""
        assert _is_within_horizon(None)
