"""Tests for dossier context builders.

Verifies all 8 context builders produce correct output shapes,
CSS class mappings, availability flags, and handle empty data gracefully.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

import pytest

from do_uw.models.dossier import (
    ASC606Element,
    ConcentrationDimension,
    DossierData,
    EmergingRisk,
    RevenueModelCardRow,
    RevenueSegmentDossier,
    UnitEconomicMetric,
    WaterfallRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.dossier_asc606 import extract_asc_606
from do_uw.stages.render.context_builders.dossier_emerging_risks import (
    extract_emerging_risks,
)
from do_uw.stages.render.context_builders.dossier_money_flows import (
    extract_money_flows,
)
from do_uw.stages.render.context_builders.dossier_revenue_card import (
    extract_revenue_model_card,
)
from do_uw.stages.render.context_builders.dossier_segments import (
    extract_revenue_segments,
)
from do_uw.stages.render.context_builders.dossier_unit_economics import (
    extract_unit_economics,
)
from do_uw.stages.render.context_builders.dossier_waterfall import (
    extract_revenue_waterfall,
)
from do_uw.stages.render.context_builders.dossier_what_company_does import (
    extract_what_company_does,
)


def _make_populated_state() -> AnalysisState:
    """Create an AnalysisState with fully populated DossierData."""
    dossier = DossierData(
        business_description_plain="Acme Corp manufactures industrial widgets for aerospace customers.",
        core_do_exposure="Concentrated customer base creates revenue cliff risk; single-product dependency.",
        revenue_flow_diagram="Customer -> Contract -> Delivery -> Invoice -> Payment",
        revenue_flow_narrative="Revenue flows through long-term contracts with milestone billing.",
        revenue_card=[
            RevenueModelCardRow(
                attribute="Model Type",
                value="Subscription + Usage",
                do_risk="Recurring revenue may mask churn risk",
                risk_level="MEDIUM",
            ),
            RevenueModelCardRow(
                attribute="Pricing",
                value="Tiered per-seat",
                do_risk="Price increases may trigger customer attrition",
                risk_level="HIGH",
            ),
            RevenueModelCardRow(
                attribute="Contract Length",
                value="Annual",
                do_risk="Low switching cost",
                risk_level="LOW",
            ),
        ],
        segment_dossiers=[
            RevenueSegmentDossier(
                segment_name="Aerospace",
                revenue_pct="45%",
                growth_rate="8.2%",
                rev_rec_method="Percentage of completion",
                do_exposure="Defense contract concentration risk",
                risk_level="HIGH",
            ),
            RevenueSegmentDossier(
                segment_name="Commercial",
                revenue_pct="35%",
                growth_rate="3.1%",
                rev_rec_method="Point-in-time delivery",
                do_exposure="Cyclical demand exposure",
                risk_level="MEDIUM",
            ),
            RevenueSegmentDossier(
                segment_name="Aftermarket",
                revenue_pct="20%",
                growth_rate="12.5%",
                rev_rec_method="Point-in-time delivery",
                do_exposure="Low risk recurring services",
                risk_level="LOW",
            ),
        ],
        concentration_dimensions=[
            ConcentrationDimension(
                dimension="Customer",
                metric="Top 3 = 65%",
                risk_level="HIGH",
                do_implication="Revenue cliff risk if key customer lost",
            ),
            ConcentrationDimension(
                dimension="Geographic",
                metric="US = 80%",
                risk_level="MEDIUM",
                do_implication="Domestic regulatory exposure",
            ),
            ConcentrationDimension(
                dimension="Product",
                metric="Widgets = 90%",
                risk_level="HIGH",
                do_implication="Single product dependency",
            ),
            ConcentrationDimension(
                dimension="Channel",
                metric="Direct = 70%",
                risk_level="MEDIUM",
                do_implication="Channel disruption risk",
            ),
            ConcentrationDimension(
                dimension="Payer",
                metric="Government = 45%",
                risk_level="HIGH",
                do_implication="Budget sequestration risk",
            ),
        ],
        unit_economics=[
            UnitEconomicMetric(
                metric="LTV:CAC Ratio",
                value="3.2x",
                benchmark=">3.0x",
                assessment="Above benchmark",
                do_risk="Sustainable acquisition economics",
            ),
            UnitEconomicMetric(
                metric="Gross Margin",
                value="42%",
                benchmark="40-50%",
                assessment="Within range",
                do_risk="Margin pressure from input costs",
            ),
            UnitEconomicMetric(
                metric="Payback Period",
                value="18 months",
                benchmark="<24 months",
                assessment="Healthy",
                do_risk="Manageable cash cycle",
            ),
        ],
        unit_economics_narrative="Unit economics are healthy with LTV:CAC above industry benchmark.",
        waterfall_rows=[
            WaterfallRow(
                label="Prior Year Revenue",
                value="$1.2B",
                delta="",
                narrative="Starting base from FY2024",
            ),
            WaterfallRow(
                label="Organic Growth",
                value="+$120M",
                delta="+10%",
                narrative="Driven by aerospace contract wins",
            ),
        ],
        waterfall_narrative="Revenue growth primarily organic, driven by new aerospace contracts.",
        emerging_risks=[
            EmergingRisk(
                risk="Tariff exposure on imported components",
                probability="HIGH",
                impact="MEDIUM",
                timeframe="6-12 months",
                do_factor="Supply chain disruption may impact guidance",
                status="ACTIVE",
            ),
            EmergingRisk(
                risk="AI automation displacing manual assembly",
                probability="MEDIUM",
                impact="HIGH",
                timeframe="24-36 months",
                do_factor="Workforce restructuring litigation risk",
                status="MONITORING",
            ),
            EmergingRisk(
                risk="Customer consolidation in defense sector",
                probability="LOW",
                impact="HIGH",
                timeframe="12-24 months",
                do_factor="Contract renegotiation under monopsony",
                status="MONITORING",
            ),
        ],
        asc_606_elements=[
            ASC606Element(
                element="Performance Obligations",
                approach="Distinct deliverables per contract",
                complexity="MEDIUM",
                do_risk="Multi-element arrangement complexity",
            ),
            ASC606Element(
                element="Variable Consideration",
                approach="Expected value method for rebates",
                complexity="HIGH",
                do_risk="Revenue estimation uncertainty",
            ),
        ],
        billings_vs_revenue_narrative="Billings exceeded recognized revenue by 8% due to advance payments.",
    )
    return AnalysisState(ticker="TEST", dossier=dossier)


def _make_empty_state() -> AnalysisState:
    """Create an AnalysisState with default (empty) DossierData."""
    return AnalysisState(ticker="TEST")


# ------------------------------------------------------------------
# Test 1: what_company_does with populated data
# ------------------------------------------------------------------
class TestWhatCompanyDoes:
    def test_populated_returns_available(self) -> None:
        state = _make_populated_state()
        result = extract_what_company_does(state)
        assert result["what_company_does_available"] is True
        assert "Acme Corp" in result["business_description"]
        assert "Concentrated customer base" in result["core_do_exposure"]

    def test_empty_returns_unavailable(self) -> None:
        state = _make_empty_state()
        result = extract_what_company_does(state)
        assert result["what_company_does_available"] is False


# ------------------------------------------------------------------
# Test 3-4: revenue_model_card
# ------------------------------------------------------------------
class TestRevenueModelCard:
    def test_returns_formatted_rows(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_model_card(state)
        assert result["revenue_card_available"] is True
        assert len(result["rows"]) == 3
        # Check row keys
        row = result["rows"][0]
        assert "attribute" in row
        assert "value" in row
        assert "do_risk" in row
        assert "row_class" in row

    def test_high_risk_produces_css_class(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_model_card(state)
        # Second row has risk_level=HIGH
        high_row = result["rows"][1]
        assert high_row["row_class"] == "risk-high"

    def test_low_risk_produces_css_class(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_model_card(state)
        low_row = result["rows"][2]
        assert low_row["row_class"] == "risk-low"

    def test_medium_risk_produces_css_class(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_model_card(state)
        med_row = result["rows"][0]
        assert med_row["row_class"] == "risk-medium"


# ------------------------------------------------------------------
# Test 5: revenue_segments with segments + concentration
# ------------------------------------------------------------------
class TestRevenueSegments:
    def test_segments_and_concentration_available(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_segments(state)
        assert result["segments_available"] is True
        assert result["concentration_available"] is True
        assert len(result["segments"]) == 3
        assert len(result["concentration_dimensions"]) == 5

    def test_segment_row_has_expected_keys(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_segments(state)
        seg = result["segments"][0]
        for key in ("segment_name", "revenue_pct", "growth_rate", "rev_rec_method", "do_exposure", "row_class"):
            assert key in seg

    def test_segment_css_class_mapping(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_segments(state)
        assert result["segments"][0]["row_class"] == "risk-high"  # Aerospace = HIGH
        assert result["segments"][1]["row_class"] == "risk-medium"  # Commercial = MEDIUM
        assert result["segments"][2]["row_class"] == "risk-low"  # Aftermarket = LOW

    def test_concentration_has_row_class(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_segments(state)
        dim = result["concentration_dimensions"][0]
        assert dim["row_class"] == "risk-high"


# ------------------------------------------------------------------
# Test 6: money_flows
# ------------------------------------------------------------------
class TestMoneyFlows:
    def test_populated_returns_available(self) -> None:
        state = _make_populated_state()
        result = extract_money_flows(state)
        assert result["money_flows_available"] is True
        assert "Contract" in result["flow_diagram"]
        assert "milestone" in result["flow_narrative"]


# ------------------------------------------------------------------
# Test 7: unit_economics
# ------------------------------------------------------------------
class TestUnitEconomics:
    def test_returns_formatted_metrics(self) -> None:
        state = _make_populated_state()
        result = extract_unit_economics(state)
        assert result["unit_economics_available"] is True
        assert len(result["metrics"]) == 3
        m = result["metrics"][0]
        for key in ("metric", "value", "benchmark", "assessment", "do_risk"):
            assert key in m
        assert "narrative" in result


# ------------------------------------------------------------------
# Test 8: revenue_waterfall
# ------------------------------------------------------------------
class TestRevenueWaterfall:
    def test_returns_formatted_waterfall(self) -> None:
        state = _make_populated_state()
        result = extract_revenue_waterfall(state)
        assert result["waterfall_available"] is True
        assert len(result["rows"]) == 2
        row = result["rows"][0]
        for key in ("label", "value", "delta", "narrative"):
            assert key in row
        assert "narrative" in result


# ------------------------------------------------------------------
# Test 9: emerging_risks CSS class mapping
# ------------------------------------------------------------------
class TestEmergingRisks:
    def test_probability_css_class(self) -> None:
        state = _make_populated_state()
        result = extract_emerging_risks(state)
        assert result["emerging_risks_available"] is True
        assert len(result["risks"]) == 3
        assert result["risks"][0]["probability_class"] == "risk-high"
        assert result["risks"][1]["probability_class"] == "risk-medium"
        assert result["risks"][2]["probability_class"] == "risk-low"

    def test_risk_has_expected_keys(self) -> None:
        state = _make_populated_state()
        result = extract_emerging_risks(state)
        risk = result["risks"][0]
        for key in ("risk", "probability", "impact", "timeframe", "do_factor", "status", "probability_class"):
            assert key in risk


# ------------------------------------------------------------------
# Test 10: asc_606 complexity CSS class
# ------------------------------------------------------------------
class TestASC606:
    def test_high_complexity_css_class(self) -> None:
        state = _make_populated_state()
        result = extract_asc_606(state)
        assert result["asc_606_available"] is True
        assert len(result["elements"]) == 2
        # Second element has complexity=HIGH
        assert result["elements"][1]["complexity_class"] == "risk-high"
        # First element has complexity=MEDIUM
        assert result["elements"][0]["complexity_class"] == "risk-medium"

    def test_billings_narrative_present(self) -> None:
        state = _make_populated_state()
        result = extract_asc_606(state)
        assert "billings_narrative" in result
        assert "8%" in result["billings_narrative"]


# ------------------------------------------------------------------
# Test 11: All 8 builders return available=False when empty
# ------------------------------------------------------------------
_BUILDER_PARAMS = [
    ("what_company_does", extract_what_company_does, "what_company_does_available"),
    ("money_flows", extract_money_flows, "money_flows_available"),
    ("revenue_card", extract_revenue_model_card, "revenue_card_available"),
    ("unit_economics", extract_unit_economics, "unit_economics_available"),
    ("waterfall", extract_revenue_waterfall, "waterfall_available"),
    ("emerging_risks", extract_emerging_risks, "emerging_risks_available"),
    ("asc_606", extract_asc_606, "asc_606_available"),
]


@pytest.mark.parametrize("name,builder,key", _BUILDER_PARAMS, ids=[p[0] for p in _BUILDER_PARAMS])
def test_empty_dossier_returns_unavailable(name: str, builder, key: str) -> None:  # noqa: ANN001
    state = _make_empty_state()
    result = builder(state)
    assert result[key] is False


def test_segments_empty_returns_unavailable() -> None:
    state = _make_empty_state()
    result = extract_revenue_segments(state)
    assert result["segments_available"] is False
    assert result["concentration_available"] is False


# ------------------------------------------------------------------
# Test 12: No builder raises on None signal_results
# ------------------------------------------------------------------
_ALL_BUILDERS = [
    extract_what_company_does,
    extract_money_flows,
    extract_revenue_model_card,
    extract_revenue_segments,
    extract_unit_economics,
    extract_revenue_waterfall,
    extract_emerging_risks,
    extract_asc_606,
]


@pytest.mark.parametrize("builder", _ALL_BUILDERS, ids=[b.__name__ for b in _ALL_BUILDERS])
def test_no_exception_with_none_signal_results(builder) -> None:  # noqa: ANN001
    state = _make_populated_state()
    # Should not raise with signal_results=None (the default)
    result = builder(state)
    assert isinstance(result, dict)
