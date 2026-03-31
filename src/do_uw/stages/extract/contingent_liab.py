"""Contingent liability extraction from 10-K footnotes (SECT6-12).

Extracts ASC 450 loss contingencies via regex scan and footnote parsing.
Also provides litigation reserve filtering (sum_litigation_reserves)
to exclude warranty/tax contingencies from the litigation reserve total.
"""

from __future__ import annotations

import logging
import re

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation_details import ContingentLiability
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.contingent_notes import (
    ACCRUED_RE,
    FOOTNOTE_REF_RE,
    RANGE_RE,
    classify_asc450,
    extract_footnote_matters,
    parse_dollar_amount,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

_SOURCE = "10-K"

EXPECTED_FIELDS: list[str] = [
    "probable_matters",
    "reasonably_possible_matters",
    "remote_matters",
    "accrued_amounts",
    "range_disclosures",
    "total_reserve",
]

# --- Regex patterns ---

_CONTINGENT_RE = re.compile(
    r"(?i)(?:contingent|contingency|contingencies"
    r"|loss\s+contingenc(?:y|ies)"
    r"|commitments\s+and\s+contingencies)"
)

_AMOUNT_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
)

_TOTAL_RESERVE_RE = re.compile(
    r"(?i)(?:total\s+(?:litigation|legal)\s+reserve[ds]?"
    r"|aggregate\s+(?:litigation|legal)\s+(?:accrual|reserve))"
    r".{0,200}?"
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
    re.DOTALL,
)

# Item 3 section markers for pending litigation matters.
_ITEM3_START = [
    r"(?i)\bitem\s+3[\.\s:]+legal\s+proceedings\b",
    r"(?i)\bitem\s+3\b(?!\s*[0-9a-z])",
]
_ITEM3_END = [
    r"(?i)\bitem\s+3a\b",
    r"(?i)\bitem\s+4\b",
]


# ---------------------------------------------------------------------------
# Contingency extraction (full-text scan)
# ---------------------------------------------------------------------------


def extract_contingencies_from_text(
    full_text: str,
) -> list[ContingentLiability]:
    """Extract contingent liabilities from full 10-K text.

    Searches for ASC 450 language, classifies each contingency,
    and extracts accrued amounts and disclosed ranges.

    Args:
        full_text: Full 10-K filing text.

    Returns:
        List of ContingentLiability instances.
    """
    liabilities: list[ContingentLiability] = []

    # Find all contingency mentions.
    for match in _CONTINGENT_RE.finditer(full_text):
        # Extract surrounding context (500 chars).
        start = max(0, match.start() - 200)
        end = min(len(full_text), match.end() + 300)
        context = full_text[start:end].strip()

        liability = _parse_contingency_context(context)
        if liability is not None:
            liabilities.append(liability)

    return liabilities


def _parse_contingency_context(
    context: str,
) -> ContingentLiability | None:
    """Parse a single contingency mention from surrounding context.

    Args:
        context: Text context around a contingency keyword.

    Returns:
        ContingentLiability or None if insufficient information.
    """
    liability = ContingentLiability()

    # Classify ASC 450.
    classification = classify_asc450(context)
    if classification:
        liability.asc_450_classification = sourced_str(
            classification, _SOURCE, Confidence.MEDIUM
        )
    else:
        # No explicit classification -- skip this mention.
        return None

    # Description (max 500 chars).
    desc = context[:500].strip()
    # Clean up whitespace.
    desc = re.sub(r"\s+", " ", desc)
    liability.description = sourced_str(
        desc, _SOURCE, Confidence.MEDIUM
    )

    # Accrued amount.
    accrued = ACCRUED_RE.search(context)
    if accrued:
        amount = parse_dollar_amount(
            accrued.group(1), accrued.group(2)
        )
        if amount is not None:
            liability.accrued_amount = sourced_float(
                amount, _SOURCE, Confidence.MEDIUM
            )

    # Range disclosure.
    range_match = RANGE_RE.search(context)
    if range_match:
        low = parse_dollar_amount(
            range_match.group(1), range_match.group(2)
        )
        high = parse_dollar_amount(
            range_match.group(3), range_match.group(4)
        )
        if low is not None:
            liability.range_low = sourced_float(
                low, _SOURCE, Confidence.MEDIUM
            )
        if high is not None:
            liability.range_high = sourced_float(
                high, _SOURCE, Confidence.MEDIUM
            )

    # Footnote reference.
    footnote = FOOTNOTE_REF_RE.search(context)
    if footnote:
        liability.source_note = sourced_str(
            footnote.group(0), _SOURCE, Confidence.HIGH
        )

    return liability


