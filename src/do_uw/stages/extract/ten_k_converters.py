"""10-K converter: TenKExtraction -> domain model SourcedValues.

Maps flat LLM-extracted 10-K filing fields into typed SourcedValue
wrappers consumed by the scoring engine and worksheet renderer.
Every field gets HIGH confidence and '10-K (LLM)' source attribution.

Grouped by 10-K Item:
- Item 1: Business description, segments, geography, concentration, complexity
- Item 1 BMOD: Revenue model type, key person risk, lifecycle, disruption, margins
- Item 7: MD&A qualitative trends, estimates, non-GAAP measures
- Item 8: Debt enrichment, stock comp (qualitative context, never overrides XBRL)
- Item 9A: Controls assessment, material weaknesses, auditor attestation

Public functions:
- convert_business_description
- convert_revenue_segments
- convert_geographic_footprint
- convert_customer_concentration
- convert_supplier_concentration
- convert_operational_complexity_flags
- convert_employee_count
- convert_competitive_position
- convert_regulatory_environment
- convert_revenue_model_type
- convert_key_person_risk
- convert_segment_lifecycle
- convert_disruption_risk
- convert_segment_margins
- convert_mda_qualitative
- convert_debt_enrichment
- convert_stock_comp_detail
- convert_controls_assessment
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
    sourced_int,
    sourced_str,
    sourced_str_dict,
)

_LLM_SOURCE = "10-K (LLM)"


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _sourced_bool(value: bool) -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with LLM source and HIGH confidence."""
    return SourcedValue[bool](
        value=value,
        source=_LLM_SOURCE,
        confidence=Confidence.HIGH,
        as_of=now(),
    )


def _parse_colon_pair(text: str, key_name: str, val_name: str) -> dict[str, str]:
    """Parse 'Name: Value' into {key_name: name, val_name: value}.

    If no colon found, the entire text is used as the key_name value
    with an empty string for val_name.
    """
    if ":" in text:
        left, right = text.split(":", 1)
        return {key_name: left.strip(), val_name: right.strip()}
    return {key_name: text.strip(), val_name: ""}


# ------------------------------------------------------------------
# Item 1: Business
# ------------------------------------------------------------------


