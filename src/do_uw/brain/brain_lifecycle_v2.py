"""Brain signal lifecycle state machine: 5-state model with transition proposals.

LEARN-04: INCUBATING -> ACTIVE -> MONITORING -> DEPRECATED -> ARCHIVED.
Transitions proposed by compute_lifecycle_proposals() based on fire rate,
consecutive runs, feedback reactions, days in state. Written to brain_proposals
for confirmation via brain apply-proposal.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import duckdb
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LifecycleState(StrEnum):
    """Signal lifecycle states."""

    INCUBATING = "INCUBATING"
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


VALID_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.INCUBATING: {LifecycleState.ACTIVE, LifecycleState.ARCHIVED},
    LifecycleState.ACTIVE: {LifecycleState.MONITORING, LifecycleState.DEPRECATED},
    LifecycleState.MONITORING: {LifecycleState.ACTIVE, LifecycleState.DEPRECATED},
    LifecycleState.DEPRECATED: {LifecycleState.ARCHIVED, LifecycleState.ACTIVE},
    LifecycleState.ARCHIVED: set(),  # Terminal -- no transitions out
}

# Map legacy states to new lifecycle states
LEGACY_STATE_MAP: dict[str, LifecycleState] = {
    "INACTIVE": LifecycleState.DEPRECATED,
    "RETIRED": LifecycleState.ARCHIVED,
    "ACTIVE": LifecycleState.ACTIVE,
    "INCUBATING": LifecycleState.INCUBATING,
    "MONITORING": LifecycleState.MONITORING,
    "DEPRECATED": LifecycleState.DEPRECATED,
    "ARCHIVED": LifecycleState.ARCHIVED,
}



class TransitionProposal(BaseModel):
    """A proposed lifecycle state transition for a signal."""

    signal_id: str
    current_state: LifecycleState
    proposed_state: LifecycleState
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: str = "MEDIUM"  # LOW | MEDIUM | HIGH


class LifecycleReport(BaseModel):
    """Result of lifecycle analysis across all signals."""

    proposals: list[TransitionProposal] = Field(default_factory=list)
    total_signals_analyzed: int = 0
    by_state: dict[str, int] = Field(default_factory=dict)
    summary: str = ""



def is_valid_transition(
    from_state: LifecycleState,
    to_state: LifecycleState,
) -> bool:
    """Check whether a lifecycle transition is allowed."""
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def normalize_lifecycle_state(raw: str | None) -> LifecycleState:
    """Map raw YAML/DB value to LifecycleState.

    None -> ACTIVE (signals without explicit lifecycle_state).
    "INACTIVE" -> DEPRECATED (legacy mapping).
    "RETIRED" -> ARCHIVED (legacy mapping).
    Unknown values -> ACTIVE (safe default).
    """
    if raw is None:
        return LifecycleState.ACTIVE
    return LEGACY_STATE_MAP.get(raw.upper(), LifecycleState.ACTIVE)



def _get_signal_run_stats(conn: duckdb.DuckDBPyConnection, signal_id: str) -> dict[str, Any]:
    """Query brain_signal_runs for total_runs, fire_rate, last_3_fire_rates."""
    row = conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN status='TRIGGERED' THEN 1 ELSE 0 END), "
        "MIN(run_date) FROM brain_signal_runs "
        "WHERE signal_id = ? AND is_backtest = FALSE", [signal_id],
    ).fetchone()
    total_runs = row[0] if row else 0
    fire_count = row[1] if row else 0
    fire_rate = fire_count / total_runs if total_runs > 0 else 0.0

    last_3_rows = conn.execute(
        "SELECT status FROM brain_signal_runs WHERE signal_id = ? AND is_backtest = FALSE "
        "ORDER BY run_date DESC LIMIT 3", [signal_id],
    ).fetchall()
    last_3 = [1.0 if r[0] == "TRIGGERED" else 0.0 for r in last_3_rows]

    return {"total_runs": total_runs, "fire_count": fire_count,
            "fire_rate": fire_rate, "first_run_date": row[2] if row else None,
            "last_3_fire_rates": last_3}


def _get_disagree_count(conn: duckdb.DuckDBPyConnection, signal_id: str) -> int:
    """Count pending DISAGREE reactions for a signal."""
    row = conn.execute(
        "SELECT COUNT(*) FROM brain_feedback "
        "WHERE signal_id = ? AND reaction_type = 'DISAGREE' AND status = 'PENDING'",
        [signal_id],
    ).fetchone()
    return row[0] if row else 0


def _to_aware_dt(val: Any) -> datetime | None:
    """Convert a raw DB timestamp to timezone-aware datetime, or None."""
    if val is None:
        return None
    dt = datetime.fromisoformat(val) if isinstance(val, str) else val
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _get_days_in_state(conn: duckdb.DuckDBPyConnection, signal_id: str, current_state: str) -> int:
    """Days since last lifecycle change, falling back to first run date."""
    row = conn.execute(
        "SELECT MAX(changed_at) FROM brain_changelog "
        "WHERE signal_id = ? AND change_type = 'LIFECYCLE_TRANSITION'", [signal_id],
    ).fetchone()
    ref = _to_aware_dt(row[0] if row else None)

    if ref is None:
        row = conn.execute(
            "SELECT MIN(run_date) FROM brain_signal_runs "
            "WHERE signal_id = ? AND is_backtest = FALSE", [signal_id],
        ).fetchone()
        ref = _to_aware_dt(row[0] if row else None)

    return (datetime.now(timezone.utc) - ref).days if ref else 0


def _has_recent_feedback(conn: duckdb.DuckDBPyConnection, signal_id: str) -> bool:
    """Check if signal has any pending feedback (objections to archival)."""
    row = conn.execute(
        "SELECT COUNT(*) FROM brain_feedback WHERE signal_id = ? AND status = 'PENDING'",
        [signal_id],
    ).fetchone()
    return (row[0] if row else 0) > 0



def evaluate_transition(
    conn: duckdb.DuckDBPyConnection, signal_id: str, current_state: LifecycleState,
) -> TransitionProposal | None:
    """Evaluate whether a signal should transition based on locked criteria."""
    run_stats = _get_signal_run_stats(conn, signal_id)
    disagree_count = _get_disagree_count(conn, signal_id)
    days_in_state = _get_days_in_state(conn, signal_id, current_state.value)

    total_runs = run_stats["total_runs"]
    fire_rate = run_stats["fire_rate"]
    last_3 = run_stats.get("last_3_fire_rates", [])

    evidence = {
        "fire_rate": round(fire_rate, 4),
        "total_runs": total_runs,
        "disagree_count": disagree_count,
        "days_in_state": days_in_state,
        "last_3_fire_rates": last_3,
    }

    # Determine confidence based on data volume
    if total_runs >= 25:
        confidence = "HIGH"
    elif total_runs >= 10:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    if current_state == LifecycleState.INCUBATING:
        return _evaluate_incubating(signal_id, run_stats, disagree_count, evidence, confidence)

    if current_state == LifecycleState.ACTIVE:
        return _evaluate_active(signal_id, run_stats, disagree_count, last_3, evidence, confidence)

    if current_state == LifecycleState.MONITORING:
        return _evaluate_monitoring(signal_id, run_stats, evidence, confidence)

    if current_state == LifecycleState.DEPRECATED:
        return _evaluate_deprecated(signal_id, conn, days_in_state, evidence, confidence)

    # ARCHIVED: terminal, no transitions
    return None


def _evaluate_incubating(
    signal_id: str,
    run_stats: dict[str, Any],
    disagree_count: int,
    evidence: dict[str, Any],
    confidence: str,
) -> TransitionProposal | None:
    """INCUBATING -> ACTIVE: 5+ runs, fire rate 5-80%, 0 DISAGREE."""
    total_runs = run_stats["total_runs"]
    fire_rate = run_stats["fire_rate"]

    if total_runs >= 5 and 0.05 <= fire_rate <= 0.80 and disagree_count == 0:
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.INCUBATING,
            proposed_state=LifecycleState.ACTIVE,
            reason=(
                f"Graduated: {total_runs} runs, "
                f"{fire_rate:.1%} fire rate (healthy 5-80% range), "
                f"no DISAGREE feedback"
            ),
            evidence=evidence,
            confidence=confidence,
        )
    return None


def _evaluate_active(
    signal_id: str,
    run_stats: dict[str, Any],
    disagree_count: int,
    last_3: list[float],
    evidence: dict[str, Any],
    confidence: str,
) -> TransitionProposal | None:
    """ACTIVE -> MONITORING: fire rate anomaly or feedback issues."""
    fire_rate = run_stats["fire_rate"]

    # Check for 3+ DISAGREE reactions
    if disagree_count >= 3:
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.ACTIVE,
            proposed_state=LifecycleState.MONITORING,
            reason=(
                f"Feedback concern: {disagree_count} DISAGREE reactions pending"
            ),
            evidence=evidence,
            confidence=confidence,
        )

    # Check for high fire rate (>80%) for 3+ consecutive runs
    if len(last_3) >= 3 and all(r > 0.80 for r in last_3) and fire_rate > 0.80:
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.ACTIVE,
            proposed_state=LifecycleState.MONITORING,
            reason=(
                f"Always fires: {fire_rate:.1%} overall fire rate, "
                f"last 3 runs all TRIGGERED"
            ),
            evidence=evidence,
            confidence=confidence,
        )

    # Check for low fire rate (<2%) for 3+ consecutive runs
    if len(last_3) >= 3 and all(r < 0.02 for r in last_3) and fire_rate < 0.02:
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.ACTIVE,
            proposed_state=LifecycleState.MONITORING,
            reason=(
                f"Never fires: {fire_rate:.1%} overall fire rate, "
                f"last 3 runs all CLEAR"
            ),
            evidence=evidence,
            confidence=confidence,
        )

    return None


def _evaluate_monitoring(
    signal_id: str,
    run_stats: dict[str, Any],
    evidence: dict[str, Any],
    confidence: str,
) -> TransitionProposal | None:
    """MONITORING -> ACTIVE (recalibrated) or MONITORING -> DEPRECATED."""
    fire_rate = run_stats["fire_rate"]
    total_runs = run_stats["total_runs"]

    # If fire rate is back in healthy range, propose return to ACTIVE
    if 0.05 <= fire_rate <= 0.80:
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.MONITORING,
            proposed_state=LifecycleState.ACTIVE,
            reason=(
                f"Recalibrated: fire rate {fire_rate:.1%} "
                f"now in healthy 5-80% range"
            ),
            evidence=evidence,
            confidence=confidence,
        )

    # If still anomalous after 10+ runs, propose DEPRECATED
    if total_runs >= 10 and (fire_rate > 0.80 or fire_rate < 0.05):
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.MONITORING,
            proposed_state=LifecycleState.DEPRECATED,
            reason=(
                f"Still anomalous after {total_runs} runs: "
                f"fire rate {fire_rate:.1%} "
                f"({'always fires' if fire_rate > 0.80 else 'never fires'})"
            ),
            evidence=evidence,
            confidence=confidence,
        )

    return None


def _evaluate_deprecated(
    signal_id: str,
    conn: duckdb.DuckDBPyConnection,
    days_in_state: int,
    evidence: dict[str, Any],
    confidence: str,
) -> TransitionProposal | None:
    """DEPRECATED -> ARCHIVED: 90+ days with no objections."""
    if days_in_state >= 90 and not _has_recent_feedback(conn, signal_id):
        return TransitionProposal(
            signal_id=signal_id,
            current_state=LifecycleState.DEPRECATED,
            proposed_state=LifecycleState.ARCHIVED,
            reason=(
                f"Eligible for archive: {days_in_state} days deprecated, "
                f"no pending feedback"
            ),
            evidence=evidence,
            confidence="HIGH",  # Time-based criteria is deterministic
        )
    return None



def generate_lifecycle_proposals(
    conn: duckdb.DuckDBPyConnection,
    proposals: list[TransitionProposal],
) -> int:
    """Write lifecycle transition proposals to brain_proposals.

    Returns count of proposals inserted.
    """
    count = 0
    for p in proposals:
        proposed_changes = json.dumps({
            "from_state": p.current_state.value,
            "to_state": p.proposed_state.value,
            "lifecycle_state": p.proposed_state.value,
        })
        backtest_results = json.dumps(p.evidence)

        conn.execute(
            """INSERT INTO brain_proposals
               (source_type, source_ref, signal_id, proposal_type,
                proposed_changes, backtest_results, rationale, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')""",
            [
                "CALIBRATION",
                "brain_lifecycle_v2.py",
                p.signal_id,
                "LIFECYCLE_TRANSITION",
                proposed_changes,
                backtest_results,
                p.reason,
            ],
        )
        count += 1

    return count



