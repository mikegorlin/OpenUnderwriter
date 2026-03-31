"""Tests for the ANALYZE stage: check engine, mappers, and orchestrator.

Covers:
- SignalResult model creation and serialization
- aggregate_results counts
- evaluate_signal for each threshold type
- Missing data produces SKIPPED, never CLEAR
- execute_signals batch processing
- Data mappers for each domain section
- AnalyzeStage orchestration
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.analyze.signal_engine import evaluate_signal, execute_signals
from do_uw.stages.analyze.signal_mappers import map_signal_data
from do_uw.stages.analyze.signal_results import (
    SignalResult,
    SignalStatus,
    aggregate_results,
)

# ---------------------------------------------------------------------------
# SignalResult model tests
# ---------------------------------------------------------------------------


class TestSignalResult:
    """Tests for SignalResult model creation and serialization."""

    def test_create_minimal(self) -> None:
        """SignalResult can be created with minimal fields."""
        result = SignalResult(
            signal_id="TEST.001",
            signal_name="Test Check",
            status=SignalStatus.CLEAR,
        )
        assert result.signal_id == "TEST.001"
        assert result.signal_name == "Test Check"
        assert result.status == SignalStatus.CLEAR
        assert result.value is None
        assert result.threshold_level == ""
        assert result.factors == []

    def test_create_full(self) -> None:
        """SignalResult with all fields populated."""
        result = SignalResult(
            signal_id="FIN.LIQ.position",
            signal_name="Liquidity Position",
            status=SignalStatus.TRIGGERED,
            value=0.85,
            threshold_level="red",
            evidence="Value 0.85 below red threshold 1.0",
            source="current_ratio",
            factors=["F3"],
            section=3,
            needs_calibration=True,
        )
        assert result.status == SignalStatus.TRIGGERED
        assert result.value == 0.85
        assert result.threshold_level == "red"
        assert result.section == 3
        assert result.needs_calibration is True

    def test_serialization_roundtrip(self) -> None:
        """SignalResult serializes and deserializes correctly."""
        original = SignalResult(
            signal_id="GOV.EXEC.ceo_profile",
            signal_name="CEO Profile",
            status=SignalStatus.INFO,
            value="John Smith, 3yr tenure",
            factors=["F7"],
            section=5,
        )
        data = original.model_dump()
        restored = SignalResult.model_validate(data)
        assert restored.signal_id == original.signal_id
        assert restored.status == original.status
        assert restored.value == original.value
        assert restored.factors == original.factors


# ---------------------------------------------------------------------------
# aggregate_results tests
# ---------------------------------------------------------------------------


class TestAggregateResults:
    """Tests for aggregate_results counting helper."""

    def test_empty_list(self) -> None:
        """Empty list returns all zeros."""
        counts = aggregate_results([])
        assert counts == {
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "info": 0,
        }

    def test_mixed_statuses(self) -> None:
        """Correctly counts each status type."""
        results = [
            SignalResult(signal_id="a", signal_name="A", status=SignalStatus.CLEAR),
            SignalResult(signal_id="b", signal_name="B", status=SignalStatus.TRIGGERED),
            SignalResult(signal_id="c", signal_name="C", status=SignalStatus.SKIPPED),
            SignalResult(signal_id="d", signal_name="D", status=SignalStatus.INFO),
            SignalResult(signal_id="e", signal_name="E", status=SignalStatus.TRIGGERED),
            SignalResult(signal_id="f", signal_name="F", status=SignalStatus.CLEAR),
        ]
        counts = aggregate_results(results)
        assert counts["executed"] == 6
        assert counts["passed"] == 2
        assert counts["failed"] == 2
        assert counts["skipped"] == 1
        assert counts["info"] == 1


# ---------------------------------------------------------------------------
# evaluate_signal tests
# ---------------------------------------------------------------------------


def _make_check(
    signal_id: str = "TEST.001",
    name: str = "Test",
    threshold_type: str = "tiered",
    section: int = 3,
    factors: list[str] | None = None,
    **threshold_kw: Any,
) -> dict[str, Any]:
    """Helper to create a check config dict."""
    threshold: dict[str, Any] = {"type": threshold_type, **threshold_kw}
    return {
        "id": signal_id,
        "name": name,
        "section": section,
        "pillar": "P1_WHAT_WRONG",
        "factors": factors or [],
        "required_data": ["SEC_10K"],
        "data_locations": {},
        "threshold": threshold,
        "execution_mode": "AUTO",
        "tier": 1,
    }


class TestEvaluateCheckTiered:
    """Tests for tiered threshold evaluation."""

    def test_triggered_red_higher_is_worse(self) -> None:
        """Value exceeding red threshold triggers red."""
        check = _make_check(
            threshold_type="tiered",
            red=">25% from top customer",
            yellow=">15% from top customer",
            clear="<15% from top customer",
            factors=["F9"],
        )
        result = evaluate_signal(check, {"customer_conc": 30.0})
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"

    def test_triggered_yellow_higher_is_worse(self) -> None:
        """Value exceeding yellow but not red triggers yellow."""
        check = _make_check(
            threshold_type="tiered",
            red=">25% from top customer",
            yellow=">15% from top customer",
            clear="<15% from top customer",
            factors=["F9"],
        )
        result = evaluate_signal(check, {"customer_conc": 20.0})
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "yellow"

    def test_clear_higher_is_worse(self) -> None:
        """Value below all thresholds is CLEAR."""
        check = _make_check(
            threshold_type="tiered",
            red=">25% from top customer",
            yellow=">15% from top customer",
            clear="<15% from top customer",
            factors=["F9"],
        )
        result = evaluate_signal(check, {"customer_conc": 10.0})
        assert result.status == SignalStatus.CLEAR
        assert result.threshold_level == "clear"

    def test_triggered_lower_is_worse(self) -> None:
        """Value below red threshold triggers (lower = worse)."""
        check = _make_check(
            threshold_type="tiered",
            red="<1.0",
            yellow="<1.5",
            clear="Otherwise",
            factors=["F3"],
        )
        result = evaluate_signal(check, {"current_ratio": 0.8})
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"

    def test_clear_lower_is_worse(self) -> None:
        """Value above thresholds is CLEAR (lower = worse)."""
        check = _make_check(
            threshold_type="tiered",
            red="<1.0",
            yellow="<1.5",
            clear="Otherwise",
            factors=["F3"],
        )
        result = evaluate_signal(check, {"current_ratio": 2.0})
        assert result.status == SignalStatus.CLEAR

    def test_missing_data_skipped(self) -> None:
        """Missing data returns SKIPPED, not CLEAR."""
        check = _make_check(threshold_type="tiered", red="<1.0", yellow="<1.5")
        result = evaluate_signal(check, {"current_ratio": None})
        assert result.status == SignalStatus.SKIPPED
        assert "Required data" in result.evidence

    def test_qualitative_returns_info(self) -> None:
        """Qualitative tiered checks (non-numeric thresholds) return INFO."""
        check = _make_check(
            threshold_type="tiered",
            red="Prior SCA within 3 years",
            yellow="Prior SCA within 5 years",
            clear="No SCA history in 5+ years",
        )
        # Pass a string value -- no numeric comparison possible
        result = evaluate_signal(check, {"litigation_history": "No prior SCA"})
        assert result.status == SignalStatus.INFO
        assert result.value == "No prior SCA"


class TestEvaluateCheckInfoTypes:
    """Tests for info-only threshold types."""

    def test_info_type_with_data(self) -> None:
        """Info type returns INFO with data value."""
        check = _make_check(threshold_type="info")
        result = evaluate_signal(check, {"sector": "Technology"})
        assert result.status == SignalStatus.INFO
        assert result.value == "Technology"

    def test_info_type_missing_data(self) -> None:
        """Info type with missing data returns SKIPPED."""
        check = _make_check(threshold_type="info")
        result = evaluate_signal(check, {"sector": None})
        assert result.status == SignalStatus.SKIPPED

    def test_pattern_type(self) -> None:
        """Pattern type always returns INFO."""
        check = _make_check(
            threshold_type="pattern",
            detection=">15% single-day drop",
            red="Pattern detected",
        )
        result = evaluate_signal(check, {"event_collapse": "no pattern"})
        assert result.status == SignalStatus.INFO

    def test_classification_type(self) -> None:
        """Classification type returns INFO with classification value."""
        check = _make_check(
            threshold_type="classification",
            values=["BINARY_EVENT", "GROWTH_DARLING"],
        )
        result = evaluate_signal(check, {"classification": "GROWTH_DARLING"})
        assert result.status == SignalStatus.INFO
        assert result.value == "GROWTH_DARLING"


class TestEvaluateCheckBoolean:
    """Tests for boolean threshold evaluation."""

    def test_boolean_true_triggers(self) -> None:
        """Boolean True triggers (red condition)."""
        check = _make_check(
            threshold_type="boolean",
            red="Active SCA pending",
            clear="No SCA history",
            factors=["F1"],
        )
        result = evaluate_signal(check, {"active_sca": True})
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"

    def test_boolean_false_clears(self) -> None:
        """Boolean False clears."""
        check = _make_check(
            threshold_type="boolean",
            red="Active SCA pending",
            clear="No SCA history",
            factors=["F1"],
        )
        result = evaluate_signal(check, {"active_sca": False})
        assert result.status == SignalStatus.CLEAR

    def test_boolean_missing_skips(self) -> None:
        """Boolean with missing data returns SKIPPED."""
        check = _make_check(threshold_type="boolean", red="Active", clear="No")
        result = evaluate_signal(check, {"active_sca": None})
        assert result.status == SignalStatus.SKIPPED


class TestEvaluateCheckOtherTypes:
    """Tests for percentage, count, value threshold types."""

    def test_percentage_triggered(self) -> None:
        """Percentage threshold triggers on exceedance."""
        check = _make_check(
            threshold_type="percentage",
            red=">25%",
            yellow=">15%",
            clear="<15%",
        )
        result = evaluate_signal(check, {"pct_value": 30.0})
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"

    def test_count_triggered(self) -> None:
        """Count threshold triggers when count exceeds level."""
        check = _make_check(
            threshold_type="count",
            red=">3 flags",
            yellow=">2 flags",
        )
        result = evaluate_signal(check, {"flag_count": 5})
        assert result.status == SignalStatus.TRIGGERED

    def test_value_clear(self) -> None:
        """Value threshold clears when within limits."""
        check = _make_check(
            threshold_type="value",
            red=">50",
            yellow=">10",
            clear="<10",
        )
        result = evaluate_signal(check, {"exposure": 5.0})
        assert result.status == SignalStatus.CLEAR


# ---------------------------------------------------------------------------
# execute_signals tests
# ---------------------------------------------------------------------------


class TestExecuteChecks:
    """Tests for batch check execution."""

    def test_batch_execution(self) -> None:
        """Execute a batch of 3 mock checks."""
        from do_uw.models.state import ExtractedData

        checks = [
            _make_check(
                signal_id="C1",
                name="Check 1",
                threshold_type="info",
                section=1,
            ),
            _make_check(
                signal_id="C2",
                name="Check 2",
                threshold_type="boolean",
                red="Bad",
                clear="Good",
                section=4,
            ),
            _make_check(
                signal_id="C3",
                name="Check 3",
                threshold_type="tiered",
                red="<1.0",
                yellow="<1.5",
                section=3,
            ),
        ]

        extracted = ExtractedData()
        results = execute_signals(checks, extracted, company=None)
        assert len(results) == 3
        # All should be SKIPPED since ExtractedData is empty
        assert all(r.status == SignalStatus.SKIPPED for r in results)

    def test_filters_auto_only(self) -> None:
        """Only AUTO execution_mode checks are executed."""
        from do_uw.models.state import ExtractedData

        checks = [
            _make_check(signal_id="AUTO1", threshold_type="info"),
            {
                "id": "MANUAL1",
                "name": "Manual Check",
                "section": 1,
                "pillar": "P1",
                "factors": [],
                "required_data": [],
                "data_locations": {},
                "threshold": {"type": "info"},
                "execution_mode": "MANUAL_ONLY",
                "tier": 1,
            },
        ]

        extracted = ExtractedData()
        results = execute_signals(checks, extracted, company=None)
        assert len(results) == 1
        assert results[0].signal_id == "AUTO1"


# ---------------------------------------------------------------------------
# Helper for creating SourcedValue instances in tests
# ---------------------------------------------------------------------------


def _sv(value: Any, source: str = "test") -> Any:
    """Create a SourcedValue for testing."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Data mapper tests (Task 2)
