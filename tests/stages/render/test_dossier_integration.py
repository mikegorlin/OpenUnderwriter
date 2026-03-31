"""Integration tests for Phase 118 dossier pipeline wiring.

Verifies that:
1. html_context_assembly.py contains all 8 dossier context builder imports
2. Context builders produce correct keys with populated/empty dossier data
3. Output manifest contains intelligence_dossier section with 9 groups
4. build_html_context includes all dossier context keys

Phase 118-06: Revenue Model & Company Intelligence Dossier Integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from do_uw.models.dossier import (
    ASC606Element,
    DossierData,
    EmergingRisk,
    RevenueModelCardRow,
    RevenueSegmentDossier,
    UnitEconomicMetric,
    WaterfallRow,
)
from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_empty_state() -> AnalysisState:
    """Build minimal AnalysisState with default (empty) DossierData."""
    return AnalysisState(ticker="TEST")


def _make_populated_state() -> AnalysisState:
    """Build AnalysisState with fully populated DossierData."""
    state = AnalysisState(ticker="TEST")
    state.dossier = DossierData(
        business_description_plain="Acme Corp manufactures widgets.",
        core_do_exposure="Concentrated revenue from 3 contracts.",
        revenue_flow_diagram="Customer --> Revenue",
        revenue_flow_narrative="60% recurring, 40% hardware.",
        revenue_card=[
            RevenueModelCardRow(
                attribute="Model Type",
                value="B2B Contracts",
                do_risk="Deferred recognition risk.",
                risk_level="MEDIUM",
            ),
        ],
        segment_dossiers=[
            RevenueSegmentDossier(
                segment_name="Aerospace",
                revenue_pct="45%",
                growth_rate="+8.2%",
                rev_rec_method="Percentage of completion",
                do_exposure="SCA trigger if revised.",
                risk_level="MEDIUM",
            ),
        ],
        unit_economics=[
            UnitEconomicMetric(
                metric="LTV:CAC",
                value="3.2x",
                benchmark=">3x",
                assessment="Healthy",
                do_risk="Low churn risk.",
            ),
        ],
        unit_economics_narrative="Unit economics are healthy.",
        waterfall_rows=[
            WaterfallRow(
                label="Base Revenue",
                value="$1.2B",
                delta="+5%",
                narrative="Organic growth.",
            ),
        ],
        waterfall_narrative="Revenue grew 5% YoY.",
        emerging_risks=[
            EmergingRisk(
                risk="Supply chain disruption",
                probability="MEDIUM",
                impact="HIGH",
                timeframe="12-24 months",
                do_factor="F.5 operational risk",
                status="MONITORING",
            ),
        ],
        asc_606_elements=[
            ASC606Element(
                element="Performance Obligations",
                approach="Multiple deliverables",
                complexity="MEDIUM",
                do_risk="Unbundling risk.",
            ),
        ],
        billings_vs_revenue_narrative="Billings exceed revenue by 8%.",
    )
    return state


def _get_source_file(name: str) -> str:
    """Read a source file and return its contents."""
    base = Path(__file__).resolve().parent.parent.parent.parent / "src" / "do_uw"
    return (base / name).read_text()


def _get_manifest_path() -> Path:
    """Get the output manifest YAML path."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "brain"
        / "output_manifest.yaml"
    )


# ---------------------------------------------------------------------------
# Source code wiring verification
# ---------------------------------------------------------------------------


DOSSIER_CONTEXT_KEYS = [
    "dossier_what",
    "dossier_flows",
    "dossier_card",
    "dossier_segments",
    "dossier_unit",
    "dossier_waterfall",
    "dossier_risks",
    "dossier_asc",
]

DOSSIER_BUILDER_NAMES = [
    "extract_what_company_does",
    "extract_money_flows",
    "extract_revenue_model_card",
    "extract_revenue_segments",
    "extract_unit_economics",
    "extract_revenue_waterfall",
    "extract_emerging_risks",
    "extract_asc_606",
]


