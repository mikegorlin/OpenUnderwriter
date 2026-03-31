"""CI contract tests for the brain signal system.

These tests validate that every ACTIVE signal in the brain YAML meets the
minimum contract requirements. Failing these tests means a signal is incomplete
and the build should not pass.

V3 contract test stubs (Phase 82) define the migration target for Plan 82-02.
Tests marked with skip require v3 migration to pass.
"""

import yaml
from pathlib import Path

import pytest

# Use __file__ for robust path resolution regardless of CWD
_PROJECT_ROOT = Path(__file__).parent.parent.parent
SIGNALS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals"
FACETS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "sections"

# Maximum allowed SKIPPED count (CI gate)
# Target: ~34 (down from ~68 pre-Phase 49)
# Set conservatively; tighten as signals are fixed
MAX_SKIPPED_THRESHOLD = 45


def _load_all_signals() -> list[dict]:
    """Load all signal entries from brain YAML files."""
    signals: list[dict] = []
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            signals.extend(data)
    return signals


def _active_signals() -> list[dict]:
    """Return only ACTIVE signals (not INACTIVE or DEPRECATED)."""
    return [
        s
        for s in _load_all_signals()
        if s.get("lifecycle_state", "ACTIVE") not in ("INACTIVE", "DEPRECATED")
    ]


def _active_signals_validated() -> list[dict]:
    """Return ACTIVE signals loaded through BrainLoader (with v3 inference).

    Uses BrainLoader so signal_class is inferred from v2 type/work_type fields.
    """
    from do_uw.brain.brain_unified_loader import BrainLoader, _reset_cache

    _reset_cache()
    loader = BrainLoader()
    all_sigs = loader.load_signals()["signals"]
    return [
        s
        for s in all_sigs
        if s.get("lifecycle_state", "ACTIVE") not in ("INACTIVE", "DEPRECATED")
    ]


def _is_foundational(sig: dict) -> bool:
    """Check if signal is foundational (v3: signal_class only)."""
    return sig.get("signal_class") == "foundational"


class TestSignalDataRoute:
    """Every ACTIVE signal must have a data route."""

    def test_all_active_signals_have_data_strategy(self) -> None:
        for sig in _active_signals():
            # Foundational signals use acquisition blocks, not data_strategy
            if _is_foundational(sig):
                assert sig.get("acquisition"), (
                    f"{sig['id']} foundational signal missing acquisition block"
                )
                continue
            # Inference signals (conjunction, absence, contextual) derive data
            # from other signals via evaluation rules, not data_strategy
            if sig.get("signal_class") == "inference":
                continue
            ds = sig.get("data_strategy", {})
            # data_strategy should exist and have content, OR data_locations should exist
            has_route = bool(ds) or bool(sig.get("data_locations"))
            assert has_route, f"{sig['id']} missing data_strategy/data_locations"


class TestSignalThreshold:
    """Every ACTIVE evaluable signal must have a threshold."""

    def test_all_active_signals_have_threshold(self) -> None:
        for sig in _active_signals():
            if sig.get("work_type") == "extract":
                continue  # Extract-only signals don't need thresholds
            if _is_foundational(sig):
                continue  # Foundational signals are not evaluated
            threshold = sig.get("threshold", {})
            assert threshold.get("type"), f"{sig['id']} missing threshold.type"


class TestSignalSectionMapping:
    """Every ACTIVE signal must have v6_subsection_ids."""

    def test_all_active_signals_have_v6_subsection(self) -> None:
        for sig in _active_signals():
            if _is_foundational(sig):
                continue  # Foundational signals are manifest entries, not evaluated
            # Inference signals (conjunction, absence, contextual) use group
            # field for render targeting, not v6_subsection_ids
            if sig.get("signal_class") == "inference":
                continue
            assert "v6_subsection_ids" in sig, (
                f"{sig['id']} missing v6_subsection_ids"
            )


class TestSignalScoringLinkage:
    """Every ACTIVE evaluable signal must have factor or peril mapping."""

    def test_all_active_signals_have_scoring_linkage(self) -> None:
        for sig in _active_signals():
            if sig.get("work_type") == "extract":
                continue  # Display-only signals don't need scoring
            if _is_foundational(sig):
                continue  # Foundational signals are manifest entries, not scored
            # Inference signals (conjunction, absence, contextual) contribute
            # through their component signals' scoring, not directly
            if sig.get("signal_class") == "inference":
                continue
            has_factor = bool(sig.get("factors"))
            has_peril = bool(sig.get("peril_ids"))
            has_chain = bool(sig.get("chain_roles"))
            assert has_factor or has_peril or has_chain, (
                f"{sig['id']} has no scoring linkage (factors, peril_ids, or chain_roles)"
            )


class TestSignalDisplaySpec:
    """Every ACTIVE non-foundational signal must have display.value_format."""

    def test_all_active_signals_have_display(self) -> None:
        for sig in _active_signals():
            if _is_foundational(sig):
                continue  # Foundational signals are manifest entries, not displayed
            # Inference signals (conjunction, absence, contextual) display
            # through their evaluation rules, not display.value_format
            if sig.get("signal_class") == "inference":
                continue
            display = sig.get("display", {})
            assert display.get("value_format"), (
                f"{sig['id']} missing display.value_format"
            )


