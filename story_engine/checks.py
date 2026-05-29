import re
import string
from collections import Counter
from typing import Any

from story_engine.schemas import DraftStory, PostDraftReport, StoryBlueprint


_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_DOUBLE_QUOTE_DIALOGUE_RE = re.compile(r'"[^"\n]*"')

THOUGHT_VERBS = {
    "felt",
    "looked",
    "noticed",
    "pondered",
    "thought",
    "watched",
    "wondered",
}
ACTION_VERBS = {
    "counted",
    "held",
    "knelt",
    "picked",
    "pointed",
    "reached",
    "stepped",
    "touched",
    "traced",
    "tucked",
    "walked",
    "whispered",
}
NON_THOUGHT_VERBS = ACTION_VERBS | {
    "ask",
    "bring",
    "carry",
    "join",
    "move",
    "open",
    "place",
    "rest",
    "set",
    "share",
    "sit",
    "touch",
    "walk",
}
VERB_STEM_LEXICON = {
    "ask": {"ask", "asks", "asked", "asking"},
    "carry": {"carry", "carries", "carried", "carrying"},
    "join": {"join", "joins", "joined", "joining"},
    "move": {"move", "moves", "moved", "moving"},
    "place": {"place", "places", "placed", "placing"},
    "set": {"set", "sets", "setting"},
    "touch": {"touch", "touches", "touched", "touching"},
    "walk": {"walk", "walks", "walked", "walking"},
    "rest": {"rest", "rests", "rested", "resting"},
}
PHRASE_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "for",
    "from",
    "in",
    "into",
    "it",
    "of",
    "on",
    "or",
    "the",
    "then",
    "to",
    "with",
}


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _tokens(text: Any) -> list[str]:
    return [token.lower() for token in _WORD_RE.findall(str(text))]


def _content_tokens(text: Any) -> list[str]:
    return [token for token in _tokens(text) if token not in PHRASE_STOPWORDS and len(token) > 2]


def _head_token(text: str) -> str:
    for token in _tokens(text):
        if token not in PHRASE_STOPWORDS:
            return token
    return ""


def _head_verb_stem(text: str) -> str:
    tokens = _tokens(text)
    for token in tokens:
        for stem, forms in VERB_STEM_LEXICON.items():
            if token in forms or token.startswith(stem):
                return stem
    for token in tokens:
        if token in PHRASE_STOPWORDS:
            continue
        if len(token) > 3:
            return token
    return ""


def _has_verb_stem(text: str, stem: str) -> bool:
    if not stem:
        return False
    words = set(_tokens(text))
    forms = VERB_STEM_LEXICON.get(stem, {stem})
    return any(form in words for form in forms)


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in _SENTENCE_RE.findall(text) if sentence.strip()]


def _strip_dialogue(text: str) -> str:
    text = re.sub(r'"[^"]*"', " ", text)
    text = re.sub(r"“[^”]*”", " ", text)
    return re.sub(r"'[^']*'", " ", text)


