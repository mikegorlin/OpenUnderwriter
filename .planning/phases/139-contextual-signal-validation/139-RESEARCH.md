# Phase 139: Contextual Signal Validation - Research

**Researched:** 2026-03-27
**Domain:** Post-ANALYZE signal cross-validation with company state context
**Confidence:** HIGH

## Summary

Phase 139 introduces a YAML-driven validation pass that runs after signal execution in the ANALYZE stage. Its job is to cross-check triggered signals against the company's actual state (years public, distress scores, executive roster, evidence text) and annotate false positives with explanatory context -- never suppressing them. This follows the brain portability principle: validation rules live in YAML, Python is a dumb executor.

The existing codebase already has scattered precursors: `should_suppress_insolvency()` in `red_flag_gates.py` (Python if/else, render-time, suppression-based), sector filtering in `signal_engine.py` (compile-time, NOT_APPLICABLE disposition), and 20 contextual lifecycle signals in `brain/signals/contextual/`. Phase 139 consolidates these patterns into a single post-ANALYZE pass with a new YAML rule format, adds an `annotations` field to `SignalResult`, and introduces negation detection and temporal executive validation.

**Primary recommendation:** Create a new `stages/analyze/contextual_validator.py` module with a `validate_signals()` function that loads YAML validation rules from `brain/config/validation_rules.yaml`, iterates over TRIGGERED signals, evaluates applicable rules against company state, and appends annotation strings to a new `annotations: list[str]` field on `SignalResult`. Insert this as a step in the ANALYZE `__init__.py` between signal execution and disposition tagging. Render-side insolvency suppression logic migrates to annotation-based display.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SIG-01 | Post-ANALYZE validation pass cross-checks triggered signals against company state | New `contextual_validator.py` module inserted after `execute_signals()` in ANALYZE `__init__.py`, before disposition tagging |
| SIG-02 | YAML-driven validation rules (not Python if/else) following brain portability principle | New `brain/config/validation_rules.yaml` file with declarative rule format; Python evaluator is a dumb executor |
| SIG-03 | IPO/offering signals suppressed for companies public > 5 years with no recent offerings | Validation rule: `applies_to` signal IDs matching `BIZ.EVENT.ipo*`, `condition` checks `company.years_public > 5`, annotation explains why |
| SIG-04 | Financial distress signals annotated when Z-Score and O-Score are both in Safe zone | Validation rule cross-references `FIN.DISTRESS.*` signals against Z-Score > 3.0 and O-Score safe zone from state |
| SIG-05 | Negation detection -- signals whose evidence says "do not have" / "no holdings" get annotated as negated | Regex-based negation pattern matching on `SignalResult.evidence` field, patterns defined in YAML |
| SIG-06 | Temporal validation -- signals referencing departed executives annotated with departure date | Cross-reference signal evidence against `extracted.governance.leadership.departures_18mo` |
| SIG-07 | Validation annotates findings (adds context), never suppresses them | `annotations: list[str]` field on `SignalResult`; status/threshold_level NEVER modified by validator |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.2 | Load validation rules YAML | Already used throughout brain/ for signal YAML loading |
| Pydantic v2 | 2.11+ | Validation rule models, SignalResult extension | Project standard for all data models |
| re (stdlib) | N/A | Negation pattern matching | No external NLP needed for keyword patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test validation rules | All unit/integration tests |

**No new dependencies required.** Everything builds on existing PyYAML + Pydantic stack already in the project.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  stages/analyze/
    contextual_validator.py     # NEW: validation engine (< 300 lines)
  brain/config/
    validation_rules.yaml       # NEW: declarative validation rules
  models/
    state.py                    # MODIFY: no changes needed (annotations go on SignalResult)
  stages/analyze/
    signal_results.py           # MODIFY: add annotations field to SignalResult
    __init__.py                 # MODIFY: insert validate_signals() call
