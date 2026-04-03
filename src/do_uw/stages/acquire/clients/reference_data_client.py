"""Static reference data acquisition client.

Loads sector classification and risk reference data from brain/config/ YAML/JSON
files for use in sector signal extraction and brain coverage validation.

Files loaded:
- sector_hazard_tiers.yaml
- sector_claim_patterns.yaml
- sector_regulatory_overlay.yaml
- sector_peer_benchmarks.yaml
- sic_gics_mapping.json

These are static reference data (same for all companies) loaded once per analysis.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Cache TTL: 30 days (static data changes rarely).
REFERENCE_DATA_TTL = 30 * 24 * 3600

# Path to brain/config directory.
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "brain" / "config"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from brain/config/."""
    path = _CONFIG_DIR / filename
    return yaml.safe_load(path.read_text())  # type: ignore[no-any-return]


class ReferenceDataClient:
    """Static reference data acquisition client."""

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "reference_data"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Load static reference data files.

        Args:
            state: Analysis state (unused, data is company-independent).
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with keys: sector_hazard_tiers, sector_claim_patterns,
            sector_regulatory_overlay, sector_peer_benchmarks, sic_gics_mapping.
        """
        # Cache key is static (same for all companies).
        cache_key = "reference_data:static"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for reference data")
                return dict(cached)

        logger.info("Loading static reference data from brain/config/")

        result: dict[str, Any] = {}

        try:
            result["sector_hazard_tiers"] = _load_yaml("sector_hazard_tiers.yaml")
        except Exception as exc:
            logger.warning("Failed to load sector_hazard_tiers.yaml: %s", exc)
            result["sector_hazard_tiers"] = {}

        try:
            result["sector_claim_patterns"] = _load_yaml("sector_claim_patterns.yaml")
        except Exception as exc:
            logger.warning("Failed to load sector_claim_patterns.yaml: %s", exc)
            result["sector_claim_patterns"] = {}

        try:
            result["sector_regulatory_overlay"] = _load_yaml("sector_regulatory_overlay.yaml")
        except Exception as exc:
            logger.warning("Failed to load sector_regulatory_overlay.yaml: %s", exc)
            result["sector_regulatory_overlay"] = {}

        try:
            result["sector_peer_benchmarks"] = _load_yaml("sector_peer_benchmarks.yaml")
        except Exception as exc:
            logger.warning("Failed to load sector_peer_benchmarks.yaml: %s", exc)
            result["sector_peer_benchmarks"] = {}

        try:
            path = _CONFIG_DIR / "sic_gics_mapping.json"
            result["sic_gics_mapping"] = json.loads(path.read_text())
        except Exception as exc:
            logger.warning("Failed to load sic_gics_mapping.json: %s", exc)
            result["sic_gics_mapping"] = {}

        # Cache on success.
        if cache is not None and result:
            cache.set(
                cache_key,
                result,
                source="reference_data",
                ttl=REFERENCE_DATA_TTL,
            )

        return result
