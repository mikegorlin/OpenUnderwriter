"""Capital allocation forensic analysis module (FRNSC-02).

Computes 4 capital deployment quality indicators from XBRL-extracted
FinancialStatements data. Pure computation -- zero LLM dependency.

Metrics:
1. ROIC trend (return on invested capital)
2. Acquisition effectiveness (goodwill growth vs revenue growth)
3. Buyback timing quality (implied repurchase price vs market price)
4. Dividend sustainability (FCF payout ratio)
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.common import Confidence
from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import CapitalAllocationForensics, ForensicMetric
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    composite_confidence,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# ROIC zone thresholds
_ROIC_DANGER = 0.05
_ROIC_WARNING = 0.10

# Acquisition effectiveness: goodwill_growth / revenue_growth ratio
_ACQ_DANGER = 2.0
_ACQ_WARNING = 1.5

# Buyback timing: implied price premium over average
_BUYBACK_DANGER = 1.3
_BUYBACK_WARNING = 1.1

# Dividend sustainability: FCF payout ratio
_DIV_DANGER = 1.0
_DIV_WARNING = 0.8

# Trend threshold (absolute change in ratio)
_TREND_THRESHOLD = 0.02

# US statutory corporate tax rate fallback
_STATUTORY_TAX_RATE = 0.21


def _classify_zone_lower(
    value: float,
    danger_below: float,
    warning_below: float,
) -> str:
    """Classify zone where LOWER values are worse (e.g., ROIC)."""
    if value < danger_below:
        return "danger"
    if value < warning_below:
        return "warning"
    return "safe"


def _classify_zone_upper(
    value: float,
    danger_above: float,
    warning_above: float,
) -> str:
    """Classify zone where HIGHER values are worse (e.g., payout ratio)."""
    if value > danger_above:
        return "danger"
    if value > warning_above:
        return "warning"
    return "safe"


def _compute_trend(
    current: float | None,
    prior: float | None,
) -> str | None:
    """Compute trend from current vs prior value.

    For ROIC: increasing = improving, decreasing = deteriorating.
    """
    if current is None or prior is None:
        return None
    diff = current - prior
    if diff > _TREND_THRESHOLD:
        return "improving"
    if diff < -_TREND_THRESHOLD:
        return "deteriorating"
    return "stable"


def _compute_roic(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute ROIC = NOPAT / invested_capital with trend.

    NOPAT = EBIT * (1 - effective_tax_rate)
    Invested capital = equity + total_debt - cash
    """
    ebit = extract_input(statements, "ebit") or extract_input(
        statements, "operating_income"
    )
    tax = extract_input(statements, "income_tax_expense")
    pretax = extract_input(statements, "pretax_income")
    equity = extract_input(statements, "stockholders_equity")
    total_debt = extract_input(statements, "total_debt")
    cash = extract_input(statements, "cash_and_equivalents")

    if ebit is None or equity is None:
        return ForensicMetric()

    # Effective tax rate with statutory fallback
    tax_rate: float | None = None
    if tax is not None and pretax is not None and pretax > 0:
        tax_rate = tax / pretax
    if tax_rate is None or tax_rate < 0:
        tax_rate = _STATUTORY_TAX_RATE

    nopat = ebit * (1.0 - tax_rate)
    invested_capital = (equity or 0.0) + (total_debt or 0.0) - (cash or 0.0)

    roic = safe_ratio(nopat, invested_capital)
    if roic is None:
        return ForensicMetric()

    # Prior period ROIC for trend
    ebit_prior = extract_input(statements, "ebit", "prior") or extract_input(
        statements, "operating_income", "prior"
    )
    tax_prior = extract_input(statements, "income_tax_expense", "prior")
    pretax_prior = extract_input(statements, "pretax_income", "prior")
    equity_prior = extract_input(statements, "stockholders_equity", "prior")
    debt_prior = extract_input(statements, "total_debt", "prior")
    cash_prior = extract_input(statements, "cash_and_equivalents", "prior")

    roic_prior: float | None = None
    if ebit_prior is not None and equity_prior is not None:
        tax_rate_prior = _STATUTORY_TAX_RATE
        if (
            tax_prior is not None
            and pretax_prior is not None
            and pretax_prior > 0
        ):
            tax_rate_prior = tax_prior / pretax_prior
        if tax_rate_prior < 0:
            tax_rate_prior = _STATUTORY_TAX_RATE
        nopat_prior = ebit_prior * (1.0 - tax_rate_prior)
        ic_prior = (
            (equity_prior or 0.0)
            + (debt_prior or 0.0)
            - (cash_prior or 0.0)
        )
        roic_prior = safe_ratio(nopat_prior, ic_prior)

    trend = _compute_trend(roic, roic_prior)

    concepts = [
        "ebit",
        "income_tax_expense",
        "pretax_income",
        "stockholders_equity",
        "total_debt",
        "cash_and_equivalents",
    ]

    return ForensicMetric(
        value=round(roic, 4),
        zone=_classify_zone_lower(roic, _ROIC_DANGER, _ROIC_WARNING),
        trend=trend,
        confidence=composite_confidence(statements, concepts),
    )


