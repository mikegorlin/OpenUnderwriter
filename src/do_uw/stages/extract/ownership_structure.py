"""Ownership structure extraction and activist risk assessment.

Extracts institutional/insider ownership, top holders, activist investor
identification, SC 13D/13G filing analysis, dual-class detection, and
overall activist risk assessment (SECT5-08).

Usage:
    ownership, report = extract_ownership(state)
    state.extracted.governance.ownership = ownership
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import OwnershipAnalysis
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_documents,
    get_info_dict,
    get_market_data,
    now,
    sourced_float,
    sourced_str,
    sourced_str_dict,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

EXPECTED_FIELDS: list[str] = [
    "institutional_pct", "insider_pct", "top_holders",
    "activist_check", "13d_filings", "dual_class", "activist_risk",
]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_activist_investors(
    path: Path | None = None,
) -> list[str]:
    """Load known activist investor names from config."""
    if path is not None:
        import json
        if not path.exists():
            logger.warning("Activist investors config not found: %s", path)
            return []
        with path.open(encoding="utf-8") as f:
            data_raw: dict[str, Any] = json.load(f)
        raw = data_raw.get("known_activists")
        if isinstance(raw, list):
            return [str(x) for x in cast(list[str], raw)]
        return []

    data = load_config("activist_investors")
    raw = data.get("known_activists")
    if isinstance(raw, list):
        return [str(x) for x in cast(list[str], raw)]
    return []


# ---------------------------------------------------------------------------
# Institutional holder extraction
# ---------------------------------------------------------------------------


def extract_from_institutional_holders(
    holders_data: dict[str, Any],
) -> list[SourcedValue[dict[str, Any]]]:
    """Parse yfinance institutional_holders into top 10 holder records.

    The holders_data is a dict-of-lists from DataFrame.to_dict("list").
    """
    # yfinance returns columns: Holder, Shares, Date Reported, % Out, Value
    names_raw = holders_data.get("Holder", [])
    if not isinstance(names_raw, list) or not names_raw:
        return []

    names = cast(list[Any], names_raw)
    # yfinance column name varies: "% Out" (older) or "pctHeld" (newer)
    pcts = cast(list[Any], holders_data.get("% Out") or holders_data.get("pctHeld", []))
    shares = cast(list[Any], holders_data.get("Shares", []))
    values = cast(list[Any], holders_data.get("Value", []))

    result: list[SourcedValue[dict[str, Any]]] = []
    for i in range(min(10, len(names))):
        holder: dict[str, Any] = {"name": str(names[i])}
        if i < len(pcts) and pcts[i] is not None:
            holder["pct_out"] = float(pcts[i])
        if i < len(shares) and shares[i] is not None:
            holder["shares"] = int(shares[i])
        if i < len(values) and values[i] is not None:
            holder["value"] = float(values[i])

        result.append(SourcedValue[dict[str, Any]](
            value=holder, source="yfinance institutional_holders",
            confidence=Confidence.MEDIUM, as_of=now(),
        ))
    return result


# ---------------------------------------------------------------------------
# Activist detection
# ---------------------------------------------------------------------------


def _activist_matches(activist: str, holder: str) -> bool:
    """Check if activist name matches holder name.

    Matches if: (a) substring match, or (b) the distinctive first word
    of the activist name is present in the holder name.
    """
    if activist in holder or holder in activist:
        return True
    # Word-level: first word of activist in holder (e.g. "elliott" in "elliott investment...")
    first_word = activist.split()[0] if activist else ""
    if len(first_word) >= 4 and first_word in holder:
        return True
    return False


def check_for_activists(
    holders: list[SourcedValue[dict[str, Any]]],
    known_activists: list[str],
) -> list[SourcedValue[str]]:
    """Match institutional holders against known activist investor list.

    Uses case-insensitive matching: substring match or shared distinctive
    words (first word of activist name found in holder name).
    """
    if not holders or not known_activists:
        return []

    activists_lower = [a.lower() for a in known_activists]
    matches: list[SourcedValue[str]] = []

    for holder_sv in holders:
        holder_name = str(holder_sv.value.get("name", "")).lower()
        if not holder_name:
            continue
        for i, activist_lower in enumerate(activists_lower):
            if _activist_matches(activist_lower, holder_name):
                matches.append(sourced_str(
                    known_activists[i],
                    f"yfinance institutional_holders (matched: {holder_sv.value.get('name', '')})",
                    Confidence.MEDIUM,
                ))
                break  # One match per holder.

    return matches


# ---------------------------------------------------------------------------
# 13D/13G filing extraction
# ---------------------------------------------------------------------------


def _extract_13d_filings(
    state: AnalysisState,
) -> tuple[
    list[SourcedValue[dict[str, str]]],
    list[SourcedValue[dict[str, str]]],
]:
    """Parse SC 13D and SC 13G filing metadata from acquired data.

    Identifies 13G-to-13D conversions (passive to activist signal).

    Returns:
        Tuple of (13d_filings, conversions_13g_to_13d).
    """
    docs = get_filing_documents(state)
    filings_13d: list[SourcedValue[dict[str, str]]] = []
    filings_13g: list[SourcedValue[dict[str, str]]] = []
    conversions: list[SourcedValue[dict[str, str]]] = []

    # Collect 13D filings.
    for doc in docs.get("SC 13D", []):
        filing_info = {
            "form_type": "SC 13D",
            "filing_date": str(doc.get("filing_date", "")),
            "accession": str(doc.get("accession", "")),
        }
        # Try to extract filer name from text.
        full_text = str(doc.get("full_text", ""))
        filer = _extract_filer_name(full_text)
        if filer:
            filing_info["filer"] = filer
        filings_13d.append(sourced_str_dict(
            filing_info, "SEC filing SC 13D", Confidence.HIGH,
        ))

    # Collect 13G filings for conversion detection.
    for doc in docs.get("SC 13G", []):
        filing_info = {
            "form_type": "SC 13G",
            "filing_date": str(doc.get("filing_date", "")),
            "accession": str(doc.get("accession", "")),
        }
        full_text = str(doc.get("full_text", ""))
        filer = _extract_filer_name(full_text)
        if filer:
            filing_info["filer"] = filer
        filings_13g.append(sourced_str_dict(
            filing_info, "SEC filing SC 13G", Confidence.HIGH,
        ))

    # Detect 13G-to-13D conversions (same filer has both).
    filers_13d = {
        f.value.get("filer", "").lower()
        for f in filings_13d if f.value.get("filer")
    }
    for g in filings_13g:
        g_filer = g.value.get("filer", "").lower()
        if g_filer and g_filer in filers_13d:
            conversions.append(sourced_str_dict(
                {"filer": g.value.get("filer", ""), "conversion": "13G_to_13D"},
                "SEC filings SC 13G -> SC 13D",
                Confidence.HIGH,
            ))

    return filings_13d, conversions


def _extract_filer_name(text: str) -> str:
    """Extract filer name from 13D/13G filing text."""
    if not text:
        return ""
    # Look for "FILED BY:" or "NAME OF REPORTING PERSON" patterns.
    patterns = [
        r"FILED BY:\s*(.+?)(?:\n|$)",
        r"NAME OF REPORTING PERSONS?\s*[\n:]\s*(.+?)(?:\n|$)",
        r"REPORTING PERSON\s*[\n:]\s*(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if len(name) > 2:
                return name
    return ""


# ---------------------------------------------------------------------------
# Activist risk assessment
# ---------------------------------------------------------------------------


def assess_activist_risk(
    ownership: OwnershipAnalysis,
) -> str:
    """Compute overall activist risk level: HIGH, MEDIUM, or LOW.

    HIGH: Known activist holder OR 13G-to-13D conversion OR proxy contest
    MEDIUM: 13D filing without known activist OR high institutional ownership
    LOW: No activist indicators
    """
    # HIGH triggers.
    if ownership.known_activists:
        return "HIGH"
    if ownership.conversions_13g_to_13d:
        return "HIGH"
    if ownership.proxy_contests_3yr:
        return "HIGH"

    # MEDIUM triggers.
    if ownership.filings_13d_24mo:
        return "MEDIUM"
    inst_pct = (
        ownership.institutional_pct.value
        if ownership.institutional_pct is not None
        else 0.0
    )
    if inst_pct > 90.0:
        return "MEDIUM"

    return "LOW"


# ---------------------------------------------------------------------------
# Dual-class detection
# ---------------------------------------------------------------------------


def extract_dual_class(
    proxy_text: str,
    info: dict[str, Any],
) -> tuple[bool, float | None, float | None]:
    """Detect dual-class voting structure.

    Checks proxy text for dual-class keywords and info dict for
    share class information.

    Returns:
        Tuple of (has_dual_class, control_pct, economic_pct).
    """
    has_dual = False
    control_pct: float | None = None
    economic_pct: float | None = None

    # Check info dict for share class signals.
    share_class = str(info.get("shareClass", ""))
    if share_class and share_class.upper() in ("A", "B", "C"):
        has_dual = True

    # Check proxy text for dual-class keywords.
    if proxy_text:
        proxy_lower = proxy_text.lower()
        dual_class_terms = [
            "dual-class", "dual class", "class a common stock",
            "class b common stock", "supervoting",
            "multiple classes of common stock",
            "10 votes per share", "ten votes per share",
        ]
        if any(term in proxy_lower for term in dual_class_terms):
            has_dual = True

        # Try to extract voting control percentage.
        vote_pct_match = re.search(
            r"(?:class b|supervoting).*?(\d{1,3}(?:\.\d+)?)\s*%\s*"
            r"(?:of the|of all|voting)",
            proxy_lower,
        )
        if vote_pct_match:
            control_pct = float(vote_pct_match.group(1))

    return has_dual, control_pct, economic_pct


# ---------------------------------------------------------------------------
# LLM enrichment
# ---------------------------------------------------------------------------


def _enrich_from_llm(
    state: AnalysisState, ownership: OwnershipAnalysis,
) -> None:
    """Enrich ownership with LLM-extracted DEF 14A proxy data.

    Strategy:
    - Top holders: LLM fills only when yfinance holders are empty
    - Insider pct: LLM fills only when yfinance/existing is empty
      (Note: Phase 19 governance path also supplements insider_pct.
       This path handles the case where governance ran first but
       ownership_structure runs independently of governance ordering.)
    """
    from do_uw.stages.extract.llm_helpers import get_llm_def14a

    llm_def14a = get_llm_def14a(state)
    if llm_def14a is None:
        return

    from do_uw.stages.extract.proxy_ownership_converter import (
        convert_insider_ownership,
        convert_top_holders,
    )

    # Top holders: fill when yfinance returned nothing
    if not ownership.top_holders:
        llm_holders = convert_top_holders(llm_def14a)
        if llm_holders:
            ownership.top_holders = [
                SourcedValue[dict[str, Any]](
                    value=cast(dict[str, Any], sv.value),
                    source=sv.source,
                    confidence=sv.confidence,
                    as_of=sv.as_of,
                )
                for sv in llm_holders
            ]

    # Insider pct: fill when yfinance/governance left empty
    if ownership.insider_pct is None:
        llm_insider = convert_insider_ownership(llm_def14a)
        if llm_insider is not None:
            ownership.insider_pct = llm_insider

    logger.info("SECT5: Enriched ownership with LLM DEF 14A data")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_ownership(
    state: AnalysisState,
    activists_path: Path | None = None,
) -> tuple[OwnershipAnalysis, ExtractionReport]:
    """Extract ownership structure and activist risk assessment.

    Parses institutional holders, checks for activist investors,
    analyzes 13D/13G filings, detects dual-class structure, and
    computes activist risk level.

    Returns:
        Tuple of (OwnershipAnalysis, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "yfinance + SEC filings (SC 13D/13G, DEF 14A)"
    ownership = OwnershipAnalysis()

    known_activists = load_activist_investors(activists_path)
    market_data = get_market_data(state)
    info = get_info_dict(state)

    # 1. Institutional ownership percentage.
    inst_pct_raw = info.get("heldPercentInsiders")
    insider_pct_raw = info.get("heldPercentInstitutions")
    # Note: yfinance labels are swapped in some versions.
    if isinstance(insider_pct_raw, (int, float)):
        ownership.institutional_pct = sourced_float(
            float(insider_pct_raw) * 100, "yfinance info", Confidence.MEDIUM,
        )
        found.append("institutional_pct")
    if isinstance(inst_pct_raw, (int, float)):
        ownership.insider_pct = sourced_float(
            float(inst_pct_raw) * 100, "yfinance info", Confidence.MEDIUM,
        )
        found.append("insider_pct")

    # 2. Top institutional holders.
    holders_data = market_data.get("institutional_holders", {})
    if isinstance(holders_data, dict):
        holders_dict = cast(dict[str, Any], holders_data)
        top_holders = extract_from_institutional_holders(holders_dict)
        ownership.top_holders = top_holders
        if top_holders:
            found.append("top_holders")

    # 3. Activist investor check.
    activist_matches = check_for_activists(
        ownership.top_holders, known_activists,
    )
    ownership.known_activists = activist_matches
    found.append("activist_check")

    # 4. 13D/13G filings.
    filings_13d, conversions = _extract_13d_filings(state)
    ownership.filings_13d_24mo = filings_13d
    ownership.conversions_13g_to_13d = conversions
    found.append("13d_filings")

    # 5. Dual-class detection.
    proxy_text = get_filing_document_text(state, "DEF 14A")
    has_dual, control_pct, economic_pct = extract_dual_class(
        proxy_text, info,
    )
    ownership.has_dual_class = SourcedValue[bool](
        value=has_dual,
        source="DEF 14A + yfinance info",
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )
    if control_pct is not None:
        ownership.dual_class_control_pct = sourced_float(
            control_pct, "DEF 14A proxy statement", Confidence.LOW,
        )
    if economic_pct is not None:
        ownership.dual_class_economic_pct = sourced_float(
            economic_pct, "DEF 14A proxy statement", Confidence.LOW,
        )
    found.append("dual_class")

    # 6. LLM DEF 14A ownership enrichment.
    _enrich_from_llm(state, ownership)

    # 7. Activist risk assessment.
    risk = assess_activist_risk(ownership)
    ownership.activist_risk_assessment = sourced_str(
        risk, "Computed from ownership signals", Confidence.LOW,
    )
    found.append("activist_risk")

    report = create_report(
        extractor_name="ownership_structure",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return ownership, report
