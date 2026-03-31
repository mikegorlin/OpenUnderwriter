"""True percentile computation from SEC Frames API data.

Computes real cross-filer percentile rankings for direct XBRL metrics
(single concept) and derived metrics (ratio of two concepts joined by CIK).
Replaces the ratio-to-baseline proxy for financial metrics.

Per CLAUDE.md: No data acquisition in this module -- it consumes
pre-acquired Frames data from the ACQUIRE stage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from do_uw.models.scoring import FramesPercentileResult
from do_uw.stages.acquire.clients.sec_client_frames import FRAMES_METRICS
from do_uw.stages.benchmark.percentile_engine import percentile_rank

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DerivedMetricDef:
    """Definition of a derived metric computed by joining two Frames datasets.

    Attributes:
        metric_name: Internal name (e.g., "current_ratio").
        numerator_metric: Frames metric name for the numerator.
        denominator_metric: Frames metric name for the denominator.
        higher_is_better: Whether higher ratio values are favorable.
    """

    metric_name: str
    numerator_metric: str
    denominator_metric: str
    higher_is_better: bool


# Five derived metrics computed by joining two Frames datasets by CIK.
DERIVED_METRICS: list[DerivedMetricDef] = [
    DerivedMetricDef(
        "current_ratio", "current_assets", "current_liabilities", True,
    ),
    DerivedMetricDef(
        "debt_to_equity", "total_liabilities", "total_equity", False,
    ),
    DerivedMetricDef(
        "operating_margin", "operating_income", "revenue", True,
    ),
    DerivedMetricDef(
        "net_margin", "net_income", "revenue", True,
    ),
    DerivedMetricDef(
        "roe", "net_income", "total_equity", True,
    ),
]


def _compute_direct_percentile(
    company_cik: int,
    frames_data: list[dict[str, Any]],
    sic_mapping: dict[int, str],
    company_sic: str | None,
    higher_is_better: bool,
) -> FramesPercentileResult:
    """Compute percentile for a single Frames metric.

    Finds the company's value in the Frames data, then ranks it against
    all filers (overall) and same 2-digit SIC filers (sector).

    Args:
        company_cik: CIK of the target company.
        frames_data: List of entity dicts with 'cik' and 'val' keys.
        sic_mapping: CIK -> SIC code mapping for sector filtering.
        company_sic: Company's SIC code (4-digit string) or None.
        higher_is_better: Whether higher values indicate better performance.

    Returns:
        FramesPercentileResult with overall and sector percentiles.
    """
    # Find company value
    company_value: float | None = None
    for entity in frames_data:
        if entity.get("cik") == company_cik:
            company_value = float(entity["val"])
            break

    if company_value is None:
        return FramesPercentileResult(higher_is_better=higher_is_better)

    # Overall percentile: all filers
    all_values = [float(e["val"]) for e in frames_data]
    overall_pct = percentile_rank(
        company_value, all_values, higher_is_better=higher_is_better,
    )

    # Sector percentile: filter by 2-digit SIC prefix
    sector_pct: float | None = None
    sector_count = 0
    if company_sic and sic_mapping:
        sic_prefix = company_sic[:2]
        sector_values = [
            float(e["val"])
            for e in frames_data
            if sic_mapping.get(e.get("cik", -1), "")[:2] == sic_prefix
        ]
        sector_count = len(sector_values)
        if sector_count > 0:
            sector_pct = percentile_rank(
                company_value, sector_values,
                higher_is_better=higher_is_better,
            )

    return FramesPercentileResult(
        overall=round(overall_pct, 2),
        sector=round(sector_pct, 2) if sector_pct is not None else None,
        peer_count_overall=len(all_values),
        peer_count_sector=sector_count,
        company_value=company_value,
        higher_is_better=higher_is_better,
    )


def _compute_derived_percentile(
    company_cik: int,
    numerator_data: list[dict[str, Any]],
    denominator_data: list[dict[str, Any]],
    sic_mapping: dict[int, str],
    company_sic: str | None,
    higher_is_better: bool,
) -> FramesPercentileResult:
    """Compute percentile for a derived metric (ratio of two datasets).

    Inner-joins numerator and denominator by CIK, computes the ratio
    per entity, then ranks the company's ratio against all peers.

    Args:
        company_cik: CIK of the target company.
        numerator_data: Frames data for the numerator metric.
        denominator_data: Frames data for the denominator metric.
        sic_mapping: CIK -> SIC code mapping for sector filtering.
        company_sic: Company's SIC code or None.
        higher_is_better: Whether higher ratio values are favorable.

    Returns:
        FramesPercentileResult with overall and sector percentiles.
    """
    # Build denominator lookup
    denom_by_cik: dict[int, float] = {
        e["cik"]: float(e["val"]) for e in denominator_data
    }

    # Inner join + compute ratios (skip division by zero)
    ratios: dict[int, float] = {}
    for entity in numerator_data:
        cik = entity.get("cik")
        if cik is None:
            continue
        denom = denom_by_cik.get(cik)
        if denom is None or denom == 0.0:
            continue
        ratios[cik] = float(entity["val"]) / denom

    # Find company ratio
    company_value = ratios.get(company_cik)
    if company_value is None:
        return FramesPercentileResult(higher_is_better=higher_is_better)

    # Overall percentile
    all_values = list(ratios.values())
    overall_pct = percentile_rank(
        company_value, all_values, higher_is_better=higher_is_better,
    )

    # Sector percentile
    sector_pct: float | None = None
    sector_count = 0
    if company_sic and sic_mapping:
        sic_prefix = company_sic[:2]
        sector_values = [
            ratio
            for cik, ratio in ratios.items()
            if sic_mapping.get(cik, "")[:2] == sic_prefix
        ]
        sector_count = len(sector_values)
        if sector_count > 0:
            sector_pct = percentile_rank(
                company_value, sector_values,
                higher_is_better=higher_is_better,
            )

    return FramesPercentileResult(
        overall=round(overall_pct, 2),
        sector=round(sector_pct, 2) if sector_pct is not None else None,
        peer_count_overall=len(all_values),
        peer_count_sector=sector_count,
        company_value=round(company_value, 6),
        higher_is_better=higher_is_better,
    )


def compute_frames_percentiles(
    frames_data: dict[str, list[dict[str, Any]]],
    company_cik: int,
    company_sic: str | None,
    sic_mapping: dict[int, str],
) -> dict[str, FramesPercentileResult]:
    """Compute all Frames-based percentile rankings.

    Processes both direct metrics (single Frames dataset) and derived
    metrics (ratio of two datasets joined by CIK).

    Args:
        frames_data: Dict keyed by metric_name -> list of entity dicts.
        company_cik: CIK of the target company.
        company_sic: Company's SIC code (4-digit string) or None.
        sic_mapping: CIK -> SIC code mapping for sector filtering.

    Returns:
        Dict keyed by metric_name -> FramesPercentileResult.
    """
    if not frames_data:
        return {}

    result: dict[str, FramesPercentileResult] = {}

    # Direct metrics: one Frames dataset per metric
    for metric_def in FRAMES_METRICS:
        data = frames_data.get(metric_def.metric_name)
        if not data:
            continue
        result[metric_def.metric_name] = _compute_direct_percentile(
            company_cik=company_cik,
            frames_data=data,
            sic_mapping=sic_mapping,
            company_sic=company_sic,
            higher_is_better=metric_def.higher_is_better,
        )

    # Derived metrics: join two datasets by CIK
    for derived in DERIVED_METRICS:
        num_data = frames_data.get(derived.numerator_metric)
        den_data = frames_data.get(derived.denominator_metric)
        if not num_data or not den_data:
            continue
        result[derived.metric_name] = _compute_derived_percentile(
            company_cik=company_cik,
            numerator_data=num_data,
            denominator_data=den_data,
            sic_mapping=sic_mapping,
            company_sic=company_sic,
            higher_is_better=derived.higher_is_better,
        )

    logger.info(
        "Frames percentiles computed: %d metrics (%d direct, %d derived)",
        len(result),
        sum(1 for m in FRAMES_METRICS if m.metric_name in result),
        sum(1 for d in DERIVED_METRICS if d.metric_name in result),
    )

    return result


__all__ = [
    "DERIVED_METRICS",
    "compute_frames_percentiles",
]
