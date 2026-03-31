"""Shadow calibration runner and HTML report generator.

Runs both H/A/E and legacy scoring lenses on a curated set of
30-40 diverse tickers and produces an interactive HTML comparison
report. The calibration report lets the UW provide tier assessments
with rationale for each ticker, generating JSON feedback for weight
adjustment.

Two modes:
1. Stub mode (run_shadow_calibration): Generates synthetic comparison
   data for report structure testing. The real pipeline takes 20+
   minutes per ticker and requires MCP tools.
2. Live mode (calibrate_from_pipeline): Extracts real comparison
   data from a completed pipeline run (AnalysisState).

The report is a single self-contained HTML file with inline CSS/JS.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from do_uw.stages.score._calibration_report import (
    generate_calibration_html,
)

__all__ = [
    "CALIBRATION_TICKERS",
    "CalibrationMetrics",
    "CalibrationRow",
    "calibrate_from_pipeline",
    "generate_calibration_html",
    "run_shadow_calibration",
    "save_calibration_report",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Calibration ticker universe
# ---------------------------------------------------------------

CALIBRATION_TICKERS: list[dict[str, Any]] = [
    # Known Good: Large-cap stable companies with clean governance
    {"ticker": "BRK-B", "category": "known_good", "sector": "Financials",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Berkshire Hathaway -- exceptional governance, fortress balance sheet"},
    {"ticker": "JNJ", "category": "known_good", "sector": "Healthcare",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Johnson & Johnson -- diversified healthcare, strong controls"},
    {"ticker": "PG", "category": "known_good", "sector": "Consumer Staples",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Procter & Gamble -- stable consumer staples, clean record"},
    {"ticker": "MSFT", "category": "known_good", "sector": "Technology",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Microsoft -- strong governance, diversified revenue"},
    {"ticker": "AAPL", "category": "known_good", "sector": "Technology",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Apple -- massive cash, minimal litigation history"},
    {"ticker": "KO", "category": "known_good", "sector": "Consumer Staples",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Coca-Cola -- iconic brand, stable governance"},
    {"ticker": "WMT", "category": "known_good", "sector": "Consumer Discretionary",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Walmart -- dominant retailer, strong compliance program"},
    {"ticker": "V", "category": "known_good", "sector": "Financials",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Visa -- payment network duopoly, clean governance"},
    {"ticker": "UNH", "category": "known_good", "sector": "Healthcare",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "UnitedHealth -- healthcare leader, strong financials"},
    {"ticker": "HD", "category": "known_good", "sector": "Consumer Discretionary",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Home Depot -- retail leader, consistent performance"},

    # Known Bad: Companies with active/recent litigation, enforcement, distress
    {"ticker": "SMCI", "category": "known_bad", "sector": "Technology",
     "expected_tier_range": ["HIGH_RISK", "PROHIBITED"],
     "rationale": "Super Micro -- DOJ probe, auditor resignation, delisting risk (2024)"},
    {"ticker": "RIVN", "category": "known_bad", "sector": "Consumer Discretionary",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Rivian -- SCA filed 2024, significant cash burn, uncertain path"},
    {"ticker": "LCID", "category": "known_bad", "sector": "Consumer Discretionary",
     "expected_tier_range": ["HIGH_RISK", "PROHIBITED"],
     "rationale": "Lucid -- SCA filed, heavy losses, going concern risk"},
    {"ticker": "COIN", "category": "known_bad", "sector": "Financials",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Coinbase -- SEC enforcement action, regulatory uncertainty"},
    {"ticker": "MPW", "category": "known_bad", "sector": "Real Estate",
     "expected_tier_range": ["HIGH_RISK", "PROHIBITED"],
     "rationale": "Medical Properties Trust -- short seller reports, tenant distress"},
    {"ticker": "WBD", "category": "known_bad", "sector": "Communication Services",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Warner Bros Discovery -- massive goodwill impairments, SCA risk"},
    {"ticker": "MSTR", "category": "known_bad", "sector": "Technology",
     "expected_tier_range": ["HIGH_RISK", "PROHIBITED"],
     "rationale": "MicroStrategy -- Bitcoin concentration, prior restatement history"},
    {"ticker": "NKLA", "category": "known_bad", "sector": "Industrials",
     "expected_tier_range": ["PROHIBITED", "PROHIBITED"],
     "rationale": "Nikola -- founder fraud conviction, near-insolvency"},

    # Edge Cases: Mixed signal profiles requiring nuanced judgment
    {"ticker": "TSLA", "category": "edge_case", "sector": "Consumer Discretionary",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Tesla -- key-person risk, governance concerns, SEC history"},
    {"ticker": "META", "category": "edge_case", "sector": "Technology",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "Meta -- large cap, clean financials but regulatory risk, privacy litigation"},
    {"ticker": "CRM", "category": "edge_case", "sector": "Technology",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "Salesforce -- strong growth but activist pressure, acquisition integration"},
    {"ticker": "SQ", "category": "edge_case", "sector": "Financials",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "Block/Square -- fintech growth but short seller attention, crypto exposure"},
    {"ticker": "PARA", "category": "edge_case", "sector": "Communication Services",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Paramount -- M&A uncertainty, declining linear TV, management turnover"},
    {"ticker": "DIS", "category": "edge_case", "sector": "Communication Services",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "Disney -- strong brand but streaming losses, proxy fight history"},
    {"ticker": "BA", "category": "edge_case", "sector": "Industrials",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Boeing -- DOJ settlement, 737 MAX fallout, quality control issues"},
    {"ticker": "INTC", "category": "edge_case", "sector": "Technology",
     "expected_tier_range": ["ELEVATED", "HIGH_RISK"],
     "rationale": "Intel -- strategic restructuring, market share loss, revenue decline"},

    # Recent Actuals: Companies that would appear on a Liberty deal list
    {"ticker": "SHW", "category": "recent_actual", "sector": "Materials",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Sherwin-Williams -- industrial leader, clean D&O profile"},
    {"ticker": "SNA", "category": "recent_actual", "sector": "Industrials",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Snap-on -- strong mid-cap, Liberty renewal account"},
    {"ticker": "NVDA", "category": "recent_actual", "sector": "Technology",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "NVIDIA -- mega-cap tech, AI concentration risk but strong fundamentals"},
    {"ticker": "JPM", "category": "recent_actual", "sector": "Financials",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "JPMorgan Chase -- largest bank, strong governance, clean record"},
    {"ticker": "AMZN", "category": "recent_actual", "sector": "Technology",
     "expected_tier_range": ["STANDARD", "ELEVATED"],
     "rationale": "Amazon -- massive enterprise, antitrust scrutiny but strong financials"},
    {"ticker": "LLY", "category": "recent_actual", "sector": "Healthcare",
     "expected_tier_range": ["PREFERRED", "STANDARD"],
     "rationale": "Eli Lilly -- pharma leader, strong pipeline, clean governance"},
]
"""Curated calibration ticker universe for shadow comparison.

