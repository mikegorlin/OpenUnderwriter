# Phase 109: Pattern Engines + Named Patterns - Research

**Researched:** 2026-03-16
**Domain:** Pattern detection engines, case library, named archetypes, firing panel visualization
**Confidence:** HIGH

## Summary

Phase 109 implements four pattern detection engines (Conjunction Scan, Peer Outlier, Migration Drift, Precedent Match), a YAML case library seeded with 20 canonical D&O cases, 6 named archetypes, and a firing panel visualization. All four engines operate on data already available in the pipeline (signal evaluation results, XBRL quarterly data, SEC Frames peer data). The engines are independent of each other and run in parallel during the ScoreStage pipeline.

The implementation builds on substantial existing infrastructure: `brain_correlation.py` (463 lines of co-occurrence mining), `brain_schema.py::PatternDefinition` (Pydantic schema), `ScoringLens` Protocol pattern (from Phase 107), `SeverityLens` Protocol pattern (from Phase 108), and three complete design artifacts from Phase 106 (`pattern_engine_design.yaml`, `case_library_design.yaml`, `named_archetypes_design.yaml`). The primary technical risks are: (1) ensuring Conjunction Scan works with seed correlations when `brain_correlations` table has no run history, (2) correctly extracting quarterly XBRL trend data for Migration Drift from the existing `QuarterlyStatements` model, and (3) keeping each new source file under the 500-line project limit.

**Primary recommendation:** Implement a `PatternEngine` Protocol mirroring the `ScoringLens` and `SeverityLens` patterns. Each engine is a standalone module in `stages/score/` with its own file. Results stored on `state.scoring` via a new `PatternEngineResult` Pydantic model. Firing panel rendered as a new context builder + HTML section template.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Conjunction Scan: seed + enrich model. Ship with curated seed correlation table from D&O domain knowledge. `brain_correlations` from actual runs supplement/override seeds as run history builds.
- Peer Outlier: reuse existing SEC Frames data. No new ACQUIRE step. Limited to already-acquired metrics.
- Migration Drift: AnalysisState XBRL only. Operates on 8 quarters already extracted. No cross-run history needed.
- Missing data: NOT_FIRED with note "Insufficient data." No distinct DATA_UNAVAILABLE visual state.
- Case library: YAML file(s) in `brain/framework/`. Pydantic-validated. Loaded at runtime like signals.
- Signal profile depth: deep reconstruction (50-100 signals) for 5-6 landmark cases, key-facts level (10-20 signals) for remaining 14.
- Auto-expansion: When pipeline detects active SCAC filing, auto-create case entry with current signal profile and outcome=ongoing. Flagged as POST_FILING with LOW confidence.
- Engine thresholds: Use design doc defaults. All thresholds in config YAML, not hardcoded.
- Archetype recommendation_floor: raises tier, never lowers. Consistent with CRF veto logic.
- No aggregate pattern score. Each engine stands alone.
- Precedent Match: show all matches including dismissals. Dismissed cases get 0.5x outcome severity weight.
- Firing panel: always show all 10 items (4 engines + 6 archetypes). Gray cards for NOT_FIRED.
- Placement: after scoring, before P x S.
- Card detail: compact face + expandable drill-down.
- Precedent Match: top 3 matches with similarity + outcome.

### Claude's Discretion
- Code organization within stages/score/ (new files, module structure)
- Exact Pydantic model structure for engine results and case library entries
- Seed correlation table contents and format
- Signal profile reconstruction depth judgment per case
- How to integrate engine results into the ScoreStage pipeline
- Chart rendering details for the firing panel (card layout, colors, spacing)
- YAML schema for case library entries (extending or mirroring PatternDefinition)

