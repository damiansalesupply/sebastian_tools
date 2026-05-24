from __future__ import annotations

from collections.abc import Iterator

from base.logger import logger

from ..fetcher import HybridFetcher
from ..models import Listing
from .base import SiteAdapter, to_float


class G2GSite(SiteAdapter):
    """G2G.com.

    G2G renders listings from a JSON search API (``sls.g2g.com/offer/search``) rather than
    server-side HTML, so we hit that endpoint directly and fall back to the browser's HTTP
    stack (``browser_mode="api"``) when the datacenter IP is challenged.
    """

    name = "g2g"
    DEFAULT_API = "https://sls.g2g.com/offer/search"
    DEFAULT_OFFER_URL = "https://www.g2g.com/offer/{seo}"

    def iter_listings(self, fetcher: HybridFetcher, query: str, max_pages: int) -> Iterator[Listing]:
        api = self.config.get("api_url", self.DEFAULT_API)
        seo_term = self.config.get("seo_term") or query.replace(" ", "-").lower()
        page_size = int(self.config.get("page_size", 48))
        currency = self.config.get("currency", "USD")
        country = self.config.get("country", "US")

        for page in range(1, max_pages + 1):
            params = {
                "seo_term": seo_term,
                "page": page,
                "page_size": page_size,
                "currency": currency,
                "country": country,
                "sort": self.config.get("sort", "most_relevant"),
            }
            res = fetcher.get(api, params=params, want="json", browser_mode="api")
            if not res.ok:
                logger.warning("[g2g] page %s failed (status=%s err=%s)", page, res.status, res.error)
                break
            results = self._extract_results(res.json())
            if not results:
                break
            for item in results:
                if isinstance(item, dict):
                    yield self._to_listing(item)

    @staticmethod
    def _extract_results(data: object) -> list:
        if not isinstance(data, dict):
            return []
        payload = data.get("payload")
        container = payload if isinstance(payload, dict) else data
        results = container.get("results")
        return results if isinstance(results, list) else []

    def _to_listing(self, item: dict) -> Listing:
        offer_id = str(item.get("offer_id") or item.get("id") or "") or None
        seo = item.get("seo_term") or item.get("seo") or ""
        url = self.DEFAULT_OFFER_URL.format(seo=seo)
        if offer_id:
            url = f"{url}?id={offer_id}"
        price = item.get("converted_unit_price") or item.get("unit_price") or item.get("display_price")
        seller = item.get("username")
        if not seller and isinstance(item.get("seller"), dict):
            seller = item["seller"].get("username")
        keep_raw = bool(self.config.get("keep_raw"))
        return Listing(
            site=self.name,
            listing_id=offer_id,
            title=item.get("title") or item.get("offer_title") or "",
            description=item.get("description") or item.get("offer_attributes_desc"),
            url=url,
            price=to_float(price),
            currency=item.get("offer_currency") or item.get("display_currency") or self.config.get("currency"),
            seller=seller,
            raw=item if keep_raw else None,
        )
