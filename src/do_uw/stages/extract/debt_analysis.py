"""Debt analysis extraction -- liquidity, leverage, debt structure, refinancing.

SECT3-08..11. Ratio computations (liquidity, leverage) here. Text parsing
(debt structure, refinancing risk) in debt_text_parsing.py. LLM enrichment
adds qualitative covenant/facility context from Item 8 footnotes.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import FinancialStatement
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.debt_text_parsing import (
    extract_debt_structure,
    extract_refinancing_risk,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)


def _get_line_item_value(
    statement: FinancialStatement, concept: str, period: str
) -> float | None:
    """Get a numeric value from a statement by xbrl_concept and period."""
    for item in statement.line_items:
        if item.xbrl_concept == concept:
            sv = item.values.get(period)
            return sv.value if sv is not None else None
    return None


def _safe_divide(
    numerator: float | None, denominator: float | None
) -> float | None:
    """Divide with None and zero-denominator safety."""
    if numerator is None or denominator is None or denominator == 0.0:
        return None
    return numerator / denominator


def _make_sourced_value_dict(
    value: dict[str, float | None],
    source: str,
    confidence: Confidence = Confidence.HIGH,
) -> SourcedValue[dict[str, float | None]]:
    """Create a SourcedValue wrapping a dict of ratios."""
    return SourcedValue[dict[str, float | None]](
        value=value,
        source=source,
        confidence=confidence,
        as_of=datetime.now(tz=UTC),
    )


# ---------------------------------------------------------------------------
# SECT3-08: Liquidity Assessment
# ---------------------------------------------------------------------------


def _extract_liquidity(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, float | None]] | None, ExtractionReport]:
    """Compute liquidity ratios (current, quick, cash, working capital, days cash)."""
    expected = [
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "working_capital",
        "days_cash_on_hand",
    ]
    found: list[str] = []
    source_filing = "N/A"

    financials = (
        state.extracted.financials if state.extracted is not None else None
    )
    if financials is None or financials.statements.balance_sheet is None:
        report = create_report(
            extractor_name="liquidity",
            expected=expected,
            found=found,
            source_filing=source_filing,
            warnings=["No balance sheet data available"],
        )
        return None, report

    bs = financials.statements.balance_sheet
    source_filing = bs.filing_source or "Balance sheet"
    period = bs.periods[-1] if bs.periods else ""
    if not period:
        report = create_report(
            extractor_name="liquidity",
            expected=expected,
            found=found,
            source_filing=source_filing,
            warnings=["No periods available in balance sheet"],
        )
        return None, report

    # Extract base values
    current_assets = _get_line_item_value(bs, "current_assets", period)
    current_liabilities = _get_line_item_value(
        bs, "current_liabilities", period
    )
    inventory = _get_line_item_value(bs, "inventory", period)
    cash = _get_line_item_value(bs, "cash_and_equivalents", period)

    # Get operating expenses for days_cash_on_hand
    income_stmt = financials.statements.income_statement
    operating_expenses: float | None = None
    if income_stmt is not None and income_stmt.periods:
        inc_period = income_stmt.periods[-1]
        revenue = _get_line_item_value(income_stmt, "revenue", inc_period)
        operating_income = _get_line_item_value(
            income_stmt, "operating_income", inc_period
        )
        if revenue is not None and operating_income is not None:
            operating_expenses = revenue - operating_income

    # Compute ratios
    ratios: dict[str, float | None] = {}

    current_ratio = _safe_divide(current_assets, current_liabilities)
    ratios["current_ratio"] = (
        round(current_ratio, 4) if current_ratio is not None else None
    )
    if current_ratio is not None:
        found.append("current_ratio")

    quick_assets = (
        (current_assets - (inventory or 0.0))
        if current_assets is not None
        else None
    )
    quick_ratio = _safe_divide(quick_assets, current_liabilities)
    ratios["quick_ratio"] = (
        round(quick_ratio, 4) if quick_ratio is not None else None
    )
    if quick_ratio is not None:
        found.append("quick_ratio")

    cash_ratio = _safe_divide(cash, current_liabilities)
    ratios["cash_ratio"] = (
        round(cash_ratio, 4) if cash_ratio is not None else None
    )
    if cash_ratio is not None:
        found.append("cash_ratio")

    if current_assets is not None and current_liabilities is not None:
        ratios["working_capital"] = current_assets - current_liabilities
        found.append("working_capital")
    else:
        ratios["working_capital"] = None

    if cash is not None and operating_expenses is not None:
        daily_opex = operating_expenses / 365.0
        days_cash = _safe_divide(cash, daily_opex)
        ratios["days_cash_on_hand"] = (
            round(days_cash, 1) if days_cash is not None else None
        )
        if days_cash is not None:
            found.append("days_cash_on_hand")
    else:
        ratios["days_cash_on_hand"] = None

    report = create_report(
        extractor_name="liquidity",
        expected=expected,
        found=found,
        source_filing=source_filing,
    )

    if not found:
        return None, report

    result = _make_sourced_value_dict(
        ratios, f"Derived from XBRL balance sheet ({source_filing})"
    )
    return result, report


# ---------------------------------------------------------------------------
# SECT3-09: Leverage Assessment
# ---------------------------------------------------------------------------


def _extract_leverage(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, float | None]] | None, ExtractionReport]:
    """Compute leverage ratios (D/E, D/EBITDA, interest coverage, D/A, net debt)."""
    expected = [
        "debt_to_equity",
        "debt_to_ebitda",
        "interest_coverage",
        "debt_to_assets",
        "net_debt",
    ]
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "N/A"

    financials = (
        state.extracted.financials if state.extracted is not None else None
    )
    if financials is None or financials.statements.balance_sheet is None:
        report = create_report(
            extractor_name="leverage",
            expected=expected,
            found=found,
            source_filing=source_filing,
            warnings=["No balance sheet data available"],
        )
        return None, report

    bs = financials.statements.balance_sheet
    source_filing = bs.filing_source or "Balance sheet + Income statement"
    period = bs.periods[-1] if bs.periods else ""
    if not period:
        report = create_report(
            extractor_name="leverage",
            expected=expected,
            found=found,
            source_filing=source_filing,
            warnings=["No periods available"],
        )
        return None, report

    # Balance sheet values
    total_debt = _get_line_item_value(bs, "total_debt", period)
    # Fallback: long_term_debt + short_term_debt
    if total_debt is None:
        ltd = _get_line_item_value(bs, "long_term_debt", period)
        std = _get_line_item_value(bs, "short_term_debt", period)
        if ltd is not None or std is not None:
            total_debt = (ltd or 0.0) + (std or 0.0)

    equity = _get_line_item_value(bs, "stockholders_equity", period)
    total_assets = _get_line_item_value(bs, "total_assets", period)
    cash = _get_line_item_value(bs, "cash_and_equivalents", period)

    # Income statement values
    income_stmt = financials.statements.income_statement
    operating_income: float | None = None
    interest_expense: float | None = None
    da: float | None = None

    if income_stmt is not None and income_stmt.periods:
        inc_period = income_stmt.periods[-1]
        operating_income = _get_line_item_value(
            income_stmt, "operating_income", inc_period
        )
        interest_expense = _get_line_item_value(
            income_stmt, "interest_expense", inc_period
        )
        # Fallback: if interest_expense missing for latest period,
        # use most recent available period (XBRL tags may differ by year).
        if interest_expense is None:
            for fallback_period in income_stmt.periods:
                ie = _get_line_item_value(
                    income_stmt, "interest_expense", fallback_period
                )
                if ie is not None:
                    interest_expense = ie
                    break

    # D&A from cash flow statement
    cf_stmt = financials.statements.cash_flow
    if cf_stmt is not None and cf_stmt.periods:
        cf_period = cf_stmt.periods[-1]
        da = _get_line_item_value(
            cf_stmt, "depreciation_amortization", cf_period
        )

    # Compute EBITDA
    ebitda: float | None = None
    if operating_income is not None:
        ebitda = operating_income + (da or 0.0)

    # Compute ratios
    ratios: dict[str, float | None] = {}

    d_e = _safe_divide(total_debt, equity)
    ratios["debt_to_equity"] = round(d_e, 4) if d_e is not None else None
    if d_e is not None:
        found.append("debt_to_equity")
        if d_e > 3.0:
            warnings.append(
                f"HIGH: Debt-to-Equity {d_e:.2f} > 3.0 "
                "(aggressive capital structure)"
            )

    d_ebitda = _safe_divide(total_debt, ebitda)
    ratios["debt_to_ebitda"] = (
        round(d_ebitda, 4) if d_ebitda is not None else None
    )
    if d_ebitda is not None:
        found.append("debt_to_ebitda")
        if d_ebitda > 4.0:
            warnings.append(
                f"HIGH: Debt-to-EBITDA {d_ebitda:.2f} > 4.0 (high leverage)"
            )

    if interest_expense is not None and interest_expense == 0.0:
        ratios["interest_coverage"] = None
        found.append("interest_coverage")
        warnings.append("No debt service: interest expense is zero")
    else:
        int_cov = _safe_divide(operating_income, interest_expense)
        ratios["interest_coverage"] = (
            round(int_cov, 4) if int_cov is not None else None
        )
        if int_cov is not None:
            found.append("interest_coverage")
            if int_cov < 2.0:
                warnings.append(
                    f"HIGH: Interest Coverage {int_cov:.2f} < 2.0 "
                    "(thin coverage)"
                )

    d_a = _safe_divide(total_debt, total_assets)
    ratios["debt_to_assets"] = round(d_a, 4) if d_a is not None else None
    if d_a is not None:
        found.append("debt_to_assets")

    if total_debt is not None and cash is not None:
        ratios["net_debt"] = total_debt - cash
        found.append("net_debt")
    else:
        ratios["net_debt"] = None

    report = create_report(
        extractor_name="leverage",
        expected=expected,
        found=found,
        source_filing=source_filing,
        warnings=warnings if warnings else None,
    )

    if not found:
        return None, report

    result = _make_sourced_value_dict(
        ratios,
        f"Derived from XBRL financial statements ({source_filing})",
    )
    return result, report


# ---------------------------------------------------------------------------
# LLM enrichment (qualitative supplements, never overrides XBRL)
# ---------------------------------------------------------------------------


def _enrich_debt_with_llm(
    state: AnalysisState,
    debt_structure: SourcedValue[dict[str, Any]] | None,
) -> SourcedValue[dict[str, Any]] | None:
    """Supplement debt_structure with LLM Item 8 covenant/facility context.

    Qualitative only -- numeric XBRL values are never modified.
    MD&A qualitative data stays on TenKExtraction for narrative renderers.
    """
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k

    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is None:
        return debt_structure

    from do_uw.stages.extract.ten_k_converters import convert_debt_enrichment

    debt_ctx = convert_debt_enrichment(llm_ten_k)
    has_covenant = debt_ctx.get("covenant_status") is not None
    has_facility = debt_ctx.get("credit_facility_detail") is not None
    has_instruments = bool(debt_ctx.get("debt_instruments"))
    if not has_covenant and not has_facility and not has_instruments:
        return debt_structure

    # Bootstrap empty structure if regex found nothing
    if debt_structure is None:
        debt_structure = SourcedValue[dict[str, Any]](
            value={"maturity_schedule": {}, "interest_rates": {},
                   "covenants": {}, "credit_facility": {"detected": False, "amount": None}},
            source="10-K (LLM)", confidence=Confidence.MEDIUM,
            as_of=datetime.now(tz=UTC),
        )

    ds = debt_structure.value
    if has_covenant:
        cov = ds.get("covenants", {})
        if isinstance(cov, dict):
            cov["covenant_status"] = debt_ctx["covenant_status"]
            cov["mentioned"] = True
            ds["covenants"] = cov
    if has_facility:
        fac = ds.get("credit_facility", {})
        if isinstance(fac, dict):
            fac["llm_detail"] = debt_ctx["credit_facility_detail"]
            ds["credit_facility"] = fac
    if has_instruments:
        ds["llm_debt_instruments"] = debt_ctx["debt_instruments"]

    logger.info("SECT3: Enriched debt analysis with LLM Item 8 footnotes")
    return debt_structure


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def extract_debt_analysis(
    state: AnalysisState,
) -> tuple[
    SourcedValue[dict[str, float | None]] | None,  # liquidity
    SourcedValue[dict[str, float | None]] | None,  # leverage
    SourcedValue[dict[str, Any]] | None,  # debt_structure
    SourcedValue[dict[str, Any]] | None,  # refinancing_risk
    list[ExtractionReport],
]:
    """Extract debt analysis: liquidity, leverage, debt structure, refinancing risk."""
    reports: list[ExtractionReport] = []

    # 1. Liquidity
    liquidity, liq_report = _extract_liquidity(state)
    reports.append(liq_report)

    # 2. Leverage
    leverage, lev_report = _extract_leverage(state)
    reports.append(lev_report)

    # 3. Debt structure (text-based, from debt_text_parsing.py)
    debt_structure, ds_report = extract_debt_structure(state)
    reports.append(ds_report)

    # 3b. LLM Item 8 footnote enrichment (qualitative only, never overrides XBRL)
    debt_structure = _enrich_debt_with_llm(state, debt_structure)

    # 4. Refinancing risk (depends on debt_structure + liquidity)
    cash_value: float | None = None
    credit_facility_amount: float | None = None

    financials = (
        state.extracted.financials if state.extracted is not None else None
    )
    if (
        financials is not None
        and financials.statements.balance_sheet is not None
    ):
        bs = financials.statements.balance_sheet
        if bs.periods:
            cash_value = _get_line_item_value(
                bs, "cash_and_equivalents", bs.periods[-1]
            )

    if debt_structure is not None:
        facility_raw = debt_structure.value.get("credit_facility", {})
        if isinstance(facility_raw, dict):
            facility = cast(dict[str, Any], facility_raw)
            if facility.get("detected"):
                amt = facility.get("amount")
                if isinstance(amt, (int, float)):
                    credit_facility_amount = float(amt)

    refinancing_risk, ref_report = extract_refinancing_risk(
        debt_structure, liquidity, cash_value, credit_facility_amount
    )
    reports.append(ref_report)

    logger.info(
        "Debt analysis complete: liquidity=%s leverage=%s "
        "debt_structure=%s refinancing=%s",
        "yes" if liquidity else "no",
        "yes" if leverage else "no",
        "yes" if debt_structure else "no",
        "yes" if refinancing_risk else "no",
    )

    return liquidity, leverage, debt_structure, refinancing_risk, reports
