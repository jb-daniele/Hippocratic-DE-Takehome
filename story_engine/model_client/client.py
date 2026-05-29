import json
import os
import re
import shutil
import threading
from json import JSONDecodeError
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from story_engine.config import LOGS_DIR, MODEL, STORIES_DIR
from story_engine.errors import raise_run_failed
from story_engine.trace import current_run_id, ensure_dir, event as trace_event, partitioned_log_dir, prompt_payload


load_dotenv()


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_LOG_LOCK = threading.Lock()
_SEQUENCES: dict[str, int] = {}
_CLIENT: OpenAI | None = None


def strip_json_fence(text: str) -> str:
    match = _JSON_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _utc_now_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _run_id() -> str:
    return current_run_id() or "untraced"


def llm_log_path(run_id: str | None = None) -> Path:
    active_run_id = run_id or _run_id()
    story_log = STORIES_DIR / active_run_id / "llm-calls.jsonl"
    if story_log.parent.exists():
        return story_log
    if active_run_id == "untraced":
        utc_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return Path(LOGS_DIR) / utc_date / f"{active_run_id}-llm-calls.jsonl"
    return partitioned_log_dir(active_run_id, root=LOGS_DIR) / f"{active_run_id}-llm-calls.jsonl"


def copy_llm_log_to_story_dir(trace_id: str | None, story_run_id: str) -> None:
    source = llm_log_path(trace_id)
    if not source.exists():
        return
    destination = STORIES_DIR / story_run_id / "llm-calls.jsonl"
    ensure_dir(destination.parent)
    if source.resolve() == destination.resolve():
        return
    shutil.copyfile(source, destination)


def _next_sequence(run_id: str) -> int:
    with _LOG_LOCK:
        sequence = _SEQUENCES.get(run_id, 0) + 1
        _SEQUENCES[run_id] = sequence
        return sequence


def _write_or_replace_record(record: dict[str, Any]) -> None:
    path = llm_log_path(str(record["run_id"]))
    ensure_dir(path.parent)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with _LOG_LOCK:
        lines: list[str] = []
        replaced = False
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for index, existing in enumerate(lines):
            try:
                payload = json.loads(existing)
            except json.JSONDecodeError:
                continue
            if payload.get("sequence") == record.get("sequence"):
                lines[index] = line
                replaced = True
                break
        if replaced:
            path.write_text("".join(lines), encoding="utf-8")
        else:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)


def _base_record(
    *,
    run_id: str,
    sequence: int,
    agent_name: str,
    iteration: int,
    scene_index: int | None,
    temperature: float | None,
    prompt: str | None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "ts": _utc_now_ms(),
        "sequence": sequence,
        "agent_name": agent_name,
        "tool_name": None,
        "iteration": iteration,
        "scene_index": scene_index,
        "model": MODEL,
        "temperature": temperature,
        "prompt": prompt,
        "response": None,
        "parsed_response": None,
        "latency_ms": None,
        "input_tokens": None,
        "output_tokens": None,
        "error": None,
    }


def log_validator_decision(**payload: Any) -> None:
    run_id = _run_id()
    sequence = _next_sequence(run_id)
    record = _base_record(
        run_id=run_id,
        sequence=sequence,
        agent_name="_validator",
        iteration=int(payload.pop("iteration", 0) or 0),
        scene_index=payload.pop("scene_index", None),
        temperature=None,
        prompt=None,
    )
    record.update(payload)
    _write_or_replace_record(record)


def _client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI()
    return _CLIENT


def _chat_completion(prompt: str, *, temperature: float, max_tokens: int) -> tuple[str, int | None, int | None]:
    resp = _client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    usage = resp.usage
    input_tokens = usage.prompt_tokens if usage is not None else None
    output_tokens = usage.completion_tokens if usage is not None else None
    return resp.choices[0].message.content or "", input_tokens, output_tokens


def _tool_parse_error(message: str, raw_response: str = "") -> JSONDecodeError:
    return JSONDecodeError(message, raw_response, 0)


