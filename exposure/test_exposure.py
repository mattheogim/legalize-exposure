"""Test the exposure mapping pipeline end-to-end."""

import sys
from datetime import date
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from exposure.schema import (
    EdgeType, EvidenceType, ObligationType,
    Edge, Law, Regulation, Provision, Obligation,
    RegulatedEntityType, Industry, ETFProxy, ExposureGraph,
)
from exposure.lookups import AgencyLookup, CFRLookup
from exposure.etf_exposure import ETFExposureEngine
from exposure.mapper import ExposureMapper
from exposure.macro_calendar import MacroEventCalendar, MacroEventType


def test_schema():
    """Test node/edge creation and validation."""
    print("=== Schema Tests ===")

    # Test hard link confidence validation
    try:
        Edge(
            source_id="a", target_id="b",
            edge_type=EdgeType.CITES,
            evidence_type=EvidenceType.CITATION,
            confidence=0.5,  # should fail: hard link needs >= 0.9
            provenance="test",
        )
        print("FAIL: Should have raised ValueError for low-confidence hard link")
    except ValueError as e:
        print(f"PASS: Hard link confidence validation: {e}")

    # Test soft link allows low confidence
    edge = Edge(
        source_id="a", target_id="b",
        edge_type=EdgeType.MENTIONS,
        evidence_type=EvidenceType.KEYWORD,
        confidence=0.4,
        provenance="keyword match",
    )
    print(f"PASS: Soft link created with confidence {edge.confidence}")

    # Test edge type properties
    assert EdgeType.CITES.is_hard
    assert EdgeType.IMPLEMENTS.is_hard
    assert EdgeType.MENTIONS.is_soft
    assert EdgeType.EXPOSES.is_soft
    print("PASS: Edge type hard/soft classification")

    print()


def test_graph_validation():
    """Test that the graph enforces allowed edge types."""
    print("=== Graph Validation Tests ===")
    graph = ExposureGraph()

    law = Law(title="Clean Air Act", usc_cite="42 USC §7401")
    reg = Regulation(title="Emissions Standards", agency_slug="epa")
    etf = ETFProxy(ticker="XLE", name="Energy SPDR")

    graph.add_node(law)
    graph.add_node(reg)
    graph.add_node(etf)

    # Valid: Law → Regulation via CITES
    graph.add_edge(Edge(
        source_id=law.id, target_id=reg.id,
        edge_type=EdgeType.CITES,
        evidence_type=EvidenceType.CITATION,
        confidence=0.95,
        provenance="42 USC §7401 authorizes 40 CFR 60",
    ))
    print("PASS: Law → Regulation (CITES) accepted")

    # Invalid: Law → ETF directly (should fail)
    try:
        graph.add_edge(Edge(
            source_id=law.id, target_id=etf.id,
            edge_type=EdgeType.EXPOSES,
            evidence_type=EvidenceType.HOLDINGS,
            confidence=0.5,
            provenance="test",
        ))
        print("FAIL: Should have blocked Law → ETF direct link")
    except TypeError as e:
        print(f"PASS: Law → ETF blocked: {e}")

    print()


def test_agency_lookup():
    """Test LF1: Agency → Industry mapping."""
    print("=== Agency Lookup (LF1) Tests ===")
    lookup = AgencyLookup()

    # EPA should map to Energy/Environment industries
    epa = lookup.match("environmental-protection-agency")
    naics_codes = [m.naics_code for m in epa]
    assert "211" in naics_codes, f"EPA should map to Oil & Gas (211), got {naics_codes}"
    assert "221" in naics_codes, f"EPA should map to Utilities (221)"
    assert "562" in naics_codes, f"EPA should map to Waste Management (562)"
    print(f"PASS: EPA → {len(epa)} industries: {naics_codes}")

    # SEC should map to Financial industries
    sec = lookup.match("securities-and-exchange-commission")
    naics_codes = [m.naics_code for m in sec]
    assert "523" in naics_codes, f"SEC should map to Securities (523)"
    print(f"PASS: SEC → {len(sec)} industries: {naics_codes}")

    # Unknown agency returns empty
    unknown = lookup.match("fake-agency")
    assert len(unknown) == 0
    print("PASS: Unknown agency → empty list")

    print()


