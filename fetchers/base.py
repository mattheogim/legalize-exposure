"""Abstract base for data source clients used by the exposure engine.

Adapted from legalize-pipeline's fetcher/base.py pattern. Provides:
- Thread-safe rate limiting
- Retry with exponential backoff
- Context manager support
- Factory classmethod for config-driven instantiation

Each US data source (Federal Register, Congress.gov, CourtListener, SEC/EDGAR)
implements a client inheriting from DataSourceClient or HttpDataClient.
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = "legalize-bot/1.0 (+https://github.com/legalize-dev/legalize)"
_RETRY_STATUS_CODES = (429, 502, 503, 504)


class DataSourceClient(ABC):
    """Base class for data source API clients.

    Each source implements its own client with endpoints for
    fetching documents, metadata, and search results.
    """

    @classmethod
    def create(cls, source_config: dict[str, Any]) -> DataSourceClient:
        """Create a client from source config (from config.yaml).

        Override in subclass to read source-specific params.
        Default: no-args constructor.
        """
        return cls()

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class HttpDataClient(DataSourceClient):
    """Base class for HTTP-based data source clients.

    Provides requests.Session with configurable User-Agent,
    thread-safe rate limiting, and retry with exponential backoff.
    """

    def __init__(
        self,
        *,
        base_url: str = "",
        user_agent: str = _DEFAULT_USER_AGENT,
        request_timeout: int = 30,
        max_retries: int = 3,
        requests_per_second: float = 2.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._timeout = request_timeout
        self._max_retries = max_retries

        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent
        if extra_headers:
            self._session.headers.update(extra_headers)

        # Thread-safe rate limiter.
        self._min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self._last_request: float = 0.0
        self._rate_lock = threading.Lock()

    def _wait_rate_limit(self) -> None:
        """Wait if needed to respect the rate limit."""
        if self._min_interval <= 0:
            return
        with self._rate_lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """HTTP request with rate limiting and retry on transient errors."""
        self._wait_rate_limit()
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout or self._timeout,
                )
                if resp.status_code in _RETRY_STATUS_CODES and attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "%s %d on %s, retrying in %ds (attempt %d/%d)",
                        method, resp.status_code, url, wait, attempt + 1, self._max_retries,
                    )
                    time.sleep(wait)
                    self._wait_rate_limit()
                    continue
                resp.raise_for_status()
                return resp
            except requests.HTTPError:
                raise
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("Request error (attempt %d/%d): %s", attempt + 1, self._max_retries, exc)
                    time.sleep(wait)
        raise last_exc or RuntimeError(f"Failed {method} {url}")

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET request returning the full Response object."""
        return self._request("GET", url, **kwargs)

    def _get_json(self, url: str, **kwargs) -> dict:
        """GET request returning parsed JSON."""
        return self._get(url, **kwargs).json()

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
