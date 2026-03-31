# Pitfalls Research: Adding Typed Contracts & Quality Gates to Existing Untyped Pipeline

**Domain:** Typed output contracts, canonical metrics, contextual validation, and output sanitization for an existing Python/Jinja2 data pipeline
**Researched:** 2026-03-27
**Confidence:** HIGH (based on direct codebase analysis of 97 context builders, 260 templates, 208 dict-returning functions, 115 MagicMock test files, plus established patterns from Pydantic migration literature)

---

## Critical Pitfalls

Mistakes that cause rewrites, regressions, or multi-day debugging sessions.

### Pitfall 1: Pydantic Rigidity Kills Graceful Degradation

**What goes wrong:**
The existing system handles missing data gracefully through `safe_float()` (383 call sites), `format_na` filters, and `v if v else 'X'` patterns in 260 Jinja2 templates. Pydantic models with required fields reject data that the old system would have rendered as "N/A" or "--". A strict Pydantic model for the financials section that requires `revenue: float` will crash when XBRL returns no data for a newly-public company. The pipeline goes from "renders with gaps" to "crashes completely."

**Why it happens:**
Developers designing typed contracts think about the ideal case, not the 50 ways data can be missing. The current codebase has accumulated defensive patterns precisely because real-world SEC data is incomplete, inconsistent, and sometimes garbage. A strict schema discards this institutional knowledge.

**How to avoid:**
1. Every field in output contracts MUST be `Optional[T] | None` with a default of `None` -- no required fields for data that comes from external sources.
2. Use Pydantic's `model_validator(mode='before')` to coerce messy inputs (strings like "N/A", "$3.2B", "13.2%") into typed values or None, replicating what `safe_float()` does today.
3. Define a `DisplayValue` type that wraps `value: T | None` + `formatted: str` + `source: str | None` so templates always have a renderable string even when the typed value is None.
4. Write a "strictness ladder" test: for each output model, verify it accepts the actual state.json from at least 3 real tickers (AAPL, RPM, HNGE) including one with known data gaps.

**Warning signs:**
- Pydantic `ValidationError` count spikes during first integration runs
- Templates that previously rendered "N/A" now show blank or crash
- Developers adding `try/except ValidationError` wrappers around model construction

**Phase to address:**
First phase (Typed Output Contract). The Optional-by-default rule must be established in the schema design, not retrofitted later.

---

### Pitfall 2: Big-Bang Migration of 97 Context Builders

**What goes wrong:**
Attempting to migrate all 97 context builder files (28,298 lines) and 208 dict-returning functions to typed contracts simultaneously. The migration stalls at 30% completion because each builder has unique assumptions about state structure, and testing requires real pipeline output. Meanwhile, half the codebase returns dicts and half returns Pydantic models, creating a worse situation than the original.

**Why it happens:**
The typed contract feels like a prerequisite for all other quality improvements. There is pressure to "do it right" by converting everything at once. But 97 files with 208 dict-returning functions is 2-4 weeks of mechanical work, and each conversion can break templates that depend on specific dict key names, nesting, or the ability to add arbitrary keys.

**How to avoid:**
1. Use a **wrapper pattern**, not a replacement pattern. Define the output Pydantic model, but have builders return `model.model_dump()` so templates see the same dict they always did. This separates "adding validation" from "changing what templates consume."
2. Migrate in rings: Ring 1 = the 5-6 builders that produce the most cross-section data (company profile, financials, scoring, litigation). Ring 2 = section-specific builders. Ring 3 = helpers and assembly functions.
3. Each ring must pass all existing tests before starting the next ring.
4. Add a `@typed_output(MyModel)` decorator that validates the dict against the model but still returns the dict. This gives validation without breaking templates.

**Warning signs:**
- PR with 40+ file changes that "adds types to context builders"
- Tests patched to accept both dict and model returns
- Templates modified to handle `.attribute` access alongside `['key']` access

**Phase to address:**
First phase establishes the decorator/wrapper pattern. Subsequent phases migrate ring-by-ring.

---

### Pitfall 3: Canonical Metrics Registry Becomes a God Object

**What goes wrong:**
The canonical metrics registry -- meant to ensure revenue, margin, exchange, and growth rates are computed once -- becomes a 2,000-line module that every context builder imports. Adding a new metric requires understanding the full registry. Circular imports emerge because the registry needs state data that itself depends on computed metrics. The registry becomes the bottleneck for every feature change.

**Why it happens:**
"Compute once, use everywhere" is the right principle but the wrong architecture when taken literally as a single module. The current system has 23 `safe_float` calls in `financials_computed.py` alone, each computing a metric inline. Centralizing all of these into one registry creates a massive dependency hub.

