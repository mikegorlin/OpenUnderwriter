"""Revenue quality forensic analysis module (FRNSC-04).

Computes 4 revenue quality indicators from XBRL-extracted
FinancialStatements data. Pure computation -- zero LLM dependency.

Metrics:
1. Deferred revenue divergence (revenue growth vs deferred revenue growth)
2. Channel stuffing indicator (AR growth / revenue growth)
3. Margin compression (gross margin trend across periods)
4. OCF/revenue ratio (operating cash flow quality)

NOTE: Does NOT recompute DSO or accruals_ratio -- those already
exist in earnings_quality.py.
"""

from __future__ import annotations

import logging

from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import ForensicMetric, RevenueForensics
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    collect_all_period_values,
    composite_confidence,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Zone thresholds
_DIVERGENCE_DANGER = 0.20
_DIVERGENCE_WARNING = 0.10
_CHANNEL_STUFFING_DANGER = 2.0
_CHANNEL_STUFFING_WARNING = 1.5
_OCF_REV_DANGER = 0.05
_OCF_REV_WARNING = 0.10
_MARGIN_DECLINE_DANGER = 3  # 3+ declining transitions (= 4+ periods declining)
_MARGIN_DECLINE_WARNING = 2  # 2 declining transitions (= 3 periods declining)


def _compute_deferred_revenue_divergence(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute revenue growth vs deferred revenue growth divergence.

    Divergence = rev_growth - deferred_growth.
    Positive divergence (revenue growing much faster than deferred)
    may indicate premature revenue recognition.
    """
    rev_current = extract_input(statements, "revenue")
    rev_prior = extract_input(statements, "revenue", period="prior")
    def_current = extract_input(statements, "deferred_revenue")
    def_prior = extract_input(statements, "deferred_revenue", period="prior")

    rev_growth = safe_ratio(
        (rev_current - rev_prior) if rev_current is not None and rev_prior is not None else None,
        rev_prior,
    )
    def_growth = safe_ratio(
        (def_current - def_prior) if def_current is not None and def_prior is not None else None,
        def_prior,
    )

    if rev_growth is None or def_growth is None:
        return ForensicMetric()

    divergence = rev_growth - def_growth

    # Zone: positive divergence = revenue growing faster than deferred = concern
    if divergence > _DIVERGENCE_DANGER:
        zone = "danger"
    elif divergence > _DIVERGENCE_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(divergence, 4),
        zone=zone,
        confidence=composite_confidence(
            statements, ["revenue", "deferred_revenue"]
        ),
    )


def _compute_channel_stuffing(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute AR growth / revenue growth ratio.

    High ratio (AR growing much faster than revenue) may indicate
    channel stuffing or aggressive revenue recognition.
    """
    ar_current = extract_input(statements, "accounts_receivable")
    ar_prior = extract_input(statements, "accounts_receivable", period="prior")
    rev_current = extract_input(statements, "revenue")
    rev_prior = extract_input(statements, "revenue", period="prior")

    ar_growth = safe_ratio(
        (ar_current - ar_prior) if ar_current is not None and ar_prior is not None else None,
        ar_prior,
    )
    rev_growth = safe_ratio(
        (rev_current - rev_prior) if rev_current is not None and rev_prior is not None else None,
        rev_prior,
    )

    if ar_growth is None or rev_growth is None:
        return ForensicMetric()

    # Only meaningful when revenue is growing
    if rev_growth <= 0:
        # Revenue flat/declining -- AR growth alone is the signal
        if ar_growth > 0.20:
            return ForensicMetric(
                value=round(ar_growth, 4),
                zone="warning",
                confidence=composite_confidence(
                    statements, ["accounts_receivable", "revenue"]
                ),
            )
        return ForensicMetric(
            value=round(ar_growth, 4),
            zone="safe",
            confidence=composite_confidence(
                statements, ["accounts_receivable", "revenue"]
            ),
        )

    ratio = ar_growth / rev_growth

    if ratio > _CHANNEL_STUFFING_DANGER:
        zone = "danger"
    elif ratio > _CHANNEL_STUFFING_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(ratio, 4),
        zone=zone,
        confidence=composite_confidence(
            statements, ["accounts_receivable", "revenue"]
        ),
    )