def test_cfr_lookup():
    """Test LF2: CFR Title → Industry mapping."""
    print("=== CFR Lookup (LF2) Tests ===")
    lookup = CFRLookup()

    # Title 40 = Environment
    env = lookup.match(40)
    naics_codes = [m.naics_code for m in env]
    assert "211" in naics_codes, f"CFR 40 should map to Oil & Gas"
    assert "562" in naics_codes, f"CFR 40 should map to Waste Management"
    print(f"PASS: CFR Title 40 → {len(env)} industries: {naics_codes}")

    # Parse from citation string
    from_cite = lookup.match_from_cite("40 CFR Part 60.112a")
    assert len(from_cite) == len(env)
    print(f"PASS: Citation parsing '40 CFR Part 60.112a' → {len(from_cite)} matches")

    # Title 21 = Food & Drugs
    fda = lookup.match(21)
    naics_codes = [m.naics_code for m in fda]
    assert "3254" in naics_codes, f"CFR 21 should map to Pharma"
    print(f"PASS: CFR Title 21 → {len(fda)} industries: {naics_codes}")

    print()


def test_etf_exposure():
    """Test ETF holdings-based exposure engine."""
    print("=== ETF Exposure Engine Tests ===")
    engine = ETFExposureEngine()

    # XLE should be highly exposed to Oil & Gas (211)
    score = engine.exposure_score("XLE", "211")
    assert score > 0.3, f"XLE should have >30% exposure to NAICS 211, got {score}"
    print(f"PASS: XLE exposure to NAICS 211 (Oil & Gas) = {score:.0%}")

    # XLF should be highly exposed to Banking (522)
    score = engine.exposure_score("XLF", "522")
    assert score > 0.3, f"XLF should have >30% exposure to NAICS 522"
    print(f"PASS: XLF exposure to NAICS 522 (Banking) = {score:.0%}")

    # XLE should NOT be exposed to Banking
    score = engine.exposure_score("XLE", "522")
    assert score < 0.05, f"XLE should have <5% exposure to Banking"
    print(f"PASS: XLE exposure to NAICS 522 (Banking) = {score:.0%} (correctly low)")

    # Find ETFs exposed to Utilities (221)
    exposed = engine.find_exposed_etfs("221")
    tickers = [t for t, _ in exposed]
    assert "XLU" in tickers, f"XLU should be exposed to Utilities"
    print(f"PASS: ETFs exposed to Utilities (221): {exposed}")

    print()


def test_full_pipeline():
    """Test the complete mapping pipeline with a realistic example."""
    print("=== Full Pipeline Test ===")
    mapper = ExposureMapper()

    # Example: EPA emissions rule
    result = mapper.map_federal_register_doc(
        title="Standards of Performance for New Stationary Sources: "
              "Electric Utility Steam Generating Units",
        agency_slug="environmental-protection-agency",
        cfr_citations=["40 CFR 60"],
        doc_type="RULE",
        fr_doc_number="2026-05678",
        publication_date=date(2026, 3, 15),
        effective_date=date(2026, 7, 1),
        significant=True,
        abstract=(
            "The Environmental Protection Agency is finalizing amendments to "
            "the emissions standards for coal-fired and natural gas-fired "
            "electric utility steam generating units. These standards shall "
            "require facilities to reduce carbon dioxide emissions by 90 "
            "percent by 2032."
        ),
    )

    print(f"Regulation: {result.regulation.title[:60]}...")
    print(f"Industries found: {len(result.industries)}")
    for ind in result.industries:
        print(f"  NAICS {ind.naics_code}: {ind.naics_title} ({ind.gics_sector})")

    print(f"ETFs exposed: {len(result.etfs)}")
    for etf in result.etfs:
        print(f"  {etf.ticker}: {etf.name} (exposure: {etf.exposure_score:.0%})")

    print(f"Graph: {result.graph.summary()}")
    print(f"Confidence: {result.confidence_summary}")

    # Verify key expectations
    ind_naics = {i.naics_code for i in result.industries}
    assert "211" in ind_naics, "EPA rule should map to Oil & Gas"
    assert "221" in ind_naics, "EPA rule should map to Utilities"

    etf_tickers = {e.ticker for e in result.etfs}
    assert "XLE" in etf_tickers, "Should expose XLE (Energy)"
    assert "XLU" in etf_tickers, "Should expose XLU (Utilities)"

    print("\nPASS: Full pipeline produced valid exposure graph")

    # Test explainability: trace path from regulation to XLE
    print("\n--- Exposure Path: Regulation → XLE ---")
    xle = next(e for e in result.etfs if e.ticker == "XLE")
    path = result.graph.get_exposure_path(result.regulation.id, xle.id)
    if path:
        for node, edge in path:
            node_type = type(node).__name__
            if edge:
                print(f"  {node_type} --[{edge.edge_type.value}]--> "
                      f"(conf: {edge.confidence:.2f}, evidence: {edge.evidence_type.value})")
            else:
                print(f"  {node_type}: {getattr(node, 'ticker', getattr(node, 'title', ''))}")
    else:
        print("  (no direct path found — graph traversal via provision)")

    print()


