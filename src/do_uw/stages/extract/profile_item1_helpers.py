"""Item 1 text-based extraction helpers for company profile.

Revenue segment parsing from XBRL and text, operational complexity
detection (VIE, dual-class, SPE), and business changes extraction.
Split from company_profile.py to stay under 500-line limit.
"""

from __future__ import annotations

import re
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_texts,
    get_filings,
    now,
    sourced_dict,
    sourced_str,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

# ------------------------------------------------------------------
# Revenue segment helpers
# ------------------------------------------------------------------


def extract_revenue_segments(
    state: AnalysisState,
    facts_inner: dict[str, Any] | None,
) -> tuple[list[SourcedValue[dict[str, str | float]]], ExtractionReport]:
    """Extract revenue breakdown by segment from XBRL, then text fallback."""
    expected = ["revenue_segments"]
    found: list[str] = []
    warnings: list[str] = []
    fallbacks: list[str] = []
    src_filing = "SEC EDGAR Company Facts"

    segments: list[SourcedValue[dict[str, str | float]]] = []

    if isinstance(facts_inner, dict):
        us_gaap = facts_inner.get("us-gaap")
        if isinstance(us_gaap, dict):
            segments = _search_segment_data(
                cast(dict[str, Any], us_gaap), found,
            )

    # Fallback: parse segment revenue from 10-K Item 7 text.
    if not segments:
        text_segments = _extract_segments_from_text(state)
        if text_segments:
            segments = text_segments
            found.append("revenue_segments")
            fallbacks.append("10-K_item7_text_parsing")
            src_filing = "10-K Item 7 text"
        else:
            warnings.append(
                "No segment revenue data in XBRL or filing text; "
                "company may be single_segment_filer or not_disclosed"
            )

    return segments, create_report(
        extractor_name="revenue_segments", expected=expected,
        found=found, source_filing=src_filing, warnings=warnings,
        fallbacks_used=fallbacks,
    )


def _search_segment_data(
    us_gaap: dict[str, Any], found: list[str],
) -> list[SourcedValue[dict[str, str | float]]]:
    """Search US-GAAP data for segment revenue entries."""
    segments: list[SourcedValue[dict[str, str | float]]] = []
    tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues", "SalesRevenueNet",
    ]
    for tag in tags:
        concept_raw = us_gaap.get(tag)
        if not isinstance(concept_raw, dict):
            continue
        units_raw = cast(dict[str, Any], concept_raw).get("units")
        if not isinstance(units_raw, dict):
            continue
        usd_raw = cast(dict[str, Any], units_raw).get("USD")
        if not isinstance(usd_raw, list):
            continue
        entries = cast(list[dict[str, Any]], usd_raw)

        seg_entries = [
            e for e in entries
            if str(e.get("form", "")) == "10-K"
            and ("segment" in str(e.get("frame", "")).lower()
                 or _has_segment_dimension(e))
        ]
        if not seg_entries:
            continue

        fy_vals = [int(e.get("fy", 0)) for e in seg_entries if e.get("fy")]
        latest_fy = max(fy_vals, default=0)
        if latest_fy == 0:
            continue

        for entry in (e for e in seg_entries if int(e.get("fy", 0)) == latest_fy):
            name = _extract_segment_name(entry)
            val = entry.get("val", 0)
            if name and isinstance(val, (int, float)):
                segments.append(sourced_dict(
                    {"segment": name, "revenue": float(val)},
                    f"SEC EDGAR Company Facts {tag} FY{latest_fy}",
                    Confidence.HIGH,
                ))
        if segments:
            found.append("revenue_segments")
            break
    return segments


