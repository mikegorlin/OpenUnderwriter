"""Section 7: Risk Scoring & Synthesis renderer.

Renders scoring narrative lead, tier classification box, composite
score breakdown table, 10-factor radar chart, red flag gates table,
and delegates detailed factor/pattern/allegation content to
sect7_scoring_detail.py.

Phase 60-02: Receives context dict from build_template_context().
Uses context["_state"] escape hatch for scoring, benchmark, and
analysis layer data not yet directly in context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.scoring import (
    RedFlagResult,
    ScoringResult,
)
from do_uw.models.scoring_output import RedFlagSummary
from do_uw.stages.benchmark.risk_levels import score_to_risk_level
from do_uw.stages.render.chart_helpers import embed_chart
from do_uw.stages.render.charts.radar_chart import create_radar_chart
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import format_currency
from do_uw.stages.render.md_narrative_sections import scoring_narrative
from do_uw.stages.render.peer_context import get_peer_context_line
from do_uw.stages.render.sections.sect7_coverage_gaps import render_coverage_gaps
from do_uw.stages.render.sections.sect7_peril_map import render_peril_map
from do_uw.stages.render.sections.sect7_scoring_detail import render_scoring_detail

# Backward-compat alias for any callers using the old private name
_score_to_risk_level = score_to_risk_level


# -- Data access --

def _get_scoring(context: dict[str, Any]) -> ScoringResult | None:
    """Extract scoring data from context dict."""
    # TODO(phase-60): use context["scoring"] when it returns ScoringResult
    state = context.get("_state")
    return state.scoring if state is not None else None


# -- Narrative lead --

def _render_narrative_lead(
    doc: Any, context: dict[str, Any], scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render scoring narrative lead paragraph."""
    # TODO(phase-60): move scoring_narrative to context_builders
    state = context.get("_state")
    narrative_text = scoring_narrative(state) if state is not None else ""
    if narrative_text:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(narrative_text)
        run.font.name = ds.font_body
        run.font.size = ds.size_body
        run.font.color.rgb = ds.color_text
    else:
        # Fallback summary
        tier_label = scoring.tier.tier.value if scoring.tier else "N/A"
        para = doc.add_paragraph(style="DOBody")
        para.add_run(
            f"Quality Score: {scoring.quality_score:.1f}/100. "
            f"Tier: {tier_label}."
        )
        risk_level = _score_to_risk_level(scoring.quality_score)
        add_risk_indicator(para, risk_level, ds)


# -- Tier Classification Box --

def _render_tier_box(
    doc: Any, context: dict[str, Any], scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render tier classification with quality score peer context."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Tier Classification")

    # Quality score with peer context
    qs_label = f"{scoring.quality_score:.1f} / 100"
    # TODO(phase-60): move benchmark to context_builders
    state = context.get("_state")
    qs_context = get_peer_context_line("quality_score", state.benchmark if state else None)
    if qs_context:
        qs_label += f" ({qs_context.split('Ranks at the ')[1]})" if "Ranks at the " in qs_context else ""

    rows: list[list[str]] = []
    rows.append(["Quality Score", qs_label])
    rows.append(["Composite Score (pre-ceiling)", f"{scoring.composite_score:.1f}"])
    rows.append(["Total Risk Points Deducted", f"{scoring.total_risk_points:.1f}"])

    if scoring.tier:
        tier = scoring.tier
        rows.append(["Tier", tier.tier.value])
        rows.append([
            "Tier Range",
            f"{tier.score_range_low} - {tier.score_range_high}",
        ])
        if tier.action:
            rows.append(["Action Guidance", tier.action])
        if tier.probability_range:
            rows.append(["Probability Range", tier.probability_range])
        if tier.pricing_multiplier:
            rows.append(["Pricing Multiplier", tier.pricing_multiplier])

    if scoring.binding_ceiling_id:
        rows.append(["Binding Ceiling", scoring.binding_ceiling_id])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Risk level indicator
    risk_level = _score_to_risk_level(scoring.quality_score)
    pos_para: Any = doc.add_paragraph(style="DOBody")
    pos_run: Any = pos_para.add_run(
        f"Risk Assessment: {risk_level}"
    )
    pos_run.bold = True
    add_risk_indicator(pos_para, risk_level, ds)

    # Peer quality score comparison
    _render_peer_quality_context(doc, context, scoring, ds)


# -- Peer Quality Score Context --

