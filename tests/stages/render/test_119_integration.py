"""Integration tests for Phase 119 pipeline wiring.

Verifies that:
1. EXTRACT __init__ contains Phase 15-17 steps
2. BENCHMARK __init__ contains Steps 11-13
3. Context builders are wired in html_context_assembly
4. All builders return safe defaults on empty AnalysisState
5. Populated state flows through context builders correctly
6. Explicit AnalysisState fields are used (not underscore-prefixed)
7. Manifest structure is correct (company_operations, competitive not deferred)
8. Templates exist on disk for all manifest entries

Phase 119-06: Stock Drop Catalysts, Competitive Landscape, Alt Data Integration
"""

from __future__ import annotations

import inspect
import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_empty_state() -> AnalysisState:
    """Build minimal AnalysisState with defaults."""
    return AnalysisState(ticker="TEST")


def _make_populated_state() -> AnalysisState:
    """Build AnalysisState with Phase 119 data populated."""
    state = AnalysisState(ticker="ACME")

    # Stock patterns (explicit field)
    state.stock_patterns = [
        {
            "type": "earnings_cluster",
            "description": "3 earnings drops in 180 days",
            "dates": "2024-01-15, 2024-04-20, 2024-07-15",
            "do_relevance": "Pattern suggests recurring miss -> SCA exposure",
        }
    ]

    # Multi-horizon returns (explicit field)
    state.multi_horizon_returns = {
        "1D": -0.5,
        "5D": -2.1,
        "1M": -8.3,
        "3M": 1.2,
        "6M": -15.4,
        "52W": -22.7,
    }

    # Analyst consensus (explicit field)
    state.analyst_consensus = {
        "narrative": "12 of 18 analysts rate Buy; avg target $145 vs $120 current (20.8% upside).",
        "buy_count": 12,
        "hold_count": 4,
        "sell_count": 2,
        "avg_target": 145.0,
        "current": 120.0,
    }

    # Drop narrative (explicit field)
    state.drop_narrative = (
        "ACME exhibits an earnings cluster pattern with 3 significant drops "
        "within 180 calendar days, indicating recurring miss exposure."
    )

    # Competitive landscape (on dossier)
    state.dossier.competitive_landscape = CompetitiveLandscape(
        peers=[
            PeerRow(name="Rival Corp", ticker="RIVL", segment="Widgets", relationship="Direct"),
            PeerRow(name="Alt Inc", ticker="ALTI", segment="Gadgets", relationship="Adjacent"),
        ],
        moat_dimensions=[
            MoatDimension(dimension="Scale Economics", strength="Strong", evidence="60% market share"),
            MoatDimension(dimension="Brand Premium", strength="Moderate", evidence="Brand recall 45%"),
            MoatDimension(dimension="Switching Costs", strength="Weak", evidence="Low lock-in"),
        ],
        competitive_position_narrative="ACME dominates the widget market with 60% share.",
        do_commentary="Scale erosion risk if new entrant disrupts pricing.",
    )

    # Alt data
    state.alt_data = AltDataAssessments(
        esg=ESGRisk(
            risk_level="MEDIUM",
            controversies=["Supply chain labor concerns in 2024"],
            ratings={"MSCI": "BB", "Sustainalytics": "Medium Risk"},
        ),
        ai_washing=AIWashingRisk(
            ai_claims_present=True,
            indicators=[{"claim": "AI-powered optimization", "evidence": "mentioned 12x in 10-K", "risk": "MEDIUM"}],
            scienter_risk="MEDIUM",
        ),
        tariff=TariffExposure(
            risk_level="HIGH",
            supply_chain_exposure="45% sourced from China",
            manufacturing_locations=["US", "China", "Mexico"],
            tariff_risk_factors=["Section 301 tariffs on components"],
        ),
        peer_sca=PeerSCACheck(
            peer_scas=[{"company": "Rival Corp", "filing_date": "2024-03-15", "allegation": "channel stuffing"}],
            sector="Industrials",
            contagion_risk="MEDIUM",
        ),
    )

    return state


# ---------------------------------------------------------------------------
# 1. Source wiring tests: EXTRACT __init__ imports
# ---------------------------------------------------------------------------


