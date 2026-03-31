"""Derived concept computation from XBRL primitives.

Computes margins, ratios, per-share metrics, and other derived financial
concepts from extracted XBRL primitive values. All computations are:
- None-safe: returns None when any required input is None
- Zero-division-safe: returns None when denominator is 0
- Exception-free: never raises, regardless of input

Usage:
    primitives = {"revenue": 1_000_000, "cost_of_revenue": 600_000, ...}
    derived = compute_derived_concepts(primitives)

    period_items = {"FY2024": primitives_2024, "FY2023": primitives_2023}
    multi = compute_multi_period_derived(period_items)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe arithmetic helpers
# ---------------------------------------------------------------------------


def _safe_div(
    numerator: float | None,
    denominator: float | None,
    *,
    scale: float = 1.0,
    precision: int = 2,
) -> float | None:
    """Safe division returning None on None inputs or zero denominator.

    Args:
        numerator: Top of fraction.
        denominator: Bottom of fraction.
        scale: Multiply result by this (100 for percentages).
        precision: Decimal places to round to.

    Returns:
        Rounded result, or None if inputs are invalid.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator * scale, precision)


def _safe_sub(a: float | None, b: float | None) -> float | None:
    """Safe subtraction returning None if either input is None."""
    if a is None or b is None:
        return None
    return a - b


def _safe_add(a: float | None, b: float | None) -> float | None:
    """Safe addition returning None if either input is None."""
    if a is None or b is None:
        return None
    return a + b


def _get(items: dict[str, float | None], key: str) -> float | None:
    """Get a value from items dict, treating missing keys as None."""
    v = items.get(key)
    if v is None:
        return None
    return float(v)


# ---------------------------------------------------------------------------
# Derived definition registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DerivedDef:
    """Definition of a derived financial concept."""

    name: str
    inputs: list[str]
    compute: Callable[[dict[str, float | None]], float | None]
    statement: str
    description: str


def _gross_margin(items: dict[str, float | None]) -> float | None:
    return _safe_div(_safe_sub(_get(items, "revenue"), _get(items, "cost_of_revenue")), _get(items, "revenue"), scale=100)


def _operating_margin(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "operating_income"), _get(items, "revenue"), scale=100)


def _net_margin(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "net_income"), _get(items, "revenue"), scale=100)


def _ebitda(items: dict[str, float | None]) -> float | None:
    return _safe_add(_get(items, "operating_income"), _get(items, "depreciation_amortization"))


def _ebitda_margin(items: dict[str, float | None]) -> float | None:
    ebitda = _ebitda(items)
    return _safe_div(ebitda, _get(items, "revenue"), scale=100)


def _effective_tax_rate(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "income_tax_expense"), _get(items, "pretax_income"), scale=100)


def _interest_coverage(items: dict[str, float | None]) -> float | None:
    # ebit = operating_income (same concept in this context)
    return _safe_div(_get(items, "operating_income"), _get(items, "interest_expense"), precision=4)


def _current_ratio(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "current_assets"), _get(items, "current_liabilities"), precision=4)


def _quick_ratio(items: dict[str, float | None]) -> float | None:
    ca = _get(items, "current_assets")
    inv = _get(items, "inventory")
    cl = _get(items, "current_liabilities")
    if ca is None or inv is None:
        return None
    return _safe_div(ca - inv, cl, precision=4)


def _debt_to_equity(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "total_debt"), _get(items, "stockholders_equity"), precision=4)


def _debt_to_ebitda(items: dict[str, float | None]) -> float | None:
    ebitda = _ebitda(items)
    return _safe_div(_get(items, "total_debt"), ebitda, precision=4)


def _tangible_book_value(items: dict[str, float | None]) -> float | None:
    eq = _get(items, "stockholders_equity")
    gw = _get(items, "goodwill")
    ia = _get(items, "intangible_assets")
    if eq is None or gw is None or ia is None:
        return None
    return round(eq - gw - ia, 2)


def _net_debt(items: dict[str, float | None]) -> float | None:
    td = _get(items, "total_debt")
    cash = _get(items, "cash_and_equivalents")
    if td is None or cash is None:
        return None
    return round(td - cash, 2)


