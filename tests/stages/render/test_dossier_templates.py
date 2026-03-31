"""Tests for Company Intelligence Dossier Jinja2 templates (Phase 118-05).

Verifies all 9 dossier templates render correctly with fixture data,
produce expected HTML elements, and handle available=False gracefully.
"""

from __future__ import annotations

import pathlib

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = pathlib.Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html"


@pytest.fixture()
def env() -> Environment:
    """Jinja2 environment pointing at project templates."""
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

WHAT_COMPANY_DOES = {
    "what_company_does_available": True,
    "business_description": "Acme Corp manufactures industrial widgets used in aerospace and defense.",
    "core_do_exposure": "Concentrated revenue from 3 defense contracts exposes Acme to 10b-5 claims if any contract is lost.",
}

MONEY_FLOWS = {
    "money_flows_available": True,
    "flow_diagram": "Customer --> [Contract] --> Revenue\n  |-> Service fees (recurring)\n  |-> Hardware sales (one-time)",
    "flow_narrative": "Acme derives 60% of revenue from recurring service contracts and 40% from hardware sales.",
}

REVENUE_MODEL_CARD = {
    "revenue_card_available": True,
    "rows": [
        {
            "attribute": "Model Type",
            "value": "B2B Contracts",
            "do_risk": "Long-term contract revenue creates deferred recognition risk under ASC 606.",
            "row_class": "risk-medium",
        },
        {
            "attribute": "Recurring %",
            "value": "60%",
            "do_risk": "High recurring share reduces volatility but masks churn risk.",
            "row_class": "risk-low",
        },
        {
            "attribute": "Customer Concentration",
            "value": "Top 3 = 72%",
            "do_risk": "Loss of any top customer triggers material disclosure obligations (F.5).",
            "row_class": "risk-high",
        },
    ],
}

REVENUE_SEGMENTS = {
    "segments_available": True,
    "segments": [
        {
            "name": "Aerospace",
            "revenue_pct": "45%",
            "growth": "+8.2%",
            "rev_rec_method": "Percentage of completion",
            "do_risk": "Percentage-of-completion estimates are subjective -- SCA trigger if revised downward.",
            "row_class": "",
        },
        {
            "name": "Defense",
            "revenue_pct": "35%",
            "growth": "+3.1%",
            "rev_rec_method": "Contract milestone",
            "do_risk": "Government contract cancellation risk tied to F.5 scoring factor.",
            "row_class": "",
        },
        {
            "name": "Commercial",
            "revenue_pct": "20%",
            "growth": "-1.5%",
            "rev_rec_method": "Point of sale",
            "do_risk": "Declining segment may require impairment disclosure.",
            "row_class": "risk-medium",
        },
    ],
    "concentration_available": True,
    "concentration_dimensions": [
        {
            "dimension": "Customer",
            "metric": "Top 3 = 72% of revenue",
            "risk_level": "HIGH",
            "do_implication": "Single customer loss = material event requiring 8-K disclosure.",
            "risk_class": "risk-high",
        },
        {
            "dimension": "Geographic",
            "metric": "US = 95%",
            "risk_level": "MEDIUM",
            "do_implication": "Limited geographic diversification amplifies domestic regulatory exposure.",
            "risk_class": "risk-medium",
        },
    ],
}

UNIT_ECONOMICS = {
    "unit_economics_available": True,
    "metrics": [
        {
            "metric": "Gross Margin",
            "value": "42.3%",
            "benchmark": "38.0%",
            "assessment": "Above peer median",
            "do_risk": "Margin compression would signal operational deterioration -- 10b-5 trigger.",
            "row_class": "risk-low",
        },
        {
            "metric": "Revenue per Employee",
            "value": "$312K",
            "benchmark": "$285K",
            "assessment": "Slightly above peers",
            "do_risk": "Declining productivity may indicate hidden operational issues.",
            "row_class": "",
        },
    ],
    "narrative": "Acme's unit economics are above peer median, driven by high-margin service contracts.",
}

REVENUE_WATERFALL = {
    "waterfall_available": True,
    "components": [
        {
            "component": "Prior Year Revenue",
            "value": "$1.2B",
            "delta": "--",
            "insight": "Base period FY2024",
            "row_class": "",
        },
        {
            "component": "Organic Growth",
            "value": "$96M",
            "delta": "+8.0%",
            "insight": "Driven by Aerospace segment expansion",
            "row_class": "",
        },
        {
            "component": "Acquisition",
            "value": "$45M",
            "delta": "+3.8%",
            "insight": "WidgetCo acquisition closed Q2",
            "row_class": "",
        },
        {
            "component": "FX Impact",
            "value": "-$12M",
            "delta": "-1.0%",
            "insight": "Strong USD headwind",
            "row_class": "risk-medium",
        },
    ],
    "narrative": "Revenue grew 10.8% YoY to $1.33B, with organic growth contributing 8.0% and WidgetCo adding 3.8%.",
}