def _has_segment_dimension(entry: dict[str, Any]) -> bool:
    """Check if an XBRL entry has segment dimensional data.

    XBRL entries with segment breakdowns use various patterns:
    - frame contains "segment" (e.g., "CY2024_iPhoneSegment")
    - frame contains "Member" (e.g., "CY2024Q4_us-gaap_IPhoneMember")
    - frame has underscore-separated parts beyond the fiscal period
      (e.g., "CY2024_ProductLine_iPhone" vs plain "CY2024")
    """
    frame = str(entry.get("frame", ""))
    frame_lower = frame.lower()
    # Direct segment/member indicators
    if "segment" in frame_lower or "member" in frame_lower:
        return True
    # Multi-part frames often indicate dimensional data (e.g., CY2024_xxx)
    # but plain period frames like "CY2024" or "CY2024Q4" are aggregates
    parts = frame.split("_")
    if len(parts) >= 2:
        # Filter out simple period-only frames like "CY2024" or "CY2024Q4I"
        non_period = [p for p in parts if not re.match(r"^CY\d{4}(Q\d)?I?$", p)]
        if non_period:
            return True
    return False


def _extract_segment_name(entry: dict[str, Any]) -> str:
    """Extract human-readable segment name from XBRL entry.

    Handles patterns like:
    - "CY2024_iPhoneSegment" -> "iPhone"
    - "CY2024_us-gaap_IPhoneMember" -> "IPhone"
    - "CY2024_ProductLine_Services" -> "Services"
    """
    frame = str(entry.get("frame", ""))
    if "_" in frame:
        parts = frame.split("_")
        # Take the last meaningful part
        raw_name = parts[-1] if len(parts) >= 2 else ""
        if raw_name:
            # Strip common XBRL suffixes
            for suffix in ("Segment", "Member", "Domain"):
                if raw_name.endswith(suffix) and len(raw_name) > len(suffix):
                    raw_name = raw_name[: -len(suffix)]
            # Convert CamelCase to spaced: "GreaterChina" -> "Greater China"
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_name)
            # Handle all-caps like "IPad" -> keep as-is
            return spaced.strip()
    return str(entry.get("fp", ""))


