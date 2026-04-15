"""SEC N-PORT Quarterly Holdings Parser.

N-PORT (Form N-PORT) is an SEC filing that registered investment companies
(mutual funds, ETFs) must submit quarterly. It contains full portfolio holdings
with market values, quantities, and identifiers.

Data source: SEC EDGAR XBRL/XML filings
  - Full-text search: https://efts.sec.gov/LATEST/search-index?q="NPORT-P"&dateRange=custom&startdt=2026-01-01
  - Direct CIK lookup: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=NPORT-P

N-PORT XML structure (simplified):
  <edgarSubmission>
    <formData>
      <genInfo>
        <regName>iShares Core S&P 500 ETF</regName>
        <repPdDate>2026-03-31</repPdDate>
        <repPdEnd>2026-03-31</repPdEnd>
      </genInfo>
      <invstOrSecs>
        <invstOrSec>
          <name>APPLE INC</name>
          <cusip>037833100</cusip>
          <balance>155000000</balance>
          <valUSD>28500000000</valUSD>
          <pctVal>7.25</pctVal>
          <assetCat>EC</assetCat>     <!-- EC=Equity Common -->
          <issuerCat>CORP</issuerCat>
          <investmentOrSecurity>
            <securityLending>...</securityLending>
          </investmentOrSecurity>
          <identifiers>
            <isin value="US0378331005"/>
            <ticker value="AAPL"/>
          </identifiers>
        </invstOrSec>
        ...
      </invstOrSecs>
    </formData>
  </edgarSubmission>

Usage:
    from exposure.nport import NPortParser, fetch_nport_filing

    # Parse from XML string
    parser = NPortParser()
    snapshot = parser.parse_xml(xml_text, etf_ticker="IVV")

    # Fetch from EDGAR
    snapshot = fetch_nport_filing(cik="0000088053", etf_ticker="IVV")
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .holdings import (
    HoldingRecord,
    HoldingsSnapshot,
    gics_sector_to_naics,
)

logger = logging.getLogger(__name__)


# ── ETF → CIK Mapping ────────────────────────────────────────────────
# Central Index Key (CIK) numbers for major ETF families on EDGAR.
# These are the filing entities, not the fund tickers.

ETF_CIK_MAP: dict[str, dict] = {
    # iShares (BlackRock)
    "IVV":  {"cik": "0000088053", "series": "S000006063", "name": "iShares Core S&P 500 ETF"},
    "IWM":  {"cik": "0000088053", "series": "S000006075", "name": "iShares Russell 2000 ETF"},
    "EFA":  {"cik": "0000088053", "series": "S000006058", "name": "iShares MSCI EAFE ETF"},
    "AGG":  {"cik": "0000088053", "series": "S000006066", "name": "iShares Core US Aggregate Bond"},
    # SPDR (State Street)
    "SPY":  {"cik": "0000884394", "series": "", "name": "SPDR S&P 500 ETF Trust"},
    "XLE":  {"cik": "0001064642", "series": "S000006421", "name": "Energy Select Sector SPDR"},
    "XLF":  {"cik": "0001064642", "series": "S000006417", "name": "Financial Select Sector SPDR"},
    "XLK":  {"cik": "0001064642", "series": "S000006426", "name": "Technology Select Sector SPDR"},
    "XLV":  {"cik": "0001064642", "series": "S000006423", "name": "Health Care Select Sector SPDR"},
    "XLI":  {"cik": "0001064642", "series": "S000006420", "name": "Industrial Select Sector SPDR"},
    "XLU":  {"cik": "0001064642", "series": "S000006427", "name": "Utilities Select Sector SPDR"},
    "XLP":  {"cik": "0001064642", "series": "S000006425", "name": "Consumer Staples Select Sector SPDR"},
    "XLY":  {"cik": "0001064642", "series": "S000006422", "name": "Consumer Discretionary Select Sector SPDR"},
    "XLB":  {"cik": "0001064642", "series": "S000006424", "name": "Materials Select Sector SPDR"},
    "XLRE": {"cik": "0001064642", "series": "S000051547", "name": "Real Estate Select Sector SPDR"},
    # Vanguard
    "VTI":  {"cik": "0000036405", "series": "S000002636", "name": "Vanguard Total Stock Market ETF"},
    "VOO":  {"cik": "0000036405", "series": "S000031189", "name": "Vanguard S&P 500 ETF"},
}


# ── N-PORT Asset Category Codes ──────────────────────────────────────

_ASSET_CAT_MAP = {
    "EC": "Equity Common",
    "EP": "Equity Preferred",
    "DBT": "Debt",
    "STIV": "Short-Term Investment Vehicle",
    "ABS": "Asset-Backed Security",
    "AGEN": "Agency",
    "CORP": "Corporate",
    "MUNI": "Municipal",
    "FX": "Foreign Exchange",
    "OTHER": "Other",
}


# ── XML Namespace Handling ────────────────────────────────────────────
# N-PORT filings use namespaces; we need to handle both namespaced and
# non-namespaced versions.

NPORT_NS = {
    "nport": "http://www.sec.gov/edgar/nport",
    "": "",  # default
}


def _find_text(element: ET.Element, path: str, default: str = "") -> str:
    """Find text in an element, trying with and without namespace."""
    # Try without namespace
    el = element.find(path)
    if el is not None and el.text:
        return el.text.strip()

    # Try with namespace
    ns_path = path.replace("/", "/nport:")
    if not ns_path.startswith("nport:"):
        ns_path = "nport:" + ns_path
    el = element.find(ns_path, NPORT_NS)
    if el is not None and el.text:
        return el.text.strip()

    return default


def _find_all(element: ET.Element, path: str) -> list[ET.Element]:
    """Find all matching elements, trying with and without namespace."""
    results = element.findall(path)
    if results:
        return results

    ns_path = path.replace("/", "/nport:")
    if not ns_path.startswith("nport:"):
        ns_path = "nport:" + ns_path
    return element.findall(ns_path, NPORT_NS)


# ── Parser ────────────────────────────────────────────────────────────

class NPortParser:
    """Parse SEC N-PORT XML filings into HoldingsSnapshot objects.

    Handles:
      - Standard N-PORT XML format
      - Both namespaced and non-namespaced documents
      - Asset category filtering (equity only by default)
      - Weight calculation from pctVal or valUSD/totalAssets
    """

    def __init__(self, equity_only: bool = True):
        """
        Args:
            equity_only: If True, only include equity holdings (EC, EP).
                        If False, include all holding types.
        """
        self.equity_only = equity_only

    def parse_xml(
        self,
        xml_text: str,
        etf_ticker: str = "",
    ) -> Optional[HoldingsSnapshot]:
        """Parse N-PORT XML text into a HoldingsSnapshot.

        Args:
            xml_text: Raw XML content of the N-PORT filing
            etf_ticker: ETF ticker symbol (used for labeling)

        Returns:
            HoldingsSnapshot or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Failed to parse N-PORT XML: {e}")
            return None

        # Find formData element
        form_data = root.find(".//formData") or root.find(".//{http://www.sec.gov/edgar/nport}formData")
        if form_data is None:
            # Try direct child elements
            form_data = root

        # Extract general info
        gen_info = form_data.find("genInfo") or form_data.find("{http://www.sec.gov/edgar/nport}genInfo") or form_data
        fund_name = _find_text(gen_info, "regName", etf_ticker)
        report_date_str = _find_text(gen_info, "repPdDate", "")
        if not report_date_str:
            report_date_str = _find_text(gen_info, "repPdEnd", "")

        # Parse report date
        report_date = date.today()
        if report_date_str:
            try:
                report_date = date.fromisoformat(report_date_str)
            except ValueError:
                pass

        # Find holdings container
        holdings_container = (
            form_data.find(".//invstOrSecs") or
            form_data.find(".//{http://www.sec.gov/edgar/nport}invstOrSecs") or
            form_data
        )

        # Parse each holding
        holdings: list[HoldingRecord] = []
        holding_elements = (
            _find_all(holdings_container, "invstOrSec") or
            _find_all(form_data, ".//invstOrSec")
        )

        for sec in holding_elements:
            record = self._parse_holding(sec)
            if record is None:
                continue

            # Filter by asset category
            if self.equity_only and record.asset_class not in ("Equity Common", "Equity Preferred", "Equity"):
                continue

            holdings.append(record)

        if not holdings:
            logger.warning(f"No holdings found in N-PORT filing for {etf_ticker}")
            return None

        # Normalize weights if needed
        weight_sum = sum(h.weight for h in holdings)
        if weight_sum > 0 and abs(weight_sum - 1.0) > 0.05:
            for h in holdings:
                h.weight = h.weight / weight_sum

        return HoldingsSnapshot(
            etf_ticker=etf_ticker or fund_name,
            snapshot_date=report_date,
            source="sec_nport",
            holdings=holdings,
        )

    def _parse_holding(self, sec: ET.Element) -> Optional[HoldingRecord]:
        """Parse a single <invstOrSec> element."""
        name = _find_text(sec, "name")
        if not name:
            return None

        cusip = _find_text(sec, "cusip")
        balance_str = _find_text(sec, "balance", "0")
        val_usd_str = _find_text(sec, "valUSD", "0")
        pct_val_str = _find_text(sec, "pctVal", "0")
        asset_cat = _find_text(sec, "assetCat", "EC")

        # Parse numeric values
        try:
            shares = int(float(balance_str.replace(",", "")))
        except (ValueError, TypeError):
            shares = 0

        try:
            market_value = float(val_usd_str.replace(",", ""))
        except (ValueError, TypeError):
            market_value = 0.0

        try:
            weight = float(pct_val_str.replace(",", ""))
            if weight > 1.0:  # percentage → decimal
                weight = weight / 100.0
        except (ValueError, TypeError):
            weight = 0.0

        # Map asset category
        asset_class = _ASSET_CAT_MAP.get(asset_cat, asset_cat)

        # Extract identifiers
        ticker = ""
        isin = ""
        sedol = ""

        identifiers = sec.find("identifiers") or sec.find("{http://www.sec.gov/edgar/nport}identifiers")
        if identifiers is not None:
            for child in identifiers:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                val = child.get("value", "") or (child.text or "").strip()
                if tag == "ticker":
                    ticker = val
                elif tag == "isin":
                    isin = val
                elif tag == "sedol":
                    sedol = val

        return HoldingRecord(
            ticker=ticker,
            name=name,
            weight=weight,
            shares=shares,
            market_value=market_value,
            asset_class=asset_class,
            isin=isin,
            sedol=sedol,
            naics_codes=[],  # Will be enriched later via NAICS cache
        )


