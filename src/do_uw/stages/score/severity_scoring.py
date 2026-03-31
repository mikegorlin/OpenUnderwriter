"""SeverityScoringLens: full orchestrator for damages -> settlement -> amplifiers -> erosion.

Implements the SeverityLens Protocol. Orchestrates the complete severity
computation pipeline:
  1. Infer primary allegation type from signal results
  2. Build scenario grid (worst_actual, sector_median, catastrophic drops)
  3. For each scenario: compute_base_damages -> apply_allegation_modifier ->
     predict_settlement_regression -> apply amplifiers -> compute defense costs
  4. Compute layer erosion (if Liberty attachment provided)
  5. Build SeverityLensResult with P x S expected loss and zone classification

Also provides:
  - compute_p_x_s(P, S) -> expected loss
  - classify_zone(P, S) -> SeverityZone
  - build_severity_result(primary, legacy, hae) -> SeverityResult

Calibration report and known settlements are in severity_calibration.py.

Phase 108 Plan 02 Task 1.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from do_uw.models.severity import (
    ScenarioSeverity,
    SeverityLensResult,
    SeverityResult,
    SeverityZone,
)
from do_uw.stages.score.damages_estimation import (
    apply_allegation_modifier,
    compute_base_damages,
    compute_defense_costs,
    compute_scenario_grid,
    estimate_turnover_rate,
)
from do_uw.stages.score.layer_erosion import (
    compute_layer_erosion,
    compute_side_a_erosion,
    get_sigma_for_allegation,
)
from do_uw.stages.score.settlement_regression import (
    infer_primary_allegation_type,
    predict_settlement_regression,
)
from do_uw.stages.score.severity_amplifiers import (
    combine_amplifiers,
    evaluate_amplifiers,
    load_amplifiers,
)

# Re-export calibration for backward compatibility
from do_uw.stages.score.severity_calibration import (  # noqa: F401
    KNOWN_SETTLEMENTS,
    generate_severity_calibration_report,
)

__all__ = [
    "KNOWN_SETTLEMENTS",
    "SeverityScoringLens",
    "build_severity_result",
    "classify_zone",
    "compute_p_x_s",
    "generate_severity_calibration_report",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# P x S helpers
# ---------------------------------------------------------------------------


def compute_p_x_s(probability: float, severity: float) -> float:
    """Compute expected loss = P x S.

    Args:
        probability: Claim probability P in [0, 1].
        severity: Estimated settlement S in USD.

    Returns:
        Expected loss in USD.
    """
    return probability * severity


def classify_zone(probability: float, severity: float) -> SeverityZone:
    """Classify P x S zone per severity_model_design.yaml criteria.

    Delegates to SeverityZone.zone_for() -- this function exists as a
    module-level convenience for direct import.

    Args:
        probability: Claim probability P in [0, 1].
        severity: Estimated settlement S in USD.

    Returns:
        SeverityZone classification.
    """
    return SeverityZone.zone_for(probability, severity)


def build_severity_result(
    primary: SeverityLensResult,
    legacy: SeverityLensResult | None,
    hae_result: Any | None,
) -> SeverityResult:
    """Combine primary and legacy lens results with P from HAE into SeverityResult.

    Args:
        primary: v7.0 severity lens result (drives worksheet).
        legacy: Legacy DDL model result (comparison only), or None.
        hae_result: ScoringLensResult from H/A/E scoring (for P), or None.

    Returns:
        SeverityResult with P, S, EL, zone, and scenario table.
    """
    probability = 0.0
    if hae_result is not None:
        probability = float(getattr(hae_result, "product_score", 0.0))

    severity_val = primary.estimated_settlement
    expected_loss = compute_p_x_s(probability, severity_val)
    zone = classify_zone(probability, severity_val)

    return SeverityResult(
        primary=primary,
        legacy=legacy,
        probability=probability,
        severity=severity_val,
        expected_loss=expected_loss,
        zone=zone,
        scenario_table=primary.scenarios,
    )


# ---------------------------------------------------------------------------
# SeverityScoringLens
# ---------------------------------------------------------------------------


class SeverityScoringLens:
    """Full severity scoring lens implementing SeverityLens Protocol.

    Orchestrates: allegation inference -> scenario grid -> damages ->
    regression -> amplifiers -> defense costs -> layer erosion.
    """

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
        hae_result: Any | None = None,
    ) -> SeverityLensResult:
        """Run full severity pipeline and return SeverityLensResult.

        Args:
            signal_results: Signal evaluation results dict.
            company: Company profile with market_cap attribute.
            liberty_attachment: Liberty layer attachment point (USD).
            liberty_product: Liberty product type (ABC or SIDE_A).
            hae_result: H/A/E scoring result for probability (P).

        Returns:
            SeverityLensResult with settlement estimate, scenarios,
            amplifiers, defense costs, layer erosion, and zone.
        """
        # Extract market cap
        market_cap = self._extract_market_cap(company)
        if market_cap <= 0:
            return self._empty_result("No market cap available")

        # Step 1: Infer primary allegation type
        primary_allegation = infer_primary_allegation_type(signal_results)

        # Step 2: Extract stock drop data from company proxy
        stock_drops, worst_drop = self._extract_stock_drops(company)
        class_period_return = worst_drop if worst_drop > 0 else 0.25

        # Step 3: Compute turnover rate
        turnover_rate = self._extract_turnover(company)

        # Step 4: Compute base damages
        base_damages = compute_base_damages(
            market_cap, class_period_return, turnover_rate,
        )
        modified_damages = apply_allegation_modifier(
            base_damages, primary_allegation,
        )

        # Step 5: Build regression estimate
        features = self._build_features(
            market_cap, worst_drop, primary_allegation,
        )
        regression_estimate = predict_settlement_regression(features)

        # Step 6: Use max(damages-based, regression-based) as point estimate
        estimated_settlement = max(modified_damages, regression_estimate)

        # Step 7: Evaluate amplifiers
        amplifiers = load_amplifiers()
        amplifier_results = evaluate_amplifiers(amplifiers, signal_results)
        combined_multiplier = combine_amplifiers(amplifier_results)
        amplified_settlement = estimated_settlement * combined_multiplier

        # Step 8: Compute defense costs
        defense_costs = compute_defense_costs(
            amplified_settlement, {}, market_cap,
        )

        # Step 9: Build scenario grid
        scenario_grid = compute_scenario_grid(market_cap, stock_drops)
        scenarios = self._build_scenarios(
            scenario_grid, market_cap, turnover_rate,
            primary_allegation, combined_multiplier,
        )

        # Step 10: Layer erosion (if attachment provided)
        layer_erosion_results = None
        if liberty_attachment is not None and liberty_attachment > 0:
            layer_erosion_results = self._compute_erosion(
                amplified_settlement, primary_allegation,
                liberty_attachment, liberty_product,
            )

        # Step 11: Zone classification
        probability = 0.0
        if hae_result is not None:
            probability = float(getattr(hae_result, "product_score", 0.0))
        zone = classify_zone(probability, amplified_settlement)

        return SeverityLensResult(
            lens_name="v7_severity_scoring",
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
                "market_cap": market_cap,
            },
        )

    # -- Internal helpers --

    @staticmethod
    def _extract_market_cap(company: Any | None) -> float:
        """Extract market cap from company profile."""
        if company is None:
            return 0.0
        mc = getattr(company, "market_cap", None)
        if mc is None:
            return 0.0
        if hasattr(mc, "value"):
            return float(mc.value)
        return float(mc)

    @staticmethod
    def _extract_stock_drops(
        company: Any | None,
    ) -> tuple[list[dict[str, Any]], float]:
        """Extract stock drop data. Returns (drop_list, worst_drop_decimal)."""
        drops: list[dict[str, Any]] = []
        worst_drop = 0.0
        if company is None:
            return drops, worst_drop

        extracted = getattr(company, "extracted", None)
        if extracted is not None:
            market = getattr(extracted, "market", None)
            if market is not None:
                sd = getattr(market, "stock_drops", None)
                if sd is not None:
                    for drop in getattr(sd, "single_day_drops", []):
                        pct = getattr(drop, "drop_pct", None)
                        if pct is not None:
                            val = float(pct.value) if hasattr(pct, "value") else float(pct)
                            drops.append({"drop_pct": val})
                            mag = abs(val) / 100.0 if abs(val) > 1 else abs(val)
                            if mag > worst_drop:
                                worst_drop = mag
        return drops, worst_drop

    @staticmethod
    def _extract_turnover(company: Any | None) -> float:
        """Extract share turnover rate, default 0.5."""
        if company is None:
            return 0.5
        extracted = getattr(company, "extracted", None)
        if extracted is None:
            return 0.5
        market = getattr(extracted, "market", None)
        if market is None:
            return 0.5
        stock = getattr(market, "stock", None)
        if stock is None:
            return 0.5

        avg_vol = getattr(stock, "average_volume", None)
        shares = getattr(stock, "shares_outstanding", None)
        if avg_vol is not None and shares is not None:
            v = float(avg_vol.value if hasattr(avg_vol, "value") else avg_vol)
            s = float(shares.value if hasattr(shares, "value") else shares)
            if v > 0 and s > 0:
                return estimate_turnover_rate(v, s)
        return 0.5

    @staticmethod
    def _build_features(
        market_cap: float,
        worst_drop: float,
        allegation_type: str,
    ) -> dict[str, float]:
        """Build a minimal feature vector for regression without state."""
        features: dict[str, float] = {
            "market_cap_at_filing": math.log10(max(market_cap, 1.0)),
            "max_stock_decline_pct": worst_drop,
            "class_period_length_days": math.log10(365),
            "number_of_named_defendants": 3.0,
            "restatement_present": 1.0 if allegation_type == "financial_restatement" else 0.0,
            "sec_investigation_present": 0.0,
            "lead_plaintiff_institutional": 0.0,
            "jurisdiction_sdny": 0.0,
            "jurisdiction_ndcal": 0.0,
            "prior_securities_litigation": 0.0,
            "auditor_change": 0.0,
        }
        for atype in [
            "financial_restatement", "insider_trading",
            "regulatory_action", "offering_securities", "merger_objection",
        ]:
            features[f"allegation_type_{atype}"] = (
                1.0 if allegation_type == atype else 0.0
            )
        return features

    @staticmethod
    def _build_scenarios(
        scenario_grid: list[tuple[str, float]],
        market_cap: float,
        turnover_rate: float,
        primary_allegation: str,
        combined_multiplier: float,
    ) -> list[ScenarioSeverity]:
        """Build scenario table from scenario grid."""
        scenarios: list[ScenarioSeverity] = []
        for drop_label, drop_pct in scenario_grid:
            drop_damages = compute_base_damages(
                market_cap, drop_pct, turnover_rate,
            )
            drop_modified = apply_allegation_modifier(
                drop_damages, primary_allegation,
            )
            drop_amplified = drop_modified * combined_multiplier
            drop_defense = compute_defense_costs(
                drop_amplified, {}, market_cap,
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
        return scenarios

    @staticmethod
    def _compute_erosion(
        amplified_settlement: float,
        primary_allegation: str,
        liberty_attachment: float,
        liberty_product: str | None,
    ) -> list[Any]:
        """Compute layer erosion for Liberty attachment."""
        sigma = get_sigma_for_allegation(primary_allegation)
        product = (liberty_product or "ABC").upper()

        if product == "SIDE_A":
            abc_tower_top = liberty_attachment * 2
            erosion = compute_side_a_erosion(
                median_settlement=amplified_settlement,
                sigma=sigma,
                attachment=0,
                limit=liberty_attachment,
                abc_tower_top=abc_tower_top,
                product="SIDE_A",
            )
        else:
            erosion = compute_layer_erosion(
                median_settlement=amplified_settlement,
                sigma=sigma,
                attachment=liberty_attachment,
                limit=liberty_attachment,
                product="ABC",
            )
        return [erosion]

    @staticmethod
    def _empty_result(note: str) -> SeverityLensResult:
        """Return empty result for edge cases."""
        return SeverityLensResult(
            lens_name="v7_severity_scoring",
            estimated_settlement=0,
            damages_estimate=0,
            amplifier_results=[],
            scenarios=[],
            defense_costs=0,
            layer_erosion=None,
            zone=SeverityZone.GREEN,
            confidence="LOW",
            metadata={"note": note},
        )
