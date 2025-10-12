"""Celery application factory."""
from __future__ import annotations

from celery import Celery

from ..core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "spam_detection",
        broker=settings.celery_broker_url,
        backend=settings.celery_backend_url,
    )
    app.conf.task_default_queue = "spam-tasks"
    return app


celery_app = create_celery_app()
