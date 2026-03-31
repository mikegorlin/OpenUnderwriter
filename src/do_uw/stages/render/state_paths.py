"""Typed state accessor registry for context builders.

Every context builder reads state through these functions instead of
navigating state paths directly. Each function:
- Uses direct attribute access (not getattr) so Pyright catches mismatches
- Documents which extractor populates the data and which builder consumes it
- Returns a typed value or a sensible empty default

This eliminates the class of bug where context builders navigate to
paths that don't exist on the real model but pass in MagicMock tests.

Usage:
    from do_uw.stages.render.state_paths import get_insider_transactions
    txs = get_insider_transactions(state)
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Market / Stock
# ---------------------------------------------------------------------------


def get_insider_transactions(state: AnalysisState) -> list[Any]:
    """Insider transactions from extracted market data.

    Populated by: stages/extract/insider_trading.py -> market.insider_analysis.transactions
    Consumed by: _governance_intelligence.build_per_insider_activity

    NOTE: InsiderTradingProfile (at market.insider_trading) has NO transactions
    field — only aggregate scalars. The actual transaction list lives on
    InsiderTradingAnalysis (at market.insider_analysis).
    """
    try:
        if state.extracted and state.extracted.market:
            analysis = state.extracted.market.insider_analysis
            if analysis and hasattr(analysis, "transactions"):
                txs = analysis.transactions
                if txs:
                    return txs
    except AttributeError:
        logger.debug("get_insider_transactions: path not found on model")
    return []


def get_insider_transactions_yfinance(state: AnalysisState) -> dict[str, Any]:
    """Raw yfinance insider_transactions dict from acquired data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.market_data["insider_transactions"]
    Consumed by: _governance_intelligence._aggregate_from_yfinance (fallback)

    Format: {"Insider": [...], "Position": [...], "Shares": [...], "Start Date": [...]}
    """
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            if isinstance(md, dict):
                return md.get("insider_transactions", {})
    except AttributeError:
        logger.debug("get_insider_transactions_yfinance: path not found")
    return {}


def get_market_history(state: AnalysisState, window: str = "5y") -> dict[str, Any]:
    """Price history from acquired market data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.market_data["history_Xy"]
    Consumed by: _market_acquired_data.build_earnings_trust, _market_correlation

    Args:
        window: "5y", "3y", "2y", or "1y" — tries longest first, falls back.
    """
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            if isinstance(md, dict):
                for key in [f"history_{window}", "history_5y", "history_3y", "history_2y", "history_1y"]:
                    h = md.get(key)
                    if h and isinstance(h, dict) and h.get("Date"):
                        return h
    except AttributeError:
        logger.debug("get_market_history: path not found")
    return {}


def get_earnings_dates(state: AnalysisState) -> dict[str, Any]:
    """Earnings dates from acquired market data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.market_data["earnings_dates"]
    Consumed by: _market_acquired_data.build_earnings_trust

    Format: {"Earnings Date": [...], "EPS Estimate": [...], "Reported EPS": [...]}
    """
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            if isinstance(md, dict):
                return md.get("earnings_dates", {})
    except AttributeError:
        pass
    return {}


def get_eps_revisions(state: AnalysisState) -> dict[str, Any]:
    """EPS revision data from acquired market data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.market_data["eps_revisions"]
    Consumed by: _market_acquired_data.build_eps_revision_trends

    NOTE: Key casing varies — downLast7Days vs downLast7days. Callers must handle both.
    """
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            if isinstance(md, dict):
                return md.get("eps_revisions", {})
    except AttributeError:
        pass
    return {}


def get_analyst_price_targets(state: AnalysisState) -> dict[str, Any]:
    """Analyst price targets from acquired market data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.market_data["analyst_price_targets"]
    Consumed by: _market_acquired_data.build_analyst_targets

    NOTE: Keys are yfinance-style (targetMeanPrice, targetLowPrice, etc.),
    NOT simplified (low, mean, high). Callers must handle both.
    """
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            if isinstance(md, dict):
                return md.get("analyst_price_targets", {})
    except AttributeError:
        pass
    return {}


# ---------------------------------------------------------------------------
# Filings
# ---------------------------------------------------------------------------


def get_filing_documents(state: AnalysisState) -> dict[str, list[dict[str, Any]]]:
    """Filing documents from acquired data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.filing_documents
    Consumed by: ten_k_yoy, supply_chain_extract

    NOTE: The field is `filings` (not `sec_filings`).
    """
    try:
        if state.acquired_data:
            fd = state.acquired_data.filing_documents
            if fd and isinstance(fd, dict):
                return fd
    except AttributeError:
        logger.debug("get_filing_documents: field not found")
    return {}


def get_filings(state: AnalysisState) -> Any:
    """Filing metadata from acquired data.

    Populated by: stages/acquire/orchestrator.py -> acquired_data.filings
    Consumed by: _company_intelligence.build_supply_chain_context

    NOTE: The field is `filings` (NOT `sec_filings` — that doesn't exist).
    """
    try:
        if state.acquired_data:
            return getattr(state.acquired_data, "filings", None)
    except AttributeError:
        pass
    return None


# ---------------------------------------------------------------------------
# Risk Factors
# ---------------------------------------------------------------------------


def get_risk_factors(state: AnalysisState) -> list[Any]:
    """Risk factor profiles from extracted data.

    Populated by: stages/extract/risk_factor_extract.py -> extracted.risk_factors
    Consumed by: _company_intelligence.build_risk_factor_review

    Returns a list of RiskFactorProfile objects (not a model with .profiles).
    """
    try:
        if state.extracted:
            rf = state.extracted.risk_factors
            if rf and isinstance(rf, list):
                return rf
    except AttributeError:
        pass
    return []


def get_ten_k_yoy(state: AnalysisState) -> Any:
    """10-K year-over-year comparison from extracted data.

    Populated by: stages/extract/ten_k_yoy.py -> extracted.ten_k_yoy
    Consumed by: _company_intelligence.build_risk_factor_review

    Returns TenKYoYComparison or None.
    """
    try:
        if state.extracted:
            return state.extracted.ten_k_yoy
    except AttributeError:
        pass
    return None


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------


def get_board_profile(state: AnalysisState) -> Any:
    """Board profile from extracted governance data.

    Populated by: stages/extract/board_governance.py -> extracted.governance.board
    Consumed by: _governance_intelligence.build_shareholder_rights_inventory
    """
    try:
        if state.extracted and state.extracted.governance:
            return state.extracted.governance.board
    except AttributeError:
        pass
    return None


def get_governance_forensics(state: AnalysisState) -> Any:
    """Governance forensic profiles from extracted data.

    Populated by: stages/extract/llm_governance.py -> extracted.governance.board_forensics
    Consumed by: _governance_intelligence.build_officer_backgrounds
    """
    try:
        if state.extracted and state.extracted.governance:
            return state.extracted.governance.board_forensics
    except AttributeError:
        pass
    return None


# ---------------------------------------------------------------------------
# Litigation
# ---------------------------------------------------------------------------


def get_securities_class_actions(state: AnalysisState) -> list[Any]:
    """SCA cases from extracted litigation data.

    Populated by: stages/extract/sca_extractor.py -> extracted.litigation.securities_class_actions
    Consumed by: litigation context builders

    Returns list of CaseDetail objects.
    """
    try:
        if state.extracted and state.extracted.litigation:
            sca = state.extracted.litigation.securities_class_actions
            if sca and isinstance(sca, list):
                return sca
    except AttributeError:
        pass
    return []


def get_regulatory_proceedings(state: AnalysisState) -> list[Any]:
    """Regulatory proceedings from extracted litigation data.

    Populated by: stages/extract/regulatory_extract.py -> extracted.litigation.regulatory_proceedings
    Consumed by: _company_intelligence.build_regulatory_map
    """
    try:
        if state.extracted and state.extracted.litigation:
            rp = state.extracted.litigation.regulatory_proceedings
            if rp and isinstance(rp, list):
                return rp
    except AttributeError:
        pass
    return []


# ---------------------------------------------------------------------------
# Forward-Looking
# ---------------------------------------------------------------------------


def get_forward_looking(state: AnalysisState) -> Any:
    """Forward-looking data from state.

    Populated by: stages/analyze -> state.forward_looking
    Consumed by: _forward_credibility, _forward_scenarios
    """
    try:
        return state.forward_looking
    except AttributeError:
        pass
    return None


def get_scoring(state: AnalysisState) -> Any:
    """Scoring data from state.

    Populated by: stages/score -> state.scoring
    Consumed by: scenario_generator, scorecard_context
    """
    try:
        return state.scoring
    except AttributeError:
        pass
    return None


__all__ = [
    "get_analyst_price_targets",
    "get_board_profile",
    "get_earnings_dates",
    "get_eps_revisions",
    "get_filing_documents",
    "get_filings",
    "get_forward_looking",
    "get_governance_forensics",
    "get_insider_transactions",
    "get_insider_transactions_yfinance",
    "get_market_history",
    "get_regulatory_proceedings",
    "get_risk_factors",
    "get_scoring",
    "get_securities_class_actions",
    "get_ten_k_yoy",
]
