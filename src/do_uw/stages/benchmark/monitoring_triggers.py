"""Company-specific monitoring trigger computation.

Loads trigger definitions from brain/config/monitoring_triggers.yaml and
computes company-specific thresholds from actual AnalysisState data.
Phase 117-03 Task 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from do_uw.models.forward_looking import MonitoringTrigger
from do_uw.models.state import AnalysisState

_trigger_config_cache: dict[str, Any] | None = None


def _load_trigger_config() -> dict[str, Any]:
    """Load monitoring trigger definitions from brain YAML."""
    global _trigger_config_cache
    if _trigger_config_cache is not None:
        return _trigger_config_cache
    config_path = (
        Path(__file__).parent.parent.parent / "brain" / "config" / "monitoring_triggers.yaml"
    )
    with open(config_path) as f:
        _trigger_config_cache = yaml.safe_load(f)
    return _trigger_config_cache


def _sv_val(sourced: object) -> Any:
    """Extract .value from SourcedValue, or return the raw value."""
    if hasattr(sourced, "value"):
        return sourced.value
    return sourced


def compute_monitoring_triggers(state: AnalysisState) -> list[MonitoringTrigger]:
    """Compute 6 monitoring triggers with company-specific thresholds.

    Each trigger has a threshold derived from the company's actual data
    (stock support level, insider selling pace, SIC code, etc.).
    """
    config = _load_trigger_config()
    triggers_def = config.get("triggers", [])
    triggers: list[MonitoringTrigger] = []

    for tdef in triggers_def:
        trigger_id = tdef["id"]
        name = tdef["name"]
        action = tdef["action"]
        default_threshold = tdef.get("default_threshold", "")

        threshold, current_value = _compute_threshold(
            trigger_id, default_threshold, state
        )

        triggers.append(
            MonitoringTrigger(
                trigger_name=name,
                action=action,
                threshold=threshold,
                current_value=current_value,
                source=tdef.get("threshold_source", ""),
            )
        )

    return triggers


def _compute_threshold(
    trigger_id: str,
    default_threshold: str,
    state: AnalysisState,
) -> tuple[str, str]:
    """Compute company-specific threshold and current value for a trigger.

    Returns (threshold_string, current_value_string).
    """
    company_name = _get_company_name(state)

    if trigger_id == "MON-01":
        return (
            f"Any Stanford SCAC match against {company_name}",
            _get_sca_status(state),
        )

    if trigger_id == "MON-02":
        return _compute_stock_threshold(state)

    if trigger_id == "MON-03":
        return _compute_insider_threshold(state)

    if trigger_id == "MON-04":
        return (">10% miss vs guidance midpoint", _get_eps_status(state))

    if trigger_id == "MON-05":
        return ("Any CEO/CFO/COO departure", "")

    if trigger_id == "MON-06":
        return _compute_peer_sca_threshold(state)

    return (default_threshold, "")


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state."""
    if state.company and state.company.identity:
        ln = state.company.identity.legal_name
        if ln is not None:
            return str(_sv_val(ln))
    return state.ticker


def _get_sca_status(state: AnalysisState) -> str:
    """Current SCA status."""
    if state.extracted and state.extracted.litigation:
        scas = state.extracted.litigation.securities_class_actions
        if scas:
            return f"{len(scas)} active SCA(s)"
    return "No active SCA"


def _compute_stock_threshold(state: AnalysisState) -> tuple[str, str]:
    """Stock below support level trigger."""
    if state.extracted and state.extracted.market:
        stock = state.extracted.market.stock
        low = stock.low_52w
        price = stock.current_price
        if low is not None:
            low_val = _sv_val(low)
            if isinstance(low_val, (int, float)):
                threshold = f"Price below ${low_val:.2f} (52-week low)"
                current = ""
                if price is not None:
                    price_val = _sv_val(price)
                    if isinstance(price_val, (int, float)):
                        current = f"${price_val:.2f}"
                return (threshold, current)
    return ("Price below 52-week low", "")


def _compute_insider_threshold(state: AnalysisState) -> tuple[str, str]:
    """Insider selling pace threshold: >2x current quarterly rate."""
    if state.extracted and state.extracted.market:
        insider = state.extracted.market.insider_trading
        sold = insider.total_sold_value
        if sold is not None:
            sold_val = _sv_val(sold)
            if isinstance(sold_val, (int, float)) and sold_val > 0:
                quarterly_rate = sold_val / 4.0
                double_rate = quarterly_rate * 2
                threshold = f">2x current quarterly rate (>${double_rate:,.0f})"
                current = f"${quarterly_rate:,.0f}/quarter (12mo: ${sold_val:,.0f})"
                return (threshold, current)
    return (">2x current quarterly selling rate", "")


def _get_eps_status(state: AnalysisState) -> str:
    """Current EPS miss status from earnings guidance."""
    if state.extracted and state.extracted.market:
        eg = state.extracted.market.earnings_guidance
        if eg and hasattr(eg, "beat_rate") and eg.beat_rate is not None:
            br = _sv_val(eg.beat_rate)
            if isinstance(br, (int, float)):
                # beat_rate is stored as decimal (0.917 = 91.7%), convert to pct
                pct = br * 100 if br <= 1.0 else br
                return f"Beat rate: {pct:.1f}%"
    return ""


def _compute_peer_sca_threshold(state: AnalysisState) -> tuple[str, str]:
    """Peer SCA threshold using company's SIC code."""
    sic = ""
    if state.company and state.company.identity:
        sic_sv = state.company.identity.sic_code
        if sic_sv is not None:
            sic = str(_sv_val(sic_sv))
    if sic:
        return (f"Any SCAC match in SIC {sic}", f"SIC {sic}")
    return ("Any SCAC match in same SIC code", "")


__all__ = ["compute_monitoring_triggers"]