# ── EDGAR Fetcher ─────────────────────────────────────────────────────

EDGAR_FILING_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"


def _edgar_request(url: str, params: dict = None) -> str:
    """Make a request to EDGAR with proper User-Agent."""
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    req = urllib.request.Request(url, headers={
        # SEC requires a company identifier in User-Agent
        "User-Agent": "Legalize/0.1 (regulation-exposure-mapper; contact@legalize.dev)",
        "Accept": "application/xml,text/xml,text/html,*/*",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_nport_filing(
    cik: str,
    etf_ticker: str = "",
    series_id: str = "",
) -> Optional[HoldingsSnapshot]:
    """Fetch the latest N-PORT filing for a fund from EDGAR.

    Note: EDGAR rate limits to 10 requests/sec.

    Args:
        cik: Central Index Key (SEC identifier)
        etf_ticker: ETF ticker for labeling
        series_id: Series ID to filter (some CIKs file for multiple funds)

    Returns:
        HoldingsSnapshot or None if fetch fails
    """
    try:
        # Step 1: Find the latest NPORT-P filing
        search_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik}&type=NPORT-P"
            f"&dateb=&owner=include&count=5&search_text=&action=getcompany"
        )
        index_html = _edgar_request(search_url)

        # Extract filing document links (look for NPORT-P entries)
        # The index page has links to individual filings
        doc_pattern = re.compile(
            r'href="(/Archives/edgar/data/\d+/\d+/[^"]+\.xml)"',
            re.IGNORECASE,
        )
        matches = doc_pattern.findall(index_html)

        if not matches:
            # Try alternate pattern for filing index
            idx_pattern = re.compile(
                r'href="(/Archives/edgar/data/\d+/\d+/\d+-\d+-\d+-index\.htm[l]?)"',
                re.IGNORECASE,
            )
            idx_matches = idx_pattern.findall(index_html)
            if idx_matches:
                # Fetch the filing index page
                idx_url = f"https://www.sec.gov{idx_matches[0]}"
                idx_html = _edgar_request(idx_url)
                matches = doc_pattern.findall(idx_html)

        if not matches:
            logger.warning(f"No NPORT-P filings found for CIK {cik}")
            return None

        # Step 2: Fetch the XML document
        xml_url = f"https://www.sec.gov{matches[0]}"
        xml_text = _edgar_request(xml_url)

        # Step 3: Parse
        parser = NPortParser()
        snapshot = parser.parse_xml(xml_text, etf_ticker=etf_ticker)

        return snapshot

    except Exception as e:
        logger.error(f"Failed to fetch N-PORT for CIK {cik}: {e}")
        return None


def fetch_nport_for_etf(etf_ticker: str) -> Optional[HoldingsSnapshot]:
    """Convenience: fetch N-PORT using the built-in ETF→CIK map."""
    if etf_ticker not in ETF_CIK_MAP:
        logger.warning(f"No CIK mapping for {etf_ticker}")
        return None

    info = ETF_CIK_MAP[etf_ticker]
    return fetch_nport_filing(
        cik=info["cik"],
        etf_ticker=etf_ticker,
        series_id=info.get("series", ""),
    )
