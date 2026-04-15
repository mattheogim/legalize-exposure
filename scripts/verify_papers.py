#!/usr/bin/env python3
"""Paper verification via Semantic Scholar API.

Automatically verifies:
  Level 1: Paper exists (title, authors, year, journal, citations)
  Level 2: Abstract contains our claimed key terms/numbers

Cannot verify (requires manual PDF review):
  Level 3: Specific formulas, table values, exact quotes from body

Usage:
    python scripts/verify_papers.py
    python scripts/verify_papers.py --update  # update 00-VERIFICATION-STATUS.md

Semantic Scholar API: https://api.semanticscholar.org/
Rate limit: 100 requests/5 minutes (no auth), 1 request/second recommended.
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

API_BASE = "https://api.semanticscholar.org/graph/v1"
RATE_LIMIT = 1.0  # seconds between requests

# ── Paper registry ──────────────────────────────────────────────────────
# Each entry: our_id, search_title, claimed_year, claimed_journal,
#             key_terms (strings that should appear in abstract)

PAPERS: list[dict] = [
    # Core methodology
    {
        "id": "goldsmith-pinkham-2025",
        "title": "Causal Inference in Financial Event Studies",
        "year": 2025,
        "journal": "arXiv",
        "key_terms": ["synthetic control", "factor model", "inconsistent"],
        "claims": ["synthetic control > event study when factor model misspecified"],
    },
    {
        "id": "baker-bloom-davis-2016",
        "title": "Measuring Economic Policy Uncertainty",
        "year": 2016,
        "journal": "Quarterly Journal of Economics",
        "key_terms": ["newspaper", "uncertainty", "policy"],
        "claims": ["EPU index from newspaper text, 3 components"],
    },
    {
        "id": "kalmenovitz-2023",
        "title": "Regulatory Intensity and Firm-Specific Exposure",
        "year": 2023,
        "journal": "Review of Financial Studies",
        "key_terms": ["regulatory", "firm-specific", "compliance"],
        "claims": ["ML on 10-K text to match regulations to firms"],
    },
    {
        "id": "hassan-2019",
        "title": "Firm-Level Political Risk: Measurement and Effects",
        "year": 2019,
        "journal": "Quarterly Journal of Economics",
        "key_terms": ["political risk", "earnings call", "transcripts"],
        "claims": ["bigram classification of conference call text"],
    },
    {
        "id": "regdata-2017",
        "title": "RegData: A Numerical Database on Industry-Specific Regulations",
        "year": 2017,
        "journal": "Regulation and Governance",
        "key_terms": ["restriction", "NAICS", "industry"],
        "claims": ["CFR restriction word counting + ML industry classification"],
    },
    {
        "id": "armstrong-2025",
        "title": "Measuring Firm Exposure to Government Agencies",
        "year": 2025,
        "journal": "Journal of Accounting and Economics",
        "key_terms": ["government agencies", "10-K", "exposure"],
        "claims": ["dictionary-based agency exposure from 10-K filings"],
    },
    # Impact / causal
    {
        "id": "cohen-2013",
        "title": "Legislating Stock Prices",
        "year": 2013,
        "journal": "Journal of Financial Economics",
        "key_terms": ["legislat", "stock prices", "abnormal returns"],
        "claims": ["90 basis points per month post-passage"],
    },
    {
        "id": "ramelli-2021",
        "title": "Investor Rewards to Climate Responsibility",
        "year": 2021,
        "journal": "Review of Corporate Finance Studies",
        "key_terms": ["climate", "election", "stock"],
        "claims": ["opposite regulatory shocks produce opposite returns"],
    },
    # Adversarial
    {
        "id": "brav-heaton-2015",
        "title": "Event Studies in Securities Litigation",
        "year": 2015,
        "journal": "Washington University Law Review",
        "key_terms": ["power", "confounding", "bias"],
        "claims": ["single-firm event studies lack power"],
    },
    {
        "id": "bae-jo-shim-2025",
        "title": "Does Economic Policy Uncertainty Differ from Other Uncertainty Measures",
        "year": 2025,
        "journal": "Canadian Journal of Economics",
        "key_terms": ["EPU", "replication", "uncertainty"],
        "claims": ["EPU loses significance 2008-2019"],
    },
    {
        "id": "binder-1998",
        "title": "The Event Study Methodology Since 1969",
        "year": 1998,
        "journal": "Review of Quantitative Finance and Accounting",
        "key_terms": ["event study", "methodology"],
        "claims": ["regulatory events anticipated, clean event windows impossible"],
    },
    # Validation
    {
        "id": "angrist-pischke-2010",
        "title": "The Credibility Revolution in Empirical Economics",
        "year": 2010,
        "journal": "Journal of Economic Perspectives",
        "key_terms": ["credibility", "design", "causal"],
        "claims": ["design-based inference required for causal claims"],
    },
    {
        "id": "brodeur-2020",
        "title": "Methods Matter: p-Hacking and Publication Bias",
        "year": 2020,
        "journal": "American Economic Review",
        "key_terms": ["p-hacking", "publication bias", "causal"],
        "claims": ["21,000 hypothesis tests analyzed"],
    },
    {
        "id": "harvey-liu-zhu-2016",
        "title": "and the Cross-Section of Expected Returns",
        "year": 2016,
        "journal": "Review of Financial Studies",
        "key_terms": ["cross-section", "factor", "t-statistic"],
        "claims": ["t > 3.0 threshold for new factors"],
    },
    # Pre-event
    {
        "id": "pastor-veronesi-2012",
        "title": "Uncertainty about Government Policy and Stock Prices",
        "year": 2012,
        "journal": "Journal of Finance",
        "key_terms": ["government policy", "uncertainty", "stock"],
        "claims": ["policy anticipation raises risk premia before announcement"],
    },
    {
        "id": "ellison-mullin-2001",
        "title": "Gradual Incorporation of Information",
        "year": 2001,
        "journal": "Journal of Law and Economics",
        "key_terms": ["pharmaceutical", "Clinton", "gradual"],
        "claims": ["52.3% pharma decline over 22 months"],
    },
    {
        "id": "prabhala-1997",
        "title": "Conditional Methods in Event Studies",
        "year": 1997,
        "journal": "Review of Financial Studies",
        "key_terms": ["conditional", "event study", "anticipated"],
        "claims": ["standard methods valid even under anticipation"],
    },
]


@dataclass
class VerificationResult:
    paper_id: str
    # Level 1: existence
    found: bool = False
    actual_title: str = ""
    actual_authors: list[str] = field(default_factory=list)
    actual_year: int = 0
    actual_venue: str = ""
    citation_count: int = 0
    semantic_scholar_id: str = ""
    # Level 2: abstract check
    abstract_available: bool = False
    key_terms_found: list[str] = field(default_factory=list)
    key_terms_missing: list[str] = field(default_factory=list)
    claims_in_abstract: list[str] = field(default_factory=list)
    # Validation
    year_matches: bool = False
    venue_matches: bool = False
    level1_pass: bool = False
    level2_pass: bool = False


def search_paper(title: str, year: int | None = None) -> dict | None:
    """Search Semantic Scholar for a paper by title."""
    params = {"query": title, "limit": 5, "fields": "title,authors,year,venue,citationCount,abstract,externalIds"}
    try:
        resp = requests.get(f"{API_BASE}/paper/search", params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", [])
            if papers:
                # Find best match by title similarity + year
                for p in papers:
                    if year and p.get("year") and abs(p["year"] - year) <= 2:
                        return p
                return papers[0]  # fallback to first result
        elif resp.status_code == 429:
            print("  ⏳ Rate limited, waiting 30s...")
            time.sleep(30)
            return search_paper(title, year)
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
    return None


def verify_paper(entry: dict) -> VerificationResult:
    """Verify a single paper against Semantic Scholar."""
    result = VerificationResult(paper_id=entry["id"])

    time.sleep(RATE_LIMIT)
    paper = search_paper(entry["title"], entry.get("year"))

    if not paper:
        return result

    result.found = True
    result.actual_title = paper.get("title", "")
    result.actual_authors = [a.get("name", "") for a in paper.get("authors", [])]
    result.actual_year = paper.get("year", 0)
    result.actual_venue = paper.get("venue", "")
    result.citation_count = paper.get("citationCount", 0)
    result.semantic_scholar_id = paper.get("paperId", "")

    # Level 1: year + venue
    if result.actual_year:
        result.year_matches = abs(result.actual_year - entry["year"]) <= 1
    if result.actual_venue:
        claimed_journal = entry.get("journal", "").lower()
        actual_venue = result.actual_venue.lower()
        result.venue_matches = (
            claimed_journal in actual_venue
            or actual_venue in claimed_journal
            or any(word in actual_venue for word in claimed_journal.split() if len(word) > 4)
        )
    result.level1_pass = result.found and result.year_matches

    # Level 2: abstract check
    abstract = paper.get("abstract", "") or ""
    result.abstract_available = len(abstract) > 50

    if result.abstract_available:
        abstract_lower = abstract.lower()
        for term in entry.get("key_terms", []):
            if term.lower() in abstract_lower:
                result.key_terms_found.append(term)
            else:
                result.key_terms_missing.append(term)

        for claim in entry.get("claims", []):
            # Check if key words from the claim appear in abstract
            claim_words = [w for w in claim.lower().split() if len(w) > 4]
            matches = sum(1 for w in claim_words if w in abstract_lower)
            if matches >= len(claim_words) * 0.4:  # 40% of key words found
                result.claims_in_abstract.append(f"LIKELY: {claim}")
            else:
                result.claims_in_abstract.append(f"NOT IN ABSTRACT: {claim}")

        result.level2_pass = len(result.key_terms_missing) <= 1

    return result


def run_verification() -> list[VerificationResult]:
    """Verify all papers."""
    results = []
    for i, entry in enumerate(PAPERS):
        print(f"[{i+1}/{len(PAPERS)}] Verifying: {entry['id']}...")
        result = verify_paper(entry)

        status = "✅" if result.level1_pass else ("⚠️" if result.found else "❌")
        cite = f"({result.citation_count} citations)" if result.found else ""
        print(f"  {status} {result.actual_title[:60]} {cite}")

        if result.key_terms_missing:
            print(f"  ⚠️ Missing key terms in abstract: {result.key_terms_missing}")

        results.append(result)
    return results


def generate_report(results: list[VerificationResult]) -> str:
    """Generate verification report."""
    lines = ["# Automated Paper Verification Report", ""]
    lines.append(f"Verified via Semantic Scholar API. {len(results)} papers checked.\n")

    found = sum(1 for r in results if r.found)
    year_ok = sum(1 for r in results if r.year_matches)
    l2_ok = sum(1 for r in results if r.level2_pass)

    lines.append(f"| Check | Result |")
    lines.append(f"|-------|--------|")
    lines.append(f"| Papers found | {found}/{len(results)} |")
    lines.append(f"| Year matches | {year_ok}/{len(results)} |")
    lines.append(f"| Abstract key terms | {l2_ok}/{len(results)} |")
    lines.append("")

    lines.append("## Per-Paper Results\n")
    lines.append("| ID | Found | Year | Venue | Citations | Key Terms | L1 | L2 |")
    lines.append("|-----|:---:|:---:|------|---:|:---:|:---:|:---:|")

    for r in results:
        found = "✅" if r.found else "❌"
        year = "✅" if r.year_matches else f"❌ ({r.actual_year})"
        venue = r.actual_venue[:30] if r.actual_venue else "—"
        cite = str(r.citation_count) if r.found else "—"
        terms = f"{len(r.key_terms_found)}/{len(r.key_terms_found)+len(r.key_terms_missing)}"
        l1 = "✅" if r.level1_pass else "❌"
        l2 = "✅" if r.level2_pass else ("⚠️" if r.abstract_available else "—")
        lines.append(f"| {r.paper_id} | {found} | {year} | {venue} | {cite} | {terms} | {l1} | {l2} |")

    lines.append("\n## Claims Requiring Manual PDF Verification\n")
    lines.append("These claims could NOT be verified from abstracts alone:\n")
    for r in results:
        for claim in r.claims_in_abstract:
            if "NOT IN ABSTRACT" in claim:
                lines.append(f"- **{r.paper_id}**: {claim}")

    lines.append("\n---")
    lines.append("*Level 1 = paper exists + year matches. Level 2 = key terms in abstract.*")
    lines.append("*Level 3 (formulas, specific numbers) requires manual PDF review.*")

    return "\n".join(lines)


def main():
    print("🔍 Verifying papers via Semantic Scholar API...\n")
    results = run_verification()
    report = generate_report(results)
    print("\n" + report)

    # Save
    out = Path("docs/papers/00-AUTO-VERIFICATION.md")
    out.write_text(report)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