def _render_peer_quality_context(
    doc: Any, context: dict[str, Any], scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render peer quality score comparison table when benchmark available."""
    # TODO(phase-60): move benchmark to context_builders
    state = context.get("_state")
    if state is None or state.benchmark is None:
        return
    bm = state.benchmark
    if not bm.peer_quality_scores:
        return

    sorted_peers = sorted(bm.peer_quality_scores.items(), key=lambda x: x[1], reverse=True)
    rows = [[ticker, f"{score:.1f}"] for ticker, score in sorted_peers[:8]]
    if not rows:
        return

    # Compute sector average: use explicit value or derive from peer scores
    sector_avg = bm.sector_average_score
    if sector_avg is None and bm.peer_quality_scores:
        scores = list(bm.peer_quality_scores.values())
        sector_avg = sum(scores) / len(scores)
    suffix = (f" (sector avg: {sector_avg:.1f})"
              if sector_avg is not None else "")
    sub_heading: Any = doc.add_paragraph(style="DOBody")
    sub_run: Any = sub_heading.add_run(f"Peer Quality Score Comparison{suffix}")
    sub_run.bold = True
    sub_run.font.size = ds.size_body
    add_styled_table(doc, ["Peer", "Quality Score"], rows, ds)


# -- Composite Score Breakdown Table --

def _render_composite_breakdown(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render 10-factor composite score breakdown."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Composite Score Breakdown")

    factors = scoring.factor_scores
    if not factors:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No factor scores available.")
        return

    headers = [
        "Factor", "Name", "Max Pts", "Deducted",
        "% Used", "Top Contributor",
    ]
    rows: list[list[str]] = []
    for fs in factors:
        pct = (
            f"{(fs.points_deducted / fs.max_points * 100):.0f}%"
            if fs.max_points > 0
            else "0%"
        )
        # Top contributor from evidence
        top = "None"
        if fs.evidence:
            top = fs.evidence[0]
        rows.append([
            fs.factor_id, fs.factor_name,
            str(fs.max_points), f"{fs.points_deducted:.1f}",
            pct, top,
        ])

    add_styled_table(doc, headers, rows, ds)


# -- Radar Chart --

def _render_radar(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Embed 10-factor radar chart."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("10-Factor Risk Profile")

    chart_buf = create_radar_chart(scoring.factor_scores, ds)
    if chart_buf is not None:
        embed_chart(doc, chart_buf)
        caption: Any = doc.add_paragraph(style="DOCaption")
        caption.add_run(
            "Figure: Radar chart showing risk fraction (points deducted / max) "
            "for each of the 10 scoring factors. Larger area = higher risk."
        )
    else:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Radar chart not available (no factor scores).")


# -- Red Flag Gates Table --

def _render_red_flag_gates(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render all 11 CRF gates with triggered status, evidence, ceiling."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Red Flag Gates")

    rfs = scoring.red_flag_summary
    if rfs is not None and rfs.items:
        _render_flagged_items(doc, rfs, ds)
    else:
        _render_red_flag_results(doc, scoring.red_flags, ds)


def _render_flagged_items(
    doc: Any, rfs: RedFlagSummary, ds: DesignSystem
) -> None:
    """Render SECT7-10 flagged items table."""
    headers = ["Severity", "Description", "Source", "Impact", "Trajectory"]
    rows: list[list[str]] = []
    for item in rfs.items:
        rows.append([
            item.severity.value, item.description,
            item.source, item.scoring_impact, item.trajectory,
        ])

    add_styled_table(doc, headers, rows, ds)

    # Summary counts
    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(
        f"Critical: {rfs.critical_count}, High: {rfs.high_count}, "
        f"Moderate: {rfs.moderate_count}, Low: {rfs.low_count}"
    )


def _render_red_flag_results(
    doc: Any, red_flags: list[RedFlagResult], ds: DesignSystem
) -> None:
    """Render individual red flag evaluation results."""
    triggered = [rf for rf in red_flags if rf.triggered]
    not_triggered = [rf for rf in red_flags if not rf.triggered]

    if not triggered and not not_triggered:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No red flag data available.")
        return

    if triggered:
        headers = [
            "Flag ID", "Name", "Triggered", "Ceiling", "Max Tier", "Evidence",
        ]
        rows: list[list[str]] = []
        for rf in triggered:
            ceiling = str(rf.ceiling_applied) if rf.ceiling_applied else "N/A"
            max_tier = rf.max_tier or "N/A"
            evidence = "; ".join(rf.evidence[:2]) if rf.evidence else "None"
            rows.append([
                rf.flag_id, rf.flag_name, "YES",
                ceiling, max_tier, evidence,
            ])

        # Also show non-triggered gates for completeness
        for rf in not_triggered:
            rows.append([
                rf.flag_id, rf.flag_name, "No",
                "N/A", "N/A", "",
            ])

        add_styled_table(doc, headers, rows, ds)

        # D&O context
        para = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: {len(triggered)} red flag(s) triggered. "
            f"Red flags impose quality score ceilings regardless of "
            f"factor scores. The binding ceiling determines maximum tier."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "CRITICAL", ds)
    else:
        para = doc.add_paragraph(style="DOBody")
        para.add_run("No critical red flags triggered.")


# -- Risk Type Classification --

def _render_risk_type(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render risk type classification."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Risk Type Classification")

    rt = scoring.risk_type
    if rt is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Risk type classification not available.")
        return

    rows: list[list[str]] = [
        ["Primary Risk Type", rt.primary.value],
    ]
    if rt.secondary is not None:
        rows.append(["Secondary Risk Type", rt.secondary.value])
    if rt.evidence:
        rows.append(["Supporting Evidence", "; ".join(rt.evidence[:3])])

    add_styled_table(doc, ["Attribute", "Value"], rows, ds)


# -- Severity Scenarios --

def _render_severity_scenarios(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render severity scenario table."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Severity Scenarios")

    ss = scoring.severity_scenarios
    if ss is None or not ss.scenarios:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Severity scenarios not available.")
        return

    # Market cap context
    if ss.market_cap > 0:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            f"Analysis based on market cap: "
            f"{format_currency(ss.market_cap, compact=True)}"
        )

    headers = [
        "Percentile", "Label", "Settlement Est.",
        "Defense Costs", "Total Exposure",
    ]
    rows: list[list[str]] = []
    for scenario in ss.scenarios:
        rows.append([
            f"{scenario.percentile}th",
            scenario.label,
            format_currency(scenario.settlement_estimate, compact=True),
            format_currency(scenario.defense_cost_estimate, compact=True),
            format_currency(scenario.total_exposure, compact=True),
        ])

    add_styled_table(doc, headers, rows, ds)


# -- Calibration Notes --

def _render_calibration_notes(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render SECT7-11 calibration notes."""
    notes = scoring.calibration_notes
    if not notes:
        return

    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Calibration Notes (SECT7-11)")

    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        "The following items are flagged NEEDS CALIBRATION "
        "and require expert review before final pricing:"
    )
    run.italic = True
    run.font.size = ds.size_small

    for note in notes:
        note_para: Any = doc.add_paragraph(style="DOBody")
        note_para.add_run(f"  - {note}")


