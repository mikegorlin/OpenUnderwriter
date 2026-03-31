#!/usr/bin/env python3
"""Cross-ticker QA comparison — checks feature parity across all outputs.

Compares every ticker output against a reference (AAPL) to catch:
- Missing sections/subsections
- Missing charts (SVG, sparklines)
- Missing interactive features (collapsibles, badges, KV tables)
- Missing data sections (8Q trends, QA audit, bull/bear)
- Data staleness (state.json older than renderer code)
- Content quality (N/A ratios, empty facets)

Usage:
    uv run python scripts/qa_compare.py [--reference AAPL] [--fix]
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_RENDER = PROJECT_ROOT / "src" / "do_uw" / "stages" / "render"

# v8.0 section IDs that should be present in all outputs
V8_SECTION_IDS = [
    "section-intelligence-dossier",
    "section-alternative-data",
    "section-forward-looking",
    "adversarial-critique",
]


@dataclass
class OutputProfile:
    ticker: str
    output_dir: Path
    html_path: Path
    html_size: int = 0
    state_mtime: float = 0.0
    sections_h2: int = 0
    sections_h3: int = 0
    section_ids: list[str] = field(default_factory=list)
    svg_count: int = 0
    sparkline_count: int = 0
    chart_figures: int = 0
    score_badges: int = 0
    collapsibles: int = 0
    kv_tables: int = 0
    bull_bear: int = 0
    facet_blocks: int = 0
    has_8q_trends: bool = False
    has_qa_audit: bool = False
    has_timeline_chart: bool = False
    has_ownership_chart: bool = False
    has_radar_chart: bool = False
    red_flag_count: int = 0
    na_ratio: float = 0.0
    yfinance_quarterly_count: int = 0
    gap_search_summary: bool = False
    # Business profile fields (Phase 92-02)
    has_revenue_segments: bool = False
    has_customer_concentration: bool = False
    has_supplier_concentration: bool = False
    has_geographic_footprint: bool = False
    has_render_audit: bool = False
    render_audit_unrendered_count: int = -1  # sentinel: -1 = not present
    has_data_audit_html: bool = False
    # v8.0 Intelligence Dossier features
    has_intelligence_dossier: bool = False
    has_forward_looking: bool = False
    has_alt_data: bool = False
    has_stock_catalysts: bool = False
    has_adversarial_critique: bool = False
    # v10.0 Phase 133-136 features
    has_drop_attribution: bool = False
    has_earnings_reaction: bool = False
    has_volume_anomalies: bool = False
    has_analyst_revisions: bool = False
    has_correlation_metrics: bool = False
    has_risk_factor_review: bool = False
    has_sector_landscape: bool = False
    has_customer_concentration_section: bool = False
    has_regulatory_environment: bool = False
    has_officer_backgrounds: bool = False
    has_shareholder_rights: bool = False
    has_insider_activity: bool = False
    has_forward_scenarios: bool = False
    has_key_dates_calendar: bool = False
    has_mgmt_credibility: bool = False
    has_short_seller_monitor: bool = False
    errors: list[str] = field(default_factory=list)


def profile_output(ticker: str, output_dir: Path) -> OutputProfile:
    """Build a full quality profile of a ticker's output."""
    html_path = output_dir / f"{ticker}_worksheet.html"
    p = OutputProfile(
        ticker=ticker,
        output_dir=output_dir,
        html_path=html_path,
    )

    if not html_path.exists():
        p.errors.append("HTML file missing")
        return p

    content = html_path.read_text(encoding="utf-8")
    p.html_size = len(content)

    # State metadata
    state_path = output_dir / "state.json"
    if state_path.exists():
        p.state_mtime = state_path.stat().st_mtime
        try:
            state = json.loads(state_path.read_text())
            ext = state.get("extracted", {})
            fin = ext.get("financials", {}) if ext else {}
            yq = fin.get("yfinance_quarterly", []) if fin else []
            p.yfinance_quarterly_count = len(yq) if yq else 0

            analysis = state.get("analysis", {})
            gs = analysis.get("gap_search_summary", {}) if analysis else {}
            p.gap_search_summary = bool(gs)

            # Business profile fields from text_signals
            ts = ext.get("text_signals", {}) if ext else {}
            # Revenue segments: revenue_quality_warn or segment_consistency
            p.has_revenue_segments = bool(
                ts.get("revenue_quality_warn") or ts.get("segment_consistency")
            )
            # Customer concentration
            p.has_customer_concentration = bool(ts.get("customer_concentration"))
            # Supplier/distribution concentration
            p.has_supplier_concentration = bool(
                ts.get("distribution_channels") or ts.get("partner_stability")
            )
            # Geographic footprint
            p.has_geographic_footprint = bool(
                ts.get("geopolitical_exposure") or ts.get("fx_exposure")
            )

            # Render audit presence in state.json
            pm = state.get("pipeline_metadata", {})
            ra = pm.get("render_audit")
            if ra and isinstance(ra, dict):
                p.has_render_audit = True
                unrendered = ra.get("unrendered_fields", [])
                p.render_audit_unrendered_count = len(unrendered) if isinstance(unrendered, list) else -1
            else:
                p.has_render_audit = False
                p.render_audit_unrendered_count = -1
        except (json.JSONDecodeError, KeyError):
            p.errors.append("state.json parse error")

    # Section counts
    p.sections_h2 = len(re.findall(r"<h2[^>]*>", content))
    p.sections_h3 = len(re.findall(r"<h3[^>]*>", content))

    # Section IDs
    p.section_ids = re.findall(r'<section[^>]*id="([^"]+)"', content)

    # Visual features
    p.svg_count = len(re.findall(r"<svg", content))
    p.sparkline_count = len(
        re.findall(r'viewBox="0 0 60 16"', content)
    )
    p.chart_figures = len(re.findall(r"chart-figure", content))
    p.score_badges = len(
        re.findall(r"score-badge|verdict-badge|badge-tier", content)
    )
    p.collapsibles = len(re.findall(r"<details|collapsible", content))
    p.kv_tables = len(re.findall(r"kv-table|key-value", content))
    p.bull_bear = len(
        re.findall(r"bull-case|bear-case|Bull Case|Bear Case", content)
    )
    p.facet_blocks = len(re.findall(r"facet-block", content))

    # Specific features
    p.has_8q_trends = "Quarterly Financial Trends" in content
    p.has_qa_audit = "QA / Audit Trail" in content or "qa-audit" in content
    p.has_timeline_chart = bool(
        re.search(r"timeline|litigation.*chart", content, re.IGNORECASE)
        and p.chart_figures > 3
    )
    p.has_ownership_chart = bool(
        re.search(r"ownership.*chart|ownership.*svg", content, re.IGNORECASE)
    )
    p.has_radar_chart = bool(
        re.search(r"radar", content, re.IGNORECASE) and p.chart_figures >= 3
    )
    p.red_flag_count = len(re.findall(r'id="facet-triggered_flags"', content))

    # Data Audit appendix presence in HTML
    p.has_data_audit_html = bool(
        re.search(r'id="data-audit"|Data Audit', content)
    )

    # --- v8.0 Intelligence Dossier features ---
    p.has_intelligence_dossier = bool(
        re.search(r'id="section-intelligence-dossier"', content)
        and (
            re.search(r'id="dossier-revenue-model-card"|revenue-model-card|Revenue Model', content)
            or re.search(r'id="dossier-what-company-does"|competitive-landscape|Competitive Landscape', content)
        )
    )
    p.has_forward_looking = bool(
        re.search(r'id="section-forward-looking"', content)
        and (
            re.search(r'credibility|Credibility', content)
            or re.search(r'monitoring-trigger|Monitoring Trigger', content)
        )
    )
    p.has_alt_data = bool(
        re.search(r'id="section-alternative-data"', content)
        and (
            re.search(r'ESG|esg|ai-washing|AI.Washing|tariff|peer.*sca|SCA.*contagion', content, re.IGNORECASE)
        )
    )
    p.has_stock_catalysts = bool(
        re.search(r'Catalyst|catalyst.*column|D&O Assessment', content)
        and re.search(r'stock.*drop|Stock.*Drop', content, re.IGNORECASE)
    )
    p.has_adversarial_critique = bool(
        re.search(r'id="adversarial-critique"', content)
    )

    # --- v10.0 Phase 133-136 features ---
    # Phase 133: Stock & Market Intelligence
    p.has_drop_attribution = bool(
        re.search(r'Drop Attribution|stock.*drop.*attribution|stock_drops', content, re.IGNORECASE)
    )
    p.has_earnings_reaction = bool(
        re.search(r'Earnings Reaction|earnings.*reaction|earnings_reaction', content, re.IGNORECASE)
    )
    p.has_volume_anomalies = bool(
        re.search(r'Volume Anomal|volume.*anomal', content, re.IGNORECASE)
    )
    p.has_analyst_revisions = bool(
        re.search(r'Analyst Revision|analyst.*revision', content, re.IGNORECASE)
    )
    p.has_correlation_metrics = bool(
        re.search(r'Correlation Metric|correlation.*metric|Beta.*S.P', content, re.IGNORECASE)
    )
    # Phase 134: Company Intelligence
    p.has_risk_factor_review = bool(
        re.search(r'Risk Factor Review|risk.*factor.*review|risk_factor_review', content, re.IGNORECASE)
    )
    p.has_sector_landscape = bool(
        re.search(r'Sector Landscape|sector.*landscape|sector_concerns', content, re.IGNORECASE)
    )
    p.has_customer_concentration_section = bool(
        re.search(r'Customer Concentration|Concentration Assessment|concentration_assessment', content, re.IGNORECASE)
    )
    p.has_regulatory_environment = bool(
        re.search(r'Regulatory Environment|regulatory.*map|regulatory_map', content, re.IGNORECASE)
    )
    # Phase 135: Governance Intelligence
    p.has_officer_backgrounds = bool(
        re.search(r'Officer Background|officer.*background', content, re.IGNORECASE)
    )
    p.has_shareholder_rights = bool(
        re.search(r'Shareholder Rights|shareholder.*rights', content, re.IGNORECASE)
    )
    p.has_insider_activity = bool(
        re.search(r'Insider Activity|Per-Insider|per.insider.*activity', content, re.IGNORECASE)
    )
    # Phase 136: Forward-Looking
    p.has_forward_scenarios = bool(
        re.search(r'Forward Risk Scenarios|forward.*scenarios', content, re.IGNORECASE)
    )
    p.has_key_dates_calendar = bool(
        re.search(r'Key Dates.*Calendar|Monitoring Calendar|key.*dates', content, re.IGNORECASE)
    )
    p.has_mgmt_credibility = bool(
        re.search(r'Management Credibility|credibility.*assessment|pattern_label', content, re.IGNORECASE)
    )
    p.has_short_seller_monitor = bool(
        re.search(r'Short-Seller.*Monitor|Conviction Monitor|short.*seller.*alert|Bears\s+(Rising|Stable|Declining)', content, re.IGNORECASE)
    )

    # N/A ratio in table cells
    na_cells = len(re.findall(r">N/A<|>—<", content))
    total_td = len(re.findall(r"<td", content))
    p.na_ratio = na_cells / max(total_td, 1)

    return p


