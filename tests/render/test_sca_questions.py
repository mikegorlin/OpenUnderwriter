"""Tests for SCA question generation, domain slotting, and badge display."""

from __future__ import annotations

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers.sca_questions import (
    generate_sca_questions,
)


def _make_state(ticker: str = "TEST") -> AnalysisState:
    return AnalysisState(ticker=ticker)


def _make_ctx_with_repeat_filer() -> dict:
    """Build ctx with repeat filer data and filing history."""
    return {
        "litigation": {
            "risk_card_filing_history": [
                {"filing_date": "2001-03-14", "case_name": "Case A", "status": "settled", "settlement_amount_m": 100.0},
                {"filing_date": "2010-06-22", "case_name": "Case B", "status": "settled", "settlement_amount_m": 50.0},
                {"filing_date": "2018-11-01", "case_name": "Case C", "status": "dismissed"},
            ],
            "risk_card_repeat_filer": {
                "filer_category": "REPEAT",
                "total_settlement_exposure_m": 250.0,
                "company_settlement_rate_pct": 60.0,
                "recency_tier": "recent",
            },
        },
    }


def _make_ctx_with_benchmarks() -> dict:
    """Build ctx with scenario benchmarks including multiplier data."""
    return {
        "litigation": {
            "risk_card_filing_history": [
                {"filing_date": "2015-01-10", "case_name": "Fraud Case", "status": "settled", "settlement_amount_m": 30.0},
            ],
            "risk_card_repeat_filer": {
                "filer_category": "PRIOR",
                "total_settlement_exposure_m": 30.0,
                "company_settlement_rate_pct": 100.0,
            },
            "risk_card_scenario_benchmarks": [
                {
                    "scenario": "accounting_fraud",
                    "settle_p25_m": 3.5,
                    "settle_p75_m": 32.73,
                    "settle_p90_m": 114.06,
                    "n_settlements": 1199,
                    "settle_mean_m": 69.8,
                    "total_filings": 2402,
                    "settle_median_m": 10.0,
                    "avg_stock_drop_pct": 20.5,
                    "dismissal_rate_pct": 44.5,
                    "sec_inv_severity_multiplier": 11.7,
                    "restatement_severity_multiplier": 3.2,
                },
            ],
        },
    }


class TestFilingFrequencyAlways:
    """SCA-LIT-01 is always generated, even with no data."""

    def test_sca_generates_filing_frequency_always(self) -> None:
        state = _make_state()
        qs = generate_sca_questions(state, {})
        assert len(qs) >= 1
        lit01 = next(q for q in qs if q["question_id"] == "SCA-LIT-01")
        assert lit01["verdict"] == "UPGRADE"
        assert "no SCA history" in lit01["answer"].lower() or "clean" in lit01["answer"].lower()
        assert lit01["domain"] == "litigation_claims"


class TestRepeatFilerData:
    """Repeat filer generates DOWNGRADE with specific numbers."""

    def test_sca_with_repeat_filer_data(self) -> None:
        state = _make_state()
        ctx = _make_ctx_with_repeat_filer()
        qs = generate_sca_questions(state, ctx)

        lit01 = next(q for q in qs if q["question_id"] == "SCA-LIT-01")
        assert lit01["verdict"] == "DOWNGRADE"
        assert "REPEAT" in lit01["answer"]
        assert "250" in lit01["answer"]
        assert len(lit01["evidence"]) > 0


class TestSettlementPerScenario:
    """Settlement severity questions include dollar amounts."""

    def test_sca_settlement_per_scenario(self) -> None:
        state = _make_state()
        ctx = _make_ctx_with_benchmarks()
        qs = generate_sca_questions(state, ctx)

        # Find the accounting_fraud settlement question
        acct_qs = [q for q in qs if q["question_id"].startswith("SCA-LIT-") and q["question_id"] != "SCA-LIT-01"]
        assert len(acct_qs) >= 1, f"Expected settlement question, got IDs: {[q['question_id'] for q in qs]}"

        acct_q = acct_qs[0]
        assert "$10" in acct_q["answer"], f"Missing median $10M in: {acct_q['answer']}"
        assert "$114" in acct_q["answer"], f"Missing P90 $114M in: {acct_q['answer']}"
        assert acct_q["domain"] == "litigation_claims"


class TestPeerComparisonMarketDomain:
    """Peer comparison goes to stock_market domain."""

    def test_sca_peer_comparison_market_domain(self) -> None:
        state = _make_state()
        ctx = _make_ctx_with_benchmarks()
        qs = generate_sca_questions(state, ctx)

        mkt_qs = [q for q in qs if q["question_id"] == "SCA-MKT-01"]
        assert len(mkt_qs) == 1
        assert mkt_qs[0]["domain"] == "stock_market"
        assert "stock drop" in mkt_qs[0]["answer"].lower() or "filings" in mkt_qs[0]["answer"].lower()


class TestTriggerPatternsOperationalDomain:
    """Trigger patterns with multiplier data -> operational_emerging domain."""

    def test_sca_trigger_patterns_operational_domain(self) -> None:
        state = _make_state()
        ctx = _make_ctx_with_benchmarks()
        qs = generate_sca_questions(state, ctx)

        ops_qs = [q for q in qs if q["question_id"] == "SCA-OPS-01"]
        assert len(ops_qs) == 1
        assert ops_qs[0]["domain"] == "operational_emerging"
        # Should DOWNGRADE because sec_inv multiplier 11.7 > 5
        assert ops_qs[0]["verdict"] == "DOWNGRADE"
        assert "11.7" in ops_qs[0]["answer"]


class TestSourceBadge:
    """All generated questions have source == 'SCA Data'."""

    def test_sca_source_badge(self) -> None:
        state = _make_state()

        # Test with empty data
        qs_empty = generate_sca_questions(state, {})
        for q in qs_empty:
            assert q["source"] == "SCA Data", f"Wrong source on {q['question_id']}: {q['source']}"

        # Test with full data
        ctx = _make_ctx_with_benchmarks()
        qs_full = generate_sca_questions(state, ctx)
        for q in qs_full:
            assert q["source"] == "SCA Data", f"Wrong source on {q['question_id']}: {q['source']}"


class TestNoDuplicateIds:
    """No two generated questions share the same question_id."""

    def test_sca_no_duplicate_ids(self) -> None:
        state = _make_state()
        ctx = _make_ctx_with_benchmarks()
        qs = generate_sca_questions(state, ctx)

        ids = [q["question_id"] for q in qs]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"