class TestContextAssemblyWiring:
    """Verify html_context_assembly.py has all 8 dossier context builder wirings."""

    def _get_assembly_source(self) -> str:
        return _get_source_file("stages/render/html_context_assembly.py")

    @pytest.mark.parametrize("builder_name", DOSSIER_BUILDER_NAMES)
    def test_imports_dossier_builder(self, builder_name: str) -> None:
        """Assembly imports each dossier context builder function."""
        src = self._get_assembly_source()
        assert builder_name in src, f"Missing import: {builder_name}"

    @pytest.mark.parametrize("key", DOSSIER_CONTEXT_KEYS)
    def test_sets_dossier_context_key(self, key: str) -> None:
        """Assembly assigns context['{key}'] for each dossier builder."""
        src = self._get_assembly_source()
        assert f'context["{key}"]' in src, f"Missing context key: {key}"

    def test_has_eight_dossier_try_blocks(self) -> None:
        """Assembly has at least 8 dossier-related try/except blocks."""
        src = self._get_assembly_source()
        # Count lines containing "Dossier" within try/except context
        dossier_context_assigns = [
            line
            for line in src.splitlines()
            if 'context["dossier_' in line and "=" in line
        ]
        assert len(dossier_context_assigns) >= 16, (
            f"Expected >=16 dossier context assignments (8 success + 8 fallback), "
            f"found {len(dossier_context_assigns)}"
        )


# ---------------------------------------------------------------------------
# Context builder functional tests with empty state
# ---------------------------------------------------------------------------


class TestContextBuildersEmptyState:
    """Verify context builders produce _available=False with empty dossier."""

    def test_what_company_does_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_what_company_does import (
            extract_what_company_does,
        )
        result = extract_what_company_does(_make_empty_state(), signal_results={})
        assert result["what_company_does_available"] is False

    def test_money_flows_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_money_flows import (
            extract_money_flows,
        )
        result = extract_money_flows(_make_empty_state(), signal_results={})
        assert result["money_flows_available"] is False

    def test_revenue_card_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_revenue_card import (
            extract_revenue_model_card,
        )
        result = extract_revenue_model_card(_make_empty_state(), signal_results={})
        assert result["revenue_card_available"] is False

    def test_segments_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_segments import (
            extract_revenue_segments,
        )
        result = extract_revenue_segments(_make_empty_state(), signal_results={})
        assert result["segments_available"] is False

    def test_unit_economics_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_unit_economics import (
            extract_unit_economics,
        )
        result = extract_unit_economics(_make_empty_state(), signal_results={})
        assert result["unit_economics_available"] is False

    def test_waterfall_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_waterfall import (
            extract_revenue_waterfall,
        )
        result = extract_revenue_waterfall(_make_empty_state(), signal_results={})
        assert result["waterfall_available"] is False

    def test_emerging_risks_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_emerging_risks import (
            extract_emerging_risks,
        )
        result = extract_emerging_risks(_make_empty_state(), signal_results={})
        assert result["emerging_risks_available"] is False

    def test_asc_606_empty(self) -> None:
        from do_uw.stages.render.context_builders.dossier_asc606 import (
            extract_asc_606,
        )
        result = extract_asc_606(_make_empty_state(), signal_results={})
        assert result["asc_606_available"] is False


# ---------------------------------------------------------------------------
# Context builder functional tests with populated state
# ---------------------------------------------------------------------------


class TestContextBuildersPopulatedState:
    """Verify context builders produce _available=True with populated dossier."""

    def test_what_company_does_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_what_company_does import (
            extract_what_company_does,
        )
        result = extract_what_company_does(_make_populated_state(), signal_results={})
        assert result["what_company_does_available"] is True

    def test_money_flows_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_money_flows import (
            extract_money_flows,
        )
        result = extract_money_flows(_make_populated_state(), signal_results={})
        assert result["money_flows_available"] is True

    def test_revenue_card_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_revenue_card import (
            extract_revenue_model_card,
        )
        result = extract_revenue_model_card(_make_populated_state(), signal_results={})
        assert result["revenue_card_available"] is True
        assert len(result["rows"]) > 0
        assert "row_class" in result["rows"][0]

    def test_segments_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_segments import (
            extract_revenue_segments,
        )
        result = extract_revenue_segments(_make_populated_state(), signal_results={})
        assert result["segments_available"] is True

    def test_unit_economics_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_unit_economics import (
            extract_unit_economics,
        )
        result = extract_unit_economics(_make_populated_state(), signal_results={})
        assert result["unit_economics_available"] is True

    def test_waterfall_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_waterfall import (
            extract_revenue_waterfall,
        )
        result = extract_revenue_waterfall(_make_populated_state(), signal_results={})
        assert result["waterfall_available"] is True

    def test_emerging_risks_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_emerging_risks import (
            extract_emerging_risks,
        )
        result = extract_emerging_risks(_make_populated_state(), signal_results={})
        assert result["emerging_risks_available"] is True
        assert len(result["risks"]) > 0
        assert "probability_class" in result["risks"][0]

    def test_asc_606_populated(self) -> None:
        from do_uw.stages.render.context_builders.dossier_asc606 import (
            extract_asc_606,
        )
        result = extract_asc_606(_make_populated_state(), signal_results={})
        assert result["asc_606_available"] is True


