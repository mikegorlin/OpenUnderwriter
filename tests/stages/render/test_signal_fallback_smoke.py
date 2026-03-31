"""Smoke test: _signal_fallback module exists and exports all names."""

from do_uw.stages.render.context_builders._signal_fallback import (
    SignalUnavailable,
    safe_get_value,
    safe_get_status,
    safe_get_level,
    safe_get_result,
    safe_get_signals_by_prefix,
)


def test_all_fallback_exports_importable() -> None:
    assert SignalUnavailable is not None
    assert callable(safe_get_value)
    assert callable(safe_get_status)
    assert callable(safe_get_level)
    assert callable(safe_get_result)
    assert callable(safe_get_signals_by_prefix)


def test_signal_unavailable_is_falsy() -> None:
    u = SignalUnavailable("TEST.SIG", "not_found")
    assert not u
