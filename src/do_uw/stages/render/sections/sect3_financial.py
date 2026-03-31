"""Section 3: Financial Health renderer (v2).

Renders financial narrative lead, distress indicators panel with zone
coloring, and earnings quality summary. Delegates all statement tables
(income, balance sheet, cash flow) to sect3_tables, and audit/debt
analysis to sect3_audit.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.density import DensityLevel
from do_uw.models.financials import (
    DistressIndicators,
    DistressResult,
    ExtractedFinancials,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_sourced_paragraph,
    add_styled_table,
    set_cell_shading,
)
from do_uw.stages.render.formatters import (
    format_citation,
    humanize_enum,
)
from do_uw.stages.render.md_narrative import financial_narrative
from do_uw.stages.render.peer_context import (
    get_peer_context_line,
)
from do_uw.stages.render.sections.sect3_peers import render_peer_group
from do_uw.stages.render.sections.sect3_quarterly import render_quarterly_update
from do_uw.stages.render.sections.sect3_tables import render_financial_tables
from do_uw.stages.render.tier_helpers import (
    add_meeting_prep_ref,
    render_objective_signal,
    render_scenario_context,
)


def render_section_3(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Financial Health section into the Word document.

    Layout order (narrative-first):
    1. Section heading
    2. Financial Health Narrative (analyst-quality interpretive lead)
    3. Income Statement table (delegated to sect3_tables)
    4. Balance Sheet table (delegated to sect3_tables)
    5. Cash Flow table (delegated to sect3_tables)
    6. Distress Indicators Panel (4 models, zone coloring, trajectory)
    7. Earnings Quality Summary
    8. Audit Risk Assessment (delegated to sect3_audit)
    9. Peer Group Comparison
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    _render_heading(doc, ds)
    _render_narrative(doc, context, ds)
    render_financial_tables(doc, context, ds)
    render_quarterly_update(doc, context, ds)
    financials = state.extracted.financials if state.extracted else None
    _render_distress_panel(doc, context, financials, ds)
    _render_earnings_quality(doc, context, financials, ds)
    _render_audit_delegation(doc, context, ds)
    render_peer_group(doc, context, financials, ds)


def _render_heading(doc: Any, ds: DesignSystem) -> None:
    """Add section heading."""
    para: Any = doc.add_paragraph(style="DOHeading1")
    run: Any = para.add_run("Section 3: Financial Health")
    _ = (run, ds)


def _render_narrative(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render analyst-quality financial narrative as the lead.

    Uses the enhanced narrative engine to produce interpretive text
    citing specific dollar amounts, margins, and D&O conclusions.
    Falls back to stored narrative if engine produces nothing.
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    financials = state.extracted.financials if state.extracted else None

    # Try the narrative engine first for analyst-quality prose
    narrative_text = financial_narrative(state)

    # Fall back to pre-stored narrative
    if not narrative_text and financials and financials.financial_health_narrative:
        sv = financials.financial_health_narrative
        narrative_text = str(sv.value)
        citation = format_citation(sv)
        add_sourced_paragraph(doc, narrative_text, citation, ds)
        return

    if narrative_text:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run(narrative_text)
    else:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("Financial health data not available.")


# ---------------------------------------------------------------------------
# Distress Indicators Panel
# ---------------------------------------------------------------------------

_ZONE_COLORS: dict[str, str] = {
    "SAFE": "DCEEF8",       # Blue (NOT green)
    "GREY": "FFF3CD",       # Amber
    "DISTRESS": "FCE8E6",   # Red
}

_ZONE_LABELS: dict[str, str] = {
    "safe": "Safe",
    "grey": "Grey Zone",
    "distress": "Distress",
    "not_applicable": "N/A",
}

_DO_CONTEXT: dict[str, str] = {
    "Altman Z-Score": (
        "Bankruptcy predictor. Distress zone companies face fiduciary duty "
        "scrutiny under Revlon/zone of insolvency doctrine."
    ),
    "Beneish M-Score": (
        "Earnings manipulation detector. Scores above -1.78 indicate "
        "elevated restatement risk, a primary SCA catalyst."
    ),
    "Ohlson O-Score": (
        "Bankruptcy probability model. Higher values signal financial stress "
        "that may limit litigation defense resources."
    ),
    "Piotroski F-Score": (
        "Fundamental quality indicator. Scores 0-3 signal weak fundamentals; "
        "7-9 indicate strong quality."
    ),
}


def _is_financial_density_clean(context: dict[str, Any]) -> bool:
    """Read pre-computed financial density from ANALYZE stage.

    Returns True when section density is CLEAN.
    Defaults to False (conservative -- show full detail) when density
    is not populated.
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    if state.analysis is not None:
        fin_density = state.analysis.section_densities.get("financial")
        if fin_density is not None:
            return fin_density.level == DensityLevel.CLEAN
    return False


