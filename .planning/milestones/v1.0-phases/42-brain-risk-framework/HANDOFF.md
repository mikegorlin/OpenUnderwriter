# Phase 42: Brain Risk Framework Restructure — Handoff v2

## Session Date: 2026-02-23

## Status: Waves 1-4 CODE COMPLETE, needs fixes + scoring presentation work

## Immediate Fix Needed

**`brain build` fails** because `build_framework()` in `brain_migrate_framework.py` does `DELETE FROM brain_perils` but the table doesn't exist in the existing brain.duckdb yet.

**Fix:** Add `create_schema(conn)` call at the top of `build_framework()`:
```python
from do_uw.brain.brain_schema import create_schema
def build_framework(conn):
    create_schema(conn)  # Ensure Phase 42 tables exist
    ...
```

After this fix, run `uv run python -m do_uw brain build` to verify.

## What's Complete

### Wave 1: YAML Framework + Layer Renames ✅
- 5 YAML files in `brain/framework/` (source of truth)
- Layer renames: `hazard` → `peril_indicator`, `risk_characteristic` → `risk_modifier`
- All references fixed across codebase (5+ files in src/, 5+ test files)
- `pyyaml` added to pyproject.toml, `uv sync` done
- `brain build` CLI command added to cli_brain.py

### Wave 2: Causal Chains + Re-tagging ✅
- 16 causal chains in causal_chains.yaml (all check IDs validated)
- 3 invalid check IDs fixed in YAML
- `peril_id` and `chain_ids` columns in brain_checks DDL
- `tag_checks_with_perils_and_chains()` function ready

### Wave 3: Coverage Matrix + Gap Detection ✅
- `brain_coverage_matrix` view in schema
- `brain_check_effectiveness` view in schema
- `brain coverage-gaps` CLI command in cli_brain_ext.py

### Wave 4: Human Query Interface ✅
- `cli_brain_explore.py` (499 lines) with 6 commands
- Registered in cli_brain.py as explore sub-app

### Tests ✅
- `test_brain_framework.py` (392 lines, 23 tests)
- `test_brain_schema.py` updated (19 tables, 11 views)
- All 269 brain tests pass

## USER REQUESTS NOT YET ADDRESSED

### 1. Scoring Presentation on Worksheet (HIGH PRIORITY)
User says: "I want all these schools of thought and models presented for scoring" and "right now it's a mess of random thoughts with random scores"

**What needs to happen:**
- The HTML/Word worksheet scoring section should be restructured around:
  - **Peril Model**: Group findings by the 8 D&O perils (Securities, Fiduciary, Regulatory, etc.)
  - **Causal Chain View**: Show how triggered checks connect into claim pathways
  - **Frequency × Severity**: Each factor tagged as frequency driver, severity driver, or both
- Instead of flat "check X = RED, check Y = YELLOW", present as:
  - "Securities Claim Risk: HIGH — stock dropped 25% (trigger), insiders sold pre-drop (amplifier)"
  - "Fiduciary Breach Risk: LOW — strong governance (mitigator), no activist pressure"
- This is a RENDER stage change, primarily in the scoring section templates

### 2. QA Function (MEDIUM PRIORITY)
User says: "you should have a QA function where you always review the final product for both content accuracy and presentation"

**What needs to happen:**
- Automated quality review step after rendering
- Check content accuracy (data matches state, no None/N/A where data exists)
- Check presentation quality (professional formatting, no debug artifacts)
- Fix issues with verified data
- Prevent recurring issues

### 3. Professional Report Quality (MEDIUM PRIORITY)
User says: "S&P/Bloomberg report quality"
- Review actual output HTML/Word/PDF for professional quality
- Compare against Bloomberg/S&P report conventions
- Fix formatting, layout, density issues

## Files Modified This Session

```
MODIFIED:
  src/do_uw/brain/brain_schema.py         — 3 new tables, 2 new views, new columns
  src/do_uw/brain/enrichment_data_ext.py  — hazard→peril_indicator rename
  src/do_uw/brain/brain_enrich.py         — risk_modifier default, stat keys
  src/do_uw/brain/brain_migrate.py        — risk_modifier default, new columns
  src/do_uw/brain/brain_writer.py         — risk_modifier default
  src/do_uw/cli_brain.py                  — brain build command, explore sub-app
  src/do_uw/cli_brain_ext.py              — coverage-gaps command
  src/do_uw/knowledge/feedback.py         — risk_modifier default
  tests/brain/test_brain_enrich.py        — updated layer values
  tests/brain/test_brain_writer.py        — updated layer values
  tests/brain/test_brain_schema.py        — updated table/view counts
  tests/test_cli_brain.py                 — updated layer values
  tests/knowledge/test_backtest.py        — updated layer values
  pyproject.toml                          — pyyaml dependency

NEW:
  src/do_uw/brain/framework/__init__.py
  src/do_uw/brain/framework/risk_model.yaml
  src/do_uw/brain/framework/perils.yaml
  src/do_uw/brain/framework/taxonomy.yaml
  src/do_uw/brain/framework/causal_chains.yaml
  src/do_uw/brain/brain_migrate_framework.py
  src/do_uw/cli_brain_explore.py
  tests/brain/test_brain_framework.py
```

## Next Session Priorities

1. **Fix `brain build`** — add `create_schema(conn)` call, verify it runs
2. **Run `brain build` + `brain explore framework`** — verify all tables populated
3. **Run pipeline on WWD** — verify output unchanged (no regression)
4. **Scoring presentation redesign** — restructure worksheet scoring around perils/chains
5. **QA function** — automated quality review of rendered output
6. **Report quality review** — run reports, compare to Bloomberg/S&P standards
