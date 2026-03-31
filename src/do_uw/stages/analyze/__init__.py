"""Analyze stage: Execute checks and detect risk patterns.

Orchestrates the ANALYZE pipeline stage:
1. Pre-ANALYZE: Classification (Layer 1) + Hazard Profile (Layer 2)
2. Load 359 signals from brain/signals.json
3. Map data requirements, evaluate thresholds
4. Store results in state.analysis

The ANALYZE stage transforms raw extracted facts into evaluated check
results -- the evidence layer that the SCORE stage consumes to compute
factor scores and detect patterns.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.brain.brain_unified_loader import BrainLoader, load_signals
from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisResults, AnalysisState
from do_uw.stages.analyze.signal_engine import execute_signals
from do_uw.stages.analyze.signal_results import aggregate_results

logger = logging.getLogger(__name__)


def _extract_market_cap(state: AnalysisState) -> float | None:
    """Safely extract market cap from company profile."""
    if state.company is None or state.company.market_cap is None:
        return None
    return float(state.company.market_cap.value)


def _extract_sector_code(state: AnalysisState) -> str:
    """Safely extract sector code from company identity."""
    if (
        state.company is not None
        and state.company.identity.sector is not None
    ):
        return str(state.company.identity.sector.value)
    return "DEFAULT"


def _extract_years_public(state: AnalysisState) -> int | None:
    """Safely extract years since IPO from company profile."""
    if state.company is None or state.company.years_public is None:
        return None
    return int(state.company.years_public.value)


def _append_playbook_signals(
    brain: Any, playbook_id: str
) -> Any:
    """Append industry-specific signals from active playbook to brain config.

    Inlined from BrainKnowledgeLoader._append_industry_checks -- loads
    industry signals from the matching playbook and appends them to the
    standard signals list (deduped by signal id).
    """
    try:
        from do_uw.knowledge.playbooks import (
            get_industry_signals,
            load_playbooks,
        )
        from do_uw.knowledge.store import KnowledgeStore

        store = KnowledgeStore()
        load_playbooks(store)
        industry_checks = get_industry_signals(store, playbook_id)
        if not industry_checks:
            return brain

        raw_checks: list[dict[str, Any]] = brain.checks.get("signals", [])
        existing_ids: set[str] = {str(c.get("id", "")) for c in raw_checks}
        new_checks = [
            ic for ic in industry_checks
            if str(ic.get("id", "")) not in existing_ids
        ]

        if new_checks:
            merged = list(raw_checks) + new_checks
            logger.info(
                "Added %d industry signals from playbook %s",
                len(new_checks),
                playbook_id,
            )
            brain.checks = {
                **brain.checks,
                "signals": merged,
                "total_signals": len(merged),
            }
    except Exception:
        logger.debug("Could not append playbook signals", exc_info=True)

    return brain


def _run_classification_and_hazard(state: AnalysisState) -> None:
    """Run Layer 1 (classification) and Layer 2 (hazard profile) pre-ANALYZE.

    Both layers are computed before check execution so that the hazard
    profile IES is available for the SCORE stage.

    Wrapped in try/except so that classification/hazard failures do NOT
    prevent check execution (graceful degradation).
    """
    # Layer 1: Classification (pre-ANALYZE)
    try:
        from do_uw.stages.analyze.layers.classify import classify_company
        from do_uw.stages.analyze.layers.classify.classification_engine import (
            load_classification_config,
        )

        classification_config = load_classification_config()
        market_cap = _extract_market_cap(state)
        sector_code = _extract_sector_code(state)
        years_public = _extract_years_public(state)
        state.classification = classify_company(
            market_cap, sector_code, years_public, classification_config,
        )
        logger.info(
            "Classification: tier=%s, rate=%.2f%%, ipo_mult=%.1fx",
            state.classification.market_cap_tier.value,
            state.classification.base_filing_rate_pct,
            state.classification.ipo_multiplier,
        )
        # Wire classification to company.risk_classification for BIZ.CLASS checks
        if state.company is not None:
            from do_uw.models.common import Confidence, SourcedValue
            from do_uw.stages.extract.sourced import now

            tier = state.classification.market_cap_tier.value
            state.company.risk_classification = SourcedValue[str](
                value=tier,
                source="Classification Engine (Layer 1)",
                confidence=Confidence.HIGH,
                as_of=now(),
            )
    except Exception:
        logger.warning(
            "Classification failed; continuing without Layer 1",
            exc_info=True,
        )

    # Layer 2: Hazard Profile (pre-ANALYZE)
    if state.classification is not None:
        try:
            from do_uw.stages.analyze.layers.hazard import compute_hazard_profile
            from do_uw.stages.analyze.layers.hazard.hazard_engine import load_hazard_config

            weights_config, interactions_config = load_hazard_config()
            state.hazard_profile = compute_hazard_profile(
                state.extracted,
                state.company,
                state.classification,
                weights_config,
                interactions_config,
            )
            logger.info(
                "Hazard profile: IES=%.1f, multiplier=%.2fx, coverage=%.0f%%",
                state.hazard_profile.ies_score,
                state.hazard_profile.ies_multiplier,
                state.hazard_profile.data_coverage_pct,
            )
        except Exception:
            logger.warning(
                "Hazard profile failed; continuing without Layer 2",
                exc_info=True,
            )


def _run_temporal_engine(state: AnalysisState) -> None:
    """Layer 3a: Temporal change detection."""
    from do_uw.stages.analyze.temporal_engine import TemporalAnalyzer

    analyzer = TemporalAnalyzer()
    temporal_result = analyzer.analyze_all_temporal(
        state.extracted, state.company,
    )
    if state.analysis is not None:
        state.analysis.temporal_signals = temporal_result.model_dump()
    logger.info(
        "Temporal: %d signals, %d deteriorating",
        len(temporal_result.signals),
        sum(
            1
            for s in temporal_result.signals
            if s.classification == "DETERIORATING"
        ),
    )


def _run_forensic_composites(state: AnalysisState) -> None:
    """Layer 3b: Financial forensics composites (FIS, RQS, CFQS)."""
    from do_uw.stages.analyze.forensic_composites import (
        compute_cash_flow_quality_score,
        compute_financial_integrity_score,
        compute_revenue_quality_score,
    )

    fis = compute_financial_integrity_score(state.extracted)
    rqs = compute_revenue_quality_score(state.extracted)
    cfqs = compute_cash_flow_quality_score(state.extracted)
    if state.analysis is not None:
        state.analysis.forensic_composites = {
            "financial_integrity_score": fis.model_dump(),
            "revenue_quality_score": rqs.model_dump(),
            "cash_flow_quality_score": cfqs.model_dump(),
        }
    logger.info(
        "Forensics: FIS=%.0f (%s), RQS=%.0f, CFQS=%.0f",
        fis.overall_score,
        fis.zone,
        rqs.overall_score,
        cfqs.overall_score,
    )


def _run_executive_forensics_engine(state: AnalysisState) -> None:
    """Layer 3c: Executive forensics (person-level risk scoring)."""
    from do_uw.stages.analyze.executive_forensics import (
        run_executive_forensics,
    )

    board_risk = run_executive_forensics(state)
    if board_risk is not None and state.analysis is not None:
        state.analysis.executive_risk = board_risk.model_dump()
        logger.info(
            "Executive forensics: aggregate=%.0f, highest=%s",
            board_risk.weighted_score,
            board_risk.highest_risk_individual,
        )


def _run_nlp_engine(state: AnalysisState) -> None:
    """Layer 3d: NLP signals (readability, tone, risk factors)."""
    from do_uw.stages.analyze.nlp_signals import analyze_nlp_signals

    nlp_results = analyze_nlp_signals(state.extracted, prior_year_text=None, state=state)
    if state.analysis is not None:
        state.analysis.nlp_signals = nlp_results
    detected = sum(
        1
        for v in nlp_results.values()
        if isinstance(v, dict) and v.get("detected")
    )
    logger.info("NLP: %d signals detected", detected)


def _run_xbrl_forensics(state: AnalysisState) -> None:
    """Layer 3e: XBRL forensic analysis (Phase 69).

    Delegates to forensic_orchestrator.run_xbrl_forensics which runs
    all forensic modules. Extracted to keep __init__.py under 500 lines.
    """
    from do_uw.stages.analyze.forensic_orchestrator import (
        run_xbrl_forensics,
    )

    run_xbrl_forensics(state)


def _run_composites(state: AnalysisState) -> None:
    """Evaluate signal composites after individual signals have completed.

    Composites are brain-level grouped analysis: they read multiple signal
    results and produce CompositeResults with structured analytical conclusions.

    Phase 50 Plan 04: Initial wiring.
    """
    from pathlib import Path

    from do_uw.brain.brain_composite_engine import evaluate_composites
    from do_uw.brain.brain_composite_schema import load_all_composites

    composites_dir = Path(__file__).parent.parent.parent / "brain" / "composites"
    if not composites_dir.exists():
        logger.info("No composites directory found, skipping composite evaluation")
        return

    composite_defs = load_all_composites(composites_dir)
    if not composite_defs:
        logger.info("No composite definitions found")
        return

    signal_results = state.analysis.signal_results if state.analysis else {}
    composite_results = evaluate_composites(composite_defs, signal_results)

    if state.analysis is not None:
        state.analysis.composite_results = {
            cid: cr.model_dump() for cid, cr in composite_results.items()
        }
    logger.info(
        "Composites: %d evaluated, severities: %s",
        len(composite_results),
        {cid: cr.severity for cid, cr in composite_results.items()},
    )


def _run_analytical_engines(state: AnalysisState) -> None:
    """Run all Phase 26 analytical engines with graceful degradation.

    Each engine is wrapped in try/except so failures don't block
    stage completion. This follows the classification/hazard pattern.
    """
    if state.extracted is None:
        return

    for name, runner in [
        ("Temporal analysis", _run_temporal_engine),
        ("Forensic composites", _run_forensic_composites),
        ("Executive forensics", _run_executive_forensics_engine),
        ("NLP signals", _run_nlp_engine),
        ("XBRL forensics", _run_xbrl_forensics),
    ]:
        try:
            runner(state)
        except Exception:
            logger.warning("%s failed; continuing", name, exc_info=True)


def _record_signal_results(
    state: AnalysisState,
    results: list[Any],
) -> None:
    """Write per-check results to brain.duckdb.

    Non-critical telemetry: failures here do NOT break the pipeline.
    Records every check outcome so fire rates, skip rates, and dead
    checks can be identified across pipeline runs.
    """
    created_at = state.created_at
    run_id = f"{state.ticker}_{created_at.strftime('%Y%m%d_%H%M%S')}"

    # Single write: brain.duckdb only.
    # knowledge.db dual-write removed in Phase 45.
    try:
        from do_uw.brain.brain_effectiveness import (
            record_signal_runs_batch,
            update_effectiveness_table,
        )
        from do_uw.brain.brain_schema import connect_brain_db

        conn = connect_brain_db()
        rows = [
            {
                "run_id": run_id,
                "signal_id": r.signal_id,
                "signal_version": getattr(r, "signal_version", 1),
                "status": r.status.value,
                "value": str(r.value) if r.value is not None else None,
                "evidence": None,
                "ticker": state.ticker,
            }
            for r in results
        ]
        count = record_signal_runs_batch(conn, rows)
        update_effectiveness_table(conn, period="all_time")
        conn.close()
        logger.info(
            "Recorded %d check results to brain.duckdb for run %s",
            count, run_id,
        )
    except Exception:
        logger.warning(
            "Failed to record check results to brain.duckdb (non-fatal)",
            exc_info=True,
        )


def _reeval_forensic_signals(
    state: AnalysisState,
    checks: list[dict[str, Any]],
    results: list[Any],
) -> None:
    """Re-evaluate forensic signals after xbrl_forensics is populated.

    Forensic signals (FIN.FORENSIC.*, FIN.QUALITY.*) produce SKIPPED on
    their first pass because xbrl_forensics data is only populated by
    _run_analytical_engines (which runs AFTER execute_signals). This
    function runs a targeted second pass with the analysis parameter,
    replacing SKIPPED results with TRIGGERED/CLEAR where data exists.

    Phase 70-04 gap closure.
    """
    try:
        if state.analysis is None or state.analysis.xbrl_forensics is None:
            logger.debug("Skipping forensic re-eval: no xbrl_forensics data")
            return

        # Filter to forensic and quality signals only
        forensic_checks = [
            c for c in checks
            if c.get("execution_mode") == "AUTO"
            and (
                str(c.get("id", "")).startswith("FIN.FORENSIC.")
                or str(c.get("id", "")).startswith("FIN.QUALITY.")
            )
        ]
        if not forensic_checks:
            return

        logger.info(
            "Re-evaluating %d forensic signals with xbrl_forensics data",
            len(forensic_checks),
        )

        # Run second pass with analysis parameter
        reeval_results = execute_signals(
            forensic_checks,
            state.extracted,
            state.company,
            analysis=state.analysis,
        )

        # Build lookup of re-evaluated results
        reeval_map = {r.signal_id: r for r in reeval_results}

        # Merge: replace SKIPPED results with non-SKIPPED re-evaluated ones
        upgraded = 0
        for signal_id, new_result in reeval_map.items():
            if new_result.status.value == "SKIPPED":
                continue
            old = state.analysis.signal_results.get(signal_id)
            if old is not None and old.get("status") == "SKIPPED":
                state.analysis.signal_results[signal_id] = new_result.model_dump()
                upgraded += 1

        if upgraded > 0:
            # Recompute aggregate counts
            triggered_now = sum(
                1 for r in state.analysis.signal_results.values()
                if r.get("status") == "TRIGGERED"
            )
            clear_now = sum(
                1 for r in state.analysis.signal_results.values()
                if r.get("status") == "CLEAR"
            )
            skipped_now = sum(
                1 for r in state.analysis.signal_results.values()
                if r.get("status") == "SKIPPED"
            )
            state.analysis.checks_failed = triggered_now
            state.analysis.checks_passed = clear_now
            state.analysis.checks_skipped = skipped_now

        logger.info(
            "Forensic re-eval: %d signals upgraded from SKIPPED to TRIGGERED/CLEAR",
            upgraded,
        )
    except Exception:
        logger.warning(
            "Forensic re-evaluation failed (non-fatal)", exc_info=True
        )


class AnalyzeStage:
    """Execute analysis checks and detect risk patterns.

    Loads all 359 signals from brain/signals.json, filters to AUTO
    execution mode, maps data from ExtractedData, evaluates thresholds,
    and populates state.analysis with results.
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "analyze"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify extract stage is complete."""
        extract = state.stages.get("extract")
        if extract is None or extract.status != StageStatus.COMPLETED:
            msg = "Extract stage must be completed before analyze"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Execute all checks against extracted data.

        1. Load brain config (signals.json and all knowledge files)
        2. Extract checks list
        3. Validate extracted data exists
        4. Execute checks against extracted data
        5. Aggregate results into counts
        6. Populate state.analysis with results
        """
        state.mark_stage_running(self.name)

        # Pre-ANALYZE: Classification + Hazard Profile
        _run_classification_and_hazard(state)

        try:
            # Load brain config (with industry playbook if active)
            #
            # BrainLoader reads YAML signals + JSON configs directly.
            # Industry playbook signals are appended if active.
            #
            loader = BrainLoader()
            brain = loader.load_all()

            # Append industry playbook signals if active
            playbook_id = state.active_playbook_id
            if playbook_id:
                brain = _append_playbook_signals(brain, playbook_id)

            # Get checks list
            raw_checks = brain.checks.get("signals", [])
            if not isinstance(raw_checks, list):
                msg = "brain.signals['signals'] is not a list"
                raise ValueError(msg)
            checks = cast(list[dict[str, Any]], raw_checks)
            logger.info("Loaded %d signals from brain/signals.json", len(checks))

            # Validate extracted data exists
            if state.extracted is None:
                msg = "state.extracted is None -- EXTRACT stage did not populate data"
                raise ValueError(msg)

            # Execute checks
            # Pass benchmarks if available (populated by prior BENCHMARK stage
            # or from cached state). Peer comparison signals use these.
            results = execute_signals(
                checks, state.extracted, state.company,
                benchmarks=getattr(state, "benchmark", None),
            )

            # Aggregate counts
            counts = aggregate_results(results)

            # Populate state.analysis
            state.analysis = AnalysisResults(
                checks_executed=counts["executed"],
                checks_passed=counts["passed"],
                checks_failed=counts["failed"],
                checks_skipped=counts["skipped"],
                signal_results={
                    r.signal_id: r.model_dump() for r in results
                },
            )

            logger.info(
                "Analyze: %d executed, %d triggered, %d clear, %d skipped, %d info",
                counts["executed"],
                counts["failed"],
                counts["passed"],
                counts["skipped"],
                counts["info"],
            )

            # Phase 46: Gap search re-evaluation
            # Apply brain_targeted_search results to SKIPPED checks.
            # Must run BEFORE _run_analytical_engines so temporal/forensic engines
            # see the updated check statuses.
            if state.acquired_data is not None:
                try:
                    from do_uw.stages.analyze.gap_revaluator import apply_gap_search_results
                    gap_summary = apply_gap_search_results(
                        state.acquired_data, state.analysis
                    )
                    if gap_summary["updated"] > 0:
                        # Recompute aggregate counts after gap re-evaluation
                        # (count statuses directly since we modified signal_results in-place)
                        triggered_now = sum(
                            1 for r in state.analysis.signal_results.values()
                            if r.get("status") == "TRIGGERED"
                        )
                        clear_now = sum(
                            1 for r in state.analysis.signal_results.values()
                            if r.get("status") == "CLEAR"
                        )
                        skipped_now = sum(
                            1 for r in state.analysis.signal_results.values()
                            if r.get("status") == "SKIPPED"
                        )
                        state.analysis.checks_failed = triggered_now
                        state.analysis.checks_passed = clear_now
                        state.analysis.checks_skipped = skipped_now
                        logger.info(
                            "Post-gap counts: %d triggered, %d clear, %d skipped",
                            triggered_now, clear_now, skipped_now,
                        )
                    # Store gap summary for QA audit template (always set, even if updated=0)
                    state.analysis.gap_search_summary = gap_summary
                except Exception:
                    logger.warning(
                        "Gap re-evaluation failed (non-fatal)", exc_info=True
                    )

            # Phase 139: Contextual signal validation (annotate false positives)
            try:
                from do_uw.stages.analyze.contextual_validator import validate_signals
                val_summary = validate_signals(state.analysis.signal_results, state)
                logger.info(
                    "Contextual validation: %d signals checked, %d annotations added",
                    val_summary["signals_checked"],
                    val_summary["annotations_added"],
                )
            except Exception:
                logger.warning("Contextual validation failed (non-fatal)", exc_info=True)

            # Phase 50: Signal composites (brain-level grouped analysis)
            try:
                _run_composites(state)
            except Exception:
                logger.warning("Composite evaluation failed (non-fatal)", exc_info=True)

            # Phase 26: Enhanced analytical engines (graceful degradation)
            _run_analytical_engines(state)

            # Phase 70-04 gap closure: Re-evaluate forensic signals now that
            # xbrl_forensics is populated by _run_analytical_engines.
            _reeval_forensic_signals(state, checks, results)

            # Phase 29: Pre-compute section density assessments for RENDER
            from do_uw.stages.analyze.section_assessments import (
                compute_section_assessments,
            )

            compute_section_assessments(state)

            # Phase 30: Record per-check results for feedback loop
            _record_signal_results(state, results)

            # Phase 78: Build disposition audit trail (AUDIT-01)
            try:
                from do_uw.stages.analyze.signal_disposition import (
                    build_dispositions,
                )

                all_signals = load_signals()["signals"]
                disp_summary = build_dispositions(
                    all_signals, state.analysis.signal_results,
                )
                state.analysis.disposition_summary = disp_summary.model_dump()
                logger.info(
                    "Disposition audit: %d total — %d triggered, %d clean, %d skipped, %d inactive",
                    disp_summary.total,
                    disp_summary.triggered_count,
                    disp_summary.clean_count,
                    disp_summary.skipped_count,
                    disp_summary.inactive_count,
                )
            except Exception:
                logger.warning("Disposition tagging failed", exc_info=True)

            state.mark_stage_completed(self.name)

        except Exception as exc:
            state.mark_stage_failed(self.name, str(exc))
            raise


__all__ = ["AnalyzeStage"]
