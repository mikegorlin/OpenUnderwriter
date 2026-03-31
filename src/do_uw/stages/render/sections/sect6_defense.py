"""Section 6 defense split: defense strength assessment, SEC enforcement
pipeline, contingent liabilities, and whistleblower indicators.

Split from sect6_timeline.py for 500-line compliance. This module
renders SECT6-04 (enforcement pipeline), SECT6-05 (defense),
SECT6-08 (contingencies), and SECT6-09 (whistleblower) sub-areas.

Phase 60-02: Receives context dict; extracts litigation via _state escape hatch.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.litigation import LitigationLandscape, SECEnforcementPipeline
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_sourced_paragraph,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_citation,
    format_currency,
    na_if_none,
    sv_val,
)


def _get_litigation(context: dict[str, Any]) -> LitigationLandscape | None:
    """Extract litigation data from context dict."""
    # TODO(phase-60): use context["litigation"] when it returns LitigationLandscape
    state = context.get("_state")
    if state is None or state.extracted is None:
        return None
    return state.extracted.litigation


# ---------------------------------------------------------------------------
# Defense Strength Assessment
# ---------------------------------------------------------------------------


def _render_defense_strength(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render defense strength assessment table.

    Shows forum provisions, PSLRA safe harbor, assigned judge track
    record, prior dismissal success, and overall defense quality.
    """
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Defense Strength Assessment")

    defense = lit.defense
    rows: list[list[str]] = []

    # Forum provisions
    fp = defense.forum_provisions
    rows.append([
        "Federal Forum Provision",
        _sv_bool(fp.has_federal_forum),
    ])
    if fp.federal_forum_details is not None:
        rows.append([
            "  FFP Details",
            str(fp.federal_forum_details.value)[:60],
        ])
    rows.append([
        "Exclusive Forum Provision",
        _sv_bool(fp.has_exclusive_forum),
    ])
    if fp.exclusive_forum_details is not None:
        rows.append([
            "  EFP Details",
            str(fp.exclusive_forum_details.value)[:60],
        ])

    # Defense strengths -- only include rows with actual data
    _candidates: list[tuple[str, str]] = [
        ("PSLRA Safe Harbor", str(sv_val(defense.pslra_safe_harbor_usage, "N/A"))),
        ("Truth-on-Market Viability", str(sv_val(defense.truth_on_market_viability, "N/A"))),
        ("Judge Track Record", str(sv_val(defense.judge_track_record, "N/A"))),
        ("Prior Dismissal Success", str(sv_val(defense.prior_dismissal_success, "N/A"))),
        ("Overall Defense Strength", str(sv_val(defense.overall_defense_strength, "N/A"))),
    ]
    populated = [(label, val) for label, val in _candidates if val != "N/A"]
    for label, val in populated:
        rows.append([label, val])

    # If no defense strength data was available, add a helpful note
    if not populated:
        rows.append([
            "Defense Assessment",
            "Insufficient litigation data for assessment",
        ])

    add_styled_table(doc, ["Factor", "Assessment"], rows, ds)

    # Defense narrative
    if defense.defense_narrative is not None:
        add_sourced_paragraph(
            doc,
            str(defense.defense_narrative.value),
            format_citation(defense.defense_narrative),
            ds,
        )

    # D&O context for weak defense
    strength = defense.overall_defense_strength
    if strength is not None and strength.value.upper() == "WEAK":
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            "D&O Context: Weak defense posture increases expected "
            "settlement amounts. Consider higher retention or "
            "attachment point recommendations."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "HIGH", ds)


# ---------------------------------------------------------------------------
# Contingent Liabilities
# ---------------------------------------------------------------------------


def _render_contingent_liabilities(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render contingent liabilities table with ASC 450 classification."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Contingent Liabilities")

    contingencies = lit.contingent_liabilities
    if not contingencies:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "No disclosed contingent liabilities found in SEC filings. "
            "Review Item 8 footnotes and Item 3 for complete assessment."
        )
        return

    headers = ["Description", "ASC 450 Class.", "Accrued", "Range"]
    rows: list[list[str]] = []
    for cont in contingencies:
        desc = (
            str(cont.description.value)[:60]
            if cont.description is not None
            else "N/A"
        )
        classification = str(sv_val(cont.asc_450_classification, "N/A"))
        accrued_val = (
            cont.accrued_amount.value
            if cont.accrued_amount is not None
            else None
        )
        accrued = format_currency(
            _normalize_llm_dollars(accrued_val), compact=True
        )
        range_str = _format_range(cont)
        rows.append([desc, classification, accrued, range_str])

    add_styled_table(doc, headers, rows, ds)

    # Total reserve
    total_reserve = lit.total_litigation_reserve
    if total_reserve is not None:
        reserve_val = _normalize_llm_dollars(total_reserve.value)
        reserve_text = (
            f"Total Litigation Reserve: "
            f"{format_currency(reserve_val, compact=True)}"
        )
        add_sourced_paragraph(
            doc, reserve_text, format_citation(total_reserve), ds
        )

    # D&O context for probable contingencies
    probable = [
        c for c in contingencies
        if (c.asc_450_classification is not None
            and c.asc_450_classification.value.lower() == "probable")
    ]
    if probable:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: {len(probable)} probable contingenc(y/ies). "
            f"ASC 450 probable classification indicates management "
            f"believes loss is likely. Direct impact on D&O exposure."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "HIGH", ds)


