"""Tests for brain chain validator.

Unit tests use constructed Pydantic models (no YAML/DuckDB needed).
Integration tests at bottom use real brain YAML data.
"""

from __future__ import annotations

import pytest

from do_uw.brain.brain_signal_schema import (
    AcquisitionSource,
    AcquisitionSpec,
    BrainSignalEntry,
    BrainSignalProvenance,
    BrainSignalThreshold,
    EvaluationSpec,
    EvaluationThreshold,
)
from do_uw.brain.manifest_schema import ManifestFacet, ManifestSection, OutputManifest
from do_uw.brain.chain_validator import (
    ChainGapType,
    ChainLink,
    ChainReport,
    GapSummary,
    SignalChainResult,
    _build_facet_signal_map,
    validate_all_chains,
    validate_single_chain,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_UNSET = object()


def _make_signal(
    signal_id: str = "FIN.PROFIT.revenue",
    name: str = "Revenue Analysis",
    work_type: str = "evaluate",
    signal_class: str = "evaluative",
    acquisition: AcquisitionSpec | None = None,
    acquisition_tier: str | None = "L1",
    data_strategy: dict | None | object = _UNSET,
    evaluation: EvaluationSpec | None = None,
    threshold_type: str = "tiered",
    threshold_red: str | None = "bad",
    group: str = "financial_health",
    lifecycle_state: str | None = None,
    **extra: object,
) -> BrainSignalEntry:
    """Build a BrainSignalEntry for testing."""
    ds = {"field_key": "xbrl_revenue_growth"} if data_strategy is _UNSET else data_strategy
    kwargs: dict = {
        "id": signal_id,
        "name": name,
        "work_type": work_type,
        "signal_class": signal_class,
        "tier": 2,
        "depth": 2,
        "threshold": BrainSignalThreshold(
            type=threshold_type,
            red=threshold_red,
        ),
        "provenance": BrainSignalProvenance(origin="test"),
        "acquisition": acquisition,
        "acquisition_tier": acquisition_tier,
        "data_strategy": ds,
        "evaluation": evaluation if evaluation is not None else EvaluationSpec(mechanism="threshold"),
        "group": group,
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "D&O underwriting practice",
            "threshold_basis": "Standard industry threshold",
        },
    }
    if lifecycle_state is not None:
        kwargs["lifecycle_state"] = lifecycle_state
    kwargs.update(extra)
    return BrainSignalEntry.model_validate(kwargs)


def _make_facet_signal_map(mapping: dict[str, list[str]] | None = None) -> dict[str, set[str]]:
    """Build a facet_signal_map for testing.

    Args:
        mapping: {facet_id: [signal_ids]}. Defaults to financial_health with FIN.PROFIT.revenue.
    """
    if mapping is None:
        mapping = {"financial_health": ["FIN.PROFIT.revenue"]}
    return {fid: set(sigs) for fid, sigs in mapping.items()}


