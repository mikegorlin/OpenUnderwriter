"""Tests for company context overlay in LLM extraction prompts."""

from __future__ import annotations

from unittest.mock import MagicMock

from do_uw.stages.extract.llm.company_context import build_company_context


def _make_company(
    ticker: str = "AAPL",
    legal_name: str = "Apple Inc.",
    sic_code: str = "3571",
    sic_description: str = "Electronic Computers",
    sector: str = "TECH",
    market_cap: float = 3.2e12,
    filer_category: str = "large accelerated filer",
    years_public: int = 44,
    employee_count: int = 161000,
    revenue_model_type: str = "HYBRID",
) -> MagicMock:
    """Create a mock CompanyProfile."""
    sv = lambda v: MagicMock(value=v)  # noqa: E731
    identity = MagicMock()
    identity.ticker = ticker
    identity.legal_name = sv(legal_name)
    identity.sic_code = sv(sic_code)
    identity.sic_description = sv(sic_description)
    identity.sector = sv(sector)

    company = MagicMock()
    company.identity = identity
    company.market_cap = sv(market_cap)
    company.filer_category = sv(filer_category)
    company.years_public = sv(years_public)
    company.employee_count = sv(employee_count)
    company.revenue_model_type = sv(revenue_model_type)
    return company


class TestBuildCompanyContext:
    def test_returns_empty_for_none(self) -> None:
        assert build_company_context(None) == ""

    def test_includes_company_name(self) -> None:
        ctx = build_company_context(_make_company())
        assert "Apple Inc." in ctx
        assert "AAPL" in ctx

    def test_includes_sector_label(self) -> None:
        ctx = build_company_context(_make_company(sic_code="3571"))
        assert "Technology/Hardware" in ctx

    def test_includes_market_cap_tier(self) -> None:
        ctx = build_company_context(_make_company(market_cap=3.2e12))
        assert "mega-cap" in ctx
        assert "$3.2T" in ctx

    def test_includes_sector_guidance(self) -> None:
        ctx = build_company_context(_make_company(sic_code="3571"))
        assert "negative working capital" in ctx.lower() or "asset-light" in ctx.lower()

    def test_includes_mega_cap_size_context(self) -> None:
        ctx = build_company_context(_make_company(market_cap=300e9))
        assert "Mega-cap" in ctx or "mega-cap" in ctx.lower()

    def test_micro_cap_elevated_severity(self) -> None:
        ctx = build_company_context(_make_company(market_cap=100e6))
        assert "elevated severity" in ctx.lower() or "micro" in ctx.lower()

    def test_ipo_company_flagged(self) -> None:
        ctx = build_company_context(_make_company(years_public=1))
        assert "IPO" in ctx

    def test_banking_sector_context(self) -> None:
        ctx = build_company_context(_make_company(sic_code="6020"))
        assert "bank" in ctx.lower() or "financial" in ctx.lower()

    def test_biotech_sector_context(self) -> None:
        ctx = build_company_context(_make_company(sic_code="2836"))
        assert "biotech" in ctx.lower() or "pharma" in ctx.lower()

    def test_general_sector_no_crash(self) -> None:
        ctx = build_company_context(_make_company(sic_code="9999"))
        # Should not crash, just less specific context
        assert "AAPL" in ctx
