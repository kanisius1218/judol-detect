"""Custom exception hierarchy for the service."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ServiceError(Exception):
    """Base class for service level exceptions."""

    message: str
    code: str = "service_error"

    def __str__(self) -> str:  # pragma: no cover - simple wrapper
        return f"{self.code}: {self.message}"


@dataclass
class SpamDetectionError(ServiceError):
    code: str = "spam_detection_error"


@dataclass
class RepositoryError(ServiceError):
    code: str = "repository_error"


@dataclass
class SecurityError(ServiceError):
    code: str = "security_error"
