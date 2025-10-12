"""FastAPI application factory for the spam detection system."""
from __future__ import annotations

from fastapi import FastAPI

from .src.api.v1.middleware import cors, error_handler
from .src.api.v1.routes import admin, analytics, detection, health
from .src.core.config import get_settings
from .src.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(title="Spam Detection System", version="1.0.0", debug=settings.api_debug)

    cors.configure_cors(app, settings.api_allowed_origins)
    error_handler.register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(detection.router)
    app.include_router(analytics.router)
    app.include_router(admin.router)

    return app


app = create_app()
