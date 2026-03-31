#!/usr/bin/env python3
"""Multi-ticker calibration baseline: before/after CRF ceiling comparison.

Loads existing state.json files from prior pipeline runs, re-scores each
ticker using the new size-conditioned + weighted-compounding CRF ceiling
logic, and produces a before/after comparison table plus JSON snapshot.

Usage:
    uv run python scripts/calibration_baseline.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Calibration ticker set (from 121-CONTEXT.md)
TICKERS = ["AAPL", "ANGI", "RPM", "HNGE", "EXPO", "V"]

# Tier ordering for distance calculation
TIER_ORDER = ["NO_TOUCH", "WALK", "WATCH", "WRITE", "WANT", "WIN"]


def find_state_json(ticker: str) -> Path | None:
    """Find the most recent state.json for a ticker in output/."""
    candidates: list[Path] = []
    for d in OUTPUT_DIR.iterdir():
        if not d.is_dir():
            continue
        # Match directories starting with ticker (e.g., "AAPL - Apple")
        dir_name = d.name.upper()
        if dir_name.startswith(ticker.upper()):
            # Find all state.json under this ticker directory
            for state_file in sorted(d.glob("*/state.json"), reverse=True):
                candidates.append(state_file)
    if not candidates:
        return None
    # Return most recent (sorted by parent directory name descending)
    return candidates[0]


def load_scoring_config() -> dict:
    """Load scoring.json from brain config."""
    config_path = PROJECT_ROOT / "src" / "do_uw" / "brain" / "config" / "scoring.json"
    with open(config_path) as f:
        return json.load(f)


def normalize_crf_id(raw_id: str) -> str:
    """Normalize CRF ID: CRF-001 -> CRF-1."""
    match = re.match(r"CRF-0*(\d+)", raw_id)
    if match:
        return f"CRF-{match.group(1)}"
    return raw_id


def resolve_crf_ceiling(
    crf_entry: dict, market_cap: float | None, analysis_results: dict | None = None
) -> tuple[int, str]:
    """Resolve CRF ceiling using size-severity matrix or distress graduation.

    Mirrors red_flag_gates._resolve_crf_ceiling() logic.
    """
    flat_ceiling = int(crf_entry.get("max_quality_score", 100))
    flat_tier = str(crf_entry.get("max_tier", ""))

    # Check for distress graduation (CRF-13)
    graduation = crf_entry.get("distress_graduation")
    if graduation is not None:
        ar = analysis_results or {}
        if ar.get("going_concern"):
            gc = graduation.get("going_concern", {})
            return int(gc.get("ceiling", flat_ceiling)), str(gc.get("max_tier", flat_tier))
        z_score = ar.get("altman_z_score")
        neg_eq = ar.get("negative_equity", False)
        if z_score is not None:
            severe = graduation.get("severe", {})
            if z_score <= float(severe.get("z_max", 1.0)) and neg_eq:
                return int(severe.get("ceiling", flat_ceiling)), str(severe.get("max_tier", flat_tier))
            distress = graduation.get("distress", {})
            if z_score <= float(distress.get("z_max", 1.81)):
                return int(distress.get("ceiling", flat_ceiling)), str(distress.get("max_tier", flat_tier))
            gray = graduation.get("gray", {})
            if z_score <= float(gray.get("z_max", 2.99)):
                return int(gray.get("ceiling", flat_ceiling)), str(gray.get("max_tier", flat_tier))
        return flat_ceiling, flat_tier

    # Check for size-severity matrix
    matrix = crf_entry.get("size_severity_matrix")
    if matrix is None or market_cap is None:
        return flat_ceiling, flat_tier

    for tier_name in ("mega_cap", "large_cap", "mid_cap", "small_cap", "micro_cap"):
        tier = matrix.get(tier_name)
        if tier is None:
            continue
        if market_cap >= float(tier["threshold_usd"]):
            return int(tier["ceiling"]), str(tier.get("max_tier", flat_tier))

    return flat_ceiling, flat_tier


def classify_tier_from_score(quality_score: float, tiers_config: list[dict]) -> str:
    """Classify a quality score into a tier name."""
    for tier_entry in tiers_config:
        min_score = int(tier_entry.get("min_score", 0))
        max_score = int(tier_entry.get("max_score", 100))
        if min_score <= quality_score <= max_score:
            return str(tier_entry.get("tier", "NO_TOUCH"))
    return "NO_TOUCH"


def compute_old_ceiling(
    red_flags: list[dict],
) -> tuple[float, str | None]:
    """Old ceiling logic: lowest ceiling wins (flat, no size conditioning)."""
    lowest = float("inf")
    binding_id: str | None = None
    for rf in red_flags:
        if rf.get("triggered") and rf.get("ceiling_applied") is not None:
            ceiling = float(rf["ceiling_applied"])
            if ceiling < lowest:
                lowest = ceiling
                binding_id = rf.get("flag_id")
    if lowest < float("inf"):
        return lowest, binding_id
    return float("inf"), None


def compute_new_ceiling(
    red_flags: list[dict],
    scoring_config: dict,
    market_cap: float | None,
    analysis_results: dict | None = None,
) -> tuple[float, str | None, list[dict]]:
    """New ceiling logic: size-conditioned + weighted compounding."""
    COMPOUNDING_FACTOR = 0.5
    MAX_COMPOUNDING_REDUCTION = 0.80
    COMPOUNDING_FLOOR = 5

    ceilings_cfg = scoring_config.get("critical_red_flag_ceilings", {}).get("ceilings", [])
    ceiling_lookup: dict[str, dict] = {}
    for c in ceilings_cfg:
        norm = normalize_crf_id(str(c.get("id", "")))
        ceiling_lookup[norm] = c

    triggered: list[tuple[str, int, float]] = []
    details: list[dict] = []

    for rf in red_flags:
        if not rf.get("triggered"):
            continue
        flag_id = rf.get("flag_id", "")
        norm_id = normalize_crf_id(flag_id)
        cfg = ceiling_lookup.get(norm_id, {})
        ceiling, tier = resolve_crf_ceiling(cfg, market_cap, analysis_results)
        weight = float(cfg.get("severity_weight", 0.15))
        triggered.append((norm_id, ceiling, weight))
        details.append({
            "crf_id": norm_id,
            "resolved_ceiling": ceiling,
            "resolved_tier": tier,
            "severity_weight": weight,
        })

    if not triggered:
        return float("inf"), None, []

    triggered.sort(key=lambda t: t[1])
    primary_id, primary_ceiling, _pw = triggered[0]

    total_reduction = 0.0
    for _crf_id, _ceiling, weight in triggered[1:]:
        total_reduction += weight * COMPOUNDING_FACTOR

    total_reduction = min(total_reduction, MAX_COMPOUNDING_REDUCTION)
    final_ceiling = max(COMPOUNDING_FLOOR, primary_ceiling * (1.0 - total_reduction))

    for i, d in enumerate(details):
        if d["crf_id"] == primary_id and i == 0:
            d["role"] = "primary"
        else:
            d["role"] = d.get("role", "additional")
        d["contribution"] = d["severity_weight"] * COMPOUNDING_FACTOR if d["role"] == "additional" else 0.0

    return final_ceiling, primary_id, details


def extract_analysis_results(state: dict) -> dict | None:
    """Extract analysis_results dict for distress graduation (CRF-13)."""
    analysis = state.get("analysis")
    if analysis is None:
        return None
    # Try to find Altman Z and going concern
    result: dict = {}
    forensics = analysis.get("forensic_composites") or {}
    if isinstance(forensics, dict):
        altman = forensics.get("altman_z_score")
        if altman is not None:
            result["altman_z_score"] = float(altman)
    # Going concern from extracted.financials
    extracted = state.get("extracted", {})
    financials = extracted.get("financials") if extracted else None
    if financials and isinstance(financials, dict):
        audit = financials.get("audit", {})
        gc = audit.get("going_concern")
        if gc is not None:
            gc_val = gc.get("value") if isinstance(gc, dict) else gc
            result["going_concern"] = bool(gc_val)
    return result if result else None


def format_market_cap(mc: float | None) -> str:
    """Format market cap in human-readable form."""
    if mc is None:
        return "N/A"
    if mc >= 1e12:
        return f"${mc / 1e12:,.1f}T"
    if mc >= 1e9:
        return f"${mc / 1e9:,.1f}B"
    if mc >= 1e6:
        return f"${mc / 1e6:,.0f}M"
    return f"${mc:,.0f}"


def tier_distance(tier_a: str, tier_b: str) -> int:
    """Number of tier steps between two tiers."""
    if tier_a not in TIER_ORDER or tier_b not in TIER_ORDER:
        return 0
    return abs(TIER_ORDER.index(tier_a) - TIER_ORDER.index(tier_b))


def main() -> None:
    scoring_config = load_scoring_config()
    tiers_config = scoring_config.get("tiers", [])

    results: dict[str, dict] = {}
    before_dist: dict[str, int] = {t: 0 for t in TIER_ORDER}
    after_dist: dict[str, int] = {t: 0 for t in TIER_ORDER}

    print()
    print("Calibration Baseline Report")
    print("=" * 100)
    print(
        f"{'Ticker':<10}| {'MktCap':<12}| {'Composite':>10} | "
        f"{'Before (Score/Tier)':<22}| {'After (Score/Tier)':<22}| "
        f"{'CRFs':>4} | {'Binding CRF':<12}"
    )
    print("-" * 100)

    for ticker in TICKERS:
        state_path = find_state_json(ticker)
        if state_path is None:
            print(f"{ticker:<10}| {'--':>12}| {'N/A':>10} | {'No state.json found -- needs pipeline run first'}")
            continue

        with open(state_path) as f:
            state = json.load(f)

        scoring = state.get("scoring", {})
        company = state.get("company", {})
        mc_data = company.get("market_cap", {})
        market_cap = mc_data.get("value") if isinstance(mc_data, dict) else None

        composite = scoring.get("composite_score", 0.0)
        red_flags = scoring.get("red_flags", [])
        n_triggered = sum(1 for rf in red_flags if rf.get("triggered"))

        # "Before" scores: old flat-ceiling logic
        old_ceiling, old_binding = compute_old_ceiling(red_flags)
        old_quality = min(composite, old_ceiling) if old_ceiling < float("inf") else composite
        old_tier = classify_tier_from_score(old_quality, tiers_config)

        # "After" scores: new size-conditioned + weighted compounding
        analysis_results = extract_analysis_results(state)
        new_ceiling, new_binding, ceiling_details = compute_new_ceiling(
            red_flags, scoring_config, market_cap, analysis_results,
        )
        new_quality = min(composite, new_ceiling) if new_ceiling < float("inf") else composite
        new_tier = classify_tier_from_score(new_quality, tiers_config)

        mc_fmt = format_market_cap(market_cap)
        before_str = f"{old_quality:.1f} / {old_tier}"
        after_str = f"{new_quality:.1f} / {new_tier}"
        binding_str = new_binding or "None"

        print(
            f"{ticker:<10}| {mc_fmt:<12}| {composite:>10.1f} | "
            f"{before_str:<22}| {after_str:<22}| "
            f"{n_triggered:>4} | {binding_str:<12}"
        )

        before_dist[old_tier] += 1
        after_dist[new_tier] += 1

        results[ticker] = {
            "state_path": str(state_path),
            "market_cap": market_cap,
            "composite": round(composite, 2),
            "before": {
                "quality_score": round(old_quality, 1),
                "tier": old_tier,
                "binding_crf": old_binding,
            },
            "after": {
                "quality_score": round(new_quality, 1),
                "tier": new_tier,
                "binding_crf": new_binding,
                "ceiling_details": ceiling_details,
            },
            "crfs_triggered": n_triggered,
        }

    print("-" * 100)
    print()

    # Distribution summary
    before_counts = {t: c for t, c in before_dist.items() if c > 0}
    after_counts = {t: c for t, c in after_dist.items() if c > 0}
    before_str = ", ".join(f"{t}={c}" for t, c in before_counts.items())
    after_str = ", ".join(f"{t}={c}" for t, c in after_counts.items())

    print("Tier Distribution:")
    print(f"  Before: {before_str} ({len(before_counts)} distinct tier{'s' if len(before_counts) != 1 else ''})")
    print(f"  After:  {after_str} ({len(after_counts)} distinct tier{'s' if len(after_counts) != 1 else ''})")
    print()

    # Differentiation check
    if "AAPL" in results and "ANGI" in results:
        aapl_tier = results["AAPL"]["after"]["tier"]
        angi_tier = results["ANGI"]["after"]["tier"]
        dist = tier_distance(aapl_tier, angi_tier)
        status = "PASS" if dist >= 2 else "FAIL"
        print(f"AAPL vs ANGI differentiation: {aapl_tier} vs {angi_tier} ({dist} tiers apart) [{status}]")
    else:
        print("AAPL vs ANGI differentiation: N/A (missing ticker data)")

    tier_spread = len(after_counts)
    spread_status = "PASS" if tier_spread >= 3 else "FAIL"
    print(f"Tier spread: {tier_spread} distinct tiers [{spread_status}]")
    print()

    # Save JSON
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scoring_config_version": scoring_config.get("version", "unknown"),
        "tickers": results,
        "distribution": {
            "before": {t: before_dist[t] for t in TIER_ORDER},
            "after": {t: after_dist[t] for t in TIER_ORDER},
        },
        "validation": {
            "aapl_angi_differentiation": (
                tier_distance(
                    results.get("AAPL", {}).get("after", {}).get("tier", ""),
                    results.get("ANGI", {}).get("after", {}).get("tier", ""),
                )
                if "AAPL" in results and "ANGI" in results
                else None
            ),
            "distinct_tiers_after": tier_spread,
        },
    }

    json_path = OUTPUT_DIR / "calibration_baseline.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved baseline to: {json_path}")


if __name__ == "__main__":
    main()
