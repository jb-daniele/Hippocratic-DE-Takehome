import re

from story_engine.checks import calculate_word_count


_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")


def _sentence_units(paragraph: str) -> list[str]:
    units = [match.group(0).strip() for match in _SENTENCE_RE.finditer(paragraph) if match.group(0).strip()]
    return units or [paragraph]


def _word_chunks(text: str, hard_cap: int) -> list[str]:
    words = text.split()
    return [" ".join(words[index : index + hard_cap]) for index in range(0, len(words), hard_cap)]


def _append_page(pages: list[str], units: list[str]) -> None:
    if units:
        pages.append(" ".join(units).strip())


def paginate(body: str, target: int = 120, hard_cap: int = 180) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in body.splitlines() if paragraph.strip()]
    if not paragraphs:
        return []

    pages: list[str] = []
    current_units: list[str] = []
    current_count = 0

    for paragraph in paragraphs:
        sentence_units = _sentence_units(paragraph)
        for sentence in sentence_units:
            sentence_count = calculate_word_count(sentence)
            chunks = [sentence] if sentence_count <= hard_cap else _word_chunks(sentence, hard_cap)
            for chunk in chunks:
                chunk_count = calculate_word_count(chunk)
                if current_units and current_count + chunk_count > target:
                    _append_page(pages, current_units)
                    current_units = []
                    current_count = 0
                current_units.append(chunk)
                current_count += chunk_count
                if current_count >= target or current_count >= hard_cap:
                    _append_page(pages, current_units)
                    current_units = []
                    current_count = 0

    if current_units:
        _append_page(pages, current_units)

    return pages
