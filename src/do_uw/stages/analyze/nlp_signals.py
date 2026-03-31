"""NLP signal detection for D&O underwriting analysis.

Detects readability changes (Fog Index), MD&A tone shifts, risk factor
evolution, and whistleblower language by comparing current and prior year
10-K text. Uses textstat for readability metrics.

Graceful degradation: when prior-year filing is unavailable, reports
current-year-only metrics with INFO classification.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import textstat

from do_uw.models.state import AnalysisState, ExtractedData

logger = logging.getLogger(__name__)

_NEGATIVE_KEYWORDS = [
    "decline", "loss", "adverse", "uncertain", "risk", "challenge",
    "impairment", "restructuring", "litigation", "investigation", "default",
    "deteriorat", "downturn", "layoff", "termination", "unfavorable",
    "weakness", "deficit", "shortfall", "volatility",
]

_POSITIVE_KEYWORDS = [
    "growth", "improve", "strong", "exceed", "record", "innovation",
    "opportunity", "expand", "momentum", "robust", "favorable",
    "outperform", "milestone", "achievement", "accelerat",
]

_WHISTLEBLOWER_KEYWORDS = [
    "whistleblower", "qui tam", "false claims act", "relator", "retaliation",
    "hotline complaint", "internal investigation triggered by",
    "whistleblowing", "dodd-frank whistleblower", "sec whistleblower",
]

# Readability change thresholds
_FOG_INCREASE_THRESHOLD = 2.0  # points increase = INCREASING_COMPLEXITY
_FOG_DECREASE_THRESHOLD = -2.0  # points decrease = IMPROVING_CLARITY

# Tone shift threshold
_TONE_SHIFT_THRESHOLD = 0.05  # 5 percentage point shift


def compute_readability_change(
    current_text: str,
    prior_text: str | None,
) -> dict[str, Any]:
    """Compute readability metrics and year-over-year change.

    Uses Gunning Fog Index and Flesch Reading Ease. Increasing Fog
    (harder to read) is adverse -- research shows companies obfuscate
    before bad news.

    Returns dict with current/prior Fog, change, and classification.
    """
    if not current_text or len(current_text) < 100:
        return {
            "current_fog": None,
            "prior_fog": None,
            "fog_change": None,
            "current_flesch": None,
            "prior_flesch": None,
            "classification": "INSUFFICIENT_DATA",
            "evidence": "Current text too short for readability analysis",
        }

    current_fog = textstat.gunning_fog(current_text)
    current_flesch = textstat.flesch_reading_ease(current_text)

    if prior_text is None or len(prior_text) < 100:
        return {
            "current_fog": round(current_fog, 2),
            "prior_fog": None,
            "fog_change": None,
            "current_flesch": round(current_flesch, 2),
            "prior_flesch": None,
            "classification": "CURRENT_ONLY",
            "evidence": f"Current Fog Index: {current_fog:.1f} (prior year unavailable)",
        }

    prior_fog = textstat.gunning_fog(prior_text)
    prior_flesch = textstat.flesch_reading_ease(prior_text)
    fog_change = current_fog - prior_fog

    if fog_change >= _FOG_INCREASE_THRESHOLD:
        classification = "INCREASING_COMPLEXITY"
        evidence = (
            f"Fog Index increased {fog_change:+.1f} points "
            f"({prior_fog:.1f} -> {current_fog:.1f}). "
            "Increased complexity may indicate obfuscation."
        )
    elif fog_change <= _FOG_DECREASE_THRESHOLD:
        classification = "IMPROVING_CLARITY"
        evidence = (
            f"Fog Index decreased {fog_change:+.1f} points "
            f"({prior_fog:.1f} -> {current_fog:.1f}). "
            "Improved readability."
        )
    else:
        classification = "STABLE"
        evidence = (
            f"Fog Index change: {fog_change:+.1f} points "
            f"({prior_fog:.1f} -> {current_fog:.1f}). Stable readability."
        )

    return {
        "current_fog": round(current_fog, 2),
        "prior_fog": round(prior_fog, 2),
        "fog_change": round(fog_change, 2),
        "current_flesch": round(current_flesch, 2),
        "prior_flesch": round(prior_flesch, 2),
        "classification": classification,
        "evidence": evidence,
    }


def _count_keywords(text: str, keywords: list[str]) -> int:
    """Count occurrences of keywords in text (case-insensitive, word-boundary aware)."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        # Use simple substring matching for multi-word keywords
        count += len(re.findall(re.escape(kw), text_lower))
    return count


