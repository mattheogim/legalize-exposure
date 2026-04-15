"""Ontology schema for Regulation-to-Exposure Mapping.

Implements the 7-layer chain:
    Law → Regulation → Provision → Obligation → RegulatedEntityType → Industry → ETF

Edge taxonomy follows Meta-style verb separation:
    - Structural edges: CITES, IMPLEMENTS, IMPOSES, APPLIES_TO (hard)
    - Inferred edges:   MENTIONS, EXPOSES (soft)

Regulation character (RESTRICTS, MANDATES, etc.) is stored as
an Obligation property, NOT as an edge type (Gemini-style separation).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


# ── Edge Types (Meta-style) ─────────────────────────────────────────────

class EdgeType(str, Enum):
    """Relationship types between nodes.

    Hard links (document-evidenced):
        CITES        – law references a regulation (USC → CFR)
        IMPLEMENTS   – regulation implements a law (FR preamble "Authority:")
        IMPOSES      – regulation imposes an obligation ("shall", "must")
        APPLIES_TO   – obligation defines its regulated entity scope

    Soft links (inferred):
        MENTIONS     – text contains industry keywords (TF-IDF, NER)
        EXPOSES      – industry has market exposure via ETF (holdings-based)
    """
    # Hard links
    CITES = "CITES"
    IMPLEMENTS = "IMPLEMENTS"
    IMPOSES = "IMPOSES"
    APPLIES_TO = "APPLIES_TO"
    # Soft links
    MENTIONS = "MENTIONS"
    EXPOSES = "EXPOSES"
    # Negative links (explicit exclusion)
    NOT_RELATED = "NOT_RELATED"

    @property
    def is_hard(self) -> bool:
        return self in (
            EdgeType.CITES,
            EdgeType.IMPLEMENTS,
            EdgeType.IMPOSES,
            EdgeType.APPLIES_TO,
        )

    @property
    def is_soft(self) -> bool:
        return self in (EdgeType.MENTIONS, EdgeType.EXPOSES)

    @property
    def is_negative(self) -> bool:
        return self == EdgeType.NOT_RELATED


class EvidenceType(str, Enum):
    """How an edge was established."""
    CITATION = "citation"       # explicit USC/CFR reference in text
    DEFINITION = "definition"   # "covered entity means..." clause
    KEYWORD = "keyword"         # TF-IDF / regex match
    METADATA = "metadata"       # agency slug, CFR title, etc.
    EMBEDDING = "embedding"     # semantic similarity score
    HOLDINGS = "holdings"       # ETF constituent weights
    LLM = "llm"                 # LLM zero-shot classification
    MANUAL = "manual"           # human reviewer


class ObligationType(str, Enum):
    """Character of the obligation (stored as Obligation property, not edge).

    Gemini-style: these describe WHAT the regulation does,
    separate from HOW nodes are connected.
    """
    RESTRICTS = "RESTRICTS"         # tightens / limits
    MANDATES = "MANDATES"           # imposes affirmative duty
    SUBSIDIZES = "SUBSIDIZES"       # financial incentive / tax benefit
    EXEMPTS = "EXEMPTS"             # removes obligation
    PERMITS = "PERMITS"             # allows previously restricted activity
    MODIFIES_THRESHOLD = "MODIFIES_THRESHOLD"  # changes numeric limit


# ── Edge ────────────────────────────────────────────────────────────────

@dataclass
class Edge:
    """A connection between two nodes in the exposure graph.

    Every edge carries 4 mandatory fields per design principle §6:
        evidence_type, confidence, provenance, contamination_score

    Temporal fields:
        valid_from:  When this edge becomes effective (e.g., regulation effective date).
                     None = effective immediately / since creation.
        valid_until: When this edge expires (e.g., regulation repealed, sunset clause).
                     None = no known expiration (still active).
        superseded_by: ID of the edge that replaces this one (regulatory amendment chain).
    """
    source_id: str
    target_id: str
    edge_type: EdgeType
    evidence_type: EvidenceType
    confidence: float                       # 0.0–1.0
    provenance: str                         # source snippet or URL
    contamination_score: float = 0.0        # confounding events in window
    created_at: datetime = field(default_factory=datetime.utcnow)
    # Temporal dimension
    valid_from: Optional[date] = None       # None = effective since creation
    valid_until: Optional[date] = None      # None = no expiration
    superseded_by: Optional[str] = None     # edge or regulation ID that replaces this

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0–1, got {self.confidence}")
        if self.edge_type.is_hard and not self.edge_type.is_negative and self.confidence < 0.9:
            raise ValueError(
                f"Hard link {self.edge_type.value} requires confidence >= 0.9, "
                f"got {self.confidence}"
            )
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError(
                f"valid_from ({self.valid_from}) must be <= valid_until ({self.valid_until})"
            )

    def is_active_on(self, query_date: date) -> bool:
        """Check if this edge is active on a given date.

        An edge is active if:
          - query_date >= valid_from (or valid_from is None)
          - query_date <= valid_until (or valid_until is None)
          - The edge has not been superseded
        """
        if self.valid_from and query_date < self.valid_from:
            return False
        if self.valid_until and query_date > self.valid_until:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if this edge has passed its valid_until date."""
        if self.valid_until is None:
            return False
        return date.today() > self.valid_until

    @property
    def is_future(self) -> bool:
        """Check if this edge hasn't started yet."""
        if self.valid_from is None:
            return False
        return date.today() < self.valid_from


