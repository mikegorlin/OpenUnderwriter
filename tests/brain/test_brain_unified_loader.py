"""Tests for brain_unified_loader.py — unified BrainLoader.

Tests cover:
- YAML signal loading with backward-compat enrichment
- JSON config loading from brain/config/
- Convenience methods (load_scoring, load_patterns, etc.)
- load_all() returning BrainConfig
- Framework data loading (perils, causal chains, taxonomy)
- Caching behavior
- Invalid signal handling (lazy validation)
- Performance benchmark (< 1 second for 400 signals)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------
# Integration tests: use actual YAML/JSON files on disk
# ---------------------------------------------------------------


class TestLoadSignalsIntegration:
    """Integration tests against actual brain/signals/ YAML files."""

    def setup_method(self) -> None:
        """Reset caches before each test."""
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_load_signals_returns_dict_with_signals_key(self) -> None:
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        assert isinstance(result, dict)
        assert "signals" in result
        assert "total_signals" in result

    def test_load_signals_returns_expected_count(self) -> None:
        """Signal count: 400 evaluative + 25 foundational = 425 total."""
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        assert result["total_signals"] >= 425, (
            f"Expected >= 425 signals (400 evaluative + 25 foundational), got {result['total_signals']}"
        )
        assert len(result["signals"]) == result["total_signals"]

    def test_load_signals_performance_under_1_second(self) -> None:
        """Benchmark: load_signals() must complete in < 1 second."""
        from do_uw.brain.brain_unified_loader import _reset_cache, load_signals

        _reset_cache()
        start = time.time()
        load_signals()
        elapsed = time.time() - start
        assert elapsed < 1.0, f"load_signals() took {elapsed:.3f}s, must be < 1.0s"

    def test_signals_have_backward_compat_fields(self) -> None:
        """Each signal dict must have content_type, hazard_or_signal, category, section."""
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        for sig in result["signals"]:
            assert "content_type" in sig, f"Signal {sig.get('id')} missing content_type"
            assert "hazard_or_signal" in sig, f"Signal {sig.get('id')} missing hazard_or_signal"
            assert "category" in sig, f"Signal {sig.get('id')} missing category"
            assert "section" in sig, f"Signal {sig.get('id')} missing section"

    def test_signals_content_type_values(self) -> None:
        """content_type should be one of the three valid values."""
        from do_uw.brain.brain_unified_loader import load_signals

        valid_types = {"EVALUATIVE_CHECK", "MANAGEMENT_DISPLAY", "INFERENCE_PATTERN"}
        result = load_signals()
        for sig in result["signals"]:
            assert sig["content_type"] in valid_types, (
                f"Signal {sig['id']} has invalid content_type: {sig['content_type']}"
            )

    def test_signals_have_id_and_name(self) -> None:
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        for sig in result["signals"]:
            assert "id" in sig
            assert "name" in sig

    def test_signals_cached_second_call(self) -> None:
        """Second call returns same object without re-parsing."""
        from do_uw.brain.brain_unified_loader import load_signals

        r1 = load_signals()
        r2 = load_signals()
        assert r1 is r2  # same object reference = cached

    def test_signals_section_is_integer(self) -> None:
        """section field should be an integer (section number)."""
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        for sig in result["signals"]:
            assert isinstance(sig["section"], int), (
                f"Signal {sig['id']} section should be int, got {type(sig['section'])}"
            )


class TestLoadConfigIntegration:
    """Integration tests for load_config() against actual brain/config/ JSON."""

    def setup_method(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_load_config_actuarial(self) -> None:
        from do_uw.brain.brain_unified_loader import load_config

        result = load_config("actuarial")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_load_config_nonexistent_returns_empty(self) -> None:
        from do_uw.brain.brain_unified_loader import load_config

        result = load_config("nonexistent_config_xyz")
        assert result == {}

    def test_load_config_cached(self) -> None:
        from do_uw.brain.brain_unified_loader import load_config

        r1 = load_config("actuarial")
        r2 = load_config("actuarial")
        assert r1 is r2

    def test_load_scoring(self) -> None:
        from do_uw.brain.brain_unified_loader import load_scoring

        result = load_scoring()
        assert isinstance(result, dict)
        assert "factors" in result

    def test_load_scoring_has_10_factors(self) -> None:
        from do_uw.brain.brain_unified_loader import load_scoring

        result = load_scoring()
        factors = result.get("factors", {})
        assert len(factors) == 10, f"Expected 10 scoring factors, got {len(factors)}"

    def test_load_scoring_has_tiers(self) -> None:
        from do_uw.brain.brain_unified_loader import load_scoring

        result = load_scoring()
        assert "tiers" in result

    def test_load_patterns(self) -> None:
        from do_uw.brain.brain_unified_loader import load_patterns

        result = load_patterns()
        assert isinstance(result, dict)
        assert "patterns" in result
        assert "total_patterns" in result

    def test_load_red_flags(self) -> None:
        from do_uw.brain.brain_unified_loader import load_red_flags

        result = load_red_flags()
        assert isinstance(result, dict)
        assert "escalation_triggers" in result

    def test_load_sectors(self) -> None:
        from do_uw.brain.brain_unified_loader import load_sectors

        result = load_sectors()
        assert isinstance(result, dict)
        assert "short_interest" in result
        assert "volatility_90d" in result


class TestLoadAllIntegration:
    """Test load_all() returns properly structured BrainConfig."""

    def setup_method(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_load_all_returns_brain_config(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainConfig, load_all

        result = load_all()
        assert isinstance(result, BrainConfig)

    def test_load_all_has_checks(self) -> None:
        from do_uw.brain.brain_unified_loader import load_all

        result = load_all()
        assert isinstance(result.checks, dict)
        assert "signals" in result.checks

    def test_load_all_has_scoring(self) -> None:
        from do_uw.brain.brain_unified_loader import load_all

        result = load_all()
        assert isinstance(result.scoring, dict)
        assert "factors" in result.scoring

    def test_load_all_has_patterns(self) -> None:
        from do_uw.brain.brain_unified_loader import load_all

        result = load_all()
        assert isinstance(result.patterns, dict)

    def test_load_all_has_sectors(self) -> None:
        from do_uw.brain.brain_unified_loader import load_all

        result = load_all()
        assert isinstance(result.sectors, dict)

    def test_load_all_has_red_flags(self) -> None:
        from do_uw.brain.brain_unified_loader import load_all

        result = load_all()
        assert isinstance(result.red_flags, dict)


class TestFrameworkDataIntegration:
    """Test framework data loading (perils, causal chains, taxonomy)."""

    def setup_method(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_load_perils_returns_list(self) -> None:
        from do_uw.brain.brain_unified_loader import load_perils

        result = load_perils()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_load_perils_have_expected_keys(self) -> None:
        from do_uw.brain.brain_unified_loader import load_perils

        result = load_perils()
        for peril in result:
            assert "id" in peril or "peril_id" in peril
            assert "name" in peril
            assert "description" in peril

    def test_load_causal_chains_returns_list(self) -> None:
        from do_uw.brain.brain_unified_loader import load_causal_chains

        result = load_causal_chains()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_load_causal_chains_have_expected_keys(self) -> None:
        from do_uw.brain.brain_unified_loader import load_causal_chains

        result = load_causal_chains()
        for chain in result:
            assert "id" in chain or "chain_id" in chain
            assert "name" in chain

    def test_load_taxonomy_returns_dict(self) -> None:
        from do_uw.brain.brain_unified_loader import load_taxonomy

        result = load_taxonomy()
        assert isinstance(result, dict)


class TestBrainLoaderClass:
    """Test the BrainLoader class wrapper."""

    def setup_method(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_class_load_signals(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        result = loader.load_signals()
        assert isinstance(result, dict)
        assert result["total_signals"] >= 425  # 400 evaluative + 25 foundational

    def test_class_load_scoring(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        result = loader.load_scoring()
        assert isinstance(result, dict)

    def test_class_load_all(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainConfig, BrainLoader

        loader = BrainLoader()
        result = loader.load_all()
        assert isinstance(result, BrainConfig)

    def test_class_source_property(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        assert loader.source == "brain_yaml"

    def test_class_load_perils(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        result = loader.load_perils()
        assert isinstance(result, list)

    def test_class_load_causal_chains(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        result = loader.load_causal_chains()
        assert isinstance(result, list)

    def test_class_load_taxonomy(self) -> None:
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        result = loader.load_taxonomy()
        assert isinstance(result, dict)


class TestBackwardCompatAPI:
    """Test backward-compat load_brain_config function."""

    def setup_method(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache

        _reset_cache()

    def test_load_brain_config_compat(self) -> None:
        from do_uw.brain.brain_unified_loader import load_brain_config

        result = load_brain_config("actuarial")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_load_brain_config_ignores_config_dir(self) -> None:
        """config_dir parameter is accepted but ignored."""
        from do_uw.brain.brain_unified_loader import load_brain_config

        result = load_brain_config("actuarial", config_dir=Path("/nonexistent"))
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_load_brain_config_or_raise_missing(self) -> None:
        from do_uw.brain.brain_unified_loader import load_brain_config_or_raise

        with pytest.raises(FileNotFoundError):
            load_brain_config_or_raise("nonexistent_config_xyz")

    def test_load_brain_config_or_raise_found(self) -> None:
        from do_uw.brain.brain_unified_loader import load_brain_config_or_raise

        result = load_brain_config_or_raise("actuarial")
        assert isinstance(result, dict)
        assert len(result) > 0


class TestResetCache:
    """Test _reset_cache() clears all caches."""

    def test_reset_cache_clears_signals(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache, load_signals

        r1 = load_signals()
        _reset_cache()
        r2 = load_signals()
        assert r1 is not r2  # different objects after cache reset

    def test_reset_cache_clears_config(self) -> None:
        from do_uw.brain.brain_unified_loader import _reset_cache, load_config

        r1 = load_config("actuarial")
        _reset_cache()
        r2 = load_config("actuarial")
        assert r1 is not r2


# ---------------------------------------------------------------
# Unit tests: use temp directories with fixture YAML
# ---------------------------------------------------------------


class TestEnrichmentUnit:
    """Unit tests for signal enrichment logic using fixture YAML."""

    def _write_signal_yaml(self, tmp_path: Path, signals: list[dict[str, Any]]) -> None:
        """Write signals to a YAML fixture file."""
        import yaml

        sig_dir = tmp_path / "signals" / "test"
        sig_dir.mkdir(parents=True)
        with open(sig_dir / "test.yaml", "w") as f:
            yaml.dump(signals, f)

    def test_enrichment_evaluative_check(self, tmp_path: Path) -> None:
        """work_type=evaluate -> content_type=EVALUATIVE_CHECK."""
        from do_uw.brain.brain_enrichment import enrich_signal

        raw: dict[str, Any] = {
            "id": "TEST.1",
            "name": "Test",
            "work_type": "evaluate",
            "layer": "signal",
            "tier": 2,
            "depth": 2,
            "threshold": {"type": "tiered"},
            "provenance": {"origin": "test"},
        }
        enriched = enrich_signal(raw)
        assert enriched["content_type"] == "EVALUATIVE_CHECK"

    def test_enrichment_management_display(self, tmp_path: Path) -> None:
        """work_type=extract -> content_type=MANAGEMENT_DISPLAY."""
        from do_uw.brain.brain_enrichment import enrich_signal

        raw: dict[str, Any] = {
            "id": "TEST.2",
            "name": "Test Display",
            "work_type": "extract",
            "layer": "hazard",
            "tier": 1,
            "depth": 1,
            "threshold": {"type": "display"},
            "provenance": {"origin": "test"},
        }
        enriched = enrich_signal(raw)
        assert enriched["content_type"] == "MANAGEMENT_DISPLAY"
        assert enriched["category"] == "CONTEXT_DISPLAY"

    def test_enrichment_inference_pattern(self) -> None:
        """work_type=infer -> content_type=INFERENCE_PATTERN."""
        from do_uw.brain.brain_enrichment import enrich_signal

        raw: dict[str, Any] = {
            "id": "TEST.3",
            "name": "Test Infer",
            "work_type": "infer",
            "layer": "peril_confirming",
            "tier": 3,
            "depth": 3,
            "threshold": {"type": "tiered"},
            "provenance": {"origin": "test"},
        }
        enriched = enrich_signal(raw)
        assert enriched["content_type"] == "INFERENCE_PATTERN"
        assert enriched["hazard_or_signal"] == "PERIL_CONFIRMING"

    def test_enrichment_section_from_worksheet_section(self) -> None:
        """worksheet_section=financial -> section=3."""
        from do_uw.brain.brain_enrichment import enrich_signal

        raw: dict[str, Any] = {
            "id": "TEST.4",
            "name": "Test Section",
            "work_type": "evaluate",
            "layer": "signal",
            "tier": 2,
            "depth": 2,
            "worksheet_section": "financial",
            "threshold": {"type": "tiered"},
            "provenance": {"origin": "test"},
        }
        enriched = enrich_signal(raw)
        assert enriched["section"] == 3

    def test_enrichment_decision_driving_category(self) -> None:
        """Non tier-1 extract -> category=DECISION_DRIVING."""
        from do_uw.brain.brain_enrichment import enrich_signal

        raw: dict[str, Any] = {
            "id": "TEST.5",
            "name": "Test Category",
            "work_type": "evaluate",
            "layer": "signal",
            "tier": 2,
            "depth": 2,
            "threshold": {"type": "tiered"},
            "provenance": {"origin": "test"},
        }
        enriched = enrich_signal(raw)
        assert enriched["category"] == "DECISION_DRIVING"


class TestInvalidSignalHandling:
    """Test that invalid signals are logged and skipped."""

    def test_invalid_signal_skipped(self, tmp_path: Path) -> None:
        """Signal missing required fields should be skipped with warning."""
        import yaml

        from do_uw.brain.brain_unified_loader import _load_and_validate_signals

        sig_dir = tmp_path / "signals" / "test"
        sig_dir.mkdir(parents=True)

        # Valid signal (includes v7.0 required fields)
        valid = {
            "id": "TEST.VALID",
            "name": "Valid Signal",
            "work_type": "evaluate",
            "layer": "signal",
            "tier": 2,
            "depth": 2,
            "threshold": {"type": "tiered"},
            "provenance": {"origin": "test"},
            "rap_class": "host",
            "rap_subcategory": "host.financials",
            "epistemology": {
                "rule_origin": "D&O underwriting practice",
                "threshold_basis": "Standard industry threshold",
            },
            "evaluation": {"mechanism": "threshold"},
        }
        # Invalid signal (missing required fields)
        invalid = {
            "id": "TEST.INVALID",
            # missing name, work_type, etc.
        }

        with open(sig_dir / "test.yaml", "w") as f:
            yaml.dump([valid, invalid], f)

        signals, skipped = _load_and_validate_signals(sig_dir)
        assert len(signals) == 1
        assert signals[0]["id"] == "TEST.VALID"
        assert skipped == 1
