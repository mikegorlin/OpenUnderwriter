"""Tests for XBRL derived concept computation.

Covers all ~25 derived concepts: margins, ratios, per-share metrics,
and multi-period computation. Validates None-safety and zero-division guards.
"""

from __future__ import annotations

import pytest

from do_uw.stages.extract.xbrl_derived import (
    compute_derived_concepts,
    compute_multi_period_derived,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_primitives() -> dict[str, float | None]:
    """Complete set of primitive inputs for all derived concepts."""
    return {
        "revenue": 1_000_000,
        "cost_of_revenue": 600_000,
        "operating_income": 200_000,
        "net_income": 100_000,
        "depreciation_amortization": 50_000,
        "interest_expense": 20_000,
        "income_tax_expense": 30_000,
        "pretax_income": 130_000,
        "current_assets": 500_000,
        "current_liabilities": 250_000,
        "inventory": 80_000,
        "total_debt": 400_000,
        "stockholders_equity": 300_000,
        "goodwill": 50_000,
        "intangible_assets": 30_000,
        "cash_and_equivalents": 150_000,
        "shares_outstanding": 10_000,
        "operating_cash_flow": 180_000,
        "capital_expenditures": 60_000,
        "dividends_paid": 40_000,
        "total_assets": 1_200_000,
    }


# ---------------------------------------------------------------------------
# Margin tests
# ---------------------------------------------------------------------------

class TestMargins:
    def test_gross_margin_pct(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # (1_000_000 - 600_000) / 1_000_000 * 100 = 40.0
        assert result["gross_margin_pct"] == 40.0

    def test_operating_margin_pct(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 200_000 / 1_000_000 * 100 = 20.0
        assert result["operating_margin_pct"] == 20.0

    def test_net_margin_pct(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 100_000 / 1_000_000 * 100 = 10.0
        assert result["net_margin_pct"] == 10.0

    def test_ebitda_margin_pct(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # ebitda = 200_000 + 50_000 = 250_000
        # 250_000 / 1_000_000 * 100 = 25.0
        assert result["ebitda_margin_pct"] == 25.0

    def test_effective_tax_rate(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 30_000 / 130_000 * 100 = 23.08
        assert result["effective_tax_rate"] == pytest.approx(23.08, abs=0.01)


# ---------------------------------------------------------------------------
# Coverage / leverage ratio tests
# ---------------------------------------------------------------------------

class TestRatios:
    def test_interest_coverage_ratio(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # ebit = operating_income = 200_000; 200_000 / 20_000 = 10.0
        assert result["interest_coverage_ratio"] == 10.0

    def test_current_ratio(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 500_000 / 250_000 = 2.0
        assert result["current_ratio"] == 2.0

    def test_quick_ratio(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # (500_000 - 80_000) / 250_000 = 1.68
        assert result["quick_ratio"] == 1.68

    def test_debt_to_equity(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 400_000 / 300_000 = 1.3333
        assert result["debt_to_equity"] == pytest.approx(1.3333, abs=0.001)

    def test_debt_to_ebitda(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # ebitda = 250_000; 400_000 / 250_000 = 1.6
        assert result["debt_to_ebitda"] == 1.6

    def test_return_on_assets(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 100_000 / 1_200_000 * 100 = 8.33
        assert result["return_on_assets"] == pytest.approx(8.33, abs=0.01)

    def test_return_on_equity(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 100_000 / 300_000 * 100 = 33.33
        assert result["return_on_equity"] == pytest.approx(33.33, abs=0.01)

    def test_asset_turnover(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 1_000_000 / 1_200_000 = 0.8333
        assert result["asset_turnover"] == pytest.approx(0.8333, abs=0.001)


# ---------------------------------------------------------------------------
# Balance sheet derived tests
# ---------------------------------------------------------------------------

class TestBalanceSheetDerived:
    def test_tangible_book_value(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 300_000 - 50_000 - 30_000 = 220_000
        assert result["tangible_book_value"] == 220_000.0

    def test_net_debt(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 400_000 - 150_000 = 250_000
        assert result["net_debt"] == 250_000.0

    def test_book_value_per_share(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 300_000 / 10_000 = 30.0
        assert result["book_value_per_share"] == 30.0

    def test_working_capital(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 500_000 - 250_000 = 250_000
        assert result["working_capital"] == 250_000.0

    def test_ebitda(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 200_000 + 50_000 = 250_000
        assert result["ebitda"] == 250_000.0


# ---------------------------------------------------------------------------
# Cash flow derived tests
# ---------------------------------------------------------------------------

class TestCashFlowDerived:
    def test_free_cash_flow(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 180_000 - 60_000 = 120_000
        assert result["free_cash_flow"] == 120_000.0

    def test_fcf_to_revenue(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # FCF = 120_000; 120_000 / 1_000_000 * 100 = 12.0
        assert result["fcf_to_revenue"] == 12.0

    def test_capex_to_revenue(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 60_000 / 1_000_000 * 100 = 6.0
        assert result["capex_to_revenue"] == 6.0

    def test_capex_to_depreciation(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 60_000 / 50_000 = 1.2
        assert result["capex_to_depreciation"] == 1.2

    def test_dividend_payout_ratio(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # 40_000 / 100_000 * 100 = 40.0
        assert result["dividend_payout_ratio"] == 40.0

    def test_fcf_per_share(self) -> None:
        result = compute_derived_concepts(_base_primitives())
        # FCF = 120_000; 120_000 / 10_000 = 12.0
        assert result["fcf_per_share"] == 12.0


# ---------------------------------------------------------------------------
# None-safety and zero-division tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_none_input_returns_none(self) -> None:
        """All derived concepts return None when any required input is None."""
        result = compute_derived_concepts({"revenue": None, "cost_of_revenue": None})
        assert result.get("gross_margin_pct") is None
        assert result.get("current_ratio") is None

    def test_missing_input_returns_none(self) -> None:
        """Missing keys treated as None -- no KeyError."""
        result = compute_derived_concepts({})
        assert result.get("gross_margin_pct") is None
        assert result.get("net_margin_pct") is None

    def test_zero_denominator_returns_none(self) -> None:
        """Zero denominators produce None, not ZeroDivisionError."""
        primitives = _base_primitives()
        primitives["revenue"] = 0
        primitives["current_liabilities"] = 0
        primitives["stockholders_equity"] = 0
        primitives["interest_expense"] = 0
        primitives["shares_outstanding"] = 0
        primitives["depreciation_amortization"] = 0
        primitives["total_assets"] = 0
        result = compute_derived_concepts(primitives)
        assert result.get("gross_margin_pct") is None
        assert result.get("operating_margin_pct") is None
        assert result.get("net_margin_pct") is None
        assert result.get("current_ratio") is None
        assert result.get("debt_to_equity") is None
        assert result.get("interest_coverage_ratio") is None
        assert result.get("book_value_per_share") is None
        assert result.get("capex_to_depreciation") is None
        assert result.get("return_on_assets") is None
        assert result.get("return_on_equity") is None
        assert result.get("asset_turnover") is None

    def test_no_exceptions_ever(self) -> None:
        """compute_derived_concepts never raises, regardless of input."""
        # Empty dict
        compute_derived_concepts({})
        # All None
        compute_derived_concepts({k: None for k in _base_primitives()})
        # Negative values
        compute_derived_concepts({k: -1.0 for k in _base_primitives()})

    def test_partial_inputs_computes_what_it_can(self) -> None:
        """With partial inputs, computes available concepts and skips the rest."""
        result = compute_derived_concepts({
            "revenue": 1000,
            "cost_of_revenue": 600,
        })
        assert result["gross_margin_pct"] == 40.0
        assert result.get("current_ratio") is None


# ---------------------------------------------------------------------------
# Multi-period tests
# ---------------------------------------------------------------------------

class TestMultiPeriod:
    def test_compute_multi_period_derived(self) -> None:
        """Multi-period returns per-period derived values."""
        period_items = {
            "FY2024": _base_primitives(),
            "FY2023": {**_base_primitives(), "revenue": 900_000},
        }
        result = compute_multi_period_derived(period_items)
        assert "gross_margin_pct" in result
        assert "FY2024" in result["gross_margin_pct"]
        assert "FY2023" in result["gross_margin_pct"]
        assert result["gross_margin_pct"]["FY2024"] == 40.0

    def test_revenue_growth_yoy_requires_two_periods(self) -> None:
        """revenue_growth_yoy needs 2 periods; single period returns None."""
        single = {"FY2024": _base_primitives()}
        result = compute_multi_period_derived(single)
        assert result.get("revenue_growth_yoy", {}).get("FY2024") is None

    def test_revenue_growth_yoy_computed(self) -> None:
        """revenue_growth_yoy correctly computes growth."""
        period_items = {
            "FY2023": {**_base_primitives(), "revenue": 800_000},
            "FY2024": _base_primitives(),  # revenue = 1_000_000
        }
        result = compute_multi_period_derived(period_items)
        # (1_000_000 - 800_000) / 800_000 * 100 = 25.0
        assert result["revenue_growth_yoy"]["FY2024"] == 25.0
        # First period has no prior, so None
        assert result["revenue_growth_yoy"]["FY2023"] is None

    def test_revenue_growth_yoy_negative(self) -> None:
        """revenue_growth_yoy handles revenue decline."""
        period_items = {
            "FY2023": _base_primitives(),  # revenue = 1_000_000
            "FY2024": {**_base_primitives(), "revenue": 700_000},
        }
        result = compute_multi_period_derived(period_items)
        # (700_000 - 1_000_000) / 1_000_000 * 100 = -30.0
        assert result["revenue_growth_yoy"]["FY2024"] == -30.0

    def test_revenue_growth_yoy_from_negative_base(self) -> None:
        """revenue_growth_yoy uses abs(prior) for negative base revenue."""
        period_items = {
            "FY2023": {**_base_primitives(), "revenue": -100_000},
            "FY2024": {**_base_primitives(), "revenue": 200_000},
        }
        result = compute_multi_period_derived(period_items)
        # (200_000 - (-100_000)) / abs(-100_000) * 100 = 300.0
        assert result["revenue_growth_yoy"]["FY2024"] == 300.0

    def test_empty_periods(self) -> None:
        """Empty period_items returns empty dict."""
        result = compute_multi_period_derived({})
        assert result == {}

    def test_three_periods(self) -> None:
        """Three periods produce YoY for latter two."""
        period_items = {
            "FY2022": {**_base_primitives(), "revenue": 500_000},
            "FY2023": {**_base_primitives(), "revenue": 800_000},
            "FY2024": _base_primitives(),  # 1_000_000
        }
        result = compute_multi_period_derived(period_items)
        yoy = result["revenue_growth_yoy"]
        assert yoy["FY2022"] is None
        # (800_000 - 500_000) / 500_000 * 100 = 60.0
        assert yoy["FY2023"] == 60.0
        # (1_000_000 - 800_000) / 800_000 * 100 = 25.0
        assert yoy["FY2024"] == 25.0
