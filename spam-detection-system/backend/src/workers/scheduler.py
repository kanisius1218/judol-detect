"""Scheduler utilities for periodic jobs."""
from __future__ import annotations

from datetime import timedelta

from celery.schedules import crontab

from .celery_app import celery_app


def register_periodic_tasks() -> None:
    celery_app.conf.beat_schedule = {
        "cleanup-rollbacks": {
            "task": "deletion.execute",
            "schedule": timedelta(minutes=5),
            "args": ("cleanup",),
        }
    }
