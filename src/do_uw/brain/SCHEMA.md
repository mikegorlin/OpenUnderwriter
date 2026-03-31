# Brain Check Schema — Unified YAML Knowledge Model

**Version:** 1.0 (Phase 44)
**Status:** Canonical — all checks/*.yaml files are validated against this spec.
**Location:** `src/do_uw/brain/SCHEMA.md`

This document is the single source of truth for what a valid check looks like. Every plan in Phase 44 (44-02 through 44-05) builds to this contract. Any deviation from this spec is a bug in the YAML file, not a gap in the spec.

---

## 1. Overview

Every check in `brain/signals/**/*.yaml` is a **self-describing knowledge unit** across three orthogonal axes:

1. **work_type** — what the check does (the operation)
2. **risk_position** — where it sits in the D&O liability framework (the framework linkage)
3. **acquisition_tier** — how hard it is to get the data (the pipeline cost)

These three axes, combined with presentation fields (`worksheet_section`, `display_when`) and provenance metadata, make each check fully autonomous: a consumer reading the YAML knows what the check does, why it matters, how to get the data, where to display it, and where the knowledge came from — without consulting any other file.

**DuckDB is a pure cache.** Nothing enters DuckDB (`brain.duckdb`) that is not first declared in a YAML check file. The `brain build` command rebuilds DuckDB from YAML. If DuckDB is deleted, `brain build` restores it in seconds.

---

## 2. Three-Axis Model

### Axis 1 — work_type (what the check does)

The `work_type` field classifies the operation the check performs. It replaces the deprecated `content_type` field and collapses `category` and `signal_type` into a single canonical dimension.

| work_type | Operation | Old content_type |
|-----------|-----------|-----------------|
| `extract` | Pulls structured data from filings; no judgment, just retrieval. Returns a value or "Not Available". | MANAGEMENT_DISPLAY (99 checks) |
| `evaluate` | Applies threshold logic to an extracted value; produces a rating (red/yellow/clear). | EVALUATIVE_CHECK (280 checks) |
| `infer` | Combines multiple signals into a higher-order finding; connects dots across checks. | INFERENCE_PATTERN (21 checks) |

**Decision rule:** If the check returns a number or string from a filing with no judgment → `extract`. If it compares a value to a threshold → `evaluate`. If it synthesizes two or more other checks into a conclusion → `infer`.

### Axis 2 — risk_position (where in the D&O framework)

Risk position is expressed through four sub-fields. Together they locate the check within the causal chain model.

#### 2a. layer (required)

| layer | Meaning |
|-------|---------|
| `hazard` | Root cause vulnerability — an inherent company characteristic that creates exposure (e.g., aggressive revenue recognition culture). |
| `signal` | Observable indicator that a hazard is activating (e.g., CFO resignation + restatement in same quarter). |
| `peril_confirming` | Direct evidence a peril has materialized (e.g., securities class action filed). |

#### 2b. factors (optional list)

List of D&O scoring factor IDs (F1–F10) that this check affects. Include only when the check contributes to a scored factor. Empty list `[]` or omit entirely if unscored.

#### 2c. peril_ids (optional list)

List of peril IDs from `brain/framework/perils.yaml` that this check informs. Use `[]` if the check is not yet linked to a peril. Cross-validated during `brain build` — IDs must exist in perils.yaml.

#### 2d. chain_roles (optional dict)

Maps a causal chain ID (from `brain/framework/causal_chains.yaml`) to this check's role in that chain.

Valid roles:

| role | Meaning |
|------|---------|
| `trigger` | This check's finding initiates the causal chain. |
| `amplifier` | This check's finding worsens the chain outcome. |
| `mitigator` | This check's finding weakens or interrupts the chain. |
| `evidence` | This check provides corroborating evidence for the chain. |

Example: `{ CH_GOV_001: trigger }` means this check is the trigger event in governance causal chain 001.

Use `{}` if not yet linked. Set `unlinked: true` when `chain_roles` is `{}`. The `brain build` pipeline counts unlinked checks and reports them as INFO — they do not fail the build.

### Axis 3 — acquisition_tier (how hard to get the data)

Derived from the `required_data` field values. Classifies the pipeline cost to acquire the check's input data.

| acquisition_tier | Data sources | required_data examples |
|-----------------|-------------|----------------------|
| `L1` | Structured XBRL or machine-readable filing data | `SEC_10K`, `SEC_10Q`, `SEC_8K`, `XBRL_INCOME`, `XBRL_BALANCE` |
| `L2` | Filing text items requiring prose extraction or NLP | `item_1`, `item_7`, `item_9a`, `item_1a` (risk factors) |
| `L3` | Web, market, or court data | `MARKET_PRICE`, `NEWS`, `COURT_RECORDS`, `WEB_SEARCH` |
| `L4` | Derived — computed from other checks or composites | Sources are check IDs, not data source names |

**Rule:** Set the highest-cost tier present. If a check requires both L1 and L3 sources, it is `L3`. If computed from other checks entirely, it is `L4`.

---

## 3. Required Fields

Every check in `checks/**/*.yaml` MUST have all of the following fields. A check missing any required field will cause `brain build` to fail with a validation error.

| Field | Type | Valid values | Description |
|-------|------|-------------|-------------|
| `id` | `str` | Domain prefix format: `DOMAIN.SUBDOMAIN.name` | Unique check identifier. Domain prefix drives file assignment (see Section 6). Must be globally unique across all YAML files. |
| `name` | `str` | Free text | Human-readable check name. Used in worksheet headers and UI. |
| `work_type` | `enum` | `extract` \| `evaluate` \| `infer` | Classifies the operation (Axis 1). |
| `layer` | `enum` | `hazard` \| `signal` \| `peril_confirming` | Risk framework layer (Axis 2a). |
| `acquisition_tier` | `enum` | `L1` \| `L2` \| `L3` \| `L4` | Data acquisition cost (Axis 3). |
| `required_data` | `list[str]` | Data source names or check IDs | Which data sources this check needs to run. Determines acquisition_tier. |
| `worksheet_section` | `str` | Semantic string | Named section of the underwriting worksheet where this check appears. Examples: `governance`, `financial`, `litigation`, `management`, `stock_activity`, `forward_looking`, `business_overview`. |
| `display_when` | `str` | `always` \| `has_data` \| `fired` \| `critical_only` | Controls when this check appears in the rendered worksheet. `always` = show regardless of value; `has_data` = show only when data was retrieved; `fired` = show only when threshold breached; `critical_only` = show only when tier=1 and threshold red. |
| `provenance` | `dict` | See Section 5 | Origin metadata — who created this check, from what source, when. Required field; value may be `{}` for migrated checks. |

---

## 4. Optional Fields

These fields are included only when applicable. Including an optional field with a null/empty value is equivalent to omitting it. The `brain build` validator warns (does not fail) when optional fields are present with null values for fields that have conditional requirements.

| Field | Type | When to include | Description |
|-------|------|----------------|-------------|
| `factors` | `list[str]` | Check affects D&O scoring | F1–F10 scoring factor IDs. Example: `[F3, F9]`. |
| `peril_ids` | `list[str]` | Check linked to a peril | IDs from `framework/perils.yaml`. Use `[]` if unlinked. Cross-validated in `brain build`. |
| `chain_roles` | `dict` | Check linked to a causal chain | Maps chain_id → role. Use `{}` if unlinked. Cross-validated in `brain build`. |
| `unlinked` | `bool` | Always when chain_roles is `{}` | Set `true` when `chain_roles` is empty. Auto-set by `brain build` if omitted. |
| `threshold` | `dict` | work_type is `evaluate` | Threshold definition. Required for evaluate checks. See threshold structure below. |
| `data_locations` | `dict` | Data source has known location | Maps source name → list of filing sections/items. Example: `{ SEC_PROXY: [board_composition] }`. |
| `execution_mode` | `str` | Non-AUTO checks only | `AUTO` (default) or `MANUAL`. MANUAL checks require human input during ACQUIRE. |
| `claims_correlation` | `float` | Empirically known | 0.0–1.0. Correlation between this check firing and securities class action claims. Include only when derived from empirical data. |
| `tier` | `int` | Non-default criticality | 1 (critical), 2 (standard, default), 3 (informational). Default is 2 if omitted. |
| `depth` | `int` | Non-default depth | 1 (surface), 2 (standard, default), 3 (deep). Default is 2 if omitted. |
| `pattern_ref` | `str` | work_type is `infer` ONLY | Pattern ID from `brain_patterns` DuckDB table. Only valid on infer-type checks. |
| `plaintiff_lenses` | `list[str]` | Check relevant to specific plaintiff class | `SHAREHOLDERS`, `BONDHOLDERS`, `REGULATORS`, `EMPLOYEES`. Include only the relevant classes. |
| `v6_subsection_ids` | `list[str]` | Check linked to v6 taxonomy | IDs like `"4.1"`, `"7.2"` from taxonomy.yaml. |
| `amplifier` | `str \| null` | Check is a scoring amplifier | The check ID of the primary check this amplifies. Only on amplifier checks. |
| `amplifier_bonus_points` | `float` | amplifier is set | Bonus points added to the primary check's score when this check also fires. Only when `amplifier` is set. |
| `sector_adjustments` | `dict` | Industry-specific thresholds differ | Maps sector name → threshold overrides. Example: `{ FINANCIAL: { red: "< 0.40" } }`. |
| `extraction_hints` | `dict` | NLP-domain checks (NLP.*) | NLP/regex patterns to guide extraction. Structure: `{ patterns: [...], negative_patterns: [...] }`. Only for NLP-prefix checks. |
| `critical_red_flag` | `bool` | Check triggers a score ceiling | Set `true` if this check's firing triggers a maximum score ceiling rule (from red_flags.json escalation triggers). |
| `data_strategy` | `dict` | Pipeline routing needed | Structure: `{ field_key: str, primary_source: str }`. Used by ACQUIRE stage to route data requests. |

**threshold structure** (required for evaluate checks):

```yaml
threshold:
  type: ratio          # ratio | integer | boolean | categorical | percentage | count
  red: "< 0.50"        # Condition string for red alert
  yellow: "0.50-0.75"  # Condition string for yellow caution
  clear: "> 0.75"      # Condition string for clear/green
