"""Earnings quality forensic analysis ratios.

Computes accruals ratio, OCF/NI, DSO trend, asset quality, cash flow
adequacy, and overall quality score from extracted financial statements.

Covers SECT3-06 (earnings quality metrics).

Usage:
    quality, report = compute_earnings_quality(statements)
    state.extracted.financials.earnings_quality = quality
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    FinancialLineItem,
    FinancialStatements,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Thresholds for quality flags.
ACCRUALS_RED_FLAG: float = 0.10
OCF_NI_LOW: float = 0.5
OCF_NI_HEALTHY_LOW: float = 0.8
OCF_NI_HEALTHY_HIGH: float = 1.5
CASH_FLOW_ADEQUACY_MIN: float = 1.0


class QualityScore(StrEnum):
    """Overall earnings quality assessment."""

    STRONG = "STRONG"
    ADEQUATE = "ADEQUATE"
    WEAK = "WEAK"
    RED_FLAG = "RED_FLAG"


# ---------------------------------------------------------------------------
# Line item helpers (shared pattern with distress_models.py)
# ---------------------------------------------------------------------------


def _find_item(
    items: list[FinancialLineItem], concept: str
) -> FinancialLineItem | None:
    """Find a line item by XBRL concept name."""
    for item in items:
        if item.xbrl_concept == concept:
            return item
    return None


def _latest_value(item: FinancialLineItem) -> float | None:
    """Get the most recent period value."""
    if not item.values:
        return None
    for key in sorted(item.values.keys(), reverse=True):
        sv = item.values.get(key)
        if sv is not None:
            return sv.value
    return None


def _prior_value(item: FinancialLineItem) -> float | None:
    """Get the second-most-recent period value."""
    if not item.values or len(item.values) < 2:
        return None
    sorted_keys = sorted(item.values.keys())
    if len(sorted_keys) < 2:
        return None
    sv = item.values.get(sorted_keys[-2])
    return sv.value if sv is not None else None


def _get_val(
    statements: FinancialStatements,
    concept: str,
    period: str = "latest",
) -> float | None:
    """Extract a value from any statement by concept name."""
    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = _find_item(stmt.line_items, concept)
        if item is None:
            continue
        val = _prior_value(item) if period == "prior" else _latest_value(item)
        if val is not None:
            return val
    return None


# ---------------------------------------------------------------------------
# Individual metric computations
# ---------------------------------------------------------------------------


def _accruals_ratio(
    ni: float | None,
    ocf: float | None,
    ta: float | None,
) -> float | None:
    """Accruals Ratio = (NI - OCF) / TA.

    Positive = less earnings quality (cash lags income).
    """
    if ni is None or ocf is None or ta is None or ta == 0.0:
        return None
    return round((ni - ocf) / ta, 4)


def _ocf_to_ni_ratio(
    ocf: float | None,
    ni: float | None,
) -> float | None:
    """Operating Cash Flow to Net Income = OCF / NI.

    Healthy range: 0.8 to 1.5.
    Below 0.5 = poor earnings quality.
    """
    if ocf is None or ni is None or ni == 0.0:
        return None
    return round(ocf / ni, 4)


def _dso(
    receivables: float | None,
    revenue: float | None,
) -> float | None:
    """Days Sales Outstanding = (AR / Revenue) * 365."""
    if receivables is None or revenue is None or revenue == 0.0:
        return None
    return round((receivables / revenue) * 365.0, 2)


def _asset_quality_flag(
    ta: float | None,
    ta_p: float | None,
    ca: float | None,
    ca_p: float | None,
    rev: float | None,
    rev_p: float | None,
) -> float | None:
    """Non-current asset growth vs revenue growth comparison.

    Returns delta: (nca_growth - revenue_growth). Positive means
    non-current assets grew faster than revenue -- possible
    capitalization of expenses.
    """
    if (
        ta is None or ta_p is None
        or ca is None or ca_p is None
        or rev is None or rev_p is None
    ):
        return None

    nca_t = ta - ca
    nca_p = ta_p - ca_p
    if nca_p == 0.0 or rev_p == 0.0:
        return None
    nca_growth = (nca_t - nca_p) / abs(nca_p)
    rev_growth = (rev - rev_p) / abs(rev_p)
    return round(nca_growth - rev_growth, 4)


def _cash_flow_adequacy(
    ocf: float | None,
    capex: float | None,
    dividends: float | None,
) -> float | None:
    """Cash Flow Adequacy = OCF / (CapEx + Debt Payments + Dividends).

    Below 1.0 = company cannot fund obligations from operations.
    Uses CapEx + Dividends as proxy (debt payments often unavailable).
    """
    if ocf is None:
        return None
    denom = abs(capex or 0.0) + abs(dividends or 0.0)
    if denom == 0.0:
        return None
    return round(ocf / denom, 4)


# ---------------------------------------------------------------------------
# Quality score aggregation
# ---------------------------------------------------------------------------


def _determine_quality_score(
    metrics: dict[str, float | None],
) -> QualityScore:
    """Aggregate individual metrics into overall quality assessment.

    Counts red flags from individual metrics:
    - Accruals ratio > 0.10
    - OCF/NI < 0.5 or negative (different signs)
    - DSO increasing > 10%
    - Asset quality flag > 0.10 (non-current growing faster than revenue)
    - Cash flow adequacy < 1.0

    0 flags = STRONG, 1 = ADEQUATE, 2 = WEAK, 3+ = RED_FLAG.
    """
    flags = 0

    accruals = metrics.get("accruals_ratio")
    if accruals is not None and accruals > ACCRUALS_RED_FLAG:
        flags += 1

    ocf_ni = metrics.get("ocf_to_ni")
    if ocf_ni is not None and (ocf_ni < OCF_NI_LOW or ocf_ni < 0):
        flags += 1

    dso_delta = metrics.get("dso_delta")
    if dso_delta is not None and dso_delta > 10.0:
        flags += 1

    asset_q = metrics.get("asset_quality_delta")
    if asset_q is not None and asset_q > 0.10:
        flags += 1

    cfa = metrics.get("cash_flow_adequacy")
    if cfa is not None and cfa < CASH_FLOW_ADEQUACY_MIN:
        flags += 1

    if flags == 0:
        return QualityScore.STRONG
    if flags == 1:
        return QualityScore.ADEQUATE
    if flags == 2:
        return QualityScore.WEAK
    return QualityScore.RED_FLAG


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def compute_earnings_quality(
    statements: FinancialStatements,
) -> tuple[SourcedValue[dict[str, float | None]] | None, ExtractionReport]:
    """Compute earnings quality forensic analysis ratios.

    Analyzes accruals, OCF/NI, DSO trend, asset quality, and cash
    flow adequacy. Returns a SourcedValue wrapping the metrics dict
    and an ExtractionReport documenting coverage.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (SourcedValue with metrics dict, ExtractionReport).
    """
    expected_metrics = [
        "accruals_ratio", "ocf_to_ni", "dso_current",
        "dso_prior", "dso_delta", "asset_quality_delta",
        "cash_flow_adequacy", "quality_score",
    ]
    found_metrics: list[str] = []
    metrics: dict[str, float | None] = {}

    # Extract required inputs.
    ni = _get_val(statements, "net_income")
    ocf = _get_val(statements, "operating_cash_flow")
    ta = _get_val(statements, "total_assets")
    ta_p = _get_val(statements, "total_assets", "prior")
    ca = _get_val(statements, "current_assets")
    ca_p = _get_val(statements, "current_assets", "prior")
    recv = _get_val(statements, "accounts_receivable")
    recv_p = _get_val(statements, "accounts_receivable", "prior")
    rev = _get_val(statements, "revenue")
    rev_p = _get_val(statements, "revenue", "prior")
    capex = _get_val(statements, "capital_expenditures")
    dividends = _get_val(statements, "dividends_paid")

    # 1. Accruals Ratio.
    accruals = _accruals_ratio(ni, ocf, ta)
    metrics["accruals_ratio"] = accruals
    if accruals is not None:
        found_metrics.append("accruals_ratio")
        if accruals > ACCRUALS_RED_FLAG:
            logger.warning(
                "Earnings quality: high accruals ratio %.4f (>%.2f)",
                accruals, ACCRUALS_RED_FLAG,
            )

    # 2. OCF/NI Ratio.
    ocf_ni = _ocf_to_ni_ratio(ocf, ni)
    metrics["ocf_to_ni"] = ocf_ni
    if ocf_ni is not None:
        found_metrics.append("ocf_to_ni")
        if ocf_ni < OCF_NI_LOW:
            logger.warning(
                "Earnings quality: low OCF/NI ratio %.4f (<%.1f)",
                ocf_ni, OCF_NI_LOW,
            )

    # 3. DSO trend.
    dso_current = _dso(recv, rev)
    dso_prior = _dso(recv_p, rev_p)
    metrics["dso_current"] = dso_current
    metrics["dso_prior"] = dso_prior
    if dso_current is not None:
        found_metrics.append("dso_current")
    if dso_prior is not None:
        found_metrics.append("dso_prior")

    dso_delta: float | None = None
    if dso_current is not None and dso_prior is not None and dso_prior != 0.0:
        dso_delta = round(
            (dso_current - dso_prior) / abs(dso_prior) * 100.0, 2
        )
        found_metrics.append("dso_delta")
        if dso_delta > 10.0:
            logger.warning(
                "Earnings quality: DSO increased %.1f%% YoY", dso_delta
            )
    metrics["dso_delta"] = dso_delta

    # 4. Asset quality.
    asset_delta = _asset_quality_flag(ta, ta_p, ca, ca_p, rev, rev_p)
    metrics["asset_quality_delta"] = asset_delta
    if asset_delta is not None:
        found_metrics.append("asset_quality_delta")

    # 5. Cash flow adequacy.
    cfa = _cash_flow_adequacy(ocf, capex, dividends)
    metrics["cash_flow_adequacy"] = cfa
    if cfa is not None:
        found_metrics.append("cash_flow_adequacy")
        if cfa < CASH_FLOW_ADEQUACY_MIN:
            logger.warning(
                "Earnings quality: low cash flow adequacy %.4f (<%.1f)",
                cfa, CASH_FLOW_ADEQUACY_MIN,
            )

    # 6. Quality score summary.
    quality = _determine_quality_score(metrics)
    # Store as float for dict compatibility (0=STRONG,1=ADEQUATE,2=WEAK,3=RED_FLAG)
    quality_map: dict[QualityScore, float] = {
        QualityScore.STRONG: 0.0,
        QualityScore.ADEQUATE: 1.0,
        QualityScore.WEAK: 2.0,
        QualityScore.RED_FLAG: 3.0,
    }
    metrics["quality_score"] = quality_map[quality]
    found_metrics.append("quality_score")

    report = create_report(
        extractor_name="earnings_quality",
        expected=expected_metrics,
        found=found_metrics,
        source_filing="Derived from XBRL financial statements",
    )

    if not found_metrics:
        logger.warning("Earnings quality: no metrics could be computed")
        return None, report

    sv: SourcedValue[dict[str, float | None]] = SourcedValue(
        value=metrics,
        source="Derived from XBRL financial statements",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )

    logger.info(
        "Earnings quality: %d/%d metrics computed, score=%s",
        len(found_metrics), len(expected_metrics), quality.value,
    )

    return sv, report
