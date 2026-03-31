"""Tests for LLMExtractor core class.

Validates schema hashing, cache integration, error handling paths,
budget enforcement, and API mocking. No actual Anthropic API calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from do_uw.stages.extract.llm.cache import ExtractionCache
from do_uw.stages.extract.llm.extractor import (
    LLMExtractor,
    schema_hash,
)

# --- Test schemas ---


class SampleExtraction(BaseModel):
    """Simple test schema for extraction tests."""

    field1: str = ""
    field2: int = 0


class SampleExtractionV2(BaseModel):
    """Modified schema to test hash changes."""

    field1: str = ""
    field2: int = 0
    field3: float = 0.0


# --- schema_hash tests ---


def test_schema_hash_deterministic() -> None:
    """Same model always produces the same hash."""
    h1 = schema_hash(SampleExtraction)
    h2 = schema_hash(SampleExtraction)
    assert h1 == h2


def test_schema_hash_is_12_char_hex() -> None:
    """Hash is a 12-character hex string."""
    h = schema_hash(SampleExtraction)
    assert len(h) == 12
    assert all(c in "0123456789abcdef" for c in h)


def test_schema_hash_changes_with_fields() -> None:
    """Different model produces a different hash."""
    h1 = schema_hash(SampleExtraction)
    h2 = schema_hash(SampleExtractionV2)
    assert h1 != h2


# --- LLMExtractor guard tests ---


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_none_when_instructor_missing() -> None:
    """Returns None when instructor is not installed."""
    extractor = LLMExtractor()
    with patch(
        "do_uw.stages.extract.llm.extractor.instructor", None
    ):
        result = extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-001",
            "10-K",
            "Extract data.",
        )
    assert result is None


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_none_when_anthropic_missing() -> None:
    """Returns None when anthropic is not installed."""
    extractor = LLMExtractor()
    with patch(
        "do_uw.stages.extract.llm.extractor.anthropic", None
    ):
        result = extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-001",
            "10-K",
            "Extract data.",
        )
    assert result is None


@patch.dict("os.environ", {}, clear=True)
def test_extract_returns_none_without_api_key() -> None:
    """Returns None when ANTHROPIC_API_KEY is not set."""
    extractor = LLMExtractor()
    result = extractor.extract(
        "filing text",
        SampleExtraction,
        "acc-001",
        "10-K",
        "Extract data.",
    )
    assert result is None


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_none_when_over_budget() -> None:
    """Returns None when cost budget is exceeded."""
    extractor = LLMExtractor(budget_usd=0.0)  # Zero budget = always over
    # Need to push it over: record one token to trigger
    extractor._cost_tracker.record(input_tokens=1, output_tokens=1)
    result = extractor.extract(
        "filing text",
        SampleExtraction,
        "acc-001",
        "10-K",
        "Extract data.",
    )
    assert result is None


# --- Cache interaction tests ---


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_cached_result(tmp_path: Path) -> None:
    """Returns cached result without calling API."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")
    version = schema_hash(SampleExtraction)

    # Pre-populate cache
    test_data = SampleExtraction(field1="cached", field2=42)
    cache.set(
        "acc-001", "10-K", version,
        test_data.model_dump_json(),
    )

    extractor = LLMExtractor(cache=cache)

    # This should return cached result without calling API
    result = extractor.extract(
        "filing text",
        SampleExtraction,
        "acc-001",
        "10-K",
        "Extract data.",
    )

    assert result is not None
    assert result.field1 == "cached"
    assert result.field2 == 42
    cache.close()


