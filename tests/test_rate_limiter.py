"""Tests for SEC EDGAR rate limiter and retry logic.

Validates configurable RPS, exponential backoff on 403/5xx,
immediate failure on other 4xx, and connection error retry.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from do_uw.stages.acquire.rate_limiter import (
    get_max_rps,
    sec_get,
    sec_get_text,
    set_max_rps,
)


@pytest.fixture(autouse=True)
def _reset_rps() -> None:  # noqa: PT004
    """Reset RPS to default after each test."""
    yield  # type: ignore[misc]
    set_max_rps(10)


# --- set_max_rps / get_max_rps tests ---


def test_set_max_rps_updates_interval() -> None:
    """Setting RPS to 5 updates interval to 0.2."""
    set_max_rps(5)
    assert get_max_rps() == 5
    # Verify indirectly that interval changed
    import do_uw.stages.acquire.rate_limiter as rl

    assert rl._sec_interval == pytest.approx(0.2)


def test_set_max_rps_clamps_bounds() -> None:
    """RPS is clamped to [1, 10]."""
    set_max_rps(0)
    assert get_max_rps() == 1

    set_max_rps(20)
    assert get_max_rps() == 10


# --- Retry tests ---


def _make_http_error(
    status_code: int, url: str = "https://example.com",
) -> httpx.HTTPStatusError:
    """Create an HTTPStatusError with the given status code."""
    request = httpx.Request("GET", url)
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(
        f"{status_code}", request=request, response=response,
    )


@patch("do_uw.stages.acquire.rate_limiter.time")
@patch("do_uw.stages.acquire.rate_limiter._get_client")
def test_sec_get_retries_on_403(
    mock_get_client: MagicMock,
    mock_time: MagicMock,
) -> None:
    """sec_get retries on 403, succeeds on third attempt."""
    mock_time.monotonic.return_value = 999.0  # Skip rate limit wait

    mock_response_ok = MagicMock()
    mock_response_ok.raise_for_status.return_value = None
    mock_response_ok.json.return_value = {"ok": True}

    client = MagicMock()
    client.get.side_effect = [
        _make_403_response(),
        _make_403_response(),
        mock_response_ok,
    ]
    mock_get_client.return_value = client

    result = sec_get("https://data.sec.gov/test", max_retries=5)
    assert result == {"ok": True}
    assert client.get.call_count == 3


def _make_403_response() -> MagicMock:
    """Create a mock response that raises 403 on raise_for_status."""
    resp = MagicMock()
    resp.status_code = 403
    error = _make_http_error(403)
    resp.raise_for_status.side_effect = error
    return resp


def _make_500_response() -> MagicMock:
    """Create a mock response that raises 500 on raise_for_status."""
    resp = MagicMock()
    resp.status_code = 500
    error = _make_http_error(500)
    resp.raise_for_status.side_effect = error
    return resp


def _make_404_response() -> MagicMock:
    """Create a mock response that raises 404 on raise_for_status."""
    resp = MagicMock()
    resp.status_code = 404
    error = _make_http_error(404)
    resp.raise_for_status.side_effect = error
    return resp


@patch("do_uw.stages.acquire.rate_limiter.time")
@patch("do_uw.stages.acquire.rate_limiter._get_client")
def test_sec_get_retries_on_500(
    mock_get_client: MagicMock,
    mock_time: MagicMock,
) -> None:
    """sec_get retries on 500, succeeds on second attempt."""
    mock_time.monotonic.return_value = 999.0

    mock_response_ok = MagicMock()
    mock_response_ok.raise_for_status.return_value = None
    mock_response_ok.json.return_value = {"data": 42}

    client = MagicMock()
    client.get.side_effect = [_make_500_response(), mock_response_ok]
    mock_get_client.return_value = client

    result = sec_get("https://data.sec.gov/test", max_retries=5)
    assert result == {"data": 42}
    assert client.get.call_count == 2


@patch("do_uw.stages.acquire.rate_limiter.time")
@patch("do_uw.stages.acquire.rate_limiter._get_client")
def test_sec_get_no_retry_on_404(
    mock_get_client: MagicMock,
    mock_time: MagicMock,
) -> None:
    """sec_get raises immediately on 404 without retrying."""
    mock_time.monotonic.return_value = 999.0

    client = MagicMock()
    client.get.return_value = _make_404_response()
    mock_get_client.return_value = client

    with pytest.raises(httpx.HTTPStatusError):
        sec_get("https://data.sec.gov/test", max_retries=5)

    assert client.get.call_count == 1


@patch("do_uw.stages.acquire.rate_limiter.time")
@patch("do_uw.stages.acquire.rate_limiter._get_client")
def test_sec_get_text_retries_on_403(
    mock_get_client: MagicMock,
    mock_time: MagicMock,
) -> None:
    """sec_get_text retries on 403, succeeds on second attempt."""
    mock_time.monotonic.return_value = 999.0

    mock_response_ok = MagicMock()
    mock_response_ok.raise_for_status.return_value = None
    mock_response_ok.text = "<html>OK</html>"

    client = MagicMock()
    client.get.side_effect = [_make_403_response(), mock_response_ok]
    mock_get_client.return_value = client

    result = sec_get_text("https://data.sec.gov/test", max_retries=5)
    assert result == "<html>OK</html>"
    assert client.get.call_count == 2


@patch("do_uw.stages.acquire.rate_limiter.time")
@patch("do_uw.stages.acquire.rate_limiter._get_client")
def test_sec_get_retries_on_connection_error(
    mock_get_client: MagicMock,
    mock_time: MagicMock,
) -> None:
    """sec_get retries on connection errors with backoff."""
    mock_time.monotonic.return_value = 999.0

    mock_response_ok = MagicMock()
    mock_response_ok.raise_for_status.return_value = None
    mock_response_ok.json.return_value = {"ok": True}

    client = MagicMock()
    request = httpx.Request("GET", "https://data.sec.gov/test")
    client.get.side_effect = [
        httpx.ConnectError("Connection refused", request=request),
        mock_response_ok,
    ]
    mock_get_client.return_value = client

    result = sec_get("https://data.sec.gov/test", max_retries=5)
    assert result == {"ok": True}
    assert client.get.call_count == 2
