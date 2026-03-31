"""Text-based debt structure and refinancing risk extraction.

Parses 10-K filing text for debt maturity schedules, interest rate
details, covenant information, credit facility terms, and computes
refinancing risk from parsed data plus liquidity.

Sources: Item 7 MD&A, then full 10-K Note section containing "Debt"
(e.g., Note 9) which typically has the maturity schedule table,
interest rate ranges, and credit facility details.

Covers SECT3-10 (Debt Structure) and SECT3-11 (Refinancing Risk).
Split from debt_analysis.py to stay under 500-line limit.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_texts,
    get_filings,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# "$X million due/maturing YYYY"
_MATURITY_AMOUNT_RE = re.compile(
    r"\$\s*([\d,.]+)\s*(?:million|billion|thousand)?"
    r"\s*(?:due|matur(?:es?|ing))\s+(?:in\s+)?(\d{4})",
    re.IGNORECASE,
)
# "X.XX% ... Notes due ... YYYY" — captures rate and year together.
_NOTES_DUE_RE = re.compile(
    r"(\d+\.?\d*)\s*%\s+.*?"
    r"(?:Notes?|Bonds?|Debentures?)"
    r"\s+(?:due|matur\w*)\s+(?:in\s+)?(\d{4})",
    re.IGNORECASE,
)
# Table-style maturity row: "2026 $ 1 $ 1,575 $ 1,576".
# Text may lack newlines (SEC filings normalize to single line).
# Captures year + content up to next year/Thereafter/Total.
_MATURITY_TABLE_ROW_RE = re.compile(
    r"(20[2-3]\d)\s+(.+?)(?=20[2-3]\d\s|Thereafter\s|Total\s)",
)
_INTEREST_RATE_RE = re.compile(
    r"(\d+\.?\d*)\s*%\s*(?:per\s+annum|interest|coupon|rate)?",
    re.IGNORECASE,
)
# Rate range: "4.70 - 6.57 %" (common in SEC filing tables).
_RATE_RANGE_RE = re.compile(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*%")
_FLOATING_RATE_RE = re.compile(
    r"(?:SOFR|LIBOR|SONIA|EURIBOR|Loan\s+Prime\s+Rate"
    r"|floating|variable)\s*(?:\+|plus|minus)?\s*(\d+\.?\d*)?\s*%?",
    re.IGNORECASE,
)
_COVENANT_RE = re.compile(
    r"(?:financial|debt)\s+covenant"
    r"|covenant\s+(?:ratio|requirement|test)"
    r"|(?:material\s+)?compliance\s+with\s+.*?covenant",
    re.IGNORECASE,
)
_CREDIT_FACILITY_RE = re.compile(
    r"(?:revolving\s+credit|credit\s+(?:agreement|facility))"
    r".*?\$\s*([\d,.]+)\s*(?:million|billion)?",
    re.IGNORECASE,
)
# Alt: "commitment of up to $X billion" or "facility of $X billion".
_CREDIT_FACILITY_RE_ALT = re.compile(
    r"(?:commitment|facility)\s+(?:of\s+)?(?:up\s+to\s+)?"
    r"\$\s*([\d,.]+)\s*(million|billion)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv_any(
    value: dict[str, Any],
    source: str,
    confidence: Confidence = Confidence.MEDIUM,
) -> SourcedValue[dict[str, Any]]:
    """Create a SourcedValue wrapping a dict of mixed types."""
    return SourcedValue[dict[str, Any]](
        value=value, source=source, confidence=confidence,
        as_of=datetime.now(tz=UTC),
    )


def _safe_divide(
    num: float | None, den: float | None
) -> float | None:
    """Divide with None and zero-denominator safety."""
    if num is None or den is None or den == 0.0:
        return None
    return num / den


def _parse_year(year_str: str) -> int | None:
    """Parse a year string to int, returning None on failure."""
    try:
        return int(year_str)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Note section extraction from full 10-K text
# ---------------------------------------------------------------------------


def _extract_note_section(
    full_text: str, note_keyword: str
) -> str | None:
    """Extract a numbered note section (e.g. "Note 9 - Debt") from 10-K.

    Returns text from the heading to the next Note heading, or None.
    """
    heading_re = re.compile(
        r"Note\s+(\d+)\s*[\u2013\u2014\-]+\s*" + re.escape(note_keyword),
        re.IGNORECASE,
    )
    match = heading_re.search(full_text)
    if match is None:
        return None
    note_num = int(match.group(1))
    start = match.start()
    next_re = re.compile(
        r"Note\s+" + str(note_num + 1) + r"\s*[\u2013\u2014\-]",
        re.IGNORECASE,
    )
    next_match = next_re.search(full_text, start + 50)
    end = next_match.start() if next_match else start + 15000
    return full_text[start:end]


# ---------------------------------------------------------------------------
# Sub-parsers
# ---------------------------------------------------------------------------


def _parse_maturity_schedule(text: str) -> dict[str, float]:
    """Parse inline maturity patterns ("$200 million matures in 2026")."""
    schedule: dict[str, float] = {}
    for m in _MATURITY_AMOUNT_RE.finditer(text):
        try:
            schedule[m.group(2)] = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
    # "X.XX% Notes due YYYY" — year without inline dollar amount.
    for m in _NOTES_DUE_RE.finditer(text):
        if m.group(2) not in schedule:
            schedule[m.group(2)] = 0.0
    return schedule


def _parse_maturity_table(text: str) -> dict[str, float]:
    """Parse tabular maturity schedule ("2026 $ 1 $ 1,575 $ 1,576").

    Finds "Schedule of Principal Maturities" and extracts year rows
    where the last numeric value on each row is the total.
    """
    idx = text.lower().find("principal maturities")
    if idx < 0:
        return {}
    section = text[idx : idx + 1500]
    schedule: dict[str, float] = {}
    for m in _MATURITY_TABLE_ROW_RE.finditer(section):
        year = m.group(1)
        nums = re.findall(r"[\d,]+", m.group(2))
        amounts: list[float] = []
        for n in nums:
            clean = n.replace(",", "").strip()
            if clean:
                try:
                    amounts.append(float(clean))
                except ValueError:
                    continue
        if amounts:
            schedule[year] = amounts[-1]
    return schedule


def _parse_credit_facility(text: str) -> float | None:
    """Extract credit facility amount from filing text.

    Tries the more specific "commitment/facility of $X billion"
    pattern first to avoid false matches on tabular data.
    """
    # Prefer the specific pattern (avoids greedy .*? across tables).
    alt = _CREDIT_FACILITY_RE_ALT.search(text)
    if alt:
        try:
            amount = float(alt.group(1).replace(",", ""))
            if alt.group(2).lower() == "billion":
                amount *= 1000.0
            return amount
        except ValueError:
            pass
    # Fall back to "revolving credit ... $X".
    match = _CREDIT_FACILITY_RE.search(text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _parse_interest_rates(text: str) -> dict[str, Any]:
    """Parse fixed and floating interest rate information."""
    fixed_rates: list[float] = []
    # Rate ranges: "4.70 - 6.57 %" — add both endpoints.
    for m in _RATE_RANGE_RE.finditer(text):
        for grp in (1, 2):
            try:
                rate = float(m.group(grp))
                if 0.0 < rate < 30.0:
                    fixed_rates.append(rate)
            except ValueError:
                continue
    # Individual rates: "4.5% per annum".
    for m in _INTEREST_RATE_RE.finditer(text):
        try:
            rate = float(m.group(1))
            if 0.0 < rate < 30.0:
                fixed_rates.append(rate)
        except ValueError:
            continue
    floating_refs = [
        m.group(0).strip() for m in _FLOATING_RATE_RE.finditer(text)
    ]
    return {
        "fixed_rates": sorted(set(fixed_rates)),
        "floating_rates": floating_refs,
        "has_floating": len(floating_refs) > 0,
    }


# ---------------------------------------------------------------------------
# SECT3-10: Debt Structure (text-based extraction)
# ---------------------------------------------------------------------------


def extract_debt_structure(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Extract debt structure from 10-K filing text.

    Tries the debt footnote (Note N) from the full 10-K text first,
    falling back to Item 7 MD&A. Parses maturity schedule, interest
    rates, covenants, and credit facility details.
    """
    expected = [
        "maturity_schedule", "interest_rates", "covenants",
        "credit_facility",
    ]
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "N/A"

    # Item 7 / MD&A text
    filings = get_filings(state)
    filing_texts = get_filing_texts(filings)
    item7_text: str | None = None
    for key in ("item7", "10-K_item7", "item_7", "mda"):
        raw = filing_texts.get(key)
        if raw is not None and isinstance(raw, str) and len(raw) > 100:
            item7_text = raw
            source_filing = f"10-K {key}"
            break

    # Debt note section from full 10-K text (e.g. Note 9 - Debt).
    note_text: str | None = None
    full_10k = get_filing_document_text(state, "10-K")
    if full_10k:
        note_text = _extract_note_section(full_10k, "Debt")
        if note_text is not None:
            source_filing = "10-K Note (Debt)"

    # Prefer note text (has tables + detail), fall back to item7.
    primary_text = note_text or item7_text
    if primary_text is None:
        return None, create_report(
            extractor_name="debt_structure", expected=expected,
            found=found, source_filing=source_filing,
            warnings=["No filing text available for debt extraction"],
        )

    result: dict[str, Any] = {}

    # 1. Maturity schedule — try table format first, then inline.
    sched = _parse_maturity_table(primary_text)
    if not sched:
        sched = _parse_maturity_schedule(primary_text)
    if not sched and item7_text and item7_text != primary_text:
        sched = _parse_maturity_schedule(item7_text)
    result["maturity_schedule"] = sched
    if sched:
        found.append("maturity_schedule")
    else:
        warnings.append("Could not parse maturity schedule from filing text")

    # 2. Interest rates
    rates = _parse_interest_rates(primary_text)
    if (
        not rates.get("fixed_rates")
        and not rates.get("floating_rates")
        and item7_text and item7_text != primary_text
    ):
        rates = _parse_interest_rates(item7_text)
    result["interest_rates"] = rates
    if rates.get("fixed_rates") or rates.get("floating_rates"):
        found.append("interest_rates")

    # 3. Covenants — search both sources.
    has_cov = bool(_COVENANT_RE.search(primary_text))
    if not has_cov and item7_text and item7_text != primary_text:
        has_cov = bool(_COVENANT_RE.search(item7_text))
    result["covenants"] = {"mentioned": has_cov}
    if has_cov:
        found.append("covenants")

    # 4. Credit facility — try primary, then item7.
    fac_amt = _parse_credit_facility(primary_text)
    if fac_amt is None and item7_text and item7_text != primary_text:
        fac_amt = _parse_credit_facility(item7_text)
    if fac_amt is not None:
        result["credit_facility"] = {"detected": True, "amount": fac_amt}
        found.append("credit_facility")
    else:
        result["credit_facility"] = {"detected": False, "amount": None}

    report = create_report(
        extractor_name="debt_structure", expected=expected,
        found=found, source_filing=source_filing,
        warnings=warnings if warnings else None,
    )
    if not found:
        return None, report
    return _sv_any(
        result, f"Text extraction from {source_filing}",
        confidence=Confidence.MEDIUM,
    ), report


