from __future__ import annotations

from pathlib import Path

import pytest

from brawl_scraper.fetcher import FetchResult

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeFetcher:
    """Stand-in for HybridFetcher in tests.

    ``responses`` maps a URL substring to a list of FetchResults returned on successive calls.
    Once a queue is exhausted an empty 200 response is returned, which makes the adapters stop
    paginating (no more results).
    """

    def __init__(self, responses: dict[str, list[FetchResult]]) -> None:
        self._responses = {key: list(items) for key, items in responses.items()}
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, **kwargs) -> FetchResult:
        self.calls.append((url, kwargs))
        for key, queue in self._responses.items():
            if key in url:
                return queue.pop(0) if queue else FetchResult(url=url, status=200, text="")
        return FetchResult(url=url, status=404, text="", error="no fixture for url")

    def close(self) -> None:
        pass


@pytest.fixture
def fake_fetcher_factory():
    def _make(responses: dict[str, list[FetchResult]]) -> FakeFetcher:
        return FakeFetcher(responses)

    return _make
