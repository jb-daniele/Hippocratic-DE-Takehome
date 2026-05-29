from __future__ import annotations

from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Any

from story_engine.text.scene_split import split_scenes
from story_engine.trace import event as trace_event

# Planner and judge fan-outs are safe to run in threads: each agent function is
# pure with respect to its inputs, trace writes are append-only under a lock, and
# call_model_json does not share mutable request state.

# These deterministic checks are approval gates, not just warning signals.
# Keeping the list explicit makes the polish activation surface visible.
APPROVAL_BLOCKING_CHECKS = (
    "phrase_repetition",
)

_split_scenes = split_scenes


def _latency_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def _trace_check_result(stage: str, check_name: str, result: dict[str, Any], **extra: Any) -> None:
    trace_event(
        stage,
        event_type="check_result",
        check_name=check_name,
        passed=bool(result.get("ok", False)),
        severity=result.get("severity"),
        route=result.get("route"),
        issues=result.get("issues"),
        details={key: value for key, value in result.items() if key not in {"ok", "severity", "route", "issues"}},
        **extra,
    )


def _trace_route(stage: str, route: str, reason: str, **extra: Any) -> None:
    trace_event(stage, event_type="route", route=route, reason=reason, **extra)


def _submit_with_trace_context(executor: ThreadPoolExecutor, fn, *args: Any):
    context = copy_context()
    return executor.submit(context.run, fn, *args)
