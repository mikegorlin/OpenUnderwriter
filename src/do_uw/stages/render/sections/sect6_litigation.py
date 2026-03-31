"""Section 6: Litigation & Regulatory Exposure renderer.

Renders litigation narrative lead, timeline chart (VIS-03), securities
class actions table with full case details, and SEC enforcement pipeline
with visual stage progression. Delegates remaining content to
sect6_timeline (derivative/regulatory/industry/SOL) and sect6_defense
(defense strength/contingencies/whistleblower).

Issue-driven density gating: clean litigation (no active SCA, no SEC
enforcement, no derivative suits, no regulatory proceedings, no deal
litigation) renders concisely. Problematic litigation retains full
forensic detail.

Phase 60-02: Receives context dict from build_template_context().
Uses context["_state"] escape hatch for density, narrative engine,
timeline chart, and acquired_data blind spot results.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.density import DensityLevel
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
)
from do_uw.stages.render.chart_helpers import embed_chart
from do_uw.stages.render.charts.timeline_chart import create_litigation_timeline
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_sourced_paragraph,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_citation,
    format_currency,
    format_date_range,
    sv_val,
)
from do_uw.stages.render.md_narrative_sections import litigation_narrative
from do_uw.stages.render.sections.sect6_defense import (
    render_defense_assessment,
    render_enforcement_pipeline,
)
from do_uw.stages.render.sections.sect6_timeline import render_litigation_details
from do_uw.stages.render.tier_helpers import (
    add_meeting_prep_ref,
    render_objective_signal,
    render_scenario_context,
)

# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------


def _get_litigation(context: dict[str, Any]) -> LitigationLandscape | None:
    """Extract litigation data from context dict."""
    # TODO(phase-60): use context["litigation"] when it returns LitigationLandscape
    state = context.get("_state")
    if state is None or state.extracted is None:
        return None
    return state.extracted.litigation


# ---------------------------------------------------------------------------
# Litigation cleanliness assessment
# ---------------------------------------------------------------------------


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


def _count_historical_matters(lit: LitigationLandscape) -> int:
    """Count resolved historical matters for the concise summary."""
    count = 0
    if lit.historical_matter_count is not None:
        return int(lit.historical_matter_count.value)
    # Fallback: count settled/dismissed SCAs
    for sca in lit.securities_class_actions:
        if sca.status is not None and sca.status.value.upper() in (
            "SETTLED", "DISMISSED", "CLOSED",
        ):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Narrative lead
# ---------------------------------------------------------------------------


def _render_narrative_lead(
    doc: Any, context: dict[str, Any], lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render litigation narrative lead paragraph."""
    # TODO(phase-60): move litigation_narrative to context_builders
    state = context.get("_state")
    narrative_text = litigation_narrative(state) if state is not None else ""
    if narrative_text:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(narrative_text)
        run.font.name = ds.font_body
        run.font.size = ds.size_body
        run.font.color.rgb = ds.color_text
    elif lit.litigation_summary is not None:
        text = str(lit.litigation_summary.value)
        citation = format_citation(lit.litigation_summary)
        add_sourced_paragraph(doc, text, citation, ds)
    else:
        para = doc.add_paragraph(style="DOBody")
        para.add_run("Litigation data not available for narrative summary.")

    # Active/historical matter counts
    active = lit.active_matter_count
    historical = lit.historical_matter_count
    if active is not None or historical is not None:
        counts_para: Any = doc.add_paragraph(style="DOBody")
        parts: list[str] = []
        if active is not None:
            parts.append(f"{active.value} active matter(s)")
        if historical is not None:
            parts.append(f"{historical.value} historical matter(s)")
        run = counts_para.add_run("Litigation Overview: " + ", ".join(parts))
        run.font.size = ds.size_body


# ---------------------------------------------------------------------------
# Timeline chart
# ---------------------------------------------------------------------------


