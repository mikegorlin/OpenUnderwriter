"""Ground truth validation tests -- identity, financials, distress.

Validates extracted AnalysisState data against hand-verified ground truth
values. Tests are parametrized across all 10 companies and report
field-level accuracy.

Design decisions:
- Tests SKIP (not fail) if no state file exists for a company
- Financial comparisons use relative tolerance (10% for most values)
  to accommodate XBRL tag variations and period differences
- Governance fields use xfail for known extraction limitations
- Accuracy report prints summary to stdout for visibility

Phase 20 coverage tests (Items 1/7/8/9A, 8-K, ownership, risk factors)
are in test_ground_truth_coverage.py to keep both files under 500 lines.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast

import pytest

from tests.ground_truth import ALL_GROUND_TRUTH
from tests.ground_truth.helpers import (
    JsonDict,
    assert_financial_close,
    find_line_item_by_label,
    find_line_item_latest,
    get_nested,
    has_extraction,
    load_state,
    market_cap_tier,
    print_accuracy_report,
    record,
    sourced_value,
    sourced_value_from_obj,
)

# ---------------------------------------------------------------------------
# Identity validation
# ---------------------------------------------------------------------------

TICKERS = list(ALL_GROUND_TRUTH.keys())


@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_legal_name(ticker: str) -> None:
    """Verify extracted legal name matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["identity"]["legal_name"]
    actual = sourced_value(state, "company", "identity", "legal_name")
    record(ticker, "identity.legal_name", passed=actual == expected)
    assert actual == expected, f"Expected '{expected}', got '{actual}'"


@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_cik(ticker: str) -> None:
    """Verify extracted CIK matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["identity"]["cik"]
    actual = sourced_value(state, "company", "identity", "cik")
    # CIK may have leading zeros stripped
    actual_normalized = str(int(actual)) if actual else None
    expected_normalized = str(int(expected))
    record(
        ticker,
        "identity.cik",
        passed=actual_normalized == expected_normalized,
    )
    assert actual_normalized == expected_normalized, (
        f"Expected CIK '{expected_normalized}', got '{actual_normalized}'"
    )


@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_sic_code(ticker: str) -> None:
    """Verify extracted SIC code matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["identity"]["sic_code"]
    actual = sourced_value(state, "company", "identity", "sic_code")
    record(ticker, "identity.sic_code", passed=actual == expected)
    assert actual == expected, f"Expected SIC '{expected}', got '{actual}'"


@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_sector(ticker: str) -> None:
    """Verify extracted sector matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["identity"]["sector"]
    actual = sourced_value(state, "company", "identity", "sector")
    record(ticker, "identity.sector", passed=actual == expected)
    assert actual == expected, f"Expected sector '{expected}', got '{actual}'"


@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_exchange(ticker: str) -> None:
    """Verify extracted exchange matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["identity"]["exchange"]
    actual = sourced_value(state, "company", "identity", "exchange")
    record(ticker, "identity.exchange", passed=actual == expected)
    assert actual == expected, f"Expected exchange '{expected}', got '{actual}'"


# ---------------------------------------------------------------------------
# Financial validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", TICKERS)
def test_financials_revenue(ticker: str) -> None:
    """Verify extracted revenue matches ground truth within tolerance."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: float = truth["financials"]["revenue_latest"]
    actual = find_line_item_latest(state, "income_statement", "revenue")
    if actual is None:
        actual = find_line_item_by_label(
            state, "income_statement", "revenue", "net sales",
        )
    assert_financial_close(ticker, "revenue", actual, expected, rel_tol=0.10)


@pytest.mark.parametrize("ticker", TICKERS)
def test_financials_net_income(ticker: str) -> None:
    """Verify extracted net income matches ground truth within tolerance."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: float = truth["financials"]["net_income_latest"]
    actual = find_line_item_latest(state, "income_statement", "net_income")
    if actual is None:
        actual = find_line_item_by_label(
            state, "income_statement", "net income", "net loss",
        )
    assert_financial_close(
        ticker, "net_income", actual, expected, rel_tol=0.10,
    )


@pytest.mark.parametrize("ticker", TICKERS)
def test_financials_total_assets(ticker: str) -> None:
    """Verify extracted total assets matches ground truth within tolerance."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: float = truth["financials"]["total_assets"]
    actual = find_line_item_latest(state, "balance_sheet", "total_assets")
    assert_financial_close(
        ticker, "total_assets", actual, expected, rel_tol=0.10,
    )


@pytest.mark.parametrize("ticker", TICKERS)
def test_financials_cash(ticker: str) -> None:
    """Verify extracted cash matches ground truth within tolerance."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: float = truth["financials"]["cash_and_equivalents"]
    actual = find_line_item_latest(
        state, "balance_sheet", "cash_and_equivalents",
    )
    assert_financial_close(
        ticker, "cash_and_equivalents", actual, expected, rel_tol=0.10,
    )