def convert_business_description(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert business description to SourcedValue[str].

    Returns None if the field is None or empty.
    """
    if not extraction.business_description:
        return None
    return sourced_str(extraction.business_description, _LLM_SOURCE, Confidence.HIGH)


def convert_revenue_segments(
    extraction: TenKExtraction,
) -> list[SourcedValue[dict[str, str]]]:
    """Convert revenue segment strings to list of SourcedValue dicts.

    Parses format 'Cloud Services: 60%' into
    {'segment': 'Cloud Services', 'percentage': '60%'}.
    Returns empty list if no segments.
    """
    results: list[SourcedValue[dict[str, str]]] = []
    for seg in extraction.revenue_segments:
        parsed = _parse_colon_pair(seg, "segment", "percentage")
        results.append(
            sourced_str_dict(parsed, _LLM_SOURCE, Confidence.HIGH)
        )
    return results


def convert_geographic_footprint(
    extraction: TenKExtraction,
) -> list[SourcedValue[dict[str, str]]]:
    """Convert geographic region strings to list of SourcedValue dicts.

    Parses format 'United States: 55%' into
    {'region': 'United States', 'percentage': '55%'}.
    Returns empty list if no regions.
    """
    results: list[SourcedValue[dict[str, str]]] = []
    for region in extraction.geographic_regions:
        parsed = _parse_colon_pair(region, "region", "percentage")
        results.append(
            sourced_str_dict(parsed, _LLM_SOURCE, Confidence.HIGH)
        )
    return results


def convert_customer_concentration(
    extraction: TenKExtraction,
) -> list[SourcedValue[str]]:
    """Wrap each customer concentration string in a SourcedValue.

    Returns empty list if no concentration disclosures.
    """
    return [
        sourced_str(c, _LLM_SOURCE, Confidence.HIGH)
        for c in extraction.customer_concentration
    ]


def convert_supplier_concentration(
    extraction: TenKExtraction,
) -> list[SourcedValue[str]]:
    """Wrap each supplier concentration string in a SourcedValue.

    Returns empty list if no supplier disclosures.
    """
    return [
        sourced_str(s, _LLM_SOURCE, Confidence.HIGH)
        for s in extraction.supplier_concentration
    ]


def convert_operational_complexity_flags(
    extraction: TenKExtraction,
) -> dict[str, SourcedValue[bool]]:
    """Convert dual-class and VIE flags to SourcedValue bools.

    Returns empty dict if both flags are None. Only includes
    flags that have a definitive extraction value.
    """
    flags: dict[str, SourcedValue[bool]] = {}
    if extraction.is_dual_class is not None:
        flags["has_dual_class"] = _sourced_bool(extraction.is_dual_class)
    if extraction.has_vie is not None:
        flags["has_vie"] = _sourced_bool(extraction.has_vie)
    return flags


def convert_employee_count(
    extraction: TenKExtraction,
) -> SourcedValue[int] | None:
    """Convert employee count to SourcedValue[int].

    Returns None if the field is None.
    """
    if extraction.employee_count is None:
        return None
    return sourced_int(extraction.employee_count, _LLM_SOURCE, Confidence.HIGH)


def convert_workforce_distribution(
    extraction: TenKExtraction,
) -> SourcedValue[dict[str, Any]] | None:
    """Convert workforce fields into a composite distribution dict.

    Combines domestic/international/union employee data into a single
    SourcedValue[dict]. Returns None if no workforce data was extracted.
    """
    # Need at least one data point
    has_data = any(
        getattr(extraction, f) is not None
        for f in (
            "domestic_employee_count",
            "international_employee_count",
            "unionized_employee_count",
            "unionized_employee_pct",
        )
    )
    if not has_data and extraction.employee_count is None:
        return None

    total = extraction.employee_count
    domestic = extraction.domestic_employee_count
    international = extraction.international_employee_count

    domestic_pct: float | None = None
    international_pct: float | None = None
    if total and total > 0:
        if domestic is not None:
            domestic_pct = round(domestic / total * 100, 1)
        if international is not None:
            international_pct = round(international / total * 100, 1)
        # Infer missing half if we have one side
        if domestic is not None and international is None:
            international = total - domestic
            international_pct = round(international / total * 100, 1)
        elif international is not None and domestic is None:
            domestic = total - international
            domestic_pct = round(domestic / total * 100, 1)

    unionized_pct = extraction.unionized_employee_pct
    if unionized_pct is None and extraction.unionized_employee_count is not None and total and total > 0:
        unionized_pct = round(extraction.unionized_employee_count / total * 100, 1)

    value: dict[str, Any] = {
        "total_employees": total,
        "domestic_count": domestic,
        "international_count": international,
        "domestic_pct": domestic_pct,
        "international_pct": international_pct,
        "unionized_count": extraction.unionized_employee_count,
        "unionized_pct": unionized_pct,
    }

    return SourcedValue[dict[str, Any]](
        value=value,
        source="10-K Item 1 (LLM)",
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )


def convert_operational_resilience(
    extraction: TenKExtraction,
) -> SourcedValue[dict[str, Any]] | None:
    """Convert operational resilience fields into a composite dict.

    Combines geography, facility dependency, and supply chain data.
    Infers supply_chain_depth from description keywords.
    Returns None if no resilience data was extracted.
    """
    has_data = any(
        getattr(extraction, f) is not None
        for f in (
            "primary_operations_geography",
            "single_facility_dependency",
            "supply_chain_description",
        )
    )
    if not has_data:
        return None

    # Infer supply chain depth from description
    depth = "moderate"
    desc = extraction.supply_chain_description or ""
    desc_lower = desc.lower()
    if any(kw in desc_lower for kw in ("vertically integrated", "diversified", "multiple source")):
        depth = "deep"
    elif any(kw in desc_lower for kw in ("single-source", "single source", "concentrated", "sole supplier")):
        depth = "shallow"

    value: dict[str, Any] = {
        "primary_geography": extraction.primary_operations_geography,
        "single_facility_risk": extraction.single_facility_dependency or False,
        "supply_chain_description": extraction.supply_chain_description,
        "supply_chain_depth": depth,
    }

    return SourcedValue[dict[str, Any]](
        value=value,
        source="10-K Item 1A (LLM)",
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )


def convert_competitive_position(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert competitive position summary to SourcedValue[str].

    Returns None if the field is None or empty.
    """
    if not extraction.competitive_position:
        return None
    return sourced_str(extraction.competitive_position, _LLM_SOURCE, Confidence.HIGH)


def convert_regulatory_environment(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert regulatory environment summary to SourcedValue[str].

    Returns None if the field is None or empty.
    """
    if not extraction.regulatory_environment:
        return None
    return sourced_str(
        extraction.regulatory_environment, _LLM_SOURCE, Confidence.HIGH
    )


# ------------------------------------------------------------------
# Item 1: Business Model Dimensions (v6.0 BMOD)
# ------------------------------------------------------------------

_BMOD_SOURCE = "10-K + Proxy (LLM)"


def convert_revenue_model_type(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert revenue model type to SourcedValue[str].

    Returns None if the field is None or empty.
    Valid values: RECURRING, PROJECT, TRANSACTION, HYBRID.
    """
    if not extraction.revenue_model_type:
        return None
    return sourced_str(extraction.revenue_model_type, _LLM_SOURCE, Confidence.MEDIUM)


def convert_key_person_risk(
    extraction: TenKExtraction,
) -> SourcedValue[dict[str, Any]] | None:
    """Combine key person indicators into a composite risk dict.

    Computes risk_score (0-3): +1 if founder-led, +1 if CEO tenure
    >10yr, +1 if no succession plan disclosed.
    Returns None if no key person data was extracted.
    """
    # Need at least one data point to produce a result
    if (
        extraction.is_founder_led is None
        and extraction.ceo_tenure_years is None
        and extraction.has_succession_plan is None
    ):
        return None

    risk_score = 0
    if extraction.is_founder_led is True:
        risk_score += 1
    if extraction.ceo_tenure_years is not None and extraction.ceo_tenure_years > 10:
        risk_score += 1
    if extraction.has_succession_plan is False:
        risk_score += 1

    value: dict[str, Any] = {
        "is_founder_led": extraction.is_founder_led,
        "ceo_tenure_years": extraction.ceo_tenure_years,
        "has_succession_plan": extraction.has_succession_plan,
        "risk_score": risk_score,
    }

    return SourcedValue[dict[str, Any]](
        value=value,
        source=_BMOD_SOURCE,
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )


def convert_segment_lifecycle(
    extraction: TenKExtraction,
) -> list[SourcedValue[dict[str, str | float]]]:
    """Parse segment lifecycle stage strings into structured dicts.

    Expected input format: 'Segment Name: STAGE (X% YoY)'
    Returns list of SourcedValue with keys: name, stage, growth_rate.
    """
    import re

    results: list[SourcedValue[dict[str, str | float]]] = []
    for entry in extraction.segment_lifecycle_stages:
        # Parse "Cloud: GROWTH (20% YoY)" or "Legacy: DECLINING (-5% YoY)"
        parts = entry.split(":", 1)
        name = parts[0].strip() if len(parts) > 1 else entry.strip()
        remainder = parts[1].strip() if len(parts) > 1 else ""

        stage = "UNKNOWN"
        growth_rate = 0.0

        for s in ("GROWTH", "MATURE", "DECLINING"):
            if s in remainder.upper():
                stage = s
                break

        # Extract percentage from parentheses
        pct_match = re.search(r"([+-]?\d+\.?\d*)%", remainder)
        if pct_match:
            growth_rate = float(pct_match.group(1))

        value: dict[str, str | float] = {
            "name": name,
            "stage": stage,
            "growth_rate": growth_rate,
        }
        results.append(
            SourcedValue[dict[str, str | float]](
                value=value,
                source=_LLM_SOURCE,
                confidence=Confidence.MEDIUM,
                as_of=now(),
            )
        )
    return results


def convert_disruption_risk(
    extraction: TenKExtraction,
) -> SourcedValue[dict[str, Any]] | None:
    """Convert disruption threats into a risk assessment dict.

    Level: HIGH if >= 3 threats, MODERATE if >= 1, LOW if 0.
    Returns None only if disruption_threats is empty AND no other
    signal suggests disruption assessment was attempted.
    """
    threats = extraction.disruption_threats
    threat_count = len(threats)

    if threat_count >= 3:
        level = "HIGH"
    elif threat_count >= 1:
        level = "MODERATE"
    else:
        level = "LOW"

    value: dict[str, Any] = {
        "level": level,
        "threats": threats,
        "threat_count": threat_count,
    }

    return SourcedValue[dict[str, Any]](
        value=value,
        source=_LLM_SOURCE,
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )


def convert_segment_margins(
    extraction: TenKExtraction,
) -> list[SourcedValue[dict[str, str | float]]]:
    """Parse segment margin strings into structured dicts.

    Expected input format: 'Name: X% (prior year: Y%)'
    Returns list of SourcedValue with keys: name, margin_pct,
    prior_margin_pct, change_bps.
    """
    import re

    results: list[SourcedValue[dict[str, str | float]]] = []
    for entry in extraction.segment_margins:
        # Parse "Cloud: 35.0% (prior year: 32.0%)"
        parts = entry.split(":", 1)
        name = parts[0].strip() if len(parts) > 1 else entry.strip()
        remainder = parts[1].strip() if len(parts) > 1 else ""

        margin_pct = 0.0
        prior_margin_pct = 0.0

        # Extract current margin (first percentage)
        pct_matches = re.findall(r"([+-]?\d+\.?\d*)%", remainder)
        if pct_matches:
            margin_pct = float(pct_matches[0])
        if len(pct_matches) >= 2:
            prior_margin_pct = float(pct_matches[1])

        # Change in basis points: (current - prior) * 100
        change_bps = round((margin_pct - prior_margin_pct) * 100)

        value: dict[str, str | float] = {
            "name": name,
            "margin_pct": margin_pct,
            "prior_margin_pct": prior_margin_pct,
            "change_bps": float(change_bps),
        }
        results.append(
            SourcedValue[dict[str, str | float]](
                value=value,
                source=_LLM_SOURCE,
                confidence=Confidence.MEDIUM,
                as_of=now(),
            )
        )
    return results


# ------------------------------------------------------------------
# Item 7: MD&A
# ------------------------------------------------------------------


def convert_mda_qualitative(
    extraction: TenKExtraction,
) -> dict[str, SourcedValue[str] | list[SourcedValue[str]] | None]:
    """Convert MD&A qualitative fields to a dict of SourcedValues.

    Returns a dict with keys:
    - revenue_trend: SourcedValue[str] | None
    - margin_trend: SourcedValue[str] | None
    - key_financial_concerns: list[SourcedValue[str]]
    - guidance_language: SourcedValue[str] | None
    - critical_accounting_estimates: list[SourcedValue[str]]
    - non_gaap_measures: list[SourcedValue[str]]
    """
    result: dict[str, SourcedValue[str] | list[SourcedValue[str]] | None] = {}

    # Scalar string fields.
    result["revenue_trend"] = (
        sourced_str(extraction.revenue_trend, _LLM_SOURCE, Confidence.HIGH)
        if extraction.revenue_trend
        else None
    )
    result["margin_trend"] = (
        sourced_str(extraction.margin_trend, _LLM_SOURCE, Confidence.HIGH)
        if extraction.margin_trend
        else None
    )
    result["guidance_language"] = (
        sourced_str(extraction.guidance_language, _LLM_SOURCE, Confidence.HIGH)
        if extraction.guidance_language
        else None
    )

    # List fields: key_financial_concerns is list[str] on the schema.
    result["key_financial_concerns"] = [
        sourced_str(c, _LLM_SOURCE, Confidence.HIGH)
        for c in extraction.key_financial_concerns
    ]

    # List fields for estimates and non-GAAP measures.
    result["critical_accounting_estimates"] = [
        sourced_str(e, _LLM_SOURCE, Confidence.HIGH)
        for e in extraction.critical_accounting_estimates
    ]
    result["non_gaap_measures"] = [
        sourced_str(m, _LLM_SOURCE, Confidence.HIGH)
        for m in extraction.non_gaap_measures
    ]

    return result


# ------------------------------------------------------------------
# Item 8: Financial Statements (footnote enrichment)
# ------------------------------------------------------------------


def convert_debt_enrichment(
    extraction: TenKExtraction,
) -> dict[str, SourcedValue[str] | list[SourcedValue[str]] | None]:
    """Convert Item 8 footnote fields to qualitative SourcedValues.

    These SUPPLEMENT XBRL financial data -- they provide qualitative
    context about debt instruments, credit facilities, covenants,
    and tax positions. They NEVER override XBRL numeric values.

    Returns a dict with keys:
    - debt_instruments: list[SourcedValue[str]]
    - credit_facility_detail: SourcedValue[str] | None
    - covenant_status: SourcedValue[str] | None
    - tax_rate_notes: SourcedValue[str] | None
    """
    result: dict[str, SourcedValue[str] | list[SourcedValue[str]] | None] = {}

    result["debt_instruments"] = [
        sourced_str(d, _LLM_SOURCE, Confidence.HIGH)
        for d in extraction.debt_instruments
    ]

    result["credit_facility_detail"] = (
        sourced_str(extraction.credit_facility_detail, _LLM_SOURCE, Confidence.HIGH)
        if extraction.credit_facility_detail
        else None
    )

    result["covenant_status"] = (
        sourced_str(extraction.covenant_status, _LLM_SOURCE, Confidence.HIGH)
        if extraction.covenant_status
        else None
    )

    result["tax_rate_notes"] = (
        sourced_str(extraction.tax_rate_notes, _LLM_SOURCE, Confidence.HIGH)
        if extraction.tax_rate_notes
        else None
    )

    return result


def convert_stock_comp_detail(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert stock compensation detail to SourcedValue[str].

    Returns None if the field is None or empty.
    """
    if not extraction.stock_comp_detail:
        return None
    return sourced_str(extraction.stock_comp_detail, _LLM_SOURCE, Confidence.HIGH)


# ------------------------------------------------------------------
# Item 9A: Controls and Procedures
# ------------------------------------------------------------------


def convert_controls_assessment(
    extraction: TenKExtraction,
) -> dict[str, Any]:
    """Convert Item 9A controls fields to a dict of SourcedValues.

    Returns a dict with keys:
    - has_material_weakness: SourcedValue[bool] | None
    - material_weakness_detail: list[SourcedValue[str]]
    - significant_deficiencies: list[SourcedValue[str]]
    - remediation_status: SourcedValue[str] | None
    - auditor_attestation: SourcedValue[str] | None
    - auditor_name: SourcedValue[str] | None
    - auditor_tenure_years: SourcedValue[int] | None
    """
    result: dict[str, Any] = {}

    # has_material_weakness is a bool (not optional) on TenKExtraction,
    # but we still wrap it as SourcedValue for downstream consumers.
    result["has_material_weakness"] = _sourced_bool(extraction.has_material_weakness)

    result["material_weakness_detail"] = [
        sourced_str(mw, _LLM_SOURCE, Confidence.HIGH)
        for mw in extraction.material_weakness_detail
    ]

    result["significant_deficiencies"] = [
        sourced_str(sd, _LLM_SOURCE, Confidence.HIGH)
        for sd in extraction.significant_deficiencies
    ]

    result["remediation_status"] = (
        sourced_str(extraction.remediation_status, _LLM_SOURCE, Confidence.HIGH)
        if extraction.remediation_status
        else None
    )

    result["auditor_attestation"] = (
        sourced_str(extraction.auditor_attestation, _LLM_SOURCE, Confidence.HIGH)
        if extraction.auditor_attestation
        else None
    )

    result["auditor_name"] = (
        sourced_str(extraction.auditor_name, _LLM_SOURCE, Confidence.HIGH)
        if extraction.auditor_name
        else None
    )

    result["auditor_tenure_years"] = (
        sourced_int(extraction.auditor_tenure_years, _LLM_SOURCE, Confidence.HIGH)
        if extraction.auditor_tenure_years is not None
        else None
    )

    return result


# ------------------------------------------------------------------
# Business Combinations / M&A
# ------------------------------------------------------------------


def convert_goodwill_balance(
    extraction: TenKExtraction,
) -> SourcedValue[float] | None:
    """Convert goodwill balance to SourcedValue[float]."""
    val = getattr(extraction, "goodwill_balance", None)
    if val is None:
        return None
    return sourced_float(float(val), _LLM_SOURCE, Confidence.HIGH)


def convert_acquisitions_total_spend(
    extraction: TenKExtraction,
) -> SourcedValue[float] | None:
    """Convert total acquisition spend to SourcedValue[float]."""
    val = getattr(extraction, "acquisitions_total_spend", None)
    if val is None:
        return None
    return sourced_float(float(val), _LLM_SOURCE, Confidence.HIGH)


def convert_acquisitions(
    extraction: TenKExtraction,
) -> list[SourcedValue[str]]:
    """Convert acquisitions list to SourcedValue[str] list."""
    raw = getattr(extraction, "acquisitions", [])
    if not raw:
        return []
    return [
        sourced_str(str(a), _LLM_SOURCE, Confidence.HIGH)
        for a in raw if a
    ]


def convert_goodwill_change_description(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert goodwill change description to SourcedValue[str]."""
    val = getattr(extraction, "goodwill_change_description", None)
    if not val:
        return None
    return sourced_str(str(val), _LLM_SOURCE, Confidence.HIGH)
