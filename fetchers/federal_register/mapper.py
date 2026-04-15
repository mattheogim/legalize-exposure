"""Federal Register data models and API response parsing.

Converts raw API JSON into typed RegDocument objects.
No network calls — pure data transformation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

DOC_TYPES = {
    "PRORULE": "Proposed Rule",
    "RULE": "Final Rule",
    "NOTICE": "Notice",
    "PRESDOC": "Presidential Document",
}


@dataclass(frozen=True)
class RegDocument:
    """A Federal Register document (immutable)."""

    document_number: str
    doc_type: str
    title: str
    abstract: str = ""
    agency_names: tuple[str, ...] = ()
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    comment_end_date: Optional[date] = None
    docket_ids: tuple[str, ...] = ()
    cfr_references: tuple[str, ...] = ()
    html_url: str = ""
    pdf_url: str = ""
    significant: bool = False
    action: str = ""

    @property
    def identifier(self) -> str:
        return self.document_number

    @property
    def type_label(self) -> str:
        return DOC_TYPES.get(self.doc_type, self.doc_type)

    def to_markdown(self) -> str:
        """Render as Markdown."""
        lines = [f"# {self.title}", ""]
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
            lines.extend(["## Abstract", "", self.abstract, ""])
        return "\n".join(lines)


def _parse_date_str(s: str | None) -> date | None:
    """Parse YYYY-MM-DD date string."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_document(data: dict) -> RegDocument | None:
    """Parse a single document from FR API response JSON.

    Returns None if parsing fails.
    """
    try:
        cfr_refs: list[str] = []
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
            agency_names=tuple(data.get("agency_names", []) or []),
            publication_date=_parse_date_str(data.get("publication_date")),
            effective_date=_parse_date_str(data.get("effective_on")),
            comment_end_date=_parse_date_str(data.get("comments_close_on")),
            docket_ids=tuple(data.get("docket_ids", []) or []),
            cfr_references=tuple(cfr_refs),
            html_url=data.get("html_url", ""),
            pdf_url=data.get("pdf_url", ""),
            significant=bool(data.get("significant")),
            action=data.get("action", "") or "",
        )
    except Exception as e:
        logger.error("Failed to parse FR document: %s", e)
        return None


def parse_search_results(api_response: dict) -> list[RegDocument]:
    """Parse the 'results' array from a FR API search response."""
    docs: list[RegDocument] = []
    for result in api_response.get("results", []):
        doc = parse_document(result)
        if doc:
            docs.append(doc)
    return docs