```

---

## 5. Provenance Block

The provenance block records the origin and validation history of each check. It enables the live learning loop: new knowledge from articles, enforcement actions, and academic research can be traced back to its source.

```yaml
provenance:
  origin: migrated_from_json       # Source of this check entry
  confidence: inherited             # Confidence level
  last_validated: null              # ISO 8601 date or null
  source_url: null                  # URL of article/filing that originated this check
  source_date: null                 # ISO 8601 date of source document
  source_author: null               # Author of source article (if applicable)
  added_by: null                    # "brain add" CLI user annotation
```

**origin values:**

| value | Meaning |
|-------|---------|
| `migrated_from_json` | Migrated from signals.json during Phase 44. Legacy check; provenance not known. |
| `manual` | Written by a human directly in YAML without using the brain add CLI. |
| `brain_add` | Added via the `brain add` CLI command. source_url and source_date MUST be populated. |
| `ingest_pipeline` | Added by an automated pipeline. Must include source_url. |

**Migrated checks:** All checks migrated from signals.json during Plan 44-02 receive:
- `origin: migrated_from_json`
- `confidence: inherited`
- All other provenance fields: `null`

**brain add CLI checks:** Checks written via `brain add` MUST have `source_url` and `source_date` populated. The CLI enforces this via `--source` and `--date` flags. Any check with `origin: brain_add` missing `source_url` fails `brain validate`.

---

## 6. File Layout Rules

### Directory structure

Checks are stored in `brain/signals/**/*.yaml`. The `brain build` pipeline reads the glob `checks/**/*.yaml`, so subdirectory structure is transparent to all consumers.

**Domain prefix drives file assignment:** The first segment of a check's `id` determines which subdirectory it belongs in.

| ID prefix | Directory | Est. check count | File strategy |
|-----------|-----------|-----------------|--------------|
| `BIZ.*` | `checks/biz/` | 43 | Subdirs: `core.yaml`, `model.yaml`, `operations.yaml` |
| `FIN.*` | `checks/fin/` | 58 | Subdirs: `income.yaml`, `balance.yaml`, `cash.yaml`, `quality.yaml` |
| `GOV.*` | `checks/gov/` | 85 | Subdirs: `board.yaml`, `audit.yaml`, `exec.yaml`, `activist.yaml`, `pay.yaml`, `rights.yaml`, `effect.yaml` |
| `EXEC.*` | `checks/exec/` | 20 | Single file: `exec.yaml` (at limit — monitor) |
| `LIT.*` | `checks/lit/` | 65 | Subdirs: `sca.yaml`, `sec.yaml`, `private.yaml`, `employment.yaml` |
| `STOCK.*` | `checks/stock/` | 35 | Subdirs: `price.yaml`, `short.yaml`, `insider.yaml` |
| `FWRD.*` | `checks/fwrd/` | 79 | Subdirs: `guidance.yaml`, `spac.yaml`, `ma.yaml`, `transform.yaml` |
| `NLP.*` | `checks/nlp/` | 15 | Single file: `nlp.yaml` (~375 lines, within limit) |

### 500-line rule

The CLAUDE.md anti-context-rot rule applies to YAML files as well as Python files. At approximately 25 lines per check:

- `gov/` at 85 checks × 25 lines = ~2,125 lines → **MUST** use subdirectory structure
- `fwrd/` at 79 checks × 25 lines = ~1,975 lines → **MUST** use subdirectory structure
- `biz/`, `fin/`, `lit/`, `stock/` all exceed 500 lines → **MUST** use subdirectory structure
- `exec/` is at the limit → monitor; split if any checks are added
- `nlp/` is within limit → single file acceptable

### YAML format rules

- Each YAML file contains a **list** of check objects (not a mapping/dict)
- List separator: each check is a top-level list item starting with `- id: ...`
- No anchors or aliases (`&`, `*`) — each check is fully self-contained
- Comments are encouraged for non-obvious fields
- Provenance block is always last, after all functional fields

---

## 7. Deprecated Fields

The following fields from `signals.json` are **eliminated** in the unified YAML schema. They do not appear in any `checks/**/*.yaml` file.

| Deprecated field | Replacement | Rationale |
|-----------------|-------------|-----------|
| `pillar` | Removed entirely | Redundant with `work_type` + `layer`. The pillar was a display grouping that combined what the check does and where it sits in the framework. Now these are orthogonal axes. |
| `category` | Removed entirely | Was `CONTEXT_DISPLAY` / `DECISION_DRIVING` / `RED_FLAG_SIGNAL` — a proxy for `work_type`. Collapsed into the explicit `work_type` enum. |
| `signal_type` | Removed entirely | Was `STRUCTURAL` / `PATTERN` / `QUANTITATIVE` — redundant classification that overlapped with both `work_type` and `layer`. |
| `hazard_or_signal` | Replaced by `layer` | Was `HAZARD` / `SIGNAL` / `PERIL_CONFIRMING` — exact semantic match with `layer` field. Kept in DuckDB for backward compatibility until all callers updated. |
| `content_type` | Replaced by `work_type` | Was `MANAGEMENT_DISPLAY` / `EVALUATIVE_CHECK` / `INFERENCE_PATTERN` — see mapping in Section 2. Kept in DuckDB for backward compatibility until all callers updated. |
| `section` (int) | Replaced by `worksheet_section` (str) | Old field used integers 1–7 to encode worksheet sections. New field uses semantic strings (e.g., `"governance"`, `"financial"`). Mapping table in brain_loader._SECTION_MAP. |

**Backward compatibility note:** `hazard_or_signal` and `content_type` are kept as columns in the DuckDB `brain_signals` table during the Phase 44 transition. The `brain_loader.py` backward compatibility shim populates these old field names from new canonical fields so downstream code (score, analyze, render stages) does not break before callers are updated. These columns will be dropped in a follow-on cleanup phase after all callers have been migrated.

---

## 8. Complete Annotated Example

The following is a complete, valid check entry for `GOV.BOARD.independence`. It demonstrates all common fields with inline comments explaining each decision.

```yaml
# GOV.BOARD.independence — Board Independence Ratio
# File: checks/gov/board.yaml
#
# This check evaluates whether the board has sufficient independent directors.
# It is a signal-layer check because independence itself is observable; the
# underlying hazard (insider-captured board) is a structural condition.

