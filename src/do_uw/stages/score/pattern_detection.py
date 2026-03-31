"""Composite pattern detection engine for D&O underwriting.

Evaluates 19 patterns defined in brain/patterns.json against ExtractedData.
Each pattern has trigger conditions, severity modifiers, and score impacts.

Patterns detect multi-factor risk signals that are more significant than
any individual factor. Examples: EVENT_COLLAPSE (stock + trigger + peers),
DEATH_SPIRAL (price + convertibles + shorts + delisting + cash).

Field value mapping is in pattern_fields.py (split for 500-line limit).
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.company import CompanyProfile
from do_uw.models.scoring import PatternMatch
from do_uw.models.state import ExtractedData
from do_uw.stages.score.pattern_fields import get_pattern_field_value

logger = logging.getLogger(__name__)

# Re-export for backward compat (tests import _get_pattern_field_value)
_get_pattern_field_value = get_pattern_field_value


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def detect_all_patterns(
    patterns_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> list[PatternMatch]:
    """Detect all patterns from patterns.json against extracted data.

    Returns a PatternMatch for every pattern (both detected and not),
    so downstream consumers see the full pattern evaluation.
    """
    patterns = patterns_config.get("patterns", [])
    results: list[PatternMatch] = []
    for pattern_cfg in patterns:
        match = _detect_pattern(pattern_cfg, extracted, company)
        results.append(match)
    return results


# -----------------------------------------------------------------------
# Single pattern detection
# -----------------------------------------------------------------------


def _detect_pattern(
    pattern_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> PatternMatch:
    """Evaluate a single pattern against extracted data.

    Detection logic:
    1. Evaluate each trigger_condition via _evaluate_trigger()
    2. Count matched triggers. Pattern detected when majority (>50%) match.
    3. If detected, compute severity from severity_modifiers.
    4. Compute score_impact from config + severity points.
    """
    pattern_id = str(pattern_config.get("id", ""))
    pattern_name = str(pattern_config.get("name", ""))

    # Get trigger conditions
    triggers = pattern_config.get("trigger_conditions", [])
    if not triggers:
        return PatternMatch(
            pattern_id=pattern_id,
            pattern_name=pattern_name,
            detected=False,
        )

    # Evaluate each trigger
    matched_triggers: list[str] = []
    total_triggers = len(triggers)

    for trigger in triggers:
        if _evaluate_trigger(trigger, extracted, company):
            desc = str(trigger.get("description", trigger.get("field", "")))
            matched_triggers.append(desc)

    # Detection threshold: majority (>50%) of triggers must match
    threshold = total_triggers / 2.0
    detected = len(matched_triggers) > threshold

    if not detected:
        return PatternMatch(
            pattern_id=pattern_id,
            pattern_name=pattern_name,
            detected=False,
            triggers_matched=matched_triggers,
        )

    # Compute severity
    severity, severity_points = _compute_severity(
        pattern_config, matched_triggers, extracted, company
    )

    # Compute score impact
    score_impact = _compute_score_impact(
        pattern_config, severity, severity_points
    )

    return PatternMatch(
        pattern_id=pattern_id,
        pattern_name=pattern_name,
        detected=True,
        severity=severity,
        triggers_matched=matched_triggers,
        score_impact=score_impact,
    )


# -----------------------------------------------------------------------
# Trigger evaluation
# -----------------------------------------------------------------------


def _evaluate_trigger(
    trigger: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> bool:
    """Evaluate a single trigger condition.

    Handles both simple triggers (field/operator/value) and
    compound triggers with "any_of" sub-conditions.

    Missing data causes the trigger to NOT match (returns False),
    never raises an error.
    """
    # Handle "any_of" compound triggers
    any_of = trigger.get("any_of")
    if any_of is not None and isinstance(any_of, list):
        any_of_typed = cast(list[dict[str, Any]], any_of)
        return any(
            _evaluate_simple_trigger(sub, extracted, company)
            for sub in any_of_typed
        )

    return _evaluate_simple_trigger(trigger, extracted, company)


def _evaluate_simple_trigger(
    trigger: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> bool:
    """Evaluate a simple field/operator/value trigger."""
    field_name = trigger.get("field")
    if field_name is None:
        return False

    actual = get_pattern_field_value(str(field_name), extracted, company)
    if actual is None:
        return False

    operator = str(trigger.get("operator", ""))
    expected = trigger.get("value")

    return _apply_operator(operator, actual, expected)


def _apply_operator(operator: str, actual: Any, expected: Any) -> bool:
    """Apply comparison operator between actual and expected values."""
    try:
        if operator == "gt":
            return float(actual) > float(expected)
        if operator == "lt":
            return float(actual) < float(expected)
        if operator == "gte":
            return float(actual) >= float(expected)
        if operator == "lte":
            return float(actual) <= float(expected)
        if operator == "eq":
            # Handle bool comparison carefully
            if isinstance(expected, bool):
                if isinstance(actual, bool):
                    return actual == expected
                return bool(actual) == expected
            return actual == expected
        if operator == "ne":
            return actual != expected
        if operator == "in":
            if isinstance(expected, list):
                return actual in expected
            return False
        if operator == "not_in":
            if isinstance(expected, list):
                return actual not in expected
            return True
    except (ValueError, TypeError):
        return False

    logger.warning("Unknown operator: %s", operator)
    return False


# -----------------------------------------------------------------------
# Severity computation
# -----------------------------------------------------------------------


def _compute_severity(
    pattern_config: dict[str, Any],
    matched_triggers: list[str],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> tuple[str, int]:
    """Evaluate severity modifiers and return (severity_level, points).

    Severity mapping:
    - 0 additional points: BASELINE
    - 1-2 additional points: ELEVATED
    - 3-4 additional points: HIGH
    - 5+ additional points: SEVERE
    """
    modifiers = pattern_config.get("severity_modifiers", [])
    total_points = 0

    for modifier in modifiers:
        field = str(modifier.get("field", ""))
        actual = get_pattern_field_value(field, extracted, company)
        if actual is None:
            continue

        operator = str(modifier.get("operator", ""))
        expected = modifier.get("value")
        points = int(modifier.get("points", 0))

        if _apply_operator(operator, actual, expected):
            total_points += points

    # Also check severity_levels table if present (for patterns that
    # define severity by trigger count)
    severity_levels_raw = pattern_config.get("severity_levels", [])
    severity_levels = cast(list[dict[str, Any]], severity_levels_raw)
    if severity_levels:
        trigger_count = len(matched_triggers)
        for level in severity_levels:
            count_range = level.get("triggers_count_range")
            count_min = level.get("triggers_count_min")
            if count_range is not None:
                range_list = cast(list[int], count_range)
                low, high = range_list
                if low <= trigger_count <= high:
                    level_pts = int(
                        level.get(
                            "points",
                            level.get(
                                "f10_points",
                                level.get("f2_points", 0),
                            ),
                        )
                    )
                    total_points = max(total_points, level_pts)
            elif count_min is not None:
                if trigger_count >= int(count_min):
                    level_pts = int(
                        level.get(
                            "points",
                            level.get(
                                "f10_points",
                                level.get("f2_points", 0),
                            ),
                        )
                    )
                    total_points = max(total_points, level_pts)

    severity = _points_to_severity(total_points)
    return severity, total_points


def _points_to_severity(points: int) -> str:
    """Map severity points to severity level string."""
    if points >= 5:
        return "SEVERE"
    if points >= 3:
        return "HIGH"
    if points >= 1:
        return "ELEVATED"
    return "BASELINE"


# -----------------------------------------------------------------------
# Score impact computation
# -----------------------------------------------------------------------


def _compute_score_impact(
    pattern_config: dict[str, Any],
    severity: str,
    severity_points: int,
) -> dict[str, float]:
    """Compute factor score impact from pattern config.

    Each score_impact entry: {"F2": {"base": 2, "max": 5}}
    Total impact = min(base + severity_points, max).
    """
    impact_cfg = cast(
        dict[str, Any], pattern_config.get("score_impact", {})
    )
    result: dict[str, float] = {}

    for factor_id, cfg in impact_cfg.items():
        if not isinstance(cfg, dict):
            continue
        cfg_dict = cast(dict[str, Any], cfg)
        base = float(cfg_dict.get("base", 0))
        max_val = float(cfg_dict.get("max", base))
        total = min(base + severity_points, max_val)
        result[factor_id] = total

    _ = severity  # Used indirectly via severity_points
    return result
