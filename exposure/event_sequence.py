"""Multi-event regulatory timeline tracker.

Tracks the full regulatory pipeline for a regulation:
  ANPRM → NPRM (Proposed Rule) → Comment Close → Final Rule → Effective Date

Matches proposed↔final rules via RIN (Regulation Identifier Number) or
Docket ID. Runs incremental event studies at each milestone.

Methodology: Schipper & Thompson (1983) multi-event framework.
[src:schipper-thompson-1983] — each stage gets a dummy variable,
measures incremental information at each milestone.

Usage:
    seq = EventSequenceTracker()
    timeline = seq.build_timeline(rin="3211-AA41")
    results = seq.run_multi_event_study(timeline, etf_tickers=["XLF"])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

FR_API_BASE = "https://www.federalregister.gov/api/v1"
_FIELDS = [
    "document_number", "type", "title", "publication_date",
    "effective_on", "comments_close_on", "docket_ids",
    "regulation_id_numbers", "cfr_references",
    "agency_names", "significant", "action", "abstract",
]


@dataclass
class RegulatoryMilestone:
    """A single milestone in the regulatory pipeline."""
    stage: str              # "ANPRM", "NPRM", "FINAL", "EFFECTIVE"
    date: date
    document_number: str = ""
    title: str = ""
    doc_type: str = ""      # "Proposed Rule", "Rule", etc.
    action: str = ""


@dataclass
class RegulatoryTimeline:
    """Full timeline for one regulation, linked by RIN or Docket ID."""
    rin: str = ""
    docket_id: str = ""
    title: str = ""
    agency: str = ""
    milestones: list[RegulatoryMilestone] = field(default_factory=list)

    @property
    def nprm_date(self) -> Optional[date]:
        for m in self.milestones:
            if m.stage == "NPRM":
                return m.date
        return None

    @property
    def final_date(self) -> Optional[date]:
        for m in self.milestones:
            if m.stage == "FINAL":
                return m.date
        return None

    @property
    def effective_date(self) -> Optional[date]:
        for m in self.milestones:
            if m.stage == "EFFECTIVE":
                return m.date
        return None

    @property
    def comment_close_date(self) -> Optional[date]:
        for m in self.milestones:
            if m.stage == "COMMENT_CLOSE":
                return m.date
        return None

    @property
    def stage_count(self) -> int:
        return len(self.milestones)

    def days_nprm_to_final(self) -> Optional[int]:
        if self.nprm_date and self.final_date:
            return (self.final_date - self.nprm_date).days
        return None

    def summary(self) -> str:
        lines = [f"Timeline: {self.title[:60]}"]
        lines.append(f"  RIN: {self.rin or 'N/A'} | Docket: {self.docket_id or 'N/A'}")
        for m in sorted(self.milestones, key=lambda x: x.date):
            lines.append(f"  {m.date.isoformat()} [{m.stage:14s}] {m.document_number}")
        days = self.days_nprm_to_final()
        if days is not None:
            lines.append(f"  NPRM → Final: {days} days")
        return "\n".join(lines)


@dataclass
class MultiEventResult:
    """Results from running event studies at each milestone."""
    timeline: RegulatoryTimeline
    stage_results: dict  # stage → EventStudyResult (from event_study.py)
    pre_event_car: Optional[float] = None  # [-60, -1] CAR for priced-in check


class EventSequenceTracker:
    """Tracks the full regulatory pipeline via FR API."""

    def __init__(self, rate_limit: float = 1.0):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "legalize-bot/1.0"
        self._rate_limit = rate_limit
        import time
        self._last_request = 0.0
        self._time = time

    def _wait(self):
        elapsed = self._time.monotonic() - self._last_request
        if elapsed < self._rate_limit:
            self._time.sleep(self._rate_limit - elapsed)
        self._last_request = self._time.monotonic()

    def _search(self, **conditions) -> list[dict]:
        """Search FR API with conditions."""
        self._wait()
        params = {"per_page": 20, "order": "oldest", "fields[]": _FIELDS}
        for k, v in conditions.items():
            params[f"conditions[{k}]"] = v
        try:
            resp = self._session.get(f"{FR_API_BASE}/documents.json", params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            logger.error("FR API search failed: %s", e)
            return []

    def build_timeline_by_rin(self, rin: str) -> RegulatoryTimeline:
        """Build a timeline for a regulation identified by RIN."""
        docs = self._search(**{"regulation_id_number": rin})
        return self._docs_to_timeline(docs, rin=rin)

    def build_timeline_by_docket(self, docket_id: str) -> RegulatoryTimeline:
        """Build a timeline for a regulation identified by Docket ID."""
        docs = self._search(**{"docket_id": docket_id})
        return self._docs_to_timeline(docs, docket_id=docket_id)

    def build_timeline_from_doc(self, document_number: str) -> RegulatoryTimeline:
        """Build a timeline starting from any document number.

        Fetches the document, extracts RIN/Docket, then searches for
        all related documents in the same rulemaking.
        """
        self._wait()
        try:
            resp = self._session.get(
                f"{FR_API_BASE}/documents/{document_number}.json",
                params={"fields[]": _FIELDS},
                timeout=15,
            )
            resp.raise_for_status()
            doc = resp.json()
        except Exception as e:
            logger.error("Failed to fetch document %s: %s", document_number, e)
            return RegulatoryTimeline()

        # Try RIN first, then Docket ID
        rins = doc.get("regulation_id_numbers", [])
        dockets = doc.get("docket_ids", [])

        if rins:
            return self.build_timeline_by_rin(rins[0])
        elif dockets:
            return self.build_timeline_by_docket(dockets[0])
        else:
            # Single document, no linked timeline
            return self._docs_to_timeline([doc])

    def _docs_to_timeline(
        self,
        docs: list[dict],
        rin: str = "",
        docket_id: str = "",
    ) -> RegulatoryTimeline:
        """Convert FR API documents into a RegulatoryTimeline."""
        timeline = RegulatoryTimeline(rin=rin, docket_id=docket_id)

        for doc in docs:
            doc_type = doc.get("type", "")
            pub_date_str = doc.get("publication_date", "")
            eff_date_str = doc.get("effective_on", "")
            comment_close_str = doc.get("comments_close_on", "")

            pub_date = _parse_date(pub_date_str)
            if not pub_date:
                continue

            if not timeline.title:
                timeline.title = doc.get("title", "")
            if not timeline.agency and doc.get("agency_names"):
                timeline.agency = doc["agency_names"][0]

            # Determine stage from document type
            stage = self._classify_stage(doc_type, doc.get("action", ""))

            timeline.milestones.append(RegulatoryMilestone(
                stage=stage,
                date=pub_date,
                document_number=doc.get("document_number", ""),
                title=doc.get("title", "")[:100],
                doc_type=doc_type,
                action=doc.get("action", "")[:80],
            ))

            # Add comment close as separate milestone
            comment_close = _parse_date(comment_close_str)
            if comment_close and stage == "NPRM":
                timeline.milestones.append(RegulatoryMilestone(
                    stage="COMMENT_CLOSE",
                    date=comment_close,
                    document_number=doc.get("document_number", ""),
                    title=f"Comment period closes: {doc.get('title', '')[:60]}",
                ))

            # Add effective date as separate milestone
            eff_date = _parse_date(eff_date_str)
            if eff_date and stage == "FINAL":
                timeline.milestones.append(RegulatoryMilestone(
                    stage="EFFECTIVE",
                    date=eff_date,
                    document_number=doc.get("document_number", ""),
                    title=f"Effective: {doc.get('title', '')[:60]}",
                ))

            # Extract RIN/docket if not already set
            if not timeline.rin:
                rins = doc.get("regulation_id_numbers", [])
                if rins:
                    timeline.rin = rins[0]
            if not timeline.docket_id:
                dockets = doc.get("docket_ids", [])
                if dockets:
                    timeline.docket_id = dockets[0]

        # Sort milestones chronologically
        timeline.milestones.sort(key=lambda m: m.date)
        return timeline

    @staticmethod
    def _classify_stage(doc_type: str, action: str) -> str:
        """Classify a document into a regulatory pipeline stage."""
        doc_type_upper = doc_type.upper().replace(" ", "")
        action_lower = action.lower()

        if doc_type_upper in ("PROPOSEDRULE", "PRORULE"):
            if "advance notice" in action_lower or "anprm" in action_lower:
                return "ANPRM"
            return "NPRM"
        elif doc_type_upper in ("RULE",):
            if "interim" in action_lower:
                return "INTERIM_FINAL"
            return "FINAL"
        elif doc_type_upper in ("NOTICE",):
            return "NOTICE"
        elif doc_type_upper in ("PRESDOC", "PRESIDENTIALDOCUMENT"):
            return "EXECUTIVE"
        return "OTHER"

    def run_multi_event_study(
        self,
        timeline: RegulatoryTimeline,
        etf_tickers: list[str],
        event_window: tuple[int, int] = (1, 1),
    ) -> MultiEventResult:
        """Run event studies at each milestone in the timeline.

        Returns a MultiEventResult with per-stage CAR measurements.
        [src:schipper-thompson-1983] Multi-event framework.
        """
        from exposure.event_study import EventStudyEngine

        engine = EventStudyEngine(event_window=event_window)
        stage_results = {}

        for milestone in timeline.milestones:
            if milestone.stage in ("NPRM", "FINAL", "EFFECTIVE", "COMMENT_CLOSE"):
                try:
                    result = engine.run_regulation_study(
                        etf_tickers=etf_tickers,
                        event_date=milestone.date,
                        regulation_title=f"[{milestone.stage}] {timeline.title[:50]}",
                    )
                    stage_results[milestone.stage] = result
                    logger.info(
                        "Stage %s (%s): %d ETFs studied",
                        milestone.stage, milestone.date, len(etf_tickers),
                    )
                except Exception as e:
                    logger.error("Event study failed for %s: %s", milestone.stage, e)

        # Pre-event diagnostic: [-60, -1] CAR before earliest milestone
        # [src:kothari-warner-2007] Check if information already priced in
        pre_car = None
        if timeline.milestones:
            earliest = timeline.milestones[0].date
            try:
                pre_engine = EventStudyEngine(event_window=(60, 1))
                pre_result = pre_engine.run_regulation_study(
                    etf_tickers=etf_tickers[:1],  # Just first ETF for quick check
                    event_date=earliest,
                    regulation_title=f"[PRE-EVENT] {timeline.title[:50]}",
                )
                if pre_result and hasattr(pre_result, "results") and pre_result.results:
                    pre_car = pre_result.results[0].car_pre
            except Exception:
                pass

        return MultiEventResult(
            timeline=timeline,
            stage_results=stage_results,
            pre_event_car=pre_car,
        )


def _parse_date(s: str | None) -> date | None:
    """Parse YYYY-MM-DD date string."""
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
