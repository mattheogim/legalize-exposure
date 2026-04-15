"""Federal Register → Exposure Mapper connector.

Bridges the FR API response format to the ExposureMapper input format.

Two usage modes:
  1. From RegDocument objects (if federal_register.py is importable)
  2. From raw FR API JSON dicts (standalone, no external dependencies)

The key transformations:
  - Agency display name → agency slug
  - CFR reference strings → list of citation strings
  - FR API JSON → ExposureMapper.map_federal_register_doc() kwargs
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .mapper import ExposureMapper, MappingResult
from .macro_calendar import MacroEventCalendar
from .summarizer import RegulationSummarizer, RegulationSummary


# ── Agency Name → Slug Mapping ─────────────────────────────────────────
#
# FR API returns display names in agency_names[], but our lookups use slugs.
# This is a lossy conversion — we normalize and match.

_AGENCY_NAME_TO_SLUG: dict[str, str] = {
    "Environmental Protection Agency": "environmental-protection-agency",
    "Department of Energy": "department-of-energy",
    "Food and Drug Administration": "food-and-drug-administration",
    "Department of Health and Human Services": "department-of-health-and-human-services",
    "Securities and Exchange Commission": "securities-and-exchange-commission",
    "Consumer Financial Protection Bureau": "consumer-financial-protection-bureau",
    "Department of the Treasury": "department-of-the-treasury",
    "Internal Revenue Service": "internal-revenue-service",
    "Federal Communications Commission": "federal-communications-commission",
    "Federal Trade Commission": "federal-trade-commission",
    "Department of Labor": "department-of-labor",
    "Department of Transportation": "department-of-transportation",
    "Department of Homeland Security": "department-of-homeland-security",
    "Department of Education": "department-of-education",
    "Department of Justice": "department-of-justice",
    "Department of Agriculture": "department-of-agriculture",
    "Department of Defense": "department-of-defense",
    "Department of the Interior": "department-of-the-interior",
    "Department of Commerce": "department-of-commerce",
    "Department of Housing and Urban Development": "department-of-housing-and-urban-development",
    "Department of Veterans Affairs": "department-of-veterans-affairs",
    "Federal Aviation Administration": "federal-aviation-administration",
    "Occupational Safety and Health Administration": "occupational-safety-and-health-administration",
    "Centers for Medicare & Medicaid Services": "centers-for-medicare-and-medicaid-services",
    "Centers for Medicare and Medicaid Services": "centers-for-medicare-and-medicaid-services",
    "Federal Deposit Insurance Corporation": "federal-deposit-insurance-corporation",
    "Commodity Futures Trading Commission": "commodity-futures-trading-commission",
    "Nuclear Regulatory Commission": "nuclear-regulatory-commission",
    "National Highway Traffic Safety Administration": "national-highway-traffic-safety-administration",
    "Pipeline and Hazardous Materials Safety Administration": "pipeline-and-hazardous-materials-safety-administration",
    "Bureau of Land Management": "bureau-of-land-management",
    "Fish and Wildlife Service": "fish-and-wildlife-service",
}


def agency_name_to_slug(name: str) -> str:
    """Convert FR API agency display name to slug.

    First tries exact match, then falls back to slugification.
    """
    # Exact lookup
    if name in _AGENCY_NAME_TO_SLUG:
        return _AGENCY_NAME_TO_SLUG[name]

    # Fallback: slugify (lowercase, replace spaces/special chars with hyphens)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


# ── CFR Reference Parsing ──────────────────────────────────────────────

def parse_cfr_references(cfr_refs: list[str]) -> list[str]:
    """Normalize CFR reference strings from FR API format.

    FR API returns cfr_references as objects with {title, parts}.
    Our fetcher formats them as "40 CFR 60, 63".
    This function normalizes to ["40 CFR 60", "40 CFR 63"] format
    that CFRLookup.match_from_cite() can parse.
    """
    normalized = []
    for ref in cfr_refs:
        # Already in "N CFR X" format from our fetcher
        m = re.match(r"(\d+)\s*CFR\s*(.*)", ref.strip())
        if m:
            title_num = m.group(1)
            parts_str = m.group(2)
            # Split comma-separated parts
            parts = [p.strip() for p in parts_str.split(",") if p.strip()]
            if parts:
                for part in parts:
                    normalized.append(f"{title_num} CFR {part}")
            else:
                normalized.append(f"{title_num} CFR")
        else:
            normalized.append(ref)  # pass through as-is
    return normalized


def parse_cfr_from_api_json(cfr_references: list[dict]) -> list[str]:
    """Parse CFR references directly from FR API JSON format.

    API returns: [{"title": 40, "parts": [60, 63]}, ...]
    Returns: ["40 CFR 60", "40 CFR 63"]
    """
    normalized = []
    for ref in cfr_references or []:
        title = ref.get("title", "")
        parts = ref.get("parts", [])
        if title and parts:
            for part in parts:
                normalized.append(f"{title} CFR {part}")
        elif title:
            normalized.append(f"{title} CFR")
    return normalized


# ── Pipeline Result ────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    """Full result from FR document → exposure mapping pipeline."""
    document_number: str
    title: str
    doc_type: str
    agency_slug: str
    agency_display: str
    publication_date: Optional[date]
    mapping: MappingResult
    contamination_score: float
    contamination_events: list[str]   # nearby macro event titles
    html_url: str = ""
    significant: bool = False
    summary: Optional[RegulationSummary] = None

    @property
    def etf_tickers(self) -> list[str]:
        return sorted(e.ticker for e in self.mapping.etfs)

    @property
    def industry_count(self) -> int:
        return len(self.mapping.industries)

    @property
    def etf_count(self) -> int:
        return len(self.mapping.etfs)

    def summary_line(self) -> str:
        """One-line summary for reports."""
        sig = " [SIGNIFICANT]" if self.significant else ""
        contam = f" [contamination:{self.contamination_score:.2f}]"
        return (
            f"{self.document_number} | {self.agency_slug[:30]:30s} | "
            f"{self.industry_count} industries → {self.etf_count} ETFs "
            f"({', '.join(self.etf_tickers[:6])}){sig}{contam}"
        )


# ── Connector ──────────────────────────────────────────────────────────

class FRExposureConnector:
    """Connects Federal Register documents to the exposure mapping engine.

    Usage:
        connector = FRExposureConnector()

        # From a raw FR API JSON result dict:
        result = connector.map_from_api_json(api_result_dict)

        # From RegDocument object:
        result = connector.map_from_regdoc(reg_document)

        # Batch processing:
        results = connector.map_batch(list_of_api_dicts)
    """

    def __init__(
        self,
        calendar: Optional[MacroEventCalendar] = None,
        contamination_window: int = 5,
    ):
        self._mapper = ExposureMapper()
        self._calendar = calendar or MacroEventCalendar()
        self._window = contamination_window

    def map_from_api_json(self, api_result: dict) -> Optional[PipelineResult]:
        """Map a single FR API JSON result dict to exposure.

        Args:
            api_result: One item from FR API "results" array. Expected keys:
                document_number, type, title, abstract, agency_names,
                publication_date, cfr_references, significant, html_url, etc.
        """
        # Extract fields
        doc_number = api_result.get("document_number", "")
        doc_type = api_result.get("type", "")
        title = api_result.get("title", "")
        abstract = api_result.get("abstract", "") or ""
        agency_names = api_result.get("agency_names", []) or []
        html_url = api_result.get("html_url", "")
        significant = bool(api_result.get("significant"))

        # Parse publication date
        pub_date = None
        pub_str = api_result.get("publication_date", "")
        if pub_str:
            try:
                pub_date = datetime.strptime(pub_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Resolve agency slug (use first agency)
        agency_display = agency_names[0] if agency_names else ""
        agency_slug = agency_name_to_slug(agency_display) if agency_display else ""

        # Parse CFR references (handle both API format and our fetcher format)
        raw_cfr = api_result.get("cfr_references", []) or []
        if raw_cfr and isinstance(raw_cfr[0], dict):
            cfr_citations = parse_cfr_from_api_json(raw_cfr)
        elif raw_cfr and isinstance(raw_cfr[0], str):
            cfr_citations = parse_cfr_references(raw_cfr)
        else:
            cfr_citations = []

        # Run the mapper
        mapping = self._mapper.map_federal_register_doc(
            title=title,
            agency_slug=agency_slug,
            cfr_citations=cfr_citations,
            doc_type=doc_type,
            fr_doc_number=doc_number,
            publication_date=pub_date,
            significant=significant,
            abstract=abstract,
        )

        # Calculate contamination
        contamination = 0.0
        contam_events = []
        if pub_date:
            contamination = self._calendar.contamination_score(
                pub_date, self._window
            )
            from datetime import timedelta
            nearby = self._calendar.events_in_window(
                pub_date - timedelta(days=self._window),
                pub_date + timedelta(days=self._window),
            )
            contam_events = [e.title for e in nearby]

        # Generate summary
        summarizer = RegulationSummarizer()
        obligation_type = (
            mapping.regulation.obligation_type
            if hasattr(mapping, 'regulation') and hasattr(mapping.regulation, 'obligation_type')
            else None
        )
        # Get obligation type from graph if available
        from .schema import Obligation
        obl_type = None
        for node in mapping.graph.nodes.values():
            if isinstance(node, Obligation):
                obl_type = node.obligation_type
                break

        summary = summarizer.summarize(
            title=title,
            agency_slug=agency_slug,
            abstract=abstract,
            doc_type=doc_type,
            obligation_type=obl_type,
            significant=significant,
            etf_tickers=sorted(e.ticker for e in mapping.etfs),
            industry_count=len(mapping.industries),
        )

        return PipelineResult(
            document_number=doc_number,
            title=title,
            doc_type=doc_type,
            agency_slug=agency_slug,
            agency_display=agency_display,
            publication_date=pub_date,
            mapping=mapping,
            contamination_score=contamination,
            contamination_events=contam_events,
            html_url=html_url,
            significant=significant,
            summary=summary,
        )

    def map_from_regdoc(self, doc) -> Optional[PipelineResult]:
        """Map from a RegDocument object (from federal_register.py).

        Accepts any object with: document_number, doc_type, title, abstract,
        agency_names, publication_date, cfr_references, significant, html_url.
        """
        # Convert RegDocument to API-like dict
        api_dict = {
            "document_number": getattr(doc, "document_number", ""),
            "type": getattr(doc, "doc_type", ""),
            "title": getattr(doc, "title", ""),
            "abstract": getattr(doc, "abstract", ""),
            "agency_names": getattr(doc, "agency_names", []),
            "publication_date": (
                doc.publication_date.isoformat()
                if getattr(doc, "publication_date", None)
                else ""
            ),
            "cfr_references": getattr(doc, "cfr_references", []),
            "significant": getattr(doc, "significant", False),
            "html_url": getattr(doc, "html_url", ""),
        }
        return self.map_from_api_json(api_dict)

    def map_batch(
        self,
        documents: list[dict],
        min_etfs: int = 0,
    ) -> list[PipelineResult]:
        """Map a batch of FR API results.

        Args:
            documents: List of FR API result dicts
            min_etfs: Minimum ETF matches to include in results (0 = all)
        """
        results = []
        for doc in documents:
            result = self.map_from_api_json(doc)
            if result and (min_etfs == 0 or result.etf_count >= min_etfs):
                results.append(result)
        return results

    def generate_report(self, results: list[PipelineResult]) -> str:
        """Generate a Markdown report from pipeline results."""
        lines = [
            "# Regulation → Exposure Mapping Report",
            f"*Generated: {date.today().isoformat()}*",
            f"*Documents processed: {len(results)}*",
            "",
        ]

        # Summary stats
        with_etfs = [r for r in results if r.etf_count > 0]
        significant = [r for r in results if r.significant]
        high_contam = [r for r in results if r.contamination_score >= 0.5]

        lines.append(f"**Mapped to ETFs:** {len(with_etfs)}/{len(results)}")
        lines.append(f"**Significant:** {len(significant)}")
        lines.append(f"**High contamination (≥0.5):** {len(high_contam)}")
        lines.append("")

        # Results table
        lines.append("| Doc # | Agency | Industries | ETFs | Contamination | Sig |")
        lines.append("|-------|--------|-----------|------|---------------|-----|")

        for r in sorted(results, key=lambda x: x.etf_count, reverse=True):
            sig = "✓" if r.significant else ""
            contam = f"{r.contamination_score:.2f}"
            etfs = ", ".join(r.etf_tickers[:5])
            if r.etf_count > 5:
                etfs += f" +{r.etf_count - 5}"
            lines.append(
                f"| {r.document_number} | {r.agency_slug[:25]} | "
                f"{r.industry_count} | {etfs} | {contam} | {sig} |"
            )

        lines.append("")

        # Detail section for significant or high-ETF results
        notable = [r for r in results if r.significant or r.etf_count >= 5]
        if notable:
            lines.append("## Notable Mappings")
            lines.append("")
            for r in notable:
                lines.append(f"### {r.document_number}: {r.title[:80]}")
                lines.append(f"- **Agency:** {r.agency_display}")
                lines.append(f"- **Type:** {r.doc_type}")
                if r.publication_date:
                    lines.append(f"- **Published:** {r.publication_date.isoformat()}")
                lines.append(f"- **Industries ({r.industry_count}):** "
                           + ", ".join(i.naics_code for i in r.mapping.industries))
                lines.append(f"- **ETFs ({r.etf_count}):** "
                           + ", ".join(r.etf_tickers))
                lines.append(f"- **Contamination:** {r.contamination_score:.2f}")
                if r.contamination_events:
                    lines.append(f"  - Nearby events: {', '.join(r.contamination_events[:3])}")
                if r.html_url:
                    lines.append(f"- **Source:** {r.html_url}")
                lines.append("")

        return "\n".join(lines)
