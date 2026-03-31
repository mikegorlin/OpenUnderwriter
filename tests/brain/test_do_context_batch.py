"""Tests for batch-generated do_context templates across all brain signals.

Validates that every signal YAML has do_context with proper templates,
valid syntax, placeholder variables, and no generic boilerplate.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from do_uw.stages.analyze.do_context_engine import validate_do_context_template

SIGNALS_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "do_uw" / "brain" / "signals"

# Banned generic phrases that violate QUAL-04
BANNED_PHRASES = [
    "elevated risk",
    "warrants attention",
    "notable concern",
    "significant implications",
    "requires monitoring",
    "should be noted",
    "bears watching",
    "merits consideration",
    "deserves scrutiny",
]

# Valid placeholder variables
VALID_PLACEHOLDERS = {"{value}", "{company}", "{evidence}", "{score}", "{zone}",
                      "{threshold}", "{threshold_level}", "{source}", "{confidence}",
                      "{ticker}"}


def _load_all_signals() -> list[tuple[str, str, dict]]:
    """Load all signals from YAML files.

    Returns list of (file_path, signal_id, signal_dict) tuples.
    """
    signals = []
    for yaml_file in sorted(SIGNALS_DIR.rglob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            continue
        for sig in data:
            sig_id = sig.get("id", f"unknown@{yaml_file.name}")
            signals.append((str(yaml_file), sig_id, sig))
    return signals


def _load_all_do_context_templates() -> list[tuple[str, str, str, str]]:
    """Load all do_context templates across all signals.

    Returns list of (file_path, signal_id, template_key, template_text) tuples.
    """
    templates = []
    for file_path, sig_id, sig in _load_all_signals():
        pres = sig.get("presentation")
        if pres and isinstance(pres, dict):
            dc = pres.get("do_context")
            if dc and isinstance(dc, dict):
                for key, text in dc.items():
                    templates.append((file_path, sig_id, key, str(text)))
    return templates


class TestAllSignalsHaveDoContext:
    """Every signal must have presentation.do_context."""

    def test_all_signals_have_do_context(self) -> None:
        """Assert every signal YAML entry has presentation.do_context with
        at least TRIGGERED_RED and CLEAR keys.
        """
        missing: list[str] = []
        incomplete: list[str] = []

        for file_path, sig_id, sig in _load_all_signals():
            pres = sig.get("presentation")
            if not pres or not isinstance(pres, dict):
                missing.append(f"{sig_id} ({Path(file_path).name})")
                continue

            dc = pres.get("do_context")
            if not dc or not isinstance(dc, dict):
                missing.append(f"{sig_id} ({Path(file_path).name})")
                continue

            # Must have at least TRIGGERED_RED and CLEAR
            if "TRIGGERED_RED" not in dc:
                incomplete.append(f"{sig_id}: missing TRIGGERED_RED")
            if "CLEAR" not in dc:
                incomplete.append(f"{sig_id}: missing CLEAR")

        assert not missing, (
            f"{len(missing)} signals missing do_context:\n"
            + "\n".join(missing[:20])
            + (f"\n  ... and {len(missing) - 20} more" if len(missing) > 20 else "")
        )
        assert not incomplete, (
            f"{len(incomplete)} signals with incomplete do_context:\n"
            + "\n".join(incomplete[:20])
        )


class TestAllTemplatesPassValidation:
    """Every do_context template must pass validate_do_context_template."""

    def test_all_templates_pass_validation(self) -> None:
        """Run validate_do_context_template on every template across all signals."""
        errors: list[str] = []

        for file_path, sig_id, key, text in _load_all_do_context_templates():
            errs = validate_do_context_template(text)
            if errs:
                errors.append(f"{sig_id}.{key}: {'; '.join(errs)}")

        assert not errors, (
            f"{len(errors)} template validation errors:\n"
            + "\n".join(errors[:20])
            + (f"\n  ... and {len(errors) - 20} more" if len(errors) > 20 else "")
        )


class TestTemplatesContainPlaceholders:
    """Every template must reference at least one company-specific variable."""

    def test_templates_contain_placeholders(self) -> None:
        """Assert every do_context template contains at least one of:
        {value}, {company}, {evidence}, {score}, {zone}.
        """
        no_placeholder: list[str] = []

        for file_path, sig_id, key, text in _load_all_do_context_templates():
            # Check for any valid placeholder
            has_placeholder = False
            for ph in VALID_PLACEHOLDERS:
                if ph in text:
                    has_placeholder = True
                    break
            # Also check for {details_*} pattern
            if not has_placeholder and "{details_" in text:
                has_placeholder = True

            if not has_placeholder:
                no_placeholder.append(f"{sig_id}.{key}: '{text[:80]}...'")

        assert not no_placeholder, (
            f"{len(no_placeholder)} templates without placeholder variables:\n"
            + "\n".join(no_placeholder[:20])
        )


class TestNoGenericBoilerplate:
    """Templates must not contain banned generic phrases (QUAL-04)."""

    def test_no_generic_boilerplate(self) -> None:
        """Grep for banned phrases in all do_context templates."""
        violations: list[str] = []

        for file_path, sig_id, key, text in _load_all_do_context_templates():
            text_lower = text.lower()
            for phrase in BANNED_PHRASES:
                if phrase in text_lower:
                    violations.append(
                        f"{sig_id}.{key}: contains '{phrase}'"
                    )

        assert not violations, (
            f"{len(violations)} generic boilerplate violations:\n"
            + "\n".join(violations[:20])
            + (f"\n  ... and {len(violations) - 20} more" if len(violations) > 20 else "")
        )


class TestDoContextTemplateKeys:
    """Template keys must be valid status strings."""

    VALID_KEYS = {"TRIGGERED_RED", "TRIGGERED_YELLOW", "CLEAR", "TRIGGERED", "DEFAULT", "INFO"}

    def test_template_keys_are_valid(self) -> None:
        """Assert all do_context keys are recognized by _select_template."""
        invalid_keys: list[str] = []

        for file_path, sig_id, sig in _load_all_signals():
            pres = sig.get("presentation")
            if pres and isinstance(pres, dict):
                dc = pres.get("do_context")
                if dc and isinstance(dc, dict):
                    for key in dc:
                        if key not in self.VALID_KEYS:
                            invalid_keys.append(f"{sig_id}: invalid key '{key}'")

        assert not invalid_keys, (
            f"{len(invalid_keys)} invalid do_context keys:\n"
            + "\n".join(invalid_keys[:20])
        )
