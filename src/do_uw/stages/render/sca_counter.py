"""Canonical SCA counter -- single source of truth for active genuine SCA counts.

All code that needs to count or list active genuine securities class actions
MUST use these functions. Do NOT implement inline SCA filtering elsewhere.

Active = status in (ACTIVE, PENDING, N/A, None, "") -- conservative: unknown = active
Genuine = NOT filtered by _is_regulatory_not_sca (excludes FCPA, environmental, etc.)
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

# Statuses that indicate an SCA is active or unknown (conservative underwriting)
_ACTIVE_STATUSES = {"ACTIVE", "PENDING", "N/A", ""}


def get_active_genuine_scas(state: AnalysisState) -> list[Any]:
    """Return list of active genuine securities class actions.

    Single source of truth for SCA filtering across the entire codebase.

    Primary: state.extracted.litigation.securities_class_actions (pipeline)
    Supplementary: state.acquired_data.litigation_data.supabase_cases (Supabase)
    Supabase cases are added only if not already present in extracted SCAs.

    Active = status is None (unknown = assume active) or status string
    (after .value if enum) uppercased is in {ACTIVE, PENDING, N/A, ""}.
    Genuine = NOT filtered by _is_regulatory_not_sca.
    """
    result: list[Any] = []

    # Primary: extracted SCAs from pipeline
    extracted = getattr(state, "extracted", None)
    litigation = getattr(extracted, "litigation", None) if extracted else None
    scas = getattr(litigation, "securities_class_actions", None) if litigation else []
    if scas:
        for sca in scas:
            if _is_regulatory_not_sca(sca):
                continue
            status_obj = getattr(sca, "status", None)
            if status_obj is None:
                result.append(sca)
                continue
            status_str = (
                status_obj.value if hasattr(status_obj, "value") else str(status_obj)
            )
            status_upper = str(status_str).upper() if status_str is not None else ""
            if status_upper in _ACTIVE_STATUSES:
                result.append(sca)

    # Supplementary: Supabase SCA cases (MEDIUM confidence)
    # Add active Supabase cases not already captured by extraction.
    # Deduplicate by class period — multiple filings with the same class
    # period are the same lawsuit (initial complaint + consolidated/amended).
    supabase_cases = _get_supabase_active_cases(state)
    if supabase_cases:
        existing_dates: set[str] = set()
        existing_class_periods: set[str] = set()
        for sca in result:
            fd = getattr(sca, "filing_date", None) or getattr(sca, "date_filed", None)
            if fd:
                existing_dates.add(str(fd)[:10])
            cp_start = getattr(sca, "class_period_start", None)
            cp_end = getattr(sca, "class_period_end", None)
            if cp_start and cp_end:
                existing_class_periods.add(f"{cp_start}|{cp_end}")

        # Deduplicate Supabase cases against each other too — same class
        # period = same case, keep the most recent filing
        seen_class_periods: set[str] = set(existing_class_periods)
        for case in sorted(
            supabase_cases,
            key=lambda c: c.get("filing_date", ""),
            reverse=True,
        ):
            fd = str(case.get("filing_date", ""))[:10]
            cp_start = str(case.get("class_period_start", "") or "")
            cp_end = str(case.get("class_period_end", "") or "")
            cp_key = f"{cp_start}|{cp_end}" if cp_start and cp_end else ""

            # Skip if same class period already seen (same lawsuit)
            if cp_key and cp_key in seen_class_periods:
                continue
            # Skip if same filing date already in extracted
            if fd and fd in existing_dates:
                continue

            result.append(case)
            existing_dates.add(fd)
            if cp_key:
                seen_class_periods.add(cp_key)

    return result


def _get_supabase_active_cases(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract active SCA cases from Supabase data in acquired_data."""
    acquired = getattr(state, "acquired_data", None)
    if not acquired:
        return []
    lit_data = getattr(acquired, "litigation_data", None)
    if not lit_data:
        return []
    cases: list[dict[str, Any]] = []
    if isinstance(lit_data, dict):
        cases = lit_data.get("supabase_cases", [])
    else:
        cases = getattr(lit_data, "supabase_cases", []) or []

    active_statuses = {"ACTIVE", "PENDING", "OPEN", "FILED", "ONGOING"}
    return [
        c for c in cases
        if isinstance(c, dict)
        and str(c.get("case_status", "")).upper() in active_statuses
    ]


def count_active_genuine_scas(state: AnalysisState) -> int:
    """Return count of active genuine securities class actions.

    Convenience wrapper around get_active_genuine_scas().
    """
    return len(get_active_genuine_scas(state))


__all__ = ["get_active_genuine_scas", "count_active_genuine_scas"]
