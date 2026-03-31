"""CSS variable definitions and tier-to-CSS-class mapping for dashboard templates.

Mirrors the Angry Dolphin brand colors from design_system.py as CSS custom
properties, and provides helper functions to map scoring tiers and risk
levels to DaisyUI badge CSS classes.
"""

from __future__ import annotations

# CSS custom properties mirroring design_system.py brand colors
CSS_VARIABLES: dict[str, str] = {
    # Angry Dolphin brand
    "--ad-navy": "#1A1446",
    "--ad-gold": "#FFD000",
    "--ad-text": "#333333",
    "--ad-text-light": "#666666",
    "--ad-white": "#FFFFFF",
    # Risk heat spectrum (NO green -- nothing is "safe" in underwriting)
    "--risk-critical": "#CC0000",
    "--risk-high": "#E67300",
    "--risk-elevated": "#FFB800",
    "--risk-moderate": "#4A90D9",
    "--risk-neutral": "#999999",
    # Conditional formatting backgrounds
    "--fmt-deteriorating": "#FCE8E6",
    "--fmt-caution": "#FFF3CD",
    "--fmt-improving": "#DCEEF8",
}

# DaisyUI badge class mappings for scoring tiers
_TIER_CLASSES: dict[str, str] = {
    "WIN": "badge-info",
    "WANT": "badge-info",
    "WRITE": "badge-warning",
    "WATCH": "badge-warning",
    "WALK": "badge-error",
    "NO_TOUCH": "badge-error",
}

# DaisyUI badge class mappings for risk levels
_RISK_LEVEL_CLASSES: dict[str, str] = {
    "CRITICAL": "badge-error",
    "HIGH": "badge-error",
    "ELEVATED": "badge-warning",
    "MODERATE": "badge-info",
    "LOW": "badge-info",
    "NEUTRAL": "badge-ghost",
}


def tier_to_css_class(tier: str | None) -> str:
    """Map a scoring tier to a DaisyUI badge CSS class.

    Args:
        tier: Scoring tier string (WIN, WANT, WRITE, WATCH, WALK, NO_TOUCH).

    Returns:
        DaisyUI badge class string (e.g., "badge-info", "badge-warning").
    """
    if tier is None:
        return "badge-ghost"
    return _TIER_CLASSES.get(tier.upper(), "badge-ghost")


def risk_level_to_css_class(level: str | None) -> str:
    """Map a risk level to a DaisyUI badge CSS class.

    Args:
        level: Risk level string (CRITICAL, HIGH, ELEVATED, MODERATE, LOW, NEUTRAL).

    Returns:
        DaisyUI badge class string (e.g., "badge-error", "badge-warning").
    """
    if level is None:
        return "badge-ghost"
    return _RISK_LEVEL_CLASSES.get(level.upper(), "badge-ghost")


__all__ = [
    "CSS_VARIABLES",
    "risk_level_to_css_class",
    "tier_to_css_class",
]
