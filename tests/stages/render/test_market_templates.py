"""Tests for market template condensation and audit overflow.

Phase 123-02: Verifies condensed market templates consume overflow keys
correctly and audit appendix is properly registered in manifest.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Paths
MANIFEST_PATH = Path("src/do_uw/brain/output_manifest.yaml")
TEMPLATE_DIR = Path("src/do_uw/templates/html")
OVERFLOW_TEMPLATE = TEMPLATE_DIR / "appendices" / "market_overflow.html.j2"
INSIDER_TEMPLATE = TEMPLATE_DIR / "sections" / "market" / "insider_trading.html.j2"
DROPS_TEMPLATE = TEMPLATE_DIR / "sections" / "market" / "stock_drops.html.j2"
CHARTS_TEMPLATE = TEMPLATE_DIR / "sections" / "market" / "stock_charts.html.j2"


class TestManifestAuditEntry:
    """Verify market_overflow is registered in manifest audit layer."""

    def test_market_overflow_in_manifest(self) -> None:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text())
        sections = manifest.get("sections", [])
        overflow = [s for s in sections if s.get("id") == "market_overflow"]
        assert len(overflow) == 1, "market_overflow section must exist in manifest"

    def test_market_overflow_is_audit_layer(self) -> None:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text())
        sections = manifest.get("sections", [])
        overflow = [s for s in sections if s.get("id") == "market_overflow"][0]
        assert overflow["layer"] == "audit", "market_overflow must be in audit layer"

    def test_market_overflow_template_path(self) -> None:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text())
        sections = manifest.get("sections", [])
        overflow = [s for s in sections if s.get("id") == "market_overflow"][0]
        assert overflow["template"] == "appendices/market_overflow.html.j2"


class TestOverflowTemplate:
    """Verify the audit overflow template exists and has key elements."""

    def test_template_file_exists(self) -> None:
        assert OVERFLOW_TEMPLATE.exists(), f"Missing: {OVERFLOW_TEMPLATE}"

    def test_has_audit_anchor(self) -> None:
        content = OVERFLOW_TEMPLATE.read_text()
        assert "audit-market-overflow" in content

    def test_no_duplicate_chart_embeds(self) -> None:
        content = OVERFLOW_TEMPLATE.read_text()
        # Charts are in main body (stock_charts.html.j2), not duplicated in overflow
        assert content.count("embed_chart") == 0

    def test_has_full_insider_table(self) -> None:
        content = OVERFLOW_TEMPLATE.read_text()
        assert "transactions_overflow" in content
        assert "other_transactions_overflow" in content

    def test_has_full_drops_table(self) -> None:
        content = OVERFLOW_TEMPLATE.read_text()
        assert "drop_events_overflow" in content


class TestInsiderOverflowLinks:
    """Verify insider template has overflow notices with audit links."""

    def test_sales_overflow_link(self) -> None:
        content = INSIDER_TEMPLATE.read_text()
        assert 'href="#audit-market-overflow"' in content
        assert "transactions_overflow" in content

    def test_other_overflow_link(self) -> None:
        content = INSIDER_TEMPLATE.read_text()
        assert "other_transactions_overflow" in content


class TestDropsOverflowLinks:
    """Verify stock drops template has overflow notice with audit link."""

    def test_drops_overflow_link(self) -> None:
        content = DROPS_TEMPLATE.read_text()
        assert 'href="#audit-market-overflow"' in content
        assert "drop_events_overflow" in content


class TestChartsInMainBody:
    """Verify stock charts template has all charts visible in main body.

    Updated: charts were restored to main body (preserve before improve rule).
    All 1Y and 5Y chart pairs must be present — nothing hidden in audit appendix.
    """

    def test_has_1y_chart(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert 'embed_chart("stock_1y"' in content

    def test_has_5y_chart(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert 'embed_chart("stock_5y"' in content

    def test_has_drawdown_charts(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert 'embed_chart("drawdown_1y"' in content
        assert 'embed_chart("drawdown_5y"' in content

    def test_has_volatility_charts(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert 'embed_chart("volatility_1y"' in content
        assert 'embed_chart("volatility_5y"' in content

    def test_has_relative_charts(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert 'embed_chart("relative_1y"' in content
        assert 'embed_chart("relative_5y"' in content

    def test_keeps_return_attribution(self) -> None:
        content = CHARTS_TEMPLATE.read_text()
        assert "Return Attribution" in content
