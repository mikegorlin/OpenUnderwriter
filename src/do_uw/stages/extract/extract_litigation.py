"""Litigation extraction sub-orchestrator (SECT6).

Calls all SECT6 extractors in dependency order, collects
ExtractionReports, and assembles a populated LitigationLandscape model.

SOL mapper runs late because it reads extracted litigation data from
state.  Contingent liabilities and workforce/product extractors return
3-tuples requiring special unpacking.

After all extractors complete, generates a rule-based litigation
summary synthesizing 5 key dimensions and builds a chronological
timeline of litigation events.

Summary narrative and timeline construction are in
litigation_narrative.py to stay under 500 lines.
"""

from __future__ import annotations

import logging
import re

from do_uw.models.common import SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import (
    ContingentLiability,
    DealLitigation,
    DefenseAssessment,
    IndustryClaimPattern,
    SOLWindow,
    WhistleblowerIndicator,
    WorkforceProductEnvironmental,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)


def run_litigation_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
    manifest: object | None = None,
) -> LitigationLandscape:
    """Run all SECT6 litigation extractors in dependency order.

    Each extractor is wrapped in try/except so a single failure
    does not abort the entire litigation extraction pass.  On failure
    the default (empty) sub-model is used and a warning is logged.

    After all extractors finish, a rule-based litigation_summary is
    generated synthesizing active matters, regulatory pipeline,
    defense posture, and emerging exposure.  Timeline events are
    built from case dates across all sub-areas.

    Args:
        state: Pipeline state with acquired data.
        reports: Mutable report list -- each extractor appends its report.

    Returns:
        Populated LitigationLandscape instance.
    """
    from do_uw.stages.extract.litigation_narrative import (
        build_timeline_events,
        count_active_matters,
        count_historical_matters,
        generate_litigation_summary,
    )

    landscape = LitigationLandscape()

    # Log brain requirements for this domain if manifest provided
    if manifest is not None:
        from do_uw.stages.extract.extraction_manifest import ExtractionManifest

        if isinstance(manifest, ExtractionManifest):
            reqs = manifest.get_requirements_for_source("SEC_10K")
            hunt_reqs = [
                r for r in manifest.requirements.values()
                if r.acquisition_type == "broad_search"
            ]
            if reqs or hunt_reqs:
                logger.info(
                    "SECT6: Brain needs %d fields from SEC_10K, "
                    "%d from broad search",
                    len(reqs), len(hunt_reqs),
                )

    # Pre-deserialize LLM results (once for all extractors)
    from do_uw.stages.extract.llm_helpers import get_llm_def14a, get_llm_ten_k

    llm_ten_k = get_llm_ten_k(state)
    llm_def14a = get_llm_def14a(state)

    # 1. Securities class actions (SECT6-03) -- foundational
    landscape.securities_class_actions = _run_sca_extractor(state, reports)

    # Supplement with LLM extraction of web search results
    web_llm_cases = _run_web_llm_extraction(state, landscape)
    if web_llm_cases:
        logger.info(
            "SECT6-03: Web LLM added %d SCA cases", len(web_llm_cases),
        )

    # Supplement with LLM Item 3 legal proceedings — route by case type
    if llm_ten_k and llm_ten_k.legal_proceedings:
        from do_uw.stages.extract.llm_litigation import (
            convert_legal_proceedings,
        )

        llm_cases = convert_legal_proceedings(llm_ten_k)
        existing_names = {
            c.case_name.value.lower()
            for c in landscape.securities_class_actions
            if c.case_name and c.case_name.value
        }
        sca_count = 0
        routed_count = 0
        for case in llm_cases:
            if not (case.case_name and case.case_name.value):
                continue
            if case.case_name.value.lower() in existing_names:
                continue
            existing_names.add(case.case_name.value.lower())

            # Route based on coverage_type and legal_theories
            destination = _classify_case_destination(case)
            if destination == "SCA":
                landscape.securities_class_actions.append(case)
                sca_count += 1
            else:
                routed_count += 1
                # Non-SCA cases: route to appropriate sub-model
                # Environmental/regulatory/employment/product cases
                # are informational but should NOT trigger SCA scoring
                logger.info(
                    "SECT6: Routed non-SCA case to %s: %s",
                    destination,
                    case.case_name.value[:80],
                )
        logger.info(
            "SECT6: LLM Item 3: %d -> SCA, %d -> non-SCA",
            sca_count, routed_count,
        )

    # 2. SEC enforcement pipeline (SECT6-04)
    landscape.sec_enforcement = _run_sec_enforcement(state, reports)

    # 3. Derivative suits (SECT6-05)
    landscape.derivative_suits = _run_derivative_suits(state, reports)

    # 4. Regulatory proceedings (SECT6-06)
    # Phase 3 field typed as list[SourcedValue[dict]], but Phase 5
    # extractor returns list[RegulatoryProceeding].  Runtime-safe via
    # Pydantic frozen=False; type: ignore for pyright strict.
    landscape.regulatory_proceedings = _run_regulatory_proceedings(
        state, reports
    )

    # 5. Deal litigation (SECT6-07)
    landscape.deal_litigation = _run_deal_litigation(state, reports)

    # 6. Workforce/product/environmental + whistleblower (SECT6-08)
    wpe, whistleblowers = _run_workforce_product(state, reports)
    landscape.workforce_product_environmental = wpe
    landscape.whistleblower_indicators = whistleblowers

    # 7. Defense assessment (SECT6-09)
    landscape.defense = _run_defense_assessment(state, reports)

    # Supplement defense with LLM forum provisions from DEF 14A
    if llm_def14a and (
        llm_def14a.exclusive_forum_provision is not None
        or llm_def14a.forum_selection_clause
    ):
        from do_uw.stages.extract.llm_litigation import (
            convert_forum_provisions,
        )

        llm_forum = convert_forum_provisions(llm_def14a)
        if not landscape.defense.forum_provisions.has_exclusive_forum:
            landscape.defense.forum_provisions = llm_forum
            logger.info("SECT6-09: Forum provisions from LLM DEF 14A")

    # 8. Industry claim patterns (SECT6-10) -- reads peer data
    landscape.industry_patterns = _run_industry_claims(state, reports)

    # 9. SOL map (SECT6-11) -- reads extracted litigation data
    _ensure_extracted_litigation(state, landscape)
    landscape.sol_map = _run_sol_mapper(state, reports)

    # 10. Contingent liabilities (SECT6-12)
    if llm_ten_k and llm_ten_k.contingent_liabilities:
        from do_uw.stages.extract.llm_litigation import (
            convert_contingencies,
        )

        landscape.contingent_liabilities = convert_contingencies(llm_ten_k)
        from do_uw.stages.extract.contingent_liab import (
            sum_litigation_reserves,
        )

        total = sum_litigation_reserves(landscape.contingent_liabilities)
        if total > 0:
            from do_uw.models.common import Confidence
            from do_uw.stages.extract.sourced import sourced_float

            landscape.total_litigation_reserve = sourced_float(
                total, "10-K (LLM)", Confidence.MEDIUM
            )
        logger.info("SECT6-12: Contingent liabilities from LLM extraction")
    else:
        liabilities, total_reserve = _run_contingent_liabilities(
            state, reports
        )
        landscape.contingent_liabilities = liabilities
        landscape.total_litigation_reserve = total_reserve

    # Store LLM risk factors on ExtractedData
    if llm_ten_k and llm_ten_k.risk_factors:
        from do_uw.stages.extract.llm_litigation import convert_risk_factors

        risk_factors = convert_risk_factors(llm_ten_k)
        from do_uw.models.state import ExtractedData

        if state.extracted is None:
            state.extracted = ExtractedData()
        state.extracted.risk_factors = risk_factors
        logger.info("SECT6: Stored %d LLM risk factors", len(risk_factors))

    # Cross-validate SCAs against web search results
    _cross_validate_scas(state, landscape)

    # --- Unified post-extraction classification (Phase 140) ---
    from do_uw.stages.extract.litigation_classifier import (
        classify_all_cases,
        deduplicate_all_cases,
        disambiguate_by_year,
        flag_missing_fields,
    )

    # Pass 1: Classify all cases by legal theory + filter boilerplate (D-01, D-07)
    classify_all_cases(landscape)

    # Pass 2: Deduplicate across all case lists (D-03) -- MUST run before year disambiguation
    deduplicate_all_cases(landscape)

    # Pass 3: Append year suffix to all case names (D-05)
    disambiguate_by_year(landscape)

    # Pass 4: Flag missing critical fields with data quality annotations (D-06)
    flag_missing_fields(landscape)

    logger.info(
        "SECT6: Unified classifier complete — %d SCAs, %d derivatives, "
        "%d unclassified reserves",
        len(landscape.securities_class_actions),
        len(landscape.derivative_suits),
        len(landscape.unclassified_reserves),
    )

    # SECT6-01: Generate litigation summary narrative (MUST be last)
    landscape.litigation_summary = generate_litigation_summary(landscape)

    # SECT6-02: Build timeline events
    landscape.litigation_timeline_events = build_timeline_events(landscape)

    # Compute matter counts
    landscape.active_matter_count = count_active_matters(landscape)
    landscape.historical_matter_count = count_historical_matters(landscape)

    return landscape


