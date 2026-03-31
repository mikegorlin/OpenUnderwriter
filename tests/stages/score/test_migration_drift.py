"""Tests for MigrationDriftEngine.

TDD tests for the Migration Drift pattern engine that detects
cross-domain gradual deterioration from quarterly XBRL data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.common import SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements
from do_uw.stages.score.migration_drift import MigrationDriftEngine

_NOW = datetime.now(tz=UTC)


def _make_quarterly_period(
    fy: int,
    fq: int,
    income: dict[str, float] | None = None,
    balance: dict[str, float] | None = None,
) -> QuarterlyPeriod:
    """Create a QuarterlyPeriod with SourcedValue-wrapped metrics."""
    inc: dict[str, SourcedValue[float]] = {}
    if income:
        for k, v in income.items():
            inc[k] = SourcedValue(
                value=v, source="test", confidence="HIGH", as_of=_NOW
            )
    bal: dict[str, SourcedValue[float]] = {}
    if balance:
        for k, v in balance.items():
            bal[k] = SourcedValue(
                value=v, source="test", confidence="HIGH", as_of=_NOW
            )
    return QuarterlyPeriod(
        fiscal_year=fy,
        fiscal_quarter=fq,
        fiscal_label=f"Q{fq} FY{fy}",
        calendar_period=f"CY{fy}Q{fq}",
        period_end=f"{fy}-{fq * 3:02d}-28",
        income=inc,
        balance=bal,
    )


def _make_state(
    quarters: list[QuarterlyPeriod] | None = None,
) -> MagicMock:
    """Create a mock AnalysisState with quarterly XBRL data."""
    state = MagicMock()
    if quarters is not None:
        state.extracted.financials.quarterly_xbrl = QuarterlyStatements(
            quarters=quarters
        )
    else:
        state.extracted.financials.quarterly_xbrl = None
    return state


class TestMigrationDriftFires:
    """Tests where the engine should fire."""

    def test_8_quarters_two_rap_categories_declining(self) -> None:
        """8 quarters with declining revenue (agent) and assets (host) => fired."""
        # Revenue declining 10% per quarter (agent metrics)
        # Total assets declining 5% per quarter (host metrics)
        quarters = []
        base_revenue = 1000.0
        base_assets = 5000.0
        for i in range(8):
            fy = 2023 + (i // 4)
            fq = (i % 4) + 1
            quarters.append(
                _make_quarterly_period(
                    fy=fy,
                    fq=fq,
                    income={"Revenues": base_revenue * (0.90 ** i)},
                    balance={"Assets": base_assets * (0.95 ** i)},
                )
            )
        # Reverse so most recent is first (matches QuarterlyStatements spec)
        quarters.reverse()
        state = _make_state(quarters)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is True
        assert result.confidence > 0.0
        assert "drift" in result.headline.lower() or "deterioration" in result.headline.lower()

    def test_mixed_trends_2_categories_declining(self) -> None:
        """Mixed trends: some improving, 2+ RAP categories declining => fired."""
        quarters = []
        for i in range(8):
            fy = 2023 + (i // 4)
            fq = (i % 4) + 1
            quarters.append(
                _make_quarterly_period(
                    fy=fy,
                    fq=fq,
                    income={
                        "Revenues": 1000 * (0.90 ** i),  # declining (agent)
                        "NetIncomeLoss": 100 * (1.05 ** i),  # improving
                    },
                    balance={
                        "Assets": 5000 * (0.93 ** i),  # declining (host)
                        "StockholdersEquity": 2000 * (1.02 ** i),  # improving
                    },
                )
            )
        quarters.reverse()
        state = _make_state(quarters)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is True


class TestMigrationDriftDoesNotFire:
    """Tests where the engine should NOT fire."""

    def test_fewer_than_4_quarters(self) -> None:
        """< 4 quarters of data => NOT_FIRED."""
        quarters = [
            _make_quarterly_period(
                2024, q, income={"Revenues": 1000 * (0.90 ** q)}
            )
            for q in range(1, 4)
        ]
        quarters.reverse()
        state = _make_state(quarters)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False
        assert "insufficient" in result.headline.lower()

    def test_no_declining_metrics(self) -> None:
        """All metrics stable or improving => NOT_FIRED."""
        quarters = []
        for i in range(8):
            fy = 2023 + (i // 4)
            fq = (i % 4) + 1
            quarters.append(
                _make_quarterly_period(
                    fy=fy,
                    fq=fq,
                    income={"Revenues": 1000 * (1.05 ** i)},
                    balance={"Assets": 5000 * (1.02 ** i)},
                )
            )
        quarters.reverse()
        state = _make_state(quarters)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False

    def test_only_one_rap_category_declining(self) -> None:
        """Declining in only 1 RAP category => NOT_FIRED."""
        quarters = []
        for i in range(8):
            fy = 2023 + (i // 4)
            fq = (i % 4) + 1
            # Only revenue declining (agent), assets stable (host)
            quarters.append(
                _make_quarterly_period(
                    fy=fy,
                    fq=fq,
                    income={"Revenues": 1000 * (0.85 ** i)},
                    balance={"Assets": 5000},  # stable
                )
            )
        quarters.reverse()
        state = _make_state(quarters)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False

    def test_no_quarterly_xbrl(self) -> None:
        """state.extracted.financials.quarterly_xbrl = None => NOT_FIRED."""
        state = _make_state(quarters=None)

        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False
        assert "insufficient" in result.headline.lower()


class TestMigrationDriftProtocol:
    """Tests for PatternEngine protocol compliance."""

    def test_engine_id(self) -> None:
        """engine_id is 'migration_drift'."""
        engine = MigrationDriftEngine()
        assert engine.engine_id == "migration_drift"

    def test_engine_name(self) -> None:
        """engine_name is 'Migration Drift'."""
        engine = MigrationDriftEngine()
        assert engine.engine_name == "Migration Drift"

    def test_returns_engine_result(self) -> None:
        """evaluate() returns an EngineResult."""
        from do_uw.stages.score.pattern_engine import EngineResult

        state = _make_state(quarters=None)
        engine = MigrationDriftEngine()
        result = engine.evaluate({}, state=state)
        assert isinstance(result, EngineResult)
