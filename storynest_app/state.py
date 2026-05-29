from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

from story_engine import persistence
from story_engine.config import STORIES_DIR
from story_engine.schemas import RequestOptions


STORY_MODE_OPTIONS = {
    "Auto-detect (let StoryNest choose)": "auto_detect",
    "Classic bedtime story": "classic",
    "Animal story": "animal",
    "Gentle adventure": "gentle_adventure",
    "Magical story": "magical",
    "Friendship story": "friendship",
    "Silly story": "silly",
    "Educational story": "educational",
}
FAILURE_MESSAGES = {
    "safety_fail": "Unable to generate a safe story with your request. Please try again!",
}
GENERIC_FAILURE_MESSAGE = "Something went wrong while writing your story. Please try again."


def message_for_failure(category: str) -> str:
    return FAILURE_MESSAGES.get(category, GENERIC_FAILURE_MESSAGE)


STABLE_SCREENS = {"home", "request", "library", "about", "remix", "error"}


def _init_state() -> None:
    defaults = {
        "screen": "home",
        "page_index": 0,
        "package": None,
        "pending_request": "",
        "pending_options": None,
        "trace_id": None,
        "pending_remix_source": None,
        "fail_message": None,
        "save_result": None,
        "saved_story": None,
        "library_selected_run_id": None,
        "reader_mode": "generation",
        "read_view": None,
        "shelf_filter_category": "All categories",
        "shelf_sort": "Newest",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if not st.session_state.setdefault("_seeded_examples", False):
        try:
            persistence.ensure_seed_examples()
            st.session_state["_seeded_examples"] = True
        except Exception as exc:
            print(f"Failed to seed example stories: {exc}", file=sys.stderr)


def _read_index_entries() -> list[dict[str, Any]]:
    path = Path(STORIES_DIR) / "index.jsonl"
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _options_from_request_form() -> RequestOptions:
    mode_label = st.radio("Story mode", list(STORY_MODE_OPTIONS), index=0, key="form_mode")
    character = st.text_input("Main character name (optional)", key="form_character")
    return RequestOptions(
        story_mode=STORY_MODE_OPTIONS[mode_label],
        main_character_name=character.strip(),
    )


def _clear_generation_state() -> None:
    st.session_state.package = None
    st.session_state.pending_request = ""
    st.session_state.pending_options = None
    st.session_state.pending_remix_source = None
    st.session_state.read_view = None
    st.session_state.reader_mode = "generation"
    st.session_state.page_index = 0
    st.session_state.save_result = None


def _begin_generation(request: str, options: RequestOptions, remix_source: str | None = None) -> None:
    st.session_state.pending_request = request
    st.session_state.pending_options = options
    st.session_state.trace_id = persistence.run_id_for("streamlit-generation")
    st.session_state.pending_remix_source = remix_source
    st.session_state.screen = "generating"
    st.session_state.reader_mode = "generation"
    st.session_state.read_view = None
    st.session_state.page_index = 0
    st.session_state.save_result = None
    st.rerun()


def _begin_read(run_id: str) -> None:
    st.session_state.read_view = persistence.load_for_read(run_id)
    st.session_state.reader_mode = "read_only"
    st.session_state.page_index = 0
    st.session_state.library_selected_run_id = run_id
    st.session_state.screen = "reader"
    st.rerun()


def _begin_remix_from_library(run_id: str) -> None:
    st.session_state.saved_story = persistence.load_for_remix(run_id)
    st.session_state.library_selected_run_id = run_id
    st.session_state.screen = "remix"
    st.rerun()
