"""Tests for Phase 117 forward-looking and scoring Jinja2 templates.

Verifies that all 10 templates (6 forward-looking + 3 scoring + 1 trigger matrix)
render correctly with mock context data and handle empty states gracefully.
"""

from __future__ import annotations

import jinja2
import pytest


@pytest.fixture
def env() -> jinja2.Environment:
    """Create Jinja2 environment pointing at project templates."""
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader("src/do_uw/templates/html"),
        undefined=jinja2.Undefined,
    )


# ---------------------------------------------------------------------------
# Mock data factories
# ---------------------------------------------------------------------------

def _mock_forward_risk_map() -> dict:
    """Mock forward_risk_map context with 3 statements, 2 catalysts, 3 estimates."""
    return {
        "has_forward_statements": True,
        "has_quantitative_guidance": True,
        "forward_statement_count": 3,
        "forward_statements": [
            {
                "metric_name": "Revenue",
                "current_value": "$12.5B",
                "guidance_claim": "$13.0B - $13.5B",
                "guidance_type": "QUANTITATIVE",
                "miss_risk": "HIGH",
                "miss_risk_rationale": "Current run-rate trails guidance midpoint by 8%",
                "sca_relevance": "10b-5 materiality if revenue misses by >5%",
                "source": "10-K FY2025",
                "confidence": "HIGH",
                "row_class": "risk-high",
            },
            {
                "metric_name": "EPS",
                "current_value": "$4.20",
                "guidance_claim": "$4.50 - $4.80",
                "guidance_type": "QUANTITATIVE",
                "miss_risk": "MEDIUM",
                "miss_risk_rationale": "Within achievable range given margin expansion",
                "sca_relevance": "Earnings miss could trigger class action",
                "source": "8-K Q3 2025",
                "confidence": "MEDIUM",
                "row_class": "risk-medium",
            },
            {
                "metric_name": "Market expansion",
                "current_value": "3 regions",
                "guidance_claim": "Enter 2 new markets by Q4",
                "guidance_type": "QUALITATIVE",
                "miss_risk": "LOW",
                "miss_risk_rationale": "",
                "sca_relevance": "",
                "source": "10-K FY2025",
                "confidence": "LOW",
                "row_class": "risk-low",
            },
        ],
        "has_catalysts": True,
        "catalyst_count": 2,
        "catalysts": [
            {
                "event": "FDA approval decision",
                "timing": "Q2 2026",
                "impact_if_negative": "Revenue shortfall of ~$2B",
                "litigation_risk": "HIGH",
                "row_class": "risk-high",
            },
            {
                "event": "Earnings release Q1",
                "timing": "April 2026",
                "impact_if_negative": "Stock drop >10%",
                "litigation_risk": "MEDIUM",
                "row_class": "risk-medium",
            },
        ],
        "has_growth_estimates": True,
        "growth_estimates": [
            {
                "period": "FY2026",
                "metric": "Revenue",
                "estimate": "$14.2B",
                "trend": "UP",
                "trend_icon": "\u2191",
                "source": "Company guidance",
            },
            {
                "period": "FY2026",
                "metric": "EPS",
                "estimate": "$5.10",
                "trend": "UP",
                "trend_icon": "\u2191",
                "source": "Company guidance",
            },
            {
                "period": "FY2027",
                "metric": "Revenue",
                "estimate": "$16.0B",
                "trend": "FLAT",
                "trend_icon": "\u2192",
                "source": "yfinance",
            },
        ],
        "alt_signals": {
            "short_interest": {
                "short_ratio": "3.2",
                "shares_short": "12,500,000",
                "trend": "INCREASING",
            },
            "analyst_sentiment": {
                "consensus": "Overweight",
                "target_mean": "$185.00",
                "coverage_count": 24,
            },
            "buyback_support": {
                "has_buyback": True,
                "amount": "$5B authorized",
            },
            "has_alt_signals": True,
        },
        "forward_available": True,
    }


