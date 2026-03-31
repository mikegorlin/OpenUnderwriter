"""Narrative builders and helpers for Section 1 Executive Summary.

Narrative construction logic has been relocated to
do_uw.stages.benchmark.narrative_helpers (analytical logic belongs in
benchmark/, not render/). This module re-exports those functions for
backward compatibility.

Helper functions for safe data extraction remain here (presentation-layer
utilities used by sect1_executive, sect1_findings, etc.).
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float

# Re-export analytical functions from their canonical location in benchmark/
from do_uw.stages.benchmark.narrative_helpers import (
    build_claim_narrative as build_claim_narrative,
)
from do_uw.stages.benchmark.narrative_helpers import (
    build_risk_narrative as build_risk_narrative,
)
from do_uw.stages.benchmark.narrative_helpers import (
    build_thesis_narrative as build_thesis_narrative,
)
from do_uw.stages.benchmark.narrative_helpers import (
    market_cap_decile as market_cap_decile,
)
from do_uw.stages.benchmark.narrative_helpers import (
    safe_distress as safe_distress,
)
from do_uw.stages.benchmark.narrative_helpers import (
    safe_leverage_ratio as safe_leverage_ratio,
)

# ---------------------------------------------------------------------------
# Presentation-layer helpers (remain here -- used only by render/)
# ---------------------------------------------------------------------------


def safe_auditor(state: AnalysisState) -> str | None:
    """Safely extract auditor name."""
    ext: Any = state.extracted
    if ext is None:
        return None
    fin: Any = ext.financials
    if fin is None:
        return None
    audit: Any = fin.audit
    if audit is None:
        return None
    an: Any = audit.auditor_name
    if an is None:
        return None
    val: Any = getattr(an, "value", None)
    return str(val) if val else None


def safe_auditor_tenure(state: AnalysisState) -> int | None:
    """Safely extract auditor tenure."""
    ext: Any = state.extracted
    if ext is None:
        return None
    fin: Any = ext.financials
    if fin is None:
        return None
    audit: Any = fin.audit
    if audit is None:
        return None
    ty: Any = audit.tenure_years
    if ty is None:
        return None
    val: Any = getattr(ty, "value", None)
    return int(val) if val else None


def safe_governance_field(
    state: AnalysisState, field: str
) -> float | None:
    """Safely extract a governance metric."""
    ext: Any = state.extracted
    if ext is None:
        return None
    gov: Any = ext.governance
    if gov is None:
        return None
    board: Any = gov.board
    if board is None:
        return None
    sv: Any = getattr(board, field, None)
    if sv is None:
        return None
    val: Any = getattr(sv, "value", None)
    if val is not None:
        return safe_float(val)
    return None


def safe_short_interest(state: AnalysisState) -> float | None:
    """Safely extract short interest percentage."""
    ext: Any = state.extracted
    if ext is None:
        return None
    mkt: Any = ext.market
    if mkt is None:
        return None
    si: Any = mkt.short_interest
    if si is None:
        return None
    spf: Any = si.short_pct_float
    if spf is None:
        return None
    val: Any = getattr(spf, "value", None)
    if val is not None:
        return safe_float(val)
    return None


__all__ = [
    "build_claim_narrative",
    "build_risk_narrative",
    "build_thesis_narrative",
    "market_cap_decile",
    "safe_auditor",
    "safe_auditor_tenure",
    "safe_distress",
    "safe_governance_field",
    "safe_leverage_ratio",
    "safe_short_interest",
]
