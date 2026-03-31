"""Severity lens protocol for pluggable severity estimation engines.

Defines the SeverityLens Protocol (pluggable interface) mirroring the
ScoringLens pattern from Phase 107. First implementation will be the
damages/settlement/amplifier model in Phase 108.

The legacy DDL model is wrapped as a second lens for comparison.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from do_uw.models.severity import SeverityLensResult

__all__ = [
    "SeverityLens",
    "SeverityLensResult",
]


@runtime_checkable
class SeverityLens(Protocol):
    """Protocol for pluggable severity estimation lenses.

    All severity engines implement this interface to produce a
    SeverityLensResult from signal evaluation results, company data,
    and Liberty layer information.
    """

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
        hae_result: Any | None = None,
    ) -> SeverityLensResult: ...
