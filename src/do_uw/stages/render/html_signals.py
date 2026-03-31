"""Signal result processing utilities for HTML rendering.

Extracted from html_renderer.py (Plan 43-04 500-line split rule).
Phase 84-03: Migrated from section YAML to manifest groups + signal self-selection.

Contains:
  - _group_signals_by_section: Groups signal_results dict by section prefix
  - _compute_coverage_stats: Computes per-section signal coverage statistics
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import (
    format_adaptive,
    humanize_check_evidence,
    humanize_field_name,
)
from do_uw.stages.render.html_footnotes import _SOURCE_LABELS

def _looks_like_raw_dump(text: str) -> bool:
    """Detect strings that are raw Python repr dumps (dicts, SourcedValue, etc)."""
    return (
        "SourcedValue" in text
        or ("{'maturity_schedule'" in text)
        or ("Qualitative check: value={" in text and len(text) > 200)
        or (text.startswith("{") and "datetime.datetime" in text)
    )


# Cached maps built lazily on first call.
_signal_to_prefix: dict[str, str] | None = None
_prefix_to_name: dict[str, str] | None = None
_facet_metadata_cache: dict[str, dict[str, str]] | None = None


def _reset_caches() -> None:
    """Reset module-level caches (for testing)."""
    global _signal_to_prefix, _prefix_to_name, _facet_metadata_cache
    _signal_to_prefix = None
    _prefix_to_name = None
    _facet_metadata_cache = None


def _build_signal_section_map() -> tuple[dict[str, str], dict[str, str]]:
    """Build signal-to-prefix and prefix-to-name maps from manifest + signal groups.

    Returns (signal_to_prefix, prefix_to_name) where:
    - signal_to_prefix maps each signal ID to its prefix (e.g. "BIZ")
    - prefix_to_name maps each prefix to its section display name (e.g. "Business Profile")

    Uses prefix-based grouping (derived from signal ID prefixes) for backward
    compatibility with HTML templates that reference keys like 'FIN', 'BIZ', etc.
    Section names are resolved via manifest sections.
    """
    global _signal_to_prefix, _prefix_to_name
    if _signal_to_prefix is not None and _prefix_to_name is not None:
        return _signal_to_prefix, _prefix_to_name

    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import load_manifest

    manifest = load_manifest()
    signals_data = load_signals()

    # Build group_id -> section_name mapping from manifest
    group_to_section_name: dict[str, str] = {}
    for ms in manifest.sections:
        for group in ms.groups:
            group_to_section_name[group.id] = ms.name

    # Build prefix -> section_name by examining signals in each manifest section
    # A signal like "BIZ.company_description" has prefix "BIZ"
    # Its group maps to a manifest section name like "Business Profile"
    prefix_to_section_name: dict[str, str] = {}
    sig_to_prefix: dict[str, str] = {}

    for sig in signals_data.get("signals", []):
        sig_id = sig.get("id", "")
        if "." not in sig_id:
            continue

        prefix = sig_id.split(".")[0]
        sig_to_prefix[sig_id] = prefix

        # Map prefix to display name via signal's group -> manifest section
        gid = sig.get("group", "")
        if gid and gid in group_to_section_name and prefix not in prefix_to_section_name:
            prefix_to_section_name[prefix] = group_to_section_name[gid]

    _signal_to_prefix = sig_to_prefix
    _prefix_to_name = prefix_to_section_name
    return _signal_to_prefix, _prefix_to_name


def _build_facet_metadata_cache() -> dict[str, dict[str, str]]:
    """Build cached signal_id -> {facet_id, facet_name} map from manifest groups.

    Each signal's group field maps to a manifest group, providing the
    group_id and group_name as facet metadata.
    """
    global _facet_metadata_cache
    if _facet_metadata_cache is not None:
        return _facet_metadata_cache

    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import load_manifest

    manifest = load_manifest()
    signals_data = load_signals()

    # Build group_id -> (group_id, group_name) from manifest
    group_meta: dict[str, tuple[str, str]] = {}
    for ms in manifest.sections:
        for group in ms.groups:
            group_meta[group.id] = (group.id, group.name)

    # Map each signal to its group metadata
    cache: dict[str, dict[str, str]] = {}
    for sig in signals_data.get("signals", []):
        sig_id = sig.get("id", "")
        gid = sig.get("group", "")
        if gid and gid in group_meta:
            gid_val, gname = group_meta[gid]
            cache[sig_id] = {"facet_id": gid_val, "facet_name": gname}

    _facet_metadata_cache = cache
    return _facet_metadata_cache


def _lookup_facet_metadata(signal_id: str) -> dict[str, str]:
    """Look up group_id and group_name for a signal from manifest groups."""
    cache = _build_facet_metadata_cache()
    return cache.get(signal_id, {"facet_id": "", "facet_name": ""})


def _format_signal_source(
    trace_data_source: str,
    raw_source: str,
    filing_date_lookup: dict[str, str],
) -> str:
    """Format source column for QA audit table.

    Priority:
    1. WEB sources (raw_source starts with "WEB") -> domain-truncated URL
    2. trace_data_source -> parse form type, look up date -> "10-K 2024-09-28"
    3. Fallback -> raw_source or "---"

    URL truncation: domain + path up to 35 chars, appending "..." if longer.
    Example: "WEB (reuters.com/tech/apple-lawsuit-very-long-path...)"
    """
    _WEB_MAX_LEN = 35

    if raw_source and raw_source.upper().startswith("WEB"):
        # Gap search or web-sourced check -- show domain + truncated path
        content = raw_source[len("WEB (gap) "):].strip() if "gap" in raw_source.lower() else raw_source
        # Extract domain from URL if present
        try:
            from urllib.parse import urlparse
            parsed = urlparse(content)
            if parsed.netloc:
                path_preview = (parsed.netloc + parsed.path)[:_WEB_MAX_LEN]
                if len(parsed.netloc + parsed.path) > _WEB_MAX_LEN:
                    path_preview += "..."
                return f"WEB ({path_preview})"
        except Exception:
            pass
        # Fallback: truncate raw_source directly
        truncated = raw_source[:_WEB_MAX_LEN + 5]
        if len(raw_source) > _WEB_MAX_LEN + 5:
            truncated += "..."
        return truncated

    if trace_data_source:
        # Parse first source from trace_data_source (may be ";" separated)
        first_chunk = trace_data_source.split(";")[0].strip()
        src_key = first_chunk.split(":")[0].strip() if ":" in first_chunk else first_chunk
        label = _SOURCE_LABELS.get(src_key, "")
        if label:
            date = filing_date_lookup.get(label, "")
            return f"{label} {date}".strip()

    return raw_source or "\u2014"


def _group_signals_by_section(
    signal_results: dict[str, Any],
    filing_date_lookup: dict[str, str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Group signal results by their section prefix.

    Returns dict keyed by prefix (BIZ, FIN, GOV, etc.)
    with list of signal result dicts including content_type.
    """
    lookup = filing_date_lookup or {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    signal_to_prefix, _ = _build_signal_section_map()

    for signal_id, result_data in signal_results.items():
        if not isinstance(result_data, dict):
            continue

        # Primary: signal-declared prefix from manifest mapping
        prefix = signal_to_prefix.get(signal_id)
        if prefix is None:
            # Fallback: infer from ID (undeclared signals)
            prefix = signal_id.split(".")[0] if "." in signal_id else "OTHER"
        if prefix not in grouped:
            grouped[prefix] = []

        # Format raw signal values for human display
        raw_val = result_data.get("value")
        if isinstance(raw_val, float):
            formatted_val = format_adaptive(raw_val)
        elif isinstance(raw_val, dict):
            # NLP readability etc. - stringify cleanly
            formatted_val = ", ".join(f"{k}: {v}" for k, v in raw_val.items())
        elif isinstance(raw_val, str) and _looks_like_raw_dump(raw_val):
            formatted_val = "Present"
        else:
            formatted_val = raw_val

        # Humanize signal evidence for display
        raw_evidence = result_data.get("evidence", "")
        if isinstance(raw_evidence, str) and _looks_like_raw_dump(raw_evidence):
            raw_evidence = "Data present"
        clean_evidence = humanize_check_evidence(raw_evidence)

        # Humanize signal name: "high_risk_jurisdiction:China" -> "High Risk Jurisdiction: China"
        raw_name = result_data.get("signal_name", signal_id)
        if ":" in raw_name and "_" in raw_name.split(":")[0]:
            parts = raw_name.split(":", 1)
            raw_name = f"{humanize_field_name(parts[0])}:{parts[1]}"

        # Format source column for QA audit table: "10-K 2024-09-28" or "WEB (domain.com/...)"
        trace_src = result_data.get("trace_data_source", "")
        filing_ref = _format_signal_source(
            trace_data_source=trace_src,
            raw_source=result_data.get("source", ""),
            filing_date_lookup=lookup,
        )

        # Look up facet metadata (additive parallel classification)
        facet_meta = _lookup_facet_metadata(signal_id)

        grouped[prefix].append({
            "signal_id": signal_id,
            "signal_name": raw_name,
            "status": result_data.get("status", "INFO"),
            "value": formatted_val,
            "evidence": clean_evidence,
            "content_type": result_data.get("content_type", "EVALUATIVE_CHECK"),
            "source": result_data.get("source", ""),
            "confidence": result_data.get("confidence", ""),
            "data_status": result_data.get("data_status", "EVALUATED"),
            "data_status_reason": result_data.get("data_status_reason", ""),
            "factors": result_data.get("factors", []),
            "filing_ref": filing_ref,
            "trace_data_source": trace_src,
            # Facet metadata from manifest groups
            "facet_id": facet_meta["facet_id"],
            "facet_name": facet_meta["facet_name"],
            # D&O context from brain YAML do_context templates
            "do_context": result_data.get("do_context", ""),
        })

    return grouped


def _compute_coverage_stats(
    signal_results: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Compute per-section signal coverage statistics.

    Returns:
        (overall_stats, per_section_stats)
    """
    section_counts: dict[str, dict[str, int]] = {}
    total = 0
    total_evaluated = 0
    total_skipped = 0
    total_deferred = 0
    _, prefix_to_name = _build_signal_section_map()

    for signal_id, result_data in signal_results.items():
        if not isinstance(result_data, dict):
            continue

        total += 1
        prefix = signal_id.split(".")[0] if "." in signal_id else "OTHER"
        section_name = prefix_to_name.get(prefix, prefix)

        if section_name not in section_counts:
            section_counts[section_name] = {
                "total": 0, "evaluated": 0, "skipped": 0, "info": 0,
                "deferred": 0,
            }

        section_counts[section_name]["total"] += 1
        status = result_data.get("status", "INFO")
        data_status = result_data.get("data_status", "EVALUATED")

        if data_status == "DEFERRED":
            total_deferred += 1
            section_counts[section_name]["deferred"] += 1
        elif data_status == "EVALUATED":
            total_evaluated += 1
            section_counts[section_name]["evaluated"] += 1
        elif status == "SKIPPED" or data_status == "DATA_UNAVAILABLE":
            total_skipped += 1
            section_counts[section_name]["skipped"] += 1
        elif status == "INFO":
            section_counts[section_name]["info"] += 1
            total_evaluated += 1
            section_counts[section_name]["evaluated"] += 1

    overall = {
        "total": total,
        "evaluated": total_evaluated,
        "skipped": total_skipped,
        "deferred": total_deferred,
        "coverage_pct": f"{total_evaluated / total * 100:.0f}" if total > 0 else "0",
    }

    per_section: dict[str, dict[str, Any]] = {}
    for name, counts in section_counts.items():
        sec_total = counts["total"]
        sec_eval = counts["evaluated"]
        per_section[name] = {
            **counts,
            "coverage_pct": round(sec_eval / sec_total * 100) if sec_total > 0 else 0,
        }

    return overall, per_section


__all__ = [
    "_build_signal_section_map",
    "_compute_coverage_stats",
    "_format_signal_source",
    "_group_signals_by_section",
    "_lookup_facet_metadata",
    "_reset_caches",
]
