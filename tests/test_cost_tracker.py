"""Tests for CostTracker budget enforcement and cost recording.

Validates initial state, accumulation, budget limits,
and summary reporting.
"""

from __future__ import annotations

from do_uw.stages.extract.llm.cost_tracker import (
    HAIKU_INPUT_COST,
    HAIKU_OUTPUT_COST,
    CostTracker,
)


def test_initial_state() -> None:
    """Tracker starts at zero with full budget."""
    tracker = CostTracker(budget_usd=1.0)
    assert tracker.total_input_tokens == 0
    assert tracker.total_output_tokens == 0
    assert tracker.total_cost_usd == 0.0
    assert tracker.extraction_count == 0
    assert not tracker.is_over_budget()
    assert tracker.budget_remaining() == 1.0


def test_estimate_cost() -> None:
    """Cost estimate uses Haiku pricing constants."""
    tracker = CostTracker()
    cost = tracker.estimate_cost(
        input_tokens=1_000_000, output_tokens=100_000
    )
    expected = 1_000_000 * HAIKU_INPUT_COST + 100_000 * HAIKU_OUTPUT_COST
    assert abs(cost - expected) < 0.0001
    # 1M input = $1.00, 100k output = $0.50 => $1.50
    assert abs(cost - 1.50) < 0.0001


def test_record_accumulates() -> None:
    """Recording multiple extractions accumulates totals."""
    tracker = CostTracker(budget_usd=10.0)

    cost1 = tracker.record(input_tokens=10000, output_tokens=2000)
    assert cost1 > 0
    assert tracker.extraction_count == 1
    assert tracker.total_input_tokens == 10000
    assert tracker.total_output_tokens == 2000

    cost2 = tracker.record(input_tokens=20000, output_tokens=4000)
    assert cost2 > 0
    assert tracker.extraction_count == 2
    assert tracker.total_input_tokens == 30000
    assert tracker.total_output_tokens == 6000
    assert abs(tracker.total_cost_usd - (cost1 + cost2)) < 0.0001


def test_is_over_budget_triggers() -> None:
    """Budget exceeded after sufficient token usage."""
    tracker = CostTracker(budget_usd=0.001)  # Very small budget

    # Record enough tokens to exceed $0.001
    # 1000 input tokens = $0.001, so right at the boundary
    tracker.record(input_tokens=1000, output_tokens=100)
    # Cost = 1000 * 1e-6 + 100 * 5e-6 = 0.001 + 0.0005 = 0.0015
    assert tracker.is_over_budget()


def test_budget_remaining_decrements() -> None:
    """Remaining budget decreases with each extraction."""
    tracker = CostTracker(budget_usd=1.0)
    assert tracker.budget_remaining() == 1.0

    cost = tracker.record(input_tokens=100000, output_tokens=5000)
    remaining = tracker.budget_remaining()
    assert abs(remaining - (1.0 - cost)) < 0.0001


def test_budget_remaining_floors_at_zero() -> None:
    """Remaining budget never goes negative."""
    tracker = CostTracker(budget_usd=0.001)
    tracker.record(input_tokens=1_000_000, output_tokens=100_000)
    assert tracker.budget_remaining() == 0.0


def test_summary_returns_all_fields() -> None:
    """Summary dict contains all expected keys."""
    tracker = CostTracker(budget_usd=5.0)
    tracker.record(input_tokens=50000, output_tokens=3000)
    tracker.record(input_tokens=30000, output_tokens=2000)

    summary = tracker.summary()
    assert summary["budget_usd"] == 5.0
    assert summary["total_cost_usd"] > 0
    assert summary["budget_remaining_usd"] > 0
    assert summary["total_input_tokens"] == 80000
    assert summary["total_output_tokens"] == 5000
    assert summary["extraction_count"] == 2
    assert summary["average_cost_per_extraction"] > 0
    assert abs(
        summary["average_cost_per_extraction"]
        - summary["total_cost_usd"] / 2
    ) < 0.0001


def test_summary_zero_extractions() -> None:
    """Summary with no extractions has zero average."""
    tracker = CostTracker()
    summary = tracker.summary()
    assert summary["average_cost_per_extraction"] == 0.0
    assert summary["extraction_count"] == 0
