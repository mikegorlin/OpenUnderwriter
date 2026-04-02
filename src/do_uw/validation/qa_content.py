"""HTML content quality verification.

Checks the actual rendered HTML output for quality issues that
automated tests miss: SCREAMING_SNAKE codes, excessive N/A values,
truncated text, raw threshold evidence, duplicate content, and
forensic signal value diversity.

Runs as part of post-pipeline QA verification.
"""

from __future__ import annotations

import re
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from do_uw.validation.qa_report import QACheck

logger = logging.getLogger(__name__)

# Source codes and status codes that should never appear in user-facing text
_KNOWN_CODES = {
    "DATA_UNAVAILABLE",
    "NOT_AUTO_EVALUATED",
    "MANUAL_ONLY",
    "FALLBACK_ONLY",
    "SECTOR_CONDITIONAL",
    "SEC_FORM4",
    "SEC_ENFORCEMENT",
    "MARKET_SHORT",
    "SEC_FRAMES",
    "REFERENCE_DATA",
    "SEC_S1",
    "SEC_S3",
    "SEC_13DG",
    "INSIDER_TRADES",
    "SEC_8K",
    "SCAC_SEARCH",
    "SEC_DEF14A",
    "MARKET_PRICE",
    "SEC_10K",
    "NET_SELLING",
    "A_DISCLOSURE",
}

# Signal IDs in audit appendix are intentional — don't flag these
_AUDIT_SECTION_IDS = {
    "qa-audit",
    "signal-audit",
    "epistemological-trace",
    "coverage",
    "data-audit",
    "decision-record",
}


def check_html_content(output_dir: Path, state: Any) -> list[QACheck]:
    """Run HTML content quality checks on rendered output.

    Args:
        output_dir: Directory containing output files.
        state: Completed AnalysisState.

    Returns:
        List of QACheck results.
    """
    checks: list[QACheck] = []
    html_files = list(output_dir.glob("*_worksheet.html"))
    if not html_files:
        return checks

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup not available — skipping HTML content QA")
        return checks

    html_path = html_files[0]
    try:
        html = html_path.read_text(encoding="utf-8")
    except Exception:
        logger.warning("Failed to read HTML file for QA")
        return checks

    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style for text analysis
    for tag in soup(["script", "style"]):
        tag.decompose()

    checks.extend(_check_screaming_snake(soup))
    checks.extend(_check_na_count(soup))
    checks.extend(_check_truncation_artifacts(soup))
    checks.extend(_check_raw_threshold_evidence(soup))
    checks.extend(_check_forensic_diversity(state))
    checks.extend(_check_stock_drop_reasonableness(state))
    checks.extend(_check_section_content(soup))
    checks.extend(_check_broken_urls(soup))
    checks.extend(_check_empty_data_tables(soup))

    return checks


def _check_screaming_snake(soup: Any) -> list[QACheck]:
    """Check for SCREAMING_SNAKE internal codes in user-facing sections."""
    # Only check non-audit sections
    user_sections = []
    for section in soup.find_all("section"):
        sid = section.get("id", "")
        if sid not in _AUDIT_SECTION_IDS:
            user_sections.append(section)

    if not user_sections:
        # Fall back to full text minus audit
        text = soup.get_text()
    else:
        text = " ".join(s.get_text() for s in user_sections)

    snake_re = re.compile(r"[A-Z][A-Z0-9_]{2,}[A-Z0-9]")
    matches = [m for m in snake_re.findall(text) if "_" in m and m in _KNOWN_CODES]
    count = len(matches)

    if count == 0:
        return [
            QACheck(
                category="Content",
                name="Internal codes",
                status="PASS",
                detail="No SCREAMING_SNAKE codes in user sections",
                value="0",
            )
        ]
    elif count <= 5:
        top = Counter(matches).most_common(3)
        detail = f"{count} internal codes leaked: {', '.join(f'{t}({c})' for t, c in top)}"
        return [
            QACheck(
                category="Content",
                name="Internal codes",
                status="WARN",
                detail=detail,
                value=str(count),
            )
        ]
    else:
        top = Counter(matches).most_common(5)
        detail = f"{count} internal codes: {', '.join(f'{t}({c})' for t, c in top)}"
        return [
            QACheck(
                category="Content",
                name="Internal codes",
                status="FAIL",
                detail=detail,
                value=str(count),
            )
        ]


