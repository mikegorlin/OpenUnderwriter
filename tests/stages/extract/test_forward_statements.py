"""Tests for forward statement extraction from SEC filings.

Tests cover:
- LLM extraction of forward statements (mocked)
- Quantitative and qualitative guidance handling
- Catalyst event extraction
- Growth estimate extraction from yfinance data
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.forward_looking import (
    CatalystEvent,
    ForwardStatement,
    GrowthEstimate,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.forward_statements import extract_forward_statements


def _make_state(
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    market_data: dict[str, Any] | None = None,
    earnings_guidance: Any | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState for forward statement extraction tests."""
    state = AnalysisState(ticker="TEST")
    state.acquired_data = MagicMock()
    state.acquired_data.filing_documents = filing_documents or {}
    state.acquired_data.market_data = market_data or {}
    # Set up extracted.market.earnings_guidance
    if earnings_guidance is not None:
        state.extracted = MagicMock()
        state.extracted.market = MagicMock()
        state.extracted.market.earnings_guidance = earnings_guidance
    return state


def _mock_llm_extraction_result(
    forward_statements: list[dict[str, Any]] | None = None,
    catalyst_events: list[dict[str, Any]] | None = None,
    provides_numeric_guidance: bool = False,
    guidance_summary: str = "",
) -> dict[str, Any]:
    """Build a mock ForwardLookingExtraction-like dict."""
    return {
        "forward_statements": forward_statements or [],
        "guidance_changes": [],
        "catalyst_events": catalyst_events or [],
        "provides_numeric_guidance": provides_numeric_guidance,
        "guidance_summary": guidance_summary,
    }


