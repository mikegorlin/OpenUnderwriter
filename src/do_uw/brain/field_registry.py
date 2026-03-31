"""Field registry loader: maps logical field names to data model paths.

Loads and validates brain/field_registry.yaml, caching the result for
process duration. Used by V2 signals for declarative field resolution
(Phase 55+). Coexists with FIELD_FOR_CHECK dict -- zero legacy deletion.

The registry maps field_key -> dotted_path (e.g., "current_ratio" ->
"extracted.financials.liquidity"). This is a DIFFERENT abstraction from
FIELD_FOR_CHECK which maps signal_id -> field_key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FieldRegistryEntry(BaseModel):
    """A single field registry entry.

    DIRECT_LOOKUP: resolved by dotted-path traversal into the state model.
    COMPUTED: dispatched to a named Python function with arg paths.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["DIRECT_LOOKUP", "COMPUTED"]
    path: str | None = None
    key: str | None = Field(
        default=None,
        description="Sub-key for dict-valued SourcedValue fields",
    )
    function: str | None = None
    args: list[str] = Field(default_factory=list)
    description: str = ""

    @model_validator(mode="after")
    def _validate_type_fields(self) -> FieldRegistryEntry:
        """Ensure DIRECT_LOOKUP has path, COMPUTED has function."""
        if self.type == "DIRECT_LOOKUP":
            if not self.path:
                msg = "DIRECT_LOOKUP entries must have a non-empty 'path'"
                raise ValueError(msg)
        elif self.type == "COMPUTED":
            if not self.function:
                msg = "COMPUTED entries must have a non-empty 'function'"
                raise ValueError(msg)
            if not self.args:
                msg = "COMPUTED entries must have at least one arg"
                raise ValueError(msg)
        return self


class FieldRegistry(BaseModel):
    """Top-level field registry model.

    Validates the entire registry YAML, catching malformed entries
    and unexpected fields via extra='forbid'.
    """

    model_config = ConfigDict(extra="forbid")

    version: int
    fields: dict[str, FieldRegistryEntry]


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------

_REGISTRY_CACHE: FieldRegistry | None = None

_REGISTRY_PATH = Path(__file__).parent / "field_registry.yaml"


def load_field_registry(*, path: Path | None = None) -> FieldRegistry:
    """Load and validate the field registry YAML.

    Reads from brain/field_registry.yaml with CSafeLoader, validates
    with Pydantic FieldRegistry model, and caches the result.

    Args:
        path: Override path for testing. Defaults to the co-located YAML file.

    Returns:
        Validated FieldRegistry instance (cached after first call).
    """
    global _REGISTRY_CACHE  # noqa: PLW0603

    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE

    registry_path = path or _REGISTRY_PATH
    raw = yaml.load(  # noqa: S506
        registry_path.read_text(),
        Loader=yaml.CSafeLoader,
    )
    registry = FieldRegistry.model_validate(raw)
    _REGISTRY_CACHE = registry
    return registry


def get_field_entry(field_key: str) -> FieldRegistryEntry | None:
    """Look up a field registry entry by logical field name.

    Convenience wrapper that loads the registry (cached) and returns
    the entry for the given key, or None if not found.
    """
    registry = load_field_registry()
    return registry.fields.get(field_key)


def get_computed_function(name: str) -> Callable[..., Any] | None:
    """Look up a COMPUTED function by name.

    Lazy import to avoid circular dependencies. Returns None if
    the function name is not registered.
    """
    from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

    return COMPUTED_FUNCTIONS.get(name)


def _reset_cache() -> None:
    """Reset the module-level cache (for testing only)."""
    global _REGISTRY_CACHE  # noqa: PLW0603
    _REGISTRY_CACHE = None


__all__ = [
    "FieldRegistry",
    "FieldRegistryEntry",
    "get_computed_function",
    "get_field_entry",
    "load_field_registry",
]
