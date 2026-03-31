"""Earnings guidance and analyst sentiment extraction (SECT4-06, SECT4-07).

Extracts quarterly earnings beat/miss records from yfinance earnings
history, computes guidance philosophy classification, and builds analyst
sentiment profiles from recommendation and target-price data.

Usage:
    guidance, report = extract_earnings_guidance(state)
    state.extracted.market.earnings_guidance = guidance

    sentiment, report = extract_analyst_sentiment(state)
    state.extracted.market.analyst = sentiment
"""

from __future__ import annotations

import logging
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from do_uw.models.common import Confidence
from do_uw.models.market_events import (
    AnalystSentimentProfile,
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    EarningsResult,
    GuidancePhilosophy,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.earnings_guidance_classify import (
    _consensus_from_mean,
    classify_result,
    compute_consecutive_misses,
    compute_philosophy,
)
from do_uw.stages.extract.sourced import (
    get_market_data,
    sourced_float,
    sourced_int,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Source attribution constants.
_YFINANCE_EARNINGS = "yfinance earnings_dates"
_YFINANCE_INFO = "yfinance info"
_YFINANCE_RECS = "yfinance recommendations"
_YFINANCE_UPGRADES = "yfinance upgrades_downgrades"

# Expected fields for earnings guidance extraction report.
EXPECTED_GUIDANCE_FIELDS: list[str] = [
    "quarters",
    "beat_rate",
    "consecutive_miss_count",
    "philosophy",
]

# Expected fields for analyst sentiment extraction report.
EXPECTED_SENTIMENT_FIELDS: list[str] = [
    "coverage_count",
    "consensus",
    "recommendation_mean",
    "target_price_mean",
    "target_price_high",
    "target_price_low",
    "recent_upgrades",
    "recent_downgrades",
]


# ---------------------------------------------------------------------------
# Forward guidance detection -- patterns match explicit guidance language
# but NOT boilerplate "forward-looking statements" disclaimers.
# ---------------------------------------------------------------------------

_GUIDANCE_PATTERN = re.compile(
    r"we\s+expect\s+(?:revenue|earnings|sales|net\s+income|EPS)"
    r"|(?:our|the\s+company'?s?)\s+(?:outlook|guidance|forecast)\s+(?:for|is|remains)"
    r"|guidance\s+range"
    r"|we\s+(?:anticipate|project|forecast)\s+(?:revenue|net\s+income|EPS|earnings)"
    r"|full[- ]year\s+(?:\d{4}\s+)?(?:revenue|earnings)\s+(?:guidance|outlook)"
    r"|(?:raises?|lowers?|maintains?|reaffirms?|reiterates?|withdraws?)\s+(?:its?\s+)?(?:full[- ]year\s+)?guidance"
    r"|(?:fiscal\s+)?(?:20\d{2}|FY\d{2})\s+(?:revenue|earnings|EPS)\s+(?:guidance|outlook|forecast)"
    r"|we\s+(?:are\s+)?(?:providing|issuing|updating)\s+(?:our\s+)?(?:financial\s+)?guidance",
    re.IGNORECASE,
)


def detect_forward_guidance(filing_text: str) -> bool:
    """Detect explicit forward guidance language in filing text.

    Returns True if the text contains revenue/earnings forecasts or outlook
    statements. Standard SEC "forward-looking statements" disclaimers do NOT
    trigger detection.
    """
    if not filing_text or not filing_text.strip():
        return False
    return _GUIDANCE_PATTERN.search(filing_text) is not None


# ---------------------------------------------------------------------------
# Earnings guidance extraction (SECT4-06)
# ---------------------------------------------------------------------------


def _safe_float(value: Any) -> float | None:
    """Safely extract a float from a value that may be NaN or missing."""
    if value is None:
        return None
    try:
        f = float(value)
    except (ValueError, TypeError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _parse_earnings_dates(
    market_data: dict[str, Any],
) -> list[EarningsQuarterRecord]:
    """Parse yfinance earnings_dates into quarter records.

    The earnings_dates dict comes from yfinance Ticker.earnings_dates
    as a DataFrame-to-dict conversion. Keys may include:
    'EPS Estimate', 'Reported EPS', 'Surprise(%)'.
    Index is datetime-based (earnings dates).
    """
    raw_val = market_data.get("earnings_dates")
    if raw_val is None or not isinstance(raw_val, dict):
        return []
    raw = cast(dict[str, Any], raw_val)

    # yfinance earnings_dates may arrive in two formats:
    #   1. dict-of-dicts: column -> {date_str: value}  (index-oriented)
    #   2. dict-of-lists: column -> [value, ...]        (list-oriented)
    # Both formats include an "Earnings Date" key with the date index.
    # We normalize to dict-of-dicts keyed by date string.
    def _normalize_col(
        col_val: Any, date_keys: list[str]
    ) -> dict[str, Any]:
        """Normalize a column value to {date_str: value} dict."""
        if isinstance(col_val, dict):
            return cast(dict[str, Any], col_val)
        if isinstance(col_val, list):
            # Zip list values with date keys from the Earnings Date col.
            typed_list = cast(list[Any], col_val)
            return {
                str(k): v
                for k, v in zip(date_keys, typed_list, strict=False)
            }
        return {}

    # Build date keys from the Earnings Date column (for list format).
    raw_dates: Any = raw.get(
        "Earnings Date", raw.get("earnings_dates", [])
    )
    if isinstance(raw_dates, list):
        date_keys = [str(d) for d in cast(list[Any], raw_dates)]
    elif isinstance(raw_dates, dict):
        date_keys = [
            str(k) for k in cast(dict[str, Any], raw_dates)
        ]
    else:
        date_keys = []

    eps_estimate_col = _normalize_col(
        raw.get("EPS Estimate", {}), date_keys
    )
    reported_eps_col = _normalize_col(
        raw.get("Reported EPS", {}), date_keys
    )
    surprise_col = _normalize_col(raw.get("Surprise(%)", {}), date_keys)

    # Collect all date keys across columns.
    all_dates: set[str] = set()
    for col in [eps_estimate_col, reported_eps_col, surprise_col]:
        all_dates.update(str(k) for k in col)
    # Also include date keys from the Earnings Date column itself
    # (in list format, dates may only appear there).
    if date_keys:
        all_dates.update(date_keys)

    records: list[EarningsQuarterRecord] = []
    for date_str in sorted(all_dates, reverse=True):
        estimate = _safe_float(eps_estimate_col.get(date_str))
        actual = _safe_float(reported_eps_col.get(date_str))
        surprise = _safe_float(surprise_col.get(date_str))

        # If we have no actual EPS, this is a future date -- skip.
        if actual is None:
            continue

        result, miss_mag = classify_result(estimate, actual)

        # Build quarter label from date string (best effort).
        quarter_label = _date_to_quarter_label(date_str)

        # yfinance "Surprise(%)" is EPS surprise, NOT stock price reaction.
        # Clamp to ±100% to prevent absurd values (41076%) from displaying.
        # Real stock returns are computed by compute_earnings_reactions() from
        # price history and used as fallback in build_earnings_trust().
        stock_reaction: float | None = None
        if surprise is not None:
            # Only use as stock reaction proxy if magnitude is plausible (<100%)
            if abs(surprise) <= 100:
                stock_reaction = surprise

        record = EarningsQuarterRecord(
            quarter=quarter_label,
            actual_eps=sourced_float(
                actual, _YFINANCE_EARNINGS, Confidence.MEDIUM
            ),
            result=result,
        )
        if estimate is not None:
            record.consensus_eps_low = sourced_float(
                estimate, _YFINANCE_EARNINGS, Confidence.MEDIUM
            )
            record.consensus_eps_high = sourced_float(
                estimate, _YFINANCE_EARNINGS, Confidence.MEDIUM
            )
        if miss_mag is not None:
            record.miss_magnitude_pct = sourced_float(
                miss_mag, _YFINANCE_EARNINGS, Confidence.MEDIUM
            )
        if stock_reaction is not None:
            record.stock_reaction_pct = sourced_float(
                stock_reaction, _YFINANCE_EARNINGS, Confidence.LOW
            )

        records.append(record)

    return records


def _date_to_quarter_label(date_str: str) -> str:
    """Convert a date string to a quarter label like 'Q3 2025'.

    Handles various yfinance date formats. Falls back to the
    raw string if parsing fails.
    """
    try:
        # yfinance dates may have timezone info.
        cleaned = date_str.strip().split("+")[0].split(" ")[0]
        parts = cleaned.split("-")
        if len(parts) >= 2:
            year = parts[0]
            month = int(parts[1])
            quarter = (month - 1) // 3 + 1
            return f"Q{quarter} {year}"
    except (ValueError, IndexError):
        pass
    return date_str[:10]


def extract_earnings_guidance(
    state: AnalysisState,
    guidance_text: str | None = None,
) -> tuple[EarningsGuidanceAnalysis, ExtractionReport]:
    """Extract earnings guidance analysis from market data (SECT4-06).

    Reads earnings_dates from state.acquired_data.market_data, builds
    per-quarter records, and computes beat rate / philosophy.

    Args:
        state: Analysis state with acquired market data.
        guidance_text: Filing text for forward guidance detection (optional).
    """
    market_data = get_market_data(state)
    found_fields: list[str] = []
    warnings: list[str] = []

    analysis = EarningsGuidanceAnalysis()

    # Parse quarterly records.
    try:
        records = _parse_earnings_dates(market_data)
    except (KeyError, TypeError, ValueError) as exc:
        warnings.append(f"Error parsing earnings_dates: {exc}")
        records = []

    if records:
        analysis.quarters = records
        found_fields.append("quarters")

        # Compute beat rate.
        classified = [r for r in records if r.result != ""]
        if classified:
            beats = sum(
                1 for r in classified if r.result == EarningsResult.BEAT
            )
            beat_rate = beats / len(classified)
            analysis.beat_rate = sourced_float(
                round(beat_rate, 4),
                _YFINANCE_EARNINGS,
                Confidence.MEDIUM,
            )
            found_fields.append("beat_rate")

            # Consecutive misses.
            analysis.consecutive_miss_count = compute_consecutive_misses(
                records
            )
            found_fields.append("consecutive_miss_count")

            # Philosophy.
            analysis.philosophy = compute_philosophy(beat_rate)
            found_fields.append("philosophy")
        else:
            analysis.philosophy = GuidancePhilosophy.NO_GUIDANCE
            found_fields.append("philosophy")
    else:
        analysis.philosophy = GuidancePhilosophy.NO_GUIDANCE
        found_fields.append("philosophy")
        warnings.append("No earnings history available")

    # Detect forward guidance from filing text.
    if guidance_text:
        analysis.provides_forward_guidance = detect_forward_guidance(guidance_text)
        logger.info("Forward guidance detected: %s", analysis.provides_forward_guidance)

    report = create_report(
        extractor_name="earnings_guidance",
        expected=EXPECTED_GUIDANCE_FIELDS,
        found=found_fields,
        source_filing=_YFINANCE_EARNINGS,
        warnings=warnings,
    )
    log_report(report)
    return analysis, report


# ---------------------------------------------------------------------------
# Analyst sentiment extraction (SECT4-07)
# ---------------------------------------------------------------------------


def _extract_target_prices(
    info: dict[str, Any],
) -> dict[str, float | None]:
    """Extract target price data from yfinance info dict."""
    return {
        "mean": _safe_float(info.get("targetMeanPrice")),
        "high": _safe_float(info.get("targetHighPrice")),
        "low": _safe_float(info.get("targetLowPrice")),
    }


def _count_recent_changes(
    upgrades_downgrades: Any,
    days: int = 90,
) -> tuple[int, int]:
    """Count recent upgrades and downgrades within trailing days.

    The upgrades_downgrades data from yfinance may be a dict with
    date-indexed entries containing 'Action' field.

    Returns (upgrades, downgrades) counts.
    """
    upgrades = 0
    downgrades = 0

    if not isinstance(upgrades_downgrades, dict):
        return 0, 0
    ud_dict = cast(dict[str, Any], upgrades_downgrades)

    cutoff = datetime.now(tz=UTC) - timedelta(days=days)

    # yfinance returns columns: Firm, ToGrade, FromGrade, Action
    raw_action = ud_dict.get("Action", {})
    if not isinstance(raw_action, dict):
        return 0, 0
    action_col = cast(dict[str, Any], raw_action)

    for date_key_raw, action_raw in action_col.items():
        date_key = str(date_key_raw)
        action = str(action_raw)
        # Try to parse the date key.
        try:
            date_str = date_key.strip().split("+")[0].split(" ")[0]
            parts = date_str.split("-")
            if len(parts) >= 3:
                dt = datetime(
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                    tzinfo=UTC,
                )
                if dt < cutoff:
                    continue
        except (ValueError, IndexError):
            continue

        action_str = action.lower()
        if "up" in action_str:
            upgrades += 1
        elif "down" in action_str:
            downgrades += 1

    return upgrades, downgrades


def extract_analyst_sentiment(
    state: AnalysisState,
) -> tuple[AnalystSentimentProfile, ExtractionReport]:
    """Extract analyst sentiment profile from market data (SECT4-07).

    Reads yfinance info, recommendations, and upgrades_downgrades from
    state.acquired_data.market_data.

    Args:
        state: Analysis state with acquired market data.

    Returns:
        Tuple of (AnalystSentimentProfile, ExtractionReport).
    """
    market_data = get_market_data(state)
    found_fields: list[str] = []
    warnings: list[str] = []

    profile = AnalystSentimentProfile()

    # -- Info dict: coverage count, recommendation mean, target prices --
    raw_info = market_data.get("info")
    info: dict[str, Any] = (
        cast(dict[str, Any], raw_info)
        if raw_info is not None and isinstance(raw_info, dict)
        else {}
    )

    # Coverage count from numberOfAnalystOpinions.
    analyst_count = _safe_float(info.get("numberOfAnalystOpinions"))
    if analyst_count is not None:
        profile.coverage_count = sourced_int(
            int(analyst_count), _YFINANCE_INFO, Confidence.MEDIUM
        )
        found_fields.append("coverage_count")
        # Also populate analyst_count (DN-033 easy-win).
        profile.analyst_count = sourced_int(
            int(analyst_count), _YFINANCE_INFO, Confidence.MEDIUM
        )

    # Recommendation mean.
    rec_mean = _safe_float(info.get("recommendationMean"))
    if rec_mean is not None:
        profile.recommendation_mean = sourced_float(
            round(rec_mean, 2), _YFINANCE_INFO, Confidence.MEDIUM
        )
        found_fields.append("recommendation_mean")

        # Derive consensus from mean.
        profile.consensus = sourced_str(
            _consensus_from_mean(rec_mean),
            _YFINANCE_INFO,
            Confidence.MEDIUM,
        )
        found_fields.append("consensus")

    # Target prices.
    targets = _extract_target_prices(info)
    if targets["mean"] is not None:
        profile.target_price_mean = sourced_float(
            targets["mean"], _YFINANCE_INFO, Confidence.MEDIUM
        )
        found_fields.append("target_price_mean")
    if targets["high"] is not None:
        profile.target_price_high = sourced_float(
            targets["high"], _YFINANCE_INFO, Confidence.MEDIUM
        )
        found_fields.append("target_price_high")
    if targets["low"] is not None:
        profile.target_price_low = sourced_float(
            targets["low"], _YFINANCE_INFO, Confidence.MEDIUM
        )
        found_fields.append("target_price_low")

    # -- Upgrades/downgrades --
    raw_ud = market_data.get("upgrades_downgrades")
    try:
        ups, downs = _count_recent_changes(raw_ud, days=90)
        profile.recent_upgrades = ups
        profile.recent_downgrades = downs
        found_fields.append("recent_upgrades")
        found_fields.append("recent_downgrades")
    except (KeyError, TypeError, ValueError) as exc:
        warnings.append(f"Error parsing upgrades_downgrades: {exc}")

    report = create_report(
        extractor_name="analyst_sentiment",
        expected=EXPECTED_SENTIMENT_FIELDS,
        found=found_fields,
        source_filing=_YFINANCE_INFO,
        warnings=warnings,
    )
    log_report(report)
    return profile, report