# ---------------------------------------------------------------------------


class TestMapCheckDataDispatch:
    """Tests for map_signal_data section routing."""

    def test_section_1_dispatches_to_company(self) -> None:
        """Section 1 check routes to company mapper."""
        from do_uw.models.state import ExtractedData

        check_config: dict[str, Any] = {"section": 1}
        extracted = ExtractedData()
        result = map_signal_data("BIZ.CLASS.primary", check_config, extracted)
        # Empty dict since no company provided
        assert isinstance(result, dict)

    def test_section_3_dispatches_to_financial(self) -> None:
        """Section 3 check routes to financial mapper."""
        from do_uw.models.state import ExtractedData

        check_config: dict[str, Any] = {"section": 3}
        extracted = ExtractedData()
        result = map_signal_data("FIN.LIQ.position", check_config, extracted)
        assert isinstance(result, dict)

    def test_section_5_dispatches_to_governance(self) -> None:
        """Section 5 check routes to governance mapper."""
        from do_uw.models.state import ExtractedData

        check_config: dict[str, Any] = {"section": 5}
        extracted = ExtractedData()
        result = map_signal_data("GOV.EXEC.ceo", check_config, extracted)
        assert isinstance(result, dict)

    def test_unknown_section_returns_empty(self) -> None:
        """Unknown section returns empty dict."""
        from do_uw.models.state import ExtractedData

        check_config: dict[str, Any] = {"section": 99}
        extracted = ExtractedData()
        result = map_signal_data("UNKNOWN.001", check_config, extracted)
        assert result == {}


