"""Tests for yfinance info dict field population.

Covers: profitability, growth, valuation, scale fields on StockPerformance,
short interest absolute counts on ShortInterestProfile, and ISS risk scores
on BoardProfile.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.governance import BoardProfile
from do_uw.models.market import ShortInterestProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.stock_performance import extract_stock_performance


def _sourced_str(val: str) -> SourcedValue[str]:
    from datetime import UTC, datetime

    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(info: dict[str, Any]) -> AnalysisState:
    """Build minimal state with yfinance info dict."""
    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"),
        sector=_sourced_str("TECH"),
    )
    # Minimal price history so extractor doesn't bail early
    history_1y = {
        "Close": [100.0, 101.0],
        "Date": ["2025-01-02", "2025-01-03"],
        "Open": [100.0, 101.0],
        "High": [101.0, 102.0],
        "Low": [99.0, 100.0],
        "Volume": [1000000, 1000000],
    }
    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(identity=identity),
        acquired_data=AcquiredData(
            market_data={"history_1y": history_1y, "info": info},
            filings={},
        ),
    )


class TestProfitabilityFields:
    """Test profitability margin population from yfinance info."""

    def test_profit_margin_populated(self) -> None:
        info = {"profitMargins": 0.2634}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.profit_margin is not None
        assert perf.profit_margin.value == 0.2634

    def test_operating_margin_populated(self) -> None:
        info = {"operatingMargins": 0.3012}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.operating_margin is not None
        assert perf.operating_margin.value == 0.3012

    def test_gross_margin_populated(self) -> None:
        info = {"grossMargins": 0.4587}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.gross_margin is not None
        assert perf.gross_margin.value == 0.4587

    def test_return_on_equity_populated(self) -> None:
        info = {"returnOnEquity": 1.4736}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.return_on_equity is not None
        assert perf.return_on_equity.value == 1.4736

    def test_return_on_assets_populated(self) -> None:
        info = {"returnOnAssets": 0.2847}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.return_on_assets is not None
        assert perf.return_on_assets.value == 0.2847


class TestGrowthFields:
    """Test growth metric population from yfinance info."""

    def test_revenue_growth_populated(self) -> None:
        info = {"revenueGrowth": 0.0474}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.revenue_growth is not None
        assert perf.revenue_growth.value == 0.0474

    def test_earnings_growth_populated(self) -> None:
        info = {"earningsGrowth": 0.1003}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.earnings_growth is not None
        assert perf.earnings_growth.value == 0.1003


class TestValuationFields:
    """Test additional valuation ratio population."""

    def test_price_to_book(self) -> None:
        info = {"priceToBook": 65.12}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.price_to_book is not None
        assert perf.price_to_book.value == 65.12

    def test_price_to_sales(self) -> None:
        info = {"priceToSalesTrailing12Months": 9.87}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.price_to_sales is not None
        assert perf.price_to_sales.value == 9.87

    def test_enterprise_to_revenue(self) -> None:
        info = {"enterpriseToRevenue": 10.23}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.enterprise_to_revenue is not None
        assert perf.enterprise_to_revenue.value == 10.23


class TestScaleFields:
    """Test scale metric population from yfinance info."""

    def test_market_cap_yf(self) -> None:
        info = {"marketCap": 3_790_000_000_000}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.market_cap_yf is not None
        assert perf.market_cap_yf.value == 3_790_000_000_000

    def test_enterprise_value(self) -> None:
        info = {"enterpriseValue": 3_830_000_000_000}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.enterprise_value is not None
        assert perf.enterprise_value.value == 3_830_000_000_000

    def test_employee_count_yf(self) -> None:
        info = {"fullTimeEmployees": 164000}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.employee_count_yf is not None
        assert perf.employee_count_yf.value == 164000

    def test_none_values_skipped(self) -> None:
        """None or missing info keys don't crash or populate fields."""
        info = {"marketCap": None, "fullTimeEmployees": None}
        state = _make_state(info)
        perf, _, _ = extract_stock_performance(state)
        assert perf.market_cap_yf is None
        assert perf.employee_count_yf is None


class TestShortInterestAbsoluteFields:
    """Test absolute short interest fields populated from yfinance."""

    def test_shares_short_fields(self) -> None:
        from do_uw.stages.extract.short_interest import extract_short_interest

        state = _make_state({
            "sharesShort": 120000000,
            "sharesShortPriorMonth": 115000000,
            "sharesPercentSharesOut": 0.0079,
            "shortPercentOfFloat": 0.0093,
            "shortRatio": 1.08,
        })
        profile, _ = extract_short_interest(state)

        assert profile.shares_short is not None
        assert profile.shares_short.value == 120000000
        assert profile.shares_short_prior is not None
        assert profile.shares_short_prior.value == 115000000
        assert profile.short_pct_shares_out is not None
        assert abs(profile.short_pct_shares_out.value - 0.79) < 0.01


class TestISSRiskScores:
    """Test ISS governance risk score population from yfinance."""

    def test_iss_scores_populated(self) -> None:
        from do_uw.stages.extract.governance_fallbacks import (
            fill_board_from_yfinance,
        )

        state = _make_state({
            "auditRisk": 1,
            "boardRisk": 1,
            "compensationRisk": 5,
            "shareHolderRightsRisk": 1,
            "overallRisk": 1,
        })
        board = BoardProfile()
        fill_board_from_yfinance(state, board)

        assert board.iss_audit_risk is not None
        assert board.iss_audit_risk.value == 1
        assert board.iss_board_risk is not None
        assert board.iss_board_risk.value == 1
        assert board.iss_compensation_risk is not None
        assert board.iss_compensation_risk.value == 5
        assert board.iss_shareholder_rights_risk is not None
        assert board.iss_shareholder_rights_risk.value == 1
        assert board.iss_overall_risk is not None
        assert board.iss_overall_risk.value == 1

    def test_iss_scores_skip_out_of_range(self) -> None:
        from do_uw.stages.extract.governance_fallbacks import (
            fill_board_from_yfinance,
        )

        state = _make_state({
            "auditRisk": 0,  # below valid range
            "boardRisk": 11,  # above valid range
        })
        board = BoardProfile()
        fill_board_from_yfinance(state, board)

        assert board.iss_audit_risk is None
        assert board.iss_board_risk is None