# ---------------------------------------------------------------------------
# Partial data handling
# ---------------------------------------------------------------------------


class TestPartialData:
    """Verify context builders handle partial dossier data gracefully."""

    def test_partial_state_no_crash(self) -> None:
        """build_html_context does not crash when dossier has only some data."""
        from do_uw.stages.render.html_context_assembly import build_html_context

        state = AnalysisState(ticker="TEST")
        # Only populate revenue_card, leave everything else empty
        state.dossier.revenue_card = [
            RevenueModelCardRow(
                attribute="Test",
                value="Test Value",
                do_risk="Test risk",
                risk_level="LOW",
            ),
        ]
        # Should not raise
        context = build_html_context(state)
        # Revenue card should be available
        assert context["dossier_card"]["revenue_card_available"] is True
        # Others should be unavailable
        assert context["dossier_what"]["what_company_does_available"] is False


# ---------------------------------------------------------------------------
# Output manifest verification
# ---------------------------------------------------------------------------


class TestOutputManifest:
    """Verify output_manifest.yaml has dossier groups in company_operations section."""

    def _load_manifest(self) -> dict[str, Any]:
        path = _get_manifest_path()
        with path.open() as f:
            return yaml.safe_load(f)

    def test_manifest_contains_company_operations(self) -> None:
        """Manifest has company_operations section (merged from business_profile + intelligence_dossier)."""
        m = self._load_manifest()
        section_ids = [s["id"] for s in m["sections"]]
        assert "company_operations" in section_ids

    def test_manifest_company_operations_has_dossier_groups(self) -> None:
        """company_operations section contains all 9 dossier groups."""
        m = self._load_manifest()
        ops = next(s for s in m["sections"] if s["id"] == "company_operations")
        group_ids = {g["id"] for g in ops["groups"]}
        dossier_groups = {
            "dossier_what_company_does",
            "dossier_money_flows",
            "dossier_revenue_model_card",
            "dossier_revenue_segments",
            "dossier_unit_economics",
            "dossier_revenue_waterfall",
            "dossier_competitive_landscape",
            "dossier_emerging_risk_radar",
            "dossier_asc_606",
        }
        assert dossier_groups.issubset(group_ids)

    def test_manifest_competitive_landscape_active(self) -> None:
        """dossier_competitive_landscape group is active (Phase 119 activated it)."""
        m = self._load_manifest()
        ops = next(s for s in m["sections"] if s["id"] == "company_operations")
        cl = next(g for g in ops["groups"] if g["id"] == "dossier_competitive_landscape")
        assert cl["render_as"] == "data_table"
        assert "deferred" not in cl["template"]

    def test_manifest_dossier_group_ids(self) -> None:
        """company_operations section has all expected dossier group IDs."""
        m = self._load_manifest()
        ops = next(s for s in m["sections"] if s["id"] == "company_operations")
        group_ids = {g["id"] for g in ops["groups"]}
        expected_dossier = {
            "dossier_what_company_does",
            "dossier_money_flows",
            "dossier_revenue_model_card",
            "dossier_revenue_segments",
            "dossier_unit_economics",
            "dossier_revenue_waterfall",
            "dossier_competitive_landscape",
            "dossier_emerging_risk_radar",
            "dossier_asc_606",
        }
        assert expected_dossier.issubset(group_ids)
