"""Insider trading analysis: deduplication, ownership concentration, trajectory.

Split from insider_trading.py for 500-line compliance (Phase 71).
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from do_uw.models.market_events import (
    InsiderClusterEvent,
    InsiderTransaction,
    OwnershipConcentrationAlert,
    OwnershipTrajectoryPoint,
)

logger = logging.getLogger(__name__)

# C-suite title patterns for elevated alert levels.
_C_SUITE_PATTERN = re.compile(
    r"(?i)\b(CEO|CFO|COO|CLO|CTO|CIO|CISO|Chief)\b"
)

# Ownership concentration thresholds (from brain signal config).
_RED_FLAG_PCT = 50.0
_WARNING_PCT = 25.0
_LOOKBACK_MONTHS = 6


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def _deduplicate_transactions(
    transactions: list[InsiderTransaction],
) -> list[InsiderTransaction]:
    """Deduplicate transactions, preferring 4/A amendments over originals.

    Groups by (insider_name, transaction_date, transaction_code).
    If a group has both amendment and non-amendment entries, marks
    originals as is_superseded=True but retains them in the list.
    """
    groups: dict[tuple[str, str, str], list[InsiderTransaction]] = defaultdict(list)

    for tx in transactions:
        name = tx.insider_name.value if tx.insider_name else ""
        date = tx.transaction_date.value if tx.transaction_date else ""
        code = tx.transaction_code
        groups[(name, date, code)].append(tx)

    result: list[InsiderTransaction] = []
    for _key, group in groups.items():
        amendments = [t for t in group if t.is_amendment]
        originals = [t for t in group if not t.is_amendment]

        if amendments and originals:
            # Mark originals as superseded, keep the amendment
            for orig in originals:
                orig.is_superseded = True
            result.extend(originals)
            result.extend(amendments)
        else:
            result.extend(group)

    return result


# ---------------------------------------------------------------------------
# Ownership concentration
# ---------------------------------------------------------------------------


def _is_c_suite(tx: InsiderTransaction) -> bool:
    """Check if insider is C-suite based on title and is_officer flag."""
    title = tx.title.value if tx.title else ""
    if _C_SUITE_PATTERN.search(title):
        return True
    return False


def _get_role(tx: InsiderTransaction) -> str:
    """Extract role label from transaction."""
    if tx.title and tx.title.value:
        return tx.title.value
    if tx.is_officer:
        return "Officer"
    if tx.is_director:
        return "Director"
    return "Unknown"


def compute_ownership_concentration(
    transactions: list[InsiderTransaction],
    cluster_events: list[InsiderClusterEvent],
) -> list[OwnershipConcentrationAlert]:
    """Compute ownership concentration alerts with tiered severity.

    Returns alerts for insiders who sold significant portions of their
    holdings. C-suite gets WARNING/RED_FLAG; directors get INFORMATIONAL.
    10b5-1 plans reduce severity. Cluster overlap compounds severity.
    """
    cluster_names: set[str] = set()
    for cluster in cluster_events:
        cluster_names.update(cluster.insiders)

    # Group by insider
    by_insider: dict[str, list[InsiderTransaction]] = defaultdict(list)
    for tx in transactions:
        name = tx.insider_name.value if tx.insider_name else ""
        if not name:
            continue
        by_insider[name].append(tx)

    alerts: list[OwnershipConcentrationAlert] = []

    for name, txns in by_insider.items():
        # Separate buys and sells
        sells = [t for t in txns if t.transaction_code == "S"]
        buys = [t for t in txns if t.transaction_code == "P"]

        # Handle purchases as POSITIVE signal
        if buys and not sells:
            sample = buys[0]
            alerts.append(OwnershipConcentrationAlert(
                insider_name=name,
                role=_get_role(sample),
                severity="POSITIVE",
                personal_pct_sold=0.0,
                shares_sold=0.0,
                shares_remaining=(
                    sample.shares_owned_following.value
                    if sample.shares_owned_following else 0.0
                ),
                lookback_months=_LOOKBACK_MONTHS,
                is_10b5_1=False,
                is_c_suite=_is_c_suite(sample),
                compounds_with_cluster=False,
            ))
            continue

        if not sells:
            continue

        # Compute total shares sold and remaining
        total_sold = sum(
            (t.shares.value if t.shares else 0.0) for t in sells
        )
        # Use last transaction's shares_owned_following as remaining
        sells_with_following = [
            t for t in sells if t.shares_owned_following is not None
        ]
        if not sells_with_following:
            continue

        # Sort by date to get most recent
        sells_with_following.sort(
            key=lambda t: t.transaction_date.value if t.transaction_date else "",
        )
        last_tx = sells_with_following[-1]
        shares_remaining = last_tx.shares_owned_following.value if last_tx.shares_owned_following else 0.0

        # personal_pct = sold / (sold + remaining) * 100
        total_holding = total_sold + shares_remaining
        if total_holding <= 0:
            continue
        personal_pct = (total_sold / total_holding) * 100.0

        sample = sells[0]
        c_suite = _is_c_suite(sample)
        has_10b5_1 = any(
            t.is_10b5_1 and t.is_10b5_1.value is True for t in sells
        )
        in_cluster = name in cluster_names

        # Determine severity
        severity = _determine_severity(
            personal_pct, c_suite, has_10b5_1, in_cluster,
        )

        alerts.append(OwnershipConcentrationAlert(
            insider_name=name,
            role=_get_role(sample),
            severity=severity,
            personal_pct_sold=round(personal_pct, 1),
            outstanding_pct=None,
            shares_sold=total_sold,
            shares_remaining=shares_remaining,
            lookback_months=_LOOKBACK_MONTHS,
            is_10b5_1=has_10b5_1,
            is_c_suite=c_suite,
            compounds_with_cluster=in_cluster,
        ))

    return alerts


def _determine_severity(
    pct_sold: float,
    is_c_suite: bool,
    is_10b5_1: bool,
    in_cluster: bool,
) -> str:
    """Determine alert severity based on thresholds and role."""
    if not is_c_suite:
        return "INFORMATIONAL"

    # Base severity from percentage
    if pct_sold >= _RED_FLAG_PCT:
        severity = "RED_FLAG"
    elif pct_sold >= _WARNING_PCT:
        severity = "WARNING"
    else:
        return "INFORMATIONAL"

    # 10b5-1 reduces severity by one level
    if is_10b5_1:
        severity = "WARNING" if severity == "RED_FLAG" else "INFORMATIONAL"

    # Cluster overlap compounds (raises by one level)
    if in_cluster:
        if severity == "WARNING":
            severity = "RED_FLAG"
        elif severity == "INFORMATIONAL":
            severity = "WARNING"

    return severity


def build_ownership_trajectories(
    transactions: list[InsiderTransaction],
) -> dict[str, list[OwnershipTrajectoryPoint]]:
    """Build ownership timeline from shares_owned_following sequence."""
    by_insider: dict[str, list[InsiderTransaction]] = defaultdict(list)
    for tx in transactions:
        name = tx.insider_name.value if tx.insider_name else ""
        if name and tx.shares_owned_following is not None:
            by_insider[name].append(tx)

    trajectories: dict[str, list[OwnershipTrajectoryPoint]] = {}
    for name, txns in by_insider.items():
        txns.sort(key=lambda t: t.transaction_date.value if t.transaction_date else "")
        points: list[OwnershipTrajectoryPoint] = []
        for tx in txns:
            shares_val = tx.shares.value if tx.shares else 0.0
            change = shares_val if tx.transaction_type == "BUY" else -shares_val
            points.append(OwnershipTrajectoryPoint(
                date=tx.transaction_date.value if tx.transaction_date else "",
                shares_owned=tx.shares_owned_following.value if tx.shares_owned_following else 0.0,
                transaction_type=tx.transaction_type,
                change=change,
            ))
        if points:
            trajectories[name] = points

    return trajectories


# ---------------------------------------------------------------------------
# Pipeline wiring wrapper (Phase 74)
# ---------------------------------------------------------------------------


def run_ownership_analysis(
    transactions: list[InsiderTransaction],
    cluster_events: list[InsiderClusterEvent],
    analysis: "InsiderTradingAnalysis",
) -> list[str]:
    """Run ownership concentration + trajectory, return warning messages.

    Modifies *analysis* in place (sets ownership_alerts and
    ownership_trajectories) and returns a list of human-readable
    warning strings suitable for the extraction report.
    """
    warnings: list[str] = []

    alerts = compute_ownership_concentration(transactions, cluster_events)
    analysis.ownership_alerts = alerts
    if alerts:
        red_flags = [a for a in alerts if a.severity == "RED_FLAG"]
        warnings.append(
            f"Ownership concentration alerts: {len(alerts)} "
            f"({len(red_flags)} RED_FLAG)"
        )

    trajectories = build_ownership_trajectories(transactions)
    analysis.ownership_trajectories = trajectories

    return warnings