- id: GOV.BOARD.independence             # Unique ID — domain.subdomain.name format
                                          # GOV prefix → file lives in checks/gov/
  name: Board Independence Ratio          # Human-readable; shown in worksheet headers

  # === Axis 1: work_type ===
  # This check compares a ratio to a threshold → evaluate
  work_type: evaluate

  # === Axis 2: risk_position ===
  layer: signal                           # Observable indicator (board composition is public)
                                          # The hazard is "captured board"; this is the signal
  factors: [F9]                           # F9 = Governance Quality scoring factor
  peril_ids: [P_GOV_FAIL]                 # Cross-validated against framework/perils.yaml
  chain_roles:                            # Role in causal chain CH_GOV_001
    CH_GOV_001: trigger                   # Low independence triggers the governance failure chain
  unlinked: false                         # Has chain_roles, so not unlinked

  # === Axis 3: acquisition_tier ===
  acquisition_tier: L1                    # Data from SEC proxy filing (structured)
  required_data: [SEC_PROXY]              # Proxy statement has board composition table
  data_locations:
    SEC_PROXY: [board_composition]        # Specific section within the proxy

  # === Evaluation logic ===
  threshold:
    type: ratio                           # Ratio of independent directors to total board
    red: "< 0.50"                         # Majority insider-controlled → red
    yellow: "0.50-0.75"                   # Borderline → yellow
    clear: "> 0.75"                       # Strong majority independent → clear
  execution_mode: AUTO                    # ACQUIRE stage can retrieve this automatically
  claims_correlation: 0.62               # 62% of SCAs in dataset had <75% independence

  # === Presentation ===
  worksheet_section: governance           # Appears in "Governance" section of worksheet
  display_when: always                    # Always show — independence is a base-rate factor
  v6_subsection_ids: ["4.1"]             # v6 taxonomy section 4.1: Board Composition
  plaintiff_lenses: [SHAREHOLDERS]        # Most relevant to shareholder plaintiffs

  # === Quality metadata ===
  tier: 2                                 # Standard criticality
  depth: 2                               # Standard analysis depth

  # === Provenance ===
  provenance:
    origin: migrated_from_json           # Migrated from signals.json in Phase 44
    confidence: inherited                 # Inherits confidence from original entry
    last_validated: null                  # Not yet validated against current literature
    source_url: null                      # Original source unknown (pre-provenance era)
    source_date: null
    source_author: null
    added_by: null