# ── Node Types (7-layer chain) ──────────────────────────────────────────

@dataclass
class Law:
    """Top-level legal authority (e.g., Clean Air Act, 42 USC §7401)."""
    id: str = field(default_factory=lambda: f"law-{uuid.uuid4().hex[:8]}")
    title: str = ""
    usc_cite: str = ""              # e.g., "42 USC §7401"
    public_law_number: str = ""     # e.g., "PL 117-169"
    jurisdiction: str = "US"
    enacted_date: Optional[date] = None


@dataclass
class Regulation:
    """Agency regulation implementing a law (e.g., 40 CFR Part 60)."""
    id: str = field(default_factory=lambda: f"reg-{uuid.uuid4().hex[:8]}")
    title: str = ""
    cfr_cite: str = ""              # e.g., "40 CFR 60"
    fr_doc_number: str = ""         # Federal Register document number
    agency_slug: str = ""           # e.g., "environmental-protection-agency"
    doc_type: str = ""              # RULE, PRORULE, NOTICE, PRESDOC
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    comment_end_date: Optional[date] = None
    significant: bool = False       # >$100M economic impact
    rin: str = ""                   # Regulation Identifier Number


@dataclass
class Provision:
    """Individual section/subsection where the diff actually occurs."""
    id: str = field(default_factory=lambda: f"prov-{uuid.uuid4().hex[:8]}")
    regulation_id: str = ""
    section: str = ""               # e.g., "§60.112a"
    title: str = ""
    diff_summary: str = ""          # plain-language change summary
    added_text: str = ""
    removed_text: str = ""


@dataclass
class Obligation:
    """What the provision requires or prohibits.

    obligation_type is the Gemini-style property (RESTRICTS, MANDATES, etc.)
    stored here, NOT as an edge type.
    """
    id: str = field(default_factory=lambda: f"obl-{uuid.uuid4().hex[:8]}")
    provision_id: str = ""
    obligation_type: ObligationType = ObligationType.MANDATES
    description: str = ""           # "shall file quarterly reports"
    mandatory_language: str = ""    # "shall", "must", "may not"
    penalty_mentioned: bool = False
    threshold_value: str = ""       # "$100M", "25MW", "10,000 tons"


@dataclass
class RegulatedEntityType:
    """Who bears the obligation (as described in regulation text).

    Examples: "bank holding company", "petroleum refinery with >25MW capacity",
    "covered entity under HIPAA".
    """
    id: str = field(default_factory=lambda: f"ent-{uuid.uuid4().hex[:8]}")
    description: str = ""           # verbatim from regulation text
    naics_codes: list[str] = field(default_factory=list)  # mapped NAICS
    sic_codes: list[str] = field(default_factory=list)    # mapped SIC