def _book_value_per_share(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "stockholders_equity"), _get(items, "shares_outstanding"), precision=4)


def _working_capital(items: dict[str, float | None]) -> float | None:
    return _safe_sub(_get(items, "current_assets"), _get(items, "current_liabilities"))


def _free_cash_flow(items: dict[str, float | None]) -> float | None:
    return _safe_sub(_get(items, "operating_cash_flow"), _get(items, "capital_expenditures"))


def _fcf_to_revenue(items: dict[str, float | None]) -> float | None:
    fcf = _free_cash_flow(items)
    return _safe_div(fcf, _get(items, "revenue"), scale=100)


def _capex_to_revenue(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "capital_expenditures"), _get(items, "revenue"), scale=100)


def _capex_to_depreciation(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "capital_expenditures"), _get(items, "depreciation_amortization"), precision=4)


def _dividend_payout_ratio(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "dividends_paid"), _get(items, "net_income"), scale=100)


def _fcf_per_share(items: dict[str, float | None]) -> float | None:
    fcf = _free_cash_flow(items)
    return _safe_div(fcf, _get(items, "shares_outstanding"), precision=4)


def _return_on_assets(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "net_income"), _get(items, "total_assets"), scale=100)


def _return_on_equity(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "net_income"), _get(items, "stockholders_equity"), scale=100)


def _asset_turnover(items: dict[str, float | None]) -> float | None:
    return _safe_div(_get(items, "revenue"), _get(items, "total_assets"), precision=4)


# ---------------------------------------------------------------------------
# Signal-driven derived ratios
# ---------------------------------------------------------------------------


def _asset_impairment_pct(items: dict[str, float | None]) -> float | None:
    """Asset impairment charges as % of total assets."""
    return _safe_div(_get(items, "asset_impairment_charges"), _get(items, "total_assets"), scale=100)


def _goodwill_to_assets(items: dict[str, float | None]) -> float | None:
    """Goodwill as % of total assets."""
    return _safe_div(_get(items, "goodwill"), _get(items, "total_assets"), scale=100)


def _rou_asset_pct(items: dict[str, float | None]) -> float | None:
    """Operating lease ROU asset as % of total assets."""
    return _safe_div(_get(items, "right_of_use_asset"), _get(items, "total_assets"), scale=100)


def _operating_lease_burden(items: dict[str, float | None]) -> float | None:
    """Operating lease liabilities as % of total assets."""
    return _safe_div(_get(items, "operating_lease_liabilities"), _get(items, "total_assets"), scale=100)


def _sbc_dilution_pct(items: dict[str, float | None]) -> float | None:
    """Stock-based compensation as % of revenue."""
    return _safe_div(_get(items, "stock_based_compensation"), _get(items, "revenue"), scale=100)


def _contract_liability_pct(items: dict[str, float | None]) -> float | None:
    """Contract with customer liability as % of revenue."""
    return _safe_div(_get(items, "contract_with_customer_liability"), _get(items, "revenue"), scale=100)


def _derivative_fair_value_pct(items: dict[str, float | None]) -> float | None:
    """Net derivative fair value (assets - liabilities) as % of total assets."""
    assets = _get(items, "derivative_assets")
    liabilities = _get(items, "derivative_liabilities")
    if assets is None and liabilities is None:
        return None
    net = (assets or 0.0) - (liabilities or 0.0)
    return _safe_div(net, _get(items, "total_assets"), scale=100)


def _derivative_notional_pct(items: dict[str, float | None]) -> float | None:
    """Derivative notional amount as % of total assets."""
    return _safe_div(_get(items, "derivative_notional_amount"), _get(items, "total_assets"), scale=100)


def _warranty_reserve_pct(items: dict[str, float | None]) -> float | None:
    """Product warranty accrual as % of revenue."""
    return _safe_div(_get(items, "product_warranty_accrual"), _get(items, "revenue"), scale=100)


