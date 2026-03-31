# Knowledge System Architecture

## Overview

The D&O underwriting worksheet system uses a layered knowledge architecture to evaluate companies against 359+ risk checks, detect composite risk patterns, assign quality scores, and produce underwriting recommendations. This document explains how knowledge is organized, how it flows through the pipeline, how checks are added and improved, how calibration parameters change, and how intent is preserved across modifications.

The knowledge system has three layers:

1. **Brain files** (`src/do_uw/brain/`) -- flat JSON files containing the original domain knowledge
2. **Knowledge store** (`src/do_uw/knowledge/`) -- SQLAlchemy ORM database providing queryable, versionable access
3. **Config files** (`src/do_uw/config/`) -- operational parameters (scoring weights, thresholds, industry theories)

---

## 1. Knowledge Organization

### 1.1 Brain Directory (`src/do_uw/brain/`)

The `brain/` directory contains 5 JSON files that represent the original domain knowledge migrated from the predecessor system. These files are the **source of truth for initial migration** into the knowledge store.

| File | Contents | Records |
|------|----------|---------|
| `checks.json` | 359 D&O risk checks organized by section (1-7) and pillar | 359 checks |
| `scoring.json` | 10-factor scoring weights, rules, tier boundaries | 10 factors, ~70 rules |
| `patterns.json` | 17 composite risk patterns with trigger conditions | 17 patterns |
| `red_flags.json` | Critical red flag escalation triggers with score ceilings | ~10 CRF gates |
| `sectors.json` | Sector-specific baselines for contextual scoring | 10 metric sections |

**Example check from `checks.json`:**

```json
{
  "id": "BIZ.CLASS.primary",
  "name": "Primary D&O Risk Classification",
  "section": 2,
  "pillar": "BUSINESS_PROFILE",
  "required_data": ["SEC_10K", "MARKET_PRICE"],
  "data_locations": {
    "SEC_10K": ["item_1_business", "cover_page"],
    "MARKET_PRICE": ["market_cap"]
  },
  "threshold": { "type": "qualitative" },
  "factors": ["F1"]
}
```

Each check specifies:
- **What data it needs** (`required_data`: data source IDs like `SEC_10K`, `MARKET_PRICE`)
- **Where in the data to look** (`data_locations`: maps sources to sub-paths)
- **How to evaluate** (`threshold`: type + value for numeric, qualitative for expert judgment)
- **What scoring factor it feeds** (`factors`: scoring factor IDs like `F1`, `F3`)

### 1.2 Knowledge Store (`src/do_uw/knowledge/`)

The knowledge store is a SQLAlchemy 2.0 ORM backed by SQLite (`knowledge.db`). It provides the **runtime source of truth** after migration from brain/ JSON files.

**ORM Models** (defined in `src/do_uw/knowledge/models.py`):

| Model | Table | Purpose |
|-------|-------|---------|
| `Check` | `checks` | Primary check registry with lifecycle tracking |
| `CheckHistory` | `check_history` | Audit trail for every field change |
| `Pattern` | `patterns` | Composite risk patterns |
| `ScoringRule` | `scoring_rules` | Factor scoring rules (condition -> points) |
| `RedFlag` | `red_flags` | Critical red flag gates with score ceilings |
| `Sector` | `sectors` | Per-sector baseline metrics |
| `Note` | `notes` | Free-form knowledge artifacts with FTS5 search |
| `IndustryPlaybook` | `industry_playbooks` | Industry-vertical-specific check sets |

**Key Check model fields:**

```
id              -- Unique check identifier (e.g., "FIN.ACCT.restatement")
name            -- Human-readable description
section         -- Output section number (1-7)
pillar          -- Knowledge pillar (FINANCIAL_REPORTING, GOVERNANCE, etc.)
status          -- Lifecycle state (INCUBATING, DEVELOPING, ACTIVE, DEPRECATED)
required_data   -- JSON list of data source IDs
data_locations  -- JSON dict/list mapping sources to sub-paths
scoring_factor  -- Factor ID this check feeds (e.g., "F1")
origin          -- How created (BRAIN_MIGRATION, USER_ADDED, AI_GENERATED, PLAYBOOK)
version         -- Auto-incrementing version number
```

**Full-Text Search:** The store supports FTS5 for searching checks and notes. When FTS5 is unavailable at runtime, it falls back to SQL LIKE queries. FTS5 tables are standalone (not content-synced) with rebuild-on-search for reliable indexing.

### 1.3 Config Files (`src/do_uw/config/`)

Config files contain **operational parameters** that control pipeline behavior. Unlike brain/ files (which contain domain knowledge), config files contain tuning parameters and reference data.

