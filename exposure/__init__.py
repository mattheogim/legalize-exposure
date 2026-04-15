"""Regulation-to-Exposure Mapping engine.

Maps regulatory events to affected industries and ETF proxies
using a 7-layer ontology:

    Law → Regulation → Provision → Obligation → EntityType → Industry → ETF

Design principles:
  - No direct Law→ETF links (ETFs are market proxies, not regulated entities)
  - Hard links (text-evidenced) vs soft links (inferred) are always separated
  - Every edge carries: evidence_type, confidence, provenance, contamination_score
  - LLM is a weak signal, not a final judge
"""

from .schema import (
    EdgeType,
    EvidenceType,
    ObligationType,
    Edge,
    Law,
    Regulation,
    Provision,
    Obligation,
    RegulatedEntityType,
    Industry,
    ETFProxy,
    ExposureGraph,
)
from .lookups import AgencyLookup, CFRLookup
from .etf_exposure import ETFExposureEngine
from .macro_calendar import MacroEventCalendar, MacroEventType, MacroEvent
from .fr_connector import FRExposureConnector, PipelineResult
from .batch import BatchProcessor

__all__ = [
    "EdgeType",
    "EvidenceType",
    "ObligationType",
    "Edge",
    "Law",
    "Regulation",
    "Provision",
    "Obligation",
    "RegulatedEntityType",
    "Industry",
    "ETFProxy",
    "ExposureGraph",
    "AgencyLookup",
    "CFRLookup",
    "ETFExposureEngine",
    "MacroEventCalendar",
    "MacroEventType",
    "MacroEvent",
    "FRExposureConnector",
    "PipelineResult",
    "BatchProcessor",
]
