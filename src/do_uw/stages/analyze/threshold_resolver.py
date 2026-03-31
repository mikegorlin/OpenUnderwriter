"""Sector-aware threshold resolver for signal evaluation.

Resolves signal thresholds against company context (sector, market cap).
Two resolution strategies:

1. **Sector baselines** — signals with field_keys mapped to sectors.json
   metrics get sector-specific thresholds (e.g., tech current ratio).

2. **Signal-level overrides** — signals matched by ID get context-aware
   threshold adjustments based on sector + market cap tier. These handle
   signals where the MEANING of the metric changes by company type (e.g.,
   negative working capital is normal for mega-cap tech, channel stuffing
   indicators are false positives for distributor-model companies).

This prevents false positives like Apple's current ratio < 1.0 triggering
a liquidity warning, or high OCF/NI being flagged as cash flow manipulation
when it's actually a sign of business quality.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile

logger = logging.getLogger(__name__)

# Lazily-loaded sector baselines
_sector_baselines: dict[str, Any] | None = None


def _load_sector_baselines() -> dict[str, Any]:
    """Load sectors.json from brain/config/."""
    global _sector_baselines
    if _sector_baselines is None:
        path = (
            Path(__file__).resolve().parent.parent.parent
            / "brain" / "config" / "sectors.json"
        )
        if path.exists():
            _sector_baselines = json.loads(path.read_text())
        else:
            logger.warning("sectors.json not found at %s", path)
            _sector_baselines = {}
    return _sector_baselines


def _get_company_sector(company: CompanyProfile | None) -> str | None:
    """Extract sector code from CompanyProfile."""
    if company is None:
        return None
    identity = company.identity
    sector_sv = identity.sector
    if sector_sv is not None:
        val = sector_sv.value if hasattr(sector_sv, "value") else sector_sv
        if val:
            return str(val)
    return None


def _get_market_cap(company: CompanyProfile | None) -> float | None:
    """Extract market cap from CompanyProfile."""
    if company is None:
        return None
    mcap_sv = company.market_cap
    if mcap_sv is None:
        return None
    mcap = mcap_sv.value if hasattr(mcap_sv, "value") else mcap_sv
    if mcap is None:
        return None
    try:
        return float(mcap)
    except (ValueError, TypeError):
        return None


def _get_market_cap_tier(company: CompanyProfile | None) -> str:
    """Classify company by market cap tier."""
    mcap = _get_market_cap(company)
    if mcap is None:
        return "unknown"
    if mcap >= 200e9:
        return "mega"
    if mcap >= 10e9:
        return "large"
    if mcap >= 2e9:
        return "mid"
    if mcap >= 300e6:
        return "small"
    return "micro"


# ---------------------------------------------------------------------------
# Strategy 1: Sector baselines from sectors.json
# ---------------------------------------------------------------------------

# Map signal field_key -> (sectors_json_key, red_level, yellow_level)
_FIELD_TO_SECTOR_METRIC: dict[str, tuple[str, str, str]] = {
    "xbrl_current_ratio": ("current_ratio", "critical", "elevated"),
    "short_percent_float": ("short_interest", "high", "elevated"),
    "volatility_90d": ("volatility_90d", "high", "elevated"),
    "debt_to_ebitda": ("leverage_debt_ebitda", "critical", "elevated"),
}


def _resolve_via_sector_baselines(
    signal: dict[str, Any],
    company: CompanyProfile,
    sector: str,
) -> dict[str, Any] | None:
    """Check sectors.json for sector-specific metric thresholds."""
    ds = signal.get("data_strategy")
    if not isinstance(ds, dict):
        return None
    field_key = ds.get("field_key", "")

    mapping = _FIELD_TO_SECTOR_METRIC.get(field_key)
    if mapping is None:
        return None

    metric_key, red_level, yellow_level = mapping
    baselines = _load_sector_baselines()
    metric_data = baselines.get(metric_key)
    if not metric_data:
        return None

    sector_thresholds = metric_data.get(sector) or metric_data.get("DEFAULT")
    if not sector_thresholds:
        return None

    red_val = sector_thresholds.get(red_level)
    yellow_val = sector_thresholds.get(yellow_level)
    if red_val is None and yellow_val is None:
        return None

    return _build_adjusted_threshold(signal, sector, red_val, yellow_val)


# ---------------------------------------------------------------------------
# Strategy 2: Signal-level context overrides
# ---------------------------------------------------------------------------

# Per-signal threshold overrides keyed by signal ID.
# Each entry: signal_id -> function(sector, mcap_tier) -> (red, yellow) or None
# These encode domain knowledge about WHEN a signal is a false positive.

def _override_working_capital(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Negative working capital is normal for asset-light mega/large caps."""
    # Tech, retail, consumer — high inventory turnover / deferred revenue
    if sector in ("TECH", "CONS", "STPL", "COMM") and mcap_tier in ("mega", "large"):
        # For mega-cap tech, only flag MASSIVE negative WC relative to assets
        # Effectively suppress this signal — the current ratio signal handles it
        return (-1e15, -1e14)  # Unreachable thresholds
    return None


