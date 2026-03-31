# Architecture Patterns: Typed Output Contracts & Quality Gates

**Domain:** Typed context-builder contracts, canonical metrics, contextual signal validation, and cross-section consistency for existing Pydantic/Jinja2 pipeline
**Researched:** 2026-03-27
**Confidence:** HIGH (based on direct codebase analysis of ~420 Python source files, 90+ context builders, 239 Jinja2 templates)

## Recommended Architecture

Six new architectural components inserted into the existing pipeline. No new pipeline stages. No changes to stages 1-4 (RESOLVE through ANALYZE, except one post-processing hook). All changes are additive with fallback paths.

### Current Flow (What Exists)

```
AnalysisState
  -> ~90 context builder functions (return dict[str, Any])
    -> assembly_registry.build_html_context() merges all into one giant dict
      -> 239 Jinja2 templates consume dict keys, untyped
        -> HTML string
          -> health_check.py / semantic_qa.py / self_review.py (post-hoc diagnostics)
```

**Root problems this architecture solves:**

1. **Untyped boundary:** Context builders return `dict[str, Any]`. Raw Python objects (SourcedValue, Pydantic models, lists-of-dicts) leak into templates. Type mismatches discovered only at render time (or by the user).
2. **Metric duplication:** Revenue is computed in `key_stats_context.py` (`_extract_revenue`), `financials.py` (from statement rows), `company_profile.py` (from `company.financials`), and `beta_report` sections. Each may yield different values from different sources.
3. **False positive signals:** Signals fire on data presence/thresholds without checking company context. IPO signals fire for 30-year-old companies. Insolvency signals fire for mega-caps. `should_suppress_insolvency()` exists but is ad-hoc, not systematic.
4. **Cross-section inconsistency:** Same fact (revenue, CEO, exchange, case count) can appear differently across sections because each builder extracts independently.
5. **Output pollution:** Markdown formatting, debug strings (`[object Object]`, `SourcedValue(...)`), and system jargon leak into final HTML.

### Proposed Flow (What Changes)

```
AnalysisState
  |
  v
[NEW] CanonicalMetricsRegistry     <-- compute-once, single source per metric
  |
  v
~90 context builders               <-- gradually gain typed Pydantic return models
  |                                     (with untyped fallback during migration)
  v
[NEW] TypedContextAssembler         <-- validates typed models, produces template dict
  |
  v
[NEW] CrossSectionConsistencyChecker <-- verify same fact identical everywhere
  |
  v
Jinja2 templates (UNCHANGED)       <-- consume same dict keys, zero template changes
  |
  v
[NEW] OutputSanitizer               <-- strip markdown, debug strings, jargon
  |
  v
HTML output
  |
  v
health_check + semantic_qa + self_review (existing, UNCHANGED)


SEPARATELY (post-ANALYZE, pre-SCORE):

SignalResult[] from execute_signals()
  |
  v
[NEW] ContextualSignalValidator     <-- suppress false positives using state context
  |
  v
state.analysis.signal_results (cleaned)
  |
  v
SCORE stage (receives fewer false positives)
```

### Component Boundaries

| Component | Responsibility | Location | Insertion Point |
|-----------|---------------|----------|-----------------|
| CanonicalMetricsRegistry | Single computed value per metric with provenance | `stages/render/canonical_metrics.py` (NEW) | Called once at top of `build_html_context()` |
| Typed Context Models | Pydantic BaseModel per section replacing `dict[str, Any]` returns | `stages/render/context_models/` (NEW package) | Wrap existing builder functions |
| TypedContextAssembler | Validate typed models, serialize to template dict | Modification of `assembly_registry.py` | Replaces raw dict merge |
| ContextualSignalValidator | Cross-check signals against company state, suppress false positives | `stages/analyze/contextual_validator.py` (NEW) | After `execute_signals()`, before SCORE |
| CrossSectionConsistencyChecker | Verify same fact appears identically in all sections | `stages/render/consistency_checker.py` (NEW) | After context assembly, before Jinja2 |
| SectionCompletenessGate | Suppress >50% N/A sections with placeholder | `stages/render/section_gate.py` (NEW) | After typed model validation |
| OutputSanitizer | Strip markdown, debug strings, raw serialization from HTML | `stages/render/output_sanitizer.py` (NEW) | After Jinja2 render, before disk write |

