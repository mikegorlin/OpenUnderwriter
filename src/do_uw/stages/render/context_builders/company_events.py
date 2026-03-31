"""Corporate events and 10-K YoY comparison context builders.

Extracts M&A forensics, IPO/offering exposure, restatement history,
capital changes, business changes, and 10-K year-over-year comparison
into template-ready dicts.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.formatters import (
    format_percentage,
)


def _build_corporate_events(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Build corporate events context from state data.

    Aggregates M&A forensics, IPO/offering exposure, restatement history,
    capital changes, and business changes into a template-ready dict.

    Returns (events_dict, has_data) tuple for template consumption.
    """
    prof = state.company

    # --- M&A Activity ---
    ma_dict: dict[str, Any] = {}
    ma_forensics: dict[str, Any] = {}
    if (
        state.analysis is not None
        and state.analysis.xbrl_forensics is not None
    ):
        xf = state.analysis.xbrl_forensics
        if isinstance(xf, dict):
            ma_forensics = xf.get("ma_forensics", {}) or {}
        else:
            mf = getattr(xf, "ma_forensics", None)
            if mf is not None:
                ma_forensics = (
                    mf.model_dump() if hasattr(mf, "model_dump") else {}
                )

    if ma_forensics:
        is_serial = ma_forensics.get("is_serial_acquirer", False)
        acq_years = ma_forensics.get("acquisition_years", [])
        goodwill_growth = ma_forensics.get("goodwill_growth_rate")
        acq_to_rev = ma_forensics.get("acquisition_to_revenue")
        total_spend = ma_forensics.get("total_acquisition_spend")

        ma_score = 0
        if is_serial:
            ma_score += 2
        if goodwill_growth is not None and goodwill_growth > 0.40:
            ma_score += 1
        if goodwill_growth is not None and goodwill_growth > 0.25:
            ma_score += 1

        if ma_score >= 3:
            ma_level, ma_color = "HIGH", "red"
        elif ma_score >= 1:
            ma_level, ma_color = "MODERATE", "amber"
        else:
            ma_level, ma_color = "LOW", "green"

        # Format total spend for display
        spend_fmt = "N/A"
        if total_spend is not None:
            if total_spend >= 1_000_000_000:
                spend_fmt = f"${total_spend / 1_000_000_000:.1f}B"
            elif total_spend >= 1_000_000:
                spend_fmt = f"${total_spend / 1_000_000:.0f}M"
            else:
                spend_fmt = f"${total_spend:,.0f}"

        ma_dict = {
            "score": ma_score,
            "level": ma_level,
            "color": ma_color,
            "acquisition_count": len(acq_years),
            "acquisition_years": acq_years,
            "is_serial_acquirer": is_serial,
            "total_acquisition_spend": spend_fmt,
            "goodwill_growth_rate": (
                f"{goodwill_growth:.1%}" if goodwill_growth is not None else "N/A"
            ),
            "acquisition_to_revenue": (
                f"{acq_to_rev:.1%}" if acq_to_rev is not None else "N/A"
            ),
        }

    # Enrich with BIZ.EVENT signals if available
    event_signals = safe_get_signals_by_prefix(signal_results, "BIZ.EVENT.")
    for sig in event_signals:
        if sig.status == "TRIGGERED":
            _level = signal_to_display_level(sig.status, sig.threshold_level)

    # --- IPO / Offering Exposure ---
    ipo_dict: dict[str, Any] = {}
    years_public = None
    if prof is not None and prof.years_public is not None:
        years_public = prof.years_public.value
    if years_public is not None:
        in_ipo_window = years_public <= 3
        ipo_dict = {
            "years_public": years_public,
            "in_ipo_window": in_ipo_window,
            "level": "HIGH" if in_ipo_window else "LOW",
            "color": "red" if in_ipo_window else "green",
        }

    # --- Restatement History ---
    restatement_dict: dict[str, Any] = {}
    if state.extracted is not None:
        audit_data = state.extracted.text_signals.get("audit_concerns", {}) or {}
        has_restatement = bool(audit_data.get("has_restatement"))
        material_weakness = bool(audit_data.get("material_weakness"))
        if has_restatement or material_weakness:
            restatement_dict = {
                "has_restatement": has_restatement,
                "material_weakness": material_weakness,
                "level": "HIGH" if has_restatement else "MODERATE",
                "color": "red" if has_restatement else "amber",
            }

    # --- Capital Changes ---
    capital_changes: list[str] = []
    if state.extracted is not None:
        cap_data = state.extracted.text_signals.get("capital_structure_changes", {}) or {}
        if isinstance(cap_data, dict):
            changes_list = cap_data.get("changes", [])
            if isinstance(changes_list, list):
                capital_changes = [str(c) for c in changes_list if c]

    # --- Business Changes ---
    # Filter out raw 8-K filing date dumps and keyword detections;
    # summarize 8-K activity as a single count, and skip "Detected keyword" entries.
    business_changes: list[str] = []
    eight_k_count = 0
    eight_k_latest: str | None = None
    if prof is not None:
        for sv_change in prof.business_changes:
            val = str(sv_change.value if hasattr(sv_change, "value") else sv_change).strip()
            if not val:
                continue
            # Count 8-K filings instead of listing each date
            if val.startswith("8-K filed"):
                eight_k_count += 1
                # Track latest date (first entry is most recent)
                if eight_k_latest is None:
                    date_part = val.replace("8-K filed ", "").strip()
                    if date_part:
                        eight_k_latest = date_part
                continue
            # Skip raw keyword detections — these are noise, not actionable
            if val.startswith("Detected keyword:"):
                continue
            # Keep substantive changes (M&A activity indicated, etc.)
            business_changes.append(val)
    # Add summarized 8-K activity if any were filed
    if eight_k_count > 0:
        summary = f"{eight_k_count} current event filings (8-K)"
        if eight_k_latest:
            summary += f", most recent {eight_k_latest}"
        business_changes.insert(0, summary)

    has_data = bool(
        ma_dict or ipo_dict or restatement_dict or capital_changes or business_changes
    )

    return {
        "ma_activity": ma_dict,
        "ipo_exposure": ipo_dict,
        "restatements": restatement_dict,
        "capital_changes": capital_changes,
        "business_changes": business_changes,
    }, has_data


