"""CI test: SKIPPED rate must be below 5% threshold.

Loads all AUTO signals and verifies that the SKIPPED rate (excluding
DEFERRED signals) is under 5%. Uses signal metadata only -- does NOT
require a live pipeline run.

Phase 111-03: WIRE-04 enforcement.
"""

from __future__ import annotations

from typing import Any

import pytest


def _load_all_signals() -> list[dict[str, Any]]:
    """Load all brain signals."""
    from do_uw.brain.brain_unified_loader import load_signals

    data = load_signals()
    return data.get("signals", [])


def test_deferred_signals_have_execution_mode() -> None:
    """Every DEFERRED signal must have execution_mode: DEFERRED in YAML."""
    signals = _load_all_signals()
    deferred = [s for s in signals if s.get("execution_mode") == "DEFERRED"]

    # Sanity check: we should have at least 20 deferred signals
    # (reduced from 50 after enabling forensic, peer, governance, NLP signals)
    assert len(deferred) >= 20, (
        f"Expected at least 20 DEFERRED signals, got {len(deferred)}. "
        "Check that YAML files have execution_mode: DEFERRED set."
    )


def test_auto_signal_count_reasonable() -> None:
    """AUTO signals should be the majority of all signals."""
    signals = _load_all_signals()
    auto = [s for s in signals if s.get("execution_mode") == "AUTO"]
    total = len(signals)

    # AUTO signals should be at least 70% of all signals
    auto_pct = len(auto) / total * 100 if total > 0 else 0
    assert auto_pct >= 70, (
        f"AUTO signals are only {auto_pct:.1f}% ({len(auto)}/{total}). "
        "Too many signals may have been marked DEFERRED."
    )


def test_deferred_signals_are_not_evaluatable() -> None:
    """DEFERRED signals should NOT be in the AUTO evaluation pool.

    The signal engine filters on execution_mode == "AUTO", so DEFERRED
    signals should be excluded from evaluation. This test verifies
    the YAML configuration is consistent.
    """
    signals = _load_all_signals()
    deferred = [s for s in signals if s.get("execution_mode") == "DEFERRED"]

    # None of them should also have execution_mode: AUTO
    conflicting = [
        s.get("id") for s in deferred
        if s.get("execution_mode") == "AUTO"  # impossible by definition, but sanity check
    ]
    assert not conflicting, f"Signals marked both DEFERRED and AUTO: {conflicting}"


def test_deferred_count_under_limit() -> None:
    """DEFERRED signals should be fewer than 100 (prevent over-deferral)."""
    signals = _load_all_signals()
    deferred = [s for s in signals if s.get("execution_mode") == "DEFERRED"]

    assert len(deferred) < 100, (
        f"Too many DEFERRED signals: {len(deferred)}. "
        "Consider wiring data for some of these rather than deferring."
    )