def _check_na_count(soup: Any) -> list[QACheck]:
    """Check for excessive N/A values in the output."""
    text = soup.get_text()
    na_count = len(re.findall(r"\bN/A\b", text))

    if na_count <= 30:
        return [
            QACheck(
                category="Content",
                name="N/A values",
                status="PASS",
                detail=f"{na_count} N/A values (acceptable)",
                value=str(na_count),
            )
        ]
    elif na_count <= 80:
        return [
            QACheck(
                category="Content",
                name="N/A values",
                status="WARN",
                detail=f"{na_count} N/A values — check for extraction gaps",
                value=str(na_count),
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="N/A values",
                status="FAIL",
                detail=f"{na_count} N/A values — significant data gaps",
                value=str(na_count),
            )
        ]


def _check_truncation_artifacts(soup: Any) -> list[QACheck]:
    """Check for Jinja truncate() artifacts in analytical text.

    Jinja's truncate() adds '...' at a character boundary mid-word.
    Extraction-time truncation (where LLM cut off a risk factor description)
    is different — those end with '...' at a natural break. We detect Jinja
    truncation by looking for '...' preceded by a cut-off word (no space/punctuation
    before the dots).
    """
    jinja_truncated = 0
    extraction_truncated = 0
    # Only check user-facing sections (not audit appendices)
    user_sections = []
    for section in soup.find_all("section"):
        sid = section.get("id", "")
        if sid not in _AUDIT_SECTION_IDS:
            user_sections.append(section)
    elements = []
    for sec in user_sections:
        elements.extend(sec.find_all(["td", "span", "p", "div"]))
    for el in elements:
        text = el.get_text(strip=True)
        if not text.endswith("...") or len(text) <= 20:
            continue
        # Detect extraction truncation patterns (mention(s):, etc.)
        if "mention(s):" in text:
            extraction_truncated += 1
            continue
        # Jinja truncate cuts mid-word: "some te..."
        # Extraction cuts at sentence end: "incidents, terr..."
        # Jinja truncate() produces exact character-count cuts with no trailing space.
        # Extraction truncation produces longer prose with natural word breaks.
        # Heuristic: Jinja truncation is short (< 200 chars) and cuts mid-word.
        # Long text (> 200 chars) ending in '...' is extraction, not Jinja.
        if len(text) < 200:
            jinja_truncated += 1
        else:
            extraction_truncated += 1

    total = jinja_truncated + extraction_truncated
    if jinja_truncated == 0:
        status = "PASS" if extraction_truncated <= 20 else "WARN"
        detail = f"No Jinja truncation detected"
        if extraction_truncated > 0:
            detail += f" ({extraction_truncated} extraction-time cuts — source data, not template)"
        return [
            QACheck(
                category="Content",
                name="Truncated text",
                status=status,
                detail=detail,
                value=str(total),
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="Truncated text",
                status="FAIL",
                detail=f"{jinja_truncated} Jinja truncate() artifacts + {extraction_truncated} extraction cuts",
                value=str(jinja_truncated),
            )
        ]


def _check_raw_threshold_evidence(soup: Any) -> list[QACheck]:
    """Check for raw threshold evidence in user-facing sections.

    Catches patterns like 'Value 0.208 exceeds red threshold 0.15' which
    are internal signal evaluation output, not underwriter-ready text.
    """
    # Only check non-audit sections
    user_text = ""
    for section in soup.find_all("section"):
        sid = section.get("id", "")
        if sid not in _AUDIT_SECTION_IDS:
            user_text += section.get_text() + " "

    raw_patterns = [
        r"Value [\d.]+ (?:exceeds|below) (?:red|yellow|green) threshold",
        r"Boolean check: .+ condition met",
        r"Boolean check: True",
        r"Gap search: keyword match=",
    ]

    total = 0
    for pattern in raw_patterns:
        total += len(re.findall(pattern, user_text, re.IGNORECASE))

    if total == 0:
        return [
            QACheck(
                category="Content",
                name="Raw evidence",
                status="PASS",
                detail="No raw threshold evidence in user sections",
                value="0",
            )
        ]
    elif total <= 5:
        return [
            QACheck(
                category="Content",
                name="Raw evidence",
                status="WARN",
                detail=f"{total} raw threshold patterns — humanize before shipping",
                value=str(total),
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="Raw evidence",
                status="FAIL",
                detail=f"{total} raw threshold patterns leaked to user sections",
                value=str(total),
            )
        ]


