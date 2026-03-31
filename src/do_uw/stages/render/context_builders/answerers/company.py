"""Answerers for Domain 1: Company & Business Model (BIZ-01 through BIZ-06)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    fmt_currency,
    no_data,
    partial_answer,
    safe_float_extract,
    sv,
    triggered_signals,
    yf_info,
)


@register("BIZ-01")
def _answer_biz_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """What does this company do and what sector does it operate in?"""
    es = ctx.get("exec_summary", {})
    yfi = yf_info(ctx)

    company_name = es.get("company_name", state.ticker)
    sector = yfi.get("sector", es.get("sector", ""))
    industry = yfi.get("industry", "")
    sic = ""
    if state.company and state.company.identity.sic_code:
        sic = sv(state.company.identity.sic_code) or ""

    if not sector and not industry:
        return no_data()

    evidence = []
    if sector:
        evidence.append(f"Sector: {sector}")
    if industry:
        evidence.append(f"Industry: {industry}")
    if sic:
        evidence.append(f"SIC: {sic}")

    answer = f"{company_name} operates in the {industry or sector} industry"
    if sic:
        answer += f" (SIC {sic})"
    answer += "."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": "NEUTRAL",
        "confidence": "HIGH",
        "data_found": True,
    }


@register("BIZ-02")
def _answer_biz_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """How does the company generate revenue and how concentrated is it?"""
    fin = ctx.get("fin", {})
    es = ctx.get("exec_summary", {})
    yfi = yf_info(ctx)

    rev = es.get("revenue", fin.get("revenue", ""))
    rev_raw = safe_float_extract(yfi.get("totalRevenue"))
    rev_display = rev if rev else (fmt_currency(rev_raw) if rev_raw else "")

    evidence = []
    if rev_display:
        evidence.append(f"Revenue: {rev_display}")

    # Segment data from extracted financials
    segments_found = False
    if state.extracted and state.extracted.financials:
        stmts = getattr(state.extracted.financials, "statements", None)
        if isinstance(stmts, dict):
            seg_data = stmts.get("segments", stmts.get("segment_data"))
            if isinstance(seg_data, (list, dict)) and seg_data:
                segments_found = True
                if isinstance(seg_data, list):
                    evidence.append(f"Segments: {len(seg_data)} reported")
                elif isinstance(seg_data, dict):
                    evidence.append(f"Segments: {len(seg_data)} reported")

    growth = yfi.get("revenueGrowth")
    if growth is not None:
        evidence.append(f"Revenue growth: {growth * 100:.1f}% YoY")

    if not evidence:
        return no_data()

    answer_parts = []
    if rev_display:
        answer_parts.append(f"Revenue: {rev_display}")
    if growth is not None:
        answer_parts.append(f"Growth: {growth * 100:.1f}% YoY")

    answer = ". ".join(answer_parts) + "."

    if not segments_found:
        return {
            **partial_answer(
                answer,
                "segment breakdown not extracted",
                "10-K Item 1/7 for segment detail",
            ),
            "evidence": evidence,
        }

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": "NEUTRAL",
        "confidence": "MEDIUM" if segments_found else "LOW",
        "data_found": True,
    }


@register("BIZ-03")
def _answer_biz_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """How long has this company been public and what's its market cap?"""
    es = ctx.get("exec_summary", {})
    yfi = yf_info(ctx)

    mc_raw = safe_float_extract(yfi.get("marketCap"))
    mc_display = es.get("market_cap", "")

    evidence = []
    if mc_display and mc_display != "N/A":
        evidence.append(f"Market cap: {mc_display}")
    elif mc_raw:
        evidence.append(f"Market cap: {fmt_currency(mc_raw)}")

    if not evidence:
        return no_data()

    if mc_raw:
        if mc_raw >= 50e9:
            tier = "mega-cap"
        elif mc_raw >= 10e9:
            tier = "large-cap"
        elif mc_raw >= 2e9:
            tier = "mid-cap"
        elif mc_raw >= 500e6:
            tier = "small-cap"
        else:
            tier = "micro-cap"
        answer = f"Market cap {mc_display or fmt_currency(mc_raw)} ({tier})."
        verdict = "UPGRADE" if mc_raw < 2e9 else "NEUTRAL"
    else:
        answer = f"Market cap: {mc_display}."
        verdict = "NEUTRAL"

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("BIZ-04")
def _answer_biz_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """How many employees and where are key operations?"""
    yfi = yf_info(ctx)
    employees = yfi.get("fullTimeEmployees")
    hq = ""
    city = yfi.get("city", "")
    st = yfi.get("state", "")
    country = yfi.get("country", "")
    if city and st:
        hq = f"{city}, {st}"
    elif city and country:
        hq = f"{city}, {country}"
    elif city:
        hq = city

    evidence = []
    if employees:
        evidence.append(f"Employees: {employees:,}")
    if hq:
        evidence.append(f"HQ: {hq}")

    if not evidence:
        return no_data()

    parts = []
    if employees:
        parts.append(f"{employees:,} full-time employees")
    if hq:
        parts.append(f"Headquartered in {hq}")
    answer = ". ".join(parts) + "."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": "NEUTRAL",
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("BIZ-05")
def _answer_biz_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Are there any pending or recent M&A transactions?"""
    evidence = []

    # Check for M&A signals
    ma_signals = triggered_signals(ctx, prefix="ma")
    for s in ma_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check ctx for ma_profile
    ma_profile = ctx.get("ma_profile")
    if isinstance(ma_profile, dict) and ma_profile:
        status = ma_profile.get("status", "")
        if status:
            evidence.append(f"M&A status: {status}")

    # LLM extraction fallback path (D-02): check filing text for M&A indicators
    # This is the non-LLM fallback; actual LLM extraction would be added in a future plan
    if not evidence and state.extracted:
        # Check for 8-K Item 1.01 (material agreement / M&A)
        sec_filings = getattr(state.extracted, "sec_filings", None)
        if isinstance(sec_filings, (list, dict)):
            eight_k_count = 0
            if isinstance(sec_filings, list):
                eight_k_count = sum(
                    1 for f in sec_filings if isinstance(f, dict) and "8-K" in str(f.get("form_type", ""))
                )
            if eight_k_count > 0:
                evidence.append(f"8-K filings found: {eight_k_count} (may contain M&A disclosures)")

    if not evidence:
        return {
            **partial_answer(
                "No M&A activity detected in pipeline signals",
                "M&A details from 8-K/proxy not auto-extracted",
                "8-K Item 1.01 and proxy statement",
            ),
            "evidence": ["No M&A signals triggered"],
        }

    if ma_signals:
        verdict = "DOWNGRADE"
        answer = f"{len(ma_signals)} M&A-related signal(s) triggered."
    elif ma_profile:
        verdict = "DOWNGRADE"
        answer = f"M&A activity detected: {ma_profile.get('status', 'active')}."
    else:
        verdict = "NEUTRAL"
        answer = "8-K filings found that may contain M&A disclosures."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("BIZ-06")
def _answer_biz_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """What are the company's key risk factors from their own 10-K?"""
    evidence = []

    # Check extracted risk factors
    risk_factors: list[Any] = []
    if state.extracted:
        rf = getattr(state.extracted, "risk_factors", None)
        if isinstance(rf, list) and rf:
            risk_factors = rf

    if risk_factors:
        evidence.append(f"Risk factors disclosed: {len(risk_factors)}")
        for rf in risk_factors[:3]:
            if isinstance(rf, dict):
                title = rf.get("title", rf.get("category", ""))
                if title:
                    evidence.append(f"Risk: {str(title)[:100]}")
            elif hasattr(rf, "category"):
                evidence.append(f"Risk: {str(getattr(rf, 'category', ''))[:100]}")

    # Also check triggered signals for risk-factor related items
    rf_signals = triggered_signals(ctx, prefix="risk_factor")
    for s in rf_signals[:2]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:80]}"
        )

    if not evidence:
        # LLM extraction candidate (D-02) — non-LLM fallback
        return {
            **partial_answer(
                "Risk factor details not structurally extracted",
                "10-K Item 1A risk factor text not parsed",
                "10-K Item 1A Risk Factors",
            ),
            "evidence": ["Risk factor extraction pending"],
        }

    answer = f"{len(risk_factors)} risk factors disclosed in 10-K."
    if rf_signals:
        answer += f" {len(rf_signals)} risk-factor signal(s) triggered."

    # Downgrade if many risk factors or signals triggered
    verdict = "DOWNGRADE" if rf_signals or len(risk_factors) > 20 else "NEUTRAL"

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
