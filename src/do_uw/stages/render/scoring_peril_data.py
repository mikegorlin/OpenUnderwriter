"""Extract peril-organized scoring data from brain framework + pipeline results.

Loads brain perils and causal chains from DuckDB, cross-references with
pipeline signal_results, and produces structured peril-organized scoring
data for renderers.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Risk level ordering for comparison (higher = more severe)
_RISK_ORDER = {"LOW": 0, "MODERATE": 1, "ELEVATED": 2, "HIGH": 3}


def _risk_order(level: str) -> int:
    """Return numeric risk order for sorting."""
    return _RISK_ORDER.get(level, 0)


def _check_fired(signal_id: str, signal_results: dict[str, Any]) -> bool:
    """Check if a specific check fired (TRIGGERED or red/yellow threshold).

    Handles both SignalResult Pydantic objects (runtime) and serialized
    dicts (from state.json).
    """
    result = signal_results.get(signal_id)
    if result is None:
        return False

    # Handle dict (serialized) form
    if isinstance(result, dict):
        status = str(result.get("status", "")).upper()
        if status in ("TRIGGERED", "FIRED", "FLAGGED"):
            return True
        threshold_level = str(result.get("threshold_level", "")).lower()
        if threshold_level in ("red", "yellow"):
            return True
        return False

    # Handle Pydantic SignalResult object (runtime)
    status = str(getattr(result, "status", "")).upper()
    if status in ("TRIGGERED", "FIRED", "FLAGGED"):
        return True
    threshold_level = str(getattr(result, "threshold_level", "")).lower()
    if threshold_level in ("red", "yellow"):
        return True
    return False


def _get_check_evidence(signal_id: str, signal_results: dict[str, Any]) -> str:
    """Extract evidence string from a check result."""
    result = signal_results.get(signal_id)
    if result is None:
        return ""
    if isinstance(result, dict):
        return str(result.get("evidence", ""))
    return str(getattr(result, "evidence", ""))


def _has_associated_red_flag(
    chain: dict[str, Any],
    signal_results: dict[str, Any],
) -> bool:
    """Check if chain has any associated red flags that fired."""
    red_flags = chain.get("red_flags") or []
    for rf_id in red_flags:
        if isinstance(rf_id, str) and _check_fired(rf_id, signal_results):
            return True
    return False


def _evaluate_chain(
    chain: dict[str, Any],
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a causal chain against pipeline check results.

    Returns chain status dict with activation details and risk level.
    """
    triggers = chain.get("trigger_signals") or []
    amplifiers = chain.get("amplifier_signals") or []
    mitigators = chain.get("mitigator_signals") or []
    evidence_signals = chain.get("evidence_signals") or []

    fired_triggers = [c for c in triggers if _check_fired(c, signal_results)]
    fired_amplifiers = [c for c in amplifiers if _check_fired(c, signal_results)]
    fired_mitigators = [c for c in mitigators if _check_fired(c, signal_results)]

    # Chain is active if any trigger check fired
    active = len(fired_triggers) > 0

    # Risk level determination
    if len(fired_triggers) >= 2 or _has_associated_red_flag(chain, signal_results):
        risk_level = "HIGH"
    elif fired_triggers and fired_amplifiers:
        risk_level = "ELEVATED"
    elif fired_triggers:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    # Mitigators can reduce one level
    if fired_mitigators and risk_level in ("HIGH", "ELEVATED"):
        risk_level = {"HIGH": "ELEVATED", "ELEVATED": "MODERATE"}[risk_level]

    # Collect evidence from evidence checks
    evidence_summary = [
        _get_check_evidence(c, signal_results)
        for c in evidence_signals
        if _get_check_evidence(c, signal_results)
    ]

    return {
        "chain_id": chain.get("chain_id", ""),
        "name": chain.get("name", ""),
        "peril_id": chain.get("peril_id", ""),
        "description": chain.get("description", ""),
        "active": active,
        "risk_level": risk_level,
        "triggered_triggers": fired_triggers,
        "active_amplifiers": fired_amplifiers,
        "active_mitigators": fired_mitigators,
        "total_triggers": len(triggers),
        "total_amplifiers": len(amplifiers),
        "total_mitigators": len(mitigators),
        "evidence_summary": evidence_summary,
        "historical_filing_rate": chain.get("historical_filing_rate"),
        "median_severity_usd": chain.get("median_severity_usd"),
    }


