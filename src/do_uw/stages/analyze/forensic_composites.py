"""Composite forensic scores: FIS (5 sub-dimensions), RQS, CFQS.

Config-driven weights from forensic_models.json. Missing data handled
via reweighting. Zones: HIGH_INTEGRITY through CRITICAL (0-100 scale).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from do_uw.models.forensic import (
    CashFlowQualityScore,
    FinancialIntegrityScore,
    ForensicZone,
    RevenueQualityScore,
    SubScore,
)
from do_uw.stages.analyze.forensic_models import (
    _bs,
    _cf,
    _get_distress_score,
    _get_earnings_quality_field,
    _inc,
    compute_accrual_intensity,
    compute_dechow_f_score,
    compute_enhanced_sloan_ratio,
    compute_montier_c_score,
)

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData

from do_uw.brain.brain_unified_loader import load_config

logger = logging.getLogger(__name__)


def _load_forensic_config() -> dict:
    """Load forensic_models.json configuration."""
    return load_config("forensic_models")


def _normalize_to_score(raw: float, good: float, bad: float) -> float:
    """Map raw value to 0-100. good=100, bad=0. Clamped."""
    if good == bad:
        return 50.0
    if good < bad:  # Higher raw = worse
        if raw <= good:
            return 100.0
        if raw >= bad:
            return 0.0
        s = 100.0 * (bad - raw) / (bad - good)
    else:  # Higher raw = better
        if raw >= good:
            return 100.0
        if raw <= bad:
            return 0.0
        s = 100.0 * (raw - bad) / (good - bad)
    return max(0.0, min(100.0, round(s, 1)))


def _weighted_composite(
    scores: dict[str, float | None], weights: dict[str, float],
) -> float:
    """Weighted average skipping None. Reweights proportionally."""
    total_w = 0.0
    total_s = 0.0
    for k, w in weights.items():
        s = scores.get(k)
        if s is not None:
            total_s += s * w
            total_w += w
    return round(total_s / total_w, 1) if total_w > 0 else 50.0


def _classify_zone(
    score: float, zones: dict | None = None,
) -> ForensicZone:
    """Map 0-100 score to ForensicZone."""
    z = zones or {}
    if score >= z.get("HIGH_INTEGRITY", [80, 100])[0]:
        return ForensicZone.HIGH_INTEGRITY
    if score >= z.get("ADEQUATE", [60, 80])[0]:
        return ForensicZone.ADEQUATE
    if score >= z.get("CONCERNING", [40, 60])[0]:
        return ForensicZone.CONCERNING
    if score >= z.get("WEAK", [20, 40])[0]:
        return ForensicZone.WEAK
    return ForensicZone.CRITICAL


def _compute_manipulation_detection(
    extracted: ExtractedData, model_config: dict,
) -> SubScore:
    """Manipulation sub-score: Beneish + Dechow + Montier normalized to 0-100."""
    comps: dict[str, float] = {}
    scores: dict[str, float | None] = {}
    models = model_config.get("manipulation_detection_models", {})

    beneish = _get_distress_score(extracted, "beneish_m_score")
    b_cfg = models.get("beneish_m_score", {})
    if beneish is not None:
        n = _normalize_to_score(beneish, b_cfg.get("yellow_threshold", -2.22),
                                b_cfg.get("red_threshold", -1.78))
        comps["beneish_raw"] = beneish
        comps["beneish_normalized"] = n
        scores["beneish"] = n

    d_score, _ = compute_dechow_f_score(extracted)
    d_cfg = models.get("dechow_f_score", {})
    if d_score > 0.0:
        n = _normalize_to_score(d_score, d_cfg.get("yellow_threshold", 1.40) * 0.5,
                                d_cfg.get("red_threshold", 1.85))
        comps["dechow_raw"] = d_score
        comps["dechow_normalized"] = n
        scores["dechow"] = n

    m_score, m_ev = compute_montier_c_score(extracted)
    m_cfg = models.get("montier_c_score", {})
    if m_score > 0.0 or "flagged" in m_ev:
        n = _normalize_to_score(m_score, 0.0, float(m_cfg.get("max_score", 6)))
        comps["montier_raw"] = m_score
        comps["montier_normalized"] = n
        scores["montier"] = n

    wts = {}
    if "beneish" in scores:
        wts["beneish"] = b_cfg.get("weight", 0.40)
    if "dechow" in scores:
        wts["dechow"] = d_cfg.get("weight", 0.35)
    if "montier" in scores:
        wts["montier"] = m_cfg.get("weight", 0.25)

    composite = _weighted_composite(scores, wts) if wts else 50.0
    parts = []
    if beneish is not None:
        parts.append(f"Beneish={beneish:.2f}")
    if d_score > 0:
        parts.append(f"Dechow={d_score:.2f}")
    if "montier" in scores:
        parts.append(f"Montier={m_score:.0f}/6")

    return SubScore(
        name="manipulation_detection", score=composite, components=comps,
        evidence=f"Manipulation: {composite:.0f}/100 ({len(scores)}/3). "
        + (", ".join(parts) or "No data"),
    )


def _compute_accrual_quality(extracted: ExtractedData) -> SubScore:
    """Accrual quality: Sloan ratio + accrual intensity."""
    comps: dict[str, float] = {}
    scores: dict[str, float | None] = {}

    sl, sl_ev = compute_enhanced_sloan_ratio(extracted)
    if sl != 0.0 or "Insufficient" not in sl_ev:
        n = _normalize_to_score(sl, 0.0, 0.15)
        comps.update(sloan_raw=sl, sloan_normalized=n)
        scores["sloan"] = n

    ai, ai_ev = compute_accrual_intensity(extracted)
    if ai != 0.0 or "Insufficient" not in ai_ev:
        n = _normalize_to_score(ai, 0.0, 0.60)
        comps.update(intensity_raw=ai, intensity_normalized=n)
        scores["intensity"] = n

    c = _weighted_composite(scores, {"sloan": 0.55, "intensity": 0.45})
    return SubScore(
        name="accrual_quality", score=c, components=comps,
        evidence=f"Accrual quality: {c:.0f}/100. Sloan={sl:.4f}, AI={ai:.4f}",
    )


def _compute_revenue_quality_sub(extracted: ExtractedData) -> SubScore:
    """Revenue quality: DSO trend, AR divergence, Q4, deferred revenue."""
    comps: dict[str, float] = {}
    scores: dict[str, float | None] = {}
    rev_c = _inc(extracted, "revenue", 0)
    rev_p = _inc(extracted, "revenue", 1)
    recv_c = _bs(extracted, "receivable", 0)
    recv_p = _bs(extracted, "receivable", 1)

    # DSO trend
    if (all(v is not None for v in (recv_c, rev_c, recv_p, rev_p))
            and rev_c != 0.0 and rev_p != 0.0):  # type: ignore[operator]
        dso_c = (recv_c / rev_c) * 365  # type: ignore[operator]
        dso_p = (recv_p / rev_p) * 365  # type: ignore[operator]
        chg = dso_c - dso_p
        n = _normalize_to_score(chg, -10.0, 30.0)
        comps.update(dso_curr=round(dso_c, 1), dso_prior=round(dso_p, 1),
                     dso_change=round(chg, 1), dso_normalized=n)
        scores["dso_trend"] = n

    # AR divergence
    if (all(v is not None for v in (recv_c, recv_p, rev_c, rev_p))
            and recv_p != 0.0 and rev_p != 0.0):  # type: ignore[operator]
        ar_g = (recv_c - recv_p) / abs(recv_p)  # type: ignore[operator]
        rv_g = (rev_c - rev_p) / abs(rev_p)  # type: ignore[operator]
        div = ar_g - rv_g
        n = _normalize_to_score(div, -0.10, 0.20)
        comps.update(ar_growth=round(ar_g, 4), rev_growth=round(rv_g, 4),
                     ar_divergence=round(div, 4), ar_divergence_normalized=n)
        scores["ar_divergence"] = n

    # Q4 / revenue quality proxy
    eq = _get_earnings_quality_field(extracted, "revenue_quality")
    if eq is not None:
        n = min(100.0, max(0.0, eq * 100.0))
        comps["eq_revenue_quality"] = eq
        scores["q4_concentration"] = n

    # Deferred revenue
    df_c = _bs(extracted, "deferred revenue", 0)
    df_p = _bs(extracted, "deferred revenue", 1)
    if df_c is not None and df_p is not None and df_p != 0.0:
        chg = (df_c - df_p) / abs(df_p)
        n = _normalize_to_score(chg, 0.10, -0.20)
        comps.update(deferred_change=round(chg, 4), deferred_normalized=n)
        scores["deferred_revenue"] = n

    wts = {"dso_trend": 0.30, "ar_divergence": 0.25,
           "q4_concentration": 0.25, "deferred_revenue": 0.20}
    c = _weighted_composite(scores, wts)
    return SubScore(
        name="revenue_quality", score=c, components=comps,
        evidence=f"Revenue quality: {c:.0f}/100 ({len(scores)}/4)",
    )


def _compute_cash_flow_quality_sub(extracted: ExtractedData) -> SubScore:
    """Cash flow quality: QoE, cash conversion, capex adequacy."""
    comps: dict[str, float] = {}
    scores: dict[str, float | None] = {}
    ni = _inc(extracted, "net income", 0)
    cfo = _cf(extracted, "operating", 0)
    rev = _inc(extracted, "revenue", 0)
    capex = _cf(extracted, "capital expenditure", 0)
    dep = _cf(extracted, "depreci", 0)

    if ni is not None and cfo is not None and ni != 0.0:
        qoe = cfo / ni
        n = _normalize_to_score(abs(qoe - 1.0), 0.0, 1.0)
        comps.update(qoe_ratio=round(qoe, 4), qoe_normalized=n)
        scores["quality_of_earnings"] = n

    if cfo is not None and rev is not None and rev != 0.0:
        cv = abs(capex) if capex is not None else 0.0
        cc = (cfo - cv) / rev
        n = _normalize_to_score(cc, 0.15, -0.10)
        comps.update(cash_conversion=round(cc, 4), cash_conversion_normalized=n)
        scores["cash_conversion"] = n

    if capex is not None and dep is not None and dep != 0.0:
        cr = abs(capex) / abs(dep)
        n = _normalize_to_score(cr, 1.5, 0.3)
        comps.update(capex_dep_ratio=round(cr, 4), capex_normalized=n)
        scores["capex_adequacy"] = n

    wts = {"quality_of_earnings": 0.40, "cash_conversion": 0.35, "capex_adequacy": 0.25}
    c = _weighted_composite(scores, wts)
    return SubScore(
        name="cash_flow_quality", score=c, components=comps,
        evidence=f"Cash flow quality: {c:.0f}/100 ({len(scores)}/3)",
    )


def _compute_audit_risk(extracted: ExtractedData) -> SubScore:
    """Audit risk: deduction-based (start 100, subtract for issues)."""
    if extracted.financials is None:
        return SubScore(name="audit_risk", score=50.0,
                        evidence="Audit risk: 50/100 (no data)")

    comps: dict[str, float] = {}
    s = 100.0
    parts: list[str] = []
    audit = extracted.financials.audit

    mw = len(audit.material_weaknesses)
    if mw > 0:
        d = min(40.0, mw * 20.0)
        s -= d
        comps["material_weaknesses"] = float(mw)
        parts.append(f"{mw} MW (-{d:.0f})")

    sd = len(audit.significant_deficiencies)
    if sd > 0:
        d = min(15.0, sd * 5.0)
        s -= d
        comps["significant_deficiencies"] = float(sd)
        parts.append(f"{sd} SD (-{d:.0f})")

    if audit.going_concern is not None and audit.going_concern.value is True:
        s -= 25.0
        comps["going_concern"] = 1.0
        parts.append("GC (-25)")

    rs = len(audit.restatements)
    if rs > 0:
        d = min(20.0, rs * 10.0)
        s -= d
        comps["restatements"] = float(rs)
        parts.append(f"{rs} restatement(s) (-{d:.0f})")

    if audit.is_big4 is not None and audit.is_big4.value is False:
        s -= 5.0
        comps["non_big4"] = 1.0
        parts.append("non-Big4 (-5)")

    s = max(0.0, min(100.0, s))
    comps["final_score"] = s
    return SubScore(
        name="audit_risk", score=s, components=comps,
        evidence=f"Audit: {s:.0f}/100. " + ("; ".join(parts) or "No issues"),
    )


def compute_financial_integrity_score(
    extracted: ExtractedData, config: dict | None = None,
) -> FinancialIntegrityScore:
    """FIS: 5 sub-dimensions -> weighted 0-100 score with zone."""
    if config is None:
        config = _load_forensic_config()
    fis = config.get("financial_integrity_score", {})
    wts = fis.get("weights", {"manipulation_detection": 0.30, "accrual_quality": 0.20,
                               "revenue_quality": 0.20, "cash_flow_quality": 0.15,
                               "audit_risk": 0.15})

    manip = _compute_manipulation_detection(extracted, fis)
    accr = _compute_accrual_quality(extracted)
    rev = _compute_revenue_quality_sub(extracted)
    cf = _compute_cash_flow_quality_sub(extracted)
    audit = _compute_audit_risk(extracted)

    sub_s: dict[str, float | None] = {
        "manipulation_detection": manip.score if manip.components else None,
        "accrual_quality": accr.score if accr.components else None,
        "revenue_quality": rev.score if rev.components else None,
        "cash_flow_quality": cf.score if cf.components else None,
        "audit_risk": audit.score,
    }
    overall = _weighted_composite(sub_s, wts)
    zone = _classify_zone(overall, fis.get("zones"))

    return FinancialIntegrityScore(
        overall_score=overall, zone=zone,
        manipulation_detection=manip, accrual_quality=accr,
        revenue_quality=rev, cash_flow_quality=cf, audit_risk=audit,
        sub_scores={n: sub.score for n, sub in [
            ("manipulation_detection", manip), ("accrual_quality", accr),
            ("revenue_quality", rev), ("cash_flow_quality", cf),
            ("audit_risk", audit)]},
    )


def compute_revenue_quality_score(
    extracted: ExtractedData, config: dict | None = None,
) -> RevenueQualityScore:
    """RQS standalone: DSO (30%), AR div (25%), Q4 (25%), deferred (20%)."""
    if config is None:
        config = _load_forensic_config()
    zones = config.get("revenue_quality_score", {}).get("zones")
    sub = _compute_revenue_quality_sub(extracted)
    c = sub.components

    dso_s = c.get("dso_normalized", 50.0)
    ar_s = c.get("ar_divergence_normalized", 50.0)
    q4_s = c.get("eq_revenue_quality", 50.0)
    if "eq_revenue_quality" in c:
        q4_s = min(100.0, max(0.0, c["eq_revenue_quality"] * 100.0))
    df_s = c.get("deferred_normalized", 50.0)

    def _sub(name: str, sc: float, filt: str) -> SubScore:
        return SubScore(name=name, score=sc,
                        components={k: v for k, v in c.items() if filt in k},
                        evidence=f"{name}: {sc:.0f}/100")

    return RevenueQualityScore(
        overall_score=sub.score, zone=_classify_zone(sub.score, zones),
        dso_trend=_sub("dso_trend", dso_s, "dso"),
        ar_divergence=SubScore(
            name="ar_divergence", score=ar_s,
            components={k: v for k, v in c.items() if "ar_" in k or "rev_growth" in k},
            evidence=f"ar_divergence: {ar_s:.0f}/100"),
        q4_concentration=_sub("q4_concentration", q4_s, "eq_"),
        deferred_revenue=_sub("deferred_revenue", df_s, "deferred"),
    )


def compute_cash_flow_quality_score(
    extracted: ExtractedData, config: dict | None = None,
) -> CashFlowQualityScore:
    """CFQS standalone: QoE (40%), cash conversion (35%), capex (25%)."""
    if config is None:
        config = _load_forensic_config()
    zones = config.get("cash_flow_quality_score", {}).get("zones")
    sub = _compute_cash_flow_quality_sub(extracted)
    c = sub.components

    def _sub(name: str, key: str) -> SubScore:
        sc = c.get(f"{key}_normalized", c.get(key, 50.0))
        return SubScore(name=name, score=sc,
                        components={k: v for k, v in c.items() if key in k},
                        evidence=f"{name}: {sc:.0f}/100")

    return CashFlowQualityScore(
        overall_score=sub.score, zone=_classify_zone(sub.score, zones),
        quality_of_earnings=_sub("quality_of_earnings", "qoe"),
        cash_conversion=_sub("cash_conversion", "cash_conversion"),
        capex_adequacy=_sub("capex_adequacy", "capex"),
    )


def detect_beneish_dechow_convergence(
    extracted: ExtractedData, config: dict | None = None,
) -> tuple[bool, str]:
    """Detect both Beneish AND Dechow flagging. Amplifier, not additive."""
    if config is None:
        config = _load_forensic_config()
    fis = config.get("financial_integrity_score", {})
    models = fis.get("manipulation_detection_models", {})

    ben = _get_distress_score(extracted, "beneish_m_score")
    ben_t = models.get("beneish_m_score", {}).get("red_threshold", -1.78)
    ben_f = ben is not None and ben > ben_t

    dec, _ = compute_dechow_f_score(extracted)
    dec_t = models.get("dechow_f_score", {}).get("red_threshold", 1.85)
    dec_f = dec > 0.0 and dec > dec_t

    conv = ben_f and dec_f
    parts = []
    if ben is not None:
        parts.append(f"Beneish={ben:.2f}({'F' if ben_f else 'OK'})")
    else:
        parts.append("Beneish=N/A")
    parts.append(f"Dechow={dec:.2f}({'F' if dec_f else 'OK'})")

    if conv:
        return (True, "CONVERGENCE: " + "; ".join(parts))
    return (False, "No convergence. " + "; ".join(parts))


__all__ = [
    "compute_cash_flow_quality_score",
    "compute_financial_integrity_score",
    "compute_revenue_quality_score",
    "detect_beneish_dechow_convergence",
]
