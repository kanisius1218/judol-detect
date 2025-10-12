"""Spam log ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String

from .base import Base


class SpamLog(Base):
    """Persisted detection outcome."""

    __tablename__ = "spam_logs"

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    is_spam = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    reasons = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
