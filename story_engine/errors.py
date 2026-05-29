from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from story_engine.config import STORIES_DIR
from story_engine.trace import current_run_id, ensure_dir


class RunFailed(Exception):
    def __init__(
        self,
        *,
        agent_name: str,
        failure_category: str,
        last_raw_response: str | None = None,
        attempt_count: int = 0,
    ) -> None:
        super().__init__(f"{agent_name} failed: {failure_category}")
        self.agent_name = agent_name
        self.failure_category = failure_category
        self.last_raw_response = last_raw_response
        self.attempt_count = attempt_count


def persist_agent_failure(exc: RunFailed, *, run_id: str | None = None) -> Path:
    active_run_id = run_id or current_run_id() or "untraced"
    directory = ensure_dir(Path(STORIES_DIR) / active_run_id / "agent_failures")
    path = directory / f"{exc.agent_name}.json"
    payload = {
        "agent_name": exc.agent_name,
        "failure_category": exc.failure_category,
        "raw_response": exc.last_raw_response,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "attempt_count": exc.attempt_count,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    return path


def raise_run_failed(
    *,
    agent_name: str,
    failure_category: str,
    last_raw_response: str | None = None,
    attempt_count: int = 0,
) -> None:
    exc = RunFailed(
        agent_name=agent_name,
        failure_category=failure_category,
        last_raw_response=last_raw_response,
        attempt_count=attempt_count,
    )
    persist_agent_failure(exc)
    raise exc