# --- API call tests ---


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_calls_api_and_caches(tmp_path: Path) -> None:
    """Successful extraction calls API and caches result."""
    cache = ExtractionCache(db_path=tmp_path / "test.db")
    extractor = LLMExtractor(cache=cache)

    # Mock the API -- instructor.from_anthropic wraps Anthropic client
    mock_result = SampleExtraction(field1="extracted", field2=99)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_result

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
    ):
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        result = extractor.extract(
            "Sample filing text content.",
            SampleExtraction,
            "acc-002",
            "10-K",
            "Extract data.",
        )

    assert result is not None
    assert result.field1 == "extracted"
    assert result.field2 == 99

    # Verify it was cached
    version = schema_hash(SampleExtraction)
    cached = cache.get("acc-002", "10-K", version)
    assert cached is not None

    # Verify cost was tracked
    assert extractor.cost_summary["extraction_count"] == 1
    assert extractor.cost_summary["total_cost_usd"] > 0
    cache.close()


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_none_on_api_error() -> None:
    """Returns None when API call raises an exception."""
    extractor = LLMExtractor()

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError(
            "API error"
        )
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        result = extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-003",
            "10-K",
            "Extract data.",
        )

    assert result is None
    # Cost should not be recorded for failed extractions
    assert extractor.cost_summary["extraction_count"] == 0


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_returns_none_for_oversized_filing() -> None:
    """Returns None when filing exceeds token limit."""
    extractor = LLMExtractor()

    # Create a filing that exceeds 190k tokens (~760k chars)
    oversized_text = "x" * 800_000

    with patch(
        "do_uw.stages.extract.llm.extractor.instructor"
    ) as mock_instructor:
        result = extractor.extract(
            oversized_text,
            SampleExtraction,
            "acc-004",
            "10-K",
            "Extract data.",
        )

    assert result is None
    # API should never have been called
    mock_instructor.from_anthropic.assert_not_called()


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_without_cache() -> None:
    """Extraction works without cache (cache=None)."""
    extractor = LLMExtractor(cache=None)

    mock_result = SampleExtraction(field1="no-cache", field2=1)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_result

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
    ):
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        result = extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-005",
            "10-K",
            "Extract data.",
        )

    assert result is not None
    assert result.field1 == "no-cache"


def test_cost_summary_property() -> None:
    """cost_summary delegates to CostTracker.summary()."""
    extractor = LLMExtractor(budget_usd=5.0)
    summary = extractor.cost_summary
    assert summary["budget_usd"] == 5.0
    assert summary["extraction_count"] == 0


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_passes_system_prompt(tmp_path: Path) -> None:
    """System prompt is passed to the API call."""
    extractor = LLMExtractor()

    mock_result = SampleExtraction(field1="test", field2=1)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_result

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
    ):
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-006",
            "10-K",
            "Custom system prompt.",
        )

    # Verify the system prompt and messages passed to the API
    call_kwargs: dict[str, Any] = (
        mock_client.messages.create.call_args.kwargs
    )
    assert call_kwargs["system"] == "Custom system prompt."
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "user"


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_error_log_includes_exception_type() -> None:
    """Error log includes exception type name for debugging."""
    extractor = LLMExtractor()

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
        patch(
            "do_uw.stages.extract.llm.extractor.logger"
        ) as mock_logger,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = ValueError(
            "test error"
        )
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        result = extractor.extract(
            "filing text",
            SampleExtraction,
            "acc-007",
            "10-K",
            "Extract data.",
        )

    assert result is None
    # Find the warning call that includes the exception type
    warning_calls = mock_logger.warning.call_args_list
    assert len(warning_calls) >= 1
    log_msg = warning_calls[0].args[0]
    log_args = warning_calls[0].args[1:]
    # Format string should include %s placeholders for accession and type
    assert "LLM extraction failed" in log_msg
    # The exception type name should be in the logged args
    assert "ValueError" in log_args


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
def test_extract_budget_warning_at_80_percent() -> None:
    """Warns when cost budget is 80% consumed."""
    # Budget is tiny; pre-load tracker to 80% so next extraction triggers
    extractor = LLMExtractor(budget_usd=0.001)
    # Push to 80% usage before extraction
    extractor._cost_tracker.total_cost_usd = 0.0008

    mock_result = SampleExtraction(field1="test", field2=1)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_result

    with (
        patch(
            "do_uw.stages.extract.llm.extractor.anthropic"
        ) as mock_anthropic,
        patch(
            "do_uw.stages.extract.llm.extractor.instructor"
        ) as mock_instructor,
        patch(
            "do_uw.stages.extract.llm.extractor.logger"
        ) as mock_logger,
    ):
        mock_anthropic.Anthropic.return_value = MagicMock()
        mock_instructor.from_anthropic.return_value = mock_client

        extractor.extract(
            "Some filing text here.",
            SampleExtraction,
            "acc-008",
            "10-K",
            "Extract data.",
        )

    # Should have logged a budget warning
    warning_calls = mock_logger.warning.call_args_list
    budget_warnings = [
        c for c in warning_calls
        if "budget" in str(c.args[0]).lower()
        and "consumed" in str(c.args[0]).lower()
    ]
    assert len(budget_warnings) >= 1