### Deferred Ideas (OUT OF SCOPE)
- Supabase migration for growing knowledge corpus
- Aggregate pattern score (weighted composite across engines)
- Interactive calibration session for pattern thresholds
- Bow-Tie engine and Control System engine (ADV-03, ADV-04)
- Case library versioning and immutability
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PAT-01 | Conjunction Scan engine detects 3+ individually normal signals co-occurring as elevated risk | Seed correlation table + brain_correlation.py infrastructure; cross-domain check via rap_signal_mapping.yaml |
| PAT-02 | Peer Outlier engine detects multi-dimensional statistical outliers from SEC Frames data | XBRL data already on state.extracted.financials.quarterly_xbrl; z-score computation via median/MAD |
| PAT-03 | Migration Drift engine detects cross-domain gradual deterioration from XBRL quarterly trends | QuarterlyStatements model has 8 quarters; linear regression slope per subcategory |
| PAT-04 | Precedent Match engine computes signal profile similarity against case library | Weighted Jaccard on binary fingerprint; CRF signals 3x weight; case_library_design.yaml schema |
| PAT-05 | Case library seeded from Stanford SCAC data (signal profiles + outcomes) | 20 canonical cases defined in case_library_design.yaml; deep profiles for 6 landmarks |
| PAT-06 | 6 named D&O pattern archetypes defined in YAML | named_archetypes_design.yaml has all 6 with real signal IDs; PatternDefinition schema fits |
| PAT-07 | Engine firing panel visualization showing which engines fired with confidence | HTML card grid with 10 items; context builder + Jinja2 template; severity_context.py as pattern |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Data models for engine results, case library entries | Project standard; all models use Pydantic |
| PyYAML | existing | Load case library, archetype definitions, seed correlations | Project standard; brain YAML ecosystem |
| Python math/statistics | stdlib | Linear regression, z-scores, Jaccard similarity | No external deps needed; computations are simple |
| matplotlib | existing | Firing panel chart (if needed for PDF) | Project standard for charts |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | existing | MAD computation, vectorized z-scores for Peer Outlier | Only if stdlib statistics is insufficient for MAD |
| Jinja2 | existing | Firing panel HTML template | Project standard for rendering |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scipy for statistics | stdlib math/statistics | scipy would add dependency; all computations (linear regression, z-scores, sigmoid) are simple enough for stdlib |
| sklearn for similarity | manual Jaccard implementation | sklearn is overkill for weighted Jaccard on binary vectors; ~20 lines of Python |
| DuckDB for Conjunction Scan correlations | In-memory dict lookup from seed YAML | DuckDB requires run history that may not exist yet; seed YAML is the cold-start solution |

**No new installation needed.** All libraries are already in the project.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  stages/score/
    pattern_engine.py          # PatternEngine Protocol + PatternEngineResult models (~80 lines)
    conjunction_scan.py        # Conjunction Scan engine implementation (~250 lines)
    peer_outlier.py            # Peer Outlier engine implementation (~250 lines)
    migration_drift.py         # Migration Drift engine implementation (~250 lines)
    precedent_match.py         # Precedent Match engine implementation (~250 lines)
    _pattern_runner.py         # Orchestrator: runs all 4 engines, evaluates archetypes (~200 lines)
  models/
    patterns.py                # Pydantic models: EngineResult, ArchetypeResult, FiringPanelData (~200 lines)
  brain/framework/
    seed_correlations.yaml     # Curated seed co-fire pairs for Conjunction Scan
    case_library.yaml          # 20 seed cases with signal profiles
    named_archetypes_design.yaml  # Already exists - 6 archetypes
  stages/render/
    context_builders/
      pattern_context.py       # Build firing panel template context (~150 lines)
    charts/
      firing_panel.py          # HTML card grid renderer (~200 lines)
tests/stages/score/
    test_conjunction_scan.py
    test_peer_outlier.py
    test_migration_drift.py
    test_precedent_match.py
    test_pattern_runner.py
    test_pattern_context.py
```

### Pattern 1: PatternEngine Protocol
**What:** Mirror the ScoringLens and SeverityLens Protocol pattern for pattern engines. Each engine implements `evaluate()` returning a typed result.
**When to use:** All 4 engines and the 6 archetype evaluations.
**Example:**
```python
# Source: Established pattern from stages/score/scoring_lens.py + severity_lens.py
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class PatternEngine(Protocol):
    """Protocol for pluggable pattern detection engines."""

    @property
    def engine_id(self) -> str: ...

    @property
    def engine_name(self) -> str: ...

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        state: AnalysisState | None = None,
    ) -> EngineResult: ...
```

### Pattern 2: Step Integration in ScoreStage
**What:** Add pattern engine execution as Step 16 in the ScoreStage pipeline, after severity (Step 15.5).
**When to use:** When integrating engine results into the scoring pipeline.
**Example:**
```python
# Source: Established pattern from stages/score/__init__.py Step 15.5
# In ScoreStage.run(), after Step 15.5 severity:

