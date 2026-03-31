"""Section 5: Governance & Leadership renderer.

Renders governance narrative, board composition table with full
director roster, board quality metrics, ownership structure with
donut chart, sentiment analysis, and anti-takeover provisions.
Delegates compensation detail to sect5_governance_comp.py.
Delegates board/ownership/sentiment to sect5_governance_board.py.

Issue-driven density gating: clean governance (high independence,
no overboarding, no CEO/Chair duality, no activists, no forensic
red flags) renders concisely. Problematic governance retains full
forensic detail.

Phase 60-02: Receives context dict from build_template_context().
Uses context["_state"] escape hatch for density, narrative engine,
and benchmark data not yet in context_builders.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.density import DensityLevel
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import LeadershipForensicProfile
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_sourced_paragraph,
    add_styled_table,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
)
from do_uw.stages.render.formatters import format_citation, format_percentage
from do_uw.stages.render.md_narrative_sections import governance_narrative
from do_uw.stages.render.peer_context import (
    get_peer_context_line,
)
from do_uw.stages.render.sections.sect5_governance_board import (
    clean_board_name,
    count_shade_factors,
    filter_valid_executives,
    render_anti_takeover,
    render_board_composition,
    render_board_quality_metrics,
    render_ownership,
    render_sentiment,
    sv_str,
)
from do_uw.stages.render.sections.sect5_governance_comp import (
    render_compensation_detail,
)
from do_uw.stages.render.tier_helpers import (
    add_meeting_prep_ref,
    render_objective_signal,
    render_scenario_context,
)


def _read_density_clean(context: dict[str, Any], section: str) -> bool:
    """Read pre-computed density from context or _state escape hatch.

    Returns True when section density is CLEAN.
    Defaults to False (conservative -- show full detail) when density is not
    populated, which causes the render to show full detail rather than
    suppressing content. This is safer than the old default of True.
    """
    # Try context densities first
    densities = context.get("densities")
    if densities is not None:
        density = densities.get(section)
        if density is not None:
            # context["densities"] stores DensityLevel enums directly
            return density == DensityLevel.CLEAN
    # TODO(phase-60): remove _state fallback when densities fully in context
    state = context.get("_state")
    if state is not None and state.analysis is not None:
        density = state.analysis.section_densities.get(section)
        if density is not None:
            return density.level == DensityLevel.CLEAN
    return False


def render_section_5(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Section 5: Governance & Leadership.

    Uses issue-driven density gating: when governance is clean (high
    independence, no overboarding, no CEO/Chair duality, no activists,
    no forensic red flags), board/ownership/sentiment/anti-takeover
    render concisely. Leadership profiles and compensation always
    render fully (always useful for underwriter).

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    heading: Any = doc.add_paragraph(style="DOHeading1")
    heading.add_run("Section 5: Governance & Leadership")

    gov = _get_governance(context)
    if gov is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Governance data not available.")
        return

    _render_narrative(doc, context, ds)

    clean = _read_density_clean(context, "governance")

    if clean:
        # Concise mode: one-sentence summaries for clean areas
        _render_governance_score_with_context(doc, context, gov, ds)
        _render_clean_board_summary(doc, gov, ds)
        _render_leadership(doc, context, gov, ds)
        render_compensation_detail(doc, context, ds)
        _render_clean_ownership_summary(doc, gov, ds)
        _render_clean_sentiment_summary(doc, gov, ds)
        _render_clean_anti_takeover_summary(doc, gov, ds)
    else:
        # Full forensic detail for problematic governance
        _render_governance_score_with_context(doc, context, gov, ds)
        _render_leadership(doc, context, gov, ds)
        render_board_composition(doc, gov, ds)
        _enrich_governance_signals(doc, gov, ds)
        render_board_quality_metrics(doc, gov, context, ds)
        render_compensation_detail(doc, context, ds)
        render_ownership(doc, gov, ds)
        render_sentiment(doc, gov, ds)
        render_anti_takeover(doc, gov, ds)



def _get_governance(context: dict[str, Any]) -> GovernanceData | None:
    """Extract governance data from context dict."""
    # TODO(phase-60): use context["governance"] when extract_governance returns GovernanceData
    state = context.get("_state")
    if state is None:
        return None
    if state.extracted is None:
        return None
    return state.extracted.governance


# ---------------------------------------------------------------------------
# Governance score with peer context
# ---------------------------------------------------------------------------


def _render_governance_score_with_context(
    doc: Any,
    context: dict[str, Any],
    gov: GovernanceData,
    ds: DesignSystem,
) -> None:
    """Render governance quality score with peer percentile context."""
    gs = gov.governance_score
    if gs.total_score is None:
        return

    score_val = gs.total_score.value
    label = f"Governance Quality Score: {score_val:.1f}/10"

    # Add peer context if available
    # TODO(phase-60): move benchmark to context_builders
    state = context.get("_state")
    benchmark = state.benchmark if state is not None else None
    context_line = get_peer_context_line("governance_score", benchmark)
    if context_line:
        label += f" ({context_line.split('Ranks at the ')[1]})" if "Ranks at the " in context_line else f" -- {context_line}"

    citation = format_citation(gs.total_score)
    add_sourced_paragraph(doc, label, citation, ds)


# ---------------------------------------------------------------------------
# Clean governance summary renderers
# ---------------------------------------------------------------------------


def _render_clean_board_summary(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render one-sentence board summary for clean governance."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Board Composition")

    board = gov.board
    size = board.size.value if board.size else "N/A"
    indep_pct = (
        format_percentage(board.independence_ratio.value * 100)
        if board.independence_ratio is not None
        else "N/A"
    )

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(
        f"Board Governance: {size}-member board, {indep_pct} independent, "
        f"no overboarding flags, no CEO/Chair duality."
    )


def _render_clean_ownership_summary(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render one-sentence ownership summary for clean governance."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Ownership Structure")

    ownership = gov.ownership
    inst_pct = (
        format_percentage(ownership.institutional_pct.value)
        if ownership.institutional_pct
        else "N/A"
    )
    insider_pct = (
        format_percentage(ownership.insider_pct.value)
        if ownership.insider_pct
        else "N/A"
    )

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(
        f"Ownership: No activist investors. "
        f"Institutional ownership {inst_pct}. "
        f"Insider ownership {insider_pct}."
    )


def _render_clean_sentiment_summary(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render brief sentiment summary when no flags detected.

    If no sentiment data exists at all, hides the entire section
    (silence = clean). Only shows when there's actual data to display.
    """
    sentiment = gov.sentiment
    coherence = gov.narrative_coherence

    # Check if any actual sentiment data exists
    has_data = any([
        sentiment.management_tone_trajectory is not None,
        sentiment.hedging_language_trend is not None,
        sentiment.ceo_cfo_divergence is not None,
        sentiment.qa_evasion_score is not None,
        coherence.overall_assessment is not None,
    ])
    has_flags = bool(coherence.coherence_flags)

    if not has_data and not has_flags:
        # No data at all — hide section entirely (silence = clean)
        return

    if has_flags:
        # Flags present -- fall through to full render
        render_sentiment(doc, gov, ds)
        return

    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Sentiment & Narrative Coherence")

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(
        "Sentiment: No material coherence flags detected. "
        "Management tone and narrative consistency within normal parameters."
    )


