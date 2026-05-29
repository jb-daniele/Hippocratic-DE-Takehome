from __future__ import annotations

import streamlit as st

from storynest_app.state import STORY_MODE_OPTIONS, _begin_generation
from story_engine.schemas import RequestOptions


def remix_screen() -> None:
    saved_story = st.session_state.saved_story
    if not saved_story:
        st.session_state.screen = "home"
        st.rerun()
        return

    blueprint = saved_story["blueprint"]
    options = saved_story["options"]

    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        st.title("Remix Story")
        st.caption(
            f"{blueprint.get('title', 'Saved story')} · "
            f"{blueprint.get('category_display_name', blueprint.get('category_id', 'Story'))}"
        )
        remix_characters = st.text_input(
            "Character names",
            key="remix_characters",
            value=", ".join(blueprint.get("main_characters", [])),
        )
        remix_setting = st.text_input("Setting (optional)", key="remix_setting", value="")
        remix_plot = st.text_area(
            "What should they do next?",
            key="remix_plot",
            height=190,
            placeholder="A new little adventure for them...",
        )
        mode_value = options.get("story_mode", "auto_detect")
        mode_index = (
            list(STORY_MODE_OPTIONS.values()).index(mode_value)
            if mode_value in STORY_MODE_OPTIONS.values()
            else 0
        )
        mode_label = st.selectbox(
            "Story mode",
            list(STORY_MODE_OPTIONS),
            key="remix_mode",
            index=mode_index,
        )

        action_col, back_col = st.columns([2, 1])
        with action_col:
            submitted = st.button(
                "Remix Story",
                type="primary",
                use_container_width=True,
                key="remix_submit",
                disabled=not remix_plot.strip(),
            )
        with back_col:
            cancelled = st.button(
                "Cancel",
                use_container_width=True,
                key="remix_cancel",
            )

        if cancelled:
            st.session_state.screen = "library"
            st.rerun()
        if submitted:
            parts = []
            characters = remix_characters.strip()
            setting = remix_setting.strip()
            plot = remix_plot.strip()
            if characters:
                parts.append(f"characters: {characters}")
            if setting:
                parts.append(f"setting: {setting}")
            parts.append(f"user request: {plot}")
            request = ", ".join(parts)
            remix_options = RequestOptions(
                story_mode=STORY_MODE_OPTIONS[mode_label],
                main_character_name=characters,
            )
            _begin_generation(request, remix_options, remix_source=saved_story["run_id"])
