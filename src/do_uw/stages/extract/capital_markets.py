"""Capital markets activity extraction (SECT4-08).

Identifies shelf registrations, offerings, and convertible securities
from SEC filing metadata to assess Section 11 liability exposure.

Section 11 of the Securities Act of 1933 creates strict liability for
material misstatements in registration statements. The statute of
limitations is 3 years from the offering date, making recent offerings
a critical D&O risk factor.

Usage:
    activity, report = extract_capital_markets(state)
    state.extracted.market.capital_markets = activity
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import (
    CapitalMarketsActivity,
    CapitalMarketsOffering,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filings,
    now,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Source attribution constant.
_SEC_FILINGS = "SEC filing metadata"

# Section 11 statute of limitations: 3 years from offering.
_SECTION_11_YEARS = 3

# Filing types that indicate capital markets activity.
_OFFERING_FORM_TYPES: set[str] = {
    "S-1",
    "S-1/A",
    "S-3",
    "S-3/A",
    "S-3ASR",
    "F-1",
    "F-1/A",
    "F-3",
    "F-3/A",
    "F-3ASR",
    "424B1",
    "424B2",
    "424B3",
    "424B4",
    "424B5",
}

# Filing types that suggest ATM (at-the-market) programs.
_ATM_INDICATORS: set[str] = {"S-3ASR", "F-3ASR", "424B5"}

# Filing types associated with convertible securities.
_CONVERTIBLE_INDICATORS: set[str] = {"424B2", "424B3"}

# Expected fields for extraction report.
EXPECTED_FIELDS: list[str] = [
    "offerings",
    "active_section_11_windows",
    "has_atm_program",
    "convertible_securities",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string (YYYY-MM-DD) to datetime, or None."""
    try:
        cleaned = date_str.strip().split("T")[0]
        parts = cleaned.split("-")
        if len(parts) >= 3:
            return datetime(
                int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=UTC
            )
    except (ValueError, IndexError):
        pass
    return None


def compute_section_11_end(filing_date: str) -> str:
    """Compute Section 11 window end date (filing_date + 3 years).

    Returns YYYY-MM-DD string, or empty string if date is unparseable.
    """
    dt = _parse_date(filing_date)
    if dt is None:
        return ""
    try:
        end = dt.replace(year=dt.year + _SECTION_11_YEARS)
    except ValueError:
        # Handle Feb 29 in leap year.
        end = dt.replace(
            year=dt.year + _SECTION_11_YEARS, month=3, day=1
        )
    return end.strftime("%Y-%m-%d")


def _classify_offering_type(form_type: str) -> str:
    """Classify offering type from SEC form type."""
    ft = form_type.upper()
    if ft.startswith("S-1") or ft.startswith("F-1"):
        return "IPO"
    if ft in {"S-3ASR", "F-3ASR"}:
        return "SHELF_ATM"
    if ft.startswith("S-3") or ft.startswith("F-3"):
        return "SHELF"
    if ft.startswith("424B"):
        return "PROSPECTUS_SUPPLEMENT"
    return "OTHER"


def is_window_active(section_11_end: str) -> bool:
    """Check whether the Section 11 window is still open."""
    end_dt = _parse_date(section_11_end)
    if end_dt is None:
        return False
    return end_dt > datetime.now(tz=UTC)