# Step 16: Pattern engines (Phase 109)
try:
    from do_uw.stages.score._pattern_runner import run_pattern_engines
    pattern_result = run_pattern_engines(
        state=state,
        signal_results=signal_results,
        hae_result=hae_result,
    )
    if pattern_result is not None:
        state.scoring.pattern_engine_result = pattern_result
        # Apply archetype tier floors
        if hae_result is not None:
            for archetype in pattern_result.archetype_results:
                if archetype.fired and archetype.recommendation_floor:
                    floor_tier = HAETier(archetype.recommendation_floor)
                    if floor_tier > hae_result.tier:
                        hae_result = hae_result.model_copy(update={
                            "tier": floor_tier,
                            "tier_source": f"pattern_floor:{archetype.archetype_id}",
                        })
except Exception:
    logger.warning("Pattern engines failed; continuing without patterns", exc_info=True)
```

### Pattern 3: Seed + Enrich for Cold Start
**What:** Ship with curated seed YAML data that works on day one, with DuckDB correlations supplementing/overriding seeds as run history builds.
**When to use:** Conjunction Scan engine -- needs co-fire rate data that may not exist yet.
**Example:**
```python
# Source: CONTEXT.md locked decision
def _load_correlations() -> dict[tuple[str, str], float]:
    """Load seed correlations from YAML, supplement with DuckDB if available."""
    # Always start with seed data
    seed_path = Path(__file__).parent.parent.parent / "brain" / "framework" / "seed_correlations.yaml"
    correlations = _parse_seed_yaml(seed_path)

    # Try to supplement/override with empirical data from brain_correlations
    try:
        db_correlations = _load_from_duckdb()
        for pair, rate in db_correlations.items():
            correlations[pair] = rate  # Empirical overrides seed
    except Exception:
        pass  # Seed data is sufficient

    return correlations
```

### Pattern 4: Graceful Degradation
**What:** Engine failure is logged as warning, scoring continues. Missing data = NOT_FIRED with note.
**When to use:** Every engine must handle missing data gracefully.
**Example:**
```python
# Source: Established pattern from ScoreStage Step 7.5 (hae_scoring) and Step 15.5 (severity)
class ConjunctionScanEngine:
    def evaluate(self, signal_results, *, state=None) -> EngineResult:
        correlations = _load_correlations()
        if not correlations:
            return EngineResult(
                engine_id="conjunction_scan",
                engine_name="Conjunction Scan",
                fired=False,
                confidence=0.0,
                headline="Insufficient correlation data",
                findings=[],
            )
        # ... actual computation ...
