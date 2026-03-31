"""Brain co-occurrence mining engine: discovers correlated signals from pipeline run data.

Analyzes brain_signal_runs to find signal pairs that co-fire on >70% of
companies, classifies them as redundancy (same prefix) vs risk correlation
(cross prefix), detects prefix-level redundancy clusters, and generates
CORRELATION_ANNOTATION proposals for YAML write-back.

Key functions:
  - mine_cooccurrences: DuckDB cross-join query for co-firing signal pairs
  - detect_redundancy_clusters: Groups same-prefix pairs into clusters
  - generate_correlation_proposals: Writes proposals to brain_proposals
  - compute_correlation_report: Orchestrates full analysis
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CorrelatedPair(BaseModel):
    """A pair of signals that co-fire above (or below) a threshold."""

    signal_a: str
    signal_b: str
    co_fire_count: int
    co_fire_rate: float
    a_fire_count: int
    b_fire_count: int
    correlation_type: str  # "potential_redundancy" | "risk_correlation"


class RedundancyCluster(BaseModel):
    """A group of 3+ same-prefix signals that all co-fire above threshold."""

    prefix: str
    signal_ids: list[str]
    co_fire_rates: list[float]
    recommendation: str


class CorrelationReport(BaseModel):
    """Full correlation analysis report."""

    correlated_pairs: list[CorrelatedPair] = Field(default_factory=list)
    redundancy_clusters: list[RedundancyCluster] = Field(default_factory=list)
    total_pairs_analyzed: int = 0
    above_threshold_count: int = 0
    below_threshold_count: int = 0
    excluded_high_fire_rate: int = 0
    proposals_generated: int = 0


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DEFAULT_CO_FIRE_THRESHOLD = 0.70
_DEFAULT_HIGH_FIRE_RATE = 0.80


def get_co_fire_threshold(brain_config_dir: Path | None = None) -> float:
    """Load co-fire threshold from brain/config/learning_config.json.

    Falls back to 0.70 if file missing or key absent.
    """
    if brain_config_dir is not None:
        config_path = brain_config_dir / "learning_config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return float(data.get("co_fire_threshold", _DEFAULT_CO_FIRE_THRESHOLD))
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
    return _DEFAULT_CO_FIRE_THRESHOLD


def _get_high_fire_rate_threshold(brain_config_dir: Path | None = None) -> float:
    """Load high fire rate exclusion threshold from config. Default 0.80."""
    if brain_config_dir is not None:
        config_path = brain_config_dir / "learning_config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return float(data.get("high_fire_rate_threshold", _DEFAULT_HIGH_FIRE_RATE))
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
    return _DEFAULT_HIGH_FIRE_RATE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_prefix(signal_id: str) -> str:
    """Extract prefix from signal ID: first 2 dot-separated segments.

    Example: "FIN.LIQ.current" -> "FIN.LIQ"
    """
    parts = signal_id.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return signal_id


def _classify_correlation(sig_a: str, sig_b: str) -> str:
    """Return 'potential_redundancy' if same prefix, 'risk_correlation' if different."""
    return (
        "potential_redundancy"
        if _extract_prefix(sig_a) == _extract_prefix(sig_b)
        else "risk_correlation"
    )


# ---------------------------------------------------------------------------
# Core mining
# ---------------------------------------------------------------------------


def _get_high_fire_rate_signals(
    conn: duckdb.DuckDBPyConnection,
    high_fire_rate_threshold: float = _DEFAULT_HIGH_FIRE_RATE,
) -> set[str]:
    """Identify signals with fire_rate > threshold for exclusion."""
    rows = conn.execute(
        """
        SELECT signal_id,
               SUM(CASE WHEN status = 'TRIGGERED' THEN 1 ELSE 0 END) * 1.0
                   / COUNT(*) AS fire_rate
        FROM brain_signal_runs
        WHERE is_backtest = FALSE
        GROUP BY signal_id
        HAVING fire_rate > ?
        """,
        [high_fire_rate_threshold],
    ).fetchall()
    return {r[0] for r in rows}


def mine_cooccurrences(
    conn: duckdb.DuckDBPyConnection,
    threshold: float = _DEFAULT_CO_FIRE_THRESHOLD,
    excluded_signal_ids: set[str] | None = None,
) -> tuple[list[CorrelatedPair], list[CorrelatedPair]]:
    """Execute DuckDB cross-join query for co-firing signal pairs.

    Returns:
        Tuple of (above_threshold_pairs, below_threshold_pairs).
        Both lists contain CorrelatedPair with classification.
    """
    if excluded_signal_ids is None:
        excluded_signal_ids = set()

    # Build exclusion clause
    exclude_clause = ""
    params: list[Any] = []
    if excluded_signal_ids:
        placeholders = ", ".join("?" for _ in excluded_signal_ids)
        exclude_clause = f"AND signal_id NOT IN ({placeholders})"
        params.extend(sorted(excluded_signal_ids))

    # Co-occurrence mining SQL
    query = f"""
    WITH fired AS (
        SELECT DISTINCT run_id, signal_id
        FROM brain_signal_runs
        WHERE status = 'TRIGGERED' AND is_backtest = FALSE
        {exclude_clause}
    ),
    sig_totals AS (
        SELECT signal_id, COUNT(DISTINCT run_id) AS total_fires
        FROM fired
        GROUP BY signal_id
    ),
    pairs AS (
        SELECT a.signal_id AS sig_a, b.signal_id AS sig_b,
               COUNT(DISTINCT a.run_id) AS co_fire_count,
               sa.total_fires AS a_total,
               sb.total_fires AS b_total
        FROM fired a
        JOIN fired b ON a.run_id = b.run_id AND a.signal_id < b.signal_id
        JOIN sig_totals sa ON sa.signal_id = a.signal_id
        JOIN sig_totals sb ON sb.signal_id = b.signal_id
        GROUP BY a.signal_id, b.signal_id, sa.total_fires, sb.total_fires
    )
    SELECT sig_a, sig_b, co_fire_count,
           ROUND(co_fire_count * 1.0 / LEAST(a_total, b_total), 4) AS co_fire_rate,
           a_total, b_total
    FROM pairs
    ORDER BY co_fire_rate DESC, sig_a, sig_b
    """

    rows = conn.execute(query, params).fetchall()

    above: list[CorrelatedPair] = []
    below: list[CorrelatedPair] = []

    for sig_a, sig_b, co_fire_count, co_fire_rate, a_total, b_total in rows:
        pair = CorrelatedPair(
            signal_a=sig_a,
            signal_b=sig_b,
            co_fire_count=co_fire_count,
            co_fire_rate=float(co_fire_rate),
            a_fire_count=a_total,
            b_fire_count=b_total,
            correlation_type=_classify_correlation(sig_a, sig_b),
        )
        if co_fire_rate >= threshold:
            above.append(pair)
        else:
            below.append(pair)

    return above, below


# ---------------------------------------------------------------------------
# Redundancy detection
# ---------------------------------------------------------------------------


def detect_redundancy_clusters(
    pairs: list[CorrelatedPair],
) -> list[RedundancyCluster]:
    """Group same-prefix above-threshold pairs into redundancy clusters.

    Only flags clusters with 3+ distinct signals in the same prefix where
    all pairwise combinations appear in the above-threshold pairs.
    """
    # Collect same-prefix pairs
    prefix_signals: dict[str, set[str]] = defaultdict(set)
    prefix_rates: dict[str, list[float]] = defaultdict(list)
    prefix_pair_set: dict[str, set[tuple[str, str]]] = defaultdict(set)

    for p in pairs:
        if p.correlation_type == "potential_redundancy":
            prefix = _extract_prefix(p.signal_a)
            prefix_signals[prefix].add(p.signal_a)
            prefix_signals[prefix].add(p.signal_b)
            prefix_rates[prefix].append(p.co_fire_rate)
            prefix_pair_set[prefix].add((p.signal_a, p.signal_b))

    clusters: list[RedundancyCluster] = []
    for prefix, signals in prefix_signals.items():
        if len(signals) < 3:
            continue

        # Verify all pairwise combinations exist above threshold
        signal_list = sorted(signals)
        all_paired = True
        for i in range(len(signal_list)):
            for j in range(i + 1, len(signal_list)):
                pair_key = (signal_list[i], signal_list[j])
                reverse_key = (signal_list[j], signal_list[i])
                if pair_key not in prefix_pair_set[prefix] and reverse_key not in prefix_pair_set[prefix]:
                    all_paired = False
                    break
            if not all_paired:
                break

        if all_paired:
            clusters.append(
                RedundancyCluster(
                    prefix=prefix,
                    signal_ids=signal_list,
                    co_fire_rates=prefix_rates[prefix],
                    recommendation=(
                        f"Consider consolidating {len(signal_list)} signals "
                        f"in {prefix} -- all co-fire >70%"
                    ),
                )
            )

    return clusters


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def store_correlations(
    conn: duckdb.DuckDBPyConnection,
    above: list[CorrelatedPair],
    below: list[CorrelatedPair] | None = None,
) -> None:
    """Store discovered correlations in brain_correlations table.

    Deletes existing rows then inserts fresh data.
    """
    conn.execute("DELETE FROM brain_correlations")

    for pair in above:
        conn.execute(
            """INSERT INTO brain_correlations
               (signal_a, signal_b, co_fire_count, co_fire_rate,
                a_fire_count, b_fire_count, correlation_type, above_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)""",
            [
                pair.signal_a,
                pair.signal_b,
                pair.co_fire_count,
                pair.co_fire_rate,
                pair.a_fire_count,
                pair.b_fire_count,
                pair.correlation_type,
            ],
        )

    if below:
        for pair in below:
            conn.execute(
                """INSERT INTO brain_correlations
                   (signal_a, signal_b, co_fire_count, co_fire_rate,
                    a_fire_count, b_fire_count, correlation_type, above_threshold)
                   VALUES (?, ?, ?, ?, ?, ?, ?, FALSE)""",
                [
                    pair.signal_a,
                    pair.signal_b,
                    pair.co_fire_count,
                    pair.co_fire_rate,
                    pair.a_fire_count,
                    pair.b_fire_count,
                    pair.correlation_type,
                ],
            )


# ---------------------------------------------------------------------------
# Proposal generation
# ---------------------------------------------------------------------------


def generate_correlation_proposals(
    conn: duckdb.DuckDBPyConnection,
    pairs: list[CorrelatedPair],
) -> int:
    """Generate CORRELATION_ANNOTATION proposals for above-threshold pairs.

    For each pair, generates two proposals (one per signal side) with
    proposed_changes = {"correlated_signals": [other_signal_id]}.

    Returns count of proposals generated.
    """
    # Aggregate correlated signals per signal_id
    correlated_map: dict[str, list[str]] = defaultdict(list)
    for p in pairs:
        correlated_map[p.signal_a].append(p.signal_b)
        correlated_map[p.signal_b].append(p.signal_a)

    count = 0
    for signal_id, correlated_signals in correlated_map.items():
        # Deduplicate
        unique_correlated = sorted(set(correlated_signals))
        proposed_changes = json.dumps({"correlated_signals": unique_correlated})
        rationale = (
            f"Signal {signal_id} co-fires >70% with: "
            f"{', '.join(unique_correlated)}. "
            f"Consider annotating YAML with correlated_signals for transparency."
        )

        conn.execute(
            """INSERT INTO brain_proposals
               (source_type, source_ref, signal_id, proposal_type,
                proposed_changes, rationale, status)
               VALUES (?, ?, ?, ?, ?, ?, 'PENDING')""",
            [
                "CORRELATION_MINING",
                "brain_correlation.py",
                signal_id,
                "CORRELATION_ANNOTATION",
                proposed_changes,
                rationale,
            ],
        )
        count += 1

    return count


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def compute_correlation_report(
    conn: duckdb.DuckDBPyConnection,
    threshold: float | None = None,
    brain_config_dir: Path | None = None,
) -> CorrelationReport:
    """Orchestrate full co-occurrence analysis.

    1. Load threshold from config (or use parameter)
    2. Identify high-fire-rate signals for exclusion
    3. Run mine_cooccurrences excluding high-fire signals
    4. Detect redundancy clusters
    5. Store correlations
    6. Generate proposals
    7. Return complete report

    Args:
        conn: DuckDB connection with brain schema.
        threshold: Override co-fire threshold (default: from config or 0.70).
        brain_config_dir: Path to brain/config/ for learning_config.json.

    Returns:
        CorrelationReport with all results.
    """
    if threshold is None:
        threshold = get_co_fire_threshold(brain_config_dir)

    # Find high fire rate signals to exclude
    high_fr_threshold = _get_high_fire_rate_threshold(brain_config_dir)
    high_fr_signals = _get_high_fire_rate_signals(conn, high_fr_threshold)

    # Mine co-occurrences
    above, below = mine_cooccurrences(
        conn,
        threshold=threshold,
        excluded_signal_ids=high_fr_signals,
    )

    # Detect redundancy clusters
    clusters = detect_redundancy_clusters(above)

    # Store all correlations
    store_correlations(conn, above, below)

    # Generate proposals for above-threshold pairs
    proposals_count = generate_correlation_proposals(conn, above)

    return CorrelationReport(
        correlated_pairs=above,
        redundancy_clusters=clusters,
        total_pairs_analyzed=len(above) + len(below),
        above_threshold_count=len(above),
        below_threshold_count=len(below),
        excluded_high_fire_rate=len(high_fr_signals),
        proposals_generated=proposals_count,
    )


__all__ = [
    "CorrelatedPair",
    "CorrelationReport",
    "RedundancyCluster",
    "compute_correlation_report",
    "detect_redundancy_clusters",
    "generate_correlation_proposals",
    "get_co_fire_threshold",
    "mine_cooccurrences",
    "store_correlations",
]
