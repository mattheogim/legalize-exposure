"""Regulation-to-Exposure Mapper.

The main pipeline that takes a Federal Register document and produces
a complete exposure graph: regulation → provisions → obligations →
entity types → industries → ETFs.

This is the "brain" that the design principles doc calls for:
"법이 바뀌는 걸 보는 좋은 눈"(diff pipeline) 에 연결되는
"그래서 누구와 관련 있는지 판단하는 뇌".
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .schema import (
    EdgeType,
    EvidenceType,
    ObligationType,
    Edge,
    Regulation,
    Provision,
    Obligation,
    RegulatedEntityType,
    Industry,
    ETFProxy,
    ExposureGraph,
)
from .lookups import AgencyLookup, CFRLookup, IndustryMatch
from .etf_exposure import ETFExposureEngine

logger = logging.getLogger(__name__)


# ── Exclusion Rules ───────────────────────────────────────────────────
# Known false-positive patterns: (agency_slug, naics_prefix) pairs that
# should be excluded even though the broad agency→NAICS mapping suggests
# a connection. These represent domain knowledge about regulatory scope.
#
# Format: {agency_slug: [list of NAICS prefixes that are NOT relevant]}
# The agency lookup casts a wide net; these narrow it down.

_EXCLUSION_RULES: dict[str, list[str]] = {
    # EPA air/water rules don't affect banking/finance
    "environmental-protection-agency": [
        "522",   # Credit Intermediation (Banking)
        "523",   # Securities & Investments
        "524",   # Insurance
    ],
    # SEC financial rules don't affect mining/drilling/farming
    "securities-and-exchange-commission": [
        "211",   # Oil & Gas Extraction
        "212",   # Mining
        "213",   # Mining Support
        "111",   # Crop Production
        "112",   # Animal Production
    ],
    # OSHA workplace safety rules don't affect pure financial services
    "occupational-safety-and-health-administration": [
        "522",   # Banking
        "523",   # Securities
        "524",   # Insurance
    ],
    # NRC nuclear rules are very narrow
    "nuclear-regulatory-commission": [
        "111",   # Crop Production
        "112",   # Animal Production
        "445",   # Food & Beverage Retail
        "721",   # Accommodation
        "722",   # Food Services
    ],
    # NHTSA vehicle rules don't affect non-transport sectors
    "national-highway-traffic-safety-administration": [
        "522",   # Banking
        "523",   # Securities
        "524",   # Insurance
        "111",   # Crops
        "112",   # Animals
    ],
    # FCC telecom rules are narrow
    "federal-communications-commission": [
        "211",   # Oil & Gas
        "212",   # Mining
        "111",   # Crops
        "112",   # Animals
        "721",   # Accommodation
    ],
    # FAA aviation rules are narrow
    "federal-aviation-administration": [
        "211",   # Oil & Gas
        "212",   # Mining
        "522",   # Banking
        "523",   # Securities
        "111",   # Crops
        "112",   # Animals
    ],
    # FDIC banking rules don't affect non-financial sectors
    "federal-deposit-insurance-corporation": [
        "211",   # Oil & Gas
        "212",   # Mining
        "325",   # Chemical Manufacturing
        "336",   # Transportation Equipment
    ],
    # CFTC commodities/derivatives rules are financial-specific
    "commodity-futures-trading-commission": [
        "325",   # Chemical Manufacturing
        "336",   # Transportation Equipment
        "541",   # Professional Services
    ],
}

# Keyword-based exclusion: if ALL of these keywords appear in the title/abstract,
# exclude the listed NAICS. Catches narrow rules the agency map misses.
_KEYWORD_EXCLUSIONS: list[tuple[list[str], list[str]]] = [
    # Aviation safety rules → exclude banking
    (["aircraft", "airworthiness"], ["522", "523", "524"]),
    # Nuclear plant rules → exclude agriculture
    (["nuclear", "reactor"], ["111", "112", "113", "114"]),
    # Drug labeling rules → exclude energy
    (["drug", "labeling"], ["211", "212", "213", "221"]),
    # Mine safety rules → exclude healthcare
    (["mine", "safety"], ["621", "622", "623"]),
    # Vehicle emission rules → exclude banking
    (["vehicle", "emission"], ["522", "523", "524"]),
    # Telecom spectrum rules → exclude agriculture
    (["spectrum", "wireless"], ["111", "112", "113", "114"]),
]


def get_excluded_naics(
    agency_slug: str, title: str = "", abstract: str = ""
) -> set[str]:
    """Return NAICS prefixes that should be excluded for this regulation.

    Combines agency-level rules with keyword-based rules.
    """
    excluded: set[str] = set()

    # Agency-level exclusions
    if agency_slug in _EXCLUSION_RULES:
        excluded.update(_EXCLUSION_RULES[agency_slug])

    # Keyword-based exclusions
    text = (title + " " + abstract).lower()
    for keywords, naics_list in _KEYWORD_EXCLUSIONS:
        if all(kw in text for kw in keywords):
            excluded.update(naics_list)

    return excluded


@dataclass
class MappingResult:
    """Result of mapping a regulatory document to its exposure chain."""
    regulation: Regulation
    graph: ExposureGraph
    industries: list[Industry]
    etfs: list[ETFProxy]
    confidence_summary: dict[str, float]   # edge_type → avg confidence


class ExposureMapper:
    """Maps Federal Register documents to affected industries and ETFs.

    Usage:
        mapper = ExposureMapper()

        result = mapper.map_federal_register_doc(
            title="Emissions Standards for Power Plants",
            agency_slug="environmental-protection-agency",
            cfr_citations=["40 CFR 60"],
            doc_type="RULE",
            fr_doc_number="2026-01234",
            publication_date=date(2026, 3, 15),
            significant=True,
            abstract="EPA is finalizing emissions standards for coal-fired...",
        )

        print(result.etfs)          # [ETFProxy(ticker="XLE", ...), ...]
        print(result.graph.summary())
    """

    def __init__(self):
        self.agency_lookup = AgencyLookup()
        self.cfr_lookup = CFRLookup()
        self.etf_engine = ETFExposureEngine()

    def map_federal_register_doc(
        self,
        title: str,
        agency_slug: str,
        cfr_citations: list[str],
        doc_type: str = "RULE",
        fr_doc_number: str = "",
        publication_date: Optional[date] = None,
        effective_date: Optional[date] = None,
        comment_end_date: Optional[date] = None,
        significant: bool = False,
        rin: str = "",
        abstract: str = "",
    ) -> MappingResult:
        """Full mapping pipeline for a Federal Register document.

        Steps:
        1. Create Regulation node
        2. Run LF1 (agency → industry) and LF2 (CFR → industry)
        3. Merge and deduplicate industry matches
        4. For each industry, find exposed ETFs via holdings
        5. Build the exposure graph with all edges
        """
        graph = ExposureGraph()

        # ── Step 1: Regulation node ──────────────────────────────────
        reg = Regulation(
            title=title,
            agency_slug=agency_slug,
            cfr_cite=cfr_citations[0] if cfr_citations else "",
            doc_type=doc_type,
            fr_doc_number=fr_doc_number,
            publication_date=publication_date,
            effective_date=effective_date,
            comment_end_date=comment_end_date,
            significant=significant,
            rin=rin,
        )
        graph.add_node(reg)

        # ── Step 2: Provision (placeholder — filled by diff parser) ──
        prov = Provision(
            regulation_id=reg.id,
            section=cfr_citations[0] if cfr_citations else "",
            title=title,
            diff_summary=abstract[:500] if abstract else "",
        )
        graph.add_node(prov)

        # ── Step 3: Obligation extraction (rule-based) ───────────────
        obl_type = self._detect_obligation_type(title, abstract)
        obl = Obligation(
            provision_id=prov.id,
            obligation_type=obl_type,
            description=abstract[:300] if abstract else title,
            mandatory_language=self._extract_mandatory_language(abstract),
        )
        graph.add_node(obl)

        # Temporal: edges are valid from effective_date (or publication_date)
        edge_valid_from = effective_date or publication_date

        # Link: Provision → Obligation
        graph.add_edge(Edge(
            source_id=prov.id,
            target_id=obl.id,
            edge_type=EdgeType.IMPOSES,
            evidence_type=EvidenceType.KEYWORD,
            confidence=0.9,
            provenance=f"Obligation extracted from: {title}",
            valid_from=edge_valid_from,
        ))

        # ── Step 4: Entity Type (generic for now) ────────────────────
        entity = RegulatedEntityType(
            description=f"Entities regulated by {agency_slug.replace('-', ' ').title()}",
        )
        graph.add_node(entity)

        # Link: Obligation → EntityType
        graph.add_edge(Edge(
            source_id=obl.id,
            target_id=entity.id,
            edge_type=EdgeType.APPLIES_TO,
            evidence_type=EvidenceType.METADATA,
            confidence=0.9,
            provenance=f"Agency jurisdiction: {agency_slug}",
            valid_from=edge_valid_from,
        ))

        # ── Step 5: Industry matching (LF1 + LF2 merge) ─────────────
        industry_matches: dict[str, IndustryMatch] = {}

        # LF1: Agency → Industry
        for match in self.agency_lookup.match(agency_slug):
            key = match.naics_code
            if key not in industry_matches or match.confidence > industry_matches[key].confidence:
                industry_matches[key] = match

        # LF2: CFR → Industry (higher confidence, overwrites if better)
        for cite in cfr_citations:
            for match in self.cfr_lookup.match_from_cite(cite):
                key = match.naics_code
                if key not in industry_matches or match.confidence > industry_matches[key].confidence:
                    industry_matches[key] = match

        # LF3: NAICS regex in text (highest confidence if found)
        for naics_code in self._extract_naics_codes(abstract):
            if naics_code not in industry_matches:
                industry_matches[naics_code] = IndustryMatch(
                    naics_code=naics_code,
                    naics_title=f"NAICS {naics_code}",
                    confidence=0.95,
                    provenance=f"NAICS code found in text: {naics_code}",
                )

        # ── Step 5b: Apply exclusion rules (negative mapping) ────────
        excluded_naics = get_excluded_naics(agency_slug, title, abstract)
        excluded_matches: dict[str, IndustryMatch] = {}
        for naics_code in list(industry_matches.keys()):
            # Check if this NAICS or any of its prefixes is excluded
            if self._is_excluded(naics_code, excluded_naics):
                excluded_matches[naics_code] = industry_matches.pop(naics_code)

        industries = []
        for match in industry_matches.values():
            ind = Industry(
                naics_code=match.naics_code,
                naics_title=match.naics_title,
                gics_sector=match.gics_sector,
                gics_code=match.gics_code,
            )
            graph.add_node(ind)
            industries.append(ind)

            # Link: EntityType → Industry (soft link)
            graph.add_edge(Edge(
                source_id=entity.id,
                target_id=ind.id,
                edge_type=EdgeType.MENTIONS,
                evidence_type=(
                    EvidenceType.CITATION if match.confidence >= 0.9
                    else EvidenceType.METADATA
                ),
                confidence=match.confidence,
                provenance=match.provenance,
                valid_from=edge_valid_from,
            ))

        # Record excluded industries as NOT_RELATED edges (for explainability)
        for match in excluded_matches.values():
            excl_ind = Industry(
                naics_code=match.naics_code,
                naics_title=match.naics_title,
                gics_sector=match.gics_sector,
                gics_code=match.gics_code,
            )
            graph.add_node(excl_ind)
            graph.add_edge(Edge(
                source_id=reg.id,
                target_id=excl_ind.id,
                edge_type=EdgeType.NOT_RELATED,
                evidence_type=EvidenceType.MANUAL,
                confidence=0.8,
                provenance=(
                    f"Exclusion rule: {agency_slug} regulations "
                    f"do not typically affect NAICS {match.naics_code} "
                    f"({match.naics_title})"
                ),
            ))

        # ── Step 6: ETF exposure (holdings-based) ────────────────────
        etfs: list[ETFProxy] = []
        seen_tickers: set[str] = set()

        for ind in industries:
            exposed = self.etf_engine.find_exposed_etfs(ind.naics_code)
            for ticker, score in exposed:
                if ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    profile = self.etf_engine.get_profile(ticker)
                    etf = ETFProxy(
                        ticker=ticker,
                        name=profile.name if profile else "",
                        sector=profile.sector if profile else "",
                        exposure_score=score,
                    )
                    graph.add_node(etf)
                    etfs.append(etf)

                # Link: Industry → ETF (soft link, holdings-based)
                graph.add_edge(Edge(
                    source_id=ind.id,
                    target_id=etf.id if ticker not in {e.ticker for e in etfs[:-1]} else
                        next(e.id for e in etfs if e.ticker == ticker),
                    edge_type=EdgeType.EXPOSES,
                    evidence_type=EvidenceType.HOLDINGS,
                    confidence=min(score + 0.3, 0.85),  # holdings confidence
                    provenance=(
                        f"{ticker} has {score:.0%} exposure to NAICS "
                        f"{ind.naics_code} ({ind.naics_title})"
                    ),
                    valid_from=edge_valid_from,
                ))

        # ── Build confidence summary ─────────────────────────────────
        conf_by_type: dict[str, list[float]] = {}
        for edge in graph.edges:
            key = edge.edge_type.value
            conf_by_type.setdefault(key, []).append(edge.confidence)
        conf_summary = {
            k: sum(v) / len(v) for k, v in conf_by_type.items()
        }

        return MappingResult(
            regulation=reg,
            graph=graph,
            industries=industries,
            etfs=etfs,
            confidence_summary=conf_summary,
        )

    # ── Helper Methods ───────────────────────────────────────────────

    @staticmethod
    def _is_excluded(naics_code: str, excluded_prefixes: set[str]) -> bool:
        """Check if a NAICS code matches any excluded prefix.

        "522" excludes "522", "5221", "52211", etc.
        "5221" does NOT exclude "522" (more specific doesn't exclude broader).
        """
        for prefix in excluded_prefixes:
            if naics_code.startswith(prefix):
                return True
        return False

    @staticmethod
    def _detect_obligation_type(title: str, abstract: str) -> ObligationType:
        """Simple keyword-based obligation type detection."""
        text = (title + " " + abstract).lower()

        if any(w in text for w in ["exempt", "waiver", "relief", "exclusion"]):
            return ObligationType.EXEMPTS
        if any(w in text for w in ["subsid", "incentiv", "tax credit", "grant"]):
            return ObligationType.SUBSIDIZES
        if any(w in text for w in ["prohibit", "restrict", "ban", "limit", "reduce"]):
            return ObligationType.RESTRICTS
        if any(w in text for w in ["threshold", "increase the", "decrease the", "raise", "lower"]):
            return ObligationType.MODIFIES_THRESHOLD
        if any(w in text for w in ["permit", "allow", "authorize"]):
            return ObligationType.PERMITS
        return ObligationType.MANDATES  # default

    @staticmethod
    def _extract_mandatory_language(text: str) -> str:
        """Extract the strongest mandatory verb from text."""
        text_lower = text.lower()
        for phrase in ["shall not", "must not", "may not", "is prohibited",
                       "shall", "must", "is required", "may"]:
            if phrase in text_lower:
                return phrase
        return ""

    @staticmethod
    def _extract_naics_codes(text: str) -> list[str]:
        """LF3: Extract NAICS codes directly mentioned in text."""
        if not text:
            return []
        # Match patterns like "NAICS 211110", "NAICS code 325", "SIC 2911"
        patterns = [
            r"NAICS\s+(?:code\s+)?(\d{3,6})",
            r"SIC\s+(?:code\s+)?(\d{4})",
            r"North American Industry Classification.*?(\d{6})",
        ]
        codes = []
        for pat in patterns:
            codes.extend(re.findall(pat, text, re.IGNORECASE))
        return list(set(codes))
