"""Reusable UI components for the Streamlit app. Stateless renderers only."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import streamlit as st


def rating_stars(rating: int | None) -> str:
    if rating is None:
        return "Not rated"
    filled = max(0, min(5, int(rating)))
    return "★" * filled + "☆" * (5 - filled)


def category_label(entry_or_cover: dict[str, Any]) -> str:
    if entry_or_cover.get("category_id") == "cozy_animal_story":
        return "Animal story"
    return str(
        entry_or_cover.get("category_display_name")
        or entry_or_cover.get("category_chip")
        or entry_or_cover.get("category_id")
        or "Story"
    )


def category_chip_html(name: str) -> str:
    return (
        f"<span style='background:#e8eaf6;color:#3949ab;padding:3px 12px;"
        f"border-radius:14px;font-size:0.82rem;font-weight:500;"
        f"display:inline-block;margin-right:6px;'>{html.escape(name)}</span>"
    )


def page_progress(index: int, total: int) -> None:
    if total <= 0:
        return
    st.progress((index + 1) / total)
    st.caption(f"Page {index + 1} of {total}")


def cover_panel(package: Any, *, rating: int | None) -> None:
    """Render a centered book-cover-style panel for a generated story."""
    cover = package.cover
    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        st.markdown(
            f"<h1 style='text-align:center;margin:0.2rem 0 0.6rem 0;font-size:2.1rem;line-height:1.25;'>"
            f"{html.escape(cover['title'])}</h1>",
            unsafe_allow_html=True,
        )
        chip_html = category_chip_html(category_label(cover))
        st.markdown(
            f"<div style='text-align:center;margin-bottom:1.2rem;'>{chip_html}</div>",
            unsafe_allow_html=True,
        )

        if cover.get("fallback") or package.classification.fallback:
            st.info("Default category — the classifier fell back to general bedtime.")

        st.markdown("---")

        meta_rows = [
            ("Words", str(cover["actual_word_count"])),
            ("User score", rating_stars(rating)),
        ]
        for label, value in meta_rows:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:0.4rem 0;border-bottom:1px solid rgba(128,128,128,0.18);'>"
                f"<span style='opacity:0.7;'>{html.escape(label)}</span>"
                f"<span style='font-weight:500;'>{html.escape(value)}</span></div>",
                unsafe_allow_html=True,
            )


def shelf_tile(entry: dict[str, Any], key: str) -> str | None:
    """Render one story shelf tile. Returns 'read', 'remix', or None."""
    action: str | None = None
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:1.1rem;font-weight:600;margin-bottom:0.4rem;'>"
            f"{html.escape(entry['title'])}</div>",
            unsafe_allow_html=True,
        )
        if entry.get("is_example"):
            st.markdown(
                "<div style='margin-bottom:0.4rem;'>"
                "<span style='background:#fff3cd;color:#856404;padding:3px 12px;"
                "border-radius:14px;font-size:0.82rem;font-weight:500;"
                "display:inline-block;margin-right:6px;'>EXAMPLE</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        chip_parts = [category_chip_html(category_label(entry))]
        st.markdown(
            f"<div style='margin-bottom:0.4rem;'>{''.join(chip_parts)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{entry['actual_word_count']} words · {rating_stars(entry.get('user_rating'))}")
        read_col, remix_col = st.columns(2)
        if read_col.button("Read Again", key=f"{key}_read", use_container_width=True):
            action = "read"
        if remix_col.button("Remix Story", key=f"{key}_remix", use_container_width=True):
            action = "remix"
    return action


_STAGE_LABELS = [
    ("pipeline.understand", "Understood request"),
    ("pipeline.assemble_blueprint", "Planned spine, scenes, and characters"),
    ("agents.write_draft", "Wrote scenes"),
    ("agents.stitch_scenes", "Stitched scenes together"),
    ("pipeline.judge_all", "Judged for bedtime fit"),
    ("pipeline.package", "Prepared reader"),
]


def _read_trace_events(trace_id: str | None) -> list[dict[str, Any]]:
    if not trace_id:
        return []
    from story_engine.config import LOGS_DIR

    path = Path(LOGS_DIR) / f"{trace_id}.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def progress_checklist(trace_id: str | None) -> None:
    """Render a static post-run checklist of pipeline stages by replaying the trace."""
    events = _read_trace_events(trace_id)
    if not events:
        st.caption("No trace events recorded for this run.")
        return
    stages_seen = {event.get("stage") for event in events}
    polish_count = sum(1 for event in events if event.get("stage") == "agent.polish")
    lines: list[str] = []
    for stage_key, label in _STAGE_LABELS:
        mark = "✅" if stage_key in stages_seen else "·"
        lines.append(f"{mark} {label}")
    if polish_count > 0:
        lines.insert(-1, f"✅ Polished {polish_count} time(s)")
    st.markdown("<br>".join(lines), unsafe_allow_html=True)


def reviewer_details(package: Any, trace_id: str | None) -> None:
    """Curated reviewer-facing summary for a freshly generated package, with raw trace below."""
    classification = package.classification
    summary = {
        "Selected category": classification.category_display_name,
        "Classifier skipped": classification.classifier_skipped,
        "Classifier fallback used": classification.fallback,
        "Final word count": package.cover["actual_word_count"],
        "Pages": package.cover.get("page_count"),
        "Trace ID": trace_id or "—",
    }
    revision_count = len(getattr(package, "revision_plans", []) or [])
    summary["Revisions"] = revision_count

    st.markdown("**Pipeline stages**")
    progress_checklist(trace_id)
    st.markdown("")
    st.markdown("**Run summary**")
    for label, value in summary.items():
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:0.25rem 0;'>"
            f"<span style='opacity:0.7;'>{html.escape(label)}</span>"
            f"<span><code>{html.escape(str(value))}</code></span></div>",
            unsafe_allow_html=True,
        )
    with st.expander("Raw trace JSON"):
        events = _read_trace_events(trace_id)
        st.json(events if events else {"trace_id": trace_id, "events": "none"})
    with st.expander("LLM calls"):
        from story_engine.model_client.call_log import _error_text, load_records, summary_line
        records = load_records(trace_id) if trace_id else []
        if not records:
            st.caption("No LLM call log for this run.")
        else:
            agents = sorted({r.get("agent_name") or "?" for r in records})
            selected_agents = st.multiselect(
                "Filter by agent", options=agents, default=agents,
                key=f"llm_calls_agents_{trace_id}",
            )
            errors_only = st.checkbox(
                "Errors only", key=f"llm_calls_errors_{trace_id}",
            )
            filtered = [
                r for r in records
                if (r.get("agent_name") or "?") in selected_agents
                and (not errors_only or r.get("error"))
            ]
            st.caption(f"{len(filtered)} of {len(records)} calls")
            if filtered:
                labels = [summary_line(r) for r in filtered]
                idx = st.selectbox(
                    "Select a call",
                    options=list(range(len(filtered))),
                    format_func=lambda i: labels[i],
                    key=f"llm_calls_select_{trace_id}",
                )
                record = filtered[idx]
                if record.get("error"):
                    err_type, err_msg = _error_text(record["error"])
                    st.error(f"{err_type}: {err_msg}")
                col_prompt, col_response = st.columns(2)
                with col_prompt:
                    st.markdown("**Prompt**")
                    st.code(record.get("prompt") or "(no prompt)", language="text")
                with col_response:
                    st.markdown("**Response**")
                    st.code(record.get("response") or "(no response)", language="text")

