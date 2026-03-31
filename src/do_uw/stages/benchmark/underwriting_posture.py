"""Underwriting posture engine -- algorithmic posture from scoring tier + brain YAML.

Produces PostureRecommendation, ZER-001 zero-factor verifications, and watch items.
All posture logic reads from brain YAML -- no hardcoded mappings. Phase 117-03.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from do_uw.models.forward_looking import (
    PostureElement,
    PostureRecommendation,
    WatchItem,
)
from do_uw.models.scoring import ScoringResult
from do_uw.models.state import AnalysisState

_posture_config_cache: dict[str, Any] | None = None


def load_posture_config() -> dict[str, Any]:
    """Load posture decision matrix from brain/config/underwriting_posture.yaml."""
    global _posture_config_cache
    if _posture_config_cache is not None:
        return _posture_config_cache

    config_path = (
        Path(__file__).parent.parent.parent / "brain" / "config" / "underwriting_posture.yaml"
    )
    with open(config_path) as f:
        _posture_config_cache = yaml.safe_load(f)
    return _posture_config_cache


def _reset_config_cache() -> None:
    """Clear config cache (for testing)."""
    global _posture_config_cache
    _posture_config_cache = None


_POSTURE_ELEMENTS = [
    "decision",
    "retention",
    "limit",
    "pricing",
    "exclusions",
    "monitoring",
    "re_evaluation",
]


def _get_factor_score(scoring_result: ScoringResult, factor_id: str) -> float:
    """Look up points_deducted for a factor by factor_id (e.g., 'F.1')."""
    for fs in scoring_result.factor_scores:
        if fs.factor_id == factor_id:
            return fs.points_deducted
    return 0.0


def _parse_condition(condition: str) -> tuple[str, str, float]:
    """Parse 'F1 > 0' into (factor_shorthand, op, threshold)."""
    parts = condition.strip().split()
    if len(parts) != 3:
        return ("", ">", 0.0)
    factor_short, op, threshold_str = parts
    try:
        threshold = float(threshold_str)
    except ValueError:
        threshold = 0.0
    return (factor_short, op, threshold)


def _eval_condition(
    scoring_result: ScoringResult,
    override: dict[str, Any],
) -> bool:
    """Evaluate whether a factor override condition is met."""
    # Use the explicit factor_id field if available, otherwise parse from condition
    factor_id = override.get("factor_id", "")
    if not factor_id:
        # Fall back to parsing "F1 > 0" style condition
        short, _op, threshold = _parse_condition(override.get("condition", ""))
        # Convert F1 -> F.1 etc.
        if short and short[0] == "F" and len(short) > 1:
            factor_id = f"F.{short[1:]}"
        else:
            return False
    else:
        _, _op, threshold = _parse_condition(override.get("condition", ""))

    score = _get_factor_score(scoring_result, factor_id)

    if _op == ">":
        return score > threshold
    if _op == ">=":
        return score >= threshold
    return score > threshold  # default to >


def _build_element_rationales(
    scoring_result: ScoringResult,
    state: AnalysisState,
    tier_name: str,
) -> dict[str, str]:
    """Build company-specific rationales for each posture element using actual risk data."""
    # Gather key risk facts from state
    market_cap_str = ""
    drawdown_str = ""
    active_sca = ""
    insider_selling = ""
    quality_score = f"{scoring_result.quality_score:.0f}"

    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        mc = md.get("market_cap")
        if mc and isinstance(mc, dict):
            mc_val = mc.get("value", 0)
        elif isinstance(mc, (int, float)):
            mc_val = mc
        else:
            mc_val = 0
        if mc_val and mc_val > 0:
            if mc_val >= 1e9:
                market_cap_str = f"${mc_val / 1e9:.1f}B"
            else:
                market_cap_str = f"${mc_val / 1e6:.0f}M"

        # Drawdown
        high_52w = md.get("fifty_two_week_high")
        if isinstance(high_52w, dict):
            high_52w = high_52w.get("value")
        current = md.get("current_price")
        if isinstance(current, dict):
            current = current.get("value")
        if high_52w and current:
            try:
                dd = (float(current) - float(high_52w)) / float(high_52w) * 100
                if dd < -10:
                    drawdown_str = f"{abs(dd):.0f}% off 52-week high"
            except (ValueError, ZeroDivisionError, TypeError):
                pass

    # Active litigation
    if state.extracted and state.extracted.litigation:
        lit = state.extracted.litigation
        cases = getattr(lit, "active_cases", None) or []
        if cases:
            active_sca = f"{len(cases)} active case(s)"

    # Top factor drag
    top_factor = ""
    if scoring_result.factor_scores:
        sorted_factors = sorted(
            scoring_result.factor_scores, key=lambda f: f.points_deducted, reverse=True
        )
        if sorted_factors and sorted_factors[0].points_deducted > 0:
            tf = sorted_factors[0]
            top_factor = f"{tf.factor_name} ({tf.points_deducted:.0f}/{tf.max_points})"

    # Build per-element rationales
    decision_parts = [f"Quality score {quality_score} ({tier_name})"]
    if active_sca:
        decision_parts.append(active_sca)
    if drawdown_str:
        decision_parts.append(drawdown_str)

    retention_parts = []
    if market_cap_str:
        retention_parts.append(f"{market_cap_str} market cap")
    if drawdown_str:
        retention_parts.append(f"stock {drawdown_str}")
    if active_sca:
        retention_parts.append("active litigation exposure")
    if not retention_parts:
        retention_parts.append(f"{tier_name} tier risk profile")

    pricing_parts = []
    if top_factor:
        pricing_parts.append(f"heaviest drag: {top_factor}")
    if drawdown_str:
        pricing_parts.append(f"stock {drawdown_str}")
    if not pricing_parts:
        pricing_parts.append(f"{tier_name} tier pricing guidance")

    limit_parts = []
    if market_cap_str:
        limit_parts.append(f"{market_cap_str} market cap")
    if active_sca:
        limit_parts.append("active SCA creates direct loss exposure")
    if not limit_parts:
        limit_parts.append(f"{tier_name} tier capacity guidance")

    exclusion_parts = []
    if active_sca:
        exclusion_parts.append("pending matters exclusion warranted")
    if top_factor:
        exclusion_parts.append(f"targeted exclusions for {top_factor}")
    if not exclusion_parts:
        exclusion_parts.append(f"{tier_name} tier exclusion guidance")

    monitoring_parts = [f"{tier_name} tier requires ongoing monitoring"]
    if active_sca:
        monitoring_parts.append("track litigation status")
    if drawdown_str:
        monitoring_parts.append("monitor stock recovery")

    reeval_parts = [f"{tier_name} tier re-evaluation cycle"]
    if active_sca:
        reeval_parts.append("accelerated for active litigation")

    return {
        "decision": "; ".join(decision_parts),
        "retention": "; ".join(retention_parts),
        "pricing": "; ".join(pricing_parts),
        "limit": "; ".join(limit_parts),
        "exclusions": "; ".join(exclusion_parts),
        "monitoring": "; ".join(monitoring_parts),
        "re_evaluation": "; ".join(reeval_parts),
    }


def generate_posture(
    scoring_result: ScoringResult,
    state: AnalysisState,
) -> PostureRecommendation:
    """Derive underwriting posture from scoring tier + factor overrides + nuclear escalation."""
    config = load_posture_config()
    posture_matrix = config.get("posture_matrix", {})

    # Determine tier name
    tier_name = "WRITE"  # default fallback
    if scoring_result.tier is not None:
        tier_val = scoring_result.tier.tier
        tier_name = tier_val.value if hasattr(tier_val, "value") else str(tier_val)

    # Build base posture from matrix
    base = posture_matrix.get(tier_name, posture_matrix.get("WRITE", {}))

    # Generate company-specific rationales per element
    rationales = _build_element_rationales(scoring_result, state, tier_name)

    elements: list[PostureElement] = []
    for elem_key in _POSTURE_ELEMENTS:
        recommendation = base.get(elem_key, "")
        elements.append(
            PostureElement(
                element=elem_key,
                recommendation=recommendation,
                rationale=rationales.get(elem_key, f"{tier_name} tier"),
            )
        )

    overrides_applied: list[str] = []

    # Apply factor overrides
    factor_overrides = config.get("factor_overrides", [])
    for override in factor_overrides:
        if _eval_condition(scoring_result, override):
            desc = override.get("description", override.get("condition", ""))
            factor_id = override.get("factor_id", "")
            override_rationale = override.get("rationale", desc)

            # Apply exclusion addition
            add_exclusion = override.get("add_exclusion", "")
            if add_exclusion:
                _append_to_element(elements, "exclusions", add_exclusion)
                overrides_applied.append(
                    f"{factor_id}: {add_exclusion}"
                )

            # Apply monitoring addition
            add_monitoring = override.get("add_monitoring", "")
            if add_monitoring:
                _append_to_element(elements, "monitoring", add_monitoring)
                if not add_exclusion:
                    # Only record once if both exclusion and monitoring
                    overrides_applied.append(
                        f"{factor_id}: {add_monitoring}"
                    )

            # Update relevant element rationales with override-specific context
            for elem in elements:
                if elem.element in ("exclusions", "monitoring"):
                    if factor_id in (o.split(":")[0] for o in overrides_applied):
                        elem.rationale = override_rationale

    # Nuclear trigger escalation
    _apply_nuclear_escalation(config, state, elements, overrides_applied, tier_name)

    return PostureRecommendation(
        tier=tier_name,
        elements=elements,
        overrides_applied=overrides_applied,
    )


def _append_to_element(
    elements: list[PostureElement],
    element_name: str,
    addition: str,
) -> None:
    """Append text to an existing element's recommendation."""
    for elem in elements:
        if elem.element == element_name:
            if elem.recommendation and elem.recommendation != "N/A":
                elem.recommendation = f"{elem.recommendation}; {addition}"
            else:
                elem.recommendation = addition
            return