def detect_tone_shift(
    current_mda: str,
    prior_mda: str | None,
) -> dict[str, Any]:
    """Detect tone shift between current and prior year MD&A.

    Simple keyword-based tone analysis using negative/positive keyword
    ratios. Increasing negative tone is adverse.

    Returns dict with current/prior ratios, shift, and classification.
    """
    if not current_mda or len(current_mda) < 100:
        return {
            "current_negative_ratio": None,
            "prior_negative_ratio": None,
            "shift": None,
            "classification": "INSUFFICIENT_DATA",
            "evidence": "Current MD&A text too short for tone analysis",
        }

    current_neg = _count_keywords(current_mda, _NEGATIVE_KEYWORDS)
    current_pos = _count_keywords(current_mda, _POSITIVE_KEYWORDS)
    current_total = current_neg + current_pos
    current_ratio = current_neg / current_total if current_total > 0 else 0.0

    if prior_mda is None or len(prior_mda) < 100:
        return {
            "current_negative_ratio": round(current_ratio, 4),
            "prior_negative_ratio": None,
            "shift": None,
            "classification": "CURRENT_ONLY",
            "evidence": (
                f"Current negative tone ratio: {current_ratio:.1%} "
                f"({current_neg} neg / {current_total} total). Prior year unavailable."
            ),
        }

    prior_neg = _count_keywords(prior_mda, _NEGATIVE_KEYWORDS)
    prior_pos = _count_keywords(prior_mda, _POSITIVE_KEYWORDS)
    prior_total = prior_neg + prior_pos
    prior_ratio = prior_neg / prior_total if prior_total > 0 else 0.0
    shift = current_ratio - prior_ratio

    if shift >= _TONE_SHIFT_THRESHOLD:
        classification = "MORE_NEGATIVE"
        evidence = (
            f"Negative tone increased {shift:+.1%} "
            f"({prior_ratio:.1%} -> {current_ratio:.1%}). "
            "MD&A tone has shifted toward more negative language."
        )
    elif shift <= -_TONE_SHIFT_THRESHOLD:
        classification = "MORE_POSITIVE"
        evidence = (
            f"Negative tone decreased {shift:+.1%} "
            f"({prior_ratio:.1%} -> {current_ratio:.1%}). "
            "MD&A tone has improved."
        )
    else:
        classification = "STABLE"
        evidence = (
            f"Tone shift: {shift:+.1%} "
            f"({prior_ratio:.1%} -> {current_ratio:.1%}). Stable tone."
        )

    return {
        "current_negative_ratio": round(current_ratio, 4),
        "prior_negative_ratio": round(prior_ratio, 4),
        "shift": round(shift, 4),
        "classification": classification,
        "evidence": evidence,
    }


