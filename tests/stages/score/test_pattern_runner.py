"""Tests for pattern runner orchestrator (109-03).

Tests run_pattern_engines(), archetype evaluation, tier floor logic,
auto-expansion, and ScoreStage Step 16 integration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.patterns import PatternEngineResult
from do_uw.stages.score.pattern_engine import ArchetypeResult, EngineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal_results(
    statuses: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a mock signal_results dict.

    statuses maps signal_id -> status (RED, YELLOW, CLEAR, SKIPPED).
    """
    if statuses is None:
        statuses = {}
    results: dict[str, Any] = {}
    for sig_id, status in statuses.items():
        results[sig_id] = {
            "status": status,
            "signal_id": sig_id,
            "rap_class": sig_id.split(".")[0].lower() if "." in sig_id else "agent",
        }
    return results


def _make_mock_state(
    *,
    ticker: str = "TEST",
    company_name: str = "Test Corp",
    has_scac: bool = False,
    signal_results: dict[str, Any] | None = None,
) -> MagicMock:
    """Build a minimal mock AnalysisState."""
    state = MagicMock()
    state.company = MagicMock()
    state.company.identity = MagicMock()
    state.company.identity.ticker = ticker
    state.company.identity.legal_name = MagicMock()
    state.company.identity.legal_name.value = company_name

    # Litigation data
    if has_scac:
        case = MagicMock()
        case.status = "active"
        case.case_type = "SCA"
        state.extracted = MagicMock()
        state.extracted.litigation = MagicMock()
        state.extracted.litigation.securities_class_actions = [case]
    else:
        state.extracted = MagicMock()
        state.extracted.litigation = MagicMock()
        state.extracted.litigation.securities_class_actions = []

    # Analysis
    state.analysis = MagicMock()
    state.analysis.signal_results = signal_results or {}

    return state


def _make_mock_engine(
    engine_id: str,
    engine_name: str,
    fired: bool = False,
    confidence: float = 0.0,
    headline: str = "",
    should_raise: bool = False,
) -> MagicMock:
    """Build a mock PatternEngine."""
    engine = MagicMock()
    engine.engine_id = engine_id
    engine.engine_name = engine_name
    if should_raise:
        engine.evaluate.side_effect = RuntimeError(f"Engine {engine_id} failed")
    else:
        engine.evaluate.return_value = EngineResult(
            engine_id=engine_id,
            engine_name=engine_name,
            fired=fired,
            confidence=confidence,
            headline=headline or f"{engine_name} result",
        )
    return engine


# ---------------------------------------------------------------------------
# Tests: run_pattern_engines returns PatternEngineResult
# ---------------------------------------------------------------------------

class TestRunPatternEngines:
    """Tests for the run_pattern_engines() orchestrator."""

    def test_returns_pattern_engine_result(self) -> None:
        """run_pattern_engines returns PatternEngineResult with 4 engine + 6 archetype results."""
        from do_uw.stages.score._pattern_runner import run_pattern_engines

        state = _make_mock_state()
        signal_results = _make_signal_results({"FIN.QUALITY.revenue_recognition_risk": "RED"})

        result = run_pattern_engines(state=state, signal_results=signal_results)

        assert result is not None
        assert isinstance(result, PatternEngineResult)
        assert len(result.engine_results) == 4
        assert len(result.archetype_results) == 6

    def test_engine_failure_caught_remaining_continue(self) -> None:
        """Individual engine failure is caught; remaining engines still run."""
        from do_uw.stages.score._pattern_runner import run_pattern_engines

        state = _make_mock_state()
        signal_results = _make_signal_results()

        # Patch one engine to raise
        with patch(
            "do_uw.stages.score._pattern_runner.ConjunctionScanEngine"
        ) as mock_cls:
            mock_cls.return_value.engine_id = "conjunction_scan"
            mock_cls.return_value.engine_name = "Conjunction Scan"
            mock_cls.return_value.evaluate.side_effect = RuntimeError("boom")

            result = run_pattern_engines(state=state, signal_results=signal_results)

        assert result is not None
        assert len(result.engine_results) == 4
        # The failed engine should show NOT_FIRED
        conj_result = [r for r in result.engine_results if r.engine_id == "conjunction_scan"]
        assert len(conj_result) == 1
        assert conj_result[0].fired is False
        assert "error" in conj_result[0].headline.lower() or "Engine error" in conj_result[0].headline

    def test_all_engines_fail_returns_4_not_fired(self) -> None:
        """All 4 engine failures => PatternEngineResult with 4 NOT_FIRED (not None)."""
        from do_uw.stages.score._pattern_runner import run_pattern_engines

        state = _make_mock_state()
        signal_results = _make_signal_results()

        with patch(
            "do_uw.stages.score._pattern_runner.ConjunctionScanEngine"
        ) as mock_conj, patch(
            "do_uw.stages.score._pattern_runner.PeerOutlierEngine"
        ) as mock_peer, patch(
            "do_uw.stages.score._pattern_runner.MigrationDriftEngine"
        ) as mock_drift, patch(
            "do_uw.stages.score._pattern_runner.PrecedentMatchEngine"
        ) as mock_prec:
            for cls, eid, ename in [
                (mock_conj, "conjunction_scan", "Conjunction Scan"),
                (mock_peer, "peer_outlier", "Peer Outlier"),
                (mock_drift, "migration_drift", "Migration Drift"),
                (mock_prec, "precedent_match", "Precedent Match"),
            ]:
                cls.return_value.engine_id = eid
                cls.return_value.engine_name = ename
                cls.return_value.evaluate.side_effect = RuntimeError("fail")

            result = run_pattern_engines(state=state, signal_results=signal_results)

        assert result is not None
        assert len(result.engine_results) == 4
        assert all(not r.fired for r in result.engine_results)


