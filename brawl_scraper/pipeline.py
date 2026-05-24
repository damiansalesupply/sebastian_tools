from __future__ import annotations

from datetime import datetime, timezone

from tqdm import tqdm

from base.logger import logger

from .fetcher import HybridFetcher
from .matcher import ColtChallengerMatcher
from .models import Listing
from .sites import build_adapter


def run_scrape(
    *,
    sites: list[str],
    query: str,
    max_pages: int,
    config: dict | None = None,
    matcher: ColtChallengerMatcher | None = None,
    allow_browser: bool = True,
    save_all: bool = False,
    fetcher: HybridFetcher | None = None,
) -> dict:
    """Scrape the given sites, tag each listing with the Challenger Colt filter, and return a report.

    The returned dict always includes the matched listings and per-site stats; when ``save_all`` is
    set it also includes every scanned listing (useful for studying the wider market). Pass a
    ``fetcher`` to reuse/inject one (e.g. in tests); otherwise one is built and closed here.
    """
    config = config or {}
    matcher = matcher or ColtChallengerMatcher(config.get("filter_patterns"))
    fetch_cfg = config.get("fetch", {})

    owns_fetcher = fetcher is None
    if fetcher is None:
        fetcher = HybridFetcher(
            timeout=fetch_cfg.get("timeout", 20),
            min_delay=fetch_cfg.get("min_delay", 2.0),
            allow_browser=allow_browser,
            browser_wait_ms=fetch_cfg.get("browser_wait_ms", 3500),
        )

    all_listings: list[Listing] = []
    per_site: dict[str, dict] = {}
    site_configs = config.get("sites", {})

    try:
        for name in sites:
            adapter = build_adapter(name, site_configs.get(name, {}))
            scanned = 0
            matched = 0
            logger.info("Scraping %s (query=%r, max_pages=%s)", name, query, max_pages)
            try:
                for listing in tqdm(adapter.iter_listings(fetcher, query, max_pages), desc=name, unit="offer"):
                    result = matcher.match(listing.searchable_text())
                    listing.matches_filter = result.matched
                    listing.matched_terms = result.terms
                    all_listings.append(listing)
                    scanned += 1
                    matched += int(result.matched)
            except Exception as e:  # noqa: BLE001 - one broken site must not abort the others
                logger.error("Site %s failed mid-scrape: %s", name, e)
            per_site[name] = {"scanned": scanned, "matched": matched}
            logger.info("%s: scanned=%s matched=%s", name, scanned, matched)
    finally:
        if owns_fetcher:
            fetcher.close()

    matched_listings = [listing for listing in all_listings if listing.matches_filter]
    report: dict = {
        "query": query,
        "filter": "challenger colt",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "scanned": len(all_listings),
            "matched": len(matched_listings),
            "per_site": per_site,
        },
        "matched_listings": [listing.model_dump(mode="json", exclude_none=True) for listing in matched_listings],
    }
    if save_all:
        report["all_listings"] = [listing.model_dump(mode="json", exclude_none=True) for listing in all_listings]
    return report
