"""Tests for competitive landscape LLM extraction from 10-K.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.competitive_landscape import (
    CompetitiveLandscape,
    MoatDimension,
    PeerRow,
)


def _make_state(
    *,
    filing_text: str = "",
    accession: str = "",
    company_name: str = "Acme Corp",
    ticker: str = "ACME",
    sic_code: str = "3674",
    sector: str = "Technology",
    revenue: float | None = 5_000_000_000.0,
) -> Any:
    """Build a minimal mock AnalysisState for competitive extraction tests."""
    from do_uw.models.alt_data import AltDataAssessments
    from do_uw.models.dossier import DossierData

    state = MagicMock()
    state.dossier = DossierData()
    state.alt_data = AltDataAssessments()

    # Company identity
    state.company.identity.legal_name.value = company_name
    state.company.identity.ticker = ticker
    state.company.identity.sic_code.value = sic_code
    state.company.identity.sector.value = sector
    state.company.revenue_model_type.value = "B2B"

    # Financials
    stmt = MagicMock()
    stmt.revenue = revenue
    state.extracted.financials.statements = [stmt]

    # Scoring
    state.scoring.composite_score = 72.5
    state.scoring.tier = "WATCH"

    # Filing documents
    if filing_text:
        state.acquired_data.filing_documents = {
            "10-K": [{"full_text": filing_text, "accession": accession}],
        }
    else:
        state.acquired_data.filing_documents = {}

    return state


_MOCK_LLM_RESPONSE = {
    "peers": [
        {
            "company_name": "Beta Inc",
            "ticker": "BETA",
            "market_cap": "$10B",
            "revenue": "$3B",
            "margin": "22%",
            "growth_rate": "8%",
            "rd_spend": "$500M",
            "market_share": "15%",
            "stock_performance": "Not Disclosed",
            "sca_history": "Not Disclosed",
        },
        {
            "company_name": "Gamma Corp",
            "ticker": "GAMA",
            "market_cap": "Not Disclosed",
            "revenue": "$2B",
            "margin": "18%",
            "growth_rate": "12%",
            "rd_spend": "Not Disclosed",
            "market_share": "10%",
            "stock_performance": "Not Disclosed",
            "sca_history": "Not Disclosed",
        },
        {
            "company_name": "Delta Ltd",
            "ticker": "DELT",
            "market_cap": "$8B",
            "revenue": "$4B",
            "margin": "25%",
            "growth_rate": "5%",
            "rd_spend": "$300M",
            "market_share": "20%",
            "stock_performance": "Not Disclosed",
            "sca_history": "Not Disclosed",
        },
        {
            "company_name": "Epsilon Inc",
            "ticker": "EPSI",
            "market_cap": "$6B",
            "revenue": "$2.5B",
            "margin": "20%",
            "growth_rate": "10%",
            "rd_spend": "$200M",
            "market_share": "8%",
            "stock_performance": "Not Disclosed",
            "sca_history": "Not Disclosed",
        },
    ],
    "moat_dimensions": [
        {
            "dimension": "Data Advantage",
            "present": True,
            "strength": "Strong",
            "durability": "High",
            "evidence": "Proprietary dataset of 500M records",
        },
        {
            "dimension": "Switching Costs",
            "present": True,
            "strength": "Moderate",
            "durability": "Medium",
            "evidence": "Deep enterprise integrations",
        },
        {
            "dimension": "Scale Economics",
            "present": True,
            "strength": "Strong",
            "durability": "High",
            "evidence": "Fixed cost base with 80% gross margin",
        },
        {
            "dimension": "Brand Premium",
            "present": False,
            "strength": "Weak",
            "durability": "Low",
            "evidence": "Commodity perception in market",
        },
        {
            "dimension": "Network Effects",
            "present": False,
            "strength": "Weak",
            "durability": "Low",
            "evidence": "No network externalities identified",
        },
        {
            "dimension": "Regulatory Barrier",
            "present": True,
            "strength": "Moderate",
            "durability": "High",
            "evidence": "FDA clearance required for new entrants",
        },
        {
            "dimension": "Distribution Lock",
            "present": False,
            "strength": "Weak",
            "durability": "Low",
            "evidence": "Open distribution channels",
        },
    ],
    "competitive_position_narrative": (
        "Acme Corp holds a strong competitive position through its proprietary "
        "dataset and scale economics, offsetting weak brand positioning."
    ),
}


class TestExtractCompetitiveLandscapeEmpty:
    """Test graceful fallback when no 10-K text is available."""

    @pytest.mark.asyncio
    async def test_empty_state_no_crash(self) -> None:
        """Function returns gracefully with empty CompetitiveLandscape on empty state."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state()
        await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert isinstance(cl, CompetitiveLandscape)
        assert cl.peers == []
        assert cl.moat_dimensions == []
        assert cl.competitive_position_narrative == ""


