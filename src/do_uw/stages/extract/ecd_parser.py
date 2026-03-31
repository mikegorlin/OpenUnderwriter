"""Parse inline XBRL ECD (Executive Compensation Disclosure) tags from DEF 14A.

Since the 2022 SEC mandate, DEF 14A proxy statements contain inline XBRL
tags in the ``ecd:`` namespace with structured compensation and governance
data. Parsing these directly yields HIGH confidence data — no LLM needed.

Covers:
- Pay-vs-Performance table (CEO comp, NEO avg comp, TSR, peer TSR)
- Insider trading policy disclosure
- Award timing flags (MNPI consideration, predetermined schedule)
- Company-selected performance measure

Usage:
    from do_uw.stages.extract.ecd_parser import extract_ecd_from_proxy

    ecd, report = extract_ecd_from_proxy(state)
    gov.ecd = ecd
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_documents,
    now,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "ceo_name",
    "ceo_total_comp",
    "ceo_comp_actually_paid",
    "neo_avg_total_comp",
    "neo_avg_comp_actually_paid",
    "company_tsr",
    "peer_group_tsr",
    "company_selected_measure_name",
    "company_selected_measure_amt",
    "insider_trading_policy",
    "award_timing_mnpi_considered",
    "award_timing_predetermined",
]

# ---------------------------------------------------------------------------
# Regex patterns for inline XBRL tags
# ---------------------------------------------------------------------------

# ix:nonFraction — numeric values (compensation amounts, TSR, etc.)
_NONFRACTION_RE = re.compile(
    r'<ix:nonFraction[^>]*\bname="ecd:(\w+)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonFraction>",
    re.IGNORECASE | re.DOTALL,
)

# ix:nonNumeric — text values (names, flags, measure names)
_NONNUMERIC_RE = re.compile(
    r'<ix:nonNumeric[^>]*\bname="ecd:(\w+)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonNumeric>",
    re.IGNORECASE | re.DOTALL,
)

# contextRef extraction for multi-year disambiguation
_CONTEXTREF_NONFRACTION_RE = re.compile(
    r'<ix:nonFraction[^>]*\bcontextRef="([^"]*)"[^>]*\bname="ecd:(\w+)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonFraction>",
    re.IGNORECASE | re.DOTALL,
)

_CONTEXTREF_NONNUMERIC_RE = re.compile(
    r'<ix:nonNumeric[^>]*\bcontextRef="([^"]*)"[^>]*\bname="ecd:(\w+)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonNumeric>",
    re.IGNORECASE | re.DOTALL,
)

# Also handle contextRef appearing after name= (tag attribute order varies)
_NONFRACTION_ALT_RE = re.compile(
    r'<ix:nonFraction[^>]*\bname="ecd:(\w+)"[^>]*\bcontextRef="([^"]*)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonFraction>",
    re.IGNORECASE | re.DOTALL,
)

_NONNUMERIC_ALT_RE = re.compile(
    r'<ix:nonNumeric[^>]*\bname="ecd:(\w+)"[^>]*\bcontextRef="([^"]*)"[^>]*>'
    r"([^<]*)"
    r"</ix:nonNumeric>",
    re.IGNORECASE | re.DOTALL,
)

# ECD concept-to-field mapping
_CONCEPT_MAP: dict[str, str] = {
    "PeoTotalCompAmt": "ceo_total_comp",
    "PeoActuallyPaidCompAmt": "ceo_comp_actually_paid",
    "NonPeoNeoAvgTotalCompAmt": "neo_avg_total_comp",
    "NonPeoNeoAvgCompActuallyPaidAmt": "neo_avg_comp_actually_paid",
    "TotalShareholderRtnAmt": "company_tsr",
    "PeerGroupTotalShareholderRtnAmt": "peer_group_tsr",
    "CompActuallyPaidVsTotalShareholderRtnTextBlock": "_unused",
    "CoSelectedMeasureAmt": "company_selected_measure_amt",
}

_TEXT_CONCEPT_MAP: dict[str, str] = {
    "PeoName": "ceo_name",
    "CoSelectedMeasureName": "company_selected_measure_name",
    "InsiderTrdPoliciesProcAdoptedFlag": "insider_trading_policy",
    "AwardTmgMnpiCnsdrdFlag": "award_timing_mnpi_considered",
    "AwardTmgPredtrmndFlag": "award_timing_predetermined",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class ECDYearData:
    """ECD data for a single fiscal year."""

    __slots__ = (
        "year",
        "ceo_total_comp",
        "ceo_comp_actually_paid",
        "neo_avg_total_comp",
        "neo_avg_comp_actually_paid",
        "company_tsr",
        "peer_group_tsr",
        "company_selected_measure_amt",
    )

    def __init__(self, year: str) -> None:
        self.year = year
        self.ceo_total_comp: float | None = None
        self.ceo_comp_actually_paid: float | None = None
        self.neo_avg_total_comp: float | None = None
        self.neo_avg_comp_actually_paid: float | None = None
        self.company_tsr: float | None = None
        self.peer_group_tsr: float | None = None
        self.company_selected_measure_amt: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict, omitting None values."""
        result: dict[str, Any] = {"year": self.year}
        for attr in self.__slots__:
            if attr == "year":
                continue
            val = getattr(self, attr)
            if val is not None:
                result[attr] = val
        return result


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_numeric(raw: str) -> float | None:
    """Parse a numeric value from inline XBRL text content.

    Handles commas, whitespace, negative signs, and parenthetical negatives.
    Returns None if the value cannot be parsed.
    """
    cleaned = raw.strip()
    if not cleaned:
        return None

    # Remove HTML entities that might remain
    cleaned = re.sub(r"&[a-zA-Z]+;", "", cleaned)
    cleaned = re.sub(r"&#\d+;", "", cleaned)

    # Handle parenthetical negatives: (1,234) → -1234
    paren_match = re.match(r"\(([^)]+)\)", cleaned)
    if paren_match:
        cleaned = "-" + paren_match.group(1)

    # Remove $ and commas
    cleaned = cleaned.replace("$", "").replace(",", "").strip()

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_bool_flag(raw: str) -> bool | None:
    """Parse a boolean flag from inline XBRL text.

    ECD flags use ``true``/``false`` or ``Yes``/``No``.
    """
    val = raw.strip().lower()
    if val in ("true", "yes"):
        return True
    if val in ("false", "no"):
        return False
    return None


