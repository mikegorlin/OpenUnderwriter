"""Multi-signal peer group construction for benchmarking.

Constructs a peer group using composite scoring across 5 signals:
SIC code match, industry match, market cap proximity, revenue
similarity, and business description overlap.

Covers SECT2-09 (peer group) and SECT3-05 (peer benchmarking foundation).

See also: peer_scoring.py (signal scoring functions, composite score).

Usage:
    peer_group, report = construct_peer_group(state)
    state.extracted.financials.peer_group = peer_group
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from do_uw.models.financials import PeerCompany, PeerGroup
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.peer_scoring import (
    compute_composite_score,
    score_description_overlap,
    score_industry_match,
    score_market_cap_proximity,
    score_revenue_similarity,
    score_sic_match,
)
from do_uw.stages.extract.sourced import (
    get_info_dict,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Cache for financedatabase equities data
_FD_CACHE_PATH = Path(".cache/financedatabase_equities.pkl")
_FD_CACHE_MAX_AGE_DAYS = 7


def _load_equities_data() -> Any | None:
    """Load equities data from financedatabase with local cache."""
    import pickle
    import time
    from financedatabase import Equities

    # Ensure cache directory exists
    _FD_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Check cache freshness
    if _FD_CACHE_PATH.exists():
        cache_age = time.time() - _FD_CACHE_PATH.stat().st_mtime
        if cache_age < _FD_CACHE_MAX_AGE_DAYS * 86400:
            try:
                with open(_FD_CACHE_PATH, "rb") as f:
                    logger.debug("Loading equities data from cache")
                    return pickle.load(f)
            except Exception:
                logger.warning("Failed to load cached equities data")

    # Download fresh data
    try:
        logger.info("Downloading financedatabase equities data (may take a moment)")
        equities = Equities()
        with open(_FD_CACHE_PATH, "wb") as f:
            pickle.dump(equities, f)
        return equities
    except Exception as e:
        logger.warning(f"Failed to download financedatabase data: {e}")
        # Try to load stale cache as fallback
        if _FD_CACHE_PATH.exists():
            try:
                with open(_FD_CACHE_PATH, "rb") as f:
                    logger.warning("Using stale cache as fallback")
                    return pickle.load(f)
            except Exception:
                pass
    return None


# Target peer count and limits.
TARGET_PEER_COUNT: int = 10
MIN_PEER_COUNT: int = 5
MAX_CANDIDATES: int = 10

# Market cap band multipliers.
MCAP_BAND_TIGHT: tuple[float, float] = (0.5, 2.0)
MCAP_BAND_WIDE: tuple[float, float] = (0.3, 3.0)


# ---------------------------------------------------------------------------
# Sector ETF lookup
# ---------------------------------------------------------------------------


def _default_sectors_path() -> Path:
    """Return default path to brain/sectors.json."""
    return Path(__file__).parent.parent.parent / "brain" / "config" / "sectors.json"


def _get_sector_etf(sector_code: str) -> str | None:
    """Look up sector ETF ticker from sectors.json."""
    sectors_path = _default_sectors_path()
    if not sectors_path.exists():
        return None

    with sectors_path.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    etfs = data.get("sector_etfs")
    if not isinstance(etfs, dict):
        return None

    sector_data = cast(dict[str, Any], etfs).get(sector_code)
    if isinstance(sector_data, dict):
        primary = cast(dict[str, Any], sector_data).get("primary")
        if isinstance(primary, str):
            return primary
    return None


# ---------------------------------------------------------------------------
# Peer tier assignment
# ---------------------------------------------------------------------------


def _assign_tier(
    peer: PeerCompany,
    target_sic: str,
) -> str:
    """Assign a peer tier based on matching signals."""
    peer_sic = peer.sic_code or ""
    target_padded = target_sic.ljust(4, "0")
    peer_padded = peer_sic.ljust(4, "0")

    if target_padded == peer_padded:
        return "primary_sic"
    if peer.industry is not None:
        return "sector_etf"
    return "market_cap_cohort"


# ---------------------------------------------------------------------------
# Candidate fetching
# ---------------------------------------------------------------------------


# yfinance sector names differ from financedatabase (GICS) names.
_SECTOR_NAME_MAP: dict[str, str] = {
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Technology": "Information Technology",
    "Financial Services": "Financials",
    "Basic Materials": "Materials",
    "Communication Services": "Communication Services",
    "Healthcare": "Health Care",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "Real Estate": "Real Estate",
}


# Hardcoded sector peer fallbacks for when financedatabase is unavailable.
_SECTOR_FALLBACK_PEERS: dict[str, list[str]] = {
    "Technology": ["MSFT", "GOOGL", "AMZN", "META", "NVDA", "CRM", "ADBE", "ORCL", "CSCO", "INTC"],
    "Information Technology": [
        "MSFT",
        "AAPL",
        "NVDA",
        "AVGO",
        "CRM",
        "ADBE",
        "ORCL",
        "CSCO",
        "INTC",
        "AMD",
    ],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "CMG"],
    "Consumer Discretionary": [
        "AMZN",
        "TSLA",
        "HD",
        "MCD",
        "NKE",
        "SBUX",
        "LOW",
        "TJX",
        "BKNG",
        "CMG",
    ],
    "Healthcare": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    "Health Care": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    "Financial Services": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "BLK", "SCHW"],
    "Financials": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "BLK", "SCHW"],
    "Communication Services": [
        "GOOGL",
        "META",
        "NFLX",
        "DIS",
        "CMCSA",
        "T",
        "VZ",
        "TMUS",
        "CHTR",
        "EA",
    ],
    "Industrials": ["GE", "CAT", "HON", "UNP", "RTX", "BA", "DE", "LMT", "UPS", "MMM"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "PXD"],
    "Consumer Defensive": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "MDLZ", "KHC"],
    "Consumer Staples": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "MDLZ", "KHC"],
    "Basic Materials": ["LIN", "APD", "ECL", "SHW", "NEM", "FCX", "NUE", "DOW", "DD", "PPG"],
    "Materials": ["LIN", "APD", "ECL", "SHW", "NEM", "FCX", "NUE", "DOW", "DD", "PPG"],
    "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "SPG", "PSA", "O", "DLR", "WELL", "AVB"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "WEC", "ED"],
}


def _get_sector_fallback_peers(
    target_sector: str,
    target_ticker: str,
) -> list[dict[str, Any]]:
    """Return hardcoded sector peers when financedatabase is unavailable."""
    peers = _SECTOR_FALLBACK_PEERS.get(target_sector, [])
    return [
        {"symbol": p, "name": "", "sector": target_sector, "industry": ""}
        for p in peers
        if p != target_ticker
    ]


def _is_us_ticker(symbol: str) -> bool:
    """Check if a ticker symbol looks like a US exchange listing."""
    # Filter out non-US: .L (London), .TO (Toronto), .HK, .T (Tokyo), etc.
    if "." in symbol and not symbol.endswith(".U"):
        return False
    # Filter out symbols with digits at the start (ADR codes like 0A3P)
    if symbol and symbol[0].isdigit():
        return False
    return True


def _fetch_candidates_financedatabase(
    target_sector: str,
    target_ticker: str,
) -> list[dict[str, Any]]:
    """Fetch candidate peers from financedatabase.

    Returns list of candidate dicts with keys: symbol, name, sector, industry.
    """
    try:
        # Use cached equities data
        equities = _load_equities_data()
        if equities is None:
            logger.warning("financedatabase unavailable, falling back")
            return []

        # Translate yfinance sector name to financedatabase (GICS) name.
        gics_sector = _SECTOR_NAME_MAP.get(target_sector, target_sector)
        if gics_sector != target_sector:
            logger.info(
                "Mapped sector '%s' -> '%s' for financedatabase",
                target_sector,
                gics_sector,
            )

        results = equities.search(  # type: ignore[no-untyped-call]
            country="United States",
            sector=gics_sector,
        )

        df: Any = results
        if df is None or len(df) == 0:
            return []

        candidates: list[dict[str, Any]] = []
        raw_index: list[Any] = list(df.index)
        index_list: list[str] = [str(s) for s in raw_index]
        for sym_str in index_list:
            if sym_str == target_ticker:
                continue
            row: Any = df.loc[sym_str]
            candidates.append(
                {
                    "symbol": sym_str,
                    "name": str(row.get("name", "") if hasattr(row, "get") else ""),
                    "sector": str(row.get("sector", "") if hasattr(row, "get") else ""),
                    "industry": str(row.get("industry", "") if hasattr(row, "get") else ""),
                }
            )
            if len(candidates) >= MAX_CANDIDATES * 3:
                break

        return candidates

    except Exception:
        logger.warning("financedatabase unavailable, falling back")
        return []


def _enrich_candidate_yfinance(
    symbol: str,
) -> dict[str, Any] | None:
    """Get market data for a candidate via yfinance.

    ACCEPTED ARCH-02 EXCEPTION: This function makes live yfinance calls in
    EXTRACT, not ACQUIRE. This is intentional — peer candidates are identified
    during EXTRACT using the target company's financial profile (SIC, sector,
    market cap) which is only fully assembled after structured data acquisition.
    Pre-fetching at ACQUIRE time would require knowing which symbols to fetch
    before extraction, creating a two-pass dependency. Since this enriches
    discovered candidates (not fixed sources), moving it to ACQUIRE adds
    complexity without benefit. Logged in STATE.md as an accepted exception.
    """
    try:
        import yfinance as yf  # type: ignore[import-untyped]

        ticker = yf.Ticker(symbol)
        info = cast(dict[str, Any], ticker.info)  # type: ignore[union-attr]
        return {
            "market_cap": float(info.get("marketCap", 0) or 0),
            "revenue": float(info.get("totalRevenue", 0) or 0),
            "sic_code": str(info.get("sic", "") or ""),
            "industry": str(info.get("industry", "") or ""),
            "sector": str(info.get("sector", "") or ""),
            "description": str(info.get("longBusinessSummary", "") or ""),
            "name": str(info.get("shortName", symbol) or symbol),
        }
    except Exception:
        logger.debug("yfinance failed for %s", symbol)
        return None


def _score_candidate(
    yf_data: dict[str, Any],
    target_sic: str,
    target_sector: str,
    target_industry: str,
    target_mcap: float,
    target_revenue: float,
    target_desc: str,
) -> float:
    """Score a candidate peer using all 5 signals."""
    return compute_composite_score(
        score_sic_match(target_sic, str(yf_data.get("sic_code", ""))),
        score_industry_match(
            target_industry,
            target_sector,
            str(yf_data.get("industry", "")),
            str(yf_data.get("sector", "")),
        ),
        score_market_cap_proximity(
            target_mcap,
            float(yf_data.get("market_cap", 0)),
        ),
        score_revenue_similarity(
            target_revenue,
            float(yf_data.get("revenue", 0)),
        ),
        score_description_overlap(
            target_desc,
            str(yf_data.get("description", "")),
        ),
    )


def _make_peer(
    symbol: str,
    yf_data: dict[str, Any],
    score: float,
    tier: str = "",
) -> PeerCompany:
    """Build a PeerCompany from yfinance data."""
    cand_mcap = float(yf_data.get("market_cap", 0))
    return PeerCompany(
        ticker=symbol,
        name=str(yf_data.get("name", symbol)),
        sic_code=str(yf_data.get("sic_code", "")) or None,
        industry=str(yf_data.get("industry", "")) or None,
        market_cap=cand_mcap if cand_mcap > 0 else None,
        revenue=float(yf_data.get("revenue", 0)) or None,
        peer_score=score,
        peer_tier=tier,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def construct_peer_group(
    state: AnalysisState,
    override_peers: list[str] | None = None,
) -> tuple[PeerGroup, ExtractionReport]:
    """Construct multi-signal peer group for benchmarking.

    Five scoring signals: SIC match (25%), industry match (20%),
    market cap proximity (25%), revenue similarity (15%), and
    business description overlap (15%).

    Args:
        state: AnalysisState with company profile populated.
        override_peers: Optional list of ticker symbols to force-include.

    Returns:
        Tuple of (PeerGroup, ExtractionReport).

    Raises:
        ValueError: If state.company is None.
    """
    if state.company is None:
        msg = "CompanyProfile must be populated by RESOLVE stage first"
        raise ValueError(msg)

    target_ticker = state.company.identity.ticker
    info = get_info_dict(state)
    warnings: list[str] = []

    # Target company attributes.
    target_sic = ""
    if state.company.identity.sic_code is not None:
        target_sic = state.company.identity.sic_code.value
    target_sector = str(info.get("sector", ""))
    target_industry = str(info.get("industry", ""))
    target_mcap = float(info.get("marketCap", 0) or 0)
    target_revenue = float(info.get("totalRevenue", 0) or 0)
    target_desc = str(info.get("longBusinessSummary", "") or "")

    # Sector ETF.
    sector_code = ""
    if state.company.identity.sector is not None:
        sector_code = state.company.identity.sector.value
    sector_etf = _get_sector_etf(sector_code)

    # Build peer list.
    peers: list[PeerCompany] = []
    override_set = set(override_peers or [])

    # Process overrides first.
    for ticker in override_set:
        yf_data = _enrich_candidate_yfinance(ticker)
        if yf_data is not None:
            score = _score_candidate(
                yf_data,
                target_sic,
                target_sector,
                target_industry,
                target_mcap,
                target_revenue,
                target_desc,
            )
            peers.append(_make_peer(ticker, yf_data, score))

    # Fetch candidates from financedatabase.
    candidates = _fetch_candidates_financedatabase(
        target_sector,
        target_ticker,
    )
    if not candidates:
        warnings.append("financedatabase returned no candidates")
        # Fallback: hardcoded mega-cap peers by sector
        fallback = _get_sector_fallback_peers(target_sector, target_ticker)
        if fallback:
            candidates = fallback
            warnings.append(f"Using {len(fallback)} hardcoded sector peers as fallback")

    # Enrich and score candidates (limited to MAX_CANDIDATES).
    scored: list[PeerCompany] = []
    enriched_count = 0

    for candidate in candidates:
        if enriched_count >= MAX_CANDIDATES:
            break
        symbol = str(candidate.get("symbol", ""))
        if not symbol or symbol == target_ticker or symbol in override_set:
            continue
        if not _is_us_ticker(symbol):
            continue

        yf_data = _enrich_candidate_yfinance(symbol)
        if yf_data is None:
            continue
        enriched_count += 1

        cand_mcap = float(yf_data.get("market_cap", 0))
        if target_mcap > 0 and cand_mcap > 0:
            ratio = cand_mcap / target_mcap
            if ratio < MCAP_BAND_TIGHT[0] or ratio > MCAP_BAND_TIGHT[1]:
                continue

        score = _score_candidate(
            yf_data,
            target_sic,
            target_sector,
            target_industry,
            target_mcap,
            target_revenue,
            target_desc,
        )
        scored.append(_make_peer(symbol, yf_data, score))

    # Sort by score and take top.
    scored.sort(key=lambda p: p.peer_score, reverse=True)
    remaining = TARGET_PEER_COUNT - len(peers)
    if remaining > 0:
        peers.extend(scored[:remaining])

    # Expand band if below minimum.
    if len(peers) < MIN_PEER_COUNT:
        warnings.append(f"Only {len(peers)} peers in tight band; expanded to 0.3x-3.0x")
        _expand_peer_band(
            peers,
            candidates,
            target_ticker,
            target_mcap,
        )

    # Final fallback: if still no peers (all candidates were non-US),
    # use hardcoded sector peers
    if len(peers) < MIN_PEER_COUNT:
        fallback = _get_sector_fallback_peers(target_sector, target_ticker)
        for fb_candidate in fallback:
            if len(peers) >= TARGET_PEER_COUNT:
                break
            fb_symbol = str(fb_candidate.get("symbol", ""))
            if any(p.ticker == fb_symbol for p in peers):
                continue
            fb_data = _enrich_candidate_yfinance(fb_symbol)
            if fb_data is None:
                continue
            fb_score = _score_candidate(
                fb_data,
                target_sic,
                target_sector,
                target_industry,
                target_mcap,
                target_revenue,
                target_desc,
            )
            peers.append(_make_peer(fb_symbol, fb_data, fb_score))
        if peers:
            warnings.append(f"Used hardcoded sector fallback peers ({len(peers)} found)")

    # Assign tiers.
    for peer in peers:
        if peer.peer_tier == "":
            peer.peer_tier = _assign_tier(peer, target_sic)

    peer_group = PeerGroup(
        target_ticker=target_ticker,
        peers=peers,
        construction_method=(
            "Multi-signal composite: SIC 25%, industry 20%, "
            "market cap 25%, revenue 15%, description 15%"
        ),
        sector_etf=sector_etf,
    )

    expected_fields = [f"peer_{i + 1}" for i in range(MIN_PEER_COUNT)]
    found_fields = [f"peer_{i + 1}" for i in range(len(peers))]
    report = create_report(
        extractor_name="peer_group",
        expected=expected_fields,
        found=found_fields,
        source_filing="financedatabase + yfinance",
        warnings=warnings,
    )
    log_report(report)

    logger.info(
        "Peer group: %d peers for %s (sector ETF: %s)",
        len(peers),
        target_ticker,
        sector_etf or "N/A",
    )
    return peer_group, report


def _expand_peer_band(
    peers: list[PeerCompany],
    candidates: list[dict[str, Any]],
    target_ticker: str,
    target_mcap: float,
) -> None:
    """Expand market cap band to 0.3x-3.0x to reach minimum peer count."""
    for candidate in candidates:
        if len(peers) >= MIN_PEER_COUNT:
            break
        symbol = str(candidate.get("symbol", ""))
        if any(p.ticker == symbol for p in peers) or symbol == target_ticker:
            continue
        if not _is_us_ticker(symbol):
            continue

        yf_data = _enrich_candidate_yfinance(symbol)
        if yf_data is None:
            continue
        cand_mcap = float(yf_data.get("market_cap", 0))
        if target_mcap > 0 and cand_mcap > 0:
            ratio = cand_mcap / target_mcap
            if ratio < MCAP_BAND_WIDE[0] or ratio > MCAP_BAND_WIDE[1]:
                continue

        peers.append(_make_peer(symbol, yf_data, 0.0, "market_cap_cohort"))
