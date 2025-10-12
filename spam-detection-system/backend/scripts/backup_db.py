"""Database backup placeholder script."""
from __future__ import annotations

from pathlib import Path
import shutil


def main(db_path: str = "spam.db", backup_dir: str = "backups") -> None:
    source = Path(db_path)
    target_dir = Path(backup_dir)
    target_dir.mkdir(exist_ok=True)
    if source.exists():
        shutil.copy(source, target_dir / source.name)
        print(f"Database backed up to {target_dir / source.name}")
    else:
        print("Database file does not exist")


if __name__ == "__main__":
    main()
