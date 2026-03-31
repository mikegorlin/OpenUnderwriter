# Phase 115: do_context Infrastructure - Research

**Researched:** 2026-03-18
**Domain:** Brain signal template system, ANALYZE stage extension, CI enforcement
**Confidence:** HIGH

## Summary

Phase 115 extends the brain signal YAML schema with `presentation.do_context` template-driven D&O commentary, builds an evaluation engine in ANALYZE to render those templates against signal results, migrates 4 hardcoded Python distress commentary functions to YAML, and adds a CI gate preventing new hardcoded D&O commentary.

The existing codebase provides strong patterns to follow. `PresentationSpec` already has `context_templates: dict[str, str]` -- the new `do_context` field is the same type with a different purpose. The `_apply_traceability()` function in `signal_engine.py` is the exact pattern for a new `_apply_do_context()` post-evaluation hook. `SignalResultView` in `_signal_consumer.py` is a frozen dataclass that needs a new `do_context: str` field.

**Primary recommendation:** Follow existing patterns exactly -- add `do_context: dict[str, str]` to `PresentationSpec`, add `do_context: str = ""` to `SignalResult`, create `do_context_engine.py` in ANALYZE with a single `render_do_context()` function, and wire it as a post-evaluation step in `execute_signals()`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Per-status templates** -- `presentation.do_context` is a dict keyed by signal outcome: `TRIGGERED_RED`, `TRIGGERED_YELLOW`, `CLEAR`, etc. Each value is a template string with placeholders
- **Separate field** -- `do_context` lives alongside existing `context_templates` on `PresentationSpec`, not merged into it. Different purpose
- **Available variables** -- `{value}`, `{score}` (alias), `{zone}`, `{threshold}`, `{threshold_level}`, `{evidence}`, `{source}`, `{confidence}`, plus `{company}`, `{ticker}` from state, plus `{details.*}` for any key from the signal's details dict
- **Graceful missing variables** -- Missing variables resolve to empty string, log warning
- **Evaluated in ANALYZE stage** -- `do_context_engine.py` renders templates right after signal evaluation, stores on `SignalResult.do_context`
- **Compound key lookup** -- Engine tries `TRIGGERED_RED` first, falls back to `TRIGGERED`, then `DEFAULT`, then empty string
- **New field on SignalResult** -- `do_context: str = ""` added to existing Pydantic model
- **Phase 115 migrates only 4 distress functions** -- `altman_do_context()`, `beneish_do_context()`, `piotroski_do_context()`, `ohlson_do_context()`
- **Delete Python functions after migration** -- once YAML do_context produces identical output
- **Keep data builder functions** -- `build_altman_trajectory()` and `build_piotroski_components()` stay
- **All signal types can carry do_context** -- Schema doesn't restrict by content_type
- **Pattern-based CI detection** -- scan `context_builders/` and Jinja2 templates for D&O evaluative terms
- **Progressive enforcement** -- FAIL on Phase 115 scope (4 distress functions), WARN on Phase 116 targets
- **Golden snapshot tests** -- capture current Python function output, assert YAML engine produces identical strings
- **Basic validation in `brain health` and `brain audit`** -- validate template syntax, check variable references

### Claude's Discretion
- Exact implementation of do_context engine module structure
- How to handle `details.*` variable resolution (dot-path parsing)
- Whether `_distress_do_context.py` gets renamed/restructured after deleting the 4 commentary functions
- CI gate test file location and naming
- Exact regex patterns for the CI gate