@dataclass
class Industry:
    """NAICS-based industry classification."""
    id: str = field(default_factory=lambda: f"ind-{uuid.uuid4().hex[:8]}")
    naics_code: str = ""            # e.g., "211110"
    naics_title: str = ""           # e.g., "Crude Petroleum Extraction"
    gics_sector: str = ""           # cross-reference (NAICS ≠ GICS)
    gics_code: str = ""


@dataclass
class ETFProxy:
    """Market proxy for observing industry exposure.

    ETFs are NOT regulated entities. They are baskets for market observation.
    Connection is always through Industry, never direct from Law/Regulation.
    """
    id: str = field(default_factory=lambda: f"etf-{uuid.uuid4().hex[:8]}")
    ticker: str = ""                # e.g., "XLE"
    name: str = ""                  # e.g., "Energy Select Sector SPDR"
    sector: str = ""                # broad label (for display only)
    exposure_score: float = 0.0     # Σ(weight × revenue_share)
    holdings_count: int = 0
    last_updated: Optional[date] = None


# ── Exposure Graph ──────────────────────────────────────────────────────

class ExposureGraph:
    """DAG of regulatory exposure relationships.

    Internal model is a DAG. UI shows highlighted paths.
    Enforces the "no direct Law→ETF link" principle.
    """

    # Allowed edge pairs (source_type → target_type)
    ALLOWED_EDGES: dict[EdgeType, tuple[type, type]] = {
        EdgeType.CITES:      (Law, Regulation),
        EdgeType.IMPLEMENTS: (Regulation, Law),
        EdgeType.IMPOSES:    (Provision, Obligation),
        EdgeType.APPLIES_TO: (Obligation, RegulatedEntityType),
        EdgeType.MENTIONS:   (RegulatedEntityType, Industry),
        EdgeType.EXPOSES:    (Industry, ETFProxy),
        # NOT_RELATED can link any pair in the lower chain (blocks exposure)
        # Validation is relaxed: source/target can be Regulation, Industry, or ETFProxy
    }

    def __init__(self):
        self.nodes: dict[str, object] = {}
        self.edges: list[Edge] = []

    def add_node(self, node) -> str:
        """Add a node and return its id."""
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, edge: Edge) -> None:
        """Add an edge with validation."""
        # Verify both nodes exist
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} not found")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node {edge.target_id} not found")

        # NOT_RELATED edges skip type validation (can link any pair)
        if not edge.edge_type.is_negative:
            source = self.nodes[edge.source_id]
            target = self.nodes[edge.target_id]
            allowed = self.ALLOWED_EDGES.get(edge.edge_type)
            if allowed:
                src_type, tgt_type = allowed
                if not isinstance(source, src_type):
                    raise TypeError(
                        f"{edge.edge_type.value} requires source type "
                        f"{src_type.__name__}, got {type(source).__name__}"
                    )
                if not isinstance(target, tgt_type):
                    raise TypeError(
                        f"{edge.edge_type.value} requires target type "
                        f"{tgt_type.__name__}, got {type(target).__name__}"
                    )

        self.edges.append(edge)

    def get_edges_from(self, node_id: str, as_of: Optional[date] = None) -> list[Edge]:
        """All edges originating from a node.

        Args:
            node_id: Source node ID
            as_of: If provided, only return edges active on this date
        """
        edges = [e for e in self.edges if e.source_id == node_id]
        if as_of is not None:
            edges = [e for e in edges if e.is_active_on(as_of)]
        return edges

    def get_edges_to(self, node_id: str, as_of: Optional[date] = None) -> list[Edge]:
        """All edges pointing to a node.

        Args:
            node_id: Target node ID
            as_of: If provided, only return edges active on this date
        """
        edges = [e for e in self.edges if e.target_id == node_id]
        if as_of is not None:
            edges = [e for e in edges if e.is_active_on(as_of)]
        return edges

    def trace_exposure(
        self, regulation_id: str, as_of: Optional[date] = None
    ) -> list[ETFProxy]:
        """Follow the full chain from a regulation to all exposed ETFs.

        Returns ETFProxy nodes reachable through the 7-layer chain.
        This is the core query: "Given this regulation, what ETFs are exposed?"

        Args:
            regulation_id: Starting regulation node ID
            as_of: If provided, only follow edges active on this date.
                   This enables point-in-time queries: "What was the exposure
                   on 2025-06-15?" vs "What is it now?"

        NOT_RELATED edges block paths: if a negative edge exists from any
        node in the chain to a target, that target is excluded.
        """
        # Build exclusion set: all (source, target) pairs with NOT_RELATED
        # that are active on the query date
        excluded_pairs: set[tuple[str, str]] = set()
        excluded_targets: set[str] = set()
        for edge in self.edges:
            if edge.edge_type.is_negative:
                if as_of is None or edge.is_active_on(as_of):
                    excluded_pairs.add((edge.source_id, edge.target_id))
                    if edge.source_id == regulation_id:
                        excluded_targets.add(edge.target_id)

        exposed: list[ETFProxy] = []
        visited: set[str] = set()

        def _walk(node_id: str, source_id: str = ""):
            if node_id in visited:
                return
            if (source_id, node_id) in excluded_pairs:
                return
            if node_id in excluded_targets:
                return
            visited.add(node_id)
            node = self.nodes.get(node_id)
            if isinstance(node, ETFProxy):
                exposed.append(node)
                return
            for edge in self.get_edges_from(node_id, as_of=as_of):
                if not edge.edge_type.is_negative:
                    _walk(edge.target_id, source_id=node_id)

        # Start from regulation → provisions → obligations → ... → ETFs
        for edge in self.get_edges_from(regulation_id, as_of=as_of):
            if not edge.edge_type.is_negative:
                _walk(edge.target_id, source_id=regulation_id)
        # Also walk provisions that belong to this regulation
        for nid, node in self.nodes.items():
            if isinstance(node, Provision) and node.regulation_id == regulation_id:
                _walk(nid, source_id=regulation_id)

        return exposed

    def get_exposure_path(
        self, regulation_id: str, etf_id: str
    ) -> list[tuple[object, Edge]]:
        """Return the full path from a regulation to an ETF.

        Used for explainability: "why is this ETF linked to this regulation?"
        Returns list of (node, edge_to_next) tuples.
        """
        # BFS to find shortest path
        from collections import deque

        queue: deque[list[str]] = deque([[regulation_id]])
        visited: set[str] = {regulation_id}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == etf_id:
                # Build result with nodes and edges
                result = []
                for i in range(len(path) - 1):
                    node = self.nodes[path[i]]
                    edge = next(
                        (e for e in self.edges
                         if e.source_id == path[i] and e.target_id == path[i + 1]),
                        None,
                    )
                    result.append((node, edge))
                result.append((self.nodes[etf_id], None))
                return result

            for edge in self.get_edges_from(current):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(path + [edge.target_id])

            # Also check provision→regulation link
            for nid, node in self.nodes.items():
                if (isinstance(node, Provision)
                        and node.regulation_id == current
                        and nid not in visited):
                    visited.add(nid)
                    queue.append(path + [nid])

        return []  # no path found

    # ── Summary / Stats ──────────────────────────────────────────────

    def summary(self) -> dict:
        """Quick stats about the graph."""
        type_counts: dict[str, int] = {}
        for node in self.nodes.values():
            name = type(node).__name__
            type_counts[name] = type_counts.get(name, 0) + 1

        hard = sum(1 for e in self.edges if e.edge_type.is_hard)
        soft = sum(1 for e in self.edges if e.edge_type.is_soft)
        negative = sum(1 for e in self.edges if e.edge_type.is_negative)
        temporal = sum(1 for e in self.edges if e.valid_from or e.valid_until)
        expired = sum(1 for e in self.edges if e.is_expired)
        future = sum(1 for e in self.edges if e.is_future)

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "hard_edges": hard,
            "soft_edges": soft,
            "negative_edges": negative,
            "temporal_edges": temporal,
            "expired_edges": expired,
            "future_edges": future,
            "node_types": type_counts,
        }
