"""Post-evaluation details enrichment for SignalResult objects.

Populates the `details` field on SignalResult with structured evaluation
data that composites can read. This preserves rich data computed during
the evaluation pipeline that would otherwise be discarded after threshold
comparison.

Each enrichment function targets a specific signal prefix/domain and reads
from the ExtractedData to populate details on matching SignalResult objects.

The details field is purely additive -- threshold evaluation logic is
unchanged. The evaluator produces results exactly as before, and this
module ADDITIONALLY populates details with the structured data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.signal_results import SignalResult

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)


def enrich_signal_details(
    results: list[SignalResult],
    extracted: ExtractedData,
) -> None:
    """Enrich signal results with structured details from extracted data.

    Iterates through results and populates the `details` field for signals
    where rich source data is available. Modifies results in-place.

    Args:
        results: List of evaluated SignalResult objects.
        extracted: The ExtractedData populated by the EXTRACT stage.
    """
    # Build a lookup for fast signal_id matching
    for result in results:
        signal_id = result.signal_id

        # Dispatch to domain-specific enrichment based on signal prefix
        if signal_id.startswith("STOCK.PRICE.single_day"):
            _enrich_stock_drop_events(result, extracted)
        elif signal_id.startswith("STOCK.INSIDER."):
            _enrich_insider_trading(result, extracted)
        elif signal_id.startswith("LIT.SCA.") or signal_id.startswith("LIT.SEC."):
            _enrich_litigation(result, extracted)
        elif signal_id.startswith("FIN.DISTRESS."):
            _enrich_financial_distress(result, extracted)


# ---------------------------------------------------------------------------
# Domain-specific enrichment functions
# ---------------------------------------------------------------------------


def _enrich_stock_drop_events(
    result: SignalResult,
    extracted: ExtractedData,
) -> None:
    """Enrich STOCK.PRICE.single_day_events with per-event structured data.

    Populates details.events with date, drop_pct, trigger, sector_drop,
    company_specific, and recovery information for each stock drop event.
    """
    if extracted.market is None:
        return

    drops = extracted.market.stock_drops
    events: list[dict[str, Any]] = []

    for drop in drops.single_day_drops:
        event: dict[str, Any] = {
            "date": drop.date.value if drop.date else None,
            "drop_pct": drop.drop_pct.value if drop.drop_pct else None,
            "trigger": drop.trigger_event.value if drop.trigger_event else "unknown",
            "is_market_wide": drop.is_market_wide,
            "company_specific": not drop.is_market_wide,
            "recovery": None,  # Recovery data not on individual events
        }
        events.append(event)

    if events:
        result.details = {
            "events": events,
            "total_single_day": len(drops.single_day_drops),
            "total_multi_day": len(drops.multi_day_drops),
            "worst_single_day_pct": (
                drops.worst_single_day.drop_pct.value
                if drops.worst_single_day and drops.worst_single_day.drop_pct
                else None
            ),
        }


def _enrich_insider_trading(
    result: SignalResult,
    extracted: ExtractedData,
) -> None:
    """Enrich STOCK.INSIDER.* signals with insider trading details.

    Populates details with cluster events, net direction, transaction
    summaries, and 10b5-1 plan information.
    """
    if extracted.market is None:
        return

    insider = extracted.market.insider_analysis
    if insider is None:
        return

    details: dict[str, Any] = {}

    # Cluster events
    if insider.cluster_events:
        clusters: list[dict[str, Any]] = []
        for cluster in insider.cluster_events:
            cluster_data: dict[str, Any] = {
                "start_date": cluster.start_date if hasattr(cluster, "start_date") else None,
                "insider_count": cluster.insider_count if hasattr(cluster, "insider_count") else None,
                "insiders": cluster.insiders if hasattr(cluster, "insiders") else [],
                "total_value": cluster.total_value if hasattr(cluster, "total_value") else 0.0,
            }
            clusters.append(cluster_data)
        details["clusters"] = clusters

    # Net direction
    if insider.net_buying_selling:
        details["net_direction"] = (
            insider.net_buying_selling.value
            if hasattr(insider.net_buying_selling, "value")
            else str(insider.net_buying_selling)
        )

    # 10b5-1 plan info
    if insider.pct_10b5_1:
        details["pct_10b5_1"] = (
            insider.pct_10b5_1.value
            if hasattr(insider.pct_10b5_1, "value")
            else insider.pct_10b5_1
        )

    # Transaction count
    if insider.transactions:
        details["transaction_count"] = len(insider.transactions)

    if details:
        result.details = details


def _enrich_litigation(
    result: SignalResult,
    extracted: ExtractedData,
) -> None:
    """Enrich LIT.SCA.* and LIT.SEC.* signals with litigation details.

    Populates details with case information, SEC enforcement status,
    and settlement data.
    """
    if extracted.litigation is None:
        return

    lit = extracted.litigation
    details: dict[str, Any] = {}

    # Securities class actions
    if result.signal_id.startswith("LIT.SCA.") and lit.securities_class_actions:
        cases: list[dict[str, Any]] = []
        for case in lit.securities_class_actions:
            case_info: dict[str, Any] = {
                "case_name": case.case_name.value if case.case_name else None,
                "filing_date": case.filing_date.value if case.filing_date else None,
                "status": case.status.value if case.status else None,
                "coverage_type": case.coverage_type.value if case.coverage_type else None,
            }
            cases.append(case_info)
        details["securities_class_actions"] = cases
        details["total_sca_count"] = len(lit.securities_class_actions)

    # SEC enforcement
    if result.signal_id.startswith("LIT.SEC."):
        enforcement = lit.sec_enforcement
        details["enforcement_stage"] = (
            enforcement.current_stage.value
            if enforcement.current_stage
            else "NONE"
        )
        details["wells_notice"] = (
            enforcement.wells_notice.value
            if enforcement.wells_notice
            else False
        )

    if details:
        result.details = details


def _enrich_financial_distress(
    result: SignalResult,
    extracted: ExtractedData,
) -> None:
    """Enrich FIN.DISTRESS.* signals with financial distress components.

    Populates details with Z-score components, key ratios, and
    distress indicator values.
    """
    if extracted.financials is None:
        return

    fin = extracted.financials
    details: dict[str, Any] = {}

    # Altman Z-Score components (if available)
    if hasattr(fin, "altman_z_score") and fin.altman_z_score is not None:
        z_val = fin.altman_z_score
        details["altman_z_score"] = (
            z_val.value if hasattr(z_val, "value") else z_val
        )

    # Key liquidity ratios
    if hasattr(fin, "current_ratio") and fin.current_ratio is not None:
        cr = fin.current_ratio
        details["current_ratio"] = (
            cr.value if hasattr(cr, "value") else cr
        )

    if hasattr(fin, "quick_ratio") and fin.quick_ratio is not None:
        qr = fin.quick_ratio
        details["quick_ratio"] = (
            qr.value if hasattr(qr, "value") else qr
        )

    # Going concern flag
    if hasattr(fin, "going_concern") and fin.going_concern is not None:
        gc = fin.going_concern
        details["going_concern"] = (
            gc.value if hasattr(gc, "value") else gc
        )

    if details:
        result.details = details


__all__ = [
    "enrich_signal_details",
]