def _extract_year_from_context(context_ref: str) -> str | None:
    """Extract fiscal year from a contextRef string.

    Common patterns:
    - ``C_0001308179_20240928_20250927`` → "2025" (end date year)
    - ``FY2024`` → "2024"
    - ``ecd_PvpTable_2024`` → "2024"
    """
    # Try 4-digit year at end of date range (YYYYMMDD_YYYYMMDD)
    date_match = re.search(r"_(\d{4})\d{4}$", context_ref)
    if date_match:
        return date_match.group(1)

    # Try standalone year
    year_match = re.search(r"(?:FY|_)(\d{4})(?:_|$)", context_ref)
    if year_match:
        return year_match.group(1)

    # Try any 4-digit year between 2020-2030
    any_year = re.findall(r"(20[2-3]\d)", context_ref)
    if any_year:
        return any_year[-1]  # Use the latest year found

    return None


def _get_raw_filing_html(state: AnalysisState) -> tuple[str, str]:
    """Get raw DEF 14A HTML (with inline XBRL tags intact).

    The filing_documents store HTML-stripped plain text, but the ECD
    parser needs the raw HTML with <ix:nonFraction> and <ix:nonNumeric>
    tags. We fetch directly from SEC EDGAR using the primary document
    URL stored in the filing metadata.
    """
    # Get the most recent DEF 14A filing metadata (has URL, accession)
    filings: dict[str, object] = {}
    if state.acquired_data is not None:
        filings = state.acquired_data.filings or {}
    proxy_filings = filings.get("DEF 14A", [])
    if not proxy_filings or not isinstance(proxy_filings, list):
        return "", ""

    filing = proxy_filings[0]
    if not isinstance(filing, dict):
        return "", ""

    accession = str(filing.get("accession_number", filing.get("accn", "")))
    primary_url = str(filing.get("primary_doc_url", ""))

    if primary_url:
        # Fetch raw HTML directly from SEC EDGAR
        try:
            from do_uw.stages.acquire.rate_limiter import sec_get_text

            logger.info("ECD: Fetching raw HTML for DEF 14A: %s", primary_url)
            raw_html = sec_get_text(primary_url)
            if raw_html and "<ix:" in raw_html:
                logger.info(
                    "ECD: Got %d chars of raw HTML with inline XBRL tags",
                    len(raw_html),
                )
                return raw_html, accession
            logger.info("ECD: Raw HTML has no inline XBRL tags")
        except Exception:
            logger.warning("ECD: Failed to fetch raw HTML", exc_info=True)

    # Fallback: stripped text from filing_documents (won't have XBRL tags)
    docs = get_filing_documents(state)
    proxy_docs = docs.get("DEF 14A", [])
    if proxy_docs and isinstance(proxy_docs[0], dict):
        return str(proxy_docs[0].get("full_text", "")), accession
    return "", accession


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def parse_ecd_tags(html_text: str) -> dict[str, Any]:
    """Parse all ECD inline XBRL tags from HTML text.

    Returns a flat dict with the most recent year's numeric values
    plus text/flag values. Also includes ``pvp_table`` with multi-year
    data when available.

    Args:
        html_text: Raw HTML text from DEF 14A filing.

    Returns:
        Dict with extracted ECD values.
    """
    if not html_text:
        return {}

    result: dict[str, Any] = {}
    year_data: dict[str, ECDYearData] = {}

    # --- Extract numeric values (nonFraction) ---

    # Try contextRef patterns first (for multi-year disambiguation)
    numeric_with_context: list[tuple[str, str, str]] = []

    for match in _CONTEXTREF_NONFRACTION_RE.finditer(html_text):
        ctx, concept, value = match.group(1), match.group(2), match.group(3)
        numeric_with_context.append((ctx, concept, value))

    for match in _NONFRACTION_ALT_RE.finditer(html_text):
        concept, ctx, value = match.group(1), match.group(2), match.group(3)
        numeric_with_context.append((ctx, concept, value))

    # Deduplicate by (context, concept)
    seen_numeric: set[tuple[str, str]] = set()
    for ctx, concept, value in numeric_with_context:
        key = (ctx, concept)
        if key in seen_numeric:
            continue
        seen_numeric.add(key)

        field = _CONCEPT_MAP.get(concept)
        if not field or field == "_unused":
            continue

        parsed = _parse_numeric(value)
        if parsed is None:
            continue

        year = _extract_year_from_context(ctx)
        if year:
            if year not in year_data:
                year_data[year] = ECDYearData(year)
            setattr(year_data[year], field, parsed)

    # Fallback: simple nonFraction without context tracking
    if not year_data:
        for match in _NONFRACTION_RE.finditer(html_text):
            concept, value = match.group(1), match.group(2)
            field = _CONCEPT_MAP.get(concept)
            if not field or field == "_unused":
                continue
            parsed = _parse_numeric(value)
            if parsed is not None:
                result[field] = parsed

    # --- Extract text/flag values (nonNumeric) ---

    # Collect all text values (flags + names)
    text_values: dict[str, list[str]] = {}

    for match in _NONNUMERIC_RE.finditer(html_text):
        concept, value = match.group(1), match.group(2)
        field = _TEXT_CONCEPT_MAP.get(concept)
        if field:
            text_values.setdefault(field, []).append(value.strip())

    for match in _NONNUMERIC_ALT_RE.finditer(html_text):
        concept, _ctx, value = match.group(1), match.group(2), match.group(3)
        field = _TEXT_CONCEPT_MAP.get(concept)
        if field:
            text_values.setdefault(field, []).append(value.strip())

    # Process text values
    for field, values in text_values.items():
        if not values:
            continue
        # For names, take the first non-empty value
        # For boolean flags, parse
        if field in (
            "insider_trading_policy",
            "award_timing_mnpi_considered",
            "award_timing_predetermined",
        ):
            for v in values:
                parsed_bool = _parse_bool_flag(v)
                if parsed_bool is not None:
                    result[field] = parsed_bool
                    break
        else:
            # Take first non-empty value
            for v in values:
                if v:
                    result[field] = v
                    break

    # --- Assemble multi-year PvP table ---
    if year_data:
        sorted_years = sorted(year_data.keys(), reverse=True)
        pvp_table = [year_data[y].to_dict() for y in sorted_years]
        result["pvp_table"] = pvp_table

        # Populate top-level with most recent year
        latest = year_data[sorted_years[0]]
        for attr in ECDYearData.__slots__:
            if attr == "year":
                continue
            val = getattr(latest, attr)
            if val is not None:
                result[attr] = val

    return result


