"""Peer metric extraction and ranking engine for BENCHMARK stage.

Defines a registry of benchmarked metrics, extracts company and peer
values from AnalysisState, and computes percentile rankings via the
percentile engine.

Metrics fall into three categories:
1. Peer data (from PeerCompany model): market_cap, revenue
2. Sector baselines (from sectors.json): volatility, short_interest, leverage
3. Risk scores (company-specific): quality_score, governance_score
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, cast

from do_uw.models.scoring import MetricBenchmark
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.percentile_engine import (
    percentile_rank,
    ratio_to_baseline,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricDef:
    """Definition of a metric to benchmark.

    Each metric defines how to extract the company value and peer/baseline
    values, plus display metadata.
    """

    metric_name: str
    peer_source: str  # "peer_company", "sector_baseline", or "risk_score"
    higher_is_better: bool
    section: str
    baseline_key: str = ""  # Key in sectors.json for baseline lookup


# Metric registry: ordered list of all benchmarked metrics.
METRIC_REGISTRY: list[MetricDef] = [
    # Category 1: Peer data (from PeerCompany)
    MetricDef(
        metric_name="market_cap",
        peer_source="peer_company",
        higher_is_better=True,
        section="SECT2",
    ),
    MetricDef(
        metric_name="revenue",
        peer_source="peer_company",
        higher_is_better=True,
        section="SECT2",
    ),
    # Category 2: Sector baselines (from sectors.json)
    MetricDef(
        metric_name="volatility_90d",
        peer_source="sector_baseline",
        higher_is_better=False,
        section="SECT4",
        baseline_key="volatility_90d",
    ),
    MetricDef(
        metric_name="short_interest_pct",
        peer_source="sector_baseline",
        higher_is_better=False,
        section="SECT4",
        baseline_key="short_interest",
    ),
    MetricDef(
        metric_name="leverage_debt_ebitda",
        peer_source="sector_baseline",
        higher_is_better=False,
        section="SECT3",
        baseline_key="leverage_debt_ebitda",
    ),
    # Category 3: Risk scores
    MetricDef(
        metric_name="quality_score",
        peer_source="risk_score",
        higher_is_better=True,
        section="SECT7",
    ),
    MetricDef(
        metric_name="governance_score",
        peer_source="risk_score",
        higher_is_better=True,
        section="SECT5",
    ),
]


def _get_sector_code(state: AnalysisState) -> str:
    """Extract sector code from state, defaulting to DEFAULT."""
    if (
        state.company is not None
        and state.company.identity.sector is not None
    ):
        return str(state.company.identity.sector.value)
    return "DEFAULT"


def _extract_company_value(
    metric: MetricDef,
    state: AnalysisState,
) -> float | None:
    """Extract the company's value for a given metric from state."""
    if metric.metric_name == "market_cap":
        if state.company and state.company.market_cap:
            return float(state.company.market_cap.value)
        return None

    if metric.metric_name == "revenue":
        return _extract_revenue(state)

    if metric.metric_name == "volatility_90d":
        return _extract_volatility(state)

    if metric.metric_name == "short_interest_pct":
        return _extract_short_interest(state)

    if metric.metric_name == "leverage_debt_ebitda":
        return _extract_leverage(state)

    if metric.metric_name == "quality_score":
        if state.scoring:
            return state.scoring.quality_score
        return None

    if metric.metric_name == "governance_score":
        return _extract_governance_score(state)

    return None


def _extract_revenue(state: AnalysisState) -> float | None:
    """Extract revenue from financial statements.

    Checks income statement line items for revenue/sales labels,
    then falls back to yfinance quarterly data if available.
    """
    if not state.extracted or not state.extracted.financials:
        return None
    fin = state.extracted.financials
    stmts = fin.statements

    # Primary: income statement line items
    if stmts.income_statement is not None:
        # First pass: exact "revenue" match
        for item in stmts.income_statement.line_items:
            if "revenue" in item.label.lower():
                for period in stmts.income_statement.periods:
                    val = item.values.get(period)
                    if val is not None:
                        return float(val.value)
        # Second pass: "net sales" / "total sales" for companies like Apple
        for item in stmts.income_statement.line_items:
            label_lower = item.label.lower()
            if "sales" in label_lower and "cost" not in label_lower:
                for period in stmts.income_statement.periods:
                    val = item.values.get(period)
                    if val is not None:
                        return float(val.value)

    # Fallback: yfinance quarterly data (most recent quarter annualized
    # is unreliable, but sum of 4 quarters gives TTM revenue)
    yf_quarters = getattr(fin, "yfinance_quarterly", None)
    if yf_quarters and len(yf_quarters) >= 4:
        ttm_rev = sum(
            q.get("revenue", 0) or 0
            for q in yf_quarters[:4]
        )
        if ttm_rev > 0:
            return ttm_rev

    return None


def _extract_volatility(state: AnalysisState) -> float | None:
    """Extract 90-day volatility from market data."""
    if not state.extracted or not state.extracted.market:
        return None
    vol = state.extracted.market.stock.volatility_90d
    if vol is not None:
        return float(vol.value)
    return None


def _extract_short_interest(state: AnalysisState) -> float | None:
    """Extract short interest percentage from market data."""
    if not state.extracted or not state.extracted.market:
        return None
    si = state.extracted.market.short_interest.short_pct_float
    if si is not None:
        return float(si.value)
    return None


