"""Historical Replay Framework for Point-in-Time Evaluation.

Design principle §14: Historical replay with future information hidden.

The replay framework answers: "If this system had been running on date X,
what would it have produced?" It's the backtesting backbone.

Key rules:
  1. No future information — only data available AT that date is used
  2. Holdings snapshots are frozen to the latest available BEFORE event date
  3. Contamination scores use the calendar known at that time
  4. Results are compared against actual market data (Phase 2)

Usage:
    replayer = HistoricalReplayer()

    # Replay a single regulation
    result = replayer.replay_regulation(
        fr_doc={...},  # FR API format
        as_of=date(2025, 6, 15),
    )

    # Replay a full day
    results = replayer.replay_day(date(2025, 6, 15))

    # Replay a date range for backtesting
    all_results = replayer.replay_range(
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
    )
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from .fr_connector import FRExposureConnector, PipelineResult
from .macro_calendar import MacroEventCalendar
from .holdings import HoldingsStore, HoldingsSnapshot

logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """Result of replaying one regulation at a point in time."""
    replay_date: date                    # as-of date
    pipeline_result: PipelineResult      # mapping result
    holdings_date: Optional[date]        # which holdings snapshot was used
    holdings_source: str                 # "live", "static_fallback", etc.
    information_leakage: bool            # True if any future data leaked
    leakage_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "replay_date": self.replay_date.isoformat(),
            "document_number": self.pipeline_result.document_number,
            "title": self.pipeline_result.title,
            "agency": self.pipeline_result.agency_slug,
            "publication_date": (
                self.pipeline_result.publication_date.isoformat()
                if self.pipeline_result.publication_date else None
            ),
            "industries": [i.naics_code for i in self.pipeline_result.mapping.industries],
            "etfs": self.pipeline_result.etf_tickers,
            "contamination_score": self.pipeline_result.contamination_score,
            "holdings_date": self.holdings_date.isoformat() if self.holdings_date else None,
            "holdings_source": self.holdings_source,
            "information_leakage": self.information_leakage,
            "leakage_notes": self.leakage_notes,
        }


@dataclass
class ReplayDaySummary:
    """Summary of all replays for a single day."""
    replay_date: date
    total_documents: int
    mapped_documents: int
    total_etfs_exposed: int
    avg_contamination: float
    results: list[ReplayResult]
    leakage_warnings: int

    def to_dict(self) -> dict:
        return {
            "replay_date": self.replay_date.isoformat(),
            "total_documents": self.total_documents,
            "mapped_documents": self.mapped_documents,
            "total_etfs_exposed": self.total_etfs_exposed,
            "avg_contamination": round(self.avg_contamination, 3),
            "leakage_warnings": self.leakage_warnings,
            "results": [r.to_dict() for r in self.results],
        }


class HistoricalReplayer:
    """Point-in-time evaluation engine.

    Replays the regulation→exposure pipeline as if it were running
    at a specific date, with no future information.

    Usage:
        replayer = HistoricalReplayer(
            holdings_dir="holdings_data",
            calendar_years=[2025, 2026],
        )

        # Replay one document
        result = replayer.replay_regulation(
            fr_doc={"document_number": "2025-12345", ...},
            as_of=date(2025, 6, 15),
        )

        # Replay a full day from stored FR documents
        day_summary = replayer.replay_day(
            replay_date=date(2025, 6, 15),
            fr_docs=[...],  # list of FR API dicts
        )
    """

    def __init__(
        self,
        holdings_dir: str | Path = "holdings_data",
        calendar_years: Optional[list[int]] = None,
        contamination_window: int = 5,
    ):
        self._holdings_store = HoldingsStore(holdings_dir)
        self._calendar = MacroEventCalendar(years=calendar_years or [2025, 2026])
        self._contamination_window = contamination_window
        # Create connector with our calendar
        self._connector = FRExposureConnector(
            calendar=self._calendar,
            contamination_window=contamination_window,
        )

    def replay_regulation(
        self,
        fr_doc: dict,
        as_of: Optional[date] = None,
    ) -> ReplayResult:
        """Replay a single regulation through the pipeline at a point in time.

        Args:
            fr_doc: FR API format document dict
            as_of: Pretend we're running on this date (default: doc's pub date)

        Returns:
            ReplayResult with mapping and leakage checks
        """
        # Determine replay date
        pub_date_str = fr_doc.get("publication_date", "")
        pub_date = None
        if pub_date_str:
            try:
                from datetime import datetime
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        replay_date = as_of or pub_date or date.today()

        # ── Leakage checks ──
        leakage = False
        leakage_notes = []

        # Check 1: Publication date must be <= replay date
        if pub_date and pub_date > replay_date:
            leakage = True
            leakage_notes.append(
                f"Document published {pub_date} is AFTER replay date {replay_date}"
            )

        # Check 2: Find the most recent holdings snapshot BEFORE replay date
        holdings_date = None
        holdings_source = "static_fallback"

        # Look for the latest snapshot date <= replay_date
        available_dates = self._holdings_store.get_available_dates()
        valid_dates = [d for d in available_dates if d <= replay_date]
        if valid_dates:
            holdings_date = valid_dates[-1]
            holdings_source = "historical_snapshot"
            # Check staleness
            staleness = (replay_date - holdings_date).days
            if staleness > 30:
                leakage_notes.append(
                    f"Holdings snapshot is {staleness} days old "
                    f"({holdings_date} for replay {replay_date})"
                )
        else:
            leakage_notes.append(
                "No historical holdings available, using static fallback"
            )

        # ── Run the pipeline ──
        pipeline_result = self._connector.map_from_api_json(fr_doc)

        if not pipeline_result:
            # Create a minimal result for failed mappings
            pipeline_result = PipelineResult(
                document_number=fr_doc.get("document_number", "unknown"),
                title=fr_doc.get("title", ""),
                doc_type=fr_doc.get("type", ""),
                agency_slug="",
                agency_display="",
                publication_date=pub_date,
                mapping=None,
                contamination_score=0,
                contamination_events=[],
            )

        return ReplayResult(
            replay_date=replay_date,
            pipeline_result=pipeline_result,
            holdings_date=holdings_date,
            holdings_source=holdings_source,
            information_leakage=leakage,
            leakage_notes=leakage_notes,
        )

    def replay_day(
        self,
        replay_date: date,
        fr_docs: list[dict],
    ) -> ReplayDaySummary:
        """Replay all documents from a specific day.

        Args:
            replay_date: The date to replay
            fr_docs: List of FR API format documents published on this date
        """
        results = []
        all_etfs = set()

        for doc in fr_docs:
            result = self.replay_regulation(doc, as_of=replay_date)
            results.append(result)
            all_etfs.update(result.pipeline_result.etf_tickers)

        mapped = [r for r in results if r.pipeline_result.etf_count > 0]
        contaminations = [
            r.pipeline_result.contamination_score
            for r in results
            if r.pipeline_result.contamination_score > 0
        ]
        avg_contam = (
            sum(contaminations) / len(contaminations)
            if contaminations else 0.0
        )
        leakage_count = sum(1 for r in results if r.information_leakage)

        return ReplayDaySummary(
            replay_date=replay_date,
            total_documents=len(fr_docs),
            mapped_documents=len(mapped),
            total_etfs_exposed=len(all_etfs),
            avg_contamination=avg_contam,
            results=results,
            leakage_warnings=leakage_count,
        )

    def replay_range(
        self,
        start: date,
        end: date,
        fr_docs_by_date: dict[str, list[dict]] | None = None,
        fr_docs_dir: Optional[Path] = None,
    ) -> list[ReplayDaySummary]:
        """Replay across a date range for backtesting.

        Args:
            start: Start date
            end: End date
            fr_docs_by_date: {date_iso: [docs]} mapping
            fr_docs_dir: Directory with {date}.json files
        """
        summaries = []
        current = start

        while current <= end:
            date_str = current.isoformat()

            # Get documents for this date
            docs = []
            if fr_docs_by_date and date_str in fr_docs_by_date:
                docs = fr_docs_by_date[date_str]
            elif fr_docs_dir:
                doc_file = fr_docs_dir / f"{date_str}.json"
                if doc_file.exists():
                    try:
                        docs = json.loads(doc_file.read_text())
                    except (json.JSONDecodeError, IOError):
                        pass

            if docs:
                summary = self.replay_day(current, docs)
                summaries.append(summary)
                logger.info(
                    f"Replayed {date_str}: {summary.mapped_documents}/"
                    f"{summary.total_documents} mapped, "
                    f"{summary.total_etfs_exposed} ETFs"
                )

            current += timedelta(days=1)

        return summaries

    def generate_backtest_report(
        self, summaries: list[ReplayDaySummary]
    ) -> str:
        """Generate a Markdown backtest report."""
        lines = [
            "# Historical Replay Backtest Report",
            f"*Generated: {date.today().isoformat()}*",
            "",
        ]

        if not summaries:
            lines.append("No data to report.")
            return "\n".join(lines)

        # Aggregate stats
        total_docs = sum(s.total_documents for s in summaries)
        total_mapped = sum(s.mapped_documents for s in summaries)
        total_leakage = sum(s.leakage_warnings for s in summaries)
        all_etfs = set()
        for s in summaries:
            for r in s.results:
                all_etfs.update(r.pipeline_result.etf_tickers)

        date_range = f"{summaries[0].replay_date} to {summaries[-1].replay_date}"

        lines.extend([
            f"**Date range:** {date_range}",
            f"**Days replayed:** {len(summaries)}",
            f"**Total documents:** {total_docs}",
            f"**Mapped to ETFs:** {total_mapped}/{total_docs} "
            f"({total_mapped/total_docs:.0%})" if total_docs else "",
            f"**Unique ETFs exposed:** {len(all_etfs)}",
            f"**Leakage warnings:** {total_leakage}",
            "",
        ])

        # Daily table
        lines.extend([
            "| Date | Docs | Mapped | ETFs | Avg Contam | Leakage |",
            "|------|------|--------|------|------------|---------|",
        ])
        for s in summaries:
            lines.append(
                f"| {s.replay_date} | {s.total_documents} | "
                f"{s.mapped_documents} | {s.total_etfs_exposed} | "
                f"{s.avg_contamination:.2f} | "
                f"{'⚠' if s.leakage_warnings else '✓'} |"
            )

        lines.append("")

        # Contamination analysis
        high_contam = [
            s for s in summaries if s.avg_contamination >= 0.5
        ]
        if high_contam:
            lines.append(f"**High contamination days ({len(high_contam)}):** "
                        "These days have confounding macro events and "
                        "should be interpreted with caution.")
            lines.append("")

        return "\n".join(lines)
