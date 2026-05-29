from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.categories import CATEGORIES, FALLBACK_CATEGORY_ID
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.classifier import build_prompt
from story_engine.schemas import RequestClassification, SchemaError, validate_category_id
from story_engine.trace import event as trace_event

from ._common import _latency_ms
from .tool_schemas import CLASSIFICATION_TOOL_NAME, CLASSIFICATION_TOOL_SCHEMA


def _category_by_id(category_id: str) -> dict[str, Any]:
    for category in CATEGORIES:
        if category["id"] == category_id:
            return category
    return CATEGORIES[0]


def _blank_classification(
    request: str,
    story_mode_hint: str,
    category_id: str,
    confidence: str,
    rationale: str,
    matched_signals: list[str],
    fallback: bool,
) -> RequestClassification:
    category = _category_by_id(category_id)
    return RequestClassification(
        request_text=request,
        selected_story_mode=story_mode_hint,
        main_character_name="",
        category_id=category["id"],
        category_display_name=category["display_name"],
        classifier_confidence=confidence,
        classifier_rationale=rationale,
        matched_signals=matched_signals,
        fallback=fallback,
        classifier_skipped=False,
        main_characters=[],
    )


def _classification_from_response(request: str, story_mode_hint: str, response: Any) -> RequestClassification:
    if not isinstance(response, dict):
        raise SchemaError("Classifier response must be a JSON object")

    category_id = response.get("category_id")
    confidence = response.get("confidence")
    rationale = response.get("rationale")
    matched_signals = response.get("matched_signals")
    fallback = response.get("fallback")

    if not validate_category_id(category_id):
        raise SchemaError("Classifier returned invalid category_id")
    if confidence not in {"high", "medium", "low"}:
        raise SchemaError("Classifier returned invalid confidence")
    if not isinstance(rationale, str) or not rationale.strip():
        raise SchemaError("Classifier returned invalid rationale")
    if not isinstance(matched_signals, list) or not all(isinstance(signal, str) for signal in matched_signals):
        raise SchemaError("Classifier returned invalid matched_signals")
    if not isinstance(fallback, bool):
        raise SchemaError("Classifier returned invalid fallback")

    return _blank_classification(
        request=request,
        story_mode_hint=story_mode_hint,
        category_id=category_id,
        confidence=confidence,
        rationale=rationale,
        matched_signals=matched_signals,
        fallback=fallback,
    )


def _signal_matches(text: str, signals: list[str]) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for signal in signals:
        normalized = signal.strip().lower()
        if normalized and normalized in lowered:
            matches.append(signal)
    return matches


def _deterministic_category_route(request: str, story_mode_hint: str) -> RequestClassification | None:
    scores: list[tuple[int, dict[str, Any], list[str], list[str]]] = []
    for category in CATEGORIES:
        inclusions = _signal_matches(request, category.get("inclusion_signals", []))
        exclusions = _signal_matches(request, category.get("exclusion_signals", []))
        scores.append((len(inclusions) - len(exclusions), category, inclusions, exclusions))
    scores.sort(key=lambda item: item[0], reverse=True)
    if not scores or scores[0][0] <= 0:
        return None
    lead_score, lead_category, lead_inclusions, lead_exclusions = scores[0]
    second_score = scores[1][0] if len(scores) > 1 else -999
    if lead_score - second_score < 2:
        return None
    rationale = "Deterministic classifier route via inclusion/exclusion signals"
    matched = list(dict.fromkeys([*lead_inclusions, *[f"not:{signal}" for signal in lead_exclusions]]))
    return _blank_classification(
        request=request,
        story_mode_hint=story_mode_hint,
        category_id=str(lead_category["id"]),
        confidence="high",
        rationale=rationale,
        matched_signals=matched,
        fallback=False,
    )


def classify_request(request: str, story_mode_hint: str) -> RequestClassification:
    start = perf_counter()
    deterministic = _deterministic_category_route(request, story_mode_hint)
    if deterministic is not None:
        trace_event(
            "agents.classify_request",
            fallback=deterministic.fallback,
            category_id=deterministic.category_id,
            deterministic=True,
            latency_ms=_latency_ms(start),
        )
        return deterministic

    prompt = build_prompt(request, story_mode_hint, CATEGORIES)
    candidate_prompt = prompt
    last_error: Exception | None = None
    last_response: Any = None
    for attempt in range(3):
        try:
            attempt_start = perf_counter()
            last_response = model_client.call_model_tool(
                candidate_prompt,
                tool_name=CLASSIFICATION_TOOL_NAME,
                tool_schema=CLASSIFICATION_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["classifier"],
                agent_name="classifier",
                iteration=attempt,
            )
            classification = _classification_from_response(request, story_mode_hint, last_response)
            trace_event(
                "agent.classify.llm_attempt",
                attempt=attempt + 1,
                ok=True,
                category_id=classification.category_id,
                latency_ms=_latency_ms(attempt_start),
            )
            trace_event(
                "agents.classify_request",
                fallback=classification.fallback,
                category_id=classification.category_id,
                latency_ms=_latency_ms(start),
            )
            return classification
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_error = exc
            break
        except Exception as exc:
            last_error = exc
            trace_event(
                "agent.classify.llm_attempt",
                attempt=attempt + 1,
                ok=False,
                error_type=type(exc).__name__,
                latency_ms=_latency_ms(attempt_start),
            )
            if attempt < 2:
                trace_event("agents.classify_request", event_type="retry", attempt=attempt + 2, reason=type(exc).__name__)
                candidate_prompt = (
                    f"{prompt}\n\nStrict retry: return only a valid JSON object using one listed category_id, "
                    "confidence high/medium/low, rationale, matched_signals array, and fallback boolean. "
                    f"Previous classifier validation error: {type(exc).__name__}: {exc}"
                )

    if isinstance(last_response, dict) and validate_category_id(last_response.get("category_id")):
        confidence = last_response.get("confidence")
        rationale = last_response.get("rationale")
        matched_signals = last_response.get("matched_signals")
        fallback = last_response.get("fallback")
        classification = _blank_classification(
            request=request,
            story_mode_hint=story_mode_hint,
            category_id=str(last_response["category_id"]),
            confidence=confidence if confidence in {"high", "medium", "low"} else "low",
            rationale=rationale.strip() if isinstance(rationale, str) and rationale.strip() else "degraded_after_retries",
            matched_signals=matched_signals if isinstance(matched_signals, list) and all(isinstance(signal, str) for signal in matched_signals) else [],
            fallback=fallback if isinstance(fallback, bool) else True,
        )
        trace_event(
            "agents.classify_request",
            event_type="degraded",
            reason="classifier_parseable_after_retries",
            fallback=True,
            category_id=classification.category_id,
            latency_ms=_latency_ms(start),
        )
        return classification
    classification = _blank_classification(
        request,
        story_mode_hint,
        FALLBACK_CATEGORY_ID,
        "low",
        "classifier_fallback_after_retries",
        [],
        True,
    )
    trace_event(
        "agents.classify_request",
        event_type="degraded",
        reason="classifier_fallback_after_retries",
        fallback=True,
        category_id=classification.category_id,
        last_error=str(last_error) if last_error else None,
        latency_ms=_latency_ms(start),
    )
    return classification
