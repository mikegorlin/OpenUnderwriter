# Signal Author Guide

How to add or modify brain signals in the D&O Underwriting system.

## 1. Signal Types

There are two signal types:

**Foundational (`type: foundational`)** -- Declares a Tier 1 data source that the ACQUIRE stage always pulls for every company. These are NOT evaluated by the signal engine (no thresholds, no fire/clear). They exist for traceability: every always-acquired data source maps to a foundational signal. Located in `brain/signals/base/`.

**Evaluative (`work_type: evaluate`)** -- Checks a data point against thresholds to produce FIRED/CLEAR/SKIPPED status. These are the 400+ signals that drive risk scoring. Located in `brain/signals/{domain}/` (e.g., `fin/`, `gov/`, `lit/`, `mkt/`, `ops/`).

**When to use each:**
- Adding a new always-acquired data source? Create a foundational signal in `base/`.
- Adding a new risk check against existing data? Create an evaluative signal in the appropriate domain folder.

## 2. Adding a Foundational Signal

Place in `brain/signals/base/`. Must have an `acquisition` block listing state paths.

**Required fields:** `id`, `name`, `type: foundational`, `work_type: acquire`, `tier: 0`, `depth: 1`, `threshold.type: info`, `provenance`, `acquisition`, `facet`, `description`.

**Example** (from `base/xbrl.yaml`):

```yaml
- id: BASE.XBRL.balance_sheet
  name: XBRL Balance Sheet Data
  type: foundational
  work_type: acquire
  tier: 0
  depth: 1
  threshold:
    type: info
  provenance:
    origin: v3.1_tier1_manifest
    confidence: HIGH
    source_author: system
    added_by: Phase70
  acquisition:
    sources:
      - type: SEC_10K
        fields:
          - extracted.financials.statements.balance_sheet
        fallback_to: null
  facet: financial_health
  description: >
    Annual balance sheet line items from XBRL filing.
```

After adding, update `docs/TIER1_MANIFEST.md` with the new signal and run `uv run pytest tests/brain/test_foundational_coverage.py` to verify CI coverage.

## 3. Adding an Evaluative Signal

Place in `brain/signals/{domain}/`. Must have `data_strategy` with `field_key` and `threshold` with comparison values.

**Required fields:** `id`, `name`, `work_type: evaluate`, `layer: signal`, `factors` (scoring factor list), `data_strategy`, `threshold`, `tier`, `depth`, `provenance`, `facet`.

**Example** (from `fin/forensic_xbrl.yaml`):

```yaml
- id: FIN.FORENSIC.goodwill_impairment_risk
  name: Goodwill Impairment Risk
  work_type: evaluate
  layer: signal
  factors: [F3]
  data_strategy:
    field_key: forensic_goodwill_to_assets
    primary_source: SEC_10K
  threshold:
    type: tiered
    red: '> 0.40'
    yellow: '> 0.25'
    clear: <= 0.25
  tier: 1
  depth: 3
  provenance:
    origin: v3.1_xbrl_forensic
    confidence: HIGH
    source_author: system
    added_by: Phase70
  facet: financial_health
```

**Threshold types:**
- `tiered` -- red/yellow/clear zones (most common)
- `boolean` -- true/false check
- `info` -- informational only (no evaluation)

## 4. Acquisition Blocks

**When to add `acquisition:`** -- The signal needs data NOT already in the Tier 1 manifest. The acquisition block tells the ACQUIRE stage what additional data to fetch.

```yaml
acquisition:
  sources:
    - type: EXTERNAL_API
      fields:
        - extracted.special.external_data
      fallback_to: null
```

**When NOT to add `acquisition:`** -- The signal uses data already staged by Tier 1 foundational signals. Just reference the data via `data_strategy.field_key`. This is the common case for evaluative signals -- they consume data that foundational signals declared.

```yaml
# No acquisition block needed -- data already in Tier 1
data_strategy:
  field_key: forensic_goodwill_to_assets
  primary_source: SEC_10K
```