def _extract_segments_from_text(
    state: AnalysisState,
) -> list[SourcedValue[dict[str, str | float]]]:
    """Parse segment revenue from 10-K Item 7 text (XBRL fallback)."""
    filing_texts = get_filing_texts(get_filings(state))
    item7 = str(filing_texts.get("10-K_item7", ""))
    if not item7:
        item7 = str(filing_texts.get("item7", ""))
    if not item7.strip():
        return []

    # Multiple regex patterns for different reporting styles:
    # Pattern 1: "Segment Name segment revenue $XX,XXX"
    # Pattern 2: "iPhone  $XX,XXX" (tabular format, AAPL-style)
    # Pattern 3: "Products $XX,XXX" / "Services $XX,XXX" (category format)
    patterns = [
        # Traditional "segment revenue" format
        re.compile(
            r"(?:total\s+)?"
            r"([\w&,\s]+?)"
            r"\s+segment\s+revenue"
            r"\s+\$?\s*([\d,]+)",
            re.IGNORECASE,
        ),
        # "Net sales by category/product:" table format
        # Matches lines like "iPhone    201,183" or "Services  96,169"
        re.compile(
            r"^\s*((?:iPhone|iPad|Mac|Wearables|Services|Products)"
            r"(?:[,\s]+Home\s+and\s+Accessories)?)"
            r"\s+\$?\s*([\d,]+)\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        # Generic "Category   $amount" after revenue heading
        re.compile(
            r"(?:net\s+sales|revenue)\s+by\s+(?:category|reportable\s+segment|"
            r"product\s+line|operating\s+segment)[:\s]*\n"
            r"(?:.*\n){0,5}"
            r"([\w&,\s]+?)\s+\$?\s*([\d,]+)",
            re.IGNORECASE,
        ),
    ]
    segments: list[SourcedValue[dict[str, str | float]]] = []
    seen_names: set[str] = set()
    for pat in patterns:
        for match in pat.finditer(item7):
            name = match.group(1).strip()
            val_str = match.group(2).replace(",", "")
            if not val_str:
                continue
            try:
                val = float(val_str)
            except ValueError:
                continue
            # Skip sub-totals and duplicates.
            name_key = name.lower()
            if name_key in seen_names or name_key in ("total", "total net sales"):
                continue
            seen_names.add(name_key)
            # Convert to full value if in millions (SEC filings typically
            # state amounts in millions at the top of the table).
            if val < 1_000_000:
                val = val * 1_000_000
            segments.append(sourced_dict(
                {"segment": name, "revenue": val},
                "10-K Item 7 text",
                Confidence.MEDIUM,
            ))
        if segments:
            break  # Stop at first pattern that finds results
    return segments


# ------------------------------------------------------------------
# Operational complexity detection
# ------------------------------------------------------------------


def extract_operational_complexity(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Detect VIE, dual-class, and SPE indicators in filing text."""
    filing_texts = get_filing_texts(get_filings(state))
    expected = ["vie_flag", "dual_class_flag", "spe_flag"]
    source = "10-K text analysis"

    combined = " ".join(
        str(filing_texts.get(k, ""))
        for k in ("10-K_item1", "10-K_item7", "item1", "item7")
    ).lower()

    complexity: dict[str, Any] = {
        "has_vie": False, "has_dual_class": False, "has_spe": False,
    }

    if "variable interest" in combined:
        complexity["has_vie"] = True

    for pat in (r"class\s+[ab]\s+common\s+stock", r"dual[- ]class",
                r"supervoting", r"class\s+[ab]\s+share"):
        if re.search(pat, combined):
            complexity["has_dual_class"] = True
            break

    for phrase in ("special purpose entit", "special purpose vehicle",
                   "structured investment vehicle"):
        if phrase in combined:
            complexity["has_spe"] = True
            break

    # Always report all flags as "found" -- confirming absence is a finding.
    found = list(expected)

    result: SourcedValue[dict[str, Any]] | None = None
    if combined.strip():
        # We have text to analyze; always produce a result (even all-False).
        result = SourcedValue[dict[str, Any]](
            value=complexity, source=source,
            confidence=Confidence.MEDIUM, as_of=now(),
        )
    return result, create_report(
        extractor_name="operational_complexity", expected=expected,
        found=found, source_filing=source,
    )


# ------------------------------------------------------------------
# Business changes detection
# ------------------------------------------------------------------


def extract_business_changes(
    state: AnalysisState,
) -> tuple[list[SourcedValue[str]], ExtractionReport]:
    """Detect acquisitions, divestitures, restructurings."""
    filings = get_filings(state)
    found: list[str] = []
    changes: list[SourcedValue[str]] = []

    eight_k_raw = filings.get("8-K")
    if isinstance(eight_k_raw, list):
        for filing in cast(list[dict[str, str]], eight_k_raw):
            date = str(filing.get("filing_date", ""))
            ftype = str(filing.get("form_type", "8-K"))
            changes.append(sourced_str(
                f"8-K filed {date}", f"{ftype} {date}", Confidence.HIGH,
            ))

    filing_texts = get_filing_texts(filings)
    combined = " ".join(
        str(filing_texts.get(k, ""))
        for k in ("10-K_item1", "10-K_item7", "item1", "item7")
    )

    # Detect M&A activity keywords and summarize (not individual keyword dumps)
    _ma_keywords_found = [
        kw for kw in ("acquisition", "merger", "divestiture", "restructuring",
                       "discontinued operations")
        if kw in combined.lower()
    ]
    if _ma_keywords_found:
        changes.append(sourced_str(
            f"M&A activity indicated ({', '.join(_ma_keywords_found)})",
            "10-K text analysis",
            Confidence.MEDIUM,
        ))

    if changes:
        found.append("business_changes")

    return changes, create_report(
        extractor_name="business_changes", expected=["business_changes"],
        found=found, source_filing="8-K filings + 10-K text",
    )
