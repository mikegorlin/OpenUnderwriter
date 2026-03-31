"""Footnote-based contingent liability extraction (SECT6-12).

Extracts individual litigation matters from the "Commitments and
Contingencies" footnote (typically Note 13) in 10-K filings.
Many filers (e.g., Tesla, Apple) redirect Item 3 to this note,
so footnote extraction is essential for complete coverage.

Also contains shared regex patterns and utility functions used by
contingent_liab.py to avoid circular imports.
"""

from __future__ import annotations

import logging
import re

from do_uw.models.common import Confidence
from do_uw.models.litigation_details import ContingentLiability
from do_uw.stages.extract.sourced import (
    sourced_float,
    sourced_str,
)

logger = logging.getLogger(__name__)

_NOTE_SOURCE = "10-K Note"


# ---------------------------------------------------------------------------
# Shared regex patterns (used by contingent_liab.py too)
# ---------------------------------------------------------------------------

ACCRUED_RE = re.compile(
    r"(?i)(?:accrued|accrual|reserve[ds]?)"
    r"\s+(?:for|of)?\s*"
    r"(?:litigation|legal|contingent)"
    r".{0,200}?"
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
    re.DOTALL,
)

RANGE_RE = re.compile(
    r"(?i)(?:range\s+of\s+(?:possible|potential)\s+loss"
    r"|(?:possible|potential)\s+loss.*?range)"
    r".{0,300}?"
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?"
    r".{0,100}?"
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
    re.DOTALL,
)

FOOTNOTE_REF_RE = re.compile(
    r"(?i)(?:Note\s+\d+|Footnote\s+\d+)",
)

ASC450_CLASS_RE = re.compile(
    r"(?i)(probable|reasonably\s+possible|remote)"
    r"\s+(?:\w+\s+){0,4}"
    r"(?:that|loss|liability|of\s+loss|outcome|the\s+company|we\s+will"
    r"|additional|an?\s+unfavorable|damages|exposure|incur)",
)


# --- Footnote section extraction patterns ---

# Start boundary: "Note NN -- Commitments and Contingencies"
_NOTE_COMMITMENTS_START_RE = re.compile(
    r"(?i)Note\s+\d+\s*[\u2013\u2014\-]+\s*Commitments\s+and\s+Contingencies"
)

# End boundary: next note heading "Note NN --"
_NOTE_NEXT_RE = re.compile(
    r"(?i)Note\s+\d+\s*[\u2013\u2014\-]+"
)

# Matter heading patterns within a footnote section.
# These identify sub-sections like "Litigation Relating to ..."
# Patterns are ordered by specificity. "Other Legal/Matters" is
# removed because it matches mid-sentence text too aggressively.
_MATTER_HEADING_RE = re.compile(
    r"(?:Legal\s+Proceedings"
    r"|Litigation\s+(?:and\s+Investigations?\s+)?(?:Relat(?:ing|ed)|Regarding|Concerning)"
    r"|Other\s+Litigation\s+Related"
    r"|Certain\s+(?:Derivative|Investigations|Litigation)"
    r"|Investigations?\s+and\s+Other\s+Matters"
    r"|Discrimination\s+and\s+Harassment"
    r"|Letters\s+of\s+Credit"
    r"|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z])",
)

# Litigation keyword check for matters without explicit classification.
_LITIGATION_KW_RE = re.compile(
    r"(?i)(?:lawsuit|litigation|complaint|plaintiff|defendant"
    r"|filed|court|action|settlement|verdict|damages|judgment"
    r"|alleged|alleging|claims?)"
)


# --- Implicit ASC 450 classification patterns ---

# Probable indicators: company has recorded an accrual (ASC 450 requires
# accrual only when loss is probable AND estimable).
_IMPLICIT_PROBABLE_RE = re.compile(
    r"(?i)(?:recorded\s+(?:a|an)\s+(?:(?:immaterial\s+)?accrual"
    r"|provision|charge|reserve)"
    r"|has\s+(?:been\s+)?accrued"
    r"|accrued\s+(?:a\s+)?(?:liability|charge|provision|loss)"
    r"|established\s+(?:a\s+)?(?:reserve|provision|accrual))",
)

# Reasonably possible indicators: unable to estimate, unfavorable outcome
# could be material, cannot predict, possible loss.
_IMPLICIT_POSSIBLE_RE = re.compile(
    r"(?i)(?:unable\s+to\s+(?:reasonably\s+)?estimate"
    r"|cannot\s+(?:reasonably\s+)?estimate"
    r"|(?:an?\s+)?unfavorable\s+(?:outcome|ruling|result|development|verdict)"
    r"|material\s+adverse\s+(?:impact|effect|consequence)"
    r"|possible\s+loss\s+or\s+range\s+of\s+loss"
    r"|cannot\s+predict\s+the\s+(?:outcome|impact|result)"
    r"|we\s+cannot\s+predict)",
)

