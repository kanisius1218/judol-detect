"""Tests for utility validators."""
from __future__ import annotations

import pytest

from backend.src.utils.validators import ensure_unique, validate_platform


def test_validate_platform_success():
    validate_platform("youtube")


def test_validate_platform_failure():
    with pytest.raises(ValueError):
        validate_platform("unknown")


def test_ensure_unique_detects_duplicates():
    with pytest.raises(ValueError):
        ensure_unique(["a", "b", "a"])
