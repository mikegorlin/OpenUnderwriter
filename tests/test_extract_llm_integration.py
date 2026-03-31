"""Integration tests for LLM extraction wiring in ExtractStage.

Tests the Phase 0 LLM extraction pre-step: schema lookup, extractor
invocation, caching, cost tracking, graceful degradation, and CLI
flag propagation. All LLM API calls are mocked.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue, StageStatus
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.governance import GovernanceData
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import MarketSignals
from do_uw.models.state import AcquiredData, AnalysisState

# Patch paths for LLM components (re-export namespace, used by lazy imports)
_LLM_PATH = "do_uw.stages.extract.llm.LLMExtractor"
_CACHE_PATH = "do_uw.stages.extract.llm.ExtractionCache"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_test_state(
    filing_docs: dict[str, list[dict[str, str]]] | None = None,
) -> AnalysisState:
    """Build minimal state for LLM extraction testing."""
    identity = CompanyIdentity(
        ticker="TEST", cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"), sector=_sourced_str("TECH"),
    )
    acquired = AcquiredData(
        filings={"company_facts": {"cik": 1234567, "entityName": "Test Corp",
                 "facts": {"us-gaap": {}, "dei": {}}}, "filing_texts": {}},
        market_data={"info": {"marketCap": 1e12}},
        filing_documents=filing_docs or {},
    )
    state = AnalysisState(
        ticker="TEST", company=CompanyProfile(identity=identity),
        acquired_data=acquired,
    )
    state.mark_stage_running("resolve")
    state.mark_stage_completed("resolve")
    state.mark_stage_running("acquire")
    state.mark_stage_completed("acquire")
    return state


def _make_filing_docs() -> dict[str, list[dict[str, str]]]:
    """Build filing_documents with 10-K, DEF 14A, and 8-K."""
    return {
        "10-K": [{"accession": "0001-24-001", "filing_date": "2025-02-15",
                   "form_type": "10-K", "full_text": "Annual report..."}],
        "DEF 14A": [{"accession": "0001-24-002", "filing_date": "2025-04-15",
                      "form_type": "DEF 14A", "full_text": "Proxy..."}],
        "8-K": [{"accession": "0001-24-003", "filing_date": "2025-01-10",
                  "form_type": "8-K", "full_text": "Current report..."}],
    }


def _mock_cost_summary(count: int = 0) -> dict[str, Any]:
    return {"extraction_count": count, "total_input_tokens": count * 5000,
            "total_output_tokens": count * 1000, "total_cost_usd": count * 0.01}


# ---------------------------------------------------------------------------
# Shared fixture: patches sub-orchestrators for extract stage
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_sub_orchestrators() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]
    """Patch all sub-orchestrators to prevent full extract run."""
    with ExitStack() as stack:
        stack.enter_context(patch(
            "do_uw.stages.extract.run_litigation_extractors",
            return_value=LitigationLandscape()))
        stack.enter_context(patch(
            "do_uw.stages.extract.run_governance_extractors",
            return_value=GovernanceData()))
        stack.enter_context(patch(
            "do_uw.stages.extract.run_market_extractors",
            return_value=MarketSignals()))
        stack.enter_context(patch(
            "do_uw.stages.extract.peer_group._enrich_candidate_yfinance",
            return_value={"marketCap": 1e12}))
        stack.enter_context(patch(
            "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase",
            return_value=[]))
        yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestLLMExtractionDisabled:
    """LLM extraction is skipped when use_llm=False."""

    def test_no_llm_when_disabled(self) -> None:
        """ExtractStage(use_llm=False) skips LLM extraction entirely."""
        from do_uw.stages.extract import ExtractStage

        state = _make_test_state(_make_filing_docs())
        stage = ExtractStage(use_llm=False)
        with patch(_LLM_PATH, side_effect=AssertionError("Should not call")):
            stage.run(state)

        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}
        assert state.stages["extract"].status == StageStatus.COMPLETED


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestLLMExtractionNoAPIKey:
    """LLM extraction returns empty when ANTHROPIC_API_KEY is unset."""

    def test_no_api_key_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without ANTHROPIC_API_KEY, LLM returns empty dict."""
        from do_uw.stages.extract import ExtractStage

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        state = _make_test_state(_make_filing_docs())
        ExtractStage(use_llm=True).run(state)

        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}
        assert state.stages["extract"].status == StageStatus.COMPLETED


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestLLMExtractionProcessesFilings:
    """LLM extraction processes each supported filing type."""

    def test_all_filing_types_processed(
        self, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Each filing type with a schema is sent to LLMExtractor."""
        from pydantic import BaseModel

        from do_uw.stages.extract import ExtractStage

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-fake")

        class MockExtraction(BaseModel):
            test_field: str = "extracted"

        mock_ext = MagicMock()
        mock_ext.extract.return_value = MockExtraction()
        mock_ext.cost_summary = _mock_cost_summary(3)

        state = _make_test_state(_make_filing_docs())
        with (
            patch(_LLM_PATH, return_value=mock_ext),
            patch(_CACHE_PATH),
            caplog.at_level(logging.INFO, logger="do_uw.stages.extract"),
        ):
            ExtractStage(use_llm=True).run(state)

        assert state.acquired_data is not None
        llm = state.acquired_data.llm_extractions
        assert len(llm) == 3
        assert "10-K:0001-24-001" in llm
        assert "DEF 14A:0001-24-002" in llm
        assert "8-K:0001-24-003" in llm
        for val in llm.values():
            assert isinstance(val, dict)
            assert val.get("test_field") == "extracted"  # type: ignore[union-attr]

        cost_msgs = [r.message for r in caplog.records
                     if "LLM extraction complete" in r.message]
        assert len(cost_msgs) >= 1
        assert "$0.0300" in cost_msgs[0]
        assert state.stages["extract"].status == StageStatus.COMPLETED


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestLLMExtractionAPIFailure:
    """LLM extraction handles API failures gracefully."""

    def test_api_failure_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """RuntimeError in LLMExtractor creation returns empty dict."""
        from do_uw.stages.extract import ExtractStage

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-fake")
        state = _make_test_state(_make_filing_docs())

        with (
            patch(_LLM_PATH, side_effect=RuntimeError("API unavailable")),
            patch(_CACHE_PATH),
            caplog.at_level(logging.WARNING, logger="do_uw.stages.extract"),
        ):
            ExtractStage(use_llm=True).run(state)

        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}
        warn_msgs = [r.message for r in caplog.records
                     if "LLM extraction failed" in r.message]
        assert len(warn_msgs) >= 1
        assert state.stages["extract"].status == StageStatus.COMPLETED


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestForm4NotLLMExtracted:
    """Form 4 filings are not sent to LLM extraction."""

    def test_form4_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Form 4 has no schema entry, so it is not LLM-extracted."""
        from do_uw.stages.extract import ExtractStage

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-fake")
        docs: dict[str, list[dict[str, str]]] = {
            "4": [{"accession": "0001-24-F4", "form_type": "4",
                    "full_text": "Form 4 XML content..."}],
        }
        mock_ext = MagicMock()
        mock_ext.extract.return_value = None
        mock_ext.cost_summary = _mock_cost_summary(0)

        state = _make_test_state(docs)
        with patch(_LLM_PATH, return_value=mock_ext), patch(_CACHE_PATH):
            ExtractStage(use_llm=True).run(state)

        mock_ext.extract.assert_not_called()
        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestCacheHitSkipsAPICall:
    """Cache hit prevents redundant API call."""

    def test_cache_hit_uses_cached_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When cache has data, extractor.extract returns cached model."""
        from pydantic import BaseModel

        from do_uw.stages.extract import ExtractStage

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-fake")
        docs: dict[str, list[dict[str, str]]] = {
            "10-K": [{"accession": "0001-24-CACHED", "form_type": "10-K",
                       "full_text": "Some 10-K text..."}],
        }

        class MockResult(BaseModel):
            cached_field: str = "from_cache"

        mock_ext = MagicMock()
        mock_ext.extract.return_value = MockResult()
        mock_ext.cost_summary = _mock_cost_summary(0)

        state = _make_test_state(docs)
        with patch(_LLM_PATH, return_value=mock_ext), patch(_CACHE_PATH):
            ExtractStage(use_llm=True).run(state)

        assert state.acquired_data is not None
        llm = state.acquired_data.llm_extractions
        assert "10-K:0001-24-CACHED" in llm
        assert llm["10-K:0001-24-CACHED"]["cached_field"] == "from_cache"


class TestNoLLMCLIFlagPropagates:
    """--no-llm CLI flag propagates to pipeline config."""

    def test_no_llm_in_pipeline_config(self) -> None:
        """Pipeline config receives no_llm=True from CLI."""
        from do_uw.pipeline import _build_default_stages  # pyright: ignore[reportPrivateUsage]
        from do_uw.stages.extract import ExtractStage

        stages = _build_default_stages(config={"no_llm": True})
        extract_stage = next(
            (s for s in stages if isinstance(s, ExtractStage)), None)
        assert extract_stage is not None
        assert extract_stage._use_llm is False  # pyright: ignore[reportPrivateUsage]

    def test_default_uses_llm(self) -> None:
        """Without no_llm, use_llm defaults to True."""
        from do_uw.pipeline import _build_default_stages  # pyright: ignore[reportPrivateUsage]
        from do_uw.stages.extract import ExtractStage

        stages = _build_default_stages()
        extract_stage = next(
            (s for s in stages if isinstance(s, ExtractStage)), None)
        assert extract_stage is not None
        assert extract_stage._use_llm is True  # pyright: ignore[reportPrivateUsage]


@pytest.mark.usefixtures("_patch_sub_orchestrators")
class TestLLMExtractionEdgeCases:
    """Edge cases: empty docs, missing text, import failure."""

    def test_empty_filing_documents(self) -> None:
        """Empty filing_documents produces empty llm_extractions."""
        from do_uw.stages.extract import ExtractStage

        state = _make_test_state({})
        ExtractStage(use_llm=True).run(state)
        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}
        assert state.stages["extract"].status == StageStatus.COMPLETED

    def test_skips_missing_full_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Docs without full_text are skipped."""
        from do_uw.stages.extract import ExtractStage

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-fake")
        docs: dict[str, list[dict[str, str]]] = {
            "10-K": [{"accession": "0001-24-NOTEXT", "form_type": "10-K",
                       "full_text": ""}],
        }
        mock_ext = MagicMock()
        mock_ext.cost_summary = _mock_cost_summary(0)
        state = _make_test_state(docs)

        with patch(_LLM_PATH, return_value=mock_ext), patch(_CACHE_PATH):
            ExtractStage(use_llm=True).run(state)

        mock_ext.extract.assert_not_called()
        assert state.acquired_data is not None
        assert state.acquired_data.llm_extractions == {}

    def test_cache_init_failure_returns_empty(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """If LLM cache creation fails, returns empty dict."""
        from do_uw.stages.extract import _run_llm_extraction  # pyright: ignore[reportPrivateUsage]

        state = _make_test_state(_make_filing_docs())
        with (
            patch(_CACHE_PATH, side_effect=RuntimeError("DB init failed")),
            caplog.at_level(logging.WARNING, logger="do_uw.stages.extract"),
        ):
            result = _run_llm_extraction(state, use_llm=True)
        assert result == {}


class TestAcquiredDataLLMExtractionsField:
    """The llm_extractions field on AcquiredData works correctly."""

    def test_default_empty_dict(self) -> None:
        """Default value is empty dict."""
        assert AcquiredData().llm_extractions == {}

    def test_serialization_roundtrip(self) -> None:
        """LLM extractions survive JSON serialization."""
        acquired = AcquiredData(llm_extractions={
            "10-K:acc1": {"field": "value", "nested": {"a": 1}},
            "DEF 14A:acc2": {"other": "data"},
        })
        loaded = AcquiredData.model_validate_json(acquired.model_dump_json())
        assert loaded.llm_extractions == acquired.llm_extractions
        assert loaded.llm_extractions["10-K:acc1"]["field"] == "value"