tests/stages/analyze/
    test_contextual_validator.py  # NEW: unit tests for validator
```

### Pattern 1: YAML Validation Rule Format
**What:** Each rule declares: which signals it applies to (by ID pattern), what state condition to check, and what annotation text to produce.
**When to use:** For every cross-check between a signal result and company state.
**Example:**
```yaml
# brain/config/validation_rules.yaml
rules:
  - id: VAL.IPO.mature_company
    name: "IPO signals on mature companies"
    applies_to:
      signal_pattern: "BIZ.EVENT.ipo*"
    condition:
      type: state_check
      path: company.years_public
      op: ">"
      value: 5
      # Also check no recent offerings
      additional_checks:
        - path: extracted.market.capital_markets.offerings_3yr
          op: "empty_or_none"
    annotation: "Company has been public {years_public} years with no offerings in 3 years -- IPO exposure window is historical context only"
    rule_class: lifecycle_mismatch

  - id: VAL.FIN.distress_safe_zone
    name: "Distress signals with safe Z/O scores"
    applies_to:
      signal_pattern: "FIN.DISTRESS.*|FIN.LIQ.*|FIN.SOLV.*"
    condition:
      type: compound
      all:
        - path: extracted.financials.distress.altman_z_score.score
          op: ">"
          value: 3.0
        - path: extracted.financials.distress.ohlson_o_score.score
          op: "<"
          value: 0.5
    annotation: "Note: Altman Z-Score ({z_score}) and O-Score ({o_score}) both in safe zone"
    rule_class: contradicting_indicator

  - id: VAL.NLP.negation_detection
    name: "Negation patterns in evidence"
    applies_to:
      signal_pattern: "*"
    condition:
      type: evidence_regex
      patterns:
        - "\\bdo not have\\b"
        - "\\bno (?:material |significant )?holdings?\\b"
        - "\\bnot (?:a |an )?party\\b"
        - "\\bno (?:pending |known )?litigation\\b"
        - "\\bdoes not (?:currently )?(?:have|maintain|hold)\\b"
        - "\\bno (?:material )?exposure\\b"
    annotation: "Evidence contains negation language -- signal may be triggered from negative finding"
    rule_class: negation

  - id: VAL.EXEC.departed
    name: "Departed executive references"
    applies_to:
      signal_pattern: "EXEC.*|GOV.*"
    condition:
      type: executive_temporal
      departure_source: extracted.governance.leadership.departures_18mo
    annotation: "References {exec_name} who departed on {departure_date}"
    rule_class: temporal_staleness
```

### Pattern 2: Validation Engine Architecture
**What:** A pure function that takes signal results + state, loads YAML rules, evaluates each rule against each TRIGGERED signal, and returns annotated results in place.
**When to use:** Single call in ANALYZE __init__.py.
**Example:**
```python
# stages/analyze/contextual_validator.py
def validate_signals(
    signal_results: dict[str, dict[str, Any]],
    state: AnalysisState,
) -> dict[str, int]:
    """Post-ANALYZE contextual validation pass.

    Iterates TRIGGERED signals, evaluates YAML rules, appends annotations.
    NEVER changes signal status or threshold_level.

    Returns: summary dict {rules_evaluated, annotations_added, signals_checked}
    """
    rules = _load_validation_rules()
    summary = {"rules_evaluated": 0, "annotations_added": 0, "signals_checked": 0}

    for signal_id, result in signal_results.items():
        if result.get("status") != "TRIGGERED":
            continue
        summary["signals_checked"] += 1

        for rule in rules:
            if not _signal_matches_pattern(signal_id, rule["applies_to"]["signal_pattern"]):
                continue
            summary["rules_evaluated"] += 1

            annotation = _evaluate_rule(rule, result, state)
            if annotation:
                existing = result.get("annotations", [])
                existing.append(annotation)
                result["annotations"] = existing
                summary["annotations_added"] += 1

    return summary
