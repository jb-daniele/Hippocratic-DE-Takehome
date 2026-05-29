from __future__ import annotations

import re


BAD_TITLE_PATTERNS = [
    re.compile(r"\bGentle Bedtime\b", re.IGNORECASE),
    re.compile(r"\bCozy Bedtime\b", re.IGNORECASE),
    re.compile(r"\bPeaceful Bedtime\b", re.IGNORECASE),
    re.compile(r"\bBedtime Story\b", re.IGNORECASE),
    re.compile(r"^[A-Z][A-Za-z]+(?:'s)? Bedtime$"),
    re.compile(r"^[A-Z][A-Za-z]+(?:'s)? Gentle Bedtime$"),
    re.compile(r"^A Cozy Adventure$", re.IGNORECASE),
    re.compile(r"^A Magical Night$", re.IGNORECASE),
]

_TITLE_CASE_SKIPS = {"a", "an", "and", "the", "of", "in", "on", "to", "for", "with", "at", "by"}


def is_bad_title(title: str) -> bool:
    stripped = title.strip()
    if not stripped:
        return True
    return any(pattern.search(stripped) for pattern in BAD_TITLE_PATTERNS)


def is_valid_title(title: str) -> bool:
    stripped = title.strip().strip('"“”')
    if not stripped or stripped != title.strip():
        return False
    words = stripped.split()
    if not 2 <= len(words) <= 7:
        return False
    if is_bad_title(stripped):
        return False
    for index, word in enumerate(words):
        if index > 0 and word.lower() in _TITLE_CASE_SKIPS:
            continue
        if not word[0].isupper():
            return False
    return True
