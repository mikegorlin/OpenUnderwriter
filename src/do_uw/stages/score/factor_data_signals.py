"""Signal-to-factor aggregation engine.

Computes factor scores from signal evaluation results rather than reading
ExtractedData directly. Provides the signal-driven scoring path with
configurable coverage thresholds and weighted severity normalization.

Signal-driven scoring is primary when coverage >= 50%; falls back to
rule-based scoring otherwise (backward compatibility).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_signals

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor canonical mapping (F1..F10 short <-> long)
# ---------------------------------------------------------------------------

FACTOR_SHORT_TO_LONG: dict[str, str] = {
    "F1": "F1_prior_litigation",
    "F2": "F2_stock_decline",
    "F3": "F3_restatement_audit",
    "F4": "F4_ipo_spac_ma",
    "F5": "F5_guidance_misses",
    "F6": "F6_short_interest",
    "F7": "F7_volatility",
    "F8": "F8_financial_distress",
    "F9": "F9_governance",
    "F10": "F10_officer_stability",
}

FACTOR_LONG_TO_SHORT: dict[str, str] = {v: k for k, v in FACTOR_SHORT_TO_LONG.items()}

# Minimum fraction of evaluable signals that must have results to use signal path
COVERAGE_THRESHOLD = 0.50


# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------


def _threshold_to_severity(level: str) -> float:
    """Map threshold level to numeric severity.

    red=1.0 (full contribution), yellow=0.5 (half), clear/empty=0.0.
    """
    normalized = level.strip().lower()
    if normalized == "red":
        return 1.0
    if normalized == "yellow":
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# Signal weight resolution
# ---------------------------------------------------------------------------


def _get_signal_weight(brain_signal: dict[str, Any], factor_key: str) -> float:
    """Get the weight for a signal's contribution to a specific factor.

    Resolution order:
    1. scoring.contributions[factor_key].weight (per-factor override)
    2. scoring.weight (global signal weight)
    3. 0.5 for inference signals (conjunction/absence/contextual)
    4. 1.0 default

    Args:
        brain_signal: Brain signal dict from YAML.
        factor_key: Long-form factor key (e.g. F1_prior_litigation).
    """
    # Inference signals get half weight by default
    signal_class = brain_signal.get("signal_class", "evaluative")
    default_weight = 0.5 if signal_class == "inference" else 1.0

    scoring = brain_signal.get("scoring")
    if scoring is None:
        return default_weight

    # Check per-factor contribution override
    contributions = scoring.get("contributions", [])
    # Resolve both short and long factor key forms
    short_key = FACTOR_LONG_TO_SHORT.get(factor_key, factor_key)
    for contrib in contributions:
        cf = contrib.get("factor", "")
        if cf == factor_key or cf == short_key:
            return float(contrib.get("weight", default_weight))

    # Global signal weight
    return float(scoring.get("weight", default_weight))


# ---------------------------------------------------------------------------
# Signal lookup for factor
# ---------------------------------------------------------------------------


def get_signals_for_factor(factor_key: str) -> list[dict[str, Any]]:
    """Get all evaluable brain signals tagged for a given factor.

    Loads signals from YAML (cached), filters to:
    - evaluative or inference signal_class (excludes foundational)
    - AUTO execution_mode
    - factors list contains the factor key (short or long form)

    Args:
        factor_key: Long-form factor key (e.g. F1_prior_litigation).

    Returns:
        List of brain signal dicts that contribute to this factor.
    """
    data = load_signals()
    all_signals = data.get("signals", [])

    short_key = FACTOR_LONG_TO_SHORT.get(factor_key, "")
    long_key = factor_key

    matched: list[dict[str, Any]] = []
    for sig in all_signals:
        # Exclude foundational signals (INFO/display)
        sig_class = sig.get("signal_class", "evaluative")
        if sig_class == "foundational":
            continue

        # Only AUTO execution mode
        exec_mode = sig.get("execution_mode", "AUTO")
        if exec_mode != "AUTO":
            continue

        # Check if signal is tagged for this factor
        factors = sig.get("factors", [])
        if short_key in factors or long_key in factors:
            matched.append(sig)

    return matched


# ---------------------------------------------------------------------------
# Aggregation engine
# ---------------------------------------------------------------------------


def aggregate_factor_from_signals(
    factor_key: str,
    signal_results: dict[str, Any],
    max_points: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Aggregate signal results into a factor score.

    For each signal tagged to this factor:
    1. Look up result in signal_results dict
    2. Skip DEFERRED/SKIPPED (excluded from denominator)
    3. Compute weighted severity for TRIGGERED signals
    4. Normalize to 0-max_points scale

    Args:
        factor_key: Long-form factor key (e.g. F1_prior_litigation).
        signal_results: Dict mapping signal_id -> result dict.
        max_points: Maximum points for this factor.

    Returns:
        Tuple of (data_dict, contributions_list):
        - data_dict: signal_score, signal_coverage, use_signal_path
        - contributions_list: per-signal contribution details, sorted desc
    """
    tagged_signals = get_signals_for_factor(factor_key)

    if not tagged_signals:
        return (
            {"signal_score": 0.0, "signal_coverage": 0.0, "use_signal_path": False},
            [],
        )

    weighted_severity_sum = 0.0
    total_weight = 0.0
    evaluated_count = 0
    evaluable_count = 0
    contributions: list[dict[str, Any]] = []

    for sig in tagged_signals:
        sig_id = sig["id"]
        result = signal_results.get(sig_id)

        if result is None:
            # Signal has no result at all -- counts as unevaluated
            evaluable_count += 1
            continue

        status = result.get("status", "")

        # DEFERRED and SKIPPED are excluded from denominator entirely
        if status in ("DEFERRED", "SKIPPED"):
            continue

        evaluable_count += 1
        evaluated_count += 1

        weight = _get_signal_weight(sig, factor_key)
        threshold_level = result.get("threshold_level", "")
        severity = _threshold_to_severity(threshold_level)

        contribution = severity * weight
        weighted_severity_sum += contribution
        total_weight += weight

        contributions.append({
            "signal_id": sig_id,
            "status": status,
            "threshold_level": threshold_level,
            "severity": severity,
            "weight": weight,
            "contribution": contribution,
        })

    # Calculate coverage
    coverage = evaluated_count / evaluable_count if evaluable_count > 0 else 0.0

    # Calculate normalized score
    if total_weight > 0:
        signal_score = (weighted_severity_sum / total_weight) * max_points
    else:
        signal_score = 0.0

    use_signal_path = coverage >= COVERAGE_THRESHOLD

    # Sort contributions by contribution desc
    contributions.sort(key=lambda c: c["contribution"], reverse=True)

    data: dict[str, Any] = {
        "signal_score": signal_score,
        "signal_coverage": coverage,
        "use_signal_path": use_signal_path,
    }

    return data, contributions
