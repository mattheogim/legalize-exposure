"""Congress.gov API client.

Handles HTTP communication with the Congress.gov API v3.
Requires an API key (set via config or CONGRESS_API_KEY env var).
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

from fetchers.base import HttpDataClient

logger = logging.getLogger(__name__)

CONGRESS_API_BASE = "https://api.congress.gov/v3"
DEFAULT_API_KEY = "DEMO_KEY"

BILL_TYPES = {
    "hr": "House Bill",
    "s": "Senate Bill",
    "hjres": "House Joint Resolution",
    "sjres": "Senate Joint Resolution",
    "hconres": "House Concurrent Resolution",
    "sconres": "Senate Concurrent Resolution",
    "hres": "House Simple Resolution",
    "sres": "Senate Simple Resolution",
}

TRACKED_ACTIONS = {
    "IntroReferral",
    "Committee",
    "Floor",
    "BecameLaw",
    "President",
    "Calendars",
    "ResolvingDifferences",
}


class CongressClient(HttpDataClient):
    """HTTP client for the Congress.gov API."""

    def __init__(
        self,
        *,
        base_url: str = CONGRESS_API_BASE,
        api_key: str = "",
        request_timeout: int = 30,
        max_retries: int = 3,
        requests_per_second: float = 1.0,
    ) -> None:
        super().__init__(
            base_url=base_url,
            request_timeout=request_timeout,
            max_retries=max_retries,
            requests_per_second=requests_per_second,
        )
        self._api_key = api_key or os.environ.get("CONGRESS_API_KEY", DEFAULT_API_KEY)

    @classmethod
    def create(cls, source_config: dict[str, Any]) -> CongressClient:
        api_key = source_config.get("api_key", "")
        # Resolve ${ENV_VAR} syntax.
        if api_key.startswith("${") and api_key.endswith("}"):
            api_key = os.environ.get(api_key[2:-1], DEFAULT_API_KEY)
        return cls(
            base_url=source_config.get("base_url", CONGRESS_API_BASE),
            api_key=api_key,
            request_timeout=source_config.get("request_timeout", 30),
            max_retries=source_config.get("max_retries", 3),
            requests_per_second=source_config.get("rate_limit_rps", 1.0),
        )

    def _api_get(self, endpoint: str, params: dict | None = None) -> dict:
        """Authenticated API request."""
        params = params or {}
        params["api_key"] = self._api_key
        params["format"] = "json"
        url = f"{self._base_url}/{endpoint}"
        return self._get_json(url, params=params)

    def fetch_bills(
        self,
        congress: int = 119,
        bill_type: str = "hr",
        limit: int = 50,
        from_date: date | None = None,
    ) -> dict:
        """Fetch bills from the API. Returns raw API response."""
        params: dict[str, Any] = {"limit": min(limit, 250)}
        if from_date:
            params["fromDateTime"] = f"{from_date.isoformat()}T00:00:00Z"
        return self._api_get(f"bill/{congress}/{bill_type}", params)

    def fetch_bill_actions(self, congress: int, bill_type: str, number: int) -> dict:
        """Fetch action history for a specific bill."""
        return self._api_get(f"bill/{congress}/{bill_type}/{number}/actions")
