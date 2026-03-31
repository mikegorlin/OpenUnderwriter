"""PDF renderer for D&O underwriting worksheet.

Renders the worksheet as a PDF using WeasyPrint (optional dependency).
If WeasyPrint is not installed, gracefully skips PDF generation with
a warning log. Uses an HTML/CSS template with Angry Dolphin branding.

Charts are embedded as base64-encoded PNG images in the HTML.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import jinja2

from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
)
from do_uw.stages.render.context_builders import dim_display_name

logger = logging.getLogger(__name__)

# Template directory relative to this package
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "pdf"

# Zone-to-CSS-class mapping for distress indicator conditional formatting.
# Maps common zone labels from scoring models to risk CSS classes.
_ZONE_CLASS_MAP: dict[str, str] = {
    "distress": "critical",
    "danger": "critical",
    "grey": "elevated",
    "gray": "elevated",
    "warning": "elevated",
    "caution": "elevated",
    "manipulation likely": "critical",
    "manipulation unlikely": "low",
    "safe": "low",
    "strong": "low",
    "moderate": "moderate",
    "weak": "elevated",
    "n/a": "",
}


def _risk_class(zone: str) -> str:
    """Jinja2 filter: map a distress zone label to a CSS risk class name.

    Returns one of: critical, elevated, moderate, low, or empty string.
    Used in template as ``risk-{{ zone|lower|risk_class }}``.
    """
    return _ZONE_CLASS_MAP.get(zone.strip().lower(), "") if zone else ""


def _load_chart_images(
    chart_dir: Path | None,
) -> dict[str, str]:
    """Load chart images from disk and encode as base64.

    Returns a dict mapping chart name to base64-encoded PNG string.
    """
    images: dict[str, str] = {}
    if chart_dir is None or not chart_dir.exists():
        return images

    # Load ALL PNG files in chart directory — don't hardcode names
    chart_files = {
        p.stem: p.name for p in chart_dir.glob("*.png")
    }

    for name, filename in chart_files.items():
        chart_path = chart_dir / filename
        if chart_path.exists():
            data = chart_path.read_bytes()
            images[name] = base64.b64encode(data).decode("ascii")

    return images


def _build_pdf_context(
    state: AnalysisState,
    chart_dir: Path | None = None,
) -> dict[str, Any]:
    """Build template context for PDF rendering.

    Reuses the same extraction logic as the Markdown renderer.
    """
    from do_uw.stages.render.md_renderer import build_template_context

    context = build_template_context(state, chart_dir)
    context["chart_images"] = _load_chart_images(chart_dir)
    return context


def render_pdf(
    state: AnalysisState,
    output_path: Path,
    ds: DesignSystem,
    chart_dir: Path | None = None,
) -> Path | None:
    """Render the D&O worksheet as a PDF via WeasyPrint.

    WeasyPrint is an optional dependency. If not installed, this
    function logs a warning and returns None without crashing.

    Args:
        state: Complete AnalysisState with all pipeline data.
        output_path: Where to save the .pdf file.
        ds: Design system (used for consistency).
        chart_dir: Optional directory with chart PNG images.

    Returns:
        The output_path if PDF was generated, or None if
        WeasyPrint is not available.
    """
    try:
        from weasyprint import HTML  # type: ignore[import-untyped,import-not-found]
    except ImportError:
        logger.warning(
            "WeasyPrint not installed. Skipping PDF generation. Install with: uv add weasyprint"
        )
        return None

    _ = ds  # Reserved for future PDF styling extensions

    # Set up Jinja2 environment pointing to PDF templates
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
        undefined=jinja2.StrictUndefined,
    )
    env.filters["format_currency"] = format_currency
    env.filters["format_pct"] = format_percentage
    env.filters["na_if_none"] = na_if_none
    env.filters["risk_class"] = _risk_class
    env.filters["dim_display_name"] = dim_display_name

    template = env.get_template("worksheet.html.j2")
    context = _build_pdf_context(state, chart_dir)
    html_content = template.render(**context)

    # Read the CSS stylesheet
    css_path = _TEMPLATE_DIR / "styles.css"
    css_content = ""
    if css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")

    # Inject CSS inline (WeasyPrint resolves relative paths poorly)
    html_with_css = html_content.replace(
        '<link rel="stylesheet" href="styles.css">',
        f"<style>{css_content}</style>",
    )

    # Generate PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_with_css).write_pdf(  # type: ignore[no-untyped-call]
        str(output_path)
    )
    logger.info("Generated PDF: %s", output_path)

    return output_path


__all__ = ["render_pdf"]