class TestExtractWiring:
    """Verify EXTRACT __init__ contains Phase 119 steps."""

    def test_phase_15_stock_catalyst_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.extract", fromlist=["ExtractStage"]).ExtractStage)
        assert "Phase 15: Stock catalyst" in source
        assert "enrich_drops_with_prices_and_volume" in source

    def test_phase_16_alt_data_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.extract", fromlist=["ExtractStage"]).ExtractStage)
        assert "Phase 16: Alt data" in source
        assert "extract_alt_data" in source

    def test_phase_17_competitive_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.extract", fromlist=["ExtractStage"]).ExtractStage)
        assert "Phase 17: Competitive landscape" in source
        assert "extract_competitive_landscape" in source

    def test_extract_uses_explicit_state_fields(self) -> None:
        """No underscore-prefixed state attributes in extract wiring."""
        source = inspect.getsource(__import__("do_uw.stages.extract", fromlist=["ExtractStage"]).ExtractStage)
        assert "state.stock_patterns" in source
        assert "state.multi_horizon_returns" in source
        assert "state.analyst_consensus" in source
        assert "state._stock_patterns" not in source
        assert "state._multi_horizon_returns" not in source
        assert "state._analyst_consensus" not in source


# ---------------------------------------------------------------------------
# 2. BENCHMARK wiring tests
# ---------------------------------------------------------------------------


class TestBenchmarkWiring:
    """Verify BENCHMARK __init__ contains Phase 119 steps."""

    def test_step_11_drop_do_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.benchmark", fromlist=["BenchmarkStage"]).BenchmarkStage)
        assert "Step 11: Stock drop D&O" in source
        assert "generate_drop_do_assessments" in source

    def test_step_12_competitive_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.benchmark", fromlist=["BenchmarkStage"]).BenchmarkStage)
        assert "Step 12: Competitive landscape" in source
        assert "enrich_competitive_landscape" in source

    def test_step_13_alt_data_wired(self) -> None:
        source = inspect.getsource(__import__("do_uw.stages.benchmark", fromlist=["BenchmarkStage"]).BenchmarkStage)
        assert "Step 13: Alt data" in source
        assert "enrich_alt_data" in source

    def test_benchmark_uses_explicit_state_fields(self) -> None:
        """No underscore-prefixed state attributes in benchmark wiring."""
        source = inspect.getsource(__import__("do_uw.stages.benchmark", fromlist=["BenchmarkStage"]).BenchmarkStage)
        assert "state.stock_patterns" in source
        assert "state.drop_narrative" in source
        assert "state._stock_patterns" not in source
        assert "state._drop_narrative" not in source


# ---------------------------------------------------------------------------
# 3. Context builder wiring tests
# ---------------------------------------------------------------------------


class TestContextBuilderWiring:
    """Verify html_context_assembly imports all Phase 119 context builders."""

    def test_stock_catalyst_context_imported(self) -> None:
        source = Path("src/do_uw/stages/render/html_context_assembly.py").read_text()
        assert "build_stock_catalyst_context" in source
        assert "build_stock_performance_summary" in source

    def test_competitive_context_imported(self) -> None:
        source = Path("src/do_uw/stages/render/html_context_assembly.py").read_text()
        assert "build_competitive_landscape_context" in source

    def test_alt_data_context_imported(self) -> None:
        source = Path("src/do_uw/stages/render/html_context_assembly.py").read_text()
        assert "build_esg_context" in source
        assert "build_ai_washing_context" in source
        assert "build_tariff_context" in source
        assert "build_peer_sca_context" in source

    def test_context_assembly_uses_explicit_fields(self) -> None:
        """html_context_assembly reads explicit state fields."""
        source = Path("src/do_uw/stages/render/html_context_assembly.py").read_text()
        assert "state.stock_patterns" in source
        assert "state.drop_narrative" in source
        assert "state.multi_horizon_returns" in source
        assert "state.analyst_consensus" in source


# ---------------------------------------------------------------------------
# 4. Empty state tests: safe defaults
# ---------------------------------------------------------------------------


