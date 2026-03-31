"""Tests for LLM extraction schemas and registry."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from do_uw.stages.extract.llm.prompts import (
    CAPITAL_SYSTEM_PROMPT,
    DEF14A_SYSTEM_PROMPT,
    EIGHT_K_SYSTEM_PROMPT,
    OWNERSHIP_SYSTEM_PROMPT,
    TEN_K_SYSTEM_PROMPT,
    TEN_Q_SYSTEM_PROMPT,
    get_prompt,
)
from do_uw.stages.extract.llm.schemas import (
    SCHEMA_REGISTRY,
    CapitalFilingExtraction,
    DEF14AExtraction,
    EightKExtraction,
    SC13DExtraction,
    SC13GExtraction,
    SchemaEntry,
    TenKExtraction,
    TenQExtraction,
    get_schema_for_filing,
)

# ---------------------------------------------------------------------------
# Schema instantiation tests (all defaults, no required fields)
# ---------------------------------------------------------------------------

ALL_SCHEMAS: list[type[BaseModel]] = [
    TenKExtraction,
    DEF14AExtraction,
    EightKExtraction,
    TenQExtraction,
    SC13DExtraction,
    SC13GExtraction,
    CapitalFilingExtraction,
]


@pytest.mark.parametrize("schema_cls", ALL_SCHEMAS, ids=lambda c: c.__name__)
def test_schema_instantiates_with_defaults(schema_cls: type[BaseModel]) -> None:
    """Every schema should instantiate with no arguments (all fields optional)."""
    instance = schema_cls()
    assert instance is not None


@pytest.mark.parametrize("schema_cls", ALL_SCHEMAS, ids=lambda c: c.__name__)
def test_schema_produces_valid_json_schema(schema_cls: type[BaseModel]) -> None:
    """Every schema should produce a valid JSON schema."""
    json_schema = schema_cls.model_json_schema()
    assert "title" in json_schema
    assert "properties" in json_schema
    assert "type" in json_schema
    assert json_schema["type"] == "object"


@pytest.mark.parametrize("schema_cls", ALL_SCHEMAS, ids=lambda c: c.__name__)
def test_schema_has_sufficient_fields(schema_cls: type[BaseModel]) -> None:
    """Each schema should have at least 5 fields for meaningful extraction."""
    field_count = len(schema_cls.model_fields)
    assert field_count >= 5, (
        f"{schema_cls.__name__} has only {field_count} fields"
    )


# ---------------------------------------------------------------------------
# Schema nesting depth tests
# ---------------------------------------------------------------------------


def _get_max_depth(schema: dict[str, Any], defs: dict[str, Any], depth: int = 0) -> int:
    """Recursively calculate max nesting depth of a JSON schema."""
    max_d = depth
    props = schema.get("properties", {})
    for _name, prop in props.items():
        # Check if property references a $def
        ref = prop.get("$ref", "")
        if ref:
            ref_name = ref.rsplit("/", 1)[-1]
            if ref_name in defs:
                sub = defs[ref_name]
                max_d = max(max_d, _get_max_depth(sub, defs, depth + 1))
        # Check array items
        items = prop.get("items", {})
        if isinstance(items, dict):
            item_ref = items.get("$ref", "")
            if item_ref:
                ref_name = item_ref.rsplit("/", 1)[-1]
                if ref_name in defs:
                    sub = defs[ref_name]
                    max_d = max(max_d, _get_max_depth(sub, defs, depth + 1))
    return max_d


@pytest.mark.parametrize("schema_cls", ALL_SCHEMAS, ids=lambda c: c.__name__)
def test_schema_nesting_max_3_levels(schema_cls: type[BaseModel]) -> None:
    """Schema nesting should be max 3 levels (flat for structured output)."""
    json_schema = schema_cls.model_json_schema()
    defs = json_schema.get("$defs", {})
    max_depth = _get_max_depth(json_schema, defs)
    assert max_depth <= 3, (
        f"{schema_cls.__name__} has nesting depth {max_depth} (max 3)"
    )


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

EXPECTED_FORM_TYPES = [
    "10-K", "20-F", "DEF 14A", "10-Q", "6-K",
    "8-K", "SC 13D", "SC 13G", "S-3", "S-1", "424B",
]


def test_registry_has_all_expected_form_types() -> None:
    """Registry should have entries for all 11 expected form types."""
    for form_type in EXPECTED_FORM_TYPES:
        assert form_type in SCHEMA_REGISTRY, (
            f"Missing registry entry for {form_type!r}"
        )


def test_registry_has_exactly_11_entries() -> None:
    """Registry should have exactly 11 entries (no extras)."""
    assert len(SCHEMA_REGISTRY) == 11


def test_registry_excludes_form_4() -> None:
    """Form 4 should NOT be in the registry (XML-parsed, not LLM-extracted)."""
    assert "4" not in SCHEMA_REGISTRY
    assert "Form 4" not in SCHEMA_REGISTRY


def test_registry_entries_are_schema_entries() -> None:
    """All registry values should be SchemaEntry instances."""
    for form_type, entry in SCHEMA_REGISTRY.items():
        assert isinstance(entry, SchemaEntry), (
            f"{form_type} entry is not SchemaEntry"
        )
        assert issubclass(entry.schema, BaseModel)
        assert isinstance(entry.prompt_key, str)
        assert isinstance(entry.max_tokens, int)
        assert entry.max_tokens > 0


def test_registry_fpi_uses_domestic_schemas() -> None:
    """FPI forms should map to their domestic equivalents."""
    assert SCHEMA_REGISTRY["20-F"].schema is TenKExtraction
    assert SCHEMA_REGISTRY["6-K"].schema is TenQExtraction


def test_registry_capital_filings_share_schema() -> None:
    """S-3, S-1, and 424B should all use CapitalFilingExtraction."""
    for form_type in ("S-3", "S-1", "424B"):
        assert SCHEMA_REGISTRY[form_type].schema is CapitalFilingExtraction


# ---------------------------------------------------------------------------
# get_schema_for_filing tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("form_type", EXPECTED_FORM_TYPES)
def test_get_schema_returns_entry(form_type: str) -> None:
    """get_schema_for_filing should return SchemaEntry for valid types."""
    result = get_schema_for_filing(form_type)
    assert result is not None
    assert isinstance(result, SchemaEntry)


def test_get_schema_returns_none_for_form4() -> None:
    """get_schema_for_filing should return None for Form 4."""
    assert get_schema_for_filing("4") is None


def test_get_schema_returns_none_for_unknown() -> None:
    """get_schema_for_filing should return None for unknown types."""
    assert get_schema_for_filing("UNKNOWN") is None
    assert get_schema_for_filing("") is None


# ---------------------------------------------------------------------------
# Prompt tests
# ---------------------------------------------------------------------------

PROMPT_KEYS = ["ten_k", "def14a", "eight_k", "ten_q", "ownership", "capital"]
PROMPT_CONSTANTS = [
    TEN_K_SYSTEM_PROMPT,
    DEF14A_SYSTEM_PROMPT,
    EIGHT_K_SYSTEM_PROMPT,
    TEN_Q_SYSTEM_PROMPT,
    OWNERSHIP_SYSTEM_PROMPT,
    CAPITAL_SYSTEM_PROMPT,
]


@pytest.mark.parametrize("key", PROMPT_KEYS)
def test_get_prompt_returns_nonempty_string(key: str) -> None:
    """get_prompt should return a non-empty string for each key."""
    prompt = get_prompt(key)
    assert isinstance(prompt, str)
    assert len(prompt) > 50, f"Prompt for {key!r} is too short"


def test_get_prompt_raises_for_unknown_key() -> None:
    """get_prompt should raise KeyError for unknown keys."""
    with pytest.raises(KeyError, match="Unknown prompt key"):
        get_prompt("nonexistent")


@pytest.mark.parametrize("prompt", PROMPT_CONSTANTS)
def test_prompts_contain_anti_hallucination(prompt: str) -> None:
    """All prompts should contain anti-hallucination instructions."""
    assert "NEVER fabricate" in prompt or "never fabricate" in prompt.lower()


@pytest.mark.parametrize("prompt", PROMPT_CONSTANTS)
def test_prompts_mention_do_underwriting(prompt: str) -> None:
    """All prompts should mention D&O underwriting context."""
    assert "D&O" in prompt


def test_all_registry_prompt_keys_have_prompts() -> None:
    """Every prompt_key in the registry should have a corresponding prompt."""
    seen_keys: set[str] = set()
    for _form_type, entry in SCHEMA_REGISTRY.items():
        seen_keys.add(entry.prompt_key)

    for key in seen_keys:
        prompt = get_prompt(key)
        assert len(prompt) > 0


# ---------------------------------------------------------------------------
# Specific schema content tests
# ---------------------------------------------------------------------------


def test_ten_k_has_risk_factors_field() -> None:
    """TenKExtraction should have a risk_factors list field."""
    assert "risk_factors" in TenKExtraction.model_fields


def test_ten_k_has_legal_proceedings_field() -> None:
    """TenKExtraction should have a legal_proceedings list field."""
    assert "legal_proceedings" in TenKExtraction.model_fields


def test_def14a_has_directors_field() -> None:
    """DEF14AExtraction should have a directors list field."""
    assert "directors" in DEF14AExtraction.model_fields


def test_def14a_has_compensation_field() -> None:
    """DEF14AExtraction should have named_executive_officers."""
    assert "named_executive_officers" in DEF14AExtraction.model_fields


def test_eight_k_has_restatement_fields() -> None:
    """EightKExtraction should have restatement fields (Item 4.02)."""
    assert "restatement_periods" in EightKExtraction.model_fields
    assert "restatement_reason" in EightKExtraction.model_fields


def test_sc13d_has_activist_fields() -> None:
    """SC13DExtraction should have activist intent fields."""
    assert "is_activist" in SC13DExtraction.model_fields
    assert "demands" in SC13DExtraction.model_fields
    assert "purpose" in SC13DExtraction.model_fields


def test_capital_filing_has_offering_fields() -> None:
    """CapitalFilingExtraction should have offering detail fields."""
    assert "offering_type" in CapitalFilingExtraction.model_fields
    assert "underwriters" in CapitalFilingExtraction.model_fields
    assert "dilution_pct" in CapitalFilingExtraction.model_fields
