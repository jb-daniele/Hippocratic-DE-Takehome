from __future__ import annotations

import re
from time import perf_counter
from typing import Any, Iterable

from story_engine import checks, model_client
from story_engine.checks import calculate_word_count
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.scene_writer import build_prompt as build_scene_writer_prompt
from story_engine.schemas import CharacterCard, DraftStory, SceneCard, SchemaError, StoryBlueprint
from story_engine.text.normalizers import normalize_dialogue
from story_engine.text.summaries import already_written_summary, upcoming_scene_summary
from story_engine.trace import event as trace_event

from ._common import _format_failures, _latency_ms, _raw_response, _trace_degraded
from .planner import _content_tokens


_DIALOGUE_PUNCT_SPACE_RE = re.compile(r"([.!?,])\s+(['\"])(?=\s|$|[^A-Za-z])")
_SINGLE_QUOTE_DIALOGUE_RE = re.compile(r"(?<!\w)'([^'\n]{1,200}[.!?,])\s*'(?!\w)")

_WRITER_RETRY_GUIDANCE_BY_CODE: dict[str, str] = {
    "missing_dialogue": "Your previous scene still failed `missing_dialogue`. The next output must include the planned dialogue as quoted spoken speech from the planned speaker. Narration, thoughts, feelings, gestures, and reported speech such as 'Rory suggested...' or 'Grandpa explained...' do not count as dialogue.",
    "missing_setting": "Your previous scene still failed `missing_setting`. The next output must visibly show the SceneCard setting through a concrete place or object detail.",
    "missing_planned_beat": "Your previous scene still failed `missing_planned_beat`. The next output must visibly show the missing planned beat as action, object detail, speech, or what a character notices. Do not summarize it as a feeling, conclusion, or general success.",
    "extra_dialogue": "Your previous scene still failed `extra_dialogue`. The next output must not include any dialogue beyond the planned `scene_card.dialogue` items. If `scene_card.dialogue` is empty, include no quoted speech.",
    "end_with_missing": "Your previous scene still failed `end_with_missing`. The second paragraph must end with the SceneCard `end_with` image exactly or with only tiny grammar changes.",
}


def _build_writer_retry_guidance(codes: Iterable[str]) -> str:
    seen: set[str] = set()
    instructions: list[str] = []
    for code in codes:
        clean_code = code.strip()
        if not clean_code or clean_code in seen:
            continue
        seen.add(clean_code)
        if clean_code in _WRITER_RETRY_GUIDANCE_BY_CODE:
            instructions.append(_WRITER_RETRY_GUIDANCE_BY_CODE[clean_code])
    return "\n".join(instructions)


def _parse_scene_paragraphs(response: Any, role: str) -> str:
    if not isinstance(response, dict) or "paragraphs" not in response:
        raise SchemaError(f"{role} scene must return paragraphs")
    paragraphs = response.get("paragraphs")
    if not isinstance(paragraphs, list) or not paragraphs:
        raise SchemaError(f"{role} scene must return paragraphs")
    stripped: list[str] = []
    for paragraph in paragraphs:
        if not isinstance(paragraph, str) or not paragraph.strip():
            raise SchemaError(f"{role} scene must return paragraphs")
        stripped.append(paragraph.strip())
    if len(stripped) != 2:
        raise SchemaError(f"paragraph_count_invalid: expected 2, got {len(stripped)}")
    return "\n\n".join(stripped)


def _scene_role(scene_index: int, scene_count: int) -> str:
    if scene_index == 0:
        return "opening"
    if scene_index == scene_count - 1:
        return "closing"
    return "development"


def _paragraph_count(text: str) -> int:
    return len([paragraph for paragraph in text.split("\n\n") if paragraph.strip()])


def _sentence_chunks(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.findall(r"[^.!?]+[.!?]?", text) if chunk.strip()]


def _truncated_evidence(text: str) -> str:
    return " ".join(text.split())[:120]


def _quoted_spans_with_offsets(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in re.finditer(r'"[^"\n]*"', text)]


