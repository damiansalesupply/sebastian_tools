from __future__ import annotations

import json as _json
import time
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

from base.logger import logger
from base.requests_utils import request_with_retry

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}

# Statuses that usually mean an anti-bot wall (Cloudflare etc.) rather than a real "not found".
# These are what trigger the browser fallback.
BLOCK_STATUSES = {403, 405, 429, 503}


@dataclass
class FetchResult:
    url: str
    status: int | None
    text: str
    used_browser: bool = False
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300 and not self.error

    def json(self) -> object | None:
        try:
            return _json.loads(self.text)
        except (ValueError, TypeError):
            return None


class HybridFetcher:
    """Fetch a URL with plain ``requests`` first, falling back to a real browser when blocked.

    The browser path uses Playwright and is imported lazily: if Playwright (or its Chromium
    binary) is not installed, the fetcher logs a hint and returns the direct response instead
    of crashing, so the requests-only path keeps working everywhere.
    """

    def __init__(
        self,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 20,
        min_delay: float = 2.0,
        allow_browser: bool = True,
        browser_wait_ms: int = 3500,
    ) -> None:
        self.headers = {**DEFAULT_HEADERS, **(headers or {})}
        self.timeout = timeout
        self.min_delay = min_delay
        self.allow_browser = allow_browser
        self.browser_wait_ms = browser_wait_ms
        self._last_request: dict[str, float] = {}
        self._browser = None
        self._pw = None
        self._browser_failed = False

    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        last = self._last_request.get(host)
        if last is not None:
            wait = self.min_delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request[host] = time.monotonic()

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        want: str = "text",
        render: str = "auto",
        browser_mode: str = "page",
    ) -> FetchResult:
        """GET ``url``.

        ``render``: ``"auto"`` (requests, browser only if blocked), ``"always"`` (browser only),
        or ``"never"``. ``want``: ``"text"`` or ``"json"`` (a failed JSON fetch also triggers the
        browser). ``browser_mode``: ``"page"`` renders the DOM, ``"api"`` uses the browser's HTTP
        stack for JSON endpoints.
        """
        self._throttle(url)
        merged = {**self.headers, **(headers or {})}

        if render == "always":
            browser_result = self._browser_get(url, params=params, headers=merged, mode=browser_mode)
            return browser_result or FetchResult(url=url, status=None, text="", error="browser unavailable")

        try:
            resp = request_with_retry("GET", url, headers=merged, params=params, timeout0=self.timeout, max_retries=2)
            result = FetchResult(url=str(resp.url), status=resp.status_code, text=resp.text)
        except Exception as e:  # noqa: BLE001 - surface any transport error as a failed FetchResult
            result = FetchResult(url=url, status=None, text="", error=str(e))

        if render == "never":
            return result

        blocked = result.status in BLOCK_STATUSES
        json_failed = want == "json" and (not result.ok or result.json() is None)
        if (blocked or json_failed) and self.allow_browser:
            browser_result = self._browser_get(url, params=params, headers=merged, mode=browser_mode)
            if browser_result is not None:
                return browser_result
            logger.warning("Browser fallback unavailable; using direct response for %s (status=%s)", url, result.status)
        return result

    def _ensure_browser(self) -> bool:
        if self._browser is not None:
            return True
        if self._browser_failed:
            return False
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning(
                "Playwright not installed; skipping browser fallback. "
                "Install with: pip install playwright && playwright install chromium"
            )
            self._browser_failed = True
            return False
        try:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            return True
        except Exception as e:  # noqa: BLE001 - launch failure (missing binary) must not crash the run
            logger.warning("Could not launch Chromium (%s). Try: playwright install chromium", e)
            self._browser_failed = True
            self._pw = None
            self._browser = None
            return False

    def _browser_get(self, url: str, *, params: dict | None, headers: dict[str, str], mode: str) -> FetchResult | None:
        if not self.allow_browser or not self._ensure_browser():
            return None
        full = url
        if params:
            full = url + ("&" if "?" in url else "?") + urlencode(params)
        context = None
        try:
            ua = headers.get("User-Agent")
            extra = {k: v for k, v in headers.items() if k.lower() != "user-agent"}
            context = self._browser.new_context(user_agent=ua, extra_http_headers=extra)
            if mode == "api":
                resp = context.request.get(full, timeout=self.timeout * 1000)
                return FetchResult(url=full, status=resp.status, text=resp.text(), used_browser=True)
            page = context.new_page()
            resp = page.goto(full, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            page.wait_for_timeout(self.browser_wait_ms)
            html = page.content()
            return FetchResult(url=full, status=resp.status if resp else None, text=html, used_browser=True)
        except Exception as e:  # noqa: BLE001 - a single failed browser fetch falls back to None
            logger.warning("Browser fetch failed for %s: %s", full, e)
            return None
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:  # noqa: BLE001
                    pass

    def close(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
            if self._pw is not None:
                self._pw.stop()
        except Exception:  # noqa: BLE001
            pass
        self._browser = None
        self._pw = None
