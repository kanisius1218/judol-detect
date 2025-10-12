"""API key model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, String

from .base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    hashed_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    scopes = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
