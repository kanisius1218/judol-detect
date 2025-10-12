"""Base repository implementations."""
from __future__ import annotations

from typing import Generic, Iterable, List, Optional, TypeVar

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    """Simple in-memory repository for prototyping and unit tests."""

    def __init__(self) -> None:
        self._items: List[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)

    def list(self) -> Iterable[T]:
        return list(self._items)

    def get(self, predicate) -> Optional[T]:
        return next((item for item in self._items if predicate(item)), None)

    def remove(self, predicate) -> int:
        initial = len(self._items)
        self._items = [item for item in self._items if not predicate(item)]
        return initial - len(self._items)
