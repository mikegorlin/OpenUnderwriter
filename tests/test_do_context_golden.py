"""Golden snapshot tests: YAML do_context must match Python function output.

Verifies that brain YAML do_context templates produce identical strings to the
original hardcoded Python functions they replace. Each test constructs a mock
SignalResult, loads the YAML signal definition, selects the template via
_select_template(), renders it via render_do_context(), and asserts exact
match to the golden string captured from the Python function.

Piotroski uses {value} in templates -- the score is passed as SignalResult.value.
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.do_context_engine import (
    _select_template,
    render_do_context,
)
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus
from do_uw.brain.brain_unified_loader import load_signals
from do_uw.stages.render.context_builders._signal_consumer import (
    SignalResultView,
    get_signal_result,
)

# ---------------------------------------------------------------------------
# Golden strings: exact output of the original Python functions
# ---------------------------------------------------------------------------

GOLDEN_ALTMAN = {
    "distress": (
        "Distress zone (below 1.81) \u2014 historically associated with "
        "2-3x higher D&O claim frequency. Companies in financial "
        "distress face elevated exposure to going-concern lawsuits, "
        "creditor derivative actions, and breach-of-fiduciary-duty claims."
    ),
    "grey": (
        "Grey zone (1.81-2.99) \u2014 moderate financial stress. "
        "Warrants monitoring for deterioration that could trigger "
        "securities class actions if stock price declines coincide "
        "with negative financial disclosures."
    ),
    "safe": (
        "Safe zone (above 2.99) \u2014 low bankruptcy probability. "
        "Strong financial position is a protective factor for D&O risk, "
        "reducing exposure to going-concern and insolvency-related claims."
    ),
}

GOLDEN_BENEISH = {
    "safe": (
        "Below -2.22 threshold \u2014 low earnings manipulation probability. "
        "Reduces restatement risk, which is a primary trigger for "
        "securities fraud class actions under Section 10(b) and Rule 10b-5."
    ),
    "grey": (
        "Grey zone (-2.22 to -1.78) \u2014 inconclusive manipulation signal. "
        "Scores in this range warrant deeper forensic review. "
        "Historically, companies restating earnings face SCA filing "
        "rates 5-8x higher than non-restating peers."
    ),
    "danger": (
        "Above -1.78 \u2014 elevated manipulation probability. "
        "Research shows scores above this threshold predict earnings "
        "restatement with ~76% accuracy (Beneish 1999). Restatements "
        "are the single strongest predictor of securities class actions, "
        "with average D&O settlements exceeding $35M."
    ),
}

GOLDEN_PIOTROSKI = {
    "strong_8": (
        "Score of 8/9 indicates strong fundamentals across "
        "profitability, leverage, and efficiency. Strong financial health "
        "correlates with lower D&O claim frequency and smaller settlements."
    ),
    "weak_2": (
        "Score of 2/9 signals weak fundamentals \u2014 companies "
        "scoring 0-3 historically experience higher stock volatility and "
        "increased exposure to shareholder derivative suits alleging "
        "mismanagement."
    ),
    "moderate_5": (
        "Score of 5/9 indicates moderate financial strength. "
        "Mid-range scores suggest mixed signals across profitability, "
        "leverage, and operational efficiency metrics."
    ),
}

GOLDEN_OHLSON = {
    "distress": (
        "Elevated bankruptcy probability (O-Score > 0.5). "
        "The Ohlson model considers size, leverage, profitability, and "
        "liquidity \u2014 high scores correlate with Zone-of-Insolvency "
        "fiduciary duty claims against directors."
    ),
    "safe": (
        "Low bankruptcy probability \u2014 supportive of favorable D&O risk profile."
    ),
}

# ---------------------------------------------------------------------------
# Helper to load do_context templates from brain YAML
# ---------------------------------------------------------------------------


def _load_signal_do_context(signal_id: str) -> dict[str, str]:
    """Load the do_context templates dict for a signal from brain YAML."""
    data = load_signals()
    for sig in data.get("signals", []):
        if sig.get("id") == signal_id:
            pres = sig.get("presentation", {})
            if isinstance(pres, dict):
                return pres.get("do_context", {})
    return {}


def _make_result(
    signal_id: str,
    value: float | int | None,
    status: str,
    threshold_level: str,
) -> SignalResult:
    """Construct a minimal SignalResult for template rendering."""
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_id,
        status=SignalStatus(status),
        value=value,
        threshold_level=threshold_level,
    )


# ---------------------------------------------------------------------------
# Altman Z-Score golden parity tests
# ---------------------------------------------------------------------------


class TestAltmanDoContext:
    """YAML do_context for FIN.ACCT.quality_indicators matches Python golden."""

    SIGNAL_ID = "FIN.ACCT.quality_indicators"

    def test_distress(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, 1.5, "TRIGGERED", "red")
        template = _select_template(templates, "TRIGGERED", "red")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_ALTMAN["distress"]

    def test_grey(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, 2.5, "TRIGGERED", "yellow")
        template = _select_template(templates, "TRIGGERED", "yellow")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_ALTMAN["grey"]

    def test_safe(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, 3.5, "CLEAR", "")
        template = _select_template(templates, "CLEAR", "")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_ALTMAN["safe"]

    def test_none_returns_empty(self) -> None:
        """None value + SKIPPED status -> empty string (no do_context)."""
        templates = _load_signal_do_context(self.SIGNAL_ID)
        template = _select_template(templates, "SKIPPED", "")
        assert template == ""


# ---------------------------------------------------------------------------
# Beneish M-Score golden parity tests
# ---------------------------------------------------------------------------


class TestBeneishDoContext:
    """YAML do_context for FIN.ACCT.earnings_manipulation matches Python golden."""

    SIGNAL_ID = "FIN.ACCT.earnings_manipulation"

    def test_safe(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, -2.5, "CLEAR", "")
        template = _select_template(templates, "CLEAR", "")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_BENEISH["safe"]

    def test_grey(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, -2.0, "TRIGGERED", "yellow")
        template = _select_template(templates, "TRIGGERED", "yellow")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_BENEISH["grey"]

    def test_danger(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, -1.5, "TRIGGERED", "red")
        template = _select_template(templates, "TRIGGERED", "red")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_BENEISH["danger"]

    def test_none_returns_empty(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        template = _select_template(templates, "SKIPPED", "")
        assert template == ""


class TestBeneishCompositeDoContext:
    """YAML do_context for FIN.FORENSIC.m_score_composite also matches."""

    SIGNAL_ID = "FIN.FORENSIC.m_score_composite"

    def test_safe(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, -2.5, "CLEAR", "")
        template = _select_template(templates, "CLEAR", "")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_BENEISH["safe"]


# ---------------------------------------------------------------------------
# Piotroski F-Score golden parity tests
# ---------------------------------------------------------------------------


class TestPiotroskiDoContext:
    """YAML do_context for FIN.FORENSIC.dechow_f_score matches Python golden."""

    SIGNAL_ID = "FIN.FORENSIC.dechow_f_score"

    def test_strong(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, 8, "CLEAR", "")
        template = _select_template(templates, "CLEAR", "")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_PIOTROSKI["strong_8"]

    def test_weak(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, 2, "TRIGGERED", "red")
        template = _select_template(templates, "TRIGGERED", "red")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_PIOTROSKI["weak_2"]

    def test_moderate(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        result = _make_result(self.SIGNAL_ID, 5, "TRIGGERED", "yellow")
        template = _select_template(templates, "TRIGGERED", "yellow")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_PIOTROSKI["moderate_5"]

    def test_none_returns_empty(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        template = _select_template(templates, "SKIPPED", "")
        assert template == ""


# ---------------------------------------------------------------------------
# Ohlson O-Score golden parity tests (YAML do_context)
# ---------------------------------------------------------------------------


class TestOhlsonYaml:
    """YAML do_context for FIN.ACCT.ohlson_o_score matches Python golden."""

    SIGNAL_ID = "FIN.ACCT.ohlson_o_score"

    def test_distress(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, 0.7, "TRIGGERED", "red")
        template = _select_template(templates, "TRIGGERED", "red")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_OHLSON["distress"]

    def test_safe(self) -> None:
        templates = _load_signal_do_context(self.SIGNAL_ID)
        assert templates, f"No do_context templates found for {self.SIGNAL_ID}"
        result = _make_result(self.SIGNAL_ID, 0.3, "CLEAR", "")
        template = _select_template(templates, "CLEAR", "")
        rendered = render_do_context(template, result)
        assert rendered == GOLDEN_OHLSON["safe"]

    def test_none_returns_empty(self) -> None:
        """None value + SKIPPED status -> empty string (no do_context)."""
        templates = _load_signal_do_context(self.SIGNAL_ID)
        template = _select_template(templates, "SKIPPED", "")
        assert template == ""


# ---------------------------------------------------------------------------
# SignalResultView do_context field tests
# ---------------------------------------------------------------------------


class TestSignalResultViewDoContext:
    """SignalResultView has do_context field and get_signal_result populates it."""

    def test_view_has_do_context_field(self) -> None:
        """SignalResultView dataclass includes do_context attribute."""
        import dataclasses
        field_names = [f.name for f in dataclasses.fields(SignalResultView)]
        assert "do_context" in field_names

    def test_get_signal_result_populates_do_context(self) -> None:
        """get_signal_result extracts do_context from raw dict."""
        raw = {
            "TEST.SIGNAL": {
                "status": "TRIGGERED",
                "value": 1.5,
                "threshold_level": "red",
                "do_context": "Test D&O commentary string",
            }
        }
        view = get_signal_result(raw, "TEST.SIGNAL")
        assert view is not None
        assert view.do_context == "Test D&O commentary string"

    def test_get_signal_result_empty_do_context_default(self) -> None:
        """Missing do_context in raw dict defaults to empty string."""
        raw = {
            "TEST.SIGNAL": {
                "status": "CLEAR",
                "value": 3.0,
                "threshold_level": "",
            }
        }
        view = get_signal_result(raw, "TEST.SIGNAL")
        assert view is not None
        assert view.do_context == ""
