"""Chart type registry -- declarative catalog of all charts.

Loads chart_registry.yaml and provides typed access to chart metadata,
function resolution, and filtering by section/format.

Usage:
    from do_uw.stages.render.chart_registry import (
        load_chart_registry,
        resolve_chart_fn,
        get_charts_for_section,
        get_charts_for_format,
    )

    entries = load_chart_registry()
    for entry in get_charts_for_section("stock_charts"):
        fn = resolve_chart_fn(entry)
        # fn is the callable chart-rendering function
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)

_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "config"
    / "chart_registry.yaml"
)

_REQUIRED_FIELDS = {"id", "name", "module", "function", "formats", "data_requires"}


@dataclass
class ChartEntry:
    """A single chart declaration from the registry."""

    id: str
    name: str
    module: str
    function: str
    formats: list[str]
    data_requires: list[str]
    params: dict[str, Any] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)
    section: str = ""
    position: int = 0
    call_style: str = "standard"
    overlays: list[str] = field(default_factory=list)
    golden_reference: str | None = None


def _load_yaml() -> dict[str, Any]:
    """Load raw YAML data from chart_registry.yaml."""
    text = _REGISTRY_PATH.read_text()
    data = yaml.safe_load(text)
    if data is None:
        msg = f"chart_registry.yaml is empty: {_REGISTRY_PATH}"
        raise ValueError(msg)
    return data


def _validate_and_parse(raw: dict[str, Any]) -> list[ChartEntry]:
    """Validate raw YAML data and parse into ChartEntry objects."""
    charts_raw: list[dict[str, Any]]
    if isinstance(raw, list):
        charts_raw = raw
    else:
        charts_raw = raw.get("charts", [])

    if not charts_raw:
        msg = "chart_registry.yaml contains no chart entries"
        raise ValueError(msg)

    entries: list[ChartEntry] = []
    for idx, chart in enumerate(charts_raw):
        missing = _REQUIRED_FIELDS - chart.keys()
        if missing:
            chart_id = chart.get("id", f"<entry {idx}>")
            msg = f"Chart '{chart_id}' missing required field(s): {', '.join(sorted(missing))}"
            raise ValueError(msg)

        entries.append(
            ChartEntry(
                id=chart["id"],
                name=chart["name"],
                module=chart["module"],
                function=chart["function"],
                formats=chart["formats"],
                data_requires=chart["data_requires"],
                params=chart.get("params") or {},
                signals=chart.get("signals") or [],
                section=chart.get("section", ""),
                position=chart.get("position", 0),
                call_style=chart.get("call_style", "standard"),
                overlays=chart.get("overlays") or [],
                golden_reference=chart.get("golden_reference"),
            )
        )

    return entries


# Module-level cache for lazy singleton load
_cache: list[ChartEntry] | None = None


def load_chart_registry() -> list[ChartEntry]:
    """Load and validate chart registry, returning list of ChartEntry.

    Results are cached after first load. Call with fresh import or
    set ``_cache = None`` to force reload.

    Raises:
        ValueError: If YAML is missing, empty, or entries lack required fields.
        FileNotFoundError: If chart_registry.yaml does not exist.
    """
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache

    raw = _load_yaml()
    entries = _validate_and_parse(raw)
    _cache = entries
    logger.info("Loaded chart registry: %d entries", len(entries))
    return entries


def resolve_chart_fn(entry: ChartEntry) -> Callable[..., Any]:
    """Resolve a ChartEntry to its rendering function callable.

    Uses importlib to dynamically import the module and look up the
    function by name.

    Args:
        entry: A ChartEntry with module and function fields.

    Returns:
        The callable chart-rendering function.

    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the function is not found in the module.
    """
    try:
        mod = importlib.import_module(entry.module)
    except ImportError as exc:
        msg = (
            f"Cannot import module '{entry.module}' for chart '{entry.id}'. "
            f"Check that the module path is correct and the package is installed."
        )
        raise ImportError(msg) from exc

    try:
        fn = getattr(mod, entry.function)
    except AttributeError as exc:
        msg = (
            f"Module '{entry.module}' has no function '{entry.function}' "
            f"for chart '{entry.id}'. Available: {[a for a in dir(mod) if not a.startswith('_')]}"
        )
        raise AttributeError(msg) from exc

    return fn  # type: ignore[no-any-return]


def get_charts_for_section(section: str) -> list[ChartEntry]:
    """Return chart entries for a given template section, sorted by position.

    Args:
        section: The section name (e.g. "stock_charts", "scoring").

    Returns:
        List of ChartEntry objects with matching section, sorted by position.
    """
    entries = load_chart_registry()
    return sorted(
        [e for e in entries if e.section == section],
        key=lambda e: e.position,
    )


def get_charts_for_format(fmt: str) -> list[ChartEntry]:
    """Return chart entries that support a given output format.

    Args:
        fmt: The format string (e.g. "html", "pdf").

    Returns:
        List of ChartEntry objects that include fmt in their formats list.
    """
    entries = load_chart_registry()
    return [e for e in entries if fmt in e.formats]


__all__ = [
    "ChartEntry",
    "get_charts_for_format",
    "get_charts_for_section",
    "load_chart_registry",
    "resolve_chart_fn",
]
