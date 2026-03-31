"""Executive forensics scorer -- person-level risk scoring for D&O.

Scores each NEO/director across 6 dimensions, computes role-weighted
board aggregate. Config-driven from config/executive_scoring.json.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.executive_risk import BoardAggregateRisk, IndividualRiskScore
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.executive_data import extract_executive_data

logger = logging.getLogger(__name__)

# Keywords indicating prior litigation in biographical text
_LITIGATION_KEYWORDS = [
    "securities class action",
    "class action",
    "securities litigation",
    "derivative action",
    "shareholder lawsuit",
    "sec enforcement",
    "sec investigation",
    "sec action",
    "fraud",
    "indictment",
    "settlement",
    "consent decree",
]

# Keywords indicating company failures in biographical text
_FAILURE_KEYWORDS = [
    "bankruptcy",
    "chapter 11",
    "chapter 7",
    "liquidation",
    "receivership",
    "insolvency",
    "wind down",
    "delisted",
    "restatement",
    "material weakness",
]

# Keywords indicating regulatory enforcement
_ENFORCEMENT_KEYWORDS = [
    "sec enforcement",
    "sec action",
    "doj investigation",
    "department of justice",
    "state attorney general",
    "cease and desist",
    "administrative proceeding",
    "civil penalty",
    "disgorgement",
    "debarment",
]


def _load_config() -> dict[str, Any]:
    """Load executive scoring config from JSON."""
    return load_config("executive_scoring")


def _apply_time_decay(
    score: float,
    years_ago: float,
    half_life: float,
    minimum_weight: float,
) -> float:
    """Apply exponential time decay: score * max(2^(-years/half_life), min_weight)."""
    if years_ago <= 0:
        return score
    decay_factor = math.pow(2.0, -years_ago / half_life)
    return score * max(decay_factor, minimum_weight)


def _count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in text (case insensitive)."""
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _score_prior_litigation(
    exec_data: dict[str, Any],
    max_score: float,
    time_decay_config: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score prior litigation dimension (0 to max_score).

    Sources: prior_litigation list from SCAC + bio_summary text mining.
    Score 0 if no data (not "no risk" -- data may be missing).
    """
    findings: list[str] = []
    score = 0.0

    # Direct prior litigation records
    prior_lit = exec_data.get("prior_litigation", [])
    for lit_item in prior_lit:
        if lit_item:
            score += 10.0  # Each prior litigation finding is significant
            findings.append(f"Prior litigation: {lit_item[:100]}")

    # Bio text mining for litigation keywords
    bio = exec_data.get("bio_summary", "")
    lit_matches = _count_keyword_matches(bio, _LITIGATION_KEYWORDS)
    if lit_matches > 0:
        score += lit_matches * 5.0
        findings.append(f"Bio contains {lit_matches} litigation-related keyword(s)")

    return min(score, max_score), findings


def _score_regulatory_enforcement(
    exec_data: dict[str, Any],
    max_score: float,
    time_decay_config: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score regulatory enforcement dimension (0 to max_score).

    Sources: prior_enforcement list + bio text mining for enforcement keywords.
    """
    findings: list[str] = []
    score = 0.0

    # Direct enforcement records
    prior_enforcement = exec_data.get("prior_enforcement", [])
    for enf_item in prior_enforcement:
        if enf_item:
            score += 12.0
            findings.append(f"Regulatory enforcement: {enf_item[:100]}")

    # Bio text mining
    bio = exec_data.get("bio_summary", "")
    enf_matches = _count_keyword_matches(bio, _ENFORCEMENT_KEYWORDS)
    if enf_matches > 0:
        score += enf_matches * 5.0
        findings.append(f"Bio contains {enf_matches} enforcement-related keyword(s)")

    return min(score, max_score), findings


def _score_prior_company_failures(
    exec_data: dict[str, Any],
    max_score: float,
    time_decay_config: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score prior company failures dimension (0 to max_score).

    Sources: prior_restatements list + bio text mining for failure keywords.
    """
    findings: list[str] = []
    score = 0.0

    # Prior restatements
    restatements = exec_data.get("prior_restatements", [])
    for rst in restatements:
        if rst:
            score += 7.0
            findings.append(f"Prior restatement: {rst[:100]}")

    # Bio text mining for failure keywords
    bio = exec_data.get("bio_summary", "")
    failure_matches = _count_keyword_matches(bio, _FAILURE_KEYWORDS)
    if failure_matches > 0:
        score += failure_matches * 4.0
        findings.append(f"Bio contains {failure_matches} failure-related keyword(s)")

    return min(score, max_score), findings


def _score_insider_trading_patterns(
    exec_data: dict[str, Any],
    max_score: float,
) -> tuple[float, list[str]]:
    """Score insider trading patterns dimension (0 to max_score).

    Analyzes Form 4 trades for this person:
    - Net selling trend
    - Sales outside 10b5-1 plans
    - Cluster timing with other insiders
    """
    findings: list[str] = []
    score = 0.0

    trades = exec_data.get("insider_trades", [])
    if not trades:
        return 0.0, []

    # Compute net buy/sell
    total_buy_value = 0.0
    total_sell_value = 0.0
    discretionary_sells = 0
    total_sells = 0

    for trade in trades:
        ttype = (trade.get("transaction_type") or "").upper()
        value = trade.get("total_value") or 0.0

        if ttype == "SELL" or ttype == "S":
            total_sell_value += abs(value)
            total_sells += 1
            if trade.get("is_discretionary", False):
                discretionary_sells += 1
        elif ttype == "BUY" or ttype == "P":
            total_buy_value += abs(value)

    # Net selling pattern
    if total_sell_value > total_buy_value * 2 and total_sell_value > 100_000:
        score += 4.0
        findings.append(
            f"Net seller: ${total_sell_value:,.0f} sold vs ${total_buy_value:,.0f} bought"
        )

    # Discretionary selling (not under 10b5-1)
    if total_sells > 0 and discretionary_sells > 0:
        disc_ratio = discretionary_sells / total_sells
        if disc_ratio > 0.5:
            score += 3.0
            findings.append(
                f"{discretionary_sells}/{total_sells} sales are discretionary (not 10b5-1)"
            )
        elif disc_ratio > 0:
            score += 1.5
            findings.append(
                f"{discretionary_sells}/{total_sells} sales are discretionary"
            )

    # Volume of selling activity
    if total_sells >= 5:
        score += 2.0
        findings.append(f"High selling frequency: {total_sells} sell transactions")

    return min(score, max_score), findings


def _score_tenure_stability(
    exec_data: dict[str, Any],
    max_score: float,
) -> tuple[float, list[str]]:
    """Score tenure stability dimension (0 to max_score).

    Short tenure (<2 years) in current role = higher risk.
    Recent appointment or interim status = elevated.
    """
    findings: list[str] = []
    score = 0.0

    tenure_years = exec_data.get("years_tenure")
    is_interim = exec_data.get("is_interim", False)
    is_recent = exec_data.get("officer_change_recent", False)
    role = exec_data.get("role", "Other")

    if is_interim:
        score += 3.0
        findings.append("Serving in interim capacity")

    if tenure_years is not None:
        if tenure_years < 1.0:
            score += 2.5
            findings.append(f"Very short tenure: {tenure_years:.1f} years")
        elif tenure_years < 2.0:
            score += 1.5
            findings.append(f"Short tenure: {tenure_years:.1f} years")

    if is_recent and role in ("CEO", "CFO", "CAO"):
        score += 1.0
        findings.append(f"Recent {role} appointment (<1 year)")

    return min(score, max_score), findings


def score_individual_risk(
    exec_data: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> IndividualRiskScore:
    """Score a single executive across 6 risk dimensions.

    Each dimension is scored from 0 to its maximum (from config).
    Total score is the sum of all dimensions (0-100 theoretical max).

    Args:
        exec_data: Dict from extract_executive_data with person's data
        config: Executive scoring config (loaded from file if None)

    Returns:
        IndividualRiskScore with all dimensions populated
    """
    if config is None:
        config = _load_config()

    dim_max = config.get("dimension_max_scores", {})
    time_decay_config = config.get("time_decay", {})
    role_weights = config.get("role_weights", {})

    name = exec_data.get("name", "Unknown")
    role = exec_data.get("role", "Other")
    role_weight = exec_data.get("role_weight", role_weights.get(role, 1.0))

    all_findings: list[str] = []
    all_sources: list[str] = []
    time_decay_applied = False

    # Dimension 1: Prior litigation (0-25)
    lit_score, lit_findings = _score_prior_litigation(
        exec_data, dim_max.get("prior_litigation", 25), time_decay_config
    )
    all_findings.extend(lit_findings)

    # Dimension 2: Regulatory enforcement (0-25)
    enf_score, enf_findings = _score_regulatory_enforcement(
        exec_data, dim_max.get("regulatory_enforcement", 25), time_decay_config
    )
    all_findings.extend(enf_findings)

    # Dimension 3: Prior company failures (0-15)
    fail_score, fail_findings = _score_prior_company_failures(
        exec_data, dim_max.get("prior_company_failures", 15), time_decay_config
    )
    all_findings.extend(fail_findings)

    # Dimension 4: Insider trading patterns (0-10)
    trade_score, trade_findings = _score_insider_trading_patterns(
        exec_data, dim_max.get("insider_trading_patterns", 10)
    )
    all_findings.extend(trade_findings)

    # Dimension 5: Negative news (0-10) -- deferred, always 0
    news_score = 0.0

    # Dimension 6: Tenure stability (0-5)
    tenure_score, tenure_findings = _score_tenure_stability(
        exec_data, dim_max.get("tenure_stability", 5)
    )
    all_findings.extend(tenure_findings)

    total = lit_score + enf_score + fail_score + trade_score + news_score + tenure_score

    # Build source list from data available
    if exec_data.get("prior_litigation"):
        all_sources.append("Stanford SCAC")
    if exec_data.get("prior_enforcement"):
        all_sources.append("SEC enforcement records")
    if exec_data.get("insider_trades"):
        all_sources.append("SEC Form 4 filings")
    if exec_data.get("bio_summary"):
        all_sources.append("DEF 14A biography")

    return IndividualRiskScore(
        person_name=name,
        role=role,
        role_weight=role_weight,
        total_score=round(total, 2),
        prior_litigation=round(lit_score, 2),
        regulatory_enforcement=round(enf_score, 2),
        prior_company_failures=round(fail_score, 2),
        insider_trading_patterns=round(trade_score, 2),
        negative_news=round(news_score, 2),
        tenure_stability=round(tenure_score, 2),
        time_decay_applied=time_decay_applied,
        findings=all_findings,
        sources=all_sources,
    )


def compute_board_aggregate_risk(
    individual_scores: list[IndividualRiskScore],
    config: dict[str, Any] | None = None,
) -> BoardAggregateRisk:
    """Compute role-weighted aggregate risk from individual scores.

    Weighted average: sum(score * role_weight) / sum(role_weights).
    Identifies highest-risk individual and collects key findings.

    Args:
        individual_scores: List of IndividualRiskScore for all assessed persons
        config: Executive scoring config (loaded from file if None)

    Returns:
        BoardAggregateRisk with aggregate score and findings
    """
    if config is None:
        config = _load_config()

    if not individual_scores:
        return BoardAggregateRisk(
            weighted_score=0.0,
            individual_scores=[],
            highest_risk_individual="",
            key_findings=["No executive data available for scoring"],
        )

    # Weighted average
    total_weighted = sum(s.total_score * s.role_weight for s in individual_scores)
    total_weights = sum(s.role_weight for s in individual_scores)

    weighted_score = total_weighted / total_weights if total_weights > 0 else 0.0

    # Identify highest-risk individual (by weighted score)
    highest = max(
        individual_scores,
        key=lambda s: s.total_score * s.role_weight,
    )

    # Collect key findings (top findings from scored individuals)
    key_findings: list[str] = []
    for score in individual_scores:
        if score.total_score > 0:
            for finding in score.findings[:3]:
                key_findings.append(f"[{score.person_name} ({score.role})]: {finding}")

    # Add risk level classification
    thresholds = config.get("aggregate_thresholds", {})
    if weighted_score >= thresholds.get("critical", 85):
        key_findings.insert(0, "CRITICAL board aggregate risk")
    elif weighted_score >= thresholds.get("high", 70):
        key_findings.insert(0, "HIGH board aggregate risk")
    elif weighted_score >= thresholds.get("elevated", 50):
        key_findings.insert(0, "ELEVATED board aggregate risk")
    elif weighted_score >= thresholds.get("moderate", 35):
        key_findings.insert(0, "MODERATE board aggregate risk")

    return BoardAggregateRisk(
        weighted_score=round(weighted_score, 2),
        individual_scores=individual_scores,
        highest_risk_individual=highest.person_name,
        key_findings=key_findings,
    )


def run_executive_forensics(
    state: AnalysisState,
) -> BoardAggregateRisk | None:
    """Run the full executive forensics pipeline.

    Orchestrator: extract data -> score each executive -> compute aggregate.
    Returns None if no executive data available (graceful degradation).

    Args:
        state: The AnalysisState with extracted governance and market data

    Returns:
        BoardAggregateRisk or None if insufficient data
    """
    config = _load_config()

    # Extract standardized executive data from state
    exec_data_list = extract_executive_data(state)
    if not exec_data_list:
        logger.info("No executive data available -- skipping executive forensics")
        return None

    # Score each executive
    individual_scores: list[IndividualRiskScore] = []
    for exec_data in exec_data_list:
        score = score_individual_risk(exec_data, config)
        individual_scores.append(score)
        if score.total_score > 0:
            logger.info(
                "Executive %s (%s): score=%.1f",
                score.person_name,
                score.role,
                score.total_score,
            )

    # Compute board aggregate
    aggregate = compute_board_aggregate_risk(individual_scores, config)
    logger.info(
        "Board aggregate risk: %.1f (highest: %s)",
        aggregate.weighted_score,
        aggregate.highest_risk_individual,
    )

    return aggregate


__all__ = [
    "compute_board_aggregate_risk",
    "run_executive_forensics",
    "score_individual_risk",
]