### Deferred Ideas (OUT OF SCOPE)
- Interactive `brain preview-do-context SIGNAL_ID` command
- do_context coverage threshold in CI (e.g., "must be >50%")
- Templating in do_context for cross-signal references
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Brain signal YAML schema supports `presentation.do_context` field with template-driven D&O commentary | Add `do_context: dict[str, str]` to `PresentationSpec` (line 459 of brain_signal_schema.py). Same type as existing `context_templates`. PresentationSpec uses `extra="forbid"` so the field MUST be added explicitly |
| INFRA-02 | do_context engine in ANALYZE evaluates templates against signal results | New `do_context_engine.py` module. Called after signal evaluation in `execute_signals()`, follows `_apply_traceability()` pattern |
| INFRA-03 | 4 hardcoded distress functions migrated to brain YAML do_context blocks | Add `do_context` blocks to relevant signals in `fin/forensic.yaml` and `fin/accounting.yaml`. Delete 4 Python functions from `_distress_do_context.py` |
| INFRA-04 | Context builders consume do_context strings from signal results via standard accessor | Add `do_context: str` to `SignalResultView` dataclass, add `get_signal_do_context()` to `_signal_consumer.py`, modify `financials_evaluative.py` to consume |
| INFRA-05 | Templates render do_context strings as-is -- zero D&O interpretation in Jinja2 | Modify `distress_indicators.html.j2` to display do_context strings instead of inline Jinja2 conditionals. CI gate prevents regression |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x (project standard) | Schema validation for `PresentationSpec.do_context` field | Already used for all models in project |
| Python `str.format_map()` | stdlib | Template variable resolution with safe missing-key handling | No external dependency needed; `format_map()` with custom dict handles missing keys gracefully |
| PyYAML | existing | Brain YAML signal loading | Already used throughout brain/ |
| pytest | existing | Golden snapshot tests, CI gate tests | Project standard test framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` (stdlib) | stdlib | CI gate pattern scanning for D&O evaluative terms | Pattern detection in Python files and Jinja2 templates |
| `ast` (stdlib) | stdlib | CI gate string literal extraction from Python files | More accurate than regex for detecting string literals containing D&O terms |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `str.format_map()` | Jinja2 templates | Jinja2 is heavy for simple variable substitution; `format_map()` is simpler, faster, and sufficient for `{variable}` placeholders |
| AST-based CI scanning | Pure regex scanning | AST is more accurate for Python (extracts string literals only, ignores comments), but regex is simpler for Jinja2 templates. Use both |

## Architecture Patterns

### Recommended Module Structure
```
src/do_uw/stages/analyze/
  do_context_engine.py     # NEW: Template evaluation engine
  signal_engine.py         # MODIFIED: Call do_context after evaluation
  signal_results.py        # MODIFIED: Add do_context field

src/do_uw/brain/
  brain_signal_schema.py   # MODIFIED: Add do_context to PresentationSpec

src/do_uw/stages/render/context_builders/
  _signal_consumer.py      # MODIFIED: Add do_context to SignalResultView
  _distress_do_context.py  # MODIFIED: Delete 4 commentary functions, keep 2 data builders
  financials_evaluative.py # MODIFIED: Consume do_context from signal results

tests/stages/analyze/
  test_do_context_engine.py # NEW: Engine unit tests
tests/brain/
  test_do_context_ci_gate.py # NEW: CI gate enforcement test
tests/
  test_do_context_golden.py  # NEW: Golden snapshot comparison tests
```

### Pattern 1: Template Evaluation with Safe Missing Variables
**What:** Use `str.format_map()` with a `defaultdict` that returns `""` for missing keys
**When to use:** Every do_context template evaluation
**Example:**
```python
from collections import defaultdict

class SafeFormatDict(dict):
    """Dict that returns empty string for missing format keys."""
    def __missing__(self, key: str) -> str:
        logger.warning("do_context template missing variable: %s", key)
        return ""

def render_do_context(
    template: str,
    signal_result: SignalResult,
    company_name: str = "",
    ticker: str = "",
) -> str:
    """Render a do_context template string against signal result data."""
    # Build variable dict from signal result fields
    variables = SafeFormatDict({
        "value": str(signal_result.value) if signal_result.value is not None else "",
        "score": str(signal_result.value) if signal_result.value is not None else "",  # alias
        "zone": signal_result.threshold_level,
        "threshold": signal_result.threshold_context,
        "threshold_level": signal_result.threshold_level,
        "evidence": signal_result.evidence,
        "source": signal_result.source,
        "confidence": signal_result.confidence,
        "company": company_name,
        "ticker": ticker,
    })
    # Add details.* variables
    for k, v in signal_result.details.items():
        variables[f"details.{k}"] = str(v) if v is not None else ""

    return template.format_map(variables)
