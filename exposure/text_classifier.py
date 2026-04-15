"""Text-based NAICS classification (LF3+).

Supplements Agency→NAICS lookup (LF1) and CFR→NAICS lookup (LF2) with
keyword-based classification from regulation titles and abstracts.

Approach: Armstrong et al. (2025) — simple dictionary methods work as
well as GPT for measuring regulatory exposure. [src:armstrong-2025]

Two functions:
1. classify_from_title() — keyword matching on regulation title
2. narrow_dot_mapping() — reduce DOT over-mapping based on sub-agency keywords
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from exposure.lookups import IndustryMatch


# ── Keyword → NAICS dictionaries ────────────────────────────────────────
# Each entry: keyword pattern → (NAICS codes to ADD, NAICS codes to REMOVE)

_TITLE_KEYWORDS: list[tuple[str, list[dict], list[str]]] = [
    # Aviation / Aerospace
    (
        r"airworth|airspace|aviation|aircraft|airplane|helicopter|flight|pilot|faa|airport",
        [
            {"naics": "481", "title": "Air Transportation", "gics": "Industrials", "gics_code": "20"},
            {"naics": "3364", "title": "Aerospace Manufacturing", "gics": "Industrials", "gics_code": "20"},
            {"naics": "4881", "title": "Support Activities for Air Transport", "gics": "Industrials", "gics_code": "20"},
        ],
        ["482", "483", "484"],  # Remove rail, water, truck if aviation-specific
    ),

    # Marine / Coast Guard
    (
        r"vessel|marine|coast guard|navigation|waterway|port safety|shipping|maritime",
        [
            {"naics": "483", "title": "Water Transportation", "gics": "Industrials", "gics_code": "20"},
        ],
        ["481", "482", "484", "3364"],  # Remove air, rail, truck, aerospace
    ),

    # Highway / Motor Vehicle
    (
        r"motor vehicle|highway|truck|crash|tire|fuel economy|automobile|nhtsa|seat belt|airbag",
        [
            {"naics": "3361", "title": "Motor Vehicle Manufacturing", "gics": "Consumer Discretionary", "gics_code": "25"},
            {"naics": "484", "title": "Truck Transportation", "gics": "Industrials", "gics_code": "20"},
            {"naics": "441", "title": "Motor Vehicle Dealers", "gics": "Consumer Discretionary", "gics_code": "25"},
        ],
        ["481", "482", "483", "3364"],  # Remove air, rail, water, aerospace
    ),

    # Rail
    (
        r"railroad|rail safety|locomotive|freight rail|passenger rail|amtrak",
        [
            {"naics": "482", "title": "Rail Transportation", "gics": "Industrials", "gics_code": "20"},
        ],
        ["481", "483", "484", "3364"],  # Remove air, water, truck, aerospace
    ),

    # Pipeline / Hazmat
    (
        r"pipeline|hazardous material|hazmat|phmsa",
        [
            {"naics": "486", "title": "Pipeline Transportation", "gics": "Energy", "gics_code": "10"},
            {"naics": "324", "title": "Petroleum/Coal Products", "gics": "Energy", "gics_code": "10"},
        ],
        ["481", "482", "483", "3364"],  # Remove air, rail, water, aerospace
    ),

    # Pharmaceutical / Drug
    (
        r"drug|pharmaceutical|medication|prescription|opioid|vaccine|biosimilar|generic drug",
        [
            {"naics": "3254", "title": "Pharmaceutical Manufacturing", "gics": "Health Care", "gics_code": "35"},
        ],
        [],
    ),

    # Medical Device
    (
        r"medical device|implant|diagnostic|reclassification.*device|prosthe",
        [
            {"naics": "3391", "title": "Medical Equipment", "gics": "Health Care", "gics_code": "35"},
        ],
        [],
    ),

    # Food Safety
    (
        r"food safety|food labeling|dietary|nutrition|import.*food|adulterat",
        [
            {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        ],
        [],
    ),

    # Tobacco / E-cigarette
    (
        r"tobacco|cigarette|nicotine|vaping|e-cigarette|pmta",
        [
            {"naics": "3122", "title": "Tobacco Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        ],
        [],
    ),

    # Banking specific
    (
        r"bank|depository|lending|mortgage|credit union|fdic|occ|capital requirement",
        [
            {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        ],
        [],
    ),

    # Securities / Investment
    (
        r"securities|investment advis|broker.dealer|mutual fund|etf|exchange.traded|custody|clearing",
        [
            {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
        ],
        [],
    ),

    # Insurance
    (
        r"insurance|actuarial|underwriting|policyholder|annuity",
        [
            {"naics": "524", "title": "Insurance Carriers", "gics": "Financials", "gics_code": "40"},
        ],
        [],
    ),

    # Nuclear
    (
        r"nuclear|spent fuel|reactor|nrc|uranium|radioactive",
        [
            {"naics": "2211", "title": "Electric Power Generation (Nuclear)", "gics": "Utilities", "gics_code": "55"},
        ],
        [],
    ),

    # Oil & Gas specific
    (
        r"oil.*gas|petroleum|drilling|offshore.*energy|fracking|lng|crude",
        [
            {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        ],
        [],
    ),

    # Mining
    (
        r"mining|mineral|coal mine|msha|surface mining",
        [
            {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
        ],
        [],
    ),

    # Telecom
    (
        r"spectrum|broadcast|telecom|wireless|broadband|5g|satellite",
        [
            {"naics": "517", "title": "Telecommunications", "gics": "Communication Services", "gics_code": "50"},
        ],
        [],
    ),

    # Fisheries / Wildlife
    (
        r"fisher|fish|marine mammal|endangered species|wildlife|sea otter|whale",
        [
            {"naics": "114", "title": "Fishing/Hunting/Trapping", "gics": "Consumer Staples", "gics_code": "30"},
        ],
        [],
    ),

    # Agriculture / Animal
    (
        r"cattle|poultry|livestock|animal.*health|veterinar|grain|crop|import.*animal|horse",
        [
            {"naics": "112", "title": "Animal Production", "gics": "Consumer Staples", "gics_code": "30"},
        ],
        [],
    ),

    # Medicare / Medicaid / Health programs
    (
        r"medicare|medicaid|cms|hospice|hospital.*payment|drg|physician fee",
        [
            {"naics": "622", "title": "Hospitals", "gics": "Health Care", "gics_code": "35"},
            {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
            {"naics": "524", "title": "Insurance Carriers (Health)", "gics": "Financials", "gics_code": "40"},
        ],
        [],
    ),

    # Housing / Real Estate
    (
        r"housing|mortgage|hud|fair housing|rent|landlord|fha",
        [
            {"naics": "531", "title": "Real Estate", "gics": "Real Estate", "gics_code": "60"},
            {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        ],
        [],
    ),

    # Cybersecurity
    (
        r"cyber|data breach|privacy|information security|encryption",
        [
            {"naics": "5415", "title": "Computer Systems Design", "gics": "Information Technology", "gics_code": "45"},
            {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
        ],
        [],
    ),
]


def classify_from_title(title: str) -> tuple[list[IndustryMatch], set[str]]:
    """Classify regulation by matching title keywords to NAICS codes.

    Returns:
        (matches, naics_to_remove) — matches to ADD, NAICS prefixes to REMOVE
        from the agency-level mapping.
    """
    title_lower = title.lower()
    all_matches: list[IndustryMatch] = []
    all_removals: set[str] = set()

    for pattern, add_entries, remove_codes in _TITLE_KEYWORDS:
        if re.search(pattern, title_lower):
            for e in add_entries:
                all_matches.append(IndustryMatch(
                    naics_code=e["naics"],
                    naics_title=e["title"],
                    confidence=0.75,  # title keyword match = higher than agency (0.6)
                    provenance=f"Title keyword: '{pattern[:30]}...' → NAICS {e['naics']}",
                    gics_sector=e.get("gics", ""),
                    gics_code=e.get("gics_code", ""),
                ))
            all_removals.update(remove_codes)

    return all_matches, all_removals


def refine_mapping(
    agency_matches: list[IndustryMatch],
    title: str,
) -> list[IndustryMatch]:
    """Refine agency-level matches using title keywords.

    1. Run title classification → get adds + removes
    2. Remove over-broad agency matches (e.g., DOT → all transport)
    3. Add specific matches from title (e.g., "airworthiness" → aviation only)
    4. Deduplicate by NAICS code (keep highest confidence)
    """
    title_matches, removals = classify_from_title(title)

    # If no title matches, keep agency matches as-is.
    if not title_matches:
        return agency_matches

    # Filter out over-broad agency matches.
    filtered = []
    for m in agency_matches:
        naics_prefix = m.naics_code[:3]
        if naics_prefix not in removals:
            filtered.append(m)

    # Combine filtered agency matches + title matches.
    combined = filtered + title_matches

    # Deduplicate: keep highest confidence per NAICS prefix.
    by_naics: dict[str, IndustryMatch] = {}
    for m in combined:
        key = m.naics_code[:3]
        if key not in by_naics or m.confidence > by_naics[key].confidence:
            by_naics[key] = m

    return list(by_naics.values())