30+ tickers covering:
- 10 known_good: Large-cap stable with clean governance
- 8 known_bad: Active litigation, enforcement, or distress
- 8 edge_cases: Mixed signals requiring nuanced judgment
- 6 recent_actuals: Companies typical of Liberty deal list
"""

# ---------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------

_TIER_ORDER_MAP = {
    "PREFERRED": 0, "STANDARD": 1, "ELEVATED": 2,
    "HIGH_RISK": 3, "PROHIBITED": 4,
}


class CalibrationRow(BaseModel):
    """One ticker's comparison result for shadow calibration."""

    ticker: str = Field(description="Stock ticker symbol")
    sector: str = Field(default="", description="Sector classification")
    market_cap_tier: str = Field(
        default="", description="Market cap tier: mega/large/mid/small"
    )
    category: str = Field(
        description="Calibration category: known_good/known_bad/edge_case/recent_actual"
    )

    # Legacy scoring
    legacy_score: float = Field(
        default=0.0, description="Legacy 10-factor quality score (0-100)"
    )
    legacy_tier: str = Field(
        default="STANDARD", description="Legacy tier (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH)"
    )

    # H/A/E scoring
    host_composite: float = Field(default=0.0, description="Host composite [0, 1]")
    agent_composite: float = Field(default=0.0, description="Agent composite [0, 1]")
    environment_composite: float = Field(
        default=0.0, description="Environment composite [0, 1]"
    )
    hae_product: float = Field(
        default=0.0, description="Multiplicative product P = H x A x E"
    )
    hae_tier: str = Field(
        default="STANDARD", description="H/A/E tier classification"
    )

    # Comparison
    tier_delta: int = Field(
        default=0,
        description="Signed tier delta: positive = H/A/E more restrictive",
    )
    crf_vetoes_active: list[str] = Field(
        default_factory=list,
        description="List of active CRF veto IDs",
    )
    interpretation: str = Field(
        default="",
        description="Auto-generated interpretation of the delta",
    )

    # Signal-driven vs rule-based factor comparison
    factor_scores_signal: dict[str, float] = Field(
        default_factory=dict,
        description="Factor ID -> signal-driven score (points deducted)",
    )
    factor_scores_rule: dict[str, float] = Field(
        default_factory=dict,
        description="Factor ID -> rule-based score (points deducted)",
    )
    signal_composite: float = Field(
        default=0.0,
        description="Total quality score from signal-driven factor path",
    )
    signal_coverage_avg: float = Field(
        default=0.0,
        description="Average signal coverage across factors (0.0-1.0)",
    )
    scoring_methods: dict[str, str] = Field(
        default_factory=dict,
        description="Factor ID -> scoring method ('signal_driven' or 'rule_based')",
    )

    # UW assessment (filled via HTML form)
    uw_assessment: str = Field(
        default="",
        description="UW tier assessment (from calibration form)",
    )
    uw_rationale: str = Field(
        default="",
        description="UW rationale for assessment (from calibration form)",
    )


