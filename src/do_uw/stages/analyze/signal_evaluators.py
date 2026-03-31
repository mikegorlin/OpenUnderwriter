"""Threshold-type evaluator functions for check execution.

Each evaluator handles a specific threshold type (tiered, boolean,
percentage, count, value, info, temporal) and returns a SignalResult.

These are called by the main dispatcher in signal_engine.evaluate_signal().
"""

from __future__ import annotations

from typing import Any, cast

from do_uw.stages.analyze.signal_helpers import (
    coerce_value,
    extract_factors,
    first_data_value,
    has_numeric_thresholds,
    make_skipped,
    try_numeric_compare,
)
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus


def _summarize_qualitative(data_value: Any) -> str:
    """Produce a human-readable evidence string for qualitative checks.

    Avoids dumping raw dicts/SourcedValue objects into the evidence field.
    """
    if isinstance(data_value, dict):
        # Extract key scalar values from the dict
        parts: list[str] = []
        for k, v in data_value.items():
            if hasattr(v, "value"):
                v = v.value  # noqa: PLW2901 — unwrap SourcedValue
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, dict):
                # Summarize nested dict as key count
                parts.append(f"{k}: ({len(v)} items)")
            elif isinstance(v, list):
                parts.append(f"{k}: [{len(v)} items]")
        return "Qualitative: " + "; ".join(parts) if parts else "Qualitative: data present"
    if hasattr(data_value, "value"):
        return f"Qualitative: {data_value.value}"
    val_str = str(data_value)
    if len(val_str) > 200:
        val_str = val_str[:200] + "..."
    return f"Qualitative: {val_str}"


def evaluate_numeric_threshold(
    check: dict[str, Any],
    data: dict[str, Any],
    threshold: dict[str, Any],
    label: str,
    needs_calibration: bool = True,
) -> SignalResult:
    """Common evaluator for percentage, count, and value threshold types.

    Checks for known clear signals first (defensive), then attempts
    numeric comparison; falls back to INFO if not possible.
    """
    data_value, data_key = first_data_value(data)

    if data_value is None:
        return make_skipped(check, data, needs_calibration)

    # Check for known clear signals FIRST (defensive: prevents numeric parsing
    # from accidentally matching qualitative values like 0.0 for wells_notice=False)
    signal_id = str(check.get("id", ""))
    clear_signal = _check_clear_signal(data_value, data_key, signal_id)
    if clear_signal is not None:
        status, level, evidence = clear_signal
        return SignalResult(
            signal_id=signal_id or "UNKNOWN",
            signal_name=check.get("name", ""),
            status=status,
            value=coerce_value(data_value),
            threshold_level=level,
            evidence=evidence,
            source=data_key,
            factors=extract_factors(check),
            section=check.get("section", 0),
            needs_calibration=needs_calibration,
        )

    # Try numeric comparison
    numeric_result = try_numeric_compare(data_value, threshold)
    if numeric_result is not None:
        status, level, evidence = numeric_result
        return SignalResult(
            signal_id=check.get("id", "UNKNOWN"),
            signal_name=check.get("name", ""),
            status=status,
            value=coerce_value(data_value),
            threshold_level=level,
            evidence=evidence,
            source=data_key,
            factors=extract_factors(check),
            section=check.get("section", 0),
            needs_calibration=needs_calibration,
        )

    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.INFO,
        value=coerce_value(data_value),
        evidence=f"{label} check: value={data_value}",
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=needs_calibration,
    )


def _check_clear_signal(
    data_value: Any,
    data_key: str,
    signal_id: str,
) -> tuple[SignalStatus, str, str] | None:
    """Recognize known clear/negative signals in qualitative data.

    Some checks have string or boolean values where specific values
    definitively indicate CLEAR (no risk). Without this, they'd
    fall through to INFO which obscures the signal.

    Returns (status, threshold_level, evidence) or None if not matched.
    """
    val_str = str(data_value).upper().strip() if data_value is not None else ""

    # SEC enforcement stage: "NONE" means no enforcement activity
    if data_key == "sec_enforcement_stage":
        if val_str in ("NONE", ""):
            return (
                SignalStatus.CLEAR,
                "clear",
                "No SEC enforcement activity",
            )

    # Wells notice: False or "NONE" means no Wells notice
    if data_key == "wells_notice":
        if data_value is False or val_str in ("FALSE", "NONE", ""):
            return (
                SignalStatus.CLEAR,
                "clear",
                "No Wells notice history",
            )

    # Customer concentration: "Not mentioned" = positive (SEC requires
    # disclosure of any customer >10% of revenue; absence means diversified)
    if data_key == "customer_concentration":
        if "NOT MENTIONED" in val_str or val_str == "":
            return (
                SignalStatus.CLEAR,
                "clear",
                "No customer >10% of revenue disclosed "
                "(SEC requires disclosure -- absence indicates diversified base)",
            )

    return None