# ---------------------------------------------------------------------------
# Market validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", TICKERS)
def test_market_cap_tier(ticker: str) -> None:
    """Verify market cap tier classification matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["market"]["market_cap_tier"]
    market_cap_raw = sourced_value(state, "company", "market_cap")
    market_cap: float | None = (
        float(market_cap_raw) if market_cap_raw is not None else None
    )
    actual = market_cap_tier(market_cap)
    record(ticker, "market.market_cap_tier", passed=actual == expected)
    if market_cap is not None:
        msg = (
            f"Expected tier '{expected}', got '{actual}' "
            f"(market_cap={market_cap:,.0f})"
        )
    else:
        msg = f"Expected tier '{expected}', got None (no market_cap)"
    assert actual == expected, msg


# ---------------------------------------------------------------------------
# Governance validation (xfail -- regex extraction is known-weak)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", TICKERS)
@pytest.mark.xfail(
    reason="Board size extraction requires LLM-based proxy parsing (Phase 19)",
    strict=False,
)
def test_governance_board_size(ticker: str) -> None:
    """Verify extracted board size matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: int = truth["governance"]["board_size"]
    # Try board.size SourcedValue
    actual = sourced_value(
        state, "extracted", "governance", "board", "size",
    )
    if actual is None:
        # Fallback: count board_forensics entries
        board_forensics = get_nested(
            state, "extracted", "governance", "board_forensics",
        )
        if isinstance(board_forensics, list) and len(
            cast(list[Any], board_forensics),
        ) > 0:
            actual = len(cast(list[Any], board_forensics))
    record(ticker, "governance.board_size", passed=actual == expected)
    assert actual == expected, (
        f"Expected board size {expected}, got {actual}"
    )


@pytest.mark.parametrize("ticker", TICKERS)
@pytest.mark.xfail(
    reason="CEO name extraction requires LLM-based proxy parsing (Phase 19)",
    strict=False,
)
def test_governance_ceo_name(ticker: str) -> None:
    """Verify extracted CEO name matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: str = truth["governance"]["ceo_name"]
    leadership = get_nested(
        state, "extracted", "governance", "leadership",
    )
    actual: str | None = None
    if isinstance(leadership, dict):
        executives: list[Any] = cast(
            list[Any],
            cast(JsonDict, leadership).get("executives", []),
        )
        for exec_profile in executives:
            title = sourced_value_from_obj(exec_profile, "title")
            if title and "CEO" in str(title).upper():
                name = sourced_value_from_obj(exec_profile, "name")
                if name and expected.lower() in str(name).lower():
                    actual = expected
                    break
                if name:
                    actual = str(name)
                    break
    record(ticker, "governance.ceo_name", passed=actual == expected)
    assert actual == expected, f"Expected CEO '{expected}', got '{actual}'"


# ---------------------------------------------------------------------------
# Litigation validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", TICKERS)
def test_litigation_has_active_sca(ticker: str) -> None:
    """Verify SCA detection matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected: bool = truth["litigation"]["has_active_sca"]
    scas = get_nested(
        state, "extracted", "litigation", "securities_class_actions",
    )
    sca_count = len(cast(list[Any], scas)) if isinstance(scas, list) else 0
    actual = sca_count > 0
    record(ticker, "litigation.has_active_sca", passed=actual == expected)
    assert actual == expected, (
        f"Expected has_active_sca={expected}, "
        f"got {actual} (SCA count: {sca_count})"
    )


# ---------------------------------------------------------------------------
# Distress validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", TICKERS)
def test_distress_altman_z_zone(ticker: str) -> None:
    """Verify Altman Z-Score zone matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]
    expected_zone: str = str(truth["distress"]["altman_z_zone"]).lower()
    altman = get_nested(
        state, "extracted", "financials", "distress", "altman_z_score",
    )
    if not isinstance(altman, dict):
        record(ticker, "distress.altman_z_zone", passed=False)
        pytest.fail("Altman Z-Score not computed")
    actual_zone = str(
        cast(JsonDict, altman).get("zone", ""),
    ).lower()
    # For banks, "not_applicable" is also acceptable
    acceptable: set[str] = {expected_zone}
    if expected_zone == "safe":
        acceptable.add("not_applicable")
    is_match = actual_zone in acceptable
    record(ticker, "distress.altman_z_zone", passed=is_match)
    score = cast(Any, cast(JsonDict, altman).get("score"))
    assert is_match, (
        f"Expected zone '{expected_zone}' (or {acceptable}), "
        f"got '{actual_zone}' (score: {score})"
    )


# ---------------------------------------------------------------------------
# Accuracy report (runs after all tests via session-scoped fixture)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="session")
def print_accuracy_summary() -> Generator[None, None, None]:
    """Print accuracy summary after all tests complete."""
    yield
    for ticker in TICKERS:
        print_accuracy_report(ticker)
