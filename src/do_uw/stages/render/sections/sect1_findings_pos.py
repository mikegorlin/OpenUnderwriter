"""Positive finding narrative sub-builders for executive summary.

Each function produces a list of sentences for one finding type,
backed by real data from the analysis state. Every sentence must
contain company-specific data. No generic D&O primer text.

Phase 119.1-01: Rewrote all functions with deep state data extraction.
               Removed all boilerplate closing sentences.
"""

from __future__ import annotations

from do_uw.models.state import AnalysisState
from do_uw.stages.render.sections.sect1_findings_data import (
    board_size,
    bs_line_item,
    ceo_name,
    ceo_tenure_years,
    classified_board,
    company_name,
    executive_departure_count,
    fmt_billions,
    going_concern,
    goodwill_ratio,
    is_line_item,
    scoring_tier,
    short_interest_pct,
)
from do_uw.stages.render.sections.sect1_helpers import (
    safe_auditor,
    safe_auditor_tenure,
    safe_distress,
    safe_governance_field,
    safe_leverage_ratio,
    safe_short_interest,
)


def pos_clean_audit(state: AnalysisState, name: str) -> list[str]:
    """Clean audit and accounting history."""
    auditor = safe_auditor(state)
    tenure = safe_auditor_tenure(state)
    gw = goodwill_ratio(state)

    base = f"{name} maintains a clean audit opinion"
    if auditor:
        base += f" from {auditor}"
    if tenure:
        base += f" (tenure: {tenure} years)"
    base += (" with no material weaknesses, restatements, or "
             "going concern qualifications.")
    sentences = [base]

    # Specific track record context instead of generic "eliminates catalysts"
    if auditor and tenure:
        sentences.append(
            f"The {tenure}-year relationship with {auditor} provides "
            "audit continuity that reduces the likelihood of "
            "restatement-driven class actions."
        )
    elif auditor:
        sentences.append(
            f"{auditor}'s clean opinion supports disclosure reliability "
            f"for {name}'s financial statements."
        )

    if gw is not None and gw > 10:
        sentences.append(
            f"However, goodwill at {gw:.1f}% of total assets "
            "requires ongoing impairment testing -- clean audit "
            "history does not eliminate future impairment risk."
        )
    return sentences


def pos_strong_governance(
    state: AnalysisState, name: str,
) -> list[str]:
    """Strong board governance -- tied to actual board metrics."""
    independence = safe_governance_field(state, "independence_ratio")
    bsz = board_size(state)
    classified = classified_board(state)
    auditor = safe_auditor(state)

    parts: list[str] = []
    if independence is not None:
        parts.append(f"{independence * 100:.0f}% independence")
    if classified is False:
        parts.append("annual elections (no classified board)")
    if bsz:
        parts.append(f"{bsz}-member board")

    base = "Board governance is strong"
    if parts:
        base += f" with {', '.join(parts)}"
    sentences = [base + "."]

    if auditor:
        gc = going_concern(state)
        sentences.append(
            f"{auditor} serves as external auditor"
            + (" with a clean opinion and no material weaknesses."
               if not gc else ".")
        )

    # Specific governance defense tied to actual metrics
    if independence is not None and independence >= 0.75 and classified is False:
        sentences.append(
            f"At {independence * 100:.0f}% independence with annual "
            f"elections, {name}'s board structure demonstrates "
            "shareholder alignment that supports Caremark defense "
            "and reduces proxy contest risk."
        )
    elif independence is not None:
        sentences.append(
            f"Board independence at {independence * 100:.0f}% supports "
            f"{name}'s oversight posture."
        )
    return sentences


def pos_no_distress(state: AnalysisState, name: str) -> list[str]:
    """No financial distress indicators -- tied to actual Z-score/D/E values."""
    z = safe_distress(state, "altman_z_score")
    de = safe_leverage_ratio(state, "debt_to_equity")
    current = bs_line_item(state, "current_ratio")
    interest_cov = is_line_item(state, "interest_coverage_ratio")
    revenue = is_line_item(state, "total_revenue")
    total_debt = bs_line_item(state, "total_debt")

    detail: list[str] = []
    if z is not None:
        detail.append(f"Altman Z-Score of {z:.2f}")
    if de is not None:
        detail.append(f"D/E of {de:.2f}")
    if current is not None:
        detail.append(f"current ratio of {current:.1f}x")
    if interest_cov is not None:
        detail.append(f"interest coverage of {interest_cov:.1f}x")

    if detail:
        sentences = [
            f"No financial distress indicators present "
            f"({', '.join(detail)}).",
        ]
    else:
        sentences = ["No financial distress indicators present."]

    rev_str = fmt_billions(revenue)
    debt_str = fmt_billions(total_debt)
    if rev_str and debt_str:
        sentences.append(
            f"On {rev_str} annual revenue with {debt_str} total "
            f"debt, {name} has adequate capacity to service "
            "obligations without covenant pressure."
        )

    # Specific interpretation tied to actual Z-score instead of generic
    if z is not None and z > 2.99:
        sentences.append(
            f"An Altman Z of {z:.2f} places {name} firmly in the "
            "safe zone, eliminating going-concern, covenant violation, "
            "and creditor-related D&O exposure."
        )
    elif z is not None:
        sentences.append(
            f"Altman Z of {z:.2f} is in the gray zone but other "
            "indicators do not suggest imminent distress."
        )
    return sentences


