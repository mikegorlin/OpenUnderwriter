"""Balance sheet forensic analysis module (FRNSC-01).

Computes 5 balance sheet health indicators from XBRL-extracted
FinancialStatements data. Pure computation -- zero LLM dependency.

Metrics:
1. Goodwill impairment risk (goodwill/TA with trend)
2. Intangible concentration ((goodwill+intangibles)/TA)
3. Off-balance-sheet ratio (operating leases/TA)
4. Cash conversion cycle (inventory days + DSO - DPO)
5. Working capital volatility (CV of current ratio across periods)
"""

from __future__ import annotations

import logging
import statistics

from do_uw.models.common import Confidence
from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import BalanceSheetForensics, ForensicMetric
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    collect_all_period_values,
    composite_confidence,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Zone thresholds
_GW_DANGER = 0.40
_GW_WARNING = 0.20
_INTANGIBLE_DANGER = 0.60
_INTANGIBLE_WARNING = 0.30
_OBS_DANGER = 0.15
_OBS_WARNING = 0.05
_CCC_DANGER = 120.0
_CCC_WARNING = 60.0
_WC_VOL_DANGER = 0.30
_WC_VOL_WARNING = 0.15

# Trend threshold (percentage point change)
_TREND_THRESHOLD = 0.05


def _classify_zone(
    value: float,
    danger_threshold: float,
    warning_threshold: float,
) -> str:
    """Classify a metric value into safe/warning/danger zone."""
    if value > danger_threshold:
        return "danger"
    if value > warning_threshold:
        return "warning"
    return "safe"


def _compute_trend(
    current: float | None,
    prior: float | None,
) -> str | None:
    """Compute trend from current vs prior value.

    Returns improving/stable/deteriorating based on change magnitude.
    """
    if current is None or prior is None:
        return None
    diff = current - prior
    if diff > _TREND_THRESHOLD:
        return "deteriorating"
    if diff < -_TREND_THRESHOLD:
        return "improving"
    return "stable"


def _compute_goodwill_to_assets(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute goodwill / total assets ratio with trend."""
    gw = extract_input(statements, "goodwill")
    ta = extract_input(statements, "total_assets")

    ratio = safe_ratio(gw, ta)
    if ratio is None:
        return ForensicMetric()

    # Prior period for trend
    gw_prior = extract_input(statements, "goodwill", period="prior")
    ta_prior = extract_input(statements, "total_assets", period="prior")
    ratio_prior = safe_ratio(gw_prior, ta_prior)
    trend = _compute_trend(ratio, ratio_prior)

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone(ratio, _GW_DANGER, _GW_WARNING),
        trend=trend,
        confidence=composite_confidence(
            statements, ["goodwill", "total_assets"]
        ),
    )


def _compute_intangible_concentration(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute (goodwill + intangible_assets) / total_assets."""
    gw = extract_input(statements, "goodwill")
    intangibles = extract_input(statements, "intangible_assets")
    ta = extract_input(statements, "total_assets")

    if ta is None or ta == 0.0:
        return ForensicMetric()

    # Either or both can be present
    numerator = (gw or 0.0) + (intangibles or 0.0)
    if gw is None and intangibles is None:
        return ForensicMetric()

    ratio = numerator / ta

    concepts = [c for c in ["goodwill", "intangible_assets", "total_assets"]
                if extract_input(statements, c) is not None]

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone(ratio, _INTANGIBLE_DANGER, _INTANGIBLE_WARNING),
        confidence=composite_confidence(statements, concepts),
    )


