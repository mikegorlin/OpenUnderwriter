"""Tests for the field registry YAML and loader module.

Validates:
- YAML loads successfully with correct count
- DIRECT_LOOKUP entries have required fields
- COMPUTED entries have required fields
- Dual root validation (extracted.* or company.*)
- Pydantic validation rejects invalid entries
- Cache behavior
- Registry version
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import ValidationError

from do_uw.brain.field_registry import (
    FieldRegistry,
    FieldRegistryEntry,
    _reset_cache,
    get_field_entry,
    load_field_registry,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the module-level cache before each test."""
    _reset_cache()
    yield
    _reset_cache()


# ---------------------------------------------------------------------------
# YAML loading tests
# ---------------------------------------------------------------------------


class TestLoadFieldRegistry:
    """Tests for load_field_registry() and the YAML content."""

    def test_loads_successfully(self):
        """Registry loads without error and returns a FieldRegistry."""
        registry = load_field_registry()
        assert isinstance(registry, FieldRegistry)

    def test_field_count(self):
        """Registry has the expected number of fields (17 base + 29 forensic = 46 after Phase 70)."""
        registry = load_field_registry()
        assert len(registry.fields) >= 46, (
            f"Expected >= 46 fields (17 base + 29 forensic), got {len(registry.fields)}"
        )

    def test_version_is_1(self):
        """Registry version is 1."""
        registry = load_field_registry()
        assert registry.version == 1

    def test_all_direct_lookup_have_path(self):
        """Every DIRECT_LOOKUP entry has a non-empty path."""
        registry = load_field_registry()
        for key, entry in registry.fields.items():
            if entry.type == "DIRECT_LOOKUP":
                assert entry.path, f"{key}: DIRECT_LOOKUP missing path"

    def test_all_computed_have_function(self):
        """Every COMPUTED entry has a non-empty function name."""
        registry = load_field_registry()
        for key, entry in registry.fields.items():
            if entry.type == "COMPUTED":
                assert entry.function, f"{key}: COMPUTED missing function"

    def test_all_computed_have_at_least_one_arg(self):
        """Every COMPUTED entry has at least one arg path."""
        registry = load_field_registry()
        for key, entry in registry.fields.items():
            if entry.type == "COMPUTED":
                assert len(entry.args) >= 1, f"{key}: COMPUTED has no args"

    def test_all_paths_start_with_valid_root(self):
        """All dotted paths start with 'extracted.', 'company.', or 'analysis.'."""
        valid_prefixes = ("extracted.", "company.", "analysis.")
        registry = load_field_registry()
        for key, entry in registry.fields.items():
            if entry.path:
                assert entry.path.startswith(valid_prefixes), (
                    f"{key}: path '{entry.path}' does not start with "
                    f"one of {valid_prefixes}"
                )
            for arg in entry.args:
                assert arg.startswith(valid_prefixes), (
                    f"{key}: arg '{arg}' does not start with "
                    f"one of {valid_prefixes}"
                )

    def test_known_direct_lookup_fields(self):
        """Spot-check that known DIRECT_LOOKUP fields exist and are correct."""
        registry = load_field_registry()
        # current_ratio
        cr = registry.fields["current_ratio"]
        assert cr.type == "DIRECT_LOOKUP"
        assert cr.path == "extracted.financials.liquidity"
        assert cr.key == "current_ratio"

        # decline_from_high
        dfh = registry.fields["decline_from_high"]
        assert dfh.type == "DIRECT_LOOKUP"
        assert dfh.path == "extracted.market.stock.decline_from_high_pct"

        # market_cap
        mc = registry.fields["market_cap"]
        assert mc.type == "DIRECT_LOOKUP"
        assert mc.path == "company.market_cap"

    def test_known_computed_fields(self):
        """Spot-check that known COMPUTED fields exist and are correct."""
        registry = load_field_registry()
        # active_sca_count
        asc = registry.fields["active_sca_count"]
        assert asc.type == "COMPUTED"
        assert asc.function == "count_active_scas"
        assert "extracted.litigation.securities_class_actions" in asc.args

        # filing_13d_count
        f13d = registry.fields["filing_13d_count"]
        assert f13d.type == "COMPUTED"
        assert f13d.function == "count_items"
        assert "extracted.governance.ownership.filings_13d_24mo" in f13d.args


# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------


class TestGetFieldEntry:
    """Tests for get_field_entry() convenience function."""

    def test_returns_entry_for_known_key(self):
        """get_field_entry returns the correct entry for a known key."""
        entry = get_field_entry("current_ratio")
        assert entry is not None
        assert entry.type == "DIRECT_LOOKUP"
        assert entry.path == "extracted.financials.liquidity"

    def test_returns_none_for_unknown_key(self):
        """get_field_entry returns None for an unknown key."""
        assert get_field_entry("nonexistent_field") is None

    def test_returns_none_for_empty_string(self):
        """get_field_entry returns None for an empty string key."""
        assert get_field_entry("") is None


# ---------------------------------------------------------------------------
# Cache behavior tests
# ---------------------------------------------------------------------------


class TestCacheBehavior:
    """Tests for the module-level caching."""

    def test_second_call_returns_same_object(self):
        """Second call returns the exact same object (cache hit)."""
        r1 = load_field_registry()
        r2 = load_field_registry()
        assert r1 is r2

    def test_reset_cache_clears(self):
        """After _reset_cache(), a new object is returned."""
        r1 = load_field_registry()
        _reset_cache()
        r2 = load_field_registry()
        assert r1 is not r2
        # But they should be equal
        assert r1.version == r2.version
        assert len(r1.fields) == len(r2.fields)


