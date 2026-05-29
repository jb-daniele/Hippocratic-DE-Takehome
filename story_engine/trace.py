import json
import hashlib
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from story_engine.config import LOGS_DIR, MODEL


_current_run_id: ContextVar[str | None] = ContextVar("story_engine_trace_run_id", default=None)
_current_metadata: ContextVar[dict[str, Any]] = ContextVar("story_engine_trace_metadata", default={})
_RUN_ID_PREFIX_RE = re.compile(r"^(?P<date>\d{8})T")


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_date_partition(run_id: str) -> str:
    match = _RUN_ID_PREFIX_RE.match(run_id)
    if match is None:
        raise ValueError(f"run_id must start with UTC timestamp prefix YYYYMMDDT: {run_id}")
    stamp = match.group("date")
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"


def partitioned_log_dir(run_id: str, *, root: str | Path | None = None) -> Path:
    return Path(LOGS_DIR if root is None else root) / _run_date_partition(run_id)


class Run:
    def __init__(self, run_id: str, *, metadata: dict[str, Any] | None = None):
        self.run_id = run_id
        self.path = partitioned_log_dir(run_id) / f"{run_id}.jsonl"
        self._token = None
        self._metadata_token = None
        self.metadata = metadata or {}

    def __enter__(self) -> "Run":
        ensure_dir(self.path.parent)
        self._token = _current_run_id.set(self.run_id)
        merged = dict(_current_metadata.get() or {})
        merged.update(self.metadata)
        self._metadata_token = _current_metadata.set(merged)
        self.event("run_start")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc is None:
            self.event("run_end")
        else:
            self.event("run_error", error=str(exc), error_type=exc_type.__name__ if exc_type else "unknown")
        if self._metadata_token is not None:
            _current_metadata.reset(self._metadata_token)
        if self._token is not None:
            _current_run_id.reset(self._token)

    def event(self, stage: str, **kwargs: Any) -> None:
        ensure_dir(self.path.parent)
        metadata = current_metadata()
        payload = {
            "run_id": self.run_id,
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "event_type": kwargs.pop("event_type", "log"),
            "mode": kwargs.pop("mode", metadata.get("mode", "dev")),
            "model_snapshot": kwargs.pop("model_snapshot", metadata.get("model_snapshot", MODEL)),
            "prompt_id": kwargs.pop("prompt_id", metadata.get("prompt_id")),
            "seed": kwargs.pop("seed", metadata.get("seed")),
            **kwargs,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def event(stage: str, **kwargs: Any) -> None:
    run_id = _current_run_id.get()
    if run_id:
        Run(run_id).event(stage, **kwargs)


def current_run_id() -> str | None:
    return _current_run_id.get()


def current_metadata() -> dict[str, Any]:
    return dict(_current_metadata.get() or {})


def prompt_payload(prompt: str, *, include_text: bool = True, preview_chars: int = 160) -> dict[str, Any]:
    payload = {
        "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:preview_chars],
    }
    if include_text:
        payload["prompt_text"] = prompt
    return payload

def trace_path(run_id: str) -> Path:
    return partitioned_log_dir(run_id) / f"{run_id}.jsonl"
