"""Tests for enhanced frequency model: classification x hazard x signal.

Covers clean companies, CRF-elevated, pattern-elevated, factor-elevated,
combined signals, signal cap, probability cap, and tier-based fallback.
"""

from __future__ import annotations

import pytest

from do_uw.models.scoring import FactorScore, PatternMatch, RedFlagResult
from do_uw.stages.score.frequency_model import compute_enhanced_frequency

# ---------------------------------------------------------------------------
# Fixtures -- minimal state builders
# ---------------------------------------------------------------------------


def _make_state(
    *,
    base_filing_rate_pct: float | None = None,
    ies_multiplier: float | None = None,
    claim_prob_high: float | None = None,
) -> object:
    """Build a minimal mock AnalysisState with classification + hazard."""

    class _MockClassification:
        def __init__(self, rate: float) -> None:
            self.base_filing_rate_pct = rate

    class _MockHazardProfile:
        def __init__(self, mult: float) -> None:
            self.ies_multiplier = mult

    class _MockClaimProb:
        def __init__(self, high: float) -> None:
            self.range_high_pct = high

    class _MockScoring:
        def __init__(self, prob: _MockClaimProb) -> None:
            self.claim_probability = prob

    class _MockState:
        def __init__(self) -> None:
            self.classification = None
            self.hazard_profile = None
            self.scoring = None
            self.analysis = None

    state = _MockState()
    if base_filing_rate_pct is not None:
        state.classification = _MockClassification(base_filing_rate_pct)
    if ies_multiplier is not None:
        state.hazard_profile = _MockHazardProfile(ies_multiplier)
    if claim_prob_high is not None:
        state.scoring = _MockScoring(_MockClaimProb(claim_prob_high))
    return state


def _make_red_flags(triggered_count: int, total: int = 5) -> list[RedFlagResult]:
    """Create red flag results with N triggered out of total."""
    results: list[RedFlagResult] = []
    for i in range(total):
        results.append(
            RedFlagResult(
                flag_id=f"CRF-{i + 1:02d}",
                flag_name=f"Test flag {i + 1}",
                triggered=i < triggered_count,
            )
        )
    return results


def _make_patterns(detected_count: int, total: int = 5) -> list[PatternMatch]:
    """Create pattern matches with N detected out of total."""
    results: list[PatternMatch] = []
    for i in range(total):
        results.append(
            PatternMatch(
                pattern_id=f"PATTERN.TEST.P{i + 1}",
                pattern_name=f"Test pattern {i + 1}",
                detected=i < detected_count,
            )
        )
    return results


def _make_factors(
    elevated_count: int, total: int = 10, max_pts: int = 10
) -> list[FactorScore]:
    """Create factor scores with N elevated (>50% deducted) out of total."""
    results: list[FactorScore] = []
    for i in range(total):
        deducted = float(max_pts * 0.8) if i < elevated_count else 0.0
        results.append(
            FactorScore(
                factor_id=f"F{i + 1}",
                factor_name=f"Factor {i + 1}",
                max_points=max_pts,
                points_deducted=deducted,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnhancedFrequencyClean:
    """Clean company: classification + hazard, no signals."""

    def test_base_times_hazard_no_signals(self) -> None:
        state = _make_state(base_filing_rate_pct=5.0, ies_multiplier=1.2)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.methodology == "classification x hazard x signal"
        assert result.base_rate_pct == 5.0
        assert result.hazard_multiplier == 1.2
        assert result.signal_multiplier == 1.0
        # 5.0 * 1.2 * 1.0 = 6.0
        assert result.adjusted_probability_pct == 6.0

    def test_zero_signals_all_components_unity(self) -> None:
        """0 CRF / 0 patterns / 0 elevated = signal_mult 1.0."""
        state = _make_state(base_filing_rate_pct=3.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.crf_signal == 1.0
        assert result.pattern_signal == 1.0
        assert result.factor_signal == 1.0
        assert result.signal_multiplier == 1.0
        assert result.adjusted_probability_pct == 3.0


class TestCRFSignal:
    """CRF triggers elevating signal."""

    def test_one_trigger(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(1),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.crf_signal == 1.15
        # 4.0 * 1.0 * 1.15 = 4.6
        assert result.adjusted_probability_pct == 4.6

    def test_two_triggers(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(2),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.crf_signal == 1.30

    def test_three_plus_triggers(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(4),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.crf_signal == 1.50


class TestPatternSignal:
    """Pattern detection elevating signal."""

    def test_one_pattern(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(1),
            _make_factors(0),
        )
        assert result.pattern_signal == 1.10

    def test_two_patterns(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(2),
            _make_factors(0),
        )
        assert result.pattern_signal == 1.10

    def test_three_patterns(self) -> None:
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(3),
            _make_factors(0),
        )
        assert result.pattern_signal == 1.25


class TestFactorSignal:
    """Elevated factors elevating signal."""

    def test_majority_elevated(self) -> None:
        """6/10 factors elevated (60%) -> 1.15x."""
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(6, total=10),
        )
        assert result.factor_signal == 1.15

    def test_supermajority_elevated(self) -> None:
        """8/10 factors elevated (80%) -> 1.30x."""
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(8, total=10),
        )
        assert result.factor_signal == 1.30

    def test_no_elevated(self) -> None:
        """0/10 factors elevated -> 1.0x."""
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0, total=10),
        )
        assert result.factor_signal == 1.0


class TestSignalCap:
    """Combined signals capped at 2.0x."""

    def test_combined_capped_at_two(self) -> None:
        """3+ CRF (1.50) * 3+ patterns (1.25) * 80% factors (1.30) = 2.4375 -> 2.0."""
        state = _make_state(base_filing_rate_pct=4.0, ies_multiplier=1.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(4),
            _make_patterns(4),
            _make_factors(8, total=10),
        )
        assert result.signal_multiplier == 2.0
        # 4.0 * 1.0 * 2.0 = 8.0
        assert result.adjusted_probability_pct == 8.0


class TestProbabilityCap:
    """Final probability capped at 50%."""

    def test_high_base_rate_capped(self) -> None:
        """Very high base + multipliers -> cap at 50%."""
        state = _make_state(base_filing_rate_pct=20.0, ies_multiplier=2.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(4),  # 1.50x
            _make_patterns(0),
            _make_factors(0),
        )
        # 20.0 * 2.0 * 1.50 = 60.0 -> capped at 50.0
        assert result.adjusted_probability_pct == 50.0


class TestFallback:
    """Fallback when classification is None."""

    def test_no_classification_uses_claim_prob(self) -> None:
        """No classification -> falls back to claim_prob.range_high_pct."""
        state = _make_state(claim_prob_high=8.5, ies_multiplier=1.1)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.methodology == "tier-based fallback"
        assert result.base_rate_pct == 8.5
        # 8.5 * 1.1 * 1.0 = 9.35
        assert result.adjusted_probability_pct == 9.35

    def test_no_classification_no_scoring_uses_default(self) -> None:
        """No classification, no scoring -> 4.0% default."""
        state = _make_state()
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.methodology == "tier-based fallback"
        assert result.base_rate_pct == 4.0
        assert result.adjusted_probability_pct == 4.0

    def test_no_hazard_profile_defaults_to_one(self) -> None:
        """No hazard profile -> hazard_multiplier = 1.0."""
        state = _make_state(base_filing_rate_pct=6.0)
        result = compute_enhanced_frequency(
            state,  # type: ignore[arg-type]
            _make_red_flags(0),
            _make_patterns(0),
            _make_factors(0),
        )
        assert result.hazard_multiplier == 1.0
        assert result.adjusted_probability_pct == 6.0
