"""Debt and tax structure forensic analysis module (FRNSC-03).

Computes 5 debt/tax indicators from XBRL-extracted FinancialStatements
data. Pure computation -- zero LLM dependency.

Metrics:
1. Interest coverage trajectory (EBIT / interest_expense)
2. Debt maturity concentration (short_term_debt / total_debt)
3. ETR anomaly (effective tax rate vs statutory rate divergence)
4. Deferred tax growth vs revenue growth
5. Pension underfunding (pension_liability / stockholders_equity)
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence
from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import DebtTaxForensics, ForensicMetric
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    composite_confidence,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Interest coverage thresholds
_IC_DANGER = 1.5
_IC_WARNING = 3.0

# Debt maturity concentration thresholds
_MATURITY_DANGER = 0.50
_MATURITY_WARNING = 0.30

# ETR anomaly thresholds (absolute deviation from statutory rate)
_ETR_DANGER = 0.10
_ETR_WARNING = 0.05

# Deferred tax growth vs revenue ratio thresholds
_DTL_DANGER = 2.0
_DTL_WARNING = 1.5

# Pension underfunding thresholds
_PENSION_DANGER = 0.30
_PENSION_WARNING = 0.15

# US statutory corporate tax rate
_STATUTORY_TAX_RATE = 0.21

# Trend threshold (absolute change)
_TREND_THRESHOLD = 0.5


def _classify_zone_lower(
    value: float,
    danger_below: float,
    warning_below: float,
) -> str:
    """Classify zone where LOWER values are worse (e.g., interest coverage)."""
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
    """Classify zone where HIGHER values are worse."""
    if value > danger_above:
        return "danger"
    if value > warning_above:
        return "warning"
    return "safe"


def _compute_trend_coverage(
    current: float | None,
    prior: float | None,
) -> str | None:
    """Compute trend for interest coverage (higher = better)."""
    if current is None or prior is None:
        return None
    diff = current - prior
    if diff > _TREND_THRESHOLD:
        return "improving"
    if diff < -_TREND_THRESHOLD:
        return "deteriorating"
    return "stable"


def _compute_interest_coverage(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute interest coverage = EBIT / interest_expense with trend."""
    ebit = extract_input(statements, "ebit") or extract_input(
        statements, "operating_income"
    )
    interest = extract_input(statements, "interest_expense")

    coverage = safe_ratio(ebit, interest)
    if coverage is None:
        return ForensicMetric()

    # Prior period for trend
    ebit_prior = extract_input(statements, "ebit", "prior") or extract_input(
        statements, "operating_income", "prior"
    )
    interest_prior = extract_input(statements, "interest_expense", "prior")
    coverage_prior = safe_ratio(ebit_prior, interest_prior)
    trend = _compute_trend_coverage(coverage, coverage_prior)

    return ForensicMetric(
        value=round(coverage, 4),
        zone=_classify_zone_lower(coverage, _IC_DANGER, _IC_WARNING),
        trend=trend,
        confidence=composite_confidence(
            statements, ["ebit", "interest_expense"]
        ),
    )


