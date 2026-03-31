"""Generic YAML-driven signal field resolver.

Replaces ~3,000 lines of hardcoded prefix-based routing (signal_mappers*.py)
with a generic resolver that reads field path declarations directly from
signal YAML and resolves them against the AnalysisState.

Resolution priority for each signal:
1. acquisition.sources[*].fields[*] (v7.0 YAML paths: path, computed_from, fallback_paths)
2. field_path (legacy direct field key)
3. data_strategy.field_key (legacy strategy key)

Phase 111-03: Initial implementation with phased migration (resolver primary,
old mapper fallback in signal_engine.py).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def resolve_signal_data(
    sig: dict[str, Any],
    state: AnalysisState,
) -> dict[str, Any]:
    """Resolve signal data from YAML field declarations against state.

    Reads the signal's acquisition block and resolves declared field paths
    against the live AnalysisState. Returns a dict keyed by field name
    with resolved values (same contract as map_signal_data).

    Resolution priority:
    1. acquisition.sources[*].fields[*].path (v7.0 YAML direct paths)
    2. acquisition.sources[*].fields[*].computed_from (analysis-stage outputs)
    3. acquisition.sources[*].fields[*].fallback_paths (ordered alternatives)
    4. field_path (legacy direct field key)
    5. data_strategy.field_key (legacy strategy key)

    Args:
        sig: Signal config dict from brain YAML.
        state: The AnalysisState populated by the pipeline.

    Returns:
        Dict keyed by field name with resolved values. Empty dict if
        no data could be resolved from any declared path.
    """
    result: dict[str, Any] = {}

    # Priority 1-3: v7.0 acquisition block
    acquisition = sig.get("acquisition")
    if isinstance(acquisition, dict):
        sources = acquisition.get("sources")
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                fields = source.get("fields")
                if not isinstance(fields, list):
                    continue
                for field_spec in fields:
                    if not isinstance(field_spec, dict):
                        continue
                    _resolve_field_spec(field_spec, state, result)

    # If acquisition block resolved data, return it
    if result:
        return result

    # Priority 4: field_path (legacy)
    field_path = sig.get("field_path")
    if isinstance(field_path, str) and field_path:
        value = _resolve_path(state, field_path)
        if value is not None:
            # Use the last segment as the key name
            key = field_path.rsplit(".", 1)[-1] if "." in field_path else field_path
            result[key] = value
            return result

    # Priority 5: data_strategy.field_key (legacy)
    ds = sig.get("data_strategy")
    if isinstance(ds, dict):
        field_key = ds.get("field_key")
        if isinstance(field_key, str) and field_key:
            # field_key may be a dotted state path (e.g., "extracted.market.stock.volatility_90d")
            # or a plain key name (e.g., "xbrl_current_ratio" — for use with mapper)
            value = _resolve_path(state, field_key)
            if value is not None:
                key = field_key.rsplit(".", 1)[-1] if "." in field_key else field_key
                result[key] = value
                return result

    return result


def _resolve_field_spec(
    field_spec: dict[str, Any],
    state: Any,
    result: dict[str, Any],
) -> None:
    """Resolve a single field specification from YAML acquisition block.

    Tries path, then computed_from, then fallback_paths in order.
    Writes resolved value into result dict keyed by field name.
    """
    name = field_spec.get("name", "")
    if not name:
        # If no name, try to derive from path
        path = field_spec.get("path") or field_spec.get("computed_from") or ""
        name = path.rsplit(".", 1)[-1] if "." in path else path
    if not name:
        return

    # Try primary path
    path = field_spec.get("path")
    if isinstance(path, str) and path:
        value = _resolve_path(state, path)
        if value is not None:
            result[name] = value
            return

    # Try computed_from
    computed = field_spec.get("computed_from")
    if isinstance(computed, str) and computed:
        value = _resolve_path(state, computed)
        if value is not None:
            result[name] = value
            return

    # Try fallback_paths in order
    fallbacks = field_spec.get("fallback_paths")
    if isinstance(fallbacks, list):
        for fb_path in fallbacks:
            if isinstance(fb_path, str) and fb_path:
                value = _resolve_path(state, fb_path)
                if value is not None:
                    result[name] = value
                    return


def _resolve_path(obj: Any, path: str) -> Any:
    """Traverse a dotted path on an object, unwrapping SourcedValues.

    Handles both dict access (obj.get(part)) and attribute access
    (getattr(obj, part)) at each path segment. Automatically unwraps
    SourcedValue wrappers (objects with both .value and .source attributes).

    Args:
        obj: Root object to traverse from (typically AnalysisState).
        path: Dot-separated path string (e.g., "extracted.governance.board.size").

    Returns:
        The resolved value, or None if any segment is missing.
    """
    parts = path.split(".")
    current = obj

    for part in parts:
        if current is None:
            return None

        # Try dict access first (for actual dicts and dict-like objects)
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)

        # Unwrap SourcedValue: check for .value + .source attributes
        # (not on dicts, strings, numbers, lists)
        if current is not None and _is_sourced_value(current):
            current = current.value

    return current


def _is_sourced_value(obj: Any) -> bool:
    """Check if an object is a SourcedValue wrapper.

    SourcedValue has both .value and .source attributes and is not a
    primitive type (dict, str, int, float, list, bool, type(None)).
    """
    if isinstance(obj, (dict, str, int, float, list, bool, type(None))):
        return False
    return hasattr(obj, "value") and hasattr(obj, "source")


__all__ = [
    "_resolve_path",
    "resolve_signal_data",
]
