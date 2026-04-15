"""Source registry — dynamic dispatch for exposure data sources.

Adapted from legalize-pipeline's countries.py pattern. Uses lazy imports
so startup only loads the sources that are actually used.

To add a new source:
1. Create fetchers/{source_name}/ with client.py, mapper.py
2. Register the import paths in SOURCES below
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fetchers.base import DataSourceClient

SOURCES: dict[str, dict[str, tuple[str, str]]] = {
    "federal_register": {
        "client": ("fetchers.federal_register.client", "FederalRegisterClient"),
    },
    "congress": {
        "client": ("fetchers.congress.client", "CongressClient"),
    },
    "courtlistener": {
        "client": ("fetchers.courtlistener.client", "CourtListenerClient"),
    },
    # Future sources:
    # "sec_edgar": {"client": ("fetchers.sec_edgar.client", "EdgarClient")},
    # "fred": {"client": ("fetchers.fred.client", "FredClient")},
}


def _import_class(module_path: str, class_name: str) -> Any:
    """Lazy import a class by module path and name."""
    module = import_module(module_path)
    return getattr(module, class_name)


def supported_sources() -> list[str]:
    """List of registered source names."""
    return sorted(SOURCES.keys())


def get_client_class(source: str) -> type[DataSourceClient]:
    """Get the client class for a source."""
    if source not in SOURCES:
        available = ", ".join(sorted(SOURCES.keys()))
        raise ValueError(f"Source '{source}' not registered. Available: {available}")
    module_path, class_name = SOURCES[source]["client"]
    return _import_class(module_path, class_name)
