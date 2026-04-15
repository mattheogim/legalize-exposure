"""Federal fetcher: Parse Canadian federal legislation from Justice Canada XML.

Data sources:
 - GitHub bulk XML: https://github.com/justicecanada/laws-lois-xml
 - Direct XML: https://laws-lois.justice.gc.ca/eng/XML/{ActID}.xml
 - Open Data portal: https://open.canada.ca/data/en/dataset/ff56de85-...
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

from lxml import etree

from ..models import Jurisdiction, LawDocument, LawMetadata, LawStatus, LawType
from ..utils import ThrottledClient

logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://laws-lois.justice.gc.ca"
ACTS_INDEX_URL = f"{BASE_URL}/eng/acts/"
REGS_INDEX_URL = f"{BASE_URL}/eng/regulations/"
XML_URL_TEMPLATE = f"{BASE_URL}/eng/XML/{{act_id}}.xml"
NS = {"lims": "http://justice.gc.ca/lims"}

# XML Parsing helpers
def _text(el: Optional[etree._Element]) -> str:
    """Extract text content from an element, stripping whitespace."""
    if el is None:
        return ""
    return (el.text or "").strip()

def _attr(el: etree._Element, name: str, default: str = "") -> str:
    """Get attribute from element with fallback."""
    return el.get(name, default)

def _parse_date(date_str: str) -> Optional[date]:
    """Parse dates in various formats from Justice Canada XML."""
    if not date_str:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{4})(\d{2})(\d{2})", date_str)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

# XML → Markdown conversion
def _section_to_md(section: etree._Element, depth: int = 0) -> str:
    """Convert a <Section> XML element to Markdown."""
    lines = []
    marginal = section.find(".//MarginalNote")
    sec_num = section.find(".//SectionNumber") or section.find(".//Label")
    heading_parts = []
    if sec_num is not None and sec_num.text:
        heading_parts.append(sec_num.text.strip())
    if marginal is not None and marginal.text:
        heading_parts.append(marginal.text.strip())
    if heading_parts:
        lines.append(f"##### {' '.join(heading_parts)}")
        lines.append("")
    for text_el in section.findall("./Text"):
        txt = _extract_text(text_el)
        if txt:
            lines.append(txt)
            lines.append("")
    for subsec in section.findall("./Subsection"):
        label = subsec.find("Label")
        label_text = _text(label) if label is not None else ""
        for text_el in subsec.findall("./Text"):
            txt = _extract_text(text_el)
            if txt:
                if label_text:
                    lines.append(f"**{label_text}** {txt}")
                else:
                    lines.append(txt)
                lines.append("")
        # Introduction (preamble text within subsection)
        for intro in subsec.findall("./Introduction"):
            for text_el in intro.findall("./Text"):
                txt = _extract_text(text_el)
                if txt:
                    lines.append(txt)
                    lines.append("")

        for para in subsec.findall("./Paragraph"):
            p_label = para.find("Label")
            p_label_text = _text(p_label) if p_label is not None else ""
            for text_el in para.findall("./Text"):
                txt = _extract_text(text_el)
                if txt:
                    if p_label_text:
                        lines.append(f" **{p_label_text}** {txt}")
                    else:
                        lines.append(f" {txt}")
                    lines.append("")
            # Subparagraphs within paragraph
            for subpara in para.findall("./Subparagraph"):
                sp_label = subpara.find("Label")
                sp_label_text = _text(sp_label) if sp_label is not None else ""
                for text_el in subpara.findall("./Text"):
                    txt = _extract_text(text_el)
                    if txt:
                        prefix = f"    **{sp_label_text}** " if sp_label_text else "    "
                        lines.append(f"{prefix}{txt}")
                        lines.append("")
                # Clauses within subparagraph
                for clause in subpara.findall("./Clause"):
                    c_label = clause.find("Label")
                    c_label_text = _text(c_label) if c_label is not None else ""
                    for text_el in clause.findall("./Text"):
                        txt = _extract_text(text_el)
                        if txt:
                            prefix = f"      **{c_label_text}** " if c_label_text else "      "
                            lines.append(f"{prefix}{txt}")
                            lines.append("")
                    # Subclauses within clause
                    for subclause in clause.findall("./Subclause"):
                        sc_label = subclause.find("Label")
                        sc_label_text = _text(sc_label) if sc_label is not None else ""
                        for text_el in subclause.findall("./Text"):
                            txt = _extract_text(text_el)
                            if txt:
                                prefix = f"        **{sc_label_text}** " if sc_label_text else "        "
                                lines.append(f"{prefix}{txt}")
                                lines.append("")
                # ContinuedSubparagraph within subparagraph
                for csp in subpara.findall("./ContinuedSubparagraph"):
                    for text_el in csp.findall("./Text"):
                        txt = _extract_text(text_el)
                        if txt:
                            lines.append(f"    {txt}")
                            lines.append("")

        # ContinuedParagraph (text continuation after paragraph break)
        for cp in subsec.findall("./ContinuedParagraph"):
            for text_el in cp.findall("./Text"):
                txt = _extract_text(text_el)
                if txt:
                    lines.append(f" {txt}")
                    lines.append("")

        # ContinuedSubparagraph at subsection level
        for csp in subsec.findall("./ContinuedSubparagraph"):
            for text_el in csp.findall("./Text"):
                txt = _extract_text(text_el)
                if txt:
                    lines.append(f"    {txt}")
                    lines.append("")

        # Item (list items within subsection)
        for item in subsec.findall("./Item"):
            i_label = item.find("Label")
            i_label_text = _text(i_label) if i_label is not None else ""
            for text_el in item.findall("./Text"):
                txt = _extract_text(text_el)
                if txt:
                    prefix = f" **{i_label_text}** " if i_label_text else " "
                    lines.append(f"{prefix}{txt}")
                    lines.append("")

        # Formula (mathematical/financial formulas)
        for formula in subsec.findall("./Formula"):
            formula_parts = []
            for fc in formula:
                fc_tag = etree.QName(fc).localname if isinstance(fc.tag, str) else ""
                if fc_tag in ("FormulaTerm", "FormulaText", "FormulaDefinition", "FormulaConnector"):
                    fc_text = _extract_text(fc)
                    if fc_text:
                        formula_parts.append(fc_text)
            if formula_parts:
                lines.append(f"  `{' '.join(formula_parts)}`")
                lines.append("")

    # Section-level Introduction
    for intro in section.findall("./Introduction"):
        for text_el in intro.findall("./Text"):
            txt = _extract_text(text_el)
            if txt:
                lines.append(txt)
                lines.append("")

    # Section-level Item
    for item in section.findall("./Item"):
        i_label = item.find("Label")
        i_label_text = _text(i_label) if i_label is not None else ""
        for text_el in item.findall("./Text"):
            txt = _extract_text(text_el)
            if txt:
                prefix = f"**{i_label_text}** " if i_label_text else ""
                lines.append(f"{prefix}{txt}")
                lines.append("")

    # Section-level Formula
    for formula in section.findall("./Formula"):
        formula_parts = []
        for fc in formula:
            fc_tag = etree.QName(fc).localname if isinstance(fc.tag, str) else ""
            if fc_tag in ("FormulaTerm", "FormulaText", "FormulaDefinition", "FormulaConnector"):
                fc_text = _extract_text(fc)
                if fc_text:
                    formula_parts.append(fc_text)
        if formula_parts:
            lines.append(f"`{' '.join(formula_parts)}`")
            lines.append("")

    for defn in section.findall("./Definition"):
        term = defn.find("DefinedTermEn")
        if term is not None and term.text:
            lines.append(f"**{term.text.strip()}**")
        for text_el in defn.findall("./Text"):
            txt = _extract_text(text_el)
            if txt:
                lines.append(f" {txt}")
            lines.append("")
    return "\n".join(lines)

def _extract_text(el: etree._Element) -> str:
    """Recursively extract text from an element, including tail text."""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        tag = etree.QName(child).localname if isinstance(child.tag, str) else ""
        child_text = _extract_text(child)
        if tag in ("Emphasis", "DefinedTermEn", "DefinedTermFr"):
            parts.append(f"*{child_text}*")
        elif tag == "DefinitionRef":
            parts.append(f"*{child_text}*")
        elif tag in ("XRefExternal", "AmendedText"):
            parts.append(child_text)
        elif tag in ("FormulaTerm", "FormulaText", "FormulaDefinition", "FormulaConnector"):
            parts.append(child_text)
        else:
            parts.append(child_text)
        if child.tail:
            parts.append(child.tail)
    return "".join(parts).strip()

def _heading_to_md(heading: etree._Element) -> str:
    """Convert a <Heading> element to Markdown heading."""
    title = heading.find("TitleText")
    if title is not None and title.text:
        return f"## {title.text.strip()}"
    return ""

def _body_to_md(body: etree._Element) -> str:
    """Convert the <Body> of an Act/Regulation to Markdown."""
    lines = []
    for child in body:
        tag = etree.QName(child).localname if isinstance(child.tag, str) else ""
        if tag == "Heading":
            h = _heading_to_md(child)
            if h:
                lines.append(h)
                lines.append("")
        elif tag == "Section":
            s = _section_to_md(child)
            if s.strip():
                lines.append(s)
        elif tag == "Part":
            label = child.find("Label")
            title = child.find("TitleText")
            part_heading = ""
            if label is not None and label.text:
                part_heading += label.text.strip()
            if title is not None and title.text:
                part_heading += f" - {title.text.strip()}"
            if part_heading:
                lines.append(f"# {part_heading}")
                lines.append("")
            lines.append(_body_to_md(child))
        elif tag == "Division":
            label = child.find("Label")
            title = child.find("TitleText")
            div_heading = ""
            if label is not None and label.text:
                div_heading += label.text.strip()
            if title is not None and title.text:
                div_heading += f" - {title.text.strip()}"
            if div_heading:
                lines.append(f"### {div_heading}")
                lines.append("")
            lines.append(_body_to_md(child))
        elif tag == "Oath":
            oath_text = _extract_text(child)
            if oath_text:
                lines.append(f"> *{oath_text}*")
                lines.append("")
        elif tag == "List":
            for item in child.findall(".//Item"):
                item_label = item.find("Label")
                item_label_text = _text(item_label) if item_label is not None else ""
                for text_el in item.findall("./Text"):
                    txt = _extract_text(text_el)
                    if txt:
                        prefix = f"**{item_label_text}** " if item_label_text else "- "
                        lines.append(f"{prefix}{txt}")
            lines.append("")
        elif tag == "Schedule":
            sched_label = child.find("Label")
            if sched_label is not None and sched_label.text:
                lines.append(f"---\n\n## {sched_label.text.strip()}")
                lines.append("")
            lines.append(_body_to_md(child))
    return "\n".join(lines)

# Main parse function
def parse_federal_xml(xml_bytes: bytes) -> LawDocument:
    """Parse a Justice Canada XML file into a LawDocument."""
    root = etree.fromstring(xml_bytes)
    root_tag = etree.QName(root).localname if isinstance(root.tag, str) else root.tag
    is_act = root_tag == "Act"
    law_type = LawType.ACT if is_act else LawType.REGULATION

    ident = root.find(".//Identification")
    short_title_el = root.find(".//ShortTitle")
    long_title_el = root.find(".//LongTitle")
    title_en = ""
    title_fr = ""
    identifier = ""

    if short_title_el is not None:
        title_en = _extract_text(short_title_el)
    elif long_title_el is not None:
        title_en = _extract_text(long_title_el)

    instrument = root.find(".//InstrumentNumber")
    chapter = root.find(".//Chapter")
    if instrument is not None and instrument.text:
        identifier = instrument.text.strip()
    elif chapter is not None:
        chap_no = chapter.find("ChapterNumber")
        if chap_no is not None and chap_no.text:
            identifier = f"c-{chap_no.text.strip()}"

    if not identifier:
        from slugify import slugify
        identifier = slugify(title_en) if title_en else "unknown"

    last_amended_str = (
        _attr(root, "{http://justice.gc.ca/lims}lastAmendedDate", "")
        or _attr(root, "lastAmendedDate", "")
    )
    pit_date_str = (
        _attr(root, "{http://justice.gc.ca/lims}pit-date", "")
        or _attr(root, "pit-date", "")
    )
    enacted_str = (
        _attr(root, "{http://justice.gc.ca/lims}enactedDate", "")
        or _attr(root, "enactedDate", "")
    )
    last_amended = _parse_date(last_amended_str)
    pit_date = _parse_date(pit_date_str)
    enacted = _parse_date(enacted_str)

    current_el = root.find(".//Current")
    status = LawStatus.IN_FORCE
    if current_el is not None:
        if current_el.get("in-force", "yes") == "no":
            status = LawStatus.NOT_IN_FORCE

    enabling = root.find(".//EnablingAuthority")
    department = ""
    if enabling is not None:
        department = _extract_text(enabling)

    try:
        nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}
        fr_title_el = root.find(".//ShortTitle[@xml:lang='fr']", namespaces=nsmap)
    except (SyntaxError, KeyError):
        fr_title_el = None

    if fr_title_el is None:
        for st in root.findall(".//ShortTitle"):
            lang = st.get("{http://www.w3.org/XML/1998/namespace}lang", "")
            if lang == "fr":
                fr_title_el = st
                break

    if fr_title_el is not None:
        title_fr = _extract_text(fr_title_el)

    source_url = f"{BASE_URL}/eng/acts/{identifier}/" if is_act else f"{BASE_URL}/eng/regulations/{identifier}/"

    metadata = LawMetadata(
        title=title_en or identifier,
        identifier=identifier,
        jurisdiction=Jurisdiction.FEDERAL,
        law_type=law_type,
        status=status,
        last_amended=last_amended or pit_date,
        enacted_date=enacted,
        title_fr=title_fr or None,
        source_url=source_url,
        department=department,
    )

    body = root.find(".//Body")
    body_md = _body_to_md(body) if body is not None else ""

    preamble = root.find(".//Preamble")
    if preamble is not None:
        preamble_text = _extract_text(preamble)
        if preamble_text:
            body_md = f"> {preamble_text}\n\n{body_md}"

    return LawDocument(
        metadata=metadata,
        body_markdown=body_md,
        raw_xml=xml_bytes.decode("utf-8", errors="replace"),
    )

# Fetcher class
class FederalFetcher:
    """Fetch and parse Canadian federal legislation."""

    def __init__(self, throttle: float = 0.3):
        self.client = ThrottledClient(throttle=throttle)

    def discover_acts(self) -> list[str]:
        """Discover all Act IDs from the index page.
        Returns a list of Act alphanumeric IDs (e.g., ['A-1', 'B-3', 'C-46']).
        """
        logger.info("Discovering federal acts...")
        html = self.client.get_text(ACTS_INDEX_URL)
        act_ids = re.findall(r'/eng/acts/([A-Za-z0-9._-]+)/', html)
        seen = set()
        unique = []
        for aid in act_ids:
            if aid not in seen:
                seen.add(aid)
                unique.append(aid)
        logger.info(f"Found {len(unique)} federal acts")
        return unique

    def discover_regulations(self) -> list[str]:
        """Discover all Regulation IDs from the index page."""
        logger.info("Discovering federal regulations...")
        html = self.client.get_text(REGS_INDEX_URL)
        reg_ids = re.findall(r'/eng/regulations/([A-Za-z0-9._-]+)/', html)
        seen = set()
        unique = []
        for rid in reg_ids:
            if rid not in seen:
                seen.add(rid)
                unique.append(rid)
        logger.info(f"Found {len(unique)} federal regulations")
        return unique

    def fetch_act(self, act_id: str) -> Optional[LawDocument]:
        """Fetch and parse a single federal Act by ID."""
        url = XML_URL_TEMPLATE.format(act_id=act_id)
        try:
            xml_bytes = self.client.get_xml(url)
            doc = parse_federal_xml(xml_bytes)
            logger.info(f"Parsed: {doc.metadata.title} ({act_id})")
            return doc
        except Exception as e:
            logger.error(f"Failed to fetch/parse act {act_id}: {e}")
            return None

    def fetch_regulation(self, reg_id: str) -> Optional[LawDocument]:
        """Fetch and parse a single federal Regulation by ID."""
        url = XML_URL_TEMPLATE.format(act_id=reg_id)
        try:
            xml_bytes = self.client.get_xml(url)
            doc = parse_federal_xml(xml_bytes)
            logger.info(f"Parsed: {doc.metadata.title} ({reg_id})")
            return doc
        except Exception as e:
            logger.error(f"Failed to fetch/parse regulation {reg_id}: {e}")
            return None

    def fetch_all(self, include_regulations: bool = False) -> Iterator[LawDocument]:
        """Fetch all federal acts (and optionally regulations).
        Yields LawDocument objects as they are fetched.
        """
        act_ids = self.discover_acts()
        for act_id in act_ids:
            doc = self.fetch_act(act_id)
            if doc:
                yield doc
        if include_regulations:
            reg_ids = self.discover_regulations()
            for reg_id in reg_ids:
                doc = self.fetch_regulation(reg_id)
                if doc:
                    yield doc

    def fetch_from_local_xml(self, xml_dir: Path) -> Iterator[LawDocument]:
        """Parse laws from a local clone of justicecanada/laws-lois-xml.

        This is faster than fetching from the web — clone the repo first:
          git clone https://github.com/justicecanada/laws-lois-xml.git

        Only processes English consolidated acts and regulations.
        Skips: French (fra/), annual statutes, lookup tables, XSLT, DTDs.
        """
        if not xml_dir.exists():
            raise FileNotFoundError(f"XML directory not found: {xml_dir}")

        # FIX 1: Only scan English consolidated acts + regulations
        acts_dir = xml_dir / "eng" / "acts"
        regs_dir = xml_dir / "eng" / "regulations"
        xml_files = sorted(
            list(acts_dir.glob("*.xml")) + list(regs_dir.glob("*.xml"))
        )
        logger.info(f"Found {len(xml_files)} English XML files in {xml_dir}")

        for xml_file in xml_files:
            try:
                xml_bytes = xml_file.read_bytes()
                doc = parse_federal_xml(xml_bytes)

                # FIX 2: Use the XML filename stem for source_url
                # The file stem matches the Justice Canada URL path component:
                #   eng/acts/A-1.xml        → https://laws-lois.justice.gc.ca/eng/acts/A-1/
                #   eng/regulations/SOR-2018-187.xml → .../eng/regulations/SOR-2018-187/
                stem = xml_file.stem
                parent = xml_file.parent.name  # "acts" or "regulations"

                if parent == "acts":
                    doc.metadata.source_url = f"{BASE_URL}/eng/acts/{stem}/"
                    doc.metadata.law_type = LawType.ACT
                elif parent == "regulations":
                    doc.metadata.source_url = f"{BASE_URL}/eng/regulations/{stem}/"
                    doc.metadata.law_type = LawType.REGULATION

                logger.info(f"Parsed: {doc.metadata.title}")
                yield doc
            except Exception as e:
                logger.error(f"Failed to parse {xml_file}: {e}")