# Remote indicators: no merit, without merit, frivolous.
_IMPLICIT_REMOTE_RE = re.compile(
    r"(?i)(?:without\s+merit"
    r"|lacks?\s+merit"
    r"|no\s+merit"
    r"|frivolous"
    r"|(?:we\s+)?believe\s+(?:the\s+)?claims?\s+(?:is|are)\s+"
    r"(?:without|lacking)\s+merit)",
)

# Immaterial accrual pattern (no dollar amount disclosed).
_IMMATERIAL_ACCRUAL_RE = re.compile(
    r"(?i)recorded\s+(?:a|an)\s+immaterial\s+accrual"
)


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def parse_dollar_amount(
    amount_str: str, unit: str | None = None
) -> float | None:
    """Parse a dollar amount string to float.

    Handles comma-separated numbers and million/billion multipliers.

    Args:
        amount_str: Numeric string (e.g., '2,500' or '1.5').
        unit: Optional unit ('million' or 'billion').

    Returns:
        Float value in USD, or None if parsing fails.
    """
    try:
        cleaned = amount_str.replace(",", "")
        value = float(cleaned)
    except ValueError:
        return None

    if unit:
        unit_lower = unit.lower()
        if unit_lower == "billion":
            value *= 1_000_000_000
        elif unit_lower == "million":
            value *= 1_000_000

    return value


def classify_asc450(text: str) -> str | None:
    """Classify ASC 450 loss contingency from text context.

    Matches explicit keywords: probable, reasonably possible, remote.

    Returns: 'probable', 'reasonably_possible', 'remote', or None.
    """
    match = ASC450_CLASS_RE.search(text)
    if match:
        raw = match.group(1).lower().strip()
        if "probable" in raw:
            return "probable"
        if "reasonably" in raw:
            return "reasonably_possible"
        if "remote" in raw:
            return "remote"
    return None


def classify_asc450_implicit(text: str) -> str | None:
    """Classify ASC 450 using implicit language patterns.

    Many filers avoid explicit "probable" / "reasonably possible"
    terms and instead use phrases that imply the classification:
    - "recorded an accrual" -> probable (ASC 450 requires accrual
      only when loss is probable AND estimable)
    - "unable to estimate" / "unfavorable outcome" -> reasonably_possible
    - "without merit" / "frivolous" -> remote

    Returns: 'probable', 'reasonably_possible', 'remote', or None.
    """
    # Try explicit first.
    explicit = classify_asc450(text)
    if explicit:
        return explicit

    # Check implicit patterns in priority order.
    if _IMPLICIT_PROBABLE_RE.search(text):
        return "probable"
    if _IMPLICIT_POSSIBLE_RE.search(text):
        return "reasonably_possible"
    if _IMPLICIT_REMOTE_RE.search(text):
        return "remote"
    return None


# ---------------------------------------------------------------------------
# Footnote section extraction
# ---------------------------------------------------------------------------


def extract_commitments_note(text_10k: str) -> str:
    """Extract the Commitments and Contingencies footnote from 10-K.

    Finds "Note NN -- Commitments and Contingencies" and extracts
    all text until the next "Note NN --" heading.

    Args:
        text_10k: Full 10-K filing text.

    Returns:
        Footnote text, or empty string if not found.
    """
    start_match = _NOTE_COMMITMENTS_START_RE.search(text_10k)
    if not start_match:
        return ""

    # Find the next note heading after this one.
    search_start = start_match.end()
    end_match = _NOTE_NEXT_RE.search(text_10k[search_start:])
    if end_match:
        note_text = text_10k[
            start_match.start() : search_start + end_match.start()
        ]
    else:
        # No next note -- take up to 50K chars.
        note_text = text_10k[
            start_match.start() : start_match.start() + 50_000
        ]

    return note_text.strip()


