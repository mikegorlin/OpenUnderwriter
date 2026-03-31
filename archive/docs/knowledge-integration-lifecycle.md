# Knowledge Integration Lifecycle

How external documents become active underwriting checks in the D&O pipeline.

This guide covers the full integration path: from ingesting an external document
through the knowledge store, through human review and graduation, to active
execution in the analysis pipeline. It uses the Sidley Austin biotech SCA study
as a concrete worked example throughout.

---

## 1. Document Ingestion Pipeline

### Overview

The ingestion pipeline reads external text or markdown documents, extracts
structured knowledge items using rule-based patterns, and stores them in the
knowledge store as incubating checks and notes.

**Entry point:** `src/do_uw/knowledge/ingestion.py` via `ingest_document()`

**CLI command:**

```bash
do-uw knowledge ingest <filepath> --type <TYPE>
```

### Supported Inputs

- **File formats:** `.txt` and `.md` files only
- **Document types** (6 categories, defined as `DocumentType` StrEnum):

| DocumentType           | Tag string       | Typical content                     |
|------------------------|------------------|-------------------------------------|
| `SHORT_SELLER_REPORT`  | `short_seller`   | Activist short research reports     |
| `CLAIMS_STUDY`         | `claims_study`   | SCA settlement data, claims studies |
| `UNDERWRITER_NOTES`    | `underwriter`    | Internal underwriting observations  |
| `INDUSTRY_ANALYSIS`    | `industry`       | Sector-specific risk analyses       |
| `REGULATORY_GUIDANCE`  | `regulatory`     | Regulatory framework updates        |
| `GENERAL`              | `general`        | Anything else                       |

### Extraction Patterns

The rule-based extractor (`extract_knowledge_items()`) applies four pattern
types sequentially to the document text:

**Pattern 1: RISK:/CHECK: prefixed lines** (`_extract_check_items`)
- Lines starting with `RISK:` or `CHECK:` (case-insensitive)
- Extracted as `check_idea` items
- Title: first 100 characters of content after prefix

**Pattern 2: NOTE:/OBSERVATION: prefixed lines** (`_extract_note_items`)
- Lines starting with `NOTE:` or `OBSERVATION:` (case-insensitive)
- Extracted as `note` items
- Title: first 100 characters of content after prefix

**Pattern 3: Header bullet extraction** (`_extract_header_bullets`)
- Finds markdown headers matching: `KEY FINDINGS`, `CONCLUSIONS`,
  `RECOMMENDATIONS`, `SUMMARY`
- Extracts bullet points (`- ` or `* `) under those headers as `note` items
- Stops at the next header or section boundary

**Pattern 4: Numbered list extraction** (`_extract_numbered_items`)
- Matches numbered lists (`1.`, `2)`, etc.)
- Items must be >10 characters (filters out short list markers)
- Extracted as `check_idea` items

The extraction function also accepts a pluggable `extraction_fn` parameter
for future LLM-based extraction (currently unused).

### Tag Mapping

Each document type maps to a tag string via `_DOC_TYPE_TAGS`:

```python
DocumentType.CLAIMS_STUDY  -> "claims_study"
DocumentType.SHORT_SELLER_REPORT -> "short_seller"
```

This tag is attached to every item extracted from that document, enabling
downstream filtering by source type.

### Output

The `ingest_document()` function returns an `IngestionResult`:

```python
@dataclass
class IngestionResult:
    document_name: str       # Name of the ingested file
    doc_type: str            # DocumentType value
    checks_created: int      # Count of incubating checks created
    notes_added: int         # Count of notes added
    errors: list[str]        # Any errors encountered
```

---

## 2. What Happens to Ingested Items

### Check Ideas

Each extracted `check_idea` becomes a `Check` ORM object
(`src/do_uw/knowledge/models.py`) with these initial values:

| Field             | Value                                    |
|-------------------|------------------------------------------|
| `id`              | `ING-{YYYYMMDDHHMMSS}-{hash}`           |
| `name`            | First 100 chars of extracted content     |
| `section`         | `0` (unassigned)                         |
| `pillar`          | `INGESTED`                               |
| `severity`        | `None`                                   |
| `execution_mode`  | `MANUAL`                                 |
| `status`          | `INCUBATING`                             |
| `threshold_type`  | `None`                                   |
| `threshold_value` | `None`                                   |
| `required_data`   | `[]` (empty list)                        |
| `data_locations`  | `{}` (empty dict)                        |
| `scoring_factor`  | `None`                                   |
| `scoring_rule`    | `None`                                   |
| `output_section`  | `None`                                   |
| `origin`          | `AI_GENERATED`                           |
| `version`         | `1`                                      |

