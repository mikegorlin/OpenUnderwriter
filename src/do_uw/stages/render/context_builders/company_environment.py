"""Environment assessment and sector risk context builders.

Extracts regulatory intensity, geopolitical risk, ESG gaps, cyber risk,
macro sensitivity, and sector risk classification into template-ready dicts.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)


def _format_env_signal(
    env_data: dict[str, Any],
    score_key: str,
    details_key: str,
) -> dict[str, Any]:
    """Format a single environment signal for template consumption.

    Maps numeric scores to HIGH/MODERATE/LOW levels and extracts
    human-readable detail strings from the details dict.
    """
    score = env_data.get(score_key, 0) or 0
    details_dict = env_data.get(details_key, {}) or {}

    if score >= 3:
        level = "HIGH"
    elif score >= 1:
        level = "MODERATE"
    else:
        level = "LOW"

    details_parts: list[str] = []
    if isinstance(details_dict, dict):
        regulators = details_dict.get("regulators")
        if regulators:
            details_parts.append(", ".join(str(r) for r in regulators))
        sanctioned = details_dict.get("sanctioned_countries")
        if sanctioned:
            details_parts.append(f"Sanctioned: {', '.join(str(c) for c in sanctioned)}")
        high_risk = details_dict.get("high_risk_countries")
        if high_risk:
            details_parts.append(f"Elevated: {', '.join(str(c) for c in high_risk)}")
        esg_count = details_dict.get("esg_risk_factor_count")
        if esg_count:
            details_parts.append(f"{esg_count} ESG risk factor{'s' if esg_count > 1 else ''}")
        if details_dict.get("esg_litigation_present"):
            details_parts.append("ESG litigation present")
        if details_dict.get("breach_detected"):
            details_parts.append("Breach indicator detected")
        elif details_dict.get("has_high_severity"):
            details_parts.append("High severity cyber risk factors")
        cyber_count = details_dict.get("cyber_risk_factor_count")
        if cyber_count and not details_dict.get("breach_detected"):
            details_parts.append(f"{cyber_count} cyber risk factor{'s' if cyber_count > 1 else ''}")
        dimensions = details_dict.get("dimensions")
        if dimensions:
            details_parts.append(", ".join(str(d).replace("_", " ").title() for d in dimensions))

    details = "; ".join(details_parts) if details_parts else ""

    return {"score": score, "level": level, "details": details}


def _build_environment_assessment(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Build environment assessment context from state text_signals.

    Returns (env_dict, has_data) tuple for template consumption.
    """
    env_data: dict[str, Any] = {}
    if state.extracted is not None:
        env_data = state.extracted.text_signals.get("environment_assessment", {}) or {}

    if not env_data:
        return {}, False

    env_dict = {
        "regulatory_intensity": _format_env_signal(
            env_data, "regulatory_intensity_score", "regulatory_details",
        ),
        "geopolitical_risk": _format_env_signal(
            env_data, "geopolitical_risk_score", "geopolitical_details",
        ),
        "esg_gap": _format_env_signal(
            env_data, "esg_gap_score", "esg_gap_details",
        ),
        "cyber_risk": _format_env_signal(
            env_data, "cyber_risk_score", "cyber_risk_details",
        ),
        "macro_sensitivity": _format_env_signal(
            env_data, "macro_sensitivity_score", "macro_sensitivity_details",
        ),
    }

    # Enrich with ENVR.* signal results if available
    envr_signals = safe_get_signals_by_prefix(signal_results, "ENVR.")
    for sig in envr_signals:
        if sig.status == "TRIGGERED":
            # Map signal ID suffix to env_dict key
            suffix = sig.signal_id.split(".")[-1].lower()
            if suffix in env_dict:
                display = signal_to_display_level(sig.status, sig.threshold_level)
                if display == "Critical":
                    env_dict[suffix]["level"] = "HIGH"

    has_data = any(sig.get("score", 0) > 0 for sig in env_dict.values())
    return env_dict, has_data


