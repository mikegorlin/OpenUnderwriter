"""Data acquisition client protocol and exports.

All data clients implement the DataClient protocol, which provides
a uniform interface for the ACQUIRE stage orchestrator.
"""

from __future__ import annotations

from typing import Any, Protocol

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.state import AnalysisState


class DataClient(Protocol):
    """Protocol for all data acquisition clients.

    Each client acquires raw data from a specific source category
    (SEC filings, market data, litigation, news, etc.) and returns
    it as a dict for storage in AcquiredData.
    """

    @property
    def name(self) -> str:
        """Human-readable client name for logging."""
        ...

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire raw data for the given analysis state.

        Args:
            state: Current analysis state with resolved company identity.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict of raw data to store in AcquiredData.
        """
        ...


__all__ = ["DataClient"]