EMERGING_RISKS = {
    "emerging_risks_available": True,
    "risks": [
        {
            "risk": "Defense budget sequestration",
            "probability": "High",
            "impact": "Very High",
            "timeframe": "6-12mo",
            "do_factor": "F.5",
            "status": "Monitoring",
            "probability_class": "text-risk-red",
        },
        {
            "risk": "Supply chain disruption (rare earth)",
            "probability": "Medium",
            "impact": "High",
            "timeframe": "12-24mo",
            "do_factor": "F.7",
            "status": "Active",
            "probability_class": "text-amber-600",
        },
    ],
}

ASC_606 = {
    "asc_606_available": True,
    "elements": [
        {
            "element": "Performance Obligations",
            "approach": "Distinct goods/services identified per contract",
            "complexity": "High",
            "do_risk": "Multiple performance obligations increase misallocation risk.",
            "complexity_class": "text-risk-red",
        },
        {
            "element": "Transaction Price",
            "approach": "Fixed pricing with variable consideration for incentives",
            "complexity": "Medium",
            "do_risk": "Variable consideration estimates may require revision -- restatement trigger.",
            "complexity_class": "text-amber-600",
        },
    ],
    "billings_narrative": "Acme's billings exceed recognized revenue by $47M, reflecting deferred revenue from multi-year contracts.",
}


# ---------------------------------------------------------------------------
# Test: what_company_does
# ---------------------------------------------------------------------------


