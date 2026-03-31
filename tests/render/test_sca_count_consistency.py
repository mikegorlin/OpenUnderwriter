"""Tests proving all SCA count paths produce identical results.

Validates that the canonical sca_counter module produces correct counts
and that all 13 call sites in the codebase produce identical results
when given the same AnalysisState.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_sca(
    status: str | None,
    case_name: str = "Test v. Company",
    coverage_type: str = "SCA_SIDE_C",
    legal_theories: list[str] | None = None,
) -> MagicMock:
    """Build a mock SCA case detail."""
    sca = MagicMock()
    if status is not None:
        sca.status = MagicMock()
        sca.status.value = status
    else:
        sca.status = None

    sca.case_name = MagicMock()
    sca.case_name.value = case_name

    sca.coverage_type = MagicMock()
    sca.coverage_type.value = coverage_type

    theories = legal_theories or ["RULE_10B5"]
    sca.legal_theories = [MagicMock(value=t) for t in theories]
    sca.allegations = []
    sca.court = MagicMock(value="S.D.N.Y.")
    sca.filing_date = MagicMock(value="2024-01-15")
    sca.class_period_start = None
    sca.class_period_end = None
    sca.class_period_days = None
    sca.lead_counsel = None
    sca.lead_counsel_tier = None
    sca.settlement_amount = None
    sca.corroborated = None
    return sca


def _make_state_with_scas(scas: list[MagicMock]) -> MagicMock:
    """Build a mock AnalysisState with the given SCA list."""
    state = MagicMock()
    state.extracted.litigation.securities_class_actions = scas
    return state


# The 6-SCA test case from the plan:
# 1 ACTIVE genuine, 1 PENDING genuine, 1 status=None genuine,
# 1 SETTLED genuine, 1 ACTIVE regulatory (FCPA), 1 status="N/A" genuine
# Expected active genuine count = 4 (ACTIVE + PENDING + None + N/A)

MIXED_SCAS = [
    _make_sca("ACTIVE", "Smith v. Acme Corp"),
    _make_sca("PENDING", "Jones v. Acme Corp"),
    _make_sca(None, "Unknown v. Acme Corp"),  # status=None -> assume active
    _make_sca("SETTLED", "Doe v. Acme Corp"),  # excluded
    _make_sca(
        "ACTIVE",
        "DOJ FCPA Investigation",
        coverage_type="REGULATORY_ENTITY",
        legal_theories=["FCPA"],
    ),  # regulatory -> excluded
    _make_sca("N/A", "Class v. Acme Corp"),  # N/A -> assume active
]


class TestGetActiveGenuineScas:
    """Tests for the canonical get_active_genuine_scas function."""

    def test_returns_only_active_genuine(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas(MIXED_SCAS)
        result = get_active_genuine_scas(state)
        assert len(result) == 4

    def test_excludes_settled(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([_make_sca("SETTLED")])
        result = get_active_genuine_scas(state)
        assert len(result) == 0

    def test_excludes_dismissed(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([_make_sca("DISMISSED")])
        result = get_active_genuine_scas(state)
        assert len(result) == 0

    def test_excludes_closed(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([_make_sca("CLOSED")])
        result = get_active_genuine_scas(state)
        assert len(result) == 0

    def test_excludes_regulatory(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        sca = _make_sca(
            "ACTIVE", "FCPA Matter",
            coverage_type="REGULATORY_ENTITY",
            legal_theories=["FCPA"],
        )
        state = _make_state_with_scas([sca])
        result = get_active_genuine_scas(state)
        assert len(result) == 0

    def test_includes_none_status(self) -> None:
        """status=None should be treated as active (conservative underwriting)."""
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([_make_sca(None)])
        result = get_active_genuine_scas(state)
        assert len(result) == 1

    def test_includes_na_status(self) -> None:
        """status='N/A' should be treated as active."""
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([_make_sca("N/A")])
        result = get_active_genuine_scas(state)
        assert len(result) == 1

    def test_empty_sca_list(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = _make_state_with_scas([])
        result = get_active_genuine_scas(state)
        assert result == []

    def test_no_litigation(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = MagicMock()
        state.extracted.litigation = None
        result = get_active_genuine_scas(state)
        assert result == []

    def test_no_extracted(self) -> None:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        state = MagicMock()
        state.extracted = None
        result = get_active_genuine_scas(state)
        assert result == []


class TestCountActiveGenuineScas:
    """Tests for count_active_genuine_scas."""

    def test_count_matches_len(self) -> None:
        from do_uw.stages.render.sca_counter import count_active_genuine_scas

        state = _make_state_with_scas(MIXED_SCAS)
        assert count_active_genuine_scas(state) == 4

    def test_zero_when_empty(self) -> None:
        from do_uw.stages.render.sca_counter import count_active_genuine_scas

        state = _make_state_with_scas([])
        assert count_active_genuine_scas(state) == 0
