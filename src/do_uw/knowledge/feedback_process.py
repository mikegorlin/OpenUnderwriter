"""Feedback processing: aggregate reactions into calibration proposals.

Batch-processes pending underwriter reactions into brain calibration
proposals with confidence scoring and impact projections.

Functions:
    process_pending_reactions: Main entry point -- aggregate and generate proposals
    aggregate_reactions: Group reactions by signal and determine consensus
    compute_fire_rate_impact: Project fire rate change for a signal
    compute_score_impact: Project score impact across historical runs
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

import duckdb
from pydantic import BaseModel

from do_uw.knowledge.feedback_models import (
    FeedbackReaction,
    ProposalRecord,
    ReactionType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal model
# ---------------------------------------------------------------------------


class AggregationResult(BaseModel):
    """Result of aggregating reactions for one signal."""

    signal_id: str
    total_reactions: int
    agree_count: int
    disagree_count: int
    adjust_count: int
    confidence: str  # LOW, MEDIUM, HIGH
    consensus: str  # AGREE, DISAGREE, ADJUST, CONFLICTED
    severity_targets: list[str]
    """Collected severity targets from ADJUST_SEVERITY reactions."""
    rationale_summary: str
    """Combined rationale from reactions contributing to consensus."""
    reaction_ids: list[int]
    """Feedback IDs of reactions that contributed."""


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_reactions(
    grouped_reactions: dict[str, list[FeedbackReaction]],
) -> list[AggregationResult]:
    """Aggregate reactions per signal into consensus results.

    Rules:
    - Confidence: LOW (1 entry), MEDIUM (2-3), HIGH (4+)
    - AGREE majority (> disagree + adjust) -> consensus=AGREE (no proposal needed)
    - DISAGREE majority (>= adjust, and > agree) -> consensus=DISAGREE
    - ADJUST_SEVERITY majority (> disagree, and > agree) -> consensus=ADJUST
    - No direction >60% of total -> consensus=CONFLICTED
    """
    results: list[AggregationResult] = []

    for signal_id, reactions in grouped_reactions.items():
        total = len(reactions)
        agree = sum(1 for r in reactions if r.reaction_type == ReactionType.AGREE)
        disagree = sum(
            1 for r in reactions if r.reaction_type == ReactionType.DISAGREE
        )
        adjust = sum(
            1 for r in reactions if r.reaction_type == ReactionType.ADJUST_SEVERITY
        )

        confidence = "LOW" if total == 1 else ("MEDIUM" if total <= 3 else "HIGH")

        # Determine consensus
        max_count = max(agree, disagree, adjust)
        consensus: str

        if total == 1:
            # Single reaction: direct mapping
            if agree == 1:
                consensus = "AGREE"
            elif disagree == 1:
                consensus = "DISAGREE"
            else:
                consensus = "ADJUST"
        elif max_count / total > 0.6:
            # Clear majority (>60%)
            if agree == max_count:
                consensus = "AGREE"
            elif disagree == max_count:
                consensus = "DISAGREE"
            else:
                consensus = "ADJUST"
        else:
            consensus = "CONFLICTED"

        # Collect severity targets from ADJUST reactions
        severity_targets = [
            r.severity_target
            for r in reactions
            if r.reaction_type == ReactionType.ADJUST_SEVERITY and r.severity_target
        ]

        # Build rationale summary from contributing reactions
        if consensus == "AGREE":
            contributing = [
                r for r in reactions if r.reaction_type == ReactionType.AGREE
            ]
        elif consensus == "DISAGREE":
            contributing = [
                r for r in reactions if r.reaction_type == ReactionType.DISAGREE
            ]
        elif consensus == "ADJUST":
            contributing = [
                r
                for r in reactions
                if r.reaction_type == ReactionType.ADJUST_SEVERITY
            ]
        else:
            contributing = reactions  # CONFLICTED: include all

        rationale_parts = [r.rationale for r in contributing if r.rationale]
        rationale_summary = "; ".join(rationale_parts[:5])  # Cap at 5 for readability
        if len(rationale_parts) > 5:
            rationale_summary += f" (+{len(rationale_parts) - 5} more)"

        reaction_ids = [r.feedback_id for r in reactions if r.feedback_id is not None]

        results.append(
            AggregationResult(
                signal_id=signal_id,
                total_reactions=total,
                agree_count=agree,
                disagree_count=disagree,
                adjust_count=adjust,
                confidence=confidence,
                consensus=consensus,
                severity_targets=severity_targets,
                rationale_summary=rationale_summary,
                reaction_ids=reaction_ids,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Impact projections
# ---------------------------------------------------------------------------


def compute_fire_rate_impact(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> dict[str, Any]:
    """Compute historical fire rate for a signal from brain_signal_runs.

    Returns dict with total_runs, triggered_count, fire_rate_pct,
    and human-readable description.
    """
    try:
        row = conn.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) as triggered,
                SUM(CASE WHEN status NOT IN ('SKIPPED') THEN 1 ELSE 0 END) as evaluated
               FROM brain_signal_runs
               WHERE signal_id = ? AND is_backtest = FALSE""",
            [signal_id],
        ).fetchone()

        if row is None or row[0] == 0:
            return {
                "total_runs": 0,
                "triggered_count": 0,
                "fire_rate_pct": 0.0,
                "description": "No historical data",
            }

        total_runs = row[0]
        triggered = row[1] or 0
        evaluated = row[2] or 0

        fire_rate = (triggered / evaluated * 100) if evaluated > 0 else 0.0

        return {
            "total_runs": total_runs,
            "triggered_count": triggered,
            "evaluated_count": evaluated,
            "fire_rate_pct": round(fire_rate, 1),
            "description": f"Triggered {triggered}/{evaluated} runs ({fire_rate:.1f}%)",
        }

    except Exception:
        logger.exception("Fire rate query failed for %s", signal_id)
        return {
            "total_runs": 0,
            "triggered_count": 0,
            "fire_rate_pct": 0.0,
            "description": "Query failed",
        }


