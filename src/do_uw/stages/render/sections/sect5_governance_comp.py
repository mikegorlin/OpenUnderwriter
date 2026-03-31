"""Section 5 sub-module: Compensation Analysis.

Renders summary compensation table (SCT) for all NEOs, CEO pay ratio,
compensation structure analysis, golden parachute values, and
compensation red flags. All with D&O context annotations.

Called by sect5_governance.py via render_compensation_detail().

Phase 60-02: Receives context dict; extracts governance via _state escape hatch.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.governance import CompensationFlags, GovernanceData
from do_uw.models.governance_forensics import (
    CompensationAnalysis,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
)

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def render_compensation_detail(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render executive compensation detail section.

    Called by sect5_governance.render_section_5() after board
    composition and quality metrics.
    """
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Compensation Analysis")

    gov = _get_governance(context)
    if gov is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Compensation data not available.")
        return

    comp = gov.comp_analysis
    comp_flags = gov.compensation

    _render_summary_comp_table(doc, comp, ds)
    _render_ceo_pay_ratio(doc, comp, comp_flags, ds)
    _render_compensation_structure(doc, comp, ds)
    _render_golden_parachute(doc, comp_flags, ds)
    _render_compensation_red_flags(doc, comp, comp_flags, ds)


# ---------------------------------------------------------------------------
# Summary Compensation Table
# ---------------------------------------------------------------------------


