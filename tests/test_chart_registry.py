"""Tests for chart type registry — declarative catalog of all charts.

Tests loading, validation, function resolution, and filtering of chart_registry.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml


# ---- Task 1 Tests: YAML registry structure ----

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "brain" / "config" / "chart_registry.yaml"

EXPECTED_IDS = [
    "stock_1y", "stock_5y",
    "drawdown_1y", "drawdown_5y",
    "volatility_1y", "volatility_5y",
    "relative_1y", "relative_5y",
    "drop_analysis_1y", "drop_analysis_5y",
    "drop_scatter_1y", "drop_scatter_5y",
    "radar", "ownership", "timeline",
]

REQUIRED_FIELDS = {"id", "name", "module", "function", "formats", "data_requires"}


class TestRegistryYAML:
    """Test 1-3: YAML is valid, all charts present, required fields exist."""

    def test_yaml_is_valid_and_loadable(self) -> None:
        """Test 1: YAML file exists and is loadable."""
        assert REGISTRY_PATH.exists(), f"chart_registry.yaml not found at {REGISTRY_PATH}"
        data = yaml.safe_load(REGISTRY_PATH.read_text())
        charts = data if isinstance(data, list) else data.get("charts", [])
        assert len(charts) > 0, "Registry has no chart entries"

    def test_all_expected_charts_present(self) -> None:
        """Test 2: Every chart key currently in _generate_chart_svgs has a registry entry."""
        data = yaml.safe_load(REGISTRY_PATH.read_text())
        charts = data if isinstance(data, list) else data.get("charts", [])
        ids = [c["id"] for c in charts]
        missing = [eid for eid in EXPECTED_IDS if eid not in ids]
        assert not missing, f"Missing chart entries: {missing}"

    def test_each_entry_has_required_fields(self) -> None:
        """Test 3: Each entry has required fields: id, name, module, function, formats, data_requires."""
        data = yaml.safe_load(REGISTRY_PATH.read_text())
        charts = data if isinstance(data, list) else data.get("charts", [])
        for chart in charts:
            for field in REQUIRED_FIELDS:
                assert field in chart, f"Chart '{chart.get('id', '?')}' missing required field '{field}'"


# ---- Task 2 Tests: Loader, validator, function resolution ----

from do_uw.stages.render.chart_registry import (
    ChartEntry,
    get_charts_for_format,
    get_charts_for_section,
    load_chart_registry,
    resolve_chart_fn,
)


class TestLoadChartRegistry:
    """Test 1: load_chart_registry() returns list of ChartEntry."""

    def test_returns_list_of_chart_entry(self) -> None:
        entries = load_chart_registry()
        assert isinstance(entries, list)
        assert len(entries) == 16
        for entry in entries:
            assert isinstance(entry, ChartEntry)

    def test_chart_entry_fields_populated(self) -> None:
        """Test 2: Each ChartEntry has typed fields."""
        entries = load_chart_registry()
        for entry in entries:
            assert isinstance(entry.id, str) and entry.id
            assert isinstance(entry.name, str) and entry.name
            assert isinstance(entry.module, str) and entry.module
            assert isinstance(entry.function, str) and entry.function
            assert isinstance(entry.formats, list) and len(entry.formats) > 0
            assert isinstance(entry.data_requires, list) and len(entry.data_requires) > 0


class TestResolveChartFn:
    """Test 3: resolve_chart_fn returns a callable for each entry."""

    def test_all_entries_resolvable(self) -> None:
        entries = load_chart_registry()
        for entry in entries:
            fn = resolve_chart_fn(entry)
            assert callable(fn), f"resolve_chart_fn({entry.id}) did not return callable"

    def test_resolve_returns_correct_function(self) -> None:
        entries = load_chart_registry()
        stock_entry = next(e for e in entries if e.id == "stock_1y")
        fn = resolve_chart_fn(stock_entry)
        assert fn.__name__ == "create_stock_chart"


class TestSectionFiltering:
    """Test 4: get_charts_for_section returns correct subsets, sorted by position."""

    def test_stock_charts_section(self) -> None:
        entries = get_charts_for_section("stock_charts")
        assert len(entries) == 12  # 2 stock + 2 drop_analysis + 2 drawdown + 2 scatter + 2 volatility + 2 relative
        positions = [e.position for e in entries]
        assert positions == sorted(positions), "stock_charts not sorted by position"

    def test_scoring_section(self) -> None:
        entries = get_charts_for_section("scoring")
        assert len(entries) == 1
        assert entries[0].id == "radar"

    def test_empty_section(self) -> None:
        entries = get_charts_for_section("nonexistent_section")
        assert entries == []


class TestFormatFiltering:
    """Test 5: get_charts_for_format returns entries with that format."""

    def test_html_format_returns_all(self) -> None:
        entries = get_charts_for_format("html")
        assert len(entries) == 16  # All charts support html

    def test_pdf_format_returns_all(self) -> None:
        entries = get_charts_for_format("pdf")
        assert len(entries) == 16  # All charts support pdf

    def test_unknown_format_returns_empty(self) -> None:
        entries = get_charts_for_format("docx")
        assert entries == []


class TestValidation:
    """Test 6: Validation rejects entries missing required fields."""

    def test_missing_field_raises_value_error(self) -> None:
        bad_yaml: dict[str, Any] = {
            "charts": [
                {
                    "id": "test_chart",
                    "name": "Test",
                    # missing module, function, formats, data_requires
                }
            ]
        }
        with patch("do_uw.stages.render.chart_registry._load_yaml", return_value=bad_yaml):
            # Clear cache so it reloads
            import do_uw.stages.render.chart_registry as mod
            mod._cache = None
            with pytest.raises(ValueError, match="missing required field"):
                load_chart_registry()
            # Reset cache for other tests
            mod._cache = None