# All derived concept definitions, ordered by statement type.
DERIVED_DEFINITIONS: list[DerivedDef] = [
    # -- Income statement derived --
    DerivedDef("gross_margin_pct", ["revenue", "cost_of_revenue"], _gross_margin, "income", "Gross margin percentage"),
    DerivedDef("operating_margin_pct", ["operating_income", "revenue"], _operating_margin, "income", "Operating margin percentage"),
    DerivedDef("net_margin_pct", ["net_income", "revenue"], _net_margin, "income", "Net margin percentage"),
    DerivedDef("ebitda", ["operating_income", "depreciation_amortization"], _ebitda, "derived", "EBITDA"),
    DerivedDef("ebitda_margin_pct", ["operating_income", "depreciation_amortization", "revenue"], _ebitda_margin, "income", "EBITDA margin percentage"),
    DerivedDef("effective_tax_rate", ["income_tax_expense", "pretax_income"], _effective_tax_rate, "income", "Effective tax rate"),
    DerivedDef("interest_coverage_ratio", ["operating_income", "interest_expense"], _interest_coverage, "income", "Interest coverage ratio"),
    # -- Balance sheet derived --
    DerivedDef("working_capital", ["current_assets", "current_liabilities"], _working_capital, "derived", "Working capital"),
    DerivedDef("current_ratio", ["current_assets", "current_liabilities"], _current_ratio, "balance_sheet", "Current ratio"),
    DerivedDef("quick_ratio", ["current_assets", "inventory", "current_liabilities"], _quick_ratio, "balance_sheet", "Quick ratio"),
    DerivedDef("debt_to_equity", ["total_debt", "stockholders_equity"], _debt_to_equity, "balance_sheet", "Debt-to-equity ratio"),
    DerivedDef("debt_to_ebitda", ["total_debt", "operating_income", "depreciation_amortization"], _debt_to_ebitda, "balance_sheet", "Debt-to-EBITDA ratio"),
    DerivedDef("tangible_book_value", ["stockholders_equity", "goodwill", "intangible_assets"], _tangible_book_value, "balance_sheet", "Tangible book value"),
    DerivedDef("net_debt", ["total_debt", "cash_and_equivalents"], _net_debt, "balance_sheet", "Net debt"),
    DerivedDef("book_value_per_share", ["stockholders_equity", "shares_outstanding"], _book_value_per_share, "balance_sheet", "Book value per share"),
    DerivedDef("return_on_assets", ["net_income", "total_assets"], _return_on_assets, "balance_sheet", "Return on assets"),
    DerivedDef("return_on_equity", ["net_income", "stockholders_equity"], _return_on_equity, "balance_sheet", "Return on equity"),
    DerivedDef("asset_turnover", ["revenue", "total_assets"], _asset_turnover, "balance_sheet", "Asset turnover ratio"),
    # -- Cash flow derived --
    DerivedDef("free_cash_flow", ["operating_cash_flow", "capital_expenditures"], _free_cash_flow, "cash_flow", "Free cash flow"),
    DerivedDef("fcf_to_revenue", ["operating_cash_flow", "capital_expenditures", "revenue"], _fcf_to_revenue, "cash_flow", "FCF-to-revenue ratio"),
    DerivedDef("capex_to_revenue", ["capital_expenditures", "revenue"], _capex_to_revenue, "cash_flow", "Capex-to-revenue ratio"),
    DerivedDef("capex_to_depreciation", ["capital_expenditures", "depreciation_amortization"], _capex_to_depreciation, "cash_flow", "Capex-to-depreciation ratio"),
    DerivedDef("dividend_payout_ratio", ["dividends_paid", "net_income"], _dividend_payout_ratio, "cash_flow", "Dividend payout ratio"),
    DerivedDef("fcf_per_share", ["operating_cash_flow", "capital_expenditures", "shares_outstanding"], _fcf_per_share, "cash_flow", "Free cash flow per share"),
    # -- Signal-driven ratios --
    DerivedDef("asset_impairment_pct", ["asset_impairment_charges", "total_assets"], _asset_impairment_pct, "derived", "Asset impairment charges as % of total assets"),
    DerivedDef("goodwill_to_assets_pct", ["goodwill", "total_assets"], _goodwill_to_assets, "derived", "Goodwill as % of total assets"),
    DerivedDef("rou_asset_pct", ["right_of_use_asset", "total_assets"], _rou_asset_pct, "derived", "ROU asset as % of total assets"),
    DerivedDef("operating_lease_burden", ["operating_lease_liabilities", "total_assets"], _operating_lease_burden, "derived", "Operating lease liabilities as % of total assets"),
    DerivedDef("sbc_dilution_pct", ["stock_based_compensation", "revenue"], _sbc_dilution_pct, "derived", "Stock-based compensation as % of revenue"),
    DerivedDef("contract_liability_pct", ["contract_with_customer_liability", "revenue"], _contract_liability_pct, "derived", "Contract liability as % of revenue"),
    DerivedDef("derivative_fair_value_pct", ["derivative_assets", "derivative_liabilities", "total_assets"], _derivative_fair_value_pct, "derived", "Net derivative fair value as % of total assets"),
    DerivedDef("derivative_notional_pct", ["derivative_notional_amount", "total_assets"], _derivative_notional_pct, "derived", "Derivative notional as % of total assets"),
    DerivedDef("warranty_reserve_pct", ["product_warranty_accrual", "revenue"], _warranty_reserve_pct, "derived", "Product warranty reserve as % of revenue"),
]

