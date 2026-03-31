"""Ground truth coverage tests -- Phase 20 extraction areas.

Validates extraction accuracy for new Phase 20 sections:
- Item 1 business description and company details
- Item 8 footnotes (going concern, restatements)
- Item 9A controls (auditor, material weakness)
- 8-K event timeline
- Ownership (insider %, top holders)
- Risk factors (Item 1A -- requires LLM extraction)

Tests skip gracefully when state.json doesn't exist. Risk factor tests
use xfail because LLM extraction may not yet be populated.

Navigation paths verified against actual TSLA/AAPL state.json files:
- Business description: state.company.business_description.value
- Employee count: state.company.employee_count.value
- Audit: state.extracted.financials.audit.*
- Ownership: state.extracted.governance.ownership.*
- Event timeline: state.company.event_timeline (list)
- Risk factors: state.extracted.risk_factors (list[RiskFactorProfile])
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from tests.ground_truth import ALL_GROUND_TRUTH
from tests.ground_truth.helpers import (
    JsonDict,
    get_nested,
    has_extraction,
    load_state,
    record,
    sourced_value,
)

# All companies except JPM (bank holding company with only 6 categories)
COVERAGE_TICKERS = [t for t in ALL_GROUND_TRUTH if t != "JPM"]


# ---------------------------------------------------------------------------
# Item 1 Business Description
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_item1_has_business_description(ticker: str) -> None:
    """Verify business description is populated."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item1_business"]
    expected: bool = truth["has_business_description"]
    desc = sourced_value(state, "company", "business_description")
    has_desc = desc is not None and len(str(desc)) > 50
    record(ticker, "item1.has_business_description", passed=has_desc == expected)
    assert has_desc == expected, (
        f"Expected has_business_description={expected}, "
        f"got {has_desc} (len={len(str(desc)) if desc else 0})"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_item1_employee_count(ticker: str) -> None:
    """Verify employee count within tolerance."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item1_business"]
    expected: int = truth["employee_count_approximate"]
    tolerance: float = truth["employee_count_tolerance"]
    actual_raw = sourced_value(state, "company", "employee_count")
    if actual_raw is None:
        record(ticker, "item1.employee_count", passed=False)
        pytest.skip(f"Employee count not available for {ticker}")
    actual = float(actual_raw)
    is_close = abs(actual - expected) <= tolerance * expected
    record(ticker, "item1.employee_count", passed=is_close)
    pct_diff = abs(actual - expected) / expected * 100
    assert is_close, (
        f"Employee count: {actual:,.0f} vs expected ~{expected:,} "
        f"({pct_diff:.1f}% diff, tolerance {tolerance * 100:.0f}%)"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Dual-class detection requires Item 1 LLM extraction (Phase 20)",
    strict=False,
)
def test_item1_dual_class(ticker: str) -> None:
    """Verify dual-class share structure detection."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item1_business"]
    expected: bool = truth["is_dual_class"]
    # Check operational_complexity for dual_class flag
    oc = get_nested(state, "company", "operational_complexity")
    actual: bool | None = None
    if isinstance(oc, dict):
        val = cast(Any, cast(JsonDict, oc).get("value"))
        if isinstance(val, dict):
            actual = cast(Any, cast(JsonDict, val).get("has_dual_class"))
    # Also check governance board dual_class_structure
    if actual is None:
        actual_sv = sourced_value(
            state, "extracted", "governance", "board", "dual_class_structure",
        )
        if actual_sv is not None:
            actual = bool(actual_sv)
    record(ticker, "item1.is_dual_class", passed=actual == expected)
    assert actual == expected, (
        f"Expected is_dual_class={expected}, got {actual}"
    )


# ---------------------------------------------------------------------------
# Item 8 Footnotes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_item8_going_concern(ticker: str) -> None:
    """Verify going concern detection from audit data."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item8_footnotes"]
    expected: bool = truth["has_going_concern"]
    gc = get_nested(
        state, "extracted", "financials", "audit", "going_concern",
    )
    actual: bool | None = None
    if isinstance(gc, dict):
        actual = cast(Any, cast(JsonDict, gc).get("value"))
    elif isinstance(gc, bool):
        actual = gc
    record(ticker, "item8.has_going_concern", passed=actual == expected)
    assert actual == expected, (
        f"Expected has_going_concern={expected}, got {actual}"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_item8_restatements(ticker: str) -> None:
    """Verify restatement detection from audit data."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item8_footnotes"]
    expected: bool = truth["has_restatements"]
    restatements = get_nested(
        state, "extracted", "financials", "audit", "restatements",
    )
    has_restatements = (
        isinstance(restatements, list)
        and len(cast(list[Any], restatements)) > 0
    )
    record(
        ticker,
        "item8.has_restatements",
        passed=has_restatements == expected,
    )
    assert has_restatements == expected, (
        f"Expected has_restatements={expected}, got {has_restatements}"
    )


