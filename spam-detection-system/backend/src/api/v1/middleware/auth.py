"""Authentication utilities and dependencies."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ...core.config import get_settings
from ...core.security import ApiKeyCredentials, SecurityService

api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_security_service() -> SecurityService:
    """Provide the singleton security service instance."""

    settings = get_settings()
    return SecurityService(salt=settings.api_key_salt)


async def enforce_api_key(
    api_key: str | None = Security(api_key_scheme),
    service: SecurityService = Depends(get_security_service),
) -> ApiKeyCredentials:
    """Validate the provided API key and return the associated credentials."""

    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    credentials = service.validate_api_key(api_key)
    if not credentials:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    return credentials


async def enforce_internal_header(x_internal_call: str | None = Header(default=None)) -> None:
    """Ensure that sensitive endpoints are only callable from trusted internal services."""

    if x_internal_call != "1":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal access required")