**How to avoid:**
1. Organize metrics by domain, not in a single registry: `metrics/financial.py`, `metrics/market.py`, `metrics/governance.py`. Each is a small, focused module.
2. Metrics are **computed lazily** from state, not eagerly at pipeline start. Use `@cached_property` or a `MetricsCache` that computes on first access.
3. The "consistency" guarantee comes from a **post-computation audit**, not from centralized computation. After all builders run, a checker verifies that revenue appears the same everywhere. This is lighter-weight and doesn't require restructuring builder dependencies.
4. Registry entries should be pure functions: `def revenue(state) -> float | None`. No side effects, no imports from builders, no circular dependencies possible.

**Warning signs:**
- Registry module approaching 500+ lines
- Import cycles involving the registry
- Developers bypassing the registry "just for this one case" because adding to it is too complex
- Registry computing derived values that only one section uses

**Phase to address:**
Canonical Metrics phase. Start with 10-15 core metrics (revenue, net_income, total_assets, market_cap, shares_outstanding, exchange, sector, years_public, employee_count, current_ratio, debt_to_equity, score, tier, probability, severity). Expand only when cross-section inconsistency is proven for a metric.

---

### Pitfall 4: Signal Validation Suppresses Real Findings

**What goes wrong:**
Contextual signal validation (e.g., "suppress IPO signals if years_public > 5") is implemented with overly aggressive rules that hide legitimate findings. A company that went public 6 years ago but did a secondary offering last year gets its offering-related signals suppressed. A CEO-change signal gets suppressed because the validator checks `current_ceo` against state but the state hasn't been updated after an 8-K disclosed the change.

**Why it happens:**
Validation rules are written against clean mental models of data, not against the messy reality of stale state, edge cases, and temporal mismatches. The developer thinks "IPO signals should only fire for companies public < 5 years" but forgets that Section 11 liability windows from secondary offerings can extend well past the 5-year mark. False positive suppression feels safe because "we're just hiding noise" -- but every suppressed signal is a potential blind spot.

**How to avoid:**
1. Validation rules NEVER suppress -- they ANNOTATE. A signal marked `validation_flag: "years_public exceeds IPO threshold"` is still visible in the worksheet with a note, not silently removed.
2. Every validation rule must have an explicit **false-negative risk assessment**: "If this rule incorrectly suppresses, what D&O risk do we miss?" If the answer is "a real liability window," the rule must annotate, not suppress.
3. Validation rules operate on a whitelist, not a blacklist. Instead of "suppress signals that don't match context," use "boost confidence of signals that DO match context."
4. Log every validation suppression with full context. A weekly audit of suppressions should be easy to run.

**Warning signs:**
- Signal count drops significantly after validation is added (e.g., from 120 triggered to 80)
- Underwriter feedback: "Why didn't the system flag X? It's in the 10-K."
- Validation rules referencing state fields that are frequently None (like `company.ticker` and `company.name` which are ALWAYS None per project memory)

**Phase to address:**
Contextual Signal Validation phase. The annotate-not-suppress rule must be the foundational design decision.

---

### Pitfall 5: Output Sanitization Strips Legitimate Content

**What goes wrong:**
The HTML sanitization pass (meant to strip markdown artifacts, debug strings, raw serialization) is implemented with regex patterns that also match legitimate content. A company description containing "**significant**" gets its asterisks stripped. A litigation finding containing `[2024-01-15]` loses its date because the sanitizer treats brackets as markdown artifacts. Dollar amounts like `$3.2B` get corrupted. The existing CLAUDE.md rule "NEVER truncate analytical content" is violated by the sanitizer.

**Why it happens:**
Sanitization regex patterns are tested against known bad inputs but not against the full corpus of legitimate worksheet content. The patterns are broad ("strip all markdown-like syntax") instead of targeted ("strip markdown only in fields that should be plain text"). LLM-generated text can contain legitimate formatting that overlaps with debug artifacts.

**How to avoid:**
1. Sanitization rules must be field-specific, not global. LLM-generated commentary may legitimately use bold/italic. Raw data fields should never contain markdown.
2. Build a **sanitization test corpus** from actual worksheet output (at least 3 tickers). Run every sanitization rule against every field value and verify zero legitimate content is altered.
3. Use a **positive pattern match** for known bad content (e.g., `repr()` output, `<class 'dict'>`, `MagicMock`, `{'key':`) rather than negative pattern removal of formatting characters.
4. Sanitization should produce a diff report: "Changed X occurrences in Y fields." Review this report for false positives before shipping.