def _format_range(cont: Any) -> str:
    """Format contingent liability range."""
    low = cont.range_low
    high = cont.range_high
    if low is not None and high is not None:
        low_val = _normalize_llm_dollars(low.value)
        high_val = _normalize_llm_dollars(high.value)
        return (
            f"{format_currency(low_val, compact=True)} - "
            f"{format_currency(high_val, compact=True)}"
        )
    if low is not None:
        low_val = _normalize_llm_dollars(low.value)
        return f">= {format_currency(low_val, compact=True)}"
    if high is not None:
        high_val = _normalize_llm_dollars(high.value)
        return f"<= {format_currency(high_val, compact=True)}"
    return na_if_none(None)


# ---------------------------------------------------------------------------
# Whistleblower Indicators
# ---------------------------------------------------------------------------


def _render_whistleblower_indicators(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render whistleblower risk indicators."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Whistleblower Indicators")

    indicators = lit.whistleblower_indicators
    if not indicators:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "No whistleblower indicators identified in SEC filings. "
            "SEC whistleblower tips are not publicly disclosed; "
            "absence does not confirm lack of activity."
        )
        return

    headers = ["Type", "Description", "Date", "Significance"]
    rows: list[list[str]] = []
    for ind in indicators:
        ind_type = str(sv_val(ind.indicator_type, "N/A"))
        desc = (
            str(ind.description.value)[:60]
            if ind.description is not None
            else "N/A"
        )
        date_str = (
            str(ind.date_identified.value)
            if ind.date_identified is not None
            else "N/A"
        )
        significance = str(sv_val(ind.significance, "N/A"))
        rows.append([ind_type, desc, date_str, significance])

    add_styled_table(doc, headers, rows, ds)

    # D&O context for high-significance indicators
    high_significance = [
        i for i in indicators
        if (i.significance is not None
            and i.significance.value.upper() == "HIGH")
    ]
    if high_significance:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: {len(high_significance)} high-significance "
            f"whistleblower indicator(s). Whistleblower activity often "
            f"precedes SEC enforcement actions and can trigger qui tam "
            f"claims under the False Claims Act."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "HIGH", ds)


# ---------------------------------------------------------------------------
# SEC Enforcement Pipeline (moved from sect6_litigation for 500-line limit)
# ---------------------------------------------------------------------------

# Canonical stage ordering for pipeline visualization
STAGE_ORDER: list[str] = [
    "Comment Letters", "Informal Inquiry", "Formal Investigation",
    "Wells Notice", "Enforcement Action",
]

_STAGE_MAP: dict[str, int] = {
    "NONE": -1, "COMMENT_LETTER": 0, "INFORMAL_INQUIRY": 1,
    "FORMAL_INVESTIGATION": 2, "WELLS_NOTICE": 3, "ENFORCEMENT_ACTION": 4,
}


