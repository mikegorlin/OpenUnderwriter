#!/usr/bin/env python3
"""Batch generate D&O commentary (do_context) templates for all brain signals.

Reads all YAML files from src/do_uw/brain/signals/, generates TRIGGERED_RED,
TRIGGERED_YELLOW, and CLEAR templates for each signal lacking do_context,
writes enriched YAML back preserving structure via ruamel.yaml.

Usage:
    uv run python scripts/batch_generate_do_context.py                  # full run (deterministic)
    uv run python scripts/batch_generate_do_context.py --use-llm        # use Claude API
    uv run python scripts/batch_generate_do_context.py --dry-run        # print what would change
    uv run python scripts/batch_generate_do_context.py --validate-only  # validate existing
    uv run python scripts/batch_generate_do_context.py --file PATH      # single file
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

# Add project root to path so we can import do_uw
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from do_uw.stages.analyze.do_context_engine import validate_do_context_template

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor to D&O litigation theory mapping
# ---------------------------------------------------------------------------

FACTOR_TO_THEORY: dict[str, str] = {
    "F1": "Litigation History / Settlement Patterns — prior SCA filings, settlement frequency, and recidivism risk that plaintiffs cite when establishing a pattern of securities fraud exposure",
    "F2": "Stock Decline / Securities Fraud — stock price volatility, corrective disclosures, and price drops that form the basis of Section 10(b) loss causation claims",
    "F3": "Financial Irregularities / Restatement Risk — accounting manipulation, restatement probability, and GAAP violations underlying financial fraud allegations in SCA complaints",
    "F4": "Insider Trading / Scienter — suspicious trading patterns by officers/directors that plaintiffs use to establish scienter (intent to defraud) in securities class actions",
    "F5": "Regulatory Action / Government Investigation — SEC enforcement, DOJ referrals, and regulatory sanctions that often trigger derivative suits and D&O coverage disputes",
    "F6": "Governance Failures / Breach of Fiduciary Duty — board composition, oversight lapses, and structural weaknesses invoked in Caremark and derivative claims",
    "F7": "Insider Selling / Director Trading — director-level share sales and hedging activity that signal potential self-dealing or breach of duty claims",
    "F8": "Market Position / Business Risk — competitive dynamics, revenue concentration, and operational vulnerabilities that amplify D&O exposure during downturns",
    "F9": "SEC Enforcement / Regulatory Compliance — specific SEC actions, AAER filings, and compliance failures that directly increase D&O claim severity",
    "F10": "Emerging Risk / Forward-Looking Exposure — macro trends, ESG liabilities, and forward-looking risk factors not yet in litigation but recognized in D&O underwriting",
}

# Peril ID to description mapping for prompt context
PERIL_DESCRIPTIONS: dict[str, str] = {
    "SCA": "Securities Class Action (Section 10(b)/Rule 10b-5)",
    "DERIV": "Shareholder Derivative Suit (breach of fiduciary duty)",
    "M&A": "Merger Objection / Appraisal Action",
    "SEC": "SEC Enforcement Action (civil/administrative)",
    "ERISA": "ERISA / Employee Benefit Plan Litigation",
    "INSOLVENCY": "Zone-of-Insolvency Claims (creditor derivative)",
    "ANTITRUST": "Antitrust / Competition Law Exposure",
    "CYBER": "Data Breach / Cybersecurity Litigation",
    "ESG": "ESG / Climate / Social Responsibility Litigation",
    "IPO": "IPO / Section 11 / Section 12 Claims",
    "REGULATORY": "Regulatory / Government Investigation",
}

# RAP class to D&O context explanation
RAP_CLASS_CONTEXT: dict[str, str] = {
    "host": "host risk (company-level characteristics that attract or deter D&O claims)",
    "agent": "agent risk (executive/director actions and decisions that create D&O exposure)",
    "environment": "environment risk (external market, regulatory, and industry conditions affecting D&O liability)",
}

# Threshold type descriptions for template generation
THRESHOLD_TYPE_CONTEXT: dict[str, str] = {
    "tiered": "numeric threshold with RED/YELLOW/CLEAR zones",
    "boolean": "binary check (triggered/clear)",
    "info": "informational display (context for underwriter, no risk threshold)",
    "display": "data display (no evaluation threshold)",
    "numeric": "numeric comparison threshold",
    "percentage": "percentage-based threshold",
    "trend": "trend detection (improving/deteriorating)",
}


# ---------------------------------------------------------------------------
# Deterministic template generation (no LLM required)
# ---------------------------------------------------------------------------


def _get_factor_theories(factors: list[str]) -> str:
    """Get D&O theories for a signal's factors."""
    theories = []
    for f in factors:
        # Normalize: "F1", "F.1", "F1_prior_litigation" -> "F1"
        key = f.split("_")[0].replace(".", "")
        if key in FACTOR_TO_THEORY:
            theories.append(f"{key}: {FACTOR_TO_THEORY[key].split(' — ')[0]}")
    return "; ".join(theories) if theories else "General D&O risk assessment"


