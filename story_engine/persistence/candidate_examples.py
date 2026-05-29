from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from story_engine.config import PROMPT_EXAMPLE_CANDIDATES_DIR, STORIES_DIR
from story_engine.trace import event as trace_event


_CATEGORY_ID_RE = re.compile(r"^[a-z0-9_-]+$")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _candidate_paths(run_id: str) -> list[Path]:
    if not PROMPT_EXAMPLE_CANDIDATES_DIR.exists():
        return []
    return sorted(PROMPT_EXAMPLE_CANDIDATES_DIR.glob(f"*/{run_id}.json"))


def _remove_candidate(run_id: str, rating: int) -> None:
    removed_paths: list[Path] = []
    for path in _candidate_paths(run_id):
        path.unlink()
        removed_paths.append(path)

    if removed_paths:
        trace_event(
            "prompt_example_candidate.removed",
            run_id=run_id,
            rating=rating,
            path=str(removed_paths[0]),
        )
    else:
        trace_event(
            "prompt_example_candidate.skipped",
            run_id=run_id,
            rating=rating,
            reason="rating_below_threshold",
        )


def _get_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _get_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def export_candidate_if_eligible(run_id: str, rating: int) -> dict | None:
    if rating != 5:
        _remove_candidate(run_id, rating)
        return None

    story_path = STORIES_DIR / run_id / "story.json"
    if not story_path.exists():
        trace_event(
            "prompt_example_candidate.skipped",
            run_id=run_id,
            rating=rating,
            reason="story_json_missing",
        )
        return None

    source = _read_json(story_path)
    classification = _get_dict(source.get("classification"))
    blueprint = _get_dict(source.get("blueprint"))
    final_package = _get_dict(source.get("final_package"))
    story = _get_dict(final_package.get("story"))

    category_id = classification.get("category_id") or ""
    if not category_id:
        trace_event(
            "prompt_example_candidate.skipped",
            run_id=run_id,
            rating=rating,
            reason="missing_category_id",
        )
        return None
    if not isinstance(category_id, str) or not _CATEGORY_ID_RE.fullmatch(category_id):
        trace_event(
            "prompt_example_candidate.skipped",
            run_id=run_id,
            rating=rating,
            reason="invalid_category_id",
        )
        return None

    story_spine = _get_dict(blueprint.get("story_spine"))
    scene_cards = _get_list(blueprint.get("scene_cards"))
    final_story_body = story.get("body", "")

    validation = {
        "category_id_present": bool(category_id),
        "story_spine_present": bool(story_spine),
        "scene_cards_present": bool(scene_cards),
        "scene_count": len(scene_cards),
        "final_story_body_present": bool(final_story_body),
        "candidate_saved": True,
    }
    payload = {
        "run_id": run_id,
        "category_id": category_id,
        "rating": rating,
        "created_at": _utc_now(),
        "story_title": story.get("title", ""),
        "request_text": classification.get("request_text", ""),
        "story_spine": story_spine,
        "scene_cards": scene_cards,
        "final_story_body": final_story_body,
        "validation": validation,
        "promotion_status": "candidate",
    }

    target_path = PROMPT_EXAMPLE_CANDIDATES_DIR / category_id / f"{run_id}.json"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(target_path, payload)
    trace_event(
        "prompt_example_candidate.saved",
        run_id=run_id,
        category_id=category_id,
        rating=rating,
        path=str(target_path),
        validation=validation,
    )
    return payload