```

### Anti-Patterns to Avoid
- **Monolithic engine file:** Each engine MUST be its own file under 500 lines. The runner orchestrates all four.
- **Hardcoded thresholds:** All thresholds in YAML config files, never in code. CONTEXT.md explicitly requires this.
- **Cross-engine dependencies:** Engines are independent and parallel. No engine reads another engine's output.
- **Mutating HAETier directly:** Archetype tier floors go through the existing tier comparison pattern (max of current tier vs floor), never replace the tier unconditionally.
- **New ACQUIRE steps:** Peer Outlier uses existing SEC Frames data, Migration Drift uses existing XBRL. No new acquisition.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Co-fire correlation table | Mining engine from scratch | Extend `brain_correlation.py` + seed YAML | 463-line engine already exists with CorrelatedPair model |
| Signal fingerprint extraction | Manual dict traversal | `_signal_consumer.py::get_signal_result()` + `get_signals_by_prefix()` | Typed extraction layer already handles status/value/rap_class |
| Pydantic schema for archetypes | New schema from scratch | Extend `PatternDefinition` from `brain_schema.py` | Already has required_signals, minimum_matches, recommendation_floor, rap_dimensions, historical_cases, epistemology |
| YAML loading/validation | Custom loaders | Follow brain_unified_loader.py + YAML safe_load pattern | Project-standard pattern for YAML -> Pydantic |
| Tier floor application | Custom tier logic | HAETier comparison operators (`>`, `max()`) | HAETier already has `__lt__`, `__gt__`, `__ge__`, `__le__` for ordered comparison |
| Context builder for rendering | Custom template data | Follow severity_context.py pattern | 180-line context builder is the canonical pattern from Phase 108 |

**Key insight:** This phase assembles existing infrastructure into new engines more than it builds from scratch. The signal consumer, brain schema, correlation mining, scoring lens protocol, and rendering patterns are all established. The novel work is the engine algorithms themselves and the case library data.

## Common Pitfalls

### Pitfall 1: Cold Start Data Gap
**What goes wrong:** Conjunction Scan queries `brain_correlations` table in DuckDB but no runs have been executed, so the table is empty.
**Why it happens:** New installation or fresh pipeline -- no historical run data to mine co-occurrences from.
**How to avoid:** CONTEXT.md decision: seed + enrich model. Ship curated seed correlation YAML with known D&O co-fire patterns (e.g., insider selling + margin compression + guidance miss). Seed data works on first run. DuckDB supplements over time.
**Warning signs:** Engine returns NOT_FIRED on every company because correlations dict is empty.

### Pitfall 2: XBRL Data Completeness for Migration Drift
**What goes wrong:** `QuarterlyStatements.quarters` has fewer than 4 quarters, making linear regression unreliable.
**Why it happens:** Company is recently public, fiscal year is non-standard, or XBRL extraction failed for some quarters.
**How to avoid:** Check `len(quarters) >= 4` before computing slope. Return NOT_FIRED with "Insufficient quarterly data (N quarters, need 4)" if below minimum.
**Warning signs:** NaN or extreme slope values from regression on 1-2 data points.

### Pitfall 3: Peer Outlier Peer Set Size
**What goes wrong:** Fewer than 10 sector peers in SEC Frames data, making z-scores statistically meaningless.
**Why it happens:** Niche sectors, non-standard GICS classification, or SEC Frames data gaps.
**How to avoid:** Check peer count >= 10 as per design doc thresholds. Use MAD (median absolute deviation) instead of standard deviation for robustness to outliers in the peer set. Return NOT_FIRED if insufficient peers.
**Warning signs:** z-scores that are extreme (>10) due to tiny peer sets with one unusual company.

### Pitfall 4: Weighted Jaccard Division by Zero
**What goes wrong:** Weighted Jaccard similarity formula has denominator of zero when both company and case have all zeros for a set of signals.
**Why it happens:** Most signals are CLEAR/not-fired for both company and case, SKIPPED signals excluded, very few overlapping fired signals.
**How to avoid:** Guard: `if total_weight_denominator == 0: return 0.0`. This naturally happens when neither company nor case fires any weighted signals.
**Warning signs:** ZeroDivisionError in Precedent Match.

### Pitfall 5: 500-Line File Limit
**What goes wrong:** Engines have both computation and data loading logic, growing past the project limit.
**Why it happens:** Each engine has: config loading, data extraction, computation, result building, logging.
**How to avoid:** Plan file splits from the start. Each engine file handles only computation. Shared utilities (YAML loading, correlation loading, case library loading) go in `_pattern_runner.py` or dedicated helpers.
**Warning signs:** Any file approaching 400 lines needs proactive splitting.

### Pitfall 6: Forward Reference in ScoringResult
**What goes wrong:** Adding `pattern_engine_result` field to ScoringResult creates circular import.
**Why it happens:** ScoringResult is in models/, pattern result model references types from stages/score/.
**How to avoid:** Follow the established TYPE_CHECKING + model_rebuild() pattern from Phase 107/108. Define PatternEngineResult in a models/ file (not stages/score/). Use `if TYPE_CHECKING:` for forward references. Call `ScoringResult.model_rebuild()` in the `_rebuild_scoring_models()` function.
**Warning signs:** ImportError at module load time.

### Pitfall 7: Archetype Signal ID Mismatches
**What goes wrong:** Signal IDs in named_archetypes_design.yaml don't match actual brain signal IDs.
**Why it happens:** Design doc created from survey of signals but not validated against the canonical signal list at implementation time.
**How to avoid:** At startup, validate all archetype required_signals against the loaded brain signal registry. Log warnings for unresolvable IDs. The `future_signal.*` IDs in AI Mirage are expected to be missing -- handle gracefully.
**Warning signs:** Archetypes never fire because required signals don't resolve.

## Code Examples

### Engine Result Model
```python
# Source: Pattern from ScoringLensResult + SeverityLensResult
class EngineResult(BaseModel):
    """Result from a single pattern engine evaluation."""
    model_config = ConfigDict(frozen=False)

    engine_id: str
    engine_name: str
    fired: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    headline: str = ""  # One-sentence summary
    findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### Archetype Evaluation
```python
# Source: PatternDefinition schema from brain_schema.py
class ArchetypeResult(BaseModel):
    """Result from evaluating a named archetype."""
    archetype_id: str
    archetype_name: str
    fired: bool = False
    signals_matched: int = 0
    signals_required: int = 0
    matched_signal_ids: list[str] = Field(default_factory=list)
    recommendation_floor: str | None = None  # e.g., "ELEVATED"
    confidence: float = 0.0
    historical_cases: list[str] = Field(default_factory=list)
```