def _get_peril_context(peril_ids: list[str]) -> str:
    """Get peril descriptions for a signal's peril_ids."""
    perils = []
    for pid in peril_ids:
        if pid in PERIL_DESCRIPTIONS:
            perils.append(PERIL_DESCRIPTIONS[pid])
    return ", ".join(perils) if perils else ""


def _build_threshold_desc(threshold: dict[str, Any]) -> dict[str, str]:
    """Extract threshold descriptions for each zone."""
    return {
        "red": str(threshold.get("red", "")),
        "yellow": str(threshold.get("yellow", "")),
        "clear": str(threshold.get("clear", "")),
        "type": str(threshold.get("type", "unknown")),
        "triggered": str(threshold.get("triggered", "")),
    }


def generate_do_context_for_signal(signal: dict[str, Any]) -> dict[str, str]:
    """Generate do_context templates deterministically from signal metadata.

    Produces company-specific templates using {value}, {company}, {evidence}
    placeholders and references the signal's D&O litigation theories.

    Alias: generate_do_context_deterministic (same function).
    """
    sig_id = signal["id"]
    name = signal["name"]
    factors = signal.get("factors", [])
    peril_ids = signal.get("peril_ids", [])
    threshold = signal.get("threshold", {})
    epistemology = signal.get("epistemology", {})
    rap_class = signal.get("rap_class", "host")
    rap_sub = signal.get("rap_subcategory", "")
    work_type = signal.get("work_type", "evaluate")
    th_type = threshold.get("type", "unknown")

    # Build context pieces
    factor_theories = _get_factor_theories(factors)
    peril_context = _get_peril_context(peril_ids)
    rap_desc = RAP_CLASS_CONTEXT.get(rap_class, "D&O risk factor")
    th_desc = _build_threshold_desc(threshold)
    rule_origin = epistemology.get("rule_origin", "")
    threshold_basis = epistemology.get("threshold_basis", "")

    # Determine the primary D&O theory reference
    if factors:
        primary_factor = factors[0].split("_")[0].replace(".", "")
        primary_theory = FACTOR_TO_THEORY.get(primary_factor, "").split(" — ")[0]
    elif peril_ids:
        primary_theory = PERIL_DESCRIPTIONS.get(peril_ids[0], "D&O liability exposure")
    else:
        primary_theory = "D&O risk assessment"

    # For info/display signals, generate minimal but accurate templates
    if th_type in ("info", "display"):
        return _generate_info_templates(sig_id, name, factors, primary_theory, rap_desc)

    # For boolean signals
    if th_type == "boolean":
        return _generate_boolean_templates(
            sig_id, name, factors, primary_theory, peril_context, rap_desc, th_desc
        )

    # For tiered/numeric/percentage signals
    return _generate_tiered_templates(
        sig_id, name, factors, primary_theory, peril_context, rap_desc, th_desc,
        threshold_basis, rule_origin
    )


# Alias for backward compatibility
generate_do_context_deterministic = generate_do_context_for_signal


