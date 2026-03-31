"""Answerers for Domain 2: Financial Health & Accounting (FIN-01 through FIN-08)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    fmt_currency,
    fmt_pct,
    no_data,
    partial_answer,
    safe_float_extract,
    triggered_signals,
    yf_info,
)


@register("FIN-01")
def _answer_fin_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Is the company profitable and what's the trend?"""
    fin = ctx.get("fin", {})
    es = ctx.get("exec_summary", {})
    yfi = yf_info(ctx)

    evidence = []
    rev = es.get("revenue", fin.get("revenue", ""))
    ni = fin.get("net_income", "")
    rev_growth = yfi.get("revenueGrowth")
    ebitda_margin = yfi.get("ebitdaMargins")

    if rev:
        evidence.append(f"Revenue: {rev}")
    if ni:
        evidence.append(f"Net income: {ni}")
    if rev_growth is not None:
        evidence.append(f"Revenue growth: {rev_growth * 100:.1f}%")
    if ebitda_margin is not None:
        evidence.append(f"EBITDA margin: {ebitda_margin * 100:.1f}%")

    if not evidence:
        return no_data()

    is_profitable = ni and not str(ni).startswith("-") and not str(ni).startswith("(")
    growing = rev_growth is not None and rev_growth > 0

    if is_profitable and growing:
        verdict = "UPGRADE"
        answer = f"Profitable with {rev_growth * 100:.1f}% revenue growth." if rev_growth else "Profitable."
    elif not is_profitable:
        verdict = "DOWNGRADE"
        answer = f"Net loss of {ni}."
    else:
        verdict = "NEUTRAL"
        answer = f"Revenue: {rev}. Net income: {ni}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("FIN-02")
def _answer_fin_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Balance sheet strength -- cash, debt, and liquidity."""
    fin = ctx.get("fin", {})
    yfi = yf_info(ctx)

    evidence = []
    cash = fin.get("cash", "")
    debt = fin.get("debt", fin.get("total_debt", ""))
    cr = fin.get("current_ratio", "")
    dte = safe_float_extract(yfi.get("debtToEquity"))

    if cash:
        evidence.append(f"Cash: {cash}")
    if debt:
        evidence.append(f"Debt: {debt}")
    if cr:
        evidence.append(f"Current ratio: {cr}")
    if dte is not None:
        evidence.append(f"Debt/equity: {dte:.1f}")

    if not evidence:
        return no_data()

    cr_val = safe_float_extract(str(cr).replace("x", "").strip()) if cr else None

    if cr_val and cr_val > 2.0 and (dte is None or dte < 100):
        verdict = "UPGRADE"
        answer = f"Strong liquidity (CR {cr}) with manageable leverage."
    elif cr_val and cr_val < 1.0:
        verdict = "DOWNGRADE"
        answer = f"Current ratio below 1.0 ({cr}) -- potential liquidity concern."
    elif dte and dte > 300:
        verdict = "DOWNGRADE"
        answer = f"High leverage -- D/E ratio of {dte:.0f}%."
    else:
        verdict = "NEUTRAL"
        parts = []
        if cash:
            parts.append(f"Cash: {cash}")
        if debt:
            parts.append(f"Debt: {debt}")
        if cr:
            parts.append(f"CR: {cr}")
        answer = ". ".join(parts) + "."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("FIN-03")
def _answer_fin_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Earnings quality red flags -- Beneish, Altman, forensics."""
    fin = ctx.get("fin", {})
    forensics = ctx.get("forensic_composites", {})

    evidence = []
    beneish = fin.get("beneish_score")
    beneish_level = fin.get("beneish_level", "")
    altman = fin.get("altman_z_score")
    altman_zone = fin.get("altman_zone", "")

    if beneish is not None:
        evidence.append(f"Beneish M-Score: {beneish} ({beneish_level})")
    if altman is not None:
        evidence.append(f"Altman Z-Score: {altman} ({altman_zone})")
    if isinstance(forensics, dict) and forensics:
        n_flags = len([v for v in forensics.values() if isinstance(v, dict) and v.get("flagged")])
        evidence.append(f"Forensic flags: {n_flags}")

    if not evidence:
        return no_data()

    # Determine verdict
    is_manipulator = beneish_level and "manipulator" in str(beneish_level).lower()
    is_distress = altman_zone and "distress" in str(altman_zone).lower()

    if is_manipulator or is_distress:
        verdict = "DOWNGRADE"
        parts = []
        if is_manipulator:
            parts.append(f"Beneish M-Score {beneish} suggests possible manipulation")
        if is_distress:
            parts.append(f"Altman Z-Score {altman} in distress zone")
        answer = ". ".join(parts) + "."
    elif beneish_level and "safe" in str(beneish_level).lower():
        verdict = "UPGRADE"
        answer = f"Beneish M-Score: {beneish} (safe zone, threshold: -1.78). Altman Z: {altman or 'N/A'} ({altman_zone or 'N/A'})."
    else:
        verdict = "NEUTRAL"
        answer = f"Beneish: {beneish or 'N/A'} ({beneish_level or 'N/A'}). Altman: {altman or 'N/A'} ({altman_zone or 'N/A'})."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("FIN-04")
