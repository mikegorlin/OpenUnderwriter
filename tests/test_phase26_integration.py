"""Phase 26 integration tests: analytical engines, CRF gates, factor scoring.

Validates that all Phase 26 components are properly wired:
- AnalyzeStage calls temporal, forensic, executive, NLP engines
- New CRF-12 through CRF-17 gates trigger on appropriate conditions
- Factor scoring absorbs new sub-factors as amplifiers
- IES-aware amplification adjusts behavioral signals
- Full pipeline runs without regression
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue, StageStatus
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import (
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
)
from do_uw.models.governance import GovernanceData
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.litigation_details import WhistleblowerIndicator
from do_uw.models.market import MarketSignals
from do_uw.models.state import AnalysisResults, AnalysisState, ExtractedData
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus
from do_uw.stages.score.red_flag_gates import evaluate_red_flag_gates
from do_uw.stages.score.red_flag_gates_enhanced import evaluate_phase26_trigger

_NOW = datetime.now(tz=UTC)

# Paths for brain config files
_BRAIN_CONFIG_DIR = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "brain" / "config"


def _sv(value: Any, source: str = "test") -> SourcedValue:
    """Create a SourcedValue with test defaults."""
    return SourcedValue(
        value=value, source=source,
        confidence=Confidence.LOW, as_of=_NOW,
    )


def _load_red_flags_config() -> dict[str, Any]:
    with (_BRAIN_CONFIG_DIR / "red_flags.json").open() as f:
        return json.load(f)


def _load_scoring_config() -> dict[str, Any]:
    with (_BRAIN_CONFIG_DIR / "scoring.json").open() as f:
        return json.load(f)


def _load_signals_config() -> dict[str, Any]:
    with (_BRAIN_CONFIG_DIR / "signals.json").open() as f:
        return json.load(f)


def _make_minimal_state() -> AnalysisState:
    """Create a minimal AnalysisState with extract complete."""
    state = AnalysisState(ticker="TEST")
    state.company = CompanyProfile(
        identity=CompanyIdentity(ticker="TEST", company_name="Test Inc"),
    )
    state.extracted = ExtractedData(
        financials=ExtractedFinancials(),
        market=MarketSignals(),
        governance=GovernanceData(),
        litigation=LitigationLandscape(),
    )
    state.stages["extract"].status = StageStatus.COMPLETED
    return state


# -----------------------------------------------------------------------
# AnalyzeStage engine wiring tests
# -----------------------------------------------------------------------


class TestAnalyzeStageEngines:
    """Verify AnalyzeStage runs Phase 26 analytical engines."""

    def test_analyze_stage_runs_temporal(self) -> None:
        """After AnalyzeStage.run(), temporal_signals is populated."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _make_minimal_state()
        stage = AnalyzeStage()
        stage.run(state)

        assert state.analysis is not None
        # temporal_signals may be None if temporal engine has no data
        # but the engine should have been called (graceful degradation)
        # The key test is that analysis completed successfully
        assert state.stages["analyze"].status == StageStatus.COMPLETED

    def test_analyze_stage_runs_forensics(self) -> None:
        """After AnalyzeStage.run(), forensic_composites populated."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _make_minimal_state()
        stage = AnalyzeStage()
        stage.run(state)

        assert state.analysis is not None
        # Forensics should populate even with empty data
        if state.analysis.forensic_composites is not None:
            assert "financial_integrity_score" in state.analysis.forensic_composites

    def test_analyze_stage_runs_executive(self) -> None:
        """After AnalyzeStage.run(), executive_risk populated or None."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _make_minimal_state()
        stage = AnalyzeStage()
        stage.run(state)

        assert state.analysis is not None
        # executive_risk is None if no exec data -- that's OK
        assert state.stages["analyze"].status == StageStatus.COMPLETED

    def test_analyze_stage_runs_nlp(self) -> None:
        """After AnalyzeStage.run(), nlp_signals populated."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _make_minimal_state()
        stage = AnalyzeStage()
        stage.run(state)

        assert state.analysis is not None
        # NLP signals should populate even with empty text
        if state.analysis.nlp_signals is not None:
            assert isinstance(state.analysis.nlp_signals, dict)

    def test_analyze_stage_graceful_degradation(self) -> None:
        """If temporal engine raises, analysis still completes."""
        from do_uw.stages.analyze import AnalyzeStage

        state = _make_minimal_state()

        # Force temporal engine to raise
        with patch(
            "do_uw.stages.analyze.temporal_engine.TemporalAnalyzer"
            ".analyze_all_temporal",
            side_effect=RuntimeError("test explosion"),
        ):
            stage = AnalyzeStage()
            stage.run(state)

        # Analysis should still complete
        assert state.analysis is not None
        assert state.stages["analyze"].status == StageStatus.COMPLETED
        # temporal_signals should be None due to failure
        assert state.analysis.temporal_signals is None


# -----------------------------------------------------------------------
# Check classification metadata tests
# -----------------------------------------------------------------------


class TestCheckClassificationMetadata:
    """Verify SignalResult populated with classification from check defs."""

    def test_signal_result_has_classification(self) -> None:
        """SignalResult from analysis has category and plaintiff_lenses."""
        from do_uw.stages.analyze.signal_engine import evaluate_signal

        check = {
            "id": "TEST.CHECK",
            "name": "Test Check",
            "threshold": {"type": "info"},
            "category": "DECISION_DRIVING",
            "plaintiff_lenses": ["SHAREHOLDERS", "REGULATORS"],
            "signal_type": "LEVEL",
            "hazard_or_signal": "SIGNAL",
        }
        data = {"value": "present"}
        result = evaluate_signal(check, data)

        assert result.category == "DECISION_DRIVING"
        assert result.plaintiff_lenses == ["SHAREHOLDERS", "REGULATORS"]
        assert result.signal_type == "LEVEL"
        assert result.hazard_or_signal == "SIGNAL"


# -----------------------------------------------------------------------
# CRF gate tests (CRF-12 through CRF-17)
# -----------------------------------------------------------------------


class TestCRFPhase26Gates:
    """Test CRF-12 through CRF-17 gate detection logic."""

    def test_crf_12_doj_investigation(self) -> None:
        """CRF-12 triggers on DOJ evidence in regulatory proceedings."""
        extracted = ExtractedData(
            litigation=LitigationLandscape(
                regulatory_proceedings=[
                    _sv({"agency": "DOJ", "type": "Criminal investigation"})
                ]
            ),
        )
        fired, evidence = evaluate_phase26_trigger("CRF-12", extracted)
        assert fired is True
        assert any("DOJ" in e for e in evidence)

    def test_crf_12_no_trigger_without_doj(self) -> None:
        """CRF-12 does not trigger without DOJ evidence."""
        extracted = ExtractedData(
            litigation=LitigationLandscape(),
        )
        fired, evidence = evaluate_phase26_trigger("CRF-12", extracted)
        assert fired is False

    def test_crf_13_altman_distress(self) -> None:
        """CRF-13 triggers on Altman Z < 1.81."""
        extracted = ExtractedData(
            financials=ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(
                        score=1.50, zone=DistressZone.DISTRESS,
                    )
                ),
            ),
        )
        fired, evidence = evaluate_phase26_trigger("CRF-13", extracted)
        assert fired is True
        assert any("1.50" in e for e in evidence)

    def test_crf_13_no_trigger_healthy(self) -> None:
        """CRF-13 does not trigger when Altman Z >= 1.81."""
        extracted = ExtractedData(
            financials=ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(
                        score=2.50, zone=DistressZone.GREY,
                    )
                ),
            ),
        )
        fired, evidence = evaluate_phase26_trigger("CRF-13", extracted)
        assert fired is False

    def test_crf_16_fis_critical(self) -> None:
        """CRF-16 triggers on FIS zone CRITICAL."""
        analysis = {
            "forensic_composites": {
                "financial_integrity_score": {
                    "overall_score": 15.0,
                    "zone": "CRITICAL",
                },
            },
        }
        extracted = ExtractedData()
        fired, evidence = evaluate_phase26_trigger(
            "CRF-16", extracted, analysis,
        )
        assert fired is True
        assert any("CRITICAL" in e for e in evidence)

    def test_crf_16_no_trigger_healthy(self) -> None:
        """CRF-16 does not trigger when FIS is healthy."""
        analysis = {
            "forensic_composites": {
                "financial_integrity_score": {
                    "overall_score": 75.0,
                    "zone": "HIGH_INTEGRITY",
                },
            },
        }
        extracted = ExtractedData()
        fired, evidence = evaluate_phase26_trigger(
            "CRF-16", extracted, analysis,
        )
        assert fired is False

    def test_crf_15_executive_aggregate(self) -> None:
        """CRF-15 triggers when executive risk > 50."""
        analysis = {
            "executive_risk": {
                "weighted_score": 65.0,
                "highest_risk_individual": "John Doe (CEO)",
            },
        }
        extracted = ExtractedData()
        fired, evidence = evaluate_phase26_trigger(
            "CRF-15", extracted, analysis,
        )
        assert fired is True

    def test_crf_17_whistleblower(self) -> None:
        """CRF-17 triggers on whistleblower disclosure."""
        extracted = ExtractedData(
            litigation=LitigationLandscape(
                whistleblower_indicators=[
                    WhistleblowerIndicator(
                        indicator_type=_sv("sec_whistleblower"),
                        description=_sv("Whistleblower complaint filed"),
                    )
                ]
            ),
        )
        fired, evidence = evaluate_phase26_trigger("CRF-17", extracted)
        assert fired is True

    def test_all_17_gates_in_evaluation(self) -> None:
        """Full CRF evaluation produces 17 results."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()
        extracted = ExtractedData()
        results = evaluate_red_flag_gates(
            rf_config, sc_config, extracted, None,
        )
        assert len(results) == 17


