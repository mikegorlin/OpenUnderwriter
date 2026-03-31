"""Tests for governance intelligence context builders (Phase 135 Plan 02).

Tests cover:
- build_officer_backgrounds: officer card data with serial defendant detection
- build_shareholder_rights: 8-provision checklist with defense posture
- build_per_insider_activity: per-insider aggregation with 10b5-1 badges
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Fixtures: minimal state builders
# ---------------------------------------------------------------------------

def _make_state(
    *,
    executives: list[Any] | None = None,
    board: Any | None = None,
    insider_transactions: list[Any] | None = None,
    shares_outstanding: float | None = None,
) -> Any:
    """Build a minimal mock AnalysisState with governance + market data."""
    # Use spec (not spec_set) with an AnalysisState instance so Pydantic v2
    # model fields are visible to the mock. spec validates attribute access
    # while still allowing deep mock assignment.
    state = MagicMock(spec=AnalysisState(ticker="SPEC"))

    # Governance leadership
    if executives is not None:
        state.extracted.governance.leadership.executives = executives
    else:
        state.extracted.governance.leadership.executives = []

    # Board
    if board is not None:
        state.extracted.governance.board = board
    else:
        state.extracted.governance.board = _make_board()

    # Insider trading -- transactions live on insider_analysis, NOT insider_trading
    # (InsiderTradingProfile has no transactions field; InsiderTradingAnalysis does)
    if insider_transactions is not None:
        state.extracted.market.insider_analysis.transactions = insider_transactions
    else:
        state.extracted.market.insider_analysis.transactions = []

    # Shares outstanding
    state.company.shares_outstanding = shares_outstanding

    # Financials statements for shares_outstanding fallback
    state.extracted.financials.statements = {}

    return state


def _make_board(
    *,
    classified_board: bool | None = None,
    poison_pill: bool | None = None,
    supermajority_voting: bool | None = None,
    proxy_access_threshold: str | None = None,
    cumulative_voting: bool | None = None,
    written_consent_allowed: bool | None = None,
    special_meeting_threshold: str | None = None,
    forum_selection_clause: str | None = None,
) -> Any:
    """Build a mock BoardProfile with SourcedValue fields."""
    board = MagicMock()

    def _sv(val: Any) -> Any:
        if val is None:
            return None
        sv = MagicMock()
        sv.value = val
        return sv

    board.classified_board = _sv(classified_board)
    board.poison_pill = _sv(poison_pill)
    board.supermajority_voting = _sv(supermajority_voting)
    board.proxy_access_threshold = _sv(proxy_access_threshold)
    board.cumulative_voting = _sv(cumulative_voting)
    board.written_consent_allowed = _sv(written_consent_allowed)
    board.special_meeting_threshold = _sv(special_meeting_threshold)
    board.forum_selection_clause = _sv(forum_selection_clause)

    return board


def _make_executive(name: str, title: str, bio: str = "", prior_lit: list[str] | None = None) -> Any:
    """Build a mock LeadershipForensicProfile."""
    exec_mock = MagicMock()
    exec_mock.name.value = name
    exec_mock.title.value = title
    exec_mock.bio_summary.value = bio if bio else ""
    exec_mock.bio_summary = MagicMock(value=bio if bio else "")
    exec_mock.prior_litigation = prior_lit or []
    return exec_mock


def _make_insider_tx(
    name: str, title: str, tx_type: str = "SELL",
    total_value: float = 0.0, shares: float = 0.0,
    is_10b5_1: bool = False, tx_code: str = "S",
    tx_date: str = "2024-01-15",
) -> Any:
    """Build a mock InsiderTransaction."""
    tx = MagicMock()
    tx.insider_name.value = name
    tx.title.value = title
    tx.transaction_type = tx_type
    tx.transaction_code = tx_code
    tx.total_value.value = total_value
    tx.shares.value = shares
    tx.is_10b5_1.value = is_10b5_1
    tx.transaction_date.value = tx_date
    return tx


# ===========================================================================
# Tests: build_officer_backgrounds
# ===========================================================================

class TestBuildOfficerBackgrounds:
    """Tests for officer background investigation context builder."""

    def test_empty_executives_returns_no_data(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_officer_backgrounds,
        )
        state = _make_state(executives=[])
        result = build_officer_backgrounds(state)
        assert result["has_officer_backgrounds"] is False
        assert result["officer_backgrounds"] == []
        assert result["serial_defendant_count"] == 0

    def test_officers_returned_with_name_and_title(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_officer_backgrounds,
        )
        execs = [
            _make_executive("John Smith", "CEO", bio="served as CFO of Acme Corp from 2010 to 2015"),
            _make_executive("Jane Doe", "CFO"),
        ]
        state = _make_state(executives=execs)
        result = build_officer_backgrounds(state)
        assert result["has_officer_backgrounds"] is True
        assert len(result["officer_backgrounds"]) == 2
        assert result["officer_backgrounds"][0]["name"] == "John Smith"
        assert result["officer_backgrounds"][0]["title"] == "CEO"

    def test_serial_defendant_count(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_officer_backgrounds,
        )
        execs = [_make_executive("John Smith", "CEO")]
        state = _make_state(executives=execs)
        # No SCA matches expected with empty Supabase
        result = build_officer_backgrounds(state)
        assert result["serial_defendant_count"] == 0

    def test_suitability_field_present(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_officer_backgrounds,
        )
        execs = [_make_executive("John Smith", "CEO", bio="served as CFO of Acme Corp from 2010 to 2015")]
        state = _make_state(executives=execs)
        result = build_officer_backgrounds(state)
        officer = result["officer_backgrounds"][0]
        assert "suitability" in officer
        assert officer["suitability"] in ("HIGH", "MEDIUM", "LOW")
        assert "suitability_reason" in officer


# ===========================================================================
# Tests: build_shareholder_rights
# ===========================================================================

class TestBuildShareholderRights:
    """Tests for shareholder rights inventory context builder."""

    def test_shareholder_rights_returns_8_provisions(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        board = _make_board(
            classified_board=True, poison_pill=False,
            supermajority_voting=True, proxy_access_threshold="3%",
            cumulative_voting=False, written_consent_allowed=True,
            special_meeting_threshold="25%", forum_selection_clause="Delaware",
        )
        state = _make_state(board=board)
        result = build_shareholder_rights(state)
        assert result["has_shareholder_rights"] is True
        rights = result["shareholder_rights"]
        assert len(rights["provisions"]) == 8

    def test_defense_strength_strong(self) -> None:
        """5+ protective provisions -> Strong defense posture."""
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        # All protective: classified_board=Yes, poison_pill=Yes, supermajority=Yes,
        # forum_selection=Yes, + special_meeting with high threshold (Protective)
        board = _make_board(
            classified_board=True, poison_pill=True,
            supermajority_voting=True, proxy_access_threshold=None,
            cumulative_voting=False, written_consent_allowed=False,
            special_meeting_threshold=None, forum_selection_clause="Delaware",
        )
        state = _make_state(board=board)
        result = build_shareholder_rights(state)
        rights = result["shareholder_rights"]
        assert rights["overall_defense_posture"] == "Strong"
        assert rights["protective_count"] >= 5

    def test_defense_strength_moderate(self) -> None:
        """3-4 protective provisions -> Moderate defense posture."""
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        board = _make_board(
            classified_board=True, poison_pill=False,
            supermajority_voting=True, proxy_access_threshold="3%",
            cumulative_voting=False, written_consent_allowed=True,
            special_meeting_threshold="25%", forum_selection_clause="Delaware",
        )
        state = _make_state(board=board)
        result = build_shareholder_rights(state)
        rights = result["shareholder_rights"]
        assert rights["overall_defense_posture"] == "Moderate"
        assert 3 <= rights["protective_count"] <= 4

    def test_defense_strength_weak(self) -> None:
        """0-2 protective provisions -> Weak defense posture."""
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        board = _make_board(
            classified_board=False, poison_pill=False,
            supermajority_voting=False, proxy_access_threshold="3%",
            cumulative_voting=True, written_consent_allowed=True,
            special_meeting_threshold="10%", forum_selection_clause=None,
        )
        state = _make_state(board=board)
        result = build_shareholder_rights(state)
        rights = result["shareholder_rights"]
        assert rights["overall_defense_posture"] == "Weak"
        assert rights["protective_count"] <= 2

    def test_provision_has_do_implication(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        board = _make_board(classified_board=True)
        state = _make_state(board=board)
        result = build_shareholder_rights(state)
        provision = result["shareholder_rights"]["provisions"][0]
        assert provision["do_implication"]  # non-empty
        assert provision["defense_strength"] in ("Protective", "Shareholder-Friendly", "Neutral")

    def test_no_board_returns_no_data(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_shareholder_rights,
        )
        state = _make_state()
        state.extracted.governance.board = None
        result = build_shareholder_rights(state)
        assert result["has_shareholder_rights"] is False


# ===========================================================================
# Tests: build_per_insider_activity
# ===========================================================================

class TestBuildPerInsiderActivity:
    """Tests for per-insider activity context builder."""

    def test_per_insider_sorted_by_sales(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        txs = [
            _make_insider_tx("Alice", "CEO", total_value=500000, shares=1000, tx_date="2024-01-10"),
            _make_insider_tx("Bob", "CFO", total_value=1000000, shares=2000, tx_date="2024-02-15"),
        ]
        state = _make_state(insider_transactions=txs)
        result = build_per_insider_activity(state)
        assert result["has_per_insider_activity"] is True
        assert len(result["per_insider_activity"]) == 2
        # Bob has more sales, should be first
        assert result["per_insider_activity"][0]["name"] == "Bob"
        assert result["per_insider_activity"][1]["name"] == "Alice"

    def test_10b5_1_badge(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        txs = [
            _make_insider_tx("Alice", "CEO", total_value=500000, is_10b5_1=True),
            _make_insider_tx("Bob", "CFO", total_value=300000, is_10b5_1=False),
        ]
        state = _make_state(insider_transactions=txs)
        result = build_per_insider_activity(state)
        insiders = result["per_insider_activity"]
        alice = next(i for i in insiders if i["name"] == "Alice")
        bob = next(i for i in insiders if i["name"] == "Bob")
        assert alice["ten_b5_1_badge"] == "10b5-1"
        assert bob["ten_b5_1_badge"] == "Discretionary"

    def test_empty_transactions_returns_no_data(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        state = _make_state(insider_transactions=[])
        result = build_per_insider_activity(state)
        assert result["has_per_insider_activity"] is False
        assert result["per_insider_activity"] == []

    def test_formatted_currency_values(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        txs = [_make_insider_tx("Alice", "CEO", total_value=1234567.89, shares=5000)]
        state = _make_state(insider_transactions=txs, shares_outstanding=1000000)
        result = build_per_insider_activity(state)
        insider = result["per_insider_activity"][0]
        # Should have formatted currency string
        assert "$" in insider["total_sold_fmt"]
        assert result["insider_count"] == 1

    def test_pct_os_calculated_when_shares_available(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        txs = [_make_insider_tx("Alice", "CEO", total_value=500000, shares=10000)]
        state = _make_state(insider_transactions=txs, shares_outstanding=1000000)
        result = build_per_insider_activity(state)
        insider = result["per_insider_activity"][0]
        # 10000 / 1000000 = 1.0%
        assert insider["pct_os"] != "N/A"

    def test_pct_os_na_when_no_shares(self) -> None:
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )
        txs = [_make_insider_tx("Alice", "CEO", total_value=500000, shares=10000)]
        state = _make_state(insider_transactions=txs, shares_outstanding=None)
        result = build_per_insider_activity(state)
        insider = result["per_insider_activity"][0]
        assert insider["pct_os"] == "N/A"
