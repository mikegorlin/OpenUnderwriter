"""Render stage: Word, PDF, and Markdown output generation.

Produces the D&O underwriting worksheet in three formats:
- Word (.docx): Primary output with custom styles, charts, tables
- Markdown (.md): Jinja2-templated single-file Markdown (DEPRECATED)
- PDF (.pdf): Playwright HTML-to-PDF (primary), WeasyPrint (fallback)
"""

from __future__ import annotations

import hashlib
import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import (
    DesignSystem,
    configure_matplotlib_defaults,
)
from do_uw.stages.render.html_renderer import render_html_pdf
from do_uw.stages.render.md_renderer import render_markdown
from do_uw.stages.render.pdf_renderer import render_pdf  # noqa: F401 -- WeasyPrint fallback
from do_uw.stages.render.word_renderer import render_word_document


def _get_output_basename(ticker: str) -> str:
    """Generate output filename base with date and version.

    Format: {ticker}_{date}_v{version}_worksheet
    Example: AAPL_20260329_v0.2.0_worksheet
    """
    date_str = datetime.now().strftime("%Y%m%d")
    from do_uw import __version__

    version = __version__.replace(".", "_")  # v0_2_0 for filesystem safety
    return f"{ticker}_{date_str}_v{version}_worksheet"


logger = logging.getLogger(__name__)


