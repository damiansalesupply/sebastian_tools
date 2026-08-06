from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Listing(BaseModel):
    """A single account offer scraped from a marketplace, normalized across sites."""

    site: str
    listing_id: str | None = None
    title: str = ""
    description: str | None = None
    url: str | None = None
    price: float | None = None
    currency: str | None = None
    seller: str | None = None
    # Whether this listing matched the Challenger Colt filter, and which phrases triggered it.
    matches_filter: bool = False
    matched_terms: list[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=_utcnow)
    # Optional raw payload kept only when explicitly requested (debugging / re-parsing).
    raw: dict | None = None

    def searchable_text(self) -> str:
        """Text the skin filter runs against: title plus description."""
        return " ".join(p for p in (self.title, self.description) if p)
