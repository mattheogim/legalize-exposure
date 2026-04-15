"""Canadian case law fetcher: Fetch court decisions from CanLII API.

Data source:
 - CanLII API: https://api.canlii.org/v1/
 - API docs: https://github.com/canlii/API_documentation
 - Requires API key (free, request via https://www.canlii.org/en/feedback.html)

Usage:
  fetcher = CanLIICaseFetcher(api_key="your-key")

  # List available court databases
  courts = fetcher.list_courts()

  # Fetch Supreme Court of Canada decisions
  for doc in fetcher.fetch_court("csc-scc", limit=100):
      print(doc.case_name, doc.citation)

  # Fetch all courts
  for doc in fetcher.fetch_all(limit_per_court=50):
      print(doc.court_name, doc.case_name)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

from ..utils import ThrottledClient

logger = logging.getLogger(__name__)

CANLII_BASE = "https://api.canlii.org/v1"

# Major Canadian courts — court_id → (directory_name, display_name)
CANADIAN_COURTS = {
    # Supreme Court
    "csc-scc": ("supreme-court", "Supreme Court of Canada"),
    # Federal Courts
    "fca-caf": ("federal-court-appeal", "Federal Court of Appeal"),
    "fct-cf": ("federal-court", "Federal Court"),
    # Provincial Supreme/Appeal Courts
    "onca": ("on-court-appeal", "Ontario Court of Appeal"),
    "onsc": ("on-superior-court", "Ontario Superior Court"),
    "bcca": ("bc-court-appeal", "BC Court of Appeal"),
    "bcsc": ("bc-supreme-court", "BC Supreme Court"),
    "abca": ("ab-court-appeal", "Alberta Court of Appeal"),
    "abqb": ("ab-court-queens-bench", "Alberta Court of Queen's Bench"),
    "qcca": ("qc-court-appeal", "Quebec Court of Appeal"),
    "qccs": ("qc-superior-court", "Quebec Superior Court"),
    "skca": ("sk-court-appeal", "Saskatchewan Court of Appeal"),
    "mbca": ("mb-court-appeal", "Manitoba Court of Appeal"),
    "nsca": ("ns-court-appeal", "Nova Scotia Court of Appeal"),
    "nbca": ("nb-court-appeal", "New Brunswick Court of Appeal"),
    "peca": ("pe-court-appeal", "PEI Court of Appeal"),
    "nlca": ("nl-court-appeal", "Newfoundland Court of Appeal"),
}


class CaseDocument:
    """A Canadian court decision as a structured document."""

    def __init__(
        self,
        case_name: str,
        citation: str,
        court_id: str,
        court_name: str,
        decision_date: Optional[date],
        docket_number: str,
        body_markdown: str,
        source_url: str,
        lang: str = "en",
        keywords: Optional[list[str]] = None,
    ):
        self.case_name = case_name
        self.citation = citation
        self.court_id = court_id
        self.court_name = court_name
        self.decision_date = decision_date
        self.docket_number = docket_number
        self.body_markdown = body_markdown
        self.source_url = source_url
        self.lang = lang
        self.keywords = keywords or []

    @property
    def slug(self) -> str:
        """Generate filesystem-safe slug from citation."""
        text = self.citation or self.case_name
        # CanLII citations like "2016 SCC 27" → "2016scc27"
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_]+", "", slug).strip("-")
        return slug[:120]

    @property
    def output_dir(self) -> str:
        """Directory path based on court."""
        court_dir, _ = CANADIAN_COURTS.get(
            self.court_id,
            (self.court_id, self.court_name),
        )
        return court_dir

    @property
    def output_path(self) -> str:
        """Full output path: {court_dir}/{slug}.md"""
        return f"{self.output_dir}/{self.slug}.md"

    def to_frontmatter(self) -> dict:
        """Generate YAML frontmatter dict."""
        fm = {
            "case_name": self.case_name,
            "citation": self.citation,
            "court": self.court_name,
            "court_id": self.court_id,
            "decision_date": str(self.decision_date) if self.decision_date else "",
            "docket_number": self.docket_number,
            "lang": self.lang,
            "country": "ca",
            "source": self.source_url,
        }
        if self.keywords:
            fm["keywords"] = self.keywords
        return fm

    def to_markdown(self) -> str:
        """Generate full Markdown file content."""
        fm = self.to_frontmatter()
        lines = ["---"]
        for k, v in fm.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            elif isinstance(v, str) and (":" in v or '"' in v or "\n" in v):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {self.case_name}")
        lines.append("")
        if self.body_markdown.strip():
            lines.append(self.body_markdown)
        return "\n".join(lines)


def _parse_date(date_str: str) -> Optional[date]:
    """Parse CanLII date format (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


class CanLIICaseFetcher:
    """Fetch Canadian court decisions from the CanLII API."""

    def __init__(self, api_key: str, lang: str = "en", throttle: float = 0.5):
        """Initialize fetcher.

        Args:
            api_key: CanLII API key (request at https://www.canlii.org/en/feedback.html).
            lang: Language for API responses ("en" or "fr").
            throttle: Seconds between API requests.
        """
        self.api_key = api_key
        self.lang = lang
        self.client = ThrottledClient(throttle=throttle)

    def _api_url(self, endpoint: str) -> str:
        """Build a CanLII API URL with the API key."""
        sep = "&" if "?" in endpoint else "?"
        return f"{CANLII_BASE}/{endpoint}{sep}api_key={self.api_key}"

    def list_courts(self) -> list[dict]:
        """List all available case databases (courts/tribunals).

        Returns:
            List of dicts with 'databaseId', 'name', 'jurisdiction'.
        """
        url = self._api_url(f"caseBrowse/{self.lang}/")
        resp = self.client.get_text(url)
        data = json.loads(resp)
        courts = data.get("caseDatabases", [])
        logger.info(f"Found {len(courts)} court databases")
        return courts

    def fetch_court(
        self,
        database_id: str,
        limit: int = 0,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Iterator[CaseDocument]:
        """Fetch cases from a specific court database.

        Args:
            database_id: CanLII database ID (e.g. "csc-scc" for SCC).
            limit: Max number of cases (0 = no limit).
            after: Only cases decided after this date (YYYY-MM-DD).
            before: Only cases decided before this date (YYYY-MM-DD).

        Yields:
            CaseDocument for each case.
        """
        court_dir, court_name = CANADIAN_COURTS.get(
            database_id,
            (database_id, database_id),
        )

        offset = 0
        batch_size = 100  # CanLII max per request
        count = 0

        while True:
            # Build URL with filters
            params = f"offset={offset}&resultCount={batch_size}"
            if after:
                params += f"&decisionDateAfter={after}"
            if before:
                params += f"&decisionDateBefore={before}"

            url = self._api_url(f"caseBrowse/{self.lang}/{database_id}/?{params}")
            logger.info(f"Fetching cases from {database_id} (offset={offset})")

            resp = self.client.get_text(url)
            data = json.loads(resp)
            cases = data.get("cases", [])

            if not cases:
                break

            for case_info in cases:
                try:
                    doc = self._fetch_case_detail(database_id, case_info, court_name)
                    if doc:
                        yield doc
                        count += 1
                        if limit and count >= limit:
                            return
                except Exception as e:
                    case_id = case_info.get("caseId", {}).get("en", "unknown")
                    logger.error(f"Failed to fetch case {case_id}: {e}")

            offset += batch_size

            # CanLII caps at 10,000 results
            if offset >= 10000:
                logger.warning(f"Reached CanLII 10,000 result limit for {database_id}")
                break

        logger.info(f"Fetched {count} cases from {database_id}")

    def _fetch_case_detail(
        self,
        database_id: str,
        case_info: dict,
        court_name: str,
    ) -> Optional[CaseDocument]:
        """Fetch full case metadata and build a CaseDocument.

        Note: CanLII API provides metadata but NOT full text.
        Full text must be scraped from the CanLII website.
        The body will contain the case URL for reference.
        """
        case_id_obj = case_info.get("caseId", {})
        case_id = case_id_obj.get("en", "") if isinstance(case_id_obj, dict) else str(case_id_obj)

        if not case_id:
            return None

        # Get detailed metadata
        url = self._api_url(f"caseBrowse/{self.lang}/{database_id}/{case_id}/")
        resp = self.client.get_text(url)
        detail = json.loads(resp)

        title = detail.get("title", case_info.get("title", ""))
        citation = detail.get("citation", "")
        decision_date = _parse_date(detail.get("decisionDate", ""))
        docket = detail.get("docketNumber", "")
        keywords = detail.get("keywords", [])
        case_url = detail.get("url", "")

        # CanLII API doesn't provide full text — link to the case
        body = f"[Read full decision on CanLII]({case_url})"

        # Try to get citing/cited cases
        try:
            citator_url = self._api_url(
                f"caseCitator/en/{database_id}/{case_id}/citedCases"
            )
            citator_resp = self.client.get_text(citator_url)
            citator_data = json.loads(citator_resp)
            cited = citator_data.get("citedCases", [])
            if cited:
                body += "\n\n## Cases Cited\n\n"
                for c in cited[:20]:  # Cap at 20
                    c_title = c.get("title", "")
                    c_citation = c.get("citation", "")
                    body += f"- {c_title} ({c_citation})\n"
        except Exception:
            pass  # Citator may not be available for all cases

        return CaseDocument(
            case_name=title,
            citation=citation,
            court_id=database_id,
            court_name=court_name,
            decision_date=decision_date,
            docket_number=docket,
            body_markdown=body,
            source_url=case_url,
            lang=self.lang,
            keywords=keywords if isinstance(keywords, list) else [],
        )

    def fetch_all(
        self,
        courts: Optional[list[str]] = None,
        limit_per_court: int = 0,
    ) -> Iterator[CaseDocument]:
        """Fetch cases from multiple courts.

        Args:
            courts: List of database IDs. Defaults to all major courts.
            limit_per_court: Max cases per court (0 = no limit).

        Yields:
            CaseDocument for each case.
        """
        target_courts = courts or list(CANADIAN_COURTS.keys())
        logger.info(f"Fetching cases from {len(target_courts)} courts")

        for court_id in target_courts:
            try:
                yield from self.fetch_court(court_id, limit=limit_per_court)
            except Exception as e:
                logger.error(f"Failed to fetch court {court_id}: {e}")
