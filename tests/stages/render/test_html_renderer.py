"""Tests for the HTML-to-PDF renderer (html_renderer.py).

Tests context building, template rendering, check grouping,
coverage stats, and Playwright fallback behavior.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.density import DensityLevel, PreComputedNarratives, SectionDensity
from do_uw.models.state import AnalysisState
from do_uw.stages.render.html_renderer import (
    _compute_coverage_stats,
    _group_signals_by_section,
    build_html_context,
    render_html_pdf,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_state(**overrides: Any) -> AnalysisState:
    """Create a minimal AnalysisState for testing."""
    from datetime import UTC, datetime

    state = AnalysisState(ticker="TEST")

    # Set up company identity
    from do_uw.models.common import SourcedValue
    from do_uw.models.company import CompanyIdentity, CompanyProfile

    _now = datetime.now(tz=UTC)
    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            legal_name=SourcedValue[str](
                value="Test Company Inc.",
                source="test",
                confidence="HIGH",
                as_of=_now,
            ),
        ),
    )

    # Set up analysis with densities and narratives
    from do_uw.models.state import AnalysisResults

    state.analysis = AnalysisResults()
    state.analysis.section_densities = {
        "executive": SectionDensity(level=DensityLevel.CLEAN),
        "financial": SectionDensity(level=DensityLevel.ELEVATED),
        "litigation": SectionDensity(level=DensityLevel.CRITICAL),
    }
    state.analysis.pre_computed_narratives = PreComputedNarratives(
        executive_summary="Test thesis narrative.",
        financial="Financial health summary.",
    )
    state.analysis.signal_results = {
        "FIN.LIQ.position": {
            "signal_name": "Liquidity Position",
            "status": "TRIGGERED",
            "value": 0.8,
            "evidence": "Current ratio below 1.0",
            "content_type": "EVALUATIVE_CHECK",
            "data_status": "EVALUATED",
        },
        "GOV.BOARD.size": {
            "signal_name": "Board Size",
            "status": "CLEAR",
            "value": 11,
            "evidence": "Board size within norms",
            "content_type": "MANAGEMENT_DISPLAY",
            "data_status": "EVALUATED",
        },
        "LIT.SCA.active": {
            "signal_name": "Active SCA",
            "status": "SKIPPED",
            "value": None,
            "evidence": "",
            "content_type": "EVALUATIVE_CHECK",
            "data_status": "DATA_UNAVAILABLE",
            "data_status_reason": "SCA database not available",
        },
        "BIZ.SIZE.employees": {
            "signal_name": "Employee Count",
            "status": "INFO",
            "value": 50000,
            "evidence": "Large employer",
            "content_type": "MANAGEMENT_DISPLAY",
            "data_status": "EVALUATED",
        },
    }

    for key, val in overrides.items():
        setattr(state, key, val)

    return state


# ---------------------------------------------------------------------------
# test_build_html_context
# ---------------------------------------------------------------------------


class TestBuildHtmlContext:
    """Tests for build_html_context."""

    def test_returns_dict_with_required_keys(self) -> None:
        state = _make_state()
        ctx = build_html_context(state)

        assert isinstance(ctx, dict)
        assert "densities" in ctx
        assert "narratives" in ctx
        assert "chart_images" in ctx
        assert "signal_results_by_section" in ctx
        assert "coverage_stats" in ctx
        assert "coverage_by_section" in ctx

    def test_densities_from_state(self) -> None:
        state = _make_state()
        ctx = build_html_context(state)

        assert "executive" in ctx["densities"]
        assert ctx["densities"]["financial"].level == DensityLevel.ELEVATED

    def test_narratives_from_state(self) -> None:
        state = _make_state()
        ctx = build_html_context(state)

        narr = ctx["narratives"]
        assert narr.executive_summary == "Test thesis narrative."
        assert narr.financial == "Financial health summary."

    def test_empty_state_returns_defaults(self) -> None:
        state = AnalysisState(ticker="EMPTY")
        ctx = build_html_context(state)

        assert ctx["densities"] == {}
        assert isinstance(ctx["narratives"], PreComputedNarratives)
        assert ctx["chart_images"] == {}
        assert ctx["signal_results_by_section"] == {}

    def test_contains_company_name(self) -> None:
        state = _make_state()
        ctx = build_html_context(state)

        assert ctx["company_name"] == "Test Company Inc."

    def test_generation_date_present(self) -> None:
        state = _make_state()
        ctx = build_html_context(state)

        assert "generation_date" in ctx
        assert len(ctx["generation_date"]) == 10  # YYYY-MM-DD


# ---------------------------------------------------------------------------
# test_render_html_template
# ---------------------------------------------------------------------------


class TestRenderHtmlTemplate:
    """Tests for _render_html_template."""

    def test_returns_html_string(self) -> None:
        from do_uw.stages.render.html_renderer import _render_html_template

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html

    def test_contains_company_name(self) -> None:
        from do_uw.stages.render.html_renderer import _render_html_template

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        assert "Test Company Inc." in html

    def test_contains_section_ids(self) -> None:
        from do_uw.stages.render.html_renderer import _render_html_template

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        assert 'id="executive-summary"' in html
        assert 'id="financial-health"' in html
        assert 'id="coverage"' in html


# ---------------------------------------------------------------------------
# test_group_signals_by_section
# ---------------------------------------------------------------------------


class TestGroupChecksBySection:
    """Tests for _group_signals_by_section."""

    def test_groups_by_prefix(self) -> None:
        results = {
            "FIN.LIQ.ratio": {
                "signal_name": "Ratio",
                "status": "TRIGGERED",
                "content_type": "EVALUATIVE_CHECK",
            },
            "FIN.DEBT.level": {
                "signal_name": "Debt",
                "status": "CLEAR",
                "content_type": "EVALUATIVE_CHECK",
            },
            "GOV.BOARD.size": {
                "signal_name": "Board",
                "status": "INFO",
                "content_type": "MANAGEMENT_DISPLAY",
            },
        }
        grouped = _group_signals_by_section(results)

        assert "FIN" in grouped
        assert len(grouped["FIN"]) == 2
        assert "GOV" in grouped
        assert len(grouped["GOV"]) == 1

    def test_preserves_content_type(self) -> None:
        results = {
            "GOV.BOARD.size": {
                "signal_name": "Board Size",
                "status": "INFO",
                "content_type": "MANAGEMENT_DISPLAY",
            },
        }
        grouped = _group_signals_by_section(results)

        assert grouped["GOV"][0]["content_type"] == "MANAGEMENT_DISPLAY"

    def test_empty_results(self) -> None:
        grouped = _group_signals_by_section({})
        assert grouped == {}

    def test_skips_non_dict_values(self) -> None:
        results = {"BAD.CHECK": "not a dict"}
        grouped = _group_signals_by_section(results)
        assert grouped == {}


# ---------------------------------------------------------------------------
# test_compute_coverage_stats
# ---------------------------------------------------------------------------


class TestComputeCoverageStats:
    """Tests for _compute_coverage_stats."""

    def test_correct_counts(self) -> None:
        results = {
            "FIN.A": {"status": "TRIGGERED", "data_status": "EVALUATED"},
            "FIN.B": {"status": "CLEAR", "data_status": "EVALUATED"},
            "GOV.C": {"status": "SKIPPED", "data_status": "DATA_UNAVAILABLE"},
            "LIT.D": {"status": "INFO", "data_status": "EVALUATED"},
        }
        overall, by_section = _compute_coverage_stats(results)

        assert overall["total"] == 4
        assert overall["evaluated"] == 3
        assert overall["skipped"] == 1
        assert overall["coverage_pct"] == "75"

    def test_per_section_breakdown(self) -> None:
        results = {
            "FIN.A": {"status": "TRIGGERED", "data_status": "EVALUATED"},
            "FIN.B": {"status": "SKIPPED", "data_status": "DATA_UNAVAILABLE"},
            "GOV.C": {"status": "CLEAR", "data_status": "EVALUATED"},
        }
        _, by_section = _compute_coverage_stats(results)

        assert "Financial Health" in by_section
        assert by_section["Financial Health"]["total"] == 2
        assert by_section["Financial Health"]["evaluated"] == 1
        assert by_section["Financial Health"]["skipped"] == 1

    def test_empty_results(self) -> None:
        overall, by_section = _compute_coverage_stats({})

        assert overall["total"] == 0
        assert overall["coverage_pct"] == "0"
        assert by_section == {}

    def test_all_evaluated(self) -> None:
        results = {
            "FIN.A": {"status": "TRIGGERED", "data_status": "EVALUATED"},
            "FIN.B": {"status": "CLEAR", "data_status": "EVALUATED"},
        }
        overall, _ = _compute_coverage_stats(results)

        assert overall["coverage_pct"] == "100"


# ---------------------------------------------------------------------------
# test_render_html_pdf_fallback
# ---------------------------------------------------------------------------


class TestRenderHtmlPdfFallback:
    """Tests for render_html_pdf fallback behavior."""

    @patch(
        "do_uw.stages.render.html_renderer.render_html_pdf.__module__",
        new="do_uw.stages.render.html_renderer",
    )
    def test_fallback_when_playwright_unavailable(self, tmp_path: Any) -> None:
        """When playwright import fails, should try WeasyPrint."""
        state = _make_state()
        ds = MagicMock()
        output = tmp_path / "test.pdf"

        # Patch playwright import to fail
        with (
            patch.dict(
                "sys.modules",
                {"playwright": None, "playwright.sync_api": None},
            ),
            patch(
                "do_uw.stages.render.html_renderer._fallback_weasyprint",
                return_value=None,
            ) as mock_fallback,
        ):
            result = render_html_pdf(state, output, ds)

        mock_fallback.assert_called_once()
        assert result is None

    def test_returns_none_when_no_renderer(self, tmp_path: Any) -> None:
        """When both Playwright and WeasyPrint unavailable, returns None."""
        state = _make_state()
        ds = MagicMock()
        output = tmp_path / "test.pdf"

        with (
            patch.dict(
                "sys.modules",
                {"playwright": None, "playwright.sync_api": None},
            ),
            patch(
                "do_uw.stages.render.html_renderer._fallback_weasyprint",
                return_value=None,
            ),
        ):
            result = render_html_pdf(state, output, ds)

        assert result is None


# ---------------------------------------------------------------------------
# test_integration
# ---------------------------------------------------------------------------


class TestHtmlRendererIntegration:
    """Integration tests for the full HTML rendering pipeline."""

    def test_full_html_render(self) -> None:
        """Build context and render HTML for a populated state."""
        from do_uw.stages.render.html_renderer import _render_html_template

        state = _make_state()
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        # Should contain all major sections (Phase 114 order:
        # key-stats → scorecard → executive-brief → red_flags → financial → market →
        # governance → litigation → ai-risk → scoring → meeting-prep → coverage)
        # Note: identity and executive-summary are replaced by key-stats and executive-brief.
        assert "Executive Brief" in html
        assert "Red Flags" in html
        assert "Financial Health" in html
        assert "Market" in html
        assert "Governance" in html
        assert "Litigation" in html
        assert "Scoring" in html
        assert "AI Risk" in html
        assert "Meeting Prep" in html
        assert "Coverage" in html

    def test_density_indicators_rendered(self) -> None:
        """Density indicators should appear for non-CLEAN sections that use them."""
        from do_uw.stages.render.html_renderer import _render_html_template

        state = _make_state()
        # Set ai_risk density to CRITICAL so the ai_risk section renders its density_indicator
        state.analysis.section_densities["ai_risk"] = SectionDensity(level=DensityLevel.CRITICAL)
        ctx = build_html_context(state)
        html = _render_html_template(ctx)

        # ai_risk template calls density_indicator(level) — with CRITICAL it shows "Critical Risk"
        assert "Critical Risk" in html