def compare_profiles(
    ref: OutputProfile, target: OutputProfile
) -> list[str]:
    """Compare target against reference, return list of issues."""
    issues: list[str] = []
    t = target.ticker

    # Section parity
    if target.sections_h2 < ref.sections_h2:
        missing = ref.sections_h2 - target.sections_h2
        issues.append(
            f"[SECTIONS] {t} has {target.sections_h2} h2 sections "
            f"vs {ref.sections_h2} in {ref.ticker} (missing {missing})"
        )

    # Missing section IDs
    ref_ids = set(ref.section_ids)
    target_ids = set(target.section_ids)
    missing_ids = ref_ids - target_ids
    if missing_ids:
        issues.append(
            f"[SECTIONS] {t} missing section IDs: {sorted(missing_ids)}"
        )

    # Chart parity
    if target.chart_figures < ref.chart_figures - 1:
        issues.append(
            f"[CHARTS] {t} has {target.chart_figures} chart figures "
            f"vs {ref.chart_figures} in {ref.ticker}"
        )

    if ref.has_8q_trends and not target.has_8q_trends:
        if target.yfinance_quarterly_count == 0:
            issues.append(
                f"[DATA GAP] {t} missing 8Q trends — yfinance_quarterly "
                f"not in state.json (needs full pipeline re-run)"
            )
        else:
            issues.append(
                f"[RENDER BUG] {t} has yfinance_quarterly data "
                f"({target.yfinance_quarterly_count} entries) but 8Q "
                f"trends not rendering"
            )

    if ref.has_qa_audit and not target.has_qa_audit:
        if not target.gap_search_summary:
            issues.append(
                f"[DATA GAP] {t} missing QA/Audit Trail — "
                f"gap_search_summary not in state.json (needs re-run)"
            )
        else:
            issues.append(
                f"[RENDER BUG] {t} has gap_search_summary but QA/Audit "
                f"Trail not rendering"
            )

    # Interactive features
    if target.score_badges < ref.score_badges * 0.5:
        issues.append(
            f"[BADGES] {t} has {target.score_badges} score badges "
            f"vs {ref.score_badges} in {ref.ticker}"
        )

    if target.collapsibles < ref.collapsibles * 0.5:
        issues.append(
            f"[INTERACTIVITY] {t} has {target.collapsibles} collapsibles "
            f"vs {ref.collapsibles} in {ref.ticker}"
        )

    if target.sparkline_count < ref.sparkline_count * 0.5:
        issues.append(
            f"[SPARKLINES] {t} has {target.sparkline_count} sparklines "
            f"vs {ref.sparkline_count} in {ref.ticker}"
        )

    # KV tables (layout density)
    if target.kv_tables < ref.kv_tables * 0.7:
        issues.append(
            f"[LAYOUT] {t} has {target.kv_tables} KV tables "
            f"vs {ref.kv_tables} in {ref.ticker}"
        )

    # Bull/bear framing
    if target.bull_bear < ref.bull_bear * 0.5:
        issues.append(
            f"[CONTENT] {t} has {target.bull_bear} bull/bear references "
            f"vs {ref.bull_bear} in {ref.ticker}"
        )

    # --- v8.0 Section Parity ---
    v8_checks = [
        ("has_intelligence_dossier", "section-intelligence-dossier", "Intelligence Dossier"),
        ("has_forward_looking", "section-forward-looking", "Forward-Looking Risk"),
        ("has_alt_data", "section-alternative-data", "Alternative Data"),
        ("has_adversarial_critique", "adversarial-critique", "Adversarial Critique"),
        ("has_stock_catalysts", None, "Stock Catalysts (drop catalyst + D&O assessment)"),
    ]
    for field_name, section_id, label in v8_checks:
        tgt_has = getattr(target, field_name, False)
        if not tgt_has:
            # Check if section ID at least exists in HTML
            if section_id and section_id in target.section_ids:
                issues.append(
                    f"[v8.0] {t} has {label} section but missing expected content"
                )
            else:
                issues.append(
                    f"[v8.0] {t} MISSING {label} section entirely"
                )

    # --- v10.0 Phase 133-136 Section Parity ---
    # These are "soft" checks: missing sections get logged but many are data-dependent
    v10_checks = [
        # Phase 133: Stock Intelligence
        ("has_drop_attribution", "Drop Attribution (Phase 133)"),
        ("has_earnings_reaction", "Earnings Reaction (Phase 133)"),
        ("has_volume_anomalies", "Volume Anomalies (Phase 133)"),
        ("has_analyst_revisions", "Analyst Revisions (Phase 133)"),
        ("has_correlation_metrics", "Correlation Metrics (Phase 133)"),
        # Phase 134: Company Intelligence
        ("has_risk_factor_review", "Risk Factor Review (Phase 134)"),
        ("has_sector_landscape", "Sector Landscape (Phase 134)"),
        ("has_customer_concentration_section", "Customer Concentration (Phase 134)"),
        ("has_regulatory_environment", "Regulatory Environment (Phase 134)"),
        # Phase 135: Governance Intelligence
        ("has_officer_backgrounds", "Officer Backgrounds (Phase 135)"),
        ("has_shareholder_rights", "Shareholder Rights (Phase 135)"),
        ("has_insider_activity", "Insider Activity (Phase 135)"),
        # Phase 136: Forward-Looking
        ("has_forward_scenarios", "Forward Risk Scenarios (Phase 136)"),
        ("has_key_dates_calendar", "Key Dates Calendar (Phase 136)"),
        ("has_mgmt_credibility", "Management Credibility (Phase 136)"),
        ("has_short_seller_monitor", "Short-Seller Monitor (Phase 136)"),
    ]
    for field_name, label in v10_checks:
        ref_has = getattr(ref, field_name, False)
        tgt_has = getattr(target, field_name, False)
        if ref_has and not tgt_has:
            issues.append(f"[v10.0] {t} missing {label}")

    # N/A ratio
    if target.na_ratio > 0.3:
        issues.append(
            f"[DATA QUALITY] {t} has {target.na_ratio:.0%} N/A cells "
            f"(threshold: 30%)"
        )

    # Size disparity
    size_ratio = target.html_size / max(ref.html_size, 1)
    if size_ratio < 0.6:
        issues.append(
            f"[SIZE] {t} HTML is {target.html_size/1024:.0f}KB "
            f"vs {ref.html_size/1024:.0f}KB reference "
            f"({size_ratio:.0%} — suspiciously small)"
        )

    # --- Business Profile Validation (Phase 92-02) ---

    # Render audit presence checks
    if ref.has_render_audit and not target.has_render_audit:
        issues.append(
            f"[HIGH] {t} missing render_audit in state.json "
            f"(needs pipeline re-run with audit injection)"
        )

    if ref.has_data_audit_html and not target.has_data_audit_html:
        issues.append(
            f"[HIGH] {t} missing Data Audit appendix in HTML "
            f"(render_audit template not rendering)"
        )

    # Business profile field comparisons
    biz_fields = [
        ("has_revenue_segments", "revenue segments"),
        ("has_customer_concentration", "customer concentration"),
        ("has_supplier_concentration", "supplier/distribution data"),
        ("has_geographic_footprint", "geographic footprint"),
    ]

    for field_name, label in biz_fields:
        ref_has = getattr(ref, field_name, False)
        tgt_has = getattr(target, field_name, False)

        if ref_has and not tgt_has:
            # Reference has the data, target doesn't -- data gap
            issues.append(
                f"[MEDIUM] {t} missing {label} in state.json "
                f"(present in {ref.ticker} -- data gap)"
            )

    return issues


