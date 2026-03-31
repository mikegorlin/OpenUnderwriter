"""Operational data extraction -- OPS-02, OPS-03, OPS-04.

Extracts subsidiary structure (jurisdiction-level with regulatory regime
classification), workforce distribution (domestic/international split,
unionization), and operational resilience (geographic concentration,
facility risk, supply chain depth).

These populate CompanyProfile fields consumed by BIZ.OPS.* brain signals.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_texts,
    get_filings,
    now,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# --- Regulatory regime classification ---

# Jurisdictions with heavy financial/data/healthcare regulation
_HIGH_REG_JURISDICTIONS: set[str] = {
    "united kingdom", "england", "scotland", "wales",
    "singapore", "hong kong", "china", "india",
    "germany", "france", "japan", "switzerland",
    "australia", "south korea", "republic of korea",
    "brazil", "ireland", "netherlands", "italy",
    "spain", "sweden", "denmark", "norway", "finland",
    "belgium", "austria", "portugal",
}


def _classify_regime(jurisdiction: str, tax_havens: set[str]) -> str:
    """Classify a jurisdiction's regulatory regime.

    Returns: HIGH_REG, LOW_REG (tax haven/offshore), or MEDIUM_REG.
    """
    lower = jurisdiction.lower().strip()
    if lower in tax_havens:
        return "LOW_REG"
    if lower in _HIGH_REG_JURISDICTIONS:
        return "HIGH_REG"
    return "MEDIUM_REG"


# ------------------------------------------------------------------
# OPS-02: Subsidiary structure
# ------------------------------------------------------------------


def extract_subsidiary_structure(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Extract subsidiary jurisdiction structure with regulatory regime classification.

    Uses existing geographic_footprint data (from Exhibit 21 parsing) to build
    a jurisdiction-level summary with regulatory regime classification.
    """
    expected = ["subsidiary_structure"]
    found: list[str] = []
    warnings: list[str] = []

    # Get geographic footprint data (already parsed from Exhibit 21)
    profile = state.company
    if profile is None:
        return None, create_report(
            extractor_name="subsidiary_structure",
            expected=expected, found=found,
            source_filing="Exhibit 21",
            warnings=["No company profile available"],
        )

    geo_data = profile.geographic_footprint
    if not geo_data:
        warnings.append("No geographic footprint data available for subsidiary structure")
        return None, create_report(
            extractor_name="subsidiary_structure",
            expected=expected, found=found,
            source_filing="Exhibit 21",
            warnings=warnings,
        )

    # Load tax havens for LOW_REG classification
    from do_uw.stages.extract.profile_helpers import _load_tax_havens

    tax_havens = _load_tax_havens()

    # Build jurisdiction-level summary from geographic footprint
    jurisdictions: list[dict[str, Any]] = []
    total_subs = 0
    high_reg_count = 0
    low_reg_count = 0
    tax_haven_count = 0

    for sv_geo in geo_data:
        entry = sv_geo.value
        jurisdiction_name = str(
            entry.get("jurisdiction", entry.get("region", "Unknown"))
        )
        sub_count = int(float(entry.get("subsidiary_count", 1)))
        total_subs += sub_count

        regime = _classify_regime(jurisdiction_name, tax_havens)

        jurisdictions.append({
            "name": jurisdiction_name,
            "count": sub_count,
            "regulatory_regime": regime,
        })

        if regime == "HIGH_REG":
            high_reg_count += 1
        elif regime == "LOW_REG":
            low_reg_count += 1

        if entry.get("tax_haven") == "true":
            tax_haven_count += 1

    jurisdiction_count = len(jurisdictions)

    value: dict[str, Any] = {
        "total_subsidiaries": total_subs,
        "jurisdiction_count": jurisdiction_count,
        "jurisdictions": jurisdictions,
        "high_reg_count": high_reg_count,
        "low_reg_count": low_reg_count,
        "tax_haven_count": tax_haven_count,
    }

    found.append("subsidiary_structure")
    result = SourcedValue[dict[str, Any]](
        value=value,
        source="Exhibit 21",
        confidence=Confidence.HIGH,
        as_of=now(),
    )

    logger.info(
        "Subsidiary structure: %d subs across %d jurisdictions "
        "(%d high-reg, %d low-reg, %d tax haven)",
        total_subs, jurisdiction_count, high_reg_count,
        low_reg_count, tax_haven_count,
    )

    return result, create_report(
        extractor_name="subsidiary_structure",
        expected=expected, found=found,
        source_filing="Exhibit 21",
        warnings=warnings,
    )


# ------------------------------------------------------------------
# OPS-03: Workforce distribution
# ------------------------------------------------------------------


def extract_workforce_distribution(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Extract workforce distribution: domestic/international split, unionization.

    Priority: LLM extraction > regex fallback on 10-K text > total employee count only.
    """
    expected = ["workforce_distribution"]
    found: list[str] = []
    warnings: list[str] = []

    # Try LLM extraction first (via converter)
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k
    from do_uw.stages.extract.ten_k_converters import convert_workforce_distribution

    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is not None:
        llm_result = convert_workforce_distribution(llm_ten_k)
        if llm_result is not None and _has_workforce_detail(llm_result.value):
            found.append("workforce_distribution")
            return llm_result, create_report(
                extractor_name="workforce_distribution",
                expected=expected, found=found,
                source_filing="10-K Item 1 (LLM)",
            )

    # Fallback: regex on 10-K text
    filing_texts = get_filing_texts(get_filings(state))
    combined = " ".join(
        str(filing_texts.get(k, ""))
        for k in ("10-K_item1", "item1", "10-K_item7", "item7")
    ).strip()

    result = _regex_workforce(combined, state)
    if result is not None:
        found.append("workforce_distribution")
        return result, create_report(
            extractor_name="workforce_distribution",
            expected=expected, found=found,
            source_filing="10-K text",
        )

    # Last resort: just total employee count
    profile = state.company
    if profile is not None and profile.employee_count is not None:
        value: dict[str, Any] = {
            "total_employees": profile.employee_count.value,
            "domestic_count": None,
            "international_count": None,
            "domestic_pct": None,
            "international_pct": None,
            "unionized_count": None,
            "unionized_pct": None,
        }
        found.append("workforce_distribution")
        return (
            SourcedValue[dict[str, Any]](
                value=value,
                source="yfinance",
                confidence=Confidence.MEDIUM,
                as_of=now(),
            ),
            create_report(
                extractor_name="workforce_distribution",
                expected=expected, found=found,
                source_filing="yfinance",
                warnings=["Only total employee count available; no breakdown"],
            ),
        )

    warnings.append("No workforce data available")
    return None, create_report(
        extractor_name="workforce_distribution",
        expected=expected, found=found,
        source_filing="10-K",
        warnings=warnings,
    )


def _has_workforce_detail(value: dict[str, Any]) -> bool:
    """Check if workforce dict has more than just total_employees."""
    return any(
        value.get(k) is not None
        for k in ("domestic_count", "international_count", "unionized_count", "unionized_pct")
    ) or value.get("total_employees") is not None


def _regex_workforce(
    text: str, state: AnalysisState,
) -> SourcedValue[dict[str, Any]] | None:
    """Extract workforce data from 10-K text using regex patterns."""
    if not text:
        return None

    total = None
    domestic = None
    international = None
    unionized_pct: float | None = None

    # Total employees (common patterns)
    total_pat = re.compile(
        r"(?:approximately|about|had|employed)\s+([\d,]+)\s+"
        r"(?:full[- ]time\s+)?employees",
        re.IGNORECASE,
    )
    m = total_pat.search(text)
    if m:
        total = int(m.group(1).replace(",", ""))

    # Domestic/US employees
    us_pat = re.compile(
        r"(?:approximately|about)?\s*([\d,]+)\s+"
        r"(?:employees?\s+(?:in|within)\s+the\s+United\s+States"
        r"|(?:domestic|U\.?S\.?)\s+employees?)",
        re.IGNORECASE,
    )
    m = us_pat.search(text)
    if m:
        domestic = int(m.group(1).replace(",", ""))

    # International employees
    intl_pat = re.compile(
        r"(?:approximately|about)?\s*([\d,]+)\s+"
        r"(?:employees?\s+(?:outside|international|non-U\.?S\.?)"
        r"|(?:international|non-U\.?S\.?)\s+employees?)",
        re.IGNORECASE,
    )
    m = intl_pat.search(text)
    if m:
        international = int(m.group(1).replace(",", ""))

    # Unionization percentage
    union_pct_pat = re.compile(
        r"(?:approximately|about)?\s*(\d+(?:\.\d+)?)\s*%\s*"
        r"(?:of\s+(?:our\s+)?employees?\s+(?:are|were)\s+)?"
        r"(?:covered\s+by|represented\s+by|subject\s+to)\s+"
        r"collective\s+bargaining",
        re.IGNORECASE,
    )
    m = union_pct_pat.search(text)
    if m:
        unionized_pct = float(m.group(1))

    # Also check for "none of our employees are unionized" type language
    if unionized_pct is None:
        no_union_pat = re.compile(
            r"(?:none|no)\s+(?:of\s+)?(?:our\s+)?employees?\s+"
            r"(?:are|is)\s+(?:represented|covered|unionized)",
            re.IGNORECASE,
        )
        if no_union_pat.search(text):
            unionized_pct = 0.0

    # If no regex found anything useful, return None
    if total is None and domestic is None and international is None and unionized_pct is None:
        return None

    # Use profile total if regex didn't find it
    if total is None:
        profile = state.company
        if profile is not None and profile.employee_count is not None:
            total = profile.employee_count.value

    # Compute percentages
    domestic_pct: float | None = None
    international_pct: float | None = None
    if total and total > 0:
        if domestic is not None:
            domestic_pct = round(domestic / total * 100, 1)
        if international is not None:
            international_pct = round(international / total * 100, 1)
        if domestic is not None and international is None:
            international = total - domestic
            international_pct = round(international / total * 100, 1)
        elif international is not None and domestic is None:
            domestic = total - international
            domestic_pct = round(domestic / total * 100, 1)

    value: dict[str, Any] = {
        "total_employees": total,
        "domestic_count": domestic,
        "international_count": international,
        "domestic_pct": domestic_pct,
        "international_pct": international_pct,
        "unionized_count": None,
        "unionized_pct": unionized_pct,
    }

    return SourcedValue[dict[str, Any]](
        value=value,
        source="10-K text",
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )


# ------------------------------------------------------------------
# OPS-04: Operational resilience
# ------------------------------------------------------------------


def extract_operational_resilience(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Extract operational resilience indicators.

    Combines LLM-extracted facility/supply-chain data with derived
    geographic concentration score from Exhibit 21 data.
    """
    expected = ["operational_resilience"]
    found: list[str] = []
    warnings: list[str] = []

    # Try LLM extraction
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k
    from do_uw.stages.extract.ten_k_converters import convert_operational_resilience

    llm_result: SourcedValue[dict[str, Any]] | None = None
    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is not None:
        llm_result = convert_operational_resilience(llm_ten_k)

    # Derive geographic concentration score from Exhibit 21 data
    geo_score = _compute_geo_concentration(state)

    # Build composite result
    primary_geo: str | None = None
    single_facility: bool = False
    supply_desc: str | None = None
    supply_depth: str = "moderate"

    if llm_result is not None:
        llm_val = llm_result.value
        primary_geo = llm_val.get("primary_geography")
        single_facility = llm_val.get("single_facility_risk", False)
        supply_desc = llm_val.get("supply_chain_description")
        supply_depth = llm_val.get("supply_chain_depth", "moderate")

    # Overall assessment
    if geo_score > 80 or single_facility:
        overall = "WEAK"
    elif geo_score < 40 and supply_depth == "deep":
        overall = "STRONG"
    else:
        overall = "ADEQUATE"

    # Only return None if we have absolutely no data
    if llm_result is None and geo_score == 0:
        profile = state.company
        if profile is None or not profile.geographic_footprint:
            warnings.append("No operational resilience data available")
            return None, create_report(
                extractor_name="operational_resilience",
                expected=expected, found=found,
                source_filing="10-K",
                warnings=warnings,
            )

    value: dict[str, Any] = {
        "geographic_concentration_score": geo_score,
        "primary_geography": primary_geo,
        "single_facility_risk": single_facility,
        "supply_chain_depth": supply_depth,
        "supply_chain_description": supply_desc,
        "overall_assessment": overall,
    }

    found.append("operational_resilience")
    result = SourcedValue[dict[str, Any]](
        value=value,
        source="10-K + Exhibit 21",
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )

    logger.info(
        "Operational resilience: geo_score=%d, single_facility=%s, "
        "supply_chain=%s, overall=%s",
        geo_score, single_facility, supply_depth, overall,
    )

    return result, create_report(
        extractor_name="operational_resilience",
        expected=expected, found=found,
        source_filing="10-K + Exhibit 21",
        warnings=warnings,
    )


def _compute_geo_concentration(state: AnalysisState) -> int:
    """Compute geographic concentration score (0-100) from Exhibit 21 data.

    Uses Herfindahl-Hirschman Index (HHI) approach:
    - If top 1 jurisdiction has >60% of subsidiaries: score 80+
    - If top 2 have >80%: score 60-80
    - Otherwise: proportional to HHI
    """
    profile = state.company
    if profile is None or not profile.geographic_footprint:
        return 0

    counts: list[int] = []
    for sv_geo in profile.geographic_footprint:
        entry = sv_geo.value
        count = int(float(entry.get("subsidiary_count", 1)))
        counts.append(count)

    if not counts:
        return 0

    total = sum(counts)
    if total == 0:
        return 0

    # Sort descending
    counts.sort(reverse=True)

    # Top 1 concentration
    top1_pct = counts[0] / total * 100

    if top1_pct > 60:
        return min(100, int(80 + (top1_pct - 60) * 0.5))

    # Top 2 concentration
    if len(counts) >= 2:
        top2_pct = (counts[0] + counts[1]) / total * 100
        if top2_pct > 80:
            return int(60 + (top2_pct - 80) * 1.0)

    # HHI-based score (0-10000 scale -> 0-100)
    hhi = sum((c / total * 100) ** 2 for c in counts)
    # Normalize: HHI of 10000 (perfect concentration) = 100
    return min(100, int(hhi / 100))
