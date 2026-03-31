"""Severity model calibration report against known landmark settlements.

Runs the severity model on ~20 known securities class action settlements
from Cornerstone Research annual reports and computes error metrics on
a log10 scale. Produces a self-contained HTML comparison report.

Phase 108 Plan 02 Task 1.
"""

from __future__ import annotations

import html as html_module
import math
from typing import Any

from do_uw.stages.score.damages_estimation import (
    apply_allegation_modifier,
    compute_base_damages,
)
from do_uw.stages.score.settlement_regression import (
    predict_settlement_regression,
)

__all__ = [
    "KNOWN_SETTLEMENTS",
    "generate_severity_calibration_report",
]


# ---------------------------------------------------------------------------
# Known settlements for calibration (Cornerstone annual reports)
# ---------------------------------------------------------------------------

KNOWN_SETTLEMENTS: list[dict[str, Any]] = [
    {"name": "Enron", "settlement": 7_200_000_000, "market_cap": 65_000_000_000,
     "drop_pct": 0.99, "allegation": "financial_restatement", "year": 2005},
    {"name": "WorldCom", "settlement": 6_200_000_000, "market_cap": 175_000_000_000,
     "drop_pct": 0.99, "allegation": "financial_restatement", "year": 2005},
    {"name": "Tyco", "settlement": 3_200_000_000, "market_cap": 100_000_000_000,
     "drop_pct": 0.80, "allegation": "financial_restatement", "year": 2007},
    {"name": "Cendant", "settlement": 3_200_000_000, "market_cap": 36_000_000_000,
     "drop_pct": 0.47, "allegation": "financial_restatement", "year": 2000},
    {"name": "Bank of America/Merrill", "settlement": 2_430_000_000,
     "market_cap": 150_000_000_000, "drop_pct": 0.60,
     "allegation": "financial_restatement", "year": 2012},
    {"name": "Household International", "settlement": 1_575_000_000,
     "market_cap": 26_000_000_000, "drop_pct": 0.50,
     "allegation": "financial_restatement", "year": 2006},
    {"name": "AOL Time Warner", "settlement": 1_500_000_000,
     "market_cap": 200_000_000_000, "drop_pct": 0.75,
     "allegation": "financial_restatement", "year": 2006},
    {"name": "Nortel Networks", "settlement": 1_074_000_000,
     "market_cap": 230_000_000_000, "drop_pct": 0.97,
     "allegation": "financial_restatement", "year": 2006},
    {"name": "Royal Ahold", "settlement": 1_100_000_000,
     "market_cap": 30_000_000_000, "drop_pct": 0.63,
     "allegation": "financial_restatement", "year": 2005},
    {"name": "McKesson/HBOC", "settlement": 1_050_000_000,
     "market_cap": 18_000_000_000, "drop_pct": 0.48,
     "allegation": "financial_restatement", "year": 2005},
    {"name": "Lucent", "settlement": 690_000_000, "market_cap": 240_000_000_000,
     "drop_pct": 0.95, "allegation": "guidance_miss", "year": 2003},
    {"name": "Cardinal Health", "settlement": 600_000_000,
     "market_cap": 22_000_000_000, "drop_pct": 0.40,
     "allegation": "financial_restatement", "year": 2009},
    {"name": "Merck (Vioxx)", "settlement": 830_000_000,
     "market_cap": 120_000_000_000, "drop_pct": 0.30,
     "allegation": "regulatory_action", "year": 2007},
    {"name": "Bristol-Myers Squibb", "settlement": 300_000_000,
     "market_cap": 55_000_000_000, "drop_pct": 0.35,
     "allegation": "financial_restatement", "year": 2004},
    {"name": "Qwest", "settlement": 445_000_000, "market_cap": 75_000_000_000,
     "drop_pct": 0.90, "allegation": "financial_restatement", "year": 2005},
    {"name": "Rite Aid", "settlement": 319_000_000, "market_cap": 7_000_000_000,
     "drop_pct": 0.85, "allegation": "financial_restatement", "year": 2003},
    {"name": "Lehman Brothers", "settlement": 517_000_000,
     "market_cap": 40_000_000_000, "drop_pct": 0.99,
     "allegation": "financial_restatement", "year": 2012},
    {"name": "Goldman Sachs (Abacus)", "settlement": 550_000_000,
     "market_cap": 90_000_000_000, "drop_pct": 0.15,
     "allegation": "regulatory_action", "year": 2010},
    {"name": "Petrobras", "settlement": 3_000_000_000,
     "market_cap": 200_000_000_000, "drop_pct": 0.70,
     "allegation": "financial_restatement", "year": 2018},
    {"name": "Activision Blizzard", "settlement": 35_000_000,
     "market_cap": 45_000_000_000, "drop_pct": 0.15,
     "allegation": "guidance_miss", "year": 2022},
]


# ---------------------------------------------------------------------------
# Calibration helpers
# ---------------------------------------------------------------------------


