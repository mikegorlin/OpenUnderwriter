"""Brain DuckDB schema + Pydantic YAML validation models.

DuckDB is a runtime query cache rebuilt from YAML via ``brain build``.
19 tables, 11 views. See _TABLES_DDL, _VIEWS_DDL, _INDEXES_DDL.

Pydantic models (Phase 103 - Schema Foundation):
- PatternDefinition: validates pattern definition YAML files
- ChartTemplate: validates chart_registry.yaml entries
- SeverityAmplifier: validates severity amplifier YAML files
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import os

import duckdb
from pydantic import BaseModel, ConfigDict, Field

from do_uw.brain.brain_signal_schema import Epistemology


def get_brain_db_path() -> Path:
    """Return default path to brain.duckdb (alongside signals.json).

    Respects DO_UW_BRAIN_DB_PATH env var for testing isolation.
    """
    override = os.environ.get("DO_UW_BRAIN_DB_PATH")
    if override:
        return Path(override)
    return Path(__file__).parent / "brain.duckdb"


def connect_brain_db(path: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    """Connect to brain DuckDB, creating if not exists."""
    if path is None:
        path = get_brain_db_path()
    return duckdb.connect(str(path))


_TABLES_DDL = """
CREATE SEQUENCE IF NOT EXISTS changelog_seq START 1;

CREATE TABLE IF NOT EXISTS brain_signals (
    signal_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    lifecycle_state VARCHAR NOT NULL,
    depth INTEGER NOT NULL DEFAULT 2,
    execution_mode VARCHAR NOT NULL DEFAULT 'AUTO',
    report_section VARCHAR NOT NULL,
    risk_questions VARCHAR[] NOT NULL,
    risk_framework_layer VARCHAR NOT NULL,
    factors VARCHAR[],
    hazards VARCHAR[],
    characteristic_direction VARCHAR,
    characteristic_strength VARCHAR,
    threshold_type VARCHAR NOT NULL,
    threshold_red VARCHAR,
    threshold_yellow VARCHAR,
    threshold_clear VARCHAR,
    pattern_ref VARCHAR,
    question VARCHAR NOT NULL,
    rationale TEXT,
    interpretation TEXT,
    field_key VARCHAR,
    required_data VARCHAR[],
    data_locations JSON,
    acquisition_type VARCHAR,
    extraction_hints JSON,
    industry_scope VARCHAR NOT NULL DEFAULT 'universal',
    applicable_industries VARCHAR[],
    industry_threshold_overrides JSON,
    expected_fire_rate FLOAT,
    last_calibrated DATE,
    calibration_notes TEXT,
    pillar VARCHAR,
    category VARCHAR,
    signal_type VARCHAR,
    hazard_or_signal VARCHAR,
    plaintiff_lenses VARCHAR[],
    claims_correlation FLOAT,
    amplifier VARCHAR,
    amplifier_bonus_points FLOAT,
    tier INTEGER,
    section_number INTEGER,
    sector_adjustments JSON,
    v6_subsection_ids VARCHAR[],
    data_strategy JSON,
    threshold_full JSON,
    peril_id VARCHAR,
    chain_ids VARCHAR[],
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',
    change_description TEXT,
    retired_at TIMESTAMP,
    retired_reason TEXT,
    PRIMARY KEY (signal_id, version)
);

CREATE TABLE IF NOT EXISTS brain_taxonomy (
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    parent_id VARCHAR,
    weight FLOAT,
    domain VARCHAR,
    aggregation_method VARCHAR,
    frequency_trend VARCHAR,
    severity_range VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (entity_type, entity_id, version)
);

