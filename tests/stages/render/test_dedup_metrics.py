"""Dedup verification tests — enforce home section rules for headline metrics.

Each headline metric has exactly one "home section" with full provenance display.
The header bar is the ONLY allowed cross-section duplicate (MCap/Revenue/Price/Employees).

Requirements: DEDUP-01, DEDUP-02, DEDUP-03, DEDUP-04
"""

from __future__ import annotations

from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "sections"


# ── DEDUP-03: Header bar contains exactly MCap, Revenue, Price, Employees ──


def test_header_bar_has_four_metrics() -> None:
    """Verify uw_analysis.html.j2 header bar has exactly the 4 allowed metrics."""
    content = (TEMPLATES / "uw_analysis.html.j2").read_text()
    assert '("MCap"' in content
    assert '("Revenue"' in content
    assert '("Price"' in content
    assert '("Employees"' in content


# ── DEDUP-04: Non-home sections have no headline metric panels ──


def test_key_stats_no_stock_price_panel() -> None:
    """key_stats.html.j2 must not display stock price as a headline panel."""
    content = (TEMPLATES / "key_stats.html.j2").read_text()
    assert "ks.stock_price" not in content
    assert "ks_stock_current" not in content
    assert "ks.low_52w" not in content
    assert "ks.high_52w" not in content


def test_identity_no_standalone_market_cap() -> None:
    """identity.html.j2 must not display market_cap as a standalone headline value."""
    content = (TEMPLATES / "identity.html.j2").read_text()
    # Market Cap was removed from the paired KV table
    assert '"Market Cap"' not in content


def test_identity_no_standalone_revenue() -> None:
    """identity.html.j2 must not display revenue as a standalone headline value."""
    content = (TEMPLATES / "identity.html.j2").read_text()
    assert '"Revenue (TTM)"' not in content


def test_company_no_market_cap_kpi_card() -> None:
    """company.html.j2 must not display market_cap as a KPI card."""
    content = (TEMPLATES / "company.html.j2").read_text()
    # KPI strip should not have Market Cap or Revenue cards
    assert '"Market Cap"' not in content


def test_company_no_revenue_kpi_card() -> None:
    """company.html.j2 must not display revenue as a KPI card."""
    content = (TEMPLATES / "company.html.j2").read_text()
    assert '"Revenue"' not in content


# ── DEDUP-02: Home sections still contain their metrics ──


def test_stock_market_is_price_home() -> None:
    """stock_market.html.j2 IS the stock price home — must contain stock_price."""
    content = (TEMPLATES / "report" / "stock_market.html.j2").read_text()
    assert "stock_price" in content


def test_page0_dashboard_is_mcap_home() -> None:
    """page0_dashboard.html.j2 IS the market cap home — must contain market_cap."""
    content = (TEMPLATES / "report" / "page0_dashboard.html.j2").read_text()
    assert "market_cap" in content
