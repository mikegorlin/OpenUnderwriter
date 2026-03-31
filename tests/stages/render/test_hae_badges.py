"""Tests for H/A/E badge macro rendering (Phase 114-02)."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

import pytest


@pytest.fixture()
def jinja_env() -> Environment:
    """Create Jinja2 env with template dir."""
    return Environment(loader=FileSystemLoader("src/do_uw/templates/html"))


def _render_badge(jinja_env: Environment, dimensions: list[str]) -> str:
    """Render the hae_badge macro with given dimensions."""
    tmpl_str = (
        '{% from "components/hae_badge.html.j2" import hae_badge %}'
        "{{ hae_badge(dims) }}"
    )
    tmpl = jinja_env.from_string(tmpl_str)
    return tmpl.render(dims=dimensions)


def test_host_badge(jinja_env: Environment) -> None:
    """Host badge renders with hae-host class and 'H' text."""
    html = _render_badge(jinja_env, ["host"])
    assert "hae-host" in html
    assert ">H<" in html


def test_agent_badge(jinja_env: Environment) -> None:
    """Agent badge renders with hae-agent class and 'A' text."""
    html = _render_badge(jinja_env, ["agent"])
    assert "hae-agent" in html
    assert ">A<" in html


def test_environment_badge(jinja_env: Environment) -> None:
    """Environment badge renders with hae-environment class and 'E' text."""
    html = _render_badge(jinja_env, ["environment"])
    assert "hae-environment" in html
    assert ">E<" in html


def test_multiple_badges(jinja_env: Environment) -> None:
    """Multiple dimensions render multiple badges."""
    html = _render_badge(jinja_env, ["host", "agent", "environment"])
    assert "hae-host" in html
    assert "hae-agent" in html
    assert "hae-environment" in html
    assert html.count("hae-badge") == 3


def test_shorthand_badges(jinja_env: Environment) -> None:
    """Shorthand dimension letters ('h', 'a', 'e') also work."""
    html = _render_badge(jinja_env, ["h", "a", "e"])
    assert "hae-host" in html
    assert "hae-agent" in html
    assert "hae-environment" in html


def test_empty_dimensions(jinja_env: Environment) -> None:
    """Empty dimensions list renders nothing."""
    html = _render_badge(jinja_env, [])
    assert "hae-badge" not in html