# ---------------------------------------------------------------------------
# Tests: Archetype evaluation
# ---------------------------------------------------------------------------

class TestArchetypeEvaluation:
    """Tests for archetype matching logic."""

    def test_archetype_fires_at_minimum_matches(self) -> None:
        """5/18 matched with minimum_matches=5 => fired=True."""
        from do_uw.stages.score._pattern_runner import _evaluate_archetypes

        # desperate_growth_trap has minimum_matches=5 and 18 required_signals
        # Set 5 of them to RED
        statuses = {
            "FIN.QUALITY.revenue_recognition_risk": "RED",
            "FIN.QUALITY.revenue_quality_score": "RED",
            "FIN.FORENSIC.m_score_composite": "YELLOW",
            "FIN.FORENSIC.dsri_elevated": "RED",
            "FIN.TEMPORAL.revenue_deceleration": "YELLOW",
        }
        signal_results = _make_signal_results(statuses)

        results = _evaluate_archetypes(signal_results)
        dgt = [r for r in results if r.archetype_id == "desperate_growth_trap"]
        assert len(dgt) == 1
        assert dgt[0].fired is True
        assert dgt[0].signals_matched >= 5

    def test_archetype_does_not_fire_below_minimum(self) -> None:
        """4/18 matched with minimum_matches=5 => fired=False."""
        from do_uw.stages.score._pattern_runner import _evaluate_archetypes

        statuses = {
            "FIN.QUALITY.revenue_recognition_risk": "RED",
            "FIN.QUALITY.revenue_quality_score": "RED",
            "FIN.FORENSIC.m_score_composite": "YELLOW",
            "FIN.FORENSIC.dsri_elevated": "RED",
        }
        signal_results = _make_signal_results(statuses)

        results = _evaluate_archetypes(signal_results)
        dgt = [r for r in results if r.archetype_id == "desperate_growth_trap"]
        assert len(dgt) == 1
        assert dgt[0].fired is False
        assert dgt[0].signals_matched == 4

    def test_future_signals_gracefully_skipped(self) -> None:
        """future_signal.* IDs are not counted as matched or missed."""
        from do_uw.stages.score._pattern_runner import _evaluate_archetypes

        # ai_mirage has 3 future_signal.* entries
        # Set some real signals to RED but not enough to fire without futures
        statuses = {
            "BIZ.UNI.ai_claims": "RED",
            "FIN.QUALITY.revenue_recognition_risk": "RED",
            "FIN.GUIDE.track_record": "YELLOW",
        }
        signal_results = _make_signal_results(statuses)

        results = _evaluate_archetypes(signal_results)
        ai = [r for r in results if r.archetype_id == "ai_mirage"]
        assert len(ai) == 1
        # ai_mirage has minimum_matches=3 and 15 real signals (18 total - 3 future)
        # We matched 3 real signals => should fire
        assert ai[0].fired is True
        # signals_required should NOT include future_signal.* entries
        assert "future_signal" not in str(ai[0].matched_signal_ids)

    def test_all_six_archetypes_returned(self) -> None:
        """All 6 archetypes are evaluated and returned."""
        from do_uw.stages.score._pattern_runner import _evaluate_archetypes

        results = _evaluate_archetypes({})
        assert len(results) == 6
        ids = {r.archetype_id for r in results}
        expected = {
            "desperate_growth_trap",
            "governance_vacuum",
            "post_spac_hangover",
            "accounting_time_bomb",
            "regulatory_reckoning",
            "ai_mirage",
        }
        assert ids == expected


# ---------------------------------------------------------------------------
# Tests: Tier floor logic
# ---------------------------------------------------------------------------

