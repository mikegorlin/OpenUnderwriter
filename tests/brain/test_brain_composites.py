"""CI tests for brain signal composites.

Validates:
1. Composite YAML integrity (member signals exist, IDs valid)
2. Facet content refs point to valid composites/signals
3. No orphaned composite member signals
4. Engine handles empty results gracefully
"""

from pathlib import Path

import pytest
import yaml

from do_uw.brain.brain_composite_engine import evaluate_composites
from do_uw.brain.brain_composite_schema import (
    CompositeDefinition,
    load_all_composites,
)

# Use __file__ for robust path resolution regardless of CWD
_PROJECT_ROOT = Path(__file__).parent.parent.parent
SIGNALS_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals"
COMPOSITES_DIR = _PROJECT_ROOT / "src" / "do_uw" / "brain" / "composites"


def _load_all_signal_ids() -> set[str]:
    """Load all signal IDs from brain YAML files."""
    signal_ids: set[str] = set()
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "id" in entry:
                    signal_ids.add(entry["id"])
    return signal_ids


class TestCompositeYAMLIntegrity:
    """Composite YAML definitions must reference valid signals."""

    def test_composites_directory_exists(self) -> None:
        """composites/ directory must exist."""
        assert COMPOSITES_DIR.exists(), (
            f"composites directory not found at {COMPOSITES_DIR}"
        )

    def test_all_composite_member_signals_exist(self) -> None:
        """Every member_signal in every composite must be a real signal ID."""
        if not COMPOSITES_DIR.exists():
            pytest.skip("composites/ directory does not exist")

        signal_ids = _load_all_signal_ids()
        composites = load_all_composites(COMPOSITES_DIR)

        for comp_id, comp_def in composites.items():
            for sig_id in comp_def.member_signals:
                assert sig_id in signal_ids, (
                    f"Composite '{comp_id}' references unknown signal '{sig_id}'. "
                    f"Signal must exist in brain/signals/**/*.yaml"
                )

    def test_composite_ids_are_valid_format(self) -> None:
        """All composite IDs must start with 'COMP.' and be unique."""
        if not COMPOSITES_DIR.exists():
            pytest.skip("composites/ directory does not exist")

        composites = load_all_composites(COMPOSITES_DIR)
        seen_ids: set[str] = set()

        for comp_id in composites:
            assert comp_id.startswith("COMP."), (
                f"Composite ID '{comp_id}' must start with 'COMP.'"
            )
            assert comp_id not in seen_ids, (
                f"Duplicate composite ID: '{comp_id}'"
            )
            seen_ids.add(comp_id)

    def test_composite_evaluators_are_registered(self) -> None:
        """Every composite's evaluator must be in the evaluator registry."""
        if not COMPOSITES_DIR.exists():
            pytest.skip("composites/ directory does not exist")

        from do_uw.brain.brain_composite_engine import _EVALUATORS

        composites = load_all_composites(COMPOSITES_DIR)
        for comp_id, comp_def in composites.items():
            assert comp_def.evaluator in _EVALUATORS, (
                f"Composite '{comp_id}' uses unregistered evaluator "
                f"'{comp_def.evaluator}'. "
                f"Registered: {sorted(_EVALUATORS.keys())}"
            )


class TestFacetContentRefs:
    """Facet content references must point to valid composites or signals.

    Phase 84-04: Section YAML files have been deleted. Facet content_refs
    were a section YAML concept. This test class is retained for composites
    that may be referenced from manifest groups in the future.
    """

    def test_facet_content_refs_are_valid(self) -> None:
        """Skipped: section YAML (facet content refs) eliminated in 84-04."""
        pytest.skip("Section YAML eliminated in Phase 84-04; facet content refs no longer exist")


class TestCompositeSignalFacetCoverage:
    """Composite member signals should have a group assignment.

    Phase 84-04: Migrated from section YAML facet lists to signal group
    field. Every composite member signal must have a non-empty group field
    in its YAML definition (i.e., it self-selects into a manifest group).
    """

    def test_no_composite_member_signal_orphaned(self) -> None:
        """Every signal referenced by a composite should have a group
        assignment in its YAML definition."""
        if not COMPOSITES_DIR.exists():
            pytest.skip("composites/ directory does not exist")

        composites = load_all_composites(COMPOSITES_DIR)

        # Collect all signal IDs that have a group assignment
        grouped_signal_ids: set[str] = set()
        for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
            raw = yaml.safe_load(yaml_path.read_text())
            if raw is None:
                continue
            signals_list = raw if isinstance(raw, list) else raw.get("signals", [raw])
            for sig in signals_list:
                if isinstance(sig, dict) and sig.get("group"):
                    sig_id = sig.get("id", "")
                    if sig_id:
                        grouped_signal_ids.add(sig_id)

        # Check every composite member signal has a group
        for comp_id, comp_def in composites.items():
            for sig_id in comp_def.member_signals:
                assert sig_id in grouped_signal_ids, (
                    f"Composite '{comp_id}' member signal '{sig_id}' "
                    f"has no group assignment in its signal YAML"
                )


class TestDefaultEvaluatorGraceful:
    """Default evaluator must handle empty results without crashing."""

    def test_default_evaluator_handles_empty_results(self) -> None:
        """evaluate_composites with empty signal_results produces CLEAR."""
        defs = {
            "COMP.TEST.empty": CompositeDefinition(
                id="COMP.TEST.empty",
                name="Empty Test",
                member_signals=["SIG.A", "SIG.B", "SIG.C"],
                conclusion_schema={"summary": "test"},
            ),
        }
        results = evaluate_composites(defs, {})

        assert "COMP.TEST.empty" in results
        cr = results["COMP.TEST.empty"]
        assert cr.severity == "CLEAR"
        assert cr.member_count == 3
        assert cr.triggered_count == 0
        assert cr.skipped_count == 3
        assert "no data" in cr.narrative.lower()

    def test_evaluator_with_mixed_statuses(self) -> None:
        """evaluate_composites correctly counts mixed statuses."""
        defs = {
            "COMP.TEST.mixed": CompositeDefinition(
                id="COMP.TEST.mixed",
                name="Mixed Test",
                member_signals=["SIG.A", "SIG.B", "SIG.C"],
            ),
        }
        signal_results = {
            "SIG.A": {"status": "TRIGGERED", "value": "1.5", "details": {}},
            "SIG.B": {"status": "CLEAR", "value": "0.5", "details": {}},
            "SIG.C": {"status": "SKIPPED", "value": None, "details": {}},
        }
        results = evaluate_composites(defs, signal_results)

        cr = results["COMP.TEST.mixed"]
        assert cr.severity == "YELLOW"  # 1 of 2 available = 50%, not >50%
        assert cr.triggered_count == 1
        assert cr.skipped_count == 1
        assert cr.member_count == 3

    def test_evaluator_all_triggered(self) -> None:
        """All TRIGGERED = RED severity."""
        defs = {
            "COMP.TEST.red": CompositeDefinition(
                id="COMP.TEST.red",
                name="Red Test",
                member_signals=["SIG.A", "SIG.B"],
            ),
        }
        signal_results = {
            "SIG.A": {"status": "TRIGGERED", "value": "1", "details": {}},
            "SIG.B": {"status": "TRIGGERED", "value": "2", "details": {}},
        }
        results = evaluate_composites(defs, signal_results)
        assert results["COMP.TEST.red"].severity == "RED"
