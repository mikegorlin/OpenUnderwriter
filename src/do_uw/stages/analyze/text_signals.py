"""Text signal extraction from 10-K filing sections.

Scans section-split filing text for topic-specific keywords to produce
structured signals for checks that evaluate topic presence/absence
rather than numeric thresholds.

Each signal records: present (bool), mention_count (int),
context (first relevant snippet), and source_section.

This module closes ~60 DATA_UNAVAILABLE checks by extracting topic
presence from 10-K text that is already acquired and section-split.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TextSignal:
    """A topic presence signal extracted from filing text."""

    present: bool = False
    mention_count: int = 0
    context: str = ""
    source_section: str = ""


# ---------------------------------------------------------------------------
# Keyword dictionaries: topic -> (section_keys, keyword_patterns)
#
# section_keys: which filing sections to scan (item1, item1a, item7, etc.)
# keyword_patterns: list of regex patterns (case-insensitive)
# ---------------------------------------------------------------------------

_SIGNAL_DEFS: dict[str, tuple[list[str], list[str]]] = {
    # BIZ.COMP checks
    "barriers_to_entry": (
        ["item1", "item7"],
        [r"barrier.{0,20}entry", r"switching\s+cost", r"network\s+effect",
         r"econom(?:y|ies)\s+of\s+scale", r"patent\s+protect",
         r"regulatory\s+barrier", r"high\s+capital\s+requirement"],
    ),
    "competitive_moat": (
        ["item1", "item7"],
        [r"competitive\s+advantage", r"brand\s+recognition",
         r"intellectual\s+property", r"proprietary\s+technology",
         r"market\s+leader", r"dominant\s+position", r"first.mover"],
    ),
    "industry_headwinds": (
        ["item1a", "item7"],
        [r"industry\s+headwind", r"secular\s+decline",
         r"market\s+saturat", r"competitive\s+pressure",
         r"pricing\s+pressure", r"margin\s+compress",
         r"industry\s+disruption", r"market\s+downturn"],
    ),
    # BIZ.DEPEND checks
    "customer_concentration": (
        ["item1", "item1a", "item7"],
        [r"customer\s+concentration", r"(?:significant|major|key)\s+customer",
         r"(?:top|largest)\s+(?:\d+\s+)?customer",
         r"(?:single|one)\s+customer\s+(?:account|represent)",
         r"(?:10|ten)\s*%\s+(?:or more|of (?:revenue|net sales|total revenue))"],
    ),
    "technology_dependency": (
        ["item1", "item1a"],
        [r"technology\s+depend", r"reliance\s+on\s+(?:technology|IT|software)",
         r"system\s+failure", r"technology\s+risk",
         r"depend(?:s|ent)\s+(?:on|upon)\s+(?:our|the)\s+(?:technology|platform|system)"],
    ),
    "regulatory_dependency": (
        ["item1", "item1a"],
        [r"regulatory\s+(?:approval|clearance|permit|license)",
         r"subject\s+to\s+(?:extensive|significant)\s+regulation",
         r"government\s+(?:approval|contract|regulation)",
         r"FDA\s+(?:approval|clearance)", r"regulatory\s+compliance"],
    ),
    "capital_dependency": (
        ["item1", "item1a"],
        [r"capital.intensive", r"significant\s+capital\s+(?:expenditure|investment|requirement)",
         r"capital\s+requirement", r"require\s+(?:significant|substantial)\s+capital"],
    ),
    "macro_sensitivity": (
        ["item1a", "item7"],
        [r"macroeconomic\s+(?:condition|environment|factor|trend)",
         r"economic\s+(?:downturn|recession|slowdown|cycle)",
         r"sensitive\s+to\s+(?:economic|market)\s+condition",
         r"GDP\s+growth", r"consumer\s+(?:spending|confidence|demand)"],
    ),
    "distribution_channels": (
        ["item1"],
        [r"distribution\s+(?:channel|network|partner|agreement)",
         r"retail\s+(?:channel|partner|store|distribution)",
         r"direct.to.consumer", r"e.commerce", r"wholesale\s+(?:channel|distribution)"],
    ),
    "contract_terms": (
        ["item1", "item1a"],
        [r"(?:long|short).term\s+(?:contract|agreement|commitment)",
         r"contract\s+(?:renewal|expir|terminat)",
         r"revenue\s+(?:contract|backlog|commitment)",
         r"customer\s+(?:contract|agreement)"],
    ),
    # BIZ.MODEL checks
    "cost_structure_analysis": (
        ["item7"],
        [r"cost\s+of\s+(?:goods|revenue|sales)", r"operating\s+(?:expense|cost)",
         r"gross\s+margin", r"fixed\s+cost", r"variable\s+cost",
         r"R&D\s+(?:expense|spending|investment)", r"SG&A"],
    ),
    "model_regulatory_dependency": (
        ["item1a"],
        [r"regulatory\s+(?:change|reform|requirement|risk)",
         r"changes?\s+in\s+(?:law|regulation|legislation)",
         r"compliance\s+(?:cost|requirement|risk)",
         r"new\s+regulat"],
    ),
    # BIZ.UNI checks
    "cybersecurity_posture": (
        ["item1", "item1a"],
        [r"cybersecurity", r"cyber.security", r"data\s+(?:breach|security|privacy)",
         r"information\s+security", r"cyber\s+(?:attack|threat|risk|incident)",
         r"ransomware", r"phishing"],
    ),
    "cyber_business_risk": (
        ["item1a"],
        [r"cyber.{0,30}(?:business|operational|financial)\s+(?:risk|impact|disruption)",
         r"data\s+breach.{0,30}(?:cost|impact|damage|liability)",
         r"cyber\s+(?:insurance|liability)"],
    ),
    "ai_risk_exposure": (
        ["item1", "item1a"],
        [r"artificial\s+intelligence", r"\bAI\b", r"machine\s+learning",
         r"generative\s+AI", r"AI.related\s+risk", r"AI\s+(?:regulation|governance)"],
    ),
    # FWRD.MACRO checks
    "fx_exposure": (
        ["item1a", "item7"],
        [r"foreign\s+(?:exchange|currency)", r"\bFX\b",
         r"currency\s+(?:risk|fluctuat|translat|hedg)",
         r"exchange\s+rate"],
    ),
    "geopolitical_exposure": (
        ["item1a"],
        [r"geopolitical", r"sanction", r"tariff",
         r"trade\s+(?:war|tension|restriction|dispute)",
         r"political\s+(?:risk|instability|unrest)"],
    ),
    "supply_chain_disruption": (
        ["item1a", "item1"],
        [r"supply\s+chain\s+(?:disruption|risk|challenge|constraint)",
         r"component\s+shortage", r"logistic(?:s|al)\s+(?:challenge|disruption)",
         r"single.source\s+supplier", r"supply\s+(?:constraint|shortage)"],
    ),
    "trade_policy": (
        ["item1a"],
        [r"trade\s+polic(?:y|ies)", r"tariff", r"import\s+dut(?:y|ies)",
         r"export\s+control", r"trade\s+(?:restriction|agreement|regulation)"],
    ),
    "climate_transition_risk": (
        ["item1a"],
        [r"climate\s+(?:change|risk|transition)", r"carbon\s+(?:emission|footprint|tax)",
         r"\bESG\b", r"greenhouse\s+gas",
         r"environmental\s+(?:regulation|compliance|risk)"],
    ),
    "commodity_impact": (
        ["item1a", "item7"],
        [r"commodity\s+(?:price|cost|risk)", r"raw\s+material\s+(?:cost|price)",
         r"input\s+cost", r"energy\s+(?:cost|price)"],
    ),
    "interest_rate_sensitivity": (
        ["item1a", "item7"],
        [r"interest\s+rate\s+(?:risk|sensitivity|change|fluctuat)",
         r"floating\s+rate", r"LIBOR", r"SOFR",
         r"variable.rate\s+(?:debt|borrowing)"],
    ),
    "inflation_impact": (
        ["item1a", "item7"],
        [r"inflat(?:ion|ionary)", r"cost\s+increase",
         r"wage\s+(?:pressure|increase|inflation)", r"price\s+increase",
         r"rising\s+cost"],
    ),
    "labor_market": (
        ["item1a", "item1"],
        [r"(?:labor|labour)\s+(?:market|shortage|competition)",
         r"talent\s+(?:retention|attraction|competition|shortage)",
         r"(?:hiring|recruitment)\s+(?:challenge|competition|difficulty)",
         r"employee\s+(?:retention|turnover|attrition)"],
    ),
    "regulatory_changes": (
        ["item1a"],
        [r"regulatory\s+change", r"new\s+regulation",
         r"compliance\s+(?:requirement|cost)",
         r"changes?\s+in\s+(?:law|regulation|rule)",
         r"proposed\s+(?:regulation|rule|legislation)"],
    ),
    "legislative_risk": (
        ["item1a"],
        [r"legislat(?:ion|ive)\s+(?:risk|change|reform|proposal)",
         r"proposed\s+(?:law|legislation)", r"regulatory\s+reform",
         r"congressional\s+(?:action|investigation|hearing)"],
    ),
    "industry_consolidation": (
        ["item1a", "item1"],
        [r"(?:industry|market)\s+consolidat", r"acquisit(?:ion|ive)",
         r"merger", r"M&A", r"strategic\s+(?:transaction|combination)"],
    ),
    "disruptive_tech": (
        ["item1a"],
        [r"disruptive\s+(?:technology|innovation)", r"emerging\s+technology",
         r"technological\s+(?:change|disruption|advancement)",
         r"digital\s+(?:transformation|disruption)"],
    ),
    # BIZ.STRUC: structural complexity signals (Phase 96)
    "vie_spe": (
        ["item8", "item7"],
        [r"variable\s+interest\s+entit", r"\bVIE\b", r"special\s+purpose\s+(?:entit|vehicle)",
         r"\bSPE\b", r"off.balance.sheet\s+(?:entit|arrangement|structure)"],
    ),
    "obs_guarantees": (
        ["item7", "item8"],
        [r"guarantee", r"indemnif", r"letter\s+of\s+credit",
         r"surety\s+bond", r"performance\s+bond"],
    ),
    "obs_commitments": (
        ["item7", "item8"],
        [r"purchase\s+obligation", r"take.or.pay", r"throughput",
         r"unconditional\s+purchase", r"minimum\s+(?:payment|commitment|purchase)"],
    ),
    "intercompany_complexity": (
        ["item1", "item8"],
        [r"intercompany", r"intra.group", r"transfer\s+pricing",
         r"management\s+fee", r"cost\s+sharing", r"(?:intercompany|intra.group)\s+elimination"],
    ),
    "holding_layers": (
        ["item1"],
        [r"holding\s+company", r"intermediate\s+holding",
         r"parent\s+company", r"operating\s+subsidiar",
         r"wholly.owned\s+subsidiar"],
    ),
    "fls_density": (
        ["item7"],
        [r"forward.looking\s+statement", r"safe\s+harbor",
         r"Private\s+Securities\s+Litigation\s+Reform\s+Act",
         r"we\s+expect", r"we\s+anticipate", r"we\s+believe",
         r"we\s+estimate", r"we\s+project", r"we\s+intend"],
    ),
    "sec_nongaap_comment": (
        ["item7"],
        [r"SEC\s+comment", r"Staff\s+comment", r"staff\s+letter",
         r"comment\s+letter.{0,30}non.GAAP"],
    ),
    "nongaap_measures": (
        ["item7"],
        [r"(?:adjusted|non.GAAP)\s+(?:EBITDA|earnings|income|revenue|EPS|operating\s+(?:income|margin))",
         r"free\s+cash\s+flow", r"(?:core|organic)\s+(?:revenue|earnings|growth)",
         r"(?:adjusted|non.GAAP)\s+(?:net\s+income|operating\s+income)"],
    ),
    "critical_estimates": (
        ["item7"],
        [r"critical\s+accounting\s+(?:estimate|polic|judgment)",
         r"significant\s+(?:estimate|assumption|judgment)",
         r"key\s+(?:estimate|assumption|accounting\s+polic)"],
    ),
    # FWRD.DISC checks
    "mda_depth": (
        ["item7"],
        [r"management.s\s+discussion", r"MD&A",
         r"results\s+of\s+operations", r"critical\s+accounting"],
    ),
    "non_gaap_reconciliation": (
        ["item7"],
        [r"non.GAAP", r"adjusted\s+(?:EBITDA|earnings|income|revenue)",
         r"non.GAAP\s+(?:measure|financial|reconcili)"],
    ),
    "segment_consistency": (
        ["item7", "item8"],
        [r"segment\s+(?:reporting|information|result)",
         r"operating\s+segment", r"reportable\s+segment",
         r"change.{0,20}segment"],
    ),
    "related_party_completeness": (
        ["item8", "item7"],
        [r"related\s+part(?:y|ies)\s+(?:transaction|arrangement)",
         r"transaction.{0,20}(?:related|affiliated)\s+(?:party|person|entity)"],
    ),
    "metric_consistency": (
        ["item7"],
        [r"key\s+(?:performance|operating)\s+(?:indicator|metric|measure)",
         r"KPI", r"operating\s+metric"],
    ),
    # FWRD.WARN text-based checks
    "impairment_risk": (
        ["item7", "item8"],
        [r"impairment\s+(?:charge|loss|test|risk)",
         r"goodwill\s+(?:impairment|writedown|write.down)",
         r"asset\s+(?:impairment|writedown|write.down)"],
    ),
    "margin_pressure": (
        ["item7", "item1a"],
        [r"margin\s+(?:pressure|compression|decline|erosion)",
         r"gross\s+margin\s+(?:declin|decreas|compress)",
         r"operating\s+margin\s+(?:declin|decreas|compress)",
         r"pricing\s+pressure"],
    ),
    "revenue_quality_warn": (
        ["item7", "item1a"],
        [r"revenue\s+(?:recognition|quality|concentrat)",
         r"one.time\s+(?:revenue|gain|benefit)",
         r"non.recurring\s+(?:revenue|income)"],
    ),
    "capex_discipline": (
        ["item7"],
        [r"capital\s+(?:expenditure|spending|investment|allocation)",
         r"capex", r"CAPEX", r"property.{0,10}equipment\s+(?:purchase|investment)"],
    ),
    "whistleblower_exposure": (
        ["item1a", "item3"],
        [r"whistleblower", r"qui\s+tam", r"False\s+Claims\s+Act",
         r"retaliation\s+(?:claim|complaint|lawsuit)"],
    ),
    "contract_disputes": (
        ["item3", "item1a"],
        [r"contract\s+(?:dispute|breach|litigation|claim)",
         r"breach\s+of\s+(?:contract|agreement)",
         r"contractual\s+(?:dispute|obligation)"],
    ),
    "vendor_payment_delays": (
        ["item7"],
        [r"(?:vendor|supplier)\s+(?:payment|payable)\s+(?:delay|extend)",
         r"(?:days|DPO)\s+(?:payable|outstanding)",
         r"payment\s+term\s+(?:extension|renegotiat)"],
    ),
    "compliance_hiring": (
        ["item1a"],
        [r"compliance\s+(?:program|officer|function|requirement)",
         r"regulatory\s+compliance", r"internal\s+(?:control|compliance)"],
    ),
    "legal_hiring": (
        ["item1a", "item3"],
        [r"legal\s+(?:proceeding|matter|action|exposure)",
         r"(?:litigation|legal)\s+(?:risk|exposure|cost)"],
    ),
    "ai_revenue_concentration": (
        ["item1", "item1a"],
        [r"AI.(?:related|driven|based)\s+(?:revenue|product|service)",
         r"artificial\s+intelligence\s+(?:product|service|solution)"],
    ),
    "customer_churn_signals": (
        ["item1a", "item7"],
        [r"customer\s+(?:churn|attrition|retention|loss)",
         r"subscriber\s+(?:churn|loss|cancellat)",
         r"client\s+(?:retention|loss|attrition)"],
    ),
    "partner_stability": (
        ["item1a", "item1"],
        [r"partner(?:ship)?\s+(?:risk|depend|terminat|loss)",
         r"strategic\s+(?:alliance|partner|relationship)",
         r"(?:key|critical|important)\s+(?:partner|relationship)"],
    ),
    # FWRD.EVENT text-based checks
    "contract_renewal_event": (
        ["item1", "item1a"],
        [r"contract\s+(?:renewal|expir|terminat)",
         r"license\s+(?:renewal|expir)",
         r"agreement\s+(?:renewal|expir)"],
    ),
    "regulatory_decision_event": (
        ["item1a"],
        [r"(?:pending|upcoming)\s+(?:regulatory|FDA|FCC|SEC)\s+(?:decision|approval|ruling)",
         r"(?:regulatory|government)\s+(?:review|investigation|proceeding)"],
    ),
    "customer_retention_event": (
        ["item1a", "item7"],
        [r"customer\s+(?:retention|renewal|contract)",
         r"(?:key|major|significant)\s+customer",
         r"customer\s+concentration"],
    ),
    "employee_retention_event": (
        ["item1a"],
        [r"(?:key|critical)\s+(?:employee|personnel|talent)",
         r"employee\s+(?:retention|turnover|departure)",
         r"loss\s+of\s+key\s+(?:employee|personnel)"],
    ),
}


def extract_text_signals(
    filing_texts: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract topic presence signals from 10-K filing sections.

    Args:
        filing_texts: Dict of section-keyed filing text
            (keys: item1, item1a, item7, item8, item9a, etc.)

    Returns:
        Dict mapping signal_name -> serialized TextSignal dict.
    """
    signals: dict[str, dict[str, Any]] = {}

    for signal_name, (section_keys, patterns) in _SIGNAL_DEFS.items():
        signal = _scan_sections(filing_texts, section_keys, patterns)
        signal.source_section = ", ".join(section_keys)
        signals[signal_name] = {
            "present": signal.present,
            "mention_count": signal.mention_count,
            "context": signal.context,
            "source_section": signal.source_section,
        }

    return signals


def _scan_sections(
    filing_texts: dict[str, Any],
    section_keys: list[str],
    patterns: list[str],
) -> TextSignal:
    """Scan specified sections for keyword patterns."""
    signal = TextSignal()
    best_context = ""
    total_mentions = 0

    for key in section_keys:
        text = filing_texts.get(key, "")
        if not isinstance(text, str) or not text:
            continue

        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            total_mentions += len(matches)
            if matches and not best_context:
                # Extract ~150 chars of context around first match
                m = matches[0]
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 100)
                best_context = text[start:end].strip()
                # Clean up for display
                best_context = re.sub(r"\s+", " ", best_context)

    signal.present = total_mentions > 0
    signal.mention_count = total_mentions
    signal.context = best_context[:200] if best_context else ""
    return signal


__all__ = ["TextSignal", "extract_text_signals"]
