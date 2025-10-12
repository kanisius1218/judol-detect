"""Lightweight feature extraction utilities."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

SPAM_KEYWORDS = {
    "subscribe",
    "buy now",
    "click",
    "promo",
    "discount",
    "free",
    "winner",
    "bitcoin",
}

URL_REGEX = re.compile(r"https?://\S+")


@dataclass
class FeatureVector:
    """Simple representation of extracted features."""

    keyword_hits: int
    has_url: bool
    length: int

    def to_list(self) -> List[float]:
        return [float(self.keyword_hits), float(self.has_url), float(self.length)]


def extract_features(text: str) -> FeatureVector:
    """Extract basic heuristics from comment text."""

    text_lower = text.lower()
    keyword_hits = sum(1 for kw in SPAM_KEYWORDS if kw in text_lower)
    has_url = bool(URL_REGEX.search(text))
    length = len(text)
    return FeatureVector(keyword_hits=keyword_hits, has_url=has_url, length=length)


def batch_extract(texts: Iterable[str]) -> List[FeatureVector]:
    """Extract features for a list of texts."""

    return [extract_features(text) for text in texts]
