# Brain Architecture Research

**Researched:** 2026-02-15
**Purpose:** Architectural patterns for a knowledge-driven assessment system that remains readable, maintainable, and self-improving
**Audience:** System architects building a D&O underwriting brain

---

## 1. Knowledge Representation Options

### The Landscape

Five major patterns exist for representing domain knowledge in assessment systems. Each trades off readability, flexibility, and computational power differently.

#### A. Structured Configuration (JSON/YAML with Schema)

**What it is:** Domain knowledge lives in structured data files (JSON, YAML, TOML) validated by a formal schema. The schema defines what fields exist, what values are legal, and how elements relate.

**How it works in practice:**
```yaml
# Risk question (readable by underwriter)
question: "Does the company show signs of financial distress?"
# Evaluation criteria (machine-executable)
signals:
  - field: altman_z_score
    red: "< 1.81"
    yellow: "1.81 - 2.99"
    clear: "> 2.99"
  - field: current_ratio
    red: "< 1.0"
    yellow: "1.0 - 1.5"
    clear: "> 1.5"
```

**Pros:**
- Native to Python ecosystem (Pydantic validates JSON/YAML natively)
- Version-controllable in git (diff-friendly)
- Schema IS the documentation -- Pydantic generates JSON Schema automatically
- No new runtime dependency -- just data files + validation
- Underwriters can read YAML/JSON with minimal training
- Already proven in our system (388 checks in checks.json)

**Cons:**
- Complex conditional logic ("if X AND Y but not Z") gets awkward in flat config
- No built-in inference or chaining
- Schema evolution requires migration code
- Large files become hard to navigate (our checks.json is already unwieldy at 388 entries)

**Best for:** Systems where rules are mostly independent threshold checks with limited cross-rule dependencies. This is us.

#### B. Rule Engine (Drools, OPA, Clara)

**What it is:** A dedicated engine that evaluates rules using forward-chaining (data triggers rules) or backward-chaining (goals drive rule selection). Rules are written in a domain-specific language.

**How it works in practice (OPA/Rego style):**
```rego
financial_distress_risk = "RED" {
    input.altman_z_score < 1.81
    input.debt_to_equity > 3.0
}
financial_distress_risk = "YELLOW" {
    input.altman_z_score < 2.99
    input.current_ratio < 1.5
}
```

**Pros:**
- Purpose-built for rule evaluation -- handles AND/OR/NOT natively
- Supports chaining (one rule's output feeds another's input)
- Formal rule languages (Rego, DRL) are well-documented standards
- Separation of rule authoring from rule execution is clean

**Cons:**
- Martin Fowler's warning: "It was easy to set up a rules system, but very hard to maintain it because nobody can understand this implicit program flow." Chaining "can easily end up being very hard to reason about and debug."
- New DSL = new learning curve for everyone (underwriters AND developers)
- OPA is Go-native (FFI overhead from Python), Drools is Java-native
- Overkill for independent threshold checks that don't chain
- Fowler recommends: if you need one, "build a limited rules engine that's only designed to work within that narrow context" rather than adopting a general-purpose product

**Best for:** Systems with complex inter-rule dependencies, frequent rule additions by non-programmers, and hundreds of interacting conditions.

#### C. Decision Tables (DMN Standard)

**What it is:** Rules expressed as tables where rows are conditions and columns are outcomes. The DMN (Decision Model and Notation) standard from OMG formalizes this.

**How it works in practice:**
```
| Altman Z | Current Ratio | Debt/Equity | -> Risk Level |
|----------|---------------|-------------|---------------|
| < 1.81   | < 1.0         | > 3.0       | RED           |
| < 1.81   | >= 1.0        | any         | YELLOW        |
| < 2.99   | < 1.5         | > 2.0       | YELLOW        |
| >= 2.99  | >= 1.5        | <= 2.0      | CLEAR         |
```

**Pros:**
- Extremely readable by non-technical users -- it's a table
- DMN is an industry standard with tooling (Drools supports it, OpenRules supports it)
- Complete enumeration forces you to handle every combination
- Natural fit for multi-condition evaluations

**Cons:**
- Combinatorial explosion: 5 conditions x 3 states each = 243 rows
- Only works for discrete, bounded condition spaces
- Doesn't handle temporal patterns ("X happened within Y days of Z")
- Most DMN tooling is Java-ecosystem

**Best for:** Classification decisions with bounded conditions. Good for a subset of our checks (financial ratio evaluations) but not the whole brain.

#### D. Knowledge Graph / Ontology

**What it is:** Entities and relationships stored as triples (subject-predicate-object) in a graph database. Reasoning happens through graph traversal and inference rules.

**How it works in practice:**
```
Company --has_filing--> 10K_2025
10K_2025 --discloses--> MaterialWeakness
MaterialWeakness --indicates--> InternalControlRisk
InternalControlRisk --contributes_to--> GovernanceFactor(F3)
GovernanceFactor(F3) --weighted_at--> 0.15
```

