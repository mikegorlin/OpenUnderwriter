"""Integration tests for LLM-supplemented debt analysis.

Tests that LLM Item 8 footnote context (covenant status, credit facility
detail, debt instruments) supplements debt_structure without overriding
XBRL numeric values (total_debt, interest_expense, leverage ratios).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.validation import ExtractionReport


def _ten_k_dict(
    covenant_status: str | None = None,
    credit_facility_detail: str | None = None,
    debt_instruments: list[str] | None = None,
) -> dict[str, object]:
    """Build a TenKExtraction dict with specified debt fields."""
    extraction = TenKExtraction(
        covenant_status=covenant_status,
        credit_facility_detail=credit_facility_detail,
        debt_instruments=debt_instruments or [],
    )
    return extraction.model_dump()


def _make_state(with_llm: bool = True, **ten_k_kwargs: Any) -> AnalysisState:
    """Create state with optional LLM 10-K extraction."""
    state = AnalysisState(ticker="TEST")
    llm_extractions: dict[str, object] = {}
    if with_llm:
        llm_extractions["10-K:0001-24-000001"] = _ten_k_dict(**ten_k_kwargs)
    state.acquired_data = AcquiredData(llm_extractions=llm_extractions)
    return state


def _mock_no_xbrl_no_text(
    state: AnalysisState,
) -> tuple[
    SourcedValue[dict[str, float | None]] | None,
    SourcedValue[dict[str, float | None]] | None,
    SourcedValue[dict[str, Any]] | None,
    SourcedValue[dict[str, Any]] | None,
    list[ExtractionReport],
]:
    """Run extract_debt_analysis with no XBRL data and no filing text."""
    with (
        patch(
            "do_uw.stages.extract.debt_text_parsing.get_filings",
            return_value={},
        ),
        patch(
            "do_uw.stages.extract.debt_text_parsing.get_filing_texts",
            return_value={},
        ),
        patch(
            "do_uw.stages.extract.debt_text_parsing.get_filing_document_text",
            return_value=None,
        ),
    ):
        from do_uw.stages.extract.debt_analysis import extract_debt_analysis

        return extract_debt_analysis(state)


class TestDebtWithLLMCovenantStatus:
    """LLM covenant status supplements debt structure."""

    def test_covenant_status_populates(self) -> None:
        """Covenant status from LLM appears in debt_structure covenants."""
        state = _make_state(
            with_llm=True,
            covenant_status="In compliance with all covenants as of Dec 2024",
        )
        _liq, _lev, debt_structure, _ref, _reports = _mock_no_xbrl_no_text(state)

        assert debt_structure is not None
        covenants = debt_structure.value.get("covenants", {})
        assert isinstance(covenants, dict)
        assert covenants.get("mentioned") is True
        # Covenant status is a SourcedValue[str] from the converter
        cov_status = covenants.get("covenant_status")
        assert cov_status is not None
        assert cov_status.value == "In compliance with all covenants as of Dec 2024"
        assert cov_status.source == "10-K (LLM)"


class TestDebtWithoutLLM:
    """Falls back to XBRL + text parsing when no LLM data."""

    def test_no_llm_returns_none_structure(self) -> None:
        """Without LLM and without filing text, debt_structure is None."""
        state = _make_state(with_llm=False)
        _liq, _lev, debt_structure, _ref, _reports = _mock_no_xbrl_no_text(state)

        # No filing text + no LLM = None debt_structure
        assert debt_structure is None


class TestDebtLLMNoOverrideXBRL:
    """XBRL numeric values unchanged by LLM enrichment."""

    def test_liquidity_ratios_unchanged(self) -> None:
        """LLM covenant data does not affect XBRL liquidity ratios."""
        state = _make_state(
            with_llm=True,
            covenant_status="Near covenant breach on leverage ratio",
        )
        liq, _lev, _ds, _ref, _reports = _mock_no_xbrl_no_text(state)

        # With no balance sheet data, liquidity should still be None
        # (LLM doesn't generate numeric ratios)
        assert liq is None

    def test_leverage_ratios_unchanged(self) -> None:
        """LLM data does not affect XBRL leverage ratios."""
        state = _make_state(
            with_llm=True,
            covenant_status="Covenant waiver obtained",
        )
        _liq, lev, _ds, _ref, _reports = _mock_no_xbrl_no_text(state)

        # No balance sheet = no leverage ratios (LLM never creates these)
        assert lev is None


class TestDebtLLMCreditFacility:
    """Credit facility detail populated from LLM."""

    def test_credit_facility_detail_populates(self) -> None:
        """LLM credit facility detail appears in debt_structure."""
        state = _make_state(
            with_llm=True,
            credit_facility_detail="$5B revolving credit facility maturing March 2028",
        )
        _liq, _lev, debt_structure, _ref, _reports = _mock_no_xbrl_no_text(state)

        assert debt_structure is not None
        fac = debt_structure.value.get("credit_facility", {})
        assert isinstance(fac, dict)
        llm_detail = fac.get("llm_detail")
        assert llm_detail is not None
        assert llm_detail.value == "$5B revolving credit facility maturing March 2028"
        assert llm_detail.confidence == Confidence.HIGH

    def test_debt_instruments_from_llm(self) -> None:
        """LLM debt instrument descriptions stored on structure."""
        state = _make_state(
            with_llm=True,
            debt_instruments=[
                "$500M Senior Notes due 2027 at 4.5%",
                "$1B Term Loan B due 2029",
            ],
        )
        _liq, _lev, debt_structure, _ref, _reports = _mock_no_xbrl_no_text(state)

        assert debt_structure is not None
        instruments = debt_structure.value.get("llm_debt_instruments")
        assert instruments is not None
        assert len(instruments) == 2
        # Each instrument is a SourcedValue[str]
        assert instruments[0].value == "$500M Senior Notes due 2027 at 4.5%"

    def test_empty_llm_fields_no_enrichment(self) -> None:
        """No enrichment when all LLM debt fields are empty."""
        state = _make_state(
            with_llm=True,
            covenant_status=None,
            credit_facility_detail=None,
            debt_instruments=[],
        )
        _liq, _lev, debt_structure, _ref, _reports = _mock_no_xbrl_no_text(state)

        # No filing text + no enrichable LLM data = None
        assert debt_structure is None
