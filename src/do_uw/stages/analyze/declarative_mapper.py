"""Declarative field resolution for signal data mapping.

Provides dotted-path traversal and field registry resolution for
signal data requirements.

Key features:
- resolve_path(): Dotted-path traversal with SourcedValue auto-unwrap
- resolve_field(): DIRECT_LOOKUP via path + optional key, COMPUTED via dispatch

SourcedValue detection uses duck-typing (hasattr checks for value/source/
confidence) rather than isinstance -- Pydantic generics fail isinstance at
runtime. This matches the established _safe_sourced() pattern.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.field_registry import (
    FieldRegistryEntry,
    get_computed_function,
    get_field_entry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SourcedValue detection (duck-typing)
# ---------------------------------------------------------------------------


def _is_sourced_value(obj: Any) -> bool:
    """Check if obj is a SourcedValue-like object via duck typing.

    Cannot use isinstance(obj, SourcedValue) because SourcedValue is
    generic and Pydantic models don't support isinstance checks with
    generics well at runtime. Instead check for the three key attrs.
    """
    return (
        hasattr(obj, "value")
        and hasattr(obj, "source")
        and hasattr(obj, "confidence")
    )


def _unwrap_sourced(obj: Any) -> tuple[Any, str, str]:
    """Unwrap a SourcedValue-like object, extracting source/confidence.

    Returns (inner_value, source_str, confidence_str).
    """
    return obj.value, str(obj.source), str(obj.confidence)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_path(
    dotted_path: str,
    extracted: Any,
    company: Any,
) -> tuple[Any, str, str]:
    """Traverse a dotted path from root object with SourcedValue auto-unwrap.

    Path root dispatch:
    - "extracted.*" -> ExtractedData object
    - "company.*"   -> CompanyProfile object

    At each traversal step, if the current object is a SourcedValue,
    it is unwrapped and source/confidence are captured.

    Args:
        dotted_path: e.g., "extracted.financials.liquidity"
        extracted: ExtractedData instance
        company: CompanyProfile instance (may be None)

    Returns:
        (value, source, confidence) tuple. value is None if path
        cannot be fully resolved.
    """
    parts = dotted_path.split(".")
    if len(parts) < 2:
        return None, "", ""

    root_name = parts[0]
    segments = parts[1:]

    # Select root object
    if root_name == "extracted":
        obj: Any = extracted
    elif root_name == "company":
        obj = company
    else:
        return None, "", ""

    source = ""
    confidence = ""

    # Traverse each segment
    for segment in segments:
        if obj is None:
            return None, "", ""

        # Check if current obj is a SourcedValue -- unwrap before getattr
        if _is_sourced_value(obj):
            obj, source, confidence = _unwrap_sourced(obj)

        # Navigate to next attribute
        obj = getattr(obj, segment, None)

    # Final unwrap if terminal is SourcedValue
    if obj is not None and _is_sourced_value(obj):
        obj, source, confidence = _unwrap_sourced(obj)

    return obj, source, confidence


# ---------------------------------------------------------------------------
# Field resolution
# ---------------------------------------------------------------------------


def resolve_field(
    field_key: str,
    extracted: Any,
    company: Any,
) -> tuple[Any, str, str]:
    """Resolve a field_key to its value, source, and confidence.

    Looks up field_key in the field registry. For DIRECT_LOOKUP, traverses
    the dotted path and optionally extracts a dict sub-key. For COMPUTED,
    resolves all arg paths and dispatches to the named function.

    Args:
        field_key: Logical field name (e.g., "current_ratio")
        extracted: ExtractedData instance
        company: CompanyProfile instance (may be None)

    Returns:
        (value, source, confidence) tuple.
        value is None if field not found or data missing.
    """
    entry = get_field_entry(field_key)
    if entry is None:
        return None, "", ""

    if entry.type == "DIRECT_LOOKUP":
        return _resolve_direct_lookup(entry, extracted, company)
    if entry.type == "COMPUTED":
        return _resolve_computed(entry, extracted, company)

    return None, "", ""


def _resolve_direct_lookup(
    entry: FieldRegistryEntry,
    extracted: Any,
    company: Any,
) -> tuple[Any, str, str]:
    """Resolve a DIRECT_LOOKUP field via dotted-path traversal.

    If entry.key is set, extracts a sub-key from the resolved dict value.
    This handles SourcedValue[dict] fields like liquidity -> current_ratio.
    """
    assert entry.path is not None  # validated by Pydantic

    value, source, confidence = resolve_path(entry.path, extracted, company)

    # Extract sub-key from dict if specified
    if entry.key and isinstance(value, dict):
        value = value.get(entry.key)

    return value, source, confidence


def _resolve_computed(
    entry: FieldRegistryEntry,
    extracted: Any,
    company: Any,
) -> tuple[Any, str, str]:
    """Resolve a COMPUTED field by calling named function with resolved args.

    Each arg path is resolved via resolve_path. The function receives
    the resolved values (not paths). Source/confidence are propagated
    from the last non-empty arg source.
    """
    assert entry.function is not None  # validated by Pydantic

    func = get_computed_function(entry.function)
    if func is None:
        logger.warning("Unknown computed function: %s", entry.function)
        return None, "", ""

    resolved_args: list[Any] = []
    source = ""
    confidence = ""

    for arg_path in entry.args:
        val, src, conf = resolve_path(arg_path, extracted, company)
        resolved_args.append(val)
        if src:
            source = src  # Last non-empty source wins
        if conf:
            confidence = conf

    try:
        result = func(*resolved_args)
    except Exception:
        logger.exception("Computed function %s failed", entry.function)
        return None, "", ""

    return result, source, confidence


__all__ = [
    "resolve_field",
    "resolve_path",
]
