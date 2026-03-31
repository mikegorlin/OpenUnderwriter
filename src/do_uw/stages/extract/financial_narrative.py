"""Financial health narrative generation.

Synthesizes extracted financial data (revenue, profitability, liquidity,
leverage, distress indicators) into a 3-5 sentence narrative paragraph
for SECT3-01.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    DistressZone,
    ExtractedFinancials,
    FinancialStatements,
)


def generate_financial_narrative(
    financials: ExtractedFinancials,
) -> SourcedValue[str]:
    """Generate a 3-5 sentence financial health summary.

    Synthesizes revenue trend, profitability, liquidity, leverage,
    and key concerns into a narrative paragraph. Marked as DERIVED/LOW
    confidence since it's synthesized from other extracted data.
    """
    parts: list[str] = []

    # Revenue trend
    _add_revenue_narrative(parts, financials.statements)

    # Profitability
    _add_profitability_narrative(parts, financials.statements)

    # Liquidity
    _add_liquidity_narrative(parts, financials.liquidity)

    # Leverage
    _add_leverage_narrative(parts, financials.leverage)

    # Key concerns
    _add_concern_narrative(parts, financials)

    narrative = " ".join(parts) if parts else (
        "Insufficient financial data available to generate a "
        "comprehensive health assessment."
    )

    return SourcedValue[str](
        value=narrative,
        source="Derived from extracted SECT3 financial data",
        confidence=Confidence.LOW,
        as_of=datetime.now(tz=UTC),
    )


def _add_revenue_narrative(
    parts: list[str], statements: FinancialStatements
) -> None:
    """Add revenue trend sentence to narrative."""
    if statements.income_statement is None:
        return
    revenue_item = _find_line_item(
        statements.income_statement.line_items, "revenue"
    )
    if revenue_item is None:
        return
    yoy = revenue_item.yoy_change
    if yoy is not None:
        if yoy > 5.0:
            parts.append(f"Revenue is growing at {yoy:.1f}% year-over-year.")
        elif yoy < -5.0:
            parts.append(
                f"Revenue has declined {abs(yoy):.1f}% year-over-year."
            )
        else:
            parts.append(
                f"Revenue is relatively stable ({yoy:+.1f}% YoY)."
            )
    else:
        parts.append("Revenue trend data is unavailable.")


def _add_profitability_narrative(
    parts: list[str], statements: FinancialStatements
) -> None:
    """Add profitability sentence to narrative."""
    if statements.income_statement is None:
        return
    ni_item = _find_line_item(
        statements.income_statement.line_items, "net_income"
    )
    if ni_item is None:
        return
    # Check the most recent period value
    periods = statements.income_statement.periods
    if not periods:
        return
    latest = periods[0]
    val = ni_item.values.get(latest)
    if val is not None and val.value is not None:
        if val.value > 0:
            parts.append("The company is profitable.")
        else:
            parts.append(
                "The company is reporting net losses, "
                "which may signal financial stress."
            )


def _add_liquidity_narrative(
    parts: list[str],
    liquidity: SourcedValue[dict[str, float | None]] | None,
) -> None:
    """Add liquidity sentence to narrative."""
    if liquidity is None:
        return
    ratios = liquidity.value
    cr = ratios.get("current_ratio")
    if cr is not None:
        if cr >= 2.0:
            parts.append(f"Liquidity is strong with a current ratio of {cr:.2f}.")
        elif cr >= 1.0:
            parts.append(
                f"Liquidity is adequate with a current ratio of {cr:.2f}."
            )
        else:
            parts.append(
                f"Liquidity is concerning with a current ratio of "
                f"{cr:.2f}, below the 1.0 threshold."
            )


def _add_leverage_narrative(
    parts: list[str],
    leverage: SourcedValue[dict[str, float | None]] | None,
) -> None:
    """Add leverage sentence to narrative."""
    if leverage is None:
        return
    ratios = leverage.value
    d2e = ratios.get("debt_to_ebitda")
    if d2e is not None:
        if d2e <= 2.0:
            parts.append(f"Leverage is conservative (debt/EBITDA: {d2e:.1f}x).")
        elif d2e <= 4.0:
            parts.append(f"Leverage is moderate (debt/EBITDA: {d2e:.1f}x).")
        else:
            parts.append(
                f"Leverage is elevated at {d2e:.1f}x debt/EBITDA, "
                f"which may constrain financial flexibility."
            )


def _add_concern_narrative(
    parts: list[str], financials: ExtractedFinancials
) -> None:
    """Add key concerns sentence to narrative."""
    concerns: list[str] = []

    # Distress zone check
    distress = financials.distress
    if distress.altman_z_score and (
        distress.altman_z_score.zone == DistressZone.DISTRESS
        and not distress.altman_z_score.is_partial
    ):
        concerns.append("Altman Z-Score in distress zone")
    if distress.beneish_m_score and (
        distress.beneish_m_score.zone == DistressZone.DISTRESS
    ):
        concerns.append("Beneish M-Score flags potential earnings manipulation")

    # Going concern
    if financials.audit.going_concern and financials.audit.going_concern.value:
        concerns.append("going concern qualification")

    # Material weaknesses
    if financials.audit.material_weaknesses:
        mw_count = len(financials.audit.material_weaknesses)
        concerns.append(f"{mw_count} material weakness(es)")

    if concerns:
        parts.append(
            "Key concerns: " + "; ".join(concerns) + "."
        )


def _find_line_item(
    items: list[Any], label_keyword: str
) -> Any | None:
    """Find a line item by label keyword (case-insensitive)."""
    keyword = label_keyword.lower()
    for item in items:
        if keyword in item.label.lower():
            return item
    return None
