"""Section 6 continuation: derivative suits, regulatory proceedings,
industry claim patterns, and statute of limitations map.

Split from sect6_litigation.py for 500-line compliance. Defense
assessment, contingencies, and whistleblower moved to sect6_defense.py.

Phase 60-02: Receives context dict; extracts litigation via _state escape hatch.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.litigation import LitigationLandscape
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_currency,
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
# Derivative Suits
# ---------------------------------------------------------------------------


def _render_derivative_suits(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render derivative suits table."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Derivative Suits")

    suits = lit.derivative_suits
    if not suits:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No derivative suit history found.")
        return

    headers = ["Case Name", "Filing Date", "Status", "Court", "Settlement"]
    rows: list[list[str]] = []
    for suit in suits:
        case_name = str(sv_val(suit.case_name, "N/A"))
        filing_date = (
            str(suit.filing_date.value)
            if suit.filing_date is not None
            else "N/A"
        )
        status = str(sv_val(suit.status, "N/A"))
        court = str(sv_val(suit.court, "N/A"))
        settlement = format_currency(
            suit.settlement_amount.value
            if suit.settlement_amount is not None
            else None,
            compact=True,
        )
        rows.append([case_name, filing_date, status, court, settlement])

    add_styled_table(doc, headers, rows, ds)

    # D&O context
    active = [
        s for s in suits
        if s.status is not None and s.status.value.upper() == "ACTIVE"
    ]
    if active:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: {len(active)} active derivative suit(s). "
            f"Derivative claims trigger Side A coverage when company "
            f"cannot indemnify directors. Often follow SCA filings."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# Regulatory Proceedings
# ---------------------------------------------------------------------------


def _render_regulatory_proceedings(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render regulatory proceedings table."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Regulatory Proceedings")

    proceedings = lit.regulatory_proceedings
    if not proceedings:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No regulatory proceedings found.")
        return

    headers = ["Agency", "Type", "Status"]
    rows: list[list[str]] = []
    for proc_sv in proceedings:
        proc_dict = proc_sv.value
        agency = str(proc_dict.get("agency", "N/A"))
        proc_type = str(proc_dict.get("type", "N/A"))
        status = str(proc_dict.get("status", "N/A"))
        rows.append([agency, proc_type, status])

    add_styled_table(doc, headers, rows, ds)


# ---------------------------------------------------------------------------
# Industry Claim Patterns
# ---------------------------------------------------------------------------


def _render_industry_patterns(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render industry claim patterns table."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Industry Claim Patterns")

    patterns = lit.industry_patterns
    if not patterns:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No industry-specific claim patterns identified.")
        return

    headers = ["Legal Theory", "Exposed", "Contagion Risk", "Description"]
    rows: list[list[str]] = []
    for pattern in patterns:
        raw_theory = str(sv_val(pattern.legal_theory, "N/A"))
        theory = raw_theory.replace("_", " ").title() if "_" in raw_theory else raw_theory
        exposed = _sv_bool(pattern.this_company_exposed)
        contagion = _sv_bool(pattern.contagion_risk)
        desc = (
            str(pattern.description.value)[:60]
            if pattern.description is not None
            else "N/A"
        )
        rows.append([theory, exposed, contagion, desc])

    add_styled_table(doc, headers, rows, ds)

    # D&O context for exposed patterns
    exposed_patterns = [
        p for p in patterns
        if p.this_company_exposed is not None and p.this_company_exposed.value
    ]
    if exposed_patterns:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: Company exposed to {len(exposed_patterns)} "
            f"industry claim pattern(s). Peer lawsuits create contagion "
            f"risk -- plaintiff firms often file similar claims across "
            f"the industry."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# SOL Windows
# ---------------------------------------------------------------------------


def _render_sol_map(
    doc: Any, lit: LitigationLandscape, ds: DesignSystem
) -> None:
    """Render statute of limitations window map."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Statute of Limitations Map")

    sol_windows = lit.sol_map
    if not sol_windows:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No statute of limitations windows tracked.")
        return

    headers = [
        "Claim Type", "Trigger Date", "SOL Expiry",
        "Repose Expiry", "Window Open",
    ]
    rows: list[list[str]] = []
    for sol in sol_windows:
        claim_type = sol.claim_type
        trigger = str(sol.trigger_date) if sol.trigger_date else "N/A"
        sol_expiry = str(sol.sol_expiry) if sol.sol_expiry else "N/A"
        repose_expiry = str(sol.repose_expiry) if sol.repose_expiry else "N/A"
        window = "OPEN" if sol.window_open else "CLOSED"
        rows.append([claim_type, trigger, sol_expiry, repose_expiry, window])

    add_styled_table(doc, headers, rows, ds)

    # Count open windows
    open_windows = [s for s in sol_windows if s.window_open]
    if open_windows:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            f"D&O Context: {len(open_windows)} open exposure window(s). "
            f"Claims can still be filed within these periods."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv_bool(sv: Any) -> str:
    """Format a SourcedValue[bool] as Yes/No/N/A."""
    if sv is None:
        return "N/A"
    return "Yes" if sv.value else "No"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_litigation_details(
    doc: Any,
    context: dict[str, Any],
    ds: DesignSystem,
    *,
    concise: bool = False,
) -> None:
    """Render litigation detail sections.

    Covers derivative suits, regulatory proceedings, industry claim
    patterns, and SOL map. Defense assessment, contingencies, and
    whistleblower are handled by sect6_defense.py.

    When concise=True (clean litigation), only renders the SOL map
    (always relevant for D&O underwriting).

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
        concise: If True, render only the SOL map.
    """
    lit = _get_litigation(context)
    if lit is None:
        return

    if concise:
        # Only SOL map for clean litigation
        _render_sol_map(doc, lit, ds)
        return

    _render_derivative_suits(doc, lit, ds)
    _render_regulatory_proceedings(doc, lit, ds)
    _render_industry_patterns(doc, lit, ds)
    _render_sol_map(doc, lit, ds)


__all__ = ["render_litigation_details"]