def _render_summary_comp_table(
    doc: Any, comp: CompensationAnalysis, ds: DesignSystem
) -> None:
    """Render Summary Compensation Table (SCT) for CEO."""
    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Summary Compensation Table")

    # Build CEO comp breakdown
    has_data = (
        comp.ceo_total_comp is not None
        or comp.ceo_salary is not None
    )

    if not has_data:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "Detailed NEO compensation data not available. "
            "Review DEF 14A for Summary Compensation Table."
        )
        return

    headers = ["Component", "Amount"]
    rows: list[list[str]] = []

    if comp.ceo_salary:
        rows.append([
            "Base Salary",
            format_currency(comp.ceo_salary.value, compact=True),
        ])
    if comp.ceo_bonus:
        rows.append([
            "Annual Bonus/Incentive",
            format_currency(comp.ceo_bonus.value, compact=True),
        ])
    if comp.ceo_equity:
        rows.append([
            "Equity Awards (Stock + Options)",
            format_currency(comp.ceo_equity.value, compact=True),
        ])
    if comp.ceo_other:
        rows.append([
            "Other Compensation",
            format_currency(comp.ceo_other.value, compact=True),
        ])
    if comp.ceo_total_comp:
        rows.append([
            "Total CEO Compensation",
            format_currency(comp.ceo_total_comp.value, compact=True),
        ])

    if rows:
        add_styled_table(doc, headers, rows, ds)

    # Peer comparison flag
    if comp.ceo_pay_vs_peer_median and comp.ceo_pay_vs_peer_median.value > 2.0:
        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(
            f"CEO Pay vs Peer Median: "
            f"{comp.ceo_pay_vs_peer_median.value:.1f}x. "
            "Compensation exceeding 2x peer median draws heightened "
            "proxy advisory scrutiny and increases say-on-pay failure "
            "risk, which correlates with derivative compensation "
            "litigation."
        )
        _ = run
        add_risk_indicator(fp, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# CEO Pay Ratio
# ---------------------------------------------------------------------------


def _render_ceo_pay_ratio(
    doc: Any,
    comp: CompensationAnalysis,
    comp_flags: CompensationFlags,
    ds: DesignSystem,
) -> None:
    """Render CEO pay ratio section."""
    ceo_ratio = comp.ceo_pay_ratio
    flag_ratio = comp_flags.ceo_pay_ratio

    ratio_val = None
    if ceo_ratio:
        ratio_val = ceo_ratio.value
    elif flag_ratio:
        ratio_val = flag_ratio.value

    if ratio_val is None:
        return

    rows: list[list[str]] = []
    rows.append(["CEO Pay Ratio", f"{ratio_val:.0f}:1"])

    if comp.ceo_pay_vs_peer_median:
        rows.append([
            "CEO Pay vs Peer Median",
            f"{comp.ceo_pay_vs_peer_median.value:.2f}x",
        ])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # D&O context for extreme ratios
    if ratio_val > 500:
        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(
            f"CEO Pay Ratio ({ratio_val:.0f}:1): Extremely high pay "
            "ratios increase Section 14A proxy disclosure litigation "
            "risk and shareholder proposal activity. Ratios above "
            "500:1 are material governance concerns for D&O "
            "underwriting."
        )
        _ = run
        add_risk_indicator(fp, "HIGH", ds)


# ---------------------------------------------------------------------------
# Compensation Structure Analysis
# ---------------------------------------------------------------------------


def _render_compensation_structure(
    doc: Any, comp: CompensationAnalysis, ds: DesignSystem
) -> None:
    """Render compensation structure analysis."""
    if not comp.comp_mix and not comp.has_clawback:
        return

    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Compensation Structure")

    rows: list[list[str]] = []

    # Compensation mix
    if comp.comp_mix:
        for category, pct in comp.comp_mix.items():
            rows.append([category, format_percentage(pct)])

    # Clawback provision
    if comp.has_clawback:
        clawback = "Yes" if comp.has_clawback.value else "No"
        rows.append(["Clawback Policy", clawback])

    if comp.clawback_scope:
        rows.append(["Clawback Scope", str(comp.clawback_scope.value)])

    # Performance metrics
    if comp.performance_metrics:
        metrics_list = [str(m.value) for m in comp.performance_metrics[:5]]
        rows.append(["Performance Metrics", ", ".join(metrics_list)])

    if rows:
        add_styled_table(doc, ["Component", "Detail"], rows, ds)

    # D&O context: equity-heavy compensation
    equity_pct = comp.comp_mix.get("equity", comp.comp_mix.get("stock", 0.0))
    if equity_pct > 70:
        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(
            f"Equity-Heavy Compensation ({equity_pct:.0f}%): "
            "Equity-heavy compensation aligns executive interests with "
            "shareholders but creates heightened insider trading "
            "scrutiny. Courts examine whether equity vesting windows "
            "correlate with material non-public information."
        )
        _ = run
        add_risk_indicator(fp, "ELEVATED", ds)

    # No clawback warning
    if comp.has_clawback and not comp.has_clawback.value:
        fp = doc.add_paragraph(style="DOBody")
        run = fp.add_run(
            "D&O Context: Absence of clawback policy beyond Dodd-Frank "
            "minimum indicates weaker executive accountability framework. "
            "Proxy advisors flag this as a governance deficiency."
        )
        _ = run
        add_risk_indicator(fp, "ELEVATED", ds)


# ---------------------------------------------------------------------------
# Golden Parachute
# ---------------------------------------------------------------------------


def _render_golden_parachute(
    doc: Any, comp_flags: CompensationFlags, ds: DesignSystem
) -> None:
    """Render golden parachute values if available."""
    gp = comp_flags.golden_parachute_value
    if gp is None:
        return

    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Golden Parachute / Change-in-Control")

    rows: list[list[str]] = []
    rows.append([
        "Estimated CIC Payout",
        format_currency(gp.value, compact=True),
    ])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # D&O context
    if gp.value > 50_000_000:
        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(
            f"Golden Parachute "
            f"({format_currency(gp.value, compact=True)}): "
            "Change-in-control payments above $50M trigger heightened "
            "Revlon duty scrutiny and waste-of-corporate-assets claims. "
            "Shareholders may challenge the board's approval of "
            "excessive change-in-control provisions."
        )
        _ = run
        add_risk_indicator(fp, "HIGH", ds)


# ---------------------------------------------------------------------------
# Compensation Red Flags
# ---------------------------------------------------------------------------


def _render_compensation_red_flags(
    doc: Any,
    comp: CompensationAnalysis,
    comp_flags: CompensationFlags,
    ds: DesignSystem,
) -> None:
    """Render compensation red flags with D&O context."""
    flags: list[tuple[str, str]] = []

    # Say-on-pay below threshold
    say_on_pay = comp.say_on_pay_pct or comp_flags.say_on_pay_support_pct
    if say_on_pay is not None and say_on_pay.value < 70.0:
        flags.append((
            f"Low Say-on-Pay Support ({say_on_pay.value:.1f}%)",
            "Support below 70% triggers heightened ISS/Glass Lewis "
            "scrutiny and correlates with shareholder derivative "
            "suits over executive compensation.",
        ))

    # Excessive perquisites
    if comp_flags.excessive_perquisites:
        perks = [str(p.value) for p in comp_flags.excessive_perquisites[:3]]
        flags.append((
            f"Excessive Perquisites: {', '.join(perks)}",
            "Perquisites above peer norms indicate weak board "
            "oversight of management compensation.",
        ))

    # Related-party transactions
    if comp.related_party_transactions:
        count = len(comp.related_party_transactions)
        flags.append((
            f"Related-Party Transactions ({count})",
            "Related-party transactions between executives and "
            "company require enhanced disclosure and increase "
            "Caremark derivative claim exposure.",
        ))

    # Notable perquisites
    if comp.notable_perquisites:
        perks = [str(p.value) for p in comp.notable_perquisites[:3]]
        flags.append((
            f"Notable Perquisites: {', '.join(perks)}",
            "Above-peer perquisites draw proxy advisory negative "
            "recommendations.",
        ))

    if not flags:
        return

    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Compensation Red Flags")

    for flag_title, flag_context in flags:
        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(f"{flag_title}: {flag_context}")
        _ = run
        level = "HIGH" if "Say-on-Pay" in flag_title else "ELEVATED"
        add_risk_indicator(fp, level, ds)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_governance(context: dict[str, Any]) -> GovernanceData | None:
    """Extract governance data from context dict."""
    # TODO(phase-60): use context["governance"] when it returns GovernanceData
    state = context.get("_state")
    if state is None or state.extracted is None:
        return None
    return state.extracted.governance


__all__ = ["render_compensation_detail"]
