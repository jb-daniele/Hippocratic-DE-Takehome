from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine.agents import classify_request
from story_engine.categories import CATEGORIES, FALLBACK_CATEGORY_ID, STORY_MODE_TO_CATEGORY
from story_engine.guardrails import pre_request_guard
from story_engine.schemas import MainCharacter, RequestClassification, RequestOptions, SafetyAssessment
from story_engine.trace import event as trace_event

from ._common import _latency_ms

def _trace_classify(
    classification: RequestClassification,
    *,
    skip_reason: str,
    latency_ms: int,
    few_shot_examples_retrieved: int = 0,
    llm_call: bool,
) -> None:
    trace_event(
        "agent.classify",
        category_id=classification.category_id,
        category_display_name=classification.category_display_name,
        classifier_confidence=classification.classifier_confidence,
        classifier_rationale=classification.classifier_rationale,
        classifier_matched_signals=classification.matched_signals,
        fallback=classification.fallback,
        classifier_skipped=classification.classifier_skipped,
        skip_reason=skip_reason,
        latency_ms=latency_ms,
        few_shot_examples_retrieved=few_shot_examples_retrieved,
        llm_call=llm_call,
    )


def _get_option(options: RequestOptions | dict[str, Any], key: str) -> Any:
    if isinstance(options, dict):
        return options[key]
    return getattr(options, key)


def _category_by_id(category_id: str) -> dict[str, Any]:
    for category in CATEGORIES:
        if category["id"] == category_id:
            return category
    for category in CATEGORIES:
        if category["id"] == FALLBACK_CATEGORY_ID:
            return category
    return CATEGORIES[0]


def _main_characters(options: RequestOptions | dict[str, Any]) -> list[MainCharacter]:
    raw = str(_get_option(options, "main_character_name"))
    names = [part.strip() for part in raw.split(",") if part.strip()]
    return [MainCharacter(name=name, role="main") for name in names]


def _with_options(request: str, options: RequestOptions | dict[str, Any], base: RequestClassification) -> RequestClassification:
    characters = _main_characters(options)
    return RequestClassification(
        request_text=request,
        selected_story_mode=_get_option(options, "story_mode"),
        main_character_name=_get_option(options, "main_character_name"),
        category_id=base.category_id,
        category_display_name=base.category_display_name,
        classifier_confidence=base.classifier_confidence,
        classifier_rationale=base.classifier_rationale,
        matched_signals=base.matched_signals,
        fallback=base.fallback,
        classifier_skipped=base.classifier_skipped,
        main_characters=characters,
    )


def category_router(request: str, options: RequestOptions | dict[str, Any]) -> RequestClassification:
    start = perf_counter()
    story_mode = _get_option(options, "story_mode")
    if story_mode != "auto_detect":
        category_id = STORY_MODE_TO_CATEGORY.get(story_mode, FALLBACK_CATEGORY_ID)
        category = _category_by_id(category_id)
        base = RequestClassification(
            request_text=request,
            selected_story_mode=story_mode,
            main_character_name="",
            category_id=category["id"],
            category_display_name=category["display_name"],
            classifier_confidence="high",
            classifier_rationale="User-selected via story_mode",
            matched_signals=["user_selection"],
            fallback=False,
            classifier_skipped=True,
            main_characters=[],
        )
        classification = _with_options(request, options, base)
        latency_ms = _latency_ms(start)
        trace_event("pipeline.category_router", mode=story_mode, category_id=classification.category_id, latency_ms=latency_ms)
        _trace_classify(
            classification,
            skip_reason="user_selected_story_mode",
            latency_ms=latency_ms,
            llm_call=False,
        )
        return classification

    classification = classify_request(request, story_mode_hint="auto_detect")
    routed = _with_options(request, options, classification)
    latency_ms = _latency_ms(start)
    trace_event("pipeline.category_router", mode=story_mode, category_id=routed.category_id, latency_ms=latency_ms)
    _trace_classify(routed, skip_reason="", latency_ms=latency_ms, llm_call=not routed.classifier_skipped)
    return routed


def understand(request: str, options: RequestOptions | dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()
    classification = category_router(request, options)
    pre_guard = pre_request_guard(request)
    safety = SafetyAssessment(
        allowed=pre_guard["allowed"],
        redirected_request=str(pre_guard["redirected_request"]),
        reason=pre_guard["reason"],
    )
    trace_event("pipeline.understand", category_id=classification.category_id, safety_allowed=safety.allowed, latency_ms=_latency_ms(start))
    return {"classification": classification, "safety": safety}
