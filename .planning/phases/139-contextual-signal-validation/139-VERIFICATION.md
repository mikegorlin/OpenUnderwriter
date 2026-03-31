---
phase: 139-contextual-signal-validation
verified: 2026-03-28T00:32:13Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 139: Contextual Signal Validation — Verification Report

**Phase Goal:** Triggered signals are cross-checked against company state so that false positives (IPO signals on 30-year-old companies, insolvency signals on mega-caps with safe Z-Scores) get annotated with explanatory context rather than silently suppressed.

**Verified:** 2026-03-28T00:32:13Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `validate_signals()` iterates TRIGGERED signals and appends annotations without changing status | VERIFIED | `validate_signals()` checks `result.get("status") != "TRIGGERED"` to skip non-triggered; only appends to `result["annotations"]`; never writes to `status` or `threshold_level`. Confirmed by `test_status_never_modified` (PASS). |
| 2 | New validation rules can be added in YAML without Python changes | VERIFIED | All rule dispatch is by `condition.type` string from YAML; no signal ID literals exist in Python. Adding a new YAML entry with a known condition type is sufficient. Confirmed by `test_no_hardcoded_signal_ids` and the docstring in `validation_rules.yaml`. |
| 3 | IPO signals on mature companies (>5 years public) get `lifecycle_mismatch` annotation | VERIFIED | `VAL.IPO.mature_company` rule in YAML matches `BIZ.EVENT.ipo*`, state_check on `company.years_public > 5`, annotation text: "Company has been public {years_public} years -- IPO exposure window is historical context only". Tests `test_ipo_mature_company_annotation` and `test_ipo_young_company_no_annotation` both pass. |
| 4 | FIN.DISTRESS signals annotated when Z-Score >3.0 and O-Score <0.5 | VERIFIED | `VAL.FIN.distress_safe_zone` compound rule covers `FIN.DISTRESS.*\|FIN.LIQ.*\|FIN.SOLV.*`. Both Z-Score and O-Score sub-conditions must pass. `test_distress_safe_zone_annotation` (z=4.5, o=0.2, PASS) and `test_distress_danger_zone_no_annotation` (z=1.5, no annotation, PASS). |
| 5 | Negation patterns in evidence text produce negation annotation | VERIFIED | `VAL.NLP.negation_detection` rule with 6 regex patterns covers `"do not have"`, `"no holdings"`, `"not a party"`, `"no pending litigation"`, etc. Correctly excludes `"no material weakness"` (positive finding). `test_negation_detection` and `test_negation_no_false_positive` both pass. |
| 6 | Signals referencing departed executives get `temporal_staleness` annotation with departure date | VERIFIED | `VAL.EXEC.departed` rule on `EXEC.*\|GOV.*` resolves `extracted.governance.leadership.departures_18mo`, checks if executive name appears in evidence, returns annotation with `{exec_name}` and `{departure_date}`. `test_departed_executive_annotation` passes with "John Smith" / "2025-06-15". |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/analyze/contextual_validator.py` | YAML-driven validation engine; exports `validate_signals` | VERIFIED | 355 lines, fully substantive. Contains `_load_validation_rules`, `_signal_matches_pattern`, `_resolve_state_path`, `_evaluate_state_check`, `_evaluate_compound`, `_evaluate_evidence_regex`, `_evaluate_executive_temporal`, `_evaluate_rule`, `validate_signals`. |
| `src/do_uw/brain/config/validation_rules.yaml` | Declarative validation rules for 4 rule classes; contains `VAL.IPO.mature_company` | VERIFIED | 68 lines. Contains all 4 required rules: `VAL.IPO.mature_company`, `VAL.FIN.distress_safe_zone`, `VAL.NLP.negation_detection`, `VAL.EXEC.departed`. All rules have required keys: `id`, `name`, `rule_class`, `applies_to`, `condition`, `annotation`. |
| `tests/stages/analyze/test_contextual_validator.py` | Unit tests for all 7 SIG requirements; min 150 lines | VERIFIED | 450 lines, 15 test functions covering all 7 SIG requirements across 7 test classes. All 15 tests pass (0.41s). |
| `src/do_uw/stages/analyze/signal_results.py` (modified) | `annotations: list[str]` field on SignalResult | VERIFIED | Field exists at line 197 with `default_factory=list` and descriptive docstring explicitly noting "NEVER used to suppress". |
| `src/do_uw/stages/analyze/__init__.py` (modified) | Pipeline wiring with non-fatal try/except | VERIFIED | Phase 139 block at lines 590-600, positioned after gap re-evaluation (line 587) and before Phase 50 composites (line 602). Follows established pattern with `logger.info` on success and `logger.warning` with `exc_info=True` on failure. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `contextual_validator.py` | `validation_rules.yaml` | `yaml.safe_load` in `_load_validation_rules()` | VERIFIED | Line 42: `data = yaml.safe_load(f)`. RULES_PATH resolves correctly via `Path(__file__).parent.parent.parent / "brain" / "config" / "validation_rules.yaml"`. |
| `contextual_validator.py` | `signal_results.py` | writes `annotations` list on signal dicts | VERIFIED | Lines 335-347: `if "annotations" not in result: result["annotations"] = []` followed by `result["annotations"].append(annotation)`. Works against both in-memory dicts (from `state.analysis.signal_results`) and SignalResult model_dump output. |
| `analyze/__init__.py` | `contextual_validator.validate_signals` | lazy import in pipeline | VERIFIED | Line 592: `from do_uw.stages.analyze.contextual_validator import validate_signals`. Called with `state.analysis.signal_results` and `state` at line 593. |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces annotations on existing signal dicts, not UI-rendered components. The data flow is: TRIGGERED signal dict → rule evaluation → annotation appended to `result["annotations"]` list → persisted in `state.analysis.signal_results`. No rendering surface introduced in this phase.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 15 validator tests pass | `uv run pytest tests/stages/analyze/test_contextual_validator.py -x -v` | 15 passed in 0.41s | PASS |
| No hardcoded signal IDs in Python | `grep -P '"[A-Z]{2,}\.[A-Z]+\.[a-z_]+"' contextual_validator.py` | No matches | PASS |
| 4 VAL rules in YAML | `grep "VAL\." validation_rules.yaml \| wc -l` | 4 lines | PASS |
| annotations field in SignalResult | `grep -c "annotations" signal_results.py` | 2 matches (field def + description) | PASS |
| Pipeline ordering correct | `grep -n "Gap re-eval\|Phase 139\|Phase 50" analyze/__init__.py` | 587, 590, 602 — correct order | PASS |
| Broader analyze suite regressions | `uv run pytest tests/stages/analyze/ -x --tb=no -q` | 128 passed, 1 pre-existing failure | PASS (pre-existing) |

**Note on pre-existing failure:** `tests/stages/analyze/test_inference_evaluator.py::TestSingleValueFallback::test_single_value_returns_info` fails. Git log confirms this test was last modified in Phase 32 (commit `bcdb9e1c`) — predates Phase 139 by many phases. The SUMMARY explicitly documented it as out-of-scope. Not caused by this phase.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SIG-01 | 139-01-PLAN | Post-ANALYZE validation pass cross-checks triggered signals against company state | SATISFIED | `validate_signals()` loops only `status == "TRIGGERED"` signals; pipeline wired at line 590 of `__init__.py` after all signal evaluation completes |
| SIG-02 | 139-01-PLAN | YAML-driven validation rules (not Python if/else) | SATISFIED | Zero signal ID string literals in `contextual_validator.py`; all pattern matching via YAML `applies_to` + `fnmatch.fnmatch`; `test_no_hardcoded_signal_ids` passes |
| SIG-03 | 139-01-PLAN | IPO/offering signals [annotated] for companies public > 5 years | SATISFIED | `VAL.IPO.mature_company` rule implemented and tested. **Note:** REQUIREMENTS.md says "suppressed" but this directly contradicts SIG-07 ("never suppresses them"). Plan correctly resolves this conflict by implementing annotation. The SIG-07 constraint is explicitly non-negotiable for D&O. |
| SIG-04 | 139-01-PLAN | Financial distress signals annotated when Z-Score and O-Score both in safe zone | SATISFIED | `VAL.FIN.distress_safe_zone` compound rule covers `FIN.DISTRESS.*\|FIN.LIQ.*\|FIN.SOLV.*` with both conditions required |
| SIG-05 | 139-01-PLAN | Negation detection — signals with "do not have" / "no holdings" evidence get annotated | SATISFIED | `VAL.NLP.negation_detection` with 6 regex patterns; false-positive exclusion for "no material weakness" correctly implemented |
| SIG-06 | 139-01-PLAN | Temporal validation — signals referencing departed executives annotated with departure date | SATISFIED | `VAL.EXEC.departed` rule resolves `extracted.governance.leadership.departures_18mo`; returns annotation with exec name and departure date |
| SIG-07 | 139-01-PLAN | Validation annotates findings (adds context), never suppresses | SATISFIED | `validate_signals()` never writes to `status`; docstring on `annotations` field reads "NEVER used to suppress"; `test_status_never_modified` passes |

**Requirements coverage: 7/7 — all SIG requirements satisfied**

**Requirements inconsistency noted:** SIG-03 in REQUIREMENTS.md uses the word "suppressed" which directly contradicts SIG-07's prohibition on suppression. The implementation correctly follows SIG-07 (non-negotiable for D&O) and the PLAN's explicit intent. REQUIREMENTS.md SIG-03 wording should be updated to say "annotated" to match SIG-07 and the actual implementation.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/stages/analyze/test_inference_evaluator.py` | — | Pre-existing failing test (unrelated to Phase 139) | Info | Out-of-scope; predates this phase by many commits |

No anti-patterns in Phase 139 artifacts:
- No TODO/FIXME/placeholder comments in new files
- No empty implementations (`return null`, `return {}`)
- No hardcoded signal IDs in Python
- No stub patterns — all 4 rule evaluators are fully implemented

---

### Human Verification Required

None — all behaviors are mechanically verifiable. The annotation mechanism is pure logic (pattern matching, state path resolution, string formatting). No UI rendering or visual output introduced in this phase.

---

### Gaps Summary

No gaps. All 6 observable truths verified, all 5 artifacts substantive and wired, all 3 key links confirmed, all 7 SIG requirements satisfied, 15/15 tests passing.

**One requirements document inconsistency to resolve (not a code gap):** SIG-03 in `.planning/REQUIREMENTS.md` says "suppressed" but the correct behavior (matching SIG-07, the PLAN, and the implementation) is "annotated." The checkboxes in REQUIREMENTS.md remain unchecked (still showing `- [ ]`) but that is a documentation update task, not a code gap.

---

_Verified: 2026-03-28T00:32:13Z_
_Verifier: Claude (gsd-verifier)_
