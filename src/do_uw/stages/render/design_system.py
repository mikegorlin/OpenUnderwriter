"""Design system for D&O underwriting worksheet documents.

Defines visual constants: Angry Dolphin brand colors, risk heat spectrum
(no green -- nothing is "safe" in underwriting), typography, and layout.
Also provides custom paragraph style setup and matplotlib configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib
from docx.shared import Inches, Pt, RGBColor  # type: ignore[import-untyped]


@dataclass(frozen=True)
class DesignSystem:
    """Frozen visual constants for document rendering.

    All colors, fonts, sizes, and layout measurements in one place.
    Ensures visual consistency across all section renderers.
    """

    # --- Angry Dolphin brand colors (RGBColor for python-docx) ---
    color_primary: RGBColor = RGBColor(0x1A, 0x14, 0x46)  # AD Navy #1A1446
    color_accent: RGBColor = RGBColor(0xFF, 0xD0, 0x00)  # AD Gold #FFD000
    color_text: RGBColor = RGBColor(0x33, 0x33, 0x33)  # Near-black body text
    color_text_light: RGBColor = RGBColor(0x66, 0x66, 0x66)  # Gray secondary text
    color_white: RGBColor = RGBColor(0xFF, 0xFF, 0xFF)  # White

    # --- Risk heat spectrum (NO green -- nothing is "safe" in underwriting) ---
    risk_critical: str = "#CC0000"  # Dark red
    risk_high: str = "#E67300"  # Orange
    risk_elevated: str = "#FFB800"  # Amber/yellow
    risk_moderate: str = "#4A90D9"  # Blue (low end of risk)
    risk_neutral: str = "#999999"  # Gray (no data / not applicable)

    # --- Table colors (hex strings for XML shading, no '#' prefix) ---
    header_bg: str = "1A1446"  # Navy header matching primary
    header_text: str = "FFFFFF"  # White header text
    row_alt: str = "F2F4F8"  # Light gray-blue alternating rows
    highlight_bad: str = "FCE8E6"  # Light red for deteriorating
    highlight_warn: str = "FFF3CD"  # Light amber for caution
    highlight_good: str = "DCEEF8"  # Light blue for improving (NOT green)

    # --- Typography ---
    font_heading: str = "Georgia"  # Serif for headings (close to Perpetua)
    font_body: str = "Calibri"  # Sans-serif for body/tables
    font_mono: str = "Consolas"  # Monospace for data citations

    # --- Font sizes ---
    size_heading1: Pt = Pt(20)
    size_heading2: Pt = Pt(14)
    size_heading3: Pt = Pt(12)
    size_body: Pt = Pt(10)
    size_small: Pt = Pt(8)
    size_caption: Pt = Pt(9)

    # --- Layout ---
    page_margin: Inches = Inches(0.75)
    chart_width: Inches = Inches(6.5)
    chart_dpi: int = 200

    # --- HTML/PDF Bloomberg-inspired palette (hex strings) ---
    # Single source of truth for the HTML/PDF pipeline.
    # Does not affect the Word renderer (which uses python-docx RGBColor above).
    # IMPORTANT: These values MUST match the @theme block in
    # src/do_uw/templates/html/input.css. If you change a color here,
    # update input.css and run: bash scripts/build-css.sh --embed
    html_navy: str = "#0B1D3A"
    html_gold: str = "#D4A843"
    html_risk_critical: str = "#DC2626"
    html_risk_elevated: str = "#EA580C"
    html_risk_watch: str = "#EAB308"
    html_risk_positive: str = "#2563EB"
    html_neutral_gray: str = "#6B7280"
    html_bg_alt: str = "#F8FAFC"

    # Backward-compat aliases
    html_risk_red: str = "#DC2626"
    html_caution_amber: str = "#EA580C"
    html_positive_blue: str = "#2563EB"


# Risk level to hex color mapping — Phase 124 updated
_RISK_COLORS: dict[str, str] = {
    "CRITICAL": "#DC2626",
    "HIGH": "#EA580C",
    "ELEVATED": "#EAB308",
    "MODERATE": "#2563EB",
    "LOW": "#2563EB",
    "NEUTRAL": "#999999",
}

# Bloomberg Terminal GP-inspired colors for dark chart background.
# Used by stock_charts.py for the Bloomberg dark theme charts.
BLOOMBERG_DARK: dict[str, str] = {
    "bg": "#1B1B1D",
    "grid": "#2A2A2C",
    "text": "#D4D4D6",
    "text_muted": "#8E8E90",
    "price_up": "#00C853",
    "price_down": "#FF1744",
    "fill_up_alpha": "#00C85333",
    "fill_down_alpha": "#FF174433",
    "etf_line": "#FFD700",
    "spy_line": "#4FC3F7",
    "divergence_alpha": "#FFD70020",
    "drop_yellow": "#FFEB3B",
    "drop_red": "#FF1744",
    "header_bg": "#252527",
    "header_text": "#FFFFFF",
    "volume_normal": "#555555",
    "volume_spike": "#FF1744",
    "earnings_line": "#666666",
    "earnings_text_pos": "#00C853",
    "earnings_text_neg": "#FF1744",
    "earnings_text_neutral": "#888888",
    "litigation_line": "#FF6D00",
    "litigation_text": "#FF6D00",
    "class_period_shade": "#FF1744",
    "class_period_label": "#991B1B",
}


def get_risk_color(level: str) -> str:
    """Map a risk level string to its hex color.

    Args:
        level: Risk level (CRITICAL, HIGH, ELEVATED, MODERATE, LOW, NEUTRAL).

    Returns:
        Hex color string (e.g., "#CC0000").
    """
    return _RISK_COLORS.get(level.upper(), "#999999")


def setup_styles(doc: Any) -> None:
    """Create custom paragraph styles on a Document.

    Registers DOHeading1-3, DOBody, DOCaption, and DOCitation
    styles with Angry Dolphin branding.

    Args:
        doc: The python-docx Document to add styles to.
    """
    ds = DesignSystem()
    styles: Any = doc.styles

    # DOHeading1: Large serif navy heading with generous spacing
    h1_style: Any = styles.add_style("DOHeading1", 1)  # 1 = paragraph
    h1_style.font.name = ds.font_heading
    h1_style.font.size = ds.size_heading1
    h1_style.font.color.rgb = ds.color_primary
    h1_style.font.bold = True
    h1_style.paragraph_format.space_before = Pt(24)
    h1_style.paragraph_format.space_after = Pt(8)
    h1_style.paragraph_format.keep_with_next = True

    # DOHeading2: Medium serif navy heading
    h2_style: Any = styles.add_style("DOHeading2", 1)
    h2_style.font.name = ds.font_heading
    h2_style.font.size = ds.size_heading2
    h2_style.font.color.rgb = ds.color_primary
    h2_style.font.bold = True
    h2_style.paragraph_format.space_before = Pt(14)
    h2_style.paragraph_format.space_after = Pt(4)
    h2_style.paragraph_format.keep_with_next = True

    # DOHeading3: Small serif navy heading
    h3_style: Any = styles.add_style("DOHeading3", 1)
    h3_style.font.name = ds.font_heading
    h3_style.font.size = ds.size_heading3
    h3_style.font.color.rgb = ds.color_primary
    h3_style.font.bold = True
    h3_style.paragraph_format.space_before = Pt(10)
    h3_style.paragraph_format.space_after = Pt(3)
    h3_style.paragraph_format.keep_with_next = True

    # DOBody: Standard body text
    body_style: Any = styles.add_style("DOBody", 1)
    body_style.font.name = ds.font_body
    body_style.font.size = ds.size_body
    body_style.font.color.rgb = ds.color_text
    body_style.paragraph_format.space_after = Pt(4)

    # DOCaption: Small gray text for chart captions
    caption_style: Any = styles.add_style("DOCaption", 1)
    caption_style.font.name = ds.font_body
    caption_style.font.size = ds.size_caption
    caption_style.font.color.rgb = ds.color_text_light
    caption_style.paragraph_format.space_before = Pt(2)
    caption_style.paragraph_format.space_after = Pt(6)

    # DOCitation: Monospace small gray for data source citations
    cite_style: Any = styles.add_style("DOCitation", 1)
    cite_style.font.name = ds.font_mono
    cite_style.font.size = ds.size_small
    cite_style.font.color.rgb = ds.color_text_light
    cite_style.paragraph_format.space_after = Pt(2)


def configure_matplotlib_defaults() -> None:
    """Set matplotlib to non-interactive Agg backend with brand defaults.

    Call once at render stage startup. Sets font, DPI, and backend
    for headless chart generation.
    """
    matplotlib.use("Agg")

    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Calibri", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "figure.dpi": 200,
            "savefig.dpi": 200,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#CCCCCC",
            "grid.color": "#E0E0E0",
            "grid.linewidth": 0.5,
        }
    )


# Light-themed chart colors for PDF rendering on white background.
# Used by chart generators when producing charts for PDF output --
# dark-background Bloomberg charts would clash with white PDF pages.
CREDIT_REPORT_LIGHT: dict[str, str] = {
    "bg": "#FFFFFF",
    "grid": "#E5E7EB",
    "text": "#1F2937",
    "text_muted": "#6B7280",
    "price_up": "#16A34A",        # Green for positive (per LOCKED decision: green for up)
    "price_down": "#B91C1C",      # Risk red for negative
    "fill_up_alpha": "#16A34A33",
    "fill_down_alpha": "#B91C1C33",
    "etf_line": "#D4A843",        # Gold for ETF
    "spy_line": "#6B7280",        # Gray for SPY
    "divergence_alpha": "#D4A84320",
    "drop_yellow": "#D97706",     # Amber for drops
    "drop_red": "#B91C1C",        # Red for severe drops
    "header_bg": "#0B1D3A",       # Navy
    "header_text": "#FFFFFF",
    "volume_normal": "#CBD5E1",
    "volume_spike": "#B91C1C",
    "earnings_line": "#D1D5DB",
    "earnings_text_pos": "#16A34A",
    "earnings_text_neg": "#B91C1C",
    "earnings_text_neutral": "#9CA3AF",
    "litigation_line": "#C2410C",
    "litigation_text": "#C2410C",
    "class_period_shade": "#B91C1C",
    "class_period_label": "#991B1B",
}


# Unified chart color palette for all chart types (CHART-06).
# Forward-looking unified palette. Does NOT replace CREDIT_REPORT_LIGHT
# or BLOOMBERG_DARK (those remain for backward compat).
CHART_COLORS: dict[str, str] = {
    # Primary palette (institutional, professional)
    "navy": "#0B1D3A",
    "gold": "#D4A843",
    "positive": "#16A34A",      # Green for gains/positive trends
    "negative": "#B91C1C",      # Red for losses/negative trends
    "neutral": "#6B7280",       # Gray for flat/no data
    "accent_blue": "#1D4ED8",   # Blue for secondary data
    "accent_amber": "#D97706",  # Amber for warnings
    # Chart-specific
    "grid": "#E5E7EB",
    "bg": "#FFFFFF",
    "text": "#1F2937",
    "text_muted": "#6B7280",
    # Sparkline-specific
    "sparkline_up": "#16A34A",
    "sparkline_down": "#B91C1C",
    "sparkline_flat": "#6B7280",
    "sparkline_area_up": "#16A34A20",   # 12% alpha
    "sparkline_area_down": "#B91C1C20",
}


__all__ = [
    "BLOOMBERG_DARK",
    "CHART_COLORS",
    "CREDIT_REPORT_LIGHT",
    "DesignSystem",
    "configure_matplotlib_defaults",
    "get_risk_color",
    "setup_styles",
]
