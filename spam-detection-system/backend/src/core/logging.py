"""Structured logging configuration."""
from __future__ import annotations

import logging
from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging with structured JSON output."""

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {
                "level": level,
                "handlers": ["default"],
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""

    return logging.getLogger(name)