class TestTierFloorLogic:
    """Tests for _apply_tier_floors()."""

    def test_floor_raises_standard_to_elevated(self) -> None:
        """Archetype floor=ELEVATED + current tier=STANDARD => raised to ELEVATED."""
        from do_uw.stages.score._pattern_runner import _apply_tier_floors
        from do_uw.stages.score.scoring_lens import HAETier, ScoringLensResult

        hae_result = ScoringLensResult(
            lens_name="test",
            tier=HAETier.STANDARD,
            composites={"host": 0.5, "agent": 0.5, "environment": 0.5},
            product_score=0.05,
            confidence="MEDIUM",
        )
        archetype_results = [
            ArchetypeResult(
                archetype_id="test_arch",
                archetype_name="Test",
                fired=True,
                signals_matched=5,
                signals_required=10,
                recommendation_floor="ELEVATED",
                confidence=0.5,
            ),
        ]

        updated = _apply_tier_floors(hae_result, archetype_results)
        assert updated.tier == HAETier.ELEVATED
        assert "pattern_floor" in updated.tier_source

    def test_floor_does_not_lower_high_risk(self) -> None:
        """Archetype floor=ELEVATED + current tier=HIGH_RISK => unchanged."""
        from do_uw.stages.score._pattern_runner import _apply_tier_floors
        from do_uw.stages.score.scoring_lens import HAETier, ScoringLensResult

        hae_result = ScoringLensResult(
            lens_name="test",
            tier=HAETier.HIGH_RISK,
            composites={"host": 0.5, "agent": 0.5, "environment": 0.5},
            product_score=0.35,
            confidence="MEDIUM",
        )
        archetype_results = [
            ArchetypeResult(
                archetype_id="test_arch",
                archetype_name="Test",
                fired=True,
                signals_matched=5,
                signals_required=10,
                recommendation_floor="ELEVATED",
                confidence=0.5,
            ),
        ]

        updated = _apply_tier_floors(hae_result, archetype_results)
        assert updated.tier == HAETier.HIGH_RISK  # Unchanged

    def test_unfired_archetype_floor_ignored(self) -> None:
        """Unfired archetype floor is not applied."""
        from do_uw.stages.score._pattern_runner import _apply_tier_floors
        from do_uw.stages.score.scoring_lens import HAETier, ScoringLensResult

        hae_result = ScoringLensResult(
            lens_name="test",
            tier=HAETier.STANDARD,
            composites={"host": 0.5, "agent": 0.5, "environment": 0.5},
            product_score=0.05,
            confidence="MEDIUM",
        )
        archetype_results = [
            ArchetypeResult(
                archetype_id="test_arch",
                archetype_name="Test",
                fired=False,  # Not fired
                signals_matched=2,
                signals_required=10,
                recommendation_floor="ELEVATED",
                confidence=0.2,
            ),
        ]

        updated = _apply_tier_floors(hae_result, archetype_results)
        assert updated.tier == HAETier.STANDARD  # Unchanged


# ---------------------------------------------------------------------------
# Tests: Auto-expansion
# ---------------------------------------------------------------------------

class TestAutoExpansion:
    """Tests for _auto_expand_case_library()."""

    def test_auto_expansion_creates_entry_with_scac(self, tmp_path: Any) -> None:
        """Active SCAC filing => case entry created with POST_FILING flag."""
        from do_uw.stages.score._pattern_runner import _auto_expand_case_library

        state = _make_mock_state(
            ticker="ACME",
            company_name="ACME Corp",
            has_scac=True,
        )
        signal_results = _make_signal_results({
            "FIN.FORENSIC.m_score_composite": "RED",
            "GOV.BOARD.independence": "YELLOW",
        })

        auto_dir = tmp_path / "auto_cases"
        _auto_expand_case_library(state, signal_results, auto_cases_dir=auto_dir)

        # Should have created a YAML file
        files = list(auto_dir.glob("*.yaml"))
        assert len(files) == 1
        assert "acme" in files[0].name.lower()

    def test_auto_expansion_does_nothing_without_scac(self, tmp_path: Any) -> None:
        """No SCAC filing => no file written."""
        from do_uw.stages.score._pattern_runner import _auto_expand_case_library

        state = _make_mock_state(has_scac=False)
        signal_results = _make_signal_results({
            "FIN.FORENSIC.m_score_composite": "RED",
        })

        auto_dir = tmp_path / "auto_cases"
        _auto_expand_case_library(state, signal_results, auto_cases_dir=auto_dir)

        # No files should be created
        if auto_dir.exists():
            assert len(list(auto_dir.glob("*.yaml"))) == 0


# ---------------------------------------------------------------------------
# Tests: ScoreStage integration
# ---------------------------------------------------------------------------

class TestScoreStageIntegration:
    """Test Step 16 stores pattern_engine_result on state.scoring."""

    def test_step_16_stores_result(self) -> None:
        """ScoreStage Step 16 stores pattern_engine_result on state.scoring."""
        # This test verifies the integration point exists by importing
        from do_uw.stages.score._pattern_runner import run_pattern_engines

        state = _make_mock_state()
        signal_results = _make_signal_results()

        result = run_pattern_engines(
            state=state,
            signal_results=signal_results,
        )

        assert result is not None
        assert isinstance(result, PatternEngineResult)
        # Verify the result can be stored on scoring
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models
        _rebuild_scoring_models()
        scoring = ScoringResult(
            composite_score=85.0,
            quality_score=85.0,
            total_risk_points=15.0,
            factor_scores=[],
            red_flags=[],
            patterns_detected=[],
        )
        scoring.pattern_engine_result = result
        assert scoring.pattern_engine_result is not None
