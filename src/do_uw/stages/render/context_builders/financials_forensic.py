"""Forensic dashboard context builder for XBRL forensic analysis rendering.

Builds template-ready context from XBRLForensics (Phase 69) results,
including color-banded severity cards and Beneish M-Score component table.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.models.xbrl_forensics import (
    BeneishDecomposition,
    ForensicMetric,
    XBRLForensics,
)
from do_uw.stages.render.context_builders._signal_fallback import safe_get_result

logger = logging.getLogger(__name__)

_ZONE_SEVERITY: dict[str, str] = {
    "danger": "critical",
    "warning": "warning",
    "safe": "normal",
    "insufficient_data": "normal",
    "not_applicable": "normal",
}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "normal": 2}

_SEVERITY_COLORS: dict[str, str] = {
    "critical": "var(--do-risk-red, #dc2626)",
    "warning": "var(--do-risk-amber, #d97706)",
    "normal": "var(--do-risk-green, #16a34a)",
}

_BAND_LABELS: dict[str, str] = {
    "critical": "Critical Findings",
    "warning": "Elevated Concerns",
    "normal": "Normal Range",
}

# (module_name, display_name, list of (field_name, metric_label))
_MODULE_DEFS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("balance_sheet", "Balance Sheet Health", [
        ("goodwill_to_assets", "Goodwill / Assets"),
        ("intangible_concentration", "Intangible Concentration"),
        ("off_balance_sheet_ratio", "Off-Balance Sheet Exposure"),
        ("cash_conversion_cycle", "Cash Conversion Cycle"),
        ("working_capital_volatility", "Working Capital Volatility"),
    ]),
    ("capital_allocation", "Capital Allocation", [
        ("roic", "Return on Invested Capital"),
        ("acquisition_effectiveness", "Acquisition Effectiveness"),
        ("buyback_timing", "Buyback Timing Quality"),
        ("dividend_sustainability", "Dividend Sustainability"),
    ]),
    ("debt_tax", "Debt & Tax Structure", [
        ("interest_coverage", "Interest Coverage Trajectory"),
        ("debt_maturity_concentration", "Debt Maturity Concentration"),
        ("etr_anomaly", "Effective Tax Rate Anomaly"),
        ("deferred_tax_growth", "Deferred Tax Liability Growth"),
        ("pension_underfunding", "Pension Underfunding"),
    ]),
    ("revenue", "Revenue Quality", [
        ("deferred_revenue_divergence", "Deferred Revenue Divergence"),
        ("channel_stuffing_indicator", "Channel Stuffing Indicator"),
        ("margin_compression", "Margin Compression"),
        ("ocf_revenue_ratio", "OCF / Revenue Ratio"),
    ]),
    ("earnings_quality", "Earnings Quality", [
        ("sloan_accruals", "Sloan Accrual Anomaly"),
        ("cash_flow_manipulation", "Cash Flow Manipulation"),
        ("sbc_revenue_ratio", "Stock Comp / Revenue"),
        ("non_gaap_gap", "Non-GAAP Divergence"),
    ]),
]

# Map forensic field names to signal IDs for D&O context extraction
_FORENSIC_FIELD_TO_SIGNAL: dict[str, str] = {
    "goodwill_to_assets": "FIN.FORENSIC.goodwill_impairment_risk",
    "intangible_concentration": "FIN.FORENSIC.intangible_concentration",
    "off_balance_sheet_ratio": "FIN.FORENSIC.off_balance_sheet",
    "cash_conversion_cycle": "FIN.FORENSIC.cash_conversion_cycle",
    "working_capital_volatility": "FIN.FORENSIC.working_capital_volatility",
    "roic": "FIN.FORENSIC.roic_decline",
    "acquisition_effectiveness": "FIN.FORENSIC.acquisition_effectiveness",
    "buyback_timing": "FIN.FORENSIC.buyback_timing",
    "dividend_sustainability": "FIN.FORENSIC.dividend_sustainability",
    "interest_coverage": "FIN.FORENSIC.interest_coverage_decline",
    "debt_maturity_concentration": "FIN.FORENSIC.debt_maturity_concentration",
    "etr_anomaly": "FIN.FORENSIC.etr_anomaly",
    "deferred_tax_growth": "FIN.FORENSIC.deferred_tax_growth",
    "pension_underfunding": "FIN.FORENSIC.pension_underfunding",
    "deferred_revenue_divergence": "FIN.FORENSIC.deferred_revenue_divergence",
    "channel_stuffing_indicator": "FIN.FORENSIC.channel_stuffing",
    "margin_compression": "FIN.FORENSIC.margin_compression",
    "ocf_revenue_ratio": "FIN.FORENSIC.ocf_revenue_ratio",
    "sloan_accruals": "FIN.FORENSIC.sloan_accruals",
    "cash_flow_manipulation": "FIN.FORENSIC.cash_flow_manipulation",
    "sbc_revenue_ratio": "FIN.FORENSIC.sbc_dilution",
    "non_gaap_gap": "FIN.FORENSIC.non_gaap_gap",
}


def _metric_to_finding(
    metric: ForensicMetric, label: str, *, do_context: str = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "value": f"{metric.value:.2f}" if metric.value is not None else "N/A",
        "zone": metric.zone,
        "trend": metric.trend or "N/A",
        "severity": _ZONE_SEVERITY.get(metric.zone, "normal"),
        "do_context": do_context,
    }


def _score_module(findings: list[dict[str, Any]]) -> tuple[float, str, str]:
    """Compute composite score (0-100), overall zone, and worst finding text."""
    zone_scores = {"danger": 100, "warning": 60, "safe": 20, "insufficient_data": 0, "not_applicable": 0}
    scored = [f for f in findings if f["zone"] not in ("insufficient_data", "not_applicable")]

    if not scored:
        return 0.0, "insufficient_data", "No data available"

    total = sum(zone_scores.get(f["zone"], 0) for f in scored)
    composite = total / len(scored)

    if composite >= 70:
        zone = "danger"
    elif composite >= 40:
        zone = "warning"
    else:
        zone = "safe"

    # Worst finding = highest severity
    worst = max(scored, key=lambda f: zone_scores.get(f["zone"], 0))
    return round(composite, 1), zone, f"{worst['label']}: {worst['zone']}"

def _build_forensic_modules(
    forensics: XBRLForensics,
    signal_results: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for attr_name, display_name, field_defs in _MODULE_DEFS:
        sub_model = getattr(forensics, attr_name, None)
        if sub_model is None:
            continue

        findings: list[dict[str, Any]] = []
        for field_name, label in field_defs:
            metric = getattr(sub_model, field_name, None)
            if metric is not None and isinstance(metric, ForensicMetric):
                # Extract D&O context from corresponding signal
                do_ctx = ""
                sig_id = _FORENSIC_FIELD_TO_SIGNAL.get(field_name)
                if sig_id and signal_results:
                    sig = safe_get_result(signal_results, sig_id)
                    if sig and sig.do_context:
                        do_ctx = sig.do_context
                findings.append(_metric_to_finding(metric, label, do_context=do_ctx))

        if not findings:
            continue
        composite, zone, worst = _score_module(findings)
        severity = _ZONE_SEVERITY.get(zone, "normal")

        modules.append({
            "name": display_name,
            "composite_score": composite,
            "zone": zone,
            "severity": severity,
            "worst_finding": worst,
            "findings": findings,
        })

    return modules

def _group_into_bands(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group sorted modules into severity bands, hiding empty bands."""
    modules.sort(key=lambda m: _SEVERITY_ORDER.get(m["severity"], 2))
    bands: list[dict[str, Any]] = []
    for sev in ("critical", "warning", "normal"):
        band_modules = [m for m in modules if m["severity"] == sev]
        if band_modules:
            bands.append({
                "severity": sev,
                "label": _BAND_LABELS[sev],
                "color": _SEVERITY_COLORS[sev],
                "modules": band_modules,
            })
    return bands