def pos_stable_leadership(
    state: AnalysisState, name: str,
) -> list[str]:
    """Stable executive leadership -- differentiates by tenure and company health."""
    ceo = ceo_name(state)
    tenure = ceo_tenure_years(state)
    departures = executive_departure_count(state)
    tier = scoring_tier(state)
    z = safe_distress(state, "altman_z_score")

    # Determine if company is in distress
    is_distressed = False
    if tier and tier in ("WALK", "NO_TOUCH"):
        is_distressed = True
    elif z is not None and z < 1.8:
        is_distressed = True

    sentences: list[str] = []

    # Build opening with specific data
    if ceo and tenure is not None:
        sentences.append(
            f"{ceo} has led {name} for {tenure:.0f} years"
            + (f" with no recent C-suite departures." if departures == 0 else ".")
        )
    elif ceo:
        base = f"C-suite leadership is stable with {ceo} leading the organization"
        if departures == 0:
            base += " and no recent departures"
        sentences.append(base + ".")
    else:
        base = "C-suite leadership is stable with no recent departures"
        sentences.append(base + ".")

    # Differentiated interpretation based on company health
    if tenure is not None and tenure >= 10 and not is_distressed:
        sentences.append(
            f"This {tenure:.0f}-year leadership continuity during "
            "sustained financial health demonstrates management "
            "competence that undermines scienter allegations in "
            "any potential securities complaint."
        )
    elif tenure is not None and tenure < 5 and is_distressed:
        sentences.append(
            f"While {ceo or 'the CEO'} leads the organization, "
            f"the relatively brief {tenure:.0f}-year tenure means "
            "limited track record for evaluating management's "
            "response to adversity."
        )
    elif tenure is not None and tenure < 5:
        sentences.append(
            f"With {tenure:.0f} years in the role, "
            f"{ceo or 'the CEO'} has a developing track record "
            f"at {name}."
        )
    elif tenure is not None and is_distressed:
        sentences.append(
            f"Leadership stability must be weighed against "
            f"{name}'s current financial stress indicators."
        )
    elif tenure is not None:
        sentences.append(
            f"With {tenure:.0f} years of leadership, {ceo or 'the CEO'} "
            f"provides continuity for {name}."
        )

    # Departures context
    if departures is not None and departures > 0:
        sentences.append(
            f"However, {departures} C-suite departure"
            f"{'s' if departures > 1 else ''} in the past 18 months "
            "tempers the stability assessment."
        )

    return sentences


def pos_low_short(state: AnalysisState, name: str) -> list[str]:
    """Low short interest -- with actual positioning context."""
    si = short_interest_pct(state)
    base = "Short interest is low"
    if si is not None:
        base += f" at {si:.1f}% of float"
    sentences = [
        base + ", indicating institutional investors are not "
        "positioning against the stock.",
    ]

    # Specific context instead of generic "eliminates a common catalyst"
    if si is not None and si < 2:
        sentences.append(
            f"At {si:.1f}%, short positioning is minimal -- "
            "there is no institutional bearish thesis driving "
            "potential short-seller reports or activist campaigns "
            f"against {name}."
        )
    elif si is not None:
        sentences.append(
            f"Short interest at {si:.1f}% is within normal range, "
            f"suggesting no concentrated bearish positioning against {name}."
        )
    return sentences


def pos_no_enforcement(name: str) -> list[str]:
    """No active SEC enforcement."""
    return [
        f"{name} has no active SEC enforcement pipeline activity, "
        "open investigations, or pending Wells Notices.",
        f"A clean regulatory record for {name} eliminates the "
        "highest-severity D&O claim catalyst and supports "
        "favorable underwriting consideration.",
    ]