def test_sec_financial_rule():
    """Test with an SEC financial regulation."""
    print("=== SEC Financial Rule Test ===")
    mapper = ExposureMapper()

    result = mapper.map_federal_register_doc(
        title="Amendments to Form 10-K Climate Disclosure Requirements",
        agency_slug="securities-and-exchange-commission",
        cfr_citations=["17 CFR 229"],
        doc_type="RULE",
        fr_doc_number="2026-09876",
        publication_date=date(2026, 4, 1),
        significant=True,
        abstract=(
            "The Securities and Exchange Commission is adopting amendments "
            "to require registrants to disclose material climate-related risks "
            "and greenhouse gas emissions. Companies must file attestation "
            "reports for Scope 1 and Scope 2 emissions."
        ),
    )

    print(f"Industries: {len(result.industries)}")
    for ind in result.industries:
        print(f"  NAICS {ind.naics_code}: {ind.naics_title}")

    print(f"ETFs: {len(result.etfs)}")
    for etf in result.etfs:
        print(f"  {etf.ticker}: {etf.name}")

    etf_tickers = {e.ticker for e in result.etfs}
    assert "XLF" in etf_tickers, "SEC rule should expose XLF (Financials)"
    print("\nPASS: SEC rule correctly maps to financial sector")

    print()


def test_fda_drug_rule():
    """Test with an FDA pharmaceutical regulation."""
    print("=== FDA Drug Rule Test ===")
    mapper = ExposureMapper()

    result = mapper.map_federal_register_doc(
        title="New Drug Application Requirements for Biosimilar Products",
        agency_slug="food-and-drug-administration",
        cfr_citations=["21 CFR 314"],
        doc_type="PRORULE",
        fr_doc_number="2026-11111",
        publication_date=date(2026, 5, 1),
        comment_end_date=date(2026, 8, 1),
        abstract=(
            "The Food and Drug Administration is proposing to amend "
            "requirements for new drug applications to streamline the "
            "approval pathway for biosimilar products. NAICS 325414 "
            "biological product manufacturing facilities shall comply "
            "with updated documentation standards."
        ),
    )

    print(f"Industries: {len(result.industries)}")
    for ind in result.industries:
        print(f"  NAICS {ind.naics_code}: {ind.naics_title} (conf: "
              f"{next((e.confidence for e in result.graph.edges if e.target_id == ind.id), 0):.2f})")

    # NAICS 325414 should be found via LF3 (regex extraction)
    ind_naics = {i.naics_code for i in result.industries}
    assert "325414" in ind_naics, "Should extract NAICS 325414 from text"
    print("\nPASS: FDA rule correctly extracts NAICS from text (LF3)")

    print(f"ETFs: {len(result.etfs)}")
    for etf in result.etfs:
        print(f"  {etf.ticker}: {etf.name}")

    print()


