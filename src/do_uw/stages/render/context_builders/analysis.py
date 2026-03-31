"""Analysis context builder -- template-ready dicts for classification,
hazard profile, risk factors, and re-exports of evaluative builders.

Evaluative functions (forensic composites, executive risk, NLP signals,
temporal signals, peril map) live in analysis_evaluative.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    sector_display_name,
)

# Re-export evaluative builders so callers see same public API
from do_uw.stages.render.context_builders.analysis_evaluative import (  # noqa: F401
    extract_executive_risk,
    extract_forensic_composites,
    extract_nlp_signals,
    extract_peril_map,
    extract_temporal_signals,
)

# Exposure level labels from normalized IES / dimension scores
_EXPOSURE_LABELS: list[tuple[float, str]] = [
    (80, "CRITICAL"),
    (65, "HIGH"),
    (50, "ELEVATED"),
    (35, "MODERATE"),
    (0, "LOW"),
]


def _score_to_exposure(score: float) -> str:
    """Map a 0-100 score to an exposure level label."""
    for threshold, label in _EXPOSURE_LABELS:
        if score >= threshold:
            return label
    return "LOW"


# Category code -> human-readable name
_CATEGORY_NAMES: dict[str, str] = {
    "H1": "Business & Operating Model",
    "H2": "People & Management",
    "H3": "Financial Structure",
    "H4": "Governance Structure",
    "H5": "Public Company Maturity",
    "H6": "External Environment",
    "H7": "Emerging / Modern Hazards",
}


# 1. Classification (Layer 1)


def extract_classification(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract classification data (tier, sector, filing rates, severity bands)."""
    cls = state.classification
    if cls is None:
        return None

    # Re-derive sector name: prefer yfinance, fall back to SIC mapping.
    sector_name = cls.sector_name or cls.sector_code
    from do_uw.stages.render.context_builders.company import _get_yfinance_sector
    yf_sector = _get_yfinance_sector(state)
    if yf_sector:
        sector_name = yf_sector
    elif state.company and state.company.identity:
        ident = state.company.identity
        if ident.sic_code and ident.sic_code.value:
            from do_uw.stages.resolve.sec_identity import sic_to_sector

            sector_name = sector_display_name(sic_to_sector(str(ident.sic_code.value)))
        else:
            sector_name = sector_display_name(sector_name)
    else:
        sector_name = sector_display_name(sector_name)

    return {
        "market_cap_tier": cls.market_cap_tier.value,
        "sector_code": cls.sector_code,
        "sector_name": sector_name,
        "years_public": str(cls.years_public) if cls.years_public is not None else "N/A",
        "base_filing_rate_pct": format_percentage(cls.base_filing_rate_pct),
        "severity_band_low_m": format_currency(cls.severity_band_low_m * 1_000_000, compact=True),
        "severity_band_high_m": format_currency(cls.severity_band_high_m * 1_000_000, compact=True),
        "ddl_exposure_base_m": format_currency(cls.ddl_exposure_base_m * 1_000_000, compact=True),
        "ipo_multiplier": f"{cls.ipo_multiplier:.2f}x",
        "cap_filing_multiplier": f"{cls.cap_filing_multiplier:.2f}x",
    }


# 2. Hazard Profile (Layer 2)