| File | Purpose |
|------|---------|
| `activist_investors.json` | Known activist investor names for matching |
| `actuarial.json` | Actuarial pricing parameters (loss rates, defense costs) |
| `adverse_events.json` | Adverse event classification patterns |
| `ai_risk_weights.json` | AI transformation risk scoring weights |
| `claim_types.json` | D&O claim type taxonomy |
| `governance_weights.json` | 7 governance dimension weights (0-10 each) |
| `industry_theories.json` | Industry-specific litigation theories |
| `lead_counsel_tiers.json` | Plaintiff law firm tier rankings |
| `rate_decay.json` | Rate decay parameters for pricing data aging |
| `tax_havens.json` | Known tax haven jurisdictions |
| `xbrl_concepts.json` | XBRL tag-to-concept mappings |

### 1.4 Relationship Between Layers

```
brain/ (JSON source files)         config/ (operational parameters)
  |                                     |
  | migrate.py                          | loaded directly by stages
  v                                     v
knowledge.db (SQLAlchemy ORM)    +---> stages/analyze/
  |                              |     stages/score/
  | compat_loader.py             |     stages/extract/
  v                              |     stages/benchmark/
BrainConfig (Pydantic) ----------+
  |
  +--> AnalyzeStage.run()   (checks, scoring, patterns, sectors, red_flags)
  +--> ScoreStage.run()     (scoring, red_flags, patterns, sectors)
```

The `BackwardCompatLoader` (`src/do_uw/knowledge/compat_loader.py`) is the bridge between old and new. It reads from the knowledge store but returns the **exact same dict structures** that the original `ConfigLoader` returned from brain/ JSON files. This means existing ANALYZE and SCORE stages work identically with either loader -- zero code changes required in consuming stages.

---

## 2. Data Flow Through the Pipeline

To understand how knowledge flows, let us trace a concrete check end-to-end: **"Active SCA detected"** (detecting active securities class action lawsuits).

### 2.1 ACQUIRE Stage: Getting Raw Data

The check's `required_data` declares what sources it needs:

```json
"required_data": ["SCAC_SEARCH", "SEC_10K", "LITIGATION_DB"]
```

The ACQUIRE stage fetches data from these sources using a fallback chain:

1. **Stanford SCAC** (via Playwright browser automation) -- search for company in securities class action clearinghouse
2. **SEC 10-K Item 3** (via SEC EDGAR REST API) -- legal proceedings disclosures in annual report
3. **CourtListener** (via API) -- federal court records
4. **Web search** (via Brave Search) -- catch early filings, state AG actions, news coverage

Raw data is stored in `state.acquired_data` as a dict keyed by source type.

### 2.2 EXTRACT Stage: Structuring Raw Data

The EXTRACT stage parses raw acquired data into structured Pydantic models. For our SCA check:

- `src/do_uw/stages/extract/sca_extractor.py` processes Stanford SCAC search results
- `src/do_uw/stages/extract/sca_parsing.py` extracts case details (filing date, lead plaintiff, status, settlement)
- Results populate `state.extracted.litigation.securities_class_actions` as a list of `SecurityClassAction` models

The check's `data_locations` tells the system where to find extracted data:

```json
"data_locations": {
  "SCAC_SEARCH": ["search_results", "case_details", "settlement_data"],
  "SEC_10K": ["item_3_legal_proceedings"]
}
```

### 2.3 ANALYZE Stage: Evaluating Checks

The ANALYZE stage (`src/do_uw/stages/analyze/__init__.py`) loads all checks and evaluates them:

```python
# In AnalyzeStage.run():
loader = BackwardCompatLoader(playbook_id=state.active_playbook_id)
brain = loader.load_all()
checks = brain.checks.get("checks", [])
results = execute_checks(checks, state.extracted, state.company)
```

The check engine (`src/do_uw/stages/analyze/check_engine.py`):
1. Filters to `execution_mode: "AUTO"` checks (skipping MANUAL)
2. Maps each check's `data_locations` to the correct fields in `state.extracted`
3. Evaluates the threshold (numeric comparison, qualitative assessment, or count)
4. Records a `CheckResult` with: `check_id`, `triggered` (bool), `confidence`, `evidence`

For our SCA check, if `state.extracted.litigation.securities_class_actions` contains active cases, the check **fires** (triggered=True).

### 2.4 SCORE Stage: Computing Factor Scores

The SCORE stage (`src/do_uw/stages/score/__init__.py`) runs a 16-step pipeline:

