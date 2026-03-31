"""HTML-to-PDF renderer for D&O underwriting worksheet.

Renders the worksheet as a PDF using Playwright headless Chromium for
pixel-perfect Bloomberg-quality output. Falls back to WeasyPrint if
Playwright is not installed.

NOT shared with Word renderer -- per research anti-pattern guidance:
"Do NOT try to share rendering logic between Word and HTML."

Context assembly logic lives in html_context_assembly.py (Phase 114-01 split).
"""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import Any

import jinja2

from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.formatters import (
    format_adaptive,
    format_currency,
    format_currency_accounting,
    format_em_dash,
    format_na,
    format_percentage,
    format_yoy_html,
    clean_narrative_text,
    humanize_check_evidence,
    humanize_enum,
    humanize_field_name,
    humanize_impact,
    humanize_source,
    humanize_theory,
    na_if_none,
    strip_cyber_tags,
    strip_jargon,
    humanize_factor,
)
from do_uw.stages.render.charts.trend_arrows import render_trend_arrow, trend_direction
from do_uw.stages.render.html_narrative import _narratize, _strip_markdown
from do_uw.stages.render.context_builders import dim_display_name
from do_uw.stages.render.output_sanitizer import OutputSanitizer

# Re-export build_html_context for backward compatibility
from do_uw.stages.render.html_context_assembly import (  # noqa: F401
    _risk_class,
    build_html_context,
)
from do_uw.stages.render.html_footnotes import (  # noqa: F401
    FootnoteRegistry,
    build_footnote_registry,
)
from do_uw.stages.render.html_signals import (  # noqa: F401
    _compute_coverage_stats,
    _group_signals_by_section,
)

logger = logging.getLogger(__name__)

# Section cross-reference map: text patterns → (anchor, display label)
_SECTION_LINK_MAP = [
    ("(see Section 6: Litigation)", "#litigation", "Litigation & Regulatory"),
    ("(see Section 3: Financial Health)", "#financial-health", "Financial Health"),
    ("(see Section 5: Governance)", "#governance", "Governance & Leadership"),
    ("(see Section 4: Market & Trading)", "#market", "Market & Trading"),
    ("(see Section 2: Company)", "#company-profile", "Company Profile"),
    ("(see Litigation)", "#litigation", "Litigation & Regulatory"),
    ("(see Financial Health)", "#financial-health", "Financial Health"),
    ("(see Governance)", "#governance", "Governance & Leadership"),
    ("(see Market & Trading)", "#market", "Market & Trading"),
    ("(see Scoring)", "#scoring", "Scoring & Risk Assessment"),
]


def _linkify_sections(text: str) -> str:
    """Convert (see Section X) references into clickable anchor links."""
    if not text:
        return text
    for pattern, anchor, label in _SECTION_LINK_MAP:
        if pattern in text:
            link = f'<a href="{anchor}" class="eb-xref">({label} →)</a>'
            text = text.replace(pattern, link)
    return text


def _format_signal_value(value: Any) -> str:
    """Format a signal value for safe display in tooltips and tables.

    Handles list/dict values (native or stringified) by summarizing
    instead of showing raw repr. Formats floats to 2 decimal places.
    """
    if value is None:
        return "N/A"
    if isinstance(value, list):
        return _format_list_value(value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in list(value.items())[:3])
    if isinstance(value, float):
        return f"{value:.2f}" if value != int(value) else str(int(value))
    # Handle stringified list/dict repr (common from signal results)
    s = str(value)
    if s.startswith("[{") or s.startswith("[None") or s.startswith("[True"):
        import ast
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return _format_list_value(parsed)
        except (ValueError, SyntaxError):
            pass
        # Fallback: truncate the raw string
        return s[:80] + "..." if len(s) > 83 else s
    return s


def _format_list_value(value: list[Any]) -> str:
    """Format a Python list for display."""
    if not value:
        return "[]"
    first = value[0]
    if isinstance(first, dict):
        preview_keys = ["customer", "supplier", "name", "label", "key"]
        preview = None
        for k in preview_keys:
            if k in first:
                preview = str(first[k])[:60]
                break
        if preview is None:
            preview = str(first)[:60]
        if len(value) > 1:
            return f"{preview}... (+{len(value) - 1} more)"
        return preview
    return "; ".join(str(v)[:40] for v in value[:3])


