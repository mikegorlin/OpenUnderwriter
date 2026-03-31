"""Null-safe chart decorator and placeholder generator.

Provides crash-proof wrappers for chart builders so that missing or
incomplete data results in None (or a gray placeholder image) instead
of an unhandled exception that kills the render pipeline.

Exports:
    null_safe_chart: Decorator that catches data-related exceptions.
    create_chart_placeholder: Generates a gray PNG with centered text.
"""

from __future__ import annotations

import functools
import io
import logging
from typing import Any, Callable, TypeVar

import matplotlib
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

T = TypeVar("T")


def null_safe_chart(fn: Callable[..., T]) -> Callable[..., T | None]:
    """Decorator: catches data-related exceptions and returns None.

    Wraps chart builder functions so that missing data (None attributes,
    bad types, missing keys) results in a logged warning + None return
    instead of a crash that breaks the entire worksheet render.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> T | None:
        try:
            return fn(*args, **kwargs)
        except (AttributeError, TypeError, KeyError, IndexError, ValueError) as exc:
            logger.warning(
                "Chart %s skipped (missing data): %s", fn.__name__, exc
            )
            return None

    return wrapper


def create_chart_placeholder(
    width: int = 800,
    height: int = 400,
    label: str = "No data available",
) -> io.BytesIO:
    """Gray placeholder PNG with centered text for missing chart data.

    Returns a BytesIO buffer containing a valid PNG image that can be
    embedded in place of a chart when the underlying data is missing.
    """
    fig, ax = plt.subplots(figsize=(width / 100, height / 100))
    ax.set_facecolor("#E5E7EB")
    ax.text(
        0.5,
        0.5,
        label,
        ha="center",
        va="center",
        fontsize=14,
        color="#6B7280",
        transform=ax.transAxes,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#E5E7EB")
    plt.close(fig)
    buf.seek(0)
    return buf


__all__ = ["create_chart_placeholder", "null_safe_chart"]
