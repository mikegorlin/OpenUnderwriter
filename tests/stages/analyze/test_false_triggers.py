"""Regression tests for Phase 33-02 false trigger fixes.

Verifies that the 5 known false triggers identified in the QUESTION-AUDIT
do not recur. Each test targets a specific check where incorrect field
routing or miscalibrated thresholds produced misleading TRIGGERED results.

False triggers fixed:
1. BIZ.DEPEND.labor: employee_count treated as labor flag count
2. BIZ.DEPEND.key_person: employee_count treated as customer concentration
3. GOV.BOARD.ceo_chair: boolean duality evaluated as numeric vs <50%
4. GOV.PAY.peer_comparison: pay ratio (533) compared against percentile (>75)
5. FIN.LIQ.position: current ratio (0.89) compared against months runway (<6)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK, narrow_result
from do_uw.stages.analyze.signal_helpers import _extract_comparison, try_numeric_compare
from do_uw.stages.analyze.signal_results import SignalStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CHECKS_JSON = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "brain" / "config" / "signals.json"


def _load_check(signal_id: str) -> dict[str, Any]:
    """Load a specific check definition from signals.json."""
    with open(CHECKS_JSON) as f:
        data = json.load(f)
    for c in data["signals"]:
        if c.get("id") == signal_id:
            return c
    raise KeyError(f"Check {signal_id} not found in signals.json")


# ---------------------------------------------------------------------------
# Test 1: BIZ.DEPEND.labor must NOT use employee_count
# ---------------------------------------------------------------------------


class TestLaborCheckDoesNotUseEmployeeCount:
    """BIZ.DEPEND.labor threshold expects labor risk flag count, not employee_count."""

    def test_field_for_check_not_employee_count(self) -> None:
        """Legacy FIELD_FOR_CHECK must not route labor to employee_count."""
        field = FIELD_FOR_CHECK.get("BIZ.DEPEND.labor")
        assert field != "employee_count", (
            "BIZ.DEPEND.labor must not route to employee_count "
            "(was false trigger: 150,000 employees > 2 labor flags)"
        )

    def test_data_strategy_field_key_not_employee_count(self) -> None:
        """Declarative data_strategy.field_key must not be employee_count."""
        check = _load_check("BIZ.DEPEND.labor")
        field_key = check.get("data_strategy", {}).get("field_key")
        assert field_key != "employee_count", (
            "BIZ.DEPEND.labor data_strategy.field_key must not be employee_count"
        )

    def test_narrow_result_excludes_employee_count(self) -> None:
        """narrow_result for labor check must not return employee_count value."""
        check = _load_check("BIZ.DEPEND.labor")
        # Simulate mapper output with employee_count but no labor risk data
        data = {"employee_count": 150000, "sector": "Technology"}
        result = narrow_result("BIZ.DEPEND.labor", data, signal_def=check)
        # Should NOT contain employee_count (field_key is labor_risk_flag_count)
        assert result.get("employee_count") != 150000, (
            "labor check must not receive employee_count value"
        )


# ---------------------------------------------------------------------------
# Test 2: BIZ.DEPEND.key_person must NOT use employee_count
# ---------------------------------------------------------------------------


class TestKeyPersonCheckDoesNotUseEmployeeCount:
    """BIZ.DEPEND.key_person is 'Customer Concentration Risk', not employee_count."""

    def test_field_for_check_not_employee_count(self) -> None:
        """Legacy FIELD_FOR_CHECK must not route key_person to employee_count."""
        field = FIELD_FOR_CHECK.get("BIZ.DEPEND.key_person")
        assert field != "employee_count", (
            "BIZ.DEPEND.key_person must not route to employee_count "
            "(check name is 'Customer Concentration Risk')"
        )

    def test_data_strategy_field_key_not_employee_count(self) -> None:
        """Declarative data_strategy.field_key must not be employee_count."""
        check = _load_check("BIZ.DEPEND.key_person")
        field_key = check.get("data_strategy", {}).get("field_key")
        assert field_key != "employee_count", (
            "BIZ.DEPEND.key_person data_strategy.field_key must not be employee_count"
        )

    def test_narrow_result_excludes_employee_count(self) -> None:
        """narrow_result for key_person check must not return employee_count value."""
        check = _load_check("BIZ.DEPEND.key_person")
        data = {"employee_count": 150000, "customer_concentration": None}
        result = narrow_result("BIZ.DEPEND.key_person", data, signal_def=check)
        # Should return customer_concentration field (even if None -> empty dict)
        assert result.get("employee_count") != 150000, (
            "key_person check must not receive employee_count value"
        )


# ---------------------------------------------------------------------------
# Test 3: GOV.BOARD.ceo_chair must evaluate as boolean, not numeric
# ---------------------------------------------------------------------------


class TestCeoChairBooleanEvaluation:
    """GOV.BOARD.ceo_chair must use boolean threshold, not tiered with <50%."""

    def test_threshold_type_is_boolean(self) -> None:
        """Threshold type must be 'boolean', not 'tiered'."""
        check = _load_check("GOV.BOARD.ceo_chair")
        threshold = check["threshold"]
        assert threshold["type"] == "boolean", (
            f"GOV.BOARD.ceo_chair threshold type must be 'boolean', "
            f"got '{threshold['type']}' -- was false trigger when tiered "
            f"threshold '<50%' matched against boolean 1.0"
        )

    def test_threshold_red_has_no_numeric_extractor(self) -> None:
        """Red threshold text must not contain extractable numeric values."""
        check = _load_check("GOV.BOARD.ceo_chair")
        red_text = check["threshold"].get("red", "")
        # _extract_comparison should return None (no <N or >N pattern)
        result = _extract_comparison(red_text)
        assert result is None, (
            f"GOV.BOARD.ceo_chair red threshold should not have extractable "
            f"numeric comparison, but got {result} from '{red_text}'"
        )

    def test_boolean_true_does_not_numeric_compare_as_lt_50(self) -> None:
        """Boolean True (1.0) must not trigger via numeric <50.0 comparison."""
        check = _load_check("GOV.BOARD.ceo_chair")
        threshold = check["threshold"]
        # try_numeric_compare should return None for boolean thresholds
        result = try_numeric_compare(1.0, threshold)
        assert result is None or result[0] != SignalStatus.TRIGGERED or result[1] != "red", (
            "Boolean value 1.0 must not false-trigger as 'below red threshold 50.0'"
        )


# ---------------------------------------------------------------------------
# Test 4: FIN.LIQ.position threshold must use current ratio values
# ---------------------------------------------------------------------------


class TestLiquidityThresholdCalibration:
    """FIN.LIQ.position threshold must use reasonable current ratio values."""

    def test_red_threshold_is_reasonable_current_ratio(self) -> None:
        """Red threshold must be a reasonable current ratio (< 2.0, not 6.0)."""
        check = _load_check("FIN.LIQ.position")
        red_text = check["threshold"].get("red", "")
        comparison = _extract_comparison(red_text)
        assert comparison is not None, (
            f"FIN.LIQ.position red threshold must have extractable numeric value, "
            f"got None from '{red_text}'"
        )
        op, value = comparison
        assert value < 2.0, (
            f"FIN.LIQ.position red threshold {value} is too high for a current ratio "
            f"(was 6.0 from '<6 months runway', should be around 1.0)"
        )

    def test_current_ratio_0_89_triggers_red(self) -> None:
        """Current ratio 0.89 should trigger red (below 1.0 is bad)."""
        check = _load_check("FIN.LIQ.position")
        threshold = check["threshold"]
        result = try_numeric_compare(0.89, threshold)
        assert result is not None, "Current ratio 0.89 should produce a comparison result"
        status, level, _ = result
        assert status == SignalStatus.TRIGGERED, (
            f"Current ratio 0.89 should trigger, got {status}"
        )
        assert level == "red", (
            f"Current ratio 0.89 should be red, got {level}"
        )

    def test_current_ratio_1_2_triggers_yellow(self) -> None:
        """Current ratio 1.2 should trigger yellow (below 1.5 but above 1.0)."""
        check = _load_check("FIN.LIQ.position")
        threshold = check["threshold"]
        result = try_numeric_compare(1.2, threshold)
        assert result is not None, "Current ratio 1.2 should produce a comparison result"
        status, level, _ = result
        assert status == SignalStatus.TRIGGERED, (
            f"Current ratio 1.2 should trigger, got {status}"
        )
        assert level == "yellow", (
            f"Current ratio 1.2 should be yellow, got {level}"
        )

    def test_current_ratio_2_0_is_clear(self) -> None:
        """Current ratio 2.0 should be clear (above 1.5)."""
        check = _load_check("FIN.LIQ.position")
        threshold = check["threshold"]
        result = try_numeric_compare(2.0, threshold)
        assert result is not None, "Current ratio 2.0 should produce a comparison result"
        status, _, _ = result
        assert status == SignalStatus.CLEAR, (
            f"Current ratio 2.0 should be clear, got {status}"
        )


# ---------------------------------------------------------------------------
# Test 5: GOV.PAY.peer_comparison threshold must match pay ratio units
# ---------------------------------------------------------------------------


class TestPeerComparisonUnitsMatch:
    """GOV.PAY.peer_comparison threshold must use CEO pay ratio units."""

    def test_threshold_values_are_pay_ratio_scale(self) -> None:
        """Threshold numeric values must be in pay ratio scale (hundreds), not percentile (0-100)."""
        check = _load_check("GOV.PAY.peer_comparison")
        red_text = check["threshold"].get("red", "")
        comparison = _extract_comparison(red_text)
        assert comparison is not None, (
            f"GOV.PAY.peer_comparison red threshold must have extractable value"
        )
        _, value = comparison
        assert value >= 100, (
            f"GOV.PAY.peer_comparison red threshold {value} looks like a percentile, "
            f"not a pay ratio. CEO pay ratios are typically 100-1000+. "
            f"Was >75 (percentile) which false-triggered on ratio 533."
        )

    def test_pay_ratio_533_triggers_correctly(self) -> None:
        """CEO pay ratio 533:1 should trigger appropriately with calibrated thresholds."""
        check = _load_check("GOV.PAY.peer_comparison")
        threshold = check["threshold"]
        result = try_numeric_compare(533.0, threshold)
        assert result is not None, "Pay ratio 533 should produce a comparison result"
        status, level, _ = result
        # 533 is high -- should trigger red (>500)
        assert status == SignalStatus.TRIGGERED, (
            f"Pay ratio 533 should trigger, got {status}"
        )
        assert level == "red", (
            f"Pay ratio 533 should be red (>500), got {level}"
        )

    def test_pay_ratio_150_is_clear(self) -> None:
        """CEO pay ratio 150:1 should be clear (below 200 threshold)."""
        check = _load_check("GOV.PAY.peer_comparison")
        threshold = check["threshold"]
        result = try_numeric_compare(150.0, threshold)
        assert result is not None, "Pay ratio 150 should produce a comparison result"
        status, _, _ = result
        assert status == SignalStatus.CLEAR, (
            f"Pay ratio 150 should be clear (below 200), got {status}"
        )

    def test_pay_ratio_300_triggers_yellow(self) -> None:
        """CEO pay ratio 300:1 should trigger yellow (between 200 and 500)."""
        check = _load_check("GOV.PAY.peer_comparison")
        threshold = check["threshold"]
        result = try_numeric_compare(300.0, threshold)
        assert result is not None, "Pay ratio 300 should produce a comparison result"
        status, level, _ = result
        assert status == SignalStatus.TRIGGERED, (
            f"Pay ratio 300 should trigger, got {status}"
        )
        assert level == "yellow", (
            f"Pay ratio 300 should be yellow (>200 but <500), got {level}"
        )
