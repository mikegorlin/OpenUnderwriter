# Phase 50: Automated QA & Anomaly Detection - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning
**Source:** Interactive discussion

<domain>
## Phase Boundary

Phase 50 delivers four capabilities:
1. Post-analyze automated health summary (CLI)
2. `brain health` unified command
3. `brain delta` cross-run comparison command
4. `brain audit` brain health audit command

AND the foundational brain architecture and rendering evolution that makes QA meaningful:
- **Signal Composites** — a new brain-level concept for evaluating groups of related signals together
- **Facet-driven rendering** — facets control display, composites control analysis

The three-layer architecture must be established:
```
Signals (atomic evaluation) → Composites (brain analysis) → Facets (display)
```
</domain>

<decisions>
## Implementation Decisions

### Three-Layer Architecture (Locked — NON-NEGOTIABLE)
The system has THREE distinct layers. These MUST NOT be conflated:

1. **Signals** (atomic) — Individual threshold evaluations. Each signal checks ONE thing and produces ONE verdict (TRIGGERED/CLEAR/SKIPPED). Signals do NOT compose narratives or group with other signals. This layer exists and does not change.

2. **Signal Composites** (brain analysis — NEW) — A brain-level concept for evaluating groups of related signals together and producing composite analytical conclusions. Composites read multiple signal results and produce structured composite conclusions. This is an ANALYSIS function, not a display function. Composites live in the brain layer.

3. **Facets** (display/presentation) — Control how composite conclusions and signal results are rendered. Facets are PURELY about presentation — what section, what layout, what format. Facets reference composites (and individual signals not in any composite) for content.

**Key distinction:** "Group these stock drop signals and tell me if they're company-specific" is a COMPOSITE (brain analysis). "Show the drop analysis as a narrative with a table underneath" is a FACET (display).