class CalibrationMetrics(BaseModel):
    """Aggregate metrics for calibration comparison."""

    rank_correlation: float = Field(
        default=0.0,
        description="Spearman rank correlation between legacy and H/A/E scores",
    )
    tier_agreement_pct: float = Field(
        default=0.0,
        description="Percentage of tickers where |tier_delta| <= 1",
    )
    systematic_bias: float = Field(
        default=0.0,
        description="Mean tier delta (positive = H/A/E systematically more restrictive)",
    )
    extremes_agreement: bool = Field(
        default=False,
        description="Whether top/bottom 5 tickers agree between models",
    )
    all_criteria_met: bool = Field(
        default=False,
        description="All calibration criteria passed",
    )
    mean_factor_delta: float = Field(
        default=0.0,
        description="Mean absolute factor score delta (signal vs rule) across tickers",
    )
    avg_signal_coverage: float = Field(
        default=0.0,
        description="Average signal coverage across all factors and tickers",
    )
    signal_factor_count: int = Field(
        default=0,
        description="Count of factors using signal-driven path across all tickers",
    )
    rule_factor_count: int = Field(
        default=0,
        description="Count of factors using rule-based path across all tickers",
    )


# ---------------------------------------------------------------
# Synthetic data generation for stub mode
# ---------------------------------------------------------------


