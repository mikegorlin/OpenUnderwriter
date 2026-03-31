"""Peer group scoring functions -- signal computation and composite score.

Split from peer_group.py to keep files under 500 lines per CLAUDE.md.
Contains the 5 peer scoring signals (SIC, industry, market cap, revenue,
description overlap) and the composite weighted score computation.
"""

from __future__ import annotations

# Composite scoring weights (must sum to 1.0).
WEIGHT_SIC: float = 0.25
WEIGHT_INDUSTRY: float = 0.20
WEIGHT_MARKET_CAP: float = 0.25
WEIGHT_REVENUE: float = 0.15
WEIGHT_DESCRIPTION: float = 0.15


# ---------------------------------------------------------------------------
# Signal scoring functions (0-100 each)
# ---------------------------------------------------------------------------


def score_sic_match(target_sic: str, candidate_sic: str) -> float:
    """Score SIC code similarity: 4-digit=100, 3-digit=75, 2-digit=50."""
    if not target_sic or not candidate_sic:
        return 0.0
    t = target_sic.ljust(4, "0")
    c = candidate_sic.ljust(4, "0")
    if t == c:
        return 100.0
    if t[:3] == c[:3]:
        return 75.0
    if t[:2] == c[:2]:
        return 50.0
    return 0.0


def score_industry_match(
    target_industry: str,
    target_sector: str,
    candidate_industry: str,
    candidate_sector: str,
) -> float:
    """Score industry match: exact=100, sector=50, no match=0."""
    if target_industry and candidate_industry:
        if target_industry.lower() == candidate_industry.lower():
            return 100.0
    if target_sector and candidate_sector:
        if target_sector.lower() == candidate_sector.lower():
            return 50.0
    return 0.0


def score_market_cap_proximity(
    target_mcap: float, candidate_mcap: float,
) -> float:
    """Score market cap proximity: identical=100, band edge=0."""
    if target_mcap <= 0 or candidate_mcap <= 0:
        return 0.0
    ratio = candidate_mcap / target_mcap
    if ratio < 0.5 or ratio > 2.0:
        return 0.0
    # Linear scale: 1.0x = 100, 0.5x/2.0x = 0.
    if ratio <= 1.0:
        return (ratio - 0.5) / 0.5 * 100.0
    return (2.0 - ratio) / 1.0 * 100.0


def score_revenue_similarity(
    target_rev: float, candidate_rev: float,
) -> float:
    """Score revenue similarity: identical=100, 10x difference=10."""
    if target_rev <= 0 or candidate_rev <= 0:
        return 0.0
    ratio = min(target_rev, candidate_rev) / max(target_rev, candidate_rev)
    return round(ratio * 100.0, 1)


def score_description_overlap(
    target_desc: str, candidate_desc: str,
) -> float:
    """Score business description overlap using Jaccard similarity."""
    if not target_desc or not candidate_desc:
        return 0.0

    # Extract keywords (simple tokenization, filter short words).
    stop_words = {
        "the", "and", "or", "is", "in", "of", "to", "a", "an",
        "for", "on", "with", "as", "at", "by", "from", "its",
        "that", "this", "are", "was", "were", "be", "has", "have",
        "had", "been", "our", "we", "which", "their", "it",
    }

    def _tokenize(text: str) -> set[str]:
        words = set(text.lower().split())
        return {w for w in words if len(w) > 3 and w not in stop_words}

    target_tokens = _tokenize(target_desc)
    candidate_tokens = _tokenize(candidate_desc)

    if not target_tokens or not candidate_tokens:
        return 0.0

    intersection = len(target_tokens & candidate_tokens)
    union = len(target_tokens | candidate_tokens)
    if union == 0:
        return 0.0

    return round(intersection / union * 100.0, 1)


def compute_composite_score(
    sic: float,
    industry: float,
    mcap: float,
    revenue: float,
    description: float,
) -> float:
    """Compute weighted composite peer score."""
    return round(
        sic * WEIGHT_SIC
        + industry * WEIGHT_INDUSTRY
        + mcap * WEIGHT_MARKET_CAP
        + revenue * WEIGHT_REVENUE
        + description * WEIGHT_DESCRIPTION,
        2,
    )
