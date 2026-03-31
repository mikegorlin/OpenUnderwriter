"""Adversarial critique engine -- rule-based detection for 4 caveat types.

Phase 110-02: Pure functions that evaluate signal_results against YAML rules
to produce Caveat objects. Each function handles one caveat type:
  - check_false_positives: TRIGGERED signals with mitigating CLEAR signals
  - check_false_negatives: CLEAR signals where exposure indicators suggest risk
  - check_contradictions: Signal pairs with opposing statuses
  - check_data_completeness: Missing data that weakens conclusions

All functions are read-only -- they NEVER modify scores, tiers, or state.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.adversarial import Caveat

__all__ = [
    "check_contradictions",
    "check_data_completeness",
    "check_false_negatives",
    "check_false_positives",
]

logger = logging.getLogger(__name__)


def _signal_status(
    signal_results: dict[str, dict[str, Any]],
    signal_id: str,
) -> str | None:
    """Extract status string from signal_results for a given signal_id."""
    sig = signal_results.get(signal_id)
    if isinstance(sig, dict):
        return sig.get("status")
    return None


def _is_triggered(status: str | None) -> bool:
    """Check if a signal status indicates it fired."""
    return status in ("TRIGGERED", "RED", "YELLOW")


def _is_clear(status: str | None) -> bool:
    """Check if a signal status indicates it is clear."""
    return status in ("CLEAR", "GREEN")


def _data_status(
    signal_results: dict[str, dict[str, Any]],
    signal_id: str,
) -> str:
    """Extract data_status from signal_results."""
    sig = signal_results.get(signal_id)
    if isinstance(sig, dict):
        return sig.get("data_status", "EVALUATED")
    return "EVALUATED"


# ---------------------------------------------------------------------------
# False positive detection
# ---------------------------------------------------------------------------


def check_false_positives(
    signal_results: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
    *,
    state: Any | None = None,
) -> list[Caveat]:
    """Detect potential false positives: TRIGGERED signals with mitigating evidence.

    For each rule: if target signal is TRIGGERED and enough mitigating signals
    are CLEAR, creates a caveat. Confidence = mitigating_count / total_mitigating.

    Args:
        signal_results: Signal evaluation results dict.
        rules: false_positive_rules from adversarial_rules.yaml.
        state: Optional AnalysisState for additional context.

    Returns:
        List of Caveat objects with caveat_type="false_positive".
    """
    caveats: list[Caveat] = []

    for rule in rules:
        target = rule.get("target_signal", "")
        mitigating_ids: list[str] = rule.get("mitigating_signals", [])
        minimum = rule.get("minimum_mitigating", 1)

        target_status = _signal_status(signal_results, target)
        if not _is_triggered(target_status):
            continue

        # Count mitigating signals that are CLEAR
        clear_count = 0
        clear_ids: list[str] = []
        for mid in mitigating_ids:
            ms = _signal_status(signal_results, mid)
            if _is_clear(ms):
                clear_count += 1
                clear_ids.append(mid)

        if clear_count < minimum:
            continue

        total = len(mitigating_ids) if mitigating_ids else 1
        confidence = clear_count / total

        headline = rule.get("headline_template", "Possible false positive")
        explanation = rule.get("explanation_template", "").format(
            mitigating_count=clear_count,
        )
        severity = rule.get("severity", "info")

        caveats.append(
            Caveat(
                caveat_type="false_positive",
                target_signal_id=target,
                headline=headline,
                explanation=explanation,
                confidence=round(confidence, 4),
                evidence=[f"{mid} is CLEAR" for mid in clear_ids],
                severity=severity,
                narrative_source="template",
            )
        )

    return caveats


# ---------------------------------------------------------------------------
# False negative (blind spot) detection
# ---------------------------------------------------------------------------


def check_false_negatives(
    signal_results: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
    *,
    state: Any | None = None,
) -> list[Caveat]:
    """Detect potential false negatives: CLEAR signals despite exposure indicators.

    For each rule: if target signal is CLEAR but exposure_indicators are
    TRIGGERED, the system may be missing a real risk.

    Args:
        signal_results: Signal evaluation results dict.
        rules: false_negative_rules from adversarial_rules.yaml.
        state: Optional AnalysisState for company context.

    Returns:
        List of Caveat objects with caveat_type="false_negative".
    """
    caveats: list[Caveat] = []

    for rule in rules:
        target = rule.get("target_signal", "")
        indicator_ids: list[str] = rule.get("exposure_indicators", [])
        minimum = rule.get("minimum_indicators", 1)

        target_status = _signal_status(signal_results, target)
        if not _is_clear(target_status):
            continue

        # Count exposure indicators that are TRIGGERED
        triggered_count = 0
        triggered_ids: list[str] = []
        for ind in indicator_ids:
            ind_status = _signal_status(signal_results, ind)
            if _is_triggered(ind_status):
                triggered_count += 1
                triggered_ids.append(ind)

        if triggered_count < minimum:
            continue

        total = len(indicator_ids) if indicator_ids else 1
        confidence = triggered_count / total

        headline = rule.get("headline_template", "Potential blind spot")
        explanation = rule.get("explanation_template", "")
        severity = rule.get("severity", "info")

        caveats.append(
            Caveat(
                caveat_type="false_negative",
                target_signal_id=target,
                headline=headline,
                explanation=explanation,
                confidence=round(confidence, 4),
                evidence=[f"{ind} is TRIGGERED" for ind in triggered_ids],
                severity=severity,
                narrative_source="template",
            )
        )

    return caveats


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------


def check_contradictions(
    signal_results: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
) -> list[Caveat]:
    """Detect contradictory signal pairs suggesting incomplete picture.

    For each rule: if signal_a matches expected_a_status and signal_b
    matches expected_b_status, the combination is contradictory.

    Args:
        signal_results: Signal evaluation results dict.
        rules: contradiction_rules from adversarial_rules.yaml.

    Returns:
        List of Caveat objects with caveat_type="contradiction".
    """
    caveats: list[Caveat] = []

    for rule in rules:
        sig_a = rule.get("signal_a", "")
        sig_b = rule.get("signal_b", "")
        expected_a = rule.get("expected_a_status", "TRIGGERED")
        expected_b = rule.get("expected_b_status", "CLEAR")

        status_a = _signal_status(signal_results, sig_a)
        status_b = _signal_status(signal_results, sig_b)

        if status_a is None or status_b is None:
            continue

        # Check if actual statuses match the expected contradiction pattern
        a_matches = (
            _is_triggered(status_a)
            if _is_triggered(expected_a)
            else _is_clear(status_a)
        )
        b_matches = (
            _is_triggered(status_b)
            if _is_triggered(expected_b)
            else _is_clear(status_b)
        )

        if not (a_matches and b_matches):
            continue

        confidence = rule.get("confidence_level", 0.7)
        headline = rule.get("headline_template", "Contradictory signals detected")
        explanation = rule.get("explanation_template", "")
        severity = rule.get("severity", "caution")

        caveats.append(
            Caveat(
                caveat_type="contradiction",
                target_signal_id=sig_a,
                headline=headline,
                explanation=explanation,
                confidence=float(confidence),
                evidence=[
                    f"{sig_a} is {status_a}",
                    f"{sig_b} is {status_b}",
                ],
                severity=severity,
                narrative_source="template",
            )
        )

    return caveats


# ---------------------------------------------------------------------------
# Data completeness detection
# ---------------------------------------------------------------------------


def check_data_completeness(
    signal_results: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
) -> list[Caveat]:
    """Detect data gaps that weaken analysis conclusions.

    For domain rules: if enough indicator_signals have DATA_UNAVAILABLE
    data_status, the domain's conclusions are unreliable.
    For overall_rate rule: if evaluation rate falls below threshold, flag it.

    Args:
        signal_results: Signal evaluation results dict.
        rules: data_completeness_rules from adversarial_rules.yaml.

    Returns:
        List of Caveat objects with caveat_type="data_completeness".
    """
    caveats: list[Caveat] = []

    for rule in rules:
        rule_type = rule.get("rule_type", "domain")

        if rule_type == "overall_rate":
            caveats.extend(_check_overall_rate(signal_results, rule))
        else:
            caveats.extend(_check_domain_completeness(signal_results, rule))

    return caveats


def _check_domain_completeness(
    signal_results: dict[str, dict[str, Any]],
    rule: dict[str, Any],
) -> list[Caveat]:
    """Check if a specific domain has sufficient data."""
    indicator_ids: list[str] = rule.get("indicator_signals", [])
    minimum_missing = rule.get("minimum_missing", 2)

    missing_count = 0
    missing_ids: list[str] = []

    for sig_id in indicator_ids:
        ds = _data_status(signal_results, sig_id)
        status = _signal_status(signal_results, sig_id)
        if ds == "DATA_UNAVAILABLE" or status == "SKIPPED":
            missing_count += 1
            missing_ids.append(sig_id)

    if missing_count < minimum_missing:
        return []

    headline = rule.get("headline_template", "Data gap detected")
    explanation = rule.get("explanation_template", "")
    severity = rule.get("severity", "caution")

    return [
        Caveat(
            caveat_type="data_completeness",
            target_signal_id="",
            headline=headline,
            explanation=explanation,
            confidence=missing_count / max(len(indicator_ids), 1),
            evidence=[f"{mid} is DATA_UNAVAILABLE" for mid in missing_ids],
            severity=severity,
            narrative_source="template",
        )
    ]


def _check_overall_rate(
    signal_results: dict[str, dict[str, Any]],
    rule: dict[str, Any],
) -> list[Caveat]:
    """Check if overall signal evaluation rate meets threshold."""
    min_pct = rule.get("minimum_evaluation_pct", 50)

    total = len(signal_results)
    if total == 0:
        return []

    evaluated = sum(
        1
        for sig in signal_results.values()
        if isinstance(sig, dict)
        and sig.get("data_status", "EVALUATED") == "EVALUATED"
        and sig.get("status") != "SKIPPED"
    )

    eval_pct = round(100.0 * evaluated / total, 1)

    if eval_pct >= min_pct:
        return []

    headline = rule.get("headline_template", "Low overall evaluation rate")
    explanation = rule.get("explanation_template", "").format(eval_pct=eval_pct)
    severity = rule.get("severity", "warning")

    return [
        Caveat(
            caveat_type="data_completeness",
            target_signal_id="",
            headline=headline,
            explanation=explanation,
            confidence=round(1.0 - eval_pct / 100.0, 4),
            evidence=[
                f"Only {evaluated}/{total} signals evaluated ({eval_pct}%)"
            ],
            severity=severity,
            narrative_source="template",
        )
    ]
