"""Evaluative analysis context builders -- forensic composites, executive risk,
NLP signals, temporal trends, and peril map.

Extracted from analysis.py (Phase 113-04). All functions enrich with signal
results via the _signal_fallback typed consumer API.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.formatters_humanize import humanize_check_evidence

_RAW_EVIDENCE_RE = re.compile(
    r"(?:Key evidence|Key risk indicators):\s*Value\s+[\d.]+\s+(?:exceeds|below)\s+(?:red|yellow)\s+threshold",
    re.IGNORECASE,
)


def _clean_committee_summary(text: str) -> str:
    """Strip raw threshold data from committee summaries."""
    if not text:
        return text
    match = _RAW_EVIDENCE_RE.search(text)
    if not match:
        return text
    prefix = text[:match.start()].rstrip()
    if prefix.endswith("."):
        return prefix
    last_dot = prefix.rfind(".")
    return prefix[:last_dot + 1] if last_dot > 10 else prefix + "."


def extract_forensic_composites(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract FIS, RQS, CFQS forensic composite scores for template."""
    if state.analysis is None or state.analysis.forensic_composites is None:
        return None

    fc = state.analysis.forensic_composites
    composites: list[dict[str, Any]] = []

    variants: list[tuple[list[str], str]] = [
        (["fis", "FIS", "financial_integrity_score"], "Financial Integrity Score (FIS)"),
        (["rqs", "RQS", "revenue_quality_score"], "Reporting Quality Score (RQS)"),
        (["cfqs", "CFQS", "cash_flow_quality_score"], "Cash Flow Quality Score (CFQS)"),
    ]
    for keys, label in variants:
        data = None
        for k in keys:
            data = fc.get(k)
            if data is not None:
                break

        if data is None:
            composites.append({"name": label, "score": "N/A", "interpretation": "Not available", "sub_scores": {}})
            continue
        if isinstance(data, dict):
            score = data.get("overall_score", data.get("score", data.get("value", "N/A")))
            zone = data.get("zone", data.get("interpretation", data.get("label", "")))
            sub_scores: dict[str, Any] = {}
            raw_subs = data.get("sub_scores", {})
            if isinstance(raw_subs, dict):
                for sn, sv in raw_subs.items():
                    sub_scores[sn.replace("_", " ").title()] = (
                        f"{sv:.0f}/100" if isinstance(sv, (int, float)) else str(sv)
                    )
            composites.append({
                "name": label,
                "score": f"{score:.0f}/100" if isinstance(score, (int, float)) else str(score),
                "interpretation": str(zone).replace("_", " ").title() if zone else "N/A",
                "sub_scores": sub_scores,
            })
        else:
            composites.append({"name": label, "score": f"{data:.0f}/100" if isinstance(data, (int, float)) else str(data), "interpretation": "N/A", "sub_scores": {}})

    return {"composites": composites, "raw": fc}


# -- Executive Risk --


