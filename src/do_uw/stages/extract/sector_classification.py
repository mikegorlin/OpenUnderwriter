"""Sector risk classification signal extraction.

Phase 98: Computes 4 SECT.* signal field values from GICS/SIC codes
and static reference data:
- sector_hazard_tier: D&O hazard tier from GICS sub-industry filing rates
- sector_claim_patterns: Top 3 claim theories for GICS industry group
- sector_regulatory_overlay: Named regulators and intensity for GICS group
- sector_peer_comparison: Company vs sector median D&O risk dimensions
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# --- Module-level reference data (loaded once) ---

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "brain" / "config"

_hazard_tiers: dict[str, Any] | None = None
_claim_patterns: dict[str, Any] | None = None
_regulatory_overlay: dict[str, Any] | None = None
_peer_benchmarks: dict[str, Any] | None = None
_sic_gics_mapping: dict[str, Any] | None = None


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from brain/config/."""
    path = _CONFIG_DIR / filename
    return yaml.safe_load(path.read_text())  # type: ignore[no-any-return]


def _get_hazard_tiers() -> dict[str, Any]:
    global _hazard_tiers
    if _hazard_tiers is None:
        _hazard_tiers = _load_yaml("sector_hazard_tiers.yaml")
    return _hazard_tiers


def _get_claim_patterns() -> dict[str, Any]:
    global _claim_patterns
    if _claim_patterns is None:
        _claim_patterns = _load_yaml("sector_claim_patterns.yaml")
    return _claim_patterns


def _get_regulatory_overlay() -> dict[str, Any]:
    global _regulatory_overlay
    if _regulatory_overlay is None:
        _regulatory_overlay = _load_yaml("sector_regulatory_overlay.yaml")
    return _regulatory_overlay


def _get_peer_benchmarks() -> dict[str, Any]:
    global _peer_benchmarks
    if _peer_benchmarks is None:
        _peer_benchmarks = _load_yaml("sector_peer_benchmarks.yaml")
    return _peer_benchmarks


def _get_sic_gics_mapping() -> dict[str, Any]:
    global _sic_gics_mapping
    if _sic_gics_mapping is None:
        path = _CONFIG_DIR / "sic_gics_mapping.json"
        _sic_gics_mapping = json.loads(path.read_text())
    return _sic_gics_mapping


def _resolve_gics_code(gics_code: str | None, sic_code: str | None) -> str | None:
    """Resolve GICS code, falling back from SIC via sic_gics_mapping.json."""
    if gics_code:
        return gics_code
    if not sic_code:
        return None
    mapping = _get_sic_gics_mapping()
    mappings = mapping.get("mappings", {})
    entry = mappings.get(sic_code)
    if entry:
        return entry.get("gics")
    return None


def _unwrap_sourced_value(sv: Any) -> Any:
    """Extract .value from a SourcedValue, or return the raw value."""
    if sv is None:
        return None
    if hasattr(sv, "value"):
        return sv.value
    return sv


def extract_sector_signals(state: AnalysisState) -> dict[str, Any]:
    """Extract all 4 SECT signal field values from state data.

    Returns dict with keys: sector_hazard_tier, sector_claim_patterns,
    sector_regulatory_overlay, sector_peer_comparison.
    """
    # Extract GICS and SIC codes from state
    gics_raw = _unwrap_sourced_value(getattr(state.company, "gics_code", None))
    sic_raw = _unwrap_sourced_value(
        getattr(getattr(state.company, "identity", None), "sic_code", None)
    )

    gics_code = str(gics_raw) if gics_raw else None
    sic_code = str(sic_raw) if sic_raw else None

    # Resolve GICS (fall back from SIC if needed)
    resolved_gics = _resolve_gics_code(gics_code, sic_code)

    # Extract company scores for peer comparison
    company_score: float | None = None
    governance_score: float | None = None
    financial_health: float | None = None

    scoring = getattr(state, "scoring", None)
    if scoring is not None:
        company_score = getattr(scoring, "composite_score", None)

    governance = getattr(getattr(state, "extracted", None), "governance", None)
    if governance is not None:
        gov_score_obj = getattr(governance, "governance_score", None)
        if gov_score_obj is not None:
            total_sv = getattr(gov_score_obj, "total_score", None)
            governance_score = _unwrap_sourced_value(total_sv)
            if governance_score is not None:
                governance_score = float(governance_score)

    # Financial health: try Altman Z-Score from extracted financials
    financials = getattr(getattr(state, "extracted", None), "financials", None)
    if financials is not None:
        z_score = getattr(financials, "altman_z_score", None)
        if z_score is not None:
            financial_health = float(_unwrap_sourced_value(z_score))

    result: dict[str, Any] = {}
    result["sector_hazard_tier"] = _compute_hazard_tier(resolved_gics, sic_code)
    result["sector_claim_patterns"] = _compute_claim_patterns(resolved_gics)
    result["sector_regulatory_overlay"] = _compute_regulatory_overlay(resolved_gics)
    result["sector_peer_comparison"] = _compute_peer_comparison(
        resolved_gics, company_score, governance_score, financial_health
    )

    return result


