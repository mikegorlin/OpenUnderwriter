"""Loss severity modeling, tower positioning, and red flag summary.

SECT7-08: Loss severity scenarios at 25th/50th/75th/95th percentiles.
SECT7-09: Tower position recommendation with Side A assessment.
SECT7-10: Red flag summary consolidating all flagged items by severity.

All parameters are config-driven from brain/scoring.json with
needs_calibration=True per SECT7-11.

Phase 27: model_severity() is now the FALLBACK path. The primary path
is predict_settlement() from settlement_prediction.py, which uses
DDL-based estimation from stock drops. model_severity() is used when
stock drops are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.scoring import (
    FactorScore,
    PatternMatch,
    RedFlagResult,
    Tier,
    TierClassification,
)
from do_uw.models.scoring_output import (
    AllegationMapping,
    FlaggedItem,
    FlagSeverity,
    LayerAssessment,
    RedFlagSummary,
    SeverityScenario,
    SeverityScenarios,
    TowerPosition,
    TowerRecommendation,
)
from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

_DEFENSE_COST_PCTS = [0.15, 0.20, 0.25, 0.30]
_SCENARIO_LABELS = ["favorable", "median", "adverse", "catastrophic"]
_SCENARIO_PERCENTILES = [25, 50, 75, 95]

_TIER_POSITION_MAP: dict[Tier, TowerPosition] = {
    Tier.WIN: TowerPosition.PRIMARY,
    Tier.WANT: TowerPosition.PRIMARY,
    Tier.WRITE: TowerPosition.LOW_EXCESS,
    Tier.WATCH: TowerPosition.MID_EXCESS,
    Tier.WALK: TowerPosition.HIGH_EXCESS,
    Tier.NO_TOUCH: TowerPosition.DECLINE,
}

_PATTERN_SEVERITY_MAP: dict[str, FlagSeverity] = {
    "SEVERE": FlagSeverity.HIGH,
    "HIGH": FlagSeverity.HIGH,
    "ELEVATED": FlagSeverity.MODERATE,
    "BASELINE": FlagSeverity.LOW,
}


# -----------------------------------------------------------------------
# SECT7-08: Loss severity modeling
# -----------------------------------------------------------------------


def model_severity(
    market_cap: float | None,
    tier: TierClassification,
    scoring_config: dict[str, Any],
) -> SeverityScenarios | None:
    """Model loss severity at 4 percentile scenarios.

    Returns None if market_cap is unavailable.
    """
    if market_cap is None:
        return None

    decline_scenarios = {
        "10%": market_cap * 0.10,
        "20%": market_cap * 0.20,
        "30%": market_cap * 0.30,
    }
    base_low_m, base_high_m = _lookup_base_range(market_cap, scoring_config)
    mult_low, mult_high = _lookup_tier_multiplier(tier.tier, scoring_config)
    scenarios = _compute_percentile_scenarios(
        base_low_m, base_high_m, mult_low, mult_high
    )
    return SeverityScenarios(
        market_cap=market_cap,
        decline_scenarios=decline_scenarios,
        scenarios=scenarios,
        needs_calibration=True,
    )


def _lookup_base_range(
    market_cap: float, scoring_config: dict[str, Any],
) -> tuple[float, float]:
    """Look up base settlement range (low_m, high_m) by market cap."""
    by_cap = scoring_config.get("severity_ranges", {}).get("by_market_cap", [])
    cap_b = market_cap / 1e9

    for entry in by_cap:
        min_b = entry.get("min_cap_b", 0)
        max_b = entry.get("max_cap_b")
        if max_b is None:
            if cap_b >= min_b:
                base = entry.get("base_range_m", [10, 50])
                return float(base[0]), float(base[1])
        elif min_b <= cap_b < max_b:
            base = entry.get("base_range_m", [10, 50])
            return float(base[0]), float(base[1])

    if by_cap:
        base = by_cap[-1].get("base_range_m", [2, 10])
        return float(base[0]), float(base[1])
    return 5.0, 25.0


def _lookup_tier_multiplier(
    tier: Tier, scoring_config: dict[str, Any],
) -> tuple[float, float]:
    """Look up (low, high) tier multiplier. Defaults to (1.0, 1.0)."""
    tier_mults = scoring_config.get("severity_ranges", {}).get("tier_multipliers", [])
    for entry in tier_mults:
        if entry.get("quality_tier", "") == tier.value:
            mult = entry.get("multiplier")
            if mult is None:
                return 1.0, 1.0
            return float(mult[0]), float(mult[1])
    return 1.0, 1.0


def _compute_percentile_scenarios(
    base_low_m: float, base_high_m: float, mult_low: float, mult_high: float,
) -> list[SeverityScenario]:
    """Compute 4 percentile scenarios from base range and multipliers."""
    s_25 = base_low_m * mult_low * 1e6
    avg_base = (base_low_m + base_high_m) / 2.0
    avg_mult = (mult_low + mult_high) / 2.0
    s_50 = avg_base * avg_mult * 1e6
    s_75 = base_high_m * mult_high * 1e6
    s_95 = s_75 * 2.0
    settlements = [s_25, s_50, s_75, s_95]
    scenarios: list[SeverityScenario] = []
    for i, (pct, label) in enumerate(
        zip(_SCENARIO_PERCENTILES, _SCENARIO_LABELS, strict=True)
    ):
        settlement = settlements[i]
        defense = settlement * _DEFENSE_COST_PCTS[i]
        scenarios.append(SeverityScenario(
            percentile=pct, label=label,
            settlement_estimate=settlement,
            defense_cost_estimate=defense,
            total_exposure=settlement + defense,
        ))
    return scenarios


# -----------------------------------------------------------------------
# SECT7-09: Tower position recommendation
# -----------------------------------------------------------------------


def recommend_tower(
    tier: TierClassification,
    severity: SeverityScenarios | None,
    extracted: ExtractedData,
    scoring_config: dict[str, Any],
    tower_risk_data: dict[str, Any] | None = None,
) -> TowerRecommendation:
    """Recommend tower position based on tier and severity analysis.

    Args:
        tier: Tier classification result.
        severity: Severity scenarios (DDL-based or tier-based).
        extracted: Extracted data for Side A assessment.
        scoring_config: Scoring config with tower_positions.
        tower_risk_data: Optional per-layer risk characterization from
            characterize_tower_risk(). When provided, enriches layer
            assessments with expected loss share percentages.
    """
    recommended = _TIER_POSITION_MAP.get(tier.tier, TowerPosition.DECLINE)
    min_attachment = _compute_minimum_attachment(severity)
    layers = _build_layer_assessments(scoring_config, tower_risk_data)
    side_a = _assess_side_a(extracted)
    return TowerRecommendation(
        recommended_position=recommended,
        minimum_attachment=min_attachment,
        layers=layers,
        side_a_assessment=side_a,
        needs_calibration=True,
    )


def _compute_minimum_attachment(severity: SeverityScenarios | None) -> str:
    """Compute minimum attachment from severity 50th percentile."""
    if severity is None or not severity.scenarios:
        return "Insufficient data for attachment calculation"
    for scenario in severity.scenarios:
        if scenario.percentile == 50:
            amt = scenario.settlement_estimate
            if amt >= 1e6:
                return f"${amt / 1e6:.1f}M (based on 50th percentile settlement)"
            return f"${amt:,.0f} (based on 50th percentile settlement)"
    return "Insufficient data for attachment calculation"


def _build_layer_assessments(
    scoring_config: dict[str, Any],
    tower_risk_data: dict[str, Any] | None = None,
) -> list[LayerAssessment]:
    """Build layer assessments from tower_positions config.

    When tower_risk_data is provided (from characterize_tower_risk),
    enriches risk_assessment with per-layer expected loss share.
    """
    position_list = scoring_config.get("tower_positions", {}).get("positions", [])
    layers: list[LayerAssessment] = []

    # Map TowerPosition to layer_type keys in tower_risk_data
    _position_to_layer_type: dict[TowerPosition, str] = {
        TowerPosition.PRIMARY: "primary",
        TowerPosition.LOW_EXCESS: "low_excess",
        TowerPosition.MID_EXCESS: "mid_excess",
        TowerPosition.HIGH_EXCESS: "high_excess",
    }

    for entry in position_list:
        try:
            position = TowerPosition(entry.get("position", ""))
        except ValueError:
            continue

        # Default risk assessment from config
        risk_assessment = str(entry.get("risk_profile", ""))

        # Enrich with tower risk characterization when available
        if tower_risk_data:
            layer_type = _position_to_layer_type.get(position)
            if layer_type and layer_type in tower_risk_data:
                layer_data = tower_risk_data[layer_type]
                share_pct = layer_data.get("expected_loss_share_pct", 0)
                characterization = str(
                    layer_data.get("risk_characterization", "")
                )
                if characterization:
                    risk_assessment = characterization
                elif share_pct > 0:
                    risk_assessment = (
                        f"{risk_assessment} "
                        f"[{share_pct:.0f}% expected loss share]"
                    )

        layers.append(LayerAssessment(
            position=position,
            risk_assessment=risk_assessment,
            premium_guidance=str(entry.get("premium_guidance", "")),
            attachment_range=str(entry.get("typical_attachment", "")),
        ))
    return layers


def _assess_side_a(extracted: ExtractedData) -> str:
    """Evaluate Side A / DIC indemnification capacity."""
    fin = extracted.financials
    if fin is None:
        return "Standard Side A considerations (insufficient financial data)"

    gc = fin.audit.going_concern
    if gc is not None and gc.value is True:
        return (
            "HIGH Side A value -- company may not be able to indemnify "
            "(going concern opinion present)"
        )
    az = fin.distress.altman_z_score
    if az is not None and az.zone == "distress" and not az.is_partial:
        return (
            "HIGH Side A value -- company may not be able to indemnify "
            f"(Altman Z-Score in distress zone: {az.score:.2f})"
        )
    cash_runway = _estimate_cash_runway_months(fin)
    if cash_runway is not None and cash_runway < 12:
        return (
            "ELEVATED Side A value -- limited indemnification capacity "
            f"(estimated {cash_runway:.0f} months cash runway)"
        )
    return "Standard Side A considerations"


def _first_value(item: Any) -> float | None:
    """Get the first non-None value from a FinancialLineItem's values dict."""
    for sv in item.values.values():
        if sv is not None:
            return float(sv.value)
    return None


