"""Answerers for Domain 7: D&O Program & Pricing (PRG-01 through PRG-05)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    fmt_currency,
    no_data,
    safe_float_extract,
    yf_info,
)
from do_uw.stages.render.context_builders.answerers.sca_questions import (
    _extract_risk_card_from_state,
)


@register("PRG-01")
def _answer_prg_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Current D&O tower and adequacy for exposure."""
    yfi = yf_info(ctx)
    mc_raw = safe_float_extract(yfi.get("marketCap"))

    evidence = []

    # Tower recommendation from scoring
    if state.scoring:
        tower_rec = getattr(state.scoring, "tower_recommendation", None)
        if tower_rec:
            evidence.append(f"Tower recommendation: {tower_rec}")

    if mc_raw:
        evidence.append(f"Market cap: {fmt_currency(mc_raw)}")
        # Standard tower sizing guidelines
        if mc_raw >= 50e9:
            tower_guide = "$100M+ tower recommended"
        elif mc_raw >= 10e9:
            tower_guide = "$50-100M tower recommended"
        elif mc_raw >= 2e9:
            tower_guide = "$25-50M tower recommended"
        elif mc_raw >= 500e6:
            tower_guide = "$10-25M tower recommended"
        else:
            tower_guide = "$5-10M tower recommended"
        evidence.append(f"Guideline: {tower_guide}")

    if not evidence:
        return no_data()

    verdict = "NEUTRAL"
    if mc_raw:
        answer = f"Market cap {fmt_currency(mc_raw)}. {tower_guide}."
    else:
        answer = "Tower adequacy assessment requires market cap data."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("PRG-02")
def _answer_prg_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Claims history on this specific program."""
    # Get SCA data from risk card (state), not lit_detail context
    risk_card = _extract_risk_card_from_state(state)
    rc_filings = risk_card.get("filing_history", []) if risk_card else []
    rc_repeat = risk_card.get("repeat_filer_detail", {}) if risk_card else {}

    evidence = []
    if rc_filings:
        evidence.append(f"SCA filings: {len(rc_filings)}")
    if rc_repeat:
        cat = rc_repeat.get("filer_category", "NONE")
        evidence.append(f"Filer category: {cat}")

    # Claim probability from scoring
    if state.scoring:
        claim_prob = getattr(state.scoring, "claim_probability", None)
        if claim_prob:
            evidence.append(f"Claim probability: {claim_prob}")

    if not evidence:
        return no_data()

    n_filings = len(rc_filings) if rc_filings else 0
    if n_filings == 0:
        verdict = "UPGRADE"
        answer = "Clean claims history -- no prior SCA filings."
    elif n_filings >= 2:
        verdict = "DOWNGRADE"
        answer = f"{n_filings} prior SCA filings -- repeat filer history."
    else:
        verdict = "NEUTRAL"
        answer = f"{n_filings} prior SCA filing(s) in history."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("PRG-03")
def _answer_prg_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Risk pricing relative to peers."""
    evidence = []

    # Benchmark data
    if state.benchmark:
        peer_comp = getattr(state.benchmark, "peer_comparison", None)
        if isinstance(peer_comp, dict):
            for key in ["rpm", "peer_median_rpm", "percentile"]:
                if key in peer_comp:
                    evidence.append(f"{key}: {peer_comp[key]}")

    # Actuarial pricing from scoring
    if state.scoring:
        actuarial = getattr(state.scoring, "actuarial_pricing", None)
        if isinstance(actuarial, dict):
            for key, val in list(actuarial.items())[:3]:
                evidence.append(f"Actuarial {key}: {val}")

    if not evidence:
        return no_data()

    verdict = "NEUTRAL"
    answer = "Peer pricing comparison data available."
    if state.benchmark:
        answer = "Benchmark data available for peer rate comparison."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("PRG-04")
def _answer_prg_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Appropriate retention level."""
    yfi = yf_info(ctx)
    mc_raw = safe_float_extract(yfi.get("marketCap"))

    evidence = []
    if mc_raw:
        evidence.append(f"Market cap: {fmt_currency(mc_raw)}")

        # Standard retention guidelines by market cap
        if mc_raw >= 50e9:
            ret_guide = "$10M+ retention recommended"
            min_ret = "$10M"
        elif mc_raw >= 10e9:
            ret_guide = "$5-10M retention recommended"
            min_ret = "$5M"
        elif mc_raw >= 2e9:
            ret_guide = "$2.5-5M retention recommended"
            min_ret = "$2.5M"
        elif mc_raw >= 500e6:
            ret_guide = "$1-2.5M retention recommended"
            min_ret = "$1M"
        else:
            ret_guide = "$500K-1M retention recommended"
            min_ret = "$500K"

        evidence.append(f"Guideline: {ret_guide}")

        verdict = "NEUTRAL"
        answer = f"Market cap {fmt_currency(mc_raw)}. {ret_guide}. Minimum: {min_ret}."
    else:
        return no_data()

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("PRG-05")
def _answer_prg_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Coverage gaps or problematic exclusions."""
    evidence = []

    # Check scoring for allegation mapping → needed exclusions
    scoring = ctx.get("score_detail", {})
    allegation_map = scoring.get("allegation_mapping")
    if isinstance(allegation_map, dict):
        for theory, detail in list(allegation_map.items())[:3]:
            evidence.append(f"Theory requiring coverage: {theory}")

    # Red flags that suggest exclusion needs
    red_flags = scoring.get("red_flags", [])
    if isinstance(red_flags, list):
        for rf in red_flags[:3]:
            if isinstance(rf, dict):
                evidence.append(f"Red flag: {rf.get('description', str(rf))[:80]}")
            else:
                evidence.append(f"Red flag: {str(rf)[:80]}")

    if not evidence:
        return {
            "answer": "No specific coverage gaps identified from pipeline analysis. Standard broad form recommended.",
            "evidence": ["Standard coverage assessment"],
            "verdict": "UPGRADE",
            "confidence": "LOW",
            "data_found": True,
        }

    verdict = "NEUTRAL"
    answer = f"{len(evidence)} risk factors identified that may require specific coverage review."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }
