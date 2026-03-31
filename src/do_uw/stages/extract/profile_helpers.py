"""Helper extractors for company profile -- geographic, concentration, exposure.

Exhibit 21 parsing, customer/supplier concentration, D&O exposure mapping,
event timeline, and section summary generation.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_texts,
    get_filings,
    get_info_dict,
    sourced_dict,
    sourced_int,
    sourced_str,
    sourced_str_dict,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Jurisdictions recognized by the Exhibit 21 parsers.
_KNOWN_JURISDICTIONS: set[str] = {
    # US states
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
    "district of columbia", "puerto rico",
    # Countries / territories
    "united kingdom", "england", "scotland", "wales", "ireland",
    "germany", "france", "japan", "china", "india", "canada", "australia",
    "singapore", "hong kong", "switzerland", "netherlands", "brazil",
    "cayman islands", "bermuda", "luxembourg", "british virgin islands",
    "belgium", "norway", "sweden", "denmark", "finland", "austria",
    "italy", "spain", "portugal", "greece", "turkey", "israel",
    "south korea", "republic of korea", "taiwan", "thailand",
    "indonesia", "malaysia", "philippines", "vietnam", "mexico",
    "colombia", "argentina", "chile", "peru", "south africa",
    "united arab emirates", "saudi arabia", "qatar", "bahrain",
    "new zealand", "iceland", "czech republic", "czechia", "poland",
    "hungary", "romania", "croatia", "slovakia", "slovenia",
    "jordan", "egypt",
}


def _load_tax_havens() -> set[str]:
    """Load tax haven jurisdiction names from config."""
    data = load_config("tax_havens")
    if not data:
        return set()
    raw_list = data.get("jurisdictions", [])
    if not isinstance(raw_list, list):
        return set()
    jurisdictions = cast(list[dict[str, str]], raw_list)
    return {j["name"].lower() for j in jurisdictions if "name" in j}


# -----------------------------------------------------------------------
# SECT2-03: Geographic footprint (Exhibit 21)
# -----------------------------------------------------------------------


def extract_geographic_footprint(
    state: AnalysisState,
) -> tuple[list[SourcedValue[dict[str, str | float]]], ExtractionReport]:
    """Parse Exhibit 21 for geographic presence of subsidiaries."""
    filings = get_filings(state)
    expected = ["geographic_footprint", "subsidiary_count"]
    found: list[str] = []
    warnings: list[str] = []

    exhibit_21_raw = filings.get("exhibit_21", "")
    if not isinstance(exhibit_21_raw, str):
        exhibit_21_raw = str(exhibit_21_raw)

    if not exhibit_21_raw.strip():
        warnings.append("Exhibit 21 text not available in acquired data")
        return [], create_report(
            extractor_name="geographic_footprint", expected=expected,
            found=found, source_filing="Exhibit 21", warnings=warnings,
        )

    source = "Exhibit 21 (subsidiary list)"
    subs = _parse_exhibit21_html_table(exhibit_21_raw)
    if not subs:
        subs = _parse_exhibit21_pattern(exhibit_21_raw)
    if not subs:
        subs = _parse_exhibit21_lines(exhibit_21_raw)
    if not subs:
        subs = _parse_exhibit21_continuous(exhibit_21_raw)

    geo: list[SourcedValue[dict[str, str | float]]] = []
    if subs:
        geo = _build_geo_entries(subs, _load_tax_havens(), source)
        found.extend(["geographic_footprint", "subsidiary_count"])

    report = create_report(
        extractor_name="geographic_footprint", expected=expected,
        found=found, source_filing=source, warnings=warnings,
    )
    if state.company is not None and subs:
        state.company.subsidiary_count = sourced_int(
            len(subs), source, Confidence.HIGH
        )
    return geo, report


def _build_geo_entries(
    subs: list[tuple[str, str]], tax_havens: set[str], source: str,
) -> list[SourcedValue[dict[str, str | float]]]:
    """Build geographic footprint entries from parsed subsidiaries."""
    counts: dict[str, int] = {}
    for _name, j in subs:
        key = j.strip()
        counts[key] = counts.get(key, 0) + 1

    geo: list[SourcedValue[dict[str, str | float]]] = []
    for jurisdiction, count in sorted(counts.items(), key=lambda x: -x[1]):
        entry: dict[str, str | float] = {
            "jurisdiction": jurisdiction, "subsidiary_count": float(count),
        }
        if jurisdiction.lower() in tax_havens:
            entry["tax_haven"] = "true"
        geo.append(sourced_dict(entry, source, Confidence.HIGH))
    return geo


def _parse_exhibit21_html_table(html: str) -> list[tuple[str, str]]:
    """Parse Exhibit 21 from HTML table format."""
    results: list[tuple[str, str]] = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.I | re.DOTALL):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.I | re.DOTALL)
        if len(cells) >= 2:
            name = re.sub(r"<[^>]+>", "", cells[0]).strip()
            j = re.sub(r"<[^>]+>", "", cells[1]).strip()
            if name and j and not _is_header_row(name):
                results.append((name, j))
    return results


def _parse_exhibit21_pattern(text: str) -> list[tuple[str, str]]:
    """Parse Exhibit 21 using common text patterns."""
    results: list[tuple[str, str]] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or _is_header_row(s):
            continue
        if "\t" in s:
            parts = [p.strip() for p in s.split("\t") if p.strip()]
            if len(parts) >= 2:
                results.append((parts[0], parts[-1]))
                continue
        parts = re.split(r"\s{3,}", s)
        if len(parts) >= 2:
            results.append((parts[0].strip(), parts[-1].strip()))
    return results


def _parse_exhibit21_lines(text: str) -> list[tuple[str, str]]:
    """Parse Exhibit 21 line-by-line with jurisdiction keyword detection."""
    results: list[tuple[str, str]] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or _is_header_row(s):
            continue
        lower = s.lower()
        for j in _KNOWN_JURISDICTIONS:
            if j in lower:
                idx = lower.rfind(j)
                name = s[:idx].strip().rstrip(",.- ") if idx > 0 else s
                jur = s[idx:].strip() if idx > 0 else j.title()
                if name:
                    results.append((name, jur))
                break
    return results


def _parse_exhibit21_continuous(text: str) -> list[tuple[str, str]]:
    """Parse Exhibit 21 when the entire text is a single continuous line.

    SEC EDGAR filings sometimes produce Exhibit 21 as a single line with
    no newlines, tabs, or HTML tables. The format is:
        Header... Name1 Jurisdiction1 Name2 Jurisdiction2 ...
    This parser uses regex to find known jurisdictions and extract the
    entity name preceding each jurisdiction match.
    """
    # Strip the header.
    lower = text.lower()
    header_end_markers = [
        "jurisdiction of incorporation or organization",
        "state or other jurisdiction",
        "state or country of incorporation",
    ]
    start = 0
    for marker in header_end_markers:
        idx = lower.find(marker)
        if idx >= 0:
            start = max(start, idx + len(marker))

    body = text[start:]
    if len(body) < 10:
        return []

    # Build regex for all known jurisdictions (sorted longest first
    # to match e.g. "New York" before "York").
    sorted_j = sorted(_KNOWN_JURISDICTIONS, key=len, reverse=True)
    pattern = "|".join(re.escape(j.title()) for j in sorted_j)
    # Also add original-case variants for countries with special chars
    pat = re.compile(
        r"(" + pattern + r")",
        re.IGNORECASE,
    )

    results: list[tuple[str, str]] = []
    prev_end = 0
    for m in pat.finditer(body):
        name_raw = body[prev_end:m.start()].strip()
        jurisdiction = m.group(1).strip()
        prev_end = m.end()
        # Clean up entity name (remove trailing punctuation).
        name_raw = name_raw.strip(" ,.-\t\n")
        if name_raw and not _is_header_row(name_raw):
            results.append((name_raw, jurisdiction))

    return results


def _is_header_row(text: str) -> bool:
    """Check if a line is a header row in Exhibit 21."""
    lower = text.lower()
    return any(kw in lower for kw in (
        "name of subsidiary", "jurisdiction", "state or country",
        "incorporated", "organized", "name of company",
    ))


# -----------------------------------------------------------------------
# SECT2-04: Customer/supplier concentration
# -----------------------------------------------------------------------


def extract_concentration(
    state: AnalysisState,
) -> tuple[
    list[SourcedValue[dict[str, str | float]]],
    list[SourcedValue[dict[str, str | float]]],
    ExtractionReport,
]:
    """Extract customer and supplier concentration from 10-K text."""
    filing_texts = get_filing_texts(get_filings(state))
    expected = ["customer_concentration", "supplier_concentration"]
    found: list[str] = []
    source = "10-K text"

    combined = " ".join(
        str(filing_texts.get(k, ""))
        for k in ("10-K_item1", "10-K_item7", "item1", "item7")
    ).strip()

    customers: list[SourcedValue[dict[str, str | float]]] = []
    suppliers: list[SourcedValue[dict[str, str | float]]] = []

    if combined:
        customers = _extract_customers(combined, source)
        if customers:
            found.append("customer_concentration")
        suppliers = _extract_suppliers(combined, source)
        if suppliers:
            found.append("supplier_concentration")

    return customers, suppliers, create_report(
        extractor_name="concentration", expected=expected,
        found=found, source_filing=source,
    )


def _extract_customers(
    text: str, source: str
) -> list[SourcedValue[dict[str, str | float]]]:
    """Extract customer concentration from filing text."""
    result: list[SourcedValue[dict[str, str | float]]] = []
    patterns = [
        r"(?:customer|client)\s+\w*\s*(?:accounted?\s+for|represent(?:ed|s)?)\s+"
        r"(?:approximately\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?"
        r"(?:revenue|sales|net\s+(?:revenue|sales))",
        r"(\d+(?:\.\d+)?)\s*%\s*of\s*(?:our\s+)?(?:total\s+)?"
        r"(?:revenue|sales|net\s+(?:revenue|sales))"
        r".*?(?:was|were)\s+(?:from|attributable\s+to)\s+"
        r"(?:a\s+single|one)\s+(?:customer|client)",
    ]
    for pat in patterns:
        for match in re.findall(pat, text, re.IGNORECASE):
            result.append(sourced_dict(
                {"customer": "Major Customer", "revenue_pct": float(match)},
                source, Confidence.MEDIUM,
            ))
    # Detect explicit "no concentration" disclosures (e.g. "no single
    # customer accounted for more than 10% of revenue").
    if not result:
        no_conc_pat = (
            r"no\s+(?:single|individual|one)\s+(?:customer|client)\s+"
            r"(?:accounted\s+for|represented?)\s+(?:more\s+than\s+)?"
            r"(?:approximately\s+)?(\d+(?:\.\d+)?)\s*%"
        )
        match = re.search(no_conc_pat, text, re.IGNORECASE)
        if match:
            result.append(sourced_dict(
                {"customer": "No Major Customer",
                 "revenue_pct": 0.0,
                 "note": f"No customer > {match.group(1)}%"},
                source, Confidence.MEDIUM,
            ))
    return result


def _extract_suppliers(
    text: str, source: str
) -> list[SourcedValue[dict[str, str | float]]]:
    """Extract supplier concentration from filing text."""
    result: list[SourcedValue[dict[str, str | float]]] = []
    pct_pat = (
        r"(?:supplier|vendor)\s+\w*\s*(?:accounted?\s+for|represent(?:ed|s)?)\s+"
        r"(?:approximately\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?"
        r"(?:purchases|procurement|cost)"
    )
    for match in re.findall(pct_pat, text, re.IGNORECASE):
        result.append(sourced_dict(
            {"supplier": "Major Supplier", "cost_pct": float(match)},
            source, Confidence.MEDIUM,
        ))
    # Sole/single source dependency patterns.
    sole_patterns = [
        (r"(?:depend(?:s|ent)?|rel(?:y|ies))\s+on\s+(?:a\s+)?"
         r"(?:single|sole|limited)\s+(?:source|supplier|vendor)"),
        (r"(?:sourced|procured)\s+from\s+(?:a\s+)?"
         r"(?:single|sole|limited)\s+(?:source|supplier|vendor)s?"),
        (r"single[- ]source\s+(?:direct\s+)?supplier"),
    ]
    for pat in sole_patterns:
        if re.search(pat, text, re.IGNORECASE):
            result.append(sourced_dict(
                {"supplier": "Sole Source Dependency", "cost_pct": 0.0},
                source, Confidence.MEDIUM,
            ))
            break
    return result


# -----------------------------------------------------------------------
# SECT2-07: D&O exposure mapping (derived)
# -----------------------------------------------------------------------


def map_do_exposure(
    profile: CompanyProfile,
) -> list[SourcedValue[dict[str, str]]]:
    """Map business operations to D&O exposure factors (DERIVED/LOW)."""
    source = "derived:company_profile_analysis"
    factors: list[SourcedValue[dict[str, str]]] = []

    for cust in profile.customer_concentration:
        pct = cust.value.get("revenue_pct", 0)
        if isinstance(pct, (int, float)) and pct > 20:
            factors.append(sourced_str_dict(
                {"factor": "CUSTOMER_CONCENTRATION_RISK",
                 "reason": f"Customer >20% revenue ({pct}%)"},
                source, Confidence.LOW))
            break

    us_kw = {"united states", "delaware", "california"}
    non_us = sum(
        1 for g in profile.geographic_footprint
        if not any(kw in str(g.value.get("jurisdiction", "")).lower() for kw in us_kw)
    )
    total = len(profile.geographic_footprint)
    if total > 0 and non_us / total > 0.3:
        factors.append(sourced_str_dict(
            {"factor": "REGULATORY_MULTI_JURISDICTION",
             "reason": f"International ops ({non_us}/{total} non-US)"},
            source, Confidence.LOW))

    if profile.employee_count is not None and profile.employee_count.value > 10000:
        factors.append(sourced_str_dict(
            {"factor": "EMPLOYMENT_LITIGATION_RISK",
             "reason": f"Large workforce ({profile.employee_count.value:,})"},
            source, Confidence.LOW))

    if profile.identity.sector is not None and profile.identity.sector.value == "FINS":
        factors.append(sourced_str_dict(
            {"factor": "REGULATORY_SENSITIVE", "reason": "Financial services sector"},
            source, Confidence.LOW))

    ma_kw = {"acquisition", "acquired", "merger", "merged"}
    for change in profile.business_changes:
        if any(kw in change.value.lower() for kw in ma_kw):
            factors.append(sourced_str_dict(
                {"factor": "TRANSACTION_LITIGATION_RISK",
                 "reason": "Recent M&A activity detected"},
                source, Confidence.LOW))
            break

    if profile.identity.sector is not None and profile.identity.sector.value == "TECH":
        factors.append(sourced_str_dict(
            {"factor": "IP_LITIGATION_RISK", "reason": "Technology sector"},
            source, Confidence.LOW))

    return factors


# -----------------------------------------------------------------------
# SECT2-10: Event timeline
# -----------------------------------------------------------------------


def build_event_timeline(
    state: AnalysisState,
) -> list[SourcedValue[dict[str, str]]]:
    """Build chronological event timeline from 8-K LLM extractions and market data.

    Enriches generic 8-K filing entries with specific event descriptions
    from LLM extraction (restructuring, offerings, officer changes, etc.).
    """
    events: list[SourcedValue[dict[str, str]]] = []
    filings = get_filings(state)

    # Build lookup of 8-K LLM extractions by accession number
    llm_lookup: dict[str, dict[str, Any]] = {}
    if state.acquired_data is not None:
        llm_ext = state.acquired_data.llm_extractions or {}
        for key, val in llm_ext.items():
            if key.startswith("8-K:") and isinstance(val, dict):
                accession = key.split(":", 1)[1]
                llm_lookup[accession] = val

    eight_k_raw = filings.get("8-K")
    if isinstance(eight_k_raw, list):
        for f in cast(list[dict[str, str]], eight_k_raw):
            d = str(f.get("filing_date", ""))
            accession = str(f.get("accession_number", ""))

            # Try to get enriched description from LLM extraction
            llm_data = llm_lookup.get(accession, {})
            event_desc = _build_8k_event_description(llm_data, d)
            event_type = _classify_8k_event_type(llm_data)

            events.append(sourced_str_dict(
                {"date": d, "event": event_desc, "type": event_type},
                f"8-K {d}", Confidence.HIGH))

    info = get_info_dict(state)
    ft = info.get("firstTradeDateEpochUtc")
    if ft is not None and isinstance(ft, (int, float)):
        ipo_str = datetime.fromtimestamp(float(ft), tz=UTC).strftime("%Y-%m-%d")
        events.append(sourced_str_dict(
            {"date": ipo_str, "event": "First trade date / IPO", "type": "ipo"},
            "yfinance", Confidence.MEDIUM))

    events.sort(key=lambda e: e.value.get("date", ""))
    return events


def _build_8k_event_description(llm_data: dict[str, Any], filing_date: str) -> str:
    """Build a human-readable event description from 8-K LLM extraction."""
    if not llm_data:
        return f"8-K filing ({filing_date})"

    parts: list[str] = []

    # Officer departure/appointment
    dep = llm_data.get("departing_officer")
    if dep:
        title = llm_data.get("departing_officer_title") or ""
        reason = llm_data.get("departure_reason") or ""
        successor = llm_data.get("successor") or ""
        desc = f"{dep} ({title}) departing"
        if successor:
            desc += f"; {successor} succeeding"
        if reason:
            desc += f" — {reason[:100]}"
        parts.append(desc)

    # Restructuring
    restruct_type = llm_data.get("restructuring_type")
    if restruct_type:
        charge = llm_data.get("restructuring_charge")
        desc = llm_data.get("restructuring_description") or str(restruct_type)
        if charge:
            desc += f" (${charge / 1_000_000:.0f}M charge)" if isinstance(charge, (int, float)) and charge > 1_000_000 else f" (${charge})"
        parts.append(desc[:200])

    # Material agreement
    agreement = llm_data.get("agreement_summary")
    if agreement and not restruct_type:
        agr_type = llm_data.get("agreement_type") or ""
        counterparty = llm_data.get("counterparty", "")
        desc = f"{agr_type}: {agreement[:150]}" if agr_type else str(agreement)[:150]
        parts.append(desc)

    # Secondary offering / underwriting
    event_desc = llm_data.get("event_description") or ""
    if "offering" in event_desc.lower() or "underwriting" in str(llm_data.get("agreement_type") or "").lower():
        if event_desc and event_desc not in parts:
            parts.append(event_desc[:200])

    # Earnings results (lower priority — just note it)
    items = llm_data.get("items_covered", [])
    if "2.02" in items and not parts:
        parts.append("Quarterly earnings results")

    # Shareholder vote
    if "5.07" in items and not parts:
        ed = llm_data.get("event_description") or ""
        parts.append(ed[:200] if ed else "Annual meeting of stockholders")

    if parts:
        return "; ".join(parts)
    return f"8-K filing ({filing_date})"


def _classify_8k_event_type(llm_data: dict[str, Any]) -> str:
    """Classify 8-K event into a category for badge/icon rendering."""
    if not llm_data:
        return "material_event"

    items = llm_data.get("items_covered", [])
    if llm_data.get("restructuring_type"):
        return "restructuring"
    if llm_data.get("departing_officer"):
        return "officer_change"
    if "underwriting" in str(llm_data.get("agreement_type", "")).lower():
        return "offering"
    if "1.01" in items:
        return "agreement"
    if "2.02" in items:
        return "earnings"
    if "5.07" in items:
        return "shareholder_vote"
    return "material_event"


# -----------------------------------------------------------------------
# SECT2-11: Section summary (derived)
# -----------------------------------------------------------------------


def generate_section_summary(profile: CompanyProfile) -> SourcedValue[str]:
    """Generate a 2-3 sentence company profile summary (DERIVED/LOW)."""
    parts: list[str] = []

    name = profile.identity.legal_name.value if profile.identity.legal_name else ""
    industry = profile.industry_classification.value if profile.industry_classification else ""

    if name:
        parts.append(
            f"{name} operates in the {industry} industry." if industry
            else f"{name} is a publicly traded company."
        )

    size: list[str] = []
    if profile.employee_count is not None:
        size.append(f"{profile.employee_count.value:,} employees")
    if profile.market_cap is not None:
        size.append(f"${profile.market_cap.value / 1e9:.1f}B market cap")
    if size:
        parts.append(f"The company has {' and '.join(size)}.")

    if profile.do_exposure_factors:
        names = [str(f.value.get("factor", "")) for f in profile.do_exposure_factors]
        top = [n for n in names if n][:3]
        if top:
            parts.append(
                f"Key D&O exposure factors include: "
                f"{', '.join(n.replace('_', ' ').title() for n in top)}."
            )

    text = " ".join(parts) if parts else "Company profile data not available."
    return sourced_str(text, "derived:section_summary", Confidence.LOW)
