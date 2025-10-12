"""Repository for user data."""
from __future__ import annotations

from dataclasses import dataclass

from .base import InMemoryRepository


@dataclass
class UserRecord:
    id: str
    email: str
    is_admin: bool = False


class UserRepository(InMemoryRepository[UserRecord]):
    """In-memory user repository placeholder."""

    def get_by_email(self, email: str) -> UserRecord | None:
        return self.get(lambda user: user.email == email)