def _compute_hazard_tier(
    gics_code: str | None, sic_code: str | None
) -> dict[str, Any]:
    """Look up D&O hazard tier with 3-level fallback.

    Fallback: GICS sub-industry (8-digit) -> GICS sector (2-digit) -> default.
    If gics_code is None but sic_code provided, resolves via sic_gics_mapping.
    """
    data = _get_hazard_tiers()
    tiers = data.get("tiers", {})
    fallbacks = data.get("fallback_by_gics_sector", {})

    # If no GICS code, try SIC -> GICS resolution
    effective_gics = gics_code
    if not effective_gics and sic_code:
        effective_gics = _resolve_gics_code(None, sic_code)

    if effective_gics:
        # Level 1: exact sub-industry match (8-digit)
        entry = tiers.get(effective_gics)
        if entry:
            return {
                "tier": entry["tier"],
                "filing_rate": entry.get("filing_rate", 0),
                "context": entry.get("context", ""),
                "gics_code": effective_gics,
                "match_level": "sub_industry",
            }

        # Level 2: sector fallback (first 2 digits)
        sector_code = effective_gics[:2]
        fallback = fallbacks.get(sector_code)
        if fallback:
            return {
                "tier": fallback["tier"],
                "filing_rate": fallback.get("filing_rate", 0),
                "context": fallback.get("context", ""),
                "gics_code": effective_gics,
                "match_level": "sector",
            }

    # Level 3: default
    return {
        "tier": "Moderate",
        "filing_rate": 5.0,
        "context": "Default tier -- insufficient sector data for specific classification",
        "gics_code": effective_gics,
        "match_level": "default",
    }


def _compute_claim_patterns(gics_code: str | None) -> dict[str, Any]:
    """Look up top claim theories by GICS industry group (first 4 digits)."""
    data = _get_claim_patterns()
    patterns = data.get("patterns", {})

    if not gics_code:
        return {"claim_theories": [], "industry_group": None}

    # GICS industry group = first 4 digits
    group_code = gics_code[:4]
    entry = patterns.get(group_code)

    if entry:
        return {
            "claim_theories": entry.get("claim_theories", []),
            "industry_group": entry.get("industry_group", ""),
            "gics_group": group_code,
        }

    return {"claim_theories": [], "industry_group": None, "gics_group": group_code}


def _compute_regulatory_overlay(gics_code: str | None) -> dict[str, Any]:
    """Look up sector regulatory baseline by GICS industry group."""
    data = _get_regulatory_overlay()
    overlays = data.get("overlays", {})

    if not gics_code:
        return {
            "intensity": "Low",
            "regulators": [],
            "trend": "",
            "industry_group": None,
        }

    group_code = gics_code[:4]
    entry = overlays.get(group_code)

    if entry:
        return {
            "intensity": entry.get("intensity", "Low"),
            "regulators": entry.get("regulators", []),
            "trend": entry.get("trend", ""),
            "industry_group": entry.get("industry_group", ""),
            "gics_group": group_code,
        }

    return {
        "intensity": "Low",
        "regulators": [],
        "trend": "",
        "industry_group": None,
        "gics_group": group_code,
    }


def _compute_peer_comparison(
    gics_code: str | None,
    company_score: float | None,
    governance_score: float | None,
    financial_health: float | None,
) -> dict[str, Any]:
    """Compare company scores vs sector median benchmarks.

    Flags outliers (>1 std_dev from sector median) on each dimension.
    Skips dimensions where company data is unavailable.
    """
    data = _get_peer_benchmarks()
    benchmarks = data.get("benchmarks", {})

    dimensions: list[dict[str, Any]] = []
    outlier_count = 0

    if not gics_code:
        return {
            "outlier_count": 0,
            "dimensions": [],
            "sector_name": None,
        }

    sector_code = gics_code[:2]
    sector_bench = benchmarks.get(sector_code)

    if not sector_bench:
        return {
            "outlier_count": 0,
            "dimensions": [],
            "sector_name": None,
        }

    sector_name = sector_bench.get("sector_name", "")

    # Check each dimension where company data is available
    dimension_checks: list[tuple[str, float | None, str]] = [
        ("overall_score", company_score, "overall_score"),
        ("governance_quality", governance_score, "governance_quality"),
        ("financial_health", financial_health, "financial_health"),
    ]

    for dim_key, company_val, bench_key in dimension_checks:
        bench = sector_bench.get(bench_key)
        if bench is None or company_val is None:
            continue

        median = bench.get("median", 0)
        std_dev = bench.get("std_dev", 1)

        if std_dev == 0:
            std_dev = 1  # avoid division by zero

        deviation = abs(company_val - median) / std_dev
        is_outlier = deviation > 1.0

        dimensions.append({
            "dimension": dim_key,
            "company_value": company_val,
            "sector_median": median,
            "sector_std_dev": std_dev,
            "deviation_std": round(deviation, 2),
            "is_outlier": is_outlier,
        })

        if is_outlier:
            outlier_count += 1

    return {
        "outlier_count": outlier_count,
        "dimensions": dimensions,
        "sector_name": sector_name,
        "outlier_dimensions": [
            d["dimension"] for d in dimensions if d["is_outlier"]
        ],
    }


__all__ = ["extract_sector_signals"]
