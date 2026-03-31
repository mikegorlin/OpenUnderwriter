"""HTML report generator for shadow calibration.

Split from shadow_calibration.py to keep source files under 500 lines.
Generates an interactive self-contained HTML comparison report with:
- Summary metrics badges (color-coded pass/fail)
- Sortable/filterable comparison table
- UW assessment inputs (dropdown + text)
- Category filter tabs
- JSON export button
- Liberty IronPro branding
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from do_uw.stages.score.shadow_calibration import (
        CalibrationMetrics,
        CalibrationRow,
    )

__all__ = [
    "generate_calibration_html",
]


def _tier_color(tier: str) -> str:
    """Map tier to CSS color."""
    colors = {
        "PREFERRED": "#2b8a3e",
        "STANDARD": "#1864ab",
        "ELEVATED": "#e67700",
        "HIGH_RISK": "#c92a2a",
        "PROHIBITED": "#343a40",
        "WIN": "#2b8a3e",
        "WANT": "#1864ab",
        "WRITE": "#1971c2",
        "WATCH": "#e67700",
        "WALK": "#c92a2a",
        "NO_TOUCH": "#343a40",
    }
    return colors.get(tier, "#495057")


def _delta_indicator(delta: int) -> str:
    """Generate delta indicator HTML."""
    if delta == 0:
        return '<span class="delta-neutral">=</span>'
    if delta > 0:
        arrows = "&#9650;" * min(delta, 3)
        return f'<span class="delta-restrictive">{arrows} +{delta}</span>'
    arrows = "&#9660;" * min(abs(delta), 3)
    return f'<span class="delta-lenient">{arrows} {delta}</span>'


def _metric_badge(label: str, value: str, is_ok: bool) -> str:
    """Generate a color-coded metric badge."""
    cls = "badge-ok" if is_ok else "badge-warn"
    return (
        f'<div class="metric-badge {cls}">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f"</div>"
    )


def _build_table_rows(rows: list[CalibrationRow]) -> str:
    """Build HTML table rows from calibration data."""
    parts = []
    for row in rows:
        legacy_color = _tier_color(row.legacy_tier)
        hae_color = _tier_color(row.hae_tier)
        delta_html = _delta_indicator(row.tier_delta)
        crf_html = (
            ", ".join(row.crf_vetoes_active) if row.crf_vetoes_active else "--"
        )
        cat_label = row.category.replace("_", " ").title()

        parts.append(
            f'<tr data-category="{row.category}" data-ticker="{row.ticker}">'
            f'<td class="ticker-col">{row.ticker}</td>'
            f"<td>{row.sector}</td>"
            f"<td>{row.market_cap_tier}</td>"
            f'<td class="category-col">{cat_label}</td>'
            f'<td class="score-col">{row.legacy_score:.1f}</td>'
            f'<td><span class="tier-badge" style="background:{legacy_color}">'
            f"{row.legacy_tier}</span></td>"
            f'<td class="score-col">{row.host_composite:.3f}</td>'
            f'<td class="score-col">{row.agent_composite:.3f}</td>'
            f'<td class="score-col">{row.environment_composite:.3f}</td>'
            f'<td class="score-col">{row.hae_product:.4f}</td>'
            f'<td><span class="tier-badge" style="background:{hae_color}">'
            f"{row.hae_tier}</span></td>"
            f'<td class="delta-col">{delta_html}</td>'
            f'<td class="crf-col">{crf_html}</td>'
            f'<td class="interp-col">{row.interpretation}</td>'
            f"<td>"
            f'<select class="uw-select" data-field="assessment" '
            f'data-ticker="{row.ticker}">'
            f'<option value="">-- Select --</option>'
            f'<option value="PREFERRED">PREFERRED</option>'
            f'<option value="STANDARD">STANDARD</option>'
            f'<option value="ELEVATED">ELEVATED</option>'
            f'<option value="HIGH_RISK">HIGH_RISK</option>'
            f'<option value="PROHIBITED">PROHIBITED</option>'
            f"</select></td>"
            f"<td>"
            f'<input type="text" class="uw-input" data-field="rationale" '
            f'data-ticker="{row.ticker}" placeholder="Rationale...">'
            f"</td></tr>"
        )
    return "\n".join(parts)


def _build_category_tabs(rows: list[CalibrationRow]) -> str:
    """Build category filter tab buttons."""
    cats: dict[str, int] = {"all": len(rows)}
    for row in rows:
        cats[row.category] = cats.get(row.category, 0) + 1

    html = (
        f'<button class="tab-btn active" data-filter="all">'
        f'All ({cats["all"]})</button>'
    )
    for cat_key, cat_label in [
        ("known_good", "Known Good"),
        ("known_bad", "Known Bad"),
        ("edge_case", "Edge Cases"),
        ("recent_actual", "Recent Actuals"),
    ]:
        count = cats.get(cat_key, 0)
        if count > 0:
            html += (
                f'<button class="tab-btn" data-filter="{cat_key}">'
                f"{cat_label} ({count})</button>"
            )
    return html


_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
       background: #f8f9fa; color: #212529; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
           color: #fff; padding: 24px 32px; }
.header h1 { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
.header .subtitle { font-size: 14px; color: #adb5bd; }
.header .brand { color: #ff8f00; font-weight: 600; }
.metrics-bar { display: flex; gap: 16px; padding: 20px 32px;
               background: #fff; border-bottom: 1px solid #dee2e6;
               flex-wrap: wrap; }
.metric-badge { padding: 12px 20px; border-radius: 8px;
                text-align: center; min-width: 140px; }
.badge-ok { background: #d3f9d8; border: 1px solid #2b8a3e; }
.badge-warn { background: #fff3bf; border: 1px solid #e67700; }
.metric-label { font-size: 11px; text-transform: uppercase;
                letter-spacing: 0.5px; color: #495057; margin-bottom: 4px; }
.metric-value { font-size: 20px; font-weight: 700;
                font-family: 'JetBrains Mono', monospace; }
.badge-ok .metric-value { color: #2b8a3e; }
.badge-warn .metric-value { color: #e67700; }
.controls { padding: 16px 32px; background: #fff;
            border-bottom: 1px solid #dee2e6;
            display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.tab-btn { padding: 8px 16px; border: 1px solid #dee2e6;
           background: #fff; border-radius: 6px; cursor: pointer;
           font-size: 13px; transition: all 0.15s; }
.tab-btn:hover { background: #f1f3f5; }
.tab-btn.active { background: #ff8f00; color: #fff; border-color: #ff8f00; }
.export-btn { margin-left: auto; padding: 8px 20px;
              background: #1864ab; color: #fff; border: none;
              border-radius: 6px; cursor: pointer;
              font-size: 13px; font-weight: 500; }
.export-btn:hover { background: #145a99; }
.table-container { overflow-x: auto; padding: 0 32px 32px; }
table { width: 100%; border-collapse: collapse;
        margin-top: 16px; font-size: 13px; }
th { background: #343a40; color: #fff; padding: 10px 8px;
     text-align: left; cursor: pointer; white-space: nowrap;
     position: sticky; top: 0; }
th:hover { background: #495057; }
td { padding: 8px; border-bottom: 1px solid #e9ecef;
     vertical-align: middle; }
tr:hover { background: #f1f3f5; }
tr.hidden { display: none; }
.ticker-col { font-weight: 700;
              font-family: 'JetBrains Mono', monospace; }
.score-col { font-family: 'JetBrains Mono', monospace;
             text-align: right; }
.delta-col { text-align: center; }
.tier-badge { display: inline-block; padding: 3px 8px;
              border-radius: 4px; color: #fff; font-size: 11px;
              font-weight: 600; letter-spacing: 0.5px; }
.delta-neutral { color: #868e96; font-weight: 600; }
.delta-restrictive { color: #c92a2a; font-weight: 600; }
.delta-lenient { color: #2b8a3e; font-weight: 600; }
.uw-select { padding: 4px 8px; border: 1px solid #dee2e6;
             border-radius: 4px; font-size: 12px; width: 120px; }
.uw-input { padding: 4px 8px; border: 1px solid #dee2e6;
            border-radius: 4px; font-size: 12px; width: 180px; }
.footer { padding: 16px 32px; color: #868e96; font-size: 12px;
          border-top: 1px solid #dee2e6; margin-top: 32px; }
"""

