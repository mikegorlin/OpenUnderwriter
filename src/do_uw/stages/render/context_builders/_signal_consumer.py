"""Typed extraction layer for context builders consuming signal results.

SignalResultView (frozen dataclass) + 7 typed extraction functions replacing
raw dict access in context builders. Contract between ANALYZE output and RENDER.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from do_uw.brain.brain_unified_loader import load_signals

__all__ = [
    "SignalResultView",
    "get_signal_result",
    "get_signal_value",
    "get_signal_status",
    "get_signal_level",
    "get_signals_by_prefix",
    "signal_to_display_level",
    "get_signal_do_context",
    "get_signal_epistemology",
]


@dataclass(frozen=True)
class SignalResultView:
    """Read-only typed view of a signal result plus brain metadata."""

    signal_id: str
    status: str
    value: str | float | None
    threshold_level: str
    evidence: str
    source: str
    confidence: str
    threshold_context: str
    factors: tuple[str, ...]
    details: dict[str, Any]
    data_status: str
    content_type: str
    category: str
    rap_class: str
    rap_subcategory: str
    mechanism: str
    epistemology_rule_origin: str
    epistemology_threshold_basis: str
    do_context: str



_brain_signal_cache: dict[str, dict[str, Any]] | None = None


def _get_brain_signal(signal_id: str) -> dict[str, Any] | None:
    """Lazily load brain signals and look up by signal_id."""
    global _brain_signal_cache
    if _brain_signal_cache is None:
        data = load_signals()
        _brain_signal_cache = {
            s["id"]: s for s in data.get("signals", []) if "id" in s
        }
    return _brain_signal_cache.get(signal_id)


def _reset_brain_cache() -> None:
    """Clear brain signal cache (for testing)."""
    global _brain_signal_cache
    _brain_signal_cache = None



def _build_view(signal_id: str, raw: dict[str, Any]) -> SignalResultView:
    """Build a SignalResultView from a raw signal result dict."""
    brain = _get_brain_signal(signal_id)
    rap_class = rap_subcategory = mechanism = rule_origin = threshold_basis = ""
    if brain:
        rap_class = brain.get("rap_class", "")
        rap_subcategory = brain.get("rap_subcategory", "")
        ev = brain.get("evaluation")
        if isinstance(ev, dict):
            mechanism = ev.get("mechanism", "")
        ep = brain.get("epistemology")
        if isinstance(ep, dict):
            rule_origin = ep.get("rule_origin", "")
            threshold_basis = ep.get("threshold_basis", "")
    factors_raw = raw.get("factors", [])
    factors = tuple(factors_raw) if isinstance(factors_raw, list) else ()

    return SignalResultView(
        signal_id=signal_id,
        status=raw.get("status", ""),
        value=raw.get("value"),
        threshold_level=raw.get("threshold_level", ""),
        evidence=raw.get("evidence", ""),
        source=raw.get("source", ""),
        confidence=raw.get("confidence", "MEDIUM"),
        threshold_context=raw.get("threshold_context", ""),
        factors=factors,
        details=raw.get("details", {}),
        data_status=raw.get("data_status", "EVALUATED"),
        content_type=raw.get("content_type", "EVALUATIVE_CHECK"),
        category=raw.get("category", ""),
        rap_class=rap_class,
        rap_subcategory=rap_subcategory,
        mechanism=mechanism,
        epistemology_rule_origin=rule_origin,
        epistemology_threshold_basis=threshold_basis,
        do_context=raw.get("do_context", ""),
    )



def get_signal_result(
    signal_results: dict[str, Any], signal_id: str
) -> SignalResultView | None:
    """Get typed view of a signal result, or None if missing."""
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return None
    return _build_view(signal_id, raw)


def get_signal_value(
    signal_results: dict[str, Any], signal_id: str
) -> str | float | None:
    """Get just the value field of a signal result."""
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return None
    return raw.get("value")


def get_signal_status(
    signal_results: dict[str, Any], signal_id: str
) -> str | None:
    """Get just the status string of a signal result."""
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return None
    return raw.get("status")


def get_signal_level(
    signal_results: dict[str, Any], signal_id: str
) -> str:
    """Get the threshold_level of a signal result, or empty string."""
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return ""
    return raw.get("threshold_level", "")


def get_signals_by_prefix(
    signal_results: dict[str, Any], prefix: str
) -> list[SignalResultView]:
    """Get all signal results whose IDs start with the given prefix."""
    views: list[SignalResultView] = []
    for sid, raw in signal_results.items():
        if sid.startswith(prefix) and isinstance(raw, dict):
            views.append(_build_view(sid, raw))
    return views


def signal_to_display_level(status: str, threshold_level: str) -> str:
    """Map status + threshold_level to display string (Critical/Warning/etc)."""
    if status == "TRIGGERED":
        if threshold_level == "red":
            return "Critical"
        if threshold_level == "yellow":
            return "Warning"
        return "Elevated"
    if status == "CLEAR":
        return "Clear"
    if status == "SKIPPED":
        return "Unavailable"
    if status == "INFO":
        return "Info"
    return "Unknown"


def get_signal_do_context(
    signal_results: dict[str, Any], signal_id: str
) -> str:
    """Get the do_context string for a signal result, or empty string."""
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return ""
    return raw.get("do_context", "")


def get_signal_epistemology(
    signal_results: dict[str, Any], signal_id: str
) -> tuple[str, str] | None:
    """Get (rule_origin, threshold_basis) from brain YAML definition."""
    if signal_id not in signal_results:
        return None
    brain = _get_brain_signal(signal_id)
    if brain is None:
        return None
    epist = brain.get("epistemology")
    if not isinstance(epist, dict):
        return None
    return (epist.get("rule_origin", ""), epist.get("threshold_basis", ""))
