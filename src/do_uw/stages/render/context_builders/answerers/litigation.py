"""Answerers for Domain 5: Litigation & Claims History (LIT-01 through LIT-07)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    fmt_currency,
    no_data,
    partial_answer,
    safe_float_extract,
    triggered_signals,
)


def _get_supabase_cases(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract Supabase SCA cases from state."""
    if not state.acquired_data or not state.acquired_data.litigation_data:
        return []
    lit_data = state.acquired_data.litigation_data
    if isinstance(lit_data, dict):
        return lit_data.get("supabase_cases", [])
    return getattr(lit_data, "supabase_cases", []) or []


def _active_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to active/pending/ongoing/filed cases."""
    active_statuses = {"ACTIVE", "PENDING", "OPEN", "FILED", "ONGOING"}
    return [
        c for c in cases
        if isinstance(c, dict)
        and str(c.get("case_status", c.get("status", ""))).upper() in active_statuses
    ]


@register("LIT-01")
def _answer_lit_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Has this company ever been the target of a securities class action?"""
    cases = _get_supabase_cases(state)
    active = _active_cases(cases)

    if not cases:
        return no_data()

    evidence = []
    evidence.append(f"Total SCA filings: {len(cases)}")
    if active:
        evidence.append(f"Currently active: {len(active)}")
    settled = [c for c in cases if str(c.get("case_status", "")).upper() == "SETTLED"]
    if settled:
        amts = [c.get("settlement_amount_m") for c in settled if c.get("settlement_amount_m")]
        if amts:
            evidence.append(f"Settlement history: ${sum(amts):.1f}M across {len(settled)} case(s)")
    for c in cases[:3]:
        dt = c.get("filing_date", "?")
        st = c.get("case_status", "?")
        evidence.append(f"{dt}: {st}")

    if len(cases) == 0:
        verdict = "UPGRADE"
        answer = "No prior SCA history -- clean litigation record."
    elif active:
        verdict = "DOWNGRADE"
        answer = f"{len(cases)} SCA filings, {len(active)} currently active. CHRONIC filer."
    elif len(cases) >= 3:
        verdict = "DOWNGRADE"
        answer = f"CHRONIC filer -- {len(cases)} SCA filings (none currently active)."
    elif len(cases) == 1:
        verdict = "NEUTRAL"
        answer = "Single prior SCA filing."
    else:
        verdict = "DOWNGRADE"
        answer = f"REPEAT filer -- {len(cases)} SCA filings."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("LIT-02")