The check is inserted via `KnowledgeStore.bulk_insert_checks()`.

### Notes

Each extracted `note` becomes a `Note` ORM object:

| Field        | Value                                |
|--------------|--------------------------------------|
| `title`      | First 100 chars of content           |
| `content`    | Full extracted text                  |
| `tags`       | Document type tag (e.g., `claims_study`) |
| `source`     | Source document filename             |
| `check_id`   | `None` (unlinked)                    |

Notes are inserted via `KnowledgeStore.add_note()`.

### Storage

Both checks and notes are persisted to `src/do_uw/knowledge/knowledge.db`,
a SQLite database managed by SQLAlchemy 2.0 with FTS5 full-text search
support. The database schema is defined in `src/do_uw/knowledge/models.py`.

---

## 3. Lifecycle State Machine

**Source:** `src/do_uw/knowledge/lifecycle.py`

### States

```
INCUBATING  -- Raw idea captured, not yet developed
DEVELOPING  -- Building data/eval/output chain
ACTIVE      -- Production-ready, executes in pipeline
DEPRECATED  -- Preserved but inactive
```

### State Diagram

```
                  +-----------+
           +----->| INCUBATING|<------+
           |      +-----+-----+      |
           |            |             |
           |  (develop) v  (regress) |
           |      +-----+-----+      |
           |      | DEVELOPING +------+
           |      +-----+-----+
           |            |
           |  (activate)|
           |            v
           |      +-----+-----+
           |      |   ACTIVE   |
           |      +-----+-----+
           |            |
 (resurrect)|  (deprecate)|
           |            v
           |      +-----+-----+
           +------+ DEPRECATED|
                  +-----------+
```

### Valid Transitions

Defined in `VALID_TRANSITIONS` dict:

| From         | To                                       |
|--------------|------------------------------------------|
| INCUBATING   | DEVELOPING, DEPRECATED                   |
| DEVELOPING   | ACTIVE, INCUBATING (regression), DEPRECATED |
| ACTIVE       | DEPRECATED                               |
| DEPRECATED   | DEVELOPING (resurrection)                |

### Transition Mechanics

`transition_check()` performs:

1. Loads the Check ORM object by `check_id`
2. Validates the transition via `validate_transition()`
3. Updates `check.status` to the new value
4. Updates `check.modified_at` to current UTC timestamp
5. Increments `check.version`
6. Creates a `CheckHistory` record with:
   - `field_name = "status"`
   - `old_value` and `new_value`
   - `changed_at`, `changed_by`, `reason`
7. Flushes the session

### Field Change Tracking

`record_field_change()` tracks non-status field modifications (e.g.,
assigning a section, updating a threshold). It follows the same pattern:
update `modified_at`, increment `version`, create `CheckHistory` record.

### Audit Trail

Every modification is recorded in the `check_history` table
(`src/do_uw/knowledge/models.py: CheckHistory`). The provenance module
(`src/do_uw/knowledge/provenance.py`) provides query APIs:

- `get_check_history(store, check_id)` -- full chronological history
- `get_provenance_summary(store, check_id)` -- lifecycle overview
- `get_migration_stats(store)` -- store-wide composition stats
- `get_deprecation_log(store)` -- all deprecations with reasons

---

## 4. Graduation Criteria

### INCUBATING to DEVELOPING

**Purpose:** A human has reviewed the raw check idea and decided it is worth
developing into a production check.

**What must happen:**

1. **Review the check idea** -- Is the risk signal valid and actionable?
2. **Assign a section** (1-7) -- Which worksheet section does this check
   belong to?
3. **Set the pillar** -- Reclassify from `INGESTED` to the appropriate
   pillar (e.g., `FINANCIAL`, `LITIGATION`, `GOVERNANCE`)
4. **Define `required_data`** -- Which data sources does this check need?
   Must be from `KNOWN_DATA_SOURCES`:
   `SEC_10K`, `SEC_10Q`, `SEC_DEF14A`, `SEC_8K`, `SEC_FORM4`, `SEC_13DG`,
   `SEC_ENFORCEMENT`, `MARKET_PRICE`, `MARKET_SHORT`, `SCAC_SEARCH`,
   `LITIGATION_DB`, `NEWS_SEARCH`