def _mock_credibility_data() -> dict:
    """Mock credibility_data context with 4 quarter records."""
    return {
        "credibility_available": True,
        "credibility_level": "HIGH",
        "credibility_class": "cred-high",
        "beat_rate_pct": "87.5%",
        "quarters_assessed": 8,
        "quarter_records": [
            {
                "quarter": "Q4 2025",
                "metric": "EPS",
                "guided_value": "$1.10",
                "actual_value": "$1.18",
                "beat_or_miss": "BEAT",
                "magnitude_pct": "+7.3%",
                "row_class": "row-beat",
            },
            {
                "quarter": "Q3 2025",
                "metric": "EPS",
                "guided_value": "$1.05",
                "actual_value": "$0.98",
                "beat_or_miss": "MISS",
                "magnitude_pct": "-6.7%",
                "row_class": "row-miss",
            },
            {
                "quarter": "Q2 2025",
                "metric": "EPS",
                "guided_value": "$1.00",
                "actual_value": "$1.01",
                "beat_or_miss": "INLINE",
                "magnitude_pct": "+1.0%",
                "row_class": "row-inline",
            },
            {
                "quarter": "Q1 2025",
                "metric": "EPS",
                "guided_value": "$0.95",
                "actual_value": "$1.02",
                "beat_or_miss": "BEAT",
                "magnitude_pct": "+7.4%",
                "row_class": "row-beat",
            },
        ],
        "source": "yfinance earnings + 8-K analysis",
    }


def _mock_monitoring_data() -> dict:
    """Mock monitoring_data context with 6 triggers."""
    return {
        "monitoring_available": True,
        "trigger_count": 6,
        "triggers": [
            {
                "trigger_name": "Stock Price Drop",
                "action": "Review exposure and notify carrier",
                "threshold": ">20% decline over 5 days",
                "current_value": "-2.3% (5-day)",
                "source": "yfinance",
            },
            {
                "trigger_name": "New SEC Investigation",
                "action": "Escalate to senior UW",
                "threshold": "Any formal order or Wells notice",
                "current_value": "None",
                "source": "EDGAR",
            },
            {
                "trigger_name": "New SCA Filing",
                "action": "Assess coverage impact",
                "threshold": "Any securities class action",
                "current_value": "None",
                "source": "Stanford SCAC",
            },
            {
                "trigger_name": "Earnings Miss",
                "action": "Re-evaluate credibility score",
                "threshold": ">10% below guidance",
                "current_value": "+7.3% above",
                "source": "8-K",
            },
            {
                "trigger_name": "Executive Departure",
                "action": "Review D&O implications",
                "threshold": "CEO, CFO, or GC departure",
                "current_value": "Stable",
                "source": "8-K",
            },
            {
                "trigger_name": "Credit Downgrade",
                "action": "Re-assess distress models",
                "threshold": "Any rating agency downgrade",
                "current_value": "BBB+ (stable)",
                "source": "10-K",
            },
        ],
    }