def _generate_info_templates(
    sig_id: str, name: str, factors: list[str],
    primary_theory: str, rap_desc: str,
) -> dict[str, str]:
    """Generate templates for info/display signals."""
    factor_ref = f" (scoring factor {', '.join(factors)})" if factors else ""
    return {
        "TRIGGERED_RED": (
            f"{{company}} {name.lower()} at {{value}} represents {rap_desc}"
            f"{factor_ref} — this level is associated with {primary_theory} "
            f"exposure based on D&O claims experience."
        ),
        "TRIGGERED_YELLOW": (
            f"{{company}} {name.lower()} at {{value}} is a moderate indicator "
            f"for {primary_theory}{factor_ref}, warranting review of supporting "
            f"evidence: {{evidence}}."
        ),
        "CLEAR": (
            f"{{company}} {name.lower()} at {{value}} is within normal parameters "
            f"for {primary_theory}{factor_ref} — no D&O concern at this level."
        ),
    }


def _generate_boolean_templates(
    sig_id: str, name: str, factors: list[str],
    primary_theory: str, peril_context: str,
    rap_desc: str, th_desc: dict[str, str],
) -> dict[str, str]:
    """Generate templates for boolean-type signals."""
    factor_ref = f" ({', '.join(factors)})" if factors else ""
    peril_ref = f" with exposure to {peril_context}" if peril_context else ""

    return {
        "TRIGGERED_RED": (
            f"{{company}} triggered {name}{factor_ref} — this {rap_desc} "
            f"indicates {primary_theory}{peril_ref}. Evidence: {{evidence}}."
        ),
        "TRIGGERED_YELLOW": (
            f"{{company}} shows moderate signal on {name}{factor_ref} at "
            f"{{value}} — review recommended for {primary_theory} implications."
        ),
        "CLEAR": (
            f"{{company}} clear on {name}{factor_ref} — no {primary_theory} "
            f"concern identified at this level."
        ),
    }


def _generate_tiered_templates(
    sig_id: str, name: str, factors: list[str],
    primary_theory: str, peril_context: str,
    rap_desc: str, th_desc: dict[str, str],
    threshold_basis: str, rule_origin: str,
) -> dict[str, str]:
    """Generate templates for tiered/numeric/percentage signals."""
    factor_ref = f" ({', '.join(factors)})" if factors else ""
    peril_ref = f", increasing exposure to {peril_context}" if peril_context else ""

    # Include threshold values in the template when available
    red_threshold = f" (threshold: {th_desc['red']})" if th_desc["red"] and th_desc["red"] != "None" else ""
    yellow_threshold = f" (threshold: {th_desc['yellow']})" if th_desc["yellow"] and th_desc["yellow"] != "None" else ""

    # Use threshold_basis for additional context if available
    basis_ref = ""
    if threshold_basis and len(threshold_basis) < 120:
        basis_ref = f" {threshold_basis.rstrip('.')}."

    return {
        "TRIGGERED_RED": (
            f"{{company}} {name} at {{value}}{red_threshold} signals elevated "
            f"{primary_theory} risk{factor_ref}{peril_ref}. "
            f"This {rap_desc} has historically correlated with increased D&O claim "
            f"frequency and severity.{basis_ref}"
        ),
        "TRIGGERED_YELLOW": (
            f"{{company}} {name} at {{value}}{yellow_threshold} is in the caution "
            f"zone for {primary_theory}{factor_ref}. Monitor for deterioration — "
            f"trend direction and peer comparison inform the D&O risk assessment."
        ),
        "CLEAR": (
            f"{{company}} {name} at {{value}} is within acceptable range for "
            f"{primary_theory}{factor_ref} — this level is a protective factor "
            f"in D&O risk assessment, reducing claim probability."
        ),
    }


# ---------------------------------------------------------------------------
# LLM-based template generation (optional, via anthropic SDK)
# ---------------------------------------------------------------------------