5. **Define `data_locations`** -- Map data source to sub-paths that
   extractors populate (see `KNOWN_DATA_LOCATION_PATHS` in
   `src/do_uw/knowledge/traceability_constants.py`)
6. **Set execution_mode** -- Change from `MANUAL` to `AUTO` if the check
   can be evaluated automatically

**Transition command:**

```python
from do_uw.knowledge.lifecycle import transition_check, CheckStatus

with store.get_session() as session:
    transition_check(
        session, check_id="ING-20250209-1234",
        to_status=CheckStatus.DEVELOPING,
        changed_by="underwriter@example.com",
        reason="Valid biotech claim rate calibration check"
    )
```

### DEVELOPING to ACTIVE

**Purpose:** The check has been fully wired into the pipeline and all
traceability links are verified.

**What must be true (validated by traceability chain):**

The traceability validation module (`src/do_uw/knowledge/traceability.py`)
checks five dimensions. All must pass for COMPLETE status:

1. **DATA_SOURCE** -- Every entry in `required_data` is a recognized data
   source from `KNOWN_DATA_SOURCES`
2. **EXTRACTION** -- `data_locations` is non-empty with valid structure
   (dict of `{source: [sub_paths]}` or list of state paths)
3. **EVALUATION** -- Each sub-path in `data_locations` maps to a real
   extractor target (verified against `EXTRACTOR_STATE_PATHS` and
   `KNOWN_DATA_LOCATION_PATHS`)
4. **OUTPUT** -- `section` maps to a valid output section (1-7), matching
   `VALID_SECTIONS`
5. **SCORING** -- `scoring_factor` references a known factor ID
   (`F1`-`F10` or full IDs like `F1_prior_litigation`), or is `None`
   for info-only checks

**Readiness check:**

```python
from do_uw.knowledge.traceability import get_activation_readiness

report = get_activation_readiness(store, check_id="ING-20250209-1234")
if report.status == "COMPLETE":
    # Safe to transition to ACTIVE
    ...
elif report.status == "INCOMPLETE":
    # Some links missing, review report.links for details
    ...
elif report.status == "BROKEN":
    # 3+ links missing, needs significant work
    ...
```

**Additional requirements before activation:**

- `threshold_type` and `threshold_value` must be defined (for non-info checks)
- Check should not be redundant with existing active checks (use
  `learning.py: find_redundant_pairs()` with Jaccard similarity >= 0.85)
- Execution has been tested against sample data

### ACTIVE to DEPRECATED

A check can be deprecated when:
- It is no longer relevant (regulatory change, market shift)
- It is redundant with another active check
- It produces too many false positives

### DEPRECATED to DEVELOPING (Resurrection)

A deprecated check can be brought back to DEVELOPING status for rework
when circumstances change (e.g., a regulation is re-enacted).

---

## 5. Worked Example: Sidley Biotech SCA Study

This section traces the full lifecycle using the actual Sidley Austin
biotech securities class action study ingested in commit `98b46c5`.

### Step 1: Prepare the Document

The study was compiled from Sidley Austin, Cornerstone Research, Cooley
SLE, and D&O Diary into a structured markdown file following the ingestion
format conventions:

**File:** `knowledge_docs/sidley_biotech_sca_2024.md` (166 lines)

The document uses all four extraction patterns:
- `## KEY FINDINGS` and `## CONCLUSIONS` headers with bullet points
  (Pattern 3: header bullets)
- `RISK:` prefixed lines for trigger events (Pattern 1: check prefixes)
- `CHECK:` prefixed lines for calibration implications (Pattern 1)
- `NOTE:` prefixed lines for contextual observations (Pattern 2)
- Numbered lists under scoring calibration sections (Pattern 4)

### Step 2: Ingest the Document

```bash
do-uw knowledge ingest knowledge_docs/sidley_biotech_sca_2024.md --type CLAIMS_STUDY
```

This calls `ingest_document(store, path, DocumentType.CLAIMS_STUDY)` which:

1. Validates the `.md` extension is supported
2. Reads the file content (166 lines)
3. Calls `extract_knowledge_items(text, DocumentType.CLAIMS_STUDY)`
4. The tag is resolved: `CLAIMS_STUDY` -> `"claims_study"`
5. Four extraction passes run sequentially

### Step 3: Extraction Results

The extraction produced:

