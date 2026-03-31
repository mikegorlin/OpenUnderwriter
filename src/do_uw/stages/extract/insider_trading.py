"""Insider trading extraction from Form 4 filings and yfinance data.

Covers SECT4-04: insider transactions, cluster selling detection,
aggregate buy/sell direction, 10b5-1 plan classification.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import defusedxml.ElementTree as SafeET

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import (
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    InsiderTransaction,
)
from do_uw.stages.extract.insider_trading_patterns import (
    analyze_filing_timing,
    detect_exercise_sell_patterns,
    get_eight_k_filings,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_documents,
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

EXPECTED_FIELDS: list[str] = [
    "transactions",
    "cluster_events",
    "net_direction",
    "10b5_1_classification",
    "aggregate_ownership",
]

# SEC Form 4 transaction codes to human-readable types.
TX_CODE_MAP: dict[str, str] = {
    "P": "BUY", "S": "SELL", "A": "GRANT", "M": "EXERCISE",
    "F": "TAX_WITHHOLD", "G": "GIFT", "D": "DISPOSITION",
    "C": "CONVERSION", "J": "OTHER", "K": "EQUITY_SWAP",
    "U": "TENDER", "W": "WILL_OR_ESTATE", "I": "DISCRETIONARY",
}

LOOKBACK_MONTHS = 18


# ---------------------------------------------------------------------------
# Form 4 XML parsing
# ---------------------------------------------------------------------------


def parse_form4_xml(
    xml_text: str,
    accession_number: str = "",
    is_amendment: bool = False,
) -> list[InsiderTransaction]:
    """Parse a single Form 4 XML document into InsiderTransaction list."""
    transactions: list[InsiderTransaction] = []
    if not xml_text.strip():
        return transactions

    try:
        root = SafeET.fromstring(xml_text)
    except ET.ParseError:
        logger.debug("Failed to parse Form 4 XML")
        return transactions

    owner_name = _xml_text(root, ".//rptOwnerName")
    owner_title = _xml_text(root, ".//officerTitle")
    rel = root.find(".//reportingOwnerRelationship")
    is_director = _xml_text(rel, "isDirector") == "1" if rel is not None else False
    is_officer = _xml_text(rel, "isOfficer") == "1" if rel is not None else False
    is_ten_pct = _xml_text(rel, "isTenPercentOwner") == "1" if rel is not None else False
    if not owner_title and is_officer:
        owner_title = "Officer"
    elif not owner_title and is_director:
        owner_title = "Director"

    doc_10b5_1 = _detect_10b5_1(root, xml_text)
    rel_flags = {
        "is_director": is_director, "is_officer": is_officer,
        "is_ten_pct_owner": is_ten_pct,
        "accession_number": accession_number, "is_amendment": is_amendment,
    }

    for tx_el in root.findall(".//nonDerivativeTransaction"):
        tx = _parse_single_tx(tx_el, owner_name, owner_title, doc_10b5_1, rel_flags)
        if tx is not None:
            transactions.append(tx)

    for tx_el in root.findall(".//derivativeTransaction"):
        tx = _parse_single_tx(tx_el, owner_name, owner_title, doc_10b5_1, rel_flags)
        if tx is not None:
            transactions.append(tx)

    return transactions


def _xml_text(element: ET.Element, path: str) -> str:
    """Safely extract text from XML element path."""
    el = element.find(path)
    if el is not None and el.text:
        return el.text.strip()
    return ""


def _detect_10b5_1(root: ET.Element, xml_text: str) -> bool | None:
    """Detect 10b5-1 plan indicator from Form 4 XML.

    Checks multiple locations per SEC filing structure:
    1. Document-level <aff10b5One> (post-2023 SEC rule)
    2. Transaction-level <rule10b5One> elements
    3. Footnote text mentioning 10b5-1 plans
    """
    # Check document-level flag (most reliable, required since 2023)
    aff_el = root.find(".//aff10b5One")
    if aff_el is not None and aff_el.text:
        val = aff_el.text.strip()
        if val == "1":
            return True
        if val == "0":
            return False  # Explicitly NOT a 10b5-1 plan

    # Check for any transaction-level rule10b5One indicators
    for rule_el in root.findall(".//*rule10b5One"):
        if rule_el.text and rule_el.text.strip() == "1":
            return True

    # Fallback: check full text for 10b5-1 mentions
    lower = xml_text.lower()
    if "10b5-1" in lower or "rule 10b5" in lower:
        return True
    return None


# Patterns for extracting plan adoption dates from footnote text.
# Common formats: "adopted on March 15, 2025", "entered into on 3/15/2025",
# "adopted March 2024", "plan dated December 1, 2023"
_ADOPTION_PATTERNS = [
    # "adopted on March 15, 2025" or "adopted March 15, 2025"
    re.compile(
        r"(?:adopted|entered\s+into|established|executed)\s+(?:on\s+)?"
        r"([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        re.IGNORECASE,
    ),
    # "adopted on 3/15/2025" or "adopted 03-15-2025"
    re.compile(
        r"(?:adopted|entered\s+into|established|executed)\s+(?:on\s+)?"
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        re.IGNORECASE,
    ),
    # "plan dated December 1, 2023"
    re.compile(
        r"plan\s+dated\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        re.IGNORECASE,
    ),
]


def _extract_plan_adoption_date(footnote_text: str) -> str | None:
    """Extract 10b5-1 plan adoption date from footnote text.

    Returns ISO date string (YYYY-MM-DD) or None if not found.
    """
    for pattern in _ADOPTION_PATTERNS:
        m = pattern.search(footnote_text)
        if m:
            date_str = m.group(1)
            # Try parsing common formats
            for fmt in (
                "%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%m-%d-%Y",
            ):
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def _parse_single_tx(
    tx_el: ET.Element,
    owner_name: str,
    owner_title: str,
    doc_10b5_1: bool | None,
    rel_flags: dict[str, Any] | None = None,
) -> InsiderTransaction | None:
    """Parse a single transaction element into InsiderTransaction."""
    tx_date_str = _xml_text(tx_el, ".//transactionDate/value")
    tx_code = _xml_text(tx_el, ".//transactionCoding/transactionCode")
    if not tx_date_str:
        return None

    shares_val = _safe_float(
        _xml_text(tx_el, ".//transactionAmounts/transactionShares/value")
    )
    price_val = _safe_float(
        _xml_text(tx_el, ".//transactionAmounts/transactionPricePerShare/value")
    )
    total_val: float | None = None
    if shares_val is not None and price_val is not None:
        total_val = shares_val * price_val

    is_10b5_1 = doc_10b5_1
    plan_adoption_date: str | None = None
    for fn_ref in tx_el.findall(".//transactionCoding/footnoteId"):
        fn_id = fn_ref.get("id", "")
        fn_el = tx_el.find(f".//footnote[@id='{fn_id}']")
        if fn_el is not None and fn_el.text:
            fn_text = fn_el.text
            if "10b5-1" in fn_text.lower():
                is_10b5_1 = True
                # Try to extract plan adoption date from footnote
                adoption = _extract_plan_adoption_date(fn_text)
                if adoption:
                    plan_adoption_date = adoption

    # Post-transaction ownership
    post_shares = _safe_float(
        _xml_text(tx_el, ".//postTransactionAmounts/sharesOwnedFollowingTransaction/value")
    )
    # Ownership nature
    own_nature = _xml_text(tx_el, ".//ownershipNature/directOrIndirectOwnership/value") or "D"
    indirect_expl = _xml_text(tx_el, ".//ownershipNature/natureOfOwnership/value")

    flags = rel_flags or {}
    source = f"Form 4 {tx_date_str}"
    return InsiderTransaction(
        insider_name=sourced_str(owner_name, source) if owner_name else None,
        title=sourced_str(owner_title, source) if owner_title else None,
        transaction_date=sourced_str(tx_date_str, source),
        transaction_type=TX_CODE_MAP.get(tx_code, "OTHER"),
        transaction_code=tx_code,
        shares=sourced_float(shares_val, source) if shares_val is not None else None,
        price_per_share=sourced_float(price_val, source) if price_val is not None else None,
        total_value=sourced_float(total_val, source) if total_val is not None else None,
        is_10b5_1=(
            SourcedValue[bool](
                value=is_10b5_1, source=source,
                confidence=Confidence.HIGH, as_of=now(),
            )
            if is_10b5_1 is not None else None
        ),
        # Unknown 10b5-1 status should be treated as potentially discretionary
        # (conservative for D&O risk). Only mark as non-discretionary when
        # we have explicit evidence of a 10b5-1 plan.
        is_discretionary=not is_10b5_1 if is_10b5_1 is not None else True,
        plan_adoption_date=plan_adoption_date,
        shares_owned_following=(
            sourced_float(post_shares, source) if post_shares is not None else None
        ),
        is_director=bool(flags.get("is_director", False)),
        is_officer=bool(flags.get("is_officer", False)),
        is_ten_pct_owner=bool(flags.get("is_ten_pct_owner", False)),
        ownership_nature=own_nature,
        indirect_ownership_explanation=indirect_expl,
        accession_number=str(flags.get("accession_number", "")),
        is_amendment=bool(flags.get("is_amendment", False)),
    )


def _safe_float(val: str) -> float | None:
    """Safely parse a string to float."""
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Form 4 document extraction
# ---------------------------------------------------------------------------


def _extract_from_form4s(state: AnalysisState) -> list[InsiderTransaction]:
    """Extract transactions from Form 4 filing documents."""
    from do_uw.stages.extract.insider_trading_analysis import (
        _deduplicate_transactions,
    )

    docs = get_filing_documents(state)
    form4_docs = docs.get("4", [])
    if not form4_docs:
        return []

    all_txns: list[InsiderTransaction] = []
    for doc in form4_docs:
        full_text = str(doc.get("full_text", ""))
        if not full_text.strip():
            continue
        accession = str(doc.get("accession_number", ""))
        form_type = str(doc.get("form_type", "4"))
        is_amendment = "/A" in form_type or form_type == "4/A"
        all_txns.extend(
            parse_form4_xml(full_text, accession_number=accession, is_amendment=is_amendment)
        )

    # Deduplicate 4/A over original Form 4
    all_txns = _deduplicate_transactions(all_txns)

    cutoff_str = (
        datetime.now(tz=UTC) - timedelta(days=LOOKBACK_MONTHS * 30)
    ).strftime("%Y-%m-%d")

    filtered = [
        tx for tx in all_txns
        if tx.transaction_date and tx.transaction_date.value >= cutoff_str
    ]
    filtered.sort(
        key=lambda t: t.transaction_date.value if t.transaction_date else "",
        reverse=True,
    )
    logger.info(
        "Parsed %d insider transactions from %d Form 4 documents",
        len(filtered), len(form4_docs),
    )
    return filtered


# Re-export yfinance functions for backward compatibility.
from do_uw.stages.extract.insider_trading_yfinance import (  # noqa: E402, F401
    _extract_from_yfinance,
    classify_yfinance_text,
    detect_10b5_1_from_text,
    normalize_date,
)


# ---------------------------------------------------------------------------
# Cluster detection
# ---------------------------------------------------------------------------


def detect_cluster_selling(
    transactions: list[InsiderTransaction],
    window_days: int = 30,
    min_insiders: int = 3,
) -> list[InsiderClusterEvent]:
    """Detect cluster selling events using a sliding window.

    A cluster event occurs when >= min_insiders unique insiders
    sell within window_days of each other.
    """
    sales = [
        tx for tx in transactions
        if tx.transaction_type == "SELL"
        and tx.transaction_date is not None
        and tx.insider_name is not None
    ]
    if len(sales) < min_insiders:
        return []

    sales.sort(
        key=lambda t: t.transaction_date.value if t.transaction_date else ""
    )

    clusters: list[InsiderClusterEvent] = []
    seen_windows: set[str] = set()

    for i, anchor in enumerate(sales):
        anchor_date = anchor.transaction_date
        if anchor_date is None:
            continue
        try:
            anchor_dt = datetime.strptime(anchor_date.value, "%Y-%m-%d")
        except ValueError:
            continue

        window_end_str = (anchor_dt + timedelta(days=window_days)).strftime("%Y-%m-%d")

        insiders_in_window: dict[str, float] = {}
        for tx in sales[i:]:
            td, tn = tx.transaction_date, tx.insider_name
            if td is None or tn is None:
                continue
            if td.value > window_end_str:
                break
            val = tx.total_value.value if tx.total_value else 0.0
            insiders_in_window[tn.value] = insiders_in_window.get(tn.value, 0.0) + val

        if len(insiders_in_window) >= min_insiders:
            window_key = anchor_date.value
            if window_key not in seen_windows:
                seen_windows.add(window_key)
                actual_end = anchor_date.value
                for tx in sales[i:]:
                    if (
                        tx.transaction_date
                        and tx.transaction_date.value <= window_end_str
                        and tx.insider_name
                        and tx.insider_name.value in insiders_in_window
                    ):
                        actual_end = tx.transaction_date.value

                clusters.append(InsiderClusterEvent(
                    start_date=anchor_date.value,
                    end_date=actual_end,
                    insider_count=len(insiders_in_window),
                    insiders=sorted(insiders_in_window.keys()),
                    total_value=sum(insiders_in_window.values()),
                ))

    return clusters


# ---------------------------------------------------------------------------
# Aggregate computation
# ---------------------------------------------------------------------------


# Codes excluded from buy/sell aggregation (gifts, estate transfers).
EXCLUDED_CODES: set[str] = {"G", "W"}
# Compensation codes excluded entirely from output (RSU vesting, tax withhold).
COMPENSATION_CODES: set[str] = {"A", "F"}


def compute_aggregates(
    transactions: list[InsiderTransaction],
) -> dict[str, Any]:
    """Compute aggregate insider trading metrics.

    Excludes gift/estate (G, W) from buy/sell totals and
    RSU/tax (A, F) entirely from output.
    """
    total_sold = 0.0
    total_bought = 0.0
    sales_count = 0
    sales_10b5_1 = 0
    comp_excluded = 0

    for tx in transactions:
        code = tx.transaction_code
        if code in COMPENSATION_CODES:
            comp_excluded += 1
            continue
        if code in EXCLUDED_CODES:
            continue
        val = tx.total_value.value if tx.total_value else 0.0
        if tx.transaction_type == "SELL":
            total_sold += val
            sales_count += 1
            if tx.is_10b5_1 and tx.is_10b5_1.value is True:
                sales_10b5_1 += 1
        elif tx.transaction_type == "BUY":
            total_bought += val

    if total_sold == 0.0 and total_bought == 0.0:
        net_direction = "NEUTRAL"
    elif total_sold > total_bought * 1.5:
        net_direction = "NET_SELLING"
    elif total_bought > total_sold * 1.5:
        net_direction = "NET_BUYING"
    else:
        net_direction = "NEUTRAL"

    pct_10b5_1 = (sales_10b5_1 / sales_count * 100.0) if sales_count > 0 else 0.0

    return {
        "total_sold_value": total_sold,
        "total_bought_value": total_bought,
        "net_direction": net_direction,
        "pct_10b5_1": pct_10b5_1,
        "compensation_excluded": comp_excluded,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_insider_trading(
    state: AnalysisState,
) -> tuple[InsiderTradingAnalysis, ExtractionReport]:
    """Extract insider trading analysis from Form 4s and yfinance."""
    analysis = InsiderTradingAnalysis()
    found: list[str] = []
    warnings: list[str] = []
    fallbacks: list[str] = []
    source_filing = "Form 4 filings + yfinance"

    transactions = _extract_from_form4s(state)
    if not transactions:
        transactions = _extract_from_yfinance(state)
        if transactions:
            fallbacks.append("yfinance insider_transactions")
            source_filing = "yfinance insider_transactions"

    if not transactions:
        warnings.append("No insider transaction data available")
        report = create_report(
            extractor_name="insider_trading", expected=EXPECTED_FIELDS,
            found=found, source_filing=source_filing,
            fallbacks_used=fallbacks, warnings=warnings,
        )
        log_report(report)
        return analysis, report

    analysis.transactions = transactions
    found.append("transactions")

    clusters = detect_cluster_selling(transactions)
    analysis.cluster_events = clusters
    found.append("cluster_events")
    if clusters:
        warnings.append(f"Cluster selling detected: {len(clusters)} event(s)")

    aggs = compute_aggregates(transactions)
    analysis.net_buying_selling = sourced_str(
        cast(str, aggs["net_direction"]), source_filing, Confidence.MEDIUM,
    )
    found.append("net_direction")

    analysis.pct_10b5_1 = sourced_float(
        cast(float, aggs["pct_10b5_1"]), source_filing, Confidence.MEDIUM,
    )
    found.append("10b5_1_classification")

    if aggs["total_sold_value"] > 0 or aggs["total_bought_value"] > 0:
        found.append("aggregate_ownership")

    # Phase 71-02: Exercise-sell patterns
    exercise_sell_events = detect_exercise_sell_patterns(transactions)
    analysis.exercise_sell_events = exercise_sell_events
    if exercise_sell_events:
        warnings.append(
            f"Exercise-sell patterns detected: {len(exercise_sell_events)} event(s)"
        )

    # Phase 71-02: Filing timing analysis
    eight_k_filings = get_eight_k_filings(state)
    timing_suspects = analyze_filing_timing(transactions, eight_k_filings)
    analysis.timing_suspects = timing_suspects
    if timing_suspects:
        red_flags = [s for s in timing_suspects if s.severity == "RED_FLAG"]
        warnings.append(
            f"Filing timing suspects: {len(timing_suspects)} "
            f"({len(red_flags)} RED_FLAG)"
        )

    # Phase 71-01: Ownership concentration + trajectories
    from do_uw.stages.extract.insider_trading_analysis import (
        run_ownership_analysis,
    )

    ownership_warnings = run_ownership_analysis(
        transactions, clusters, analysis,
    )
    warnings.extend(ownership_warnings)

    report = create_report(
        extractor_name="insider_trading", expected=EXPECTED_FIELDS,
        found=found, source_filing=source_filing,
        fallbacks_used=fallbacks, warnings=warnings,
    )
    log_report(report)
    return analysis, report