def _compute_off_balance_sheet(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute operating lease liabilities / total assets."""
    obs = extract_input(statements, "operating_lease_liabilities")
    ta = extract_input(statements, "total_assets")

    ratio = safe_ratio(obs, ta)
    if ratio is None:
        return ForensicMetric()

    return ForensicMetric(
        value=round(ratio, 4),
        zone=_classify_zone(ratio, _OBS_DANGER, _OBS_WARNING),
        confidence=composite_confidence(
            statements, ["operating_lease_liabilities", "total_assets"]
        ),
    )


def _compute_cash_conversion_cycle(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute CCC = inventory_days + DSO - DPO.

    inventory_days = inventory / cost_of_revenue * 365
    DSO = accounts_receivable / revenue * 365
    DPO = accounts_payable / cost_of_revenue * 365
    """
    inventory = extract_input(statements, "inventory")
    ar = extract_input(statements, "accounts_receivable")
    ap = extract_input(statements, "accounts_payable")
    revenue = extract_input(statements, "revenue")
    cogs = extract_input(statements, "cost_of_revenue")

    inv_days = safe_ratio(inventory, cogs)
    dso = safe_ratio(ar, revenue)
    dpo = safe_ratio(ap, cogs)

    if inv_days is None and dso is None:
        return ForensicMetric()

    inv_days_val = (inv_days or 0.0) * 365.0
    dso_val = (dso or 0.0) * 365.0
    dpo_val = (dpo or 0.0) * 365.0

    ccc = inv_days_val + dso_val - dpo_val

    concepts = []
    for c in ["inventory", "accounts_receivable", "accounts_payable",
              "revenue", "cost_of_revenue"]:
        if extract_input(statements, c) is not None:
            concepts.append(c)

    return ForensicMetric(
        value=round(ccc, 2),
        zone=_classify_zone(ccc, _CCC_DANGER, _CCC_WARNING),
        confidence=composite_confidence(statements, concepts),
    )


def _compute_working_capital_volatility(
    statements: FinancialStatements,
) -> ForensicMetric:
    """Compute coefficient of variation of current ratio across periods.

    CV = std(current_ratios) / mean(current_ratios)
    """
    ca_values = collect_all_period_values(statements, "current_assets")
    cl_values = collect_all_period_values(statements, "current_liabilities")

    if not ca_values or not cl_values:
        return ForensicMetric()

    # Build current ratio for each matching period
    ca_dict = dict(ca_values)
    cl_dict = dict(cl_values)
    common_periods = sorted(set(ca_dict.keys()) & set(cl_dict.keys()))

    ratios: list[float] = []
    for period in common_periods:
        cl_val = cl_dict[period]
        if cl_val != 0.0:
            ratios.append(ca_dict[period] / cl_val)

    if len(ratios) < 2:
        # Need at least 2 periods for volatility
        if ratios:
            return ForensicMetric(
                value=0.0,
                zone="safe",
                confidence=composite_confidence(
                    statements, ["current_assets", "current_liabilities"]
                ),
            )
        return ForensicMetric()

    mean_ratio = statistics.mean(ratios)
    if mean_ratio == 0.0:
        return ForensicMetric()

    stdev = statistics.stdev(ratios)
    cv = stdev / mean_ratio

    return ForensicMetric(
        value=round(cv, 4),
        zone=_classify_zone(cv, _WC_VOL_DANGER, _WC_VOL_WARNING),
        confidence=composite_confidence(
            statements, ["current_assets", "current_liabilities"]
        ),
    )


def compute_balance_sheet_forensics(
    statements: FinancialStatements,
) -> tuple[BalanceSheetForensics, ExtractionReport]:
    """Compute all 5 balance sheet forensic indicators.

    All inputs from XBRL-extracted FinancialStatements.
    Returns Pydantic model + ExtractionReport per FRNSC-06.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (BalanceSheetForensics, ExtractionReport).
    """
    expected = [
        "goodwill_to_assets",
        "intangible_concentration",
        "off_balance_sheet_ratio",
        "cash_conversion_cycle",
        "working_capital_volatility",
    ]

    gw = _compute_goodwill_to_assets(statements)
    intangible = _compute_intangible_concentration(statements)
    obs = _compute_off_balance_sheet(statements)
    ccc = _compute_cash_conversion_cycle(statements)
    wc_vol = _compute_working_capital_volatility(statements)

    result = BalanceSheetForensics(
        goodwill_to_assets=gw,
        intangible_concentration=intangible,
        off_balance_sheet_ratio=obs,
        cash_conversion_cycle=ccc,
        working_capital_volatility=wc_vol,
    )

    # Build found list from metrics that successfully computed
    found: list[str] = []
    metrics = [
        ("goodwill_to_assets", gw),
        ("intangible_concentration", intangible),
        ("off_balance_sheet_ratio", obs),
        ("cash_conversion_cycle", ccc),
        ("working_capital_volatility", wc_vol),
    ]
    for name, metric in metrics:
        if metric.zone != "insufficient_data":
            found.append(name)

    report = create_report(
        extractor_name="forensic_balance_sheet",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )

    logger.info(
        "Balance sheet forensics: %d/%d metrics computed",
        len(found), len(expected),
    )

    return result, report
