"""Simple heuristic-based spam detector wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from .feature_extractor import FeatureVector, batch_extract


@dataclass
class Prediction:
    """Represents a single prediction result."""

    probability: float
    reasons: List[str]


class SpamDetector:
    """A light-weight detector that mimics ML behaviour for scaffolding."""

    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def _score(self, features: FeatureVector) -> Tuple[float, List[str]]:
        score = 0.1
        reasons: List[str] = []
        if features.keyword_hits:
            score += min(0.1 * features.keyword_hits, 0.6)
            reasons.append("keyword_match")
        if features.has_url:
            score += 0.3
            reasons.append("contains_url")
        if features.length > 300:
            score += 0.1
            reasons.append("long_content")
        score = min(score, 0.99)
        return score, reasons

    def predict(self, texts: Iterable[str]) -> List[Prediction]:
        predictions = []
        for features in batch_extract(texts):
            score, reasons = self._score(features)
            predictions.append(Prediction(probability=score, reasons=reasons))
        return predictions

    def classify(self, texts: Iterable[str], aggressive: bool = False) -> List[Tuple[bool, float, List[str]]]:
        adjusted_threshold = self.threshold - (0.2 if aggressive else 0.0)
        results = []
        for prediction in self.predict(texts):
            is_spam = prediction.probability >= adjusted_threshold
            results.append((is_spam, prediction.probability, prediction.reasons))
        return results
