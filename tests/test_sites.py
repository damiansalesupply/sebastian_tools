from __future__ import annotations

from brawl_scraper.fetcher import FetchResult
from brawl_scraper.matcher import ColtChallengerMatcher
from brawl_scraper.sites import EldoradoSite, G2GSite, PlayerAuctionsSite

from .conftest import FakeFetcher, load_fixture

MATCHER = ColtChallengerMatcher()


def _matched_titles(listings: list) -> list[str]:
    return [listing.title for listing in listings if MATCHER.match(listing.searchable_text()).matched]


def test_g2g_parses_and_filters() -> None:
    fetcher = FakeFetcher({"sls.g2g.com": [FetchResult(url="u", status=200, text=load_fixture("g2g_search.json"))]})
    listings = list(G2GSite().iter_listings(fetcher, "brawl stars account", max_pages=2))

    assert len(listings) == 3
    first = listings[0]
    assert first.listing_id == "G1"
    assert first.price == 120.5
    assert first.currency == "USD"
    assert first.seller == "seller_one"
    assert first.url == "https://www.g2g.com/offer/brawl-stars-30k?id=G1"

    matched = _matched_titles(listings)
    assert matched == ["Brawl Stars account 30k trophies | Challenger Colt + Challenger Shelly"]


def test_eldorado_parses_next_data() -> None:
    fetcher = FakeFetcher({"eldorado.gg": [FetchResult(url="u", status=200, text=load_fixture("eldorado_page.html"))]})
    listings = list(EldoradoSite().iter_listings(fetcher, "brawl stars account", max_pages=2))

    assert len(listings) == 2
    e1 = listings[0]
    assert e1.listing_id == "E1"
    assert e1.price == 99.99
    assert e1.url == "https://www.eldorado.gg/offer/e1"
    assert e1.seller == "el_seller_a"

    assert _matched_titles(listings) == ["Brawl Stars Account - Challenger-Colt unlocked, 25k trophies"]


def test_playerauctions_parses_cards() -> None:
    fetcher = FakeFetcher(
        {"playerauctions.com": [FetchResult(url="u", status=200, text=load_fixture("playerauctions_listing.html"))]}
    )
    listings = list(PlayerAuctionsSite().iter_listings(fetcher, "brawl stars account", max_pages=2))

    assert len(listings) == 2
    p1 = listings[0]
    assert p1.price == 45.0
    assert p1.url == "https://www.playerauctions.com/brawl-stars-account/123"
    assert p1.seller == "pa_seller_a"

    matched = _matched_titles(listings)
    assert matched == ["Brawl Stars Account with Challenger Colt skin and 40k trophies"]


def test_g2g_stops_when_page_empty() -> None:
    # One page of data, then the FakeFetcher returns empty -> adapter must stop without erroring.
    fetcher = FakeFetcher({"sls.g2g.com": [FetchResult(url="u", status=200, text=load_fixture("g2g_search.json"))]})
    listings = list(G2GSite().iter_listings(fetcher, "brawl stars account", max_pages=5))
    assert len(listings) == 3
