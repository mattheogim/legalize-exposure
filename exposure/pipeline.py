"""End-to-end pipeline: Federal Register API → Exposure Mapping.

This is the live runner. It fetches real documents from the FR API,
maps them through the exposure engine, and produces reports.

No authentication required for FR API.

Usage:
    python -m exposure.pipeline --days 7 --type RULE
    python -m exposure.pipeline --days 30 --significant
    python -m exposure.pipeline --doc 2026-12345
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import date, timedelta
from typing import Optional

from .fr_connector import FRExposureConnector, PipelineResult


FR_API_BASE = "https://www.federalregister.gov/api/v1"

# Fields we request from the API
FR_FIELDS = [
    "document_number", "type", "title", "abstract",
    "agency_names", "publication_date", "effective_on",
    "comments_close_on", "docket_ids", "cfr_references",
    "html_url", "pdf_url", "significant", "action",
]


def _api_get(url: str, params: dict, retries: int = 2) -> dict:
    """Make a GET request to the FR API with basic retry."""
    # Build URL with params (handle list params)
    query_parts = []
    for key, val in params.items():
        if isinstance(val, list):
            for item in val:
                query_parts.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(str(item))}")
        else:
            query_parts.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(str(val))}")

    full_url = f"{url}?{'&'.join(query_parts)}"

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(full_url, headers={
                "User-Agent": "Legalize/0.1 (regulation-exposure-mapper)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            else:
                raise RuntimeError(f"FR API request failed after {retries+1} attempts: {e}")


def fetch_documents(
    doc_types: list[str] | None = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    significant_only: bool = False,
    agency_slugs: list[str] | None = None,
    per_page: int = 50,
) -> list[dict]:
    """Fetch documents from the Federal Register API.

    Returns raw API result dicts.
    """
    params: dict = {
        "per_page": str(min(per_page, 1000)),
        "order": "newest",
        "fields[]": FR_FIELDS,
    }

    if doc_types:
        params["conditions[type][]"] = doc_types
    if from_date:
        params["conditions[publication_date][gte]"] = from_date.isoformat()
    if to_date:
        params["conditions[publication_date][lte]"] = to_date.isoformat()
    if significant_only:
        params["conditions[significant]"] = "1"
    if agency_slugs:
        params["conditions[agencies][]"] = agency_slugs

    url = f"{FR_API_BASE}/documents.json"
    data = _api_get(url, params)
    return data.get("results", [])


def fetch_single_document(doc_number: str) -> Optional[dict]:
    """Fetch a single document by document number."""
    url = f"{FR_API_BASE}/documents/{doc_number}.json"
    params = {"fields[]": FR_FIELDS}
    try:
        return _api_get(url, params)
    except Exception:
        return None


def run_pipeline(
    doc_types: list[str] | None = None,
    days: int = 7,
    significant_only: bool = False,
    agency_slugs: list[str] | None = None,
    doc_number: Optional[str] = None,
    per_page: int = 50,
    min_etfs: int = 0,
) -> list[PipelineResult]:
    """Run the full pipeline: fetch → map → return results.

    Args:
        doc_types: Filter by type (RULE, PRORULE, NOTICE, PRESDOC)
        days: How many days back to look
        significant_only: Only significant regulations
        agency_slugs: Filter by agency
        doc_number: Fetch a single document by number
        per_page: Results per page
        min_etfs: Minimum ETF matches to include
    """
    connector = FRExposureConnector()

    if doc_number:
        # Single document mode
        doc = fetch_single_document(doc_number)
        if not doc:
            print(f"Document {doc_number} not found", file=sys.stderr)
            return []
        result = connector.map_from_api_json(doc)
        return [result] if result else []

    # Batch mode
    from_date = date.today() - timedelta(days=days)
    documents = fetch_documents(
        doc_types=doc_types,
        from_date=from_date,
        significant_only=significant_only,
        agency_slugs=agency_slugs,
        per_page=per_page,
    )

    print(f"Fetched {len(documents)} documents from FR API", file=sys.stderr)
    results = connector.map_batch(documents, min_etfs=min_etfs)
    print(f"Mapped {len(results)} documents to exposure", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Legalize: Federal Register → Exposure Mapping Pipeline"
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days back to fetch (default: 7)"
    )
    parser.add_argument(
        "--type", nargs="+", choices=["RULE", "PRORULE", "NOTICE", "PRESDOC"],
        help="Document types to fetch"
    )
    parser.add_argument(
        "--significant", action="store_true",
        help="Only fetch significant regulations"
    )
    parser.add_argument(
        "--agency", nargs="+",
        help="Agency slugs to filter by"
    )
    parser.add_argument(
        "--doc", type=str,
        help="Fetch a single document by number"
    )
    parser.add_argument(
        "--per-page", type=int, default=50,
        help="Results per page (max 1000)"
    )
    parser.add_argument(
        "--min-etfs", type=int, default=1,
        help="Minimum ETF matches to show (default: 1)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of Markdown"
    )

    args = parser.parse_args()

    results = run_pipeline(
        doc_types=args.type,
        days=args.days,
        significant_only=args.significant,
        agency_slugs=args.agency,
        doc_number=args.doc,
        per_page=args.per_page,
        min_etfs=args.min_etfs,
    )

    if args.json:
        output = []
        for r in results:
            output.append({
                "document_number": r.document_number,
                "title": r.title,
                "doc_type": r.doc_type,
                "agency": r.agency_slug,
                "publication_date": r.publication_date.isoformat() if r.publication_date else None,
                "significant": r.significant,
                "industries": [i.naics_code for i in r.mapping.industries],
                "etfs": r.etf_tickers,
                "contamination_score": r.contamination_score,
                "html_url": r.html_url,
            })
        print(json.dumps(output, indent=2))
    else:
        connector = FRExposureConnector()
        report = connector.generate_report(results)
        print(report)


if __name__ == "__main__":
    main()
