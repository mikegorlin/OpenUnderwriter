"""Tests for forward-looking risk framework Pydantic models.

Validates all 14 model classes instantiate correctly with defaults,
carry source/confidence fields per data integrity rules, and compose
properly into the ForwardLookingData container.
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
    NuclearTriggerCheck,
    PostureElement,
    PostureRecommendation,
    ProspectiveCheck,
    QuickScreenResult,
    TriggerMatrixRow,
    WatchItem,
)


class TestForwardStatement:
    """ForwardStatement model tests."""

    def test_defaults(self) -> None:
        stmt = ForwardStatement()
        assert stmt.metric_name == ""
        assert stmt.miss_risk == "UNKNOWN"
        assert stmt.guidance_type == "QUANTITATIVE"
        assert stmt.confidence == "MEDIUM"

    def test_fully_populated(self) -> None:
        stmt = ForwardStatement(
            metric_name="Revenue",
            current_value="$45.2B",
            current_value_numeric=45.2,
            guidance_claim="$48-50B for FY2026",
            guidance_midpoint=49.0,
            guidance_type="QUANTITATIVE",
            miss_risk="MEDIUM",
            miss_risk_rationale="6.2% gap to midpoint, management credibility HIGH",
            sca_relevance="Potential earnings fraud theory",
            source_filing="0001193125-25-123456",
            source_date="2025-12-15",
            confidence="HIGH",
        )
        assert stmt.metric_name == "Revenue"
        assert stmt.current_value_numeric == 45.2
        assert stmt.guidance_midpoint == 49.0
        assert stmt.miss_risk == "MEDIUM"
        assert stmt.confidence == "HIGH"
        assert stmt.source_filing != ""

    def test_qualitative_guidance(self) -> None:
        stmt = ForwardStatement(
            metric_name="Market expansion",
            guidance_claim="Expect to enter 3 new international markets",
            guidance_type="QUALITATIVE",
            miss_risk="LOW",
            confidence="MEDIUM",
        )
        assert stmt.guidance_type == "QUALITATIVE"
        assert stmt.guidance_midpoint is None
        assert stmt.current_value_numeric is None


class TestCredibilityQuarter:
    """CredibilityQuarter model tests."""

    def test_defaults(self) -> None:
        cq = CredibilityQuarter()
        assert cq.quarter == ""
        assert cq.beat_or_miss == ""
        assert cq.magnitude_pct is None

    def test_populated(self) -> None:
        cq = CredibilityQuarter(
            quarter="Q3 2025",
            metric="EPS",
            guided_value="$4.50-$4.70",
            actual_value="$4.82",
            beat_or_miss="BEAT",
            magnitude_pct=4.3,
            source="yfinance",
        )
        assert cq.beat_or_miss == "BEAT"
        assert cq.magnitude_pct == pytest.approx(4.3)


class TestCredibilityScore:
    """CredibilityScore model tests."""

    def test_defaults(self) -> None:
        cs = CredibilityScore()
        assert cs.beat_rate_pct == 0.0
        assert cs.quarters_assessed == 0
        assert cs.credibility_level == "MEDIUM"
        assert cs.source == "yfinance + 8-K LLM"

    def test_high_credibility(self) -> None:
        cs = CredibilityScore(
            beat_rate_pct=87.5,
            quarters_assessed=8,
            credibility_level="HIGH",
            quarter_records=[
                CredibilityQuarter(quarter=f"Q{i} 2025", beat_or_miss="BEAT")
                for i in range(1, 5)
            ],
        )
        assert cs.credibility_level == "HIGH"
        assert cs.quarters_assessed == 8
        assert len(cs.quarter_records) == 4

    def test_low_credibility(self) -> None:
        cs = CredibilityScore(
            beat_rate_pct=37.5,
            quarters_assessed=8,
            credibility_level="LOW",
        )
        assert cs.credibility_level == "LOW"


class TestCatalystEvent:
    """CatalystEvent model tests."""

    def test_defaults(self) -> None:
        ce = CatalystEvent()
        assert ce.event == ""
        assert ce.source == ""

    def test_populated(self) -> None:
        ce = CatalystEvent(
            event="FDA approval decision for lead drug",
            timing="Q2 2026",
            impact_if_negative="Stock decline 20-30%, SCA likely",
            litigation_risk="HIGH",
            source="10-K Item 1",
        )
        assert ce.litigation_risk == "HIGH"


class TestGrowthEstimate:
    """GrowthEstimate model tests."""

    def test_defaults(self) -> None:
        ge = GrowthEstimate()
        assert ge.source == "yfinance"

    def test_populated(self) -> None:
        ge = GrowthEstimate(
            period="Current Y",
            metric="EPS",
            estimate="$5.12",
            estimate_numeric=5.12,
            trend="UP",
        )
        assert ge.estimate_numeric == pytest.approx(5.12)
        assert ge.trend == "UP"


class TestMonitoringTrigger:
    """MonitoringTrigger model tests."""

    def test_defaults(self) -> None:
        mt = MonitoringTrigger()
        assert mt.trigger_name == ""
        assert mt.source == ""

    def test_populated(self) -> None:
        mt = MonitoringTrigger(
            trigger_name="Stock Below Support",
            action="Review stock drop analysis and D&O exposure",
            threshold="Price below $120.69 (52-week low)",
            current_value="$167.40",
            source="yfinance market data",
        )
        assert mt.trigger_name == "Stock Below Support"
        assert "$120.69" in mt.threshold


class TestPostureModels:
    """PostureElement and PostureRecommendation tests."""

    def test_element_defaults(self) -> None:
        pe = PostureElement()
        assert pe.element == ""
        assert pe.recommendation == ""

    def test_recommendation_with_overrides(self) -> None:
        pr = PostureRecommendation(
            tier="WRITE",
            elements=[
                PostureElement(
                    element="decision",
                    recommendation="Conditional terms",
                    rationale="WRITE tier, quality score 58",
                ),
                PostureElement(
                    element="exclusions",
                    recommendation="Litigation exclusion (pending matters)",
                    rationale="F.1 = 3/15: active SCA override applied",
                ),
            ],
            overrides_applied=["F.1>0: litigation exclusion added"],
        )
        assert pr.tier == "WRITE"
        assert len(pr.elements) == 2
        assert len(pr.overrides_applied) == 1
        assert "F.1>0" in pr.overrides_applied[0]


class TestNuclearTriggerCheck:
    """NuclearTriggerCheck model tests."""

    def test_defaults(self) -> None:
        ntc = NuclearTriggerCheck()
        assert ntc.fired is False
        assert ntc.evidence == ""

    def test_fired(self) -> None:
        ntc = NuclearTriggerCheck(
            trigger_id="NUC-01",
            name="Active Securities Class Action",
            fired=True,
            evidence="Stanford SCAC: In re Company XYZ, S.D.N.Y., filed 2025-09-15",
            source="Stanford SCAC database",
        )
        assert ntc.fired is True
        assert ntc.trigger_id == "NUC-01"
        assert "Stanford SCAC" in ntc.evidence

    def test_clean(self) -> None:
        ntc = NuclearTriggerCheck(
            trigger_id="NUC-01",
            name="Active Securities Class Action",
            fired=False,
            evidence="Stanford SCAC clean -- no active SCA found",
            source="Stanford SCAC database",
        )
        assert ntc.fired is False
        assert "clean" in ntc.evidence


class TestWatchItem:
    """WatchItem model tests."""

    def test_defaults(self) -> None:
        wi = WatchItem()
        assert wi.item == ""
        assert wi.source == ""

    def test_populated(self) -> None:
        wi = WatchItem(
            item="Insider selling pace",
            current_state="$4.2M quarterly",
            threshold=">$8.4M quarterly (2x current)",
            re_evaluation="Monthly",
            source="SEC Form 4 filings",
        )
        assert "2x" in wi.threshold


class TestTriggerMatrixRow:
    """TriggerMatrixRow model tests."""

    def test_defaults(self) -> None:
        tmr = TriggerMatrixRow()
        assert tmr.signal_id == ""
        assert tmr.flag_level == ""

    def test_populated(self) -> None:
        tmr = TriggerMatrixRow(
            signal_id="FWRD-GUIDE-002",
            signal_name="Guidance Miss Risk",
            flag_level="RED",
            section="Forward Risk",
            section_anchor="forward-risk",
            do_context="Revenue guidance miss >10% creates 10b-5 exposure",
        )
        assert tmr.flag_level == "RED"


class TestProspectiveCheck:
    """ProspectiveCheck model tests."""

    def test_defaults(self) -> None:
        pc = ProspectiveCheck()
        assert pc.status == "UNKNOWN"

    def test_populated(self) -> None:
        pc = ProspectiveCheck(
            check_name="Earnings Expectations",
            finding="Current-quarter EPS estimate trending 8% below guidance midpoint",
            status="YELLOW",
            source="yfinance consensus vs 8-K guidance",
        )
        assert pc.status == "YELLOW"


class TestQuickScreenResult:
    """QuickScreenResult model tests."""

    def test_defaults(self) -> None:
        qsr = QuickScreenResult()
        assert qsr.nuclear_fired_count == 0
        assert qsr.red_count == 0
        assert qsr.yellow_count == 0
        assert qsr.trigger_matrix == []

    def test_with_flags_and_nuclear(self) -> None:
        qsr = QuickScreenResult(
            trigger_matrix=[
                TriggerMatrixRow(signal_id="SIG-001", flag_level="RED"),
                TriggerMatrixRow(signal_id="SIG-002", flag_level="RED"),
                TriggerMatrixRow(signal_id="SIG-003", flag_level="YELLOW"),
            ],
            nuclear_triggers=[
                NuclearTriggerCheck(trigger_id="NUC-01", fired=False),
                NuclearTriggerCheck(trigger_id="NUC-02", fired=True),
            ],
            nuclear_fired_count=1,
            red_count=2,
            yellow_count=1,
        )
        assert qsr.red_count == 2
        assert qsr.yellow_count == 1
        assert qsr.nuclear_fired_count == 1
        assert len(qsr.trigger_matrix) == 3
        assert len(qsr.nuclear_triggers) == 2

    def test_all_clear(self) -> None:
        """Quick screen with zero flags -- clean company."""
        nuclear = [
            NuclearTriggerCheck(trigger_id=f"NUC-0{i}", fired=False)
            for i in range(1, 6)
        ]
        qsr = QuickScreenResult(
            nuclear_triggers=nuclear,
            nuclear_fired_count=0,
            red_count=0,
            yellow_count=0,
        )
        assert qsr.nuclear_fired_count == 0
        assert len(qsr.nuclear_triggers) == 5
        assert all(not nt.fired for nt in qsr.nuclear_triggers)


class TestForwardLookingData:
    """ForwardLookingData container model tests."""

    def test_defaults(self) -> None:
        fld = ForwardLookingData()
        assert fld.forward_statements == []
        assert fld.credibility is None
        assert fld.posture is None
        assert fld.quick_screen is None
        assert fld.zero_verifications == []

    def test_full_container(self) -> None:
        """ForwardLookingData with all nested models populated."""
        fld = ForwardLookingData(
            forward_statements=[
                ForwardStatement(metric_name="Revenue", miss_risk="MEDIUM", confidence="HIGH"),
                ForwardStatement(metric_name="EPS", miss_risk="LOW", confidence="HIGH"),
            ],
            credibility=CredibilityScore(
                beat_rate_pct=85.0,
                quarters_assessed=8,
                credibility_level="HIGH",
            ),
            catalysts=[
                CatalystEvent(event="M&A completion", timing="Q1 2026", source="8-K"),
            ],
            growth_estimates=[
                GrowthEstimate(period="Current Y", metric="EPS", estimate="$5.12"),
            ],
            monitoring_triggers=[
                MonitoringTrigger(trigger_name="SCA Filing", action="Immediate review"),
            ],
            posture=PostureRecommendation(
                tier="WANT",
                elements=[PostureElement(element="decision", recommendation="Full terms")],
            ),
            quick_screen=QuickScreenResult(
                nuclear_fired_count=0,
                red_count=1,
                yellow_count=3,
            ),
            watch_items=[
                WatchItem(item="Insider selling pace", re_evaluation="Monthly"),
            ],
            zero_verifications=[
                {"factor_id": "F.1", "evidence": "No active SCA", "source": "Stanford SCAC"},
            ],
        )
        assert len(fld.forward_statements) == 2
        assert fld.credibility is not None
        assert fld.credibility.credibility_level == "HIGH"
        assert len(fld.catalysts) == 1
        assert len(fld.growth_estimates) == 1
        assert len(fld.monitoring_triggers) == 1
        assert fld.posture is not None
        assert fld.posture.tier == "WANT"
        assert fld.quick_screen is not None
        assert fld.quick_screen.nuclear_fired_count == 0
        assert len(fld.watch_items) == 1
        assert len(fld.zero_verifications) == 1

    def test_serialization_roundtrip(self) -> None:
        """ForwardLookingData serializes to dict and back."""
        fld = ForwardLookingData(
            forward_statements=[
                ForwardStatement(metric_name="Revenue", confidence="HIGH"),
            ],
            credibility=CredibilityScore(beat_rate_pct=75.0, quarters_assessed=4),
        )
        data = fld.model_dump()
        restored = ForwardLookingData.model_validate(data)
        assert restored.forward_statements[0].metric_name == "Revenue"
        assert restored.credibility is not None
        assert restored.credibility.beat_rate_pct == pytest.approx(75.0)


class TestStateIntegration:
    """Verify ForwardLookingData is accessible on AnalysisState."""

    def test_state_has_forward_looking(self) -> None:
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        assert isinstance(state.forward_looking, ForwardLookingData)
        assert state.forward_looking.forward_statements == []
        assert state.forward_looking.credibility is None

    def test_state_forward_looking_mutation(self) -> None:
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        state.forward_looking.forward_statements.append(
            ForwardStatement(metric_name="Revenue", miss_risk="HIGH")
        )
        assert len(state.forward_looking.forward_statements) == 1
        assert state.forward_looking.forward_statements[0].miss_risk == "HIGH"
