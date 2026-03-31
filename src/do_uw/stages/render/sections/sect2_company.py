"""Section 2: Company Profile renderer (v2).

Identity, business description, subsidiary summary, and delegation
to sect2_company_details for revenue segments, geographic footprint,
customer/supplier concentration, and D&O exposure mapping.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_sourced_paragraph,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_citation,
    format_number,
    format_source_trail,
    na_if_none,
    sector_display_name,
)
from do_uw.stages.render.peer_context import render_peer_comparison_narrative


def render_section_2(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Company Profile: identity, business, subsidiaries, details."""
    _render_heading(doc, ds)
    _render_summary(doc, context, ds)
    _render_identity(doc, context, ds)
    _render_business_description(doc, context, ds)
    _render_subsidiary_summary(doc, context, ds)
    # v6.0 subsections: business model, ops complexity, events, environment, sector, structure
    _render_v6_subsections(doc, context, ds)
    # Structured peer comparison (SC6: named peers with characteristics)
    # TODO(phase-60): migrate peer_context to use context dict
    state = context["_state"]
    render_peer_comparison_narrative(doc, state, ds)
    # Delegate detailed company data to split module
    _render_details_delegation(doc, context, ds)
    # Classification, hazard profile, risk factors (analysis layer)
    _render_hazard_delegation(doc, context, ds)


def _render_heading(doc: Any, ds: DesignSystem) -> None:
    """Add section heading."""
    para: Any = doc.add_paragraph(style="DOHeading1")
    run: Any = para.add_run("Section 2: Company Profile")
    _ = (run, ds)


