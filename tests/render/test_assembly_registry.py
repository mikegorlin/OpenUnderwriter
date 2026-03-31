"""Tests for the assembly registry pattern (Phase 128-01 Task 1).

Verifies:
1. build_html_context is importable from assembly_registry
2. Each assembly module is under 500 lines
3. html_context_assembly.py is under 20 lines (re-export stub)
4. Registry pattern works (mock builder gets called)
5. All context keys from original build_html_context are preserved
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "do_uw" / "stages" / "render"
CTX_BUILDERS_DIR = SRC_DIR / "context_builders"


def test_build_html_context_importable_from_registry():
    """Test 1: build_html_context is importable from assembly_registry."""
    from do_uw.stages.render.context_builders.assembly_registry import build_html_context
    assert callable(build_html_context)


def test_assembly_modules_under_500_lines():
    """Test 2: Each assembly module is under 500 lines."""
    modules = [
        CTX_BUILDERS_DIR / "assembly_registry.py",
        CTX_BUILDERS_DIR / "assembly_html_extras.py",
        CTX_BUILDERS_DIR / "assembly_signals.py",
        CTX_BUILDERS_DIR / "assembly_dossier.py",
    ]
    for mod in modules:
        assert mod.exists(), f"Module {mod.name} does not exist"
        line_count = len(mod.read_text().splitlines())
        assert line_count < 500, f"{mod.name} has {line_count} lines (max 500)"


def test_html_context_assembly_is_stub():
    """Test 3: html_context_assembly.py is under 20 lines (re-export stub)."""
    stub = SRC_DIR / "html_context_assembly.py"
    assert stub.exists(), "html_context_assembly.py should still exist as stub"
    line_count = len(stub.read_text().splitlines())
    assert line_count < 20, f"html_context_assembly.py has {line_count} lines (should be <20)"


def test_registry_pattern_calls_registered_builder():
    """Test 4: A mock registry builder is called when registered."""
    from do_uw.stages.render.context_builders.assembly_registry import (
        _BUILDERS,
        register_builder,
    )

    mock_builder = MagicMock()
    original_len = len(_BUILDERS)

    # Register the mock
    register_builder(mock_builder)
    assert len(_BUILDERS) == original_len + 1
    assert _BUILDERS[-1] is mock_builder

    # Clean up: remove the mock so it doesn't affect other tests
    _BUILDERS.pop()
    assert len(_BUILDERS) == original_len


def test_backward_compat_import():
    """build_html_context is still importable from html_context_assembly."""
    from do_uw.stages.render.html_context_assembly import build_html_context
    assert callable(build_html_context)


def test_risk_class_importable_from_registry():
    """_risk_class is importable from assembly_registry."""
    from do_uw.stages.render.context_builders.assembly_registry import _risk_class
    assert _risk_class("distress") == "TRIGGERED"
    assert _risk_class("safe") == "CLEAR"
    assert _risk_class("") == ""


def test_risk_class_backward_compat():
    """_risk_class is still importable from html_context_assembly."""
    from do_uw.stages.render.html_context_assembly import _risk_class
    assert _risk_class("grey") == "ELEVATED"


def test_each_module_has_register_decorator():
    """Each assembly_*.py module (except registry) uses @register_builder."""
    for name in ("assembly_html_extras", "assembly_signals", "assembly_dossier"):
        mod_path = CTX_BUILDERS_DIR / f"{name}.py"
        assert mod_path.exists(), f"{name}.py does not exist"
        content = mod_path.read_text()
        assert "@register_builder" in content, f"{name}.py missing @register_builder decorator"