**Pros:**
- Rich relationship modeling -- perfect for "how do these things connect?"
- Supports inference (transitive reasoning through the graph)
- Palantir Foundry uses an ontology layer as their core abstraction -- object types, properties, link types
- Natural for discovery queries ("what else is connected to this risk?")

**Cons:**
- Massive complexity overhead for what is fundamentally a scoring system
- Requires graph database infrastructure (Neo4j, RDF store)
- Underwriters cannot read SPARQL/Cypher queries
- Our checks are largely independent assessments, not interconnected inferences
- Ontology maintenance is a full-time job

**Best for:** Discovery systems where the relationships between entities ARE the value. Not a good fit for sequential assessment with independent checks.

#### E. Hybrid: Schema-Driven Config with Embedded Mini-Engine

**What it is:** The main knowledge base is structured config (JSON/YAML), but evaluation logic for complex checks is expressed in a constrained DSL embedded within the config. The DSL is purpose-built and minimal -- not a general-purpose language.

**How it works in practice:**
```yaml
id: FIN.DISTRESS.composite
question: "Is this company in financial distress?"
type: COMPOSITE
signals:
  - check: FIN.RATIO.altman_z
    weight: 0.4
  - check: FIN.RATIO.current
    weight: 0.2
  - check: FIN.DEBT.leverage
    weight: 0.2
  - check: FIN.CASH.burn_rate
    weight: 0.2
aggregation: weighted_worst  # RED if weighted score > threshold
threshold:
  red: 0.6   # 60%+ weight on RED signals
  yellow: 0.3
```

**Pros:**
- Structured config for 90% of checks (simple thresholds) -- stays readable
- Mini-engine handles the 10% that need composition (INFERENCE_PATTERN checks)
- No external dependencies -- the "engine" is a few hundred lines of Python
- Fowler-approved: "build a limited rules engine designed to work within that narrow context"
- Config is the documentation; Python is the engine
- Incremental: start with config, add engine features only when needed

**Cons:**
- Must design the mini-DSL carefully (scope creep risk)
- Two knowledge representations to maintain (config + engine code)
- Mini-engine becomes hard to test if it grows

**Best for:** Systems like ours with mostly independent checks plus a small number of composite/inference patterns. This is the recommended approach.

### Recommendation: Hybrid (Option E)

Our system has 305 EVALUATIVE_CHECK entries (simple threshold evaluations), 64 MANAGEMENT_DISPLAY entries (context data, no evaluation), and 19 INFERENCE_PATTERN entries (composite multi-signal checks). The overwhelming majority are independent threshold checks -- a full rule engine is overkill, but flat config alone can't express the composite patterns. A hybrid approach serves both needs.

---

## 2. Documentation-Code Sync

### The Core Problem

Our current system has knowledge in two places: `brain/checks.json` (388 checks, the "documentation") and Python code in `stages/analyze/` (the execution). These can and do drift apart. The check JSON says a field should be evaluated one way; the Python code actually evaluates it differently. Nobody knows which is right.

### Pattern 1: Schema IS the Documentation (Recommended)

**How it works:** The Pydantic model that validates check definitions IS the authoritative specification. The JSON Schema generated from that model IS the documentation. There is literally one source.

```python
class CheckDefinition(BaseModel):
    """A single underwriting check.

    Each check answers one question about the risk being assessed.
    The threshold defines what constitutes RED (concerning), YELLOW
    (watch), and CLEAR (acceptable) for this check.
    """
    id: str = Field(description="Unique check identifier, e.g. FIN.RATIO.current")
    question: str = Field(description="The risk question this check answers, in plain English")
    threshold: ThresholdSpec = Field(description="What values trigger RED/YELLOW/CLEAR")
    # ... etc
```

**What this gives you:**
- `CheckDefinition.model_json_schema()` generates a complete JSON Schema
- That schema can be rendered as HTML documentation automatically
- Pydantic validation ensures no check in the JSON violates the schema
- Adding a field to the model = adding it to the docs = adding it to validation
- Tools like `json-schema-for-humans` generate readable HTML from JSON Schema

**Key principle:** The Pydantic model is the single source of truth. The JSON data files are instances. The generated schema is the docs. Code that evaluates checks reads from the model. Nothing exists outside this chain.

### Pattern 2: Literate Configuration

**How it works:** Configuration files embed their own documentation using structured comments or adjacent markdown. The "woven" output is human-readable; the "tangled" output is machine-executable.

Martin Fowler's key insight on business-readable DSLs: "The sweet spot is in making DSLs business-readable rather than business-writable." Underwriters don't write checks -- developers do. But underwriters must be able to read them and confirm they make sense.

**Practical implementation:**
```yaml
# ============================================================
# FINANCIAL DISTRESS INDICATORS
# ============================================================
# These checks identify companies in or approaching financial
# distress, which dramatically increases D&O claim frequency.
#
# Distressed companies account for ~40% of SCA filings despite
# being <5% of public companies.
# ============================================================

- id: FIN.DISTRESS.altman_z
  question: "Is the Altman Z-Score in the distress zone?"
  # WHY THIS MATTERS: Companies with Z < 1.81 are 4x more
  # likely to face a securities class action within 24 months.
  # Source: Stanford SCA database analysis, 2020-2024
  threshold:
    red: "Z-Score < 1.81 (distress zone)"
    yellow: "Z-Score 1.81-2.99 (gray zone)"
    clear: "Z-Score > 2.99 (safe zone)"
```