def render_enforcement_pipeline(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render SEC enforcement pipeline with visual stage progression."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("SEC Enforcement Pipeline")

    enforcement = lit.sec_enforcement
    _render_pipeline_visual(doc, enforcement, ds)

    # Actions table
    if enforcement.actions:
        sub_heading: Any = doc.add_paragraph(style="DOBody")
        sub_run: Any = sub_heading.add_run("SEC Actions Detail")
        sub_run.bold = True
        sub_run.font.size = ds.size_body

        action_headers = ["Type", "Date", "Description"]
        action_rows: list[list[str]] = []
        for action_sv in enforcement.actions[:10]:
            action_dict = action_sv.value
            action_rows.append([
                str(action_dict.get("type", "N/A")),
                str(action_dict.get("date", "N/A")),
                str(action_dict.get("description", "N/A"))[:80],
            ])
        add_styled_table(doc, action_headers, action_rows, ds)

    # Enforcement narrative
    if enforcement.enforcement_narrative is not None:
        add_sourced_paragraph(
            doc,
            str(enforcement.enforcement_narrative.value),
            format_citation(enforcement.enforcement_narrative),
            ds,
        )


def _render_pipeline_visual(
    doc: Any, enforcement: SECEnforcementPipeline, ds: DesignSystem
) -> None:
    """Render visual pipeline stage table with confirmed/unconfirmed markers."""
    highest = enforcement.highest_confirmed_stage
    current_idx = -1
    if highest is not None:
        current_idx = _STAGE_MAP.get(highest.value, -1)

    pipeline_parts: list[str] = []
    for idx, stage_name in enumerate(STAGE_ORDER):
        if idx <= current_idx:
            pipeline_parts.append(f"[{stage_name}]")
        else:
            pipeline_parts.append(f"({stage_name})")

    pipeline_text = " -> ".join(pipeline_parts)
    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(f"Pipeline: {pipeline_text}")
    run.font.size = ds.size_body

    if current_idx >= 0:
        pos_para: Any = doc.add_paragraph(style="DOBody")
        pos_run: Any = pos_para.add_run(
            f"Current Position: {STAGE_ORDER[current_idx]}"
        )
        pos_run.bold = True
        risk_level = "MODERATE" if current_idx < 2 else (
            "HIGH" if current_idx < 4 else "CRITICAL"
        )
        add_risk_indicator(pos_para, risk_level, ds)

        if current_idx >= 3:
            context_para: Any = doc.add_paragraph(style="DOBody")
            context_run: Any = context_para.add_run(
                "D&O Context: Wells notice or enforcement action "
                "triggers CRF-02/CRF-03 red flags. Imposes quality "
                "score ceiling and limits tier placement."
            )
            context_run.italic = True
            context_run.font.size = ds.size_small
            add_risk_indicator(context_para, "CRITICAL", ds)

    cl_count = enforcement.comment_letter_count
    if cl_count is not None and cl_count.value > 0:
        detail = na_if_none(cl_count.value)
        cl_para: Any = doc.add_paragraph(style="DOBody")
        cl_para.add_run(f"SEC Comment Letters: {detail}")
        if enforcement.comment_letter_topics:
            topics = [str(t.value) for t in enforcement.comment_letter_topics[:5]]
            cl_para.add_run(f" (Topics: {', '.join(topics)})")

    if (enforcement.industry_sweep_detected is not None
            and enforcement.industry_sweep_detected.value):
        sweep_para: Any = doc.add_paragraph(style="DOBody")
        sweep_run: Any = sweep_para.add_run(
            "D&O Context: SEC industry sweep activity detected. "
            "Heightened regulatory scrutiny across sector."
        )
        sweep_run.italic = True
        sweep_run.font.size = ds.size_small
        add_risk_indicator(sweep_para, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_llm_dollars(value: float | None) -> float | None:
    """Normalize LLM-extracted dollar amounts to actual USD.

    LLMs frequently extract financial values in millions (e.g. 7.8 = $7.8M)
    rather than raw dollars. If 0 < value < 10,000, assume millions.
    """
    if value is None:
        return None
    if 0 < value < 10_000:
        return value * 1_000_000
    return value


def _sv_bool(sv: Any) -> str:
    """Format a SourcedValue[bool] as Yes/No/N/A."""
    if sv is None:
        return "N/A"
    return "Yes" if sv.value else "No"


# ---------------------------------------------------------------------------
# Workforce, Product & Environmental (SECT6-04)
# ---------------------------------------------------------------------------


def _render_workforce_product_env(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render workforce, product, and environmental matters."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Workforce, Product & Environmental Matters")

    wpe = lit.workforce_product_environmental
    categories: list[tuple[str, list[Any]]] = [
        ("Employment Matters", list(wpe.employment_matters) + list(wpe.eeoc_charges) + list(wpe.warn_notices)),
        ("Product Liability", list(wpe.product_recalls) + list(wpe.mass_tort_exposure)),
        ("Environmental Actions", list(wpe.environmental_actions)),
        ("Cybersecurity Incidents", list(wpe.cybersecurity_incidents)),
    ]

    has_any = any(items for _, items in categories)
    if not has_any:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("None found.")
        return

    for category_name, items in categories:
        if items:
            sub: Any = doc.add_paragraph(style="DOBody")
            run: Any = sub.add_run(f"{category_name}:")
            run.bold = True
            run.font.size = ds.size_body
            for item in items:
                val = str(item.value) if hasattr(item, "value") else str(item)
                item_para: Any = doc.add_paragraph(style="DOBody")
                item_para.add_run(f"  - {val}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_defense_assessment(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render defense assessment, contingent liabilities, whistleblower,
    and workforce/product/environmental matters.

    Covers SECT6-04 (workforce/product/env), SECT6-05 (defense strength),
    SECT6-08 (ASC 450 contingencies), and SECT6-09 (whistleblower).

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    lit = _get_litigation(context)
    if lit is None:
        return

    _render_defense_strength(doc, lit, ds)
    _render_contingent_liabilities(doc, lit, ds)
    _render_workforce_product_env(doc, lit, ds)
    _render_whistleblower_indicators(doc, lit, ds)


__all__ = ["render_defense_assessment", "render_enforcement_pipeline"]
