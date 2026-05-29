from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed, raise_run_failed
from story_engine.prompts.coherence_judge import build_prompt as build_coherence_judge_prompt
from story_engine.prompts.language_judge import LANGUAGE_JUDGE_FAILURE_CODES, build_prompt as build_language_judge_prompt
from story_engine.prompts.safety_judge import build_prompt as build_safety_judge_prompt
from story_engine.schemas import CoherenceFailCode, DraftStory, JudgeReport, RequestClassification, SchemaError, StoryBlueprint
from story_engine.text.scene_split import split_scenes
from story_engine.trace import event as trace_event

from ._common import _latency_ms, _raw_response
from .tool_schemas import (
    COHERENCE_JUDGMENT_TOOL_NAME,
    COHERENCE_JUDGMENT_TOOL_SCHEMA,
    LANGUAGE_JUDGMENT_TOOL_NAME,
    LANGUAGE_JUDGMENT_TOOL_SCHEMA,
    SAFETY_JUDGMENT_TOOL_NAME,
    SAFETY_JUDGMENT_TOOL_SCHEMA,
)


def _judge_from_response(response: Any, expected_name: str) -> JudgeReport:
    if not isinstance(response, dict):
        raise SchemaError("Judge response must be a JSON object")
    verdict = response.get("verdict")
    if verdict not in {"pass", "fail"}:
        raise SchemaError("Judge verdict must be pass or fail")
    judge_name = response.get("judge_name") or expected_name
    if judge_name != expected_name:
        raise SchemaError(f"Judge name must be {expected_name}")
    reason = response.get("reason")
    guidance = response.get("revision_guidance")
    if verdict == "pass":
        if reason is not None or guidance is not None:
            raise SchemaError("Passing judge reports must use null reason and revision_guidance")
    else:
        if not isinstance(reason, str) or not reason.strip():
            raise SchemaError("Failing judge reports need a reason")
        if not isinstance(guidance, str) or not guidance.strip():
            raise SchemaError("Failing judge reports need revision_guidance")
    return JudgeReport(judge_name=expected_name, verdict=verdict, reason=reason, revision_guidance=guidance)


def _pass(name: str) -> JudgeReport:
    return JudgeReport(judge_name=name, verdict="pass", reason=None, revision_guidance=None, fail_codes=[])


def _unknown_judge(name: str, reason: str) -> JudgeReport:
    return JudgeReport(judge_name=name, verdict="unknown", reason=reason, revision_guidance=None, fail_codes=[])


def _coherence_from_response(response: Any) -> JudgeReport:
    if not isinstance(response, dict):
        raise SchemaError("Coherence judge response must be a JSON object")
    passed = response.get("passed")
    if not isinstance(passed, bool):
        raise SchemaError("Coherence judge must return passed boolean")
    if passed:
        if response.get("fail_codes") not in ([], None):
            raise SchemaError("Passing coherence judge must use empty fail_codes")
        return _pass("coherence_judge")
    raw_codes = response.get("fail_codes")
    if not isinstance(raw_codes, list) or not raw_codes:
        raise SchemaError("Failing coherence judge must include fail_codes")
    fail_codes = [CoherenceFailCode(**item) if isinstance(item, dict) else item for item in raw_codes]
    reason = ", ".join(code.code for code in fail_codes)
    evidence = "; ".join(code.evidence for code in fail_codes)
    guidance = f"Revise only the flagged coherence issue while preserving paragraph order. Evidence: {evidence}"
    return JudgeReport(
        judge_name="coherence_judge",
        verdict="fail",
        reason=reason,
        revision_guidance=guidance,
        fail_codes=fail_codes,
    )


def _language_pass() -> JudgeReport:
    return JudgeReport(judge_name="language", verdict="pass", reason="", revision_guidance="", fail_codes=[])


def _language_from_response(response: Any) -> JudgeReport:
    if not isinstance(response, dict):
        raise SchemaError("Language judge response must be a JSON object")
    verdict = response.get("verdict")
    if verdict not in {"pass", "fail"}:
        raise SchemaError("Language judge verdict must be pass or fail")
    failures = response.get("failures")
    if not isinstance(failures, list):
        raise SchemaError("Language judge failures must be a list")
    if verdict == "pass":
        if failures:
            raise SchemaError("Passing language judge must use empty failures")
        return _language_pass()
    if not failures:
        raise SchemaError("Failing language judge must include failures")

    normalized_failures: list[dict[str, str]] = []
    for failure in failures:
        if not isinstance(failure, dict):
            raise SchemaError("Language judge failures must be objects")
        code = failure.get("code")
        evidence = failure.get("evidence")
        guidance = failure.get("revision_guidance")
        if code not in LANGUAGE_JUDGE_FAILURE_CODES:
            raise SchemaError("Language judge failure code is invalid")
        if not isinstance(evidence, str) or len(evidence) > 120:
            raise SchemaError("Language judge evidence must be a string <= 120 chars")
        evidence = evidence.replace('"', "")
        if not isinstance(guidance, str) or not guidance.strip():
            raise SchemaError("Language judge revision_guidance must be non-empty")
        normalized_failures.append({"code": code, "evidence": evidence, "revision_guidance": guidance.strip()})

    reason = "; ".join(f'{failure["code"]}: "{failure["evidence"]}"' for failure in normalized_failures)
    revision_guidance = " ".join(
        f'{failure["code"]}: {failure["revision_guidance"]} (offender: "{failure["evidence"]}")'
        for failure in normalized_failures
    )
    return JudgeReport(
        judge_name="language",
        verdict="fail",
        reason=reason,
        revision_guidance=revision_guidance,
        fail_codes=[],
    )