**Dual-source signals** -- Some signals have both a quantitative field and a narrative source. Use `narrative_key` alongside `field_key`:

```yaml
data_strategy:
  field_key: xbrl_current_ratio
  narrative_key: extracted.text_signals.liquidity_discussion
  primary_source: SEC_10K
```

## 5. gap_bucket and gap_keywords

These fields help categorize data gaps for future resolution.

**`gap_bucket`** -- Which acquisition system should eventually provide this data. Values: `xbrl`, `filings`, `market`, `litigation`, `news`, `external_api`, `llm_extraction`.

**`gap_keywords`** -- Search terms that help identify where the data might come from.

```yaml
gap_bucket: external_api
gap_keywords:
  - ISS governance score
  - proxy advisory rating
```

**When to populate:** When a signal is INACTIVE because its data source doesn't exist yet. The gap_bucket and gap_keywords help prioritize future data acquisition work.

## 6. Signal Naming Convention

Format: `{DOMAIN}.{CATEGORY}.{specific_check}`

| Domain Prefix | Scope |
|---|---|
| `BASE` | Tier 1 foundational data sources |
| `FIN` | Financial health and forensics |
| `GOV` | Governance, board, compensation |
| `LIT` | Litigation and legal exposure |
| `MKT` | Market activity, stock, ownership |
| `OPS` | Operational risk, compliance |

**Examples:**
- `FIN.FORENSIC.goodwill_impairment_risk` -- Financial forensic check
- `GOV.BOARD.independence_ratio` -- Governance board check
- `LIT.HIST.prior_sca_count` -- Litigation historical check
- `MKT.PRICE.52w_decline` -- Market price check
- `BASE.XBRL.balance_sheet` -- Tier 1 XBRL data manifest entry

## 7. data_strategy Fields

The `data_strategy` block tells the signal engine where to find data in the pipeline state.

| Field | Purpose | Required |
|---|---|---|
| `field_key` | Dot-path to the data in state (or a routing prefix) | Yes |
| `narrative_key` | Secondary dot-path for text/narrative data | No |
| `primary_source` | Which data source type (SEC_10K, MARKET_PRICE, etc.) | No |

**field_key routing:** The signal engine uses `field_key` to look up data. Some prefixes have special routing:
- `forensic_` -- Routes to `analysis.xbrl_forensics` via forensic field routing
- `xbrl_` -- Routes to XBRL-sourced financial data
- `gov_`, `lit_`, `mkt_` -- Route to respective state sections

## 8. Testing a New Signal

After creating or modifying a signal:

1. **Validate YAML loads:** `uv run pytest tests/brain/test_foundational_coverage.py -x -q` (for foundational) or `uv run pytest tests/brain/ -x -q` (all brain tests).

2. **Run the pipeline:** `uv run python -m do_uw run TICKER` for a test ticker. This populates `brain_signal_runs` in the brain database.

3. **Check signal status:** After a pipeline run, query the brain database:
   ```sql
   SELECT signal_id, status, value, threshold_used
   FROM brain_signal_runs
   WHERE signal_id = 'YOUR.SIGNAL.id'
   ORDER BY run_date DESC LIMIT 5;
   ```

4. **Verify fire/clear:** The signal should FIRE (status=FIRED) when the data exceeds the threshold, CLEAR when it doesn't, and SKIP when data is unavailable. A signal that always SKIPs likely has a `field_key` routing issue.

5. **Check for regressions:** Run the full brain test suite: `uv run pytest tests/brain/ -x -q`.

## 9. Common Pitfalls

- **Duplicate field_key prefix:** If two signals share the same `field_key`, they'll read the same data. Use distinct keys or a domain prefix (`forensic_`, `xbrl_`).
- **Missing provenance:** Every signal must have a `provenance` block with `origin`, `confidence`, `source_author`, `added_by`.
- **Foundational in wrong directory:** Foundational signals MUST be in `brain/signals/base/`. Evaluative signals MUST NOT be in `base/`.
- **Forgetting the manifest:** After adding a foundational signal, update `docs/TIER1_MANIFEST.md`.