def _mock_posture_data() -> dict:
    """Mock posture_data with 7 elements, 2 overrides, 3 zero verifications, 3 watch items."""
    return {
        "posture_available": True,
        "posture_tier": "WRITE",
        "posture_tier_class": "posture-write",
        "posture_elements": [
            {"element": "Decision", "recommendation": "Write at standard terms", "rationale": "Tier 3 WRITE with clean nuclear screen"},
            {"element": "Retention", "recommendation": "$1M SIR", "rationale": "Standard for this market cap range"},
            {"element": "Limit Capacity", "recommendation": "$10M any one layer", "rationale": "Within appetite for WRITE tier"},
            {"element": "Pricing", "recommendation": "Market rate", "rationale": "No premium loading required"},
            {"element": "Exclusions", "recommendation": "Standard form", "rationale": "No specific carve-outs needed"},
            {"element": "Monitoring", "recommendation": "Quarterly review", "rationale": "Standard monitoring cadence"},
            {"element": "Re-evaluation", "recommendation": "At renewal", "rationale": "No interim review triggers active"},
        ],
        "overrides_applied": [
            "F.7 elevated (insider trading signals) -- increase monitoring frequency",
            "F.3 restatement risk -- add restatement exclusion consideration",
        ],
        "has_overrides": True,
        "zero_verifications": [
            {
                "factor_id": "F.2",
                "factor_name": "Regulatory Risk",
                "points": "0/6",
                "evidence": "No SEC enforcement actions, no open investigations per 10-K Item 3",
                "source": "10-K FY2025 + EDGAR",
            },
            {
                "factor_id": "F.4",
                "factor_name": "Corporate Governance",
                "points": "0/8",
                "evidence": "Independent board majority (8/10), separate Chair/CEO, all committees independent",
                "source": "DEF 14A 2025",
            },
            {
                "factor_id": "F.6",
                "factor_name": "Related Party Transactions",
                "points": "0/5",
                "evidence": "No material RPTs disclosed in proxy statement",
                "source": "DEF 14A 2025",
            },
        ],
        "has_zero_verifications": True,
        "zero_verification_count": 3,
        "watch_items": [
            {
                "item": "Insider selling pattern",
                "current_state": "3 insiders sold in Q4 2025",
                "threshold": ">5 insider sales in any quarter",
                "re_evaluation": "Quarterly",
                "source": "Form 4",
            },
            {
                "item": "Short interest trend",
                "current_state": "3.2 days to cover",
                "threshold": ">5.0 days to cover",
                "re_evaluation": "Monthly",
                "source": "yfinance",
            },
            {
                "item": "Debt covenant compliance",
                "current_state": "1.8x coverage (2.0x required)",
                "threshold": "<1.5x or waiver request",
                "re_evaluation": "Quarterly",
                "source": "10-Q",
            },
        ],
        "has_watch_items": True,
        "watch_item_count": 3,
    }