```
Step  1: Evaluate CRF (Critical Red Flag) gates
Step  2: Score all 10 factors (base scores)
Step  3: Detect 17+ composite patterns
Step  4: Apply pattern modifiers to factor scores
Step  5: Compute composite score (100 - total_risk_points)
Step  6: Apply CRF ceilings (hard caps on quality score)
Step  7: Classify tier (WIN/WANT/WRITE/WATCH/WALK)
Step  8: Classify risk type (DISTRESSED, BINARY_EVENT, etc.)
Step  9: Map allegation types (A-E categories)
Step 10: Compute claim probability
Step 11: Model severity scenarios
Step 12: Recommend tower position
Step 13: Compile red flag summary
Steps 14-16: Populate ScoringResult on state
```

For our SCA check:

- **Factor scoring** (Step 2): The check fires under factor `F1_prior_litigation` (max 20 points). An active SCA triggers rule `F1-001` for the full 20-point deduction.
- **CRF gate** (Step 1): The active SCA also triggers `CRF-01` ("Active Securities Class Action"), which caps the quality score at 30 and the tier at WALK.
- **Pattern detection** (Step 3): If the SCA coincides with a stock price decline and earnings miss, it may activate the "Event-Driven Claim" composite pattern, adding additional score impact.

The ScoreStage also loads configuration via `BackwardCompatLoader`:

```python
# In ScoreStage.run():
loader = BackwardCompatLoader()
brain = loader.load_all()
# brain.scoring -> factor weights, rules, tier boundaries
# brain.red_flags -> CRF gates and score ceilings
# brain.patterns -> composite risk pattern definitions
# brain.sectors -> sector baselines for contextual scoring
```

### 2.5 Complete Data Flow Diagram

```
                         checks.json (359 checks)
                         scoring.json (10 factors)
                         patterns.json (17 patterns)        config/*.json
                         red_flags.json (CRF gates)         (operational
                         sectors.json (baselines)             parameters)
                               |                                 |
                               v                                 |
                    +-------------------+                        |
                    |   migrate.py      |                        |
                    | (JSON -> SQLite)  |                        |
                    +-------------------+                        |
                               |                                 |
                               v                                 |
                    +-------------------+                        |
                    |  knowledge.db     |                        |
                    |  (SQLAlchemy ORM) |                        |
                    +-------------------+                        |
                               |                                 |
                               v                                 |
                    +-------------------+                        |
                    | compat_loader.py  |                        |
                    | (BackwardCompat-  |                        |
                    |  Loader)          |                        |
                    +-------------------+                        |
                               |                                 |
                               v                                 v
    +--------+    +----------+    +---------+    +-------+    +----------+
    | ACQUIRE| -> | EXTRACT  | -> | ANALYZE | -> | SCORE | -> | RENDER   |
    | (data  |    | (parse   |    | (eval   |    | (16-  |    | (Word/   |
    |  fetch)|    |  struct) |    |  checks)|    |  step)|    |  PDF/MD) |
    +--------+    +----------+    +---------+    +-------+    +----------+
         |              |               |              |             |
         v              v               v              v             v
    acquired_data  state.extracted  state.analysis  state.scoring  output/
    (raw filings,  (structured      (check results  (quality score, (worksheet
     prices,        Pydantic models  per check)      tier, factors,  document)
     searches)      per domain)                      patterns)
```

---

## 3. Adding and Improving Checks

### 3.1 Check Lifecycle

Every check follows a four-state lifecycle (defined in `src/do_uw/knowledge/lifecycle.py`):

```
INCUBATING -----> DEVELOPING -----> ACTIVE -----> DEPRECATED
    |                  |                              |
    |                  +-------> INCUBATING           |
    |                  |                              |
    +-------> DEPRECATED                              |
                                                      v
                                              DEVELOPING (reactivation)
```

| Status | Meaning |
|--------|---------|
| `INCUBATING` | Raw idea captured. No data chain, no evaluation, no output. |
| `DEVELOPING` | Building the data-to-output chain. Has some but not all links. |
| `ACTIVE` | Production-ready. Executes in the pipeline. All links verified. |
| `DEPRECATED` | Preserved but inactive. Never deleted -- preserved with reason. |

Valid transitions are enforced by `validate_transition()`:

```python
VALID_TRANSITIONS = {
    INCUBATING: [DEVELOPING, DEPRECATED],
    DEVELOPING: [ACTIVE, INCUBATING, DEPRECATED],
    ACTIVE:     [DEPRECATED],
    DEPRECATED: [DEVELOPING],  # reactivation path
}
```

### 3.2 How to Add a New Check

There are three ways to add a check:

