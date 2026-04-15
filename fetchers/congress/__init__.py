"""Congress.gov data source — bill introductions, committee actions, votes.

Source: https://api.congress.gov/v3
Requires API key (free, or DEMO_KEY for testing).
"""

from fetchers.congress.client import CongressClient

__all__ = ["CongressClient"]
