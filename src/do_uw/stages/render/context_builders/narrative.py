"""Narrative context builders for SCR, D&O implications, and 5-layer architecture.

SCR per-section narratives, D&O-specific implications callouts, and
5-layer narrative data (verdict, thesis, evidence grid, implications,
deep context). Evaluative logic lives in narrative_evaluative.py.

Phase 119.1-02: Static _DO_IMPLICATIONS_MAP replaced with state-aware
generators in narrative_generators.py that produce company-specific
D&O commentary based on actual financial position.
"""

from __future__ import annotations

import re
import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._narrative_generators import (
    DO_IMPLICATIONS_REGISTRY,
    IMPLICATION_GENERATORS,
    gen_coverage_note,
)

logger = logging.getLogger(__name__)

# Regex to strip markdown artifacts from pre-computed narratives
_MD_HEADER_RE = re.compile(r"^#+\s+", re.MULTILINE)
_MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_NARRATIVE_TITLE_RE = re.compile(
    r"^(?:"
    r"[A-Z][A-Z0-9 &.,]+\s*[\u2014\u2013\-]+\s*"
    r"(?:D&O|Directors?\s*(?:&|and)\s*Officers?(?:\s+Liability)?)\s+"
    r"(?:UNDERWRITING\s+)?(?:NARRATIVE|THESIS)[^\n]*"
    r"|D&O\s+UNDERWRITING\s+THESIS\s*:\s*[A-Z][A-Z0-9 &.,]+(?:Inc\.|Corp\.|Ltd\.|LLC|Co\.)?\s*"
    r")$",
    re.MULTILINE | re.IGNORECASE,
)

_SECTION_NAMES: dict[str, str] = {
    "executive_summary": "Executive Summary",
    "business_profile": "Company Profile",
    "financial_health": "Financial Health",
    "governance": "Governance & Leadership",
    "litigation": "Litigation & Regulatory",
    "market_activity": "Market Activity",
    "scoring": "Scoring & Risk Assessment",
    "ai_risk": "AI & Technology Risk",
}
_TEMPLATE_KEYS: dict[str, str] = {
    "executive_summary": "executive_summary",
    "business_profile": "company",
    "financial_health": "financial",
    "governance": "governance",
    "litigation": "litigation",
    "market_activity": "market",
    "scoring": "scoring",
    "ai_risk": "ai_risk",
}


def _strip_md(text: str) -> str:
    """Strip markdown headers, bold markers, and title lines from narrative text."""
    text = _MD_HEADER_RE.sub("", text)
    text = _MD_BOLD_RE.sub(r"\1", text)
    text = _NARRATIVE_TITLE_RE.sub("", text)
    return text.strip()


def _derive_section_density(state: AnalysisState, section_id: str) -> str:
    """Get density level for a section from analysis state."""
    if not state.analysis or not state.analysis.section_densities:
        return "CLEAN"
    density = state.analysis.section_densities.get(section_id)
    if density is not None:
        if isinstance(density, dict):
            return str(density.get("level", "CLEAN"))
        return str(density.level)
    return "CLEAN"


def _get_narrative_text(state: AnalysisState, section_id: str) -> str:
    """Extract pre-computed narrative text for a section."""
    if not state.analysis or not state.analysis.pre_computed_narratives:
        return ""
    narr = state.analysis.pre_computed_narratives
    tpl_key = _TEMPLATE_KEYS.get(section_id, section_id)
    return getattr(narr, tpl_key, "") or ""


def _get_elevated_signal_names(state: AnalysisState, section_id: str) -> list[str]:
    """Return display names of TRIGGERED/ELEVATED signals for a section."""
    names: list[str] = []
    if not (state.analysis and state.analysis.signal_results):
        return names
    from do_uw.stages.render.html_signals import _group_signals_by_section
    grouped = _group_signals_by_section(state.analysis.signal_results, {})
    tpl_key = _TEMPLATE_KEYS.get(section_id, section_id)
    for sig in grouped.get(tpl_key, []):
        if isinstance(sig, dict) and sig.get("status") in ("TRIGGERED", "ELEVATED"):
            name = sig.get("signal_name", sig.get("signal_id", ""))
            if name:
                names.append(name)
    return names


def _build_scr_for_section(
    state: AnalysisState, section_id: str,
) -> dict[str, str] | None:
    """Build SCR narrative for a single section."""
    density = _derive_section_density(state, section_id)
    narrative = _get_narrative_text(state, section_id)
    section_name = _SECTION_NAMES.get(
        section_id, section_id.replace("_", " ").title(),
    )
    if density not in ("CRITICAL", "ELEVATED"):
        return None
    situation = (
        f"{section_name} assessment based on SEC filings, market data, "
        f"and proprietary signal evaluation."
    )
    signal_names = _get_elevated_signal_names(state, section_id)
    if density == "CRITICAL":
        if signal_names:
            triggers = ", ".join(signal_names[:4])
            complication = (
                f"Critical risk in {section_name}: {triggers}. "
                f"Requires immediate underwriting attention."
            )
        else:
            complication = (
                f"Critical risk indicators identified in "
                f"{section_name.lower()} requiring immediate "
                f"underwriting attention."
            )
    elif signal_names:
        indicators = ", ".join(signal_names[:3])
        complication = (
            f"{section_name} shows elevated indicators: "
            f"{indicators} flagged. Review recommended."
        )
    else:
        complication = (
            f"Elevated concern signals detected in "
            f"{section_name.lower()} that may affect D&O risk profile."
        )
    resolution = _build_resolution(narrative, section_name)
    return {
        "situation": situation,
        "complication": complication,
        "resolution": resolution,
    }


