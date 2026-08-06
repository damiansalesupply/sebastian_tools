from __future__ import annotations

import pytest

from brawl_scraper.matcher import ColtChallengerMatcher, normalize


@pytest.fixture
def matcher() -> ColtChallengerMatcher:
    return ColtChallengerMatcher()


@pytest.mark.parametrize(
    "text",
    [
        "Brawl Stars account with Challenger Colt skin",
        "challenger-colt unlocked",
        "CHALLENGER_COLT included",
        "rare skin: Colt (Challenger) available",
        "skins -> challenger   colt, mecha crow",
    ],
)
def test_matches_challenger_colt_variants(matcher: ColtChallengerMatcher, text: str) -> None:
    assert matcher.match(text).matched


@pytest.mark.parametrize(
    "text",
    [
        "Brawl Stars account, all brawlers maxed",
        "Challenger Shelly and Brock skins",
        "Colt brawler maxed out",
        # Both words present but NOT adjacent -> must not match (different brawler's Challenger skin).
        "Account with Challenger Shelly, Brock and the Colt brawler",
        "",
    ],
)
def test_does_not_match_unrelated(matcher: ColtChallengerMatcher, text: str) -> None:
    assert not matcher.match(text).matched


def test_reports_matched_terms(matcher: ColtChallengerMatcher) -> None:
    result = matcher.match("has Challenger Colt and also Colt Challenger duplicate")
    assert result.matched
    assert set(result.terms) == {"challenger colt", "colt challenger"}


def test_normalize_strips_accents_and_punctuation() -> None:
    assert normalize("Chàllenger—Cölt!!") == "challenger colt"


def test_custom_patterns() -> None:
    m = ColtChallengerMatcher(["mega box"])
    assert m.match("free mega-box included").matched
    assert not m.match("challenger colt").matched