```

### Pattern 2: Compound Key Lookup (Status Fallback Chain)
**What:** Try specific status keys before falling back to generic ones
**When to use:** Selecting which do_context template to use based on signal result
**Example:**
```python
def _select_template(
    do_context_templates: dict[str, str],
    status: str,
    threshold_level: str,
) -> str:
    """Select the most specific do_context template for this result.

    Fallback chain: TRIGGERED_RED -> TRIGGERED -> DEFAULT -> ""
    """
    if status == "TRIGGERED":
        # Try specific: TRIGGERED_RED, TRIGGERED_YELLOW
        specific_key = f"TRIGGERED_{threshold_level.upper()}"
        if specific_key in do_context_templates:
            return do_context_templates[specific_key]
        # Fall back to generic TRIGGERED
        if "TRIGGERED" in do_context_templates:
            return do_context_templates["TRIGGERED"]
    elif status == "CLEAR":
        if "CLEAR" in do_context_templates:
            return do_context_templates["CLEAR"]
    elif status == "INFO":
        if "INFO" in do_context_templates:
            return do_context_templates["INFO"]

    # Final fallback
    return do_context_templates.get("DEFAULT", "")
```

### Pattern 3: Post-Evaluation Hook in Signal Engine
**What:** Apply do_context rendering after signal evaluation, following `_apply_traceability()` pattern
**When to use:** In `execute_signals()` after each signal is evaluated
**Example:**
```python
# In signal_engine.py, after _apply_traceability():
result = _apply_do_context(result, sig, company_name, ticker)
```

### Pattern 4: CI Gate as pytest Test
**What:** A pytest test that scans source files for forbidden D&O evaluative patterns
**When to use:** Runs in CI on every commit
**Example:**
```python
# test_do_context_ci_gate.py
import re
from pathlib import Path

DO_CONTEXT_PATTERNS = [
    r'D&O\s+(risk|exposure|implication)',
    r'litigation\s+(risk|exposure|relevance)',
    r'SCA\s+(risk|relevance|probability)',
    r'underwriting\s+(concern|implication)',
    r'\bplaintiff\b',
    r'\bscienter\b',
    r'securities\s+fraud',
]

SCAN_DIRS = [Path("src/do_uw/stages/render/context_builders/")]
FAIL_FILES = {"_distress_do_context.py"}  # Phase 115 scope
WARN_FILES = {"sect3_audit.py", "sect4_market_events.py", ...}  # Phase 116

def test_no_hardcoded_do_context_in_builders():
    """CI gate: D&O evaluative language must come from brain YAML, not Python."""
    violations = scan_for_violations(SCAN_DIRS, DO_CONTEXT_PATTERNS)
    fail_violations = [v for v in violations if v.file in FAIL_FILES]
    warn_violations = [v for v in violations if v.file in WARN_FILES]

    for w in warn_violations:
        warnings.warn(f"Phase 116 target: {w}")

    assert not fail_violations, f"Hardcoded D&O commentary found: {fail_violations}"
```

### Anti-Patterns to Avoid
- **Evaluative logic in templates:** Never put D&O interpretation logic in Jinja2 `{% if %}` blocks. The `distress_indicators.html.j2` template currently has inline D&O commentary in the "D&O Relevance" column -- this needs migrating to do_context too (Phase 116+ scope)
- **Template rendering at render time:** All do_context must be evaluated in ANALYZE, never in RENDER. Context builders are dumb consumers
- **Modifying PresentationSpec without backward compatibility:** The `do_context` field must have `default_factory=dict` so existing 562 signals validate without changes
- **Using Jinja2 syntax in do_context templates:** Use Python `{variable}` format strings, not `{{ variable }}` Jinja2 syntax. The two template systems serve different purposes

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Safe string formatting with missing keys | Custom template parser | `str.format_map()` with `SafeFormatDict` | stdlib handles all format string edge cases; custom parser will miss escaping, nested braces, etc. |
| YAML validation | Custom YAML walker | Pydantic `PresentationSpec` model | Already enforces schema; adding `do_context` field to existing model is trivial |
| Source file scanning for CI | Custom file walker | `pathlib.Path.rglob()` + `re` module | Standard pattern for CI gates in this codebase |

## Common Pitfalls

### Pitfall 1: `str.format_map()` Crashes on `{details.key}` Dot Notation
**What goes wrong:** Python's `str.format_map()` treats `{details.key}` as attribute access on an object named `details`, not a dict key lookup for `"details.key"`
**Why it happens:** Python format string syntax interprets `.` as attribute access
**How to avoid:** Pre-flatten details into the variables dict with `details.key` as literal keys, OR pre-process the template to replace `{details.key}` with `{details_key}` before formatting. The simpler approach: use `details_key` notation in templates (underscores instead of dots), OR write a custom `format_map` that handles dots
**Warning signs:** `AttributeError: 'str' object has no attribute 'key'` at runtime
**Recommended solution:** Pre-process templates to replace `{details.X}` with flat keys, then populate the flat dict:
```python
# Flatten details into variable dict
for k, v in signal_result.details.items():
    variables[f"details_{k}"] = str(v) if v is not None else ""

