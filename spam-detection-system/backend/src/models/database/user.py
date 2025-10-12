"""User model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
