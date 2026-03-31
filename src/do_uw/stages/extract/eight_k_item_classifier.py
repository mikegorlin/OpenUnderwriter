"""8-K Item number classifier and D&O severity tagger.

Parses raw 8-K filing text for structured "Item X.XX" patterns, classifies
each item by D&O relevance, and aggregates across all 8-K filings for a
company. This is a deterministic extractor (no LLM) that complements the
LLM-based EightKExtraction by providing reliable item identification
directly from the filing text.

Public function:
- classify_eight_k_filings(state) -> EightKItemSummary
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from do_uw.models.market import EightKFiling, EightKItemSummary
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 8-K Item definitions with D&O relevance
# ---------------------------------------------------------------------------

# Maps item number -> (title, D&O severity).
# Severity: CRITICAL = near-certain litigation trigger,
#           HIGH = significant D&O exposure indicator,
#           MEDIUM = material event with potential D&O implications,
#           LOW = routine disclosure, minimal D&O relevance.
ITEM_CATALOG: dict[str, tuple[str, str]] = {
    "1.01": ("Entry into Material Definitive Agreement", "MEDIUM"),
    "1.02": ("Termination of Material Definitive Agreement", "HIGH"),
    "1.03": ("Bankruptcy or Receivership", "CRITICAL"),
    "1.04": ("Mine Safety - Reporting of Shutdowns and Patterns of Violations", "LOW"),
    "2.01": ("Completion of Acquisition or Disposition of Assets", "MEDIUM"),
    "2.02": ("Results of Operations and Financial Condition", "MEDIUM"),
    "2.03": ("Creation of Direct Financial Obligation", "MEDIUM"),
    "2.04": ("Triggering Events That Accelerate Obligations", "HIGH"),
    "2.05": ("Costs Associated with Exit or Disposal Activities", "HIGH"),
    "2.06": ("Material Impairments", "HIGH"),
    "3.01": ("Notice of Delisting or Failure to Satisfy Listing Rule", "CRITICAL"),
    "3.02": ("Unregistered Sales of Equity Securities", "MEDIUM"),
    "3.03": ("Material Modification to Rights of Security Holders", "HIGH"),
    "4.01": ("Changes in Registrant's Certifying Accountant", "CRITICAL"),
    "4.02": ("Non-Reliance on Previously Issued Financial Statements", "CRITICAL"),
    "5.01": ("Changes in Control of Registrant", "HIGH"),
    "5.02": ("Departure of Directors or Certain Officers", "HIGH"),
    "5.03": ("Amendments to Articles of Incorporation or Bylaws", "MEDIUM"),
    "5.04": ("Temporary Suspension of Trading Under Employee Benefit Plans", "MEDIUM"),
    "5.05": ("Amendment to Code of Ethics or Waiver", "HIGH"),
    "5.06": ("Change in Shell Company Status", "LOW"),
    "5.07": ("Submission of Matters to a Vote of Security Holders", "LOW"),
    "5.08": ("Shareholder Nominations Pursuant to Exchange Act Rule 14a-11", "LOW"),
    "7.01": ("Regulation FD Disclosure", "LOW"),
    "8.01": ("Other Events", "LOW"),
    "9.01": ("Financial Statements and Exhibits", "LOW"),
}

# Items that are D&O-critical: high likelihood of triggering litigation
# or representing material governance/financial risk.
DO_CRITICAL_ITEMS: set[str] = {
    "1.02",  # Termination of material agreement
    "1.03",  # Bankruptcy
    "2.04",  # Triggering events
    "2.05",  # Restructuring/exit costs
    "2.06",  # Material impairments
    "3.01",  # Delisting notice
    "3.03",  # Modification to shareholder rights
    "4.01",  # Auditor change
    "4.02",  # Restatement / non-reliance
    "5.01",  # Change in control
    "5.02",  # Officer/director departure
    "5.05",  # Code of ethics change/waiver
}

# Severity ranking for determining highest severity across items.
_SEVERITY_RANK: dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


# ---------------------------------------------------------------------------
# Regex pattern for "Item X.XX" in 8-K text
# ---------------------------------------------------------------------------

# Matches patterns like:
#   "Item 2.02" or "ITEM 2.02" or "Item  2.02" (extra whitespace)
#   Also handles "Item 2.02." with trailing period
#   Captures just the number part (e.g., "2.02")
_ITEM_PATTERN = re.compile(
    r"\bItem\s+(\d+\.\d{2})\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_eight_k_filings(state: AnalysisState) -> EightKItemSummary:
    """Parse and classify all 8-K filings from acquired data.

    Reads raw 8-K filing text from ``state.acquired_data.filing_documents``
    and LLM extraction results from ``state.acquired_data.llm_extractions``.
    Combines regex-parsed items with LLM-extracted ``items_covered`` for
    comprehensive coverage.

    Args:
        state: Pipeline state after ACQUIRE and LLM extraction.

    Returns:
        EightKItemSummary with parsed items, frequencies, and D&O flags.
    """
    if state.acquired_data is None:
        return EightKItemSummary()

    filings: list[EightKFiling] = []
    item_counter: Counter[str] = Counter()

    # Source 1: Raw filing text from filing_documents
    raw_filings = state.acquired_data.filing_documents.get("8-K", [])
    for doc in raw_filings:
        filing = _classify_single_filing(doc)
        if filing.items:
            filings.append(filing)
            item_counter.update(filing.items)

    # Source 2: LLM extraction results (may have items_covered)
    llm_items = _collect_llm_items(state)
    for accession, llm_filing in llm_items.items():
        # Check if we already have this filing from raw text
        existing = next((f for f in filings if f.accession == accession), None)
        if existing is not None:
            # Merge LLM items into existing filing
            _merge_items(existing, llm_filing)
            # Update counter for new items
            for item in llm_filing.items:
                if item not in existing.items:
                    item_counter[item] += 1
        else:
            filings.append(llm_filing)
            item_counter.update(llm_filing.items)

    # Source 3: Filing metadata from filings dict (may have item info)
    metadata_filings = state.acquired_data.filings.get("8-K", [])
    _merge_metadata_items(filings, metadata_filings, item_counter)

    # Sort filings by date descending (most recent first)
    filings.sort(key=lambda f: f.filing_date, reverse=True)

    # Build summary
    summary = EightKItemSummary(
        filings=filings,
        total_filings=len(filings),
        item_frequency=dict(item_counter),
        do_critical_count=sum(1 for f in filings if f.do_critical_items),
        has_restatement=any("4.02" in f.items for f in filings),
        has_auditor_change=any("4.01" in f.items for f in filings),
        has_officer_departure=any("5.02" in f.items for f in filings),
        has_restructuring=any("2.05" in f.items for f in filings),
        has_impairment=any("2.06" in f.items for f in filings),
    )

    # Log results
    if filings:
        critical = summary.do_critical_count
        logger.info(
            "8-K classification: %d filings, %d unique items, %d D&O-critical",
            len(filings),
            len(item_counter),
            critical,
        )
        if summary.has_restatement:
            logger.warning("8-K ALERT: Item 4.02 (restatement/non-reliance) found")
        if summary.has_auditor_change:
            logger.warning("8-K ALERT: Item 4.01 (auditor change) found")
    else:
        logger.info("8-K classification: no 8-K filings found")

    return summary


def parse_items_from_text(text: str) -> list[str]:
    """Extract Item numbers from raw 8-K filing text.

    Args:
        text: Raw text content of an 8-K filing.

    Returns:
        Deduplicated, sorted list of item numbers found.
    """
    matches = _ITEM_PATTERN.findall(text)
    # Deduplicate and sort
    seen: set[str] = set()
    items: list[str] = []
    for m in matches:
        if m not in seen and m in ITEM_CATALOG:
            seen.add(m)
            items.append(m)
    items.sort()
    return items


def get_do_severity(items: list[str]) -> str:
    """Determine the highest D&O severity across a set of items.

    Args:
        items: List of item numbers.

    Returns:
        Highest severity: CRITICAL, HIGH, MEDIUM, or LOW.
    """
    max_rank = 0
    for item in items:
        catalog_entry = ITEM_CATALOG.get(item)
        if catalog_entry is not None:
            rank = _SEVERITY_RANK.get(catalog_entry[1], 0)
            if rank > max_rank:
                max_rank = rank
    for sev, rank in sorted(_SEVERITY_RANK.items(), key=lambda x: x[1], reverse=True):
        if max_rank >= rank:
            return sev
    return "LOW"


def get_do_critical_items(items: list[str]) -> list[str]:
    """Filter items to those that are D&O-critical.

    Args:
        items: List of item numbers.

    Returns:
        Subset of items that are in the D&O-critical set.
    """
    return [item for item in items if item in DO_CRITICAL_ITEMS]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_single_filing(doc: dict[str, str]) -> EightKFiling:
    """Parse a single 8-K filing document and classify its items.

    Args:
        doc: Filing document dict with keys: accession, filing_date,
             form_type, full_text.

    Returns:
        EightKFiling with parsed items and D&O classification.
    """
    accession = doc.get("accession", "")
    filing_date = doc.get("filing_date", "")
    full_text = doc.get("full_text", "")

    items = parse_items_from_text(full_text)
    critical = get_do_critical_items(items)
    severity = get_do_severity(items)

    titles: dict[str, str] = {}
    for item in items:
        entry = ITEM_CATALOG.get(item)
        if entry is not None:
            titles[item] = entry[0]

    # Build event summary from item titles
    summary = _build_event_summary(items, titles)

    return EightKFiling(
        accession=accession,
        filing_date=filing_date,
        items=items,
        item_titles=titles,
        do_critical_items=critical,
        do_severity=severity,
        event_summary=summary,
    )


def _build_event_summary(items: list[str], titles: dict[str, str]) -> str:
    """Build a one-line summary of the event types in this 8-K.

    Skips boilerplate items (9.01 Financial Statements and Exhibits)
    to focus on substantive content.
    """
    skip = {"9.01", "7.01"}  # Boilerplate items
    substantive = [
        f"Item {item}: {titles[item]}"
        for item in items
        if item not in skip and item in titles
    ]
    if not substantive:
        # If only boilerplate items, still describe them
        substantive = [
            f"Item {item}: {titles[item]}"
            for item in items
            if item in titles
        ]
    return "; ".join(substantive[:3])  # Cap at 3 items for readability


def _collect_llm_items(state: AnalysisState) -> dict[str, EightKFiling]:
    """Collect 8-K item data from LLM extraction results.

    Returns:
        Dict mapping accession -> EightKFiling from LLM data.
    """
    results: dict[str, EightKFiling] = {}
    if state.acquired_data is None:
        return results

    for key, data in state.acquired_data.llm_extractions.items():
        if not key.startswith("8-K:") or not isinstance(data, dict):
            continue

        accession = key.split(":", 1)[1] if ":" in key else ""
        items_covered = data.get("items_covered", [])
        if not isinstance(items_covered, list):
            continue

        # Normalize items
        items = [item.strip() for item in items_covered if isinstance(item, str)]
        items = [item for item in items if item in ITEM_CATALOG]

        if not items:
            continue

        critical = get_do_critical_items(items)
        severity = get_do_severity(items)
        titles: dict[str, str] = {}
        for item in items:
            entry = ITEM_CATALOG.get(item)
            if entry is not None:
                titles[item] = entry[0]

        # Try to get filing_date from event_date in LLM extraction
        filing_date = data.get("event_date", "") or ""

        results[accession] = EightKFiling(
            accession=accession,
            filing_date=filing_date,
            items=items,
            item_titles=titles,
            do_critical_items=critical,
            do_severity=severity,
            event_summary=_build_event_summary(items, titles),
        )

    return results


def _merge_items(existing: EightKFiling, llm_filing: EightKFiling) -> None:
    """Merge LLM-parsed items into an existing filing record.

    Adds any items from the LLM extraction that weren't found by regex.
    Updates critical items, severity, and titles accordingly.
    """
    new_items = [item for item in llm_filing.items if item not in existing.items]
    if not new_items:
        return

    existing.items.extend(new_items)
    existing.items.sort()

    # Update titles
    existing.item_titles.update(llm_filing.item_titles)

    # Recalculate critical items and severity
    existing.do_critical_items = get_do_critical_items(existing.items)
    existing.do_severity = get_do_severity(existing.items)
    existing.event_summary = _build_event_summary(
        existing.items, existing.item_titles
    )


def _merge_metadata_items(
    filings: list[EightKFiling],
    metadata: list[Any],
    counter: Counter[str],
) -> None:
    """Merge item info from filing metadata into existing filings.

    Filing metadata (from state.acquired_data.filings["8-K"]) may contain
    item numbers extracted during acquisition that aren't in the full text
    parse or LLM extraction.
    """
    for meta in metadata:
        if not isinstance(meta, dict):
            continue
        accession = meta.get("accession", "") or meta.get("accession_number", "")
        items_raw = meta.get("items", [])
        if not items_raw:
            item_num = meta.get("item_number", "")
            if item_num:
                items_raw = [item_num]

        items = [
            item.strip() for item in items_raw
            if isinstance(item, str) and item.strip() in ITEM_CATALOG
        ]
        if not items:
            continue

        existing = next((f for f in filings if f.accession == accession), None)
        if existing is not None:
            new_items = [i for i in items if i not in existing.items]
            if new_items:
                existing.items.extend(new_items)
                existing.items.sort()
                for item in new_items:
                    entry = ITEM_CATALOG.get(item)
                    if entry is not None:
                        existing.item_titles[item] = entry[0]
                    counter[item] += 1
                existing.do_critical_items = get_do_critical_items(existing.items)
                existing.do_severity = get_do_severity(existing.items)
                existing.event_summary = _build_event_summary(
                    existing.items, existing.item_titles
                )
        else:
            # Create new filing from metadata
            critical = get_do_critical_items(items)
            severity = get_do_severity(items)
            titles: dict[str, str] = {}
            for item in items:
                entry = ITEM_CATALOG.get(item)
                if entry is not None:
                    titles[item] = entry[0]

            filing_date = str(meta.get("filing_date", ""))
            filings.append(EightKFiling(
                accession=accession,
                filing_date=filing_date,
                items=items,
                item_titles=titles,
                do_critical_items=critical,
                do_severity=severity,
                event_summary=_build_event_summary(items, titles),
            ))
            counter.update(items)
