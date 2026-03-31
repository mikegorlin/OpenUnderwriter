# Design Decisions Record

This document tracks the major design, architecture, and UX decisions made across all 16 phases
of the D&O Underwriting Worksheet System. Each entry explains what was decided, why, what was
rejected, and which phase originated the decision.

For detailed phase-by-phase summaries, see `.planning/phases/*/SUMMARY.md` files.

---

## 1. Architecture

### Single Pydantic AnalysisState as sole source of truth

- **Decision**: One `AnalysisState` Pydantic model holds all pipeline state. No competing state representations.
- **Rationale**: The predecessor system had 7+ state files and representations, leading to drift and contradictions. A single model guarantees consistency -- every stage reads and writes the same object.
- **Rejected**: Multiple domain-specific state files, event-sourced state, raw dict passing between stages.
- **Phase**: 1

### 7-stage pipeline (RESOLVE -> ACQUIRE -> EXTRACT -> ANALYZE -> SCORE -> BENCHMARK -> RENDER)

- **Decision**: Linear pipeline with strict stage boundaries. Each stage has a single responsibility.
- **Rationale**: Maps directly to the underwriting workflow. Clear data flow prevents the predecessor's problem of mixing acquisition with analysis (3 generations of data code).
- **Rejected**: Monolithic processing (predecessor's 9,445-line `generate_referral.py`), DAG-based execution, event-driven architecture.
- **Phase**: 1

### MCP boundary: tools only in ACQUIRE stage

- **Decision**: MCP tools (EdgarTools, Brave Search, Playwright, Fetch) are used exclusively in ACQUIRE. Subagents cannot access MCP tools. EXTRACT and later stages operate on local data only.
- **Rationale**: Keeps external I/O confined to one stage. Makes EXTRACT through RENDER deterministic and testable without network access.
- **Phase**: 1

### Synchronous rate limiter

- **Decision**: `time.sleep` + `threading.Lock` for rate limiting, not async.
- **Rationale**: The pipeline is inherently sequential (each stage depends on the previous). Async would add complexity with no throughput benefit for a single-ticker analysis.
- **Rejected**: `aiolimiter`, `asyncio`-based rate limiting.
- **Phase**: 2

### SEC REST API primary, MCP integration deferred

- **Decision**: Direct SEC EDGAR REST API calls as primary data source. MCP `edgartools` server available but not the primary path.
- **Rationale**: REST API is simpler, more predictable, and easier to test. MCP adds a layer of indirection that can be adopted later without architectural change.
- **Phase**: 2

### No source file over 500 lines

- **Decision**: Hard limit of 500 lines per source file. Split before reaching the limit.
- **Rationale**: Anti-context-rot rule from CLAUDE.md. Keeps files comprehensible in a single read. The predecessor had a 9,445-line monolith. Over 30 splits were performed across Phases 3-14.
- **Rejected**: Soft guidelines, per-module limits, no limit.
- **Phase**: 1 (enforced across all phases)

### Config-driven thresholds in JSON files

- **Decision**: All scoring weights, thresholds, patterns, and classification boundaries live in JSON files under `config/`. No hardcoded thresholds in source code.
- **Rationale**: The predecessor had thresholds in both code AND config, causing contradictions. JSON files are human-readable, diffable, and modifiable without code changes.
- **Rejected**: YAML config, environment variables, database-stored config.
- **Phase**: 1

### Pipeline config passthrough

- **Decision**: A `pipeline_config: dict` flows from CLI through Pipeline to each stage.
- **Rationale**: Allows runtime configuration (output paths, feature flags, verbosity) without modifying stage constructors or global state.
- **Phase**: 3

### Full-document-once pattern

- **Decision**: ACQUIRE downloads full SEC filings once. EXTRACT parses sections locally. No re-fetching.
- **Rationale**: Minimizes SEC API calls (rate-limited), ensures consistent data across extractors, and allows offline re-extraction.
- **Phase**: 4

### SQLAlchemy 2.0 + Alembic + SQLite FTS5 for knowledge store

- **Decision**: SQLAlchemy 2.0 with `Mapped[]` annotations, Alembic migrations, and SQLite FTS5 for full-text search. Standalone FTS5 tables (not content-synced) with rebuild-on-search.
- **Rationale**: Type-safe ORM satisfies pyright strict. SQLite is zero-config and portable. FTS5 provides search without external dependencies. Standalone tables avoid FTS5 content-sync bugs.
- **Rejected**: DuckDB for knowledge (used only for cache), Elasticsearch, raw SQL.
- **Phase**: 9

---

## 2. Visual Design and Branding

### Color scheme: navy and gold

- **Decision**: Primary: #1A1446 (navy). Accent: #FFD000 (gold). These are the two brand colors used throughout Word documents, PDF output, and the dashboard.
- **Rationale**: Professional insurance industry aesthetic. High contrast for readability. Consistent with Liberty Mutual branding guidelines.
- **Phase**: 8, refined in 16

### No green in risk spectrum

- **Decision**: Risk visualization uses red (deteriorating), amber (caution), and blue (improving). Green is explicitly excluded.
- **Rationale**: In D&O underwriting, nothing is "safe." Green implies safety and could lead to underwriter complacency. Blue signals improvement without implying absence of risk.
- **Rejected**: Traditional red/amber/green traffic light system.
- **Phase**: 8

### Conditional formatting thresholds

- **Decision**: Less than 1% change: no color. 1-10%: amber. 10%+ deteriorating: red. 10%+ improving: blue. Applied to 48 financial metrics with explicit direction mapping.
- **Rationale**: Small fluctuations are noise. The 1% floor prevents visual clutter. The 10% threshold highlights material changes. Direction mapping ensures "debt up" is red while "revenue up" is blue.
- **Phase**: 8

### Typography: Georgia, Calibri, Consolas

- **Decision**: Georgia for headings (serif, authoritative). Calibri for body text (sans-serif, readable). Consolas for citations and data references (monospace, precise).
- **Rationale**: Standard professional document typography. All fonts available on Windows and macOS without installation.
- **Phase**: 8

### Stock chart annotations

- **Decision**: Single-day drops of 8%+ shown as red triangles. Multi-day declines of 15%+ shown as orange shaded bands. Threshold of 5%+ total for inclusion in legend count.
- **Rationale**: These thresholds align with securities litigation significance (8% single-day is typical SCA filing trigger, 15% multi-day is common corrective disclosure pattern).
- **Phase**: 8

---

## 3. Data Integrity

### Every data point carries source and confidence

- **Decision**: All data points in the state model include `source` (specific filing type + date + URL/CIK) and `confidence` (HIGH/MEDIUM/LOW). Implemented via the `SourcedValue[T]` generic pattern.
- **Rationale**: Underwriting decisions require knowing data provenance. HIGH = audited/official, MEDIUM = unaudited/estimates, LOW = derived/web. This is non-negotiable per CLAUDE.md.
- **Rejected**: Implicit trust of data sources, per-section confidence, binary trusted/untrusted.
- **Phase**: 1, implemented in 3

### Never generate or guess financial data

- **Decision**: If a data source fails or data is unavailable, display "Not Available" rather than generating, estimating, or interpolating values.
- **Rationale**: Fabricated financial data in an underwriting worksheet is a professional liability risk. Missing data is always preferable to wrong data.
- **Phase**: 1

### Cross-validation requirement

- **Decision**: Web-sourced data requires corroboration from 2+ independent sources. Single-source findings are flagged as LOW confidence.
- **Rationale**: Web data is noisy and unreliable. Cross-validation catches false positives. The flag ensures underwriters know when they are relying on thin evidence.
- **Phase**: 2

### Blind spot detection as first-class acquisition

- **Decision**: Broad web search runs at the START of ACQUIRE, not as a fallback after structured APIs. Proactive discovery searches for company + risk terms, executive names + litigation terms.
- **Rationale**: Structured APIs (SEC EDGAR, yfinance) systematically miss: short seller reports, state AG actions, employee lawsuits, social media controversies, early news. Missing these entirely is worse than flagging them at LOW confidence.
- **Phase**: 2

### Data source fallback chains

- **Decision**: Each data category has a defined fallback chain (e.g., SEC: EdgarTools MCP -> SEC REST API -> web search). If a source fails, fall through to next tier. Never treat "no data" as "no issue."
- **Rationale**: Resilience against API outages or rate limits. The fallback chain ensures maximum data coverage while maintaining confidence tagging.
- **Phase**: 2

---

## 4. Scoring and Analysis

### 10-factor composite scoring model

- **Decision**: Ten orthogonal risk factors with config-driven weights and max points. Factors cover financial distress, market signals, governance, litigation, regulatory, and more.
- **Rationale**: Comprehensive coverage of D&O risk dimensions. Config-driven weights allow calibration without code changes. The predecessor had 4 competing scoring definitions.
- **Rejected**: Single composite score, 5-factor simplified model, ML-based scoring.
- **Phase**: 6

### 11 Critical Red Flag gates

- **Decision**: Eleven binary checks (e.g., active SEC enforcement, restatement, going concern) that impose score ceilings regardless of factor scores. CRF-triggered means tier cannot exceed a ceiling.
- **Rationale**: Some risks are so severe that no amount of positive signals should override them. A company under SEC investigation should never be rated WIN regardless of financial health.
- **Phase**: 6

### Theory-to-factor mapping

- **Decision**: Securities litigation theories mapped to scoring factors: A(Section 10b/Rule 10b-5)=[F1,F3,F5], B(Section 11)=[F2,F5], C(Section 14)=[F7,F8], D(Derivative/Breach)=[F9,F10], E(SOX/Whistleblower)=[F4].
- **Rationale**: Creates a causal link between scoring output and insurance coverage exposure. Enables "which theory is most likely and at what severity" analysis.
- **Phase**: 6

### Tier classification system

- **Decision**: Six tiers: WIN, WANT, WRITE, WATCH, WALK, NO_TOUCH. Derived from composite score with band-based ordering (not strict pairwise).
- **Rationale**: Maps to underwriting appetite levels. Band-based ordering acknowledges that companies scoring 84 vs 85 are effectively equivalent (noise), while 84 vs 60 is meaningfully different.
- **Rejected**: Numeric-only scoring, A/B/C/D/F letter grades, percentile ranking.
- **Phase**: 6, refined in 15

### Multiplicative inherent risk

- **Decision**: `inherent_risk = base_rate * cap_multiplier * score_multiplier`. Base rates calibrated per sector from Cornerstone/NERA/Stanford SCAC data.
- **Rationale**: Multiplicative composition reflects how risk factors compound. A company with high base rate AND high score multiplier is exponentially riskier, not additively.
- **Phase**: 7, calibrated in 15

### 17 composite risk patterns

- **Decision**: Named multi-signal patterns (EVENT_COLLAPSE, DEATH_SPIRAL, GOVERNANCE_BREAKDOWN, etc.) detected via majority-trigger threshold (>50% of constituent signals present).
- **Rationale**: Individual signals can be noise. Patterns of co-occurring signals are diagnostic. The >50% threshold balances sensitivity with false-positive control.
- **Phase**: 6

---

## 5. Rendering

### Word (.docx) as primary output

- **Decision**: Word document is the primary deliverable. PDF and Markdown are secondary outputs generated from the same data.
- **Rationale**: Underwriters need editable documents. Word is the industry standard for insurance document workflows. PDF provides a fixed-layout alternative. Markdown enables version control.
- **Rejected**: PDF-first, HTML-first, LaTeX.
- **Phase**: 8

### Section renderer dispatch via importlib

- **Decision**: Each worksheet section (1-8) is rendered by a module loaded via `importlib.import_module` with `None` fallback for not-yet-implemented sections.
- **Rationale**: Allows incremental section development across phases. New sections are added by creating a module; no registration code needed. None fallback prevents crashes during development.
- **Phase**: 8

### Radar chart risk fractions

- **Decision**: Radar chart displays risk as fractions (points_deducted / max_points, 0-1 scale) rather than raw point deductions.
- **Rationale**: Normalizes across factors with different max_points. A factor with 15/20 points deducted and one with 8/10 are both 0.75 risk -- directly comparable on the radar.
- **Phase**: 8

### Meeting prep question categories

- **Decision**: Four categories of generated questions: CLARIFICATION (ambiguous data), FORWARD_INDICATOR (future risk signals), GAP_FILLER (missing data), CREDIBILITY_TEST (verify management claims).
- **Rationale**: Structured question generation ensures underwriters prepare for the right conversations. Priority-ranked based on state analysis findings.
- **Phase**: 8

### PDF optional via WeasyPrint

- **Decision**: PDF generation depends on WeasyPrint (optional dependency). If unavailable, PDF is skipped. Markdown always generated via Jinja2.
- **Rationale**: WeasyPrint has complex system dependencies (Cairo, Pango). Making it optional prevents installation friction for users who only need Word output.
- **Phase**: 8

---

## 6. Dashboard

### FastAPI + htmx + DaisyUI CDN (no build step)

- **Decision**: Dashboard uses FastAPI (Python), htmx for interactivity, Plotly.js for charts, and DaisyUI/Tailwind via CDN. No Node.js, no webpack, no build step.
- **Rationale**: Keeps the entire project in Python. CDN-based UI libraries mean zero frontend build tooling. htmx provides SPA-like interactivity with server-rendered HTML fragments.
- **Rejected**: React/Next.js, Streamlit, Dash, full SPA architecture.
- **Phase**: 11

### Read-only view with hot-reload

- **Decision**: Dashboard reads AnalysisState as read-only. Detects file modification time changes and hot-reloads data. No write operations.
- **Rationale**: The dashboard is a viewer, not an editor. Read-only eliminates race conditions with the CLI pipeline. Hot-reload lets underwriters see updates as analysis progresses.
- **Phase**: 11

### Chart API pattern

- **Decision**: Charts served via `GET /api/chart/{name}` returning JSON. Client-side Plotly.js renders from the JSON response. `empty_figure()` returned for missing data.
- **Rationale**: Server computes chart data (access to full state), client renders (smooth interactivity). Empty figures prevent broken chart containers when data is incomplete.
- **Phase**: 11

---

## 7. Knowledge System

### Check lifecycle: INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED

- **Decision**: Underwriting checks follow a four-stage lifecycle. New checks from document ingestion start as INCUBATING. Checks must be promoted through stages before affecting scoring.
- **Rationale**: Prevents untested or poorly-defined checks from immediately affecting underwriting scores. The lifecycle provides a review gate.
- **Phase**: 9

### BackwardCompatLoader as drop-in ConfigLoader replacement

- **Decision**: `BackwardCompatLoader` replaces `ConfigLoader` with identical API. Default constructor auto-migrates brain/ JSON to in-memory SQLite store.
- **Rationale**: Zero-regression migration from file-based config to database-backed knowledge. Existing code (3 brain-consuming stages) works without modification.
- **Rejected**: Big-bang migration requiring all consumers to update simultaneously.
- **Phase**: 9

### Industry playbooks auto-activated by SIC/NAICS

- **Decision**: 10 industry verticals (Tech/SaaS, Biotech/Pharma, Financial Services, Energy/Utilities, Healthcare, CPG, Media, Manufacturing, REITs, Transportation) with playbooks auto-activated during RESOLVE based on SIC/NAICS code.
- **Rationale**: Different industries have fundamentally different D&O risk profiles. Auto-activation means no manual playbook selection. SIC/NAICS provides standardized classification.
- **Phase**: 9, expanded in 14

### PricingStore shares SQLite with KnowledgeStore

- **Decision**: Both stores use the same SQLite database file (`knowledge.db`) via a shared SQLAlchemy Base class.
- **Rationale**: Single database simplifies deployment and backup. Cross-store queries possible if needed. Alembic manages migrations for both.
- **Phase**: 10

### Document ingestion: rule-based extraction v1

- **Decision**: Rule-based text extraction with regex patterns (RISK:, CHECK:, NOTE:, headers, numbered lists). Pluggable `extraction_fn` parameter for future LLM-based extraction.
- **Rationale**: Rule-based extraction is deterministic and testable. The pluggable interface ensures LLM-based extraction can be swapped in without architectural changes.
- **Rejected**: LLM-based extraction as v1 (non-deterministic, harder to test, higher cost).
- **Phase**: 9

---

## 8. Actuarial Pricing

### ILF power curve for layer pricing

- **Decision**: Increased Limit Factor power curve for pricing excess layers. Alpha exponent configurable per layer in `actuarial.json`.
- **Rationale**: Industry-standard actuarial methodology. Power curves naturally capture the decreasing loss probability at higher attachment points.
- **Phase**: 12

### Credibility weighting for market calibration

- **Decision**: Credibility-weighted blend of model output and market data. Weight determined by market data completeness and recency.
- **Rationale**: Pure model output may diverge from market reality. Pure market data may be stale or unrepresentative. Blending balances actuarial rigor with market awareness.
- **Phase**: 12

### All actuarial parameters in actuarial.json

- **Decision**: Every actuarial parameter (base rates, ILF alphas, defense cost percentages, credibility thresholds) lives in `actuarial.json`. None hardcoded.
- **Rationale**: Actuaries need to adjust parameters without touching code. Consistent with the project-wide config-driven philosophy.
- **Phase**: 12

### Model output labeled as indicated, not prescriptive

- **Decision**: Pricing model output is explicitly labeled as "indicated" pricing -- a data point for the underwriter, not a binding recommendation.
- **Rationale**: Regulatory and professional liability concern. Prescriptive pricing from automated models could create E&O exposure. "Indicated" framing preserves underwriter judgment.
- **Phase**: 12

---

## 9. AI Transformation Risk Factor

### Independent dimension, not part of 10-factor composite

- **Decision**: AI risk is scored separately from the 10-factor composite model. It appears as Section 8 in the worksheet and as its own dashboard card.
- **Rationale**: AI transformation risk is orthogonal to traditional D&O factors. Folding it into the composite would dilute both the AI signal and the established factor model. Independent display lets underwriters weight it based on their own judgment.
- **Rejected**: Adding as Factor 11, embedding in existing factors (F1 financial impact, F4 regulatory).
- **Phase**: 13

### Threat-level baseline prior

- **Decision**: Industry-level AI threat classification (HIGH/MEDIUM/LOW) sets a baseline score (7/5/3 on 0-10 scale). Extraction evidence adjusts from the baseline.
- **Rationale**: Even without company-specific evidence, industry-level AI exposure is known. A media company faces HIGH disruption regardless of whether its 10-K mentions AI. Evidence then refines up or down.
- **Phase**: 13

### Multi-signal assessment

- **Decision**: AI risk assessed via patent filings (USPTO), 10-K disclosure analysis, news sentiment, and competitive position. Multiple signals triangulated.
- **Rationale**: No single signal reliably captures AI transformation risk. Patents show investment, disclosures show awareness, sentiment shows market perception, competitive position shows relative preparedness.
- **Phase**: 13

---

## 10. Pyright Strict Compliance Patterns

These patterns emerged from enforcing `pyright strict` mode across a codebase that depends on
several untyped or partially-typed third-party libraries.

### yfinance: type-ignore + cast

- **Decision**: `import yfinance  # type: ignore[import-untyped]` at import, `cast()` for return values. Local imports for isolation and mocking.
- **Rationale**: yfinance has no type stubs. Suppressing at import and casting at use provides type safety for downstream code while acknowledging the untyped boundary.
- **Phase**: 2

### python-docx: Any-typed API surface

- **Decision**: All python-docx objects (Document, styles, paragraphs, runs) typed as `Any`. Helper `_oxml()` wraps `OxmlElement` with `cast(Any)`.
- **Rationale**: python-docx is deeply untyped. Attempting granular typing would require hundreds of type-ignores. Accepting `Any` at the library boundary keeps the rest of the rendering code clean.
- **Phase**: 8

### Plotly: figures typed as Any

- **Decision**: `import plotly.graph_objects as go  # type: ignore[import-untyped]`. All figure objects typed as `Any` throughout.
- **Rationale**: Plotly is untyped. Dashboard chart builders return figures consumed by `fig.to_dict()` which is also untyped. Any-typing at this boundary is the pragmatic choice.
- **Phase**: 11

### FastAPI/Jinja2: template workaround

- **Decision**: `_templates: Any = templates` assignment for Jinja2Templates environment. `# type: ignore[attr-defined]` for `app.state` access.
- **Rationale**: Starlette's Jinja2Templates type is partially unknown to pyright. The `Any` alias provides type safety for template rendering calls while suppressing the partially-unknown propagation.
- **Phase**: 11

### Closures over lambdas for typed callbacks

- **Decision**: Use named closure functions instead of lambdas for callback fields in dataclasses and Pydantic models. Use `lambda: []` specifically for Pydantic list `default_factory`.
- **Rationale**: Pyright infers lambda return types as `Unknown` in some contexts (dataclass fields, `acquire_fn` parameters). Named closures get proper type inference. The `lambda: []` pattern is a known workaround for Pydantic's `default_factory` expecting a callable.
- **Phase**: 2 (discovered), applied across all phases