| Pattern                  | Type        | Count | Examples                                                    |
|--------------------------|-------------|-------|-------------------------------------------------------------|
| RISK:/CHECK: prefixes    | check_idea  | 18    | "Clinical trial failure", "Biotech base claim rate..."      |
| Numbered lists           | check_idea  | 6     | Scoring calibration data points                             |
| NOTE: prefixes           | note        | 4     | "Pre-approval stage companies face different risk profile"  |
| Header bullets           | note        | 17    | "Life sciences SCA surged 29%...", "Median biotech..."      |
| **Total**                |             | **45** | **24 checks + 21 notes**                                   |

### Step 4: Current State in Knowledge Store

After ingestion, the 24 checks exist in the knowledge store as:

```
id:              ING-20250209HHMMSS-XXXX (24 unique IDs)
status:          INCUBATING
section:         0 (unassigned)
pillar:          INGESTED
origin:          AI_GENERATED
execution_mode:  MANUAL
required_data:   [] (empty)
data_locations:  {} (empty)
scoring_factor:  None
version:         1
```

The 21 notes are stored with `tags = "claims_study"` and
`source = "sidley_biotech_sca_2024.md"`.

You can query them:

```bash
do-uw knowledge search "biotech"
do-uw knowledge stats
```

### Step 5: Graduating a Check (Worked Example)

Let us trace the graduation of one specific check through the full
lifecycle. Take the check:

> "Biotech base claim rate should be higher than all-sector average
> (21% of filings from ~10% of market)"

**5a. INCUBATING -> DEVELOPING**

A human reviewer evaluates this check idea and determines:
- It is a valid calibration signal for the severity model
- It belongs in Section 6 (Litigation Analysis)
- It needs SCAC filing data and sector baseline data
- It maps to scoring factor F1 (Prior Litigation)

The reviewer applies these changes:

```python
from do_uw.knowledge.lifecycle import (
    transition_check, record_field_change, CheckStatus,
)

check_id = "ING-20250209225126-1234"  # Example ID

with store.get_session() as session:
    # Assign section
    record_field_change(
        session, check_id, "section",
        old_value="0", new_value="6",
        changed_by="senior_uw@example.com",
        reason="Litigation analysis section"
    )

    # Update pillar
    record_field_change(
        session, check_id, "pillar",
        old_value="INGESTED", new_value="LITIGATION",
        changed_by="senior_uw@example.com",
    )

    # Set required data sources
    record_field_change(
        session, check_id, "required_data",
        old_value="[]",
        new_value='["SCAC_SEARCH", "NEWS_SEARCH"]',
        changed_by="senior_uw@example.com",
    )

    # Set data locations
    record_field_change(
        session, check_id, "data_locations",
        old_value="{}",
        new_value='{"SCAC_SEARCH": ["search_results"], "NEWS_SEARCH": ["search_results"]}',
        changed_by="senior_uw@example.com",
    )

    # Set threshold
    record_field_change(
        session, check_id, "threshold_type",
        old_value=None, new_value="percentage",
        changed_by="senior_uw@example.com",
    )
    record_field_change(
        session, check_id, "threshold_value",
        old_value=None, new_value=">9.5%",
        changed_by="senior_uw@example.com",
        reason="Biotech implied SCA rate from Sidley 2024 data"
    )

    # Set scoring factor
    record_field_change(
        session, check_id, "scoring_factor",
        old_value=None, new_value="F1",
        changed_by="senior_uw@example.com",
    )

    # Set execution mode
    record_field_change(
        session, check_id, "execution_mode",
        old_value="MANUAL", new_value="AUTO",
        changed_by="senior_uw@example.com",
    )

    # Transition to DEVELOPING
    transition_check(
        session, check_id,
        to_status=CheckStatus.DEVELOPING,
        changed_by="senior_uw@example.com",
        reason="Biotech claim rate calibration - all fields populated"
    )
```

Each `record_field_change()` call increments the check's version and
creates a `CheckHistory` audit record.

**5b. Validate Traceability**

Before promoting to ACTIVE, run the traceability validation:

```python
from do_uw.knowledge.traceability import get_activation_readiness

report = get_activation_readiness(store, check_id)
print(report.status)   # "COMPLETE" if all links verified
print(report.summary)  # "Check ING-...: all 7 links verified"

for link in report.links:
    print(f"  {link.link_type}: {'PASS' if link.found else 'FAIL'} - {link.detail}")
```

