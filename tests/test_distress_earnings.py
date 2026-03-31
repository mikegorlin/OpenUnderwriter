"""Tests for distress models and earnings quality analysis.

20 tests covering all 4 distress models + earnings quality with known
inputs and expected outputs. Verifies formulas against hand-calculated
values and edge cases (missing inputs, division by zero, pre-revenue).
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    DistressZone,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.stages.analyze.financial_formulas import (
    compute_m_score,
)
from do_uw.stages.analyze.financial_formulas_distress import (
    compute_f_score,
    compute_o_score,
)
from do_uw.stages.analyze.financial_models import compute_distress_indicators
from do_uw.stages.analyze.earnings_quality import (
    compute_earnings_quality,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _sv(val: float) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue[float](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime(2024, 12, 31, tzinfo=UTC),
    )


def _make_item(
    concept: str,
    latest: float | None = None,
    prior: float | None = None,
) -> FinancialLineItem:
    """Create a line item with latest and optional prior value."""
    vals: dict[str, SourcedValue[float] | None] = {}
    if prior is not None:
        vals["FY2023"] = _sv(prior)
    if latest is not None:
        vals["FY2024"] = _sv(latest)
    return FinancialLineItem(
        label=concept, xbrl_concept=concept, values=vals,
    )


def _build_statements(
    items: list[FinancialLineItem],
) -> FinancialStatements:
    """Build FinancialStatements from line items, routing to correct stmt."""
    income_concepts = {
        "revenue", "cost_of_revenue", "gross_profit", "ebit",
        "net_income", "sga_expense", "depreciation_amortization",
        "operating_income",
    }
    balance_concepts = {
        "total_assets", "total_liabilities", "current_assets",
        "current_liabilities", "retained_earnings", "stockholders_equity",
        "accounts_receivable", "property_plant_equipment",
        "long_term_debt", "shares_outstanding", "cash_and_equivalents",
    }
    cashflow_concepts = {
        "operating_cash_flow", "capital_expenditures", "dividends_paid",
    }

    income_items: list[FinancialLineItem] = []
    balance_items: list[FinancialLineItem] = []
    cashflow_items: list[FinancialLineItem] = []

    for item in items:
        c = item.xbrl_concept or ""
        if c in income_concepts:
            income_items.append(item)
        elif c in balance_concepts:
            balance_items.append(item)
        elif c in cashflow_concepts:
            cashflow_items.append(item)
        else:
            # Default to income.
            income_items.append(item)

    periods = ["FY2023", "FY2024"]

    return FinancialStatements(
        income_statement=FinancialStatement(
            statement_type="income", periods=periods,
            line_items=income_items,
        ) if income_items else None,
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet", periods=periods,
            line_items=balance_items,
        ) if balance_items else None,
        cash_flow=FinancialStatement(
            statement_type="cash_flow", periods=periods,
            line_items=cashflow_items,
        ) if cashflow_items else None,
        periods_available=2,
    )


# ---------------------------------------------------------------------------
# Altman Z-Score tests
# ---------------------------------------------------------------------------


class TestAltmanZScore:
    """Tests for Altman Z-Score computation."""

    def test_altman_z_original_safe(self) -> None:
        """Known inputs producing Z > 2.99 -> SAFE zone."""
        # Hand-calculated: strong healthy company.
        # WC/TA=0.3, RE/TA=0.4, EBIT/TA=0.15, MktCap/TL=5.0, Sales/TA=1.5
        # Z = 1.2*0.3 + 1.4*0.4 + 3.3*0.15 + 0.6*5.0 + 1.0*1.5
        # Z = 0.36 + 0.56 + 0.495 + 3.0 + 1.5 = 5.915
        items = [
            _make_item("total_assets", 1000.0),
            _make_item("total_liabilities", 400.0),
            _make_item("current_assets", 500.0),
            _make_item("current_liabilities", 200.0),
            _make_item("retained_earnings", 400.0),
            _make_item("ebit", 150.0),
            _make_item("revenue", 1500.0),
        ]
        stmts = _build_statements(items)
        result, _ = compute_distress_indicators(stmts, "TECH", 2000.0)

        z = result.altman_z_score
        assert z is not None
        assert z.model_variant == "original"
        assert z.score is not None
        assert z.score > 2.99
        assert z.zone == DistressZone.SAFE

    def test_altman_z_original_distress(self) -> None:
        """Known inputs producing Z < 1.81 -> DISTRESS zone."""
        # Weak company: negative working capital, low earnings.
        # WC/TA=-0.2, RE/TA=-0.1, EBIT/TA=0.01, MktCap/TL=0.5, Sales/TA=0.3
        # Z = 1.2*(-0.2) + 1.4*(-0.1) + 3.3*0.01 + 0.6*0.5 + 1.0*0.3
        # Z = -0.24 + -0.14 + 0.033 + 0.3 + 0.3 = 0.253
        items = [
            _make_item("total_assets", 1000.0),
            _make_item("total_liabilities", 800.0),
            _make_item("current_assets", 200.0),
            _make_item("current_liabilities", 400.0),
            _make_item("retained_earnings", -100.0),
            _make_item("ebit", 10.0),
            _make_item("revenue", 300.0),
        ]
        stmts = _build_statements(items)
        result, _ = compute_distress_indicators(stmts, "MFG", 400.0)

        z = result.altman_z_score
        assert z is not None
        assert z.score is not None
        assert z.score < 1.81
        assert z.zone == DistressZone.DISTRESS

    def test_altman_z_double_prime_financial_sector(self) -> None:
        """FINS sector triggers Z'' variant."""
        items = [
            _make_item("total_assets", 1000.0),
            _make_item("total_liabilities", 600.0),
            _make_item("current_assets", 500.0),
            _make_item("current_liabilities", 200.0),
            _make_item("retained_earnings", 300.0),
            _make_item("ebit", 100.0),
            _make_item("revenue", 500.0),
            _make_item("stockholders_equity", 400.0),
        ]
        stmts = _build_statements(items)
        result, _ = compute_distress_indicators(stmts, "FINS")

        z = result.altman_z_score
        assert z is not None
        assert z.model_variant == "z_double_prime"
        assert z.score is not None

    def test_altman_z_early_stage_pre_revenue(self) -> None:
        """Zero revenue -> early_stage metrics."""
        items = [
            _make_item("total_assets", 500.0),
            _make_item("total_liabilities", 100.0),
            _make_item("cash_and_equivalents", 300.0),
            _make_item("operating_cash_flow", -120.0),
        ]
        stmts = _build_statements(items)
        result, _ = compute_distress_indicators(stmts, "TECH")

        z = result.altman_z_score
        assert z is not None
        assert z.model_variant == "early_stage"
        assert z.score is None
        assert z.zone == DistressZone.NOT_APPLICABLE
        # Should have alt metrics in trajectory.
        assert len(z.trajectory) == 1
        alt = z.trajectory[0]
        assert "monthly_burn_rate" in alt
        assert "cash_runway_months" in alt
        assert alt["monthly_burn_rate"] == 10.0  # 120/12
        assert alt["cash_runway_months"] == 30.0  # 300/10

    def test_altman_z_division_by_zero(self) -> None:
        """Total assets = 0 -> handled gracefully."""
        items = [
            _make_item("total_assets", 0.0),
            _make_item("total_liabilities", 100.0),
            _make_item("revenue", 50.0),
        ]
        stmts = _build_statements(items)
        result, _ = compute_distress_indicators(stmts, "TECH", 100.0)

        z = result.altman_z_score
        assert z is not None
        assert z.score is None
        assert z.is_partial is True


# ---------------------------------------------------------------------------
# Beneish M-Score tests
# ---------------------------------------------------------------------------


class TestBeneishMScore:
    """Tests for Beneish M-Score computation."""

    def test_beneish_m_score_manipulation(self) -> None:
        """Known inputs producing M > -1.78 -> manipulation flag."""
        # Design inputs to produce M > -1.78.
        # High DSRI (1.5), high SGI (1.8), high TATA (0.15) push M up.
        inputs: dict[str, float | None] = {
            "accounts_receivable": 150.0,
            "accounts_receivable_prior": 80.0,
            "revenue": 800.0,
            "revenue_prior": 600.0,
            "gross_profit": 300.0,
            "gross_profit_prior": 270.0,
            "current_assets": 400.0,
            "current_assets_prior": 350.0,
            "property_plant_equipment": 200.0,
            "property_plant_equipment_prior": 180.0,
            "total_assets": 1000.0,
            "total_assets_prior": 850.0,
            "depreciation_amortization": 30.0,
            "depreciation_amortization_prior": 28.0,
            "sga_expense": 150.0,
            "sga_expense_prior": 130.0,
            "net_income": 200.0,
            "operating_cash_flow": 50.0,
            "total_liabilities": 500.0,
            "total_liabilities_prior": 420.0,
        }
        result = compute_m_score(inputs)
        assert result.score is not None
        assert result.score > -1.78
        assert result.zone == DistressZone.DISTRESS

    def test_beneish_m_score_clean(self) -> None:
        """Known inputs producing M < -1.78 -> SAFE."""
        # Stable company: ratios all near 1.0, low TATA.
        inputs: dict[str, float | None] = {
            "accounts_receivable": 100.0,
            "accounts_receivable_prior": 100.0,
            "revenue": 1000.0,
            "revenue_prior": 1000.0,
            "gross_profit": 400.0,
            "gross_profit_prior": 400.0,
            "current_assets": 500.0,
            "current_assets_prior": 500.0,
            "property_plant_equipment": 300.0,
            "property_plant_equipment_prior": 300.0,
            "total_assets": 1200.0,
            "total_assets_prior": 1200.0,
            "depreciation_amortization": 50.0,
            "depreciation_amortization_prior": 50.0,
            "sga_expense": 200.0,
            "sga_expense_prior": 200.0,
            "net_income": 150.0,
            "operating_cash_flow": 140.0,
            "total_liabilities": 600.0,
            "total_liabilities_prior": 600.0,
        }
        result = compute_m_score(inputs)
        assert result.score is not None
        assert result.score <= -1.78
        assert result.zone == DistressZone.SAFE

    def test_beneish_m_score_partial(self) -> None:
        """3 of 8 inputs missing -> is_partial=True with missing listed."""
        inputs: dict[str, float | None] = {
            "accounts_receivable": 100.0,
            "accounts_receivable_prior": None,
            "revenue": 1000.0,
            "revenue_prior": 1000.0,
            "gross_profit": None,
            "gross_profit_prior": None,
            "current_assets": 500.0,
            "current_assets_prior": 500.0,
            "property_plant_equipment": 300.0,
            "property_plant_equipment_prior": 300.0,
            "total_assets": 1200.0,
            "total_assets_prior": 1200.0,
            "depreciation_amortization": 50.0,
            "depreciation_amortization_prior": 50.0,
            "sga_expense": None,
            "sga_expense_prior": None,
            "net_income": 150.0,
            "operating_cash_flow": 140.0,
            "total_liabilities": 600.0,
            "total_liabilities_prior": 600.0,
        }
        result = compute_m_score(inputs)
        assert result.is_partial is True
        assert len(result.missing_inputs) >= 3
        assert "DSRI" in result.missing_inputs
        assert "GMI" in result.missing_inputs


# ---------------------------------------------------------------------------
# Ohlson O-Score tests
# ---------------------------------------------------------------------------


class TestOhlsonOScore:
    """Tests for Ohlson O-Score computation."""

    def test_ohlson_o_score_high_probability(self) -> None:
        """Known inputs -> high bankruptcy probability."""
        # Company with high leverage, negative income.
        inputs: dict[str, float | None] = {
            "total_assets": 500.0,
            "total_liabilities": 600.0,  # TL > TA
            "current_assets": 100.0,
            "current_liabilities": 300.0,
            "net_income": -100.0,
            "net_income_prior": -80.0,  # Two years negative
            "operating_cash_flow": -50.0,
            "depreciation_amortization": 20.0,
        }
        result = compute_o_score(inputs)
        assert result.score is not None
        assert result.score > 0.5  # High probability.
        assert result.zone == DistressZone.DISTRESS

    def test_ohlson_o_score_probability_range(self) -> None:
        """Verify probability between 0 and 1."""
        inputs: dict[str, float | None] = {
            "total_assets": 10000.0,
            "total_liabilities": 3000.0,
            "current_assets": 4000.0,
            "current_liabilities": 2000.0,
            "net_income": 800.0,
            "net_income_prior": 700.0,
            "operating_cash_flow": 900.0,
            "depreciation_amortization": 200.0,
        }
        result = compute_o_score(inputs)
        assert result.score is not None
        assert 0.0 <= result.score <= 1.0


# ---------------------------------------------------------------------------
# Piotroski F-Score tests
# ---------------------------------------------------------------------------


class TestPiotroskiFScore:
    """Tests for Piotroski F-Score computation."""

    def test_piotroski_f_score_strong(self) -> None:
        """All 9 criteria met -> score=9, SAFE zone."""
        inputs: dict[str, float | None] = {
            "net_income": 200.0,
            "net_income_prior": 150.0,
            "total_assets": 1000.0,
            "total_assets_prior": 1000.0,
            "operating_cash_flow": 250.0,
            "long_term_debt": 100.0,
            "long_term_debt_prior": 150.0,
            "current_assets": 500.0,
            "current_assets_prior": 400.0,
            "current_liabilities": 200.0,
            "current_liabilities_prior": 200.0,
            "shares_outstanding": 100.0,
            "shares_outstanding_prior": 100.0,
            "gross_profit": 500.0,
            "gross_profit_prior": 450.0,
            "revenue": 1200.0,
            "revenue_prior": 1100.0,
        }
        result = compute_f_score(inputs)
        assert result.score == 9.0
        assert result.zone == DistressZone.SAFE
        assert result.is_partial is False

    def test_piotroski_f_score_weak(self) -> None:
        """Only 1 criterion met -> score=1, DISTRESS zone."""
        inputs: dict[str, float | None] = {
            "net_income": -50.0,
            "net_income_prior": -30.0,  # Worsening.
            "total_assets": 1000.0,
            "total_assets_prior": 1000.0,
            "operating_cash_flow": -80.0,
            "long_term_debt": 500.0,
            "long_term_debt_prior": 400.0,  # Increasing.
            "current_assets": 200.0,
            "current_assets_prior": 300.0,  # Decreasing.
            "current_liabilities": 400.0,
            "current_liabilities_prior": 300.0,  # Increasing.
            "shares_outstanding": 120.0,
            "shares_outstanding_prior": 100.0,  # Dilution.
            "gross_profit": 300.0,
            "gross_profit_prior": 350.0,  # Declining.
            "revenue": 900.0,
            "revenue_prior": 1000.0,  # Declining.
        }
        result = compute_f_score(inputs)
        assert result.score is not None
        assert result.score <= 2.0
        assert result.zone == DistressZone.DISTRESS

    def test_piotroski_f_score_individual_criteria(self) -> None:
        """Verify each of 9 criteria independently."""
        # All criteria met = score 9.
        inputs: dict[str, float | None] = {
            "net_income": 100.0,          # 1: positive NI
            "net_income_prior": 80.0,     # 2: improving ROA
            "total_assets": 1000.0,
            "total_assets_prior": 1000.0,
            "operating_cash_flow": 150.0,  # 3: positive OCF, 4: OCF > NI
            "long_term_debt": 100.0,
            "long_term_debt_prior": 200.0,  # 5: decreasing LTD
            "current_assets": 500.0,
            "current_assets_prior": 400.0,
            "current_liabilities": 200.0,
            "current_liabilities_prior": 200.0,  # 6: improving CR
            "shares_outstanding": 100.0,
            "shares_outstanding_prior": 100.0,  # 7: no dilution
            "gross_profit": 450.0,
            "gross_profit_prior": 400.0,
            "revenue": 1000.0,
            "revenue_prior": 950.0,  # 8: improving GM, 9: improving AT
        }
        result = compute_f_score(inputs)
        assert result.score == 9.0

        # Trajectory contains all 9 criteria.
        assert len(result.trajectory) == 9
        criterion_names = [
            str(c.get("criterion", "")) for c in result.trajectory
        ]
        assert "positive_ni" in criterion_names
        assert "improving_roa" in criterion_names
        assert "positive_ocf" in criterion_names
        assert "ocf_exceeds_ni" in criterion_names
        assert "decreasing_leverage" in criterion_names
        assert "improving_current_ratio" in criterion_names
        assert "no_dilution" in criterion_names
        assert "improving_gross_margin" in criterion_names
        assert "improving_asset_turnover" in criterion_names


# ---------------------------------------------------------------------------
# Trajectory test
# ---------------------------------------------------------------------------


class TestTrajectory:
    """Tests for 4-quarter trajectory."""

    def test_trajectory_multiple_periods(self) -> None:
        """Multiple periods produce trajectory entries."""
        # Build statements with 3 periods.
        items = [
            FinancialLineItem(
                label="total_assets", xbrl_concept="total_assets",
                values={
                    "FY2022": _sv(900.0),
                    "FY2023": _sv(1000.0),
                    "FY2024": _sv(1100.0),
                },
            ),
            FinancialLineItem(
                label="total_liabilities", xbrl_concept="total_liabilities",
                values={
                    "FY2022": _sv(400.0),
                    "FY2023": _sv(450.0),
                    "FY2024": _sv(500.0),
                },
            ),
            FinancialLineItem(
                label="current_assets", xbrl_concept="current_assets",
                values={
                    "FY2022": _sv(400.0),
                    "FY2023": _sv(450.0),
                    "FY2024": _sv(500.0),
                },
            ),
            FinancialLineItem(
                label="current_liabilities",
                xbrl_concept="current_liabilities",
                values={
                    "FY2022": _sv(200.0),
                    "FY2023": _sv(200.0),
                    "FY2024": _sv(200.0),
                },
            ),
            FinancialLineItem(
                label="retained_earnings", xbrl_concept="retained_earnings",
                values={
                    "FY2022": _sv(300.0),
                    "FY2023": _sv(350.0),
                    "FY2024": _sv(400.0),
                },
            ),
            FinancialLineItem(
                label="ebit", xbrl_concept="ebit",
                values={
                    "FY2022": _sv(100.0),
                    "FY2023": _sv(120.0),
                    "FY2024": _sv(140.0),
                },
            ),
            FinancialLineItem(
                label="revenue", xbrl_concept="revenue",
                values={
                    "FY2022": _sv(1000.0),
                    "FY2023": _sv(1100.0),
                    "FY2024": _sv(1200.0),
                },
            ),
        ]

        periods = ["FY2022", "FY2023", "FY2024"]
        income_items = [i for i in items if i.xbrl_concept in {"ebit", "revenue"}]
        balance_items = [i for i in items if i.xbrl_concept not in {"ebit", "revenue"}]

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income", periods=periods,
                line_items=income_items,
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet", periods=periods,
                line_items=balance_items,
            ),
            periods_available=3,
        )

        result, _ = compute_distress_indicators(stmts, "TECH", 2000.0)
        z = result.altman_z_score
        assert z is not None
        # Should have trajectory entries (at least 2 of 3 periods).
        assert len(z.trajectory) >= 2
        for entry in z.trajectory:
            assert "period" in entry
            assert "score" in entry
            assert "zone" in entry


# ---------------------------------------------------------------------------
# Earnings quality tests
# ---------------------------------------------------------------------------


class TestEarningsQuality:
    """Tests for earnings quality analysis."""

    def test_accruals_ratio_normal(self) -> None:
        """NI close to OCF -> low accruals ratio."""
        items = [
            _make_item("net_income", 100.0),
            _make_item("operating_cash_flow", 95.0),
            _make_item("total_assets", 1000.0),
        ]
        stmts = _build_statements(items)
        sv, _report = compute_earnings_quality(stmts)
        assert sv is not None
        accruals = sv.value.get("accruals_ratio")
        assert accruals is not None
        # (100-95)/1000 = 0.005
        assert abs(accruals - 0.005) < 0.001
        assert accruals < 0.10

    def test_accruals_ratio_red_flag(self) -> None:
        """NI >> OCF -> high accruals flagged."""
        items = [
            _make_item("net_income", 200.0),
            _make_item("operating_cash_flow", 50.0),
            _make_item("total_assets", 1000.0),
        ]
        stmts = _build_statements(items)
        sv, _ = compute_earnings_quality(stmts)
        assert sv is not None
        accruals = sv.value.get("accruals_ratio")
        assert accruals is not None
        # (200-50)/1000 = 0.15
        assert accruals > 0.10

    def test_ocf_ni_ratio_healthy(self) -> None:
        """OCF/NI in 0.8-1.5 range."""
        items = [
            _make_item("net_income", 100.0),
            _make_item("operating_cash_flow", 110.0),
            _make_item("total_assets", 1000.0),
        ]
        stmts = _build_statements(items)
        sv, _ = compute_earnings_quality(stmts)
        assert sv is not None
        ocf_ni = sv.value.get("ocf_to_ni")
        assert ocf_ni is not None
        assert 0.8 <= ocf_ni <= 1.5

    def test_dso_trend_increasing(self) -> None:
        """DSO increase between periods flagged."""
        items = [
            _make_item("accounts_receivable", 200.0, 100.0),
            _make_item("revenue", 1000.0, 1000.0),
        ]
        stmts = _build_statements(items)
        sv, _ = compute_earnings_quality(stmts)
        assert sv is not None
        dso_delta = sv.value.get("dso_delta")
        assert dso_delta is not None
        # DSO current = 200/1000*365 = 73
        # DSO prior = 100/1000*365 = 36.5
        # Delta = (73-36.5)/36.5*100 = 100%
        assert dso_delta > 10.0

    def test_earnings_quality_missing_inputs(self) -> None:
        """Missing OCF -> partial result with explanation."""
        items = [
            _make_item("net_income", 100.0),
            _make_item("total_assets", 1000.0),
        ]
        stmts = _build_statements(items)
        sv, report = compute_earnings_quality(stmts)
        # Should still return something, but missing accruals and ocf_ni.
        if sv is not None:
            assert sv.value.get("accruals_ratio") is None
            assert sv.value.get("ocf_to_ni") is None
        # Report should note missing fields.
        assert "accruals_ratio" in report.missing_fields

    def test_quality_score_summary(self) -> None:
        """Multiple red flags -> WEAK or RED_FLAG overall."""
        # High accruals + low OCF/NI + low CFA = 3 flags -> RED_FLAG.
        items = [
            _make_item("net_income", 200.0),
            _make_item("operating_cash_flow", 30.0),  # OCF/NI = 0.15
            _make_item("total_assets", 1000.0),
            _make_item("capital_expenditures", 100.0),
            _make_item("dividends_paid", 50.0),
        ]
        stmts = _build_statements(items)
        sv, _ = compute_earnings_quality(stmts)
        assert sv is not None
        quality = sv.value.get("quality_score")
        assert quality is not None
        # 3.0 = RED_FLAG
        assert quality >= 2.0  # At least WEAK.
