"""Wave 0 tests for QA-02: coerce_value() handles booleans correctly.

Python bool is a subclass of int; Pydantic v2 coerces True->1.0, False->0.0
in a str|float|None union. This test suite confirms booleans must be stored
as string "True"/"False" not as floats.
These tests FAIL before Plan 02 fixes coerce_value().
"""
import pytest
from do_uw.stages.analyze.signal_helpers import coerce_value


def test_true_becomes_string_true():
    """coerce_value(True) must return 'True' string, not 1 or 1.0."""
    result = coerce_value(True)
    assert result == "True", f"Expected 'True' got {result!r}"
    assert isinstance(result, str), f"Expected str, got {type(result)}"


def test_false_becomes_string_false():
    """coerce_value(False) must return 'False' string, not 0 or 0.0."""
    result = coerce_value(False)
    assert result == "False", f"Expected 'False' got {result!r}"
    assert isinstance(result, str), f"Expected str, got {type(result)}"


def test_numeric_float_unchanged():
    """Numeric float values (e.g. ratios) are not affected by bool fix."""
    assert coerce_value(1.23) == 1.23
    assert coerce_value(0.0) == 0.0


def test_exact_one_float_is_not_bool():
    """Float 1.0 (a real ratio value) must NOT become 'True'."""
    result = coerce_value(1.0)
    assert result == 1.0
    assert not isinstance(result, str), "1.0 float should not be stringified as 'True'"


def test_none_unchanged():
    assert coerce_value(None) is None


def test_string_unchanged():
    assert coerce_value("some text") == "some text"
