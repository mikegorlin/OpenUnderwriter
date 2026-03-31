"""Shared SEC EDGAR rate limiter and HTTP client.

Provides synchronous rate-limited GET functions for SEC EDGAR APIs.
All SEC EDGAR direct API calls (submissions, company_tickers, EFTS)
should go through these functions to respect the 10 req/sec limit.

EdgarTools MCP handles its own rate limiting -- do NOT double-limit
MCP calls through this module.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Per SEC requirements: User-Agent with application name and contact email.
SEC_USER_AGENT = "do-uw/0.1.0 (contact@example.com)"

# SEC EDGAR: max 10 requests per second (configurable via set_max_rps).
_sec_max_rps = 10
_sec_interval = 1.0 / _sec_max_rps  # 0.1 seconds between requests

# Module-level singleton lock and timestamp tracker for rate limiting.
_lock = threading.Lock()
_last_request_time: float = 0.0


def set_max_rps(rps: int) -> None:
    """Configure the maximum requests per second for SEC EDGAR.

    Clamps *rps* to the range [1, 10]. Thread-safe.

    Args:
        rps: Desired requests per second (clamped to 1..10).
    """
    global _sec_max_rps, _sec_interval
    clamped = max(1, min(10, rps))
    with _lock:
        _sec_max_rps = clamped
        _sec_interval = 1.0 / clamped


def get_max_rps() -> int:
    """Return the current maximum requests per second setting."""
    return _sec_max_rps


def _rate_limit() -> None:
    """Block until the next request is allowed under the RPS limit."""
    global _last_request_time
    with _lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < _sec_interval:
            sleep_time = _sec_interval - elapsed
            time.sleep(sleep_time)
        _last_request_time = time.monotonic()


def _build_client() -> httpx.Client:
    """Create a configured httpx Client for SEC EDGAR requests."""
    return httpx.Client(
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=10.0,  # Reduced from 30.0 to 10.0 seconds
        follow_redirects=True,
    )


# Module-level reusable client (lazy-initialized).
_client: httpx.Client | None = None
_client_lock = threading.Lock()


def _get_client() -> httpx.Client:
    """Return the module-level shared httpx client, creating if needed."""
    global _client
    with _client_lock:
        if _client is None:
            _client = _build_client()
        return _client


def _retry_wait(status_code: int, attempt: int) -> float:
    """Compute retry wait time based on error type and attempt number.

    Args:
        status_code: HTTP status code (0 for connection errors).
        attempt: Zero-based attempt index.

    Returns:
        Seconds to sleep before retrying, or -1.0 if no retry.
    """
    if status_code == 429:
        # SEC rate limit — back off aggressively
        return 15.0 * (attempt + 1)
    if status_code == 403:
        return 10.0
    if status_code >= 500 or status_code == 0:
        return 2.0 * (2**attempt)
    # Other 4xx -- do not retry
    return -1.0


def _sec_request(
    url: str,
    *,
    max_retries: int,
    label: str,
) -> httpx.Response:
    """Rate-limited GET with retry logic for SEC EDGAR.

    Args:
        url: Full URL to a SEC EDGAR endpoint.
        max_retries: Maximum number of retry attempts.
        label: Request label for log messages ("json" or "text").

    Returns:
        Successful httpx.Response.

    Raises:
        httpx.HTTPStatusError: On non-retryable or exhausted retries.
        httpx.RequestError: On persistent network failures.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        _rate_limit()
        client = _get_client()
        logger.debug("SEC GET (%s): %s", label, url)
        try:
            response = client.get(url)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            wait = _retry_wait(exc.response.status_code, attempt)
            if wait < 0 or attempt >= max_retries:
                raise
            last_exc = exc
            logger.warning(
                "SEC GET %s failed (HTTP %d), retrying in %.0fs (attempt %d/%d)",
                url,
                exc.response.status_code,
                wait,
                attempt + 1,
                max_retries,
            )
            time.sleep(wait)
        except httpx.RequestError as exc:
            wait = _retry_wait(0, attempt)
            if attempt >= max_retries:
                raise
            last_exc = exc
            logger.warning(
                "SEC GET %s failed (%s), retrying in %.0fs (attempt %d/%d)",
                url,
                type(exc).__name__,
                wait,
                attempt + 1,
                max_retries,
            )
            time.sleep(wait)

    # Should not reach here, but satisfy type checker
    if last_exc is not None:  # pragma: no cover
        raise last_exc
    msg = f"SEC GET {url} failed after {max_retries} retries"
    raise RuntimeError(msg)  # pragma: no cover


def sec_get(url: str, *, max_retries: int = 2) -> dict[str, Any]:
    """Rate-limited GET returning parsed JSON, with retry on 403/5xx."""
    response = _sec_request(url, max_retries=max_retries, label="json")
    result: dict[str, Any] = response.json()
    return result


def sec_get_text(url: str, *, max_retries: int = 2) -> str:
    """Rate-limited GET returning raw text, with retry on 403/5xx."""
    response = _sec_request(url, max_retries=max_retries, label="text")
    return response.text