def test_subsector_etfs():
    """Test sub-sector ETF exposure engine additions."""
    print("=== Sub-Sector ETF Tests ===")
    engine = ETFExposureEngine()

    # Verify total ETF count: 11 sector + 24 sub-sector = 35
    total = len(engine.all_tickers())
    assert total == 35, f"Expected 35 ETFs, got {total}: {sorted(engine.all_tickers())}"
    print(f"PASS: Total ETFs loaded = {total}")

    # XBI should be highly exposed to Biological Products (325414)
    score = engine.exposure_score("XBI", "325414")
    assert score > 0.5, f"XBI should have >50% exposure to NAICS 325414, got {score}"
    print(f"PASS: XBI exposure to NAICS 325414 (Biologics) = {score:.0%}")

    # KRE should be highly exposed to Banking (522)
    score = engine.exposure_score("KRE", "522")
    assert score > 0.7, f"KRE should have >70% exposure to NAICS 522, got {score}"
    print(f"PASS: KRE exposure to NAICS 522 (Banking) = {score:.0%}")

    # JETS should be highly exposed to Air Transportation (481)
    score = engine.exposure_score("JETS", "481")
    assert score > 0.6, f"JETS should have >60% exposure to NAICS 481, got {score}"
    print(f"PASS: JETS exposure to NAICS 481 (Air Transport) = {score:.0%}")

    # SMH should be highly exposed to Semiconductors (3344)
    score = engine.exposure_score("SMH", "3344")
    assert score > 0.6, f"SMH should have >60% exposure to NAICS 3344, got {score}"
    print(f"PASS: SMH exposure to NAICS 3344 (Semiconductors) = {score:.0%}")

    # XOP should NOT be exposed to Banking
    score = engine.exposure_score("XOP", "522")
    assert score < 0.01, f"XOP should have ~0% exposure to Banking, got {score}"
    print(f"PASS: XOP exposure to NAICS 522 (Banking) = {score:.0%} (correctly zero)")

    # Sub-sector ETFs should appear in find_exposed_etfs
    biotech = engine.find_exposed_etfs("325414")
    tickers = [t for t, _ in biotech]
    assert "XBI" in tickers, "XBI should show up for NAICS 325414"
    assert "IBB" in tickers, "IBB should show up for NAICS 325414"
    print(f"PASS: ETFs exposed to NAICS 325414: {biotech}")

    # ITA should be exposed to Aerospace (3364)
    score = engine.exposure_score("ITA", "3364")
    assert score > 0.5, f"ITA should have >50% exposure to NAICS 3364"
    print(f"PASS: ITA exposure to NAICS 3364 (Aerospace) = {score:.0%}")

    # HACK/CIBR should be exposed to Software (5112)
    hack_score = engine.exposure_score("HACK", "5112")
    cibr_score = engine.exposure_score("CIBR", "5112")
    assert hack_score > 0.3, f"HACK should have >30% exposure to Software"
    assert cibr_score > 0.3, f"CIBR should have >30% exposure to Software"
    print(f"PASS: HACK→5112={hack_score:.0%}, CIBR→5112={cibr_score:.0%}")

    # ── New gap-fill ETFs ──
    # IYZ (Telecom) → FCC coverage
    score = engine.exposure_score("IYZ", "517")
    assert score > 0.6, f"IYZ should have >60% exposure to Telecom (517)"
    print(f"PASS: IYZ→517 (Telecom) = {score:.0%}")

    # IYT (Transportation) → DOT coverage
    score = engine.exposure_score("IYT", "484")
    assert score > 0.2, f"IYT should have >20% exposure to Trucking (484)"
    print(f"PASS: IYT→484 (Trucking) = {score:.0%}")

    # XRT (Retail) → FTC coverage
    score = engine.exposure_score("XRT", "454")
    assert score > 0.1, f"XRT should have >10% exposure to e-commerce (454)"
    print(f"PASS: XRT→454 (E-commerce) = {score:.0%}")

    # IHF (Healthcare Providers) → HHS coverage
    score = engine.exposure_score("IHF", "622")
    assert score > 0.2, f"IHF should have >20% exposure to Hospitals (622)"
    print(f"PASS: IHF→622 (Hospitals) = {score:.0%}")

    # KIE (Insurance) → CFPB coverage
    score = engine.exposure_score("KIE", "524")
    assert score > 0.7, f"KIE should have >70% exposure to Insurance (524)"
    print(f"PASS: KIE→524 (Insurance) = {score:.0%}")

    # MOO (Agribusiness) → USDA/CFR Title 7 coverage
    score = engine.exposure_score("MOO", "111")
    assert score > 0.15, f"MOO should have >15% exposure to Crops (111)"
    print(f"PASS: MOO→111 (Crop Production) = {score:.0%}")

    # PHO (Water) → EPA water reg coverage
    score = engine.exposure_score("PHO", "2213")
    assert score > 0.3, f"PHO should have >30% exposure to Water Systems (2213)"
    print(f"PASS: PHO→2213 (Water Systems) = {score:.0%}")

    print()