# (field_name, code, full_name, threshold, higher_is_worse)
_BENEISH_COMPONENTS: list[tuple[str, str, str, float, bool]] = [
    ("dsri", "DSRI", "Days Sales in Receivables Index", 1.031, True),
    ("gmi", "GMI", "Gross Margin Index", 1.014, True),
    ("aqi", "AQI", "Asset Quality Index", 1.039, True),
    ("sgi", "SGI", "Sales Growth Index", 1.134, True),
    ("depi", "DEPI", "Depreciation Index", 1.001, True),
    ("sgai", "SGAI", "SGA Expense Index", 1.054, True),
    ("lvgi", "LVGI", "Leverage Index", 1.111, True),
    ("tata", "TATA", "Total Accruals to Total Assets", 0.018, True),
]


def _build_beneish_context(beneish: BeneishDecomposition) -> dict[str, Any]:
    if beneish.composite_score is None:
        return {"has_data": False}

    components: list[dict[str, Any]] = []
    for field, code, name, threshold, higher_worse in _BENEISH_COMPONENTS:
        val = getattr(beneish, field, None)
        if val is None:
            components.append({
                "code": code,
                "name": name,
                "value": None,
                "value_str": "N/A",
                "threshold": threshold,
                "pass": True,  # no data = not flagged
            })
            continue

        if higher_worse:
            passes = val <= threshold
        else:
            passes = val >= threshold

        components.append({
            "code": code,
            "name": name,
            "value": val,
            "value_str": f"{val:.3f}",
            "threshold": threshold,
            "pass": passes,
        })

    # Overall zone
    m = beneish.composite_score
    if m > -1.78:
        zone = "manipulation_likely"
    elif m > -2.22:
        zone = "grey_zone"
    else:
        zone = "manipulation_unlikely"

    return {
        "has_data": True,
        "m_score": round(m, 2),
        "m_score_str": f"{m:.2f}",
        "zone": zone,
        "primary_driver": beneish.primary_driver,
        "components": components,
    }


def build_forensic_dashboard_context(
    state: AnalysisState,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build forensic dashboard context from XBRL forensic analysis results."""
    empty: dict[str, Any] = {
        "has_data": False,
        "bands": [],
        "beneish": {"has_data": False},
    }

    analysis = state.analysis
    if analysis is None or analysis.xbrl_forensics is None:
        return empty
    raw = analysis.xbrl_forensics
    try:
        if isinstance(raw, dict):
            forensics = XBRLForensics.model_validate(raw)
        else:
            forensics = raw  # type: ignore[assignment]
    except Exception:
        logger.warning("Failed to parse xbrl_forensics data")
        return empty
    modules = _build_forensic_modules(forensics, signal_results)
    bands = _group_into_bands(modules)
    beneish_ctx = _build_beneish_context(forensics.beneish)
    return {
        "has_data": bool(bands) or beneish_ctx.get("has_data", False),
        "bands": bands,
        "beneish": beneish_ctx,
    }


__all__ = ["build_forensic_dashboard_context"]