def _answer_lit_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Are there any active SCA or derivative lawsuits pending?"""
    cases = _get_supabase_cases(state)
    active = _active_cases(cases)

    # Also check lit_detail for derivative suits
    lit = ctx.get("lit_detail", {})
    derivs = lit.get("derivative_suits", [])

    evidence = []
    for c in active:
        dt = c.get("filing_date", "?")
        court = c.get("court", "?")
        status = c.get("case_status", "?")
        drop = c.get("stock_drop_pct")
        cp_start = c.get("class_period_start", "")
        cp_end = c.get("class_period_end", "")
        parts = [f"Filed {dt} in {court} ({status})"]
        if cp_start and cp_end:
            parts.append(f"Class period: {cp_start} to {cp_end}")
        if drop:
            parts.append(f"Stock drop: {drop}%")
        # Allegation types
        allegation_types = []
        for atype in ("accounting", "insider_trading", "earnings", "merger", "ipo_offering"):
            if c.get(f"allegation_{atype}"):
                allegation_types.append(atype.replace("_", " ").title())
        if allegation_types:
            parts.append(f"Allegations: {', '.join(allegation_types)}")
        evidence.append(" | ".join(parts))

    if derivs:
        evidence.append(f"Derivative suits: {len(derivs)}")

    if not active and not derivs:
        if cases:
            return {
                "answer": f"{len(cases)} historical SCA filing(s), none currently active.",
                "evidence": [f"Total historical filings: {len(cases)}"],
                "verdict": "UPGRADE",
                "confidence": "HIGH",
                "data_found": True,
            }
        return {
            "answer": "No pending D&O-related litigation detected.",
            "evidence": ["No active cases in Supabase SCA database"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    n_active = len(active) + len(derivs)
    verdict = "DOWNGRADE"
    answer = f"{n_active} active lawsuit(s) pending -- known loss exposure."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("LIT-03")
def _answer_lit_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Settlement history -- amounts, theories, and outcomes."""
    lit = ctx.get("lit_detail", {})

    rc_filings = lit.get("risk_card_filing_history", [])
    rc_repeat = lit.get("risk_card_repeat_filer", {})

    evidence = []
    if rc_repeat:
        settle_rate = rc_repeat.get("company_settlement_rate_pct")
        total_settle = rc_repeat.get("total_settlement_exposure_m")
        if settle_rate is not None:
            evidence.append(f"Settlement rate: {settle_rate}%")
        if total_settle is not None:
            evidence.append(f"Total settlement exposure: ${total_settle}M")

    if rc_filings:
        settled = [f for f in rc_filings if isinstance(f, dict) and "settled" in str(f.get("status", "")).lower()]
        evidence.append(f"Filings: {len(rc_filings)}, settled: {len(settled)}")
        for s in settled[:2]:
            amt = s.get("settlement_amount") or s.get("amount")
            if amt:
                evidence.append(f"Settlement: ${amt}M")

    # Fallback to cases
    if not evidence:
        cases = lit.get("cases", []) + lit.get("historical_cases", [])
        settled = [c for c in cases if isinstance(c, dict) and "settled" in str(c.get("status", "")).lower()]
        if settled:
            evidence.append(f"Settled cases: {len(settled)}")
            for c in settled[:2]:
                amt = c.get("settlement_amount")
                if amt:
                    evidence.append(f"Settlement: {amt}")

    if not evidence:
        return {
            "answer": "No settlement history found in database.",
            "evidence": ["No settlement data available"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    if rc_repeat and rc_repeat.get("total_settlement_exposure_m"):
        total = safe_float_extract(rc_repeat["total_settlement_exposure_m"])
        if total and total > 10:
            verdict = "DOWNGRADE"
            answer = f"Settlement exposure: ${rc_repeat['total_settlement_exposure_m']}M. Rate: {rc_repeat.get('company_settlement_rate_pct', 'N/A')}%."
        else:
            verdict = "NEUTRAL"
            answer = f"Settlement exposure: ${rc_repeat['total_settlement_exposure_m']}M."
    else:
        verdict = "NEUTRAL"
        answer = "Settlement data available -- review for patterns."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("LIT-04")
def _answer_lit_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Has the SEC or any regulator investigated or sanctioned the company?"""
    evidence = []

    sec_signals = triggered_signals(ctx, prefix="sec_enforcement")
    for s in sec_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check regulatory data
    if state.acquired_data:
        reg_data = getattr(state.acquired_data, "regulatory_data", None)
        if isinstance(reg_data, dict) and reg_data:
            for key, val in list(reg_data.items())[:3]:
                evidence.append(f"Regulatory: {key} = {str(val)[:100]}")

    if not evidence:
        return {
            "answer": "No SEC enforcement actions or regulatory investigations detected.",
            "evidence": ["No sec_enforcement signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = f"SEC/regulatory signals detected ({len(sec_signals)} signal(s))."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("LIT-05")
def _answer_lit_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """What litigation theories apply to this company's risk profile?"""
    peril = ctx.get("peril", {})
    scoring = ctx.get("score_detail", {})

    evidence = []

    # Peril map data
    if isinstance(peril, dict):
        theories = peril.get("allegation_theories") or peril.get("theories") or peril.get("top_perils")
        if isinstance(theories, list):
            for t in theories[:5]:
                if isinstance(t, dict):
                    name = t.get("theory", t.get("name", ""))
                    prob = t.get("probability", t.get("likelihood"))
                    evidence.append(f"Theory: {name}" + (f" ({prob})" if prob else ""))
                else:
                    evidence.append(f"Theory: {str(t)[:80]}")

    # Allegation mapping from scoring
    allegation_map = scoring.get("allegation_mapping")
    if isinstance(allegation_map, dict):
        for theory, detail in list(allegation_map.items())[:3]:
            evidence.append(f"Allegation: {theory} = {str(detail)[:80]}")

    if not evidence:
        return no_data()

    verdict = "DOWNGRADE" if len(evidence) >= 3 else "NEUTRAL"
    answer = f"{len(evidence)} litigation theories applicable to this risk profile."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("LIT-06")
def _answer_lit_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Non-SCA lawsuits that could generate D&O exposure."""
    evidence = []

    reg_signals = triggered_signals(ctx, prefix="regulatory")
    for s in reg_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check for non-SCA litigation in cases
    lit = ctx.get("lit_detail", {})
    cases = lit.get("cases", [])
    non_sca = [
        c for c in cases
        if isinstance(c, dict)
        and "sca" not in str(c.get("type", "")).lower()
        and "securities class" not in str(c.get("type", "")).lower()
    ]
    for c in non_sca[:3]:
        title = c.get("title", c.get("case_name", ""))
        evidence.append(f"Non-SCA case: {str(title)[:80]}")

    if not evidence:
        return {
            "answer": "No significant non-SCA litigation exposure detected.",
            "evidence": ["No regulatory signals triggered, no non-SCA cases"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE" if reg_signals or non_sca else "NEUTRAL"
    answer = f"Non-SCA litigation exposure: {len(reg_signals)} regulatory signal(s), {len(non_sca)} non-SCA case(s)."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("LIT-07")
def _answer_lit_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Statute of limitations window for recent events."""
    temporal = ctx.get("temporal", {})
    drops = ctx.get("enhanced_drop_events", [])

    evidence = []

    if isinstance(temporal, dict) and temporal:
        sol_windows = temporal.get("sol_windows") or temporal.get("statute_analysis")
        if isinstance(sol_windows, (list, dict)):
            evidence.append(f"SOL analysis available: {str(sol_windows)[:150]}")

    # Key events within SOL window (2-5 years)
    if drops:
        evidence.append(f"Stock drop events: {len(drops)} (each creates potential SOL window)")
        for d in drops[:2]:
            if isinstance(d, dict):
                evidence.append(f"Event: {d.get('date', '')} -- {d.get('pct_change', '')}%")

    if not evidence:
        return no_data()

    has_recent_events = bool(drops) or (isinstance(temporal, dict) and temporal)
    verdict = "DOWNGRADE" if has_recent_events else "NEUTRAL"
    answer = f"SOL window analysis: {len(drops)} trigger event(s) identified."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
