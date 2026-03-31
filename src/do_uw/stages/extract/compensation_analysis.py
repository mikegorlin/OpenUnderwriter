"""Compensation risk analysis extraction from proxy statements.

Extracts CEO compensation, pay mix, pay ratio, say-on-pay results,
clawback provisions, related-party transactions, and notable
perquisites from DEF 14A proxy statement text.
Covers SECT5-05 (compensation analysis) for D&O underwriting.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import CompensationAnalysis
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_texts,
    get_filings,
    get_info_dict,
    now,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "ceo_total_comp",
    "comp_mix",
    "pay_ratio",
    "say_on_pay",
    "clawback",
    "related_party",
]



def _extract_ceo_compensation(
    proxy_text: str,
) -> dict[str, float | None]:
    """Extract CEO compensation from Summary Compensation Table."""
    result: dict[str, float | None] = {
        "total": None,
        "salary": None,
        "bonus": None,
        "equity": None,
        "other": None,
    }

    if not proxy_text.strip():
        return result

    # Find Summary Compensation Table section.
    sct_match = re.search(
        r"summary\s+compensation\s+table",
        proxy_text,
        re.IGNORECASE,
    )
    if not sct_match:
        return result

    # Extract a window of text after the table header.
    window = proxy_text[sct_match.start() : sct_match.start() + 5000]

    # Look for CEO row - typically labeled "Chief Executive Officer"
    # or name with CEO indicator.
    ceo_patterns = [
        r"chief executive officer",
        r"(?<!\w)ceo(?!\w)",
        r"president and chief executive",
    ]

    ceo_line = ""
    for pat in ceo_patterns:
        match = re.search(pat, window, re.IGNORECASE)
        if match:
            # Get the line/row containing this match.
            start = max(0, match.start() - 200)
            end = min(len(window), match.end() + 500)
            ceo_line = window[start:end]
            break

    if not ceo_line:
        return result

    # Extract dollar amounts from the CEO row.
    amounts = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)", ceo_line)
    parsed: list[float] = []
    for amt_str in amounts:
        raw = amt_str.replace(",", "")
        try:
            val = float(raw)
            # Filter out likely year values (1990-2035) and tiny amounts.
            # SCT headers contain fiscal years that look like dollar amounts.
            if val > 1000 and not (1990 <= val <= 2035):
                parsed.append(val)
        except ValueError:
            pass

    if parsed:
        # Largest amount is typically total compensation.
        result["total"] = max(parsed)
        # If we have multiple amounts, try to assign categories.
        if len(parsed) >= 4:
            sorted_amounts = sorted(parsed)
            result["other"] = sorted_amounts[0]
            result["salary"] = sorted_amounts[1]
            result["bonus"] = sorted_amounts[2] if len(parsed) > 4 else None
            result["equity"] = sorted_amounts[-2] if sorted_amounts[-2] != max(parsed) else None

    return result


def _compute_comp_mix(
    comp: dict[str, float | None],
) -> dict[str, float]:
    """Compute compensation mix percentages from component values."""
    total = comp.get("total")
    if not total or total <= 0:
        return {}

    mix: dict[str, float] = {}
    for key in ("salary", "bonus", "equity", "other"):
        val = comp.get(key)
        if val is not None and val > 0:
            mix[key] = round(val / total * 100.0, 1)

    return mix


def _extract_pay_ratio(proxy_text: str) -> float | None:
    """Extract CEO-to-median-employee pay ratio (e.g. '200:1')."""
    if not proxy_text.strip():
        return None

    patterns = [
        r"(?:pay\s+ratio|ceo.{0,150}ratio).{0,100}?(\d[\d,]*)\s*(?::|to)\s*1",
        r"ratio\s+(?:of|was|is)\s+(?:approximately\s+)?(\d[\d,]*)\s*(?::|to)\s*1",
        r"(?:approximately|was)\s+(\d[\d,]*)\s*(?::|to)\s*1",
        r"(\d[\d,]*)\s*(?::|to)\s*1\s*(?:pay\s+ratio|ratio)",
    ]

    for pat in patterns:
        match = re.search(pat, proxy_text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                ratio = float(raw)
                if 1.0 <= ratio <= 10000.0:
                    return ratio
            except ValueError:
                pass
    return None


def _extract_say_on_pay(proxy_text: str) -> float | None:
    """Extract say-on-pay vote approval percentage (0-100)."""
    if not proxy_text.strip():
        return None

    patterns = [
        r"(?:say.on.pay|advisory\s+vote\s+on\s+(?:executive\s+)?compensation)"
        r".{0,200}?(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)",
        r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)\s+(?:of\s+)?(?:votes?\s+)?(?:cast\s+)?(?:in\s+)?(?:favor|for|approved)"
        r".{0,100}(?:say.on.pay|advisory\s+vote|executive\s+compensation)",
        r"(?:say.on.pay|advisory\s+vote).{0,50}(?:approved|supported)"
        r".{0,50}?(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)",
    ]

    for pat in patterns:
        match = re.search(pat, proxy_text, re.IGNORECASE)
        if match:
            try:
                pct = float(match.group(1))
                if 0.0 <= pct <= 100.0:
                    return pct
            except ValueError:
                pass
    return None


def _extract_clawback(
    proxy_text: str,
) -> tuple[bool | None, str | None]:
    """Detect clawback policy; returns (has_clawback, scope)."""
    if not proxy_text.strip():
        return None, None

    text_lower = proxy_text.lower()

    if "clawback" not in text_lower and "recoupment" not in text_lower:
        return False, None

    # Determine scope.
    broader_indicators = [
        "broader than",
        "exceeds",
        "in addition to",
        "beyond",
        "voluntary",
        "misconduct",
        "cause",
        "fraud",
    ]

    scope = "DODD_FRANK_MINIMUM"
    for indicator in broader_indicators:
        if indicator in text_lower:
            scope = "BROADER"
            break

    return True, scope


def _extract_related_party(proxy_text: str) -> list[str]:
    """Extract related-party transaction disclosures from proxy."""
    if not proxy_text.strip():
        return []

    transactions: list[str] = []

    # Find related party section.
    rpt_match = re.search(
        r"(?:related\s+(?:party|person)\s+transaction|"
        r"certain\s+relationships\s+and\s+related\s+(?:party\s+)?transaction)",
        proxy_text,
        re.IGNORECASE,
    )
    if not rpt_match:
        return transactions

    # Window of text in the related party section.
    window = proxy_text[rpt_match.start() : rpt_match.start() + 3000]
    sentences = re.split(r"[.!?]+", window)

    for sentence in sentences[1:]:  # Skip the header sentence.
        stripped = sentence.strip()
        if len(stripped) > 30 and "$" in stripped:
            transactions.append(stripped[:300])

    return transactions[:5]  # Cap at 5.


def _extract_perquisites(proxy_text: str) -> list[str]:
    """Extract notable executive perquisites from proxy."""
    if not proxy_text.strip():
        return []

    perks: list[str] = []
    text_lower = proxy_text.lower()

    perk_keywords = [
        "personal use of aircraft",
        "personal aircraft",
        "club membership",
        "tax gross-up",
        "tax reimbursement",
        "security services",
        "personal security",
        "relocation",
        "housing allowance",
        "car allowance",
        "automobile",
        "financial planning",
        "executive physical",
    ]

    for kw in perk_keywords:
        if kw in text_lower:
            # Find the sentence containing this perk.
            idx = text_lower.index(kw)
            start = max(0, proxy_text.rfind(".", 0, idx) + 1)
            end = proxy_text.find(".", idx)
            if end == -1:
                end = min(len(proxy_text), idx + 200)
            sentence = proxy_text[start:end].strip()
            if len(sentence) > 10:
                perks.append(sentence[:300])

    return perks[:5]



def extract_compensation(
    state: AnalysisState,
) -> tuple[CompensationAnalysis, ExtractionReport]:
    """Extract compensation analysis from proxy statement.

    Parses DEF 14A for CEO compensation, pay mix, pay ratio,
    say-on-pay results, clawback provisions, related-party
    transactions, and notable perquisites.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (CompensationAnalysis, ExtractionReport).
    """
    analysis = CompensationAnalysis()
    found: list[str] = []
    warnings: list[str] = []
    fallbacks: list[str] = []
    source_filing = "DEF 14A proxy statement"
    source = source_filing

    # Get proxy text.
    proxy_text = get_filing_document_text(state, "DEF 14A")
    if not proxy_text:
        filings = get_filings(state)
        texts = get_filing_texts(filings)
        proxy_text = str(texts.get("proxy_compensation", ""))
        proxy_gov = str(texts.get("proxy_governance", ""))
        if proxy_gov:
            proxy_text = proxy_text + "\n" + proxy_gov

    if not proxy_text.strip():
        warnings.append("No proxy text available for compensation analysis")

    # 1. CEO compensation from Summary Compensation Table.
    comp = _extract_ceo_compensation(proxy_text)
    if comp["total"] is not None:
        analysis.ceo_total_comp = sourced_float(
            comp["total"], source, Confidence.MEDIUM
        )
        found.append("ceo_total_comp")

        if comp["salary"] is not None:
            analysis.ceo_salary = sourced_float(
                comp["salary"], source, Confidence.LOW
            )
        if comp["bonus"] is not None:
            analysis.ceo_bonus = sourced_float(
                comp["bonus"], source, Confidence.LOW
            )
        if comp["equity"] is not None:
            analysis.ceo_equity = sourced_float(
                comp["equity"], source, Confidence.LOW
            )
        if comp["other"] is not None:
            analysis.ceo_other = sourced_float(
                comp["other"], source, Confidence.LOW
            )
    else:
        # Fallback to yfinance info dict.
        info = get_info_dict(state)
        total_comp = _get_yfinance_comp(info)
        if total_comp is not None:
            analysis.ceo_total_comp = sourced_float(
                total_comp,
                "yfinance info dict",
                Confidence.LOW,
            )
            found.append("ceo_total_comp")
            fallbacks.append("yfinance_total_comp")

    # 2. Compensation mix.
    mix = _compute_comp_mix(comp)
    if mix:
        analysis.comp_mix = mix
        found.append("comp_mix")

    # 3. Pay ratio.
    ratio = _extract_pay_ratio(proxy_text)
    if ratio is not None:
        analysis.ceo_pay_ratio = sourced_float(
            ratio, source, Confidence.HIGH
        )
        found.append("pay_ratio")

    # 4. Say-on-pay.
    sop = _extract_say_on_pay(proxy_text)
    if sop is not None:
        analysis.say_on_pay_pct = sourced_float(
            sop, source, Confidence.HIGH
        )
        found.append("say_on_pay")

    # 5. Clawback.
    has_clawback, scope = _extract_clawback(proxy_text)
    if has_clawback is not None:
        analysis.has_clawback = SourcedValue[bool](
            value=has_clawback,
            source=source,
            confidence=Confidence.HIGH,
            as_of=now(),
        )
        if scope:
            analysis.clawback_scope = sourced_str(
                scope, source, Confidence.HIGH
            )
        found.append("clawback")

    # 6. Related-party transactions.
    rpt = _extract_related_party(proxy_text)
    for txn in rpt:
        analysis.related_party_transactions.append(
            sourced_str(txn, source, Confidence.HIGH)
        )
    found.append("related_party")

    # 7. Notable perquisites.
    perks = _extract_perquisites(proxy_text)
    for perk in perks:
        analysis.notable_perquisites.append(
            sourced_str(perk, source, Confidence.MEDIUM)
        )

    report = create_report(
        extractor_name="compensation_analysis",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        fallbacks_used=fallbacks if fallbacks else None,
        warnings=warnings if warnings else None,
    )
    log_report(report)

    return analysis, report


def _get_yfinance_comp(info: dict[str, Any]) -> float | None:
    """Get total compensation from yfinance info dict."""
    from typing import cast

    # Direct key.
    total = info.get("totalCompensation")
    if total is not None:
        try:
            return float(cast(float, total))
        except (ValueError, TypeError):
            pass

    # From companyOfficers list.
    officers = info.get("companyOfficers")
    if isinstance(officers, list):
        typed_officers = cast(list[dict[str, Any]], officers)
        for officer_dict in typed_officers:
            title = str(officer_dict.get("title", "")).lower()
            if "chief executive" in title or "ceo" in title:
                comp_val = officer_dict.get("totalPay")
                if comp_val is not None:
                    try:
                        return float(cast(float, comp_val))
                    except (ValueError, TypeError):
                        pass
    return None