### Weighted Jaccard Similarity
```python
# Source: case_library_design.yaml similarity_metrics
def weighted_jaccard(
    company_fingerprint: dict[str, bool],
    case_fingerprint: dict[str, bool],
    weights: dict[str, float],
) -> float:
    """Compute weighted Jaccard similarity between two binary fingerprints."""
    numerator = 0.0
    denominator = 0.0
    for signal_id in set(company_fingerprint) | set(case_fingerprint):
        c = 1.0 if company_fingerprint.get(signal_id, False) else 0.0
        k = 1.0 if case_fingerprint.get(signal_id, False) else 0.0
        w = weights.get(signal_id, 1.0)
        numerator += w * min(c, k)
        denominator += w * max(c, k)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator
```

### Linear Regression for Migration Drift
```python
# Source: pattern_engine_design.yaml migration_drift algorithm
def _compute_slope(values: list[float]) -> float | None:
    """Compute standardized linear regression slope over quarterly values.

    Returns slope / std, or None if insufficient data.
    """
    n = len(values)
    if n < 4:
        return None
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    ss_xy = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(values))
    ss_xx = sum((i - mean_x) ** 2 for i in range(n))
    if ss_xx == 0:
        return None
    slope = ss_xy / ss_xx
    std = (sum((y - mean_y) ** 2 for y in values) / max(n - 1, 1)) ** 0.5
    if std == 0:
        return None
    return slope / std
```

### Seed Correlation Entry
```yaml
# Source: D&O domain knowledge for Conjunction Scan seed data
seed_correlations:
  - signal_a: GOV.INSIDER.cluster_sales
    signal_b: FIN.TEMPORAL.margin_compression
    co_fire_rate: 0.35
    rationale: "Insider selling often precedes margin deterioration disclosure"
  - signal_a: FIN.GUIDE.track_record
    signal_b: STOCK.PRICE.recent_drop_alert
    co_fire_rate: 0.40
    rationale: "Guidance misses and stock drops are strongly correlated"
  - signal_a: GOV.EFFECT.material_weakness
    signal_b: FIN.ACCT.restatement
    co_fire_rate: 0.55
    rationale: "Material weakness is a leading indicator of restatement"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy pattern_detection.py (19 patterns from brain/patterns.json against extracted data) | v7.0 pattern engines operating on signal evaluation results | Phase 109 | New engines detect cross-domain compound patterns invisible to single-signal or single-factor analysis |
| No case library | YAML case library with signal fingerprints | Phase 109 | Precedent-based risk assessment formalizes experienced UW pattern recognition |
| No named archetypes | 6 named D&O archetypes with real signal IDs | Phase 109 | Named patterns provide underwriter-friendly language ("Accounting Time Bomb") |
| Ad-hoc pattern display | Unified firing panel (10 items: 4 engines + 6 archetypes) | Phase 109 | "Show your work" philosophy -- UW sees all 10 were checked |

**Existing legacy pattern_detection.py (Step 3 in ScoreStage) remains unchanged.** The new engines are additive -- they operate on signal results, not extracted data. Both systems coexist.

## Open Questions

1. **Archetype tier floor interaction with CRF vetoes**
   - What we know: CRF vetoes raise tier (non-compensatory). Archetype floors also raise tier, never lower.
   - What's unclear: If both a CRF veto and an archetype floor apply, do they interact or is it simply max(all applicable floors)?
   - Recommendation: Use `max()` across all tier overrides -- CRF vetoes, archetype floors, and individual dimension criteria. They are all "tier cannot be lower than X" constraints.

2. **SEC Frames peer data availability for Peer Outlier**
   - What we know: The pipeline already pulls SEC Frames data for benchmarking (Phase 75). Peer Outlier reuses this.
   - What's unclear: Exactly which metrics are already extracted and stored on AnalysisState. The `BenchmarkResult.frames_percentiles` dict may already have the z-score context.
   - Recommendation: Audit `state.benchmarks.frames_percentiles` at implementation time. If it already contains per-metric company_value + peer stats, Peer Outlier can consume directly. If not, it may need to call the frames data extraction code.

3. **Auto-expansion of case library with SCAC filings**
   - What we know: CONTEXT.md says auto-add cases when pipeline detects active SCAC filing. Cases get POST_FILING flag and LOW confidence.
   - What's unclear: Where to detect active SCAC filings in the current pipeline. The litigation extraction may already flag this.
   - Recommendation: Check `state.extracted.litigation` for active SCAC filing indicators. Implementation detail for Plan 109-02.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing, 5,687+ tests) |
| Config file | `pyproject.toml` (existing) |
| Quick run command | `uv run pytest tests/stages/score/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAT-01 | Conjunction Scan detects 3+ co-occurring normal signals as elevated risk | unit | `uv run pytest tests/stages/score/test_conjunction_scan.py -x` | Wave 0 |
| PAT-02 | Peer Outlier detects multi-dimensional statistical outliers | unit | `uv run pytest tests/stages/score/test_peer_outlier.py -x` | Wave 0 |
| PAT-03 | Migration Drift detects cross-domain gradual deterioration | unit | `uv run pytest tests/stages/score/test_migration_drift.py -x` | Wave 0 |
| PAT-04 | Precedent Match computes signal profile similarity against case library | unit | `uv run pytest tests/stages/score/test_precedent_match.py -x` | Wave 0 |
| PAT-05 | Case library seeded with 20 canonical D&O cases | unit + validation | `uv run pytest tests/stages/score/test_case_library.py -x` | Wave 0 |
| PAT-06 | 6 named archetypes defined in YAML with required signals | unit + validation | `uv run pytest tests/stages/score/test_archetypes.py -x` | Wave 0 |
| PAT-07 | Engine firing panel visualization | unit | `uv run pytest tests/stages/score/test_pattern_context.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/score/ -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/score/test_conjunction_scan.py` -- covers PAT-01
- [ ] `tests/stages/score/test_peer_outlier.py` -- covers PAT-02
- [ ] `tests/stages/score/test_migration_drift.py` -- covers PAT-03
- [ ] `tests/stages/score/test_precedent_match.py` -- covers PAT-04
- [ ] `tests/stages/score/test_case_library.py` -- covers PAT-05 (validates 20 cases load, Pydantic validates)
- [ ] `tests/stages/score/test_archetypes.py` -- covers PAT-06 (validates 6 archetypes, signal IDs resolve)
- [ ] `tests/stages/score/test_pattern_runner.py` -- covers integration of all engines
- [ ] `tests/stages/score/test_pattern_context.py` -- covers PAT-07 (firing panel context builder)

