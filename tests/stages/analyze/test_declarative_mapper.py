"""Tests for Phase 31 declarative field_key resolution in narrow_result.

Validates the 3-tier resolution order:
1. data_strategy.field_key from check definition
2. FIELD_FOR_CHECK legacy dict
3. Full data dict fallback
"""

from __future__ import annotations

from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK, narrow_result


class TestDeclarativeFieldKey:
    """Test declarative field_key takes priority over legacy FIELD_FOR_CHECK."""

    def test_declarative_field_key_takes_priority(self) -> None:
        """When signal_def has data_strategy.field_key, use it over FIELD_FOR_CHECK."""
        signal_def = {"data_strategy": {"field_key": "x"}}
        data = {"x": 1, "y": 2}
        result = narrow_result("ANY.CHECK.id", data, signal_def=signal_def)
        assert result == {"x": 1}

    def test_fallback_to_field_for_check(self) -> None:
        """When signal_def is None, fall back to FIELD_FOR_CHECK lookup."""
        # Pick a known signal_id from FIELD_FOR_CHECK
        known_id = next(iter(FIELD_FOR_CHECK))
        expected_field = FIELD_FOR_CHECK[known_id]
        data = {expected_field: 42, "other_field": 99}

        result = narrow_result(known_id, data, signal_def=None)
        assert result == {expected_field: 42}

    def test_fallback_to_full_dict(self) -> None:
        """When no signal_def and signal_id not in FIELD_FOR_CHECK, return full dict."""
        data = {"a": 1, "b": 2}
        result = narrow_result("UNKNOWN.CHECK.xyz", data, signal_def=None)
        assert result == {"a": 1, "b": 2}

    def test_declarative_missing_field_returns_empty(self) -> None:
        """When signal_def specifies field_key not in data, return empty dict."""
        signal_def = {"data_strategy": {"field_key": "missing"}}
        data = {"other": 1}
        result = narrow_result("ANY.CHECK.id", data, signal_def=signal_def)
        assert result == {}

    def test_no_data_strategy_falls_through(self) -> None:
        """When signal_def has no data_strategy key, fall through to FIELD_FOR_CHECK."""
        signal_def = {"name": "Some Check"}  # No data_strategy
        # Use a known signal_id from FIELD_FOR_CHECK
        known_id = next(iter(FIELD_FOR_CHECK))
        expected_field = FIELD_FOR_CHECK[known_id]
        data = {expected_field: 42, "other_field": 99}

        result = narrow_result(known_id, data, signal_def=signal_def)
        assert result == {expected_field: 42}