def _override_channel_stuffing(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Distributor-model companies naturally have high receivables/revenue ratios.

    Channel stuffing indicator (AR growth vs revenue growth) produces false
    positives for companies with distributor/reseller models where large
    receivable balances are structural.
    """
    if sector in ("TECH", "CONS", "COMM") and mcap_tier in ("mega", "large"):
        return (0.50, 0.30)  # Much higher threshold for large tech
    if sector == "HLTH":
        return (0.40, 0.25)  # Healthcare has insurance receivables
    return None


def _override_cash_flow_manipulation(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """High OCF/NI ratio is a sign of business quality, not manipulation.

    Asset-light tech companies with high depreciation, stock comp, and
    deferred revenue naturally have OCF >> NI. A ratio of 1.0+ is GOOD.
    """
    if sector in ("TECH", "COMM"):
        return (3.0, 2.0)  # Only flag extreme outliers
    if sector in ("CONS", "STPL"):
        return (2.0, 1.5)
    return None


def _override_margin_compression(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Business model transitions (hardware→services) cause margin shifts.

    This is strategic, not distressed. Only flag large sudden drops.
    """
    if sector in ("TECH", "COMM") and mcap_tier in ("mega", "large"):
        return (0.20, 0.10)  # Wider tolerance for mix-shift
    return None


def _override_dividend_sustainability(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Tech companies return capital via buybacks, not dividends.

    Low dividend payout ratio is INTENTIONAL — not a sustainability concern.
    """
    if sector in ("TECH", "COMM", "BIOT"):
        # Suppress: tech companies often have <20% payout ratios by design
        return (0.02, 0.05)  # Only flag near-zero for established payers
    return None


def _override_etr_anomaly(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Multinational tech companies have structurally low ETR.

    Ireland/Singapore structures give 12-16% ETR consistently.
    Not anomalous — it's been the same for 10+ years.
    """
    if sector in ("TECH", "COMM") and mcap_tier in ("mega", "large"):
        return (0.30, 0.20)  # Only flag >30% change, not low absolute ETR
    return None


def _override_pe_ratio(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Tech mega-caps routinely trade 30-50x earnings. Growth premium."""
    if sector == "TECH":
        return (60.0, 45.0)
    if sector == "COMM":
        return (50.0, 35.0)
    if sector in ("BIOT", "HLTH"):
        return (80.0, 50.0)  # Biotech/pharma can have very high PEs
    return None


def _override_ev_ebitda(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Tech companies trade at higher EV/EBITDA multiples."""
    if sector == "TECH":
        return (40.0, 30.0)
    if sector == "COMM":
        return (35.0, 25.0)
    if sector in ("BIOT", "HLTH"):
        return (50.0, 35.0)
    return None


def _override_ceo_pay_ratio(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Mega-cap CEO pay ratios of 300-600x are standard.

    S&P 500 median CEO pay ratio is ~250x (2024). Mega-cap tech is higher
    due to stock-heavy comp and high employee counts.
    """
    if mcap_tier == "mega":
        return (800.0, 600.0)
    if mcap_tier == "large":
        return (600.0, 400.0)
    return None


def _override_peg_ratio(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """High-quality tech companies with moderate growth trade at PEG 2-3x."""
    if sector in ("TECH", "COMM"):
        return (4.0, 3.0)
    return None


# ---------------------------------------------------------------------------
# FALSE NEGATIVE prevention: TIGHTER thresholds for high-risk profiles
# ---------------------------------------------------------------------------

def _override_working_capital_tight(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Micro/small caps with negative WC are genuinely distressed.

    Unlike mega-caps, small companies can't access capital markets on demand.
    Negative WC for a $200M company is a going-concern indicator.
    """
    if mcap_tier in ("micro", "small"):
        # Tighter: flag any negative WC for small companies
        return (0, -1e6)  # red at 0 (any negative), yellow at slight negative
    return None


def _override_leverage_tight(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Small companies with moderate leverage are higher risk.

    3x debt/EBITDA is "normal" generically but dangerous for a $200M
    company with no investment-grade rating and limited refinancing options.
    """
    if mcap_tier in ("micro", "small"):
        if sector not in ("UTIL", "REIT", "FINS"):  # These are inherently leveraged
            return (3.0, 2.0)  # Tighter than generic 5.5/4.0
    return None


def _override_insider_selling_tight(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Insider selling in small/micro caps is more significant.

    In mega-caps, diversification selling is routine. In small caps,
    executives selling is a stronger signal because they have fewer
    reasons to sell and their ownership is more concentrated.
    """
    if mcap_tier in ("micro", "small"):
        return (50.0, 15.0)  # Much tighter than generic 100/25
    return None


def _override_ceo_pay_ratio_tight(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Small company CEO pay ratios above 200x are concerning.

    Small companies with fewer employees and lower revenue should not
    have mega-cap-level pay ratios. High ratio signals entrenchment.
    """
    if mcap_tier == "mega":
        return (800.0, 600.0)
    if mcap_tier == "large":
        return (600.0, 400.0)
    if mcap_tier in ("micro", "small"):
        return (200.0, 100.0)  # Tighter for small companies
    return None


def _override_board_tenure_tight(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Long board tenure in small caps signals entrenchment.

    Mega-cap boards have institutional oversight and proxy advisors.
    Small-cap boards with long tenure lack external accountability.
    """
    if mcap_tier in ("micro", "small"):
        return (8.0, 6.0)  # Tighter than generic 15/10
    return None


def _override_liquidity_biotech(
    sector: str, mcap_tier: str,
) -> tuple[float | None, float | None] | None:
    """Pre-revenue biotech needs high current ratio for cash runway.

    Generic threshold of <1.0 red is too loose — biotechs burning cash
    need 3x+ current ratio to survive to next catalyst.
    """
    if sector == "BIOT":
        return (1.5, 3.0)  # RED below 1.5, YELLOW below 3.0
    return None


# Registry mapping signal IDs to override functions.
# Each function returns (red_threshold, yellow_threshold) or None.
# Functions handle BOTH loosening (false positive prevention) AND
# tightening (false negative prevention) based on company context.
_SIGNAL_OVERRIDES: dict[str, Any] = {
    # --- False positive prevention (loosening) ---
    "FIN.LIQ.working_capital": _override_working_capital,
    "FIN.FORENSIC.channel_stuffing": _override_channel_stuffing,
    "FIN.FORENSIC.cash_flow_manipulation": _override_cash_flow_manipulation,
    "FIN.FORENSIC.margin_compression": _override_margin_compression,
    "FIN.FORENSIC.dividend_sustainability": _override_dividend_sustainability,
    "FIN.FORENSIC.etr_anomaly": _override_etr_anomaly,
    "STOCK.VALUATION.pe_ratio": _override_pe_ratio,
    "STOCK.VALUATION.ev_ebitda": _override_ev_ebitda,
    "STOCK.VALUATION.peg_ratio": _override_peg_ratio,
    # --- Bidirectional (loosen for mega, tighten for micro) ---
    "GOV.PAY.ceo_total": _override_ceo_pay_ratio_tight,
    # --- False negative prevention (tightening) ---
    "FIN.LEV.debt_ebitda": _override_leverage_tight,
    "STOCK.INSIDER.notable_activity": _override_insider_selling_tight,
    "GOV.BOARD.tenure": _override_board_tenure_tight,
}


def _resolve_via_signal_overrides(
    signal: dict[str, Any],
    company: CompanyProfile,
    sector: str,
) -> dict[str, Any] | None:
    """Check for per-signal context-aware threshold overrides."""
    signal_id = signal.get("id", "")
    override_fn = _SIGNAL_OVERRIDES.get(signal_id)
    if override_fn is None:
        return None

    mcap_tier = _get_market_cap_tier(company)
    result = override_fn(sector, mcap_tier)
    if result is None:
        return None

    red_val, yellow_val = result
    return _build_adjusted_threshold(signal, sector, red_val, yellow_val)


# ---------------------------------------------------------------------------
# Shared threshold builder
# ---------------------------------------------------------------------------

def _build_adjusted_threshold(
    signal: dict[str, Any],
    sector: str,
    red_val: float | None,
    yellow_val: float | None,
) -> dict[str, Any] | None:
    """Build an adjusted threshold dict from sector-specific values."""
    if red_val is None and yellow_val is None:
        return None

    orig = signal.get("threshold", {})
    if not isinstance(orig, dict):
        return None

    adjusted = dict(orig)
    orig_red = str(orig.get("red", ""))
    is_less_than = "<" in orig_red

    if is_less_than:
        if red_val is not None:
            adjusted["red"] = f"<{red_val} (sector-adjusted for {sector})"
        if yellow_val is not None:
            adjusted["yellow"] = f"<{yellow_val} (sector-adjusted for {sector})"
    else:
        if red_val is not None:
            adjusted["red"] = f">{red_val} (sector-adjusted for {sector})"
        if yellow_val is not None:
            adjusted["yellow"] = f">{yellow_val} (sector-adjusted for {sector})"

    return adjusted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_sector_threshold(
    signal: dict[str, Any],
    company: CompanyProfile | None,
) -> dict[str, Any] | None:
    """Resolve sector-specific threshold overrides for a signal.

    Tries two strategies in order:
    1. Signal-level overrides (by signal ID) — handles domain-specific
       false positives where the metric meaning changes by company type
    2. Sector baselines (by field_key) — uses sectors.json metric data

    Args:
        signal: Signal config dict from brain YAML.
        company: CompanyProfile for sector/size lookup.

    Returns:
        Adjusted threshold dict, or None if no override applies.
    """
    if company is None:
        return None

    sector = _get_company_sector(company)
    if not sector:
        return None

    # Strategy 1: Signal-level overrides (most specific)
    result = _resolve_via_signal_overrides(signal, company, sector)
    if result is not None:
        logger.debug(
            "Signal override for %s: sector=%s mcap=%s",
            signal.get("id", "?"), sector, _get_market_cap_tier(company),
        )
        return result

    # Strategy 2: Sector baselines from sectors.json
    result = _resolve_via_sector_baselines(signal, company, sector)
    if result is not None:
        logger.debug(
            "Sector baseline for %s: sector=%s",
            signal.get("id", "?"), sector,
        )
        return result

    return None


__all__ = ["resolve_sector_threshold"]
