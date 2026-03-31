"""Canonical Metrics Registry -- single authoritative source for cross-section metrics.

Eliminates cross-section contradictions (revenue shown as $3.05B in one section,
$2.98B in another) by computing each metric exactly once with explicit XBRL-first
source priority and full provenance tracking.

Exports:
    MetricValue: Frozen Pydantic model for a single metric with provenance.
    CanonicalMetrics: Frozen Pydantic model holding all canonical metrics.
    build_canonical_metrics: Compute all metrics from AnalysisState.

Usage:
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics
    metrics = build_canonical_metrics(state)
    print(metrics.revenue.formatted)  # "$391.0B"
    print(metrics.revenue.source)     # "xbrl:10-K:FY2024"
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class MetricValue(BaseModel):
    """A single metric with provenance tracking.

    Immutable (frozen) so metrics cannot be silently mutated after computation.
    """

    model_config = ConfigDict(frozen=True)

    raw: float | int | str | None = None
    formatted: str = "N/A"
    source: str = "none"
    confidence: str = "LOW"
    as_of: str = ""


class CanonicalMetrics(BaseModel):
    """All canonical metrics for a single company analysis.

    Every field defaults to MetricValue() so missing data never crashes.
    Frozen to prevent mutation after build.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    company_name: MetricValue = MetricValue()
    ticker: MetricValue = MetricValue()
    exchange: MetricValue = MetricValue()
    sic_code: MetricValue = MetricValue()
    sic_description: MetricValue = MetricValue()
    ceo_name: MetricValue = MetricValue()

    # Financial
    revenue: MetricValue = MetricValue()
    revenue_growth_yoy: MetricValue = MetricValue()
    net_income: MetricValue = MetricValue()
    total_assets: MetricValue = MetricValue()
    total_liabilities: MetricValue = MetricValue()
    total_debt: MetricValue = MetricValue()
    cash_and_equivalents: MetricValue = MetricValue()
    market_cap: MetricValue = MetricValue()
    shares_outstanding: MetricValue = MetricValue()
    employees: MetricValue = MetricValue()

    # Market
    stock_price: MetricValue = MetricValue()
    high_52w: MetricValue = MetricValue()
    low_52w: MetricValue = MetricValue()
    beta: MetricValue = MetricValue()

    # Scoring
    overall_score: MetricValue = MetricValue()
    tier: MetricValue = MetricValue()


# ---------------------------------------------------------------------------
# Re-export helpers used by tests and resolvers
# ---------------------------------------------------------------------------


def _sv(obj: Any) -> Any:
    """Unwrap SourcedValue to its primitive .value, or return raw."""
    if obj is None:
        return None
    return getattr(obj, "value", obj)


def _xbrl_line_item(
    state: AnalysisState,
    stmt_attr: str,
    field_names: tuple[str, ...],
) -> tuple[float | None, str]:
    """Extract a value from XBRL financial statements.

    Delegates to the resolver module's implementation.
    """
    from do_uw.stages.render._canonical_resolvers import (
        _xbrl_line_item as _impl,
    )
    return _impl(state, stmt_attr, field_names)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------


def build_canonical_metrics(state: AnalysisState) -> CanonicalMetrics:
    """Compute all canonical metrics from AnalysisState.

    Each resolver is wrapped in try/except so one failure doesn't crash
    the whole registry. Logs warnings for individual resolver failures.
    """
    # Lazy import to avoid circular dependency (resolvers import MetricValue)
    from do_uw.stages.render._canonical_resolvers import (
        resolve_beta,
        resolve_ceo_name,
        resolve_company_name,
        resolve_employees,
        resolve_exchange,
        resolve_high_52w,
        resolve_low_52w,
        resolve_market_cap,
        resolve_overall_score,
        resolve_sic_code,
        resolve_sic_description,
        resolve_stock_price,
        resolve_ticker,
        resolve_tier,
    )
    from do_uw.stages.render._canonical_resolvers_fin import (
        resolve_cash,
        resolve_net_income,
        resolve_revenue,
        resolve_revenue_growth,
        resolve_shares_outstanding,
        resolve_total_assets,
        resolve_total_debt,
        resolve_total_liabilities,
    )

    resolvers: dict[str, Any] = {
        "company_name": resolve_company_name,
        "ticker": resolve_ticker,
        "exchange": resolve_exchange,
        "sic_code": resolve_sic_code,
        "sic_description": resolve_sic_description,
        "ceo_name": resolve_ceo_name,
        "revenue": resolve_revenue,
        "revenue_growth_yoy": resolve_revenue_growth,
        "net_income": resolve_net_income,
        "total_assets": resolve_total_assets,
        "total_liabilities": resolve_total_liabilities,
        "total_debt": resolve_total_debt,
        "cash_and_equivalents": resolve_cash,
        "market_cap": resolve_market_cap,
        "shares_outstanding": resolve_shares_outstanding,
        "employees": resolve_employees,
        "stock_price": resolve_stock_price,
        "high_52w": resolve_high_52w,
        "low_52w": resolve_low_52w,
        "beta": resolve_beta,
        "overall_score": resolve_overall_score,
        "tier": resolve_tier,
    }

    results: dict[str, MetricValue] = {}
    for field_name, resolver_fn in resolvers.items():
        try:
            results[field_name] = resolver_fn(state)
        except Exception:
            logger.warning(
                "Canonical metric resolver failed for '%s'",
                field_name,
                exc_info=True,
            )
            results[field_name] = MetricValue()

    return CanonicalMetrics(**results)
