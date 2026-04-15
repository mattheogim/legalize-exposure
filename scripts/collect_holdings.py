"""CLI for daily ETF holdings collection.

Usage:
    # Collect all ETFs
    python -m exposure.collect_holdings

    # Collect specific ETF
    python -m exposure.collect_holdings --ticker XLE

    # Force re-collect (even if today exists)
    python -m exposure.collect_holdings --force

    # Show storage summary
    python -m exposure.collect_holdings --summary

    # Show NAICS exposure for a snapshot
    python -m exposure.collect_holdings --ticker XLE --exposure
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from .holdings import HoldingsCollector, HoldingsStore


def main():
    parser = argparse.ArgumentParser(
        description="Legalize: Daily ETF Holdings Collector"
    )
    parser.add_argument(
        "--ticker", type=str, nargs="*",
        help="Specific ETF ticker(s) to collect (default: all)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-collect even if today's snapshot exists"
    )
    parser.add_argument(
        "--data-dir", type=str, default="holdings_data",
        help="Directory for holdings data (default: holdings_data)"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Show storage summary and exit"
    )
    parser.add_argument(
        "--exposure", action="store_true",
        help="Show NAICS exposure for latest snapshot"
    )
    parser.add_argument(
        "--history", action="store_true",
        help="Show snapshot history dates"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    store = HoldingsStore(args.data_dir)

    # Summary mode
    if args.summary:
        summary = store.summary()
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Holdings Data Summary")
            print(f"  Dates:       {summary['total_dates']}")
            print(f"  Range:       {summary['date_range']}")
            print(f"  ETFs tracked: {summary['etfs_tracked']}")
            print(f"  NAICS cache:  {summary['naics_cache_size']} companies")
            if summary['etf_snapshot_counts']:
                print(f"\n  Snapshots per ETF:")
                for ticker, count in sorted(summary['etf_snapshot_counts'].items()):
                    print(f"    {ticker:6s}: {count} snapshots")
        return

    # History mode
    if args.history:
        tickers = args.ticker or [None]
        for ticker in tickers:
            dates = store.get_available_dates(ticker)
            label = ticker or "all"
            print(f"{label}: {len(dates)} snapshots")
            for d in dates[-10:]:  # last 10
                print(f"  {d.isoformat()}")
        return

    # Exposure mode
    if args.exposure:
        if not args.ticker:
            print("Error: --exposure requires --ticker", file=sys.stderr)
            return
        for ticker in args.ticker:
            snap = store.get_latest_snapshot(ticker)
            if not snap:
                print(f"{ticker}: no snapshot found", file=sys.stderr)
                continue
            exposure = snap.naics_exposure()
            print(f"\n{ticker} ({snap.snapshot_date}, {snap.source}):")
            print(f"  Holdings: {snap.total_holdings}")
            print(f"  NAICS exposure:")
            for naics, weight in sorted(exposure.items(), key=lambda x: x[1], reverse=True):
                print(f"    {naics:8s}: {weight:.1%}")
        return

    # Collection mode
    collector = HoldingsCollector(store=store, throttle=0.5)

    if args.ticker:
        for ticker in args.ticker:
            print(f"Collecting {ticker}...", file=sys.stderr)
            snap = collector.collect_one(ticker, force=args.force)
            if snap:
                print(f"  ✓ {ticker}: {snap.total_holdings} holdings ({snap.source})")
            else:
                print(f"  ✗ {ticker}: failed", file=sys.stderr)
    else:
        print(f"Collecting all {len(collector.ALL_ETFS)} ETFs...", file=sys.stderr)
        results = collector.collect_all(force=args.force)
        print(f"\nCollected {len(results)}/{len(collector.ALL_ETFS)} ETFs")

        # Summary table
        print(f"\n{'Ticker':8s} {'Holdings':>8s} {'Source':20s} {'Top NAICS':30s}")
        print("-" * 70)
        for snap in sorted(results, key=lambda s: s.etf_ticker):
            exposure = snap.naics_exposure()
            top = sorted(exposure.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join(f"{n}({w:.0%})" for n, w in top)
            print(f"{snap.etf_ticker:8s} {snap.total_holdings:>8d} {snap.source:20s} {top_str}")


if __name__ == "__main__":
    main()