### Signal Composites — Definition (Locked)
- A Composite is a declared group of related signals in brain YAML
- Composites evaluate AFTER individual signals have fired
- A Composite reads the SignalResult of each member signal and produces a CompositeResult
- CompositeResult contains structured analytical conclusions with rich detail
- Composites are defined in brain YAML (e.g., brain/composites/*.yaml or similar)
- The existing `chain_roles` metadata on signals hints at composite membership but chains are NOT composites — chains describe causal relationships, composites describe analytical groupings

Example Composite:
```yaml
id: COMP.STOCK.drop_analysis
name: Stock Drop Analysis
description: Evaluates all stock drop signals together to produce composite conclusion
member_signals:
  - STOCK.PRICE.single_day_events   # raw drop events
  - STOCK.PRICE.attribution          # company vs sector split
  - STOCK.PATTERN.peer_divergence    # peer gap magnitude
  - STOCK.PATTERN.event_collapse     # drop + company trigger + peers fine
  - STOCK.PRICE.recovery             # post-drop recovery
  - STOCK.INSIDER.cluster_timing     # pre-drop insider selling
conclusion_schema:
  events_by_pattern:     # grouped by: earnings, litigation, sector, company-specific
  attribution_summary:   # "2 company-specific, 1 sector-wide"
  recovery_assessment:   # "no recovery from company-specific drops"
  insider_correlation:   # "insider selling preceded Aug drop"
```

### Signal Result Enrichment (Locked)
- Add a `details` field to SignalResult that carries structured data
- Signal evaluations that compute rich data (drop events, insider clusters, peer comparisons) MUST flow that data into `details` rather than discarding it after threshold evaluation
- Example: `STOCK.PRICE.single_day_events` currently produces `value: 3` (count). It MUST also produce `details.events: [{date, drop_pct, trigger, sector_drop, company_specific, recovery}, ...]`
- The `details` field is what Composites READ to produce their analytical conclusions
- Signals provide raw structured data → Composites analyze it → Facets display the conclusions

### Facet-Driven Rendering (Locked)
- Rendering MUST be driven by facet definitions, not prefix-based grouping
- The current `_group_signals_by_section()` prefix-based approach is retired
- Facets are PURELY display — they reference composites and signals for content
- Each facet's `display_type` and `display_config` controls HOW to render
- Facets do NOT contain analytical logic — that belongs in composites
- `_PREFIX_TO_FACET` bridge map and `_PREFIX_DISPLAY` map are deprecated

### Facet References Composites (Locked)
- Facets declare which composites and individual signals they display
- A facet can contain: composites (which bring their own analytical conclusions) AND standalone signals (not part of any composite)
- Example: market_activity facet references COMP.STOCK.drop_analysis (composite) + STOCK.VALUATION.pe_ratio (standalone signal)

```yaml
# Facet YAML (display layer)
id: market_activity
name: Market Activity
display_type: hybrid
content:
  - ref: COMP.STOCK.drop_analysis
    render_as: narrative_with_table
  - ref: COMP.STOCK.short_analysis
    render_as: metric_with_alerts
  - ref: STOCK.VALUATION.pe_ratio
    render_as: metric_row
  - ref: STOCK.VALUATION.ev_ebitda
    render_as: metric_row
```

### Stock Drop Analysis via Composites (Locked — applies to all sections)
- Every 5%+ stock drop gets a full narrative: what caused it, whether peers dropped too, whether it recovered, whether news preceded it, whether insiders sold before it
- Drops are grouped by pattern type: earnings-related, litigation-related, sector-wide, company-specific
- Each pattern group gets a narrative summary with individual events listed underneath
- This is BOTH per-event detail AND grouped-by-pattern view
- Peer/industry attribution is mandatory
- All of this analysis happens in the COMPOSITE, not in the facet or template

### All Sections Same Standard (Locked)
- Every facet gets composites that provide the same depth of analysis
- Governance: composite grouping board independence + committee structure + tenure patterns
- Financial: composite grouping liquidity + debt + going concern signals
- Litigation: composite grouping active cases + SEC enforcement + settlement history
- Market: composite grouping stock drops + short interest + insider trading + analyst sentiment
- Executive: composite grouping compensation + turnover + related party transactions
- This is ambitious — planner should prioritize composites by analytical value

### QA Health Summary (Locked)
- Post-analyze health summary is CLI output only (not in HTML worksheet)
- Rich terminal output showing: evaluated/TRIGGERED/SKIPPED counts, anomaly warnings
- Anomaly examples: 0 TRIGGERED when litigation data is present, all signals SKIPPED in a section

### Claude's Discretion
- Composite schema design (Pydantic models, YAML structure, evaluation engine)
- How composites are registered and discovered (directory convention, registry, etc.)
- CompositeResult schema (how conclusions are structured)
- How facet YAML evolves to reference composites vs individual signals
- Implementation of `brain delta` storage and comparison strategy
- Implementation of `brain audit` staleness/coverage/conflict detection
- Wave ordering (composites foundation before or alongside QA commands)
- How to handle the `red_flags` facet (currently has empty signals list, sourced from scoring)
- Which composites to implement first (prioritize by analytical value)

</decisions>

<specifics>
## Specific Ideas

### Signal Details Field
```python
class SignalResult:
    # ... existing fields ...
    details: dict[str, Any] = {}  # Structured evaluation data for composites to read
```

### Composite Definition (Brain Layer)
```yaml
# brain/composites/stock_drop_analysis.yaml
id: COMP.STOCK.drop_analysis
name: Stock Drop Analysis
member_signals:
  - STOCK.PRICE.single_day_events
  - STOCK.PRICE.attribution
  - STOCK.PATTERN.peer_divergence
  - STOCK.PATTERN.event_collapse
  - STOCK.PRICE.recovery
  - STOCK.INSIDER.cluster_timing
```

### Composite Result (Brain Layer)
```python
class CompositeResult:
    composite_id: str
    member_results: dict[str, SignalResult]  # signal_id -> result
    conclusion: dict[str, Any]  # structured analytical conclusion
    narrative: str  # one-paragraph summary
    severity: str  # RED / YELLOW / CLEAR (composite-level)
```

### Facet Content Declaration (Display Layer)
```yaml
# brain/facets/market_activity.yaml (evolved)
id: market_activity
name: Market Activity
display_type: hybrid
content:
  - ref: COMP.STOCK.drop_analysis
    render_as: narrative_with_table
  - ref: COMP.STOCK.short_analysis
    render_as: metric_with_alerts
  - ref: COMP.STOCK.insider_analysis
    render_as: detail_table
  # Standalone signals not in any composite
  - ref: STOCK.VALUATION.pe_ratio
    render_as: metric_row
```

### Existing chain_roles (Reference, NOT the same as composites)
Chains describe causal relationships between signals (e.g., stock_drop → securities class action). These are about risk propagation. Composites are about analytical grouping. A composite might contain signals from multiple chains, and a chain might span multiple composites.

### Current Two-Track Problem (Reference)
- `market.html.j2` has 305 lines of rich structured rendering from `mkt.*` state data
- Then 4 lines dumping all STOCK.* signals as a flat "Market Checks" table
- Composites solve this: the composite conclusion replaces BOTH tracks with a unified analytical view that the facet then renders

### Existing Infrastructure to Build On
- 8 facet YAMLs already defined with signal lists (need evolution to reference composites)
- `FacetSpec` Pydantic schema with display_type and display_config
- `chain_roles` on signals hint at composite membership
- `brain_signal_runs` table has 36,946 rows for delta/health
- `brain_effectiveness` module computes fire rates
- `qa_report.py` post-pipeline verification hook

### Peril ID Gap (Known)
- All 380 active signals have NULL peril_id — `brain audit` will report this honestly

</specifics>

<deferred>
## Deferred Ideas

- ML-based threshold optimization (need 50+ companies first)
- Cross-company correlation engine (need 10+ companies)
- Interactive feedback mode (Phase 51 FEED-01)
- Web UI dashboard (out of scope — CLI is the surface)
- Composite-level chain analysis (chain_roles inform risk propagation paths — future phase)

</deferred>

---

*Phase: 50-automated-qa-anomaly-detection*
*Context gathered: 2026-02-26 via interactive discussion*
*Updated: 2026-02-26 — Signal Composites architecture correction (analysis ≠ display)*