def _answer_fin_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Has the company restated financials or changed accounting policies?"""
    evidence = []

    # Check restatement signals
    restatement_sigs = triggered_signals(ctx, prefix="disc.ctrl")
    restatement_sigs += [
        s for s in triggered_signals(ctx)
        if "restatement" in str(s.get("signal_id", "")).lower()
    ]
    for s in restatement_sigs[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check extracted audit data
    if state.extracted and state.extracted.financials:
        audit = getattr(state.extracted.financials, "audit", None)
        if isinstance(audit, dict):
            restatement = audit.get("restatement")
            if restatement:
                evidence.append(f"Restatement: {str(restatement)[:100]}")

    if not evidence:
        # No restatement data either way — treat as clean if we have financials
        fin = ctx.get("fin", {})
        if fin:
            return {
                "answer": "No restatement or accounting policy changes detected in pipeline analysis.",
                "evidence": ["No restatement signals triggered"],
                "verdict": "UPGRADE",
                "confidence": "MEDIUM",
                "data_found": True,
            }
        return no_data()

    verdict = "DOWNGRADE"
    answer = f"{len(restatement_sigs)} restatement/disclosure control signal(s) triggered."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("FIN-05")
def _answer_fin_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Who audits them and are there any material weaknesses?"""
    fin = ctx.get("fin", {})

    auditor = fin.get("auditor_name", "")
    audit_alerts = fin.get("audit_alerts") or fin.get("audit_disclosure_alerts") or []
    mw_context = fin.get("audit_mw_do_context", "")

    big4 = {"Deloitte", "Ernst & Young", "EY", "KPMG", "PricewaterhouseCoopers", "PwC"}

    evidence = []
    is_big4 = False
    if auditor:
        is_big4 = any(b.lower() in str(auditor).lower() for b in big4)
        evidence.append(f"Auditor: {auditor} ({'Big 4' if is_big4 else 'non-Big 4'})")

    mw_signals = triggered_signals(ctx, prefix="material_weakness")
    has_mw = bool(mw_signals) or any("material weakness" in str(a).lower() for a in audit_alerts)

    if has_mw:
        evidence.append("Material weakness identified")
    if mw_context:
        evidence.append(f"MW context: {mw_context[:150]}")
    for a in audit_alerts[:2]:
        evidence.append(f"Alert: {str(a)[:120]}")

    if not evidence:
        return no_data()

    if has_mw:
        verdict = "DOWNGRADE"
        answer = f"Material weakness or significant deficiency identified. Auditor: {auditor or 'unknown'}."
    elif not is_big4 and auditor:
        verdict = "DOWNGRADE"
        answer = f"Non-Big 4 auditor ({auditor}). No material weakness disclosed."
    elif is_big4:
        verdict = "UPGRADE"
        answer = f"Big 4 auditor ({auditor}). Clean audit opinion, no material weakness."
    else:
        verdict = "NEUTRAL"
        answer = f"Auditor: {auditor or 'unknown'}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("FIN-06")
