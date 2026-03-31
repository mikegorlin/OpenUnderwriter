"""FastAPI app factory for the Angry Dolphin dashboard.

Creates and configures a FastAPI application that serves the interactive
dashboard. Loads AnalysisState from a JSON file, sets up Jinja2 templates
with Angry Dolphin branding, and provides routes for the overview page,
section drill-downs, meeting prep, and peer comparison.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from do_uw.dashboard.charts import (
    build_factor_bar_chart,
    build_risk_heatmap,
    build_risk_radar,
    build_tier_gauge,
    empty_figure,
)
from do_uw.dashboard.charts_financial import (
    build_distress_gauges,
    build_peer_comparison_bars,
    build_red_flag_summary,
)
from do_uw.dashboard.design import CSS_VARIABLES, tier_to_css_class
from do_uw.dashboard.state_api import (
    build_dashboard_context,
    extract_finding_detail,
    extract_meeting_questions,
    extract_peer_metrics,
    extract_section_detail,
)
from do_uw.pipeline import Pipeline
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
)

logger = logging.getLogger(__name__)

# Resolve paths relative to this package
_PKG_ROOT = Path(__file__).resolve().parent.parent
_STATIC_DIR = _PKG_ROOT / "static"
_TEMPLATE_DIR = _PKG_ROOT / "templates" / "dashboard"


def _load_state_from_path(state_path: Path) -> Any:
    """Load AnalysisState from a JSON file.

    Args:
        state_path: Path to the state.json file.

    Returns:
        Deserialized AnalysisState.

    Raises:
        FileNotFoundError: If the state file does not exist.
        ValueError: If the state file is invalid.
    """
    return Pipeline.load_state(state_path)


def create_app(state_path: Path) -> FastAPI:
    """Create and configure the FastAPI dashboard application.

    Args:
        state_path: Path to the analysis state.json file.

    Returns:
        Configured FastAPI application ready to serve.
    """
    app = FastAPI(
        title="Angry Dolphin Dashboard",
        docs_url=None,
        redoc_url=None,
    )

    # Load initial state
    analysis_state = _load_state_from_path(state_path)
    app.state.analysis_state = analysis_state  # type: ignore[attr-defined]
    app.state.state_path = state_path  # type: ignore[attr-defined]
    app.state.state_mtime = state_path.stat().st_mtime  # type: ignore[attr-defined]

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Set up Jinja2 templates
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # Register template filters (Jinja2 env type is partially unknown in starlette)
    _templates: Any = templates
    env: Any = _templates.env
    env.filters["format_currency"] = format_currency
    env.filters["format_pct"] = format_percentage
    env.filters["na_if_none"] = na_if_none
    env.filters["tier_css"] = tier_to_css_class

    # Inject CSS variables into all template contexts
    env.globals["css_vars"] = CSS_VARIABLES

    def _maybe_reload_state(app_inst: FastAPI) -> None:
        """Reload state if the file has been modified since last load."""
        current_path: Path = app_inst.state.state_path  # type: ignore[attr-defined]
        stored_mtime: float = app_inst.state.state_mtime  # type: ignore[attr-defined]
        try:
            current_mtime = current_path.stat().st_mtime
            if current_mtime > stored_mtime:
                logger.info("State file changed, reloading: %s", current_path)
                new_state = _load_state_from_path(current_path)
                app_inst.state.analysis_state = new_state  # type: ignore[attr-defined]
                app_inst.state.state_mtime = current_mtime  # type: ignore[attr-defined]
        except (FileNotFoundError, ValueError):
            logger.warning("Failed to reload state file: %s", current_path)

    def _get_state(app_inst: FastAPI) -> Any:
        """Get current analysis state with hot-reload check."""
        _maybe_reload_state(app_inst)
        return app_inst.state.analysis_state  # type: ignore[attr-defined]

    # -- Page routes --

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        """Render the dashboard overview page with section summary cards."""
        state = _get_state(app)
        ctx = build_dashboard_context(state)
        return templates.TemplateResponse(request, "index.html", ctx)

    @app.get("/section/{section_id}", response_class=HTMLResponse)
    def section_detail_view(
        request: Request, section_id: str,
    ) -> HTMLResponse:
        """Render a section detail panel loaded via htmx.

        Args:
            request: The incoming HTTP request.
            section_id: The analytical section identifier.

        Returns:
            HTML fragment for the section detail.
        """
        state = _get_state(app)
        detail = extract_section_detail(state, section_id)
        ctx = build_dashboard_context(state)
        ctx["request"] = request
        ctx["detail"] = detail

        # AI risk gets a custom partial with rich sub-dimension display
        if section_id == "ai_risk" and detail.get("data"):
            ctx["section"] = detail["data"]
            return templates.TemplateResponse(
                request, "partials/_ai_risk_detail.html", ctx,
            )

        return templates.TemplateResponse(request, "section.html", ctx)

    @app.get("/section/{section_id}/finding/{finding_idx}", response_class=HTMLResponse)
    def finding_detail_view(
        request: Request, section_id: str, finding_idx: int,
    ) -> HTMLResponse:
        """Render an individual finding detail fragment.

        Args:
            request: The incoming HTTP request.
            section_id: The analytical section identifier.
            finding_idx: Zero-based index of the finding.

        Returns:
            HTML fragment for the finding detail.
        """
        state = _get_state(app)
        finding = extract_finding_detail(state, section_id, finding_idx)
        ctx: dict[str, Any] = {"request": request, "finding": finding}
        return templates.TemplateResponse(
            request, "partials/_finding_detail.html", ctx,
        )

    @app.get("/meeting-prep", response_class=HTMLResponse)
    def meeting_prep_view(
        request: Request,
        category: str | None = Query(default=None),
    ) -> HTMLResponse:
        """Render the meeting prep questions panel.

        Args:
            request: The incoming HTTP request.
            category: Optional category filter.

        Returns:
            HTML fragment for meeting prep questions.
        """
        state = _get_state(app)
        questions = extract_meeting_questions(state, category)
        ctx: dict[str, Any] = {
            "request": request,
            "questions": questions,
            "active_category": category,
        }
        return templates.TemplateResponse(
            request, "partials/_meeting_prep.html", ctx,
        )

    @app.get("/api/peer-comparison", response_class=HTMLResponse)
    def peer_comparison_view(
        request: Request,
        metric: str = Query(default="quality_score"),
    ) -> HTMLResponse:
        """Render the peer comparison panel with selected metric.

        Args:
            request: The incoming HTTP request.
            metric: Metric key to compare.

        Returns:
            HTML fragment for peer comparison.
        """
        state = _get_state(app)
        peer_data = extract_peer_metrics(state)
        ctx: dict[str, Any] = {
            "request": request,
            "peer_data": peer_data,
            "selected_metric": metric,
        }
        return templates.TemplateResponse(
            request, "partials/_peer_comparison.html", ctx,
        )

    # -- Chart API endpoints (return Plotly JSON for client-side rendering) --

    @app.get("/api/chart/risk-radar")
    def chart_risk_radar() -> JSONResponse:
        """Return Plotly JSON for the 10-factor risk radar chart."""
        fig: Any = build_risk_radar(_get_state(app))
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/risk-heatmap")
    def chart_risk_heatmap() -> JSONResponse:
        """Return Plotly JSON for the factor risk heatmap."""
        fig: Any = build_risk_heatmap(_get_state(app))
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/factor-bars")
    def chart_factor_bars() -> JSONResponse:
        """Return Plotly JSON for the factor deduction bar chart."""
        fig: Any = build_factor_bar_chart(_get_state(app))
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/quality-gauge")
    def chart_quality_gauge() -> JSONResponse:
        """Return Plotly JSON for the overall quality score gauge."""
        state: Any = _get_state(app)
        if state.scoring is None:
            fig: Any = empty_figure()
        else:
            fig = build_tier_gauge(state.scoring.quality_score)
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/distress/{model}")
    def chart_distress(model: str) -> JSONResponse:
        """Return Plotly JSON for a specific distress model gauge."""
        gauges = build_distress_gauges(_get_state(app))
        fig: Any = gauges.get(model)
        if fig is None:
            fig = empty_figure()
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/red-flags")
    def chart_red_flags() -> JSONResponse:
        """Return Plotly JSON for the red flag summary chart."""
        fig: Any = build_red_flag_summary(_get_state(app))
        return JSONResponse(content=fig.to_dict())

    @app.get("/api/chart/peer-comparison/{metric}")
    def chart_peer_comparison(metric: str) -> JSONResponse:
        """Return Plotly JSON for a peer comparison bar chart."""
        fig: Any = build_peer_comparison_bars(_get_state(app), metric)
        return JSONResponse(content=fig.to_dict())

    # Reference route handlers so pyright does not flag them as unused
    _ = (
        index,
        section_detail_view,
        finding_detail_view,
        meeting_prep_view,
        peer_comparison_view,
        chart_risk_radar,
        chart_risk_heatmap,
        chart_factor_bars,
        chart_quality_gauge,
        chart_distress,
        chart_red_flags,
        chart_peer_comparison,
    )

    return app


__all__ = ["create_app"]