def _build_sector_risk(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Build sector risk classification context from state text_signals.

    Returns (sector_dict, has_data) tuple for template consumption.
    All tier/level logic lives here -- template is a pure consumer.
    """
    sector_data: dict[str, Any] = {}
    if state.extracted is not None:
        sector_data = state.extracted.text_signals.get("sector_classification", {}) or {}

    if not sector_data:
        return {}, False

    # --- Hazard Tier ---
    hazard = sector_data.get("sector_hazard_tier", {}) or {}
    tier = hazard.get("tier", "")
    _TIER_COLORS = {
        "Highest": "bg-red-700",
        "High": "bg-amber-500",
        "Moderate": "bg-sky-500",
        "Lower": "bg-emerald-600",
    }
    tier_color = _TIER_COLORS.get(tier, "bg-gray-400")
    filing_rate = hazard.get("filing_rate")
    filing_rate_str = f"{filing_rate:.1f}% filing rate" if filing_rate else ""
    hazard_context = hazard.get("context", "")

    hazard_dict = {
        "tier": tier,
        "tier_color": tier_color,
        "filing_rate": filing_rate_str,
        "context": hazard_context,
        "match_level": hazard.get("match_level", ""),
    }

    # --- Claim Patterns ---
    claims = sector_data.get("sector_claim_patterns", {}) or {}
    claim_theories = claims.get("claim_theories", [])[:3]
    industry_group = claims.get("industry_group") or ""

    claims_dict = {
        "theories": claim_theories,
        "industry_group": industry_group,
    }

    # --- Regulatory Overlay ---
    regulatory = sector_data.get("sector_regulatory_overlay", {}) or {}
    intensity = regulatory.get("intensity", "Low")
    _INTENSITY_COLORS = {
        "Very High": "bg-red-700",
        "High": "bg-amber-500",
        "Moderate": "bg-sky-500",
        "Low": "bg-emerald-600",
    }
    intensity_color = _INTENSITY_COLORS.get(intensity, "bg-gray-400")
    regulators = regulatory.get("regulators", [])
    trend = regulatory.get("trend", "")

    regulatory_dict = {
        "intensity": intensity,
        "intensity_color": intensity_color,
        "regulators": regulators,
        "trend": trend,
    }

    # --- Peer Comparison ---
    peer = sector_data.get("sector_peer_comparison", {}) or {}
    outlier_count = peer.get("outlier_count", 0)
    dimensions = peer.get("dimensions", [])
    sector_name = peer.get("sector_name") or ""

    if outlier_count >= 2:
        peer_level = "HIGH"
    elif outlier_count >= 1:
        peer_level = "MODERATE"
    else:
        peer_level = "LOW"

    formatted_dims: list[dict[str, Any]] = []
    _DIM_LABELS = {
        "overall_score": "Overall Risk Score",
        "governance_quality": "Governance Quality",
        "financial_health": "Financial Health",
    }
    for dim in dimensions:
        formatted_dims.append({
            "name": _DIM_LABELS.get(dim.get("dimension", ""), dim.get("dimension", "")),
            "company_value": f"{dim.get('company_value', 0):.1f}",
            "median": f"{dim.get('sector_median', 0):.1f}",
            "is_outlier": dim.get("is_outlier", False),
            "deviation_std": dim.get("deviation_std", 0),
        })

    peer_dict = {
        "outlier_count": outlier_count,
        "peer_level": peer_level,
        "dimensions": formatted_dims,
        "sector_name": sector_name,
    }

    has_data = bool(tier or claim_theories or regulators or dimensions)

    return {
        "hazard": hazard_dict,
        "claims": claims_dict,
        "regulatory": regulatory_dict,
        "peer": peer_dict,
    }, has_data


__all__ = [
    "_build_environment_assessment",
    "_build_sector_risk",
    "_format_env_signal",
]
