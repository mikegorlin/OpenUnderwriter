"""Tests for forward-looking context builders: risk map, credibility, monitoring.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import pytest

from do_uw.models.forward_looking import (
    CatalystEvent,
    CredibilityQuarter,
    CredibilityScore,
    ForwardLookingData,
    ForwardStatement,
    GrowthEstimate,
    MonitoringTrigger,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.credibility_context import (
    extract_credibility,
)
from do_uw.stages.render.context_builders.forward_risk_map import (
    extract_forward_risk_map,
)
from do_uw.stages.render.context_builders.monitoring_context import (
    extract_monitoring_triggers,
)


def _make_state(**kwargs: object) -> AnalysisState:
    """Build minimal AnalysisState with forward_looking data."""
    fl = ForwardLookingData(**kwargs)  # type: ignore[arg-type]
    return AnalysisState(ticker="TEST", forward_looking=fl)


# ---------------------------------------------------------------------------
# extract_forward_risk_map tests
# ---------------------------------------------------------------------------


class TestForwardRiskMap:
    """Tests for extract_forward_risk_map context builder."""

    def test_with_three_forward_statements(self) -> None:
        """Populated state returns correct statement count and data."""
        stmts = [
            ForwardStatement(
                metric_name="Revenue",
                current_value="$10B",
                guidance_claim="$11B-$12B",
                guidance_type="QUANTITATIVE",
                miss_risk="HIGH",
                miss_risk_rationale="10% gap to guidance midpoint",
                sca_relevance="10b-5",
                source_filing="0001234-24-000001",
                confidence="HIGH",
            ),
            ForwardStatement(
                metric_name="EPS",
                current_value="$5.20",
                guidance_claim="$5.50-$6.00",
                guidance_type="QUANTITATIVE",
                miss_risk="MEDIUM",
                miss_risk_rationale="5% gap",
                sca_relevance="10b-5 + earnings fraud",
                source_filing="0001234-24-000001",
                confidence="HIGH",
            ),
            ForwardStatement(
                metric_name="Market Expansion",
                guidance_claim="Entering 3 new markets",
                guidance_type="QUALITATIVE",
                miss_risk="LOW",
                confidence="MEDIUM",
            ),
        ]
        state = _make_state(forward_statements=stmts)
        result = extract_forward_risk_map(state, {})

        assert result["has_forward_statements"] is True
        assert result["forward_statement_count"] == 3
        assert result["has_quantitative_guidance"] is True
        assert result["forward_available"] is True
        assert result["forward_statements"][0]["metric_name"] == "Revenue"
        assert result["forward_statements"][1]["miss_risk"] == "MEDIUM"

    def test_empty_state_returns_no_forward_statements(self) -> None:
        """Empty state returns has_forward_statements=False."""
        state = _make_state()
        result = extract_forward_risk_map(state, {})

        assert result["has_forward_statements"] is False
        assert result["forward_statement_count"] == 0
        assert result["has_quantitative_guidance"] is False
        assert result["forward_available"] is False

    def test_row_class_mapping(self) -> None:
        """Miss risk levels map to correct CSS classes."""
        stmts = [
            ForwardStatement(metric_name="Rev", miss_risk="HIGH"),
            ForwardStatement(metric_name="EPS", miss_risk="MEDIUM"),
            ForwardStatement(metric_name="Margin", miss_risk="LOW"),
            ForwardStatement(metric_name="Other", miss_risk="UNKNOWN"),
        ]
        state = _make_state(forward_statements=stmts)
        result = extract_forward_risk_map(state, {})

        assert result["forward_statements"][0]["row_class"] == "risk-high"
        assert result["forward_statements"][1]["row_class"] == "risk-medium"
        assert result["forward_statements"][2]["row_class"] == "risk-low"
        assert result["forward_statements"][3]["row_class"] == "risk-low"  # UNKNOWN defaults

    def test_catalysts_formatting(self) -> None:
        """Catalysts formatted with event, timing, litigation_risk, row_class."""
        cats = [
            CatalystEvent(
                event="FDA approval decision",
                timing="Q2 2025",
                impact_if_negative="Revenue guidance miss",
                litigation_risk="HIGH",
            ),
            CatalystEvent(
                event="New product launch",
                timing="H2 2025",
                impact_if_negative="Market share loss",
                litigation_risk="MEDIUM",
            ),
        ]
        state = _make_state(catalysts=cats)
        result = extract_forward_risk_map(state, {})

        assert result["has_catalysts"] is True
        assert result["catalyst_count"] == 2
        assert result["catalysts"][0]["event"] == "FDA approval decision"
        assert result["catalysts"][0]["row_class"] == "risk-high"
        assert result["catalysts"][1]["row_class"] == "risk-medium"
        assert result["forward_available"] is True

    def test_growth_estimates_with_trend_icons(self) -> None:
        """Growth estimates include correct trend icons."""
        estimates = [
            GrowthEstimate(period="Current Q", metric="EPS", estimate="$2.15", trend="UP"),
            GrowthEstimate(period="Current Y", metric="Revenue", estimate="$45B", trend="DOWN"),
            GrowthEstimate(period="Next Y", metric="EPS", estimate="$2.30", trend="FLAT"),
        ]
        state = _make_state(growth_estimates=estimates)
        result = extract_forward_risk_map(state, {})

        assert result["has_growth_estimates"] is True
        assert result["growth_estimates"][0]["trend_icon"] == "\u2191"
        assert result["growth_estimates"][1]["trend_icon"] == "\u2193"
        assert result["growth_estimates"][2]["trend_icon"] == "\u2192"

    def test_alt_signals_empty_market(self) -> None:
        """Alt signals gracefully handle empty extracted data."""
        state = _make_state()
        result = extract_forward_risk_map(state, {})

        assert result["alt_signals"]["has_alt_signals"] is False
        assert result["alt_signals"]["short_interest"] == {}
        assert result["alt_signals"]["analyst_sentiment"] == {}
        assert result["alt_signals"]["buyback_support"]["has_buyback"] is False

    def test_forward_available_with_only_catalysts(self) -> None:
        """forward_available is True if only catalysts are present."""
        cats = [CatalystEvent(event="Earnings call", timing="Q1 2025")]
        state = _make_state(catalysts=cats)
        result = extract_forward_risk_map(state, {})

        assert result["has_forward_statements"] is False
        assert result["has_catalysts"] is True
        assert result["forward_available"] is True


# ---------------------------------------------------------------------------
# extract_credibility tests
# ---------------------------------------------------------------------------


class TestCredibility:
    """Tests for extract_credibility context builder."""

    def test_with_credibility_data(self) -> None:
        """Populated credibility returns correct level, rate, and records."""
        cred = CredibilityScore(
            beat_rate_pct=75.0,
            quarters_assessed=8,
            credibility_level="MEDIUM",
            source="yfinance + 8-K LLM",
            quarter_records=[
                CredibilityQuarter(
                    quarter="Q3 2024", metric="EPS",
                    guided_value="$2.10", actual_value="$2.25",
                    beat_or_miss="BEAT", magnitude_pct=7.1,
                ),
                CredibilityQuarter(
                    quarter="Q2 2024", metric="EPS",
                    guided_value="$2.00", actual_value="$1.85",
                    beat_or_miss="MISS", magnitude_pct=-7.5,
                ),
            ],
        )
        state = _make_state(credibility=cred)
        result = extract_credibility(state, {})

        assert result["credibility_available"] is True
        assert result["credibility_level"] == "MEDIUM"
        assert result["credibility_class"] == "cred-medium"
        assert result["quarters_assessed"] == 8
        assert len(result["quarter_records"]) == 2
        assert result["source"] == "yfinance + 8-K LLM"

    def test_no_credibility_returns_unavailable(self) -> None:
        """No credibility data returns credibility_available=False."""
        state = _make_state()
        result = extract_credibility(state, {})

        assert result["credibility_available"] is False
        assert result["credibility_level"] == "UNKNOWN"
        assert result["credibility_class"] == "cred-low"
        assert result["beat_rate_pct"] == "N/A"
        assert result["quarters_assessed"] == 0
        assert result["quarter_records"] == []

    def test_quarter_records_row_class(self) -> None:
        """Quarter records get correct CSS class per beat/miss status."""
        cred = CredibilityScore(
            beat_rate_pct=50.0,
            quarters_assessed=4,
            credibility_level="MEDIUM",
            quarter_records=[
                CredibilityQuarter(quarter="Q4", beat_or_miss="BEAT"),
                CredibilityQuarter(quarter="Q3", beat_or_miss="MISS"),
                CredibilityQuarter(quarter="Q2", beat_or_miss="INLINE"),
                CredibilityQuarter(quarter="Q1", beat_or_miss="UNKNOWN"),
            ],
        )
        state = _make_state(credibility=cred)
        result = extract_credibility(state, {})

        assert result["quarter_records"][0]["row_class"] == "row-beat"
        assert result["quarter_records"][1]["row_class"] == "row-miss"
        assert result["quarter_records"][2]["row_class"] == "row-inline"
        assert result["quarter_records"][3]["row_class"] == "row-unknown"

    def test_high_credibility_class(self) -> None:
        """HIGH credibility level maps to cred-high CSS class."""
        cred = CredibilityScore(
            beat_rate_pct=90.0,
            quarters_assessed=8,
            credibility_level="HIGH",
        )
        state = _make_state(credibility=cred)
        result = extract_credibility(state, {})

        assert result["credibility_class"] == "cred-high"


# ---------------------------------------------------------------------------
# extract_monitoring_triggers tests
# ---------------------------------------------------------------------------


class TestMonitoringTriggers:
    """Tests for extract_monitoring_triggers context builder."""

    def test_with_six_triggers(self) -> None:
        """Six triggers produces correct count and data."""
        triggers = [
            MonitoringTrigger(
                trigger_name=f"Trigger {i}",
                action=f"Action {i}",
                threshold=f">{i * 10}%",
                current_value=f"{i * 5}%",
                source="computed",
            )
            for i in range(1, 7)
        ]
        state = _make_state(monitoring_triggers=triggers)
        result = extract_monitoring_triggers(state, {})

        assert result["monitoring_available"] is True
        assert result["trigger_count"] == 6
        assert len(result["triggers"]) == 6
        assert result["triggers"][0]["trigger_name"] == "Trigger 1"
        assert result["triggers"][5]["threshold"] == ">60%"

    def test_empty_state_returns_unavailable(self) -> None:
        """No monitoring triggers returns monitoring_available=False."""
        state = _make_state()
        result = extract_monitoring_triggers(state, {})

        assert result["monitoring_available"] is False
        assert result["trigger_count"] == 0
        assert result["triggers"] == []
