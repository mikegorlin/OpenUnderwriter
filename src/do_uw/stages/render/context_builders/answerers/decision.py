"""Answerers for Domain 8: Underwriting Decision (UW-01 through UW-07)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    no_data,
    safe_float_extract,
    triggered_signals,
)


@register("UW-01")
def _answer_uw_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Overall risk tier and score."""
    scoring = ctx.get("score_detail", {})

    tier = scoring.get("risk_tier", scoring.get("tier", ""))
    score = scoring.get("total_score", scoring.get("score", ""))
    red_flags = scoring.get("red_flag_count", 0)

    evidence = []
    if tier:
        evidence.append(f"Risk tier: {tier}")
    if score:
        evidence.append(f"Score: {score}")
    if red_flags:
        evidence.append(f"Red flags: {red_flags}")

    if not evidence:
        return no_data()

    tier_str = str(tier).upper()
    if "LOW" in tier_str or "FAVORABLE" in tier_str:
        verdict = "UPGRADE"
        answer = f"Risk tier: {tier}. Score: {score}."
    elif "HIGH" in tier_str or "CRITICAL" in tier_str:
        verdict = "DOWNGRADE"
        answer = f"Risk tier: {tier}. Score: {score}. {red_flags} red flags."
    else:
        verdict = "NEUTRAL"
        answer = f"Risk tier: {tier}. Score: {score}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("UW-02")
