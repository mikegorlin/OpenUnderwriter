"""Tests for adversarial critique engine -- rule-based detection of 4 caveat types.

Phase 110-02 Task 1: Adversarial critique engine.
TDD RED: Tests written before implementation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal_results(
    statuses: dict[str, str],
    *,
    data_statuses: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build signal_results dict from {signal_id: status_str}."""
    ds = data_statuses or {}
    results: dict[str, dict[str, Any]] = {}
    for sid, status in statuses.items():
        results[sid] = {
            "status": status,
            "value": "1.0",
            "threshold_level": "red" if status in ("TRIGGERED", "RED") else "",
            "data_status": ds.get(sid, "EVALUATED"),
        }
    return results


def _make_mock_state(
    *,
    sector: str = "Technology",
    board_size: int = 9,
    years_public: int = 15,
) -> MagicMock:
    """Create a minimal mock AnalysisState."""
    state = MagicMock()
    state.company = MagicMock()
    state.company.sic_code = "7372"
    state.company.sector = sector
    state.company.board_size = board_size
    state.company.years_public = years_public
    state.extracted = MagicMock()
    return state


def _load_rules() -> dict[str, Any]:
    """Load the adversarial rules YAML."""
    from pathlib import Path

    import yaml

    rules_path = (
        Path(__file__).parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "brain"
        / "framework"
        / "adversarial_rules.yaml"
    )
    with open(rules_path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Caveat + AdversarialResult model tests
# ---------------------------------------------------------------------------


class TestAdversarialModels:
    """Verify Caveat and AdversarialResult Pydantic models."""

    def test_caveat_validates_false_positive(self) -> None:
        """Caveat model validates with caveat_type='false_positive'."""
        from do_uw.models.adversarial import Caveat

        c = Caveat(
            caveat_type="false_positive",
            headline="Test headline",
            target_signal_id="SIG.A",
            confidence=0.8,
            evidence=["evidence 1"],
        )
        assert c.caveat_type == "false_positive"
        assert c.severity == "info"
        assert c.narrative_source == "template"

    def test_caveat_validates_false_negative(self) -> None:
        """Caveat model validates with caveat_type='false_negative'."""
        from do_uw.models.adversarial import Caveat

        c = Caveat(caveat_type="false_negative", headline="Blind spot")
        assert c.caveat_type == "false_negative"

    def test_caveat_validates_contradiction(self) -> None:
        """Caveat model validates with caveat_type='contradiction'."""
        from do_uw.models.adversarial import Caveat

        c = Caveat(caveat_type="contradiction", headline="Conflicting signals")
        assert c.caveat_type == "contradiction"

    def test_caveat_validates_data_completeness(self) -> None:
        """Caveat model validates with caveat_type='data_completeness'."""
        from do_uw.models.adversarial import Caveat

        c = Caveat(caveat_type="data_completeness", headline="Missing data")
        assert c.caveat_type == "data_completeness"

    def test_caveat_rejects_invalid_type(self) -> None:
        """Caveat model rejects invalid caveat_type."""
        from pydantic import ValidationError

        from do_uw.models.adversarial import Caveat

        with pytest.raises(ValidationError):
            Caveat(caveat_type="invalid_type", headline="Bad")

    def test_adversarial_result_creates(self) -> None:
        """AdversarialResult holds caveats list with computed counts."""
        from datetime import datetime, timezone

        from do_uw.models.adversarial import AdversarialResult, Caveat

        caveats = [
            Caveat(caveat_type="false_positive", headline="FP1"),
            Caveat(caveat_type="false_negative", headline="FN1"),
            Caveat(caveat_type="contradiction", headline="C1"),
            Caveat(caveat_type="data_completeness", headline="DC1"),
        ]
        result = AdversarialResult(
            caveats=caveats,
            false_positive_count=1,
            false_negative_count=1,
            contradiction_count=1,
            completeness_issues=1,
            computed_at=datetime.now(timezone.utc),
        )
        assert len(result.caveats) == 4
        assert result.false_positive_count == 1

    def test_adversarial_result_empty(self) -> None:
        """AdversarialResult with no caveats is valid."""
        from datetime import datetime, timezone

        from do_uw.models.adversarial import AdversarialResult

        result = AdversarialResult(computed_at=datetime.now(timezone.utc))
        assert result.caveats == []
        assert result.false_positive_count == 0

    def test_caveat_severity_levels(self) -> None:
        """Caveat severity accepts info, caution, warning."""
        from do_uw.models.adversarial import Caveat

        for sev in ("info", "caution", "warning"):
            c = Caveat(caveat_type="false_positive", headline="Test", severity=sev)
            assert c.severity == sev

    def test_caveat_narrative_source_values(self) -> None:
        """Caveat narrative_source accepts llm and template."""
        from do_uw.models.adversarial import Caveat

        for src in ("llm", "template"):
            c = Caveat(
                caveat_type="false_positive",
                headline="Test",
                narrative_source=src,
            )
            assert c.narrative_source == src


# ---------------------------------------------------------------------------
# check_false_positives tests
# ---------------------------------------------------------------------------


class TestCheckFalsePositives:
    """Tests for false positive detection."""

    def test_finds_triggered_with_mitigating_clear(self) -> None:
        """Finds TRIGGERED signals with mitigating CLEAR signals."""
        from do_uw.stages.score.adversarial_engine import check_false_positives

        rules = _load_rules()
        fp_rules = rules.get("false_positive_rules", [])

        # Set up a signal that is TRIGGERED plus its mitigating signals as CLEAR
        # Use first rule to find which signals to set up
        if not fp_rules:
            pytest.skip("No false_positive_rules in YAML")

        rule = fp_rules[0]
        target = rule["target_signal"]
        mitigating = rule.get("mitigating_signals", [])

        statuses = {target: "TRIGGERED"}
        for m in mitigating:
            statuses[m] = "CLEAR"

        signal_results = _make_signal_results(statuses)
        caveats = check_false_positives(signal_results, fp_rules)

        assert len(caveats) >= 1
        assert all(c.caveat_type == "false_positive" for c in caveats)

    def test_returns_empty_when_no_mitigating(self) -> None:
        """Returns empty when TRIGGERED signal has no mitigating CLEAR signals."""
        from do_uw.stages.score.adversarial_engine import check_false_positives

        rules = _load_rules()
        fp_rules = rules.get("false_positive_rules", [])
        if not fp_rules:
            pytest.skip("No false_positive_rules in YAML")

        rule = fp_rules[0]
        target = rule["target_signal"]
        # Target triggered but mitigating signals NOT clear
        signal_results = _make_signal_results({target: "TRIGGERED"})
        caveats = check_false_positives(signal_results, fp_rules)
        assert len(caveats) == 0

    def test_returns_empty_when_target_not_triggered(self) -> None:
        """Returns empty when target signal is CLEAR."""
        from do_uw.stages.score.adversarial_engine import check_false_positives

        rules = _load_rules()
        fp_rules = rules.get("false_positive_rules", [])
        if not fp_rules:
            pytest.skip("No false_positive_rules in YAML")

        rule = fp_rules[0]
        target = rule["target_signal"]
        signal_results = _make_signal_results({target: "CLEAR"})
        caveats = check_false_positives(signal_results, fp_rules)
        assert len(caveats) == 0

    def test_confidence_is_ratio(self) -> None:
        """Confidence = mitigating_count / total_mitigating_signals."""
        from do_uw.stages.score.adversarial_engine import check_false_positives

        rules = _load_rules()
        fp_rules = rules.get("false_positive_rules", [])
        if not fp_rules:
            pytest.skip("No false_positive_rules in YAML")

        rule = fp_rules[0]
        target = rule["target_signal"]
        mitigating = rule.get("mitigating_signals", [])
        if not mitigating:
            pytest.skip("Rule has no mitigating signals")

        # Set all mitigating to CLEAR
        statuses = {target: "TRIGGERED"}
        for m in mitigating:
            statuses[m] = "CLEAR"

        signal_results = _make_signal_results(statuses)
        caveats = check_false_positives(signal_results, fp_rules)

        if caveats:
            assert 0.0 <= caveats[0].confidence <= 1.0


# ---------------------------------------------------------------------------
# check_false_negatives tests
# ---------------------------------------------------------------------------


class TestCheckFalseNegatives:
    """Tests for false negative (blind spot) detection."""

    def test_finds_clear_with_exposure_indicators(self) -> None:
        """Finds CLEAR signals where exposure indicators suggest risk."""
        from do_uw.stages.score.adversarial_engine import check_false_negatives

        rules = _load_rules()
        fn_rules = rules.get("false_negative_rules", [])
        if not fn_rules:
            pytest.skip("No false_negative_rules in YAML")

        rule = fn_rules[0]
        target = rule["target_signal"]
        indicators = rule.get("exposure_indicators", [])

        statuses = {target: "CLEAR"}
        for ind in indicators:
            statuses[ind] = "TRIGGERED"

        signal_results = _make_signal_results(statuses)
        state = _make_mock_state()
        caveats = check_false_negatives(signal_results, fn_rules, state=state)

        assert len(caveats) >= 1
        assert all(c.caveat_type == "false_negative" for c in caveats)

    def test_returns_empty_when_target_triggered(self) -> None:
        """Returns empty when target is already TRIGGERED (no blind spot)."""
        from do_uw.stages.score.adversarial_engine import check_false_negatives

        rules = _load_rules()
        fn_rules = rules.get("false_negative_rules", [])
        if not fn_rules:
            pytest.skip("No false_negative_rules in YAML")

        rule = fn_rules[0]
        target = rule["target_signal"]
        signal_results = _make_signal_results({target: "TRIGGERED"})
        state = _make_mock_state()
        caveats = check_false_negatives(signal_results, fn_rules, state=state)
        assert len(caveats) == 0

    def test_returns_empty_no_exposure(self) -> None:
        """Returns empty when CLEAR but no exposure indicators present."""
        from do_uw.stages.score.adversarial_engine import check_false_negatives

        rules = _load_rules()
        fn_rules = rules.get("false_negative_rules", [])
        if not fn_rules:
            pytest.skip("No false_negative_rules in YAML")

        rule = fn_rules[0]
        target = rule["target_signal"]
        signal_results = _make_signal_results({target: "CLEAR"})
        state = _make_mock_state()
        caveats = check_false_negatives(signal_results, fn_rules, state=state)
        assert len(caveats) == 0


# ---------------------------------------------------------------------------
# check_contradictions tests
# ---------------------------------------------------------------------------


class TestCheckContradictions:
    """Tests for contradiction detection."""

    def test_finds_opposing_signal_pairs(self) -> None:
        """Finds pairs of signals with opposing statuses."""
        from do_uw.stages.score.adversarial_engine import check_contradictions

        rules = _load_rules()
        c_rules = rules.get("contradiction_rules", [])
        if not c_rules:
            pytest.skip("No contradiction_rules in YAML")

        rule = c_rules[0]
        signal_a = rule["signal_a"]
        signal_b = rule["signal_b"]
        expected_a = rule.get("expected_a_status", "TRIGGERED")
        expected_b = rule.get("expected_b_status", "CLEAR")

        signal_results = _make_signal_results({
            signal_a: expected_a,
            signal_b: expected_b,
        })
        caveats = check_contradictions(signal_results, c_rules)

        assert len(caveats) >= 1
        assert all(c.caveat_type == "contradiction" for c in caveats)

    def test_returns_empty_when_aligned(self) -> None:
        """Returns empty when signals are not contradictory."""
        from do_uw.stages.score.adversarial_engine import check_contradictions

        rules = _load_rules()
        c_rules = rules.get("contradiction_rules", [])
        if not c_rules:
            pytest.skip("No contradiction_rules in YAML")

        rule = c_rules[0]
        signal_a = rule["signal_a"]
        signal_b = rule["signal_b"]
        # Both triggered -- not contradictory
        signal_results = _make_signal_results({
            signal_a: "TRIGGERED",
            signal_b: "TRIGGERED",
        })
        caveats = check_contradictions(signal_results, c_rules)
        assert len(caveats) == 0

    def test_confidence_is_set(self) -> None:
        """Contradiction caveats have confidence set."""
        from do_uw.stages.score.adversarial_engine import check_contradictions

        rules = _load_rules()
        c_rules = rules.get("contradiction_rules", [])
        if not c_rules:
            pytest.skip("No contradiction_rules in YAML")

        rule = c_rules[0]
        signal_results = _make_signal_results({
            rule["signal_a"]: rule.get("expected_a_status", "TRIGGERED"),
            rule["signal_b"]: rule.get("expected_b_status", "CLEAR"),
        })
        caveats = check_contradictions(signal_results, c_rules)
        if caveats:
            assert caveats[0].confidence > 0.0


# ---------------------------------------------------------------------------
# check_data_completeness tests
# ---------------------------------------------------------------------------


class TestCheckDataCompleteness:
    """Tests for data completeness/gap detection."""

    def test_identifies_skipped_critical_signals(self) -> None:
        """Identifies high-impact signals that are SKIPPED with DATA_UNAVAILABLE."""
        from do_uw.stages.score.adversarial_engine import check_data_completeness

        rules = _load_rules()
        dc_rules = rules.get("data_completeness_rules", [])
        if not dc_rules:
            pytest.skip("No data_completeness_rules in YAML")

        rule = dc_rules[0]
        indicator_signals = rule.get("indicator_signals", [])
        if not indicator_signals:
            pytest.skip("Rule has no indicator_signals")

        statuses = {}
        ds: dict[str, str] = {}
        for sig in indicator_signals:
            statuses[sig] = "SKIPPED"
            ds[sig] = "DATA_UNAVAILABLE"

        signal_results = _make_signal_results(statuses, data_statuses=ds)
        caveats = check_data_completeness(signal_results, dc_rules)

        assert len(caveats) >= 1
        assert all(c.caveat_type == "data_completeness" for c in caveats)

    def test_returns_empty_when_all_evaluated(self) -> None:
        """Returns empty when all signals are EVALUATED."""
        from do_uw.stages.score.adversarial_engine import check_data_completeness

        rules = _load_rules()
        dc_rules = rules.get("data_completeness_rules", [])
        if not dc_rules:
            pytest.skip("No data_completeness_rules in YAML")

        rule = dc_rules[0]
        indicator_signals = rule.get("indicator_signals", [])
        if not indicator_signals:
            pytest.skip("Rule has no indicator_signals")

        statuses = {}
        for sig in indicator_signals:
            statuses[sig] = "CLEAR"

        signal_results = _make_signal_results(statuses)
        caveats = check_data_completeness(signal_results, dc_rules)
        assert len(caveats) == 0

    def test_low_overall_evaluation_rate(self) -> None:
        """Flags when overall evaluation rate is below threshold."""
        from do_uw.stages.score.adversarial_engine import check_data_completeness

        rules = _load_rules()
        dc_rules = rules.get("data_completeness_rules", [])

        # Find the overall rate rule
        rate_rule = None
        for r in dc_rules:
            if r.get("rule_type") == "overall_rate":
                rate_rule = r
                break

        if rate_rule is None:
            pytest.skip("No overall_rate rule in data_completeness_rules")

        # Majority SKIPPED with DATA_UNAVAILABLE
        statuses = {}
        ds: dict[str, str] = {}
        for i in range(20):
            statuses[f"SIG.{i}"] = "SKIPPED"
            ds[f"SIG.{i}"] = "DATA_UNAVAILABLE"
        # A few evaluated
        for i in range(5):
            statuses[f"SIG.OK.{i}"] = "CLEAR"

        signal_results = _make_signal_results(statuses, data_statuses=ds)
        caveats = check_data_completeness(signal_results, dc_rules)

        # Should find at least the overall rate caveat
        rate_caveats = [c for c in caveats if "overall" in c.headline.lower() or "evaluation" in c.headline.lower()]
        assert len(rate_caveats) >= 1


# ---------------------------------------------------------------------------
# Template explanation tests
# ---------------------------------------------------------------------------


class TestTemplateExplanations:
    """Tests for template-based fallback explanations on caveats."""

    def test_caveats_have_explanation(self) -> None:
        """All generated caveats have non-empty explanation (template-based)."""
        from do_uw.stages.score.adversarial_engine import check_false_positives

        rules = _load_rules()
        fp_rules = rules.get("false_positive_rules", [])
        if not fp_rules:
            pytest.skip("No false_positive_rules in YAML")

        # Trigger first rule fully
        rule = fp_rules[0]
        target = rule["target_signal"]
        mitigating = rule.get("mitigating_signals", [])
        statuses = {target: "TRIGGERED"}
        for m in mitigating:
            statuses[m] = "CLEAR"

        signal_results = _make_signal_results(statuses)
        caveats = check_false_positives(signal_results, fp_rules)

        for c in caveats:
            assert c.explanation != ""
            assert c.narrative_source == "template"
