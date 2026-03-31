"""Underwriting posture context builder.

Extracts PostureRecommendation, zero verifications, and watch items
from AnalysisState.forward_looking into template-ready dicts.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


_ELEMENT_NAMES: dict[str, str] = {
    "decision": "Decision",
    "retention": "Retention",
    "limit": "Limit Capacity",
    "pricing": "Pricing",
    "exclusions": "Exclusions",
    "monitoring": "Monitoring",
    "re_evaluation": "Re-evaluation",
}

_TIER_CSS: dict[str, str] = {
    "WIN": "posture-win",
    "WANT": "posture-want",
    "WRITE": "posture-write",
    "WATCH": "posture-watch",
    "WALK": "posture-walk",
    "NO_TOUCH": "posture-no-touch",
}


def _humanize_element(raw: str) -> str:
    """Convert element key to human-readable name."""
    return _ELEMENT_NAMES.get(raw, raw.replace("_", " ").title())


def _enrich_rationales(state: AnalysisState, tier_name: str) -> dict[str, str]:
    """Build company-specific rationale strings for each posture element from state data."""
    from do_uw.stages.render.formatters import safe_float

    # Gather key facts
    mc_str = ""
    drawdown_str = ""
    active_sca = ""
    top_factor = ""

    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        info = md.get("info", {}) if isinstance(md, dict) else {}
        # Market cap: check info.marketCap, then top-level market_cap
        mc_raw = info.get("marketCap") or md.get("market_cap")
        mc_val = mc_raw.get("value", 0) if isinstance(mc_raw, dict) else safe_float(mc_raw)
        if mc_val and mc_val > 1e6:
            mc_str = f"${mc_val / 1e9:.1f}B" if mc_val >= 1e9 else f"${mc_val / 1e6:.0f}M"

        # 52-week high and current price: check info first
        high_val = info.get("fiftyTwoWeekHigh") or md.get("fifty_two_week_high")
        if isinstance(high_val, dict):
            high_val = high_val.get("value")
        cur_val = info.get("currentPrice") or md.get("current_price")
        if isinstance(cur_val, dict):
            cur_val = cur_val.get("value")
        if high_val and cur_val:
            try:
                dd = (float(cur_val) - float(high_val)) / float(high_val) * 100
                if dd < -10:
                    drawdown_str = f"{abs(dd):.0f}% off 52-week high"
            except (ValueError, ZeroDivisionError, TypeError):
                pass

    if state.extracted and state.extracted.litigation:
        lit = state.extracted.litigation
        # Check multiple possible locations for SCA data
        cases = getattr(lit, "active_cases", None) or []
        if not cases:
            sca = getattr(lit, "securities_class_actions", None) or []
            if isinstance(sca, list):
                cases = sca
        if cases:
            active_sca = f"{len(cases)} active SCA(s)"

    if state.scoring and state.scoring.factor_scores:
        sorted_f = sorted(state.scoring.factor_scores, key=lambda f: f.points_deducted, reverse=True)
        if sorted_f and sorted_f[0].points_deducted > 0:
            tf = sorted_f[0]
            fname = tf.factor_name
            # Dynamic F4 rename: show what actually triggered
            if tf.factor_id in ("F4", "F.4") and fname and "IPO" in fname:
                evidence_text = " ".join(str(e) for e in (tf.evidence or [])).lower()
                contribs = getattr(tf, "signal_contributions", None) or []
                sig_ids = " ".join(
                    str(c.get("signal_id", "") if isinstance(c, dict)
                        else getattr(c, "signal_id", ""))
                    for c in contribs).lower()
                combined = evidence_text + " " + sig_ids
                has_ipo = any(x in combined for x in ["ipo", "section 11", "offering"])
                has_ma = any(x in combined for x in ["m&a", "acquisition", "merger", "goodwill"])
                has_insider = any(x in combined for x in ["insider", "selling", "cluster"])
                if has_insider and not has_ipo and not has_ma:
                    fname = "Insider Trading"
                elif has_ma and not has_ipo:
                    fname = "M&A Exposure"
                elif has_ipo and not has_ma:
                    fname = "IPO Exposure"
                elif has_ipo and has_ma:
                    fname = "IPO & M&A"
            top_factor = f"{fname} ({tf.points_deducted:.0f}/{tf.max_points})"

    qs = f"{state.scoring.quality_score:.0f}" if state.scoring else "N/A"

    # Build per-element
    result: dict[str, str] = {}
    parts = [f"Quality score {qs} ({tier_name})"]
    if active_sca:
        parts.append(active_sca)
    if drawdown_str:
        parts.append(drawdown_str)
    result["decision"] = "; ".join(parts)

    r_parts = []
    if mc_str:
        r_parts.append(f"{mc_str} market cap")
    if drawdown_str:
        r_parts.append(f"stock {drawdown_str}")
    if active_sca:
        r_parts.append("active litigation exposure")
    result["retention"] = "; ".join(r_parts) if r_parts else f"{tier_name} tier"

    p_parts = []
    if top_factor:
        p_parts.append(f"heaviest drag: {top_factor}")
    if drawdown_str:
        p_parts.append(f"stock {drawdown_str}")
    result["pricing"] = "; ".join(p_parts) if p_parts else f"{tier_name} tier pricing"

    l_parts = []
    if mc_str:
        l_parts.append(f"{mc_str} market cap")
    if active_sca:
        l_parts.append("active SCA creates direct loss exposure")
    result["limit"] = "; ".join(l_parts) if l_parts else f"{tier_name} tier capacity"

    e_parts = []
    if active_sca:
        e_parts.append("pending matters exclusion warranted")
    if top_factor:
        e_parts.append(f"targeted exclusions for {top_factor}")
    result["exclusions"] = "; ".join(e_parts) if e_parts else f"{tier_name} tier exclusions"

    m_parts = [f"{tier_name} tier monitoring"]
    if active_sca:
        m_parts.append("track litigation status")
    if drawdown_str:
        m_parts.append("monitor stock recovery")
    result["monitoring"] = "; ".join(m_parts)

    re_parts = [f"{tier_name} tier re-evaluation cycle"]
    if active_sca:
        re_parts.append("accelerated for active litigation")
    result["re_evaluation"] = "; ".join(re_parts)

    return result


def extract_posture(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Extract underwriting posture data for template rendering.

    Reads from state.forward_looking.posture, .zero_verifications,
    and .watch_items to produce humanized element names, override
    details, zero verification evidence, and watch items.

    Returns dict with posture_available, posture_tier, posture_tier_class,
    posture_elements, overrides, zero_verifications, and watch_items.
    """
    fl = state.forward_looking
    posture = fl.posture

    if posture is None:
        return {
            "posture_available": False,
            "posture_tier": "UNKNOWN",
            "posture_tier_class": "posture-unknown",
            "posture_elements": [],
            "overrides_applied": [],
            "has_overrides": False,
            "zero_verifications": [],
            "has_zero_verifications": False,
            "zero_verification_count": 0,
            "watch_items": [],
            "has_watch_items": False,
            "watch_item_count": 0,
        }

    # Format posture elements with humanized names and enriched rationales
    elements: list[dict[str, str]] = []
    enriched = _enrich_rationales(state, posture.tier or "UNKNOWN")
    for elem in posture.elements:
        rationale = elem.rationale or ""
        # Replace generic rationale with company-specific one if available
        if "Based on" in rationale and "tier" in rationale and elem.element in enriched:
            rationale = enriched[elem.element]
        elements.append({
            "element": _humanize_element(elem.element),
            "recommendation": elem.recommendation or "",
            "rationale": rationale,
        })

    # Overrides
    overrides = list(posture.overrides_applied) if posture.overrides_applied else []

    # Zero verifications
    zero_vecs: list[dict[str, str]] = []
    for zv in fl.zero_verifications:
        zero_vecs.append({
            "factor_id": zv.get("factor_id", ""),
            "factor_name": zv.get("factor_name", zv.get("factor_id", "")),
            "points": zv.get("points", ""),
            "evidence": zv.get("evidence", ""),
            "source": zv.get("source", ""),
        })

    # Watch items
    watch_items: list[dict[str, str]] = []
    for wi in fl.watch_items:
        watch_items.append({
            "item": wi.item or "",
            "current_state": wi.current_state or "",
            "threshold": wi.threshold or "",
            "re_evaluation": wi.re_evaluation or "",
            "source": wi.source or "",
        })

    tier = posture.tier or "UNKNOWN"
    return {
        "posture_available": True,
        "posture_tier": tier,
        "posture_tier_class": _TIER_CSS.get(tier, "posture-unknown"),
        "posture_elements": elements,
        "overrides_applied": overrides,
        "has_overrides": len(overrides) > 0,
        "zero_verifications": zero_vecs,
        "has_zero_verifications": len(zero_vecs) > 0,
        "zero_verification_count": len(zero_vecs),
        "watch_items": watch_items,
        "has_watch_items": len(watch_items) > 0,
        "watch_item_count": len(watch_items),
    }
