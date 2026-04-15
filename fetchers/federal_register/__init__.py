"""Federal Register data source — proposed rules, final rules, executive orders.

Source: https://www.federalregister.gov/api/v1
No authentication required.
"""

from fetchers.federal_register.client import FederalRegisterClient
from fetchers.federal_register.mapper import RegDocument

__all__ = ["FederalRegisterClient", "RegDocument"]
