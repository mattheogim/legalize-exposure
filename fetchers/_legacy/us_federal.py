"""US Federal fetcher: Parse US Code (USC) from USLM XML.

Data sources:
 - Bulk XML download: https://uscode.house.gov/download/download.shtml
 - USLM schema: https://github.com/usgpo/uslm
 - GovInfo API: https://www.govinfo.gov/features/beta-uslm-xml

Usage:
  # From a local directory of extracted USLM XML files:
  fetcher = USFederalFetcher()
  for doc in fetcher.fetch_from_local_xml(Path("usc-xml/")):
      print(doc.metadata.title, doc.output_path)

  # From the web (downloads per-title zips):
  for doc in fetcher.fetch_all():
      print(doc.metadata.title)
"""

from __future__ import annotations

import logging
import re
import zipfile
import io
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

from lxml import etree

from ..models import Jurisdiction, LawDocument, LawMetadata, LawStatus, LawType
from ..utils import ThrottledClient

logger = logging.getLogger(__name__)

# Constants
USCODE_BASE = "https://uscode.house.gov"
DOWNLOAD_PAGE = f"{USCODE_BASE}/download/download.shtml"

# Release-point URL pattern — titles 1–54, zero-padded to 2 digits
# Example: xml_usc01@119-73.zip for Title 1 at PL 119-73
# The release point (e.g. "119-73") changes with each public law update.
TITLE_ZIP_TEMPLATE = f"{USCODE_BASE}/download/releasepoints/us/pl/{{release}}/xml_usc{{title_num}}@{{release}}.zip"

# All 54 current USC title numbers (some are reserved/empty but included for completeness)
USC_TITLES = list(range(1, 55))

# USLM namespace
USLM_NS = "http://schemas.gpo.gov/xml/uslm"
DC_NS = "http://purl.org/dc/elements/1.1/"
NS = {
    "uslm": USLM_NS,
    "dc": DC_NS,
}


# ---------------------------------------------------------------------------
# XML → Markdown conversion
# ---------------------------------------------------------------------------

def _extract_text(el: Optional[etree._Element]) -> str:
    """Recursively extract all text content from an element."""
    if el is None:
        return ""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if not isinstance(child.tag, str):
            if child.tail:
                parts.append(child.tail)
            continue
        local = etree.QName(child).localname
        child_text = _extract_text(child)
        if local in ("ref", "externalRef"):
            parts.append(child_text)
        elif local in ("i", "emphasis"):
            parts.append(f"*{child_text}*")
        elif local in ("b", "bold"):
            parts.append(f"**{child_text}**")
        else:
            parts.append(child_text)
        if child.tail:
            parts.append(child.tail)
    return "".join(parts).strip()


def _num_text(el: etree._Element) -> str:
    """Get the <num> value from an element, or empty string."""
    num = el.find(f"{{{USLM_NS}}}num")
    if num is None:
        # Try without namespace (some files use bare tags)
        num = el.find("num")
    if num is not None:
        val = num.get("value", "") or _extract_text(num)
        return val.strip()
    return ""


def _heading_text(el: etree._Element) -> str:
    """Get the <heading> text from an element."""
    heading = el.find(f"{{{USLM_NS}}}heading")
    if heading is None:
        heading = el.find("heading")
    if heading is not None:
        return _extract_text(heading)
    return ""