def _normalize_risk_factor(text: str) -> str:
    """Normalize a risk factor title for fuzzy comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())[:80]


def track_risk_factor_evolution(
    current_risk_factors: list[str],
    prior_risk_factors: list[str] | None,
) -> dict[str, Any]:
    """Compare risk factor sections between years.

    Identifies new and removed risk factors using fuzzy matching
    on the first 80 characters of normalized text.

    Returns dict with counts, new/removed factors, and evidence.
    """
    current_count = len(current_risk_factors)

    if prior_risk_factors is None:
        return {
            "current_count": current_count,
            "prior_count": None,
            "new_factors": [],
            "removed_factors": [],
            "net_change": None,
            "evidence": (
                f"Current year has {current_count} risk factors. "
                "Prior year unavailable for comparison."
            ),
        }

    prior_count = len(prior_risk_factors)

    # Normalize for fuzzy matching
    current_normalized = {_normalize_risk_factor(f) for f in current_risk_factors if f}
    prior_normalized = {_normalize_risk_factor(f) for f in prior_risk_factors if f}

    # New = in current but not in prior
    new_normalized = current_normalized - prior_normalized
    # Removed = in prior but not in current
    removed_normalized = prior_normalized - current_normalized

    # Map back to original text for display (take first match)
    new_factors: list[str] = []
    for nf in new_normalized:
        for orig in current_risk_factors:
            if _normalize_risk_factor(orig) == nf:
                new_factors.append(orig[:150])
                break

    removed_factors: list[str] = []
    for rf in removed_normalized:
        for orig in prior_risk_factors:
            if _normalize_risk_factor(orig) == rf:
                removed_factors.append(orig[:150])
                break

    net_change = current_count - prior_count

    evidence_parts = [f"Risk factors: {prior_count} -> {current_count} (net {net_change:+d})"]
    if new_factors:
        evidence_parts.append(f"{len(new_factors)} new risk factor(s) added")
    if removed_factors:
        evidence_parts.append(f"{len(removed_factors)} risk factor(s) removed")

    return {
        "current_count": current_count,
        "prior_count": prior_count,
        "new_factors": new_factors,
        "removed_factors": removed_factors,
        "net_change": net_change,
        "evidence": ". ".join(evidence_parts),
    }


def detect_whistleblower_language(text: str) -> dict[str, Any]:
    """Scan for whistleblower/qui tam language in filing text.

    Returns dict with detected flag, matches, and evidence.
    """
    if not text:
        return {
            "detected": False,
            "matches": [],
            "evidence": "No text provided for whistleblower scan",
        }

    text_lower = text.lower()
    matches: list[str] = []

    for keyword in _WHISTLEBLOWER_KEYWORDS:
        if keyword in text_lower:
            matches.append(keyword)

    if matches:
        evidence = (
            f"Whistleblower/qui tam language detected: {', '.join(matches)}. "
            "Presence of such language in filings may indicate pending or "
            "potential False Claims Act or SEC whistleblower actions."
        )
    else:
        evidence = "No whistleblower or qui tam language detected in filing text"

    return {
        "detected": len(matches) > 0,
        "matches": matches,
        "evidence": evidence,
    }


def _extract_mda_text(state: AnalysisState) -> str | None:
    """Extract current year MD&A text from acquired filing documents."""
    if state.acquired_data is None:
        return None

    filing_docs = state.acquired_data.filing_documents
    tenk_docs = filing_docs.get("10-K", [])
    if not tenk_docs:
        return None

    # Most recent 10-K
    latest = tenk_docs[0] if tenk_docs else None
    if latest is None:
        return None

    full_text = latest.get("full_text", "")
    if not full_text:
        return None

    # Try to extract Item 7 (MD&A) section
    # Look for common section headers
    item7_patterns = [
        r"item\s*7[.\s]*management.s discussion",
        r"item\s*7[.\s]*md&a",
        r"management.s discussion and analysis",
    ]

    text_lower = full_text.lower()
    start_idx = None
    for pattern in item7_patterns:
        match = re.search(pattern, text_lower)
        if match:
            start_idx = match.start()
            break

    if start_idx is None:
        return full_text[:50000]  # Fallback: use first 50k chars

    # Find end of MD&A (typically Item 7A or Item 8)
    end_patterns = [
        r"item\s*7a",
        r"item\s*8[.\s]",
        r"quantitative and qualitative disclosures about market risk",
    ]

    end_idx = len(full_text)
    for pattern in end_patterns:
        match = re.search(pattern, text_lower[start_idx + 100:])
        if match:
            end_idx = start_idx + 100 + match.start()
            break

    return full_text[start_idx:end_idx]


def _extract_risk_factor_titles(state: AnalysisState) -> list[str]:
    """Extract risk factor titles from ExtractedData."""
    if state.extracted is None:
        return []

    return [rf.title for rf in state.extracted.risk_factors if rf.title]


def _get_full_text(state: AnalysisState) -> str:
    """Get full 10-K text for whistleblower scanning."""
    if state.acquired_data is None:
        return ""

    filing_docs = state.acquired_data.filing_documents
    tenk_docs = filing_docs.get("10-K", [])
    if not tenk_docs:
        return ""

    return tenk_docs[0].get("full_text", "") if tenk_docs else ""


def analyze_nlp_signals(
    extracted: ExtractedData | None,
    prior_year_text: dict[str, str] | None = None,
    state: AnalysisState | None = None,
) -> dict[str, Any]:
    """Run all NLP signal analyses.

    Orchestrator that runs readability, tone shift, risk factor evolution,
    and whistleblower detection. If prior_year_text is None, gracefully
    returns results with "prior year unavailable" notes.

    Args:
        extracted: Current year ExtractedData
        prior_year_text: Dict with keys "mda", "risk_factors", "full_text"
            for prior year filing text. None if unavailable.
        state: Full AnalysisState (for accessing acquired_data texts)

    Returns:
        Dict with signal results for all NLP dimensions.
    """
    results: dict[str, Any] = {}

    # Get current year texts
    current_mda = ""
    current_full_text = ""
    current_risk_factor_titles: list[str] = []

    if state is not None:
        current_mda = _extract_mda_text(state) or ""
        current_full_text = _get_full_text(state)
        current_risk_factor_titles = _extract_risk_factor_titles(state)
    elif extracted is not None:
        current_risk_factor_titles = [rf.title for rf in extracted.risk_factors if rf.title]

    # Prior year texts
    prior_mda = prior_year_text.get("mda") if prior_year_text else None
    prior_risk_factors_raw = prior_year_text.get("risk_factors", "") if prior_year_text else None

    # Parse prior risk factors into list
    prior_risk_factors: list[str] | None = None
    if prior_risk_factors_raw and isinstance(prior_risk_factors_raw, str):
        prior_risk_factors = [
            line.strip()
            for line in prior_risk_factors_raw.split("\n")
            if line.strip()
        ]
    elif isinstance(prior_risk_factors_raw, list):
        prior_risk_factors = prior_risk_factors_raw

    # 1. Readability change
    results["readability"] = compute_readability_change(current_mda, prior_mda)

    # 2. Tone shift
    results["tone_shift"] = detect_tone_shift(current_mda, prior_mda)

    # 3. Risk factor evolution
    results["risk_factors"] = track_risk_factor_evolution(
        current_risk_factor_titles,
        prior_risk_factors,
    )

    # 4. Whistleblower language
    scan_text = current_full_text or current_mda
    results["whistleblower"] = detect_whistleblower_language(scan_text)

    # Summary
    signal_count = 0
    if results["readability"]["classification"] == "INCREASING_COMPLEXITY":
        signal_count += 1
    if results["tone_shift"]["classification"] == "MORE_NEGATIVE":
        signal_count += 1
    if results["risk_factors"].get("new_factors"):
        signal_count += 1
    if results["whistleblower"]["detected"]:
        signal_count += 1

    results["summary"] = {
        "total_signals": signal_count,
        "prior_year_available": prior_year_text is not None,
    }

    return results


__all__ = [
    "analyze_nlp_signals",
    "compute_readability_change",
    "detect_tone_shift",
    "detect_whistleblower_language",
    "track_risk_factor_evolution",
]
