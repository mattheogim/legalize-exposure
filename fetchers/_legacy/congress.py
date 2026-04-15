"""Congress.gov fetcher: Track US bill introductions and committee actions.

Stage 1 of the US legislative pipeline tracker.
Detects when bills are introduced, referred to committee, or pass committee.

Data source: Congress.gov API v3
  https://api.congress.gov/v3/bill
  https://api.congress.gov/v3/bill/{congress}/{type}/{number}/actions

Rate limit: 1000 requests/hour with API key, 100/hour with DEMO_KEY.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

from ..utils import ThrottledClient

logger = logging.getLogger(__name__)

# Constants
CONGRESS_API_BASE = "https://api.congress.gov/v3"
DEFAULT_API_KEY = "DEMO_KEY"  # Replace with real key for production

# Bill types that map to legislative activity
BILL_TYPES = {
    "hr": "House Bill",
    "s": "Senate Bill",
    "hjres": "House Joint Resolution",
    "sjres": "Senate Joint Resolution",
    "hconres": "House Concurrent Resolution",
    "sconres": "Senate Concurrent Resolution",
    "hres": "House Simple Resolution",
    "sres": "Senate Simple Resolution",
}

# Key action types we track
TRACKED_ACTIONS = {
    "IntroReferral",      # Bill introduced / referred to committee
    "Committee",          # Committee action (hearing, markup, reported)
    "Floor",              # Floor action (vote, passage)
    "BecameLaw",          # Signed into law
    "President",          # Presidential action (sign, veto)
    "Calendars",          # Placed on calendar
    "ResolvingDifferences",  # Conference committee
}


class BillInfo:
    """Represents a tracked bill and its status."""

    def __init__(
        self,
        congress: int,
        bill_type: str,
        number: int,
        title: str,
        introduced_date: Optional[date] = None,
        latest_action: str = "",
        latest_action_date: Optional[date] = None,
        sponsor: str = "",
        committees: list[str] | None = None,
        policy_area: str = "",
        url: str = "",
    ):
        self.congress = congress
        self.bill_type = bill_type
        self.number = number
        self.title = title
        self.introduced_date = introduced_date
        self.latest_action = latest_action
        self.latest_action_date = latest_action_date
        self.sponsor = sponsor
        self.committees = committees or []
        self.policy_area = policy_area
        self.url = url

    @property
    def identifier(self) -> str:
        return f"{self.bill_type.upper()}-{self.number}"

    @property
    def full_identifier(self) -> str:
        return f"{self.congress}-{self.bill_type}-{self.number}"

    def to_markdown(self) -> str:
        """Convert bill info to Markdown format."""
        lines = []
        lines.append(f"# {self.identifier} — {self.title}")
        lines.append("")

        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Congress | {self.congress}th |")
        lines.append(f"| Type | {BILL_TYPES.get(self.bill_type, self.bill_type)} |")
        lines.append(f"| Number | {self.number} |")
        if self.introduced_date:
            lines.append(f"| Introduced | {self.introduced_date.isoformat()} |")
        if self.sponsor:
            lines.append(f"| Sponsor | {self.sponsor} |")
        if self.policy_area:
            lines.append(f"| Policy Area | {self.policy_area} |")
        if self.committees:
            lines.append(f"| Committees | {', '.join(self.committees)} |")
        if self.latest_action:
            lines.append(f"| Latest Action | {self.latest_action} |")
        if self.latest_action_date:
            lines.append(f"| Action Date | {self.latest_action_date.isoformat()} |")
        if self.url:
            lines.append(f"| Source | [{self.url}]({self.url}) |")
        lines.append("")

        return "\n".join(lines)


class CongressFetcher:
    """Fetch and track US bills from Congress.gov API."""

    def __init__(self, api_key: Optional[str] = None, throttle: float = 0.5):
        self.api_key = api_key or os.environ.get("CONGRESS_API_KEY", DEFAULT_API_KEY)
        self.client = ThrottledClient(throttle=throttle)

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make an authenticated API request."""
        url = f"{CONGRESS_API_BASE}/{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key
        params["format"] = "json"
        return self.client.get_json(url, params=params)

    def fetch_recent_bills(
        self,
        congress: int = 119,
        bill_type: str = "hr",
        limit: int = 50,
        from_date: Optional[date] = None,
    ) -> list[BillInfo]:
        """Fetch recently introduced/updated bills.

        Args:
            congress: Congress number (119 = 2025-2026)
            bill_type: Bill type (hr, s, hjres, sjres, etc.)
            limit: Maximum bills to return
            from_date: Only return bills updated after this date
        """
        params = {"limit": min(limit, 250)}
        if from_date:
            params["fromDateTime"] = f"{from_date.isoformat()}T00:00:00Z"

        data = self._get(f"bill/{congress}/{bill_type}", params)
        bills = []

        for bill_data in data.get("bills", []):
            bill = self._parse_bill(bill_data, congress, bill_type)
            if bill:
                bills.append(bill)

        logger.info(f"Fetched {len(bills)} {bill_type.upper()} bills from {congress}th Congress")
        return bills

    def fetch_all_types(
        self,
        congress: int = 119,
        limit_per_type: int = 50,
        from_date: Optional[date] = None,
    ) -> list[BillInfo]:
        """Fetch recent bills of all types."""
        all_bills = []
        for bill_type in BILL_TYPES:
            try:
                bills = self.fetch_recent_bills(congress, bill_type, limit_per_type, from_date)
                all_bills.extend(bills)
            except Exception as e:
                logger.error(f"Failed to fetch {bill_type}: {e}")
        return all_bills

    def fetch_bill_actions(self, congress: int, bill_type: str, number: int) -> list[dict]:
        """Fetch the action history for a specific bill.

        Returns a list of actions with type, date, and description.
        Useful for tracking committee progress.
        """
        data = self._get(f"bill/{congress}/{bill_type}/{number}/actions")
        actions = []

        for action in data.get("actions", []):
            action_date = None
            if action.get("actionDate"):
                try:
                    action_date = datetime.strptime(action["actionDate"], "%Y-%m-%d").date()
                except ValueError:
                    pass

            actions.append({
                "date": action_date,
                "type": action.get("type", ""),
                "text": action.get("text", ""),
                "action_code": action.get("actionCode", ""),
                "source_system": action.get("sourceSystem", {}).get("name", ""),
            })

        return actions

    def fetch_bill_committees(self, congress: int, bill_type: str, number: int) -> list[str]:
        """Fetch committees associated with a bill."""
        data = self._get(f"bill/{congress}/{bill_type}/{number}/committees")
        committees = []
        for comm in data.get("committees", []):
            name = comm.get("name", "")
            if name:
                committees.append(name)
        return committees

    def detect_committee_passage(
        self,
        congress: int,
        bill_type: str,
        number: int,
    ) -> Optional[dict]:
        """Check if a bill has passed committee (reported out).

        Returns action dict if passed, None otherwise.
        Key indicators:
          - actionCode "5000" = Reported to Senate
          - actionCode "H11100" = Reported to House
          - text containing "Ordered to be Reported"
          - type == "Committee" with reporting language
        """
        actions = self.fetch_bill_actions(congress, bill_type, number)

        for action in actions:
            text = action.get("text", "").lower()
            code = action.get("action_code", "")

            # Reported out of committee
            if code in ("5000", "H11100", "H11200"):
                return action
            if "ordered to be reported" in text:
                return action
            if "reported" in text and action.get("type") == "Committee":
                return action

        return None

    def _parse_bill(self, data: dict, congress: int, bill_type: str) -> Optional[BillInfo]:
        """Parse a bill from the API response."""
        try:
            number = data.get("number")
            if number is None:
                return None

            title = data.get("title", f"{bill_type.upper()} {number}")

            introduced = None
            intro_str = data.get("introducedDate", "")
            if intro_str:
                try:
                    introduced = datetime.strptime(intro_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

            latest_action_text = ""
            latest_action_date = None
            la = data.get("latestAction", {})
            if la:
                latest_action_text = la.get("text", "")
                la_date = la.get("actionDate", "")
                if la_date:
                    try:
                        latest_action_date = datetime.strptime(la_date, "%Y-%m-%d").date()
                    except ValueError:
                        pass

            policy_area = ""
            pa = data.get("policyArea", {})
            if pa:
                policy_area = pa.get("name", "")

            url = data.get("url", f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{number}")

            return BillInfo(
                congress=congress,
                bill_type=bill_type,
                number=int(number),
                title=title,
                introduced_date=introduced,
                latest_action=latest_action_text,
                latest_action_date=latest_action_date,
                policy_area=policy_area,
                url=url,
            )
        except Exception as e:
            logger.error(f"Failed to parse bill: {e}")
            return None

    def save_bills(self, bills: list[BillInfo], output_dir: Path) -> int:
        """Save bills to Markdown files in the output directory.

        File naming: {congress}-{type}-{number}.md
        Returns number of files written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for bill in bills:
            filename = f"{bill.full_identifier}.md"
            filepath = output_dir / filename
            filepath.write_text(bill.to_markdown(), encoding="utf-8")
            count += 1
        logger.info(f"Saved {count} bill files to {output_dir}")
        return count

    def generate_tracker_report(self, bills: list[BillInfo]) -> str:
        """Generate a summary Markdown report of tracked bills.

        Groups by bill type and sorts by latest action date.
        """
        lines = []
        lines.append("# US Bill Tracker Report")
        lines.append(f"\n*Generated: {date.today().isoformat()}*\n")

        # Group by type
        by_type: dict[str, list[BillInfo]] = {}
        for bill in bills:
            by_type.setdefault(bill.bill_type, []).append(bill)

        for btype, type_bills in sorted(by_type.items()):
            type_name = BILL_TYPES.get(btype, btype)
            lines.append(f"## {type_name}s ({len(type_bills)})")
            lines.append("")
            lines.append("| Bill | Title | Introduced | Latest Action | Date |")
            lines.append("|------|-------|-----------|---------------|------|")

            # Sort by latest action date descending
            type_bills.sort(
                key=lambda b: b.latest_action_date or date.min, reverse=True
            )

            for bill in type_bills:
                intro = bill.introduced_date.isoformat() if bill.introduced_date else "—"
                la_date = bill.latest_action_date.isoformat() if bill.latest_action_date else "—"
                action = bill.latest_action[:60] + "..." if len(bill.latest_action) > 60 else bill.latest_action
                lines.append(f"| {bill.identifier} | {bill.title[:50]} | {intro} | {action} | {la_date} |")

            lines.append("")

        return "\n".join(lines)