class RenderStage:
    """Generate output documents (Word, PDF, Markdown).

    Args:
        output_dir: Directory for output files. If None, defaults to
            output/<TICKER>/ relative to cwd.
        formats: List of output formats to generate. Supported values:
            "html", "word", "pdf", "markdown". Defaults to all formats.
    """

    def __init__(self, output_dir: Path | None = None, formats: list[str] | None = None) -> None:
        self._output_dir = output_dir
        self._formats = formats or ["html", "word", "pdf", "markdown"]

    @property
    def name(self) -> str:
        """Stage name."""
        return "render"

    def validate_input(self, state: AnalysisState) -> None:
        """Allow render even if upstream stages failed."""
        # Render always attempts -- it handles missing data gracefully
        pass

    def run(self, state: AnalysisState) -> None:
        """Generate the D&O underwriting worksheet documents.

        Creates Word (always), Markdown (always), and PDF (if
        WeasyPrint is installed) output files.
        """
        state.mark_stage_running(self.name)

        # Determine output directory
        output_dir = self._output_dir or Path("output") / state.ticker
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize design system and matplotlib
        ds = DesignSystem()
        configure_matplotlib_defaults()

        # Generate chart images to disk for all renderers.
        # Use light theme for PDF-friendly white-background charts.
        chart_dir = output_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        _generate_chart_images(state, chart_dir, ds, light_theme=True)

        # Generate output basename with date and version
        base_name = _get_output_basename(state.ticker)

        # Map format names to renderer functions
        format_handlers = {
            "word": (render_word_document, ".docx"),
            "markdown": (render_markdown, ".md"),
            "pdf": (render_html_pdf, ".pdf"),
        }

        for fmt in self._formats:
            if fmt == "html":
                # HTML is generated as part of PDF rendering
                # Ensure pdf format is also in list to trigger HTML generation
                if "pdf" not in self._formats:
                    # If pdf not requested, still generate HTML via pdf renderer
                    # but we need to call it with a dummy path
                    pdf_path = output_dir / f"{base_name}.pdf"
                    _render_secondary(
                        "HTML (via PDF)",
                        render_html_pdf,
                        state,
                        pdf_path,
                        ds,
                        chart_dir=chart_dir,
                    )
                continue

            if fmt not in format_handlers:
                logger.warning("Unknown output format: %s", fmt)
                continue

            render_fn, suffix = format_handlers[fmt]
            output_path = output_dir / f"{base_name}{suffix}"

            if fmt == "markdown":
                logger.warning("Markdown output is deprecated. Use HTML or Word format.")
                warnings.warn(
                    "Markdown output is deprecated. Use HTML (--format html) or Word (--format word) instead. "
                    "Markdown output will be removed in a future version.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            if fmt == "word":
                # Word is primary, no error isolation
                try:
                    render_fn(state, output_path, ds, chart_dir=chart_dir)
                    logger.info("Generated: %s", output_path)
                except Exception:
                    logger.exception("Failed to generate Word document")
            else:
                _render_secondary(
                    fmt.upper(),
                    render_fn,
                    state,
                    output_path,
                    ds,
                    chart_dir=chart_dir,
                )

        # Save source documents to output/TICKER/sources/
        _save_source_documents(state, output_dir)

        state.mark_stage_completed(self.name)


def _save_source_documents(
    state: AnalysisState,
    output_dir: Path,
) -> None:
    """Save acquired source documents to output/TICKER/sources/.

    Writes each filing as a text file and creates a manifest
    listing all sources with metadata.
    """
    sources_dir = output_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []

    if state.acquired_data is None:
        logger.info("No acquired data to save as source documents")
        return

    # Save filing documents (10-K, DEF 14A, 8-K, etc.)
    filings_dir = sources_dir / "filings"
    filings_dir.mkdir(exist_ok=True)
    source_links: dict[str, dict[str, str]] = {}
    for form_type, docs in state.acquired_data.filing_documents.items():
        for doc in docs:
            accession = doc.get("accession", "unknown")
            filing_date = doc.get("filing_date", "unknown")
            full_text = doc.get("full_text", "")
            if not full_text:
                logger.warning(
                    "Filing %s %s has no full_text -- raw source will not be saved",
                    form_type,
                    accession,
                )
                continue

            # Sanitize filename
            safe_form = form_type.replace("/", "-").replace(" ", "_")
            safe_acc = accession.replace("-", "").replace("/", "")
            filename = f"{safe_form}_{filing_date}_{safe_acc}.txt"
            filepath = filings_dir / filename
            filepath.write_text(full_text, encoding="utf-8")

            manifest.append(
                {
                    "type": "sec_filing",
                    "form_type": form_type,
                    "accession": accession,
                    "filing_date": filing_date,
                    "file": f"filings/{filename}",
                    "size_bytes": len(full_text.encode("utf-8")),
                }
            )

            # Track accession-to-file mapping for hallucination detection.
            source_links[accession] = {
                "form_type": form_type,
                "filing_date": filing_date,
                "file": f"filings/{filename}",
                "extraction_cache_key": f"{form_type}:{accession}",
            }

    # Write source_link.json mapping accession numbers to files.
    if source_links:
        source_link_path = sources_dir / "source_link.json"
        source_link_path.write_text(
            json.dumps(source_links, indent=2, default=str),
            encoding="utf-8",
        )

    # Save web search results summary
    if state.acquired_data.web_search_results:
        web_path = sources_dir / "web_search_results.json"
        web_path.write_text(
            json.dumps(
                state.acquired_data.web_search_results,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        manifest.append(
            {
                "type": "web_search",
                "file": "web_search_results.json",
            }
        )

    # Save litigation data summary
    if state.acquired_data.litigation_data:
        lit_path = sources_dir / "litigation_data.json"
        lit_path.write_text(
            json.dumps(
                state.acquired_data.litigation_data,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        manifest.append(
            {
                "type": "litigation",
                "file": "litigation_data.json",
            }
        )

    # Save acquisition metadata
    if state.acquired_data.acquisition_metadata:
        meta_path = sources_dir / "acquisition_metadata.json"
        meta_path.write_text(
            json.dumps(
                state.acquired_data.acquisition_metadata,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # Write manifest
    manifest_path = sources_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )

    filing_count = sum(len(docs) for docs in state.acquired_data.filing_documents.values())
    logger.info(
        "Saved %d source documents to %s",
        filing_count,
        sources_dir,
    )


def _render_secondary(
    format_name: str,
    renderer: object,
    state: AnalysisState,
    output_path: Path,
    ds: DesignSystem,
    chart_dir: Path | None = None,
) -> None:
    """Call a secondary renderer with error handling.

    Prevents PDF/Markdown failures from crashing the pipeline.
    """
    try:
        # Both render_markdown and render_html_pdf accept chart_dir kwarg
        result = renderer(state, output_path, ds, chart_dir=chart_dir)  # type: ignore[operator]
        if result is not None:
            logger.info("Generated %s: %s", format_name, output_path)
        else:
            logger.info(
                "%s generation skipped (dependency not available)",
                format_name,
            )
    except Exception:
        logger.exception(
            "Failed to generate %s output (non-fatal)",
            format_name,
        )


def _compute_chart_data_hash(state: AnalysisState) -> str:
    """Hash the price data inputs to detect changes.

    Produces a 16-char hex digest of the price history data
    that drives chart rendering. Used for cache invalidation.
    """
    md: dict[str, Any] = {}
    if state.acquired_data is not None:
        md = state.acquired_data.market_data
    keys = [
        "history_1y",
        "history_5y",
        "sector_history_1y",
        "sector_history_5y",
        "spy_history_1y",
        "spy_history_5y",
    ]
    hasher = hashlib.sha256()
    for k in keys:
        val = md.get(k, {})
        closes: list[Any] = val.get("Close", []) if isinstance(val, dict) else []
        tail = closes[-3:] if closes else []
        hasher.update(f"{k}:{len(closes)}:{closes[:3]}:{tail}".encode())
    return hasher.hexdigest()[:16]


def _generate_chart_images(
    state: AnalysisState,
    chart_dir: Path,
    ds: DesignSystem,
    light_theme: bool = False,
) -> None:
    """Generate all chart PNGs and save to chart_dir.

    Implements data-hash caching: computes a hash of the price data
    inputs and writes it to chart_dir/.data_hash. If the hash matches
    on next run, skips chart regeneration entirely.

    Creates: stock_1y.png, stock_5y.png, radar.png, ownership.png,
    timeline.png. Each chart is generated and saved independently --
    individual failures are logged but do not block other charts.

    Args:
        state: Complete analysis state.
        chart_dir: Directory to write chart PNGs.
        ds: Design system for styling.
        light_theme: If True, use CREDIT_REPORT_LIGHT colors for
            white-background PDF output. Default is BLOOMBERG_DARK
            for HTML dashboard.
    """
    # Data-hash cache guard: skip if price data unchanged
    hash_file = chart_dir / ".data_hash"
    current_hash = _compute_chart_data_hash(state)
    if hash_file.exists():
        existing_hash = hash_file.read_text().strip()
        stock_1y_exists = (chart_dir / "stock_1y.png").exists()
        stock_5y_exists = (chart_dir / "stock_5y.png").exists()
        if existing_hash == current_hash and (stock_1y_exists or stock_5y_exists):
            logger.info("Chart data unchanged (hash=%s), skipping regeneration", current_hash)
            return

    # Resolve color palette
    colors: dict[str, str] | None = None
    if light_theme:
        from do_uw.stages.render.design_system import CREDIT_REPORT_LIGHT

        colors = CREDIT_REPORT_LIGHT

    from do_uw.stages.render.charts.chart_guards import create_chart_placeholder
    from do_uw.stages.render.charts.stock_charts import create_stock_performance_chart

    # Stock performance charts
    for period, filename in [("1Y", "stock_1y.png"), ("5Y", "stock_5y.png")]:
        try:
            buf = create_stock_performance_chart(
                state,
                period=period,
                ds=ds,
                colors=colors,
            )
            if buf is not None:
                (chart_dir / filename).write_bytes(buf.read())
                buf.seek(0)  # Reset for potential reuse
                logger.info("Generated chart: %s", filename)
            else:
                placeholder = create_chart_placeholder(label=f"No data available ({period})")
                (chart_dir / filename).write_bytes(placeholder.read())
                logger.info("Wrote placeholder for chart: %s", filename)
        except Exception:
            logger.exception("Failed to generate chart: %s", filename)

    # Radar chart (scoring visualization) -- uses enhanced version from charts/
    try:
        from do_uw.stages.render.charts.radar_chart import (
            create_radar_chart as create_enhanced_radar,
        )

        if state.scoring and state.scoring.factor_scores:
            buf = create_enhanced_radar(
                state.scoring.factor_scores,
                ds,
                colors=colors,
            )
            if buf is not None:
                (chart_dir / "radar.png").write_bytes(buf.read())
                logger.info("Generated chart: radar.png")
            else:
                placeholder = create_chart_placeholder(
                    width=600, height=600, label="No scoring data"
                )
                (chart_dir / "radar.png").write_bytes(placeholder.read())
                logger.info("Wrote placeholder for chart: radar.png")
        else:
            placeholder = create_chart_placeholder(width=600, height=600, label="No scoring data")
            (chart_dir / "radar.png").write_bytes(placeholder.read())
            logger.info("Wrote placeholder for chart: radar.png")
    except Exception:
        logger.exception("Failed to generate radar chart")

    # Ownership chart (VIS-02)
    try:
        from do_uw.stages.render.charts.ownership_chart import create_ownership_chart

        ownership = None
        if state.extracted and state.extracted.governance:
            ownership = state.extracted.governance.ownership
        buf = create_ownership_chart(ownership, ds, colors=colors)
        if buf is not None:
            (chart_dir / "ownership.png").write_bytes(buf.read())
            logger.info("Generated chart: ownership.png")
        else:
            placeholder = create_chart_placeholder(label="No ownership data available")
            (chart_dir / "ownership.png").write_bytes(placeholder.read())
            logger.info("Wrote placeholder for chart: ownership.png")
    except Exception:
        logger.exception("Failed to generate ownership chart")

    # Litigation timeline (VIS-03)
    try:
        from do_uw.stages.render.charts.timeline_chart import create_litigation_timeline

        buf = create_litigation_timeline(state, ds, colors=colors)
        if buf is not None:
            (chart_dir / "timeline.png").write_bytes(buf.read())
            logger.info("Generated chart: timeline.png")
        else:
            placeholder = create_chart_placeholder(label="No litigation timeline data")
            (chart_dir / "timeline.png").write_bytes(placeholder.read())
            logger.info("Wrote placeholder for chart: timeline.png")
    except Exception:
        logger.exception("Failed to generate timeline chart")

    # Drawdown chart (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.drawdown_chart import create_drawdown_chart

        for period, filename in [("1Y", "drawdown_1y.png"), ("5Y", "drawdown_5y.png")]:
            try:
                buf = create_drawdown_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=colors,
                )
                if buf is not None:
                    (chart_dir / filename).write_bytes(buf.read())
                    logger.info("Generated chart: %s", filename)
                else:
                    placeholder = create_chart_placeholder(label=f"No drawdown data ({period})")
                    (chart_dir / filename).write_bytes(placeholder.read())
                    logger.info("Wrote placeholder for chart: %s", filename)
            except Exception:
                logger.exception("Failed to generate chart: %s", filename)
    except Exception:
        logger.exception("Failed to import drawdown chart module")

    # Volatility analysis chart (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.volatility_chart import create_volatility_chart

        for period, filename in [("1Y", "volatility_1y.png"), ("5Y", "volatility_5y.png")]:
            try:
                buf = create_volatility_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=colors,
                )
                if buf is not None:
                    (chart_dir / filename).write_bytes(buf.read())
                    logger.info("Generated chart: %s", filename)
                else:
                    placeholder = create_chart_placeholder(label=f"No volatility data ({period})")
                    (chart_dir / filename).write_bytes(placeholder.read())
                    logger.info("Wrote placeholder for chart: %s", filename)
            except Exception:
                logger.exception("Failed to generate chart: %s", filename)
    except Exception:
        logger.exception("Failed to import volatility chart module")

    # Relative performance chart (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.relative_performance_chart import (
            create_relative_performance_chart,
        )

        for period, filename in [("1Y", "relative_1y.png"), ("5Y", "relative_5y.png")]:
            try:
                buf = create_relative_performance_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=colors,
                )
                if buf is not None:
                    (chart_dir / filename).write_bytes(buf.read())
                    logger.info("Generated chart: %s", filename)
                else:
                    placeholder = create_chart_placeholder(
                        label=f"No relative performance data ({period})"
                    )
                    (chart_dir / filename).write_bytes(placeholder.read())
                    logger.info("Wrote placeholder for chart: %s", filename)
            except Exception:
                logger.exception("Failed to generate chart: %s", filename)
    except Exception:
        logger.exception("Failed to import relative performance chart module")

    # Drop analysis charts
    try:
        from do_uw.stages.render.charts.drop_analysis_chart import (
            create_drop_analysis_chart,
            create_drop_scatter_chart,
        )

        for period, filename in [("1Y", "drop_analysis_1y.png"), ("5Y", "drop_analysis_5y.png")]:
            try:
                buf = create_drop_analysis_chart(state, period=period)
                if buf is not None:
                    (chart_dir / filename).write_bytes(buf.read())
                    logger.info("Generated chart: %s", filename)
                else:
                    placeholder = create_chart_placeholder(
                        label=f"No drop analysis data ({period})"
                    )
                    (chart_dir / filename).write_bytes(placeholder.read())
                    logger.info("Wrote placeholder for chart: %s", filename)
            except Exception:
                logger.exception("Failed to generate chart: %s", filename)

        for period, filename in [("1Y", "drop_scatter_1y.png"), ("5Y", "drop_scatter_5y.png")]:
            try:
                buf = create_drop_scatter_chart(state, period=period)
                if buf is not None:
                    (chart_dir / filename).write_bytes(buf.read())
                    logger.info("Generated chart: %s", filename)
                else:
                    placeholder = create_chart_placeholder(
                        label=f"No drop scatter data ({period})"
                    )
                    (chart_dir / filename).write_bytes(placeholder.read())
                    logger.info("Wrote placeholder for chart: %s", filename)
            except Exception:
                logger.exception("Failed to generate chart: %s", filename)
    except Exception:
        logger.exception("Failed to import drop analysis chart module")

    # Write hash file after successful generation
    hash_file.write_text(current_hash)


def _generate_chart_svgs(
    state: AnalysisState,
    ds: DesignSystem,
) -> dict[str, str]:
    """Generate all charts as inline SVG strings for HTML embedding.

    Each chart is generated with ``format="svg"`` and
    CREDIT_REPORT_LIGHT colors (white background).  Individual
    failures are logged but do not block other charts.

    Returns:
        Dict mapping chart name to SVG markup string, e.g.
        ``{"stock_1y": "<svg ...>...</svg>", ...}``.
    """
    from do_uw.stages.render.design_system import CREDIT_REPORT_LIGHT

    svgs: dict[str, str] = {}

    # Stock performance charts (1Y and 5Y)
    try:
        from do_uw.stages.render.charts.stock_charts import create_stock_chart

        for period, key in [("1Y", "stock_1y"), ("5Y", "stock_5y")]:
            try:
                result = create_stock_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=CREDIT_REPORT_LIGHT,
                    format="svg",
                )
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import stock chart module for SVG")

    # Radar chart (10-factor scoring)
    try:
        from do_uw.stages.render.charts.radar_chart import (
            create_radar_chart as create_enhanced_radar,
        )

        if state.scoring and state.scoring.factor_scores:
            result = create_enhanced_radar(
                state.scoring.factor_scores,
                ds,
                colors=CREDIT_REPORT_LIGHT,
                format="svg",
            )
            if isinstance(result, str):
                svgs["radar"] = result
                logger.info("Generated SVG chart: radar")
    except Exception:
        logger.exception("Failed to generate SVG radar chart")

    # Ownership chart
    try:
        from do_uw.stages.render.charts.ownership_chart import create_ownership_chart

        ownership = None
        if state.extracted and state.extracted.governance:
            ownership = state.extracted.governance.ownership
        result = create_ownership_chart(
            ownership,
            ds,
            colors=CREDIT_REPORT_LIGHT,
            format="svg",
        )
        if isinstance(result, str):
            svgs["ownership"] = result
            logger.info("Generated SVG chart: ownership")
    except Exception:
        logger.exception("Failed to generate SVG ownership chart")

    # Litigation timeline
    try:
        from do_uw.stages.render.charts.timeline_chart import create_litigation_timeline

        result = create_litigation_timeline(
            state,
            ds,
            colors=CREDIT_REPORT_LIGHT,
            format="svg",
        )
        if isinstance(result, str):
            svgs["timeline"] = result
            logger.info("Generated SVG chart: timeline")
    except Exception:
        logger.exception("Failed to generate SVG timeline chart")

    # Drawdown charts (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.drawdown_chart import create_drawdown_chart

        for period, key in [("1Y", "drawdown_1y"), ("5Y", "drawdown_5y")]:
            try:
                result = create_drawdown_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=CREDIT_REPORT_LIGHT,
                    format="svg",
                )
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import drawdown chart module for SVG")

    # Volatility chart (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.volatility_chart import create_volatility_chart

        for period, key in [("1Y", "volatility_1y"), ("5Y", "volatility_5y")]:
            try:
                result = create_volatility_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=CREDIT_REPORT_LIGHT,
                    format="svg",
                )
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import volatility chart module for SVG")

    # Relative performance charts (stock analysis enhancement)
    try:
        from do_uw.stages.render.charts.relative_performance_chart import (
            create_relative_performance_chart,
        )

        for period, key in [("1Y", "relative_1y"), ("5Y", "relative_5y")]:
            try:
                result = create_relative_performance_chart(
                    state,
                    period=period,
                    ds=ds,
                    colors=CREDIT_REPORT_LIGHT,
                    format="svg",
                )
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import relative performance chart module for SVG")

    # Drop analysis charts
    try:
        from do_uw.stages.render.charts.drop_analysis_chart import (
            create_drop_analysis_chart,
            create_drop_scatter_chart,
        )

        for period, key in [("1Y", "drop_analysis_1y"), ("5Y", "drop_analysis_5y")]:
            try:
                result = create_drop_analysis_chart(state, period=period, format="svg")
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)

        for period, key in [("1Y", "drop_scatter_1y"), ("5Y", "drop_scatter_5y")]:
            try:
                result = create_drop_scatter_chart(state, period=period, format="svg")
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import drop analysis chart module for SVG")

    # Unified drop charts (investigative view with numbered events + sector overlay)
    try:
        from do_uw.stages.render.charts.unified_drop_chart import (
            create_unified_drop_chart,
        )

        for period, key in [("1Y", "unified_drop_1y"), ("5Y", "unified_drop_5y")]:
            try:
                result = create_unified_drop_chart(state, period=period, format="svg")
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import unified drop chart module for SVG")

    # Insider trading timeline charts
    try:
        from do_uw.stages.render.charts.insider_timeline_chart import (
            create_insider_timeline_chart,
        )

        for period, key in [("1Y", "insider_timeline_1y"), ("5Y", "insider_timeline_5y")]:
            try:
                result = create_insider_timeline_chart(
                    state,
                    period=period,
                    format="svg",
                )
                if isinstance(result, str):
                    svgs[key] = result
                    logger.info("Generated SVG chart: %s", key)
            except Exception:
                logger.exception("Failed to generate SVG chart: %s", key)
    except Exception:
        logger.exception("Failed to import insider timeline chart module for SVG")

    return svgs


__all__ = ["RenderStage", "_generate_chart_svgs"]
