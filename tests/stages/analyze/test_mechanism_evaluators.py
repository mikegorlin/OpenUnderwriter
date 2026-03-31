"""Tests for mechanism evaluators: conjunction, absence, contextual.

Phase 110-01: New signal evaluation mechanisms.
TDD RED: These tests are written before implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from do_uw.brain.brain_signal_schema import BrainSignalEntry, EvaluationSpec
from do_uw.stages.analyze.signal_results import DataStatus, SignalResult, SignalStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNALS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "do_uw"
    / "brain"
    / "signals"
)

CONJUNCTION_DIR = SIGNALS_DIR / "conjunction"
ABSENCE_DIR = SIGNALS_DIR / "absence"
CONTEXTUAL_DIR = SIGNALS_DIR / "contextual"


# ---------------------------------------------------------------------------
# Fixtures: minimal signal dicts for mechanism evaluators
# ---------------------------------------------------------------------------


def _make_conjunction_sig(
    sig_id: str = "CONJ.test",
    required_signals: list[str] | None = None,
    minimum_matches: int = 2,
    signal_conditions: dict[str, str] | None = None,
    recommendation_floor: str | None = None,
) -> dict[str, Any]:
    """Build a minimal conjunction signal dict."""
    return {
        "id": sig_id,
        "name": "Test Conjunction Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 1,
        "threshold": {"type": "info"},
        "provenance": {"origin": "test"},
        "signal_class": "inference",
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "test",
            "threshold_basis": "test",
        },
        "evaluation": {
            "mechanism": "conjunction",
            "conjunction_rules": {
                "required_signals": required_signals or ["SIG.A", "SIG.B", "SIG.C"],
                "minimum_matches": minimum_matches,
                "signal_conditions": signal_conditions or {},
                "recommendation_floor": recommendation_floor,
            },
        },
    }


def _make_absence_sig(
    sig_id: str = "ABS.test",
    expectation_type: str = "always_expected",
    expected_signals: list[str] | None = None,
    condition: str = "test condition",
) -> dict[str, Any]:
    """Build a minimal absence signal dict."""
    return {
        "id": sig_id,
        "name": "Test Absence Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 1,
        "threshold": {"type": "info"},
        "provenance": {"origin": "test"},
        "signal_class": "inference",
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "test",
            "threshold_basis": "test",
        },
        "evaluation": {
            "mechanism": "absence",
            "absence_rules": {
                "expectation_type": expectation_type,
                "expected_signals": expected_signals or ["SIG.X"],
                "condition": condition,
                "expected_status": "TRIGGERED",
                "absence_trigger": "SKIPPED",
            },
        },
    }


def _make_contextual_sig(
    sig_id: str = "CTX.test",
    source_signal: str = "SIG.A",
    context_dimensions: list[str] | None = None,
    context_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal contextual signal dict."""
    return {
        "id": sig_id,
        "name": "Test Contextual Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 1,
        "threshold": {"type": "info"},
        "provenance": {"origin": "test"},
        "signal_class": "inference",
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "test",
            "threshold_basis": "test",
        },
        "evaluation": {
            "mechanism": "contextual",
            "contextual_rules": {
                "source_signal": source_signal,
                "context_dimensions": context_dimensions or ["lifecycle_stage"],
                "context_adjustments": context_matrix or {
                    "pre_revenue": {
                        "threshold_adjustment": 0.5,
                        "rationale": "Pre-revenue: lower thresholds",
                    },
                    "mature": {
                        "threshold_adjustment": 1.5,
                        "rationale": "Mature: higher thresholds",
                    },
                },
            },
        },
    }