def extract_ecd_from_proxy(
    state: AnalysisState,
) -> tuple[dict[str, Any], ExtractionReport]:
    """Extract ECD inline XBRL data from the DEF 14A filing.

    This is the main entry point for the ECD parser. It reads the raw
    HTML from the most recent DEF 14A filing, parses ECD tags, and
    returns structured data with HIGH confidence sourcing.

    Args:
        state: Pipeline state with acquired DEF 14A filing.

    Returns:
        Tuple of (ecd_data dict, ExtractionReport).
    """
    html_text, accession = _get_raw_filing_html(state)
    source = f"DEF 14A XBRL (accn:{accession})" if accession else "DEF 14A XBRL"

    if not html_text:
        logger.warning("ECD: No DEF 14A text available for XBRL parsing")
        report = create_report(
            extractor_name="ecd_xbrl",
            expected=EXPECTED_FIELDS,
            found=[],
            source_filing="DEF 14A (not available)",
        )
        log_report(report)
        return {}, report

    # Check for ECD namespace presence
    has_ecd = "ecd:" in html_text.lower() or "ecd:" in html_text
    if not has_ecd:
        logger.info("ECD: No ecd: namespace found in DEF 14A — pre-2022 filing?")
        report = create_report(
            extractor_name="ecd_xbrl",
            expected=EXPECTED_FIELDS,
            found=[],
            source_filing=source,
            warnings=["No ecd: namespace in filing (pre-2022 or non-inline XBRL)"],
        )
        log_report(report)
        return {}, report

    # Parse tags
    raw_ecd = parse_ecd_tags(html_text)

    if not raw_ecd:
        logger.warning("ECD: ecd: namespace present but no tags parsed")
        report = create_report(
            extractor_name="ecd_xbrl",
            expected=EXPECTED_FIELDS,
            found=[],
            source_filing=source,
            warnings=["ecd: namespace present but no matching tags found"],
        )
        log_report(report)
        return {}, report

    # Build sourced result dict
    ecd_data: dict[str, Any] = {
        "source": source,
        "confidence": "HIGH",
    }
    found_fields: list[str] = []

    # Map parsed values to sourced output
    if "ceo_name" in raw_ecd:
        ecd_data["ceo_name"] = sourced_str(
            raw_ecd["ceo_name"], source, Confidence.HIGH
        )
        found_fields.append("ceo_name")

    for float_field in [
        "ceo_total_comp",
        "ceo_comp_actually_paid",
        "neo_avg_total_comp",
        "neo_avg_comp_actually_paid",
        "company_tsr",
        "peer_group_tsr",
        "company_selected_measure_amt",
    ]:
        if float_field in raw_ecd:
            ecd_data[float_field] = sourced_float(
                raw_ecd[float_field], source, Confidence.HIGH
            )
            found_fields.append(float_field)

    if "company_selected_measure_name" in raw_ecd:
        ecd_data["company_selected_measure_name"] = sourced_str(
            raw_ecd["company_selected_measure_name"], source, Confidence.HIGH
        )
        found_fields.append("company_selected_measure_name")

    for bool_field in [
        "insider_trading_policy",
        "award_timing_mnpi_considered",
        "award_timing_predetermined",
    ]:
        if bool_field in raw_ecd:
            ecd_data[bool_field] = SourcedValue[bool](
                value=raw_ecd[bool_field],
                source=source,
                confidence=Confidence.HIGH,
                as_of=now(),
            )
            found_fields.append(bool_field)

    # Include PvP table if present (multi-year data)
    if "pvp_table" in raw_ecd:
        ecd_data["pvp_table"] = raw_ecd["pvp_table"]

    logger.info(
        "ECD: Extracted %d/%d fields from inline XBRL (%s)",
        len(found_fields),
        len(EXPECTED_FIELDS),
        source,
    )

    report = create_report(
        extractor_name="ecd_xbrl",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=source,
    )
    log_report(report)

    return ecd_data, report


