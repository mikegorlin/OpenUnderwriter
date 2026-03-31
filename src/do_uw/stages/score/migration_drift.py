"""Migration Drift pattern engine.

Detects gradual cross-domain deterioration from quarterly XBRL data.
The "boiling frog" at the temporal level: each quarter's change is
individually small, but the cumulative multi-quarter, multi-domain
drift indicates a company sliding into higher risk territory.

Implements PatternEngine Protocol.
Phase 109-02: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import math

from do_uw.stages.score.pattern_engine import EngineResult

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------
# XBRL metric -> RAP category mapping
# ---------------------------------------------------------------
# Maps XBRL concept names to RAP categories for cross-domain drift.
# "host" = structural/balance sheet, "agent" = behavioral/income,
# "environment" = external/market (proxied by ratios).

_METRIC_RAP_MAP: dict[str, str] = {
    # Host metrics (structural/balance sheet)
    "Assets": "host",
    "Liabilities": "host",
    "StockholdersEquity": "host",
    "Goodwill": "host",
    "IntangibleAssetsNetExcludingGoodwill": "host",
    "PropertyPlantAndEquipmentNet": "host",
    "CashAndCashEquivalentsAtCarryingValue": "host",
    "CurrentAssets": "host",
    "CurrentLiabilities": "host",
    # Agent metrics (behavioral/income statement)
    "Revenues": "agent",
    "NetIncomeLoss": "agent",
    "OperatingIncomeLoss": "agent",
    "CostOfRevenue": "agent",
    "ResearchAndDevelopmentExpense": "agent",
    "SellingGeneralAndAdministrativeExpense": "agent",
    "GrossProfit": "agent",
    "OperatingExpenses": "agent",
    # Environment metrics (external proxies from XBRL ratios)
    "LongTermDebt": "environment",
    "LongTermDebtAndCapitalLeaseObligations": "environment",
    "InterestExpense": "environment",
}

# Income statement concepts (duration metrics, most-recent-first ordering)
_INCOME_CONCEPTS = {
    "Revenues",
    "NetIncomeLoss",
    "OperatingIncomeLoss",
    "CostOfRevenue",
    "ResearchAndDevelopmentExpense",
    "SellingGeneralAndAdministrativeExpense",
    "GrossProfit",
    "OperatingExpenses",
    "InterestExpense",
}


def _compute_slope(values: list[float]) -> float:
    """Compute standardized linear regression slope.

    Returns slope / std(values). If std is 0, returns 0.0.
    Uses simple OLS: slope = cov(x, y) / var(x)
    where x = [0, 1, 2, ..., n-1] (quarter indices).
    """
    n = len(values)
    if n < 2:
        return 0.0

    # Compute mean and std of values
    mean_y = sum(values) / n
    mean_x = (n - 1) / 2.0

    # Compute covariance and variance
    cov_xy = 0.0
    var_x = 0.0
    for i in range(n):
        cov_xy += (i - mean_x) * (values[i] - mean_y)
        var_x += (i - mean_x) ** 2

    if var_x == 0:
        return 0.0

    slope = cov_xy / var_x

    # Standardize by std of values
    var_y = sum((v - mean_y) ** 2 for v in values) / max(n - 1, 1)
    std_y = math.sqrt(var_y) if var_y > 0 else 0.0

    if std_y == 0:
        return 0.0

    return slope / std_y


class MigrationDriftEngine:
    """Detects gradual cross-domain deterioration from quarterly XBRL data.

    Examines 4-8 quarters of XBRL financial data, computes standardized
    regression slopes per metric, groups by RAP category (host/agent/
    environment), and fires when 2+ RAP categories show simultaneous
    deterioration (slope < threshold per quarter).

    All thresholds are configurable via constructor parameters.
    """

    def __init__(
        self,
        *,
        slope_threshold: float = -0.05,
        min_quarters: int = 4,
        min_rap_categories: int = 2,
    ) -> None:
        self._slope_threshold = slope_threshold
        self._min_quarters = min_quarters
        self._min_rap_categories = min_rap_categories

    @property
    def engine_id(self) -> str:
        return "migration_drift"

    @property
    def engine_name(self) -> str:
        return "Migration Drift"

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        state: AnalysisState | None = None,
    ) -> EngineResult:
        """Evaluate migration drift from quarterly XBRL data.

        Step 1: Extract quarterly XBRL from state. Guard insufficient data.
        Step 2: Map metrics to RAP categories.
        Step 3: Compute standardized slopes per metric.
        Step 4: Group deteriorating metrics by RAP category.
        Step 5: If 2+ RAP categories have deterioration, compute drift score.
        """
        base_result = EngineResult(
            engine_id=self.engine_id,
            engine_name=self.engine_name,
        )

        # Step 1: Extract quarterly XBRL data
        if state is None:
            return base_result.model_copy(
                update={
                    "headline": "Insufficient quarterly data (no state provided).",
                }
            )

        quarterly_xbrl = state.extracted.financials.quarterly_xbrl
        if quarterly_xbrl is None or len(quarterly_xbrl.quarters) < self._min_quarters:
            n = 0 if quarterly_xbrl is None else len(quarterly_xbrl.quarters)
            return base_result.model_copy(
                update={
                    "headline": (
                        f"Insufficient quarterly data ({n} quarters, "
                        f"need {self._min_quarters})."
                    ),
                    "metadata": {"quarters_available": n},
                }
            )

        # Step 2 & 3: Extract metric time series and compute slopes
        # Quarters are stored most-recent-first; reverse for chronological order
        quarters = list(reversed(quarterly_xbrl.quarters))
        n_quarters = len(quarters)

        metric_slopes: list[dict[str, Any]] = []

        # Collect all XBRL concepts present across quarters
        all_concepts: set[str] = set()
        for q in quarters:
            all_concepts.update(q.income.keys())
            all_concepts.update(q.balance.keys())

        for concept in all_concepts:
            if concept not in _METRIC_RAP_MAP:
                continue

            rap_category = _METRIC_RAP_MAP[concept]

            # Extract time series
            values: list[float] = []
            is_income = concept in _INCOME_CONCEPTS

            for q in quarters:
                source_dict = q.income if is_income else q.balance
                sv = source_dict.get(concept)
                if sv is not None:
                    values.append(sv.value)
                else:
                    break  # Gap in data, truncate series

            if len(values) < self._min_quarters:
                continue

            slope = _compute_slope(values)

            if slope < self._slope_threshold:
                metric_slopes.append(
                    {
                        "concept": concept,
                        "rap_category": rap_category,
                        "slope": round(slope, 4),
                        "quarters": len(values),
                        "start_value": values[0],
                        "end_value": values[-1],
                    }
                )

        # Step 4: Group deteriorating metrics by RAP category
        deteriorating_categories: dict[str, list[dict[str, Any]]] = {}
        for ms in metric_slopes:
            cat = ms["rap_category"]
            deteriorating_categories.setdefault(cat, []).append(ms)

        # Step 5: Check cross-domain drift
        if len(deteriorating_categories) < self._min_rap_categories:
            return base_result.model_copy(
                update={
                    "headline": (
                        f"No cross-domain drift detected "
                        f"({len(deteriorating_categories)} of {self._min_rap_categories} "
                        f"required RAP categories declining)."
                    ),
                    "metadata": {
                        "quarters_available": n_quarters,
                        "deteriorating_categories": list(deteriorating_categories.keys()),
                        "deteriorating_metric_count": len(metric_slopes),
                    },
                }
            )

        # Compute drift confidence
        all_slopes = [abs(ms["slope"]) for ms in metric_slopes]
        mean_abs_slope = sum(all_slopes) / len(all_slopes) if all_slopes else 0.0
        confidence = min(mean_abs_slope * 2.0, 1.0)  # Scale and cap

        # Build findings
        findings: list[dict[str, Any]] = []
        for cat, metrics in sorted(deteriorating_categories.items()):
            findings.append(
                {
                    "rap_category": cat,
                    "deteriorating_metrics": metrics,
                    "metric_count": len(metrics),
                }
            )

        # Build headline narrative
        cat_names = sorted(deteriorating_categories.keys())
        headline = (
            f"Cross-domain deterioration detected across {len(cat_names)} "
            f"RAP categories ({', '.join(cat_names)}) over {n_quarters} quarters."
        )

        return EngineResult(
            engine_id=self.engine_id,
            engine_name=self.engine_name,
            fired=True,
            confidence=round(confidence, 3),
            headline=headline,
            findings=findings,
            metadata={
                "quarters_available": n_quarters,
                "deteriorating_categories": cat_names,
                "total_deteriorating_metrics": len(metric_slopes),
                "mean_abs_slope": round(mean_abs_slope, 4),
                "slope_threshold": self._slope_threshold,
            },
        )