def _collect_peril_evidence(active_chains: list[dict[str, Any]]) -> list[str]:
    """Collect deduplicated evidence strings from active chains."""
    seen: set[str] = set()
    evidence: list[str] = []
    for chain in active_chains:
        for ev in chain.get("evidence_summary", []):
            if ev and ev not in seen:
                seen.add(ev)
                evidence.append(ev)
    return evidence


def _aggregate_peril(
    peril: dict[str, Any],
    chains: list[dict[str, Any]],
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate chain results into a peril-level assessment."""
    chain_results = [_evaluate_chain(c, signal_results) for c in chains]
    active_chains = [c for c in chain_results if c["active"]]

    # Peril risk = highest chain risk
    risk_levels = [c["risk_level"] for c in active_chains]
    peril_risk = max(risk_levels, key=_risk_order, default="LOW")

    return {
        "peril_id": peril.get("peril_id", ""),
        "name": peril.get("name", ""),
        "description": peril.get("description", ""),
        "risk_level": peril_risk,
        "active_chain_count": len(active_chains),
        "total_chain_count": len(chains),
        "chains": chain_results,
        "frequency": peril.get("frequency", "unknown"),
        "severity": peril.get("severity", "unknown"),
        "typical_settlement_range": peril.get("typical_settlement_range", ""),
        "key_drivers": peril.get("key_drivers") or [],
        "key_evidence": _collect_peril_evidence(active_chains),
    }


def extract_peril_scoring(state: Any) -> dict[str, Any]:
    """Extract peril-organized scoring data for templates.

    Cross-references brain framework perils and causal chains with
    pipeline signal_results to produce a structured scoring dict.

    Args:
        state: AnalysisState (typed as Any to avoid import dependency)

    Returns:
        Dict with keys:
        - perils: list of active peril assessments sorted by risk
        - all_perils: list of all perils with risk levels
        - active_count: number of perils with active chains
        - highest_peril: peril_id with highest risk (or None)
    """
    try:
        from do_uw.brain.brain_unified_loader import load_causal_chains, load_perils

        perils = load_perils()
        chains = load_causal_chains()
    except Exception:
        logger.debug("Could not load brain framework data, returning empty dict")
        return {}

    if not perils:
        return {}

    # Extract signal_results from state
    signal_results: dict[str, Any] = {}
    analysis = getattr(state, "analysis", None)
    if analysis is not None:
        cr = getattr(analysis, "signal_results", None)
        if cr and isinstance(cr, dict):
            signal_results = cr

    # Group chains by peril
    chains_by_peril: dict[str, list[dict[str, Any]]] = {}
    for chain in chains:
        pid = chain.get("peril_id", "")
        chains_by_peril.setdefault(pid, []).append(chain)

    # Evaluate each peril
    peril_results: list[dict[str, Any]] = []
    for peril in perils:
        pid = peril.get("peril_id", "")
        peril_chains = chains_by_peril.get(pid, [])
        result = _aggregate_peril(peril, peril_chains, signal_results)
        peril_results.append(result)

    # Sort: active perils first, then by risk level (descending)
    active = [p for p in peril_results if p["active_chain_count"] > 0]
    active.sort(key=lambda p: _risk_order(p["risk_level"]), reverse=True)

    highest = active[0]["peril_id"] if active else None

    return {
        "perils": active,
        "all_perils": peril_results,
        "active_count": len(active),
        "highest_peril": highest,
    }