# Template directory for HTML templates
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "html"


def _finalize_value(x: Any) -> Any:
    """Jinja2 finalize function — clean up output values.

    - None, "N/A", "None" → em dash
    - SourcedValue objects → unwrap to .value
    - Jinja2 Undefined → em dash
    - Everything else → pass through
    """
    if x is None or x == "N/A" or x == "None":
        return "—"
    # Handle Jinja2 Undefined (from inline if-expressions without else)
    if isinstance(x, jinja2.Undefined):
        return "—"
    # Unwrap SourcedValue objects that leak into templates
    try:
        if hasattr(x, "value") and hasattr(x, "source") and hasattr(x, "confidence"):
            return x.value if x.value is not None else "—"
    except Exception:
        return x
    return x


def _render_html_template(context: dict[str, Any]) -> str:
    """Render the HTML worksheet from Jinja2 templates.

    Sets up the environment with all required filters and renders
    the worksheet.html.j2 master template.

    Applies section completeness gate pre-render to suppress sections
    with >50% N/A values (GATE-02).
    """
    # Section completeness gate: suppress broken sections before rendering
    try:
        from do_uw.validation.section_completeness import (
            SectionCompletenessGate,
            _KNOWN_SECTION_KEYS,
        )
        SectionCompletenessGate(section_keys=_KNOWN_SECTION_KEYS).apply_banners(context)
    except Exception:
        logger.debug("Section completeness gate skipped", exc_info=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
        undefined=jinja2.Undefined,  # Tolerant of missing vars
        finalize=_finalize_value,
    )

    # Register custom filters
    env.filters["format_currency"] = format_currency
    env.filters["format_pct"] = format_percentage
    env.filters["na_if_none"] = na_if_none
    env.filters["risk_class"] = _risk_class
    env.filters["dim_display_name"] = dim_display_name
    env.filters["zip"] = zip
    # Accounting-style HTML formatters (Plan 40-03)
    env.filters["format_acct"] = format_currency_accounting
    env.filters["format_adaptive"] = format_adaptive
    env.filters["yoy_arrow"] = format_yoy_html
    env.filters["format_na"] = format_na
    # Em dash for None values in 3-column data grid (Plan 43-03)
    env.filters["format_em"] = format_em_dash
    # Enum humanization and markdown stripping (Plan 40-04)
    env.filters["humanize"] = humanize_enum
    env.filters["humanize_source"] = humanize_source
    env.filters["strip_md"] = _strip_markdown
    # Theory code humanization (Plan 40-06)
    env.filters["humanize_theory"] = humanize_theory
    # New display filters (Plan 40-07)
    env.filters["humanize_field"] = humanize_field_name
    env.filters["humanize_impact"] = humanize_impact
    env.filters["humanize_evidence"] = humanize_check_evidence
    env.filters["clean_narrative"] = clean_narrative_text
    env.filters["strip_cyber"] = strip_cyber_tags
    env.filters["strip_jargon"] = strip_jargon
    env.filters["humanize_factor"] = humanize_factor
    # Safe signal value formatting for tooltips/display
    env.filters["format_signal_value"] = _format_signal_value
    # Narrative structuring filter (Unit 2)
    env.filters["narratize"] = _narratize
    # Section cross-reference linkification
    env.filters["linkify_sections"] = _linkify_sections

    # Infographic visualization globals (INFO-04)
    env.globals["trend_arrow"] = render_trend_arrow
    env.globals["trend_dir"] = trend_direction

    template = env.get_template("worksheet.html.j2")
    html = template.render(**context)

    # Post-render jargon sanitization — catches anything that slipped through template filters
    import re as _re

    _JARGON_PATTERNS = [
        (_re.compile(r"<li>\s*Boolean check:\s*True condition met\.?\s*</li>"), ""),
        (_re.compile(r"<li>\s*Boolean check:\s*False condition met\.?\s*</li>"), ""),
        (_re.compile(r"No field_key in data_strategy"), "Data path not configured"),
        (_re.compile(r"Execution mode is MANUAL_ONLY, not AUTO"), "Requires manual review"),
        # Strip yfinance page descriptions from trigger text
        (_re.compile(r"Find the latest[^<]*?stock quote[^<]*?vital information[^<]*?(?=<)"), ""),
    ]
    # Fix Altman Z-Score misclassification: score in grey zone but CLEAR template applied
    # Root cause: signal FIN.ACCT.quality_indicators doesn't evaluate, so do_context uses
    # the CLEAR YAML template for all non-triggered values. Fix by matching the actual score.
    def _fix_altman_zone(m: _re.Match[str]) -> str:
        score_str = m.group(1)
        try:
            score = float(score_str)
        except ValueError:
            return m.group(0)
        if score < 1.81:
            return (f"Altman Z-Score of {score_str} is in the distress zone (below 1.81) "
                    "— historically associated with 2-3x higher D&amp;O claim frequency")
        if score < 2.99:
            return (f"Altman Z-Score of {score_str} is in the grey zone (1.81-2.99) "
                    "— moderate financial stress that could amplify D&amp;O claim severity")
        return m.group(0)  # Actually safe — leave as-is

    html = _re.sub(
        r"Altman Z-Score of (\d+\.\d+) is in the safe zone \(above 2\.99\)",
        _fix_altman_zone,
        html,
    )
    for pattern, replacement in _JARGON_PATTERNS:
        html = pattern.sub(replacement, html)

    # Remove empty tables — prevents blank UI boxes
    # Matches: <table ...> [optional <thead>...</thead>] <tbody></tbody> </table>
    html = _re.sub(
        r'<table[^>]*>\s*(?:<thead>.*?</thead>\s*)?<tbody[^>]*>\s*</tbody>\s*</table>',
        '', html, flags=_re.DOTALL,
    )

    return html