# ---------------------------------------------------------------------------
# Item 9A Controls
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_item9a_material_weakness(ticker: str) -> None:
    """Verify material weakness detection."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item9a_controls"]
    expected: bool = truth["has_material_weakness"]
    mw = get_nested(
        state, "extracted", "financials", "audit", "material_weaknesses",
    )
    has_mw = isinstance(mw, list) and len(cast(list[Any], mw)) > 0
    record(ticker, "item9a.has_material_weakness", passed=has_mw == expected)
    assert has_mw == expected, (
        f"Expected has_material_weakness={expected}, got {has_mw}"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Auditor name extraction only populated for ~3/26 tickers in batch",
    strict=False,
)
def test_item9a_auditor_name(ticker: str) -> None:
    """Verify auditor name (substring match for LLP suffixes)."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item9a_controls"]
    expected: str = truth["auditor_name"]
    auditor_sv = get_nested(
        state, "extracted", "financials", "audit", "auditor_name",
    )
    actual: str | None = None
    if isinstance(auditor_sv, dict):
        actual = cast(Any, cast(JsonDict, auditor_sv).get("value"))
    elif isinstance(auditor_sv, str):
        actual = auditor_sv
    is_match = actual is not None and expected.lower() in actual.lower()
    record(ticker, "item9a.auditor_name", passed=is_match)
    assert is_match, (
        f"Expected auditor containing '{expected}', got '{actual}'"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Auditor opinion extraction not populated in batch run",
    strict=False,
)
def test_item9a_auditor_opinion(ticker: str) -> None:
    """Verify auditor opinion type."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["item9a_controls"]
    expected: str = truth["auditor_opinion"]
    opinion_sv = get_nested(
        state, "extracted", "financials", "audit", "opinion_type",
    )
    actual: str | None = None
    if isinstance(opinion_sv, dict):
        actual = cast(Any, cast(JsonDict, opinion_sv).get("value"))
    elif isinstance(opinion_sv, str):
        actual = opinion_sv
    is_match = actual is not None and expected.lower() == actual.lower()
    record(ticker, "item9a.auditor_opinion", passed=is_match)
    assert is_match, (
        f"Expected opinion '{expected}', got '{actual}'"
    )


# ---------------------------------------------------------------------------
# 8-K Event Timeline
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_eight_k_has_event_timeline(ticker: str) -> None:
    """Verify event timeline is populated."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["eight_k_events"]
    expected: bool = truth["has_event_timeline"]
    timeline = get_nested(state, "company", "event_timeline")
    has_timeline = isinstance(timeline, list) and len(
        cast(list[Any], timeline),
    ) > 0
    record(
        ticker,
        "eight_k.has_event_timeline",
        passed=has_timeline == expected,
    )
    assert has_timeline == expected, (
        f"Expected has_event_timeline={expected}, got {has_timeline}"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_eight_k_event_count(ticker: str) -> None:
    """Verify minimum number of 8-K events in timeline."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["eight_k_events"]
    min_count: int = truth["event_count_min"]
    timeline = get_nested(state, "company", "event_timeline")
    count = len(cast(list[Any], timeline)) if isinstance(timeline, list) else 0
    is_sufficient = count >= min_count
    record(ticker, "eight_k.event_count", passed=is_sufficient)
    assert is_sufficient, (
        f"Expected at least {min_count} events, got {count}"
    )


# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_ownership_insider_pct(ticker: str) -> None:
    """Verify insider ownership percentage meets minimum threshold."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["ownership"]
    min_pct: float = truth["insider_ownership_pct_min"]
    insider_pct = sourced_value(
        state, "extracted", "governance", "ownership", "insider_pct",
    )
    if insider_pct is None:
        record(ticker, "ownership.insider_pct", passed=False)
        pytest.fail("Insider ownership % not available")
    actual = float(insider_pct)
    is_above_min = actual >= min_pct
    record(ticker, "ownership.insider_pct", passed=is_above_min)
    assert is_above_min, (
        f"Expected insider_pct >= {min_pct}%, got {actual:.3f}%"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
def test_ownership_top_institutional_holder(ticker: str) -> None:
    """Verify top institutional holder contains expected name."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    if not has_extraction(state):
        pytest.skip(f"Extraction not completed for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["ownership"]
    expected_contains: str = truth["top_institutional_holder_contains"]
    top_holders = get_nested(
        state, "extracted", "governance", "ownership", "top_holders",
    )
    if not isinstance(top_holders, list) or not top_holders:
        record(ticker, "ownership.top_holder", passed=False)
        pytest.fail("No top holders data available")
    # Check if any top holder name contains the expected substring
    found = False
    holder_names: list[str] = []
    for holder in cast(list[Any], top_holders):
        if isinstance(holder, dict):
            val = cast(Any, cast(JsonDict, holder).get("value"))
            if isinstance(val, dict):
                name = str(cast(JsonDict, val).get("name", ""))
            else:
                name = str(val) if val else ""
        else:
            name = str(holder)
        holder_names.append(name)
        if expected_contains.lower() in name.lower():
            found = True
            break
    record(ticker, "ownership.top_holder", passed=found)
    assert found, (
        f"Expected a top holder containing '{expected_contains}', "
        f"got: {holder_names[:5]}"
    )


# ---------------------------------------------------------------------------
# Risk Factors (Item 1A -- requires LLM extraction, Phase 20)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Risk factor extraction requires LLM pipeline (Phase 20)",
    strict=False,
)
def test_risk_factors_count(ticker: str) -> None:
    """Verify minimum number of extracted risk factors."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["risk_factors"]
    min_count: int = truth["total_risk_factors_min"]
    rf = get_nested(state, "extracted", "risk_factors")
    count = len(cast(list[Any], rf)) if isinstance(rf, list) else 0
    is_sufficient = count >= min_count
    record(ticker, "risk_factors.count", passed=is_sufficient)
    assert is_sufficient, (
        f"Expected at least {min_count} risk factors, got {count}"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Risk factor extraction requires LLM pipeline (Phase 20)",
    strict=False,
)
def test_risk_factors_has_ai_risk(ticker: str) -> None:
    """Verify AI risk factor is identified among risk factors."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["risk_factors"]
    expected: bool = truth["has_ai_risk_factor"]
    rf = get_nested(state, "extracted", "risk_factors")
    has_ai = False
    if isinstance(rf, list):
        for factor in cast(list[Any], rf):
            if isinstance(factor, dict):
                cat = str(cast(JsonDict, factor).get("category", ""))
                title = str(cast(JsonDict, factor).get("title", "")).lower()
                if cat == "AI" or "artificial intelligence" in title or "ai" in title:
                    has_ai = True
                    break
    record(ticker, "risk_factors.has_ai", passed=has_ai == expected)
    assert has_ai == expected, (
        f"Expected has_ai_risk_factor={expected}, got {has_ai}"
    )


@pytest.mark.parametrize("ticker", COVERAGE_TICKERS)
@pytest.mark.xfail(
    reason="Risk factor extraction requires LLM pipeline (Phase 20)",
    strict=False,
)
def test_risk_factors_has_cyber_risk(ticker: str) -> None:
    """Verify cybersecurity risk factor is identified."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    truth = ALL_GROUND_TRUTH[ticker]["risk_factors"]
    expected: bool = truth["has_cyber_risk_factor"]
    rf = get_nested(state, "extracted", "risk_factors")
    has_cyber = False
    if isinstance(rf, list):
        for factor in cast(list[Any], rf):
            if isinstance(factor, dict):
                cat = str(cast(JsonDict, factor).get("category", ""))
                title = str(cast(JsonDict, factor).get("title", "")).lower()
                if cat == "CYBER" or "cyber" in title or "security" in title:
                    has_cyber = True
                    break
    record(ticker, "risk_factors.has_cyber", passed=has_cyber == expected)
    assert has_cyber == expected, (
        f"Expected has_cyber_risk_factor={expected}, got {has_cyber}"
    )
