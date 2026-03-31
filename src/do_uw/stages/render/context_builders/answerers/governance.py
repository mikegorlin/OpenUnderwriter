"""Answerers for Domain 3: Governance & People Risk (GOV-01 through GOV-08)."""

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


@register("GOV-01")
def _answer_gov_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Is the board truly independent or does management control it?"""
    gov = ctx.get("gov", {})

    board_size = gov.get("board_size")
    ind_pct = gov.get("board_independence_pct") or gov.get("pct_independent")
    ceo_chair = gov.get("ceo_duality")

    evidence = []
    if board_size:
        evidence.append(f"Board size: {board_size}")
    if ind_pct:
        evidence.append(f"Independence: {ind_pct}")
    if ceo_chair is not None:
        evidence.append(f"CEO/Chair combined: {'Yes' if ceo_chair else 'No'}")

    if not evidence:
        return no_data()

    ind_val = safe_float_extract(str(ind_pct).replace("%", "").strip()) if ind_pct else None

    if ind_val and ind_val >= 75 and not ceo_chair:
        verdict = "UPGRADE"
        answer = f"Strong governance -- {ind_pct} independent, separate CEO/Chair."
    elif ind_val and ind_val < 50:
        verdict = "DOWNGRADE"
        answer = f"Weak independence -- only {ind_pct} independent directors."
    elif ceo_chair:
        verdict = "DOWNGRADE"
        answer = f"CEO serves as Board Chair. Independence: {ind_pct or 'unknown'}."
    else:
        verdict = "NEUTRAL"
        answer = f"Board: {board_size} directors, {ind_pct or 'unknown'}% independent."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("GOV-02")
def _answer_gov_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Has the CEO or any director been personally sued or investigated?"""
    evidence = []

    exec_lit_signals = triggered_signals(ctx, prefix="exec_litigation")
    exec_risk = ctx.get("exec_risk")

    for s in exec_lit_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    if isinstance(exec_risk, dict):
        for key, val in list(exec_risk.items())[:3]:
            if val and "litigation" in str(key).lower():
                evidence.append(f"Exec risk: {str(val)[:120]}")

    # Check litigation cases for officer/director names
    lit = ctx.get("lit_detail", {})
    cases = lit.get("cases", [])
    if cases:
        for c in cases[:2]:
            if isinstance(c, dict):
                defendants = c.get("defendants", [])
                if defendants:
                    evidence.append(f"Case defendants: {', '.join(str(d)[:40] for d in defendants[:3])}")

    if not evidence:
        return {
            "answer": "No personal litigation history detected for officers/directors in pipeline data.",
            "evidence": ["No exec_litigation signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = f"Executive litigation signals detected ({len(exec_lit_signals)} signal(s))."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("GOV-03")
def _answer_gov_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Is executive compensation aligned with shareholders?"""
    gov = ctx.get("gov", {})
    evidence = []

    ceo_comp = gov.get("ceo_comp", {})
    sop = gov.get("say_on_pay")
    pay_ratio = gov.get("pay_ratio")

    if isinstance(ceo_comp, dict) and ceo_comp:
        total = ceo_comp.get("total", ceo_comp.get("total_comp"))
        if total:
            evidence.append(f"CEO total compensation: {total}")
    elif isinstance(ceo_comp, (int, float, str)) and ceo_comp:
        evidence.append(f"CEO compensation: {ceo_comp}")

    if sop is not None:
        evidence.append(f"Say-on-pay: {sop}%")
    if pay_ratio is not None:
        evidence.append(f"Pay ratio: {pay_ratio}")

    # Try extracted governance
    if not evidence and state.extracted and state.extracted.governance:
        comp = getattr(state.extracted.governance, "compensation", None)
        if comp:
            evidence.append(f"Compensation data: {str(comp)[:120]}")

    if not evidence:
        return no_data()

    sop_val = safe_float_extract(str(sop).replace("%", "")) if sop else None

    if sop_val and sop_val < 70:
        verdict = "DOWNGRADE"
        answer = f"Say-on-pay only {sop_val:.0f}% -- below 70% threshold. Shareholder dissatisfaction."
    elif sop_val and sop_val >= 85:
        verdict = "UPGRADE"
        answer = f"Strong say-on-pay approval ({sop_val:.0f}%). Compensation aligned."
    else:
        verdict = "NEUTRAL"
        parts = []
        if ceo_comp:
            parts.append(f"CEO comp: {ceo_comp if isinstance(ceo_comp, str) else 'reported'}")
        if sop_val:
            parts.append(f"Say-on-pay: {sop_val:.0f}%")
        answer = ". ".join(parts) + "." if parts else "Compensation data available."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("GOV-04")
def _answer_gov_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Are there related-party transactions or conflicts of interest?"""
    evidence = []

    rpt_signals = triggered_signals(ctx, prefix="related_party")
    for s in rpt_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    if not evidence:
        # No RPT signals = clean
        return {
            "answer": "No related-party transaction signals triggered in pipeline analysis.",
            "evidence": ["No related_party signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = f"{len(rpt_signals)} related-party transaction signal(s) triggered."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("GOV-05")
def _answer_gov_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Director tenure and recent board changes."""
    gov = ctx.get("gov", {})
    evidence = []

    board_members = gov.get("board_members", [])
    if not board_members:
        return no_data()

    n_directors = len(board_members)
    evidence.append(f"Directors: {n_directors}")

    # Try to extract tenure
    tenures: list[float] = []
    for d in board_members:
        if isinstance(d, dict):
            t = d.get("tenure") or d.get("years_on_board")
            if t is not None:
                tv = safe_float_extract(t)
                if tv is not None:
                    tenures.append(tv)

    if tenures:
        avg_tenure = sum(tenures) / len(tenures)
        evidence.append(f"Average tenure: {avg_tenure:.1f} years")
        evidence.append(f"Tenure range: {min(tenures):.0f} - {max(tenures):.0f} years")

        if avg_tenure < 2:
            verdict = "DOWNGRADE"
            answer = f"Very short average director tenure ({avg_tenure:.1f} years) -- potential board instability."
        elif avg_tenure > 20:
            verdict = "DOWNGRADE"
            answer = f"Long average tenure ({avg_tenure:.1f} years) -- potential entrenchment risk."
        else:
            verdict = "NEUTRAL"
            answer = f"Board of {n_directors} directors with average tenure of {avg_tenure:.1f} years."
    else:
        verdict = "NEUTRAL"
        answer = f"Board of {n_directors} directors. Tenure data not extracted."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW" if not tenures else "MEDIUM",
        "data_found": True,
    }


@register("GOV-06")
def _answer_gov_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Do officers and directors have adequate D&O-relevant experience?"""
    gov = ctx.get("gov", {})
    evidence = []

    board_members = gov.get("board_members", [])
    if not board_members:
        return no_data()

    n_directors = len(board_members)
    evidence.append(f"Directors: {n_directors}")

    # Check qualifications
    qualified = 0
    for d in board_members:
        if isinstance(d, dict):
            quals = d.get("qualifications") or d.get("background") or d.get("expertise")
            if quals:
                qualified += 1

    if qualified > 0:
        evidence.append(f"Directors with qualifications data: {qualified}/{n_directors}")
        verdict = "NEUTRAL"
        answer = f"{qualified} of {n_directors} directors have qualification disclosures."
    else:
        return {
            **partial_answer(
                f"Board of {n_directors} directors",
                "qualification/experience details not extracted",
                "DEF 14A director biographies",
            ),
            "evidence": evidence,
        }

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }


@register("GOV-07")
def _answer_gov_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Are there any character or integrity concerns for key officers?"""
    evidence = []

    exec_risk_signals = triggered_signals(ctx, prefix="exec_risk")
    exec_risk = ctx.get("exec_risk")

    for s in exec_risk_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    if isinstance(exec_risk, dict):
        for key, val in list(exec_risk.items())[:3]:
            if val and isinstance(val, (str, dict)):
                evidence.append(f"Exec risk ({key}): {str(val)[:120]}")

    if not evidence:
        return {
            "answer": "No character or integrity flags detected in pipeline analysis.",
            "evidence": ["No exec_risk signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = f"Executive risk signals detected ({len(exec_risk_signals)} signal(s))."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("GOV-08")
def _answer_gov_08(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Is there a dual-class share structure or controlling shareholder?"""
    evidence = []

    ctrl_signals = [
        s for s in triggered_signals(ctx)
        if "controlled_company" in str(s.get("signal_id", "")).lower()
        or "dual_class" in str(s.get("signal_id", "")).lower()
    ]

    for s in ctrl_signals[:2]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check governance data
    if state.extracted and state.extracted.governance:
        ownership = getattr(state.extracted.governance, "ownership", None)
        if isinstance(ownership, dict):
            dual = ownership.get("dual_class") or ownership.get("share_structure")
            if dual:
                evidence.append(f"Share structure: {str(dual)[:100]}")

    if not evidence:
        return {
            "answer": "No dual-class structure or controlling shareholder detected.",
            "evidence": ["No controlled_company signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = "Dual-class structure or controlling shareholder flags detected."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
