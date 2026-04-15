"""Federal Register fetcher: Track proposed rules and regulatory actions.

Stage 2 of the US legislative pipeline tracker.
Detects when agencies publish proposed rules, final rules, and notices.

Data source: Federal Register API
  https://www.federalregister.gov/api/v1/documents.json
  No authentication required. Rate limit: reasonable use.

Document types:
  - PRORULE: Proposed Rule (draft regulation, open for comment)
  - RULE: Final Rule (regulation takes effect)
  - NOTICE: Agency notice (guidance, meetings, deadlines)
  - PRESDOC: Presidential Document (executive orders, proclamations)
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

from ..utils import ThrottledClient

logger = logging.getLogger(__name__)

# Constants
FR_API_BASE = "https://www.federalregister.gov/api/v1"

# Document types
DOC_TYPES = {
    "PRORULE": "Proposed Rule",
    "RULE": "Final Rule",
    "NOTICE": "Notice",
    "PRESDOC": "Presidential Document",
}

# Significant agencies to track
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


class RegDocument:
    """Represents a Federal Register document."""

    def __init__(
        self,
        document_number: str,
        doc_type: str,
        title: str,
        abstract: str = "",
        agency_names: list[str] | None = None,
        publication_date: Optional[date] = None,
        effective_date: Optional[date] = None,
        comment_end_date: Optional[date] = None,
        docket_ids: list[str] | None = None,
        cfr_references: list[str] | None = None,
        html_url: str = "",
        pdf_url: str = "",
        significant: bool = False,
        action: str = "",
    ):
        self.document_number = document_number
        self.doc_type = doc_type
        self.title = title
        self.abstract = abstract
        self.agency_names = agency_names or []
        self.publication_date = publication_date
        self.effective_date = effective_date
        self.comment_end_date = comment_end_date
        self.docket_ids = docket_ids or []
        self.cfr_references = cfr_references or []
        self.html_url = html_url
        self.pdf_url = pdf_url
        self.significant = significant
        self.action = action

    @property
    def identifier(self) -> str:
        return self.document_number

    @property
    def type_label(self) -> str:
        return DOC_TYPES.get(self.doc_type, self.doc_type)

    def to_markdown(self) -> str:
        """Convert document to Markdown format."""
        lines = []
        lines.append(f"# {self.title}")
        lines.append("")

        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Document Number | {self.document_number} |")
        lines.append(f"| Type | {self.type_label} |")
        if self.agency_names:
            lines.append(f"| Agency | {', '.join(self.agency_names)} |")
        if self.publication_date:
            lines.append(f"| Published | {self.publication_date.isoformat()} |")
        if self.effective_date:
            lines.append(f"| Effective | {self.effective_date.isoformat()} |")
        if self.comment_end_date:
            lines.append(f"| Comments Due | {self.comment_end_date.isoformat()} |")
        if self.docket_ids:
            lines.append(f"| Docket | {', '.join(self.docket_ids)} |")
        if self.cfr_references:
            lines.append(f"| CFR | {', '.join(self.cfr_references)} |")
        if self.significant:
            lines.append("| Significant | Yes |")
        if self.action:
            lines.append(f"| Action | {self.action} |")
        if self.html_url:
            lines.append(f"| Source | [{self.html_url}]({self.html_url}) |")
        lines.append("")

        if self.abstract:
            lines.append("## Abstract")
            lines.append("")
            lines.append(self.abstract)
            lines.append("")

        return "\n".join(lines)


class FederalRegisterFetcher:
    """Fetch and track regulatory actions from the Federal Register."""

    def __init__(self, throttle: float = 0.3):
        self.client = ThrottledClient(throttle=throttle)

    def _search(self, params: dict) -> dict:
        """Execute a Federal Register API search."""
        url = f"{FR_API_BASE}/documents.json"
        return self.client.get_json(url, params=params)

    def fetch_proposed_rules(
        self,
        from_date: Optional[date] = None,
        agency_slugs: list[str] | None = None,
        per_page: int = 50,
    ) -> list[RegDocument]:
        """Fetch proposed rules (draft regulations open for comment).

        Args:
            from_date: Only fetch rules published on or after this date
            agency_slugs: Filter by agency (e.g., ["environmental-protection-agency"])
            per_page: Results per page (max 1000)
        """
        params = {
            "conditions[type][]": "PRORULE",
            "per_page": min(per_page, 1000),
            "order": "newest",
            "fields[]": [
                "document_number", "type", "title", "abstract",
                "agency_names", "publication_date", "effective_on",
                "comments_close_on", "docket_ids", "cfr_references",
                "html_url", "pdf_url", "significant", "action",
            ],
        }
        if from_date:
            params["conditions[publication_date][gte]"] = from_date.isoformat()
        if agency_slugs:
            params["conditions[agencies][]"] = agency_slugs

        return self._fetch_documents(params)

    def fetch_final_rules(
        self,
        from_date: Optional[date] = None,
        agency_slugs: list[str] | None = None,
        per_page: int = 50,
    ) -> list[RegDocument]:
        """Fetch final rules (regulations taking effect)."""
        params = {
            "conditions[type][]": "RULE",
            "per_page": min(per_page, 1000),
            "order": "newest",
            "fields[]": [
                "document_number", "type", "title", "abstract",
                "agency_names", "publication_date", "effective_on",
                "comments_close_on", "docket_ids", "cfr_references",
                "html_url", "pdf_url", "significant", "action",
            ],
        }
        if from_date:
            params["conditions[publication_date][gte]"] = from_date.isoformat()
        if agency_slugs:
            params["conditions[agencies][]"] = agency_slugs

        return self._fetch_documents(params)

    def fetch_significant_documents(
        self,
        from_date: Optional[date] = None,
        per_page: int = 50,
    ) -> list[RegDocument]:
        """Fetch only significant/major regulatory actions.

        Significant regulations are those with major economic impact
        (typically >$100M annual effect on the economy).
        """
        params = {
            "conditions[significant]": "1",
            "per_page": min(per_page, 1000),
            "order": "newest",
            "fields[]": [
                "document_number", "type", "title", "abstract",
                "agency_names", "publication_date", "effective_on",
                "comments_close_on", "docket_ids", "cfr_references",
                "html_url", "pdf_url", "significant", "action",
            ],
        }
        if from_date:
            params["conditions[publication_date][gte]"] = from_date.isoformat()

        return self._fetch_documents(params)

    def fetch_executive_orders(
        self,
        from_date: Optional[date] = None,
        per_page: int = 50,
    ) -> list[RegDocument]:
        """Fetch presidential documents (executive orders, proclamations)."""
        params = {
            "conditions[type][]": "PRESDOC",
            "conditions[presidential_document_type][]": "executive_order",
            "per_page": min(per_page, 1000),
            "order": "newest",
            "fields[]": [
                "document_number", "type", "title", "abstract",
                "agency_names", "publication_date", "effective_on",
                "html_url", "pdf_url", "significant", "action",
            ],
        }
        if from_date:
            params["conditions[publication_date][gte]"] = from_date.isoformat()

        return self._fetch_documents(params)

    def fetch_all_regulatory_activity(
        self,
        from_date: Optional[date] = None,
        per_page: int = 100,
    ) -> list[RegDocument]:
        """Fetch all types of regulatory activity (proposed + final rules + EOs).

        This is the main entry point for the daily/weekly sync.
        """
        all_docs = []

        for fetch_fn in [
            self.fetch_proposed_rules,
            self.fetch_final_rules,
            self.fetch_executive_orders,
        ]:
            try:
                docs = fetch_fn(from_date=from_date, per_page=per_page)
                all_docs.extend(docs)
            except Exception as e:
                logger.error(f"Failed to fetch {fetch_fn.__name__}: {e}")

        # Deduplicate by document number
        seen = set()
        unique = []
        for doc in all_docs:
            if doc.document_number not in seen:
                seen.add(doc.document_number)
                unique.append(doc)

        logger.info(f"Fetched {len(unique)} total regulatory documents")
        return unique

    def _fetch_documents(self, params: dict) -> list[RegDocument]:
        """Fetch and parse documents from the API."""
        data = self._search(params)
        docs = []

        for result in data.get("results", []):
            doc = self._parse_document(result)
            if doc:
                docs.append(doc)

        count = data.get("count", len(docs))
        logger.info(f"Fetched {len(docs)} of {count} documents")
        return docs

    def _parse_document(self, data: dict) -> Optional[RegDocument]:
        """Parse a document from the API response."""
        try:
            pub_date = None
            if data.get("publication_date"):
                try:
                    pub_date = datetime.strptime(data["publication_date"], "%Y-%m-%d").date()
                except ValueError:
                    pass

            eff_date = None
            if data.get("effective_on"):
                try:
                    eff_date = datetime.strptime(data["effective_on"], "%Y-%m-%d").date()
                except ValueError:
                    pass

            comment_date = None
            if data.get("comments_close_on"):
                try:
                    comment_date = datetime.strptime(data["comments_close_on"], "%Y-%m-%d").date()
                except ValueError:
                    pass

            cfr_refs = []
            for ref in data.get("cfr_references", []) or []:
                title = ref.get("title", "")
                parts = ref.get("parts", [])
                if title and parts:
                    cfr_refs.append(f"{title} CFR {', '.join(str(p) for p in parts)}")

            return RegDocument(
                document_number=data.get("document_number", ""),
                doc_type=data.get("type", ""),
                title=data.get("title", ""),
                abstract=data.get("abstract", "") or "",
                agency_names=data.get("agency_names", []),
                publication_date=pub_date,
                effective_date=eff_date,
                comment_end_date=comment_date,
                docket_ids=data.get("docket_ids", []) or [],
                cfr_references=cfr_refs,
                html_url=data.get("html_url", ""),
                pdf_url=data.get("pdf_url", ""),
                significant=bool(data.get("significant")),
                action=data.get("action", "") or "",
            )
        except Exception as e:
            logger.error(f"Failed to parse document: {e}")
            return None

    def save_documents(self, docs: list[RegDocument], output_dir: Path) -> int:
        """Save documents to Markdown files.

        File naming: {doc_type}-{document_number}.md
        Returns number of files written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for doc in docs:
            safe_number = doc.document_number.replace("/", "-")
            filename = f"{doc.doc_type.lower()}-{safe_number}.md"
            filepath = output_dir / filename
            filepath.write_text(doc.to_markdown(), encoding="utf-8")
            count += 1
        logger.info(f"Saved {count} document files to {output_dir}")
        return count

    def generate_tracker_report(self, docs: list[RegDocument]) -> str:
        """Generate a summary Markdown report of regulatory activity.

        Groups by document type and sorts by publication date.
        """
        lines = []
        lines.append("# Federal Register Tracker Report")
        lines.append(f"\n*Generated: {date.today().isoformat()}*\n")

        # Group by type
        by_type: dict[str, list[RegDocument]] = {}
        for doc in docs:
            by_type.setdefault(doc.doc_type, []).append(doc)

        for dtype in ["PRORULE", "RULE", "PRESDOC", "NOTICE"]:
            type_docs = by_type.get(dtype, [])
            if not type_docs:
                continue
            type_name = DOC_TYPES.get(dtype, dtype)
            lines.append(f"## {type_name}s ({len(type_docs)})")
            lines.append("")
            lines.append("| Doc # | Title | Agency | Published | Comments Due |")
            lines.append("|-------|-------|--------|-----------|-------------|")

            type_docs.sort(
                key=lambda d: d.publication_date or date.min, reverse=True
            )

            for doc in type_docs:
                pub = doc.publication_date.isoformat() if doc.publication_date else "—"
                comment = doc.comment_end_date.isoformat() if doc.comment_end_date else "—"
                agency = doc.agency_names[0][:30] if doc.agency_names else "—"
                title = doc.title[:50] + "..." if len(doc.title) > 50 else doc.title
                sig = " **[S]**" if doc.significant else ""
                lines.append(f"| {doc.document_number} | {title}{sig} | {agency} | {pub} | {comment} |")

            lines.append("")

        return "\n".join(lines)