def _make_manifest(facet_signals: dict[str, list[str]] | None = None) -> OutputManifest:
    """Build minimal OutputManifest with specified facets and their signals.

    Args:
        facet_signals: {facet_id: [signal_ids]}. Defaults to financial_health with FIN.PROFIT.revenue.
    """
    if facet_signals is None:
        facet_signals = {"financial_health": ["FIN.PROFIT.revenue"]}
    facets = [
        ManifestFacet(
            id=fid,
            name=fid.replace("_", " ").title(),
            template=f"sections/{fid}.html",
            data_type="extract_display",
            render_as="kv_table",
            signals=sigs,
        )
        for fid, sigs in facet_signals.items()
    ]
    return OutputManifest(
        manifest_version="1.0",
        sections=[
            ManifestSection(
                id="test_section",
                name="Test Section",
                template="sections/test.html",
                facets=facets,
            )
        ],
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


class TestValidateSingleChain:
    """Unit tests for validate_single_chain."""

    def test_chain_complete_all_four_links(self) -> None:
        """Signal with acquisition, field_key, evaluation, and facet in manifest = complete."""
        signal = _make_signal(
            acquisition=AcquisitionSpec(
                sources=[AcquisitionSource(type="SEC_10K", fields=["income"])]
            ),
            evaluation=EvaluationSpec(
                thresholds=[EvaluationThreshold(op=">", value=0.2, label="RED")],
                mechanism="threshold",
            ),
        )
        manifest = _make_manifest({"financial_health": ["FIN.PROFIT.revenue"]})
        facet_signal_map = _build_facet_signal_map(manifest)
        field_routing_keys: set[str] = set()

        result = validate_single_chain(signal, facet_signal_map, manifest, field_routing_keys)

        assert result.chain_status == "complete"
        assert result.gaps == []
        assert len(result.links) == 4

    def test_no_acquisition_gap(self) -> None:
        """Signal with no acquisition spec and no tier 1 match = NO_ACQUISITION."""
        signal = _make_signal(
            acquisition=None,
            acquisition_tier=None,
        )
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert ChainGapType.NO_ACQUISITION in result.gaps
        assert result.chain_status == "broken"

    def test_missing_field_key_gap(self) -> None:
        """Signal with no data_strategy.field_key = MISSING_FIELD_KEY."""
        signal = _make_signal(data_strategy=None)
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert ChainGapType.MISSING_FIELD_KEY in result.gaps

    def test_no_field_routing_produces_missing_field_key(self) -> None:
        """Signal with empty data_strategy (no field_key) = MISSING_FIELD_KEY."""
        signal = _make_signal(data_strategy={})  # no field_key in data_strategy
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert ChainGapType.MISSING_FIELD_KEY in result.gaps

    def test_no_evaluation_gap(self) -> None:
        """Signal with no threshold and no evaluation spec = NO_EVALUATION."""
        signal = _make_signal(
            evaluation=None,
            threshold_type="display",
            threshold_red=None,
        )
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert ChainGapType.NO_EVALUATION in result.gaps

    def test_no_facet_gap(self) -> None:
        """Signal not in any manifest facet's signals list = NO_FACET."""
        signal = _make_signal(signal_id="ORPHAN.SIGNAL.xyz", group="orphan_facet")
        manifest = _make_manifest({"financial_health": ["FIN.PROFIT.revenue"]})
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert ChainGapType.NO_FACET in result.gaps

    def test_multiple_gap_types_simultaneously(self) -> None:
        """A single signal can have multiple gap types."""
        signal = _make_signal(
            signal_id="ORPHAN.BAD.signal",
            acquisition=None,
            acquisition_tier=None,
            data_strategy=None,
            evaluation=None,
            threshold_type="display",
            threshold_red=None,
            group="missing_facet",
        )
        manifest = _make_manifest({"financial_health": ["FIN.PROFIT.revenue"]})
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        assert result.chain_status == "broken"
        assert len(result.gaps) >= 3
        assert ChainGapType.NO_ACQUISITION in result.gaps
        assert ChainGapType.MISSING_FIELD_KEY in result.gaps
        assert ChainGapType.NO_FACET in result.gaps

    def test_foundational_signal_only_checks_acquire_extract(self) -> None:
        """Foundational (signal_class='foundational') signals only check acquire+extract links."""
        signal = _make_signal(
            signal_class="foundational",
            evaluation=None,
            threshold_type="display",
            threshold_red=None,
            group="",
        )
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(signal, facet_signal_map, manifest, set())

        # Analyze and render links should be N/A
        na_links = [link for link in result.links if link.status == "na"]
        assert len(na_links) == 2
        assert result.chain_status == "complete"  # acquire+extract are fine

    def test_inactive_signal_detected(self) -> None:
        """INACTIVE signals (lifecycle_state=INACTIVE) are marked inactive."""
        signal = _make_signal(lifecycle_state="INACTIVE")
        manifest = _make_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)

        result = validate_single_chain(
            signal,
            facet_signal_map,
            manifest,
            set(),
        )

        assert result.chain_status == "inactive"


class TestValidateAllChains:
    """Tests for validate_all_chains using mocked signal loading."""

    def test_chain_report_correct_counts(self) -> None:
        """ChainReport has correct total/complete/broken/inactive counts."""
        # We test the report model directly since validate_all_chains loads from files
        results = [
            SignalChainResult(
                signal_id="A",
                signal_name="A",
                signal_type="evaluate",
                chain_status="complete",
                gaps=[],
                links=[],
            ),
            SignalChainResult(
                signal_id="B",
                signal_name="B",
                signal_type="evaluate",
                chain_status="broken",
                gaps=[ChainGapType.NO_ACQUISITION],
                links=[],
            ),
            SignalChainResult(
                signal_id="C",
                signal_name="C",
                signal_type="evaluate",
                chain_status="inactive",
                gaps=[],
                links=[],
            ),
        ]
        report = ChainReport(
            total_signals=3,
            chain_complete=1,
            chain_broken=1,
            inactive_count=1,
            results=results,
            gap_summary=[
                GapSummary(
                    gap_type=ChainGapType.NO_ACQUISITION,
                    signal_ids=["B"],
                    count=1,
                )
            ],
        )

        assert report.total_signals == 3
        assert report.chain_complete == 1
        assert report.chain_broken == 1
        assert report.inactive_count == 1

    def test_gap_summary_groups_by_type(self) -> None:
        """GapSummary groups signals by gap type with counts."""
        summary = GapSummary(
            gap_type=ChainGapType.MISSING_FIELD_KEY,
            signal_ids=["A", "B", "C"],
            count=3,
        )
        assert summary.count == 3
        assert len(summary.signal_ids) == 3


