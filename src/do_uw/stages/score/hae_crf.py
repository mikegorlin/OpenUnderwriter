"""CRF ELECTRE discordance evaluation with time/claim-status awareness.

Evaluates 6 Critical Red Flag categories against signal results.
CRF vetoes are non-compensatory -- they override favorable composite
scores regardless of concordance. Time-aware (recent/aging/expired)
and claim-status-aware (NO_CLAIM/CLAIM_FILED/CLAIM_RESOLVED).

Based on ELECTRE III multi-criteria decision analysis framework.
CRF catalog is loaded from scoring_model_design.yaml.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from do_uw.stages.score.scoring_lens import (
    CRFVetoResult,
    HAETier,
)

__all__ = [
    "CRFVetoResult",
    "evaluate_crf_discordance",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------

_FRAMEWORK_DIR = Path(__file__).resolve().parent.parent.parent / "brain" / "framework"

_crf_catalog_cache: list[dict[str, Any]] | None = None

# Tier ordering for reduction operations
_TIER_ORDER_LIST = [
    HAETier.PREFERRED,
    HAETier.STANDARD,
    HAETier.ELEVATED,
    HAETier.HIGH_RISK,
    HAETier.PROHIBITED,
]


def _load_crf_catalog() -> list[dict[str, Any]]:
    """Load CRF veto catalog from scoring_model_design.yaml. Cached."""
    global _crf_catalog_cache
    if _crf_catalog_cache is not None:
        return _crf_catalog_cache
    path = _FRAMEWORK_DIR / "scoring_model_design.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    catalog = data.get("crf_discordance", {}).get("crf_veto_catalog", [])
    _crf_catalog_cache = catalog
    return _crf_catalog_cache


# ---------------------------------------------------------------
# CRF signal checking
# ---------------------------------------------------------------


def _check_crf_signal_active(
    crf: dict[str, Any], signal_results: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Check if any of a CRF's required signals are active (TRIGGERED+red).

    Returns (is_active, list of matched signal IDs).
    """
    signals = crf.get("signals", [])
    if not signals:
        return False, []

    matched: list[str] = []
    for sid in signals:
        raw = signal_results.get(sid)
        if raw is None or not isinstance(raw, dict):
            continue
        status = raw.get("status", "")
        level = raw.get("threshold_level", "")
        if status == "TRIGGERED" and level == "red":
            matched.append(sid)

    return len(matched) > 0, matched


# ---------------------------------------------------------------
# Time and claim-status determination
# ---------------------------------------------------------------


def _determine_time_context(
    signal_results: dict[str, Any], signals: list[str]
) -> str:
    """Determine temporal context from signal details.

    Returns "recent" (< 1 year), "aging" (1-3 years), or "expired" (> 3 years).
    Defaults to "recent" if temporal data unavailable (conservative).

    Per CONTEXT.md: "Decay curves need more thought" -- these are initial
    parameters, exact calibration is future work.
    """
    # Look for temporal indicators in signal details
    for sid in signals:
        raw = signal_results.get(sid)
        if raw is None or not isinstance(raw, dict):
            continue
        details = raw.get("details", {})
        if not isinstance(details, dict):
            continue

        # Check for explicit time_context in details
        time_ctx = details.get("time_context")
        if time_ctx in ("recent", "aging", "expired"):
            return time_ctx

        # Check for age/years fields
        age_years = details.get("age_years")
        if isinstance(age_years, (int, float)):
            if age_years < 1:
                return "recent"
            if age_years < 3:
                return "aging"
            return "expired"

    # Conservative default: assume recent
    return "recent"


def _determine_claim_status(signal_results: dict[str, Any]) -> str:
    """Determine overall claim status from litigation signals.

    Returns "NO_CLAIM", "CLAIM_FILED", or "CLAIM_RESOLVED".
    Checks LIT.* signal details for claim indicators.
    """
    for sid, raw in signal_results.items():
        if not sid.startswith("LIT.") or not isinstance(raw, dict):
            continue
        details = raw.get("details", {})
        if not isinstance(details, dict):
            continue

        claim_status = details.get("claim_status")
        if claim_status in ("CLAIM_FILED", "CLAIM_RESOLVED"):
            return claim_status

        # Check for active litigation indicators
        if details.get("active_litigation") is True:
            return "CLAIM_FILED"
        if details.get("resolved") is True:
            return "CLAIM_RESOLVED"

    return "NO_CLAIM"


# ---------------------------------------------------------------
# Time/claim veto adjustment
# ---------------------------------------------------------------


def _reduce_tier(tier: HAETier, levels: int) -> HAETier:
    """Reduce a tier by N levels (toward PREFERRED), minimum STANDARD.

    CRF was triggered, so never reduce below STANDARD.
    """
    idx = _TIER_ORDER_LIST.index(tier)
    new_idx = max(idx - levels, 1)  # 1 = STANDARD (minimum for CRF)
    return _TIER_ORDER_LIST[new_idx]


