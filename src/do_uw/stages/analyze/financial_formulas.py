"""Distress model formulas -- zone classifiers, Beneish M-Score.

Contains zone classification helpers, safe_ratio, and Beneish M-Score
computation. Ohlson O-Score and Piotroski F-Score are in
financial_formulas_distress.py (split for 500-line compliance).

Zone classifiers and safe_ratio are public so financial_models.py and
tests can import them directly.
"""

from __future__ import annotations

import logging

from do_uw.models.financials import DistressResult, DistressZone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Zone classification helpers
# ---------------------------------------------------------------------------


def altman_zone_original(score: float) -> DistressZone:
    """Classify Altman Z-Score into zones (original formula)."""
    if score < 1.81:
        return DistressZone.DISTRESS
    if score <= 2.99:
        return DistressZone.GREY
    return DistressZone.SAFE


def altman_zone_double_prime(score: float) -> DistressZone:
    """Classify Altman Z''-Score into zones."""
    if score < 1.1:
        return DistressZone.DISTRESS
    if score <= 2.6:
        return DistressZone.GREY
    return DistressZone.SAFE


def beneish_zone(score: float) -> DistressZone:
    """Classify Beneish M-Score. > -1.78 means manipulation likely."""
    if score > -1.78:
        return DistressZone.DISTRESS
    return DistressZone.SAFE


def ohlson_zone(probability: float) -> DistressZone:
    """Classify Ohlson O-Score probability."""
    if probability > 0.5:
        return DistressZone.DISTRESS
    if probability >= 0.25:
        return DistressZone.GREY
    return DistressZone.SAFE


def piotroski_zone(score: float) -> DistressZone:
    """Classify Piotroski F-Score (0-9)."""
    if score >= 8:
        return DistressZone.SAFE
    if score >= 3:
        return DistressZone.GREY
    return DistressZone.DISTRESS


# ---------------------------------------------------------------------------
# Safe arithmetic
# ---------------------------------------------------------------------------


def safe_ratio(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    """Divide safely, returning None on zero-division or missing inputs."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0.0:
        return None
    return numerator / denominator


# ---------------------------------------------------------------------------
# Model 2: Beneish M-Score
# ---------------------------------------------------------------------------


def compute_m_score(
    inputs: dict[str, float | None],
) -> DistressResult:
    """Compute Beneish M-Score for earnings manipulation detection.

    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
        + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    """
    missing: list[str] = []

    recv_t = inputs.get("accounts_receivable")
    recv_p = inputs.get("accounts_receivable_prior")
    rev_t = inputs.get("revenue")
    rev_p = inputs.get("revenue_prior")
    gp_t = inputs.get("gross_profit")
    gp_p = inputs.get("gross_profit_prior")
    ca_t = inputs.get("current_assets")
    ca_p = inputs.get("current_assets_prior")
    ppe_t = inputs.get("property_plant_equipment")
    ppe_p = inputs.get("property_plant_equipment_prior")
    ta_t = inputs.get("total_assets")
    ta_p = inputs.get("total_assets_prior")
    dep_t = inputs.get("depreciation_amortization")
    dep_p = inputs.get("depreciation_amortization_prior")
    sga_t = inputs.get("sga_expense")
    sga_p = inputs.get("sga_expense_prior")
    ni_t = inputs.get("net_income")
    ocf_t = inputs.get("operating_cash_flow")
    tl_t = inputs.get("total_liabilities")
    tl_p = inputs.get("total_liabilities_prior")

    # DSRI = (Receivables_t/Revenue_t) / (Receivables_t-1/Revenue_t-1)
    dsri_num = safe_ratio(recv_t, rev_t)
    dsri_den = safe_ratio(recv_p, rev_p)
    dsri = safe_ratio(dsri_num, dsri_den)
    if dsri is None:
        missing.append("DSRI")

    # GMI = GrossMargin_t-1 / GrossMargin_t
    gm_t = safe_ratio(gp_t, rev_t)
    gm_p = safe_ratio(gp_p, rev_p)
    gmi = safe_ratio(gm_p, gm_t)
    if gmi is None:
        missing.append("GMI")

    # AQI = (1-(CA+PPE)/TA)_t / (1-(CA+PPE)/TA)_t-1
    aqi: float | None = None
    if (
        ca_t is not None and ppe_t is not None and ta_t is not None
        and ca_p is not None and ppe_p is not None and ta_p is not None
        and ta_t != 0.0 and ta_p != 0.0
    ):
        aq_t = 1.0 - (ca_t + ppe_t) / ta_t
        aq_p = 1.0 - (ca_p + ppe_p) / ta_p
        aqi = safe_ratio(aq_t, aq_p)
    if aqi is None:
        missing.append("AQI")

    # SGI = Revenue_t / Revenue_t-1
    sgi = safe_ratio(rev_t, rev_p)
    if sgi is None:
        missing.append("SGI")

    # DEPI = DepRate_t-1 / DepRate_t
    depi: float | None = None
    if (
        dep_t is not None and ppe_t is not None
        and dep_p is not None and ppe_p is not None
    ):
        dep_rate_t = safe_ratio(dep_t, dep_t + ppe_t)
        dep_rate_p = safe_ratio(dep_p, dep_p + ppe_p)
        depi = safe_ratio(dep_rate_p, dep_rate_t)
    if depi is None:
        missing.append("DEPI")

    # SGAI = (SGA_t/Revenue_t) / (SGA_t-1/Revenue_t-1)
    sgai_num = safe_ratio(sga_t, rev_t)
    sgai_den = safe_ratio(sga_p, rev_p)
    sgai = safe_ratio(sgai_num, sgai_den)
    if sgai is None:
        missing.append("SGAI")

    # TATA = (NI - OCF) / TA
    tata: float | None = None
    if (
        ni_t is not None and ocf_t is not None
        and ta_t is not None and ta_t != 0.0
    ):
        tata = (ni_t - ocf_t) / ta_t
    if tata is None:
        missing.append("TATA")

    # LVGI = (TL/TA)_t / (TL/TA)_t-1
    lvgi_num = safe_ratio(tl_t, ta_t)
    lvgi_den = safe_ratio(tl_p, ta_p)
    lvgi = safe_ratio(lvgi_num, lvgi_den)
    if lvgi is None:
        missing.append("LVGI")

    # Need > 50% of inputs (> 4 of 8) to compute.
    all_ratios = [dsri, gmi, aqi, sgi, depi, sgai, tata, lvgi]
    available_count = sum(1 for r in all_ratios if r is not None)

    if available_count < 5:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="beneish_8var",
        )

    # Populate individual components for Beneish decomposition (FRNSC-05)
    components: dict[str, float | None] = {
        "dsri": dsri, "gmi": gmi, "aqi": aqi, "sgi": sgi,
        "depi": depi, "sgai": sgai, "tata": tata, "lvgi": lvgi,
    }

    m = (
        -4.84
        + 0.920 * (dsri or 0.0)
        + 0.528 * (gmi or 0.0)
        + 0.404 * (aqi or 0.0)
        + 0.892 * (sgi or 0.0)
        + 0.115 * (depi or 0.0)
        - 0.172 * (sgai or 0.0)
        + 4.679 * (tata or 0.0)
        - 0.327 * (lvgi or 0.0)
    )
    m = round(m, 4)

    return DistressResult(
        score=m, zone=beneish_zone(m),
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="beneish_8var",
        components=components,
    )