def _render_distress_panel(
    doc: Any,
    context: dict[str, Any],
    financials: ExtractedFinancials | None,
    ds: DesignSystem,
) -> None:
    """Render distress indicators as a panel with zone coloring.

    If financial health is clean, renders a concise summary instead of
    full detail tables (issue-driven density gating).
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Distress Indicators")

    distress = financials.distress if financials else None
    if distress is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Distress indicator data not available.")
        return

    # Issue-driven density gating: clean companies get concise summary
    # Read pre-computed assessment from ANALYZE stage
    fin_clean = _is_financial_density_clean(context)
    if fin_clean:
        body = doc.add_paragraph(style="DOBody")
        body.add_run(
            "Financial Integrity: No concerns identified. All distress "
            "models in safe zone. Earnings quality metrics within "
            "normal ranges."
        )
        # Add peer context for leverage if available
        # TODO(phase-60): move to context_builders
        state = context["_state"]
        lev_line = get_peer_context_line("leverage_debt_ebitda", state.benchmark)
        if lev_line:
            ctx: Any = doc.add_paragraph(style="DOBody")
            ctx.add_run(f"Leverage: {lev_line}.")
        return

    headers = ["Model", "Score", "Zone", "Trajectory", "D&O Context"]
    rows: list[list[str]] = []
    _add_distress_row(rows, "Altman Z-Score", distress.altman_z_score)
    _add_distress_row(rows, "Beneish M-Score", distress.beneish_m_score)
    _add_distress_row(rows, "Ohlson O-Score", distress.ohlson_o_score)
    _add_distress_row(rows, "Piotroski F-Score", distress.piotroski_f_score)

    if not rows:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("No distress models computed.")
        return

    table: Any = add_styled_table(doc, headers, rows, ds)
    _color_distress_zones(table, distress, ds)

    # Add peer context for leverage if available
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    lev_line = get_peer_context_line("leverage_debt_ebitda", state.benchmark)
    if lev_line:
        ctx = doc.add_paragraph(style="DOBody")
        ctx.add_run(f"Leverage context: {lev_line}.")

    # Tier 2/3: Objective signals + scenario context for elevated distress
    _enrich_distress_signals(doc, distress, ds)


def _enrich_distress_signals(
    doc: Any, distress: DistressIndicators, ds: DesignSystem
) -> None:
    """Add objective signal callouts and scenario context for elevated distress."""
    z = distress.altman_z_score
    if z is not None and z.score is not None and z.zone.value == "distress":
        render_objective_signal(
            doc, ds, f"Altman Z-Score = {z.score:.2f} (DISTRESS ZONE)",
            "HIGH", "Zone threshold: below 1.81",
        )
        render_scenario_context(
            doc, ds,
            "Companies entering the distress zone experience claim "
            "frequency 3.2x industry baseline.",
        )
        add_meeting_prep_ref(doc, ds, "Financial Distress")
    m = distress.beneish_m_score
    if m is not None and m.score is not None and m.score > -1.78:
        render_objective_signal(
            doc, ds, f"Beneish M-Score = {m.score:.2f} (LIKELY MANIPULATOR)",
            "ELEVATED", "Threshold: above -1.78",
        )
        render_scenario_context(
            doc, ds,
            "Companies with M-Score above -1.78 experience SCA filings "
            "at 2.3x the base rate. Earnings quality concerns drive "
            "Theory A (misleading financials) allegations.",
        )
        add_meeting_prep_ref(doc, ds, "Earnings Quality")


def _add_distress_row(
    rows: list[list[str]], name: str, result: DistressResult | None
) -> None:
    """Add a distress indicator row."""
    if result is None:
        rows.append([name, "N/A", "N/A", "", _DO_CONTEXT.get(name, "")])
        return

    score_str = f"{result.score:.2f}" if result.score is not None else "N/A"
    zone_str = _ZONE_LABELS.get(
        result.zone.value, humanize_enum(result.zone.value)
    )
    trajectory = _format_trajectory(result.trajectory)
    context = _DO_CONTEXT.get(name, "")
    rows.append([name, score_str, zone_str, trajectory, context])


def _format_trajectory(
    trajectory: list[dict[str, float | str]],
) -> str:
    """Format distress model trajectory as compact display string.

    Handles two trajectory shapes:
    - Period-based (Altman, Beneish, Ohlson): [{period, score, zone}, ...]
      -> "FY2023: 2.5 -> FY2024: 3.1 (improving)"
    - Criteria-based (Piotroski): [{criterion, score}, ...]
      -> "7/9 criteria met" with pass/fail summary
    """
    if not trajectory:
        return "N/A"

    # Detect criteria-based trajectory (Piotroski F-Score)
    if "criterion" in trajectory[0]:
        return _format_criteria_trajectory(trajectory)

    return _format_period_trajectory(trajectory)


def _format_criteria_trajectory(
    trajectory: list[dict[str, float | str]],
) -> str:
    """Format Piotroski-style criteria trajectory as compact summary."""
    passed = 0
    total = len(trajectory)
    for entry in trajectory:
        score = entry.get("score")
        try:
            if score is not None and float(score) >= 1.0:
                passed += 1
        except (ValueError, TypeError):
            pass  # "N/A" scores are not counted as passed

    return f"{passed}/{total} criteria met"


def _format_period_trajectory(
    trajectory: list[dict[str, float | str]],
) -> str:
    """Format period-based trajectory (Altman, Beneish, Ohlson)."""
    parts: list[str] = []
    for entry in trajectory[-4:]:
        period = str(entry.get("period", ""))
        score = entry.get("score")
        try:
            score_str = f"{float(score):.1f}" if score is not None else "?"
        except (ValueError, TypeError):
            score_str = str(score) if score is not None else "?"
        if period:
            parts.append(f"{period}: {score_str}")
        else:
            parts.append(score_str)

    trend_str = " -> ".join(parts)

    # Determine trajectory direction
    scores: list[float] = []
    for entry in trajectory[-4:]:
        s = entry.get("score")
        try:
            if s is not None:
                scores.append(float(s))
        except (ValueError, TypeError):
            pass

    if len(scores) >= 2:
        diff = scores[-1] - scores[0]
        if diff > 0.5:
            trend_str += " (improving)"
        elif diff < -0.5:
            trend_str += " (declining)"
        else:
            trend_str += " (stable)"

    return trend_str


def _color_distress_zones(
    table: Any,
    distress: DistressIndicators,
    ds: DesignSystem,
) -> None:
    """Apply color to zone cells based on distress classification."""
    results = [
        distress.altman_z_score,
        distress.beneish_m_score,
        distress.ohlson_o_score,
        distress.piotroski_f_score,
    ]
    zone_col = 2  # Zone is the 3rd column (0-indexed)
    for row_idx, result in enumerate(results):
        if result is None:
            continue
        zone = result.zone.value.upper()
        color = _ZONE_COLORS.get(zone)
        if color:
            cell: Any = table.rows[row_idx + 1].cells[zone_col]
            set_cell_shading(cell, color)


# ---------------------------------------------------------------------------
# Earnings Quality
# ---------------------------------------------------------------------------


def _render_earnings_quality(
    doc: Any,
    context: dict[str, Any],
    financials: ExtractedFinancials | None,
    ds: DesignSystem,
) -> None:
    """Render earnings quality summary from extracted data.

    If financial health is clean, the distress panel already covered
    earnings quality in its summary. Full detail only for problematic companies.
    """
    # If clean, skip the separate earnings quality section -- already summarized
    # Read pre-computed assessment from ANALYZE stage
    eq_fin_clean = _is_financial_density_clean(context)
    if eq_fin_clean:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Earnings Quality")

    eq = financials.earnings_quality if financials else None
    if eq is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Earnings quality data not available.")
        return

    eq_data = eq.value
    rows: list[list[str]] = []

    ocf_ni = eq_data.get("ocf_to_ni")
    if ocf_ni is not None:
        quality = (
            "Healthy" if ocf_ni > 0.8
            else ("Concern" if ocf_ni < 0.5 else "Adequate")
        )
        rows.append(["OCF/Net Income", f"{ocf_ni:.2f}", quality])

    accruals = eq_data.get("accruals_ratio")
    if accruals is not None:
        quality = "Elevated" if accruals > 0.10 else "Normal"
        rows.append(["Accruals Ratio", f"{accruals:.2f}", quality])

    rev_qual = eq_data.get("revenue_quality")
    if rev_qual is not None:
        rows.append(["Revenue Quality", f"{rev_qual:.2f}", ""])

    if rows:
        table: Any = add_styled_table(
            doc, ["Metric", "Value", "Assessment"], rows, ds,
        )
        # Color quality assessments
        for row_idx, row_data in enumerate(rows):
            assessment = row_data[2]
            color = _quality_color(assessment)
            if color:
                cell: Any = table.rows[row_idx + 1].cells[2]
                set_cell_shading(cell, color)
    else:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("No earnings quality metrics available.")

    # Citation
    cite: Any = doc.add_paragraph(style="DOCitation")
    cite.add_run(f"Source: {eq.source}, {eq.confidence} confidence")


def _quality_color(assessment: str) -> str | None:
    """Map quality assessment to cell color."""
    if assessment in ("Concern", "Elevated"):
        return "FCE8E6"  # Red
    if assessment == "Healthy":
        return "DCEEF8"  # Blue (NOT green)
    if assessment in ("Adequate", "Normal"):
        return "FFF3CD"  # Amber
    return None


# ---------------------------------------------------------------------------
# Audit delegation
# ---------------------------------------------------------------------------


def _render_audit_delegation(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Delegate audit risk rendering to sect3_audit."""
    from do_uw.stages.render.sections.sect3_audit import render_audit_risk

    render_audit_risk(doc, context, ds)


__all__ = ["render_section_3"]
