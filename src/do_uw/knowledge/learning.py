"""Learning infrastructure for check effectiveness tracking.

Tracks analysis outcomes, computes check fire rates, identifies
co-firing partners, and detects redundant check pairs. Analysis
run data is stored as notes with the 'analysis_run' tag in the
existing knowledge store -- no new tables required.

This module enables the system to learn over time which checks
fire frequently, which always co-fire (potential redundancy),
and eventually (when claim data becomes available) which checks
correlate with actual claims.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Any

from do_uw.knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)

_ANALYSIS_RUN_TAG = "analysis_run"


@dataclass
class AnalysisOutcome:
    """Outcome of a single company analysis run.

    Captures which checks fired and which passed, along with
    the overall quality score and tier assignment.
    """

    ticker: str
    run_date: datetime
    checks_fired: list[str]
    checks_clear: list[str]
    quality_score: float
    tier: str


@dataclass
class SignalEffectiveness:
    """Effectiveness metrics for a single check.

    Computed from historical analysis runs: fire rate, co-firing
    partners, and recency of last firing.
    """

    signal_id: str
    signal_name: str
    total_runs: int
    times_fired: int
    fire_rate: float
    co_firing_partners: list[tuple[str, float]]
    last_fired: datetime | None


def _empty_partners() -> list[tuple[str, float]]:
    """Default factory for co_firing_partners (pyright strict)."""
    return []


def _serialize_outcome(outcome: AnalysisOutcome) -> str:
    """Serialize an AnalysisOutcome to JSON string."""
    data = {
        "ticker": outcome.ticker,
        "run_date": outcome.run_date.isoformat(),
        "checks_fired": outcome.checks_fired,
        "checks_clear": outcome.checks_clear,
        "quality_score": outcome.quality_score,
        "tier": outcome.tier,
    }
    return json.dumps(data)


def _deserialize_outcome(content: str) -> AnalysisOutcome | None:
    """Deserialize JSON string to AnalysisOutcome, or None on failure."""
    try:
        data: dict[str, Any] = json.loads(content)
        return AnalysisOutcome(
            ticker=str(data["ticker"]),
            run_date=datetime.fromisoformat(str(data["run_date"])),
            checks_fired=list(data.get("checks_fired", [])),
            checks_clear=list(data.get("checks_clear", [])),
            quality_score=float(data["quality_score"]),
            tier=str(data["tier"]),
        )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        logger.warning("Failed to deserialize analysis outcome: %s", exc)
        return None


def _load_all_outcomes(store: KnowledgeStore) -> list[AnalysisOutcome]:
    """Load all analysis run outcomes from the store."""
    outcomes: list[AnalysisOutcome] = []
    notes = store.query_notes_by_tag(_ANALYSIS_RUN_TAG)
    for note in notes:
        content = str(note.get("content", ""))
        outcome = _deserialize_outcome(content)
        if outcome is not None:
            outcomes.append(outcome)
    return outcomes


def record_analysis_run(
    store: KnowledgeStore, outcome: AnalysisOutcome
) -> None:
    """Record an analysis run outcome in the knowledge store.

    Stores the outcome as a note with the 'analysis_run' tag.
    The note content is a JSON-serialized AnalysisOutcome.

    Args:
        store: Knowledge store instance.
        outcome: Analysis outcome to record.
    """
    title = (
        f"Analysis Run: {outcome.ticker} "
        f"({outcome.run_date.strftime('%Y-%m-%d')})"
    )
    content = _serialize_outcome(outcome)
    store.add_note(
        title=title,
        content=content,
        tags=_ANALYSIS_RUN_TAG,
        source="analysis_pipeline",
    )
    logger.info(
        "Recorded analysis run for %s: %d signals fired, score=%.1f, tier=%s",
        outcome.ticker,
        len(outcome.checks_fired),
        outcome.quality_score,
        outcome.tier,
    )


def get_signal_effectiveness(
    store: KnowledgeStore, signal_id: str
) -> SignalEffectiveness:
    """Compute effectiveness metrics for a given check.

    Queries all recorded analysis runs to determine how often the
    check fires, what other checks co-fire with it, and when it
    last fired.

    Args:
        store: Knowledge store instance.
        signal_id: ID of the check to analyze.

    Returns:
        SignalEffectiveness with fire rate, co-firing partners, etc.
        Returns zero-valued metrics if no analysis runs exist.
    """
    outcomes = _load_all_outcomes(store)
    total_runs = len(outcomes)

    if total_runs == 0:
        return SignalEffectiveness(
            signal_id=signal_id,
            signal_name=_get_signal_name(store, signal_id),
            total_runs=0,
            times_fired=0,
            fire_rate=0.0,
            co_firing_partners=_empty_partners(),
            last_fired=None,
        )

    # Count times this check fired and track co-firing
    times_fired = 0
    co_fire_counts: Counter[str] = Counter()
    last_fired: datetime | None = None

    for outcome in outcomes:
        if signal_id in outcome.checks_fired:
            times_fired += 1
            if last_fired is None or outcome.run_date > last_fired:
                last_fired = outcome.run_date
            # Count co-firing partners
            for other_id in outcome.checks_fired:
                if other_id != signal_id:
                    co_fire_counts[other_id] += 1

    fire_rate = times_fired / total_runs if total_runs > 0 else 0.0

    # Compute co-occurrence rate relative to this check's fires
    co_firing_partners: list[tuple[str, float]] = []
    if times_fired > 0:
        for partner_id, count in co_fire_counts.items():
            co_occurrence_rate = count / times_fired
            co_firing_partners.append((partner_id, co_occurrence_rate))
    co_firing_partners.sort(key=lambda x: x[1], reverse=True)

    return SignalEffectiveness(
        signal_id=signal_id,
        signal_name=_get_signal_name(store, signal_id),
        total_runs=total_runs,
        times_fired=times_fired,
        fire_rate=fire_rate,
        co_firing_partners=co_firing_partners,
        last_fired=last_fired,
    )


def find_redundant_pairs(
    store: KnowledgeStore, threshold: float = 0.85
) -> list[tuple[str, str, float]]:
    """Find pairs of checks that nearly always co-fire.

    Two checks are considered potentially redundant if they co-fire
    in more than `threshold` fraction of the runs where either fires.

    The co-occurrence rate is: fires_together / fires_of_either
    (Jaccard similarity of fire sets).

    Args:
        store: Knowledge store instance.
        threshold: Minimum co-occurrence rate (default 0.85).

    Returns:
        List of (check_a, check_b, co_occurrence_rate) tuples,
        sorted by rate descending. Only pairs above threshold.
    """
    outcomes = _load_all_outcomes(store)
    if not outcomes:
        return []

    # Build fire sets for each check
    fire_sets: dict[str, set[int]] = {}
    for i, outcome in enumerate(outcomes):
        for signal_id in outcome.checks_fired:
            if signal_id not in fire_sets:
                fire_sets[signal_id] = set()
            fire_sets[signal_id].add(i)

    # Compute Jaccard similarity for each pair
    redundant: list[tuple[str, str, float]] = []
    signal_ids = sorted(fire_sets.keys())
    for id_a, id_b in combinations(signal_ids, 2):
        set_a = fire_sets[id_a]
        set_b = fire_sets[id_b]
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        if union == 0:
            continue
        jaccard = intersection / union
        if jaccard >= threshold:
            redundant.append((id_a, id_b, jaccard))

    redundant.sort(key=lambda x: x[2], reverse=True)
    return redundant


def get_learning_summary(store: KnowledgeStore) -> dict[str, Any]:
    """Generate a summary of learning data from all analysis runs.

    Provides aggregate metrics useful for understanding system
    behavior and identifying optimization opportunities.

    Args:
        store: Knowledge store instance.

    Returns:
        Dictionary with:
        - total_runs: Count of recorded analysis runs
        - top_fired_checks: Top 10 most-fired checks by fire rate
        - top_redundant_pairs: Top 10 redundant pairs by co-occurrence
        - average_quality_score: Mean quality score across runs
        - tier_distribution: Count of runs per tier
    """
    outcomes = _load_all_outcomes(store)
    total_runs = len(outcomes)

    if total_runs == 0:
        return {
            "total_runs": 0,
            "top_fired_checks": [],
            "top_redundant_pairs": [],
            "average_quality_score": 0.0,
            "tier_distribution": {},
        }

    # Count fires per check
    fire_counts: Counter[str] = Counter()
    for outcome in outcomes:
        for signal_id in outcome.checks_fired:
            fire_counts[signal_id] += 1

    # Top 10 most-fired checks by fire rate
    top_fired: list[dict[str, Any]] = []
    for signal_id, count in fire_counts.most_common(10):
        fire_rate = count / total_runs
        top_fired.append({
            "signal_id": signal_id,
            "signal_name": _get_signal_name(store, signal_id),
            "times_fired": count,
            "fire_rate": fire_rate,
        })

    # Top 10 redundant pairs
    redundant_pairs = find_redundant_pairs(store, threshold=0.0)
    top_redundant: list[dict[str, Any]] = []
    for check_a, check_b, rate in redundant_pairs[:10]:
        top_redundant.append({
            "check_a": check_a,
            "check_b": check_b,
            "co_occurrence_rate": rate,
        })

    # Average quality score
    total_quality = sum(o.quality_score for o in outcomes)
    avg_quality = total_quality / total_runs

    # Tier distribution
    tier_counts: Counter[str] = Counter()
    for outcome in outcomes:
        tier_counts[outcome.tier] += 1
    tier_distribution = dict(tier_counts)

    return {
        "total_runs": total_runs,
        "top_fired_checks": top_fired,
        "top_redundant_pairs": top_redundant,
        "average_quality_score": avg_quality,
        "tier_distribution": tier_distribution,
    }


def _get_signal_name(store: KnowledgeStore, signal_id: str) -> str:
    """Look up a check name from the store, falling back to signal_id."""
    check = store.get_check(signal_id)
    if check is not None:
        name = check.get("name", signal_id)
        return str(name)
    return signal_id
