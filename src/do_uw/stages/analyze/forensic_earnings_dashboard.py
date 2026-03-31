"""Earnings quality dashboard forensic analysis (FRNSC-09).

Computes 4 earnings quality indicators:
1. Sloan Accruals: (NI - CFO - CFI) / avg_TA -- different from
   earnings_quality.py accruals_ratio which is (NI - CFO) / TA.
2. Cash flow manipulation index: OCF/NI ratio
3. SBC/revenue trend: stock_based_compensation / revenue
4. Non-GAAP gap: flagged as LIMITED / LOW confidence (not in XBRL)

Pure computation -- zero LLM dependency.
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence
from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import EarningsQualityDashboard, ForensicMetric
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    composite_confidence,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Sloan accruals zone thresholds
_SLOAN_DANGER = 0.25
_SLOAN_WARNING = 0.10

# Cash flow manipulation zone thresholds
_CFM_DANGER = 0.5
_CFM_WARNING = 0.8

# SBC/revenue zone thresholds
_SBC_DANGER = 0.10
_SBC_WARNING = 0.05


def _compute_sloan_accruals(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute Sloan accrual anomaly ratio.

    Sloan Accruals = (NI - CFO - CFI) / avg_TA

    Different from earnings_quality.py accruals_ratio which excludes
    investing cash flow (CFI). Sloan's version captures a broader
    measure of accrual quality.

    Zones: |value| < 0.10 safe, < 0.25 warning, else danger.
    """
    ni = extract_input(statements, "net_income")
    cfo = extract_input(statements, "operating_cash_flow")
    cfi = extract_input(statements, "investing_cash_flow")
    ta_current = extract_input(statements, "total_assets")
    ta_prior = extract_input(statements, "total_assets", period="prior")

    if ni is None or cfo is None or ta_current is None:
        return ForensicMetric()

    # CFI may be None -- treat as 0 (conservative: excludes investing)
    cfi_val = cfi if cfi is not None else 0.0

    # Average total assets
    if ta_prior is not None:
        avg_ta = (ta_current + ta_prior) / 2.0
    else:
        avg_ta = ta_current

    if avg_ta == 0.0:
        return ForensicMetric()

    sloan = (ni - cfo - cfi_val) / avg_ta
    abs_sloan = abs(sloan)

    # Zone classification on absolute value
    if abs_sloan >= _SLOAN_DANGER:
        zone = "danger"
    elif abs_sloan >= _SLOAN_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    concepts = ["net_income", "operating_cash_flow", "total_assets"]
    if cfi is not None:
        concepts.append("investing_cash_flow")

    return ForensicMetric(
        value=round(sloan, 4),
        zone=zone,
        confidence=composite_confidence(statements, concepts),
    )


def _compute_cash_flow_manipulation(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute cash flow manipulation index: OCF / NI.

    Healthy companies have OCF >= NI (ratio >= 1.0).
    Low ratio means earnings not backed by cash.

    Zones: < 0.5 danger, < 0.8 warning, else safe.
    """
    ocf = extract_input(statements, "operating_cash_flow")
    ni = extract_input(statements, "net_income")

    if ocf is None or ni is None or ni == 0.0:
        return ForensicMetric()

    ratio = ocf / ni

    if ratio < _CFM_DANGER:
        zone = "danger"
    elif ratio < _CFM_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(ratio, 4),
        zone=zone,
        confidence=composite_confidence(
            statements, ["operating_cash_flow", "net_income"]
        ),
    )


def _compute_sbc_revenue_ratio(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute stock-based compensation / revenue ratio.

    Phase 67 concept -- may not be available yet.

    Zones: > 10% danger, > 5% warning, else safe.
    """
    sbc = extract_input(statements, "stock_based_compensation")
    revenue = extract_input(statements, "revenue")

    if sbc is None or revenue is None or revenue == 0.0:
        return ForensicMetric()

    ratio = sbc / revenue

    if ratio > _SBC_DANGER:
        zone = "danger"
    elif ratio > _SBC_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(ratio, 4),
        zone=zone,
        confidence=composite_confidence(
            statements, ["stock_based_compensation", "revenue"]
        ),
    )


def _compute_non_gaap_gap() -> ForensicMetric:
    """Non-GAAP gap indicator -- always LIMITED.

    Non-GAAP earnings are not available in standard XBRL filings.
    Flagged as limited_data with LOW confidence per plan spec.
    """
    return ForensicMetric(
        value=None,
        zone="limited_data",
        confidence=Confidence.LOW,
    )


def compute_earnings_dashboard(
    statements: FinancialStatements,
) -> tuple[EarningsQualityDashboard, ExtractionReport]:
    """Compute earnings quality dashboard with 4 indicators.

    Provides Sloan accruals, cash flow manipulation index,
    SBC/revenue trend, and non-GAAP gap assessment.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (EarningsQualityDashboard, ExtractionReport).
    """
    expected = [
        "sloan_accruals",
        "cash_flow_manipulation",
        "sbc_revenue_ratio",
        "non_gaap_gap",
    ]

    sloan = _compute_sloan_accruals(statements)
    cfm = _compute_cash_flow_manipulation(statements)
    sbc = _compute_sbc_revenue_ratio(statements)
    non_gaap = _compute_non_gaap_gap()

    dashboard = EarningsQualityDashboard(
        sloan_accruals=sloan,
        cash_flow_manipulation=cfm,
        sbc_revenue_ratio=sbc,
        non_gaap_gap=non_gaap,
    )

    # Build found list
    found: list[str] = []
    metrics = [
        ("sloan_accruals", sloan),
        ("cash_flow_manipulation", cfm),
        ("sbc_revenue_ratio", sbc),
        ("non_gaap_gap", non_gaap),
    ]
    for name, metric in metrics:
        if metric.zone not in ("insufficient_data",):
            found.append(name)

    report = create_report(
        extractor_name="forensic_earnings_dashboard",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )

    logger.info(
        "Earnings dashboard: %d/%d metrics computed",
        len(found), len(expected),
    )

    return dashboard, report