class TestWhatCompanyDoes:
    def test_renders_business_description(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/what_company_does.html.j2")
        html = tpl.render(dossier_what=WHAT_COMPANY_DOES)
        assert "Acme Corp manufactures industrial widgets" in html
        assert "What the Company Does" in html

    def test_renders_core_do_exposure_callout(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/what_company_does.html.j2")
        html = tpl.render(dossier_what=WHAT_COMPANY_DOES)
        assert "do-callout" in html
        assert "Concentrated revenue from 3 defense contracts" in html

    def test_unavailable_renders_nothing(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/what_company_does.html.j2")
        html = tpl.render(dossier_what={"what_company_does_available": False})
        assert "What the Company Does" not in html
        assert html.strip() == ""


# ---------------------------------------------------------------------------
# Test: money_flows
# ---------------------------------------------------------------------------


class TestMoneyFlows:
    def test_renders_pre_formatted_diagram(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/money_flows.html.j2")
        html = tpl.render(dossier_flows=MONEY_FLOWS)
        assert "<pre" in html
        assert "revenue-flow" in html
        assert "Customer -->" in html

    def test_renders_narrative(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/money_flows.html.j2")
        html = tpl.render(dossier_flows=MONEY_FLOWS)
        assert "60% of revenue from recurring" in html


# ---------------------------------------------------------------------------
# Test: revenue_model_card
# ---------------------------------------------------------------------------


class TestRevenueModelCard:
    def test_renders_table_with_do_risk_column(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_model_card.html.j2")
        html = tpl.render(dossier_card=REVENUE_MODEL_CARD)
        # Column header (HTML-escaped ampersand)
        assert "D&amp;O Risk" in html
        assert "Revenue Model Card" in html

    def test_renders_row_with_risk_class(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_model_card.html.j2")
        html = tpl.render(dossier_card=REVENUE_MODEL_CARD)
        assert "risk-high" in html
        assert "risk-medium" in html

    def test_renders_do_risk_text(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_model_card.html.j2")
        html = tpl.render(dossier_card=REVENUE_MODEL_CARD)
        assert "Long-term contract revenue creates deferred recognition risk" in html
        assert "Loss of any top customer triggers material disclosure" in html

    def test_unavailable_renders_nothing(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_model_card.html.j2")
        html = tpl.render(dossier_card={"revenue_card_available": False})
        assert "Revenue Model Card" not in html
        assert html.strip() == ""


# ---------------------------------------------------------------------------
# Test: revenue_segments
# ---------------------------------------------------------------------------


class TestRevenueSegments:
    def test_renders_segment_table_and_concentration(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_segments.html.j2")
        html = tpl.render(dossier_segments=REVENUE_SEGMENTS)
        assert "Revenue Segment Breakdown" in html
        assert "Aerospace" in html
        assert "D&amp;O Litigation Exposure" in html
        # Concentration
        assert "Concentration Assessment" in html
        assert "Customer" in html
        assert "Top 3 = 72% of revenue" in html

    def test_renders_risk_levels(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_segments.html.j2")
        html = tpl.render(dossier_segments=REVENUE_SEGMENTS)
        assert "text-risk-red" in html  # HIGH risk level
        assert "HIGH" in html


# ---------------------------------------------------------------------------
# Test: unit_economics
# ---------------------------------------------------------------------------


class TestUnitEconomics:
    def test_renders_metrics_table_and_narrative(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/unit_economics.html.j2")
        html = tpl.render(dossier_unit=UNIT_ECONOMICS)
        assert "Unit Economics" in html
        assert "D&amp;O Risk" in html
        assert "Gross Margin" in html
        assert "42.3%" in html
        assert "unit economics are above peer median" in html


# ---------------------------------------------------------------------------
# Test: revenue_waterfall
# ---------------------------------------------------------------------------


class TestRevenueWaterfall:
    def test_renders_waterfall_table(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/revenue_waterfall.html.j2")
        html = tpl.render(dossier_waterfall=REVENUE_WATERFALL)
        assert "Revenue Waterfall" in html
        assert "Organic Growth" in html
        assert "+8.0%" in html
        assert "Revenue grew 10.8% YoY" in html


# ---------------------------------------------------------------------------
# Test: emerging_risk_radar
# ---------------------------------------------------------------------------


class TestEmergingRiskRadar:
    def test_renders_risk_table_with_do_factor(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/emerging_risk_radar.html.j2")
        html = tpl.render(dossier_risks=EMERGING_RISKS)
        assert "Emerging Risk Radar" in html
        assert "D&amp;O Factor" in html
        assert "Defense budget sequestration" in html
        assert "F.5" in html
        assert "text-risk-red" in html  # probability_class


# ---------------------------------------------------------------------------
# Test: asc_606
# ---------------------------------------------------------------------------


class TestASC606:
    def test_renders_asc_table_with_billings_narrative(self, env: Environment) -> None:
        tpl = env.get_template("sections/dossier/asc_606.html.j2")
        html = tpl.render(dossier_asc=ASC_606)
        assert "Revenue Recognition (ASC 606)" in html
        assert "D&amp;O Risk" in html
        assert "Performance Obligations" in html
        assert "text-risk-red" in html  # complexity_class
        assert "billings exceed recognized revenue by $47M" in html


# ---------------------------------------------------------------------------
# Test: section wrapper
# ---------------------------------------------------------------------------


class TestSectionWrapper:
    def test_wrapper_includes_all_subsections(self, env: Environment) -> None:
        """Section wrapper renders all 8 subsections when data is available."""
        tpl = env.get_template("sections/dossier.html.j2")
        html = tpl.render(
            dossier_what=WHAT_COMPANY_DOES,
            dossier_flows=MONEY_FLOWS,
            dossier_card=REVENUE_MODEL_CARD,
            dossier_segments=REVENUE_SEGMENTS,
            dossier_unit=UNIT_ECONOMICS,
            dossier_waterfall=REVENUE_WATERFALL,
            dossier_risks=EMERGING_RISKS,
            dossier_asc=ASC_606,
        )
        assert "Intelligence Dossier" in html
        assert "What the Company Does" in html
        assert "How Money Flows" in html
        assert "Revenue Model Card" in html
        assert "Revenue Segment Breakdown" in html
        assert "Unit Economics" in html
        assert "Revenue Waterfall" in html
        assert "Emerging Risk Radar" in html
        assert "Revenue Recognition (ASC 606)" in html

    def test_wrapper_with_all_unavailable(self, env: Environment) -> None:
        """Section wrapper renders heading but no subsection content when all unavailable."""
        tpl = env.get_template("sections/dossier.html.j2")
        html = tpl.render(
            dossier_what={"what_company_does_available": False},
            dossier_flows={"money_flows_available": False},
            dossier_card={"revenue_card_available": False},
            dossier_segments={"segments_available": False},
            dossier_unit={"unit_economics_available": False},
            dossier_waterfall={"waterfall_available": False},
            dossier_risks={"emerging_risks_available": False},
            dossier_asc={"asc_606_available": False},
        )
        assert "Intelligence Dossier" in html
        assert "What the Company Does" not in html
        assert "Revenue Model Card" not in html


# ---------------------------------------------------------------------------
# Test: no truncate on analytical content
# ---------------------------------------------------------------------------


class TestNoTruncate:
    def test_no_truncate_in_templates(self) -> None:
        """No dossier template uses | truncate on analytical content."""
        dossier_dir = TEMPLATE_DIR / "sections" / "dossier"
        for tpl_file in dossier_dir.glob("*.html.j2"):
            content = tpl_file.read_text()
            assert "| truncate" not in content, f"{tpl_file.name} contains | truncate"


# ---------------------------------------------------------------------------
# Test: no unresolved jinja2 in rendered output
# ---------------------------------------------------------------------------


class TestNoUnresolvedJinja:
    def test_no_jinja_syntax_in_rendered_output(self, env: Environment) -> None:
        """Rendered output should not contain unresolved {{ or {% markers."""
        tpl = env.get_template("sections/dossier.html.j2")
        html = tpl.render(
            dossier_what=WHAT_COMPANY_DOES,
            dossier_flows=MONEY_FLOWS,
            dossier_card=REVENUE_MODEL_CARD,
            dossier_segments=REVENUE_SEGMENTS,
            dossier_unit=UNIT_ECONOMICS,
            dossier_waterfall=REVENUE_WATERFALL,
            dossier_risks=EMERGING_RISKS,
            dossier_asc=ASC_606,
        )
        assert "{{ " not in html, "Unresolved Jinja2 variable in output"
        assert "{% " not in html, "Unresolved Jinja2 tag in output"
