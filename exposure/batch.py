"""Daily Batch Processing Pipeline.

Automated daily runner for the regulation→exposure mapping pipeline.
Designed to be cron-compatible: run once per day, skip already-processed
documents, save results, and produce daily reports.

Usage:
    # Process today's Federal Register documents
    python -m exposure.batch

    # Process a specific date
    python -m exposure.batch --date 2026-04-10

    # Process a date range
    python -m exposure.batch --from 2026-04-01 --to 2026-04-10

    # Include holdings collection
    python -m exposure.batch --collect-holdings

    # Dry run (fetch + map, don't save)
    python -m exposure.batch --dry-run

    # Force reprocess already-processed dates
    python -m exposure.batch --force

Cron example (run daily at 7am ET):
    0 7 * * 1-5 cd /path/to/project && python -m exposure.batch --collect-holdings >> logs/batch.log 2>&1

Output structure:
    batch_data/
    ├── runs/
    │   ├── 2026-04-10.json          # full results for that date
    │   ├── 2026-04-11.json
    │   └── ...
    ├── reports/
    │   ├── 2026-04-10.md            # markdown report
    │   └── ...
    ├── processed.json               # index of processed doc numbers
    └── run_log.json                 # execution history
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .fr_connector import FRExposureConnector, PipelineResult
from .pipeline import fetch_documents, FR_FIELDS
from .holdings import HoldingsCollector, HoldingsStore
from .macro_calendar import MacroEventCalendar

logger = logging.getLogger(__name__)


# ── State Tracking ────────────────────────────────────────────────────

@dataclass
class RunRecord:
    """Record of a single batch run."""
    run_date: str                  # ISO date of the run
    target_date: str               # ISO date being processed
    started_at: str                # ISO datetime
    finished_at: str = ""          # ISO datetime
    status: str = "running"        # running | completed | failed
    documents_fetched: int = 0
    documents_mapped: int = 0
    documents_skipped: int = 0     # already processed
    etfs_exposed: int = 0
    significant_count: int = 0
    error: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class ProcessedIndex:
    """Tracks which document numbers have been processed.

    Simple JSON set: {"doc_numbers": ["2026-12345", ...], "last_updated": "..."}
    """

    def __init__(self, path: Path):
        self._path = path
        self._doc_numbers: set[str] = set()
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._doc_numbers = set(data.get("doc_numbers", []))
            except (json.JSONDecodeError, IOError):
                self._doc_numbers = set()

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "doc_numbers": sorted(self._doc_numbers),
            "count": len(self._doc_numbers),
            "last_updated": datetime.now().isoformat(),
        }
        self._path.write_text(json.dumps(data, indent=2))

    def is_processed(self, doc_number: str) -> bool:
        return doc_number in self._doc_numbers

    def mark_processed(self, doc_numbers: list[str]):
        self._doc_numbers.update(doc_numbers)
        self._save()

    @property
    def count(self) -> int:
        return len(self._doc_numbers)


class RunLog:
    """Append-only log of batch runs."""

    def __init__(self, path: Path):
        self._path = path
        self._records: list[dict] = []
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                self._records = json.loads(self._path.read_text())
            except (json.JSONDecodeError, IOError):
                self._records = []

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._records, indent=2))

    def append(self, record: RunRecord):
        self._records.append(record.to_dict())
        self._save()

    def last_successful_date(self) -> Optional[date]:
        """Find the most recent successfully processed target date."""
        for rec in reversed(self._records):
            if rec.get("status") == "completed":
                try:
                    return date.fromisoformat(rec["target_date"])
                except (ValueError, KeyError):
                    continue
        return None

    @property
    def total_runs(self) -> int:
        return len(self._records)


# ── Batch Processor ───────────────────────────────────────────────────

class BatchProcessor:
    """Daily batch processor for Federal Register → Exposure pipeline.

    Handles:
      - Fetching new documents for a target date
      - Deduplication via processed index
      - Mapping through the exposure engine
      - Saving results as JSON + Markdown reports
      - Optional holdings collection
      - Run logging and state tracking

    Usage:
        processor = BatchProcessor(data_dir="batch_data")

        # Process today
        record = processor.process_date(date.today())

        # Process a range
        records = processor.process_range(start, end)
    """

    def __init__(
        self,
        data_dir: str | Path = "batch_data",
        holdings_dir: str | Path = "holdings_data",
        min_etfs: int = 0,
        collect_holdings: bool = False,
    ):
        self._data_dir = Path(data_dir)
        self._runs_dir = self._data_dir / "runs"
        self._reports_dir = self._data_dir / "reports"
        self._index = ProcessedIndex(self._data_dir / "processed.json")
        self._run_log = RunLog(self._data_dir / "run_log.json")
        self._connector = FRExposureConnector()
        self._min_etfs = min_etfs
        self._collect_holdings = collect_holdings
        self._holdings_dir = Path(holdings_dir)

        # Ensure directories
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def process_date(
        self,
        target_date: date,
        force: bool = False,
        dry_run: bool = False,
        doc_types: list[str] | None = None,
    ) -> RunRecord:
        """Process all Federal Register documents for a given date.

        Args:
            target_date: Date to process
            force: Reprocess even if documents were already processed
            dry_run: Fetch and map but don't save results
            doc_types: Filter by document type (default: RULE + PRORULE)

        Returns:
            RunRecord with stats about this run
        """
        record = RunRecord(
            run_date=date.today().isoformat(),
            target_date=target_date.isoformat(),
            started_at=datetime.now().isoformat(),
        )
        start_time = time.time()

        if doc_types is None:
            doc_types = ["RULE", "PRORULE"]

        try:
            # ── Step 1: Collect holdings if requested ──
            if self._collect_holdings and not dry_run:
                self._run_holdings_collection()

            # ── Step 2: Fetch documents from FR API ──
            logger.info(f"Fetching FR documents for {target_date.isoformat()}...")
            documents = fetch_documents(
                doc_types=doc_types,
                from_date=target_date,
                to_date=target_date,
                per_page=200,
            )
            record.documents_fetched = len(documents)
            logger.info(f"  Fetched {len(documents)} documents")

            if not documents:
                record.status = "completed"
                record.finished_at = datetime.now().isoformat()
                record.duration_seconds = time.time() - start_time
                if not dry_run:
                    self._run_log.append(record)
                return record

            # ── Step 3: Deduplicate ──
            if force:
                new_docs = documents
            else:
                new_docs = [
                    d for d in documents
                    if not self._index.is_processed(d.get("document_number", ""))
                ]
                record.documents_skipped = len(documents) - len(new_docs)

            if record.documents_skipped > 0:
                logger.info(f"  Skipped {record.documents_skipped} already-processed")

            if not new_docs:
                record.status = "completed"
                record.finished_at = datetime.now().isoformat()
                record.duration_seconds = time.time() - start_time
                if not dry_run:
                    self._run_log.append(record)
                return record

            # ── Step 4: Map through exposure engine ──
            logger.info(f"  Mapping {len(new_docs)} documents...")
            results = self._connector.map_batch(new_docs, min_etfs=self._min_etfs)
            record.documents_mapped = len(results)

            # Collect stats
            all_etfs = set()
            for r in results:
                all_etfs.update(r.etf_tickers)
            record.etfs_exposed = len(all_etfs)
            record.significant_count = sum(1 for r in results if r.significant)

            logger.info(
                f"  Mapped {len(results)} → {len(all_etfs)} ETFs, "
                f"{record.significant_count} significant"
            )

            # ── Step 5: Save results ──
            if not dry_run:
                self._save_results(target_date, results, new_docs)
                self._save_report(target_date, results)

                # Mark as processed
                processed_nums = [
                    d.get("document_number", "")
                    for d in new_docs
                    if d.get("document_number")
                ]
                self._index.mark_processed(processed_nums)

            record.status = "completed"

        except Exception as e:
            record.status = "failed"
            record.error = str(e)
            logger.error(f"Batch processing failed: {e}")

        record.finished_at = datetime.now().isoformat()
        record.duration_seconds = round(time.time() - start_time, 2)

        if not dry_run:
            self._run_log.append(record)

        return record

    def process_range(
        self,
        start: date,
        end: date,
        force: bool = False,
        dry_run: bool = False,
        doc_types: list[str] | None = None,
    ) -> list[RunRecord]:
        """Process a range of dates.

        Skips weekends (FR doesn't publish on weekends).
        """
        records = []
        current = start

        while current <= end:
            # Skip weekends (FR doesn't publish Sat/Sun)
            if current.weekday() < 5:
                record = self.process_date(
                    current,
                    force=force,
                    dry_run=dry_run,
                    doc_types=doc_types,
                )
                records.append(record)
                self._print_record(record)
            current += timedelta(days=1)

        return records

    def process_since_last(
        self,
        dry_run: bool = False,
        doc_types: list[str] | None = None,
    ) -> list[RunRecord]:
        """Process all dates since the last successful run.

        Useful for catch-up after downtime.
        """
        last = self._run_log.last_successful_date()
        if last:
            start = last + timedelta(days=1)
        else:
            # First run: just do today
            start = date.today()

        end = date.today()

        if start > end:
            logger.info("Already up to date, nothing to process")
            return []

        logger.info(f"Catching up from {start} to {end}")
        return self.process_range(start, end, dry_run=dry_run, doc_types=doc_types)

    # ── Private helpers ───────────────────────────────────────────────

    def _run_holdings_collection(self):
        """Trigger daily holdings snapshot collection."""
        try:
            store = HoldingsStore(self._holdings_dir)
            collector = HoldingsCollector(store=store, throttle=0.5)
            results = collector.collect_all(force=False)
            logger.info(f"  Holdings: collected {len(results)} ETF snapshots")
        except Exception as e:
            logger.warning(f"  Holdings collection failed (non-fatal): {e}")

    def _save_results(
        self, target_date: date, results: list[PipelineResult], raw_docs: list[dict]
    ):
        """Save mapping results as JSON."""
        output = {
            "date": target_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "total_documents": len(raw_docs),
            "mapped_documents": len(results),
            "results": [],
        }

        for r in results:
            entry = {
                "document_number": r.document_number,
                "title": r.title,
                "doc_type": r.doc_type,
                "agency": r.agency_slug,
                "agency_display": r.agency_display,
                "publication_date": (
                    r.publication_date.isoformat() if r.publication_date else None
                ),
                "significant": r.significant,
                "industries": [
                    {"naics": i.naics_code, "title": i.naics_title}
                    for i in r.mapping.industries
                ],
                "etfs": r.etf_tickers,
                "etf_count": r.etf_count,
                "industry_count": r.industry_count,
                "contamination_score": r.contamination_score,
                "contamination_events": r.contamination_events,
                "html_url": r.html_url,
            }

            # Add summary if available
            if r.summary:
                entry["summary"] = {
                    "headline": r.summary.headline,
                    "brief": r.summary.brief,
                    "detailed": r.summary.detailed,
                    "action_verb": r.summary.action_verb,
                    "regulated_entities": r.summary.regulated_entities,
                    "key_change": r.summary.key_change,
                    "timeline": r.summary.timeline,
                    "tags": r.summary.tags,
                }

            output["results"].append(entry)

        # Save
        out_path = self._runs_dir / f"{target_date.isoformat()}.json"
        out_path.write_text(json.dumps(output, indent=2))
        logger.info(f"  Saved results to {out_path}")

    def _save_report(self, target_date: date, results: list[PipelineResult]):
        """Save Markdown report."""
        report = self._connector.generate_report(results)

        # Prepend date header
        header = f"# Daily Report: {target_date.isoformat()}\n\n"
        report = header + report

        out_path = self._reports_dir / f"{target_date.isoformat()}.md"
        out_path.write_text(report)
        logger.info(f"  Saved report to {out_path}")

    def _print_record(self, record: RunRecord):
        """Print a summary line for a run record."""
        status_icon = "✓" if record.status == "completed" else "✗"
        print(
            f"  {status_icon} {record.target_date}: "
            f"{record.documents_mapped}/{record.documents_fetched} mapped, "
            f"{record.etfs_exposed} ETFs, "
            f"{record.significant_count} significant, "
            f"{record.documents_skipped} skipped "
            f"({record.duration_seconds:.1f}s)",
            file=sys.stderr,
        )

    # ── Status / Summary ──────────────────────────────────────────────

    def status(self) -> dict:
        """Return current batch processor status."""
        last_date = self._run_log.last_successful_date()
        return {
            "data_dir": str(self._data_dir),
            "total_runs": self._run_log.total_runs,
            "documents_processed": self._index.count,
            "last_successful_date": last_date.isoformat() if last_date else None,
            "days_behind": (date.today() - last_date).days if last_date else None,
            "runs_dir": str(self._runs_dir),
            "reports_dir": str(self._reports_dir),
        }

    def load_results(self, target_date: date) -> Optional[dict]:
        """Load saved results for a date."""
        path = self._runs_dir / f"{target_date.isoformat()}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Legalize: Daily Batch Processor"
    )
    parser.add_argument(
        "--date", type=str,
        help="Process a specific date (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--from", dest="from_date", type=str,
        help="Start date for range processing (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to", dest="to_date", type=str,
        help="End date for range processing (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--catch-up", action="store_true",
        help="Process all dates since last successful run"
    )
    parser.add_argument(
        "--type", nargs="+", choices=["RULE", "PRORULE", "NOTICE", "PRESDOC"],
        help="Document types (default: RULE PRORULE)"
    )
    parser.add_argument(
        "--min-etfs", type=int, default=0,
        help="Minimum ETF matches to include (default: 0 = all)"
    )
    parser.add_argument(
        "--collect-holdings", action="store_true",
        help="Also collect daily ETF holdings snapshots"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Reprocess already-processed documents"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and map but don't save results"
    )
    parser.add_argument(
        "--data-dir", type=str, default="batch_data",
        help="Directory for batch data (default: batch_data)"
    )
    parser.add_argument(
        "--holdings-dir", type=str, default="holdings_data",
        help="Directory for holdings data (default: holdings_data)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show batch processor status and exit"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    processor = BatchProcessor(
        data_dir=args.data_dir,
        holdings_dir=args.holdings_dir,
        min_etfs=args.min_etfs,
        collect_holdings=args.collect_holdings,
    )

    # Status mode
    if args.status:
        status = processor.status()
        print(json.dumps(status, indent=2))
        return

    # Catch-up mode
    if args.catch_up:
        records = processor.process_since_last(
            dry_run=args.dry_run,
            doc_types=args.type,
        )
        _print_summary(records)
        return

    # Range mode
    if args.from_date:
        start = date.fromisoformat(args.from_date)
        end = date.fromisoformat(args.to_date) if args.to_date else date.today()
        records = processor.process_range(
            start, end,
            force=args.force,
            dry_run=args.dry_run,
            doc_types=args.type,
        )
        _print_summary(records)
        return

    # Single date mode
    target = date.fromisoformat(args.date) if args.date else date.today()
    record = processor.process_date(
        target,
        force=args.force,
        dry_run=args.dry_run,
        doc_types=args.type,
    )
    processor._print_record(record)

    if record.status == "failed":
        print(f"\nError: {record.error}", file=sys.stderr)
        sys.exit(1)


def _print_summary(records: list[RunRecord]):
    """Print summary of a multi-day batch run."""
    if not records:
        print("No dates to process.", file=sys.stderr)
        return

    total_fetched = sum(r.documents_fetched for r in records)
    total_mapped = sum(r.documents_mapped for r in records)
    total_skipped = sum(r.documents_skipped for r in records)
    failed = [r for r in records if r.status == "failed"]
    total_time = sum(r.duration_seconds for r in records)

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Batch Run Summary", file=sys.stderr)
    print(f"  Days processed:   {len(records)}", file=sys.stderr)
    print(f"  Documents fetched: {total_fetched}", file=sys.stderr)
    print(f"  Documents mapped:  {total_mapped}", file=sys.stderr)
    print(f"  Documents skipped: {total_skipped}", file=sys.stderr)
    print(f"  Failed runs:       {len(failed)}", file=sys.stderr)
    print(f"  Total time:        {total_time:.1f}s", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
