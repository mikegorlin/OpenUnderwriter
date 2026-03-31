"""SCA (Securities Class Action) question generator for underwriting framework.

Produces Supabase-derived underwriting questions from risk card data and
slots them into matching domains (Litigation, Market, Operational).

Four SCA scenario types per D-05:
  1. Filing frequency & recidivism -> Litigation domain
  2. Settlement ranges & severity -> Litigation domain
  3. Peer SCA comparison -> Market domain
  4. Trigger pattern matching -> Operational domain

Every generated question carries ``source: "SCA Data"`` for template badge
display to distinguish from brain-derived questions (per D-04).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)


def generate_sca_questions(
    state: AnalysisState,
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate SCA-derived underwriting questions from risk card data.

    Always returns at least one question (SCA-LIT-01 for filing frequency)
    even when no SCA data is available -- a clean record is itself a finding.

    Args:
        state: Full pipeline analysis state.
        ctx: Render context dict (may contain ``litigation`` sub-dict).

    Returns:
        List of question dicts ready for domain slotting, each with
        question_id, text, weight, source, domain, data_sources, answer,
        evidence, verdict, confidence, data_found.
    """
    lit = ctx.get("lit_detail", {})

    # Extract risk card data from context first, fallback to state
    filing_history = lit.get("risk_card_filing_history", [])
    repeat_filer = lit.get("risk_card_repeat_filer", {})
    scenario_benchmarks = lit.get("risk_card_scenario_benchmarks", [])

    # Fallback: try state.acquired_data.litigation_data
    if not filing_history and not repeat_filer:
        risk_card = _extract_risk_card_from_state(state)
        if risk_card:
            filing_history = risk_card.get("filing_history", [])
            repeat_filer = risk_card.get("repeat_filer_detail", {})
            scenario_benchmarks = risk_card.get("scenario_benchmarks", [])

    questions: list[dict[str, Any]] = []

    # Type 1: Filing frequency & recidivism (ALWAYS generated)
    questions.append(_build_filing_frequency(filing_history, repeat_filer))

    # Type 2: Settlement ranges & severity (one per scenario)
    for bench in scenario_benchmarks:
        q = _build_settlement_severity(bench, filing_history, repeat_filer)
        if q:
            questions.append(q)

    # Type 3: Peer SCA comparison (if benchmarks exist)
    if scenario_benchmarks:
        questions.append(_build_peer_comparison(scenario_benchmarks))

    # Type 4: Trigger pattern matching (if multiplier data exists)
    trigger_q = _build_trigger_patterns(scenario_benchmarks)
    if trigger_q:
        questions.append(trigger_q)

    # Deduplicate by question_id (safety net)
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for q in questions:
        qid = q.get("question_id", "")
        if qid not in seen:
            seen.add(qid)
            deduped.append(q)

    logger.info("Generated %d SCA questions", len(deduped))
    return deduped