**Method 1: CLI Ingestion**

```bash
do-uw knowledge ingest report.md --type SHORT_SELLER_REPORT
```

The ingestion pipeline (`src/do_uw/knowledge/ingestion.py`) extracts check ideas from structured text using rule-based patterns:
- Lines starting with `RISK:` or `CHECK:` become incubating checks
- Lines starting with `NOTE:` or `OBSERVATION:` become notes
- Bullet points under `# KEY FINDINGS` headers become notes
- Numbered list items become check ideas

Ingested checks start as `INCUBATING` with `origin: "AI_GENERATED"`.

**Method 2: Industry Playbook**

Industry playbooks (`src/do_uw/knowledge/playbook_data.py`) define checks for 5 industry verticals:

| Playbook | SIC Ranges | Example Checks |
|----------|-----------|----------------|
| Technology/SaaS | 3571-3579, 7371-7379 | ASC 606 revenue risk, subscription metric gaming |
| Biotech/Pharma | 2830-2836, 8731-8734 | Clinical trial disclosure, FDA approval risk |
| Financial Services | 6000-6599 | CECL reserve adequacy, BSA/AML compliance |
| Energy/Utilities | 1200-1389, 4900-4991 | Reserve overstatement, wildfire liability |
| Healthcare | 8000-8099 | False Claims Act risk, HIPAA compliance |

Playbook checks are loaded via `load_playbooks()` and start as `INCUBATING` with `origin: "PLAYBOOK"`. When a company's SIC code matches a playbook, the `BackwardCompatLoader` automatically appends industry-specific checks.

**Method 3: Direct Store Insertion**

```python
from do_uw.knowledge.store import KnowledgeStore
from do_uw.knowledge.models import Check
from datetime import UTC, datetime

store = KnowledgeStore()
check = Check(
    id="CUSTOM.CHECK.001",
    name="My custom check",
    section=3,
    pillar="FINANCIAL_REPORTING",
    status="INCUBATING",
    required_data=["SEC_10K"],
    data_locations={"SEC_10K": ["item_7_mda"]},
    scoring_factor="F3",
    origin="USER_ADDED",
    created_at=datetime.now(UTC),
    modified_at=datetime.now(UTC),
    version=1,
)
store.bulk_insert_checks([check])
```

### 3.3 Required Chain for ACTIVE Promotion

A check cannot be promoted from `DEVELOPING` to `ACTIVE` until all pipeline links are verified. The traceability validator (`src/do_uw/knowledge/traceability.py`) checks 5 dimensions:

| Dimension | What It Validates | Example |
|-----------|-------------------|---------|
| `DATA_SOURCE` | `required_data` entries are recognized source IDs | `SEC_10K`, `SCAC_SEARCH`, `MARKET_PRICE` |
| `EXTRACTION` | `data_locations` is non-empty with valid structure | `{"SEC_10K": ["item_3_legal_proceedings"]}` |
| `EVALUATION` | Sub-paths correspond to actual extractor outputs | `item_3_legal_proceedings` is in `KNOWN_DATA_LOCATION_PATHS["SEC_10K"]` |
| `OUTPUT` | `section` maps to a valid output section (1-7) | `section: 6` (Litigation section) |
| `SCORING` | `scoring_factor` references a known factor ID | `F1` through `F10` |

The known constants are defined in `src/do_uw/knowledge/traceability_constants.py`:

- `KNOWN_DATA_SOURCES`: 12 recognized data source IDs (SEC filings, market data, searches)
- `KNOWN_SCORING_FACTORS`: Factor IDs F1-F10
- `EXTRACTOR_STATE_PATHS`: 30+ state paths that EXTRACT stage actually populates
- `KNOWN_DATA_LOCATION_PATHS`: Sub-paths per data source that extractors understand
- `VALID_SECTIONS`: Sections 1-7

**Validation result:**

```python
from do_uw.knowledge.traceability import get_activation_readiness

report = get_activation_readiness(store, "CUSTOM.CHECK.001")
print(report.status)    # "COMPLETE", "INCOMPLETE", or "BROKEN"
print(report.summary)   # "Check CUSTOM.CHECK.001: all 5 links verified"
```

A check with status `COMPLETE` is ready for `DEVELOPING -> ACTIVE` promotion. A `BROKEN` check (3+ missing links) needs significant work.

### 3.4 How Industry Playbooks Add Checks

When the RESOLVE stage identifies a company's SIC code, it calls:

```python
from do_uw.knowledge.playbooks import activate_playbook
playbook = activate_playbook(sic_code="3571", naics_code="5112", store=store)
state.active_playbook_id = playbook["id"]  # "TECH_SAAS"
```

