"""Sanitization helpers."""
from __future__ import annotations

import html
import re

MENTION_REGEX = re.compile(r"@[A-Za-z0-9_]+")


def sanitize_comment(text: str) -> str:
    """Perform basic sanitisation to normalise incoming text."""

    text = html.unescape(text)
    text = MENTION_REGEX.sub("@user", text)
    return text.strip()