def extract_executive_risk(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract executive/board aggregate risk profile for template."""
    if state.analysis is None or state.analysis.executive_risk is None:
        return None

    er = state.analysis.executive_risk
    weighted_score = er.get("weighted_score", er.get("overall_score", "N/A"))
    risk_level = er.get("risk_level", er.get("assessment", "N/A"))
    findings = er.get("findings", er.get("key_findings", []))

    # Enrich with EXEC.* signal results when available
    exec_signals = safe_get_signals_by_prefix(signal_results, "EXEC.")
    signal_findings: list[str] = []
    for sig in exec_signals:
        if sig.status in ("TRIGGERED", "ELEVATED") and sig.evidence:
            signal_findings.append(sig.evidence)

    cleaned_findings: list[dict[str, str]] = []
    if isinstance(findings, list):
        for f in findings[:15]:
            raw = str(f)
            m = re.match(r"\[([^\]]+)\]:\s*(.+)", raw)
            if m:
                person = m.group(1).strip()
                detail = m.group(2).strip()
                detail = re.sub(r"^Prior litigation:\s*", "", detail)
                cleaned_findings.append({"person": person, "detail": detail})
            else:
                cleaned_findings.append({"person": "", "detail": raw})
    elif findings:
        cleaned_findings.append({"person": "", "detail": str(findings)})

    # Append signal-derived findings not already present
    for sf in signal_findings[:5]:
        if not any(sf[:50] in cf["detail"] for cf in cleaned_findings):
            cleaned_findings.append({"person": "", "detail": sf[:200]})

    return {
        "weighted_score": f"{weighted_score:.0f}" if isinstance(weighted_score, (int, float)) else str(weighted_score),
        "risk_level": str(risk_level),
        "findings": cleaned_findings,
    }


# -- Temporal Signals --


def extract_temporal_signals(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> list[dict[str, str]] | None:
    """Extract temporal trend signals for template rendering."""
    if state.analysis is None or state.analysis.temporal_signals is None:
        return None

    ts = state.analysis.temporal_signals
    signals = ts.get("signals", ts.get("trends", []))
    if not signals:
        if "direction" in ts or "type" in ts:
            signals = [ts]
        else:
            return None

    result: list[dict[str, str]] = []
    for sig in signals:
        if isinstance(sig, dict):
            result.append({
                "type": str(sig.get("type", sig.get("signal_type", "Unknown"))),
                "direction": str(sig.get("direction", sig.get("trend", "N/A"))),
                "magnitude": str(sig.get("magnitude", sig.get("change_pct", "N/A"))),
                "description": str(sig.get("description", sig.get("narrative", ""))),
            })

    # Enrich with DISC.* trend signals
    disc_signals = safe_get_signals_by_prefix(signal_results, "DISC.")
    for sig in disc_signals:
        if sig.status in ("TRIGGERED", "ELEVATED") and sig.evidence:
            result.append({
                "type": sig.signal_id, "direction": sig.status,
                "magnitude": str(sig.value) if sig.value else "N/A",
                "description": sig.evidence[:200],
            })

    return result if result else None


# -- NLP Signals --


def _format_readability(readability: Any) -> str:
    """Format readability value from NLP signals dict."""
    if isinstance(readability, dict):
        cls = readability.get("classification", "N/A")
        ev = readability.get("evidence", "")
        if cls in ("INSUFFICIENT_DATA", "N/A"):
            return "Insufficient data for analysis"
        return f"{cls} -- {ev}" if ev and ev != cls else str(cls)
    if isinstance(readability, (int, float)):
        return f"{readability:.1f}"
    return str(readability) if readability else "N/A"


def extract_nlp_signals(
    state: AnalysisState, *, signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract NLP signals, sentiment profile, and narrative coherence."""
    from do_uw.stages.render.context_builders._nlp_helpers import (
        build_lm_trends, extract_coherence_data, extract_sentiment_data,
    )
    nlp = state.analysis.nlp_signals if state.analysis else None
    sentiment_data = extract_sentiment_data(state)
    coherence_data = extract_coherence_data(state)
    lm_trends = build_lm_trends(state)
    if nlp is None and not sentiment_data:
        return None
    result: dict[str, Any] = {"readability": "N/A", "tone": "N/A", "risk_density": "N/A"}
    if nlp:
        readability = nlp.get("readability_score", nlp.get("readability", "N/A"))
        tone = nlp.get("tone_assessment", nlp.get("tone", "N/A"))
        risk_density = nlp.get("risk_language_density", nlp.get("risk_density", "N/A"))
        result["readability"] = _format_readability(readability)
        result["tone"] = str(tone)
        result["risk_density"] = (
            f"{risk_density:.2f}" if isinstance(risk_density, (int, float)) else str(risk_density)
        )
        result["raw"] = nlp
    result.update(sentiment_data)
    if lm_trends:
        result["lm_trends"] = lm_trends
    if coherence_data:
        result["coherence"] = coherence_data
    # Enrich with NLP.* signal results
    for sig in safe_get_signals_by_prefix(signal_results, "NLP."):
        if sig.status in ("TRIGGERED", "ELEVATED"):
            result.setdefault("signal_alerts", []).append({
                "signal_id": sig.signal_id, "status": sig.status,
                "evidence": sig.evidence[:200] if sig.evidence else "",
            })
    return result


# -- Peril Map --


def extract_peril_map(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract peril map data for MD/HTML template rendering."""
    if state.analysis is None or state.analysis.peril_map is None:
        return None

    pm = state.analysis.peril_map
    overall = pm.get("overall_assessment") or pm.get("overall_peril_rating") or pm.get("summary")

    assessments: list[dict[str, str]] = []
    for a in pm.get("assessments", pm.get("plaintiff_assessments", [])):
        if not isinstance(a, dict):
            continue
        findings = a.get("key_findings", [])
        assessments.append({
            "type": str(a.get("plaintiff_type", a.get("peril_type", "Unknown"))).replace("_", " ").title(),
            "probability": str(a.get("probability_band", a.get("likelihood", "N/A"))).replace("_", " "),
            "severity": str(a.get("severity_band", a.get("severity", "N/A"))).replace("_", " "),
            "evidence": "; ".join(humanize_check_evidence(str(f)) for f in findings[:2]) if findings else "",
        })

    bear_cases: list[dict[str, str]] = []
    for bc in pm.get("bear_cases", []):
        if not isinstance(bc, dict):
            continue
        bear_cases.append({
            "theory": str(bc.get("theory", "Unknown")).replace("_", " ").title(),
            "summary": _clean_committee_summary(str(bc.get("committee_summary", bc.get("summary", "")))),
            "probability": str(bc.get("probability_band", "N/A")).replace("_", " "),
            "severity": str(bc.get("severity_estimate", "N/A")).replace("_", " "),
        })

    if not overall and assessments:
        prob_order = {"critical": 4, "elevated": 3, "moderate": 2, "low": 1}
        highest_prob = max(
            (prob_order.get(a["probability"].lower(), 0), a["type"]) for a in assessments
        )
        key_plaintiffs = [
            a["type"] for a in assessments
            if prob_order.get(a["probability"].lower(), 0) >= 3
        ]
        if key_plaintiffs:
            overall = f"{highest_prob[1]} exposure ({highest_prob[0]}) -- {', '.join(key_plaintiffs)} present significant risk"
        else:
            overall = f"Moderate exposure across {len(assessments)} plaintiff types"
    elif not overall:
        overall = "N/A"

    return {
        "overall_assessment": str(overall),
        "assessments": assessments,
        "bear_cases": bear_cases,
    }