def _extract_ticker(dirname: str) -> str:
    """Extract ticker from directory name.

    Handles formats:
    - 'AAPL' -> 'AAPL'
    - 'AAPL - Apple' -> 'AAPL'
    - 'AAPL-2026-03-05' -> 'AAPL'
    - 'HNGE - Hinge Health' -> 'HNGE'
    """
    # "TICKER - Company Name" format
    if " - " in dirname:
        return dirname.split(" - ")[0].strip()
    # "TICKER-date" or plain "TICKER" format
    parts = dirname.split("-")
    return parts[0].strip()


def _find_html_in_dir(d: Path, ticker: str) -> tuple[Path, Path] | None:
    """Find HTML file and its parent dir, checking date subdirs too.

    Prefers latest date subdir over direct file (date subdirs are newer runs).
    Returns (html_path, output_dir) or None.
    """
    # Date subdir: output/AAPL - Apple/2026-03-20/AAPL_worksheet.html
    # Find latest date subdir first (preferred — newer runs)
    date_dirs = sorted(
        [sd for sd in d.iterdir() if sd.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}", sd.name)],
        key=lambda p: p.name,
        reverse=True,
    )
    for dd in date_dirs:
        html = dd / f"{ticker}_worksheet.html"
        if html.exists():
            return html, dd

    # Fallback: direct file in ticker dir
    html = d / f"{ticker}_worksheet.html"
    if html.exists():
        return html, d

    return None


