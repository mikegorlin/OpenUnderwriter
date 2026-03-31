"""D&O context template evaluation engine.

Renders brain-YAML-driven D&O commentary templates against signal evaluation
results. Templates use Python str.format_map() with safe missing-key handling.

Key functions:
- render_do_context: Render a single template string against a SignalResult
- apply_do_context: Select + render the appropriate template for a signal
- _select_template: Compound key fallback chain for template selection
- validate_do_context_template: Validate template syntax for brain health/audit

Template variable reference:
  {value}       - Signal result value (str)
  {score}       - Alias for value
  {zone}        - threshold_level (red/yellow/clear)
  {threshold}   - threshold_context text
  {threshold_level} - same as zone
  {evidence}    - Evidence string
  {source}      - Data source
  {confidence}  - Confidence level
  {company}     - Company name
  {ticker}      - Ticker symbol
  {details_*}   - Flattened details dict (e.g., {details_components_profitability})
"""

from __future__ import annotations

import logging
import re
import string
from typing import Any

from do_uw.stages.analyze.signal_results import SignalResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe format dict -- returns "" for missing keys instead of raising KeyError
# ---------------------------------------------------------------------------


class SafeFormatDict(dict):  # type: ignore[type-arg]
    """Dict subclass that returns empty string for missing keys during format_map.

    Prevents KeyError when a template references a variable that doesn't exist
    in the evaluation context.
    """

    def __missing__(self, key: str) -> str:
        logger.debug("do_context template variable not found: %s", key)
        return ""


# ---------------------------------------------------------------------------
# Template selection with compound key fallback
# ---------------------------------------------------------------------------


def _select_template(
    do_context_templates: dict[str, str],
    status: str,
    threshold_level: str,
) -> str:
    """Select the best matching template from do_context dict.

    Fallback chain for TRIGGERED status:
      TRIGGERED_{LEVEL} -> TRIGGERED -> DEFAULT -> ""

    Fallback chain for CLEAR:
      CLEAR -> DEFAULT -> ""

    Fallback chain for INFO:
      INFO -> DEFAULT -> ""

    SKIPPED always returns "" (no D&O context for unevaluated signals).

    Args:
        do_context_templates: Dict of status-keyed templates from brain YAML.
        status: Signal status string (TRIGGERED, CLEAR, INFO, SKIPPED).
        threshold_level: Threshold level hit (red, yellow, etc.) or "".

    Returns:
        Selected template string, or "" if no match found.
    """
    if not do_context_templates:
        return ""

    if status == "SKIPPED":
        return ""

    if status == "TRIGGERED":
        # Try compound key first: TRIGGERED_RED, TRIGGERED_YELLOW, etc.
        if threshold_level:
            compound = f"TRIGGERED_{threshold_level.upper()}"
            if compound in do_context_templates:
                return do_context_templates[compound]
        # Fallback to generic TRIGGERED
        if "TRIGGERED" in do_context_templates:
            return do_context_templates["TRIGGERED"]
        # Final fallback to DEFAULT
        return do_context_templates.get("DEFAULT", "")

    if status == "CLEAR":
        if "CLEAR" in do_context_templates:
            return do_context_templates["CLEAR"]
        return do_context_templates.get("DEFAULT", "")

    if status == "INFO":
        if "INFO" in do_context_templates:
            return do_context_templates["INFO"]
        return do_context_templates.get("DEFAULT", "")

    # Unknown status -- try DEFAULT
    return do_context_templates.get("DEFAULT", "")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def _flatten_details(details: dict[str, Any], prefix: str = "details") -> dict[str, str]:
    """Flatten a nested details dict into underscore-joined string keys.

    Example: {"components": {"profitability": 0.75}}
    -> {"details_components_profitability": "0.75"}
    """
    result: dict[str, str] = {}
    for key, val in details.items():
        flat_key = f"{prefix}_{key}"
        if isinstance(val, dict):
            result.update(_flatten_details(val, flat_key))
        else:
            result[flat_key] = str(val) if val is not None else ""
    return result


