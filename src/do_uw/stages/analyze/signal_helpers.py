"""Shared helpers for check evaluation in the ANALYZE stage.

Contains constants, utility functions, and helper logic used by both
the check engine (dispatcher) and individual evaluators.
"""

from __future__ import annotations

import re
from typing import Any, cast

from do_uw.stages.analyze.signal_results import DataStatus, SignalResult, SignalStatus

# Threshold types that are always INFO (no pass/fail evaluation)
INFO_ONLY_TYPES = frozenset(
    {"info", "pattern", "search", "multi_period", "classification", "display"}
)

# Regex to extract leading numeric value from threshold strings
# Matches patterns like ">25%", "<1.0", ">=50", "$10M", "<-1.78", etc.
NUMERIC_RE = re.compile(
    r"[<>]=?\s*\$?\s*(-?[\d]+(?:\.[\d]+)?)\s*[%MBKmT]?"
)


def extract_factors(check: dict[str, Any]) -> list[str]:
    """Extract factor mapping from check config.

    Looks in check["factors"] first, then falls back to
    check["scoring_impact"]["factors"].
    """
    factors = check.get("factors")
    if isinstance(factors, list):
        typed_factors = cast(list[Any], factors)
        if len(typed_factors) > 0:
            return [str(f) for f in typed_factors]

    scoring_impact = check.get("scoring_impact")
    if isinstance(scoring_impact, dict):
        typed_impact = cast(dict[str, Any], scoring_impact)
        impact_factors = typed_impact.get("factors")
        if isinstance(impact_factors, list):
            typed_impact_factors = cast(list[Any], impact_factors)
            return [str(f) for f in typed_impact_factors]

    return []


def has_numeric_thresholds(threshold: dict[str, Any]) -> bool:
    """Check if threshold has configurable numeric values."""
    for key in ("red", "yellow", "clear"):
        val = threshold.get(key)
        if val is not None and isinstance(val, str):
            if NUMERIC_RE.search(val):
                return True
        if isinstance(val, (int, float)):
            return True
    return False


def extract_first_number(text: str) -> float | None:
    """Extract the first numeric value from a threshold string."""
    match = NUMERIC_RE.search(text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def first_data_value(data: dict[str, Any]) -> tuple[Any, str]:
    """Find the first non-None value in the data dict.

    Returns:
        Tuple of (value, key). value is None if no non-None found.
    """
    for key, val in data.items():
        if val is not None:
            return val, key
    return None, ""


def coerce_value(data_value: Any) -> str | float | None:
    """Coerce a data value to a type SignalResult.value accepts.

    bool MUST be checked before (str, int, float) — isinstance(True, int) == True
    in Python because bool is a subclass of int. Without this guard, True→1.0
    and False→0.0 via Pydantic float coercion, then format_adaptive(1.0) → "1.00".
    """
    if isinstance(data_value, bool):  # bool before int — ORDER MATTERS
        return "True" if data_value else "False"
    if isinstance(data_value, (str, int, float)):
        return data_value
    if data_value is None:
        return None
    return str(data_value)


def make_skipped(
    check: dict[str, Any],
    data: dict[str, Any],
    needs_calibration: bool = False,
) -> SignalResult:
    """Create a SKIPPED result for missing data.

    Always sets data_status=DATA_UNAVAILABLE with a reason describing
    which fields were mapped but had no data.
    """
    reason = (
        "Required data not available from filings"
        if data
        else "Data mapping not configured for this check"
    )
    return SignalResult(
        signal_id=check.get("id", "UNKNOWN"),
        signal_name=check.get("name", ""),
        status=SignalStatus.SKIPPED,
        evidence="Required data not available from filings",
        factors=extract_factors(check),
        section=check.get("section", 0),
        needs_calibration=needs_calibration,
        data_status=DataStatus.DATA_UNAVAILABLE,
        data_status_reason=reason,
    )


def _extract_comparison(text: str) -> tuple[str, float] | None:
    """Extract comparison operator and number from threshold text.

    Finds the first <N or >N pattern and returns the operator and value.
    Handles negative numbers (e.g., ">-1.78") and compound thresholds
    (e.g., "<6 months OR >80%") by using the first operator found.
    """
    match = NUMERIC_RE.search(text)
    if match is None:
        return None
    try:
        num = float(match.group(1))
    except ValueError:
        return None
    full = match.group(0)
    if full.startswith(">"):
        return (">", num)
    if full.startswith("<"):
        return ("<", num)
    return None


def try_numeric_compare(
    data_value: Any,
    threshold: dict[str, Any],
) -> tuple[SignalStatus, str, str] | None:
    """Attempt numeric comparison for tiered/percentage/value/count checks.

    Extracts the comparison operator (< or >) and numeric value from each
    threshold level's text. Handles negative numbers and compound thresholds
    by using the first operator-number pair found in each threshold string.

    Returns:
        Tuple of (status, threshold_level, evidence) or None if
        numeric comparison is not possible.
    """
    if data_value is None:
        return None

    try:
        numeric_val = float(data_value)
    except (ValueError, TypeError):
        return None

    red_str = str(threshold.get("red", ""))
    yellow_str = str(threshold.get("yellow", ""))

    red_cmp = _extract_comparison(red_str)
    yellow_cmp = _extract_comparison(yellow_str)

    if red_cmp is None and yellow_cmp is None:
        return None

    # Check red threshold
    if red_cmp is not None:
        op, red_num = red_cmp
        if op == ">" and numeric_val > red_num:
            return (SignalStatus.TRIGGERED, "red",
                    f"Value {numeric_val} exceeds red threshold {red_num}")
        if op == "<" and numeric_val < red_num:
            return (SignalStatus.TRIGGERED, "red",
                    f"Value {numeric_val} below red threshold {red_num}")

    # Check yellow threshold
    if yellow_cmp is not None:
        op, yellow_num = yellow_cmp
        if op == ">" and numeric_val > yellow_num:
            return (SignalStatus.TRIGGERED, "yellow",
                    f"Value {numeric_val} exceeds yellow threshold {yellow_num}")
        if op == "<" and numeric_val < yellow_num:
            return (SignalStatus.TRIGGERED, "yellow",
                    f"Value {numeric_val} below yellow threshold {yellow_num}")

    return (SignalStatus.CLEAR, "clear",
            f"Value {numeric_val} within thresholds")


__all__ = [
    "INFO_ONLY_TYPES",
    "NUMERIC_RE",
    "_extract_comparison",
    "coerce_value",
    "extract_factors",
    "extract_first_number",
    "first_data_value",
    "has_numeric_thresholds",
    "make_skipped",
    "try_numeric_compare",
]