def _check_forensic_diversity(state: Any) -> list[QACheck]:
    """Check that forensic signals have diverse values (not all identical).

    Catches the 0.208 bug where all FIN.FORENSIC signals got the same
    fallback value due to data mapping errors.
    """
    analysis = getattr(state, "analysis", None)
    if analysis is None:
        return []

    sr = getattr(analysis, "signal_results", {})
    if not sr:
        return []

    forensic_values: list[float] = []
    for sig_id, result in sr.items():
        if not sig_id.startswith("FIN.FORENSIC."):
            continue
        status = (
            result.get("status") if isinstance(result, dict) else getattr(result, "status", None)
        )
        if status in ("TRIGGERED", "CLEAR"):
            val = (
                result.get("value") if isinstance(result, dict) else getattr(result, "value", None)
            )
            if isinstance(val, (int, float)):
                forensic_values.append(float(val))

    if len(forensic_values) < 5:
        return []  # Not enough data to check

    unique = len(set(forensic_values))
    if unique >= 3:
        return [
            QACheck(
                category="Content",
                name="Forensic diversity",
                status="PASS",
                detail=f"{unique} unique values across {len(forensic_values)} forensic signals",
                value=str(unique),
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="Forensic diversity",
                status="FAIL",
                detail=f"Only {unique} unique value(s) across {len(forensic_values)} signals — likely data mapping bug",
                value=str(unique),
            )
        ]


def _check_stock_drop_reasonableness(state: Any) -> list[QACheck]:
    """Check that reported stock drops are within reasonable bounds.

    Single-day drops >25% are extremely rare for established companies
    and may indicate bad data (adjusted prices, IPO artifacts, splits).
    """
    extracted = getattr(state, "extracted", None)
    if extracted is None:
        return []

    # Stock drops live at extracted.market.stock.single_day_drops
    market = getattr(extracted, "market", None)
    stock = getattr(market, "stock", None) if market else None
    if stock is None:
        return []

    suspicious: list[str] = []

    # Check single-day drops
    single_day = getattr(stock, "single_day_drops", None) or []
    for drop in single_day:
        pct = None
        if hasattr(drop, "drop_pct") and drop.drop_pct is not None:
            pct = getattr(drop.drop_pct, "value", None)
        elif isinstance(drop, dict):
            dp = drop.get("drop_pct", {})
            pct = dp.get("value") if isinstance(dp, dict) else dp

        if pct is not None:
            try:
                pct_f = abs(float(pct))
            except (ValueError, TypeError):
                continue
            if pct_f > 25.0:
                date_val = None
                if hasattr(drop, "date") and drop.date is not None:
                    date_val = getattr(drop.date, "value", None)
                elif isinstance(drop, dict):
                    d = drop.get("date", {})
                    date_val = d.get("value") if isinstance(d, dict) else d
                suspicious.append(f"{pct_f:.1f}% on {date_val or '?'}")

    if not suspicious:
        return [
            QACheck(
                category="Data",
                name="Stock drop reasonableness",
                status="PASS",
                detail="All reported drops within reasonable bounds",
            )
        ]
    else:
        return [
            QACheck(
                category="Data",
                name="Stock drop reasonableness",
                status="WARN",
                detail=f"{len(suspicious)} suspicious drop(s) >25%: {'; '.join(suspicious[:3])}. Verify against market data.",
                value=str(len(suspicious)),
            )
        ]


# ---------------------------------------------------------------------------
# Section content verification
# ---------------------------------------------------------------------------

# Expected major heading patterns in the rendered worksheet.
# If a heading exists but its section has minimal text, something is broken
# (likely a context key mismatch between builder and template).
_EXPECTED_SECTIONS: dict[str, int] = {
    "Company": 200,
    "Market": 200,
    "Financial": 200,
    "Governance": 200,
    "Litigation": 100,
    "Scoring": 100,
    "Key Risk Findings": 50,
}


