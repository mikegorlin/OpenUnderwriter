"""Financial distress scoring formulas (Ohlson O-Score, Piotroski F-Score).

Split from financial_formulas.py (Phase 45, 500-line rule).

Contains the multi-factor bankruptcy/distress probability models:
- compute_o_score: Ohlson O-Score (bankruptcy probability)
- compute_f_score: Piotroski F-Score (financial health, 0-9)

Zone classifiers, safe_ratio, and Beneish M-Score remain in
financial_formulas.py.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from do_uw.models.financials import DistressResult, DistressZone
from do_uw.stages.analyze.financial_formulas import (
    ohlson_zone,
    piotroski_zone,
    safe_ratio,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# GDP deflator approximation for Ohlson O-Score (2024 baseline).
_GDP_DEFLATOR: float = 130.0


# ---------------------------------------------------------------------------
# Model 3: Ohlson O-Score
# ---------------------------------------------------------------------------


def compute_o_score(
    inputs: dict[str, float | None],
) -> DistressResult:
    """Compute Ohlson O-Score bankruptcy probability.

    O = -1.32 - 0.407*log(TA/GNP) + 6.03*(TL/TA) - 1.43*(WC/TA)
        + 0.076*(CL/CA) - 1.72*X - 2.37*(NI/TA) - 1.83*(FFO/TL)
        + 0.285*OENEG - 0.521*CHIN
    """
    ta = inputs.get("total_assets")
    tl = inputs.get("total_liabilities")
    ca = inputs.get("current_assets")
    cl = inputs.get("current_liabilities")
    ni = inputs.get("net_income")
    ni_p = inputs.get("net_income_prior")
    ocf = inputs.get("operating_cash_flow")
    dep = inputs.get("depreciation_amortization")

    missing: list[str] = []
    required = {
        "total_assets": ta, "total_liabilities": tl,
        "current_assets": ca, "current_liabilities": cl,
        "net_income": ni, "operating_cash_flow": ocf,
    }
    for name, val in required.items():
        if val is None:
            missing.append(name)
            logger.warning("Ohlson O-Score: missing input %s", name)

    if ta is None or ta <= 0.0:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="ohlson",
        )

    available = sum(1 for v in required.values() if v is not None)
    if available < 4:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="ohlson",
        )

    log_ta_gnp = math.log(ta / _GDP_DEFLATOR) if ta > 0 else 0.0
    tl_ta = (tl or 0.0) / ta
    wc = (ca or 0.0) - (cl or 0.0)
    wc_ta = wc / ta
    cl_ca = (cl or 0.0) / ca if ca is not None and ca != 0.0 else 0.0

    # X = 1 if TL > TA, else 0.
    x = 1.0 if (tl or 0.0) > ta else 0.0

    ni_ta = (ni or 0.0) / ta

    # FFO = OCF + Depreciation (funds from operations).
    ffo = (ocf or 0.0) + (dep or 0.0)
    ffo_tl = ffo / tl if tl is not None and tl != 0.0 else 0.0

    # OENEG = 1 if NI < 0 in both current and prior year.
    oeneg = 0.0
    if ni is not None and ni < 0 and ni_p is not None and ni_p < 0:
        oeneg = 1.0
    if ni_p is None:
        missing.append("net_income_prior")

    # CHIN = (NI_t - NI_t-1) / (|NI_t| + |NI_t-1|)
    chin = 0.0
    if ni is not None and ni_p is not None:
        denom = abs(ni) + abs(ni_p)
        if denom > 0:
            chin = (ni - ni_p) / denom

    o_score = (
        -1.32
        - 0.407 * log_ta_gnp
        + 6.03 * tl_ta
        - 1.43 * wc_ta
        + 0.076 * cl_ca
        - 1.72 * x
        - 2.37 * ni_ta
        - 1.83 * ffo_tl
        + 0.285 * oeneg
        - 0.521 * chin
    )

    probability = math.exp(o_score) / (1.0 + math.exp(o_score))
    probability = round(probability, 4)

    return DistressResult(
        score=probability, zone=ohlson_zone(probability),
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="ohlson",
    )


# ---------------------------------------------------------------------------
# Model 4: Piotroski F-Score
# ---------------------------------------------------------------------------


def compute_f_score(
    inputs: dict[str, float | None],
) -> DistressResult:
    """Compute Piotroski F-Score (9 binary criteria, 0-9).

    Profitability (4):
      1. Positive net income
      2. Improving ROA (NI/TA > prior)
      3. Positive operating cash flow
      4. OCF > NI (accruals quality)

    Leverage/Liquidity (3):
      5. Decreasing long-term debt ratio (LTD/TA)
      6. Improving current ratio (CA/CL)
      7. No new share issuance

    Efficiency (2):
      8. Improving gross margin (GP/Revenue)
      9. Improving asset turnover (Revenue/TA)
    """
    ni = inputs.get("net_income")
    ni_p = inputs.get("net_income_prior")
    ta = inputs.get("total_assets")
    ta_p = inputs.get("total_assets_prior")
    ocf = inputs.get("operating_cash_flow")
    ltd = inputs.get("long_term_debt")
    ltd_p = inputs.get("long_term_debt_prior")
    ca = inputs.get("current_assets")
    ca_p = inputs.get("current_assets_prior")
    cl = inputs.get("current_liabilities")
    cl_p = inputs.get("current_liabilities_prior")
    shares = inputs.get("shares_outstanding")
    shares_p = inputs.get("shares_outstanding_prior")
    gp = inputs.get("gross_profit")
    gp_p = inputs.get("gross_profit_prior")
    rev = inputs.get("revenue")
    rev_p = inputs.get("revenue_prior")

    missing: list[str] = []
    criteria: list[dict[str, float | str]] = []
    total = 0

    # 1. Positive net income.
    if ni is not None:
        score = 1 if ni > 0 else 0
        total += score
        criteria.append({"criterion": "positive_ni", "score": float(score)})
    else:
        missing.append("net_income")
        criteria.append({"criterion": "positive_ni", "score": "N/A"})

    # 2. Improving ROA.
    roa_t = safe_ratio(ni, ta)
    roa_p = safe_ratio(ni_p, ta_p)
    if roa_t is not None and roa_p is not None:
        score = 1 if roa_t > roa_p else 0
        total += score
        criteria.append(
            {"criterion": "improving_roa", "score": float(score)}
        )
    else:
        if roa_t is None:
            missing.append("roa_current")
        if roa_p is None:
            missing.append("roa_prior")
        criteria.append({"criterion": "improving_roa", "score": "N/A"})

    # 3. Positive operating cash flow.
    if ocf is not None:
        score = 1 if ocf > 0 else 0
        total += score
        criteria.append(
            {"criterion": "positive_ocf", "score": float(score)}
        )
    else:
        missing.append("operating_cash_flow")
        criteria.append({"criterion": "positive_ocf", "score": "N/A"})

    # 4. OCF > NI (accruals quality).
    if ocf is not None and ni is not None:
        score = 1 if ocf > ni else 0
        total += score
        criteria.append(
            {"criterion": "ocf_exceeds_ni", "score": float(score)}
        )
    else:
        missing.append("ocf_vs_ni")
        criteria.append(
            {"criterion": "ocf_exceeds_ni", "score": "N/A"}
        )

    # 5. Decreasing LTD ratio.
    ltd_ratio_t = safe_ratio(ltd, ta)
    ltd_ratio_p = safe_ratio(ltd_p, ta_p)
    if ltd_ratio_t is not None and ltd_ratio_p is not None:
        score = 1 if ltd_ratio_t < ltd_ratio_p else 0
        total += score
        criteria.append(
            {"criterion": "decreasing_leverage", "score": float(score)}
        )
    else:
        missing.append("leverage_trend")
        criteria.append(
            {"criterion": "decreasing_leverage", "score": "N/A"}
        )

    # 6. Improving current ratio.
    cr_t = safe_ratio(ca, cl)
    cr_p = safe_ratio(ca_p, cl_p)
    if cr_t is not None and cr_p is not None:
        score = 1 if cr_t > cr_p else 0
        total += score
        criteria.append(
            {"criterion": "improving_current_ratio", "score": float(score)}
        )
    else:
        missing.append("current_ratio_trend")
        criteria.append(
            {"criterion": "improving_current_ratio", "score": "N/A"}
        )

    # 7. No share dilution.
    if shares is not None and shares_p is not None:
        score = 1 if shares <= shares_p else 0
        total += score
        criteria.append(
            {"criterion": "no_dilution", "score": float(score)}
        )
    else:
        missing.append("shares_outstanding_trend")
        criteria.append({"criterion": "no_dilution", "score": "N/A"})

    # 8. Improving gross margin.
    gm_t = safe_ratio(gp, rev)
    gm_p = safe_ratio(gp_p, rev_p)
    if gm_t is not None and gm_p is not None:
        score = 1 if gm_t > gm_p else 0
        total += score
        criteria.append(
            {"criterion": "improving_gross_margin", "score": float(score)}
        )
    else:
        missing.append("gross_margin_trend")
        criteria.append(
            {"criterion": "improving_gross_margin", "score": "N/A"}
        )

    # 9. Improving asset turnover.
    at_t = safe_ratio(rev, ta)
    at_p = safe_ratio(rev_p, ta_p)
    if at_t is not None and at_p is not None:
        score = 1 if at_t > at_p else 0
        total += score
        criteria.append(
            {"criterion": "improving_asset_turnover", "score": float(score)}
        )
    else:
        missing.append("asset_turnover_trend")
        criteria.append(
            {"criterion": "improving_asset_turnover", "score": "N/A"}
        )

    # Need at least 3 of 9 criteria evaluable for meaningful score
    available_criteria = 9 - len(missing)
    if available_criteria < 3:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="piotroski_9",
            trajectory=criteria,
        )

    zone = piotroski_zone(float(total))

    return DistressResult(
        score=float(total), zone=zone,
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="piotroski_9",
        trajectory=criteria,
    )
