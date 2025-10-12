"""Centralised error handling for FastAPI."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from ...core import exceptions


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app instance."""

    @app.exception_handler(exceptions.SpamDetectionError)
    async def handle_detection_error(_: FastAPI, exc: exceptions.SpamDetectionError):  # type: ignore[override]
        return JSONResponse(status_code=422, content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(exceptions.RepositoryError)
    async def handle_repository_error(_: FastAPI, exc: exceptions.RepositoryError):  # type: ignore[override]
        return JSONResponse(status_code=500, content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(exceptions.SecurityError)
    async def handle_security_error(_: FastAPI, exc: exceptions.SecurityError):  # type: ignore[override]
        return JSONResponse(status_code=403, content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: FastAPI, exc: HTTPException):  # type: ignore[override]
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
