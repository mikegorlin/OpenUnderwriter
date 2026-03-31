"""XBRL quarterly trend computation.

Computes QoQ, YoY, acceleration, and sequential pattern trends
from quarterly XBRL data (QuarterlyStatements). These trend signals
are critical for underwriting risk assessment -- detecting margin
compression, revenue deceleration, and cash flow deterioration.

Created in Phase 68-02.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from do_uw.models.common import SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TrendResult:
    """Trend analysis result for a single financial concept.

    Captures QoQ changes, YoY changes, acceleration, consecutive
    decline count, and detected sequential pattern.
    """

    concept: str
    qoq_changes: list[float | None] = field(default_factory=lambda: [])
    yoy_changes: list[float | None] = field(default_factory=lambda: [])
    acceleration: float | None = None
    consecutive_decline: int = 0
    pattern: str | None = None  # "compression", "deceleration", "deterioration"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Statement type to QuarterlyPeriod attribute mapping
_STATEMENT_ATTRS = {
    "income": "income",
    "balance": "balance",
    "cash_flow": "cash_flow",
}


def _extract_concept_values(
    quarters: list[QuarterlyPeriod],
    concept: str,
    statement: str,
) -> list[float | None]:
    """Pull the .value from SourcedValue for a concept across quarters.

    Args:
        quarters: List of QuarterlyPeriod, most recent first.
        concept: Concept name (e.g., "revenue").
        statement: Which dict to look in: "income", "balance", "cash_flow".

    Returns:
        List aligned with quarters. None if concept missing in that quarter.
    """
    attr = _STATEMENT_ATTRS.get(statement, statement)
    values: list[float | None] = []
    for q in quarters:
        stmt_dict: dict[str, SourcedValue[float]] = getattr(q, attr, {})
        sv = stmt_dict.get(concept)
        if sv is not None:
            values.append(float(sv.value))
        else:
            values.append(None)
    return values


# ---------------------------------------------------------------------------
# Core computation functions
# ---------------------------------------------------------------------------


def compute_qoq(values: list[float | None]) -> list[float | None]:
    """Compute sequential quarter-over-quarter percentage changes.

    values[0] is most recent quarter. Returns list of same length.
    result[i] for 1 <= i <= N-2 = (values[i] - values[i+1]) / |values[i+1]| * 100
    result[0] = None (most recent endpoint, no prior change to show).
    result[-1] = None (oldest, no prior quarter in dataset).

    None inputs propagate: if either value is None, result is None.
    Zero denominator returns None.
    """
    n = len(values)
    if n < 2:
        return [None] * n

    result: list[float | None] = [None] * n
    for i in range(1, n - 1):
        curr = values[i]
        prev = values[i + 1]
        if curr is None or prev is None or prev == 0:
            result[i] = None
        else:
            result[i] = (curr - prev) / abs(prev) * 100

    # result[0] and result[-1] stay None (endpoints)
    return result


def compute_yoy(
    quarters: list[QuarterlyPeriod],
    concept: str,
    statement: str,
) -> list[float | None]:
    """Compute same-quarter year-over-year percentage changes.

    Matches by fiscal_quarter to eliminate seasonality: Q1 FY2025
    compares to Q1 FY2024, not Q4 FY2024.

    Returns list aligned with quarters (most recent first).
    None when no matching prior-year quarter exists.
    """
    n = len(quarters)
    result: list[float | None] = [None] * n

    # Build lookup: (fiscal_quarter, fiscal_year) -> value
    attr = _STATEMENT_ATTRS.get(statement, statement)
    lookup: dict[tuple[int, int], float | None] = {}
    for q in quarters:
        stmt_dict: dict[str, SourcedValue[float]] = getattr(q, attr, {})
        sv = stmt_dict.get(concept)
        val = float(sv.value) if sv is not None else None
        lookup[(q.fiscal_quarter, q.fiscal_year)] = val

    for i, q in enumerate(quarters):
        curr_val = lookup.get((q.fiscal_quarter, q.fiscal_year))
        prior_val = lookup.get((q.fiscal_quarter, q.fiscal_year - 1))
        if curr_val is None or prior_val is None or prior_val == 0:
            result[i] = None
        else:
            result[i] = (curr_val - prior_val) / abs(prior_val) * 100

    return result


def compute_acceleration(qoq_changes: list[float | None]) -> float | None:
    """Compute acceleration: most recent valid QoQ minus prior valid QoQ.

    Positive = growth speeding up. Negative = growth slowing.
    Returns None if fewer than 2 non-None QoQ values exist.
    """
    valid = [v for v in qoq_changes if v is not None]
    if len(valid) < 2:
        return None
    return valid[0] - valid[1]


def detect_sequential_pattern(
    qoq_changes: list[float | None],
    concept: str,
    threshold: int = 4,
) -> tuple[str | None, int]:
    """Detect sequential decline patterns in QoQ changes.

    Scans for threshold+ consecutive negative values (ignoring None).
    Returns (pattern_name, consecutive_count).

    Pattern name based on concept keyword:
    - "margin" in concept -> "compression"
    - "growth" or "revenue" in concept -> "deceleration"
    - else -> "deterioration"

    Returns (None, 0) if no pattern meets threshold.
    """
    max_consecutive = 0
    current_streak = 0

    for v in qoq_changes:
        if v is not None and v < 0:
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        elif v is not None:
            current_streak = 0
        # None doesn't break the streak -- skip

    if max_consecutive < threshold:
        return None, 0

    # Determine pattern name from concept
    concept_lower = concept.lower()
    if "margin" in concept_lower:
        pattern_name = "compression"
    elif "growth" in concept_lower or "revenue" in concept_lower:
        pattern_name = "deceleration"
    else:
        pattern_name = "deterioration"

    return pattern_name, max_consecutive


# ---------------------------------------------------------------------------
# Integrated functions
# ---------------------------------------------------------------------------


def compute_trends(
    quarters: list[QuarterlyPeriod],
    concept: str,
    statement: str,
) -> TrendResult:
    """Compute all trend metrics for a single concept.

    Orchestrates: extract values -> QoQ -> YoY -> acceleration -> pattern.
    Returns a TrendResult with all metrics populated.
    """
    values = _extract_concept_values(quarters, concept, statement)
    qoq = compute_qoq(values)
    yoy = compute_yoy(quarters, concept, statement)
    accel = compute_acceleration(qoq)
    pattern, consecutive = detect_sequential_pattern(qoq, concept)

    return TrendResult(
        concept=concept,
        qoq_changes=qoq,
        yoy_changes=yoy,
        acceleration=accel,
        consecutive_decline=consecutive,
        pattern=pattern,
    )


def compute_all_trends(
    quarterly: QuarterlyStatements,
) -> dict[str, TrendResult]:
    """Compute trends for every concept with data in 2+ quarters.

    Iterates all concepts across income, balance, and cash_flow dicts
    in QuarterlyStatements. Returns dict keyed by concept name.
    """
    if len(quarterly.quarters) < 2:
        return {}

    # Collect all (concept, statement) pairs with data in 2+ quarters
    concept_counts: dict[tuple[str, str], int] = {}
    for q in quarterly.quarters:
        for stmt_name, attr in _STATEMENT_ATTRS.items():
            stmt_dict: dict[str, SourcedValue[float]] = getattr(q, attr, {})
            for concept_name in stmt_dict:
                key: tuple[str, str] = (concept_name, stmt_name)
                concept_counts[key] = concept_counts.get(key, 0) + 1

    results: dict[str, TrendResult] = {}
    for (concept_name, stmt_name), count in concept_counts.items():
        if count >= 2:
            results[concept_name] = compute_trends(
                quarterly.quarters, concept_name, stmt_name
            )

    return results