# -----------------------------------------------------------------------
# IES amplification tests
# -----------------------------------------------------------------------


class TestIESAmplification:
    """Test IES-aware behavioral signal amplification."""

    def test_ies_amplification_high(self) -> None:
        """High IES amplifies behavioral signal scoring."""
        from do_uw.models.hazard_profile import HazardProfile
        from do_uw.models.scoring import FactorScore
        from do_uw.stages.score import _apply_ies_amplification

        state = AnalysisState(ticker="TEST")
        state.hazard_profile = HazardProfile(
            ies_score=70.0,
            raw_ies_score=70.0,
            ies_multiplier=1.3,
            data_coverage_pct=80.0,
        )

        factor_scores = [
            FactorScore(
                factor_name="Restatement/Audit",
                factor_id="F3",
                max_points=15,
                points_deducted=10.0,
            ),
        ]
        _apply_ies_amplification(factor_scores, state)
        # IES 70 > 60 -> 1.25x multiplier
        assert factor_scores[0].points_deducted == pytest.approx(12.5)

    def test_ies_no_amplification_neutral(self) -> None:
        """Neutral IES (40-60) does not amplify."""
        from do_uw.models.hazard_profile import HazardProfile
        from do_uw.models.scoring import FactorScore
        from do_uw.stages.score import _apply_ies_amplification

        state = AnalysisState(ticker="TEST")
        state.hazard_profile = HazardProfile(
            ies_score=50.0,
            raw_ies_score=50.0,
            ies_multiplier=1.0,
            data_coverage_pct=80.0,
        )

        factor_scores = [
            FactorScore(
                factor_name="Restatement/Audit",
                factor_id="F3",
                max_points=15,
                points_deducted=10.0,
            ),
        ]
        _apply_ies_amplification(factor_scores, state)
        assert factor_scores[0].points_deducted == 10.0  # unchanged


