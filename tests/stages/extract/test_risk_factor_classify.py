"""Tests for risk factor classification (STANDARD/NOVEL/ELEVATED).

Tests the deterministic classification logic without LLM calls.
"""

from __future__ import annotations

import pytest

from do_uw.models.state import RiskFactorProfile


def _make_factor(
    title: str = "Test factor",
    category: str = "OTHER",
    severity: str = "MEDIUM",
    is_new: bool = False,
) -> RiskFactorProfile:
    return RiskFactorProfile(
        title=title,
        category=category,
        severity=severity,
        is_new_this_year=is_new,
    )


def test_novel_classification_for_new_factors() -> None:
    """Factors with is_new_this_year=True get NOVEL."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    factors = [_make_factor("New AI risk factor", category="AI", is_new=True)]
    result = classify_risk_factors(factors)
    assert result[0].classification == "NOVEL"


def test_elevated_classification_for_escalated_high_severity() -> None:
    """HIGH severity factor with escalation from prior year gets ELEVATED."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    current = [_make_factor("Litigation risk", category="LITIGATION", severity="HIGH")]
    prior = [_make_factor("Litigation risk", category="LITIGATION", severity="MEDIUM")]
    result = classify_risk_factors(current, prior)
    assert result[0].classification == "ELEVATED"


def test_standard_classification_for_unchanged() -> None:
    """Medium severity unchanged factor gets STANDARD."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    current = [_make_factor("Market risk", severity="MEDIUM")]
    prior = [_make_factor("Market risk", severity="MEDIUM")]
    result = classify_risk_factors(current, prior)
    assert result[0].classification == "STANDARD"


def test_elevated_requires_high_severity() -> None:
    """Escalated but not HIGH severity stays STANDARD."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    current = [_make_factor("Market risk", severity="MEDIUM")]
    prior = [_make_factor("Market risk", severity="LOW")]
    result = classify_risk_factors(current, prior)
    assert result[0].classification == "STANDARD"


def test_high_severity_no_prior_match_gets_elevated() -> None:
    """HIGH severity with no matching prior factor gets ELEVATED."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    current = [_make_factor("Critical regulatory risk", severity="HIGH")]
    prior = [_make_factor("Unrelated factor", severity="LOW")]
    result = classify_risk_factors(current, prior)
    assert result[0].classification == "ELEVATED"


def test_no_prior_factors_still_works() -> None:
    """Classification works without prior factors."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    factors = [
        _make_factor("Standard risk", severity="MEDIUM"),
        _make_factor("New risk", is_new=True),
        _make_factor("High risk", severity="HIGH"),
    ]
    result = classify_risk_factors(factors)
    assert result[0].classification == "STANDARD"
    assert result[1].classification == "NOVEL"
    assert result[2].classification == "ELEVATED"


def test_do_implication_populated() -> None:
    """do_implication is set based on category."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    factors = [
        _make_factor("Litigation risk", category="LITIGATION"),
        _make_factor("Cyber risk", category="CYBER"),
        _make_factor("Regulatory risk", category="REGULATORY"),
    ]
    result = classify_risk_factors(factors)
    for r in result:
        assert r.do_implication != "", f"Empty do_implication for {r.category}"


def test_fuzzy_title_matching() -> None:
    """Slightly different titles still match (SequenceMatcher > 0.6)."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    current = [_make_factor("Risks related to our litigation exposure", severity="HIGH")]
    prior = [_make_factor("Risks related to litigation exposure", severity="LOW")]
    result = classify_risk_factors(current, prior)
    # Titles are similar enough to match, severity escalated -> ELEVATED
    assert result[0].classification == "ELEVATED"


def test_returns_same_length_list() -> None:
    """Output list has same length as input."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    factors = [_make_factor(f"Factor {i}") for i in range(5)]
    result = classify_risk_factors(factors)
    assert len(result) == 5


def test_novel_takes_precedence_over_elevated() -> None:
    """is_new_this_year=True always gets NOVEL even if HIGH severity."""
    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    factors = [_make_factor("New critical risk", severity="HIGH", is_new=True)]
    result = classify_risk_factors(factors)
    assert result[0].classification == "NOVEL"