_JS = """
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const filter = this.dataset.filter;
        document.querySelectorAll('#calibration-table tbody tr').forEach(row => {
            if (filter === 'all' || row.dataset.category === filter) {
                row.classList.remove('hidden');
            } else {
                row.classList.add('hidden');
            }
        });
    });
});

let sortDir = {};
function sortTable(col) {
    const table = document.getElementById('calibration-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    sortDir[col] = !(sortDir[col] || false);
    rows.sort((a, b) => {
        let aVal = a.cells[col].textContent.trim();
        let bVal = b.cells[col].textContent.trim();
        let aNum = parseFloat(aVal);
        let bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortDir[col] ? aNum - bNum : bNum - aNum;
        }
        return sortDir[col] ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    rows.forEach(row => tbody.appendChild(row));
}
"""

_EXPORT_JS_TEMPLATE = """
function exportAssessments() {{
    const assessments = [];
    const rowData = {rows_json};
    document.querySelectorAll('#calibration-table tbody tr').forEach((row, i) => {{
        const select = row.querySelector('.uw-select');
        const input = row.querySelector('.uw-input');
        if (select && select.value) {{
            assessments.push({{
                ticker: row.dataset.ticker,
                uw_assessment: select.value,
                uw_rationale: input ? input.value : '',
                legacy_tier: rowData[i] ? rowData[i].legacy_tier : '',
                hae_tier: rowData[i] ? rowData[i].hae_tier : '',
            }});
        }}
    }});
    if (assessments.length === 0) {{
        alert('No assessments entered yet.');
        return;
    }}
    const blob = new Blob([JSON.stringify(assessments, null, 2)],
                          {{type: 'application/json'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'calibration_assessments.json';
    a.click();
    URL.revokeObjectURL(url);
}}
"""


