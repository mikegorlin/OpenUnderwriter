"""Score stage: full 17-step scoring pipeline.

Runs CRF gates -> factor scoring -> pattern detection -> pattern modifiers
-> composite -> ceiling -> tier -> risk type -> allegations -> probability
-> severity -> tower -> red flags -> peril map + bear cases ->
pattern engines (Step 16) -> populate ScoringResult.

Phase 27: Step 11 uses DDL-based settlement prediction (predict_settlement)
as the primary severity model, falling back to tier-based model_severity()
when no stock drops are available. Step 14 builds the 7-lens peril map
and evidence-gated bear cases. Step 16 (Phase 109) runs 4 pattern engines
+ 6 named archetype evaluations with tier floor overrides.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import BrainLoader, load_config
from do_uw.models.common import StageStatus
from do_uw.models.scoring import FactorScore, PatternMatch, ScoringResult
from do_uw.models.state import AnalysisState
from do_uw.stages.score.allegation_mapping import (
    classify_risk_type,
    map_allegations,
)
from do_uw.stages.score.bear_case_builder import build_bear_cases
from do_uw.stages.score.factor_scoring import score_all_factors
from do_uw.stages.score.frequency_model import compute_enhanced_frequency
from do_uw.stages.score.pattern_detection import detect_all_patterns
from do_uw.stages.score.peril_mapping import build_peril_map
from do_uw.stages.score.red_flag_gates import (
    apply_crf_ceilings,
    evaluate_red_flag_gates,
)
from do_uw.stages.score.settlement_prediction import (
    characterize_tower_risk,
    detect_case_characteristics,
    predict_settlement,
)
from do_uw.stages.score.severity_model import (
    compile_red_flag_summary,
    model_severity,
    recommend_tower,
)
from do_uw.stages.score.tier_classification import (
    classify_tier,
    compute_claim_probability,
    probability_range_to_band,
)

logger = logging.getLogger(__name__)



def _apply_pattern_modifiers(
    factor_scores: list[FactorScore],
    patterns: list[PatternMatch],
    scoring_config: dict[str, Any],
) -> None:
    """Apply detected pattern score_impact to factor scores in place.

    For each detected pattern with non-empty score_impact, add the
    impact points to the matching FactorScore. Re-cap at max_points
    after modifier application.
    """
    factor_map = {fs.factor_id: fs for fs in factor_scores}

    for pattern in patterns:
        if not pattern.detected or not pattern.score_impact:
            continue
        for factor_id, impact_pts in pattern.score_impact.items():
            fs = factor_map.get(factor_id)
            if fs is None:
                continue
            fs.points_deducted += impact_pts
            fs.sub_components["pattern_modifier"] = (
                fs.sub_components.get("pattern_modifier", 0.0) + impact_pts
            )
            # Re-cap at max_points
            if fs.points_deducted > fs.max_points:
                fs.points_deducted = float(fs.max_points)


# Behavioral signal factors -- amplified by IES
_BEHAVIORAL_FACTORS = frozenset({
    "F3", "F5", "F6", "F7", "F9", "F10",
})


def _apply_ies_amplification(
    factor_scores: list[FactorScore],
    state: AnalysisState,
) -> None:
    """Apply IES-aware amplification to behavioral signal factors.

    High IES (inherent exposure) amplifies behavioral signal scores:
    - IES > 75: 1.50x multiplier
    - IES > 60: 1.25x multiplier
    - IES < 40: 0.85x dampener
    Capped at factor max_points.
    """
    if state.hazard_profile is None:
        return
    ies = state.hazard_profile.ies_score
    if 40 <= ies <= 60:
        return  # Neutral range -- no amplification

    if ies > 75:
        mult = 1.50
    elif ies > 60:
        mult = 1.25
    elif ies < 40:
        mult = 0.85
    else:
        return

    for fs in factor_scores:
        fid_prefix = fs.factor_id[:2] if len(fs.factor_id) >= 2 else ""
        if fid_prefix in _BEHAVIORAL_FACTORS and fs.points_deducted > 0:
            original = fs.points_deducted
            amplified = original * mult
            capped = min(amplified, float(fs.max_points))
            if capped != original:
                fs.points_deducted = capped
                fs.sub_components["ies_amplification"] = mult
                logger.debug(
                    "IES amplification: %s %.1f -> %.1f (%.2fx)",
                    fs.factor_id, original, capped, mult,
                )


def _apply_contribution_caps(
    factor_scores: list[FactorScore],
    state: AnalysisState,
) -> None:
    """Apply combined contribution caps to prevent double-counting.

    Safety net: if both IES (hazard profile) and factor scoring are
    high for the same domain, log a warning. CONTEXT_DISPLAY checks
    already have empty factors (Plan 01), so this is primarily a
    monitoring function for any remaining overlap.
    """
    if state.hazard_profile is None:
        return
    ies = state.hazard_profile.ies_score
    if ies <= 50:
        return

    # Check for overlap: high IES + high factor scores in same domain
    high_factors = [
        fs for fs in factor_scores
        if fs.points_deducted > 0.6 * fs.max_points
    ]
    if high_factors and ies > 60:
        factor_names = [fs.factor_id for fs in high_factors]
        logger.info(
            "Contribution cap check: IES=%.1f with high factors %s. "
            "CONTEXT_DISPLAY reclassification prevents double-counting.",
            ies, factor_names,
        )


def _get_market_cap(state: AnalysisState) -> float | None:
    """Extract market cap value from company profile."""
    if state.company is None or state.company.market_cap is None:
        return None
    return float(state.company.market_cap.value)


def _extract_stock_drops_as_dicts(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract stock drop events as dicts for settlement prediction.

    Combines single-day and multi-day drops from state.extracted.market.stock_drops.
    Converts Pydantic models to dicts for the settlement prediction API.
    """
    if state.extracted is None or state.extracted.market is None:
        return []

    stock_drops = state.extracted.market.stock_drops
    all_drops: list[dict[str, Any]] = []

    for drop in stock_drops.single_day_drops:
        all_drops.append(drop.model_dump())

    for drop in stock_drops.multi_day_drops:
        all_drops.append(drop.model_dump())

    return all_drops


