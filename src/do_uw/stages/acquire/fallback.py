"""Fallback chain execution framework for data acquisition.

Provides a generic mechanism for trying multiple data source tiers
in order, downgrading confidence on fallback, and logging which tier
succeeded. Used by all data acquisition clients.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from do_uw.models.common import Confidence

logger = logging.getLogger(__name__)


@dataclass
class FallbackTier:
    """A single tier in a fallback chain.

    Attributes:
        name: Human-readable tier name for logging.
        confidence: Confidence level of data from this tier.
        acquire_fn: Callable that returns data dict or None on failure.
    """

    name: str
    confidence: Confidence
    acquire_fn: Callable[..., dict[str, Any] | None]


class DataAcquisitionError(Exception):
    """Raised when all tiers in a fallback chain fail.

    Attributes:
        source_name: Name of the data source that failed.
        errors: List of error messages from each tier.
    """

    def __init__(self, source_name: str, errors: list[str]) -> None:
        self.source_name = source_name
        self.errors = errors
        super().__init__(
            f"All tiers failed for {source_name}: {errors}"
        )


@dataclass
class FallbackChain:
    """Execute data acquisition through a chain of fallback tiers.

    Tries each tier in order. Returns data from the first tier that
    succeeds (returns non-None). Logs each attempt and result.
    """

    source_name: str
    tiers: list[FallbackTier]
    _errors: list[str] = field(default_factory=lambda: [], init=False)

    def execute(self, **kwargs: Any) -> tuple[dict[str, Any], Confidence, str]:
        """Try each tier until one succeeds.

        Returns:
            Tuple of (data, confidence, tier_name).

        Raises:
            DataAcquisitionError: If all tiers fail.
        """
        self._errors = []
        for tier in self.tiers:
            logger.info(
                "Trying tier '%s' for source '%s'",
                tier.name,
                self.source_name,
            )
            try:
                result = tier.acquire_fn(**kwargs)
                if result is not None:
                    logger.info(
                        "Tier '%s' succeeded for '%s' (confidence=%s)",
                        tier.name,
                        self.source_name,
                        tier.confidence,
                    )
                    return result, tier.confidence, tier.name
                logger.debug(
                    "Tier '%s' returned None for '%s', trying next",
                    tier.name,
                    self.source_name,
                )
            except Exception as exc:
                error_msg = f"{tier.name}: {exc}"
                self._errors.append(error_msg)
                logger.warning(
                    "Tier '%s' failed for '%s': %s",
                    tier.name,
                    self.source_name,
                    exc,
                )

        raise DataAcquisitionError(self.source_name, self._errors)