def _compute_debt_maturity_concentration(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute short_term_debt / total_debt concentration."""
    short = extract_input(statements, "short_term_debt")
    total = extract_input(statements, "total_debt")

    ratio = safe_ratio(short, total)
    if ratio is None:
        return ForensicMetric()

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone_upper(ratio, _MATURITY_DANGER, _MATURITY_WARNING),
        confidence=composite_confidence(
            statements, ["short_term_debt", "total_debt"]
        ),
    )


def _compute_etr_anomaly(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute effective tax rate deviation from statutory rate.

    Flags both unusually high and low ETR as potential anomalies.
    Low ETR may indicate offshore structures or tax credits.
    High ETR may indicate prior-period adjustments or penalties.
    """
    tax = extract_input(statements, "income_tax_expense")
    pretax = extract_input(statements, "pretax_income")

    if tax is None or pretax is None or pretax <= 0:
        return ForensicMetric()

    etr = tax / pretax
    deviation = abs(etr - _STATUTORY_TAX_RATE)

    return ForensicMetric(
        value=round(etr, 4),
        zone=_classify_zone_upper(deviation, _ETR_DANGER, _ETR_WARNING),
        confidence=composite_confidence(
            statements, ["income_tax_expense", "pretax_income"]
        ),
    )


def _compute_deferred_tax_growth(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute deferred tax liability growth vs revenue growth.

    DTL growing much faster than revenue may indicate aggressive
    accounting or accumulating tax obligations.
    Phase 67 concept -- handles None gracefully.
    """
    dtl_current = extract_input(statements, "deferred_tax_liability")
    dtl_prior = extract_input(statements, "deferred_tax_liability", "prior")
    rev_current = extract_input(statements, "revenue")
    rev_prior = extract_input(statements, "revenue", "prior")

    if dtl_current is None or dtl_prior is None or dtl_prior == 0.0:
        return ForensicMetric()
    if rev_current is None or rev_prior is None or rev_prior == 0.0:
        return ForensicMetric()

    dtl_growth = (dtl_current - dtl_prior) / dtl_prior
    rev_growth = (rev_current - rev_prior) / rev_prior

    if rev_growth <= 0:
        # Revenue declining but DTL growing = concern
        if dtl_growth > 0:
            return ForensicMetric(
                value=round(dtl_growth, 4),
                zone="danger",
                confidence=composite_confidence(
                    statements, ["deferred_tax_liability", "revenue"]
                ),
            )
        return ForensicMetric()

    ratio = dtl_growth / rev_growth

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone_upper(ratio, _DTL_DANGER, _DTL_WARNING),
        confidence=composite_confidence(
            statements, ["deferred_tax_liability", "revenue"]
        ),
    )


def _compute_pension_underfunding(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute pension liability / stockholders equity.

    High pension underfunding relative to equity is a hidden leverage
    risk for D&O liability. Phase 67 concept -- handles None gracefully.
    """
    pension = extract_input(statements, "pension_liability")
    equity = extract_input(statements, "stockholders_equity")

    ratio = safe_ratio(pension, equity)
    if ratio is None:
        return ForensicMetric()

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone_upper(ratio, _PENSION_DANGER, _PENSION_WARNING),
        confidence=composite_confidence(
            statements, ["pension_liability", "stockholders_equity"]
        ),
    )


def compute_debt_tax_forensics(
    statements: FinancialStatements,
) -> tuple[DebtTaxForensics, ExtractionReport]:
    """Compute all 5 debt/tax forensic indicators.

    All inputs from XBRL-extracted FinancialStatements.
    Returns Pydantic model + ExtractionReport per FRNSC-06.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (DebtTaxForensics, ExtractionReport).
    """
    expected = [
        "interest_coverage",
        "debt_maturity_concentration",
        "etr_anomaly",
        "deferred_tax_growth",
        "pension_underfunding",
    ]

    ic = _compute_interest_coverage(statements)
    maturity = _compute_debt_maturity_concentration(statements)
    etr = _compute_etr_anomaly(statements)
    dtl = _compute_deferred_tax_growth(statements)
    pension = _compute_pension_underfunding(statements)

    result = DebtTaxForensics(
        interest_coverage=ic,
        debt_maturity_concentration=maturity,
        etr_anomaly=etr,
        deferred_tax_growth=dtl,
        pension_underfunding=pension,
    )

    # Build found list
    found: list[str] = []
    metrics = [
        ("interest_coverage", ic),
        ("debt_maturity_concentration", maturity),
        ("etr_anomaly", etr),
        ("deferred_tax_growth", dtl),
        ("pension_underfunding", pension),
    ]
    for name, metric in metrics:
        if metric.zone != "insufficient_data":
            found.append(name)

    report = create_report(
        extractor_name="forensic_debt_tax",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )

    logger.info(
        "Debt/tax forensics: %d/%d metrics computed",
        len(found),
        len(expected),
    )

    return result, report