def extract_ten_k_yoy(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract 10-K year-over-year comparison data for template.

    Data lineage:
    - yoy_summary counts: DISC.YOY.new_risk_factors, DISC.YOY.removed_risk_factors,
      DISC.YOY.escalated_risk_factors (via signal_results for threshold status)
    - controls_change: DISC.YOY.material_weakness, DISC.YOY.controls_changed
    - legal_delta: DISC.YOY.legal_proceedings_delta
    - risk_changes/disclosure_changes: detail data from extracted.ten_k_yoy
      (display facts, not evaluations)
    """
    if state.extracted is None or state.extracted.ten_k_yoy is None:
        return {}

    yoy = state.extracted.ten_k_yoy

    # Pull signal statuses for threshold-driven rendering
    signal_statuses: dict[str, str] = {}
    if state.analysis is not None and state.analysis.signal_results:
        for sig_id, result in state.analysis.signal_results.items():
            if sig_id.startswith("DISC.YOY."):
                status = result.get("status") if isinstance(result, dict) else getattr(result, "status", None)
                if status is not None:
                    signal_statuses[sig_id] = str(status)

    # Enrich with EXEC.* signals if available
    exec_signals = safe_get_signals_by_prefix(signal_results, "EXEC.")
    for sig in exec_signals:
        if sig.status == "TRIGGERED":
            _level = signal_to_display_level(sig.status, sig.threshold_level)

    _CHANGE_COLORS: dict[str, str] = {
        "NEW": "amber",
        "REMOVED": "red",
        "ESCALATED": "red",
        "DE_ESCALATED": "green",
        "UNCHANGED": "gray",
        "REORGANIZED": "blue",
        "CONSOLIDATED_INTO": "blue",
    }

    risk_changes = []
    for rc in yoy.risk_factor_changes:
        if rc.change_type in ("UNCHANGED", "CONSOLIDATED_INTO"):
            continue
        entry: dict[str, Any] = {
            "title": rc.title,
            "category": rc.category,
            "change_type": rc.change_type,
            "badge_color": _CHANGE_COLORS.get(rc.change_type, "gray"),
            "current_severity": rc.current_severity,
            "prior_severity": rc.prior_severity or "N/A",
            "summary": rc.summary,
        }
        if rc.change_type == "REORGANIZED" and rc.prior_title:
            entry["prior_title"] = rc.prior_title
        risk_changes.append(entry)

    disclosure_changes = []
    for dc in yoy.disclosure_changes:
        disclosure_changes.append({
            "section": dc.section.replace("_", " ").title(),
            "change_type": dc.change_type,
            "description": dc.description,
            "do_relevance": dc.do_relevance,
        })

    controls_change = None
    if yoy.material_weakness_change == "APPEARED":
        controls_change = "Material weakness APPEARED -- high D&O relevance"
    elif yoy.material_weakness_change == "REMEDIATED":
        controls_change = "Material weakness REMEDIATED"
    elif yoy.controls_changed:
        controls_change = "Internal controls disclosures changed"

    return {
        "yoy_summary": {
            "current_year": yoy.current_year,
            "prior_year": yoy.prior_year,
            "new_risks": yoy.new_risk_count,
            "removed_risks": yoy.removed_risk_count,
            "escalated_risks": yoy.escalated_risk_count,
            "reorganized_risks": yoy.reorganized_risk_count,
            "legal_delta": yoy.legal_proceedings_delta,
        },
        "risk_changes": risk_changes,
        "disclosure_changes": disclosure_changes,
        "controls_change": controls_change,
        "signal_statuses": signal_statuses,
    }


__all__ = [
    "_build_corporate_events",
    "extract_ten_k_yoy",
]