# ---------------------------------------------------------------------------
# SECT3-11: Refinancing Risk
# ---------------------------------------------------------------------------


def extract_refinancing_risk(
    debt_structure: SourcedValue[dict[str, Any]] | None,
    liquidity: SourcedValue[dict[str, float | None]] | None,
    cash_value: float | None,
    credit_facility_amount: float | None,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Assess refinancing risk from debt structure and liquidity.

    Risk levels: LOW, MEDIUM, HIGH, CRITICAL.
    """
    expected = [
        "near_term_maturities", "maturity_wall", "coverage", "risk_level",
    ]
    found: list[str] = []
    src = "Derived from debt structure + liquidity"

    if debt_structure is None:
        return None, create_report(
            extractor_name="refinancing_risk", expected=expected,
            found=found, source_filing=src,
            warnings=[
                "Refinancing risk not available: "
                "depends on debt structure data"
            ],
        )

    schedule: dict[str, float] = debt_structure.value.get(
        "maturity_schedule", {}
    )
    if not schedule:
        return None, create_report(
            extractor_name="refinancing_risk", expected=expected,
            found=found, source_filing=src,
            warnings=["No maturity schedule available for risk assessment"],
        )

    current_year = datetime.now(tz=UTC).year

    # Near-term maturities (within 2 years)
    near_term = sum(
        amt for yr, amt in schedule.items()
        if _parse_year(yr) is not None
        and _parse_year(yr) <= current_year + 2  # type: ignore[operator]
    )
    found.append("near_term_maturities")

    # Maturity wall (largest single-year maturity)
    wall = max(schedule.values()) if schedule else 0
    wall_year: str | None = None
    if schedule:
        wall_year = max(schedule.keys(), key=lambda k: schedule[k])
    found.append("maturity_wall")

    # Coverage: available cash + credit facility vs. near-term
    available = (cash_value or 0.0) + (credit_facility_amount or 0.0)
    cov = _safe_divide(available, near_term) if near_term > 0 else None
    found.append("coverage")

    # Risk level
    risk = _determine_risk_level(
        near_term, available, cov, current_year, schedule
    )
    found.append("risk_level")

    result: dict[str, Any] = {
        "near_term_maturities": near_term,
        "maturity_wall": wall,
        "maturity_wall_year": wall_year,
        "coverage_ratio": round(cov, 4) if cov is not None else None,
        "available_resources": available,
        "risk_level": risk,
    }
    report = create_report(
        extractor_name="refinancing_risk", expected=expected,
        found=found, source_filing=src,
    )
    return _sv_any(result, src, confidence=Confidence.MEDIUM), report


def _determine_risk_level(
    near_term: float,
    available: float,
    coverage_ratio: float | None,
    current_year: int,
    schedule: dict[str, float],
) -> str:
    """Classify refinancing risk as LOW/MEDIUM/HIGH/CRITICAL."""
    if near_term == 0:
        return "LOW"
    # Imminent maturities (this year or next)
    imminent = sum(
        amt for yr, amt in schedule.items()
        if _parse_year(yr) is not None
        and _parse_year(yr) <= current_year + 1  # type: ignore[operator]
    )
    if imminent > 0 and available < imminent * 0.5:
        return "CRITICAL"
    if coverage_ratio is None or coverage_ratio < 1.0:
        return "HIGH"
    if coverage_ratio < 2.0:
        return "MEDIUM"
    return "LOW"