# ------------------------------------------------------------------
# Individual extractor wrappers
# ------------------------------------------------------------------


def _run_sca_extractor(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[CaseDetail]:
    """Extract securities class actions."""
    try:
        from do_uw.stages.extract.sca_extractor import (
            extract_securities_class_actions,
        )

        cases, report = extract_securities_class_actions(state)
        reports.append(report)
        logger.info("SECT6-03: Securities class actions extracted")
        return cases
    except Exception:
        logger.warning(
            "SECT6-03: SCA extraction failed", exc_info=True,
        )
        return []


def _run_web_llm_extraction(
    state: AnalysisState,
    landscape: LitigationLandscape,
) -> list[CaseDetail]:
    """Extract SCA cases from web search results using LLM.

    Deduplicates against existing landscape.securities_class_actions
    before appending new cases.
    """
    try:
        from do_uw.stages.extract.sca_web_llm import extract_web_scas

        web_cases = extract_web_scas(state)
        if not web_cases:
            return []

        # Deduplicate against existing SCAs
        existing_names = {
            c.case_name.value.lower()
            for c in landscape.securities_class_actions
            if c.case_name and c.case_name.value
        }
        added: list[CaseDetail] = []
        for case in web_cases:
            if not (case.case_name and case.case_name.value):
                continue
            name_lower = case.case_name.value.lower()
            if name_lower in existing_names:
                logger.debug(
                    "SECT6-03: Web LLM duplicate skipped: %s",
                    case.case_name.value[:80],
                )
                continue
            # Also check word overlap with existing cases
            from do_uw.stages.extract.sca_extractor import word_overlap_pct

            is_dup = False
            for existing_name in existing_names:
                if word_overlap_pct(name_lower, existing_name) > 0.60:
                    is_dup = True
                    break
            if is_dup:
                continue

            existing_names.add(name_lower)
            landscape.securities_class_actions.append(case)
            added.append(case)

        return added
    except Exception:
        logger.warning(
            "SECT6-03: Web LLM SCA extraction failed", exc_info=True,
        )
        return []


def _run_sec_enforcement(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> SECEnforcementPipeline:
    """Extract SEC enforcement pipeline position."""
    try:
        from do_uw.stages.extract.sec_enforcement import (
            extract_sec_enforcement,
        )

        pipeline, report = extract_sec_enforcement(state)
        reports.append(report)
        logger.info("SECT6-04: SEC enforcement pipeline extracted")
        return pipeline
    except Exception:
        logger.warning(
            "SECT6-04: SEC enforcement extraction failed", exc_info=True,
        )
        return SECEnforcementPipeline()


def _run_derivative_suits(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[CaseDetail]:
    """Extract shareholder derivative suits."""
    try:
        from do_uw.stages.extract.derivative_suits import (
            extract_derivative_suits,
        )

        cases, report = extract_derivative_suits(state)
        reports.append(report)
        logger.info("SECT6-05: Derivative suits extracted")
        return cases
    except Exception:
        logger.warning(
            "SECT6-05: Derivative suit extraction failed", exc_info=True,
        )
        return []


def _run_regulatory_proceedings(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[SourcedValue[dict[str, str]]]:
    """Extract non-SEC regulatory proceedings.

    Converts RegulatoryProceeding objects to SourcedValue[dict[str, str]]
    to match the LitigationLandscape model field type.
    """
    try:
        from do_uw.stages.extract.regulatory_extract import (
            extract_regulatory_proceedings,
        )
        from do_uw.stages.extract.sourced import sourced_str_dict

        proceedings, report = extract_regulatory_proceedings(state)
        reports.append(report)
        logger.info("SECT6-06: Regulatory proceedings extracted")

        # Convert to model-compatible format.
        result: list[SourcedValue[dict[str, str]]] = []
        for proc in proceedings:
            agency = proc.agency.value if proc.agency else "unknown"
            ptype = (
                proc.proceeding_type.value
                if proc.proceeding_type
                else "unknown"
            )
            desc = proc.description.value if proc.description else ""
            status = proc.status.value if proc.status else "disclosed"
            source = proc.agency.source if proc.agency else "unknown"
            result.append(
                sourced_str_dict(
                    {
                        "agency": agency,
                        "type": ptype,
                        "description": desc[:200],
                        "status": status,
                    },
                    source,
                )
            )
        return result
    except Exception:
        logger.warning(
            "SECT6-06: Regulatory extraction failed", exc_info=True,
        )
        return []


def _run_deal_litigation(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[DealLitigation]:
    """Extract M&A and deal-related litigation."""
    try:
        from do_uw.stages.extract.deal_litigation import (
            extract_deal_litigation,
        )

        deals, report = extract_deal_litigation(state)
        reports.append(report)
        logger.info("SECT6-07: Deal litigation extracted")
        return deals
    except Exception:
        logger.warning(
            "SECT6-07: Deal litigation extraction failed", exc_info=True,
        )
        return []


def _run_workforce_product(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> tuple[WorkforceProductEnvironmental, list[WhistleblowerIndicator]]:
    """Extract workforce/product/environmental matters + whistleblower.

    The underlying extractor returns a 3-tuple:
    (WPE, list[WhistleblowerIndicator], ExtractionReport).
    This wrapper unpacks all 3, appends the report to reports,
    and returns only (WPE, whistleblowers) as a 2-tuple.
    """
    try:
        from do_uw.stages.extract.workforce_product import (
            extract_workforce_product_environmental,
        )

        wpe, whistleblowers, report = (
            extract_workforce_product_environmental(state)
        )
        reports.append(report)
        logger.info("SECT6-08: Workforce/product/environmental extracted")
        return wpe, whistleblowers
    except Exception:
        logger.warning(
            "SECT6-08: Workforce/product extraction failed", exc_info=True,
        )
        return WorkforceProductEnvironmental(), []


def _run_defense_assessment(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> DefenseAssessment:
    """Extract defense quality assessment."""
    try:
        from do_uw.stages.analyze.defense_assessment import (
            extract_defense_assessment,
        )

        assessment, report = extract_defense_assessment(state)
        reports.append(report)
        logger.info("SECT6-09: Defense assessment extracted")
        return assessment
    except Exception:
        logger.warning(
            "SECT6-09: Defense assessment extraction failed", exc_info=True,
        )
        return DefenseAssessment()


def _run_industry_claims(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[IndustryClaimPattern]:
    """Extract industry-specific claim patterns."""
    try:
        from do_uw.stages.analyze.industry_claims import (
            extract_industry_claim_patterns,
        )

        patterns, report = extract_industry_claim_patterns(state)
        reports.append(report)
        logger.info("SECT6-10: Industry claim patterns extracted")
        return patterns
    except Exception:
        logger.warning(
            "SECT6-10: Industry claims extraction failed", exc_info=True,
        )
        return []


def _run_sol_mapper(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> list[SOLWindow]:
    """Compute statute of limitations windows."""
    try:
        from do_uw.stages.extract.sol_mapper import compute_sol_map

        windows, report = compute_sol_map(state)
        reports.append(report)
        logger.info("SECT6-11: SOL windows computed")
        return windows
    except Exception:
        logger.warning(
            "SECT6-11: SOL map computation failed", exc_info=True,
        )
        return []


def _run_contingent_liabilities(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> tuple[list[ContingentLiability], SourcedValue[float] | None]:
    """Extract contingent liabilities and total reserve.

    The underlying extractor returns a 3-tuple:
    (liabilities, total_reserve, ExtractionReport).
    This wrapper unpacks all 3, appends the report to reports,
    and returns only (liabilities, total_reserve) as a 2-tuple.
    """
    try:
        from do_uw.stages.extract.contingent_liab import (
            extract_contingent_liabilities,
        )

        liabilities, total_reserve, report = (
            extract_contingent_liabilities(state)
        )
        reports.append(report)
        logger.info("SECT6-12: Contingent liabilities extracted")
        return liabilities, total_reserve
    except Exception:
        logger.warning(
            "SECT6-12: Contingent liabilities extraction failed",
            exc_info=True,
        )
        return [], None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _cross_validate_scas(
    state: AnalysisState, landscape: LitigationLandscape
) -> None:
    """Cross-validate extracted SCAs against web search results.

    If web search data exists, check whether each extracted SCA has
    corroboration from web sources. SCAs that exist only in 10-K Item 3
    extraction without any web search corroboration get downgraded to
    LOW confidence. Cases that are clearly not securities-related
    (environmental, product, employment) get removed.

    Also checks web search results for SCAs NOT found in extraction
    (the web search may find cases the 10-K didn't mention).
    """
    if not landscape.securities_class_actions:
        return

    # Get web search litigation results
    acquired = state.acquired_data
    if acquired is None:
        return

    lit_data = getattr(acquired, "litigation_data", None)
    if not isinstance(lit_data, dict):
        return

    web_results = lit_data.get("web_results", [])
    blind_spot = getattr(acquired, "blind_spot_results", None)

    # Gather all web text for corroboration check
    web_texts: list[str] = []
    if isinstance(web_results, list):
        for r in web_results:
            if isinstance(r, dict):
                web_texts.append(str(r.get("title", "")).upper())
                web_texts.append(str(r.get("snippet", "")).upper())
                web_texts.append(str(r.get("description", "")).upper())
    if isinstance(blind_spot, dict):
        for category_results in blind_spot.values():
            if isinstance(category_results, dict):
                for results in category_results.values():
                    if isinstance(results, list):
                        for r in results:
                            if isinstance(r, dict):
                                web_texts.append(str(r.get("title", "")).upper())
                                web_texts.append(str(r.get("snippet", "")).upper())

    web_corpus = " ".join(web_texts)

    # SCA-specific keywords that should appear in web results
    sca_keywords = {
        "SECURITIES CLASS ACTION", "SECURITIES FRAUD",
        "CLASS ACTION COMPLAINT", "SHAREHOLDER LAWSUIT",
        "10B-5", "SECTION 11", "SECURITIES LITIGATION",
    }

    # Check if ANY web result mentions an actual SCA for this company
    has_web_sca_evidence = any(kw in web_corpus for kw in sca_keywords)

    # Build company identity tokens for false-positive detection
    company_name = (
        getattr(state.company, "legal_name", None)
        or getattr(
            getattr(getattr(state.company, "identity", None), "legal_name", None),
            "value", None,
        )
        or state.ticker
        or ""
    )
    ticker = (state.ticker or "").upper()
    # Tokens: company name words + ticker, lowercased for matching
    _company_tokens = {
        w.upper() for w in company_name.split() if len(w) > 2
    }
    if ticker:
        _company_tokens.add(ticker)
    # Remove generic legal suffixes that don't help identification
    _company_tokens -= {"INC", "INC.", "CORP", "CORP.", "LLC", "LTD", "LTD.",
                        "CO.", "THE", "GROUP", "HOLDINGS", "COMPANY", "PLC"}

    # Known other-company names that should NOT match our company.
    # If a case name contains "In re <OtherCompany>" with NO reference to
    # our company, it's a false positive from web search / LLM extraction.

    # Validate each extracted SCA
    validated: list[CaseDetail] = []
    for sca in landscape.securities_class_actions:
        name = ""
        if sca.case_name is not None:
            name = (
                sca.case_name.value
                if hasattr(sca.case_name, "value")
                else str(sca.case_name)
            )

        # --- Company-name false positive check ---
        # If case name references a DIFFERENT company and does NOT
        # reference our company, exclude it. But be careful: some legitimate
        # cases don't have the company name (e.g., "Smith v. Jones" where
        # Jones is an officer). Only filter when the case name clearly
        # names another company via "In re <OtherCompany>" or
        # "<Party> v. <OtherCompany>" patterns AND our company is absent.
        source = ""
        if sca.case_name is not None and hasattr(sca.case_name, "source"):
            source = sca.case_name.source or ""
        from_scac = "SCAC" in source.upper() or "EFTS" in source.upper()

        if not from_scac and name and _company_tokens:
            name_upper = name.upper()
            # Check if ANY of our company tokens appear in the case name
            has_company_ref = any(t in name_upper for t in _company_tokens)
            if not has_company_ref:
                # Case name doesn't mention our company at all.
                # If it names another company via "In re X" or "v. X"
                # patterns, this is likely a false positive.
                # "In re" cases almost always name the defendant company
                in_re_match = re.search(r"In re\b", name, re.IGNORECASE)
                v_match = re.search(r"\bv\.?\s+", name)
                if in_re_match or v_match:
                    # Confidence check: only exclude LOW confidence cases.
                    # HIGH/MEDIUM confidence (from SCAC/EFTS/10-K) are
                    # more likely legitimate even without company name.
                    confidence = ""
                    if sca.case_name is not None and hasattr(sca.case_name, "confidence"):
                        conf_obj = sca.case_name.confidence
                        confidence = (
                            conf_obj.value if hasattr(conf_obj, "value")
                            else str(conf_obj)
                        ).upper()
                    if confidence == "LOW":
                        logger.warning(
                            "SECT6-VALIDATE: Excluding likely false-positive SCA "
                            "(case names different company, LOW confidence): %s",
                            name[:100],
                        )
                        continue

        # Check if case name appears in web results (corroboration)
        name_parts = [p for p in name.upper().split() if len(p) > 3]
        name_in_web = sum(1 for p in name_parts if p in web_corpus)
        corroborated = name_in_web >= 2  # At least 2 significant words match

        if from_scac:
            # SCAC/EFTS cases are trusted — always keep
            validated.append(sca)
        elif corroborated:
            # Web-corroborated — keep
            validated.append(sca)
            logger.info(
                "SECT6-VALIDATE: SCA corroborated by web search: %s",
                name[:80],
            )
        elif has_web_sca_evidence:
            # Web mentions SCAs for this company but not this specific case
            # Downgrade confidence but keep
            if sca.case_name is not None and hasattr(sca.case_name, "confidence"):
                from do_uw.models.common import Confidence
                sca.case_name = SourcedValue(
                    value=sca.case_name.value,
                    source=sca.case_name.source + " (unvalidated)",
                    confidence=Confidence.LOW,
                    as_of=sca.case_name.as_of,
                )
            validated.append(sca)
            logger.warning(
                "SECT6-VALIDATE: SCA not individually corroborated, "
                "downgraded to LOW: %s",
                name[:80],
            )
        else:
            # No web evidence of ANY SCA for this company — high suspicion
            # Still keep but mark as LOW and log prominently
            if sca.case_name is not None and hasattr(sca.case_name, "confidence"):
                from do_uw.models.common import Confidence
                sca.case_name = SourcedValue(
                    value=sca.case_name.value,
                    source=sca.case_name.source + " (NO web corroboration)",
                    confidence=Confidence.LOW,
                    as_of=sca.case_name.as_of,
                )
            validated.append(sca)
            logger.warning(
                "SECT6-VALIDATE: SCA has NO web corroboration — "
                "may be misclassified: %s",
                name[:80],
            )

    removed = len(landscape.securities_class_actions) - len(validated)
    if removed > 0:
        logger.info("SECT6-VALIDATE: Removed %d invalid SCAs", removed)
    landscape.securities_class_actions = validated


def _classify_case_destination(case: CaseDetail) -> str:
    """Determine where an Item 3 case should be routed.

    Returns 'SCA' only if the case has securities-related indicators.
    Otherwise returns the appropriate category name.

    A real SCA requires securities legal theories (10b-5, Section 11,
    Section 14a) or explicit securities/class-action keywords in the
    case name or allegations.  Environmental, employment, product
    liability, antitrust, and regulatory cases are NOT SCAs.
    """
    # Coverage types that definitively indicate SCA
    _SCA_COVERAGE_TYPES = {"SCA_SIDE_C", "DERIVATIVE_SIDE_A"}
    # Securities legal theories
    _SECURITIES_THEORIES = {
        "RULE_10B5", "SECTION_11", "SECTION_14A",
        "SECURITIES_FRAUD",
    }
    # Non-securities theories — cases with ONLY these are never SCAs
    _NON_SCA_THEORIES = {
        "ENVIRONMENTAL", "PRODUCT_LIABILITY", "EMPLOYMENT_DISCRIMINATION",
        "ANTITRUST", "FCPA", "CYBER_PRIVACY", "WHISTLEBLOWER", "ERISA",
    }
    # Keywords in case name/allegations that indicate securities litigation
    _SECURITIES_KEYWORDS = (
        "SECURITIES", "CLASS ACTION", "SHAREHOLDER CLASS",
        "10B-5", "10(B)", "SECTION 11", "SECTION 14",
        "SECURITIES FRAUD", "STOCK FRAUD",
        "IN RE ", "SEC. LIT.", "SECURITIES LITIGATION",
    )

    # 1. Check coverage_type
    ct_val = ""
    if case.coverage_type is not None:
        ct_val = (
            case.coverage_type.value.upper()
            if hasattr(case.coverage_type, "value")
            else str(case.coverage_type).upper()
        )
    if ct_val in _SCA_COVERAGE_TYPES:
        return "SCA"

    # 2. Check legal theories
    theory_values: set[str] = set()
    for t in (case.legal_theories or []):
        val = t.value.upper() if hasattr(t, "value") else str(t).upper()
        theory_values.add(val)

    if theory_values & _SECURITIES_THEORIES:
        return "SCA"
    if theory_values and theory_values <= _NON_SCA_THEORIES:
        # All theories are non-securities — route to appropriate bucket
        if "ENVIRONMENTAL" in theory_values:
            return "ENVIRONMENTAL"
        if "PRODUCT_LIABILITY" in theory_values:
            return "PRODUCT_LIABILITY"
        if "EMPLOYMENT_DISCRIMINATION" in theory_values:
            return "EMPLOYMENT"
        if "ANTITRUST" in theory_values:
            return "ANTITRUST"
        return "REGULATORY"

    # 3. Check case name and allegations for securities keywords
    name_upper = ""
    if case.case_name is not None:
        name_upper = (
            case.case_name.value.upper()
            if hasattr(case.case_name, "value")
            else str(case.case_name).upper()
        )
    if any(kw in name_upper for kw in _SECURITIES_KEYWORDS):
        return "SCA"

    for alg in (case.allegations or []):
        val = alg.value.upper() if hasattr(alg, "value") else str(alg).upper()
        if any(kw in val for kw in _SECURITIES_KEYWORDS):
            return "SCA"

    # 4. No securities indicators — default to GENERAL (not SCA)
    return "GENERAL"


def _ensure_extracted_litigation(
    state: AnalysisState, landscape: LitigationLandscape
) -> None:
    """Write intermediate litigation to state for SOL mapper."""
    from do_uw.models.state import ExtractedData

    if state.extracted is None:
        state.extracted = ExtractedData()
    state.extracted.litigation = landscape
