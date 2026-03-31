"""Cost tracking for LLM extraction operations.

Tracks input/output tokens and estimated USD cost per extraction,
with per-company rollup. Enforces a configurable budget limit
(default $1.00 per company) to prevent runaway costs.
"""

from __future__ import annotations

import threading
from typing import Any

# Haiku 4.5 pricing (Feb 2026)
HAIKU_INPUT_COST = 1.0 / 1_000_000  # $1.00 per MTok
HAIKU_OUTPUT_COST = 5.0 / 1_000_000  # $5.00 per MTok


class CostTracker:
    """In-memory cost tracker for a single pipeline run.

    Tracks cumulative token usage and estimated cost,
    enforcing a per-company budget limit. Thread-safe
    for use with parallel extraction.
    """

    def __init__(self, budget_usd: float = 1.0) -> None:
        """Initialize cost tracker with budget limit.

        Args:
            budget_usd: Maximum allowed cost in USD (default $1.00).
        """
        self._budget_usd = budget_usd
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.extraction_count: int = 0
        self._lock = threading.Lock()

    def estimate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate USD cost for given token counts.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        return (
            input_tokens * HAIKU_INPUT_COST
            + output_tokens * HAIKU_OUTPUT_COST
        )

    def record(
        self, input_tokens: int, output_tokens: int
    ) -> float:
        """Record an extraction's token usage and cost.

        Thread-safe: uses internal lock for concurrent access.

        Args:
            input_tokens: Number of input tokens used.
            output_tokens: Number of output tokens used.

        Returns:
            Cost in USD for this extraction.
        """
        cost = self.estimate_cost(input_tokens, output_tokens)
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cost_usd += cost
            self.extraction_count += 1
        return cost

    @property
    def budget_usd(self) -> float:
        """Return the configured budget limit in USD."""
        return self._budget_usd

    def budget_remaining(self) -> float:
        """Return remaining budget in USD."""
        return max(0.0, self._budget_usd - self.total_cost_usd)

    def is_over_budget(self) -> bool:
        """Check if cumulative cost exceeds budget. Thread-safe."""
        with self._lock:
            return self.total_cost_usd >= self._budget_usd

    def summary(self) -> dict[str, Any]:
        """Return summary of all cost tracking stats.

        Returns:
            Dict with budget, totals, and per-extraction averages.
        """
        avg_cost = (
            self.total_cost_usd / self.extraction_count
            if self.extraction_count > 0
            else 0.0
        )
        return {
            "budget_usd": self._budget_usd,
            "total_cost_usd": self.total_cost_usd,
            "budget_remaining_usd": self.budget_remaining(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "extraction_count": self.extraction_count,
            "average_cost_per_extraction": avg_cost,
        }