**Warning signs:**
- Dollar amounts, dates, or percentages corrupted in output after sanitization added
- LLM commentary loses emphasis/formatting
- Sanitization rules grow beyond 20 patterns (sign of over-broad approach)
- "Fixed sanitization regex" commits appearing repeatedly

**Phase to address:**
Output Sanitization phase. Must be the LAST quality gate, not the first, because it needs real output to test against.

---

### Pitfall 6: MagicMock Tests Pass But Real Integration Fails

**What goes wrong:**
The 1,168 MagicMock fixtures with zero `spec_set` (documented in project memory) continue to pass as typed contracts are added, giving false confidence. A context builder is "migrated" to return a typed model, all MagicMock tests pass, but the first real pipeline run crashes because the mock allowed attribute access patterns that the real state object doesn't support. The entire test suite becomes meaningless for validating the migration.

**Why it happens:**
MagicMock without `spec_set` returns a new MagicMock for any attribute access, so tests pass regardless of whether the code is accessing real state paths or nonsensical ones. When you add typed contracts, the tests don't tell you whether the typed model matches what the real state actually provides. This is the existing codebase's biggest testing gap.

**How to avoid:**
1. Before migrating ANY builder, add a **real-state integration test** for it. Load an actual `state.json` file (from `output/AAPL/` or similar), run the builder, and verify the output matches the typed model.
2. Add `spec_set=AnalysisState` to mocks incrementally -- one test file per PR, starting with the builders being migrated in the current ring.
3. Create a CI gate: `pytest tests/integration/test_real_state_builders.py` that runs all migrated builders against real state files. This is the TRUE validation, not the unit tests.
4. Do NOT delete the MagicMock tests during migration. Keep them for speed. But the integration tests are what gate the PR.

**Warning signs:**
- All unit tests pass but pipeline crashes on first real run after migration
- Developers skip `--fresh` runs because "tests pass"
- `spec_set` addition to a mock breaks 20+ tests in the same file (revealing how many false paths were tested)

**Phase to address:**
Real-State Integration Tests phase. Should run in parallel with the first builder migration ring.

---

### Pitfall 7: Template Variable Renames Break Silently in Jinja2

**What goes wrong:**
When a context builder is migrated from returning `{'market_cap': value}` to returning a Pydantic model dumped as `{'market_capitalization': value}`, Jinja2 templates that reference `{{ market_cap }}` silently render as empty string instead of crashing. The worksheet looks correct at first glance but has blank cells where data should be. This violates the "never make things look worse" mandate.

**Why it happens:**
Jinja2's `undefined` behavior defaults to empty string for `{{ undefined_var }}`. Unlike Python which throws `KeyError`, Jinja2 silently swallows the error. With 260 templates and hundreds of variable references, a rename in the Python layer creates an invisible regression in the template layer.

**How to avoid:**
1. Use Jinja2's `StrictUndefined` or `DebugUndefined` in a CI test environment to catch undefined variable access. NOT in production (it would crash on intentionally optional fields), but in a dedicated template validation test.
2. Before renaming ANY dict key in a builder, grep ALL templates for that key name. The project has 260 templates -- a missed reference is almost guaranteed without automated checking.
3. Build a **template variable registry**: extract all `{{ var }}` references from templates and cross-reference against builder output keys. This is the CI gate described in v12.0 requirements (Template Variable Type Validation).
4. During migration, keep BOTH the old key and the new key in the output dict: `{'market_cap': v, 'market_capitalization': v}`. Remove the old key only after a deprecation period with grep confirmation that no template uses it.

**Warning signs:**
- N/A counts increase after builder migration (fields rendering as empty instead of actual N/A)
- Sections that previously showed data now show nothing (not an error, just blank)
- Template variable coverage drops below 90%

**Phase to address:**
Template Variable Type Validation phase (CI gate). Should be implemented BEFORE builder migration starts, not after.

---

### Pitfall 8: Cross-Section Consistency Checker Creates False Alarms

**What goes wrong:**
The consistency checker that verifies "revenue appears the same everywhere" flags legitimate differences as inconsistencies. Revenue in the executive summary is FY2025 ($3.05B), revenue in the financial trends section is TTM ($3.12B), and revenue in the peer comparison is most-recent-quarter annualized ($3.18B). All are "correct" but different. The checker fires 50+ alerts, developers start ignoring them, and the checker becomes useless noise.

