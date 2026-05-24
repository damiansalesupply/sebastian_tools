from __future__ import annotations

from brawl_scraper.fetcher import FetchResult
from brawl_scraper.pipeline import run_scrape

from .conftest import FakeFetcher, load_fixture


def test_run_scrape_filters_and_reports() -> None:
    fetcher = FakeFetcher(
        {
            "sls.g2g.com": [FetchResult(url="u", status=200, text=load_fixture("g2g_search.json"))],
            "eldorado.gg": [FetchResult(url="u", status=200, text=load_fixture("eldorado_page.html"))],
            "playerauctions.com": [FetchResult(url="u", status=200, text=load_fixture("playerauctions_listing.html"))],
        }
    )
    report = run_scrape(
        sites=["g2g", "eldorado", "playerauctions"],
        query="brawl stars account",
        max_pages=2,
        fetcher=fetcher,
        save_all=True,
    )

    # 3 (g2g) + 2 (eldorado) + 2 (playerauctions) scanned; one match per site.
    assert report["stats"]["scanned"] == 7
    assert report["stats"]["matched"] == 3
    assert report["stats"]["per_site"]["g2g"] == {"scanned": 3, "matched": 1}
    assert len(report["matched_listings"]) == 3
    assert len(report["all_listings"]) == 7
    assert all(item["matches_filter"] for item in report["matched_listings"])


def test_run_scrape_without_save_all_omits_all_listings() -> None:
    fetcher = FakeFetcher({"sls.g2g.com": [FetchResult(url="u", status=200, text=load_fixture("g2g_search.json"))]})
    report = run_scrape(sites=["g2g"], query="brawl stars account", max_pages=1, fetcher=fetcher)
    assert "all_listings" not in report
    assert report["stats"]["matched"] == 1


def test_run_scrape_survives_unknown_site() -> None:
    fetcher = FakeFetcher({})
    # build_adapter raises for unknown site names; pipeline should let that surface clearly.
    try:
        run_scrape(sites=["nope"], query="x", max_pages=1, fetcher=fetcher)
    except ValueError as e:
        assert "Unknown site" in str(e)
    else:
        raise AssertionError("expected ValueError for unknown site")
