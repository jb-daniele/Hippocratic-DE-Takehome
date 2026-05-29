from __future__ import annotations

import re
from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.checks import calculate_word_count
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.polish_language import build_prompt as build_polish_language_prompt
from story_engine.prompts.polish_safety import build_prompt as build_polish_safety_prompt
from story_engine.schemas import DraftStory, JudgeReport, SchemaError, StoryBlueprint
from story_engine.text.normalizers import normalize_dialogue
from story_engine.trace import event as trace_event

from ._common import PolishNoOpError, _latency_ms, _trace_degraded
from .writer import _paragraph_count


class _PolishParagraphCountError(SchemaError):
    def __init__(self, message, *, input_count, output_count):
        super().__init__(message)
        self.input_count = input_count
        self.output_count = output_count


def _polish_prompt_for_failure(draft: DraftStory, failure: JudgeReport, blueprint: StoryBlueprint) -> str:
    offenders = _polish_offenders(failure)
    if failure.judge_name == "safety_judge":
        prompt = build_polish_safety_prompt(draft, failure, blueprint)
    else:
        prompt = build_polish_language_prompt(draft, failure, blueprint)
    if offenders:
        prompt = f"{prompt}\n\n# Offenders\n- offender_list: {offenders}"
    return prompt


def _polish_body_from_response(response: Any) -> str:
    if not isinstance(response, dict):
        raise SchemaError("Polish response must be a JSON object")
    body = response.get("body")
    if not isinstance(body, str) or not body.strip():
        raise SchemaError("Polish response must include body")
    return body


def _polish_offenders(failure: JudgeReport) -> list[str]:
    offenders: list[str] = []
    for source in (failure.reason, failure.revision_guidance):
        if not source:
            continue
        offenders.extend(re.findall(r"'([^']+)'", source))
        offenders.extend(re.findall(r'"([^"]+)"', source))
    deduped: list[str] = []
    seen: set[str] = set()
    for offender in offenders:
        normalized = offender.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(offender.strip())
    return deduped[:8]


def _polish_made_progress(before: str, after: str, offenders: list[str]) -> bool:
    if before == after:
        return False
    if not offenders:
        return True
    for offender in offenders:
        if offender.lower() in before.lower() and offender.lower() not in after.lower():
            return True
    return False


def polish(draft: DraftStory, failure: JudgeReport, blueprint: StoryBlueprint) -> DraftStory:
    start = perf_counter()
    input_paragraph_count = _paragraph_count(draft.body)
    offenders = _polish_offenders(failure)
    prompt = _polish_prompt_for_failure(draft, failure, blueprint)
    last_error: Exception | None = None
    for attempt in (1, 2, 3):
        try:
            body = _polish_body_from_response(
                model_client.call_model_json(
                    prompt,
                    temperature=AGENT_TEMPERATURES["polish"],
                    max_tokens=4000,
                    agent_name="polish",
                    iteration=attempt,
                )
            )
            body = normalize_dialogue(body)[0]
            output_paragraph_count = _paragraph_count(body)
            if output_paragraph_count != input_paragraph_count:
                raise _PolishParagraphCountError(
                    f"Polish changed paragraph count from {input_paragraph_count} to {output_paragraph_count}",
                    input_count=input_paragraph_count,
                    output_count=output_paragraph_count,
                )
            if not _polish_made_progress(draft.body, body, offenders):
                raise PolishNoOpError("Polish did not change the flagged offenders", offenders=offenders)
            polished = DraftStory(title=draft.title, body=body, actual_word_count=calculate_word_count(body))
            trace_event("agents.polish", fallback=False, judge_name=failure.judge_name, attempt=attempt, latency_ms=_latency_ms(start))
            return polished
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_error = exc
            break
        except Exception as exc:
            last_error = exc
            paragraph_count_failure = isinstance(exc, _PolishParagraphCountError)
            no_op_failure = isinstance(exc, PolishNoOpError)
            model_client.log_validator_decision(
                check="polish_no_op" if no_op_failure else ("polish_paragraph_count" if paragraph_count_failure else "polish_error"),
                verdict="rejected",
                judge_name=failure.judge_name,
                attempt=attempt,
                error_type=type(exc).__name__,
                error=str(exc),
                offenders=offenders,
            )
            if attempt < 3:
                reason = "polish_no_op" if no_op_failure else ("paragraph_count_drift" if paragraph_count_failure else type(exc).__name__)
                trace_event("agents.polish", event_type="retry", judge_name=failure.judge_name, attempt=attempt + 1, reason=reason)
                if paragraph_count_failure:
                    prompt = (
                        f"{prompt}\n\n# Paragraph Preservation Retry\n"
                        f"Your previous polish changed the paragraph count from {exc.input_count} to {exc.output_count}. "
                        f"Return the full story body with exactly {exc.input_count} paragraphs. "
                        "Preserve paragraph breaks and paragraph order. Do not merge, split, remove, "
                        f"summarize, or reorder paragraphs. If you cannot preserve exactly {exc.input_count} "
                        "paragraphs, return the original body unchanged."
                    )
                elif no_op_failure:
                    prompt = (
                        f"{prompt}\n\n# Retry\n"
                        f"The previous polish attempt left the offender list unchanged: {offenders}. "
                        "Change or remove those offender spans while preserving plot and paragraph structure."
                    )
                else:
                    prompt = (
                        f"{prompt}\n\n# Retry\nThe previous polish attempt failed with {type(exc).__name__}: {exc}. "
                        "Return only valid JSON with a non-empty body string."
                    )
                continue
            trace_event("agents.polish", fallback=False, judge_name=failure.judge_name, error_type=type(exc).__name__, latency_ms=_latency_ms(start))
            _trace_degraded(
                "polish",
                fields_coerced=["body"],
                original_value=str(exc),
                coerced_value=draft.body,
                reason=(
                    f"polish_paragraph_preservation_failed input_count={input_paragraph_count}"
                    if paragraph_count_failure
                    else f"polish exhausted repairs: {type(exc).__name__}: {exc}"
                ),
            )
            return draft
    trace_event(
        "agents.polish",
        event_type="degraded",
        reason="polish_non_safety_run_failed",
        fallback=True,
        judge_name=failure.judge_name,
        error_type=type(last_error).__name__ if last_error else None,
        latency_ms=_latency_ms(start),
    )
    _trace_degraded(
        "polish",
        fields_coerced=["body"],
        original_value=str(last_error) if last_error else None,
        coerced_value=draft.body,
        reason=f"polish exhausted repairs: {type(last_error).__name__}: {last_error}" if last_error else "polish exhausted repairs",
    )
    return draft
