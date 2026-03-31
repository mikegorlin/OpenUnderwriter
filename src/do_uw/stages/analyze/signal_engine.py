"""Signal execution engine for the ANALYZE stage.

Loads signals from brain/signals.json, maps data requirements to
ExtractedData fields, evaluates thresholds, produces SignalResult objects.

Threshold types: tiered, info, percentage, boolean, count, value,
pattern, search, multi_period, classification, temporal, display.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from do_uw.stages.analyze.signal_evaluators import (
    evaluate_boolean,
    evaluate_info_only,
    evaluate_numeric_threshold,
    evaluate_temporal,
    evaluate_tiered,
)
from do_uw.stages.analyze.signal_helpers import (
    INFO_ONLY_TYPES,
    coerce_value,
    extract_factors,
    first_data_value,
    make_skipped,
)
from do_uw.stages.analyze.do_context_engine import apply_do_context
from do_uw.stages.analyze.signal_results import DataStatus, SignalResult, SignalStatus

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

CHUNK_SIZE = 50
"""Number of signals per progress log message."""


def execute_signals(
    signals: list[dict[str, Any]],
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    run_id: str = "",
    ticker: str = "",
    analysis: Any | None = None,
    benchmarks: Any | None = None,
) -> list[SignalResult]:
    """Execute all AUTO-mode signals against extracted data.

    Filters to execution_mode == "AUTO" signals, then iterates in
    CHUNK_SIZE batches, calling map_signal_data() then evaluate_signal()
    for each.

    Args:
        signals: List of signal config dicts from brain/signals.json.
        extracted: The ExtractedData populated by the EXTRACT stage.
        company: Optional CompanyProfile for section 1-2 company signals.
        run_id: Optional run identifier for telemetry logging.
        ticker: Optional ticker symbol for telemetry logging.
        analysis: Optional AnalysisResults for xbrl_forensics data (Phase 70-04).
        benchmarks: Optional BenchmarkResult with frames_percentiles for peer comparison.

    Returns:
        List of SignalResult objects, one per evaluated signal.
    """
    from do_uw.stages.analyze.signal_mappers import map_signal_data

    from do_uw.brain.dependency_graph import order_signals_for_execution

    auto_signals = [
        c for c in signals if c.get("execution_mode") == "AUTO"
    ]
    auto_signals = order_signals_for_execution(auto_signals)
    total = len(auto_signals)
    logger.info("Executing %d AUTO signals (of %d total)", total, len(signals))

    # Extract company SIC sector for NOT_APPLICABLE signals
    company_sic: str | None = None
    if company is not None and company.identity.sic_code is not None:
        company_sic = str(company.identity.sic_code.value)

    # Extract company name for do_context template rendering
    _company_name: str = ""
    if company is not None:
        try:
            _company_name = str(company.identity.name) if company.identity.name else ""
        except (AttributeError, TypeError):
            _company_name = ""

    results: list[SignalResult] = []
    # Accumulated results dict for mechanism evaluators (Phase 110).
    # Mechanism signals (conjunction/absence/contextual) are inference-class
    # and run AFTER standard signals, so this dict has all standard results.
    signal_results_dict: dict[str, dict[str, Any]] = {}

    for i in range(0, total, CHUNK_SIZE):
        chunk = auto_signals[i : i + CHUNK_SIZE]
        chunk_end = min(i + CHUNK_SIZE, total)
        logger.info(
            "Processing signals %d-%d of %d", i + 1, chunk_end, total
        )

        for sig in chunk:
            signal_id: str = sig.get("id", "UNKNOWN")

            # Skip foundational signals (Tier 1 manifest — not evaluatable)
            if sig.get("signal_class") == "foundational":
                logger.debug("Skipping foundational signal: %s", signal_id)
                continue

            # NOT_APPLICABLE: sector-specific signals for wrong sector
            if not _signal_sector_applicable(sig, company_sic):
                result = SignalResult(
                    signal_id=signal_id,
                    signal_name=sig.get("name", ""),
                    status=SignalStatus.SKIPPED,
                    evidence=f"Signal not applicable to company sector (SIC: {company_sic})",
                    factors=extract_factors(sig),
                    section=sig.get("section", 0),
                    content_type=sig.get("content_type", "EVALUATIVE_CHECK"),
                    data_status=DataStatus.NOT_APPLICABLE,
                    data_status_reason=f"Sector filter {sig.get('sector_filter')} does not match SIC {company_sic}",
                )
                result = _apply_classification_metadata(result, sig)
                result = _apply_traceability(result, sig, "not_applicable")
                result = apply_do_context(result, sig, _company_name, ticker)
                results.append(result)
                signal_results_dict[signal_id] = {
                    "status": result.status.value,
                    "data_status": result.data_status,
                }
                continue

            # Phase 110: Mechanism-based dispatch (conjunction/absence/contextual)
            # Phase 111-02: Extended with trend and peer_comparison
            mechanism = _get_mechanism(sig)
            if mechanism in ("conjunction", "absence", "contextual"):
                result = _dispatch_mechanism(
                    mechanism, sig, signal_results_dict, company,
                )
                result = _apply_classification_metadata(result, sig)
                result = _apply_traceability(result, sig, mechanism)
                result = apply_do_context(result, sig, _company_name, ticker)
                result.content_type = sig.get("content_type", "EVALUATIVE_CHECK")
                results.append(result)
                signal_results_dict[signal_id] = {
                    "status": result.status.value,
                    "value": result.value,
                    "threshold_level": result.threshold_level,
                    "data_status": result.data_status,
                }
                continue

            # Phase 111-03: YAML-driven resolver primary, old mapper fallback
            from do_uw.stages.analyze.signal_resolver import resolve_signal_data
            data = resolve_signal_data(sig, _build_resolver_state(extracted, company, analysis, benchmarks))
            if not data:
                # Resolver returned empty — fall back to old mapper
                data = map_signal_data(signal_id, sig, extracted, company, analysis=analysis)
            else:
                # Resolver succeeded — still narrow via data_strategy.field_key
                # to match mapper contract (single field for threshold eval)
                ds = sig.get("data_strategy")
                if isinstance(ds, dict):
                    fk = ds.get("field_key", "")
                    if fk and "." not in fk:
                        # Plain field key (not dotted path) — check if it's in resolved data
                        if fk not in data:
                            # The resolver used dotted paths, mapper uses plain keys
                            # Fall back to mapper for backward compat
                            data = map_signal_data(signal_id, sig, extracted, company, analysis=analysis)

            # Phase 111-02: Trend and peer_comparison mechanism dispatch
            # These need mapped data (unlike conjunction/absence/contextual),
            # so they run AFTER map_signal_data. If the mechanism evaluator
            # returns SKIPPED but data exists, fall through to standard
            # threshold evaluation to prevent regression.
            if mechanism in ("trend", "peer_comparison"):
                result = _dispatch_mechanism(
                    mechanism, sig, signal_results_dict, company,
                    data=data, benchmarks=benchmarks,
                )
                # Regression guard: if mechanism evaluator SKIPPED but
                # mapper provided data, fall through to threshold evaluation
                if result.status == SignalStatus.SKIPPED and data:
                    has_real_data = any(
                        v is not None
                        for k, v in data.items()
                        if not k.startswith("_")
                    )
                    if has_real_data:
                        logger.debug(
                            "Trend/peer evaluator SKIPPED for %s but data exists; "
                            "falling through to threshold evaluation",
                            signal_id,
                        )
                        # Fall through to standard evaluation below
                    else:
                        result = _apply_classification_metadata(result, sig)
                        result = _apply_traceability(result, sig, mechanism)
                        result = apply_do_context(result, sig, _company_name, ticker)
                        result.content_type = sig.get("content_type", "EVALUATIVE_CHECK")
                        _determine_data_status(sig, data, result)
                        results.append(result)
                        signal_results_dict[signal_id] = {
                            "status": result.status.value,
                            "value": result.value,
                            "threshold_level": result.threshold_level,
                            "data_status": result.data_status,
                        }
                        continue
                else:
                    result = _apply_classification_metadata(result, sig)
                    result = _apply_traceability(result, sig, mechanism)
                    result = apply_do_context(result, sig, _company_name, ticker)
                    result.content_type = sig.get("content_type", "EVALUATIVE_CHECK")
                    _determine_data_status(sig, data, result)
                    results.append(result)
                    signal_results_dict[signal_id] = {
                        "status": result.status.value,
                        "value": result.value,
                        "threshold_level": result.threshold_level,
                        "data_status": result.data_status,
                    }
                    continue

            # Content-type-aware dispatch (Phase 32-05, updated 32-10):
            # MANAGEMENT_DISPLAY -> INFO-only (verify data presence)
            # INFERENCE_PATTERN -> multi-signal detection via inference_evaluator
            # EVALUATIVE_CHECK -> existing evaluate_signal (default)
            content_type = sig.get("content_type", "EVALUATIVE_CHECK")
            if content_type == "MANAGEMENT_DISPLAY":
                result = evaluate_management_display(sig, data)
                result = apply_do_context(result, sig, _company_name, ticker)
            elif content_type == "INFERENCE_PATTERN":
                from do_uw.stages.analyze.inference_evaluator import evaluate_inference_pattern
                result = evaluate_inference_pattern(sig, data)
                result = _apply_classification_metadata(result, sig)
                result = _apply_traceability(result, sig, "inference_pattern")
                result = apply_do_context(result, sig, _company_name, ticker)
            else:
                result = evaluate_signal(sig, data, company=company)
                result = apply_do_context(result, sig, _company_name, ticker)

            # Propagate content_type onto result for RENDER display dispatch
            result.content_type = content_type

            _determine_data_status(sig, data, result)
            results.append(result)
            # Track result for mechanism evaluators
            signal_results_dict[signal_id] = {
                "status": result.status.value,
                "value": result.value,
                "threshold_level": result.threshold_level,
                "data_status": result.data_status,
            }

    logger.info("Signal execution complete: %d results", len(results))

    # Phase 111-03: Emit DEFERRED signals into results with distinct status.
    # DEFERRED signals are not evaluated but show "Data pending" in worksheet.
    deferred_signals = [
        c for c in signals
        if c.get("execution_mode") == "DEFERRED"
        and c.get("signal_class") != "foundational"
    ]
    for sig in deferred_signals:
        signal_id = sig.get("id", "UNKNOWN")
        result = SignalResult(
            signal_id=signal_id,
            signal_name=sig.get("name", ""),
            status=SignalStatus.SKIPPED,
            evidence="Data pending — extraction not yet available",
            factors=extract_factors(sig),
            section=sig.get("section", 0),
            content_type=sig.get("content_type", "EVALUATIVE_CHECK"),
            data_status="DEFERRED",
            data_status_reason="Signal deferred: data source not yet wired in pipeline",
        )
        result = _apply_classification_metadata(result, sig)
        result = _apply_traceability(result, sig, "deferred")
        result = apply_do_context(result, sig, _company_name, ticker)
        results.append(result)
    if deferred_signals:
        logger.info("Emitted %d DEFERRED signals", len(deferred_signals))

    # Post-evaluation: enrich results with structured details for composites
    from do_uw.stages.analyze.signal_details import enrich_signal_details

    enrich_signal_details(results, extracted)

    return results


# ---------------------------------------------------------------------------
# Helpers used only by the engine dispatcher
# ---------------------------------------------------------------------------


def _build_resolver_state(
    extracted: Any,
    company: Any,
    analysis: Any,
    benchmarks: Any,
) -> Any:
    """Build a state-like proxy for the generic resolver.

    The resolver expects to traverse an AnalysisState-like object with
    .extracted, .company, .analysis, and .benchmark attributes.
    """

    class _ResolverState:
        pass

    state = _ResolverState()
    state.extracted = extracted  # type: ignore[attr-defined]
    state.company = company  # type: ignore[attr-defined]
    state.analysis = analysis  # type: ignore[attr-defined]
    state.benchmark = benchmarks  # type: ignore[attr-defined]
    return state


def _get_mechanism(sig: dict[str, Any]) -> str:
    """Extract evaluation mechanism from signal config.

    Returns 'threshold' (default) if no mechanism specified.
    """
    eval_spec = sig.get("evaluation")
    if isinstance(eval_spec, dict):
        return str(eval_spec.get("mechanism", "threshold"))
    return "threshold"


def _dispatch_mechanism(
    mechanism: str,
    sig: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
    company: Any | None,
    *,
    data: dict[str, Any] | None = None,
    benchmarks: Any | None = None,
) -> SignalResult:
    """Dispatch to mechanism-specific evaluator (Phase 110, extended 111-02).

    Args:
        mechanism: One of 'conjunction', 'absence', 'contextual', 'trend', 'peer_comparison'.
        sig: Signal config dict.
        signal_results: Accumulated results from prior signal evaluations.
        company: Optional CompanyProfile.
        data: Mapped data dict (required for trend and peer_comparison).
        benchmarks: Optional BenchmarkResult for peer_comparison evaluator.

    Returns:
        SignalResult from the mechanism evaluator.
    """
    from do_uw.stages.analyze.mechanism_evaluators import (
        evaluate_absence,
        evaluate_conjunction,
        evaluate_contextual,
        evaluate_peer_comparison,
        evaluate_trend,
    )

    if mechanism == "conjunction":
        return evaluate_conjunction(sig, {}, signal_results)
    elif mechanism == "absence":
        return evaluate_absence(sig, {}, signal_results, company=company)
    elif mechanism == "contextual":
        # Build company context from CompanyProfile if available
        company_context = _build_company_context(company)
        return evaluate_contextual(
            sig, {}, signal_results,
            company=company,
            company_context=company_context,
        )
    elif mechanism == "trend":
        return evaluate_trend(sig, data or {}, signal_results)
    elif mechanism == "peer_comparison":
        # Extract frames_percentiles from BenchmarkResult if available
        frames_pct: dict[str, Any] | None = None
        if benchmarks is not None:
            frames_pct = getattr(benchmarks, "frames_percentiles", None)
        return evaluate_peer_comparison(
            sig, data or {}, signal_results, benchmarks=frames_pct,
        )
    else:
        logger.warning("Unknown mechanism '%s' for signal %s", mechanism, sig.get("id"))
        return make_skipped(sig, {})


def _build_company_context(company: Any | None) -> dict[str, str]:
    """Build company context dict from CompanyProfile for contextual evaluators.

    Determines lifecycle_stage, size_tier, and sector from company attributes.
    Returns empty dict if company is None or attributes unavailable.
    """
    if company is None:
        return {}

    ctx: dict[str, str] = {}

    # Lifecycle stage
    try:
        years_public = getattr(company, "years_public", None)
        if years_public is not None:
            yp = float(years_public.value) if hasattr(years_public, "value") else float(years_public)
            if yp < 1:
                ctx["lifecycle_stage"] = "pre_revenue"
            elif yp < 3:
                ctx["lifecycle_stage"] = "post_ipo"
            elif yp > 10:
                ctx["lifecycle_stage"] = "mature"
            else:
                ctx["lifecycle_stage"] = "growth"
    except (TypeError, ValueError, AttributeError):
        pass

    # Size tier
    try:
        market_cap = getattr(company, "market_cap", None)
        if market_cap is not None:
            mc = float(market_cap.value) if hasattr(market_cap, "value") else float(market_cap)
            if mc < 2e9:
                ctx["size_tier"] = "small_cap"
            elif mc < 10e9:
                ctx["size_tier"] = "mid_cap"
            elif mc < 200e9:
                ctx["size_tier"] = "large_cap"
            else:
                ctx["size_tier"] = "mega_cap"
    except (TypeError, ValueError, AttributeError):
        pass

    # Sector from SIC
    try:
        sic = getattr(company, "identity", None)
        if sic is not None:
            sic_code = getattr(sic, "sic_code", None)
            if sic_code is not None:
                code = int(sic_code.value) if hasattr(sic_code, "value") else int(sic_code)
                if 6000 <= code < 6800:
                    ctx["sector"] = "financial"
                elif code in range(3570, 3580) or code in range(3670, 3680) or code in range(7370, 7380):
                    ctx["sector"] = "tech"
                elif 2830 <= code < 2837 or 3841 <= code < 3852 or 8000 <= code < 8100:
                    ctx["sector"] = "healthcare"
                elif 4900 <= code < 4950:
                    ctx["sector"] = "utilities"
                elif 6500 <= code < 6600:
                    ctx["sector"] = "real_estate"
                elif 4800 <= code < 4900:
                    ctx["sector"] = "communication"
                elif 1000 <= code < 1500 or 4900 <= code < 5000:
                    ctx["sector"] = "energy"
                elif 5000 <= code < 6000:
                    ctx["sector"] = "consumer"
                elif 2000 <= code < 4000:
                    ctx["sector"] = "industrial"
    except (TypeError, ValueError, AttributeError):
        pass

    return ctx


def _determine_data_status(
    sig: dict[str, Any],
    data: dict[str, Any],
    result: SignalResult,
) -> SignalResult:
    """Set data_status on a SignalResult based on evaluation outcome.

    - SKIPPED status -> DATA_UNAVAILABLE (already handled in make_skipped)
    - TRIGGERED/CLEAR/INFO -> EVALUATED (the default, usually no-op)
    - sector_filter mismatch -> NOT_APPLICABLE

    Returns the mutated result for chaining convenience.
    """
    # Check if mapper signaled NOT_APPLICABLE (e.g., biotech events)
    if data.get("_not_applicable"):
        result.status = SignalStatus.SKIPPED
        result.data_status = DataStatus.NOT_APPLICABLE
        result.data_status_reason = "Signal not applicable to this company type"
        result.evidence = "Not applicable"
        return result

    if result.status == SignalStatus.SKIPPED:
        # Already set by make_skipped, but ensure consistency
        if result.data_status != DataStatus.DATA_UNAVAILABLE:
            result.data_status = DataStatus.DATA_UNAVAILABLE
            if not result.data_status_reason:
                result.data_status_reason = (
                    "Required data not available from filings"
                    if data
                    else "Data mapping not configured for this signal"
                )
    # EVALUATED is the default -- no action needed for TRIGGERED/CLEAR/INFO
    return result


def _signal_sector_applicable(
    sig: dict[str, Any],
    company_sic: str | None,
) -> bool:
    """Return True if the signal applies to this company's sector.

    If the signal has a "sector_filter" field in config and the company's
    SIC sector does not match, the signal is NOT_APPLICABLE.
    Returns True (applicable) if no sector_filter or no company SIC.
    """
    sector_filter = sig.get("sector_filter")
    if not sector_filter or not company_sic:
        return True
    if isinstance(sector_filter, list):
        return company_sic in sector_filter
    return str(sector_filter) == company_sic


# ---------------------------------------------------------------------------
# Classification metadata and traceability
# ---------------------------------------------------------------------------


def _apply_classification_metadata(
    result: SignalResult, sig: dict[str, Any],
) -> SignalResult:
    """Copy Phase 26 classification fields from signal config to result."""
    for field in ("category", "signal_type", "hazard_or_signal"):
        if field in sig:
            setattr(result, field, str(sig[field]))
    lenses = sig.get("plaintiff_lenses")
    if isinstance(lenses, list):
        result.plaintiff_lenses = [str(lens) for lens in lenses]
    return result


def _apply_traceability(
    result: SignalResult, sig: dict[str, Any], ttype: str,
) -> SignalResult:
    """Populate the 5-link traceability chain from the signal definition.

    Reads directly from the signal dict fields -- no significant logic.
    """
    # Link 1 (DATA_SOURCE) + Link 2 (EXTRACTION): from required_data / data_locations
    req_data = sig.get("required_data", [])
    data_locs = sig.get("data_locations", {})
    if isinstance(data_locs, dict) and data_locs:
        loc_parts = []
        for src, fields in data_locs.items():
            if isinstance(fields, list):
                loc_parts.append(f"{src}:{','.join(str(f) for f in fields)}")
            else:
                loc_parts.append(f"{src}:{fields}")
        result.trace_data_source = "; ".join(loc_parts)
    elif isinstance(data_locs, list) and data_locs:
        result.trace_data_source = ",".join(str(loc) for loc in data_locs)
    elif req_data:
        result.trace_data_source = ",".join(str(r) for r in req_data)

    # Extraction: derive module from required_data prefixes
    _SOURCE_TO_EXTRACTOR: dict[str, str] = {
        "SEC_10K": "xbrl_extractor",
        "SEC_PROXY": "proxy_extractor",
        "XBRL": "xbrl_extractor",
        "MARKET": "market_signals_extractor",
        "STOCK": "market_signals_extractor",
        "SCAC_SEARCH": "litigation_extractor",
        "LITIGATION": "litigation_extractor",
        "SEC_ENFORCEMENT": "litigation_extractor",
        "NLP": "text_signals_extractor",
        "INSIDER": "market_signals_extractor",
    }
    extractors = []
    for src in req_data:
        ext = _SOURCE_TO_EXTRACTOR.get(str(src), f"{str(src).lower()}_extractor")
        if ext not in extractors:
            extractors.append(ext)
    result.trace_extraction = ",".join(extractors) if extractors else ""

    # Link 3 (EVALUATION): threshold type + level hit
    level = result.threshold_level
    if level:
        result.trace_evaluation = f"{ttype}_threshold:{level}"
    elif result.status == SignalStatus.SKIPPED:
        result.trace_evaluation = "skipped:data_unavailable"
    elif result.status == SignalStatus.INFO:
        result.trace_evaluation = f"info_display:{ttype}"
    else:
        result.trace_evaluation = f"{ttype}:{result.status.value.lower()}"

    # Link 4 (OUTPUT): section + pillar
    section = sig.get("section", 0)
    pillar = sig.get("pillar", "")
    result.trace_output = f"SECT{section}:{pillar}" if pillar else f"SECT{section}"

    # Link 5 (SCORING): factors list
    factors = result.factors
    if factors:
        result.trace_scoring = ",".join(factors)
    else:
        result.trace_scoring = "none:context_only"

    # QA-03: Populate threshold_context when signal triggers
    if result.status == SignalStatus.TRIGGERED:
        raw_threshold = sig.get("threshold", {})
        threshold = cast(dict[str, Any], raw_threshold) if isinstance(raw_threshold, dict) else {}
        level = result.threshold_level  # "red" or "yellow"
        criterion_text = threshold.get(level) if level else None
        if not criterion_text and threshold.get("triggered"):
            # Boolean threshold signals use "triggered" key instead of "red"/"yellow"
            criterion_text = threshold.get("triggered")
        if criterion_text:
            result.threshold_context = f"{level}: {criterion_text}" if level else str(criterion_text)

    return result


# ---------------------------------------------------------------------------
# Content-type evaluators
# ---------------------------------------------------------------------------


def evaluate_management_display(
    sig: dict[str, Any],
    data: dict[str, Any],
) -> SignalResult:
    """Evaluate a MANAGEMENT_DISPLAY signal: verify data presence only.

    MANAGEMENT_DISPLAY signals exist to surface management-reported data
    (e.g., revenue segments, geographic footprint, executive list) without
    threshold evaluation. They report INFO when data is present, SKIPPED
    when data is unavailable.

    This function does NOT evaluate thresholds. It verifies data presence
    only. The 64 MANAGEMENT_DISPLAY signals get proper INFO-only evaluation
    instead of being forced through threshold evaluation (which many would
    SKIP because they have no meaningful thresholds).

    Args:
        sig: Signal config dict with id, name, section, factors, etc.
        data: Mapped data dict from map_signal_data().

    Returns:
        SignalResult with status=INFO if data present, SKIPPED if absent.
    """
    data_value, data_key = first_data_value(data)

    if data_value is None:
        result = make_skipped(sig, data)
        result = _apply_classification_metadata(result, sig)
        return _apply_traceability(result, sig, "management_display")

    result = SignalResult(
        signal_id=sig.get("id", "UNKNOWN"),
        signal_name=sig.get("name", ""),
        status=SignalStatus.INFO,
        value=coerce_value(data_value),
        evidence=f"Management display: {data_value}",
        source=data_key,
        factors=extract_factors(sig),
        section=sig.get("section", 0),
        needs_calibration=False,
    )
    result = _apply_classification_metadata(result, sig)
    return _apply_traceability(result, sig, "management_display")


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------


def evaluate_signal(
    sig: dict[str, Any],
    data: dict[str, Any],
    company: CompanyProfile | None = None,
) -> SignalResult:
    """Evaluate a single signal against its mapped data.

    Dispatches to the appropriate evaluator based on threshold.type.
    When company context is available, checks for sector-specific
    threshold overrides before applying generic thresholds.
    """
    raw_threshold = sig.get("threshold")
    threshold: dict[str, Any] = (
        cast(dict[str, Any], raw_threshold)
        if isinstance(raw_threshold, dict)
        else {}
    )

    # Apply sector-specific threshold overrides if available
    if company is not None:
        from do_uw.stages.analyze.threshold_resolver import resolve_sector_threshold
        sector_override = resolve_sector_threshold(sig, company)
        if sector_override is not None:
            threshold = sector_override

    ttype: str = str(threshold.get("type", "info"))

    if ttype in INFO_ONLY_TYPES:
        result = evaluate_info_only(sig, data)
    elif ttype == "tiered":
        result = evaluate_tiered(sig, data, threshold)
    elif ttype == "boolean":
        result = evaluate_boolean(sig, data, threshold)
    elif ttype in ("percentage", "count", "value"):
        result = evaluate_numeric_threshold(sig, data, threshold, ttype)
    elif ttype == "temporal":
        result = evaluate_temporal(sig, data, threshold)
    else:
        logger.warning(
            "Unknown threshold type '%s' for signal %s",
            ttype,
            str(sig.get("id")),
        )
        result = evaluate_info_only(sig, data)

    result = _apply_classification_metadata(result, sig)
    return _apply_traceability(result, sig, ttype)


# ---------------------------------------------------------------------------
# Backward-compatible re-export for test imports
# ---------------------------------------------------------------------------
# Tests import _make_skipped from signal_engine; re-export it so those
# imports continue to work. _signal_sector_applicable and
# _determine_data_status are still defined in this module.

_make_skipped = make_skipped

# Backward-compat alias for callers that may reference old name
_check_sector_applicability = _signal_sector_applicable

__all__ = [
    "CHUNK_SIZE",
    "evaluate_management_display",
    "evaluate_signal",
    "execute_signals",
]
