# Phase 49: Pipeline Integrity, Facets & CI Guardrails - Research

**Researched:** 2026-02-26
**Domain:** Internal pipeline architecture -- terminology rename, facet system, data traceability, CI contract testing
**Confidence:** HIGH (all findings based on direct codebase inspection)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `brain trace <SIGNAL_ID>` shows the full pipeline journey: YAML definition -> extraction source -> mapping -> evaluation result -> rendered output location
- Step-by-step vertical flow format with clear stage markers (e.g., checkmark YAML -> checkmark Extract -> cross Evaluate (SKIPPED))
- Show actual data values + status at each stage -- extracted values, thresholds, scores alongside pass/fail/skip
- Two modes: default shows results from last completed analysis run; `--blueprint` flag shows the theoretical route from YAML without needing a run
- Errors if no run exists and --blueprint not specified
- Signals own their display spec -- each signal YAML defines data, acquisition strategy, processing, evaluation, AND how that signal renders in output
- A grouping/section level exists above signals that declares what a rendered section needs: non-signal display elements (charts, tables, narrative), ordering, layout requirements
- Some grouping-level components wrap a single signal, some combine multiple data points with enrichment, some are purely display (charts)
- Facets are a metadata layer for now -- keep existing rendering sections, add facet as parallel classification. Renderer can optionally use facets. Full migration happens in a future phase.
- Claude proposes the exact organizational model during research/planning
- Fix all DEF14A Population B signals that have a viable extraction path
- Signals with no reliable extraction path -> mark as INACTIVE in YAML (explicitly off, doesn't count as SKIPPED)
- Hard CI gate on maximum SKIPPED count -- CI fails if SKIPPED exceeds threshold (target: ~34, down from ~68)
- New evaluations go live immediately -- once a signal evaluates, it appears in the next run's output with no staging gate
- Total rename -- Python classes, function names, CLI commands, YAML field names, file/directory names, config keys, log messages, test names
- `brain/checks/` directory renames to `brain/signals/`
- Big bang single commit -- one atomic commit, clean break, no backward-compatible aliases
- CI lint guard -- a CI test greps for "check" in signal-related contexts and fails if found, preventing drift back to old terminology

### Claude's Discretion
- Exact organizational model/hierarchy for facet system (proposed during research, with clear naming)
- CI lint implementation approach (avoiding false positives on generic "check" usage)
- Trace command formatting details (colors, indentation, truncation)
- Order of operations (rename first vs facets first vs parallel)

### Deferred Ideas (OUT OF SCOPE)
- Full renderer migration to facet-driven layout (this phase adds facets as metadata; future phase makes them the primary organizer)
- Non-DEF14A skipped signal remediation
- Facet-level narrative generation (AI-written analysis paragraphs per section)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NOM-01 | "check" renamed to "signal" throughout codebase -- BrainCheckEntry -> BrainSignalEntry, all CLI commands, output, docs, and internal references use consistent "signal" terminology | Codebase audit: ~2,030 references across src/ and tests/, 400 YAML entries, DuckDB schema with 19 tables. Rename scope quantified in Architecture Patterns section |
| INT-01 | System closes SKIPPED gap -- Population B DEF14A signals evaluate instead of SKIP, reducing SKIPPED from 68 toward ~34 | DEF14A extraction schema (DEF14AExtraction) already has 30+ fields. GOV mapper connects ~15 fields. Gap analysis identifies ~34 DEF14A signals with viable extraction paths in Common Pitfalls section |
| INT-02 | User can trace any signal's full data route with `do-uw brain trace <SIGNAL_ID>` -- one command shows YAML -> extraction -> mapper -> evaluator -> renderer | Existing 5-link traceability chain on CheckResult provides data. Trace command assembles from: YAML definition, ExtractionManifest, check_field_routing, check_engine, and html_checks section mapping. Architecture in Code Examples section |
| INT-03 | System verifies every evaluated signal appears in HTML output -- `do-uw brain render-audit` reports declared vs populated signals per facet | html_checks._group_checks_by_section() groups by prefix. Facet signals list provides the "declared" set. render-audit compares facet.signals vs state.analysis.check_results keys |
| FACET-01 | Facet definitions exist for every signal domain (BIZ, FIN, GOV, LIT, STOCK, EXEC, NLP, FWRD, etc.) with declared signals | 8 domains identified: BIZ(43), EXEC(20), FIN(58), FWRD(79), GOV(85), LIT(65), NLP(15), STOCK(35) = 400 total. 2 facets exist (governance, red_flags). Need 6+ more |
| FACET-02 | Every brain signal has `facet` field and complete `display` spec (value_format, source_type, threshold_context) | Currently: 0/400 have `facet` field, 23/400 have `display` spec. DisplaySpec schema exists in brain_check_schema.py. Bulk YAML update needed |
| FACET-03 | HTML rendering is driven by facet definitions, not hardcoded prefix mappings -- facets control section organization and signal grouping | html_checks.py has `_PREFIX_DISPLAY` dict (8 entries) and md_renderer.py has `_PREFIX_DISPLAY_NAMES`. Phase 49 adds facet as parallel metadata; full migration deferred per user decision |
| FACET-04 | All facet signal IDs are correct -- every declared signal maps to a real brain signal with matching ID | CI test validates facet.signals entries against actual YAML signal IDs. Load all facets, load all signal IDs, assert intersection = facet.signals |
| QA-03 | CI tests enforce brain contract -- every ACTIVE signal has data route, threshold, v6_subsection_ids, and factor/peril mapping; new signal without these fails tests | No test_brain_contract.py exists yet. Test reads all YAML, validates required fields. Schema: BrainCheckEntry already defines required fields |
</phase_requirements>

## Summary

Phase 49 is a large-scope internal restructuring phase with four interlocking workstreams: (1) renaming "check" to "signal" across the entire codebase, (2) adding facet metadata to all 400 signals plus creating facet definitions for all 8 domains, (3) building the `brain trace` and `brain render-audit` CLI commands, and (4) fixing Population B DEF14A signals to reduce SKIPPED count while adding CI contract tests.

The rename is the riskiest workstream due to sheer scope (~2,030 references in Python code + 400 YAML entries + DuckDB schema), but the "big bang single commit" decision simplifies it by avoiding dual-naming complexity. The facet system builds on the existing FacetSpec schema (Phase 48) and DisplaySpec already in brain_check_schema.py. The trace command leverages the existing 5-link traceability chain already populated on every CheckResult. The DEF14A signal fix primarily requires wiring existing DEF14AExtraction fields through the governance mapper to signals that currently have no data route.

**Primary recommendation:** Execute the rename FIRST as a single atomic commit, then layer facets and tracing on the renamed codebase. This avoids doing rename-during-development and ensures grep-based CI lint works immediately.

## Proposed Facet Organizational Model

### Three-Layer Hierarchy

The system needs three distinct concepts with non-overlapping nomenclature:

| Layer | Name | Definition | Example |
|-------|------|-----------|---------|
| **Atom** | **Signal** | A single evaluable unit declared in `brain/signals/**/*.yaml`. Has an ID, threshold, extraction source, and evaluation result. | `GOV.BOARD.independence` |
| **Molecule** | **Facet** | A grouping of related Signals declared in `brain/facets/*.yaml`. Defines display_type, signal ordering, and display_config. A Signal belongs to exactly one Facet. | `governance` (12 GOV.* signals) |
| **Organism** | **Section** | A rendered output section that may consume one or more Facets plus non-signal display elements (charts, tables, narrative). Defined by the renderer. | "Section 5: Corporate Governance" (governance facet + board chart + narrative) |

**Why this model works:**
- **Signal** (atom): Already exists as brain check entries. Rename makes this explicit.
- **Facet** (molecule): Already started in Phase 48 with governance.yaml and red_flags.yaml. Extends naturally to all 8 domains.
- **Section** (organism): Already exists as the numbered sections in the rendered worksheet. Sections consume facets but also include charts, narrative, and enriched displays that are NOT signals.

**Key constraint:** A Signal belongs to exactly one Facet. This avoids the complexity of signals appearing in multiple facets and makes render-audit deterministic.

**Facet field on Signal YAML:**
```yaml
- id: GOV.BOARD.independence
  facet: governance
  display:
    value_format: pct_1dp
    source_type: SEC_DEF14A
    threshold_context: ""  # auto-populated at eval time
```

**Facet definition in brain/facets/governance.yaml:**
```yaml
id: governance
name: "Governance Assessment"
display_type: scorecard_table
signals:
  - GOV.BOARD.ceo_chair
  - GOV.BOARD.independence
  # ... all GOV.* signals
display_config:
  col_signal: "Governance Factor"
  col_value: "Assessment"
```

### Proposed Facet Definitions

Based on the 8 signal domains and existing prefix structure:

| Facet ID | Domain | Signal Count | display_type | Notes |
|----------|--------|-------------|--------------|-------|
| `business_profile` | BIZ | 43 | metric_table | Company classification, dependencies, competitive |
| `financial_health` | FIN | 58 | metric_table | Income, balance sheet, temporal, forensic, accounting |
| `governance` | GOV | 85 | scorecard_table | Board, compensation, rights, effectiveness (exists) |
| `litigation` | LIT | 65 | flag_list | SCA, regulatory, defense, other litigation |
| `market_activity` | STOCK | 35 | metric_table | Price, insider, short, ownership, pattern |
| `executive_risk` | EXEC | 20 | metric_table | Profile, activity, stability |
| `forward_looking` | FWRD | 79 | metric_table | Guidance, M&A, warnings, transform |
| `filing_analysis` | NLP | 15 | metric_table | MDA readability, sentiment, disclosure patterns |
| `red_flags` | (cross-cutting) | 0 | flag_list | Triggered CRFs from scoring (exists, signals=[]) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.x | CI contract tests | Already in use (4,377 tests), testpaths configured |
| pydantic | 2.10+ | Signal/Facet schemas | Already core to project (BrainCheckEntry, FacetSpec, CheckResult) |
| typer + rich | 0.15+ / 13.0+ | CLI commands (trace, render-audit) | Already used for all CLI commands |
| pyyaml | 6.0+ | YAML read/write for bulk signal updates | Already a dependency |
| duckdb | 1.4.4+ | brain.duckdb schema updates | Already core storage |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | latest | Lint after rename to catch import errors | Every commit |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual YAML bulk update | ruamel.yaml (round-trip preserving) | overkill -- signals are machine-generated YAML, comments are minimal |
| grep-based CI lint | ast-based Python analysis | grep is simpler and catches non-Python files (YAML, docs) too |

## Architecture Patterns

### Rename Scope Audit (check -> signal)

**Python source files (src/):**

| Category | File Count | Estimated References | Key Classes/Functions |
|----------|-----------|---------------------|----------------------|
| Brain module | 15 files | ~200 | `BrainCheckEntry`, `BrainCheckThreshold`, `BrainCheckProvenance`, `brain_check_schema.py`, `brain_build_checks.py`, `brain_checks` table |
| Analyze stage | 14 files | ~400 | `check_engine.py`, `check_mappers.py`, `check_evaluators.py`, `check_helpers.py`, `check_field_routing.py`, `check_results.py`, `CheckResult`, `CheckStatus` |
| Render stage | 25+ files | ~150 | `html_checks.py`, `_group_checks_by_section`, `check_results` dict keys |
| CLI | 8 files | ~100 | `cli_brain.py` (brain status/build/etc), `cli_knowledge_checks.py`, `cli_calibrate.py` |
| Models | 5 files | ~50 | `state.py` (AnalysisState.analysis.check_results), `scoring.py` |
| Knowledge | 15 files | ~200 | `feedback.py`, `calibrate.py`, `learning.py`, `store.py` |
| Tests | 40+ files | ~500 | All test files referencing check_id, CheckResult, etc |

**DuckDB schema:**
- Table `brain_checks` -> `brain_signals`
- Views: `brain_checks_current`, `brain_checks_active` -> `brain_signals_current`, `brain_signals_active`
- Column `check_id` in 7 tables (brain_checks, brain_check_runs, brain_effectiveness, brain_feedback, brain_proposals, brain_changelog, brain_causal_chains)
- All indexes referencing check tables

**YAML:**
- Directory `brain/checks/` -> `brain/signals/` (36 YAML files, 400 entries)
- Each YAML entry uses `id:` (not `check_id:`), so YAML content changes are minimal
- `checks.json` -> `signals.json` (or deprecate entirely since YAML is source of truth)

**File renames:**
- `brain_check_schema.py` -> `brain_signal_schema.py`
- `brain_build_checks.py` -> `brain_build_signals.py`
- `check_engine.py` -> `signal_engine.py`
- `check_mappers.py` -> `signal_mappers.py`
- `check_mappers_ext.py` -> `signal_mappers_ext.py`
- `check_mappers_analytical.py` -> `signal_mappers_analytical.py`
- `check_mappers_forward.py` -> `signal_mappers_forward.py`
- `check_mappers_sections.py` -> `signal_mappers_sections.py`
- `check_evaluators.py` -> `signal_evaluators.py`
- `check_helpers.py` -> `signal_helpers.py`
- `check_field_routing.py` -> `signal_field_routing.py`
- `check_results.py` -> `signal_results.py`
- `html_checks.py` -> `html_signals.py`
- `cli_knowledge_checks.py` -> `cli_knowledge_signals.py`

### Pattern 1: CI Contract Test (test_brain_contract.py)

**What:** A pytest test that loads all brain signal YAML and validates the contract.
**When to use:** Every CI run, every commit.

```python
# tests/brain/test_brain_contract.py
import yaml
from pathlib import Path

SIGNALS_DIR = Path("src/do_uw/brain/signals")
REQUIRED_FIELDS = {"id", "name", "work_type", "tier", "depth", "threshold", "provenance"}
ACTIVE_REQUIRED = {"v6_subsection_ids", "factors"}  # can be empty list but must exist

def load_all_signals():
    signals = []
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            signals.extend(data)
    return signals

def test_all_active_signals_have_data_route():
    for sig in load_all_signals():
        if sig.get("lifecycle_state") == "INACTIVE":
            continue
        assert sig.get("data_strategy"), f"{sig['id']} missing data_strategy"

def test_all_active_signals_have_threshold():
    for sig in load_all_signals():
        threshold = sig.get("threshold", {})
        assert threshold.get("type"), f"{sig['id']} missing threshold.type"

def test_all_active_signals_have_v6_subsection():
    for sig in load_all_signals():
        assert "v6_subsection_ids" in sig, f"{sig['id']} missing v6_subsection_ids"

def test_all_active_signals_have_factor_or_peril():
    for sig in load_all_signals():
        has_factor = bool(sig.get("factors"))
        has_peril = bool(sig.get("peril_ids"))
        has_chain = bool(sig.get("chain_roles"))
        work_type = sig.get("work_type")
        if work_type == "extract":
            continue  # display-only signals don't need factor mapping
        assert has_factor or has_peril or has_chain, f"{sig['id']} has no scoring linkage"

def test_facet_signal_ids_are_valid():
    signal_ids = {sig["id"] for sig in load_all_signals()}
    facets_dir = Path("src/do_uw/brain/facets")
    for yaml_path in sorted(facets_dir.glob("*.yaml")):
        facet = yaml.safe_load(yaml_path.read_text())
        for sid in facet.get("signals", []):
            assert sid in signal_ids, f"Facet '{facet['id']}' references unknown signal '{sid}'"

def test_skipped_count_below_threshold():
    """CI gate: max SKIPPED count. Requires a recent run's state.json."""
    # This test reads from the most recent test run output
    # Implementation checks state.analysis.check_results for SKIPPED count
    pass
```

### Pattern 2: Trace Command Architecture

**What:** `brain trace <SIGNAL_ID>` assembles the full data route for a signal.
**Data sources (per stage):**

| Stage | Data Source | What It Provides |
|-------|-----------|-----------------|
| YAML Definition | `brain/signals/**/*.yaml` | id, name, threshold, required_data, data_locations, data_strategy, facet, display |
| Extraction | ExtractionManifest + state.json | What extractor ran, what field was populated, raw value |
| Mapping | check_field_routing.FIELD_FOR_SIGNAL + data_strategy.field_key | Which mapper handles this signal, which field it routes to |
| Evaluation | state.analysis.check_results[signal_id] | status, value, threshold_level, evidence, trace_* fields |
| Rendering | Facet definition + html_checks._PREFIX_DISPLAY | Which section/facet displays this signal, what format |

**Blueprint mode (`--blueprint`):** Uses only YAML definition + static code analysis (no state.json needed). Shows the theoretical route by reading data_strategy, required_data, and facet membership.

**Live mode (default):** Reads the most recent state.json to show actual values at each stage.

### Pattern 3: Render Audit Architecture

**What:** `brain render-audit` compares declared signals (from facets) vs rendered signals (from state.analysis.check_results).
**Logic:**
1. Load all facet definitions -> collect all declared signal IDs
2. Load state.json -> collect all check_results keys where status != SKIPPED
3. Report: declared but not in output, in output but not declared in any facet

### Anti-Patterns to Avoid
- **Incremental rename with aliases:** The user explicitly decided "big bang, no backward-compatible aliases." Do NOT create `BrainCheckEntry = BrainSignalEntry` aliases.
- **Facet as renderer driver (premature):** The user explicitly deferred full facet-driven rendering. Keep `_PREFIX_DISPLAY` functional, add facet as parallel metadata.
- **Hand-editing 400 YAML files:** Use a script to add `facet` and `display` fields programmatically. YAML files were machine-generated (`brain_migrate_yaml.py`).
- **Broad "check" grep that false-positives:** The word "check" appears in generic English (e.g., "check if", "health check", "checksum"). The CI lint must target signal-specific contexts only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bulk YAML field addition | Manual editing of 36 files | Python script using `yaml.safe_load` / `yaml.dump` | 400 entries, error-prone manually |
| Rename across codebase | Manual find-and-replace | Scripted rename with verification (rename files, then sed/ruff) | 2,030+ references, need atomicity |
| DuckDB schema migration | Manual SQL | `brain_schema.py` DDL updates + `brain build` | Existing pattern for schema changes |

**Key insight:** The bulk operations (rename 2,030 references, add facet to 400 YAMLs) MUST be scripted, not manual. The verification (CI tests) must be automated to prevent regression.

## Common Pitfalls

### Pitfall 1: Rename Breaks Import Chains
**What goes wrong:** Renaming `check_engine.py` to `signal_engine.py` breaks every `from do_uw.stages.analyze.check_engine import ...` across the codebase. Missing even one causes ImportError at runtime.
**Why it happens:** Python imports are strings, not refactored by IDE tools in a CLI context.
**How to avoid:** After file rename + content rename, run `uv run python -c "import do_uw"` to verify all imports resolve. Then run the full test suite.
**Warning signs:** ImportError, ModuleNotFoundError in any test.

### Pitfall 2: DuckDB Column Names vs Python Names
**What goes wrong:** DuckDB schema has `check_id` columns in 7 tables. Renaming the Python references but forgetting the SQL column names (or vice versa) causes runtime SQL errors.
**Why it happens:** SQL is in string literals, not caught by Python import analysis.
**How to avoid:** The DuckDB rename requires: (1) update `_TABLES_DDL` in brain_schema.py with new column/table names, (2) add migration DDL to rename existing tables/columns, (3) update all SQL queries in brain_loader.py, brain_loader_rows.py, brain_effectiveness.py, etc. **Decision:** Since brain.duckdb is a rebuild-from-YAML cache, the simplest approach is to DROP and recreate tables with new names, then `brain build` repopulates from YAML. No data migration needed.
**Warning signs:** `duckdb.CatalogException` errors.

### Pitfall 3: Population B DEF14A Signals -- Data Route Gaps
**What goes wrong:** DEF14A signals have `data_strategy.field_key` pointing to fields like `bylaw_provisions` or `forum_selection_clause`, but the governance mapper (`check_mappers_sections.py`) doesn't populate those keys in its return dict.
**Why it happens:** The DEF14AExtraction schema was designed to extract these fields, but the mapper that converts DEF14AExtraction into the evaluator's data dict only maps ~15 of the 30+ available fields.
**How to avoid:** For each DEF14A signal that SKIPs: (1) verify DEF14AExtraction has a matching field, (2) verify the extraction LLM prompt actually populates it, (3) add the mapper line in `check_mappers_sections.py::map_governance_fields()`, (4) verify field_key in data_strategy matches.
**Warning signs:** Signal evaluates as SKIPPED despite DEF14A being acquired.

**DEF14A signals with viable extraction paths (estimated ~34):**
- GOV.BOARD.* (9 signals): board_size, independence, ceo_chair, departures, overboarding, tenure, attendance, diversity, classified_board -- most already mapped except attendance/diversity
- GOV.COMP.* (5 signals): clawback_policy, insider_ownership, dilution_rate, pay_ratio, golden_parachute -- partially mapped
- GOV.PAY.* (8 signals): ceo_total, peer_comparison, say_on_pay, structure, equity_grants, option_repricing, perquisites, severance -- partially mapped (ceo_pay_ratio mapped, others not)
- GOV.RIGHTS.* (7 signals): dual_class, voting_rights, bylaws, poison_pill, supermajority, blank_check, forum_selection -- dual_class mapped, others not
- GOV.EFFECT.* (5 signals): say_on_pay_approval, proxy_advisory, iss_score, shareholder_proposals, proxy_contest -- say_on_pay partially mapped

**Signals to mark INACTIVE (no viable extraction path):**
- Signals requiring external data sources not yet available (ISS scores, Glass Lewis, etc.)
- Signals whose DEF14A data is too inconsistently disclosed to extract reliably

### Pitfall 4: CI Lint False Positives on "check"
**What goes wrong:** A naive `grep -r "check"` matches "check if", "health check", "checksum", "typecheck", "pre-commit check", etc.
**Why it happens:** "check" is a common English word used in many non-signal contexts.
**How to avoid:** Target signal-specific patterns only:
  - `check_id` -> never appears outside signal context
  - `CheckResult` -> class name, should be `SignalResult`
  - `check_engine` -> module name, should be `signal_engine`
  - `brain/checks/` -> directory path, should be `brain/signals/`
  - `brain_checks` -> DuckDB table, should be `brain_signals`
  - Allowlist: "check if", "health check", "pre-commit", "typecheck", "checkout", "checked", "double-check"
**Warning signs:** CI lint fails on legitimate code that uses "check" as a verb.

### Pitfall 5: Facet Signal Lists Diverge from YAML
**What goes wrong:** A facet declares signal `GOV.BOARD.attendance` but the YAML file has `GOV.BOARD.meeting_attendance` (or the signal was removed/renamed).
**Why it happens:** Facet YAML and signal YAML are maintained independently.
**How to avoid:** CI test `test_facet_signal_ids_are_valid()` validates every facet signal ID exists in the actual signal YAML. Run this in every CI pass.
**Warning signs:** render-audit shows "declared but not found" signals.

## Code Examples

### Example 1: Trace Command Output Format

```
$ do-uw brain trace GOV.BOARD.independence

Signal: GOV.BOARD.independence -- Board Independence
Facet:  governance (Governance Assessment)

--- YAML Definition ---
  work_type:    evaluate
  threshold:    percentage (red: <50%, yellow: <67%, clear: >67%)
  required_data: SEC_DEF14A
  field_key:    board_independence

--- Extraction ---
  source:       DEF 14A (2025-04-15)
  extractor:    proxy_extractor -> DEF14AExtraction.independent_count
  raw_value:    10 independent of 12 total

--- Mapping ---
  mapper:       check_mappers_sections.map_governance_fields()
  field_key:    board_independence
  mapped_value: 83.3

--- Evaluation ---
  status:       CLEAR
  threshold:    >67% independent -> clear
  evidence:     "Board is 83.3% independent (10 of 12 directors)"
  factors:      [F10]

--- Rendering ---
  section:      Section 5: Corporate Governance
  facet:        governance (scorecard_table)
  display:      pct_1dp
```

### Example 2: Blueprint Mode Output

```
$ do-uw brain trace GOV.BOARD.independence --blueprint

Signal: GOV.BOARD.independence -- Board Independence
Facet:  governance (Governance Assessment)

--- YAML Definition ---
  work_type:    evaluate
  threshold:    percentage (red: <50%, yellow: <67%, clear: >67%)
  required_data: SEC_DEF14A
  field_key:    board_independence

--- Extraction Route (theoretical) ---
  source:       SEC_DEF14A -> DEF 14A
  extractor:    proxy_extractor
  target_field: DEF14AExtraction.independent_count / .board_size

--- Mapping Route (theoretical) ---
  mapper:       check_mappers_sections.map_governance_fields()
  field_key:    board_independence
  routing:      data_strategy.field_key (declarative)

--- Evaluation Route (theoretical) ---
  evaluator:    evaluate_numeric_threshold (percentage type)
  threshold:    red: <50%, yellow: <67%, clear: >67%

--- Rendering Route (theoretical) ---
  facet:        governance (scorecard_table)
  display:      pct_1dp, source: SEC_DEF14A
```

### Example 3: Render Audit Output

```
$ do-uw brain render-audit --ticker AAPL

Render Audit: AAPL (2026-02-25 run)

Facet: governance (12 declared signals)
  Rendered:  10 of 12
  Missing:   GOV.BOARD.attendance (SKIPPED), GOV.EFFECT.iss_score (SKIPPED)

Facet: financial_health (58 declared signals)
  Rendered:  52 of 58
  Missing:   6 signals (SKIPPED -- no 10-K data)

Facet: red_flags (dynamic)
  Triggered: 3 CRFs rendered

Overall: 320 / 377 active signals rendered (85%)
         57 SKIPPED (not rendered)
```

### Example 4: CI Lint Guard Pattern

```python
# tests/brain/test_signal_nomenclature.py
"""CI lint guard: ensure 'check' terminology is not used in signal contexts."""
import subprocess

# Patterns that should NOT appear in signal-related files
FORBIDDEN_PATTERNS = [
    ("check_id", "signal_id"),
    ("CheckResult", "SignalResult"),
    ("check_engine", "signal_engine"),
    ("BrainCheckEntry", "BrainSignalEntry"),
    ("brain/checks/", "brain/signals/"),
    ("brain_checks", "brain_signals"),
]

# Files/patterns to exclude from the grep
ALLOWLIST = [
    "test_signal_nomenclature.py",  # this file itself
    "*.pyc",
    "__pycache__",
]

def test_no_check_terminology_in_source():
    """Verify 'check' is not used in signal-related identifiers."""
    for old_term, new_term in FORBIDDEN_PATTERNS:
        result = subprocess.run(
            ["grep", "-rn", old_term, "src/do_uw/", "--include=*.py"],
            capture_output=True, text=True,
        )
        violations = [
            line for line in result.stdout.strip().split("\n")
            if line and not any(a in line for a in ALLOWLIST)
        ]
        assert not violations, (
            f"Found '{old_term}' (should be '{new_term}') in:\n"
            + "\n".join(violations[:10])
        )
```

## Execution Order Recommendation

Based on the dependency graph between workstreams:

**Phase 1 (Foundation):** Rename check -> signal (single atomic commit)
- This must come first because all subsequent work uses the new terminology
- Facet YAML additions reference `brain/signals/` paths
- CI lint guard tests new terminology immediately
- All subsequent plans work on the renamed codebase

**Phase 2 (Facet Metadata):** Add facet field + display spec to all 400 signals + create 6 new facet definitions
- Builds on renamed YAML structure
- Enables render-audit and trace commands to reference facets

**Phase 3 (Pipeline Fix):** Fix DEF14A Population B signals + mark INACTIVE signals
- Requires working signal engine (post-rename)
- Reduces SKIPPED count toward target ~34

**Phase 4 (Commands):** Build `brain trace` and `brain render-audit` CLI commands
- Requires facet metadata to show facet membership
- Requires post-fix SKIPPED count to demo meaningful output

**Phase 5 (CI):** Write test_brain_contract.py + CI lint guard
- Final layer that locks down the contract
- Depends on all other workstreams being complete

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "check" terminology everywhere | "signal" throughout | Phase 49 (this phase) | Consistent domain language |
| Prefix-based section grouping | Facet-based grouping (parallel) | Phase 48 schema, Phase 49 metadata | Extensible rendering |
| No contract validation | CI test suite for brain | Phase 49 (this phase) | Prevents schema drift |
| 68 SKIPPED signals | ~34 SKIPPED (target) | Phase 49 (this phase) | Better pipeline coverage |

## Open Questions

1. **Exact SKIPPED count baseline**
   - What we know: User says ~68 SKIPPED. This needs verification from a fresh AAPL run.
   - What's unclear: Exact breakdown of which signals are DEF14A-fixable vs truly INACTIVE.
   - Recommendation: Run `do-uw analyze AAPL` and count SKIPPED. Triage each one before planning detailed fixes.

2. **checks.json deprecation**
   - What we know: `checks.json` exists alongside YAML as a legacy format. `brain_build_checks.py` validates sync between them.
   - What's unclear: Can we delete checks.json entirely in this phase?
   - Recommendation: Keep checks.json in sync for now (rename to signals.json). Full deprecation is a separate concern.

3. **DuckDB column rename strategy**
   - What we know: brain.duckdb is a rebuilt cache, not persistent storage. `brain build` repopulates from YAML.
   - What's unclear: Whether to rename SQL columns in-place or drop+recreate.
   - Recommendation: Drop+recreate is simpler and brain.duckdb is expendable. Update DDL in brain_schema.py, run `brain build`.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection of all referenced files (36 YAML files, 15 brain Python modules, 14 analyze modules, 25+ render modules)
- `brain_check_schema.py` -- BrainCheckEntry with DisplaySpec (line 27-154)
- `brain_facet_schema.py` -- FacetSpec with load_all_facets (line 24-75)
- `check_results.py` -- CheckResult with 5-link traceability (line 121-264)
- `html_checks.py` -- _PREFIX_DISPLAY and _group_checks_by_section (line 37-163)
- `brain_build_checks.py` -- YAML -> DuckDB build pipeline (line 134+)
- `brain_schema.py` -- DuckDB DDL with 19 tables (line 23-498)
- `check_engine.py` -- evaluate_check dispatch and _apply_traceability (line 41-378)
- `def14a.py` -- DEF14AExtraction schema (line 19-253)
- `check_mappers_sections.py` -- map_governance_fields (line 25+)

### Secondary (MEDIUM confidence)
- Signal count per domain verified by grep: BIZ(43), EXEC(20), FIN(58), FWRD(79), GOV(85), LIT(65), NLP(15), STOCK(35) = 400
- Reference count estimate (~2,030) from grep across src/ and tests/

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in use, no new dependencies
- Architecture: HIGH - directly inspected codebase, all patterns verified
- Pitfalls: HIGH - identified from actual code paths and data flow analysis
- Facet model: MEDIUM - proposed hierarchy is sound but specific signal-to-facet assignments need verification against actual YAML content

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (internal architecture, not affected by external changes)