# -- Main entry point --

def render_section_7(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Section 7: Risk Scoring & Synthesis."""
    heading: Any = doc.add_paragraph(style="DOHeading1")
    heading.add_run("Section 7: Risk Scoring & Synthesis")

    scoring = _get_scoring(context)
    if scoring is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Scoring data not available.")
        return

    _render_narrative_lead(doc, context, scoring, ds)
    _render_tier_box(doc, context, scoring, ds)

    # Phase 42: Peril-organized scoring (brain framework perils + causal chains)
    _render_peril_scoring(doc, context, ds)

    _render_composite_breakdown(doc, scoring, ds)
    _render_radar(doc, scoring, ds)
    _render_red_flag_gates(doc, scoring, ds)
    _render_risk_type(doc, scoring, ds)
    _render_severity_scenarios(doc, scoring, ds)
    _render_calibration_notes(doc, scoring, ds)

    # Delegate detail sections
    render_scoring_detail(doc, context, ds)

    # Forensic composites, temporal signals, NLP signals (analysis layer)
    _render_analysis_composites(doc, context, ds)

    # Phase 27: Peril map (heat map + bear cases + settlement + tower)
    render_peril_map(doc, context, ds)

    # Phase 27: Coverage gaps (DATA_UNAVAILABLE disclosure -- always last)
    render_coverage_gaps(doc, context, ds)


def _render_peril_scoring(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render peril-organized scoring section. Graceful no-op if unavailable."""
    try:
        from do_uw.stages.render.scoring_peril_data import extract_peril_scoring
        from do_uw.stages.render.sections.sect7_scoring_perils import (
            render_peril_deep_dives,
            render_peril_summary,
        )

        # TODO(phase-60): extract_peril_scoring still takes state directly
        state = context.get("_state")
        if state is None:
            return
        peril_data = extract_peril_scoring(state)
        if peril_data:
            render_peril_summary(doc, peril_data, ds)
            render_peril_deep_dives(doc, peril_data, ds)
    except ImportError:
        pass  # Brain framework not available


def _render_analysis_composites(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Delegate to sect7_scoring_analysis for forensic/temporal/NLP/exec risk."""
    try:
        from do_uw.stages.render.sections.sect7_scoring_analysis import (
            render_executive_risk,
            render_forensic_composites,
            render_nlp_signals,
            render_temporal_signals,
        )
        render_forensic_composites(doc, context, ds)
        render_executive_risk(doc, context, ds)
        render_temporal_signals(doc, context, ds)
        render_nlp_signals(doc, context, ds)
    except ImportError:
        # Module not yet available -- graceful degradation
        pass


__all__ = ["render_section_7"]