Later, when the ANALYZE stage loads checks:

```python
loader = BackwardCompatLoader(playbook_id=state.active_playbook_id)
brain = loader.load_all()
# brain.checks now includes both standard 359 checks AND Tech/SaaS industry checks
```

The `BackwardCompatLoader._append_industry_checks()` method merges industry checks (avoiding duplicates by check ID).

---

## 4. Calibration Parameters

### 4.1 Scoring Configuration (`src/do_uw/brain/scoring.json`)

The scoring model uses 10 factors totaling 100 points:

| Factor | Name | Max Points | Weight |
|--------|------|-----------|--------|
| `F1_prior_litigation` | Prior Litigation | 20 | 20% |
| `F2_stock_decline` | Stock Price Decline | 15 | 15% |
| `F3_restatement_audit` | Restatement/Audit Issues | 15 | 15% |
| `F4_ipo_spac_ma` | IPO/SPAC/M&A Events | 10 | 10% |
| `F5_guidance_misses` | Guidance/Earnings Misses | 5 | 5% |
| `F6_short_interest` | Short Interest Signals | 5 | 5% |
| `F7_volatility` | Stock Volatility | 5 | 5% |
| `F8_financial_distress` | Financial Distress | 10 | 10% |
| `F9_governance` | Governance Quality | 10 | 10% |
| `F10_officer_stability` | Officer Stability | 5 | 5% |

**Scoring formula:** `quality_score = 100 - sum(points_deducted)`

Each factor has multiple scoring rules. For example, `F1_prior_litigation`:

```json
{
  "id": "F1-001",
  "condition": "Active securities class action",
  "points": 20,
  "triggers_crf": "CRF-001"
}
```

**Tier boundaries** determine the quality classification:

| Tier | Meaning | Score Range (typical) |
|------|---------|-----------------------|
| WIN | Strongly pursue | 85-100 |
| WANT | Actively compete | 70-84 |
| WRITE | Acceptable risk | 55-69 |
| WATCH | Monitor closely | 40-54 |
| WALK | Decline or excess only | 0-39 |

### 4.2 Governance Weights (`src/do_uw/config/governance_weights.json`)

Seven governance dimensions scored 0-10, weighted and summed to a 0-100 composite:

1. Board independence
2. CEO/Chair separation
3. Compensation alignment
4. Audit committee quality
5. Board diversity
6. Attendance/engagement
7. Related party controls

### 4.3 Red Flag Gates (`src/do_uw/brain/red_flags.json`)

Critical Red Flags (CRFs) are **hard gates** that cap the maximum quality score and restrict tier placement:

| CRF | Trigger | Max Score | Max Tier |
|-----|---------|-----------|----------|
| CRF-01 | Active securities class action | 30 | WALK |
| CRF-02 | Wells Notice disclosed | 30 | WALK |
| CRF-03 | DOJ criminal investigation | 30 | WALK |
| CRF-04 | Going concern opinion | 50 | WATCH |

Even if all other factors score perfectly, a triggered CRF caps the quality score at its ceiling. A company with an active SCA cannot score above 30 regardless of its governance, financials, or market position.

### 4.4 How Calibration Changes Propagate

When a calibration parameter changes (e.g., adjusting F1 max_points from 20 to 25):

```
1. Edit src/do_uw/brain/scoring.json
   (Change "max_points": 20 to "max_points": 25 for F1_prior_litigation)

2. On next pipeline run, BackwardCompatLoader auto-migrates:
   - Creates in-memory KnowledgeStore
   - Calls migrate_from_json(brain_dir, store)
   - Stores full scoring.json as metadata
   - Returns updated BrainConfig to ScoreStage

3. ScoreStage consumes updated config:
   - score_all_factors() reads max_points from config
   - Factor F1 now deducts up to 25 points instead of 20
   - total_points in scoring.json must also be updated (100 -> 105)

4. Downstream effects:
   - Composite score calculation changes
   - Tier boundaries may need adjustment
   - Severity model recalibrates
```

**Before/after example -- increasing litigation weight:**

```
BEFORE: F1 max_points=20, total_points=100
  Company with active SCA: F1 deduction = 20/100 = 20% of score
  quality_score = 100 - 20 - [other deductions]

AFTER:  F1 max_points=25, total_points=105
  Company with active SCA: F1 deduction = 25/105 = 23.8% of score
  quality_score = 105 - 25 - [other deductions]
```

### 4.5 CheckHistory Records All Changes