The five validation dimensions check:
1. DATA_SOURCE: `SCAC_SEARCH` and `NEWS_SEARCH` are in `KNOWN_DATA_SOURCES`
2. EXTRACTION: `data_locations` dict has valid sub-path lists
3. EVALUATION: `search_results` is in `KNOWN_DATA_LOCATION_PATHS["SCAC_SEARCH"]`
4. OUTPUT: Section 6 is in `VALID_SECTIONS` (1-7)
5. SCORING: `F1` is in `KNOWN_SCORING_FACTORS`

**5c. Check for Redundancy**

```python
from do_uw.knowledge.learning import find_redundant_pairs

pairs = find_redundant_pairs(store, threshold=0.85)
# Review if any pair involves our check ID
```

`find_redundant_pairs()` uses Jaccard similarity on check fire sets from
recorded analysis runs. If two checks co-fire > 85% of the time, they may
be redundant.

**5d. DEVELOPING -> ACTIVE**

Once traceability is COMPLETE and redundancy review passes:

```python
with store.get_session() as session:
    transition_check(
        session, check_id,
        to_status=CheckStatus.ACTIVE,
        changed_by="senior_uw@example.com",
        reason="Traceability complete, no redundancy detected"
    )
```

The check is now version 9+ (after all field changes and two status
transitions), with a full audit trail in `check_history`.

### Step 6: The Check Executes in the Pipeline

Once ACTIVE, the check is loaded by `BackwardCompatLoader` and executed
in the ANALYZE stage during the next `do-uw analyze <TICKER>` run.
See Section 7 below for the full activation chain.

---

## 6. Human Review Points

The following points in the lifecycle require human judgment. They cannot
be automated because they involve domain expertise, risk appetite
decisions, or quality assurance.

### Review Point 1: Ingested Check Idea Validity

**When:** After ingestion, reviewing INCUBATING checks
**Question:** Is this extracted risk signal valid and actionable for D&O
underwriting?
**Action:** Keep (proceed to develop) or deprecate (mark DEPRECATED with
reason)

### Review Point 2: Section and Pillar Assignment

**When:** INCUBATING -> DEVELOPING transition
**Question:** Which worksheet section (1-7) does this check belong to?
What is its risk pillar?
**Action:** Set `section` (1=Exec Summary, 2=Company Overview,
3=Financial, 4=Market, 5=Governance, 6=Litigation, 7=Benchmark)
and `pillar` (FINANCIAL, MARKET, GOVERNANCE, LITIGATION, etc.)

### Review Point 3: Threshold Definition

**When:** During DEVELOPING phase
**Question:** What threshold makes this check fire? What constitutes
a red/yellow/clear result?
**Action:** Set `threshold_type` (percentage, count, value, tiered,
boolean, info) and `threshold_value` (e.g., `>9.5%`, `<1.0`)

### Review Point 4: Scoring Factor Mapping

**When:** During DEVELOPING phase
**Question:** Which of the 10 scoring factors (F1-F10) should this
check contribute to?
**Action:** Set `scoring_factor` to one of:
- F1 (Prior Litigation), F2 (Stock Decline), F3 (Restatement/Audit)
- F4 (IPO/SPAC/M&A), F5 (Guidance Misses), F6 (Short Interest)
- F7 (Volatility), F8 (Financial Distress), F9 (Governance)
- F10 (Officer Stability)
- Or `None` for info-only checks

### Review Point 5: Redundancy Assessment

**When:** Before DEVELOPING -> ACTIVE promotion
**Question:** Does this check overlap with existing active checks?
**Tool:** `learning.py: find_redundant_pairs()` (Jaccard similarity
of fire sets across analysis runs)
**Action:** If Jaccard >= 0.85 with an existing check, either:
- Merge the checks (deprecate one, enhance the other)
- Keep both with documented justification

### Review Point 6: Activation Approval

**When:** DEVELOPING -> ACTIVE transition
**Question:** Has the traceability chain been verified? Has the check
been tested against sample data?
**Tool:** `traceability.py: get_activation_readiness()` -- must return
status `COMPLETE`
**Action:** Final approval to transition to ACTIVE

---

## 7. Pipeline Stage Activation

Once a check reaches ACTIVE status, it enters the production pipeline
through the `BackwardCompatLoader` (`src/do_uw/knowledge/compat_loader.py`).

### How Active Checks Enter the Pipeline

