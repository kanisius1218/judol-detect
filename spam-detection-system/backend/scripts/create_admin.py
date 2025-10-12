"""Create an admin user placeholder script."""
from __future__ import annotations

from ..src.repository.user_repository import UserRecord, UserRepository


def main(email: str) -> None:
    repo = UserRepository()
    repo.add(UserRecord(id="admin", email=email, is_admin=True))
    print(f"Admin user {email} created")


if __name__ == "__main__":
    main("admin@example.com")
