"""Section 3 quarterly update renderer for Word output.

Renders the "Recent Quarterly Update" subsection into the Word document
when post-annual 10-Q quarterly data is available. Includes metrics
comparison table, material changes, legal proceedings, and risk flags.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table
from do_uw.stages.render.formatters import (
    format_change_indicator,
    format_currency,
)


def render_quarterly_update(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render quarterly update subsection into the Word document.

    Only renders content when state.extracted.financials.quarterly_updates
    is non-empty. Uses the most recent quarterly update (index 0).

    Args:
        doc: The python-docx Document.
        context: Shared context dict with _state escape hatch.
        ds: Design system for consistent styling.
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    financials = state.extracted.financials if state.extracted else None
    if financials is None or not financials.quarterly_updates:
        return

    qu = financials.quarterly_updates[0]  # Most recent

    # Heading
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run(f"Recent Quarterly Update ({qu.quarter}, filed {qu.filing_date})")

    # Metrics comparison table
    headers = ["Metric", "Current", "Prior Year", "Change"]
    rows: list[list[str]] = []

    rev = format_currency(qu.revenue.value, compact=True) if qu.revenue else "N/A"
    prior_rev = (
        format_currency(qu.prior_year_revenue, compact=True)
        if qu.prior_year_revenue is not None
        else "N/A"
    )
    rev_change = ""
    if qu.revenue and qu.prior_year_revenue and qu.prior_year_revenue != 0:
        rev_change = format_change_indicator(
            qu.revenue.value, qu.prior_year_revenue,
        )
    rows.append(["Revenue", rev, prior_rev, rev_change])

    ni = format_currency(qu.net_income.value, compact=True) if qu.net_income else "N/A"
    prior_ni = (
        format_currency(qu.prior_year_net_income, compact=True)
        if qu.prior_year_net_income is not None
        else "N/A"
    )
    ni_change = ""
    if qu.net_income and qu.prior_year_net_income and qu.prior_year_net_income != 0:
        ni_change = format_change_indicator(
            qu.net_income.value, qu.prior_year_net_income,
        )
    rows.append(["Net Income", ni, prior_ni, ni_change])

    eps = f"${qu.eps.value:.2f}" if qu.eps else "N/A"
    prior_eps = f"${qu.prior_year_eps:.2f}" if qu.prior_year_eps is not None else "N/A"
    rows.append(["EPS", eps, prior_eps, ""])

    add_styled_table(doc, headers, rows, ds)

    # Material changes (MD&A highlights)
    if qu.md_a_highlights:
        sub_heading: Any = doc.add_paragraph(style="DOHeading3")
        sub_heading.add_run("Material Changes (MD&A)")
        for highlight in qu.md_a_highlights:
            para: Any = doc.add_paragraph(style="DOBody")
            para.add_run(f"- {highlight}")

    # New legal proceedings
    if qu.new_legal_proceedings:
        sub_heading = doc.add_paragraph(style="DOHeading3")
        sub_heading.add_run("New Legal Proceedings")
        for proc in qu.new_legal_proceedings:
            para = doc.add_paragraph(style="DOBody")
            para.add_run(f"- {proc}")

    # Going concern flag
    if qu.going_concern:
        para = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run("Going Concern: Yes")
        run.bold = True
        if qu.going_concern_detail:
            detail_para: Any = doc.add_paragraph(style="DOBody")
            detail_para.add_run(qu.going_concern_detail)

    # Material weaknesses
    if qu.material_weaknesses:
        sub_heading = doc.add_paragraph(style="DOHeading3")
        sub_heading.add_run("Material Weaknesses")
        for mw in qu.material_weaknesses:
            para = doc.add_paragraph(style="DOBody")
            para.add_run(f"- {mw}")

    # Subsequent events
    if qu.subsequent_events:
        sub_heading = doc.add_paragraph(style="DOHeading3")
        sub_heading.add_run("Subsequent Events")
        for event in qu.subsequent_events:
            para = doc.add_paragraph(style="DOBody")
            para.add_run(f"- {event}")


__all__ = ["render_quarterly_update"]
