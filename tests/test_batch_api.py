"""Tests for the Batch API utility (validation/batch.py).

Verifies request construction, result parsing with valid and invalid
schemas, and error handling. All anthropic API calls are mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from do_uw.validation.batch import (
    BatchExtractor,
    _pydantic_to_tool_schema,
)

# -- Test fixtures --


class SampleExtraction(BaseModel):
    """Minimal Pydantic model for testing."""

    company_name: str = Field(description="Name of the company")
    revenue: float | None = Field(default=None, description="Revenue")


@pytest.fixture
def extractor() -> BatchExtractor:
    """Create a BatchExtractor with default settings."""
    return BatchExtractor(model="claude-haiku-4-5-20250315")


# -- Tool schema conversion tests --


def test_pydantic_to_tool_schema() -> None:
    """Tool schema includes name, description, and input_schema."""
    tool = _pydantic_to_tool_schema(SampleExtraction)
    assert tool["name"] == "SampleExtraction"
    assert "SampleExtraction" in tool["description"]
    assert "properties" in tool["input_schema"]
    props = tool["input_schema"]["properties"]
    assert "company_name" in props
    assert "revenue" in props


# -- Request construction tests --


def test_prepare_request_format(extractor: BatchExtractor) -> None:
    """Prepared request has correct custom_id and params structure."""
    req = extractor.prepare_request(
        filing_text="Sample filing content",
        form_type="10-K",
        accession="0001234567-24-001234",
        system_prompt="Extract data.",
        schema_cls=SampleExtraction,
    )

    assert req["custom_id"] == "10-K:0001234567-24-001234"

    params = req["params"]
    assert params["model"] == "claude-haiku-4-5-20250315"
    assert params["max_tokens"] == 16384
    assert params["system"] == "Extract data."
    assert len(params["messages"]) == 1
    assert params["messages"][0]["role"] == "user"
    assert params["messages"][0]["content"] == "Sample filing content"

    # Tool definition
    assert len(params["tools"]) == 1
    tool = params["tools"][0]
    assert tool["name"] == "SampleExtraction"
    assert "input_schema" in tool

    # Tool choice forces this tool
    assert params["tool_choice"]["type"] == "tool"
    assert params["tool_choice"]["name"] == "SampleExtraction"


def test_prepare_request_custom_id_formats(
    extractor: BatchExtractor,
) -> None:
    """Custom IDs correctly combine form_type and accession."""
    req = extractor.prepare_request(
        filing_text="text",
        form_type="DEF 14A",
        accession="0009999999-23-000001",
        system_prompt="prompt",
        schema_cls=SampleExtraction,
    )
    assert req["custom_id"] == "DEF 14A:0009999999-23-000001"


# -- Batch submission tests --


@patch("do_uw.validation.batch._anthropic_mod")
def test_submit_batch_success(
    mock_anthropic: MagicMock,
    extractor: BatchExtractor,
) -> None:
    """submit_batch returns batch ID on success."""
    mock_client = MagicMock()
    mock_batch = MagicMock()
    mock_batch.id = "msgbatch_abc123"
    mock_client.messages.batches.create.return_value = mock_batch
    mock_anthropic.Anthropic.return_value = mock_client

    requests: list[dict[str, Any]] = [{"custom_id": "test", "params": {}}]
    result = extractor.submit_batch(requests)

    assert result == "msgbatch_abc123"
    mock_client.messages.batches.create.assert_called_once_with(
        requests=requests,
    )


@patch("do_uw.validation.batch._anthropic_mod")
def test_submit_batch_failure(
    mock_anthropic: MagicMock,
    extractor: BatchExtractor,
) -> None:
    """submit_batch returns None on API error."""
    mock_client = MagicMock()
    mock_client.messages.batches.create.side_effect = RuntimeError("API down")
    mock_anthropic.Anthropic.return_value = mock_client

    result = extractor.submit_batch([{"custom_id": "test", "params": {}}])
    assert result is None


# -- Result parsing tests --


def test_parse_results_valid_schema(
    extractor: BatchExtractor,
) -> None:
    """Valid tool_use content is parsed into Pydantic model."""
    # Simulate a succeeded batch result
    tool_block = SimpleNamespace(
        type="tool_use",
        input={"company_name": "Acme Corp", "revenue": 1000.0},
    )
    message = SimpleNamespace(content=[tool_block])
    result_obj = SimpleNamespace(type="succeeded", message=message)

    results: list[dict[str, Any]] = [
        {"custom_id": "10-K:acc001", "result": result_obj},
    ]
    schema_map: dict[str, type[BaseModel]] = {
        "10-K:acc001": SampleExtraction,
    }

    parsed = extractor.parse_results(results, schema_map)
    assert "10-K:acc001" in parsed
    item = parsed["10-K:acc001"]
    assert item is not None
    assert isinstance(item, SampleExtraction)
    assert item.company_name == "Acme Corp"
    assert item.revenue == 1000.0


def test_parse_results_invalid_schema(
    extractor: BatchExtractor,
) -> None:
    """Invalid tool_use content returns None with warning."""
    tool_block = SimpleNamespace(
        type="tool_use",
        # Missing required field company_name
        input={"revenue": "not_a_number_either"},
    )
    message = SimpleNamespace(content=[tool_block])
    result_obj = SimpleNamespace(type="succeeded", message=message)

    results: list[dict[str, Any]] = [
        {"custom_id": "10-K:acc002", "result": result_obj},
    ]

    # Use a strict schema that requires company_name
    class StrictSchema(BaseModel):
        company_name: str
        revenue: float

    schema_map: dict[str, type[BaseModel]] = {
        "10-K:acc002": StrictSchema,
    }

    parsed = extractor.parse_results(results, schema_map)
    assert parsed["10-K:acc002"] is None


def test_parse_results_errored_result(
    extractor: BatchExtractor,
) -> None:
    """Non-succeeded results return None."""
    result_obj = SimpleNamespace(type="errored", message=None)

    results: list[dict[str, Any]] = [
        {"custom_id": "10-K:acc003", "result": result_obj},
    ]
    schema_map: dict[str, type[BaseModel]] = {
        "10-K:acc003": SampleExtraction,
    }

    parsed = extractor.parse_results(results, schema_map)
    assert parsed["10-K:acc003"] is None


def test_parse_results_no_tool_block(
    extractor: BatchExtractor,
) -> None:
    """Results without tool_use blocks return None."""
    text_block = SimpleNamespace(type="text", text="no tools here")
    message = SimpleNamespace(content=[text_block])
    result_obj = SimpleNamespace(type="succeeded", message=message)

    results: list[dict[str, Any]] = [
        {"custom_id": "10-K:acc004", "result": result_obj},
    ]
    schema_map: dict[str, type[BaseModel]] = {
        "10-K:acc004": SampleExtraction,
    }

    parsed = extractor.parse_results(results, schema_map)
    assert parsed["10-K:acc004"] is None


def test_parse_results_unknown_custom_id(
    extractor: BatchExtractor,
) -> None:
    """Results with unknown custom_id map to None."""
    tool_block = SimpleNamespace(
        type="tool_use",
        input={"company_name": "Test"},
    )
    message = SimpleNamespace(content=[tool_block])
    result_obj = SimpleNamespace(type="succeeded", message=message)

    results: list[dict[str, Any]] = [
        {"custom_id": "unknown:id", "result": result_obj},
    ]
    # Empty schema map -- no mapping for this custom_id
    schema_map: dict[str, type[BaseModel]] = {}

    parsed = extractor.parse_results(results, schema_map)
    assert parsed["unknown:id"] is None
