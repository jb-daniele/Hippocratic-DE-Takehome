from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.config import STORIES_DIR
from story_engine.persistence import candidate_examples
from story_engine.trace import current_run_id, event as trace_event


INDEX_JSONL = STORIES_DIR / "index.jsonl"
INDEX_HTML = STORIES_DIR / "index.html"
SECRET_RE = re.compile(r"[s]k-[A-Za-z0-9_-]+")


def _latency_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "story"


def run_id_for(seed: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{slugify(seed)[:48]}"


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET_RE.sub("[redacted]", value)
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_redact(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_index_entries() -> list[dict[str, Any]]:
    if not INDEX_JSONL.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in INDEX_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(dict(json.loads(line)))
    return entries


def _write_index_entries(entries: list[dict[str, Any]]) -> None:
    ensure_dir(STORIES_DIR)
    lines = [json.dumps(_redact(entry), sort_keys=True) for entry in entries]
    INDEX_JSONL.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _replace_index_entry(entry: dict[str, Any]) -> None:
    entry = dict(entry)
    entries = [item for item in _read_index_entries() if item.get("run_id") != entry["run_id"]]
    entries.append(entry)
    _write_index_entries(entries)


def _unique_run_dir(title: str) -> tuple[str, Path]:
    for attempt in range(100):
        run_id = run_id_for(title)
        if attempt:
            run_id = f"{run_id}-{attempt}"
        run_dir = STORIES_DIR / run_id
        if not run_dir.exists():
            return run_id, run_dir
    raise RuntimeError("Could not allocate unique story run id")


def _get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    return data.get(key, default)


def _character_names(characters: list[Any]) -> list[str]:
    names: list[str] = []
    for character in characters:
        if isinstance(character, str):
            names.append(character)
        elif isinstance(character, dict) and character.get("name"):
            names.append(str(character["name"]))
        elif hasattr(character, "name"):
            names.append(str(character.name))
    return names


def _flatten_story(
    run_id: str,
    package: dict[str, Any],
    classification: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    blueprint = package["blueprint"]
    story = package["story"]
    story_spine = blueprint.get("story_spine") or {}
    cover = package.get("cover", {})

    classifier_confidence = classification["classifier_confidence"]
    characters = _character_names(blueprint.get("main_characters") or classification.get("main_characters") or [])

    return {
        "run_id": run_id,
        "id": run_id,
        "created_at": created_at,
        "title": story["title"],
        "cover": cover,
        "story_mode": classification["selected_story_mode"],
        "category_id": classification["category_id"],
        "category_display_name": classification["category_display_name"],
        "classifier_confidence": classifier_confidence,
        "classifier_rationale": classification["classifier_rationale"],
        "classifier_matched_signals": classification["matched_signals"],
        "classifier_fallback_status": classification["fallback"],
        "classifier_skipped": classification["classifier_skipped"],
        "actual_word_count": package["actual_word_count"],
        "characters": characters,
        "pages": package["pages"],
        "page_break_suggestions": package["page_break_suggestions"],
        "gentle_conflict": story_spine.get("central_problem", ""),
        "ending_closure_plan": story_spine.get("ending_image", ""),
        "body": story["body"],
        "source_request": classification["request_text"],
        "user_rating": None,
        "rating_recorded_at": None,
        "story_json_path": f"stories/{run_id}/story.json",
        "story_html_path": f"stories/{run_id}/story.html",
    }


def _render_story_html(entry: dict[str, Any]) -> str:
    paragraphs = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in entry["body"].splitlines() if paragraph.strip())
    characters = "".join(f"<span class=\"chip\">{html.escape(character)}</span>" for character in entry["characters"])
    meta_parts = [
        entry["category_display_name"],
        f"{entry['actual_word_count']} words",
    ]
    meta = " | ".join(html.escape(str(part)) for part in meta_parts)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(entry["title"])}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #17202a; }}
    .meta {{ color: #4d5b66; }}
    .chip {{ display: inline-block; border: 1px solid #ccd5df; border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <a href="../index.html">Back to library</a>
  <h1>{html.escape(entry["title"])}</h1>
  <p class="meta">{meta}</p>
  <p>{characters}</p>
  {paragraphs}
</body>
</html>
"""


def _stars(rating: int | None) -> str:
    if rating is None:
        return "Not rated"
    filled = max(0, min(5, rating))
    return "&#9733;" * filled + "&#9734;" * (5 - filled)


def persist_story(final_package: Any, classification: Any) -> dict[str, str]:
    start = perf_counter()
    package = _plain(final_package)
    classification_data = _plain(classification)
    if not isinstance(package, dict) or not isinstance(classification_data, dict):
        raise TypeError("persist_story expects dict-like package and classification")

    ensure_dir(STORIES_DIR)
    title = package["story"]["title"]
    run_id, run_dir = _unique_run_dir(title)
    ensure_dir(run_dir)

    created_at = _utc_now()
    entry = _flatten_story(run_id, package, classification_data, created_at)
    payload = {
        "run_id": run_id,
        "created_at": created_at,
        "request_options": package["request"],
        "classification": classification_data,
        "blueprint": package["blueprint"],
        "final_package": package,
        "index_entry": entry,
    }

    json_path = run_dir / "story.json"
    html_path = run_dir / "story.html"
    _write_json(json_path, payload)
    html_path.write_text(_redact(_render_story_html(entry)), encoding="utf-8")
    model_client.copy_llm_log_to_story_dir(current_run_id(), run_id)
    from story_engine.model_client.call_log import write_html
    write_html(run_id)
    _replace_index_entry(entry)
    render_index_html()

    paths = {"run_id": run_id, "json": str(json_path), "html": str(html_path)}
    trace_event("persistence.persist_story", run_id=run_id, category_id=entry["category_id"], latency_ms=_latency_ms(start))
    return paths


def _update_saved_entry(run_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    json_path = STORIES_DIR / run_id / "story.json"
    if not json_path.exists():
        raise FileNotFoundError(f"No persisted story found for run_id={run_id}")

    payload = _read_json(json_path)
    entry = payload["index_entry"]
    entry.update(updates)
    entry = dict(entry)
    payload["index_entry"] = entry
    _write_json(json_path, payload)

    entries = _read_index_entries()
    updated = False
    for index, item in enumerate(entries):
        if item.get("run_id") == run_id:
            entries[index] = entry
            updated = True
            break
    if not updated:
        entries.append(entry)
    _write_index_entries(entries)
    render_index_html()
    return entry


def record_user_rating(run_id: str, rating: int) -> None:
    start = perf_counter()
    if isinstance(rating, bool) or not isinstance(rating, int):
        raise ValueError("rating must be an integer")
    _update_saved_entry(run_id, {"user_rating": rating, "rating_recorded_at": _utc_now()})
    trace_event("persistence.record_user_rating", run_id=run_id, rating=rating, latency_ms=_latency_ms(start))
    try:
        candidate_examples.export_candidate_if_eligible(run_id, rating)
    except Exception as exc:
        trace_event("prompt_example_candidate.export_failed", run_id=run_id, error=repr(exc))


def render_index_html() -> str:
    start = perf_counter()
    ensure_dir(STORIES_DIR)
    entries = sorted(_read_index_entries(), key=lambda item: item.get("created_at", ""), reverse=True)
    cards = []
    for entry in entries:
        story_href = html.escape(f"{entry['run_id']}/story.html")
        characters = "".join(f"<span class=\"chip\">{html.escape(character)}</span>" for character in entry.get("characters", []))
        cards.append(
            f"""<article class="card">
  <h2><a href="{story_href}">{html.escape(entry["title"])}</a></h2>
  <p><span class="chip category">{html.escape(entry["category_display_name"])}</span></p>
  <p class="meta">{entry["actual_word_count"]} words</p>
  <p>{characters}</p>
  <p class="stars" aria-label="Rating {entry.get("user_rating")} out of 5">{_stars(entry.get("user_rating"))}</p>
</article>"""
        )

    body = "\n".join(cards) if cards else "<p>No saved stories yet.</p>"
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StoryNest Story Library</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; color: #17202a; background: #f7f9fb; }}
    h1 {{ margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
    .card {{ background: #fff; border: 1px solid #d9e1e8; border-radius: 8px; padding: 16px; }}
    .card h2 {{ font-size: 1.05rem; margin-top: 0; }}
    .meta {{ color: #4d5b66; margin: 8px 0; }}
    .chip {{ display: inline-block; border: 1px solid #ccd5df; border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0; font-size: 0.85rem; background: #fff; }}
    .category {{ background: #e9f2ff; border-color: #b8d5f5; }}
    .stars {{ letter-spacing: 1px; color: #7a5a00; }}
  </style>
</head>
<body>
  <h1>StoryNest Story Library</h1>
  <main class="grid">
{body}
  </main>
</body>
</html>
"""
    INDEX_HTML.write_text(_redact(document), encoding="utf-8")
    trace_event("persistence.render_index_html", entries=len(entries), latency_ms=_latency_ms(start))
    return str(INDEX_HTML)


def load_for_remix(run_id: str) -> dict[str, Any]:
    start = perf_counter()
    payload = _read_json(STORIES_DIR / run_id / "story.json")
    options = dict(payload["request_options"])
    blueprint = dict(payload["blueprint"])
    result = {
        "run_id": payload["run_id"],
        "blueprint": blueprint,
        "options": options,
    }
    trace_event("persistence.load_for_remix", run_id=run_id, latency_ms=_latency_ms(start))
    return result


def load_for_read(run_id: str) -> dict[str, Any]:
    start = perf_counter()
    payload = _read_json(STORIES_DIR / run_id / "story.json")
    entry = payload["index_entry"]
    result = {
        "run_id": run_id,
        "title": entry["title"],
        "pages": entry["pages"],
        "category_display_name": entry["category_display_name"],
        "category_id": entry["category_id"],
        "actual_word_count": entry["actual_word_count"],
        "characters": entry.get("characters", []),
        "user_rating": entry.get("user_rating"),
    }
    trace_event("persistence.load_for_read", run_id=run_id, latency_ms=_latency_ms(start))
    return result