class TestMapFinancialFields:
    """Tests for _map_financial_fields."""

    def test_with_populated_financials(self) -> None:
        """Maps financial fields from non-None financials."""
        from do_uw.models.financials import (
            AuditProfile,
            DistressIndicators,
            DistressResult,
            DistressZone,
            ExtractedFinancials,
        )
        from do_uw.models.state import ExtractedData

        audit = AuditProfile(
            going_concern=_sv(False),
            opinion_type=_sv("unqualified"),
            tenure_years=_sv(5),
            is_big4=_sv(True),
            material_weaknesses=[_sv("MW1")],
            restatements=[],
        )
        distress = DistressIndicators(
            altman_z_score=DistressResult(
                score=3.5, zone=DistressZone.SAFE
            ),
            beneish_m_score=DistressResult(score=-2.5),
        )
        financials = ExtractedFinancials(
            audit=audit,
            distress=distress,
            liquidity=_sv({"current_ratio": 2.1, "quick_ratio": 1.5}),
            leverage=_sv({"debt_to_ebitda": 3.0, "interest_coverage": 8.0}),
            earnings_quality=_sv({"accruals_ratio": 0.05, "ocf_to_ni": 1.2}),
        )
        extracted = ExtractedData(financials=financials)

        # FIN.LIQ.position narrows to current_ratio via data_strategy.field_key
        result = map_signal_data(
            "FIN.LIQ.position",
            {"section": 3, "data_strategy": {"field_key": "current_ratio"}},
            extracted,
        )
        assert result["current_ratio"] == 2.1
        assert len(result) == 1  # narrowed to single field

        # FIN.DEBT.structure narrows to xbrl_debt_to_ebitda
        result2 = map_signal_data(
            "FIN.DEBT.structure", {"section": 3}, extracted
        )
        assert result2["xbrl_debt_to_ebitda"] == 3.0

        # FIN.ACCT.quality_indicators narrows to xbrl_altman_z_score
        result3 = map_signal_data(
            "FIN.ACCT.quality_indicators", {"section": 3}, extracted
        )
        assert result3["xbrl_altman_z_score"] == 3.5

    def test_with_none_financials(self) -> None:
        """Returns empty dict when financials is None."""
        from do_uw.models.state import ExtractedData

        extracted = ExtractedData(financials=None)
        result = map_signal_data(
            "FIN.LIQ.position", {"section": 3}, extracted
        )
        assert result == {}


