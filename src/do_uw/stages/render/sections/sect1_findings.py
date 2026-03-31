"""Key findings narrative builders for Section 1 Executive Summary.

Public API: build_negative_narrative() and build_positive_narrative().
Dispatches to type-specific sub-builders in sect1_findings_neg/pos.

Phase 60-01: Migrated from state access to shared context dict.
Phase 115: Rewrote narratives to pull real data and explain D&O risk.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.executive_summary import KeyFinding
from do_uw.models.state import AnalysisState
from do_uw.stages.render.sections.sect1_findings_data import company_name
from do_uw.stages.render.sections.sect1_findings_neg import (
    neg_audit_issues,
    neg_distress,
    neg_doj,
    neg_enforcement,
    neg_from_finding,
    neg_governance,
    neg_guidance,
    neg_ipo_ma,
    neg_prior_litigation,
    neg_short_interest,
    neg_stock_risk,
)
from do_uw.stages.render.sections.sect1_findings_pos import (
    pos_clean_audit,
    pos_low_short,
    pos_no_distress,
    pos_no_enforcement,
    pos_stable_leadership,
    pos_strong_governance,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_negative_narrative(
    finding: KeyFinding,
    idx: int,
    context: dict[str, Any],
) -> tuple[str, str]:
    """Build a 3-5 sentence narrative for a negative finding.

    Returns (title, body) backed by real state data.
    """
    state: AnalysisState = context["_state"]
    title = _extract_finding_title(finding)
    raw = finding.evidence_narrative
    origin = finding.section_origin or ""
    name = company_name(state)

    # Dispatch to type-specific narrative builder.
    # IMPORTANT: Check "Prior Litigation" before enforcement patterns
    # because prior lit findings can have enforcement-related origins.
    if "Prior Litigation" in raw:
        sentences = neg_prior_litigation(state, name)
    elif "Wells Notice" in raw or "ENFORCEMENT" in origin.upper():
        sentences = neg_enforcement(state, name)
    elif "DOJ" in raw or "DOJ" in origin:
        sentences = neg_doj(name, _clean_origin(origin))
    elif "Restatement" in raw or "Audit" in raw:
        sentences = neg_audit_issues(state, name)
    elif "Guidance" in raw:
        sentences = neg_guidance(state, name)
    elif "Volatility" in raw or "Stock" in raw:
        sentences = neg_stock_risk(state, name, raw)
    elif "Governance" in raw:
        sentences = neg_governance(state, name)
    elif "Short" in raw:
        sentences = neg_short_interest(state, name)
    elif "Distress" in raw:
        sentences = neg_distress(state, name)
    elif "IPO" in raw or "SPAC" in raw or "M&A" in raw:
        sentences = neg_ipo_ma(state, name)
    else:
        sentences = neg_from_finding(state, name, finding)

    # Critical Red Flag ceiling — use resolved ceiling from RedFlagResult,
    # not the baked scoring_impact text (which may have the raw configured
    # ceiling instead of the size-adjusted one).
    impact = finding.scoring_impact
    if impact and "Ceiling" in impact:
        ceiling_val = _get_resolved_ceiling(state, finding)
        sentences.append(
            "This triggers a Critical Red Flag, imposing a "
            f"score ceiling of {ceiling_val}."
        )

    xref = _section_cross_ref(finding)
    if xref:
        sentences.append(xref)

    return (title, " ".join(sentences))


def _get_resolved_ceiling(state: AnalysisState, finding: KeyFinding) -> str:
    """Get the resolved (size-adjusted) ceiling from RedFlagResult objects.

    Falls back to parsing the baked scoring_impact text if no matching
    RedFlagResult is found.
    """
    # The quality_score IS the ceiling-adjusted score (size-aware).
    # Use it directly instead of reading the potentially-stale ceiling_applied
    # from RedFlagResult (which may have the raw config value, not the resolved one).
    if state.scoring and state.scoring.quality_score is not None:
        return str(int(state.scoring.quality_score))
    # Fallback: parse from baked scoring_impact text
    impact = finding.scoring_impact or ""
    return impact.split(":")[-1].strip() if ":" in impact else "N/A"


def build_positive_narrative(
    finding: KeyFinding,
    idx: int,
    context: dict[str, Any],
) -> tuple[str, str]:
    """Build a company-specific narrative for a positive finding.

    Returns (title, body) backed by real state data.
    """
    state: AnalysisState = context["_state"]
    title = _extract_positive_title(finding)
    raw = finding.evidence_narrative
    name = company_name(state)

    if "audit" in raw.lower() or "clean" in raw.lower():
        sentences = pos_clean_audit(state, name)
    elif "governance" in raw.lower() or "board" in raw.lower():
        sentences = pos_strong_governance(state, name)
    elif "distress" in raw.lower() or "z-score" in raw.lower():
        sentences = pos_no_distress(state, name)
    elif "stability" in raw.lower() or "departure" in raw.lower():
        sentences = pos_stable_leadership(state, name)
    elif "short" in raw.lower():
        sentences = pos_low_short(state, name)
    elif "enforcement" in raw.lower() or "sec" in raw.lower():
        sentences = pos_no_enforcement(name)
    else:
        sentences = [f"{raw}."]

    xref = _section_cross_ref(finding)
    if xref:
        sentences.append(xref)

    return (title, " ".join(sentences))


# ---------------------------------------------------------------------------
# Title extraction helpers
# ---------------------------------------------------------------------------


def _extract_finding_title(finding: KeyFinding) -> str:
    """Extract a clean title from a negative finding."""
    raw = finding.evidence_narrative
    if "Wells Notice" in raw:
        return "SEC Enforcement Action (Active)"
    if "DOJ" in raw:
        return "DOJ Investigation"
    if "Prior Litigation" in raw:
        return "Structural Complexity & Litigation History"
    if "Guidance" in raw:
        return "Earnings Guidance Track Record"
    if "Volatility" in raw:
        return "Stock Volatility"
    if "Stock Decline" in raw:
        return "Stock Price Decline"
    if "Short" in raw:
        return "Elevated Short Interest"
    if "Restatement" in raw or "Audit" in raw:
        return "Audit & Accounting Risk Factors"
    if "Governance" in raw:
        return "Governance Concerns"
    if "Distress" in raw:
        return "Financial Distress Indicators"
    if "IPO" in raw or "SPAC" in raw or "M&A" in raw:
        return "Transaction-Related Exposure"
    # Fallback: strip score data from raw text
    clean = raw.split(":")[0].strip() if ":" in raw else raw[:60]
    clean = re.sub(r"\s*\d+/\d+\s*points?", "", clean).strip()
    return clean if clean else raw[:60]


def _extract_positive_title(finding: KeyFinding) -> str:
    """Extract a clean title from a positive finding."""
    raw = finding.evidence_narrative
    if "audit" in raw.lower() or "clean" in raw.lower():
        return "Clean Audit & Accounting History"
    if "governance" in raw.lower() or "board" in raw.lower():
        return "Strong Board Governance"
    if "distress" in raw.lower() or "z-score" in raw.lower():
        return "Sound Financial Position"
    if "stability" in raw.lower() or "departure" in raw.lower():
        return "Stable Executive Leadership"
    if "short" in raw.lower():
        return "Low Short Interest"
    if "enforcement" in raw.lower() or "sec" in raw.lower():
        return "Clean Regulatory Record"
    return raw[:60]


# ---------------------------------------------------------------------------
# String / cross-ref helpers
# ---------------------------------------------------------------------------


def _clean_origin(origin: str) -> str:
    """Clean up a section_origin string for narrative use."""
    for prefix in [
        "SEC enforcement stage: ",
        "DOJ investigation signal: ",
        "Signal-driven scoring: ",
    ]:
        if origin.startswith(prefix):
            origin = origin[len(prefix):]
    origin = re.sub(
        r"\d+ signals?,? ?coverage=\d+%[;]?\s*", "", origin,
    ).strip()
    return origin


_SECTION_REFS: dict[str, str] = {
    "SECT3": "(see Financial Health)",
    "SECT4": "(see Market & Trading)",
    "SECT5": "(see Governance)",
    "SECT6": "(see Litigation)",
    "SECT7": "(see Scoring)",
}

_KEYWORD_SECTION_MAP: list[tuple[list[str], str]] = [
    (
        ["litigation", "enforcement", "sec ", "doj", "wells notice",
         "regulatory", "sca ", "class action"],
        "(see Litigation)",
    ),
    (
        ["financial", "distress", "z-score", "revenue", "audit",
         "restatement", "going concern", "leverage"],
        "(see Financial Health)",
    ),
    (
        ["governance", "board", "independence", "departure",
         "c-suite", "compensation"],
        "(see Governance)",
    ),
    (
        ["stock", "volatility", "trading", "short interest",
         "guidance", "market cap"],
        "(see Market & Trading)",
    ),
]


def _section_cross_ref(finding: KeyFinding) -> str:
    """Generate a cross-section reference for a finding."""
    origin = finding.section_origin or ""
    for code, ref in _SECTION_REFS.items():
        if code in origin.upper():
            return ref
    raw_lower = finding.evidence_narrative.lower()
    combined = f"{raw_lower} {origin.lower()}"
    for keywords, ref in _KEYWORD_SECTION_MAP:
        for kw in keywords:
            if kw in combined:
                return ref
    return ""


__all__ = [
    "build_negative_narrative",
    "build_positive_narrative",
]
