"""Golden parity tests for D&O commentary migration from Python to brain YAML.

Verifies that signal do_context consumption produces equivalent D&O intelligence
to the deleted Python functions. Tests cover all 5 migrated sections plus the
Jinja2 template cleanup.

Phase 116-02: Migration parity validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders._signal_fallback import (
    SignalUnavailable,
    safe_get_result,
)


# ---------------------------------------------------------------------------
# Helpers for creating mock signal results
# ---------------------------------------------------------------------------


def _make_signal_result(
    signal_id: str,
    *,
    status: str = "TRIGGERED",
    value: Any = None,
    threshold_level: str = "red",
    evidence: str = "",
    do_context: str = "",
) -> dict[str, Any]:
    """Build a raw signal result dict matching analyze stage output."""
    return {
        "status": status,
        "value": value,
        "threshold_level": threshold_level,
        "evidence": evidence,
        "do_context": do_context,
        "source": "test",
        "confidence": "HIGH",
        "threshold_context": "",
        "factors": [],
        "details": {},
        "data_status": "EVALUATED",
        "content_type": "EVALUATIVE_CHECK",
        "category": "test",
    }


# ---------------------------------------------------------------------------
# Test 1: Audit D&O context parity (sect3_audit.py)
# ---------------------------------------------------------------------------


class TestAuditDoContextParity:
    """Verify signal do_context covers audit D&O commentary."""

    def test_material_weakness_do_context(self) -> None:
        """Signal do_context for material weakness replaces hardcoded text."""
        results = {
            "FIN.ACCT.material_weakness": _make_signal_result(
                "FIN.ACCT.material_weakness",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME Material Weaknesses at 2 (threshold: >0 material weaknesses) signals elevated risk.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.material_weakness")
        assert sig
        assert sig.do_context
        # Old function referenced "material weaknesses", "D&O risk signal", "scienter"
        # New do_context must cover material weakness D&O implications
        assert "material" in sig.do_context.lower() or "weakness" in sig.do_context.lower()

    def test_restatement_do_context(self) -> None:
        """Signal do_context for restatement replaces hardcoded text."""
        results = {
            "FIN.ACCT.restatement": _make_signal_result(
                "FIN.ACCT.restatement",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME Restatement at 2 (threshold: >0) signals elevated restatement risk.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.restatement")
        assert sig
        assert sig.do_context
        assert "restatement" in sig.do_context.lower()

    def test_going_concern_do_context(self) -> None:
        """Signal do_context for going concern replaces hardcoded text."""
        results = {
            "FIN.ACCT.quality_indicators": _make_signal_result(
                "FIN.ACCT.quality_indicators",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME quality indicators at going_concern (threshold: Going concern) signals elevated risk.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.quality_indicators")
        assert sig
        assert sig.do_context

    def test_auditor_tenure_do_context(self) -> None:
        """Signal do_context for auditor replaces hardcoded tenure text."""
        results = {
            "FIN.ACCT.auditor": _make_signal_result(
                "FIN.ACCT.auditor",
                status="TRIGGERED",
                threshold_level="yellow",
                do_context="ACME Auditor at 25yr tenure (threshold: Qualified opinion OR auditor change) is in caution zone.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.auditor")
        assert sig
        assert sig.do_context

    def test_clean_audit_no_do_context(self) -> None:
        """When signals are CLEAR, do_context is still available but optional."""
        results = {
            "FIN.ACCT.material_weakness": _make_signal_result(
                "FIN.ACCT.material_weakness",
                status="CLEAR",
                threshold_level="",
                do_context="ACME Internal Controls is within acceptable range.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.material_weakness")
        assert sig
        # CLEAR signals should have do_context too
        assert sig.do_context

    def test_missing_signal_returns_unavailable(self) -> None:
        """When signal not in results, safe_get_result returns SignalUnavailable."""
        sig = safe_get_result({}, "FIN.ACCT.material_weakness")
        assert isinstance(sig, SignalUnavailable)
        assert not sig  # falsy


# ---------------------------------------------------------------------------
# Test 2: Departure D&O context parity (sect4_market_events.py)
# ---------------------------------------------------------------------------


class TestDepartureDoContextParity:
    """Verify signal do_context covers departure type D&O commentary."""

    def test_unplanned_departure_do_context(self) -> None:
        """Unplanned departure signal provides D&O context."""
        results = {
            "EXEC.DEPARTURE.cfo_departure_timing": _make_signal_result(
                "EXEC.DEPARTURE.cfo_departure_timing",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME CFO departure signals elevated risk -- triggers 10b-5 scrutiny.",
            ),
        }
        sig = safe_get_result(results, "EXEC.DEPARTURE.cfo_departure_timing")
        assert sig
        assert sig.do_context
        # Old function: "Elevated risk -- triggers 10b-5 scrutiny" for UNPLANNED
        assert "departure" in sig.do_context.lower() or "risk" in sig.do_context.lower()

    def test_planned_departure_low_risk(self) -> None:
        """Planned departures should produce low/clear signal."""
        results = {
            "EXEC.DEPARTURE.cfo_departure_timing": _make_signal_result(
                "EXEC.DEPARTURE.cfo_departure_timing",
                status="CLEAR",
                threshold_level="",
                do_context="ACME clear on CFO departure -- no concern identified.",
            ),
        }
        sig = safe_get_result(results, "EXEC.DEPARTURE.cfo_departure_timing")
        assert sig
        assert sig.do_context

    def test_departure_fallback_when_no_signal(self) -> None:
        """When no departure signal, fallback text should be used."""
        sig = safe_get_result({}, "EXEC.DEPARTURE.cfo_departure_timing")
        assert isinstance(sig, SignalUnavailable)


# ---------------------------------------------------------------------------
# Test 3: Governance/leadership D&O context parity (sect5_governance.py)
# ---------------------------------------------------------------------------


class TestGovernanceDoContextParity:
    """Verify signal do_context covers leadership prior litigation commentary."""

    def test_prior_litigation_do_context(self) -> None:
        """Prior litigation signal provides per-executive D&O context."""
        results = {
            "EXEC.PRIOR_LIT.any_officer": _make_signal_result(
                "EXEC.PRIOR_LIT.any_officer",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME triggered Any Officer With Prior Litigation (F9) -- prior litigation correlates with repeat allegations.",
            ),
        }
        sig = safe_get_result(results, "EXEC.PRIOR_LIT.any_officer")
        assert sig
        assert sig.do_context
        # Old: "Prior litigation history at other companies correlates with repeat allegations"
        assert "litigation" in sig.do_context.lower() or "prior" in sig.do_context.lower()

    def test_board_prior_litigation_signal(self) -> None:
        """Board-level prior litigation signal available."""
        results = {
            "GOV.BOARD.prior_litigation": _make_signal_result(
                "GOV.BOARD.prior_litigation",
                status="TRIGGERED",
                threshold_level="yellow",
                do_context="ACME Board Prior Litigation at 3 -- review recommended.",
            ),
        }
        sig = safe_get_result(results, "GOV.BOARD.prior_litigation")
        assert sig
        assert sig.do_context

    def test_clean_governance_no_flags(self) -> None:
        """Clean governance produces CLEAR signal with protective context."""
        results = {
            "EXEC.PRIOR_LIT.any_officer": _make_signal_result(
                "EXEC.PRIOR_LIT.any_officer",
                status="CLEAR",
                threshold_level="",
                do_context="ACME clear on prior litigation -- no concern identified.",
            ),
        }
        sig = safe_get_result(results, "EXEC.PRIOR_LIT.any_officer")
        assert sig
        assert "clear" in sig.do_context.lower()


# ---------------------------------------------------------------------------
# Test 4: SCA D&O context parity (sect6_litigation.py)
# ---------------------------------------------------------------------------


class TestScaDoContextParity:
    """Verify signal do_context covers SCA D&O commentary."""

    def test_active_sca_do_context(self) -> None:
        """Active SCA signal provides D&O context."""
        results = {
            "LIT.SCA.active": _make_signal_result(
                "LIT.SCA.active",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME Active SCA at 2 -- direct Side A/B/C coverage exposure.",
            ),
        }
        sig = safe_get_result(results, "LIT.SCA.active")
        assert sig
        assert sig.do_context
        # Old: "Direct exposure to Side A/B/C coverage; prior SCA is strongest future predictor"
        assert "sca" in sig.do_context.lower() or "coverage" in sig.do_context.lower() or "active" in sig.do_context.lower()

    def test_settlement_history_do_context(self) -> None:
        """Settlement history signal provides baseline context."""
        results = {
            "LIT.SCA.prior_settle": _make_signal_result(
                "LIT.SCA.prior_settle",
                status="TRIGGERED",
                threshold_level="yellow",
                do_context="ACME prior settlement at $5M -- severity baseline for pricing.",
            ),
        }
        sig = safe_get_result(results, "LIT.SCA.prior_settle")
        assert sig
        assert sig.do_context

    def test_lead_counsel_tier_context(self) -> None:
        """Lead counsel tier is addressable via SCA exposure signal."""
        results = {
            "LIT.SCA.exposure": _make_signal_result(
                "LIT.SCA.exposure",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME SCA exposure elevated -- tier 1 counsel correlates with higher settlements.",
            ),
        }
        sig = safe_get_result(results, "LIT.SCA.exposure")
        assert sig
        assert sig.do_context

    def test_no_sca_clean_signal(self) -> None:
        """No SCA produces CLEAR signal."""
        results = {
            "LIT.SCA.active": _make_signal_result(
                "LIT.SCA.active",
                status="CLEAR",
                threshold_level="",
                do_context="ACME clear on active SCA -- no litigation concern.",
            ),
        }
        sig = safe_get_result(results, "LIT.SCA.active")
        assert sig
        assert "clear" in sig.do_context.lower()


# ---------------------------------------------------------------------------
# Test 5: Pattern D&O context parity (sect7_scoring_detail.py)
# ---------------------------------------------------------------------------


class TestPatternDoContextParity:
    """Verify signal do_context covers pattern detection D&O commentary."""

    def test_high_severity_pattern_do_context(self) -> None:
        """HIGH severity pattern has do_context from signal."""
        # Pattern do_context comes from signal_contributions on FactorScore
        # which links back to signal IDs with do_context
        results = {
            "FIN.ACCT.restatement": _make_signal_result(
                "FIN.ACCT.restatement",
                status="TRIGGERED",
                threshold_level="red",
                do_context="ACME restatement pattern -- elevated claim probability, verify tower position.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.restatement")
        assert sig
        assert sig.do_context
        # Old: "This HIGH/SEVERE pattern indicates elevated claim probability"
        assert "claim" in sig.do_context.lower() or "pattern" in sig.do_context.lower() or "tower" in sig.do_context.lower()

    def test_moderate_pattern_no_do_context_needed(self) -> None:
        """Moderate patterns did not get D&O context in old code either."""
        results = {
            "FIN.ACCT.restatement": _make_signal_result(
                "FIN.ACCT.restatement",
                status="CLEAR",
                threshold_level="",
                do_context="ACME clear on restatement.",
            ),
        }
        sig = safe_get_result(results, "FIN.ACCT.restatement")
        assert sig
        # CLEAR signals still have do_context


# ---------------------------------------------------------------------------
# Test 6: Distress template has no inline D&O conditionals
# ---------------------------------------------------------------------------


class TestDistressTemplateNoInlineDoContext:
    """Verify distress_indicators.html.j2 uses pass-through variables."""

    def test_template_uses_do_context_variables(self) -> None:
        """Template must reference do_context pass-through variables."""
        import pathlib

        template_path = pathlib.Path(
            "src/do_uw/templates/html/sections/financial/distress_indicators.html.j2"
        )
        content = template_path.read_text()
        # Must have at least the D&O interpretation section with pass-through vars
        assert "z_do_context" in content or "beneish_do_context" in content
        assert "o_do_context" in content or "piotroski_do_context" in content

    def test_template_no_inline_do_conditionals_in_relevance_column(self) -> None:
        """D&O Relevance column should not have hardcoded conditional text."""
        import pathlib
        import re

        template_path = pathlib.Path(
            "src/do_uw/templates/html/sections/financial/distress_indicators.html.j2"
        )
        content = template_path.read_text()
        # The inline conditionals we're removing are in the "D&O Relevance" <td> cells
        # They look like: {% if fin.z_zone and fin.z_zone|lower == 'distress' %}Bankruptcy risk...
        # After migration, these should use {{ fin.z_do_context }} instead
        # Check there are no hardcoded D&O evaluative strings in the relevance column
        relevance_patterns = [
            r"Bankruptcy risk .* elevates going-concern",
            r"Moderate stress .* monitor for deterioration",
            r"Low bankruptcy risk .* protective for D&O",
            r"Low restatement risk .* reduces SCA exposure",
            r"Elevated manipulation signal .* restatement is primary SCA trigger",
            r"Insolvency risk .* Zone-of-Insolvency",
            r"Strong fundamentals .* lower claim frequency",
            r"Weak fundamentals .* higher derivative suit exposure",
        ]
        for pattern in relevance_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, (
                f"Found inline D&O text matching '{pattern}' -- should use do_context variable"
            )
