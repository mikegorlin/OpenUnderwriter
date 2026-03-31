"""Format-agnostic context builders for D&O worksheet rendering.

Each module extracts structured data from AnalysisState into template-ready
dicts. Both HTML and Word renderers consume these same context builders.

Modules:
  company           - Company profile + executive summary (from _narrative.py)
  financials        - Income statement extraction (from _financial_income.py)
  financials_balance - Balance sheet helpers (from _financial_balance.py, private)
  market            - Market data + insider activity (from _tables.py)
  governance        - Board + leadership extraction (from _governance.py)
  litigation        - Litigation landscape (from _ext.py)
  scoring           - Risk scoring + AI risk + meeting questions (from _scoring.py)
  analysis          - Classification, hazard, composites, NLP, peril map (from _analysis.py)
  calibration       - Brain calibration notes (from _calibration.py)
  pattern_context   - Pattern engine firing panel (Phase 109)
"""

from do_uw.stages.render.context_builders.analysis import (
    extract_classification,
    extract_executive_risk,
    extract_forensic_composites,
    extract_hazard_profile,
    extract_nlp_signals,
    extract_peril_map,
    extract_risk_factors,
    extract_temporal_signals,
)
from do_uw.stages.render.context_builders.calibration import (
    render_calibration_notes,
)
from do_uw.stages.render.context_builders.company import (
    extract_business_model,
    extract_company,
    extract_exec_summary,
    extract_ten_k_yoy,
)
from do_uw.stages.render.context_builders.financials import (
    extract_financials,
    extract_peer_matrix,
    find_line_item_value,
)
from do_uw.stages.render.context_builders.governance import (
    extract_governance,
)
from do_uw.stages.render.context_builders.litigation import (
    extract_litigation,
)
from do_uw.stages.render.context_builders.market import (
    dim_display_name,
    extract_market,
)
from do_uw.stages.render.context_builders.narrative import (
    extract_do_implications,
    extract_scr_narratives,
    extract_section_narratives,
)
from do_uw.stages.render.context_builders._bull_bear import (
    extract_bull_bear_cases,
)
from do_uw.stages.render.context_builders.chart_thresholds import (
    extract_chart_thresholds,
)
from do_uw.stages.render.context_builders.adversarial_context import (
    build_adversarial_context,
)
from do_uw.stages.render.context_builders.pattern_context import (
    build_pattern_context,
)
from do_uw.stages.render.context_builders.scoring import (
    extract_ai_risk,
    extract_meeting_questions,
    extract_scoring,
)
from do_uw.stages.render.context_builders.hae_context import (
    build_hae_context,
)
from do_uw.stages.render.context_builders.assembly_registry import (
    build_html_context,
)

__all__ = [
    "build_html_context",
    "build_adversarial_context",
    "build_hae_context",
    "build_pattern_context",
    "dim_display_name",
    "extract_ai_risk",
    "extract_business_model",
    "extract_bull_bear_cases",
    "extract_chart_thresholds",
    "extract_classification",
    "extract_company",
    "extract_do_implications",
    "extract_exec_summary",
    "extract_executive_risk",
    "extract_financials",
    "extract_forensic_composites",
    "extract_governance",
    "extract_hazard_profile",
    "extract_litigation",
    "extract_market",
    "extract_meeting_questions",
    "extract_nlp_signals",
    "extract_peer_matrix",
    "extract_peril_map",
    "extract_risk_factors",
    "extract_scoring",
    "extract_scr_narratives",
    "extract_section_narratives",
    "extract_ten_k_yoy",
    "extract_temporal_signals",
    "find_line_item_value",
    "render_calibration_notes",
]