def render_do_context(
    template: str,
    signal_result: SignalResult,
    company_name: str = "",
    ticker: str = "",
) -> str:
    """Render a do_context template string against a SignalResult.

    Uses SafeFormatDict so missing variables render as "" instead of crashing.

    Args:
        template: Template string with {variable} placeholders.
        signal_result: The evaluated SignalResult providing variable values.
        company_name: Company name for {company} variable.
        ticker: Ticker symbol for {ticker} variable.

    Returns:
        Rendered string. Empty string on any formatting error.
    """
    if not template:
        return ""

    # Build variables dict -- format floats for human readability
    raw_value = signal_result.value
    if isinstance(raw_value, float) and raw_value == int(raw_value):
        value_str = str(int(raw_value))
    elif isinstance(raw_value, float):
        # Round to 2 decimal places for human readability (e.g., 61.54 not 61.53846153846154)
        value_str = f"{raw_value:.2f}".rstrip("0").rstrip(".")
    elif raw_value is not None:
        value_str = str(raw_value)
    else:
        value_str = ""
    variables = SafeFormatDict({
        "value": value_str,
        "score": value_str,
        "zone": signal_result.threshold_level,
        "threshold": signal_result.threshold_context,
        "threshold_level": signal_result.threshold_level,
        "evidence": signal_result.evidence,
        "source": signal_result.source,
        "confidence": signal_result.confidence,
        "company": company_name,
        "ticker": ticker,
    })

    # Flatten details dict
    if signal_result.details:
        variables.update(_flatten_details(signal_result.details))

    try:
        return template.format_map(variables)
    except (ValueError, KeyError, IndexError) as exc:
        logger.warning("do_context template render error: %s (template: %s)", exc, template)
        return ""


# ---------------------------------------------------------------------------
# Pipeline integration: apply do_context to a SignalResult
# ---------------------------------------------------------------------------


def apply_do_context(
    result: SignalResult,
    sig: dict[str, Any],
    company_name: str = "",
    ticker: str = "",
) -> SignalResult:
    """Select and render do_context template for a signal, populating result.do_context.

    Reads presentation.do_context from the signal config dict, selects the
    appropriate template based on result status and threshold level, renders
    it with signal result data, and sets result.do_context.

    Args:
        result: SignalResult to enrich with do_context.
        sig: Signal config dict from brain YAML.
        company_name: Company name for template variables.
        ticker: Ticker symbol for template variables.

    Returns:
        The same SignalResult with do_context populated (or left as "").
    """
    presentation = sig.get("presentation")
    if presentation is None:
        return result

    if isinstance(presentation, dict):
        do_context_templates = presentation.get("do_context", {})
    else:
        # PresentationSpec Pydantic model
        do_context_templates = getattr(presentation, "do_context", {})

    if not do_context_templates:
        return result

    template = _select_template(
        do_context_templates,
        result.status.value,
        result.threshold_level,
    )
    if not template:
        return result

    rendered = render_do_context(template, result, company_name, ticker)
    result.do_context = rendered
    return result


# ---------------------------------------------------------------------------
# Template validation for brain health/audit
# ---------------------------------------------------------------------------

# Known valid top-level variable names
_KNOWN_VARIABLES = frozenset({
    "value", "score", "zone", "threshold", "threshold_level",
    "evidence", "source", "confidence", "company", "ticker",
})


def validate_do_context_template(template: str) -> list[str]:
    """Validate a do_context template string for syntax errors.

    Checks:
    1. Balanced braces (no unclosed { or })
    2. Valid variable references (known names or details_* pattern)

    Args:
        template: Template string to validate.

    Returns:
        List of error/warning strings. Empty list = valid template.
    """
    if not template:
        return []

    errors: list[str] = []

    # Check for formatting errors by attempting a test render
    try:
        # Use a dict that returns "" for all keys to test syntax
        test_dict = SafeFormatDict()
        template.format_map(test_dict)
    except (ValueError, KeyError, IndexError) as exc:
        errors.append(f"Template format error: {exc}")
        return errors  # Can't parse further if format is broken

    # Extract variable names from template
    # Match {name} but not {{escaped}} -- use string.Formatter for robustness
    formatter = string.Formatter()
    try:
        parsed_fields = list(formatter.parse(template))
    except (ValueError, KeyError) as exc:
        errors.append(f"Template parse error: {exc}")
        return errors

    for _, field_name, _, _ in parsed_fields:
        if field_name is None:
            continue
        # Strip any format spec or conversion
        base_name = field_name.split(".")[0].split("[")[0]
        if not base_name:
            continue
        # details_* pattern is always valid
        if base_name.startswith("details_"):
            continue
        if base_name not in _KNOWN_VARIABLES:
            errors.append(f"Unknown variable '{base_name}' (known: {', '.join(sorted(_KNOWN_VARIABLES))})")

    return errors


__all__ = [
    "SafeFormatDict",
    "_select_template",
    "apply_do_context",
    "render_do_context",
    "validate_do_context_template",
]