def extract_hazard_profile(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract hazard profile: IES, dimensions, categories, interactions."""
    hp = state.hazard_profile
    if hp is None:
        return None

    ies_label = _score_to_exposure(hp.ies_score)

    # All dimensions sorted by normalized_score descending
    elevated_levels = {"ELEVATED", "HIGH", "CRITICAL"}
    all_dimensions: list[dict[str, Any]] = []
    for dim in sorted(hp.dimension_scores, key=lambda d: d.normalized_score, reverse=True):
        evidence_str = "; ".join(dim.evidence[:2]) if dim.evidence else ""
        exposure = _score_to_exposure(dim.normalized_score)
        all_dimensions.append({
            "dimension_id": dim.dimension_id,
            "name": dim.dimension_name,
            "score": f"{dim.normalized_score:.0f}",
            "raw_score": f"{dim.raw_score:.1f}",
            "max_score": f"{dim.max_score:.1f}",
            "category": dim.category.value,
            "category_name": _CATEGORY_NAMES.get(dim.category.value, dim.category.value),
            "exposure_level": exposure,
            "evidence": evidence_str,
            "data_available": dim.data_available,
        })

    top_risk = [d for d in all_dimensions if d["exposure_level"] in elevated_levels]

    # Category summaries
    categories: list[dict[str, Any]] = []
    for cat_id in ("H1", "H2", "H3", "H4", "H5", "H6", "H7"):
        cat = hp.category_scores.get(cat_id)
        if cat is None:
            continue
        categories.append({
            "category_code": cat_id,
            "category_name": cat.category_name,
            "weight_pct": f"{cat.weight_pct:.1f}%",
            "raw_score": f"{cat.raw_score:.1f}",
            "weighted_score": f"{cat.weighted_score:.1f}",
            "dimensions_scored": f"{cat.dimensions_scored}/{cat.dimensions_total}",
            "data_coverage": f"{cat.data_coverage_pct:.0f}%",
        })

    # Interaction effects
    interactions: list[dict[str, Any]] = []
    for ie in hp.named_interactions + hp.dynamic_interactions:
        interactions.append({
            "name": ie.name,
            "interaction_id": ie.interaction_id,
            "description": ie.description,
            "multiplier": f"{ie.multiplier:.2f}x",
            "multiplier_raw": ie.multiplier,
            "triggered_dims": ie.triggered_dimensions,
            "triggered_dims_display": ", ".join(ie.triggered_dimensions[:5]),
            "is_named": ie.is_named,
            "type_label": "Named Pattern" if ie.is_named else "Dynamic Detection",
        })

    # Group dimensions by category for expandable card rendering (SURF-05)
    dims_by_cat: dict[str, list[dict[str, Any]]] = {}
    for dim in all_dimensions:
        dims_by_cat.setdefault(dim["category"], []).append(dim)

    categories_with_dims: list[dict[str, Any]] = []
    for cat_id in ("H1", "H2", "H3", "H4", "H5", "H6", "H7"):
        cat = hp.category_scores.get(cat_id)
        if cat is None:
            continue
        dims = dims_by_cat.get(cat_id, [])
        elevated_count = sum(1 for d in dims if d["exposure_level"] in elevated_levels)
        categories_with_dims.append({
            "category_code": cat_id,
            "category_name": cat.category_name,
            "weight_pct": f"{cat.weight_pct:.1f}%",
            "raw_score": f"{cat.raw_score:.1f}",
            "weighted_score": f"{cat.weighted_score:.1f}",
            "data_coverage": f"{cat.data_coverage_pct:.0f}%",
            "dimensions": dims,
            "dimension_count": len(dims),
            "elevated_count": elevated_count,
        })

    named_interactions = [i for i in interactions if i["is_named"]]
    dynamic_interactions = [i for i in interactions if not i["is_named"]]

    return {
        "ies_score": f"{hp.ies_score:.0f}",
        "ies_label": ies_label,
        "raw_ies_score": f"{hp.raw_ies_score:.0f}",
        "ies_multiplier": f"{hp.ies_multiplier:.2f}x",
        "data_coverage_pct": f"{hp.data_coverage_pct:.0f}%",
        "confidence_note": hp.confidence_note,
        "all_dimensions": all_dimensions,
        "top_risk_dimensions": top_risk,
        "categories": categories,
        "categories_with_dimensions": categories_with_dims,
        "interactions": interactions,
        "named_interactions": named_interactions,
        "dynamic_interactions": dynamic_interactions,
        "interaction_multiplier": f"{hp.interaction_multiplier:.2f}x",
        "underwriter_flags": hp.underwriter_flags,
    }


# 3. Risk Factors (Item 1A)


def extract_risk_factors(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    """Extract D&O-relevant, new, or unique risk factors for template."""
    if state.extracted is None:
        return None

    rfs = state.extracted.risk_factors
    if not rfs:
        return None

    # D&O-specific explanations for HIGH relevance risk factors by category
    _DO_WHY_MAP: dict[str, str] = {
        "REGULATORY": "Regulatory actions directly target directors and officers; enforcement proceedings can trigger D&O claims and government investigation coverage.",
        "LITIGATION": "Active or threatened litigation creates direct D&O exposure through securities class actions, derivative suits, or regulatory enforcement.",
        "FINANCIAL": "Financial misstatement or restatement risk is the #1 trigger for securities class actions; revenue/earnings volatility increases claim probability.",
        "OPERATIONAL": "Operational failures that impair financial results can give rise to breach of fiduciary duty claims and shareholder derivative actions.",
        "COMPETITIVE": "Competitive disruption that erodes margins or market share triggers stock drops — the primary catalyst for securities fraud allegations.",
        "TECHNOLOGY": "Technology failures or data breaches expose directors to oversight liability claims and regulatory investigations.",
        "GOVERNANCE": "Governance weaknesses directly increase D&O exposure through derivative suits, proxy contests, and regulatory scrutiny of board oversight.",
        "COMPLIANCE": "Compliance failures expose officers to personal liability under SOX, FCPA, and sector-specific regulations.",
        "ESG": "ESG-related misrepresentations increasingly trigger securities fraud and derivative claims; regulatory focus on greenwashing is accelerating.",
    }

    filtered: list[dict[str, Any]] = []
    for rf in rfs:
        is_relevant = rf.do_relevance in ("HIGH", "MEDIUM")
        is_new = rf.is_new_this_year
        is_unique = rf.category not in ("OTHER",) and rf.severity == "HIGH"

        if not (is_relevant or is_new or is_unique):
            continue

        source_passage = rf.source_passage
        # Add D&O explanation for HIGH relevance factors
        do_explanation = ""
        if rf.do_relevance == "HIGH":
            do_explanation = _DO_WHY_MAP.get(rf.category, "Directly relevant to D&O liability exposure.")

        filtered.append({
            "title": rf.title,
            "category": rf.category,
            "severity": rf.severity,
            "is_new": rf.is_new_this_year,
            "do_relevance": rf.do_relevance,
            "source_passage": source_passage,
            "do_explanation": do_explanation,
        })

    if not filtered:
        return None

    # Sort by D&O relevance (HIGH first), then NEW badge, then severity
    relevance_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    filtered.sort(key=lambda f: (
        relevance_order.get(f["do_relevance"], 3),
        not f["is_new"],
        severity_order.get(f["severity"], 3),
        f["category"],
    ))

    return filtered


__all__ = [
    "extract_classification",
    "extract_executive_risk",
    "extract_forensic_composites",
    "extract_hazard_profile",
    "extract_nlp_signals",
    "extract_peril_map",
    "extract_risk_factors",
    "extract_temporal_signals",
]
