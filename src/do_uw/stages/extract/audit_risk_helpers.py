"""Regex-based audit risk extraction helpers.

Auditor identification, tenure, opinion type, going concern detection,
material weakness extraction, restatement detection, late filing check,
comment letter counting, and CAM extraction from 10-K text and XBRL.
Split from audit_risk.py for 500-line compliance.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import get_filings

# Big 4 accounting firms with known name variants.
BIG4_FIRMS: dict[str, list[str]] = {
    "Deloitte": ["deloitte", "deloitte & touche", "deloitte touche"],
    "Ernst & Young": [
        "ernst & young", "ernst and young", "ernst&young",
        "ey llp", "ey ", "\ney\n", "ernst & young llp",
    ],
    "KPMG": ["kpmg"],
    "PricewaterhouseCoopers": [
        "pricewaterhousecoopers",
        "pricewaterhouse coopers",
        "pwc",
    ],
}

# SEC filing deadline days after fiscal year end by filer category.
FILING_DEADLINES: dict[str, int] = {
    "Large Accelerated Filer": 60,
    "Accelerated Filer": 75,
    "Non-accelerated Filer": 90,
    "Smaller Reporting Company": 90,
}


def extract_auditor_name(
    text: str, facts: dict[str, Any],
) -> tuple[str | None, bool]:
    """Identify the auditor and whether they are Big 4.

    Checks XBRL dei:AuditorName first, then searches filing text.

    Returns:
        Tuple of (auditor_name, is_big4).
    """
    # Try XBRL dei:AuditorName first.
    xbrl_name = _get_dei_auditor_name(facts)
    if xbrl_name:
        is_big4 = _check_big4(xbrl_name)
        return xbrl_name, is_big4

    # Search filing text for Big 4 and other known auditors.
    text_lower = text.lower()
    for firm_name, variants in BIG4_FIRMS.items():
        for variant in variants:
            if variant in text_lower:
                return firm_name, True

    # Look for "Report of Independent Registered Public Accounting Firm"
    # followed by a firm name.
    pattern = (
        r"report of independent registered public accounting firm"
        r"[\s\S]{0,500}?(?:signed|/s/)\s*([A-Z][A-Za-z &.,]+)"
    )
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        firm = match.group(1).strip()
        return firm, _check_big4(firm)

    return None, False


def _get_dei_auditor_name(facts: dict[str, Any]) -> str | None:
    """Extract AuditorName from XBRL DEI namespace."""
    facts_inner = facts.get("facts")
    if not isinstance(facts_inner, dict):
        return None
    dei = cast(dict[str, Any], facts_inner).get("dei")
    if not isinstance(dei, dict):
        return None
    auditor = cast(dict[str, Any], dei).get("AuditorName")
    if not isinstance(auditor, dict):
        return None
    units = cast(dict[str, Any], auditor).get("units")
    if not isinstance(units, dict):
        return None
    # AuditorName is a string type, look in any unit key.
    for unit_key in cast(dict[str, Any], units):
        raw_entries = cast(dict[str, Any], units)[unit_key]
        if isinstance(raw_entries, list):
            typed = cast(list[dict[str, Any]], raw_entries)
            if len(typed) > 0:
                latest = max(typed, key=lambda e: str(e.get("end", "")))
                val = str(latest.get("val", ""))
                if val:
                    return val
    return None


def _check_big4(name: str) -> bool:
    """Check if auditor name matches a Big 4 firm."""
    name_lower = name.lower()
    for variants in BIG4_FIRMS.values():
        for variant in variants:
            if variant in name_lower:
                return True
    return False


def extract_tenure(text: str) -> int | None:
    """Extract auditor tenure in years from filing text.

    Looks for patterns like 'served as auditor since 2005'.
    """
    patterns = [
        r"served as (?:the company's |the )?auditor since (\d{4})",
        r"auditor since (\d{4})",
        r"engaged (?:as )?(?:our )?(?:independent )?auditor(?:s)? since (\d{4})",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            current_year = datetime.now(tz=UTC).year
            tenure = current_year - year
            if 0 < tenure < 100:
                return tenure
    return None


def extract_opinion_type(text: str) -> str:
    """Parse the auditor's opinion type from the report text."""
    text_lower = text.lower()

    if "disclaimer of opinion" in text_lower:
        return "disclaimer"
    if "adverse opinion" in text_lower:
        return "adverse"
    if "qualified opinion" in text_lower or "except for" in text_lower:
        return "qualified"
    if "present fairly, in all material respects" in text_lower:
        return "unqualified"
    if "presents fairly, in all material respects" in text_lower:
        return "unqualified"
    if "unqualified opinion" in text_lower:
        return "unqualified"
    # Default: if auditor report exists, assume unqualified (most common).
    if "independent registered public accounting firm" in text_lower:
        return "unqualified"
    return "unknown"