Every modification to a check is recorded in the `check_history` table via `record_field_change()` in `src/do_uw/knowledge/lifecycle.py`:

```python
record_field_change(
    session=session,
    check_id="FIN.ACCT.restatement",
    field_name="threshold_value",
    old_value="3",
    new_value="5",
    changed_by="senior_underwriter",
    reason="Increased restatement lookback from 3 to 5 years based on claims data"
)
```

This creates a `CheckHistory` entry:

```
version:    2
field_name: threshold_value
old_value:  3
new_value:  5
changed_at: 2026-02-10T12:00:00Z
changed_by: senior_underwriter
reason:     Increased restatement lookback from 3 to 5 years based on claims data
```

---

## 5. Intent Preservation

### 5.1 CheckHistory: Every Modification Recorded

The `CheckHistory` model (`src/do_uw/knowledge/models.py`) records every field change with full context:

```
check_id    -- Which check was modified
version     -- Auto-incrementing version number
field_name  -- Which field changed (status, threshold_value, scoring_factor, etc.)
old_value   -- Previous value (as string)
new_value   -- New value (as string)
changed_at  -- UTC timestamp
changed_by  -- Identity of who made the change
reason      -- WHY the change was made (the intent)
```

The `reason` field is critical for intent preservation. It captures not just what changed, but **why it changed**. This prevents future maintainers from undoing deliberate calibration decisions without understanding the original rationale.

### 5.2 ProvenanceSummary: At-a-Glance Audit Trail

The provenance module (`src/do_uw/knowledge/provenance.py`) provides aggregated views of check history:

```python
from do_uw.knowledge.provenance import get_provenance_summary

summary = get_provenance_summary(store, "FIN.ACCT.restatement")
# summary.origin          -> "BRAIN_MIGRATION"
# summary.created_at      -> datetime(2026, 1, 28, ...)
# summary.current_version -> 3
# summary.total_modifications -> 5
# summary.status_transitions -> [INCUBATING->DEVELOPING, DEVELOPING->ACTIVE]
# summary.recent_changes  -> last 10 field changes
```

**Migration statistics** show how the knowledge store is populated:

```python
from do_uw.knowledge.provenance import get_migration_stats

stats = get_migration_stats(store)
# stats["by_origin"]  -> {"BRAIN_MIGRATION": 359, "PLAYBOOK": 50, "AI_GENERATED": 12}
# stats["by_status"]  -> {"ACTIVE": 359, "INCUBATING": 62}
# stats["total_checks"] -> 421
# stats["total_history_entries"] -> 1200
```

### 5.3 Deprecation Log: Checks Never Deleted

When a check becomes obsolete, it is **deprecated, never deleted**:

```python
from do_uw.knowledge.lifecycle import transition_check, CheckStatus

transition_check(
    session=session,
    check_id="OLD.CHECK.001",
    to_status=CheckStatus.DEPRECATED,
    changed_by="system_review",
    reason="Superseded by FIN.ACCT.restatement_v2 with expanded lookback window"
)
```

The deprecation log (`get_deprecation_log()` in `src/do_uw/knowledge/provenance.py`) provides a complete record:

```python
from do_uw.knowledge.provenance import get_deprecation_log

log = get_deprecation_log(store)
# [{"check_id": "OLD.CHECK.001",
#   "check_name": "Restatement check v1",
#   "deprecated_at": datetime(2026, 2, 10, ...),
#   "deprecated_by": "system_review",
#   "reason": "Superseded by FIN.ACCT.restatement_v2 ..."}]
```

This ensures that:
- No check disappears without explanation
- The reason for deprecation is permanently recorded
- Deprecated checks can be reactivated if needed (`DEPRECATED -> DEVELOPING`)

### 5.4 Learning Infrastructure: Tracking Effectiveness

The learning module (`src/do_uw/knowledge/learning.py`) tracks which checks fire across analysis runs:

```python
from do_uw.knowledge.learning import record_analysis_run, AnalysisOutcome

outcome = AnalysisOutcome(
    ticker="AAPL",
    run_date=datetime.now(UTC),
    checks_fired=["FIN.ACCT.restatement", "STOCK.PRICE.single_day_events"],
    checks_clear=["LIT.SCA.active", "GOV.BOARD.independence"],
    quality_score=72.5,
    tier="WANT",
)
record_analysis_run(store, outcome)
```

Over time, this enables:
- **Fire rate tracking**: Which checks fire most frequently
- **Co-firing detection**: Which checks always fire together (potential redundancy)
- **Effectiveness measurement**: Using Jaccard similarity to find check pairs with >85% co-occurrence

