"""Number and citation formatting utilities for document rendering.

Provides consistent formatting for currency, percentages, compact numbers,
dates, SourcedValue citations, and v2 table/risk/change utilities
across all section renderers.

Numeric/HTML formatters were extracted to formatters_numeric.py (Plan 43-03)
to keep this file under 500 lines. Backward-compat re-exports below ensure
all existing import sites continue to work unchanged.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TypeVar

from markupsafe import Markup

from do_uw.models.common import SourcedValue
from do_uw.stages.render.formatters_humanize import (
    clean_narrative_text,
    humanize_check_evidence,
    humanize_enum,
    humanize_factor,
    humanize_field_name,
    humanize_impact,
    humanize_source,
    humanize_theory,
    strip_cyber_tags,
)

# Backward-compat re-exports -- do NOT remove (import sites depend on these)
from do_uw.stages.render.formatters_numeric import (
    _NA_HTML,
    EMPLOYEE_SPECTRUM,
    MARKET_CAP_SPECTRUM,
    REVENUE_SPECTRUM,
    YEARS_PUBLIC_SPECTRUM,
    _compact_number,
    compute_spectrum_position,
    format_adaptive,
    format_currency,
    format_currency_accounting,
    format_em_dash,
    format_percentage,
    format_yoy_html,
)

_T = TypeVar("_T")

# Regex for SEC filing suffixes like /DE/, /NV/, /MD/, etc.
import re

_SEC_SUFFIX_RE = re.compile(r"\s*/[A-Z]{2,3}/?\s*$")


def safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float safely, handling 'N/A', '%' strings, and junk.

    Handles: None, 'N/A', '13.2%', concatenated strings, non-numeric garbage.
    Returns *default* on any conversion failure.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("n/a", "none", "null", "-", "—"):
        return default
    # Strip common suffixes like % before trying
    s = s.replace(",", "").replace("%", "").strip()
    # Extract first number-like pattern
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if m:
        return float(m.group())
    return default


def clean_company_name(raw: str) -> str:
    """Clean SEC-format company name for display.

    Strips state-of-incorporation suffixes (/DE/, /NV/, etc.) and
    converts ALL-CAPS names to title case while preserving known
    acronyms and Roman numerals.
    """
    if not raw:
        return raw
    # Strip SEC suffix (e.g., "/DE/")
    name = _SEC_SUFFIX_RE.sub("", raw).strip()
    # Title-case if all caps (SEC filing format)
    if name == name.upper() and len(name) > 3:
        name = _title_case_company(name)
    return name


def _title_case_company(name: str) -> str:
    """Smart title case that preserves acronyms and common patterns."""
    # True acronyms (stay ALL CAPS)
    _ACRONYMS = {
        "LLC", "LP", "LLP", "PLC", "SA", "NV", "AG", "SE", "AB",
        "USA", "US", "UK", "RPM", "IBM", "HP", "GE", "AMD",
        "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII",
    }
    # Corporate suffixes (title case with period)
    _CORP_SUFFIX = {"INC": "Inc.", "CORP": "Corp.", "CO": "Co.", "LTD": "Ltd."}
    # Lowercase words (after first word)
    _LOWER = {"of", "the", "and", "in", "for", "de", "du", "von", "van", "al"}

    words = name.split()
    result = []
    for i, w in enumerate(words):
        upper = w.upper().rstrip(".,;")
        trailing = w[len(upper):]  # preserve trailing punctuation
        if upper in _CORP_SUFFIX:
            result.append(_CORP_SUFFIX[upper])
        elif upper in _ACRONYMS:
            result.append(upper + trailing)
        elif i > 0 and w.lower() in _LOWER:
            result.append(w.lower())
        else:
            # Handle hyphenated words (e.g., FREEPORT-MCMORAN -> Freeport-McMoRan)
            result.append(_capitalize_word(w))
    return " ".join(result)


def _capitalize_word(word: str) -> str:
    """Capitalize a word, handling hyphens and ampersands."""
    if "-" in word:
        return "-".join(_capitalize_word(part) for part in word.split("-"))
    if "&" in word:
        parts = word.split("&")
        return "&".join(p.upper() if len(p) <= 2 else p.capitalize() for p in parts)
    return word.capitalize()


def format_number(value: float | int | None, decimals: int = 0) -> str:
    """Format a number with commas.

    Args:
        value: Numeric value, or None.
        decimals: Number of decimal places.

    Returns:
        Formatted string like "1,234,567", or "N/A" for None.
    """
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_compact(value: float | None) -> str:
    """Format a large number in compact notation.

    Args:
        value: Numeric value, or None.

    Returns:
        Formatted string like "1.2B", "345M", "12K", or "N/A" for None.
    """
    if value is None:
        return "N/A"
    return _compact_number(value)


def format_date(dt: datetime | None, fmt: str = "%Y-%m-%d") -> str:
    """Format a datetime as a string.

    Args:
        dt: Datetime value, or None.
        fmt: strftime format string.

    Returns:
        Formatted date string, or "N/A" for None.
    """
    if dt is None:
        return "N/A"
    return dt.strftime(fmt)


def format_citation(sv: SourcedValue[Any]) -> str:
    """Format a SourcedValue as a citation string.

    Args:
        sv: A SourcedValue with source, as_of, and confidence fields.

    Returns:
        String like "[SEC 10-K, 2024-12-31, HIGH]".
    """
    date_str = sv.as_of.strftime("%Y-%m-%d")
    return f"[{sv.source}, {date_str}, {sv.confidence}]"


def format_sourced_value(
    value: Any, sv: SourcedValue[Any] | None
) -> tuple[str, str]:
    """Format a value with its citation.

    Args:
        value: The display value.
        sv: Optional SourcedValue for citation. If None, no citation.

    Returns:
        Tuple of (formatted_value, citation_string). Citation is ""
        if sv is None.
    """
    formatted = str(value)
    if sv is None:
        return (formatted, "")
    return (formatted, format_citation(sv))


def na_if_none(value: Any, fallback: str = "N/A") -> str:
    """Return string representation or fallback for None values.

    Args:
        value: Any value.
        fallback: String to return if value is None.

    Returns:
        str(value) or fallback if value is None.
    """
    if value is None:
        return fallback
    return str(value)


# ---------------------------------------------------------------------------
# V2 formatter utilities
# ---------------------------------------------------------------------------


def format_source_trail(sv: SourcedValue[Any]) -> str:
    """Produce a full source attribution string for a SourcedValue.

    More detailed than format_citation, includes filing section when
    the source string contains it (e.g. "SEC 10-K, Item 7").

    Returns:
        String like "[SEC 10-K, filed 2024-02-15, Item 7, HIGH confidence]".
    """
    date_str = sv.as_of.strftime("%Y-%m-%d")
    source = sv.source
    # Attempt to extract filing section from source string
    section = ""
    for marker in ("Item 1", "Item 7", "Item 8", "Item 9", "DEF 14A"):
        if marker in source:
            section = f", {marker}"
            # Remove marker from source to avoid duplication
            source = source.replace(f", {marker}", "").replace(marker, "").strip()
            if source.endswith(","):
                source = source[:-1].strip()
            break
    return f"[{source}, filed {date_str}{section}, {sv.confidence} confidence]"



def format_risk_level(level: str) -> str:
    """Standardize risk level display with consistent casing.

    Returns one of: "CRITICAL", "ELEVATED", "MODERATE", "LOW", "HIGH",
    or the input uppercased if not recognized. Emoji-free per branding.
    """
    canonical = level.strip().upper()
    known = {"CRITICAL", "HIGH", "ELEVATED", "MODERATE", "LOW", "NEUTRAL"}
    if canonical in known:
        return canonical
    return canonical


def format_date_range(
    start: str | None, end: str | None,
) -> str:
    """Format a date range for class periods, SOL windows, etc.

    Parses ISO dates (YYYY-MM-DD) into "Jan 2023 - Mar 2024" format.
    Returns "N/A" if both are None.
    """
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    def _fmt(d: str | None) -> str | None:
        if not d:
            return None
        try:
            parts = d.split("-")
            yr = parts[0]
            mo = int(parts[1]) if len(parts) >= 2 else 0
            if 1 <= mo <= 12:
                return f"{months[mo - 1]} {yr}"
            return yr
        except (ValueError, IndexError):
            return d

    s = _fmt(start)
    e = _fmt(end)
    if s and e:
        return f"{s} - {e}"
    if s:
        return f"{s} - present"
    if e:
        return f"through {e}"
    return "N/A"


def format_compact_table_value(
    value: float | int | None,
    is_currency: bool = False,
    is_pct: bool = False,
) -> str:
    """Single function for table cell formatting.

    Handles None, negative values, compact notation for currencies,
    and percentage formatting. Reduces boilerplate in section renderers.
    """
    if value is None:
        return "N/A"
    if is_pct:
        return f"{value:.1f}%"
    if is_currency:
        return format_currency(safe_float(value), compact=True)
    # Default numeric with commas
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.1f}"


def sv_val(
    sv: SourcedValue[_T] | None, default: _T | str = "N/A",
) -> _T | str:
    """Safely extract .value from a SourcedValue or return default.

    More ergonomic than na_if_none for typed SourcedValue access.
    """
    if sv is None:
        return default
    return sv.value


def sector_display_name(sector_code: str) -> str:
    """Convert a sector code to a human-readable display name.

    Uses the same mappings as sectors.json sector_codes.mappings.
    Falls back to titlecase of the code if not recognized.

    Args:
        sector_code: Short sector code like "TECH", "COMM", "HLTH".

    Returns:
        Human-readable name like "Technology", "Communication Services".
    """
    _SECTOR_NAMES: dict[str, str] = {
        "TECH": "Technology",
        "HLTH": "Healthcare",
        "BIOT": "Biotech/Pharma",
        "FINS": "Financials",
        "INDU": "Industrials",
        "ENGY": "Energy",
        "CONS": "Consumer Discretionary",
        "STPL": "Consumer Staples",
        "MATL": "Materials",
        "UTIL": "Utilities",
        "REIT": "Real Estate",
        "COMM": "Communications",
        "TELE": "Telecom",
        "BDCS": "Business Development Companies",
        "SPEC": "Speculative/Cannabis",
        "DEFAULT": "Diversified",
    }
    return _SECTOR_NAMES.get(sector_code, sector_code.title())


def format_change_indicator(
    current: float, prior: float,
) -> str:
    """Format YoY change with direction indicator.

    Returns "+12.3%" or "-5.7%". No color codes (those are
    handled at rendering layer). Uses simple text arrows.
    """
    if prior == 0:
        return "N/A (no prior)"
    change = ((current - prior) / abs(prior)) * 100
    if change > 0:
        return f"+{change:.1f}%"
    if change < 0:
        return f"{change:.1f}%"
    return "0.0%"


# ---------------------------------------------------------------------------
# HTML-specific formatters (format_na stays here; HTML formatters in _numeric)
# ---------------------------------------------------------------------------


def format_na(value: Any) -> str | Markup:
    """Render None as gray italic N/A HTML, otherwise str(value).

    For consistent gray italic N/A display across all HTML templates.
    Returns Markup for the N/A span so Jinja2 autoescape does not
    double-escape the HTML tags.

    Args:
        value: Any value.

    Returns:
        Markup-safe HTML string -- gray italic N/A for None, str(value) otherwise.
    """
    if value is None or value == "None":
        return Markup(_NA_HTML)
    return str(value)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def format_percentile(rank: float) -> str:
    """Format a percentile rank as a human-readable ordinal string.

    Args:
        rank: Percentile rank 0-100.

    Returns:
        Formatted string like "92nd percentile".
    """
    from do_uw.stages.render.peer_context import _ordinal

    return f"{_ordinal(int(round(rank)))} percentile"





# ---------------------------------------------------------------------------
# Narrative boilerplate safety net
# ---------------------------------------------------------------------------

# Patterns that indicate generic narrative phrasing. If any slip through
# the upstream generators, strip_boilerplate logs a warning.
_BOILERPLATE_RX: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"has experienced a notable",
        r"the company has shown",
        r"demonstrates a commitment to",
        r"is positioned to",
        r"may impact future",
        r"faces potential challenges",
        r"has maintained a strong",
        r"continues to demonstrate",
        r"reflects the company's",
        r"underscores the importance",
        r"it is worth noting",
        r"it should be noted",
        r"given the current landscape",
        r"in the current environment",
        r"going forward(?![\w-])",
        r"moving forward",
        r"remains to be seen",
        r"time will tell",
        r"has shown a trend",
        r"the company has exhibited",
        r"warrants?\s+(?:further\s+)?underwriting\s+attention",
        r"warrants?\s+(?:further\s+)?investigation",
        r"historically correlated with",
        r"contributes? to the overall risk profile",
    )
]

_boilerplate_logger = logging.getLogger(f"{__name__}.boilerplate")


def strip_boilerplate(text: str) -> str:
    """Detect and log boilerplate phrases in narrative text.

    This is a **safety net**, not a replacement for fixing upstream
    generators.  It scans *text* for known generic phrases and logs
    a warning for each match so they can be traced back to the source.

    Returns the original text unchanged (does not mutate content).
    """
    for rx in _BOILERPLATE_RX:
        m = rx.search(text)
        if m:
            _boilerplate_logger.warning(
                "Boilerplate detected in narrative: '%s'", m.group(),
            )
    return text


# Exact boilerplate phrase from brain YAML do_context that adds no analytical value
_DO_CONTEXT_BOILERPLATE = (
    "Monitor for deterioration \u2014 trend direction and "
    "peer comparison inform the D&O risk assessment."
)


def clean_do_context(text: str) -> str:
    """Strip generic boilerplate from brain YAML do_context text.

    Brain signals often append 'Monitor for deterioration -- trend direction
    and peer comparison inform the D&O risk assessment.' which adds zero
    analytical value. This function strips that phrase and returns the
    remaining meaningful content.
    """
    if not text:
        return ""
    result = text.replace(_DO_CONTEXT_BOILERPLATE, "").strip()
    return result


import re as _re

# Pre-compiled regex for stripping "triggered SIGNAL_NAME (FN, ...) —" prefix from do_context
_TRIGGERED_PREFIX_RE = _re.compile(
    r"triggered\s+[^—]+—\s*",
)

# Factor code patterns: "F.7 = 5/8", "F1 = 3/10", "(F.7)", "(F1, F4)", "F3/F6", "factors F1, F3" etc.
_FACTOR_CODE_RE = _re.compile(
    r"\(?F\.?\d{1,2}\s*=\s*[\d.]+/\d+\)?\.?\s*",
)
_FACTOR_REF_RE = _re.compile(
    r"\(F\.?\d{1,2}(?:[,/]\s*F\.?\d{1,2})*\)\s*",
)
# Bare "F3/F6" or "F1, F3" without parentheses (in prose)
_FACTOR_BARE_RE = _re.compile(
    r"F\.?\d{1,2}(?:[,/]\s*F\.?\d{1,2})+",
)
# "affecting factors F1, F3" or "factors F1, F3"
_FACTOR_AFFECTING_RE = _re.compile(
    r",?\s*affecting\s+factors?\s+F\.?\d{1,2}(?:[,\s]+F\.?\d{1,2})*\.?",
)

# Threshold context patterns: "(threshold: Cash Ratio <0.5 OR ...)" etc.
_THRESHOLD_RE = _re.compile(r"\s*\(threshold:[^)]*\)")

# "N signals triggered" / "N of M signals triggered" / "N brain signal(s) triggered..."
# Safety net: rewrite to human-readable or strip entirely.
_SIGNALS_TRIGGERED_RE = _re.compile(
    r"\d+\s+(?:brain\s+)?signals?\(?s?\)?\s+triggered(?:\s+in\s+this\s+category)?:\s*",
)
_SIGNALS_TRIGGERED_BARE_RE = _re.compile(
    r"\d+\s+(?:brain\s+)?signals?\(?s?\)?\s+triggered(?:\s+in\s+this\s+category)?",
)

# Jargon phrases that leak from brain YAML into rendered output
_JARGON_PHRASES = [
    "this agent risk (executive/director actions and decisions that create D&O exposure)",
    "this host risk (company-level conditions that attract D&O claims)",
    "this agent risk",
    "this host risk",
    "Signal-driven scoring:",
    "coverage=100%",
    "Evidence: Boolean check:",
    "Boolean check:",
    "(company-level characteristics that attract or deter D&O claims)",
    "(executive/director actions and decisions that create D&O exposure)",
    "Executive risk threshold from D&O claims experience and SCAC defendant analysis.",
    "from D&O underwriting practice and claims experience.",
    "from D&O underwriting practice and claims experience",
    "from D&O claims experience and SCAC defendant analysis",
    "indicates Litigation History / Settlement Patterns.",
    "IPO/offering exposure windows create Section 11/12 liability under the Securities Act of 1933. These strict liability claims require no scienter proof and have lower dismissal rates than 10b-5 claims.",
    "Unexplained stock drops suggest information leakage or market discovery of undisclosed problems. Drops without corresponding public disclosure create the strongest inference that management withheld material information.",
    "Idiosyncratic volatility separates company-specific risk from market factors. High idiosyncratic volatility indicates company-specific information is driving price action -- supporting loss causation in SCA complaints.",
    "indicates Litigation History / Settlement Patterns",
    "Execution mode is MANUAL_ONLY, not AUTO",
    "No field_key in data_strategy",
    "False condition met",
]

# Pattern for "indicates <JargonCategory>" phrases — category names may include
# lowercase words like "of" (e.g., "Governance Failures / Breach of Fiduciary Duty")
_INDICATES_JARGON_RE = _re.compile(
    r"\s*indicates\s+[A-Z][a-z]+(?:\s+[A-Za-z]+){0,6}\s*/\s*[A-Z][a-z]+(?:\s+[A-Za-z]+){0,6}\s*\.?",
)

# Regex patterns for system jargon that needs context-aware removal
_THRESHOLD_JARGON_RE = _re.compile(
    r"Thresholds?\s*\((?:RED|YELLOW|GREEN)\s*:\s*<?[^)]+\)",
)
_CHECK_COUNT_RE = _re.compile(
    r"\d+/\d+\s+checks?\s+clear\s+\(\d+%\)\s+across\s+",
)
_CHANNEL_STUFFING_RE = _re.compile(
    r"Channel Stuffing Indicators?:\s*[\d.]+",
)
_MENTION_COUNT_RE = _re.compile(
    r"(\d+)\s+mention\(s\):\s*",
)

# "caution zone" rewriter — replaces generic brain YAML D&O commentary with
# specific litigation theory context that an underwriter can act on.
# Pattern: "{signal} at {value} is in the caution zone for {category} (FN)."
_CAUTION_ZONE_RE = _re.compile(
    r"is in the caution zone for\s+([^.()]+?)(?:\s*\([^)]*\))?\s*\.",
)
_CAUTION_ZONE_REWRITES: dict[str, str] = {
    "Litigation History": (
        "— elevated prior litigation increases frequency expectations. "
        "Plaintiffs' bar monitors repeat defendants for pattern claims."
    ),
    "Settlement Patterns": (
        "— elevated prior litigation increases frequency expectations. "
        "Plaintiffs' bar monitors repeat defendants for pattern claims."
    ),
    "Stock Decline": (
        "— stock decline creates measurable damages for 10b-5 claims. "
        "Dollar-Day Loss (DDL) quantifies investor exposure during the class period."
    ),
    "Securities Fraud": (
        "— stock movement patterns may support scienter inference in SCA complaints. "
        "Corrective disclosure theory ties stock drops to alleged misstatements."
    ),
    "Financial Irregularities": (
        "— financial metric anomaly may indicate earnings quality issues. "
        "Restatement-related SCAs carry higher settlement severity (2-3x median)."
    ),
    "Restatement Risk": (
        "— financial metric anomaly may indicate earnings quality issues. "
        "Restatement-related SCAs carry higher settlement severity (2-3x median)."
    ),
    "Emerging Risk": (
        "— governance or operational risk that could crystallize into D&O exposure. "
        "Early-stage indicators warrant monitoring for acceleration."
    ),
    "Forward-Looking Exposure": (
        "— governance or operational risk that could crystallize into D&O exposure. "
        "Early-stage indicators warrant monitoring for acceleration."
    ),
}


def _rewrite_caution_zone(text: str) -> str:
    """Replace 'is in the caution zone for X' with actionable D&O context."""
    def _replacer(m: _re.Match[str]) -> str:
        category = m.group(1).strip()
        # Try matching each key as a substring of the category
        for key, replacement in _CAUTION_ZONE_REWRITES.items():
            if key.lower() in category.lower():
                return replacement
        # Fallback: just remove the generic text
        return "."
    return _CAUTION_ZONE_RE.sub(_replacer, text)


def strip_jargon(text: str) -> str:
    """Strip known brain YAML jargon patterns from rendered text.

    Removes:
    - 'triggered SIGNAL_NAME (FN, FN) —' prefixes
    - 'this agent risk (...)' / 'this host risk (...)' phrases
    - 'Monitor for deterioration ...' boilerplate
    - 'Signal-driven scoring:' / 'coverage=100%' internals

    Safe to apply to any text — returns unchanged if no jargon found.
    """
    if not isinstance(text, str) or not text:
        return text or ""
    result = text
    # Rewrite "caution zone" boilerplate FIRST (before stripping other patterns)
    if "caution zone" in result:
        result = _rewrite_caution_zone(result)
    # Strip "Monitor for deterioration" boilerplate
    result = result.replace(_DO_CONTEXT_BOILERPLATE, "")
    # Strip "triggered X (FN) —" prefix
    result = _TRIGGERED_PREFIX_RE.sub("", result)
    # Strip factor codes: "F.7 = 5/8", "(F1, F4)", "F3/F6", "affecting factors F1, F3"
    result = _FACTOR_CODE_RE.sub("", result)
    result = _FACTOR_REF_RE.sub("", result)
    result = _FACTOR_AFFECTING_RE.sub("", result)
    result = _FACTOR_BARE_RE.sub("", result)
    # Strip "(threshold: ...)" internal context
    result = _THRESHOLD_RE.sub("", result)
    # Strip "N signals triggered: ..." — rewrite to keep the list but drop jargon prefix
    # e.g. "19 signals triggered: litigation history, subsidiary count" → "litigation history, subsidiary count"
    result = _SIGNALS_TRIGGERED_RE.sub("", result)
    # Strip bare "N signals triggered" with no trailing list (entire phrase is jargon)
    result = _SIGNALS_TRIGGERED_BARE_RE.sub("", result)
    # Strip known jargon phrases (longer phrases first to avoid partial matches)
    for phrase in _JARGON_PHRASES:
        result = result.replace(phrase, "")
    # Strip "Signal-driven scoring: N signals, coverage=X%" full pattern
    result = _re.sub(r"Signal-driven scoring:\s*\d+\s*signals?,?\s*coverage=\d+%\.?", "", result)
    # Strip orphan "coverage=N%" fragments
    result = _re.sub(r"coverage=\d+%\.?", "", result)
    # Strip threshold jargon: "Thresholds (RED: < 0.5; YELLOW: < 0.8)"
    result = _THRESHOLD_JARGON_RE.sub("", result)
    # Strip check count jargon: "6/33 checks clear (18%) across"
    result = _CHECK_COUNT_RE.sub("", result)
    # Strip "X at Y signals elevated Z risk" pattern
    result = _re.sub(
        r"\b\w[\w\s/()]+\s+at\s+[\d.,+-]+\s+signals?\s+elevated\s+[\w\s/]+risk\s*\.?\s*",
        "", result,
    )
    # Strip raw metric dumps: "Channel Stuffing Indicators: 0.1191"
    result = _CHANNEL_STUFFING_RE.sub("", result)
    # Rewrite mention counts: "2 mention(s): text" → "text"
    result = _MENTION_COUNT_RE.sub("", result)
    # Strip "indicates Category / Subcategory" internal references
    result = _INDICATES_JARGON_RE.sub("", result)
    # Deduplicate repeated sentences within the same text
    sentences = result.split(". ")
    if len(sentences) > 2:
        seen: set[str] = set()
        deduped: list[str] = []
        for s in sentences:
            key = s.strip().lower()[:60]
            if key not in seen or len(key) < 20:
                seen.add(key)
                deduped.append(s)
        result = ". ".join(deduped)
    # Round raw floats with >4 decimal places (e.g., 61.53846153846154 → 61.54)
    def _round_raw_float(m: _re.Match[str]) -> str:
        try:
            return f"{float(m.group(0)):.2f}".rstrip("0").rstrip(".")
        except ValueError:
            return m.group(0)

    result = _re.sub(r"\b\d+\.\d{4,}\b", _round_raw_float, result)
    # Clean up leftover artifacts: double spaces, leading/trailing punctuation
    result = _re.sub(r"\s{2,}", " ", result).strip()
    # Strip leading " indicates " that remains after removing prefix+jargon
    result = _re.sub(r"^indicates\s+", "", result).strip()
    # Capitalize first letter if it became lowercase after stripping
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    return result


__all__ = [
    "EMPLOYEE_SPECTRUM",
    "MARKET_CAP_SPECTRUM",
    "REVENUE_SPECTRUM",
    "YEARS_PUBLIC_SPECTRUM",
    "clean_do_context",
    "compute_spectrum_position",
    "format_adaptive",
    "format_change_indicator",
    "format_citation",
    "format_compact",
    "format_compact_table_value",
    "format_currency",
    "format_currency_accounting",
    "format_date",
    "format_date_range",
    "format_em_dash",
    "format_na",
    "format_number",
    "format_percentage",
    "format_percentile",
    "format_risk_level",
    "format_source_trail",
    "format_sourced_value",
    "format_yoy_html",
    "humanize_check_evidence",
    "humanize_enum",
    "humanize_field_name",
    "humanize_impact",
    "humanize_theory",
    "na_if_none",
    "safe_float",
    "sector_display_name",
    "strip_boilerplate",
    "strip_cyber_tags",
    "strip_jargon",
    "sv_val",
]