# Name -> DerivedDef lookup for quick access
DERIVED_BY_NAME: dict[str, DerivedDef] = {d.name: d for d in DERIVED_DEFINITIONS}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_derived_concepts(
    line_items: dict[str, float | None],
) -> dict[str, float | None]:
    """Compute all derived concepts from XBRL primitives.

    Takes a flat dict of primitive concept name -> value and returns
    a dict of derived concept name -> computed value. Concepts with
    insufficient inputs are omitted (returned as None via .get()).

    Args:
        line_items: Primitive XBRL values keyed by canonical concept name.

    Returns:
        Dict of derived concept name -> computed value (or None).
    """
    derived: dict[str, float | None] = {}

    for defn in DERIVED_DEFINITIONS:
        try:
            result = defn.compute(line_items)
            derived[defn.name] = result
            if result is not None:
                logger.debug(
                    "Derived %s = %s (from %s)",
                    defn.name,
                    result,
                    ", ".join(defn.inputs),
                )
        except Exception:
            logger.exception("Error computing derived concept %s", defn.name)
            derived[defn.name] = None

    return derived


def compute_multi_period_derived(
    period_items: dict[str, dict[str, float | None]],
) -> dict[str, dict[str, float | None]]:
    """Compute derived concepts for each period independently.

    Also computes revenue_growth_yoy which requires consecutive periods.

    Args:
        period_items: Dict of period_label -> {concept_name -> value}.
            Period labels must be sortable (e.g., "FY2022", "FY2023").

    Returns:
        Dict of derived_concept_name -> {period_label -> value}.
    """
    if not period_items:
        return {}

    # Sort periods chronologically.
    sorted_periods = sorted(period_items.keys())

    # Compute single-period derived for each period.
    per_period_derived: dict[str, dict[str, float | None]] = {}
    for period in sorted_periods:
        single = compute_derived_concepts(period_items[period])
        for concept_name, value in single.items():
            if concept_name not in per_period_derived:
                per_period_derived[concept_name] = {}
            per_period_derived[concept_name][period] = value

    # Compute revenue_growth_yoy (cross-period).
    yoy: dict[str, float | None] = {}
    for i, period in enumerate(sorted_periods):
        if i == 0:
            yoy[period] = None
            continue
        prior_period = sorted_periods[i - 1]
        curr_rev = _get(period_items[period], "revenue")
        prior_rev = _get(period_items[prior_period], "revenue")
        if curr_rev is not None and prior_rev is not None and prior_rev != 0:
            yoy[period] = round(
                (curr_rev - prior_rev) / abs(prior_rev) * 100, 2
            )
        else:
            yoy[period] = None

    per_period_derived["revenue_growth_yoy"] = yoy

    logger.info(
        "Computed %d derived concepts across %d periods",
        len(per_period_derived),
        len(sorted_periods),
    )

    return per_period_derived