def _render_timeline_chart(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Embed litigation timeline chart (VIS-03)."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Litigation Timeline")

    # TODO(phase-60): create_litigation_timeline still takes state directly
    state = context.get("_state")
    chart_buf = create_litigation_timeline(state, ds) if state is not None else None
    if chart_buf is not None:
        embed_chart(doc, chart_buf)
        caption: Any = doc.add_paragraph(style="DOCaption")
        caption.add_run(
            "Figure: Chronological litigation and regulatory events "
            "overlaid with corporate events for pattern recognition"
        )
    else:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Timeline chart not available (no timeline events).")


# ---------------------------------------------------------------------------
# Securities Class Actions table
# ---------------------------------------------------------------------------


def _get_signal_results(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Extract signal_results dict from context."""
    state = ctx.get("_state")
    if state is None or state.analysis is None:
        return None
    return state.analysis.signal_results


def _render_sca_table(
    doc: Any, lit: LitigationLandscape, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render full SCA roster with case details."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Securities Class Actions")

    all_scas = lit.securities_class_actions
    if not all_scas:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "No active securities class actions identified in filed "
            "documents. This assessment is based on SEC filing "
            "disclosures (Item 3 and Item 8 contingency notes)."
        )
        return

    headers = [
        "Case Name", "Legal Theory", "Coverage", "Court", "Filing Date",
        "Status", "Class Period", "Lead Counsel", "Settlement", "Source",
    ]
    rows: list[list[str]] = []
    for sca in all_scas:
        rows.append(_format_sca_row(sca))

    add_styled_table(doc, headers, rows, ds)

    # D&O context annotations from brain signal do_context
    signal_results = _get_signal_results(context)
    _render_sca_signal_do_context(doc, all_scas, signal_results, ds)


def _format_sca_row(sca: CaseDetail) -> list[str]:
    """Format a single SCA row with full case details."""
    from do_uw.stages.render.context_builders._litigation_helpers import (
        COVERAGE_DISPLAY,
        _sv_str,
        format_legal_theories,
    )

    case_name = str(sv_val(sca.case_name, "N/A"))

    # Legal theory and coverage side from classifier (Plan 01)
    legal_theories = format_legal_theories(sca) or "N/A"
    cov_sv = getattr(sca, "coverage_type", None)
    coverage = ""
    if cov_sv is not None:
        raw_cov = _sv_str(cov_sv)
        coverage = COVERAGE_DISPLAY.get(raw_cov, raw_cov.replace("_", " ").title())
    coverage = coverage or "N/A"

    court = str(sv_val(sca.court, "N/A"))
    filing_date = (
        str(sca.filing_date.value)
        if sca.filing_date is not None
        else "N/A"
    )
    status = str(sv_val(sca.status, "N/A"))

    # Class period range
    cp_start = str(sca.class_period_start.value) if sca.class_period_start else None
    cp_end = str(sca.class_period_end.value) if sca.class_period_end else None
    class_period = format_date_range(cp_start, cp_end)
    if sca.class_period_days:
        class_period += f" ({sca.class_period_days}d)"

    # Lead counsel with tier
    counsel = str(sv_val(sca.lead_counsel, "N/A"))
    if sca.lead_counsel_tier is not None:
        counsel += f" [T{sca.lead_counsel_tier.value}]"

    settlement_raw = (
        sca.settlement_amount.value
        if sca.settlement_amount is not None
        else None
    )
    # LLM extraction often stores settlements in millions (e.g. 1.6 = $1.6M).
    # If the raw value is < 10000 and > 0, it's almost certainly in millions.
    if settlement_raw is not None and 0 < settlement_raw < 10_000:
        settlement_raw = settlement_raw * 1_000_000
    settlement = format_currency(settlement_raw, compact=True)

    # Source citation from case_name SourcedValue
    source = ""
    if sca.case_name is not None:
        source = format_citation(sca.case_name)

    return [
        case_name, legal_theories, coverage, court, filing_date, status,
        class_period, counsel, settlement, source,
    ]


def _render_sca_signal_do_context(
    doc: Any,
    scas: list[CaseDetail],
    signal_results: dict[str, Any] | None,
    ds: DesignSystem,
) -> None:
    """Render D&O context for SCAs from brain signal do_context.

    Replaces the deleted _add_sca_do_context() function. Uses LIT.SCA.*
    signals for D&O commentary instead of hardcoded Python strings.
    """
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    # Use the same active-status logic as sca_counter.py:
    # None status = assume active (conservative underwriting)
    _ACTIVE_STATUSES = {"ACTIVE", "PENDING", "N/A", ""}
    active_scas = []
    settled_scas = []
    for s in scas:
        if _is_regulatory_not_sca(s):
            continue
        status_obj = getattr(s, "status", None)
        if status_obj is None:
            # Unknown status = assume active (matches sca_counter.py)
            active_scas.append(s)
            continue
        status_str = status_obj.value if hasattr(status_obj, "value") else str(status_obj)
        status_upper = str(status_str).upper() if status_str is not None else ""
        if status_upper in _ACTIVE_STATUSES:
            active_scas.append(s)
        elif status_upper == "SETTLED":
            settled_scas.append(s)

    if active_scas:
        # Use LIT.SCA.active signal do_context for active SCA commentary
        sig = safe_get_result(signal_results, "LIT.SCA.active")
        do_text = sig.do_context if sig and sig.do_context else ""
        signal_desc = do_text if do_text else (
            "Direct exposure to Side A/B/C coverage; prior SCA is strongest future predictor"
        )
        render_objective_signal(
            doc, ds,
            f"{len(active_scas)} Active Securities Class Action(s)",
            "HIGH",
            signal_desc,
        )
        render_scenario_context(
            doc, ds,
            "Cases with PSLRA safe harbor and forum selection provisions "
            "settle at 40% lower median amounts.",
        )
        add_meeting_prep_ref(doc, ds, "Active Litigation")

    if settled_scas:
        total = 0.0
        for s in settled_scas:
            if s.settlement_amount is not None:
                raw = s.settlement_amount.value
                # Normalize: LLM may store in millions
                if 0 < raw < 10_000:
                    raw = raw * 1_000_000
                total += raw
        if total > 0:
            sig = safe_get_result(signal_results, "LIT.SCA.prior_settle")
            do_text = sig.do_context if sig and sig.do_context else ""
            settlement_text = do_text if do_text else (
                f"Historical settlements total "
                f"{format_currency(total, compact=True)}. Settlement "
                f"history establishes severity baseline for pricing."
            )
            para = doc.add_paragraph(style="DOBody")
            run = para.add_run(f"D&O Context: {settlement_text}")
            run.italic = True
            run.font.size = ds.size_small
            add_risk_indicator(para, "ELEVATED", ds)

    # Lead counsel tier context from SCA exposure signal
    tier1_cases = [
        s for s in scas
        if s.lead_counsel_tier is not None and s.lead_counsel_tier.value == 1
    ]
    if tier1_cases:
        sig = safe_get_result(signal_results, "LIT.SCA.exposure")
        do_text = sig.do_context if sig and sig.do_context else ""
        counsel_text = do_text if do_text else (
            f"{len(tier1_cases)} case(s) with Tier 1 lead counsel. "
            f"Top-tier plaintiff firms correlate with higher settlement amounts."
        )
        para = doc.add_paragraph(style="DOBody")
        run = para.add_run(f"D&O Context: {counsel_text}")
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "HIGH", ds)


# ---------------------------------------------------------------------------
# Data source notice
# ---------------------------------------------------------------------------


def _render_data_source_notice(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Add notice when web-based blind spot detection was not performed.

    Checks acquired_data.blind_spot_results for actual search results.
    If empty or not present, warns the reader that the analysis relies
    solely on SEC filing disclosures.
    """
    # TODO(phase-60): move blind_spot to context_builders
    state = context.get("_state")
    acquired = state.acquired_data if state is not None else None
    if acquired is None:
        return

    blind_spot = acquired.blind_spot_results
    # Count actual results across all categories
    total_results = 0
    for key in ("pre_structured", "post_structured"):
        phase_data = blind_spot.get(key, {})
        if isinstance(phase_data, dict):
            for val in phase_data.values():
                if isinstance(val, list):
                    total_results += len(val)

    if total_results == 0:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            "Note: Web-based blind spot detection was not performed "
            "for this analysis. This section relies solely on SEC "
            "filing disclosures and may not reflect publicly known "
            "events such as short seller reports, state AG actions, "
            "or breaking news coverage."
        )
        run.italic = True
        run.font.size = ds.size_small