def compute_score_impact(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> dict[str, Any]:
    """Estimate score impact from disabling/relaxing a signal.

    Queries brain_signal_runs for distinct tickers where this signal
    fired, and returns the count. Detailed score recalculation would
    require re-running the scoring pipeline, which is out of scope --
    we report the number of affected companies instead.

    Returns dict with affected_tickers, ticker_list.
    """
    try:
        rows = conn.execute(
            """SELECT DISTINCT ticker
               FROM brain_signal_runs
               WHERE signal_id = ? AND status IN ('RED', 'YELLOW')
                 AND is_backtest = FALSE""",
            [signal_id],
        ).fetchall()

        tickers = [row[0] for row in rows]
        return {
            "affected_tickers": len(tickers),
            "ticker_list": tickers,
            "description": (
                f"Would affect scoring for {len(tickers)} ticker(s)"
                + (f": {', '.join(tickers[:5])}" if tickers else "")
            ),
        }

    except Exception:
        logger.exception("Score impact query failed for %s", signal_id)
        return {
            "affected_tickers": 0,
            "ticker_list": [],
            "description": "Query failed",
        }


# ---------------------------------------------------------------------------
# Proposal generation
# ---------------------------------------------------------------------------


def generate_proposals(
    conn: duckdb.DuckDBPyConnection,
    aggregated: list[AggregationResult],
) -> list[ProposalRecord]:
    """Generate calibration proposals from aggregated reaction results.

    Skips AGREE consensus (signal working correctly) and generates
    CONFLICTED proposals that require manual review.

    For DISAGREE: proposes THRESHOLD_CHANGE or DEACTIVATION.
    For ADJUST: proposes THRESHOLD_CHANGE with specific severity target.

    Returns list of ProposalRecord objects (already inserted into brain_proposals).
    """
    proposals: list[ProposalRecord] = []

    for agg in aggregated:
        if agg.consensus == "AGREE":
            # Signal is working correctly -- no proposal needed
            logger.info(
                "Signal %s: AGREE consensus (%d/%d), no proposal generated",
                agg.signal_id,
                agg.agree_count,
                agg.total_reactions,
            )
            continue

        # Compute impact data for the proposal
        fire_rate = compute_fire_rate_impact(conn, agg.signal_id)
        score_impact = compute_score_impact(conn, agg.signal_id)

        backtest_results = {
            "fire_rate": fire_rate,
            "score_impact": score_impact,
            "confidence": agg.confidence,
            "reaction_counts": {
                "agree": agg.agree_count,
                "disagree": agg.disagree_count,
                "adjust": agg.adjust_count,
                "total": agg.total_reactions,
            },
        }

        proposal_type: str
        proposed_changes: dict[str, Any]
        rationale: str
        status: str = "PENDING"

        if agg.consensus == "DISAGREE":
            # Strong disagreement: propose deactivation for HIGH confidence,
            # threshold relaxation for MEDIUM/LOW
            if agg.confidence == "HIGH" and agg.disagree_count >= 4:
                proposal_type = "DEACTIVATION"
                proposed_changes = {"lifecycle_state": "INACTIVE"}
                rationale = (
                    f"Disagree consensus ({agg.disagree_count}/{agg.total_reactions}, "
                    f"confidence: {agg.confidence}): {agg.rationale_summary}"
                )
            else:
                proposal_type = "THRESHOLD_CHANGE"
                proposed_changes = {"_direction": "relax"}  # Direction hint for apply
                rationale = (
                    f"Disagree consensus ({agg.disagree_count}/{agg.total_reactions}, "
                    f"confidence: {agg.confidence}): {agg.rationale_summary}"
                )

        elif agg.consensus == "ADJUST":
            proposal_type = "THRESHOLD_CHANGE"
            # Determine target severity from majority
            if agg.severity_targets:
                target_counts = Counter(agg.severity_targets)
                target_severity = target_counts.most_common(1)[0][0]
            else:
                target_severity = "MEDIUM"  # Default if no specific target

            proposed_changes = {"severity_target": target_severity}
            rationale = (
                f"Adjust severity consensus -> {target_severity} "
                f"({agg.adjust_count}/{agg.total_reactions}, "
                f"confidence: {agg.confidence}): {agg.rationale_summary}"
            )

        elif agg.consensus == "CONFLICTED":
            # Insert as a CONFLICTED proposal requiring manual resolution
            proposal_type = "THRESHOLD_CHANGE"
            proposed_changes = {"_conflicted": True}
            rationale = (
                f"CONFLICTED: {agg.agree_count} agree, {agg.disagree_count} disagree, "
                f"{agg.adjust_count} adjust ({agg.total_reactions} total). "
                f"Manual review required. Rationale: {agg.rationale_summary}"
            )
            status = "CONFLICTED"

        else:
            continue

        # Insert into brain_proposals
        source_ref = f"reactions_{agg.signal_id}"
        conn.execute(
            """INSERT INTO brain_proposals
               (source_type, source_ref, signal_id, proposal_type,
                proposed_changes, backtest_results, rationale, status)
               VALUES ('FEEDBACK', ?, ?, ?, ?, ?, ?, ?)""",
            [
                source_ref,
                agg.signal_id,
                proposal_type,
                json.dumps(proposed_changes),
                json.dumps(backtest_results),
                rationale,
                status,
            ],
        )

        # Retrieve the generated proposal_id
        result = conn.execute(
            "SELECT MAX(proposal_id) FROM brain_proposals"
        ).fetchone()
        proposal_id = result[0] if result else 0

        proposals.append(
            ProposalRecord(
                proposal_id=proposal_id,
                source_type="FEEDBACK",
                source_ref=source_ref,
                signal_id=agg.signal_id,
                proposal_type=proposal_type,  # type: ignore[arg-type]
                proposed_changes=proposed_changes,
                backtest_results=backtest_results,
                rationale=rationale,
                status=status,
            )
        )

        logger.info(
            "Generated %s proposal (ID: %d) for %s [%s, confidence: %s]",
            proposal_type,
            proposal_id,
            agg.signal_id,
            agg.consensus,
            agg.confidence,
        )

    return proposals


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def process_pending_reactions(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[list[AggregationResult], list[ProposalRecord]]:
    """Main entry point: aggregate pending reactions and generate proposals.

    1. Query all PENDING reactions grouped by signal_id
    2. Run aggregation algorithm for each signal
    3. Generate proposals for non-AGREE consensus results
    4. Mark processed reactions as PROCESSED

    Returns (aggregation_results, generated_proposals).
    """
    from do_uw.knowledge.feedback import get_pending_reactions

    # Step 1: Get grouped reactions
    grouped = get_pending_reactions(conn)

    if not grouped:
        return [], []

    # Step 2: Aggregate
    aggregated = aggregate_reactions(grouped)

    # Step 3: Generate proposals
    proposals = generate_proposals(conn, aggregated)

    # Step 4: Mark processed reactions as PROCESSED
    all_reaction_ids: list[int] = []
    for agg in aggregated:
        all_reaction_ids.extend(agg.reaction_ids)

    if all_reaction_ids:
        placeholders = ",".join(["?"] * len(all_reaction_ids))
        conn.execute(
            f"UPDATE brain_feedback SET status = 'PROCESSED' "
            f"WHERE feedback_id IN ({placeholders})",
            all_reaction_ids,
        )
        logger.info("Marked %d reactions as PROCESSED", len(all_reaction_ids))

    return aggregated, proposals