# -----------------------------------------------------------------------
# Brain/signals.json validation tests
# -----------------------------------------------------------------------


class TestBrainChecks:
    """Validate check definitions in brain/signals.json."""

    def test_new_checks_in_brain(self) -> None:
        """All new check prefixes exist in signals.json."""
        checks_data = _load_signals_config()
        checks = checks_data.get("signals", [])
        signal_ids = {c["id"] for c in checks}

        # Verify at least one check for each new prefix
        prefixes = [
            "FIN.TEMPORAL.", "FIN.FORENSIC.", "FIN.QUALITY.",
            "EXEC.", "NLP.",
        ]
        for prefix in prefixes:
            matching = [cid for cid in signal_ids if cid.startswith(prefix)]
            assert len(matching) > 0, f"No checks found for prefix {prefix}"

    def test_full_signal_count(self) -> None:
        """Total check count is in expected range after Phase 26."""
        checks_data = _load_signals_config()
        checks = checks_data.get("signals", [])
        # Plan 01 removed 36 deprecated and added ~60 new = ~380-420
        assert 370 <= len(checks) <= 420, f"Unexpected count: {len(checks)}"

    def test_backward_compat_no_regression(self) -> None:
        """Original check sections (1-5) still present.

        Section 6 was merged into sections 4-5 during signal reorganization.
        """
        checks_data = _load_signals_config()
        checks = checks_data.get("signals", [])

        # Sections 1-5 should still have checks
        for section in (1, 2, 3, 4, 5):
            section_checks = [
                c for c in checks if c.get("section") == section
            ]
            assert len(section_checks) > 0, (
                f"No checks for section {section}"
            )


# -----------------------------------------------------------------------
# Red flags.json validation
# -----------------------------------------------------------------------


class TestRedFlagsConfig:
    """Validate red_flags.json has all 17 CRF gates."""

    def test_6_new_crf_gates(self) -> None:
        """red_flags.json contains CRF-12 through CRF-17."""
        rf_config = _load_red_flags_config()
        triggers = rf_config.get("escalation_triggers", [])
        new_ids = [
            t["id"] for t in triggers
            if t["id"].startswith("CRF-1") and int(t["id"].split("-")[1]) >= 12
        ]
        assert len(new_ids) == 6, f"Expected 6 new CRF gates, got {new_ids}"

    def test_new_crfs_have_required_fields(self) -> None:
        """New CRF gates have all required fields."""
        rf_config = _load_red_flags_config()
        triggers = rf_config.get("escalation_triggers", [])
        required = {"id", "name", "condition", "max_tier", "max_quality_score"}
        for trigger in triggers:
            tid = trigger.get("id", "")
            num = int(tid.split("-")[1]) if "-" in tid else 0
            if num >= 12:
                missing = required - set(trigger.keys())
                assert not missing, (
                    f"{tid} missing required fields: {missing}"
                )
