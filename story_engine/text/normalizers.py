from __future__ import annotations

import re


SMART_QUOTES_RE = re.compile(r"[“”]")
SINGLE_QUOTE_DIALOGUE_RE = re.compile(r"(?<!\w)'([^'\n]{1,200}[.!?,])\s*'(?!\w)")
SPACE_BEFORE_CLOSING_QUOTE_RE = re.compile(r"([.!?,])\s+(['\"])(?=\s|$|[^A-Za-z])")


def normalize_dialogue(body: str) -> tuple[str, dict[str, int]]:
    stats = {
        "smart_quotes": 0,
        "single_quote_dialogue": 0,
        "space_before_closing_quote": 0,
        "linebreaks_in_quotes": 0,
    }
    result = body
    stats["smart_quotes"] = len(SMART_QUOTES_RE.findall(result))
    result = result.replace("\u201c", '"').replace("\u201d", '"')

    def single_quote_repl(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if len(inner.split()) >= 2:
            stats["single_quote_dialogue"] += 1
            return f'"{inner}"'
        return match.group(0)

    result = SINGLE_QUOTE_DIALOGUE_RE.sub(single_quote_repl, result)
    stats["space_before_closing_quote"] = len(SPACE_BEFORE_CLOSING_QUOTE_RE.findall(result))
    result = SPACE_BEFORE_CLOSING_QUOTE_RE.sub(r"\1\2", result)

    chars: list[str] = []
    in_double_quote = False
    for char in result:
        if char == '"':
            in_double_quote = not in_double_quote
            chars.append(char)
            continue
        if char == "\n" and in_double_quote:
            stats["linebreaks_in_quotes"] += 1
            if not chars or chars[-1] != " ":
                chars.append(" ")
            continue
        chars.append(char)
    result = "".join(chars)
    return result, stats