### Data Flow

```
                        AnalysisState
                             |
                   +---------+---------+
                   |                   |
         CanonicalMetricsRegistry   ContextualSignalValidator
         (compute-once metrics)     (post-ANALYZE, pre-SCORE)
                   |                   |
                   v                   v
          Context Builders -----> Typed Section Models
          (read canonical +        (Pydantic validated)
           read state directly)
                   |
                   v
          TypedContextAssembler
          (model.model_dump() -> dict)
                   |
                   v
          CrossSectionConsistencyChecker
          (verify revenue/CEO/exchange match across sections)
                   |
                   v
          SectionCompletenessGate
          (suppress or badge sections with >50% N/A)
                   |
                   v
          Jinja2 Render (unchanged — same dict keys)
                   |
                   v
          OutputSanitizer
          (clean HTML string, fix leaked artifacts)
                   |
                   v
          Final HTML -> disk
```

## Component Designs

### Component 1: CanonicalMetricsRegistry

**What:** A computed-once registry of authoritative metric values. Each metric has exactly one computation path with explicit source priority (XBRL > LLM extraction > yfinance > web). Every context builder reads from this registry for cross-section facts instead of recomputing.

**Location:** `src/do_uw/stages/render/canonical_metrics.py`

**Why it matters:** Revenue currently appears in `key_stats_context.py` (`_extract_revenue`), `financials.py` (from XBRL statement rows), `company_profile.py` (from `company.financials`), `beta_report` sections, and `page0_context.py`. Each extracts independently and can produce different values. The canonical registry eliminates this by computing every cross-section fact exactly once.

```python
from pydantic import BaseModel, Field
from do_uw.models.state import AnalysisState

class MetricValue(BaseModel):
    """Single authoritative metric value with provenance."""
    value: float | str | int | None
    formatted: str          # Pre-formatted display string: "$45.2B", "142,000"
    source: str             # "xbrl:10-K:FY2025" | "yfinance:info" | "llm:10-K"
    confidence: str         # HIGH | MEDIUM | LOW
    as_of: str              # "FY2025" | "2026-03-27" | "TTM"

class CanonicalMetrics(BaseModel):
    """All canonical metrics, computed once from state at render start."""

    # Identity (must match everywhere)
    company_name: MetricValue
    ticker: MetricValue
    exchange: MetricValue
    sic_code: MetricValue
    sic_description: MetricValue
    ceo_name: MetricValue

    # Financial (XBRL-first source priority)
    revenue: MetricValue
    revenue_growth_yoy: MetricValue
    net_income: MetricValue
    operating_margin: MetricValue
    total_assets: MetricValue
    total_liabilities: MetricValue
    total_debt: MetricValue
    cash_and_equivalents: MetricValue
    market_cap: MetricValue
    shares_outstanding: MetricValue
    employees: MetricValue

    # Market
    stock_price: MetricValue
    high_52w: MetricValue
    low_52w: MetricValue
    short_interest_pct: MetricValue
    beta: MetricValue

    # Litigation counts
    active_sca_count: MetricValue
    sec_enforcement_count: MetricValue
    derivative_count: MetricValue
    total_active_cases: MetricValue

    # Scoring
    overall_score: MetricValue
    tier: MetricValue
    filing_probability: MetricValue

def build_canonical_metrics(state: AnalysisState) -> CanonicalMetrics:
    """Compute all canonical metrics from state.

    Source priority per metric type:
    - Financial: XBRL statements > LLM 10-K extraction > yfinance
    - Market: extracted.market.stock > acquired_data.market_data["info"]
    - Identity: state.company.identity (canonical)
    - Litigation: state.extracted.litigation (canonical)
    - Scoring: state.scoring (canonical)
    """
    ...
```

**Integration pattern:** Called once at the top of `build_html_context()`. Stored as `context["_canonical"]`. Context builders receive it as a parameter and read from it for any metric that appears in multiple sections. They NEVER recompute these values.

