"""Regression tests for wiring, routing, and calibration fixes.

Phase 33-05: Verifies that check field routing, threshold calibration,
SEC enforcement evaluation, and customer concentration logic are
all correctly wired.

Phase 33-07: Adds evaluator order regression tests (clear signal before
numeric comparison).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.stages.analyze.signal_evaluators import (
    _check_clear_signal,
    evaluate_numeric_threshold,
    evaluate_tiered,
)
from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK, narrow_result
from do_uw.stages.analyze.signal_helpers import try_numeric_compare
from do_uw.stages.analyze.signal_results import SignalStatus

_CHECKS_JSON = Path(__file__).parent.parent.parent.parent / "src" / "do_uw" / "brain" / "config" / "signals.json"


# ---------------------------------------------------------------------------
# Task 1: Field routing tests
# ---------------------------------------------------------------------------


class TestFieldRoutingFixes:
    """Verify FIELD_FOR_CHECK routes checks to correct fields."""

    def test_stock_trade_liquidity_routes_to_avg_daily_volume(self) -> None:
        """STOCK.TRADE.liquidity should route to avg_daily_volume, not current_price."""
        assert FIELD_FOR_CHECK["STOCK.TRADE.liquidity"] == "avg_daily_volume"

    def test_stock_analyst_coverage_routes_to_analyst_count(self) -> None:
        """STOCK.ANALYST.coverage should route to analyst_count, not beat_rate."""
        assert FIELD_FOR_CHECK["STOCK.ANALYST.coverage"] == "analyst_count"

    def test_stock_analyst_momentum_routes_to_recommendation_mean(self) -> None:
        """STOCK.ANALYST.momentum should route to recommendation_mean, not beat_rate."""
        assert FIELD_FOR_CHECK["STOCK.ANALYST.momentum"] == "recommendation_mean"

    def test_fin_guide_current_routes_to_guidance_provided(self) -> None:
        """FIN.GUIDE.current should route to guidance_provided, not financial_health_narrative."""
        assert FIELD_FOR_CHECK["FIN.GUIDE.current"] == "guidance_provided"

    def test_fin_guide_track_record_routes_to_beat_rate(self) -> None:
        """FIN.GUIDE.track_record should route to beat_rate."""
        assert FIELD_FOR_CHECK["FIN.GUIDE.track_record"] == "beat_rate"

    def test_fin_guide_philosophy_routes_to_guidance_philosophy(self) -> None:
        """FIN.GUIDE.philosophy should route to guidance_philosophy."""
        assert FIELD_FOR_CHECK["FIN.GUIDE.philosophy"] == "guidance_philosophy"

    def test_fin_guide_earnings_reaction_routes_to_post_earnings_drift(self) -> None:
        """FIN.GUIDE.earnings_reaction should route to post_earnings_drift."""
        assert FIELD_FOR_CHECK["FIN.GUIDE.earnings_reaction"] == "post_earnings_drift"

    def test_fin_guide_analyst_consensus_routes_to_consensus_divergence(self) -> None:
        """FIN.GUIDE.analyst_consensus should route to consensus_divergence."""
        assert FIELD_FOR_CHECK["FIN.GUIDE.analyst_consensus"] == "consensus_divergence"

    def test_stock_valuation_pe_ratio_routes_correctly(self) -> None:
        """STOCK.VALUATION.pe_ratio should route to pe_ratio."""
        assert FIELD_FOR_CHECK["STOCK.VALUATION.pe_ratio"] == "pe_ratio"

    def test_stock_valuation_ev_ebitda_routes_correctly(self) -> None:
        """STOCK.VALUATION.ev_ebitda should route to ev_ebitda."""
        assert FIELD_FOR_CHECK["STOCK.VALUATION.ev_ebitda"] == "ev_ebitda"

    def test_stock_valuation_peg_ratio_routes_correctly(self) -> None:
        """STOCK.VALUATION.peg_ratio should route to peg_ratio."""
        assert FIELD_FOR_CHECK["STOCK.VALUATION.peg_ratio"] == "peg_ratio"


class TestNarrowResultRouting:
    """Verify narrow_result() returns the correct single-field dict."""

    def _data(self) -> dict[str, Any]:
        """Sample data dict with multiple fields."""
        return {
            "current_price": 150.0,
            "avg_daily_volume": 5_000_000,
            "beat_rate": 75.0,
            "analyst_count": 42,
            "recommendation_mean": 2.1,
            "guidance_provided": "Yes",
            "guidance_philosophy": "CONSERVATIVE",
            "post_earnings_drift": -1.5,
            "consensus_divergence": 3.2,
            "pe_ratio": 28.5,
            "ev_ebitda": 18.3,
            "peg_ratio": 1.8,
            "financial_health_narrative": "Strong financial position",
        }

    def test_narrow_stock_trade_liquidity(self) -> None:
        """narrow_result for STOCK.TRADE.liquidity returns avg_daily_volume only."""
        result = narrow_result("STOCK.TRADE.liquidity", self._data())
        assert result == {"avg_daily_volume": 5_000_000}

    def test_narrow_stock_analyst_coverage(self) -> None:
        """narrow_result for STOCK.ANALYST.coverage returns analyst_count only."""
        result = narrow_result("STOCK.ANALYST.coverage", self._data())
        assert result == {"analyst_count": 42}

    def test_narrow_stock_analyst_momentum(self) -> None:
        """narrow_result for STOCK.ANALYST.momentum returns recommendation_mean only."""
        result = narrow_result("STOCK.ANALYST.momentum", self._data())
        assert result == {"recommendation_mean": 2.1}

    def test_narrow_fin_guide_current(self) -> None:
        """narrow_result for FIN.GUIDE.current returns guidance_provided only."""
        result = narrow_result("FIN.GUIDE.current", self._data())
        assert result == {"guidance_provided": "Yes"}

    def test_narrow_fin_guide_track_record(self) -> None:
        """narrow_result for FIN.GUIDE.track_record returns beat_rate only."""
        result = narrow_result("FIN.GUIDE.track_record", self._data())
        assert result == {"beat_rate": 75.0}

    def test_narrow_fin_guide_philosophy(self) -> None:
        """narrow_result for FIN.GUIDE.philosophy returns guidance_philosophy only."""
        result = narrow_result("FIN.GUIDE.philosophy", self._data())
        assert result == {"guidance_philosophy": "CONSERVATIVE"}

    def test_narrow_fin_guide_earnings_reaction(self) -> None:
        """narrow_result for FIN.GUIDE.earnings_reaction returns post_earnings_drift."""
        result = narrow_result("FIN.GUIDE.earnings_reaction", self._data())
        assert result == {"post_earnings_drift": -1.5}

    def test_narrow_fin_guide_analyst_consensus(self) -> None:
        """narrow_result for FIN.GUIDE.analyst_consensus returns consensus_divergence."""
        result = narrow_result("FIN.GUIDE.analyst_consensus", self._data())
        assert result == {"consensus_divergence": 3.2}

    def test_narrow_stock_valuation_pe_ratio(self) -> None:
        """narrow_result for STOCK.VALUATION.pe_ratio returns pe_ratio only."""
        result = narrow_result("STOCK.VALUATION.pe_ratio", self._data())
        assert result == {"pe_ratio": 28.5}

    def test_narrow_stock_valuation_ev_ebitda(self) -> None:
        """narrow_result for STOCK.VALUATION.ev_ebitda returns ev_ebitda only."""
        result = narrow_result("STOCK.VALUATION.ev_ebitda", self._data())
        assert result == {"ev_ebitda": 18.3}

    def test_data_strategy_overrides_field_for_check(self) -> None:
        """data_strategy.field_key takes priority over FIELD_FOR_CHECK."""
        data = {"wrong_field": "bad", "correct_field": "good"}
        signal_def: dict[str, Any] = {"data_strategy": {"field_key": "correct_field"}}
        result = narrow_result("ANY.CHECK", data, signal_def)
        assert result == {"correct_field": "good"}

    def test_missing_field_returns_empty(self) -> None:
        """When routed field is missing from data, return empty dict."""
        result = narrow_result("STOCK.TRADE.liquidity", {"current_price": 150.0})
        assert result == {}


# ---------------------------------------------------------------------------
# Task 2: Threshold calibration, SEC enforcement, customer concentration
# ---------------------------------------------------------------------------


class TestLiquidityThresholdCalibration:
    """Verify FIN.LIQ.position evaluates against <1.0 red / <1.5 yellow."""

    _THRESHOLD: dict[str, str] = {
        "type": "tiered",
        "red": "<1.0 current ratio (inadequate liquidity)",
        "yellow": "<1.5 current ratio (tight liquidity)",
        "clear": "Current ratio at or above 1.5",
    }

    def test_current_ratio_089_is_red(self) -> None:
        """current_ratio=0.89 should trigger RED (<1.0)."""
        result = try_numeric_compare(0.89, self._THRESHOLD)
        assert result is not None
        status, level, _evidence = result
        assert status == SignalStatus.TRIGGERED
        assert level == "red"

    def test_current_ratio_12_is_yellow(self) -> None:
        """current_ratio=1.2 should trigger YELLOW (<1.5)."""
        result = try_numeric_compare(1.2, self._THRESHOLD)
        assert result is not None
        status, level, _evidence = result
        assert status == SignalStatus.TRIGGERED
        assert level == "yellow"

    def test_current_ratio_18_is_clear(self) -> None:
        """current_ratio=1.8 should be CLEAR (>= 1.5)."""
        result = try_numeric_compare(1.8, self._THRESHOLD)
        assert result is not None
        status, level, _evidence = result
        assert status == SignalStatus.CLEAR
        assert level == "clear"

    def test_current_ratio_10_is_yellow(self) -> None:
        """current_ratio=1.0 is not <1.0 so should be YELLOW (<1.5)."""
        result = try_numeric_compare(1.0, self._THRESHOLD)
        assert result is not None
        status, level, _evidence = result
        assert status == SignalStatus.TRIGGERED
        assert level == "yellow"

    def test_current_ratio_15_is_clear(self) -> None:
        """current_ratio=1.5 is not <1.5 so should be CLEAR."""
        result = try_numeric_compare(1.5, self._THRESHOLD)
        assert result is not None
        status, _level, _evidence = result
        assert status == SignalStatus.CLEAR


class TestSECEnforcementEvaluation:
    """Verify SEC enforcement NONE evaluates to CLEAR, not INFO."""

    def _make_check(self, signal_id: str) -> dict[str, Any]:
        return {
            "id": signal_id,
            "name": "SEC Investigation Check",
            "section": 6,
            "threshold": {
                "type": "tiered",
                "red": "Formal SEC investigation or Wells Notice",
                "yellow": "Informal inquiry disclosed",
                "clear": "No SEC investigation",
            },
        }

    def test_sec_enforcement_none_is_clear(self) -> None:
        """sec_enforcement_stage='NONE' should evaluate to CLEAR."""
        check = self._make_check("LIT.REG.sec_investigation")
        data = {"sec_enforcement_stage": "NONE"}
        result = evaluate_tiered(check, data, check["threshold"])
        assert result.status == SignalStatus.CLEAR
        assert "No SEC enforcement" in result.evidence

    def test_sec_enforcement_empty_is_clear(self) -> None:
        """sec_enforcement_stage='' should evaluate to CLEAR."""
        check = self._make_check("LIT.REG.sec_investigation")
        data = {"sec_enforcement_stage": ""}
        result = evaluate_tiered(check, data, check["threshold"])
        assert result.status == SignalStatus.CLEAR

    def test_sec_enforcement_formal_is_info(self) -> None:
        """sec_enforcement_stage='FORMAL_INVESTIGATION' should NOT be CLEAR."""
        check = self._make_check("LIT.REG.sec_investigation")
        data = {"sec_enforcement_stage": "FORMAL_INVESTIGATION"}
        result = evaluate_tiered(check, data, check["threshold"])
        # Non-NONE values should be INFO (qualitative, no numeric threshold)
        assert result.status == SignalStatus.INFO

    def test_wells_notice_false_is_clear(self) -> None:
        """wells_notice=False should evaluate to CLEAR."""
        check = {
            "id": "LIT.REG.wells_notice",
            "name": "Wells Notice Check",
            "section": 6,
            "threshold": {
                "type": "tiered",
                "red": "Wells notice received",
                "yellow": "Prior Wells notice (resolved)",
                "clear": "No Wells notice history",
            },
        }
        data = {"wells_notice": False}
        result = evaluate_tiered(check, data, check["threshold"])
        assert result.status == SignalStatus.CLEAR
        assert "No Wells notice" in result.evidence

    def test_wells_notice_true_is_not_clear(self) -> None:
        """wells_notice=True should NOT be CLEAR."""
        check = {
            "id": "LIT.REG.wells_notice",
            "name": "Wells Notice Check",
            "section": 6,
            "threshold": {
                "type": "tiered",
                "red": "Wells notice received",
                "yellow": "Prior Wells notice (resolved)",
                "clear": "No Wells notice history",
            },
        }
        data = {"wells_notice": True}
        result = evaluate_tiered(check, data, check["threshold"])
        # True wells_notice should NOT be clear
        assert result.status != SignalStatus.CLEAR


class TestCustomerConcentrationAbsence:
    """Verify customer concentration 'Not mentioned' evaluates to CLEAR positive."""

    def _make_check(self) -> dict[str, Any]:
        return {
            "id": "BIZ.DEPEND.customer_conc",
            "name": "Customer Concentration Risk",
            "section": 1,
            "threshold": {
                "type": "percentage",
                "red": ">25% from top customer",
                "yellow": ">15% from top customer",
                "clear": "<15% from top customer",
            },
        }

    def test_not_mentioned_is_clear(self) -> None:
        """'Not mentioned in 10-K filing' -> CLEAR with positive note."""
        check = self._make_check()
        data = {"customer_concentration": "Not mentioned in 10-K filing"}
        result = evaluate_numeric_threshold(
            check, data, check["threshold"], "percentage"
        )
        assert result.status == SignalStatus.CLEAR
        assert "SEC requires disclosure" in result.evidence

    def test_not_mentioned_case_insensitive(self) -> None:
        """'not mentioned' (lowercase) -> CLEAR."""
        signal = _check_clear_signal(
            "not mentioned in 10-K filing",
            "customer_concentration",
            "BIZ.DEPEND.customer_conc",
        )
        assert signal is not None
        status, _level, _evidence = signal
        assert status == SignalStatus.CLEAR

    def test_high_concentration_not_clear(self) -> None:
        """Numeric concentration >25% should trigger, not be CLEAR."""
        check = self._make_check()
        data = {"customer_concentration": 30.0}
        result = evaluate_numeric_threshold(
            check, data, check["threshold"], "percentage"
        )
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"


class TestClearSignalHelper:
    """Direct tests for _check_clear_signal function."""

    def test_sec_enforcement_none(self) -> None:
        result = _check_clear_signal("NONE", "sec_enforcement_stage", "LIT.REG.sec_investigation")
        assert result is not None
        assert result[0] == SignalStatus.CLEAR

    def test_sec_enforcement_none_lowercase(self) -> None:
        result = _check_clear_signal("none", "sec_enforcement_stage", "LIT.REG.sec_investigation")
        assert result is not None
        assert result[0] == SignalStatus.CLEAR

    def test_sec_enforcement_formal_not_clear(self) -> None:
        result = _check_clear_signal(
            "FORMAL_INVESTIGATION", "sec_enforcement_stage", "LIT.REG.sec_investigation"
        )
        assert result is None

    def test_wells_notice_false(self) -> None:
        result = _check_clear_signal(False, "wells_notice", "LIT.REG.wells_notice")
        assert result is not None
        assert result[0] == SignalStatus.CLEAR

    def test_wells_notice_true(self) -> None:
        result = _check_clear_signal(True, "wells_notice", "LIT.REG.wells_notice")
        assert result is None

    def test_customer_conc_not_mentioned(self) -> None:
        result = _check_clear_signal(
            "Not mentioned in 10-K filing",
            "customer_concentration",
            "BIZ.DEPEND.customer_conc",
        )
        assert result is not None
        assert result[0] == SignalStatus.CLEAR
        assert "diversified" in result[2]

    def test_unrecognized_key_returns_none(self) -> None:
        """Non-matching data_key should return None (no clear signal)."""
        result = _check_clear_signal("NONE", "some_other_field", "SOME.CHECK")
        assert result is None


# ---------------------------------------------------------------------------
# Task 3: Clear signal evaluator order regression tests (Phase 33-07)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def checks_by_id() -> dict[str, dict[str, Any]]:
    """Load all signals from brain/signals.json indexed by ID."""
    with open(_CHECKS_JSON) as f:
        data = json.load(f)
    return {c["id"]: c for c in data["signals"]}


class TestClearSignalEvaluatorOrder:
    """Verify that full evaluator functions return CLEAR for known clear signals.

    These tests confirm that _check_clear_signal fires BEFORE
    try_numeric_compare in both evaluate_tiered and evaluate_numeric_threshold,
    using real check configs loaded from signals.json.
    """

    def test_tiered_sec_enforcement_none_returns_clear(
        self, checks_by_id: dict[str, dict[str, Any]]
    ) -> None:
        """evaluate_tiered with sec_enforcement_stage='NONE' returns CLEAR."""
        check = checks_by_id["LIT.REG.sec_investigation"]
        data: dict[str, Any] = {"sec_enforcement_stage": "NONE"}
        threshold = check["threshold"]
        result = evaluate_tiered(check, data, threshold)
        assert result.status == SignalStatus.CLEAR, (
            f"Expected CLEAR for SEC enforcement NONE, got {result.status}"
        )

    def test_tiered_wells_notice_false_returns_clear(
        self, checks_by_id: dict[str, dict[str, Any]]
    ) -> None:
        """evaluate_tiered with wells_notice=False returns CLEAR."""
        check = checks_by_id["LIT.REG.wells_notice"]
        data: dict[str, Any] = {"wells_notice": False}
        threshold = check["threshold"]
        result = evaluate_tiered(check, data, threshold)
        assert result.status == SignalStatus.CLEAR, (
            f"Expected CLEAR for Wells notice False, got {result.status}"
        )

    def test_numeric_customer_concentration_not_mentioned_returns_clear(
        self, checks_by_id: dict[str, dict[str, Any]]
    ) -> None:
        """evaluate_numeric_threshold with customer_concentration 'Not mentioned' returns CLEAR."""
        check = checks_by_id["BIZ.DEPEND.customer_conc"]
        data: dict[str, Any] = {"customer_concentration": "Not mentioned in 10-K filing"}
        threshold = check["threshold"]
        result = evaluate_numeric_threshold(check, data, threshold, "percentage")
        assert result.status == SignalStatus.CLEAR, (
            f"Expected CLEAR for customer concentration 'Not mentioned', got {result.status}"
        )
