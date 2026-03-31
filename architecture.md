# Sasha Platform — Architecture & Brain Interaction

## The Complete Pipeline (5 Layers, Not 4)

The Brain Unification defined 4 processing layers. In practice, there are **5 distinct layers** because the Document model is its own layer between assessment and rendering:

```
   BRAIN (specification layer — lives alongside, not in the pipeline)
     │ defines what to collect, how to evaluate, what to present
     ▼
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ COLLECT  │ →  │ EVALUATE │ →  │ INTERPRET│ →  │ COMPOSE  │ →  │ RENDER   │
│ Layer 1  │    │ Layer 2  │    │ Layer 3  │    │ Layer 4  │    │ Layer 5  │
│          │    │          │    │          │    │          │    │          │
│ Raw data │    │ Signals  │    │ Engines  │    │ Document │    │ Output   │
│ → Dossier│    │ (H/A/E)  │    │ + Score  │    │ model    │    │ HTML/PDF │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
  "What do       "What's          "What kind     "What charts    "How to
   we know?"     risk-relevant?"   of risk?"     and narrative?"  draw it?"
```

### Where the Brain fits

The Brain is **NOT a pipeline layer** — it's the **specification layer** that tells each pipeline layer what to do:

| Brain Asset | Tells Which Layer | What It Specifies |
|-------------|-------------------|-------------------|
| `brain/signals/*.yaml` | Layer 2 (Evaluate) | What signals exist, thresholds, H/A/E classification |
| [brain/config/hazard_weights.json](file:///Users/gorlin/projects/UW/do-uw/src/do_uw/brain/config/hazard_weights.json) | Layer 2-3 | Dimension weights, scoring parameters |
| `brain/engines/*.yaml` | Layer 3 (Interpret) | Story engine rules, firing conditions |
| `brain/sections/*.yaml` | Layer 4 (Compose) | What sections exist, what goes in each, chart specs |
| `brain/playbooks/*.yaml` | Layer 2-3 | Industry-specific signal overrides |
| [brain/framework/causal_chains.yaml](file:///Users/gorlin/projects/UW/do-uw/src/do_uw/brain/framework/causal_chains.yaml) | Layer 3 | Risk propagation patterns |
| `brain/config/sector_overlay.yaml` | Layer 2-3 | Sector-specific regulatory context |

**This is crucial**: when an underwriter or developer wants to change behavior, they edit `brain/` YAML files, not code. The brain is the human-editable specification layer.

---

## How a New Piece of Information Flows Through All Layers

Example: **"Company just announced a restatement of Q3 earnings"**

### Layer 1 — Collect → Dossier
```yaml
# Stored as a raw fact in dossier.events.restatements
- date: "2026-03-10"
  filing_type: "8-K/A"
  periods_affected: ["Q3 2025"]
  magnitude: "revenue reduced by $45M"
  reason: "revenue recognition error"
```

### Layer 2 — Evaluate → Signals
The brain spec `brain/signals/disclosure.yaml` defines:
```yaml
DISCLOSURE.RESTATEMENT.severity:
  dimension: A          # Agent trigger
  category: A1          # Disclosure event
  mechanism: threshold   # Fires when restatement exists
  thresholds:
    red: "any revenue restatement"
    yellow: "non-revenue restatement"
```
Result: `SignalResult(status="fired", severity="critical", dimension="A", category="A1")`

### Layer 3 — Interpret → Engines + Score
- **Bow-Tie engine**: checks if audit controls were also weak → if yes, fires
- **Precedent Match**: compares to historical restatement-preceded-claim patterns
- **Scoring**: A1 (disclosure) agent multiplier increases to ~3.5

### Layer 4 — Compose → Document
The brain spec `brain/sections/financial_health.yaml` defines:
```yaml
section: financial_health
charts:
  - type: restatement_timeline
    title: "Restatement History & Impact"
    reading_guide: "Reading this chart: Red bars show affected revenue..."
callout_triggers:
  - signal: DISCLOSURE.RESTATEMENT.severity
    style: red_alert
    template: "⚠️ Revenue restatement of {magnitude} for {periods}"
```
Result: The Document gets a chart spec, a red callout box, and narrative text.

### Layer 5 — Render → HTML/PDF
Takes the Document's `ChartSpec` and `callout_box` and draws them.

**Key guarantee**: if the brain defines a signal for it, it flows through ALL layers automatically. Nothing gets "lost" between layers.

---

## How the Brain Lives (Human-Editable Knowledge)

```
brain/
├── signals/                    # WHAT to evaluate
│   ├── financial.yaml          #   Beneish, Z-Score, ratio signals
│   ├── market.yaml             #   Stock drops, short interest, beta
│   ├── governance.yaml         #   Board composition, comp, ISS
│   ├── disclosure.yaml         #   Restatements, late filings
│   ├── litigation.yaml         #   SEC, class actions, settlements
│   └── operational.yaml        #   Cyber, supply chain, regulatory
│
├── config/                     # HOW to weight and score
│   ├── hazard_weights.json     #   H/A/E dimension weights
│   ├── sector_overlay.yaml     #   Per-sector regulatory context
│   ├── claim_patterns.yaml     #   Historical claim type patterns
│   └── tier_thresholds.yaml    #   WIN/WATCH/WALK/RUN boundaries
│
├── engines/                    # PATTERN recognition rules
│   ├── bow_tie.yaml            #   Barrier degradation patterns
│   ├── migration_drift.yaml    #   Slow deterioration rules
│   ├── precedent_match.yaml    #   Historical case patterns
│   └── conjunction_scan.yaml   #   Weak-signal combination rules
│
├── sections/                   # HOW to present results
│   ├── exec_summary.yaml       #   Charts: risk gauge, heatmap
│   ├── financial_health.yaml   #   Charts: distress panel, forensic radar
│   ├── governance.yaml         #   Charts: board composition, comp bars
│   └── ...
│
├── playbooks/                  # INDUSTRY-specific knowledge
│   ├── biotech.yaml
│   ├── financials.yaml
│   └── ...
│
└── learning/                   # HUMAN corrections (grows over time)
    ├── rules.yaml              #   Ripple-Down Rules from overrides
    ├── cases.yaml              #   Case-Based Reasoning library
    └── calibration.yaml        #   Threshold adjustments from feedback
```

Every file is **YAML or JSON** — readable and editable by humans *and* AI agents. No code changes needed to add a new signal, adjust a threshold, or change a chart specification.

---

## Human-in-the-Loop: How the Underwriter Interacts

### During Assessment Review

1. **Override a tier**: "I think this should be WALK, not WATCH"
   → Logged in `brain/learning/rules.yaml` as an "unless" rule:
   ```yaml
   - rule_id: RDR-047
     created_by: "mgorlin"
     date: "2026-03-10"
     context: "RPM, tier=WATCH, score=0.45"
     override: "WALK"
     reason: "Construction sector regulatory tightening not captured"
     unless_condition: "sector=construction AND e2_regulatory < 1.5"
   ```

2. **Add a note**: "Ask about the CFO departure in the meeting"
   → Stored with the assessment, feeds into future assessments of similar profiles

3. **Flag a missing check**: "We should be looking at their pension obligations"
   → Creates a gap entry in `brain/signals/` for future implementation

### During Brain Editing

4. **Adjust a threshold**: "Beneish M-Score should fire at -2.22, not -1.78 for financials"
   → Edit `brain/signals/financial.yaml` directly, or via override:
   ```yaml
   FINANCIAL.BENEISH.m_score:
     thresholds:
       red: -1.78    # default
       overrides:
         - sector: financials
           red: -2.22   # financials have different baseline
           added_by: mgorlin
   ```

5. **Add a new signal**: "I want to track days-payable-outstanding trends"
   → Add to `brain/signals/financial.yaml`:
   ```yaml
   FINANCIAL.DPO.trend:
     dimension: H
     category: H2
     mechanism: trend
     description: "Days payable outstanding increasing >20% YoY"
     thresholds:
       yellow: 20    # % increase
       red: 40
   ```
   The pipeline automatically picks it up — collect/ gathers the data, evaluate/ generates the signal, compose/ includes it in the relevant section.

---

## Open Questions Still to Resolve

| # | Question | Options | Impact |
|---|----------|---------|--------|
| 1 | **Chart spec location** | In `brain/sections/` (brain-driven) vs in code (render/) | Brain = more flexible but more config; Code = simpler but harder to change |
| 2 | **Playbook format** | Current playbooks are Python code; need YAML conversion | Determines how industry-specific the system is |
| 3 | **Severity amplifier** | Per-signal (fine-grained) vs per-category (simpler) | Per-signal = more accurate but ~380 values to calibrate |
| 4 | **Engine interaction** | Do engines read each other's output, or only the signal store? | Reading each other = richer but more complex |
| 5 | **Learning persistence** | File-based (brain/learning/) vs database | File = simpler, portable; DB = queryable, auditable |
| 6 | **Multi-LOB** | When to implement Cyber/E&O sub-categories | Now (generic) vs later (D&O focus first) |

> **Recommendation**: D&O-first for all of these. Get the pipeline working end-to-end for D&O, then generalize. Chart specs in brain/ (not code). Playbooks as YAML. File-based learning. Engines read only the signal store (not each other).