# ---------------------------------------------------------------------------
# Pydantic validation tests
# ---------------------------------------------------------------------------


class TestPydanticValidation:
    """Tests for FieldRegistryEntry validation rules."""

    def test_direct_lookup_without_path_rejected(self):
        """DIRECT_LOOKUP without path raises ValidationError."""
        with pytest.raises(ValidationError, match="path"):
            FieldRegistryEntry(type="DIRECT_LOOKUP", description="test")

    def test_computed_without_function_rejected(self):
        """COMPUTED without function raises ValidationError."""
        with pytest.raises(ValidationError, match="function"):
            FieldRegistryEntry(
                type="COMPUTED", args=["extracted.x.y"], description="test"
            )

    def test_computed_without_args_rejected(self):
        """COMPUTED without args raises ValidationError."""
        with pytest.raises(ValidationError, match="arg"):
            FieldRegistryEntry(
                type="COMPUTED", function="my_func", description="test"
            )

    def test_extra_fields_rejected_on_entry(self):
        """extra='forbid' rejects unexpected fields on FieldRegistryEntry."""
        with pytest.raises(ValidationError, match="extra"):
            FieldRegistryEntry(
                type="DIRECT_LOOKUP",
                path="extracted.x.y",
                unexpected_field="bad",
            )

    def test_extra_fields_rejected_on_registry(self):
        """extra='forbid' rejects unexpected fields on FieldRegistry."""
        with pytest.raises(ValidationError, match="extra"):
            FieldRegistry(
                version=1,
                fields={},
                unexpected_top_level="bad",
            )

    def test_invalid_type_rejected(self):
        """Invalid type value raises ValidationError."""
        with pytest.raises(ValidationError):
            FieldRegistryEntry(
                type="INVALID_TYPE",  # type: ignore[arg-type]
                path="extracted.x.y",
            )


# ---------------------------------------------------------------------------
# Custom YAML loading tests (with tmpdir)
# ---------------------------------------------------------------------------


class TestCustomYAMLLoading:
    """Tests for loading from custom YAML paths."""

    def test_load_from_custom_path(self, tmp_path: Path):
        """Can load a valid registry from a custom path."""
        yaml_content = dedent("""\
            version: 1
            fields:
              test_field:
                type: DIRECT_LOOKUP
                path: extracted.test.path
                description: A test field
        """)
        registry_file = tmp_path / "test_registry.yaml"
        registry_file.write_text(yaml_content)

        registry = load_field_registry(path=registry_file)
        assert len(registry.fields) == 1
        assert "test_field" in registry.fields
        assert registry.fields["test_field"].path == "extracted.test.path"

    def test_load_invalid_yaml_raises(self, tmp_path: Path):
        """Loading YAML with invalid entries raises ValidationError."""
        yaml_content = dedent("""\
            version: 1
            fields:
              bad_field:
                type: DIRECT_LOOKUP
                description: Missing path
        """)
        registry_file = tmp_path / "bad_registry.yaml"
        registry_file.write_text(yaml_content)
        _reset_cache()

        with pytest.raises(ValidationError, match="path"):
            load_field_registry(path=registry_file)


# ---------------------------------------------------------------------------
# Phase 55 additions: new entries and COMPUTED_FUNCTIONS
# ---------------------------------------------------------------------------


class TestPhase55Additions:
    """Tests for Phase 55 field registry additions."""

    def test_cash_ratio_entry_exists(self):
        """cash_ratio DIRECT_LOOKUP entry loads correctly."""
        entry = get_field_entry("cash_ratio")
        assert entry is not None
        assert entry.type == "DIRECT_LOOKUP"
        assert entry.path == "extracted.financials.liquidity"
        assert entry.key == "cash_ratio"

    def test_cash_burn_months_entry_exists(self):
        """cash_burn_months COMPUTED entry loads correctly."""
        entry = get_field_entry("cash_burn_months")
        assert entry is not None
        assert entry.type == "COMPUTED"
        assert entry.function == "compute_cash_burn_months"
        assert "extracted.financials.earnings_quality" in entry.args

    def test_computed_functions_dict_has_all_expected(self):
        """COMPUTED_FUNCTIONS dict contains all expected function names."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        expected_names = {
            "count_items",
            "count_restatements",
            "count_active_scas",
            "sum_contingent_liabilities",
            "compute_board_independence_pct",
            "resolve_say_on_pay_pct",
            "compute_customer_concentration",
            "compute_cash_burn_months",
        }
        assert expected_names.issubset(set(COMPUTED_FUNCTIONS.keys()))

    def test_computed_functions_all_callable(self):
        """Every entry in COMPUTED_FUNCTIONS is callable."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        for name, func in COMPUTED_FUNCTIONS.items():
            assert callable(func), f"{name} is not callable"

    def test_get_computed_function_lookup(self):
        """get_computed_function returns the correct callable."""
        from do_uw.brain.field_registry import get_computed_function

        func = get_computed_function("count_items")
        assert func is not None
        assert callable(func)
        assert func([1, 2, 3]) == 3

    def test_get_computed_function_unknown_returns_none(self):
        """get_computed_function returns None for unknown name."""
        from do_uw.brain.field_registry import get_computed_function

        assert get_computed_function("nonexistent_function") is None