def extract_going_concern(text: str) -> bool:
    """Detect actual going concern qualification in filing text.

    Distinguishes genuine going concern opinions (auditor/management expressing
    doubt about continued operations) from benign accounting usage of the phrase
    "going concern" (e.g., fair value methodology, accounting policy descriptions).
    """
    text_lower = text.lower()

    # Strong indicators — unambiguous going concern qualification language.
    strong_phrases = [
        "substantial doubt about its ability to continue",
        "substantial doubt about the company's ability to continue",
        "substantial doubt about our ability to continue",
        "raise substantial doubt",
        "raised substantial doubt",
        "raises substantial doubt",
        "going concern opinion",
        "going concern qualification",
        "going-concern opinion",
        "going-concern qualification",
        "may not be able to continue as a going concern",
        "will not be able to continue as a going concern",
    ]
    if any(phrase in text_lower for phrase in strong_phrases):
        return True

    # Context-sensitive: "ability to continue as a going concern" can appear in
    # both genuine disclosures AND benign management evaluations. Require the
    # surrounding sentence to contain doubt language and NOT contain negation.
    if "ability to continue as a going concern" in text_lower:
        sentences = re.split(r"[.!?]+", text)
        negations = [
            "no substantial doubt", "not raise", "does not raise",
            "did not raise", "do not raise", "no doubt",
            "determined there are no", "concluded that no",
            "no conditions or events", "no indication",
        ]
        doubt_words = ["doubt", "uncertain", "inability", "unable", "question"]
        for sentence in sentences:
            sent_lower = sentence.lower()
            if "ability to continue as a going concern" not in sent_lower:
                continue
            if any(neg in sent_lower for neg in negations):
                continue
            if any(dw in sent_lower for dw in doubt_words):
                return True

    return False


def _is_auditor_methodology_boilerplate(sentence: str) -> bool:
    """True if the sentence is standard PCAOB auditor report methodology language.

    Auditor reports describe their audit *process* using phrases like
    "assessing the risk that a material weakness exists". These are NOT
    actual material weakness findings -- they describe what the auditor
    did, not what they found.

    Actual findings use phrases like "we identified a material weakness"
    or "management identified a material weakness".
    """
    sent_lower = sentence.lower()

    # Phrases that indicate auditor methodology description, NOT findings.
    methodology_phrases = (
        "our audit of internal control over financial reporting included",
        "obtaining an understanding of internal control",
        "assessing the risk that a material weakness exists",
        "testing and evaluating the design and operating effectiveness",
        "our responsibility is to express an opinion",
        "we conducted our audit in accordance with",
        "the standards of the public company accounting oversight board",
        "a material weakness is a deficiency",  # definition, not finding
        "a material weakness is a deficiency, or a combination of deficiencies",
        "a significant deficiency is a deficiency",  # definition, not finding
        "reasonable assurance about whether effective internal control",
        "our audit included performing procedures",
        "we also have audited, in accordance with",
        "the objectives of an audit include",
    )

    if any(phrase in sent_lower for phrase in methodology_phrases):
        return True

    return False