def _mock_quick_screen_clean() -> dict:
    """Mock quick_screen_data with 0/5 nuclear triggers fired (clean)."""
    return {
        "quick_screen_available": True,
        "nuclear_triggers": [
            {"trigger_id": "NUC-1", "name": "Active SCA", "fired": False, "evidence": "", "source": "Stanford SCAC", "icon": "clean"},
            {"trigger_id": "NUC-2", "name": "SEC Enforcement", "fired": False, "evidence": "", "source": "EDGAR", "icon": "clean"},
            {"trigger_id": "NUC-3", "name": "Restatement", "fired": False, "evidence": "", "source": "10-K", "icon": "clean"},
            {"trigger_id": "NUC-4", "name": "Going Concern", "fired": False, "evidence": "", "source": "10-K", "icon": "clean"},
            {"trigger_id": "NUC-5", "name": "Criminal Indictment", "fired": False, "evidence": "", "source": "PACER", "icon": "clean"},
        ],
        "nuclear_fired_count": 0,
        "nuclear_total": 5,
        "nuclear_clean": True,
        "nuclear_display": "0/5 nuclear triggers fired",
        "trigger_matrix": [
            {
                "signal_id": "FWRD.MISS.01",
                "signal_name": "Revenue Guidance Miss Risk",
                "flag_level": "RED",
                "flag_class": "flag-red",
                "section": "Forward-Looking",
                "section_anchor": "#forward-risk-map",
                "do_context": "Revenue run-rate trails midpoint by 8%",
            },
            {
                "signal_id": "FIN.DEBT.01",
                "signal_name": "Debt Covenant Proximity",
                "flag_level": "YELLOW",
                "flag_class": "flag-yellow",
                "section": "Financial",
                "section_anchor": "#financial",
                "do_context": "Coverage ratio at 1.8x vs 2.0x required",
            },
            {
                "signal_id": "GOV.INSIDER.01",
                "signal_name": "Insider Selling Cluster",
                "flag_level": "YELLOW",
                "flag_class": "flag-yellow",
                "section": "Governance",
                "section_anchor": "#governance",
                "do_context": "3 insiders sold in Q4 2025",
            },
            {
                "signal_id": "MKT.SHORT.01",
                "signal_name": "Elevated Short Interest",
                "flag_level": "YELLOW",
                "flag_class": "flag-yellow",
                "section": "Market",
                "section_anchor": "#market",
                "do_context": "Days to cover 3.2",
            },
            {
                "signal_id": "LIT.RISK.01",
                "signal_name": "Derivative Action Risk",
                "flag_level": "RED",
                "flag_class": "flag-red",
                "section": "Litigation",
                "section_anchor": "#litigation",
                "do_context": "Board independence below threshold for breach of fiduciary duty defense",
            },
        ],
        "trigger_matrix_by_section": {
            "Forward-Looking": [
                {
                    "signal_id": "FWRD.MISS.01",
                    "signal_name": "Revenue Guidance Miss Risk",
                    "flag_level": "RED",
                    "flag_class": "flag-red",
                    "section": "Forward-Looking",
                    "section_anchor": "#forward-risk-map",
                    "do_context": "Revenue run-rate trails midpoint by 8%",
                },
            ],
            "Financial": [
                {
                    "signal_id": "FIN.DEBT.01",
                    "signal_name": "Debt Covenant Proximity",
                    "flag_level": "YELLOW",
                    "flag_class": "flag-yellow",
                    "section": "Financial",
                    "section_anchor": "#financial",
                    "do_context": "Coverage ratio at 1.8x vs 2.0x required",
                },
            ],
            "Governance": [
                {
                    "signal_id": "GOV.INSIDER.01",
                    "signal_name": "Insider Selling Cluster",
                    "flag_level": "YELLOW",
                    "flag_class": "flag-yellow",
                    "section": "Governance",
                    "section_anchor": "#governance",
                    "do_context": "3 insiders sold in Q4 2025",
                },
            ],
            "Market": [
                {
                    "signal_id": "MKT.SHORT.01",
                    "signal_name": "Elevated Short Interest",
                    "flag_level": "YELLOW",
                    "flag_class": "flag-yellow",
                    "section": "Market",
                    "section_anchor": "#market",
                    "do_context": "Days to cover 3.2",
                },
            ],
            "Litigation": [
                {
                    "signal_id": "LIT.RISK.01",
                    "signal_name": "Derivative Action Risk",
                    "flag_level": "RED",
                    "flag_class": "flag-red",
                    "section": "Litigation",
                    "section_anchor": "#litigation",
                    "do_context": "Board independence below threshold",
                },
            ],
        },
        "red_count": 2,
        "yellow_count": 3,
        "total_flags": 5,
        "prospective_checks": [
            {"check_name": "Guidance Gap", "finding": "Within range", "status": "GREEN", "status_class": "status-green", "source": "model"},
            {"check_name": "Insider Trend", "finding": "Elevated", "status": "YELLOW", "status_class": "status-yellow", "source": "Form 4"},
            {"check_name": "Short Interest", "finding": "Normal", "status": "GREEN", "status_class": "status-green", "source": "yfinance"},
            {"check_name": "Credibility", "finding": "HIGH", "status": "GREEN", "status_class": "status-green", "source": "model"},
            {"check_name": "Distress", "finding": "None", "status": "GREEN", "status_class": "status-green", "source": "model"},
        ],
        "has_prospective_checks": True,
    }


def _mock_quick_screen_fired() -> dict:
    """Mock quick_screen_data with 1/5 nuclear trigger fired."""
    data = _mock_quick_screen_clean()
    data["nuclear_triggers"][0]["fired"] = True
    data["nuclear_triggers"][0]["evidence"] = "Active SCA: Smith v. Acme Corp filed 2025-11-15"
    data["nuclear_triggers"][0]["icon"] = "fired"
    data["nuclear_fired_count"] = 1
    data["nuclear_clean"] = False
    data["nuclear_display"] = "1/5 NUCLEAR TRIGGERS FIRED"
    return data


# ---------------------------------------------------------------------------
# Forward-Looking template tests
# ---------------------------------------------------------------------------


