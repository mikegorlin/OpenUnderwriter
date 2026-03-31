"""Contextual signal validation engine (Phase 139).

Cross-checks TRIGGERED signals against company state and annotates
potential false positives with explanatory context. NEVER suppresses
or changes signal status -- annotations are informational only.

Rule definitions live in brain/config/validation_rules.yaml. New rules
can be added there without any Python code changes (SIG-07).

Zero signal ID string literals exist in this module (SIG-02).
"""

from __future__ import annotations

import fnmatch
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

RULES_PATH = (
    Path(__file__).parent.parent.parent / "brain" / "config" / "validation_rules.yaml"
)


def _load_validation_rules() -> list[dict[str, Any]]:
    """Load validation rules from YAML file.

    Returns empty list if file does not exist or cannot be parsed.
    """
    if not RULES_PATH.exists():
        logger.debug("Validation rules file not found: %s", RULES_PATH)
        return []
    try:
        with RULES_PATH.open() as f:
            data = yaml.safe_load(f)
        if data is None or "rules" not in data:
            return []
        rules = data["rules"]
        if not isinstance(rules, list):
            return []
        return rules
    except Exception:
        logger.warning("Failed to load validation rules", exc_info=True)
        return []


def _signal_matches_pattern(signal_id: str, pattern: str) -> bool:
    """Check if signal_id matches a pipe-separated fnmatch pattern.

    Supports patterns like:
      "BIZ.EVENT.ipo*"
      "FIN.DISTRESS.*|FIN.LIQ.*|FIN.SOLV.*"
      "*" (match all)
    """
    for sub_pattern in pattern.split("|"):
        if fnmatch.fnmatch(signal_id, sub_pattern.strip()):
            return True
    return False


def _resolve_state_path(state: AnalysisState, path: str) -> Any:
    """Navigate a dotted path on the state object.

    Auto-unwraps SourcedValue objects (objects with a `.value` attribute
    that are not basic types like str, int, float, bool).

    Returns None if any segment in the path resolves to None.
    """
    obj: Any = state
    for segment in path.split("."):
        if obj is None:
            return None
        try:
            obj = getattr(obj, segment)
        except AttributeError:
            return None

    # Auto-unwrap SourcedValue: if obj has .value and is not a basic type
    if (
        obj is not None
        and not isinstance(obj, (str, int, float, bool))
        and hasattr(obj, "value")
    ):
        obj = obj.value

    return obj


def _evaluate_state_check(
    rule: dict[str, Any], state: AnalysisState
) -> str | None:
    """Evaluate a single path/op/value condition against state.

    Returns formatted annotation string or None if condition not met.
    """
    condition = rule["condition"]
    path = condition["path"]
    op = condition["op"]
    expected = condition["value"]

    actual = _resolve_state_path(state, path)
    if actual is None:
        return None

    try:
        actual_num = float(actual)
        expected_num = float(expected)
    except (ValueError, TypeError):
        return None

    passed = False
    if op == ">":
        passed = actual_num > expected_num
    elif op == "<":
        passed = actual_num < expected_num
    elif op == ">=":
        passed = actual_num >= expected_num
    elif op == "<=":
        passed = actual_num <= expected_num
    elif op == "==":
        passed = actual_num == expected_num
    elif op == "empty_or_none":
        passed = actual is None or actual == "" or actual == []

    if not passed:
        return None

    # Format annotation template with resolved value
    # Extract the last segment of the path as variable name
    var_name = path.rsplit(".", 1)[-1]
    template = rule["annotation"]
    try:
        return template.format(**{var_name: actual})
    except (KeyError, IndexError):
        return template


def _evaluate_compound(
    rule: dict[str, Any], state: AnalysisState
) -> str | None:
    """Evaluate compound condition (all sub-conditions must pass).

    Collects resolved values from all sub-conditions for template
    interpolation in the annotation string.
    """
    condition = rule["condition"]
    sub_conditions = condition.get("all", [])
    if not sub_conditions:
        return None

    resolved_values: dict[str, Any] = {}

    for sub in sub_conditions:
        path = sub["path"]
        op = sub["op"]
        expected = sub["value"]
        label = sub.get("label", path.rsplit(".", 1)[-1])

        actual = _resolve_state_path(state, path)
        if actual is None:
            return None

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (ValueError, TypeError):
            return None

        passed = False
        if op == ">":
            passed = actual_num > expected_num
        elif op == "<":
            passed = actual_num < expected_num
        elif op == ">=":
            passed = actual_num >= expected_num
        elif op == "<=":
            passed = actual_num <= expected_num
        elif op == "==":
            passed = actual_num == expected_num

        if not passed:
            return None

        resolved_values[label] = actual

    template = rule["annotation"]
    try:
        return template.format(**resolved_values)
    except (KeyError, IndexError):
        return template


