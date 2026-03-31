"""Tests for dossier LLM extraction schemas and extraction orchestration.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

import pytest


class TestRevenueModelExtraction:
    """Test RevenueModelExtraction schema instantiation."""

    def test_instantiates_with_all_fields(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

        obj = RevenueModelExtraction(
            model_type="B2B",
            pricing_model="subscription",
            revenue_quality_tier="Tier 1 contractual recurring",
            recognition_method="over time",
            contract_duration="12-36 months",
            net_dollar_retention="115%",
            gross_retention="92%",
            arpu="$1,200/month",
            concentration_risk_summary="Top 3 customers = 45% of revenue",
            regulatory_overlay="FDA regulated medical devices",
            revenue_flow_nodes=[
                {"label": "Customer", "type": "source"},
                {"label": "Platform", "type": "process"},
                {"label": "Revenue", "type": "output"},
            ],
            revenue_flow_edges=[
                {"from_node": "Customer", "to_node": "Platform", "label": "subscription"},
                {"from_node": "Platform", "to_node": "Revenue", "label": "recognized"},
            ],
            revenue_flow_narrative="Subscription revenue recognized ratably over contract term",
            segment_enrichments=[
                {
                    "segment_name": "Cloud Services",
                    "growth_rate": "15%",
                    "rev_rec_method": "over time",
                    "key_risk": "Customer churn",
                },
            ],
        )
        assert obj.model_type == "B2B"
        assert obj.pricing_model == "subscription"
        assert obj.revenue_quality_tier == "Tier 1 contractual recurring"
        assert len(obj.revenue_flow_nodes) == 3
        assert len(obj.revenue_flow_edges) == 2
        assert len(obj.segment_enrichments) == 1

    def test_defaults_to_empty(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

        obj = RevenueModelExtraction()
        assert obj.model_type == ""
        assert obj.revenue_flow_nodes == []
        assert obj.segment_enrichments == []


class TestASC606Extraction:
    """Test ASC606Extraction schema instantiation."""

    def test_instantiates_with_elements(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import (
            ASC606Extraction,
            ASC606ElementExtraction,
        )

        obj = ASC606Extraction(
            elements=[
                ASC606ElementExtraction(
                    element="Performance Obligations",
                    approach="Distinct performance obligations identified per contract",
                    complexity="HIGH",
                    key_judgment="Determining standalone selling prices for bundled arrangements",
                ),
            ],
            billings_vs_revenue_gap="Deferred revenue increased 12% YoY indicating growing backlog",
            rev_rec_complexity_overall="HIGH",
        )
        assert len(obj.elements) == 1
        assert obj.elements[0].element == "Performance Obligations"
        assert obj.rev_rec_complexity_overall == "HIGH"


class TestUnitEconomicsExtraction:
    """Test UnitEconomicsExtraction handles SaaS and non-SaaS metrics."""

    def test_saas_metrics(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import (
            UnitEconomicsExtraction,
            UnitEconomicItem,
        )

        obj = UnitEconomicsExtraction(
            revenue_model_category="RECURRING",
            metrics=[
                UnitEconomicItem(
                    metric_name="Net Dollar Retention",
                    value="115%",
                    source_section="MD&A",
                    is_disclosed=True,
                ),
                UnitEconomicItem(
                    metric_name="ARPU",
                    value="$1,200/month",
                    source_section="Item 7",
                    is_disclosed=True,
                ),
                UnitEconomicItem(
                    metric_name="Churn Rate",
                    value="5% annual",
                    source_section="Item 7",
                    is_disclosed=True,
                ),
            ],
            waterfall_components=[],
        )
        assert obj.revenue_model_category == "RECURRING"
        assert len(obj.metrics) == 3

    def test_non_saas_metrics(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import (
            UnitEconomicsExtraction,
            UnitEconomicItem,
            WaterfallItem,
        )

        obj = UnitEconomicsExtraction(
            revenue_model_category="TRANSACTION",
            metrics=[
                UnitEconomicItem(
                    metric_name="Average Selling Price",
                    value="$45.50",
                    source_section="Item 7",
                    is_disclosed=True,
                ),
                UnitEconomicItem(
                    metric_name="Volume",
                    value="2.3M units",
                    source_section="MD&A",
                    is_disclosed=True,
                ),
                UnitEconomicItem(
                    metric_name="Backlog",
                    value="$890M",
                    source_section="Item 1",
                    is_disclosed=True,
                ),
            ],
            waterfall_components=[
                WaterfallItem(
                    label="Organic Growth",
                    value="+$120M",
                    is_growth_driver=True,
                ),
            ],
        )
        assert obj.revenue_model_category == "TRANSACTION"
        assert len(obj.waterfall_components) == 1


class TestEmergingRiskExtraction:
    """Test EmergingRiskExtraction schema with probability/impact."""

    def test_accepts_risks_with_probability_impact(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import (
            EmergingRiskExtraction,
            EmergingRiskItem,
        )

        obj = EmergingRiskExtraction(
            risks=[
                EmergingRiskItem(
                    risk="AI disruption to consulting revenue",
                    probability="MEDIUM",
                    impact="HIGH",
                    timeframe="12-24 months",
                    scoring_factor_ref="F.7",
                    current_status="MONITORING",
                ),
                EmergingRiskItem(
                    risk="Regulatory changes in data privacy",
                    probability="HIGH",
                    impact="MEDIUM",
                    timeframe="6-12 months",
                    scoring_factor_ref="F.9",
                    current_status="ACTIVE",
                ),
            ],
        )
        assert len(obj.risks) == 2
        assert obj.risks[0].probability == "MEDIUM"
        assert obj.risks[1].current_status == "ACTIVE"


class TestRevenueFlowExtraction:
    """Test revenue flow diagram generation from structured nodes/edges."""

    def test_revenue_flow_nodes_and_edges(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

        obj = RevenueModelExtraction(
            revenue_flow_nodes=[
                {"label": "Enterprise Customers", "type": "source"},
                {"label": "SaaS Platform", "type": "process"},
                {"label": "Annual Subscriptions", "type": "output"},
            ],
            revenue_flow_edges=[
                {"from_node": "Enterprise Customers", "to_node": "SaaS Platform", "label": "contracts"},
                {"from_node": "SaaS Platform", "to_node": "Annual Subscriptions", "label": "recognized ratably"},
            ],
            revenue_flow_narrative="Enterprise customers sign annual contracts; revenue recognized ratably over term",
        )
        assert len(obj.revenue_flow_nodes) == 3
        assert obj.revenue_flow_edges[0]["from_node"] == "Enterprise Customers"
        assert obj.revenue_flow_narrative != ""


class TestWaterfallExtraction:
    """Test waterfall decomposition components."""

    def test_accepts_waterfall_components(self) -> None:
        from do_uw.stages.extract.llm.schemas.dossier import (
            UnitEconomicsExtraction,
            WaterfallItem,
        )

        obj = UnitEconomicsExtraction(
            revenue_model_category="HYBRID",
            metrics=[],
            waterfall_components=[
                WaterfallItem(label="Prior Year Revenue", value="$5.2B", is_growth_driver=False),
                WaterfallItem(label="Organic Growth", value="+$420M", is_growth_driver=True),
                WaterfallItem(label="Acquisitions", value="+$180M", is_growth_driver=True),
                WaterfallItem(label="FX Impact", value="-$90M", is_growth_driver=False),
                WaterfallItem(label="Current Year Revenue", value="$5.71B", is_growth_driver=False),
            ],
        )
        assert len(obj.waterfall_components) == 5
        drivers = [w for w in obj.waterfall_components if w.is_growth_driver]
        assert len(drivers) == 2


# ---------------------------------------------------------------------------
# Extraction orchestration tests (Task 2)
# ---------------------------------------------------------------------------


def _make_minimal_state() -> "AnalysisState":
    """Create a minimal AnalysisState for testing extraction."""
    from do_uw.models.company import CompanyIdentity, CompanyProfile
    from do_uw.models.state import AnalysisState

    identity = CompanyIdentity(ticker="TEST")
    company = CompanyProfile(identity=identity)
    state = AnalysisState(ticker="TEST", company=company)
    return state


class TestExtractDossier:
    """Test the main extract_dossier orchestration function."""

    def test_extract_dossier_importable(self) -> None:
        from do_uw.stages.extract.dossier_extraction import extract_dossier

        assert callable(extract_dossier)

    def test_extract_dossier_with_minimal_state_no_crash(self) -> None:
        """extract_dossier with no filing data populates defaults without crashing."""
        from do_uw.stages.extract.dossier_extraction import extract_dossier

        state = _make_minimal_state()
        extract_dossier(state)

        # Should not crash; dossier should still exist with defaults
        assert state.dossier is not None
        assert state.dossier.revenue_card == []
        assert state.dossier.asc_606_elements == []
        assert state.dossier.emerging_risks == []

    def test_handles_missing_filing_text_gracefully(self) -> None:
        """When no filing text available, extraction completes with empty results."""
        from do_uw.stages.extract.dossier_extraction import extract_dossier

        state = _make_minimal_state()
        extract_dossier(state)

        assert state.dossier.extraction_confidence == "MEDIUM"  # default
        assert state.dossier.source_filings == []


class TestExtractRevenueModel:
    """Test revenue model extraction sub-function."""

    def test_consumes_existing_revenue_segments(self) -> None:
        """Revenue model extraction consumes state.company.revenue_segments."""
        from do_uw.stages.extract.dossier_extraction import _extract_revenue_model
        from do_uw.models.common import Confidence, SourcedValue
        from datetime import UTC, datetime

        state = _make_minimal_state()

        # Add revenue segments to company
        state.company.revenue_segments = [
            SourcedValue(
                value={"name": "Cloud", "percentage": "60%"},
                source="10-K",
                confidence=Confidence.HIGH,
                as_of=datetime.now(tz=UTC),
            ),
            SourcedValue(
                value={"name": "Licensing", "percentage": "40%"},
                source="10-K",
                confidence=Confidence.HIGH,
                as_of=datetime.now(tz=UTC),
            ),
        ]

        # Call with empty filing text -- LLM extraction returns None
        # but existing segments should still be processed
        _extract_revenue_model(state, "", "test-accession")

        # No LLM extraction, so no segment enrichment, but function shouldn't crash
        # (LLM returns None, so segments won't be enriched but no exception)


class TestBuildRevenueFlowText:
    """Test revenue flow diagram text generation from nodes/edges."""

    def test_generates_readable_text(self) -> None:
        from do_uw.stages.extract.dossier_extraction import _build_revenue_flow_text

        nodes = [
            {"label": "Enterprise Customers", "type": "source"},
            {"label": "Sales Team", "type": "process"},
            {"label": "Subscription Revenue", "type": "output"},
        ]
        edges = [
            {"from_node": "Enterprise Customers", "to_node": "Sales Team", "label": "contracts"},
            {"from_node": "Sales Team", "to_node": "Subscription Revenue", "label": "recognized"},
        ]

        text = _build_revenue_flow_text(nodes, edges)
        assert "Enterprise Customers" in text
        assert "Sales Team" in text
        assert "Subscription Revenue" in text
        assert "->" in text

    def test_empty_nodes_returns_empty(self) -> None:
        from do_uw.stages.extract.dossier_extraction import _build_revenue_flow_text

        assert _build_revenue_flow_text([], []) == ""


class TestGetAnalyticalContext:
    """Test QUAL-03 analytical context builder."""

    def test_returns_context_dict(self) -> None:
        from do_uw.stages.extract.dossier_extraction import _get_analytical_context

        state = _make_minimal_state()
        ctx = _get_analytical_context(state)

        assert "company_name" in ctx
        assert "ticker" in ctx
        assert ctx["ticker"] == "TEST"
        assert "sector" in ctx
        assert "revenue" in ctx
        assert "revenue_model_type" in ctx
        assert "scoring_summary" in ctx


class TestBuildRevenueCard:
    """Test revenue model card construction."""

    def test_builds_card_from_extraction(self) -> None:
        from do_uw.stages.extract.dossier_extraction import _build_revenue_card
        from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

        extraction = RevenueModelExtraction(
            model_type="B2B",
            pricing_model="subscription",
            revenue_quality_tier="Tier 1 contractual recurring",
            recognition_method="over time",
            contract_duration="12-36 months",
        )

        rows = _build_revenue_card(extraction)
        assert len(rows) >= 4  # At least model_type, pricing, quality, recognition
        labels = [r.attribute for r in rows]
        assert "Model Type" in labels
        assert "Pricing Model" in labels

    def test_skips_empty_fields(self) -> None:
        from do_uw.stages.extract.dossier_extraction import _build_revenue_card
        from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

        extraction = RevenueModelExtraction()  # All defaults (empty)
        rows = _build_revenue_card(extraction)
        assert rows == []
