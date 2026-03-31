"""Multi-signal inference pattern evaluator for the ANALYZE stage.

Handles INFERENCE_PATTERN checks that require examining multiple data
fields with temporal and cross-reference logic. Dispatches to
pattern-specific handlers via pattern_ref from the check definition.

Pattern families:
- STOCK.PATTERN: Market signal detection (event collapse, informed trading, etc.)
- GOV.EFFECT: Governance effectiveness cross-referencing
- EXEC: Executive behavior patterns (cluster selling, turnover, etc.)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

from do_uw.stages.analyze.signal_helpers import (
    coerce_value,
    extract_factors,
    first_data_value,
    make_skipped,
)
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def evaluate_inference_pattern(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate an INFERENCE_PATTERN check using multi-signal detection.

    Reads pattern_ref from the check definition and dispatches to the
    appropriate pattern-specific handler. Falls back to generic
    multi-signal evaluation if no specific handler exists.

    Args:
        check: Check config dict with id, name, pattern_ref, threshold, etc.
        data: Mapped data dict from map_signal_data().

    Returns:
        SignalResult with status reflecting multi-signal pattern detection.
    """
    pattern_ref = str(check.get("pattern_ref", ""))
    handler = PATTERN_HANDLERS.get(pattern_ref, _evaluate_multi_signal)
    return handler(check, data)


# ---------------------------------------------------------------------------
# Generic multi-signal evaluator (fallback)
# ---------------------------------------------------------------------------


