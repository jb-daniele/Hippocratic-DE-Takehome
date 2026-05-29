from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine.schemas import SchemaError
from story_engine.trace import event as trace_event


def _latency_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def _raw_response(response: Any) -> str | None:
    if response is None:
        return None
    if isinstance(response, str):
        return response
    if hasattr(response, "model_dump"):
        response = response.model_dump()
    if hasattr(response, "to_dict"):
        response = response.to_dict()
    return repr(response)


def _short(value: Any) -> str:
    text = _raw_response(value) or ""
    return text[:200]


def _trace_degraded(
    agent_name: str,
    *,
    fields_coerced: list[str],
    original_value: Any,
    coerced_value: Any,
    reason: str,
) -> None:
    trace_event(
        "degraded_passthrough",
        agent_name=agent_name,
        fields_coerced=fields_coerced,
        original_value=_short(original_value),
        coerced_value=_short(coerced_value),
        reason=reason,
    )


def _format_failures(failures: list[dict[str, Any]]) -> str:
    return "; ".join(f"{item.get('code')}: {item.get('evidence')}" for item in failures)


class ArcValidationError(SchemaError):
    def __init__(self, message: str, *, check: str, retry_details: str, details: dict[str, Any]):
        super().__init__(message)
        self.check = check
        self.retry_details = retry_details
        self.details = details


class SceneCardValidationError(SchemaError):
    def __init__(self, message: str, *, issues: list[dict[str, Any]]):
        super().__init__(message)
        self.issues = issues


class PolishNoOpError(SchemaError):
    def __init__(self, message: str, *, offenders: list[str]):
        super().__init__(message)
        self.offenders = offenders


def _one_line(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{field} must be a non-empty string")
    return " ".join(value.split())
