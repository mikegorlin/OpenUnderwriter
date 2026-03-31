"""Scorecard context builder for worksheet front page.

Extracts tier badge, claim probability, severity/DDL, tower recommendation,
allegation mapping, H/A/E composites, factor scores, and top concerns.
Phase 114 rework: all scoring intelligence on one dense page.
Phase 131-03: visualization context (waterfall, radar, probability, scenarios, tornado).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_consumer import (
    get_signal_result,
)
from do_uw.stages.render.charts.gauge import render_score_gauge
from do_uw.stages.render.charts.waterfall_chart import render_waterfall_chart
from do_uw.stages.render.charts.tornado_chart import render_tornado_chart
from do_uw.stages.render.context_builders.probability_decomposition import (
    build_probability_decomposition,
)
from do_uw.stages.render.context_builders.scenario_generator import (
    compute_risk_clusters,
    generate_scenarios,
)
from do_uw.stages.render.formatters_numeric import (
    _compact_number,
    format_currency,
)

logger = logging.getLogger(__name__)

# Threshold level severity ordering (higher = more severe)
_LEVEL_ORDER: dict[str, int] = {"red": 3, "yellow": 2, "orange": 1, "": 0}

# Humanized factor names (shorter, underwriter-friendly)
_FACTOR_LABELS: dict[str, str] = {
    "F1": "Prior Litigation",
    "F2": "Stock Decline",
    "F3": "Restatement / Audit",
    "F4": "IPO / SPAC / M&A",
    "F5": "Guidance Misses",
    "F6": "Short Interest",
    "F7": "Volatility",
    "F8": "Financial Distress",
    "F9": "Governance",
    "F10": "Officer Stability",
}

# Zone colors for severity P×S classification
_ZONE_COLORS: dict[str, str] = {
    "GREEN": "#059669",
    "YELLOW": "#D97706",
    "ORANGE": "#EA580C",
    "RED": "#B91C1C",
}

# Tier colors for the score gauge
_TIER_COLORS: dict[str, str] = {
    "WIN": "#047857",
    "PREFERRED": "#047857",
    "WANT": "#2563EB",
    "STANDARD": "#2563EB",
    "WRITE": "#D4A843",
    "WATCH": "#D97706",
    "ELEVATED": "#D97706",
    "WALK": "#B91C1C",
    "HIGH_RISK": "#B91C1C",
    "NO TOUCH": "#7F1D1D",
    "PROHIBITED": "#7F1D1D",
}


def build_scorecard_context(
    state: AnalysisState,
    *,
    canonical: Any | None = None,
) -> dict[str, Any]:
    """Build scorecard page data from AnalysisState.

    Args:
        state: The analysis state.
        canonical: Optional CanonicalMetrics object for cross-section consistency.
            Used for metrics_strip (market_cap, revenue) when available.

    Returns comprehensive scoring context for the scorecard template.
    """
    if state.scoring is None:
        return {"scorecard_available": False}

    sc = state.scoring

    # Tier and score
    tier = sc.tier.tier if sc.tier else "N/A"
    quality_score = round(sc.quality_score, 1)

    # H/A/E composites
    hae = _build_hae_context(sc)

    # Factor scores summary
    factors_summary = _build_factors_summary(sc)

    # Claim probability
    claim_prob = _build_claim_probability(sc)

    # Severity and DDL
    severity = _build_severity(sc)

    # Tower recommendation
    tower = _build_tower(sc)

    # Actuarial pricing summary
    actuarial = _build_actuarial(sc)

    # Risk type classification
    risk_type = _build_risk_type(sc)

    # Allegation mapping
    allegations = _build_allegations(sc)

    # Top concerns: triggered signals sorted by severity (max 8)
    top_concerns = _build_top_concerns(state)

    # HAE recommendations (underwriter guidance)
    recommendations = _build_recommendations(sc)

    # Generate SVG gauge for score visualization (INFO-01)
    gauge_svg = render_score_gauge(quality_score, tier)

    # Visualization context (Phase 131-03)
    viz = _build_visualization_context(state, sc, quality_score)

    ctx = {
        "scorecard_available": True,
        "tier": tier,
        "tier_color": _TIER_COLORS.get(tier, "#6B7280"),
        "quality_score": quality_score,
        "gauge_svg": gauge_svg,
        "hae": hae,
        "factors_summary": factors_summary,
        "claim_prob": claim_prob,
        "severity": severity,
        "tower": tower,
        "actuarial": actuarial,
        "risk_type": risk_type,
        "allegations": allegations,
        "top_concerns": top_concerns,
        "recommendations": recommendations,
        # Legacy keys for backward compat with heatmap component
        "composites": hae.get("composites", {}),
        "metrics_strip": _build_metrics_strip(state, canonical=canonical),
    }
    ctx.update(viz)
    return ctx


def _build_visualization_context(
    state: AnalysisState,
    sc: Any,
    quality_score: float,
) -> dict[str, Any]:
    """Build chart and visualization context for scoring section.

    Generates waterfall SVG, radar SVG, probability decomposition,
    scenarios, tornado SVG, risk clusters, and dominant cluster label.
    Returns a dict to merge into the main scorecard context.
    """
    viz: dict[str, Any] = {}

    # -- Waterfall chart --
    tier_thresholds = [
        {"tier": "WIN", "min_score": 86},
        {"tier": "WRITE", "min_score": 71},
        {"tier": "WATCH", "min_score": 51},
        {"tier": "WALK", "min_score": 31},
        {"tier": "NO TOUCH", "min_score": 0},
    ]
    factors_for_waterfall = [
        {
            "id": fs.factor_id,
            "name": getattr(fs, "factor_name", fs.factor_id),
            "points_deducted": fs.points_deducted,
            "max_points": fs.max_points,
        }
        for fs in sc.factor_scores
    ]
    try:
        viz["waterfall_svg"] = render_waterfall_chart(
            factors_for_waterfall, quality_score, tier_thresholds
        )
    except Exception:
        logger.debug("Waterfall chart generation failed", exc_info=True)
        viz["waterfall_svg"] = ""

    # -- Radar chart (SVG format) --
    try:
        from do_uw.stages.render.charts.radar_chart import create_radar_chart
        from do_uw.stages.render.design_system import DesignSystem

        radar_result = create_radar_chart(
            sc.factor_scores,
            DesignSystem(),
            format="svg",
            show_threshold_rings=True,
            show_mean_ring=True,
        )
        viz["radar_svg"] = radar_result if isinstance(radar_result, str) else ""
    except Exception:
        logger.debug("Radar chart generation failed", exc_info=True)
        viz["radar_svg"] = ""

    # -- Probability decomposition --
    try:
        viz["probability_components"] = build_probability_decomposition(state)
    except Exception:
        logger.debug("Probability decomposition failed", exc_info=True)
        viz["probability_components"] = []

    # -- Scenarios + tornado chart --
    try:
        scenarios = generate_scenarios(state)
        viz["scenarios"] = scenarios
        if scenarios:
            viz["tornado_svg"] = render_tornado_chart(scenarios, quality_score)
        else:
            viz["tornado_svg"] = ""
    except Exception:
        logger.debug("Scenario generation failed", exc_info=True)
        viz["scenarios"] = []
        viz["tornado_svg"] = ""

    # -- Risk clusters --
    try:
        clusters = compute_risk_clusters(sc.factor_scores)
        viz["risk_clusters"] = clusters
        # Find dominant cluster (>50% of total deductions)
        dominant = next(
            (c for c in clusters if c.get("is_dominant")),
            None,
        )
        if dominant:
            fids = "+".join(dominant["factor_ids"])
            pct = round(dominant["pct_of_total"] * 100)
            viz["dominant_cluster"] = (
                f"{dominant['name']}: {fids} = {pct}% of total score"
            )
        else:
            viz["dominant_cluster"] = ""
    except Exception:
        logger.debug("Risk cluster computation failed", exc_info=True)
        viz["risk_clusters"] = []
        viz["dominant_cluster"] = ""

    return viz


def _build_hae_context(sc: Any) -> dict[str, Any]:
    """Extract H/A/E scoring lens results."""
    hae_result = getattr(sc, "hae_result", None)
    if not hae_result:
        return {"available": False, "composites": {}}

    composites = getattr(hae_result, "composites", {}) or {}
    # Format composites as percentages for display
    composites_pct = {}
    for dim, val in composites.items():
        composites_pct[dim] = round(val * 100, 1) if val else 0

    return {
        "available": True,
        "tier": getattr(hae_result, "tier", "N/A"),
        "composites": composites,
        "composites_pct": composites_pct,
        "product_score": round(getattr(hae_result, "product_score", 0) * 100, 3),
        "confidence": getattr(hae_result, "confidence", "N/A"),
        "tier_source": getattr(hae_result, "tier_source", ""),
        "crf_active": sum(
            1
            for v in (getattr(hae_result, "crf_vetoes", None) or [])
            if getattr(v, "is_active", False)
        ),
        "crf_total": len(getattr(hae_result, "crf_vetoes", None) or []),
    }


def _build_factors_summary(sc: Any) -> list[dict[str, Any]]:
    """Build factor scores with humanized labels and signal context."""
    factors: list[dict[str, Any]] = []
    for fs in sc.factor_scores:
        pct = round(fs.points_deducted / fs.max_points * 100) if fs.max_points > 0 else 0
        # Get top evidence string — skip raw scoring mechanics
        top_evidence = ""
        if fs.evidence:
            for ev in fs.evidence:
                ev_str = str(ev)
                # Skip system-internal evidence
                if "Signal-driven scoring" in ev_str or "coverage=" in ev_str:
                    continue
                if "rule_based" in ev_str.lower():
                    continue
                top_evidence = ev_str[:80]
                break

        signal_count = 0
        coverage_pct = 0
        if hasattr(fs, "signal_coverage") and fs.signal_coverage is not None:
            coverage_pct = round(fs.signal_coverage * 100)
        if hasattr(fs, "signal_contributions") and fs.signal_contributions:
            signal_count = len(fs.signal_contributions)

        factors.append({
            "id": fs.factor_id,
            "name": _FACTOR_LABELS.get(fs.factor_id, fs.factor_name),
            "full_name": fs.factor_name,
            "score": round(fs.points_deducted, 1),
            "max": fs.max_points,
            "pct": pct,
            "has_deduction": fs.points_deducted > 0.05,
            "evidence": top_evidence,
            "signal_count": signal_count,
            "coverage_pct": coverage_pct,
            "scoring_method": getattr(fs, "scoring_method", "rule_based"),
        })
    return factors


def _build_claim_probability(sc: Any) -> dict[str, Any]:
    """Extract claim probability data."""
    cp = getattr(sc, "claim_probability", None)
    if not cp:
        return {"available": False}

    return {
        "available": True,
        "band": cp.band,
        "range_low": round(cp.range_low_pct, 2),
        "range_high": round(cp.range_high_pct, 2),
        "industry_base": round(cp.industry_base_rate_pct, 2),
        "vs_industry": "below" if cp.range_high_pct < cp.industry_base_rate_pct else (
            "above" if cp.range_low_pct > cp.industry_base_rate_pct else "inline"
        ),
        "needs_calibration": getattr(cp, "needs_calibration", False),
    }


def _build_severity(sc: Any) -> dict[str, Any]:
    """Extract severity model results."""
    sr = getattr(sc, "severity_result", None)
    if not sr:
        return {"available": False}

    primary = getattr(sr, "primary", None)
    result: dict[str, Any] = {
        "available": True,
        "zone": getattr(sr, "zone", "N/A"),
        "zone_color": _ZONE_COLORS.get(str(getattr(sr, "zone", "")), "#6B7280"),
        "probability": getattr(sr, "probability", 0),
        "expected_loss": getattr(sr, "expected_loss", 0),
    }

    if primary:
        result["settlement"] = getattr(primary, "estimated_settlement", 0)
        result["settlement_fmt"] = format_currency(
            getattr(primary, "estimated_settlement", None), compact=True
        )
        result["damages"] = getattr(primary, "damages_estimate", 0)
        result["damages_fmt"] = format_currency(
            getattr(primary, "damages_estimate", None), compact=True
        )
        result["defense_costs"] = getattr(primary, "defense_costs", 0)
        result["defense_fmt"] = format_currency(
            getattr(primary, "defense_costs", None), compact=True
        )
        result["confidence"] = getattr(primary, "confidence", "N/A")

        # Amplifiers
        amps = getattr(primary, "amplifier_results", None) or []
        fired_amps = [a for a in amps if getattr(a, "fired", False)]
        result["amplifiers_total"] = len(amps)
        result["amplifiers_fired"] = len(fired_amps)
        result["fired_amplifier_names"] = [
            getattr(a, "name", "") for a in fired_amps
        ]

        # Scenarios from primary lens
        scenarios = getattr(primary, "scenarios", None) or []
        result["scenarios"] = [
            {
                "type": getattr(s, "allegation_type", getattr(s, "drop_level", "")),
                "level": getattr(s, "drop_level", ""),
                "settlement": getattr(s, "settlement_estimate", 0),
                "settlement_fmt": format_currency(
                    getattr(s, "settlement_estimate", None), compact=True
                ),
                "total_exposure": getattr(s, "total_exposure", 0),
                "total_fmt": format_currency(
                    getattr(s, "total_exposure", None), compact=True
                ),
            }
            for s in scenarios
        ]

    # DDL decline scenarios (legacy SECT7-08)
    ss = getattr(sc, "severity_scenarios", None)
    if ss:
        declines = getattr(ss, "decline_scenarios", None) or {}
        result["ddl_scenarios"] = {
            k: format_currency(v, compact=True)
            for k, v in declines.items()
        }
        result["ddl_amount"] = format_currency(
            getattr(ss, "market_cap", None), compact=True
        )
        # Percentile-based scenarios
        pct_scenarios = getattr(ss, "scenarios", None) or []
        result["ddl_percentiles"] = [
            {
                "label": getattr(s, "label", ""),
                "percentile": getattr(s, "percentile", 0),
                "settlement": format_currency(
                    getattr(s, "settlement_estimate", None), compact=True
                ),
                "defense": format_currency(
                    getattr(s, "defense_cost_estimate", None), compact=True
                ),
                "total": format_currency(
                    getattr(s, "total_exposure", None), compact=True
                ),
            }
            for s in pct_scenarios
        ]

    return result


def _build_tower(sc: Any) -> dict[str, Any]:
    """Extract tower recommendation data."""
    tr = getattr(sc, "tower_recommendation", None)
    if not tr:
        return {"available": False}

    layers = []
    for layer in (getattr(tr, "layers", None) or []):
        pos = getattr(layer, "position", "")
        # Skip DECLINE as a visual layer
        if pos == "DECLINE":
            continue
        layers.append({
            "position": pos,
            "label": _tower_label(pos),
            "risk_assessment": getattr(layer, "risk_assessment", ""),
            "premium_guidance": getattr(layer, "premium_guidance", ""),
            "attachment_range": getattr(layer, "attachment_range", ""),
        })

    return {
        "available": True,
        "recommended_position": getattr(tr, "recommended_position", "N/A"),
        "recommended_label": _tower_label(
            str(getattr(tr, "recommended_position", ""))
        ),
        "minimum_attachment": getattr(tr, "minimum_attachment", "N/A"),
        "layers": layers,
        "side_a": getattr(tr, "side_a_assessment", ""),
        "needs_calibration": getattr(tr, "needs_calibration", False),
    }


def _tower_label(position: str) -> str:
    """Convert tower position enum to display label."""
    labels = {
        "PRIMARY": "Primary",
        "LOW_EXCESS": "Low Excess",
        "MID_EXCESS": "Mid Excess",
        "HIGH_EXCESS": "High Excess",
        "DECLINE": "Decline",
    }
    return labels.get(position, position)


def _build_actuarial(sc: Any) -> dict[str, Any]:
    """Extract actuarial pricing summary."""
    ap = getattr(sc, "actuarial_pricing", None)
    if not ap or not getattr(ap, "has_data", False):
        return {"available": False}

    el = getattr(ap, "expected_loss", None)
    result: dict[str, Any] = {
        "available": True,
        "total_premium": format_currency(
            getattr(ap, "total_indicated_premium", None), compact=True
        ),
    }

    if el:
        result["filing_prob"] = round(
            getattr(el, "filing_probability_pct", 0), 2
        )
        result["median_severity"] = format_currency(
            getattr(el, "median_severity", None), compact=True
        )
        result["expected_loss"] = format_currency(
            getattr(el, "total_expected_loss", None), compact=True
        )
        result["expected_defense"] = format_currency(
            getattr(el, "expected_defense", None), compact=True
        )

        # Scenario losses
        scenario_losses = getattr(el, "scenario_losses", None) or []
        result["loss_scenarios"] = [
            {
                "label": getattr(s, "label", ""),
                "percentile": getattr(s, "percentile", 0),
                "total": format_currency(
                    getattr(s, "total_expected", None), compact=True
                ),
            }
            for s in scenario_losses
        ]

    # Layer pricing
    layer_pricing = getattr(ap, "layer_pricing", None) or []
    result["layers"] = [
        {
            "type": getattr(lp, "layer_type", ""),
            "label": _tower_label(getattr(lp, "layer_type", "").upper()),
            "attachment": format_currency(
                getattr(lp, "attachment", None), compact=True
            ),
            "limit": format_currency(
                getattr(lp, "limit", None), compact=True
            ),
            "premium": format_currency(
                getattr(lp, "indicated_premium", None), compact=True
            ),
            "rol": round(getattr(lp, "indicated_rol", 0) * 100, 2),
        }
        for lp in layer_pricing
    ]

    return result


def _build_risk_type(sc: Any) -> dict[str, Any]:
    """Extract risk type classification."""
    rt = getattr(sc, "risk_type", None)
    if not rt:
        return {"available": False}

    primary = getattr(rt, "primary", "N/A")
    # Humanize risk type name
    labels = {
        "GUIDANCE_DEPENDENT": "Guidance Dependent",
        "BINARY_EVENT": "Binary Event",
        "GROWTH_DARLING": "Growth Darling",
        "REGULATORY_SENSITIVE": "Regulatory Sensitive",
        "TRANSFORMATION": "Transformation",
        "STABLE_MATURE": "Stable Mature",
        "DISTRESSED": "Distressed",
    }

    return {
        "available": True,
        "primary": primary,
        "primary_label": labels.get(str(primary), str(primary)),
        "secondary": getattr(rt, "secondary", None),
        "evidence": getattr(rt, "evidence", []),
    }


def _build_allegations(sc: Any) -> dict[str, Any]:
    """Extract allegation mapping."""
    am = getattr(sc, "allegation_mapping", None)
    if not am:
        return {"available": False}

    # Theory labels
    labels = {
        "A_DISCLOSURE": "Disclosure Failure (10b-5)",
        "B_GUIDANCE": "Guidance / Forecast",
        "C_PRODUCT_OPS": "Product / Operations",
        "D_GOVERNANCE": "Governance (14a)",
        "E_MA": "M&A / Transaction",
    }

    primary = getattr(am, "primary_exposure", None)
    theories = []
    for t in (getattr(am, "theories", None) or []):
        theory_id = getattr(t, "theory", "")
        exposure = getattr(t, "exposure", None)
        theories.append({
            "id": theory_id,
            "label": labels.get(str(theory_id), str(theory_id)),
            "exposure": str(exposure) if exposure else "LOW",
            "is_primary": str(theory_id) == str(primary),
        })

    return {
        "available": True,
        "primary": str(primary) if primary else "N/A",
        "primary_label": labels.get(str(primary), str(primary)) if primary else "N/A",
        "theories": theories,
    }


def _build_top_concerns(state: AnalysisState) -> list[dict[str, Any]]:
    """Build top concerns from triggered signals, sorted by severity.

    Enriches each concern with the signal's human-readable name and
    RAP dimension label so underwriters see meaningful content.
    """
    # Load signal metadata for names
    signal_meta = _load_signal_metadata()

    top_concerns: list[dict[str, Any]] = []
    signal_results = {}
    if state.analysis and state.analysis.signal_results:
        signal_results = state.analysis.signal_results
    # Detect mismatched source data (same value from wrong field = mapper bug)
    _seen_source_values: dict[str, list[str]] = {}
    for sid, raw in signal_results.items():
        if isinstance(raw, dict) and raw.get("status") == "TRIGGERED":
            src = raw.get("source", "")
            val = raw.get("value")
            key = f"{src}:{val}"
            _seen_source_values.setdefault(key, []).append(sid)

    for sid, raw in signal_results.items():
        if not isinstance(raw, dict):
            continue
        if raw.get("status") != "TRIGGERED":
            continue

        # Skip signals reading from mismatched source (3+ signals same source+value)
        src = raw.get("source", "")
        val = raw.get("value")
        key = f"{src}:{val}"
        sharing = _seen_source_values.get(key, [])
        if len(sharing) >= 3 and sid != sharing[0]:
            continue  # Only keep the first of duplicated mapper bugs

        view = get_signal_result(signal_results, sid)
        if view is None:
            continue
        concern_value = view.value
        if isinstance(concern_value, float):
            concern_value = round(concern_value, 2)

        meta = signal_meta.get(sid, {})
        signal_name = meta.get("name", sid)
        rap_sub = meta.get("rap_subcategory", "")

        # Build human-readable explanation
        explanation = _humanize_concern(signal_name, raw)

        # RAP dimension labels
        rap_labels = {
            "host": "Structural Risk",
            "agent": "Behavioral Risk",
            "environment": "External Risk",
        }
        rap_label = rap_labels.get(view.rap_class, view.rap_class or "")

        top_concerns.append({
            "signal_id": view.signal_id,
            "signal_name": signal_name,
            "status": view.status,
            "level": view.threshold_level,
            "value": concern_value,
            "evidence": view.evidence,
            "explanation": explanation,
            "rap_class": view.rap_class,
            "rap_label": rap_label,
            "rap_subcategory": rap_sub,
        })
    top_concerns.sort(key=lambda c: _LEVEL_ORDER.get(c["level"], 0), reverse=True)
    return top_concerns[:8]


_SIGNAL_META_CACHE: dict[str, dict[str, str]] | None = None


def _load_signal_metadata() -> dict[str, dict[str, str]]:
    """Load signal names and metadata from brain YAML (cached)."""
    global _SIGNAL_META_CACHE  # noqa: PLW0603
    if _SIGNAL_META_CACHE is not None:
        return _SIGNAL_META_CACHE

    try:
        from do_uw.brain.brain_unified_loader import BrainLoader
        loader = BrainLoader()
        data = loader.load_signals()
        sigs = data.get("signals", [])
        _SIGNAL_META_CACHE = {
            s["id"]: {
                "name": s.get("name", s["id"]),
                "rap_class": s.get("rap_class", ""),
                "rap_subcategory": s.get("rap_subcategory", ""),
            }
            for s in sigs
            if isinstance(s, dict) and "id" in s
        }
    except Exception:
        logger.debug("Failed to load signal metadata", exc_info=True)
        _SIGNAL_META_CACHE = {}

    return _SIGNAL_META_CACHE


def _humanize_concern(
    signal_name: str,
    raw: dict[str, Any],
) -> str:
    """Convert raw signal result into underwriter-friendly explanation.

    Uses threshold_context (human-written) over raw evidence when available.
    Includes source attribution.
    """
    # Prefer threshold_context — it's the YAML-authored description
    threshold_ctx = raw.get("threshold_context", "")
    source = raw.get("source", "")
    value = raw.get("value")
    evidence = str(raw.get("evidence", ""))

    # Format source for display
    source_label = ""
    if source:
        # Clean up source field names
        src_clean = source.replace("_", " ").replace("forensic ", "").title()
        source_label = f" (Source: {src_clean})"

    # Use threshold_context if it has real content
    if threshold_ctx and ">" not in threshold_ctx and "<" not in threshold_ctx:
        return f"{threshold_ctx}{source_label}"

    # Format value nicely
    val_str = ""
    if isinstance(value, float):
        if value < 1 and value > 0:
            val_str = f"{value:.1%}"
        else:
            val_str = f"{value:,.0f}" if value == int(value) else f"{value:.2f}"
    elif value is not None:
        val_str = str(value)

    if threshold_ctx:
        return f"{threshold_ctx} — value: {val_str}{source_label}"

    # Fallback
    if val_str:
        return f"Value: {val_str}{source_label}"
    return f"Flagged{source_label}"


def _build_recommendations(sc: Any) -> dict[str, Any]:
    """Extract HAE underwriter recommendations."""
    hae_result = getattr(sc, "hae_result", None)
    if not hae_result:
        return {"available": False}

    recs = getattr(hae_result, "recommendations", {}) or {}
    return {
        "available": bool(recs),
        "pricing": recs.get("pricing_guidance", ""),
        "layer_comfort": recs.get("layer_comfort", ""),
        "terms": recs.get("terms_conditions", ""),
        "monitoring": recs.get("monitoring_triggers", ""),
        "referral": recs.get("referral_criteria", ""),
        "tone": recs.get("communication_pattern", ""),
    }


def _extract_sourced_value(obj: Any, attr: str) -> Any:
    """Extract a value from an attribute that may be a SourcedValue or plain."""
    val = getattr(obj, attr, None)
    if val is None:
        return None
    if hasattr(val, "value"):
        return val.value
    return val


def _format_large_number(value: float | int) -> str:
    """Format a large number compactly: 13B, 7.3B, 17.2K etc."""
    return "$" + _compact_number(float(value))


def _format_employee_count(value: int) -> str:
    """Format employee count with comma grouping: 17,800."""
    return f"{value:,}"


def _build_metrics_strip(
    state: AnalysisState,
    *,
    canonical: Any | None = None,
) -> dict[str, str | None]:
    """Extract key financial metrics for scorecard strip.

    When canonical is available, uses canonical values for market_cap, revenue,
    and employees. Falls back to legacy extraction otherwise.

    Returns pre-formatted strings ready for display (not raw floats).
    """
    ms: dict[str, str | None] = {
        "market_cap": None,
        "revenue": None,
        "employees": None,
        "years_public": None,
    }

    # Market cap: prefer canonical > company profile > extracted market data
    if canonical is not None and canonical.market_cap.raw is not None:
        ms["market_cap"] = canonical.market_cap.formatted
    else:
        mc_val = _extract_sourced_value(state.company, "market_cap") if state.company else None
        if mc_val is None and state.extracted and state.extracted.market:
            mc_val = _extract_sourced_value(state.extracted.market.stock, "market_cap_yf")
        if mc_val is not None:
            ms["market_cap"] = _format_large_number(mc_val)

    # Revenue: prefer canonical > inline XBRL extraction
    if canonical is not None and canonical.revenue.raw is not None:
        ms["revenue"] = canonical.revenue.formatted
    elif state.extracted and state.extracted.financials:
        stmts = state.extracted.financials.statements
        if stmts and stmts.income_statement:
            for li in stmts.income_statement.line_items:
                if "revenue" in li.label.lower() or "net sales" in li.label.lower():
                    for sv in li.values.values():
                        if sv is not None:
                            rev_val = sv.value if hasattr(sv, "value") else sv
                            if rev_val is not None:
                                ms["revenue"] = _format_large_number(rev_val)
                            break
                    break

    # Employees: prefer canonical > company profile
    if canonical is not None and canonical.employees.raw is not None:
        ms["employees"] = canonical.employees.formatted
    elif state.company:
        emp_val = _extract_sourced_value(state.company, "employee_count")
        if emp_val is not None:
            ms["employees"] = _format_employee_count(int(emp_val))

    # Years public
    if state.company:
        yp_val = _extract_sourced_value(state.company, "years_public")
        if yp_val is not None:
            ms["years_public"] = str(int(yp_val))

    return ms


__all__ = ["build_scorecard_context"]
