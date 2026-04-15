"""US case law fetcher: Fetch court opinions from CourtListener (Free Law Project).

Data sources:
 - Search API v4: https://www.courtlistener.com/api/rest/v4/search/
 - Opinions API v4: https://www.courtlistener.com/api/rest/v4/opinions/
 - Bulk data: https://www.courtlistener.com/help/api/bulk-data/
 - Free Law Project: https://free.law/

CourtListener requires a free API token (sign up at courtlistener.com).
New accounts must use API v4 (v3 is restricted to legacy users).
All US court opinions are public domain.

Usage:
  # Fetch SCOTUS opinions:
  fetcher = CourtListenerFetcher(api_token="your-token")
  for doc in fetcher.fetch_court("scotus", limit=100):
      print(doc.case_name, doc.citation)

  # Fetch from bulk CSV data:
  for doc in fetcher.fetch_from_bulk(Path("courtlistener-bulk/")):
      print(doc.case_name)
"""

from __future__ import annotations

import csv
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

import requests

logger = logging.getLogger(__name__)

# CourtListener
CL_BASE = "https://www.courtlistener.com"
CL_SEARCH = f"{CL_BASE}/api/rest/v4/search/"
CL_OPINIONS = f"{CL_BASE}/api/rest/v4/opinions/"

# Court hierarchy mapping for directory structure
COURT_LEVELS = {
    # US Supreme Court
    "scotus": ("supreme-court", "Supreme Court of the United States"),
    # Federal Circuit Courts
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


class CaseDocument:
    """A court decision/opinion as a structured document."""

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
        case_type: str = "",
        judges: str = "",
    ):
        self.case_name = case_name
        self.citation = citation
        self.court_id = court_id
        self.court_name = court_name
        self.decision_date = decision_date
        self.docket_number = docket_number
        self.body_markdown = body_markdown
        self.source_url = source_url
        self.case_type = case_type
        self.judges = judges

    @property
    def slug(self) -> str:
        """Generate a filesystem-safe slug from the citation or case name."""
        text = self.citation or self.case_name
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_]+", "-", slug).strip("-")
        return slug[:120]

    @property
    def output_dir(self) -> str:
        """Directory path based on court hierarchy."""
        court_dir, _ = COURT_LEVELS.get(
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
            "country": "us",
            "source": self.source_url,
        }
        if self.case_type:
            fm["case_type"] = self.case_type
        if self.judges:
            fm["judges"] = self.judges
        return fm

    def to_markdown(self) -> str:
        """Generate full Markdown file content."""
        fm = self.to_frontmatter()
        lines = ["---"]
        for k, v in fm.items():
            if isinstance(v, str) and (":" in v or '"' in v or "\n" in v):
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


