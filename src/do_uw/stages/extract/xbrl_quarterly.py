"""Quarterly XBRL extraction from Company Facts API.

Extracts up to 8 quarters of standalone quarterly financial data using
the SEC's ``frame`` field for YTD disambiguation. The ``frame`` field
is present ONLY on standalone quarterly entries (``CY####Q#`` for
duration, ``CY####Q#I`` for instant) and absent on YTD cumulatives.

Usage:
    facts = state.acquired_data.filings["company_facts"]
    cik = str(state.company.identity.cik.value)
    quarterly = extract_quarterly_xbrl(facts, cik)
    state.extracted.financials.quarterly_xbrl = quarterly
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements
from do_uw.stages.extract.xbrl_mapping import (
    XBRLConcept,
    load_xbrl_mapping,
    normalize_sign,
    resolve_concept,
)

logger = logging.getLogger(__name__)

# Frame patterns for standalone quarterly data.
# Duration concepts (income, cash flow): CY2024Q1, CY2024Q2, etc.
QUARTERLY_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]$")
# Instant concepts (balance sheet): CY2024Q1I, CY2024Q2I, etc.
INSTANT_FRAME_RE = re.compile(r"^CY\d{4}Q[1-4]I$")

# Duration range for standalone quarter fallback (days).
MIN_QUARTER_DAYS = 70
MAX_QUARTER_DAYS = 105

# Statement type to QuarterlyPeriod dict key mapping.
STATEMENT_DICT_KEY: dict[str, str] = {
    "income": "income",
    "balance_sheet": "balance",
    "cash_flow": "cash_flow",
}


# ---------------------------------------------------------------------------
# Frame-based quarterly filtering
# ---------------------------------------------------------------------------


def select_standalone_quarters(
    entries: list[dict[str, Any]],
    period_type: str,
) -> list[dict[str, Any]]:
    """Select standalone quarterly entries, filtering out YTD cumulatives.

    Primary strategy: filter by ``frame`` regex (CY####Q# for duration,
    CY####Q#I for instant). Deduplicate by frame value, preferring the
    most recently filed entry.

    Fallback (duration only): when no framed entries exist, compute
    end - start duration and select entries with 70-105 day spans.

    Args:
        entries: XBRL fact entries (already filtered to 10-Q form type).
        period_type: ``"duration"`` or ``"instant"``.

    Returns:
        Standalone quarterly entries sorted by end date ascending.
    """
    pattern = INSTANT_FRAME_RE if period_type == "instant" else QUARTERLY_FRAME_RE

    # Primary: frame-based filtering.
    framed = [e for e in entries if pattern.match(e.get("frame", ""))]

    if framed:
        # Deduplicate by frame, prefer most recently filed.
        by_frame: dict[str, dict[str, Any]] = {}
        for entry in sorted(
            framed, key=lambda e: str(e.get("filed", "")),
        ):
            frame_val = entry["frame"]
            by_frame[frame_val] = entry  # later filed overwrites

        return sorted(
            by_frame.values(),
            key=lambda e: str(e.get("end", "")),
        )

    # Fallback (duration only): filter by start/end span.
    if period_type == "duration":
        standalone: list[dict[str, Any]] = []
        for entry in entries:
            start_str = entry.get("start")
            end_str = entry.get("end")
            if start_str and end_str:
                try:
                    start_dt = datetime.strptime(str(start_str), "%Y-%m-%d")
                    end_dt = datetime.strptime(str(end_str), "%Y-%m-%d")
                    days = (end_dt - start_dt).days
                    if MIN_QUARTER_DAYS <= days <= MAX_QUARTER_DAYS:
                        standalone.append(entry)
                except ValueError:
                    continue

        # Deduplicate by end+fp, prefer most recently filed.
        by_key: dict[str, dict[str, Any]] = {}
        for entry in sorted(
            standalone, key=lambda e: str(e.get("filed", "")),
        ):
            key = f"{entry.get('end', '')}_{entry.get('fp', '')}"
            by_key[key] = entry

        return sorted(
            by_key.values(),
            key=lambda e: str(e.get("end", "")),
        )

    return []


# ---------------------------------------------------------------------------
# SourcedValue construction for quarterly data
# ---------------------------------------------------------------------------


def _make_quarterly_sourced_value(
    value: float,
    concept_name: str,
    entry: dict[str, Any],
    cik: str,
    expected_sign: str = "any",
) -> SourcedValue[float]:
    """Build a SourcedValue from a quarterly XBRL fact entry.

    Source format: ``XBRL:10-Q:{end_date}:CIK{cik}:accn:{accn}``

    Args:
        value: Numeric value (already normalized if needed).
        concept_name: Canonical concept name.
        entry: XBRL fact entry dict.
        cik: Company CIK string.
        expected_sign: Sign convention for normalization.

    Returns:
        SourcedValue with XBRL:10-Q provenance at HIGH confidence.
    """
    end_date = entry.get("end", "unknown")
    accn = entry.get("accn", "unknown")
    source = f"XBRL:10-Q:{end_date}:CIK{cik}:accn:{accn}"

    as_of_str = str(entry.get("end", "2000-01-01"))
    try:
        as_of = datetime.strptime(as_of_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        as_of = datetime.now(tz=UTC)

    # Apply sign normalization.
    normalized_value, _ = normalize_sign(value, expected_sign, concept_name)

    return SourcedValue[float](
        value=normalized_value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=as_of,
    )


# ---------------------------------------------------------------------------
# Quarter building
# ---------------------------------------------------------------------------


def _parse_fiscal_quarter(fp: str) -> int:
    """Parse fiscal quarter integer from fp field (e.g. 'Q1' -> 1)."""
    if fp.startswith("Q") and len(fp) == 2:
        try:
            return int(fp[1])
        except ValueError:
            pass
    return 1


def _detect_fiscal_year_end_month(
    quarters: list[QuarterlyPeriod],
) -> int | None:
    """Detect fiscal year end month from quarterly period data.

    Uses the Q4 period end date if available, otherwise infers from
    the gap between fiscal and calendar periods.
    """
    for q in quarters:
        if q.fiscal_quarter == 4:
            # FY end month is the month of Q4's period_end.
            try:
                end_dt = datetime.strptime(q.period_end, "%Y-%m-%d")
                return end_dt.month
            except ValueError:
                continue

    # Fallback: look at Q1 and infer (Q1 end month - 3 = FY start month).
    for q in quarters:
        if q.fiscal_quarter == 1:
            try:
                end_dt = datetime.strptime(q.period_end, "%Y-%m-%d")
                # Q1 ends 3 months into FY; FY end = Q1 end + 9 months.
                fy_end_month = (end_dt.month + 9 - 1) % 12 + 1
                return fy_end_month
            except ValueError:
                continue

    return None


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def extract_quarterly_xbrl(
    facts: dict[str, Any],
    cik: str,
    mapping: dict[str, XBRLConcept] | None = None,
    max_quarters: int = 8,
) -> QuarterlyStatements:
    """Extract up to 8 quarters of XBRL financial data from Company Facts.

    Uses frame-based filtering to select standalone quarterly values,
    avoiding YTD cumulatives. Groups entries by frame value to build
    QuarterlyPeriod instances.

    Args:
        facts: Full Company Facts API response.
        cik: Company CIK string.
        mapping: Optional pre-loaded XBRL concept mapping. Loaded
            automatically if None.
        max_quarters: Maximum quarters to return (default 8).

    Returns:
        QuarterlyStatements with up to max_quarters populated.
    """
    if mapping is None:
        mapping = load_xbrl_mapping()

    concepts_attempted = 0
    concepts_resolved = 0

    # Collect quarterly entries by concept, grouped by frame.
    # Structure: frame_value -> concept_name -> entry
    frame_data: dict[str, dict[str, dict[str, Any]]] = {}
    # Track which statement type each concept belongs to.
    concept_statements: dict[str, str] = {}

    for concept_name, cfg in mapping.items():
        stmt_type = cfg["statement"]
        if stmt_type not in STATEMENT_DICT_KEY and stmt_type != "derived":
            continue
        if stmt_type == "derived":
            continue  # Skip derived concepts for quarterly extraction

        concepts_attempted += 1

        entries = resolve_concept(facts, mapping, concept_name, form_type="10-Q")
        if not entries:
            continue

        period_type = cfg["period_type"]
        standalone = select_standalone_quarters(entries, period_type)

        if not standalone:
            continue

        concepts_resolved += 1
        concept_statements[concept_name] = stmt_type

        for entry in standalone:
            # Determine the frame key for grouping.
            frame_val = entry.get("frame", "")
            if not frame_val:
                # Fallback: construct a pseudo-frame from end date + fp.
                end = entry.get("end", "")
                fp = entry.get("fp", "")
                frame_val = f"_fb_{end}_{fp}"

            if frame_val not in frame_data:
                frame_data[frame_val] = {}
            frame_data[frame_val][concept_name] = entry

    if not frame_data:
        logger.info("No quarterly XBRL data found for CIK%s", cik)
        return QuarterlyStatements(
            concepts_resolved=concepts_resolved,
            concepts_attempted=concepts_attempted,
            extraction_date=datetime.now(tz=UTC),
        )

    # Build QuarterlyPeriod for each frame.
    quarters: list[QuarterlyPeriod] = []

    for frame_val, entries_by_concept in frame_data.items():
        # Use the first entry to extract period metadata.
        sample_entry = next(iter(entries_by_concept.values()))
        fy = int(sample_entry.get("fy", 0))
        fp_str = str(sample_entry.get("fp", "Q1"))
        fq = _parse_fiscal_quarter(fp_str)
        period_end = str(sample_entry.get("end", ""))
        period_start = sample_entry.get("start")

        # Determine calendar_period from frame.
        if QUARTERLY_FRAME_RE.match(frame_val):
            calendar_period = frame_val
        elif INSTANT_FRAME_RE.match(frame_val):
            calendar_period = frame_val.rstrip("I")
        else:
            calendar_period = frame_val

        fiscal_label = f"Q{fq} FY{fy}"

        # Build statement dicts.
        income: dict[str, SourcedValue[float]] = {}
        balance: dict[str, SourcedValue[float]] = {}
        cash_flow_dict: dict[str, SourcedValue[float]] = {}

        statement_dicts = {
            "income": income,
            "balance_sheet": balance,
            "cash_flow": cash_flow_dict,
        }

        for concept_name, entry in entries_by_concept.items():
            stmt_type = concept_statements.get(concept_name, "")
            target = statement_dicts.get(stmt_type)
            if target is None:
                continue

            raw_val = float(entry.get("val", 0.0))
            expected_sign = mapping[concept_name]["expected_sign"]
            sv = _make_quarterly_sourced_value(
                raw_val, concept_name, entry, cik, expected_sign,
            )
            target[concept_name] = sv

            # Update period_start from duration entries.
            entry_start = entry.get("start")
            if entry_start and period_start is None:
                period_start = str(entry_start)

        qp = QuarterlyPeriod(
            fiscal_year=fy,
            fiscal_quarter=fq,
            fiscal_label=fiscal_label,
            calendar_period=calendar_period,
            period_end=period_end,
            period_start=str(period_start) if period_start else None,
            income=income,
            balance=balance,
            cash_flow=cash_flow_dict,
        )
        quarters.append(qp)

    # Sort most recent first, limit to max_quarters.
    quarters.sort(key=lambda q: q.period_end, reverse=True)
    quarters = quarters[:max_quarters]

    # Detect fiscal year end month.
    fy_end_month = _detect_fiscal_year_end_month(quarters)

    result = QuarterlyStatements(
        quarters=quarters,
        fiscal_year_end_month=fy_end_month,
        extraction_date=datetime.now(tz=UTC),
        concepts_resolved=concepts_resolved,
        concepts_attempted=concepts_attempted,
    )

    logger.info(
        "Quarterly XBRL extraction: %d quarters, %d/%d concepts resolved, "
        "FY end month=%s",
        len(quarters),
        concepts_resolved,
        concepts_attempted,
        fy_end_month,
    )

    return result