def _generate_synthetic_row(ticker_info: dict[str, Any]) -> CalibrationRow:
    """Generate a plausible CalibrationRow based on ticker category.

    Uses deterministic hashing from ticker name for reproducibility.
    """
    ticker = ticker_info["ticker"]
    category = ticker_info["category"]
    sector = ticker_info.get("sector", "")
    hash_val = sum(ord(c) for c in ticker) % 100

    # Generate scores based on category
    if category == "known_good":
        legacy_score = 78.0 + (hash_val % 18)  # 78-95
        h = 0.05 + (hash_val % 15) / 100.0  # 0.05-0.20
        a = 0.03 + (hash_val % 12) / 100.0  # 0.03-0.15
        e = 0.08 + (hash_val % 18) / 100.0  # 0.08-0.26
        legacy_tier = "WIN" if legacy_score >= 86 else "WANT"
    elif category == "known_bad":
        legacy_score = 12.0 + (hash_val % 33)  # 12-44
        h = 0.30 + (hash_val % 40) / 100.0  # 0.30-0.70
        a = 0.45 + (hash_val % 35) / 100.0  # 0.45-0.80
        e = 0.35 + (hash_val % 30) / 100.0  # 0.35-0.65
        if legacy_score < 20:
            legacy_tier = "NO_TOUCH"
        elif legacy_score < 31:
            legacy_tier = "WALK"
        else:
            legacy_tier = "WATCH"
    elif category == "edge_case":
        legacy_score = 45.0 + (hash_val % 30)  # 45-74
        h = 0.15 + (hash_val % 30) / 100.0  # 0.15-0.45
        a = 0.20 + (hash_val % 35) / 100.0  # 0.20-0.55
        e = 0.15 + (hash_val % 25) / 100.0  # 0.15-0.40
        if legacy_score >= 71:
            legacy_tier = "WRITE"
        elif legacy_score >= 51:
            legacy_tier = "WATCH"
        else:
            legacy_tier = "WALK"
    else:  # recent_actual
        legacy_score = 65.0 + (hash_val % 25)  # 65-89
        h = 0.08 + (hash_val % 20) / 100.0  # 0.08-0.28
        a = 0.05 + (hash_val % 18) / 100.0  # 0.05-0.23
        e = 0.10 + (hash_val % 22) / 100.0  # 0.10-0.32
        if legacy_score >= 86:
            legacy_tier = "WIN"
        elif legacy_score >= 71:
            legacy_tier = "WANT"
        else:
            legacy_tier = "WRITE"

    # Compute H/A/E product
    floor = 0.05
    p = max(h, floor) * max(a, floor) * max(e, floor)

    # Determine H/A/E tier from product
    if p < 0.01:
        hae_tier_str = "PREFERRED"
    elif p < 0.08:
        hae_tier_str = "STANDARD"
    elif p < 0.25:
        hae_tier_str = "ELEVATED"
    elif p < 0.50:
        hae_tier_str = "HIGH_RISK"
    else:
        hae_tier_str = "PROHIBITED"

    # Map legacy tier to numeric for delta
    legacy_tier_map = {
        "WIN": 0, "WANT": 1, "WRITE": 1,
        "WATCH": 2, "WALK": 3, "NO_TOUCH": 4,
    }
    legacy_num = legacy_tier_map.get(legacy_tier, 1)
    hae_num = _TIER_ORDER_MAP.get(hae_tier_str, 1)
    delta = hae_num - legacy_num

    # Market cap tier
    if legacy_score > 80:
        mct = "mega"
    elif legacy_score > 60:
        mct = "large"
    elif legacy_score > 40:
        mct = "mid"
    else:
        mct = "small"

    # Interpretation
    if abs(delta) == 0:
        interp = "Models agree on tier classification"
    elif delta > 0:
        interp = f"H/A/E is {delta} tier(s) more restrictive than legacy"
    else:
        interp = f"H/A/E is {abs(delta)} tier(s) less restrictive than legacy"

    return CalibrationRow(
        ticker=ticker,
        sector=sector,
        market_cap_tier=mct,
        category=category,
        legacy_score=round(legacy_score, 1),
        legacy_tier=legacy_tier,
        host_composite=round(h, 4),
        agent_composite=round(a, 4),
        environment_composite=round(e, 4),
        hae_product=round(p, 6),
        hae_tier=hae_tier_str,
        tier_delta=delta,
        crf_vetoes_active=[],
        interpretation=interp,
    )


# ---------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------


def _compute_rank_correlation(rows: list[CalibrationRow]) -> float:
    """Compute Spearman rank correlation between legacy and H/A/E scores.

    Uses inverse quality score for legacy (lower = worse = higher risk)
    and H/A/E product for the multiplicative model.
    """
    n = len(rows)
    if n < 3:
        return 0.0

    # Rank by legacy score (inverted: high score = low risk)
    legacy_sorted = sorted(range(n), key=lambda i: rows[i].legacy_score, reverse=True)
    legacy_ranks = [0.0] * n
    for rank, idx in enumerate(legacy_sorted):
        legacy_ranks[idx] = float(rank)

    # Rank by H/A/E product (high product = high risk)
    hae_sorted = sorted(range(n), key=lambda i: rows[i].hae_product)
    hae_ranks = [0.0] * n
    for rank, idx in enumerate(hae_sorted):
        hae_ranks[idx] = float(rank)

    # Spearman: 1 - (6 * sum(d^2)) / (n * (n^2 - 1))
    sum_d2 = sum((legacy_ranks[i] - hae_ranks[i]) ** 2 for i in range(n))
    denom = n * (n * n - 1)
    if denom == 0:
        return 0.0
    return round(1.0 - (6.0 * sum_d2) / denom, 4)