def _answer_fin_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Cash flow situation -- operating vs. financing."""
    yfi = yf_info(ctx)
    fin = ctx.get("fin", {})

    ocf = safe_float_extract(yfi.get("operatingCashflow"))
    fcf = safe_float_extract(yfi.get("freeCashflow"))

    # Fallback to extracted data
    if ocf is None and state.extracted and state.extracted.financials:
        stmts = getattr(state.extracted.financials, "statements", None)
        if isinstance(stmts, dict):
            ocf = safe_float_extract(stmts.get("operating_cash_flow"))
            fcf = safe_float_extract(stmts.get("free_cash_flow"))

    evidence = []
    if ocf is not None:
        evidence.append(f"Operating cash flow: {fmt_currency(ocf)}")
    if fcf is not None:
        evidence.append(f"Free cash flow: {fmt_currency(fcf)}")

    if not evidence:
        return no_data()

    if ocf is not None and ocf < 0:
        verdict = "DOWNGRADE"
        answer = f"Negative operating cash flow ({fmt_currency(ocf)}) -- company burning cash."
    elif fcf is not None and fcf < 0 and ocf is not None and ocf > 0:
        verdict = "NEUTRAL"
        answer = f"OCF positive ({fmt_currency(ocf)}) but FCF negative ({fmt_currency(fcf)}) -- heavy CapEx."
    elif ocf is not None and ocf > 0:
        verdict = "UPGRADE"
        answer = f"Positive cash flow: OCF {fmt_currency(ocf)}, FCF {fmt_currency(fcf) if fcf else 'N/A'}."
    else:
        verdict = "NEUTRAL"
        answer = f"Cash flow data: OCF {fmt_currency(ocf)}, FCF {fmt_currency(fcf)}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("FIN-07")
def _answer_fin_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Revenue recognition complexity."""
    yfi = yf_info(ctx)
    industry = yfi.get("industry", "")
    sector = yfi.get("sector", "")

    complex_industries = {
        "software", "saas", "cloud", "construction", "defense", "aerospace",
        "consulting", "services", "telecom", "real estate",
    }
    is_complex = any(ci in industry.lower() for ci in complex_industries) if industry else False

    rev_signals = [
        s for s in triggered_signals(ctx)
        if any(k in str(s.get("signal_id", "")).lower() for k in ("rev_rec", "revenue_recognition", "asc_606"))
    ]

    evidence = []
    if industry:
        evidence.append(f"Industry: {industry}")
    for s in rev_signals[:2]:
        evidence.append(f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:80]}")

    if not evidence:
        return no_data()

    if rev_signals:
        verdict = "DOWNGRADE"
        answer = f"Revenue recognition complexity flags triggered ({len(rev_signals)} signal(s))."
    elif is_complex:
        verdict = "NEUTRAL"
        answer = f"Industry ({industry}) typically involves complex revenue recognition -- verify ASC 606 disclosures."
    else:
        verdict = "UPGRADE"
        answer = f"Industry ({industry or sector}) generally has straightforward revenue recognition."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("FIN-08")
def _answer_fin_08(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """GAAP vs non-GAAP delta on key metrics."""
    fin = ctx.get("fin", {})

    beneish = fin.get("beneish_score")
    beneish_level = fin.get("beneish_level", "")

    eq_signals = [
        s for s in triggered_signals(ctx)
        if any(
            k in str(s.get("signal_id", "")).lower()
            for k in ("gaap", "non_gaap", "earnings_quality", "earnings_manipulation")
        )
    ]

    evidence = []
    if beneish is not None:
        evidence.append(f"Beneish M-Score: {beneish} ({beneish_level})")
    for s in eq_signals[:2]:
        evidence.append(f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:80]}")

    if not evidence:
        return no_data()

    if eq_signals or (beneish_level and "manipulator" in str(beneish_level).lower()):
        verdict = "DOWNGRADE"
        answer = "Earnings quality concerns -- potential GAAP/non-GAAP divergence risk."
        if beneish is not None:
            answer = f"Beneish M-Score: {beneish} ({beneish_level}). Earnings quality concerns flagged."
    elif beneish_level and "safe" in str(beneish_level).lower():
        verdict = "UPGRADE"
        answer = f"Beneish M-Score {beneish} ({beneish_level}) -- low manipulation risk."
    else:
        verdict = "NEUTRAL"
        answer = f"Earnings quality data available. Beneish: {beneish or 'N/A'} ({beneish_level or 'N/A'})."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
