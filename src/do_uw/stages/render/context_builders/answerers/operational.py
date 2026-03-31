"""Answerers for Domain 6: Operational & Emerging Risk (OPS-01 through OPS-07)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    no_data,
    partial_answer,
    sv,
    triggered_signals,
    yf_info,
)


@register("OPS-01")
def _answer_ops_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Cybersecurity and data privacy exposure."""
    evidence = []

    cyber_signals = triggered_signals(ctx, prefix="cyber")
    for s in cyber_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # LLM extraction fallback (D-02): check risk factors for cyber terms
    if state.extracted:
        rf = getattr(state.extracted, "risk_factors", None)
        if isinstance(rf, list):
            cyber_rf = [
                r for r in rf
                if isinstance(r, dict)
                and any(
                    k in str(r.get("title", "") + str(r.get("category", ""))).lower()
                    for k in ("cyber", "data breach", "privacy", "security")
                )
            ]
            for r in cyber_rf[:2]:
                evidence.append(f"Risk factor: {str(r.get('title', r.get('category', '')))[:100]}")

    if not evidence:
        return {
            **partial_answer(
                "No cybersecurity signals triggered in pipeline analysis",
                "cyber risk details from 10-K Item 1/1A not auto-extracted",
                "10-K Item 1A/1C for cybersecurity disclosure",
            ),
            "evidence": ["No cyber signals triggered"],
        }

    if cyber_signals:
        verdict = "DOWNGRADE"
        answer = f"Cybersecurity risk signals triggered ({len(cyber_signals)} signal(s))."
    else:
        verdict = "NEUTRAL"
        answer = "Cybersecurity mentioned in risk factors -- review 10-K Item 1C disclosure."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("OPS-02")
def _answer_ops_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Regulatory change exposure."""
    evidence = []

    reg_signals = triggered_signals(ctx, prefix="regulatory")
    for s in reg_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check risk factors for regulatory mentions
    if state.extracted:
        rf = getattr(state.extracted, "risk_factors", None)
        if isinstance(rf, list):
            reg_rf = [
                r for r in rf
                if isinstance(r, dict)
                and any(
                    k in str(r.get("title", "") + str(r.get("category", ""))).lower()
                    for k in ("regulat", "fda", "epa", "ftc", "compliance")
                )
            ]
            for r in reg_rf[:2]:
                evidence.append(f"Risk factor: {str(r.get('title', r.get('category', '')))[:100]}")

    if not evidence:
        return {
            **partial_answer(
                "No regulatory change signals triggered",
                "regulatory exposure from 10-K not auto-extracted",
                "10-K Item 1/1A for regulatory environment",
            ),
            "evidence": ["No regulatory signals triggered"],
        }

    if reg_signals:
        verdict = "DOWNGRADE"
        answer = f"Regulatory risk signals triggered ({len(reg_signals)} signal(s))."
    else:
        verdict = "NEUTRAL"
        answer = "Regulatory risks mentioned in 10-K risk factors."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("OPS-03")
def _answer_ops_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """ESG or climate-related disclosure risks."""
    evidence = []

    esg_signals = triggered_signals(ctx, prefix="esg")
    for s in esg_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check alt_data for ESG context
    if hasattr(state, "alt_data") and state.alt_data:
        alt = state.alt_data
        if isinstance(alt, dict):
            esg = alt.get("esg_risk") or alt.get("esg")
            if esg:
                evidence.append(f"ESG data: {str(esg)[:120]}")

    if not evidence:
        return {
            "answer": "No ESG or climate-related disclosure risks flagged in pipeline data.",
            "evidence": ["No esg signals triggered"],
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }

    verdict = "DOWNGRADE" if esg_signals else "NEUTRAL"
    answer = f"ESG risk signals: {len(esg_signals)} triggered."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("OPS-04")
def _answer_ops_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Customer, supplier, or personnel concentration."""
    evidence = []

    conc_signals = [
        s for s in triggered_signals(ctx)
        if "concentration" in str(s.get("signal_id", "")).lower()
        or "key_person" in str(s.get("signal_id", "")).lower()
    ]
    for s in conc_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check extracted segments for customer concentration
    if state.extracted and state.extracted.financials:
        stmts = getattr(state.extracted.financials, "statements", None)
        if isinstance(stmts, dict):
            seg = stmts.get("segments") or stmts.get("segment_data")
            if isinstance(seg, (list, dict)) and seg:
                evidence.append(f"Segment data available: {len(seg) if isinstance(seg, list) else 'yes'}")

    if not evidence:
        return {
            **partial_answer(
                "No concentration signals triggered in pipeline analysis",
                "customer/supplier concentration from 10-K Item 1/7 not auto-extracted",
                "10-K Item 1/7 for major customer disclosure",
            ),
            "evidence": ["No concentration signals triggered"],
        }

    if conc_signals:
        verdict = "DOWNGRADE"
        answer = f"Concentration risk signals triggered ({len(conc_signals)} signal(s))."
    else:
        verdict = "NEUTRAL"
        answer = "Segment data available but customer concentration not specifically extracted."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }


