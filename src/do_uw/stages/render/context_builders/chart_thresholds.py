"""Chart threshold extraction from signal YAML.

Reads evaluation thresholds and display.chart_thresholds from stock signal
YAML files, builds a flat dict keyed by metric name for template consumption.
Templates reference `thresholds.beta_ratio.red` instead of hardcoded `1.3`.

Fallback: If YAML loading fails, returns _FALLBACK_THRESHOLDS so rendering
never breaks.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from do_uw.brain.brain_unified_loader import load_signals

logger = logging.getLogger(__name__)


class ThresholdSpec(TypedDict):
    """Threshold specification for a single chart metric."""

    red: float
    yellow: float


# Fallback thresholds matching values previously hardcoded in templates.
# Used when BrainLoader is unavailable (e.g., during testing without YAML).
_FALLBACK_THRESHOLDS: dict[str, ThresholdSpec] = {
    "beta_ratio": {"red": 1.5, "yellow": 1.3},
    "beta_performance": {"red": 1.5, "yellow": 1.3},
    "volatility": {"red": 40.0, "yellow": 35.0},
    "idiosyncratic_vol": {"red": 30.0, "yellow": 20.0},
    "max_drawdown": {"red": -20.0, "yellow": -15.0},
    "decline_from_high": {"red": 30.0, "yellow": 15.0},
    "decline_current": {"red": 25.0, "yellow": 15.0},
    "decline_near_high": {"red": 15.0, "yellow": 10.0},
    "alpha": {"red": 15.0, "yellow": 10.0},
    "divergence": {"red": 20.0, "yellow": 10.0},
    "mdd_ratio": {"red": 1.5, "yellow": 1.0},
    "vol_ratio": {"red": 1.5, "yellow": 1.3},
    "drop_severity": {"red": -10.0, "yellow": -5.0},
    "volume_spike": {"red": 2.0, "yellow": 1.5},
    "company_specific_drops": {"red": 3.0, "yellow": 2.0},
}

# Maps signal ID -> (metric_name, evaluation_threshold_mapping).
# For signals where evaluation.thresholds directly map to a template metric.
_SIGNAL_TO_METRIC: dict[str, str] = {
    "STOCK.PRICE.beta_ratio_elevated": "beta_ratio",
    "STOCK.PRICE.technical": "volatility",
    "STOCK.PRICE.idiosyncratic_vol": "idiosyncratic_vol",
    "STOCK.PRICE.drawdown_duration": "max_drawdown",
    "STOCK.PRICE.position": "decline_from_high",
    "STOCK.PRICE.attribution": "alpha",
    "STOCK.PRICE.chart_comparison": "divergence",
}


def _extract_evaluation_thresholds(
    signal: dict[str, Any],
) -> ThresholdSpec | None:
    """Extract red/yellow numeric thresholds from evaluation.thresholds list."""
    eval_block = signal.get("evaluation")
    if not eval_block or not isinstance(eval_block, dict):
        return None

    thresholds_list = eval_block.get("thresholds")
    if not thresholds_list or not isinstance(thresholds_list, list):
        return None

    red_val: float | None = None
    yellow_val: float | None = None

    for entry in thresholds_list:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label", "")).upper()
        value = entry.get("value")
        if value is None:
            continue
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue

        if label == "RED" and red_val is None:
            red_val = num
        elif label == "YELLOW" and yellow_val is None:
            yellow_val = num

    if red_val is not None and yellow_val is not None:
        return {"red": red_val, "yellow": yellow_val}
    return None


def _extract_chart_thresholds_from_display(
    signal: dict[str, Any],
) -> dict[str, ThresholdSpec]:
    """Extract chart_thresholds from display block."""
    display = signal.get("display")
    if not display or not isinstance(display, dict):
        return {}

    chart_thresholds = display.get("chart_thresholds")
    if not chart_thresholds or not isinstance(chart_thresholds, dict):
        return {}

    result: dict[str, ThresholdSpec] = {}
    for metric_name, spec in chart_thresholds.items():
        if not isinstance(spec, dict):
            continue
        red = spec.get("red")
        yellow = spec.get("yellow")
        if red is not None and yellow is not None:
            try:
                result[metric_name] = {
                    "red": float(red),
                    "yellow": float(yellow),
                }
            except (TypeError, ValueError):
                continue
    return result


def extract_chart_thresholds(
    state: Any,
) -> dict[str, ThresholdSpec]:
    """Extract chart evaluation thresholds from signal YAML.

    Reads stock signal YAML files via BrainLoader, extracts evaluation
    thresholds and display.chart_thresholds, and builds a flat dict
    keyed by metric name.

    Args:
        state: AnalysisState (unused -- thresholds come from YAML, not state).
              Accepts None for testing / fallback.

    Returns:
        Dict mapping metric names to ThresholdSpec dicts with 'red' and
        'yellow' float values.
    """
    try:
        data = load_signals()
        signals: list[dict[str, Any]] = data.get("signals", [])
    except Exception:
        logger.warning(
            "Failed to load signals from BrainLoader; using fallback thresholds"
        )
        return dict(_FALLBACK_THRESHOLDS)

    result: dict[str, ThresholdSpec] = {}

    for signal in signals:
        signal_id = signal.get("id", "")

        # 1. Extract evaluation.thresholds -> mapped metric name
        if signal_id in _SIGNAL_TO_METRIC:
            metric_name = _SIGNAL_TO_METRIC[signal_id]
            spec = _extract_evaluation_thresholds(signal)
            if spec is not None:
                result[metric_name] = spec

        # 2. Extract display.chart_thresholds -> direct metric names
        chart_specs = _extract_chart_thresholds_from_display(signal)
        result.update(chart_specs)

    # Fill any missing metrics from fallback
    for key, fallback_spec in _FALLBACK_THRESHOLDS.items():
        if key not in result:
            result[key] = fallback_spec

    return result


# ---------------------------------------------------------------------------
# Callout aggregation: evaluate metrics against signal callout_templates
# ---------------------------------------------------------------------------

# Fallback callout templates matching text previously hardcoded in templates.
# Used when YAML loading fails (e.g., during testing without signal files).
_FALLBACK_CALLOUTS: dict[str, dict[str, str]] = {
    "beta_ratio": {
        "yellow": "Beta ratio of {value}x indicates the stock is significantly more volatile than its sector peers relative to the broader market. Higher beta amplifies loss causation arguments in SCA claims.",
        "clear": "Beta ratio within normal range relative to sector peers.",
    },
    "vol_ratio": {
        "yellow": "90-day volatility ({value}%) exceeds sector volatility by more than 30%, suggesting elevated company-specific risk not explained by sector dynamics.",
        "clear": "Volatility at or below sector average — stock behaves in line with peers, reducing company-specific risk narrative.",
    },
    "max_drawdown": {
        "red": "Maximum 1-year drawdown of {value}% exceeds the {threshold}% threshold associated with elevated SCA filing risk. Drawdowns of this magnitude create economically viable class periods for plaintiff attorneys.",
        "clear": "Maximum drawdown within normal range for sector.",
    },
    "decline_from_high": {
        "red": "Currently {value}% below 52-week high — sustained declines of this magnitude strengthen plaintiff loss causation arguments and increase settlement values.",
        "yellow": "Trading within {value}% of 52-week high — limited stock-drop exposure for SCA class period arguments.",
    },
    "company_specific_drops": {
        "yellow": "{value} company-specific drops identified (not explained by market/sector movement). Multiple idiosyncratic declines suggest company-level issues that could anchor SCA class period allegations.",
        "clear": "No significant stock declines detected in the analysis period — clean price history reduces D&O filing probability.",
    },
    "idiosyncratic_vol": {
        "red": "Idiosyncratic volatility of {value}% is elevated — a high proportion of price movement is company-specific rather than market/sector-driven, increasing exposure to securities litigation.",
    },
    "alpha": {
        "positive": "Strong 12-month alpha of +{value}% vs sector — outperformance reduces D&O exposure and strengthens management credibility.",
    },
}

# Signal ID -> callout metric key mapping (parallel to _SIGNAL_TO_METRIC for thresholds).
_CALLOUT_SIGNAL_MAP: dict[str, str] = {
    "STOCK.PRICE.beta_ratio_elevated": "beta_ratio",
    "STOCK.PRICE.technical": "vol_ratio",
    "STOCK.PRICE.drawdown_duration": "max_drawdown",
    "STOCK.PRICE.position": "decline_from_high",
    "STOCK.PRICE.unexplained_drops": "company_specific_drops",
    "STOCK.PRICE.idiosyncratic_vol": "idiosyncratic_vol",
    "STOCK.PRICE.attribution": "alpha",
}


def _load_callout_templates() -> dict[str, dict[str, str]]:
    """Load callout_templates from signal YAML display blocks.

    Returns dict mapping callout metric key -> {severity: template_string}.
    Falls back to _FALLBACK_CALLOUTS if YAML loading fails.
    """
    try:
        data = load_signals()
        signals: list[dict[str, Any]] = data.get("signals", [])
    except Exception:
        logger.warning("Failed to load signals for callouts; using fallback templates")
        return dict(_FALLBACK_CALLOUTS)

    result: dict[str, dict[str, str]] = {}
    for signal in signals:
        signal_id = signal.get("id", "")
        if signal_id not in _CALLOUT_SIGNAL_MAP:
            continue

        callout_key = _CALLOUT_SIGNAL_MAP[signal_id]
        display = signal.get("display")
        if not display or not isinstance(display, dict):
            continue

        templates = display.get("callout_templates")
        if not templates or not isinstance(templates, dict):
            continue

        result[callout_key] = {
            str(k): str(v) for k, v in templates.items()
        }

    # Fill missing from fallback
    for key, fallback in _FALLBACK_CALLOUTS.items():
        if key not in result:
            result[key] = fallback

    return result


def _fmt(val: float, fmt_type: str) -> str:
    """Format a metric value based on its type."""
    if fmt_type == "ratio":
        return f"{val:.2f}"
    if fmt_type == "pct1":
        return f"{val:.1f}"
    if fmt_type == "pct0":
        return f"{abs(val):.0f}"
    if fmt_type == "count":
        return f"{val:.0f}"
    return f"{val:.1f}"


def evaluate_chart_callouts(
    state: Any,
    metrics: dict[str, float | None],
    thresholds: dict[str, dict[str, float]],
) -> dict[str, list[str]]:
    """Evaluate chart metrics against signal callout templates.

    Reads callout_templates from signal YAML display blocks, evaluates
    each metric against thresholds, selects the appropriate severity
    template, interpolates {value}/{threshold} placeholders, and returns
    categorized lists.

    Args:
        state: AnalysisState (unused — callouts come from YAML, not state).
        metrics: Dict of metric_name -> float value from _extract_chart_metrics.
        thresholds: Dict from extract_chart_thresholds.

    Returns:
        {"flags": [...], "positives": [...]} where flags are risk callouts
        (red/yellow severity) and positives are favorable indicators.
    """
    flags: list[str] = []
    positives: list[str] = []
    templates = _load_callout_templates()

    # If thresholds is empty, load defaults
    if not thresholds:
        thresholds = dict(_FALLBACK_THRESHOLDS)

    # --- Beta ratio ---
    beta_val = metrics.get("beta_ratio")
    if beta_val is not None:
        t_beta = thresholds.get("beta_ratio", {"red": 1.5, "yellow": 1.3})
        tmpl = templates.get("beta_ratio", {})
        if beta_val > t_beta.get("yellow", 1.3):
            text = tmpl.get("yellow", "")
            if text:
                flags.append(text.replace("{value}", _fmt(beta_val, "ratio")))

    # --- Vol ratio (90d vol vs sector vol) ---
    vol_90d = metrics.get("volatility_90d")
    sector_vol = metrics.get("sector_vol_90d")
    if vol_90d is not None and sector_vol is not None:
        t_vol = thresholds.get("vol_ratio", {"red": 1.5, "yellow": 1.3})
        tmpl = templates.get("vol_ratio", {})
        if sector_vol > 0 and vol_90d > sector_vol * t_vol.get("yellow", 1.3):
            vol_pct = vol_90d * 100 if vol_90d < 1 else vol_90d
            text = tmpl.get("yellow", "")
            if text:
                flags.append(text.replace("{value}", _fmt(vol_pct, "pct1")))
        elif vol_90d <= sector_vol:
            text = tmpl.get("clear", "")
            if text:
                positives.append(text)

    # --- Max drawdown ---
    max_dd = metrics.get("max_drawdown_1y")
    if max_dd is not None:
        t_dd = thresholds.get("max_drawdown", {"red": -20.0, "yellow": -15.0})
        tmpl = templates.get("max_drawdown", {})
        if max_dd < t_dd.get("red", -20.0):
            text = tmpl.get("red", "")
            if text:
                text = text.replace("{value}", _fmt(max_dd, "pct1"))
                text = text.replace("{threshold}", _fmt(abs(t_dd.get("red", -20.0)), "pct0"))
                flags.append(text)

    # --- Decline from high ---
    decline = metrics.get("decline_from_high_pct")
    if decline is not None:
        t_dec = thresholds.get("decline_current", {"red": 25.0, "yellow": 15.0})
        t_near = thresholds.get("decline_near_high", {"red": 15.0, "yellow": 10.0})
        tmpl = templates.get("decline_from_high", {})
        if decline < -(t_dec.get("red", 25.0)):
            text = tmpl.get("red", "")
            if text:
                flags.append(text.replace("{value}", _fmt(abs(decline), "pct0")))
        elif decline > -(t_near.get("yellow", 10.0)):
            text = tmpl.get("yellow", "")
            if text:
                positives.append(text.replace("{value}", _fmt(abs(decline) if decline else 0, "pct0")))

    # --- Company-specific drops ---
    cs_drops = metrics.get("company_specific_drop_count")
    total_drops = metrics.get("total_drop_count")
    if cs_drops is not None:
        t_drops = thresholds.get("company_specific_drops", {"red": 3.0, "yellow": 2.0})
        tmpl = templates.get("company_specific_drops", {})
        if cs_drops >= t_drops.get("yellow", 2.0):
            text = tmpl.get("yellow", "")
            if text:
                flags.append(text.replace("{value}", _fmt(cs_drops, "count")))
    if total_drops is not None and total_drops == 0:
        tmpl = templates.get("company_specific_drops", {})
        text = tmpl.get("clear", "")
        if text:
            positives.append(text)

    # --- Idiosyncratic volatility ---
    idio_vol = metrics.get("idiosyncratic_vol")
    if idio_vol is not None:
        t_idio = thresholds.get("idiosyncratic_vol", {"red": 30.0, "yellow": 20.0})
        tmpl = templates.get("idiosyncratic_vol", {})
        if idio_vol > t_idio.get("red", 30.0):
            text = tmpl.get("red", "")
            if text:
                flags.append(text.replace("{value}", _fmt(idio_vol, "pct0")))

    # --- Alpha (positive signal) ---
    alpha = metrics.get("alpha_1y")
    if alpha is not None:
        t_alpha = thresholds.get("alpha", {"red": 15.0, "yellow": 10.0})
        tmpl = templates.get("alpha", {})
        if alpha > t_alpha.get("yellow", 10.0):
            text = tmpl.get("positive", "")
            if text:
                positives.append(text.replace("{value}", _fmt(alpha, "pct1")))

    return {"flags": flags, "positives": positives}


__all__ = ["ThresholdSpec", "evaluate_chart_callouts", "extract_chart_thresholds"]