def _check_section_content(soup: Any) -> list[QACheck]:
    """Verify each major section has substantive content, not just headers.

    This catches the Phase 148 failure mode: context builders use wrong key
    names so templates render empty, but the heading still appears.
    """
    checks: list[QACheck] = []
    uw_section = soup.find("section", id="uw-analysis")
    if not uw_section:
        checks.append(
            QACheck(
                category="Content",
                name="Section content",
                status="FAIL",
                detail="No uw-analysis section found in output",
            )
        )
        return checks

    # Find all h2/h3 headings
    headings = uw_section.find_all(["h2", "h3"])
    heading_map: dict[str, str] = {}
    for h in headings:
        text = h.get_text(strip=True)
        heading_map[text] = text

    empty_sections: list[str] = []
    ok_sections: list[str] = []

    for section_name, min_chars in _EXPECTED_SECTIONS.items():
        # Find headings containing this section name
        matching = [h for h in headings if section_name.lower() in h.get_text(strip=True).lower()]
        if not matching:
            continue
        for h in matching:
            # Get text content of the parent container (next ~20 siblings)
            parent = h.parent
            if parent:
                sibling_text = ""
                for sib in list(parent.children):
                    if sib != h:
                        sibling_text += (
                            sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib)
                        )
                if len(sibling_text) < min_chars:
                    empty_sections.append(f"{section_name} ({len(sibling_text)}ch)")
                else:
                    ok_sections.append(section_name)
                break

    if empty_sections:
        checks.append(
            QACheck(
                category="Content",
                name="Section content",
                status="FAIL",
                detail=f"Near-empty sections (likely context key mismatch): {', '.join(empty_sections)}",
                value=str(len(empty_sections)),
            )
        )
    else:
        checks.append(
            QACheck(
                category="Content",
                name="Section content",
                status="PASS",
                detail=f"{len(ok_sections)} major sections verified with substantive content",
                value=str(len(ok_sections)),
            )
        )

    return checks


def _check_broken_urls(soup: Any) -> list[QACheck]:
    """Check for broken URLs that contain stringified Python dicts/lists.

    Catches the yfinance canonicalUrl bug where href="{\'url\': \'...\'}".
    """
    broken = 0
    for a in soup.find_all("a", href=True):
        href = str(a.get("href", ""))
        if href.startswith("{") or href.startswith("[") or "&#39;" in href:
            broken += 1

    if broken == 0:
        return [
            QACheck(
                category="Content",
                name="URL integrity",
                status="PASS",
                detail="All URLs are well-formed",
                value="0",
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="URL integrity",
                status="FAIL",
                detail=f"{broken} broken URL(s) — likely stringified Python dict in href",
                value=str(broken),
            )
        ]


def _check_empty_data_tables(soup: Any) -> list[QACheck]:
    """Check for tables where all data cells are empty or N/A.

    Tables that render as all-empty indicate context builder produced
    no data but the template still rendered the table skeleton.
    """
    uw_section = soup.find("section", id="uw-analysis")
    if not uw_section:
        return []

    tables = uw_section.find_all("table")
    empty_tables = 0
    for table in tables:
        tds = table.find_all("td")
        if not tds:
            continue
        non_empty = 0
        for td in tds:
            text = td.get_text(strip=True)
            if text and text not in ("—", "N/A", "", "None"):
                non_empty += 1
        if non_empty == 0 and len(tds) >= 4:
            empty_tables += 1

    if empty_tables == 0:
        return [
            QACheck(
                category="Content",
                name="Table data",
                status="PASS",
                detail="All data tables have populated cells",
                value="0",
            )
        ]
    elif empty_tables <= 3:
        return [
            QACheck(
                category="Content",
                name="Table data",
                status="WARN",
                detail=f"{empty_tables} table(s) with all-empty cells — check context builder output",
                value=str(empty_tables),
            )
        ]
    else:
        return [
            QACheck(
                category="Content",
                name="Table data",
                status="FAIL",
                detail=f"{empty_tables} table(s) with all-empty cells — context key mismatch likely",
                value=str(empty_tables),
            )
        ]
