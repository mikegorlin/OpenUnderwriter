"""Section 1 table/visual renderers: snapshot, inherent risk, claim probability, tower.

Extracted from sect1_executive.py to satisfy the 500-line limit.
All functions are called from sect1_executive.render_section_1() orchestrator.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.executive_summary import CompanySnapshot
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_data_table,
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_compact_table_value,
    format_currency,
    format_percentage,
    format_source_trail,
    sector_display_name,
    sv_val,
)
from do_uw.stages.render.peer_context import (
    get_peer_context_line,
)
from do_uw.stages.render.sections.sect1_helpers import (
    build_claim_narrative,
    build_risk_narrative,
    market_cap_decile,
)


def render_snapshot(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render company snapshot table with market cap decile."""
    para: Any = doc.add_paragraph(style="DOHeading3")
    para.add_run("Company Snapshot")

    state = context["_state"]
    snapshot = (
        state.executive_summary.snapshot if state.executive_summary else None
    )
    if snapshot is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Company snapshot not available.")
        return

    rows = _build_snapshot_rows(snapshot, context)
    add_styled_table(doc, ["Attribute", "Value", "Source"], rows, ds)


def _build_snapshot_rows(
    snapshot: CompanySnapshot, context: dict[str, Any]
) -> list[list[str]]:
    """Build snapshot table rows with decile context."""
    state = context["_state"]
    rows: list[list[str]] = []
    rows.append(["Company", snapshot.company_name, ""])
    rows.append(["Ticker", snapshot.ticker, ""])
    rows.append(["Exchange", snapshot.exchange or "N/A", ""])

    # Canonical sector from inherent risk (SIC-derived, mapped via sectors.json)
    sector_label = canonical_sector(context)
    rows.append(["Sector", sector_label, ""])
    # Industry as sub-classification (yfinance industry or SIC description)
    industry = snapshot.industry or "N/A"
    if industry and industry != "N/A" and industry != sector_label:
        rows.append(["Industry", industry, ""])

    # Market cap with decile context and peer percentile
    mcap_str = fmt_sourced_currency(snapshot.market_cap)
    mcap_cite = cite(snapshot.market_cap)
    if snapshot.market_cap:
        _decile, decile_desc = market_cap_decile(snapshot.market_cap.value)
        mcap_str = f"{mcap_str}  [{decile_desc}]"
        # Add peer percentile if benchmark data available
        # TODO(phase-60): move benchmark to context_builders
        peer_line = get_peer_context_line("market_cap", state.benchmark)
        if peer_line:
            mcap_str = f"{mcap_str}  ({peer_line})"
    rows.append(["Market Cap", mcap_str, mcap_cite])

    # Revenue with source
    rev_str = fmt_sourced_currency(snapshot.revenue)
    rev_cite = cite(snapshot.revenue)
    rows.append(["Revenue", rev_str, rev_cite])

    # Employee count -- format with commas, handle raw small numbers
    emp_str = "N/A"
    if snapshot.employee_count:
        raw_count = snapshot.employee_count.value
        # If count seems unreasonably low for a public company, flag it
        emp_str = format_compact_table_value(raw_count)
        if raw_count < 100:
            emp_str = f"{raw_count:,} (verify -- may be in thousands)"
    emp_cite = cite(snapshot.employee_count)
    rows.append(["Employees", emp_str, emp_cite])

    # SIC / GICS / NAICS / FPI / FYE from identity
    sic = snapshot.sic_code or identity_field(context, "sic_code")
    sic_desc = identity_field(context, "sic_description")
    sic_display = sic if sic != "N/A" else "N/A"
    if sic_desc and sic_desc != "N/A":
        sic_display = f"{sic_display} -- {sic_desc}"
    rows.append(["SIC", sic_display, ""])

    gics = "N/A"
    if state.company and state.company.gics_code:
        gics = str(sv_val(state.company.gics_code, "N/A"))
    if gics and gics != "N/A":
        rows.append(["GICS", gics, ""])

    naics = identity_field(context, "naics_code")
    if naics and naics != "N/A":
        rows.append(["NAICS", naics, ""])

    fpi = "Yes" if (state.company and state.company.identity.is_fpi) else "No"
    rows.append(["FPI Status", fpi, ""])
    rows.append(["Fiscal Year End", identity_field(context, "fiscal_year_end"), ""])

    return rows


