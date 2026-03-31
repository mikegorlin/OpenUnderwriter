"""Brain structural audit: staleness, coverage, threshold conflicts, orphans.

Inspects brain signal definitions for structural health issues:
- Staleness: signals not calibrated in >180 days
- Coverage: peril coverage gaps (reports NOT AVAILABLE when peril_id is NULL)
- Threshold conflicts: overlapping red/yellow/clear ranges in numeric thresholds
- Orphaned signals: active signals not assigned to any facet

Signal definitions from YAML (source of truth, via BrainLoader).
DuckDB no longer needed for definition data.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Staleness thresholds (module-level constants, not hardcoded in logic)
# ---------------------------------------------------------------------------

STALE_THRESHOLD_DAYS = 180
VERY_STALE_THRESHOLD_DAYS = 365

# Threshold types that support numeric conflict detection
NUMERIC_THRESHOLD_TYPES = frozenset({"tiered_threshold", "numeric_threshold", "tiered"})


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AuditFinding(BaseModel):
    """A single audit finding."""

    category: str  # "STALENESS", "COVERAGE", "THRESHOLD", "ORPHAN"
    severity: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    signal_id: str = ""
    message: str
    detail: str = ""


class BrainAuditReport(BaseModel):
    """Aggregated brain audit report."""

    findings: list[AuditFinding] = Field(default_factory=list)
    total_stale: int = 0
    total_threshold_issues: int = 0
    total_orphaned: int = 0
    peril_coverage_available: bool = False
    summary: str = "No structural issues found"

    # Staleness breakdown
    never_calibrated: int = 0
    very_stale: int = 0  # > 365 days
    stale: int = 0  # 180-365 days
    fresh: int = 0  # < 180 days

    # Top stale signals (for display)
    top_stale_signals: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------


def _check_staleness(
    active_signals: list[dict[str, Any]],
) -> tuple[list[AuditFinding], dict[str, int], list[dict[str, Any]]]:
    """Check signal calibration staleness from YAML data.

    Returns:
        Tuple of (findings, staleness_counts, top_stale_signals)
    """
    findings: list[AuditFinding] = []
    counts = {
        "never_calibrated": 0,
        "very_stale": 0,
        "stale": 0,
        "fresh": 0,
    }

    now = datetime.now(UTC).date()
    stale_boundary = now - timedelta(days=STALE_THRESHOLD_DAYS)
    very_stale_boundary = now - timedelta(days=VERY_STALE_THRESHOLD_DAYS)

    dated_signals: list[tuple[str, datetime]] = []

    for sig in active_signals:
        signal_id = sig.get("id", "")
        prov = sig.get("provenance", {}) or {}
        last_validated = prov.get("last_validated")

        if last_validated is None:
            counts["never_calibrated"] += 1
        else:
            try:
                if isinstance(last_validated, str):
                    cal_date = datetime.fromisoformat(last_validated).date()
                else:
                    cal_date = last_validated
                dated_signals.append((signal_id, cal_date))
                if cal_date < very_stale_boundary:
                    counts["very_stale"] += 1
                elif cal_date < stale_boundary:
                    counts["stale"] += 1
                else:
                    counts["fresh"] += 1
            except (ValueError, TypeError):
                counts["never_calibrated"] += 1

    # Report as a single finding with counts (not per-signal -- too noisy)
    if counts["never_calibrated"] > 0:
        findings.append(
            AuditFinding(
                category="STALENESS",
                severity="MEDIUM",
                message=(
                    f"{counts['never_calibrated']} signals never calibrated"
                ),
                detail="provenance.last_validated is NULL for these signals",
            )
        )

    if counts["very_stale"] > 0:
        findings.append(
            AuditFinding(
                category="STALENESS",
                severity="MEDIUM",
                message=f"{counts['very_stale']} signals stale > 365 days",
                detail="last_validated older than 1 year",
            )
        )

    if counts["stale"] > 0:
        findings.append(
            AuditFinding(
                category="STALENESS",
                severity="LOW",
                message=f"{counts['stale']} signals stale 180-365 days",
                detail="last_validated between 180-365 days ago",
            )
        )

    # Top 10 oldest calibrated signals (non-NULL)
    dated_signals.sort(key=lambda x: x[1])
    top_stale_signals = [
        {"signal_id": s, "last_calibrated": str(c)}
        for s, c in dated_signals[:10]
    ]

    return findings, counts, top_stale_signals


# ---------------------------------------------------------------------------
# Peril coverage check
# ---------------------------------------------------------------------------


def _check_peril_coverage(
    active_signals: list[dict[str, Any]],
) -> tuple[list[AuditFinding], bool]:
    """Check peril coverage from YAML. Reports NOT AVAILABLE when peril_id is NULL.

    Computes coverage matrix from YAML signals and perils directly
    (no DuckDB view needed).
    """
    from do_uw.brain.brain_unified_loader import load_perils

    findings: list[AuditFinding] = []

    total_active = len(active_signals)
    with_peril = sum(
        1 for s in active_signals
        if s.get("peril_ids") and len(s["peril_ids"]) > 0
    )

    if with_peril == 0:
        findings.append(
            AuditFinding(
                category="COVERAGE",
                severity="INFO",
                message=(
                    f"Peril coverage: NOT AVAILABLE "
                    f"(0/{total_active} signals have peril assignments)"
                ),
                detail="Peril IDs not yet populated in signal YAML",
            )
        )
        return findings, False

    # Compute coverage from YAML: count signals per peril
    perils = load_perils()
    peril_signal_count: dict[str, int] = {}
    for sig in active_signals:
        for pid in (sig.get("peril_ids") or []):
            peril_signal_count[pid] = peril_signal_count.get(pid, 0) + 1

    for peril in perils:
        pid = peril.get("peril_id", peril.get("id", ""))
        pname = peril.get("name", pid)
        count = peril_signal_count.get(pid, 0)

        if count == 0:
            coverage_level = "GAP"
        elif count < 3:
            coverage_level = "THIN"
        else:
            continue  # Adequate or better

        severity = "HIGH" if coverage_level == "GAP" else "MEDIUM"
        findings.append(
            AuditFinding(
                category="COVERAGE",
                severity=severity,
                message=(
                    f"Peril '{pname}' has {coverage_level} coverage "
                    f"({count} signals)"
                ),
                detail=f"peril_id: {pid}",
            )
        )

    return findings, True


# ---------------------------------------------------------------------------
# Threshold conflict detection
# ---------------------------------------------------------------------------


def _parse_numeric_value(s: str) -> float | None:
    """Try to extract a numeric value from a threshold string like '>10' or '<5.0'."""
    if not s:
        return None
    # Strip comparison operators and whitespace
    cleaned = s.strip().lstrip("><=!").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _check_threshold_conflicts(
    active_signals: list[dict[str, Any]],
) -> list[AuditFinding]:
    """Detect threshold conflicts in numeric threshold types only.

    A conflict is when red/yellow/clear ranges overlap in unexpected ways.
    Only checks tiered_threshold and numeric_threshold types.
    Reads from YAML signal definitions (source of truth).
    """
    findings: list[AuditFinding] = []

    for sig in active_signals:
        signal_id = sig.get("id", "")
        threshold = sig.get("threshold", {})
        if not threshold or not isinstance(threshold, dict):
            continue
        threshold_type = threshold.get("type", "")
        threshold_full_raw = threshold
        # Only check numeric threshold types
        if threshold_type not in NUMERIC_THRESHOLD_TYPES:
            continue

        # Parse threshold_full JSON
        if threshold_full_raw is None:
            continue

        try:
            if isinstance(threshold_full_raw, str):
                threshold = json.loads(threshold_full_raw)
            else:
                threshold = threshold_full_raw
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(threshold, dict):
            continue

        red_str = threshold.get("red", "")
        yellow_str = threshold.get("yellow", "")

        if not red_str or not yellow_str:
            continue

        # Try to extract numeric values for comparison
        red_val = _parse_numeric_value(str(red_str))
        yellow_val = _parse_numeric_value(str(yellow_str))

        if red_val is None or yellow_val is None:
            continue

        # For "higher is worse" signals (e.g., debt ratio):
        #   red threshold should be >= yellow threshold
        #   Example: red: ">10", yellow: ">5" (correct)
        #   Conflict: red: ">5", yellow: ">10" (yellow harder to trigger than red)
        #
        # For "lower is worse" signals (e.g., margins):
        #   red threshold should be <= yellow threshold
        #   Example: red: "<10%", yellow: "<20%" (correct)
        #   Conflict: red: "<20%", yellow: "<10%" (yellow harder to trigger than red)
        #
        # Detect the direction from the comparison operator
        red_is_greater = ">" in str(red_str) and "<" not in str(red_str)
        yellow_is_greater = ">" in str(yellow_str) and "<" not in str(yellow_str)

        # Only flag if both use same direction operator
        if red_is_greater and yellow_is_greater:
            # "Higher is worse": red should have LOWER threshold than yellow
            # (easier to trigger = lower number for > comparison)
            # Actually: red: ">10" triggers for 11+, yellow: ">5" triggers for 6+
            # So yellow captures more cases -- yellow should be lower
            # red_val > yellow_val means red is HARDER to trigger than yellow
            # That could be intentional (red = extreme, yellow = moderate)
            # A conflict is: yellow_val > red_val (yellow harder to trigger than red)
            if yellow_val > red_val:
                findings.append(
                    AuditFinding(
                        category="THRESHOLD",
                        severity="MEDIUM",
                        signal_id=signal_id,
                        message=(
                            f"Threshold conflict: yellow ({yellow_str}) is harder "
                            f"to trigger than red ({red_str})"
                        ),
                        detail=f"threshold_type: {threshold_type}",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Orphaned signal check
# ---------------------------------------------------------------------------


def _check_orphaned_signals(
    active_signals: list[dict[str, Any]],
) -> list[AuditFinding]:
    """Find active signals not assigned to any facet. Uses output manifest."""
    findings: list[AuditFinding] = []

    # Load manifest (source of truth for group-signal wiring)
    from do_uw.brain.manifest_schema import collect_signals_by_group, load_manifest

    manifest = load_manifest()
    # V3: signals self-select into groups via their `group` field
    sig_groups = collect_signals_by_group(active_signals)
    manifest_group_ids = {g.id for s in manifest.sections for g in s.groups}
    facet_signal_ids: set[str] = set()
    for gid, sig_ids in sig_groups.items():
        if gid in manifest_group_ids:
            facet_signal_ids.update(sig_ids)

    # Get active signal IDs from YAML (source of truth)
    active_ids = {s["id"] for s in active_signals}

    # Find orphans: in YAML but not in any manifest group
    orphaned = sorted(active_ids - facet_signal_ids)

    if orphaned:
        findings.append(
            AuditFinding(
                category="ORPHAN",
                severity="LOW",
                message=f"{len(orphaned)} active signals not in any facet",
                detail=", ".join(orphaned[:20])
                + ("..." if len(orphaned) > 20 else ""),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------


def compute_brain_audit(
    conn: Any = None,
) -> BrainAuditReport:
    """Compute brain structural audit report.

    Signal definitions from YAML (source of truth, via BrainLoader).
    DuckDB conn parameter kept for backward compat but no longer used.

    Checks: staleness, peril coverage, threshold conflicts, orphaned signals.
    All read-only.

    Args:
        conn: Deprecated. No longer used (DuckDB not needed for audit).

    Returns:
        BrainAuditReport with all findings.
    """
    from do_uw.brain.brain_unified_loader import load_signals

    # Load signal definitions from YAML (source of truth)
    signals_data = load_signals()
    all_signals = signals_data.get("signals", [])
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]

    all_findings: list[AuditFinding] = []

    # Staleness (from YAML provenance.last_validated)
    stale_findings, stale_counts, top_stale = _check_staleness(active_signals)
    all_findings.extend(stale_findings)

    # Peril coverage (from YAML signals + perils)
    coverage_findings, peril_available = _check_peril_coverage(active_signals)
    all_findings.extend(coverage_findings)

    # Threshold conflicts (from YAML threshold definitions)
    threshold_findings = _check_threshold_conflicts(active_signals)
    all_findings.extend(threshold_findings)

    # Orphaned signals (YAML vs facet YAML)
    orphan_findings = _check_orphaned_signals(active_signals)
    all_findings.extend(orphan_findings)

    # Count by category
    total_stale = (
        stale_counts["never_calibrated"]
        + stale_counts["very_stale"]
        + stale_counts["stale"]
    )
    total_threshold = len(threshold_findings)
    total_orphaned = sum(
        1 for f in orphan_findings if f.category == "ORPHAN"
    )
    # Get actual orphan count from the finding detail
    orphan_count = 0
    for f in orphan_findings:
        if f.category == "ORPHAN":
            # Extract number from "N active signals not in any facet"
            try:
                orphan_count = int(f.message.split()[0])
            except (ValueError, IndexError):
                pass

    # Summary
    high_count = sum(1 for f in all_findings if f.severity == "HIGH")
    medium_count = sum(1 for f in all_findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in all_findings if f.severity == "LOW")
    info_count = sum(1 for f in all_findings if f.severity == "INFO")

    total_findings = len(all_findings)
    if total_findings == 0:
        summary = "No structural issues found"
    else:
        parts = []
        if high_count:
            parts.append(f"{high_count} high")
        if medium_count:
            parts.append(f"{medium_count} medium")
        if low_count:
            parts.append(f"{low_count} low")
        if info_count:
            parts.append(f"{info_count} info")
        summary = f"{total_findings} findings: {', '.join(parts)}"

    return BrainAuditReport(
        findings=all_findings,
        total_stale=total_stale,
        total_threshold_issues=total_threshold,
        total_orphaned=orphan_count,
        peril_coverage_available=peril_available,
        summary=summary,
        never_calibrated=stale_counts["never_calibrated"],
        very_stale=stale_counts["very_stale"],
        stale=stale_counts["stale"],
        fresh=stale_counts["fresh"],
        top_stale_signals=top_stale,
    )


# ---------------------------------------------------------------------------
# HTML audit report generation
# ---------------------------------------------------------------------------


def _build_signal_row(sig: dict[str, Any]) -> dict[str, Any]:
    """Transform a raw signal dict into a template-friendly row dict."""
    prov = sig.get("provenance", {}) or {}
    tp = prov.get("threshold_provenance") or {}
    if isinstance(tp, str):
        tp = {"source": tp}

    threshold = sig.get("threshold", {}) or {}
    threshold_parts: list[str] = []
    if isinstance(threshold, dict):
        for k in ("type", "red", "yellow", "clear", "triggered"):
            v = threshold.get(k)
            if v is not None:
                threshold_parts.append(f"{k}: {v}")

    depends_on = sig.get("depends_on", []) or []
    deps_display = ", ".join(
        d.get("signal", d) if isinstance(d, dict) else str(d)
        for d in depends_on
    ) if depends_on else ""

    tp_source = tp.get("source", "") if isinstance(tp, dict) else ""
    is_unattributed = tp_source in ("unattributed", "") or not tp_source

    return {
        "id": sig.get("id", ""),
        "name": sig.get("name", ""),
        "signal_class": sig.get("signal_class", "evaluative"),
        "tier": sig.get("tier", 0),
        "group": sig.get("group", ""),
        "data_source": prov.get("data_source", ""),
        "formula": prov.get("formula", ""),
        "threshold_prov_source": tp_source,
        "threshold_prov_rationale": tp.get("rationale", "") if isinstance(tp, dict) else "",
        "render_target": prov.get("render_target", ""),
        "is_unattributed": is_unattributed,
        "field_path": sig.get("field_path", ""),
        "depends_on_display": deps_display,
        "provenance_origin": prov.get("origin", ""),
        "schema_version": sig.get("schema_version", 1),
        "threshold_display": "; ".join(threshold_parts),
    }


def _compute_coverage_fields(
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute provenance coverage statistics for the template."""
    total = len(signals) if signals else 1  # avoid div-by-zero

    def _count_populated(field_getter: Any) -> int:
        return sum(1 for s in signals if field_getter(s))

    fields = [
        ("data_source", lambda s: (s.get("provenance") or {}).get("data_source", "")),
        ("formula", lambda s: (s.get("provenance") or {}).get("formula", "")),
        ("threshold_provenance", lambda s: _has_threshold_prov(s)),
        ("render_target", lambda s: (s.get("provenance") or {}).get("render_target", "")),
        ("group", lambda s: s.get("group", "")),
        ("field_path", lambda s: s.get("field_path", "")),
        ("depends_on", lambda s: bool(s.get("depends_on"))),
    ]

    result = []
    for name, getter in fields:
        populated = _count_populated(getter)
        empty = len(signals) - populated
        pct = (populated / total) * 100 if total else 0
        result.append({
            "name": name,
            "populated": populated,
            "empty": empty,
            "pct": pct,
        })
    return result