def _estimate_cash_runway_months(fin: Any) -> float | None:
    """Estimate cash runway in months from balance sheet and cash flow."""
    bs = fin.statements.balance_sheet
    if bs is None:
        return None
    cash_amount: float | None = None
    for item in bs.line_items:
        lbl = item.label.lower()
        if "cash" in lbl and "equivalent" in lbl:
            val = _first_value(item)
            if val is not None:
                cash_amount = val
                break
    if cash_amount is None:
        return None
    cf = fin.statements.cash_flow
    if cf is None:
        return None
    operating_cf: float | None = None
    for item in cf.line_items:
        lbl = item.label.lower()
        if "operating" in lbl and ("cash" in lbl or "flow" in lbl):
            val = _first_value(item)
            if val is not None:
                operating_cf = val
                break
    if operating_cf is None or operating_cf >= 0:
        return None
    monthly_burn = abs(operating_cf) / 12.0
    return cash_amount / monthly_burn if monthly_burn > 0 else None


# -----------------------------------------------------------------------
# SECT7-10: Red flag summary
# -----------------------------------------------------------------------


def compile_red_flag_summary(
    factor_scores: list[FactorScore],
    red_flags: list[RedFlagResult],
    patterns: list[PatternMatch],
    allegation_mapping: AllegationMapping | None,
) -> RedFlagSummary:
    """Consolidate all flagged items into a severity-sorted summary."""
    items: list[FlaggedItem] = []
    items.extend(_flags_from_crf(red_flags))
    items.extend(_flags_from_factors(factor_scores, allegation_mapping))
    items.extend(_flags_from_patterns(patterns))

    severity_order = {
        FlagSeverity.CRITICAL: 0, FlagSeverity.HIGH: 1,
        FlagSeverity.MODERATE: 2, FlagSeverity.LOW: 3,
    }
    items.sort(key=lambda x: severity_order.get(x.severity, 4))

    return RedFlagSummary(
        items=items,
        critical_count=sum(1 for i in items if i.severity == FlagSeverity.CRITICAL),
        high_count=sum(1 for i in items if i.severity == FlagSeverity.HIGH),
        moderate_count=sum(1 for i in items if i.severity == FlagSeverity.MODERATE),
        low_count=sum(1 for i in items if i.severity == FlagSeverity.LOW),
    )


