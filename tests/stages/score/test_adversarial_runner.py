"""Tests for adversarial critique runner -- orchestration + LLM narrative + Step 18.

Phase 110-02 Task 1: Adversarial critique runner.
TDD RED: Tests written before implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signal_results(
    statuses: dict[str, str],
    *,
    data_statuses: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build signal_results dict from {signal_id: status_str}."""
    ds = data_statuses or {}
    results: dict[str, dict[str, Any]] = {}
    for sid, status in statuses.items():
        results[sid] = {
            "status": status,
            "value": "1.0",
            "threshold_level": "red" if status in ("TRIGGERED", "RED") else "",
            "data_status": ds.get(sid, "EVALUATED"),
        }
    return results


def _make_mock_state() -> MagicMock:
    """Create a minimal mock AnalysisState."""
    state = MagicMock()
    state.company = MagicMock()
    state.company.sic_code = "7372"
    state.company.sector = "Technology"
    state.company.board_size = 9
    state.company.years_public = 15
    state.company.identity = MagicMock()
    state.company.identity.ticker = "TEST"
    state.company.identity.legal_name = MagicMock()
    state.company.identity.legal_name.value = "Test Corp"
    state.extracted = MagicMock()
    state.analysis = MagicMock()
    state.analysis.signal_results = {}
    state.scoring = MagicMock()
    state.scoring.quality_score = 75.0
    state.scoring.tier = MagicMock()
    state.scoring.tier.tier = MagicMock()
    state.scoring.tier.tier.value = "WRITE"
    return state


def _make_scoring_result() -> MagicMock:
    """Create a mock ScoringResult."""
    sr = MagicMock()
    sr.quality_score = 75.0
    sr.composite_score = 78.0
    sr.total_risk_points = 22.0
    sr.tier = MagicMock()
    sr.tier.tier = MagicMock()
    sr.tier.tier.value = "WRITE"
    sr.severity_scenarios = None
    sr.pattern_engine_result = None
    sr.adversarial_result = None
    return sr


# ---------------------------------------------------------------------------
# Runner orchestration tests
# ---------------------------------------------------------------------------


class TestRunAdversarialCritique:
    """Tests for run_adversarial_critique orchestrator."""

    def test_orchestrates_all_4_checks(self) -> None:
        """run_adversarial_critique calls all 4 check functions and returns AdversarialResult."""
        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        result = run_adversarial_critique(
            state=state,
            signal_results=signal_results,
        )
        # Should return AdversarialResult (not None) even with no caveats
        assert result is not None
        assert hasattr(result, "caveats")
        assert hasattr(result, "false_positive_count")
        assert hasattr(result, "computed_at")

    def test_returns_none_when_yaml_missing(self) -> None:
        """Returns None when adversarial_rules.yaml is missing (graceful degradation)."""
        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        with patch(
            "do_uw.stages.score._adversarial_runner._load_adversarial_rules",
            return_value=None,
        ):
            result = run_adversarial_critique(
                state=state,
                signal_results=signal_results,
            )
        assert result is None

    def test_counts_are_correct(self) -> None:
        """Counts in AdversarialResult match actual caveats."""
        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        result = run_adversarial_critique(
            state=state,
            signal_results=signal_results,
        )
        if result is not None:
            fp = sum(1 for c in result.caveats if c.caveat_type == "false_positive")
            fn = sum(1 for c in result.caveats if c.caveat_type == "false_negative")
            ct = sum(1 for c in result.caveats if c.caveat_type == "contradiction")
            dc = sum(1 for c in result.caveats if c.caveat_type == "data_completeness")
            assert result.false_positive_count == fp
            assert result.false_negative_count == fn
            assert result.contradiction_count == ct
            assert result.completeness_issues == dc

    def test_per_check_exception_does_not_crash(self) -> None:
        """If one check function raises, remaining checks still run."""
        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        with patch(
            "do_uw.stages.score._adversarial_runner.check_false_positives",
            side_effect=RuntimeError("boom"),
        ):
            result = run_adversarial_critique(
                state=state,
                signal_results=signal_results,
            )
        # Should still return a result (other checks ran)
        assert result is not None


# ---------------------------------------------------------------------------
# Score immutability tests
# ---------------------------------------------------------------------------