def _delta_color(delta: float) -> str:
    """Color code for factor delta: green <2, yellow 2-5, red >5."""
    abs_d = abs(delta)
    if abs_d < 2.0:
        return "#2b8a3e"
    if abs_d < 5.0:
        return "#e67700"
    return "#c92a2a"


def _build_factor_comparison_section(rows: list[CalibrationRow]) -> str:
    """Build factor-level comparison table for tickers with signal data.

    Shows per-ticker, per-factor: rule-based score, signal-driven score,
    delta, coverage, and method.
    """
    # Filter rows that have factor-level signal data
    rows_with_data = [
        r for r in rows
        if r.factor_scores_signal or r.factor_scores_rule
    ]

    if not rows_with_data:
        return (
            '<div class="table-container">'
            '<h2 class="factor-comparison" style="padding:16px 0 8px;">'
            'Factor-Level Comparison</h2>'
            '<p style="color:#868e96;font-size:13px;">'
            'No signal-driven factor data available yet. '
            'Run pipeline with signal-enabled scoring to populate.</p>'
            '</div>'
        )

    header = (
        '<div class="table-container">'
        '<h2 class="factor-comparison" style="padding:16px 0 8px;">'
        'Factor-Level Comparison</h2>'
        '<table class="factor-comparison-table" style="width:100%;'
        'border-collapse:collapse;font-size:13px;margin-top:8px;">'
        '<thead><tr style="background:#343a40;color:#fff;">'
        '<th style="padding:8px;">Ticker</th>'
        '<th style="padding:8px;">Factor</th>'
        '<th style="padding:8px;text-align:right;">Rule-Based</th>'
        '<th style="padding:8px;text-align:right;">Signal-Driven</th>'
        '<th style="padding:8px;text-align:right;">Delta</th>'
        '<th style="padding:8px;text-align:right;">Coverage</th>'
        '<th style="padding:8px;">Method</th>'
        '</tr></thead><tbody>'
    )

    body_parts: list[str] = []
    for row in rows_with_data:
        all_factors = sorted(
            set(list(row.factor_scores_signal.keys()) + list(row.factor_scores_rule.keys()))
        )
        for fid in all_factors:
            sig_score = row.factor_scores_signal.get(fid, 0.0)
            rule_score = row.factor_scores_rule.get(fid, 0.0)
            delta = sig_score - rule_score
            method = row.scoring_methods.get(fid, "unknown")
            color = _delta_color(delta)
            body_parts.append(
                f'<tr style="border-bottom:1px solid #e9ecef;">'
                f'<td style="padding:6px 8px;font-weight:700;'
                f'font-family:monospace;">{row.ticker}</td>'
                f'<td style="padding:6px 8px;">{fid}</td>'
                f'<td style="padding:6px 8px;text-align:right;'
                f'font-family:monospace;">{rule_score:.1f}</td>'
                f'<td style="padding:6px 8px;text-align:right;'
                f'font-family:monospace;">{sig_score:.1f}</td>'
                f'<td style="padding:6px 8px;text-align:right;'
                f'font-family:monospace;color:{color};">{delta:+.1f}</td>'
                f'<td style="padding:6px 8px;text-align:right;'
                f'font-family:monospace;">'
                f'{row.signal_coverage_avg:.0%}</td>'
                f'<td style="padding:6px 8px;">{method}</td></tr>'
            )

        # Summary row for this ticker
        total_signal = sum(row.factor_scores_signal.values())
        total_rule = sum(row.factor_scores_rule.values())
        total_delta = total_signal - total_rule
        body_parts.append(
            f'<tr style="border-bottom:2px solid #343a40;'
            f'font-weight:700;background:#f1f3f5;">'
            f'<td style="padding:6px 8px;">{row.ticker}</td>'
            f'<td style="padding:6px 8px;">TOTAL</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'font-family:monospace;">{total_rule:.1f}</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'font-family:monospace;">{total_signal:.1f}</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'font-family:monospace;color:{_delta_color(total_delta)};">'
            f'{total_delta:+.1f}</td>'
            f'<td style="padding:6px 8px;text-align:right;'
            f'font-family:monospace;">{row.signal_coverage_avg:.0%}</td>'
            f'<td style="padding:6px 8px;">--</td></tr>'
        )

    return header + "\n".join(body_parts) + "</tbody></table></div>"


