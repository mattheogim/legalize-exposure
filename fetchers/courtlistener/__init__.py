"""CourtListener data source — US court opinions (SCOTUS + Circuit Courts).

Source: https://www.courtlistener.com/api/rest/v4/
Requires free API token.
"""

from fetchers.courtlistener.client import CourtListenerClient

__all__ = ["CourtListenerClient"]