def _html_to_markdown(html: str) -> str:
    """Simple HTML to Markdown conversion for opinion text."""
    if not html:
        return ""

    text = html
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL)
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.DOTALL)
    text = re.sub(r"<(b|strong)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL)
    text = re.sub(r"<(i|em)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.DOTALL)
    text = re.sub(r"</?[uo]l[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_date(date_str: str) -> Optional[date]:
    """Parse a date string from CourtListener."""
    if not date_str:
        return None
    # Handle timezone-aware strings like "2026-03-25T00:00:00-07:00"
    clean = date_str.split("T")[0] if "T" in date_str else date_str
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(clean.strip(), fmt).date()
        except ValueError:
            continue
    return None


class CourtListenerFetcher:
    """Fetch US court opinions from CourtListener search API."""

    def __init__(self, api_token: str, throttle: float = 1.0):
        """Initialize fetcher.

        Args:
            api_token: CourtListener API token (free at courtlistener.com).
            throttle: Seconds between API requests.
        """
        self.api_token = api_token
        self.throttle = throttle
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {api_token}",
        })

    def fetch_court(
        self,
        court_id: str,
        limit: int = 0,
        full_text: bool = True,
    ) -> Iterator[CaseDocument]:
        """Fetch opinions from a specific court via the v4 search API.

        Args:
            court_id: CourtListener court slug (e.g. "scotus", "ca9").
            limit: Max number of opinions to fetch (0 = all).
            full_text: If True, fetch full opinion text per case (slower).

        Yields:
            CaseDocument for each opinion.
        """
        court_dir, court_name = COURT_LEVELS.get(
            court_id, (court_id, court_id)
        )

        count = 0
        page_size = 20

        # V4 uses cursor-based pagination — first request uses normal params,
        # subsequent requests follow the `next` URL directly.
        url: Optional[str] = (
            f"{CL_SEARCH}?q=*&court={court_id}&type=o"
            f"&order_by=dateFiled+desc&page_size={page_size}"
        )

        while url:
            logger.info(f"Fetching {court_id} ({count} so far): {url[:120]}...")

            try:
                import time
                time.sleep(self.throttle)
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"API request failed: {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            for result in results:
                try:
                    doc = self._search_result_to_case(
                        result, court_id, court_name, full_text=full_text,
                    )
                    if doc:
                        yield doc
                        count += 1
                        if limit and count >= limit:
                            logger.info(f"Reached limit of {limit} for {court_id}")
                            return
                except Exception as e:
                    logger.error(f"Failed to parse result: {e}")

            # V4 cursor pagination — follow `next` URL or stop
            url = data.get("next")

        logger.info(f"Fetched {count} opinions from {court_id}")

    def _search_result_to_case(
        self,
        result: dict,
        court_id: str,
        court_name: str,
        full_text: bool = True,
    ) -> Optional[CaseDocument]:
        """Convert a v4 search API result to a CaseDocument."""
        case_name = result.get("caseName", "") or result.get("case_name", "")
        if not case_name:
            return None

        # Citation — can be a list or string
        citation_raw = result.get("citation", [])
        if isinstance(citation_raw, list):
            citation = citation_raw[0] if citation_raw else ""
        else:
            citation = str(citation_raw)

        decision_date = _parse_date(result.get("dateFiled", ""))
        docket = result.get("docketNumber", "")

        # V4 search results embed an `opinions` array with snippets
        snippet = result.get("snippet", "")
        opinions_list = result.get("opinions", [])
        if not snippet and opinions_list:
            snippet = opinions_list[0].get("snippet", "")
        body = _html_to_markdown(snippet) if snippet else ""

        # Get cluster_id for full text fetch
        cluster_id = result.get("cluster_id", "")
        abs_url = result.get("absolute_url", "")

        if full_text and cluster_id:
            full_body = self._fetch_full_opinion(cluster_id)
            if full_body:
                body = full_body

        source = f"{CL_BASE}{abs_url}" if abs_url else ""
        judges = result.get("judge", "")

        return CaseDocument(
            case_name=case_name,
            citation=citation,
            court_id=court_id,
            court_name=court_name,
            decision_date=decision_date,
            docket_number=docket,
            body_markdown=body,
            source_url=source,
            judges=judges,
        )

    def _fetch_full_opinion(self, cluster_id: str) -> Optional[str]:
        """Fetch the full opinion text for a given cluster ID via v4 API."""
        try:
            import time
            time.sleep(self.throttle)

            url = f"{CL_OPINIONS}?cluster={cluster_id}"
            resp = self.session.get(url, timeout=30)

            if resp.status_code != 200:
                logger.debug(f"Opinions endpoint returned {resp.status_code} for cluster {cluster_id}")
                return None

            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

            opinion = results[0]
            # Prefer HTML with citations, fall back to plain text
            html = (
                opinion.get("html_with_citations", "")
                or opinion.get("html_columbia", "")
                or opinion.get("html_lawbox", "")
                or opinion.get("html", "")
            )
            if html:
                return _html_to_markdown(html)

            plain = opinion.get("plain_text", "")
            return plain or None

        except Exception as e:
            logger.debug(f"Could not fetch full opinion {cluster_id}: {e}")
            return None

    def fetch_all(
        self,
        courts: Optional[list[str]] = None,
        limit_per_court: int = 0,
    ) -> Iterator[CaseDocument]:
        """Fetch opinions from multiple courts.

        Args:
            courts: List of court IDs. Defaults to SCOTUS + all circuits.
            limit_per_court: Max opinions per court (0 = all).

        Yields:
            CaseDocument for each opinion.
        """
        target_courts = courts or list(COURT_LEVELS.keys())
        logger.info(f"Fetching from {len(target_courts)} courts")

        for court_id in target_courts:
            try:
                yield from self.fetch_court(court_id, limit=limit_per_court)
            except Exception as e:
                logger.error(f"Failed to fetch {court_id}: {e}")

    def fetch_from_bulk(self, bulk_dir: Path) -> Iterator[CaseDocument]:
        """Parse opinions from CourtListener bulk CSV data.

        Download from: https://www.courtlistener.com/help/api/bulk-data/

        Args:
            bulk_dir: Path to directory with bulk CSV files.

        Yields:
            CaseDocument for each opinion.
        """
        if not bulk_dir.exists():
            raise FileNotFoundError(f"Bulk data directory not found: {bulk_dir}")

        # Load court mapping
        courts = {}
        courts_file = bulk_dir / "courts.csv"
        if courts_file.exists():
            with open(courts_file, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    courts[row.get("id", "")] = row.get("full_name", "")

        # Load clusters (case metadata)
        clusters = {}
        for f in sorted(bulk_dir.glob("clusters*.csv")):
            logger.info(f"Loading clusters from {f}")
            with open(f, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    clusters[row.get("id", "")] = row

        # Process opinions
        for opinion_file in sorted(bulk_dir.glob("opinions*.csv")):
            logger.info(f"Processing {opinion_file}")
            with open(opinion_file, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        cluster = clusters.get(row.get("cluster_id", ""), {})
                        case_name = cluster.get("case_name", "")
                        if not case_name:
                            continue

                        court_id = cluster.get("court_id", "")
                        court_name = courts.get(court_id, court_id)

                        html = row.get("html_with_citations", "") or row.get("html", "")
                        plain = row.get("plain_text", "")
                        body = _html_to_markdown(html) if html else plain

                        yield CaseDocument(
                            case_name=case_name,
                            citation=cluster.get("citation", ""),
                            court_id=court_id,
                            court_name=court_name,
                            decision_date=_parse_date(cluster.get("date_filed", "")),
                            docket_number=cluster.get("docket_number", ""),
                            body_markdown=body,
                            source_url=f"{CL_BASE}/opinion/{row.get('id', '')}/",
                            judges=cluster.get("judges", ""),
                        )
                    except Exception as e:
                        logger.error(f"Failed to parse opinion row: {e}")