def _compute_metrics(rows: list[CalibrationRow]) -> CalibrationMetrics:
    """Compute aggregate calibration metrics from comparison rows."""
    if not rows:
        return CalibrationMetrics()

    rank_corr = _compute_rank_correlation(rows)

    # Tier agreement: |delta| <= 1
    agree_count = sum(1 for r in rows if abs(r.tier_delta) <= 1)
    tier_agreement = round(100.0 * agree_count / len(rows), 1)

    # Systematic bias
    mean_delta = sum(r.tier_delta for r in rows) / len(rows)

    # Extremes agreement: top/bottom 5 by each model
    by_legacy = sorted(rows, key=lambda r: r.legacy_score, reverse=True)
    by_hae = sorted(rows, key=lambda r: r.hae_product)
    top5_legacy = {r.ticker for r in by_legacy[:5]}
    top5_hae = {r.ticker for r in by_hae[:5]}
    bottom5_legacy = {r.ticker for r in by_legacy[-5:]}
    bottom5_hae = {r.ticker for r in by_hae[-5:]}
    extremes_ok = (
        len(top5_legacy & top5_hae) >= 3
        and len(bottom5_legacy & bottom5_hae) >= 3
    )

    all_met = (
        rank_corr >= 0.60
        and tier_agreement >= 70.0
        and abs(mean_delta) < 1.5
        and extremes_ok
    )

    # Signal-driven metrics
    total_factor_deltas: list[float] = []
    coverage_values: list[float] = []
    signal_count = 0
    rule_count = 0

    for r in rows:
        if r.factor_scores_signal and r.factor_scores_rule:
            for fid in r.factor_scores_signal:
                sig_score = r.factor_scores_signal.get(fid, 0.0)
                rule_score = r.factor_scores_rule.get(fid, 0.0)
                total_factor_deltas.append(abs(sig_score - rule_score))
        if r.signal_coverage_avg > 0:
            coverage_values.append(r.signal_coverage_avg)
        for method in r.scoring_methods.values():
            if method == "signal_driven":
                signal_count += 1
            else:
                rule_count += 1

    mean_factor_delta_val = (
        sum(total_factor_deltas) / len(total_factor_deltas)
        if total_factor_deltas else 0.0
    )
    avg_coverage = (
        sum(coverage_values) / len(coverage_values)
        if coverage_values else 0.0
    )

    return CalibrationMetrics(
        rank_correlation=rank_corr,
        tier_agreement_pct=tier_agreement,
        systematic_bias=round(mean_delta, 3),
        extremes_agreement=extremes_ok,
        all_criteria_met=all_met,
        mean_factor_delta=round(mean_factor_delta_val, 3),
        avg_signal_coverage=round(avg_coverage, 3),
        signal_factor_count=signal_count,
        rule_factor_count=rule_count,
    )


# ---------------------------------------------------------------
# Shadow calibration runner
# ---------------------------------------------------------------


def run_shadow_calibration(
    tickers: list[dict[str, Any]] | None = None,
) -> tuple[list[CalibrationRow], CalibrationMetrics]:
    """Run shadow calibration with synthetic data.

    This is a STUB that produces synthetic comparison data based on
    ticker category. The real pipeline run takes 20+ minutes per
    ticker and requires MCP tools.

    Args:
        tickers: Optional ticker list. Defaults to CALIBRATION_TICKERS.

    Returns:
        Tuple of (rows, metrics).
    """
    ticker_list = tickers or CALIBRATION_TICKERS
    rows = [_generate_synthetic_row(t) for t in ticker_list]
    metrics = _compute_metrics(rows)

    logger.info(
        "Shadow calibration: %d tickers, corr=%.3f, agreement=%.1f%%",
        len(rows), metrics.rank_correlation, metrics.tier_agreement_pct,
    )

    return rows, metrics


# ---------------------------------------------------------------
# Live calibration from pipeline
# ---------------------------------------------------------------