CREATE TABLE IF NOT EXISTS brain_backlog (
    backlog_id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    underwriting_question TEXT,
    risk_questions VARCHAR[],
    hazards VARCHAR[],
    rationale TEXT NOT NULL,
    source VARCHAR,
    gap_reference VARCHAR,
    priority VARCHAR NOT NULL DEFAULT 'MEDIUM',
    priority_rationale TEXT,
    estimated_effort VARCHAR,
    data_sources_needed TEXT,
    data_available BOOLEAN DEFAULT FALSE,
    data_gap_notes TEXT,
    status VARCHAR NOT NULL DEFAULT 'OPEN',
    promoted_to_signal_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS brain_changelog (
    changelog_id INTEGER DEFAULT nextval('changelog_seq'),
    signal_id VARCHAR NOT NULL,
    old_version INTEGER,
    new_version INTEGER NOT NULL,
    change_type VARCHAR NOT NULL,
    change_description TEXT NOT NULL,
    fields_changed VARCHAR[],
    changed_by VARCHAR NOT NULL DEFAULT 'system',
    changed_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    change_reason TEXT,
    triggered_by VARCHAR,
    PRIMARY KEY (changelog_id)
);

CREATE TABLE IF NOT EXISTS brain_effectiveness (
    signal_id VARCHAR NOT NULL,
    measurement_period VARCHAR NOT NULL,
    total_evaluations INTEGER NOT NULL DEFAULT 0,
    red_count INTEGER NOT NULL DEFAULT 0,
    yellow_count INTEGER NOT NULL DEFAULT 0,
    clear_count INTEGER NOT NULL DEFAULT 0,
    info_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    not_available_count INTEGER NOT NULL DEFAULT 0,
    discrimination_power FLOAT,
    override_count INTEGER NOT NULL DEFAULT 0,
    override_direction VARCHAR[],
    override_reasons TEXT[],
    companies_with_claims INTEGER DEFAULT 0,
    companies_flagged_before_claim INTEGER DEFAULT 0,
    companies_cleared_before_claim INTEGER DEFAULT 0,
    flagged_always_fires BOOLEAN DEFAULT FALSE,
    flagged_never_fires BOOLEAN DEFAULT FALSE,
    flagged_high_skip BOOLEAN DEFAULT FALSE,
    flagged_low_discrimination BOOLEAN DEFAULT FALSE,
    computed_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    run_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (signal_id, measurement_period)
);

CREATE TABLE IF NOT EXISTS brain_industry (
    industry_code VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR NOT NULL,
    sic_codes VARCHAR[],
    naics_codes VARCHAR[],
    sector_etf VARCHAR,
    alternative_etf VARCHAR,
    base_sca_rate FLOAT,
    base_risk_level VARCHAR,
    typical_claim_types VARCHAR[],
    threshold_overrides JSON,
    baseline_short_interest JSON,
    baseline_volatility JSON,
    baseline_leverage JSON,
    supplement_signal_ids VARCHAR[],
    priority_modules VARCHAR[],
    operating_metrics JSON,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (industry_code, version)
);

CREATE TABLE IF NOT EXISTS brain_signal_runs (
    run_id VARCHAR NOT NULL,
    signal_id VARCHAR NOT NULL,
    signal_version INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    value VARCHAR,
    evidence TEXT,
    ticker VARCHAR NOT NULL,
    run_date TIMESTAMP NOT NULL,
    is_backtest BOOLEAN DEFAULT FALSE,
    industry_code VARCHAR,
    threshold_was_adjusted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (run_id, signal_id)
);

CREATE SEQUENCE IF NOT EXISTS feedback_seq START 1;
CREATE TABLE IF NOT EXISTS brain_feedback (
    feedback_id INTEGER PRIMARY KEY DEFAULT nextval('feedback_seq'),
    ticker VARCHAR,
    signal_id VARCHAR,
    run_id VARCHAR,
    feedback_type VARCHAR NOT NULL,
    direction VARCHAR,
    note TEXT NOT NULL,
    reviewer VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    applied_at TIMESTAMP,
    applied_change_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE SEQUENCE IF NOT EXISTS proposal_seq START 1;
CREATE TABLE IF NOT EXISTS brain_proposals (
    proposal_id INTEGER PRIMARY KEY DEFAULT nextval('proposal_seq'),
    source_type VARCHAR NOT NULL,
    source_ref VARCHAR,
    signal_id VARCHAR,
    proposal_type VARCHAR NOT NULL,
    proposed_check JSON,
    proposed_changes JSON,
    backtest_results JSON,
    rationale TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    reviewed_by VARCHAR,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS brain_correlations (
    signal_a VARCHAR NOT NULL,
    signal_b VARCHAR NOT NULL,
    co_fire_count INTEGER NOT NULL,
    co_fire_rate FLOAT NOT NULL,
    a_fire_count INTEGER NOT NULL,
    b_fire_count INTEGER NOT NULL,
    correlation_type VARCHAR NOT NULL,
    above_threshold BOOLEAN NOT NULL DEFAULT TRUE,
    discovered_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (signal_a, signal_b)
);

CREATE TABLE IF NOT EXISTS brain_scoring_factors (
    factor_id VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR NOT NULL,
    max_points INTEGER NOT NULL,
    weight_pct FLOAT NOT NULL,
    description TEXT,
    confidence VARCHAR,
    historical_lift FLOAT,
    rules JSON NOT NULL,
    modifiers JSON,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',
    PRIMARY KEY (factor_id, version)
);

CREATE TABLE IF NOT EXISTS brain_scoring_meta (
    meta_key VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    meta_json JSON NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (meta_key, version)
);

CREATE TABLE IF NOT EXISTS brain_patterns (
    pattern_id VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    description TEXT,
    trigger_conditions JSON NOT NULL,
    severity_modifiers JSON,
    score_impact JSON NOT NULL,
    component_signals VARCHAR[],
    allegation_types VARCHAR[],
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',
    PRIMARY KEY (pattern_id, version)
);

CREATE TABLE IF NOT EXISTS brain_red_flags (
    flag_id VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR NOT NULL,
    condition TEXT NOT NULL,
    max_tier VARCHAR NOT NULL,
    max_quality_score INTEGER NOT NULL,
    source_signal VARCHAR,
    action TEXT,
    auto_decline BOOLEAN DEFAULT FALSE,
    extra JSON,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by VARCHAR NOT NULL DEFAULT 'system',
    PRIMARY KEY (flag_id, version)
);

CREATE TABLE IF NOT EXISTS brain_sectors (
    metric_name VARCHAR NOT NULL,
    sector_code VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    data JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (metric_name, sector_code, version)
);

CREATE TABLE IF NOT EXISTS brain_config (
    config_key VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    config_json JSON NOT NULL,
    source_file VARCHAR,
    file_hash VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (config_key, version)
);

CREATE TABLE IF NOT EXISTS brain_meta (
    meta_key VARCHAR PRIMARY KEY,
    meta_value VARCHAR NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS brain_perils (
    peril_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    haz_codes VARCHAR[],
    frequency VARCHAR,
    severity VARCHAR,
    typical_settlement_range VARCHAR,
    key_drivers VARCHAR[],
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS brain_causal_chains (
    chain_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    peril_id VARCHAR,
    description TEXT,
    trigger_signals VARCHAR[],
    amplifier_signals VARCHAR[],
    mitigator_signals VARCHAR[],
    evidence_signals VARCHAR[],
    frequency_factors VARCHAR[],
    severity_factors VARCHAR[],
    patterns VARCHAR[],
    red_flags VARCHAR[],
    historical_filing_rate FLOAT,
    median_severity_usd FLOAT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS brain_risk_framework (
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    legacy_id VARCHAR,
    name VARCHAR NOT NULL,
    description TEXT,
    sort_order INTEGER,
    metadata JSON,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS brain_shadow_evaluations (
    run_id VARCHAR NOT NULL,
    signal_id VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    v1_status VARCHAR NOT NULL,
    v1_threshold_level VARCHAR,
    v1_value VARCHAR,
    v2_status VARCHAR NOT NULL,
    v2_threshold_level VARCHAR,
    v2_value VARCHAR,
    is_match BOOLEAN NOT NULL,
    discrepancy_detail TEXT,
    evaluated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (run_id, signal_id)
);
"""

_VIEWS_DDL = """
CREATE OR REPLACE VIEW brain_signals_current AS
SELECT * FROM brain_signals
WHERE (signal_id, version) IN (
    SELECT signal_id, MAX(version) FROM brain_signals GROUP BY signal_id
);
CREATE OR REPLACE VIEW brain_signals_active AS
SELECT * FROM brain_signals_current
WHERE lifecycle_state NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE', 'DEPRECATED', 'ARCHIVED');
CREATE OR REPLACE VIEW brain_taxonomy_current AS
SELECT * FROM brain_taxonomy
WHERE (entity_type, entity_id, version) IN (
    SELECT entity_type, entity_id, MAX(version)
    FROM brain_taxonomy GROUP BY entity_type, entity_id
);
CREATE OR REPLACE VIEW brain_scoring_factors_current AS
SELECT * FROM brain_scoring_factors
WHERE (factor_id, version) IN (
    SELECT factor_id, MAX(version) FROM brain_scoring_factors GROUP BY factor_id
);
CREATE OR REPLACE VIEW brain_scoring_meta_current AS
SELECT * FROM brain_scoring_meta
WHERE (meta_key, version) IN (
    SELECT meta_key, MAX(version) FROM brain_scoring_meta GROUP BY meta_key
);
CREATE OR REPLACE VIEW brain_patterns_current AS
SELECT * FROM brain_patterns
WHERE (pattern_id, version) IN (
    SELECT pattern_id, MAX(version) FROM brain_patterns GROUP BY pattern_id
);
CREATE OR REPLACE VIEW brain_red_flags_current AS
SELECT * FROM brain_red_flags
WHERE (flag_id, version) IN (
    SELECT flag_id, MAX(version) FROM brain_red_flags GROUP BY flag_id
);
CREATE OR REPLACE VIEW brain_sectors_current AS
SELECT * FROM brain_sectors
WHERE (metric_name, sector_code, version) IN (
    SELECT metric_name, sector_code, MAX(version)
    FROM brain_sectors GROUP BY metric_name, sector_code
);
CREATE OR REPLACE VIEW brain_config_current AS
SELECT * FROM brain_config
WHERE (config_key, version) IN (
    SELECT config_key, MAX(version) FROM brain_config GROUP BY config_key
);

CREATE OR REPLACE VIEW brain_coverage_matrix AS
SELECT
    t.entity_id as subsection_id,
    t.name as subsection_name,
    p.peril_id,
    p.name as peril_name,
    COUNT(DISTINCT c.signal_id) as total_signals,
    COUNT(DISTINCT CASE WHEN c.content_type = 'EVALUATIVE_CHECK' THEN c.signal_id END) as evaluative_signals,
    COUNT(DISTINCT CASE WHEN c.content_type = 'INFERENCE_PATTERN' THEN c.signal_id END) as pattern_signals,
    CASE
        WHEN COUNT(DISTINCT c.signal_id) >= 5 THEN 'STRONG'
        WHEN COUNT(DISTINCT c.signal_id) >= 2 THEN 'ADEQUATE'
        WHEN COUNT(DISTINCT c.signal_id) >= 1 THEN 'THIN'
        ELSE 'GAP'
    END as coverage_level
FROM brain_taxonomy_current t
CROSS JOIN brain_perils p
LEFT JOIN brain_signals_active c
    ON list_contains(c.risk_questions, t.entity_id)
    AND c.peril_id = p.peril_id
WHERE t.entity_type = 'risk_question'
GROUP BY t.entity_id, t.name, p.peril_id, p.name;

CREATE OR REPLACE VIEW brain_signal_effectiveness AS
SELECT
    cr.signal_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN cr.status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) as fire_count,
    SUM(CASE WHEN cr.status = 'CLEAR' THEN 1 ELSE 0 END) as clear_count,
    SUM(CASE WHEN cr.status = 'SKIPPED' THEN 1 ELSE 0 END) as skip_count,
    ROUND(SUM(CASE WHEN cr.status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) * 1.0
        / NULLIF(COUNT(*), 0), 3) as fire_rate,
    CASE
        WHEN COUNT(*) < 3 THEN 'INSUFFICIENT_DATA'
        WHEN SUM(CASE WHEN cr.status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) * 1.0
            / NULLIF(COUNT(*), 0) > 0.8 THEN 'ALWAYS_FIRES'
        WHEN SUM(CASE WHEN cr.status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) = 0
            THEN 'NEVER_FIRES'
        WHEN SUM(CASE WHEN cr.status IN ('RED', 'YELLOW') THEN 1 ELSE 0 END) * 1.0
            / NULLIF(COUNT(*), 0) BETWEEN 0.05 AND 0.30 THEN 'GOOD_DISCRIMINATION'
        ELSE 'MODERATE'
    END as signal_quality
FROM brain_signal_runs cr
WHERE cr.is_backtest = FALSE
GROUP BY cr.signal_id;
"""

_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_signals_current ON brain_signals(signal_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_signals_section ON brain_signals(report_section);
CREATE INDEX IF NOT EXISTS idx_effectiveness_signal ON brain_effectiveness(signal_id, measurement_period);
CREATE INDEX IF NOT EXISTS idx_runs_ticker ON brain_signal_runs(ticker, run_date);
CREATE INDEX IF NOT EXISTS idx_runs_signal ON brain_signal_runs(signal_id, status);
CREATE INDEX IF NOT EXISTS idx_feedback_ticker ON brain_feedback(ticker);
CREATE INDEX IF NOT EXISTS idx_feedback_signal ON brain_feedback(signal_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON brain_feedback(status);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON brain_proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_signal ON brain_proposals(signal_id);
CREATE INDEX IF NOT EXISTS idx_scoring_factors_id ON brain_scoring_factors(factor_id);
CREATE INDEX IF NOT EXISTS idx_patterns_category ON brain_patterns(category);
CREATE INDEX IF NOT EXISTS idx_red_flags_tier ON brain_red_flags(max_tier);
CREATE INDEX IF NOT EXISTS idx_sectors_metric ON brain_sectors(metric_name);
CREATE INDEX IF NOT EXISTS idx_config_key ON brain_config(config_key);
CREATE INDEX IF NOT EXISTS idx_perils_id ON brain_perils(peril_id);
CREATE INDEX IF NOT EXISTS idx_chains_peril ON brain_causal_chains(peril_id);
CREATE INDEX IF NOT EXISTS idx_framework_type ON brain_risk_framework(entity_type);
CREATE INDEX IF NOT EXISTS idx_shadow_signal ON brain_shadow_evaluations(signal_id);
CREATE INDEX IF NOT EXISTS idx_shadow_match ON brain_shadow_evaluations(is_match);
CREATE INDEX IF NOT EXISTS idx_correlations_rate ON brain_correlations(co_fire_rate DESC);
"""


_COLUMN_MIGRATIONS = """
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS peril_id VARCHAR;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS chain_ids VARCHAR[];
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS work_type VARCHAR;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS acquisition_tier VARCHAR;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS worksheet_section VARCHAR;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS display_when VARCHAR;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS chain_roles JSON;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS unlinked BOOLEAN DEFAULT FALSE;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS provenance JSON;
ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS peril_ids VARCHAR[];
ALTER TABLE brain_feedback ADD COLUMN IF NOT EXISTS reaction_type VARCHAR;
ALTER TABLE brain_feedback ADD COLUMN IF NOT EXISTS severity_target VARCHAR;
ALTER TABLE brain_feedback ADD COLUMN IF NOT EXISTS reaction_rationale TEXT;
"""

def create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all brain tables, views, and indexes.

    Safe to call multiple times (uses IF NOT EXISTS / CREATE OR REPLACE).
    Also runs column migrations for existing tables that predate new columns.
    """
    conn.execute(_TABLES_DDL)
    conn.execute(_COLUMN_MIGRATIONS)
    conn.execute(_VIEWS_DDL)
    conn.execute(_INDEXES_DDL)


# ---------------------------------------------------------------
# Pydantic YAML validation models (Phase 103 - Schema Foundation)
# ---------------------------------------------------------------


class PatternDefinition(BaseModel):
    """Schema for multi-signal risk pattern definitions.

    Patterns combine multiple signals into compound risk indicators
    (e.g., "desperate growth trap" = revenue decline + M&A surge +
    goodwill impairment). Used by Phase 109 pattern YAML files.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Pattern identifier (e.g. 'desperate_growth_trap')")
    name: str = Field(..., description="Human-readable pattern name")
    description: str = Field(..., description="What this pattern detects and why it matters")
    required_signals: list[str] = Field(
        ...,
        description="Signal IDs that must fire for this pattern to activate",
    )
    minimum_matches: int = Field(
        default=3,
        ge=1,
        description="Minimum number of required_signals that must fire",
    )
    recommendation_floor: str | None = Field(
        default=None,
        description="Minimum decision tier when pattern fires (e.g. 'DECLINE', 'REFER')",
    )
    rap_dimensions: list[Literal["host", "agent", "environment"]] = Field(
        ...,
        description="Which H/A/E risk dimensions are involved in this pattern",
    )
    historical_cases: list[str] = Field(
        default_factory=list,
        description="Case references where this pattern was observed (e.g. 'Enron 2001')",
    )
    epistemology: Epistemology | None = Field(
        default=None,
        description="Rule origin and threshold basis for this pattern",
    )


class ChartTemplate(BaseModel):
    """Schema for chart registry entries in chart_registry.yaml.

    Each entry declares a chart's data requirements, signal linkage,
    supported output formats, and rendering function location.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Chart identifier (e.g. 'stock_1y')")
    name: str = Field(..., description="Human-readable chart name")
    module: str = Field(..., description="Python module path containing the render function")
    function: str = Field(..., description="Function name to call for rendering")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters passed to the render function",
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Signal IDs this chart visualizes",
    )
    formats: list[Literal["html", "pdf"]] = Field(
        ...,
        description="Supported output formats",
    )
    data_requires: list[str] = Field(
        default_factory=list,
        description="State paths required for this chart (e.g. 'extracted.market.stock')",
    )
    section: str = Field(..., description="Report section this chart belongs to")
    position: int = Field(..., description="Display order within the section")
    call_style: Literal["standard", "minimal", "radar", "ownership", "timeline"] = Field(
        ...,
        description="Function call signature pattern",
    )
    overlays: list[str] = Field(
        default_factory=list,
        description="Overlay component IDs to render on top of this chart",
    )
    # v7.0 additions
    style_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-chart style overrides (colors, fonts, etc.)",
    )
    golden_reference: str | None = Field(
        default=None,
        description="Path to golden reference image for visual regression testing",
    )


class SeverityAmplifier(BaseModel):
    """Schema for severity amplifier definitions.

    Amplifiers modify the severity score of a signal or pattern when
    certain conditions are met (e.g., media notoriety increases severity
    by 2x). Used by Phase 108 severity model.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Amplifier identifier (e.g. 'media_notoriety')")
    name: str = Field(..., description="Human-readable amplifier name")
    description: str = Field(..., description="What triggers this amplifier and its effect")
    multiplier: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Severity multiplier (1.0 = no change, 5.0 = maximum amplification)",
    )
    trigger_condition: str = Field(
        ...,
        description="Condition that activates this amplifier (human-readable)",
    )
    signal_ids: list[str] = Field(
        default_factory=list,
        description="Signal IDs that can trigger this amplifier",
    )
    rap_class: Literal["host", "agent", "environment"] = Field(
        ...,
        description="H/A/E risk dimension this amplifier belongs to",
    )
    epistemology: Epistemology = Field(
        ...,
        description="Rule origin and threshold basis (required for amplifiers)",
    )