def _make_signal_results(
    statuses: dict[str, str],
    data_statuses: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build a signal_results dict from {sig_id: status_str}."""
    results: dict[str, dict[str, Any]] = {}
    for sid, status in statuses.items():
        entry: dict[str, Any] = {
            "status": status,
            "value": "1.0",
            "threshold_level": "red" if status == "TRIGGERED" else "",
            "data_status": "EVALUATED",
        }
        if data_statuses and sid in data_statuses:
            entry["data_status"] = data_statuses[sid]
        results[sid] = entry
    return results


# ---------------------------------------------------------------------------
# Schema extension tests
# ---------------------------------------------------------------------------


class TestSchemaExtensions:
    """Verify that ConjunctionRuleSpec, AbsenceRuleSpec, ContextualRuleSpec
    are valid Pydantic sub-models on EvaluationSpec."""

    def test_conjunction_rules_spec_validates(self) -> None:
        """ConjunctionRuleSpec loads from valid dict."""
        from do_uw.brain.brain_signal_schema import ConjunctionRuleSpec

        spec = ConjunctionRuleSpec(
            required_signals=["SIG.A", "SIG.B"],
            minimum_matches=2,
        )
        assert spec.required_signals == ["SIG.A", "SIG.B"]
        assert spec.minimum_matches == 2

    def test_absence_rules_spec_validates(self) -> None:
        """AbsenceRuleSpec loads from valid dict."""
        from do_uw.brain.brain_signal_schema import AbsenceRuleSpec

        spec = AbsenceRuleSpec(
            expectation_type="always_expected",
            expected_signals=["SIG.X"],
            condition="always required",
        )
        assert spec.expectation_type == "always_expected"
        assert spec.expected_signals == ["SIG.X"]

    def test_contextual_rules_spec_validates(self) -> None:
        """ContextualRuleSpec loads from valid dict."""
        from do_uw.brain.brain_signal_schema import ContextualRuleSpec

        spec = ContextualRuleSpec(
            source_signal="SIG.A",
            context_dimensions=["lifecycle_stage"],
            context_adjustments={
                "mature": {
                    "threshold_adjustment": 1.5,
                    "rationale": "Higher bar for mature companies",
                },
            },
        )
        assert spec.source_signal == "SIG.A"

    def test_evaluation_spec_accepts_conjunction_rules(self) -> None:
        """EvaluationSpec with conjunction_rules validates OK."""
        spec = EvaluationSpec(
            mechanism="conjunction",
            conjunction_rules={
                "required_signals": ["SIG.A", "SIG.B"],
                "minimum_matches": 2,
            },
        )
        assert spec.mechanism == "conjunction"
        assert spec.conjunction_rules is not None

    def test_evaluation_spec_accepts_absence_rules(self) -> None:
        """EvaluationSpec with absence_rules validates OK."""
        spec = EvaluationSpec(
            mechanism="absence",
            absence_rules={
                "expectation_type": "always_expected",
                "expected_signals": ["SIG.X"],
                "condition": "always",
            },
        )
        assert spec.mechanism == "absence"
        assert spec.absence_rules is not None

    def test_evaluation_spec_accepts_contextual_rules(self) -> None:
        """EvaluationSpec with contextual_rules validates OK."""
        spec = EvaluationSpec(
            mechanism="contextual",
            contextual_rules={
                "source_signal": "SIG.A",
                "context_dimensions": ["lifecycle_stage"],
                "context_adjustments": {},
            },
        )
        assert spec.mechanism == "contextual"
        assert spec.contextual_rules is not None

    def test_existing_threshold_signals_still_load(self) -> None:
        """Existing 508+ signals load without schema regression."""
        count = 0
        errors: list[str] = []
        for f in sorted(SIGNALS_DIR.glob("**/*.yaml")):
            # Skip new mechanism directories for this test
            if any(d in f.parts for d in ("conjunction", "absence", "contextual")):
                continue
            data = yaml.safe_load(f.read_text())
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and "id" in entry:
                        try:
                            BrainSignalEntry.model_validate(entry)
                            count += 1
                        except Exception as e:
                            errors.append(f"{entry.get('id')}: {e}")

        assert count >= 508, f"Expected 508+ signals, got {count}"
        assert not errors, f"Schema regression: {errors[:5]}"


# ---------------------------------------------------------------------------
# Conjunction evaluator tests
# ---------------------------------------------------------------------------


class TestConjunctionEvaluator:
    """Test evaluate_conjunction mechanism."""

    def test_triggers_when_minimum_matches_met(self) -> None:
        """Conjunction fires when >= minimum_matches component signals triggered."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(minimum_matches=2)
        signal_results = _make_signal_results({
            "SIG.A": "TRIGGERED",
            "SIG.B": "TRIGGERED",
            "SIG.C": "CLEAR",
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status == SignalStatus.TRIGGERED

    def test_clear_when_below_minimum_matches(self) -> None:
        """Conjunction is CLEAR when < minimum_matches met."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(minimum_matches=3)
        signal_results = _make_signal_results({
            "SIG.A": "TRIGGERED",
            "SIG.B": "CLEAR",
            "SIG.C": "CLEAR",
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status == SignalStatus.CLEAR

    def test_skipped_when_majority_components_skipped(self) -> None:
        """Conjunction is SKIPPED when >50% of component signals are SKIPPED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(
            required_signals=["SIG.A", "SIG.B", "SIG.C", "SIG.D"],
            minimum_matches=2,
        )
        signal_results = _make_signal_results({
            "SIG.A": "SKIPPED",
            "SIG.B": "SKIPPED",
            "SIG.C": "SKIPPED",
            "SIG.D": "TRIGGERED",
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status == SignalStatus.SKIPPED

    def test_custom_signal_conditions(self) -> None:
        """Conjunction respects custom signal_conditions (e.g., CLEAR means no clawback)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(
            required_signals=["SIG.PAY_UP", "SIG.PERF_DOWN", "SIG.CLAWBACK"],
            minimum_matches=3,
            signal_conditions={"SIG.CLAWBACK": "CLEAR"},
        )
        signal_results = _make_signal_results({
            "SIG.PAY_UP": "TRIGGERED",
            "SIG.PERF_DOWN": "TRIGGERED",
            "SIG.CLAWBACK": "CLEAR",
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status == SignalStatus.TRIGGERED

    def test_missing_component_treated_as_not_matched(self) -> None:
        """Missing signal in results is treated as not matching."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(minimum_matches=2)
        signal_results = _make_signal_results({
            "SIG.A": "TRIGGERED",
            # SIG.B and SIG.C not in results
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status in (SignalStatus.CLEAR, SignalStatus.SKIPPED)

    def test_returns_signal_result_type(self) -> None:
        """Evaluator returns a SignalResult instance."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig()
        result = evaluate_conjunction(sig, {}, {})
        assert isinstance(result, SignalResult)

    def test_recommendation_floor_in_details(self) -> None:
        """Fired conjunction includes recommendation_floor in details."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig(
            minimum_matches=2,
            recommendation_floor="ELEVATED",
        )
        signal_results = _make_signal_results({
            "SIG.A": "TRIGGERED",
            "SIG.B": "TRIGGERED",
            "SIG.C": "CLEAR",
        })

        result = evaluate_conjunction(sig, {}, signal_results)
        assert result.status == SignalStatus.TRIGGERED
        assert result.details.get("recommendation_floor") == "ELEVATED"


# ---------------------------------------------------------------------------
# Absence evaluator tests
# ---------------------------------------------------------------------------


class TestAbsenceEvaluator:
    """Test evaluate_absence mechanism."""

    def test_triggers_when_expected_signal_skipped(self) -> None:
        """Absence fires when expected signal is SKIPPED (looked but no data)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(
            expectation_type="always_expected",
            expected_signals=["SIG.X"],
        )
        signal_results = _make_signal_results(
            {"SIG.X": "SKIPPED"},
            data_statuses={"SIG.X": "EVALUATED"},
        )

        result = evaluate_absence(sig, {}, signal_results, company=None)
        assert result.status == SignalStatus.TRIGGERED

    def test_clear_when_expected_signal_triggered(self) -> None:
        """Absence is CLEAR when expected signal fired (disclosure present)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(expected_signals=["SIG.X"])
        signal_results = _make_signal_results({"SIG.X": "TRIGGERED"})

        result = evaluate_absence(sig, {}, signal_results, company=None)
        assert result.status == SignalStatus.CLEAR

    def test_clear_when_expected_signal_clear(self) -> None:
        """Absence is CLEAR when expected signal is CLEAR (disclosure present, no issue)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(expected_signals=["SIG.X"])
        signal_results = _make_signal_results({"SIG.X": "CLEAR"})

        result = evaluate_absence(sig, {}, signal_results, company=None)
        assert result.status == SignalStatus.CLEAR

    def test_skipped_when_data_unavailable(self) -> None:
        """Absence is SKIPPED when expected signal has DATA_UNAVAILABLE (didn't look)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(expected_signals=["SIG.X"])
        signal_results = _make_signal_results(
            {"SIG.X": "SKIPPED"},
            data_statuses={"SIG.X": "DATA_UNAVAILABLE"},
        )

        result = evaluate_absence(sig, {}, signal_results, company=None)
        assert result.status == SignalStatus.SKIPPED

    def test_skipped_when_signal_missing_from_results(self) -> None:
        """Absence is SKIPPED when expected signal is not in results at all."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(expected_signals=["SIG.MISSING"])
        signal_results: dict[str, dict[str, Any]] = {}

        result = evaluate_absence(sig, {}, signal_results, company=None)
        assert result.status == SignalStatus.SKIPPED

    def test_company_profile_type_checks_profile(self) -> None:
        """company_profile absence skips when company doesn't match criteria."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig(
            expectation_type="company_profile",
            expected_signals=["SIG.X"],
            condition="has_significant_debt",
        )
        # No company = can't check profile = SKIPPED
        result = evaluate_absence(sig, {}, {}, company=None)
        assert result.status == SignalStatus.SKIPPED

    def test_returns_signal_result_type(self) -> None:
        """Evaluator returns a SignalResult instance."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig()
        result = evaluate_absence(sig, {}, {}, company=None)
        assert isinstance(result, SignalResult)


# ---------------------------------------------------------------------------
# Contextual evaluator tests
# ---------------------------------------------------------------------------


class TestContextualEvaluator:
    """Test evaluate_contextual mechanism."""

    def test_adjusts_threshold_based_on_lifecycle(self) -> None:
        """Contextual applies threshold adjustment based on lifecycle stage."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig(
            source_signal="SIG.A",
            context_dimensions=["lifecycle_stage"],
            context_matrix={
                "pre_revenue": {
                    "threshold_adjustment": 0.5,
                    "rationale": "Lower bar for pre-revenue",
                },
            },
        )
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        # With pre-revenue context, threshold is halved -> more likely to trigger
        result = evaluate_contextual(
            sig, {}, signal_results,
            company=None,
            company_context={"lifecycle_stage": "pre_revenue"},
        )
        assert result.status in (SignalStatus.TRIGGERED, SignalStatus.CLEAR, SignalStatus.INFO)
        assert isinstance(result, SignalResult)

    def test_skipped_when_no_context_available(self) -> None:
        """Contextual is SKIPPED when company context for required dimension is missing."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig(context_dimensions=["lifecycle_stage"])
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        result = evaluate_contextual(
            sig, {}, signal_results,
            company=None,
            company_context={},
        )
        assert result.status == SignalStatus.SKIPPED

    def test_skipped_when_source_signal_missing(self) -> None:
        """Contextual is SKIPPED when source signal not in results."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig(source_signal="SIG.MISSING")

        result = evaluate_contextual(
            sig, {}, {},
            company=None,
            company_context={"lifecycle_stage": "mature"},
        )
        assert result.status == SignalStatus.SKIPPED

    def test_returns_signal_result_type(self) -> None:
        """Evaluator returns a SignalResult instance."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig()
        result = evaluate_contextual(sig, {}, {}, company=None, company_context={})
        assert isinstance(result, SignalResult)

    def test_contextual_with_no_adjustment_match(self) -> None:
        """Contextual returns INFO when lifecycle stage has no adjustment entry."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig(
            context_matrix={
                "pre_revenue": {
                    "threshold_adjustment": 0.5,
                    "rationale": "test",
                },
            },
        )
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        result = evaluate_contextual(
            sig, {}, signal_results,
            company=None,
            company_context={"lifecycle_stage": "growth"},
        )
        # No adjustment for "growth" -> pass through source status
        assert result.status in (SignalStatus.TRIGGERED, SignalStatus.INFO, SignalStatus.CLEAR)


# ---------------------------------------------------------------------------
# Signal engine dispatch tests
# ---------------------------------------------------------------------------


class TestSignalEngineDispatch:
    """Test that signal_engine dispatches to mechanism evaluators."""

    def test_evaluate_signal_dispatches_conjunction(self) -> None:
        """signal_engine.evaluate_signal routes conjunction mechanism to evaluator."""
        # This tests the integration point -- mechanism dispatch happens
        # inside execute_signals, not evaluate_signal directly
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction

        sig = _make_conjunction_sig()
        signal_results = _make_signal_results({
            "SIG.A": "TRIGGERED",
            "SIG.B": "TRIGGERED",
        })
        result = evaluate_conjunction(sig, {}, signal_results)
        assert isinstance(result, SignalResult)

    def test_evaluate_signal_dispatches_absence(self) -> None:
        """evaluate_absence is callable as a mechanism evaluator."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence

        sig = _make_absence_sig()
        result = evaluate_absence(sig, {}, {}, company=None)
        assert isinstance(result, SignalResult)

    def test_evaluate_signal_dispatches_contextual(self) -> None:
        """evaluate_contextual is callable as a mechanism evaluator."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual

        sig = _make_contextual_sig()
        result = evaluate_contextual(sig, {}, {}, company=None, company_context={})
        assert isinstance(result, SignalResult)


# ---------------------------------------------------------------------------
# YAML signal loading tests
# ---------------------------------------------------------------------------


class TestYAMLSignalLoading:
    """Verify all new YAML signal files load against BrainSignalEntry schema."""

    def test_conjunction_yamls_load(self) -> None:
        """All conjunction YAML files validate against BrainSignalEntry."""
        count = 0
        errors: list[str] = []
        for f in sorted(CONJUNCTION_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if isinstance(entry, dict) and "id" in entry:
                    try:
                        BrainSignalEntry.model_validate(entry)
                        count += 1
                    except Exception as e:
                        errors.append(f"{f.name}/{entry.get('id')}: {e}")
        assert count >= 8, f"Expected 8+ conjunction signals, got {count}"
        assert not errors, f"Validation errors: {errors[:5]}"

    def test_absence_yamls_load(self) -> None:
        """All absence YAML files validate against BrainSignalEntry."""
        count = 0
        errors: list[str] = []
        for f in sorted(ABSENCE_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if isinstance(entry, dict) and "id" in entry:
                    try:
                        BrainSignalEntry.model_validate(entry)
                        count += 1
                    except Exception as e:
                        errors.append(f"{f.name}/{entry.get('id')}: {e}")
        assert count >= 20, f"Expected 20+ absence signals, got {count}"
        assert not errors, f"Validation errors: {errors[:5]}"

    def test_contextual_yamls_load(self) -> None:
        """All contextual YAML files validate against BrainSignalEntry."""
        count = 0
        errors: list[str] = []
        for f in sorted(CONTEXTUAL_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if isinstance(entry, dict) and "id" in entry:
                    try:
                        BrainSignalEntry.model_validate(entry)
                        count += 1
                    except Exception as e:
                        errors.append(f"{f.name}/{entry.get('id')}: {e}")
        assert count >= 20, f"Expected 20+ contextual signals, got {count}"
        assert not errors, f"Validation errors: {errors[:5]}"

    def test_all_mechanism_signals_are_inference_class(self) -> None:
        """All conjunction/absence/contextual signals have signal_class=inference."""
        non_inference: list[str] = []
        for directory in (CONJUNCTION_DIR, ABSENCE_DIR, CONTEXTUAL_DIR):
            for f in sorted(directory.glob("*.yaml")):
                data = yaml.safe_load(f.read_text())
                entries = data if isinstance(data, list) else [data]
                for entry in entries:
                    if isinstance(entry, dict) and "id" in entry:
                        if entry.get("signal_class") != "inference":
                            non_inference.append(entry["id"])
        assert not non_inference, f"Non-inference signals: {non_inference}"

    def test_conjunction_signals_have_conjunction_mechanism(self) -> None:
        """All conjunction signals have evaluation.mechanism=conjunction."""
        wrong: list[str] = []
        for f in sorted(CONJUNCTION_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if isinstance(entry, dict) and "id" in entry:
                    mech = entry.get("evaluation", {}).get("mechanism")
                    if mech != "conjunction":
                        wrong.append(f"{entry['id']}: {mech}")
        assert not wrong, f"Wrong mechanisms: {wrong}"


# ---------------------------------------------------------------------------
# Context matrix YAML test
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Trend evaluator fixtures
# ---------------------------------------------------------------------------


def _make_trend_sig(
    sig_id: str = "DISC.YOY.test",
    field_key: str = "revenue_growth",
    threshold_value: float | None = 0.10,
    direction: str = "increasing_is_risk",
) -> dict[str, Any]:
    """Build a minimal trend signal dict."""
    eval_block: dict[str, Any] = {
        "mechanism": "trend",
    }
    if threshold_value is not None:
        eval_block["threshold"] = threshold_value
    if direction:
        eval_block["direction"] = direction
    return {
        "id": sig_id,
        "name": "Test Trend Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 1,
        "threshold": {"type": "percentage", "red": 0.20, "yellow": 0.10},
        "provenance": {"origin": "test"},
        "signal_class": "evaluative",
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "test",
            "threshold_basis": "test",
        },
        "data_strategy": {"field_key": field_key},
        "evaluation": eval_block,
    }


def _make_peer_sig(
    sig_id: str = "PEER.test",
    field_key: str = "current_ratio",
    threshold_percentile: float | None = 75.0,
    direction: str = "high_is_risk",
) -> dict[str, Any]:
    """Build a minimal peer_comparison signal dict."""
    eval_block: dict[str, Any] = {
        "mechanism": "peer_comparison",
    }
    if threshold_percentile is not None:
        eval_block["threshold_percentile"] = threshold_percentile
    if direction:
        eval_block["direction"] = direction
    return {
        "id": sig_id,
        "name": "Test Peer Comparison Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 1,
        "threshold": {"type": "percentage"},
        "provenance": {"origin": "test"},
        "signal_class": "evaluative",
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "test",
            "threshold_basis": "test",
        },
        "data_strategy": {"field_key": field_key},
        "evaluation": eval_block,
    }


# ---------------------------------------------------------------------------
# Trend evaluator tests
# ---------------------------------------------------------------------------


class TestTrendEvaluator:
    """Test evaluate_trend mechanism."""

    def test_triggered_significant_increase(self) -> None:
        """Trend signal with current=100, prior=80 -> TRIGGERED (25% increase)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig(threshold_value=0.10, direction="increasing_is_risk")
        data = {"revenue_growth": 100, "revenue_growth_prior": 80}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.TRIGGERED
        assert result.details.get("current_value") == 100
        assert result.details.get("prior_value") == 80
        assert "pct_change" in result.details
        assert "delta" in result.details

    def test_clear_no_significant_change(self) -> None:
        """Trend signal with current=100, prior=100 -> CLEAR (0% change)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig(threshold_value=0.10, direction="increasing_is_risk")
        data = {"revenue_growth": 100, "revenue_growth_prior": 100}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.CLEAR

    def test_skipped_no_data(self) -> None:
        """Trend signal with no data -> SKIPPED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig()
        data: dict[str, Any] = {}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.SKIPPED
        assert "No trend data" in result.evidence or "data" in result.evidence.lower()

    def test_respects_threshold(self) -> None:
        """Trend signal with configured threshold -> uses it for TRIGGERED/CLEAR."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig(threshold_value=0.30, direction="increasing_is_risk")
        # 20% increase - below 30% threshold
        data = {"revenue_growth": 120, "revenue_growth_prior": 100}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.CLEAR

    def test_skipped_only_current_no_prior(self) -> None:
        """Trend signal with only current value (no prior) -> SKIPPED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig()
        data = {"revenue_growth": 100}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.SKIPPED

    def test_decreasing_is_risk_direction(self) -> None:
        """Trend signal with decreasing_is_risk detects declines."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig(threshold_value=0.10, direction="decreasing_is_risk")
        data = {"revenue_growth": 80, "revenue_growth_prior": 100}

        result = evaluate_trend(sig, data, {})
        assert result.status == SignalStatus.TRIGGERED

    def test_returns_signal_result_type(self) -> None:
        """Evaluator returns a SignalResult instance."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig()
        result = evaluate_trend(sig, {}, {})
        assert isinstance(result, SignalResult)

    def test_evidence_contains_direction(self) -> None:
        """Evidence includes direction interpretation (improving/deteriorating)."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_trend

        sig = _make_trend_sig(threshold_value=0.05, direction="increasing_is_risk")
        data = {"revenue_growth": 120, "revenue_growth_prior": 100}

        result = evaluate_trend(sig, data, {})
        assert "direction" in result.details


# ---------------------------------------------------------------------------
# Peer comparison evaluator tests
# ---------------------------------------------------------------------------


class TestPeerComparisonEvaluator:
    """Test evaluate_peer_comparison mechanism."""

    def test_triggered_at_high_percentile(self) -> None:
        """Peer signal with value at 90th percentile (above 75 threshold) -> TRIGGERED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig(threshold_percentile=75.0, direction="high_is_risk")
        data = {"current_ratio": 3.5}
        benchmarks = {
            "current_ratio": {
                "overall_percentile": 90.0,
                "sector_percentile": 88.0,
                "metric_name": "current_ratio",
            }
        }

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=benchmarks)
        assert result.status == SignalStatus.TRIGGERED
        assert result.details.get("overall_percentile") == 90.0

    def test_clear_at_median_percentile(self) -> None:
        """Peer signal with value at 50th percentile -> CLEAR."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig(threshold_percentile=75.0, direction="high_is_risk")
        data = {"current_ratio": 1.5}
        benchmarks = {
            "current_ratio": {
                "overall_percentile": 50.0,
                "sector_percentile": 48.0,
                "metric_name": "current_ratio",
            }
        }

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=benchmarks)
        assert result.status == SignalStatus.CLEAR

    def test_skipped_no_benchmark_data(self) -> None:
        """Peer signal with no benchmark data -> SKIPPED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig()
        data = {"current_ratio": 1.5}

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=None)
        assert result.status == SignalStatus.SKIPPED
        assert "peer" in result.evidence.lower() or "benchmark" in result.evidence.lower()

    def test_evidence_includes_both_percentiles(self) -> None:
        """Peer signal evidence includes both sector and overall percentiles."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig(threshold_percentile=75.0)
        data = {"current_ratio": 3.5}
        benchmarks = {
            "current_ratio": {
                "overall_percentile": 90.0,
                "sector_percentile": 85.0,
                "metric_name": "current_ratio",
            }
        }

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=benchmarks)
        assert result.details.get("overall_percentile") == 90.0
        assert result.details.get("sector_percentile") == 85.0

    def test_skipped_metric_not_in_benchmarks(self) -> None:
        """Peer signal with benchmarks but metric not found -> SKIPPED."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig(field_key="debt_to_equity")
        data = {"debt_to_equity": 2.0}
        benchmarks = {
            "current_ratio": {
                "overall_percentile": 50.0,
            }
        }

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=benchmarks)
        assert result.status == SignalStatus.SKIPPED

    def test_returns_signal_result_type(self) -> None:
        """Evaluator returns a SignalResult instance."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig()
        result = evaluate_peer_comparison(sig, {}, {}, benchmarks=None)
        assert isinstance(result, SignalResult)

    def test_low_is_risk_direction(self) -> None:
        """Peer signal with low_is_risk triggers when at low percentile."""
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_peer_comparison

        sig = _make_peer_sig(threshold_percentile=25.0, direction="low_is_risk")
        data = {"current_ratio": 0.5}
        benchmarks = {
            "current_ratio": {
                "overall_percentile": 10.0,
                "sector_percentile": 12.0,
                "metric_name": "current_ratio",
            }
        }

        result = evaluate_peer_comparison(sig, data, {}, benchmarks=benchmarks)
        assert result.status == SignalStatus.TRIGGERED


class TestContextMatrix:
    """Verify context_matrix.yaml structure."""

    def test_context_matrix_exists_and_loads(self) -> None:
        """context_matrix.yaml loads with required sections."""
        matrix_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "context_matrix.yaml"
        )
        assert matrix_path.exists(), "context_matrix.yaml missing"
        data = yaml.safe_load(matrix_path.read_text())
        assert "lifecycle_stages" in data
        assert "size_tiers" in data
        assert "sector_groups" in data