def _build_offering(
    form_type: str,
    filing_date: str,
    accession: str,
) -> CapitalMarketsOffering:
    """Build a CapitalMarketsOffering from filing metadata."""
    offering_type = _classify_offering_type(form_type)
    section_11_end = compute_section_11_end(filing_date)

    source = f"{form_type} {filing_date} {accession}"

    return CapitalMarketsOffering(
        offering_type=offering_type,
        filing_type=form_type,
        date=sourced_str(filing_date, source, Confidence.HIGH),
        section_11_window_end=section_11_end,
    )


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def extract_capital_markets(
    state: AnalysisState,
) -> tuple[CapitalMarketsActivity, ExtractionReport]:
    """Extract capital markets activity from SEC filings (SECT4-08).

    Reads filing metadata from state.acquired_data.filings, identifies
    offering-related filings, and computes Section 11 windows.

    Args:
        state: Analysis state with acquired filing data.

    Returns:
        Tuple of (CapitalMarketsActivity, ExtractionReport).
    """
    filings = get_filings(state)
    found_fields: list[str] = []
    warnings: list[str] = []

    activity = CapitalMarketsActivity()

    # Collect all offering filings from recent filings list.
    # The filings dict may have a "recent" key with filing metadata.
    offerings: list[CapitalMarketsOffering] = []
    shelves: list[CapitalMarketsOffering] = []
    convertibles: list[CapitalMarketsOffering] = []
    has_atm = False

    # Check multiple locations where filing metadata could be stored.
    filing_list = _extract_filing_list(filings)

    for filing_meta in filing_list:
        form_type = str(filing_meta.get("form_type", "")).strip()
        if form_type.upper() not in _OFFERING_FORM_TYPES:
            continue

        filing_date = str(filing_meta.get("filing_date", ""))
        accession = str(filing_meta.get("accession", ""))

        offering = _build_offering(form_type, filing_date, accession)
        offerings.append(offering)

        # Classify into sub-lists.
        ft_upper = form_type.upper()
        if ft_upper.startswith(("S-3", "F-3", "S-1", "F-1")):
            shelves.append(offering)
        if ft_upper in _ATM_INDICATORS:
            has_atm = True
        if ft_upper in _CONVERTIBLE_INDICATORS:
            convertibles.append(offering)

    if offerings:
        activity.offerings_3yr = offerings
        activity.shelf_registrations = shelves
        found_fields.append("offerings")

        # Compute active Section 11 windows.
        active_count = sum(
            1
            for o in offerings
            if is_window_active(o.section_11_window_end)
        )
        activity.active_section_11_windows = active_count
        found_fields.append("active_section_11_windows")
    else:
        activity.active_section_11_windows = 0
        found_fields.append("active_section_11_windows")
        warnings.append("No offering-related filings found")

    # ATM program detection.
    activity.has_atm_program = SourcedValue[bool](
        value=has_atm,
        source=_SEC_FILINGS,
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )
    found_fields.append("has_atm_program")

    # Convertible securities.
    activity.convertible_securities = convertibles
    found_fields.append("convertible_securities")

    report = create_report(
        extractor_name="capital_markets",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=_SEC_FILINGS,
        warnings=warnings,
    )
    log_report(report)
    return activity, report


def _extract_filing_list(
    filings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract a flat list of filing metadata dicts.

    Filing metadata may be stored in different places depending on
    what the ACQUIRE stage collected. Tries multiple locations.
    """
    result: list[dict[str, Any]] = []

    # Try 'recent' key (submissions API format).
    recent_raw = filings.get("recent")
    if isinstance(recent_raw, dict):
        recent = cast(dict[str, Any], recent_raw)
        # submissions API returns parallel arrays.
        forms = cast(list[str], recent.get("form", []))
        dates = cast(list[str], recent.get("filingDate", []))
        accessions = cast(list[str], recent.get("accessionNumber", []))
        for i in range(len(forms)):
            entry: dict[str, Any] = {
                "form_type": forms[i] if i < len(forms) else "",
                "filing_date": (
                    dates[i] if i < len(dates) else ""
                ),
                "accession": (
                    accessions[i] if i < len(accessions) else ""
                ),
            }
            result.append(entry)

    # Try 'filing_list' key (alternative storage format).
    filing_list_raw = filings.get("filing_list")
    if isinstance(filing_list_raw, list):
        filing_list = cast(list[Any], filing_list_raw)
        for item in filing_list:
            if isinstance(item, dict):
                result.append(cast(dict[str, Any], item))

    # Try individual form-type keys from filing_documents.
    filing_docs_raw = filings.get("filing_documents")
    if isinstance(filing_docs_raw, dict):
        filing_docs = cast(dict[str, Any], filing_docs_raw)
        for form_type_key, docs_raw in filing_docs.items():
            if isinstance(docs_raw, list):
                docs = cast(list[dict[str, Any]], docs_raw)
                for doc in docs:
                    doc_entry: dict[str, Any] = {
                        "form_type": str(form_type_key),
                        "filing_date": str(doc.get("filing_date", "")),
                        "accession": str(doc.get("accession", "")),
                    }
                    result.append(doc_entry)

    return result
