"""Tests for html_signals.py -- signal grouping and coverage stats.

Phase 84-03: Validates manifest-driven signal grouping and facet metadata.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.stages.render.html_signals import (
    _build_signal_section_map,
    _compute_coverage_stats,
    _group_signals_by_section,
    _lookup_facet_metadata,
    _reset_caches,
)


@pytest.fixture(autouse=True)
def _clear_caches() -> None:  # type: ignore[return]
    """Reset module-level caches before each test."""
    _reset_caches()
    yield
    _reset_caches()


class TestBuildSignalSectionMap:
    """_build_signal_section_map() returns correct signal-to-prefix mapping."""

    def test_returns_two_dicts(self) -> None:
        signal_to_prefix, prefix_to_name = _build_signal_section_map()
        assert isinstance(signal_to_prefix, dict)
        assert isinstance(prefix_to_name, dict)

    def test_maps_signals_to_prefix(self) -> None:
        """Known signals map to their expected prefixes."""
        signal_to_prefix, _ = _build_signal_section_map()
        # BIZ.COMP.market_position -> BIZ
        assert signal_to_prefix.get("BIZ.COMP.market_position") == "BIZ"
        # FIN.ACCT.auditor -> FIN
        assert signal_to_prefix.get("FIN.ACCT.auditor") == "FIN"

    def test_prefix_to_name_has_known_sections(self) -> None:
        """prefix_to_name maps prefixes to manifest section names."""
        _, prefix_to_name = _build_signal_section_map()
        # Should have well-known prefixes
        assert "BIZ" in prefix_to_name
        assert "FIN" in prefix_to_name
        assert "GOV" in prefix_to_name

    def test_prefix_names_are_display_names(self) -> None:
        """Section names are human-readable, not IDs."""
        _, prefix_to_name = _build_signal_section_map()
        # Names should have spaces and proper casing
        for name in prefix_to_name.values():
            assert name, "Section name should not be empty"
            # At least some names should have spaces (multi-word)
            assert any(" " in n for n in prefix_to_name.values())
            break

    def test_significant_signal_coverage(self) -> None:
        """Most signals have prefix mappings."""
        signal_to_prefix, _ = _build_signal_section_map()
        assert len(signal_to_prefix) > 300, (
            f"Expected 300+ signal mappings, got {len(signal_to_prefix)}"
        )

    def test_caching_returns_same_objects(self) -> None:
        """Subsequent calls return cached results."""
        result1 = _build_signal_section_map()
        result2 = _build_signal_section_map()
        assert result1[0] is result2[0]
        assert result1[1] is result2[1]


class TestLookupFacetMetadata:
    """_lookup_facet_metadata() returns group metadata for signals."""

    def test_known_signal_returns_metadata(self) -> None:
        meta = _lookup_facet_metadata("FIN.ACCT.auditor")
        assert meta["facet_id"], "facet_id should not be empty for known signal"
        assert meta["facet_name"], "facet_name should not be empty for known signal"

    def test_unknown_signal_returns_empty(self) -> None:
        meta = _lookup_facet_metadata("NONEXISTENT.signal_999")
        assert meta == {"facet_id": "", "facet_name": ""}

    def test_returns_dict_with_expected_keys(self) -> None:
        meta = _lookup_facet_metadata("BIZ.COMP.market_position")
        assert "facet_id" in meta
        assert "facet_name" in meta


class TestGroupSignalsBySection:
    """_group_signals_by_section() groups signals by prefix."""

    def _make_signal_results(self) -> dict[str, Any]:
        return {
            "BIZ.company_description": {
                "value": "Test company",
                "status": "INFO",
                "signal_name": "company_description",
                "source": "10-K",
                "confidence": "HIGH",
                "data_status": "EVALUATED",
            },
            "FIN.current_ratio": {
                "value": 2.5,
                "status": "PASS",
                "signal_name": "current_ratio",
                "source": "XBRL",
                "confidence": "HIGH",
                "data_status": "EVALUATED",
            },
            "FIN.debt_to_equity": {
                "value": 0.8,
                "status": "PASS",
                "signal_name": "debt_to_equity",
                "source": "XBRL",
                "confidence": "HIGH",
                "data_status": "EVALUATED",
            },
        }

    def test_groups_by_prefix(self) -> None:
        results = self._make_signal_results()
        grouped = _group_signals_by_section(results)
        assert "BIZ" in grouped
        assert "FIN" in grouped
        assert len(grouped["BIZ"]) == 1
        assert len(grouped["FIN"]) == 2

    def test_grouped_entry_has_required_keys(self) -> None:
        results = self._make_signal_results()
        grouped = _group_signals_by_section(results)
        required_keys = {
            "signal_id", "signal_name", "status", "value", "evidence",
            "content_type", "source", "confidence", "data_status",
            "data_status_reason", "factors", "filing_ref",
            "trace_data_source", "facet_id", "facet_name",
        }
        for prefix_signals in grouped.values():
            for entry in prefix_signals:
                assert required_keys.issubset(set(entry.keys()))

    def test_skips_non_dict_results(self) -> None:
        results: dict[str, Any] = {
            "BIZ.test": {"value": 1, "status": "INFO"},
            "bad_entry": "not a dict",
        }
        grouped = _group_signals_by_section(results)
        # Should only include the dict entry
        total = sum(len(v) for v in grouped.values())
        assert total == 1

    def test_fallback_prefix_for_unknown_signals(self) -> None:
        results: dict[str, Any] = {
            "UNKNOWN.signal": {"value": 1, "status": "INFO"},
        }
        grouped = _group_signals_by_section(results)
        assert "UNKNOWN" in grouped


class TestComputeCoverageStats:
    """_compute_coverage_stats() produces coverage statistics."""

    def test_basic_coverage(self) -> None:
        results: dict[str, Any] = {
            "BIZ.test1": {"status": "PASS", "data_status": "EVALUATED"},
            "BIZ.test2": {"status": "SKIPPED", "data_status": "DATA_UNAVAILABLE"},
            "FIN.test1": {"status": "PASS", "data_status": "EVALUATED"},
        }
        overall, per_section = _compute_coverage_stats(results)
        assert overall["total"] == 3
        assert overall["evaluated"] == 2
        assert overall["skipped"] == 1

    def test_empty_results(self) -> None:
        overall, per_section = _compute_coverage_stats({})
        assert overall["total"] == 0
        assert overall["coverage_pct"] == "0"

    def test_per_section_has_coverage_pct(self) -> None:
        results: dict[str, Any] = {
            "BIZ.test1": {"status": "PASS", "data_status": "EVALUATED"},
        }
        _, per_section = _compute_coverage_stats(results)
        for stats in per_section.values():
            assert "coverage_pct" in stats
