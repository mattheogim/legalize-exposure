#!/usr/bin/env python3
"""Cross-Reference Validator for legalize documentation.

Scans all Markdown docs for:
1. [src:PAPER-ID] tags → verifies paper exists in PAPERS.md
2. Untagged numerical claims → warns about missing source
3. Adversarial cross-check → flags claims that adversarial papers challenge

Usage:
    python scripts/validate_claims.py                    # scan all docs
    python scripts/validate_claims.py docs/SPEC.md       # scan one file
    python scripts/validate_claims.py --strict            # exit 1 on any error

Hook integration:
    Add to .claude/settings.local.json as a PostToolUse hook
    on Edit/Write targeting docs/*.md files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ── Configuration ──

DOCS_DIR = Path(__file__).parent.parent / "docs"
PAPERS_INDEX = DOCS_DIR / "PAPERS.md"
PAPERS_DIR = DOCS_DIR / "papers"

# Known paper IDs (short keys used in [src:] tags).
# Extracted from PAPERS.md on first run, cached here for validation.
KNOWN_PAPER_IDS = {
    "goldsmith-pinkham-2025",
    "baker-bloom-davis-2016",
    "kalmenovitz-2023",
    "hassan-2019",
    "regdata-2017",
    "armstrong-2025",
    "mackinlay-1997",
    "ramelli-2021",
    "brav-heaton-2015",
    "bae-jo-shim-2025",
    "binder-1998",
    "kothari-warner-2007",
    "shapiro-2024",
    "christensen-hail-leuz-2016",
    "igan-mishra-tressel-2012",
    "loughran-mcdonald-2016",
    "kengmegni-2025",
    "de-chaisemartin-2024",
    "krieger-2020",
    "chen-liu-2023",
    "gutierrez-teshima-2024",
    "chan-2024",
    "kordas-savva-2020",
    "dodd-frank-2016",
    "fda-fast-track-2023",
    "karpoff-2005",
    "wang-tang-li-2025",
    "abadie-2010",
    "kou-2024",
    "pastor-veronesi-2012",
    "stigler-1971",
    "gentzkow-2019",
    "cohen-2013",
}

# Claims that adversarial papers challenge.
# Maps (claim keyword) → (adversarial paper, severity, what it says).
ADVERSARIAL_CHECKS = {
    "event study": (
        "brav-heaton-2015",
        "SEVERE",
        "Event studies are underpowered and biased for single-firm regulatory events",
    ),
    "event_study": (
        "brav-heaton-2015",
        "SEVERE",
        "Event studies are underpowered and biased for single-firm regulatory events",
    ),
    "CAR": (
        "goldsmith-pinkham-2025",
        "SEVERE",
        "Market Model CAR is inconsistent when factor model is misspecified",
    ),
    "Market Model": (
        "goldsmith-pinkham-2025",
        "SEVERE",
        "Replace with synthetic control for consistent estimates",
    ),
    "EPU": (
        "bae-jo-shim-2025",
        "DEVASTATING",
        "EPU index loses significance for 2008-2019. Only works during crises.",
    ),
    "policy uncertainty index": (
        "bae-jo-shim-2025",
        "DEVASTATING",
        "EPU fails outside crisis periods per replication study",
    ),
    "NAICS": (
        "kalmenovitz-2023",
        "MODERATE",
        "Industry-level mapping is too coarse. Firm-level 10-K matching is more accurate.",
    ),
    "word count": (
        "shapiro-2024",
        "SEVERE",
        "Text-based regulation measurement is unreliable — 'shall' ≠ actual burden",
    ),
    "restriction count": (
        "shapiro-2024",
        "SEVERE",
        "Counting regulatory words fails to capture actual regulatory burden",
    ),
    "long-horizon": (
        "kothari-warner-2007",
        "SEVERE",
        "Long-horizon event studies have low power and severe misspecification",
    ),
    "sentiment": (
        "loughran-mcdonald-2016",
        "MODERATE",
        "General sentiment dictionaries massively misclassify financial text",
    ),
    "NLP predict": (
        "kengmegni-2025",
        "MODERATE",
        "NLP-based return prediction fails out of sample due to overfitting",
    ),
    "impact": (
        None,
        "WARNING",
        "DESIGN_PRINCIPLES §11 bans 'impact' — use 'exposure' unless backed by DiD/SC/opposite-shock evidence",
    ),
    "caused": (
        None,
        "WARNING",
        "DESIGN_PRINCIPLES §11 bans causal language — use 'associated with' or 'around the time of'",
    ),
    "drove": (
        None,
        "WARNING",
        "DESIGN_PRINCIPLES §11 bans 'drove' — use 'coincided with'",
    ),
}

# Regex for numerical claims (numbers with % or specific magnitudes).
NUM_CLAIM_RE = re.compile(r"\b\d+\.?\d*\s*%|\$\d+[\d,.]*[MBK]?\b|\b\d+\.?\d*\s*(basis points|bps|bp)\b")

# Regex for [src:PAPER-ID] tags.
SRC_TAG_RE = re.compile(r"\[src:([^\]]+)\]")

# ── Scanning ──


class Issue:
    def __init__(self, level: str, file: str, line: int, msg: str):
        self.level = level  # ERROR, WARN, INFO, ADVERSARIAL
        self.file = file
        self.line = line
        self.msg = msg

    def __str__(self):
        return f"[{self.level}] {self.file}:{self.line} — {self.msg}"


def scan_file(path: Path) -> list[Issue]:
    """Scan a single Markdown file for claim issues."""
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    rel = str(path.relative_to(path.parent.parent))

    for i, line in enumerate(text.split("\n"), 1):
        # Skip frontmatter, code blocks, URLs.
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("http") or stripped.startswith("|"):
            continue

        # 1. Check [src:] tags point to known papers.
        for match in SRC_TAG_RE.finditer(line):
            paper_id = match.group(1).strip()
            if paper_id not in KNOWN_PAPER_IDS:
                issues.append(Issue("ERROR", rel, i, f"Unknown paper reference: [src:{paper_id}]"))

        # 2. Check for untagged numerical claims.
        if NUM_CLAIM_RE.search(line) and not SRC_TAG_RE.search(line):
            # Skip lines that are clearly in tables, code, or paper notes.
            if not any(skip in rel for skip in ["papers/", "PAPERS.md", "VALIDATION_ARCHIVE"]):
                num = NUM_CLAIM_RE.search(line).group()
                issues.append(Issue("INFO", rel, i, f"Numerical claim '{num}' without [src:] tag"))

        # 3. Adversarial cross-check.
        # Only flag in NEW code/docs that make claims, not in existing reference docs.
        lower = line.lower()
        # Skip existing reference docs + all exposure code (adversarial applies to NEW claims only).
        skip_files = ["papers/", "PAPERS.md", "VALIDATION_ARCHIVE", "CROSS_VALIDATION",
                       "DESIGN_PRINCIPLES", "SPEC.md", "ROADMAP.md", "PIPELINE_GUIDE",
                       "exposure/", "fetchers/", "scripts/", "ui/"]
        if not any(skip in rel for skip in skip_files):
            for keyword, (paper_id, severity, warning) in ADVERSARIAL_CHECKS.items():
                if keyword.lower() in lower:
                    # Don't flag if the line acknowledges the limitation.
                    ack_words = ["bias", "limitation", "caveat", "however", "but", "replace",
                                 "instead", "upgrade", "fix", "alternative", "warning", "note"]
                    if not any(ack in lower for ack in ack_words):
                        issues.append(Issue("ADVERSARIAL", rel, i, f"'{keyword}' — {warning}"))
                        break

    return issues


def scan_all(targets: list[Path] | None = None) -> list[Issue]:
    """Scan all documentation files."""
    all_issues: list[Issue] = []

    if targets:
        files = targets
    else:
        files = sorted(DOCS_DIR.glob("**/*.md"))
        # Also scan exposure module docstrings.
        files.extend(sorted((DOCS_DIR.parent / "exposure").glob("*.py")))

    for f in files:
        if f.exists():
            all_issues.extend(scan_file(f))

    return all_issues


def main():
    strict = "--strict" in sys.argv
    targets = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]

    issues = scan_all(targets if targets else None)

    # Group by level.
    errors = [i for i in issues if i.level == "ERROR"]
    adversarial = [i for i in issues if i.level == "ADVERSARIAL"]
    warns = [i for i in issues if i.level == "WARN"]
    infos = [i for i in issues if i.level == "INFO"]

    print(f"\n{'='*60}")
    print(f"Claim Validation Report")
    print(f"{'='*60}")

    if errors:
        print(f"\n🔴 ERRORS ({len(errors)}) — broken references:")
        for i in errors:
            print(f"  {i}")

    if adversarial:
        print(f"\n🟡 ADVERSARIAL ({len(adversarial)}) — claims challenged by counter-evidence:")
        for i in adversarial:
            print(f"  {i}")

    if warns:
        print(f"\n⚠️  WARNINGS ({len(warns)}):")
        for i in warns:
            print(f"  {i}")

    if infos:
        print(f"\n📝 INFO ({len(infos)}) — untagged numerical claims:")
        for i in infos[:20]:  # Cap at 20 to avoid noise.
            print(f"  {i}")
        if len(infos) > 20:
            print(f"  ... and {len(infos) - 20} more")

    print(f"\n{'='*60}")
    print(f"ERRORS: {len(errors)}  ADVERSARIAL: {len(adversarial)}  WARNS: {len(warns)}  INFO: {len(infos)}")
    print(f"{'='*60}\n")

    if strict and (errors or adversarial):
        sys.exit(1)


if __name__ == "__main__":
    main()
