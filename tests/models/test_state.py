"""Tests for AnalysisState root model and supporting types.

Validates:
- State creation with correct defaults
- JSON serialization roundtrip without data loss
- SourcedValue provenance enforcement
- Stage result lifecycle transitions
- All 7 pipeline stages present
- CompanyProfile nested model
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models import (
    PIPELINE_STAGES,
    AnalysisState,
    CompanyIdentity,
    CompanyProfile,
    Confidence,
    SourcedValue,
    StageStatus,
)


class TestAnalysisStateDefaults:
    """AnalysisState creation with sensible defaults."""

    def test_creates_with_ticker(self) -> None:
        state = AnalysisState(ticker="AAPL")
        assert state.ticker == "AAPL"
        assert state.version == "1.0.0"

    def test_all_seven_stages_present(self) -> None:
        state = AnalysisState(ticker="MSFT")
        assert len(state.stages) == 7
        expected = {
            "resolve", "acquire", "extract", "analyze",
            "score", "benchmark", "render",
        }
        assert set(state.stages.keys()) == expected

    def test_all_stages_start_pending(self) -> None:
        state = AnalysisState(ticker="GOOG")
        for stage_name, result in state.stages.items():
            assert result.status == StageStatus.PENDING, (
                f"Stage {stage_name} should be PENDING, got {result.status}"
            )
            assert result.stage == stage_name

    def test_stage_outputs_start_none(self) -> None:
        state = AnalysisState(ticker="TSLA")
        assert state.company is None
        assert state.acquired_data is None
        assert state.extracted is None
        assert state.analysis is None
        assert state.scoring is None
        assert state.benchmark is None

    def test_pipeline_stages_constant(self) -> None:
        assert len(PIPELINE_STAGES) == 7
        assert PIPELINE_STAGES[0] == "resolve"
        assert PIPELINE_STAGES[-1] == "render"


class TestSerializationRoundtrip:
    """JSON serialization roundtrip preserves all data."""

    def test_state_serialization_roundtrip(self) -> None:
        state = AnalysisState(ticker="AAPL")
        json_str = state.model_dump_json(indent=2)
        restored = AnalysisState.model_validate_json(json_str)
        assert restored.ticker == state.ticker
        assert restored.version == state.version
        assert len(restored.stages) == 7
        assert all(
            s.status == StageStatus.PENDING
            for s in restored.stages.values()
        )

    def test_roundtrip_with_company_profile(self) -> None:
        state = AnalysisState(ticker="AAPL")
        now = datetime.now(tz=UTC)
        state.company = CompanyProfile(
            identity=CompanyIdentity(
                ticker="AAPL",
                legal_name=SourcedValue(
                    value="Apple Inc.",
                    source="SEC EDGAR CIK 0000320193",
                    confidence=Confidence.HIGH,
                    as_of=now,
                ),
            ),
            market_cap=SourcedValue(
                value=3_000_000_000_000.0,
                source="Yahoo Finance 2026-02-07",
                confidence=Confidence.MEDIUM,
                as_of=now,
            ),
        )

        json_str = state.model_dump_json(indent=2)
        restored = AnalysisState.model_validate_json(json_str)

        assert restored.company is not None
        assert restored.company.identity.ticker == "AAPL"
        assert restored.company.identity.legal_name is not None
        assert restored.company.identity.legal_name.value == "Apple Inc."
        assert (
            restored.company.identity.legal_name.confidence == Confidence.HIGH
        )
        assert restored.company.market_cap is not None
        assert restored.company.market_cap.value == 3_000_000_000_000.0


class TestSourcedValue:
    """SourcedValue enforces provenance on every data point."""

    def test_sourced_value_requires_fields(self) -> None:
        now = datetime.now(tz=UTC)
        sv: SourcedValue[float] = SourcedValue(
            value=150.0,
            source="Yahoo Finance 2026-02-07",
            confidence=Confidence.MEDIUM,
            as_of=now,
        )
        assert sv.value == 150.0
        assert sv.source == "Yahoo Finance 2026-02-07"
        assert sv.confidence == Confidence.MEDIUM
        assert sv.retrieved_at is not None

    def test_sourced_value_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        sv: SourcedValue[str] = SourcedValue(
            value="Apple Inc.",
            source="SEC EDGAR",
            confidence=Confidence.HIGH,
            as_of=now,
        )
        json_str = sv.model_dump_json()
        restored = SourcedValue[str].model_validate_json(json_str)
        assert restored.value == "Apple Inc."
        assert restored.confidence == Confidence.HIGH


class TestStageTransitions:
    """Stage result lifecycle: PENDING -> RUNNING -> COMPLETED/FAILED."""

    def test_mark_stage_running(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("resolve")
        assert state.stages["resolve"].status == StageStatus.RUNNING
        assert state.stages["resolve"].started_at is not None

    def test_mark_stage_completed(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("resolve")
        state.mark_stage_completed("resolve")
        assert state.stages["resolve"].status == StageStatus.COMPLETED
        assert state.stages["resolve"].completed_at is not None
        assert state.stages["resolve"].duration_seconds is not None
        assert state.stages["resolve"].duration_seconds >= 0

    def test_mark_stage_failed(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("acquire")
        state.mark_stage_failed("acquire", "Connection timeout")
        assert state.stages["acquire"].status == StageStatus.FAILED
        assert state.stages["acquire"].error == "Connection timeout"

    def test_invalid_stage_raises(self) -> None:
        state = AnalysisState(ticker="TEST")
        import pytest
        with pytest.raises(ValueError, match="Unknown stage"):
            state.mark_stage_running("invalid_stage")
