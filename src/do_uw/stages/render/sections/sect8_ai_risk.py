"""Section 8: AI Transformation Risk renderer.

Renders company-specific AI risk assessment from actual filing data:
- Overview panel: composite score, threat level, industry model, trend
- Sub-dimension scores: 5 dimensions with evidence and source citations
- AI disclosures: From LLM 10-K extraction (Item 1/1A/7)
- Patent & innovation: Patent count, competitive position, filing trend
- Peer comparison: Company vs peers on AI dimensions
- Forward indicators: Hiring trends, investment trajectory, regulatory
- Data source attribution

All data from state.extracted.ai_risk (AIRiskAssessment model).
"""

from __future__ import annotations

from typing import Any

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)
from do_uw.stages.benchmark.risk_levels import (
    dim_score_threat as dim_score_threat,
)
from do_uw.stages.benchmark.risk_levels import (
    score_to_threat_label as score_to_threat_label,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_section_divider,
    add_sourced_paragraph,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_number,
    format_percentage,
    format_risk_level,
)

# Backward-compat aliases for the old private names
_score_to_threat_label = score_to_threat_label
_dim_score_threat = dim_score_threat

# ---------------------------------------------------------------------------
# Display name mapping for sub-dimensions
# ---------------------------------------------------------------------------

_DIM_DISPLAY_NAMES: dict[str, str] = {
    "revenue_displacement": "Revenue Displacement",
    "cost_structure": "Cost Structure",
    "competitive_moat": "Competitive Moat",
    "workforce_automation": "Workforce Automation",
    "regulatory_ip": "Regulatory/IP",
}

_DIM_DO_CONTEXT: dict[str, str] = {
    "revenue_displacement": (
        "AI-driven revenue displacement increases claim probability through "
        "shareholder allegations of failure to adapt business model."
    ),
    "cost_structure": (
        "AI cost structure disruption may trigger margin compression "
        "leading to earnings miss litigation."
    ),
    "competitive_moat": (
        "Eroding competitive moat from AI disruption increases "
        "vulnerability to securities fraud claims."
    ),
    "workforce_automation": (
        "Workforce automation exposure creates both employment "
        "practices liability and disclosure obligation risks."
    ),
    "regulatory_ip": (
        "AI regulatory and IP risks include patent infringement "
        "exposure and evolving AI governance requirements."
    ),
}


# ---------------------------------------------------------------------------
# Safe data extraction
# ---------------------------------------------------------------------------


def _get_ai_risk(context: dict[str, Any]) -> AIRiskAssessment | None:
    """Extract AI risk assessment from context dict."""
    # TODO(phase-60): use context["ai_risk"] when available
    state = context.get("_state")
    if state is None or state.extracted is None:
        return None
    return state.extracted.ai_risk


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------


