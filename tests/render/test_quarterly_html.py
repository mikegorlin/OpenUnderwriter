"""Tests for multi-quarter rendering in the HTML financial template.

Covers: 0, 1, 2+, and filtered-empty quarter scenarios, plus
trend summary table presence for 2+ valid quarters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2
import pytest


# ---------------------------------------------------------------------------
# Jinja2 environment setup -- mirrors html_renderer._render_html_template
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "do_uw"
    / "templates"
    / "html"
)


def _make_env() -> jinja2.Environment:
    """Create a Jinja2 environment matching the HTML renderer."""
    from do_uw.stages.render.formatters import (
        format_currency_accounting,
        format_adaptive,
        format_na,
        format_yoy_html,
    )

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
        undefined=jinja2.Undefined,
    )
    # Filters used by the financial template and macros
    env.filters["format_na"] = format_na
    env.filters["format_acct"] = format_currency_accounting
    env.filters["format_adaptive"] = format_adaptive
    env.filters["yoy_arrow"] = format_yoy_html
    env.filters["zip"] = zip
    env.filters["strip_jargon"] = lambda v: str(v) if v else ""
    return env


def _render_financial(fin: dict[str, Any]) -> str:
    """Render financial.html.j2 with given financial context dict.

    Wraps the template in a minimal base-like harness that imports
    the same macros the real base.html.j2 imports, then includes
    the financial section template.
    """
    env = _make_env()

    # Build a wrapper template that imports macros and includes financial section
    wrapper_src = """\
{%- from "components/badges.html.j2" import traffic_light, density_indicator, confidence_marker, tier_badge, check_summary -%}
{%- from "components/tables.html.j2" import data_table, kv_table, multi_column_grid, conditional_cell, financial_row -%}
{%- from "components/callouts.html.j2" import discovery_box, warning_box, do_context, gap_notice -%}
{%- from "components/narratives.html.j2" import section_narrative, evidence_chain -%}
{% include "sections/financial.html.j2" %}
"""
    template = env.from_string(wrapper_src)

    # Provide minimal context that financial.html.j2 expects
    context: dict[str, Any] = {
        "financials": fin,
        "densities": {},
        "narratives": None,
        "signal_results_by_section": {},
    }
    return template.render(**context)


# ---------------------------------------------------------------------------
# Quarterly update context builder helpers
# ---------------------------------------------------------------------------


def _make_quarter(
    quarter: str = "Q3 2025",
    revenue: str = "$10.5B",
    net_income: str = "$2.1B",
    eps: str = "$1.50",
    *,
    prior_revenue: str = "$9.8B",
    prior_net_income: str = "$1.9B",
    prior_eps: str = "$1.35",
    revenue_change: str = "+7.1%",
    net_income_change: str = "+10.5%",
    filing_date: str = "2025-11-15",
    period_end: str = "2025-09-30",
    md_a_highlights: list[str] | None = None,
    new_legal_proceedings: list[str] | None = None,
    legal_updates: list[str] | None = None,
    going_concern: bool = False,
    going_concern_detail: str = "",
    material_weaknesses: list[str] | None = None,
    subsequent_events: list[str] | None = None,
) -> dict[str, Any]:
    """Build a quarterly update context dict matching _build_quarterly_context output."""
    return {
        "quarter": quarter,
        "period_end": period_end,
        "filing_date": filing_date,
        "revenue": revenue,
        "net_income": net_income,
        "eps": eps,
        "prior_revenue": prior_revenue,
        "prior_net_income": prior_net_income,
        "prior_eps": prior_eps,
        "revenue_change": revenue_change,
        "net_income_change": net_income_change,
        "md_a_highlights": md_a_highlights or [],
        "new_legal_proceedings": new_legal_proceedings or [],
        "legal_updates": legal_updates or [],
        "going_concern": going_concern,
        "going_concern_detail": going_concern_detail,
        "material_weaknesses": material_weaknesses or [],
        "subsequent_events": subsequent_events or [],
    }


def _make_empty_quarter(quarter: str = "Q1 2025") -> dict[str, Any]:
    """Build a quarterly update where all financial metrics are N/A."""
    return _make_quarter(
        quarter=quarter,
        revenue="N/A",
        net_income="N/A",
        eps="N/A",
        prior_revenue="N/A",
        prior_net_income="N/A",
        prior_eps="N/A",
        revenue_change="",
        net_income_change="",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSingleQuarterlyUpdateRenders:
    """Single valid quarterly update renders with original heading style."""

    def test_single_quarterly_update_renders(self) -> None:
        qu = _make_quarter(quarter="Q3 2025")
        html = _render_financial({"quarterly_updates": [qu]})

        # Should use the original "Post-Annual Update" heading
        assert "Post-Annual Update: Q3 2025" in html
        # Should NOT show "Quarterly Updates (" multi-quarter heading
        assert "Quarterly Updates (" not in html
        # Should NOT show trend summary
        assert "Quarterly Trend Summary" not in html
        # Financial data present
        assert "Revenue" in html
        assert "Net Income" in html


class TestMultipleQuarterlyUpdatesRender:
    """Multiple valid quarterly updates all render with trend summary."""

    def test_multiple_quarterly_updates_render(self) -> None:
        quarters = [
            _make_quarter(quarter="Q3 2025", revenue="$10.5B", net_income="$2.1B", eps="$1.50"),
            _make_quarter(quarter="Q2 2025", revenue="$10.2B", net_income="$2.0B", eps="$1.42"),
            _make_quarter(quarter="Q1 2025", revenue="$9.9B", net_income="$1.8B", eps="$1.30"),
        ]
        html = _render_financial({"quarterly_updates": quarters})

        # Multi-quarter heading
        assert "Quarterly Updates (3 Quarters)" in html
        # All quarters present
        assert "Q3 2025" in html
        assert "Q2 2025" in html
        assert "Q1 2025" in html
        # Most Recent / Prior labels
        assert "Most Recent" in html
        assert "Prior" in html
        # Trend summary table
        assert "Quarterly Trend Summary" in html


class TestEmptyQuarterlyUpdatesFiltered:
    """Quarters with all N/A metrics are filtered from display."""

    def test_empty_quarterly_updates_filtered(self) -> None:
        quarters = [
            _make_quarter(quarter="Q3 2025", revenue="$10.5B", net_income="$2.1B", eps="$1.50"),
            _make_empty_quarter(quarter="Q2 2025"),  # All N/A -- should be filtered
            _make_quarter(quarter="Q1 2025", revenue="$9.9B", net_income="$1.8B", eps="$1.30"),
        ]
        html = _render_financial({"quarterly_updates": quarters})

        # Should show 2 quarters (the empty one is filtered)
        assert "Quarterly Updates (2 Quarters)" in html
        # Valid quarters present
        assert "Q3 2025" in html
        assert "Q1 2025" in html
        # The filtered quarter label should not appear in the main body
        # (Q2 2025 is filtered out, so it should not be in a heading or trend table)
        # Note: it won't appear in trend summary either since it was excluded
        assert "Quarterly Trend Summary" in html


class TestZeroQuarterlyUpdates:
    """Empty or missing quarterly updates render nothing."""

    def test_zero_quarterly_updates(self) -> None:
        html = _render_financial({"quarterly_updates": []})

        # No quarterly content should appear
        assert "Post-Annual Update" not in html
        assert "Quarterly Updates" not in html
        assert "Quarterly Trend Summary" not in html

    def test_missing_quarterly_updates_key(self) -> None:
        html = _render_financial({})

        # No quarterly content should appear
        assert "Post-Annual Update" not in html
        assert "Quarterly Updates" not in html

    def test_all_quarters_empty_shows_nothing(self) -> None:
        """When all quarters have N/A metrics, nothing should render."""
        quarters = [
            _make_empty_quarter(quarter="Q3 2025"),
            _make_empty_quarter(quarter="Q2 2025"),
        ]
        html = _render_financial({"quarterly_updates": quarters})

        assert "Post-Annual Update" not in html
        assert "Quarterly Updates" not in html
        assert "Quarterly Trend Summary" not in html


class TestTrendSummaryTablePresent:
    """Trend summary table appears only for 2+ valid quarters."""

    def test_trend_summary_table_present(self) -> None:
        quarters = [
            _make_quarter(quarter="Q3 2025", revenue="$10.5B", net_income="$2.1B", eps="$1.50"),
            _make_quarter(quarter="Q2 2025", revenue="$10.2B", net_income="$2.0B", eps="$1.42"),
        ]
        html = _render_financial({"quarterly_updates": quarters})

        # Trend summary heading and table elements
        assert "Quarterly Trend Summary" in html
        # Trend table has revenue/net_income/eps columns
        assert "Revenue" in html
        assert "Net Income" in html
        assert "EPS" in html
        # Explanation footnote
        assert "Quarters shown most-recent first" in html

    def test_trend_summary_absent_for_single_quarter(self) -> None:
        quarters = [_make_quarter(quarter="Q3 2025")]
        html = _render_financial({"quarterly_updates": quarters})

        assert "Quarterly Trend Summary" not in html
        assert "Quarters shown most-recent first" not in html