def test_macro_calendar():
    """Test FOMC + macro event calendar."""
    print("=== Macro Event Calendar Tests ===")
    cal = MacroEventCalendar(years=[2025, 2026])

    # Check event count is reasonable
    all_events = cal.events
    assert len(all_events) > 100, f"Expected >100 events, got {len(all_events)}"
    print(f"PASS: Calendar loaded {len(all_events)} events for 2025-2026")

    # FOMC decision on 2026-03-18 should exist
    fomc_events = cal.events_in_window(
        date(2026, 3, 18), date(2026, 3, 18),
        event_types=[MacroEventType.FOMC_DECISION],
    )
    assert len(fomc_events) == 1, f"Expected FOMC on 2026-03-18, got {fomc_events}"
    print(f"PASS: FOMC decision found on 2026-03-18: {fomc_events[0].title}")

    # Contamination score on FOMC day should be very high
    score = cal.contamination_score(date(2026, 3, 18), window_days=5)
    assert score >= 0.8, f"FOMC day should have contamination >= 0.8, got {score}"
    print(f"PASS: Contamination on FOMC day (2026-03-18) = {score:.2f}")

    # Day far from any event should have lower contamination
    # Pick a random mid-month date that's unlikely to be near major events
    quiet_score = cal.contamination_score(date(2026, 2, 22), window_days=2)
    print(f"INFO: Contamination on 2026-02-22 (±2d) = {quiet_score:.2f}")

    # NFP should exist (1st Friday of each month)
    nfp_jan = cal.events_in_window(
        date(2026, 1, 1), date(2026, 1, 10),
        event_types=[MacroEventType.NFP],
    )
    assert len(nfp_jan) == 1, f"Expected NFP in early Jan 2026, got {nfp_jan}"
    print(f"PASS: NFP found: {nfp_jan[0].event_date} ({nfp_jan[0].title})")

    # Summary should work
    summary = cal.summary(2026)
    assert summary["total_events"] > 50
    assert "FOMC_DECISION" in summary["by_type"]
    assert summary["by_type"]["FOMC_DECISION"] == 8  # 8 meetings/year
    print(f"PASS: 2026 summary: {summary['total_events']} events, "
          f"{summary['by_type']['FOMC_DECISION']} FOMC decisions")

    # Earnings season contamination
    # April 15 2026 should be in earnings season
    earnings_score = cal.contamination_score(date(2026, 4, 15), window_days=3)
    assert earnings_score >= 0.4, f"Mid-earnings should have >= 0.4, got {earnings_score}"
    print(f"PASS: Earnings season contamination (2026-04-15) = {earnings_score:.2f}")

    # Find clean windows should return some dates
    clean = cal.find_clean_windows(
        date(2026, 2, 1), date(2026, 2, 28),
        window_days=3, max_contamination=0.3,
    )
    print(f"PASS: Found {len(clean)} clean dates in Feb 2026 (±3d, max 0.3)")

    print()


def test_pipeline_with_contamination():
    """Test that mapper + calendar work together."""
    print("=== Pipeline + Contamination Integration Test ===")
    mapper = ExposureMapper()
    cal = MacroEventCalendar()

    # Map an EPA rule published ON an FOMC day
    result = mapper.map_federal_register_doc(
        title="Revised Emissions Standards for Refineries",
        agency_slug="environmental-protection-agency",
        cfr_citations=["40 CFR 63"],
        doc_type="RULE",
        fr_doc_number="2026-07777",
        publication_date=date(2026, 3, 18),  # FOMC day!
        significant=True,
        abstract="EPA is revising national emission standards for petroleum refineries.",
    )

    # Calculate contamination for this date
    contamination = cal.contamination_score(
        date(2026, 3, 18), window_days=5,
    )
    print(f"Regulation published: 2026-03-18")
    print(f"Contamination score: {contamination:.2f} (FOMC day)")
    print(f"Industries: {len(result.industries)}, ETFs: {len(result.etfs)}")

    # Sub-sector ETFs should now appear
    etf_tickers = {e.ticker for e in result.etfs}
    print(f"ETFs found: {sorted(etf_tickers)}")
    assert "XLE" in etf_tickers, "Should expose XLE (broad energy)"
    assert "XOP" in etf_tickers, "Should expose XOP (O&G E&P)"
    print(f"PASS: Both XLE (sector) and XOP (sub-sector) exposed")

    # Verify contamination is high (FOMC)
    assert contamination >= 0.8
    print(f"PASS: High contamination correctly flagged for FOMC day")

    print()


if __name__ == "__main__":
    test_schema()
    test_graph_validation()
    test_agency_lookup()
    test_cfr_lookup()
    test_etf_exposure()
    test_subsector_etfs()
    test_macro_calendar()
    test_full_pipeline()
    test_sec_financial_rule()
    test_fda_drug_rule()
    test_pipeline_with_contamination()
    print("=" * 60)
    print("ALL TESTS PASSED")
