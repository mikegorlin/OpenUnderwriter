"""CI tests for signal group coverage (WIRE-01).

Every signal in brain/signals/ must have a non-empty `group` field that
maps to a valid manifest group ID. Phase 110 mechanism signals (absence,
conjunction, contextual) are specifically regression-guarded.
"""

from pathlib import Path

import yaml


_PROJECT_ROOT = Path(__file__).parent.parent.parent
SIGNALS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals"
MANIFEST_PATH = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "output_manifest.yaml"


def _load_all_signals() -> list[dict]:
    """Load all signal entries from brain YAML files."""
    signals: list[dict] = []
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            signals.extend(data)
        elif isinstance(data, dict):
            signals.append(data)
    return signals


def _load_manifest_group_ids() -> set[str]:
    """Load all group IDs from the output manifest."""
    data = yaml.safe_load(MANIFEST_PATH.read_text())
    group_ids: set[str] = set()
    for section in data.get("sections", []):
        for group in section.get("groups", []):
            group_ids.add(group["id"])
    return group_ids


class TestSignalGroupCoverage:
    """Every signal must have a group field mapped to a manifest group."""

    def test_all_signals_have_group(self) -> None:
        """All 562 signals must have a non-empty group field."""
        signals = _load_all_signals()
        assert len(signals) >= 562, f"Expected 562+ signals, got {len(signals)}"

        missing: list[str] = []
        for sig in signals:
            if not isinstance(sig, dict):
                continue
            group = sig.get("group", "")
            if not group:
                missing.append(sig.get("id", "UNKNOWN"))

        assert not missing, (
            f"{len(missing)} signal(s) have no group field: "
            f"{missing[:10]}{'...' if len(missing) > 10 else ''}"
        )

    def test_all_signal_groups_exist_in_manifest(self) -> None:
        """Every signal's group value must match a manifest group ID."""
        signals = _load_all_signals()
        manifest_groups = _load_manifest_group_ids()

        invalid: list[tuple[str, str]] = []
        for sig in signals:
            if not isinstance(sig, dict):
                continue
            group = sig.get("group", "")
            if group and group not in manifest_groups:
                invalid.append((sig.get("id", "UNKNOWN"), group))

        assert not invalid, (
            f"{len(invalid)} signal(s) reference non-existent manifest groups: "
            f"{invalid[:10]}{'...' if len(invalid) > 10 else ''}"
        )

    def test_phase_110_mechanism_signals_have_groups(self) -> None:
        """Regression guard: all 48 Phase 110 mechanism signals have groups."""
        signals = _load_all_signals()
        manifest_groups = _load_manifest_group_ids()

        # Phase 110 signals live in absence/, conjunction/, contextual/ dirs
        mechanism_prefixes = ("ABS.", "CONJ.", "CTX.")
        mechanism_signals = [
            s for s in signals
            if isinstance(s, dict) and any(
                s.get("id", "").startswith(p) for p in mechanism_prefixes
            )
        ]

        assert len(mechanism_signals) == 48, (
            f"Expected 48 mechanism signals, got {len(mechanism_signals)}"
        )

        for sig in mechanism_signals:
            group = sig.get("group", "")
            assert group, f"{sig['id']} has no group field"
            assert group in manifest_groups, (
                f"{sig['id']} group '{group}' not in manifest"
            )
