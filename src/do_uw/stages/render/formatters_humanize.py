"""Humanization utilities for display formatting.

Extracted from formatters.py (Plan 43-03) to keep files under 500 lines.
Provides theory code, field name, evidence, and impact humanization.

Backward-compat re-exports are provided in formatters.py so existing
import sites need no changes.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Theory code humanization
# ---------------------------------------------------------------------------

_THEORY_DISPLAY: dict[str, str] = {
    "A_DISCLOSURE": "Securities Disclosure (10b-5)",
    "A_MISREPRESENTATION": "Material Misrepresentation",
    "A_OMISSION": "Material Omission",
    "B_FIDUCIARY": "Fiduciary Duty Breach",
    "B_WASTE": "Corporate Waste",
    "B_LOYALTY": "Duty of Loyalty",
    "C_REGULATORY": "Regulatory Non-Compliance",
    "C_ENFORCEMENT": "Enforcement Action",
    "D_EMPLOYMENT": "Employment Practices",
    "D_ERISA": "ERISA Violation",
    "E_ANTITRUST": "Antitrust / Competition",
    "E_IP": "Intellectual Property",
    "E_MA": "Mergers & Acquisitions",
    "B_GUIDANCE": "Forward Guidance / Projections",
    "C_PRODUCT_OPS": "Product / Operations Liability",
    "D_GOVERNANCE": "Corporate Governance",
}


def humanize_theory(code: str) -> str:
    """Convert internal theory codes to human-readable labels.

    Handles patterns like:
    - A_DISCLOSURE -> "Securities Disclosure (10b-5)"
    - SECT7-F7 -> "Factor 7"
    - Unknown codes -> title-cased with underscores as spaces

    Args:
        code: Internal theory code string.

    Returns:
        Human-readable label.
    """
    if not code:
        return ""
    # Check direct mapping first
    if code in _THEORY_DISPLAY:
        return _THEORY_DISPLAY[code]
    # SECT7-FN pattern
    m = re.match(r"SECT\d+-F(\d+)", code)
    if m:
        return f"Factor {m.group(1)}"
    # Fallback: humanize
    return code.replace("_", " ").title()


def humanize_field_name(field: str) -> str:
    """Convert snake_case field names to Title Case for display.

    Examples:
        "no_sec_enforcement" -> "No SEC Enforcement"
        "stable_leadership" -> "Stable Leadership"
        "clean_audit" -> "Clean Audit"
        "reasonably_possible" -> "Reasonably Possible"

    Handles special acronyms: SEC, CEO, CFO, IPO, NLP, D&O.
    """
    if not field:
        return ""
    # Split on underscores and title-case
    words = field.replace("_", " ").title()
    # Fix known acronyms that get title-cased incorrectly
    _ACRONYMS = {
        "Sec ": "SEC ", "Ceo ": "CEO ", "Cfo ": "CFO ",
        "Ipo ": "IPO ", "Nlp ": "NLP ", "D&o ": "D&O ",
        "Ar ": "AR ", "Dso ": "DSO ", "Ocf": "OCF",
    }
    for wrong, right in _ACRONYMS.items():
        words = words.replace(wrong, right)
    return words


def _humanize_single_evidence(evidence: str) -> str:
    """Humanize a single evidence fragment (no semicolons)."""
    evidence = evidence.strip()
    if not evidence:
        return ""

    # Strip raw scoring mechanics that should never appear in output
    evidence = re.sub(
        r"Signal-driven scoring:\s*\d+\s*signals?,?\s*coverage=\d+%\.?\s*;?\s*",
        "", evidence,
    ).strip()
    evidence = re.sub(r"^Boolean [Cc]heck:\s*True condition met\.?\s*", "Detected", evidence)
    evidence = re.sub(r"^Boolean [Cc]heck:\s*False condition met\.?\s*", "Not detected", evidence)
    evidence = re.sub(r"^Boolean [Cc]heck:\s*", "", evidence)
    # Strip inference engine jargon
    evidence = re.sub(
        r"Single signal present \([^)]*\)\.\s*Insufficient data for multi-signal pattern detection\.\s*",
        "", evidence,
    )
    evidence = re.sub(r"^False condition met\.?\s*", "Not detected. ", evidence)
    # Strip gap search implementation details
    evidence = re.sub(r"Gap [Ss]earch: keyword match=\w+, query='[^']*'\s*", "Resolved via web search. ", evidence)
    if not evidence:
        return "Detected"

    # Strip leading check name prefix: "Check Name: VALUE..." -> "VALUE..."
    check_prefix = re.match(r"^([A-Za-z][A-Za-z_ \-/&]+):\s*", evidence)
    signal_name = ""
    if check_prefix:
        signal_name = humanize_field_name(check_prefix.group(1))
        evidence = evidence[check_prefix.end():]

    # Pattern: "Value X below/exceeds yellow/red threshold Y"
    m = re.match(
        r"Value\s+([\d.,-]+)\s+(below|exceeds|above)\s+(?:yellow|red|green|blue)\s+threshold\s+([\d.,-]+)",
        evidence,
    )
    if m:
        val, direction, thresh = m.group(1), m.group(2), m.group(3)
        try:
            val_f = float(val)
            val_str = f"{val_f:.2f}" if val_f != int(val_f) else str(int(val_f))
        except ValueError:
            val_str = val
        try:
            thresh_f = float(thresh)
            thresh_str = f"{thresh_f:.2f}" if thresh_f != int(thresh_f) else str(int(thresh_f))
        except ValueError:
            thresh_str = thresh
        # Plain English: "145 detected (elevated vs benchmark of 100)"
        if direction == "exceeds" or direction == "above":
            result = f"{val_str} (elevated vs benchmark of {thresh_str})"
        else:
            result = f"{val_str} (below benchmark of {thresh_str})"
        if signal_name:
            return f"{signal_name}: {result}"
        return result

    # Pattern: "Value X within thresholds" -> "Verified (value: X)"
    m2 = re.match(r"Value\s+([\d.,-]+)\s+within\s+thresholds?", evidence, re.IGNORECASE)
    if m2:
        val = m2.group(1)
        try:
            val_f = float(val)
            val_str = f"{val_f:.2f}" if val_f != int(val_f) else str(int(val_f))
        except ValueError:
            val_str = val
        result = f"Verified (value: {val_str})"
        if signal_name:
            return f"{signal_name}: {result}"
        return result

    # Boolean check (case insensitive)
    if evidence.lower().startswith("boolean check:"):
        result = re.sub(r"^[Bb]oolean [Cc]heck:\s*", "", evidence).strip()
        # "True condition met" -> "Detected", "False condition met" -> "Not detected"
        if result.lower() in ("true condition met", "true", "present"):
            result = "Detected"
        elif result.lower() in ("false condition met", "false", "absent"):
            result = "Not detected"
        # "VIE/SPE structures present" -> keep as-is but capitalize
        result = result[0].upper() + result[1:] if result else result
        if signal_name:
            return f"{signal_name}: {result}"
        return result

    # Pattern: "X at Y signals elevated FACTOR risk" -> "X: Y"
    m_sig = re.match(
        r"(.+?)\s+at\s+([\d.,+-]+)\s+signals?\s+elevated\s+(.+?)(?:\s+risk)?$",
        evidence, re.IGNORECASE,
    )
    if m_sig:
        metric = m_sig.group(1).strip()
        val = m_sig.group(2).strip()
        return f"{metric}: {val}"

    # Pattern: "X signals elevated Y" without "at" -> just show X
    m_sig2 = re.match(
        r"(.+?)\s+signals?\s+elevated\s+(.+?)(?:\s+risk)?$",
        evidence, re.IGNORECASE,
    )
    if m_sig2:
        return m_sig2.group(1).strip()

    # If we extracted a check name but didn't transform the rest, rejoin
    if signal_name:
        return f"{signal_name}: {evidence}"
    return evidence


def humanize_check_evidence(evidence: str) -> str:
    """Clean up raw check evidence text for human display.

    Handles compound evidence with semicolons:
        "Check A: Value 0.2 below yellow threshold 0.5; Check B: Value 0.9 below red threshold 6.0"
    """
    if not evidence:
        return ""
    # Split on semicolons and humanize each part
    parts = [p.strip() for p in evidence.split(";") if p.strip()]
    if len(parts) > 1:
        return "; ".join(_humanize_single_evidence(p) for p in parts)
    return _humanize_single_evidence(evidence)


def strip_cyber_tags(text: str) -> str:
    """Strip [data_breach]/[cyber_attack] category prefixes from text.

    Also strips trailing source tags like "| 2025 Form 10-K | 11".
    """
    if not text:
        return ""
    # Strip leading category tags
    text = re.sub(r"^\[(?:data_breach|cyber_attack|privacy|ransomware)\]\s*", "", text)
    # Strip trailing source tags: | YEAR Form TYPE | NUM (various formats)
    text = re.sub(r"\s*\|\s*\d{4}\s+Form\s+[\w\-/]+\s*\|\s*\d+\s*$", "", text)
    # Also strip inline source tags mid-text
    text = re.sub(r"\s*\|\s*\d{4}\s+Form\s+[\w\-/]+\s*\|\s*\d+", "", text)
    return text.strip()


def humanize_impact(impact: str) -> str:
    """Clean up impact field from exec summary findings.

    Transforms:
        "Positive: no_sec_enforcement" -> "No SEC Enforcement"
        "F7: -4 points" -> "Factor 7: -4 points"
        "F1: 6 pts" -> "Factor 1: 6 pts"
    """
    if not impact:
        return ""
    # Strip "Positive: " or "Negative: " prefix and humanize the field name
    for prefix in ("Positive: ", "Negative: "):
        if impact.startswith(prefix):
            field = impact[len(prefix):]
            return humanize_field_name(field)
    # Factor references: "F7: -4 points" -> "Factor 7: -4 points"
    m = re.match(r"F(\d+):\s*(.*)", impact)
    if m:
        return f"Factor {m.group(1)}: {m.group(2)}"
    return impact


def clean_narrative_text(text: str) -> str:
    """Clean LLM-generated narrative text and add HTML formatting.

    - Strips double-nested HTML bold tags
    - Decodes HTML-entity-encoded tags that shouldn't be there
    - Strips SCREAMING_SNAKE_CASE variable names
    - Bolds key D&O underwriting terms
    - Converts (1)...(2)...(3) numbered items into HTML list
    """
    if not text:
        return ""

    # --- Phase 1: Fix double-encoding and nested tags ---
    # Decode HTML entities that represent tags (e.g., &lt;strong&gt; -> <strong>)
    import html as html_mod
    text = html_mod.unescape(text)

    # Remove double-nested bold: <strong><strong>X</strong></strong> -> <strong>X</strong>
    # Also handles whitespace between nested tags.
    _prev = ""
    while _prev != text:
        _prev = text
        text = re.sub(
            r"<strong>\s*<strong>(.*?)</strong>\s*</strong>",
            r"<strong>\1</strong>",
            text,
            flags=re.DOTALL,
        )

    # Same for <b> tags
    _prev = ""
    while _prev != text:
        _prev = text
        text = re.sub(
            r"<b>\s*<b>(.*?)</b>\s*</b>",
            r"<b>\1</b>",
            text,
            flags=re.DOTALL,
        )

    # Remove mixed nesting: <strong><b>X</b></strong> or <b><strong>X</strong></b>
    text = re.sub(
        r"<strong>\s*<b>(.*?)</b>\s*</strong>",
        r"<strong>\1</strong>",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"<b>\s*<strong>(.*?)</strong>\s*</b>",
        r"<strong>\1</strong>",
        text,
        flags=re.DOTALL,
    )

    # --- Phase 2: Normalize existing formatting ---
    # Replace SCREAMING_SNAKE patterns with Title Case
    def _snake_to_title(m: re.Match) -> str:
        return m.group(0).replace("_", " ").title()

    text = re.sub(r"\b[A-Z][A-Z_]{3,}[A-Z]\b", _snake_to_title, text)

    # Bold key D&O terms (case-insensitive, word-boundary)
    _DO_TERMS = [
        r"D&O", r"securities class action", r"SCA", r"derivative",
        r"Section 10\(b\)", r"Section 11", r"Caremark",
        r"scienter", r"fiduciary duty", r"material weakness",
        r"restatement", r"going.concern", r"DDL",
        r"class period", r"SEC enforcement", r"Wells Notice",
        r"goodwill impairment", r"regulatory exposure",
        r"settlement severity", r"claim frequency",
    ]
    for term in _DO_TERMS:
        text = re.sub(
            rf"(?<!<strong>)(?<!\*\*)\b({term})\b(?!\*\*)(?!</strong>)",
            r"<strong>\1</strong>",
            text,
            flags=re.IGNORECASE,
            count=1,  # Only bold first occurrence
        )

    # Convert (1)...; (2)...; (3)... patterns into HTML list
    # Match: (1) text; (2) text; (3) text
    numbered = re.search(
        r"\(1\)\s+.+?(?:;\s*and\s+\(\d\)|\.\s*$)", text, re.DOTALL
    )
    if numbered:
        # Split on (N) pattern
        items = re.split(r"\(\d+\)\s*", text[numbered.start():])
        items = [i.strip().rstrip(";").rstrip(".").strip() for i in items if i.strip()]
        if len(items) >= 2:
            before = text[:numbered.start()].strip()
            after_match = numbered.end()
            after = text[after_match:].strip() if after_match < len(text) else ""
            list_html = "<ul class='ai-assessment-list'>"
            for item in items:
                # Clean trailing "and" or ";"
                item = re.sub(r";\s*and\s*$", "", item).strip()
                item = item.rstrip(";").strip()
                if item:
                    list_html += f"<li>{item}</li>"
            list_html += "</ul>"
            text = f"{before}{list_html}{after}"

    return text


def humanize_enum(value: str) -> str:
    """Convert SCREAMING_SNAKE or UPPER enum values to Title Case.

    Examples:
        "SAFE" -> "Safe"
        "GREY_ZONE" -> "Grey Zone"
        "DISTRESS" -> "Distress"
        "NOT_APPLICABLE" -> "Not Applicable"

    Returns input unchanged if already in mixed/title case.
    """
    if "_" in value or value.isupper():
        return value.replace("_", " ").title()
    return value


_SOURCE_LABELS: dict[str, str] = {
    "SEC_10K": "10-K",
    "SEC_10Q": "10-Q",
    "SEC_8K": "8-K",
    "SEC_DEF14A": "DEF 14A",
    "SEC_FORM4": "Form 4",
    "SEC_S1": "S-1",
    "SEC_S3": "S-3",
    "SEC_13DG": "SC 13D/G",
    "SEC_ENFORCEMENT": "SEC Enforcement",
    "SEC_FRAMES": "SEC XBRL Frames",
    "MARKET_PRICE": "Market Data",
    "MARKET_SHORT": "Short Interest Data",
    "SCAC_SEARCH": "SCA Database",
    "INSIDER_TRADES": "Insider Trades",
    "REFERENCE_DATA": "Reference Data",
    "WEB_SEARCH": "Web Search",
}

_STATUS_LABELS: dict[str, str] = {
    "DATA_UNAVAILABLE": "Data not available",
    "NOT_AUTO_EVALUATED": "Manual review",
    "MANUAL_ONLY": "Manual review only",
    "FALLBACK_ONLY": "Fallback data",
    "SECTOR_CONDITIONAL": "Sector-specific",
    "DEFERRED": "Data pending",
}


def humanize_source(code: str) -> str:
    """Humanize a data source code for display.

    SEC_FORM4 -> 'Form 4', MARKET_SHORT -> 'Short Interest Data', etc.
    Falls back to title-casing with underscores replaced.
    """
    if not code:
        return ""
    return _SOURCE_LABELS.get(code, _STATUS_LABELS.get(code, code.replace("_", " ").title()))


__all__: list[str] = [
    "humanize_check_evidence",
    "humanize_enum",
    "humanize_field_name",
    "humanize_impact",
    "humanize_source",
    "humanize_theory",
    "humanize_factor",
    "strip_cyber_tags",
]


# ---------------------------------------------------------------------------
# Factor code humanization (F1-F10 → human names)
# ---------------------------------------------------------------------------

_FACTOR_HUMAN_NAMES: dict[str, str] = {
    "F1": "Prior Litigation",
    "F2": "Stock Decline",
    "F3": "Restatement / Audit",
    "F4": "IPO / SPAC / M&A",
    "F5": "Guidance Misses",
    "F6": "Short Interest",
    "F7": "Volatility",
    "F8": "Financial Distress",
    "F9": "Governance",
    "F10": "Officer Stability",
    "F11": "Sector Risk",
}


_EXPOSURE_FACTOR_NAMES: dict[str, str] = {
    "REGULATORY_MULTI_JURISDICTION": "Multi-Jurisdiction Regulatory",
    "EMPLOYMENT_LITIGATION_RISK": "Employment Litigation",
    "TRANSACTION_LITIGATION_RISK": "Transaction Litigation",
    "IP_LITIGATION_RISK": "IP Litigation",
    "ENVIRONMENTAL_LITIGATION_RISK": "Environmental Litigation",
    "PRODUCT_LIABILITY_RISK": "Product Liability",
    "ANTITRUST_RISK": "Antitrust",
    "DATA_PRIVACY_RISK": "Data Privacy",
    "CYBERSECURITY_RISK": "Cybersecurity",
}


def humanize_factor(factor_id: str) -> str:
    """Convert factor code (F1-F11) or exposure factor enum to human-readable name.

    Returns the human name if known, otherwise converts SCREAMING_SNAKE_CASE to Title Case.
    """
    if not factor_id:
        return ""
    # Handle case where it's already a human name
    if factor_id in _FACTOR_HUMAN_NAMES.values():
        return factor_id
    # Check scoring factor codes (F1-F11)
    if factor_id in _FACTOR_HUMAN_NAMES:
        return _FACTOR_HUMAN_NAMES[factor_id]
    # Check D&O exposure factor enums
    if factor_id in _EXPOSURE_FACTOR_NAMES:
        return _EXPOSURE_FACTOR_NAMES[factor_id]
    # Fallback: convert SCREAMING_SNAKE_CASE to Title Case
    if "_" in factor_id and factor_id == factor_id.upper():
        return factor_id.replace("_", " ").title()
    return factor_id
