"""CI contract test: signal portability gate.

Validates that all brain signals with acquisition blocks (v6-era signals)
also have evaluation and presentation blocks. This enforces the brain
portability principle: signals must be self-contained with all metadata
needed for another system to process them.

Phase 100-03: CI contract tests for brain portability.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Signal YAML files live under src/do_uw/brain/signals/
_SIGNALS_DIR = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "brain" / "signals"


def _load_all_signals() -> list[tuple[str, str, dict]]:
    """Load all signals from all YAML files.

    Returns list of (file_relative_path, signal_id, signal_dict).
    """
    signals: list[tuple[str, str, dict]] = []
    for yaml_path in sorted(_SIGNALS_DIR.rglob("*.yaml")):
        rel = yaml_path.relative_to(_SIGNALS_DIR)
        data = yaml.safe_load(yaml_path.read_text())
        if not isinstance(data, list):
            continue
        for entry in data:
            if not isinstance(entry, dict):
                continue
            sig_id = entry.get("id", f"unknown-in-{rel}")
            signals.append((str(rel), sig_id, entry))
    return signals


def test_v6_signals_have_all_portability_blocks() -> None:
    """Every signal with an acquisition block must also have evaluation and presentation.

    The v6 brain portability principle requires signals to be self-contained:
    acquisition (how to get data), evaluation (how to assess), and presentation
    (how to display). Signals that declare acquisition but lack the other two
    blocks are incomplete and would break portability to another rendering system.

    Note: Legacy signals (pre-v6) without acquisition blocks are exempt -- they
    use the older data_strategy/threshold/display pattern.
    """
    signals = _load_all_signals()
    assert len(signals) > 0, "No signals found -- check _SIGNALS_DIR path"

    failures: list[str] = []
    checked = 0

    for rel_path, sig_id, sig in signals:
        # Only check signals that have an acquisition block (v6-era)
        if sig.get("acquisition") is None:
            continue

        # BASE.* signals are foundational data-fetching signals that acquire
        # raw data (filings, XBRL, market data) for other signals to consume.
        # They have acquisition blocks but intentionally lack evaluation and
        # presentation blocks -- they are inputs, not display signals.
        if sig_id.startswith("BASE."):
            continue

        checked += 1
        missing: list[str] = []

        if sig.get("evaluation") is None:
            missing.append("evaluation")
        if sig.get("presentation") is None:
            missing.append("presentation")

        if missing:
            failures.append(
                f"  {sig_id} ({rel_path}): missing {', '.join(missing)}"
            )

    assert checked > 0, "No signals with acquisition blocks found -- expected v6 signals"

    assert not failures, (
        f"{len(failures)} signal(s) have acquisition but missing required blocks:\n"
        + "\n".join(failures)
    )


def test_signal_yaml_files_are_valid() -> None:
    """All signal YAML files must parse without errors and contain a list."""
    for yaml_path in sorted(_SIGNALS_DIR.rglob("*.yaml")):
        rel = yaml_path.relative_to(_SIGNALS_DIR)
        try:
            data = yaml.safe_load(yaml_path.read_text())
        except yaml.YAMLError as e:
            raise AssertionError(f"YAML parse error in {rel}: {e}") from e

        assert isinstance(data, list), (
            f"Signal file {rel} must contain a YAML list, got {type(data).__name__}"
        )
        assert len(data) > 0, f"Signal file {rel} is empty (no signals defined)"


def test_signal_count_minimum() -> None:
    """Guard against accidentally losing signals during refactoring.

    As of v6.0 there are 508 signals across 51 YAML files.
    """
    signals = _load_all_signals()
    # Allow some variance but catch catastrophic loss
    assert len(signals) >= 400, (
        f"Expected at least 400 signals, found {len(signals)}. "
        "Possible signal loss during refactoring."
    )
