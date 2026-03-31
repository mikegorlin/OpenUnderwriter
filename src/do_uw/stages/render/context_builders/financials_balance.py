"""Balance sheet context builders for financial statement rendering.

Format-agnostic helpers that build full financial statement row data
for all three statement types (income, balance sheet, cash flow).

Moved from md_renderer_helpers_financial_balance.py (Phase 58, shared context layer).
The income statement orchestrator (extract_financials) lives in
context_builders/financials.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import (
    format_change_indicator,
    format_compact,
    format_currency,
    format_percentage,
)


def _format_line_value(value: float, label: str) -> str:
    """Format a financial line item value based on label context.

    Detects non-currency line items (shares, EPS, margins) and applies
    the appropriate formatter instead of always using format_currency.
    """
    label_lower = label.lower()
    if "margin" in label_lower or "%" in label_lower:
        return format_percentage(value)
    if "eps" in label_lower or "per share" in label_lower:
        return f"${value:.2f}"
    # Share counts and non-monetary counts -- no $ prefix
    if any(kw in label_lower for kw in (
        "shares", "share count", "weighted average",
        "diluted shares", "basic shares",
    )):
        return format_compact(value)
    # Financial ratios -- plain numbers or multipliers, no $ prefix
    if any(kw in label_lower for kw in (
        "ratio", "return on", "roe", "roa", "roic",
        "debt_to_equity", "debt to equity",
    )):
        if abs(value) < 100:
            return f"{value:.2f}x"
        return f"{value:.1f}x"
    return format_currency(value, compact=True)


def _build_statement_rows(
    stmts: Any,
) -> dict[str, Any]:
    """Build full statement row data for all three financial statements.

    Returns dict with income_statement_rows, balance_sheet_rows,
    cash_flow_rows (each a list of row dicts), and statement_periods.
    """
    from do_uw.models.financials import FinancialStatement

    out: dict[str, Any] = {
        "income_statement_rows": [],
        "balance_sheet_rows": [],
        "cash_flow_rows": [],
        "statement_periods": [],
    }

    def _filter_periods(stmt: FinancialStatement) -> list[str]:
        """Filter periods to those with >20% data coverage (matches Word renderer)."""
        raw_periods = stmt.periods or []
        total_items = len(stmt.line_items)
        if total_items == 0:
            return raw_periods
        period_data_count: dict[str, int] = dict.fromkeys(raw_periods, 0)
        for item in stmt.line_items:
            for p in raw_periods:
                if item.values.get(p) is not None:
                    period_data_count[p] += 1
        min_coverage = max(1, int(total_items * 0.2))
        return [p for p in raw_periods if period_data_count[p] >= min_coverage]

    def _rows_for_stmt(
        stmt: FinancialStatement, periods: list[str],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in stmt.line_items:
            values: dict[str, str] = {}
            has_any = False
            for period in periods:
                sv = item.values.get(period)
                if sv is not None:
                    values[period] = _format_line_value(sv.value, item.label)
                    has_any = True
                else:
                    values[period] = "N/A"
            if not has_any:
                continue  # Skip entirely N/A rows
            yoy = (
                format_change_indicator(
                    float(list(item.values.values())[0].value),
                    float(list(item.values.values())[1].value),
                )
                if len(item.values) >= 2
                and list(item.values.values())[0] is not None
                and list(item.values.values())[1] is not None
                and list(item.values.values())[1].value != 0
                else None
            )
            rows.append({
                "label": item.label,
                "period_values": values,
                "yoy_change": yoy,
            })
        return rows

    if stmts.income_statement is not None:
        filtered = _filter_periods(stmts.income_statement)
        out["income_statement_rows"] = _rows_for_stmt(stmts.income_statement, filtered)
        out["statement_periods"] = filtered
    if stmts.balance_sheet is not None:
        filtered = _filter_periods(stmts.balance_sheet)
        out["balance_sheet_rows"] = _rows_for_stmt(stmts.balance_sheet, filtered)
        if not out["statement_periods"]:
            out["statement_periods"] = filtered
    if stmts.cash_flow is not None:
        filtered = _filter_periods(stmts.cash_flow)
        out["cash_flow_rows"] = _rows_for_stmt(stmts.cash_flow, filtered)
        if not out["statement_periods"]:
            out["statement_periods"] = filtered

    # Ensure every row has values for ALL statement_periods.
    # Different statements may cover different period ranges (e.g. cash flow
    # has 2 periods while income statement has 3). The Jinja2 template
    # iterates statement_periods globally, so missing keys cause errors.
    canonical = out["statement_periods"]
    for key in ("income_statement_rows", "balance_sheet_rows", "cash_flow_rows"):
        for row in out[key]:
            pv = row["period_values"]
            for period in canonical:
                if period not in pv:
                    pv[period] = "N/A"

    return out


__all__ = ["_build_statement_rows"]