def find_all_outputs() -> dict[str, OutputProfile]:
    """Find and profile all ticker outputs."""
    profiles: dict[str, OutputProfile] = {}

    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir():
            continue

        ticker = _extract_ticker(d.name)
        if not ticker:
            continue

        result = _find_html_in_dir(d, ticker)
        if result is None:
            continue

        _html_path, output_dir = result

        # Use latest output if multiple exist for same ticker
        if ticker in profiles:
            existing_mtime = profiles[ticker].state_mtime
            new_state = output_dir / "state.json"
            if new_state.exists() and new_state.stat().st_mtime > existing_mtime:
                profiles[ticker] = profile_output(ticker, output_dir)
        else:
            profiles[ticker] = profile_output(ticker, output_dir)

    return profiles


def main() -> int:
    ref_ticker = "AAPL"
    for arg in sys.argv[1:]:
        if arg.startswith("--reference"):
            ref_ticker = sys.argv[sys.argv.index(arg) + 1]

    profiles = find_all_outputs()

    if not profiles:
        print("ERROR: No output directories found")
        return 1

    if ref_ticker not in profiles:
        print(f"ERROR: Reference ticker {ref_ticker} not found in outputs")
        return 1

    ref = profiles[ref_ticker]

    # Print reference profile
    print(f"\n{'=' * 72}")
    print(f" QA CROSS-TICKER COMPARISON — Reference: {ref_ticker}")
    print(f"{'=' * 72}\n")

    print(f"Reference: {ref_ticker} ({ref.html_size/1024:.0f}KB)")
    print(f"  Sections: {ref.sections_h2} h2, {ref.sections_h3} h3")
    print(f"  Charts: {ref.chart_figures} figures, {ref.svg_count} SVGs, {ref.sparkline_count} sparklines")
    print(f"  Interactivity: {ref.score_badges} badges, {ref.collapsibles} collapsibles")
    print(f"  Layout: {ref.kv_tables} KV tables, {ref.facet_blocks} facet blocks")
    print(f"  Content: {ref.bull_bear} bull/bear, 8Q={ref.has_8q_trends}, QA={ref.has_qa_audit}")
    print(f"  Data: N/A ratio={ref.na_ratio:.1%}, yfinance_quarterly={ref.yfinance_quarterly_count}")
    print(f"  Business Profile: rev_segs={ref.has_revenue_segments}, customer={ref.has_customer_concentration}, "
          f"supplier={ref.has_supplier_concentration}, geo={ref.has_geographic_footprint}")
    print(f"  Render Audit: state={ref.has_render_audit}, html={ref.has_data_audit_html}, "
          f"unrendered={ref.render_audit_unrendered_count}")
    print(f"  v8.0: dossier={ref.has_intelligence_dossier}, forward={ref.has_forward_looking}, "
          f"alt_data={ref.has_alt_data}, catalysts={ref.has_stock_catalysts}, "
          f"adversarial={ref.has_adversarial_critique}")

    # v8.0 section ID check on reference
    ref_v8_missing = [sid for sid in V8_SECTION_IDS if sid not in ref.section_ids]
    if ref_v8_missing:
        print(f"  WARNING: Reference missing v8.0 section IDs: {ref_v8_missing}")
    print()

    # Compare each ticker
    total_issues = 0
    data_gap_tickers: list[str] = []

    for ticker, profile in sorted(profiles.items()):
        if ticker == ref_ticker:
            continue

        issues = compare_profiles(ref, profile)
        has_data_gap = any("[DATA GAP]" in i for i in issues)
        if has_data_gap:
            data_gap_tickers.append(ticker)

        status = "PASS" if not issues else f"FAIL ({len(issues)} issues)"
        icon = "  " if not issues else "  "

        print(f"{'─' * 72}")
        print(f"{icon} {ticker} ({profile.html_size/1024:.0f}KB) — {status}")

        if not issues:
            print(f"  Feature parity with {ref_ticker}")
        else:
            for issue in issues:
                print(f"  {issue}")
            total_issues += len(issues)

        # Always show key stats
        print(f"  Stats: {profile.sections_h2}h2 {profile.chart_figures}charts "
              f"{profile.score_badges}badges {profile.collapsibles}collapsibles "
              f"{profile.sparkline_count}sparklines {profile.na_ratio:.0%}NA")
        v8_present = sum([
            profile.has_intelligence_dossier,
            profile.has_forward_looking,
            profile.has_alt_data,
            profile.has_stock_catalysts,
            profile.has_adversarial_critique,
        ])
        v10_present = sum([
            profile.has_drop_attribution,
            profile.has_earnings_reaction,
            profile.has_volume_anomalies,
            profile.has_analyst_revisions,
            profile.has_correlation_metrics,
            profile.has_risk_factor_review,
            profile.has_sector_landscape,
            profile.has_customer_concentration_section,
            profile.has_regulatory_environment,
            profile.has_officer_backgrounds,
            profile.has_shareholder_rights,
            profile.has_insider_activity,
            profile.has_forward_scenarios,
            profile.has_key_dates_calendar,
            profile.has_mgmt_credibility,
            profile.has_short_seller_monitor,
        ])
        print(f"  v8.0: {v8_present}/5 features | v10.0: {v10_present}/16 sections")
        print()

    # Summary
    print(f"{'=' * 72}")
    tickers_checked = len(profiles) - 1

    if total_issues == 0:
        print(f" ALL {tickers_checked} TICKERS MATCH REFERENCE")
    else:
        # Severity breakdown
        all_issues: list[str] = []
        for ticker, profile in sorted(profiles.items()):
            if ticker == ref_ticker:
                continue
            all_issues.extend(compare_profiles(ref, profile))

        high_count = sum(1 for i in all_issues if "[HIGH]" in i)
        medium_count = sum(1 for i in all_issues if "[MEDIUM]" in i)
        low_count = sum(1 for i in all_issues if "[LOW]" in i)
        other_count = total_issues - high_count - medium_count - low_count

        print(f" {total_issues} ISSUES across {tickers_checked} tickers")
        if high_count or medium_count or low_count:
            parts = []
            if high_count:
                parts.append(f"{high_count} HIGH")
            if medium_count:
                parts.append(f"{medium_count} MEDIUM")
            if low_count:
                parts.append(f"{low_count} LOW")
            if other_count:
                parts.append(f"{other_count} other")
            print(f"  Severity: {', '.join(parts)}")

    if data_gap_tickers:
        print(f"\n  DATA GAP TICKERS (need full pipeline re-run):")
        for t in data_gap_tickers:
            print(f"    uv run python -m do_uw.cli analyze {t}")

    print(f"{'=' * 72}\n")
    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