class TestSkippedCountThreshold:
    """SKIPPED signal count must remain below threshold.

    This is a static check on lifecycle_state in YAML, not a runtime check.
    Signals with lifecycle_state=SKIPPED are those that have incomplete wiring.
    """

    def test_skipped_count_below_threshold(self) -> None:
        all_signals = _load_all_signals()
        skipped = [
            s["id"]
            for s in all_signals
            if s.get("lifecycle_state") == "SKIPPED"
        ]
        assert len(skipped) <= MAX_SKIPPED_THRESHOLD, (
            f"SKIPPED count {len(skipped)} exceeds threshold {MAX_SKIPPED_THRESHOLD}. "
            f"First 10: {skipped[:10]}"
        )


# ---------------------------------------------------------------------------
# V3 Contract Tests (Phase 82)
# Migration complete (Plan 82-02) — all tests active.
# ---------------------------------------------------------------------------


class TestSignalGroupAssignment:
    """SCHEMA-01: Every ACTIVE non-foundational signal must have a group."""

    def test_all_active_signals_have_group(self) -> None:
        """Every non-foundational ACTIVE signal has non-empty group."""
        for sig in _active_signals_validated():
            if sig.get("signal_class") == "foundational":
                continue
            assert sig.get("group"), (
                f"{sig['id']} missing group field (v3 contract)"
            )

    def test_group_values_exist_in_manifest(self) -> None:
        """Every group value references a valid manifest group ID."""
        manifest_path = (
            _PROJECT_ROOT / "src" / "do_uw" / "brain" / "output_manifest.yaml"
        )
        if not manifest_path.exists():
            pytest.skip("output_manifest.yaml not found")

        manifest = yaml.safe_load(manifest_path.read_text())
        # Extract all group IDs from manifest sections (groups or legacy facets key)
        valid_groups: set[str] = set()
        for section in manifest.get("sections", []):
            for group in section.get("groups", []):
                gid = group.get("id", "")
                if gid:
                    valid_groups.add(gid)
            for facet in section.get("facets", []):
                gid = facet.get("id", "")
                if gid:
                    valid_groups.add(gid)

        for sig in _active_signals_validated():
            group = sig.get("group", "")
            if group:
                assert group in valid_groups, (
                    f"{sig['id']} has group '{group}' not in manifest"
                )


class TestSignalDependencies:
    """SCHEMA-02: Signal dependency validation."""

    def test_foundational_signals_have_empty_depends_on(self) -> None:
        """Foundational signals should have empty depends_on."""
        for sig in _active_signals_validated():
            if sig.get("signal_class") == "foundational":
                assert not sig.get("depends_on"), (
                    f"{sig['id']} is foundational but has depends_on"
                )

    def test_depends_on_signal_ids_exist(self) -> None:
        """Every signal ID in depends_on references an actual signal."""
        all_ids = {s["id"] for s in _active_signals_validated()}
        for sig in _active_signals_validated():
            for dep in sig.get("depends_on", []):
                dep_id = dep if isinstance(dep, str) else dep.get("signal", "")
                assert dep_id in all_ids, (
                    f"{sig['id']} depends_on unknown signal '{dep_id}'"
                )


class TestSignalFieldPath:
    """SCHEMA-03: Signals with data_strategy should have field_path."""

    def test_signals_with_data_strategy_have_field_path(self) -> None:
        """Signals that have data_strategy.field_key should have non-empty field_path."""
        for sig in _active_signals_validated():
            ds = sig.get("data_strategy", {})
            if ds and ds.get("field_key"):
                assert sig.get("field_path"), (
                    f"{sig['id']} has data_strategy.field_key but missing field_path"
                )


class TestSignalClass:
    """SCHEMA-04: Every signal must have a valid signal_class."""

    def test_all_signals_have_valid_signal_class(self) -> None:
        """Every signal's signal_class is one of the valid values."""
        valid_classes = {"foundational", "evaluative", "inference"}
        for sig in _active_signals_validated():
            sc = sig.get("signal_class", "evaluative")
            assert sc in valid_classes, (
                f"{sig['id']} has invalid signal_class '{sc}'"
            )

    def test_foundational_count_in_range(self) -> None:
        """Between 20-35 signals should be foundational."""
        sigs = _active_signals_validated()
        fc = sum(1 for s in sigs if s.get("signal_class") == "foundational")
        assert 20 <= fc <= 35, (
            f"Foundational count {fc} outside expected range 20-35"
        )


class TestSignalAuditTrail:
    """SCHEMA-08: Signal provenance audit trail."""

    def test_active_signals_have_provenance_data_source(self) -> None:
        """Non-foundational ACTIVE signals have non-empty provenance.data_source."""
        for sig in _active_signals_validated():
            if sig.get("signal_class") == "foundational":
                continue
            prov = sig.get("provenance", {})
            assert prov.get("data_source"), (
                f"{sig['id']} missing provenance.data_source"
            )

    def test_threshold_provenance_categorized(self) -> None:
        """Signals with thresholds have threshold_provenance.source categorized."""
        valid_sources = {
            "calibrated", "standard", "unattributed",
            "d_and_o_claims_analysis", "sca_settlement_data",
            "academic_research", "underwriting_practice",
        }
        for sig in _active_signals_validated():
            threshold = sig.get("threshold", {})
            if not threshold.get("type") or threshold.get("type") in ("info", "display"):
                continue
            prov = sig.get("provenance", {})
            tp = prov.get("threshold_provenance", {})
            if tp:
                src = tp.get("source", "unattributed")
                assert src in valid_sources, (
                    f"{sig['id']} threshold_provenance.source '{src}' not valid"
                )