**Why it happens:**
Financial metrics have multiple valid representations depending on time period, accounting method, and context. "Revenue" is not one number -- it's FY revenue, TTM revenue, quarterly revenue, segment revenue, GAAP revenue, non-GAAP revenue. A naive consistency checker that just compares numeric values will drown in false positives.

**How to avoid:**
1. Consistency checks must compare **metric + period + basis** triples, not raw values. `(revenue, FY2025, GAAP)` in section A must equal `(revenue, FY2025, GAAP)` in section B. But `(revenue, FY2025, GAAP)` and `(revenue, TTM, GAAP)` are correctly different.
2. The canonical metrics registry should store the period and basis alongside the value: `CanonicalMetric(value=3.05e9, period="FY2025", basis="GAAP", source="XBRL")`.
3. Start with a SMALL set of truly-canonical facts: ticker, exchange, SIC code, CEO name, total score, tier. These have exactly one correct value. Expand only when false-alarm rate is <5%.
4. Tolerance bands for numeric comparisons: revenue within 1% across sections is "consistent" (rounding differences are expected).

**Warning signs:**
- Consistency checker produces >20 alerts per run
- Developers add exceptions/suppressions faster than they fix real inconsistencies
- Same metric intentionally displayed with different periods in different sections

**Phase to address:**
Cross-Section Consistency Checker phase. Design the metric+period+basis tuple FIRST, implement checker SECOND.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `model.model_dump()` everywhere instead of passing typed models to templates | Templates work unchanged | Lose type safety at the template boundary -- the whole point of typed contracts | During migration only. Must be removed per-section as templates are validated. |
| `# type: ignore` on builder return types during migration | Unblocks migration of dependent code | Accumulates until nobody knows which ignores are intentional vs. lazy | Never more than 10 total. Each must have a TODO with ticket number. |
| Skipping `spec_set` on new MagicMock fixtures | Tests are faster to write | Continues the 1,168-mock problem that makes integration testing unreliable | Never. All new mocks must have `spec_set`. |
| Hardcoding metric values in consistency checker expected set | Checker works for known tickers | Fails for new tickers with different data availability | Never. Checker must be data-driven, not ticker-driven. |
| Global sanitization regex instead of field-specific | Faster to implement | Strips legitimate content, requires ongoing regex maintenance | Never. Spend the extra day making it field-specific. |

## Integration Gotchas

Mistakes when connecting typed contracts to existing system components.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Pydantic model + Jinja2 template | Passing model object directly; template uses `{{ model.field }}` but Jinja2 attribute access differs from Python | Always `model.model_dump()` for Jinja2 context. Or register a custom Jinja2 extension for model access. |
| Canonical metrics + brain signals | Metrics registry duplicates computation already done by signal evaluators | Metrics registry reads FROM signal results, doesn't recompute. Signals remain source of truth for evaluated values. |
| Signal validation + state_paths.py | Validation rules access state directly instead of through canonical paths | All state access in validation rules must go through `state_paths.py` registry. 44 builders still need migration. |
| Output sanitization + `safe_float()` | Sanitizer runs before formatters, corrupting values that `safe_float` would have handled | Sanitization runs on FINAL HTML output, after all formatting. Never on intermediate data. |
| Consistency checker + re-render | Checker runs on state but not on rendered output; state is consistent but template formatting introduces differences | Checker must have two modes: state-level (metric values) and output-level (rendered text). |
| Typed contracts + Word renderer | HTML and Word renderers consume shared context but have different field needs | Output contracts must be renderer-agnostic. Word-specific fields go in a separate model, not the shared contract. |

## Performance Traps