# In YAML templates, use {details_components_profitability} not {details.components.profitability}
```
Alternative: use a regex pre-pass to replace `{details.X.Y}` with `{details_X_Y}` and flatten nested dicts accordingly.

### Pitfall 2: PresentationSpec `extra="forbid"` Blocks New Fields
**What goes wrong:** Adding `do_context` to YAML without updating `PresentationSpec` model causes validation errors on ALL 562 signals
**Why it happens:** `PresentationSpec` has `model_config = ConfigDict(extra="forbid")` (line 462)
**How to avoid:** Add the field to the Pydantic model FIRST, then add YAML content. The field must have `default_factory=dict` for backward compatibility
**Warning signs:** Pydantic `ValidationError` mentioning "extra fields not permitted"

### Pitfall 3: Signal IDs for Distress Models Are Not in forensic.yaml
**What goes wrong:** Assuming all 4 distress model signals are in `forensic.yaml`
**Why it happens:** The Altman Z-Score signal is `FIN.ACCT.quality_indicators` in `fin/accounting.yaml` (line 827), not in `forensic.yaml`. The Beneish composite is `FIN.FORENSIC.fis_composite` in `forensic.yaml`. Ohlson and Piotroski are consumed from `fin.distress.ohlson_o_score` and `fin.distress.piotroski_f_score` state objects -- they may NOT have corresponding brain signals yet
**How to avoid:** Check which signals actually exist for each distress model. The do_context may need to be added to existing signals OR new signals may need to be created
**Warning signs:** Looking for `FIN.FORENSIC.altman` and not finding it

### Pitfall 4: Distress Commentary Functions Read from State, Not Signal Results
**What goes wrong:** The 4 Python functions take `(score, zone)` parameters directly from `fin.distress.*` state objects, not from signal results. Migration assumes signal results carry the same score/zone data
**Why it happens:** The `_extract_distress_signals()` function in `financials_evaluative.py` reads `fin.distress.altman_z_score.score` and `fin.distress.altman_z_score.zone` directly from state, then passes to Python functions
**How to avoid:** Ensure the corresponding brain signals populate `value` (score) and `threshold_level` (zone mapping) on their SignalResult. Verify the data is available in signal results before migrating
**Warning signs:** do_context templates produce empty strings because `{value}` is None

### Pitfall 5: Jinja2 Template Inline D&O Commentary Also Needs Migration
**What goes wrong:** The `distress_indicators.html.j2` template has hardcoded D&O commentary in the "D&O Relevance" column (lines 20-51) that is separate from the Python functions
**Why it happens:** D&O commentary exists in TWO places: (1) Python functions for the "D&O Underwriting Interpretation" box, and (2) Jinja2 inline conditionals for the table column
**How to avoid:** Phase 115 migrates the Python functions. The Jinja2 inline D&O commentary in the table should also be migrated (or at minimum, the CI gate should WARN on it for Phase 116+)
**Warning signs:** CI gate catches violations in Jinja2 templates that weren't expected

### Pitfall 6: `format_map()` and Curly Braces in Template Text
**What goes wrong:** Template strings that contain literal `{` or `}` (e.g., "M-Score > -1.78 {above threshold}") crash `format_map()`
**Why it happens:** Python format strings require `{{` and `}}` for literal braces
**How to avoid:** Document in brain YAML authoring guide that literal braces must be escaped as `{{` and `}}`; add validation in `brain health` to catch unbalanced braces

## Code Examples

### Example 1: Adding do_context to PresentationSpec
```python
# In brain_signal_schema.py, PresentationSpec class:
class PresentationSpec(BaseModel):
    """V2 presentation section: rendering hints beyond DisplaySpec."""
    model_config = ConfigDict(extra="forbid")

    detail_levels: list[PresentationDetailLevel] = Field(
        default_factory=list,
        description="Content specifications per detail level",
    )
    context_templates: dict[str, str] = Field(
        default_factory=dict,
        description="Status-keyed template strings (e.g. TRIGGERED, CLEAR)",
    )
    do_context: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "D&O commentary templates keyed by signal outcome "
            "(TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR, TRIGGERED, DEFAULT). "
            "Evaluated in ANALYZE via do_context_engine.py."
        ),
    )