```

### Pattern 3: Insertion Point in ANALYZE Pipeline
**What:** Insert after gap re-evaluation and before composites/analytical engines.
**Where:** `stages/analyze/__init__.py` around line 590, after gap search re-evaluation and before `_run_composites()`.
```python
# After gap re-evaluation, before composites
# Phase 139: Contextual signal validation
try:
    from do_uw.stages.analyze.contextual_validator import validate_signals
    val_summary = validate_signals(state.analysis.signal_results, state)
    logger.info(
        "Contextual validation: %d signals checked, %d annotations added",
        val_summary["signals_checked"],
        val_summary["annotations_added"],
    )
except Exception:
    logger.warning("Contextual validation failed (non-fatal)", exc_info=True)
```

### Anti-Patterns to Avoid
- **Suppressing signals:** NEVER change `status` from TRIGGERED to CLEAR/SKIPPED. SIG-07 is explicit: annotate, don't suppress. In D&O, hiding a finding is worse than a false positive.
- **Python if/else for rules:** All validation logic must be in YAML. The Python evaluator reads YAML conditions and evaluates them generically. No `if signal_id == "BIZ.EVENT.ipo_exposure"` in Python.
- **Modifying evidence field:** The `evidence` field is the original evaluation evidence. Annotations go in a separate `annotations` field so the original is preserved.
- **Blocking on validation failure:** Validation is non-critical. Wrap in try/except, log warning, continue pipeline.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Negation detection | Full NLP dependency parser | Regex patterns in YAML | Evidence text is machine-generated with predictable phrasing; 10 regex patterns cover 95%+ of cases |
| Executive departure matching | Fuzzy name matching library | Exact substring match on names from `departures_18mo` | Executive names in evidence come from the same extraction pipeline that populates departures |
| Signal pattern matching | Custom glob implementation | `fnmatch.fnmatch` from stdlib | Standard glob patterns (`BIZ.EVENT.ipo*`) are sufficient |
| State path traversal | Custom dotted path resolver | Existing `getattr` chain pattern used throughout codebase | Consistent with how `signal_resolver.py` and other modules access nested state |

## Common Pitfalls

### Pitfall 1: Accidentally Suppressing Instead of Annotating
**What goes wrong:** Developer adds logic that changes `status` from TRIGGERED to CLEAR when validation rule matches.
**Why it happens:** The existing `should_suppress_insolvency()` pattern does exactly this -- suppress at render time.
**How to avoid:** The validator function signature should make this impossible: it takes `dict[str, dict[str, Any]]` (signal results) and ONLY writes to the `annotations` key. Add a test that verifies no signal status changes after validation.
**Warning signs:** Any test that checks `status == "CLEAR"` after validation ran on a TRIGGERED signal.

### Pitfall 2: Hardcoded Signal IDs in Python
**What goes wrong:** Developer adds `if signal_id == "BIZ.EVENT.ipo_exposure"` in the validator.
**Why it happens:** It's faster to write than a YAML rule.
**How to avoid:** The validator should have ZERO knowledge of specific signal IDs. It reads `applies_to.signal_pattern` from YAML and uses glob matching. Python code is generic.
**Warning signs:** Any signal ID string literal in `contextual_validator.py`.

### Pitfall 3: Overly Broad Negation Patterns
**What goes wrong:** A negation regex like `\bno\b` matches "no material weakness" (a positive finding for D&O) and incorrectly annotates it as negated.
**Why it happens:** Simple negation detection is linguistically hard.
**How to avoid:** Patterns must be specific phrases ("do not have", "no holdings", "not a party") not single words. Test against real evidence strings from pipeline runs. Include negative test cases for phrases that contain "no" but aren't negations.
**Warning signs:** Annotation rate > 15% of triggered signals for negation rules.

### Pitfall 4: State Path Navigation Failures
**What goes wrong:** YAML rule references `extracted.financials.distress.altman_z_score.score` but the actual path requires `.value` accessor on SourcedValue.
**Why it happens:** State uses Pydantic models with `SourcedValue[T]` wrappers; signal_results is already serialized to dict via `model_dump()`.
**How to avoid:** The state path resolver must handle both dict access (for signal_results) and attribute access (for AnalysisState). Use the same `getattr` chain pattern as `signal_resolver.py`. Test with real state.json files.
**Warning signs:** Rules that never fire because path resolution silently returns None.

### Pitfall 5: Breaking Existing Insolvency Suppression
**What goes wrong:** Removing `should_suppress_insolvency()` from render code before validation-based annotations are wired into the render path.
**Why it happens:** Desire to consolidate, but render code depends on the suppression function today.
**How to avoid:** Phase 1: Add validation annotations alongside existing suppression. Phase 2 (optional/future): Migrate render code to check annotations instead of calling `should_suppress_insolvency()`. The existing function stays until render code is updated.
**Warning signs:** CRF insolvency flag appearing on AAPL/MSFT after changes.

## Code Examples

### SignalResult Annotations Field
```python
# stages/analyze/signal_results.py - ADD to SignalResult class
annotations: list[str] = Field(
    default_factory=list,
    description=(
        "Contextual validation annotations added post-ANALYZE. "
        "These provide explanatory context for triggered signals "
        "that may be false positives given company state. "
        "NEVER used to suppress -- only to inform the underwriter."
    ),
)
```

### YAML Rule Evaluation (Generic)
```python
# stages/analyze/contextual_validator.py
import fnmatch
import re
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.state import AnalysisState