def _render_overview_panel(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render AI risk overview panel with score, threat level, and trend."""
    threat = _score_to_threat_label(ai_risk.overall_score)
    model_label = ai_risk.industry_model_id.replace("_", " ").title()

    # Summary paragraph
    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        f"AI Transformation Risk Score: {ai_risk.overall_score:.0f}/100"
    )
    run.bold = True
    add_risk_indicator(para, threat, ds)

    # Key metrics table
    rows: list[list[str]] = [
        ["Composite Score", f"{ai_risk.overall_score:.0f} / 100"],
        ["Threat Level", format_risk_level(threat)],
        ["Industry Model", model_label],
        ["Disclosure Trend", ai_risk.disclosure_trend],
    ]
    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # D&O context for high scores
    if ai_risk.overall_score >= 70.0:
        ctx: Any = doc.add_paragraph(style="DOBody")
        ctx_run: Any = ctx.add_run(
            "D&O Context: Score above 70 indicates material AI disruption "
            "exposure. Companies in this range face elevated shareholder "
            "litigation risk from failure-to-adapt allegations and "
            "competitive displacement scenarios."
        )
        ctx_run.italic = True
        ctx_run.font.size = ds.size_small
        add_risk_indicator(ctx, "HIGH", ds)


def _render_sub_dimensions(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render sub-dimension scoring table with evidence and D&O context."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Risk Sub-Dimensions")

    if not ai_risk.sub_dimensions:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Sub-dimension scoring not available.")
        return

    headers = [
        "Dimension", "Score (/10)", "Weight", "Threat Level", "Key Evidence",
    ]
    rows: list[list[str]] = []
    high_dims: list[AISubDimension] = []

    for dim in ai_risk.sub_dimensions:
        dim_name = _DIM_DISPLAY_NAMES.get(
            dim.dimension, dim.dimension.replace("_", " ").title()
        )
        evidence = _format_evidence(dim.evidence)
        computed_threat = _dim_score_threat(dim.score)
        display_threat = dim.threat_level if dim.threat_level != "UNKNOWN" else computed_threat
        rows.append([
            dim_name,
            f"{dim.score:.1f}",
            format_percentage(dim.weight * 100, decimals=0),
            format_risk_level(display_threat),
            evidence,
        ])
        if dim.score >= 7.0:
            high_dims.append(dim)

    add_styled_table(doc, headers, rows, ds)

    # D&O context for high-scoring dimensions
    for dim in high_dims:
        dim_name = _DIM_DISPLAY_NAMES.get(
            dim.dimension, dim.dimension.replace("_", " ")
        )
        context_text = _DIM_DO_CONTEXT.get(
            dim.dimension,
            f"Elevated {dim_name} score indicates increased D&O exposure.",
        )
        context_para: Any = doc.add_paragraph(style="DOBody")
        label_run: Any = context_para.add_run(f"D&O Context ({dim_name}): ")
        label_run.bold = True
        label_run.font.size = ds.size_small
        text_run: Any = context_para.add_run(
            f"Score {dim.score:.1f}/10 -- {context_text}"
        )
        text_run.italic = True
        text_run.font.size = ds.size_small
        add_risk_indicator(context_para, "HIGH", ds)


def _render_disclosures(
    doc: Any, disclosure: AIDisclosureData, ds: DesignSystem
) -> None:
    """Render AI disclosure analysis from filing data."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("AI Disclosures (Filing Analysis)")

    if disclosure.mention_count == 0 and not disclosure.risk_factors:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No AI-related disclosures identified in SEC filings.")
        return

    # Disclosure metrics table
    rows: list[list[str]] = [
        ["Total AI Mentions (Item 1A)", format_number(disclosure.mention_count)],
        ["Opportunity Mentions", format_number(disclosure.opportunity_mentions)],
        ["Threat Mentions", format_number(disclosure.threat_mentions)],
        ["AI Sentiment", disclosure.sentiment],
        ["Year-over-Year Trend", disclosure.yoy_trend],
    ]
    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Risk factors from filings
    if disclosure.risk_factors:
        rf_heading: Any = doc.add_paragraph(style="DOBody")
        rf_run: Any = rf_heading.add_run("Disclosed AI Risk Factors:")
        rf_run.bold = True

        for i, factor in enumerate(disclosure.risk_factors[:5], 1):
            factor_para: Any = doc.add_paragraph(style="DOBody")
            factor_para.add_run(f"  {i}. {factor}")

    # Sentiment D&O context
    if disclosure.sentiment == "THREAT":
        ctx: Any = doc.add_paragraph(style="DOBody")
        ctx_run: Any = ctx.add_run(
            "D&O Context: Company frames AI primarily as a threat. "
            "Threat-dominant disclosure may indicate material business "
            "model risk that shareholders could allege was inadequately "
            "addressed by management."
        )
        ctx_run.italic = True
        ctx_run.font.size = ds.size_small
        add_risk_indicator(ctx, "ELEVATED", ds)


def _render_patent_activity(
    doc: Any, patent: AIPatentActivity, ds: DesignSystem
) -> None:
    """Render AI patent and innovation section."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("AI Patent & Innovation")

    if patent.ai_patent_count == 0 and not patent.recent_filings:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "No AI patent activity identified. Companies without AI patent "
            "portfolios may face competitive displacement risk."
        )
        return

    rows: list[list[str]] = [
        ["AI Patent Count", format_number(patent.ai_patent_count)],
        ["Filing Trend", patent.filing_trend],
    ]
    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Recent filings
    if patent.recent_filings:
        recent_heading: Any = doc.add_paragraph(style="DOBody")
        r_run: Any = recent_heading.add_run("Recent AI Patent Filings:")
        r_run.bold = True

        for filing in patent.recent_filings[:3]:
            title = filing.get("title", "Untitled")
            date = filing.get("filing_date", "N/A")
            number = filing.get("patent_number", "")
            filing_para: Any = doc.add_paragraph(style="DOBody")
            text = f"  {number}: {title} (filed {date})" if number else f"  {title} (filed {date})"
            filing_para.add_run(text)


def _render_peer_comparison(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render peer AI comparison table."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Peer AI Comparison")

    if not ai_risk.peer_comparison_available:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "Peer comparison unavailable. Run with "
            "--analyze-peers for peer-relative assessment."
        )
        return

    cp: AICompetitivePosition = ai_risk.competitive_position

    # Summary metrics
    rows: list[list[str]] = [
        ["Company AI Mentions", format_number(cp.company_ai_mentions)],
        ["Peer Average Mentions", f"{cp.peer_avg_mentions:.1f}"],
        ["Adoption Stance", cp.adoption_stance],
    ]
    if cp.percentile_rank is not None:
        rows.append(["Percentile Rank", f"{cp.percentile_rank:.0f}th"])
    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Peer mention breakdown
    if cp.peer_mention_counts:
        mention_heading: Any = doc.add_paragraph(style="DOBody")
        m_run: Any = mention_heading.add_run("Peer AI Mention Breakdown:")
        m_run.bold = True

        mention_headers = ["Peer", "AI Mentions", "vs. Company"]
        mention_rows: list[list[str]] = []
        for ticker, count in sorted(
            cp.peer_mention_counts.items(), key=lambda x: x[1], reverse=True
        ):
            delta = count - cp.company_ai_mentions
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            mention_rows.append([ticker, format_number(count), delta_str])
        add_styled_table(doc, mention_headers, mention_rows, ds)

    # D&O context for lagging companies
    if cp.adoption_stance == "LAGGING":
        ctx: Any = doc.add_paragraph(style="DOBody")
        ctx_run: Any = ctx.add_run(
            "D&O Context: LAGGING AI adoption relative to peers increases "
            "competitive displacement risk and potential shareholder "
            "allegations of failure to adapt. Management may face claims "
            "of breaching duty of care by not investing in AI capabilities."
        )
        ctx_run.italic = True
        ctx_run.font.size = ds.size_small
        add_risk_indicator(ctx, "ELEVATED", ds)


def _render_industry_assessment(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render industry-specific narrative assessment."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Industry-Specific Assessment")

    if ai_risk.narrative:
        add_sourced_paragraph(
            doc,
            ai_risk.narrative,
            f"[{ai_risk.narrative_source}, {ai_risk.narrative_confidence} confidence]"
            if ai_risk.narrative_source else "",
            ds,
        )
    else:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Industry-specific AI risk narrative not available.")


def _render_forward_indicators(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render forward-looking AI risk indicators."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Forward-Looking Indicators")

    if not ai_risk.forward_indicators:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No forward indicators identified.")
        return

    for indicator in ai_risk.forward_indicators:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(f"  - {indicator}")

    # D&O context if many indicators
    if len(ai_risk.forward_indicators) >= 3:
        ctx: Any = doc.add_paragraph(style="DOBody")
        ctx_run: Any = ctx.add_run(
            f"D&O Context: {len(ai_risk.forward_indicators)} forward "
            f"indicators identified. Multiple AI transformation signals "
            f"suggest accelerating industry change that may affect "
            f"claim probability within the policy period."
        )
        ctx_run.italic = True
        ctx_run.font.size = ds.size_small


def _render_data_sources(
    doc: Any, ai_risk: AIRiskAssessment, ds: DesignSystem
) -> None:
    """Render data source attribution."""
    if not ai_risk.data_sources:
        return

    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        "Data Sources: " + "; ".join(ai_risk.data_sources)
    )
    run.font.size = ds.size_small
    run.font.color.rgb = ds.color_text_light


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _format_evidence(evidence: list[str], max_items: int = 2) -> str:
    """Format evidence list into a display string."""
    if not evidence:
        return "None"
    return "; ".join(evidence[:max_items])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_section_8(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Section 8: AI Transformation Risk.

    Includes overall AI risk score, sub-dimension table, AI disclosures,
    patent activity, peer comparison, industry assessment narrative,
    forward indicators, and data sources.

    Phase 60-02: Receives context dict from build_template_context().

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    add_section_divider(doc)
    heading: Any = doc.add_paragraph(style="DOHeading1")
    heading.add_run("Section 8: AI Transformation Risk")

    ai_risk = _get_ai_risk(context)
    if ai_risk is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("AI risk assessment unavailable.")
        return

    _render_overview_panel(doc, ai_risk, ds)
    _render_sub_dimensions(doc, ai_risk, ds)
    _render_disclosures(doc, ai_risk.disclosure_data, ds)
    _render_patent_activity(doc, ai_risk.patent_activity, ds)
    _render_peer_comparison(doc, ai_risk, ds)
    _render_industry_assessment(doc, ai_risk, ds)
    _render_forward_indicators(doc, ai_risk, ds)
    _render_data_sources(doc, ai_risk, ds)


__all__ = ["render_section_8"]