def generate_do_context_llm(
    signals_batch: list[dict[str, Any]],
    client: Any,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, dict[str, str]]:
    """Generate do_context templates using Claude API for a batch of signals.

    Args:
        signals_batch: List of signal dicts to generate templates for.
        client: Anthropic client instance.
        model: Model to use for generation.

    Returns:
        Dict mapping signal_id -> {TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR}.
    """
    # Build the batch prompt
    signal_descriptions = []
    for sig in signals_batch:
        factors = sig.get("factors", [])
        factor_theories = []
        for f in factors:
            key = f.split("_")[0].replace(".", "")
            if key in FACTOR_TO_THEORY:
                factor_theories.append(f"  - {key}: {FACTOR_TO_THEORY[key]}")

        peril_ids = sig.get("peril_ids", [])
        peril_descs = [f"  - {p}: {PERIL_DESCRIPTIONS.get(p, p)}" for p in peril_ids]

        threshold = sig.get("threshold", {})
        epistemology = sig.get("epistemology", {})

        desc = f"""Signal: {sig['id']}
Name: {sig['name']}
Work Type: {sig.get('work_type', 'evaluate')}
RAP Class: {sig.get('rap_class', 'host')} ({RAP_CLASS_CONTEXT.get(sig.get('rap_class', 'host'), '')})
RAP Subcategory: {sig.get('rap_subcategory', '')}
Factors:
{chr(10).join(factor_theories) if factor_theories else '  (none)'}
Peril IDs:
{chr(10).join(peril_descs) if peril_descs else '  (none)'}
Threshold Type: {threshold.get('type', 'unknown')}
Threshold Red: {threshold.get('red', 'N/A')}
Threshold Yellow: {threshold.get('yellow', 'N/A')}
Threshold Clear: {threshold.get('clear', 'N/A')}
Rule Origin: {epistemology.get('rule_origin', 'N/A')}
Threshold Basis: {epistemology.get('threshold_basis', 'N/A')}"""
        signal_descriptions.append(desc)

    prompt = f"""Generate D&O underwriting commentary templates for the following brain signals. These templates will be rendered in a D&O liability underwriting worksheet to help underwriters assess risk.

For EACH signal, generate exactly 3 templates:
- TRIGGERED_RED: Most severe — the signal is in the danger zone. Explain the specific D&O claim exposure.
- TRIGGERED_YELLOW: Moderate concern — the signal is in the caution zone. Explain what to monitor.
- CLEAR: Signal is clean — explain why this is a protective factor for D&O risk.

REQUIREMENTS (STRICT):
1. Every template MUST use at least one of: {{value}}, {{company}}, {{evidence}}
2. Every template MUST reference the specific D&O litigation theory (Securities Class Action, derivative suit, breach of fiduciary duty, etc.) that the signal maps to via its factors
3. Templates must be 1-3 sentences. Company-specific when rendered — no generic boilerplate.
4. BANNED phrases: "elevated risk", "warrants attention", "notable concern", "significant implications", "requires monitoring" — use precise D&O language instead
5. RED templates should cite the specific claim type (SCA, derivative, Caremark, Section 10(b), etc.)
6. For info/display type signals, explain the indirect D&O relevance

SIGNALS:

{chr(10).join(f'---{chr(10)}{d}' for d in signal_descriptions)}

OUTPUT FORMAT (JSON):
Return a JSON object mapping signal_id to template dict. Example:
{{
  "FIN.FORENSIC.example": {{
    "TRIGGERED_RED": "{{company}} example at {{value}} signals...",
    "TRIGGERED_YELLOW": "{{company}} example at {{value}} is in...",
    "CLEAR": "{{company}} example at {{value}} is within..."
  }}
}}

Return ONLY the JSON object, no markdown fences or explanation."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        # Fall back to deterministic generation
        result = {}
        for sig in signals_batch:
            result[sig["id"]] = generate_do_context_deterministic(sig)
        return result


# ---------------------------------------------------------------------------
# YAML file processing
# ---------------------------------------------------------------------------


def load_yaml_file(path: Path) -> tuple[Any, YAML]:
    """Load a YAML file with ruamel.yaml for round-trip preservation."""
    yml = YAML()
    yml.preserve_quotes = True
    yml.width = 120
    with open(path) as f:
        data = yml.load(f)
    return data, yml


def save_yaml_file(path: Path, data: Any, yml: YAML) -> None:
    """Save YAML file preserving structure."""
    with open(path, "w") as f:
        yml.dump(data, f)


def signal_has_do_context(signal: dict[str, Any] | CommentedMap) -> bool:
    """Check if a signal already has do_context templates."""
    pres = signal.get("presentation")
    if pres is None:
        return False
    if isinstance(pres, (dict, CommentedMap)):
        dc = pres.get("do_context")
        return bool(dc and isinstance(dc, (dict, CommentedMap)) and len(dc) > 0)
    return False


def _add_do_context_to_signal(
    signal: CommentedMap,
    templates: dict[str, str],
) -> None:
    """Add do_context templates to a signal's presentation block."""
    if "presentation" not in signal or signal["presentation"] is None:
        signal["presentation"] = CommentedMap()

    pres = signal["presentation"]
    if not isinstance(pres, CommentedMap):
        # Convert plain dict to CommentedMap
        new_pres = CommentedMap()
        for k, v in pres.items():
            new_pres[k] = v
        signal["presentation"] = new_pres
        pres = signal["presentation"]

    dc = CommentedMap()
    # Order: TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR (matches exemplar)
    for key in ("TRIGGERED_RED", "TRIGGERED_YELLOW", "CLEAR"):
        if key in templates:
            dc[key] = templates[key]

    pres["do_context"] = dc