RULES_PATH = Path(__file__).parent.parent.parent / "brain" / "config" / "validation_rules.yaml"

def _load_validation_rules() -> list[dict[str, Any]]:
    """Load validation rules from brain YAML."""
    if not RULES_PATH.exists():
        return []
    with open(RULES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])

def _signal_matches_pattern(signal_id: str, pattern: str) -> bool:
    """Check if signal_id matches a pipe-separated glob pattern."""
    for p in pattern.split("|"):
        if fnmatch.fnmatch(signal_id, p.strip()):
            return True
    return False

def _resolve_state_path(state: AnalysisState, path: str) -> Any:
    """Navigate dotted path on state, handling SourcedValue.value."""
    obj: Any = state
    for part in path.split("."):
        if obj is None:
            return None
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            obj = getattr(obj, part, None)
        # Unwrap SourcedValue
        if hasattr(obj, "value") and not isinstance(obj, (str, int, float, bool)):
            obj = obj.value
    return obj
```

### Negation Detection
```python
def _check_negation(evidence: str, patterns: list[str]) -> str | None:
    """Check if evidence text contains negation patterns."""
    if not evidence:
        return None
    evidence_lower = evidence.lower()
    for pattern in patterns:
        if re.search(pattern, evidence_lower):
            return f"Evidence contains negation language (matched: '{pattern}')"
    return None
```

### Executive Temporal Validation
```python
def _check_departed_executives(
    evidence: str,
    departures: list[dict[str, Any]],
) -> str | None:
    """Check if signal evidence references a departed executive."""
    if not evidence or not departures:
        return None
    evidence_lower = evidence.lower()
    for dep in departures:
        name = dep.get("name", "")
        if name and name.lower() in evidence_lower:
            date = dep.get("departure_date", "unknown date")
            return f"References {name} who departed on {date}"
    return None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Render-time suppression (`should_suppress_insolvency`) | Post-ANALYZE annotation (keeps signal, adds context) | Phase 139 | Signals never hidden; underwriter sees full picture with explanatory notes |