class TestEmptyStateDefaults:
    """All builders return safe defaults on empty AnalysisState."""

    def test_stock_catalyst_empty(self) -> None:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_catalyst_context,
        )

        state = _make_empty_state()
        ctx = build_stock_catalyst_context(state)
        assert ctx["enhanced_drop_events"] == []
        assert ctx["stock_patterns"] == []
        assert ctx["drop_narrative"] == ""
        assert ctx["has_catalyst_data"] is False

    def test_stock_performance_summary_empty(self) -> None:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_performance_summary,
        )

        state = _make_empty_state()
        ctx = build_stock_performance_summary(state)
        assert ctx["horizons"] == []
        assert ctx["analyst"] == {}
        assert ctx["has_performance_data"] is False

    def test_competitive_landscape_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_competitive import (
            build_competitive_landscape_context,
        )

        state = _make_empty_state()
        ctx = build_competitive_landscape_context(state)
        assert ctx["comp_peers"] == []
        assert ctx["comp_moats"] == []
        assert ctx["has_competitive_data"] is False

    def test_esg_empty(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_esg_context,
        )

        state = _make_empty_state()
        ctx = build_esg_context(state)
        assert ctx["esg_risk_level"] == "LOW"

    def test_ai_washing_empty(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_ai_washing_context,
        )

        state = _make_empty_state()
        ctx = build_ai_washing_context(state)
        assert ctx["ai_claims_present"] is False
        assert ctx["has_ai_data"] is False

    def test_tariff_empty(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_tariff_context,
        )

        state = _make_empty_state()
        ctx = build_tariff_context(state)
        assert ctx["tariff_risk_level"] == "LOW"

    def test_peer_sca_empty(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_peer_sca_context,
        )

        state = _make_empty_state()
        ctx = build_peer_sca_context(state)
        assert ctx["peer_scas"] == []
        assert ctx["has_peer_sca"] is False


# ---------------------------------------------------------------------------
# 5. Populated state tests
# ---------------------------------------------------------------------------


class TestPopulatedState:
    """Populated state flows through context builders correctly."""

    def test_stock_catalyst_populated(self) -> None:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_catalyst_context,
        )

        state = _make_populated_state()
        ctx = build_stock_catalyst_context(
            state,
            patterns=state.stock_patterns,
            drop_narrative=state.drop_narrative,
        )
        assert len(ctx["stock_patterns"]) == 1
        assert ctx["stock_patterns"][0]["type"] == "earnings_cluster"
        assert "earnings cluster pattern" in ctx["drop_narrative"]

    def test_stock_performance_populated(self) -> None:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_performance_summary,
        )

        state = _make_populated_state()
        ctx = build_stock_performance_summary(
            state,
            multi_horizon_returns=state.multi_horizon_returns,
            analyst_consensus=state.analyst_consensus,
        )
        assert len(ctx["horizons"]) == 6
        assert ctx["has_performance_data"] is True
        assert ctx["analyst"]["buy_count"] == 12

    def test_competitive_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_competitive import (
            build_competitive_landscape_context,
        )

        state = _make_populated_state()
        ctx = build_competitive_landscape_context(state)
        assert len(ctx["comp_peers"]) == 2
        assert len(ctx["comp_moats"]) == 3
        assert ctx["has_competitive_data"] is True
        assert "60% share" in ctx["comp_narrative"]

    def test_esg_populated(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_esg_context,
        )

        state = _make_populated_state()
        ctx = build_esg_context(state)
        assert ctx["esg_risk_level"] == "MEDIUM"
        assert len(ctx["esg_controversies"]) == 1
        assert ctx["has_esg_data"] is True

    def test_ai_washing_populated(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_ai_washing_context,
        )

        state = _make_populated_state()
        ctx = build_ai_washing_context(state)
        assert ctx["ai_claims_present"] is True
        assert ctx["has_ai_data"] is True

    def test_tariff_populated(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_tariff_context,
        )

        state = _make_populated_state()
        ctx = build_tariff_context(state)
        assert ctx["tariff_risk_level"] == "HIGH"
        assert ctx["has_tariff_data"] is True

    def test_peer_sca_populated(self) -> None:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_peer_sca_context,
        )

        state = _make_populated_state()
        ctx = build_peer_sca_context(state)
        assert len(ctx["peer_scas"]) == 1
        assert ctx["has_peer_sca"] is True


# ---------------------------------------------------------------------------
# 6. Explicit field tests
# ---------------------------------------------------------------------------