def _compute_margin_compression(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute gross margin trend across periods.

    4+ periods of declining margin = danger pattern.
    2-3 declining = warning.
    """
    rev_values = collect_all_period_values(statements, "revenue")
    gp_values = collect_all_period_values(statements, "gross_profit")

    if not rev_values or not gp_values:
        return ForensicMetric()

    rev_dict = dict(rev_values)
    gp_dict = dict(gp_values)
    common = sorted(set(rev_dict.keys()) & set(gp_dict.keys()))

    if len(common) < 2:
        # Need at least 2 periods to detect trend
        if common:
            rev_val = rev_dict[common[0]]
            if rev_val and rev_val != 0:
                margin = gp_dict[common[0]] / rev_val
                return ForensicMetric(
                    value=round(margin, 4),
                    zone="safe",
                    confidence=composite_confidence(
                        statements, ["revenue", "gross_profit"]
                    ),
                )
        return ForensicMetric()

    # Compute margins per period
    margins: list[float] = []
    for period in common:
        r = rev_dict[period]
        if r and r != 0:
            margins.append(gp_dict[period] / r)

    if len(margins) < 2:
        return ForensicMetric()

    # Count consecutive declining periods
    declining_count = 0
    for i in range(1, len(margins)):
        if margins[i] < margins[i - 1]:
            declining_count += 1

    # Latest margin as the metric value
    latest_margin = margins[-1]

    # Trend determination
    if margins[-1] < margins[0]:
        trend = "deteriorating"
    elif margins[-1] > margins[0]:
        trend = "improving"
    else:
        trend = "stable"

    if declining_count >= _MARGIN_DECLINE_DANGER:
        zone = "danger"
    elif declining_count >= _MARGIN_DECLINE_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(latest_margin, 4),
        zone=zone,
        trend=trend,
        confidence=composite_confidence(
            statements, ["revenue", "gross_profit"]
        ),
    )


def _compute_ocf_revenue(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute operating cash flow / revenue ratio.

    Low OCF/revenue suggests earnings quality concerns.
    """
    ocf = extract_input(statements, "operating_cash_flow")
    rev = extract_input(statements, "revenue")

    ratio = safe_ratio(ocf, rev)
    if ratio is None:
        return ForensicMetric()

    if ratio < _OCF_REV_DANGER:
        zone = "danger"
    elif ratio < _OCF_REV_WARNING:
        zone = "warning"
    else:
        zone = "safe"

    return ForensicMetric(
        value=round(ratio, 4),
        zone=zone,
        confidence=composite_confidence(
            statements, ["operating_cash_flow", "revenue"]
        ),
    )


def compute_revenue_forensics(
    statements: FinancialStatements,
) -> tuple[RevenueForensics, ExtractionReport]:
    """Compute all 4 revenue quality forensic indicators.

    All inputs from XBRL-extracted FinancialStatements.
    Returns Pydantic model + ExtractionReport per FRNSC-06.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (RevenueForensics, ExtractionReport).
    """
    expected = [
        "deferred_revenue_divergence",
        "channel_stuffing_indicator",
        "margin_compression",
        "ocf_revenue_ratio",
    ]

    div = _compute_deferred_revenue_divergence(statements)
    channel = _compute_channel_stuffing(statements)
    margin = _compute_margin_compression(statements)
    ocf = _compute_ocf_revenue(statements)

    result = RevenueForensics(
        deferred_revenue_divergence=div,
        channel_stuffing_indicator=channel,
        margin_compression=margin,
        ocf_revenue_ratio=ocf,
    )

    found: list[str] = []
    metrics = [
        ("deferred_revenue_divergence", div),
        ("channel_stuffing_indicator", channel),
        ("margin_compression", margin),
        ("ocf_revenue_ratio", ocf),
    ]
    for name, metric in metrics:
        if metric.zone != "insufficient_data":
            found.append(name)

    report = create_report(
        extractor_name="forensic_revenue",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )

    logger.info(
        "Revenue forensics: %d/%d metrics computed",
        len(found), len(expected),
    )

    return result, report