```

### Example 2: YAML do_context for Altman Z-Score
```yaml
# In the signal's presentation block:
  presentation:
    do_context:
      TRIGGERED_RED: >-
        Distress zone (below 1.81) — historically associated with
        2-3x higher D&O claim frequency. Companies in financial
        distress face elevated exposure to going-concern lawsuits,
        creditor derivative actions, and breach-of-fiduciary-duty claims.
      TRIGGERED_YELLOW: >-
        Grey zone (1.81-2.99) — moderate financial stress.
        Warrants monitoring for deterioration that could trigger
        securities class actions if stock price declines coincide
        with negative financial disclosures.
      CLEAR: >-
        Safe zone (above 2.99) — low bankruptcy probability.
        Strong financial position is a protective factor for D&O risk,
        reducing exposure to going-concern and insolvency-related claims.
```

### Example 3: Adding do_context to SignalResult
```python
# In signal_results.py, SignalResult class:
    do_context: str = Field(
        default="",
        description=(
            "Rendered D&O commentary string from brain YAML do_context template. "
            "Populated by do_context_engine after signal evaluation in ANALYZE. "
            "Consumed as-is by context builders — no evaluative logic downstream."
        ),
    )
```

### Example 4: Adding do_context to SignalResultView
```python
# In _signal_consumer.py, SignalResultView dataclass:
@dataclass(frozen=True)
class SignalResultView:
    """Read-only typed view of a signal result plus brain metadata."""
    signal_id: str
    status: str
    value: str | float | None
    threshold_level: str
    evidence: str
    source: str
    confidence: str
    threshold_context: str
    factors: tuple[str, ...]
    details: dict[str, Any]
    data_status: str
    content_type: str
    category: str
    rap_class: str
    rap_subcategory: str
    mechanism: str
    epistemology_rule_origin: str
    epistemology_threshold_basis: str
    do_context: str  # NEW: rendered D&O commentary from brain YAML
```

### Example 5: Consumer Pattern in financials_evaluative.py
```python
# BEFORE (hardcoded):
result["z_do_context"] = altman_do_context(z.score if z else None, z.zone if z else None)

# AFTER (signal-driven):
z_signal = safe_get_result(signal_results, "FIN.ACCT.quality_indicators")
result["z_do_context"] = z_signal.do_context if z_signal else ""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| D&O commentary in Python functions | D&O commentary in brain YAML templates | Phase 115 (this phase) | Commentary becomes portable, auditable, editable without code changes |
| Inline D&O interpretation in Jinja2 templates | do_context strings rendered as-is | Phase 115-116 | Templates become dumb consumers; all D&O intelligence in brain YAML |
| context_templates for short status strings | do_context for rich D&O paragraphs | Phase 115 | Separate concerns: context_templates = display, do_context = interpretation |

## Open Questions

1. **Ohlson and Piotroski Signal IDs**
   - What we know: The Python functions read from `fin.distress.ohlson_o_score` and `fin.distress.piotroski_f_score` state objects. `FIN.FORENSIC.dechow_f_score` exists in forensic.yaml but its epistemology references Piotroski (naming confusion).
   - What's unclear: Which brain signal IDs should carry the do_context for Ohlson and Piotroski? There may not be 1:1 signal-to-distress-model mapping.
   - Recommendation: Map the 4 Python functions to their closest brain signal IDs. If no matching signal exists, create one or add do_context to the closest existing signal. The data builders (`build_altman_trajectory`, `build_piotroski_components`) will still read from state -- only the commentary string changes.

