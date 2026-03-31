"""Tests for Phase 119 competitive landscape + alt data context builders."""

from __future__ import annotations

import pytest

from do_uw.models.alt_data import (
    AIWashingRisk,
    AltDataAssessments,
    ESGRisk,
    PeerSCACheck,
    TariffExposure,
)
from do_uw.models.competitive_landscape import (
    CompetitiveLandscape,
    MoatDimension,
    PeerRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.alt_data_context import (
    build_ai_washing_context,
    build_esg_context,
    build_peer_sca_context,
    build_tariff_context,
)
from do_uw.stages.render.context_builders.dossier_competitive import (
    build_competitive_landscape_context,
)


@pytest.fixture
def state() -> AnalysisState:
    return AnalysisState(ticker="TEST")


# ---------------------------------------------------------------------------
# build_competitive_landscape_context
# ---------------------------------------------------------------------------


class TestBuildCompetitiveLandscapeContext:
    def test_empty_landscape(self, state: AnalysisState) -> None:
        result = build_competitive_landscape_context(state)
        assert result["comp_peers"] == []
        assert result["comp_moats"] == []
        assert result["comp_narrative"] == ""
        assert result["comp_do"] == ""
        assert result["has_competitive_data"] is False

    def test_with_peers(self, state: AnalysisState) -> None:
        state.dossier.competitive_landscape = CompetitiveLandscape(
            peers=[
                PeerRow(
                    company_name="Acme Corp",
                    ticker="ACM",
                    market_cap="$10B",
                    revenue="$5B",
                    margin="15%",
                    growth_rate="8%",
                    rd_spend="$500M",
                    market_share="12%",
                    sca_history="1 filing (2023)",
                    do_relevance="Peer SCA creates sector contagion risk.",
                ),
            ],
            competitive_position_narrative="Subject is #2 in market share.",
            do_commentary="Competitive pressure may drive aggressive guidance.",
        )
        result = build_competitive_landscape_context(state)
        assert result["has_competitive_data"] is True
        assert len(result["comp_peers"]) == 1
        assert result["comp_peers"][0]["company"] == "Acme Corp"
        assert result["comp_peers"][0]["ticker"] == "ACM"
        assert result["comp_narrative"] == "Subject is #2 in market share."
        assert result["comp_do"] == "Competitive pressure may drive aggressive guidance."

    def test_with_moats(self, state: AnalysisState) -> None:
        state.dossier.competitive_landscape = CompetitiveLandscape(
            moat_dimensions=[
                MoatDimension(
                    dimension="Switching Costs",
                    present=True,
                    strength="Strong",
                    durability="High",
                    evidence="Enterprise contracts with 3-year terms.",
                    do_risk="If switching costs erode, revenue cliff creates DDL exposure.",
                ),
                MoatDimension(
                    dimension="Network Effects",
                    present=False,
                    strength="Weak",
                    durability="Low",
                    evidence="No meaningful network effects.",
                    do_risk="",
                ),
            ]
        )
        result = build_competitive_landscape_context(state)
        assert result["has_competitive_data"] is True
        assert len(result["comp_moats"]) == 2
        assert result["comp_moats"][0]["dimension"] == "Switching Costs"
        assert result["comp_moats"][0]["present"] == "Yes"
        assert result["comp_moats"][1]["present"] == "No"

    def test_empty_fields_show_not_disclosed(self, state: AnalysisState) -> None:
        state.dossier.competitive_landscape = CompetitiveLandscape(
            peers=[PeerRow(company_name="X Corp", ticker="X")]
        )
        result = build_competitive_landscape_context(state)
        peer = result["comp_peers"][0]
        assert peer["market_cap"] == "Not Disclosed"
        assert peer["revenue"] == "Not Disclosed"

    def test_signal_results_param_accepted(self, state: AnalysisState) -> None:
        """Verify signal_results keyword-only param is accepted."""
        result = build_competitive_landscape_context(
            state, signal_results={"SIG-001": {"status": "TRIGGERED"}}
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# build_esg_context
# ---------------------------------------------------------------------------


class TestBuildESGContext:
    def test_empty_esg(self, state: AnalysisState) -> None:
        result = build_esg_context(state)
        assert result["esg_risk_level"] == "LOW"
        assert result["esg_controversies"] == []
        assert result["esg_ratings"] == []
        assert result["has_esg_data"] is False

    def test_with_data(self, state: AnalysisState) -> None:
        state.alt_data = AltDataAssessments(
            esg=ESGRisk(
                risk_level="HIGH",
                controversies=["Water pollution incident (2024)", "Labor violations"],
                ratings={"MSCI": "CCC", "ISS": "5"},
                greenwashing_indicators=["Carbon neutral claim unverified"],
                do_relevance="ESG controversies create shareholder derivative risk.",
            )
        )
        result = build_esg_context(state)
        assert result["has_esg_data"] is True
        assert result["esg_risk_level"] == "HIGH"
        assert len(result["esg_controversies"]) == 2
        assert result["esg_ratings"][0] == {"agency": "MSCI", "rating": "CCC"}
        assert len(result["esg_greenwashing"]) == 1


# ---------------------------------------------------------------------------
# build_ai_washing_context
# ---------------------------------------------------------------------------


class TestBuildAIWashingContext:
    def test_empty_ai(self, state: AnalysisState) -> None:
        result = build_ai_washing_context(state)
        assert result["ai_claims_present"] is False
        assert result["has_ai_data"] is False

    def test_with_data(self, state: AnalysisState) -> None:
        state.alt_data = AltDataAssessments(
            ai_washing=AIWashingRisk(
                ai_claims_present=True,
                indicators=[
                    {"claim": "AI-powered analytics", "evidence": "No ML team", "risk": "HIGH"},
                ],
                scienter_risk="MEDIUM",
                do_relevance="SEC focus on AI-washing in 2024-2025.",
            )
        )
        result = build_ai_washing_context(state)
        assert result["has_ai_data"] is True
        assert result["ai_scienter_risk"] == "MEDIUM"
        assert len(result["ai_indicators"]) == 1


# ---------------------------------------------------------------------------
# build_tariff_context
# ---------------------------------------------------------------------------


class TestBuildTariffContext:
    def test_empty_tariff(self, state: AnalysisState) -> None:
        result = build_tariff_context(state)
        assert result["tariff_risk_level"] == "LOW"
        assert result["has_tariff_data"] is False

    def test_with_data(self, state: AnalysisState) -> None:
        state.alt_data = AltDataAssessments(
            tariff=TariffExposure(
                risk_level="HIGH",
                supply_chain_exposure="Heavy reliance on Chinese manufacturing",
                manufacturing_locations=["Shenzhen, China", "Taipei, Taiwan"],
                international_revenue_pct="62%",
                tariff_risk_factors=["Section 301 tariffs", "CHIPS Act compliance"],
                do_relevance="Tariff risk creates material forward guidance exposure.",
            )
        )
        result = build_tariff_context(state)
        assert result["has_tariff_data"] is True
        assert result["tariff_risk_level"] == "HIGH"
        assert len(result["tariff_manufacturing"]) == 2
        assert result["tariff_intl_revenue"] == "62%"


# ---------------------------------------------------------------------------
# build_peer_sca_context
# ---------------------------------------------------------------------------


class TestBuildPeerSCAContext:
    def test_empty_peer_sca(self, state: AnalysisState) -> None:
        result = build_peer_sca_context(state)
        assert result["peer_scas"] == []
        assert result["has_peer_sca"] is False

    def test_with_data(self, state: AnalysisState) -> None:
        state.alt_data = AltDataAssessments(
            peer_sca=PeerSCACheck(
                peer_scas=[
                    {"company": "Rival Inc", "filing_date": "2025-01-20", "allegation": "Revenue misstatement"},
                ],
                sector="Technology",
                contagion_risk="MEDIUM",
                do_relevance="Sector-wide SCA wave increases filing probability.",
            )
        )
        result = build_peer_sca_context(state)
        assert result["has_peer_sca"] is True
        assert result["peer_sector"] == "Technology"
        assert result["peer_contagion_risk"] == "MEDIUM"
        assert len(result["peer_scas"]) == 1

    def test_signal_results_param_accepted(self, state: AnalysisState) -> None:
        result = build_peer_sca_context(
            state, signal_results={"SIG-002": {"status": "CLEAR"}}
        )
        assert isinstance(result, dict)