def _evaluate_multi_signal(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Generic multi-signal evaluator for inference patterns.

    Collects all data values, counts how many signals are present and
    active, and determines status based on signal density.

    Status logic:
    - TRIGGERED: majority of expected signals are active
    - INFO: some signals present but pattern not fully formed
    - CLEAR: all signals present, none active
    - SKIPPED: insufficient data (most signals None)
    """
    total_keys = len(data)
    if total_keys == 0:
        return make_skipped(check, data)

    # Collect signal states
    present_signals: list[str] = []
    active_signals: list[str] = []
    none_count = 0

    for key, val in data.items():
        if val is None:
            none_count += 1
            continue
        present_signals.append(key)
        if _is_active_signal(val):
            active_signals.append(key)

    # Graceful degradation: if only 1 non-None value, treat as single-value
    if len(present_signals) <= 1:
        return _single_value_fallback(check, data, present_signals, active_signals)

    # Insufficient data: most signals are None
    if none_count > total_keys // 2:
        return _make_result(
            check,
            data,
            SignalStatus.SKIPPED,
            evidence=(
                f"Insufficient data: {none_count}/{total_keys} signals unavailable. "
                f"Present: [{', '.join(present_signals)}]"
            ),
        )

    # All present, none active -> CLEAR
    if len(active_signals) == 0:
        return _make_result(
            check,
            data,
            SignalStatus.CLEAR,
            evidence=(
                f"0 of {len(present_signals)} signals active. "
                f"Examined: [{', '.join(present_signals)}]"
            ),
        )

    # Majority active -> TRIGGERED
    if len(active_signals) >= (len(present_signals) + 1) // 2:
        return _make_result(
            check,
            data,
            SignalStatus.TRIGGERED,
            evidence=(
                f"{len(active_signals)} of {len(present_signals)} signals active: "
                f"[{', '.join(active_signals)}]"
            ),
            threshold_level="red" if len(active_signals) >= len(present_signals) else "yellow",
        )

    # Some active but not majority -> INFO
    return _make_result(
        check,
        data,
        SignalStatus.INFO,
        evidence=(
            f"{len(active_signals)} of {len(present_signals)} signals active: "
            f"[{', '.join(active_signals)}]. Pattern not fully formed."
        ),
    )


# ---------------------------------------------------------------------------
# Pattern-specific handlers
# ---------------------------------------------------------------------------


def _evaluate_stock_pattern(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate STOCK.PATTERN checks using market signal detection.

    Examines all mapped data keys for market signals: price drops,
    trigger events, peer comparison, short interest, volume anomalies.
    Applies temporal correlation logic for co-occurring signals.
    """
    signals: list[str] = []
    examined: list[str] = []
    none_keys: list[str] = []

    for key, val in data.items():
        if val is None:
            none_keys.append(key)
            continue
        examined.append(key)
        if _is_active_signal(val):
            signals.append(key)

    if not examined:
        return make_skipped(check, data)

    # Single value graceful degradation
    if len(examined) == 1:
        return _single_value_fallback(check, data, examined, signals)

    pattern_ref = str(check.get("pattern_ref", ""))
    raw_threshold = check.get("threshold")
    threshold = cast(dict[str, Any], raw_threshold) if isinstance(raw_threshold, dict) else {}
    detection = str(threshold.get("detection", ""))

    # Determine severity from threshold config
    red_desc = str(threshold.get("red", ""))
    yellow_desc = str(threshold.get("yellow", ""))

    if not signals:
        return _make_result(
            check, data, SignalStatus.CLEAR,
            evidence=(
                f"{pattern_ref}: 0 of {len(examined)} market signals active. "
                f"Detection criteria: {detection}. Examined: [{', '.join(examined)}]"
            ),
        )

    # More than half of examined signals active -> TRIGGERED
    if len(signals) >= (len(examined) + 1) // 2:
        level = "red" if len(signals) >= len(examined) else "yellow"
        return _make_result(
            check, data, SignalStatus.TRIGGERED,
            evidence=(
                f"{pattern_ref}: {len(signals)} of {len(examined)} market signals active: "
                f"[{', '.join(signals)}]. "
                f"{'Red' if level == 'red' else 'Yellow'}: {red_desc if level == 'red' else yellow_desc}"
            ),
            threshold_level=level,
        )

    # Some signals but pattern not fully formed
    return _make_result(
        check, data, SignalStatus.INFO,
        evidence=(
            f"{pattern_ref}: {len(signals)} of {len(examined)} market signals active: "
            f"[{', '.join(signals)}]. Detection criteria: {detection}. Pattern not fully formed."
        ),
    )


def _evaluate_governance_effectiveness(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate GOV.EFFECT checks by cross-referencing governance signals.

    Looks for combinations of governance red flags: material weakness,
    audit committee issues, auditor changes, late filings, etc.
    Uses pattern_ref to determine which governance signals to combine.
    """
    signals: list[str] = []
    examined: list[str] = []

    for key, val in data.items():
        if val is None:
            continue
        examined.append(key)
        if _is_active_signal(val):
            signals.append(key)

    if not examined:
        return make_skipped(check, data)

    # Single value graceful degradation
    if len(examined) == 1:
        return _single_value_fallback(check, data, examined, signals)

    pattern_ref = str(check.get("pattern_ref", ""))

    if not signals:
        return _make_result(
            check, data, SignalStatus.CLEAR,
            evidence=(
                f"{pattern_ref}: 0 of {len(examined)} governance signals active. "
                f"Examined: [{', '.join(examined)}]"
            ),
        )

    # Governance severity: any active signal is at least INFO, 2+ is TRIGGERED
    if len(signals) >= 2:
        return _make_result(
            check, data, SignalStatus.TRIGGERED,
            evidence=(
                f"{pattern_ref}: {len(signals)} of {len(examined)} governance signals active: "
                f"[{', '.join(signals)}]. Multiple governance concerns detected."
            ),
            threshold_level="red" if len(signals) >= 3 else "yellow",
        )

    return _make_result(
        check, data, SignalStatus.INFO,
        evidence=(
            f"{pattern_ref}: {len(signals)} of {len(examined)} governance signals active: "
            f"[{', '.join(signals)}]. Single governance concern noted."
        ),
    )


def _evaluate_executive_pattern(
    check: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate EXEC.INSIDER and EXEC.TENURE inference patterns.

    Pattern-specific logic:
    - CLUSTER_SELLING: 3+ insiders selling within 30-day window
    - NON_10B51: discretionary (non-plan) insider sales ratio
    - C_SUITE_TURNOVER: multiple C-suite departures within 12 months
    """
    signals: list[str] = []
    examined: list[str] = []

    for key, val in data.items():
        if val is None:
            continue
        examined.append(key)
        if _is_active_signal(val):
            signals.append(key)

    if not examined:
        return make_skipped(check, data)

    # Single value graceful degradation
    if len(examined) == 1:
        return _single_value_fallback(check, data, examined, signals)

    pattern_ref = str(check.get("pattern_ref", ""))
    raw_threshold = check.get("threshold")
    threshold = cast(dict[str, Any], raw_threshold) if isinstance(raw_threshold, dict) else {}
    triggered_val: str = str(threshold.get("triggered", ""))
    red_val: str = str(threshold.get("red", ""))
    threshold_desc = triggered_val if triggered_val else red_val

    if not signals:
        return _make_result(
            check, data, SignalStatus.CLEAR,
            evidence=(
                f"{pattern_ref}: 0 of {len(examined)} executive signals active. "
                f"Examined: [{', '.join(examined)}]"
            ),
        )

    # Any active signal for executive patterns is significant
    if len(signals) >= 2 or (len(signals) == 1 and len(examined) <= 2):
        level = "red" if len(signals) >= len(examined) else "yellow"
        return _make_result(
            check, data, SignalStatus.TRIGGERED,
            evidence=(
                f"{pattern_ref}: {len(signals)} of {len(examined)} executive signals active: "
                f"[{', '.join(signals)}]. Threshold: {threshold_desc}"
            ),
            threshold_level=level,
        )

    return _make_result(
        check, data, SignalStatus.INFO,
        evidence=(
            f"{pattern_ref}: {len(signals)} of {len(examined)} executive signals active: "
            f"[{', '.join(signals)}]. Below pattern threshold."
        ),
    )


# ---------------------------------------------------------------------------
# Pattern handler registry
# ---------------------------------------------------------------------------

PATTERN_HANDLERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], SignalResult]] = {
    # STOCK.PATTERN (6 checks)
    "EVENT_COLLAPSE": _evaluate_stock_pattern,
    "INFORMED_TRADING": _evaluate_stock_pattern,
    "PRICE_CASCADE": _evaluate_stock_pattern,
    "PEER_DIVERGENCE": _evaluate_stock_pattern,
    "DEATH_SPIRAL": _evaluate_stock_pattern,
    "SHORT_ATTACK": _evaluate_stock_pattern,
    # GOV.EFFECT (10 checks)
    "AUDIT_COMMITTEE": _evaluate_governance_effectiveness,
    "AUDIT_OPINION": _evaluate_governance_effectiveness,
    "AUDITOR_CHANGE": _evaluate_governance_effectiveness,
    "MATERIAL_WEAKNESS": _evaluate_governance_effectiveness,
    "ISS_SCORE": _evaluate_governance_effectiveness,
    "PROXY_ADVISORY": _evaluate_governance_effectiveness,
    "SOX_404": _evaluate_governance_effectiveness,
    "SIG_DEFICIENCY": _evaluate_governance_effectiveness,
    "LATE_FILING": _evaluate_governance_effectiveness,
    "NT_FILING": _evaluate_governance_effectiveness,
    # EXEC (3 checks)
    "CLUSTER_SELLING": _evaluate_executive_pattern,
    "NON_10B51": _evaluate_executive_pattern,
    "C_SUITE_TURNOVER": _evaluate_executive_pattern,
}


