"""Tests for Phase 119: Competitive landscape D&O enrichment."""

from __future__ import annotations

import pytest

from do_uw.models.competitive_landscape import (
    CompetitiveLandscape,
    MoatDimension,
    PeerRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.competitive_enrichment import (
    enrich_competitive_landscape,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    *,
    ticker: str = "ACME",
    peers: list[PeerRow] | None = None,
    moats: list[MoatDimension] | None = None,
) -> AnalysisState:
    state = AnalysisState(ticker=ticker)
    if peers is not None:
        state.dossier.competitive_landscape.peers = peers
    if moats is not None:
        state.dossier.competitive_landscape.moat_dimensions = moats
    return state


def _make_peer(name: str = "Rival Inc", ticker: str = "RVL") -> PeerRow:
    return PeerRow(company_name=name, ticker=ticker, market_cap="$10B")


def _make_moat(
    dimension: str = "Scale Economics",
    present: bool = True,
    strength: str = "Strong",
) -> MoatDimension:
    return MoatDimension(
        dimension=dimension,
        present=present,
        strength=strength,
        durability="High",
        evidence="Market leader",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnrichCompetitiveLandscape:
    """Test competitive landscape D&O enrichment."""

    def test_empty_state_no_crash(self) -> None:
        state = _make_state(peers=[], moats=[])
        enrich_competitive_landscape(state)
        assert state.dossier.competitive_landscape.do_commentary == ""

    def test_do_commentary_references_company(self) -> None:
        state = _make_state(
            peers=[_make_peer(), _make_peer("Rival2", "RV2")],
            moats=[_make_moat()],
        )
        enrich_competitive_landscape(state)
        assert "ACME" in state.dossier.competitive_landscape.do_commentary

    def test_do_commentary_mentions_peer_count(self) -> None:
        state = _make_state(
            peers=[_make_peer(), _make_peer("Rival2", "RV2")],
            moats=[],
        )
        enrich_competitive_landscape(state)
        assert "2" in state.dossier.competitive_landscape.do_commentary

    def test_moat_dimensions_listed(self) -> None:
        state = _make_state(
            peers=[_make_peer()],
            moats=[_make_moat("Scale Economics"), _make_moat("Brand Premium")],
        )
        enrich_competitive_landscape(state)
        commentary = state.dossier.competitive_landscape.do_commentary
        assert "Scale Economics" in commentary or "2 moat" in commentary

    def test_weak_moat_warning(self) -> None:
        state = _make_state(
            peers=[_make_peer()],
            moats=[_make_moat("Scale Economics", strength="Weak")],
        )
        enrich_competitive_landscape(state)
        commentary = state.dossier.competitive_landscape.do_commentary
        assert "Weak" in commentary or "WARNING" in commentary

    def test_per_moat_do_risk_populated(self) -> None:
        moat = _make_moat("Scale Economics", strength="Weak")
        state = _make_state(peers=[_make_peer()], moats=[moat])
        enrich_competitive_landscape(state)
        assert moat.do_risk != ""
        assert "10(b)" in moat.do_risk or "guidance" in moat.do_risk.lower()

    def test_strong_moat_no_do_risk(self) -> None:
        moat = _make_moat("Scale Economics", strength="Strong")
        state = _make_state(peers=[_make_peer()], moats=[moat])
        enrich_competitive_landscape(state)
        # Strong moats should not get do_risk (only Weak/Moderate)
        assert moat.do_risk == ""

    def test_moderate_moat_gets_do_risk(self) -> None:
        moat = _make_moat("Switching Costs", strength="Moderate")
        state = _make_state(peers=[_make_peer()], moats=[moat])
        enrich_competitive_landscape(state)
        assert moat.do_risk != ""

    def test_unknown_moat_dimension_fallback(self) -> None:
        moat = _make_moat("Proprietary Tech", strength="Weak")
        state = _make_state(peers=[_make_peer()], moats=[moat])
        enrich_competitive_landscape(state)
        assert "D&O" in moat.do_risk or "exposure" in moat.do_risk.lower()

    def test_no_peers_but_moats(self) -> None:
        state = _make_state(
            peers=[],
            moats=[_make_moat()],
        )
        enrich_competitive_landscape(state)
        # Should still enrich because moats are present
        assert state.dossier.competitive_landscape.do_commentary != ""
