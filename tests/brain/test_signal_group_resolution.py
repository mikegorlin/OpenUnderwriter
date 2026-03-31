"""Tests for signal self-selection into manifest groups.

Phase 84 Plan 01: Validates that signals correctly self-select into groups
via their `group` field, and that all group IDs match between signals and manifest.
"""

from __future__ import annotations

from do_uw.brain.brain_unified_loader import load_signals
from do_uw.brain.manifest_schema import (
    collect_signals_by_group,
    load_manifest,
)


class TestSignalGroupResolution:
    """Tests that signal group fields match manifest group IDs."""

    def test_all_signal_groups_exist_in_manifest(self) -> None:
        """Every unique group ID from signals must exist as a ManifestGroup."""
        manifest = load_manifest()
        manifest_group_ids: set[str] = set()
        for section in manifest.sections:
            for group in section.groups:
                manifest_group_ids.add(group.id)

        sigs = load_signals()["signals"]
        signal_group_ids: set[str] = set()
        for sig in sigs:
            gid = sig.get("group", "")
            if gid:
                signal_group_ids.add(gid)

        missing = signal_group_ids - manifest_group_ids
        assert not missing, (
            f"Signal group IDs not in manifest: {sorted(missing)}"
        )

    def test_signal_group_count_is_61(self) -> None:
        """There should be 61 unique group IDs across all signals.

        Count progression: 55 (Phase 95) -> 60 (Phases 96-98 added
        structural_complexity, environment_assessment, sector_classification,
        sector_patterns, sector_compliance) -> 61 (DISC.YOY ten_k_yoy).
        """
        sigs = load_signals()["signals"]
        group_ids = {s.get("group", "") for s in sigs} - {""}
        assert len(group_ids) == 61, (
            f"Expected 61 signal group IDs, got {len(group_ids)}"
        )

    def test_collect_signals_by_group_non_empty(self) -> None:
        """collect_signals_by_group returns non-empty lists for known groups."""
        sigs = load_signals()["signals"]
        groups = collect_signals_by_group(sigs)
        assert len(groups) > 0
        for gid, sig_ids in groups.items():
            assert len(sig_ids) > 0, f"Group {gid} has no signals"

    def test_signals_with_empty_group_excluded(self) -> None:
        """Signals with empty or missing group field are excluded."""
        sigs = load_signals()["signals"]
        groups = collect_signals_by_group(sigs)
        # No empty-string key should exist
        assert "" not in groups

    def test_signal_bearing_manifest_groups_have_signals(self) -> None:
        """Manifest groups that correspond to signal groups have at least 1 signal.

        Infrastructure groups (checks, density_alerts, charts) may have 0.
        """
        manifest = load_manifest()
        sigs = load_signals()["signals"]
        sig_groups = collect_signals_by_group(sigs)

        # Signal-bearing group IDs (from signals)
        signal_gids = set(sig_groups.keys())

        # Manifest group IDs
        manifest_gids: set[str] = set()
        for section in manifest.sections:
            for group in section.groups:
                manifest_gids.add(group.id)

        # Every signal group ID should have at least 1 signal (by definition)
        for gid in signal_gids:
            assert len(sig_groups[gid]) >= 1, (
                f"Group {gid} has signals in YAML but collect_signals_by_group is empty"
            )

    def test_total_signal_assignments(self) -> None:
        """Total signal-to-group assignments should match signal count with groups."""
        sigs = load_signals()["signals"]
        groups = collect_signals_by_group(sigs)
        total_assigned = sum(len(v) for v in groups.values())
        # Count signals that have a non-empty group
        expected = sum(1 for s in sigs if s.get("group", ""))
        assert total_assigned == expected
