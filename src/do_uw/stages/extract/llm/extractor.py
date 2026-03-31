"""LLM-powered filing extraction using instructor + DeepSeek.

Sends complete filing documents to DeepSeek-V3.2 (deepseek-chat or deepseek-reasoner)
with a Pydantic schema and receives validated structured data back. Supports caching,
cost tracking, rate limiting, and graceful degradation.

Rate limiting: The DeepSeek API has rate limits; large SEC filings (80-150k tokens)
can exceed per-minute budgets, so this module implements proactive inter-request
delays based on token estimates and configurable TPM limits.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from do_uw.stages.extract.llm.boilerplate import (
    estimate_tokens,
    strip_boilerplate,
)
from do_uw.stages.extract.llm.cache import ExtractionCache
from do_uw.stages.extract.llm.cost_tracker import CostTracker

try:
    import openai as openai  # type: ignore[import-untyped]
    import instructor as instructor
    from instructor import Mode
    import httpx
except ImportError:  # pragma: no cover
    openai = None  # type: ignore[assignment]
    instructor = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Default LLM model for extraction. Override via DO_UW_LLM_MODEL env var.
DEFAULT_LLM_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

# Maximum token estimate before rejecting a filing as too large
# DeepSeek-V3.2 has 128k context; leave room for system prompt + schema + output
MAX_INPUT_TOKEN_ESTIMATE = 120_000

# Default rate limit conservative estimate (actual org limit may differ)
# Increased for DeepSeek aggressive optimization (user directive: "push it to the limit")
_DEFAULT_RATE_LIMIT_TPM = 100_000_000  # Effectively no rate limiting (100M TPM)


def schema_hash(model: type[BaseModel]) -> str:
    """Generate deterministic hash of a Pydantic model's JSON schema.

    Used as the schema_version component of the cache key so that
    cache entries automatically invalidate when schemas change.

    Args:
        model: Pydantic model class to hash.

    Returns:
        First 12 characters of the SHA-256 hex digest.
    """
    schema = model.model_json_schema()
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


class LLMExtractor:
    """LLM-powered filing extractor using instructor + DeepSeek.

    Sends complete filing documents to a DeepSeek model with a Pydantic
    schema and returns validated structured data. Caches results by
    (accession_number, form_type, schema_version) to prevent re-extraction.

    Implements proactive rate limiting: before each API call, calculates
    the required delay based on token estimates and the configured TPM
    limit, then sleeps accordingly. This prevents 429 rate limit errors
    rather than relying solely on retry backoff.

    All error paths return None (never raises). Callers should fall
    back to regex extraction when None is returned.
    """

    def __init__(
        self,
        model: str = f"openai/{DEFAULT_LLM_MODEL}",
        max_retries: int = 2,
        cache: ExtractionCache | None = None,
        budget_usd: float = 2.0,
        rate_limit_tpm: int = _DEFAULT_RATE_LIMIT_TPM,
    ) -> None:
        """Initialize the extractor.

        Args:
            model: Model identifier for instructor.from_provider().
            max_retries: Number of retries on validation failure.
            cache: Optional extraction cache instance.
            budget_usd: Maximum cost budget in USD.
            rate_limit_tpm: Tokens per minute rate limit (default 40k).
        """
        self._model = model
        # Strip provider prefix for direct OpenAI client usage
        self._model_name = model.removeprefix("openai/") if model else model
        self._max_retries = max_retries
        self._cache = cache
        self._cost_tracker = CostTracker(budget_usd=budget_usd)
        self._rate_limit_tpm = rate_limit_tpm
        self._last_call_time: float = 0.0
        self._last_token_count: int = 0
        self._rate_lock = threading.Lock()

    def extract(
        self,
        filing_text: str,
        schema: type[T],
        accession: str,
        form_type: str,
        system_prompt: str,
        max_tokens: int = 8192,
        company_context: str = "",
    ) -> T | None:
        """Extract structured data from a filing document.

        Args:
            filing_text: Complete filing document text.
            schema: Pydantic model class defining extraction schema.
            accession: SEC accession number (cache key).
            form_type: Filing form type, e.g. "10-K" (cache key).
            system_prompt: System prompt for the LLM.
            max_tokens: Maximum output tokens for the response.
            company_context: Optional company context overlay (sector,
                size, business model) appended to system prompt so the
                LLM can calibrate extraction for this company type.

        Returns:
            Validated Pydantic model instance, or None on failure.
        """
        # Append company context to system prompt if provided
        if company_context:
            system_prompt = system_prompt + company_context
        # Guard: dependencies available
        if instructor is None or openai is None:
            logger.warning(
                "instructor/openai not installed; skipping LLM extraction for %s",
                accession,
            )
            return None

        # Guard: API key set
        if not os.environ.get("DEEPSEEK_API_KEY"):
            logger.warning(
                "DEEPSEEK_API_KEY not set; skipping LLM extraction for %s",
                accession,
            )
            return None

        # Guard: budget check
        if self._cost_tracker.is_over_budget():
            logger.warning(
                "Cost budget exceeded (%.4f USD); skipping LLM extraction for %s",
                self._cost_tracker.total_cost_usd,
                accession,
            )
            return None

        # Compute schema version for cache key
        version = schema_hash(schema)

        # Check cache
        if self._cache is not None:
            cached = self._cache.get(accession, form_type, version)
            if cached is not None:
                logger.debug(
                    "Cache hit for %s/%s/%s",
                    accession,
                    form_type,
                    version,
                )
                return schema.model_validate_json(cached)

        # Strip boilerplate to reduce token count
        cleaned_text = strip_boilerplate(filing_text)

        # Quick token estimate check
        token_est = estimate_tokens(cleaned_text)
        if token_est > MAX_INPUT_TOKEN_ESTIMATE:
            logger.warning(
                "Filing %s too large (~%d tokens after stripping); skipping LLM extraction",
                accession,
                token_est,
            )
            return None

        # Proactive rate limiting: wait before making API call
        logger.debug("Checking rate limit for %s (~%d tokens)", accession, token_est)
        self._wait_for_rate_limit(token_est)
        logger.debug("Rate limit check passed for %s", accession)

        # Record call timing BEFORE the call (so even failed calls
        # contribute to rate limit tracking). Thread-safe.
        with self._rate_lock:
            self._last_call_time = time.monotonic()
            self._last_token_count = token_est
            logger.debug(
                "Recorded rate limit timing: time=%f, tokens=%d",
                self._last_call_time,
                self._last_token_count,
            )

        # Call the LLM via instructor wrapping DeepSeek client.
        # max_retries=10 on OpenAI SDK gives exponential backoff up to ~8min
        # which handles TPM rate limits on large filings.
        result = self._call_llm(cleaned_text, schema, system_prompt, max_tokens, accession)
        if result is None:
            return None

        # Record cost (estimate from text lengths since instructor
        # returns the Pydantic model directly, not raw response with usage)
        input_tokens = estimate_tokens(cleaned_text)
        result_json = result.model_dump_json()
        output_tokens = estimate_tokens(result_json)
        cost = self._cost_tracker.record(input_tokens, output_tokens)

        # Cache the result
        if self._cache is not None:
            self._cache.set(
                accession,
                form_type,
                version,
                result_json,
                input_tokens,
                output_tokens,
                cost,
                self._model,
            )

        logger.info(
            "LLM extraction complete for %s (%s): ~%d input tokens, $%.4f",
            accession,
            form_type,
            input_tokens,
            cost,
        )

        # Warn when approaching budget limit
        budget = self._cost_tracker.budget_usd
        used = self._cost_tracker.total_cost_usd
        if budget > 0:
            pct = (used / budget) * 100.0
            if pct >= 80.0:
                logger.warning(
                    "Cost budget %.0f%% consumed ($%.2f/$%.2f) for current company",
                    pct,
                    used,
                    budget,
                )

        return result

    def _call_llm(
        self,
        cleaned_text: str,
        schema: type[T],
        system_prompt: str,
        max_tokens: int,
        accession: str,
    ) -> T | None:
        """Make the actual LLM API call with retry handling.

        Uses exponential backoff via the OpenAI SDK (max_retries=10)
        to handle 429 rate limit errors on large filings. Falls back
        to None on any failure.

        Args:
            cleaned_text: Boilerplate-stripped filing text.
            schema: Pydantic response model.
            system_prompt: System prompt for extraction.
            max_tokens: Maximum output tokens.
            accession: For logging.

        Returns:
            Validated Pydantic model, or None on failure.
        """
        try:
            # Guards already checked in extract(); assert for pyright
            assert openai is not None  # noqa: S101
            assert instructor is not None  # noqa: S101
            logger.debug("Creating HTTP client for DeepSeek API call")
            # Custom HTTP client with generous timeouts for large filings
            http_client = httpx.Client(
                timeout=httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
            raw_client = openai.OpenAI(
                api_key=os.environ.get("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                max_retries=3,
                timeout=180.0,  # fallback
                http_client=http_client,
            )
            logger.debug("Patching OpenAI client with instructor (mode=JSON)")
            client = instructor.patch(raw_client, mode=instructor.Mode.JSON)
            # Cap max_tokens for DeepSeek API (valid range [1, 8192])
            capped_tokens = max(1, min(max_tokens, 8192))
            if capped_tokens != max_tokens:
                logger.debug(f"Capped max_tokens from {max_tokens} to {capped_tokens}")

            logger.info(
                "Making DeepSeek API call for %s (model: %s, tokens: %d)",
                accession,
                self._model_name,
                capped_tokens,
            )
            start_time = time.monotonic()
            result = cast(
                T,
                client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": cleaned_text},
                    ],
                    response_model=schema,
                    max_tokens=capped_tokens,
                    max_retries=1,
                ),
            )
            elapsed = time.monotonic() - start_time
            logger.info("DeepSeek API call completed for %s in %.1fs", accession, elapsed)
            return result
        except Exception as exc:
            logger.warning(
                "LLM extraction failed for %s (%s): %s",
                accession,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            return None

    def _wait_for_rate_limit(self, next_tokens: int) -> None:
        """Sleep to stay under the tokens-per-minute rate limit.

        Calculates delay based on the previous request's token count
        and the configured TPM. Thread-safe: reads state under lock,
        then sleeps without holding the lock.

        Args:
            next_tokens: Estimated token count for the upcoming request.
        """
        with self._rate_lock:
            if self._last_call_time == 0.0:
                return  # First call, no wait needed
            prev_tokens = self._last_token_count
            last_time = self._last_call_time

        # Compute wait outside lock so other threads aren't blocked
        total_tokens = prev_tokens + next_tokens
        seconds_needed = (total_tokens / self._rate_limit_tpm) * 60.0
        seconds_needed += 0.0  # No safety margin for aggressive optimization

        elapsed = time.monotonic() - last_time
        wait = seconds_needed - elapsed
        if wait > 0:
            logger.info(
                "Rate limiting: waiting %.0fs before next extraction "
                "(~%dk prev + ~%dk next tokens, %dk TPM limit)",
                wait,
                prev_tokens // 1000,
                next_tokens // 1000,
                self._rate_limit_tpm // 1000,
            )
            time.sleep(wait)
        else:
            logger.debug(
                "Rate limiting: no wait needed (elapsed %.2fs, needed %.2fs)",
                elapsed,
                seconds_needed,
            )

    def extract_raw(
        self,
        filing_text: str,
        accession: str,
        form_type: str,
        system_prompt: str,
        max_tokens: int = 8192,
        company_context: str = "",
    ) -> dict[str, Any] | None:
        """Extract raw JSON data without a strict schema.

        Returns a dict parsed from LLM JSON response, or None on failure.
        """
        from pydantic import RootModel

        class RawDict(RootModel[dict[str, Any]]):
            pass

        result = self.extract(
            filing_text=filing_text,
            schema=RawDict,
            accession=accession,
            form_type=form_type,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            company_context=company_context,
        )
        if result is None:
            return None
        return result.root

    @property
    def cost_summary(self) -> dict[str, Any]:
        """Return cost tracking summary."""
        return self._cost_tracker.summary()