class TestExtractForwardStatements:
    """Test extract_forward_statements with mocked LLM."""

    def test_returns_forward_statements_list(self) -> None:
        """extract_forward_statements returns a list of ForwardStatement."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {
                        "accession": "0001234-24-000001",
                        "filing_date": "2024-06-15",
                        "full_text": "We expect revenue to grow 15% in FY2025.",
                    }
                ]
            },
        )
        mock_extraction = _mock_llm_extraction_result(
            forward_statements=[
                {
                    "metric": "Revenue Growth",
                    "target_value": "15%",
                    "target_numeric_low": 15.0,
                    "target_numeric_high": 15.0,
                    "timeframe": "FY2025",
                    "context": "We expect revenue to grow 15% in FY2025.",
                    "is_quantitative": True,
                    "filing_section": "MD&A",
                }
            ],
            provides_numeric_guidance=True,
            guidance_summary="Company guides for 15% revenue growth in FY2025.",
        )

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert isinstance(statements, list)
        assert len(statements) >= 1
        assert isinstance(statements[0], ForwardStatement)
        assert statements[0].metric_name == "Revenue Growth"

    def test_qualitative_only_company(self) -> None:
        """Companies without numeric guidance still get qualitative ForwardStatements."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {
                        "accession": "0001234-24-000002",
                        "filing_date": "2024-06-15",
                        "full_text": "We expect continued growth in our cloud segment.",
                    }
                ]
            },
        )
        mock_extraction = _mock_llm_extraction_result(
            forward_statements=[
                {
                    "metric": "Cloud Segment Growth",
                    "target_value": "",
                    "target_numeric_low": None,
                    "target_numeric_high": None,
                    "timeframe": "",
                    "context": "We expect continued growth in our cloud segment.",
                    "is_quantitative": False,
                    "filing_section": "MD&A",
                }
            ],
            provides_numeric_guidance=False,
            guidance_summary="Qualitative growth expectations only.",
        )

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert len(statements) >= 1
        assert statements[0].guidance_type == "QUALITATIVE"
        assert statements[0].guidance_midpoint is None

    def test_quantitative_guidance_with_midpoint(self) -> None:
        """Quantitative guidance produces ForwardStatements with guidance_midpoint."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {
                        "accession": "0001234-24-000003",
                        "filing_date": "2024-06-15",
                        "full_text": "We expect EPS of $4.50 to $4.70 for FY2025.",
                    }
                ]
            },
        )
        mock_extraction = _mock_llm_extraction_result(
            forward_statements=[
                {
                    "metric": "EPS",
                    "target_value": "$4.50-$4.70",
                    "target_numeric_low": 4.50,
                    "target_numeric_high": 4.70,
                    "timeframe": "FY2025",
                    "context": "We expect EPS of $4.50 to $4.70 for FY2025.",
                    "is_quantitative": True,
                    "filing_section": "MD&A",
                }
            ],
            provides_numeric_guidance=True,
        )

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert len(statements) >= 1
        assert statements[0].guidance_type == "QUANTITATIVE"
        assert statements[0].guidance_midpoint == pytest.approx(4.60, abs=0.01)

    def test_catalyst_extraction(self) -> None:
        """Catalyst events are extracted and converted to CatalystEvent models."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {
                        "accession": "0001234-24-000004",
                        "filing_date": "2024-06-15",
                        "full_text": "FDA approval expected Q3 2025.",
                    }
                ]
            },
        )
        mock_extraction = _mock_llm_extraction_result(
            catalyst_events=[
                {
                    "event": "FDA drug approval decision",
                    "expected_timing": "Q3 2025",
                    "potential_impact": "Revenue loss if rejected",
                    "mentioned_in": "Risk Factors",
                }
            ],
        )

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert len(catalysts) >= 1
        assert isinstance(catalysts[0], CatalystEvent)
        assert catalysts[0].event == "FDA drug approval decision"
        assert catalysts[0].timing == "Q3 2025"
        assert "rejected" in catalysts[0].impact_if_negative.lower()

    def test_growth_estimates_from_yfinance(self) -> None:
        """Growth estimates are extracted from yfinance market data."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {
                        "accession": "0001234-24-000005",
                        "filing_date": "2024-06-15",
                        "full_text": "Annual report content.",
                    }
                ]
            },
            market_data={
                "info": {
                    "forwardEps": 5.20,
                    "trailingEps": 4.80,
                    "revenueGrowth": 0.12,
                    "earningsGrowth": 0.15,
                },
            },
        )
        mock_extraction = _mock_llm_extraction_result()

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert len(growth_ests) >= 1
        assert isinstance(growth_ests[0], GrowthEstimate)
        # At least one growth estimate should have numeric data
        numeric_ests = [g for g in growth_ests if g.estimate_numeric is not None]
        assert len(numeric_ests) >= 1

    def test_no_filings_returns_empty(self) -> None:
        """No filing documents returns empty lists with report."""
        state = _make_state(filing_documents={})
        statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert statements == []
        assert catalysts == []
        assert report is not None
        assert report.extractor_name == "forward_statements"

    def test_8k_filing_extraction(self) -> None:
        """8-K filings are also extracted for forward statements."""
        state = _make_state(
            filing_documents={
                "8-K": [
                    {
                        "accession": "0001234-24-000006",
                        "filing_date": "2024-09-15",
                        "full_text": "The company raises FY2025 EPS guidance to $5.00-$5.20.",
                    }
                ]
            },
        )
        mock_extraction = _mock_llm_extraction_result(
            forward_statements=[
                {
                    "metric": "EPS",
                    "target_value": "$5.00-$5.20",
                    "target_numeric_low": 5.00,
                    "target_numeric_high": 5.20,
                    "timeframe": "FY2025",
                    "context": "Company raises FY2025 EPS guidance.",
                    "is_quantitative": True,
                    "filing_section": "Earnings Release",
                }
            ],
            provides_numeric_guidance=True,
        )

        with patch(
            "do_uw.stages.extract.forward_statements._run_llm_extraction",
            return_value=mock_extraction,
        ):
            statements, catalysts, growth_ests, report = extract_forward_statements(state)

        assert len(statements) >= 1
        assert statements[0].source_filing == "8-K:0001234-24-000006"