# ---------------------------------------------------------------------------
# Total reserve extraction
# ---------------------------------------------------------------------------


def extract_total_reserve(
    full_text: str,
) -> SourcedValue[float] | None:
    """Extract total litigation reserve amount from 10-K text.

    Args:
        full_text: Full 10-K filing text.

    Returns:
        SourcedValue[float] if found, else None.
    """
    match = _TOTAL_RESERVE_RE.search(full_text)
    if match:
        amount = parse_dollar_amount(match.group(1), match.group(2))
        if amount is not None:
            return sourced_float(amount, _SOURCE, Confidence.MEDIUM)
    return None


# ---------------------------------------------------------------------------
# Item 3 pending matters
# ---------------------------------------------------------------------------


def extract_item3_matters(text_10k: str) -> list[ContingentLiability]:
    """Extract pending litigation matters from Item 3.

    Creates contingent liability entries for each disclosed active
    case in the Legal Proceedings section.

    Args:
        text_10k: Full 10-K text.

    Returns:
        List of ContingentLiability from Item 3.
    """
    from do_uw.stages.extract.filing_sections import extract_section

    item3 = extract_section(text_10k, _ITEM3_START, _ITEM3_END)
    if not item3:
        return []

    liabilities: list[ContingentLiability] = []

    # Look for individual case mentions.
    case_pattern = re.compile(
        r"(?i)(?:pending|filed|commenced|alleged|claim|lawsuit|action)"
    )
    sentences = re.split(r"(?<=[.!?])\s+", item3)
    for sentence in sentences:
        if case_pattern.search(sentence) and len(sentence) > 50:
            liability = ContingentLiability()
            desc = sentence.strip()[:500]
            desc = re.sub(r"\s+", " ", desc)
            liability.description = sourced_str(
                desc, "10-K Item 3", Confidence.MEDIUM
            )
            # Item 3 matters are typically reasonably possible.
            liability.asc_450_classification = sourced_str(
                "reasonably_possible",
                "10-K Item 3",
                Confidence.LOW,
            )
            # Check for amounts.
            amount_match = _AMOUNT_RE.search(sentence)
            if amount_match:
                amount = parse_dollar_amount(
                    amount_match.group(1), amount_match.group(2)
                )
                if amount is not None:
                    liability.accrued_amount = sourced_float(
                        amount, "10-K Item 3", Confidence.LOW
                    )
            liabilities.append(liability)

    return liabilities


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def deduplicate_liabilities(
    liabilities: list[ContingentLiability],
) -> list[ContingentLiability]:
    """Remove duplicate liabilities based on description similarity.

    Uses simple prefix matching (first 100 chars) for deduplication.

    Args:
        liabilities: List to deduplicate.

    Returns:
        Deduplicated list.
    """
    seen: set[str] = set()
    unique: list[ContingentLiability] = []
    for lib in liabilities:
        if lib.description is None:
            unique.append(lib)
            continue
        key = lib.description.value[:100].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(lib)
    return unique


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def extract_contingent_liabilities(
    state: AnalysisState,
) -> tuple[
    list[ContingentLiability], SourcedValue[float] | None, ExtractionReport
]:
    """Extract contingent liabilities from 10-K footnotes and Item 3.

    Uses three extraction strategies:
    1. Full-text scan for explicit ASC 450 keywords.
    2. Footnote extraction: locate the "Commitments and Contingencies"
       note, split into individual matters, classify with implicit
       patterns (see contingent_notes.py).
    3. Item 3 parsing for pending litigation matters.

    Args:
        state: Analysis state with acquired filing data.

    Returns:
        Tuple of (liabilities, total_reserve, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []

    text_10k = get_filing_document_text(state, "10-K")
    if not text_10k:
        warnings.append(
            "No 10-K text available for contingent liabilities"
        )
        report = create_report(
            extractor_name="contingent_liabilities",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=_SOURCE,
            warnings=warnings,
        )
        log_report(report)
        return [], None, report

    # --- Strategy 1: Full-text scan for explicit ASC 450 keywords ---
    fulltext_liabs = extract_contingencies_from_text(text_10k)

    # --- Strategy 2: Footnote extraction with implicit patterns ---
    footnote_liabs = extract_footnote_matters(text_10k)

    # --- Strategy 3: Item 3 parsing ---
    item3_liabs = extract_item3_matters(text_10k)

    # --- Combine and deduplicate ---
    all_liabs = fulltext_liabs + footnote_liabs + item3_liabs
    all_liabs = deduplicate_liabilities(all_liabs)

    # --- Classify counts ---
    probable_count = 0
    possible_count = 0
    remote_count = 0
    accrued_count = 0
    range_count = 0

    for lib in all_liabs:
        if lib.asc_450_classification is not None:
            cls = lib.asc_450_classification.value
            if cls == "probable":
                probable_count += 1
            elif cls == "reasonably_possible":
                possible_count += 1
            elif cls == "remote":
                remote_count += 1
        if lib.accrued_amount is not None:
            accrued_count += 1
        if lib.range_low is not None or lib.range_high is not None:
            range_count += 1

    if probable_count > 0:
        found.append("probable_matters")
    if possible_count > 0:
        found.append("reasonably_possible_matters")
    if remote_count > 0:
        found.append("remote_matters")
    if accrued_count > 0:
        found.append("accrued_amounts")
    if range_count > 0:
        found.append("range_disclosures")

    # --- Total reserve ---
    reserve = extract_total_reserve(text_10k)

    # Also check existing state data.
    if reserve is None and state.extracted is not None:
        lit = state.extracted.litigation
        if lit is not None and lit.total_litigation_reserve is not None:
            reserve = lit.total_litigation_reserve

    if reserve is not None:
        found.append("total_reserve")

    logger.info(
        "Contingent liabilities: %d total (%d probable, %d possible, "
        "%d remote), %d accrued, %d ranges, reserve=%s",
        len(all_liabs),
        probable_count,
        possible_count,
        remote_count,
        accrued_count,
        range_count,
        "found" if reserve else "not found",
    )

    report = create_report(
        extractor_name="contingent_liabilities",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=_SOURCE,
        warnings=warnings,
    )
    log_report(report)
    return all_liabs, reserve, report


# ---------------------------------------------------------------------------
# Litigation reserve filtering
# ---------------------------------------------------------------------------

# Keywords indicating litigation-related contingencies.
_LITIGATION_KEYWORDS = {
    "litigation", "lawsuit", "legal", "settlement", "plaintiff",
    "defendant", "court", "arbitration", "claim", "damages",
    "securities", "class action", "derivative", "fiduciary",
    "antitrust", "regulatory", "enforcement", "investigation",
    "indemnif", "judgment", "verdict", "injunction",
}

# Keywords indicating NON-litigation contingencies.
_NON_LITIGATION_KEYWORDS = {
    "warranty", "product warranty", "resale value guarantee",
    "tax contingenc", "tax position", "unrecognized tax",
}


def is_litigation_related(description: str) -> bool:
    """Check if a contingent liability description is litigation-related.

    Filters out warranty reserves, tax contingencies, and other
    non-litigation ASC 450 items that shouldn't count toward the
    litigation reserve total.
    """
    desc_lower = description.lower()
    for kw in _NON_LITIGATION_KEYWORDS:
        if kw in desc_lower:
            return False
    for kw in _LITIGATION_KEYWORDS:
        if kw in desc_lower:
            return True
    return False


def sum_litigation_reserves(
    liabilities: list[ContingentLiability],
) -> float:
    """Sum accrued amounts from litigation-related contingencies only.

    Filters out warranty reserves, tax positions, and other non-litigation
    ASC 450 items. Uses contingency_type field when available, falls back
    to keyword matching on description.
    """
    total = 0.0
    for cl in liabilities:
        if cl.accrued_amount and cl.accrued_amount.value:
            ct = cl.contingency_type.value if cl.contingency_type else None
            if ct and ct.lower() in ("litigation", "regulatory"):
                total += cl.accrued_amount.value
                continue
            if ct and ct.lower() in ("warranty", "tax", "environmental"):
                logger.debug(
                    "Excluding %s contingency from reserve: %s",
                    ct,
                    (cl.description.value if cl.description else "")[:80],
                )
                continue
            desc = cl.description.value if cl.description else ""
            if is_litigation_related(desc):
                total += cl.accrued_amount.value
            else:
                logger.debug(
                    "Excluding non-litigation contingency from reserve: %s",
                    desc[:80],
                )
    return total
