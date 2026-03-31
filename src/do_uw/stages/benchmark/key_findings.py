"""Key findings selection for Executive Summary (SECT1-03/04).

Selects the top 5 key negatives and top 5 key positives for the
underwriting worksheet executive summary. Negatives come from red
flags, factor scores, and detected patterns. Positives come from
a catalog of positive indicator checks run against state data.

Multi-signal ranking for negatives:
- Scoring impact: 40% (points deducted, normalized)
- Recency: 20% (trajectory-based proxy)
- Trajectory: 20% (WORSENING > NEW > STABLE > IMPROVING)
- Claim correlation: 20% (allegation theory exposure)

Positive indicator catalog and check functions are in
positive_indicators.py (split for 500-line compliance).
"""

from __future__ import annotations

from dataclasses import dataclass

from do_uw.models.executive_summary import KeyFinding
from do_uw.models.scoring import FactorScore, PatternMatch
from do_uw.models.scoring_output import (
    AllegationMapping,
    FlaggedItem,
    FlagSeverity,
    RedFlagSummary,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.positive_indicators import (
    build_positive_indicators,
)

# -----------------------------------------------------------------------
# Ranking weight constants
# -----------------------------------------------------------------------

_W_SCORING_IMPACT = 0.40
_W_RECENCY = 0.20
_W_TRAJECTORY = 0.20
_W_CLAIM_CORRELATION = 0.20

_MAX_KEY_FINDINGS = 5

# Trajectory score mapping
_TRAJECTORY_SCORES: dict[str, float] = {
    "WORSENING": 1.0,
    "NEW": 0.7,
    "STABLE": 0.3,
    "IMPROVING": 0.0,
}

# Recency proxy based on trajectory (NEW items are most recent)
_RECENCY_SCORES: dict[str, float] = {
    "NEW": 1.0,
    "WORSENING": 0.8,
    "STABLE": 0.4,
    "IMPROVING": 0.2,
}

# Severity to scoring impact normalization
_SEVERITY_IMPACT: dict[FlagSeverity, float] = {
    FlagSeverity.CRITICAL: 1.0,
    FlagSeverity.HIGH: 0.75,
    FlagSeverity.MODERATE: 0.45,
    FlagSeverity.LOW: 0.2,
}


# -----------------------------------------------------------------------
# Negative finding candidate
# -----------------------------------------------------------------------


@dataclass
class _NegativeCandidate:
    """Internal representation for ranking negative findings."""

    evidence: str
    section_origin: str
    scoring_impact_label: str
    theory_mapping: str
    trajectory: str = "STABLE"
    severity: FlagSeverity = FlagSeverity.MODERATE
    points_deducted: float = 0.0
    max_points_possible: float = 15.0  # Default normalization basis


# -----------------------------------------------------------------------
# Scoring functions for negative ranking
# -----------------------------------------------------------------------


def _scoring_impact_score(candidate: _NegativeCandidate) -> float:
    """Normalize scoring impact to 0-1 range."""
    if candidate.points_deducted > 0 and candidate.max_points_possible > 0:
        return min(
            candidate.points_deducted / candidate.max_points_possible, 1.0,
        )
    return _SEVERITY_IMPACT.get(candidate.severity, 0.3)


def _recency_score(candidate: _NegativeCandidate) -> float:
    """Trajectory-based recency proxy. NEW = most recent."""
    return _RECENCY_SCORES.get(candidate.trajectory, 0.4)


def _trajectory_score(candidate: _NegativeCandidate) -> float:
    """WORSENING > NEW > STABLE > IMPROVING."""
    return _TRAJECTORY_SCORES.get(candidate.trajectory, 0.3)


def _claim_correlation_score(
    candidate: _NegativeCandidate,
    exposure_map: dict[str, str],
) -> float:
    """Map allegation theory to exposure level. HIGH=1, MOD=0.6, LOW=0.3."""
    theory = candidate.theory_mapping
    if not theory:
        return 0.1
    exposure = exposure_map.get(theory, "")
    if exposure == "HIGH":
        return 1.0
    if exposure == "MODERATE":
        return 0.6
    if exposure == "LOW":
        return 0.3
    return 0.1


def _rank_candidate(
    candidate: _NegativeCandidate,
    exposure_map: dict[str, str],
) -> float:
    """Compute composite ranking score for a negative candidate."""
    return (
        _W_SCORING_IMPACT * _scoring_impact_score(candidate)
        + _W_RECENCY * _recency_score(candidate)
        + _W_TRAJECTORY * _trajectory_score(candidate)
        + _W_CLAIM_CORRELATION
        * _claim_correlation_score(candidate, exposure_map)
    )


# -----------------------------------------------------------------------
# Build exposure map from AllegationMapping
# -----------------------------------------------------------------------


def _build_exposure_map(
    mapping: AllegationMapping | None,
) -> dict[str, str]:
    """Extract theory -> exposure_level from AllegationMapping."""
    if mapping is None:
        return {}
    result: dict[str, str] = {}
    for te in mapping.theories:
        result[te.theory.value] = te.exposure_level
    return result


# -----------------------------------------------------------------------
# Convert sources to candidates
# -----------------------------------------------------------------------


def _candidates_from_flags(
    items: list[FlaggedItem],
) -> list[_NegativeCandidate]:
    """Convert FlaggedItem list to ranking candidates."""
    candidates: list[_NegativeCandidate] = []
    for item in items:
        # Include source evidence in the narrative so downstream
        # renderers know WHY this flag fired (e.g., "Active SCA: Tucker v. Apple")
        evidence = item.description
        if item.source and item.source != "CRF evaluation":
            evidence = f"{item.description} — {item.source}"
        candidates.append(
            _NegativeCandidate(
                evidence=evidence,
                section_origin=item.source,
                scoring_impact_label=item.scoring_impact,
                theory_mapping=item.allegation_theory,
                trajectory=item.trajectory,
                severity=item.severity,
            ),
        )
    return candidates


def _candidates_from_factors(
    factor_scores: list[FactorScore],
) -> list[_NegativeCandidate]:
    """Convert high-deduction factor scores to ranking candidates.

    Filters out F3 (audit/accounting) when points_deducted < 1.0,
    since a clean Beneish M-Score (0/8 flags, below -2.22 threshold)
    should not surface as a key negative finding.
    """
    candidates: list[_NegativeCandidate] = []
    for fs in factor_scores:
        if fs.points_deducted < 3.0:
            continue  # Only include significant deductions
        # Guard: F3 (Audit & Accounting) with minimal deduction
        # should not appear as a key negative — a clean Beneish
        # M-Score (0/8 flags) means no real audit concern exists.
        if fs.factor_id == "F3" and fs.points_deducted < 2.0:
            continue
        evidence = (
            f"{fs.factor_name} ({fs.factor_id}): "
            f"{fs.points_deducted:.1f}/{fs.max_points} points deducted"
        )
        if fs.evidence:
            evidence += f" - {fs.evidence[0]}"
        candidates.append(
            _NegativeCandidate(
                evidence=evidence,
                section_origin=f"SECT7-{fs.factor_id}",
                scoring_impact_label=(
                    f"{fs.factor_id}: -{fs.points_deducted:.0f} points"
                ),
                theory_mapping="",
                points_deducted=fs.points_deducted,
                max_points_possible=float(fs.max_points),
                severity=FlagSeverity.HIGH
                if fs.points_deducted >= 8
                else FlagSeverity.MODERATE,
            ),
        )
    return candidates


def _candidates_from_patterns(
    patterns: list[PatternMatch],
) -> list[_NegativeCandidate]:
    """Convert detected patterns (above BASELINE) to candidates."""
    candidates: list[_NegativeCandidate] = []
    for pm in patterns:
        if not pm.detected or pm.severity == "BASELINE":
            continue
        total_impact = sum(pm.score_impact.values())
        severity_map = {
            "SEVERE": FlagSeverity.CRITICAL,
            "HIGH": FlagSeverity.HIGH,
            "ELEVATED": FlagSeverity.MODERATE,
        }
        candidates.append(
            _NegativeCandidate(
                evidence=(
                    f"Pattern: {pm.pattern_name} ({pm.severity})"
                ),
                section_origin=f"SECT7-{pm.pattern_id}",
                scoring_impact_label=(
                    f"Pattern modifier: +{total_impact:.0f} points"
                ),
                theory_mapping="",
                trajectory="NEW",
                severity=severity_map.get(
                    pm.severity, FlagSeverity.MODERATE,
                ),
                points_deducted=total_impact,
                max_points_possible=15.0,
            ),
        )
    return candidates


# -----------------------------------------------------------------------
# Deduplication
# -----------------------------------------------------------------------


# Normalized topic labels for dedup — maps common evidence prefixes to
# a canonical topic key so the same finding from different sources
# (red flags vs factor scores) only appears once.
_TOPIC_NORMALIZE: list[tuple[list[str], str]] = [
    (["stock volatility", "volatility"], "volatility"),
    (["prior litigation", "litigation history"], "prior_litigation"),
    (["wells notice", "sec enforcement"], "sec_enforcement"),
    (["doj investigation", "doj"], "doj"),
    (["guidance", "earnings guidance"], "guidance"),
    (["restatement", "audit"], "restatement"),
    (["governance", "board"], "governance"),
    (["distress", "going concern"], "distress"),
    (["short interest", "short"], "short_interest"),
    (["stock decline", "stock price"], "stock_decline"),
]


def _topic_key(candidate: _NegativeCandidate) -> str:
    """Extract a normalized topic key for deduplication."""
    evidence_lower = candidate.evidence.lower()
    for keywords, key in _TOPIC_NORMALIZE:
        for kw in keywords:
            if kw in evidence_lower:
                return key
    # Fallback: use first 30 chars of evidence
    return evidence_lower[:30]


def _deduplicate_candidates(
    candidates: list[_NegativeCandidate],
    exposure_map: dict[str, str],
) -> list[_NegativeCandidate]:
    """Remove duplicate candidates about the same topic.

    When multiple sources (red flags, factor scores, patterns) produce
    findings about the same issue, keep only the highest-ranked one.
    """
    seen: dict[str, _NegativeCandidate] = {}
    for c in candidates:
        key = _topic_key(c)
        if key not in seen:
            seen[key] = c
        else:
            # Keep the one with the higher ranking score
            existing = seen[key]
            if _rank_candidate(c, exposure_map) > _rank_candidate(
                existing, exposure_map
            ):
                seen[key] = c
    return list(seen.values())


# -----------------------------------------------------------------------
# Key negatives selection (SECT1-03)
# -----------------------------------------------------------------------


def select_key_negatives(
    red_flag_summary: RedFlagSummary | None,
    factor_scores: list[FactorScore],
    patterns_detected: list[PatternMatch],
    allegation_mapping: AllegationMapping | None,
) -> list[KeyFinding]:
    """Select top 5 key negatives using multi-signal ranking.

    Ranking formula:
    - Scoring impact: 40%
    - Recency: 20%
    - Trajectory: 20%
    - Claim correlation: 20%

    Sources:
    1. RedFlagSummary.items (FlaggedItem)
    2. Factor scores with high deductions (>=3 points)
    3. Detected patterns above BASELINE severity

    Returns sorted list of top 5 KeyFinding objects.
    """
    exposure_map = _build_exposure_map(allegation_mapping)

    # Collect candidates from all sources
    candidates: list[_NegativeCandidate] = []
    if red_flag_summary is not None:
        candidates.extend(_candidates_from_flags(red_flag_summary.items))
    candidates.extend(_candidates_from_factors(factor_scores))
    candidates.extend(_candidates_from_patterns(patterns_detected))

    if not candidates:
        return []

    # Guard: suppress audit/accounting findings when F3 is clean.
    # If F3 (audit/accounting factor) has points_deducted < 1.0,
    # the Beneish M-Score is clean (0/8 flags) and audit-related
    # findings should not surface as key negatives.
    f3_clean = False
    for fs in factor_scores:
        if fs.factor_id == "F3" and fs.points_deducted < 2.0:
            f3_clean = True
            break
    if f3_clean:
        _AUDIT_KEYWORDS = ("audit", "restatement", "beneish", "m-score")
        candidates = [
            c for c in candidates
            if not any(kw in c.evidence.lower() for kw in _AUDIT_KEYWORDS)
        ]

    if not candidates:
        return []

    # Deduplicate: when red flags and factor scores produce findings
    # about the same underlying issue (e.g., "Stock Volatility" from both
    # check evaluation and F7 scoring), keep only the highest-ranked one.
    deduped = _deduplicate_candidates(candidates, exposure_map)

    # Rank and select top N
    ranked = sorted(
        deduped,
        key=lambda c: _rank_candidate(c, exposure_map),
        reverse=True,
    )

    results: list[KeyFinding] = []
    for candidate in ranked[:_MAX_KEY_FINDINGS]:
        results.append(
            KeyFinding(
                evidence_narrative=candidate.evidence,
                section_origin=candidate.section_origin,
                scoring_impact=candidate.scoring_impact_label,
                theory_mapping=candidate.theory_mapping,
                ranking_score=_rank_candidate(candidate, exposure_map),
            ),
        )
    return results


# -----------------------------------------------------------------------
# Key positives selection (SECT1-04)
# -----------------------------------------------------------------------


def select_key_positives(
    state: AnalysisState,
    factor_scores: list[FactorScore],
) -> list[KeyFinding]:
    """Select top 5 key positives from positive indicator catalog.

    For each indicator, checks if condition is met using state data.
    If met, creates a KeyFinding with evidence, section, and theory.
    Sorted by scoring_relevance (how impactful for underwriting).
    Returns top 5.

    Args:
        state: Full analysis state for condition checks.
        factor_scores: Factor scores (unused in current implementation
            but available for future factor-based positive detection).

    Returns:
        List of top 5 positive KeyFinding objects.
    """
    indicators = build_positive_indicators()
    matched: list[tuple[float, str, str, str, str]] = []

    for indicator in indicators:
        if indicator.check_fn(state):
            matched.append((
                indicator.scoring_relevance,
                indicator.evidence_template,
                indicator.section_origin,
                indicator.condition,
                indicator.theory_mapping,
            ))

    # Sort by scoring relevance descending
    matched.sort(key=lambda pair: pair[0], reverse=True)

    results: list[KeyFinding] = []
    for relevance, evidence, section, condition, theory in (
        matched[:_MAX_KEY_FINDINGS]
    ):
        results.append(
            KeyFinding(
                evidence_narrative=evidence,
                section_origin=section,
                scoring_impact=f"Positive: {condition}",
                theory_mapping=theory,
                ranking_score=relevance,
            ),
        )
    return results


__all__ = ["select_key_negatives", "select_key_positives"]
