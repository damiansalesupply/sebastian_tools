from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..fetcher import HybridFetcher
from ..models import Listing


def to_float(value: object) -> float | None:
    """Best-effort parse of a price that may arrive as a number or a string like ``"$12.50"``."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    cleaned = "".join(c for c in s if c.isdigit() or c in ".,")
    if not cleaned:
        return None
    # If both separators appear, assume the last one is the decimal point.
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "") if cleaned.rfind(".") > cleaned.rfind(",") else cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


class SiteAdapter(ABC):
    """One marketplace. Subclasses know how to query it and parse its results into Listings.

    Endpoints and selectors are defined as defaults but can be overridden per-site via the
    config dict (see ``brawl_config.yml``), because marketplace markup/APIs change over time
    and should be tunable without editing code.
    """

    name: str = "base"

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def iter_listings(self, fetcher: HybridFetcher, query: str, max_pages: int) -> Iterator[Listing]:
        ...
