"""Governance quality scoring (7 dimensions, 0-10 each).

Computes a weighted governance quality score across independence,
CEO/chair duality, board refreshment, overboarding, committee structure,
say-on-pay support, and tenure distribution.
"""

from __future__ import annotations

from do_uw.models.common import Confidence
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
)
from do_uw.stages.extract.sourced import sourced_float


def _score_independence(profiles: list[BoardForensicProfile], t: dict[str, float]) -> float:
    ind = sum(1 for p in profiles if p.is_independent is not None and p.is_independent.value)
    total = len(profiles)
    if total == 0:
        return 0.0
    ratio = ind / total
    if ratio >= t.get("independence_high", 0.75):
        return 10.0
    return 7.0 if ratio >= t.get("independence_medium", 0.50) else 3.0


def _score_ceo_chair(profiles: list[BoardForensicProfile]) -> float:
    if not profiles:
        return 5.0
    has_ceo, has_chair = False, False
    for p in profiles:
        if p.name is None:
            continue
        nl = p.name.value.lower()
        if "ceo" in nl or "chief executive" in nl:
            has_ceo = True
        if ("chair" in nl or "chairman" in nl) and not has_ceo:
            has_chair = True
    if has_chair:
        return 10.0
    return 3.0 if has_ceo else 5.0


def _score_refreshment(profiles: list[BoardForensicProfile], t: dict[str, float]) -> float:
    threshold = t.get("refreshment_new_directors_3yr", 2)
    new = sum(1 for p in profiles if p.tenure_years is not None and p.tenure_years.value <= 3.0)
    if new >= threshold:
        return 10.0
    return 6.0 if new >= 1 else 2.0


def score_overboarding(profiles: list[BoardForensicProfile]) -> float:
    """Score board overboarding risk (public API, used in tests)."""
    overboarded = sum(1 for p in profiles if p.is_overboarded)
    ratio = overboarded / (len(profiles) or 1)
    if ratio == 0:
        return 10.0
    if ratio <= 0.1:
        return 7.0
    return 4.0 if ratio <= 0.25 else 2.0


def _score_committee_structure(profiles: list[BoardForensicProfile]) -> float:
    required = {"Audit", "Compensation", "Nominating/Governance"}
    covered: set[str] = set()
    for p in profiles:
        if p.is_independent is not None and p.is_independent.value:
            covered.update(p.committees)
    found = required & covered
    return 10.0 if len(found) == len(required) else round(len(found) / len(required) * 10.0, 1)


def _score_say_on_pay(comp: CompensationAnalysis | None, t: dict[str, float]) -> float:
    if comp is None or comp.say_on_pay_pct is None:
        return 5.0
    pct = comp.say_on_pay_pct.value
    if pct >= t.get("say_on_pay_strong", 90.0):
        return 10.0
    return 6.0 if pct >= t.get("say_on_pay_concern", 70.0) else 3.0


def _score_tenure(profiles: list[BoardForensicProfile], t: dict[str, float]) -> float:
    tenures = [p.tenure_years.value for p in profiles if p.tenure_years is not None]
    if not tenures:
        return 5.0
    avg = sum(tenures) / len(tenures)
    ideal_min = t.get("tenure_ideal_min", 5.0)
    ideal_max = t.get("tenure_ideal_max", 10.0)
    concern_max = t.get("tenure_concern_max", 15.0)
    if ideal_min <= avg <= ideal_max:
        return 10.0
    if avg < ideal_min:
        return max(3.0, 10.0 - (ideal_min - avg) * 2)
    if avg <= concern_max:
        return max(4.0, 10.0 - (avg - ideal_max) * 1.5)
    return 2.0


def compute_governance_score(
    profiles: list[BoardForensicProfile],
    compensation: CompensationAnalysis | None,
    weights: dict[str, float],
    thresholds: dict[str, float],
) -> GovernanceQualityScore:
    """Compute 7-dimension governance quality score (total 0-100)."""
    score = GovernanceQualityScore()
    if not profiles:
        return score

    score.independence_score = _score_independence(profiles, thresholds)
    score.ceo_chair_score = _score_ceo_chair(profiles)
    score.refreshment_score = _score_refreshment(profiles, thresholds)
    score.overboarding_score = score_overboarding(profiles)
    score.committee_score = _score_committee_structure(profiles)
    score.say_on_pay_score = _score_say_on_pay(compensation, thresholds)
    score.tenure_score = _score_tenure(profiles, thresholds)

    components = {
        "independence": score.independence_score,
        "ceo_chair": score.ceo_chair_score,
        "refreshment": score.refreshment_score,
        "overboarding": score.overboarding_score,
        "committee_structure": score.committee_score,
        "say_on_pay": score.say_on_pay_score,
        "tenure": score.tenure_score,
    }
    weighted = sum(components[k] * weights.get(k, 0.0) for k in components)
    total = round(weighted * 10.0, 1)
    score.total_score = sourced_float(
        total, "Computed from governance dimensions", Confidence.LOW,
    )
    return score