```python
from do_uw.knowledge.learning import find_redundant_pairs

pairs = find_redundant_pairs(store, threshold=0.85)
# [("CHECK.A", "CHECK.B", 0.92)]  -- these two nearly always co-fire
```

### 5.5 Narrative Composition: Turning Signals into Stories

The narrative module (`src/do_uw/knowledge/narrative.py`) groups fired checks into coherent risk stories using 7 pre-defined templates:

| Narrative | Key Check Patterns | Severity |
|-----------|--------------------|----------|
| Restatement Risk | FIN.ACCT.restatement, STOCK.INSIDER.cluster_timing | HIGH |
| Event-Driven Claim | STOCK.PRICE.single_day_events, FIN.GUIDE.earnings_reaction | HIGH |
| Governance Failure | GOV.BOARD.independence, GOV.PAY.ceo_ratio | MEDIUM |
| Regulatory Exposure | LIT.REG.sec_active, LIT.REG.wells_notice | HIGH |
| Financial Distress | FIN.DEBT.covenants, FIN.LIQ.position | HIGH |
| Insider Trading Pattern | STOCK.INSIDER.cluster_timing, STOCK.PATTERN.informed_trading | HIGH |
| Acquisition Risk | LIT.SCA.merger_obj, GOV.ACTIVIST.campaigns | MEDIUM |

A narrative activates when 2+ of its component check patterns fire. This transforms individual signals into **underwriter-presentable risk stories** with context about what the pattern means for D&O exposure.

---

## 6. System Architecture Diagram

```
+===========================================================================+
|                        KNOWLEDGE SYSTEM ARCHITECTURE                       |
+===========================================================================+

  SOURCE LAYER (Static Knowledge)
  ================================

  src/do_uw/brain/                    src/do_uw/config/
  +-------------------+               +--------------------+
  | checks.json  (359)|               | scoring.json       |
  | scoring.json  (10)|               | governance_wts.json|
  | patterns.json (17)|               | actuarial.json     |
  | red_flags.json    |               | claim_types.json   |
  | sectors.json      |               | (11 more files)    |
  +-------------------+               +--------------------+
           |                                    |
           | migrate_from_json()                | (direct file reads)
           v                                    |
  STORE LAYER (Queryable Knowledge)             |
  ================================              |
                                                |
  src/do_uw/knowledge/knowledge.db              |
  +-------------------------------------------+ |
  | checks          (Check ORM)               | |
  | check_history   (CheckHistory ORM)        | |
  | patterns        (Pattern ORM)             | |
  | scoring_rules   (ScoringRule ORM)         | |
  | red_flags       (RedFlag ORM)             | |
  | sectors         (Sector ORM)              | |
  | notes           (Note ORM + FTS5)         | |
  | industry_playbooks (IndustryPlaybook ORM) | |
  | notes_fts / checks_fts (FTS5 virtual)     | |
  +-------------------------------------------+ |
           |                                    |
           | BackwardCompatLoader               |
           | (compat_loader.py)                 |
           v                                    |
  COMPATIBILITY LAYER                           |
  ================================              |
                                                |
  BrainConfig (Pydantic)                        |
  +-------------------------------------------+ |
  | .checks   = dict  (same as checks.json)   | |
  | .scoring  = dict  (same as scoring.json)   | |
  | .patterns = dict  (same as patterns.json)  | |
  | .sectors  = dict  (same as sectors.json)   | |
  | .red_flags= dict  (same as red_flags.json) | |
  +-------------------------------------------+ |
           |                                    |
           v                                    v
  CONSUMPTION LAYER (Pipeline Stages)
  ================================

  +----------+   +----------+   +-----------+   +---------+   +--------+
  | RESOLVE  |-->| ACQUIRE  |-->|  EXTRACT  |-->| ANALYZE |-->| SCORE  |
  | (ticker  |   | (SEC,    |   | (parse    |   | (eval   |   | (16-   |
  |  lookup) |   |  market, |   |  filings, |   |  checks |   |  step  |
  |          |   |  search) |   |  struct)  |   |  vs     |   |  pipe- |
  |  Activates   |          |   |           |   |  data)  |   |  line) |
  |  playbook|   |          |   |           |   |         |   |        |
  +----------+   +----------+   +-----------+   +---------+   +--------+
                                                     |              |
                                                     | Reads checks | Reads scoring,
                                                     | via Compat-  | red_flags,
                                                     | Loader       | patterns,
                                                     |              | sectors via
                                                     |              | CompatLoader
                                                     v              v
  GOVERNANCE LAYER (Quality & Learning)
  ================================

  +-------------------+  +------------------+  +------------------+
  | lifecycle.py      |  | provenance.py    |  | traceability.py  |
  | (state machine:   |  | (audit trail:    |  | (chain validation|
  |  INCUBATING ->    |  |  who changed     |  |  5 dimensions:   |
  |  DEVELOPING ->    |  |  what and why,   |  |  DATA_SOURCE,    |
  |  ACTIVE ->        |  |  migration stats,|  |  EXTRACTION,     |
  |  DEPRECATED)      |  |  deprecation log)|  |  EVALUATION,     |
  +-------------------+  +------------------+  |  OUTPUT,         |
                                               |  SCORING)        |
  +-------------------+  +------------------+  +------------------+
  | learning.py       |  | narrative.py     |
  | (fire rates,      |  | (risk stories:   |
  |  co-firing,       |  |  7 templates,    |
  |  redundancy       |  |  2+ check        |
  |  detection,       |  |  threshold)      |
  |  Jaccard sim)     |  |                  |
  +-------------------+  +------------------+

  +-------------------+  +------------------+
  | ingestion.py      |  | playbooks.py     |
  | (external docs:   |  | (5 industry      |
  |  RISK:/CHECK:     |  |  verticals,      |
  |  patterns,        |  |  SIC/NAICS       |
  |  rule-based       |  |  matching,       |
  |  extraction)      |  |  50 checks)      |
  +-------------------+  +------------------+
```

