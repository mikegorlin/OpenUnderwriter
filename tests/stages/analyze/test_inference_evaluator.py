"""Tests for multi-signal inference pattern evaluator.

Phase 32-10: Verifies that INFERENCE_PATTERN checks use a dedicated
evaluator examining multiple data fields with pattern-specific logic.

Coverage:
- Dispatch by pattern_ref to correct handler
- Generic multi-signal: all active, all clear, partial, insufficient
- Stock pattern handler with market signals
- Governance effectiveness handler with governance signals
- Executive pattern handler with insider/turnover signals
- Fallback to generic when pattern_ref not in registry
- Single-value graceful degradation
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus
from do_uw.stages.analyze.inference_evaluator import (
    PATTERN_HANDLERS,
    _evaluate_executive_pattern,
    _evaluate_governance_effectiveness,
    _evaluate_multi_signal,
    _evaluate_stock_pattern,
    _is_active_signal,
    evaluate_inference_pattern,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_check(
    signal_id: str = "TEST.INFER.001",
    name: str = "Test Inference Check",
    content_type: str = "INFERENCE_PATTERN",
    section: int = 2,
    factors: list[str] | None = None,
    threshold: dict[str, Any] | None = None,
    pattern_ref: str = "",
    execution_mode: str = "AUTO",
    **extra: Any,
) -> dict[str, Any]:
    """Build a minimal INFERENCE_PATTERN check config dict."""
    check: dict[str, Any] = {
        "id": signal_id,
        "name": name,
        "content_type": content_type,
        "section": section,
        "factors": factors or ["F2"],
        "threshold": threshold or {"type": "pattern"},
        "execution_mode": execution_mode,
        "required_data": ["MARKET"],
        "data_locations": {},
        "pattern_ref": pattern_ref,
    }
    check.update(extra)
    return check


# ---------------------------------------------------------------------------
# 1. Dispatch tests
# ---------------------------------------------------------------------------


class TestDispatchByPatternRef:
    """evaluate_inference_pattern dispatches to correct handler."""

    def test_dispatches_to_stock_pattern(self) -> None:
        """EVENT_COLLAPSE -> _evaluate_stock_pattern."""
        check = _make_check(pattern_ref="EVENT_COLLAPSE")
        data = {"drop_pct": 20, "trigger": "earnings_miss", "peers_drop": 2}
        result = evaluate_inference_pattern(check, data)
        assert isinstance(result, SignalResult)
        assert "EVENT_COLLAPSE" in result.evidence

    def test_dispatches_to_governance(self) -> None:
        """AUDIT_COMMITTEE -> _evaluate_governance_effectiveness."""
        check = _make_check(pattern_ref="AUDIT_COMMITTEE", section=5)
        data = {"audit_committee": True, "independence": 0.8}
        result = evaluate_inference_pattern(check, data)
        assert isinstance(result, SignalResult)
        assert "AUDIT_COMMITTEE" in result.evidence

    def test_dispatches_to_executive(self) -> None:
        """CLUSTER_SELLING -> _evaluate_executive_pattern."""
        check = _make_check(pattern_ref="CLUSTER_SELLING", section=5)
        data = {"insider_sales_count": 5, "window_days": 20}
        result = evaluate_inference_pattern(check, data)
        assert isinstance(result, SignalResult)
        assert "CLUSTER_SELLING" in result.evidence

    def test_unknown_pattern_ref_falls_back_to_generic(self) -> None:
        """Unknown pattern_ref uses _evaluate_multi_signal."""
        check = _make_check(pattern_ref="TOTALLY_UNKNOWN_PATTERN")
        data = {"signal_a": True, "signal_b": True, "signal_c": False}
        result = evaluate_inference_pattern(check, data)
        assert isinstance(result, SignalResult)
        # Generic evaluator does not include pattern_ref in evidence
        assert "TOTALLY_UNKNOWN_PATTERN" not in result.evidence

    def test_all_19_pattern_refs_have_handlers(self) -> None:
        """Every known pattern_ref should be in PATTERN_HANDLERS."""
        expected = {
            "EVENT_COLLAPSE", "INFORMED_TRADING", "PRICE_CASCADE",
            "PEER_DIVERGENCE", "DEATH_SPIRAL", "SHORT_ATTACK",
            "AUDIT_COMMITTEE", "AUDIT_OPINION", "AUDITOR_CHANGE",
            "MATERIAL_WEAKNESS", "ISS_SCORE", "PROXY_ADVISORY",
            "SOX_404", "SIG_DEFICIENCY", "LATE_FILING", "NT_FILING",
            "CLUSTER_SELLING", "NON_10B51", "C_SUITE_TURNOVER",
        }
        assert set(PATTERN_HANDLERS.keys()) == expected


# ---------------------------------------------------------------------------
# 2. Generic multi-signal evaluator tests
# ---------------------------------------------------------------------------


class TestMultiSignalGeneric:
    """_evaluate_multi_signal: generic multi-signal evaluation."""

    def test_all_active_triggers(self) -> None:
        """All signals present and active -> TRIGGERED."""
        check = _make_check()
        data = {"sig_a": 10, "sig_b": True, "sig_c": "detected"}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert "3 of 3" in result.evidence

    def test_all_present_none_active_clears(self) -> None:
        """All signals present but none active -> CLEAR."""
        check = _make_check()
        data = {"sig_a": 0, "sig_b": False, "sig_c": ""}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.CLEAR
        assert "0 of 3" in result.evidence

    def test_majority_active_triggers(self) -> None:
        """Majority of signals active -> TRIGGERED."""
        check = _make_check()
        data = {"sig_a": 5, "sig_b": True, "sig_c": 0}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert "2 of 3" in result.evidence

    def test_minority_active_info(self) -> None:
        """Less than majority active -> INFO."""
        check = _make_check()
        data = {"sig_a": 5, "sig_b": 0, "sig_c": 0, "sig_d": 0}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.INFO
        assert "not fully formed" in result.evidence

    def test_insufficient_data_skips(self) -> None:
        """Most signals None -> SKIPPED (needs >1 present to avoid single-value fallback)."""
        check = _make_check()
        # 3 None out of 5 total -> majority None but 2 present (avoids single-value fallback)
        data = {"sig_a": None, "sig_b": None, "sig_c": 5, "sig_d": None, "sig_e": 3}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.SKIPPED
        assert "Insufficient data" in result.evidence

    def test_empty_data_skips(self) -> None:
        """Empty data dict -> SKIPPED."""
        check = _make_check()
        data: dict[str, Any] = {}
        result = _evaluate_multi_signal(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_evidence_lists_active_signals(self) -> None:
        """Evidence should name the active signals."""
        check = _make_check()
        data = {"drop_pct": 20, "volume_spike": True, "peer_ok": 0}
        result = _evaluate_multi_signal(check, data)
        assert "drop_pct" in result.evidence
        assert "volume_spike" in result.evidence


# ---------------------------------------------------------------------------
# 3. Stock pattern handler tests
# ---------------------------------------------------------------------------


class TestStockPattern:
    """_evaluate_stock_pattern: market signal detection."""

    def test_event_collapse_all_signals(self) -> None:
        """Event collapse with all signals active -> TRIGGERED."""
        check = _make_check(
            signal_id="STOCK.PATTERN.event_collapse",
            pattern_ref="EVENT_COLLAPSE",
            threshold={
                "type": "pattern",
                "detection": ">15% single-day drop + company-specific trigger + peers dropped <5%",
                "red": "Pattern detected with fraud/accounting trigger",
                "yellow": "Pattern detected with earnings/guidance trigger",
            },
        )
        data = {
            "single_day_drop": 18,
            "company_trigger": "accounting_fraud",
            "peer_drop": 2,
        }
        result = _evaluate_stock_pattern(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert "EVENT_COLLAPSE" in result.evidence
        assert "3 of 3" in result.evidence

    def test_stock_pattern_no_signals_clears(self) -> None:
        """Stock pattern with no active signals -> CLEAR."""
        check = _make_check(
            pattern_ref="PRICE_CASCADE",
            threshold={"type": "pattern", "detection": "test"},
        )
        data = {"decline_days": 0, "recovery": False, "shorts": 0}
        result = _evaluate_stock_pattern(check, data)
        assert result.status == SignalStatus.CLEAR

    def test_stock_pattern_partial_info(self) -> None:
        """Stock pattern with minority active -> INFO."""
        check = _make_check(
            pattern_ref="DEATH_SPIRAL",
            threshold={"type": "pattern", "detection": "test"},
        )
        data = {"price_low": 3.5, "convertibles": 0, "shorts": 0, "delisting": 0}
        result = _evaluate_stock_pattern(check, data)
        assert result.status == SignalStatus.INFO

    def test_stock_pattern_no_data_skips(self) -> None:
        """Stock pattern with no data -> SKIPPED."""
        check = _make_check(pattern_ref="SHORT_ATTACK")
        data = {"short_report": None, "short_spike": None}
        result = _evaluate_stock_pattern(check, data)
        assert result.status == SignalStatus.SKIPPED


# ---------------------------------------------------------------------------
# 4. Governance effectiveness handler tests
# ---------------------------------------------------------------------------


class TestGovernanceEffectiveness:
    """_evaluate_governance_effectiveness: governance cross-referencing."""

    def test_multiple_governance_signals_triggers(self) -> None:
        """2+ governance signals active -> TRIGGERED."""
        check = _make_check(
            signal_id="GOV.EFFECT.material_weakness",
            pattern_ref="MATERIAL_WEAKNESS",
            section=5,
        )
        data = {
            "material_weakness": True,
            "audit_opinion": "qualified",
            "auditor_change": False,
        }
        result = _evaluate_governance_effectiveness(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert "MATERIAL_WEAKNESS" in result.evidence

    def test_single_governance_signal_info(self) -> None:
        """Single governance signal -> INFO."""
        check = _make_check(pattern_ref="AUDITOR_CHANGE", section=5)
        data = {
            "auditor_changed": True,
            "audit_opinion": 0,
            "material_weakness": 0,
        }
        result = _evaluate_governance_effectiveness(check, data)
        assert result.status == SignalStatus.INFO
        assert "Single governance concern" in result.evidence

    def test_no_governance_signals_clears(self) -> None:
        """No governance signals active -> CLEAR."""
        check = _make_check(pattern_ref="ISS_SCORE", section=5)
        data = {"iss_score": 0, "proxy_vote": 0}
        result = _evaluate_governance_effectiveness(check, data)
        assert result.status == SignalStatus.CLEAR

    def test_governance_no_data_skips(self) -> None:
        """Governance with no data -> SKIPPED."""
        check = _make_check(pattern_ref="SOX_404", section=5)
        data = {"sox_finding": None, "internal_controls": None}
        result = _evaluate_governance_effectiveness(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_three_plus_signals_red(self) -> None:
        """3+ governance signals active -> red threshold level."""
        check = _make_check(pattern_ref="LATE_FILING", section=5)
        data = {
            "late_filing": True,
            "nt_filing": True,
            "sox_issue": True,
        }
        result = _evaluate_governance_effectiveness(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"


# ---------------------------------------------------------------------------
# 5. Executive pattern handler tests
# ---------------------------------------------------------------------------


class TestExecutivePattern:
    """_evaluate_executive_pattern: insider/turnover patterns."""

    def test_cluster_selling_triggers(self) -> None:
        """Cluster selling with multiple signals -> TRIGGERED."""
        check = _make_check(
            signal_id="EXEC.INSIDER.cluster_selling",
            pattern_ref="CLUSTER_SELLING",
            section=5,
            threshold={"type": "boolean", "triggered": "3+ officers selling within 30-day window"},
        )
        data = {"insider_sales_count": 4, "window_days": 20}
        result = _evaluate_executive_pattern(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert "CLUSTER_SELLING" in result.evidence

    def test_c_suite_turnover_partial(self) -> None:
        """C-suite turnover with mixed signals -> depends on active count."""
        check = _make_check(
            pattern_ref="C_SUITE_TURNOVER",
            section=5,
            threshold={"type": "tiered", "red": "3+ departures"},
        )
        data = {"departures": 2, "new_hires": 0, "tenure_changes": 0}
        result = _evaluate_executive_pattern(check, data)
        # 1 of 3 active -> INFO
        assert result.status == SignalStatus.INFO

    def test_executive_no_signals_clears(self) -> None:
        """No executive signals active -> CLEAR."""
        check = _make_check(pattern_ref="NON_10B51", section=5)
        data = {"discretionary_pct": 0, "total_sales": 0}
        result = _evaluate_executive_pattern(check, data)
        assert result.status == SignalStatus.CLEAR

    def test_executive_no_data_skips(self) -> None:
        """Executive pattern with no data -> SKIPPED."""
        check = _make_check(pattern_ref="CLUSTER_SELLING", section=5)
        data = {"transactions": None}
        result = _evaluate_executive_pattern(check, data)
        assert result.status == SignalStatus.SKIPPED


# ---------------------------------------------------------------------------
# 6. Single-value fallback / backward compatibility
# ---------------------------------------------------------------------------


class TestSingleValueFallback:
    """Single-value data still produces reasonable results."""

    def test_single_value_returns_info(self) -> None:
        """Single non-None value -> INFO (graceful degradation, cannot confirm pattern)."""
        check = _make_check(pattern_ref="EVENT_COLLAPSE")
        data = {"single_day_drop": 20, "trigger": None, "peers": None}
        result = evaluate_inference_pattern(check, data)
        # Only 1 of 3 keys is non-None -> single-value fallback returns INFO
        assert result.status == SignalStatus.INFO
        assert "Single signal only" in result.evidence

    def test_single_value_in_dict(self) -> None:
        """Dict with exactly one non-None value -> INFO fallback."""
        check = _make_check(pattern_ref="TOTALLY_NEW_PATTERN")
        data = {"only_signal": 42}
        result = evaluate_inference_pattern(check, data)
        assert result.status == SignalStatus.INFO
        assert "Single signal only" in result.evidence

    def test_all_none_returns_skipped(self) -> None:
        """All None values -> SKIPPED."""
        check = _make_check(pattern_ref="EVENT_COLLAPSE")
        data = {"a": None, "b": None}
        result = evaluate_inference_pattern(check, data)
        assert result.status == SignalStatus.SKIPPED


# ---------------------------------------------------------------------------
# 7. Signal detection helper
# ---------------------------------------------------------------------------


class TestIsActiveSignal:
    """_is_active_signal correctly classifies signal values."""

    def test_positive_number_active(self) -> None:
        assert _is_active_signal(5) is True
        assert _is_active_signal(0.5) is True

    def test_zero_not_active(self) -> None:
        assert _is_active_signal(0) is False
        assert _is_active_signal(0.0) is False

    def test_bool_true_active(self) -> None:
        assert _is_active_signal(True) is True

    def test_bool_false_not_active(self) -> None:
        assert _is_active_signal(False) is False

    def test_nonempty_string_active(self) -> None:
        assert _is_active_signal("detected") is True
        assert _is_active_signal("yes") is True

    def test_empty_or_na_string_not_active(self) -> None:
        assert _is_active_signal("") is False
        assert _is_active_signal("none") is False
        assert _is_active_signal("N/A") is False
        assert _is_active_signal("not available") is False
        assert _is_active_signal("No") is False

    def test_nonempty_list_active(self) -> None:
        assert _is_active_signal([1, 2]) is True

    def test_empty_list_not_active(self) -> None:
        assert _is_active_signal([]) is False

    def test_nonempty_dict_active(self) -> None:
        assert _is_active_signal({"a": 1}) is True

    def test_empty_dict_not_active(self) -> None:
        assert _is_active_signal({}) is False


# ---------------------------------------------------------------------------
# 8. Result structure tests
# ---------------------------------------------------------------------------


class TestResultStructure:
    """Results have correct check metadata."""

    def test_signal_id_preserved(self) -> None:
        check = _make_check(signal_id="STOCK.PATTERN.event_collapse", pattern_ref="EVENT_COLLAPSE")
        data = {"a": 1, "b": 2}
        result = evaluate_inference_pattern(check, data)
        assert result.signal_id == "STOCK.PATTERN.event_collapse"

    def test_section_preserved(self) -> None:
        check = _make_check(section=5, pattern_ref="AUDIT_COMMITTEE")
        data = {"a": 1, "b": 2}
        result = evaluate_inference_pattern(check, data)
        assert result.section == 5

    def test_factors_preserved(self) -> None:
        check = _make_check(factors=["F2", "F4"], pattern_ref="SHORT_ATTACK")
        data = {"a": 1, "b": 2}
        result = evaluate_inference_pattern(check, data)
        assert result.factors == ["F2", "F4"]

    def test_needs_calibration_false(self) -> None:
        """Inference pattern checks never need calibration."""
        check = _make_check(pattern_ref="DEATH_SPIRAL")
        data = {"a": 1, "b": 2}
        result = evaluate_inference_pattern(check, data)
        assert result.needs_calibration is False


# ---------------------------------------------------------------------------
# 9. Integration tests: signal_engine dispatch
# ---------------------------------------------------------------------------


class TestCheckEngineIntegration:
    """Verify signal_engine routes INFERENCE_PATTERN to the new evaluator."""

    def test_execute_signals_routes_inference_pattern(self) -> None:
        """execute_signals should route INFERENCE_PATTERN to evaluate_inference_pattern."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        check = _make_check(
            signal_id="STOCK.PATTERN.event_collapse",
            pattern_ref="EVENT_COLLAPSE",
            threshold={"type": "pattern", "detection": "test"},
            section=2,
            factors=["F2"],
            category="DECISION_DRIVING",
            signal_type="PATTERN",
            required_data=["MARKET"],
            pillar="P1_WHAT_WRONG",
        )
        extracted = ExtractedData()
        results = execute_signals([check], extracted)
        assert len(results) == 1
        result = results[0]
        assert result.signal_id == "STOCK.PATTERN.event_collapse"

    def test_inference_pattern_gets_classification_metadata(self) -> None:
        """INFERENCE_PATTERN result should have classification metadata from check."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        check = _make_check(
            signal_id="GOV.EFFECT.material_weakness",
            pattern_ref="MATERIAL_WEAKNESS",
            section=5,
            factors=["F10"],
            category="CONTEXT_DISPLAY",
            signal_type="PATTERN",
            hazard_or_signal="HAZARD",
            required_data=["SEC_DEF14A"],
            pillar="P2_WHO_BLAMED",
        )
        extracted = ExtractedData()
        results = execute_signals([check], extracted)
        result = results[0]
        assert result.category == "CONTEXT_DISPLAY"
        assert result.signal_type == "PATTERN"
        assert result.hazard_or_signal == "HAZARD"

    def test_inference_pattern_gets_traceability(self) -> None:
        """INFERENCE_PATTERN result should have the 5-link traceability chain."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        check = _make_check(
            signal_id="EXEC.INSIDER.cluster_selling",
            pattern_ref="CLUSTER_SELLING",
            section=5,
            factors=["F6", "F9"],
            category="DECISION_DRIVING",
            signal_type="PATTERN",
            required_data=["SEC_FORM4"],
            data_locations={"SEC_FORM4": ["all_transactions"]},
            pillar="P2_WHO_SUE",
        )
        extracted = ExtractedData()
        results = execute_signals([check], extracted)
        result = results[0]
        # Traceability links should be populated
        assert result.trace_output, f"trace_output empty: {result.trace_output}"
        assert "SECT5" in result.trace_output
        assert result.trace_evaluation, f"trace_evaluation empty: {result.trace_evaluation}"
        # With no data, evaluator returns SKIPPED, so traceability says skipped
        # The key test is that _apply_traceability was called (trace_output populated)
        assert result.trace_data_source, f"trace_data_source empty: {result.trace_data_source}"
        assert "SEC_FORM4" in result.trace_data_source
        assert result.trace_scoring, f"trace_scoring empty: {result.trace_scoring}"
        assert "F6" in result.trace_scoring

    def test_evaluative_check_not_affected(self) -> None:
        """EVALUATIVE_CHECK should still go through evaluate_signal()."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        check: dict[str, Any] = {
            "id": "FIN.LIQ.position",
            "name": "Liquidity Position",
            "content_type": "EVALUATIVE_CHECK",
            "section": 3,
            "factors": ["F1"],
            "threshold": {"type": "tiered", "red": ">5.0", "yellow": ">3.0"},
            "execution_mode": "AUTO",
            "required_data": ["SEC_10K"],
            "data_locations": {},
        }
        extracted = ExtractedData()
        results = execute_signals([check], extracted)
        assert len(results) == 1
        # With no data, should be SKIPPED (not routed to inference evaluator)
        assert results[0].status == SignalStatus.SKIPPED

    def test_mixed_content_types_separate_paths(self) -> None:
        """Mix of content types should go through different code paths."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        evaluative = {
            "id": "FIN.LEV.ratio",
            "name": "Leverage",
            "content_type": "EVALUATIVE_CHECK",
            "section": 3,
            "factors": ["F1"],
            "threshold": {"type": "info"},
            "execution_mode": "AUTO",
            "required_data": [],
            "data_locations": {},
        }
        inference = _make_check(
            signal_id="STOCK.PATTERN.cascade",
            pattern_ref="PRICE_CASCADE",
            section=2,
            factors=["F2"],
            category="DECISION_DRIVING",
            signal_type="PATTERN",
            required_data=["MARKET_PRICE"],
            pillar="P1_WHAT_WRONG",
        )
        management = {
            "id": "BIZ.PROF.segments",
            "name": "Revenue Segments",
            "content_type": "MANAGEMENT_DISPLAY",
            "section": 1,
            "factors": [],
            "threshold": {"type": "info"},
            "execution_mode": "AUTO",
            "required_data": [],
            "data_locations": {},
        }
        extracted = ExtractedData()
        results = execute_signals([evaluative, inference, management], extracted)
        assert len(results) == 3
        # All should produce results regardless of content type
        assert results[0].signal_id == "FIN.LEV.ratio"
        assert results[1].signal_id == "STOCK.PATTERN.cascade"
        assert results[2].signal_id == "BIZ.PROF.segments"
