from __future__ import annotations

from brawl_scraper.models import Listing


def test_searchable_text_joins_title_and_description() -> None:
    listing = Listing(site="g2g", title="Brawl Stars account", description="Challenger Colt included")
    assert listing.searchable_text() == "Brawl Stars account Challenger Colt included"


def test_searchable_text_handles_missing_description() -> None:
    listing = Listing(site="g2g", title="Only title")
    assert listing.searchable_text() == "Only title"


def test_model_dump_is_json_serializable() -> None:
    listing = Listing(site="g2g", title="x", price=12.5, currency="USD", matches_filter=True, matched_terms=["challenger colt"])
    dumped = listing.model_dump(mode="json", exclude_none=True)
    assert dumped["price"] == 12.5
    assert dumped["matches_filter"] is True
    assert "scraped_at" in dumped
    assert "description" not in dumped  # excluded because None