def _extract_leverage(state: AnalysisState) -> float | None:
    """Extract debt/EBITDA ratio from financial data."""
    if not state.extracted or not state.extracted.financials:
        return None
    leverage = state.extracted.financials.leverage
    if leverage is None:
        return None
    lev_data = leverage.value
    d2e = lev_data.get("debt_to_ebitda")
    if d2e is not None:
        return float(d2e)
    return None


def _extract_governance_score(state: AnalysisState) -> float | None:
    """Extract governance quality score."""
    if not state.extracted or not state.extracted.governance:
        return None
    gs = state.extracted.governance.governance_score
    if gs.total_score is not None:
        return float(gs.total_score.value)
    return None


def _extract_peer_values(
    metric: MetricDef,
    state: AnalysisState,
    sectors_config: dict[str, Any],
) -> tuple[list[float], float | None]:
    """Extract peer values and optional baseline for a metric.

    Returns:
        Tuple of (peer_values_list, sector_baseline_or_None).
    """
    if metric.peer_source == "peer_company":
        return _get_peer_company_values(metric, state)

    if metric.peer_source == "sector_baseline":
        return _get_sector_baseline_values(metric, state, sectors_config)

    # risk_score: no peer distribution, just baseline comparison
    return ([], None)


def _get_peer_company_values(
    metric: MetricDef,
    state: AnalysisState,
) -> tuple[list[float], float | None]:
    """Get values from PeerCompany list for a given metric."""
    if (
        not state.extracted
        or not state.extracted.financials
        or not state.extracted.financials.peer_group
    ):
        return ([], None)

    peers = state.extracted.financials.peer_group.peers
    values: list[float] = []

    for peer in peers:
        val: float | None = None
        if metric.metric_name == "market_cap":
            val = peer.market_cap
        elif metric.metric_name == "revenue":
            val = peer.revenue
        if val is not None:
            values.append(val)

    return (values, None)


def _get_sector_baseline_values(
    metric: MetricDef,
    state: AnalysisState,
    sectors_config: dict[str, Any],
) -> tuple[list[float], float | None]:
    """Get sector baseline value for a metric.

    For sector baseline metrics, we compare company value against the
    sector "normal" or "typical" value. No peer distribution is used.
    """
    sector_code = _get_sector_code(state)
    raw_section: Any = sectors_config.get(metric.baseline_key, {})

    if not isinstance(raw_section, dict):
        return ([], None)
    section = cast(dict[str, Any], raw_section)

    # Try sector-specific, then DEFAULT
    raw_data: Any = section.get(sector_code, section.get("DEFAULT"))
    if raw_data is None or not isinstance(raw_data, dict):
        return ([], None)
    sector_data = cast(dict[str, Any], raw_data)

    # Different sections use different key names for baseline
    baseline: float | None = None
    for key in ("normal", "typical"):
        raw_val: Any = sector_data.get(key)
        if raw_val is not None:
            baseline = float(cast(float, raw_val))
            break

    return ([], baseline)


def compute_peer_rankings(
    state: AnalysisState,
    sectors_config: dict[str, Any],
) -> tuple[dict[str, float], dict[str, MetricBenchmark]]:
    """Compute peer rankings and detailed metric benchmarks.

    For each metric in METRIC_REGISTRY:
    1. Extract company value from state
    2. Extract peer/baseline values
    3. Compute percentile rank using percentile_engine
    4. Build MetricBenchmark entry

    Args:
        state: Current analysis state with extracted data.
        sectors_config: Full sectors.json configuration.

    Returns:
        Tuple of:
        - peer_rankings: dict mapping metric_name -> percentile rank
          (for backward compat with BenchmarkResult.peer_rankings)
        - metric_details: dict mapping metric_name -> MetricBenchmark
    """
    peer_rankings: dict[str, float] = {}
    metric_details: dict[str, MetricBenchmark] = {}

    for metric in METRIC_REGISTRY:
        company_value = _extract_company_value(metric, state)

        if company_value is None:
            logger.debug(
                "Skipping metric %s: no company value", metric.metric_name,
            )
            metric_details[metric.metric_name] = MetricBenchmark(
                metric_name=metric.metric_name,
                higher_is_better=metric.higher_is_better,
                section=metric.section,
            )
            continue

        peer_values, baseline = _extract_peer_values(
            metric, state, sectors_config,
        )

        # Compute percentile rank
        pct_rank: float | None = None
        if peer_values:
            pct_rank = percentile_rank(
                company_value,
                peer_values,
                higher_is_better=metric.higher_is_better,
            )
        elif baseline is not None:
            # No peer distribution; use ratio to baseline as proxy
            ratio = ratio_to_baseline(company_value, baseline)
            if metric.higher_is_better:
                # Higher ratio = better
                pct_rank = min(ratio * 50, 100.0)
            else:
                # Lower ratio = better (invert)
                pct_rank = min((2.0 - ratio) * 50, 100.0)
                pct_rank = max(pct_rank, 0.0)

        if pct_rank is not None:
            peer_rankings[metric.metric_name] = round(pct_rank, 1)

        metric_details[metric.metric_name] = MetricBenchmark(
            metric_name=metric.metric_name,
            company_value=company_value,
            percentile_rank=(
                round(pct_rank, 1) if pct_rank is not None else None
            ),
            peer_count=len(peer_values),
            baseline_value=baseline,
            higher_is_better=metric.higher_is_better,
            section=metric.section,
        )

    return (peer_rankings, metric_details)


__all__ = ["compute_peer_rankings"]