def _render_clean_anti_takeover_summary(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render brief anti-takeover summary when no provisions flagged."""
    board = gov.board
    has_classified = (
        board.classified_board is not None and board.classified_board.value
    )
    has_dual_class = (
        board.dual_class_structure is not None
        and board.dual_class_structure.value
    )

    if has_classified or has_dual_class:
        # Provisions present -- full detail
        render_anti_takeover(doc, gov, ds)
        return

    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Anti-Takeover Provisions")

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(
        "Anti-Takeover: No classified board. No dual-class structure. "
        "Standard governance provisions."
    )


def _enrich_governance_signals(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Add objective signal callouts for governance red flags (NOT-clean path only)."""
    board = gov.board
    if board.ceo_chair_duality is not None and board.ceo_chair_duality.value:
        render_objective_signal(
            doc, ds, "CEO/Chair Duality", "ELEVATED",
            "Single individual holds both CEO and Board Chair roles",
        )
        render_scenario_context(
            doc, ds,
            "Companies with CEO/Chair duality face 1.8x higher "
            "derivative suit filing rates due to governance concentration.",
        )
        add_meeting_prep_ref(doc, ds, "Governance Structure")
    # Overboarding
    overboarded = [d for d in gov.board_forensics if d.is_overboarded]
    if overboarded:
        names = ", ".join(
            (d.name.value[:30] if d.name else "Unknown")
            for d in overboarded[:3]
        )
        render_objective_signal(
            doc, ds,
            f"Overboarded Directors: {len(overboarded)} ({names})",
            "ELEVATED",
            "Directors serving on 3+ boards may have insufficient oversight capacity",
        )


def _render_narrative(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render governance narrative (OUT-03)."""
    gov = _get_governance(context)
    # Try pre-built summary first, then generate narrative
    if gov and gov.governance_summary is not None:
        text = str(gov.governance_summary.value)
        citation = format_citation(gov.governance_summary)
        add_sourced_paragraph(doc, text, citation, ds)
    else:
        # TODO(phase-60): move governance_narrative to context_builders
        state = context.get("_state")
        text = governance_narrative(state) if state is not None else ""
        if text:
            add_sourced_paragraph(doc, text, "", ds)
        else:
            para: Any = doc.add_paragraph(style="DOBody")
            para.add_run(
                "Governance data not available for narrative summary."
            )


def _render_leadership(
    doc: Any, context: dict[str, Any], gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render leadership stability table.

    Filters out garbage extraction entries where name equals company name,
    is a single word, or is otherwise not a valid person name. Deduplicates
    by title to keep the most complete entry per role.
    """
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Leadership Stability")

    leadership = gov.leadership
    executives = leadership.executives
    if not executives:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No executive profile data available.")
        return

    # Get company name for filtering (reject exec names matching company)
    company_name = context.get("company_name", "")
    if not company_name:
        # TODO(phase-60): ensure company_name always in context
        state = context.get("_state")
        if state is not None and state.company and state.company.identity and state.company.identity.legal_name:
            company_name = str(state.company.identity.legal_name.value or "")

    # Filter out garbage names
    valid_execs = filter_valid_executives(executives, company_name)
    if not valid_execs:
        para = doc.add_paragraph(style="DOBody")
        para.add_run("No executive profile data available.")
        return

    headers = [
        "Name", "Title", "Tenure (Yrs)", "Status",
        "Prior Lit.", "Flags",
    ]
    rows: list[list[str]] = []
    for exec_prof in valid_execs:
        name = clean_board_name(sv_str(exec_prof.name))
        title = sv_str(exec_prof.title)
        tenure = (
            f"{exec_prof.tenure_years:.1f}"
            if exec_prof.tenure_years is not None
            else "N/A"
        )
        status = exec_prof.departure_type or "ACTIVE"
        prior_lit = str(len(exec_prof.prior_litigation))
        flags = count_shade_factors(exec_prof)
        rows.append([name, title, tenure, status, prior_lit, flags])

    add_styled_table(doc, headers, rows, ds)

    # D&O context for executives with prior litigation from brain signal do_context
    _render_leadership_signal_do_context(doc, context, valid_execs, ds)

    # Stability metrics
    if leadership.stability_score is not None:
        score_text = (
            f"Leadership Stability Score: "
            f"{leadership.stability_score.value:.0f}/100"
        )
        citation = format_citation(leadership.stability_score)
        add_sourced_paragraph(doc, score_text, citation, ds)


def _get_signal_results(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Extract signal_results dict from context."""
    state = ctx.get("_state")
    if state is None or state.analysis is None:
        return None
    return state.analysis.signal_results


def _render_leadership_signal_do_context(
    doc: Any,
    context: dict[str, Any],
    executives: list[LeadershipForensicProfile],
    ds: DesignSystem,
) -> None:
    """Render D&O context for flagged leadership items from brain signal do_context.

    Replaces the deleted _add_leadership_do_context() function. Uses
    EXEC.PRIOR_LIT.any_officer and GOV.BOARD.prior_litigation signals
    for D&O commentary instead of hardcoded Python strings.
    """
    flagged = [e for e in executives if e.prior_litigation]
    if not flagged:
        return

    signal_results = _get_signal_results(context)
    # Try officer-level signal first, then board-level
    sig = safe_get_result(signal_results, "EXEC.PRIOR_LIT.any_officer")
    if not sig or not sig.do_context:
        sig = safe_get_result(signal_results, "GOV.BOARD.prior_litigation")

    do_text = sig.do_context if sig and sig.do_context else ""

    for exec_prof in flagged:
        name = clean_board_name(sv_str(exec_prof.name))
        case_count = len(exec_prof.prior_litigation)
        para: Any = doc.add_paragraph(style="DOBody")
        if do_text:
            run: Any = para.add_run(
                f"D&O Context ({name}, {case_count} prior case(s)): {do_text}"
            )
        else:
            run = para.add_run(
                f"D&O Context ({name}): {case_count} prior case(s) found."
            )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


__all__ = ["render_section_5"]