**The key:** Each check has a `question` field (plain English), a WHY comment (domain rationale), and machine-readable thresholds. An underwriter reads the question and the WHY. The engine reads the thresholds.

### Pattern 3: Generated Documentation (Complement to Pattern 1)

**How it works:** A build step generates human-readable documentation FROM the authoritative source (the check definitions). This documentation is never hand-edited.

```
make docs  # Reads checks.json, generates:
           #   docs/brain/index.html       -- browsable check catalog
           #   docs/brain/by-factor.html   -- checks grouped by F1-F10
           #   docs/brain/by-question.html -- checks grouped by risk question
           #   docs/brain/coverage.html    -- what's covered, what's missing
```

**Benefits:**
- Documentation can never be stale (it's regenerated from source)
- Multiple views of the same data (by factor, by question, by data source)
- Coverage reports show gaps automatically
- CI/CD can block merges if documentation generation fails

### Pattern 4: Audit Trail (Required for Insurance)

**How it works:** Every change to the knowledge base is tracked with who, when, why, and what effect.

The EU AI Act requires that AI systems used in insurance underwriting maintain:
- Technical documentation of decision logic
- Human oversight with trained personnel who can override
- Record-keeping and logging of all decisions
- Explainability -- why a decision was made

**Practical implementation:**
- Check definitions live in git (full history)
- Every check evaluation logs: check_id, input_data, threshold_applied, result, timestamp
- Version field in check definitions tracks schema evolution
- `CheckRun` table (already exists from Phase 30) stores per-run results

### Recommended Combination

1. **Pydantic model as authoritative schema** (Pattern 1) -- the single source of truth
2. **Literate configuration** (Pattern 2) -- checks include plain-English questions and rationale
3. **Generated documentation** (Pattern 3) -- multiple views auto-generated from source
4. **Audit trail** (Pattern 4) -- git history + CheckRun logging

This combination ensures: a developer adds a check by editing the JSON and the Pydantic model validates it. The check includes a readable question and rationale. Documentation regenerates automatically. Every evaluation is logged.

---

## 3. Self-Improvement Mechanisms

### The Goal

A brain that learns: which checks actually predict claims, which checks never fire (and may be pointless), which threshold levels are well-calibrated, and where blind spots exist.

### Mechanism 1: Fire Rate Analysis

**What it is:** Track how often each check fires (produces RED or YELLOW) across all companies analyzed.

**Why it matters:**
- A check that NEVER fires may have a threshold set too conservatively -- or may be testing for something that doesn't occur in modern companies
- A check that ALWAYS fires may have a threshold set too aggressively -- or may be testing for something universal (not discriminating)
- The useful checks are those with intermediate fire rates that differentiate companies

**Implementation:**
```python
@dataclass
class CheckEffectiveness:
    check_id: str
    total_evaluations: int
    red_count: int
    yellow_count: int
    clear_count: int
    not_available_count: int
    fire_rate: float  # (red + yellow) / total
    discrimination_power: float  # entropy of result distribution
```

**Thresholds for action:**
- Fire rate = 0% over 20+ runs: investigate -- is the threshold unreachable?
- Fire rate > 80% over 20+ runs: investigate -- is the threshold too sensitive?
- Not-available rate > 50%: data acquisition gap -- the check can't get what it needs
- Low discrimination power (entropy < 0.3): check doesn't differentiate risk

### Mechanism 2: Calibration Analysis

**What it is:** Compare the risk level assigned by the brain to actual outcomes (claims filed, settlements paid, stock drops).

**Why it matters:** A RED flag that never leads to a claim is a false positive that wastes underwriter attention. A CLEAR assessment for a company that later faces a major claim is a dangerous miss.

**Implementation approach:**

The Brier Score is the standard metric for calibration of probabilistic predictions: the mean squared difference between predicted probability and observed outcome. However, for ordinal scoring (RED/YELLOW/CLEAR), we need an adapted approach:

```
For each check and each historical company:
  1. Record the check result (RED=1.0, YELLOW=0.5, CLEAR=0.0)
  2. Record the actual outcome (claim filed=1, no claim=0)
  3. Compute calibration: does RED actually predict claims?

Aggregate:
  - P(claim | RED flag on check X)
  - P(claim | YELLOW flag on check X)
  - P(claim | CLEAR on check X)

  If P(claim | RED) is not significantly > P(claim | CLEAR),
  the check is not calibrated and should be investigated.
```

**Key caveat:** This requires historical claims data mapped to specific companies and time periods. In D&O insurance, the feedback loop is long (claims can take years to materialize and years more to resolve). Short-term proxies:
- Securities class action filing within 24 months (from Stanford SCAC)
- Stock drop > 20% within 12 months
- SEC enforcement action within 24 months
- Restatement within 12 months

### Mechanism 3: Coverage Gap Detection

**What it is:** Automatically identify risk areas where the brain has no checks, or where checks exist but data acquisition doesn't support them.

**Implementation:**
```
Gap types:
1. NO_CHECK: Risk area identified in claims data but no check exists
   Example: crypto exposure risks emerged 2021-2023, no checks existed initially

2. CHECK_NO_DATA: Check exists but data pipeline can't populate it
   Example: 190 of 388 current checks are effectively placeholders

3. CHECK_NO_FIRE: Check exists and has data but threshold never triggers
   Example: threshold set for conditions that no longer occur

4. BLIND_SPOT: Claims occurred in area where brain had CLEAR assessment
   Example: company scored CLEAR on governance but had board capture issue
```

The existing `GapDetector` concept from Phase 32 research already addresses gap type 2. Mechanisms 1 and 3 extend this to cover types 3, 4, and 1 respectively.

### Mechanism 4: Backtesting Against Historical Data

**What it is:** Run the current brain against historical company data and compare results to known outcomes.

**Implementation approach:**
```
For each historical company-year in the database:
  1. Load the state snapshot from that period
  2. Run all checks against that snapshot
  3. Record results
  4. Compare to known outcomes (claim filed, settlement amount, etc.)

Metrics:
  - Sensitivity: of companies that had claims, what % did we flag?
  - Specificity: of companies that didn't have claims, what % did we clear?
  - Lift: how much better is the brain than random assignment?
  - Factor-level analysis: which of F1-F10 are most predictive?
```

**Data requirements:**
- Historical state files (exist for AAPL and TSLA from Phase 30)
- Claims database mapping (companies to claims, with dates and severity)
- At least 50+ company-years for statistical significance
- Both claim and no-claim examples (balanced dataset)

### Mechanism 5: A/B Testing of Rule Changes

**What it is:** When modifying a threshold or adding a check, run both old and new versions side-by-side and compare outputs.

**Implementation:**
```
brain_v1 = load_checks("checks_v9.json")
brain_v2 = load_checks("checks_v10_candidate.json")

for company in test_set:
    results_v1 = evaluate(brain_v1, company)
    results_v2 = evaluate(brain_v2, company)
    diff = compare(results_v1, results_v2)
    # Show: which companies changed, in what direction, by how much
```

This prevents "silent regression" -- changing a threshold that seems reasonable but actually degrades the brain's predictive power.

### Recommended Implementation Order

1. **Fire rate analysis** (easiest, highest immediate value -- shows which checks are dead weight)
2. **Coverage gap detection** (extends existing Phase 32 gap detector work)
3. **Backtesting infrastructure** (requires historical data, but the framework is reusable)
4. **Calibration analysis** (requires claims outcome data -- longest feedback loop)
5. **A/B testing** (most valuable once there's a cadence of brain updates)

---

## 4. Risk Assessment Architecture

### How the Best Systems Structure Hierarchical Scoring

#### FICO Model: The Gold Standard for Transparent Scoring

FICO scores are organized as a weighted hierarchy of five factors:

```
FICO Score (300-850)
├── Payment History (35%)
├── Credit Utilization / Amounts Owed (30%)
├── Length of Credit History (15%)
├── New Credit Inquiries (10%)
└── Credit Mix (10%)
```

Key architectural lessons:
1. **Small number of top-level factors** -- 5, not 50. Humans can reason about 5 things.
2. **Published weights** -- everyone knows payment history is 35%. Transparency builds trust.
3. **Each factor has sub-signals** -- but the user sees the factor, not the sub-signals.
4. **The composite score is a single number** -- 300-850. Easy to threshold for decisions.
5. **Factor-level explanations** -- "Your score is low because of high credit utilization."

#### Moody's Corporate Rating Methodology

Moody's uses scorecards with published weights:

```
Corporate Credit Rating
├── Scale and Diversification (20%)
│   ├── Revenue
│   └── Business diversification
├── Business Profile (20%)
│   ├── Market position
│   └── Operating environment
├── Profitability (10%)
│   ├── EBIT margin
│   └── Return on assets
├── Leverage and Coverage (30%)
│   ├── Debt/EBITDA
│   ├── EBIT/Interest
│   └── Free cash flow/Debt
└── Financial Policy (20%)
    ├── Management track record
    └── Governance quality
```

Key lessons:
1. **Scorecard approach** -- explicit mapping from metrics to sub-scores to composite
2. **Qualitative + quantitative** -- "Management track record" requires judgment; "Debt/EBITDA" is mechanical
3. **Published methodology** -- Moody's publishes 50+ page methodology documents explaining every factor
4. **Scorecard-indicated vs. actual** -- the scorecard gives a starting point; analyst judgment adjusts. This maps to our AUTO vs. MANUAL distinction.
5. **Sector-specific overlays** -- different industries get different factor weights

#### FAIR Framework: Decomposing Risk into Measurable Factors

The Factor Analysis of Information Risk (FAIR) framework decomposes risk into:

```
Risk ($)
├── Loss Event Frequency
│   ├── Threat Event Frequency
│   │   ├── Contact Frequency
│   │   └── Probability of Action
│   └── Vulnerability
│       ├── Threat Capability
│       └── Resistance Strength
└── Loss Magnitude
    ├── Primary Loss
    │   ├── Productivity Loss
    │   ├── Response Cost
    │   └── Replacement Cost
    └── Secondary Loss
        ├── Secondary Loss Event Frequency
        └── Secondary Loss Magnitude
```

Key lessons:
1. **Decomposition into orthogonal factors** -- each node in the tree represents one independent concept
2. **Quantitative at every level** -- FAIR insists on dollar amounts, not ordinal ratings
3. **Monte Carlo simulation** -- uncertainty is explicit (ranges, not point estimates)
4. **Complements other frameworks** -- FAIR provides the analysis engine; NIST/ISO provide the control catalog

### Mapping to Our D&O System

Our current 10-factor model (F1-F10) maps naturally to the FICO-like hierarchy:

```
D&O Risk Assessment
├── F1: Securities Class Action History (litigation track record)
├── F2: Financial Condition (distress, liquidity, solvency)
├── F3: Corporate Governance (board independence, controls, oversight)
├── F4: Industry Risk (sector-specific exposure patterns)
├── F5: Stock Volatility (market-based risk signals)
├── F6: Growth/Earnings (guidance dependency, miss risk)
├── F7: Insider Activity (trading patterns, alignment)
├── F8: M&A/Restructuring (event-driven risk)
├── F9: Regulatory/Compliance (enforcement, regulatory change)
└── F10: Emerging/Forward Risk (new threats, trend signals)
```

**Current problem:** Our checks are organized by DATA SOURCE prefix (BIZ, EXEC, FIN, GOV, LIT, NLP, STOCK, FWRD), not by RISK QUESTION. This means:
- A financial distress check is in FIN.*
- But the governance check that asks "does the audit committee have financial expertise?" is in GOV.*
- And the stock check for "is short interest elevated?" is in STOCK.*
- Yet all three inform the same risk question: "Is this company financially vulnerable?"

**The fix:** Reorganize from data-source prefixes to risk-question prefixes, or (better) add a `risk_question` field that groups checks across data sources into the questions they collectively answer.

### Risk Taxonomy Design Principles

From Open Risk Management's taxonomy guidance:

1. **MECE (Mutually Exclusive, Collectively Exhaustive):** Every risk belongs to exactly one category, and all categories together cover the entire risk universe. Our factor mapping (F1-F10) should satisfy this -- currently 64 checks have no factor mapping, violating exhaustiveness.

2. **Stable over time:** Categories should not change with every new risk that emerges. Our F1-F10 are stable; the checks within them change. This is correct architecture.

3. **Purpose-driven granularity:** The level of detail should match the decisions being made. For underwriting, we need enough granularity to price the risk but not so much that the underwriter drowns in detail.

4. **Hierarchical with flexible depth:** Not all branches need the same number of levels. F1 (litigation history) might have 3 levels; F8 (M&A) might have 2.

---

## 5. Relevant Frameworks and Precedents

### NIST Risk Management Framework (RMF)

**Structure:** 7-step lifecycle: Prepare -> Categorize -> Select -> Implement -> Assess -> Authorize -> Monitor

**Relevance to our system:**
- **Categorize** maps to our RESOLVE + classify stage
- **Select** maps to deciding which checks apply (not all 388 checks apply to every company)
- **Assess** maps to our ANALYZE + SCORE stages
- **Monitor** maps to our self-improvement mechanisms (Section 3)

**Key tool insight:** Automated RMF tools (Xacta 360, ConfigOS) succeed by maintaining a control catalog (analogous to our checks.json) that maps to specific assessment procedures. The catalog is the knowledge base; the tool automates evaluation.

### Open Policy Agent (OPA) / Rego

**Relevance:** OPA demonstrates a successful "policy as code" pattern:
- Policies are written in Rego (a declarative DSL)
- Policies are separate from the systems they govern
- The engine evaluates policies against input data and returns decisions
- Policies are version-controlled and testable

**Architectural lesson:** OPA works because policies are DECLARATIVE (what should be true) not IMPERATIVE (how to check). Our checks should declare "current ratio < 1.0 is RED" without specifying how to compute current ratio. The compute logic lives in EXTRACT; the assessment logic lives in the check definition.

### DMN (Decision Model and Notation)

**Relevance:** DMN provides a standardized way to express decision logic that non-programmers can read. Its decision tables are particularly relevant for multi-condition checks.

**Practical value:** We don't need to adopt DMN tooling, but we can borrow the decision table concept for our multi-signal INFERENCE_PATTERN checks. A 19-row subset of our checks could be expressed as decision tables within the JSON config.

### openRiskScore (Python)

**What it is:** An open-source Python library for credit risk scoring (Probability of Default, Loss Given Default).

**Relevance:** Demonstrates how to build a risk scoring framework in Python with:
- Statistical estimation of risk models
- Transition matrix analysis (state changes over time)
- Model validation and backtesting
- Open source, well-documented

**Practical value:** Reference implementation for our backtesting infrastructure.

### EU AI Act Requirements for Insurance

**Classification:** AI systems used for life/health insurance risk assessment are explicitly classified as HIGH-RISK under the EU AI Act (Annex III).

**Requirements that affect our architecture:**
1. **Technical documentation:** Full description of decision logic, training data, performance metrics
2. **Human oversight:** Trained professionals must be able to understand, monitor, and override
3. **Record-keeping:** Logs of all decisions with enough detail to reconstruct reasoning
4. **Transparency:** Individuals affected must be informed that AI was involved
5. **Bias monitoring:** Regular assessment for discriminatory outcomes

**Impact on brain architecture:**
- Every check evaluation must be logged with inputs, thresholds, and results (we already do this via CheckRun)
- The brain must be readable by underwriters (not just developers) -- this is a regulatory requirement, not just a nice-to-have
- Generated documentation must be maintained and auditable
- Calibration/effectiveness tracking (Section 3) becomes a compliance requirement, not just a quality improvement

**Note:** D&O liability insurance may not fall directly under Annex III (which specifies life/health), but the direction of regulation is toward more coverage, and US state regulators are following the EU's lead. Building for explainability now is prudent.

### S&P / Moody's Published Criteria

**Key insight:** Rating agencies publish their methodologies in 50-100 page documents that serve three purposes simultaneously:
1. Transparency for issuers and investors
2. Training material for new analysts
3. Audit trail for regulators

**Architectural lesson:** Our "brain documentation" should serve the same three purposes. A single generated document that explains every check, its rationale, its threshold, and its effectiveness would satisfy underwriter readability, analyst training, and regulatory audit requirements.

---

## 6. Recommended Architecture

### Core Principles

1. **Risk questions, not data sources, organize the brain.** Checks answer questions like "Is this company financially distressed?" not "What does the 10-K say about liquidity?"

2. **Schema is the single source of truth.** The Pydantic model defines what a check is. JSON files are instances. Generated docs are views. Code evaluates instances.

3. **Business-readable, not business-writable.** Underwriters read checks and confirm they make sense. Developers write and maintain them. (Fowler's sweet spot.)

4. **Minimal engine, maximal config.** 90% of checks are threshold evaluations that need no engine -- just config. The 10% that need composition get a small, purpose-built evaluator.

5. **Everything is versioned, logged, and measurable.** Every check has a version. Every evaluation is logged. Effectiveness is tracked over time.

### Proposed Structure

#### Layer 1: Risk Taxonomy (Stable, Changes Rarely)

```yaml
# risk_taxonomy.yaml -- The "what we assess" layer
# Changes: ~yearly, requires senior review

pillars:
  P1_WHAT_WRONG:
    name: "What Could Go Wrong?"
    description: "Identifies exposures that create liability"
  P2_WHO_SUE:
    name: "Who Would Sue?"
    description: "Identifies plaintiff populations and motivations"
  P3_HOW_BAD:
    name: "How Bad Could It Get?"
    description: "Quantifies potential severity and frequency"
  P4_WHAT_NEXT:
    name: "What's Coming?"
    description: "Forward-looking risk indicators"

factors:
  F1:
    name: "Securities Class Action History"
    pillar: P3_HOW_BAD
    weight: 0.15  # Published, transparent
    description: "Prior litigation and enforcement track record"
  F2:
    name: "Financial Condition"
    pillar: P1_WHAT_WRONG
    weight: 0.12
    description: "Company solvency, liquidity, distress indicators"
  # ... F3 through F10
```

#### Layer 2: Risk Questions (Semi-Stable, Changes Quarterly)

```yaml
# risk_questions/financial_condition.yaml
# Each file covers one risk domain, contains the questions

domain: "Financial Condition"
factor: F2

questions:
  - id: Q.FIN.DISTRESS
    text: "Is this company showing signs of financial distress?"
    why: >
      Financially distressed companies account for ~40% of securities
      class action filings despite representing <5% of public companies.
      Distress creates perverse incentives for earnings management,
      disclosure failures, and insider self-dealing.
    checks:
      - FIN.DISTRESS.altman_z
      - FIN.DISTRESS.going_concern
      - FIN.RATIO.current
      - FIN.DEBT.leverage
      - STOCK.SHORT.interest  # Cross-domain signal
    aggregation: worst_of  # Question is RED if any check is RED

  - id: Q.FIN.EARNINGS
    text: "Is the company managing earnings or using aggressive accounting?"
    why: >
      Earnings management is the single most common allegation in D&O
      securities class actions. Revenue recognition issues, reserve
      manipulation, and channel stuffing recur across industries.
    checks:
      - FIN.EARN.quality
      - FIN.EARN.restatement_risk
      - FIN.ACCT.revenue_recognition
      - NLP.TONE.mda_optimism  # Cross-domain signal
```

#### Layer 3: Check Definitions (Active Development, Changes Weekly)

```yaml
# checks/financial/distress.yaml
# Individual check definitions with full machine-executable spec

- id: FIN.DISTRESS.altman_z
  name: "Altman Z-Score Assessment"
  version: 3
  question: Q.FIN.DISTRESS

  # What an underwriter reads:
  readable:
    summary: "Altman Z-Score bankruptcy prediction model"
    interpretation: >
      The Z-Score predicts bankruptcy probability within 2 years.
      Below 1.81 = high distress risk. Above 2.99 = low risk.
      The gray zone (1.81-2.99) requires judgment.
    source_reference: "Altman, 1968; updated Altman, 2000"

  # What the engine executes:
  evaluation:
    field: altman_z_score
    type: numeric_threshold
    thresholds:
      red: "< 1.81"
      yellow: "1.81 - 2.99"
      clear: "> 2.99"

  # What data acquisition needs:
  data_requirements:
    sources: [SEC_10K]
    sections: [item_8_financials]
    fields_needed: [total_assets, total_liabilities, working_capital,
                    retained_earnings, ebit, market_cap, revenue]

  # What self-improvement tracks:
  effectiveness:
    expected_fire_rate: 0.05  # ~5% of companies
    claims_correlation: 0.72  # Empirical correlation with claims
    last_calibrated: "2026-01-15"
    calibration_notes: "Validated against 2020-2025 SCA filings"
```

#### Layer 4: Evaluation Engine (Code, Changes Infrequently)

```python
# stages/analyze/brain_engine.py -- The minimal engine

class BrainEngine:
    """Evaluates checks against company data.

    Handles five evaluation types:
    1. numeric_threshold -- compare number to RED/YELLOW/CLEAR ranges
    2. boolean_flag -- presence/absence of a condition
    3. pattern_match -- regex or keyword detection
    4. temporal_check -- event within time window
    5. composite -- weighted combination of other checks
    """

    def evaluate(self, check: CheckDefinition, data: AnalysisState) -> CheckResult:
        evaluator = self.EVALUATORS[check.evaluation.type]
        return evaluator(check, data)
```

#### Layer 5: Effectiveness Tracking (Automated, Runs Continuously)

```python
# stages/analyze/brain_effectiveness.py

class EffectivenessTracker:
    """Tracks brain performance over time.

    After each pipeline run:
    1. Records all check results to CheckRun table
    2. Updates fire rate statistics
    3. Flags anomalies (never-fires, always-fires)

    On schedule (weekly/monthly):
    4. Runs calibration analysis against known outcomes
    5. Generates effectiveness report
    6. Flags checks for review
    """
```

### File Organization

```
src/do_uw/brain/
  taxonomy.yaml              # Layer 1: Risk taxonomy (pillars, factors, weights)
  questions/                  # Layer 2: Risk questions organized by domain
    financial_condition.yaml
    corporate_governance.yaml
    litigation_history.yaml
    stock_market.yaml
    insider_activity.yaml
    regulatory.yaml
    industry.yaml
    mna_restructuring.yaml
    emerging_risk.yaml
  checks/                     # Layer 3: Check definitions organized by domain
    financial/
      distress.yaml
      ratios.yaml
      earnings.yaml
      debt.yaml
    governance/
      board.yaml
      controls.yaml
      compensation.yaml
    litigation/
      history.yaml
      current.yaml
      enforcement.yaml
    # ... etc
  schemas/                    # Pydantic models that validate all the above
    taxonomy_schema.py
    question_schema.py
    check_schema.py
  engine/                     # Layer 4: Evaluation engine
    evaluators.py             # The five evaluation types
    aggregators.py            # Question-level and factor-level aggregation
    compositor.py             # Composite/inference pattern evaluation
  effectiveness/              # Layer 5: Self-improvement
    tracker.py
    calibration.py
    gap_detector.py
    backtester.py
```

### Migration Path from Current System

The current system has 388 checks in a single `checks.json` file organized by data-source prefix. Migration should be incremental:

1. **Phase A:** Add `risk_question` field to existing checks.json entries. Map every check to a question. Don't change file structure yet.

2. **Phase B:** Create `taxonomy.yaml` and `questions/*.yaml` as NEW files that reference existing check IDs. Validate that every check is covered. This is additive -- nothing breaks.

3. **Phase C:** Split `checks.json` into per-domain YAML files (`checks/financial/*.yaml`, etc.). Maintain backward compatibility by generating `checks.json` from the YAML files during build. Tests verify equivalence.

4. **Phase D:** Wire the new engine to read from YAML files instead of `checks.json`. The generated `checks.json` becomes a compatibility artifact.

5. **Phase E:** Add effectiveness tracking. Start recording fire rates and calibration data from each pipeline run.

Each phase is independently deployable and testable. No big-bang rewrite.

---

## Sources

### Knowledge Representation
- [Rules Engine Design Patterns - Nected](https://www.nected.ai/blog/rules-engine-design-pattern)
- [Rule Engine Design Pattern and Applications - Sparkling Logic](https://www.sparklinglogic.com/rule-engine-design-and-applications/)
- [Martin Fowler: Rules Engine](https://martinfowler.com/bliki/RulesEngine.html)
- [Martin Fowler: Business Readable DSL](https://martinfowler.com/bliki/BusinessReadableDSL.html)
- [Decision Engine vs Rule Engine - FlexRule](https://www.flexrule.com/archives/decision-engine-vs-rule-engine/)
- [Rules for Knowledge Graphs - Dan McCreary](https://dmccreary.medium.com/rules-for-knowledge-graphs-rules-f22587307a8f)
- [Finding Patterns with Rules Using Knowledge Graphs - Oxford Semantic](https://www.oxfordsemantic.tech/blog/finding-patterns-with-rules-using-knowledge-graphs-and-semantic-reasoning)
- [Knowledge Representation in Expert Systems - ResearchGate](https://www.researchgate.net/publication/386487116_Knowledge_Representation_in_Expert_Systems_Structure_Classification_and_Applications)

### Documentation-Code Sync
- [Schema-Driven Development - NoClocks](https://blog.noclocks.dev/schema-driven-development-and-single-source-of-truth-essential-practices-for-modern-developers)
- [Using a Schema-First Design as Your Single Source of Truth - Nordic APIs](https://nordicapis.com/using-a-schema-first-design-as-your-single-source-of-truth/)
- [Documentation as Code: Agile One Source of Truth - Scand](https://scand.com/company/blog/documentation-as-code-agile-one-source-of-truth/)
- [Pydantic JSON Schema Generation](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [json-schema-for-humans - GitHub](https://github.com/coveooss/json-schema-for-humans)

### Self-Improvement and Calibration
- [Brier Score - Wikipedia](https://en.wikipedia.org/wiki/Brier_score)
- [Weighted Brier Score for Risk Prediction - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12523994/)
- [Scoring a Risk Forecast - Ryan McGeehan](https://magoo.medium.com/scoring-a-risk-forecast-58673bb6a05e)
- [What is Concept Drift in ML - Evidently AI](https://www.evidentlyai.com/ml-in-production/concept-drift)
- [How to Release Fraud Rules Safely - Sardine](https://www.sardine.ai/blog/fraud-rules)
- [Backtesting - Wikipedia](https://en.wikipedia.org/wiki/Backtesting)

### Risk Assessment Architecture
- [FICO Score Credit Education](https://www.myfico.com/credit-education/credit-scores/fico-score-versions)
- [Credit Scoring Models: FICO, VantageScore - Debt.org](https://www.debt.org/credit/report/scoring-models/)
- [Moody's Rating Methodologies](https://ratings.moodys.com/api/rmc-documents/356428)
- [Moody's Rating Process](https://www.lwm-info.org/DocumentCenter/View/3047/Moodys-Rating-Process)
- [FDIC Scoring and Modeling](https://www.fdic.gov/regulations/examinations/credit_card/pdf_version/ch8.pdf)

### Risk Taxonomy
- [What Constitutes a Good Risk Taxonomy - Open Risk](https://www.openriskmanagement.com/what-constitutes-a-good-risk-taxonomy/)
- [Risk Taxonomy Guide - MetricStream](https://www.metricstream.com/learn/risk-taxonomy.html)
- [How to Develop an Enterprise Risk Taxonomy - GARP](https://www.garp.org/risk-intelligence/culture-governance/how-to-develop-an-enterprise-risk-taxonomy)
- [Open Risk Taxonomy White Paper](https://www.openriskmanagement.com/wp-content/uploads/2017/02/OpenRiskWP04_061415.pdf)

### Frameworks and Standards
- [FAIR Framework - The FAIR Institute](https://www.fairinstitute.org/what-is-fair)
- [Factor Analysis of Information Risk - Wikipedia](https://en.wikipedia.org/wiki/Factor_analysis_of_information_risk)
- [NIST Risk Management Framework - CSRC](https://csrc.nist.gov/projects/risk-management)
- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs)
- [DMN in Drools](https://docs.drools.org/latest/drools-docs/drools/DMN/index.html)
- [openRiskScore - GitHub](https://github.com/open-risk/openRiskScore)

### Regulatory
- [EU AI Act and Insurance - Blue Arrow](https://bluearrow.ai/ai-act-and-insurance/)
- [EU AI Act High-Level Summary](https://artificialintelligenceact.eu/high-level-summary/)
- [Future of Credit Underwriting Under EU AI Act - Harvard Data Science Review](https://hdsr.mitpress.mit.edu/pub/19cwd6qx)
- [Algorithmic Bias Under EU AI Act in Insurance - MDPI](https://www.mdpi.com/2227-9091/13/9/160)
- [EIOPA Regulatory Framework for AI in Insurance](https://www.eiopa.europa.eu/document/download/b53a3b92-08cc-4079-a4f7-606cf309a34a_en)

### Platform References
- [Palantir Foundry Ontology Overview](https://www.palantir.com/docs/foundry/ontology/overview)
- [Palantir Ontology SDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview)
- [Automated Underwriting in Insurance - SCNSoft](https://www.scnsoft.com/insurance/underwriting-automation)
- [AI in Insurance Underwriting - Salesforce](https://www.salesforce.com/financial-services/artificial-intelligence/ai-in-insurance-underwriting/)
