"""Integration tests for signal execution ordering in signal_engine.

Phase 83-01: Verifies that execute_signals() applies tier-based
topological ordering before the chunk loop processes signals.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.brain.dependency_graph import order_signals_for_execution


def _make_signal(
    signal_id: str,
    signal_class: str = "evaluative",
    deps: list[str] | None = None,
    execution_mode: str = "AUTO",
    threshold_type: str = "info",
) -> dict[str, Any]:
    """Build a minimal signal dict for execution testing."""
    sig: dict[str, Any] = {
        "id": signal_id,
        "name": f"Test {signal_id}",
        "signal_class": signal_class,
        "content_type": "EVALUATIVE_CHECK",
        "section": 3,
        "factors": [],
        "threshold": {"type": threshold_type},
        "execution_mode": execution_mode,
        "required_data": [],
        "data_locations": {},
        "depends_on": [],
    }
    if deps:
        sig["depends_on"] = [{"signal": d, "field": ""} for d in deps]
    return sig


class TestExecutionOrderTiers:
    """Verify tier ordering: foundational -> evaluative -> inference."""

    def test_execution_order_tiers(self) -> None:
        """Foundational signals appear before evaluative before inference after ordering."""
        signals = [
            _make_signal("INF.1", signal_class="inference"),
            _make_signal("EVAL.1", signal_class="evaluative"),
            _make_signal("FOUND.1", signal_class="foundational"),
            _make_signal("EVAL.2", signal_class="evaluative"),
        ]
        ordered = order_signals_for_execution(signals)
        ids = [s["id"] for s in ordered]

        # Foundational first
        assert ids.index("FOUND.1") < ids.index("EVAL.1")
        assert ids.index("FOUND.1") < ids.index("EVAL.2")
        # Evaluative before inference
        assert ids.index("EVAL.1") < ids.index("INF.1")
        assert ids.index("EVAL.2") < ids.index("INF.1")


class TestExecutionOrderWithinTier:
    """Verify within-tier topological ordering."""

    def test_execution_order_within_tier(self) -> None:
        """Two evaluative signals where B depends on A: A appears first."""
        signals = [
            _make_signal("EVAL.B", deps=["EVAL.A"]),
            _make_signal("EVAL.A"),
        ]
        ordered = order_signals_for_execution(signals)
        ids = [s["id"] for s in ordered]
        assert ids.index("EVAL.A") < ids.index("EVAL.B")


class TestExecutionOrderNoRegression:
    """Verify ordering does not lose or duplicate signals."""

    def test_execution_order_no_regression(self) -> None:
        """All signals are preserved after ordering (no loss, no duplication)."""
        signals = [
            _make_signal(f"SIG.{i}") for i in range(20)
        ]
        ordered = order_signals_for_execution(signals)
        input_ids = {s["id"] for s in signals}
        output_ids = {s["id"] for s in ordered}
        assert input_ids == output_ids
        assert len(ordered) == len(signals)

    def test_execute_signals_calls_ordering(self) -> None:
        """execute_signals applies order_signals_for_execution before processing."""
        from do_uw.stages.analyze.signal_engine import execute_signals

        # Create a minimal ExtractedData mock
        extracted = MagicMock()
        extracted.financials = MagicMock()

        signals = [
            _make_signal("EVAL.X", threshold_type="info"),
        ]

        with patch(
            "do_uw.brain.dependency_graph.order_signals_for_execution",
            wraps=order_signals_for_execution,
        ) as mock_order:
            # Just verify order_signals_for_execution is called
            # We don't need to run full evaluation
            try:
                execute_signals(signals, extracted)
            except Exception:
                pass  # Evaluation may fail with mock data, that's OK
            mock_order.assert_called_once()
