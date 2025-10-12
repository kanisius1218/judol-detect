"""Tests for the spam detector heuristics."""
from __future__ import annotations

from backend.src.models.ml.spam_detector import SpamDetector


def test_classifier_aggressive_mode():
    detector = SpamDetector()
    texts = ["Click this link for free stuff", "Hello there"]
    results_normal = detector.classify(texts, aggressive=False)
    results_aggressive = detector.classify(texts, aggressive=True)
    assert results_normal[0][0] is True
    assert results_normal[1][0] is False
    assert results_aggressive[0][0] is True
