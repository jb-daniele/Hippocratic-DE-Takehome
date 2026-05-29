from __future__ import annotations

from time import perf_counter

from story_engine import model_client
from story_engine.checks import calculate_word_count
from story_engine.config import AGENT_TEMPERATURES
from story_engine.prompts.scene_stitcher import build_prompt as build_scene_stitcher_prompt
from story_engine.schemas import DraftStory, SchemaError, StoryBlueprint
from story_engine.text.normalizers import normalize_dialogue
from story_engine.trace import event as trace_event

from ._common import _latency_ms, _trace_degraded
from .writer import _paragraph_count

_MIN_WORD_RATIO = 0.9
_MAX_WORD_RATIO = 1.1


def compute_scene_boundaries(scenes: list[str]) -> list[dict[str, int]]:
    boundaries: list[dict[str, int]] = []
    cursor = 1
    for index, scene in enumerate(scenes, start=1):
        paragraph_count = max(1, len([paragraph for paragraph in scene.split("\n\n") if paragraph.strip()]))
        boundaries.append(
            {
                "scene_number": index,
                "start_paragraph": cursor,
                "end_paragraph": cursor + paragraph_count - 1,
            }
        )
        cursor += paragraph_count
    return boundaries
def _is_word_count_close_enough(pre_word_count: int, post_word_count: int) -> bool:
    return _MIN_WORD_RATIO * pre_word_count <= post_word_count <= _MAX_WORD_RATIO * pre_word_count


def stitch_scenes(blueprint: StoryBlueprint, draft: DraftStory, stitch_failure: dict) -> DraftStory:
    start = perf_counter()
    expected_paragraph_count = stitch_failure["expected_paragraph_count"]
    pre_paragraph_count = _paragraph_count(draft.body)
    pre_quote_count = draft.body.count('"')
    pre_word_count = draft.actual_word_count
    scene_count = blueprint.scene_plan["scene_count"]
    scenes = list(draft.scenes) if draft.scenes else []
    scene_boundaries = compute_scene_boundaries(scenes) if scenes else []
    base_prompt = build_scene_stitcher_prompt(
        blueprint,
        draft.body,
        scene_count,
        scene_boundaries,
        stitch_failure,
        expected_paragraph_count,
    )
    last_error: Exception | None = None
    try:
        response = model_client.call_model_json(
            base_prompt,
            temperature=AGENT_TEMPERATURES["scene_stitcher"],
            max_tokens=4000,
            agent_name="scene_stitcher",
            iteration=0,
        )
        if not isinstance(response, dict):
            raise SchemaError("stitcher scene response must be a JSON object")
        raw_body = response.get("body")
        if not isinstance(raw_body, str) or not raw_body.strip():
            raise SchemaError("stitcher scene must return a body")
        body = raw_body.strip()
        body = normalize_dialogue(body)[0]
        post_paragraph_count = _paragraph_count(body)
        if post_paragraph_count != pre_paragraph_count:
            raise SchemaError(f"Scene stitcher changed paragraph count: pre={pre_paragraph_count}, post={post_paragraph_count}")
        post_quote_count = body.count('"')
        if post_quote_count != pre_quote_count:
            raise SchemaError(f"Scene stitcher changed quote count: pre={pre_quote_count}, post={post_quote_count}")
        post_word_count = calculate_word_count(body)
        if not _is_word_count_close_enough(pre_word_count, post_word_count):
            raise SchemaError(
                f"Scene stitcher changed word count outside allowed band: pre={pre_word_count}, post={post_word_count}, "
                f"allowed=[{int(pre_word_count * _MIN_WORD_RATIO)}, {int(pre_word_count * _MAX_WORD_RATIO)}]"
            )
        trace_event(
            "agents.stitch_scenes",
            fallback=False,
            pre_paragraph_count=pre_paragraph_count,
            post_paragraph_count=post_paragraph_count,
            paragraphs_removed=0,
            pre_word_count=pre_word_count,
            post_word_count=post_word_count,
            latency_ms=_latency_ms(start),
        )
        return DraftStory(title=draft.title, body=body, actual_word_count=post_word_count, scenes=[])
    except Exception as exc:
        last_error = exc
    restored_body = normalize_dialogue(draft.body)[0]
    post_word_count = calculate_word_count(restored_body)
    post_paragraph_count = _paragraph_count(restored_body)
    _trace_degraded(
        "scene_stitcher",
        fields_coerced=["body"],
        original_value=str(last_error) if last_error else None,
        coerced_value=restored_body,
        reason="scene stitcher exhausted repairs; preserving pre-stitch paragraph body unchanged",
    )
    trace_event(
        "agents.stitch_scenes",
        degraded=True,
        error_type=type(last_error).__name__ if last_error else "unknown",
        fallback_to_original_assembled_body=True,
        pre_paragraph_count=pre_paragraph_count,
        post_paragraph_count=post_paragraph_count,
        paragraphs_removed=pre_paragraph_count - post_paragraph_count,
        pre_word_count=pre_word_count,
        post_word_count=post_word_count,
        latency_ms=_latency_ms(start),
    )
    return DraftStory(title=draft.title, body=restored_body, actual_word_count=post_word_count, scenes=[])