def validate_written_scene(body: str, card: SceneCard) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]

    setting_token = checks._head_token(card.setting)
    lowered_body = body.lower()
    if setting_token and setting_token not in lowered_body:
        failures.append({"code": "missing_setting", "evidence": _truncated_evidence(body)})

    for index, paragraph in enumerate(paragraphs):
        lowered_paragraph = paragraph.lower()
        for item in card.paragraph_beats[index].must_show:
            head_verb = checks._head_verb_stem(item)
            head_token = checks._head_token(item)
            has_verb = bool(head_verb) and checks._has_verb_stem(lowered_paragraph, head_verb)
            has_token = bool(head_token) and head_token in lowered_paragraph
            if not has_verb and not has_token:
                failures.append({"code": "missing_planned_beat", "evidence": _truncated_evidence(item)})

    quoted_offsets = _quoted_spans_with_offsets(body)
    if not card.dialogue and quoted_offsets:
        quote_start, quote_end = quoted_offsets[0]
        failures.append({"code": "extra_dialogue", "evidence": body[quote_start:quote_end].strip()[:120]})
    lowered_full = body.lower()
    for item in card.dialogue:
        speaker = item.speaker
        found = False
        speaker_lower = speaker.lower()
        for match in re.finditer(re.escape(speaker_lower), lowered_full):
            for quote_start, quote_end in quoted_offsets:
                if abs(match.start() - quote_start) <= 80 or abs(match.start() - quote_end) <= 80:
                    found = True
                    break
            if found:
                break
        if not found:
            evidence = _truncated_evidence(f"{speaker} {item.purpose}")
            failures.append({"code": "missing_dialogue", "evidence": evidence})

    if card.end_with is not None:
        last_sentence = _sentence_chunks(paragraphs[1])[-1].lower() if _sentence_chunks(paragraphs[1]) else paragraphs[1].lower()
        end_tokens = [token for token in _content_tokens(card.end_with)[:3] if token]
        if end_tokens and not any(token in last_sentence for token in end_tokens):
            failures.append({"code": "end_with_missing", "evidence": _truncated_evidence(body[-120:])})
    return failures


def _scene_writer_errors(body: str, card: SceneCard | None) -> list[dict[str, str]]:
    if card is None:
        raise SchemaError("scene_writer requires a SceneCard")
    return validate_written_scene(body, card)


def _write_scene_result(
    blueprint: StoryBlueprint,
    scene_index: int,
    already_written_summary: str = "",
    upcoming_scene_summary: str = "",
) -> tuple[str, bool, list[dict[str, str]]]:
    start = perf_counter()
    scene_count = blueprint.scene_plan["scene_count"]
    role = _scene_role(scene_index, scene_count)
    cards = getattr(blueprint, "scene_cards", None) or []
    card = cards[scene_index] if scene_index < len(cards) else None
    if card is None:
        raise SchemaError("scene_writer requires a SceneCard")
    prompt = build_scene_writer_prompt(
        blueprint,
        card,
        scene_role=role,
        character_cards=blueprint.character_cards,
        already_written_summary=already_written_summary,
        upcoming_scene_summary=upcoming_scene_summary,
    )
    last_body: str | None = None
    last_response: Any = None
    last_exception: Exception | None = None
    last_errors: list[dict[str, str]] = []
    retried = False
    for attempt in range(3):
        try:
            last_response = model_client.call_model_json(
                prompt,
                temperature=AGENT_TEMPERATURES["scene_writer"],
                max_tokens=4000,
                agent_name="scene_writer",
                iteration=attempt,
                scene_index=scene_index,
            )
            body = _parse_scene_paragraphs(last_response, role)
            body = normalize_dialogue(body)[0]
            last_body = body
            last_errors = _scene_writer_errors(body, card)
            if not last_errors:
                trace_event(
                    "agents.write_scene",
                    scene_index=scene_index,
                    role=role,
                    paragraph_count=_paragraph_count(body),
                    fallback=False,
                    retried=retried,
                    actual_word_count=calculate_word_count(body),
                    latency_ms=_latency_ms(start),
                )
                return body, False, []
            raise SchemaError(_format_failures(last_errors))
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_exception = exc
            break
        except Exception as exc:
            last_exception = exc
            if not last_errors:
                last_errors = [{"code": type(exc).__name__, "evidence": str(exc)}]
            trace_event(
                "agents.write_scene.error",
                event_type="retry" if attempt < 2 else "degraded",
                scene_index=scene_index,
                role=role,
                error_type=type(exc).__name__,
                reason=_format_failures(last_errors),
            )
            if attempt < 2:
                retried = True
                retry_codes = [item.get("code", "") for item in last_errors]
                retry_guidance = _build_writer_retry_guidance(retry_codes)
                prompt = (
                    f"{prompt}\n\n## Repair\n"
                    f"Your previous scene failed these field-level checks: {_format_failures(last_errors)}. "
                    "Return the complete scene again."
                )
                if retry_guidance:
                    prompt = f"{prompt}\n\n## Code-specific repair guidance\n{retry_guidance}"
                continue
    if last_body is not None:
        _trace_degraded(
            "scene_writer",
            fields_coerced=[],
            original_value=last_response,
            coerced_value=last_body,
            reason=_format_failures(last_errors),
        )
        trace_event(
            "agents.write_scene",
            scene_index=scene_index,
            role=role,
            paragraph_count=_paragraph_count(last_body),
            fallback=True,
            degraded=True,
            retried=retried,
            actual_word_count=calculate_word_count(last_body),
            latency_ms=_latency_ms(start),
        )
        return last_body, True, last_errors
    first_items = card.paragraph_beats[0].must_show if card.paragraph_beats else []
    second_items = card.paragraph_beats[1].must_show if len(card.paragraph_beats) > 1 else []

    def _join_must_show(items: list[str], opener: str) -> str:
        sentence = "; ".join(item.strip().rstrip(".!?") for item in items if item.strip())
        if not sentence:
            sentence = "the gentle moment continued"
        return f"{opener} {sentence}."

    body = "\n\n".join(
        [
            _join_must_show(first_items, "The narrator showed"),
            _join_must_show(second_items, "The narrator noticed"),
        ]
    )
    for before, after in (
        (" is ", " was "),
        (" are ", " were "),
        (" has ", " had "),
        (" have ", " had "),
    ):
        body = body.replace(before, after)
    trace_event(
        "agents.write_scene",
        event_type="degraded",
        reason="writer_synth_from_must_show",
        fallback=True,
        scene_index=scene_index,
        role=role,
        paragraph_count=_paragraph_count(body),
        actual_word_count=calculate_word_count(body),
        last_error=str(last_exception) if last_exception else _raw_response(last_response),
        latency_ms=_latency_ms(start),
    )
    return body, True, []


