"""CI tests ensuring foundational signals in brain/signals/base/ cover the Tier 1 manifest.

Validates:
- All Tier 1 data sources have a corresponding foundational signal
- Every foundational signal has type: foundational and an acquisition block
- No duplicate signal IDs across base/ files
"""

from pathlib import Path

import pytest
import yaml

# Use __file__ for robust path resolution regardless of CWD
_PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_SIGNALS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals" / "base"


def _load_all_foundational_signals() -> list[dict]:
    """Load all signals from brain/signals/base/*.yaml."""
    signals: list[dict] = []
    for yaml_file in sorted(BASE_SIGNALS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            for entry in data:
                entry["_source_file"] = yaml_file.name
                signals.append(entry)
    return signals


class TestFoundationalCoverage:
    """Ensure foundational signals cover all Tier 1 data sources."""

    def test_all_tier1_sources_have_foundational_signal(self) -> None:
        """There must be at least 26 foundational signals (25 existing + 1 peer)."""
        signals = _load_all_foundational_signals()
        assert len(signals) >= 26, (
            f"Expected >= 26 foundational signals, found {len(signals)}. "
            f"IDs: {[s['id'] for s in signals]}"
        )

    def test_foundational_signals_have_signal_class(self) -> None:
        """Every signal in base/ must have signal_class: foundational."""
        signals = _load_all_foundational_signals()
        for signal in signals:
            assert signal.get("signal_class") == "foundational", (
                f"Signal {signal['id']} in {signal['_source_file']} "
                f"has signal_class={signal.get('signal_class')!r}, expected 'foundational'"
            )

    def test_no_duplicate_foundational_signal_ids(self) -> None:
        """No duplicate signal IDs across base/ files."""
        signals = _load_all_foundational_signals()
        seen: dict[str, str] = {}
        duplicates: list[str] = []
        for signal in signals:
            sid = signal["id"]
            source = signal["_source_file"]
            if sid in seen:
                duplicates.append(f"{sid} in {source} (first seen in {seen[sid]})")
            else:
                seen[sid] = source
        assert not duplicates, f"Duplicate foundational signal IDs: {duplicates}"

    def test_all_foundational_signals_have_acquisition_block(self) -> None:
        """Every foundational signal must have an acquisition section with fields."""
        signals = _load_all_foundational_signals()
        missing: list[str] = []
        for signal in signals:
            acq = signal.get("acquisition")
            if not acq:
                missing.append(f"{signal['id']}: no acquisition block")
                continue
            sources = acq.get("sources", [])
            if not sources:
                missing.append(f"{signal['id']}: acquisition has no sources")
                continue
            for src in sources:
                if not src.get("fields"):
                    missing.append(
                        f"{signal['id']}: source type={src.get('type')} has no fields"
                    )
        assert not missing, f"Foundational signals missing acquisition fields: {missing}"

    def test_expected_categories_covered(self) -> None:
        """Verify all expected Tier 1 categories have at least one signal."""
        signals = _load_all_foundational_signals()
        id_prefixes = {s["id"].split(".")[1] for s in signals}
        expected = {"FILING", "MARKET", "XBRL", "FORENSIC", "LIT", "NEWS", "PEER"}
        missing = expected - id_prefixes
        assert not missing, f"Missing foundational signal categories: {missing}"

    def test_all_signals_have_required_fields(self) -> None:
        """Every foundational signal must have id, name, signal_class, description."""
        signals = _load_all_foundational_signals()
        required = {"id", "name", "signal_class", "description"}
        for signal in signals:
            missing = required - set(signal.keys())
            assert not missing, (
                f"Signal {signal.get('id', '?')} in {signal['_source_file']} "
                f"missing required fields: {missing}"
            )

    def test_peer_frames_signal_exists(self) -> None:
        """BASE.PEER.frames foundational signal must exist for Frames API."""
        signals = _load_all_foundational_signals()
        ids = [s["id"] for s in signals]
        assert "BASE.PEER.frames" in ids, (
            f"BASE.PEER.frames not found in foundational signals. "
            f"Found: {ids}"
        )