def _estimate_for_case(case: dict[str, Any]) -> float:
    """Run the severity model on a single known case for calibration."""
    market_cap = case["market_cap"]
    drop_pct = case["drop_pct"]
    allegation = case["allegation"]

    # Build minimal feature vector
    features: dict[str, float] = {
        "market_cap_at_filing": math.log10(max(market_cap, 1.0)),
        "max_stock_decline_pct": drop_pct,
        "class_period_length_days": math.log10(365),
        "number_of_named_defendants": 3.0,
        "restatement_present": 1.0 if allegation == "financial_restatement" else 0.0,
        "sec_investigation_present": 0.0,
        "lead_plaintiff_institutional": 0.0,
        "jurisdiction_sdny": 0.0,
        "jurisdiction_ndcal": 0.0,
        "prior_securities_litigation": 0.0,
        "auditor_change": 0.0,
    }
    for atype in [
        "financial_restatement", "insider_trading",
        "regulatory_action", "offering_securities", "merger_objection",
    ]:
        features[f"allegation_type_{atype}"] = (
            1.0 if allegation == atype else 0.0
        )

    # Regression estimate
    regression_est = predict_settlement_regression(features)

    # Damages estimate
    turnover = 0.5
    base = compute_base_damages(market_cap, drop_pct, turnover)
    modified = apply_allegation_modifier(base, allegation)

    return max(regression_est, modified)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_severity_calibration_report() -> str:
    """Generate HTML calibration report comparing model to known settlements.

    Runs the severity model on each known case from KNOWN_SETTLEMENTS,
    compares estimates to actual settlements, and computes error metrics
    on a log10 scale.

    Returns:
        Self-contained HTML string with comparison table and error metrics.
    """
    rows: list[dict[str, Any]] = []
    log_errors: list[float] = []

    for case in KNOWN_SETTLEMENTS:
        estimate = _estimate_for_case(case)
        actual = case["settlement"]
        log_estimate = math.log10(max(estimate, 1))
        log_actual = math.log10(max(actual, 1))
        log_error = log_estimate - log_actual
        log_errors.append(log_error)

        rows.append({
            "name": case["name"],
            "year": case["year"],
            "market_cap": case["market_cap"],
            "drop_pct": case["drop_pct"],
            "allegation": case["allegation"],
            "actual": actual,
            "estimate": estimate,
            "ratio": estimate / actual if actual > 0 else 0,
            "log_error": log_error,
        })

    # Compute metrics
    n = len(log_errors)
    mae_log = sum(abs(e) for e in log_errors) / n if n > 0 else 0
    bias_log = sum(log_errors) / n if n > 0 else 0
    mse_log = sum(e * e for e in log_errors) / n if n > 0 else 0

    # R-squared on log scale
    mean_log_actual = sum(
        math.log10(max(r["actual"], 1)) for r in rows
    ) / n if n > 0 else 0
    ss_tot = sum(
        (math.log10(max(r["actual"], 1)) - mean_log_actual) ** 2
        for r in rows
    )
    ss_res = sum(e * e for e in log_errors)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Build HTML
    table_rows = ""
    for r in rows:
        actual_str = f"${r['actual']:,.0f}"
        est_str = f"${r['estimate']:,.0f}"
        ratio_str = f"{r['ratio']:.2f}x"
        err_str = f"{r['log_error']:+.2f}"
        err_color = "#c92a2a" if abs(r["log_error"]) > 1.0 else "#2b8a3e"
        table_rows += (
            f"<tr>"
            f"<td>{html_module.escape(r['name'])}</td>"
            f"<td>{r['year']}</td>"
            f"<td>{r['allegation']}</td>"
            f"<td style='text-align:right'>{actual_str}</td>"
            f"<td style='text-align:right'>{est_str}</td>"
            f"<td style='text-align:right'>{ratio_str}</td>"
            f"<td style='text-align:right;color:{err_color}'>{err_str}</td>"
            f"</tr>\n"
        )

    return f"""<!DOCTYPE html>
<html>
<head>
<title>Severity Model Calibration Report</title>
<style>
body {{ font-family: 'Inter', 'Calibri', sans-serif; max-width: 1200px; margin: auto; padding: 20px; }}
h1 {{ color: #1A1446; }}
h2 {{ color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 13px; }}
th {{ background: #1A1446; color: white; text-align: left; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
.metric-value {{ font-size: 28px; font-weight: bold; color: #1A1446; }}
.metric-label {{ font-size: 12px; color: #666; }}
</style>
</head>
<body>
<h1>Severity Model Calibration Report</h1>
<p>Comparison of model estimates vs. {n} known landmark securities class action
settlements from Cornerstone Research annual reports.</p>

<h2>Error Metrics (log10 scale)</h2>
<div>
<div class="metric">
  <div class="metric-value">{mae_log:.2f}</div>
  <div class="metric-label">MAE (log10)</div>
</div>
<div class="metric">
  <div class="metric-value">{bias_log:+.2f}</div>
  <div class="metric-label">Bias (log10)</div>
</div>
<div class="metric">
  <div class="metric-value">{r_squared:.2f}</div>
  <div class="metric-label">R-squared (log10)</div>
</div>
<div class="metric">
  <div class="metric-value">{math.sqrt(mse_log):.2f}</div>
  <div class="metric-label">RMSE (log10)</div>
</div>
</div>

<h2>Case-by-Case Comparison</h2>
<table>
<thead>
<tr>
  <th>Case</th>
  <th>Year</th>
  <th>Allegation Type</th>
  <th>Actual Settlement</th>
  <th>Model Estimate</th>
  <th>Ratio</th>
  <th>Log Error</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>

<h2>Methodology</h2>
<p>Each case is evaluated using the v7.0 severity model with published company
characteristics (market cap, stock price decline, allegation type). The model
uses max(damages-based estimate, regression-based estimate) as the settlement
prediction. Amplifiers are not applied for calibration (no signal data
available for historical cases).</p>

<p><em>Log Error = log10(estimate) - log10(actual). Positive = overestimate,
negative = underestimate. MAE on log10 scale: 1.0 = 10x average error.</em></p>
</body>
</html>"""
