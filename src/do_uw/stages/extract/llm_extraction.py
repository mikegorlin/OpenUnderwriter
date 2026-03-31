"""LLM extraction orchestration: parallel extraction with filing prioritization.

Handles prioritizing, filtering, and concurrently extracting structured data
from SEC filings via LLM. Called by ExtractStage as Phase 0b.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, NamedTuple

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Filing priority: higher value = extract first. 10-K is the comprehensive
# baseline; DEF 14A has unique governance data; 8-Ks are material events.
_FILING_PRIORITY: dict[str, int] = {
    "10-K": 100,
    "20-F": 100,
    "DEF 14A": 90,
    "S-1": 85,
    "S-3": 80,
    "424B": 75,  # Capital filings above 8-K for IPO companies
    "8-K": 70,
    "10-Q": 50,
    "6-K": 50,
    "SC 13D": 40,
    "SC 13G": 30,
}

# Concurrent extraction threads. SDK handles 429 rate-limit retries.
# Reduced to 1 to avoid API concurrency limits (DeepSeek)
_MAX_EXTRACT_WORKERS = 1

# Cap total filings per company to bound cost (~$0.10-0.20 per filing).
# Reduced for speed (user: "push it to the limit")
_MAX_FILINGS_PER_COMPANY = 1

# Post-annual quarterly filings (10-Q/6-K filed after latest 10-K) get
# boosted priority so they survive the cap. Set above 8-K (70) but
# below DEF 14A (90) -- these contain genuinely new interim data.
_POST_ANNUAL_Q_PRIORITY = 80


class _WorkItem(NamedTuple):
    """Single filing queued for LLM extraction."""

    form_type: str
    accession: str
    filing_date: str
    full_text: str
    schema: type[Any]  # type[BaseModel]
    prompt: str
    max_tokens: int
    priority: int

    @property
    def key(self) -> str:
        """Cache/result key for this filing."""
        return f"{self.form_type}:{self.accession}"

    @property
    def short_label(self) -> str:
        """Human-readable label for progress display."""
        acc = self.accession[:20] if self.accession else "?"
        return f"{self.form_type} ({acc})"


def _prepare_work_items(
    filing_documents: dict[str, list[dict[str, str]]],
    manifest: Any | None = None,
    company: Any | None = None,
) -> list[_WorkItem]:
    """Build prioritized, filtered list of extraction work items.

    Filing prioritization logic:
    - 10-K/20-F first (comprehensive annual baseline)
    - DEF 14A second (unique governance data domain)
    - 8-Ks (material events, small documents)
    - 10-Qs ONLY if filed after the most recent 10-K
      (pre-10-K quarterlies are superseded by the annual)
    - Ownership and capital filings last (small, supplementary)

    Within each type, most recent filings first.
    Capped at _MAX_FILINGS_PER_COMPANY total.

    Args:
        filing_documents: Dict mapping form type to list of filing docs.
        manifest: Optional extraction manifest for brain-driven targets.
        company: Optional CompanyProfile for sector/size context in prompts.
    """
    from do_uw.stages.extract.llm.prompts import get_prompt
    from do_uw.stages.extract.llm.schemas import get_schema_for_filing

    # Build company context overlay once (shared across all prompts)
    company_context = ""
    if company is not None:
        from do_uw.stages.extract.llm.company_context import build_company_context

        company_context = build_company_context(company)

    items: list[_WorkItem] = []
    for form_type, docs in filing_documents.items():
        entry = get_schema_for_filing(form_type)
        if entry is None:
            continue
        prompt = get_prompt(entry.prompt_key)
        # Enhance prompt with brain extraction targets if manifest available
        if manifest is not None:
            from do_uw.stages.extract.llm.prompt_enhancer import (
                enhance_prompt_with_brain_requirements,
            )

            prompt = enhance_prompt_with_brain_requirements(
                prompt,
                form_type,
                manifest,
            )
        # Append company context so LLM calibrates for this company type
        if company_context:
            prompt = prompt + company_context
        priority = _FILING_PRIORITY.get(form_type, 0)

        for doc in docs:
            accession = doc.get("accession", "")
            full_text = doc.get("full_text", "")
            filing_date = doc.get("filing_date", "")
            if not full_text or not accession:
                continue
            items.append(
                _WorkItem(
                    form_type=form_type,
                    accession=accession,
                    filing_date=filing_date,
                    full_text=full_text,
                    schema=entry.schema,
                    prompt=prompt,
                    max_tokens=entry.max_tokens,
                    priority=priority,
                )
            )

    # Filter redundant quarterly filings (also boosts post-annual Q priority)
    items = _filter_redundant_filings(items)

    # Sort: highest priority first; within same priority, newest first.
    # Done AFTER filtering since post-annual Qs get boosted priority.
    items.sort(key=lambda w: w.filing_date or "0000", reverse=True)
    items.sort(key=lambda w: w.priority, reverse=True)

    # Cap total filings
    if len(items) > _MAX_FILINGS_PER_COMPANY:
        logger.info(
            "Capping LLM extraction at %d filings (had %d)",
            _MAX_FILINGS_PER_COMPANY,
            len(items),
        )
        items = items[:_MAX_FILINGS_PER_COMPANY]

    return items


def _filter_redundant_filings(
    items: list[_WorkItem],
) -> list[_WorkItem]:
    """Remove quarterly filings superseded by the latest annual report.

    Logic: The 10-K includes comprehensive full-year data (financials,
    risk factors, legal proceedings, controls) that supersedes any
    quarterly snapshots from that fiscal year. However, 10-Qs filed
    AFTER the 10-K contain genuinely new information (new lawsuits,
    quarterly performance, emerging issues) and must be kept.

    Post-annual 10-Qs are boosted to priority 80 (above 8-K at 70) so
    they survive the _MAX_FILINGS_PER_COMPANY cap. These filings are
    the only source of interim financial data between annual reports.

    If no annual report exists, all filings are kept.
    """
    # Find the most recent annual report date
    annual_date: str | None = None
    for item in items:
        if item.form_type in ("10-K", "20-F") and item.filing_date:
            annual_date = item.filing_date
            break  # Items already sorted by priority+date

    if annual_date is None:
        return items

    filtered: list[_WorkItem] = []
    post_annual_count = 0
    for item in items:
        # Skip quarterly reports older than the annual
        if item.form_type in ("10-Q", "6-K"):
            if item.filing_date and item.filing_date < annual_date:
                logger.debug(
                    "Skipping %s (%s) -- superseded by 10-K (%s)",
                    item.form_type,
                    item.filing_date,
                    annual_date,
                )
                continue
            # Boost post-annual quarterly priority above 8-K (70)
            # so they survive the filing cap
            item = item._replace(priority=_POST_ANNUAL_Q_PRIORITY)
            post_annual_count += 1
        filtered.append(item)

    skipped = len(items) - len(filtered)
    if skipped > 0:
        logger.info(
            "Skipped %d quarterly filings older than 10-K (%s)",
            skipped,
            annual_date,
        )
    if post_annual_count > 0:
        logger.info(
            "Boosted %d post-annual quarterly filings to priority %d",
            post_annual_count,
            _POST_ANNUAL_Q_PRIORITY,
        )
    return filtered


def _extract_single_filing(
    extractor: Any,  # LLMExtractor
    item: _WorkItem,
) -> tuple[str, dict[str, Any] | None]:
    """Extract one filing via LLM. Thread-safe (extractor is locked)."""
    result = extractor.extract(
        filing_text=item.full_text,
        schema=item.schema,
        accession=item.accession,
        form_type=item.form_type,
        system_prompt=item.prompt,
        max_tokens=item.max_tokens,
    )
    if result is not None:
        return (item.key, result.model_dump())
    return (item.key, None)


def run_llm_extraction(
    state: AnalysisState,
    use_llm: bool,
    progress_fn: Callable[[str], None] | None = None,
    manifest: Any | None = None,
) -> dict[str, Any]:
    """Run LLM extraction on filing documents in parallel.

    Prioritizes filings by importance (10-K > DEF 14A > 8-K > 10-Q),
    skips quarterly reports superseded by the latest 10-K, and extracts
    up to 3 filings concurrently using ThreadPoolExecutor.

    The OpenAI SDK handles 429 rate-limit errors with exponential
    backoff (max_retries=10), so parallel requests self-regulate.

    Gracefully degrades: returns empty dict if LLM deps are missing,
    API key is unset, or any error occurs.

    Side effect: Stores LLM cost summary in state.pipeline_metadata["llm_cost"]
    for downstream consumption by the render stage's worksheet footer.

    Args:
        state: Current analysis state with acquired filing documents.
        use_llm: Whether LLM extraction is enabled.
        progress_fn: Optional callback for real-time progress display.

    Returns:
        Dict mapping 'form_type:accession' to serialized extraction dicts.
    """
    if not use_llm:
        logger.info("LLM extraction disabled (--no-llm or use_llm=False)")
        return {}

    if state.acquired_data is None:
        return {}

    filing_documents = state.acquired_data.filing_documents
    if not filing_documents:
        logger.debug("No filing_documents for LLM extraction")
        return {}

    try:
        from do_uw.stages.extract.llm import ExtractionCache, LLMExtractor
    except Exception:
        logger.warning("LLM extraction dependencies not available; continuing with regex only")
        return {}

    # Build prioritized, filtered work list (with company context for prompts)
    work_items = _prepare_work_items(
        filing_documents,
        manifest=manifest,
        company=state.company,
    )
    if not work_items:
        logger.debug("No extractable filings after filtering")
        return {}

    total = len(work_items)
    logger.info(
        "LLM extraction: %d filings to process (%d workers)",
        total,
        _MAX_EXTRACT_WORKERS,
    )
    if progress_fn:
        types = ", ".join(sorted({w.form_type for w in work_items}))
        progress_fn(f"LLM Extract: 0/{total} — queued: {types}")

    all_results: dict[str, Any] = {}
    try:
        cache = ExtractionCache(db_path=Path(".cache/analysis.db"))
        extractor = LLMExtractor(cache=cache, rate_limit_tpm=100_000_000)

        completed = 0
        with ThreadPoolExecutor(max_workers=_MAX_EXTRACT_WORKERS) as pool:
            futures = {
                pool.submit(_extract_single_filing, extractor, item): item for item in work_items
            }

            for future in as_completed(futures):
                item = futures[future]
                try:
                    key, result_dict = future.result()
                    if result_dict is not None:
                        all_results[key] = result_dict
                except Exception:
                    logger.warning(
                        "LLM extraction failed for %s (%s)",
                        item.accession,
                        item.form_type,
                        exc_info=True,
                    )

                completed += 1
                if progress_fn:
                    progress_fn(f"LLM Extract [{completed}/{total}]: {item.short_label}")

        # Log cost summary and persist to state for render footer
        summary = extractor.cost_summary
        cost_usd = summary.get("total_cost_usd", 0.0)
        logger.info(
            "LLM extraction complete: %d/%d filings, %d input tokens, %d output tokens, $%.4f",
            len(all_results),
            total,
            summary.get("total_input_tokens", 0),
            summary.get("total_output_tokens", 0),
            cost_usd,
        )

        # Persist cost data in state for downstream render footer
        state.pipeline_metadata["llm_cost"] = {
            "input_tokens": summary.get("total_input_tokens", 0),
            "output_tokens": summary.get("total_output_tokens", 0),
            "total_cost_usd": cost_usd,
            "extractions": summary.get("extraction_count", 0),
            "budget_usd": summary.get("budget_usd", 0.0),
        }

        if progress_fn:
            progress_fn(f"LLM Extract: {len(all_results)}/{total} filings done (${cost_usd:.4f})")
    except Exception:
        logger.warning(
            "LLM extraction failed; continuing with regex only",
            exc_info=True,
        )
        return {}

    return all_results
