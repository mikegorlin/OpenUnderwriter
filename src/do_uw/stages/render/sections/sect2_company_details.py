"""Section 2 details: revenue segments, geographic footprint,
customer/supplier concentration, and D&O exposure mapping.

Split from sect2_company.py for the 500-line limit.
Provides render_company_details() called by sect2_company.
Delegates D&O exposure rendering to sect2_company_exposure.py.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_citation,
    format_currency,
)
from do_uw.stages.render.sections.sect2_company_exposure import (
    render_do_exposure_mapping,
)


def render_company_details(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render detailed company data: revenue, geography, concentration, D&O."""
    _render_revenue_segments(doc, context, ds)
    _render_geographic_footprint(doc, context, ds)
    _render_concentration(doc, context, ds)
    render_do_exposure_mapping(doc, context, ds)


def _render_revenue_segments(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render revenue segments table with source citations."""
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
        rev_val = seg.get("revenue")
        pct_val = seg.get("percentage")
        if pct_val is None and total_rev > 0 and rev_val is not None:
            pct_val = float(rev_val) / total_rev * 100
        growth_val = seg.get("yoy_growth", seg.get("growth"))
        rows.append([
            name,
            _safe_currency(rev_val),
            _safe_pct(pct_val),
            _safe_pct(growth_val) if growth_val is not None else "N/A",
            format_citation(sv_seg),
        ])

    add_styled_table(
        doc,
        ["Segment", "Revenue", "% of Total", "YoY Growth", "Source"],
        rows,
        ds,
    )


def _render_geographic_footprint(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render geographic footprint with jurisdiction analysis.

    Handles two data shapes from extraction:
    - Exhibit 21 style: {jurisdiction, subsidiary_count}
    - Revenue style: {region/geography, revenue, percentage}

    The section purpose is to show WHERE the company operates,
    identify geographic CONCENTRATIONS, flag HIGH-RISK jurisdictions,
    and highlight multi-jurisdiction regulatory exposure.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Geographic Footprint")

    state = context["_state"]
    geo = state.company.geographic_footprint if state.company else []
    if not geo:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Geographic footprint data not available.")
        return

    # Detect data shape: Exhibit 21 (jurisdiction/subsidiary_count) vs revenue
    first_val = geo[0].value if geo else {}
    is_subsidiary_data = "subsidiary_count" in first_val or "jurisdiction" in first_val

    if is_subsidiary_data:
        _render_geo_subsidiary(doc, geo, context, ds)
    else:
        _render_geo_revenue(doc, geo, context, ds)


def _render_geo_subsidiary(
    doc: Any, geo: list[Any], context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render geographic footprint from Exhibit 21 subsidiary data."""
    # Read pre-computed high-risk jurisdiction names from ANALYZE density
    high_risk_names = _get_high_risk_names(context)

    # Parse and aggregate
    us_states: list[tuple[str, float]] = []
    international: list[tuple[str, float]] = []
    total_subs = 0.0
    high_risk_found: list[str] = []

    _US_STATES = {
        "delaware", "texas", "california", "new york", "florida",
        "new jersey", "illinois", "virginia", "pennsylvania", "ohio",
        "georgia", "massachusetts", "colorado", "maryland", "connecticut",
        "louisiana", "nevada", "wyoming", "washington", "michigan",
        "minnesota", "arizona", "north carolina", "indiana", "tennessee",
        "missouri", "oregon", "wisconsin", "oklahoma", "iowa",
        "south carolina", "kentucky", "montana", "utah", "hawaii",
        "alabama", "nebraska", "idaho", "new hampshire", "arkansas",
        "mississippi", "new mexico", "west virginia", "north dakota",
        "south dakota", "maine", "vermont", "rhode island", "alaska",
        "district of columbia",
    }

    for sv_geo in geo:
        g = sv_geo.value
        jurisdiction = str(
            g.get("jurisdiction", g.get("region", g.get("geography", "")))
        )
        if not jurisdiction or jurisdiction.lower() in ("unknown", "n/a", ""):
            continue
        # Skip obviously malformed entries (concatenated text from bad parsing)
        if len(jurisdiction) > 50:
            continue

        count_raw = g.get("subsidiary_count", g.get("count", 1))
        try:
            count = float(count_raw)
        except (ValueError, TypeError):
            count = 1.0

        total_subs += count

        # Classify as US state or international
        if jurisdiction.lower() in _US_STATES:
            us_states.append((jurisdiction, count))
        else:
            international.append((jurisdiction, count))

        # Check pre-computed high-risk classification
        if jurisdiction.lower() in high_risk_names:
            high_risk_found.append(jurisdiction)

    if total_subs == 0:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Geographic footprint data not available.")
        return

    # Sort by subsidiary count descending
    us_states.sort(key=lambda x: x[1], reverse=True)
    international.sort(key=lambda x: x[1], reverse=True)

    # Build summary rows: top US states + all international
    rows: list[list[str]] = []
    intl_total = sum(c for _, c in international)

    # Top US states (show top 5, aggregate rest)
    for name, count in us_states[:5]:
        pct = (count / total_subs) * 100
        risk = " [HIGH RISK]" if name.lower() in high_risk_names else ""
        rows.append([f"{name}{risk}", f"{int(count)}", f"{pct:.1f}%", "US"])

    if len(us_states) > 5:
        other_us = sum(c for _, c in us_states[5:])
        pct = (other_us / total_subs) * 100
        rows.append([
            f"Other US States ({len(us_states) - 5})",
            f"{int(other_us)}", f"{pct:.1f}%", "US",
        ])

    # International jurisdictions (show all, they're the interesting ones)
    for name, count in international[:15]:
        pct = (count / total_subs) * 100
        risk = " [HIGH RISK]" if name.lower() in high_risk_names else ""
        rows.append([f"{name}{risk}", f"{int(count)}", f"{pct:.1f}%", "Int'l"])

    if len(international) > 15:
        other_intl = sum(c for _, c in international[15:])
        pct = (other_intl / total_subs) * 100
        rows.append([
            f"Other Int'l ({len(international) - 15})",
            f"{int(other_intl)}", f"{pct:.1f}%", "Int'l",
        ])

    add_styled_table(
        doc,
        ["Jurisdiction", "Subsidiaries", "% of Total", "Region"],
        rows,
        ds,
    )

    # Concentration summary
    intl_pct = (intl_total / total_subs) * 100 if total_subs > 0 else 0
    summary: Any = doc.add_paragraph(style="DOCaption")
    summary.add_run(
        f"Total: {int(total_subs)} subsidiaries across "
        f"{len(us_states)} US states and {len(international)} "
        f"international jurisdictions. International exposure: "
        f"{intl_pct:.0f}% of entity footprint. "
        "Multi-jurisdiction operations increase regulatory, tax, "
        "and litigation complexity for D&O exposure."
    )

    # High-risk jurisdiction callout (using pre-computed classification)
    if high_risk_found:
        risk_para: Any = doc.add_paragraph(style="DOBody")
        run: Any = risk_para.add_run(
            f"D&O Alert: Operations in high-risk jurisdictions: "
            f"{', '.join(high_risk_found)}. "
            "Sanctions compliance and regulatory exposure elevated."
        )
        run.bold = True
        add_risk_indicator(risk_para, "HIGH", ds)


def _render_geo_revenue(
    doc: Any, geo: list[Any], context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render geographic footprint from revenue-based data."""
    # Read pre-computed high-risk jurisdiction names from ANALYZE density
    high_risk_names = _get_high_risk_names(context)

    rows: list[list[str]] = []
    intl_pct_total = 0.0
    high_risk_found: list[str] = []

    for sv_geo in geo:
        g = sv_geo.value
        region = str(g.get("jurisdiction", g.get("region", g.get("geography", "Unknown"))))
        if region.lower() in ("unknown", "n/a", ""):
            continue

        rev_str = _safe_currency(g.get("revenue"))
        pct_val = g.get("percentage")
        pct_str = _safe_pct(pct_val)

        # Track international percentage
        region_lower = region.lower()
        if region_lower not in ("united states", "us", "domestic", "u.s."):
            try:
                intl_pct_total += float(pct_val) if pct_val else 0.0
            except (ValueError, TypeError):
                pass

        # Check pre-computed high-risk classification
        risk = " [HIGH RISK]" if region_lower in high_risk_names else ""
        if risk:
            high_risk_found.append(region)

        rows.append([region + risk, rev_str, pct_str])

    if not rows:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Geographic footprint data not available.")
        return

    add_styled_table(doc, ["Region", "Revenue", "% of Total"], rows, ds)

    if intl_pct_total > 0:
        intl_note: Any = doc.add_paragraph(style="DOCaption")
        intl_note.add_run(
            f"International revenue exposure: ~{intl_pct_total:.1f}% of total. "
            "Multi-jurisdiction operations increase regulatory and "
            "litigation complexity."
        )

    if high_risk_found:
        risk_para: Any = doc.add_paragraph(style="DOBody")
        run: Any = risk_para.add_run(
            f"D&O Alert: Operations in high-risk jurisdictions: "
            f"{', '.join(high_risk_found)}. "
            "Sanctions compliance and regulatory exposure elevated."
        )
        run.bold = True
        add_risk_indicator(risk_para, "HIGH", ds)


def _render_concentration(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render customer/supplier concentration with D&O context."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Customer & Supplier Concentration")

    state = context["_state"]
    customers = state.company.customer_concentration if state.company else []
    suppliers = state.company.supplier_concentration if state.company else []

    if not customers and not suppliers:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Concentration data not available from filings.")
        return

    # Customer concentration
    if customers:
        cust_rows: list[list[str]] = []
        for sv_cust in customers:
            c = sv_cust.value
            name = str(c.get("name", c.get("customer", "Undisclosed")))
            pct = _safe_pct(c.get("percentage", c.get("revenue_pct")))
            cust_rows.append([name, pct, format_citation(sv_cust)])

        add_styled_table(
            doc, ["Customer", "% of Revenue", "Source"], cust_rows, ds
        )

        # D&O context for concentration risk
        _add_concentration_context(doc, customers, "customer", ds)

    # Supplier concentration
    if suppliers:
        sup_heading: Any = doc.add_paragraph(style="DOHeading3")
        sup_heading.add_run("Key Suppliers")
        sup_rows: list[list[str]] = []
        for sv_sup in suppliers:
            s = sv_sup.value
            name = str(s.get("name", s.get("supplier", "Undisclosed")))
            dep = str(s.get("dependency", s.get("description", "N/A")))
            sup_rows.append([name, dep, format_citation(sv_sup)])

        add_styled_table(
            doc, ["Supplier", "Dependency", "Source"], sup_rows, ds
        )


def _add_concentration_context(
    doc: Any,
    customers: list[Any],
    label: str,
    ds: DesignSystem,
) -> None:
    """Add D&O context note for concentration risk."""
    _ = ds  # available for future risk indicator use
    # Check if any customer is >10% of revenue
    high_conc = False
    for sv_cust in customers:
        c = sv_cust.value
        pct_raw = c.get("percentage", c.get("revenue_pct"))
        try:
            if pct_raw and float(pct_raw) > 10.0:
                high_conc = True
                break
        except (ValueError, TypeError):
            pass

    if high_conc:
        note: Any = doc.add_paragraph(style="DOCaption")
        note.add_run(
            f"D&O Note: {label.capitalize()} concentration >10% creates "
            "binary event risk. Loss of a major customer/contract can "
            "trigger stock drop and securities litigation."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_high_risk_names(context: dict[str, Any]) -> set[str]:
    """Read pre-computed high-risk jurisdiction names from ANALYZE density.

    Returns a set of lowercased jurisdiction names flagged as high-risk
    in the company section density concerns. If density not computed,
    returns empty set (no classification in render).
    """
    state = context["_state"]
    high_risk: set[str] = set()
    if state.analysis is None:
        return high_risk
    company_density = state.analysis.section_densities.get("company")
    if company_density is None:
        return high_risk
    for concern in company_density.concerns:
        if concern.startswith("high_risk_jurisdiction:"):
            high_risk.add(concern.split(":", 1)[1].lower())
    return high_risk


def _safe_currency(val: Any) -> str:
    """Parse currency value (numeric or pre-formatted string)."""
    if val is None:
        return "N/A"
    try:
        return format_currency(float(val), compact=True)
    except (ValueError, TypeError):
        return str(val)


def _safe_pct(val: Any) -> str:
    """Parse percentage value (numeric or pre-formatted string)."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return str(val)


__all__ = ["render_company_details"]
