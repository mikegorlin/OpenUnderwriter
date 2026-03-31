"""Data mapper for BIZ.EVENT.* corporate event signals.

Routes BIZ.EVENT signal IDs to their data from AnalysisState fields:
- M&A history from xbrl_forensics.ma_forensics
- IPO/offering exposure from capital_markets
- Restatements from audit profile
- Capital changes from capital_markets offerings
- Business changes from CompanyProfile.business_changes

Split from signal_mappers.py to stay under 500-line limit.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.signal_field_routing import narrow_result

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData


def _safe_sourced(sv: Any) -> Any:
    """Unwrap a SourcedValue, returning None if the wrapper is None."""
    if sv is None:
        return None
    if hasattr(sv, "value"):
        return sv.value
    return sv


def _get_forensic_value(
    xbrl_forensics: dict[str, Any],
    category: str,
    field: str,
) -> Any:
    """Extract a field from nested xbrl_forensics dict.

    Unlike _extract_forensic_value in signal_mappers_analytical.py,
    this handles non-ForensicMetric fields (bools, floats) directly.
    """
    cat_data = xbrl_forensics.get(category)
    if not isinstance(cat_data, dict):
        return None
    val = cat_data.get(field)
    # ForensicMetric dicts have a 'zone' key
    if isinstance(val, dict) and "zone" in val:
        if val.get("zone") == "insufficient_data":
            return None
        return val.get("value")
    return val


def _map_ma_history(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis: Any | None,
) -> dict[str, Any]:
    """Map M&A activity risk data.

    Score: 2 if serial acquirer, +1 if goodwill >40% of assets,
    +1 if goodwill growth >25%.
    """
    result: dict[str, Any] = {}
    score = 0

    xbrl_forensics: dict[str, Any] | None = None
    if analysis is not None:
        xbrl_forensics = getattr(analysis, "xbrl_forensics", None)

    if xbrl_forensics is not None:
        # Serial acquirer flag
        serial = _get_forensic_value(
            xbrl_forensics, "ma_forensics", "is_serial_acquirer"
        )
        if serial:
            score += 2

        # Goodwill to assets ratio
        gw_to_assets = _get_forensic_value(
            xbrl_forensics, "balance_sheet", "goodwill_to_assets"
        )
        if isinstance(gw_to_assets, (int, float)) and gw_to_assets > 0.40:
            score += 1

        # Goodwill growth rate
        gw_growth = _get_forensic_value(
            xbrl_forensics, "ma_forensics", "goodwill_growth_rate"
        )
        if isinstance(gw_growth, (int, float)) and gw_growth > 0.25:
            score += 1

    result["event_ma_risk_score"] = score
    return result


def _map_ipo_exposure(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis: Any | None,
) -> dict[str, Any]:
    """Map IPO/offering Section 11 exposure.

    Score = count of active Section 11 windows (0 = clear).
    """
    result: dict[str, Any] = {}
    score = 0

    mkt = extracted.market
    if mkt is not None:
        cm = mkt.capital_markets
        score = cm.active_section_11_windows or 0

    result["event_ipo_exposure_score"] = score
    return result


def _map_restatements(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis: Any | None,
) -> dict[str, Any]:
    """Map restatement and material weakness severity.

    Score: 2 for any restatement, 1 for material weakness only, 0 for clean.
    """
    result: dict[str, Any] = {}
    severity = 0

    fin = extracted.financials
    if fin is not None:
        restatement_count = (
            len(fin.audit.restatements) if fin.audit.restatements else 0
        )
        mw_count = (
            len(fin.audit.material_weaknesses)
            if fin.audit.material_weaknesses
            else 0
        )
        if restatement_count > 0:
            severity = 2
        elif mw_count > 0:
            severity = 1

    result["event_restatement_severity"] = severity
    return result


def _map_capital_changes(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis: Any | None,
) -> dict[str, Any]:
    """Map capital structure change count.

    Count = number of offerings in trailing 3-year period.
    """
    result: dict[str, Any] = {}
    count = 0

    mkt = extracted.market
    if mkt is not None:
        count = len(mkt.capital_markets.offerings_3yr)

    result["event_capital_change_count"] = count
    return result


# Pattern for generic 8-K filings that are not meaningful business changes
_GENERIC_8K_PATTERN = re.compile(
    r"^8-K\s+filed\s+\d{4}-\d{2}-\d{2}$", re.IGNORECASE
)


def _map_business_changes(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    analysis: Any | None,
) -> dict[str, Any]:
    """Map business pivots and restructurings count.

    Filters out generic '8-K filed DATE' entries -- only counts
    entries with keyword-matched substance.
    """
    result: dict[str, Any] = {}
    count = 0

    if company is not None and company.business_changes:
        for change_sv in company.business_changes:
            val = _safe_sourced(change_sv)
            if val is None:
                continue
            text = str(val).strip()
            # Skip generic 8-K entries
            if _GENERIC_8K_PATTERN.match(text):
                continue
            count += 1

    result["event_business_change_count"] = count
    return result


_EVENT_MAPPERS: dict[str, Any] = {
    "BIZ.EVENT.ma_history": _map_ma_history,
    "BIZ.EVENT.ipo_exposure": _map_ipo_exposure,
    "BIZ.EVENT.restatements": _map_restatements,
    "BIZ.EVENT.capital_changes": _map_capital_changes,
    "BIZ.EVENT.business_changes": _map_business_changes,
}


def map_event_fields(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map BIZ.EVENT signal IDs to their data from AnalysisState.

    Routes to specific mapper functions per signal, then narrows
    the result via signal_field_routing.narrow_result().
    """
    mapper = _EVENT_MAPPERS.get(signal_id)
    if mapper is None:
        return {}
    result = mapper(extracted, company, analysis)
    return narrow_result(signal_id, result, check_config)


__all__ = ["map_event_fields"]