2. **`details.*` Dot-Path Variable Syntax**
   - What we know: Python `str.format_map()` interprets dots as attribute access, not dict key lookup
   - What's unclear: Whether to use underscore notation (`{details_key}`) or implement a custom formatter
   - Recommendation: Use underscore notation (`{details_key}`) in YAML templates, flatten details dict with underscore-joined keys. Simpler, no custom formatter needed, and the 4 distress functions don't use details variables anyway (they only use score and zone).

3. **Distress Template Variables**
   - What we know: Altman uses score+zone, Beneish uses score+zone, Piotroski uses score (integer), Ohlson uses score+zone
   - What's unclear: Whether `{value}` in templates maps to score or zone. The Python functions receive both explicitly.
   - Recommendation: Map `{value}` to the numeric score, `{zone}` to the descriptive zone string (derived from threshold_level). For Piotroski, `{value}` is the integer score. This matches how `SignalResult.value` stores the evaluated data value.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/stages/analyze/test_do_context_engine.py tests/brain/test_do_context_ci_gate.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | PresentationSpec accepts do_context field | unit | `uv run pytest tests/brain/test_brain_schema.py -x -k do_context` | Needs update |
| INFRA-02 | do_context engine renders templates correctly | unit | `uv run pytest tests/stages/analyze/test_do_context_engine.py -x` | Wave 0 |
| INFRA-03 | Migrated YAML produces identical output to Python functions | integration | `uv run pytest tests/test_do_context_golden.py -x` | Wave 0 |
| INFRA-04 | Context builders consume do_context strings | unit | `uv run pytest tests/stages/render/test_financials_evaluative.py -x -k do_context` | Wave 0 |
| INFRA-05 | CI gate catches hardcoded D&O commentary | unit | `uv run pytest tests/brain/test_do_context_ci_gate.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/analyze/test_do_context_engine.py tests/brain/test_do_context_ci_gate.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/analyze/test_do_context_engine.py` -- engine unit tests (template rendering, fallback chain, missing variables)
- [ ] `tests/brain/test_do_context_ci_gate.py` -- CI enforcement test
- [ ] `tests/test_do_context_golden.py` -- golden snapshot comparison (4 distress functions x multiple zones)

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/brain_signal_schema.py` lines 459-472 -- PresentationSpec model (verified `extra="forbid"`, `context_templates` pattern)
- `src/do_uw/stages/analyze/signal_engine.py` lines 522-600 -- `_apply_traceability()` pattern (verified exact integration point)
- `src/do_uw/stages/analyze/signal_results.py` lines 122-199 -- `SignalResult` model (verified field layout and defaults)
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- `SignalResultView` dataclass and accessor functions (verified frozen dataclass pattern)
- `src/do_uw/stages/render/context_builders/_distress_do_context.py` -- 4 target Python functions + 2 data builders (verified exact function signatures and output)
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` -- Consumer of distress functions (verified import and call sites)
- `src/do_uw/templates/html/sections/financial/distress_indicators.html.j2` -- Template consuming do_context strings (verified both Python-sourced and Jinja2-inline D&O commentary)
- `src/do_uw/brain/signals/fin/forensic.yaml` -- Existing signal definitions (verified FIN.FORENSIC.fis_composite for Beneish)
- `src/do_uw/brain/signals/fin/accounting.yaml` lines 827-893 -- FIN.ACCT.quality_indicators (Altman Z-Score signal)

### Secondary (MEDIUM confidence)
- Python `str.format_map()` documentation -- verified format string behavior with missing keys requires custom dict

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new dependencies
- Architecture: HIGH -- follows established patterns exactly (`_apply_traceability`, `PresentationSpec`, `SignalResultView`)
- Pitfalls: HIGH -- identified from direct code inspection (PresentationSpec `extra="forbid"`, dot-notation in format strings, signal ID mapping)
- Migration: MEDIUM -- signal ID mapping for Ohlson/Piotroski needs verification during implementation

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable internal architecture, no external dependencies)
