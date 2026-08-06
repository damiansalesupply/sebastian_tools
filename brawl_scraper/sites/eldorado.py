from __future__ import annotations

import json
from collections.abc import Iterator

import bs4

from base.logger import logger

from ..fetcher import HybridFetcher
from ..models import Listing
from .base import SiteAdapter, to_float

# Keys that mark a dict (inside Eldorado's embedded JSON) as an offer rather than some other node.
_TITLE_KEYS = ("offerTitle", "title", "name", "description")
_PRICE_KEYS = ("pricePerUnit", "price", "unitPrice", "amount")
_ID_KEYS = ("id", "offerId", "_id")


class EldoradoSite(SiteAdapter):
    """Eldorado.gg.

    Eldorado is a Next.js app; the offer list is delivered either through a JSON API or embedded
    in the page's ``__NEXT_DATA__`` script. We try a configurable API endpoint first and, failing
    that, parse ``__NEXT_DATA__`` from the rendered category page and walk it for offer objects.
    """

    name = "eldorado"
    # {query} -> url-friendly query, {page} -> page number.
    DEFAULT_PAGE_URL = "https://www.eldorado.gg/brawl-stars-accounts/c/Account?searchTerm={query}&pageIndex={page}"

    def iter_listings(self, fetcher: HybridFetcher, query: str, max_pages: int) -> Iterator[Listing]:
        api_url = self.config.get("api_url")
        page_tmpl = self.config.get("page_url", self.DEFAULT_PAGE_URL)
        q = query.replace(" ", "+")

        for page in range(1, max_pages + 1):
            if api_url:
                res = fetcher.get(api_url.format(query=q, page=page), want="json", browser_mode="api")
                offers = self._find_offers(res.json()) if res.ok else []
            else:
                url = page_tmpl.format(query=q, page=page)
                res = fetcher.get(url, render="auto", browser_mode="page")
                offers = self._offers_from_html(res.text) if res.ok else []

            if not res.ok:
                logger.warning("[eldorado] page %s failed (status=%s err=%s)", page, res.status, res.error)
                break
            if not offers:
                break
            for offer in offers:
                yield self._to_listing(offer)

    def _offers_from_html(self, html: str) -> list[dict]:
        if not html:
            return []
        soup = bs4.BeautifulSoup(html, "html.parser")
        node = soup.find("script", id="__NEXT_DATA__")
        if not node or not node.string:
            return []
        try:
            data = json.loads(node.string)
        except ValueError:
            return []
        return self._find_offers(data)

    @classmethod
    def _find_offers(cls, data: object) -> list[dict]:
        """Recursively collect dicts that look like offers (have a title-ish and a price-ish key)."""
        found: list[dict] = []
        seen: set[int] = set()

        def walk(obj: object) -> None:
            if isinstance(obj, dict):
                has_title = any(k in obj for k in _TITLE_KEYS)
                has_price = any(k in obj for k in _PRICE_KEYS)
                if has_title and has_price and id(obj) not in seen:
                    seen.add(id(obj))
                    found.append(obj)
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        return found

    def _to_listing(self, item: dict) -> Listing:
        offer_id = next((str(item[k]) for k in _ID_KEYS if item.get(k) is not None), None)
        title = next((str(item[k]) for k in _TITLE_KEYS if item.get(k)), "")
        price = next((item[k] for k in _PRICE_KEYS if item.get(k) is not None), None)
        url = item.get("offerUrl") or item.get("url")
        if url and url.startswith("/"):
            url = "https://www.eldorado.gg" + url
        keep_raw = bool(self.config.get("keep_raw"))
        return Listing(
            site=self.name,
            listing_id=offer_id,
            title=title,
            description=item.get("description") or item.get("offerDescription"),
            url=url,
            price=to_float(price),
            currency=item.get("currency") or self.config.get("currency"),
            seller=item.get("sellerName") or item.get("seller"),
            raw=item if keep_raw else None,
        )
