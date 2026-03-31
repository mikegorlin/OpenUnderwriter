"""Tests for Phase 119: Alternative data D&O relevance enrichment."""

from __future__ import annotations

import pytest

from do_uw.models.alt_data import AltDataAssessments
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.alt_data_enrichment import enrich_alt_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    *,
    ticker: str = "ACME",
    esg_risk: str = "LOW",
    esg_controversies: list[str] | None = None,
    ai_claims: bool = False,
    ai_indicators: list[dict[str, str]] | None = None,
    ai_scienter: str = "LOW",
    tariff_risk: str = "LOW",
    tariff_supply: str = "",
    tariff_intl_rev: str = "",
    peer_scas: list[dict[str, str]] | None = None,
    peer_contagion: str = "LOW",
) -> AnalysisState:
    state = AnalysisState(ticker=ticker)

    state.alt_data.esg.risk_level = esg_risk
    if esg_controversies:
        state.alt_data.esg.controversies = esg_controversies

    state.alt_data.ai_washing.ai_claims_present = ai_claims
    if ai_indicators:
        state.alt_data.ai_washing.indicators = ai_indicators
    state.alt_data.ai_washing.scienter_risk = ai_scienter

    state.alt_data.tariff.risk_level = tariff_risk
    state.alt_data.tariff.supply_chain_exposure = tariff_supply
    state.alt_data.tariff.international_revenue_pct = tariff_intl_rev

    if peer_scas:
        state.alt_data.peer_sca.peer_scas = peer_scas
    state.alt_data.peer_sca.contagion_risk = peer_contagion

    return state


# ---------------------------------------------------------------------------
# ESG Tests
# ---------------------------------------------------------------------------


class TestESGEnrichment:
    """Test ESG D&O relevance enrichment."""

    def test_low_risk_no_controversies(self) -> None:
        state = _make_state(esg_risk="LOW")
        enrich_alt_data(state)
        assert "LOW risk" in state.alt_data.esg.do_relevance
        assert "ACME" in state.alt_data.esg.do_relevance

    def test_high_risk_mentions_caremark(self) -> None:
        state = _make_state(
            esg_risk="HIGH",
            esg_controversies=["Environmental violation", "Worker safety"],
        )
        enrich_alt_data(state)
        rel = state.alt_data.esg.do_relevance
        assert "Caremark" in rel or "derivative" in rel.lower()
        assert "2 controversies" in rel
        assert "ACME" in rel

    def test_medium_risk_with_controversies(self) -> None:
        state = _make_state(
            esg_risk="MEDIUM",
            esg_controversies=["Supply chain labor"],
        )
        enrich_alt_data(state)
        assert state.alt_data.esg.do_relevance != ""
        assert "1 controvers" in state.alt_data.esg.do_relevance


# ---------------------------------------------------------------------------
# AI-Washing Tests
# ---------------------------------------------------------------------------


class TestAIWashingEnrichment:
    """Test AI-washing D&O relevance enrichment."""

    def test_no_ai_claims(self) -> None:
        state = _make_state(ai_claims=False)
        enrich_alt_data(state)
        assert "No AI" in state.alt_data.ai_washing.do_relevance
        assert "ACME" in state.alt_data.ai_washing.do_relevance

    def test_ai_claims_present(self) -> None:
        state = _make_state(
            ai_claims=True,
            ai_indicators=[{"claim": "AI-powered analytics", "risk": "HIGH"}],
            ai_scienter="HIGH",
        )
        enrich_alt_data(state)
        rel = state.alt_data.ai_washing.do_relevance
        assert "10(b)" in rel or "SEC" in rel
        assert "ACME" in rel
        assert "1 indicator" in rel


# ---------------------------------------------------------------------------
# Tariff Tests
# ---------------------------------------------------------------------------


class TestTariffEnrichment:
    """Test tariff exposure D&O relevance enrichment."""

    def test_low_tariff_risk(self) -> None:
        state = _make_state(tariff_risk="LOW")
        enrich_alt_data(state)
        assert "LOW" in state.alt_data.tariff.do_relevance
        assert "ACME" in state.alt_data.tariff.do_relevance

    def test_high_tariff_risk(self) -> None:
        state = _make_state(
            tariff_risk="HIGH",
            tariff_supply="China 60%",
            tariff_intl_rev="45%",
        )
        enrich_alt_data(state)
        rel = state.alt_data.tariff.do_relevance
        assert "Section 10(b)" in rel or "10(b)" in rel
        assert "ACME" in rel

    def test_medium_tariff_mentions_guidance(self) -> None:
        state = _make_state(tariff_risk="MEDIUM")
        enrich_alt_data(state)
        rel = state.alt_data.tariff.do_relevance
        assert "guidance" in rel.lower() or "revenue" in rel.lower()


# ---------------------------------------------------------------------------
# Peer SCA Tests
# ---------------------------------------------------------------------------


class TestPeerSCAEnrichment:
    """Test peer SCA contagion D&O relevance enrichment."""

    def test_no_peer_scas(self) -> None:
        state = _make_state()
        enrich_alt_data(state)
        assert "No active SCAs" in state.alt_data.peer_sca.do_relevance

    def test_with_peer_scas(self) -> None:
        state = _make_state(
            peer_scas=[
                {"company": "Rival Inc", "filing_date": "2025-01", "allegation": "10b-5"},
                {"company": "Other Co", "filing_date": "2025-03", "allegation": "Section 11"},
            ],
            peer_contagion="HIGH",
        )
        enrich_alt_data(state)
        rel = state.alt_data.peer_sca.do_relevance
        assert "2 active SCA" in rel
        assert "contagion" in rel.lower() or "Contagion" in rel

    def test_contagion_copycat_mention(self) -> None:
        state = _make_state(
            peer_scas=[{"company": "Rival", "filing_date": "2025-01", "allegation": "fraud"}],
            peer_contagion="MEDIUM",
        )
        enrich_alt_data(state)
        rel = state.alt_data.peer_sca.do_relevance
        assert "copycat" in rel.lower() or "precedent" in rel.lower()


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestEnrichAltDataIntegration:
    """Full enrichment integration tests."""

    def test_all_populated(self) -> None:
        state = _make_state(
            esg_risk="HIGH",
            esg_controversies=["Pollution"],
            ai_claims=True,
            ai_indicators=[{"claim": "AI engine"}],
            tariff_risk="MEDIUM",
            peer_scas=[{"company": "X", "filing_date": "2025-01", "allegation": "fraud"}],
        )
        enrich_alt_data(state)
        assert state.alt_data.esg.do_relevance != ""
        assert state.alt_data.ai_washing.do_relevance != ""
        assert state.alt_data.tariff.do_relevance != ""
        assert state.alt_data.peer_sca.do_relevance != ""

    def test_empty_state_no_crash(self) -> None:
        state = AnalysisState(ticker="TEST")
        enrich_alt_data(state)
        # Should produce default LOW messages
        assert state.alt_data.esg.do_relevance != ""
        assert state.alt_data.peer_sca.do_relevance != ""
