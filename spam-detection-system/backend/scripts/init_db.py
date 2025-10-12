"""Initialise database tables."""
from __future__ import annotations

from sqlalchemy import create_engine

from ..src.core.config import get_settings
from ..src.models.database import base


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    base.Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
