"""Model version management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .spam_detector import SpamDetector


@dataclass
class ModelInfo:
    version: str
    path: Path


class ModelManager:
    """Manage lifecycle of ML models."""

    def __init__(self, storage_path: Path, default_version: str) -> None:
        self.storage_path = storage_path
        self.default_version = default_version

    def load(self, version: str | None = None) -> tuple[SpamDetector, ModelInfo]:
        model_version = version or self.default_version
        # In a production system we would load a serialized model. For now we return a heuristic one.
        info = ModelInfo(version=model_version, path=self.storage_path / model_version)
        detector = SpamDetector()
        return detector, info