def call_model_tool(
    prompt: str,
    *,
    tool_name: str,
    tool_schema: dict[str, Any],
    temperature: float,
    max_tokens: int = 4000,
    agent_name: str = "unknown",
    iteration: int = 0,
    scene_index: int | None = None,
) -> dict[str, Any]:
    retry_prompt = prompt
    last_raw_response: str | None = None
    for attempt in range(3):
        raw_arguments: str | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None
        run_id = _run_id()
        sequence = _next_sequence(run_id)
        start = perf_counter()
        record = _base_record(
            run_id=run_id,
            sequence=sequence,
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            temperature=temperature,
            prompt=retry_prompt,
        )
        record["tool_name"] = tool_name
        trace_event(
            agent_name,
            event_type="prompt_assembled",
            details=prompt_payload(retry_prompt),
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            sequence=sequence,
            attempt=attempt + 1,
            temperature=temperature,
        )
        trace_event(
            agent_name,
            event_type="model_call",
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            sequence=sequence,
            attempt=attempt + 1,
            temperature=temperature,
        )
        _write_or_replace_record(record)
        try:
            resp = _client().chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": retry_prompt}],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": f"Return {tool_name} arguments as JSON.",
                            "parameters": tool_schema,
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                parallel_tool_calls=False,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            usage = resp.usage
            input_tokens = usage.prompt_tokens if usage is not None else None
            output_tokens = usage.completion_tokens if usage is not None else None
            message = resp.choices[0].message
            tool_calls = message.tool_calls
            if not tool_calls:
                raise _tool_parse_error(f"{tool_name} tool call missing")
            tool_call = tool_calls[0]
            if tool_call.function.name != tool_name:
                raise _tool_parse_error(f"Expected tool {tool_name}, got {tool_call.function.name}")
            raw_arguments = tool_call.function.arguments
            last_raw_response = raw_arguments
            parsed = json.loads(raw_arguments)
            if not isinstance(parsed, dict):
                raise _tool_parse_error(f"{tool_name} arguments must decode to a JSON object", raw_arguments)
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "response": raw_arguments,
                    "parsed_response": parsed,
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            return parsed
        except JSONDecodeError as exc:
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "response": raw_arguments,
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            if attempt < 2:
                trace_event(
                    agent_name,
                    event_type="retry",
                    agent_name=agent_name,
                    iteration=iteration,
                    scene_index=scene_index,
                    sequence=sequence,
                    attempt=attempt + 1,
                    reason="json_decode_error",
                )
                retry_prompt = (
                    f"{prompt}\n\n"
                    f"Your previous response did not invoke the {tool_name} function with valid JSON arguments. Retry."
                )
        except Exception as exc:
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "response": raw_arguments,
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise

    raise_run_failed(
        agent_name=agent_name,
        failure_category="unparseable_json",
        last_raw_response=last_raw_response,
        attempt_count=3,
    )


def call_model_json(
    prompt: str,
    *,
    temperature: float,
    max_tokens: int = 4000,
    agent_name: str = "unknown",
    iteration: int = 0,
    scene_index: int | None = None,
) -> Any:
    retry_prompt = prompt
    last_raw_response: str | None = None
    for attempt in range(3):
        response: str | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None
        run_id = _run_id()
        sequence = _next_sequence(run_id)
        start = perf_counter()
        record = _base_record(
            run_id=run_id,
            sequence=sequence,
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            temperature=temperature,
            prompt=retry_prompt,
        )
        trace_event(
            agent_name,
            event_type="prompt_assembled",
            details=prompt_payload(retry_prompt),
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            sequence=sequence,
            attempt=attempt + 1,
            temperature=temperature,
        )
        trace_event(
            agent_name,
            event_type="model_call",
            agent_name=agent_name,
            iteration=iteration,
            scene_index=scene_index,
            sequence=sequence,
            attempt=attempt + 1,
            temperature=temperature,
        )
        _write_or_replace_record(record)
        try:
            response, input_tokens, output_tokens = _chat_completion(retry_prompt, temperature=temperature, max_tokens=max_tokens)
            last_raw_response = response
            parsed = json.loads(strip_json_fence(response))
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "response": response,
                    "parsed_response": parsed,
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            return parsed
        except JSONDecodeError as exc:
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "response": response,
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            if attempt < 2:
                response_preview = (response or "")[:200]
                trace_event(
                    agent_name,
                    event_type="retry",
                    agent_name=agent_name,
                    iteration=iteration,
                    scene_index=scene_index,
                    sequence=sequence,
                    attempt=attempt + 1,
                    reason="json_decode_error",
                )
                retry_prompt = (
                    f"{prompt}\n\nThe previous response was not valid JSON. "
                    f"JSONDecodeError: {exc}. "
                    f"Response preview: {response_preview}. "
                    "Return only valid JSON, with no prose or markdown fences."
                )
        except Exception as exc:
            record.update(
                {
                    "ts": _utc_now_ms(),
                    "latency_ms": int((perf_counter() - start) * 1000),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            _write_or_replace_record(record)
            trace_event(
                agent_name,
                event_type="model_result",
                agent_name=agent_name,
                iteration=iteration,
                scene_index=scene_index,
                sequence=sequence,
                attempt=attempt + 1,
                latency_ms=record["latency_ms"],
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise

    raise_run_failed(
        agent_name=agent_name,
        failure_category="unparseable_json",
        last_raw_response=last_raw_response,
        attempt_count=3,
    )