**Relationship to `state_paths.py`:** Complementary, not competing. `state_paths.py` provides typed read access to raw state data (insider transactions, market history, etc.). The canonical registry provides formatted, reconciled display values. `state_paths.py` reads raw data for analysis; canonical registry provides display values for templates.

**Migration path:** Add `canonical: CanonicalMetrics | None = None` parameter to existing `BuilderFn` type. Builders that receive it use it; builders that don't continue extracting independently (to be migrated later). No breaking change.

### Component 2: Typed Context Models

**What:** Pydantic BaseModel for each section's template context. Fields use concrete types (`str`, `float`, `list[DirectorRow]`), not `Any`. Pre-formatted display strings are `str`.

**Location:** `src/do_uw/stages/render/context_models/` (new package, one file per section)

**Design principles:**
- Models describe what the TEMPLATE needs, not what the STATE contains. Context models transform, not mirror.
- Optional fields use `None` default, not missing keys.
- Pre-formatted strings (`"$45.2B"`, `"83%"`) are `str`, not raw `float`.
- `ConfigDict(extra="forbid")` catches unexpected keys leaking through.
- `Field(alias="template_key_name")` maps model field names to existing template variable names, enabling zero template changes.

```python
# context_models/key_stats.py
from pydantic import BaseModel, ConfigDict, Field

class ScaleMetric(BaseModel):
    """Single scale metric for the identity spectrum display."""
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str          # Pre-formatted: "$45.2B", "142,000", "47"
    tier: str           # "Large", "Mid", "Small", "--"
    pct: float          # 0-100 spectrum position
    inverted: bool = False

class GovernanceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    board_size: int | None = None
    independence_pct: str = "N/A"
    avg_tenure: str = "N/A"
    gender_diversity: str = "N/A"
    ceo_pay_ratio: str = "N/A"

class KeyStatsContext(BaseModel):
    """Typed context for Key Stats Overview section.

    Every field the key_stats template accesses is declared here.
    model_dump() produces the exact dict the template expects.
    """
    model_config = ConfigDict(extra="forbid")

    available: bool = True
    company_name: str = "N/A"
    ticker: str = ""
    exchange: str = "N/A"
    sic_code: str = "N/A"
    sic_description: str = "N/A"
    # ... every field the template reads
    scale_metrics: list[ScaleMetric] = Field(default_factory=list)
    governance: GovernanceSummary | None = None
    chart_1y: str = ""
    chart_5y: str = ""
    # etc.
```

**Migration strategy (CRITICAL -- incremental, not big-bang):**

1. **Start with 5 highest-leakage sections** based on known CUO audit failures: `key_stats`, `scoring`, `financials`, `company_profile`, `governance`. These are the sections where untyped leakage has caused real bugs.

2. **Each model has a `to_template_dict()` that produces the exact dict templates expect.** Zero template changes needed. This is achieved via `model_dump(by_alias=True)` with `Field(alias=...)` where model field names differ from template variable names.

3. **Validation wrapper pattern (non-breaking):**

```python
def build_key_stats_typed(state: AnalysisState) -> KeyStatsContext:
    """Typed wrapper around existing builder."""
    raw = build_key_stats_context(state)  # existing function, unchanged
    return KeyStatsContext.model_validate(raw)

# In assembler:
try:
    typed = build_key_stats_typed(state)
    context["key_stats"] = typed.model_dump()
except ValidationError as e:
    logger.warning("KeyStatsContext validation failed (%d errors), using untyped fallback", e.error_count())
    context["key_stats"] = build_key_stats_context(state)  # fallback
```

4. **CI ratchet gate:** `test_context_model_coverage.py` tracks which builders have typed models. Coverage must increase monotonically (cannot remove typed models once added).

**Pydantic v2 patterns:**
- `model_validate()` for dict-to-model (not `__init__(**dict)` which skips validation)
- `model_dump()` for model-to-dict (not deprecated `.dict()`)
- `ConfigDict(extra="forbid")` to catch unexpected keys
- `Field(default=...)` with concrete defaults, never `Optional[Any]`
- `Field(alias="template_var_name")` for backward compat with existing template variables
- No discriminated unions needed (context models are flat per-section, not polymorphic)

### Component 3: ContextualSignalValidator

**What:** Post-ANALYZE pass that cross-checks signal results against company context. Suppresses false positives, downgrades inappropriate severity, annotates confidence.

