"""Company profile extraction -- SECT2-01 through SECT2-11.

Main orchestrator plus identity enrichment.
Item-level parsing helpers (_resolve_gics_code, _resolve_naics_code,
_validate_employee_count, _extract_business_description) are in
company_profile_items.py (split for 500-line compliance).
Revenue segments, operational complexity, and business changes are
in profile_item1_helpers.py.
See also: profile_helpers.py and sourced.py.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.company_profile_items import (
    _extract_business_description,
    _resolve_gics_code,
    _resolve_naics_code,
    _validate_employee_count,
)
from do_uw.stages.extract.profile_helpers import (
    build_event_timeline,
    extract_concentration,
    extract_geographic_footprint,
    generate_section_summary,
    map_do_exposure,
)
from do_uw.stages.extract.profile_item1_helpers import (
    extract_business_changes,
    extract_operational_complexity,
    extract_revenue_segments,
)
from do_uw.stages.extract.sourced import (
    get_company_facts,
    get_info_dict,
    sourced_float,
    sourced_int,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    merge_reports,
)

logger = logging.getLogger(__name__)


def extract_company_profile(
    state: AnalysisState,
) -> tuple[CompanyProfile, ExtractionReport]:
    """Extract complete company profile (SECT2-01 through SECT2-11)."""
    if state.company is None:
        msg = "CompanyProfile must be populated by RESOLVE stage first"
        raise ValueError(msg)

    profile = state.company
    reports: list[ExtractionReport] = []

    reports.extend(_enrich_identity(state, profile))

    desc, desc_report = _extract_business_description(state)
    if desc is not None:
        profile.business_description = desc
    reports.append(desc_report)

    facts = get_company_facts(state)
    facts_inner = facts.get("facts") if facts else None

    typed_facts: dict[str, Any] | None = (
        cast(dict[str, Any], facts_inner) if isinstance(facts_inner, dict) else None
    )
    segments, seg_report = extract_revenue_segments(state, typed_facts)
    profile.revenue_segments = segments
    reports.append(seg_report)

    geo, geo_report = extract_geographic_footprint(state)
    profile.geographic_footprint = geo
    reports.append(geo_report)

    customers, suppliers, conc_report = extract_concentration(state)
    profile.customer_concentration = customers
    profile.supplier_concentration = suppliers
    reports.append(conc_report)

    complexity, comp_report = extract_operational_complexity(state)
    profile.operational_complexity = complexity
    reports.append(comp_report)

    # --- Operational data (OPS-02, OPS-03, OPS-04) ---
    from do_uw.stages.extract.operational_extraction import (
        extract_operational_resilience,
        extract_subsidiary_structure,
        extract_workforce_distribution,
    )

    sub_struct, sub_report = extract_subsidiary_structure(state)
    profile.subsidiary_structure = sub_struct
    reports.append(sub_report)

    workforce, wf_report = extract_workforce_distribution(state)
    profile.workforce_distribution = workforce
    reports.append(wf_report)

    resilience, res_report = extract_operational_resilience(state)
    profile.operational_resilience = resilience
    reports.append(res_report)

    changes, changes_report = extract_business_changes(state)
    profile.business_changes = changes
    reports.append(changes_report)

    # --- LLM Item 1 enrichment ---
    _enrich_from_llm(state, profile)

    # --- External environment assessment (Phase 97 ENVR signals) ---
    if state.extracted is not None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        try:
            env_signals = extract_environment_signals(state)
            state.extracted.text_signals["environment_assessment"] = env_signals
        except Exception:
            logger.warning("Environment signal extraction failed", exc_info=True)

    # --- Sector risk classification (Phase 98 SECT signals) ---
    if state.extracted is not None:
        from do_uw.stages.extract.sector_classification import extract_sector_signals

        try:
            sect_signals = extract_sector_signals(state)
            state.extracted.text_signals["sector_classification"] = sect_signals
        except Exception:
            logger.warning("Sector signal extraction failed", exc_info=True)

    profile.do_exposure_factors = map_do_exposure(profile)
    profile.event_timeline = build_event_timeline(state)
    profile.section_summary = generate_section_summary(profile)

    merged = merge_reports(reports)
    logger.info(
        "Company profile extraction: %.1f%% coverage (%s confidence)",
        merged.coverage_pct, merged.confidence.value,
    )
    return profile, merged


# ------------------------------------------------------------------
# LLM enrichment
# ------------------------------------------------------------------


def _enrich_from_llm(
    state: AnalysisState, profile: CompanyProfile,
) -> None:
    """Enrich company profile with LLM-extracted Item 1 data.

    Strategy:
    - Business description: LLM replaces if richer (longer)
    - Geographic footprint: LLM fills only when regex found nothing
    - Concentration: LLM supplements (regex rarely finds these)
    - Operational complexity: LLM flags supplement existing
    - Employee count: LLM fills when yfinance is absent
    """
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k

    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is None:
        return

    from do_uw.stages.extract.ten_k_converters import (
        convert_acquisitions,
        convert_acquisitions_total_spend,
        convert_business_description,
        convert_customer_concentration,
        convert_disruption_risk,
        convert_employee_count,
        convert_geographic_footprint,
        convert_goodwill_balance,
        convert_goodwill_change_description,
        convert_key_person_risk,
        convert_operational_complexity_flags,
        convert_revenue_model_type,
        convert_segment_lifecycle,
        convert_segment_margins,
        convert_supplier_concentration,
    )

    # Business description: LLM always replaces — it produces a proper
    # narrative about what the company does, revenue model, and earnings
    # drivers. Initial extraction is either yfinance summary or raw 10-K text.
    llm_desc = convert_business_description(llm_ten_k)
    if llm_desc is not None:
        profile.business_description = llm_desc

    # Geographic footprint: LLM 10-K revenue data ALWAYS preferred over
    # Exhibit 21 subsidiary counts. 10-K gives country/region-level revenue
    # breakdowns which are far more useful for underwriting than sub counts.
    llm_geo = convert_geographic_footprint(llm_ten_k)
    if llm_geo:
        # Widen dict[str, str] to dict[str, str | float] for model
        profile.geographic_footprint = [
            SourcedValue[dict[str, str | float]](
                value=cast(dict[str, str | float], sv.value),
                source=sv.source,
                confidence=sv.confidence,
                as_of=sv.as_of,
            )
            for sv in llm_geo
        ]

    # Customer concentration: LLM supplements (regex rarely finds these)
    llm_cust = convert_customer_concentration(llm_ten_k)
    if llm_cust and not profile.customer_concentration:
        profile.customer_concentration = [
            SourcedValue[dict[str, str | float]](
                value={"customer": sv.value, "revenue_pct": 0.0},
                source=sv.source,
                confidence=sv.confidence,
                as_of=sv.as_of,
            )
            for sv in llm_cust
        ]

    # Supplier concentration: LLM supplements (regex rarely finds these)
    llm_supp = convert_supplier_concentration(llm_ten_k)
    if llm_supp and not profile.supplier_concentration:
        profile.supplier_concentration = [
            SourcedValue[dict[str, str | float]](
                value={"supplier": sv.value, "cost_pct": 0.0},
                source=sv.source,
                confidence=sv.confidence,
                as_of=sv.as_of,
            )
            for sv in llm_supp
        ]

    # Operational complexity: LLM flags supplement existing
    llm_flags = convert_operational_complexity_flags(llm_ten_k)
    if profile.operational_complexity is not None and llm_flags:
        existing = profile.operational_complexity.value
        for key, sourced_val in llm_flags.items():
            if sourced_val.value and not existing.get(key):
                existing[key] = sourced_val.value

    # Employee count: LLM fills when yfinance is absent, with validation.
    # If the most recent 10-K didn't extract it, fall back to older filings.
    llm_emp = convert_employee_count(llm_ten_k)
    if llm_emp is None and profile.employee_count is None:
        llm_emp = _fallback_employee_count(state)
    if llm_emp is not None:
        yf_count = (
            profile.employee_count.value
            if profile.employee_count is not None
            else None
        )
        revenue = (
            profile.market_cap.value if profile.market_cap is not None else None
        )
        validated = _validate_employee_count(
            llm_count=llm_emp.value,
            revenue=revenue,
            yfinance_count=yf_count,
        )
        if validated != llm_emp.value:
            # Correction applied -- use validated value with MEDIUM confidence
            if yf_count is not None and validated == yf_count:
                # Keep existing yfinance-sourced value (already set)
                pass
            else:
                profile.employee_count = sourced_int(
                    validated, "10-K (LLM, corrected)", Confidence.MEDIUM,
                )
        elif profile.employee_count is None:
            profile.employee_count = llm_emp

    # Operational data LLM enrichment (OPS-03, OPS-04)
    from do_uw.stages.extract.ten_k_converters import (
        convert_operational_resilience,
        convert_workforce_distribution,
    )

    llm_wf = convert_workforce_distribution(llm_ten_k)
    if llm_wf is not None and profile.workforce_distribution is None:
        profile.workforce_distribution = llm_wf

    llm_res = convert_operational_resilience(llm_ten_k)
    if llm_res is not None and profile.operational_resilience is None:
        profile.operational_resilience = llm_res

    # Business model dimensions (v6.0 BMOD)
    llm_rev_model = convert_revenue_model_type(llm_ten_k)
    if llm_rev_model is not None:
        profile.revenue_model_type = llm_rev_model

    llm_key_person = convert_key_person_risk(llm_ten_k)
    if llm_key_person is not None:
        profile.key_person_risk = llm_key_person

    llm_lifecycle = convert_segment_lifecycle(llm_ten_k)
    if llm_lifecycle:
        profile.segment_lifecycle = llm_lifecycle

    llm_disruption = convert_disruption_risk(llm_ten_k)
    if llm_disruption is not None:
        profile.disruption_risk = llm_disruption

    llm_seg_margins = convert_segment_margins(llm_ten_k)
    if llm_seg_margins:
        profile.segment_margins = llm_seg_margins

    # M&A profile (from 10-K business combination footnotes)
    llm_gw = convert_goodwill_balance(llm_ten_k)
    if llm_gw is not None:
        profile.goodwill_balance = llm_gw

    llm_acq_spend = convert_acquisitions_total_spend(llm_ten_k)
    if llm_acq_spend is not None:
        profile.acquisitions_total_spend = llm_acq_spend

    llm_acqs = convert_acquisitions(llm_ten_k)
    if llm_acqs:
        profile.acquisitions = llm_acqs

    llm_gw_change = convert_goodwill_change_description(llm_ten_k)
    if llm_gw_change is not None:
        profile.goodwill_change_description = llm_gw_change

    logger.info("SECT2: Enriched company profile with LLM Item 1 data")


# ------------------------------------------------------------------
# Employee count fallback
# ------------------------------------------------------------------


def _fallback_employee_count(
    state: AnalysisState,
) -> SourcedValue[int] | None:
    """Search older 10-K LLM extractions for employee count.

    The most recent 10-K may omit employee_count (LLM extraction
    gap). Fall back to the next available filing that has it.
    """
    if state.acquired_data is None:
        return None
    from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
    from do_uw.stages.extract.ten_k_converters import convert_employee_count

    for key, data in state.acquired_data.llm_extractions.items():
        if not key.startswith("10-K:") or not isinstance(data, dict):
            continue
        try:
            extraction = TenKExtraction.model_validate(data)
        except Exception:
            continue
        emp = convert_employee_count(extraction)
        if emp is not None:
            emp.source = f"{emp.source} (prior filing)"
            emp.confidence = Confidence.MEDIUM
            logger.info(
                "Employee count fallback: %d from %s",
                emp.value, key,
            )
            return emp
    return None


# ------------------------------------------------------------------
# Identity enrichment
# ------------------------------------------------------------------


def _enrich_identity(
    state: AnalysisState, profile: CompanyProfile
) -> list[ExtractionReport]:
    """Enrich identity fields from Company Facts and yfinance."""
    info = get_info_dict(state)
    expected = [
        "exchange", "industry_classification", "employee_count",
        "market_cap", "filer_category", "gics_code", "naics_code",
    ]
    found: list[str] = []
    src = "yfinance"

    exchange_raw = str(info.get("exchange", ""))
    if profile.identity.exchange is None and exchange_raw:
        profile.identity.exchange = sourced_str(
            exchange_raw, src, Confidence.MEDIUM
        )
        found.append("exchange")
    elif profile.identity.exchange is not None:
        found.append("exchange")

    industry_raw = str(info.get("industry", ""))
    if industry_raw:
        profile.industry_classification = sourced_str(
            industry_raw, src, Confidence.MEDIUM
        )
        found.append("industry_classification")

    emp_raw = info.get("fullTimeEmployees")
    if emp_raw is not None and isinstance(emp_raw, (int, float)) and int(emp_raw) > 0:
        profile.employee_count = sourced_int(
            int(emp_raw), src, Confidence.MEDIUM
        )
        found.append("employee_count")

    mcap_raw = info.get("marketCap")
    if mcap_raw is not None and isinstance(mcap_raw, (int, float)) and float(mcap_raw) > 0:
        profile.market_cap = sourced_float(
            float(mcap_raw), src, Confidence.MEDIUM
        )
        found.append("market_cap")

    # Years public from first trade date
    ftd_ms = info.get("firstTradeDateMilliseconds")
    if ftd_ms is not None and isinstance(ftd_ms, (int, float)) and ftd_ms > 0:
        from datetime import UTC, datetime

        ipo_date = datetime.fromtimestamp(ftd_ms / 1000, tz=UTC)
        years = (datetime.now(tz=UTC) - ipo_date).days / 365.25
        if years > 0:
            profile.years_public = sourced_int(
                int(years), src, Confidence.MEDIUM
            )
            found.append("years_public")

    found = _enrich_filer_category(state, profile, found)

    # GICS code (DN-035 easy-win): SIC -> GICS mapping fallback.
    if profile.gics_code is None:
        gics = _resolve_gics_code(profile, info)
        if gics is not None:
            profile.gics_code = gics
            found.append("gics_code")
    else:
        found.append("gics_code")

    # NAICS code: SIC -> NAICS crosswalk.
    if profile.identity.naics_code is None:
        naics = _resolve_naics_code(profile)
        if naics is not None:
            profile.identity.naics_code = naics
            found.append("naics_code")
    else:
        found.append("naics_code")

    return [create_report(
        extractor_name="identity_enrichment", expected=expected,
        found=found, source_filing="yfinance + SEC Company Facts",
    )]


def _enrich_filer_category(
    state: AnalysisState, profile: CompanyProfile, found: list[str],
) -> list[str]:
    """Extract filer category from DEI, fallback to market cap inference."""
    if _filer_category_from_dei(state, profile):
        found.append("filer_category")
        return found

    # Fallback: infer from market cap.
    if profile.market_cap is not None:
        mcap = profile.market_cap.value
        if mcap >= 700_000_000:
            cat = "Large Accelerated Filer"
        elif mcap >= 75_000_000:
            cat = "Accelerated Filer"
        else:
            cat = "Non-Accelerated Filer"
        profile.filer_category = sourced_str(
            cat, "derived:market_cap_threshold", Confidence.LOW
        )
        found.append("filer_category")
    return found


def _filer_category_from_dei(
    state: AnalysisState, profile: CompanyProfile,
) -> bool:
    """Try to extract filer category from SEC Company Facts DEI."""
    facts = get_company_facts(state)
    facts_inner = facts.get("facts")
    if not isinstance(facts_inner, dict):
        return False
    dei = cast(dict[str, Any], facts_inner).get("dei")
    if not isinstance(dei, dict):
        return False
    filer_cat = cast(dict[str, Any], dei).get("EntityFilerCategory")
    if not isinstance(filer_cat, dict):
        return False
    units_data = cast(dict[str, Any], filer_cat).get("units")
    if not isinstance(units_data, dict):
        return False

    filer_entries: list[dict[str, Any]] = []
    for unit_key in cast(dict[str, Any], units_data):
        candidate = cast(dict[str, Any], units_data)[unit_key]
        if isinstance(candidate, list):
            typed = cast(list[dict[str, Any]], candidate)
            if len(typed) > 0:
                filer_entries = typed
                break

    if filer_entries:
        latest = max(filer_entries, key=lambda e: str(e.get("end", "")))
        val = str(latest.get("val", ""))
        if val:
            profile.filer_category = sourced_str(
                val, "SEC EDGAR Company Facts DEI", Confidence.HIGH
            )
            return True
    return False