def _build_resolution(narrative: str, section_name: str) -> str:
    """Build resolution text from narrative or default."""
    if not narrative:
        return (
            f"No material concerns identified in {section_name.lower()} "
            f"assessment. Standard underwriting parameters apply."
        )
    clean = _strip_md(narrative)
    lines = [ln.strip() for ln in clean.split("\n") if ln.strip()]
    clean = " ".join(
        ln for ln in lines
        if not _NARRATIVE_TITLE_RE.match(ln)
        and not ln.upper().startswith("TIER:")
        and not ln.startswith("Tier:")
        and not ln.startswith("Action:")
    )
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean)
        if s.strip()
    ]
    parts = sentences[:2]
    if parts:
        joined = " ".join(parts)
        resolution = (
            joined if joined.rstrip().endswith((".", "!", "?"))
            else joined + "."
        )
    else:
        return (
            f"Analysis of {section_name.lower()} is within "
            f"normal parameters."
        )
    if len(resolution) > 300:
        cut = resolution[:300].rfind(". ")
        if cut > 100:
            return resolution[:cut + 1]
    return resolution


def extract_scr_narratives(
    state: AnalysisState,
) -> dict[str, dict[str, str]]:
    """Build SCR narratives for all sections."""
    result: dict[str, dict[str, str]] = {}
    for section_id in _SECTION_NAMES:
        scr = _build_scr_for_section(state, section_id)
        if scr:
            result[_TEMPLATE_KEYS.get(section_id, section_id)] = scr
    return result


def extract_do_implications(
    state: AnalysisState,
) -> dict[str, dict[str, Any]]:
    """Build D&O implications using state-aware generators."""
    from do_uw.stages.render.context_builders.narrative_evaluative import (
        check_implication_condition,
    )
    result: dict[str, dict[str, Any]] = {}
    for section_id, conditions in DO_IMPLICATIONS_REGISTRY.items():
        items: list[dict[str, str]] = []
        for cond_key, severity in conditions:
            if check_implication_condition(state, section_id, cond_key):
                gen = IMPLICATION_GENERATORS.get(cond_key)
                if gen:
                    text = gen(state)
                    if text:
                        items.append({"text": text, "severity": severity})
        if items:
            tpl_key = _TEMPLATE_KEYS.get(section_id, section_id)
            result[tpl_key] = {
                "items": items,
                "coverage_note": gen_coverage_note(state, section_id),
            }
    return result


def build_section_narrative(
    state: AnalysisState, section_id: str,
) -> dict[str, Any] | None:
    """Build 5-layer narrative for a single section (NARR-01)."""
    from do_uw.stages.render.context_builders.narrative_evaluative import (
        build_thesis, collect_deep_context, collect_evidence,
        determine_verdict, check_implication_condition,
    )
    try:
        from do_uw.brain.narratives import load_narrative_config
        config = load_narrative_config(section_id)
    except (FileNotFoundError, ImportError):
        return None
    evidence = collect_evidence(state, section_id)
    if not evidence:
        return None
    impl_texts: list[str] = []
    for ck, _sev in DO_IMPLICATIONS_REGISTRY.get(section_id, []):
        if check_implication_condition(state, section_id, ck):
            gen = IMPLICATION_GENERATORS.get(ck)
            if gen:
                text = gen(state)
                if text:
                    impl_texts.append(text)
    return {
        "verdict": determine_verdict(state, section_id, config),
        "thesis": build_thesis(state, section_id, config),
        "evidence_items": evidence,
        "implications": (
            " ".join(impl_texts[:3])
            if impl_texts
            else gen_coverage_note(state, section_id)
        ),
        "deep_context": collect_deep_context(state, section_id),
    }


def extract_section_narratives(
    state: AnalysisState,
) -> dict[str, dict[str, Any]]:
    """Build 5-layer narratives for all 12 sections (NARR-01)."""
    from do_uw.brain.narratives import SECTION_IDS
    result: dict[str, dict[str, Any]] = {}
    for sid in SECTION_IDS:
        narr = build_section_narrative(state, sid)
        if narr:
            result[_TEMPLATE_KEYS.get(sid, sid)] = narr
    return result


__all__ = [
    "build_section_narrative",
    "extract_do_implications",
    "extract_scr_narratives",
    "extract_section_narratives",
]
