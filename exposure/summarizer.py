"""Plain-Language Regulation Summary Generator.

Turns raw regulation text into human-readable summaries at three levels:
  1. Headline  — ≤15 words, for feed/notification
  2. Brief     — 2-3 sentences, for card/preview
  3. Detailed  — structured breakdown with who/what/why/when

Design principle §11: UI/language principles.
  - Never say "impact", "caused", "drove"
  - Use "around the time of", "coincided with", "associated with"
  - ETFs are "exposed to" regulations, not "affected by" them

This module is rules-based (no LLM). It extracts structure from:
  - Title patterns ("Standards of Performance for...")
  - Agency context (EPA → environmental, SEC → financial)
  - Obligation type (RESTRICTS, MANDATES, SUBSIDIZES, EXEMPTS)
  - CFR references (which code is being changed)
  - Abstract text (keyword extraction)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .schema import ObligationType


# ── Summary Output ─────────────────────────────────────────────────────

@dataclass
class RegulationSummary:
    """Multi-level summary of a regulation."""
    headline: str           # ≤15 words, for feed
    brief: str              # 2-3 sentences, for card
    detailed: str           # structured breakdown
    action_verb: str        # "tightens", "requires", "incentivizes", etc.
    regulated_entities: str # who is regulated (plain language)
    key_change: str         # what changes (plain language)
    timeline: str           # when it takes effect
    tags: list[str]         # topic tags for filtering


# ── Agency Context ─────────────────────────────────────────────────────

_AGENCY_CONTEXT: dict[str, dict] = {
    "environmental-protection-agency": {
        "domain": "environmental",
        "short": "EPA",
        "typical_entities": "industrial facilities, manufacturers, power plants",
        "topics": ["emissions", "pollution", "waste", "water quality", "air quality"],
    },
    "securities-and-exchange-commission": {
        "domain": "financial",
        "short": "SEC",
        "typical_entities": "public companies, broker-dealers, investment funds",
        "topics": ["disclosure", "reporting", "trading", "investor protection"],
    },
    "food-and-drug-administration": {
        "domain": "health",
        "short": "FDA",
        "typical_entities": "drug manufacturers, medical device makers, food producers",
        "topics": ["drug approval", "safety", "labeling", "clinical trials"],
    },
    "department-of-health-and-human-services": {
        "domain": "healthcare",
        "short": "HHS",
        "typical_entities": "healthcare providers, insurers, pharmaceutical companies, hospitals",
        "topics": ["public health", "healthcare policy", "insurance regulation", "drug pricing"],
    },
    "federal-aviation-administration": {
        "domain": "transportation",
        "short": "FAA",
        "typical_entities": "airlines, aircraft manufacturers, airports",
        "topics": ["airworthiness", "safety", "certification", "air traffic"],
    },
    "department-of-labor": {
        "domain": "labor",
        "short": "DOL",
        "typical_entities": "employers, workers, unions",
        "topics": ["wages", "workplace safety", "benefits", "overtime"],
    },
    "occupational-safety-and-health-administration": {
        "domain": "workplace safety",
        "short": "OSHA",
        "typical_entities": "employers in construction, manufacturing, mining",
        "topics": ["safety standards", "hazard prevention", "worker protection"],
    },
    "federal-communications-commission": {
        "domain": "telecommunications",
        "short": "FCC",
        "typical_entities": "telecom carriers, broadcasters, internet providers",
        "topics": ["spectrum", "broadband", "broadcasting", "net neutrality"],
    },
    "department-of-transportation": {
        "domain": "transportation",
        "short": "DOT",
        "typical_entities": "carriers, vehicle manufacturers, pipeline operators",
        "topics": ["safety standards", "infrastructure", "vehicle standards"],
    },
    "national-highway-traffic-safety-administration": {
        "domain": "auto safety",
        "short": "NHTSA",
        "typical_entities": "automakers, vehicle dealers, parts manufacturers",
        "topics": ["vehicle safety", "recalls", "crash standards", "fuel economy"],
    },
    "centers-for-medicare-and-medicaid-services": {
        "domain": "healthcare",
        "short": "CMS",
        "typical_entities": "hospitals, physicians, insurers, nursing facilities",
        "topics": ["Medicare", "Medicaid", "payment rates", "coverage"],
    },
    "consumer-financial-protection-bureau": {
        "domain": "consumer finance",
        "short": "CFPB",
        "typical_entities": "banks, lenders, credit card companies, debt collectors",
        "topics": ["lending", "credit", "consumer protection", "fair lending"],
    },
    "federal-deposit-insurance-corporation": {
        "domain": "banking",
        "short": "FDIC",
        "typical_entities": "banks, savings institutions, credit unions",
        "topics": ["deposit insurance", "bank safety", "resolution", "compliance"],
    },
    "commodity-futures-trading-commission": {
        "domain": "derivatives",
        "short": "CFTC",
        "typical_entities": "futures exchanges, swap dealers, commodity traders",
        "topics": ["derivatives", "margin", "clearing", "market manipulation"],
    },
    "nuclear-regulatory-commission": {
        "domain": "nuclear",
        "short": "NRC",
        "typical_entities": "nuclear power plants, fuel facilities, waste handlers",
        "topics": ["nuclear safety", "licensing", "radiation", "waste disposal"],
    },
    "department-of-agriculture": {
        "domain": "agriculture",
        "short": "USDA",
        "typical_entities": "farms, food processors, agricultural businesses",
        "topics": ["food safety", "organic", "animal welfare", "crop insurance"],
    },
    "bureau-of-land-management": {
        "domain": "public lands",
        "short": "BLM",
        "typical_entities": "mining companies, oil/gas lessees, ranchers",
        "topics": ["leasing", "mining", "grazing", "land use"],
    },
    "department-of-housing-and-urban-development": {
        "domain": "housing",
        "short": "HUD",
        "typical_entities": "lenders, landlords, housing authorities",
        "topics": ["fair housing", "mortgage", "affordable housing", "FHA"],
    },
    "pipeline-and-hazardous-materials-safety-administration": {
        "domain": "pipeline safety",
        "short": "PHMSA",
        "typical_entities": "pipeline operators, hazmat transporters",
        "topics": ["pipeline integrity", "hazmat", "safety standards"],
    },
    "department-of-defense": {
        "domain": "defense",
        "short": "DOD",
        "typical_entities": "defense contractors, military suppliers",
        "topics": ["procurement", "cybersecurity", "acquisition", "ITAR"],
    },
    "fish-and-wildlife-service": {
        "domain": "wildlife",
        "short": "FWS",
        "typical_entities": "developers, landowners, fishing operations",
        "topics": ["endangered species", "habitat", "conservation", "hunting"],
    },
    "department-of-the-interior": {
        "domain": "natural resources",
        "short": "DOI",
        "typical_entities": "energy companies, mining operators, park concessions",
        "topics": ["public lands", "energy leasing", "conservation", "water rights"],
    },
    "department-of-commerce": {
        "domain": "trade/technology",
        "short": "DOC",
        "typical_entities": "exporters, tech companies, manufacturers",
        "topics": ["export controls", "trade", "technology transfer", "census"],
    },
    "internal-revenue-service": {
        "domain": "tax",
        "short": "IRS",
        "typical_entities": "taxpayers, corporations, financial institutions",
        "topics": ["taxation", "reporting", "deductions", "compliance"],
    },
    "department-of-the-treasury": {
        "domain": "financial",
        "short": "Treasury",
        "typical_entities": "banks, financial institutions, foreign investors",
        "topics": ["sanctions", "AML", "banking", "currency"],
    },
    "department-of-veterans-affairs": {
        "domain": "veterans",
        "short": "VA",
        "typical_entities": "VA hospitals, veterans, healthcare providers",
        "topics": ["veterans benefits", "healthcare", "disability", "GI Bill"],
    },
    "department-of-education": {
        "domain": "education",
        "short": "ED",
        "typical_entities": "schools, universities, student loan servicers",
        "topics": ["student loans", "Title IX", "accreditation", "financial aid"],
    },
    "department-of-justice": {
        "domain": "law enforcement",
        "short": "DOJ",
        "typical_entities": "tech platforms, pharmaceutical companies",
        "topics": ["antitrust", "civil rights", "drug enforcement", "privacy"],
    },
    "federal-trade-commission": {
        "domain": "consumer protection",
        "short": "FTC",
        "typical_entities": "retailers, advertisers, data brokers, tech companies",
        "topics": ["privacy", "competition", "advertising", "data security"],
    },
    "department-of-homeland-security": {
        "domain": "security",
        "short": "DHS",
        "typical_entities": "transportation providers, critical infrastructure",
        "topics": ["cybersecurity", "immigration", "border security", "FEMA"],
    },
    "department-of-energy": {
        "domain": "energy",
        "short": "DOE",
        "typical_entities": "utilities, energy producers, appliance manufacturers",
        "topics": ["efficiency standards", "nuclear", "renewable energy", "grid"],
    },
}

# ── Obligation → Action Verb ───────────────────────────────────────────

_OBLIGATION_VERBS: dict[ObligationType, dict] = {
    ObligationType.RESTRICTS: {
        "verb": "tightens",
        "past": "tightened",
        "gerund": "tightening",
        "description": "places new limits on",
    },
    ObligationType.MANDATES: {
        "verb": "requires",
        "past": "required",
        "gerund": "requiring",
        "description": "introduces new requirements for",
    },
    ObligationType.SUBSIDIZES: {
        "verb": "incentivizes",
        "past": "incentivized",
        "gerund": "incentivizing",
        "description": "creates financial incentives for",
    },
    ObligationType.EXEMPTS: {
        "verb": "exempts",
        "past": "exempted",
        "gerund": "exempting",
        "description": "removes obligations from",
    },
    ObligationType.PERMITS: {
        "verb": "allows",
        "past": "allowed",
        "gerund": "allowing",
        "description": "permits previously restricted activity for",
    },
    ObligationType.MODIFIES_THRESHOLD: {
        "verb": "adjusts thresholds for",
        "past": "adjusted thresholds for",
        "gerund": "adjusting thresholds for",
        "description": "changes numeric limits affecting",
    },
}

# ── Title Pattern Extraction ───────────────────────────────────────────

_TITLE_PATTERNS = [
    # "Standards of Performance for X"
    (r"Standards? of Performance for (.+)", "performance standards for {0}"),
    # "National Emission Standards for X"
    (r"National Emission Standards? for (?:Hazardous Air Pollutants:?\s*)?(.+)",
     "emission standards for {0}"),
    # "Airworthiness Directives; X"
    (r"Airworthiness Directives?[;:]\s*(.+)", "airworthiness directive for {0}"),
    # "Federal Motor Vehicle Safety Standards; X"
    (r"Federal Motor Vehicle Safety Standards?[;:]\s*(.+)", "vehicle safety standard: {0}"),
    # "Medicare Program; X"
    (r"Medicare Program[;:]\s*(.+)", "Medicare {0}"),
    # "Medicaid Program; X"
    (r"Medicaid Program[;:]\s*(.+)", "Medicaid {0}"),
    # "Oil and Gas; X"
    (r"Oil and Gas[;:]\s*(.+)", "oil and gas {0}"),
    # "Cybersecurity X"
    (r"Cybersecurity\s+(.+)", "cybersecurity {0}"),
    # General: "The X of Y"
    (r"The (.+?) (?:of|for) (.+)", "{0} of {1}"),
]


def _extract_subject_from_title(title: str) -> str:
    """Extract the core subject from a regulation title."""
    for pattern, template in _TITLE_PATTERNS:
        m = re.match(pattern, title, re.IGNORECASE)
        if m:
            groups = m.groups()
            result = template
            for i, g in enumerate(groups):
                result = result.replace(f"{{{i}}}", g.strip()[:60])
            return result

    # Fallback: use title as-is, truncated
    clean = re.sub(r"\s+", " ", title).strip()
    if len(clean) > 80:
        clean = clean[:77] + "..."
    return clean.lower()


# ── Keyword Extraction from Abstract ───────────────────────────────────

_CHANGE_KEYWORDS = {
    "new": "introduces new",
    "revised": "revises",
    "amend": "amends",
    "update": "updates",
    "repeal": "repeals",
    "withdraw": "withdraws",
    "extend": "extends",
    "delay": "delays",
    "increase": "increases",
    "decrease": "decreases",
    "establish": "establishes",
    "eliminate": "eliminates",
    "prohibit": "prohibits",
    "require": "requires",
    "modify": "modifies",
    "strengthen": "strengthens",
    "relax": "relaxes",
    "expand": "expands",
    "limit": "limits",
    "finalize": "finalizes",
}


def _detect_change_type(abstract: str) -> str:
    """Detect the type of change from abstract text."""
    lower = abstract.lower()
    for keyword, verb in _CHANGE_KEYWORDS.items():
        if keyword in lower:
            return verb
    return "updates"


def _extract_timeline(abstract: str, effective_date=None, comment_end=None) -> str:
    """Extract timeline information."""
    parts = []
    if effective_date:
        parts.append(f"effective {effective_date.isoformat()}")
    if comment_end:
        parts.append(f"comments due {comment_end.isoformat()}")

    # Look for date mentions in abstract
    date_patterns = [
        r"effective (\w+ \d+, \d{4})",
        r"beginning (\w+ \d+, \d{4})",
        r"compliance date.{0,20}(\w+ \d+, \d{4})",
    ]
    for pattern in date_patterns:
        m = re.search(pattern, abstract, re.IGNORECASE)
        if m:
            parts.append(f"compliance by {m.group(1)}")
            break

    return "; ".join(parts) if parts else "timeline not specified"


def _extract_tags(
    agency_slug: str, abstract: str, title: str
) -> list[str]:
    """Generate topic tags for filtering."""
    tags = set()

    # Agency-based tags
    ctx = _AGENCY_CONTEXT.get(agency_slug, {})
    if ctx.get("domain"):
        tags.add(ctx["domain"])
    for topic in ctx.get("topics", []):
        if topic.lower() in abstract.lower() or topic.lower() in title.lower():
            tags.add(topic)

    # Content-based tags
    tag_keywords = {
        "climate": ["climate", "greenhouse", "carbon", "emission"],
        "cybersecurity": ["cyber", "cybersecurity", "data breach", "incident"],
        "AI": ["artificial intelligence", "machine learning", "AI", "algorithm"],
        "crypto": ["cryptocurrency", "digital asset", "blockchain", "token"],
        "privacy": ["privacy", "personal data", "GDPR", "consumer data"],
        "ESG": ["ESG", "sustainability", "social governance"],
        "pharma": ["drug", "pharmaceutical", "biosimilar", "clinical trial"],
        "banking": ["bank", "deposit", "lending", "mortgage"],
        "energy": ["oil", "gas", "petroleum", "renewable", "solar", "wind"],
        "auto": ["vehicle", "automobile", "crash", "fuel economy"],
    }

    lower_text = (abstract + " " + title).lower()
    for tag, keywords in tag_keywords.items():
        if any(kw.lower() in lower_text for kw in keywords):
            tags.add(tag)

    return sorted(tags)


# ── Main Summarizer ────────────────────────────────────────────────────

class RegulationSummarizer:
    """Generate plain-language summaries of regulations.

    Usage:
        summarizer = RegulationSummarizer()
        summary = summarizer.summarize(
            title="Standards of Performance for GHG Emissions...",
            agency_slug="environmental-protection-agency",
            abstract="EPA is finalizing emission guidelines...",
            doc_type="RULE",
            obligation_type=ObligationType.RESTRICTS,
        )
        print(summary.headline)  # "EPA tightens GHG emission standards for power plants"
        print(summary.brief)     # 2-3 sentence summary
    """

    def summarize(
        self,
        title: str,
        agency_slug: str,
        abstract: str = "",
        doc_type: str = "RULE",
        obligation_type: Optional[ObligationType] = None,
        effective_date=None,
        comment_end_date=None,
        significant: bool = False,
        etf_tickers: list[str] | None = None,
        industry_count: int = 0,
    ) -> RegulationSummary:
        """Generate a multi-level summary."""

        ctx = _AGENCY_CONTEXT.get(agency_slug, {})
        agency_short = ctx.get("short", agency_slug.split("-")[0].upper())
        typical_entities = ctx.get("typical_entities", "regulated entities")

        # Determine action verb
        if obligation_type:
            verb_info = _OBLIGATION_VERBS.get(obligation_type, {})
            action_verb = verb_info.get("verb", "updates rules for")
            action_desc = verb_info.get("description", "changes rules for")
        else:
            change = _detect_change_type(abstract)
            action_verb = change
            action_desc = f"{change} rules for"

        # Extract subject from title
        subject = _extract_subject_from_title(title)

        # Doc type context
        if doc_type == "PRORULE":
            doc_label = "proposes"
            status = "proposed"
        elif doc_type == "RULE":
            doc_label = "finalizes"
            status = "final"
        else:
            doc_label = "issues"
            status = ""

        # ── Headline (≤15 words) ──
        headline = f"{agency_short} {action_verb} {subject}"
        # Truncate to ~15 words
        words = headline.split()
        if len(words) > 15:
            headline = " ".join(words[:14]) + "..."

        # ── Brief (2-3 sentences) ──
        brief_parts = []

        # Sentence 1: What happened
        s1 = f"The {agency_short} {doc_label} a {status} rule {action_desc} {typical_entities}."
        brief_parts.append(s1.strip())

        # Sentence 2: What it does (from abstract)
        if abstract:
            # Extract first meaningful sentence from abstract
            sentences = re.split(r"[.!]\s+", abstract)
            for sent in sentences[1:3]:  # skip first (usually "The Agency is...")
                sent = sent.strip()
                if len(sent) > 30 and not sent.startswith("This action"):
                    brief_parts.append(sent[:200] + ("." if not sent.endswith(".") else ""))
                    break

        # Sentence 3: Exposure note
        if etf_tickers:
            etf_str = ", ".join(etf_tickers[:4])
            if len(etf_tickers) > 4:
                etf_str += f" and {len(etf_tickers) - 4} others"
            brief_parts.append(
                f"Exposure observed in {etf_str} across {industry_count} industries."
            )

        brief = " ".join(brief_parts)

        # ── Detailed ──
        detail_lines = []
        detail_lines.append(f"**Regulation:** {title}")
        detail_lines.append(f"**Agency:** {agency_short} ({agency_slug})")
        detail_lines.append(f"**Status:** {status.title()} Rule" if status else f"**Type:** {doc_type}")
        if significant:
            detail_lines.append("**Significance:** Major (>$100M economic threshold)")
        detail_lines.append(f"**Action:** {action_verb.title()}")
        detail_lines.append(f"**Regulated entities:** {typical_entities}")

        timeline = _extract_timeline(abstract, effective_date, comment_end_date)
        detail_lines.append(f"**Timeline:** {timeline}")

        if abstract:
            detail_lines.append(f"\n**Summary:** {abstract[:500]}")

        if etf_tickers:
            detail_lines.append(f"\n**Exposed ETFs ({len(etf_tickers)}):** {', '.join(etf_tickers)}")
            detail_lines.append(f"**Industries:** {industry_count}")

        detailed = "\n".join(detail_lines)

        # ── Tags ──
        tags = _extract_tags(agency_slug, abstract, title)

        # ── Regulated entities (plain language) ──
        regulated = typical_entities

        # ── Key change ──
        key_change = f"{action_verb} {subject}"

        return RegulationSummary(
            headline=headline,
            brief=brief,
            detailed=detailed,
            action_verb=action_verb,
            regulated_entities=regulated,
            key_change=key_change,
            timeline=timeline,
            tags=tags,
        )