class TestMapMarketFields:
    """Tests for _map_market_fields."""

    def test_with_populated_market(self) -> None:
        """Maps market fields from non-None market data."""
        from do_uw.models.market import (
            MarketSignals,
            ShortInterestProfile,
            StockPerformance,
        )
        from do_uw.models.state import ExtractedData

        stock = StockPerformance(
            decline_from_high_pct=_sv(-25.0),
            volatility_90d=_sv(0.45),
            returns_1y=_sv(-15.0),
        )
        short = ShortInterestProfile(
            short_pct_float=_sv(8.5),
            days_to_cover=_sv(4.2),
        )
        market = MarketSignals(
            stock=stock,
            short_interest=short,
        )
        extracted = ExtractedData(market=market)

        result = map_signal_data(
            "STOCK.PRICE.decline", {"section": 4}, extracted
        )

        assert result["decline_from_high"] == -25.0
        assert result["volatility_90d"] == 0.45
        assert result["short_interest_pct"] == 8.5
        assert result["short_interest_ratio"] == 4.2


class TestMapLitigationFields:
    """Tests for _map_litigation_fields."""

    def test_with_populated_litigation(self) -> None:
        """Maps litigation fields from non-None litigation data."""
        from do_uw.models.litigation import (
            CaseDetail,
            LitigationLandscape,
            SECEnforcementPipeline,
        )
        from do_uw.models.state import ExtractedData

        sca = CaseDetail(
            case_name=_sv("In re Acme Corp"),
            status=_sv("ACTIVE"),
            lead_counsel=_sv("Robbins Geller"),
            lead_counsel_tier=_sv(1),
        )
        sec = SECEnforcementPipeline(
            highest_confirmed_stage=_sv("FORMAL_INVESTIGATION"),
            aaer_count=_sv(0),
        )
        litigation = LitigationLandscape(
            securities_class_actions=[sca],
            sec_enforcement=sec,
            derivative_suits=[CaseDetail(status=_sv("ACTIVE"))],
        )
        extracted = ExtractedData(litigation=litigation)

        # LIT.SCA.active narrows to active_sca_count only
        result = map_signal_data(
            "LIT.SCA.active", {"section": 4}, extracted
        )
        assert result["active_sca_count"] == 1
        assert len(result) == 1

        # LIT.REG.sec_investigation narrows to sec_enforcement_stage
        result2 = map_signal_data(
            "LIT.REG.sec_investigation", {"section": 4}, extracted
        )
        assert result2["sec_enforcement_stage"] == "FORMAL_INVESTIGATION"

        # LIT.SCA.derivative narrows to derivative_suit_count
        result3 = map_signal_data(
            "LIT.SCA.derivative", {"section": 4}, extracted
        )
        assert result3["derivative_suit_count"] == 1