def _level_to_md(el: etree._Element, depth: int = 0) -> str:
    """Convert a USLM hierarchical <level>, <section>, <subsection>, etc. to Markdown.

    USLM uses a generic <level> element (or named variants like <section>,
    <subsection>, <paragraph>, <subparagraph>, <chapter>, <subchapter>)
    at arbitrary depth.  Each may contain:
      - <num>       — section/paragraph number
      - <heading>   — optional heading
      - <chapeau>   — introductory text before sub-levels
      - <text>      — content text
      - <content>   — wrapper around mixed text / sub-levels
      - child levels
    """
    if not isinstance(el.tag, str):
        return ""

    local = etree.QName(el).localname
    lines: list[str] = []

    num = _num_text(el)
    heading = _heading_text(el)

    # Determine Markdown heading level from depth
    # depth 0 = title/part → #, depth 1 = chapter → ##, depth 2 = subchapter → ###
    # depth 3+ = section-level → ##### (flat, matching Canadian style)
    if depth <= 3:
        md_level = "#" * min(depth + 1, 4)
    else:
        md_level = "#####"

    # Build heading line
    heading_parts = []
    if num:
        heading_parts.append(num)
    if heading:
        heading_parts.append(heading)

    # Named structural levels get headings
    structural = {
        "title", "subtitle", "part", "subpart", "chapter", "subchapter",
        "division", "subdivision", "article", "subarticle",
    }
    section_like = {
        "section", "subsection", "paragraph", "subparagraph",
        "clause", "subclause", "item", "subitem",
    }

    if local in structural and heading_parts:
        lines.append(f"{md_level} {' — '.join(heading_parts)}")
        lines.append("")
    elif local in section_like and heading_parts:
        if depth <= 3:
            lines.append(f"##### {' '.join(heading_parts)}")
            lines.append("")
        else:
            # Inline label for deep nesting
            label = f"**{num}**" if num else ""
            if heading:
                label += f" {heading}" if label else heading
            if label:
                lines.append(label)
                lines.append("")
    elif local == "level" and heading_parts:
        lines.append(f"{md_level} {' '.join(heading_parts)}")
        lines.append("")

    # Chapeau (introductory text before sub-elements)
    for chapeau in el.findall(f"{{{USLM_NS}}}chapeau"):
        txt = _extract_text(chapeau)
        if txt:
            lines.append(txt)
            lines.append("")
    # Also try bare tag
    for chapeau in el.findall("chapeau"):
        txt = _extract_text(chapeau)
        if txt:
            lines.append(txt)
            lines.append("")

    # Direct <text> or <p> children
    for tag in ("text", "p"):
        for text_el in el.findall(f"{{{USLM_NS}}}{tag}"):
            txt = _extract_text(text_el)
            if txt:
                if local in section_like and num and depth > 3:
                    lines.append(f"**{num}** {txt}")
                else:
                    lines.append(txt)
                lines.append("")
        for text_el in el.findall(tag):
            txt = _extract_text(text_el)
            if txt:
                lines.append(txt)
                lines.append("")

    # <content> wrapper — recurse into its children
    for content in el.findall(f"{{{USLM_NS}}}content"):
        lines.append(_level_to_md(content, depth))
    for content in el.findall("content"):
        lines.append(_level_to_md(content, depth))

    # Child levels (recursive)
    all_level_tags = structural | section_like | {"level"}
    for child in el:
        if not isinstance(child.tag, str):
            continue
        child_local = etree.QName(child).localname
        if child_local in all_level_tags:
            child_md = _level_to_md(child, depth + 1)
            if child_md.strip():
                lines.append(child_md)

    # Continuation (text after sub-elements)
    for cont in el.findall(f"{{{USLM_NS}}}continuation"):
        txt = _extract_text(cont)
        if txt:
            lines.append(txt)
            lines.append("")

    return "\n".join(lines)


def _notes_to_md(el: etree._Element) -> str:
    """Convert statutory notes sections to markdown."""
    lines = []
    for note in el.findall(f".//{{{USLM_NS}}}note"):
        heading = _heading_text(note)
        if heading:
            lines.append(f"#### {heading}")
            lines.append("")
        for text_el in note.findall(f".//{{{USLM_NS}}}text"):
            txt = _extract_text(text_el)
            if txt:
                lines.append(txt)
                lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_uslm_xml(xml_bytes: bytes) -> LawDocument:
    """Parse a USLM XML file (single USC title) into a LawDocument.

    Expects the root element to be <lawDoc> or <usc:lawDoc>.
    """
    root = etree.fromstring(xml_bytes)
    root_local = etree.QName(root).localname if isinstance(root.tag, str) else root.tag

    # --- Metadata ---
    title_text = ""
    identifier = ""
    title_num = ""

    # Try <meta> block
    meta = root.find(f"{{{USLM_NS}}}meta") or root.find("meta")
    if meta is not None:
        dc_title = meta.find(f"{{{DC_NS}}}title")
        if dc_title is not None and dc_title.text:
            title_text = dc_title.text.strip()

    # Try <preface> for title info
    preface = root.find(f"{{{USLM_NS}}}preface") or root.find("preface")
    if preface is not None:
        num_el = preface.find(f".//{{{USLM_NS}}}num")
        if num_el is None:
            num_el = preface.find(".//num")
        if num_el is not None:
            val = num_el.get("value", "") or _extract_text(num_el)
            title_num = val.strip()

        heading_el = preface.find(f".//{{{USLM_NS}}}heading")
        if heading_el is None:
            heading_el = preface.find(".//heading")
        if heading_el is not None:
            pref_heading = _extract_text(heading_el)
            if pref_heading and not title_text:
                title_text = pref_heading

    # Build identifier like "usc-title-1"
    if title_num:
        identifier = f"usc-title-{title_num}"
    elif title_text:
        # Fallback: extract number from title
        m = re.search(r"Title\s+(\d+)", title_text, re.IGNORECASE)
        if m:
            title_num = m.group(1)
            identifier = f"usc-title-{title_num}"
        else:
            from slugify import slugify
            identifier = slugify(title_text) or "unknown"
    else:
        identifier = "unknown"

    if not title_text:
        title_text = f"United States Code — Title {title_num}" if title_num else identifier

    # Source URL
    source_url = f"https://uscode.house.gov/view.xhtml?path=/prelim@title{title_num}&edition=prelim" if title_num else ""

    metadata = LawMetadata(
        title=title_text,
        identifier=identifier,
        jurisdiction=Jurisdiction.US_FEDERAL,
        law_type=LawType.ACT,  # USC titles are codified statutes
        status=LawStatus.IN_FORCE,
        source_url=source_url,
    )

    # --- Body ---
    main = root.find(f"{{{USLM_NS}}}main") or root.find("main")
    body_md = ""
    if main is not None:
        body_md = _level_to_md(main, depth=0)

    # Notes / appendix
    notes = root.find(f"{{{USLM_NS}}}notes") or root.find("notes")
    if notes is not None:
        notes_md = _notes_to_md(notes)
        if notes_md.strip():
            body_md += f"\n\n---\n\n## Statutory Notes\n\n{notes_md}"

    return LawDocument(
        metadata=metadata,
        body_markdown=body_md,
        raw_xml=xml_bytes.decode("utf-8", errors="replace"),
    )