def _has_threshold_prov(sig: dict[str, Any]) -> bool:
    """Check if a signal has non-empty threshold provenance."""
    prov = sig.get("provenance", {}) or {}
    tp = prov.get("threshold_provenance")
    if not tp:
        return False
    if isinstance(tp, dict):
        src = tp.get("source", "")
        return bool(src) and src != "unattributed"
    return bool(tp)


def generate_audit_html(output_path: Path | None = None) -> Path:
    """Generate an institutional-quality HTML audit report for all brain signals.

    Loads all signals from YAML, groups by manifest section, and renders
    a filterable HTML report with provenance metadata and coverage stats.

    Args:
        output_path: Where to write the HTML file.
            Defaults to ``output/brain_audit_report.html``.

    Returns:
        The path to the generated HTML file.
    """
    from collections import Counter

    from jinja2 import Environment, FileSystemLoader

    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import load_manifest

    if output_path is None:
        output_path = Path("output") / "brain_audit_report.html"

    # Load signals
    signals_data = load_signals()
    all_signals = signals_data.get("signals", [])
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]

    # Load manifest for section ordering and grouping
    manifest = load_manifest()

    # Build signal-to-section mapping via manifest facets
    signal_to_section: dict[str, str] = {}
    section_meta: dict[str, str] = {}
    section_order: list[str] = []
    for ms in manifest.sections:
        section_meta[ms.id] = ms.name
        section_order.append(ms.id)
        # V3: map signals to sections via group membership
        for group in ms.groups:
            for sig in active_signals:
                if sig.get("group") == group.id:
                    signal_to_section[sig["id"]] = ms.id

    # Group signals by section
    sections_map: dict[str, list[dict[str, Any]]] = {}
    unassigned: list[dict[str, Any]] = []

    for sig in active_signals:
        sig_id = sig.get("id", "")
        section_id = signal_to_section.get(sig_id, "")
        row = _build_signal_row(sig)
        if section_id:
            sections_map.setdefault(section_id, []).append(row)
        else:
            unassigned.append(row)

    # Build ordered section list
    sections: list[dict[str, Any]] = []
    for sid in section_order:
        if sid in sections_map:
            sections.append({
                "id": sid,
                "name": section_meta.get(sid, sid),
                "signals": sorted(sections_map[sid], key=lambda s: s["id"]),
            })

    # Add unassigned signals section
    if unassigned:
        sections.append({
            "id": "unassigned",
            "name": "Unassigned (No Manifest Section)",
            "signals": sorted(unassigned, key=lambda s: s["id"]),
        })

    # Compute stats
    class_counter: Counter[str] = Counter()
    tier_counter: Counter[int] = Counter()
    for sig in active_signals:
        class_counter[sig.get("signal_class", "evaluative")] += 1
        tier_counter[sig.get("tier", 0)] += 1

    coverage_fields = _compute_coverage_fields(active_signals)

    # Render template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
    )
    template = env.get_template("audit_report.html")

    from datetime import UTC, datetime

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    html = template.render(
        generated_at=generated_at,
        total_signals=len(active_signals),
        section_count=len(sections),
        class_counts=class_counter,
        tier_counts=tier_counter,
        sections=sections,
        coverage_fields=coverage_fields,
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return output_path


__all__ = [
    "AuditFinding",
    "BrainAuditReport",
    "compute_brain_audit",
    "generate_audit_html",
]