@register("OPS-05")
def _answer_ops_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Tariff, trade, or geopolitical risks."""
    evidence = []

    tariff_signals = triggered_signals(ctx, prefix="tariff")
    for s in tariff_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check alt_data for tariff/geopolitical
    if hasattr(state, "alt_data") and state.alt_data:
        alt = state.alt_data
        if isinstance(alt, dict):
            tariff = alt.get("tariff_exposure") or alt.get("geopolitical")
            if tariff:
                evidence.append(f"Tariff/geo data: {str(tariff)[:120]}")

    if not evidence:
        return {
            "answer": "No tariff, trade, or geopolitical risk signals detected.",
            "evidence": ["No tariff signals triggered"],
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }

    verdict = "DOWNGRADE" if tariff_signals else "NEUTRAL"
    answer = f"Tariff/geopolitical signals: {len(tariff_signals)} triggered."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("OPS-06")
def _answer_ops_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Is the company in a high-frequency D&O claim sector?"""
    yfi = yf_info(ctx)
    sector = yfi.get("sector", "")
    industry = yfi.get("industry", "")

    sic = ""
    if state.company and state.company.identity.sic_code:
        sic = sv(state.company.identity.sic_code) or ""

    evidence = []
    if sector:
        evidence.append(f"Sector: {sector}")
    if industry:
        evidence.append(f"Industry: {industry}")
    if sic:
        evidence.append(f"SIC: {sic}")

    if not evidence:
        return no_data()

    # High-frequency D&O sectors
    high_freq = {
        "biotechnology", "pharmaceutical", "cannabis", "fintech", "cryptocurrency",
        "blank check", "spac", "electric vehicle",
    }
    is_high = any(hf in industry.lower() for hf in high_freq) if industry else False

    # Risk card scenario benchmarks if available
    lit = ctx.get("lit_detail", {})
    scenario = lit.get("scenario_benchmarks", {})
    if isinstance(scenario, dict):
        filing_rate = scenario.get("sector_filing_rate") or scenario.get("annual_filing_rate")
        if filing_rate:
            evidence.append(f"Sector SCA filing rate: {filing_rate}%")

    if is_high:
        verdict = "DOWNGRADE"
        answer = f"High-frequency D&O claim sector: {industry}."
    elif sector:
        verdict = "NEUTRAL"
        answer = f"Sector: {sector} ({industry or 'N/A'})."
    else:
        verdict = "NEUTRAL"
        answer = "Sector classification available."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("OPS-07")
def _answer_ops_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Forward-looking events that could trigger claims in next 12 months."""
    evidence = []

    # Check forward-looking analysis
    if state.analysis:
        fwd = getattr(state.analysis, "forward_indicators", None)
        if isinstance(fwd, (list, dict)):
            if isinstance(fwd, list):
                for f in fwd[:3]:
                    evidence.append(f"Forward indicator: {str(f)[:100]}")
            elif isinstance(fwd, dict):
                for key, val in list(fwd.items())[:3]:
                    evidence.append(f"Forward: {key} = {str(val)[:80]}")

    # Temporal signals
    temporal = ctx.get("temporal", {})
    if isinstance(temporal, dict):
        upcoming = temporal.get("upcoming_events") or temporal.get("catalysts")
        if isinstance(upcoming, list):
            for e in upcoming[:3]:
                evidence.append(f"Upcoming: {str(e)[:100]}")

    if not evidence:
        return {
            "answer": "No specific forward-looking trigger events identified in pipeline data.",
            "evidence": ["No forward indicators available"],
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }

    verdict = "DOWNGRADE" if len(evidence) >= 2 else "NEUTRAL"
    answer = f"{len(evidence)} forward-looking event(s) identified for monitoring."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
