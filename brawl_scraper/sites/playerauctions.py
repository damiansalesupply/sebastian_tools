from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import urljoin

import bs4

from base.logger import logger

from ..fetcher import HybridFetcher
from ..models import Listing
from .base import SiteAdapter, to_float


class PlayerAuctionsSite(SiteAdapter):
    """PlayerAuctions.com.

    Offers are rendered as HTML cards on the category page, so we parse them with BeautifulSoup.
    The CSS selectors live in config (with sensible defaults) since marketplace markup drifts.
    """

    name = "playerauctions"
    DEFAULT_PAGE_URL = "https://www.playerauctions.com/brawl-stars-account/?page={page}"
    BASE_URL = "https://www.playerauctions.com"
    DEFAULT_SELECTORS = {
        "card": "div.offer-card, li.offer, div.product-item",
        "title": "a.offer-title, .product-title, h3",
        "price": ".offer-price, .price",
        "link": "a.offer-title, a.product-link, a",
        "seller": ".seller-name, .offer-seller",
    }

    def iter_listings(self, fetcher: HybridFetcher, query: str, max_pages: int) -> Iterator[Listing]:
        page_tmpl = self.config.get("page_url", self.DEFAULT_PAGE_URL)
        selectors = {**self.DEFAULT_SELECTORS, **(self.config.get("selectors") or {})}

        for page in range(1, max_pages + 1):
            url = page_tmpl.format(page=page)
            res = fetcher.get(url, render="auto", browser_mode="page")
            if not res.ok:
                logger.warning("[playerauctions] page %s failed (status=%s err=%s)", page, res.status, res.error)
                break
            cards = self._parse_cards(res.text, selectors)
            if not cards:
                break
            yield from cards

    def _parse_cards(self, html: str, selectors: dict) -> list[Listing]:
        if not html:
            return []
        soup = bs4.BeautifulSoup(html, "html.parser")
        listings: list[Listing] = []
        for card in soup.select(selectors["card"]):
            title_el = card.select_one(selectors["title"])
            price_el = card.select_one(selectors["price"])
            link_el = card.select_one(selectors["link"])
            seller_el = card.select_one(selectors["seller"])

            href = link_el.get("href") if link_el else None
            url = urljoin(self.BASE_URL, href) if href else None
            title = title_el.get_text(strip=True) if title_el else ""
            description = card.get_text(" ", strip=True)
            listings.append(
                Listing(
                    site=self.name,
                    title=title,
                    description=description,
                    url=url,
                    price=to_float(price_el.get_text(strip=True) if price_el else None),
                    seller=seller_el.get_text(strip=True) if seller_el else None,
                )
            )
        return listings
