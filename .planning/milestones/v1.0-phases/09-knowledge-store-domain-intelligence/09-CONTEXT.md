# Phase 9: Knowledge Store & Domain Intelligence -- Context

## Phase Goal

Migrate the system's domain knowledge from flat JSON config files to a queryable knowledge store with check lifecycle management, provenance tracking, learning infrastructure, industry-specialized playbooks, and document ingestion -- so knowledge evolves reliably, the system gets smarter over time, and underwriting ideas flow naturally from observation to production check.

## Current Knowledge Architecture

### Two-Tier Knowledge System

**Brain Directory** (`src/do_uw/brain/`) -- 5 files, ~295KB total:
- `checks.json` (198KB) -- 359 D&O checks with execution rules, thresholds, data locations
- `scoring.json` (35KB) -- 10-factor scoring weights, tier boundaries, probability ceilings, tower positions
- `patterns.json` (46KB) -- 19 composite risk patterns with trigger conditions and severity modifiers
- `red_flags.json` (7KB) -- 11 critical red flag escalation triggers with quality score ceilings
- `sectors.json` (9KB) -- Sector baselines for short interest, volatility, leverage, claim rates, filing multipliers

**Config Directory** (`src/do_uw/config/`) -- 8 files, ~28KB total:
- `xbrl_concepts.json` (17KB) -- 50 canonical financial concepts mapped to XBRL taxonomy
- `industry_theories.json` (4KB) -- Industry-specific legal theories for 8 SIC code ranges
- `claim_types.json` (2.2KB) -- 9 claim types with SOL/repose periods
- `adverse_events.json` (624B) -- Severity weights for 16 adverse event types
- `activist_investors.json` (620B) -- 23 known activist investor names
- `governance_weights.json` (585B) -- Governance scoring weights and thresholds
- `lead_counsel_tiers.json` (531B) -- Plaintiff firm tier classifications
- `tax_havens.json` (2.5KB) -- 34 tax haven jurisdictions

### Config Loading Patterns

**Centralized (brain/)**: `ConfigLoader` in `src/do_uw/config/loader.py` (319 lines) loads all 5 brain files, returns validated `BrainConfig` Pydantic model. Consumed by ANALYZE, SCORE, BENCHMARK stages.

**Decentralized (config/)**: Each EXTRACT extractor loads its own config file independently via `Path(__file__).parent / "filename.json"` pattern. 8 files, each with exactly 1 consumer.

### Stage Boundaries

| Stage | Brain (5 files) | Config (8 files) |
|-------|-----------------|-------------------|
| EXTRACT | -- | All 8 files |
| ANALYZE | checks.json | -- |
| SCORE | All 5 files | -- |
| BENCHMARK | All 5 files | -- |
| RENDER | -- | -- |

### Existing Cache Infrastructure

- **SQLite** (`cache/sqlite_cache.py`, 205 lines): Key-value store with TTL, JSON values, ~35 entries. Used for API response caching.
- **DuckDB** (`.cache/analysis.duckdb`): Exists but empty. Available as potential knowledge store backend.

## Key Design Constraints

1. **Zero regression**: All 1090 existing tests must continue to pass after migration
2. **500-line limit**: All source files under 500 lines
3. **Pyright strict**: Full type safety required
4. **Gradual migration**: Can't break consumers during transition -- need adapter/compatibility layer
5. **brain/ vs config/ distinction**: Brain = domain knowledge (scoring logic), Config = technical mappings (XBRL concepts). Phase 9 primarily targets brain/ files; config/ files may or may not migrate.

## User Requirements (from discussion)

### Industry-Specialized Playbooks
- Deep per-vertical expertise, not generic checks
- Each industry gets its own tailored checks, risk patterns, claim theories, underwriting questions
- Auto-activated by SIC/NAICS during RESOLVE
- At least 5 high-priority verticals: Technology/SaaS, Biotech/Pharma, Financial Services, Energy/Utilities, Healthcare
- Stored in knowledge store alongside generic checks
- Applied per-company based on industry classification

### AI Transformation Risk (Phase 13, but knowledge store prepares the infrastructure)
- Separate scoring dimension from the 10-factor composite
- Industry-specific AI impact models
- Knowledge store must support rapidly-evolving knowledge (more frequent updates than traditional risk factors)

## Success Criteria (from ROADMAP.md)

1. All 359+ checks with provenance metadata (origin, validation status, dates, history)
2. Queryable by: sector, factor, section, severity, status, allegation theory, free-text search
3. Check traceability: data source deps → evaluation logic → output mapping → scoring impact
4. Check lifecycle: INCUBATING → DEVELOPING → ACTIVE → DEPRECATED
5. Underwriting notes with full-text search
6. Version history preserved on modifications
7. Learning infrastructure: outcome tracking, effectiveness metrics, redundancy analysis
8. Narrative composition: checks grouped into risk stories
9. Document ingestion: external documents → knowledge artifacts
10. Scoring engine reads from knowledge store (zero regression)
11. Industry playbooks for 5+ high-priority verticals
12. Playbooks auto-activated by SIC/NAICS

## Related Requirements

No formal requirements from REQUIREMENTS.md -- this is a new capability. But it serves:
- All existing SECT* requirements (better knowledge = better analysis)
- Future Phase 13 (AI Transformation) depends on knowledge store infrastructure

## Technical Decisions Needed

1. **Storage backend**: DuckDB (already installed, analytical), SQLite (already used, simpler), or both?
2. **Schema design**: Relational tables vs document store vs hybrid?
3. **Migration strategy**: Big bang vs gradual (adapter pattern)?
4. **Query API**: Direct SQL vs Python ORM vs domain-specific API?
5. **Industry playbook format**: Same schema as checks? Separate tables? Inheritance model?
6. **Document ingestion**: NLP-based extraction? Template-based? AI-assisted?
7. **Full-text search**: SQLite FTS5? DuckDB full-text? Dedicated search library?