def generate_calibration_html(
    rows: list[CalibrationRow],
    metrics: CalibrationMetrics,
) -> str:
    """Generate interactive HTML calibration report.

    Produces a single self-contained HTML file with inline CSS/JS.
    """
    badges_html = "".join([
        _metric_badge(
            "Rank Correlation",
            f"{metrics.rank_correlation:.3f}",
            metrics.rank_correlation >= 0.60,
        ),
        _metric_badge(
            "Tier Agreement",
            f"{metrics.tier_agreement_pct:.1f}%",
            metrics.tier_agreement_pct >= 70.0,
        ),
        _metric_badge(
            "Systematic Bias",
            f"{metrics.systematic_bias:+.2f}",
            abs(metrics.systematic_bias) < 1.5,
        ),
        _metric_badge(
            "Extremes Match",
            "YES" if metrics.extremes_agreement else "NO",
            metrics.extremes_agreement,
        ),
        _metric_badge(
            "All Criteria",
            "PASS" if metrics.all_criteria_met else "FAIL",
            metrics.all_criteria_met,
        ),
        _metric_badge(
            "Signal Coverage",
            f"{metrics.avg_signal_coverage:.0%}" if metrics.avg_signal_coverage > 0 else "N/A",
            metrics.avg_signal_coverage >= 0.50,
        ),
        _metric_badge(
            "Factor Delta",
            f"{metrics.mean_factor_delta:.2f}" if metrics.mean_factor_delta > 0 else "N/A",
            metrics.mean_factor_delta < 2.0,
        ),
    ])

    rows_html = _build_table_rows(rows)
    tabs_html = _build_category_tabs(rows)
    factor_comparison_html = _build_factor_comparison_section(rows)
    rows_json = json.dumps([r.model_dump() for r in rows], indent=2)
    export_js = _EXPORT_JS_TEMPLATE.format(rows_json=rows_json)

    th_cells = "".join(
        f'<th onclick="sortTable({i})">{h}</th>'
        for i, h in enumerate([
            "Ticker", "Sector", "Cap", "Category",
            "Legacy Score", "Legacy Tier",
            "Host", "Agent", "Env", "P (HxAxE)",
            "H/A/E Tier", "Delta",
        ])
    )
    th_cells += "<th>CRF Vetoes</th><th>Interpretation</th>"
    th_cells += "<th>UW Assessment</th><th>UW Rationale</th>"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Shadow Calibration Report - Liberty IronPro</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        '<div class="header">\n'
        "  <h1>Shadow Calibration Report</h1>\n"
        '  <div class="subtitle">H/A/E Multiplicative vs Legacy 10-Factor'
        ' &middot; <span class="brand">Liberty IronPro</span></div>\n'
        "</div>\n"
        f'<div class="metrics-bar">{badges_html}</div>\n'
        f'<div class="controls">{tabs_html}'
        '<button class="export-btn" onclick="exportAssessments()">'
        "Export Assessments (JSON)</button></div>\n"
        '<div class="table-container">\n'
        '<table id="calibration-table">\n'
        f"<thead><tr>{th_cells}</tr></thead>\n"
        f"<tbody>{rows_html}</tbody>\n"
        "</table></div>\n"
        f"{factor_comparison_html}\n"
        f'<div class="footer">Shadow Calibration Report &middot; '
        f"{len(rows)} tickers &middot; H/A/E model v7.0 &middot; "
        f"Liberty IronPro &middot; "
        f"Synthetic data (stub mode)</div>\n"
        f"<script>{_JS}\n{export_js}</script>\n"
        "</body>\n</html>"
    )
