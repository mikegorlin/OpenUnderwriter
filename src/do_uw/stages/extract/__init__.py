"""Extract stage: Parse filings and extract structured data.

Orchestrates all extraction modules in dependency order, collects
ExtractionReports, produces a consolidated validation summary, and
populates state.extracted with complete SECT2/SECT3/SECT4/SECT5/SECT6 data.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from do_uw.models.common import StageStatus
from do_uw.models.financials import (
    ExtractedFinancials,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.extract.audit_risk import extract_audit_risk
from do_uw.stages.extract.company_profile import extract_company_profile
from do_uw.stages.extract.debt_analysis import extract_debt_analysis
from do_uw.stages.extract.extract_ai_risk import run_ai_risk_extractors
from do_uw.stages.extract.extract_governance import run_governance_extractors
from do_uw.stages.extract.extract_litigation import run_litigation_extractors
from do_uw.stages.extract.extract_market import run_market_extractors
from do_uw.stages.extract.extraction_manifest import (
    ExtractionManifest,
    build_extraction_manifest,
)
from do_uw.stages.extract.field_key_collector import collect_extracted_field_keys
from do_uw.stages.extract.financial_narrative import generate_financial_narrative
from do_uw.stages.extract.financial_statements import (
    extract_financial_statements,
)
from do_uw.stages.extract.llm_extraction import run_llm_extraction
from do_uw.stages.extract.peer_group import construct_peer_group
from do_uw.stages.extract.sourced import (
    ensure_filing_texts,
    rehydrate_company_facts,
)
from do_uw.stages.extract.tax_indicators import extract_tax_indicators
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)

# Re-export for backward compatibility (tests import this private name)
_run_llm_extraction = run_llm_extraction


class ExtractStage:
    """Parse raw acquired data into structured models.

    Calls all extractors in dependency order:
    1. Company profile (SECT2)
    2. Financial statements (SECT3-02/03/04)
    3. Distress indicators (SECT3-07) -- depends on statements
    4. Earnings quality (SECT3-06) -- depends on statements
    5. Debt analysis (SECT3-08/09/10/11)
    6. Audit risk (SECT3-12)
    7. Tax indicators (SECT3-13)
    8. Peer group (SECT2-09 + SECT3-05)
    9. Financial health narrative (SECT3-01) -- depends on all above
    10. Market extractors (SECT4) -- via sub-orchestrator
    11. Governance extractors (SECT5) -- via sub-orchestrator
    12. Litigation extractors (SECT6) -- via sub-orchestrator
    """

    def __init__(
        self,
        peers: list[str] | None = None,
        use_llm: bool = True,
        progress_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._peers = peers
        self._use_llm = use_llm
        self._progress_fn = progress_fn
        self._manifest: ExtractionManifest | None = None

    @property
    def name(self) -> str:
        """Stage name."""
        return "extract"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify acquire stage is complete."""
        acquire = state.stages.get("acquire")
        if acquire is None or acquire.status != StageStatus.COMPLETED:
            msg = "Acquire stage must be completed before extract"
            raise ValueError(msg)
        if state.acquired_data is None:
            msg = "No acquired data available for extraction"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Run all extractors and populate state.extracted."""
        state.mark_stage_running(self.name)
        reports: list[ExtractionReport] = []
        try:
            # Pre-phase: Build extraction manifest from brain checks
            try:
                self._manifest = build_extraction_manifest()
                if self._manifest.requirements:
                    logger.info(
                        "Extraction manifest: %d field requirements across %d sources",
                        len(self._manifest.requirements),
                        len({r.primary_source for r in self._manifest.requirements.values()}),
                    )
            except Exception:
                logger.warning("Failed to build extraction manifest; continuing without manifest")
                self._manifest = None

            # Phase 0: Rehydrate large blobs stripped from state.json
            rehydrate_company_facts(state)

            # Phase 0a: Ensure filing texts are section-split
            ensure_filing_texts(state)

            # Phase 0b: LLM extraction (pre-step, parallel)
            llm_results = run_llm_extraction(
                state,
                self._use_llm,
                self._progress_fn,
                manifest=self._manifest,
            )
            if state.acquired_data is not None:
                state.acquired_data.llm_extractions = llm_results

            # Phase 1: Company profile (SECT2)
            profile, profile_report = extract_company_profile(state)
            state.company = profile
            reports.append(profile_report)

            # Phase 2: Financial statements (SECT3-02/03/04)
            statements, stmt_reports = extract_financial_statements(state)
            extracted = _ensure_extracted(state)
            extracted.financials = ExtractedFinancials(
                statements=statements,
            )
            reports.extend(stmt_reports)

            # Phase 3: Distress indicators (SECT3-07)
            from do_uw.stages.analyze.financial_models import (
                compute_distress_indicators,
            )

            sector = _get_sector(state)
            market_cap = _get_market_cap(state)
            distress, distress_reports = compute_distress_indicators(
                statements, sector, market_cap
            )
            extracted.financials.distress = distress
            reports.extend(distress_reports)

            # Phase 4: Earnings quality (SECT3-06)
            from do_uw.stages.analyze.earnings_quality import (
                compute_earnings_quality,
            )

            eq, eq_report = compute_earnings_quality(statements)
            extracted.financials.earnings_quality = eq
            reports.append(eq_report)

            # Phase 5: Debt analysis (SECT3-08/09/10/11)
            liquidity, leverage, debt_struct, refi, debt_reports = extract_debt_analysis(state)
            extracted.financials.liquidity = liquidity
            extracted.financials.leverage = leverage
            extracted.financials.debt_structure = debt_struct
            extracted.financials.refinancing_risk = refi
            reports.extend(debt_reports)

            # Phase 6: Audit risk (SECT3-12)
            audit, audit_report = extract_audit_risk(state)
            extracted.financials.audit = audit
            reports.append(audit_report)

            # Phase 7: Tax indicators (SECT3-13)
            tax, tax_report = extract_tax_indicators(state)
            extracted.financials.tax_indicators = tax
            reports.append(tax_report)

            # Phase 8: Peer group (SECT2-09 + SECT3-05)
            peers, peer_report = construct_peer_group(state, override_peers=self._peers)
            extracted.financials.peer_group = peers
            reports.append(peer_report)

            # Phase 8b: Quarterly updates (post-annual 10-Q aggregation)
            from do_uw.stages.extract.quarterly_integration import (
                aggregate_quarterly_updates,
            )

            extracted.financials.quarterly_updates = aggregate_quarterly_updates(state)

            # Phase 8c: yfinance 8-quarter trending data
            from do_uw.stages.extract.yfinance_quarterly import (
                extract_yfinance_quarterly,
            )

            extracted.financials.yfinance_quarterly = extract_yfinance_quarterly(state)

            # Phase 8d-8g: XBRL quarterly extraction + trends + reconciliation
            try:
                facts = None
                cik = None
                if state.acquired_data is not None:
                    facts = state.acquired_data.filings.get("company_facts")
                if state.company and state.company.identity.cik:
                    cik = state.company.identity.cik.value

                if facts and cik:
                    # Phase 8d: Extract quarterly XBRL data
                    from do_uw.stages.extract.xbrl_quarterly import (
                        extract_quarterly_xbrl,
                    )

                    quarterly = extract_quarterly_xbrl(facts, cik)
                    extracted.financials.quarterly_xbrl = quarterly
                    logger.info(
                        "XBRL quarterly: %d quarters extracted",
                        len(quarterly.quarters),
                    )

                    # Phase 8e: Trend computation (needs >= 2 quarters)
                    if quarterly.quarters and len(quarterly.quarters) >= 2:
                        from do_uw.stages.extract.xbrl_trends import (
                            compute_all_trends,
                        )

                        trends = compute_all_trends(quarterly)
                        state.pipeline_metadata["quarterly_trends"] = {
                            concept: {
                                "pattern": v.pattern,
                                "consecutive_decline": v.consecutive_decline,
                            }
                            for concept, v in trends.items()
                        }
                        logger.info(
                            "Quarterly trends: %d concepts analyzed",
                            len(trends),
                        )

                    # Phase 8f: XBRL/LLM reconciliation
                    from do_uw.stages.extract.xbrl_llm_reconciler import (
                        reconcile_quarterly,
                        cross_validate_yfinance,
                    )

                    recon = reconcile_quarterly(
                        quarterly,
                        extracted.financials.quarterly_updates,
                    )
                    logger.info(
                        "XBRL/LLM reconciliation: %d comparisons, %d divergences, %d XBRL wins",
                        recon.total_comparisons,
                        recon.divergences,
                        recon.xbrl_wins,
                    )
                    state.pipeline_metadata["xbrl_reconciliation"] = {
                        "total_comparisons": recon.total_comparisons,
                        "divergences": recon.divergences,
                        "xbrl_wins": recon.xbrl_wins,
                        "llm_fallbacks": recon.llm_fallbacks,
                    }

                    # Persist discrepancy warnings on state for audit appendix
                    if recon.discrepancy_warnings:
                        extracted.financials.reconciliation_warnings = [
                            dataclasses.asdict(w) for w in recon.discrepancy_warnings
                        ]
                        logger.warning(
                            "XBRL/LLM reconciliation: %d hallucination-level "
                            "discrepancies (>2x divergence) detected",
                            len(recon.discrepancy_warnings),
                        )

                    # Phase 8g: yfinance cross-validation
                    yf_recon = cross_validate_yfinance(
                        quarterly,
                        extracted.financials.yfinance_quarterly,
                    )
                    logger.info(
                        "yfinance cross-validation: %d comparisons, %d divergences",
                        yf_recon.total_comparisons,
                        yf_recon.divergences,
                    )
            except Exception as exc:
                logger.warning(
                    "XBRL quarterly extraction failed: %s",
                    exc,
                )

            # Phase 9: Financial health narrative (SECT3-01)
            narrative = generate_financial_narrative(extracted.financials)
            extracted.financials.financial_health_narrative = narrative

            # Phase 10: Market extractors (SECT4)
            extracted.market = run_market_extractors(
                state,
                reports,
                manifest=self._manifest,
            )

            # Phase 11: Governance extractors (SECT5)
            extracted.governance = run_governance_extractors(
                state,
                reports,
                manifest=self._manifest,
            )

            # Phase 12: Litigation extractors (SECT6)
            extracted.litigation = run_litigation_extractors(
                state,
                reports,
                manifest=self._manifest,
            )

            # Phase 12b: Text signal extraction (BIZ, FWRD, NLP checks)
            from do_uw.stages.analyze.text_signals import (
                extract_text_signals,
            )

            filing_texts_data = {}
            if state.acquired_data is not None:
                filing_texts_data = state.acquired_data.filings.get("filing_texts", {})
            if isinstance(filing_texts_data, dict) and filing_texts_data:
                extracted.text_signals = extract_text_signals(filing_texts_data)
                logger.info(
                    "Text signals: %d topics extracted (%d present)",
                    len(extracted.text_signals),
                    sum(
                        1
                        for s in extracted.text_signals.values()
                        if isinstance(s, dict) and s.get("present")
                    ),
                )

            # Phase 12c: 10-K year-over-year comparison
            try:
                from do_uw.stages.extract.ten_k_yoy import (
                    compute_yoy_comparison,
                )

                yoy = compute_yoy_comparison(state)
                if yoy is not None:
                    extracted.ten_k_yoy = yoy
                    logger.info(
                        "10-K YoY: %s vs %s — %d risk changes, %d disclosure changes",
                        yoy.current_year,
                        yoy.prior_year,
                        len(yoy.risk_factor_changes),
                        len(yoy.disclosure_changes),
                    )
            except Exception as exc:
                logger.warning(
                    "10-K YoY comparison failed: %s",
                    exc,
                )

            # Phase 13: AI risk extractors (SECT8)
            try:
                extracted.ai_risk = run_ai_risk_extractors(state, reports)
            except Exception:
                logger.warning("AI risk extraction failed; continuing without AI risk data")

            # Phase 14: Company Intelligence Dossier extraction (Phase 118)
            try:
                from do_uw.stages.extract.dossier_extraction import (
                    extract_dossier,
                )

                extract_dossier(state)
                logger.info(
                    "Dossier extraction complete: %d revenue card rows, %d emerging risks",
                    len(state.dossier.revenue_card),
                    len(state.dossier.emerging_risks),
                )
            except Exception:
                logger.warning(
                    "Dossier extraction failed",
                    exc_info=True,
                )

            # Phase 15: Stock drop catalyst enrichment (Phase 119)
            try:
                from do_uw.stages.extract.stock_catalyst import (
                    enrich_drops_with_prices_and_volume,
                    detect_stock_patterns,
                )
                from do_uw.stages.extract.stock_performance_summary import (
                    compute_multi_horizon_returns,
                    build_analyst_consensus,
                )

                mkt = state.extracted.market if state.extracted else None
                if mkt and mkt.stock_drops:
                    all_drops = (mkt.stock_drops.single_day_drops or []) + (
                        mkt.stock_drops.multi_day_drops or []
                    )
                    history = getattr(state.acquired_data, "market_data", {}) or {}
                    enrich_drops_with_prices_and_volume(
                        all_drops,
                        history.get("history_2y", {}),
                    )
                    state.stock_patterns = detect_stock_patterns(
                        all_drops,
                        trading_days_available=(
                            getattr(mkt.stock, "trading_days_available", None)
                            if mkt.stock
                            else None
                        ),
                    )
                # Multi-horizon returns
                if mkt and mkt.stock:
                    from do_uw.stages.extract.stock_drops import get_close_prices

                    history_data = (getattr(state.acquired_data, "market_data", {}) or {}).get(
                        "history_1y", {}
                    )
                    prices = get_close_prices(history_data)
                    td = getattr(mkt.stock, "trading_days_available", None)
                    state.multi_horizon_returns = compute_multi_horizon_returns(
                        prices,
                        trading_days_available=td,
                    )
                # Analyst consensus
                if mkt and mkt.analyst:
                    market_data = getattr(state.acquired_data, "market_data", {}) or {}
                    current = (
                        mkt.stock.current_price.value
                        if mkt.stock and mkt.stock.current_price
                        else None
                    )
                    state.analyst_consensus = build_analyst_consensus(
                        mkt.analyst,
                        market_data,
                        current,
                    )
                logger.info("Phase 15: Stock catalyst enrichment complete")
            except Exception:
                logger.warning(
                    "Phase 15: Stock catalyst enrichment failed",
                    exc_info=True,
                )

            # Phase 16: Alt data extraction (Phase 119)
            try:
                from do_uw.stages.extract.alt_data_extraction import (
                    extract_alt_data,
                )

                extract_alt_data(state)
                logger.info("Phase 16: Alt data extraction complete")
            except Exception:
                logger.warning(
                    "Phase 16: Alt data extraction failed",
                    exc_info=True,
                )

            # Phase 17: Competitive landscape extraction (Phase 119)
            try:
                import asyncio

                from do_uw.stages.extract.competitive_extraction import (
                    extract_competitive_landscape,
                )

                asyncio.run(extract_competitive_landscape(state))
                logger.info("Phase 17: Competitive landscape extraction complete")
            except Exception:
                logger.warning(
                    "Phase 17: Competitive landscape extraction failed",
                    exc_info=True,
                )

            # Validation summary
            _log_validation_summary(reports)

            # Extraction manifest gap report
            if self._manifest and self._manifest.requirements:
                # Mark fulfilled fields from extraction state
                extracted_keys = collect_extracted_field_keys(state)
                self._manifest.mark_fulfilled_batch(extracted_keys)

                # Also mark brain_fields from LLM extractions
                from do_uw.stages.extract.llm_helpers import (
                    collect_brain_fields,
                )

                brain_fields = collect_brain_fields(state)
                self._manifest.mark_fulfilled_batch(set(brain_fields.keys()))

                # Generate and log gap report
                gap_report = self._manifest.get_gap_report()
                logger.info(
                    "Extraction manifest coverage: %.1f%% (%d/%d requirements fulfilled)",
                    gap_report.coverage_pct,
                    gap_report.fulfilled,
                    gap_report.total_requirements,
                )

                # Log actionable gaps by source
                if gap_report.gaps:
                    by_source: dict[str, list[str]] = {}
                    for gap in gap_report.gaps:
                        by_source.setdefault(gap.source, []).append(gap.field_key)
                    for source, fields in sorted(by_source.items()):
                        logger.info(
                            "  Gaps [%s]: %s",
                            source,
                            ", ".join(fields[:5])
                            + (f" (+{len(fields) - 5})" if len(fields) > 5 else ""),
                        )

                # Store gap report in pipeline metadata
                state.pipeline_metadata["extraction_gaps"] = {
                    "total_requirements": gap_report.total_requirements,
                    "fulfilled": gap_report.fulfilled,
                    "coverage_pct": round(gap_report.coverage_pct, 1),
                    "gap_count": len(gap_report.gaps),
                    "gaps_by_source": {
                        source: len([g for g in gap_report.gaps if g.source == source])
                        for source in {g.source for g in gap_report.gaps}
                    },
                }

            # Persist extraction metadata for render footer
            now = datetime.now(tz=UTC)
            state.pipeline_metadata["data_freshness_date"] = now.strftime("%Y-%m-%d")
            state.pipeline_metadata["extraction_timestamp"] = now.isoformat()
            # If no LLM cost was set (cached/no-LLM run), leave it absent
            # rather than inserting zeros; render handles the missing case.

            state.mark_stage_completed(self.name)
        except Exception as exc:
            state.mark_stage_failed(self.name, str(exc))
            raise


# ---------------------------------------------------------------------------
# Small state helpers (kept here to avoid circular imports)
# ---------------------------------------------------------------------------


def _ensure_extracted(state: AnalysisState) -> ExtractedData:
    """Create ExtractedData on state if it doesn't exist."""
    if state.extracted is None:
        state.extracted = ExtractedData()
    return state.extracted


def _get_sector(state: AnalysisState) -> str:
    """Safely get sector from company identity."""
    if state.company and state.company.identity.sector:
        return state.company.identity.sector.value
    return "OTHER"


def _get_market_cap(state: AnalysisState) -> float | None:
    """Safely get market cap from company profile."""
    if state.company and state.company.market_cap:
        return state.company.market_cap.value
    return None


def _log_validation_summary(reports: list[ExtractionReport]) -> None:
    """Log consolidated extraction coverage summary."""
    total_expected = sum(len(r.expected_fields) for r in reports)
    total_found = sum(len(r.found_fields) for r in reports)
    overall_pct = (total_found / total_expected * 100.0) if total_expected > 0 else 0.0

    logger.info(
        "Extract stage: %d extractors, %d total fields expected, %d found (%.1f%% coverage)",
        len(reports),
        total_expected,
        total_found,
        overall_pct,
    )

    # Log any low-coverage extractors
    for report in reports:
        if report.coverage_pct < 50.0:
            logger.warning(
                "Low coverage [%s]: %.1f%% (%d/%d fields)",
                report.extractor_name,
                report.coverage_pct,
                len(report.found_fields),
                len(report.expected_fields),
            )


__all__ = ["ExtractStage"]