def answer_sca_question(
    q: dict[str, Any],
    state: AnalysisState,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """Re-answer a pre-generated SCA question from current data.

    Useful when questions are pre-generated but need refreshing with
    updated pipeline data.

    Args:
        q: Previously generated SCA question dict.
        state: Current pipeline state.
        ctx: Current render context.

    Returns:
        Updated answer fields (answer, evidence, verdict, confidence, data_found).
    """
    qid = q.get("question_id", "")
    lit = ctx.get("lit_detail", {})
    filing_history = lit.get("risk_card_filing_history", [])
    repeat_filer = lit.get("risk_card_repeat_filer", {})
    scenario_benchmarks = lit.get("risk_card_scenario_benchmarks", [])

    if not filing_history and not repeat_filer:
        risk_card = _extract_risk_card_from_state(state)
        if risk_card:
            filing_history = risk_card.get("filing_history", [])
            repeat_filer = risk_card.get("repeat_filer_detail", {})
            scenario_benchmarks = risk_card.get("scenario_benchmarks", [])

    if qid == "SCA-LIT-01":
        result = _build_filing_frequency(filing_history, repeat_filer)
        return {k: result[k] for k in ("answer", "evidence", "verdict", "confidence", "data_found")}

    if qid == "SCA-MKT-01" and scenario_benchmarks:
        result = _build_peer_comparison(scenario_benchmarks)
        return {k: result[k] for k in ("answer", "evidence", "verdict", "confidence", "data_found")}

    if qid == "SCA-OPS-01":
        result = _build_trigger_patterns(scenario_benchmarks) or _no_sca_data()
        return {k: result[k] for k in ("answer", "evidence", "verdict", "confidence", "data_found")}

    # Settlement severity questions (SCA-LIT-{SCENARIO})
    if qid.startswith("SCA-LIT-") and qid != "SCA-LIT-01":
        for bench in scenario_benchmarks:
            scenario_tag = _scenario_tag(bench.get("scenario", ""))
            if qid == f"SCA-LIT-{scenario_tag}":
                result = _build_settlement_severity(bench, filing_history, repeat_filer)
                if result:
                    return {k: result[k] for k in ("answer", "evidence", "verdict", "confidence", "data_found")}

    return _no_sca_data()


# ── Internal builders ────────────────────────────────────────────────


def _base_question(
    question_id: str,
    text: str,
    domain: str,
    weight: int,
) -> dict[str, Any]:
    """Build base question dict with SCA Data source badge."""
    return {
        "question_id": question_id,
        "text": text,
        "weight": weight,
        "source": "SCA Data",
        "domain": domain,
        "data_sources": ["supabase_sca"],
    }


def _build_filing_frequency(
    filing_history: list[dict[str, Any]],
    repeat_filer: dict[str, Any],
) -> dict[str, Any]:
    """Type 1: Filing frequency & recidivism -> Litigation domain (SCA-LIT-01)."""
    q = _base_question(
        question_id="SCA-LIT-01",
        text="What is the company's SCA filing frequency and recidivism category?",
        domain="litigation_claims",
        weight=9,
    )

    n_filings = len(filing_history)
    filer_cat = repeat_filer.get("filer_category", "NONE") if repeat_filer else "NONE"
    settle_rate = safe_float(repeat_filer.get("company_settlement_rate_pct"), 0.0) if repeat_filer else 0.0
    total_exposure = safe_float(repeat_filer.get("total_settlement_exposure_m"), 0.0) if repeat_filer else 0.0

    if n_filings == 0 and filer_cat in ("NONE", "FIRST_TIME"):
        q.update({
            "answer": "FIRST_TIME filer -- no SCA history. Clean litigation record.",
            "evidence": ["No SCA filings found in database", f"Filer category: {filer_cat}"],
            "verdict": "UPGRADE",
            "confidence": "HIGH",
            "data_found": True,
        })
    else:
        evidence = [
            f"Filer category: {filer_cat}",
            f"Total SCA filings: {n_filings}",
        ]
        if settle_rate > 0:
            evidence.append(f"Settlement rate: {settle_rate:.0f}%")
        if total_exposure > 0:
            evidence.append(f"Total settlement exposure: ${total_exposure:,.1f}M")

        if filer_cat in ("REPEAT", "CHRONIC") or n_filings >= 2:
            verdict = "DOWNGRADE"
            answer = (
                f"{filer_cat} filer -- {n_filings} SCA filing(s). "
                f"Settlement rate: {settle_rate:.0f}%. "
                f"Total exposure: ${total_exposure:,.1f}M."
            )
        else:
            verdict = "NEUTRAL"
            answer = f"Single prior SCA filing. Filer category: {filer_cat}."

        q.update({
            "answer": answer,
            "evidence": evidence,
            "verdict": verdict,
            "confidence": "HIGH",
            "data_found": True,
        })

    return q


def _build_settlement_severity(
    benchmark: dict[str, Any],
    filing_history: list[dict[str, Any]],
    repeat_filer: dict[str, Any],
) -> dict[str, Any] | None:
    """Type 2: Settlement ranges & severity -> Litigation domain."""
    scenario = benchmark.get("scenario", "")
    if not scenario:
        return None

    tag = _scenario_tag(scenario)
    q = _base_question(
        question_id=f"SCA-LIT-{tag}",
        text=f"What are the settlement severity benchmarks for {_humanize_scenario(scenario)} cases?",
        domain="litigation_claims",
        weight=8,
    )

    median = safe_float(benchmark.get("settle_median_m"), 0.0)
    p25 = safe_float(benchmark.get("settle_p25_m"), 0.0)
    p75 = safe_float(benchmark.get("settle_p75_m"), 0.0)
    p90 = safe_float(benchmark.get("settle_p90_m"), 0.0)
    n_settlements = int(safe_float(benchmark.get("n_settlements"), 0))
    total_filings = int(safe_float(benchmark.get("total_filings"), 0))

    answer = (
        f"For {_humanize_scenario(scenario)} cases, median settlement is "
        f"${median:,.1f}M (P25: ${p25:,.1f}M, P75: ${p75:,.1f}M, P90: ${p90:,.1f}M). "
        f"{n_settlements} comparable settlements from {total_filings} filings."
    )

    evidence = [
        f"Scenario: {_humanize_scenario(scenario)}",
        f"Median settlement: ${median:,.1f}M",
        f"P90 settlement: ${p90:,.1f}M",
        f"Sample size: {n_settlements} settlements / {total_filings} filings",
    ]

    # Check if company has this scenario in its history
    company_scenarios = (
        repeat_filer.get("scenario_history", [])
        if repeat_filer
        else []
    )
    # Also check company_profile if available
    if not company_scenarios and isinstance(benchmark.get("_company_profile"), dict):
        company_scenarios = benchmark["_company_profile"].get("scenario_history", [])

    has_scenario = scenario in company_scenarios
    if has_scenario:
        verdict = "DOWNGRADE"
        evidence.append(f"Company has prior {_humanize_scenario(scenario)} filing(s)")
    else:
        verdict = "NEUTRAL"

    q.update({
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    })
    return q


def _build_peer_comparison(
    scenario_benchmarks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Type 3: Peer SCA comparison -> Market domain (SCA-MKT-01)."""
    q = _base_question(
        question_id="SCA-MKT-01",
        text="How does the company's SCA exposure compare to sector peers?",
        domain="stock_market",
        weight=7,
    )

    evidence: list[str] = []
    total_filings_all = 0
    avg_drop_parts: list[float] = []

    for bench in scenario_benchmarks:
        scenario = bench.get("scenario", "unknown")
        total = int(safe_float(bench.get("total_filings"), 0))
        dismissal = safe_float(bench.get("dismissal_rate_pct"), 0.0)
        drop_pct = safe_float(bench.get("avg_stock_drop_pct"), 0.0)

        total_filings_all += total
        if drop_pct > 0:
            avg_drop_parts.append(drop_pct)

        evidence.append(
            f"{_humanize_scenario(scenario)}: {total} filings, "
            f"{dismissal:.1f}% dismissal rate"
        )

    if avg_drop_parts:
        avg_drop = sum(avg_drop_parts) / len(avg_drop_parts)
        evidence.append(f"Average stock drop in matching cases: {avg_drop:.1f}%")
        answer = (
            f"Sector has {total_filings_all} SCA filings across "
            f"{len(scenario_benchmarks)} scenario type(s). "
            f"Average stock drop in matching cases: {avg_drop:.1f}%."
        )
    else:
        answer = (
            f"Sector has {total_filings_all} SCA filings across "
            f"{len(scenario_benchmarks)} scenario type(s)."
        )

    # Elevated if high filing volume
    verdict = "DOWNGRADE" if total_filings_all > 500 else "NEUTRAL"

    q.update({
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    })
    return q


def _build_trigger_patterns(
    scenario_benchmarks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Type 4: Trigger pattern matching -> Operational domain (SCA-OPS-01)."""
    if not scenario_benchmarks:
        return None

    # Only generate if multiplier data exists
    has_multipliers = any(
        bench.get("sec_inv_severity_multiplier") is not None
        or bench.get("restatement_severity_multiplier") is not None
        for bench in scenario_benchmarks
    )
    if not has_multipliers:
        return None

    q = _base_question(
        question_id="SCA-OPS-01",
        text="Does the company match known SCA trigger patterns with elevated severity multipliers?",
        domain="operational_emerging",
        weight=8,
    )

    evidence: list[str] = []
    max_sec_mult = 0.0
    max_restate_mult = 0.0
    trigger_scenarios: list[str] = []

    for bench in scenario_benchmarks:
        scenario = bench.get("scenario", "unknown")
        sec_mult = safe_float(bench.get("sec_inv_severity_multiplier"), 0.0)
        restate_mult = safe_float(bench.get("restatement_severity_multiplier"), 0.0)

        if sec_mult > 0 or restate_mult > 0:
            trigger_scenarios.append(_humanize_scenario(scenario))
            evidence.append(
                f"{_humanize_scenario(scenario)}: "
                f"SEC investigation multiplier {sec_mult:.1f}x, "
                f"restatement multiplier {restate_mult:.1f}x"
            )
            max_sec_mult = max(max_sec_mult, sec_mult)
            max_restate_mult = max(max_restate_mult, restate_mult)

    if not evidence:
        return None

    scenarios_str = ", ".join(trigger_scenarios)
    answer = (
        f"Company matches {scenarios_str} pattern(s). "
        f"SEC investigation multiplier: {max_sec_mult:.1f}x. "
        f"Restatement multiplier: {max_restate_mult:.1f}x."
    )

    # DOWNGRADE if any multiplier > 5x
    verdict = "DOWNGRADE" if max_sec_mult > 5 or max_restate_mult > 5 else "NEUTRAL"

    q.update({
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    })
    return q


# ── Helpers ──────────────────────────────────────────────────────────


def _extract_risk_card_from_state(state: AnalysisState) -> dict[str, Any] | None:
    """Try to get risk_card from state.acquired_data.litigation_data."""
    if not state.acquired_data:
        return None
    lit_data = getattr(state.acquired_data, "litigation_data", None)
    if not lit_data:
        return None
    if isinstance(lit_data, dict):
        return lit_data.get("risk_card")
    return getattr(lit_data, "risk_card", None)


def _scenario_tag(scenario: str) -> str:
    """Convert scenario name to question ID suffix (max 8 chars, uppercase)."""
    return scenario[:8].upper().replace(" ", "_").replace("-", "_")


def _humanize_scenario(scenario: str) -> str:
    """Convert scenario slug to human-readable label."""
    return scenario.replace("_", " ").title()


def _no_sca_data() -> dict[str, Any]:
    """Return empty answer for missing SCA data."""
    return {
        "answer": "No SCA data available for this question.",
        "evidence": [],
        "verdict": "NO_DATA",
        "confidence": "LOW",
        "data_found": False,
    }


__all__ = ["generate_sca_questions", "answer_sca_question"]