def _load_calibration_config() -> dict[str, Any]:
    """Load settlement_calibration.json from config directory."""
    return load_config("settlement_calibration")


def _load_actuarial_config() -> dict[str, Any]:
    """Load actuarial.json from config directory."""
    return load_config("actuarial")


class ScoreStage:
    """Full 17-step scoring pipeline.

    Pipeline: CRF gates -> factors -> patterns -> modifiers -> composite
    -> ceiling -> tier -> risk type -> allegations -> probability ->
    severity -> tower -> red flag summary -> peril map + bear cases ->
    populate ScoringResult.
    """

    def __init__(
        self,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
    ) -> None:
        """Initialize ScoreStage.

        Args:
            liberty_attachment: Liberty layer attachment point (USD), from CLI --attachment.
            liberty_product: Liberty product type (ABC or SIDE_A), from CLI --product.
        """
        self._liberty_attachment = liberty_attachment
        self._liberty_product = liberty_product

    @property
    def name(self) -> str:
        """Stage name."""
        return "score"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify analyze stage is complete."""
        analyze = state.stages.get("analyze")
        if analyze is None or analyze.status != StageStatus.COMPLETED:
            msg = "Analyze stage must be completed before score"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Run the full SCORE stage pipeline (16 steps)."""
        state.mark_stage_running(self.name)

        # Load brain config
        loader = BrainLoader()
        brain = loader.load_all()

        # Validate extracted data exists
        if state.extracted is None:
            msg = "No extracted data available for scoring"
            raise ValueError(msg)

        # Build analysis results dict for Phase 26 CRF gates
        analysis_dict: dict[str, Any] | None = None
        if state.analysis is not None:
            analysis_dict = {
                "signal_results": state.analysis.signal_results,
                "executive_risk": state.analysis.executive_risk,
                "forensic_composites": state.analysis.forensic_composites,
                "nlp_signals": state.analysis.nlp_signals,
            }

        # Step 1: Evaluate CRF gates FIRST (per processing_rules)
        red_flag_results = evaluate_red_flag_gates(
            brain.red_flags, brain.scoring, state.extracted, state.company,
            analysis_dict,
        )

        # Step 2: Score all 10 factors (base scores, with Phase 26 sub-factors)
        # Extract signal_results for signal-driven scoring path (Phase 112)
        signal_results_for_scoring = (
            analysis_dict.get("signal_results") if analysis_dict else None
        )
        factor_scores = score_all_factors(
            brain.scoring, state.extracted, state.company, brain.sectors,
            analysis_dict, signal_results_for_scoring,
        )

        # Step 3: Detect 17+ patterns
        patterns = detect_all_patterns(
            brain.patterns, state.extracted, state.company,
        )

        # Step 4: Apply pattern modifiers to factor scores
        _apply_pattern_modifiers(factor_scores, patterns, brain.scoring)

        # Step 4.5: IES-aware behavioral signal amplification (Phase 26)
        _apply_ies_amplification(factor_scores, state)

        # Step 4.6: Combined contribution caps (Phase 26)
        _apply_contribution_caps(factor_scores, state)

        # Step 5: Compute composite score (after pattern modifiers)
        total_risk = sum(f.points_deducted for f in factor_scores)
        composite = 100.0 - total_risk

        # Step 6: Apply CRF ceilings (size-conditioned + weighted compounding)
        market_cap = _get_market_cap(state)
        quality_score, binding_id, ceiling_details = apply_crf_ceilings(
            composite, red_flag_results,
            scoring_config=brain.scoring,
            market_cap=market_cap,
            analysis_results=analysis_dict,
        )

        # Step 6.5: Sync resolved ceilings back to RedFlagResult objects
        # evaluate_red_flag_gates sets ceiling_applied from flat config,
        # but apply_crf_ceilings resolves via size-severity matrix.
        # Without this sync, renderers display the flat ceiling (e.g. 30)
        # while the actual applied ceiling is size-adjusted (e.g. 70).
        if ceiling_details:
            resolved_map = {
                d["crf_id"]: d for d in ceiling_details
            }
            for rfr in red_flag_results:
                if rfr.triggered and rfr.flag_id in resolved_map:
                    detail = resolved_map[rfr.flag_id]
                    rfr.ceiling_applied = detail["resolved_ceiling"]
                    if detail.get("resolved_tier"):
                        rfr.max_tier = detail["resolved_tier"]

        # Step 7: Classify tier
        tiers_config: list[dict[str, Any]] = brain.scoring.get("tiers", [])
        tier = classify_tier(quality_score, tiers_config)

        # Step 7.1: Apply industry-specific tier ceilings
        from do_uw.stages.score.tier_classification import apply_industry_ceiling
        tier = apply_industry_ceiling(tier, state, tiers_config)

        # Step 7.5: H/A/E multiplicative scoring (v7.0)
        hae_result = None
        try:
            from do_uw.stages.score.hae_crf import evaluate_crf_discordance
            from do_uw.stages.score.hae_scoring import HAEScoringLens

            hae_lens = HAEScoringLens()
            signal_results = (
                state.analysis.signal_results if state.analysis else {}
            )
            hae_result = hae_lens.evaluate(
                signal_results,
                company=state.company,
                liberty_attachment=None,  # populated when Liberty layer data available
                liberty_product=None,
            )
            # Apply CRF discordance
            final_tier, crf_vetoes = evaluate_crf_discordance(
                signal_results, hae_result.tier,
            )
            hae_result = hae_result.model_copy(update={
                "tier": final_tier,
                "crf_vetoes": crf_vetoes,
                "tier_source": "crf_override"
                if final_tier != hae_result.tier
                else hae_result.tier_source,
            })
            logger.info(
                "H/A/E scoring: P=%.4f tier=%s (H=%.3f A=%.3f E=%.3f)",
                hae_result.product_score,
                hae_result.tier.value,
                hae_result.composites.get("host", 0),
                hae_result.composites.get("agent", 0),
                hae_result.composites.get("environment", 0),
            )
        except Exception:
            logger.warning(
                "H/A/E scoring failed; continuing with legacy only",
                exc_info=True,
            )

        # Step 8: Classify risk type
        risk_type = classify_risk_type(
            state.extracted, state.company, factor_scores, patterns,
        )

        # Step 9: Map allegations
        allegation_map = map_allegations(
            factor_scores, patterns, red_flag_results, state.extracted,
        )

        # Step 10: Compute claim probability
        claim_prob = compute_claim_probability(
            tier, state.company, brain.sectors,
        )

        # Step 10.5: Enhanced frequency model (Phase 27 gap closure)
        # Replaces ad-hoc IES adjustment with explicit classification x hazard x signal
        enhanced_freq = compute_enhanced_frequency(
            state, red_flag_results, patterns, factor_scores,
        )
        if enhanced_freq.methodology != "tier-based fallback":
            claim_prob.range_low_pct = round(
                enhanced_freq.adjusted_probability_pct * 0.7, 2,
            )
            claim_prob.range_high_pct = round(
                enhanced_freq.adjusted_probability_pct, 2,
            )
            claim_prob.adjustment_narrative += (
                f" Enhanced frequency: {enhanced_freq.base_rate_pct:.2f}% base"
                f" x {enhanced_freq.hazard_multiplier:.2f} hazard"
                f" x {enhanced_freq.signal_multiplier:.2f} signal"
                f" = {enhanced_freq.adjusted_probability_pct:.2f}%."
            )
            # Sync tier probability_range with the enhanced model output
            # so Tier Classification and Claim Probability show the same
            # values (the enhanced model supersedes the static tier range).
            tier.probability_range = (
                f"{claim_prob.range_low_pct:.1f}-"
                f"{claim_prob.range_high_pct:.1f}%"
            )
            # Update band to match the new range
            claim_prob.band = probability_range_to_band(
                tier.probability_range,
            )

        # Step 11: Model severity (Phase 27: DDL-based settlement prediction)
        # market_cap already computed at Step 6
        severity = None
        tower_risk_data: dict[str, Any] | None = None

        # Try DDL-based settlement prediction first
        if market_cap is not None:
            stock_drops = _extract_stock_drops_as_dicts(state)
            case_chars = detect_case_characteristics(state)
            calibration_config = _load_calibration_config()

            severity = predict_settlement(
                market_cap, stock_drops, case_chars, calibration_config, tier,
            )

            if severity is not None:
                # Load actuarial config for tower risk characterization
                actuarial_config = _load_actuarial_config()
                tower_risk_data = characterize_tower_risk(
                    severity, actuarial_config,
                )

                # Store settlement prediction on analysis results
                if state.analysis is not None:
                    state.analysis.settlement_prediction = {
                        "model": "ddl_v1",
                        "ddl_amount": severity.scenarios[0].ddl_amount
                        if severity.scenarios
                        else 0.0,
                        "case_characteristics": case_chars,
                        "tower_risk": tower_risk_data or {},
                    }

                logger.info(
                    "DDL-based settlement prediction: median=$%.0f, "
                    "%d case chars active",
                    severity.scenarios[1].settlement_estimate
                    if len(severity.scenarios) > 1
                    else 0,
                    sum(1 for v in case_chars.values() if v),
                )

        # Fallback to tier-based model when DDL prediction unavailable
        if severity is None:
            severity = model_severity(market_cap, tier, brain.scoring)
            logger.info(
                "Using tier-based severity model (DDL unavailable)"
            )

        # Step 12: Recommend tower position (with risk characterization)
        tower = recommend_tower(
            tier, severity, state.extracted, brain.scoring, tower_risk_data,
        )

        # Step 13: Compile red flag summary
        rf_summary = compile_red_flag_summary(
            factor_scores, red_flag_results, patterns, allegation_map,
        )

        # Step 14: Build peril map + bear cases (Phase 27)
        try:
            peril_map = build_peril_map(state)

            # Build bear cases from allegation mapping
            company_name = ""
            if state.company is not None:
                ln = state.company.identity.legal_name
                if ln is not None:
                    company_name = ln.value
                else:
                    company_name = state.company.identity.ticker
            signal_results_dict = (
                state.analysis.signal_results if state.analysis is not None else {}
            )
            bear_cases = build_bear_cases(
                allegation_map.model_dump(),
                signal_results_dict,
                [a.model_dump() for a in peril_map.assessments],
                state.extracted,
                company_name or "Company",
            )
            peril_map.bear_cases = bear_cases

            # Store peril map on analysis results
            if state.analysis is not None:
                state.analysis.peril_map = peril_map.model_dump()

            logger.info(
                "Peril map: overall=%s, %d bear cases, %d coverage gaps",
                peril_map.overall_peril_rating,
                len(bear_cases),
                len(peril_map.coverage_gaps),
            )
        except Exception:
            logger.warning(
                "Peril map construction failed; continuing without peril map",
                exc_info=True,
            )

        # Count detected patterns and CRF triggers
        detected_patterns = [p for p in patterns if p.detected]
        n_flags = sum(1 for r in red_flag_results if r.triggered)

        # Populate complete scoring result
        state.scoring = ScoringResult(
            composite_score=composite,
            quality_score=quality_score,
            total_risk_points=total_risk,
            factor_scores=factor_scores,
            red_flags=[r for r in red_flag_results if r.triggered],
            tier=tier,
            patterns_detected=detected_patterns,
            risk_type=risk_type,
            allegation_mapping=allegation_map,
            claim_probability=claim_prob,
            severity_scenarios=severity,
            tower_recommendation=tower,
            red_flag_summary=rf_summary,
            binding_ceiling_id=binding_id,
            ceiling_details=ceiling_details if isinstance(ceiling_details, list) else [],
            calibration_notes=[
                "SECT7-11: All scoring parameters require calibration "
                "against historical cases"
            ],
        )

        # Step 15: Store H/A/E result on scoring output (v7.0)
        if hae_result is not None:
            state.scoring.hae_result = hae_result

        # Step 15.5: v7.0 Severity model (Phase 108)
        try:
            from do_uw.stages.score._severity_runner import run_severity_model

            severity_result = run_severity_model(
                state=state,
                signal_results=signal_results,
                hae_result=hae_result,
                legacy_severity=severity,
                market_cap=market_cap,
                liberty_attachment=self._liberty_attachment,
                liberty_product=self._liberty_product,
            )
            if severity_result is not None:
                state.scoring.severity_result = severity_result
                logger.info(
                    "v7.0 severity: S=$%.0f, P=%.4f, EL=$%.0f, zone=%s",
                    severity_result.severity,
                    severity_result.probability,
                    severity_result.expected_loss,
                    severity_result.zone.value,
                )
        except Exception:
            logger.warning(
                "v7.0 severity model failed; continuing with legacy only",
                exc_info=True,
            )

        # Step 16: Pattern engines (Phase 109)
        try:
            from do_uw.stages.score._pattern_runner import run_pattern_engines

            pattern_result = run_pattern_engines(
                state=state,
                signal_results=signal_results,
                hae_result=hae_result,
            )
            if pattern_result is not None:
                state.scoring.pattern_engine_result = pattern_result
                # Apply archetype tier floors to hae_result
                if hae_result is not None:
                    from do_uw.stages.score._pattern_runner import (
                        _apply_tier_floors,
                    )

                    updated_hae = _apply_tier_floors(
                        hae_result, pattern_result.archetype_results,
                    )
                    if updated_hae.tier != hae_result.tier:
                        hae_result = updated_hae
                        state.scoring.hae_result = hae_result
                n_fired = sum(
                    1 for e in pattern_result.engine_results if e.fired
                )
                n_arch = sum(
                    1 for a in pattern_result.archetype_results if a.fired
                )
                logger.info(
                    "Pattern engines: %d/%d fired, %d/%d archetypes matched",
                    n_fired,
                    len(pattern_result.engine_results),
                    n_arch,
                    len(pattern_result.archetype_results),
                )
        except Exception:
            logger.warning(
                "Pattern engines failed; continuing without patterns",
                exc_info=True,
            )

        # Step 17: Conditional deep-dive triggers (Phase 110)
        try:
            from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

            deepdive_result = run_deepdive_triggers(
                state=state,
                signal_results=signal_results,
                hae_result=hae_result,
            )
            if deepdive_result is not None:
                state.scoring.deepdive_result = deepdive_result
                logger.info(
                    "Deep-dive triggers: %d/%d fired",
                    deepdive_result.triggers_fired,
                    deepdive_result.triggers_evaluated,
                )
        except Exception:
            logger.warning(
                "Deep-dive triggers failed; continuing",
                exc_info=True,
            )

        # Step 18: Adversarial critique (Phase 110)
        try:
            from do_uw.stages.score._adversarial_runner import run_adversarial_critique

            adversarial_result = run_adversarial_critique(
                state=state,
                signal_results=signal_results,
                scoring_result=state.scoring,
            )
            if adversarial_result is not None:
                state.scoring.adversarial_result = adversarial_result
                logger.info(
                    "Adversarial critique: %d caveats (%d FP, %d FN, %d contradictions, %d completeness)",
                    len(adversarial_result.caveats),
                    adversarial_result.false_positive_count,
                    adversarial_result.false_negative_count,
                    adversarial_result.contradiction_count,
                    adversarial_result.completeness_issues,
                )
        except Exception:
            logger.warning("Adversarial critique failed; continuing", exc_info=True)

        logger.info(
            "Score complete: quality=%.1f, tier=%s, %d patterns, %d CRF triggers",
            quality_score,
            tier.tier.value,
            len(detected_patterns),
            n_flags,
        )

        # Phase 13: AI risk scoring (independent of 10-factor model)
        try:
            from do_uw.stages.score.ai_risk_scoring import score_ai_risk

            if state.extracted and state.extracted.ai_risk:
                state.extracted.ai_risk = score_ai_risk(state)
                logger.info(
                    "AI risk scored: %.1f/100",
                    state.extracted.ai_risk.overall_score,
                )
        except Exception:
            logger.warning(
                "AI risk scoring failed; continuing without AI risk scores"
            )

        state.mark_stage_completed(self.name)


__all__ = ["ScoreStage"]