def process_yaml_file(
    path: Path,
    *,
    dry_run: bool = False,
    validate_only: bool = False,
    use_llm: bool = False,
    llm_client: Any = None,
    llm_model: str = "claude-sonnet-4-20250514",
) -> dict[str, Any]:
    """Process a single YAML file, generating do_context for signals that lack it.

    Returns stats dict with keys: total, skipped, generated, errors, file.
    """
    stats: dict[str, Any] = {
        "file": str(path),
        "total": 0,
        "skipped": 0,
        "generated": 0,
        "errors": [],
        "validated": 0,
        "validation_errors": [],
    }

    data, yml = load_yaml_file(path)
    if not isinstance(data, (list, CommentedSeq)):
        logger.warning("Skipping %s: not a signal list", path)
        return stats

    modified = False
    signals_needing_dc: list[tuple[int, CommentedMap]] = []

    for idx, signal in enumerate(data):
        stats["total"] += 1

        if validate_only:
            # Just validate existing do_context
            pres = signal.get("presentation")
            if pres and isinstance(pres, (dict, CommentedMap)):
                dc = pres.get("do_context")
                if dc and isinstance(dc, (dict, CommentedMap)):
                    for key, template in dc.items():
                        stats["validated"] += 1
                        errs = validate_do_context_template(str(template))
                        if errs:
                            stats["validation_errors"].append(
                                f"{signal.get('id', f'idx={idx}')}.{key}: {'; '.join(errs)}"
                            )
            continue

        if signal_has_do_context(signal):
            stats["skipped"] += 1
            continue

        signals_needing_dc.append((idx, signal))

    if validate_only:
        return stats

    if not signals_needing_dc:
        return stats

    # Generate templates
    if use_llm and llm_client:
        # Batch LLM generation (up to 20 signals per call)
        batch_size = 15
        for batch_start in range(0, len(signals_needing_dc), batch_size):
            batch = signals_needing_dc[batch_start : batch_start + batch_size]
            sig_dicts = [dict(s) for _, s in batch]
            try:
                results = generate_do_context_llm(sig_dicts, llm_client, llm_model)
            except Exception as e:
                logger.error("LLM batch failed, falling back: %s", e)
                results = {}
                for _, sig in batch:
                    results[sig["id"]] = generate_do_context_deterministic(dict(sig))

            for idx, signal in batch:
                sig_id = signal.get("id", f"idx={idx}")
                templates = results.get(sig_id)
                if not templates:
                    templates = generate_do_context_deterministic(dict(signal))

                # Validate before writing
                valid = True
                for key, tmpl in templates.items():
                    errs = validate_do_context_template(tmpl)
                    if errs:
                        stats["errors"].append(f"{sig_id}.{key}: {'; '.join(errs)}")
                        valid = False

                if valid and not dry_run:
                    _add_do_context_to_signal(signal, templates)
                    modified = True
                    stats["generated"] += 1
                elif valid:
                    stats["generated"] += 1
                    logger.info("[DRY RUN] Would generate do_context for %s", sig_id)

            # Rate limiting for LLM calls
            if use_llm and batch_start + batch_size < len(signals_needing_dc):
                time.sleep(1)
    else:
        # Deterministic generation
        for idx, signal in signals_needing_dc:
            sig_id = signal.get("id", f"idx={idx}")
            templates = generate_do_context_deterministic(dict(signal))

            # Validate before writing
            valid = True
            for key, tmpl in templates.items():
                errs = validate_do_context_template(tmpl)
                if errs:
                    stats["errors"].append(f"{sig_id}.{key}: {'; '.join(errs)}")
                    valid = False

            if valid and not dry_run:
                _add_do_context_to_signal(signal, templates)
                modified = True
                stats["generated"] += 1
            elif valid:
                stats["generated"] += 1
                if dry_run:
                    logger.info("[DRY RUN] Would generate do_context for %s", sig_id)

    # Write back if modified
    if modified and not dry_run:
        save_yaml_file(path, data, yml)
        logger.info("Wrote %d do_context templates to %s", stats["generated"], path)

    return stats


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def get_signal_yaml_files(base_dir: Path | None = None) -> list[Path]:
    """Get all signal YAML files from the brain signals directory."""
    if base_dir is None:
        base_dir = PROJECT_ROOT / "src" / "do_uw" / "brain" / "signals"
    files = sorted(base_dir.rglob("*.yaml"))
    return files


