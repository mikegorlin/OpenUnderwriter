"""Numeric and HTML-specific formatters for financial document rendering.

Extracted from formatters.py (Plan 43-03) to keep files under 500 lines.
Provides currency, percentage, adaptive, and YoY HTML formatters.

Backward-compat re-exports are provided in formatters.py so existing
import sites need no changes.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup

_NA_HTML = '<span class="text-gray-400">—</span>'


def format_currency(value: float | None, compact: bool = False) -> str:
    """Format a number as currency.

    Args:
        value: Dollar amount, or None.
        compact: If True, use compact notation ($1.2B, $345M).

    Returns:
        Formatted string like "$1,234,567" or "$1.2B", or "N/A" for None.
    """
    if value is None:
        return "N/A"
    if compact:
        return "$" + _compact_number(value)
    if value < 0:
        return f"-${abs(value):,.0f}"
    return f"${value:,.0f}"


def format_percentage(value: float | None, decimals: int = 1) -> str:
    """Format a number as a percentage.

    Args:
        value: Percentage value (e.g., 12.3 for 12.3%), or None.
        decimals: Number of decimal places.

    Returns:
        Formatted string like "12.3%", or "N/A" for None.
    """
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def format_currency_accounting(
    value: float | None, compact: bool = False,
) -> str:
    """Accounting-style currency formatting for HTML rendering.

    Negative values display as red parentheses: $(1,234).
    Positive values display normally: $1,234 or $394.3B (compact).
    None returns gray italic N/A HTML span.

    Args:
        value: Dollar amount, or None.
        compact: If True, use adaptive precision ($1.2B, $345M).

    Returns:
        HTML string with appropriate styling classes.
    """
    if value is None:
        return Markup(_NA_HTML)
    if value < 0:
        if compact:
            inner = _compact_number(abs(value))
            return Markup(f'<span class="text-risk-red">(${inner})</span>')
        return Markup(f'<span class="text-risk-red">(${abs(value):,.0f})</span>')
    if compact:
        return "$" + _compact_number(value)
    return f"${value:,.0f}"


def format_adaptive(
    value: float | None, unit: str | None = None,
) -> str:
    """Auto-detect and format values with adaptive precision.

    Handles ratios (1.07x), percentages (23.4%), and large numbers
    in B/M/K notation. If unit is specified, uses that format.

    Args:
        value: Numeric value, or None.
        unit: Optional hint -- 'currency', 'pct', 'ratio', or None.

    Returns:
        Formatted string with appropriate notation.
    """
    if value is None:
        return Markup(_NA_HTML)
    if unit == "currency":
        return format_currency_accounting(value, compact=True)
    if unit == "pct":
        return format_percentage(value, 1)
    if unit == "ratio":
        return f"{value:.2f}x"
    # Auto-detect from magnitude
    abs_val = abs(value)
    if abs_val >= 1_000_000:
        return format_currency_accounting(value, compact=True)
    if abs_val < 100 and abs_val != int(abs_val):
        # Small decimal -- likely a ratio
        return f"{value:.2f}x"
    return f"{value:,.1f}"


def format_yoy_html(change_pct: float | None) -> str:
    """Format YoY change as HTML with colored triangle arrow.

    Positive: green up-triangle with +X.X%.
    Negative: red down-triangle with -X.X%.
    Zero/None: gray dashes.

    Uses triangle characters: up &#9650;, down &#9660;.

    Args:
        change_pct: Percentage change value, or None.

    Returns:
        HTML string with colored arrow and change percentage.
    """
    if change_pct is None or change_pct == 0:
        return Markup('<span class="text-gray-400">--</span>')
    if change_pct > 0:
        return Markup(
            f'<span class="text-risk-green">&#9650; +{change_pct:.1f}%</span>'
        )
    return Markup(
        f'<span class="text-risk-red">&#9660; {change_pct:.1f}%</span>'
    )


def format_em_dash(value: object) -> str:
    """Return em dash for None/empty values, otherwise str(value).

    Used in 3-column data grid for CapIQ-style missing data display.
    Leaves existing format_na('N/A') calls unchanged for backward compatibility.
    """
    if value is None or value == "" or value == []:
        return "\u2014"  # em dash
    return str(value)


def _compact_number(value: float) -> str:
    """Convert a number to compact notation.

    Internal helper for format_compact and format_currency(compact=True).
    """
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000_000:.1f}T"
    if abs_val >= 1_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val / 1_000:.1f}K"
    return f"{sign}{abs_val:.0f}"


# ---------------------------------------------------------------------------
# Size spectrum computation for SEC filer universe context
# ---------------------------------------------------------------------------

# Approximate SEC filer universe percentile tiers.
# Source: SEC EDGAR filer statistics (approximate, suitable for v1).
MARKET_CAP_SPECTRUM: list[dict[str, Any]] = [
    {"label": "Nano", "max": 50_000_000, "pct": 15},
    {"label": "Micro", "max": 300_000_000, "pct": 40},
    {"label": "Small", "max": 2_000_000_000, "pct": 65},
    {"label": "Mid", "max": 10_000_000_000, "pct": 85},
    {"label": "Large", "max": 200_000_000_000, "pct": 97},
    {"label": "Mega", "max": float("inf"), "pct": 100},
]

REVENUE_SPECTRUM: list[dict[str, Any]] = [
    {"label": "Pre-Revenue", "max": 1_000_000, "pct": 10},
    {"label": "Micro", "max": 50_000_000, "pct": 30},
    {"label": "Small", "max": 500_000_000, "pct": 55},
    {"label": "Mid", "max": 5_000_000_000, "pct": 80},
    {"label": "Large", "max": 50_000_000_000, "pct": 95},
    {"label": "Mega", "max": float("inf"), "pct": 100},
]

EMPLOYEE_SPECTRUM: list[dict[str, Any]] = [
    {"label": "Startup", "max": 50, "pct": 15},
    {"label": "Small", "max": 500, "pct": 40},
    {"label": "Mid", "max": 5_000, "pct": 65},
    {"label": "Large", "max": 50_000, "pct": 88},
    {"label": "Enterprise", "max": 250_000, "pct": 97},
    {"label": "Mega", "max": float("inf"), "pct": 100},
]

YEARS_PUBLIC_SPECTRUM: list[dict[str, Any]] = [
    {"label": "IPO", "max": 2, "pct": 10},
    {"label": "Young", "max": 5, "pct": 25},
    {"label": "Established", "max": 15, "pct": 55},
    {"label": "Mature", "max": 30, "pct": 80},
    {"label": "Legacy", "max": float("inf"), "pct": 100},
]


def compute_spectrum_position(
    value: float | int | None,
    spectrum: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Compute where a value falls on a spectrum.

    Args:
        value: The numeric value to position.
        spectrum: List of tier dicts with 'label', 'max', 'pct' keys.

    Returns:
        Dict with tier_label, percentile, position_pct (0-100 for bar),
        or None if value is None.
    """
    if value is None:
        return None

    val = float(value)
    for i, tier in enumerate(spectrum):
        if val <= tier["max"]:
            # Interpolate within this tier
            prev_max = spectrum[i - 1]["max"] if i > 0 else 0
            prev_pct = spectrum[i - 1]["pct"] if i > 0 else 0
            tier_pct = tier["pct"]

            # Linear interpolation within tier
            tier_range = tier["max"] - prev_max
            if tier_range > 0 and tier["max"] != float("inf"):
                progress = (val - prev_max) / tier_range
                position = prev_pct + progress * (tier_pct - prev_pct)
            else:
                position = float(prev_pct + tier_pct) / 2

            return {
                "tier_label": tier["label"],
                "percentile": int(round(position)),
                "position_pct": min(max(int(round(position)), 1), 99),
            }

    # Beyond all tiers -- max position
    last = spectrum[-1]
    return {
        "tier_label": last["label"],
        "percentile": last["pct"],
        "position_pct": 99,
    }


__all__: list[str] = [
    "EMPLOYEE_SPECTRUM",
    "MARKET_CAP_SPECTRUM",
    "REVENUE_SPECTRUM",
    "YEARS_PUBLIC_SPECTRUM",
    "compute_spectrum_position",
    "format_adaptive",
    "format_currency",
    "format_currency_accounting",
    "format_em_dash",
    "format_percentage",
    "format_yoy_html",
]
