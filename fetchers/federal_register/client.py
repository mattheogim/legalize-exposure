"""Federal Register API client.

Handles all HTTP communication with the Federal Register API.
Returns raw JSON dicts — data transformation is in mapper.py.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fetchers.base import HttpDataClient

logger = logging.getLogger(__name__)

FR_API_BASE = "https://www.federalregister.gov/api/v1"

# Default fields to request from the API.
_DEFAULT_FIELDS = [
    "document_number", "type", "title", "abstract",
    "agency_names", "publication_date", "effective_on",
    "comments_close_on", "docket_ids", "cfr_references",
    "html_url", "pdf_url", "significant", "action",
]

# Significant agencies to track.
MAJOR_AGENCIES = [
    "environmental-protection-agency",
    "securities-and-exchange-commission",
    "federal-trade-commission",
    "department-of-justice",
    "department-of-the-treasury",
    "internal-revenue-service",
    "federal-communications-commission",
    "department-of-health-and-human-services",
    "food-and-drug-administration",
    "department-of-labor",
    "department-of-homeland-security",
    "consumer-financial-protection-bureau",
    "department-of-energy",
    "department-of-education",
    "department-of-transportation",
]


class FederalRegisterClient(HttpDataClient):
    """HTTP client for the Federal Register API."""

    def __init__(
        self,
        *,
        base_url: str = FR_API_BASE,
        request_timeout: int = 30,
        max_retries: int = 3,
        requests_per_second: float = 2.0,
    ) -> None:
        super().__init__(
            base_url=base_url,
            request_timeout=request_timeout,
            max_retries=max_retries,
            requests_per_second=requests_per_second,
        )

    @classmethod
    def create(cls, source_config: dict[str, Any]) -> FederalRegisterClient:
        return cls(
            base_url=source_config.get("base_url", FR_API_BASE),
            request_timeout=source_config.get("request_timeout", 30),
            max_retries=source_config.get("max_retries", 3),
            requests_per_second=source_config.get("rate_limit_rps", 2.0),
        )

    def search_documents(
        self,
        *,
        doc_type: str | None = None,
        from_date: date | None = None,
        agency_slugs: list[str] | None = None,
        significant_only: bool = False,
        presidential_doc_type: str | None = None,
        per_page: int = 100,
        fields: list[str] | None = None,
    ) -> dict:
        """Search the Federal Register documents endpoint.

        Returns raw API response dict with 'results' and 'count'.
        """
        params: dict[str, Any] = {
            "per_page": min(per_page, 1000),
            "order": "newest",
            "fields[]": fields or _DEFAULT_FIELDS,
        }
        if doc_type:
            params["conditions[type][]"] = doc_type
        if from_date:
            params["conditions[publication_date][gte]"] = from_date.isoformat()
        if agency_slugs:
            params["conditions[agencies][]"] = agency_slugs
        if significant_only:
            params["conditions[significant]"] = "1"
        if presidential_doc_type:
            params["conditions[presidential_document_type][]"] = presidential_doc_type

        url = f"{self._base_url}/documents.json"
        return self._get_json(url, params=params)

    def fetch_proposed_rules(self, from_date: date | None = None, **kwargs) -> dict:
        """Fetch proposed rules (PRORULE)."""
        return self.search_documents(doc_type="PRORULE", from_date=from_date, **kwargs)

    def fetch_final_rules(self, from_date: date | None = None, **kwargs) -> dict:
        """Fetch final rules (RULE)."""
        return self.search_documents(doc_type="RULE", from_date=from_date, **kwargs)

    def fetch_executive_orders(self, from_date: date | None = None, **kwargs) -> dict:
        """Fetch executive orders (PRESDOC)."""
        return self.search_documents(
            doc_type="PRESDOC",
            presidential_doc_type="executive_order",
            from_date=from_date,
            **kwargs,
        )

    def fetch_significant(self, from_date: date | None = None, **kwargs) -> dict:
        """Fetch only significant regulatory actions."""
        return self.search_documents(significant_only=True, from_date=from_date, **kwargs)