def evaluate_tiered(
    check: dict[str, Any],
    data: dict[str, Any],
    threshold: dict[str, Any],
) -> SignalResult:
    """Evaluate a tiered threshold check (309 checks).

    For numeric data, attempts numeric comparison against threshold
    values. For string/qualitative data, checks for known clear signals
    before falling back to INFO.
    """
    data_value, data_key = first_data_value(data)
    calibration = has_numeric_thresholds(threshold)

    if data_value is None:
        return make_skipped(check, data, calibration)

    # Check for known clear signals FIRST (defensive: prevents numeric parsing
    # from accidentally matching qualitative values like 0.0 for wells_notice=False)
    signal_id = str(check.get("id", ""))
    clear_signal = _check_clear_signal(data_value, data_key, signal_id)
    if clear_signal is not None:
        status, level, evidence = clear_signal
        return SignalResult(
            signal_id=signal_id or "UNKNOWN",
            signal_name=check.get("name", ""),
            status=status,
            value=coerce_value(data_value),
            threshold_level=level,
            evidence=evidence,
            source=data_key,
            factors=extract_factors(check),
            section=check.get("section", 0),
            needs_calibration=calibration,
        )

    # Try numeric comparison
    numeric_result = try_numeric_compare(data_value, threshold)
    if numeric_result is not None:
        status, level, evidence = numeric_result
        return SignalResult(
            signal_id=check.get("id", "UNKNOWN"),
            signal_name=check.get("name", ""),
            status=status,
            value=coerce_value(data_value),
            threshold_level=level,
            evidence=evidence,
            source=data_key,
            factors=extract_factors(check),
            section=check.get("section", 0),
            needs_calibration=calibration,
        )

    # Qualitative tiered check -- report as INFO
    # Sanitize dict values to avoid raw data dumps in rendered output.
    display_value = "Present" if isinstance(data_value, dict) else coerce_value(data_value)
    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.INFO,
        value=display_value,
        threshold_level="",
        evidence=_summarize_qualitative(data_value),
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=calibration,
    )


def evaluate_boolean(
    check: dict[str, Any],
    data: dict[str, Any],
    threshold: dict[str, Any],
) -> SignalResult:
    """Evaluate a boolean threshold check (2 checks)."""
    data_value, data_key = first_data_value(data)

    if data_value is None:
        return make_skipped(check, data, needs_calibration=False)

    is_true = bool(data_value)
    if is_true:
        return SignalResult(
            signal_id=check.get("id", "UNKNOWN"),
            signal_name=check.get("name", ""),
            status=SignalStatus.TRIGGERED,
            value=coerce_value(data_value),
            threshold_level="red",
            evidence=f"Boolean check: {threshold.get('red', 'True condition met')}",
            source=data_key,
            factors=extract_factors(check),
            section=check.get("section", 0),
            needs_calibration=False,
        )

    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.CLEAR,
        value=coerce_value(data_value),
        threshold_level="clear",
        evidence=f"Boolean check: {threshold.get('clear', 'False condition met')}",
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=False,
    )


def evaluate_info_only(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate an info-only check (info, pattern, search, etc.)."""
    raw_threshold = check.get("threshold")
    threshold_dict = (
        cast(dict[str, Any], raw_threshold)
        if isinstance(raw_threshold, dict)
        else {}
    )
    data_value, data_key = first_data_value(data)

    if data_value is None:
        return make_skipped(check, data, needs_calibration=False)

    ttype: str = str(threshold_dict.get("type", "info"))
    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.INFO,
        value=coerce_value(data_value),
        evidence=f"{ttype} check: {data_value}",
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=False,
    )


def evaluate_temporal(
    check: dict[str, Any],
    data: dict[str, Any],
    threshold: dict[str, Any],
) -> SignalResult:
    """Evaluate a temporal threshold check (delegates to TemporalAnalyzer).

    Temporal checks produce INFO status in the check engine -- the actual
    trend classification (IMPROVING/STABLE/DETERIORATING/CRITICAL) is
    computed by the TemporalAnalyzer and stored in temporal_classification.
    The SCORE stage maps: DETERIORATING/CRITICAL -> TRIGGERED,
    IMPROVING -> CLEAR, STABLE -> INFO.
    """
    data_value, data_key = first_data_value(data)

    if data_value is None:
        return make_skipped(check, data, needs_calibration=False)

    metric = threshold.get("metric", "unknown")
    direction = threshold.get("direction", "lower_is_worse")

    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.INFO,
        value=coerce_value(data_value),
        evidence=f"temporal check: metric={metric}, direction={direction}, value={data_value}",
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=False,
    )


__all__ = [
    "evaluate_boolean",
    "evaluate_info_only",
    "evaluate_numeric_threshold",
    "evaluate_temporal",
    "evaluate_tiered",
]
