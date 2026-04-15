"""ETF Holdings-based Exposure Engine.

Design principle §9: ETFs are connected via holdings, not sector labels.

    exposure_score = Σ(weight_i × revenue_share_in_industry_i)

For MVP, we use a simplified approach:
    - Static sector ETF → NAICS mapping with approximate weights
    - Phase 2: fetch live holdings from ETF provider APIs (iShares CSV, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Holding:
    """A single ETF constituent."""
    ticker: str
    name: str
    weight: float               # 0.0–1.0 (proportion of ETF)
    naics_codes: list[str]      # primary NAICS classifications


@dataclass(frozen=True)
class ETFProfile:
    """An ETF with its holdings and NAICS exposure breakdown."""
    ticker: str
    name: str
    sector: str                 # broad label for display
    holdings: list[Holding]
    naics_exposure: dict[str, float]    # NAICS prefix → total weight

    def exposure_to(self, naics_prefix: str) -> float:
        """What fraction of this ETF is exposed to a NAICS code/prefix?

        Handles hierarchical matching: querying "211" will match
        holdings with NAICS "2111", "21111", "211110", etc.
        """
        total = 0.0
        for code, weight in self.naics_exposure.items():
            if code.startswith(naics_prefix) or naics_prefix.startswith(code):
                total += weight
        return min(total, 1.0)


# ── Static ETF Data (MVP) ───────────────────────────────────────────────
#
# Source: Approximate sector compositions from SPDR/iShares fact sheets.
# Phase 2 will replace this with live holdings data.
#
# Format: {NAICS prefix: approximate weight in ETF}

_SECTOR_ETFS: dict[str, dict] = {
    "XLE": {
        "name": "Energy Select Sector SPDR",
        "sector": "Energy",
        "naics_exposure": {
            "211": 0.42,    # Oil & Gas Extraction
            "324": 0.28,    # Petroleum/Coal Products
            "213": 0.12,    # Support Activities for Mining
            "221": 0.08,    # Utilities (pipeline/gas distribution)
            "486": 0.10,    # Pipeline Transportation
        },
    },
    "XLF": {
        "name": "Financial Select Sector SPDR",
        "sector": "Financials",
        "naics_exposure": {
            "522": 0.40,    # Banking / Credit Intermediation
            "523": 0.25,    # Securities / Investments
            "524": 0.20,    # Insurance
            "525": 0.10,    # Funds / Trusts
            "5223": 0.05,   # Activities Related to Credit
        },
    },
    "XLV": {
        "name": "Health Care Select Sector SPDR",
        "sector": "Health Care",
        "naics_exposure": {
            "3254": 0.40,   # Pharmaceutical Manufacturing
            "3391": 0.20,   # Medical Equipment
            "621": 0.10,    # Ambulatory Health Care
            "622": 0.08,    # Hospitals
            "524": 0.12,    # Health Insurance
            "5417": 0.10,   # Scientific R&D
        },
    },
    "XLK": {
        "name": "Technology Select Sector SPDR",
        "sector": "Information Technology",
        "naics_exposure": {
            "334": 0.35,    # Computer/Electronic Manufacturing
            "5112": 0.30,   # Software Publishers
            "5415": 0.20,   # Computer Systems Design
            "518": 0.10,    # Data Processing / Hosting
            "5182": 0.05,   # Data Processing Services
        },
    },
    "XLI": {
        "name": "Industrial Select Sector SPDR",
        "sector": "Industrials",
        "naics_exposure": {
            "3364": 0.15,   # Aerospace Product Manufacturing
            "332": 0.10,    # Fabricated Metal Products
            "333": 0.12,    # Machinery Manufacturing
            "236": 0.08,    # Construction of Buildings
            "484": 0.10,    # Truck Transportation
            "481": 0.08,    # Air Transportation
            "482": 0.05,    # Rail Transportation
            "561": 0.12,    # Administrative/Support Services
            "562": 0.08,    # Waste Management
            "238": 0.07,    # Specialty Trade Contractors
            "928": 0.05,    # National Security (defense contractors)
        },
    },
    "XLU": {
        "name": "Utilities Select Sector SPDR",
        "sector": "Utilities",
        "naics_exposure": {
            "2211": 0.55,   # Electric Power Generation
            "2212": 0.25,   # Natural Gas Distribution
            "2213": 0.15,   # Water/Sewage
            "221": 0.05,    # Utilities (general)
        },
    },
    "XLP": {
        "name": "Consumer Staples Select Sector SPDR",
        "sector": "Consumer Staples",
        "naics_exposure": {
            "311": 0.25,    # Food Manufacturing
            "312": 0.15,    # Beverage and Tobacco
            "325": 0.15,    # Chemical Mfg (household products)
            "445": 0.15,    # Food and Beverage Retail
            "446": 0.10,    # Health/Personal Care Stores
            "4529": 0.10,   # General Merchandise (Walmart, etc.)
            "424": 0.10,    # Nondurable Goods Wholesalers
        },
    },
    "XLY": {
        "name": "Consumer Discretionary Select Sector SPDR",
        "sector": "Consumer Discretionary",
        "naics_exposure": {
            "454": 0.25,    # Nonstore Retailers (e-commerce)
            "3361": 0.20,   # Motor Vehicle Manufacturing
            "721": 0.10,    # Accommodation (hotels)
            "722": 0.08,    # Food Services (restaurants)
            "448": 0.08,    # Clothing Stores
            "451": 0.07,    # Sporting Goods / Hobby
            "611": 0.07,    # Educational Services
            "7131": 0.08,   # Amusement Parks
            "7132": 0.07,   # Gambling Industries
        },
    },
    "XLC": {
        "name": "Communication Services Select Sector SPDR",
        "sector": "Communication Services",
        "naics_exposure": {
            "517": 0.30,    # Telecommunications
            "515": 0.15,    # Broadcasting
            "518": 0.15,    # Internet / Data Processing
            "519": 0.20,    # Web Search / Data Services
            "512": 0.10,    # Motion Picture / Sound Recording
            "7111": 0.10,   # Performing Arts
        },
    },
    "XLRE": {
        "name": "Real Estate Select Sector SPDR",
        "sector": "Real Estate",
        "naics_exposure": {
            "531": 0.60,    # Real Estate
            "525": 0.25,    # REITs (Funds/Trusts)
            "236": 0.15,    # Construction of Buildings
        },
    },
    "XLB": {
        "name": "Materials Select Sector SPDR",
        "sector": "Materials",
        "naics_exposure": {
            "325": 0.35,    # Chemical Manufacturing
            "331": 0.15,    # Primary Metal Manufacturing
            "322": 0.12,    # Paper Manufacturing
            "327": 0.10,    # Nonmetallic Mineral Products
            "212": 0.15,    # Mining (except Oil and Gas)
            "332": 0.08,    # Fabricated Metal Products
            "326": 0.05,    # Plastics/Rubber Products
        },
    },
}


# ── Sub-Sector / Thematic ETFs (Phase 1 expansion) ────────────────────
#
# These provide granular exposure beyond the 11 SPDR sector ETFs.
# Source: Approximate compositions from iShares/SPDR/VanEck fact sheets.

_SUBSECTOR_ETFS: dict[str, dict] = {
    # ── Biotech / Pharma ───────────────────────────────────────────
    "XBI": {
        "name": "SPDR S&P Biotech ETF",
        "sector": "Health Care",
        "naics_exposure": {
            "325414": 0.55,  # Biological Product Manufacturing
            "3254": 0.25,    # Pharmaceutical Manufacturing
            "5417": 0.15,    # Scientific R&D Services
            "3391": 0.05,    # Medical Equipment & Supplies
        },
    },
    "IBB": {
        "name": "iShares Biotechnology ETF",
        "sector": "Health Care",
        "naics_exposure": {
            "325414": 0.50,  # Biological Product Manufacturing
            "3254": 0.30,    # Pharmaceutical Manufacturing
            "5417": 0.12,    # Scientific R&D Services
            "621": 0.05,     # Ambulatory Health Care
            "3391": 0.03,    # Medical Equipment
        },
    },
    "IHI": {
        "name": "iShares U.S. Medical Devices ETF",
        "sector": "Health Care",
        "naics_exposure": {
            "3391": 0.60,    # Medical Equipment & Supplies
            "3345": 0.20,    # Navigational/Electromedical Instruments
            "3254": 0.10,    # Pharmaceutical (drug-device combos)
            "5417": 0.10,    # Scientific R&D Services
        },
    },

    # ── Oil & Gas / Energy ─────────────────────────────────────────
    "XOP": {
        "name": "SPDR S&P Oil & Gas Exploration & Production ETF",
        "sector": "Energy",
        "naics_exposure": {
            "211": 0.70,     # Oil & Gas Extraction
            "213": 0.15,     # Support Activities for Mining
            "324": 0.10,     # Petroleum/Coal Products
            "486": 0.05,     # Pipeline Transportation
        },
    },
    "OIH": {
        "name": "VanEck Oil Services ETF",
        "sector": "Energy",
        "naics_exposure": {
            "213": 0.55,     # Support Activities for Mining
            "211": 0.20,     # Oil & Gas Extraction
            "333": 0.15,     # Machinery Manufacturing (drilling equipment)
            "324": 0.10,     # Petroleum/Coal Products
        },
    },

    # ── Clean Energy / Solar ───────────────────────────────────────
    "TAN": {
        "name": "Invesco Solar ETF",
        "sector": "Energy",
        "naics_exposure": {
            "3344": 0.45,    # Semiconductor/Electronic Component Mfg (solar cells)
            "2211": 0.25,    # Electric Power Generation (solar farms)
            "335": 0.15,     # Electrical Equipment Manufacturing
            "238": 0.10,     # Specialty Trade Contractors (solar install)
            "5416": 0.05,    # Mgmt/Scientific/Technical Consulting
        },
    },
    "ICLN": {
        "name": "iShares Global Clean Energy ETF",
        "sector": "Energy",
        "naics_exposure": {
            "2211": 0.40,    # Electric Power Generation (wind/solar/hydro)
            "3344": 0.20,    # Semiconductor Mfg (solar cells)
            "335": 0.15,     # Electrical Equipment Manufacturing
            "221": 0.10,     # Utilities (general)
            "333": 0.10,     # Machinery (wind turbines)
            "238": 0.05,     # Specialty Trade Contractors
        },
    },

    # ── Banking / Finance ──────────────────────────────────────────
    "KRE": {
        "name": "SPDR S&P Regional Banking ETF",
        "sector": "Financials",
        "naics_exposure": {
            "522": 0.75,     # Credit Intermediation (commercial banking)
            "5223": 0.10,    # Activities Related to Credit
            "523": 0.08,     # Securities/Commodity Contracts
            "524": 0.07,     # Insurance
        },
    },
    "IAI": {
        "name": "iShares U.S. Broker-Dealers & Securities Exchanges ETF",
        "sector": "Financials",
        "naics_exposure": {
            "523": 0.65,     # Securities, Commodity Contracts, Investments
            "522": 0.15,     # Credit Intermediation
            "525": 0.10,     # Funds, Trusts, Financial Vehicles
            "5223": 0.10,    # Activities Related to Credit
        },
    },

    # ── Airlines / Transportation ──────────────────────────────────
    "JETS": {
        "name": "U.S. Global Jets ETF",
        "sector": "Industrials",
        "naics_exposure": {
            "481": 0.70,     # Air Transportation
            "4881": 0.15,    # Support Activities for Air Transport
            "3364": 0.10,    # Aerospace Product & Parts Mfg
            "721": 0.05,     # Accommodation (airline hotel partnerships)
        },
    },

    # ── Semiconductors / Tech ──────────────────────────────────────
    "SMH": {
        "name": "VanEck Semiconductor ETF",
        "sector": "Information Technology",
        "naics_exposure": {
            "3344": 0.65,    # Semiconductor/Electronic Component Mfg
            "334": 0.15,     # Computer/Electronic Product Mfg (broader)
            "3332": 0.10,    # Industrial Machinery (fab equipment)
            "5415": 0.10,    # Computer Systems Design (EDA, design services)
        },
    },

    # ── Cybersecurity ──────────────────────────────────────────────
    "HACK": {
        "name": "ETFMG Prime Cyber Security ETF",
        "sector": "Information Technology",
        "naics_exposure": {
            "5415": 0.45,    # Computer Systems Design
            "5112": 0.35,    # Software Publishers
            "518": 0.10,     # Data Processing / Hosting
            "5416": 0.10,    # Mgmt/Scientific Consulting (cyber consulting)
        },
    },
    "CIBR": {
        "name": "First Trust NASDAQ Cybersecurity ETF",
        "sector": "Information Technology",
        "naics_exposure": {
            "5112": 0.40,    # Software Publishers
            "5415": 0.40,    # Computer Systems Design
            "518": 0.12,     # Data Processing / Hosting
            "334": 0.08,     # Computer/Electronic Product Mfg (hardware security)
        },
    },

    # ── Homebuilders / Real Estate ─────────────────────────────────
    "XHB": {
        "name": "SPDR S&P Homebuilders ETF",
        "sector": "Consumer Discretionary",
        "naics_exposure": {
            "236": 0.40,     # Construction of Buildings
            "238": 0.20,     # Specialty Trade Contractors
            "321": 0.10,     # Wood Product Manufacturing
            "337": 0.10,     # Furniture Manufacturing
            "444": 0.10,     # Building Material Dealers
            "531": 0.10,     # Real Estate
        },
    },

    # ── Mining / Metals ────────────────────────────────────────────
    "XME": {
        "name": "SPDR S&P Metals & Mining ETF",
        "sector": "Materials",
        "naics_exposure": {
            "212": 0.45,     # Mining (except Oil & Gas)
            "331": 0.35,     # Primary Metal Manufacturing
            "332": 0.10,     # Fabricated Metal Products
            "213": 0.10,     # Support Activities for Mining
        },
    },

    # ── Lithium / Battery ──────────────────────────────────────────
    "LIT": {
        "name": "Global X Lithium & Battery Tech ETF",
        "sector": "Materials",
        "naics_exposure": {
            "212": 0.30,     # Mining (lithium extraction)
            "3359": 0.25,    # Battery Manufacturing (Other Electrical Equipment)
            "331": 0.15,     # Primary Metal Manufacturing
            "325": 0.15,     # Chemical Manufacturing (battery chemicals)
            "3361": 0.10,    # Motor Vehicle Manufacturing (EV)
            "3344": 0.05,    # Semiconductor Mfg (battery mgmt chips)
        },
    },

    # ── Defense / Aerospace ────────────────────────────────────────
    "ITA": {
        "name": "iShares U.S. Aerospace & Defense ETF",
        "sector": "Industrials",
        "naics_exposure": {
            "3364": 0.55,    # Aerospace Product & Parts Mfg
            "928": 0.15,     # National Security / International Affairs
            "334": 0.10,     # Computer/Electronic Products (avionics)
            "3345": 0.10,    # Navigational Instruments
            "5415": 0.10,    # Computer Systems Design (defense IT)
        },
    },

    # ── Telecommunications (FCC coverage gap) ──────────────────────
    "IYZ": {
        "name": "iShares U.S. Telecommunications ETF",
        "sector": "Communication Services",
        "naics_exposure": {
            "517": 0.65,     # Telecommunications
            "515": 0.15,     # Broadcasting
            "518": 0.10,     # Data Processing / Hosting
            "334": 0.10,     # Computer/Electronic Products (telecom equipment)
        },
    },

    # ── Transportation (DOT coverage — truck/rail/sea, beyond JETS) ─
    "IYT": {
        "name": "iShares Transportation Average ETF",
        "sector": "Industrials",
        "naics_exposure": {
            "484": 0.25,     # Truck Transportation
            "482": 0.20,     # Rail Transportation
            "481": 0.20,     # Air Transportation
            "483": 0.10,     # Water Transportation
            "492": 0.10,     # Couriers and Messengers
            "488": 0.10,     # Support Activities for Transportation
            "493": 0.05,     # Warehousing and Storage
        },
    },

    # ── Retail (FTC consumer protection coverage) ──────────────────
    "XRT": {
        "name": "SPDR S&P Retail ETF",
        "sector": "Consumer Discretionary",
        "naics_exposure": {
            "452": 0.20,     # General Merchandise Stores
            "448": 0.15,     # Clothing/Accessories Stores
            "454": 0.15,     # Nonstore Retailers (e-commerce)
            "445": 0.12,     # Food and Beverage Stores
            "441": 0.10,     # Motor Vehicle Dealers
            "444": 0.08,     # Building Material Dealers
            "446": 0.08,     # Health/Personal Care Stores
            "443": 0.07,     # Electronics/Appliance Stores
            "442": 0.05,     # Furniture Stores
        },
    },

    # ── Healthcare Providers (HHS/CMS hospital/insurance coverage) ─
    "IHF": {
        "name": "iShares U.S. Healthcare Providers ETF",
        "sector": "Health Care",
        "naics_exposure": {
            "524": 0.35,     # Insurance Carriers (health insurance)
            "622": 0.25,     # Hospitals
            "621": 0.20,     # Ambulatory Health Care
            "623": 0.10,     # Nursing/Residential Care
            "621111": 0.10,  # Offices of Physicians
        },
    },

    # ── Insurance (CFPB/state reg coverage) ────────────────────────
    "KIE": {
        "name": "SPDR S&P Insurance ETF",
        "sector": "Financials",
        "naics_exposure": {
            "524": 0.70,     # Insurance Carriers
            "5242": 0.15,    # Insurance Agencies/Brokerages
            "523": 0.10,     # Securities (reinsurance/financial)
            "522": 0.05,     # Credit Intermediation (bancassurance)
        },
    },

    # ── Agriculture (USDA / CFR Title 7 coverage) ──────────────────
    "MOO": {
        "name": "VanEck Agribusiness ETF",
        "sector": "Consumer Staples",
        "naics_exposure": {
            "111": 0.18,     # Crop Production
            "112": 0.13,     # Animal Production/Aquaculture
            "113": 0.05,     # Forestry and Logging
            "114": 0.04,     # Fishing/Hunting/Trapping
            "311": 0.23,     # Food Manufacturing
            "325320": 0.09,  # Pesticide/Fertilizer Manufacturing
            "333": 0.10,     # Machinery (farm equipment)
            "424": 0.09,     # Nondurable Goods Merchant Wholesalers
            "115": 0.09,     # Support Activities for Agriculture
        },
    },

    # ── Water Resources (EPA water regulation coverage) ────────────
    "PHO": {
        "name": "Invesco Water Resources ETF",
        "sector": "Utilities",
        "naics_exposure": {
            "2213": 0.35,    # Water/Sewage Systems
            "562": 0.20,     # Waste Management (water treatment)
            "333": 0.15,     # Machinery (pumps, filtration equipment)
            "3272": 0.10,    # Glass/Ceramics (pipes)
            "325": 0.10,     # Chemical Manufacturing (water chemicals)
            "5417": 0.10,    # Scientific R&D (water tech)
        },
    },
}


class ETFExposureEngine:
    """Calculate exposure scores between industries and ETFs.

    Usage:
        engine = ETFExposureEngine()

        # What ETFs are exposed to Oil & Gas (NAICS 211)?
        results = engine.find_exposed_etfs("211")
        # → [("XLE", 0.42), ("XLB", 0.0), ...]

        # How exposed is XLE to Chemical Manufacturing (NAICS 325)?
        score = engine.exposure_score("XLE", "325")
        # → 0.0 (no direct exposure via that code)

        # Get full profile for an ETF
        profile = engine.get_profile("XLE")
    """

    def __init__(self):
        self._profiles: dict[str, ETFProfile] = {}
        # Load both sector-level and sub-sector ETFs
        for source in (_SECTOR_ETFS, _SUBSECTOR_ETFS):
            for ticker, data in source.items():
                self._profiles[ticker] = ETFProfile(
                    ticker=ticker,
                    name=data["name"],
                    sector=data["sector"],
                    holdings=[],  # Phase 2: populate from live data
                    naics_exposure=data["naics_exposure"],
                )

    def get_profile(self, ticker: str) -> ETFProfile | None:
        """Get full ETF profile."""
        return self._profiles.get(ticker)

    def all_tickers(self) -> list[str]:
        """All available ETF tickers."""
        return sorted(self._profiles.keys())

    def exposure_score(self, ticker: str, naics_prefix: str) -> float:
        """How exposed is this ETF to a specific NAICS code/prefix?"""
        profile = self._profiles.get(ticker)
        if not profile:
            return 0.0
        return profile.exposure_to(naics_prefix)

    def find_exposed_etfs(
        self, naics_prefix: str, min_exposure: float = 0.05
    ) -> list[tuple[str, float]]:
        """Find all ETFs with meaningful exposure to a NAICS code.

        Returns list of (ticker, exposure_score) sorted by exposure descending.
        """
        results = []
        for ticker, profile in self._profiles.items():
            score = profile.exposure_to(naics_prefix)
            if score >= min_exposure:
                results.append((ticker, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def find_exposed_etfs_multi(
        self, naics_prefixes: list[str], min_exposure: float = 0.05
    ) -> list[tuple[str, float, str]]:
        """Find ETFs exposed to any of several NAICS codes.

        Returns list of (ticker, max_exposure, matching_naics) sorted by exposure.
        """
        results: dict[str, tuple[float, str]] = {}
        for naics in naics_prefixes:
            for ticker, score in self.find_exposed_etfs(naics, min_exposure):
                if ticker not in results or score > results[ticker][0]:
                    results[ticker] = (score, naics)
        output = [(t, s, n) for t, (s, n) in results.items()]
        output.sort(key=lambda x: x[1], reverse=True)
        return output
