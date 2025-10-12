"""Security related helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ApiKeyCredentials:
    """Represents validated API key credentials."""

    key_id: str
    scopes: list[str]


class SecurityService:
    """Stateless helper for hashing, verifying and managing API keys."""

    def __init__(self, salt: str | None = None) -> None:
        self._salt = salt or "salt"
        self._keys: Dict[str, ApiKeyCredentials] = {
            self._hash("default-key"): ApiKeyCredentials(key_id="default", scopes=["read", "write"])
        }

    def _hash(self, value: str) -> str:
        return hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()

    def generate_api_key(self, name: str, scopes: list[str]) -> tuple[str, ApiKeyCredentials]:
        raw_key = secrets.token_urlsafe(32)
        hashed = self._hash(raw_key)
        credentials = ApiKeyCredentials(key_id=name, scopes=scopes)
        self._keys[hashed] = credentials
        return raw_key, credentials

    def validate_api_key(self, api_key: str) -> Optional[ApiKeyCredentials]:
        hashed = self._hash(api_key)
        return self._keys.get(hashed)


class SecurityError(RuntimeError):
    """Raised when a security related issue occurs."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = "security_error"
