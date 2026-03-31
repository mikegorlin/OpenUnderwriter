"""CI tests for manifest governance (WIRE-02).

Every manifest group must either have signal coverage (at least one signal
with `group: <group_id>`) or be explicitly marked `display_only: true`.
This prevents ungoverned groups from silently rendering without signal backing.
"""

from pathlib import Path

import yaml


_PROJECT_ROOT = Path(__file__).parent.parent.parent
SIGNALS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals"
MANIFEST_PATH = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "output_manifest.yaml"


def _load_signal_groups() -> set[str]:
    """Collect all unique group values from signal YAML files."""
    groups: set[str] = set()
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            sigs = data
        elif isinstance(data, dict):
            sigs = [data]
        else:
            continue
        for sig in sigs:
            if isinstance(sig, dict):
                group = sig.get("group", "")
                if group:
                    groups.add(group)
    return groups


def _load_manifest_groups() -> list[dict]:
    """Load all manifest groups with their metadata."""
    data = yaml.safe_load(MANIFEST_PATH.read_text())
    groups: list[dict] = []
    for section in data.get("sections", []):
        for group in section.get("groups", []):
            group["_section_id"] = section["id"]
            groups.append(group)
    return groups


class TestManifestGovernance:
    """Manifest groups must be governed by signals or marked display_only."""

    def test_ungoverned_groups_marked_display_only(self) -> None:
        """Every manifest group without signal coverage must be display_only."""
        signal_groups = _load_signal_groups()
        manifest_groups = _load_manifest_groups()

        violations: list[str] = []
        for mg in manifest_groups:
            group_id = mg["id"]
            has_signals = group_id in signal_groups
            is_display_only = mg.get("display_only", False)

            if not has_signals and not is_display_only:
                violations.append(
                    f"{mg['_section_id']}/{group_id}: "
                    f"no signal coverage and not display_only"
                )

        assert not violations, (
            f"{len(violations)} manifest group(s) have no signal coverage "
            f"and are not marked display_only:\n  "
            + "\n  ".join(violations)
        )

    def test_display_only_groups_are_legitimate(self) -> None:
        """display_only groups must genuinely have no signal coverage.

        Prevents accidentally marking a governed group as display_only,
        which would hide that it has signal backing.
        """
        signal_groups = _load_signal_groups()
        manifest_groups = _load_manifest_groups()

        false_display_only: list[str] = []
        for mg in manifest_groups:
            group_id = mg["id"]
            is_display_only = mg.get("display_only", False)
            has_signals = group_id in signal_groups

            if is_display_only and has_signals:
                false_display_only.append(
                    f"{mg['_section_id']}/{group_id}: "
                    f"marked display_only but has signal coverage"
                )

        assert not false_display_only, (
            f"{len(false_display_only)} group(s) marked display_only "
            f"but actually have signal coverage (remove display_only):\n  "
            + "\n  ".join(false_display_only)
        )