def render_inherent_risk(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render inherent risk with decile, calculation chain, and narrative."""
    para: Any = doc.add_paragraph(style="DOHeading3")
    para.add_run("Inherent Risk Baseline")

    state = context["_state"]
    risk = (
        state.executive_summary.inherent_risk
        if state.executive_summary
        else None
    )
    if risk is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Inherent risk baseline not available.")
        return

    # Market cap decile context
    mcap = None
    if state.executive_summary and state.executive_summary.snapshot:
        snap = state.executive_summary.snapshot
        if snap.market_cap:
            mcap = snap.market_cap.value
    _decile, decile_desc = market_cap_decile(mcap)

    # Risk decomposition table showing the calculation chain
    rows: list[list[str]] = [
        ["Market Cap Tier", f"{risk.market_cap_tier}  [{decile_desc}]"],
        [
            "Sector",
            f"{risk.sector_name} (Base rate: "
            f"{format_percentage(risk.sector_base_rate_pct)})",
        ],
        [
            "Size Adjustment",
            f"{risk.market_cap_multiplier:.2f}x ({risk.market_cap_tier} cap multiplier) "
            f"-> {format_percentage(risk.market_cap_adjusted_rate_pct)}",
        ],
        [
            "Score Adjustment",
            f"{risk.score_multiplier:.2f}x (quality score multiplier) "
            f"-> {format_percentage(risk.company_adjusted_rate_pct)}",
        ],
    ]
    add_styled_table(doc, ["Component", "Value"], rows, ds)

    # Severity scenario summary
    sev_rows = [
        ("25th (favorable)", risk.severity_range_25th),
        ("50th (median)", risk.severity_range_50th),
        ("75th (adverse)", risk.severity_range_75th),
        ("95th (catastrophic)", risk.severity_range_95th),
    ]
    sev_table_rows: list[list[str]] = []
    for label, val in sev_rows:
        sev_table_rows.append([
            label,
            format_currency(val * 1_000_000, compact=True),
        ])
    add_styled_table(doc, ["Severity Percentile", "Settlement Estimate"], sev_table_rows, ds)

    # Read pre-computed narrative, fallback to local computation
    # TODO(phase-60): move benchmark to context_builders
    narrative = (
        state.benchmark.risk_narrative
        if state.benchmark and state.benchmark.risk_narrative
        else build_risk_narrative(risk, state)
    )
    note: Any = doc.add_paragraph(style="DOBody")
    note.add_run(narrative)

    if risk.methodology_note:
        calib: Any = doc.add_paragraph(style="DOCaption")
        calib.add_run(f"Note: {risk.methodology_note}")


def render_claim_probability(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render claim probability with context narrative."""
    para: Any = doc.add_paragraph(style="DOHeading3")
    para.add_run("Claim Probability")

    state = context["_state"]
    cp = state.scoring.claim_probability if state.scoring else None
    if cp is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Claim probability not available.")
        return

    rows: list[list[str]] = [
        ["Band", cp.band.value],
        ["Company Rate", f"{cp.range_low_pct:.1f}% - {cp.range_high_pct:.1f}%"],
        ["Industry Base Rate", format_percentage(cp.industry_base_rate_pct)],
    ]

    sev = state.scoring.severity_scenarios if state.scoring else None
    if sev and sev.scenarios:
        for sc in sev.scenarios:
            rows.append([
                f"Severity {sc.label.capitalize()}",
                format_currency(sc.total_exposure, compact=True),
            ])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Band indicator
    band_para: Any = doc.add_paragraph(style="DOBody")
    band_para.add_run(f"Probability Band: {cp.band.value}")
    add_band_indicator(band_para, cp.band.value, ds)

    # Read pre-computed narrative, fallback to local computation
    # TODO(phase-60): move benchmark to context_builders
    claim_ctx = (
        state.benchmark.claim_narrative
        if state.benchmark and state.benchmark.claim_narrative
        else build_claim_narrative(state)
    )
    if claim_ctx:
        ctx_para: Any = doc.add_paragraph(style="DOBody")
        ctx_para.add_run(claim_ctx)


def render_tower_recommendation(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render tower recommendation with layer detail."""
    para: Any = doc.add_paragraph(style="DOHeading3")
    para.add_run("Tower Recommendation")

    state = context["_state"]
    tr = state.scoring.tower_recommendation if state.scoring else None
    if tr is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Tower recommendation not available.")
        return

    rows: list[list[str]] = [
        ["Position", tr.recommended_position.value.replace("_", " ").title()],
        ["Min Attachment", tr.minimum_attachment or "N/A"],
        ["Side A/DIC", tr.side_a_assessment or "N/A"],
    ]
    add_data_table(doc, ["Metric", "Value"], rows, ds)

    if tr.layers:
        layer_rows = [
            [
                la.position.value,
                la.risk_assessment or "N/A",
                la.premium_guidance or "N/A",
            ]
            for la in tr.layers
        ]
        add_styled_table(
            doc,
            ["Layer", "Risk Assessment", "Premium Guidance"],
            layer_rows,
            ds,
        )


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def fmt_sourced_currency(sv: Any) -> str:
    """Format a SourcedValue as compact currency, or N/A."""
    return "N/A" if sv is None else format_currency(sv.value, compact=True)


def cite(sv: Any) -> str:
    """Format a SourcedValue's source trail, or empty string."""
    return "" if sv is None else format_source_trail(sv)


def canonical_sector(context: dict[str, Any]) -> str:
    """Get the canonical sector display name from the best available source.

    Priority: yfinance sector -> SIC code -> sic_to_sector() -> "N/A".
    yfinance provides more accurate classification for generic SIC codes.
    """
    state = context["_state"]
    # Prefer yfinance sector (most accurate)
    from do_uw.stages.render.context_builders.company import _get_yfinance_sector
    yf_sector = _get_yfinance_sector(state)
    if yf_sector:
        return yf_sector
    # Re-derive from SIC code at render time
    if state.company and state.company.identity:
        ident = state.company.identity
        if ident.sic_code and ident.sic_code.value:
            from do_uw.stages.resolve.sec_identity import sic_to_sector

            code = sic_to_sector(str(ident.sic_code.value))
            return sector_display_name(code)
    # Fallback: inherent risk sector name from pipeline
    if state.executive_summary and state.executive_summary.inherent_risk:
        name = state.executive_summary.inherent_risk.sector_name
        if name:
            return name
    if state.company and state.company.identity.sector:
        code = state.company.identity.sector.value
        return sector_display_name(code)
    return "N/A"


def identity_field(context: dict[str, Any], field: str) -> str:
    """Get a field from company identity as string."""
    state = context["_state"]
    if not state.company:
        return "N/A"
    sv = getattr(state.company.identity, field, None)
    if sv is None:
        return "N/A"
    return str(sv_val(sv, "N/A"))


def build_factor_breakdown(context: dict[str, Any]) -> str:
    """Build factor breakdown summary string."""
    state = context["_state"]
    if not state.scoring or not state.scoring.factor_scores:
        return ""
    return ", ".join(
        f"{fs.factor_id}: {fs.points_deducted:.1f}"
        for fs in state.scoring.factor_scores
    )


def build_ceiling_line(context: dict[str, Any]) -> str:
    """Build ceiling line showing which red flag capped the score."""
    from do_uw.stages.render.context_builders.scoring import (
        _should_suppress_insolvency_crf_flag,
    )

    state = context["_state"]
    if not state.scoring or not state.scoring.red_flags:
        return ""
    triggered = [
        rf for rf in state.scoring.red_flags
        if rf.triggered and not _should_suppress_insolvency_crf_flag(state, rf)
    ]
    if not triggered:
        return ""
    lowest = min(
        (rf for rf in triggered if rf.ceiling_applied is not None),
        key=lambda rf: rf.ceiling_applied or 999,
        default=None,
    )
    if lowest and lowest.ceiling_applied is not None:
        return (
            f"Capped at {lowest.ceiling_applied} by "
            f"{lowest.flag_id} ({lowest.flag_name})"
        )
    return ""


_TIER_RISK: dict[str, str] = {
    "WIN": "MODERATE", "WANT": "MODERATE", "WRITE": "ELEVATED",
    "WATCH": "HIGH", "WALK": "CRITICAL", "NO_TOUCH": "CRITICAL",
}
_BAND_RISK: dict[str, str] = {
    "LOW": "MODERATE", "MODERATE": "ELEVATED", "ELEVATED": "HIGH",
    "HIGH": "CRITICAL", "VERY_HIGH": "CRITICAL",
}


def add_tier_indicator(para: Any, tier_name: str, ds: DesignSystem) -> None:
    """Add tier-appropriate risk indicator to paragraph."""
    add_risk_indicator(para, _TIER_RISK.get(tier_name, "NEUTRAL"), ds)


def add_band_indicator(para: Any, band_name: str, ds: DesignSystem) -> None:
    """Add band-appropriate risk indicator to paragraph."""
    add_risk_indicator(para, _BAND_RISK.get(band_name, "NEUTRAL"), ds)


__all__ = [
    "add_band_indicator",
    "add_tier_indicator",
    "build_ceiling_line",
    "build_factor_breakdown",
    "canonical_sector",
    "cite",
    "fmt_sourced_currency",
    "identity_field",
    "render_claim_probability",
    "render_inherent_risk",
    "render_snapshot",
    "render_tower_recommendation",
]
