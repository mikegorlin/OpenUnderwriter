"""Brain migration: signals.json -> brain.duckdb.

Migrates all 388 signals from signals.json into brain_signals as version 1.
Populates brain_taxonomy with 45 v6 risk question subsections (X.Y format),
10 scoring factors (F1-F10), 15 hazard codes (HAZ-*), and 5 v6 report sections.
Seeds brain_backlog with 7 gap items from BRAIN-DESIGN.md Phase C.

After migration, runs enrichment (version 2) and v6 remap validation.

Non-destructive by default: only inserts rows not already present.
Use force_clean=True for a full reset.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import duckdb
import yaml

from do_uw.brain.brain_schema import connect_brain_db, create_schema

# Prefix -> report_section mapping (v6: 5 sections)
_PREFIX_TO_SECTION = {
    "BIZ": "company",
    "FIN": "financial",
    "GOV": "governance",
    "EXEC": "governance",
    "LIT": "litigation",
    "STOCK": "market",
    "NLP": "governance",      # disclosure merged into governance (Section 4) in v6
    "FWRD": "company",        # forward-looking maps to company risk calendar (1.11) in v6
}


def _get_checks_json_path() -> Path:
    """Return path to signals.json."""
    return Path(__file__).parent / "config" / "signals.json"


def load_signals_from_yaml(checks_dir: Path) -> list[dict]:
    """Load all signals from checks/**/*.yaml glob. Returns flat list of check dicts."""
    all_checks: list[dict] = []
    pattern = str(checks_dir / "**" / "*.yaml")
    for yaml_file in sorted(glob.glob(pattern, recursive=True)):
        data = yaml.safe_load(Path(yaml_file).read_text())
        if isinstance(data, list):
            all_checks.extend(data)
        elif isinstance(data, dict) and "signals" in data:
            all_checks.extend(data["signals"])
    return all_checks


def _alter_add_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Add columns that may not exist in older brain.duckdb files."""
    new_cols = [
        ("extraction_hints", "JSON"),
        ("pillar", "VARCHAR"),
        ("category", "VARCHAR"),
        ("signal_type", "VARCHAR"),
        ("hazard_or_signal", "VARCHAR"),
        ("plaintiff_lenses", "VARCHAR[]"),
        ("claims_correlation", "FLOAT"),
        ("amplifier", "VARCHAR"),
        ("amplifier_bonus_points", "FLOAT"),
        ("tier", "INTEGER"),
        ("section_number", "INTEGER"),
        ("sector_adjustments", "JSON"),
        ("v6_subsection_ids", "VARCHAR[]"),
        ("data_strategy", "JSON"),
        ("threshold_full", "JSON"),
        # Phase 42: framework tagging
        ("peril_id", "VARCHAR"),
        ("chain_ids", "VARCHAR[]"),
    ]
    for col_name, col_type in new_cols:
        try:
            conn.execute(
                f"ALTER TABLE brain_signals ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
        except duckdb.CatalogException:
            pass


def _determine_lifecycle_state(check: dict) -> str:
    """Determine lifecycle state from check properties."""
    content_type = check.get("content_type", "EVALUATIVE_CHECK")

    if content_type == "MANAGEMENT_DISPLAY":
        return "MONITORING"

    # Check if threshold has real criteria
    threshold = check.get("threshold", {})
    red = threshold.get("red", "")
    yellow = threshold.get("yellow", "")

    # Placeholder checks have no meaningful threshold criteria
    if not red and not yellow:
        return "INVESTIGATION"

    # Checks with actual criteria are SCORING
    if red or yellow:
        return "SCORING"

    return "INVESTIGATION"


def _extract_threshold(check: dict, level: str) -> str | None:
    """Extract threshold criterion text for a given level."""
    threshold = check.get("threshold", {})
    return threshold.get(level)


# ---------------------------------------------------------------------------
# v6 Taxonomy Data: 45 subsections from QUESTIONS-FINAL.md
# ---------------------------------------------------------------------------

_V6_SUBSECTIONS: list[tuple[str, str, str, str]] = [
    # Section 1: COMPANY (11 subsections)
    ("1.1", "Identity", "What is this company?", "1"),
    ("1.2", "Business Model & Revenue", "How does this company make money?", "1"),
    ("1.3", "Operations & Dependencies", "What does this company depend on to operate?", "1"),
    ("1.4", "Corporate Structure & Complexity", "How is this company organized?", "1"),
    ("1.5", "Geographic Footprint", "Where does this company operate and what jurisdictional risks exist?", "1"),
    ("1.6", "M&A & Corporate Transactions", "What deal activity has there been and what's pending?", "1"),
    ("1.7", "Competitive Position & Industry Dynamics", "How is this company positioned within its industry?", "1"),
    ("1.8", "Macro & Industry Environment", "What external forces are creating risk?", "1"),
    ("1.9", "Employee & Workforce Signals", "What are employees telling us about the company's health?", "1"),
    ("1.10", "Customer & Product Signals", "What are customers and the market experiencing?", "1"),
    ("1.11", "Risk Calendar & Upcoming Catalysts", "What events are coming in the next policy year?", "1"),
    # Section 2: MARKET (8 subsections)
    ("2.1", "Stock Price Performance", "How has the stock performed?", "2"),
    ("2.2", "Stock Drop Events", "Have there been significant drops that could trigger litigation?", "2"),
    ("2.3", "Volatility & Trading Patterns", "What does trading behavior signal?", "2"),
    ("2.4", "Short Interest & Bearish Signals", "Are sophisticated investors betting against this company?", "2"),
    ("2.5", "Ownership Structure", "Who owns the stock?", "2"),
    ("2.6", "Analyst Coverage & Sentiment", "What do professional analysts think?", "2"),
    ("2.7", "Valuation Metrics", "Is the stock priced appropriately?", "2"),
    ("2.8", "Insider Trading Activity", "Are insiders buying or selling, and is the timing suspicious?", "2"),
    # Section 3: FINANCIAL (8 subsections)
    ("3.1", "Liquidity & Solvency", "Can the company meet its near-term obligations?", "3"),
    ("3.2", "Leverage & Debt Structure", "How much debt does the company carry, and can they service it?", "3"),
    ("3.3", "Profitability & Growth", "Is the business economically viable and growing?", "3"),
    ("3.4", "Earnings Quality & Forensic Analysis", "Are the financial statements trustworthy, or is there manipulation?", "3"),
    ("3.5", "Accounting Integrity & Audit Risk", "Is the financial reporting reliable?", "3"),
    ("3.6", "Financial Distress Indicators", "How close is this company to failure?", "3"),
    ("3.7", "Guidance & Market Expectations", "Is management credible in their forward communications?", "3"),
    ("3.8", "Sector-Specific Financial Metrics", "Which industry-specific financial metrics apply?", "3"),
    # Section 4: GOVERNANCE & DISCLOSURE (9 subsections)
    ("4.1", "Board Composition & Quality", "Is the board structured to provide effective oversight?", "4"),
    ("4.2", "Executive Team & Stability", "Are the right leaders in place, and is the team stable?", "4"),
    ("4.3", "Compensation & Alignment", "Is management incentivized to act in shareholders' interests?", "4"),
    ("4.4", "Shareholder Rights & Protections", "How well are shareholder rights protected?", "4"),
    ("4.5", "Activist Pressure", "Is there activist investor activity creating governance instability?", "4"),
    ("4.6", "Disclosure Quality & Filing Mechanics", "Is the company meeting its disclosure obligations?", "4"),
    ("4.7", "Narrative Analysis & Tone", "What does the language reveal about management's confidence?", "4"),
    ("4.8", "Whistleblower & Investigation Signals", "Are there signals of internal problems?", "4"),
    ("4.9", "Media & External Narrative", "What are external observers seeing?", "4"),
    # Section 5: LITIGATION & REGULATORY (9 subsections)
    ("5.1", "Securities Class Actions (Active)", "Are there current SCAs, and how serious are they?", "5"),
    ("5.2", "Securities Class Action History", "What does the litigation track record tell us?", "5"),
    ("5.3", "Derivative & Merger Litigation", "Are there non-SCA shareholder claims?", "5"),
    ("5.4", "SEC Enforcement", "Where is this company in the SEC enforcement pipeline?", "5"),
    ("5.5", "Other Regulatory & Government", "What non-SEC enforcement exposure exists?", "5"),
    ("5.6", "Non-Securities Litigation", "What is the aggregate non-SCA litigation landscape?", "5"),
    ("5.7", "Defense Posture & Reserves", "How well positioned is the company to defend against claims?", "5"),
    ("5.8", "Litigation Risk Patterns", "What systemic litigation patterns apply?", "5"),
    ("5.9", "Sector-Specific Litigation & Regulatory Patterns", "What sector-specific patterns apply?", "5"),
]

# v6 Section-level entities (5 sections)
_V6_SECTIONS: list[tuple[str, str, str]] = [
    ("company", "Company", "Entity identity, business model, operations, structure, geography, M&A, competitive position, macro environment, employee signals, customer signals, risk calendar"),
    ("market", "Market", "Stock price, volatility, trading patterns, short interest, ownership structure, analyst coverage, valuation, insider trading"),
    ("financial", "Financial", "Liquidity, leverage, profitability, earnings quality, accounting, distress, guidance, sector KPIs"),
    ("governance", "Governance & Disclosure", "Board, executives, compensation, shareholder rights, activists, disclosure, narrative, whistleblower, media"),
    ("litigation", "Litigation & Regulatory", "Securities class actions, SCA history, derivative, SEC enforcement, other regulatory, non-securities, defense, patterns, sector-specific"),
]


def migrate_checks_to_brain(
    conn: duckdb.DuckDBPyConnection | None = None,
    checks_path: Path | None = None,
    *,
    run_enrichment: bool = True,
    force_clean: bool = False,
) -> dict[str, int]:
    """Migrate signals.json into brain DuckDB tables.

    Non-destructive by default: only inserts v1 rows for signal_ids not
    already present. Use force_clean=True for a full reset.

    Args:
        conn: DuckDB connection. If None, connects to default brain.duckdb.
        checks_path: Path to signals.json. Defaults to module-relative.
        run_enrichment: If True, run enrichment + v6 remap after migration.
        force_clean: If True, delete all existing data first (destructive).

    Returns:
        Dict with counts: checks, taxonomy_questions, taxonomy_factors, etc.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()

    # Ensure schema exists
    create_schema(conn)

    # Schema migration: add columns that may not exist in older brain.duckdb files
    _alter_add_columns(conn)

    # Clear existing data only if force_clean requested
    if force_clean:
        conn.execute("DELETE FROM brain_changelog")
        conn.execute("DELETE FROM brain_signals")
        conn.execute("DELETE FROM brain_taxonomy")
        conn.execute("DELETE FROM brain_backlog")

    # Load signals.json
    if checks_path is None:
        checks_path = _get_checks_json_path()
    with open(checks_path) as f:
        data = json.load(f)
    checks = data["signals"]

    # Build rows for batch insert
    rows = []
    for check in checks:
        signal_id = check["id"]
        prefix = signal_id.split(".")[0]
        report_section = _PREFIX_TO_SECTION.get(prefix, "company")
        lifecycle_state = _determine_lifecycle_state(check)

        data_strategy = check.get("data_strategy") or {}
        field_key = data_strategy.get("field_key") or check.get("field_key")

        # Full threshold and data_strategy as JSON for round-trip fidelity
        threshold_obj = check.get("threshold", {})
        data_strategy_obj = check.get("data_strategy")

        rows.append((
            signal_id,
            1,  # version
            check["name"],
            check.get("content_type", "EVALUATIVE_CHECK"),
            lifecycle_state,
            check.get("depth", 2),
            check.get("execution_mode", "AUTO"),
            report_section,
            [],  # risk_questions (enriched later)
            "risk_modifier",  # default framework layer
            check.get("factors", []),
            [],  # hazards (enriched later)
            None,  # characteristic_direction
            None,  # characteristic_strength
            threshold_obj.get("type", "tiered"),
            _extract_threshold(check, "red"),
            _extract_threshold(check, "yellow"),
            _extract_threshold(check, "clear"),
            check.get("pattern_ref"),
            check["name"],  # question (placeholder)
            check.get("rationale"),
            None,  # interpretation
            field_key,
            check.get("required_data", []),
            json.dumps(check.get("data_locations", {})),
            "structured",  # acquisition_type default
            json.dumps(check["extraction_hints"]) if check.get("extraction_hints") else None,
            "universal",  # industry_scope
            None,  # applicable_industries
            None,  # industry_threshold_overrides
            None,  # expected_fire_rate
            None,  # last_calibrated
            None,  # calibration_notes
            # Phase 41 Wave 1: new fields from signals.json
            check.get("pillar"),
            check.get("category"),
            check.get("signal_type"),
            check.get("hazard_or_signal"),
            check.get("plaintiff_lenses", []),
            check.get("claims_correlation"),
            check.get("amplifier"),
            check.get("amplifier_bonus_points"),
            check.get("tier"),
            check.get("section"),  # section_number
            json.dumps(check["sector_adjustments"]) if check.get("sector_adjustments") else None,
            check.get("v6_subsection_ids", []),
            json.dumps(data_strategy_obj) if data_strategy_obj else None,
            json.dumps(threshold_obj) if threshold_obj else None,
            "migration_v1",  # created_by
            None,  # change_description
        ))

    # Non-destructive: filter out signal_ids already present at v1
    if not force_clean:
        existing_ids = {
            r[0]
            for r in conn.execute(
                "SELECT signal_id FROM brain_signals WHERE version = 1"
            ).fetchall()
        }
        rows = [r for r in rows if r[0] not in existing_ids]

    # Batch insert checks (35 original + 14 new = 49 columns)
    if rows:
        conn.executemany(
            """INSERT INTO brain_signals (
                signal_id, version, name, content_type, lifecycle_state,
                depth, execution_mode, report_section, risk_questions,
                risk_framework_layer, factors, hazards,
                characteristic_direction, characteristic_strength,
                threshold_type, threshold_red, threshold_yellow, threshold_clear,
                pattern_ref, question, rationale, interpretation,
                field_key, required_data, data_locations, acquisition_type,
                extraction_hints,
                industry_scope, applicable_industries, industry_threshold_overrides,
                expected_fire_rate, last_calibrated, calibration_notes,
                pillar, category, signal_type, hazard_or_signal,
                plaintiff_lenses, claims_correlation, amplifier,
                amplifier_bonus_points, tier, section_number,
                sector_adjustments, v6_subsection_ids, data_strategy,
                threshold_full,
                created_by, change_description
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )""",
            rows,
        )

    # Populate taxonomy (non-destructive: skip if already populated)
    existing_taxonomy = conn.execute(
        "SELECT COUNT(*) FROM brain_taxonomy"
    ).fetchone()[0]
    if existing_taxonomy == 0 or force_clean:
        # 45 v6 risk question subsections from QUESTIONS-FINAL.md
        for entity_id, name, question, parent_id in _V6_SUBSECTIONS:
            conn.execute(
                """INSERT INTO brain_taxonomy (entity_type, entity_id, name, description, domain, parent_id)
                VALUES ('risk_question', ?, ?, ?, ?, ?)""",
                [entity_id, name, f"v6 subsection {entity_id}: {question}", f"section_{parent_id}", parent_id],
            )

        # 10 factors from scoring.json
        scoring_path = Path(__file__).parent / "config" / "scoring.json"
        with open(scoring_path) as f:
            scoring = json.load(f)
        factor_count = 0
        for _key, factor in scoring["factors"].items():
            fid = factor["factor_id"].replace(".", "")  # "F.1" -> "F1"
            conn.execute(
                """INSERT INTO brain_taxonomy (entity_type, entity_id, name, description, weight)
                VALUES ('factor', ?, ?, ?, ?)""",
                [fid, factor["name"], factor.get("description", factor["name"]),
                 factor.get("weight_pct", 0) / 100.0],
            )
            factor_count += 1

        # 15 hazard codes from BRAIN-DESIGN.md Section 1
        hazards = [
            ("HAZ-SCA", "Securities Class Actions (10b-5)", "stable", "Median settlement $14M; total $4.75B (2024)"),
            ("HAZ-S11", "Section 11 Claims (IPO/offering)", "stable", "Very high; strict liability"),
            ("HAZ-DER", "Shareholder Derivative Suits", "growing", "$1.4B in settlements past 5 years"),
            ("HAZ-SEC", "SEC Enforcement", "stable", "Fines, disgorgement, bars; triggers follow-on litigation"),
            ("HAZ-DOJ", "DOJ Criminal Actions", "stable", "Imprisonment, massive fines"),
            ("HAZ-REG", "Industry-Specific Regulatory", "growing", "State AG enforcement increasing"),
            ("HAZ-BANK", "Bankruptcy/Insolvency Claims", "growing", "Very high; 17 mega-bankruptcies H1 2025"),
            ("HAZ-EMPL", "Employment Claims", "growing", "High frequency, lower severity per claim"),
            ("HAZ-CYBER", "Cyber-Related D&O Claims", "growing", "13.6x SCA risk increase post-breach"),
            ("HAZ-AI", "AI-Related Claims", "growing", "30%+ stock drops triggering fraud claims"),
            ("HAZ-ESG", "ESG/Greenwashing Claims", "growing", "EU penalties up to 10% global turnover"),
            ("HAZ-SPAC", "SPAC/De-SPAC Claims", "declining", "Severity growing, frequency past peak"),
            ("HAZ-ANTITRUST", "Antitrust/Competition", "stable", "Criminal imprisonment, treble damages"),
            ("HAZ-IP", "Intellectual Property", "stable", "Variable"),
            ("HAZ-PRODUCT", "Product Liability Escalation", "stable", "Case-dependent; Boeing, PG&E precedents"),
        ]
        for hid, name, trend, severity in hazards:
            conn.execute(
                """INSERT INTO brain_taxonomy (entity_type, entity_id, name, description, frequency_trend, severity_range)
                VALUES ('hazard', ?, ?, ?, ?, ?)""",
                [hid, name, f"D&O hazard: {name}", trend, severity],
            )

        # 5 v6 report sections
        for sid, name, desc in _V6_SECTIONS:
            conn.execute(
                """INSERT INTO brain_taxonomy (entity_type, entity_id, name, description)
                VALUES ('report_section', ?, ?, ?)""",
                [sid, name, desc],
            )

    # Seed backlog (non-destructive: skip if already populated)
    existing_backlog = conn.execute(
        "SELECT COUNT(*) FROM brain_backlog"
    ).fetchone()[0]
    if existing_backlog == 0 or force_clean:
        backlog_items = [
            ("BL-G1", "SPAC/De-SPAC Detection",
             "5 checks: SPAC identification, de-SPAC timeline, SPAC sponsor analysis, PIPE investor analysis, SPAC-specific risk factors",
             "17% litigation rate for de-SPACs; severity increasing. Critical gap in current system.",
             ["1.1", "1.3"], ["HAZ-SPAC", "HAZ-SCA"], "G1", "L"),
            ("BL-G2", "Going Concern Explicit Flag",
             "Parse auditor's report in 10-K for going concern opinion. Also check 8-K Item 4.02 for non-reliance disclosures.",
             "Going concern is a very strong amplifier for all D&O claim types. Currently not explicitly checked.",
             ["3.1", "3.5"], ["HAZ-BANK", "HAZ-SCA", "HAZ-DER"], "G2", "S"),
            ("BL-G3", "Altman Z-Score",
             "Compute Altman Z-Score from XBRL financial data. Inputs: working capital, retained earnings, EBIT, market cap, total liabilities, revenue, total assets.",
             "Classic bankruptcy predictor. Data already available in XBRL financials. Quick win.",
             ["3.6"], ["HAZ-BANK"], "G3", "S"),
            ("BL-G4", "AGR Score",
             "Compute AGR Score from financial metrics: accruals quality, revenue recognition patterns, off-balance-sheet items.",
             "Research-validated predictor of financial fraud and restatements.",
             ["3.4"], ["HAZ-SCA", "HAZ-SEC"], "G4", "M"),
            ("BL-G5", "Revenue Fraud Pattern Taxonomy",
             "6-8 pattern-specific checks: channel stuffing, bill-and-hold, round-tripping, premature recognition, side agreements, cookie-jar reserves.",
             "Revenue fraud is the #1 cause of financial restatements and securities litigation.",
             ["3.4"], ["HAZ-SCA", "HAZ-SEC", "HAZ-DOJ"], "G5", "L"),
            ("BL-G6", "Derivative Risk Category Assessment",
             "5 category checks: Caremark duty, corporate waste, controlling stockholder self-dealing, books-and-records demand, breach of fiduciary duty.",
             "$1.4B in derivative settlements past 5 years. Expanding via Caremark doctrine.",
             ["5.3", "4.1"], ["HAZ-DER"], "G6", "L"),
            ("BL-G7", "AI-Specific Hazard Checks",
             "7 hazard checks: AI overclaiming/washing, algorithmic bias, AI-generated content liability, deepfake risk, AI safety incidents, EU AI Act compliance, AI patent disputes.",
             "Fastest-growing D&O claim category. 7 (2023) to 15 (2024) to 12 (H1 2025).",
             ["1.3"], ["HAZ-AI", "HAZ-SCA", "HAZ-REG"], "G7", "M"),
        ]
        for bid, title, desc, rationale, rqs, hzs, gap_ref, effort in backlog_items:
            conn.execute(
                """INSERT INTO brain_backlog (
                    backlog_id, title, description, rationale,
                    risk_questions, hazards,
                    priority, gap_reference, estimated_effort, source, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, 'HIGH', ?, ?, 'BRAIN-DESIGN.md', 'migration_v1')""",
                [bid, title, desc, rationale, rqs, hzs, gap_ref, effort],
            )

    # Run enrichment + v6 remap if requested (skip if v2+ already exists)
    if run_enrichment:
        max_version = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM brain_signals"
        ).fetchone()[0]
        if max_version < 2 or force_clean:
            from do_uw.brain.brain_enrich import enrich_brain_signals, remap_to_v6
            enrich_brain_signals(conn)
            remap_to_v6(conn)

    signal_count = conn.execute("SELECT COUNT(*) FROM brain_signals_current").fetchone()[0]
    backlog_count = conn.execute("SELECT COUNT(*) FROM brain_backlog").fetchone()[0]

    # Count taxonomy entities by type
    q_count = conn.execute(
        "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'risk_question'"
    ).fetchone()[0]
    f_count = conn.execute(
        "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'factor'"
    ).fetchone()[0]
    h_count = conn.execute(
        "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'hazard'"
    ).fetchone()[0]
    s_count = conn.execute(
        "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'report_section'"
    ).fetchone()[0]

    if own_conn:
        conn.close()

    return {
        "signals": signal_count,
        "taxonomy_questions": q_count,
        "taxonomy_factors": f_count,
        "taxonomy_hazards": h_count,
        "taxonomy_sections": s_count,
        "backlog": backlog_count,
    }
