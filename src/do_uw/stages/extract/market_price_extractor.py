"""MARKET_PRICE extractor: validate yfinance field coverage for brain requirements.

Checks that all MARKET_PRICE required fields (from brain signals) are present
in extracted market data. This is a validation/extraction hybrid that ensures
the brain's MARKET_PRICE source requirements are satisfied.

Fields expected (from brain/signals/stock/price.yaml):
- adverse_event_count
- analyst_count
- avg_daily_volume
- beta_ratio
- current_price
- decline_from_high
- ev_ebitda
- idiosyncratic_vol
- max_drawdown_1y
- pe_ratio
- peg_ratio
- recommendation_mean
- returns_1y
- single_day_drops_count
- unexplained_drop_count
- volatility_90d
- volume_spike_count
- xbrl_market_cap
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.market import MarketSignals
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)

# Hardcoded list of MARKET_PRICE field keys from brain/signals/stock/price.yaml
MARKET_PRICE_FIELD_KEYS = {
    "adverse_event_count",
    "analyst_count",
    "avg_daily_volume",
    "beta_ratio",
    "current_price",
    "decline_from_high",
    "ev_ebitda",
    "idiosyncratic_vol",
    "max_drawdown_1y",
    "pe_ratio",
    "peg_ratio",
    "recommendation_mean",
    "returns_1y",
    "single_day_drops_count",
    "unexplained_drop_count",
    "volatility_90d",
    "volume_spike_count",
    "xbrl_market_cap",
}


def extract_market_price_coverage(
    state: AnalysisState, signals: MarketSignals | None = None
) -> tuple[dict[str, Any], ExtractionReport]:
    """Validate MARKET_PRICE field coverage and return gap report.

    Args:
        state: Pipeline state with extracted data.
        signals: Existing MarketSignals (optional). If None, reads from state.extracted.market.

    Returns:
        Tuple of (coverage_dict, extraction_report).
        coverage_dict contains:
          - present_fields: list of field keys found
          - missing_fields: list of field keys missing
          - coverage_pct: percentage of fields present
        extraction_report follows standard ExtractionReport format.
    """
    # Determine which fields are present using field_key_collector
    from do_uw.stages.extract.field_key_collector import collect_extracted_field_keys

    extracted_keys = collect_extracted_field_keys(state)

    present = MARKET_PRICE_FIELD_KEYS.intersection(extracted_keys)
    missing = MARKET_PRICE_FIELD_KEYS - extracted_keys
    coverage_pct = (
        (len(present) / len(MARKET_PRICE_FIELD_KEYS)) * 100 if MARKET_PRICE_FIELD_KEYS else 100.0
    )

    # Log results
    if missing:
        logger.warning(
            "MARKET_PRICE extractor: %d/%d fields missing: %s",
            len(missing),
            len(MARKET_PRICE_FIELD_KEYS),
            sorted(missing),
        )
    else:
        logger.info(
            "MARKET_PRICE extractor: 100%% coverage (%d fields)", len(MARKET_PRICE_FIELD_KEYS)
        )

    # Build coverage dict
    coverage_dict = {
        "present_fields": sorted(present),
        "missing_fields": sorted(missing),
        "coverage_pct": coverage_pct,
        "total_required": len(MARKET_PRICE_FIELD_KEYS),
        "extracted_count": len(present),
    }

    # Build extraction report using create_report helper
    from do_uw.stages.extract.validation import create_report

    report = create_report(
        extractor_name="market_price_coverage",
        expected=sorted(MARKET_PRICE_FIELD_KEYS),
        found=sorted(present),
        source_filing="yfinance market data",
    )

    return coverage_dict, report
