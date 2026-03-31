"""10-factor scoring engine for D&O underwriting.

Reads scoring.json rules, evaluates F1-F10 against ExtractedData,
produces FactorScore objects with sub-component breakdowns.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.company import CompanyProfile
from do_uw.models.scoring import FactorScore
from do_uw.models.state import ExtractedData
from do_uw.stages.score.factor_data import (
    get_factor_data,
    get_sector_code,
    min_settlement_years,
)
from do_uw.stages.score.factor_rules import rule_matches

logger = logging.getLogger(__name__)

# Re-export for backward compat (tests import _get_sector_code)
_get_sector_code = get_sector_code
_min_settlement_years = min_settlement_years


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def score_all_factors(
    scoring_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
    sectors_config: dict[str, Any],
    analysis_results: dict[str, Any] | None = None,
    signal_results: dict[str, Any] | None = None,
) -> list[FactorScore]:
    """Score all 10 factors and return ordered list of FactorScore.

    When signal_results is provided, each factor tries signal-driven scoring
    first (coverage >= 50%). Falls back to rule-based scoring when coverage
    is insufficient or signal_results is None (backward compatibility).
    """
    factors_cfg = scoring_config.get("factors", {})
    factor_keys = [
        "F1_prior_litigation",
        "F2_stock_decline",
        "F3_restatement_audit",
        "F4_ipo_spac_ma",
        "F5_guidance_misses",
        "F6_short_interest",
        "F7_volatility",
        "F8_financial_distress",
        "F9_governance",
        "F10_officer_stability",
    ]
    results: list[FactorScore] = []
    for key in factor_keys:
        factor_cfg = factors_cfg.get(key, {})
        if not factor_cfg:
            logger.warning("No config found for factor %s", key)
            continue
        score = _score_factor(
            key, factor_cfg, extracted, company, sectors_config,
            analysis_results, signal_results,
        )
        results.append(score)
    return results


# -----------------------------------------------------------------------
# Sector weight adjustment
# -----------------------------------------------------------------------


def _apply_sector_weight(
    max_points: int,
    factor_key: str,
    sectors: dict[str, Any],
    company: CompanyProfile | None,
) -> int:
    """Adjust factor max_points by sector-specific weight multiplier.

    Reads factor_weight_adjustments from sectors.json. A multiplier of
    0.6 means this factor carries 60% of its normal weight for this sector
    (e.g., financial health signals are less meaningful for asset-light tech).
    """
    if company is None:
        return max_points

    adjustments = sectors.get("factor_weight_adjustments", {})
    if not adjustments:
        return max_points

    # Get company sector
    sector = get_sector_code(company)
    sector_adj = adjustments.get(sector, adjustments.get("DEFAULT", {}))
    if not sector_adj:
        return max_points

    multiplier = sector_adj.get(factor_key)
    if multiplier is None or not isinstance(multiplier, (int, float)):
        return max_points

    adjusted = round(max_points * multiplier)
    if adjusted != max_points:
        logger.debug(
            "Sector weight: %s %s max_points %d → %d (×%.1f)",
            sector, factor_key, max_points, adjusted, multiplier,
        )
    return adjusted


# -----------------------------------------------------------------------
# Factor scoring core
# -----------------------------------------------------------------------


def _score_factor(
    factor_key: str,
    factor_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
    sectors: dict[str, Any],
    analysis_results: dict[str, Any] | None = None,
    signal_results: dict[str, Any] | None = None,
) -> FactorScore:
    """Score a single factor against extracted data.

    When signal_results is provided and signal coverage >= 50%,
    the signal-driven path replaces the rule-based base score.
    Factor modifiers (F2 insider amplifier, market cap, F9 dual_class)
    still apply on top of the signal-driven base.
    """
    factor_id = factor_config.get("factor_id", factor_key)
    factor_name = factor_config.get("name", factor_key)
    max_points = int(factor_config.get("max_points", 0))

    # Apply sector-specific factor weight adjustment.
    # E.g., TECH gets F3_financial_health × 0.6 (financial distress metrics
    # are misleading for asset-light tech) while BIOT gets F3 × 1.4 (cash
    # runway is critical for pre-revenue biotech).
    max_points = _apply_sector_weight(max_points, factor_key, sectors, company)

    # Get factor-specific data from extracted (needed for modifiers + fallback)
    data = get_factor_data(
        factor_key, extracted, company, sectors, analysis_results,
    )

    # Try signal-driven scoring path first
    signal_contributions: list[dict[str, Any]] = []
    signal_coverage = 0.0
    scoring_method = "rule_based"
    use_signal_path = False

    if signal_results is not None:
        try:
            from do_uw.stages.score.factor_data_signals import (
                aggregate_factor_from_signals,
            )

            sig_data, sig_contribs = aggregate_factor_from_signals(
                factor_key, signal_results, float(max_points),
            )
            signal_coverage = sig_data.get("signal_coverage", 0.0)
            use_signal_path = sig_data.get("use_signal_path", False)

            if use_signal_path:
                signal_contributions = sig_contribs
                scoring_method = "signal_driven"
        except Exception:
            logger.warning(
                "Signal aggregation failed for %s; falling back to rule-based",
                factor_key,
                exc_info=True,
            )

    if use_signal_path:
        # Signal-driven path: use signal_score as base
        base_points = sig_data["signal_score"]
        evidence: list[str] = [
            f"Signal-driven scoring: {len(signal_contributions)} signals, "
            f"coverage={signal_coverage:.0%}",
        ]
        rules_triggered: list[str] = []
        sub_components: dict[str, float] = {"base": base_points}
    else:
        # Rule-based path (existing logic)
        rules = factor_config.get("rules", [])
        matched_rule, base_points = _find_matching_rule(rules, data, factor_key)
        evidence = []
        rules_triggered = []
        sub_components = {"base": base_points}

        if matched_rule is not None:
            rule_id = str(matched_rule.get("id", ""))
            rules_triggered.append(rule_id)
            evidence.append(str(matched_rule.get("condition", "")))

    # Apply bonuses (both paths)
    bonus_points = _evaluate_bonuses(
        factor_config.get("bonuses", []), data, evidence, rules_triggered
    )
    sub_components["bonus"] = bonus_points

    # Apply factor-specific modifiers (both paths)
    modifier_points = _apply_factor_modifiers(
        factor_key, factor_config, data, evidence, rules_triggered, sub_components
    )

    # Apply hard triggers (F8 has hard_triggers) (both paths)
    hard_trigger_pts = _evaluate_hard_triggers(
        factor_config.get("hard_triggers", []),
        data,
        evidence,
        rules_triggered,
    )
    sub_components["hard_triggers"] = hard_trigger_pts

    total = base_points + bonus_points + modifier_points + hard_trigger_pts

    # Apply insider amplifier for F2 (both paths)
    if factor_key == "F2_stock_decline":
        total = _apply_insider_amplifier(
            factor_config, data, total, evidence, rules_triggered, sub_components
        )

    # Apply market cap multiplier for F2 (both paths)
    if factor_key == "F2_stock_decline":
        total = _apply_market_cap_multiplier(
            factor_config.get("market_cap_multipliers"),
            company,
            total,
            sub_components,
        )

    # Apply drop contribution modifier for F2 (both paths)
    if factor_key == "F2_stock_decline":
        total = _apply_drop_contribution_modifier(
            factor_config, data, total, evidence, rules_triggered, sub_components
        )

    # Cap at max_points
    capped = min(total, float(max_points))
    if capped < 0:
        capped = 0.0
    sub_components["total_before_cap"] = total
    sub_components["capped"] = capped

    return FactorScore(
        factor_name=factor_name,
        factor_id=factor_id.replace(".", ""),
        max_points=max_points,
        points_deducted=capped,
        evidence=evidence,
        rules_triggered=rules_triggered,
        sub_components=sub_components,
        signal_contributions=signal_contributions,
        signal_coverage=signal_coverage,
        scoring_method=scoring_method,
    )


# -----------------------------------------------------------------------
# Rule matching
# -----------------------------------------------------------------------


def _find_matching_rule(
    rules: list[dict[str, Any]],
    data: dict[str, Any],
    factor_key: str,
) -> tuple[dict[str, Any] | None, float]:
    """Evaluate rules and return the highest-triggered rule + points.

    Rules are evaluated in order (scoring.json has them highest-first).
    We find ALL matching rules and return the one with highest points.
    """
    best_rule: dict[str, Any] | None = None
    best_points: float = 0.0

    for rule in rules:
        points = float(rule.get("points", 0))
        if rule_matches(rule, data, factor_key):
            if points > best_points or best_rule is None:
                best_rule = rule
                best_points = points

    return best_rule, best_points


# -----------------------------------------------------------------------
# Bonus, modifier, and hard trigger evaluation
# -----------------------------------------------------------------------


def _evaluate_bonuses(
    bonuses: list[dict[str, Any]],
    data: dict[str, Any],
    evidence: list[str],
    rules_triggered: list[str],
) -> float:
    """Evaluate bonus conditions and return total bonus points."""
    total = 0.0
    for bonus in bonuses:
        bonus_id = str(bonus.get("id", ""))
        condition = str(bonus.get("condition", "")).lower()
        points = float(bonus.get("points", 0))

        triggered = False
        # F2 bonuses
        if "underperformed sector" in condition:
            peer_perf = data.get("peer_underperformance_ppts", 0.0)
            triggered = peer_perf > 20
        elif "event-window" in condition:
            # Check for significant event-window decline
            triggered = False  # Deferred to pattern modifiers in 06-04
        # F5 bonuses
        elif "single miss >15%" in condition or "single_miss_gt_15" in condition:
            max_miss = data.get("max_miss_magnitude", 0.0)
            triggered = max_miss > 15.0

        if triggered:
            total += points
            rules_triggered.append(bonus_id)
            evidence.append(str(bonus.get("condition", "")))

    return total


def _evaluate_hard_triggers(
    hard_triggers: list[dict[str, Any]],
    data: dict[str, Any],
    evidence: list[str],
    rules_triggered: list[str],
) -> float:
    """Evaluate hard trigger conditions (F8)."""
    total = 0.0
    for trigger in hard_triggers:
        trigger_id = str(trigger.get("id", ""))
        condition = str(trigger.get("condition", "")).lower()
        points = float(trigger.get("points", trigger.get("minimum_points", 0)))

        triggered = False
        if "going concern" in condition:
            triggered = data.get("going_concern", False)
        elif "covenant breach" in condition or "covenant" in condition:
            triggered = data.get("covenant_breach", False)
        elif "missed debt" in condition:
            triggered = data.get("missed_debt_payment", False)
        elif "credit rating downgrade" in condition:
            triggered = data.get("credit_downgrade_junk", False)

        if triggered:
            total += points
            rules_triggered.append(trigger_id)
            evidence.append(str(trigger.get("condition", "")))

    return total


def _apply_factor_modifiers(
    factor_key: str,
    factor_config: dict[str, Any],
    data: dict[str, Any],
    evidence: list[str],
    rules_triggered: list[str],
    sub_components: dict[str, float],
) -> float:
    """Apply factor-specific modifiers (trend, cash runway, etc.)."""
    total = 0.0

    # F6: market cap modifiers + trend modifiers
    if factor_key == "F6_short_interest":
        total += _eval_modifier_list(
            factor_config.get("market_cap_modifiers", []),
            data,
            "market_cap_b",
            evidence,
            rules_triggered,
        )
        total += _eval_modifier_list(
            factor_config.get("trend_modifiers", []),
            data,
            "si_trend_change_pct",
            evidence,
            rules_triggered,
        )
        # Short report override
        for override in factor_config.get("short_report_override", []):
            oid = str(override.get("id", ""))
            if oid == "F6-X01" and data.get("short_report_months", 999) < 6:
                min_pts = float(override.get("minimum_points", 0))
                sub_components["short_report_override"] = min_pts
                rules_triggered.append(oid)
                evidence.append("Named short report <6 months")
            elif oid == "F6-X02" and 6 <= data.get("short_report_months", 999) < 12:
                min_pts = float(override.get("minimum_points", 0))
                sub_components["short_report_override_6_12"] = min_pts
                rules_triggered.append(oid)
                evidence.append("Named short report 6-12 months")

    # F7: trend modifiers + extreme events
    if factor_key == "F7_volatility":
        total += _eval_modifier_list(
            factor_config.get("trend_modifiers", []),
            data,
            "vol_trend_change_pct",
            evidence,
            rules_triggered,
        )
        total += _eval_modifier_list(
            factor_config.get("extreme_events", []),
            data,
            "extreme_days",
            evidence,
            rules_triggered,
        )

    # F8: cash runway + trend modifiers
    if factor_key == "F8_financial_distress":
        total += _eval_cash_runway(
            factor_config.get("cash_runway", []),
            data,
            evidence,
            rules_triggered,
        )
        total += _eval_modifier_list(
            factor_config.get("trend_modifiers", []),
            data,
            "f8_trend",
            evidence,
            rules_triggered,
        )

    # F9: dual_class_override
    if factor_key == "F9_governance":
        dc_override = factor_config.get("dual_class_override")
        if dc_override and data.get("dual_class", False):
            pts = float(dc_override.get("points", 0))
            total += pts
            evidence.append("Dual-class structure")
            rules_triggered.append("F9-DC")
            sub_components["dual_class"] = pts

    sub_components["modifiers"] = total
    return total


# -----------------------------------------------------------------------
# Insider amplifier and market cap multiplier (F2-specific)
# -----------------------------------------------------------------------


def _apply_insider_amplifier(
    factor_config: dict[str, Any],
    data: dict[str, Any],
    current_total: float,
    evidence: list[str],
    rules_triggered: list[str],
    sub_components: dict[str, float],
) -> float:
    """Apply F2 insider trading amplifier multiplier."""
    amplifier_cfg = factor_config.get("insider_amplifier", {})
    multipliers = amplifier_cfg.get("multipliers", [])
    insider_data = data.get("insider_amplifier_data", {})

    best_multiplier = 1.0
    best_id = ""

    cluster_selling = insider_data.get("cluster_selling", False)
    heavy_selling = insider_data.get("heavy_selling", False)
    pre_announcement = insider_data.get("pre_announcement_selling", False)

    for mult in multipliers:
        mult_id = str(mult.get("id", ""))
        mult_val = float(mult.get("multiplier", 1.0))
        condition = str(mult.get("condition", "")).lower()

        matched = False
        if "pre-announcement" in condition and pre_announcement:
            matched = True
        elif "cluster" in condition and cluster_selling:
            matched = True
        elif "heavy selling" in condition and heavy_selling:
            matched = True

        if matched and mult_val > best_multiplier:
            best_multiplier = mult_val
            best_id = mult_id

    if best_multiplier > 1.0:
        amplified = current_total * best_multiplier
        sub_components["insider_multiplier"] = best_multiplier
        sub_components["pre_amplifier"] = current_total
        sub_components["post_amplifier"] = amplified
        evidence.append(f"Insider amplifier: {best_multiplier}x")
        rules_triggered.append(best_id)
        return amplified

    return current_total


def _apply_market_cap_multiplier(
    mktcap_config: dict[str, Any] | None,
    company: CompanyProfile | None,
    current_total: float,
    sub_components: dict[str, float],
) -> float:
    """Apply market cap multiplier from scoring.json market_cap_multipliers."""
    if mktcap_config is None or company is None:
        return current_total

    # market_cap_multipliers may be a list of tier dicts
    tiers: list[dict[str, Any]]
    if isinstance(mktcap_config, list):
        tiers = cast(list[dict[str, Any]], mktcap_config)
    else:
        tiers = []
    if not tiers:
        return current_total

    mktcap_sv = company.market_cap
    if mktcap_sv is None:
        return current_total
    mktcap_b = mktcap_sv.value / 1e9

    for tier_entry in tiers:
        min_b = float(tier_entry.get("min_cap_b", 0))
        max_b_raw = tier_entry.get("max_cap_b")
        max_b_f = float("inf") if max_b_raw is None else float(max_b_raw)
        if min_b <= mktcap_b < max_b_f:
            mult = float(tier_entry.get("multiplier", 1.0))
            result = current_total * mult
            sub_components["mktcap_multiplier"] = mult
            return result

    return current_total


# -----------------------------------------------------------------------
# Drop contribution modifier (Phase 90: decay + company-specific + disclosure)
# -----------------------------------------------------------------------


def _apply_drop_contribution_modifier(
    factor_config: dict[str, Any],
    data: dict[str, Any],
    current_total: float,
    evidence: list[str],
    rules_triggered: list[str],
    sub_components: dict[str, float],
) -> float:
    """Apply decay, company-specific, and disclosure modifiers from individual drops.

    Each drop's contribution is: magnitude * decay_weight * company_pct_ratio * disclosure_mult
    The overall modifier is the ratio of weighted sum to raw sum, applied to current_total.

    This adjusts F2 so that:
    - Recent drops score higher than old ones (decay_weight)
    - Company-specific drops score higher than market-driven ones (company_pct_ratio)
    - Drops with corrective disclosures get 1.5x uplift (disclosure_mult)
    """
    contributions = data.get("drop_contributions", [])
    if not contributions:
        return current_total

    raw_sum = sum(c["magnitude"] for c in contributions)
    if raw_sum <= 0:
        return current_total

    weighted_sum = 0.0
    for c in contributions:
        disclosure_mult = 1.5 if c["has_disclosure"] else 1.0
        weighted = c["magnitude"] * c["decay_weight"] * c["company_pct_ratio"] * disclosure_mult
        weighted_sum += weighted

    modifier = weighted_sum / raw_sum
    adjusted = current_total * modifier

    sub_components["drop_contribution_modifier"] = round(modifier, 3)
    evidence.append(f"Drop contribution modifier: {modifier:.2f}x (decay + company-specific + disclosure)")
    if modifier != 1.0:
        rules_triggered.append("drop_contribution_adjustment")

    return adjusted


# -----------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------


def _eval_modifier_list(
    modifiers: list[dict[str, Any]],
    data: dict[str, Any],
    _data_key: str,
    evidence: list[str],
    rules_triggered: list[str],
) -> float:
    """Evaluate a list of modifier rules (trend, market cap, extreme)."""
    # These modifiers have condition strings we need to interpret
    # For now, return 0 -- detailed modifier matching deferred to data availability
    _ = modifiers, data, _data_key, evidence, rules_triggered
    return 0.0


def _eval_cash_runway(
    cash_runway_rules: list[dict[str, Any]],
    data: dict[str, Any],
    evidence: list[str],
    rules_triggered: list[str],
) -> float:
    """Evaluate F8 cash runway rules against data."""
    months = data.get("cash_runway_months", 999)
    if months >= 999:
        # No cash runway data available -- do not penalize
        return 0.0

    best_points = 0.0
    for rule in cash_runway_rules:
        rule_id = str(rule.get("id", ""))
        points = float(rule.get("points", 0))

        if _match_cash_runway_condition(rule_id, months):
            if points > best_points:
                best_points = points
                if points > 0:
                    rules_triggered.append(rule_id)
                    evidence.append(
                        str(
                            rule.get(
                                "condition",
                                f"Cash runway: {months:.0f} months",
                            )
                        )
                    )

    return best_points


def _match_cash_runway_condition(rule_id: str, months: float) -> bool:
    """Match F8 cash runway rule by ID."""
    if rule_id == "F8-C01":
        return months < 6
    if rule_id == "F8-C02":
        return 6 <= months < 12
    if rule_id == "F8-C03":
        return 12 <= months < 18
    if rule_id == "F8-C04":
        return months >= 18
    return False
