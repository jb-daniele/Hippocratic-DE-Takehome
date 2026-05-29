from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from story_engine.config import LOGS_DIR, STORIES_DIR
from story_engine.trace import partitioned_log_dir


def _error_text(err: Any) -> tuple[str, str]:
    """Return (type, message) for either dict-shaped or string-shaped error values."""
    if isinstance(err, dict):
        return str(err.get("type", "?")), str(err.get("message", ""))
    return "error", str(err)


def load_records(run_id: str) -> list[dict[str, Any]]:
    """Load LLM-call records for a run, preferring the story-dir copy, sorted by sequence."""
    dated_log = None
    try:
        dated_log = partitioned_log_dir(run_id, root=LOGS_DIR) / f"{run_id}-llm-calls.jsonl"
    except ValueError:
        dated_log = None
    candidates = [
        STORIES_DIR / run_id / "llm-calls.jsonl",
        *([dated_log] if dated_log is not None else []),
        Path(LOGS_DIR) / f"{run_id}-llm-calls.jsonl",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    records.sort(key=lambda r: r.get("sequence") or 0)
    return records


def summary_line(record: dict[str, Any]) -> str:
    """One-line summary, e.g. '[05] scene_writer · sc 2 · iter 0 · 2310ms · 2204→518t'."""
    seq = record.get("sequence")
    seq_str = f"[{seq:02d}]" if isinstance(seq, int) else "[??]"
    agent = record.get("agent_name") or "?"
    scene = record.get("scene_index")
    scene_str = f"sc {scene}" if scene is not None else "—"
    it = record.get("iteration") or 0
    latency = record.get("latency_ms")
    err = record.get("error")
    if err:
        err_type, _ = _error_text(err)
        status = f"ERROR {err_type}"
    elif latency is not None:
        status = f"{latency}ms"
    else:
        status = "(pending)"
    tin = record.get("input_tokens")
    tout = record.get("output_tokens")
    if tin is not None or tout is not None:
        tokens = f"{tin if tin is not None else '?'}→{tout if tout is not None else '?'}t"
    else:
        tokens = "—"
    return f"{seq_str} {agent} · {scene_str} · iter {it} · {status} · {tokens}"


def render_html(run_id: str, records: list[dict[str, Any]]) -> str:
    """Render a self-contained static HTML page of LLM calls for a run."""
    rows: list[str] = []
    for r in records:
        summary = html.escape(summary_line(r))
        prompt = html.escape(r.get("prompt") or "(no prompt)")
        response = html.escape(r.get("response") or "(no response)")
        err = r.get("error")
        error_html = ""
        if err:
            err_type, err_msg = _error_text(err)
            error_html = (
                f'<div class="error">Error: {html.escape(err_type)} '
                f'— {html.escape(err_msg)}</div>'
            )
        rows.append(
            f"""<details class="call">
  <summary>{summary}</summary>
  {error_html}
  <div class="cols">
    <section><h3>Prompt</h3><pre>{prompt}</pre></section>
    <section><h3>Response</h3><pre>{response}</pre></section>
  </div>
</details>"""
        )
    body = "\n".join(rows) if rows else "<p>No LLM calls recorded.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLM calls — {html.escape(run_id)}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 2rem; max-width: 1200px; }}
h1 {{ font-size: 1.25rem; }}
details.call {{ border: 1px solid #ddd; border-radius: 6px; margin: 0.5rem 0; padding: 0.5rem 0.75rem; }}
details.call summary {{ cursor: pointer; font-family: ui-monospace, Menlo, monospace; font-size: 0.9rem; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.75rem; }}
.cols section h3 {{ font-size: 0.85rem; opacity: 0.7; margin: 0 0 0.25rem 0; }}
.cols pre {{ background: #f7f7f8; padding: 0.75rem; border-radius: 4px; white-space: pre-wrap; word-break: break-word; font-size: 0.8rem; max-height: 600px; overflow: auto; }}
.error {{ color: #b00020; background: #fff5f5; padding: 0.5rem; border-radius: 4px; margin-top: 0.5rem; }}
</style>
</head>
<body>
<h1>LLM calls — {html.escape(run_id)}</h1>
<p>{len(records)} call{'' if len(records) == 1 else 's'} recorded.</p>
{body}
</body>
</html>
"""


def write_html(run_id: str) -> Path | None:
    """Write llm-calls.html into the story dir if records exist. Returns the path or None."""
    records = load_records(run_id)
    if not records:
        return None
    target_dir = STORIES_DIR / run_id
    if not target_dir.exists():
        return None
    path = target_dir / "llm-calls.html"
    path.write_text(render_html(run_id, records), encoding="utf-8")
    return path