def _apply_nuclear_escalation(
    config: dict[str, Any],
    state: AnalysisState,
    elements: list[PostureElement],
    overrides_applied: list[str],
    tier_name: str,
) -> None:
    """Add nuclear trigger escalation if any nuclear trigger fired."""
    nuclear_config = config.get("nuclear_escalation", {})
    if not nuclear_config:
        return

    quick_screen = state.forward_looking.quick_screen
    if quick_screen is None:
        return

    fired = [nt for nt in quick_screen.nuclear_triggers if nt.fired]
    if not fired:
        return

    message = nuclear_config.get("message", "NUCLEAR TRIGGER FIRED")
    override_monitoring = nuclear_config.get("override_monitoring", "Immediate daily monitoring")
    override_re_eval = nuclear_config.get("override_re_evaluation", "Immediate")

    for elem in elements:
        if elem.element == "monitoring":
            elem.recommendation = override_monitoring
            elem.rationale = f"Nuclear trigger override ({tier_name}): {message}"
        elif elem.element == "re_evaluation":
            elem.recommendation = override_re_eval
            elem.rationale = f"Nuclear trigger override ({tier_name}): {message}"

    trigger_names = ", ".join(nt.name for nt in fired)
    overrides_applied.append(f"NUCLEAR: {trigger_names}")