def _split_note_into_matters(
    note_text: str,
) -> list[tuple[str, str]]:
    """Split a footnote into individual litigation matters.

    Returns list of (heading, body) tuples. Each body contains
    the text from one heading to the next.

    Filters out near-duplicate headings (when one heading appears
    immediately inside another, e.g., "Legal Proceedings" at pos 40
    followed by "Litigation Relating" at pos 58 -- the short
    "Legal Proceedings" section is just a container heading).

    Args:
        note_text: Full text of the commitments and contingencies note.

    Returns:
        List of (heading, body) tuples.
    """
    # Find all heading positions.
    heading_positions: list[tuple[int, str]] = []
    for match in _MATTER_HEADING_RE.finditer(note_text):
        heading = match.group(0).strip()
        heading_positions.append((match.start(), heading))

    if not heading_positions:
        # No sub-headings found -- treat entire note as one matter.
        if len(note_text) > 200:
            return [("Commitments and Contingencies", note_text)]
        return []

    matters: list[tuple[str, str]] = []
    for i, (pos, heading) in enumerate(heading_positions):
        if i + 1 < len(heading_positions):
            end = heading_positions[i + 1][0]
        else:
            end = len(note_text)
        body = note_text[pos:end].strip()
        # Skip very short bodies -- container headings or
        # headings immediately followed by another heading.
        if len(body) > 200:
            matters.append((heading, body))

    return matters


# ---------------------------------------------------------------------------
# Individual matter parsing
# ---------------------------------------------------------------------------


def _parse_footnote_matter(
    heading: str, body: str
) -> ContingentLiability | None:
    """Parse a single litigation matter from footnote text.

    Uses implicit classification patterns to determine ASC 450 class.

    Args:
        heading: Matter heading text.
        body: Full matter body text.

    Returns:
        ContingentLiability or None if not a litigation matter.
    """
    # Skip non-litigation sections (e.g., "Letters of Credit").
    if re.search(r"(?i)letters\s+of\s+credit", heading):
        return None

    classification = classify_asc450_implicit(body)
    if classification is None:
        if not _LITIGATION_KW_RE.search(body):
            return None
        # Has litigation language but no classification signal --
        # default to reasonably_possible (conservative assumption).
        classification = "reasonably_possible"

    liability = ContingentLiability()
    liability.asc_450_classification = sourced_str(
        classification, _NOTE_SOURCE, Confidence.MEDIUM
    )

    # Description: heading + first 400 chars of body.
    desc = f"{heading}: {body[:400]}"
    desc = re.sub(r"\s+", " ", desc).strip()
    liability.description = sourced_str(
        desc[:500], _NOTE_SOURCE, Confidence.MEDIUM
    )

    # Extract dollar amounts from the matter body.
    _extract_matter_amounts(liability, body)

    # Note reference.
    note_ref = FOOTNOTE_REF_RE.search(body)
    if note_ref:
        liability.source_note = sourced_str(
            note_ref.group(0), _NOTE_SOURCE, Confidence.HIGH
        )

    return liability


def _extract_matter_amounts(
    liability: ContingentLiability, body: str
) -> None:
    """Extract accrued amounts and ranges from matter body text.

    Looks for accrual language near dollar amounts. For matters
    classified as probable, also checks for explicit dollar amounts
    associated with verdicts, settlements, or awards.

    Args:
        liability: The ContingentLiability to populate.
        body: Matter body text.
    """
    # Check for accrual with dollar amount.
    accrued_match = ACCRUED_RE.search(body)
    if accrued_match:
        amount = parse_dollar_amount(
            accrued_match.group(1), accrued_match.group(2)
        )
        if amount is not None:
            liability.accrued_amount = sourced_float(
                amount, _NOTE_SOURCE, Confidence.MEDIUM
            )

    # Check for "recorded an immaterial accrual" (no dollar amount).
    if liability.accrued_amount is None:
        if _IMMATERIAL_ACCRUAL_RE.search(body):
            # Accrual exists but amount not disclosed.
            liability.accrued_amount = sourced_float(
                0.0, _NOTE_SOURCE, Confidence.LOW
            )

    # Check for range disclosures.
    range_match = RANGE_RE.search(body)
    if range_match:
        low = parse_dollar_amount(
            range_match.group(1), range_match.group(2)
        )
        high = parse_dollar_amount(
            range_match.group(3), range_match.group(4)
        )
        if low is not None:
            liability.range_low = sourced_float(
                low, _NOTE_SOURCE, Confidence.MEDIUM
            )
        if high is not None:
            liability.range_high = sourced_float(
                high, _NOTE_SOURCE, Confidence.MEDIUM
            )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_footnote_matters(
    text_10k: str,
) -> list[ContingentLiability]:
    """Extract individual litigation matters from footnote text.

    Locates the Commitments and Contingencies footnote, splits it
    into individual matters, and classifies each using both explicit
    and implicit ASC 450 patterns.

    Args:
        text_10k: Full 10-K filing text.

    Returns:
        List of ContingentLiability instances from footnotes.
    """
    note_text = extract_commitments_note(text_10k)
    if not note_text:
        return []

    matters = _split_note_into_matters(note_text)
    liabilities: list[ContingentLiability] = []

    for heading, body in matters:
        liability = _parse_footnote_matter(heading, body)
        if liability is not None:
            liabilities.append(liability)

    return liabilities
