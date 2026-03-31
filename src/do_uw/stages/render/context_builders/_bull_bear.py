"""Bull/bear case extraction and confidence verb calibration (NARR-02, NARR-03).

Provides CONFIDENCE_VERBS mapping, calibrate_verb(), calibrate_narrative_text(),
derive_section_confidence(), and extract_bull_bear_cases().
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Pattern to detect raw threshold evidence text that should never appear in output
_RAW_THRESHOLD_RE = re.compile(
    r"(?:Key evidence|Key risk indicators):\s*Value\s+[\d.]+\s+(?:exceeds|below)\s+(?:red|yellow)\s+threshold",
    re.IGNORECASE,
)


def _clean_bear_text(text: str) -> str:
    """Strip raw threshold data from bear case text, keeping only the claim sentence."""
    if not text:
        return text
    match = _RAW_THRESHOLD_RE.search(text)
    if match:
        # Truncate just before the "Key evidence/risk indicators:" part
        cut = match.start()
        # Find the sentence boundary before the raw data
        prefix = text[:cut].rstrip()
        if prefix.endswith("."):
            return prefix
        # Find last period before the raw data
        last_dot = prefix.rfind(".")
        if last_dot > 10:
            return prefix[:last_dot + 1]
        return prefix + "."
    return text

# Confidence Verb Mapping (NARR-03)

CONFIDENCE_VERBS: dict[str, str] = {
    "HIGH": "confirms",
    "MEDIUM": "indicates",
    "LOW": "suggests",
    "INFERENCE": "pattern may indicate",
}

_GENERIC_VERBS_PATTERN = re.compile(
    r"(?<=\b)(shows|has|is|indicates|presents|reveals|demonstrates)\b",
    re.IGNORECASE,
)


def calibrate_verb(confidence: str) -> str:
    """Return confidence-calibrated verb. Defaults to 'suggests' for unknown tiers."""
    return CONFIDENCE_VERBS.get(confidence.upper(), "suggests")


def calibrate_narrative_text(text: str, confidence: str) -> str:
    """Replace generic assertion verbs with confidence-calibrated verb per sentence."""
    if not text:
        return text
    verb = calibrate_verb(confidence)
    sentences = text.split(". ")
    calibrated: list[str] = []
    for sentence in sentences:
        calibrated.append(
            _GENERIC_VERBS_PATTERN.sub(verb, sentence, count=1)
        )
    return ". ".join(calibrated)


def derive_section_confidence(state: AnalysisState, section_id: str) -> str:
    """Determine dominant confidence tier for a section from signal_results."""
    counts: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    if state.analysis and state.analysis.signal_results:
        for key, result in state.analysis.signal_results.items():
            if not isinstance(result, dict):
                continue
            sig_section = result.get("section", "")
            if sig_section != section_id:
                continue
            conf = str(result.get("confidence", "MEDIUM")).upper()
            if conf in counts:
                counts[conf] += 1

    if not any(counts.values()):
        return "MEDIUM"

    return max(counts, key=lambda k: counts[k])


# ---------------------------------------------------------------------------
# Bull/Bear Case Extraction (NARR-02)
# ---------------------------------------------------------------------------

_MAX_ITEMS = 5


def _build_bull_items_from_positives(state: AnalysisState) -> list[dict[str, str]]:
    """Extract bull case items from executive summary positive findings."""
    items: list[dict[str, str]] = []
    if not state.executive_summary or not state.executive_summary.key_findings:
        return items
    for finding in state.executive_summary.key_findings.positives[:_MAX_ITEMS]:
        items.append({
            "text": finding.evidence_narrative,
            "source": finding.section_origin,
            "severity": "",
        })
    return items


def _build_bear_items_from_negatives(state: AnalysisState) -> list[dict[str, str]]:
    """Extract bear case items from executive summary negative findings."""
    items: list[dict[str, str]] = []
    if not state.executive_summary or not state.executive_summary.key_findings:
        return items
    for finding in state.executive_summary.key_findings.negatives[:_MAX_ITEMS]:
        # Combine evidence with section_origin for context-rich text
        text = finding.evidence_narrative
        origin = finding.section_origin
        if origin and origin not in text:
            text = f"{text} ({origin})"
        items.append({
            "text": text,
            "source": finding.scoring_impact.split(":")[0].strip() if finding.scoring_impact else "",
            "severity": "HIGH" if "critical" in finding.scoring_impact.lower() else "MEDIUM",
        })
    return items


def _build_bear_items_from_peril(state: AnalysisState) -> list[dict[str, str]]:
    """Extract bear case items from peril map bear cases."""
    items: list[dict[str, str]] = []
    if not state.analysis or not state.analysis.peril_map:
        return items
    peril = state.analysis.peril_map
    bear_cases = peril.get("bear_cases", [])
    for bc in bear_cases[:_MAX_ITEMS]:
        if not isinstance(bc, dict):
            continue
        raw_text = bc.get("committee_summary", bc.get("theory", ""))
        text = _clean_bear_text(raw_text)
        # Enrich with evidence chain signal names for specificity
        chain = bc.get("evidence_chain", [])
        if chain and state.analysis and state.analysis.signal_results:
            sr = state.analysis.signal_results
            signal_names: list[str] = []
            for e in chain[:3]:
                if not isinstance(e, dict):
                    continue
                sid = e.get("signal_id", "")
                # Look up human-readable signal_name from signal_results
                sig_data = sr.get(sid, {})
                name = sig_data.get("signal_name", "") if isinstance(sig_data, dict) else ""
                if name:
                    signal_names.append(name)
            if signal_names:
                text = f"{text} Key indicators: {', '.join(signal_names)}."
        items.append({
            "text": text,
            "source": bc.get("plaintiff_type", ""),
            "severity": bc.get("severity_estimate", "MEDIUM"),
        })
    return items




def _build_scoring_bull(state: AnalysisState) -> list[dict[str, str]]:
    """Extract bull items for scoring from favorable signals and defenses.

    Mines signal_results for specific favorable metrics (CLEAR signals with
    meaningful values) rather than generic density labels.
    """
    items: list[dict[str, str]] = []
    # Defense assessments from bear cases
    if state.analysis and state.analysis.peril_map:
        for bc in state.analysis.peril_map.get("bear_cases", []):
            if isinstance(bc, dict) and bc.get("defense_assessment"):
                items.append({
                    "text": bc["defense_assessment"],
                    "source": "Peril Assessment",
                    "severity": "",
                })
    # Mine signal_results for specific favorable metrics in clean sections
    if state.analysis and state.analysis.section_densities:
        sr = state.analysis.signal_results if state.analysis.signal_results else {}
        for sid, density in state.analysis.section_densities.items():
            level = str(density.level) if hasattr(density, "level") else "CLEAN"
            if level not in ("CLEAN", "FAVORABLE"):
                continue
            # Find specific favorable signals for this section
            specifics = _extract_favorable_signals(sr, sid)
            if specifics:
                for text, source in specifics[:2]:
                    items.append({"text": text, "source": source, "severity": ""})
            else:
                # Fallback: still note clean section but with section name
                name = _SECTION_DISPLAY_NAMES.get(sid, sid.replace("_", " ").title())
                items.append({
                    "text": f"{name}: no material concerns identified",
                    "source": "Signal Analysis",
                    "severity": "",
                })
    return items[:_MAX_ITEMS]


def _build_scoring_bear(state: AnalysisState) -> list[dict[str, str]]:
    """Extract bear items for scoring from high-risk signals and density concerns.

    Uses SectionDensity.concerns and critical_evidence for specific items,
    then enriches with TRIGGERED signal values from signal_results.
    """
    items: list[dict[str, str]] = []
    if state.analysis and state.analysis.section_densities:
        sr = state.analysis.signal_results if state.analysis.signal_results else {}
        for sid, density in state.analysis.section_densities.items():
            level = str(density.level) if hasattr(density, "level") else "CLEAN"
            if level not in ("CRITICAL", "ELEVATED"):
                continue
            sev = "HIGH" if level == "CRITICAL" else "MEDIUM"
            name = _SECTION_DISPLAY_NAMES.get(sid, sid.replace("_", " ").title())
            # First: use specific concerns/critical_evidence from SectionDensity
            specifics_added = False
            concerns = density.concerns if hasattr(density, "concerns") else []
            crit_evidence = (
                density.critical_evidence
                if hasattr(density, "critical_evidence")
                else []
            )
            for evidence_text in (crit_evidence + concerns)[:2]:
                items.append({
                    "text": f"{name}: {evidence_text}",
                    "source": "Section Assessment",
                    "severity": sev,
                })
                specifics_added = True
            # Second: enrich with triggered signal specifics
            triggered = _extract_triggered_signals(sr, sid)
            for text, source in triggered[:2 if not specifics_added else 1]:
                items.append({"text": text, "source": source, "severity": sev})
                specifics_added = True
            # Fallback only if nothing specific found
            if not specifics_added:
                items.append({
                    "text": f"{name}: {level.lower()} risk level — review recommended",
                    "source": "Density Analysis",
                    "severity": sev,
                })
    # Peril bear cases
    items.extend(_build_bear_items_from_peril(state))
    return items[:_MAX_ITEMS]


# ---------------------------------------------------------------------------
# Signal mining helpers for data-driven bull/bear items
# ---------------------------------------------------------------------------

# Section density key -> display name
_SECTION_DISPLAY_NAMES: dict[str, str] = {
    "governance": "Governance",
    "litigation": "Litigation",
    "financial": "Financial Health",
    "market": "Market Activity",
    "company": "Company Profile",
    "executive_summary": "Executive Summary",
    "scoring": "Scoring",
    "ai_risk": "AI & Technology",
}

# Density key -> signal ID prefixes for mining signal_results
_SECTION_SIGNAL_PREFIXES: dict[str, list[str]] = {
    "governance": ["GOV.", "EXEC."],
    "litigation": ["LIT."],
    "financial": ["FIN.", "NLP."],
    "market": ["STOCK.", "FWRD."],
    "company": ["BIZ."],
}

# Favorable CLEAR signal templates: signal_id -> (text_template, source_label)
# fmt: off
_FAVORABLE_SIGNAL_TEMPLATES: dict[str, tuple[str, str]] = {
    "GOV.BOARD.independence":         ("Board independence at {value}%", "Board Structure"),
    "GOV.BOARD.attendance":           ("Board attendance at {value}%", "Board Structure"),
    "GOV.PAY.say_on_pay":            ("Say-on-pay approval at {value}%", "Proxy Filing"),
    "GOV.ACTIVIST.13d_filings":      ("No activist 13D filings", "SEC Filings"),
    "EXEC.TENURE.ceo_new":           ("CEO tenure {value} years — management stability", "Leadership"),
    "EXEC.TENURE.cfo_new":           ("CFO tenure {value} years — financial leadership stability", "Leadership"),
    "EXEC.PRIOR_LIT.ceo_cfo":       ("No prior litigation involving CEO or CFO", "Background"),
    "LIT.SCA.active":                ("No active securities class actions", "Litigation"),
    "LIT.SCA.derivative":            ("No derivative litigation pending", "Litigation"),
    "LIT.SCA.settle_amount":         ("No prior SCA settlements", "Litigation"),
    "LIT.REG.civil_penalty":         ("No civil penalties on record", "Regulatory"),
    "LIT.DEFENSE.contingent_liabilities": ("No contingent liability disclosures (ASC 450)", "10-K Filing"),
    "FIN.ACCT.restatement":          ("No restatement history", "SEC Filings"),
    "FIN.ACCT.material_weakness":    ("No material weaknesses in internal controls", "Audit"),
    "FIN.ACCT.internal_controls":    ("Clean internal controls assessment", "SOX Compliance"),
    "FIN.ACCT.quality_indicators":   ("Altman Z-Score {value:.2f} — safe zone", "Distress Model"),
    "FIN.ACCT.earnings_manipulation": ("Beneish M-Score {value:.2f} — no manipulation indicated", "Forensic Model"),
    "FIN.DEBT.coverage":             ("Debt service coverage ratio {value:.1f}x", "Financial Analysis"),
    "FWRD.WARN.zone_of_insolvency":  ("Altman Z-Score {value:.2f} — above insolvency threshold", "Distress Model"),
    "STOCK.SHORT.position":          ("Short interest at {value:.1f}% — below concern threshold", "Market Data"),
    "STOCK.LIT.existing_action":     ("No existing securities actions", "Litigation Monitor"),
    "BIZ.STRUCT.related_party":      ("No related-party transaction concerns", "10-K Analysis"),
}

# Triggered risk signal templates: signal_id -> (text_template, source_label)
_TRIGGERED_SIGNAL_TEMPLATES: dict[str, tuple[str, str]] = {
    "EXEC.INSIDER.ceo_net_selling":  ("CEO net selling ratio {value}% — elevated insider disposition", "Insider Transactions"),
    "EXEC.INSIDER.cfo_net_selling":  ("CFO net selling ratio {value}% — elevated insider disposition", "Insider Transactions"),
    "EXEC.AGGREGATE.board_risk":     ("Board aggregate risk score {value:.1f} — above threshold", "Board Assessment"),
    "FIN.LIQ.position":             ("Current ratio {value:.2f} — below liquidity threshold", "Financial Analysis"),
    "FIN.ACCT.quality_indicators":   ("Altman Z-Score {value:.2f} — distress zone", "Distress Model"),
    "FIN.ACCT.earnings_manipulation": ("Beneish M-Score {value:.2f} — manipulation risk", "Forensic Model"),
    "BIZ.DEPEND.macro_sensitivity":  ("Supply chain complexity score {value:.0f} — elevated dependency risk", "Business Analysis"),
    "BIZ.DEPEND.distribution":       ("Product concentration score {value:.0f} — elevated concentration", "Business Analysis"),
    "BIZ.CLASS.litigation_history":  ("Prior litigation history flagged — elevated claim recurrence risk", "Litigation History"),
    "STOCK.PRICE.recent_drop_alert": ("Recent stock decline {value:.1f}% — event-driven claim exposure", "Market Data"),
    "GOV.INSIDER.cluster_sales":     ("{value:.0f} insider cluster selling event(s) detected", "Insider Transactions"),
    "FWRD.WARN.zone_of_insolvency":  ("Z-Score {value:.2f} — approaching insolvency zone", "Distress Model"),
}
# fmt: on


def _extract_favorable_signals(
    signal_results: dict[str, Any], density_section: str
) -> list[tuple[str, str]]:
    """Mine signal_results for specific favorable data points in a clean section.

    Returns list of (text, source) tuples with concrete metrics cited.
    """
    prefixes = _SECTION_SIGNAL_PREFIXES.get(density_section, [])
    if not prefixes:
        return []

    found: list[tuple[str, str]] = []
    for signal_id, sig_data in signal_results.items():
        if not isinstance(sig_data, dict):
            continue
        if sig_data.get("status") != "CLEAR":
            continue
        if not any(signal_id.startswith(p) for p in prefixes):
            continue
        template_entry = _FAVORABLE_SIGNAL_TEMPLATES.get(signal_id)
        if not template_entry:
            continue
        template, source = template_entry
        value = sig_data.get("value")
        try:
            if value is not None and "{value" in template:
                text = template.format(value=value)
            elif value is None or value == 0 or value is False:
                # For zero/false values, the template should read as-is (no risk)
                text = template.replace("{value}", "0")
            else:
                text = template.format(value=value)
        except (ValueError, KeyError, TypeError):
            text = sig_data.get("signal_name", signal_id)
        found.append((text, source))
    return found


def _extract_triggered_signals(
    signal_results: dict[str, Any], density_section: str
) -> list[tuple[str, str]]:
    """Mine signal_results for specific triggered risk data points in a section.

    Returns list of (text, source) tuples with concrete metrics cited.
    """
    prefixes = _SECTION_SIGNAL_PREFIXES.get(density_section, [])
    if not prefixes:
        return []

    found: list[tuple[str, str]] = []
    for signal_id, sig_data in signal_results.items():
        if not isinstance(sig_data, dict):
            continue
        if sig_data.get("status") != "TRIGGERED":
            continue
        if not any(signal_id.startswith(p) for p in prefixes):
            continue
        template_entry = _TRIGGERED_SIGNAL_TEMPLATES.get(signal_id)
        value = sig_data.get("value")
        if template_entry:
            template, source = template_entry
            try:
                if value is not None and "{value" in template:
                    text = template.format(value=value)
                else:
                    text = template.replace("{value}", str(value) if value else "N/A")
            except (ValueError, KeyError, TypeError):
                text = sig_data.get("signal_name", signal_id)
        else:
            # Generic but still data-aware fallback for unmapped triggered signals
            sig_name = sig_data.get("signal_name", signal_id)
            threshold = sig_data.get("threshold_level", "")
            if value is not None and threshold:
                text = f"{sig_name}: value {value} ({threshold} threshold)"
            elif value is not None:
                text = f"{sig_name}: {value}"
            else:
                text = f"{sig_name} triggered"
            source = "Signal Analysis"
        found.append((text, source))
    return found


def extract_bull_bear_cases(state: AnalysisState) -> dict[str, dict[str, Any]]:
    """Extract bull/bear framing data for executive summary and scoring."""
    result: dict[str, dict[str, Any]] = {}

    # Executive Summary bull/bear
    exec_bull = _build_bull_items_from_positives(state)
    exec_bear = _build_bear_items_from_negatives(state)
    # Supplement bear with peril bear cases if needed
    if len(exec_bear) < _MAX_ITEMS:
        peril_bears = _build_bear_items_from_peril(state)
        exec_bear.extend(peril_bears[:_MAX_ITEMS - len(exec_bear)])

    if exec_bull or exec_bear:
        result["executive_summary"] = {
            "bull_case": {"title": "Bull Case", "entries": exec_bull} if exec_bull else None,
            "bear_case": {"title": "Bear Case", "entries": exec_bear} if exec_bear else None,
            "confidence_tier": derive_section_confidence(state, "executive_summary"),
        }

    # Scoring bull/bear
    scoring_bull = _build_scoring_bull(state)
    scoring_bear = _build_scoring_bear(state)

    if scoring_bull or scoring_bear:
        result["scoring"] = {
            "bull_case": {"title": "Bull Case", "entries": scoring_bull} if scoring_bull else None,
            "bear_case": {"title": "Bear Case", "entries": scoring_bear} if scoring_bear else None,
            "confidence_tier": derive_section_confidence(state, "scoring"),
        }

    return result
