"""Smoke test: _signal_consumer module exists and exports all names."""

from do_uw.stages.render.context_builders._signal_consumer import (
    SignalResultView,
    get_signal_result,
    get_signal_value,
    get_signal_status,
    get_signal_level,
    get_signals_by_prefix,
    signal_to_display_level,
    get_signal_epistemology,
)


def test_all_exports_importable() -> None:
    assert SignalResultView is not None
    assert callable(get_signal_result)
    assert callable(get_signal_value)
    assert callable(get_signal_status)
    assert callable(get_signal_level)
    assert callable(get_signals_by_prefix)
    assert callable(signal_to_display_level)
    assert callable(get_signal_epistemology)