# ---------------------------------------------------------------------------
# Fetcher class
# ---------------------------------------------------------------------------

class USFederalFetcher:
    """Fetch and parse US federal legislation (US Code) from USLM XML."""

    def __init__(self, throttle: float = 1.0):
        """Initialize with throttle delay (seconds between requests).

        Default is 1.0s — be respectful to government servers.
        """
        self.client = ThrottledClient(throttle=throttle)
        self._release: Optional[str] = None

    def discover_release_point(self) -> str:
        """Discover the latest release point from the download page.

        Returns a string like '119-73' (Public Law number).
        """
        if self._release:
            return self._release

        logger.info("Discovering latest USC release point...")
        html = self.client.get_text(DOWNLOAD_PAGE)

        # Look for release point pattern in download links
        # e.g. xml_usc01@119-73.zip → release = "119-73"
        matches = re.findall(r"xml_usc\d+@([\d]+-[\d]+)\.zip", html)
        if matches:
            # Most recent release is the most common one
            from collections import Counter
            self._release = Counter(matches).most_common(1)[0][0]
            logger.info(f"Latest release point: PL {self._release}")
            return self._release

        raise RuntimeError(
            "Could not determine USC release point from download page. "
            "Check https://uscode.house.gov/download/download.shtml manually."
        )

    def _title_zip_url(self, title_num: int, release: str) -> str:
        """Build the download URL for a single title's XML zip."""
        return TITLE_ZIP_TEMPLATE.format(
            release=release,
            title_num=f"{title_num:02d}",
        )

    def fetch_title(self, title_num: int) -> Optional[LawDocument]:
        """Fetch and parse a single USC title by number (1–54)."""
        release = self.discover_release_point()
        url = self._title_zip_url(title_num, release)

        try:
            logger.info(f"Downloading USC Title {title_num} from {url}")
            zip_bytes = self.client.get_bytes(url)

            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                # Find the main XML file inside the zip
                xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
                if not xml_names:
                    logger.warning(f"No XML found in zip for Title {title_num}")
                    return None

                # Usually one main file per zip
                xml_bytes = zf.read(xml_names[0])
                doc = parse_uslm_xml(xml_bytes)
                logger.info(f"Parsed: {doc.metadata.title}")
                return doc

        except Exception as e:
            logger.error(f"Failed to fetch/parse USC Title {title_num}: {e}")
            return None

    def fetch_all(self, titles: Optional[list[int]] = None) -> Iterator[LawDocument]:
        """Fetch all (or selected) USC titles.

        Args:
            titles: List of title numbers to fetch. Defaults to all 54.

        Yields:
            LawDocument for each successfully parsed title.
        """
        target_titles = titles or USC_TITLES
        release = self.discover_release_point()
        logger.info(f"Fetching {len(target_titles)} USC titles (PL {release})")

        for title_num in target_titles:
            doc = self.fetch_title(title_num)
            if doc:
                yield doc

    def fetch_from_local_xml(self, xml_dir: Path) -> Iterator[LawDocument]:
        """Parse USC titles from a local directory of USLM XML files.

        Supports two layouts:
          1. Flat directory of .xml files (one per title)
          2. Extracted zip structure with nested XML

        This is faster than downloading from the web.

        Args:
            xml_dir: Path to directory containing USLM XML files.

        Yields:
            LawDocument for each successfully parsed file.
        """
        if not xml_dir.exists():
            raise FileNotFoundError(f"XML directory not found: {xml_dir}")

        # Collect all XML files
        xml_files = sorted(xml_dir.glob("**/*.xml"))
        logger.info(f"Found {len(xml_files)} XML files in {xml_dir}")

        for xml_file in xml_files:
            try:
                xml_bytes = xml_file.read_bytes()
                doc = parse_uslm_xml(xml_bytes)
                logger.info(f"Parsed: {doc.metadata.title}")
                yield doc
            except Exception as e:
                logger.error(f"Failed to parse {xml_file}: {e}")
