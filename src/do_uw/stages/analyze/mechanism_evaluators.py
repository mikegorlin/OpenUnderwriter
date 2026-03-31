"""Mechanism evaluators for conjunction, absence, contextual, trend, and peer_comparison signals.

Phase 110-01: Conjunction, absence, contextual evaluators.
Phase 111-02: Trend and peer_comparison evaluators.

These evaluators are dispatched by signal_engine when a signal has
evaluation.mechanism != "threshold". They operate on already-computed
signal results (inference-class signals run AFTER standard signals).

Each evaluator returns a SignalResult (same type as standard evaluators).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.signal_results import DataStatus, SignalResult, SignalStatus

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

__all__ = [
    "evaluate_absence",
    "evaluate_conjunction",
    "evaluate_contextual",
    "evaluate_peer_comparison",
    "evaluate_trend",
]


# ---------------------------------------------------------------------------
# Conjunction evaluator
# ---------------------------------------------------------------------------


def evaluate_conjunction(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
) -> SignalResult:
    """Evaluate a conjunction signal: checks if multiple signals co-fire.

    Reads conjunction_rules from sig["evaluation"]["conjunction_rules"].
    For each required_signal, looks up status in signal_results dict.
    If matched >= minimum_matches, returns TRIGGERED.
    If >50% of component signals are SKIPPED/missing, returns SKIPPED.

    Args:
        sig: Signal config dict with conjunction_rules in evaluation.
        data: Mapped data dict (unused for conjunction, but kept for API consistency).
        signal_results: Dict of {signal_id: {status, value, ...}} from prior evaluation.

    Returns:
        SignalResult with TRIGGERED, CLEAR, or SKIPPED status.
    """
    signal_id = sig.get("id", "UNKNOWN")
    signal_name = sig.get("name", "")

    eval_spec = sig.get("evaluation", {})
    rules = eval_spec.get("conjunction_rules", {})
    if not rules:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No conjunction_rules defined"
        )

    required_signals: list[str] = rules.get("required_signals", [])
    minimum_matches: int = rules.get("minimum_matches", 2)
    signal_conditions: dict[str, str] = rules.get("signal_conditions", {})
    recommendation_floor: str | None = rules.get("recommendation_floor")

    if not required_signals:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No required_signals specified"
        )

    # Count matches and skipped
    matched: list[str] = []
    skipped_count = 0
    missing_count = 0

    for req_id in required_signals:
        entry = signal_results.get(req_id)
        if entry is None:
            missing_count += 1
            continue

        status = entry.get("status", "")
        expected = signal_conditions.get(req_id, "TRIGGERED")

        if expected == "TRIGGERED":
            # Match on TRIGGERED (or RED/YELLOW for legacy compatibility)
            if status in ("TRIGGERED", "RED", "YELLOW"):
                matched.append(req_id)
            elif status == "SKIPPED":
                skipped_count += 1
        elif expected == "CLEAR":
            # Match on CLEAR (absence of a condition)
            if status == "CLEAR":
                matched.append(req_id)
            elif status == "SKIPPED":
                skipped_count += 1
        else:
            # Exact match on custom status
            if status == expected:
                matched.append(req_id)
            elif status == "SKIPPED":
                skipped_count += 1

    total = len(required_signals)
    unavailable = skipped_count + missing_count

    # If >50% unavailable, can't reliably evaluate
    if total > 0 and unavailable / total > 0.5:
        return _make_mechanism_skipped(
            signal_id,
            signal_name,
            sig,
            f"{unavailable}/{total} component signals unavailable",
        )

    # Check if minimum matches met
    if len(matched) >= minimum_matches:
        evidence = (
            f"Conjunction fired: {len(matched)}/{total} signals matched "
            f"(minimum: {minimum_matches}). Matched: {', '.join(matched)}"
        )
        details: dict[str, Any] = {
            "matched_signals": matched,
            "matched_count": len(matched),
            "required_count": total,
            "minimum_matches": minimum_matches,
            "mechanism": "conjunction",
        }
        if recommendation_floor:
            details["recommendation_floor"] = recommendation_floor

        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.TRIGGERED,
            threshold_level="red",
            evidence=evidence,
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details=details,
        )

    # Not enough matches -> CLEAR
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=SignalStatus.CLEAR,
        evidence=(
            f"Conjunction not met: {len(matched)}/{total} matched "
            f"(minimum: {minimum_matches})"
        ),
        factors=sig.get("factors", []),
        section=sig.get("section", 0),
        details={
            "matched_signals": matched,
            "matched_count": len(matched),
            "required_count": total,
            "minimum_matches": minimum_matches,
            "mechanism": "conjunction",
        },
    )


# ---------------------------------------------------------------------------
# Absence evaluator
# ---------------------------------------------------------------------------


def evaluate_absence(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
    *,
    company: Any | None = None,
) -> SignalResult:
    """Evaluate an absence signal: detect missing expected disclosures.

    Reads absence_rules from sig["evaluation"]["absence_rules"].
    Checks if expected disclosure signals are present in signal_results.

    Three expectation types:
    - always_expected: fire if signal SKIPPED regardless of company profile
    - company_profile: fire only if company attributes indicate expectation
    - peer_comparison: fire if peers have the disclosure but company doesn't

    Args:
        sig: Signal config dict with absence_rules in evaluation.
        data: Mapped data dict (unused for absence).
        signal_results: Dict of {signal_id: {status, value, ...}}.
        company: Optional CompanyProfile for company_profile checks.

    Returns:
        SignalResult with TRIGGERED, CLEAR, or SKIPPED status.
    """
    signal_id = sig.get("id", "UNKNOWN")
    signal_name = sig.get("name", "")

    eval_spec = sig.get("evaluation", {})
    rules = eval_spec.get("absence_rules", {})
    if not rules:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No absence_rules defined"
        )

    expectation_type: str = rules.get("expectation_type", "always_expected")
    expected_signals: list[str] = rules.get("expected_signals", [])
    condition: str = rules.get("condition", "")

    if not expected_signals:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No expected_signals specified"
        )

    # For company_profile type, check if company matches criteria
    if expectation_type == "company_profile":
        if company is None:
            return _make_mechanism_skipped(
                signal_id,
                signal_name,
                sig,
                "Company profile required but not available",
            )
        # Company profile checks are based on the condition string.
        # For now, if company is available, proceed with the check.
        # The condition is documentation-only; actual filtering happens
        # at the signal level based on which signals are expected.

    # Check each expected signal
    any_present = False
    any_absent = False
    all_unavailable = True

    for exp_id in expected_signals:
        entry = signal_results.get(exp_id)
        if entry is None:
            # Signal not in results at all -> can't determine
            continue

        all_unavailable = False
        status = entry.get("status", "")
        data_status = entry.get("data_status", "EVALUATED")

        # If data was never acquired, we can't conclude absence
        if data_status == "DATA_UNAVAILABLE":
            continue

        # Signal was evaluated (data available)
        if status in ("TRIGGERED", "CLEAR", "INFO"):
            # Disclosure is present (signal ran and produced a result)
            any_present = True
        elif status == "SKIPPED":
            # Signal tried to evaluate but had no data -> disclosure absent
            if data_status in ("EVALUATED", "NOT_APPLICABLE"):
                any_absent = True
            else:
                # DATA_UNAVAILABLE = didn't look, not absent
                pass

    # If no expected signals found in results at all -> SKIPPED
    if all_unavailable:
        return _make_mechanism_skipped(
            signal_id,
            signal_name,
            sig,
            "Expected signals not found in evaluation results",
        )

    # If any expected signal is present (TRIGGERED or CLEAR), disclosure exists
    if any_present:
        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.CLEAR,
            evidence=f"Expected disclosure present: {', '.join(expected_signals)}",
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details={
                "expectation_type": expectation_type,
                "condition": condition,
                "mechanism": "absence",
            },
        )

    # If absent (signal was SKIPPED with evaluated status)
    if any_absent:
        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.TRIGGERED,
            threshold_level="yellow",
            evidence=(
                f"Missing expected disclosure: {', '.join(expected_signals)}. "
                f"Expectation: {expectation_type} ({condition})"
            ),
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details={
                "expectation_type": expectation_type,
                "condition": condition,
                "absent_signals": expected_signals,
                "mechanism": "absence",
            },
        )

    # Neither clearly present nor absent -> SKIPPED
    return _make_mechanism_skipped(
        signal_id,
        signal_name,
        sig,
        "Could not determine disclosure presence or absence",
    )


# ---------------------------------------------------------------------------
# Contextual evaluator
# ---------------------------------------------------------------------------


def evaluate_contextual(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
    *,
    company: Any | None = None,
    company_context: dict[str, str] | None = None,
) -> SignalResult:
    """Evaluate a contextual signal: re-evaluate through company-type lens.

    Reads contextual_rules from sig["evaluation"]["contextual_rules"].
    Looks up source signal result, determines company context, applies
    threshold adjustment based on context_adjustments mapping.

    Args:
        sig: Signal config dict with contextual_rules in evaluation.
        data: Mapped data dict (unused for contextual).
        signal_results: Dict of {signal_id: {status, value, ...}}.
        company: Optional CompanyProfile.
        company_context: Pre-computed context dict {dimension: value}.

    Returns:
        SignalResult with TRIGGERED, CLEAR, SKIPPED, or INFO status.
    """
    signal_id = sig.get("id", "UNKNOWN")
    signal_name = sig.get("name", "")

    eval_spec = sig.get("evaluation", {})
    rules = eval_spec.get("contextual_rules", {})
    if not rules:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No contextual_rules defined"
        )

    source_signal: str = rules.get("source_signal", "")
    context_dimensions: list[str] = rules.get("context_dimensions", [])
    context_adjustments: dict[str, Any] = rules.get("context_adjustments", {})

    if not source_signal:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No source_signal specified"
        )

    # Look up source signal result
    source_entry = signal_results.get(source_signal)
    if source_entry is None:
        return _make_mechanism_skipped(
            signal_id,
            signal_name,
            sig,
            f"Source signal {source_signal} not in results",
        )

    # Determine company context
    ctx = company_context or {}

    # Check if required context dimensions are available
    if not context_dimensions:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No context_dimensions specified"
        )

    # Find the first available context dimension value
    context_value: str | None = None
    matched_dimension: str | None = None
    for dim in context_dimensions:
        if dim in ctx:
            context_value = ctx[dim]
            matched_dimension = dim
            break

    if context_value is None:
        return _make_mechanism_skipped(
            signal_id,
            signal_name,
            sig,
            f"Required context dimensions {context_dimensions} not available",
        )

    # Look up adjustment for this context value
    adjustment_entry = context_adjustments.get(context_value)
    source_status = source_entry.get("status", "")

    if adjustment_entry is None:
        # No specific adjustment for this context -> pass through source status as INFO
        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.INFO,
            evidence=(
                f"Contextual evaluation: {source_signal} status={source_status}, "
                f"context {matched_dimension}={context_value} (no adjustment defined)"
            ),
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details={
                "source_signal": source_signal,
                "source_status": source_status,
                "context_dimension": matched_dimension,
                "context_value": context_value,
                "adjustment": None,
                "mechanism": "contextual",
            },
        )

    # Apply adjustment
    threshold_adj = 1.0
    rationale = ""
    if isinstance(adjustment_entry, dict):
        threshold_adj = float(adjustment_entry.get("threshold_adjustment", 1.0))
        rationale = adjustment_entry.get("rationale", "")

    # Contextual re-evaluation logic:
    # If source signal was TRIGGERED and adjustment < 1.0 (lower bar), it remains TRIGGERED
    # If source signal was TRIGGERED and adjustment > 1.0 (higher bar), it may become CLEAR
    # If source signal was CLEAR and adjustment < 1.0 (lower bar), it may become TRIGGERED
    # For simplicity, we translate the adjustment into a severity interpretation
    if source_status in ("TRIGGERED", "RED", "YELLOW"):
        if threshold_adj <= 1.0:
            # Lower threshold -> signal is even more concerning
            result_status = SignalStatus.TRIGGERED
            level = "red"
        else:
            # Higher threshold -> signal may be less concerning in context
            result_status = SignalStatus.INFO
            level = ""
    elif source_status == "CLEAR":
        if threshold_adj < 1.0:
            # Lower threshold -> CLEAR result might actually be a concern
            result_status = SignalStatus.TRIGGERED
            level = "yellow"
        else:
            result_status = SignalStatus.CLEAR
            level = ""
    else:
        # SKIPPED or other -> pass through
        result_status = SignalStatus.INFO
        level = ""

    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=result_status,
        threshold_level=level,
        evidence=(
            f"Contextual re-evaluation of {source_signal} "
            f"({source_status}) through {matched_dimension}={context_value} lens. "
            f"Adjustment: {threshold_adj}x. {rationale}"
        ),
        factors=sig.get("factors", []),
        section=sig.get("section", 0),
        details={
            "source_signal": source_signal,
            "source_status": source_status,
            "context_dimension": matched_dimension,
            "context_value": context_value,
            "threshold_adjustment": threshold_adj,
            "rationale": rationale,
            "mechanism": "contextual",
        },
    )


# ---------------------------------------------------------------------------
# Trend evaluator
# ---------------------------------------------------------------------------


def evaluate_trend(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
) -> SignalResult:
    """Evaluate a trend signal: compare current vs prior period values.

    Reads field_key from sig["data_strategy"]["field_key"] and looks for
    current and prior values in the data dict. Calculates delta and
    percentage change, compares against threshold from evaluation spec.

    Supports two direction modes:
    - increasing_is_risk: trigger when pct_change > threshold (e.g., rising debt)
    - decreasing_is_risk: trigger when pct_change < -threshold (e.g., falling revenue)

    Args:
        sig: Signal config dict with data_strategy.field_key and evaluation block.
        data: Mapped data dict containing current and prior values.
        signal_results: Dict of prior signal results (unused, kept for API consistency).

    Returns:
        SignalResult with TRIGGERED, CLEAR, or SKIPPED status.
    """
    signal_id = sig.get("id", "UNKNOWN")
    signal_name = sig.get("name", "")

    # Extract field key
    data_strategy = sig.get("data_strategy", {})
    field_key = data_strategy.get("field_key", "") if isinstance(data_strategy, dict) else ""

    if not field_key:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No field_key in data_strategy"
        )

    # Get current value
    current_value = data.get(field_key)
    if current_value is None:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No trend data available for field"
        )

    # Get prior value -- look for {field_key}_prior pattern
    prior_value = data.get(f"{field_key}_prior")

    # Also check YoY comparison data patterns (extracted.ten_k_yoy)
    if prior_value is None:
        prior_value = data.get("prior_value")
    if prior_value is None:
        prior_value = data.get(f"{field_key}_previous")

    if prior_value is None:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig,
            f"No prior period data available for {field_key}",
        )

    # Coerce to float
    try:
        current_f = float(current_value)
        prior_f = float(prior_value)
    except (TypeError, ValueError):
        return _make_mechanism_skipped(
            signal_id, signal_name, sig,
            f"Cannot convert trend values to numeric: current={current_value}, prior={prior_value}",
        )

    # Calculate delta and pct_change
    delta = current_f - prior_f
    if prior_f != 0:
        pct_change = delta / abs(prior_f)
    else:
        pct_change = 0.0 if delta == 0 else (1.0 if delta > 0 else -1.0)

    # Get threshold and direction from evaluation spec
    eval_spec = sig.get("evaluation", {})
    threshold = float(eval_spec.get("threshold", 0.10))
    direction = str(eval_spec.get("direction", "increasing_is_risk"))

    # Determine direction interpretation
    if direction == "decreasing_is_risk":
        is_risky = pct_change < -threshold
        direction_label = "deteriorating" if pct_change < 0 else "improving"
    else:
        # increasing_is_risk (default)
        is_risky = pct_change > threshold
        direction_label = "deteriorating" if pct_change > 0 else "improving"

    details: dict[str, Any] = {
        "current_value": current_f,
        "prior_value": prior_f,
        "delta": round(delta, 4),
        "pct_change": round(pct_change, 4),
        "direction": direction_label,
        "threshold": threshold,
        "direction_mode": direction,
        "mechanism": "trend",
    }

    if is_risky:
        evidence = (
            f"Trend {direction_label}: {field_key} changed {pct_change:+.1%} "
            f"(from {prior_f} to {current_f}), exceeds {threshold:.0%} threshold"
        )
        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.TRIGGERED,
            threshold_level="red" if abs(pct_change) > threshold * 2 else "yellow",
            value=current_f,
            evidence=evidence,
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details=details,
        )

    evidence = (
        f"Trend {direction_label}: {field_key} changed {pct_change:+.1%} "
        f"(from {prior_f} to {current_f}), within {threshold:.0%} threshold"
    )
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=SignalStatus.CLEAR,
        value=current_f,
        evidence=evidence,
        factors=sig.get("factors", []),
        section=sig.get("section", 0),
        details=details,
    )


# ---------------------------------------------------------------------------
# Peer comparison evaluator
# ---------------------------------------------------------------------------


def evaluate_peer_comparison(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
    *,
    benchmarks: dict[str, Any] | None = None,
) -> SignalResult:
    """Evaluate a peer comparison signal: compare company value to SEC Frames percentile.

    Reads field_key from sig["data_strategy"]["field_key"], looks up the
    company's percentile position from the benchmarks dict (frames_percentiles),
    and compares against the threshold percentile.

    Supports two direction modes:
    - high_is_risk: trigger when percentile > threshold (outlier high, e.g., excessive leverage)
    - low_is_risk: trigger when percentile < threshold (outlier low, e.g., weak liquidity)

    Args:
        sig: Signal config dict with data_strategy.field_key and evaluation block.
        data: Mapped data dict containing the company metric value.
        signal_results: Dict of prior signal results (unused, kept for API consistency).
        benchmarks: Dict of {metric_name: {overall_percentile, sector_percentile, ...}}.

    Returns:
        SignalResult with TRIGGERED, CLEAR, or SKIPPED status.
    """
    signal_id = sig.get("id", "UNKNOWN")
    signal_name = sig.get("name", "")

    # Extract field key
    data_strategy = sig.get("data_strategy", {})
    field_key = data_strategy.get("field_key", "") if isinstance(data_strategy, dict) else ""

    if not field_key:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig, "No field_key in data_strategy"
        )

    # Check benchmarks available
    if not benchmarks:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig,
            "No peer comparison data available",
        )

    # Look up metric in benchmarks
    metric_data = benchmarks.get(field_key)
    if metric_data is None:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig,
            f"Metric {field_key} not found in benchmark data",
        )

    # Get percentile values
    overall_percentile = metric_data.get("overall_percentile")
    sector_percentile = metric_data.get("sector_percentile")

    if overall_percentile is None:
        return _make_mechanism_skipped(
            signal_id, signal_name, sig,
            f"No percentile data for {field_key}",
        )

    # Get company value from data
    company_value = data.get(field_key)

    # Get threshold and direction from evaluation spec
    eval_spec = sig.get("evaluation", {})
    threshold_percentile = float(eval_spec.get("threshold_percentile", 75.0))
    direction = str(eval_spec.get("direction", "high_is_risk"))

    overall_f = float(overall_percentile)
    sector_f = float(sector_percentile) if sector_percentile is not None else None

    # Determine if triggered based on direction
    if direction == "low_is_risk":
        is_risky = overall_f < threshold_percentile
    else:
        # high_is_risk (default)
        is_risky = overall_f > threshold_percentile

    details: dict[str, Any] = {
        "company_value": company_value,
        "overall_percentile": overall_f,
        "metric_name": field_key,
        "threshold_percentile": threshold_percentile,
        "direction_mode": direction,
        "mechanism": "peer_comparison",
    }
    if sector_f is not None:
        details["sector_percentile"] = sector_f

    if is_risky:
        evidence = (
            f"Peer outlier: {field_key} at {overall_f:.0f}th percentile "
            f"(threshold: {threshold_percentile:.0f}th, direction: {direction})"
        )
        if sector_f is not None:
            evidence += f", sector: {sector_f:.0f}th percentile"
        return SignalResult(
            signal_id=signal_id,
            signal_name=signal_name,
            status=SignalStatus.TRIGGERED,
            threshold_level="red" if abs(overall_f - 50) > 40 else "yellow",
            value=company_value,
            evidence=evidence,
            factors=sig.get("factors", []),
            section=sig.get("section", 0),
            details=details,
        )

    evidence = (
        f"Within peer range: {field_key} at {overall_f:.0f}th percentile "
        f"(threshold: {threshold_percentile:.0f}th)"
    )
    if sector_f is not None:
        evidence += f", sector: {sector_f:.0f}th percentile"
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=SignalStatus.CLEAR,
        value=company_value,
        evidence=evidence,
        factors=sig.get("factors", []),
        section=sig.get("section", 0),
        details=details,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_mechanism_skipped(
    signal_id: str,
    signal_name: str,
    sig: dict[str, Any],
    reason: str,
) -> SignalResult:
    """Create a SKIPPED result for a mechanism evaluator."""
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=SignalStatus.SKIPPED,
        evidence=reason,
        factors=sig.get("factors", []),
        section=sig.get("section", 0),
        data_status=DataStatus.DATA_UNAVAILABLE,
        data_status_reason=reason,
        details={"mechanism": sig.get("evaluation", {}).get("mechanism", "unknown")},
    )
