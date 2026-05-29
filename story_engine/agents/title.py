from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.title_writer import build_prompt as build_title_writer_prompt
from story_engine.schemas import SchemaError, StoryBlueprint
from story_engine.text.title_guard import is_bad_title, is_valid_title
from story_engine.trace import event as trace_event

from ._common import _latency_ms, _one_line, _raw_response
from .tool_schemas import TITLE_TOOL_NAME, TITLE_TOOL_SCHEMA


def _title_from_response(response: Any) -> str:
    if not isinstance(response, dict):
        raise SchemaError("Title writer response must be a JSON object")
    title = response.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SchemaError("Title writer must return a non-empty title")
    return _one_line(title, "title")


def _title_rejection_reason(title: str) -> str | None:
    stripped = title.strip()
    if not stripped or stripped != title.strip().strip('"“”'):
        return "title has empty text or surrounding quotes"
    words = stripped.split()
    if not 2 <= len(words) <= 7:
        return f"length rejected: {len(words)} words"
    if is_bad_title(stripped):
        return "banned phrase rejected"
    for index, word in enumerate(words):
        if index > 0 and word.lower() in {"a", "an", "and", "the", "of", "in", "on", "to", "for", "with", "at", "by"}:
            continue
        if not word[0].isupper():
            return f"casing rejected: {word}"
    return None


def write_title(blueprint: StoryBlueprint) -> str:
    start = perf_counter()
    prompt = build_title_writer_prompt(blueprint)
    last_title: str | None = None
    last_response: Any = None
    last_reason = "title_rejected_or_error"
    for attempt in (1, 2, 3):
        try:
            last_response = model_client.call_model_tool(
                prompt,
                tool_name=TITLE_TOOL_NAME,
                tool_schema=TITLE_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["title_writer"],
                agent_name="title_writer",
                iteration=attempt,
            )
            title = _title_from_response(
                last_response
            )
            last_title = title
            if is_valid_title(title):
                trace_event("agents.write_title", fallback=False, attempt=attempt, latency_ms=_latency_ms(start))
                return title
            last_reason = _title_rejection_reason(title) or "title_rejected"
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_reason = f"{type(exc).__name__}: {exc}"
            trace_event("agents.write_title", fallback=False, attempt=attempt, error_type=type(exc).__name__, latency_ms=_latency_ms(start))
        except Exception as exc:
            last_reason = f"{type(exc).__name__}: {exc}"
            trace_event("agents.write_title", fallback=False, attempt=attempt, error_type=type(exc).__name__, latency_ms=_latency_ms(start))
        if attempt < 3:
            trace_event("agents.write_title", event_type="retry", attempt=attempt + 1, reason=last_reason)
            prompt = (
                prompt
                + f"\n\n# Reminder\nThe previous attempt was rejected because: {last_reason}. Pick a 2-7 word, title-cased title "
                "that is specific to this story. Do not use any phrase from the banned list."
            )
    if last_title and not is_bad_title(last_title):
        trace_event(
            "agents.write_title",
            event_type="degraded",
            reason="title_writer_last_title_after_retries",
            fallback=True,
            latency_ms=_latency_ms(start),
        )
        return last_title
    if blueprint.main_characters:
        title = f"{blueprint.main_characters[0].title()} and the Quiet Night"
        reason = "title_writer_synth_from_main_character"
    else:
        title = blueprint.category_display_name
        reason = "title_writer_category_display_name"
    trace_event(
        "agents.write_title",
        event_type="degraded",
        reason=reason,
        fallback=True,
        last_raw_response=_raw_response(last_response),
        last_reason=last_reason,
        latency_ms=_latency_ms(start),
    )
    return title