| Python if/else in render code | YAML-driven validation rules | Phase 139 | Brain portability: rules travel with YAML, not embedded in Python |
| No negation detection | Evidence regex matching | Phase 139 | Catches "do not have X" triggers that are informational, not risk indicators |
| No temporal executive validation | Cross-reference departures_18mo | Phase 139 | Stale executive findings get departure date annotation |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` ([tool.pytest.ini_options]) |
| Quick run command | `uv run pytest tests/stages/analyze/test_contextual_validator.py -x` |
| Full suite command | `uv run pytest tests/stages/analyze/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIG-01 | validate_signals() runs on TRIGGERED signals and adds annotations | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_validate_signals_adds_annotations -x` | Wave 0 |
| SIG-02 | Rules loaded from YAML, no signal IDs in Python | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_no_hardcoded_signal_ids -x` | Wave 0 |
| SIG-03 | IPO signals annotated for companies public > 5 years | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_ipo_mature_company_annotation -x` | Wave 0 |
| SIG-04 | Distress signals annotated when Z/O safe | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_distress_safe_zone_annotation -x` | Wave 0 |
| SIG-05 | Negation patterns in evidence detected | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_negation_detection -x` | Wave 0 |
| SIG-06 | Departed executive signals annotated with date | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_departed_executive_annotation -x` | Wave 0 |
| SIG-07 | Validation NEVER changes signal status | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py::test_status_never_modified -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/analyze/test_contextual_validator.py -x`
- **Per wave merge:** `uv run pytest tests/stages/analyze/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/analyze/test_contextual_validator.py` -- covers SIG-01 through SIG-07
- [ ] Framework install: N/A -- pytest already configured

## Open Questions

1. **Render-side consumption of annotations**
   - What we know: Annotations will be stored on signal results as `list[str]`. Context builders read signal results via `_signal_consumer.py`.
   - What's unclear: Whether annotations should appear inline with signal evidence or as separate tooltip/footnote in the worksheet.
   - Recommendation: Store annotations on SignalResult; render changes are out of scope for Phase 139 (future work to display them). The existing `should_suppress_insolvency()` stays in place during this phase.

2. **Number of initial validation rules**
   - What we know: Requirements specify 4 rule types (IPO lifecycle, distress safe zone, negation, executive temporal).
   - What's unclear: How many specific signal ID patterns each rule needs.
   - Recommendation: Start with 4-6 rules covering the explicit requirements. The YAML format is extensible; more rules can be added per-evidence as patterns emerge from QA.

3. **SourcedValue unwrapping in state path resolution**
   - What we know: State uses `SourcedValue[T]` wrappers where `.value` holds the actual data.
   - What's unclear: Whether all paths the rules need traverse through SourcedValue or some are plain attributes.
   - Recommendation: The path resolver auto-detects and unwraps SourcedValue objects. Test with real state.json to confirm paths.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/analyze/__init__.py` -- ANALYZE pipeline flow, insertion points
- `src/do_uw/stages/analyze/signal_results.py` -- SignalResult model, all existing fields
- `src/do_uw/stages/analyze/signal_engine.py` -- Signal execution, mechanism dispatch
- `src/do_uw/stages/analyze/mechanism_evaluators.py` -- Existing contextual evaluator pattern
- `src/do_uw/stages/score/red_flag_gates.py` -- Existing `should_suppress_insolvency()` implementation
- `src/do_uw/brain/signals/biz/events.yaml` -- IPO signal definitions (BIZ.EVENT.ipo_exposure)
- `src/do_uw/brain/signals/contextual/*.yaml` -- 20 existing contextual lifecycle signals
- `src/do_uw/models/state.py` -- AnalysisResults model, signal_results storage

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/render/context_builders/` -- How render code consumes signal results (for future annotation display)
- `src/do_uw/stages/benchmark/quick_screen.py` -- Executive departure checking pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing libraries
- Architecture: HIGH -- clear insertion point in ANALYZE pipeline, well-understood signal result model
- Pitfalls: HIGH -- patterns from existing false trigger fixes (Phase 33) and insolvency suppression (Phase 129)

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable internal architecture, no external dependency risk)