# ZER-001: Factor-specific positive evidence templates
_ZERO_EVIDENCE: dict[str, str] = {
    "F.1": "Stanford SCAC clean, no SEC enforcement, no derivative suits",
    "F.2": "Stock price within normal range, no significant decline from 52-week high",
    "F.3": "No restatement history, no material weakness, clean audit opinion",
    "F.4": "No recent IPO, SPAC merger, or major M&A activity",
    "F.5": "Consistent guidance track record, no significant earnings misses",
    "F.6": "Short interest within normal range",
    "F.7": "Stock volatility within normal range",
    "F.8": "No financial distress indicators, healthy balance sheet metrics",
    "F.9": "No SEC enforcement, no regulatory proceedings, clean governance",
    "F.10": "Stable officer team, no recent departures",
}


def verify_zero_factors(
    scoring_result: ScoringResult,
    state: AnalysisState,
) -> list[dict[str, str]]:
    """ZER-001: For each zero-scored factor, build positive evidence of WHY it is clean."""
    verifications: list[dict[str, str]] = []

    for factor in scoring_result.factor_scores:
        if factor.points_deducted > 0:
            continue

        evidence = _ZERO_EVIDENCE.get(
            factor.factor_id,
            f"Factor scored 0/{factor.max_points} -- no issues detected",
        )

        # Enrich evidence from state data where available
        evidence = _enrich_zero_evidence(factor.factor_id, evidence, state)

        source = _get_zero_evidence_source(factor.factor_id)

        verifications.append({
            "factor_id": factor.factor_id,
            "factor_name": factor.factor_name,
            "points": f"0/{factor.max_points}",
            "evidence": evidence,
            "source": source,
        })

    return verifications