def calculate_word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _jaccard(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _normalize_seam_sentence(sentence: str) -> str:
    collapsed = re.sub(r"\s+", " ", sentence.strip().lower())
    return collapsed.rstrip(string.punctuation + " ")


def _trim_evidence(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())[:79]


def check_scene_seams(scene_paragraphs: list[list[str]], blueprint) -> dict[str, Any]:
    del blueprint
    issues: list[str] = []
    for index in range(len(scene_paragraphs) - 1):
        current = scene_paragraphs[index]
        following = scene_paragraphs[index + 1]
        if not current or not following:
            continue
        last_paragraph = current[-1]
        first_paragraph = following[0]
        last_sentences = _sentences(last_paragraph)
        first_sentences = _sentences(first_paragraph)
        last_sentence = last_sentences[-1] if last_sentences else ""
        first_sentence = first_sentences[0] if first_sentences else ""

        normalized_last = _normalize_seam_sentence(last_sentence)
        normalized_first = _normalize_seam_sentence(first_sentence)
        if normalized_last and normalized_first and normalized_last == normalized_first:
            evidence = _trim_evidence(last_sentence or first_sentence)
            issues.append(f"seam_a_{index + 1}->_{index + 2}: {evidence}")

        last_tokens = _content_tokens(last_sentence)
        first_tokens = _content_tokens(first_sentence)
        if len(last_tokens) >= 4 and len(first_tokens) >= 4 and _jaccard(last_tokens, first_tokens) >= 0.7:
            evidence = _trim_evidence(f"{last_sentence} || {first_sentence}")
            issues.append(f"seam_b_{index + 1}->_{index + 2}: {evidence}")

        tail_grams = {tuple(last_paragraph_tokens[offset:offset + 5]) for last_paragraph_tokens in [_content_tokens(last_paragraph)] for offset in range(len(last_paragraph_tokens) - 4)}
        head_grams = {tuple(first_paragraph_tokens[offset:offset + 5]) for first_paragraph_tokens in [_content_tokens(first_paragraph)] for offset in range(len(first_paragraph_tokens) - 4)}
        overlap = tail_grams & head_grams
        if overlap:
            evidence = _trim_evidence(" ".join(next(iter(sorted(overlap)))))
            issues.append(f"seam_c_{index + 1}->_{index + 2}: {evidence}")

    if issues:
        return {"ok": False, "severity": "failure", "issues": issues, "route": "stitch"}
    return {"ok": True, "severity": "none", "issues": [], "route": None}


def check_boundary_only_edits(assembled_body, stitched_body, failed_boundary_indexes, scene_boundaries) -> dict[str, Any]:
    assembled_paragraphs = [paragraph for paragraph in assembled_body.split("\n\n") if paragraph.strip()]
    stitched_paragraphs = [paragraph for paragraph in stitched_body.split("\n\n") if paragraph.strip()]
    if len(assembled_paragraphs) != len(stitched_paragraphs):
        return {"ok": False, "severity": "failure", "issues": ["paragraph_count_mismatch"], "allowed_paragraphs": []}

    allowed: set[int] = set()
    for boundary_index in failed_boundary_indexes:
        left_index = boundary_index - 1
        right_index = boundary_index
        if left_index < 0 or right_index >= len(scene_boundaries):
            continue
        allowed.add(scene_boundaries[left_index]["end_paragraph"])
        allowed.add(scene_boundaries[right_index]["start_paragraph"])

    issues: list[str] = []
    for index, (assembled, stitched) in enumerate(zip(assembled_paragraphs, stitched_paragraphs), start=1):
        if index in allowed:
            continue
        normalized_assembled = re.sub(r"\s+", " ", assembled.strip())
        normalized_stitched = re.sub(r"\s+", " ", stitched.strip())
        if normalized_assembled != normalized_stitched:
            issues.append(f"non_boundary_paragraph_changed:{index}")

    return {
        "ok": not issues,
        "severity": "failure" if issues else "none",
        "issues": issues,
        "allowed_paragraphs": sorted(allowed),
    }


def _warning_check(issues: list[str], revision_guidance: str | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "severity": "warning" if issues else "none",
        "issues": issues,
        "revision_guidance": revision_guidance if issues else None,
    }


def check_phrase_repetition(draft: DraftStory | dict[str, Any], blueprint: StoryBlueprint | dict[str, Any]) -> dict[str, Any]:
    body = _strip_dialogue(_get(draft, "body", ""))
    names = {str(name).lower() for name in _get(blueprint, "main_characters", []) or []}
    tokens = [word.lower() for word in _WORD_RE.findall(body)]
    counts: Counter[str] = Counter()
    for size in range(3, 6):
        for index in range(0, max(0, len(tokens) - size + 1)):
            gram = tokens[index:index + size]
            if any(token in names for token in gram):
                continue
            if gram[0] in PHRASE_STOPWORDS or gram[-1] in PHRASE_STOPWORDS:
                continue
            if sum(token not in PHRASE_STOPWORDS for token in gram) < 2:
                continue
            counts[" ".join(gram)] += 1
    repeated = [phrase for phrase, count in counts.most_common() if count >= 3][:8]
    guidance = None
    if repeated:
        guidance = f"Vary repeated phrases like '{repeated[0]}' with concrete alternatives."
    if len(repeated) >= 5:
        return {
            "ok": False,
            "severity": "failure",
            "issues": repeated,
            "revision_guidance": guidance,
        }
    return _warning_check(repeated, guidance)


def check_ending_image(draft: DraftStory | dict[str, Any], blueprint: StoryBlueprint | dict[str, Any]) -> dict[str, Any]:
    paragraphs = [paragraph.strip() for paragraph in _get(draft, "body", "").split("\n\n") if paragraph.strip()]
    final_paragraph = paragraphs[-1].lower() if paragraphs else ""
    ending_image = _get(_get(blueprint, "story_spine", {}), "ending_image", "")
    ending_tokens = [token for token in _content_tokens(ending_image)[:3] if token]
    if ending_tokens and not any(token in final_paragraph for token in ending_tokens):
        return {
            "ok": False,
            "severity": "failure",
            "issues": ["final paragraph lacks ending image substance"],
            "revision_guidance": "Scene 4 must show the substance of story_spine.ending_image.",
        }
    return {"ok": True, "severity": "none", "issues": []}


def run_all(draft: DraftStory | dict[str, Any], blueprint: StoryBlueprint | dict[str, Any]) -> PostDraftReport:
    body = _get(draft, "body", "")
    word_count = calculate_word_count(body)
    checks = {
        "phrase_repetition": check_phrase_repetition(draft, blueprint),
        "ending_image": check_ending_image(draft, blueprint),
    }
    ok = all(check["ok"] for check in checks.values())
    return PostDraftReport(word_count=word_count, checks=checks, ok=ok)