class TestMapGovernanceFields:
    """Tests for _map_governance_fields."""

    def test_with_populated_governance(self) -> None:
        """Maps governance fields from non-None governance data."""
        from do_uw.models.governance import BoardProfile, GovernanceData
        from do_uw.models.state import ExtractedData

        board = BoardProfile(
            independence_ratio=_sv(0.8),
            ceo_chair_duality=_sv(True),
            size=_sv(9),
            overboarded_count=_sv(1),
        )
        gov = GovernanceData(board=board)
        extracted = ExtractedData(governance=gov)

        # GOV.BOARD.independence narrows to xbrl_board_independence
        result = map_signal_data(
            "GOV.BOARD.independence", {"section": 5}, extracted
        )
        assert result["xbrl_board_independence"] == 80.0  # ratio 0.8 → 80%
        assert len(result) == 1

        # GOV.BOARD.ceo_chair narrows to ceo_chair_duality
        result2 = map_signal_data(
            "GOV.BOARD.ceo_chair", {"section": 5}, extracted
        )
        assert result2["ceo_chair_duality"] is True

        # GOV.BOARD.overboarding narrows to overboarded_directors
        result3 = map_signal_data(
            "GOV.BOARD.overboarding", {"section": 5}, extracted
        )
        assert result3["overboarded_directors"] == 1