---

## File Reference

All source files mentioned in this document, with their locations relative to the project root:

### Knowledge Store Core
- `src/do_uw/knowledge/__init__.py` -- Public API exports
- `src/do_uw/knowledge/models.py` -- SQLAlchemy ORM models (Check, CheckHistory, Pattern, etc.)
- `src/do_uw/knowledge/store.py` -- KnowledgeStore query API with FTS5 search
- `src/do_uw/knowledge/store_converters.py` -- ORM-to-dict conversion functions
- `src/do_uw/knowledge/store_search.py` -- FTS5 and LIKE search implementations

### Knowledge Lifecycle & Governance
- `src/do_uw/knowledge/lifecycle.py` -- Check state machine (INCUBATING->ACTIVE->DEPRECATED)
- `src/do_uw/knowledge/provenance.py` -- Audit trail, migration stats, deprecation log
- `src/do_uw/knowledge/traceability.py` -- 5-dimension chain validation
- `src/do_uw/knowledge/traceability_constants.py` -- Ground truth sets for validation

### Knowledge Evolution
- `src/do_uw/knowledge/learning.py` -- Fire rate tracking, co-firing detection, redundancy
- `src/do_uw/knowledge/narrative.py` -- Risk narrative composition (7 templates)
- `src/do_uw/knowledge/ingestion.py` -- External document ingestion pipeline

### Migration & Compatibility
- `src/do_uw/knowledge/migrate.py` -- brain/ JSON to SQLite migration
- `src/do_uw/knowledge/compat_loader.py` -- BackwardCompatLoader (drop-in for ConfigLoader)

### Industry Playbooks
- `src/do_uw/knowledge/playbooks.py` -- Playbook activation and query API
- `src/do_uw/knowledge/playbook_data.py` -- Tech/SaaS, Biotech/Pharma, Financial Services
- `src/do_uw/knowledge/playbook_data_extra.py` -- Energy/Utilities, Healthcare

### Brain Files (Source Knowledge)
- `src/do_uw/brain/checks.json` -- 359 D&O risk checks
- `src/do_uw/brain/scoring.json` -- 10-factor scoring model
- `src/do_uw/brain/patterns.json` -- 17 composite risk patterns
- `src/do_uw/brain/red_flags.json` -- Critical red flag gates
- `src/do_uw/brain/sectors.json` -- Sector baselines

### Config Files (Operational Parameters)
- `src/do_uw/config/loader.py` -- ConfigLoader (original brain/ file loader)
- `src/do_uw/config/scoring.json` -- Scoring weights (consumed directly by some stages)
- `src/do_uw/config/governance_weights.json` -- 7 governance dimensions
- `src/do_uw/config/actuarial.json` -- Actuarial pricing parameters
- `src/do_uw/config/claim_types.json` -- D&O claim type taxonomy
- `src/do_uw/config/industry_theories.json` -- Industry-specific litigation theories
- Plus 8 more config files (see Section 1.3)

### Pipeline Stages (Consumers)
- `src/do_uw/stages/analyze/__init__.py` -- AnalyzeStage (loads checks, evaluates)
- `src/do_uw/stages/score/__init__.py` -- ScoreStage (16-step scoring pipeline)
