"""Section 2 v6.0 subsection renderers for Word/PDF output.

Renders business model, operational complexity, corporate events,
environment assessment, sector risk, and structural complexity
subsections in the Word document. All data comes from the shared
context dict built by context_builders/company.py.

Phase 100-02: Word/PDF parity with HTML for all v6.0 dimensions.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)


# ---------------------------------------------------------------------------
# Level -> risk indicator mapping (shared)
# ---------------------------------------------------------------------------

_LEVEL_TO_RISK: dict[str, str] = {
    "HIGH": "HIGH",
    "MODERATE": "MODERATE",
    "LOW": "NEUTRAL",
    "NONE": "NEUTRAL",
}


def _level_indicator(para: Any, level: str, ds: DesignSystem) -> None:
    """Append a risk indicator badge after level text."""
    risk = _LEVEL_TO_RISK.get(level.upper(), "NEUTRAL")
    add_risk_indicator(para, risk, ds)


# ---------------------------------------------------------------------------
# Business Model Profile (BMOD dimensions)
# ---------------------------------------------------------------------------


def render_business_model(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Business Model Profile subsection in Word output."""
    company = context.get("company") or {}
    bm = company.get("business_model")
    if not bm:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Business Model Profile")

    # KV table rows
    rows: list[list[str]] = []

    # BMOD-01: Revenue model
    rev_model = bm.get("revenue_model_type")
    if rev_model:
        rows.append(["Revenue Model", str(rev_model)])

    # BMOD-02: Concentration risk
    conc_level = bm.get("concentration_level", "NONE")
    if conc_level and conc_level != "NONE":
        flags_str = "; ".join(bm.get("concentration_flags", []))
        detail = f"{conc_level} (Score: {bm.get('concentration_score', 0)}/3)"
        if flags_str:
            detail += f" - {flags_str}"
        rows.append(["Concentration Risk", detail])

    # BMOD-03: Key person
    kp = bm.get("key_person")
    if kp:
        parts: list[str] = [f"{kp.get('risk_level', 'LOW')} (Score: {kp.get('risk_score', 0)}/3)"]
        details: list[str] = []
        if kp.get("is_founder_led"):
            details.append("Founder-led")
        tenure = kp.get("ceo_tenure_years")
        if tenure is not None:
            details.append(f"CEO tenure: {tenure}yr")
        succession = kp.get("has_succession_plan")
        if succession is not None:
            details.append(f"Succession: {'Yes' if succession else 'No'}")
        if details:
            parts.append(" | ".join(details))
        rows.append(["Key Person Risk", " - ".join(parts)])

    # BMOD-05: Disruption
    disruption = bm.get("disruption")
    if disruption:
        level = disruption.get("level", "LOW")
        threat_count = disruption.get("threat_count", 0)
        threats = disruption.get("threats", [])
        detail = level
        if threat_count:
            detail += f" ({threat_count} threat{'s' if threat_count > 1 else ''})"
        if threats:
            detail += f" - {'; '.join(str(t) for t in threats)}"
        rows.append(["Disruption Risk", detail])

    if rows:
        add_styled_table(doc, ["Dimension", "Assessment"], rows, ds)

    # BMOD-04: Segment Lifecycle table
    lifecycle = bm.get("lifecycle", [])
    if lifecycle:
        lc_heading: Any = doc.add_paragraph(style="DOHeading3")
        lc_heading.add_run("Segment Lifecycle")
        lc_rows = [
            [seg["name"], seg["stage"], seg["growth_rate"]]
            for seg in lifecycle
        ]
        add_styled_table(
            doc, ["Segment", "Stage", "Growth Rate"], lc_rows, ds,
        )

    # BMOD-06: Segment Margins table
    margins = bm.get("segment_margins", [])
    if margins:
        mg_heading: Any = doc.add_paragraph(style="DOHeading3")
        mg_heading.add_run("Segment Margins")
        mg_rows = [
            [seg["name"], seg["margin"], seg["prior_margin"], seg["change_bps"]]
            for seg in margins
        ]
        add_styled_table(
            doc, ["Segment", "Margin", "Prior", "Change (bps)"], mg_rows, ds,
        )