class TestExtractCompetitiveLandscapeValid:
    """Test valid extraction with mocked LLM response."""

    @pytest.mark.asyncio
    async def test_extracts_4_peers(self) -> None:
        """LLM extraction populates 4+ PeerRow objects."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state(
            filing_text="Item 1. Business Description\nCompetition section...",
            accession="0001234567-24-000001",
        )

        with patch(
            "do_uw.stages.extract.competitive_extraction._run_competitive_llm",
            return_value=_MOCK_LLM_RESPONSE,
        ):
            await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert len(cl.peers) >= 4
        assert all(isinstance(p, PeerRow) for p in cl.peers)
        assert cl.peers[0].company_name == "Beta Inc"
        assert cl.peers[0].ticker == "BETA"

    @pytest.mark.asyncio
    async def test_extracts_7_moat_dimensions(self) -> None:
        """LLM extraction populates 7 MoatDimension objects."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state(
            filing_text="Item 1. Business Description\nCompetition section...",
            accession="0001234567-24-000001",
        )

        with patch(
            "do_uw.stages.extract.competitive_extraction._run_competitive_llm",
            return_value=_MOCK_LLM_RESPONSE,
        ):
            await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert len(cl.moat_dimensions) == 7
        assert all(isinstance(m, MoatDimension) for m in cl.moat_dimensions)
        # Check specific dimension
        data_adv = [m for m in cl.moat_dimensions if m.dimension == "Data Advantage"]
        assert len(data_adv) == 1
        assert data_adv[0].present is True
        assert data_adv[0].strength == "Strong"

    @pytest.mark.asyncio
    async def test_competitive_narrative_populated(self) -> None:
        """LLM extraction populates competitive_position_narrative."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state(
            filing_text="Item 1. Business Description\nCompetition...",
            accession="0001234567-24-000001",
        )

        with patch(
            "do_uw.stages.extract.competitive_extraction._run_competitive_llm",
            return_value=_MOCK_LLM_RESPONSE,
        ):
            await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert "Acme Corp" in cl.competitive_position_narrative

    @pytest.mark.asyncio
    async def test_prompt_contains_qual03_context(self) -> None:
        """The prompt sent to LLM contains QUAL-03 analytical context."""
        from do_uw.stages.extract.competitive_extraction import (
            _COMPETITIVE_PROMPT,
        )

        # Verify template has required placeholders
        assert "{company_name}" in _COMPETITIVE_PROMPT
        assert "{ticker}" in _COMPETITIVE_PROMPT
        assert "{sector}" in _COMPETITIVE_PROMPT
        assert "{revenue}" in _COMPETITIVE_PROMPT

    @pytest.mark.asyncio
    async def test_not_disclosed_in_prompt(self) -> None:
        """Prompt instructs LLM to use 'Not Disclosed' for missing data."""
        from do_uw.stages.extract.competitive_extraction import (
            _COMPETITIVE_PROMPT,
        )

        assert "Not Disclosed" in _COMPETITIVE_PROMPT


class TestExtractCompetitiveLandscapeMalformed:
    """Test handling of malformed LLM responses."""

    @pytest.mark.asyncio
    async def test_malformed_json_fallback(self) -> None:
        """Malformed LLM response results in empty CompetitiveLandscape."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state(
            filing_text="Item 1. Business\nCompetition...",
            accession="0001234567-24-000001",
        )

        with patch(
            "do_uw.stages.extract.competitive_extraction._run_competitive_llm",
            return_value=None,
        ):
            await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert isinstance(cl, CompetitiveLandscape)
        # Should not crash, may have empty lists
        assert isinstance(cl.peers, list)

    @pytest.mark.asyncio
    async def test_missing_10k_text(self) -> None:
        """No filing text available returns empty competitive landscape."""
        from do_uw.stages.extract.competitive_extraction import (
            extract_competitive_landscape,
        )

        state = _make_state(filing_text="", accession="")
        await extract_competitive_landscape(state)

        cl = state.dossier.competitive_landscape
        assert cl.peers == []
        assert cl.moat_dimensions == []
