"""Brain question framework — structured D&O underwriting questions.

Loads question definitions from YAML files in this directory.
Each YAML file defines a domain (company identity, financial health, etc.)
with ordered questions that map to pipeline data sources.

The question framework follows the logical order a 30-year D&O underwriter
uses to evaluate an account:
  1. Company & Business Model — who is this and what do they do?
  2. Financial Health & Accounting — can I trust the numbers?
  3. Governance & People — who runs it and are they trustworthy?
  4. Stock & Market Risk — what could trigger a claim?
  5. Litigation & Claims — what's the history?
  6. Operational & Emerging Risk — what hasn't happened yet?
  7. D&O Program & Pricing — is the program adequate?
  8. Underwriting Decision — what's the call?
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_QUESTIONS_DIR = Path(__file__).parent


def load_all_domains() -> list[dict[str, Any]]:
    """Load all question domains from YAML, sorted by order field.

    Returns list of domain dicts, each with:
      - domain, domain_label, order, description
      - questions: list of question dicts
    """
    domains: list[dict[str, Any]] = []
    for yaml_file in sorted(_QUESTIONS_DIR.glob("*.yaml")):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, dict) and "questions" in data:
                domains.append(data)
        except Exception:
            logger.warning("Failed to load question file: %s", yaml_file)
    domains.sort(key=lambda d: d.get("order", 99))
    return domains


def load_all_questions() -> list[dict[str, Any]]:
    """Load all questions across all domains, in domain order.

    Each question dict includes the parent domain_label for grouping.
    """
    questions: list[dict[str, Any]] = []
    for domain in load_all_domains():
        domain_label = domain.get("domain_label", "")
        domain_id = domain.get("domain", "")
        for q in domain.get("questions", []):
            questions.append({
                **q,
                "domain_label": domain_label,
                "domain": domain_id,
            })
    return questions


def get_question_count() -> int:
    """Return total count of defined questions."""
    return len(load_all_questions())


__all__ = ["load_all_domains", "load_all_questions", "get_question_count"]
