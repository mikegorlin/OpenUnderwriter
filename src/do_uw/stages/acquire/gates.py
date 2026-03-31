"""Acquisition completeness gate system.

Defines HARD gates (must pass to proceed) and SOFT gates (warn but
continue) that validate data completeness after the ACQUIRE stage.

Gate definitions per user's locked decisions:
- 3 HARD gates: annual_report, quarterly_report, market_data
- 3 SOFT gates: proxy_statement (recent IPOs may lack DEF 14A), litigation, news_sentiment

Note: 8-K and Form 4 filings ARE acquired by SECFilingClient but are
NOT separately gated. They are supplementary data that enriches analysis.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from do_uw.models.state import AcquiredData


class GateType(StrEnum):
    """Acquisition gate severity level."""

    HARD = "HARD"
    SOFT = "SOFT"


@dataclass(frozen=True)
class GateResult:
    """Result of evaluating a single acquisition gate."""

    gate_name: str
    gate_type: GateType
    passed: bool
    message: str


@dataclass(frozen=True)
class AcquisitionGate:
    """Definition of a single acquisition completeness gate.

    Attributes:
        name: Human-readable gate name.
        gate_type: HARD (halt) or SOFT (warn).
        check_fn: Callable that returns True if gate passes.
        description: Explanation of what this gate validates.
    """

    name: str
    gate_type: GateType
    check_fn: Callable[[AcquiredData], bool]
    description: str


def _has_annual_report(data: AcquiredData) -> bool:
    """Check for 10-K or 20-F filings."""
    return bool(data.filings.get("10-K") or data.filings.get("20-F"))


def _has_quarterly_report(data: AcquiredData) -> bool:
    """Check for 10-Q or 6-K filings."""
    return bool(data.filings.get("10-Q") or data.filings.get("6-K"))


def _has_proxy_statement(data: AcquiredData) -> bool:
    """Check for DEF 14A or DEF14A proxy statement."""
    return bool(
        data.filings.get("DEF 14A") or data.filings.get("DEF14A")
    )


def _has_market_data(data: AcquiredData) -> bool:
    """Check for non-empty market data."""
    return bool(data.market_data)


def _has_litigation_data(data: AcquiredData) -> bool:
    """Check for non-empty litigation data."""
    return bool(data.litigation_data)


def _has_news_sentiment(data: AcquiredData) -> bool:
    """Check for non-empty web search results."""
    return bool(data.web_search_results)


ACQUISITION_GATES: list[AcquisitionGate] = [
    AcquisitionGate(
        name="annual_report",
        gate_type=GateType.HARD,
        check_fn=_has_annual_report,
        description="Annual report (10-K or 20-F) required for analysis",
    ),
    AcquisitionGate(
        name="quarterly_report",
        gate_type=GateType.HARD,
        check_fn=_has_quarterly_report,
        description="Quarterly report (10-Q or 6-K) required for analysis",
    ),
    AcquisitionGate(
        name="proxy_statement",
        gate_type=GateType.SOFT,
        check_fn=_has_proxy_statement,
        description="Proxy statement (DEF 14A) recommended for governance analysis (recent IPOs may not have one yet)",
    ),
    AcquisitionGate(
        name="market_data",
        gate_type=GateType.HARD,
        check_fn=_has_market_data,
        description="Stock/market data required for pricing analysis",
    ),
    AcquisitionGate(
        name="litigation",
        gate_type=GateType.SOFT,
        check_fn=_has_litigation_data,
        description="Litigation data recommended for risk assessment",
    ),
    AcquisitionGate(
        name="news_sentiment",
        gate_type=GateType.SOFT,
        check_fn=_has_news_sentiment,
        description="News/sentiment data recommended for current risk signals",
    ),
]


def check_gates(
    data: AcquiredData,
    gates: list[AcquisitionGate] | None = None,
) -> list[GateResult]:
    """Run all acquisition gates and return results.

    Args:
        data: Acquired data to validate.
        gates: Gate definitions to check. Defaults to ACQUISITION_GATES.

    Returns:
        List of GateResult for each gate evaluated.
    """
    gate_list = gates if gates is not None else ACQUISITION_GATES
    results: list[GateResult] = []
    for gate in gate_list:
        passed = gate.check_fn(data)
        message = (
            f"{gate.name}: passed"
            if passed
            else f"{gate.name}: FAILED - {gate.description}"
        )
        results.append(
            GateResult(
                gate_name=gate.name,
                gate_type=gate.gate_type,
                passed=passed,
                message=message,
            )
        )
    return results