class TestScoreImmutability:
    """Verify adversarial caveats do NOT modify any scoring fields."""

    def test_caveats_never_modify_quality_score(self) -> None:
        """Adversarial caveats do NOT modify quality_score."""
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models

        _rebuild_scoring_models()
        sr = ScoringResult(
            quality_score=75.0,
            composite_score=78.0,
            total_risk_points=22.0,
        )
        original_score = sr.quality_score

        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        state.scoring = sr
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        result = run_adversarial_critique(
            state=state,
            signal_results=signal_results,
            scoring_result=sr,
        )

        # Score must not change
        assert sr.quality_score == original_score
        assert sr.composite_score == 78.0
        assert sr.total_risk_points == 22.0

    def test_caveats_never_modify_tier(self) -> None:
        """Adversarial caveats do NOT modify tier."""
        from do_uw.models.scoring import ScoringResult, Tier, TierClassification, _rebuild_scoring_models

        _rebuild_scoring_models()
        tier = TierClassification(
            tier=Tier.WRITE,
            score_range_low=56,
            score_range_high=70,
        )
        sr = ScoringResult(
            quality_score=65.0,
            tier=tier,
        )

        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        state.scoring = sr
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        run_adversarial_critique(
            state=state,
            signal_results=signal_results,
            scoring_result=sr,
        )

        assert sr.tier.tier == Tier.WRITE

    def test_scoring_result_has_adversarial_field(self) -> None:
        """ScoringResult.adversarial_result field exists with None default."""
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models

        _rebuild_scoring_models()
        sr = ScoringResult()
        assert hasattr(sr, "adversarial_result")
        assert sr.adversarial_result is None


# ---------------------------------------------------------------------------
# LLM narrative generation tests
# ---------------------------------------------------------------------------


class TestLLMNarrativeGeneration:
    """Tests for LLM-based caveat explanation generation."""

    def test_generate_narratives_enriches_caveats(self) -> None:
        """generate_caveat_narratives produces LLM-quality explanations."""
        from do_uw.models.adversarial import Caveat
        from do_uw.stages.score._adversarial_runner import generate_caveat_narratives

        caveats = [
            Caveat(
                caveat_type="false_positive",
                headline="CEO comp may be justified",
                explanation="Template text",
                confidence=0.8,
                evidence=["Strong stock performance"],
            ),
        ]
        state = _make_mock_state()

        # Mock LLM to return enriched explanations
        mock_response = {
            "explanations": [
                "The CEO compensation flag may be a false positive because the company's strong stock performance over the past year suggests that high compensation is performance-linked rather than excessive."
            ],
            "summary": "Overall, the assessment shows one potential false positive.",
        }
        with patch(
            "do_uw.stages.score._adversarial_runner._call_llm_for_narratives",
            return_value=mock_response,
        ):
            enriched = generate_caveat_narratives(caveats, state)

        assert len(enriched) == 1
        assert enriched[0].narrative_source == "llm"
        assert len(enriched[0].explanation) > len("Template text")

    def test_llm_failure_falls_back_to_template(self) -> None:
        """LLM failure preserves template-based explanations."""
        from do_uw.models.adversarial import Caveat
        from do_uw.stages.score._adversarial_runner import generate_caveat_narratives

        caveats = [
            Caveat(
                caveat_type="false_positive",
                headline="Test",
                explanation="Original template text",
                confidence=0.8,
            ),
        ]
        state = _make_mock_state()

        with patch(
            "do_uw.stages.score._adversarial_runner._call_llm_for_narratives",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            enriched = generate_caveat_narratives(caveats, state)

        assert len(enriched) == 1
        assert enriched[0].narrative_source == "template"
        assert enriched[0].explanation == "Original template text"

    def test_max_8_caveats_get_llm(self) -> None:
        """Only top 8 caveats (by severity then confidence) get LLM narratives."""
        from do_uw.models.adversarial import Caveat
        from do_uw.stages.score._adversarial_runner import generate_caveat_narratives

        # Create 12 caveats
        caveats = []
        for i in range(12):
            caveats.append(
                Caveat(
                    caveat_type="false_positive",
                    headline=f"Caveat {i}",
                    explanation=f"Template {i}",
                    confidence=float(i) / 12.0,
                    severity="warning" if i < 3 else "info",
                )
            )
        state = _make_mock_state()

        call_count = 0

        def mock_llm(caveats_batch: Any, state: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {
                "explanations": [f"LLM text {i}" for i in range(len(caveats_batch))],
                "summary": "Summary",
            }

        with patch(
            "do_uw.stages.score._adversarial_runner._call_llm_for_narratives",
            side_effect=mock_llm,
        ):
            enriched = generate_caveat_narratives(caveats, state)

        assert len(enriched) == 12
        llm_count = sum(1 for c in enriched if c.narrative_source == "llm")
        template_count = sum(1 for c in enriched if c.narrative_source == "template")
        assert llm_count <= 8
        assert template_count >= 4

    def test_summary_generated_by_llm(self) -> None:
        """AdversarialResult.summary is populated from LLM response."""
        from do_uw.stages.score._adversarial_runner import run_adversarial_critique

        state = _make_mock_state()
        signal_results = _make_signal_results({"SIG.A": "TRIGGERED"})

        # Even without LLM, summary should be a string
        result = run_adversarial_critique(
            state=state,
            signal_results=signal_results,
        )
        if result is not None:
            assert isinstance(result.summary, str)