def _flags_from_crf(red_flags: list[RedFlagResult]) -> list[FlaggedItem]:
    """Convert triggered CRF gates to CRITICAL FlaggedItems."""
    items: list[FlaggedItem] = []
    for rf in red_flags:
        if not rf.triggered:
            continue
        evidence = "; ".join(rf.evidence) if rf.evidence else "CRF evaluation"
        items.append(FlaggedItem(
            description=f"Critical Red Flag: {rf.flag_name or rf.flag_id}",
            source=evidence,
            severity=FlagSeverity.CRITICAL,
            scoring_impact=f"Ceiling: {rf.ceiling_applied}",
            trajectory="NEW",
        ))
    return items


def _flags_from_factors(
    factor_scores: list[FactorScore],
    allegation_mapping: AllegationMapping | None,
) -> list[FlaggedItem]:
    """Convert factor scores to flagged items by severity threshold."""
    items: list[FlaggedItem] = []
    theory_map = _build_factor_theory_map(allegation_mapping)
    for fs in factor_scores:
        if fs.points_deducted <= 0 or fs.max_points == 0:
            continue
        pct = fs.points_deducted / fs.max_points
        if pct >= 0.80:
            severity = FlagSeverity.HIGH
        elif pct >= 0.50:
            severity = FlagSeverity.MODERATE
        else:
            severity = FlagSeverity.LOW
        evidence = "; ".join(fs.evidence[:2]) if fs.evidence else "Factor scoring"
        items.append(FlaggedItem(
            description=f"{fs.factor_name}: {fs.points_deducted:.0f}/{fs.max_points} points",
            source=evidence,
            severity=severity,
            scoring_impact=f"{fs.factor_id}: {fs.points_deducted:.0f} pts",
            allegation_theory=theory_map.get(fs.factor_id, ""),
            trajectory="NEW",
        ))
    return items