def write_draft(blueprint: StoryBlueprint) -> DraftStory:
    start = perf_counter()
    scene_plan = blueprint.scene_plan
    scene_count = scene_plan["scene_count"]
    scenes: list[str] = []
    per_scene_residuals: list[list[str]] = []
    any_fallback = False
    for scene_index in range(scene_count):
        done = blueprint.scene_cards[:scene_index]
        future = blueprint.scene_cards[scene_index + 1 :]
        written_summary = already_written_summary(done)
        future_summary = upcoming_scene_summary(future)
        scene, fallback, residuals = _write_scene_result(
            blueprint,
            scene_index,
            already_written_summary=written_summary,
            upcoming_scene_summary=future_summary,
        )
        card = blueprint.scene_cards[scene_index] if scene_index < len(blueprint.scene_cards) else None
        if card is not None and residuals:
            rewritten = rewrite_scene(
                card,
                scene,
                residuals,
                character_cards=blueprint.character_cards,
                already_written_summary=written_summary,
                upcoming_scene_summary=future_summary,
            )
            repair_failures = rewritten["residual_failures"]
            trace_event(
                "checks.scene_against_card.repair",
                scene_index=scene_index,
                ok=not repair_failures,
            )
            if not repair_failures:
                scene = rewritten["body"]
                residual_codes: list[str] = []
            else:
                residual_codes = [str(item.get("code", "")).strip() for item in repair_failures if str(item.get("code", "")).strip()]
                trace_event(
                    "checks.scene_against_card.unresolved",
                    scene_index=scene_index,
                    hard_failures=[f"{item['code']}: {item['evidence']}" for item in repair_failures],
                )
        else:
            residual_codes = [str(item.get("code", "")).strip() for item in residuals if str(item.get("code", "")).strip()]
        scenes.append(scene)
        per_scene_residuals.append(residual_codes)
        any_fallback = any_fallback or fallback
    body = "\n\n".join(scenes)
    draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
    object.__setattr__(draft, "_writer_residuals", per_scene_residuals)
    trace_event(
        "agents.write_draft",
        fallback=any_fallback,
        scene_count=scene_count,
        actual_word_count=draft.actual_word_count,
        latency_ms=_latency_ms(start),
    )
    return draft


from .rewriter import rewrite_scene
