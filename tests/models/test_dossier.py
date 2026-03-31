"""Tests for Company Intelligence Dossier Pydantic models.

Phase 118: Revenue Model & Company Intelligence Dossier
Plan 01: Data model definitions and AnalysisState wiring.
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


class TestDossierDataDefaults:
    """Test 1: DossierData() instantiates with all defaults."""

    def test_instantiates_with_defaults(self) -> None:
        d = DossierData()
        # String fields default to ""
        assert d.business_description_plain == ""
        assert d.core_do_exposure == ""
        assert d.revenue_flow_diagram == ""
        assert d.revenue_flow_narrative == ""
        assert d.unit_economics_narrative == ""
        assert d.waterfall_narrative == ""
        assert d.billings_vs_revenue_narrative == ""
        assert d.extraction_confidence == "MEDIUM"
        # List fields default to empty
        assert d.revenue_card == []
        assert d.segment_dossiers == []
        assert d.concentration_dimensions == []
        assert d.unit_economics == []
        assert d.waterfall_rows == []
        assert d.emerging_risks == []
        assert d.asc_606_elements == []
        assert d.source_filings == []


class TestDossierDataSerialization:
    """Test 2: DossierData with populated revenue_card serializes to dict and back."""

    def test_round_trip_serialization(self) -> None:
        row = RevenueModelCardRow(
            attribute="Model Type",
            value="B2B SaaS",
            do_risk="Recurring revenue reduces miss risk",
            risk_level="LOW",
        )
        d = DossierData(revenue_card=[row])
        data = d.model_dump()
        restored = DossierData.model_validate(data)
        assert len(restored.revenue_card) == 1
        assert restored.revenue_card[0].attribute == "Model Type"
        assert restored.revenue_card[0].value == "B2B SaaS"
        assert restored.revenue_card[0].do_risk == "Recurring revenue reduces miss risk"
        assert restored.revenue_card[0].risk_level == "LOW"


class TestRevenueModelCardRow:
    """Test 3: RevenueModelCardRow accepts attribute, value, do_risk, risk_level."""

    def test_full_construction(self) -> None:
        row = RevenueModelCardRow(
            attribute="Model Type",
            value="B2B SaaS",
            do_risk="Recurring revenue reduces SCA exposure from revenue miss claims",
            risk_level="HIGH",
        )
        assert row.attribute == "Model Type"
        assert row.value == "B2B SaaS"
        assert row.do_risk == "Recurring revenue reduces SCA exposure from revenue miss claims"
        assert row.risk_level == "HIGH"

    def test_defaults(self) -> None:
        row = RevenueModelCardRow()
        assert row.attribute == ""
        assert row.value == ""
        assert row.do_risk == ""
        assert row.risk_level == "LOW"


class TestConcentrationDimension:
    """Test 4: ConcentrationDimension accepts all 5 dimension types."""

    @pytest.mark.parametrize(
        "dimension",
        ["Customer", "Geographic", "Product", "Channel", "Payer"],
    )
    def test_dimension_types(self, dimension: str) -> None:
        cd = ConcentrationDimension(
            dimension=dimension,
            metric="Top 3 = 65%",
            risk_level="HIGH",
            do_implication=f"{dimension} concentration creates SCA surface",
        )
        assert cd.dimension == dimension
        assert cd.metric == "Top 3 = 65%"
        assert cd.risk_level == "HIGH"
        assert dimension in cd.do_implication

    def test_defaults(self) -> None:
        cd = ConcentrationDimension()
        assert cd.dimension == ""
        assert cd.risk_level == "LOW"


class TestEmergingRisk:
    """Test 5: EmergingRisk accepts probability/impact/timeframe/do_factor/status."""

    def test_full_construction(self) -> None:
        er = EmergingRisk(
            risk="AI commoditization of SaaS tools",
            probability="MEDIUM",
            impact="HIGH",
            timeframe="12-24 months",
            do_factor="Revenue miss from competitive disruption => 10b-5 exposure",
            status="MONITORING",
        )
        assert er.risk == "AI commoditization of SaaS tools"
        assert er.probability == "MEDIUM"
        assert er.impact == "HIGH"
        assert er.timeframe == "12-24 months"
        assert er.do_factor == "Revenue miss from competitive disruption => 10b-5 exposure"
        assert er.status == "MONITORING"


class TestASC606Element:
    """Test 6: ASC606Element accepts element/approach/complexity/do_risk."""

    def test_full_construction(self) -> None:
        el = ASC606Element(
            element="Performance Obligations",
            approach="Distinct deliverables identified per contract",
            complexity="MEDIUM",
            do_risk="Multiple POs increase restatement surface",
        )
        assert el.element == "Performance Obligations"
        assert el.approach == "Distinct deliverables identified per contract"
        assert el.complexity == "MEDIUM"
        assert el.do_risk == "Multiple POs increase restatement surface"

    def test_defaults(self) -> None:
        el = ASC606Element()
        assert el.complexity == "LOW"


class TestUnitEconomicMetric:
    """Test 7: UnitEconomicMetric accepts metric/value/benchmark/assessment/do_risk."""

    def test_full_construction(self) -> None:
        m = UnitEconomicMetric(
            metric="LTV:CAC Ratio",
            value="3.2x",
            benchmark="3.0x (SaaS median)",
            assessment="Healthy unit economics",
            do_risk="Low risk of unsustainable growth claims",
        )
        assert m.metric == "LTV:CAC Ratio"
        assert m.value == "3.2x"
        assert m.benchmark == "3.0x (SaaS median)"
        assert m.assessment == "Healthy unit economics"
        assert m.do_risk == "Low risk of unsustainable growth claims"


class TestWaterfallRow:
    """Test 8: WaterfallRow accepts label/value/delta/narrative."""

    def test_full_construction(self) -> None:
        w = WaterfallRow(
            label="Gross Revenue",
            value="$4.2B",
            delta="+8.3% YoY",
            narrative="Driven by cloud adoption",
        )
        assert w.label == "Gross Revenue"
        assert w.value == "$4.2B"
        assert w.delta == "+8.3% YoY"
        assert w.narrative == "Driven by cloud adoption"

    def test_defaults(self) -> None:
        w = WaterfallRow()
        assert w.delta == ""
        assert w.narrative == ""


class TestRevenueSegmentDossier:
    """Test 9: RevenueSegmentDossier with full fields."""

    def test_full_construction(self) -> None:
        seg = RevenueSegmentDossier(
            segment_name="Cloud Services",
            revenue_pct="42%",
            growth_rate="+18.5% YoY",
            rev_rec_method="Ratably over subscription period",
            do_exposure="Miss risk tied to ARR growth guidance",
            risk_level="MEDIUM",
        )
        assert seg.segment_name == "Cloud Services"
        assert seg.revenue_pct == "42%"
        assert seg.growth_rate == "+18.5% YoY"
        assert seg.rev_rec_method == "Ratably over subscription period"
        assert seg.do_exposure == "Miss risk tied to ARR growth guidance"
        assert seg.risk_level == "MEDIUM"

    def test_defaults(self) -> None:
        seg = RevenueSegmentDossier()
        assert seg.risk_level == "LOW"


class TestDossierDataJsonSchema:
    """Test 10: DossierData.model_json_schema() produces valid JSON schema."""

    def test_json_schema_generation(self) -> None:
        schema = DossierData.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "revenue_card" in schema["properties"]
        assert "segment_dossiers" in schema["properties"]
        assert "emerging_risks" in schema["properties"]
        assert "asc_606_elements" in schema["properties"]