class TestRiskMapTemplate:
    """Tests for risk_map.html.j2."""

    def test_renders_with_forward_statements(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/risk_map.html.j2")
        ctx = {"forward_risk_map": _mock_forward_risk_map()}
        html = tmpl.render(**ctx)
        assert "Forward-Looking Statement Risk Map" in html
        assert "Revenue" in html
        assert "HIGH" in html
        assert "MEDIUM" in html
        assert "LOW" in html
        assert "miss_risk_rationale" not in html  # variable name should not appear
        assert "sca_relevance" not in html or "10b-5" in html  # should have actual content

    def test_renders_qualitative_notice(self, env: jinja2.Environment) -> None:
        data = _mock_forward_risk_map()
        data["has_quantitative_guidance"] = False
        tmpl = env.get_template("sections/forward_looking/risk_map.html.j2")
        html = tmpl.render(forward_risk_map=data)
        assert "does not provide explicit numeric guidance" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/risk_map.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestCredibilityTemplate:
    """Tests for credibility.html.j2."""

    def test_renders_with_quarter_records(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/credibility.html.j2")
        ctx = {"credibility_data": _mock_credibility_data()}
        html = tmpl.render(**ctx)
        assert "Management Credibility" in html
        assert "87.5%" in html
        assert "BEAT" in html
        assert "MISS" in html
        assert "INLINE" in html
        assert "Q4 2025" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/credibility.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestCatalystsTemplate:
    """Tests for catalysts.html.j2."""

    def test_renders_with_catalysts(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/catalysts.html.j2")
        ctx = {"forward_risk_map": _mock_forward_risk_map()}
        html = tmpl.render(**ctx)
        assert "Catalysts" in html
        assert "FDA approval decision" in html
        assert "HIGH" in html
        assert "MEDIUM" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/catalysts.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestMonitoringTriggersTemplate:
    """Tests for monitoring_triggers.html.j2."""

    def test_renders_with_triggers(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/monitoring_triggers.html.j2")
        ctx = {"monitoring_data": _mock_monitoring_data()}
        html = tmpl.render(**ctx)
        assert "Monitoring Triggers" in html
        assert "Stock Price Drop" in html
        assert ">20% decline over 5 days" in html
        assert "6 monitoring trigger(s) configured" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/monitoring_triggers.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestGrowthEstimatesTemplate:
    """Tests for growth_estimates.html.j2."""

    def test_renders_with_estimates(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/growth_estimates.html.j2")
        ctx = {"forward_risk_map": _mock_forward_risk_map()}
        html = tmpl.render(**ctx)
        assert "Growth Estimates" in html
        assert "$14.2B" in html
        assert "FY2026" in html
        assert "\u2191" in html  # up arrow

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/growth_estimates.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestAltSignalsTemplate:
    """Tests for alt_signals.html.j2."""

    def test_renders_with_alt_signals(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/alt_signals.html.j2")
        ctx = {"forward_risk_map": _mock_forward_risk_map()}
        html = tmpl.render(**ctx)
        assert "Alternative Forward-Looking Signals" in html
        assert "Short Interest" in html
        assert "3.2" in html
        assert "Analyst Sentiment" in html
        assert "Overweight" in html
        assert "Buyback Support" in html
        assert "Active" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/forward_looking/alt_signals.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


# ---------------------------------------------------------------------------
# Scoring template tests
# ---------------------------------------------------------------------------


class TestZeroVerificationTemplate:
    """Tests for zero_verification.html.j2."""

    def test_renders_with_zero_factors(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/zero_verification.html.j2")
        ctx = {"posture_data": _mock_posture_data()}
        html = tmpl.render(**ctx)
        assert "ZER-001 Verifications" in html
        assert "3 factors at zero" in html
        assert "F.2" in html
        assert "Regulatory Risk" in html
        assert "Positive Evidence" in html
        assert "No SEC enforcement" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/zero_verification.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestUnderwritingPostureTemplate:
    """Tests for underwriting_posture.html.j2."""

    def test_renders_with_posture_elements(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/underwriting_posture.html.j2")
        ctx = {"posture_data": _mock_posture_data()}
        html = tmpl.render(**ctx)
        assert "Suggested Underwriting Posture" in html
        assert "WRITE" in html
        assert "posture-write" in html
        assert "Decision" in html
        assert "Retention" in html
        assert "Limit Capacity" in html
        assert "Pricing" in html
        assert "Exclusions" in html
        assert "Monitoring" in html
        assert "Re-evaluation" in html
        # All 7 elements present
        assert html.count("<tr class=") >= 7

    def test_renders_overrides(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/underwriting_posture.html.j2")
        ctx = {"posture_data": _mock_posture_data()}
        html = tmpl.render(**ctx)
        assert "Factor Overrides Applied" in html
        assert "F.7 elevated" in html
        assert "F.3 restatement" in html

    def test_no_overrides_section_when_none(self, env: jinja2.Environment) -> None:
        data = _mock_posture_data()
        data["has_overrides"] = False
        data["overrides_applied"] = []
        tmpl = env.get_template("sections/scoring/underwriting_posture.html.j2")
        html = tmpl.render(posture_data=data)
        assert "Factor Overrides Applied" not in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/underwriting_posture.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


class TestWatchItemsTemplate:
    """Tests for watch_items.html.j2."""

    def test_renders_with_watch_items(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/watch_items.html.j2")
        ctx = {"posture_data": _mock_posture_data()}
        html = tmpl.render(**ctx)
        assert "Watch Items (3)" in html
        assert "Insider selling pattern" in html
        assert "Short interest trend" in html
        assert "Debt covenant compliance" in html
        assert "Quarterly" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/scoring/watch_items.html.j2")
        html = tmpl.render()
        assert html.strip() == ""


# ---------------------------------------------------------------------------
# Trigger Matrix template tests
# ---------------------------------------------------------------------------


class TestTriggerMatrixTemplate:
    """Tests for trigger_matrix.html.j2."""

    def test_renders_clean_nuclear(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        ctx = {"quick_screen_data": _mock_quick_screen_clean()}
        html = tmpl.render(**ctx)
        assert 'id="quick-screen"' in html
        assert "Quick Screen" in html
        assert "0/5 nuclear triggers fired" in html
        assert "border-green-500" in html
        assert "bg-green-100" in html
        assert "NUC-1" in html
        assert "NUC-5" in html

    def test_renders_fired_nuclear(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        ctx = {"quick_screen_data": _mock_quick_screen_fired()}
        html = tmpl.render(**ctx)
        assert "1/5 NUCLEAR TRIGGERS FIRED" in html
        assert "border-risk-red" in html
        assert "bg-risk-red" in html

    def test_renders_flag_summary(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        ctx = {"quick_screen_data": _mock_quick_screen_clean()}
        html = tmpl.render(**ctx)
        assert "2 RED" in html
        assert "3 YELLOW" in html
        assert "Forward-Looking" in html
        assert "Financial" in html
        assert "Governance" in html

    def test_renders_prospective_checks(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        ctx = {"quick_screen_data": _mock_quick_screen_clean()}
        html = tmpl.render(**ctx)
        assert "Prospective Checks" in html
        assert "Guidance Gap" in html
        assert "Insider Trend" in html
        assert "status-green" in html
        assert "status-yellow" in html

    def test_empty_state_no_output(self, env: jinja2.Environment) -> None:
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        html = tmpl.render()
        assert html.strip() == ""

    def test_clean_profile_message_when_no_flags(self, env: jinja2.Environment) -> None:
        data = _mock_quick_screen_clean()
        data["total_flags"] = 0
        data["red_count"] = 0
        data["yellow_count"] = 0
        data["trigger_matrix"] = []
        data["trigger_matrix_by_section"] = {}
        tmpl = env.get_template("sections/trigger_matrix.html.j2")
        html = tmpl.render(quick_screen_data=data)
        assert "No RED or YELLOW flags detected" in html
        assert "Clean risk profile" in html