def _compute_acquisition_effectiveness(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute goodwill growth rate vs revenue growth rate.

    If goodwill is growing 2x+ faster than revenue, management may be
    overpaying for acquisitions (danger signal).
    """
    gw_current = extract_input(statements, "goodwill")
    gw_prior = extract_input(statements, "goodwill", "prior")
    rev_current = extract_input(statements, "revenue")
    rev_prior = extract_input(statements, "revenue", "prior")

    if gw_current is None or gw_prior is None or gw_prior == 0.0:
        return ForensicMetric()
    if rev_current is None or rev_prior is None or rev_prior == 0.0:
        return ForensicMetric()

    gw_growth = (gw_current - gw_prior) / gw_prior
    rev_growth = (rev_current - rev_prior) / rev_prior

    if rev_growth <= 0:
        # Revenue declining but goodwill growing = danger
        if gw_growth > 0:
            return ForensicMetric(
                value=round(gw_growth, 4),
                zone="danger",
                confidence=composite_confidence(
                    statements, ["goodwill", "revenue"]
                ),
            )
        return ForensicMetric()

    ratio = gw_growth / rev_growth

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone_upper(ratio, _ACQ_DANGER, _ACQ_WARNING),
        confidence=composite_confidence(
            statements, ["goodwill", "revenue"]
        ),
    )


def _compute_buyback_timing(
    statements: FinancialStatements,
    market_data: dict[str, Any] | None = None,
) -> ForensicMetric:
    """Compute buyback timing quality.

    implied_price = repurchase_spend / shares_retired
    premium = implied_price / avg_stock_price
    """
    repurchases_raw = extract_input(statements, "share_repurchases")
    repurchases = abs(repurchases_raw) if repurchases_raw is not None else 0.0

    if repurchases == 0.0:
        return ForensicMetric(zone="not_applicable")

    shares_current = extract_input(statements, "shares_outstanding")
    shares_prior = extract_input(statements, "shares_outstanding", "prior")

    if shares_current is None or shares_prior is None:
        return ForensicMetric()

    shares_retired = shares_prior - shares_current
    if shares_retired <= 0:
        return ForensicMetric()

    implied_price = repurchases / shares_retired

    # Need market data for premium calculation
    if market_data is None:
        return ForensicMetric()

    avg_price = getattr(market_data, "avg_close", None) if not isinstance(market_data, dict) else market_data.get("avg_close")
    if avg_price is None or avg_price <= 0:
        return ForensicMetric()

    premium = implied_price / avg_price

    concepts = ["share_repurchases", "shares_outstanding"]

    return ForensicMetric(
        value=round(premium, 4),
        zone=_classify_zone_upper(premium, _BUYBACK_DANGER, _BUYBACK_WARNING),
        confidence=composite_confidence(statements, concepts),
    )


def _compute_dividend_sustainability(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute dividend payout ratio vs FCF.

    payout_ratio = dividends_paid / (OCF - capex)
    Uses FCF, not net income, for true sustainability.
    """
    dividends_raw = extract_input(statements, "dividends_paid")
    dividends = abs(dividends_raw) if dividends_raw is not None else 0.0

    if dividends == 0.0:
        return ForensicMetric(zone="not_applicable")

    ocf = extract_input(statements, "operating_cash_flow")
    capex_raw = extract_input(statements, "capital_expenditures")
    capex = abs(capex_raw) if capex_raw is not None else 0.0

    if ocf is None:
        return ForensicMetric()

    fcf = ocf - capex
    if fcf <= 0:
        # Negative FCF but paying dividends = danger
        return ForensicMetric(
            value=None,
            zone="danger",
            confidence=composite_confidence(
                statements,
                ["dividends_paid", "operating_cash_flow", "capital_expenditures"],
            ),
        )

    payout_ratio = dividends / fcf

    return ForensicMetric(
        value=round(payout_ratio, 4),
        zone=_classify_zone_upper(payout_ratio, _DIV_DANGER, _DIV_WARNING),
        confidence=composite_confidence(
            statements,
            ["dividends_paid", "operating_cash_flow", "capital_expenditures"],
        ),
    )


def compute_capital_allocation_forensics(
    statements: FinancialStatements,
    market_data: dict[str, Any] | None = None,
) -> tuple[CapitalAllocationForensics, ExtractionReport]:
    """Compute all 4 capital allocation forensic indicators.

    All inputs from XBRL-extracted FinancialStatements.
    Returns Pydantic model + ExtractionReport per FRNSC-06.

    Args:
        statements: Extracted financial statements.
        market_data: Optional market data dict with 'avg_close' key.

    Returns:
        Tuple of (CapitalAllocationForensics, ExtractionReport).
    """
    expected = [
        "roic",
        "acquisition_effectiveness",
        "buyback_timing",
        "dividend_sustainability",
    ]

    roic = _compute_roic(statements)
    acq = _compute_acquisition_effectiveness(statements)
    buyback = _compute_buyback_timing(statements, market_data)
    div = _compute_dividend_sustainability(statements)

    result = CapitalAllocationForensics(
        roic=roic,
        acquisition_effectiveness=acq,
        buyback_timing=buyback,
        dividend_sustainability=div,
    )

    # Build found list from metrics that successfully computed
    found: list[str] = []
    metrics = [
        ("roic", roic),
        ("acquisition_effectiveness", acq),
        ("buyback_timing", buyback),
        ("dividend_sustainability", div),
    ]
    for name, metric in metrics:
        if metric.zone not in ("insufficient_data",):
            found.append(name)

    report = create_report(
        extractor_name="forensic_capital_alloc",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )

    logger.info(
        "Capital allocation forensics: %d/%d metrics computed",
        len(found),
        len(expected),
    )

    return result, report
