"""Tests for the generic YAML-driven signal field resolver.

Verifies that resolve_signal_data() resolves data from YAML field
declarations against state, supporting direct paths, computed_from,
fallback_paths, field_path, and data_strategy.field_key.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


class _Obj:
    """Simple namespace object for building mock state trees."""
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class _SV:
    """Mock SourcedValue with .value and .source attributes."""
    def __init__(self, value: Any, source: str = "test") -> None:
        self.value = value
        self.source = source
        self.confidence = "HIGH"


def _make_mock_state() -> Any:
    """Build a mock AnalysisState with realistic nested structure.

    Uses _Obj (plain namespace) for non-SourcedValue nodes and _SV for
    SourcedValue leaves. Avoids MagicMock which auto-creates .value/.source.
    """
    state = _Obj(
        extracted=_Obj(
            governance=_Obj(
                board_composition=_Obj(
                    size=11,
                    nonexistent=None,
                ),
            ),
            financials=_Obj(
                statements=_Obj(revenue=None),
                liquidity=_SV({"current_ratio": 1.8, "quick_ratio": 1.2}, "SEC_10K"),
            ),
            market=_Obj(
                stock=_Obj(
                    volatility_90d=_SV(0.35, "yfinance"),
                ),
            ),
        ),
        analysis=_Obj(
            xbrl_forensics=_Obj(
                beneish=_Obj(composite_score=-2.5),
            ),
        ),
        company=_Obj(
            market_cap=_SV(5_000_000_000, "yfinance"),
            financials=_Obj(
                revenue=_SV(50_000_000, "XBRL"),
            ),
        ),
        benchmark=_Obj(),
    )
    return state


class TestResolveSignalData:
    """Tests for the resolve_signal_data function."""

    def test_direct_path_resolves(self) -> None:
        """Test: resolve_signal_data with direct path returns correct value."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "GOV.BOARD.size",
            "acquisition": {
                "sources": [{
                    "fields": [{
                        "name": "board_size",
                        "path": "extracted.governance.board_composition.size",
                    }]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        assert result.get("board_size") == 11

    def test_computed_from_resolves(self) -> None:
        """Test: resolve_signal_data with computed_from returns correct value."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "FIN.FORENSIC.m_score_composite",
            "acquisition": {
                "sources": [{
                    "fields": [{
                        "name": "beneish_score",
                        "computed_from": "analysis.xbrl_forensics.beneish.composite_score",
                    }]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        assert result.get("beneish_score") == -2.5

    def test_fallback_paths_first_none_second_resolves(self) -> None:
        """Test: resolve_signal_data with fallback_paths tries each in order."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "FIN.PROFIT.revenue",
            "acquisition": {
                "sources": [{
                    "fields": [{
                        "name": "revenue",
                        "path": "extracted.financials.statements.revenue",
                        "fallback_paths": [
                            "company.financials.revenue",
                        ],
                    }]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        # Should fall back to company.financials.revenue (SourcedValue unwrapped)
        assert result.get("revenue") == 50_000_000

    def test_sourced_value_unwrapped(self) -> None:
        """Test: resolve_signal_data with SourcedValue unwraps to raw value."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "BIZ.SIZE.market_cap",
            "acquisition": {
                "sources": [{
                    "fields": [{
                        "name": "market_cap",
                        "path": "company.market_cap",
                    }]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        assert result.get("market_cap") == 5_000_000_000

    def test_field_path_legacy_resolves(self) -> None:
        """Test: resolve_signal_data with field_path (legacy) resolves correctly."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "GOV.BOARD.size",
            "field_path": "extracted.governance.board_composition.size",
        }
        result = resolve_signal_data(sig, state)
        # For field_path, the key should be the last path segment
        assert "board_composition.size" in str(result) or result.get("size") == 11 or 11 in result.values()

    def test_data_strategy_field_key_resolves(self) -> None:
        """Test: resolve_signal_data with data_strategy.field_key resolves correctly."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "STOCK.PRICE.technical",
            "data_strategy": {
                "field_key": "extracted.market.stock.volatility_90d",
            },
        }
        result = resolve_signal_data(sig, state)
        assert 0.35 in result.values()

    def test_empty_dict_when_all_paths_none(self) -> None:
        """Test: resolve_signal_data returns empty dict when all paths resolve to None."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "GOV.BOARD.nonexistent",
            "acquisition": {
                "sources": [{
                    "fields": [{
                        "name": "nonexistent_field",
                        "path": "extracted.governance.board_composition.nonexistent",
                    }]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        assert result == {}

    def test_multiple_fields_in_single_source(self) -> None:
        """Test: resolve_signal_data resolves multiple fields from one source."""
        from do_uw.stages.analyze.signal_resolver import resolve_signal_data

        state = _make_mock_state()
        sig: dict[str, Any] = {
            "id": "TEST.multi",
            "acquisition": {
                "sources": [{
                    "fields": [
                        {
                            "name": "board_size",
                            "path": "extracted.governance.board_composition.size",
                        },
                        {
                            "name": "market_cap",
                            "path": "company.market_cap",
                        },
                    ]
                }]
            },
        }
        result = resolve_signal_data(sig, state)
        assert result.get("board_size") == 11
        assert result.get("market_cap") == 5_000_000_000


class TestResolvePath:
    """Tests for the _resolve_path internal function."""

    def test_dict_access(self) -> None:
        """Test: _resolve_path handles dict access."""
        from do_uw.stages.analyze.signal_resolver import _resolve_path

        obj = {"level1": {"level2": 42}}
        assert _resolve_path(obj, "level1.level2") == 42

    def test_attribute_access(self) -> None:
        """Test: _resolve_path handles attribute access."""
        from do_uw.stages.analyze.signal_resolver import _resolve_path

        obj = _Obj(level1=_Obj(level2="hello"))
        assert _resolve_path(obj, "level1.level2") == "hello"

    def test_none_returns_none(self) -> None:
        """Test: _resolve_path returns None for missing paths."""
        from do_uw.stages.analyze.signal_resolver import _resolve_path

        obj = {"level1": None}
        assert _resolve_path(obj, "level1.level2") is None

    def test_sourced_value_unwrap(self) -> None:
        """Test: _resolve_path unwraps SourcedValue at each level."""
        from do_uw.stages.analyze.signal_resolver import _resolve_path

        sv = _SV(42, "test")
        obj = _Obj(field=sv)
        assert _resolve_path(obj, "field") == 42
