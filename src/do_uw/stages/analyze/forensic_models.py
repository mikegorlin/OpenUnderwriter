"""Individual forensic model computations for manipulation detection.

Models: Dechow F-Score, Montier C-Score, Enhanced Sloan Ratio, Accrual Intensity.
Each operates on ExtractedData and returns (score, evidence_narrative).
Feeds into composite scores (FIS, RQS, CFQS) in forensic_composites.py.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)


def _safe_ratio(num: float | None, den: float | None) -> float | None:
    """Divide safely, returning None on zero-division or missing inputs."""
    if num is None or den is None or den == 0.0:
        return None
    return num / den


def _get_line_item_value(
    extracted: ExtractedData, statement_type: str,
    label: str, period_index: int = 0,
) -> float | None:
    """Extract a financial line item value (case-insensitive contains match)."""
    if extracted.financials is None:
        return None
    stmts = extracted.financials.statements
    if stmts is None:
        return None
    statement = getattr(stmts, statement_type, None)
    if statement is None:
        return None
    periods = statement.periods
    if period_index >= len(periods):
        return None
    period_label = periods[period_index]
    label_lower = label.lower()
    for item in statement.line_items:
        if label_lower in item.label.lower():
            sv = item.values.get(period_label)
            if sv is not None:
                return sv.value
    return None


def _get_distress_score(extracted: ExtractedData, model_name: str) -> float | None:
    """Get a pre-computed distress model score from ExtractedData."""
    if extracted.financials is None or extracted.financials.distress is None:
        return None
    result = getattr(extracted.financials.distress, model_name, None)
    return result.score if result is not None else None


def _get_earnings_quality_field(extracted: ExtractedData, key: str) -> float | None:
    """Get a field from earnings_quality SourcedValue dict."""
    if extracted.financials is None or extracted.financials.earnings_quality is None:
        return None
    val = extracted.financials.earnings_quality.value.get(key)
    return float(val) if val is not None else None


def _bs(extracted: ExtractedData, label: str, period: int = 0) -> float | None:
    """Balance sheet line item shortcut."""
    return _get_line_item_value(extracted, "balance_sheet", label, period)


def _inc(extracted: ExtractedData, label: str, period: int = 0) -> float | None:
    """Income statement line item shortcut."""
    return _get_line_item_value(extracted, "income_statement", label, period)


def _cf(extracted: ExtractedData, label: str, period: int = 0) -> float | None:
    """Cash flow line item shortcut."""
    return _get_line_item_value(extracted, "cash_flow", label, period)


def compute_dechow_f_score(extracted: ExtractedData) -> tuple[float, str]:
    """Simplified Dechow F-Score for misstatement detection.

    Score > 1.85 = high risk, > 1.40 = elevated. Returns 0.0 if insufficient data.
    """
    ta_curr = _bs(extracted, "total assets", 0)
    ta_prior = _bs(extracted, "total assets", 1)
    recv_curr = _bs(extracted, "receivable", 0)
    recv_prior = _bs(extracted, "receivable", 1)
    inv_curr = _bs(extracted, "inventor", 0)
    inv_prior = _bs(extracted, "inventor", 1)
    ca_curr = _bs(extracted, "current assets", 0)
    ppe_curr = _bs(extracted, "property", 0)
    cash_curr = _bs(extracted, "cash", 0)
    rev_curr = _inc(extracted, "revenue", 0)
    rev_prior = _inc(extracted, "revenue", 1)
    ni_curr = _inc(extracted, "net income", 0)
    ni_prior = _inc(extracted, "net income", 1)

    if ta_curr is None or ta_curr == 0.0:
        return (0.0, "Insufficient data for Dechow F-Score")

    parts: list[str] = []
    raw = 0.0
    n = 0

    if recv_curr is not None and recv_prior is not None:
        v = (recv_curr - recv_prior) / ta_curr
        raw += 0.35 * v
        n += 1
        parts.append(f"d_recv/TA={v:.4f}")

    if inv_curr is not None and inv_prior is not None:
        v = (inv_curr - inv_prior) / ta_curr
        raw += 0.30 * v
        n += 1
        parts.append(f"d_inv/TA={v:.4f}")

    if ca_curr is not None and ppe_curr is not None and cash_curr is not None:
        v = (ta_curr - cash_curr - ppe_curr) / ta_curr
        raw += 0.25 * v
        n += 1
        parts.append(f"soft/TA={v:.4f}")

    if rev_curr is not None and rev_prior is not None:
        cs_c = rev_curr - (recv_curr or 0.0)
        cs_p = rev_prior - (recv_prior or 0.0)
        v = (cs_c - cs_p) / abs(cs_p) if cs_p != 0.0 else 0.0
        raw += 0.05 * v
        n += 1
        parts.append(f"cash_sales={v:.4f}")

    if (
        ni_curr is not None and ni_prior is not None
        and ta_prior is not None and ta_prior != 0.0
    ):
        v = (ni_curr / ta_curr) - (ni_prior / ta_prior)
        raw += 0.05 * v
        n += 1
        parts.append(f"earn_chg={v:.4f}")

    if n < 2:
        return (0.0, "Insufficient data for Dechow F-Score")

    f_score = round(1.0 + raw * 10.0, 4)
    evidence = (
        f"Dechow F-Score: {f_score:.2f} ({n}/5 components). "
        f"{', '.join(parts)}. >1.85 high risk, >1.40 elevated."
    )
    return (f_score, evidence)


def compute_montier_c_score(extracted: ExtractedData) -> tuple[float, str]:
    """Montier C-Score: 6 binary indicators (0-6). >=4 = high risk."""
    ni_c = _inc(extracted, "net income", 0)
    ni_p = _inc(extracted, "net income", 1)
    cfo_c = _cf(extracted, "operating", 0)
    cfo_p = _cf(extracted, "operating", 1)
    rev_c = _inc(extracted, "revenue", 0)
    rev_p = _inc(extracted, "revenue", 1)
    recv_c = _bs(extracted, "receivable", 0)
    recv_p = _bs(extracted, "receivable", 1)
    inv_c = _bs(extracted, "inventor", 0)
    inv_p = _bs(extracted, "inventor", 1)
    ca_c = _bs(extracted, "current assets", 0)
    ca_p = _bs(extracted, "current assets", 1)
    dep_c = _cf(extracted, "depreci", 0)
    dep_p = _cf(extracted, "depreci", 1)
    ppe_c = _bs(extracted, "property", 0)
    ppe_p = _bs(extracted, "property", 1)
    ta_c = _bs(extracted, "total assets", 0)
    ta_p = _bs(extracted, "total assets", 1)

    flags: list[str] = []
    score = 0
    evald = 0

    # 1. Increasing NI-CFO divergence
    if all(v is not None for v in (ni_c, cfo_c, ni_p, cfo_p)):
        f = (ni_c - cfo_c) > (ni_p - cfo_p)  # type: ignore[operator]
        score += int(f)
        evald += 1
        flags.append(f"NI-CFO:{'FLAG' if f else 'OK'}")

    # 2. Increasing DSO
    if (
        all(v is not None for v in (recv_c, rev_c, recv_p, rev_p))
        and rev_c != 0.0 and rev_p != 0.0  # type: ignore[operator]
    ):
        f = (recv_c / rev_c) > (recv_p / rev_p)  # type: ignore[operator]
        score += int(f)
        evald += 1
        flags.append(f"DSO:{'FLAG' if f else 'OK'}")

    # 3. Increasing DSI
    if (
        all(v is not None for v in (inv_c, rev_c, inv_p, rev_p))
        and rev_c != 0.0 and rev_p != 0.0  # type: ignore[operator]
    ):
        f = (inv_c / rev_c) > (inv_p / rev_p)  # type: ignore[operator]
        score += int(f)
        evald += 1
        flags.append(f"DSI:{'FLAG' if f else 'OK'}")

    # 4. Other current assets vs revenue
    if (
        all(v is not None for v in (ca_c, recv_c, inv_c, ca_p, recv_p, inv_p, rev_c, rev_p))
        and rev_c != 0.0 and rev_p != 0.0  # type: ignore[operator]
    ):
        oca_c = (ca_c - recv_c - inv_c) / rev_c  # type: ignore[operator]
        oca_p = (ca_p - recv_p - inv_p) / rev_p  # type: ignore[operator]
        f = oca_c > oca_p
        score += int(f)
        evald += 1
        flags.append(f"OCA:{'FLAG' if f else 'OK'}")

    # 5. Declining depreciation/PPE
    if (
        all(v is not None for v in (dep_c, ppe_c, dep_p, ppe_p))
        and ppe_c != 0.0 and ppe_p != 0.0  # type: ignore[operator]
    ):
        f = (abs(dep_c) / ppe_c) < (abs(dep_p) / ppe_p)  # type: ignore[operator]
        score += int(f)
        evald += 1
        flags.append(f"Dep:{'FLAG' if f else 'OK'}")

    # 6. High total asset growth (>10%)
    if ta_c is not None and ta_p is not None and ta_p != 0.0:
        growth = (ta_c - ta_p) / abs(ta_p)
        f = growth > 0.10
        score += int(f)
        evald += 1
        flags.append(f"TA_growth:{'FLAG' if f else 'OK'}")

    if evald == 0:
        return (0.0, "Insufficient data for Montier C-Score")

    evidence = (
        f"Montier C-Score: {score}/{evald} flagged (max 6). "
        f">=4 high risk. {'; '.join(flags)}"
    )
    return (float(score), evidence)


def compute_enhanced_sloan_ratio(extracted: ExtractedData) -> tuple[float, str]:
    """Enhanced Sloan Ratio = (NI - CFO) / |TA|. >0.10 = high risk."""
    ni = _inc(extracted, "net income", 0)
    cfo = _cf(extracted, "operating", 0)
    ta = _bs(extracted, "total assets", 0)

    if ni is None or cfo is None or ta is None or ta == 0.0:
        missing = []
        if ni is None:
            missing.append("NI")
        if cfo is None:
            missing.append("CFO")
        if ta is None or ta == 0.0:
            missing.append("TA")
        return (0.0, f"Insufficient data for Sloan Ratio: {', '.join(missing)}")

    ratio = round((ni - cfo) / abs(ta), 4)
    if ratio > 0.10:
        level = "HIGH accruals"
    elif ratio > 0.05:
        level = "MODERATE"
    elif ratio > -0.05:
        level = "NORMAL"
    else:
        level = "HEALTHY"

    return (
        ratio,
        f"Sloan Ratio: {ratio:.4f} (NI={ni:,.0f}, CFO={cfo:,.0f}, "
        f"TA={ta:,.0f}). {level}. >0.10 high, >0.05 elevated.",
    )


def compute_accrual_intensity(extracted: ExtractedData) -> tuple[float, str]:
    """|WC Accruals| / |CFO|. >0.50 = high accrual reliance."""
    cfo = _cf(extracted, "operating", 0)
    if cfo is None or cfo == 0.0:
        return (0.0, "Insufficient data for Accrual Intensity")

    # Try working capital accruals
    ca_c = _bs(extracted, "current assets", 0)
    ca_p = _bs(extracted, "current assets", 1)
    cash_c = _bs(extracted, "cash", 0)
    cash_p = _bs(extracted, "cash", 1)
    cl_c = _bs(extracted, "current liab", 0)
    cl_p = _bs(extracted, "current liab", 1)

    wc_acc: float | None = None
    method = "NI-CFO"
    if all(v is not None for v in (ca_c, ca_p, cash_c, cash_p, cl_c, cl_p)):
        wc_acc = (ca_c - cash_c) - (ca_p - cash_p) - (cl_c - cl_p)  # type: ignore[operator]
        method = "WC"

    if wc_acc is None:
        ni = _inc(extracted, "net income", 0)
        if ni is None:
            return (0.0, "Insufficient data for Accrual Intensity")
        wc_acc = ni - cfo

    ratio = round(abs(wc_acc) / abs(cfo), 4)
    if ratio > 0.50:
        level = "HIGH"
    elif ratio > 0.25:
        level = "MODERATE"
    else:
        level = "LOW"

    return (
        ratio,
        f"Accrual Intensity: {ratio:.4f} ({method}, "
        f"acc={wc_acc:,.0f}, CFO={cfo:,.0f}). {level}.",
    )


__all__ = [
    "compute_accrual_intensity",
    "compute_dechow_f_score",
    "compute_enhanced_sloan_ratio",
    "compute_montier_c_score",
]