def main() -> int:
    """Main entry point for batch do_context generation."""
    parser = argparse.ArgumentParser(
        description="Batch generate D&O do_context templates for brain signals"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Just validate existing do_context templates",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a single YAML file instead of all",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use Claude API for generation (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use for LLM generation",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Get files to process
    if args.file:
        if not args.file.exists():
            logger.error("File not found: %s", args.file)
            return 1
        yaml_files = [args.file]
    else:
        yaml_files = get_signal_yaml_files()
        logger.info("Found %d signal YAML files", len(yaml_files))

    # Set up LLM client if needed
    llm_client = None
    if args.use_llm:
        try:
            import anthropic
            llm_client = anthropic.Anthropic()
            logger.info("Using Claude API for generation (model: %s)", args.model)
        except Exception as e:
            logger.error("Failed to initialize Anthropic client: %s", e)
            logger.info("Falling back to deterministic generation")

    # Process files
    totals = {
        "files": 0,
        "total_signals": 0,
        "skipped": 0,
        "generated": 0,
        "errors": [],
        "validated": 0,
        "validation_errors": [],
    }

    for path in yaml_files:
        stats = process_yaml_file(
            path,
            dry_run=args.dry_run,
            validate_only=args.validate_only,
            use_llm=args.use_llm,
            llm_client=llm_client,
            llm_model=args.model,
        )
        totals["files"] += 1
        totals["total_signals"] += stats["total"]
        totals["skipped"] += stats["skipped"]
        totals["generated"] += stats["generated"]
        totals["errors"].extend(stats["errors"])
        totals["validated"] += stats["validated"]
        totals["validation_errors"].extend(stats["validation_errors"])

    # Print summary
    print("\n" + "=" * 60)
    print("BATCH DO_CONTEXT GENERATION SUMMARY")
    print("=" * 60)
    print(f"Files processed:     {totals['files']}")
    print(f"Total signals:       {totals['total_signals']}")

    if args.validate_only:
        print(f"Templates validated: {totals['validated']}")
        if totals["validation_errors"]:
            print(f"Validation errors:   {len(totals['validation_errors'])}")
            for err in totals["validation_errors"]:
                print(f"  ERROR: {err}")
            return 1
        else:
            print("All templates pass validation.")
            return 0

    print(f"Already had dc:      {totals['skipped']}")
    print(f"Generated:           {totals['generated']}")
    if totals["errors"]:
        print(f"Errors:              {len(totals['errors'])}")
        for err in totals["errors"]:
            print(f"  ERROR: {err}")
        return 1

    if args.dry_run:
        print("\n(DRY RUN — no files were modified)")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