def judge_coherence(draft: DraftStory, blueprint: StoryBlueprint, classification: RequestClassification, request: str) -> JudgeReport:
    start = perf_counter()
    scenes = None
    reason = None
    try:
        candidate = split_scenes(draft.body, blueprint, draft=draft)
    except Exception as exc:
        candidate = None
        reason = f"exception:{type(exc).__name__}"
    if candidate is None or not candidate:
        scenes = None
        if reason is None:
            reason = "empty"
    elif len(candidate) != blueprint.scene_plan["scene_count"]:
        scenes = None
        reason = "shape_mismatch"
    elif not all(str(scene).strip() for scene in candidate):
        scenes = None
        reason = "empty_element"
    else:
        scenes = candidate
    if scenes is None:
        trace_event("agents.coherence_judge.scene_labels_degraded", reason=reason or "unknown")
    prompt = build_coherence_judge_prompt(draft, blueprint, classification, request, scenes=scenes)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            report = _coherence_from_response(
                model_client.call_model_tool(
                    prompt,
                    tool_name=COHERENCE_JUDGMENT_TOOL_NAME,
                    tool_schema=COHERENCE_JUDGMENT_TOOL_SCHEMA,
                    temperature=AGENT_TEMPERATURES["coherence_judge"],
                    agent_name="coherence_judge",
                    iteration=attempt,
                )
            )
            trace_event("agents.judge", judge_name="coherence_judge", verdict=report.verdict, fallback=False, latency_ms=_latency_ms(start))
            return report
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                trace_event("agents.judge", event_type="retry", judge_name="coherence_judge", attempt=attempt + 2, reason=f"{type(exc).__name__}: {exc}")
                prompt = f"{prompt}\n\n# Repair\nThe previous coherence judge response failed parsing: {type(exc).__name__}: {exc}. Return the required JSON shape only."
    report = _unknown_judge("coherence_judge", f"coherence judge unavailable after retries: {last_error}")
    trace_event("agents.judge", judge_name="coherence_judge", verdict=report.verdict, fallback=False, latency_ms=_latency_ms(start))
    return report


def judge_language(draft: DraftStory) -> JudgeReport:
    start = perf_counter()
    prompt = build_language_judge_prompt(draft)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            report = _language_from_response(
                model_client.call_model_tool(
                    prompt,
                    tool_name=LANGUAGE_JUDGMENT_TOOL_NAME,
                    tool_schema=LANGUAGE_JUDGMENT_TOOL_SCHEMA,
                    temperature=AGENT_TEMPERATURES["language_judge"],
                    agent_name="language_judge",
                    iteration=attempt,
                )
            )
            trace_event("agents.judge", judge_name="language", verdict=report.verdict, fallback=False, latency_ms=_latency_ms(start))
            return report
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                trace_event("agents.judge", event_type="retry", judge_name="language", attempt=attempt + 2, reason=f"{type(exc).__name__}: {exc}")
                prompt = f"{prompt}\n\n# Repair\nThe previous language judge response failed parsing: {type(exc).__name__}: {exc}. Return the required JSON shape only."
    trace_event(
        "agents.judge",
        judge_name="language",
        event_type="degraded",
        verdict="pass",
        reason="parse_or_tool_exhausted",
        error_type=type(last_error).__name__,
        error=str(last_error),
        fallback=True,
        latency_ms=_latency_ms(start),
    )
    return _language_pass()


def judge_safety(draft: DraftStory, blueprint: StoryBlueprint, classification: RequestClassification, request: str) -> JudgeReport:
    start = perf_counter()
    prompt = build_safety_judge_prompt(draft, blueprint, classification, request)
    last_response: Any = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            last_response = model_client.call_model_tool(
                prompt,
                tool_name=SAFETY_JUDGMENT_TOOL_NAME,
                tool_schema=SAFETY_JUDGMENT_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["safety_judge"],
                agent_name="safety_judge",
                iteration=attempt,
            )
            report = _judge_from_response(last_response, "safety_judge")
            trace_event("agents.judge", judge_name="safety_judge", verdict=report.verdict, fallback=False, latency_ms=_latency_ms(start))
            return report
        except RunFailed:
            raise
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                trace_event("agents.judge", event_type="retry", judge_name="safety_judge", attempt=attempt + 2, reason=f"{type(exc).__name__}: {exc}")
                prompt = f"{prompt}\n\n# Repair\nThe previous safety judge response failed parsing: {type(exc).__name__}: {exc}. Return the required JSON shape only."
    raise_run_failed(
        agent_name="safety_judge",
        failure_category="safety_fail",
        last_raw_response=_raw_response(last_response) or (str(last_error) if last_error else None),
        attempt_count=3,
    )