def _adjust_veto_for_time_and_claims(
    base_veto: HAETier, time_context: str, claim_status: str
) -> HAETier:
    """Adjust CRF veto target based on temporal context and claim status.

    Decay rules (initial parameters, calibration_required=true):
    - recent + NO_CLAIM: full veto (claim imminent)
    - recent + CLAIM_FILED: full veto (exposure crystallized)
    - aging + NO_CLAIM: reduce by 1 tier (exposure diminishing)
    - aging + CLAIM_FILED: full veto (claim still active)
    - expired + NO_CLAIM: reduce by 2 tiers (DDL likely passed)
    - expired + CLAIM_RESOLVED: minimum STANDARD (risk resolved)
    - Never reduce below STANDARD (CRF was triggered)
    """
    if time_context == "recent":
        # Full veto regardless of claim status
        return base_veto

    if time_context == "aging":
        if claim_status == "CLAIM_FILED":
            return base_veto  # Active claim, no decay
        if claim_status == "CLAIM_RESOLVED":
            return _reduce_tier(base_veto, 1)
        # NO_CLAIM: diminishing exposure
        return _reduce_tier(base_veto, 1)

    if time_context == "expired":
        if claim_status == "CLAIM_FILED":
            return _reduce_tier(base_veto, 1)  # Expired but claim active
        if claim_status == "CLAIM_RESOLVED":
            return HAETier.STANDARD  # Risk resolved
        # NO_CLAIM: DDL likely passed
        return _reduce_tier(base_veto, 2)

    # Unknown time context, conservative
    return base_veto


# ---------------------------------------------------------------
# CRF veto target mapping (5-tier adaptation)
# ---------------------------------------------------------------

# Map design doc tier names to 5-tier HAETier
# CAUTIOUS -> ELEVATED, ADVERSE -> HIGH_RISK per CONTEXT.md
_TIER_REMAP: dict[str, HAETier] = {
    "PREFERRED": HAETier.PREFERRED,
    "STANDARD": HAETier.STANDARD,
    "CAUTIOUS": HAETier.ELEVATED,
    "ELEVATED": HAETier.ELEVATED,
    "ADVERSE": HAETier.HIGH_RISK,
    "HIGH_RISK": HAETier.HIGH_RISK,
    "PROHIBITED": HAETier.PROHIBITED,
}


def _resolve_veto_target(raw_target: str) -> HAETier:
    """Resolve a raw tier string to HAETier, handling 6->5 tier remapping."""
    return _TIER_REMAP.get(raw_target, HAETier.ELEVATED)


# ---------------------------------------------------------------
# Main CRF evaluation
# ---------------------------------------------------------------


def evaluate_crf_discordance(
    signal_results: dict[str, Any],
    pre_crf_tier: HAETier,
) -> tuple[HAETier, list[CRFVetoResult]]:
    """Evaluate all CRF categories against signal results.

    Returns (final_tier, list of all CRF veto results).
    Final tier = max(pre_crf_tier, max(active adjusted veto targets)).

    Args:
        signal_results: Signal evaluation results dict
        pre_crf_tier: Tier from composite/individual assessment

    Returns:
        Tuple of (final_tier, all_veto_results)
    """
    catalog = _load_crf_catalog()
    claim_status = _determine_claim_status(signal_results)

    all_vetoes: list[CRFVetoResult] = []
    active_count = 0

    for crf in catalog:
        crf_id = crf.get("id", "")

        # Skip CRF-MULTI (handled separately after counting)
        if crf_id == "CRF-MULTI":
            continue

        is_active, matched = _check_crf_signal_active(crf, signal_results)

        if is_active:
            active_count += 1

        time_context = (
            _determine_time_context(signal_results, matched)
            if is_active
            else "recent"
        )

        raw_target = crf.get("veto_target", "ELEVATED")
        base_veto = _resolve_veto_target(raw_target)

        # Apply time/claim adjustments if active
        adjusted_veto = (
            _adjust_veto_for_time_and_claims(base_veto, time_context, claim_status)
            if is_active
            else base_veto
        )

        all_vetoes.append(
            CRFVetoResult(
                crf_id=crf_id,
                condition=crf.get("condition", ""),
                veto_target=adjusted_veto if is_active else base_veto,
                signals_matched=matched,
                is_active=is_active,
                time_context=time_context if is_active else "",
                claim_status=claim_status if is_active else "",
            )
        )

    # Handle CRF-MULTI: fires if 3+ other CRFs are active
    multi_crf = next((c for c in catalog if c.get("id") == "CRF-MULTI"), None)
    if multi_crf:
        multi_active = active_count >= 3
        raw_target = multi_crf.get("veto_target", "HIGH_RISK")
        base_veto = _resolve_veto_target(raw_target)

        all_vetoes.append(
            CRFVetoResult(
                crf_id="CRF-MULTI",
                condition=multi_crf.get("condition", "3+ CRFs active"),
                veto_target=base_veto,
                signals_matched=[],
                is_active=multi_active,
                time_context="recent" if multi_active else "",
                claim_status=claim_status if multi_active else "",
            )
        )

    # Compute final tier: max of pre_crf_tier and all active veto targets
    final_tier = pre_crf_tier
    for veto in all_vetoes:
        if veto.is_active and veto.veto_target > final_tier:
            final_tier = veto.veto_target

    return final_tier, all_vetoes