def _answer_uw_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Top 3 reasons to write this risk."""
    scoring = ctx.get("score_detail", {})
    evidence = []

    # Find lowest-deduction factors (strengths)
    factor_scores = scoring.get("factor_scores", {})
    if isinstance(factor_scores, dict):
        # Sort by deduction (ascending = best factors first)
        sorted_factors = sorted(
            factor_scores.items(),
            key=lambda x: safe_float_extract(x[1].get("deduction", 0) if isinstance(x[1], dict) else x[1], 0) or 0,
        )
        for name, detail in sorted_factors[:3]:
            if isinstance(detail, dict):
                ded = detail.get("deduction", 0)
                evidence.append(f"Strength: {name} (deduction: {ded})")
            else:
                evidence.append(f"Strength: {name} = {detail}")
    elif isinstance(factor_scores, list):
        for f in factor_scores[:3]:
            if isinstance(f, dict):
                evidence.append(f"Factor: {f.get('name', '')} = {f.get('score', f.get('deduction', ''))}")

    # Add any upgrade factors
    upgrade_factors = scoring.get("upgrade_factors", [])
    if isinstance(upgrade_factors, list):
        for uf in upgrade_factors[:3]:
            evidence.append(f"Upgrade: {str(uf)[:80]}")

    if not evidence:
        return no_data()

    answer = f"Top strengths: {', '.join(e.split(': ', 1)[1] if ': ' in e else e for e in evidence[:3])}."
    verdict = "UPGRADE"

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("UW-03")
def _answer_uw_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Top 3 reasons NOT to write this risk."""
    scoring = ctx.get("score_detail", {})
    evidence = []

    # Red flags
    red_flags = scoring.get("red_flags", [])
    if isinstance(red_flags, list):
        for rf in red_flags[:3]:
            if isinstance(rf, dict):
                evidence.append(f"Red flag: {rf.get('description', rf.get('flag', str(rf)))[:80]}")
            else:
                evidence.append(f"Red flag: {str(rf)[:80]}")

    # Highest-deduction factors
    factor_scores = scoring.get("factor_scores", {})
    if isinstance(factor_scores, dict):
        sorted_factors = sorted(
            factor_scores.items(),
            key=lambda x: safe_float_extract(x[1].get("deduction", 0) if isinstance(x[1], dict) else x[1], 0) or 0,
            reverse=True,
        )
        for name, detail in sorted_factors[:3]:
            if isinstance(detail, dict):
                ded = detail.get("deduction", 0)
                if ded and safe_float_extract(ded, 0):
                    evidence.append(f"Concern: {name} (deduction: {ded})")

    if not evidence:
        return {
            "answer": "No significant risk factors identified -- clean risk profile.",
            "evidence": ["No red flags or high deductions"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    answer = f"Top concerns: {', '.join(e.split(': ', 1)[1] if ': ' in e else e for e in evidence[:3])}."
    verdict = "DOWNGRADE"

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("UW-04")
def _answer_uw_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Specific conditions or exclusions required."""
    scoring = ctx.get("score_detail", {})
    evidence = []

    # Red flags → conditions
    red_flags = scoring.get("red_flags", [])
    if isinstance(red_flags, list):
        for rf in red_flags[:3]:
            if isinstance(rf, dict):
                evidence.append(f"Condition driver: {rf.get('description', str(rf))[:80]}")

    # Allegation mapping → exclusion needs
    allegation_map = scoring.get("allegation_mapping")
    if isinstance(allegation_map, dict):
        for theory in list(allegation_map.keys())[:3]:
            evidence.append(f"Theory requiring review: {theory}")

    if not evidence:
        return {
            "answer": "Standard terms appear sufficient based on pipeline analysis.",
            "evidence": ["No specific condition drivers identified"],
            "verdict": "UPGRADE",
            "confidence": "LOW",
            "data_found": True,
        }

    verdict = "NEUTRAL"
    answer = f"{len(evidence)} factor(s) suggest specific conditions or exclusion review."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }


@register("UW-05")
def _answer_uw_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Right price for this risk at the proposed attachment."""
    evidence = []

    # Actuarial pricing
    if state.scoring:
        actuarial = getattr(state.scoring, "actuarial_pricing", None)
        if isinstance(actuarial, dict):
            for key, val in list(actuarial.items())[:3]:
                evidence.append(f"Actuarial {key}: {val}")

        severity = getattr(state.scoring, "severity_scenarios", None)
        if isinstance(severity, dict):
            for key, val in list(severity.items())[:3]:
                evidence.append(f"Severity {key}: {val}")

    scoring = ctx.get("score_detail", {})
    tier = scoring.get("risk_tier", scoring.get("tier", ""))
    if tier:
        evidence.append(f"Risk tier: {tier}")

    if not evidence:
        return no_data()

    verdict = "NEUTRAL"
    answer = f"Pricing analysis available. Risk tier: {tier or 'N/A'}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }


@register("UW-06")
def _answer_uw_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """What would make you decline this risk?"""
    scoring = ctx.get("score_detail", {})
    evidence = []

    # Red flags as potential decline triggers
    red_flags = scoring.get("red_flags", [])
    if isinstance(red_flags, list):
        for rf in red_flags[:5]:
            if isinstance(rf, dict):
                evidence.append(f"Potential trigger: {rf.get('description', str(rf))[:80]}")
            else:
                evidence.append(f"Potential trigger: {str(rf)[:80]}")

    # Ceiling details
    if state.scoring:
        ceiling = getattr(state.scoring, "ceiling_details", None)
        if isinstance(ceiling, dict) and ceiling:
            for key, val in list(ceiling.items())[:3]:
                evidence.append(f"Ceiling: {key} = {str(val)[:80]}")

    if not evidence:
        return {
            "answer": "No decline triggers present based on pipeline analysis.",
            "evidence": ["No red flags or ceiling constraints"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    n_triggers = len(evidence)
    if n_triggers >= 3:
        verdict = "DOWNGRADE"
        answer = f"{n_triggers} potential decline triggers identified -- careful review required."
    else:
        verdict = "NEUTRAL"
        answer = f"{n_triggers} factor(s) warrant monitoring but no automatic decline."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("UW-07")
def _answer_uw_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Follow-up information needed from the broker."""
    evidence = []

    # Count skipped signals needing human review
    if state.analysis and hasattr(state.analysis, "disposition_summary"):
        ds = state.analysis.disposition_summary
        if isinstance(ds, dict):
            skipped = ds.get("skipped", 0)
            if skipped:
                evidence.append(f"Skipped signals needing review: {skipped}")

    # Low-confidence data
    all_signals = triggered_signals(ctx)
    low_conf = [
        s for s in all_signals
        if isinstance(s, dict) and str(s.get("confidence", "")).upper() == "LOW"
    ]
    if low_conf:
        evidence.append(f"Low-confidence signals: {len(low_conf)}")
        for s in low_conf[:3]:
            evidence.append(f"Verify: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:60]}")

    if not evidence:
        return {
            "answer": "All key data available from public sources. No critical information gaps.",
            "evidence": ["Pipeline data coverage adequate"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "NEUTRAL"
    answer = f"{len(evidence)} information gap(s) identified for broker follow-up."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "LOW",
        "data_found": True,
    }