def _flags_from_patterns(patterns: list[PatternMatch]) -> list[FlaggedItem]:
    """Convert detected patterns to flagged items with mapped severity."""
    items: list[FlaggedItem] = []
    for pm in patterns:
        if not pm.detected:
            continue
        severity = _PATTERN_SEVERITY_MAP.get(pm.severity, FlagSeverity.LOW)
        triggers = "; ".join(pm.triggers_matched[:3]) if pm.triggers_matched else ""
        impacts = [f"{k}: {v:.0f}" for k, v in pm.score_impact.items()]
        items.append(FlaggedItem(
            description=f"Pattern: {pm.pattern_name or pm.pattern_id} ({pm.severity})",
            source=triggers or "Pattern evaluation",
            severity=severity,
            scoring_impact=", ".join(impacts) if impacts else "Pattern detected",
            trajectory="NEW",
        ))
    return items


def _build_factor_theory_map(
    allegation_mapping: AllegationMapping | None,
) -> dict[str, str]:
    """Build factor_id -> primary allegation theory string mapping."""
    if allegation_mapping is None:
        return {}
    result: dict[str, str] = {}
    for theory_exp in allegation_mapping.theories:
        for fid in theory_exp.factor_sources:
            if fid not in result:
                result[fid] = theory_exp.theory.value
    return result
