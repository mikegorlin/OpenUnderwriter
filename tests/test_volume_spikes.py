"""Tests for volume spike detection and signal wiring.

Covers: detect_volume_spikes(), YAML signal upgrade, field routing,
and signal mapper integration.
"""

from __future__ import annotations

from typing import Any

import pytest
import yaml


def _make_history(
    volumes: list[int], closes: list[float] | None = None
) -> dict[str, Any]:
    """Create a yfinance-format dict-of-dicts history fixture."""
    n = len(volumes)
    if closes is None:
        closes = [100.0] * n
    return {
        "Volume": {str(i): v for i, v in enumerate(volumes)},
        "Close": {str(i): c for i, c in enumerate(closes)},
        "Date": {str(i): f"2025-01-{i + 1:02d}" for i in range(n)},
    }


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


class TestDetectVolumeSpikes:
    """Tests for the core detect_volume_spikes() function."""

    def test_detect_no_spikes(self) -> None:
        """Uniform volume (all 1M shares) produces 0 spikes."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 0

    def test_detect_single_spike(self) -> None:
        """One day at 3M in a sea of 1M produces 1 spike with volume_multiple >= 2.0."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        volumes[25] = 3_000_000  # Day 25 is a spike
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 1
        assert spikes[0]["volume"] == 3_000_000
        assert spikes[0]["volume_multiple"] >= 2.0

    def test_detect_multiple_spikes(self) -> None:
        """3 spike days produces 3 events."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        volumes[25] = 3_000_000
        volumes[35] = 4_000_000
        volumes[45] = 5_000_000
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 3

    def test_insufficient_history(self) -> None:
        """History shorter than lookback returns empty list."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 15  # Less than 20 + 1
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert spikes == []

    def test_empty_history(self) -> None:
        """Empty dict returns empty list."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        spikes = detect_volume_spikes({})
        assert spikes == []

    def test_spike_includes_price_change(self) -> None:
        """Spike event includes price_change_pct when close data available."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        closes = [100.0] * 50
        volumes[25] = 5_000_000
        closes[24] = 100.0
        closes[25] = 110.0  # 10% increase
        history = _make_history(volumes, closes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 1
        assert spikes[0]["price_change_pct"] == 10.0

    def test_spike_event_structure(self) -> None:
        """Each spike has date, volume, avg_volume, volume_multiple, price_change_pct."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        volumes[30] = 5_000_000
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 1
        spike = spikes[0]
        assert "date" in spike
        assert "volume" in spike
        assert "avg_volume" in spike
        assert "volume_multiple" in spike
        assert "price_change_pct" in spike

    def test_threshold_boundary(self) -> None:
        """Volume at exactly 2x average counts as a spike (>= threshold)."""
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        volumes = [1_000_000] * 50
        volumes[30] = 2_000_000  # Exactly 2x
        history = _make_history(volumes)
        spikes = detect_volume_spikes(history)
        assert len(spikes) == 1
        assert spikes[0]["volume_multiple"] == 2.0


# ---------------------------------------------------------------------------
# Signal wiring tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Correlation tests
# ---------------------------------------------------------------------------


class TestCorrelateVolumeSpikes:
    """Tests for spike event correlation via web search."""

    def test_correlate_adds_catalyst(self) -> None:
        """Mock search_fn returns results, catalyst field is populated."""
        from do_uw.stages.acquire.spike_correlator import correlate_volume_spikes

        def mock_search(q: str) -> list[dict[str, str]]:
            return [{"title": "Earnings Beat", "description": "Q3 results exceeded expectations"}]

        spikes = [
            {"date": "2025-07-15", "volume": 5_000_000, "volume_multiple": 3.5, "price_change_pct": 8.2},
            {"date": "2025-09-10", "volume": 4_000_000, "volume_multiple": 2.8, "price_change_pct": -5.1},
        ]
        result = correlate_volume_spikes(spikes, "Snap-on Inc", "SNA", mock_search)
        assert len(result) == 2
        assert result[0]["catalyst"] is not None
        assert "Earnings Beat" in result[0]["catalyst"]

    def test_correlate_budget_limit(self) -> None:
        """With 10 spikes and max_searches=5, only top 5 by volume_multiple are searched."""
        from do_uw.stages.acquire.spike_correlator import correlate_volume_spikes

        search_count = 0

        def counting_search(q: str) -> list[dict[str, str]]:
            nonlocal search_count
            search_count += 1
            return [{"title": f"Result {search_count}"}]

        spikes = [
            {"date": f"2025-01-{i+1:02d}", "volume": 1_000_000 * (i + 1), "volume_multiple": float(i + 1)}
            for i in range(10)
        ]
        correlate_volume_spikes(spikes, "Test Corp", "TST", counting_search, max_searches=5)
        assert search_count == 5
        # Spikes not searched should have catalyst=None
        none_count = sum(1 for s in spikes if s.get("catalyst") is None)
        assert none_count == 5

    def test_correlate_empty_results(self) -> None:
        """Search returns empty list, catalyst is None (not error)."""
        from do_uw.stages.acquire.spike_correlator import correlate_volume_spikes

        def empty_search(q: str) -> list[dict[str, str]]:
            return []

        spikes = [{"date": "2025-03-01", "volume": 3_000_000, "volume_multiple": 3.0}]
        result = correlate_volume_spikes(spikes, "Test Corp", "TST", empty_search)
        assert result[0]["catalyst"] is None

    def test_correlate_search_failure(self) -> None:
        """Search_fn raises exception, catalyst is None, no crash."""
        from do_uw.stages.acquire.spike_correlator import correlate_volume_spikes

        def failing_search(q: str) -> list[dict[str, str]]:
            raise ConnectionError("Network error")

        spikes = [{"date": "2025-04-01", "volume": 4_000_000, "volume_multiple": 4.0}]
        result = correlate_volume_spikes(spikes, "Test Corp", "TST", failing_search)
        assert result[0]["catalyst"] is None

    def test_extract_catalyst_picks_first_result(self) -> None:
        """_extract_catalyst returns first result title."""
        from do_uw.stages.acquire.spike_correlator import _extract_catalyst

        results = [
            {"title": "First Result", "description": "First desc"},
            {"title": "Second Result", "description": "Second desc"},
        ]
        catalyst = _extract_catalyst(results)
        assert catalyst is not None
        assert "First Result" in catalyst


# ---------------------------------------------------------------------------
# Signal wiring tests
# ---------------------------------------------------------------------------


class TestSignalWiring:
    """Tests for YAML, field routing, and mapper integration."""

    def test_signal_yaml_tiered(self) -> None:
        """STOCK.TRADE.volume_patterns has threshold.type=tiered and correct field_key."""
        yaml_path = "src/do_uw/brain/signals/stock/insider.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        vp = [s for s in data if s["id"] == "STOCK.TRADE.volume_patterns"]
        assert len(vp) == 1
        signal = vp[0]
        assert signal["threshold"]["type"] == "tiered"
        assert signal["data_strategy"]["field_key"] == "volume_spike_count"
        assert signal["work_type"] == "evaluate"
        assert "volume" in signal["data_locations"]["MARKET_PRICE"]

    def test_field_routing_updated(self) -> None:
        """FIELD_FOR_CHECK maps STOCK.TRADE.volume_patterns to volume_spike_count."""
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        assert FIELD_FOR_CHECK["STOCK.TRADE.volume_patterns"] == "volume_spike_count"
