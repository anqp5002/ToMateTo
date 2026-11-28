"""Shared content-name normalization for writing and fixtures; never email."""

import re
import unicodedata


def normalize_name(value: str) -> str:
    lowered = re.sub(r"\s+", " ", value).strip().lower().replace("đ", "d")
    result = "".join(
        c for c in unicodedata.normalize("NFD", lowered) if not unicodedata.combining(c)
    )
    if not result:
        raise ValueError("Name must not be empty")
    return result