def _enrich_zero_evidence(
    factor_id: str,
    base_evidence: str,
    state: AnalysisState,
) -> str:
    """Enrich evidence with actual state data where available."""
    if factor_id == "F.1" and state.extracted and state.extracted.litigation:
        lit = state.extracted.litigation
        if hasattr(lit, "active_cases") and not lit.active_cases:
            return "Stanford SCAC clean, no active securities class actions, no SEC enforcement"

    if factor_id == "F.3" and state.extracted and state.extracted.financials:
        audit = state.extracted.financials.audit
        if audit and hasattr(audit, "going_concern"):
            gc = audit.going_concern
            gc_val = gc.value if hasattr(gc, "value") and gc is not None else gc
            if not gc_val:
                return "No restatement history, no material weakness, clean audit opinion, no going concern"

    return base_evidence


def _get_zero_evidence_source(factor_id: str) -> str:
    """Get the data source for a zero-factor verification."""
    sources: dict[str, str] = {
        "F.1": "Stanford SCAC database, SEC EDGAR",
        "F.2": "yfinance stock data",
        "F.3": "10-K audit opinion, SEC filings",
        "F.4": "SEC EDGAR filings, company profile",
        "F.5": "yfinance earnings data, 8-K filings",
        "F.6": "yfinance short interest data",
        "F.7": "yfinance stock data",
        "F.8": "10-K financial statements",
        "F.9": "SEC EDGAR enforcement, DEF 14A proxy",
        "F.10": "8-K Item 5.02 filings, DEF 14A proxy",
    }
    return sources.get(factor_id, "Multiple sources")



def generate_watch_items(
    scoring_result: ScoringResult,
    state: AnalysisState,
) -> list[WatchItem]:
    """Identify factors >=50% deduction and HIGH miss-risk forward statements."""
    items: list[WatchItem] = []

    for factor in scoring_result.factor_scores:
        if factor.points_deducted <= 0:
            continue

        ratio = factor.points_deducted / factor.max_points if factor.max_points > 0 else 0
        if ratio < 0.5:
            continue

        # Significant deduction -- add watch item
        is_high = ratio >= 0.75
        threshold = _get_factor_watch_threshold(factor.factor_id)
        re_eval = "Monthly" if is_high else "Quarterly"

        items.append(
            WatchItem(
                item=f"{factor.factor_id} {factor.factor_name}: {factor.points_deducted:.0f}/{factor.max_points} deducted",
                current_state=f"{factor.points_deducted:.0f}/{factor.max_points} points deducted ({ratio:.0%} of maximum)",
                threshold=threshold,
                re_evaluation=re_eval,
                source="10-factor scoring model",
            )
        )

    # Forward-looking: HIGH miss risk statements
    for stmt in state.forward_looking.forward_statements:
        if stmt.miss_risk == "HIGH":
            items.append(
                WatchItem(
                    item=f"Forward guidance risk: {stmt.metric_name}",
                    current_state=f"Miss risk HIGH -- {stmt.miss_risk_rationale}" if stmt.miss_risk_rationale else "Miss risk HIGH",
                    threshold="Actual vs guidance divergence >10%",
                    re_evaluation="Quarterly",
                    source=stmt.source_filing or "Forward statement extraction",
                )
            )

    return items


def _get_factor_watch_threshold(factor_id: str) -> str:
    """Get a factor-specific threshold description for watch items."""
    thresholds: dict[str, str] = {
        "F.1": "Any new litigation filing or SEC enforcement action",
        "F.2": "Additional 10%+ decline from current level",
        "F.3": "Any new restatement, material weakness, or auditor change",
        "F.4": "Additional M&A activity or SPAC-related developments",
        "F.5": "Next quarterly earnings vs guidance",
        "F.6": "Short interest increase >50% from current level",
        "F.7": "Sustained volatility increase above current level",
        "F.8": "Deterioration in key financial distress indicators",
        "F.9": "Any new regulatory action or governance concern",
        "F.10": "Any C-suite departure announcement",
    }
    return thresholds.get(factor_id, "Significant change from current state")


__all__ = [
    "generate_posture",
    "generate_watch_items",
    "load_posture_config",
    "verify_zero_factors",
]