```

---

## 9. Article → Brain Decomposition Guide

When an article, enforcement action, academic study, or litigation filing contains knowledge that belongs in the brain, follow this 8-step workflow to add it correctly.

**Step 1: Read and extract the specific claim.**
Do not capture vague impressions ("governance problems"). Capture the specific, quantified, or legally-grounded claim. Example: "Boards with more than 3 insider directors have a 2.3x higher securities class action rate (Stanford SCAC, 2023)."

**Step 2: Decision — new check, threshold update, or chain evidence?**
- New pattern the brain does not yet track → new check
- Existing check with updated threshold or correlation → update existing check's `threshold.red/yellow/clear` or `claims_correlation`
- Evidence that corroborates an existing causal chain → add `chain_roles` entry to the relevant check, or update `provenance.source_url` on an existing check
- Out of scope (process inefficiency, product failure) → do not add; note why

**Step 3 (new check only): Determine work_type.**
- Does the check retrieve a value from a filing? → `extract`
- Does the check compare a value to a threshold? → `evaluate`
- Does the check synthesize two or more other checks into a conclusion? → `infer`

**Step 4 (new check only): Determine layer and acquisition_tier.**
- Layer: Is this a root cause condition (hazard), an observable indicator (signal), or direct evidence of materialized harm (peril_confirming)?
- acquisition_tier: What data sources does it need? L1 (XBRL), L2 (filing text), L3 (web/market/court), or L4 (derived)?

**Step 5: Write the YAML entry.**
- Place in the correct domain file based on the ID prefix
- Populate `provenance.source_url` (the article URL or citation) and `provenance.source_date` (ISO date)
- Set `provenance.origin: brain_add` and `provenance.added_by: <your name or handle>`
- Set `provenance.confidence: medium` (single source) or `high` (corroborated by 2+ independent sources)

**Step 6: Determine chain linkage.**
- Does this check fit an existing causal chain in `framework/causal_chains.yaml`?
- If yes: add the chain ID and role to `chain_roles`; set `unlinked: false`
- If no existing chain fits: leave `chain_roles: {}` and `unlinked: true`; document the potential new chain in a comment

**Step 7: Run `brain build` to validate and load into DuckDB.**

```bash
uv run do-uw brain build
```

The build command will:
- Validate your YAML against this schema (Pydantic model)
- Cross-validate `peril_ids` against `framework/perils.yaml`
- Cross-validate `chain_roles` keys against `framework/causal_chains.yaml`
- Report any validation errors (does not fail on unlinked checks)
- Wipe and rebuild `brain_signals` table (preserves all other tables)
- Print a summary: N checks loaded, M unlinked, K errors

**Step 8: Run `brain validate` and tests.**

```bash
uv run do-uw brain validate
uv run pytest tests/brain/ -x -q
```

The validate command performs a post-build sanity check: check count matches YAML count, all cross-references resolve, no duplicate IDs. Tests must pass before committing the new check.

---

### Worked Example: Article Decomposition End-to-End

**Source article:** Hypothetical research note — "Stanford SCAC data 2010-2023 shows boards where insiders hold >40% of seats have 2.8x higher securities class action filing rate compared to boards with <25% insider representation."

This example walks through all 8 steps above with real YAML output and CLI commands.

---

**Step 1: Identify the specific claim**

Extract the quantified, sourceable claim: **Insider board concentration >40% → 2.8x higher SCA filing rate** (Stanford SCAC, 2023). This is quantified (2.8x), bounded (>40% vs <25%), and sourced (SCAC dataset 2010-2023).

---

**Step 2: Decision — new check, threshold update, or chain evidence?**

Search for existing coverage:

```bash
grep -r "board independence\|insider" src/do_uw/brain/signals/gov/ -l
# Returns: board.yaml
grep "independence\|insider" src/do_uw/brain/signals/gov/board.yaml | head -5
# Shows: GOV.BOARD.independence with threshold red: "< 0.50"
```

Finding: `GOV.BOARD.independence` exists with threshold `red: "< 0.50"` (50% independent). The article provides evidence for a **tighter danger zone at >40% insider** (60% insider = 40% independent). This is distinct enough to warrant a **new check** — `GOV.BOARD.insider_concentration` — focused specifically on the >40% insider danger zone. The existing `GOV.BOARD.independence` threshold could also be tightened, but that is a separate update.

Decision: **Add new check** `GOV.BOARD.insider_concentration`.

---

**Step 3: Determine work_type**

The check compares a computed ratio (insider_pct) to a threshold (>40%). This is an `evaluate` check — it applies threshold logic to an extracted value.

---

**Step 4: Determine layer and acquisition_tier**

- **layer = signal**: Insider board concentration is an observable indicator. The underlying hazard is "captured board governance"; this check surfaces the signal.
- **acquisition_tier = L1**: `insider_pct` is derivable from SEC proxy filing data (structured XBRL/table data). Proxy statements contain board composition tables with director independence classifications.

---

**Step 5: Write the YAML entry**

```yaml
- id: GOV.BOARD.insider_concentration
  name: Insider Board Concentration (>40%)
  work_type: evaluate
  layer: signal
  acquisition_tier: L1

  # Risk position
  factors: [F9]
  peril_ids: []
  chain_roles: {}
  unlinked: true

  # Data acquisition
  required_data: [SEC_PROXY]
  data_locations:
    SEC_PROXY: [board_composition, director_independence]

  # Evaluation
  threshold:
    type: ratio
    red: "> 0.40"
    yellow: "0.25-0.40"
    clear: "< 0.25"
  execution_mode: AUTO
  claims_correlation: 0.71
  tier: 2
  depth: 2

  # Presentation
  worksheet_section: governance
  display_when: has_data
  v6_subsection_ids: ["4.1"]
  plaintiff_lenses: [SHAREHOLDERS]

  # Provenance
  provenance:
    origin: brain_add
    confidence: medium
    last_validated: "2026-02-25"
    source_url: https://example.com/scac-study-2023
    source_date: "2023-11-15"
    source_author: Stanford Securities Class Action Clearinghouse
    added_by: null