def _render_summary(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render summary paragraph with source citation."""
    state = context["_state"]
    summary_text = "Company profile data not available."
    citation = ""

    if state.company and state.company.section_summary:
        sv = state.company.section_summary
        summary_text = str(sv.value)
        citation = format_citation(sv)

    add_sourced_paragraph(doc, summary_text, citation, ds)


def _render_identity(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render company identity table with source citations."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Company Identity")

    state = context["_state"]
    identity = state.company.identity if state.company else None
    if identity is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Company identity data not available.")
        return

    # Canonical sector: use inherent risk sector_name, fall back to sector code
    sector_label = "N/A"
    if (
        state.executive_summary
        and state.executive_summary.inherent_risk
        and state.executive_summary.inherent_risk.sector_name
    ):
        sector_label = state.executive_summary.inherent_risk.sector_name
    elif identity.sector:
        sector_label = sector_display_name(identity.sector.value)

    # GICS code from profile (populated during extraction)
    gics_str = "N/A"
    gics_cite = ""
    if state.company and state.company.gics_code:
        gics_str = _sv_str(state.company.gics_code)
        gics_cite = _sv_cite(state.company.gics_code)

    rows: list[list[str]] = [
        ["Legal Name", _sv_str(identity.legal_name), _sv_cite(identity.legal_name)],
        ["Ticker", identity.ticker, ""],
        ["CIK", _sv_str(identity.cik), _sv_cite(identity.cik)],
        ["Sector", sector_label, _sv_cite(identity.sector) if identity.sector else ""],
        ["SIC Code", _sv_str(identity.sic_code), _sv_cite(identity.sic_code)],
        ["SIC Description", _sv_str(identity.sic_description), ""],
        ["GICS Code", gics_str, gics_cite],
        ["NAICS Code", _sv_str(identity.naics_code), _sv_cite(identity.naics_code)],
        ["Exchange", _sv_str(identity.exchange), _sv_cite(identity.exchange)],
        [
            "State of Incorporation",
            _sv_str(identity.state_of_incorporation),
            _sv_cite(identity.state_of_incorporation),
        ],
        ["FPI Status", "Yes" if identity.is_fpi else "No", ""],
        [
            "Fiscal Year End",
            _sv_str(identity.fiscal_year_end) if identity.fiscal_year_end else "N/A",
            _sv_cite(identity.fiscal_year_end) if identity.fiscal_year_end else "",
        ],
    ]
    add_styled_table(doc, ["Field", "Value", "Source"], rows, ds)


def _render_business_description(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render business description from LLM extraction or fallback."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Business Description")

    state = context["_state"]

    # Primary: business_description from Item 1 extraction
    if state.company and state.company.business_description:
        sv = state.company.business_description
        add_sourced_paragraph(doc, str(sv.value), format_source_trail(sv), ds)
        return

    # Fallback: business_model_description
    if state.company and state.company.business_model_description:
        sv = state.company.business_model_description
        add_sourced_paragraph(doc, str(sv.value), format_source_trail(sv), ds)
        return

    # Final fallback: industry classification
    if state.company and state.company.industry_classification:
        sv = state.company.industry_classification
        desc = f"Industry classification: {sv.value}"
        add_sourced_paragraph(doc, desc, format_source_trail(sv), ds)
        return

    body: Any = doc.add_paragraph(style="DOBody")
    body.add_run("Business description not available.")


def _render_subsidiary_summary(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render subsidiary count and key subsidiaries if available."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Subsidiaries")

    state = context["_state"]
    sub_count = state.company.subsidiary_count if state.company else None
    if sub_count is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Subsidiary data not available.")
        return

    count_val = sub_count.value
    count_text = f"Total subsidiaries: {format_number(count_val)}"
    add_sourced_paragraph(doc, count_text, format_source_trail(sub_count), ds)

    # Flag high subsidiary counts as D&O complexity indicator
    if count_val > 100:
        note: Any = doc.add_paragraph(style="DOCaption")
        run: Any = note.add_run(
            f"D&O Note: {format_number(count_val)} subsidiaries indicates "
            "complex corporate structure with multi-jurisdiction exposure."
        )
        _ = run


def _render_details_delegation(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Delegate to sect2_company_details for revenue/geo/exposure."""
    try:
        from do_uw.stages.render.sections.sect2_company_details import (
            render_company_details,
        )
        render_company_details(doc, context, ds)
    except ImportError:
        # Module not yet available -- graceful degradation
        _render_legacy_details(doc, context, ds)


def _render_legacy_details(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Fallback: render revenue segments, geo, and exposure inline."""
    _render_revenue_segments_inline(doc, context, ds)
    _render_geographic_inline(doc, context, ds)
    _render_exposure_factors_inline(doc, context, ds)


def _render_revenue_segments_inline(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Inline revenue segments (legacy fallback)."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Revenue Segments")

    state = context["_state"]
    segments = state.company.revenue_segments if state.company else []
    if not segments:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Revenue segment data not available.")
        return

    rows: list[list[str]] = []
    total_rev = sum(float(s.value.get("revenue", 0) or 0) for s in segments)
    for sv_seg in segments:
        seg = sv_seg.value
        name = str(seg.get("name", seg.get("segment", "Unknown")))
        rev_str = _safe_currency(seg.get("revenue"))
        pct = seg.get("percentage")
        if pct is None and total_rev > 0 and seg.get("revenue") is not None:
            pct = float(seg["revenue"]) / total_rev * 100
        pct_str = _safe_percentage(pct)
        rows.append([name, rev_str, pct_str, format_citation(sv_seg)])

    add_styled_table(
        doc, ["Segment", "Revenue", "% of Total", "Source"], rows, ds
    )


def _render_geographic_inline(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Inline geographic footprint (legacy fallback).

    Handles both Exhibit 21 style (jurisdiction/subsidiary_count) and
    revenue-based geographic data.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Geographic Footprint")

    state = context["_state"]
    geo = state.company.geographic_footprint if state.company else []
    if not geo:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Geographic footprint data not available.")
        return

    rows: list[list[str]] = []
    for sv_geo in geo:
        g = sv_geo.value
        # Handle both data shapes
        region = str(
            g.get("jurisdiction",
                   g.get("region", g.get("geography", "Unknown")))
        )
        if region.lower() in ("unknown", "n/a", ""):
            continue

        # Try subsidiary count first, then revenue
        sub_count = g.get("subsidiary_count")
        if sub_count is not None:
            rows.append([region, str(int(float(sub_count))), ""])
        else:
            rev_str = _safe_currency(g.get("revenue"))
            pct_str = _safe_percentage(g.get("percentage"))
            rows.append([region, rev_str, pct_str])

    if not rows:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("Geographic footprint data not available.")
        return

    # Determine headers based on data shape
    first_g = geo[0].value
    if "subsidiary_count" in first_g:
        add_styled_table(
            doc, ["Jurisdiction", "Subsidiaries", ""], rows, ds,
        )
    else:
        add_styled_table(
            doc, ["Region", "Revenue", "% of Total"], rows, ds,
        )


def _render_exposure_factors_inline(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Inline D&O exposure factors (legacy fallback)."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("D&O Exposure Factors")

    state = context["_state"]
    factors = state.company.do_exposure_factors if state.company else []
    if not factors:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("D&O exposure factor data not available.")
        return

    for sv_factor in factors:
        factor = sv_factor.value
        name = str(factor.get("factor", factor.get("name", "Unknown")))
        level = str(factor.get("level", "N/A"))
        rationale = str(factor.get("reason", factor.get("rationale", "")))

        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(f"{name}: {level}")
        run.bold = True
        _add_exposure_indicator(fp, level, ds)

        if rationale:
            detail: Any = doc.add_paragraph(style="DOCaption")
            detail.add_run(rationale)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv_str(sv: Any) -> str:
    """Extract string value from SourcedValue or return N/A."""
    return "N/A" if sv is None else na_if_none(sv.value)


def _sv_cite(sv: Any) -> str:
    """Extract source trail from SourcedValue or return empty."""
    return "" if sv is None else format_source_trail(sv)


def _safe_currency(val: Any) -> str:
    """Parse a value that may be numeric or a string like '$61.3B'."""
    if val is None:
        return "N/A"
    try:
        from do_uw.stages.render.formatters import format_currency as fc
        return fc(float(val), compact=True)
    except (ValueError, TypeError):
        return str(val)


def _safe_percentage(val: Any) -> str:
    """Parse a value that may be numeric or string like '47%'."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return str(val)


def _add_exposure_indicator(
    para: Any, level: str, ds: DesignSystem
) -> None:
    """Add risk indicator based on exposure level string."""
    level_map: dict[str, str] = {
        "HIGH": "HIGH", "ELEVATED": "ELEVATED", "MODERATE": "MODERATE",
        "LOW": "MODERATE", "CRITICAL": "CRITICAL",
    }
    risk_level = level_map.get(level.upper(), "NEUTRAL")
    add_risk_indicator(para, risk_level, ds)


def _render_v6_subsections(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Delegate to sect2_company_v6 for all v6.0 dimension subsections."""
    try:
        from do_uw.stages.render.sections.sect2_company_v6 import (
            render_v6_subsections,
        )
        render_v6_subsections(doc, context, ds)
    except ImportError:
        # Module not yet available -- graceful degradation
        pass


def _render_hazard_delegation(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Delegate to sect2_company_hazard for classification/hazard/risk factors."""
    try:
        from do_uw.stages.render.sections.sect2_company_hazard import (
            render_classification,
            render_hazard_profile,
            render_risk_factors,
        )
        render_classification(doc, context, ds)
        render_hazard_profile(doc, context, ds)
        render_risk_factors(doc, context, ds)
    except ImportError:
        # Module not yet available -- graceful degradation
        pass


__all__ = ["render_section_2"]
