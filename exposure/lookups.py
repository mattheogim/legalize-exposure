"""Rule-based classification lookups (Labeling Functions LF1 & LF2).

These are the anchor rules — the backbone of initial classification.
No ML, no LLM. Just documented, reproducible mappings.

LF1: Agency → Industry (NAICS codes)
LF2: CFR Title → Industry (NAICS codes)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndustryMatch:
    """A matched industry with confidence and provenance."""
    naics_code: str
    naics_title: str
    confidence: float
    provenance: str         # why this match exists
    gics_sector: str = ""   # cross-reference for ETF mapping
    gics_code: str = ""


# ── LF1: Agency → Industry ──────────────────────────────────────────────

# Federal Register agency slugs → primary affected NAICS codes
# Sources:
#   - Agency mission statements
#   - Historical regulatory scope
#   - CFR title jurisdiction

_AGENCY_MAP: dict[str, list[dict]] = {
    # ── Energy / Environment ──
    "environmental-protection-agency": [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
        {"naics": "322", "title": "Paper Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "324", "title": "Petroleum and Coal Products", "gics": "Energy", "gics_code": "10"},
        {"naics": "325", "title": "Chemical Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "562", "title": "Waste Management", "gics": "Industrials", "gics_code": "20"},
    ],
    "department-of-energy": [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
        {"naics": "324", "title": "Petroleum and Coal Products", "gics": "Energy", "gics_code": "10"},
        {"naics": "333", "title": "Machinery Manufacturing", "gics": "Industrials", "gics_code": "20"},
    ],

    # ── Healthcare ──
    "food-and-drug-administration": [
        {"naics": "3254", "title": "Pharmaceutical Manufacturing", "gics": "Health Care", "gics_code": "35"},
        {"naics": "3391", "title": "Medical Equipment", "gics": "Health Care", "gics_code": "35"},
        {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "312", "title": "Beverage and Tobacco", "gics": "Consumer Staples", "gics_code": "30"},
    ],
    "department-of-health-and-human-services": [
        {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "622", "title": "Hospitals", "gics": "Health Care", "gics_code": "35"},
        {"naics": "623", "title": "Nursing/Residential Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "524", "title": "Insurance Carriers", "gics": "Financials", "gics_code": "40"},
    ],

    # ── Financial ──
    "securities-and-exchange-commission": [
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "525", "title": "Funds, Trusts, Financial Vehicles", "gics": "Financials", "gics_code": "40"},
    ],
    "consumer-financial-protection-bureau": [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "5223", "title": "Activities Related to Credit", "gics": "Financials", "gics_code": "40"},
        {"naics": "524", "title": "Insurance Carriers", "gics": "Financials", "gics_code": "40"},
    ],
    "department-of-the-treasury": [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
    ],
    "internal-revenue-service": [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
        {"naics": "541", "title": "Professional Services", "gics": "Industrials", "gics_code": "20"},
    ],

    # ── Technology / Communications ──
    "federal-communications-commission": [
        {"naics": "517", "title": "Telecommunications", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "515", "title": "Broadcasting", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
    ],
    "federal-trade-commission": [
        {"naics": "454", "title": "Nonstore Retailers (e-commerce)", "gics": "Consumer Discretionary", "gics_code": "25"},
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "519", "title": "Web Search / Data Services", "gics": "Communication Services", "gics_code": "50"},
    ],

    # ── Labor / Industrial ──
    "department-of-labor": [
        {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        {"naics": "238", "title": "Specialty Trade Contractors", "gics": "Industrials", "gics_code": "20"},
        {"naics": "331", "title": "Primary Metal Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "332", "title": "Fabricated Metal Products", "gics": "Industrials", "gics_code": "20"},
    ],
    "department-of-transportation": [
        {"naics": "481", "title": "Air Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "482", "title": "Rail Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "483", "title": "Water Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "484", "title": "Truck Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "3361", "title": "Motor Vehicle Manufacturing", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],

    # ── Homeland Security / Defense ──
    "department-of-homeland-security": [
        {"naics": "561", "title": "Administrative/Support Services", "gics": "Industrials", "gics_code": "20"},
        {"naics": "928", "title": "National Security", "gics": "Industrials", "gics_code": "20"},
        {"naics": "5415", "title": "Computer Systems Design", "gics": "Information Technology", "gics_code": "45"},
    ],

    # ── Education ──
    "department-of-education": [
        {"naics": "611", "title": "Educational Services", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],

    # ── Justice ──
    "department-of-justice": [
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "519", "title": "Web Search / Data Services", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "3391", "title": "Medical Equipment", "gics": "Health Care", "gics_code": "35"},
    ],

    # ── Agriculture ──
    "department-of-agriculture": [
        {"naics": "111", "title": "Crop Production", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "112", "title": "Animal Production/Aquaculture", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "113", "title": "Forestry and Logging", "gics": "Materials", "gics_code": "15"},
        {"naics": "115", "title": "Support Activities for Agriculture", "gics": "Consumer Staples", "gics_code": "30"},
    ],

    # ── Defense ──
    "department-of-defense": [
        {"naics": "3364", "title": "Aerospace Product Manufacturing", "gics": "Industrials", "gics_code": "20"},
        {"naics": "928", "title": "National Security", "gics": "Industrials", "gics_code": "20"},
        {"naics": "334", "title": "Computer/Electronic Products", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "5415", "title": "Computer Systems Design", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "332", "title": "Fabricated Metal Products", "gics": "Industrials", "gics_code": "20"},
    ],

    # ── Interior ──
    "department-of-the-interior": [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
        {"naics": "113", "title": "Forestry and Logging", "gics": "Materials", "gics_code": "15"},
        {"naics": "114", "title": "Fishing/Hunting/Trapping", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "721", "title": "Accommodation (National Parks)", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],

    # ── Commerce ──
    "department-of-commerce": [
        {"naics": "334", "title": "Computer/Electronic Products", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "517", "title": "Telecommunications", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "5417", "title": "Scientific R&D Services", "gics": "Health Care", "gics_code": "35"},
        {"naics": "331", "title": "Primary Metal Manufacturing", "gics": "Materials", "gics_code": "15"},
    ],

    # ── Housing and Urban Development ──
    "department-of-housing-and-urban-development": [
        {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        {"naics": "531", "title": "Real Estate", "gics": "Real Estate", "gics_code": "60"},
        {"naics": "522", "title": "Credit Intermediation (Mortgage)", "gics": "Financials", "gics_code": "40"},
        {"naics": "524", "title": "Insurance Carriers (Mortgage Insurance)", "gics": "Financials", "gics_code": "40"},
    ],

    # ── Veterans Affairs ──
    "department-of-veterans-affairs": [
        {"naics": "622", "title": "Hospitals (VA Medical)", "gics": "Health Care", "gics_code": "35"},
        {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "3254", "title": "Pharmaceutical Manufacturing", "gics": "Health Care", "gics_code": "35"},
        {"naics": "3391", "title": "Medical Equipment", "gics": "Health Care", "gics_code": "35"},
    ],

    # ── Sub-agencies (high Federal Register volume) ──

    "federal-aviation-administration": [
        {"naics": "481", "title": "Air Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "3364", "title": "Aerospace Product Manufacturing", "gics": "Industrials", "gics_code": "20"},
        {"naics": "4881", "title": "Support Activities for Air Transport", "gics": "Industrials", "gics_code": "20"},
    ],
    "occupational-safety-and-health-administration": [
        {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        {"naics": "238", "title": "Specialty Trade Contractors", "gics": "Industrials", "gics_code": "20"},
        {"naics": "331", "title": "Primary Metal Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "332", "title": "Fabricated Metal Products", "gics": "Industrials", "gics_code": "20"},
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
    ],
    "centers-for-medicare-and-medicaid-services": [
        {"naics": "622", "title": "Hospitals", "gics": "Health Care", "gics_code": "35"},
        {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "623", "title": "Nursing/Residential Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "524", "title": "Insurance Carriers (Health)", "gics": "Financials", "gics_code": "40"},
        {"naics": "3254", "title": "Pharmaceutical Manufacturing", "gics": "Health Care", "gics_code": "35"},
    ],
    "federal-deposit-insurance-corporation": [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "5223", "title": "Activities Related to Credit", "gics": "Financials", "gics_code": "40"},
    ],
    "commodity-futures-trading-commission": [
        {"naics": "523", "title": "Securities/Commodity Contracts", "gics": "Financials", "gics_code": "40"},
        {"naics": "525", "title": "Funds, Trusts, Financial Vehicles", "gics": "Financials", "gics_code": "40"},
    ],
    "nuclear-regulatory-commission": [
        {"naics": "2211", "title": "Electric Power Generation (Nuclear)", "gics": "Utilities", "gics_code": "55"},
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
        {"naics": "562", "title": "Waste Management (Nuclear Waste)", "gics": "Industrials", "gics_code": "20"},
    ],
    "national-highway-traffic-safety-administration": [
        {"naics": "3361", "title": "Motor Vehicle Manufacturing", "gics": "Consumer Discretionary", "gics_code": "25"},
        {"naics": "484", "title": "Truck Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "441", "title": "Motor Vehicle Dealers", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],
    "pipeline-and-hazardous-materials-safety-administration": [
        {"naics": "486", "title": "Pipeline Transportation", "gics": "Energy", "gics_code": "10"},
        {"naics": "484", "title": "Truck Transportation (hazmat)", "gics": "Industrials", "gics_code": "20"},
        {"naics": "324", "title": "Petroleum/Coal Products", "gics": "Energy", "gics_code": "10"},
    ],
    "bureau-of-land-management": [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
        {"naics": "113", "title": "Forestry and Logging", "gics": "Materials", "gics_code": "15"},
    ],
    "fish-and-wildlife-service": [
        {"naics": "114", "title": "Fishing/Hunting/Trapping", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "112", "title": "Animal Production", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "721", "title": "Accommodation (Wildlife Tourism)", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],
}


# ── Agency slug aliases ─────────────────────────────────────────────────
# The Federal Register API uses different slug formats depending on context.
# This maps alternative slugs to canonical slugs used in _AGENCY_MAP.

_AGENCY_ALIASES: dict[str, str] = {
    # "{name}-department" ↔ "department-of-{name}" variants
    "transportation-department": "department-of-transportation",
    "treasury-department": "department-of-the-treasury",
    "agriculture-department": "department-of-agriculture",
    "commerce-department": "department-of-commerce",
    "defense-department": "department-of-defense",
    "education-department": "department-of-education",
    "energy-department": "department-of-energy",
    "interior-department": "department-of-the-interior",
    "justice-department": "department-of-justice",
    "labor-department": "department-of-labor",
    "homeland-security-department": "department-of-homeland-security",
    "health-and-human-services-department": "department-of-health-and-human-services",
    "housing-and-urban-development-department": "department-of-housing-and-urban-development",
    "veterans-affairs-department": "department-of-veterans-affairs",
    # Sub-agencies and independent agencies
    "federal-reserve-system": "department-of-the-treasury",  # monetary policy → financial
    "national-credit-union-administration": "federal-deposit-insurance-corporation",  # credit unions ≈ banking
    "farm-credit-administration": "department-of-agriculture",  # farm credit ≈ agriculture
    "pension-benefit-guaranty-corporation": "department-of-labor",  # pensions ≈ labor
    "financial-stability-oversight-council": "department-of-the-treasury",  # FSOC ≈ Treasury
    "office-of-the-national-cyber-director": "department-of-homeland-security",  # cyber ≈ DHS
    "consumer-product-safety-commission": "federal-trade-commission",  # CPSC ≈ FTC (consumer safety)
}


# ── LF2: CFR Title → Industry ───────────────────────────────────────────

# Code of Federal Regulations titles → primary affected industries
# Source: https://www.ecfr.gov/

_CFR_TITLE_MAP: dict[int, list[dict]] = {
    # Title 7: Agriculture
    7: [
        {"naics": "111", "title": "Crop Production", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "112", "title": "Animal Production", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
    ],
    # Title 10: Energy
    10: [
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
    ],
    # Title 12: Banks and Banking
    12: [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 14: Aeronautics and Space
    14: [
        {"naics": "3364", "title": "Aerospace Manufacturing", "gics": "Industrials", "gics_code": "20"},
        {"naics": "481", "title": "Air Transportation", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 17: Commodity and Securities Exchanges
    17: [
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 21: Food and Drugs
    21: [
        {"naics": "3254", "title": "Pharmaceutical Manufacturing", "gics": "Health Care", "gics_code": "35"},
        {"naics": "3391", "title": "Medical Equipment", "gics": "Health Care", "gics_code": "35"},
        {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
    ],
    # Title 26: Internal Revenue
    26: [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "541", "title": "Professional Services", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 29: Labor
    29: [
        {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        {"naics": "331", "title": "Primary Metal Manufacturing", "gics": "Materials", "gics_code": "15"},
    ],
    # Title 30: Mineral Resources
    30: [
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
    ],
    # Title 33: Navigation and Navigable Waters
    33: [
        {"naics": "483", "title": "Water Transportation", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 40: Protection of Environment
    40: [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
        {"naics": "324", "title": "Petroleum and Coal Products", "gics": "Energy", "gics_code": "10"},
        {"naics": "325", "title": "Chemical Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "562", "title": "Waste Management", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 42: Public Health
    42: [
        {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
        {"naics": "622", "title": "Hospitals", "gics": "Health Care", "gics_code": "35"},
        {"naics": "524", "title": "Insurance Carriers", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 47: Telecommunication
    47: [
        {"naics": "517", "title": "Telecommunications", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "515", "title": "Broadcasting", "gics": "Communication Services", "gics_code": "50"},
    ],
    # Title 49: Transportation
    49: [
        {"naics": "481", "title": "Air Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "482", "title": "Rail Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "484", "title": "Truck Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "3361", "title": "Motor Vehicle Manufacturing", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],
    # Title 9: Animals and Animal Products
    9: [
        {"naics": "112", "title": "Animal Production/Aquaculture", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "311", "title": "Food Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "114", "title": "Fishing/Hunting/Trapping", "gics": "Consumer Staples", "gics_code": "30"},
    ],
    # Title 15: Commerce and Foreign Trade
    15: [
        {"naics": "334", "title": "Computer/Electronic Products", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "331", "title": "Primary Metal Manufacturing", "gics": "Materials", "gics_code": "15"},
        {"naics": "517", "title": "Telecommunications", "gics": "Communication Services", "gics_code": "50"},
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
    ],
    # Title 16: Commercial Practices (FTC)
    16: [
        {"naics": "454", "title": "Nonstore Retailers (e-commerce)", "gics": "Consumer Discretionary", "gics_code": "25"},
        {"naics": "518", "title": "Data Processing / Internet", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "522", "title": "Credit Intermediation", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 18: Conservation of Power and Water Resources
    18: [
        {"naics": "2211", "title": "Electric Power Generation", "gics": "Utilities", "gics_code": "55"},
        {"naics": "2213", "title": "Water/Sewage Systems", "gics": "Utilities", "gics_code": "55"},
        {"naics": "221", "title": "Utilities", "gics": "Utilities", "gics_code": "55"},
    ],
    # Title 24: Housing and Urban Development
    24: [
        {"naics": "236", "title": "Construction of Buildings", "gics": "Industrials", "gics_code": "20"},
        {"naics": "531", "title": "Real Estate", "gics": "Real Estate", "gics_code": "60"},
        {"naics": "522", "title": "Credit Intermediation (Mortgage)", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 27: Alcohol, Tobacco Products and Firearms
    27: [
        {"naics": "312", "title": "Beverage and Tobacco Manufacturing", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "332", "title": "Fabricated Metal Products (Firearms)", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 31: Money and Finance: Treasury
    31: [
        {"naics": "522", "title": "Credit Intermediation (Banking)", "gics": "Financials", "gics_code": "40"},
        {"naics": "523", "title": "Securities and Investments", "gics": "Financials", "gics_code": "40"},
        {"naics": "525", "title": "Funds, Trusts, Financial Vehicles", "gics": "Financials", "gics_code": "40"},
    ],
    # Title 32: National Defense
    32: [
        {"naics": "3364", "title": "Aerospace Product Manufacturing", "gics": "Industrials", "gics_code": "20"},
        {"naics": "928", "title": "National Security", "gics": "Industrials", "gics_code": "20"},
        {"naics": "334", "title": "Computer/Electronic Products", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "5415", "title": "Computer Systems Design", "gics": "Information Technology", "gics_code": "45"},
    ],
    # Title 34: Education
    34: [
        {"naics": "611", "title": "Educational Services", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],
    # Title 36: Parks, Forests, and Public Property
    36: [
        {"naics": "113", "title": "Forestry and Logging", "gics": "Materials", "gics_code": "15"},
        {"naics": "721", "title": "Accommodation (Parks/Tourism)", "gics": "Consumer Discretionary", "gics_code": "25"},
    ],
    # Title 38: Pensions, Bonuses, and Veterans' Relief
    38: [
        {"naics": "622", "title": "Hospitals (VA)", "gics": "Health Care", "gics_code": "35"},
        {"naics": "524", "title": "Insurance Carriers (Veterans Benefits)", "gics": "Financials", "gics_code": "40"},
        {"naics": "621", "title": "Ambulatory Health Care", "gics": "Health Care", "gics_code": "35"},
    ],
    # Title 43: Public Lands: Interior
    43: [
        {"naics": "211", "title": "Oil and Gas Extraction", "gics": "Energy", "gics_code": "10"},
        {"naics": "212", "title": "Mining (except Oil and Gas)", "gics": "Materials", "gics_code": "15"},
        {"naics": "113", "title": "Forestry and Logging", "gics": "Materials", "gics_code": "15"},
    ],
    # Title 46: Shipping
    46: [
        {"naics": "483", "title": "Water Transportation", "gics": "Industrials", "gics_code": "20"},
        {"naics": "488", "title": "Support Activities for Transportation", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 48: Federal Acquisition Regulations
    48: [
        {"naics": "3364", "title": "Aerospace Product Manufacturing", "gics": "Industrials", "gics_code": "20"},
        {"naics": "5415", "title": "Computer Systems Design", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "334", "title": "Computer/Electronic Products", "gics": "Information Technology", "gics_code": "45"},
        {"naics": "928", "title": "National Security", "gics": "Industrials", "gics_code": "20"},
    ],
    # Title 50: Wildlife and Fisheries
    50: [
        {"naics": "114", "title": "Fishing/Hunting/Trapping", "gics": "Consumer Staples", "gics_code": "30"},
        {"naics": "112", "title": "Animal Production", "gics": "Consumer Staples", "gics_code": "30"},
    ],
}


# ── Lookup Classes ──────────────────────────────────────────────────────

class AgencyLookup:
    """LF1: Agency slug → affected industries.

    Usage:
        lookup = AgencyLookup()
        matches = lookup.match("environmental-protection-agency")
        # → [IndustryMatch(naics="211", ...), ...]
    """

    def __init__(self):
        self._map = _AGENCY_MAP

    def match(self, agency_slug: str) -> list[IndustryMatch]:
        """Return industry matches for a Federal Register agency slug.

        Resolves aliases automatically (e.g., "treasury-department" →
        "department-of-the-treasury").
        """
        # Resolve alias if needed.
        canonical = _AGENCY_ALIASES.get(agency_slug, agency_slug)
        entries = self._map.get(canonical, [])
        return [
            IndustryMatch(
                naics_code=e["naics"],
                naics_title=e["title"],
                confidence=0.6,     # agency match is medium confidence
                provenance=f"Agency mapping: {agency_slug} → NAICS {e['naics']}",
                gics_sector=e.get("gics", ""),
                gics_code=e.get("gics_code", ""),
            )
            for e in entries
        ]

    def all_agencies(self) -> list[str]:
        """List all mapped agency slugs."""
        return list(self._map.keys())

    def has_agency(self, agency_slug: str) -> bool:
        return agency_slug in self._map


class CFRLookup:
    """LF2: CFR title number → affected industries.

    Usage:
        lookup = CFRLookup()
        matches = lookup.match(40)  # Title 40: Environment
        # → [IndustryMatch(naics="211", ...), ...]
    """

    def __init__(self):
        self._map = _CFR_TITLE_MAP

    def match(self, cfr_title: int) -> list[IndustryMatch]:
        """Return industry matches for a CFR title number."""
        entries = self._map.get(cfr_title, [])
        return [
            IndustryMatch(
                naics_code=e["naics"],
                naics_title=e["title"],
                confidence=0.7,     # CFR title is higher confidence than agency
                provenance=f"CFR Title {cfr_title} → NAICS {e['naics']}",
                gics_sector=e.get("gics", ""),
                gics_code=e.get("gics_code", ""),
            )
            for e in entries
        ]

    def match_from_cite(self, cfr_cite: str) -> list[IndustryMatch]:
        """Extract CFR title from a citation string and match.

        Accepts formats like "40 CFR 60", "40 CFR Part 60.112a", etc.
        """
        import re
        m = re.match(r"(\d+)\s*CFR", cfr_cite.strip())
        if m:
            return self.match(int(m.group(1)))
        return []

    def all_titles(self) -> list[int]:
        """List all mapped CFR titles."""
        return sorted(self._map.keys())

    def has_title(self, cfr_title: int) -> bool:
        return cfr_title in self._map
