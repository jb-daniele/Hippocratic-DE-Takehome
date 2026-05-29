from typing import Any

from story_engine.trace import event as trace_event


_BLOCKED_SIGNALS = (
    "abuse",
    "assault",
    "graphic violence",
    "gore",
    "bloody",
    "hate",
    "knife",
    "murder",
    "self harm",
    "suicide",
    "sexual",
    "explicit",
)


def pre_request_guard(request: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(request, dict):
        text = " ".join(str(value) for value in request.values())
        redirected_request = dict(request)
    else:
        text = request
        redirected_request = request

    lowered = text.lower()
    for signal in _BLOCKED_SIGNALS:
        if signal in lowered:
            trace_event("guardrails.pre_request", allowed=False, blocked_signal=signal)
            return {
                "allowed": False,
                "redirected_request": redirected_request,
                "reason": f"Blocked unsafe bedtime-story request: {signal}.",
            }

    trace_event("guardrails.pre_request", allowed=True, blocked_signal=None)
    return {"allowed": True, "redirected_request": redirected_request, "reason": ""}