# ---------------------------------------------------------------------------
# Integration tests -- real YAML data
# ---------------------------------------------------------------------------


class TestIntegrationRealData:
    """Integration tests using real brain YAML, sections, and manifest."""

    def test_validate_all_chains_with_real_data(self) -> None:
        """validate_all_chains processes all real signals without error.

        After Phase 81, render-link resolution uses manifest facets (476 signals)
        instead of section YAML facets (135 signals), so broken chains should
        drop significantly from the previous 403.
        """
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()  # ensure fresh load
        report = validate_all_chains()

        # We have ~476 signals
        assert report.total_signals > 400, f"Expected 400+ signals, got {report.total_signals}"

        # Counts must add up
        assert (
            report.chain_complete + report.chain_broken + report.inactive_count
            == report.total_signals
        ), (
            f"Counts don't add up: {report.chain_complete} + {report.chain_broken} "
            f"+ {report.inactive_count} != {report.total_signals}"
        )

        # After manifest-based resolution, broken chains should be significantly
        # less than the old 403. Phase 110 added 48 inference signals (562 total).
        assert report.chain_broken < 280, (
            f"Expected broken chains < 280 (was 403 with section YAML), "
            f"got {report.chain_broken}"
        )

        # Every result has a valid signal_id
        for result in report.results:
            assert result.signal_id, f"Empty signal_id found in results"
            assert result.chain_status in (
                "complete",
                "broken",
                "inactive",
            ), f"Invalid chain_status: {result.chain_status}"

    def test_single_chain_real_signal(self) -> None:
        """Validate a known well-connected signal (FIN.PROFIT.revenue)."""
        from do_uw.brain.brain_signal_schema import BrainSignalEntry
        from do_uw.brain.brain_unified_loader import load_signals
        from do_uw.brain.chain_validator import _build_facet_signal_map
        from do_uw.brain.manifest_schema import load_manifest
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        data = load_signals()
        signal_dicts = data["signals"]
        target = None
        for raw in signal_dicts:
            if isinstance(raw, dict) and raw.get("id") == "FIN.PROFIT.revenue":
                target = BrainSignalEntry.model_validate(raw)
                break
            elif isinstance(raw, BrainSignalEntry) and raw.id == "FIN.PROFIT.revenue":
                target = raw
                break

        assert target is not None, "FIN.PROFIT.revenue not found in signals"

        manifest = load_manifest()
        facet_signal_map = _build_facet_signal_map(manifest)
        field_routing_keys = set(FIELD_FOR_CHECK.keys())

        result = validate_single_chain(target, facet_signal_map, manifest, field_routing_keys)

        # Document what we find -- this signal should at minimum have acquire+extract
        assert result.signal_type == "evaluative"
        assert result.chain_status in ("complete", "broken")
        # At minimum acquire and extract should be complete for this well-known signal
        acquire_link = next((l for l in result.links if l.link_type == "acquire"), None)
        extract_link = next((l for l in result.links if l.link_type == "extract"), None)
        assert acquire_link is not None and acquire_link.status == "complete"
        assert extract_link is not None and extract_link.status == "complete"

    def test_foundational_signals_have_modified_chain(self) -> None:
        """Foundational signals have analyze and render links marked N/A."""
        report = validate_all_chains()

        foundational_results = [
            r for r in report.results if r.signal_type == "foundational"
        ]

        # If there are foundational signals, verify their chain structure
        for result in foundational_results:
            if result.chain_status == "inactive":
                continue
            na_links = [link for link in result.links if link.status == "na"]
            assert len(na_links) == 2, (
                f"Foundational signal {result.signal_id} should have 2 N/A links, "
                f"got {len(na_links)}"
            )
            na_types = {link.link_type for link in na_links}
            assert na_types == {"analyze", "render"}, (
                f"Foundational signal {result.signal_id} N/A links should be "
                f"analyze+render, got {na_types}"
            )