# ---------------------------------------------------------------------------
# AnalyzeStage orchestrator tests (Task 2)
# ---------------------------------------------------------------------------


class TestAnalyzeStage:
    """Tests for AnalyzeStage orchestration."""

    def test_validate_input_raises_when_extract_not_complete(self) -> None:
        """Raises ValueError when extract stage not completed."""
        from do_uw.models.state import AnalysisState
        from do_uw.stages.analyze import AnalyzeStage

        state = AnalysisState(ticker="TEST")
        stage = AnalyzeStage()
        with pytest.raises(ValueError, match="Extract stage must be completed"):
            stage.validate_input(state)

    def test_validate_input_passes_when_extract_complete(self) -> None:
        """No error when extract stage is completed."""
        from do_uw.models.common import StageStatus
        from do_uw.models.state import AnalysisState
        from do_uw.stages.analyze import AnalyzeStage

        state = AnalysisState(ticker="TEST")
        state.stages["extract"].status = StageStatus.COMPLETED
        stage = AnalyzeStage()
        stage.validate_input(state)  # Should not raise

    @patch("do_uw.stages.analyze.BrainLoader")
    def test_run_populates_state_analysis(
        self, mock_loader_cls: MagicMock
    ) -> None:
        """AnalyzeStage.run populates state.analysis with correct counts."""
        from do_uw.models.common import StageStatus
        from do_uw.models.state import AnalysisState, ExtractedData
        from do_uw.stages.analyze import AnalyzeStage

        # Set up mock BrainLoader to return a small set of checks
        mock_brain = MagicMock()
        mock_brain.checks = {
            "signals": [
                {
                    "id": "TEST.001",
                    "name": "Test Info",
                    "section": 1,
                    "pillar": "P1",
                    "factors": [],
                    "required_data": [],
                    "data_locations": {},
                    "threshold": {"type": "info"},
                    "execution_mode": "AUTO",
                    "tier": 1,
                },
                {
                    "id": "TEST.002",
                    "name": "Test Tiered",
                    "section": 3,
                    "pillar": "P1",
                    "factors": ["F3"],
                    "required_data": ["SEC_10K"],
                    "data_locations": {},
                    "threshold": {
                        "type": "tiered",
                        "red": "<1.0",
                        "yellow": "<1.5",
                    },
                    "execution_mode": "AUTO",
                    "tier": 1,
                },
            ],
        }
        mock_loader_cls.return_value.load_all.return_value = mock_brain

        state = AnalysisState(ticker="TEST")
        state.stages["extract"].status = StageStatus.COMPLETED
        state.extracted = ExtractedData()

        stage = AnalyzeStage()
        stage.run(state)

        # Verify state.analysis is populated
        assert state.analysis is not None
        assert state.analysis.checks_executed == 2
        # Both checks should be SKIPPED (no data available)
        assert state.analysis.checks_skipped == 2
        assert state.analysis.checks_passed == 0
        assert state.analysis.checks_failed == 0
        assert len(state.analysis.signal_results) == 2
        assert "TEST.001" in state.analysis.signal_results
        assert "TEST.002" in state.analysis.signal_results

        # Verify stage marked completed
        assert state.stages["analyze"].status == StageStatus.COMPLETED

    @patch("do_uw.stages.analyze.BrainLoader")
    def test_run_fails_without_extracted(
        self, mock_loader_cls: MagicMock
    ) -> None:
        """AnalyzeStage.run raises when state.extracted is None."""
        from do_uw.models.common import StageStatus
        from do_uw.models.state import AnalysisState
        from do_uw.stages.analyze import AnalyzeStage

        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}
        mock_loader_cls.return_value.load_all.return_value = mock_brain

        state = AnalysisState(ticker="TEST")
        state.stages["extract"].status = StageStatus.COMPLETED
        state.extracted = None

        stage = AnalyzeStage()
        with pytest.raises(ValueError, match=r"state\.extracted is None"):
            stage.run(state)

        # Verify stage marked failed
        assert state.stages["analyze"].status == StageStatus.FAILED