# ---------------------------------------------------------------------------
# Clean litigation concise summary
# ---------------------------------------------------------------------------


def _render_clean_litigation_summary(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render concise litigation summary for clean companies."""
    historical = _count_historical_matters(lit)

    if historical > 0:
        text = (
            f"Litigation Landscape: No active securities litigation. "
            f"No SEC enforcement actions. No derivative suits. "
            f"{historical} historical matter(s), all resolved."
        )
    else:
        text = (
            "Litigation Landscape: No litigation exposure identified "
            "in the analysis period."
        )

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run(text)

    # Brief defense summary line (forum selection, safe harbor)
    defense = lit.defense
    fp = defense.forum_provisions
    parts: list[str] = []
    if fp.has_federal_forum is not None and fp.has_federal_forum.value:
        parts.append("Federal Forum Provision in place")
    if fp.has_exclusive_forum is not None and fp.has_exclusive_forum.value:
        parts.append("Exclusive Forum Provision in place")
    if defense.pslra_safe_harbor_usage is not None:
        parts.append(
            f"PSLRA Safe Harbor: {defense.pslra_safe_harbor_usage.value}"
        )

    if parts:
        defense_para: Any = doc.add_paragraph(style="DOBody")
        defense_para.add_run(f"Defense Posture: {'; '.join(parts)}.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_section_6(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Section 6: Litigation & Regulatory Exposure.

    Uses issue-driven density gating: when litigation is clean (no
    active SCA, no SEC enforcement, no derivative suits, no regulatory
    proceedings, no deal litigation), renders a concise summary instead
    of full forensic tables. SOL map and defense summary always render
    (always relevant for D&O).

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    heading: Any = doc.add_paragraph(style="DOHeading1")
    heading.add_run("Section 6: Litigation & Regulatory Exposure")

    lit = _get_litigation(context)
    if lit is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Litigation data not available.")
        return

    clean = _read_density_clean(context, "litigation")

    if clean:
        _render_clean_litigation_summary(doc, lit, ds)
        _render_data_source_notice(doc, context, ds)
        # SOL map always relevant -- delegate to timeline module
        render_litigation_details(doc, context, ds, concise=True)
        # Brief defense summary
        render_defense_assessment(doc, context, ds)
    else:
        # Full forensic detail for problematic litigation
        _render_narrative_lead(doc, context, lit, ds)
        _render_timeline_chart(doc, context, ds)
        _render_sca_table(doc, lit, context, ds)
        render_enforcement_pipeline(doc, lit, ds)
        _render_data_source_notice(doc, context, ds)
        render_litigation_details(doc, context, ds)
        render_defense_assessment(doc, context, ds)

    # Unclassified reserves (D-07 boilerplate bucket)
    _render_unclassified_reserves(doc, lit, ds)


def _render_unclassified_reserves(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render separated unclassified reserves (boilerplate bucket from classifier)."""
    reserves = getattr(lit, "unclassified_reserves", [])
    if not reserves:
        return

    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Unclassified Litigation Reserves")

    headers = ["Case Name", "Filing Date", "Status"]
    rows: list[list[str]] = []
    for uc in reserves:
        case_name = str(sv_val(uc.case_name, "N/A")) if uc.case_name else "N/A"
        filing_date = str(uc.filing_date.value) if uc.filing_date else "N/A"
        status = str(sv_val(uc.status, "N/A")) if uc.status else "N/A"
        rows.append([case_name, filing_date, status])

    add_styled_table(doc, headers, rows, ds)

    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        "Note: These reserves were disclosed in SEC filings but could not "
        "be classified under a specific legal theory. They typically represent "
        "generic litigation accruals or boilerplate contingency disclosures."
    )
    run.italic = True
    run.font.size = ds.size_small


__all__ = ["render_section_6"]
