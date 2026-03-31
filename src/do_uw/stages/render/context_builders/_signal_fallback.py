"""Graceful degradation wrappers for signal consumption in context builders.

Wraps _signal_consumer functions with null-safety and default values so
context builders never crash on missing or SKIPPED signals. SignalUnavailable
is a falsy sentinel that surfaces in rendered output as a visible marker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from do_uw.stages.render.context_builders._signal_consumer import (
    SignalResultView,
    get_signal_level,
    get_signal_result,
    get_signal_status,
    get_signal_value,
    get_signals_by_prefix,
)

__all__ = [
    "SignalUnavailable",
    "safe_get_value",
    "safe_get_status",
    "safe_get_level",
    "safe_get_result",
    "safe_get_signals_by_prefix",
]


@dataclass(frozen=True)
class SignalUnavailable:
    """Falsy sentinel indicating a signal could not be retrieved.

    Returned by safe_get_result when signal is missing or data unavailable.
    Renders as a visible marker in templates via __str__.
    """

    signal_id: str
    reason: str  # "not_found", "no_results", "skipped", "data_unavailable"

    def __str__(self) -> str:
        return f"Signal unavailable: {self.signal_id} ({self.reason})"

    def __bool__(self) -> bool:
        return False


def safe_get_result(
    signal_results: dict[str, Any] | None, signal_id: str
) -> SignalResultView | SignalUnavailable:
    """Get typed view or SignalUnavailable sentinel. Never raises."""
    if signal_results is None:
        return SignalUnavailable(signal_id, "no_results")
    view = get_signal_result(signal_results, signal_id)
    if view is None:
        return SignalUnavailable(signal_id, "not_found")
    return view


def safe_get_value(
    signal_results: dict[str, Any] | None,
    signal_id: str,
    default: str | float | None = None,
) -> str | float | None:
    """Get signal value with fallback default. Never raises."""
    if signal_results is None:
        return default
    result = get_signal_value(signal_results, signal_id)
    return result if result is not None else default


def safe_get_status(
    signal_results: dict[str, Any] | None,
    signal_id: str,
    default: str = "SKIPPED",
) -> str:
    """Get signal status with fallback default. Never raises."""
    if signal_results is None:
        return default
    result = get_signal_status(signal_results, signal_id)
    return result if result is not None else default


def safe_get_level(
    signal_results: dict[str, Any] | None,
    signal_id: str,
    default: str = "",
) -> str:
    """Get threshold_level with fallback default. Never raises."""
    if signal_results is None:
        return default
    result = get_signal_level(signal_results, signal_id)
    return result if result else default


def safe_get_signals_by_prefix(
    signal_results: dict[str, Any] | None, prefix: str
) -> list[SignalResultView]:
    """Get signals by prefix, returning empty list on None. Never raises."""
    if signal_results is None:
        return []
    return get_signals_by_prefix(signal_results, prefix)