```

Note: `confidence: medium` because this is a single source. If corroborated by a second independent study, upgrade to `high`.

---

**Step 6: Determine chain linkage**

Review `framework/causal_chains.yaml` for governance chains. Suppose no existing chain captures the "insider concentration → governance failure → derivative suit" path precisely. Set `chain_roles: {}` and `unlinked: true`. Add a comment proposing a new chain:

```yaml
# TODO: Link to new causal chain CH_GOV_insider_concentration when created.
# Proposed chain: high insider concentration (trigger) → governance capture →
# self-dealing → derivative suit (peril).
chain_roles: {}
unlinked: true
```

---

**Step 7: Run brain add**

```bash
uv run do-uw brain add \
  --domain gov \
  --source "https://example.com/scac-study-2023" \
  --date "2023-11-15"
# Opens $EDITOR with template pre-populated with source and date.
# Paste the YAML entry from Step 5 (replacing the template content).
# Save and close the editor.
```

Expected output:

```
Added check 'GOV.BOARD.insider_concentration' to src/do_uw/brain/signals/gov/board.yaml
Running brain build...
Brain Build Complete

  Loaded 401 checks (284 unlinked) from 36 YAML files
  Perils migrated:       ...
brain build complete — new check is active
```

---

**Step 8: Verify with brain validate and brain provenance**

```bash
uv run do-uw brain validate
# Expected: VALIDATION PASSED: 401 checks valid, 0 warnings
```

```bash
uv run do-uw brain provenance GOV.BOARD.insider_concentration
# Expected output:
#
# Check: GOV.BOARD.insider_concentration
# File:  src/do_uw/brain/signals/gov/board.yaml
# Name:  Insider Board Concentration (>40%)
#
# Provenance:
#   origin:          brain_add
#   confidence:      medium
#   source_url:      https://example.com/scac-study-2023
#   source_date:     2023-11-15
#   source_author:   Stanford Securities Class Action Clearinghouse
#   last_validated:  2026-02-25
#   added_by:        null
#
# Risk position:
#   work_type:        evaluate
#   layer:            signal
#   acquisition_tier: L1
#   factors:          ['F9']
#   peril_ids:        []
#   chain_roles:      {}
#   unlinked:         True
```

This completes the live learning loop: article claim → check YAML → brain build → provenance trace.

---

## 10. Section Mapping: int → semantic string

The old `signals.json` used integer section numbers (1–7). The `brain_loader._SECTION_MAP` translates between the old and new systems during the backward compatibility transition.

| Old section int | New worksheet_section string | Description |
|----------------|----------------------------|-------------|
| 1 | `company_profile` | Business model, industry, company background |
| 2 | `governance` | Board, audit committee, executive compensation |
| 3 | `management` | Leadership team, experience, insider activity |
| 4 | `financial` | Income, balance sheet, cash flow, quality |
| 5 | `litigation` | Securities class actions, SEC enforcement, private suits |
| 6 | `stock_activity` | Price behavior, short interest, insider trading |
| 7 | `forward_looking` | Guidance, M&A, SPAC, restructuring, transformation |

Checks that do not cleanly map to a single section should use the section where they most frequently appear in the worksheet. If a check spans two sections (e.g., a financial metric with litigation implications), assign to the primary section and note the secondary in a comment.

---

## Appendix: Validation Summary

The following invariants are enforced by `brain build` and `brain validate`:

| Invariant | Enforcement level | Action on failure |
|-----------|------------------|------------------|
| All required fields present | ERROR | Build fails; check not loaded |
| work_type is valid enum value | ERROR | Build fails; check not loaded |
| layer is valid enum value | ERROR | Build fails; check not loaded |
| acquisition_tier is valid enum value | ERROR | Build fails; check not loaded |
| id is globally unique across all YAML files | ERROR | Build fails; duplicate reported |
| peril_ids reference existing peril IDs in perils.yaml | ERROR | Build fails; invalid reference reported |
| chain_roles keys reference existing chain IDs in causal_chains.yaml | ERROR | Build fails; invalid reference reported |
| pattern_ref only on work_type: infer checks | WARNING | Build continues; check flagged |
| threshold present on work_type: evaluate checks | WARNING | Build continues; check flagged |
| brain_add checks have source_url and source_date | ERROR (validate only) | validate fails; build continues |
| unlinked check count matches (chain_roles == {}) count | INFO | Reported in build summary |
| Total check count matches expected (set during migration) | INFO | Reported in build summary |