def merge_ecd_into_compensation(
    ecd_data: dict[str, Any],
    comp: Any,
) -> None:
    """Merge ECD XBRL data into CompensationAnalysis, preferring XBRL over LLM.

    XBRL data is HIGH confidence (machine-parsed from structured tags),
    while LLM extraction is MEDIUM. When both exist, XBRL wins.

    Args:
        ecd_data: ECD dict from extract_ecd_from_proxy.
        comp: CompensationAnalysis model instance.
    """
    if not ecd_data:
        return

    # CEO total comp — XBRL overrides LLM if present
    ceo_comp = ecd_data.get("ceo_total_comp")
    if isinstance(ceo_comp, SourcedValue) and (
        comp.ceo_total_comp is None
        or comp.ceo_total_comp.confidence != Confidence.HIGH
    ):
        comp.ceo_total_comp = ceo_comp
        logger.debug("ECD→Comp: ceo_total_comp upgraded to HIGH via XBRL")

    # CEO pay ratio cannot be derived from ECD directly (need median worker)
    # but if we have CEO total comp from XBRL it improves the ratio calculation

    # Say-on-pay is not in ECD — it's in proxy voting results section
    # Clawback is not in ECD — it's a separate disclosure

    # The PvP table gives us comp-actually-paid which is a D&O risk signal
    # (large gap between total comp and actually-paid suggests realizable pay issues)