Patterns that work at small scale but fail as the system grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Eager validation of full state on every builder call | Pipeline slows 2-5x; validation dominates render time | Validate once at render entry point, pass validated state to all builders | When state.json > 5MB (most tickers) |
| Consistency checker runs N^2 comparisons across all sections | Checker takes >10s, longer than rendering itself | Compare against canonical registry, not between sections pairwise | When sections exceed 20 |
| Sanitization regex compiled per-call instead of module-level | Imperceptible at first, adds 100ms+ per section | Compile regexes at module import time with `re.compile()` | When template count exceeds 100 (already there) |
| Real-state integration tests loading full state.json per test | Test suite goes from 30s to 5+ minutes | Load state.json once per test module with `@pytest.fixture(scope="module")`, share across tests | When integration tests exceed 50 |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Typed output contract:** Often missing Optional defaults -- verify that model accepts `{}` (empty dict) without crashing, because some tickers genuinely have near-empty state sections
- [ ] **Canonical metrics:** Often missing period/basis metadata -- verify that `get_revenue()` returns not just the number but WHICH revenue (FY vs TTM vs quarterly)
- [ ] **Signal validation:** Often missing false-negative analysis -- verify that every suppression rule has a documented risk assessment ("if we suppress this incorrectly, we miss X")
- [ ] **Output sanitization:** Often missing corpus testing -- verify sanitizer has been run against at least 3 real ticker outputs without corrupting legitimate content
- [ ] **Consistency checker:** Often missing tolerance bands -- verify that rounding differences (e.g., $3.050B vs $3.05B) don't trigger false alarms
- [ ] **Template validation CI gate:** Often missing partial template coverage -- verify that `{% include %}` sub-templates are also validated, not just top-level templates
- [ ] **MagicMock replacement:** Often missing edge case mocks -- verify that new `spec_set` mocks reproduce the None/missing-data patterns from real state, not just the happy path
- [ ] **Builder migration:** Often missing the `model_dump()` call -- verify that templates still receive dicts, not Pydantic model objects (Jinja2 handles them differently)

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Pydantic rigidity crashes pipeline | LOW | Add `Optional` defaults to failing fields, re-run. No schema redesign needed. |
| Big-bang migration stalls at 50% | HIGH | Revert to wrapper/decorator pattern. Significant rework of already-migrated builders. |
| God-object metrics registry | MEDIUM | Split into domain modules. Import paths change but logic is preserved. |
| Signal validation hides real findings | HIGH | Audit all suppressions against actual worksheet output. May need to re-run with validation disabled and manually compare. Underwriter trust impact. |
| Sanitization corrupts content | LOW | Disable sanitizer, re-render. Fix regex patterns against corpus. Re-enable. |
| MagicMock tests mask real failures | MEDIUM | Add real-state integration tests retroactively. Each test reveals 3-5 bugs. 2-3 day effort. |
| Template variables silently disappear | MEDIUM | Run `StrictUndefined` test pass, fix all template references. 1-2 days for 260 templates. |
| Consistency checker drowns in false alarms | LOW | Narrow to 5-10 truly-canonical facts. Rebuild trust with low-noise baseline. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Pydantic rigidity | Typed Output Contract (Phase 1) | Model accepts real state.json from 3+ tickers without ValidationError |
| Big-bang migration | Typed Output Contract (Phase 1) | Decorator/wrapper pattern documented and used for first 5 builders; no template changes |
| God-object registry | Canonical Metrics (Phase 2) | Registry split into 3+ domain modules; no module >200 lines; no circular imports |
| Signal suppression | Contextual Validation (Phase 3) | Zero suppressed signals; all validation results are annotations; log output reviewable |
| Sanitization corruption | Output Sanitization (Phase 5) | Sanitizer tested against 3+ ticker corpus; zero legitimate content altered; diff report clean |
| MagicMock masking | Real-State Integration Tests (Phase 4+) | Integration test exists for every migrated builder; CI runs against real state.json |
| Silent template renames | Template Variable Validation (CI gate, Phase 1) | CI gate catches undefined variables before merge; zero undeclared variables in templates |
| False-alarm consistency | Cross-Section Consistency (Phase 2) | Checker produces <5 alerts per ticker; all alerts are real inconsistencies |

## Sources

- Direct analysis of project codebase: 97 context builders, 260 templates, 208 dict-returning functions, 383 `safe_float`/`format_na` call sites, 115 MagicMock test files
- [Pydantic Migration Guide](https://docs.pydantic.dev/latest/migration/) -- patterns for gradual migration
- [Pydantic Upgrade Lessons](https://swilcox.github.io/post/pydantic_upgrade_lessons/) -- real-world migration experience
- [Jinja2 Undefined Types](https://jinja.palletsprojects.com/en/stable/api/) -- StrictUndefined for template validation
- [Canonical Data Models Guide](https://www.alation.com/blog/canonical-data-models-explained-benefits-tools-getting-started/) -- pitfalls of single canonical models
- [dbt Semantic Layer at Scale](https://b-eye.com/blog/dbt-semantic-layer-scale/) -- metrics layer consistency challenges
- [Why Single Canonical Data Model Slows Integration](https://www.appseconnect.com/why-a-single-canonical-data-model-slows-down-modern-integration/) -- overhead of canonical schemas
- Project CLAUDE.md rules on `safe_float()`, visual quality, content preservation, and self-verification
- Project MEMORY.md: 1,168 unspec'd MagicMocks, `state.company.ticker` always None, state_paths.py migration status

---
*Pitfalls research for: Adding typed contracts and quality gates to existing untyped Python/Jinja2 pipeline*
*Researched: 2026-03-27*
