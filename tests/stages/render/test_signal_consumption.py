"""BUILD-07 verification: rewritten builders must consume signal results.

Verifies that each builder in SIGNAL_CONSUMING_BUILDERS imports and uses
at least one function from _signal_consumer or _signal_fallback.
Grows as plans 02-04 add more builders.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_BUILDERS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "do_uw"
    / "stages"
    / "render"
    / "context_builders"
)

# Signal consumption functions to look for
_SIGNAL_FUNCTIONS = {
    "safe_get_result",
    "safe_get_value",
    "safe_get_level",
    "safe_get_signals_by_prefix",
    "get_signal_result",
    "get_signals_by_prefix",
    "safe_get_status",
    "signal_to_display_level",
}

# Builders that have been rewritten to consume signals -- grows over plans
SIGNAL_CONSUMING_BUILDERS: list[str] = [
    "company_profile.py",
    "company_exec_summary.py",
    "company_business_model.py",
    "company_environment.py",
    "company_operations.py",
    "company_events.py",
    "governance.py",
    "governance_evaluative.py",
    "litigation.py",
    "litigation_evaluative.py",
    "financials_evaluative.py",
    "market_evaluative.py",
    "analysis_evaluative.py",
    "narrative_evaluative.py",
]


# Primary builders that delegate signal consumption to companion *_evaluative.py modules.
# These builders don't import signal functions directly -- they delegate to companions.
DELEGATION_BUILDERS: dict[str, list[str]] = {
    "financials.py": ["financials_evaluative.py"],
    "market.py": ["market_evaluative.py"],
    "analysis.py": ["analysis_evaluative.py"],
    "scoring.py": ["scoring_evaluative.py"],
    "narrative.py": ["narrative_evaluative.py"],
}

# scoring_evaluative.py is exempted from signal function import requirement
# because it extracts from post-signal computed artifacts (see module docstring).
_DELEGATION_SIGNAL_EXEMPT = {"scoring_evaluative.py"}


def _get_builder_files() -> list[tuple[str, Path]]:
    """Get list of (name, path) tuples for signal-consuming builders that exist."""
    result = []
    for name in SIGNAL_CONSUMING_BUILDERS:
        path = _BUILDERS_DIR / name
        if path.exists():
            result.append((name, path))
    return result


@pytest.mark.parametrize(
    "name,builder_path",
    _get_builder_files(),
    ids=lambda x: x if isinstance(x, str) else x.name,
)
def test_builder_imports_signal_functions(name: str, builder_path: Path) -> None:
    """Each rewritten builder must import signal consumption functions."""
    source = builder_path.read_text()
    found = any(fn in source for fn in _SIGNAL_FUNCTIONS)
    assert found, (
        f"{name} does not import any signal consumption function from "
        f"_signal_consumer or _signal_fallback. Expected at least one of: "
        f"{', '.join(sorted(_SIGNAL_FUNCTIONS))}"
    )


def _get_delegation_pairs() -> list[tuple[str, list[str]]]:
    """Get delegation builder pairs where files exist."""
    result = []
    for primary, companions in DELEGATION_BUILDERS.items():
        if (_BUILDERS_DIR / primary).exists():
            result.append((primary, companions))
    return result


def _get_delegation_companions() -> list[tuple[str, str]]:
    """Get (primary, companion) pairs for companion signal validation."""
    result = []
    for primary, companions in DELEGATION_BUILDERS.items():
        for companion in companions:
            if (_BUILDERS_DIR / companion).exists():
                result.append((primary, companion))
    return result


@pytest.mark.parametrize(
    "primary,companions",
    _get_delegation_pairs(),
    ids=lambda x: x if isinstance(x, str) else str(x),
)
def test_delegation_builder_imports_evaluative(
    primary: str, companions: list[str],
) -> None:
    """Primary builders must import from their companion *_evaluative.py modules."""
    source = (_BUILDERS_DIR / primary).read_text()
    for companion in companions:
        module_name = companion.removesuffix(".py")
        assert module_name in source, (
            f"{primary} does not import from companion {companion}. "
            f"Expected import from do_uw.stages.render.context_builders.{module_name}"
        )


@pytest.mark.parametrize(
    "primary,companion",
    _get_delegation_companions(),
    ids=lambda x: x if isinstance(x, str) else str(x),
)
def test_delegation_companion_consumes_signals(
    primary: str, companion: str,
) -> None:
    """Companion *_evaluative.py modules must import signal functions (with exemptions)."""
    if companion in _DELEGATION_SIGNAL_EXEMPT:
        pytest.skip(
            f"{companion} is exempt -- extracts from post-signal computed artifacts"
        )
    source = (_BUILDERS_DIR / companion).read_text()
    found = any(fn in source for fn in _SIGNAL_FUNCTIONS)
    assert found, (
        f"{companion} (companion of {primary}) does not import any signal function. "
        f"Expected at least one of: {', '.join(sorted(_SIGNAL_FUNCTIONS))}"
    )