class TestExplicitStateFields:
    """Verify AnalysisState explicit fields work correctly (not silently dropped)."""

    def test_stock_patterns_field_persists(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.stock_patterns = [{"type": "test"}]
        assert state.stock_patterns == [{"type": "test"}]

    def test_multi_horizon_returns_field_persists(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.multi_horizon_returns = {"1M": -5.0}
        assert state.multi_horizon_returns == {"1M": -5.0}

    def test_analyst_consensus_field_persists(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.analyst_consensus = {"narrative": "test narrative"}
        assert state.analyst_consensus == {"narrative": "test narrative"}

    def test_drop_narrative_field_persists(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.drop_narrative = "test narrative"
        assert state.drop_narrative == "test narrative"


# ---------------------------------------------------------------------------
# 7. Analyst consensus narrative flow test
# ---------------------------------------------------------------------------


class TestAnalystNarrativeFlow:
    """Analyst consensus narrative flows through build_stock_performance_summary."""

    def test_analyst_narrative_in_context(self) -> None:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_performance_summary,
        )

        state = _make_populated_state()
        ctx = build_stock_performance_summary(
            state,
            multi_horizon_returns=state.multi_horizon_returns,
            analyst_consensus=state.analyst_consensus,
        )
        assert "narrative" in ctx["analyst"]
        assert "12 of 18 analysts" in ctx["analyst"]["narrative"]


# ---------------------------------------------------------------------------
# 8. Manifest structure tests
# ---------------------------------------------------------------------------


class TestManifestStructure:
    """Verify manifest has correct Phase 119 structure."""

    @pytest.fixture()
    def manifest(self) -> dict[str, Any]:
        path = Path("src/do_uw/brain/output_manifest.yaml")
        with path.open() as f:
            return yaml.safe_load(f)

    def test_company_operations_section_exists(self, manifest: dict[str, Any]) -> None:
        section_ids = [s["id"] for s in manifest["sections"]]
        assert "company_operations" in section_ids

    def test_company_operations_has_dossier_groups(self, manifest: dict[str, Any]) -> None:
        ops = next(s for s in manifest["sections"] if s["id"] == "company_operations")
        group_ids = [g["id"] for g in ops["groups"]]
        assert "dossier_competitive_landscape" in group_ids
        assert "dossier_what_company_does" in group_ids

    def test_competitive_landscape_not_deferred(self, manifest: dict[str, Any]) -> None:
        ops = next(s for s in manifest["sections"] if s["id"] == "company_operations")
        cl = next(g for g in ops["groups"] if g["id"] == "dossier_competitive_landscape")
        assert cl["render_as"] != "deferred"
        assert cl["render_as"] == "data_table"
        assert "deferred/" not in cl["template"]

    def test_stock_performance_summary_in_market(self, manifest: dict[str, Any]) -> None:
        market = next(s for s in manifest["sections"] if s["id"] == "market_activity")
        group_ids = [g["id"] for g in market["groups"]]
        assert "stock_performance_summary" in group_ids
        assert "stock_drop_catalyst" in group_ids

    def test_no_deferred_competitive_entry(self, manifest: dict[str, Any]) -> None:
        """Ensure no 'render_as: deferred' for competitive landscape."""
        for section in manifest["sections"]:
            for group in section.get("groups", []):
                if group["id"] == "dossier_competitive_landscape":
                    assert group.get("render_as") != "deferred"


# ---------------------------------------------------------------------------
# 9. Template existence tests
# ---------------------------------------------------------------------------


class TestTemplateExistence:
    """All manifest template files exist on disk."""

    _TEMPLATE_BASE = Path("src/do_uw/templates/html")

    def test_competitive_landscape_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/dossier/competitive_landscape.html.j2").exists()

    def test_alt_data_section_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/alt_data.html.j2").exists()

    def test_alt_data_esg_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/alt_data/esg_risk.html.j2").exists()

    def test_alt_data_ai_washing_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/alt_data/ai_washing.html.j2").exists()

    def test_alt_data_tariff_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/alt_data/tariff_exposure.html.j2").exists()

    def test_alt_data_peer_sca_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/alt_data/peer_sca.html.j2").exists()

    def test_stock_performance_summary_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/market/stock_performance_summary.html.j2").exists()

    def test_stock_drop_catalyst_template_exists(self) -> None:
        assert (self._TEMPLATE_BASE / "sections/market/stock_drop_catalyst.html.j2").exists()

    def test_deferred_placeholder_removed(self) -> None:
        assert not (self._TEMPLATE_BASE / "deferred/dossier_competitive_landscape.html.j2").exists()
