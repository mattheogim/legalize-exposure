"""CourtListener API client.

Handles HTTP communication with the CourtListener API v4.
Requires a free API token (sign up at courtlistener.com).
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

from fetchers.base import HttpDataClient

logger = logging.getLogger(__name__)

CL_BASE = "https://www.courtlistener.com"

COURT_LEVELS = {
    "scotus": ("supreme-court", "Supreme Court of the United States"),
    "ca1": ("1st-circuit", "First Circuit"),
    "ca2": ("2nd-circuit", "Second Circuit"),
    "ca3": ("3rd-circuit", "Third Circuit"),
    "ca4": ("4th-circuit", "Fourth Circuit"),
    "ca5": ("5th-circuit", "Fifth Circuit"),
    "ca6": ("6th-circuit", "Sixth Circuit"),
    "ca7": ("7th-circuit", "Seventh Circuit"),
    "ca8": ("8th-circuit", "Eighth Circuit"),
    "ca9": ("9th-circuit", "Ninth Circuit"),
    "ca10": ("10th-circuit", "Tenth Circuit"),
    "ca11": ("11th-circuit", "Eleventh Circuit"),
    "cadc": ("dc-circuit", "D.C. Circuit"),
    "cafc": ("federal-circuit", "Federal Circuit"),
}


class CourtListenerClient(HttpDataClient):
    """HTTP client for the CourtListener API v4."""

    def __init__(
        self,
        *,
        base_url: str = CL_BASE,
        api_token: str = "",
        request_timeout: int = 30,
        max_retries: int = 3,
        requests_per_second: float = 1.0,
    ) -> None:
        extra_headers = {}
        token = api_token or os.environ.get("COURTLISTENER_API_TOKEN", "")
        if token:
            extra_headers["Authorization"] = f"Token {token}"

        super().__init__(
            base_url=base_url,
            request_timeout=request_timeout,
            max_retries=max_retries,
            requests_per_second=requests_per_second,
            extra_headers=extra_headers,
        )

    @classmethod
    def create(cls, source_config: dict[str, Any]) -> CourtListenerClient:
        api_token = source_config.get("api_token", "")
        if api_token.startswith("${") and api_token.endswith("}"):
            api_token = os.environ.get(api_token[2:-1], "")
        return cls(
            base_url=source_config.get("base_url", CL_BASE),
            api_token=api_token,
            request_timeout=source_config.get("request_timeout", 30),
            max_retries=source_config.get("max_retries", 3),
            requests_per_second=source_config.get("rate_limit_rps", 1.0),
        )

    def search_opinions(
        self,
        court: str = "scotus",
        from_date: date | None = None,
        limit: int = 50,
    ) -> dict:
        """Search court opinions. Returns raw API response."""
        params: dict[str, Any] = {
            "type": "o",
            "court": court,
            "order_by": "dateFiled desc",
            "page_size": min(limit, 100),
        }
        if from_date:
            params["filed_after"] = from_date.isoformat()
        url = f"{self._base_url}/api/rest/v4/search/"
        return self._get_json(url, params=params)

    def get_opinion(self, opinion_id: int) -> dict:
        """Fetch a single opinion by ID."""
        url = f"{self._base_url}/api/rest/v4/opinions/{opinion_id}/"
        return self._get_json(url)
