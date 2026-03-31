"""Company context builder re-export shim.

Backward-compatible re-exports from the 6 focused company_*.py modules.
All imports from this module continue to work unchanged.
"""

from do_uw.stages.render.context_builders.company_business_model import (
    extract_business_model,
)
from do_uw.stages.render.context_builders.company_environment import (
    _build_environment_assessment,
    _build_sector_risk,
    _format_env_signal,
)
from do_uw.stages.render.context_builders.company_events import (
    _build_corporate_events,
    extract_ten_k_yoy,
)
from do_uw.stages.render.context_builders.company_exec_summary import (
    extract_exec_summary,
)
from do_uw.stages.render.context_builders.company_operations import (
    _build_operational_complexity,
    _build_structural_complexity,
)
from do_uw.stages.render.context_builders.company_profile import (
    _get_yfinance_sector,
    _lookup_gics_name,
    extract_company,
)

__all__ = [
    "_build_corporate_events",
    "_build_environment_assessment",
    "_build_operational_complexity",
    "_build_sector_risk",
    "_build_structural_complexity",
    "_format_env_signal",
    "_get_yfinance_sector",
    "_lookup_gics_name",
    "extract_business_model",
    "extract_company",
    "extract_exec_summary",
    "extract_ten_k_yoy",
]