def calibrate_from_pipeline(state: Any) -> CalibrationRow | None:
    """Extract calibration data from a completed pipeline run.

    Args:
        state: AnalysisState from a completed pipeline run.

    Returns:
        CalibrationRow with real data, or None if scoring data missing.
    """
    if state.scoring is None:
        return None

    scoring = state.scoring
    ticker = state.company.identity.ticker if state.company else "UNKNOWN"
    sector = ""
    if state.company and state.company.sector:
        s = state.company.sector
        sector = s.value if hasattr(s, "value") else str(s)

    # Legacy scoring data
    legacy_score = scoring.quality_score
    legacy_tier = scoring.tier.tier.value if scoring.tier else "WRITE"

    # H/A/E scoring data
    hae = scoring.hae_result
    if hae is None:
        return None

    host = hae.composites.get("host", 0.0)
    agent = hae.composites.get("agent", 0.0)
    env = hae.composites.get("environment", 0.0)

    # Map legacy tier to numeric for delta
    from do_uw.stages.score.legacy_lens import LEGACY_TIER_MAP
    legacy_hae = LEGACY_TIER_MAP.get(legacy_tier, "STANDARD")
    legacy_num = _TIER_ORDER_MAP.get(legacy_hae, 1)
    hae_num = _TIER_ORDER_MAP.get(hae.tier.value, 1)
    delta = hae_num - legacy_num

    # Active CRF vetoes
    active_crfs = [v.crf_id for v in hae.crf_vetoes if v.is_active]

    # Market cap tier
    mct = "unknown"
    if state.company and state.company.market_cap:
        mc = float(state.company.market_cap.value)
        if mc >= 200e9:
            mct = "mega"
        elif mc >= 10e9:
            mct = "large"
        elif mc >= 2e9:
            mct = "mid"
        else:
            mct = "small"

    # Interpretation
    if abs(delta) == 0:
        interp = "Models agree"
    elif delta > 0:
        interp = f"H/A/E {delta} tier(s) more restrictive"
    else:
        interp = f"H/A/E {abs(delta)} tier(s) less restrictive"

    # Per-factor signal-driven vs rule-based comparison
    factor_scores_signal: dict[str, float] = {}
    factor_scores_rule: dict[str, float] = {}
    scoring_methods: dict[str, str] = {}
    coverage_values: list[float] = []

    for fs in scoring.factor_scores:
        fid = fs.factor_id
        scoring_methods[fid] = fs.scoring_method
        if fs.scoring_method == "signal_driven":
            factor_scores_signal[fid] = round(fs.points_deducted, 2)
            coverage_values.append(fs.signal_coverage)
        else:
            factor_scores_rule[fid] = round(fs.points_deducted, 2)

    signal_deductions = sum(factor_scores_signal.values())
    signal_composite = round(100.0 - signal_deductions, 1) if factor_scores_signal else 0.0
    signal_coverage_avg = (
        round(sum(coverage_values) / len(coverage_values), 3)
        if coverage_values else 0.0
    )

    return CalibrationRow(
        ticker=ticker,
        sector=sector,
        market_cap_tier=mct,
        category="pipeline_run",
        legacy_score=round(legacy_score, 1),
        legacy_tier=legacy_tier,
        host_composite=round(host, 4),
        agent_composite=round(agent, 4),
        environment_composite=round(env, 4),
        hae_product=round(hae.product_score, 6),
        hae_tier=hae.tier.value,
        tier_delta=delta,
        crf_vetoes_active=active_crfs,
        interpretation=interp,
        factor_scores_signal=factor_scores_signal,
        factor_scores_rule=factor_scores_rule,
        signal_composite=signal_composite,
        signal_coverage_avg=signal_coverage_avg,
        scoring_methods=scoring_methods,
    )


# ---------------------------------------------------------------
# Save report to disk
# ---------------------------------------------------------------


def save_calibration_report(
    rows: list[CalibrationRow],
    metrics: CalibrationMetrics,
    output_dir: str = "output",
) -> str:
    """Generate HTML report and save to output directory.

    Args:
        rows: Calibration comparison rows.
        metrics: Aggregate comparison metrics.
        output_dir: Output directory path.

    Returns:
        Full path to the saved report file.
    """
    html = generate_calibration_html(rows, metrics)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    report_path = out_path / "calibration_report.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Calibration report saved: %s", report_path)
    return str(report_path)