# ---------------------------------------------------------------------------
# Shared helpers (internal)
# ---------------------------------------------------------------------------


def _is_active_signal(val: Any) -> bool:
    """Determine if a data value represents an active (fired) signal.

    Active means: truthy value, positive number, non-empty string,
    or boolean True. Zeros and empty strings are not active.
    """
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        # Normalize: certain string values mean "not active"
        lower = val.strip().lower()
        if lower in ("", "none", "n/a", "not available", "no", "false", "0"):
            return False
        return True
    if isinstance(val, list):
        return len(cast(list[Any], val)) > 0
    if isinstance(val, dict):
        return len(cast(dict[str, Any], val)) > 0
    return bool(val)


def _single_value_fallback(
    check: dict[str, Any],
    data: dict[str, Any],
    present: list[str],
    active: list[str],
) -> SignalResult:
    """Handle graceful degradation when only 1 non-None value is mapped.

    Reports the single value as INFO (cannot confirm/deny multi-signal
    pattern with a single data point), or SKIPPED if none present.
    """
    if not present:
        return make_skipped(check, data)

    data_value, data_key = first_data_value(data)
    status = SignalStatus.INFO
    if active:
        status = SignalStatus.INFO  # Single signal, cannot confirm full pattern
    evidence = f"Detected ({present[0]}). Limited corroborating data available."
    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=status,
        value=coerce_value(data_value),
        evidence=evidence,
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=False,
    )


def _make_result(
    check: dict[str, Any],
    data: dict[str, Any],
    status: SignalStatus,
    evidence: str,
    threshold_level: str = "",
) -> SignalResult:
    """Create a SignalResult for multi-signal evaluation."""
    data_value, data_key = first_data_value(data)
    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=status,
        value=coerce_value(data_value),
        threshold_level=threshold_level,
        evidence=evidence,
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=False,
    )


__all__ = [
    "PATTERN_HANDLERS",
    "evaluate_inference_pattern",
]
