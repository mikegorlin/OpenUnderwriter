"""Phase 119: Stock drop D&O assessment and pattern narrative generation.

Generates D&O litigation risk assessments for each drop catalyst
and an overall pattern narrative for underwriting context.

Runs in BENCHMARK stage. Each StockDropEvent gets a do_assessment
string explaining the specific D&O litigation theory triggered by
that catalyst type, with company-specific data (pct, date, prices).
"""

from __future__ import annotations

from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.formatters import safe_float


# ---------------------------------------------------------------------------
# Catalyst -> D&O litigation theory templates
# ---------------------------------------------------------------------------

_CATALYST_DO_MAP: dict[str, str] = {
    "earnings_miss": (
        "Section 10(b)/Rule 10b-5 exposure: {company} stock dropped {pct}% on {date} "
        "following earnings miss. {detail} Market reaction (AR: {ar}%) suggests investors "
        "viewed this as corrective disclosure of previously concealed weakness."
    ),
    "guidance_cut": (
        "Forward guidance reduction weakens safe harbor defense: {company} cut guidance "
        "triggering {pct}% decline on {date}. {detail} If prior guidance was specific and "
        "quantitative, plaintiff attorneys argue management knew results would miss."
    ),
    "restatement": (
        "Financial restatement creates dual exposure: Section 10(b) fraud claim + "
        "Section 11 strict liability. {company} dropped {pct}% on {date}. {detail}"
    ),
    "litigation": (
        "Litigation-driven drop: {company} fell {pct}% on {date} following {detail}. "
        "Pre-existing litigation compounds D&O exposure -- insurers face stacking risk."
    ),
    "analyst_downgrade": (
        "Analyst downgrade supports loss causation argument: {company} dropped {pct}% "
        "on {date}. {detail} Downgrades establish that stock price inflation corrected "
        "when negative information entered the market."
    ),
    "regulatory": (
        "Regulatory action: {company} fell {pct}% on {date}. {detail} "
        "Regulatory findings often trigger parallel shareholder suits and "
        "create additional D&O exposure from government investigation costs."
    ),
    "management_departure": (
        "Executive departure: {company} dropped {pct}% on {date}. {detail} "
        "Key person D&O coverage triggered -- personal conduct investigation "
        "risk and potential Side A claims."
    ),
    "market_wide": (
        "Market-wide event: {company} declined {pct}% on {date}. "
        "Market contributed {market_pct}% to decline -- loss causation defense "
        "available. Company-specific residual: {company_pct}%."
    ),
}

_DEFAULT_TEMPLATE = (
    "{company} dropped {pct}% on {date}. {detail} "
    "{assessment_note}"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_drop_do_assessments(
    drops: list[StockDropEvent],
    company_name: str,
) -> None:
    """Populate do_assessment on each drop event based on catalyst type.

    Mutates drops in-place. Does not return a value.

    Args:
        drops: List of StockDropEvent to enrich with D&O assessments.
        company_name: Company name for narrative personalization.
    """
    for drop in drops:
        drop.do_assessment = _assess_single_drop(drop, company_name)


def generate_drop_pattern_narrative(
    patterns: list[dict[str, str]],
    drops: list[StockDropEvent],
    company_name: str,
) -> str:
    """Generate overall D&O underwriting implication narrative from drop patterns.

    Describes the overall drop pattern: how many drops are company-specific,
    how many are market-driven, whether clusters were detected, and what
    the pattern implies for D&O underwriting.

    Args:
        patterns: Detected stock patterns (from detect_stock_patterns).
        drops: All StockDropEvent objects.
        company_name: Company name for narrative personalization.

    Returns:
        Narrative string, or empty string if no drops.
    """
    if not drops:
        return ""

    total = len(drops)
    company_specific = sum(1 for d in drops if d.is_company_specific)
    market_driven = sum(1 for d in drops if d.is_market_driven)

    parts: list[str] = []

    # Overall drop count
    parts.append(
        f"{company_name} experienced {total} significant stock decline(s) "
        f"in the analysis period."
    )

    # Company-specific vs market-driven breakdown
    if company_specific > 0:
        parts.append(
            f"{company_specific} of {total} drops are company-specific, "
            f"indicating endogenous risk factors."
        )
    if market_driven > 0:
        parts.append(
            f"{market_driven} of {total} drops are market-driven, "
            f"supporting loss causation defense."
        )

    # Pattern descriptions
    if patterns:
        pattern_descs = [
            p.get("description", p.get("pattern", ""))
            for p in patterns
            if p.get("description") or p.get("pattern")
        ]
        if pattern_descs:
            parts.append(
                f"Detected patterns: {'; '.join(pattern_descs)}."
            )

    # D&O implication
    if company_specific > total / 2:
        parts.append(
            "D&O Underwriting Implication: majority of declines are "
            "company-specific, suggesting catalytic disclosure failures "
            "that strengthen plaintiff 10(b) claims."
        )
    elif market_driven >= total / 2:
        parts.append(
            "D&O Underwriting Implication: majority of declines are "
            "market-driven, providing loss causation defense. However, "
            "company-specific residuals should still be evaluated."
        )
    else:
        parts.append(
            "D&O Underwriting Implication: mixed pattern of company-specific "
            "and market-driven declines requires careful attribution analysis."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _assess_single_drop(drop: StockDropEvent, company_name: str) -> str:
    """Generate D&O assessment for a single drop event."""
    pct = abs(safe_float(drop.drop_pct.value if drop.drop_pct else 0.0))
    date_str = str(drop.date.value) if drop.date else "unknown date"
    detail = drop.trigger_description or "No specific trigger identified."
    ar = safe_float(drop.abnormal_return_pct)

    # Market attribution values
    market_pct_val = safe_float(drop.market_pct)
    company_pct_val = safe_float(drop.company_pct)

    # Format assessment note for unknown/default category
    assessment_note = ""
    if drop.is_company_specific and drop.trigger_category in ("unknown", ""):
        assessment_note = (
            "Unattributed company-specific decline: plaintiff attorneys "
            "may allege undisclosed negative information."
        )

    template = _CATALYST_DO_MAP.get(drop.trigger_category, _DEFAULT_TEMPLATE)

    return template.format(
        company=company_name,
        pct=f"{pct:.1f}",
        date=date_str,
        detail=detail,
        ar=f"{abs(ar):.1f}",
        market_pct=f"{abs(market_pct_val):.1f}",
        company_pct=f"{abs(company_pct_val):.1f}",
        assessment_note=assessment_note,
    )
