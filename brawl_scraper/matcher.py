from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Challenger Colt is an esports/competitive skin. "Challenger" alone is ambiguous (there are
# Challenger skins for several brawlers) and "Colt" alone is far too broad, so we require the
# two words adjacent (in either order). Separators like '-', '_' or punctuation are normalized
# to spaces first, so "challenger-colt", "Challenger Colt" and "Colt (Challenger)" all match.
DEFAULT_PATTERNS: tuple[str, ...] = (
    r"challenger colt",
    r"colt challenger",
)


def normalize(text: str) -> str:
    """Lowercase, strip accents, and collapse every run of non-alphanumerics to one space."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class MatchResult:
    matched: bool
    terms: list[str]


class ColtChallengerMatcher:
    """Detects whether a piece of listing text advertises the Challenger Colt skin."""

    def __init__(self, patterns: list[str] | tuple[str, ...] | None = None) -> None:
        pats = tuple(patterns) if patterns else DEFAULT_PATTERNS
        self._patterns = [re.compile(p) for p in pats]

    def match(self, text: str) -> MatchResult:
        norm = normalize(text)
        found: list[str] = []
        for rx in self._patterns:
            m = rx.search(norm)
            if m:
                found.append(m.group(0))
        return MatchResult(matched=bool(found), terms=sorted(set(found)))