def compute_lifecycle_proposals(
    conn: duckdb.DuckDBPyConnection,
    signal_overrides: dict[str, LifecycleState] | None = None,
) -> LifecycleReport:
    """Orchestrate lifecycle analysis across all signals.

    For each signal, normalizes lifecycle state, evaluates transition criteria,
    collects proposals, writes them to brain_proposals, and returns a report.

    Args:
        conn: DuckDB connection with brain schema.
        signal_overrides: Optional dict of signal_id -> LifecycleState for
            testing (bypasses BrainLoader, uses run data in DB directly).

    Returns:
        LifecycleReport with proposals and state distribution.
    """
    proposals: list[TransitionProposal] = []
    state_counts: Counter[str] = Counter()

    if signal_overrides:
        # Testing mode: use provided signal states
        for signal_id, state in signal_overrides.items():
            state_counts[state.value] += 1
            proposal = evaluate_transition(conn, signal_id, state)
            if proposal:
                proposals.append(proposal)
    else:
        # Production mode: load signals from BrainLoader
        from do_uw.brain.brain_unified_loader import load_signals

        signals_data = load_signals()
        all_signals = signals_data.get("signals", [])

        for sig in all_signals:
            signal_id = sig.get("id", "")
            raw_state = sig.get("lifecycle_state")
            state = normalize_lifecycle_state(raw_state)
            state_counts[state.value] += 1

            proposal = evaluate_transition(conn, signal_id, state)
            if proposal:
                proposals.append(proposal)

    # Write proposals to DuckDB
    proposals_written = 0
    if proposals:
        proposals_written = generate_lifecycle_proposals(conn, proposals)

    total_analyzed = sum(state_counts.values())
    by_state = dict(state_counts)

    # Build summary
    state_parts = [f"{count} {state}" for state, count in sorted(by_state.items())]
    summary = (
        f"Analyzed {total_analyzed} signals. "
        f"Distribution: {', '.join(state_parts)}. "
        f"{proposals_written} transition{'s' if proposals_written != 1 else ''} proposed."
    )

    return LifecycleReport(
        proposals=proposals,
        total_signals_analyzed=total_analyzed,
        by_state=by_state,
        summary=summary,
    )


__all__ = [
    "LifecycleReport",
    "LifecycleState",
    "TransitionProposal",
    "VALID_TRANSITIONS",
    "compute_lifecycle_proposals",
    "evaluate_transition",
    "generate_lifecycle_proposals",
    "is_valid_transition",
    "normalize_lifecycle_state",
]
