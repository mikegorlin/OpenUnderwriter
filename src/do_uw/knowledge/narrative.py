"""Narrative composition for grouping checks into risk stories.

Transforms individual check signals into coherent risk stories
that underwriters can present to stakeholders. Uses pre-defined
narrative templates that activate when enough component checks
fire in an analysis run.

Templates cover 7 core risk narratives: restatement risk,
event-driven claims, governance failure, regulatory exposure,
financial distress, insider trading patterns, and acquisition risk.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from do_uw.knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


@dataclass
class NarrativeStory:
    """A composed risk narrative grouping related checks.

    Represents a coherent risk story assembled from individual
    check signals that fired during an analysis run.
    """

    story_id: str
    title: str
    description: str
    checks: list[str]
    factors_affected: list[str]
    allegation_types: list[str]
    severity: str
    evidence_summary: str


# Pre-defined narrative templates
# Each template defines:
#   title: Human-readable story name
#   description: What this risk story represents
#   check_patterns: Regex patterns or prefixes to match check IDs
#   factors: Scoring factors touched by this narrative
#   allegation_types: D&O allegation categories (A-E)
#   severity: Base severity (may be upgraded based on individual checks)
NARRATIVE_TEMPLATES: dict[str, dict[str, Any]] = {
    "restatement_risk": {
        "title": "Restatement Risk Narrative",
        "description": (
            "Signals suggest elevated risk of financial restatement: "
            "aggressive accounting practices combined with insider "
            "selling and auditor concerns create a pattern frequently "
            "seen before restatement announcements."
        ),
        "check_patterns": [
            r"FIN\.ACCT\.restatement",
            r"FIN\.ACCT\.earnings_manipulation",
            r"FIN\.ACCT\.internal_controls",
            r"FIN\.ACCT\.auditor",
            r"FIN\.ACCT\.quality_indicators",
            r"STOCK\.INSIDER\.cluster_timing",
            r"STOCK\.INSIDER\.notable_activity",
            r"GOV\.EFFECT\.auditor_change",
            r"GOV\.EFFECT\.audit_opinion",
            r"FIN\.ACCT\.sec_correspondence",
        ],
        "factors": ["F1", "F3", "F5"],
        "allegation_types": ["A"],
        "severity": "HIGH",
    },
    "event_driven_claim": {
        "title": "Event-Driven Claim Narrative",
        "description": (
            "A significant stock price decline following a disclosure "
            "event creates the classic pattern for securities class "
            "action filing. Earnings miss, disclosure gap, and price "
            "impact align with typical SCA triggers."
        ),
        "check_patterns": [
            r"STOCK\.PRICE\.single_day_events",
            r"STOCK\.PRICE\.recent_drop_alert",
            r"STOCK\.PATTERN\.event_collapse",
            r"FIN\.GUIDE\.earnings_reaction",
            r"FIN\.GUIDE\.track_record",
            r"STOCK\.PATTERN\.cascade",
            r"LIT\.SCA\.prefiling",
            r"LIT\.SCA\.active",
            r"STOCK\.PRICE\.attribution",
        ],
        "factors": ["F2", "F5"],
        "allegation_types": ["A", "B"],
        "severity": "HIGH",
    },
    "governance_failure": {
        "title": "Governance Failure Narrative",
        "description": (
            "Board oversight deficiencies combined with compensation "
            "concerns and structural governance weaknesses suggest "
            "inadequate management oversight, a common basis for "
            "derivative and breach of fiduciary duty claims."
        ),
        "check_patterns": [
            r"GOV\.BOARD\.independence",
            r"GOV\.BOARD\.ceo_chair",
            r"GOV\.BOARD\.overboarding",
            r"GOV\.BOARD\.departures",
            r"GOV\.PAY\.ceo_ratio",
            r"GOV\.PAY\.peer_comparison",
            r"GOV\.PAY\.excess_comp",
            r"GOV\.EFFECT\.audit_committee",
            r"GOV\.BOARD\.attendance",
            r"GOV\.BOARD\.committees",
        ],
        "factors": ["F7", "F8"],
        "allegation_types": ["C"],
        "severity": "MEDIUM",
    },
    "regulatory_exposure": {
        "title": "Regulatory Exposure Narrative",
        "description": (
            "Active or pending regulatory proceedings combined with "
            "enforcement history indicate elevated risk of regulatory "
            "action that could trigger follow-on securities litigation "
            "or shareholder derivative suits."
        ),
        "check_patterns": [
            r"LIT\.REG\.sec_active",
            r"LIT\.REG\.sec_investigation",
            r"LIT\.REG\.wells_notice",
            r"LIT\.REG\.doj_investigation",
            r"LIT\.REG\.comment_letters",
            r"LIT\.REG\.consent_order",
            r"LIT\.REG\.civil_penalty",
            r"LIT\.REG\.state_ag",
            r"LIT\.REG\.ftc_investigation",
            r"LIT\.REG\.sec_severity",
        ],
        "factors": ["F9", "F10"],
        "allegation_types": ["D"],
        "severity": "HIGH",
    },
    "financial_distress": {
        "title": "Financial Distress Narrative",
        "description": (
            "Deteriorating financial metrics across debt, liquidity, "
            "and profitability dimensions signal potential distress. "
            "Companies in financial distress face heightened D&O "
            "exposure from creditor suits, bankruptcy-related claims, "
            "and going concern disclosures."
        ),
        "check_patterns": [
            r"FIN\.DEBT\.covenants",
            r"FIN\.DEBT\.coverage",
            r"FIN\.DEBT\.maturity",
            r"FIN\.LIQ\.position",
            r"FIN\.LIQ\.cash_burn",
            r"FIN\.LIQ\.trend",
            r"FIN\.PROFIT\.trend",
            r"FIN\.PROFIT\.margins",
            r"STOCK\.PRICE\.delisting_risk",
            r"STOCK\.PATTERN\.death_spiral",
        ],
        "factors": ["F4"],
        "allegation_types": ["E"],
        "severity": "HIGH",
    },
    "insider_trading_pattern": {
        "title": "Insider Trading Pattern Narrative",
        "description": (
            "Clustered insider selling activity, particularly when "
            "combined with suspicious timing relative to material "
            "events, creates a pattern that plaintiffs frequently "
            "cite as evidence of scienter in securities fraud claims."
        ),
        "check_patterns": [
            r"STOCK\.INSIDER\.cluster_timing",
            r"STOCK\.INSIDER\.notable_activity",
            r"STOCK\.INSIDER\.summary",
            r"STOCK\.PATTERN\.informed_trading",
            r"GOV\.PAY\.excess_comp",
            r"FIN\.ACCT\.earnings_manipulation",
        ],
        "factors": ["F1", "F3"],
        "allegation_types": ["A", "B"],
        "severity": "HIGH",
    },
    "acquisition_risk": {
        "title": "Acquisition Risk Narrative",
        "description": (
            "M&A activity combined with valuation concerns and "
            "governance questions creates exposure for merger "
            "objection suits and breach of fiduciary duty claims "
            "challenging deal terms or process."
        ),
        "check_patterns": [
            r"LIT\.SCA\.merger_obj",
            r"STOCK\.VALUATION\.premium_discount",
            r"STOCK\.VALUATION\.ev_ebitda",
            r"GOV\.BOARD\.independence",
            r"GOV\.ACTIVIST\.campaigns",
            r"GOV\.ACTIVIST\.13d_filings",
            r"BIZ\.SIZE\.growth_trajectory",
        ],
        "factors": ["F2", "F7"],
        "allegation_types": ["C"],
        "severity": "MEDIUM",
    },
}


def compose_narrative(
    store: KnowledgeStore, fired_checks: list[str]
) -> list[NarrativeStory]:
    """Compose risk narratives from fired check IDs.

    Matches fired checks against NARRATIVE_TEMPLATES. A template
    is activated when >= 2 of its required check patterns match.
    Generates evidence summaries by combining check descriptions
    from the knowledge store.

    Args:
        store: Knowledge store for looking up check descriptions.
        fired_checks: List of check IDs that fired in an analysis.

    Returns:
        List of NarrativeStory instances, sorted by severity
        (HIGH first, then MEDIUM, then LOW).
    """
    if not fired_checks:
        return []

    stories: list[NarrativeStory] = []
    fired_set = set(fired_checks)

    for story_id, template in NARRATIVE_TEMPLATES.items():
        patterns: list[str] = template["check_patterns"]
        matching_checks = _match_checks(fired_set, patterns)

        if len(matching_checks) < 2:
            continue

        # Determine severity from worst check or template default
        severity = _determine_severity(store, matching_checks, template)

        # Build evidence summary from check descriptions
        evidence = _build_evidence_summary(store, matching_checks)

        story = NarrativeStory(
            story_id=story_id,
            title=template["title"],
            description=template["description"],
            checks=sorted(matching_checks),
            factors_affected=list(template["factors"]),
            allegation_types=list(template["allegation_types"]),
            severity=severity,
            evidence_summary=evidence,
        )
        stories.append(story)

    # Sort by severity: HIGH first
    stories.sort(key=lambda s: _SEVERITY_ORDER.get(s.severity, 99))
    return stories


def get_available_narratives() -> list[dict[str, Any]]:
    """Return all available narrative templates with their requirements.

    Useful for understanding what stories the system can compose
    and what check patterns are needed to activate each.

    Returns:
        List of dicts with template metadata.
    """
    result: list[dict[str, Any]] = []
    for story_id, template in NARRATIVE_TEMPLATES.items():
        result.append({
            "story_id": story_id,
            "title": template["title"],
            "description": template["description"],
            "check_patterns": template["check_patterns"],
            "factors": template["factors"],
            "allegation_types": template["allegation_types"],
            "severity": template["severity"],
            "activation_threshold": 2,
        })
    return result


def suggest_new_narrative(
    store: KnowledgeStore,
    co_firing_data: list[tuple[str, str, float]],
) -> list[dict[str, Any]]:
    """Suggest potential new narrative stories from co-firing data.

    Identifies clusters of 3+ checks that frequently co-fire,
    which may represent undiscovered risk narratives.

    Args:
        store: Knowledge store (used for check name lookup).
        co_firing_data: Co-firing pairs from learning module
            as (check_a, check_b, co_occurrence_rate) tuples.

    Returns:
        List of suggested narratives with check IDs and rates.
    """
    if not co_firing_data:
        return []

    # Build adjacency graph from co-firing pairs
    adjacency: dict[str, set[str]] = defaultdict(set)
    pair_rates: dict[tuple[str, str], float] = {}
    for check_a, check_b, rate in co_firing_data:
        adjacency[check_a].add(check_b)
        adjacency[check_b].add(check_a)
        pair_key = (min(check_a, check_b), max(check_a, check_b))
        pair_rates[pair_key] = rate

    # Find clusters via greedy expansion from highest-degree nodes
    visited: set[str] = set()
    clusters: list[set[str]] = []

    sorted_nodes = sorted(
        adjacency.keys(), key=lambda n: len(adjacency[n]), reverse=True
    )

    for node in sorted_nodes:
        if node in visited:
            continue
        cluster = {node}
        visited.add(node)
        # Add connected neighbors that connect to most of the cluster
        for neighbor in sorted(
            adjacency[node],
            key=lambda n: len(adjacency[n]),
            reverse=True,
        ):
            if neighbor in visited:
                continue
            # Neighbor must connect to at least half the cluster
            connections = sum(
                1 for c in cluster if neighbor in adjacency[c]
            )
            if connections >= len(cluster) / 2:
                cluster.add(neighbor)
                visited.add(neighbor)

        if len(cluster) >= 3:
            clusters.append(cluster)

    # Convert clusters to suggestions
    suggestions: list[dict[str, Any]] = []
    for cluster in clusters:
        signal_ids = sorted(cluster)
        signal_names: list[str] = []
        for cid in signal_ids:
            check = store.get_check(cid)
            name = str(check.get("name", cid)) if check else cid
            signal_names.append(name)

        # Compute average co-occurrence rate within cluster
        cluster_rates: list[float] = []
        for a, b in _pairs_from_set(cluster):
            pair_key = (min(a, b), max(a, b))
            if pair_key in pair_rates:
                cluster_rates.append(pair_rates[pair_key])

        avg_rate = (
            sum(cluster_rates) / len(cluster_rates)
            if cluster_rates
            else 0.0
        )

        suggestions.append({
            "signal_ids": signal_ids,
            "signal_names": signal_names,
            "cluster_size": len(cluster),
            "average_co_occurrence_rate": avg_rate,
        })

    # Sort by cluster size descending, then avg rate
    suggestions.sort(
        key=lambda s: (s["cluster_size"], s["average_co_occurrence_rate"]),
        reverse=True,
    )
    return suggestions


def _match_checks(
    fired_set: set[str], patterns: list[str]
) -> list[str]:
    """Match fired check IDs against regex patterns."""
    matched: list[str] = []
    for signal_id in fired_set:
        for pattern in patterns:
            if re.fullmatch(pattern, signal_id):
                matched.append(signal_id)
                break
    return matched


def _determine_severity(
    store: KnowledgeStore,
    matching_checks: list[str],
    template: dict[str, Any],
) -> str:
    """Determine narrative severity from matching checks.

    Uses the worst (highest) severity among matching checks,
    falling back to the template default.
    """
    worst = template.get("severity", "MEDIUM")
    for signal_id in matching_checks:
        check = store.get_check(signal_id)
        if check is None:
            continue
        sev = check.get("severity")
        if isinstance(sev, str) and sev in _SEVERITY_ORDER:
            if _SEVERITY_ORDER[sev] < _SEVERITY_ORDER.get(worst, 99):
                worst = sev
    return str(worst)


def _build_evidence_summary(
    store: KnowledgeStore, matching_checks: list[str]
) -> str:
    """Build evidence summary by combining check descriptions."""
    lines: list[str] = []
    for signal_id in sorted(matching_checks):
        check = store.get_check(signal_id)
        if check is not None:
            name = check.get("name", signal_id)
            lines.append(f"- {name} ({signal_id})")
        else:
            lines.append(f"- {signal_id}")
    if not lines:
        return "No evidence details available."
    return "Evidence from fired checks:\n" + "\n".join(lines)


def _pairs_from_set(s: set[str]) -> list[tuple[str, str]]:
    """Generate all unique pairs from a set."""
    items = sorted(s)
    pairs: list[tuple[str, str]] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pairs.append((items[i], items[j]))
    return pairs