**Location:** `src/do_uw/stages/analyze/contextual_validator.py`

**Insertion point:** Called AFTER `execute_signals()` returns `list[SignalResult]`, BEFORE results are stored on state and passed to SCORE. This means false positive suppression reduces the score correctly (suppressed signals don't contribute to factor scores).

**Why necessary:** Currently signals fire on data presence and threshold comparison only. Known false positive categories:
- IPO signals (`IPO.*`, `OFFERING.*`, `S1_*`) fire for companies public 30+ years
- Insolvency/distress signals fire for mega-caps with strong financials (partially handled by `should_suppress_insolvency()` but it's ad-hoc, not systematic)
- CEO-related signals fire without validating against actual CEO name/tenure
- "Revenue decline" fires when one quarterly comparison is negative despite strong YoY trend
- Temporal signals fire on events >5 years old

**Design:** YAML-driven rules, following the brain signal pattern. Rules are data, not code.

```yaml
# config/contextual_validation_rules.yaml
rules:
  - id: "CV-01"
    signal_pattern: "IPO.*|OFFERING.*|S1_.*"
    condition: "years_public > 10"
    action: suppress
    reason: "IPO/offering signals not applicable for companies public >10 years"

  - id: "CV-02"
    signal_pattern: "INSOLVENCY.*|GOING_CONCERN.*|BANKRUPTCY.*"
    condition: "market_cap > 50e9 and current_ratio > 1.5 and altman_z > 2.99"
    action: suppress
    reason: "Distress signals suppressed for large-cap with healthy financials"

  - id: "CV-03"
    signal_pattern: "REV_DECLINE.*"
    condition: "revenue_growth_yoy > 0.05"
    action: downgrade
    downgrade_to: "INFO"
    reason: "Revenue decline signal downgraded when overall YoY growth is positive"

  - id: "CV-04"
    signal_pattern: "RESTATEMENT.*"
    condition: "restatement_age_years > 5"
    action: annotate
    annotation: "Historical restatement (>5 years ago) -- reduced current relevance"

  - id: "CV-05"
    signal_pattern: "CEO_DEPARTURE.*|CEO_CHANGE.*"
    condition: "ceo_tenure_years > 3"
    action: suppress
    reason: "CEO departure signal suppressed when current CEO has >3 year tenure"
```

```python
class ValidationRule(BaseModel):
    id: str
    signal_pattern: str    # regex matched against signal_id
    condition: str         # safe expression evaluated against company context
    action: str            # "suppress" | "downgrade" | "annotate"
    reason: str
    downgrade_to: str | None = None
    annotation: str | None = None

class CompanyContext(BaseModel):
    """Flat context extracted from state for rule condition evaluation."""
    years_public: float | None = None
    market_cap: float | None = None
    current_ratio: float | None = None
    altman_z: float | None = None
    revenue_growth_yoy: float | None = None
    ceo_tenure_years: float | None = None
    restatement_age_years: float | None = None
    # ... every attribute referenced by any rule condition

class ContextualValidator:
    def __init__(self, rules: list[ValidationRule]):
        self.rules = rules

    def validate(
        self,
        results: list[SignalResult],
        context: CompanyContext,
    ) -> tuple[list[SignalResult], list[dict[str, str]]]:
        """Apply rules. Returns (modified_results, suppression_log)."""
        ...
```

**Condition evaluation:** NOT Python `eval()`. Use a safe expression parser that only allows comparisons (`>`, `<`, `==`, `>=`, `<=`, `!=`), boolean operators (`and`, `or`, `not`), numeric literals, and attribute lookups on `CompanyContext`. No function calls, no imports, no side effects.

**Relationship to existing `should_suppress_insolvency()`:** The contextual validator subsumes it. `should_suppress_insolvency()` becomes one rule in the YAML. The existing function can remain as a backward-compat wrapper that delegates to the validator.

### Component 4: CrossSectionConsistencyChecker

**What:** Validates that the same fact (revenue, CEO, exchange, case counts, stock price) appears identically in every section where it's rendered.

**Location:** `src/do_uw/stages/render/consistency_checker.py`

**Insertion point:** After all context builders have run and the assembled context dict is complete, before Jinja2 rendering.

```python
class ConsistencyFact(BaseModel):
    """A fact that must be consistent across sections."""
    name: str               # "revenue", "ceo_name", "exchange"
    paths: list[str]        # dot-paths into context dict: ["key_stats.revenue", "financials.revenue_display"]
    comparator: str = "exact"  # "exact" | "numeric_1pct" | "case_insensitive"

class InconsistencyReport(BaseModel):
    fact: str
    values_found: dict[str, str]  # path -> rendered value
    severity: str               # "ERROR" | "WARNING"

# Config-driven:
# config/consistency_facts.yaml
facts:
  - name: revenue
    paths:
      - "key_stats.revenue_display"
      - "financials.revenue_latest"
      - "page0.mini_cards[0].value"  # Revenue card
    comparator: numeric_1pct

  - name: ceo_name
    paths:
      - "key_stats.ceo_name"
      - "governance.ceo_name"
      - "executive_brief.ceo"
    comparator: case_insensitive

  - name: exchange
    paths:
      - "key_stats.exchange"
      - "company.exchange"
    comparator: exact
```

**Pre-render vs post-render:** Both layers.
- **Pre-render:** Compares context dict values. Catches builder-level inconsistencies.
- **Post-render:** Parses HTML and compares displayed values. Catches template-level hardcoding.

**Relationship to CanonicalMetricsRegistry:** If all builders read from the canonical registry, consistency is guaranteed by construction. The checker is defense-in-depth for builders that haven't been migrated yet or templates that bypass context variables.

**Deployment mode:** Report-only initially. Will find existing inconsistencies. Fix by routing through canonical registry. Promote to blocking only after inconsistency count reaches zero.

### Component 5: SectionCompletenessGate

**What:** Suppress sections that are >50% N/A. Replace with a clean "Insufficient data for this section" card instead of rendering broken tables full of dashes.

**Location:** `src/do_uw/stages/render/section_gate.py`

```python
class SectionReadiness(BaseModel):
    section_key: str
    completeness_pct: float    # 0.0-1.0
    missing_fields: list[str]
    render_mode: str           # "full" | "limited" | "suppressed"

def assess_section_readiness(
    section_key: str,
    context: BaseModel,       # typed context model
    threshold: float = 0.5,
) -> SectionReadiness:
    """Count populated vs None/N/A fields in typed model."""
    total = len(context.model_fields)
    populated = 0
    missing = []
    for field_name in context.model_fields:
        val = getattr(context, field_name)
        if val is not None and str(val) not in {"N/A", "--", "", "0", "0.0"}:
            populated += 1
        else:
            missing.append(field_name)
    pct = populated / total if total > 0 else 0
    mode = "full" if pct >= threshold else ("limited" if pct >= 0.25 else "suppressed")
    return SectionReadiness(
        section_key=section_key,
        completeness_pct=pct,
        missing_fields=missing,
        render_mode=mode,
    )
```

**Template integration:** Context dict gains `section_readiness: dict[str, SectionReadiness]`. Templates check `{% if section_readiness.financials.render_mode != 'suppressed' %}`. "Limited" mode renders available data with a "Partial data available" badge.

**Why typed models are a prerequisite:** Can't count N/A fields on `dict[str, Any]` — you don't know which keys are expected. Typed models enumerate all expected fields via `model_fields`.

### Component 6: OutputSanitizer

**What:** Single-pass cleanup of rendered HTML. Fixes what leaked through despite all upstream protections.

**Location:** `src/do_uw/stages/render/output_sanitizer.py`

**Insertion point:** After Jinja2 rendering produces the HTML string, before writing to disk. Applied once to complete HTML.

```python
import re

# Patterns shared with health_check.yaml
_SANITIZE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Markdown formatting leaked from LLM text
    (re.compile(r'\*\*([^*]+)\*\*'), r'\1'),              # **bold** -> bold
    (re.compile(r'(?<!\w)##\s+([^\n]+)'), r'\1'),         # ## heading -> heading
    (re.compile(r'```[\s\S]*?```'), ''),                   # code blocks
    # Debug strings
    (re.compile(r'\[object Object\]'), ''),
    (re.compile(r"<class '[^']+'>"), ''),
    (re.compile(r'SourcedValue\([^)]*\)'), ''),
    (re.compile(r'Decimal\([^)]*\)'), ''),
    # System jargon (factor codes in prose context)
    (re.compile(r'\bF\.\d+ = \d+/\d+\b'), ''),           # "F.7 = 5/8" in prose
    (re.compile(r'\b\d+-of-\d+\b'), ''),                  # "5-of-90"
    # Double-encoded HTML
    (re.compile(r'&amp;amp;'), '&amp;'),
    (re.compile(r'&amp;lt;'), '&lt;'),
    (re.compile(r'&amp;gt;'), '&gt;'),
]

def sanitize_output(html: str) -> str:
    """Clean rendered HTML output.

    Applied after Jinja2 rendering, before disk write.
    Shares pattern config with health_check.yaml.
    """
    result = html
    for pattern, replacement in _SANITIZE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
```

**Relationship to health_check.py:** Health check diagnoses and reports (read-only). Sanitizer fixes (modifies output). They share pattern definitions from `config/health_check.yaml`. Health check runs AFTER sanitizer to catch anything the sanitizer missed.

## Integration: New vs Modified Components

### New Components (7 files/packages)

| File | Est. Lines | Dependencies |
|------|-----------|--------------|
| `stages/render/canonical_metrics.py` | ~300 | `models/state.py`, `formatters.py`, `state_paths.py` |
| `stages/render/context_models/` (package, ~10 files) | ~150 each | `pydantic` |
| `stages/analyze/contextual_validator.py` | ~250 | `signal_results.py`, `models/state.py`, YAML config |
| `stages/render/consistency_checker.py` | ~200 | `canonical_metrics.py`, YAML config |
| `stages/render/section_gate.py` | ~100 | `context_models/` |
| `stages/render/output_sanitizer.py` | ~150 | `config/health_check.yaml` |
| `config/contextual_validation_rules.yaml` | ~100 | None |
| `config/consistency_facts.yaml` | ~50 | None |

### Modified Components (4 files, minimal changes)

| File | Change | Risk |
|------|--------|------|
| `stages/render/context_builders/assembly_registry.py` | Add canonical metrics computation at top; wrap builders with typed validation; add consistency check and sanitizer calls | LOW -- additive, try/except fallback on every change |
| `stages/analyze/signal_engine.py` (or its caller) | Call `ContextualValidator.validate()` after `execute_signals()` | LOW -- post-processing, input/output types unchanged |
| `stages/render/html_renderer.py` | Call `sanitize_output()` on final HTML string | LOW -- string transform, reversible |
| Individual context builders (one at a time) | Add typed wrapper alongside existing function | LOW -- one builder per PR, with untyped fallback |

### Unchanged Components

- **All 239 Jinja2 templates** -- zero template changes. Typed models produce the same dict keys via `model_dump()`.
- **All models in `models/`** -- state model unchanged.
- **All stages RESOLVE through BENCHMARK** -- unchanged except the signal validator hook in ANALYZE.
- **`state_paths.py`** -- unchanged, complementary to canonical metrics.
- **`formatters.py`** -- unchanged, used by canonical metrics.
- **`health_check.py`, `semantic_qa.py`, `self_review.py`** -- unchanged, defense-in-depth.

## Patterns to Follow

### Pattern 1: Gradual Typing via Validation Wrapper

**What:** Wrap existing untyped builders with Pydantic validation. Fall through to untyped dict on validation failure.
**When:** Every context builder migration.

```python
from pydantic import ValidationError

def build_section_typed(state: AnalysisState) -> SectionContext:
    raw = build_section_untyped(state)   # existing function, unchanged
    return SectionContext.model_validate(raw)

# In assembler:
try:
    context["section"] = build_section_typed(state).model_dump()
except ValidationError as e:
    logger.warning("Typed validation failed for section (%d errors)", e.error_count())
    context["section"] = build_section_untyped(state)  # graceful fallback
```

**Why:** Non-breaking migration. Every builder migrated independently. Typed coverage grows monotonically. Production never breaks even if a model is wrong.

### Pattern 2: Canonical Registry as Constructor Parameter

**What:** Pass the canonical metrics registry to context builders so they read reconciled values.
**When:** Any builder that uses a metric appearing in 2+ sections.

```python
def build_financial_context(
    state: AnalysisState,
    canonical: CanonicalMetrics,
) -> FinancialContext:
    revenue_display = canonical.revenue.formatted   # "$3.05B (FY2025)"
    revenue_source = canonical.revenue.source       # "xbrl:10-K:FY2025"
    # NOT: _extract_revenue(state.extracted)  <-- old pattern, may disagree
```

**Why:** Makes cross-section disagreement on revenue, CEO name, exchange, etc. structurally impossible.

### Pattern 3: YAML-Driven Validation Rules

**What:** Contextual signal validation rules in YAML, following the brain signal pattern.
**When:** Signal validation rules that evolve as the brain grows.

**Why YAML not Python:** Follows brain portability principle. Rules are inspectable, version-controlled, and editable without code changes. Same pattern as brain signals: data drives behavior.

### Pattern 4: Report-Then-Block Deployment

**What:** New quality gates start in report-only mode. Log findings. Fix root causes. Promote to blocking only when finding count reaches zero.
**When:** Consistency checker, section completeness gate.

**Why:** Initial deployment will find dozens of existing inconsistencies (they exist today, just undiscovered). Blocking immediately would mean no output. Fix the root causes first.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Big-Bang Type Migration

**What:** Typing all 90 context builders and 239 templates at once.
**Why bad:** Creates massive merge conflicts. Any model error breaks the entire render pipeline. Cannot be tested incrementally. Estimated effort: weeks.
**Instead:** One builder at a time. Validation wrapper with fallback. CI ratchet gate. No template changes ever.

### Anti-Pattern 2: Context Models That Mirror State Models

**What:** Creating context model fields that are 1:1 copies of AnalysisState fields.
**Why bad:** Creates a second source of truth. State model changes require context model changes. Doubles maintenance.
**Instead:** Context models describe what the TEMPLATE needs (pre-formatted strings, CSS class names, boolean flags for conditional rendering). They TRANSFORM state data into display data. Example: state has `revenue: float = 3050000000.0`; context model has `revenue_display: str = "$3.05B (FY2025)"`.

### Anti-Pattern 3: Changing Template Variable Names

**What:** Renaming template variables to match new typed model field names.
**Why bad:** 239 templates. No type checker for Jinja2. Template changes are the highest-risk changes in the codebase.
**Instead:** Use `Field(alias="existing_template_key")` and `model_dump(by_alias=True)` to produce the exact dict keys templates already expect. Zero template changes.

### Anti-Pattern 4: Eager Consistency Enforcement (Blocking on Day 1)

**What:** Making the consistency checker block rendering on first inconsistency found.
**Why bad:** There are almost certainly existing inconsistencies (multiple builders compute revenue independently today). Blocking means no output until all are fixed.
**Instead:** Report-only mode. Fix root causes by migrating builders to canonical registry. Block only after reaching zero inconsistencies.

### Anti-Pattern 5: Signal Validation Logic in Python Code

**What:** Writing contextual validation as Python if/elif chains scattered across `signal_engine.py`.
**Why bad:** Violates brain portability. Rules become invisible. Testing requires Python. Changes require code deployment.
**Instead:** YAML rules in `config/contextual_validation_rules.yaml`, loaded by a generic interpreter.

### Anti-Pattern 6: OutputSanitizer That Modifies Data

**What:** Sanitizer that changes financial numbers, dates, or names (not just formatting artifacts).
**Why bad:** Could silently corrupt data. Underwriters need exact numbers.
**Instead:** Sanitizer only removes/fixes presentation artifacts (markdown, HTML entities, debug strings). Never touches content inside `<td>`, numeric values, or names. Pattern matching must be precise enough to avoid false positives on data.

## Build Order (Dependency-Aware)

```
Phase 1: CanonicalMetricsRegistry
  [no dependencies -- enables everything else]
  1. Define CanonicalMetrics Pydantic model with all cross-section facts
  2. Implement build_canonical_metrics(state) with XBRL-first source priority
  3. Wire into assembly_registry.build_html_context() -- compute once, store in context
  4. CI: test_canonical_metrics.py validates against real state.json files
  5. No consumer changes yet -- registry exists but nothing reads from it

Phase 2: Typed Context Models (5 priority sections)
  [depends on Phase 1 for canonical access]
  1. Define models for key_stats, scoring, financials, company_profile, governance
  2. Create validation wrappers with untyped fallback for each
  3. Wire wrappers into assembler with try/except pattern
  4. CI ratchet: test_context_model_coverage.py (coverage only goes up)
  5. Migrate each builder to read cross-section facts from canonical registry

Phase 3: ContextualSignalValidator
  [INDEPENDENT of Phases 1-2 -- can run in parallel]
  1. Define ValidationRule schema and YAML config format
  2. Implement safe expression parser for conditions (no eval())
  3. Implement rule engine and wire into ANALYZE stage after execute_signals()
  4. Seed with ~15 rules from known false positives (IPO, insolvency, CEO, temporal)
  5. CI: validate rules against real state.json to confirm no over-suppression

Phase 4: Quality Gates
  [depends on Phases 1-2 for consistency checking to work against canonical]
  1. Implement CrossSectionConsistencyChecker (report-only mode)
  2. Implement SectionCompletenessGate (requires typed models from Phase 2)
  3. Implement OutputSanitizer (independent, but logically groups with gates)
  4. Wire all three into render pipeline
  5. CI: run against all cached state.json files, baseline inconsistency count

Phase 5: CI Integration & Blocking Mode
  [depends on all above being stable]
  1. Template variable type validation CI gate (parse .j2 files vs context models)
  2. Promote consistency checker from report-only to blocking
  3. Replace 1,168 unspec'd MagicMock fixtures with real state.json tests
  4. Cross-ticker consistency validation in scripts/qa_compare.py
```

**Why this order:**
- Phase 1 first because the canonical registry is the foundation everything else references. Without it, consistency checking and typed models can't guarantee cross-section agreement.
- Phase 2 depends on Phase 1 because typed models should read from canonical rather than recomputing.
- Phase 3 is independent -- signal validation is a separate pipeline insertion point that doesn't interact with the render path. Can run in parallel with Phase 2.
- Phase 4 depends on Phases 1-2 because consistency checking is most effective when comparing canonical values, and section completeness gate requires typed models.
- Phase 5 is the "tighten the screws" phase -- only blocks after root causes are fixed.

## Scalability Considerations

| Concern | At 5 tickers | At 50 tickers | At 500 tickers |
|---------|-------------|---------------|----------------|
| Context model validation overhead | <100ms per render | Same (per-render, no aggregation) | Same |
| Canonical metrics computation | ~50ms | ~50ms (per-render) | Same |
| Contextual signal validation | ~100ms for 600 signals | Same (per-run) | Same |
| Consistency check (pre-render) | ~50ms (dict traversal) | Same | Same |
| Consistency check (post-render) | ~200ms (HTML parse) | Same | Same |
| Output sanitizer | ~100ms (regex over ~150K HTML) | Same | Same |
| Real-state test fixtures | 5 state.json files (~5MB each) | 50 files, CI ~5 min | Need fixture sampling |
| Context model count | 5 models (priority sections) | 15+ models (all sections) | Same |

**No scaling bottlenecks.** All new components are per-render (not cross-ticker) and operate on in-memory data structures. The only growth dimension is the number of typed context models, which grows linearly with sections (capped at ~15-20).

## Sources

- Existing codebase: direct analysis of `src/do_uw/` (~420 Python files, 90+ context builders, 239 Jinja2 templates) -- HIGH confidence
- Pydantic v2 patterns: `model_validate()`, `model_dump()`, `ConfigDict(extra="forbid")`, `Field(alias=...)` -- HIGH confidence (Pydantic v2 official semantics)
- Existing `state_paths.py` typed accessor pattern -- HIGH confidence (21 tests passing)
- Existing `should_suppress_insolvency()` contextual suppression pattern -- HIGH confidence (production code)
- Existing `health_check.py` / `semantic_qa.py` post-render validation -- HIGH confidence (production code)
- Brain YAML-driven rules pattern from `brain/signals/*.yaml` -- HIGH confidence (600+ signals in production)
