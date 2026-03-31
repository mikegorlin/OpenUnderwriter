"""Severity amplifiers: YAML loading, signal-driven firing, combination (Phase 108).

Amplifiers modify estimated severity when specific signal conditions are
met. Each amplifier has a multiplier (1.0-5.0) and a list of signal_ids
that trigger it. If ANY signal in the list is TRIGGERED/STRONG/CRITICAL,
the amplifier fires.

Amplifier combination is multiplicative with a 3.0 cap to prevent
runaway from multiple small amplifiers stacking.

The 11 amplifiers are defined in severity_model_design.yaml and conform
to the SeverityAmplifier Pydantic schema from brain_schema.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from do_uw.brain.brain_schema import SeverityAmplifier
from do_uw.models.severity import AmplifierResult

__all__ = [
    "combine_amplifiers",
    "evaluate_amplifiers",
    "load_amplifiers",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Design YAML loading
# ---------------------------------------------------------------

_DESIGN_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "framework"
    / "severity_model_design.yaml"
)
_design_cache: dict[str, Any] | None = None
_amplifiers_cache: list[SeverityAmplifier] | None = None


def _load_severity_design() -> dict[str, Any]:
    """Load severity_model_design.yaml. Cached as module-level singleton."""
    global _design_cache
    if _design_cache is not None:
        return _design_cache
    with open(_DESIGN_YAML_PATH) as f:
        _design_cache = yaml.safe_load(f)
    return _design_cache  # type: ignore[return-value]


def load_amplifiers() -> list[SeverityAmplifier]:
    """Load 11 severity amplifiers from design YAML catalog.

    Returns validated SeverityAmplifier Pydantic models.
    Cached as module-level singleton.
    """
    global _amplifiers_cache
    if _amplifiers_cache is not None:
        return _amplifiers_cache

    design = _load_severity_design()
    catalog = design.get("severity_amplifiers", {}).get("catalog", [])

    # Fields that the SeverityAmplifier schema accepts
    _valid_fields = set(SeverityAmplifier.model_fields.keys())

    amplifiers: list[SeverityAmplifier] = []
    for entry in catalog:
        try:
            # Strip extra fields not in schema (e.g. calibration_required)
            cleaned = {k: v for k, v in entry.items() if k in _valid_fields}
            amp = SeverityAmplifier(**cleaned)
            amplifiers.append(amp)
        except Exception:
            logger.warning(
                "Failed to parse amplifier: %s", entry.get("id", "unknown"),
                exc_info=True,
            )

    _amplifiers_cache = amplifiers
    logger.debug("Loaded %d severity amplifiers from design YAML", len(amplifiers))
    return amplifiers


# ---------------------------------------------------------------
# Signal status checking
# ---------------------------------------------------------------

_TRIGGERED_STATUSES = frozenset({
    "TRIGGERED", "FIRED", "FLAGGED", "RED", "YELLOW",
    "CRITICAL", "STRONG", "HIGH",
})


def _is_signal_triggered(signal_results: dict[str, Any], signal_id: str) -> bool:
    """Check if a signal is in a triggered state.

    Handles dict-based signal results with 'status', 'triggered', 'fired'
    fields. Same pattern as case_characteristics._check_triggered().
    """
    result = signal_results.get(signal_id)
    if result is None:
        return False

    if isinstance(result, dict):
        # Check explicit boolean fields
        if result.get("triggered") is True or result.get("fired") is True:
            return True
        # Check status string
        status = str(result.get("status", "")).upper()
        if status in _TRIGGERED_STATUSES:
            return True
        # Check data_status + severity combination
        data_status = str(result.get("data_status", "")).upper()
        severity = str(result.get("severity", "")).upper()
        if data_status == "EVALUATED" and severity in ("HIGH", "CRITICAL"):
            return True

    # SignalResultView objects (Phase 104)
    if hasattr(result, "status"):
        status_val = str(getattr(result, "status", "")).upper()
        if status_val in _TRIGGERED_STATUSES:
            return True

    return False


# ---------------------------------------------------------------
# Amplifier evaluation
# ---------------------------------------------------------------


def evaluate_amplifiers(
    amplifiers: list[SeverityAmplifier],
    signal_results: dict[str, Any],
) -> list[AmplifierResult]:
    """Evaluate each amplifier against signal results.

    An amplifier fires if ANY of its signal_ids is triggered in the
    signal results. If no signal data is available, the amplifier
    silently doesn't fire (multiplier=1.0, no noise).

    Args:
        amplifiers: List of SeverityAmplifier definitions.
        signal_results: Signal evaluation results dict.

    Returns:
        List of AmplifierResult for each amplifier.
    """
    results: list[AmplifierResult] = []

    for amp in amplifiers:
        matched_signals: list[str] = []
        for signal_id in amp.signal_ids:
            if _is_signal_triggered(signal_results, signal_id):
                matched_signals.append(signal_id)

        fired = len(matched_signals) > 0
        multiplier = amp.multiplier if fired else 1.0

        explanation = ""
        if fired:
            explanation = (
                f"{amp.name}: {len(matched_signals)} signal(s) triggered "
                f"({', '.join(matched_signals[:3])})"
            )

        results.append(
            AmplifierResult(
                amplifier_id=amp.id,
                name=amp.name,
                fired=fired,
                multiplier=multiplier,
                trigger_signals_matched=matched_signals,
                explanation=explanation,
            )
        )

    return results


# ---------------------------------------------------------------
# Amplifier combination
# ---------------------------------------------------------------

_MAX_COMBINED_MULTIPLIER = 3.0


def combine_amplifiers(results: list[AmplifierResult]) -> float:
    """Combine fired amplifier multipliers multiplicatively with cap.

    Multiplies all fired amplifier multipliers together. Caps at 3.0
    to prevent runaway from many small amplifiers stacking.

    Args:
        results: List of AmplifierResult (some fired, some not).

    Returns:
        Combined multiplier (1.0 if none fired, capped at 3.0).
    """
    combined = 1.0
    for result in results:
        if result.fired:
            combined *= result.multiplier

    if combined > _MAX_COMBINED_MULTIPLIER:
        logger.warning(
            "Amplifier combination %.2f exceeds cap %.1f; capping",
            combined, _MAX_COMBINED_MULTIPLIER,
        )
        combined = _MAX_COMBINED_MULTIPLIER

    return combined
