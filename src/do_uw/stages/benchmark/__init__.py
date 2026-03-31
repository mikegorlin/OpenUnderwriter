"""Benchmark stage: Peer-relative comparisons and executive summary.

Replaces the Phase 1 stub with a real implementation that:
1. Computes percentile rankings across peer metrics
2. Calculates actuarial inherent risk baseline (SECT1-02)
3. Builds complete ExecutiveSummary (SECT1-01 through SECT1-07)
4. Enriches with market intelligence and actuarial pricing (optional)
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import BrainLoader
from do_uw.models.common import StageStatus
from do_uw.models.executive_summary import InherentRiskBaseline
from do_uw.models.scoring import BenchmarkResult, MetricBenchmark, Tier
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.benchmark_enrichments import (
    enrich_actuarial_pricing,
    enrich_market_intelligence,
)
from do_uw.stages.benchmark.inherent_risk import (
    compute_inherent_risk_baseline,
)
from do_uw.stages.benchmark.peer_metrics import compute_peer_rankings
from do_uw.stages.benchmark.summary_builder import build_executive_summary

logger = logging.getLogger(__name__)


def _get_sector_code(state: AnalysisState) -> str:
    """Extract sector code from company identity."""
    if state.company is not None and state.company.identity.sector is not None:
        return str(state.company.identity.sector.value)
    return "DEFAULT"


def _get_market_cap(state: AnalysisState) -> float | None:
    """Extract market cap value from company profile."""
    if state.company is None or state.company.market_cap is None:
        return None
    return float(state.company.market_cap.value)


def _compute_relative_position(
    quality_score: float,
    metric_details: dict[str, MetricBenchmark],
) -> str:
    """Determine relative position label from quality score and metrics.

    Uses quality score percentile if available, otherwise falls back
    to quality score thresholds:
    - 86+: BEST_IN_CLASS
    - 71-85: ABOVE_AVERAGE
    - 51-70: AVERAGE
    - 31-50: BELOW_AVERAGE
    - 0-30: WORST_IN_CLASS
    """
    # Check if we have a quality_score percentile from peer comparison
    qs_metric = metric_details.get("quality_score")
    if qs_metric and qs_metric.percentile_rank is not None:
        pct = qs_metric.percentile_rank
        if pct >= 80:
            return "BEST_IN_CLASS"
        if pct >= 60:
            return "ABOVE_AVERAGE"
        if pct >= 40:
            return "AVERAGE"
        if pct >= 20:
            return "BELOW_AVERAGE"
        return "WORST_IN_CLASS"

    # Fall back to absolute quality score thresholds
    if quality_score >= 86:
        return "BEST_IN_CLASS"
    if quality_score >= 71:
        return "ABOVE_AVERAGE"
    if quality_score >= 51:
        return "AVERAGE"
    if quality_score >= 31:
        return "BELOW_AVERAGE"
    return "WORST_IN_CLASS"


def _get_sector_avg(
    sectors_config: dict[str, Any],
    state: AnalysisState,
) -> float | None:
    """Get sector average quality score if available.

    Currently returns None as we don't have sector-level quality scores.
    Placeholder for future peer quality score aggregation.
    """
    return None


def _reeval_peer_signals(
    state: AnalysisState,
    all_signals: list[dict[str, Any]],
) -> None:
    """Re-evaluate FIN.PEER.* signals after frames_percentiles are available.

    Peer comparison signals are SKIPPED during ANALYZE because the
    BENCHMARK stage runs later and populates frames_percentiles. This
    function re-runs only FIN.PEER.* AUTO signals with the now-available
    benchmark data, replacing SKIPPED results with TRIGGERED/CLEAR.
    """
    from do_uw.stages.analyze.signal_engine import execute_signals

    peer_checks = [
        c
        for c in all_signals
        if c.get("execution_mode") == "AUTO" and str(c.get("id", "")).startswith("FIN.PEER.")
    ]
    if not peer_checks:
        return

    if state.extracted is None or state.benchmark is None:
        return

    logger.info(
        "Re-evaluating %d FIN.PEER signals with frames_percentiles",
        len(peer_checks),
    )

    try:
        reeval_results = execute_signals(
            peer_checks,
            state.extracted,
            state.company,
            benchmarks=state.benchmark,
        )

        upgraded = 0
        for result in reeval_results:
            if result.status.value == "SKIPPED":
                continue
            old = state.analysis.signal_results.get(result.signal_id)  # type: ignore[union-attr]
            if old is not None and old.get("status") == "SKIPPED":
                state.analysis.signal_results[result.signal_id] = result.model_dump()  # type: ignore[union-attr]
                upgraded += 1

        if upgraded > 0 and state.analysis is not None:
            # Recompute aggregate counts
            state.analysis.checks_failed = sum(
                1 for r in state.analysis.signal_results.values() if r.get("status") == "TRIGGERED"
            )
            state.analysis.checks_passed = sum(
                1 for r in state.analysis.signal_results.values() if r.get("status") == "CLEAR"
            )
            state.analysis.checks_skipped = sum(
                1 for r in state.analysis.signal_results.values() if r.get("status") == "SKIPPED"
            )

        logger.info(
            "Peer signal re-eval: %d signals upgraded from SKIPPED",
            upgraded,
        )
    except Exception:
        logger.warning(
            "Peer signal re-evaluation failed (non-fatal)",
            exc_info=True,
        )


class BenchmarkStage:
    """Peer-relative benchmarking, inherent risk, and executive summary.

    Pipeline position: After SCORE, before RENDER.
    Requires: scoring, company, extracted data.
    Produces: BenchmarkResult, ExecutiveSummary (all SECT1 fields).
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "benchmark"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify score stage is complete."""
        score = state.stages.get("score")
        if score is None or score.status != StageStatus.COMPLETED:
            msg = "Score stage must be completed before benchmark"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Run the BENCHMARK stage.

        Steps:
        1. Compute peer rankings (percentile per metric)
        2. Compute relative position
        3. Populate BenchmarkResult
        4. Compute inherent risk baseline
        5. Build complete ExecutiveSummary (snapshot, inherent risk,
           key findings, thesis, deal context)
        """
        state.mark_stage_running(self.name)
        logger.debug("BENCHMARK stage started")
        print("DEBUG: BenchmarkStage.run starting")

        loader = BrainLoader()
        logger.debug("Loading brain...")
        brain = loader.load_all()
        logger.debug("Brain loaded")

        # Validate scoring exists
        scoring = state.scoring
        if scoring is None:
            msg = "No scoring data available for benchmarking"
            raise ValueError(msg)
        logger.debug(f"Scoring validated: quality_score={scoring.quality_score}")

        # Step 1: Compute peer rankings
        peer_tickers: list[str] = []
        if (
            state.extracted
            and state.extracted.financials
            and state.extracted.financials.peer_group
        ):
            peer_tickers = [p.ticker for p in state.extracted.financials.peer_group.peers]
        logger.debug(f"Peer tickers: {peer_tickers}")

        logger.debug("Computing peer rankings...")
        print("DEBUG: Before compute_peer_rankings")
        peer_rankings, metric_details = compute_peer_rankings(
            state,
            brain.sectors,
        )
        print("DEBUG: After compute_peer_rankings")
        logger.debug(f"Peer rankings computed: {len(peer_rankings)} metrics")

        # Step 1b: Compute Frames-based percentiles (true cross-filer ranking)
        logger.debug("Checking for frames data...")
        frames_data: dict = {}
        sic_mapping: dict = {}
        if state.acquired_data:
            filings = state.acquired_data.filings
            if isinstance(filings, dict):
                frames_data = filings.get("frames", {})
                sic_mapping = filings.get("sic_mapping", {})
        logger.debug(
            f"Frames data present: {bool(frames_data)}, keys: {list(frames_data.keys()) if frames_data else []}"
        )

        frames_percentiles: dict = {}
        if frames_data:
            from do_uw.stages.benchmark.frames_benchmarker import (
                compute_frames_percentiles,
            )

            logger.debug("Importing compute_frames_percentiles...")

            company_cik: int | None = None
            company_sic: str | None = None
            if state.company and state.company.identity.cik:
                company_cik = int(state.company.identity.cik.value)
            if state.company and state.company.identity.sic_code:
                company_sic = str(state.company.identity.sic_code.value)
            logger.debug(f"Company CIK: {company_cik}, SIC: {company_sic}")

            if company_cik:
                logger.debug("Computing frames percentiles...")
                frames_percentiles = compute_frames_percentiles(
                    frames_data=frames_data,
                    company_cik=company_cik,
                    company_sic=company_sic,
                    sic_mapping=sic_mapping,
                )
                logger.info(
                    "Frames percentiles: %d metrics computed",
                    len(frames_percentiles),
                )
        else:
            logger.debug("No frames data, skipping frames percentiles")

        # Step 2: Compute relative position
        logger.debug("Computing relative position...")
        relative_position = _compute_relative_position(
            scoring.quality_score,
            metric_details,
        )
        logger.debug(f"Relative position: {relative_position}")

        # Step 3: Populate BenchmarkResult
        logger.debug("Creating BenchmarkResult...")
        state.benchmark = BenchmarkResult(
            peer_group_tickers=peer_tickers,
            peer_rankings=peer_rankings,
            metric_details=metric_details,
            sector_average_score=_get_sector_avg(brain.sectors, state),
            relative_position=relative_position,
        )
        logger.debug("BenchmarkResult created")

        # Step 3b: Attach Frames percentiles and merge into metric_details
        logger.debug(f"Attaching frames percentiles (count: {len(frames_percentiles)})")
        state.benchmark.frames_percentiles = frames_percentiles
        updated_count = 0
        added_count = 0
        for metric_name, fp in frames_percentiles.items():
            if fp.overall is not None:
                existing = metric_details.get(metric_name)
                if existing is not None:
                    # Update existing metric with Frames data
                    existing.percentile_rank = round(fp.overall, 1)
                    existing.peer_count = fp.peer_count_overall
                    existing.company_value = fp.company_value
                    updated_count += 1
                else:
                    # Add new metric from Frames data
                    metric_details[metric_name] = MetricBenchmark(
                        metric_name=metric_name,
                        company_value=fp.company_value,
                        percentile_rank=round(fp.overall, 1),
                        peer_count=fp.peer_count_overall,
                        higher_is_better=fp.higher_is_better,
                        section="SECT3",
                    )
                    added_count += 1
        state.benchmark.metric_details = metric_details
        logger.debug(f"Frames percentiles merged: {updated_count} updated, {added_count} added")

        # Step 3c: Re-evaluate peer comparison signals now that frames data exists.
        # FIN.PEER.* signals use mechanism=peer_comparison which requires
        # benchmarks (frames_percentiles). These were SKIPPED during ANALYZE
        # because BENCHMARK runs after ANALYZE in the pipeline.
        logger.debug(
            f"Checking for peer signal re-eval: frames_percentiles={bool(frames_percentiles)}, analysis={state.analysis is not None}"
        )
        if frames_percentiles and state.analysis is not None:
            from do_uw.brain.brain_unified_loader import load_signals

            logger.debug("Loading signals for peer re-eval...")
            all_signals = load_signals().get("signals", [])
            logger.debug(f"Loaded {len(all_signals)} total signals")
            _reeval_peer_signals(state, all_signals)
        else:
            logger.debug("Skipping peer signal re-eval")

        # Step 4: Compute inherent risk baseline
        logger.debug("Computing inherent risk baseline...")
        sector_code = _get_sector_code(state)
        market_cap = _get_market_cap(state)
        tier = scoring.tier.tier if scoring.tier else Tier.WRITE
        logger.debug(
            f"Inherent risk inputs: sector_code={sector_code}, market_cap={market_cap}, tier={tier}, quality_score={scoring.quality_score}"
        )

        inherent_risk: InherentRiskBaseline = compute_inherent_risk_baseline(
            sector_code,
            market_cap,
            scoring.quality_score,
            tier,
            brain.sectors,
            brain.scoring,
        )
        state.benchmark.inherent_risk = inherent_risk
        logger.debug(
            f"Inherent risk computed: company_adjusted_rate_pct={inherent_risk.company_adjusted_rate_pct}"
        )

        # Silent sanity check: compare old baseline with new
        logger.debug("Running inherent risk sanity check...")
        if state.classification is not None:
            old_rate = inherent_risk.company_adjusted_rate_pct
            new_rate = state.classification.base_filing_rate_pct
            if state.hazard_profile is not None:
                new_rate *= state.hazard_profile.ies_multiplier
            if old_rate > 0 and abs(new_rate - old_rate) / old_rate > 1.0:
                logger.warning(
                    "Inherent risk divergence: old=%.2f%% vs new=%.2f%% (>2x difference)",
                    old_rate,
                    new_rate,
                )
        logger.debug("Inherent risk sanity check complete")

        # Step 5: Build complete ExecutiveSummary
        logger.debug("Building executive summary...")
        state.executive_summary = build_executive_summary(
            state,
            inherent_risk,
        )
        logger.debug("Executive summary built")

        # Step 6: Market intelligence (optional, non-breaking)
        logger.debug("Enriching market intelligence...")
        enrich_market_intelligence(state, scoring)
        logger.debug("Market intelligence enriched")

        # Step 7: Actuarial pricing (optional, non-breaking)
        logger.debug("Enriching actuarial pricing...")
        enrich_actuarial_pricing(state, scoring, inherent_risk)
        logger.debug("Actuarial pricing enriched")

        # Step 8: Pre-compute narratives for RENDER
        logger.debug("Pre-computing narratives...")
        self._precompute_narratives(state, scoring)
        logger.debug("Narratives pre-computed")

        # Step 8.5: Pre-compute dual-voice commentary (Phase 130)
        logger.debug("Pre-computing dual-voice commentary...")
        self._precompute_commentary(state)
        logger.debug("Dual-voice commentary pre-computed")

        # Step 9: Forward-Looking Intelligence (Phase 117)
        logger.debug("Computing forward-looking intelligence...")
        self._compute_forward_looking_intelligence(state)
        logger.debug("Forward-looking intelligence computed")

        # Step 10: Dossier Enrichment (Phase 118)
        logger.debug("Enriching dossier...")
        self._enrich_dossier(state)
        logger.debug("Dossier enriched")

        # Step 11: Stock drop D&O assessment (Phase 119)
        logger.debug("Starting stock drop D&O assessment...")
        try:
            from do_uw.stages.benchmark.stock_drop_narrative import (
                generate_drop_do_assessments,
                generate_drop_pattern_narrative,
            )

            logger.debug("Imported stock drop narrative modules")

            mkt = state.extracted.market if state.extracted else None
            logger.debug(f"Market data present: {mkt is not None}")
            if mkt and mkt.stock_drops:
                all_drops = (mkt.stock_drops.single_day_drops or []) + (
                    mkt.stock_drops.multi_day_drops or []
                )
                logger.debug(f"Found {len(all_drops)} stock drops")
                company_name = "Company"
                if state.company and state.company.identity:
                    _id = state.company.identity
                    company_name = (
                        (_id.legal_name.value if _id.legal_name else None)
                        or _id.ticker
                        or "Company"
                    )
                logger.debug(f"Company name: {company_name}")
                generate_drop_do_assessments(all_drops, company_name)
                patterns = state.stock_patterns
                state.drop_narrative = generate_drop_pattern_narrative(
                    patterns,
                    all_drops,
                    company_name,
                )
                logger.debug("Stock drop narrative generated")
            else:
                logger.debug("No market data or stock drops found")
            logger.info("Step 11: Stock drop D&O assessment complete")
        except Exception:
            logger.warning(
                "Step 11: Stock drop D&O assessment failed",
                exc_info=True,
            )

        # Step 12: Competitive landscape enrichment (Phase 119)
        logger.debug("Starting competitive landscape enrichment...")
        try:
            from do_uw.stages.benchmark.competitive_enrichment import (
                enrich_competitive_landscape,
            )

            logger.debug("Imported competitive enrichment module")

            enrich_competitive_landscape(state)
            logger.info("Step 12: Competitive landscape enrichment complete")
        except Exception:
            logger.warning(
                "Step 12: Competitive landscape enrichment failed",
                exc_info=True,
            )

        # Step 13: Alt data enrichment (Phase 119)
        logger.debug("Starting alt data enrichment...")
        try:
            from do_uw.stages.benchmark.alt_data_enrichment import (
                enrich_alt_data,
            )

            logger.debug("Imported alt data enrichment module")

            enrich_alt_data(state)
            logger.info("Step 13: Alt data enrichment complete")
        except Exception:
            logger.warning(
                "Step 13: Alt data enrichment failed",
                exc_info=True,
            )

        n_metrics = len([v for v in metric_details.values() if v.percentile_rank is not None])
        logger.info(
            "Benchmark complete: %d metrics ranked, position=%s, inherent_risk=%.2f%%",
            n_metrics,
            relative_position,
            inherent_risk.company_adjusted_rate_pct,
        )
        logger.debug("All benchmark steps completed")

        state.mark_stage_completed(self.name)
        logger.debug("Stage marked as completed")

    def _precompute_narratives(
        self,
        state: AnalysisState,
        scoring: Any,
    ) -> None:
        """Pre-compute narratives for RENDER stage.

        Generates:
        1. Thesis/risk/claim narratives on state.benchmark (legacy)
        2. LLM section narratives on state.analysis.pre_computed_narratives
        """
        if state.benchmark is None:
            return

        # Legacy thesis/risk/claim narratives
        self._precompute_legacy_narratives(state, scoring)

        # Phase 35: LLM-generated section narratives
        try:
            from do_uw.stages.benchmark.narrative_generator import (
                generate_all_narratives,
            )

            if state.analysis is not None:
                state.analysis.pre_computed_narratives = generate_all_narratives(state)
                pcn = state.analysis.pre_computed_narratives
                count = sum(
                    1
                    for f in [
                        pcn.company,
                        pcn.financial,
                        pcn.market,
                        pcn.governance,
                        pcn.litigation,
                        pcn.scoring,
                        pcn.ai_risk,
                    ]
                    if f is not None
                )
                logger.info(
                    "Pre-computed %d section narratives",
                    count,
                )
        except Exception:
            logger.warning(
                "Failed to generate section narratives",
                exc_info=True,
            )

    def _precompute_commentary(
        self,
        state: AnalysisState,
    ) -> None:
        """Pre-compute dual-voice commentary for RENDER stage (Phase 130).

        Generates 8 section commentaries with What Was Said + Underwriting
        Commentary voices. Cached on state.analysis.pre_computed_commentary.
        """
        if state.analysis is None:
            return

        # Cache guard: skip if commentary already exists (re-render reuse)
        if state.analysis.pre_computed_commentary is not None:
            return

        try:
            from do_uw.stages.benchmark.commentary_generator import (
                generate_all_commentary,
            )

            state.analysis.pre_computed_commentary = generate_all_commentary(state)
            pcc = state.analysis.pre_computed_commentary
            count = sum(
                1
                for f in [
                    pcc.executive_brief,
                    pcc.financial,
                    pcc.market,
                    pcc.governance,
                    pcc.litigation,
                    pcc.scoring,
                    pcc.company,
                    pcc.meeting_prep,
                ]
                if f is not None and (f.what_was_said or f.underwriting_commentary)
            )
            total_warnings = sum(
                len(f.hallucination_warnings)
                for f in [
                    pcc.executive_brief,
                    pcc.financial,
                    pcc.market,
                    pcc.governance,
                    pcc.litigation,
                    pcc.scoring,
                    pcc.company,
                    pcc.meeting_prep,
                ]
                if f is not None
            )
            logger.info(
                "Pre-computed %d section commentaries (%d hallucination warnings)",
                count,
                total_warnings,
            )
        except Exception:
            logger.warning(
                "Failed to generate section commentary",
                exc_info=True,
            )

    def _precompute_legacy_narratives(
        self,
        state: AnalysisState,
        scoring: Any,
    ) -> None:
        """Pre-compute thesis/risk/claim narratives (legacy path).

        Non-breaking: failures are logged and silently ignored.
        RENDER falls back to local computation if these are None.
        """
        try:
            from do_uw.stages.benchmark.narrative_helpers import (
                build_thesis_narrative,
            )

            state.benchmark.thesis_narrative = build_thesis_narrative(state)
        except Exception:
            logger.warning(
                "Failed to pre-compute thesis narrative",
                exc_info=True,
            )

        try:
            from do_uw.stages.benchmark.narrative_helpers import (
                build_risk_narrative,
            )

            if state.benchmark.inherent_risk is not None:
                state.benchmark.risk_narrative = build_risk_narrative(
                    state.benchmark.inherent_risk,
                    state,
                )
        except Exception:
            logger.warning(
                "Failed to pre-compute risk narrative",
                exc_info=True,
            )

        try:
            from do_uw.stages.benchmark.risk_levels import (
                score_to_risk_level,
            )

            if scoring.quality_score is not None:
                state.benchmark.risk_level = score_to_risk_level(
                    scoring.quality_score,
                )
        except Exception:
            logger.warning(
                "Failed to pre-compute risk level",
                exc_info=True,
            )

        try:
            from do_uw.stages.benchmark.narrative_helpers import (
                build_claim_narrative,
            )

            state.benchmark.claim_narrative = build_claim_narrative(state)
        except Exception:
            logger.warning(
                "Failed to pre-compute claim narrative",
                exc_info=True,
            )

    def _compute_forward_looking_intelligence(
        self,
        state: AnalysisState,
    ) -> None:
        """Compute forward-looking intelligence: credibility, risk, posture, triggers.

        Phase 117: Runs AFTER scoring and narratives are complete.
        Results stored on state.forward_looking (ForwardLookingData).
        """
        try:
            from do_uw.models.forward_looking import ForwardLookingData

            if state.forward_looking is None:
                state.forward_looking = ForwardLookingData()

            fl = state.forward_looking

            # 9a. Management credibility scoring
            from do_uw.stages.analyze.credibility_engine import (
                compute_credibility_score,
            )

            fl.credibility = compute_credibility_score(state)
            logger.info(
                "Credibility: %s (beat rate %.1f%%)",
                fl.credibility.credibility_level,
                fl.credibility.beat_rate_pct,
            )

            # 9b. Miss risk enrichment (needs credibility from 9a)
            from do_uw.stages.analyze.miss_risk import (
                enrich_forward_statements,
            )

            if fl.forward_statements and fl.credibility:
                fl.forward_statements = enrich_forward_statements(
                    fl.forward_statements,
                    fl.credibility,
                )
                logger.info(
                    "Enriched %d forward statements with miss risk",
                    len(fl.forward_statements),
                )

            # 9c. Monitoring triggers (company-specific thresholds)
            from do_uw.stages.benchmark.monitoring_triggers import (
                compute_monitoring_triggers,
            )

            fl.monitoring_triggers = compute_monitoring_triggers(state)
            logger.info(
                "Monitoring triggers: %d configured",
                len(fl.monitoring_triggers),
            )

            # 9d. Underwriting posture (needs scoring from SCORE stage)
            if state.scoring:
                from do_uw.stages.benchmark.underwriting_posture import (
                    generate_posture,
                    generate_watch_items,
                    verify_zero_factors,
                )

                fl.posture = generate_posture(state.scoring, state)
                fl.zero_verifications = verify_zero_factors(
                    state.scoring,
                    state,
                )
                fl.watch_items = generate_watch_items(state.scoring, state)
                logger.info(
                    "Posture: %s tier, %d overrides, %d watch items",
                    fl.posture.tier,
                    len(fl.posture.overrides_applied),
                    len(fl.watch_items),
                )

            # 9e. Quick screen / trigger matrix (needs signal results)
            signal_results: dict[str, object] = {}
            if state.analysis and state.analysis.signal_results:
                signal_results = state.analysis.signal_results
            from do_uw.stages.benchmark.quick_screen import (
                build_quick_screen,
            )

            fl.quick_screen = build_quick_screen(state, signal_results)
            logger.info(
                "Quick screen: %d nuclear checked, %d red, %d yellow",
                len(fl.quick_screen.nuclear_triggers),
                fl.quick_screen.red_count,
                fl.quick_screen.yellow_count,
            )

        except Exception:
            logger.warning(
                "Forward-looking intelligence computation failed",
                exc_info=True,
            )

    def _enrich_dossier(self, state: AnalysisState) -> None:
        """Enrich dossier data with D&O risk commentary and concentration assessment.

        Phase 118: Runs after scoring is complete so D&O commentary
        can reference scoring factors and tier.
        """
        try:
            from do_uw.stages.benchmark.dossier_enrichment import (
                enrich_dossier,
            )

            enrich_dossier(state)
            logger.info("Dossier enrichment complete")
        except Exception:
            logger.warning(
                "Dossier enrichment failed",
                exc_info=True,
            )


__all__ = ["BenchmarkStage"]