def _evaluate_evidence_regex(
    rule: dict[str, Any], evidence: str
) -> str | None:
    """Match regex patterns against evidence text (case-insensitive).

    Returns annotation on first match.
    """
    if not evidence:
        return None

    condition = rule["condition"]
    patterns = condition.get("patterns", [])

    for pattern in patterns:
        if re.search(pattern, evidence, re.IGNORECASE):
            return rule["annotation"]

    return None


def _evaluate_executive_temporal(
    rule: dict[str, Any], evidence: str, state: AnalysisState
) -> str | None:
    """Check if evidence references a departed executive.

    Gets departures list from state via departure_source path, checks
    if any executive name appears in the evidence text.
    """
    if not evidence:
        return None

    condition = rule["condition"]
    departure_source = condition.get("departure_source", "")
    departures = _resolve_state_path(state, departure_source)

    if not departures or not isinstance(departures, list):
        return None

    evidence_lower = evidence.lower()

    for dep in departures:
        # Extract name from departure profile
        name = None
        if hasattr(dep, "name"):
            name_attr = dep.name
            # SourcedValue unwrap
            if (
                name_attr is not None
                and not isinstance(name_attr, (str, int, float, bool))
                and hasattr(name_attr, "value")
            ):
                name = name_attr.value
            elif isinstance(name_attr, str):
                name = name_attr
        elif isinstance(dep, dict):
            name = dep.get("name")

        if not name:
            continue

        if name.lower() in evidence_lower:
            # Get departure date
            departure_date = ""
            if hasattr(dep, "departure_date"):
                departure_date = dep.departure_date or ""
            elif isinstance(dep, dict):
                departure_date = dep.get("departure_date", "")

            template = rule["annotation"]
            try:
                return template.format(
                    exec_name=name, departure_date=departure_date
                )
            except (KeyError, IndexError):
                return template

    return None


def _evaluate_rule(
    rule: dict[str, Any],
    signal_result: dict[str, Any],
    state: AnalysisState,
) -> str | None:
    """Dispatch rule evaluation by condition type.

    Returns annotation string if rule fires, None otherwise.
    """
    condition = rule.get("condition", {})
    cond_type = condition.get("type", "")
    evidence = signal_result.get("evidence", "")

    if cond_type == "state_check":
        return _evaluate_state_check(rule, state)
    elif cond_type == "compound":
        return _evaluate_compound(rule, state)
    elif cond_type == "evidence_regex":
        return _evaluate_evidence_regex(rule, evidence)
    elif cond_type == "executive_temporal":
        return _evaluate_executive_temporal(rule, evidence, state)
    else:
        logger.warning("Unknown rule condition type: %s", cond_type)
        return None


def validate_signals(
    signal_results: dict[str, dict[str, Any]],
    state: AnalysisState,
) -> dict[str, int]:
    """Main entry point: validate TRIGGERED signals and add annotations.

    Iterates signal_results, skips non-TRIGGERED signals, evaluates all
    matching rules against each TRIGGERED signal, and appends annotation
    strings to the signal's annotations list.

    NEVER modifies signal status, threshold_level, or any other field.
    Only appends to the annotations list.

    Returns:
        Summary dict with keys: rules_evaluated, annotations_added, signals_checked.
    """
    rules = _load_validation_rules()

    rules_evaluated = 0
    annotations_added = 0
    signals_checked = 0

    for signal_id, result in signal_results.items():
        # Only check TRIGGERED signals (efficiency: SIG-01)
        if result.get("status") != "TRIGGERED":
            continue

        signals_checked += 1

        # Ensure annotations list exists
        if "annotations" not in result:
            result["annotations"] = []

        for rule in rules:
            pattern = rule.get("applies_to", "")
            if not _signal_matches_pattern(signal_id, pattern):
                continue

            rules_evaluated += 1
            annotation = _evaluate_rule(rule, result, state)

            if annotation is not None:
                result["annotations"].append(annotation)
                annotations_added += 1

    return {
        "rules_evaluated": rules_evaluated,
        "annotations_added": annotations_added,
        "signals_checked": signals_checked,
    }