```
KnowledgeStore (knowledge.db)
    |
    v
BackwardCompatLoader.load_checks()
    |  - Loads all checks from store (via raw metadata or reconstruction)
    |  - Appends industry-specific checks from active playbook (if any)
    |
    v
BrainConfig.checks
    |
    v
AnalyzeStage.run() [src/do_uw/stages/analyze/__init__.py]
    |  - Filters to execution_mode == "AUTO"
    |  - Calls execute_checks(checks, state.extracted, state.company)
    |
    v
check_engine.execute_checks() [src/do_uw/stages/analyze/check_engine.py]
    |  - Maps check data requirements to ExtractedData fields
    |  - Evaluates thresholds
    |  - Produces CheckResult objects
    |
    v
state.analysis (CheckResult list stored on AnalysisState)
```

### Which Pipeline Stages Consume Knowledge Store Data

| Stage         | Module                                     | What it consumes                          |
|---------------|--------------------------------------------|-------------------------------------------|
| **ANALYZE**   | `stages/analyze/check_engine.py`           | All ACTIVE checks with `execution_mode=AUTO`, evaluated against extracted data |
| **SCORE**     | `stages/score/factor_scoring.py`           | Scoring rules from `scoring.json` via `BackwardCompatLoader.load_scoring()` |
| **SCORE**     | `stages/score/pattern_detection.py`        | Risk patterns from `patterns.json` via `BackwardCompatLoader.load_patterns()` |
| **BENCHMARK** | `stages/benchmark/market_position.py`      | Sector baselines from `sectors.json` via `BackwardCompatLoader.load_sectors()` |

### Industry Playbook Integration

Industry playbooks add sector-specific checks automatically:

1. **RESOLVE stage** identifies the company's SIC code
2. `KnowledgeStore.get_playbook_for_sic()` matches against playbook
   SIC ranges
3. The matched `playbook_id` is stored on `state.active_playbook_id`
4. When `BackwardCompatLoader` is constructed with `playbook_id`,
   `load_checks()` calls `_append_industry_checks()` to merge
   industry-specific checks with the standard check set
5. Five industry playbooks are available:
   - Technology/SaaS
   - Biotech/Pharma
   - Financial Services
   - Energy/Utilities
   - Healthcare

### Data Flow Summary

```
External Document
    |
    | do-uw knowledge ingest
    v
Knowledge Store (INCUBATING checks + notes)
    |
    | Human review + field assignment
    v
Knowledge Store (DEVELOPING checks)
    |
    | Traceability validation + approval
    v
Knowledge Store (ACTIVE checks)
    |
    | BackwardCompatLoader.load_checks()
    v
ANALYZE stage (execute_checks)
    |
    | CheckResult objects
    v
SCORE stage (factor scoring + pattern detection)
    |
    | ScoringResult, RiskClassification
    v
RENDER stage (Word/PDF/Markdown worksheet)
```

---

## Appendix: Key Source Files

| File                                          | Role                                     |
|-----------------------------------------------|------------------------------------------|
| `src/do_uw/knowledge/ingestion.py`            | Document ingestion pipeline              |
| `src/do_uw/knowledge/lifecycle.py`            | State machine transitions + history      |
| `src/do_uw/knowledge/models.py`               | ORM models (Check, CheckHistory, Note)   |
| `src/do_uw/knowledge/store.py`                | CRUD operations + FTS5 search            |
| `src/do_uw/knowledge/provenance.py`           | Audit trail queries                      |
| `src/do_uw/knowledge/learning.py`             | Effectiveness tracking + redundancy      |
| `src/do_uw/knowledge/traceability.py`         | Traceability chain validation            |
| `src/do_uw/knowledge/traceability_constants.py` | Ground truth: known sources, paths, factors |
| `src/do_uw/knowledge/compat_loader.py`        | Pipeline integration adapter             |
| `src/do_uw/cli_knowledge.py`                  | CLI commands for knowledge operations    |
| `knowledge_docs/sidley_biotech_sca_2024.md`   | Sidley biotech study (worked example)    |

## Appendix: CLI Quick Reference

```bash
# Ingest a document
do-uw knowledge ingest <file.md> --type CLAIMS_STUDY

# Search the knowledge store
do-uw knowledge search "biotech settlement"

# View store statistics (checks by origin/status)
do-uw knowledge stats

# View learning summary (fire rates, redundancy)
do-uw knowledge learning-summary

# Migrate brain/ JSON to knowledge store
do-uw knowledge migrate

# Compose risk narratives from analysis run
do-uw knowledge narratives <TICKER>
```