def extract_material_weaknesses(text: str) -> list[str]:
    """Extract material weakness descriptions from Item 9A / SOX 404.

    Filters out standard PCAOB auditor report boilerplate that describes
    audit methodology (e.g., "assessing the risk that a material weakness
    exists") -- these describe the audit PROCESS, not actual findings.
    """
    text_lower = text.lower()
    weaknesses: list[str] = []

    if "material weakness" not in text_lower:
        return weaknesses

    # Find sentences containing "material weakness".
    sentences = re.split(r"[.!?]+", text)
    for sentence in sentences:
        if "material weakness" in sentence.lower() and len(sentence.strip()) > 20:
            cleaned = sentence.strip()[:500]
            if _is_auditor_methodology_boilerplate(cleaned):
                continue
            weaknesses.append(cleaned)

    return weaknesses[:5]  # Cap at 5 most relevant.


def extract_restatements(text: str) -> list[dict[str, str]]:
    """Detect restatement disclosures in filing text."""
    text_lower = text.lower()
    restatements: list[dict[str, str]] = []

    keywords = ["restatement", "restated", "corrected and restated"]
    if not any(kw in text_lower for kw in keywords):
        return restatements

    # Classify restatement type.
    restatement_type = "little_r"
    if "10-k/a" in text_lower or "amendment" in text_lower:
        restatement_type = "big_R"

    # Extract context sentences.
    sentences = re.split(r"[.!?]+", text)
    for sentence in sentences:
        sent_lower = sentence.lower()
        if any(kw in sent_lower for kw in keywords) and len(sentence.strip()) > 20:
            restatements.append({
                "type": restatement_type,
                "description": sentence.strip()[:500],
            })
            break  # Take first relevant sentence.

    return restatements


def check_late_filing(state: AnalysisState) -> bool:
    """Check if the most recent 10-K was filed after the SEC deadline."""
    if state.company is None:
        return False

    filer_cat_sv = state.company.filer_category
    filer_cat = filer_cat_sv.value if filer_cat_sv else "Non-accelerated Filer"
    deadline_days = FILING_DEADLINES.get(filer_cat, 90)

    filings = get_filings(state)
    filing_meta = filings.get("10-K")
    if not isinstance(filing_meta, dict):
        return False

    typed_meta = cast(dict[str, Any], filing_meta)
    filing_date_str = str(typed_meta.get("filing_date", ""))
    period_end_str = str(typed_meta.get("period_of_report", ""))

    if not filing_date_str or not period_end_str:
        return False

    try:
        filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
        period_end = datetime.strptime(period_end_str, "%Y-%m-%d")
        delta = (filing_date - period_end).days
        return delta > deadline_days
    except ValueError:
        return False


def count_comment_letters(state: AnalysisState) -> int:
    """Count SEC comment letters (CORRESP filings) from acquired data."""
    filings = get_filings(state)
    corresp = filings.get("CORRESP")
    if isinstance(corresp, list):
        typed_list = cast(list[Any], corresp)
        return len(typed_list)
    if isinstance(corresp, int):
        return corresp
    return 0


def extract_cams(text: str) -> list[str]:
    """Extract Critical Audit Matters from auditor report."""
    cams: list[str] = []
    text_lower = text.lower()

    if "critical audit matter" not in text_lower:
        return cams

    # Find CAM titles -- usually formatted as headers.
    cam_pattern = r"critical audit matter[s]?\s*[-:]\s*(.+?)(?:\n|$)"
    matches = re.findall(cam_pattern, text, re.IGNORECASE)
    for match in matches:
        title = match.strip()[:200]
        if title and len(title) > 5:
            cams.append(title)

    # If no titled matches, extract sentences.
    if not cams:
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            if "critical audit matter" in sentence.lower() and len(sentence.strip()) > 30:
                cams.append(sentence.strip()[:300])

    return cams[:5]  # Cap at 5 CAMs.
