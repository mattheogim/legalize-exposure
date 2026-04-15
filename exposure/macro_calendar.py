"""FOMC + Macro Event Calendar for Contamination Scoring.

Design principle §10: Market data is context layer only.
Design principle §6: Every edge carries a contamination_score.

contamination_score answers: "Was a major macro event happening in the
same window as this regulatory event?" If yes, any observed market
movement is confounded — the regulation's effect can't be isolated.

Usage:
    calendar = MacroEventCalendar()

    # Check if a date window is contaminated
    score = calendar.contamination_score(
        event_date=date(2026, 3, 19),
        window_days=5,
    )
    # → 0.8 (high: FOMC decision on March 18)

    # Get all events in a window
    events = calendar.events_in_window(
        start=date(2026, 3, 15),
        end=date(2026, 3, 25),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Optional


class MacroEventType(str, Enum):
    """Categories of macro events that confound regulation analysis."""
    FOMC_DECISION = "FOMC_DECISION"           # rate decision day
    FOMC_MINUTES = "FOMC_MINUTES"             # minutes release (~3 weeks after)
    FOMC_SPEECH = "FOMC_SPEECH"               # Chair press conference
    NFP = "NFP"                               # Non-Farm Payrolls (1st Friday)
    CPI = "CPI"                               # Consumer Price Index
    PPI = "PPI"                               # Producer Price Index
    GDP = "GDP"                               # GDP release (advance/prelim/final)
    EARNINGS_SEASON = "EARNINGS_SEASON"       # major earnings window
    JOBS_REPORT = "JOBS_REPORT"               # weekly claims, JOLTS
    RETAIL_SALES = "RETAIL_SALES"             # Census Bureau retail
    ISM_PMI = "ISM_PMI"                       # ISM Manufacturing/Services PMI
    TRADE_BALANCE = "TRADE_BALANCE"           # international trade data
    HOUSING = "HOUSING"                       # housing starts, existing home sales
    CONSUMER_CONFIDENCE = "CONSUMER_CONFIDENCE"  # Conference Board / U of M
    DEBT_CEILING = "DEBT_CEILING"             # debt limit events
    GOVERNMENT_SHUTDOWN = "GOVERNMENT_SHUTDOWN"  # shutdown threats
    GEOPOLITICAL = "GEOPOLITICAL"             # major geopolitical events


@dataclass(frozen=True)
class MacroEvent:
    """A single macro event that may contaminate regulatory analysis."""
    event_type: MacroEventType
    event_date: date
    title: str
    severity: float             # 0.0–1.0 (how much it moves markets)
    sector_specific: bool       # True = affects specific sectors only
    affected_sectors: tuple[str, ...] = ()  # GICS sectors, if sector_specific
    recurring: bool = True      # part of regular schedule
    notes: str = ""


# ── FOMC Meeting Schedule ──────────────────────────────────────────────
# Source: Federal Reserve Board published schedule.
# 2025–2026 FOMC dates (decision day = day 2 of 2-day meeting).

_FOMC_2025 = [
    date(2025, 1, 29),
    date(2025, 3, 19),
    date(2025, 5, 7),
    date(2025, 6, 18),
    date(2025, 7, 30),
    date(2025, 9, 17),
    date(2025, 10, 29),
    date(2025, 12, 17),
]

_FOMC_2026 = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 10, 28),
    date(2026, 12, 16),
]

# FOMC minutes release: approximately 3 weeks after decision
_FOMC_MINUTES_LAG_DAYS = 21


# ── Recurring Economic Data Releases (approximate schedule) ───────────
#
# These are generated programmatically for any year.
# Actual dates shift slightly — Phase 2 will use BLS/Census calendars.

def _generate_nfp_dates(year: int) -> list[date]:
    """Non-Farm Payrolls: 1st Friday of each month."""
    dates = []
    for month in range(1, 13):
        d = date(year, month, 1)
        # Find first Friday (weekday 4)
        days_until_friday = (4 - d.weekday()) % 7
        first_friday = d + timedelta(days=days_until_friday)
        dates.append(first_friday)
    return dates


def _generate_cpi_dates(year: int) -> list[date]:
    """CPI: ~10th-14th of each month (approx 2nd Tuesday/Wednesday)."""
    dates = []
    for month in range(1, 13):
        d = date(year, month, 1)
        # Approximate: 2nd Tuesday
        days_until_tuesday = (1 - d.weekday()) % 7
        second_tuesday = d + timedelta(days=days_until_tuesday + 7)
        dates.append(second_tuesday)
    return dates


def _generate_gdp_dates(year: int) -> list[date]:
    """GDP: Advance (~4th week of month after quarter ends).

    Q4 → late Jan, Q1 → late Apr, Q2 → late Jul, Q3 → late Oct
    """
    return [
        date(year, 1, 26),    # Q4 advance
        date(year, 4, 27),    # Q1 advance
        date(year, 7, 27),    # Q2 advance
        date(year, 10, 26),   # Q3 advance
    ]


def _generate_earnings_windows(year: int) -> list[tuple[date, date]]:
    """Major earnings season windows (roughly 3 weeks each).

    These are the peak periods when >30% of S&P 500 reports.
    """
    return [
        (date(year, 1, 13), date(year, 2, 7)),    # Q4 earnings
        (date(year, 4, 14), date(year, 5, 9)),     # Q1 earnings
        (date(year, 7, 14), date(year, 8, 8)),     # Q2 earnings
        (date(year, 10, 13), date(year, 11, 7)),   # Q3 earnings
    ]


def _generate_ism_dates(year: int) -> list[date]:
    """ISM Manufacturing PMI: 1st business day of each month."""
    dates = []
    for month in range(1, 13):
        d = date(year, month, 1)
        # Skip weekends
        while d.weekday() >= 5:  # Saturday=5, Sunday=6
            d += timedelta(days=1)
        dates.append(d)
    return dates


# ── Calendar Builder ───────────────────────────────────────────────────

def _build_events_for_year(year: int) -> list[MacroEvent]:
    """Generate all macro events for a given year."""
    events: list[MacroEvent] = []

    # FOMC decisions
    fomc_dates = {2025: _FOMC_2025, 2026: _FOMC_2026}.get(year, [])
    for d in fomc_dates:
        events.append(MacroEvent(
            event_type=MacroEventType.FOMC_DECISION,
            event_date=d,
            title=f"FOMC Rate Decision",
            severity=0.9,
            sector_specific=False,
        ))
        # Minutes release
        minutes_date = d + timedelta(days=_FOMC_MINUTES_LAG_DAYS)
        events.append(MacroEvent(
            event_type=MacroEventType.FOMC_MINUTES,
            event_date=minutes_date,
            title=f"FOMC Minutes Release ({d.isoformat()})",
            severity=0.5,
            sector_specific=False,
        ))

    # Non-Farm Payrolls
    for d in _generate_nfp_dates(year):
        events.append(MacroEvent(
            event_type=MacroEventType.NFP,
            event_date=d,
            title=f"Non-Farm Payrolls ({d.strftime('%B')})",
            severity=0.8,
            sector_specific=False,
        ))

    # CPI
    for d in _generate_cpi_dates(year):
        events.append(MacroEvent(
            event_type=MacroEventType.CPI,
            event_date=d,
            title=f"CPI Release ({d.strftime('%B')})",
            severity=0.7,
            sector_specific=False,
        ))

    # GDP
    for d in _generate_gdp_dates(year):
        quarter = {1: "Q4", 4: "Q1", 7: "Q2", 10: "Q3"}[d.month]
        events.append(MacroEvent(
            event_type=MacroEventType.GDP,
            event_date=d,
            title=f"GDP Advance Estimate ({quarter})",
            severity=0.7,
            sector_specific=False,
        ))

    # ISM PMI
    for d in _generate_ism_dates(year):
        events.append(MacroEvent(
            event_type=MacroEventType.ISM_PMI,
            event_date=d,
            title=f"ISM Manufacturing PMI ({d.strftime('%B')})",
            severity=0.5,
            sector_specific=False,
        ))

    # Earnings seasons (these are windows, so we create start/end markers)
    for start, end in _generate_earnings_windows(year):
        events.append(MacroEvent(
            event_type=MacroEventType.EARNINGS_SEASON,
            event_date=start,
            title=f"Earnings Season Start ({start.strftime('%B')})",
            severity=0.6,
            sector_specific=False,
            notes=f"Peak earnings window: {start.isoformat()} to {end.isoformat()}",
        ))
        events.append(MacroEvent(
            event_type=MacroEventType.EARNINGS_SEASON,
            event_date=end,
            title=f"Earnings Season End ({end.strftime('%B')})",
            severity=0.3,
            sector_specific=False,
        ))

    return sorted(events, key=lambda e: e.event_date)


class MacroEventCalendar:
    """Calendar of macro events for contamination scoring.

    Usage:
        cal = MacroEventCalendar()

        # Get contamination score for a regulatory event
        score = cal.contamination_score(date(2026, 3, 18), window_days=5)
        # → ~0.9 (FOMC decision on that exact day)

        # Get all events near a date
        events = cal.events_in_window(date(2026, 3, 15), date(2026, 3, 25))
    """

    def __init__(self, years: Optional[list[int]] = None):
        """Initialize with events for given years (default: 2025–2026)."""
        if years is None:
            years = [2025, 2026]
        self._events: list[MacroEvent] = []
        for year in years:
            self._events.extend(_build_events_for_year(year))
        self._events.sort(key=lambda e: e.event_date)
        # Earnings windows for fast lookup
        self._earnings_windows: list[tuple[date, date]] = []
        for year in years:
            self._earnings_windows.extend(_generate_earnings_windows(year))

    @property
    def events(self) -> list[MacroEvent]:
        """All events in the calendar, sorted by date."""
        return list(self._events)

    def events_in_window(
        self,
        start: date,
        end: date,
        event_types: Optional[list[MacroEventType]] = None,
    ) -> list[MacroEvent]:
        """Get all macro events between start and end dates (inclusive).

        Args:
            start: Window start date
            end: Window end date
            event_types: Filter to specific event types (None = all)
        """
        results = []
        for event in self._events:
            if event.event_date < start:
                continue
            if event.event_date > end:
                break  # events are sorted
            if event_types and event.event_type not in event_types:
                continue
            results.append(event)
        return results

    def _in_earnings_season(self, d: date) -> bool:
        """Check if a date falls within a major earnings window."""
        for start, end in self._earnings_windows:
            if start <= d <= end:
                return True
        return False

    def contamination_score(
        self,
        event_date: date,
        window_days: int = 5,
        exclude_types: Optional[list[MacroEventType]] = None,
    ) -> float:
        """Calculate contamination score for a regulatory event.

        Looks at macro events within ±window_days of event_date.
        Returns 0.0 (clean window) to 1.0 (heavily contaminated).

        The score is the MAX severity of any event in the window,
        with distance-based decay:
            adjusted_severity = severity × (1 - distance / (window_days + 1))

        This is conservative: even a single FOMC decision in the window
        makes the score high. Multiple events don't stack above 1.0.

        Args:
            event_date: The regulatory event publication date
            window_days: Days before/after to check (Event Study window)
            exclude_types: Event types to ignore (e.g., minor indicators)
        """
        if exclude_types is None:
            exclude_types = []

        start = event_date - timedelta(days=window_days)
        end = event_date + timedelta(days=window_days)
        events = self.events_in_window(start, end)

        max_score = 0.0
        for event in events:
            if event.event_type in exclude_types:
                continue
            distance = abs((event.event_date - event_date).days)
            # Decay: closer events have stronger contamination
            decay = 1.0 - (distance / (window_days + 1))
            adjusted = event.severity * decay
            max_score = max(max_score, adjusted)

        # Bonus if inside earnings season
        if self._in_earnings_season(event_date):
            max_score = max(max_score, 0.4)  # minimum 0.4 during earnings

        return min(max_score, 1.0)

    def find_clean_windows(
        self,
        start: date,
        end: date,
        window_days: int = 5,
        max_contamination: float = 0.3,
    ) -> list[date]:
        """Find dates in a range with low contamination scores.

        Useful for identifying ideal natural experiment dates where
        a regulatory event could be studied with minimal confounds.
        """
        clean = []
        current = start
        while current <= end:
            score = self.contamination_score(current, window_days)
            if score <= max_contamination:
                clean.append(current)
            current += timedelta(days=1)
        return clean

    def summary(self, year: int) -> dict:
        """Summary statistics for a given year."""
        year_events = [e for e in self._events if e.event_date.year == year]
        by_type: dict[str, int] = {}
        for e in year_events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
        return {
            "year": year,
            "total_events": len(year_events),
            "by_type": by_type,
            "highest_severity": max(
                (e.severity for e in year_events), default=0.0
            ),
        }