Framework install: None needed -- existing pytest infrastructure covers all requirements.

## Sources

### Primary (HIGH confidence)
- `brain/framework/pattern_engine_design.yaml` -- complete algorithm specifications for all 4 engines
- `brain/framework/case_library_design.yaml` -- case schema, 20 seed cases, similarity metrics
- `brain/framework/named_archetypes_design.yaml` -- 6 archetypes with real signal IDs
- `brain/brain_schema.py` -- PatternDefinition Pydantic schema
- `brain/brain_correlation.py` -- co-occurrence mining infrastructure (CorrelatedPair, mine_cooccurrences)
- `stages/score/scoring_lens.py` -- ScoringLens Protocol pattern
- `stages/score/severity_lens.py` -- SeverityLens Protocol pattern
- `stages/score/__init__.py` -- ScoreStage 16-step pipeline
- `stages/score/_severity_runner.py` -- runner pattern for pluggable computation
- `stages/render/context_builders/severity_context.py` -- context builder pattern
- `models/scoring.py` -- ScoringResult model (where pattern results are stored)
- `models/severity.py` -- SeverityResult model (comparison: lens result architecture)
- `models/financials.py` -- QuarterlyStatements, QuarterlyPeriod models (XBRL data for Migration Drift)
- `stages/render/context_builders/_signal_consumer.py` -- SignalResultView, get_signal_result()

### Secondary (MEDIUM confidence)
- `109-CONTEXT.md` -- user decisions constraining implementation scope
- `REQUIREMENTS.md` -- PAT-01 through PAT-07 requirements

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new dependencies
- Architecture: HIGH -- established Protocol pattern (ScoringLens, SeverityLens), established runner pattern (_severity_runner.py), established context builder pattern (severity_context.py)
- Pitfalls: HIGH -- cold-start data gap, XBRL completeness, peer set size, Jaccard division-by-zero, file size limits, forward references are all known issues with known mitigations from prior phases
- Algorithm specifications: HIGH -- complete in Phase 106 design artifacts with step-by-step algorithms, thresholds, and complexity analysis

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable -- domain-specific implementation with no external dependency risk)
