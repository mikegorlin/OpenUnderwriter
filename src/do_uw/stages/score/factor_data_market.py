"""Market and trading factor data helpers.

Split from factor_data.py (Phase 45, 500-line rule).

Contains data extraction functions for market and trading factors:
- get_sector_code: sector code extraction utility
- F6: Short Interest data
- F7: Volatility data
"""

from __future__ import annotations

from datetime import date
from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData


def get_sector_code(company: CompanyProfile | None) -> str:
    """Extract sector code from CompanyProfile, default to DEFAULT."""
    if company is None:
        return "DEFAULT"
    ident = company.identity
    if ident.sector is not None:
        return ident.sector.value
    return "DEFAULT"


def _get_f6_data(
    extracted: ExtractedData,
    sectors: dict[str, Any],
    company: CompanyProfile | None,
) -> dict[str, Any]:
    """Extract F6 (Short Interest) data."""
    data: dict[str, Any] = {
        "si_vs_sector_ratio": 0.0,
        "short_interest_pct": 0.0,
        "sector_baseline": 0.0,
        "si_trend_change_pct": 0.0,
        "market_cap_b": 0.0,
        "short_report_months": 999,
    }
    mkt = extracted.market
    if mkt is None:
        return data

    si = mkt.short_interest
    if si.short_pct_float is not None:
        data["short_interest_pct"] = si.short_pct_float.value

    sector_code = get_sector_code(company)
    si_baselines = sectors.get("short_interest", {})
    sector_bl = si_baselines.get(sector_code, si_baselines.get("DEFAULT", {}))
    baseline = float(sector_bl.get("normal", 3.0))
    data["sector_baseline"] = baseline

    if si.vs_sector_ratio is not None:
        data["si_vs_sector_ratio"] = si.vs_sector_ratio.value
    elif baseline > 0 and data["short_interest_pct"] > 0:
        data["si_vs_sector_ratio"] = data["short_interest_pct"] / baseline

    if si.short_seller_reports:
        for report in si.short_seller_reports:
            report_dict = report.value
            report_date_str = report_dict.get("date", "")
            if report_date_str:
                try:
                    rpt_date = date.fromisoformat(report_date_str)
                    months = (date.today() - rpt_date).days / 30.4
                    if months < data["short_report_months"]:
                        data["short_report_months"] = months
                except (ValueError, TypeError):
                    pass

    if company is not None and company.market_cap is not None:
        data["market_cap_b"] = company.market_cap.value / 1e9

    return data


def _get_f7_data(
    extracted: ExtractedData,
    sectors: dict[str, Any],
    company: CompanyProfile | None,
) -> dict[str, Any]:
    """Extract F7 (Volatility) data."""
    data: dict[str, Any] = {
        "vol_vs_sector_ratio": 0.0,
        "volatility_90d": 0.0,
        "sector_volatility": 0.0,
        "extreme_days": 0,
        "vol_trend_change_pct": 0.0,
    }
    mkt = extracted.market
    if mkt is None:
        return data

    if mkt.stock.volatility_90d is not None:
        data["volatility_90d"] = mkt.stock.volatility_90d.value

    sector_code = get_sector_code(company)
    vol_baselines = sectors.get("volatility_90d", {})
    sector_bl = vol_baselines.get(sector_code, vol_baselines.get("DEFAULT", {}))
    sector_vol = float(sector_bl.get("typical", 2.5))
    data["sector_volatility"] = sector_vol

    if sector_vol > 0 and data["volatility_90d"] > 0:
        data["vol_vs_sector_ratio"] = data["volatility_90d"] / sector_vol

    data["extreme_days"] = len(mkt.stock.single_day_events)
    return data