def _optimize_chart_images_for_pdf(context: dict[str, Any]) -> None:
    """Reduce chart image sizes for PDF output.

    Re-encodes base64 PNG chart images at reduced resolution for smaller
    PDF file size. Modifies context["chart_images"] in place.
    Silently skipped if Pillow is not available (graceful degradation).
    """
    try:
        from PIL import Image
    except ImportError:
        return  # Pillow not available, skip optimization

    optimized: dict[str, str] = {}
    for name, b64_data in context.get("chart_images", {}).items():
        if not b64_data:
            optimized[name] = b64_data
            continue
        try:
            img_bytes = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(img_bytes))
            # Resize if width > 800px (sufficient for letter-size PDF)
            if img.width > 800:
                ratio = 800 / img.width
                new_size = (800, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            # Re-encode as optimized PNG
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            optimized[name] = base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception:
            optimized[name] = b64_data  # Keep original on error
    context["chart_images"] = optimized


def _build_pdf_html(
    state: AnalysisState,
    chart_dir: Path | None = None,
) -> str:
    """Build HTML specifically for PDF rendering with pdf_mode=True.

    Sets pdf_mode=True in context so templates can conditionally
    enable PDF-specific elements (running headers/footers, static charts).
    Optimizes chart images for smaller PDF file size.

    Returns:
        Rendered HTML string optimized for print/PDF output.
    """
    context = build_html_context(state, chart_dir)
    context["pdf_mode"] = True
    _optimize_chart_images_for_pdf(context)
    return _render_html_template(context)


def render_html_pdf(
    state: AnalysisState,
    output_path: Path,
    ds: DesignSystem,
    chart_dir: Path | None = None,
) -> Path | None:
    """Render the D&O worksheet as a PDF via Playwright headless Chromium.

    Fallback chain: Playwright -> WeasyPrint -> None.

    Args:
        state: Complete AnalysisState with all pipeline data.
        output_path: Where to save the .pdf file.
        ds: Design system (for consistency reference).
        chart_dir: Optional directory with chart PNG images.

    Returns:
        The output_path if PDF was generated, or None if
        no PDF engine is available.
    """
    _ = ds  # Reserved for future extensions

    # Build browser-view HTML (pdf_mode=False) for review alongside PDF
    browser_context = build_html_context(state, chart_dir)
    browser_html = _render_html_template(browser_context)

    # Post-render sanitization safety net — catches markdown, jargon, debug leaks
    sanitizer = OutputSanitizer.from_defaults()
    browser_html, browser_log = sanitizer.sanitize(browser_html)
    if browser_log.total_substitutions > 0:
        logger.warning(
            "Sanitizer cleaned %d items from browser HTML",
            browser_log.total_substitutions,
        )
        log_path = output_path.with_suffix("").with_name(
            output_path.stem + "_sanitization_log.txt"
        )
        log_path.write_text(browser_log.summary(), encoding="utf-8")
        logger.info("Sanitization log: %s", log_path)

    html_review_path = output_path.with_suffix(".html")
    html_review_path.write_text(browser_html, encoding="utf-8")
    logger.info("Saved HTML for review: %s", html_review_path)

    # Build PDF-specific HTML (pdf_mode=True) with running headers/footers active
    html_content = _build_pdf_html(state, chart_dir)
    html_content, pdf_log = sanitizer.sanitize(html_content)
    if pdf_log.total_substitutions > 0:
        logger.warning(
            "Sanitizer cleaned %d items from PDF HTML",
            pdf_log.total_substitutions,
        )

    # Try Playwright first (primary)
    try:
        from playwright.sync_api import (
            sync_playwright,  # type: ignore[import-untyped,import-not-found]
        )
    except ImportError:
        logger.info(
            "Playwright not installed. Falling back to WeasyPrint for PDF."
        )
        return _fallback_weasyprint(state, output_path, ds, chart_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write HTML to temp file for Playwright
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(html_content)
        html_path = Path(tmp.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                f"file://{html_path}",
                wait_until="load",  # No CDN dependencies -- static CSS is instant
            )
            # Small delay for CSS layout to stabilize before PDF generation
            page.wait_for_timeout(500)

            # Expand all <details> elements for PDF (PDF-06) -- belt-and-suspenders
            # with the template script to ensure they're open before printing
            page.evaluate("document.querySelectorAll('details').forEach(d => d.setAttribute('open', ''))")

            # Wait briefly for DOM updates after details expansion
            page.wait_for_timeout(200)

            page.pdf(
                path=str(output_path),
                format="Letter",
                margin={
                    "top": "0.75in",    # Space for CSS fixed running header
                    "bottom": "0.75in", # Space for CSS fixed running footer + page numbers
                    "left": "0.65in",
                    "right": "0.65in",
                },
                print_background=True,
                # CSS position:fixed handles running header/footer content;
                # Playwright header/footer used ONLY for page numbers
                display_header_footer=True,
                header_template='<span></span>',
                footer_template=(
                    '<div style="font-size:7pt; color:#999; width:100%; '
                    'text-align:center;">'
                    '<span class="pageNumber"></span> / '
                    '<span class="totalPages"></span>'
                    '</div>'
                ),
            )
            browser.close()

        logger.info("Generated PDF via Playwright: %s", output_path)
        return output_path

    except Exception:
        logger.exception(
            "Playwright PDF generation failed. Falling back to WeasyPrint."
        )
        return _fallback_weasyprint(state, output_path, ds, chart_dir)

    finally:
        # Cleanup temp HTML file
        try:
            html_path.unlink(missing_ok=True)
        except OSError:
            pass


def _fallback_weasyprint(
    state: AnalysisState,
    output_path: Path,
    ds: DesignSystem,
    chart_dir: Path | None = None,
) -> Path | None:
    """Attempt PDF generation via WeasyPrint as fallback.

    Returns None if WeasyPrint is also unavailable.
    """
    try:
        from do_uw.stages.render.pdf_renderer import render_pdf

        return render_pdf(state, output_path, ds, chart_dir)
    except Exception:
        logger.warning(
            "WeasyPrint fallback also failed. Skipping PDF generation."
        )
        return None


__all__ = [
    "FootnoteRegistry",
    "_build_pdf_html",
    "_narratize",
    "build_footnote_registry",
    "build_html_context",
    "render_html_pdf",
]
