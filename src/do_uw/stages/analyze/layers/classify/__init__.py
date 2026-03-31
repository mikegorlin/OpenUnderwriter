"""Classification engine: Layer 1 of the five-layer analysis architecture.

Takes exactly 3 objective variables (market cap tier, industry sector,
IPO age) and produces a deterministic base filing rate + severity band.

All domain values are config-driven from classification.json --
zero hardcoded thresholds in Python code.

Usage:
    from do_uw.stages.analyze.layers.classify import classify_company, load_classification_config

    config = load_classification_config()
    result = classify_company(
        market_cap=50_000_000_000,
        sector_code="TECH",
        years_public=15,
        config=config,
    )
"""

from do_uw.stages.analyze.layers.classify.classification_engine import (
    classify_company,
    load_classification_config,
)

__all__ = [
    "classify_company",
    "load_classification_config",
]