# ---------------------------------------------------------------------------
# Operational Complexity (Phase 99 OPS signals)
# ---------------------------------------------------------------------------


def render_operational_complexity(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Operational Complexity subsection in Word output."""
    company = context.get("company") or {}
    if not company.get("has_ops_complexity"):
        return
    ops = company.get("operational_complexity_signals", {})
    if not ops:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Operational Complexity")

    # Composite score line
    score_para: Any = doc.add_paragraph(style="DOBody")
    run: Any = score_para.add_run(
        f"Complexity Score: {ops.get('composite_score', 0)}/20 "
        f"-- {ops.get('composite_level', 'LOW')}"
    )
    run.bold = True
    _level_indicator(score_para, ops.get("composite_level", "LOW"), ds)

    # Component KV table
    total_emp = ops.get("total_employees")
    emp_str = f"{total_emp:,}" if total_emp else "N/A"
    intl_pct = ops.get("international_pct", 0)
    if intl_pct:
        emp_str += f" ({intl_pct}% international)"

    rows: list[list[str]] = [
        ["Jurisdictions", f"{ops.get('jurisdiction_count', 0)} ({ops.get('high_reg_count', 0)} high-regulatory)"],
        ["Workforce", emp_str],
    ]
    unionized = ops.get("unionized_pct", 0)
    if unionized:
        rows.append(["Unionized", f"{unionized}%"])
    rows.extend([
        ["Segments", str(ops.get("segment_count", 0))],
        ["Geographic Concentration", f"{ops.get('geographic_concentration_score', 0)}/100"],
        ["Supply Chain", str(ops.get("supply_chain_depth", "N/A"))],
        ["Overall Resilience", str(ops.get("overall_assessment", "N/A"))],
    ])
    add_styled_table(doc, ["Component", "Value"], rows, ds)

    # Structural indicators
    indicators = ops.get("indicators", [])
    if indicators:
        ind_para: Any = doc.add_paragraph(style="DOCaption")
        parts = []
        for ind in indicators:
            mark = "[X]" if ind.get("present") else "[ ]"
            parts.append(f"{mark} {ind['name']}")
        ind_para.add_run("Structural Indicators: " + "  |  ".join(parts))


# ---------------------------------------------------------------------------
# Corporate Events & Transaction Risk (Phase 100)
# ---------------------------------------------------------------------------


def render_corporate_events(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Corporate Events & Transaction Risk subsection in Word output."""
    company = context.get("company") or {}
    if not company.get("has_corporate_events"):
        return
    events = company.get("corporate_events_signals", {})
    if not events:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Corporate Events & Transaction Risk")

    rows: list[list[str]] = []

    # M&A Activity
    ma = events.get("ma_activity", {})
    if ma:
        parts: list[str] = []
        parts.append(f"{ma.get('level', 'LOW')} (Score: {ma.get('score', 0)}/4)")
        details: list[str] = []
        acq_count = ma.get("acquisition_count", 0)
        details.append(f"{acq_count} acquisition year{'s' if acq_count != 1 else ''}")
        if ma.get("is_serial_acquirer"):
            details.append("Serial Acquirer")
        gw = ma.get("goodwill_growth_rate", "N/A")
        if gw != "N/A":
            details.append(f"Goodwill growth: {gw}")
        ar = ma.get("acquisition_to_revenue", "N/A")
        if ar != "N/A":
            details.append(f"Acq/Rev: {ar}")
        rows.append(["M&A Activity", f"{parts[0]} | {' | '.join(details)}"])

    # IPO / Offering
    ipo = events.get("ipo_exposure", {})
    if ipo:
        yrs = ipo.get("years_public", "N/A")
        detail = f"{ipo.get('level', 'LOW')} - {yrs} year{'s' if yrs != 1 else ''} public"
        if ipo.get("in_ipo_window"):
            detail += " | Within IPO litigation window"
        rows.append(["IPO / Offering Exposure", detail])

    # Restatements
    rest = events.get("restatements", {})
    if rest:
        parts_r: list[str] = [rest.get("level", "MODERATE")]
        if rest.get("has_restatement"):
            parts_r.append("Restatement detected")
        if rest.get("material_weakness"):
            parts_r.append("Material weakness")
        rows.append(["Restatement History", " | ".join(parts_r)])

    if rows:
        add_styled_table(doc, ["Event Type", "Assessment"], rows, ds)

    # Capital changes (bullet list)
    cap_changes = events.get("capital_changes", [])
    if cap_changes:
        cap_heading: Any = doc.add_paragraph(style="DOBody")
        cap_run: Any = cap_heading.add_run("Capital Structure Changes:")
        cap_run.bold = True
        for change in cap_changes:
            bp: Any = doc.add_paragraph(style="DOBody")
            bp.add_run(f"  - {change}")

    # Business changes (bullet list)
    biz_changes = events.get("business_changes", [])
    if biz_changes:
        biz_heading: Any = doc.add_paragraph(style="DOBody")
        biz_run: Any = biz_heading.add_run("Business Changes:")
        biz_run.bold = True
        for change in biz_changes:
            bp = doc.add_paragraph(style="DOBody")
            bp.add_run(f"  - {change}")


# ---------------------------------------------------------------------------
# Environment Assessment (Phase 97 ENVR signals)
# ---------------------------------------------------------------------------


def render_environment_assessment(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render External Environment Assessment subsection in Word output."""
    company = context.get("company") or {}
    if not company.get("has_environment_data"):
        return
    env = company.get("environment_assessment", {})
    if not env:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("External Environment Assessment")

    _ENV_LABELS = [
        ("regulatory_intensity", "Regulatory Intensity"),
        ("geopolitical_risk", "Geopolitical Exposure"),
        ("esg_gap", "ESG Commitment Gap"),
        ("cyber_risk", "Cyber Risk Profile"),
        ("macro_sensitivity", "Macro Sensitivity"),
    ]

    rows: list[list[str]] = []
    for key, label in _ENV_LABELS:
        sig = env.get(key, {})
        if sig:
            level = sig.get("level", "LOW")
            details = sig.get("details", "")
            value = level
            if details:
                value += f" - {details}"
            rows.append([label, value])

    if rows:
        add_styled_table(doc, ["Signal", "Assessment"], rows, ds)


# ---------------------------------------------------------------------------
# Sector Risk Classification (Phase 98 SECT signals)
# ---------------------------------------------------------------------------


def render_sector_risk(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Sector Risk Classification subsection in Word output."""
    company = context.get("company") or {}
    if not company.get("has_sector_risk"):
        return
    sect = company.get("sector_risk", {})
    if not sect:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Sector Risk Classification")

    rows: list[list[str]] = []

    # Hazard tier
    hazard = sect.get("hazard", {})
    if hazard and hazard.get("tier"):
        detail = hazard["tier"]
        filing_rate = hazard.get("filing_rate", "")
        if filing_rate:
            detail += f" ({filing_rate})"
        ctx = hazard.get("context", "")
        if ctx:
            detail += f" - {ctx}"
        rows.append(["Sector Hazard Tier", detail])

    # Claim patterns
    claims = sect.get("claims", {})
    theories = claims.get("theories", [])
    if theories:
        industry_group = claims.get("industry_group", "")
        label = "Common Claim Theories"
        if industry_group:
            label += f" ({industry_group})"
        theory_lines = []
        for t in theories:
            theory_name = t.get("theory", "") if isinstance(t, dict) else str(t)
            legal_basis = t.get("legal_basis", "") if isinstance(t, dict) else ""
            line = theory_name
            if legal_basis:
                line += f" [{legal_basis}]"
            theory_lines.append(line)
        rows.append([label, "; ".join(theory_lines)])

    # Regulatory overlay
    reg = sect.get("regulatory", {})
    regulators = reg.get("regulators", [])
    if regulators:
        detail = f"{reg.get('intensity', 'Low')} - {', '.join(str(r) for r in regulators)}"
        trend = reg.get("trend", "")
        if trend:
            detail += f" ({trend})"
        rows.append(["Sector Regulatory Baseline", detail])

    # Peer comparison
    peer = sect.get("peer", {})
    dimensions = peer.get("dimensions", [])
    if dimensions:
        sector_name = peer.get("sector_name", "")
        label = "Peer Risk Comparison"
        if sector_name:
            label += f" ({sector_name})"
        dim_lines = []
        for dim in dimensions:
            line = f"{dim['name']}: {dim['company_value']} vs median {dim['median']}"
            if dim.get("is_outlier"):
                line += " [OUTLIER]"
            dim_lines.append(line)
        if peer.get("outlier_count", 0) == 0:
            dim_lines.append("Within sector norms")
        rows.append([label, "; ".join(dim_lines)])

    if rows:
        add_styled_table(doc, ["Dimension", "Assessment"], rows, ds)


# ---------------------------------------------------------------------------
# Structural Complexity (Phase 96/100)
# ---------------------------------------------------------------------------


def render_structural_complexity(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Structural Complexity subsection in Word output."""
    company = context.get("company") or {}
    if not company.get("has_structural_complexity"):
        return
    sc = company.get("structural_complexity_signals", {})
    if not sc:
        return

    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Structural Complexity")

    _SC_DIMENSIONS = [
        ("disclosure_complexity", "Disclosure Complexity", "score"),
        ("nongaap", "Non-GAAP Usage", "count"),
        ("related_parties", "Related Party Density", "count"),
        ("obs_exposure", "Off-Balance-Sheet Exposure", "score"),
        ("holding_structure", "Holding Structure Depth", "count"),
    ]

    rows: list[list[str]] = []
    for key, label, count_key in _SC_DIMENSIONS:
        dim = sc.get(key, {})
        if not dim:
            continue
        level = dim.get("level", "LOW")
        count_val = dim.get(count_key, 0)
        detail = level
        if count_val:
            detail += f" ({count_val})"

        # Extra detail for disclosure complexity
        if key == "disclosure_complexity":
            sub_parts: list[str] = []
            rf = dim.get("risk_factor_count")
            if rf:
                sub_parts.append(f"Risk factors: {rf}")
            ca = dim.get("critical_accounting_count")
            if ca:
                sub_parts.append(f"Critical accounting: {ca}")
            fls = dim.get("fls_density")
            if fls:
                sub_parts.append(f"FLS density: {fls}")
            if sub_parts:
                detail += f" - {' | '.join(sub_parts)}"

        rows.append([label, detail])

    if rows:
        add_styled_table(doc, ["Dimension", "Assessment"], rows, ds)


# ---------------------------------------------------------------------------
# Master dispatcher
# ---------------------------------------------------------------------------


def render_v6_subsections(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render all v6.0 subsections in order.

    Called from sect2_company.render_section_2() to add new dimensions
    between subsidiary summary and peer comparison.
    """
    render_business_model(doc, context, ds)
    render_operational_complexity(doc, context, ds)
    render_corporate_events(doc, context, ds)
    render_environment_assessment(doc, context, ds)
    render_sector_risk(doc, context, ds)
    render_structural_complexity(doc, context, ds)


__all__ = [
    "render_business_model",
    "render_corporate_events",
    "render_environment_assessment",
    "render_operational_complexity",
    "render_sector_risk",
    "render_structural_complexity",
    "render_v6_subsections",
]
