"""Severity model runner: orchestrates damages, regression, amplifiers, erosion (Phase 108).

Combines all severity computation components into a single entry point
for the ScoreStage pipeline. Produces a SeverityResult on state.scoring.

Called as Step 15.5 in the ScoreStage pipeline, after H/A/E scoring
(providing P) and after legacy severity (providing comparison data).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.severity import (
    ScenarioSeverity,
    SeverityLensResult,
    SeverityResult,
    SeverityZone,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.score.damages_estimation import (
    apply_allegation_modifier,
    compute_base_damages,
    compute_defense_costs,
    compute_scenario_grid,
    estimate_turnover_rate,
)
from do_uw.stages.score.layer_erosion import (
    compute_dic_probability,
    compute_layer_erosion,
    compute_side_a_erosion,
    get_sigma_for_allegation,
)
from do_uw.stages.score.legacy_severity_lens import LegacySeverityLens
from do_uw.stages.score.settlement_regression import (
    build_feature_vector,
    infer_primary_allegation_type,
    predict_settlement_regression,
)
from do_uw.stages.score.severity_amplifiers import (
    combine_amplifiers,
    evaluate_amplifiers,
    load_amplifiers,
)

__all__ = ["run_severity_model"]

logger = logging.getLogger(__name__)


def _extract_stock_data(state: AnalysisState) -> tuple[list[dict[str, Any]], float]:
    """Extract stock drops and worst drop from state.

    Returns (stock_drops_list_for_scenario_grid, worst_drop_decimal).
    """
    drops: list[dict[str, Any]] = []
    worst_drop = 0.0

    if state.extracted is not None and state.extracted.market is not None:
        stock_drops = getattr(state.extracted.market, "stock_drops", None)
        if stock_drops is not None:
            for drop in getattr(stock_drops, "single_day_drops", []):
                pct = getattr(drop, "drop_pct", None)
                if pct is not None:
                    val = float(pct.value) if hasattr(pct, "value") else float(pct)
                    drops.append({"drop_pct": val})
                    magnitude = abs(val) / 100.0 if abs(val) > 1 else abs(val)
                    if magnitude > worst_drop:
                        worst_drop = magnitude

    return drops, worst_drop


def _extract_turnover_data(state: AnalysisState) -> float:
    """Extract turnover rate from state data."""
    if state.extracted is None or state.extracted.market is None:
        return 0.5  # Default assumption

    market = state.extracted.market
    stock = getattr(market, "stock", None)
    if stock is None:
        return 0.5

    avg_volume = 0.0
    shares_out = 0.0

    vol_attr = getattr(stock, "average_volume", None)
    if vol_attr is not None:
        avg_volume = float(vol_attr.value if hasattr(vol_attr, "value") else vol_attr)

    shares_attr = getattr(stock, "shares_outstanding", None)
    if shares_attr is not None:
        shares_out = float(shares_attr.value if hasattr(shares_attr, "value") else shares_attr)

    if avg_volume > 0 and shares_out > 0:
        return estimate_turnover_rate(avg_volume, shares_out)
    return 0.5


def run_severity_model(
    state: AnalysisState,
    signal_results: dict[str, Any],
    hae_result: Any | None = None,
    legacy_severity: Any | None = None,
    market_cap: float | None = None,
    liberty_attachment: float | None = None,
    liberty_product: str | None = None,
) -> SeverityResult | None:
    """Run the full v7.0 severity computation pipeline.

    Pipeline:
    1. Infer primary allegation type from signals
    2. Compute base damages from market cap + stock data
    3. Apply allegation modifiers and build scenario grid
    4. Run settlement regression for point estimate
    5. Load and evaluate severity amplifiers
    6. Compute defense costs
    7. Compute layer erosion (if attachment provided)
    8. Wrap legacy severity as comparison lens
    9. Build SeverityResult with P x S expected loss

    Args:
        state: AnalysisState with company, extracted, analysis data.
        signal_results: Signal evaluation results.
        hae_result: ScoringLensResult from H/A/E scoring (for P).
        legacy_severity: SeverityScenarios from legacy DDL model.
        market_cap: Company market cap (USD).
        liberty_attachment: Liberty layer attachment (USD), or None.
        liberty_product: Liberty product type ("ABC" or "SIDE_A"), or None.

    Returns:
        SeverityResult, or None if market_cap unavailable.
    """
    if market_cap is None or market_cap <= 0:
        logger.info("No market cap available; skipping severity model")
        return None

    # Step 1: Infer allegation type
    from do_uw.stages.score.case_characteristics import detect_case_characteristics
    case_chars = detect_case_characteristics(state)
    primary_allegation = infer_primary_allegation_type(signal_results, case_chars)

    # Step 2: Extract stock data and compute turnover
    stock_drops, worst_drop = _extract_stock_data(state)
    turnover_rate = _extract_turnover_data(state)
    class_period_return = worst_drop if worst_drop > 0 else 0.25  # default 25%

    # Step 3: Compute base damages
    base_damages = compute_base_damages(market_cap, class_period_return, turnover_rate)
    modified_damages = apply_allegation_modifier(base_damages, primary_allegation)

    # Step 4: Build scenario grid
    scenario_grid = compute_scenario_grid(market_cap, stock_drops)

    # Step 5: Run settlement regression
    features = build_feature_vector(state, primary_allegation)
    regression_estimate = predict_settlement_regression(features)

    # Use regression estimate as primary point estimate
    estimated_settlement = regression_estimate

    # Step 6: Load and evaluate amplifiers
    amplifiers = load_amplifiers()
    amplifier_results = evaluate_amplifiers(amplifiers, signal_results)
    combined_multiplier = combine_amplifiers(amplifier_results)
    amplified_settlement = estimated_settlement * combined_multiplier

    # Step 7: Compute defense costs
    defense_costs = compute_defense_costs(
        amplified_settlement,
        {
            "multi_defendant": case_chars.get("multiple_corrective_disclosures", False),
            "gov_investigation": case_chars.get("sec_investigation", False),
            "long_class_period": case_chars.get("class_period_over_1yr", False),
        },
        market_cap,
    )

    # Step 8: Build scenario table
    scenarios: list[ScenarioSeverity] = []
    for drop_label, drop_pct in scenario_grid:
        drop_damages = compute_base_damages(market_cap, drop_pct, turnover_rate)
        drop_modified = apply_allegation_modifier(drop_damages, primary_allegation)
        drop_amplified = drop_modified * combined_multiplier
        drop_defense = compute_defense_costs(
            drop_amplified,
            {"gov_investigation": case_chars.get("sec_investigation", False)},
            market_cap,
        )
        scenarios.append(
            ScenarioSeverity(
                allegation_type=primary_allegation,
                drop_level=drop_label,
                base_damages=drop_damages,
                settlement_estimate=drop_modified,
                amplified_settlement=drop_amplified,
                defense_cost_estimate=drop_defense,
                total_exposure=drop_amplified + drop_defense,
            )
        )

    # Step 9: Compute layer erosion (if attachment provided)
    layer_erosion_results = None
    if liberty_attachment is not None and liberty_attachment > 0:
        sigma = get_sigma_for_allegation(primary_allegation)
        product = liberty_product or "ABC"

        if product.upper() == "SIDE_A":
            # Default ABC tower top if not specified
            abc_tower_top = liberty_attachment * 2  # heuristic
            erosion = compute_side_a_erosion(
                median_settlement=amplified_settlement,
                sigma=sigma,
                attachment=0,  # Side A attaches at top of ABC
                limit=liberty_attachment,
                abc_tower_top=abc_tower_top,
                product="SIDE_A",
            )
        else:
            erosion = compute_layer_erosion(
                median_settlement=amplified_settlement,
                sigma=sigma,
                attachment=liberty_attachment,
                limit=liberty_attachment,  # Use attachment as default limit
                product="ABC",
            )
        layer_erosion_results = [erosion]

    # Step 10: Get probability from H/A/E result
    probability = 0.0
    if hae_result is not None:
        probability = getattr(hae_result, "product_score", 0.0)

    # Step 11: Compute zone
    zone = SeverityZone.zone_for(probability, amplified_settlement)

    # Step 12: Build primary lens result
    primary_result = SeverityLensResult(
        lens_name="v7_severity",
        estimated_settlement=amplified_settlement,
        damages_estimate=base_damages,
        amplifier_results=amplifier_results,
        scenarios=scenarios,
        defense_costs=defense_costs,
        layer_erosion=layer_erosion_results,
        zone=zone,
        confidence="MEDIUM",
        metadata={
            "primary_allegation_type": primary_allegation,
            "regression_estimate": regression_estimate,
            "combined_amplifier_multiplier": combined_multiplier,
            "turnover_rate": turnover_rate,
            "class_period_return": class_period_return,
        },
    )

    # Step 13: Wrap legacy severity as comparison lens
    legacy_lens = LegacySeverityLens(legacy_severity)
    legacy_result = legacy_lens.evaluate(signal_results)

    # Step 14: Build SeverityResult
    expected_loss = probability * amplified_settlement

    return SeverityResult(
        primary=primary_result,
        legacy=legacy_result,
        probability=probability,
        severity=amplified_settlement,
        expected_loss=expected_loss,
        zone=zone,
        scenario_table=scenarios,
    )
