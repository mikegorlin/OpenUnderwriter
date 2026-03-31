"""Chart style registry -- Pydantic-validated YAML loader for chart styles.

Loads chart_styles.yaml and provides typed access to canonical chart style
definitions. All chart renderers consume these values instead of hardcoding
colors, figure sizes, and axis styling.

Usage:
    from do_uw.stages.render.chart_style_registry import (
        load_chart_styles,
        get_chart_style,
        get_theme_colors,
        resolve_colors,
    )

    style = get_chart_style("stock")
    colors = resolve_colors("stock", "png")  # dark theme for stock PNG
    colors = resolve_colors("stock", "svg")  # always light theme for SVG
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

_STYLES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "config"
    / "chart_styles.yaml"
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ChartStyleDefaults(BaseModel):
    """Default style values shared across all chart types."""

    model_config = ConfigDict(extra="allow")

    dpi: int = 200
    font_family: list[str] = ["Calibri", "Arial", "DejaVu Sans"]
    title_fontsize: int = 12
    title_fontweight: str = "bold"
    title_color: str = "#1A1446"
    label_fontsize: int = 9
    tick_fontsize: int = 8
    legend_fontsize: int = 7
    grid_alpha: float = 0.3
    grid_linewidth: float = 0.5
    spine_linewidth: float = 0.5
    hide_spines: list[str] = ["top", "right"]


class ChartTypeStyle(BaseModel):
    """Style definition for a single chart type family."""

    model_config = ConfigDict(extra="allow")

    theme: str = "light"
    figure_size: list[float] = [10, 6]
    colors: dict[str, Any] = {}
    overlays: dict[str, str] | None = None
    zone_thresholds: dict[str, float] | None = None


class ChartStyleRegistry(BaseModel):
    """Top-level structure of chart_styles.yaml."""

    model_config = ConfigDict(extra="allow")

    defaults: ChartStyleDefaults
    themes: dict[str, dict[str, str]]
    chart_types: dict[str, ChartTypeStyle]


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------

_cache: ChartStyleRegistry | None = None


def load_chart_styles() -> ChartStyleRegistry:
    """Load and validate chart styles from YAML, with caching.

    Returns:
        Validated ChartStyleRegistry.

    Raises:
        FileNotFoundError: If chart_styles.yaml does not exist.
        ValueError: If YAML is empty or invalid.
    """
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache

    text = _STYLES_PATH.read_text()
    raw = yaml.safe_load(text)
    if raw is None:
        msg = f"chart_styles.yaml is empty: {_STYLES_PATH}"
        raise ValueError(msg)

    # Parse chart_types from raw dict into ChartTypeStyle objects
    chart_types_raw: dict[str, Any] = raw.get("chart_types", {})
    chart_types: dict[str, ChartTypeStyle] = {}
    for name, ct_raw in chart_types_raw.items():
        chart_types[name] = ChartTypeStyle(**ct_raw)

    registry = ChartStyleRegistry(
        defaults=ChartStyleDefaults(**raw.get("defaults", {})),
        themes=raw.get("themes", {}),
        chart_types=chart_types,
    )

    _cache = registry
    logger.info("Loaded chart style registry: %d chart types", len(registry.chart_types))
    return registry


def get_chart_style(chart_type: str) -> ChartTypeStyle:
    """Get the style definition for a chart type family.

    Args:
        chart_type: Chart type name (e.g., "stock", "drawdown", "radar").

    Returns:
        ChartTypeStyle with colors, figure_size, theme, etc.

    Raises:
        KeyError: If chart_type is not defined in chart_styles.yaml.
    """
    registry = load_chart_styles()
    if chart_type not in registry.chart_types:
        msg = f"Unknown chart type: {chart_type!r}. Available: {list(registry.chart_types.keys())}"
        raise KeyError(msg)
    return registry.chart_types[chart_type]


def get_theme_colors(theme: str) -> dict[str, str]:
    """Get the full color palette for a theme.

    Args:
        theme: Theme name ("light" or "dark").

    Returns:
        Dict of color name to hex color string.

    Raises:
        KeyError: If theme is not defined.
    """
    registry = load_chart_styles()
    if theme not in registry.themes:
        msg = f"Unknown theme: {theme!r}. Available: {list(registry.themes.keys())}"
        raise KeyError(msg)
    return registry.themes[theme]


def resolve_colors(chart_type: str, format: str = "png") -> dict[str, str]:
    """Resolve the full color dict for a chart type and output format.

    Merges theme base colors with chart-specific color overrides.
    SVG format always uses light theme (for white HTML pages).

    Args:
        chart_type: Chart type name.
        format: Output format ("png", "svg", "pdf").

    Returns:
        Merged color dict ready for use by chart renderers.
    """
    style = get_chart_style(chart_type)

    # SVG always uses light theme (charts embed in white HTML pages)
    if format == "svg":
        theme_name = "light"
    else:
        theme_name = style.theme

    theme_colors = get_theme_colors(theme_name)

    # Start with theme base colors
    merged: dict[str, str] = dict(theme_colors)

    # Overlay chart-specific colors (these override theme defaults)
    for key, value in style.colors.items():
        merged[key] = str(value)

    # Overlay chart-specific overlay colors
    if style.overlays:
        for key, value in style.overlays.items():
            merged[key] = str(value)

    return merged


def reset_cache() -> None:
    """Clear the cached registry (useful for testing)."""
    global _cache  # noqa: PLW0603
    _cache = None


__all__ = [
    "ChartStyleDefaults",
    "ChartStyleRegistry",
    "ChartTypeStyle",
    "get_chart_style",
    "get_theme_colors",
    "load_chart_styles",
    "reset_cache",
    "resolve_colors",
]
